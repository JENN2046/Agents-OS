import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import {canonical,digest,signed,exportPublicKey,ProtectedStore,ROLES,verified} from '../src/lease-core.mjs';
import {verifyRecoveryHandoff,inspectRecoveryIssuerSnapshot}
 from '../authority/recovery-handoff.mjs';
import {validateInstalledTrustPolicy} from '../src/minimal-trust-issuer-once.mjs';
import {runMinimalTrustOnce,replayInitialState} from '../src/minimal-trust-issuer.mjs';
import {recoveryHandoffFixture,sealRecoveryHandoff} from './fixtures/recovery-handoff-fixture.mjs';

const inspect=f=>inspectRecoveryIssuerSnapshot({snapshot:f.wrapper.data,wrapper:f.wrapper,
 admission:f.admission,grantId:f.grant.body.id,issuerPublicKey:f.roots.issuerPublicKey,
 releasePublicKey:f.roots.releasePublicKey,now:f.now});
const verify=f=>verifyRecoveryHandoff(f.handoff,f.roots.enrollmentAuthorityPublicKey,
 {grantId:f.grant.body.id,release:f.r17,mode:'recovery_only',grantHash:digest(f.grant),issuerPublicKey:f.roots.issuerPublicKey});
const policy=f=>validateInstalledTrustPolicy(f.config,{trustRoots:f.roots,now:f.now});
function runtime(t,f){
 const temp=fs.mkdtempSync(path.join(os.tmpdir(),'mht-synthetic-recovery-'));fs.chmodSync(temp,0o700);
 const issuerDirectory=path.join(temp,'issuer'),replayDirectory=path.join(temp,'replay');
 fs.mkdirSync(issuerDirectory,{mode:0o700});
 fs.writeFileSync(path.join(issuerDirectory,'state.json'),canonical(f.wrapper),{mode:0o600});
 const replay=new ProtectedStore({directory:replayDirectory,create:true,initial:replayInitialState(),now:()=>f.now});
 replay.close();
 t.after(()=>fs.rmSync(temp,{recursive:true,force:true}));
 const read=(directory)=>JSON.parse(fs.readFileSync(path.join(directory,'state.json'),'utf8'));
 const args=()=>({issuerDirectory,replayDirectory,issuerPrivateKey:f.keys.issuer,
  issuerPublicKey:f.roots.issuerPublicKey,releasePublicKey:f.roots.releasePublicKey,
  enrollmentAuthorityPublicKey:f.roots.enrollmentAuthorityPublicKey,grantId:f.grant.body.id,
  release:f.r17,resolveProject:(_workspace,project)=>project,humanAuthorityPublicKey:exportPublicKey(f.keys.human),
  expectedGrantHash:digest(f.grant),mode:'recovery_only',now:()=>f.now,handoffBinding:f.binding()});
 const run=(envelope,extra={})=>runMinimalTrustOnce({...args(),...extra,envelope});
 return {temp,issuerDirectory,replayDirectory,run,readIssuer:()=>read(issuerDirectory),
  readReplay:()=>read(replayDirectory),writeIssuer:value=>fs.writeFileSync(path.join(issuerDirectory,'state.json'),canonical(value),{mode:0o600})};
}
test('complete signed issuer-shape two UNKNOWN snapshot admits only the exact R17 recovery receiver',()=>{
 const f=recoveryHandoffFixture(),original=structuredClone(f.wrapper),unknowns=structuredClone(f.unknownProjection);
 assert.equal(verify(f).schema,'mht.issuer-handoff.v2');
 assert.equal(inspect(f).status,'EXACT_TWO_READ_UNKNOWNS_ADMITTED_FOR_RECOVERY');
 assert.deepEqual(policy(f).handoffBinding,f.binding());
 assert.deepEqual(f.wrapper,original);assert.deepEqual(f.unknownProjection,unknowns);
 assert.equal(f.productionEvidenceVerified,false);
});
test('trusted Enrollment re-signing cannot change an original operation id/hash/generation or admit writes',()=>{
 for(const patch of [{operationId:'another-operation'},{operationHash:digest('replacement')},
  {generation:31},{action:'edit_code'},{outcome:'COMPLETED'},{replayAllowed:true},{originalResultAvailable:true}]){
  const f=recoveryHandoffFixture();Object.assign(f.admission.operations[0],patch);sealRecoveryHandoff(f);
  assert.throws(()=>verify(f),{code:'RECOVERY_HANDOFF_OPERATIONS'});
 }
});
test('duplicate operations or a third unresolved project cannot acquire recovery admission',()=>{
 for(const change of [f=>{f.admission.operations[1]=structuredClone(f.admission.operations[0]);},
  f=>{f.admission.operations.push(structuredClone(f.admission.operations[0]));}]){
  const f=recoveryHandoffFixture();change(f);sealRecoveryHandoff(f);assert.throws(()=>verify(f));
 }
});
test('a cross-project signed lease hash is refused even inside a trusted signed handoff',()=>{
 const f=recoveryHandoffFixture();f.admission.operations[0].leaseHash=f.admission.operations[1].leaseHash;
 sealRecoveryHandoff(f);assert.throws(()=>inspect(f),{code:'RECOVERY_HANDOFF_LEASE'});
});
test('unadmitted active third project and any pending project block the entire receiver',()=>{
 const f=recoveryHandoffFixture();f.wrapper.data.grants[0].projects.push(f.makeProject({projectId:'foreign',generation:1}));
 sealRecoveryHandoff(f);assert.throws(()=>inspect(f),{code:'RECOVERY_HANDOFF_FOREIGN_PROJECT'});
 const g=recoveryHandoffFixture();g.projects[0].pending=structuredClone(g.projects[0].active);
 sealRecoveryHandoff(g);assert.throws(()=>inspect(g),{code:'RECOVERY_HANDOFF_PROJECTS'});
});
test('genuinely certified historical closed projects remain admissible in addition to the two UNKNOWNs',()=>{
 const f=recoveryHandoffFixture();f.wrapper.data.grants[0].projects.push(f.closedProject());sealRecoveryHandoff(f);
 assert.equal(inspect(f).status,'EXACT_TWO_READ_UNKNOWNS_ADMITTED_FOR_RECOVERY');
});
test('snapshot data, full wrapper revision and historical logical clock are bound independently',()=>{
 for(const change of [f=>{f.wrapper.revision++;},f=>{f.wrapper.maxNow++;},
  f=>{f.wrapper.data.grants[0].status='REVOKED';}]){
  const f=recoveryHandoffFixture();change(f);assert.throws(()=>inspect(f),{code:'RECOVERY_HANDOFF_SNAPSHOT'});
 }
});
test('fresh observation attests an old unchanged wrapper without rewriting its maxNow',()=>{
 const f=recoveryHandoffFixture();assert.ok(f.now-f.wrapper.maxNow>30000);
 assert.equal(inspect(f).status,'EXACT_TWO_READ_UNKNOWNS_ADMITTED_FOR_RECOVERY');
 for(const observedAt of [f.now-30001,f.now+1]){
  const g=recoveryHandoffFixture();g.admission.observedAt=observedAt;sealRecoveryHandoff(g);
  assert.throws(()=>inspect(g),{code:'RECOVERY_HANDOFF_OBSERVATION_EXPIRED'});
 }
});
test('re-signed old release ids and runtime versions cannot bypass exact R15 source pins',()=>{
 for(const patch of [{id:'r16-daily-20261012-r14'},
  {versions:{app:digest('wrong'),bridge:digest('wrong'),native:digest('wrong')}}]){
  const f=recoveryHandoffFixture();const changed=signed({...f.r15.body,...patch},f.keys.release);
  f.projects[0].active.release=changed;
  f.projects[0].history[0]=structuredClone(f.projects[0].active);sealRecoveryHandoff(f);
  assert.throws(()=>inspect(f));
 }
});
test('wrong activation, peer close proof or history cannot certify an unresolved active generation',()=>{
 for(const change of [f=>{const a=f.projects[0].active;a.activation=signed({...a.activation.body,
  evidenceHash:digest('wrong')},f.keys.issuer);},
  f=>{const a=f.projects[0].active;a.evidence.bridge=signed({...a.evidence.bridge.body,
   projectId:'pmog2'},f.signers.bridge);a.activation=signed({...a.activation.body,
    evidenceHash:digest(a.evidence)},f.keys.issuer);},
  f=>{f.projects[0].history=[];}]){
  const f=recoveryHandoffFixture();change(f);sealRecoveryHandoff(f);assert.throws(()=>inspect(f));
 }
});
test('authentic peer signatures cannot certify durableClosed false, pending work or extra authority',()=>{
 for(const patch of [{durableClosed:false},{pending:1},{mayActivateBusiness:true}]){
  const f=recoveryHandoffFixture(),active=f.projects[0].active;
  active.evidence.native=signed({...active.evidence.native.body,...patch},f.signers.native);
  active.activation=signed({...active.activation.body,evidenceHash:digest(active.evidence)},f.keys.issuer);
  f.projects[0].history[0]=structuredClone(active);sealRecoveryHandoff(f);
  assert.throws(()=>inspect(f));
 }
});
test('first binding validates both locked ledgers and preserves issuer/UNKNOWN bytes',t=>{
 const f=recoveryHandoffFixture(),r=runtime(t,f),before=r.readIssuer(),unknowns=structuredClone(f.unknownProjection);
 assert.deepEqual(r.run(f.envelope('grant')),f.grant);
 assert.deepEqual(r.readIssuer(),before);assert.deepEqual(f.unknownProjection,unknowns);
 assert.deepEqual(r.readReplay().data.handoff,f.binding());
 assert.equal(fs.existsSync(path.join(r.issuerDirectory,'.lock')),false);
 assert.equal(fs.existsSync(path.join(r.replayDirectory,'.lock')),false);
});
test('v2 rejects active mode on both first binding and subsequent recorded invocations',t=>{
 const f=recoveryHandoffFixture(),r=runtime(t,f);
 assert.throws(()=>r.run(f.envelope('grant'),{mode:'active'}),{code:'RECOVERY_HANDOFF_SCOPE'});
 assert.equal(r.readReplay().data.handoff,null);
 r.run(f.envelope('grant'));
 assert.throws(()=>r.run(f.envelope('grant'),{mode:'active'}),{code:'RECOVERY_HANDOFF_SCOPE'});
});
test('unsigned allowance and a changed recorded handoff are rejected before issuer dispatch',t=>{
 const f=recoveryHandoffFixture(),r=runtime(t,f);
 const forged={...f.binding(),recoveryHandoff:{body:f.handoff.body,signature:'A'.repeat(86)}};
 assert.throws(()=>r.run(f.envelope('grant'),{handoffBinding:forged}),{code:'BAD_SIGNATURE'});
 r.run(f.envelope('grant'));f.handoff=signed({...f.handoff.body,epoch:9999},f.keys.enrollment);
 assert.throws(()=>r.run(f.envelope('grant')),{code:'HANDOFF_BINDING'});
});
test('pre-existing replay records and expired first binding cannot bypass snapshot admission',t=>{
 const f=recoveryHandoffFixture(),r=runtime(t,f),s=new ProtectedStore({directory:r.replayDirectory,
  create:false,now:()=>f.now});
 s.transact(state=>state.used.push({id:'native:preexisting-nonce-1234',phase:'INTENT',
  at:f.now,kind:'grant',requestHash:digest('request'),effectHash:digest('effect')}));s.close();
 assert.throws(()=>r.run(f.envelope('grant')),{code:'HANDOFF_SNAPSHOT'});
 const g=recoveryHandoffFixture(),q=runtime(t,g);g.now=g.handoff.body.expiresAt;
 assert.throws(()=>q.run(g.envelope('grant')),{code:'HANDOFF_SNAPSHOT'});
});
test('legacy v1 still rejects active old leases and accepts its original all-closed path',t=>{
 const f=recoveryHandoffFixture(),r=runtime(t,f);
 const {recoveryAdmission,...legacyBody}=f.handoff.body;
 const v1=signed({...legacyBody,schema:'mht.issuer-handoff.v1'},f.keys.enrollment);
 f.config.handoff=v1;f.roots.handoffHash=digest(v1);
 const binding=policy(f).handoffBinding;
 assert.throws(()=>r.run(f.envelope('grant'),{handoffBinding:binding}),{code:'HANDOFF_SNAPSHOT'});
 const g=recoveryHandoffFixture();g.projects.forEach(project=>{project.active=null;project.pending=null;});
 const q=runtime(t,g),{recoveryAdmission:ignored,...body}=g.handoff.body;
 g.config.handoff=signed({...body,schema:'mht.issuer-handoff.v1',issuerSnapshotHash:digest(g.wrapper.data)},g.keys.enrollment);
 g.roots.handoffHash=digest(g.config.handoff);
 const legacy=policy(g).handoffBinding;
 assert.deepEqual(q.run(g.envelope('grant'),{handoffBinding:legacy}),g.grant);
});
test('recorded v2 recovery allows nonce/status cleanup, never prepare or activate business',t=>{
 const f=recoveryHandoffFixture(),r=runtime(t,f),envelope=f.envelope('grant'),before=r.readIssuer();
 r.run(envelope);
 const status=r.run(f.envelope('nonceStatus',{nonce:envelope.body.nonce,requestHash:digest(envelope)}));
 assert.equal(status.status,'RESULT');assert.deepEqual(status.result,f.grant);
 assert.throws(()=>r.run(envelope),{code:'REPLAY_REJECTED'});
 for(const action of ['prepare','activate'])assert.throws(()=>r.run(f.envelope(action,{})),{code:'RECOVERY_ONLY'});
 assert.deepEqual(r.readIssuer(),before);
});
test('signed old-lease closure in recovery preserves the original UNKNOWN projection and never runs business',t=>{
 const f=recoveryHandoffFixture(),r=runtime(t,f),unknowns=structuredClone(f.unknownProjection);
 r.run(f.envelope('grant'));
 const project=f.projects[0],lease=project.active.lease;
 const evidence=Object.fromEntries(ROLES.map(role=>[role,signed({schema:'r16.stopped.v1',role,
  peerId:f.peers[role].id,grantId:f.grant.body.id,grantVersion:1,projectId:project.projectId,
  generation:project.generation,leaseHash:digest(lease),requestId:lease.body.requestId,
  durableClosed:true,pending:0,resultsHash:digest({unknownsPreserved:unknowns})},f.signers[role])]));
 const closed=r.run(f.envelope('closeLease',{grantId:f.grant.body.id,projectId:project.projectId,lease,evidence}));
 assert.equal(verified(closed,f.roots.issuerPublicKey,'r16.closed.v1').leaseHash,digest(lease));
 const saved=r.readIssuer().data.grants[0].projects.find(row=>row.projectId===project.projectId);
 assert.equal(saved.active,null);assert.equal(saved.pending,null);
 assert.deepEqual(saved.history.at(-1).lease,lease);assert.deepEqual(f.unknownProjection,unknowns);
 assert.ok(unknowns.every(row=>row.status==='UNKNOWN'&&row.replayAllowed===false));
 assert.throws(()=>r.run(f.envelope('prepare',{})),{code:'RECOVERY_ONLY'});
});
