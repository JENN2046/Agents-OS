import test from 'node:test';
import assert from 'node:assert/strict';
import {generateKeyPairSync,randomUUID} from 'node:crypto';
import {signed,exportPublicKey,digest,ROLES,ACTIONS} from '../src/lease-core.mjs';
import {runtimeVersion} from '../authority/runtime-manifest.mjs';
import {STAGE_CONSTRAINTS} from '../authority/stage-authorization.mjs';
import {EXACT_R17_MIGRATION_SCOPE} from '../migration/r17-one-time-recovery-admission.mjs';
import {inspectStagedR17HandoffAdmission} from '../release/staged-r17-handoff-admission.mjs';
import {validateHumanProposal,firstTrustReviewedIntent} from '../human/approval-policy.mjs';

import {stagedHandoffFixture as fixture} from './fixtures/staged-handoff-fixture.mjs';
const PLAN='/etc/minimal-human-trust/first-trust-publication.json';
const TX='/var/lib/minimal-human-trust/first-trust-publication';
const OLD='/var/lib/r16-owner/issuer/state.json';
const NEXT='/var/lib/minimal-human-trust/issuer/state.json';
const pair=()=>generateKeyPairSync('ed25519').privateKey;
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
