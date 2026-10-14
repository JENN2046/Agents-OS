import test from 'node:test';
import assert from 'node:assert/strict';
import {generateKeyPairSync,randomUUID} from 'node:crypto';
import {signed,exportPublicKey,digest,ACTIONS,ROLES} from '../src/lease-core.mjs';
import {validateHumanProposal,firstTrustReviewedIntent,PROJECTS_ROOT} from '../human/approval-policy.mjs';
import {inspectFirstTrustJournal} from '../human/first-trust-journal.mjs';
import {STAGE_CONSTRAINTS} from '../authority/stage-authorization.mjs';

const pair=()=>generateKeyPairSync('ed25519').privateKey;
function fixture(){
 const releaseKey=pair(),issuerKey=pair(),enrollmentKey=pair(),humanKey=pair();
 const peers=Object.fromEntries(ROLES.map(role=>[role,{id:'peer-'+role,publicKey:exportPublicKey(pair())}]));
 const now=1792000000000;
 const versions=Object.fromEntries(ROLES.map(role=>[role,digest(role)]));
 const sourceRelease=signed({schema:'r16.release.v1',id:'r16-daily-20261012-r15',
   issuedAt:now-86400000,notAfter:now-1000,formats:['r16.workspace.v1'],
   versions,actions:ACTIONS,permissionVersion:1},releaseKey);
 const sourceGrant=signed({schema:'r16.workspace.v1',id:'r16-projects-daily',
   version:1,createdAt:now-86400000,workspace:{id:'ws_8c7dd971e518',
     root:PROJECTS_ROOT,dev:1,ino:2},actions:ACTIONS,channel:'main',peers},issuerKey);
 const reviewManifest={schema:'r16.reviewed-installation.v1',
   releaseId:'r16-daily-20261012-r17',
   artifacts:{app:{},bridge:{},native:{}},
   localFiles:[{role:'native',path:'/opt/r16/releases/r16-daily-20261012-r17/src/a.mjs',
     sha256:digest('a'),artifactPath:'src/a.mjs'}]};
 const trustRoots={schema:'mht.trust-roots.v1',grantId:'r16-projects-daily',
   issuerPublicKey:exportPublicKey(issuerKey),releasePublicKey:exportPublicKey(releaseKey),
   enrollmentAuthorityPublicKey:exportPublicKey(enrollmentKey),
   releaseHash:digest(sourceRelease),handoffHash:digest('handoff'),installationProfile:'isolated'};
 const stageAuthorization={schema:'mht.first-trust-stage-authorization.v2',phase:'STAGE_ONLY',
   sourceReleaseId:'r16-daily-20261012-r15',targetReleaseId:'r16-daily-20261012-r17',
   grantId:'r16-projects-daily',grantHash:digest(sourceGrant),grantVersion:1,
   r15PublicConfigDigest:digest('public-config'),reviewedManifestHash:digest(reviewManifest),
   recoveryEvidenceDigest:digest('evidence'),sourceFreezeDigest:digest('source-freeze'),
   installerHash:digest('installer'),issuerSnapshotHash:digest('issuer-snapshot'),trustRootsDigest:digest(trustRoots),
   stopEpoch:randomUUID(),handoffEpoch:1,issuedAt:now-20000,expiresAt:now+30000,
   constraints:{...STAGE_CONSTRAINTS}};
 const body={schema:'mht.human-proposal.v1',action:'enroll_human',grantId:'r16-projects-daily',
   expectedVersion:1,expectedGrantHash:digest(sourceGrant),releaseId:'r16-daily-20261012-r15',
   releaseHash:digest(sourceRelease),nonce:randomUUID(),issuedAt:now-20000,
   expiresAt:now+30000,target:{humanUid:1000,humanSubject:'local-human:1000',
     humanPublicKey:exportPublicKey(humanKey),enrollmentExpiresAt:now+86400000,
     targetReleaseId:'r16-daily-20261012-r17',reviewedManifestHash:digest(reviewManifest),
     stageAuthorizationHash:digest(stageAuthorization),stageAuthorization}};
 const proposal=signed(body,releaseKey);
 const policy={schema:'mht.human-pending-policy.v1',proposalHash:digest(proposal),grantId:'r16-projects-daily',
   grantHash:digest(sourceGrant),grantVersion:1,releaseHash:digest(sourceRelease),releaseId:'r16-daily-20261012-r15',
   humanPublicKey:exportPublicKey(humanKey),workspaceId:'ws_8c7dd971e518',
   workspaceRoot:PROJECTS_ROOT,workspaceDev:1,workspaceIno:2,installationProfile:'isolated'};
 const checked=validateHumanProposal({proposal,policy,roots:trustRoots,now});
 const reviewedIntent=firstTrustReviewedIntent(checked);
 const osIntent={schema:'mht.human-os-intent.v1',proposalHash:policy.proposalHash,peerUid:1000,
   processStart:321,confirmedAt:now-1000,challengeHash:digest('fresh-challenge')};
 const osResult={ok:true,status:'APPROVED_NOT_APPLIED',firstTrustOsConfirmationOnly:true,
   proposalHash:policy.proposalHash,reviewedIntent,approval:null};
 const base='/var/lib/minimal-human-trust/human-approval/'+policy.proposalHash;
 const files=new Map([[base+'.intent.json',osIntent],[base+'.result.json',osResult]]);
 const readProtected=file=>{if(!files.has(file))throw Error('MISSING_ROOT_JOURNAL');return Buffer.from(JSON.stringify(files.get(file)));};
 const args={proposal,policy,trustRoots,sourceRelease,sourceGrant,reviewManifest,now,
   readProtected,isInstalled:()=>false};
 return {args,files,base,now,releaseKey,issuerKey};
}
const reject=fn=>assert.throws(fn);
test('one OS-confirmed first Human proposal is read and bound to expired genuine R15',()=>{
 const f=fixture(),result=inspectFirstTrustJournal(f.args);
 assert.equal(result.status,'OS_CONFIRMED_NOT_APPLIED');
 assert.equal(result.sourceReleaseId,'r16-daily-20261012-r15');
 assert.equal(result.targetReleaseId,'r16-daily-20261012-r17');
 assert.equal(result.reviewedManifestHash,digest(f.args.reviewManifest));
 assert.deepEqual(result.stageAuthorization,f.args.proposal.body.target.stageAuthorization);
 assert.equal(result.stageAuthorizationHash,digest(result.stageAuthorization));
 assert.equal(result.signerAuthority,false);
 assert.equal(result.mayInstall,false);
 assert.equal(result.maySignRelease,false);
 assert.equal(result.mayHandoffIssuer,false);
});
test('first-use does not overwrite an existing enrolled identity',()=>{
 const f=fixture();f.args.isInstalled=()=>true;
 reject(()=>inspectFirstTrustJournal(f.args));
});
test('tampered signed Human proposal is refused',()=>{
 const f=fixture();f.args.proposal={...f.args.proposal,signature:'A'.repeat(86)};
 reject(()=>inspectFirstTrustJournal(f.args));
});
test('release signer root mismatch is refused',()=>{
 const f=fixture();f.args.trustRoots={...f.args.trustRoots,releasePublicKey:exportPublicKey(pair())};
 reject(()=>inspectFirstTrustJournal(f.args));
});
test('no grant, grant signature forgery, or old grant switch may bootstrap',()=>{
 for(const change of [
   o=>{o.sourceGrant={...o.sourceGrant,signature:'A'.repeat(86)};},
   o=>{o.sourceGrant=signed({...o.sourceGrant.body,id:'foreign'},pair());},
 ]){
   const f=fixture();change(f.args);reject(()=>inspectFirstTrustJournal(f.args));
 }
});
test('review manifest must be exact signed proposal target',()=>{
 const f=fixture();
 f.args.reviewManifest={...f.args.reviewManifest,releaseId:'r16-daily-20261012-r18'};
 reject(()=>inspectFirstTrustJournal(f.args));
});
test('missing root-only OS receipt is not approval',()=>{
 const f=fixture();f.files.delete(f.base+'.intent.json');
 reject(()=>inspectFirstTrustJournal(f.args));
});
test('fake UID or OS confirmation outside the original request window is denied',()=>{
 for(const change of [{peerUid:0},{confirmedAt:1792000040000},{processStart:0},{challengeHash:'x'}]){
   const f=fixture(),v=f.files.get(f.base+'.intent.json');
   f.files.set(f.base+'.intent.json',{...v,...change});
   reject(()=>inspectFirstTrustJournal(f.args));
 }
});
test('journal changed after OS confirmation is rejected',()=>{
 const f=fixture(),v=f.files.get(f.base+'.result.json');
 f.files.set(f.base+'.result.json',{...v,proposalHash:digest('other')});
 reject(()=>inspectFirstTrustJournal(f.args));
});
test('the first bootstrap result MUST have a null approval signature',()=>{
 const f=fixture(),v=f.files.get(f.base+'.result.json');
 f.files.set(f.base+'.result.json',{...v,approval:{body:{},signature:'fake'}});
 reject(()=>inspectFirstTrustJournal(f.args));
});
test('an extra capability or a false applied state is rejected',()=>{
 for(const extra of [{mayInstall:true},{status:'ENROLLED'}]){
   const f=fixture(),v=f.files.get(f.base+'.result.json');
   f.files.set(f.base+'.result.json',{...v,...extra});
   reject(()=>inspectFirstTrustJournal(f.args));
 }
});
test('pending first trust intent expires and cannot be reused for another release',()=>{
 const f=fixture();f.args.now=f.now+50000;
 reject(()=>inspectFirstTrustJournal(f.args));
});
test('protected journal cannot substitute the stage plan displayed to Human',()=>{
 for(const field of ['installerHash','sourceFreezeDigest','issuerSnapshotHash','trustRootsDigest','handoffEpoch']){
  const f=fixture(),result=structuredClone(f.files.get(f.base+'.result.json'));
  result.reviewedIntent.stageAuthorization[field]=field==='handoffEpoch'?2:digest('different');
  result.reviewedIntent.stageAuthorizationHash=digest(result.reviewedIntent.stageAuthorization);
  f.files.set(f.base+'.result.json',result);
  assert.throws(()=>inspectFirstTrustJournal(f.args),{code:'FIRST_TRUST_RESULT_CONFLICT'});
 }
});
test('legacy protected enrollment record without complete stage core is refused',()=>{
 const f=fixture(),result=structuredClone(f.files.get(f.base+'.result.json'));
 delete result.reviewedIntent.stageAuthorization;delete result.reviewedIntent.stageAuthorizationHash;
 f.files.set(f.base+'.result.json',result);
 assert.throws(()=>inspectFirstTrustJournal(f.args),{code:'FIRST_TRUST_RESULT_CONFLICT'});
});
