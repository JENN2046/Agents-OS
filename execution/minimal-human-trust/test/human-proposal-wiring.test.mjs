import test from 'node:test';
import assert from 'node:assert/strict';
import {spawnSync} from 'node:child_process';
import {digest} from '../src/lease-core.mjs';
import {inspectHumanProposalRequest,proposalArtifacts,verifyHumanProposalArtifacts} from '../release/human-proposal-inputs.mjs';
import {firstCutoverFixture} from './fixtures/first-cutover-fixture.mjs';
const child=new URL('./fixtures/human-proposal-wiring-child.mjs',import.meta.url).pathname;
for(const scenario of ['positive','partial-publication','expired-result','wrong-key','post-key-drift',
 'protected-repeat-read-drift','during-import-drift','wrong-pub-no-import','expiry-during-guard',
 'clock-reversal','existing-output','bad-target','workspace-drift','isolated-profile','wrong-context',
 'unsigned-evidence-drift','physical-drift','dependency-window'])test('synthetic root proposal integration: '+scenario,()=>{
 const r=spawnSync(process.execPath,['--experimental-test-module-mocks',child,scenario],{encoding:'utf8',timeout:20000});
 assert.equal(r.status,0,r.stderr+'\n'+r.stdout);assert.match(r.stdout,/PASS_SYNTHETIC_ONLY/);
});
function cutover(t){
 const f=firstCutoverFixture(t),a=f.humanArgs();const {proposalHash,...policy}=f.policy;
 const request={schema:'mht.human-proposal-request.v1',body:f.proposal.body,
   policyTemplate:{...policy,schema:'mht.human-pending-policy-template.v1'},issuerStateFileHash:digest(f.f.snapshot)};
 const args={request,roots:a.roots,pub:a.priorPublicConfig,reviewManifest:a.reviewManifest,
   sourceFreeze:f.sourceFreeze,installerBytes:f.readProtected('/etc/minimal-human-trust/stage-installer-reviewed.mjs'),
   wrapper:f.f.snapshot,readProtected:f.readProtected,workspaceIdentity:{dev:policy.workspaceDev,ino:policy.workspaceIno},now:f.now()};
 return {f,args};
}
test('cutover producer inspects actual synthetic signed Stage and all physical files, not future Human consent',t=>{
 const {f,args}=cutover(t);const inspected=inspectHumanProposalRequest(args);
 assert.equal(inspected.status,'UNSIGNED_EXACT_TARGET_INSPECTED');assert.equal(inspected.mayCutover,false);
 const artifact=proposalArtifacts({proposal:f.proposal,inspection:inspected,request:args.request,roots:args.roots,now:f.now()});
 assert.equal(artifact.publicationPlan,null);assert.equal(verifyHumanProposalArtifacts(artifact,{inspection:inspected,request:args.request,roots:args.roots,now:f.now()}),true);
 assert.ok(f.reads.includes('/opt/r16/releases/r16-daily-20261012-r17/app/main.mjs'));
});
test('cutover producer refuses any drifted nonfreeze staged physical file before a proposal may sign',t=>{
 const {f,args}=cutover(t);f.writeBytes('/opt/r16/releases/r16-daily-20261012-r17/app/main.mjs',Buffer.from('drift'));
 assert.throws(()=>inspectHumanProposalRequest(args),{code:'FIRST_TRUST_FILE_DRIFT'});
});
test('cutover proposal binds exact complete wrapper and enrolled Human public key',t=>{
 const {f,args}=cutover(t);
 assert.throws(()=>inspectHumanProposalRequest({...args,wrapper:{...args.wrapper,revision:999}}));
 assert.throws(()=>inspectHumanProposalRequest({...args,request:{...args.request,policyTemplate:{...args.request.policyTemplate,humanPublicKey:f.f.args.roots.issuerPublicKey}}}));
});

test('producer requires every freeze file to be bound by the Native candidate manifest',t=>{
 const {args}=cutover(t);const review=structuredClone(args.reviewManifest);delete review.artifacts.native.files['release/human-proposal-once.mjs'];
 assert.throws(()=>inspectHumanProposalRequest({...args,reviewManifest:review}),{code:'HUMAN_PROPOSAL_NATIVE_FREEZE_BINDING'});
});
