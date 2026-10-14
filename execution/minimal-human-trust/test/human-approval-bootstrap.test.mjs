import test from 'node:test';
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {APPROVAL_REQUIRED_FILES,checkApprovalSourceFreeze,runApprovalBootstrap}
  from '../human/approval-bootstrap.mjs';
const sha=b=>createHash('sha256').update(b).digest('hex');
function fixture(){
 const files=new Map(APPROVAL_REQUIRED_FILES.map(p=>['/usr/lib/minimal-human-trust/'+p,Buffer.from('synthetic-freeze-'+p)]));
 const manifest={schema:'mht.first-trust-code-freeze.v1',sourceCommit:'a'.repeat(40),
   files:Object.fromEntries(APPROVAL_REQUIRED_FILES.map(p=>[p,sha(files.get('/usr/lib/minimal-human-trust/'+p))]))};
 const m='/etc/minimal-human-trust/first-trust-code.json';files.set(m,Buffer.from(JSON.stringify(manifest)));
 const seen=[];
 return {files,manifest,seen,read:p=>{seen.push(p);assert.ok(files.has(p));return files.get(p);},
   cgroup:()=> '0::/system.slice/system-minimal\\x2dhuman\\x2dtrust\\x2dapproval.slice/minimal-human-trust-approval@2.service'};
}
test('complete source freeze passes before dynamic signer import and input read',async()=>{
 const f=fixture(),events=[];
 const result=await runApprovalBootstrap({...f,euid:0,load:async()=>{
   events.push('import');assert.equal(f.seen.length,1+APPROVAL_REQUIRED_FILES.length);
   return {readApprovalInput:async()=>{events.push('input');return {operation:'preview',proposalHash:null};},
     runHumanApprovalOperation:opts=>{events.push('run');return opts.input;}};
 }});
 assert.deepEqual(events,['import','input','run']);assert.equal(result.operation,'preview');
});
test('every required source deletion or mismatch prevents dynamic import',async()=>{
 for(const rel of APPROVAL_REQUIRED_FILES){
   const f=fixture();f.files.set('/usr/lib/minimal-human-trust/'+rel,Buffer.from('tampered'));
   await assert.rejects(runApprovalBootstrap({...f,euid:0,load:()=>assert.fail('must not import')}));
   const g=fixture();delete g.manifest.files[rel];assert.throws(()=>checkApprovalSourceFreeze(g));
 }
});
test('untrusted source names, schema, commit and unsupported manifest fields reject before reading source',()=>{
 for(const patch of [{schema:'other'},{sourceCommit:'bad'},{extra:true}]){
   const f=fixture();Object.assign(f.manifest,patch);assert.throws(()=>checkApprovalSourceFreeze(f));
 }
 for(const p of ['../secret','/etc/key','x\\secret','x//y','__proto__']){
   const f=fixture();Object.defineProperty(f.manifest.files,p,{value:'a'.repeat(64),enumerable:true});
   assert.throws(()=>checkApprovalSourceFreeze(f));
 }
});
test('nonroot, wrong service, duplicate and malformed cgroup reject before root reads',async()=>{
 const f=fixture();for(const patch of [{euid:1000},{cgroup:()=> '0::/user.slice/minimal-human-trust-approval@2.service'},
   {cgroup:()=>f.cgroup()+'\n'+f.cgroup()},{cgroup:()=>f.cgroup()+'\nbad'}]){
   await assert.rejects(runApprovalBootstrap({...f,euid:0,read:()=>assert.fail('must not read'),...patch}));
 }
});
test('manifest or code drift during dynamic import never reaches input or signing',async()=>{
 for(const mutate of [f=>f.files.set('/etc/minimal-human-trust/first-trust-code.json',Buffer.from('changed')),
   f=>f.files.set('/usr/lib/minimal-human-trust/human/approval-policy.mjs',Buffer.from('changed'))]){
   const f=fixture();await assert.rejects(runApprovalBootstrap({...f,euid:0,load:async()=>{
     mutate(f);return {readApprovalInput:()=>assert.fail('must not read input'),runHumanApprovalOperation:()=>assert.fail('must not sign')};
   }}));
 }
});
