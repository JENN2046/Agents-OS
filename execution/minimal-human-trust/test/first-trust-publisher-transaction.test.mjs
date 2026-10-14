import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import {stagePublisherOnce} from '../release/publisher-transaction.mjs';
import {canonical,digest} from '../src/lease-core.mjs';

const fail=(f,code)=>assert.throws(f,{code});
const fixture=t=>{
 const directory=fs.mkdtempSync(path.join(os.tmpdir(),'g1d-first-publisher-'));
 fs.chmodSync(directory,0o700);
 t.after(()=>fs.rmSync(directory,{recursive:true,force:true}));
 let signs=0;
 const signedArtifacts={schema:'test.signed.v1',publicReceipt:'synthetic-only'};
 const identity={schema:'mht.first-trust-signer-intent.v1',reviewedManifestHash:digest('source'),
  originalRelease:'r16-daily-20261012-r15',targetRelease:'r16-daily-20261012-r17',
  firstHumanDigest:digest('confirmed')};
 const sign=()=>{signs++;return signedArtifacts;};
 const verifyResult=x=>assert.deepEqual(x,signedArtifacts);
 const stage=(extra={})=>stagePublisherOnce({
  directory,identity,sign,verifyResult,...extra});
 return {directory,identity,sign,verifyResult,stage,signs:()=>signs};
};
test('one immutable intent and result are durable before one sign returns',t=>{
 const f=fixture(t);
 const result=f.stage();
 assert.equal(result.status,'SIGNED_STAGED');
 assert.equal(result.signerCalled,true);
 assert.equal(result.mayActivate,false);
 assert.equal(f.signs(),1);
 const intent=JSON.parse(fs.readFileSync(path.join(f.directory,'intent.json')));
 const saved=JSON.parse(fs.readFileSync(path.join(f.directory,'result.json')));
 assert.equal(intent.schema,f.identity.schema);
 assert.equal(saved.intentHash,digest(f.identity));
 assert.deepEqual(saved.signedArtifacts,{schema:'test.signed.v1',publicReceipt:'synthetic-only'});
});
test('lost successful reply returns exact result without re-signing or reapplying',t=>{
 const f=fixture(t);
 const a=f.stage();
 const b=f.stage({sign:()=>assert.fail('sign must never run twice')});
 assert.equal(b.status,'SIGNED_STAGED_ALREADY');
 assert.equal(b.signerCalled,false);
 assert.equal(a.resultHash,b.resultHash);
 assert.equal(f.signs(),1);
});
test('crash immediately after durable intent fails closed and never signs',t=>{
 const f=fixture(t);
 fail(()=>f.stage({fault:s=>{if(s==='after_intent')throw Object.assign(Error('FAULT'),{code:'FAULT'});}}),'FAULT');
 assert.equal(f.signs(),0);
 fail(()=>f.stage(),'PUBLISHER_EFFECT_UNKNOWN');
 assert.equal(f.signs(),0);
});
test('crash after private-key effect but before result preserves UNKNOWN',t=>{
 const f=fixture(t);
 fail(()=>f.stage({fault:s=>{if(s==='after_effect')throw Object.assign(Error('FAULT'),{code:'FAULT'});}}),'FAULT');
 assert.equal(f.signs(),1);
 fail(()=>f.stage(),'PUBLISHER_EFFECT_UNKNOWN');
 assert.equal(f.signs(),1);
});
test('crash after committed result is safe to read without another sign',t=>{
 const f=fixture(t);
 fail(()=>f.stage({fault:s=>{if(s==='after_result')throw Object.assign(Error('FAULT'),{code:'FAULT'});}}),'FAULT');
 assert.equal(f.signs(),1);
 const b=f.stage({sign:()=>assert.fail('double-sign')});
 assert.equal(b.status,'SIGNED_STAGED_ALREADY');
 assert.equal(f.signs(),1);
});
test('a new or modified intent cannot reuse an existing publisher result',t=>{
 const f=fixture(t);f.stage();
 fail(()=>f.stage({identity:{...f.identity,firstHumanDigest:digest('other')}}),'PUBLISHER_INTENT_CONFLICT');
 assert.equal(f.signs(),1);
});
test('orphan result without a matching intent cannot justify a new signature',t=>{
 const f=fixture(t);f.stage();
 fs.unlinkSync(path.join(f.directory,'intent.json'));
 fail(()=>f.stage(),'PUBLISHER_ORPHAN_RESULT');
});
test('result tamper is refused even when the original intent is exact',t=>{
 const f=fixture(t);f.stage();
 const p=path.join(f.directory,'result.json');
 const changed=JSON.parse(fs.readFileSync(p));
 changed.signedArtifacts={schema:'test.signed.v1',publicReceipt:'modified'};
 fs.writeFileSync(p,canonical(changed),{mode:0o600});
 assert.throws(()=>f.stage());
});
test('weak or symlinked publisher result never becomes trusted',t=>{
 const f=fixture(t);f.stage();
 const p=path.join(f.directory,'result.json');
 fs.chmodSync(p,0o644);
 fail(()=>f.stage(),'PUBLISHER_STATE_UNTRUSTED');
});
test('weak transaction directory is rejected before creating a signer intent',t=>{
 const f=fixture(t);fs.chmodSync(f.directory,0o777);
 fail(()=>f.stage(),'PUBLISHER_DIRECTORY');
});
test('flock contention blocks signing and does not leave an intent',t=>{
 const f=fixture(t);
 fail(()=>f.stage({run:()=>({status:1})}),'PUBLISHER_LOCK_BUSY');
 assert.equal(fs.existsSync(path.join(f.directory,'intent.json')),false);
 assert.equal(f.signs(),0);
});
test('a valid result is revalidated on every readback',t=>{
 const f=fixture(t);f.stage();
 fail(()=>f.stage({verifyResult:()=>{throw Object.assign(Error('BAD_SIGNATURE'),{code:'BAD_SIGNATURE'});}}),'BAD_SIGNATURE');
 assert.equal(f.signs(),1);
});

test('actual child process exits at signature-effect and durable-result boundaries',async t=>{
 const {spawnSync}=await import('node:child_process');
 const child=new URL('./fixtures/first-trust-publisher-crash-child.mjs',import.meta.url).pathname;
 const identity={schema:'mht.first-trust-signer-intent.v1',
   reviewedManifestHash:digest('fixture-reviewed-r17')};
 const expected={schema:'synthetic-test-signature.v1',hash:digest('not-production')};
 for(const crash of ['after_effect','after_result']){
  const dir=fs.mkdtempSync(path.join(os.tmpdir(),'g1d-publisher-process-'));
  fs.chmodSync(dir,0o700);
  t.after(()=>fs.rmSync(dir,{recursive:true,force:true}));
  const childRun=spawnSync(process.execPath,[child,dir,crash],{
    encoding:'utf8',timeout:10000,env:{PATH:process.env.PATH}});
  assert.equal(childRun.status,91,childRun.stderr);
  assert.equal(fs.readFileSync(path.join(dir,'synthetic-effect.marker'),'utf8'),'called');
  const next=()=>stagePublisherOnce({
    directory:dir,identity,
    sign:()=>assert.fail('Never sign twice after child process exit'),
    verifyResult:result=>assert.deepEqual(result,expected)});
  if(crash==='after_effect')assert.throws(next,{code:'PUBLISHER_EFFECT_UNKNOWN'});
  else{
    const receipt=next();
    assert.equal(receipt.status,'SIGNED_STAGED_ALREADY');
    assert.equal(receipt.signerCalled,false);
  }
 }
});
