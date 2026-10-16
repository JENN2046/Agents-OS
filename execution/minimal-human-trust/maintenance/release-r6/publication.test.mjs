import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import {verify} from 'node:crypto';
import * as P from './publication.mjs';
import {inspectPhysicalPackage} from './maintenance-release-base.mjs';
const time=Date.now(),inspection=inspectPhysicalPackage({now:time}),h=P.createIsolatedPublicationHarness({inspection,now:time});
const artifacts=h.build({approvedAt:time-500,expiresAt:time+299500,releaseNotAfter:time+86400000,freezeDigest:P.digest('isolated-complete-freeze'),nonce:'r3_fixture_nonce_once'});
const rollbackDeadline=artifacts.approvedAt+1800000;
function fixture(t,overrides={}){
  const directory=fs.mkdtempSync(path.join(os.tmpdir(),'r3-publication-'));fs.chmodSync(directory,0o700);t.after(()=>fs.rmSync(directory,{recursive:true,force:true}));
  let clock=time;const counts={release:0,issuer:0},signer=async(role,body)=>{counts[role]++;return h.sign({role,body});};
  const make=extra=>P.createIsolatedSigner({harness:h,artifacts,directory,rollbackDeadline,now:()=>clock,signer,...overrides,...extra});
  return {directory,counts,make,setTime:x=>{clock=x;},getTime:()=>clock};
}
test('production functions reject nonroot fixture callers before private credential access',async()=>{
  await assert.rejects(P.signPublication({artifacts}),{code:'FIXED_ROOT_ONESHOT_REQUIRED'});
  await assert.rejects(P.signRollbackDelivery({artifacts,currentAcceptedDelivery:h.sourceDelivery,issuedAt:time}),{code:'FIXED_ROOT_ONESHOT_REQUIRED'});
  await assert.rejects(P.signPublication({artifacts,now:()=>time}),{code:'PRODUCTION_CLOCK_OVERRIDE_REFUSED'});
});
test('root production journal and unit paths are fixed, with no environment selector',()=>{
  assert.equal(P.ROOT_JOURNAL,'/var/lib/r16-maintenance/recovery-r6');assert.equal(P.UNIT,'r16-native-recovery-maintenance-r6.service');
  assert.equal(P.ROOT_PACKAGE,P.ROOT_JOURNAL+'/package');
  assert.equal(P.SOURCE_FREEZE,'/etc/r16-maintenance/recovery-r6-source-freeze.json');
});
test('separate original-role signatures, same Grant, and strict revision17 publish once',async t=>{
  const f=fixture(t),s=f.make(),r=await s.signPublication();assert.equal(r.revision,17);
  assert.deepEqual(r.publicConfig.grant,h.sourcePublicConfig.grant);assert.deepEqual(r.control,h.sourceDelivery.body.control);
  assert.equal(r.status,'SIGNED_NOT_INSTALLED');assert.equal(r.productionInstallationPerformed,false);
  assert.deepEqual(f.counts,{release:1,issuer:1});const old=await s.signPublication();assert.equal(old.historicalReadOnly,true);assert.deepEqual(f.counts,{release:1,issuer:1});
  for(const [e,k] of [[r.release,h.sourcePublicConfig.releasePublicKey],[r.delivery,h.sourcePublicConfig.issuerPublicKey]])
    assert.equal(verify(null,Buffer.from('R16-SIGNED\0'+P.canonical(e.body)),{key:Buffer.from(k,'base64url'),format:'der',type:'spki'},Buffer.from(e.signature,'base64url')),false);
});
test('restart after durable Release signature continues without signing it again',async t=>{
  const f=fixture(t),s=f.make({afterSave:name=>{if(name==='release')throw Error('crash after durable Release');}});
  await assert.rejects(s.signPublication(),/crash after durable Release/);assert.deepEqual(f.counts,{release:1,issuer:0});
  assert.equal((await f.make().signPublication()).revision,17);assert.deepEqual(f.counts,{release:1,issuer:1});
});
test('intent-only Release uncertainty never signs again',async t=>{
  const f=fixture(t,{signer:async role=>{f.counts[role]++;throw Error('lost signer response');}}),s=f.make();
  await assert.rejects(s.signPublication(),/lost signer response/);await assert.rejects(f.make().signPublication(),{code:'SIGNER_EFFECT_UNKNOWN'});
  assert.deepEqual(f.counts,{release:1,issuer:0});
});
test('known Release is durable before expiry blocks the next signing role',async t=>{
  const f=fixture(t),s=f.make({signer:async(role,body)=>{f.counts[role]++;const result=h.sign({role,body});f.setTime(artifacts.expiresAt);return result;}});
  await assert.rejects(s.signPublication(),{code:'PUBLICATION_WINDOW_EXPIRED'});assert.ok(s.readKnownSignatures().release);assert.equal(s.readKnownSignatures().delivery,null);
  await assert.rejects(f.make().signPublication(),{code:'PUBLICATION_WINDOW_EXPIRED'});assert.deepEqual(f.counts,{release:1,issuer:0});
});
test('known delivery survives expiry; result recovers inertly, then same-maintenance rollback works',async t=>{
  const f=fixture(t),s=f.make({signer:async(role,body)=>{f.counts[role]++;const result=h.sign({role,body});if(role==='issuer')f.setTime(artifacts.expiresAt);return result;}});
  await assert.rejects(s.signPublication(),{code:'PUBLICATION_WINDOW_EXPIRED'});assert.ok(s.readKnownSignatures().delivery);
  const restarted=f.make(),known=await restarted.signPublication();assert.equal(known.historicalReadOnly,true);assert.deepEqual(f.counts,{release:1,issuer:1});
  const rollback=await restarted.signRollbackDelivery({currentAcceptedDelivery:known.delivery,issuedAt:f.getTime()});
  assert.equal(rollback.delivery.body.revision,18);assert.deepEqual(rollback.delivery.body.publicConfig,h.sourcePublicConfig);assert.deepEqual(f.counts,{release:1,issuer:2});
});
test('partial installation before cloud acceptance rolls back with revision18, never a conflicting17',async t=>{
  const f=fixture(t),s=f.make();await s.signPublication();const r=await s.signRollbackDelivery({currentAcceptedDelivery:h.sourceDelivery,issuedAt:time});
  assert.equal(r.delivery.body.revision,18);assert.equal(r.preserveCurrentLedgers,true);assert.equal(r.restoreHistoricalLedgerSnapshot,false);
  assert.deepEqual(r.delivery.body.publicConfig,h.sourcePublicConfig);assert.deepEqual(f.counts,{release:1,issuer:2});
  assert.equal((await f.make().signRollbackDelivery({currentAcceptedDelivery:r.delivery,issuedAt:time+1000})).historicalReadOnly,true);
  assert.deepEqual(f.counts,{release:1,issuer:2});
});
test('rollback window expires without creating a new approval or signature',async t=>{
  const f=fixture(t),s=f.make(),r=await s.signPublication();f.setTime(rollbackDeadline);
  await assert.rejects(s.signRollbackDelivery({currentAcceptedDelivery:r.delivery,issuedAt:f.getTime()}),{code:'ROLLBACK_WINDOW_EXPIRED'});assert.deepEqual(f.counts,{release:1,issuer:1});
});
test('rollback signature returned at expiry is durably retained and recovered without resigning',async t=>{
  const f=fixture(t),r=await f.make().signPublication();
  const s=f.make({signer:async(role,body)=>{f.counts[role]++;const result=h.sign({role,body});f.setTime(rollbackDeadline);return result;}});
  await assert.rejects(s.signRollbackDelivery({currentAcceptedDelivery:r.delivery,issuedAt:time}),{code:'ROLLBACK_WINDOW_EXPIRED'});
  assert.ok(s.readKnownSignatures().rollback);const recovered=await f.make().signRollbackDelivery({currentAcceptedDelivery:r.delivery,issuedAt:time});
  assert.equal(recovered.historicalReadOnly,true);assert.equal(recovered.delivery.body.revision,18);assert.deepEqual(f.counts,{release:1,issuer:2});
});
test('rollback needs the original same-journal publication and never signs a foreign Grant',async t=>{
  const f=fixture(t),s=f.make();await assert.rejects(s.signRollbackDelivery({currentAcceptedDelivery:h.sourceDelivery,issuedAt:time}),{code:'ORIGINAL_PUBLICATION_REQUIRED'});
  const r=await s.signPublication(),foreign=h.sign({role:'issuer',body:{...r.delivery.body,control:{...r.delivery.body.control,grantId:'foreign'}}});
  await assert.rejects(s.signRollbackDelivery({currentAcceptedDelivery:foreign,issuedAt:time}),{code:'ROLLBACK_ACCEPTED_SCOPE_CHANGED'});assert.deepEqual(f.counts,{release:1,issuer:1});
});
test('cross-role signatures cannot be captured or published',async t=>{
  const f=fixture(t),s=f.make({signer:async(role,body)=>{f.counts[role]++;return h.sign({role:role==='release'?'issuer':'release',body});}});
  await assert.rejects(s.signPublication(),{code:'SIGNATURE_INVALID'});assert.equal(s.readKnownSignatures().release,null);
  await assert.rejects(f.make().signPublication(),{code:'SIGNER_EFFECT_UNKNOWN'});assert.equal(f.counts.release,1);
});
test('weak-mode journal result cannot be trusted on restart',async t=>{
  const f=fixture(t),s=f.make();await s.signPublication();fs.chmodSync(path.join(f.directory,'publication-result.json'),0o644);
  await assert.rejects(s.signPublication(),{code:'FILE_UNPROTECTED'});assert.deepEqual(f.counts,{release:1,issuer:1});
});
test('malformed known rollback evidence does not downgrade the target revision',async t=>{
  const f=fixture(t),s=f.make(),r=await s.signPublication();await s.signRollbackDelivery({currentAcceptedDelivery:r.delivery,issuedAt:time});
  const file=path.join(f.directory,'rollback-result.json'),v=JSON.parse(fs.readFileSync(file,'utf8'));v.delivery=h.sourceDelivery;fs.writeFileSync(file,JSON.stringify(v));
  await assert.rejects(s.signRollbackDelivery({currentAcceptedDelivery:r.delivery,issuedAt:time}),{code:'ROLLBACK_RESULT_CONFLICT'});
});
test('rollback with unknown signing effect never uses a new timestamp to sign again',async t=>{
  const f=fixture(t),r=await f.make().signPublication();const s=f.make({signer:async(role)=>{f.counts[role]++;throw Error('unknown rollback signature');}});
  await assert.rejects(s.signRollbackDelivery({currentAcceptedDelivery:r.delivery,issuedAt:time}),/unknown rollback signature/);
  await assert.rejects(f.make().signRollbackDelivery({currentAcceptedDelivery:r.delivery,issuedAt:time}),{code:'SIGNER_EFFECT_UNKNOWN'});
  f.setTime(time+1);await assert.rejects(f.make().signRollbackDelivery({currentAcceptedDelivery:r.delivery,issuedAt:time+1}),{code:'ROLLBACK_INTENT_CONFLICT'});assert.deepEqual(f.counts,{release:1,issuer:2});
});
test('a complete pending known signature recovers without signing it again',async t=>{
  const f=fixture(t),s=f.make({afterSave:name=>{if(name==='release')throw Error('pause');}});
  await assert.rejects(s.signPublication(),/pause/);
  fs.renameSync(path.join(f.directory,'release-signature.json'),path.join(f.directory,'.release-signature.json.pending'));
  assert.equal((await f.make().signPublication()).revision,17);assert.deepEqual(f.counts,{release:1,issuer:1});
  assert.equal(fs.existsSync(path.join(f.directory,'.release-signature.json.pending')),false);
});
test('a managed two-link result is verified and its stale link is removed',async t=>{
  const f=fixture(t),s=f.make({afterSave:name=>{if(name==='release')throw Error('pause');}});
  await assert.rejects(s.signPublication(),/pause/);
  const file=path.join(f.directory,'release-signature.json');fs.linkSync(file,path.join(f.directory,'.release-signature.json.pending'));
  assert.equal((await f.make().signPublication()).revision,17);assert.equal(fs.statSync(file).nlink,1);assert.deepEqual(f.counts,{release:1,issuer:1});
});
test('a partial pending signature remains uncertain and never triggers signing',async t=>{
  const f=fixture(t),s=f.make({afterSave:name=>{if(name==='release')throw Error('pause');}});
  await assert.rejects(s.signPublication(),/pause/);fs.unlinkSync(path.join(f.directory,'release-signature.json'));
  fs.writeFileSync(path.join(f.directory,'.release-signature.json.pending'),'{"body":',{mode:0o600});
  await assert.rejects(f.make().signPublication(),{code:'JOURNAL_RECORD_UNCERTAIN'});assert.deepEqual(f.counts,{release:1,issuer:0});
});
