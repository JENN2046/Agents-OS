import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {generateKeyPairSync} from 'node:crypto';
import {signed,verified,digest} from '../src/lease-core.mjs';
import {runHumanApprovalOperation} from '../human/approval-signer.mjs';
import {validateFirstCutoverTarget} from '../authority/first-cutover-authorization.mjs';
import {inspectFirstCutoverHandoffAdmission} from '../human/first-cutover-admission.mjs';
import {firstCutoverFixture,FIRST_CUTOVER_PENDING,FIRST_CUTOVER_POLICY,SOURCE_FREEZE}
  from './fixtures/first-cutover-fixture.mjs';
function setup(t){
 const x=firstCutoverFixture(t);
 x.writeJson('/etc/minimal-human-trust/trust-roots.json',x.f.args.roots);
 x.writeJson('/run/r16-owner/public-config.json',x.f.args.priorPublicConfig);
 x.writeJson('/etc/minimal-human-trust/reviewed-installation.json',x.f.args.reviewManifest);
 let keyReads=0;
 const opts={readProtected:x.readProtected,now:x.now,euid:0,
   readWorkspaceIdentity:()=>({dev:x.policy.workspaceDev,ino:x.policy.workspaceIno}),
   loadHumanKey:expected=>{keyReads++;assert.equal(expected,x.humanPublicKey);return x.humanKey;}};
 const call=(operation='preview_first_cutover',extra={})=>runHumanApprovalOperation({...opts,
   input:{operation,proposalHash:operation.startsWith('preview')?null:digest(x.proposal)},...extra});
 return {x,opts,call,keyReads:()=>keyReads,
   freshSign:()=>fs.unlinkSync(x.protectedFiles.get(x.journalBase+'.result.json'))};
}
test('first Native preview uses verified stage enrollment without reading installed issuer or credential',t=>{
 const a=setup(t),p=a.call();assert.equal(p.summary.action,'first_cutover_handoff');
 assert.deepEqual(p.summary.target,a.x.target);assert.equal(a.keyReads(),0);
 assert.ok(!a.x.reads.includes('/etc/minimal-human-trust/issuer.json'));
});
test('first Native sign requires fresh OS intent then signs only exact short consent',t=>{
 const a=setup(t);a.freshSign();const result=a.call('sign_first_cutover');
 assert.equal(result.status,'APPROVED_NOT_APPLIED');assert.equal(a.keyReads(),1);
 const b=verified(result.approval,a.x.humanPublicKey,'mht.first-cutover-authorization.v1');
 assert.equal(b.proposalHash,digest(a.x.proposal));assert.equal(b.targetHash,digest(a.x.target));
 assert.equal(b.expiresAt,a.x.proposal.body.expiresAt);assert.equal(b.issuedAt,a.x.now());
 assert.ok(!a.x.reads.includes('/etc/minimal-human-trust/issuer.json'));
});
test('completed consent result, missing intent and wrong nonce refuse before any key read',t=>{
 for(const mutate of [()=>{},a=>fs.unlinkSync(a.x.protectedFiles.get(a.x.journalBase+'.intent.json')),
   a=>a.x.resignProposal({nonce:'different-nonce-123456'})]){
   const a=setup(t);mutate(a);assert.throws(()=>a.call('sign_first_cutover'));assert.equal(a.keyReads(),0);
 }
});
test('unsupported input, nonroot and both cross-lane substitutions refuse before key read',t=>{
 const a=setup(t);
 for(const input of [{operation:'run_command',proposalHash:null},{operation:'preview_first_cutover',proposalHash:null,path:'/etc/key'},
   {operation:'preview_first_cutover',proposalHash:'a'.repeat(64)}])
   assert.throws(()=>a.call('preview_first_cutover',{input}));
 assert.throws(()=>a.call('preview_first_cutover',{euid:1000}));
 a.x.writeJson('/etc/minimal-human-trust/human-pending.json',a.x.proposal);
 a.x.writeJson('/etc/minimal-human-trust/human-policy.json',a.x.policy);
 assert.throws(()=>a.call('preview'));assert.equal(a.keyReads(),0);
 const b=setup(t);b.x.writeJson(FIRST_CUTOVER_PENDING,b.x.f.proposal);
 b.x.writeJson(FIRST_CUTOVER_POLICY,b.x.f.policy);
 assert.throws(()=>b.call());assert.equal(b.keyReads(),0);
});
test('reviewed code, source authority, workspace and Human key drift refuse before credential',t=>{
 for(const mutate of [a=>a.x.writeBytes('/usr/lib/minimal-human-trust/human/approval-policy.mjs',Buffer.from('changed')),
   a=>a.x.writeJson(SOURCE_FREEZE,{...a.x.sourceFreeze,sourceCommit:'b'.repeat(40)}),
   a=>a.x.writeJson(FIRST_CUTOVER_POLICY,{...a.x.policy,humanPublicKey:a.x.f.args.roots.issuerPublicKey})]){
   const a=setup(t);a.freshSign();mutate(a);assert.throws(()=>a.call('sign_first_cutover'));assert.equal(a.keyReads(),0);
 }
 const a=setup(t);assert.throws(()=>a.call('preview_first_cutover',{
   readWorkspaceIdentity:()=>({dev:99,ino:88})}));assert.equal(a.keyReads(),0);
});
test('actual Human credential mismatch and clock expiry never produce an approval',t=>{
 const a=setup(t);a.freshSign();assert.throws(()=>a.call('sign_first_cutover',{
   loadHumanKey:()=>generateKeyPairSync('ed25519').privateKey}));
 const b=setup(t);b.freshSign();b.x.setNow(b.x.proposal.body.expiresAt);
 assert.throws(()=>b.call('sign_first_cutover'));assert.equal(b.keyReads(),0);
});
test('proposal or OS receipt drift during credential access refuses result and leaves intent unknown',t=>{
 for(const mutate of [a=>a.x.resignProposal({nonce:'changed-during-sign-12345'}),
   a=>a.x.writeJson(a.x.journalBase+'.intent.json',{...a.x.osIntent,challengeHash:digest('changed')})]){
   const a=setup(t);a.freshSign();assert.throws(()=>a.call('sign_first_cutover',{
     loadHumanKey:()=>{mutate(a);return a.x.humanKey;}}));
   assert.ok(fs.existsSync(a.x.protectedFiles.get(a.x.journalBase+'.intent.json')));
 }
});
test('public-key padding aliases cannot defeat first-cutover key separation',t=>{
 const a=setup(t),template={...a.x.target.newRootTemplate};
 template.enrollmentAuthorityPublicKey=template.issuerPublicKey+'=';
 assert.throws(()=>validateFirstCutoverTarget({...a.x.target,newRootTemplate:template,
   newRootTemplateHash:digest(template)}));
});
test('machine control delivery must be signed after Human consent and never future-dated',t=>{
 for(const deliveredAt of [a=>a.x.approvedAt-1,a=>a.x.now()+1]){
   const a=setup(t);a.x.f.args.delivery=signed({...a.x.f.args.delivery.body,
     issuedAt:deliveredAt(a)},a.x.f.issuer);
   assert.throws(()=>inspectFirstCutoverHandoffAdmission({humanArgs:a.x.humanArgs(),
     finalRoots:a.x.finalRoots(),handoffArgs:a.x.f.args,now:a.x.now()}),
     {code:'FIRST_CUTOVER_DELIVERY_NOT_AFTER_HUMAN'});
 }
});
