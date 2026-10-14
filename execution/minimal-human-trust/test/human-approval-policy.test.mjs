import test from 'node:test';
import assert from 'node:assert/strict';
import {generateKeyPairSync,randomUUID} from 'node:crypto';
import {signed,exportPublicKey,digest,ACTIONS} from '../src/lease-core.mjs';
import {validateHumanProposal,humanApprovalBody,firstTrustReviewedIntent,PROJECTS_ROOT} from '../human/approval-policy.mjs';
import {validateStageAuthorization,STAGE_CONSTRAINTS} from '../authority/stage-authorization.mjs';
const key=()=>generateKeyPairSync('ed25519').privateKey;
function fixture(action='revoke_grant',target={}){
 const issuer=key(),publisher=key(),enroller=key(),human=key(),now=1792000000000;
 const policy={schema:'mht.human-pending-policy.v1',proposalHash:'',grantId:action==='enroll_human'?'r16-projects-daily':'g1d-isolated-human',grantHash:digest('grant'),
  grantVersion:1,releaseHash:digest('release'),releaseId:action==='enroll_human'?'r16-daily-20261012-r15':'r16-daily-human-fixture',humanPublicKey:exportPublicKey(human),
  workspaceId:'projects-fixture',workspaceRoot:PROJECTS_ROOT,workspaceDev:1,workspaceIno:2,installationProfile:'isolated'};
 const roots={schema:'mht.trust-roots.v1',issuerPublicKey:exportPublicKey(issuer),releasePublicKey:exportPublicKey(publisher),
  enrollmentAuthorityPublicKey:exportPublicKey(enroller),handoffHash:digest('handoff'),grantId:policy.grantId,releaseHash:policy.releaseHash,installationProfile:'isolated'};
 const body={schema:'mht.human-proposal.v1',action,grantId:policy.grantId,expectedVersion:1,expectedGrantHash:policy.grantHash,
  releaseId:policy.releaseId,releaseHash:policy.releaseHash,nonce:randomUUID(),issuedAt:now-1000,expiresAt:now+60000,target};
 const proposal=signed(body,publisher);policy.proposalHash=digest(proposal);
 return {proposal,policy,roots,now,publisher,human};
}
const rewrite=(f,patch)=>{f.proposal=signed({...f.proposal.body,...patch},f.publisher);f.policy.proposalHash=digest(f.proposal);return f;};
function enrollmentTarget(f,reviewedManifestHash=digest('reviewed-R17')){
 const p=f.proposal.body;
 const stageAuthorization={schema:'mht.first-trust-stage-authorization.v2',phase:'STAGE_ONLY',
  sourceReleaseId:p.releaseId,targetReleaseId:'r16-daily-20261012-r17',grantId:p.grantId,
  grantHash:p.expectedGrantHash,grantVersion:p.expectedVersion,
  r15PublicConfigDigest:digest('public-config'),reviewedManifestHash,
  recoveryEvidenceDigest:digest('evidence'),sourceFreezeDigest:digest('source-freeze'),
  installerHash:digest('installer'),issuerSnapshotHash:digest('issuer-snapshot'),trustRootsDigest:digest(f.roots),
  stopEpoch:randomUUID(),handoffEpoch:1,issuedAt:p.issuedAt,expiresAt:p.expiresAt,
  constraints:{...STAGE_CONSTRAINTS}};
 return {humanUid:1000,humanSubject:'local-human:1000',humanPublicKey:f.policy.humanPublicKey,
  enrollmentExpiresAt:f.now+86400000,targetReleaseId:stageAuthorization.targetReleaseId,
  reviewedManifestHash,stageAuthorization,stageAuthorizationHash:digest(stageAuthorization)};
}
test('exact revoke proof pins target/version/hash/nonce and grants no new capability',()=>{
 const f=fixture(),checked=validateHumanProposal(f),approval=humanApprovalBody(checked,{now:f.now});
 assert.equal(approval.schema,'mht.human-authorization.v1');assert.equal(approval.action,'revoke_grant');
 assert.equal(approval.expectedGrantHash,f.policy.grantHash);assert.equal(approval.nonce,f.proposal.body.nonce);
});
test('plain uid, unknown action and unsigned caller target cannot produce approval',()=>{
 const f=fixture();assert.throws(()=>validateHumanProposal({...f,proposal:{uid:1000}}));
 assert.throws(()=>validateHumanProposal(rewrite(f,{action:'run_shell'})));
});
test('publisher impostor and protected proposal digest mismatch reject',()=>{
 const f=fixture();assert.throws(()=>validateHumanProposal({...f,proposal:signed(f.proposal.body,key())}));
 f.policy.proposalHash=digest('another');assert.throws(()=>validateHumanProposal(f));
});
test('grant, version, exactrelease and currentgrant hash substitutions reject',()=>{
 for(const patch of [{grantId:'foreign'},{expectedVersion:2},{expectedGrantHash:digest('foreign')},
 {releaseHash:digest('foreign')},{releaseId:'foreign'}])assert.throws(()=>validateHumanProposal(rewrite(fixture(),patch)));
});
test('fresh exact nonce expires while human is confirming',()=>{
 const f=fixture(),checked=validateHumanProposal(f);
 assert.throws(()=>humanApprovalBody(checked,{now:f.proposal.body.expiresAt}));
 assert.throws(()=>validateHumanProposal({...f,now:f.now+300001}));
});
test('create grant constrained to projects real scope and existing ProjectForge actions only',()=>{
 const target={workspaceId:'projects-fixture',workspaceRoot:PROJECTS_ROOT,channel:'main',actions:ACTIONS};
 const f=fixture('create_grant',target);assert.equal(humanApprovalBody(validateHumanProposal(f),{now:f.now}).schema,'mht.human-reviewed-change.v1');
 for(const patch of [{workspaceRoot:'/etc'},{workspaceRoot:PROJECTS_ROOT+'/../secrets'},{channel:'side'},
 {actions:['shell']},{actions:['read_code','read_code']}])assert.throws(()=>validateHumanProposal(fixture('create_grant',{...target,...patch})));
});
test('trust replacement is explicit oldroot to newroot and cannot expand permissions',()=>{
 const f=fixture('change_trust');rewrite(f,{target:{oldRootHash:digest(f.roots),newRootHash:digest('reviewed-newroots'),permissionsUnchanged:true}});
 assert.equal(humanApprovalBody(validateHumanProposal(f),{now:f.now}).schema,'mht.human-reviewed-change.v1');
 rewrite(f,{target:{...f.proposal.body.target,permissionsUnchanged:false}});assert.throws(()=>validateHumanProposal(f));
});
test('enrollment proposal is exact identity approval artifact, never an automatic enrollment signature',()=>{
 const f=fixture('enroll_human');rewrite(f,{target:enrollmentTarget(f,digest('exact-R17-reviewed-source'))});
 const checked=validateHumanProposal(f);
 const result=humanApprovalBody(checked,{now:f.now});assert.equal(result.schema,'mht.human-reviewed-change.v1');
 const first=firstTrustReviewedIntent(checked);
 assert.equal(first.targetReleaseId,'r16-daily-20261012-r17');
 assert.equal(first.reviewedManifestHash,f.proposal.body.target.reviewedManifestHash);
 assert.deepEqual(first.stageAuthorization,checked.summary.target.stageAuthorization);
 assert.equal(first.stageAuthorizationHash,digest(first.stageAuthorization));
 assert.equal(checked.summary.issuedAt,f.proposal.body.issuedAt);
 assert.equal(checked.summary.expiresAt,f.proposal.body.expiresAt);
 assert.ok(Buffer.byteLength(JSON.stringify({...checked.summary,confirmationChallenge:'f'.repeat(64)}))<8192);
 assert.ok(Buffer.byteLength(JSON.stringify({status:'CONFIRM_EXACT_TARGET',proposalHash:checked.proposalHash,
  challenge:'f'.repeat(64),summary:checked.summary}))<16384);
 assert.equal(first.mayInstall,false);
 assert.equal(first.maySignRelease,false);
 assert.equal(first.mayHandoffIssuer,false);
 rewrite(f,{target:{...f.proposal.body.target,humanPublicKey:exportPublicKey(key())}});assert.throws(()=>validateHumanProposal(f));
});

test('first enrollment can only target exact R17 reviewed manifest and Human key',()=>{
 const base=fixture('enroll_human');
 const target=enrollmentTarget(base);
 for(const change of [
   {targetReleaseId:'r16-daily-20261012-r18'},
   {reviewedManifestHash:'0'.repeat(63)},
   {humanUid:0},{humanSubject:'agent-user'},
   {enrollmentExpiresAt:base.now-1},
 ]){
   const f=fixture('enroll_human');
   rewrite(f,{target:{...target,humanPublicKey:f.policy.humanPublicKey,...change}});
   assert.throws(()=>validateHumanProposal(f));
 }
 assert.throws(()=>firstTrustReviewedIntent(validateHumanProposal(fixture())));
});

test('enrollment rejects hash-only or missing stage authorization before confirmation',()=>{
 for(const field of ['stageAuthorization','stageAuthorizationHash']){
  const f=fixture('enroll_human'),target=enrollmentTarget(f);delete target[field];
  assert.throws(()=>validateHumanProposal(rewrite(f,{target})));
 }
});
test('stage authorization refuses hidden field or source substitution despite a fresh publisher signature',()=>{
 for(const patch of [{stageAuthorizationHash:digest('another-plan')},
  {stageAuthorization:{extra:'hidden'}}]){
  const f=fixture('enroll_human');
  assert.throws(()=>validateHumanProposal(rewrite(f,{target:{...enrollmentTarget(f),...patch}})));
 }
 for(const field of ['sourceFreezeDigest','installerHash','issuerSnapshotHash','recoveryEvidenceDigest',
  'r15PublicConfigDigest','trustRootsDigest','stopEpoch','handoffEpoch']){
  const f=fixture('enroll_human'),target=enrollmentTarget(f);
  target.stageAuthorization[field]=field==='handoffEpoch'?2:field==='stopEpoch'?randomUUID():digest('substitute');
  // The outer signed proposal still commits the original plan hash.
  assert.throws(()=>validateHumanProposal(rewrite(f,{target})));
 }
});
test('stage authorization rejects phase, permissions, clocks, grant and epoch drift even with updated digest',()=>{
 const changes=[{phase:'ACTIVATE'},{sourceReleaseId:'r16-daily-20261012-r14'},
  {targetReleaseId:'r16-daily-20261012-r18'},{grantId:'foreign'},{grantHash:digest('other-grant')},
  {grantVersion:2},{reviewedManifestHash:digest('other-review')},
  {issuedAt:1791999998999},{expiresAt:1792000059999},{handoffEpoch:0},
  {stopEpoch:'not-a-uuid'},
  {installerHash:'a'.repeat(63)},{sourceFreezeDigest:null},{trustRootsDigest:digest('other-roots')}];
 for(const patch of changes){
  const f=fixture('enroll_human'),target=enrollmentTarget(f);
  Object.assign(target.stageAuthorization,patch);target.stageAuthorizationHash=digest(target.stageAuthorization);
  assert.throws(()=>validateHumanProposal(rewrite(f,{target})));
 }
 for(const field of Object.keys(STAGE_CONSTRAINTS)){
  const f=fixture('enroll_human'),target=enrollmentTarget(f);
  target.stageAuthorization.constraints[field]=!STAGE_CONSTRAINTS[field];
  target.stageAuthorizationHash=digest(target.stageAuthorization);
  assert.throws(()=>validateHumanProposal(rewrite(f,{target})));
 }
});
test('changing the enrollment root needs a new Human-bound root digest even with a trusted new proposal',()=>{
 const f=fixture('enroll_human'),target=enrollmentTarget(f);
 f.roots={...f.roots,enrollmentAuthorityPublicKey:exportPublicKey(key())};
 assert.throws(()=>validateHumanProposal(rewrite(f,{target})),{code:'HUMAN_STAGE_ROOTS_CHANGED'});
});
test('stage core time bounds reject future, expired or excessive windows',()=>{
 const f=fixture('enroll_human'),core=enrollmentTarget(f).stageAuthorization;
 assert.equal(validateStageAuthorization(core,{now:f.now}),core);
 for(const [patch,now] of [[{issuedAt:f.now+1},f.now],[{},core.expiresAt],
  [{expiresAt:core.issuedAt+300001},f.now],[{handoffEpoch:Number.MAX_SAFE_INTEGER+1},f.now]]){
  assert.throws(()=>validateStageAuthorization({...core,...patch},{now}));
 }
});
