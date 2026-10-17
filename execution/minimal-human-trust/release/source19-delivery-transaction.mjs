// Source-only protocol for a FUTURE root-admitted, single-writer R17 entry.
// No default key loader, service operation or admission. Selector IO requires
// an exact admitted descriptor and the existing configuration-store lock.
// Installing this library does not install/admit that entry: READY_UNINSTALLED.
import fs from 'node:fs';
import path from 'node:path';
import {createHash} from 'node:crypto';
import {protectedRuntimeFile,runtimeVersion} from '../authority/runtime-manifest.mjs';
import {ProtectedStore,canonical,digest,verified,verifyRelease,ROLES,ACTIONS} from '../src/lease-core.mjs';
import {SOURCE19_BASELINE,HISTORICAL_R15_BASELINE,inspectSourcePublicConfiguration} from '../authority/source-baseline.mjs';
import {acceptConfiguration} from '../deployment/cloud-configuration-receiver.mjs';

const need=(v,c='SOURCE19_DELIVERY_REJECTED')=>{if(!v)throw Object.assign(Error(c),{code:c});};
const same=(a,b)=>canonical(a)===canonical(b);
const HASH=/^[a-f0-9]{64}$/;
const SELECTOR_FILES=Object.freeze({app:'/etc/r16-cloud/app-host.json',bridge:'/etc/r16-cloud/bridge-host.json',native:'/etc/r16/native-host.json'});
const keys=(o,n)=>need(o&&same(Object.keys(o).sort(),n.slice().sort()),'DELIVERY_FIELDS');
const copy=x=>JSON.parse(canonical(x));
export const DELIVERY_READINESS='READY_UNINSTALLED';
export const DELIVERY_REVISIONS=Object.freeze({source:19,forward:21,recovery:22});
export const deliveryTransactionInitialState=()=>({kind:'mht.source19-delivery-transaction.v1',binding:null,steps:{},recoveryRequired:false,failures:[],terminal:null});

export function inspectDeliveryPlan({plan,sourceDelivery,targetRelease,now=Date.now()}){
 keys(plan,['schema','nonce','mode','sourceRevision','sourceDeliveryHash','sourcePublicHash','forwardRevision','recoveryRevision','targetReleaseHash','targetVersions','grantHash','stopEpoch','handoffHash','preservedStateHash','approvedAt','expiresAt','recoveryDeadline','connectRequested','allowForwardRecovery22','selectorBindingsHash']);
 need(plan.schema==='mht.source19-fixed-delivery-plan.v1'&&plan.mode==='recovery_only'&&plan.connectRequested===false&&plan.allowForwardRecovery22===true,'DELIVERY_MODE');
 need(plan.sourceRevision===19&&plan.forwardRevision===21&&plan.recoveryRevision===22,'DELIVERY_REVISIONS');
 need(plan.sourceDeliveryHash===SOURCE19_BASELINE.acceptedDeliveryHash&&plan.sourcePublicHash===SOURCE19_BASELINE.publicConfigDigest&&plan.grantHash===SOURCE19_BASELINE.grantHash,'DELIVERY_SOURCE_NOT_PINNED');
 for(const n of ['nonce','targetReleaseHash','handoffHash','preservedStateHash','selectorBindingsHash'])need(HASH.test(plan[n]),'DELIVERY_PLAN_HASH');
 need(typeof plan.stopEpoch==='string'&&/^[a-f0-9]{8}(?:-[a-f0-9]{4}){3}-[a-f0-9]{12}$/.test(plan.stopEpoch),'DELIVERY_STOP_EPOCH');
 need(Number.isSafeInteger(now)&&Number.isSafeInteger(plan.approvedAt)&&Number.isSafeInteger(plan.expiresAt)&&Number.isSafeInteger(plan.recoveryDeadline)&&plan.approvedAt<=now&&plan.expiresAt>plan.approvedAt&&plan.expiresAt<=plan.approvedAt+300000&&plan.recoveryDeadline>=plan.expiresAt&&plan.recoveryDeadline<=plan.approvedAt+1800000,'DELIVERY_PLAN_TIME');
 const p=sourceDelivery?.body?.publicConfig;
 need(inspectSourcePublicConfiguration(p)===SOURCE19_BASELINE,'DELIVERY_SOURCE_NOT_PINNED');
 const b=verified(sourceDelivery,p.issuerPublicKey,'r16.configuration-delivery.v1');
 keys(b,['schema','revision','issuedAt','publicConfig','control']);
 need(digest(sourceDelivery)===plan.sourceDeliveryHash&&b.revision===19&&Number.isSafeInteger(b.issuedAt)&&b.issuedAt<=now&&same(b.control,{grantId:p.grant.body.id,grantVersion:1,status:'ACTIVE',connectRequested:true}),'DELIVERY_SOURCE_NOT_PINNED');
 const g=verified(p.grant,p.issuerPublicKey,'r16.workspace.v1');
 need(g.id==='r16-projects-daily'&&g.version===1&&same(g.actions,ACTIONS)&&same(g.peers,p.peers),'DELIVERY_GRANT');
 const r=verifyRelease(targetRelease,p.releasePublicKey,{versions:plan.targetVersions,actions:g.actions,now:plan.approvedAt});
 need(digest(targetRelease)===plan.targetReleaseHash&&digest(targetRelease)!==digest(p.release)&&r.id!==p.release.body.id&&same(Object.keys(r.versions).sort(),ROLES.slice().sort()),'DELIVERY_TARGET_NOT_PINNED');
 return Object.freeze({planHash:digest(plan),sourcePublic:copy(p),targetPublic:{...copy(p),release:copy(targetRelease),versions:copy(r.versions)}});
}
export function deliveryBody(inputs,phase){
 const scope=inspectDeliveryPlan(inputs),{plan}=inputs;
 need(['forward','recovery'].includes(phase),'DELIVERY_PHASE');
 return {schema:'r16.configuration-delivery.v1',revision:phase==='forward'?21:22,issuedAt:plan.approvedAt,publicConfig:phase==='forward'?scope.targetPublic:scope.sourcePublic,control:{grantId:scope.sourcePublic.grant.body.id,grantVersion:1,status:'ACTIVE',connectRequested:false}};
}
// A separate fixed-plan receiver, NOT a permissive revision override for the
// generic recovery projector. The previous envelope must be exact 19/21/22.
export function exactDeliveryVerifier(inputs){
 const scope=inspectDeliveryPlan(inputs),p=scope.sourcePublic;
 const body=phase=>deliveryBody(inputs,phase);
 const checkEnvelope=(e)=>{
  const b=verified(e,p.issuerPublicKey,'r16.configuration-delivery.v1');
  if(b.revision===19)need(digest(e)===inputs.plan.sourceDeliveryHash,'DELIVERY_SOURCE_CONFLICT');
  else need((b.revision===21||b.revision===22)&&same(b,body(b.revision===21?'forward':'recovery')),'DELIVERY_PLAN_CONFLICT');
  return b;
 };
 return (envelope,pin,previous,now)=>{
  need(same(pin,{issuerPublicKey:p.issuerPublicKey,releasePublicKey:p.releasePublicKey}),'DELIVERY_ROOT_CONFLICT');
  const b=checkEnvelope(envelope),old=checkEnvelope(previous);
  need(b.revision!==19&&b.issuedAt<=now,'DELIVERY_NEW_REVISION_REQUIRED');
  need(b.revision>=old.revision,'CONFIGURATION_ROLLBACK');
  if(b.revision===old.revision)need(same(envelope,previous),'CONFIGURATION_CONFLICT');
  return b;
 };
}
function guard(inputs,backend,operation,phase,now){
 const scope=inspectDeliveryPlan({...inputs,now}),{plan}=inputs;
 need(backend&&typeof backend.require==='function'&&typeof backend.fresh==='function','DELIVERY_BACKEND_UNINSTALLED');
 need(now<(phase==='recovery'?plan.recoveryDeadline:plan.expiresAt),'DELIVERY_AUTHORITY_EXPIRED');
 // A NEW forward code identity must remain currently valid. Recovery22 must
 // still close back to the pinned historical source if the target expires.
 if(phase==='forward')verifyRelease(inputs.targetRelease,scope.sourcePublic.releasePublicKey,{versions:plan.targetVersions,actions:ACTIONS,now});
 const request={operation,phase,planHash:scope.planHash,stopEpoch:plan.stopEpoch,handoffHash:plan.handoffHash,now};
 backend.require(copy(request));
 const f=backend.fresh(copy(request));
 need(f&&f.planHash===scope.planHash&&f.stopEpoch===plan.stopEpoch&&f.handoffHash===plan.handoffHash&&f.singleWriter==='HANDOFF_ACCEPTED_OWNER_FENCED'&&f.preservedStateHash===plan.preservedStateHash,'DELIVERY_FRESH_SCOPE_CHANGED');
 return scope;
}
// A borrowed view keeps the caller's ONE actual ProtectedStore lock alive.
// The cloud receiver may close its view; only withHostStore closes the owner.
export function borrowDeliveryStore(store){
 need(store instanceof ProtectedStore,'SELECTOR_HOST_LOCK_REQUIRED');
 store.guard();return Object.freeze({snapshot:()=>store.snapshot(),transact:fn=>store.transact(fn),close:()=>{}});
}
export function createExactCloudReceiver({inputs,backend,options,now=Date.now}){
 return envelope=>{
  const phase=envelope?.body?.revision===22?'recovery':'forward';
  return withHostStore({inputs,backend,openStore:options?.openStore,host:'cloud',envelope,now},store=>
   acceptConfiguration(envelope,{...options,openStore:()=>borrowDeliveryStore(store),now:now(),verify:exactDeliveryVerifier(inputs),beforeEffect:effect=>guard(inputs,backend,'cloud-'+effect,phase,now())}));
 };
}
// Same real ProtectedStore/cache format as OwnerAuthority.cloudDelivery().
// Only AFTER an admitted single-writer handoff. Preserve all authority fields;
// selector INTENT/RESULT metadata is under delivery, never the business ledger.
export function createFencedLocalReceiver({inputs,backend,openStore,readPublic,writePublic,now=Date.now}){
 need(typeof openStore==='function'&&typeof readPublic==='function'&&typeof writePublic==='function','LOCAL_DELIVERY_ADAPTER_UNINSTALLED');
 return envelope=>{
  const phase=envelope?.body?.revision===22?'recovery':'forward';
  return withHostStore({inputs,backend,openStore,host:'local',envelope,now},s=>{
   const before=s.snapshot(),invariant=copy(before);delete invariant.delivery;
   const p=inputs.sourceDelivery.body.publicConfig,prior=before.delivery;
   need(prior&&prior.revision===prior.envelope?.body?.revision&&prior.hash===digest({publicConfig:prior.envelope.body.publicConfig,control:prior.envelope.body.control,connectionNonce:before.connectionNonce||0})&&before.activeGrantId===p.grant.body.id,'LOCAL_DELIVERY_CACHE_CONFLICT');
   const b=exactDeliveryVerifier(inputs)(envelope,{issuerPublicKey:p.issuerPublicKey,releasePublicKey:p.releasePublicKey},prior.envelope,now());
   const cache={hash:digest({publicConfig:b.publicConfig,control:b.control,connectionNonce:before.connectionNonce||0}),revision:b.revision,envelope};
   if(prior.selectorTransaction)cache.selectorTransaction=copy(prior.selectorTransaction);
   guard(inputs,backend,'local-commit',phase,now());
   if(!same(prior,cache))s.transact(c=>{need(same(c,before),'LOCAL_DELIVERY_CAS');c.delivery=copy(cache);});
   const after=s.snapshot(),stable=copy(after);delete stable.delivery;
   need(same(stable,invariant)&&same(after.delivery,cache),'LOCAL_DELIVERY_READBACK');
   guard(inputs,backend,'local-project',phase,now());writePublic(copy(b.publicConfig));
   need(same(readPublic(),b.publicConfig),'LOCAL_PUBLIC_READBACK');
   return {status:'STORED',revision:b.revision,deliveryDigest:digest(envelope)};
  });
 };
}
// Existing accepted revision is the ONLY monotonic authority; no parallel
// maxRevision ledger. Configuration and physical selector effects both acquire
// the exact same protected store, so22 cannot interleave a selector21 rename.
function hostState(store,inputs,host,revision){
 need(store instanceof ProtectedStore,'SELECTOR_HOST_LOCK_REQUIRED');
 const s=store.snapshot();
 need(s.kind===(host==='cloud'?'r16.cloud-publication.v1':'r16.owner.configuration.v1'),'SELECTOR_HOST_STORE');
 const accepted=host==='cloud'?s.accepted:s.delivery?.envelope;
 const b=verified(accepted,inputs.sourceDelivery.body.publicConfig.issuerPublicKey,'r16.configuration-delivery.v1');
 need([19,21,22].includes(b.revision)&&b.revision<=revision,'SELECTOR_SUPERSEDED');
 const expected=b.revision===19?inputs.sourceDelivery.body:deliveryBody(inputs,b.revision===21?'forward':'recovery');
 need(same(b,expected)&&(b.revision!==19||digest(accepted)===inputs.plan.sourceDeliveryHash),'SELECTOR_ACCEPTED_PLAN_CONFLICT');
 const selection=host==='cloud'?s.selectorTransaction:s.delivery?.selectorTransaction;
 need(!selection||selection.planHash===digest(inputs.plan),'SELECTOR_HOST_BINDING');
 return {state:s,accepted,revision:b.revision,selection:selection||{planHash:digest(inputs.plan),phases:{}}};
}
function withHostStore({inputs,backend,openStore,host,envelope,now},fn){
 need(typeof openStore==='function','SELECTOR_HOST_LOCK_REQUIRED');
 const revision=envelope?.body?.revision,phase=revision===22?'recovery':'forward';
 need([21,22].includes(revision),'SELECTOR_REVISION');
 guard(inputs,backend,host+'-host-store',phase,now());
 const store=openStore();
 try{hostState(store,inputs,host,revision);return fn(store);}finally{store.close();}
}
function saveHostSelection(store,inputs,host,phase,step){
 store.transact(s=>{
  const container=host==='cloud'?s:s.delivery;
  const old=container.selectorTransaction||{planHash:digest(inputs.plan),phases:{}};
  need(old.planHash===digest(inputs.plan),'SELECTOR_HOST_BINDING');
  old.phases[phase]=copy(step);container.selectorTransaction=old;
 });
}
const bytesHash=x=>createHash('sha256').update(x).digest('hex');
export function selectorRequest(inputs,phase,envelope){
 return {schema:'mht.source19-selector-intent.v1',planHash:digest(inputs.plan),phase,
  revision:envelope.body.revision,deliveryDigest:digest(envelope),bindingsHash:inputs.plan.selectorBindingsHash,
  intentHash:digest({planHash:digest(inputs.plan),phase,deliveryDigest:digest(envelope),bindingsHash:inputs.plan.selectorBindingsHash})};
}
function validateBindings(inputs,bindings){
 need(bindings&&digest(bindings)===inputs.plan.selectorBindingsHash,'SELECTOR_BINDINGS_NOT_PINNED');
 keys(bindings,ROLES);
 for(const role of ROLES){
  const b=bindings[role];keys(b,['host','selectorFile','source','target']);
  need(b.host===(role==='native'?'local':'cloud')&&b.selectorFile===SELECTOR_FILES[role],'SELECTOR_BINDING');
  for(const phase of ['source','target']){
   keys(b[phase],['manifestFile','bytes']);
   const directory=phase==='target'?'/opt/r16/releases/'+inputs.targetRelease.body.id:
     role==='bridge'?HISTORICAL_R15_BASELINE.directory:SOURCE19_BASELINE.directory;
   need(b[phase].manifestFile===directory+'/'+role+'-manifest.json','SELECTOR_MANIFEST_PATH');
   const raw=Buffer.from(b[phase].bytes,'base64');
   need(raw.length>0&&raw.length<=262144&&raw.toString('base64')===b[phase].bytes,'SELECTOR_BYTES');
   const selector=JSON.parse(raw);
   need(selector.schema==='r16.'+role+'-host.v1'&&selector.codeManifest===b[phase].manifestFile&&selector.publicConfiguration===(role==='native'?'/run/r16-owner/public-config.json':'/etc/r16-cloud/public-config.json'),'SELECTOR_SEMANTICS');
  }
  const source=JSON.parse(Buffer.from(b.source.bytes,'base64')),target=JSON.parse(Buffer.from(b.target.bytes,'base64'));
  delete source.codeManifest;delete target.codeManifest;need(same(source,target),'SELECTOR_UNRELATED_CHANGE');
 }
 need(new Set(ROLES.map(r=>bindings[r].selectorFile)).size===3,'SELECTOR_DUPLICATE_PATH');
 return bindings;
}
function inspectSelectorRole(inputs,bindings,role,phase,readFile){
 const target=bindings[role][phase==='forward'?'target':'source'];
 const actual=Buffer.from(readFile(bindings[role].selectorFile));
 need(actual.equals(Buffer.from(target.bytes,'base64')),'SELECTOR_PHYSICAL_MISMATCH');
 const manifest=JSON.parse(readFile(target.manifestFile));
 const expected=phase==='forward'?inputs.plan.targetVersions[role]:SOURCE19_BASELINE.versions[role];
 need(runtimeVersion(manifest,role)===expected,'SELECTOR_MANIFEST_MISMATCH');
 const fileHashes={};
 for(const name of Object.keys(manifest.files)){
  const hash=bytesHash(readFile(path.join(path.dirname(target.manifestFile),name)));
  need(hash===manifest.files[name],'SELECTOR_CODE_MISMATCH');fileHashes[name]=hash;
 }
 return {selectorHash:bytesHash(actual),manifestFile:target.manifestFile,manifest,fileHashes};
}
function inspectHostSelectors(inputs,bindings,host,phase,readFile){
 return Object.fromEntries(ROLES.filter(r=>bindings[r].host===host).map(role=>[role,inspectSelectorRole(inputs,bindings,role,phase,readFile)]));
}
function assertAccepted(inputs,host,envelope,store,readProjection){
 const row=hostState(store,inputs,host,envelope.body.revision),p=readProjection(row.state);
 const projected=host==='cloud'?row.state.projectedDigest:digest(row.state.delivery.envelope);
 need(same(row.accepted,envelope)&&projected===digest(envelope)&&
   same(p.publicConfig,envelope.body.publicConfig)&&same(p.control,envelope.body.control),'SELECTOR_ACCEPTED_CHANGED');
}
function atomicSelector({file,bytes,expected,io,uid,guardBeforeRename,intentHash}){
 const stat=io.lstatSync(file);
 need(stat.isFile()&&!stat.isSymbolicLink()&&stat.uid===uid&&stat.nlink===1&&(stat.mode&0o7022)===0,'SELECTOR_FILE_UNTRUSTED');
 const temp=file+'.mht-selector-'+intentHash+'.pending';
 guardBeforeRename();
 const fd=io.openSync(temp,fs.constants.O_WRONLY|fs.constants.O_CREAT|fs.constants.O_EXCL|fs.constants.O_NOFOLLOW,stat.mode&0o777);
 try{guardBeforeRename();io.writeFileSync(fd,bytes);io.fsyncSync(fd);}finally{io.closeSync(fd);}
 // Last effect boundary: both admission and irreversible host phase are fresh.
 guardBeforeRename();
 const current=io.lstatSync(file);
 need(current.dev===stat.dev&&current.ino===stat.ino&&current.mode===stat.mode&&current.uid===stat.uid&&current.nlink===1&&
   Buffer.from(io.readFileSync(file)).equals(expected),'SELECTOR_FILE_CAS');
 guardBeforeRename();
 io.renameSync(temp,file);
 const dir=io.openSync(path.dirname(file),fs.constants.O_RDONLY|fs.constants.O_DIRECTORY|fs.constants.O_NOFOLLOW);
 try{io.fsyncSync(dir);}finally{io.closeSync(dir);}
 need(Buffer.from(io.readFileSync(file)).equals(bytes),'SELECTOR_DURABLE_READBACK');
}
/** Trusted fixed backend supplies the approved descriptor and actual protected
 * filesystem. No stdin/RPC caller can inject a path through this library.
 * Both configurations and selectors MUST open the SAME existing delivery store.
 */
export function createSelectorHostReceiver({inputs,bindings,host,backend,openStore,readProjection,readFile=protectedRuntimeFile,io=fs,uid=process.geteuid(),now=Date.now,fault=()=>{}}){
 bindings=copy(bindings);validateBindings(inputs,bindings);need(['cloud','local'].includes(host),'SELECTOR_HOST');
 if(!readProjection)readProjection=s=>({publicConfig:JSON.parse(readFile(host==='cloud'?'/etc/r16-cloud/public-config.json':'/run/r16-owner/public-config.json')),control:host==='cloud'?JSON.parse(readFile('/etc/r16-cloud/authority-control.json')):s.delivery.envelope.body.control});
 const inspect=(envelope,request)=>{
  validateBindings(inputs,bindings);
  const phase=envelope.body.revision===22?'recovery':'forward';
  need(same(request,selectorRequest(inputs,phase,envelope)),'SELECTOR_INTENT_CONFLICT');
  return withHostStore({inputs,backend,openStore,host,envelope,now},stage=>{
   const s=hostState(stage,inputs,host,envelope.body.revision),step=s.selection.phases[phase];
   need(step&&['INTENT','RESULT'].includes(step.status)&&step.intentHash===request.intentHash,'SELECTOR_EFFECT_UNKNOWN');
   assertAccepted(inputs,host,envelope,stage,readProjection);
   const roles=inspectHostSelectors(inputs,bindings,host,phase,readFile);
   if(step.status==='RESULT')need(digest(roles)===step.readbackHash,'SELECTOR_RESULT_CHANGED');
   else saveHostSelection(stage,inputs,host,phase,{...request,status:'RESULT',readbackHash:digest(roles)});
   return {host,revision:envelope.body.revision,planHash:request.planHash,bindingsHash:request.bindingsHash,
    roles,pendingEffects:0,hostPhase:s.revision};
  });
 };
 const commit=(envelope,request)=>{
  validateBindings(inputs,bindings);
  const phase=envelope.body.revision===22?'recovery':'forward';
  need(same(request,selectorRequest(inputs,phase,envelope)),'SELECTOR_INTENT_CONFLICT');
  return withHostStore({inputs,backend,openStore,host,envelope,now},stage=>{
   const s=hostState(stage,inputs,host,envelope.body.revision),prior=s.selection.phases[phase];
   assertAccepted(inputs,host,envelope,stage,readProjection);
   if(prior){
    need(prior.intentHash===request.intentHash,'SELECTOR_INTENT_CONFLICT');
    // INTENT-only is inspect-only. Partial physical effects cannot be replayed.
    const roles=inspectHostSelectors(inputs,bindings,host,phase,readFile);
    if(prior.status!=='RESULT')saveHostSelection(stage,inputs,host,phase,{...request,status:'RESULT',readbackHash:digest(roles)});
    return {host,roles,pendingEffects:0,revision:envelope.body.revision};
   }
   saveHostSelection(stage,inputs,host,phase,{...request,status:'INTENT'});fault(host+':intent');
   for(const role of ROLES.filter(r=>bindings[r].host===host)){
    const b=bindings[role],target=b[phase==='forward'?'target':'source'],desired=Buffer.from(target.bytes,'base64');
    const actual=Buffer.from(readFile(b.selectorFile));
    need(actual.equals(Buffer.from(b.source.bytes,'base64'))||phase==='recovery'&&actual.equals(Buffer.from(b.target.bytes,'base64')),'SELECTOR_FILE_CAS');
    // Verify signed manifest and all code BEFORE selecting it (using a read-only
    // view of the desired selector only; physical code/manifest remain real).
    inspectSelectorRole(inputs,bindings,role,phase,file=>file===b.selectorFile?desired:readFile(file));
    if(!actual.equals(desired))atomicSelector({file:b.selectorFile,bytes:desired,expected:actual,io,uid,intentHash:request.intentHash,
      guardBeforeRename:()=>{guard(inputs,backend,host+'-selector-'+role,phase,now());hostState(stage,inputs,host,envelope.body.revision);assertAccepted(inputs,host,envelope,stage,readProjection);}});
    fault(host+':'+role+':effect');
   }
   const roles=inspectHostSelectors(inputs,bindings,host,phase,readFile);
   saveHostSelection(stage,inputs,host,phase,{...request,status:'RESULT',readbackHash:digest(roles)});fault(host+':result');
   return {host,roles,pendingEffects:0,revision:envelope.body.revision};
  });
 };
 return Object.freeze({commit,inspect});
}
function selectorReadback(inputs,backend,envelope,request){
 const r=backend.readSelectors(copy(envelope),copy(request));
 need(r?.schema==='mht.source19-selector-readback.v1'&&r.planHash===digest(inputs.plan)&&r.revision===envelope.body.revision&&r.bindingsHash===inputs.plan.selectorBindingsHash,'SELECTOR_READBACK_SCOPE');
 const bindings=validateBindings(inputs,r.bindings),phase=envelope.body.revision===22?'recovery':'forward';
 keys(r.roles,ROLES);
 for(const role of ROLES){
  const x=r.roles[role],binding=bindings[role][phase==='forward'?'target':'source'];
  need(x&&x.manifestFile===binding.manifestFile&&x.selectorHash===bytesHash(Buffer.from(binding.bytes,'base64'))&&
    runtimeVersion(x.manifest,role)===envelope.body.publicConfig.versions[role]&&same(x.fileHashes,x.manifest.files),'SELECTOR_READBACK_ROLE');
 }
 const m=r.machine;
 need(m&&m.oldOwner?.state==='STOPPED_FENCED'&&m.oldOwner.writerCount===0&&
   (m.issuer?.state==='ABSENT'&&m.issuer.writerCount===0||m.issuer?.state==='RECOVERY_ONLY'&&m.issuer.writerCount===1&&m.issuer.planHash===digest(inputs.plan)&&m.issuer.connectRequested===false)&&
   m.preservedStateHash===inputs.plan.preservedStateHash&&m.originalUnknownCount===2&&m.currentInflight===0&&m.pendingEffects===0&&r.pendingEffects===0,'SELECTOR_MACHINE_NOT_SAFE');
 keys(m.roles,ROLES);
 for(const role of ROLES){
  const x=m.roles[role];need(x&&x.stopEpoch===inputs.plan.stopEpoch&&x.inflight===0&&x.admissionClosed===true&&x.pendingJob===false&&
   (x.state==='STOPPED'&&x.mainPid===0&&x.controlPid===0&&Array.isArray(x.members)&&x.members.length===0&&['inactive','failed'].includes(x.serviceState)||
    x.state==='BUSINESS_FENCED'&&Number.isSafeInteger(x.mainPid)&&x.mainPid>0&&x.serviceState==='active'&&HASH.test(x.fenceHash)&&x.writerAuthorityLimited===true),'SELECTOR_ROLE_NOT_SAFE');
 }
 for(const host of ['cloud','local'])need(r.hosts?.[host]?.hostPhase===envelope.body.revision&&r.hosts[host].pendingEffects===0,'SELECTOR_HOST_PHASE_UNPROVEN');
 return r;
}
function readback(inputs,backend,side,envelope){
 const r=backend[side==='cloud'?'readCloud':'readLocal']();
 const p=envelope.body.publicConfig,c=envelope.body.control;
 need(r&&same(r.accepted,envelope)&&same(r.publicConfig,p)&&same(r.control,c)&&r.projectedDigest===digest(envelope)&&r.preservedStateHash===inputs.plan.preservedStateHash,'DELIVERY_READBACK_NOT_EXACT');
 return {deliveryDigest:digest(envelope),revision:envelope.body.revision,preservedStateHash:r.preservedStateHash};
}
function preSignReadback(inputs,backend,phase){
 const {sourceDelivery}=inputs,source=sourceDelivery.body;
 const allowed=phase==='forward'?[source]:[source,deliveryBody(inputs,'forward'),deliveryBody(inputs,'recovery')];
 for(const side of ['Cloud','Local']){
  const r=backend['read'+side](),b=verified(r?.accepted,source.publicConfig.issuerPublicKey,'r16.configuration-delivery.v1');
  need(allowed.some(x=>same(x,b))&&r.preservedStateHash===inputs.plan.preservedStateHash,'DELIVERY_CURRENT_SCOPE_CHANGED');
  if(b.revision===19)need(digest(r.accepted)===inputs.plan.sourceDeliveryHash,'DELIVERY_CURRENT_SCOPE_CHANGED');
  if(phase==='forward')need(same(r.publicConfig,b.publicConfig)&&same(r.control,b.control)&&r.projectedDigest===digest(r.accepted),'DELIVERY_SOURCE_PROJECTION_CHANGED');
  else need(allowed.some(x=>same(x.publicConfig,r.publicConfig))&&allowed.some(x=>same(x.control,r.control)),'DELIVERY_RECOVERY_PROJECTION_CHANGED');
 }
}
function state(j,planHash){const s=j.snapshot();need(s.kind==='mht.source19-delivery-transaction.v1'&&(!s.binding||s.binding===planHash),'DELIVERY_JOURNAL_CONFLICT');return s;}
const safeCode=e=>typeof e?.code==='string'&&/^[A-Z][A-Z0-9_]{0,79}$/.test(e.code)?e.code:'DELIVERY_EFFECT_UNKNOWN';
/** Caller supplies an already opened protected journal (exclusive lifetime
 * lock) and a root-admitted backend. Nothing here discovers keys or installs a
 * production entry. Commit INTENT can only reconcile by exact readback, never
 * replay its external call. Sign INTENT without RESULT is permanently UNKNOWN.
 */
export function runDeliveryTransaction({journal,backend,plan,sourceDelivery,targetRelease,now=Date.now,fault=()=>{},mode='FORWARD'}){
 const inputs={plan,sourceDelivery,targetRelease},scope=inspectDeliveryPlan({...inputs,now:now()});
 need(journal instanceof ProtectedStore,'DELIVERY_JOURNAL_REQUIRED');
 need(['FORWARD','RECOVER'].includes(mode),'DELIVERY_MODE');
 need(backend&&['require','fresh','sign','commitCloud','commitLocal','readCloud','readLocal','commitSelectors','readSelectors'].every(k=>typeof backend[k]==='function'),'DELIVERY_BACKEND_UNINSTALLED');
 let s=state(journal,scope.planHash);
 const save=fn=>journal.transact(x=>{need(!x.binding||x.binding===scope.planHash,'DELIVERY_JOURNAL_CONFLICT');x.binding=scope.planHash;fn(x);});
 if(s.terminal&&mode==='RECOVER'&&s.terminal.status==='FORWARD_TERMINAL'){
  save(x=>{x.forwardTerminal=x.terminal;x.terminal=null;x.recoveryRequired=true;});s=state(journal,scope.planHash);
 }
 if(s.terminal){
  need(['FORWARD_TERMINAL','TERMINAL_RECOVERED'].includes(s.terminal.status),'DELIVERY_LEGACY_TERMINAL_NOT_COMPLETE');
  const phase=s.terminal.revision===22?'recovery':'forward',saved=s.steps[phase+'-sign'];
  need(saved?.status==='RESULT','DELIVERY_SIGNATURE_UNKNOWN');
  readback(inputs,backend,'cloud',saved.envelope);readback(inputs,backend,'local',saved.envelope);
  selectorReadback(inputs,backend,saved.envelope,selectorRequest(inputs,phase,saved.envelope));
  return copy(s.terminal);
 }
 const signPhase=phase=>{
  const key=phase+'-sign';s=state(journal,scope.planHash);
  const step=s.steps[key];
  if(step?.status==='RESULT'){
   need(same(verified(step.envelope,scope.sourcePublic.issuerPublicKey,'r16.configuration-delivery.v1'),deliveryBody(inputs,phase)),'DELIVERY_SIGNATURE_RESULT_CONFLICT');return step.envelope;
  }
  need(!step,'DELIVERY_SIGNATURE_UNKNOWN');
  guard(inputs,backend,key,phase,now());
  preSignReadback(inputs,backend,phase);
  const body=deliveryBody(inputs,phase);save(x=>{x.steps[key]={status:'INTENT',bodyHash:digest(body)};});fault(key+':intent');
  // Guard again after intent fsync, directly before private-key operation.
  guard(inputs,backend,key,phase,now());
  const envelope=backend.sign(copy(body),{phase,planHash:scope.planHash});
  need(same(verified(envelope,scope.sourcePublic.issuerPublicKey,'r16.configuration-delivery.v1'),body),'DELIVERY_SIGNATURE_RESULT_CONFLICT');
  fault(key+':effect');
  // Preserve a known signature BEFORE any expiry/freshness refusal.
  save(x=>{x.steps[key]={status:'RESULT',bodyHash:digest(body),envelope:copy(envelope)};});fault(key+':result');
  return envelope;
 };
 const commit=(phase,side,envelope)=>{
  const key=phase+'-'+side;s=state(journal,scope.planHash);
  if(s.steps[key]){
   const exact=readback(inputs,backend,side,envelope);
   if(s.steps[key].status!=='RESULT')save(x=>{x.steps[key]={status:'RESULT',...exact};});return;
  }
  guard(inputs,backend,key,phase,now());
  save(x=>{x.steps[key]={status:'INTENT',deliveryDigest:digest(envelope)};});fault(key+':intent');
  guard(inputs,backend,key,phase,now());
  let ack;
  try{ack=backend[side==='cloud'?'commitCloud':'commitLocal'](copy(envelope));fault(key+':effect');}
  catch(e){
   // A lost reply is not permission to send or sign again. Exact readback may
   // establish that this one call completed. Any other observation is pending.
   try{const exact=readback(inputs,backend,side,envelope);save(x=>{x.steps[key]={status:'RESULT',...exact};});return;}catch{throw e;}
  }
  need(ack?.status==='STORED'&&ack.revision===envelope.body.revision&&ack.deliveryDigest===digest(envelope),'DELIVERY_ACK_NOT_EXACT');
  const exact=readback(inputs,backend,side,envelope);save(x=>{x.steps[key]={status:'RESULT',...exact};});fault(key+':result');
 };
 const finish=phase=>{
  const envelope=signPhase(phase);commit(phase,'cloud',envelope);commit(phase,'local',envelope);
  readback(inputs,backend,'cloud',envelope);readback(inputs,backend,'local',envelope);
  const request=selectorRequest(inputs,phase,envelope),key=phase+'-selector';
  s=state(journal,scope.planHash);
  if(!s.steps[key]){
   guard(inputs,backend,key,phase,now());
   save(x=>{x.steps[key]={status:'INTENT',...request};});fault(key+':intent');
   guard(inputs,backend,key,phase,now());
   // An uncertain selector effect is NEVER replayed. Reentry only inspects.
   try{backend.commitSelectors(copy(envelope),copy(request));fault(key+':effect');}
   catch(e){try{selectorReadback(inputs,backend,envelope,request);}catch{throw e;}}
  }
  const selectors=selectorReadback(inputs,backend,envelope,request);
  if(state(journal,scope.planHash).steps[key].status!=='RESULT'){
   save(x=>{x.steps[key]={status:'RESULT',...request,readbackHash:digest(selectors)};});fault(key+':result');
  }
  // The overall terminal is AFTER physical selectors and the machine safety
  // readback, never merely after accepting the two configuration envelopes.
  readback(inputs,backend,'cloud',envelope);readback(inputs,backend,'local',envelope);
  const receipt={schema:'mht.source19-delivery-receipt.v2',status:phase==='forward'?'FORWARD_TERMINAL':'TERMINAL_RECOVERED',planHash:scope.planHash,deliveryDigest:digest(envelope),revision:envelope.body.revision,selectorReadbackHash:digest(selectors),readiness:DELIVERY_READINESS,entryImplementation:'ENTRY_UNIMPLEMENTED',productionAcceptance:'NOT_PROVEN',businessAcceptance:false,originalLedger:'PRESERVED_NOT_RESTORED',connectRequested:false};
  save(x=>{x.terminal=receipt;});return receipt;
 };
 s=state(journal,scope.planHash);
 if(mode==='RECOVER'||s.recoveryRequired||s.steps['recovery-sign']){
  need(s.steps['forward-sign']?.status==='RESULT','DELIVERY_SIGNATURE_UNKNOWN');
  return finish('recovery');
 }
 try{return finish('forward');}
 catch(e){
  s=state(journal,scope.planHash);
  // Unknown signer result cannot safely be replaced by another signature.
  if(s.steps['forward-sign']?.status!=='RESULT')throw e;
  save(x=>{x.recoveryRequired=true;x.failures.push({code:safeCode(e)});});
  return finish('recovery');
 }
}
