// Synthetic isolated integration only: migration's original production hash-pinned
// proofs cannot be forged with test keys. ONLY that migration inspector is mocked
// in a child test process. Stage, signed Human proposal, public Release/Grant and
// protected journal validators are the actual source modules; no service runs.
import test from 'node:test';
import assert from 'node:assert/strict';
import {spawnSync} from 'node:child_process';

const url=relative=>new URL(relative,import.meta.url).href;
const fixtureCode=`
import assert from 'node:assert/strict';
import {mock} from 'node:test';
import {generateKeyPairSync,randomUUID,createHash} from 'node:crypto';
import {digest,signed,exportPublicKey,ACTIONS,ROLES} from ${JSON.stringify(url('../src/lease-core.mjs'))};
import {validateHumanProposal,firstTrustReviewedIntent,PROJECTS_ROOT} from ${JSON.stringify(url('../human/approval-policy.mjs'))};
import {runtimeVersion} from ${JSON.stringify(url('../authority/runtime-manifest.mjs'))};
import {STAGE_CONSTRAINTS} from ${JSON.stringify(url('../authority/stage-authorization.mjs'))};
let migrationCalls=0;
mock.module(${JSON.stringify(url('../migration/r17-one-time-recovery-admission.mjs'))},{namedExports:{
 inspectReviewedR17MigrationEvidence:(evidence,reviewHash,verifyCrownCall)=>{
  migrationCalls++;
  assert.equal(reviewHash,digest(evidence.reviewManifest));
  assert.equal(typeof verifyCrownCall,'function');
  return {status:'PENDING_TRUSTED_QUIESCENCE_AND_SIGNER',other_projects_closed:true,
   old_release:'r16-daily-20261012-r15',proposed_release:'r16-daily-20261012-r17',
   grant_id:'r16-projects-daily',review_sha256:reviewHash,
   exact_owner_snapshot_digest:digest({issuerState:evidence.issuerState,ownerConfiguration:{synthetic:true}}),
   operations:[
    {project_id:'p2vox',operation_id:'c434da49-055a-43dc-a3e3-695cce137909',generation:30,
     operation_sha256:digest('synthetic-proof-p2vox'),action:'find_symbol',outcome:'UNRESOLVED',replay_allowed:false,original_result_available:false},
    {project_id:'pmog2',operation_id:'d0364f8b-3a68-4ca2-a396-7953b29cee4c',generation:38,
     operation_sha256:digest('synthetic-proof-pmog2'),action:'find_symbol',outcome:'UNRESOLVED',replay_allowed:false,original_result_available:false},
   ]};
 }
}});
const {inspectPublisherInputs}=await import(${JSON.stringify(url('../release/publisher-inputs.mjs'))});
const sha=bytes=>createHash('sha256').update(bytes).digest('hex');
const key=()=>generateKeyPairSync('ed25519').privateKey;
const releaseKey=key(),issuerKey=key(),humanKey=key(),enrollmentKey=key(),now=1792000000000;
const peers=Object.fromEntries(ROLES.map(role=>[role,{id:'synthetic-'+role,publicKey:exportPublicKey(key())}]));
const crownPath='app/upstream/src/project-forge-crown-transport.mjs';
const crownBytes=Buffer.from('synthetic pinned Crown module, not executed');
const r15AppManifest={schema:'r16.runtime-code.v1',role:'app',entry:crownPath,files:{[crownPath]:sha(crownBytes)}};
const versions={app:runtimeVersion(r15AppManifest,'app'),bridge:digest('synthetic-r15-bridge'),native:digest('synthetic-r15-native')};
const release=signed({schema:'r16.release.v1',id:'r16-daily-20261012-r15',issuedAt:now-86400000,
 notAfter:now-1000,formats:['r16.workspace.v1'],versions,actions:ACTIONS,permissionVersion:1},releaseKey);
const grant=signed({schema:'r16.workspace.v1',id:'r16-projects-daily',version:1,createdAt:now-86400000,
 workspace:{id:'ws_8c7dd971e518',root:PROJECTS_ROOT,dev:1,ino:2},actions:ACTIONS,channel:'main',peers},issuerKey);
const roots={schema:'mht.trust-roots.v1',grantId:grant.body.id,issuerPublicKey:exportPublicKey(issuerKey),
 releasePublicKey:exportPublicKey(releaseKey),enrollmentAuthorityPublicKey:exportPublicKey(enrollmentKey),
 releaseHash:digest(release),handoffHash:digest('not-issued-synthetic-handoff'),installationProfile:'isolated'};
const publicConfig={schema:'r16.runtime-configuration.v1',issuerPublicKey:roots.issuerPublicKey,
 releasePublicKey:roots.releasePublicKey,release,grant,versions,peers,channel:'main'};
const stagedFiles=new Map(),artifacts={},localFiles=[];
for(const role of ROLES){
 const entry=role+'/main.mjs',bytes=Buffer.from('synthetic staged '+role),hash=sha(bytes);
 artifacts[role]={schema:'r16.runtime-code.v1',role,entry,files:{[entry]:hash}};
 const path='/opt/r16/releases/r16-daily-20261012-r17/'+entry;
 localFiles.push({role,artifactPath:entry,path,sha256:hash});stagedFiles.set(path,bytes);
}
const reviewManifest={schema:'r16.reviewed-installation.v1',releaseId:'r16-daily-20261012-r17',
 issuedAt:now-1000,notAfter:now+86400000,artifacts,localFiles};
const sourceFreeze={schema:'mht.first-trust-code-freeze.v1',sourceCommit:'a'.repeat(40),files:{}};
const installerBytes=Buffer.from('// synthetic stage-only installer fixture');
const old={publicConfiguration:publicConfig,reviewManifest,issuerState:{kind:'r16.issuer.v1',synthetic:true},now:now-120000};
const evidence={schema:'mht.first-trust-stage-evidence.v2',existingR15Evidence:old};
const core={schema:'mht.first-trust-stage-authorization.v2',phase:'STAGE_ONLY',sourceReleaseId:release.body.id,
 targetReleaseId:reviewManifest.releaseId,grantId:grant.body.id,grantHash:digest(grant),grantVersion:1,
 r15PublicConfigDigest:digest(publicConfig),reviewedManifestHash:digest(reviewManifest),
 recoveryEvidenceDigest:digest(old),sourceFreezeDigest:digest(sourceFreeze),installerHash:sha(installerBytes),
 issuerSnapshotHash:digest(old.issuerState),trustRootsDigest:digest(roots),stopEpoch:randomUUID(),handoffEpoch:1,
 issuedAt:now-20000,expiresAt:now+60000,constraints:{...STAGE_CONSTRAINTS}};
const body={schema:'mht.human-proposal.v1',action:'enroll_human',grantId:grant.body.id,expectedVersion:1,
 expectedGrantHash:digest(grant),releaseId:release.body.id,releaseHash:digest(release),nonce:randomUUID(),
 issuedAt:core.issuedAt,expiresAt:core.expiresAt,target:{humanUid:1000,humanSubject:'local-human:1000',
 humanPublicKey:exportPublicKey(humanKey),enrollmentExpiresAt:now+86400000,
 targetReleaseId:reviewManifest.releaseId,reviewedManifestHash:digest(reviewManifest),
 stageAuthorizationHash:digest(core),stageAuthorization:structuredClone(core)}};
let proposal=signed(body,releaseKey);
const policy={schema:'mht.human-pending-policy.v1',proposalHash:digest(proposal),grantId:grant.body.id,
 grantHash:digest(grant),grantVersion:1,releaseHash:digest(release),releaseId:release.body.id,
 humanPublicKey:exportPublicKey(humanKey),workspaceId:'ws_8c7dd971e518',workspaceRoot:PROJECTS_ROOT,
 workspaceDev:1,workspaceIno:2,installationProfile:'isolated'};
const journal=new Map();
let firstTrust={proposal,policy,trustRoots:roots,sourceRelease:release,sourceGrant:grant,
 reviewManifest,now,readProtected:file=>{
  assert.ok(journal.has(file),'synthetic root journal missing');return Buffer.from(JSON.stringify(journal.get(file)));
 },isInstalled:()=>false};
const plan={schema:'mht.first-trust-publisher-stage-plan.v2',authorization:core,humanProposalHash:policy.proposalHash};
function journalize(){
 const checked=validateHumanProposal({proposal:firstTrust.proposal,policy,roots,now});
 const base='/var/lib/minimal-human-trust/human-approval/'+policy.proposalHash;
 journal.clear();
 journal.set(base+'.intent.json',{schema:'mht.human-os-intent.v1',proposalHash:policy.proposalHash,
 peerUid:1000,processStart:321,confirmedAt:now-1000,challengeHash:digest('synthetic-fresh-challenge')});
 journal.set(base+'.result.json',{ok:true,status:'APPROVED_NOT_APPLIED',firstTrustOsConfirmationOnly:true,
 proposalHash:policy.proposalHash,reviewedIntent:firstTrustReviewedIntent(checked),approval:null});
}
function resignChangedCore(){
 body.target.stageAuthorization=structuredClone(core);body.target.stageAuthorizationHash=digest(core);
 proposal=signed(body,releaseKey);firstTrust.proposal=proposal;policy.proposalHash=digest(proposal);
 plan.humanProposalHash=policy.proposalHash;journalize();
}
journalize();
const args={plan,roots,publicConfig,evidence,firstTrust,verifyCrownCall:()=>({synthetic:true}),now};
`;
function scenario(name,code){
 test(name,()=>{
  const child=spawnSync(process.execPath,['--experimental-test-module-mocks','--input-type=module','-e',fixtureCode+'\n'+code+'\nconsole.log("SYNTHETIC_TEST_PASS");'],
    {encoding:'utf8',timeout:15000,maxBuffer:262144});
  assert.equal(child.status,0,child.stderr||child.stdout);
  assert.match(child.stdout,/SYNTHETIC_TEST_PASS/);
 });
}
scenario('synthetic migration seam: stage-only actual Human/core admission accepts a 120-second snapshot without STOP',`
const result=inspectPublisherInputs(args);
assert.equal(result.status,'PREPARED_FOR_SINGLE_USE_STAGE_ONLY_SIGNER');
assert.equal(result.stopped,null);assert.equal(result.stopEvidenceRequiredBeforeHandoff,true);
assert.equal(result.maySign,false);assert.equal(result.mayInstall,false);assert.equal(result.mayRetireOwner,false);
assert.equal(result.admission.maySignRelease,false);assert.equal(result.admission.mayActivateBusiness,false);
assert.equal(result.admission.maySettleUnknown,false);assert.equal(result.admission.signerAuthority,false);
assert.deepEqual(result.authorization,body.target.stageAuthorization);assert.equal(migrationCalls,1);
`);
scenario('stage publication rejects future, expired, overlong or different-phase Human core',`
for(const patch of [{issuedAt:now+1},{expiresAt:now},{issuedAt:now-300001,expiresAt:now+1},{phase:'ACTIVATE'}]){
 const saved=structuredClone(core);Object.assign(core,patch);
 assert.throws(()=>inspectPublisherInputs(args),{code:'STAGE_AUTHORIZATION_REJECTED'});
 Object.assign(core,saved);
}
assert.equal(migrationCalls,0);
`);
scenario('stage publication refuses any installation or handoff capability in its authorization',`
for(const flag of ['mayInstall','mayActivateBusiness','mayHandoffIssuer','maySettleUnknown']){
 core.constraints[flag]=true;
 assert.throws(()=>inspectPublisherInputs(args),{code:'STAGE_AUTHORIZATION_REJECTED'});
 core.constraints[flag]=false;
}
for(const flag of ['requireSignedThreeRoleStop','requireProtectedSameEpochIssuerSnapshot','requireOldWriterFenced']){
 core.constraints[flag]=false;
 assert.throws(()=>inspectPublisherInputs(args),{code:'STAGE_AUTHORIZATION_REJECTED'});
 core.constraints[flag]=true;
}
assert.equal(migrationCalls,0);
`);
scenario('stage-only evidence cannot smuggle a claimed STOP or an activation field',`
for(const field of ['stopReceipts','cloudDelivery','mayInstall']){
 evidence[field]=true;
 assert.throws(()=>inspectPublisherInputs(args),{code:'PUBLISHER_STAGE_EVIDENCE_SHAPE'});
 delete evidence[field];
}
assert.equal(migrationCalls,0);
`);
scenario('publisher-only installer, source-freeze or handoff changes cannot override signed Human intent',`
for(const field of ['installerHash','sourceFreezeDigest','handoffEpoch']){
 const saved=core[field];core[field]=field==='handoffEpoch'?2:digest('foreign-'+field);
 assert.throws(()=>inspectPublisherInputs(args),{code:'PUBLISHER_FIRST_TRUST_MISSING'});
 core[field]=saved;
}
`);
scenario('altered snapshot bytes or a replaced proposal hash are rejected',`
old.issuerState.extra='tampered';
assert.throws(()=>inspectPublisherInputs(args),{code:'PUBLISHER_SOURCE_DRIFT'});delete old.issuerState.extra;
plan.humanProposalHash=digest('different-native-approval');
assert.throws(()=>inspectPublisherInputs(args),{code:'PUBLISHER_SOURCE_DRIFT'});
assert.equal(migrationCalls,0);
`);
scenario('frozen evidence older than five minutes or future evidence remains rejected even if Human re-signs it',`
for(const time of [now-300001,now+1]){
 old.now=time;core.recoveryEvidenceDigest=digest(old);resignChangedCore();
 assert.throws(()=>inspectPublisherInputs(args),{code:'PUBLISHER_SNAPSHOT_NOT_FRESH'});
}
assert.equal(migrationCalls,0);
`);
scenario('real Human proposal cryptography is enforced before the synthetic migration seam',`
firstTrust.proposal={...proposal,signature:'A'.repeat(86)};
policy.proposalHash=digest(firstTrust.proposal);plan.humanProposalHash=policy.proposalHash;
assert.throws(()=>inspectPublisherInputs(args),{code:'BAD_SIGNATURE'});
assert.equal(migrationCalls,0);
`);
scenario('root pin drift and missing protected Human journal cannot be repaired by a JSON stage plan',`
const original=roots.releasePublicKey;roots.releasePublicKey=exportPublicKey(key());
assert.throws(()=>inspectPublisherInputs(args));roots.releasePublicKey=original;
journal.clear();assert.throws(()=>inspectPublisherInputs(args),/synthetic root journal missing/);
assert.equal(migrationCalls,0);
`);

scenario('synthetic migration seam: actual R17 and Enrollment cryptography remains staged and exact-core bound',`
const {signFirstTrustRecoveryArtifacts}=await import(${JSON.stringify(url('../release/first-trust-release-builder.mjs'))});
const {validateStagedPublisherResult}=await import(${JSON.stringify(url('../release/publisher-once.mjs'))});
const {verified}=await import(${JSON.stringify(url('../src/lease-core.mjs'))});
const inspected=inspectPublisherInputs(args);
let signGuards=0;
const result=signFirstTrustRecoveryArtifacts({firstTrust,existingR15Evidence:old,verifyCrownCall:args.verifyCrownCall,
 releaseSigningKey:releaseKey,enrollmentSigningKey:enrollmentKey,now,
 guard:()=>{signGuards++;},
 readFile:path=>{assert.ok(stagedFiles.has(path));return stagedFiles.get(path);}});
assert.equal(signGuards,2);
assert.equal(result.schema,'mht.first-trust-staged-signatures.v2');
assert.equal(result.status,'SIGNED_STAGED_NOT_INSTALLED');
assert.equal(result.stageAuthorizationHash,digest(core));
for(const flag of ['mayInstall','mayActivateBusiness','mayHandoffIssuer','maySettleUnknown'])assert.equal(result[flag],false);
const releaseBody=verified(result.release,roots.releasePublicKey,'r16.release.v1');
const enrollment=verified(result.enrollment,roots.enrollmentAuthorityPublicKey,'mht.human-enrollment.v1');
assert.equal(releaseBody.id,'r16-daily-20261012-r17');
assert.equal(enrollment.releaseHash,digest(result.release));
assert.equal(enrollment.humanPublicKey,body.target.humanPublicKey);
assert.equal(enrollment.expiresAt,body.target.enrollmentExpiresAt);
assert.equal(validateStagedPublisherResult(result,{pub:publicConfig,roots,admission:inspected,reviewManifest,now}),true);
const changed={...result,stageAuthorizationHash:digest('another-human-core')};
assert.throws(()=>validateStagedPublisherResult(changed,{pub:publicConfig,roots,admission:inspected,reviewManifest,now}),{code:'PUBLISHER_OUTPUT_SCOPE'});
`);
scenario('fresh authority refusal immediately before either signature never returns a staged result',`
const {signFirstTrustRecoveryArtifacts}=await import(${JSON.stringify(url('../release/first-trust-release-builder.mjs'))});
for(const stopAt of [1,2]){
 let guards=0,reads=0;
 const immutableBefore=digest({old,publicConfig,core});
 assert.throws(()=>signFirstTrustRecoveryArtifacts({firstTrust,existingR15Evidence:old,verifyCrownCall:args.verifyCrownCall,
  releaseSigningKey:releaseKey,enrollmentSigningKey:enrollmentKey,now,
  readFile:path=>{reads++;return stagedFiles.get(path);},guard:()=>{if(++guards===stopAt)throw Object.assign(Error('accepted source changed'),{code:'SOURCE19_ACCEPTED_DELIVERY_NOT_PINNED'});}}),{code:'SOURCE19_ACCEPTED_DELIVERY_NOT_PINNED'});
 assert.equal(guards,stopAt);assert.equal(reads,stagedFiles.size);assert.equal(digest({old,publicConfig,core}),immutableBefore);
}
`);
scenario('synthetic migration seam: wrong signing keys and incomplete final file coverage cannot produce staged signatures',`
const {signFirstTrustRecoveryArtifacts}=await import(${JSON.stringify(url('../release/first-trust-release-builder.mjs'))});
const signArgs={firstTrust,existingR15Evidence:old,verifyCrownCall:args.verifyCrownCall,
 releaseSigningKey:releaseKey,enrollmentSigningKey:enrollmentKey,now,
 readFile:path=>stagedFiles.get(path)};
assert.throws(()=>signFirstTrustRecoveryArtifacts({...signArgs,enrollmentSigningKey:key()}),{code:'FIRST_TRUST_KEY_ORIGIN'});
assert.throws(()=>signFirstTrustRecoveryArtifacts({...signArgs,releaseSigningKey:key()}),{code:'FIRST_TRUST_KEY_ORIGIN'});
reviewManifest.localFiles.pop();core.reviewedManifestHash=digest(reviewManifest);
body.target.reviewedManifestHash=core.reviewedManifestHash;core.recoveryEvidenceDigest=digest(old);resignChangedCore();
let reads=0;assert.throws(()=>signFirstTrustRecoveryArtifacts({...signArgs,readFile:()=>{reads++;return Buffer.from('foreign');}}),{code:'FIRST_TRUST_FILE_COVERAGE'});
assert.equal(reads,0);
`);

scenario('protected enrollment-root substitution fails the complete Human-approved trust-root digest',`
roots.enrollmentAuthorityPublicKey=exportPublicKey(key());
assert.throws(()=>inspectPublisherInputs(args),{code:'PUBLISHER_SOURCE_DRIFT'});
assert.equal(migrationCalls,0);
`);
