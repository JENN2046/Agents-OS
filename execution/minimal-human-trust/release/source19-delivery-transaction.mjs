// Source-only protocol for a FUTURE root-admitted, single-writer R17 entry.
// No default key loader, filesystem selector, service operation or admission.
// Installing this library does not install/admit that entry: READY_UNINSTALLED.
import {ProtectedStore,canonical,digest,verified,verifyRelease,ROLES,ACTIONS} from '../src/lease-core.mjs';
import {SOURCE19_BASELINE,inspectSourcePublicConfiguration} from '../authority/source-baseline.mjs';
import {acceptConfiguration} from '../deployment/cloud-configuration-receiver.mjs';

const need=(v,c='SOURCE19_DELIVERY_REJECTED')=>{if(!v)throw Object.assign(Error(c),{code:c});};
const same=(a,b)=>canonical(a)===canonical(b);
const HASH=/^[a-f0-9]{64}$/;
const keys=(o,n)=>need(o&&same(Object.keys(o).sort(),n.slice().sort()),'DELIVERY_FIELDS');
const copy=x=>JSON.parse(canonical(x));
export const DELIVERY_READINESS='READY_UNINSTALLED';
export const DELIVERY_REVISIONS=Object.freeze({source:19,forward:21,recovery:22});
export const deliveryTransactionInitialState=()=>({kind:'mht.source19-delivery-transaction.v1',binding:null,steps:{},recoveryRequired:false,failures:[],terminal:null});

export function inspectDeliveryPlan({plan,sourceDelivery,targetRelease,now=Date.now()}){
 keys(plan,['schema','nonce','mode','sourceRevision','sourceDeliveryHash','sourcePublicHash','forwardRevision','recoveryRevision','targetReleaseHash','targetVersions','grantHash','stopEpoch','handoffHash','preservedStateHash','approvedAt','expiresAt','recoveryDeadline','connectRequested','allowForwardRecovery22']);
 need(plan.schema==='mht.source19-fixed-delivery-plan.v1'&&plan.mode==='recovery_only'&&plan.connectRequested===false&&plan.allowForwardRecovery22===true,'DELIVERY_MODE');
 need(plan.sourceRevision===19&&plan.forwardRevision===21&&plan.recoveryRevision===22,'DELIVERY_REVISIONS');
 need(plan.sourceDeliveryHash===SOURCE19_BASELINE.acceptedDeliveryHash&&plan.sourcePublicHash===SOURCE19_BASELINE.publicConfigDigest&&plan.grantHash===SOURCE19_BASELINE.grantHash,'DELIVERY_SOURCE_NOT_PINNED');
 for(const n of ['nonce','targetReleaseHash','stopEpoch','handoffHash','preservedStateHash'])need(HASH.test(plan[n]),'DELIVERY_PLAN_HASH');
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
export function createExactCloudReceiver({inputs,backend,options,now=Date.now}){
 return envelope=>{
  const phase=envelope?.body?.revision===22?'recovery':'forward';
  guard(inputs,backend,'cloud-commit',phase,now());
  // Spread options first: callers cannot replace the exact-plan verifier.
  return acceptConfiguration(envelope,{...options,now:now(),verify:exactDeliveryVerifier(inputs),beforeEffect:effect=>guard(inputs,backend,'cloud-'+effect,phase,now())});
 };
}
// Same real ProtectedStore/cache format as OwnerAuthority.cloudDelivery().
// Only callable AFTER an independently admitted single-writer handoff/fence.
// No proposal/selector update, connected/nonce/authority/ledger mutation or start.
export function createFencedLocalReceiver({inputs,backend,openStore,readPublic,writePublic,now=Date.now}){
 need(typeof openStore==='function'&&typeof readPublic==='function'&&typeof writePublic==='function','LOCAL_DELIVERY_ADAPTER_UNINSTALLED');
 return envelope=>{
  const phase=envelope?.body?.revision===22?'recovery':'forward';
  guard(inputs,backend,'local-commit',phase,now());
  const s=openStore();
  try{
   need(s instanceof ProtectedStore,'LOCAL_DELIVERY_STORE');
   const before=s.snapshot();need(before.kind==='r16.owner.configuration.v1','LOCAL_DELIVERY_STORE');
   const invariant=copy(before);delete invariant.delivery;
   const p=inputs.sourceDelivery.body.publicConfig,prior=before.delivery;
   need(prior&&prior.revision===prior.envelope?.body?.revision&&prior.hash===digest({publicConfig:prior.envelope.body.publicConfig,control:prior.envelope.body.control,connectionNonce:before.connectionNonce||0})&&before.activeGrantId===p.grant.body.id,'LOCAL_DELIVERY_CACHE_CONFLICT');
   const b=exactDeliveryVerifier(inputs)(envelope,{issuerPublicKey:p.issuerPublicKey,releasePublicKey:p.releasePublicKey},before.delivery?.envelope,now());
   const cache={hash:digest({publicConfig:b.publicConfig,control:b.control,connectionNonce:before.connectionNonce||0}),revision:b.revision,envelope};
   // Fresh authority after all reads and immediately before the durable write.
   guard(inputs,backend,'local-commit',phase,now());
   if(!same(before.delivery,cache))s.transact(c=>{need(same(c,before),'LOCAL_DELIVERY_CAS');c.delivery=copy(cache);});
   const after=s.snapshot(),stable=copy(after);delete stable.delivery;
   need(same(stable,invariant)&&same(after.delivery,cache),'LOCAL_DELIVERY_READBACK');
   guard(inputs,backend,'local-project',phase,now());writePublic(copy(b.publicConfig));
   need(same(readPublic(),b.publicConfig),'LOCAL_PUBLIC_READBACK');
   return {status:'STORED',revision:b.revision,deliveryDigest:digest(envelope)};
  }finally{s.close();}
 };
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
 need(backend&&['require','fresh','sign','commitCloud','commitLocal','readCloud','readLocal'].every(k=>typeof backend[k]==='function'),'DELIVERY_BACKEND_UNINSTALLED');
 let s=state(journal,scope.planHash);
 const save=fn=>journal.transact(x=>{need(!x.binding||x.binding===scope.planHash,'DELIVERY_JOURNAL_CONFLICT');x.binding=scope.planHash;fn(x);});
 if(s.terminal)return copy(s.terminal);
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
  const receipt={schema:'mht.source19-delivery-receipt.v1',status:phase==='forward'?'FORWARD_21_STORED_RECOVERY_ONLY':'RECOVERY_22_STORED_SOURCE_CODE_ONLY',planHash:scope.planHash,deliveryDigest:digest(envelope),revision:envelope.body.revision,readiness:DELIVERY_READINESS,entryImplementation:'ENTRY_UNIMPLEMENTED',productionAcceptance:'NOT_PROVEN',businessAcceptance:false,originalLedger:'PRESERVED_NOT_RESTORED',connectRequested:false};
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
