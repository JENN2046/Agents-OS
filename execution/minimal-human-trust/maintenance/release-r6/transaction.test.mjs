import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import {generateKeyPairSync,createPublicKey,sign,verify} from 'node:crypto';
import {drive} from './run.mjs';
import {commitCloud,validateDelivery} from './cloud.mjs';
import {commitLocal,writeImmutableFile} from './local.mjs';
import {ProtectedStore} from './legacy/lease-core.mjs';
import {FIXED} from './maintenance-release-base.mjs';
import {canonical,digest,same,json,atomicJson,atomicBytes,sha,command} from './io.mjs';

const DOMAIN='R16-INTEGRATED-ISOLATED-NOT-A-RELEASE\0';
const clone=structuredClone;
function isolatedKeys(){
  const r=generateKeyPairSync('ed25519').privateKey,i=generateKeyPairSync('ed25519').privateKey;
  const pub=k=>createPublicKey(k).export({format:'der',type:'spki'}).toString('base64url');
  const envelope=(body,key)=>({body:clone(body),signature:sign(null,Buffer.from(DOMAIN+canonical(body)),key).toString('base64url')});
  const check=(e,key,schema)=>{assert.equal(e.body.schema,schema);assert(verify(null,Buffer.from(DOMAIN+canonical(e.body)),{key:Buffer.from(key,'base64url'),type:'spki',format:'der'},Buffer.from(e.signature,'base64url')));return clone(e.body);};
  return {r,i,releasePublicKey:pub(r),issuerPublicKey:pub(i),envelope,check};
}
function fixture(){
  const k=isolatedKeys(),at=1000000;
  const source=JSON.parse(fs.readFileSync(new URL('./fixtures/R15_PUBLIC_CONFIG.json',import.meta.url)));
  source.releasePublicKey=k.releasePublicKey;source.issuerPublicKey=k.issuerPublicKey;
  source.release=k.envelope({...source.release.body,issuedAt:at-1000,notAfter:at+9000000},k.r);
  source.grant=k.envelope(source.grant.body,k.i);
  const control={grantId:'r16-projects-daily',grantVersion:1,status:'ACTIVE',connectRequested:true};
  const plan={approvedAt:at,expiresAt:at+300000,rollbackDeadline:at+1800000};
  const delivery=(p,revision,issuedAt=at)=>k.envelope({schema:'r16.configuration-delivery.v1',revision,issuedAt,publicConfig:p,control},k.i);
  const target={...clone(source),versions:{app:FIXED.targetAppVersion,bridge:FIXED.bridgeVersion,native:FIXED.nativeVersion}};
  target.release=k.envelope({...source.release.body,id:FIXED.targetReleaseId,issuedAt:at,versions:target.versions},k.r);
  return {k,at,plan,source,target,old:delivery(source,16,at-1),forward:delivery(target,17),rollback:delivery(source,18,at+1)};
}
function privateTree(t){const dir=fs.mkdtempSync(path.join(os.homedir(),'.r16-integrated-test-'));fs.chmodSync(dir,0o700);t.after(()=>fs.rmSync(dir,{recursive:true}));return dir;}
function persistentJournal(dir){return {read:n=>{try{return json(dir+'/'+n+'.json');}catch(e){if(e.code==='ENOENT')return null;throw e;}},write:(n,v)=>atomicJson(dir+'/'+n+'.json',v)};}
function runtime(journal,{fail=null}={}){
  const f=fixture(),calls=[],state={active:true,cloud:f.old,local:f.old,releaseSigns:0,issuerSigns:0,rollbackSigns:0};
  const pub={delivery:f.forward,proposal:{target:true},reviewedInstallation:{target:true}};
  const adapters={
    baseline:()=>{calls.push('baseline');return {baseline:true};},
    quiesce:()=>{calls.push('quiesce');state.active=false;return {quiet:true};},
    observe:()=>{assert.equal(state.active,false);return {quiet:true};},
    stage:()=>{calls.push('payload');return {installed:true};},
    sign:()=>{let signed=journal.read('private-signature');if(!signed){state.releaseSigns++;state.issuerSigns++;signed=pub;journal.write('private-signature',signed);}return signed;},
    cloudCommit:d=>{calls.push('cloud'+d.body.revision);state.cloud=d;return {revision:d.body.revision};},
    localCommit:(p,rollback)=>{calls.push('local'+p.delivery.body.revision);if(fail==='local'&&!rollback)throw Object.assign(Error(),{code:'INJECTED_LOCAL_FAILURE'});state.local=p.delivery;return {revision:p.delivery.body.revision};},
    activate:()=>{calls.push('activate');state.active=true;if(fail==='activate'&&state.cloud.body.revision===17)throw Object.assign(Error(),{code:'INJECTED_START_FAILURE'});return {status:'OS_ACTIVE',active:true};},
    requiesce:()=>{calls.push('requiesce');state.active=false;return {quiet:true};},
    resume:()=>{calls.push('resume');state.active=true;return {status:'OS_ACTIVE',restored:true};},
    accepted:()=>state.cloud,
    signRollback:()=>{let x=journal.read('private-rollback');if(!x){state.rollbackSigns++;x={delivery:f.rollback};journal.write('private-rollback',x);}return x;},
    verify:d=>{assert(state.active);assert(same(state.local,d));assert(same(state.cloud,d));return {revision:d.body.revision,businessAcceptance:false};},
  };
  return {f,state,calls,adapters};
}
test('full isolated transaction commits both hosts and returns historical receipt without effects',async t=>{
  const j=persistentJournal(privateTree(t)),r=runtime(j);const result=await drive({journal:j,adapters:r.adapters,now:()=>r.f.at});
  assert.equal(result.status,'MAINTENANCE_COMMITTED');assert.equal(result.configurationRevision,17);assert.equal(result.businessAcceptance,false);
  assert.equal(r.state.releaseSigns,1);assert.equal(r.state.issuerSigns,1);const n=r.calls.length;
  const old=await drive({journal:j,adapters:r.adapters});assert(old.historicalReadOnly);assert.equal(r.calls.length,n);
});
for(const failed of ['local','activate'])test('failure '+failed+' quiesces before higher revision rollback and preserves journal',async t=>{
  const j=persistentJournal(privateTree(t)),r=runtime(j,{fail:failed});const result=await drive({journal:j,adapters:r.adapters,now:()=>r.f.at+10});
  assert.equal(result.status,'ROLLED_BACK_TO_R15_WITH_NEWER_REVISION');assert.equal(result.configurationRevision,18);assert.equal(r.state.rollbackSigns,1);
  assert(r.calls.indexOf('requiesce')<r.calls.indexOf('cloud18'));assert(r.calls.indexOf('cloud18')<r.calls.indexOf('local18'));
});
for(const point of ['intent','effect','done'])for(const name of ['baseline','quiesce','payload','signed','cloud-commit','local-commit','activate','readback'])test('crash '+point+':'+name+' resumes exact transaction without duplicate signing',async t=>{
  const j=persistentJournal(privateTree(t)),r=runtime(j);let once=false;
  await assert.rejects(drive({journal:j,adapters:r.adapters,now:()=>r.f.at,fault:p=>{if(p===point+':'+name&&!once){once=true;throw Object.assign(Error('POWER_LOSS'),{simulatedCrash:true});}}}));
  const result=await drive({journal:j,adapters:r.adapters,now:()=>r.f.at+1});assert.equal(result.status,'MAINTENANCE_COMMITTED');assert.equal(r.state.releaseSigns,1);assert.equal(r.state.issuerSigns,1);
});
test('crash in persisted rollback never re-enters forward commit',async t=>{
  const j=persistentJournal(privateTree(t)),r=runtime(j,{fail:'local'});let once=false;
  await assert.rejects(drive({journal:j,adapters:r.adapters,now:()=>r.f.at,fault:p=>{if(p==='effect:rollback-signed'&&!once){once=true;throw Object.assign(Error('POWER_LOSS'),{simulatedCrash:true});}}}));
  const count=r.calls.filter(c=>c==='local17').length;
  const result=await drive({journal:j,adapters:r.adapters,now:()=>r.f.at+1});assert.equal(result.status,'ROLLED_BACK_TO_R15_WITH_NEWER_REVISION');assert.equal(r.calls.filter(c=>c==='local17').length,count);assert.equal(r.state.rollbackSigns,1);
});
for(const point of ['intent','effect','done'])for(const name of ['rollback-quiesce','rollback-signed','rollback-cloud','rollback-local','rollback-activate','rollback-readback'])test('rollback crash '+point+':'+name+' resumes without restarting forward transaction',async t=>{
  const j=persistentJournal(privateTree(t)),r=runtime(j,{fail:'local'});let once=false;
  await assert.rejects(drive({journal:j,adapters:r.adapters,now:()=>r.f.at,fault:p=>{if(p===point+':'+name&&!once){once=true;throw Object.assign(Error('POWER_LOSS'),{simulatedCrash:true});}}}));
  const forwardWrites=r.calls.filter(c=>c==='local17').length;
  const result=await drive({journal:j,adapters:r.adapters,now:()=>r.f.at+1});assert.equal(result.status,'ROLLED_BACK_TO_R15_WITH_NEWER_REVISION');assert.equal(r.calls.filter(c=>c==='local17').length,forwardWrites);assert.equal(r.state.rollbackSigns,1);
});
test('unresolved signer intent aborts before configuration and does not create rollback signature',async t=>{
  const j=persistentJournal(privateTree(t)),r=runtime(j);r.adapters.sign=()=>{throw Object.assign(Error(),{code:'SIGNER_EFFECT_UNKNOWN'});};
  const result=await drive({journal:j,adapters:r.adapters,now:()=>r.f.at});assert.equal(result.status,'ABORTED_BEFORE_CONFIGURATION_CHANGE');assert.equal(r.state.rollbackSigns,0);assert.equal(r.state.cloud.body.revision,16);assert(r.state.active);
});
test('failed re-quiescence leaves recovery pending and never mutates config under live writers',async t=>{
  const j=persistentJournal(privateTree(t)),r=runtime(j,{fail:'activate'});r.adapters.requiesce=()=>{throw Object.assign(Error(),{code:'GRACEFUL_STOP_INCOMPLETE'});};
  const result=await drive({journal:j,adapters:r.adapters,now:()=>r.f.at});assert.equal(result.status,'RECOVERY_REQUIRED_SERVICES_MAY_REMAIN_FENCED');assert.equal(r.state.rollbackSigns,0);assert(!r.calls.includes('cloud18'));
});
test('baseline refusal does not pretend an OS restoration occurred',async t=>{
  const j=persistentJournal(privateTree(t)),r=runtime(j);r.adapters.baseline=()=>{throw Object.assign(Error(),{code:'SOURCE_DRIFT'});};
  const result=await drive({journal:j,adapters:r.adapters,now:()=>r.f.at});assert.equal(result.status,'ABORTED_BEFORE_SERVICE_CHANGES');assert(!r.calls.includes('resume'));
});
test('partial abort restoration is reported as recovery required',async t=>{
  const j=persistentJournal(privateTree(t)),r=runtime(j);r.adapters.sign=()=>{throw Object.assign(Error(),{code:'SIGNER_EFFECT_UNKNOWN'});};r.adapters.resume=()=>({status:'RESTORE_PARTIAL'});
  const result=await drive({journal:j,adapters:r.adapters,now:()=>r.f.at});assert.equal(result.status,'RECOVERY_REQUIRED_SERVICES_MAY_REMAIN_FENCED');
});
test('known configuration prefix is completed without replaying an external effect',t=>{
  const dir=privateTree(t),file=dir+'/config.json',raw=Buffer.from('{"known":"configuration"}\n');
  fs.writeFileSync(file+'.next-'+sha(raw),raw.subarray(0,9),{mode:0o600});atomicBytes(file,raw);assert(fs.readFileSync(file).equals(raw));
});
test('rollback uses its own exact content temporary file and refuses foreign prefix',t=>{
  const dir=privateTree(t),file=dir+'/config.json',forward=Buffer.from('{"revision":17}'),rollback=Buffer.from('{"revision":18}');
  fs.writeFileSync(file+'.next-'+sha(forward),forward.subarray(0,7),{mode:0o600});atomicBytes(file,rollback);assert(fs.readFileSync(file).equals(rollback));
  const bad=Buffer.from('not-the-prefix');fs.writeFileSync(file+'.next-'+sha(forward),bad,{mode:0o600});assert.throws(()=>atomicBytes(file,forward));assert(fs.readFileSync(file).equals(rollback));
});
test('physical executable dependency resumes partial staging with exact executable mode',t=>{
  const dir=privateTree(t),file=dir+'/bin/tool',raw=Buffer.from('#!/bin/sh\nexit 0\n');fs.mkdirSync(dir+'/bin',{mode:0o755});
  fs.writeFileSync(file+'.next-'+sha(raw),raw.subarray(0,4),{mode:0o600});writeImmutableFile(file,raw,0o755);assert(fs.readFileSync(file).equals(raw));assert.equal(fs.statSync(file).mode&0o7777,0o755);
  writeImmutableFile(file,raw,0o755);assert.throws(()=>writeImmutableFile(file,Buffer.from('foreign'),0o755));
  const mask=process.umask(0o077);try{writeImmutableFile(dir+'/new-bin/sub/tool',raw,0o755);}finally{process.umask(mask);}
  assert.equal(fs.statSync(dir+'/new-bin').mode&0o7777,0o755);assert.equal(fs.statSync(dir+'/new-bin/sub').mode&0o7777,0o755);
});
test('fixed command propagates only a bounded structured refusal code',()=>{
  assert.throws(()=>command('/usr/bin/python3',['-I','-B','-c','import json,sys; print(json.dumps({"code":"GRACEFUL_STOP_INCOMPLETE"}));sys.exit(78)']),e=>e.code==='GRACEFUL_STOP_INCOMPLETE');
  assert.throws(()=>command('/usr/bin/python3',['-I','-B','-c','import json,sys; print(json.dumps({"code":"unsafe raw detail"}));sys.exit(78)']),e=>e.code==='FIXED_COMMAND_FAILED');
});
for(const checkpoint of ['app-selector','accepted','public','control','cutover','start-attempt'])test('cloud real ProtectedStore interrupted at '+checkpoint+' resumes exact signed revision',t=>{
  const f=fixture(),dir=privateTree(t),storeDir=dir+'/store';const init=new ProtectedStore({directory:storeDir,create:true,initial:{kind:'r16.cloud-publication.v1',accepted:f.old},now:()=>f.at});init.close();
  const sourceAppConfig={schema:'r16.app-host.v1',publicConfiguration:'/etc/r16-cloud/public-config.json',codeManifest:FIXED.sourceDirectory+'/app-manifest.json'};
  const paths={app:dir+'/app.json',public:dir+'/public.json',control:dir+'/control.json',cutover:dir+'/cutover.json',startAttempt:dir+'/start.json'};atomicJson(paths.app,sourceAppConfig);atomicJson(paths.public,f.source);atomicJson(paths.control,f.old.body.control);atomicJson(paths.cutover,{schema:'r16.cloud-cutover.v1',phase:'ACTIVE',grantId:'r16-projects-daily',releaseId:FIXED.sourceReleaseId});
  atomicJson(paths.startAttempt,{schema:'r16.cloud-start-attempt.v1',grantId:'r16-projects-daily',revision:16});
  const opts={sourceAppConfig,plan:f.plan,sourcePublicConfig:f.source,openStore:()=>new ProtectedStore({directory:storeDir,create:false,now:()=>f.at}),read:k=>json(paths[k]),write:(k,v)=>atomicJson(paths[k],v),quiescent:()=>{},ledgerSnapshot:()=>({business:'UNCHANGED',UNKNOWN:2}),now:f.at,domainVerify:f.k.check};
  assert.throws(()=>commitCloud(f.forward,{...opts,checkpoint:p=>{if(p===checkpoint)throw Error('POWER_LOSS');}}));
  const result=commitCloud(f.forward,opts);assert.equal(result.revision,17);assert(same(json(paths.public),f.target));assert.equal(json(paths.app).codeManifest,FIXED.targetDirectory+'/app-manifest.json');
  assert.throws(()=>commitCloud(f.old,opts));const rb=commitCloud(f.rollback,{...opts,now:f.at+1});assert.equal(rb.revision,18);assert(same(json(paths.public),f.source));assert(same(json(paths.app),sourceAppConfig));
});
test('cloud refuses same revision conflict, expired forward, foreign Grant and missing quiescence',()=>{
  const f=fixture(),opts={plan:f.plan,sourcePublicConfig:f.source,previous:f.forward,now:f.at,domainVerify:f.k.check};
  const bad=f.k.envelope({...f.forward.body,issuedAt:f.at-1},f.k.i);assert.throws(()=>validateDelivery(bad,opts));
  assert.throws(()=>validateDelivery(f.forward,{...opts,now:f.plan.expiresAt}));
  const foreign=f.k.envelope({...f.forward.body,publicConfig:{...f.target,grant:{wrong:true}}},f.k.i);assert.throws(()=>validateDelivery(foreign,opts));
  assert.throws(()=>commitCloud(f.forward,{quiescent:()=>{throw Error('LIVE_WRITER');}}));
});
for(const checkpoint of ['reviewed','native','proposal','owner-delivery'])test('local selector/cache interruption '+checkpoint+' preserves Owner authority and Issuer',t=>{
  const f=fixture(),dir=privateTree(t),storeDir=dir+'/configuration';
  const historical={scopeHash:'historical',activeProposal:{release:'OLD_HUMAN_APPROVAL'}};
  const config={kind:'r16.owner.configuration.v1',trust:historical,connected:true,connectionNonce:7,delivery:{hash:'old',revision:16,envelope:f.old},blockedProjects:[],replacement:null};
  const init=new ProtectedStore({directory:storeDir,create:true,initial:config,now:()=>f.at});init.close();
  const snapshots={proposal:{original:true},reviewed:{original:true},native:{schema:'r16.native-host.v1',codeManifest:FIXED.sourceDirectory+'/native-manifest.json'}};
  const paths=Object.fromEntries(Object.keys(snapshots).map(k=>[k,dir+'/'+k+'.json']));for(const [k,v]of Object.entries(snapshots))atomicJson(paths[k],v);
  const invariant=clone(config);delete invariant.delivery;
  const before={issuerDataHash:'never-write-issuer',configurationInvariantHash:digest(invariant),originalUnknown:{a:'UNKNOWN',b:'UNKNOWN'},projectBusinessHashes:{a:'immutable',b:'immutable'}};
  const context={before,snapshots,inputs:{sourceDelivery:f.old,sourcePublicConfig:f.source}};
  const publication={delivery:f.forward,proposal:{target:true},reviewedInstallation:{target:true}};
  const opts={context,openStore:()=>new ProtectedStore({directory:storeDir,create:false,now:()=>f.at}),read:k=>json(paths[k]),write:(k,v)=>atomicJson(paths[k],v),quiescent:()=>{},capture:()=>clone(before)};
  assert.throws(()=>commitLocal(publication,{...opts,checkpoint:p=>{if(p===checkpoint)throw Error('POWER_LOSS');}}));
  commitLocal(publication,opts);let store=opts.openStore(),state=store.snapshot();store.close();assert(same(state.trust,historical));assert.equal(state.connectionNonce,7);
  assert.equal(state.delivery.hash,digest({publicConfig:f.target,control:f.forward.body.control,connectionNonce:7}));assert.equal(state.delivery.revision,17);
  commitLocal({...publication,delivery:f.rollback},{...opts,rollback:true});store=opts.openStore();state=store.snapshot();store.close();assert.equal(state.delivery.revision,18);assert(same(state.trust,historical));assert(same(json(paths.native),snapshots.native));
});
