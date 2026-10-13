import test from 'node:test';
import assert from 'node:assert/strict';
import {generateKeyPairSync,randomUUID} from 'node:crypto';
import {signed,exportPublicKey,digest,ACTIONS} from '../src/lease-core.mjs';
import {validateHumanProposal,humanApprovalBody,firstTrustReviewedIntent,PROJECTS_ROOT} from '../human/approval-policy.mjs';
const key=()=>generateKeyPairSync('ed25519').privateKey;
function fixture(action='revoke_grant',target={}){
 const issuer=key(),publisher=key(),enroller=key(),human=key(),now=1792000000000;
 const policy={schema:'mht.human-pending-policy.v1',proposalHash:'',grantId:'g1d-isolated-human',grantHash:digest('grant'),
  grantVersion:1,releaseHash:digest('release'),releaseId:'r16-daily-human-fixture',humanPublicKey:exportPublicKey(human),
  workspaceId:'projects-fixture',workspaceRoot:PROJECTS_ROOT,workspaceDev:1,workspaceIno:2,installationProfile:'isolated'};
 const roots={schema:'mht.trust-roots.v1',issuerPublicKey:exportPublicKey(issuer),releasePublicKey:exportPublicKey(publisher),
  enrollmentAuthorityPublicKey:exportPublicKey(enroller),handoffHash:digest('handoff'),grantId:policy.grantId,releaseHash:policy.releaseHash,installationProfile:'isolated'};
 const body={schema:'mht.human-proposal.v1',action,grantId:policy.grantId,expectedVersion:1,expectedGrantHash:policy.grantHash,
  releaseId:policy.releaseId,releaseHash:policy.releaseHash,nonce:randomUUID(),issuedAt:now-1000,expiresAt:now+60000,target};
 const proposal=signed(body,publisher);policy.proposalHash=digest(proposal);
 return {proposal,policy,roots,now,publisher,human};
}
const rewrite=(f,patch)=>{f.proposal=signed({...f.proposal.body,...patch},f.publisher);f.policy.proposalHash=digest(f.proposal);return f;};
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
 const f=fixture('enroll_human');rewrite(f,{target:{humanUid:1000,humanSubject:'local-human:1000',humanPublicKey:f.policy.humanPublicKey,enrollmentExpiresAt:f.now+86400000,targetReleaseId:'r16-daily-20261012-r17',reviewedManifestHash:digest('exact-R17-reviewed-source')}});
 const checked=validateHumanProposal(f);
 const result=humanApprovalBody(checked,{now:f.now});assert.equal(result.schema,'mht.human-reviewed-change.v1');
 const first=firstTrustReviewedIntent(checked);
 assert.equal(first.targetReleaseId,'r16-daily-20261012-r17');
 assert.equal(first.reviewedManifestHash,f.proposal.body.target.reviewedManifestHash);
 assert.equal(first.mayInstall,false);
 assert.equal(first.maySignRelease,false);
 assert.equal(first.mayHandoffIssuer,false);
 rewrite(f,{target:{...f.proposal.body.target,humanPublicKey:exportPublicKey(key())}});assert.throws(()=>validateHumanProposal(f));
});

test('first enrollment can only target exact R17 reviewed manifest and Human key',()=>{
 const base=fixture('enroll_human');
 const target={humanUid:1000,humanSubject:'local-human:1000',humanPublicKey:base.policy.humanPublicKey,
   enrollmentExpiresAt:base.now+86400000,targetReleaseId:'r16-daily-20261012-r17',
   reviewedManifestHash:digest('reviewed-R17')};
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
