import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import {generateKeyPairSync} from 'node:crypto';
import {ProtectedStore,issuerInitialState,signed,verified,exportPublicKey,
  digest,ACTIONS} from '../src/lease-core.mjs';
import {cloudDeliveryInitialState,createCloudDeliveryProjector} from '../src/cloud-delivery-projector.mjs';
import {verifyDelivery,acceptConfiguration,reconcileServices} from '../deployment/cloud-configuration-receiver.mjs';
const key=()=>generateKeyPairSync('ed25519').privateKey;
const denied=(f,code)=>assert.throws(f,{code});
function fixture(t){
 const dir=fs.mkdtempSync(path.join(os.tmpdir(),'g1d-cloud-'));fs.chmodSync(dir,0o700);
 const issuerKey=key(),releaseKey=key(),keys={app:key(),bridge:key(),native:key()};
 const peers=Object.fromEntries(Object.entries(keys).map(([role,k])=>[role,
   {id:'peer-'+role,publicKey:exportPublicKey(k)}]));
 let time=1791859000000;const now=()=>time;
 const publicIssuer=exportPublicKey(issuerKey),publicRelease=exportPublicKey(releaseKey);
 const grant=signed({schema:'r16.workspace.v1',id:'r16-projects-daily',version:1,createdAt:time-86400000,
   workspace:{id:'ws_8c7dd971e518',root:'/home/jenn/AGENTS_OS_Workspace/projects',dev:1,ino:2},
   actions:ACTIONS,channel:'main',peers},issuerKey);
 const versions={app:digest('app'),bridge:digest('bridge'),native:digest('native')};
 const release=signed({schema:'r16.release.v1',id:'r16-daily-20261012-r15',
   issuedAt:time-86400000,notAfter:time+86400000,formats:['r16.workspace.v1'],
   versions,actions:ACTIONS,permissionVersion:1},releaseKey);
 const publicConfig={schema:'r16.runtime-configuration.v1',issuerPublicKey:publicIssuer,
   releasePublicKey:publicRelease,release,grant,peers,versions,channel:'main'};
 const control={grantId:grant.body.id,grantVersion:1,status:'ACTIVE',connectRequested:true};
 const prior=signed({schema:'r16.configuration-delivery.v1',revision:87,
   issuedAt:time-1000,publicConfig,control},issuerKey);
 const stores=[];
 const open=(n,initial)=>{const s=new ProtectedStore({directory:path.join(dir,n),create:true,initial,now});stores.push(s);return s;};
 const issuerStore=open('issuer',issuerInitialState());
 issuerStore.transact(s=>{s.grants.push({grant,version:1,status:'ACTIVE',projects:[],revocationAcks:[]});});
 const projectionStore=open('projection',cloudDeliveryInitialState(prior));
 const receiverStore=open('cloud',{kind:'r16.cloud-publication.v1',accepted:prior});
 receiverStore.close();
 const openReceiver=()=>new ProtectedStore({directory:path.join(dir,'cloud'),create:false,now});
 const readReceiver=()=>{const s=openReceiver();try{return s.snapshot();}finally{s.close();}};
 const projector=()=>createCloudDeliveryProjector({
   deliveryStore:projectionStore,issuerStore,issuerSigningKey:issuerKey,issuerPublicKey:publicIssuer,
   releasePublicKey:publicRelease,release,now});
 const pin={issuerPublicKey:publicIssuer,releasePublicKey:publicRelease};
 const published=new Map();
 const accept=packet=>acceptConfiguration(packet,{
   read:filename=>{if(filename==='/etc/r16-cloud/issuer-pin.json')return Buffer.from(JSON.stringify(pin));
     if(published.has(filename))return Buffer.from(JSON.stringify(published.get(filename)));
     throw Error('UNEXPECTED_PRIVATE_READ');},
   write:(file,obj)=>{published.set(file,obj);},
   ensureCredentials:()=>{throw Error('NO_REAL_CREDENTIAL_INSTALL_IN_TEST');},
   initializeLedgers:()=>{},
   reconcile:()=>{throw Error('NO_REAL_SERVICE_RESTART_IN_TEST');},
   status:()=>({credentialsInvalid:false}),now:time,openStore:openReceiver
 });
 const safeAccept=packet=>acceptConfiguration(packet,{
   read:filename=>{if(filename==='/etc/r16-cloud/issuer-pin.json')return Buffer.from(JSON.stringify(pin));assert.ok(published.has(filename));return Buffer.from(JSON.stringify(published.get(filename)));},
   write:(file,obj)=>published.set(file,obj),
   ensureCredentials:()=>{},
   initializeLedgers:()=>{},
   reconcile:()=>false,
   status:()=>({credentialsInvalid:false}),now:time,openStore:openReceiver,
 });
 t.after(()=>{for(const s of stores)try{s.close();}catch{}fs.rmSync(dir,{recursive:true,force:true});});
 return{dir,now,advance:n=>time+=n,issuerKey,releaseKey,issuerStore,projectionStore,receiverStore,
   grant,release,prior,projector,pin,safeAccept,accept,published,publicIssuer,publicRelease,readReceiver,openReceiver};
}
test('new on-demand publisher emits issuer-signed revision 88 with recovery_only never opening new business',t=>{
 const f=fixture(t),one=f.projector(),next=one.publish();
 const body=verified(next,f.publicIssuer,'r16.configuration-delivery.v1');
 assert.equal(body.revision,88);assert.equal(body.control.connectRequested,false);
 assert.equal(body.control.status,'ACTIVE');assert.equal(body.publicConfig.release.body.id,f.release.body.id);
 assert.equal(verifyDelivery(next,f.pin,f.prior,f.now()).revision,88);
 assert.deepEqual(one.snapshot(),{grantId:f.grant.body.id,mode:'recovery_only',revision:88,
   lastPublishedRecovery:true,mayStartBusiness:false});
});
test('cloud receiver consumes identical existing R16 signed contract and persists exact control',t=>{
 const f=fixture(t),next=f.projector().publish();
 const reply=f.safeAccept(next);
 assert.deepEqual(reply,{status:'STORED',revision:88,deliveryDigest:digest(next),credentialsInvalid:false});
 assert.equal(f.published.get('/etc/r16-cloud/authority-control.json').connectRequested,false);
 assert.equal(f.published.get('/etc/r16-cloud/public-config.json').release.body.id,f.release.body.id);
 assert.deepEqual(f.readReceiver().accepted,next);
});
test('lost remote ACK retries the exact same signed envelope and does not allocate revision 89',t=>{
 const f=fixture(t),one=f.projector(),next=one.publish();
 assert.deepEqual(one.publish(),next);
 assert.deepEqual(f.projector().publish(),next);
 assert.equal(f.safeAccept(next).revision,88);
 assert.equal(f.safeAccept(next).revision,88);
});
test('cloud receiver refuses forgery and rollback while retaining last accepted config',t=>{
 const f=fixture(t),next=f.projector().publish();
 f.safeAccept(next);
 const wrong=signed({...next.body,revision:89},key());
 assert.throws(()=>f.safeAccept(wrong));
 const prior=f.prior;
 assert.throws(()=>f.safeAccept(prior));
 assert.deepEqual(f.readReceiver().accepted,next);
});
test('cloud delivery cannot be minted from an arbitrary replacement Issuer key',t=>{
 const f=fixture(t);
 denied(()=>createCloudDeliveryProjector({
 deliveryStore:f.projectionStore,issuerStore:f.issuerStore,
 issuerSigningKey:key(),issuerPublicKey:f.publicIssuer,
 releasePublicKey:f.publicRelease,release:f.release,now:f.now}),'ISSUER_KEY_MISMATCH');
});
test('no prior signed delivery cannot reset the cloud revision to one',t=>{
 const f=fixture(t);f.projectionStore.transact(s=>{s.last=null;});
 denied(()=>f.projector(),'CLOUD_PRIOR_REQUIRED');
});
test('recovery-only publisher refuses active mode even if caller requests it',t=>{
 const f=fixture(t);
 denied(()=>createCloudDeliveryProjector({
 deliveryStore:f.projectionStore,issuerStore:f.issuerStore,
 issuerSigningKey:f.issuerKey,issuerPublicKey:f.publicIssuer,
 releasePublicKey:f.publicRelease,release:f.release,mode:'active',now:f.now}),'RECOVERY_ONLY');
});
test('new revocation version changes the public status without expanding scope',t=>{
 const f=fixture(t);
 f.issuerStore.transact(s=>{s.grants[0].version=2;s.grants[0].status='REVOKED';});
 const delivery=f.projector().publish();
 const body=verified(delivery,f.publicIssuer,'r16.configuration-delivery.v1');
 assert.equal(body.control.grantVersion,2);
 assert.equal(body.control.status,'REVOKED');
 assert.equal(body.control.connectRequested,false);
 assert.equal(verifyDelivery(delivery,f.pin,f.prior,f.now()).control.status,'REVOKED');
});
test('private keys and synthetic OS bootstrap never enter the cloud public configuration',t=>{
 const f=fixture(t),body=f.projector().publish().body;
 assert.equal(Object.hasOwn(body.publicConfig,'issuerSigningKey'),false);
 assert.equal(Object.hasOwn(body.publicConfig,'humanPrivateKey'),false);
 assert.equal(body.publicConfig.grant.body.workspace.root,'/home/jenn/AGENTS_OS_Workspace/projects');
});

test('receiver refuses missing independent Release pin and issuer-signed root substitution',t=>{
 const f=fixture(t),next=f.projector().publish();
 assert.throws(()=>verifyDelivery(next,{issuerPublicKey:f.publicIssuer},f.prior,f.now()),/RELEASE_PIN_REQUIRED/);
 const replacement=key(),release=signed({...f.release.body},replacement);
 const swapped=signed({...next.body,publicConfig:{...next.body.publicConfig,
   releasePublicKey:exportPublicKey(replacement),release}},f.issuerKey);
 assert.throws(()=>f.safeAccept(swapped));
 assert.deepEqual(f.readReceiver().accepted,f.prior);
});
test('higher revision cannot restore revoked authority or reduce its version',t=>{
 const f=fixture(t);f.issuerStore.transact(s=>{s.grants[0].version=2;s.grants[0].status='REVOKED';});
 const revoked=f.projector().publish();f.safeAccept(revoked);
 for(const control of [{...revoked.body.control,status:'ACTIVE'},
   {...revoked.body.control,grantVersion:1}]){
  const rollback=signed({...revoked.body,revision:89,control},f.issuerKey);
  assert.throws(()=>f.safeAccept(rollback),/CONTROL_ROLLBACK/);
 }
 assert.deepEqual(f.readReceiver().accepted,revoked);
});
test('publisher refuses cached binding that does not describe the cached envelope',t=>{
 const f=fixture(t),next=f.projector().publish();
 f.projectionStore.transact(s=>{s.last=signed({...next.body,control:{...next.body.control,connectRequested:true}},f.issuerKey);});
 denied(()=>f.projector().publish(),'CLOUD_BINDING_CORRUPT');
});
test('crash between public projection writes leaves durable intent and exact retry repairs it',t=>{
 const f=fixture(t),next=f.projector().publish();let fail=true,reconciles=0;
 const options={
  read:file=>Buffer.from(JSON.stringify(file==='/etc/r16-cloud/issuer-pin.json'?f.pin:f.published.get(file))),
  write:(file,value)=>{if(fail&&file.endsWith('authority-control.json'))throw Error('SYNTHETIC_POWER_LOSS');f.published.set(file,value);},
  ensureCredentials:()=>{},initializeLedgers:()=>{},reconcile:()=>{reconciles++;},
  status:()=>({credentialsInvalid:false}),openStore:f.openReceiver,now:f.now()
 };
 assert.throws(()=>acceptConfiguration(next,options),/SYNTHETIC_POWER_LOSS/);
 assert.deepEqual(f.readReceiver().accepted,next);
 assert.equal(f.readReceiver().projectedDigest,undefined);assert.equal(reconciles,0);
 fail=false;const receipt=acceptConfiguration(next,options);
 assert.equal(receipt.deliveryDigest,digest(next));assert.equal(receipt.revision,88);
 assert.equal(f.readReceiver().projectedDigest,digest(next));assert.equal(reconciles,0);
 assert.deepEqual(f.published.get('/etc/r16-cloud/authority-control.json'),next.body.control);
});
test('failed projection readback cannot report STORED or call lifecycle reconciler',t=>{
 const f=fixture(t),next=f.projector().publish();let reconciles=0;
 assert.throws(()=>acceptConfiguration(next,{
  read:file=>Buffer.from(JSON.stringify(file==='/etc/r16-cloud/issuer-pin.json'?f.pin:{})),
  write:()=>{},ensureCredentials:()=>{},initializeLedgers:()=>{},
  reconcile:()=>{reconciles++;},status:()=>({}),now:f.now(),openStore:f.openReceiver
 }),/CONFIGURATION_READBACK_MISMATCH/);
 assert.equal(reconciles,0);assert.equal(f.readReceiver().projectedDigest,undefined);
});

test('recovery publication never provisions execution ledgers or credentials and cannot start services',t=>{
 const f=fixture(t),next=f.projector().publish();let starts=0;
 const result=f.accept(next);assert.equal(result.deliveryDigest,digest(next));
 const started=reconcileServices(next.body,{
  read:()=>Buffer.from(JSON.stringify({schema:'r16.cloud-cutover.v1',phase:'ACTIVE',grantId:f.grant.body.id,releaseId:f.release.body.id})),
  write:()=>{throw Error('RECOVERY_MUST_NOT_WRITE_START_TOKEN');},run:()=>{starts++;throw Error('RECOVERY_MUST_NOT_START');}
 });
 assert.equal(started,false);assert.equal(starts,0);
});

test('partial stop projection survives Release expiry and exact retry without credential or lifecycle effects',t=>{
 const f=fixture(t),next=f.projector().publish();let fail=true,credentials=0,starts=0;
 const options=()=>({
  read:file=>Buffer.from(JSON.stringify(file==='/etc/r16-cloud/issuer-pin.json'?f.pin:f.published.get(file))),
  write:(file,value)=>{if(fail&&file.endsWith('authority-control.json'))throw Error('SYNTHETIC_POWER_LOSS');f.published.set(file,value);},
  ensureCredentials:()=>{credentials++;},initializeLedgers:()=>{throw Error('RECOVERY_LEDGER_WRITE');},
  reconcile:()=>{starts++;},status:()=>({credentialsInvalid:false}),openStore:f.openReceiver,now:f.now()
 });
 assert.throws(()=>acceptConfiguration(next,options()),/SYNTHETIC_POWER_LOSS/);
 f.advance(86400001);fail=false;
 assert.deepEqual(f.projector().publish(),next);
 const result=acceptConfiguration(next,options());
 assert.equal(result.deliveryDigest,digest(next));assert.equal(result.revision,88);
 assert.equal(credentials,0);assert.equal(starts,0);
 assert.equal(f.readReceiver().projectedDigest,digest(next));
});
test('post-expiry signed revocation advances control but never opens business',t=>{
 const f=fixture(t);f.advance(86400001);
 f.issuerStore.transact(s=>{s.grants[0].version=2;s.grants[0].status='REVOKED';});
 const revoked=f.projector().publish();
 assert.equal(revoked.body.control.status,'REVOKED');
 assert.equal(f.safeAccept(revoked).deliveryDigest,digest(revoked));
 const unsafe=signed({...revoked.body,revision:89,control:{...revoked.body.control,connectRequested:true}},f.issuerKey);
 assert.throws(()=>f.safeAccept(unsafe),/REVOKED_CONNECT_FORBIDDEN/);
});
test('expired active connection request remains rejected even with valid issuer signature',t=>{
 const f=fixture(t),stop=f.projector().publish();f.advance(86400001);
 const active=signed({...stop.body,issuedAt:f.now(),control:{...stop.body.control,connectRequested:true}},f.issuerKey);
 assert.throws(()=>f.safeAccept(active),{code:'RELEASE_EXPIRED'});
 assert.deepEqual(f.readReceiver().accepted,f.prior);
});
test('recovery cannot use an unpinned replacement historical release or bootstrap unknown history',t=>{
 const f=fixture(t),stop=f.projector().publish();f.advance(86400001);
 const replacement=signed({...f.release.body,id:'other-signed-release'},f.releaseKey);
 const swapped=signed({...stop.body,publicConfig:{...stop.body.publicConfig,release:replacement}},f.issuerKey);
 assert.throws(()=>f.safeAccept(swapped),{code:'RECOVERY_RELEASE_NOT_PINNED'});
 assert.throws(()=>verifyDelivery(stop,f.pin,null,f.now()),{code:'RECOVERY_RELEASE_NOT_PINNED'});
 denied(()=>createCloudDeliveryProjector({deliveryStore:f.projectionStore,issuerStore:f.issuerStore,
   issuerSigningKey:f.issuerKey,issuerPublicKey:f.publicIssuer,releasePublicKey:f.publicRelease,release:replacement,now:f.now}),
   'RECOVERY_RELEASE_NOT_PINNED');
});
