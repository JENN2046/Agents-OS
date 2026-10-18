import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import {pathToFileURL} from 'node:url';
import {generateKeyPairSync,createHash} from 'node:crypto';
import {execFileSync} from 'node:child_process';
import {signed,exportPublicKey} from '../../src/lease-core.mjs';
import * as P from './publication.mjs';
export const clone=x=>JSON.parse(JSON.stringify(x));
const sha=b=>createHash('sha256').update(b).digest('hex');
export function fixture(t){
 const root=fs.mkdtempSync(path.join(os.tmpdir(),'source19-publication-'));fs.chmodSync(root,0o700);t.after(()=>fs.rmSync(root,{recursive:true,force:true}));
 const now=Date.now(),keys=Object.fromEntries(['release','issuer','app','bridge','native'].map(r=>[r,generateKeyPairSync('ed25519').privateKey]));
 const peers=Object.fromEntries(['app','bridge','native'].map(r=>[r,{id:r+'-peer',publicKey:exportPublicKey(keys[r])}]));
 const sourceBytes=Object.fromEntries([...P.CHANGED,'src/core.mjs','app/runner.mjs','bridge/runner.mjs'].map(n=>[n,Buffer.from('fixture old '+n)]));
 const targetBytes=Object.fromEntries(Object.entries(sourceBytes).map(([n,b])=>[n,P.CHANGED.includes(n)?Buffer.from('fixture new '+n):b]));
 const manifest=(role,entry,names,bytes)=>({schema:'r16.runtime-code.v1',role,entry,files:Object.fromEntries(names.map(n=>[n,sha(bytes[n])]))});
 const sourceManifests={app:manifest('app','app/runner.mjs',['app/runner.mjs'],sourceBytes),bridge:manifest('bridge','bridge/runner.mjs',['bridge/runner.mjs'],sourceBytes),native:manifest('native','host/native-runner.mjs',[...P.CHANGED,'src/core.mjs'],sourceBytes)};
 const targetManifests={...clone(sourceManifests),native:manifest('native','host/native-runner.mjs',[...P.CHANGED,'src/core.mjs'],targetBytes)};
 const versions=Object.fromEntries(Object.entries(sourceManifests).map(([r,m])=>[r,P.digest(m)]));
 const grant=signed({schema:'r16.workspace.v1',id:'r16-projects-daily',version:1,createdAt:now-1000,workspace:{id:'ws',root:'/fixture',dev:1,ino:2},actions:['find_symbol'],channel:'main',peers},keys.issuer);
 const release=signed({schema:'r16.release.v1',id:'r16-daily-20261015-r15-app-recovery-r6',issuedAt:now-1000,notAfter:now+3600000,formats:['r16.workspace.v1'],versions,actions:['find_symbol'],permissionVersion:1},keys.release);
 const pub={schema:'r16.runtime-configuration.v1',releasePublicKey:exportPublicKey(keys.release),issuerPublicKey:exportPublicKey(keys.issuer),release,grant,peers,versions,channel:'main'};
 const delivery=signed({schema:'r16.configuration-delivery.v1',revision:19,issuedAt:now-500,publicConfig:pub,control:{grantId:'r16-projects-daily',grantVersion:1,status:'ACTIVE',connectRequested:true}},keys.issuer);
 const revisionInventory={schema:'r16.fresh-revision-inventory.v1',acceptedRevision:19,acceptedDeliveryHash:'b8645f6fe206e84dd07c2c6c166bfe4016d1deefca28bf9545dcfa1560f013e9',observedAt:now,signedMaximum:19,reservedMaximum:20,complete:true};
 const requested={forward:21,recovery:22,legacy21_22Disposition:'CANCELLED_UNALLOCATED_REPLAN'},revisionPlan=P.explicitRevisionPlan(revisionInventory,requested,now);
 const inventory=Object.fromEntries(Object.entries(targetBytes).map(([n,b])=>[n,{sha256:sha(b),bytes:b.length,mode:420,origin:P.CHANGED.includes(n)?'EXACT_NATIVE_LIFECYCLE_BACKPORT':'EXACT_SOURCE19_BASE'}]));
 const instance={pid:123,startTicks:'456',bootId:'fixture-boot',cgroup:'/fixture/native'};
 const historicalOperations=[['p2vox','c434da49-055a-43dc-a3e3-695cce137909',30],['pmog2','d0364f8b-3a68-4ca2-a396-7953b29cee4c',38]].map(([projectId,id,generation])=>signed({schema:'r16.operation.v1',id,grantId:'r16-projects-daily',projectId,generation,leaseHash:'8'.repeat(64),channel:'main',action:'find_symbol',payloadHash:'9'.repeat(64)},keys.app));
 const ledgerRegistry={schema:'r16.native-ledgers.v1',grants:[{grantId:'r16-projects-daily',grantHash:P.digest(grant),status:'READY',directory:'/var/lib/r16-native/grants/r16-projects-daily/dispatcher',dev:1,ino:2}]};
 const ledgerRegistryRaw=Buffer.from(P.canonical(ledgerRegistry)+'\n');
 const checkpoint={schema:'r16.source19-native-checkpoint.v1',completeRegisteredFileSet:true,noForeignWriters:true,noTemporaryFiles:true,newUnknown:[],inflight:[],originalSignaturesAndLeasesVerified:true,originalLeaseBindingsHash:'b'.repeat(64),registeredRootsHash:'c'.repeat(64),controlUnknownRows:[],controlUnknownHash:P.digest([]),controlUnknownCount:0,originalUnknown:Object.fromEntries(historicalOperations.map(op=>[op.body.projectId,{id:op.body.id,generation:op.body.generation,hash:P.digest(op)}])),nativeLedgerRegistration:{directory:ledgerRegistry.grants[0].directory,dev:1,ino:2,registryHash:sha(ledgerRegistryRaw)}};
 const plan={schema:'r16.source19-native-transition.plan.v1',sourcePublicConfigHash:P.digest(pub),sourceDeliveryHash:P.digest(delivery),grantHash:P.digest(grant),sourceNativeVersion:pub.versions.native,
  codeFreezeHash:'a'.repeat(64),originalBaselineHash:'b'.repeat(64),nativeTargetHash:P.digest(instance),stopEpoch:'11111111-2222-4333-8444-555555555555',nonce:'a'.repeat(32),
  approvedAt:now,expiresAt:now+300000,recoveryDeadline:now+1800000,revisionPlanHash:P.digest(revisionPlan),targetReleaseId:P.TARGET_RELEASE,targetNativeVersion:P.digest(targetManifests.native),targetInventoryHash:P.digest(inventory),
  approvedControlUnknownHash:P.digest([]),approvedControlUnknownCount:0,recoveryPolicy:'KEEP_CRASHED_NATIVE_STOPPED_NO_AUTOMATIC_BUSINESS_REOPEN',scope:'SAME_PLAN_SOURCE19_NATIVE_MAINTENANCE_NOT_DRAINED',allowNativeNonGracefulOnce:true,acceptUnprovenInflight:true,acceptPossibleUpstreamContinuation:true};
 const units={'r16-owner.service':['jenn-System-Product-Name','r16-owner.service'],'r16-native.service':['jenn-System-Product-Name','r16-native.service'],'r16-app.service':['VM-0-12-ubuntu','r16-app.service'],'r16-bridge.service':['VM-0-12-ubuntu','r16-bridge.service']};
 const proof={schema:'r16.source19-native-transition.stopped-fenced.v1',status:'STOPPED_FENCED_NOT_DRAINED',environment:'ISOLATED_TEST',planHash:P.digest(plan),sourcePublicConfigHash:plan.sourcePublicConfigHash,sourceDeliveryHash:plan.sourceDeliveryHash,grantHash:P.digest(grant),codeFreezeHash:plan.codeFreezeHash,originalBaselineHash:plan.originalBaselineHash,checkpointHash:P.digest(checkpoint),controlUnknownHash:P.digest([]),controlUnknownCount:0,nativeTargetHash:plan.nativeTargetHash,stopEpoch:plan.stopEpoch,issuedAt:now,expiresAt:now+30000,originalUnknownPreserved:true,noForeignWriters:true,relayStopped:true,globalExecution:'UNPROVEN',forceTerminationUsed:true,roleStopReceipt:false,businessAcceptance:false,actors:Object.fromEntries(Object.entries(units).map(([r,[host,unit]])=>[r,{host,unit,mainPid:0,controlPid:0,cgroupEmpty:true,ownedPersistentFence:true,pendingJob:false}]))};
 const input={sourcePublicConfig:pub,sourceDelivery:delivery,sourceManifests,targetManifests,inventory,revisionInventory,revisionPlan:requested,plan,stoppedProof:proof,now};
 const a=P.buildIsolatedPublicationArtifacts(input,root);
 const sign=(artifacts,rollback=false)=>{const r=rollback?artifacts.sourcePublicConfig.release:signed(artifacts.releaseBody,keys.release);return {release:r,delivery:signed(P.deliveryBody(artifacts,r,rollback),keys.issuer)};};
 return {root,now,keys,input,a,proof,sign,targetBytes,history:{checkpoint,sourceNativeInstance:instance,ledgerRegistry,ledgerRegistryRaw:ledgerRegistryRaw.toString('base64'),historicalOperations}};
}
if(process.argv[1]&&pathToFileURL(process.argv[1]).href===import.meta.url){
 test('real public signed19 validates; same-public higher revision and wrong public fail',()=>{
  const pub=JSON.parse(fs.readFileSync(new URL('../../test/fixtures/SOURCE19_PUBLIC_CONFIG.json',import.meta.url))),d=JSON.parse(fs.readFileSync(new URL('../../test/fixtures/SOURCE19_DELIVERY_ENVELOPE.json',import.meta.url)));
  assert.equal(P.inspectSource19(pub,d).revision,19);const drift=clone(d);drift.body.revision=21;assert.throws(()=>P.inspectSource19(pub,drift));const p=clone(pub);p.channel='wrong';assert.throws(()=>P.inspectSource19(p,d));
 });
 test('explicit fresh source19 plan skips20 and cancels old unsigned21/22 planning',t=>{const f=fixture(t);assert.equal(f.a.revisionPlan.forward,21);assert.equal(f.a.revisionPlan.recovery,22);assert.notEqual(f.a.releaseBody.id,'r16-daily-20261012-r17');assert.equal(f.a.releaseBody.versions.app,f.input.sourcePublicConfig.versions.app);});
 test('missing/stale/incomplete inventory or default+1/old planning reuse rejects',t=>{const f=fixture(t);for(const mutate of [i=>i.complete=false,i=>i.observedAt=f.now-60001,i=>i.acceptedRevision=18]){const i=clone(f.input.revisionInventory);mutate(i);assert.throws(()=>P.explicitRevisionPlan(i,f.input.revisionPlan,f.now));}for(const p of [{forward:20,recovery:21},{forward:21,recovery:22},{forward:21,recovery:21}])assert.throws(()=>P.explicitRevisionPlan(f.input.revisionInventory,p,f.now));});
 test('actual five-file scope enforced; nonNative or extra Native changes fail',t=>{const f=fixture(t);for(const change of [i=>i.targetManifests.app.files['app/runner.mjs']='0'.repeat(64),i=>i.targetManifests.native.files['src/core.mjs']='0'.repeat(64),i=>delete i.targetManifests.native.files[P.CHANGED[0]]]){const i=clone(f.input);change(i);assert.throws(()=>P.buildIsolatedPublicationArtifacts(i,f.root));}});
 test('fixture cannot enter production source or fixed signer',t=>{const f=fixture(t);assert.throws(()=>P.buildPublicationArtifacts(f.input));assert.throws(()=>P.signFixedPublication(f.a,f.proof),/FIXED_SIGNER_CONTEXT_REQUIRED/);});
 test('typed NOT_DRAINED proof binds environment, epoch, checkpoint, identities and expiry',t=>{const f=fixture(t);assert.equal(P.assertStoppedProof(f.proof,f.a,f.now),P.digest(f.proof));for(const change of [p=>p.environment='PRODUCTION',p=>p.stopEpoch='different',p=>p.checkpointHash='0'.repeat(64),p=>p.actors['r16-native.service'].mainPid=123,p=>p.actors['r16-native.service'].ownedPersistentFence=false,p=>p.relayStopped=false,p=>p.globalExecution='DRAINED',p=>p.expiresAt=f.now]){const p=clone(f.proof);change(p);assert.throws(()=>P.assertStoppedProof(p,f.a,f.now));}});
 test('actual Ed25519 release and delivery acceptance rejects wrong signer, version and revision',t=>{const f=fixture(t),p=f.sign(f.a);assert.equal(P.acceptSignedPublication(f.a,p,false,f.now).delivery.body.revision,21);for(const change of [x=>x.release.body.versions.native='0'.repeat(64),x=>x.delivery.body.revision=20,x=>x.delivery.signature='A'.repeat(86)]){const v=clone(p);change(v);assert.throws(()=>P.acceptSignedPublication(f.a,v,false,f.now));}assert.equal(P.acceptSignedPublication(f.a,f.sign(f.a,true),true,f.now).delivery.body.revision,22);});
 test('expired window and artifact reconstruction cannot acquire signing authority',t=>{const f=fixture(t);assert.throws(()=>P.acceptSignedPublication(f.a,f.sign(f.a),false,f.a.plan.expiresAt));assert.throws(()=>P.assertStoppedProof(f.proof,clone(f.a),f.now));const i=clone(f.input);i.plan.artifactsHash='0'.repeat(64);assert.throws(()=>P.buildIsolatedPublicationArtifacts(i,f.root),/PLAN_HASH_CYCLE_REFUSED/);});
 test('actual Python stop Driver output feeds JS artifact with exact planHash, B is not in plan',t=>{
  const f=fixture(t),script=`import importlib.util,json,sys\nfrom pathlib import Path\nspec=importlib.util.spec_from_file_location('cross_stop',sys.argv[1]);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)\nx=json.load(sys.stdin);s=m.s\n# Isolated synthetic public roots only; production constants/source files unchanged.\ns.PUBLIC=x['plan']['sourcePublicConfigHash'];s.DELIVERY=x['plan']['sourceDeliveryHash'];s.GRANT=x['plan']['grantHash'];s.SOURCE_NATIVE=x['plan']['sourceNativeVersion']\nb=m.Backend();j=m.Journal();p=x['plan'];p['originalBaselineHash']=s.digest(b.baseline);p['nativeTargetHash']=s.digest(b.baseline[s.NATIVE])\nproof=s.Driver(b,j,lambda:x['now']).run(p)\nprint(json.dumps({'plan':p,'proof':proof,'signalCount':b.kills}))`;
  const raw=execFileSync('/usr/bin/python3',['-I','-B','-c',script,new URL('./test_stop_transition.py',import.meta.url).pathname],{input:JSON.stringify({plan:f.input.plan,now:f.now}),encoding:'utf8',timeout:10000});
  const actual=JSON.parse(raw),input={...f.input,plan:actual.plan,stoppedProof:actual.proof};const a=P.buildIsolatedPublicationArtifacts(input,f.root);
  assert.equal(a.planHash,actual.proof.planHash);assert.equal(a.checkpointHash,actual.proof.checkpointHash);assert.equal(actual.signalCount,1);assert.equal(actual.proof.controlUnknownHash,input.plan.approvedControlUnknownHash);assert.equal(actual.proof.controlUnknownCount,input.plan.approvedControlUnknownCount);assert.equal(Object.hasOwn(a.plan,'checkpointHash'),false);assert.equal(Object.hasOwn(a.plan,'artifactsHash'),false);
 });
 test('post-stop artifact keeps accepted planning inventory and exact pre-stop plan timestamp',t=>{
  const f=fixture(t),input=clone(f.input);input.now=f.now+120000;input.stoppedProof.issuedAt=input.now;input.stoppedProof.expiresAt=input.now+30000;
  const a=P.buildIsolatedPublicationArtifacts(input,f.root);assert.equal(a.planHash,f.a.planHash);assert.equal(a.revisionPlan.inventoryHash,f.a.revisionPlan.inventoryHash);
 });

 test('control uncertainty is plan-bound, exact count/hash and proof fields cannot drift',t=>{
  const f=fixture(t);for(const mutate of [i=>delete i.plan.approvedControlUnknownHash,i=>i.plan.approvedControlUnknownCount=-1,i=>i.plan.approvedControlUnknownCount=true,i=>i.stoppedProof.controlUnknownHash='f'.repeat(64),i=>i.stoppedProof.controlUnknownCount=1]){const i=clone(f.input);mutate(i);assert.throws(()=>P.buildIsolatedPublicationArtifacts(i,f.root));}
 });
 test('fixed signer rechecks each actual credential read after consumed-marker fsync and between keys',async t=>{
  // Actual signing/mountedKey control flow, synthetic in-memory key material
  // and explicit fake root/cgroup metadata. No production key or root IO.
  const f=fixture(t),source=fs.readFileSync(new URL('./publication.mjs',import.meta.url),'utf8');
  for(const phase of ['marker-fsync','between-credentials']){
   const slot='__signerWindow_'+phase.replaceAll('-','')+Math.random().toString(36).slice(2),state={now:f.now,reads:[],fsyncs:0};
   globalThis[slot]=state;t.after(()=>delete globalThis[slot]);
   const intent={planHash:f.a.planHash,artifactsHash:P.digest(f.a),kind:'forward',proofHash:P.digest(f.proof)};
   const keys=Object.fromEntries(['release','issuer'].map(n=>[n+'-signing-key',f.keys[n].export({format:'der',type:'pkcs8'})]));
   state.read=p=>{if(p.endsWith('signing-forward-intent.json'))return Buffer.from(P.canonical(intent));const name=p.split('/').at(-1);assert.ok(Object.hasOwn(keys,name));state.reads.push(name);if(phase==='between-credentials')state.now=f.a.plan.expiresAt;return Buffer.from(keys[name]);};
   state.fs={...fs,readFileSync:(p,...args)=>p==='/proc/self/mountinfo'?'1 0 0:1 / /run/credentials/'+P.UNIT+' ro - tmpfs tmpfs ro':fs.readFileSync(p,...args),openSync:()=>91,closeSync:()=>{},writeFileSync:()=>{},fsyncSync:()=>{state.fsyncs++;if(phase==='marker-fsync'&&state.fsyncs===2)state.now=f.a.plan.expiresAt;},lstatSync:p=>p.startsWith('/run/credentials/')?{mode:0o100400,dev:1}:fs.lstatSync(p)};
   const data=x=>'data:text/javascript;base64,'+Buffer.from(x).toString('base64');
   let text=source.replace("'node:fs'",JSON.stringify(data('export default globalThis['+JSON.stringify(slot)+'].fs;')));
   const start=text.indexOf('function protectedBytes('),end=text.indexOf('export function assertFixedSigningContext',start);
   text=text.slice(0,start)+'function protectedBytes(p){return globalThis['+JSON.stringify(slot)+'].read(p); }\n'+text.slice(end);
   const a=text.indexOf('export function assertFixedSigningContext('),b=text.indexOf("import {createHash}",a);
   text=text.slice(0,a)+'export function assertFixedSigningContext(a,p,rollback=false){need(globalThis['+JSON.stringify(slot)+'].now<(rollback?a.plan.recoveryDeadline:a.plan.expiresAt),"FIXED_SIGNER_WINDOW_EXPIRED");}\n'+text.slice(b);
   text=text.replace(/from '([^']+)'/g,(match,rel)=>'from '+JSON.stringify(new URL(rel,import.meta.url).href));
   const m=await import(data(text));const artifact=m.buildIsolatedPublicationArtifacts(f.input,f.root);
   assert.throws(()=>m.signFixedPublication(artifact,f.proof),/FIXED_SIGNER_WINDOW_EXPIRED/);
   assert.deepEqual(state.reads,phase==='marker-fsync'?[]:['release-signing-key']);
  }
 });
}
