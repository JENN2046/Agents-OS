import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import {spawnSync} from 'node:child_process';
import {generateKeyPairSync,sign,verify,createPublicKey} from 'node:crypto';
import {issueHumanProposalOnce} from '../release/human-proposal-transaction.mjs';
import {canonical,digest} from '../src/lease-core.mjs';

const identity=()=>({schema:'mht.human-proposal-signing-intent.v1',action:'enroll_human',
 requestHash:digest('disposable-request'),sourceFreezeDigest:digest('disposable-source'),
 proposalBodyHash:digest({schema:'synthetic.proposal.v1',purpose:'test-only'}),
 policyTemplateHash:digest('disposable-policy')});
const verifyFixture=artifacts=>{
 assert.deepEqual(artifacts.body,{schema:'synthetic.proposal.v1',purpose:'test-only'});
 const key=createPublicKey({key:Buffer.from(artifacts.publicKey,'base64url'),format:'der',type:'spki'});
 assert.equal(verify(null,Buffer.from(canonical(artifacts.body)),key,
  Buffer.from(artifacts.signature,'base64url')),true,'Synthetic Ed25519 signature must verify');
};
const fixture=t=>{
 const directory=fs.mkdtempSync(path.join(os.tmpdir(),'g1d-human-proposal-'));
 fs.chmodSync(directory,0o700);
 t.after(()=>fs.rmSync(directory,{recursive:true,force:true}));
 const {privateKey,publicKey}=generateKeyPairSync('ed25519');
 const request=identity();
 let signs=0,publishes=0;
 const publish=artifacts=>{
  publishes++;
  const file=path.join(directory,'published.json'),bytes=Buffer.from(canonical(artifacts));
  if(fs.existsSync(file))assert.deepEqual(fs.readFileSync(file),bytes);
  else fs.writeFileSync(file,bytes,{flag:'wx',mode:0o600});
 };
 const produce=()=>{
  // The durable INTENT must be observable before the synthetic signing effect.
  assert.deepEqual(JSON.parse(fs.readFileSync(path.join(directory,'intent.json'))),request);
  assert.equal(fs.existsSync(path.join(directory,'result.json')),false);
  signs++;
  const body={schema:'synthetic.proposal.v1',purpose:'test-only'};
  return {body,publicKey:publicKey.export({format:'der',type:'spki'}).toString('base64url'),
   signature:sign(null,Buffer.from(canonical(body)),privateKey).toString('base64url')};
 };
 const issue=(extra={})=>issueHumanProposalOnce({directory,identity:request,produce,
  verifyResult:verifyFixture,publish,...extra});
 return {directory,request,issue,produce,publish,signs:()=>signs,publishes:()=>publishes};
};
const throws=(fn,code)=>assert.throws(fn,{code});
const fault=stage=>name=>{if(stage===name)throw Object.assign(Error('CRASH_FIXTURE'),{code:'CRASH_FIXTURE'});};
const replace=(f,name,value)=>fs.writeFileSync(path.join(f.directory,name),canonical(value),{mode:0o600});

test('durable proposal INTENT precedes synthetic signing; verified RESULT precedes publication',t=>{
 const f=fixture(t),events=[];
 const receipt=f.issue({guard:()=>events.push('guard'),fault:stage=>events.push(stage),
  publish:artifacts=>{
   const saved=JSON.parse(fs.readFileSync(path.join(f.directory,'result.json')));
   assert.deepEqual(saved.artifacts,artifacts);
   f.publish(artifacts);
  }});
 assert.equal(receipt.status,'SIGNED_PROPOSAL_ONLY');
 assert.equal(receipt.signerCalled,true);
 assert.equal(f.signs(),1);
 assert.equal(f.publishes(),1);
 assert.deepEqual(events,['guard','after_intent','guard','guard','after_effect','after_result',
  'guard','after_publish','guard']);
 for(const key of ['mayEnroll','maySignRelease','mayInstall','mayCutover'])assert.equal(receipt[key],false);
 for(const file of ['intent.json','result.json','.lock'])assert.equal(fs.statSync(path.join(f.directory,file)).mode&0o7777,0o600);
});
test('lost reply recovers immutable identical bytes with zero second signature',t=>{
 const f=fixture(t),a=f.issue(),bytes=fs.readFileSync(path.join(f.directory,'published.json'));
 const b=f.issue({produce:()=>assert.fail('must not sign again')});
 assert.equal(b.status,'SIGNED_PROPOSAL_ALREADY');
 assert.equal(b.signerCalled,false);
 assert.equal(a.resultHash,b.resultHash);
 assert.equal(a.artifactsHash,b.artifactsHash);
 assert.deepEqual(fs.readFileSync(path.join(f.directory,'published.json')),bytes);
 assert.equal(f.signs(),1);
});
test('both files and parent directory are fsynced before private effect and publication',t=>{
 const f=fixture(t),synced=[];
 const io={...fs,fsyncSync:fd=>{
  synced.push(fs.readlinkSync(`/proc/self/fd/${fd}`));fs.fsyncSync(fd);
 }};
 f.issue({io,produce:()=>{
  assert.deepEqual(synced,[path.join(f.directory,'intent.json'),f.directory]);
  return f.produce();
 },publish:artifacts=>{
  assert.deepEqual(synced,[path.join(f.directory,'intent.json'),f.directory,
   path.join(f.directory,'result.json'),f.directory]);
  f.publish(artifacts);
 }});
});
for(const stage of ['after_intent','after_effect'])test(`${stage} leaves UNKNOWN that cannot authorize retry`,t=>{
 const f=fixture(t);
 throws(()=>f.issue({fault:fault(stage)}),'CRASH_FIXTURE');
 assert.equal(f.signs(),stage==='after_intent'?0:1);
 assert.equal(fs.existsSync(path.join(f.directory,'result.json')),false);
 throws(()=>f.issue(),'HUMAN_PROPOSAL_EFFECT_UNKNOWN');
 assert.equal(f.signs(),stage==='after_intent'?0:1);
 assert.equal(f.publishes(),0);
});
for(const stage of ['after_result','after_publish'])test(`${stage} recovers publication from RESULT without signing`,t=>{
 const f=fixture(t);
 throws(()=>f.issue({fault:fault(stage)}),'CRASH_FIXTURE');
 const receipt=f.issue({produce:()=>assert.fail('must never sign twice')});
 assert.equal(receipt.status,'SIGNED_PROPOSAL_ALREADY');
 assert.equal(f.signs(),1);
 verifyFixture(JSON.parse(fs.readFileSync(path.join(f.directory,'published.json'))));
});
test('publication failure keeps verified RESULT for safe identical publication retry',t=>{
 const f=fixture(t);
 throws(()=>f.issue({publish:()=>{throw Object.assign(Error('PUBLICATION_FAILED'),{code:'PUBLICATION_FAILED'});}}),
  'PUBLICATION_FAILED');
 assert.equal(f.issue().signerCalled,false);
 assert.equal(f.signs(),1);
});
test('expiry guard rejects old RESULT without signing or publishing and cannot refresh expiry',t=>{
 const f=fixture(t);f.issue();
 const bytes=fs.readFileSync(path.join(f.directory,'result.json'));
 throws(()=>f.issue({guard:()=>{throw Object.assign(Error('EXPIRED'),{code:'EXPIRED'});}}),'EXPIRED');
 assert.deepEqual(fs.readFileSync(path.join(f.directory,'result.json')),bytes);
 assert.equal(f.signs(),1);assert.equal(f.publishes(),1);
});
test('guard failure after the effect leaves INTENT UNKNOWN without publication',t=>{
 const f=fixture(t);let calls=0;
 throws(()=>f.issue({guard:()=>{if(++calls===3)throw Object.assign(Error('DRIFT'),{code:'DRIFT'});}}),'DRIFT');
 assert.equal(f.signs(),1);assert.equal(f.publishes(),0);
 throws(()=>f.issue(),'HUMAN_PROPOSAL_EFFECT_UNKNOWN');
});
test('invalid crypto cannot become durable RESULT or publication',t=>{
 const f=fixture(t);
 assert.throws(()=>f.issue({produce:()=>({...f.produce(),signature:'invalid'})}));
 assert.equal(fs.existsSync(path.join(f.directory,'result.json')),false);
 assert.equal(f.publishes(),0);
 throws(()=>f.issue(),'HUMAN_PROPOSAL_EFFECT_UNKNOWN');
});
test('RESULT crypto is independently revalidated before each recovered publication',t=>{
 const f=fixture(t);f.issue();
 const result=JSON.parse(fs.readFileSync(path.join(f.directory,'result.json')));
 result.artifacts.signature='invalid';replace(f,'result.json',result);
 assert.throws(()=>f.issue());assert.equal(f.signs(),1);assert.equal(f.publishes(),1);
});
test('changed request and cross-action reuse are conflicts',t=>{
 const f=fixture(t);f.issue();
 for(const changed of [{...f.request,requestHash:digest('changed')},{...f.request,action:'first_cutover_handoff'}])
  throws(()=>f.issue({identity:changed}),'HUMAN_PROPOSAL_INTENT_CONFLICT');
 assert.equal(f.signs(),1);
});
test('identity rejects extra keys, invalid hashes and unsupported actions before journal creation',t=>{
 const f=fixture(t);
 for(const changed of [{...f.request,extra:true},{...f.request,requestHash:'a'},{...f.request,action:'install'},
  {...f.request,sourceFreezeDigest:'A'.repeat(64)}])
  throws(()=>f.issue({identity:changed}),'HUMAN_PROPOSAL_INTENT_INVALID');
 assert.equal(fs.existsSync(path.join(f.directory,'intent.json')),false);
});
test('orphan RESULT refuses signing',t=>{
 const f=fixture(t);f.issue();fs.unlinkSync(path.join(f.directory,'intent.json'));
 throws(()=>f.issue(),'HUMAN_PROPOSAL_ORPHAN_RESULT');assert.equal(f.signs(),1);
});
test('RESULT unknown extra authority field and mismatched intent hash are refused',t=>{
 const f=fixture(t);f.issue();
 const original=JSON.parse(fs.readFileSync(path.join(f.directory,'result.json')));
 for(const changed of [{...original,mayEnroll:true},{...original,intentHash:digest('wrong')}]){
  replace(f,'result.json',changed);throws(()=>f.issue(),'HUMAN_PROPOSAL_RESULT_CONFLICT');
 }
 assert.equal(f.signs(),1);assert.equal(f.publishes(),1);
});
for(const file of ['intent.json','result.json'])test(`weak ${file} is never trusted`,t=>{
 const f=fixture(t);f.issue();fs.chmodSync(path.join(f.directory,file),0o644);
 throws(()=>f.issue(),'HUMAN_PROPOSAL_STATE_UNTRUSTED');
});
test('symlinked and hardlinked journal files are refused',t=>{
 const f=fixture(t);f.issue();
 const p=path.join(f.directory,'result.json'),other=path.join(f.directory,'saved.json');
 fs.renameSync(p,other);fs.symlinkSync(other,p);assert.throws(()=>f.issue());
 fs.unlinkSync(p);fs.linkSync(other,p);throws(()=>f.issue(),'HUMAN_PROPOSAL_STATE_UNTRUSTED');
});
test('noncanonical bytes, duplicate JSON keys and empty journal are refused',t=>{
 const f=fixture(t);f.issue();const p=path.join(f.directory,'result.json'),bytes=fs.readFileSync(p);
 for(const changed of [Buffer.concat([bytes,Buffer.from('\n')]),Buffer.from('{"schema":"x","schema":"y"}'),Buffer.alloc(0)]){
  fs.writeFileSync(p,changed);throws(()=>f.issue(),'HUMAN_PROPOSAL_STATE_UNTRUSTED');
 }
});
test('weak directory and symlinked directory are refused before signing',t=>{
 const f=fixture(t);fs.chmodSync(f.directory,0o755);
 throws(()=>f.issue(),'HUMAN_PROPOSAL_DIRECTORY');fs.chmodSync(f.directory,0o700);
 const link=f.directory+'-link';fs.symlinkSync(f.directory,link);t.after(()=>fs.unlinkSync(link));
 throws(()=>f.issue({directory:link}),'HUMAN_PROPOSAL_DIRECTORY');assert.equal(f.signs(),0);
});
test('directory replacement by a callback is detected before signing',t=>{
 const f=fixture(t),moved=f.directory+'-moved';
 t.after(()=>fs.rmSync(moved,{recursive:true,force:true}));
 throws(()=>f.issue({guard:()=>{fs.renameSync(f.directory,moved);fs.mkdirSync(f.directory,{mode:0o700});}}),
  'HUMAN_PROPOSAL_DIRECTORY_DRIFT');assert.equal(f.signs(),0);
});
test('lock symlink and replacement are refused',t=>{
 const f=fixture(t),lock=path.join(f.directory,'.lock'),other=path.join(f.directory,'other');
 fs.writeFileSync(other,'',{mode:0o600});fs.symlinkSync(other,lock);assert.throws(()=>f.issue());fs.unlinkSync(lock);
 throws(()=>f.issue({guard:()=>{fs.unlinkSync(lock);fs.writeFileSync(lock,'',{mode:0o600});}}),
  'HUMAN_PROPOSAL_LOCK_UNTRUSTED');assert.equal(f.signs(),0);
});
test('weak and hardlinked lock files cannot authorize signing',t=>{
 const f=fixture(t),lock=path.join(f.directory,'.lock'),other=path.join(f.directory,'lock-other');
 fs.writeFileSync(lock,'',{mode:0o644});throws(()=>f.issue(),'HUMAN_PROPOSAL_LOCK_UNTRUSTED');
 fs.chmodSync(lock,0o600);fs.linkSync(lock,other);
 throws(()=>f.issue(),'HUMAN_PROPOSAL_LOCK_UNTRUSTED');assert.equal(f.signs(),0);
});
test('production root journal rejects writable ancestors before signing',t=>{
 const f=fixture(t);
 const io={...fs,lstatSync:file=>{const st=fs.lstatSync(file);st.uid=0;return st;}};
 // Simulated root ownership only; /tmp retains its actual writable mode.
 throws(()=>f.issue({uid:0,io}),'HUMAN_PROPOSAL_PARENT_UNTRUSTED');
 assert.equal(f.signs(),0);assert.equal(fs.existsSync(path.join(f.directory,'intent.json')),false);
});
test('oversize journal file is refused without parsing or signing',t=>{
 const f=fixture(t);f.issue();
 fs.truncateSync(path.join(f.directory,'result.json'),8*1024*1024+1);
 throws(()=>f.issue(),'HUMAN_PROPOSAL_STATE_UNTRUSTED');assert.equal(f.signs(),1);
});
test('actual flock excludes concurrent child while full signer chain is running',t=>{
 const f=fixture(t),child=new URL('./fixtures/human-proposal-crash-child.mjs',import.meta.url).pathname;
 f.issue({produce:()=>{
  const concurrent=spawnSync(process.execPath,[child,f.directory,'none'],{encoding:'utf8',timeout:10000});
  assert.equal(concurrent.status,3,concurrent.stderr);
  assert.match(concurrent.stderr,/HUMAN_PROPOSAL_LOCK_BUSY/);
  return f.produce();
 }});
 assert.equal(f.signs(),1);
 assert.equal(fs.existsSync(path.join(f.directory,'synthetic-effect.marker')),false);
});
test('async callback is refused and leaves no retryable effect',t=>{
 const f=fixture(t);
 throws(()=>f.issue({guard:async()=>{}}),'HUMAN_PROPOSAL_ASYNC_CALLBACK');
 assert.equal(fs.existsSync(path.join(f.directory,'intent.json')),false);
 throws(()=>f.issue({produce:async()=>({})}),'HUMAN_PROPOSAL_ASYNC_CALLBACK');
 throws(()=>f.issue(),'HUMAN_PROPOSAL_EFFECT_UNKNOWN');
});
test('post-publication guard failure returns no success receipt; recovery cannot re-sign',t=>{
 const f=fixture(t);let calls=0;
 throws(()=>f.issue({guard:()=>{if(++calls===5)throw Object.assign(Error('AFTER_DRIFT'),{code:'AFTER_DRIFT'});}}),
  'AFTER_DRIFT');assert.equal(f.signs(),1);assert.equal(f.publishes(),1);
 assert.equal(f.issue().signerCalled,false);
});
test('publication cannot mutate the durable RESULT unnoticed',t=>{
 const f=fixture(t);
 throws(()=>f.issue({publish:()=>{
  const result=JSON.parse(fs.readFileSync(path.join(f.directory,'result.json')));
  result.intentHash=digest('tampered');replace(f,'result.json',result);
 }}),'HUMAN_PROPOSAL_RESULT_CONFLICT');assert.equal(f.signs(),1);
});
test('publication cannot mutate its artifact object into a misleading public digest',t=>{
 const f=fixture(t);
 throws(()=>f.issue({publish:artifacts=>{artifacts.body.purpose='mutated';}}),
  'HUMAN_PROPOSAL_RESULT_CONFLICT');
 assert.equal(f.issue().signerCalled,false);assert.equal(f.signs(),1);
});
test('actual process exit boundaries retain UNKNOWN or exact recoverable RESULT',t=>{
 const child=new URL('./fixtures/human-proposal-crash-child.mjs',import.meta.url).pathname;
 for(const stage of ['after_intent','after_effect','after_result','after_publish']){
  const f=fixture(t),crashed=spawnSync(process.execPath,[child,f.directory,stage],{encoding:'utf8',timeout:10000});
  assert.equal(crashed.status,91,crashed.stderr);
  assert.equal(fs.existsSync(path.join(f.directory,'synthetic-effect.marker')),stage!=='after_intent');
  if(['after_intent','after_effect'].includes(stage))throws(()=>f.issue(),'HUMAN_PROPOSAL_EFFECT_UNKNOWN');
  else{
   const receipt=f.issue({produce:()=>assert.fail('Never retry synthetic signing after process exit')});
   assert.equal(receipt.status,'SIGNED_PROPOSAL_ALREADY');assert.equal(receipt.signerCalled,false);
   verifyFixture(JSON.parse(fs.readFileSync(path.join(f.directory,'published.json'))));
  }
 }
});
