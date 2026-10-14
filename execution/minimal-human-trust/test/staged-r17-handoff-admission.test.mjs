import test from 'node:test';
import assert from 'node:assert/strict';
import {generateKeyPairSync,randomUUID} from 'node:crypto';
import {signed,exportPublicKey,digest,ROLES,ACTIONS} from '../src/lease-core.mjs';
import {runtimeVersion} from '../authority/runtime-manifest.mjs';
import {STAGE_CONSTRAINTS} from '../authority/stage-authorization.mjs';
import {EXACT_R17_MIGRATION_SCOPE} from '../migration/r17-one-time-recovery-admission.mjs';
import {inspectStagedR17HandoffAdmission} from '../release/staged-r17-handoff-admission.mjs';
import {validateHumanProposal,firstTrustReviewedIntent} from '../human/approval-policy.mjs';

const pair=()=>generateKeyPairSync('ed25519').privateKey;
const PLAN='/etc/minimal-human-trust/first-trust-publication.json';
const TX='/var/lib/minimal-human-trust/first-trust-publication';
const OLD='/var/lib/r16-owner/issuer/state.json';
const NEXT='/var/lib/minimal-human-trust/issuer/state.json';
function fixture(){
 const now=1792200000000,approvedAt=now-360000;
 const issuer=pair(),releaseKey=pair(),enroller=pair(),human=pair();
 const signers=Object.fromEntries(ROLES.map(role=>[role,pair()]));
 const peers=Object.fromEntries(ROLES.map(role=>[role,{id:'peer-'+role,publicKey:exportPublicKey(signers[role])}]));
 const grant=signed({schema:'r16.workspace.v1',id:'r16-projects-daily',version:1,
  createdAt:now-86400000,workspace:{id:'synthetic-workspace',
   root:'/home/jenn/AGENTS_OS_Workspace/projects',dev:1,ino:2},channel:'main',actions:ACTIONS,peers},issuer);
 const r15=signed({schema:'r16.release.v1',id:'r16-daily-20261012-r15',issuedAt:now-86400000,
  notAfter:now+86400000,formats:['r16.workspace.v1'],versions:EXACT_R17_MIGRATION_SCOPE.sourceVersions,
  actions:ACTIONS,permissionVersion:1},releaseKey);
 const priorPublicConfig={schema:'r16.runtime-configuration.v1',
  issuerPublicKey:exportPublicKey(issuer),releasePublicKey:exportPublicKey(releaseKey),
  grant,release:r15,peers,versions:r15.body.versions,channel:'main'};
 const roots={schema:'mht.trust-roots.v1',grantId:grant.body.id,
  issuerPublicKey:exportPublicKey(issuer),releasePublicKey:exportPublicKey(releaseKey),
  enrollmentAuthorityPublicKey:exportPublicKey(enroller),releaseHash:digest(r15),
  handoffHash:digest('initial-bootstrap-pin'),installationProfile:'production'};
 const artifacts=Object.fromEntries(ROLES.map(role=>[role,{schema:'r16.runtime-code.v1',role,
  entry:role+'/main.mjs',files:{[role+'/main.mjs']:digest('synthetic-byte-'+role)}}]));
 const versions=Object.fromEntries(ROLES.map(role=>[role,runtimeVersion(artifacts[role],role)]));
 const reviewManifest={schema:'r16.reviewed-installation.v1',releaseId:'r16-daily-20261012-r17',
  issuedAt:approvedAt-1000,notAfter:approvedAt+86400000,artifacts,
  localFiles:ROLES.map(role=>({role,artifactPath:role+'/main.mjs',
   path:'/opt/r16/releases/r16-daily-20261012-r17/'+role+'/main.mjs',sha256:artifacts[role].files[role+'/main.mjs']}))};
 const r17=signed({schema:'r16.release.v1',id:reviewManifest.releaseId,
  issuedAt:reviewManifest.issuedAt,notAfter:reviewManifest.notAfter,formats:['r16.workspace.v1'],
  versions,actions:ACTIONS,permissionVersion:1},releaseKey);
 const snapshot={schema:1,revision:4,maxNow:now-1000,data:{kind:'r16.issuer.v1',
  grants:[{grant,version:1,status:'ACTIVE',projects:EXACT_R17_MIGRATION_SCOPE.projects.map(row=>
   ({projectId:row.projectId,operationId:row.operationId,generation:row.generation,
    originalOperationHash:row.operationHash,outcome:'UNKNOWN'})),revocationAcks:[]}]}};
 const authorization={schema:'mht.first-trust-stage-authorization.v2',phase:'STAGE_ONLY',
  sourceReleaseId:r15.body.id,targetReleaseId:r17.body.id,grantId:grant.body.id,
  grantHash:digest(grant),grantVersion:1,r15PublicConfigDigest:digest(priorPublicConfig),
  reviewedManifestHash:digest(reviewManifest),recoveryEvidenceDigest:digest('historical-proof'),
  sourceFreezeDigest:digest('reviewed-source'),installerHash:digest('reviewed-installer'),
  issuerSnapshotHash:digest(snapshot.data),trustRootsDigest:digest(roots),
  stopEpoch:randomUUID(),handoffEpoch:1234,issuedAt:approvedAt-20000,expiresAt:approvedAt+60000,
  constraints:{...STAGE_CONSTRAINTS}};
 const plan={schema:'mht.first-trust-publisher-stage-plan.v2',authorization,humanProposalHash:digest('native-proposal')};
 const proposal=signed({schema:'mht.human-proposal.v1',action:'enroll_human',grantId:grant.body.id,
  expectedVersion:grant.body.version,expectedGrantHash:digest(grant),releaseId:r15.body.id,
  releaseHash:digest(r15),nonce:randomUUID(),issuedAt:authorization.issuedAt,expiresAt:authorization.expiresAt,
  target:{humanUid:1000,humanSubject:'local-human:1000',humanPublicKey:exportPublicKey(human),
   enrollmentExpiresAt:approvedAt+86400000,targetReleaseId:r17.body.id,reviewedManifestHash:digest(reviewManifest),
   stageAuthorizationHash:digest(authorization),stageAuthorization:authorization}},releaseKey);
 plan.humanProposalHash=digest(proposal);
 const policy={schema:'mht.human-pending-policy.v1',proposalHash:digest(proposal),grantId:grant.body.id,
  grantHash:digest(grant),grantVersion:1,releaseHash:digest(r15),releaseId:r15.body.id,
  humanPublicKey:exportPublicKey(human),workspaceId:grant.body.workspace.id,
  workspaceRoot:grant.body.workspace.root,workspaceDev:1,workspaceIno:2,installationProfile:'production'};
 const checked=validateHumanProposal({proposal,policy,roots,now:approvedAt});
 const osIntent={schema:'mht.human-os-intent.v1',proposalHash:plan.humanProposalHash,
  peerUid:1000,processStart:321,confirmedAt:approvedAt-1000,challengeHash:digest('fresh-native-challenge')};
 const osResult={ok:true,status:'APPROVED_NOT_APPLIED',firstTrustOsConfirmationOnly:true,
  proposalHash:plan.humanProposalHash,reviewedIntent:firstTrustReviewedIntent(checked),approval:null};
 const journalBase='/var/lib/minimal-human-trust/human-approval/'+plan.humanProposalHash;
 const intent={schema:'mht.first-trust-signer-intent.v1',approvedAt,planHash:digest(plan),
  stageAuthorizationHash:digest(authorization),phase:'STAGE_ONLY',
  reviewedManifestHash:authorization.reviewedManifestHash,sourceFreezeDigest:authorization.sourceFreezeDigest,
  installerHash:authorization.installerHash,r15PublicConfigDigest:authorization.r15PublicConfigDigest,
  recoveryEvidenceDigest:authorization.recoveryEvidenceDigest,humanApprovalReceiptHash:digest({osIntent,osResult}),
  stopEpoch:authorization.stopEpoch,handoffEpoch:authorization.handoffEpoch,stopProofs:null,
  stopRequiredBeforeHandoff:true,grantId:grant.body.id,
  twoReadOperationIds:EXACT_R17_MIGRATION_SCOPE.projects.map(row=>row.operationId),
  sourceReleaseId:r15.body.id,targetReleaseId:r17.body.id};
 const enrollment=signed({schema:'mht.human-enrollment.v1',enrolledAt:approvedAt,
  expiresAt:approvedAt+86400000,grantId:grant.body.id,grantHash:digest(grant),
  humanPublicKey:exportPublicKey(human),humanUid:1000,humanSubject:'local-human:1000',
  releaseId:r17.body.id,releaseHash:digest(r17)},enroller);
 const signedArtifacts={schema:'mht.first-trust-staged-signatures.v2',status:'SIGNED_STAGED_NOT_INSTALLED',
  oldReleaseId:r15.body.id,reviewedManifestHash:digest(reviewManifest),
  osApprovalReceiptHash:intent.humanApprovalReceiptHash,firstTrustAdmissionDigest:digest('native-stage-admission'),
  stageAuthorizationHash:digest(authorization),release:r17,enrollment,grantUnchanged:true,
  mayInstall:false,mayActivateBusiness:false,mayHandoffIssuer:false,maySettleUnknown:false};
 const result={schema:'mht.first-trust-publisher-result.v1',intentHash:digest(intent),signedArtifacts};
 const publicConfig={...priorPublicConfig,release:r17,versions};
 const revision=88;
 const delivery=signed({schema:'r16.configuration-delivery.v1',revision,issuedAt:now-1000,
  publicConfig,control:{grantId:grant.body.id,grantVersion:1,status:'ACTIVE',connectRequested:false}},issuer);
 const expectedResultsHashes=Object.fromEntries(ROLES.map(role=>[role,digest('role-results-'+role)]));
 const receipts=Object.fromEntries(ROLES.map(role=>[role,signed({schema:'mht.business-stopped.v2',role,
  peerId:peers[role].id,grantId:grant.body.id,releaseId:r17.body.id,revision,
  reviewDigest:authorization.reviewedManifestHash,stopEpoch:authorization.stopEpoch,
  issuedAt:now-1000,expiresAt:now+12000,stopped:true,inflight:0,
  unresolved:EXACT_R17_MIGRATION_SCOPE.projects.map(row=>row.operationId),grantVersion:1,
  releaseHash:digest(r17),runtimeVersion:versions[role],resultsHash:expectedResultsHashes[role]},signers[role])]));
 const handoff=signed({schema:'mht.issuer-handoff.v1',grantId:grant.body.id,grantHash:digest(grant),
  releaseHash:digest(r17),issuerSnapshotHash:authorization.issuerSnapshotHash,
  installationProfile:'production',epoch:authorization.handoffEpoch,mode:'recovery_only',oldWriterClosed:true,
  participantClosureHashes:Object.fromEntries(ROLES.map(role=>[role,digest(receipts[role])])),
  issuedAt:now-1000,expiresAt:now+20000},enroller);
 const files=new Map([[PLAN,plan],[TX+'/intent.json',intent],[TX+'/result.json',result],
  ['/etc/minimal-human-trust/human-pending.json',proposal],
  ['/etc/minimal-human-trust/human-policy.json',policy],
  [journalBase+'.intent.json',osIntent],[journalBase+'.result.json',osResult],
  [OLD,snapshot],[NEXT,structuredClone(snapshot)]]);
 const reads=[];
 const readProtected=file=>{
  reads.push(file);assert.ok(files.has(file),'only explicit fixed root paths are read: '+file);
  return Buffer.from(JSON.stringify(files.get(file)));
 };
 const args={priorPublicConfig,roots,reviewManifest,delivery,receipts,expectedRevision:revision,
  expectedResultsHashes,handoff,readProtected,
  readUnit:()=>({ActiveState:'inactive',SubState:'dead',MainPID:'0',UnitFileState:'masked'}),
  lockExists:()=>false,now,euid:0};
 return {args,files,reads,issuer,releaseKey,enroller,signers,authorization,plan,intent,result,r15,r17,snapshot,
  proposal,policy,osIntent,osResult,journalBase};
}
const inspect=f=>inspectStagedR17HandoffAdmission(f.args);
const reSign=(f,role,patch)=>{f.args.receipts[role]=signed({...f.args.receipts[role].body,...patch},f.signers[role]);};
test('historical stage plus real R17 STOP and fenced identical snapshots are inspection only',()=>{
 const f=fixture(),before=structuredClone([...f.files]),result=inspect(f);
 assert.ok(f.authorization.expiresAt<f.args.now);
 assert.equal(result.status,'STAGED_R17_STOP_AND_FENCED_OWNER_INSPECTED');
 assert.equal(result.stageAuthorizationHash,digest(f.authorization));
 assert.equal(result.handoffEpoch,1234);
 for(const field of ['mayStartIssuer','mayInstall','mayActivate','mayClearUnknown','mayReplayUnknown','mayRetireOwner','signerAuthority'])
  assert.equal(result[field],false);
 assert.deepEqual([...f.files],before);
});
test('ordinary user fails before even reading root stage state',()=>{
 const f=fixture();f.args.euid=1000;
 assert.throws(()=>inspect(f),{code:'ROOT_REQUIRED'});assert.equal(f.reads.length,0);
});
test('missing durable RESULT never admits stage-only or intent-only completion',()=>{
 const f=fixture();f.files.delete(TX+'/result.json');assert.throws(()=>inspect(f));
});
test('root stage plan, intent and result cannot be swapped independently',()=>{
 for(const change of [f=>{f.plan.humanProposalHash=digest('different');},
  f=>{f.intent.stageAuthorizationHash=digest('different');},
  f=>{f.result.intentHash=digest('different');},
  f=>{f.intent.approvedAt=f.args.now+1;}]){
  const f=fixture();change(f);assert.throws(()=>inspect(f));
 }
});
test('a staged artifact that claims activation or writer authority is refused',()=>{
 for(const field of ['mayInstall','mayActivateBusiness','mayHandoffIssuer','maySettleUnknown']){
  const f=fixture();f.result.signedArtifacts[field]=true;assert.throws(()=>inspect(f));
 }
});
test('untrusted root replacement cannot reuse the old stage authorization',()=>{
 const f=fixture();f.args.roots={...f.args.roots,enrollmentAuthorityPublicKey:exportPublicKey(pair())};
 assert.throws(()=>inspect(f),{code:'STAGED_HANDOFF_SOURCE_DRIFT'});
});
test('forged Release or enrollment signature never reaches STOP/handoff inspection',()=>{
 for(const field of ['release','enrollment']){
  const f=fixture();f.result.signedArtifacts[field].signature='A'.repeat(86);
  assert.throws(()=>inspect(f),{code:'BAD_SIGNATURE'});
 }
});
test('a valid new release signature cannot change exact reviewed versions or clocks',()=>{
 for(const patch of [{versions:{app:digest('foreign'),bridge:digest('foreign'),native:digest('foreign')}},
  {issuedAt:1792199638000},{notAfter:1792200000000+86400000}]){
  const f=fixture();f.result.signedArtifacts.release=signed({...f.r17.body,...patch},f.releaseKey);
  assert.throws(()=>inspect(f),{code:'STAGED_HANDOFF_RELEASE_DRIFT'});
 }
});
test('trusted enrollment signature must still bind the exact staged release and Grant',()=>{
 for(const patch of [{releaseHash:digest('different-release')},{grantHash:digest('different-grant')},
  {humanUid:0},{enrolledAt:1792199639999},{humanPublicKey:exportPublicKey(pair())},
  {expiresAt:1792199640000+2*86400000}]){
  const f=fixture();f.result.signedArtifacts.enrollment=signed({...f.result.signedArtifacts.enrollment.body,...patch},f.enroller);
  assert.throws(()=>inspect(f),{code:'STAGED_HANDOFF_ENROLLMENT_DRIFT'});
 }
});
test('stage alone without one authentic role STOP is never handoff admission',()=>{
 const f=fixture();delete f.args.receipts.bridge;assert.throws(()=>inspect(f));
});
test('R15 STOP cannot masquerade as the newly staged R17 role code',()=>{
 const f=fixture();reSign(f,'app',{releaseId:f.r15.body.id,releaseHash:digest(f.r15),runtimeVersion:f.r15.body.versions.app});
 assert.throws(()=>inspect(f),{code:'STOP_ROLE_MISMATCH'});
});
test('handoff requires fresh thirty-second proof window and no in-flight business',()=>{
 for(const patch of [{expiresAt:1792199999999},{issuedAt:1792199999999,expiresAt:1792200030000},
  {inflight:1},{stopped:false}]){
  const f=fixture();reSign(f,'native',patch);assert.throws(()=>inspect(f));
 }
});
test('STOP exact UNKNOWN identities and signed runtime/result bindings cannot drift',()=>{
 for(const patch of [{unresolved:[EXACT_R17_MIGRATION_SCOPE.projects[0].operationId,'foreign']},
  {runtimeVersion:digest('foreign')},{resultsHash:digest('foreign')},{stopEpoch:randomUUID()}]){
  const f=fixture();reSign(f,'bridge',patch);assert.throws(()=>inspect(f),{code:'STOP_ROLE_MISMATCH'});
 }
});
test('signed delivery with continuing business or another R17 revision is rejected',()=>{
 for(const patch of [{revision:89},{control:{grantId:'r16-projects-daily',grantVersion:1,status:'ACTIVE',connectRequested:true}}]){
  const f=fixture();f.args.delivery=signed({...f.args.delivery.body,...patch},f.issuer);
  assert.throws(()=>inspect(f),{code:'STOP_CLOUD_CONTROL'});
 }
});
test('signed handoff cannot substitute epoch, release, profile or final snapshot',()=>{
 for(const patch of [{epoch:1235},{releaseHash:digest('R15')},
  {installationProfile:'isolated'}]){
  const f=fixture();f.args.handoff=signed({...f.args.handoff.body,...patch},f.enroller);
  assert.throws(()=>inspect(f),{code:'STAGED_HANDOFF_EPOCH_OR_SNAPSHOT_DRIFT'});
 }
 const f=fixture();f.args.handoff=signed({...f.args.handoff.body,issuerSnapshotHash:digest('different')},f.enroller);
 assert.throws(()=>inspect(f),{code:'ISSUER_SNAPSHOT_CHANGED'});
});
test('signed oldWriterClosed does not override actual active or restartable Owner',()=>{
 for(const patch of [{ActiveState:'active',SubState:'running',MainPID:'77'},
  {UnitFileState:'enabled'},{UnitFileState:'disabled'}]){
  const f=fixture();f.args.readUnit=()=>({ActiveState:'inactive',SubState:'dead',MainPID:'0',UnitFileState:'masked',...patch});
  assert.throws(()=>inspect(f),{code:'OWNER_WRITER_STILL_ACTIVE'});
 }
});
test('live old or candidate ledger lock blocks the exclusive writer preflight',()=>{
 for(const path of ['/var/lib/r16-owner/issuer/.lock','/var/lib/minimal-human-trust/issuer/.lock']){
  const f=fixture();f.args.lockExists=p=>p===path;
  assert.throws(()=>inspect(f),{code:'ISSUER_WRITER_LOCK_PRESENT'});
 }
});
test('candidate snapshot drift or an old writer change during readback blocks handoff',()=>{
 const f=fixture();f.files.get(NEXT).revision++;
 assert.throws(()=>inspect(f),{code:'ISSUER_SNAPSHOT_CHANGED'});
 const g=fixture();let oldReads=0;const original=g.args.readProtected;
 g.args.readProtected=path=>{
  if(path===OLD&&++oldReads===2)g.snapshot.revision++;
  return original(path);
 };
 assert.throws(()=>inspect(g),{code:'ISSUER_SNAPSHOT_CHANGED'});
});
test('durable stage evidence changed during OS checks cannot be admitted',()=>{
 const f=fixture();f.args.readUnit=()=>{
  f.result.signedArtifacts.firstTrustAdmissionDigest=digest('changed-while-inspecting');
  return {ActiveState:'inactive',SubState:'dead',MainPID:'0',UnitFileState:'masked'};
 };
 assert.throws(()=>inspect(f),{code:'STAGED_HANDOFF_DURABLE_STATE_CHANGED'});
});
test('fresh final closed-state snapshots can differ from the earlier stage snapshot',()=>{
 const f=fixture();f.snapshot.data.closedForHandoff=true;f.snapshot.revision++;
 f.files.set(NEXT,structuredClone(f.snapshot));
 f.args.handoff=signed({...f.args.handoff.body,issuerSnapshotHash:digest(f.snapshot.data)},f.enroller);
 const result=inspect(f);
 assert.notEqual(result.issuerSnapshotHash,f.authorization.issuerSnapshotHash);
 assert.equal(result.issuerSnapshotHash,digest(f.snapshot.data));
});
test('stale or future final snapshot cannot substitute for fresh root readback',()=>{
 for(const maxNow of [1792200000000-30001,1792200000000+1]){
  const f=fixture();f.snapshot.maxNow=maxNow;f.files.get(NEXT).maxNow=maxNow;
  assert.throws(()=>inspect(f),{code:'STAGED_HANDOFF_SNAPSHOT_NOT_FRESH'});
 }
});
test('historical native proposal or durable OS journal substitution is rejected',()=>{
 const f=fixture();f.proposal.signature='A'.repeat(86);
 assert.throws(()=>inspect(f),{code:'STAGED_HANDOFF_HUMAN_PROPOSAL_DRIFT'});
 const g=fixture();g.osResult.reviewedIntent.stageAuthorization.installerHash=digest('another');
 assert.throws(()=>inspect(g));
});
test('expired R17 is never admitted for a present handoff even with fresh signed STOP',()=>{
 const f=fixture();f.args.now=f.r17.body.notAfter;
 assert.throws(()=>inspect(f),{code:'RELEASE_EXPIRED'});
});
test('fresh handoff proof cannot outlive the actual Human enrollment',()=>{
 const f=fixture();f.result.signedArtifacts.enrollment=signed({
  ...f.result.signedArtifacts.enrollment.body,expiresAt:f.args.now-1},f.enroller);
 assert.throws(()=>inspect(f),{code:'STAGED_HANDOFF_ENROLLMENT_DRIFT'});
});
test('old handoff signature is not a fresh same-epoch ceremony',()=>{
 const f=fixture();f.args.handoff=signed({...f.args.handoff.body,
  issuedAt:f.args.now-30001,expiresAt:f.args.now+1000},f.enroller);
 assert.throws(()=>inspect(f),{code:'STAGED_HANDOFF_EPOCH_OR_SNAPSHOT_DRIFT'});
});
test('historical OS receipt changed during Owner readback is never silently accepted',()=>{
 const f=fixture();f.args.readUnit=()=>{
  f.osIntent.challengeHash=digest('different-challenge');
  return {ActiveState:'inactive',SubState:'dead',MainPID:'0',UnitFileState:'masked'};
 };
 assert.throws(()=>inspect(f),{code:'STAGED_HANDOFF_DURABLE_STATE_CHANGED'});
});
