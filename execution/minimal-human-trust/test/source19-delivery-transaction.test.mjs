import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import {pathToFileURL} from 'node:url';
import {generateKeyPairSync,createHash} from 'node:crypto';
import {ProtectedStore,canonical,digest,signed,verified,exportPublicKey,ACTIONS} from '../src/lease-core.mjs';
import {inspectSourcePublicConfiguration,SOURCE19_BASELINE} from '../authority/source-baseline.mjs';
import * as production from '../release/source19-delivery-transaction.mjs';
import {verifyDelivery} from '../deployment/cloud-configuration-receiver.mjs';
const root=new URL('../',import.meta.url),fixtureFile=new URL('fixtures/source19-native-trusted-launcher.mjs',import.meta.url);
const sha=b=>createHash('sha256').update(b).digest('hex');
const url=s=>'data:text/javascript;base64,'+Buffer.from(s).toString('base64');
const absolutize=(s,base)=>s.replace(/(from\s+['"])(\.\.?\/[^'"]+)(['"])/g,(_,a,b,c)=>a+new URL(b,base).href+c);
const key=()=>generateKeyPairSync('ed25519').privateKey;
const clone=o=>JSON.parse(canonical(o));
// Explicit test boundary: only immutable SOURCE19 public pins are replaced with
// ephemeral signed fixture pins. Production exports expose NO pin override.
// All plan validation, crypto, journals, receivers and Owner cache code is real.
async function fixture(t){
 const dir=fs.mkdtempSync(path.join(os.tmpdir(),'source19-delivery-'));fs.chmodSync(dir,0o700);
 let clock=Date.now();const now=()=>clock,issuer=key(),releaseKey=key();
 const peers=Object.fromEntries(['app','bridge','native'].map(role=>[role,{id:'peer-'+role,publicKey:exportPublicKey(key())}]));
 const manifest=n=>({schema:'r16.runtime-code.v1',role:'native',entry:'host/native-runner.mjs',files:{'host/native-runner.mjs':sha(Buffer.from('export const fixture='+n+';'))}});
 const sourceManifest=manifest(1),targetManifest=manifest(2);
 const versions={app:digest('old-app'),bridge:digest('bridge'),native:digest(sourceManifest)};
 const targetVersions={app:digest('new-app'),bridge:versions.bridge,native:digest(targetManifest)};
 const grant=signed({schema:'r16.workspace.v1',id:'r16-projects-daily',version:1,createdAt:clock-10000,workspace:{id:'ws_8c7dd971e518',root:'/home/jenn/AGENTS_OS_Workspace/projects',dev:1,ino:2},actions:ACTIONS,channel:'main',peers},issuer);
 const release=(id,v)=>signed({schema:'r16.release.v1',id,issuedAt:clock-10000,notAfter:clock+86400000,formats:['r16.workspace.v1'],versions:v,actions:ACTIONS,permissionVersion:1},releaseKey);
 const old=release(SOURCE19_BASELINE.releaseId,versions),target=release('r17-source19-ephemeral-fixture',targetVersions);
 const pub={schema:'r16.runtime-configuration.v1',issuerPublicKey:exportPublicKey(issuer),releasePublicKey:exportPublicKey(releaseKey),release:old,grant,peers,versions,channel:'main'};
 const control={grantId:grant.body.id,grantVersion:1,status:'ACTIVE',connectRequested:true};
 const source=signed({schema:'r16.configuration-delivery.v1',revision:19,issuedAt:clock-1000,publicConfig:pub,control},issuer);
 const spec={...SOURCE19_BASELINE,acceptedDeliveryHash:digest(source),publicConfigDigest:digest(pub),releaseHash:digest(old),grantHash:digest(grant),versions};
 let baseline=fs.readFileSync(new URL('authority/source-baseline.mjs',root),'utf8');
 baseline=baseline.replace(/export const SOURCE19_BASELINE=freeze\(\{[\s\S]*?\n\}\);/,'export const SOURCE19_BASELINE=freeze('+canonical(spec)+');');
 baseline=absolutize(baseline,new URL('authority/source-baseline.mjs',root));
 let code=fs.readFileSync(new URL('release/source19-delivery-transaction.mjs',root),'utf8');
 code=code.replace("'../authority/source-baseline.mjs'",JSON.stringify(url(baseline)));
 const m=await import(url(absolutize(code,new URL('release/source19-delivery-transaction.mjs',root))));
 const plan={schema:'mht.source19-fixed-delivery-plan.v1',nonce:digest('unique-'+dir),mode:'recovery_only',sourceRevision:19,sourceDeliveryHash:digest(source),sourcePublicHash:digest(pub),forwardRevision:21,recoveryRevision:22,targetReleaseHash:digest(target),targetVersions,grantHash:digest(grant),stopEpoch:digest('epoch'),handoffHash:digest('completed-handoff'),preservedStateHash:digest('original-2-UNKNOWN-and-old-leases'),approvedAt:clock,expiresAt:clock+300000,recoveryDeadline:clock+1800000,connectRequested:false,allowForwardRecovery22:true};
 const inputs={plan,sourceDelivery:source,targetRelease:target};
 const opened=[];
 const make=(name,initial)=>{const d=path.join(dir,name),s=new ProtectedStore({directory:d,create:true,initial,now});s.close();return()=>new ProtectedStore({directory:d,now});};
 const openCloud=make('cloud',{kind:'r16.cloud-publication.v1',accepted:source,projectedDigest:digest(source)});
 const cache={hash:digest({publicConfig:pub,control,connectionNonce:7}),revision:19,envelope:source};
 const initialLocal={kind:'r16.owner.configuration.v1',connected:true,connectionNonce:7,activeGrantId:grant.body.id,originalUnknown:[{id:'old1',status:'UNKNOWN',leaseHash:digest('old-lease1')},{id:'old2',status:'UNKNOWN',leaseHash:digest('old-lease2')}],delivery:cache,trust:{historical:'unchanged'}};
 const openLocal=make('local',initialLocal);
 const journal=new ProtectedStore({directory:path.join(dir,'journal'),create:true,initial:m.deliveryTransactionInitialState(),now});opened.push(journal);
 const get=open=>{const s=open();try{return s.snapshot();}finally{s.close();}};
 const published=new Map([['/etc/r16-cloud/public-config.json',pub],['/etc/r16-cloud/authority-control.json',control]]);let localPublic=pub;
 const calls={sign:[],cloud:[],local:[],forbidden:0,requirements:[]};
 const backend={
  require:r=>{calls.requirements.push(r);},
  fresh:()=>({planHash:digest(plan),stopEpoch:plan.stopEpoch,handoffHash:plan.handoffHash,singleWriter:'HANDOFF_ACCEPTED_OWNER_FENCED',preservedStateHash:plan.preservedStateHash}),
  sign:b=>{calls.sign.push(b.revision);return signed(b,issuer);},
  readCloud:()=>{const s=get(openCloud);return {accepted:s.accepted,publicConfig:published.get('/etc/r16-cloud/public-config.json'),control:published.get('/etc/r16-cloud/authority-control.json'),projectedDigest:s.projectedDigest,preservedStateHash:plan.preservedStateHash};},
  readLocal:()=>{const s=get(openLocal);return {accepted:s.delivery.envelope,publicConfig:localPublic,control:s.delivery.envelope.body.control,projectedDigest:digest(s.delivery.envelope),preservedStateHash:plan.preservedStateHash};}
 };
 const forbid=()=>{calls.forbidden++;throw Error('FORBIDDEN_CREDENTIAL_LEDGER_OR_SERVICE_EFFECT');};
 const cloudOptions={read:file=>Buffer.from(canonical(file==='/etc/r16-cloud/issuer-pin.json'?{issuerPublicKey:pub.issuerPublicKey,releasePublicKey:pub.releasePublicKey}:published.get(file))),write:(file,value)=>published.set(file,value),openStore:openCloud,ensureCredentials:forbid,initializeLedgers:forbid,reconcile:forbid,status:()=>({credentialsInvalid:false})};
 const cloud=m.createExactCloudReceiver({inputs,backend,now,options:cloudOptions});
 const local=m.createFencedLocalReceiver({inputs,backend,now,openStore:openLocal,readPublic:()=>localPublic,writePublic:v=>{localPublic=v;}});
 backend.commitCloud=e=>{calls.cloud.push(e.body.revision);return cloud(e);};
 backend.commitLocal=e=>{calls.local.push(e.body.revision);return local(e);};
 const run=(options={})=>m.runDeliveryTransaction({journal,backend,...inputs,now,...options});
 t.after(()=>{for(const s of opened)try{s.close();}catch{}fs.rmSync(dir,{recursive:true,force:true});});
 return {m,dir,inputs,plan,pub,source,target,issuer,releaseKey,backend,journal,run,calls,cloud,local,get,openLocal,openCloud,initialLocal,published,cloudOptions,now,advance:n=>clock+=n,sourceManifest,targetManifest};
}
test('real source19 public fixture is immutable and production API has no baseline override',()=>{
 const p=JSON.parse(fs.readFileSync(new URL('fixtures/SOURCE19_PUBLIC_CONFIG.json',import.meta.url)));
 assert.equal(inspectSourcePublicConfiguration(p),SOURCE19_BASELINE);
 assert.equal(production.DELIVERY_READINESS,'READY_UNINSTALLED');
 assert.deepEqual(production.DELIVERY_REVISIONS,{source:19,forward:21,recovery:22});
});
test('21 integrates actual cloud receiver + real protected Owner cache without service or business effects',async t=>{
 const f=await fixture(t),before=f.get(f.openLocal),r=f.run();
 assert.equal(r.status,'FORWARD_21_STORED_RECOVERY_ONLY');assert.equal(r.readiness,'READY_UNINSTALLED');assert.equal(r.entryImplementation,'ENTRY_UNIMPLEMENTED');assert.equal(r.productionAcceptance,'NOT_PROVEN');
 assert.deepEqual(f.calls.sign,[21]);assert.deepEqual(f.calls.cloud,[21]);assert.deepEqual(f.calls.local,[21]);assert.equal(f.calls.forbidden,0);
 const after=f.get(f.openLocal),oldInvariant={...before},newInvariant={...after};delete oldInvariant.delivery;delete newInvariant.delivery;
 assert.equal(canonical(oldInvariant),canonical(newInvariant));
 assert.equal(after.delivery.hash,digest({publicConfig:after.delivery.envelope.body.publicConfig,control:after.delivery.envelope.body.control,connectionNonce:7}));
 assert.equal(after.delivery.envelope.body.control.connectRequested,false);
 assert.deepEqual(f.run(),r);assert.deepEqual(f.calls.sign,[21]);
});
test('partial local21 failure produces fixed recovery22 on both actual persistence chains, no old-ledger restore',async t=>{
 const f=await fixture(t),real=f.backend.commitLocal;
 f.backend.commitLocal=e=>{if(e.body.revision===21)throw Object.assign(Error('no write'),{code:'FIXTURE_LOCAL_REFUSED'});return real(e);};
 const r=f.run();assert.equal(r.revision,22);assert.equal(r.originalLedger,'PRESERVED_NOT_RESTORED');
 assert.deepEqual(f.calls.sign,[21,22]);assert.equal(f.backend.readCloud().accepted.body.publicConfig.release.body.id,f.pub.release.body.id);
 assert.equal(f.backend.readLocal().accepted.body.control.connectRequested,false);assert.equal(f.calls.forbidden,0);
 assert.deepEqual(f.get(f.openLocal).originalUnknown,f.initialLocal.originalUnknown);
});
test('lost cloud and local ACK are reconciled by exact readback without replay or another signature',async t=>{
 const f=await fixture(t);for(const side of ['commitCloud','commitLocal']){const real=f.backend[side];f.backend[side]=e=>{real(e);throw Error('LOST_ACK');};}
 assert.equal(f.run().revision,21);assert.deepEqual(f.calls.sign,[21]);assert.deepEqual(f.calls.cloud,[21]);assert.deepEqual(f.calls.local,[21]);
});
for(const crash of ['forward-sign:intent','forward-sign:effect'])test('signature '+crash+' is UNKNOWN across reentry, never signed again',async t=>{
 const f=await fixture(t);assert.throws(()=>f.run({fault:p=>{if(p===crash)throw Error('POWER_LOSS');}}));
 const n=f.calls.sign.length;assert.throws(()=>f.run(),/DELIVERY_SIGNATURE_UNKNOWN/);assert.equal(f.calls.sign.length,n);assert.throws(()=>f.run({mode:'RECOVER'}),/DELIVERY_SIGNATURE_UNKNOWN/);assert.equal(f.calls.sign.length,n);assert.equal(f.calls.cloud.length,0);
});
test('known signature is saved even if signer returns after native expiry; no forward commit or resign',async t=>{
 const f=await fixture(t),real=f.backend.sign;f.backend.sign=b=>{const e=real(b);f.advance(1800001);return e;};
 assert.throws(()=>f.run(),/DELIVERY_AUTHORITY_EXPIRED/);assert.equal(f.journal.snapshot().steps['forward-sign'].status,'RESULT');assert.deepEqual(f.calls.cloud,[]);assert.deepEqual(f.calls.sign,[21]);
});
test('saved commit INTENT with unknown readback never resends that external call',async t=>{
 const f=await fixture(t);f.backend.commitLocal=e=>{throw Error('UNKNOWN_NETWORK');};
 assert.throws(()=>f.run(),/UNKNOWN_NETWORK/);assert.deepEqual(f.calls.sign,[21,22]);
 let calls=0;f.backend.commitLocal=()=>{calls++;throw Error('MUST_NOT_REPLAY');};
 assert.throws(()=>f.run(),/DELIVERY_READBACK_NOT_EXACT/);assert.equal(calls,0);assert.deepEqual(f.calls.sign,[21,22]);
});
test('source revision20, arbitrary jump, true connect, changed grant and bad target cannot enter signing',async t=>{
 const f=await fixture(t);
 for(const patch of [{sourceRevision:20},{forwardRevision:20},{forwardRevision:23},{recoveryRevision:23},{connectRequested:true},{allowForwardRecovery22:false},{grantHash:digest('replacement')},{targetReleaseHash:digest('different')}]){
  assert.throws(()=>f.run({plan:{...f.plan,...patch}}));
 }
 assert.deepEqual(f.calls.sign,[]);assert.equal(f.journal.snapshot().binding,null);
});
test('missing production backend refuses without journal mutation',async t=>{
 const f=await fixture(t);assert.throws(()=>f.run({backend:undefined}),/DELIVERY_BACKEND_UNINSTALLED/);assert.equal(f.journal.snapshot().binding,null);
});
test('expired admission, epoch drift, ledger drift and still-running Owner all refuse before signing',async t=>{
 const f=await fixture(t),fresh=f.backend.fresh;
 for(const patch of [{stopEpoch:digest('new')},{handoffHash:digest('new')},{preservedStateHash:digest('changed')},{singleWriter:'OWNER_STILL_RUNNING'}]){
  f.backend.fresh=()=>({...fresh(),...patch});assert.throws(()=>f.run(),/DELIVERY_FRESH_SCOPE_CHANGED/);
 }
 f.backend.fresh=fresh;f.advance(300000);assert.throws(()=>f.run(),/DELIVERY_AUTHORITY_EXPIRED/);assert.deepEqual(f.calls.sign,[]);
});
test('fresh guard is rechecked immediately before signature after durable intent',async t=>{
 const f=await fixture(t);let n=0;f.backend.require=r=>{if(r.operation==='forward-sign'&&++n===2)throw Object.assign(Error('expired'),{code:'NATIVE_EXPIRED'});};
 assert.throws(()=>f.run(),/expired/);assert.deepEqual(f.calls.sign,[]);assert.equal(f.journal.snapshot().steps['forward-sign'].status,'INTENT');
});
test('old receiver default remains strict and cannot accept false-connect newrelease21',async t=>{
 const f=await fixture(t),next=signed(f.m.deliveryBody(f.inputs,'forward'),f.issuer);
 assert.throws(()=>verifyDelivery(next,{issuerPublicKey:f.pub.issuerPublicKey,releasePublicKey:f.pub.releasePublicKey},f.source,f.now()),/RECOVERY_RELEASE_NOT_PINNED/);
});
test('cloud/local22 monotonic readback refuses delayed21 and same-revision different signatures/body',async t=>{
 const f=await fixture(t),a=signed(f.m.deliveryBody(f.inputs,'forward'),f.issuer),b=signed(f.m.deliveryBody(f.inputs,'recovery'),f.issuer);
 f.cloud(a);f.local(a);f.cloud(b);f.local(b);
 assert.throws(()=>f.cloud(a),/CONFIGURATION_ROLLBACK/);assert.throws(()=>f.local(a),/CONFIGURATION_ROLLBACK/);
 const changed=signed({...b.body,issuedAt:b.body.issuedAt+1},f.issuer);assert.throws(()=>f.cloud(changed),/DELIVERY_PLAN_CONFLICT/);
});
test('ACK missing exact deliveryDigest is rejected, then approved recovery22 is delivered',async t=>{
 const f=await fixture(t),real=f.backend.commitCloud;f.backend.commitCloud=e=>{const r=real(e);return e.body.revision===21?{status:'STORED',revision:21}:r;};
 assert.equal(f.run().revision,22);assert.equal(f.journal.snapshot().failures[0].code,'DELIVERY_ACK_NOT_EXACT');
});
test('local projection crash keeps exact durable cache and repairs only through same-envelope explicit receiver',async t=>{
 const f=await fixture(t),a=signed(f.m.deliveryBody(f.inputs,'forward'),f.issuer);let projection=f.pub;
 const receiver=f.m.createFencedLocalReceiver({inputs:f.inputs,backend:f.backend,now:f.now,openStore:f.openLocal,readPublic:()=>projection,writePublic:()=>{throw Error('FIXTURE_PROJECT_CRASH');}});
 assert.throws(()=>receiver(a),/FIXTURE_PROJECT_CRASH/);assert.deepEqual(f.get(f.openLocal).delivery.envelope,a);
 assert.equal(f.local(a).revision,21);assert.equal(f.backend.readLocal().projectedDigest,digest(a));
});
// Original physical Native bootstrap bytes are copied verbatim and pinned. The
// ONLY test seam is filesystem metadata/contents (root-owned synthetic files).
// Real release signature/time, selected manifest and per-file hashes execute.
async function nativeFixture(){
 const raw=fs.readFileSync(fixtureFile,'utf8');assert.equal(sha(raw),'4583ddd8c1fca94881b5a05919ae59a173743682ae6d121c05bc6ffd10885e27');
 const token='__source19NativeIO'+Math.random().toString(16).slice(2);
 const files=new Map();const fakefs={lstatSync:p=>({uid:0,mode:files.has(p)?0o100644:0o40755,nlink:1,size:files.get(p)?.length||0,isSymbolicLink:()=>false,isFile:()=>files.has(p)}),readFileSync:p=>{assert.ok(files.has(p),p);return files.get(p);}};
 globalThis[token]=fakefs;
 const source=raw.replace("import fs from 'node:fs';",'const fs=globalThis['+JSON.stringify(token)+'];');
 const module=await import(url(source));delete globalThis[token];return {module,files};
}
test('actual Native entry validates21/22 inputs WHEN installer has selected matching manifests; no selector installation/start is exercised',async t=>{
 const f=await fixture(t),n=await nativeFixture();
 for(const [phase,manifest,body] of [['forward',f.targetManifest,'export const fixture=2;'],['recovery',f.sourceManifest,'export const fixture=1;']]){
  const delivery=signed(f.m.deliveryBody(f.inputs,phase),f.issuer);f.local(delivery);
  const base='/opt/r16/releases/'+delivery.body.publicConfig.release.body.id;
  n.files.set('/etc/r16/native-host.json',Buffer.from(canonical({schema:'r16.native-host.v1',publicConfiguration:'/run/r16-owner/public-config.json',codeManifest:base+'/native-manifest.json'})));
  n.files.set('/run/r16-owner/public-config.json',Buffer.from(canonical(f.backend.readLocal().publicConfig)));
  n.files.set('/etc/r16/cutover.json',Buffer.from(canonical({schema:'r16.local-cutover.v1',phase:'ACTIVE',grantId:f.pub.grant.body.id})));
  n.files.set(base+'/native-manifest.json',Buffer.from(canonical(manifest)));n.files.set(base+'/host/native-runner.mjs',Buffer.from(body));
  const checked=n.module.verifyNativeRelease('/etc/r16/native-host.json');assert.equal(checked.publicConfig.release.body.id,delivery.body.publicConfig.release.body.id);assert.equal(checked.manifest.entry,'host/native-runner.mjs');
  n.files.set(base+'/host/native-runner.mjs',Buffer.from('tampered'));assert.throws(()=>n.module.verifyNativeRelease('/etc/r16/native-host.json'),/R16_RELEASE_REJECTED/);
 }
});


test('cloud receiver rechecks native expiry between durable public and control projection writes',async t=>{
 const f=await fixture(t),a=signed(f.m.deliveryBody(f.inputs,'forward'),f.issuer);
 const receiver=f.m.createExactCloudReceiver({inputs:f.inputs,backend:f.backend,now:f.now,options:{...f.cloudOptions,write:(file,value)=>{f.cloudOptions.write(file,value);if(file==='/etc/r16-cloud/public-config.json')f.advance(300000);}}});
 assert.throws(()=>receiver(a),/DELIVERY_AUTHORITY_EXPIRED/);
 assert.equal(f.get(f.openCloud).accepted.body.revision,21);
 assert.equal(f.published.get('/etc/r16-cloud/public-config.json').release.body.id,f.target.body.id);
 assert.equal(f.published.get('/etc/r16-cloud/authority-control.json').connectRequested,true);
 assert.equal(f.get(f.openCloud).projectedDigest,digest(f.source));assert.equal(f.calls.forbidden,0);
});
test('real cloud partial21 projection recovers via22 while preserving original21 INTENT and business bytes',async t=>{
 const f=await fixture(t),old=f.backend.commitCloud;let once=true;
 const broken=f.m.createExactCloudReceiver({inputs:f.inputs,backend:f.backend,now:f.now,options:{...f.cloudOptions,write:(file,value)=>{if(file==='/etc/r16-cloud/authority-control.json'&&once){once=false;throw Object.assign(Error('partial'),{code:'FIXTURE_PARTIAL_PROJECTION'});}f.cloudOptions.write(file,value);}}});
 f.backend.commitCloud=e=>e.body.revision===21?broken(e):old(e);
 const before=canonical(f.get(f.openLocal).originalUnknown),r=f.run();assert.equal(r.revision,22);
 assert.equal(f.journal.snapshot().steps['forward-cloud'].status,'INTENT');
 assert.equal(f.journal.snapshot().steps['recovery-cloud'].status,'RESULT');
 assert.equal(canonical(f.get(f.openLocal).originalUnknown),before);assert.equal(f.calls.forbidden,0);
});
test('genuine protected journal reopen retains unknown signer intent without a replacement signature',async t=>{
 const f=await fixture(t);assert.throws(()=>f.run({fault:p=>{if(p==='forward-sign:effect')throw Error('LOST_SIGNER_RESULT');}}));
 f.journal.close();const reopened=new ProtectedStore({directory:path.join(f.dir,'journal'),now:f.now});
 try{assert.throws(()=>f.run({journal:reopened}),/DELIVERY_SIGNATURE_UNKNOWN/);assert.deepEqual(f.calls.sign,[21]);assert.equal(f.calls.cloud.length,0);}finally{reopened.close();}
});
test('pre-sign fresh actual accepted revision outside exact plan is rejected before INTENT',async t=>{
 const f=await fixture(t),read=f.backend.readCloud;
 f.backend.readCloud=()=>({...read(),accepted:signed({...f.source.body,revision:20},f.issuer)});
 assert.throws(()=>f.run(),/DELIVERY_CURRENT_SCOPE_CHANGED/);assert.deepEqual(f.calls.sign,[]);assert.equal(f.journal.snapshot().binding,null);
});
test('epoch drift after local cache commit blocks public projection and leaves durable intent observable',async t=>{
 const f=await fixture(t),a=signed(f.m.deliveryBody(f.inputs,'forward'),f.issuer),fresh=f.backend.fresh;
 f.backend.require=r=>{if(r.operation==='local-project')f.backend.fresh=()=>({...fresh(),stopEpoch:digest('changed')});};
 assert.throws(()=>f.local(a),/DELIVERY_FRESH_SCOPE_CHANGED/);
 assert.equal(f.get(f.openLocal).delivery.revision,21);assert.equal(f.backend.readLocal().publicConfig.release.body.id,f.pub.release.body.id);
});

test('local received envelope cannot bypass a corrupted Owner cache binding',async t=>{
 const f=await fixture(t),s=f.openLocal();s.transact(x=>{x.delivery.hash=digest('wrong-cache');});s.close();
 const a=signed(f.m.deliveryBody(f.inputs,'forward'),f.issuer);
 assert.throws(()=>f.local(a),/LOCAL_DELIVERY_CACHE_CONFLICT/);assert.equal(f.get(f.openLocal).delivery.revision,19);
});

test('target Release expiry inside native window refuses forward before signature or intent',async t=>{
 const f=await fixture(t);
 const expired=signed({...f.target.body,notAfter:f.plan.approvedAt+1},f.releaseKey);
 f.inputs.targetRelease=expired;f.plan.targetReleaseHash=digest(expired);f.advance(2);
 assert.throws(()=>f.run({targetRelease:expired}),/RELEASE_EXPIRED/);assert.deepEqual(f.calls.sign,[]);assert.equal(f.journal.snapshot().binding,null);
});
test('known target signature may expire and still recover to historical source22 within approved recovery window',async t=>{
 const f=await fixture(t),short=signed({...f.target.body,notAfter:f.plan.approvedAt+1},f.releaseKey);
 f.inputs.targetRelease=short;f.plan.targetReleaseHash=digest(short);
 const sign=f.backend.sign;f.backend.sign=b=>{const e=sign(b);if(b.revision===21)f.advance(2);return e;};
 const r=f.run({targetRelease:short});assert.equal(r.revision,22);assert.deepEqual(f.calls.sign,[21,22]);assert.equal(f.backend.readCloud().accepted.body.publicConfig.release.body.id,f.pub.release.body.id);
});
