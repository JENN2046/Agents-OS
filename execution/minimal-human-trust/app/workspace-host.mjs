import {establishBusinessStop,signRuntimeBusinessStop} from '../src/runtime-business-stop.mjs';
import {replyWindow,waitUntilIssued} from '../src/control-clock.mjs';
import fs from 'node:fs';
import path from 'node:path';
import {randomUUID,createHash,timingSafeEqual} from 'node:crypto';
import {ProtectedStore,createParticipant,participantInitialState,signed,verified,digest,canonical,publicKey,verifyRelease} from '../src/lease-core.mjs';
const same=(a,b)=>canonical(a)===canonical(b);
const check=(v,c='AUTHORITY_REJECTED')=>{if(!v)throw Object.assign(Error(c),{code:c});};
const copy=x=>structuredClone(x);
export const appHostInitialState=()=>({kind:'r16.app-workspace.v1',projects:[],allocations:[],operations:[],status:'native_offline'});

// Loopback transport authenticates both direction and body. No automatic replay,
// redirects, credential discovery, arbitrary endpoints or public admin methods.
export function createWorkspaceClient({url,grant,signingKey,fetchImpl=fetch,now=Date.now}) {
 const u=new URL(url);check(u.protocol==='http:'&&u.hostname==='127.0.0.1'&&u.port&&u.pathname.endsWith('/workspace/exchange')&&!u.search&&!u.hash&&!u.username&&!u.password);
 const bridgeKey=publicKey(grant.body.peers.bridge.publicKey);
 return async(target,payload)=>{
  const t=now(),route=signed({schema:'r16.workspace-route.v1',id:randomUUID(),target,payloadHash:digest(payload),issuedAt:t,expiresAt:t+30000},signingKey);
  const response=await fetchImpl(u,{method:'POST',redirect:'error',headers:{'content-type':'application/vnd.r16.workspace+json'},body:JSON.stringify({route,payload}),signal:AbortSignal.timeout(15000)});
  check(response.ok,response.status===401||response.status===403?'CREDENTIALS_INVALID':'NATIVE_OFFLINE');
  check(response.body,'NATIVE_OFFLINE');let bytes=0;const chunks=[];
  for await(const chunk of response.body){bytes+=chunk.length;check(bytes<=3*1024*1024,'RESULT_TOO_LARGE');chunks.push(chunk);}
  const raw=JSON.parse(Buffer.concat(chunks).toString('utf8'));
  const b=verified(raw,bridgeKey,'r16.workspace-route-result.v1');
  check(b.id===route.body.id&&b.requestHash===digest(route),'PROOF_REJECTED');return b.result;
 };
}

export function createWorkspaceHost({store,directory,grant,release,versions,signingKey,issuerKey,releaseKey,
 channelCapability,crown,createCrownExecutor,exchange,now=Date.now}) {
 check(store instanceof ProtectedStore&&store.snapshot().kind==='r16.app-workspace.v1');
 const g=verified(grant,issuerKey,'r16.workspace.v1'),appKey=publicKey(g.peers.app.publicKey),nativeKey=publicKey(g.peers.native.publicKey);
 // A previously signed R15 release may be expired during an interrupted
 // close/reconcile. Authenticate it at its ORIGINAL issue time only when
 // durable local state actually needs recovery. New business still uses
 // current(), which always verifies the release at the current time.
 const historical=verified(release,releaseKey,'r16.release.v1');
 if(now()>=historical.notAfter&&now()>=historical.issuedAt){
  const prior=store.snapshot();
  check(prior.businessStop||prior.revoked||
    (Array.isArray(prior.projects)&&prior.projects.length>0)||
    (Array.isArray(prior.operations)&&prior.operations.some(o=>['UNKNOWN','INFLIGHT'].includes(o.status)))||
    (Array.isArray(prior.allocations)&&prior.allocations.some(o=>['UNKNOWN','INFLIGHT'].includes(o.status))),
    'RECOVERY_ONLY_REQUIRED');
  verifyRelease(release,releaseKey,{versions,actions:g.actions,now:historical.issuedAt});
 }else verifyRelease(release,releaseKey,{versions,actions:g.actions,now:now()});
 check(Buffer.isBuffer(channelCapability)&&channelCapability.length>=32&&typeof exchange==='function');
 const capabilityHash=createHash('sha256').update(channelCapability).digest();
 const contexts=new WeakMap(),entries=new Map(),rotations=new Map(),authorized=new Map(),inflight=new Map();
 let closed=false,draining=false,timer=null,tickRunning=false,tickPromise=null,closePromise=null,shutdownPromise=null,bridgeFreshUntil=0,bridgeRefresh=null,appFreshUntil=0,stoppedCleanups=0,liveLifecycle=0;
 const liveWork=new Set();
 async function tracked(work){liveLifecycle++;let running;try{running=Promise.resolve(work());liveWork.add(running);return await running;}finally{if(running)liveWork.delete(running);liveLifecycle--;}}
 const current=()=>{check(!closed&&!draining,'RECOVERY_UNRESOLVED');check(!store.snapshot().revoked&&!store.snapshot().businessStop,'GRANT_REVOKED');verifyRelease(release,releaseKey,{versions,actions:g.actions,now:now()});};
 const mark=status=>store.transact(s=>{s.status=status;});
 const markError=error=>mark(error?.code==='GRANT_REVOKED'?'revoked':error?.code==='CREDENTIALS_INVALID'?'credentials_invalid':['NATIVE_OFFLINE','ISSUER_UNAVAILABLE'].includes(error?.code)?'native_offline':'recovery_pending');
 function bridge(operation,data={}) {return tracked(()=>{
  if(['registry','sign_prepare','prepare','activate'].includes(operation))current();
  return exchange('bridge',{operation,data});
 });}
 async function control(operation,data={},fixed=null) {return tracked(async()=>{
  const cleanup=['status','close','drain','stop','reconcile','control_status','fresh'].includes(operation)||(operation==='issuer'&&['fresh','acknowledgeRevocation','closeLease','prepareStatus','heartbeat'].includes(data?.operation));
  if(!cleanup)current();
  const t=now(),proof=fixed??signed({schema:'r16.workspace-control.v1',id:randomUUID(),grantId:g.id,channel:g.channel,operation,data,issuedAt:t,expiresAt:t+30000},signingKey);
  const result=verified(await exchange('native',{command:'WorkspaceControl',proof}),nativeKey,'r16.workspace-control-result.v1');
  check(result.id===proof.body.id&&result.operation===operation&&result.ok===true,'NATIVE_CONTROL_REJECTED');return result.result;
 });}
 const issuer=(operation,params)=>control('issuer',{operation,params});
 async function freshApp(){
  if(now()<appFreshUntil)return;
  const issuedAt=now(),challenge=randomUUID(),request=signed({schema:'r16.fresh-request.v1',grantId:g.id,role:'app',peerId:g.peers.app.id,challenge,issuedAt},signingKey);
  const b=verified(await issuer('fresh',{request}),issuerKey,'r16.fresh.v1');
  check(b.grantId===g.id&&b.role==='app'&&b.peerId===g.peers.app.id&&b.challenge===challenge&&replyWindow(b,issuedAt,now()),'PROOF_REJECTED');
  if(b.status!=='ACTIVE'||b.version!==g.version){store.transact(s=>{s.revoked=true;s.revokedVersion=b.version;s.status='revoked';});await acknowledgeRevocation();check(false,'GRANT_REVOKED');}
  appFreshUntil=Math.min(b.expiresAt,now()+20000);
 }
 async function acknowledgeRevocation(){
  const s=store.snapshot();check(s.revoked&&s.revokedVersion>g.version,'NOT_REVOKED');
  const request=await bridge('fresh',{phase:'request'}),response=await issuer('fresh',{request});
  const result=await bridge('fresh',{phase:'accept',response});check(result.status==='REVOKED','REVOCATION_ACK');
  await issuer('acknowledgeRevocation',{proof:await bridge('revocation_ack')});
  const proof=signed({schema:'r16.revocation-ack.v1',grantId:g.id,version:s.revokedVersion,role:'app',peerId:g.peers.app.id,newOperationsStopped:true},signingKey);
  const receipt=await issuer('acknowledgeRevocation',{proof});
  check(['REVOKED','WAITING_OFFLINE_ACK'].includes(receipt.status),'REVOCATION_ACK');
  store.transact(state=>{state.revocationAcknowledged=true;state.status='revoked';});
 }
 async function freshBridge(projectId) {
  const request=await bridge('fresh',{phase:'request',...(projectId?{projectId}:{})});
  const response=await issuer('fresh',{request});
  const result=await bridge('fresh',{phase:'accept',...(projectId?{projectId}:{}),response});
  check(result.status==='CONNECTED','GRANT_REVOKED');
 }
 async function bridgeConnected() {
  if(now()<bridgeFreshUntil)return;
  if(!bridgeRefresh)bridgeRefresh=freshBridge().then(()=>{bridgeFreshUntil=now()+20000;}).finally(()=>{bridgeRefresh=null;});
  return bridgeRefresh;
 }

 function entry(project) {
  let e=entries.get(project.id);if(e){check(same(e.project,project),'PROJECT_BINDING');return e;}
  const registered=store.snapshot().projects.find(x=>x.project.id===project.id);check(registered&&same(registered.project,project),'PROJECT_BINDING');
  const dir=path.join(directory,'project-'+project.id);
  const exists=fs.existsSync(dir);check(exists||registered.initialized!==true,'STATE_MISSING');
  const pstore=new ProtectedStore({directory:dir,create:!exists,initial:participantInitialState('app'),now});
  const p=createParticipant({store:pstore,role:'app',signingKey,issuerKey,releaseKey,
   resolveProject:(workspace,target)=>{check(same(workspace,g.workspace)&&same(target,project)&&target.root.startsWith(workspace.root+'/'),'PROJECT_BINDING');return copy(target);}});
  p.pair({grant});store.transact(s=>{s.projects.find(x=>x.project.id===project.id).initialized=true;});e={project:copy(project),participant:p,store:pstore};entries.set(project.id,e);return e;
 }
 function remember(project) {
  check(typeof project?.id==='string'&&/^[A-Za-z0-9_-]{1,128}$/.test(project.id)&&project.workspaceId===g.workspace.id&&project.root.startsWith(g.workspace.root+'/'),'PROJECT_BINDING');
  store.transact(s=>{const e=s.projects.find(x=>x.project.id===project.id);if(e)check(same(e.project,project),'PROJECT_BINDING');else s.projects.push({project:copy(project),transition:null,retirement:null,initialized:false});});return entry(project);
 }
 async function fresh(e) {
  const request=e.participant.freshRequest(g.id),response=await issuer('fresh',{request});
  const r=e.participant.acceptFresh({response,grant});check(r.status==='CONNECTED','GRANT_REVOKED');
 }
 async function reconcile(e) {
  for(const record of store.snapshot().operations.filter(o=>o.projectId===e.project.id&&o.status!=='KNOWN')) {
   const found=await control('reconcile',{projectId:e.project.id,operationId:record.id,operation:record.operation});
   check(found?.receipt,'RECOVERY_UNRESOLVED');
   const r=verified(found.receipt,nativeKey,'r16.result.v1');
   if(found.nativeResult)check(r.resultHash===digest(found.nativeResult),'PROOF_REJECTED');
   e.participant.reconcile({receipt:found.receipt,operation:record.operation});
   await bridge('reconcile',{projectId:e.project.id,receipt:found.receipt,operation:record.operation});
   store.transact(s=>{const o=s.operations.find(x=>x.id===record.id);o.status='KNOWN';o.resultHash=r.resultHash;
    if(record.operation.body.action==='create_project'){
     const a=s.allocations.find(x=>x.project?.id===e.project.id);check(a,'PROJECT_BINDING');
     if(found.nativeResult?.fields?.ok===true)a.actualProjectId=found.nativeResult.fields.project_id;
     else a.creationRejected=true;
    }
   });
   await executor.resolvePending(record.id,{operation:record.operation,receipt:found.receipt,nativeResult:found.nativeResult});
  }
 }
 async function rotate(e) {
  await fresh(e);
  let transition=store.snapshot().projects.find(x=>x.project.id===e.project.id).transition;
  if(!transition) {
   const request={schema:'r16.prepare.v1',requestId:randomUUID(),grantId:g.id,grantVersion:g.version,project:e.project,channel:g.channel,versions,actions:e.project.id.startsWith('pending-')?['create_project']:g.actions,issuedAt:now()};
   transition={request,proofs:null,submitted:false,lease:null,activation:null};store.transact(s=>{s.projects.find(x=>x.project.id===e.project.id).transition=transition;});
  }
  if(!transition.lease) {
   if(transition.submitted){
    check(transition.proofs,'RECOVERY_UNRESOLVED');
    const queryId=randomUUID(),queryIssuedAt=now();
    const status=verified(await issuer('prepareStatus',{grantId:g.id,request:transition.request,proofs:transition.proofs,release,queryId,queryIssuedAt}),issuerKey,'r16.prepare-status.v1');
    check(status.grantId===g.id&&status.requestHash===digest(transition.request)&&status.queryId===queryId&&replyWindow(status,queryIssuedAt,now()),'PROOF_REJECTED');
    if(status.state==='PREPARED'){
     check(status.lease,'PROOF_REJECTED');
     const restored=await issuer('prepare',{grantId:g.id,request:transition.request,proofs:transition.proofs,release});
     check(same(restored,status.lease),'PROOF_REJECTED');transition={...transition,lease:restored};
    }
    else {check(status.state==='NOT_ISSUED'&&status.lease===null,'RECOVERY_UNRESOLVED');transition={...transition,submitted:false,proofs:null};}
    store.transact(s=>{s.projects.find(x=>x.project.id===e.project.id).transition=transition;});
   }
  }
  if(!transition.lease) {
   if(!transition.submitted&&now()-transition.request.issuedAt>20000){
    transition={...transition,request:{...transition.request,requestId:randomUUID(),issuedAt:now()},proofs:null};
    store.transact(s=>{s.projects.find(x=>x.project.id===e.project.id).transition=transition;});
   }
   if(!transition.proofs){
    check(!transition.submitted,'RECOVERY_UNRESOLVED');
    const nativeProof=await control('sign_prepare',{request:transition.request,release});
    const proofs={app:signed(transition.request,signingKey),bridge:await bridge('sign_prepare',{request:transition.request,release,nativeProof}),native:nativeProof};
    transition={...transition,proofs};store.transact(s=>{s.projects.find(x=>x.project.id===e.project.id).transition=transition;});
   }
   transition={...transition,submitted:true};store.transact(s=>{s.projects.find(x=>x.project.id===e.project.id).transition=transition;});
   const lease=await issuer('prepare',{grantId:g.id,request:transition.request,proofs:transition.proofs,release});
   transition={...transition,lease};store.transact(s=>{s.projects.find(x=>x.project.id===e.project.id).transition=transition;});
  }
  await freshBridge(e.project.id);
  const preparedClock=verified(transition.lease,issuerKey,'r16.lease.v1');
  await waitUntilIssued(preparedClock.issuedAt,preparedClock.expiresAt,{now});
  e.participant.prepare({lease:transition.lease,grant,release});
  await bridge('prepare',{projectId:e.project.id,lease:transition.lease,release});
  await control('prepare',{projectId:e.project.id,lease:transition.lease,release});
  await Promise.allSettled([...inflight].filter(([,v])=>v.projectId===e.project.id).map(([,v])=>v.promise));
  await reconcile(e);
  if(!transition.activation) {
   const evidence={app:e.participant.closeEvidence(),bridge:await bridge('close',{projectId:e.project.id}),native:await control('close',{projectId:e.project.id})};
   const activation=await issuer('activate',{grantId:g.id,projectId:e.project.id,evidence});
   transition={...transition,activation};store.transact(s=>{s.projects.find(x=>x.project.id===e.project.id).transition=transition;});
  }
  const activationClock=verified(transition.activation,issuerKey,'r16.activation.v1');
  await waitUntilIssued(activationClock.activatedAt,preparedClock.expiresAt,{now});
  // All old writers are durably closed before any of these activations.
  await control('activate',{projectId:e.project.id,activation:transition.activation});
  await bridge('activate',{projectId:e.project.id,activation:transition.activation});
  e.participant.activate({activation:transition.activation});
  archiveKnown(e.project.id,transition.lease.body.previousGeneration);
  store.transact(s=>{s.projects.find(x=>x.project.id===e.project.id).transition=null;s.status='ready';});
 }
 function archiveKnown(projectId,generation) {
  const rows=store.snapshot().operations.filter(o=>o.projectId===projectId&&o.status==='KNOWN'&&o.operation.body.generation<=generation);
  for(const row of rows)store.archive('app-operation-'+row.id,row);
  store.transact(s=>{const ids=new Set(rows.map(r=>r.id));s.operations=s.operations.filter(o=>!ids.has(o.id));});
 }
 async function retire(e) {
  const record=store.snapshot().projects.find(x=>x.project.id===e.project.id),snapshot=e.participant.snapshot();
  const lease=record.retirement?.lease??snapshot.closing??snapshot.pending?.lease??snapshot.active?.lease;
  if(!lease)return;
  store.transact(s=>{s.projects.find(x=>x.project.id===e.project.id).retirement={lease};});
  e.participant.drain({lease});
  await bridge('drain',{projectId:e.project.id,lease});await control('drain',{projectId:e.project.id,lease});
  await Promise.allSettled([...inflight.values()].filter(v=>v.projectId===e.project.id).map(v=>v.promise));
  await reconcile(e);
  const evidence={app:e.participant.stop({lease}),bridge:await bridge('close_current',{projectId:e.project.id,lease}),native:await control('stop',{projectId:e.project.id,lease})};
  const proof=await issuer('closeLease',{grantId:g.id,projectId:e.project.id,lease,evidence});
  const close=verified(proof,issuerKey,'r16.closed.v1');check(close.leaseHash===digest(lease),'PROOF_REJECTED');
  store.archive('app-close-'+e.project.id+'-'+lease.body.generation,proof);archiveKnown(e.project.id,lease.body.generation);
  store.transact(s=>{const row=s.projects.find(x=>x.project.id===e.project.id);row.transition=null;row.retirement=null;row.closedGeneration=lease.body.generation;for(const a of s.allocations)if(a.project?.id===e.project.id&&(a.actualProjectId||a.creationRejected))a.status='CLOSED';});
 }
 async function ensure(e) {
  if(rotations.has(e.project.id))return rotations.get(e.project.id);
  // Publish the shared flight before any freshness or retirement step can await.
  // Active-generation checks use the same single-challenge participants as rotation.
  const pending=Promise.resolve().then(async()=>{
  // A live call keeps its participant freshness until its result is reconciled.
  await Promise.allSettled([...inflight.values()].filter(v=>v.projectId===e.project.id).map(v=>v.promise));
  const recorded=store.snapshot().projects.find(x=>x.project.id===e.project.id);
  const unresolved=store.snapshot().operations.some(o=>o.projectId===e.project.id&&(o.status==='UNKNOWN'||(o.status==='INFLIGHT'&&!inflight.has(o.id))));
  if(recorded.retirement||unresolved||(recorded.transition?.lease&&now()>=recorded.transition.lease.body.expiresAt)){await retire(e);}
  const snap=e.participant.snapshot(),l=snap.active?.lease.body;
  if(l&&!recorded.transition&&!snap.pending&&!snap.closing&&now()<l.renewAt){
   await fresh(e);await freshBridge(e.project.id);
   const native=await control('fresh',{projectId:e.project.id}),remote=await bridge('status',{projectId:e.project.id});
   const leaseHash=digest(snap.active.lease);
   // A logged-out Native can durably stop its generation before APP/Bridge
   // have collected the joint closure. The authenticated fresh projection is
   // only a reason to attempt the normal retirement protocol, never its proof.
   const localStatus=e.participant.status();
   const nativeStopped=native.status?.role==='native'&&native.status.paired===true&&
    native.status.connected===true&&native.status.revoked===false&&native.status.version===g.version&&
    native.status.generation===l.generation&&native.status.available===false&&
    native.status.closing===false&&native.status.pendingGeneration===null&&native.status.expiresAt===null&&
    Array.isArray(native.status.unresolved)&&native.status.unresolved.length===0&&
    native.activeGeneration===0&&native.activeLeaseHash===null&&native.pendingLeaseHash===null&&native.closingLeaseHash===null;
   const bridgeCurrent=remote.available===true&&remote.activeGeneration===l.generation&&
    remote.activeLeaseHash===leaseHash&&remote.pendingLeaseHash===null&&remote.closingLeaseHash===null&&
    Array.isArray(remote.unresolved)&&remote.unresolved.length===0;
   if(nativeStopped&&localStatus.available&&localStatus.unresolved.length===0&&bridgeCurrent){
    check(![...inflight.values()].some(v=>v.projectId===e.project.id)&&
     !store.snapshot().operations.some(o=>o.projectId===e.project.id&&o.status!=='KNOWN'),'RECOVERY_UNRESOLVED');
    // stop() must return genuine role evidence and closeLease must verify it.
    // Any uncertain or failed close keeps retirement pending and blocks rotation.
    await retire(e);await rotate(e);return;
   }
   check(e.participant.status().available&&native.status.available&&remote.available&&native.activeGeneration===l.generation&&remote.activeGeneration===l.generation&&native.activeLeaseHash===leaseHash&&remote.activeLeaseHash===leaseHash&&!native.pendingLeaseHash&&!native.closingLeaseHash&&!remote.pendingLeaseHash&&!remote.closingLeaseHash,'RECOVERY_UNRESOLVED');
   return;
  }
  await rotate(e);
  });
  rotations.set(e.project.id,pending);
  try{await pending;e.ensureError=null;}catch(error){e.ensureError=error;markError(error);throw error;}finally{rotations.delete(e.project.id);}
 }
 async function recoverAllocations(){
  for(const allocation of store.snapshot().allocations.filter(a=>['UNKNOWN','INFLIGHT'].includes(a.status))){
   const found=await control('control_status',{id:allocation.id,originalProof:allocation.proof});
   if(found.status==='KNOWN'){
    const b=verified(found.response,nativeKey,'r16.workspace-control-result.v1');
    check(b.id===allocation.id&&b.operation==='allocate'&&b.ok===true&&b.result?.pending===true,'PROOF_REJECTED');
    remember(b.result.project);store.transact(s=>{Object.assign(s.allocations.find(a=>a.id===allocation.id),{status:'KNOWN',project:b.result.project});});
   }else if(found.status==='NOT_EXECUTED')store.transact(s=>{s.allocations.find(a=>a.id===allocation.id).status='NOT_EXECUTED';});
   else {check(['UNKNOWN','NOT_SEEN'].includes(found.status),'PROOF_REJECTED');mark('recovery_pending');}
  }
 }
 async function heartbeat(){
  const t=now(),state=store.snapshot(),projects=[];let available=true;
  for(const row of state.projects){
   const e=entry(row.project),s=e.participant.snapshot(),lease=s.pending?.lease||s.active?.lease;
   if(lease){const pending=!!s.pending||!!s.closing||t>=lease.body.expiresAt;projects.push({projectId:e.project.id,generation:lease.body.generation,leaseHash:digest(lease),phase:pending?'DRAINING':'ACTIVE'});if(pending||!e.participant.status().available)available=false;}
   else {const stopped=s.stopped.at(-1);if(stopped)projects.push({projectId:e.project.id,generation:stopped.body.generation,leaseHash:stopped.body.leaseHash,phase:'CLOSED'});}
  }
  const unresolved=state.operations.some(o=>o.status==='UNKNOWN'||(o.status==='INFLIGHT'&&!inflight.has(o.id)))||state.allocations.some(a=>['UNKNOWN','INFLIGHT'].includes(a.status));
  const credentialValid=t<appFreshUntil&&!state.revoked;
  const report=signed({schema:'r16.participant-heartbeat.v1',role:'app',peerId:g.peers.app.id,grantId:g.id,grantVersion:g.version,issuedAt:t,expiresAt:t+30000,ready:credentialValid&&available&&!unresolved&&!closed&&!draining&&!state.businessStop,credentialValid,unresolved,projects:projects.sort((a,b)=>a.projectId.localeCompare(b.projectId))},signingKey);
  await issuer('heartbeat',{report:await bridge('heartbeat')});
  const response=await issuer('heartbeat',{report});
  if(response.revoked||response.grantVersion!==g.version){store.transact(s=>{s.revoked=true;s.revokedVersion=response.grantVersion;s.status='revoked';});await acknowledgeRevocation();check(false,'GRANT_REVOKED');}
  if(response.connectRequested===false){for(const row of store.snapshot().projects)await retire(entry(row.project));mark('native_offline');}
  return response;
 }
 async function resolve(projectId) {const allocation=store.snapshot().allocations.find(a=>a.actualProjectId===projectId&&a.status!=='CLOSED');if(allocation)await retire(entry(allocation.project));const result=await control('resolve',{projectId});current();return remember(result.project);}
 const transport={
  async describe(){current();await freshApp();await bridgeConnected();const identity=await bridge('registry');return control('describe',{identity});},
  async allocateProject({request,workspace}) {
   current();check(workspace.id===g.workspace.id&&workspace.path===g.workspace.root&&request.action==='create_project','PROJECT_BINDING');
   await recoverAllocations();current();check(!store.snapshot().allocations.some(a=>['UNKNOWN','INFLIGHT'].includes(a.status)),'RECOVERY_UNRESOLVED');
   const unused=store.snapshot().allocations.find(a=>a.status==='KNOWN'&&!a.consumed&&a.project);
   if(unused){store.transact(s=>{s.allocations.find(a=>a.id===unused.id).consumed=true;});return {id:workspace.id,alias:workspace.alias,path:unused.project.root};}
   const t=now(),proof=signed({schema:'r16.workspace-control.v1',id:randomUUID(),grantId:g.id,channel:g.channel,operation:'allocate',data:{},issuedAt:t,expiresAt:t+30000},signingKey);
   store.transact(s=>{s.allocations.push({id:proof.body.id,status:'INFLIGHT',proof});});
   try {const result=await control('allocate',{},proof);remember(result.project);store.transact(s=>{Object.assign(s.allocations.find(a=>a.id===proof.body.id),{status:'KNOWN',project:result.project,consumed:true});});return {id:workspace.id,alias:workspace.alias,path:result.project.root};}
   catch(error){store.transact(s=>{s.allocations.find(a=>a.id===proof.body.id).status='UNKNOWN';s.status='recovery_pending';});throw error;}
  },
  async handle(proof) {
   current();
   const p=crown.verifyCall(proof,appKey,now());
   if(['list_workspaces','list_projects'].includes(p.request.action))return control(p.request.action,{proof});
   const context=authorized.get(p.request_id);check(context,'AUTHORITY_REJECTED');authorized.delete(p.request_id);
   const e=context.entry,operation=context.operation;
   // A scheduled refresh owns the single participant challenge until it settles.
   while(rotations.has(e.project.id))await rotations.get(e.project.id);
   current();crown.verifyCall(proof,appKey,now());
   check(!e.ensureError,'RECOVERY_UNRESOLVED');
   const dispatchLease=e.participant.snapshot().active?.lease;
   check(e.participant.status().available&&dispatchLease&&operation.body.generation===dispatchLease.body.generation&&operation.body.leaseHash===digest(dispatchLease),'RECOVERY_UNRESOLVED');
   store.archive('app-call-'+p.request_id,{operation,proof});
   store.transact(s=>{s.operations.push({id:p.request_id,projectId:e.project.id,operation,status:'INFLIGHT'});});
   const decision=e.participant.begin({operation});check(decision.decision==='EXECUTE','RECOVERY_UNRESOLVED');
   const work=(async()=>{
    const result=await exchange('native',{command:'WorkspaceCall',operation,proof});
    check(result?.receipt&&result.nativeResult,'RECOVERY_UNRESOLVED');
    const r=verified(result.receipt,nativeKey,'r16.result.v1');check(r.resultHash===digest(result.nativeResult),'PROOF_REJECTED');
    e.participant.reconcile({receipt:result.receipt,operation});
    store.transact(s=>{const o=s.operations.find(x=>x.id===p.request_id);o.status='KNOWN';o.resultHash=r.resultHash;});
    return result.nativeResult;
   })();
   inflight.set(p.request_id,{projectId:e.project.id,promise:work});
   let completed;
   try{completed=await work;}catch(error){try{e.participant.markUnknown(p.request_id);}catch{}store.transact(s=>{s.operations.find(o=>o.id===p.request_id).status='UNKNOWN';s.status='recovery_pending';});throw error;}finally{inflight.delete(p.request_id);}
   if(p.request.action==='create_project'&&completed.fields?.ok===true){
    store.transact(s=>{const a=s.allocations.find(x=>x.project?.id===e.project.id);check(a,'PROJECT_BINDING');a.actualProjectId=completed.fields.project_id;});
    try{await retire(e);}catch{mark('recovery_pending');}
   }
   return completed;
  }
 };
 const admission={
  admit(context,request){current();const record=contexts.get(context);check(record&&record.hash===digest(request),'AUTHORITY_REJECTED');return record;},
  owner(capability){check(capability?.channel===g.channel,'AUTHORITY_REJECTED');return g.channel;},
  async authorize(capability,p,{signal}={}) {
   const activeAdmission=()=>check(!signal?.aborted,'ADMISSION_CANCELLED');
   activeAdmission();current();check(capability?.channel===g.channel&&g.actions.includes(p.request.action),'AUTHORITY_REJECTED');
   if(!['list_workspaces','list_projects'].includes(p.request.action)){
    let e;
    if(p.request.action==='create_project') {const allocation=store.snapshot().allocations.find(x=>x.status==='KNOWN'&&x.project.root===p.workspace.path);check(allocation,'PROJECT_BINDING');e=entry(allocation.project);}
    else e=await resolve(p.binding?.projectId??p.request.project_id);
    activeAdmission();current();
    if(p.binding)check(p.binding.projectRoot===e.project.root&&p.binding.workspaceId===e.project.workspaceId,'PROJECT_BINDING');
    await ensure(e);activeAdmission();current();const lease=e.participant.snapshot().active.lease;
    const operation=signed({schema:'r16.operation.v1',id:p.request_id,grantId:g.id,projectId:e.project.id,generation:lease.body.generation,leaseHash:digest(lease),channel:g.channel,action:p.request.action,payloadHash:digest(p)},signingKey);
    authorized.set(p.request_id,{entry:e,operation});
   }
   return {authorized:true,trusted_client:true,explicit_intent:true,authorization_ref:p.authorization_ref,request_sha256:crown.digest(p.request),target_sha256:crown.digest(crown.callTarget(p))};
  },observeReceipt(){}
 };
 for(const name of ['describe','allocateProject','handle']){const original=transport[name];transport[name]=(...args)=>tracked(()=>original(...args));}
 const authorize=admission.authorize;admission.authorize=(...args)=>tracked(()=>authorize(...args));
 const rawExecutor=createCrownExecutor({enabled:true,privateKey:signingKey,admission,transport,now,timeoutMs:30000,partitionUnknownByProject:true,
  verifyPendingOutcome:(payload,evidence)=>{
   const o=verified(evidence.operation,appKey,'r16.operation.v1'),r=verified(evidence.receipt,nativeKey,'r16.result.v1');
   check(o.id===payload.request_id&&o.payloadHash===digest(payload)&&r.operationId===o.id&&r.operationHash===digest(evidence.operation)&&r.grantId===g.id&&r.projectId===o.projectId&&r.generation===o.generation,'PROOF_REJECTED');
   check(['COMPLETED','REJECTED','NOT_EXECUTED'].includes(r.outcome)&&r.resultHash===digest(evidence.nativeResult),'PROOF_REJECTED');return true;
  }});
 const executor=(...args)=>tracked(()=>rawExecutor(...args));
 for(const name of ['requiresTrustedContext','pending','resolvePending','close'])if(Object.hasOwn(rawExecutor,name))Object.defineProperty(executor,name,Object.getOwnPropertyDescriptor(rawExecutor,name));
 if(typeof rawExecutor.reconcile==='function')executor.reconcile=(...args)=>tracked(()=>rawExecutor.reconcile(...args));
 function resolveProjectForgeCrownContext(req) {
  current();check(['127.0.0.1','::1','::ffff:127.0.0.1'].includes(req.socket?.remoteAddress),'AUTHORITY_REJECTED');
  const headers=req.rawHeaders;check(Array.isArray(headers)&&headers.filter((v,i)=>i%2===0&&String(v).toLowerCase()==='x-r16-task-capability').length===1,'AUTHORITY_REJECTED');
  const value=req.headers?.['x-r16-task-capability'];check(typeof value==='string'&&value.length<=4096,'AUTHORITY_REJECTED');
  const actual=createHash('sha256').update(value).digest();check(timingSafeEqual(capabilityHash,actual),'AUTHORITY_REJECTED');
  const context=Object.freeze({});contexts.set(context,{channel:g.channel,hash:digest(req.body?.params?.arguments)});return context;
 }
 function stopAdmission(){draining=true;authorized.clear();if(timer){clearInterval(timer);timer=null;}}
 async function drainWork(){
  // A lifecycle call can create a transport flight after its first await. Keep
  // draining until all enclosing calls and their nested work have settled.
  while(true){
   const pending=[...(tickRunning&&tickPromise?[tickPromise]:[]),...liveWork,...rotations.values(),...[...inflight.values()].map(x=>x.promise)];
   if(!pending.length)return;
   await Promise.allSettled(pending);
  }
 }
 function shutdown(){
  if(shutdownPromise)return shutdownPromise;
  stopAdmission();
  shutdownPromise=(async()=>{
   await Promise.allSettled(closePromise?[closePromise]:[]);
   await drainWork();
   if(closed)return;
   let failure;
   try{await executor.close();}catch(error){failure=error;}
   // OS shutdown is not business retirement. Preserve leases, freshness,
   // UNKNOWN records and signed history; only release lifetime writer locks.
   for(const e of entries.values())try{e.store.close();}catch(error){failure??=error;}
   closed=true;try{store.close();}catch(error){failure??=error;}
   if(failure)throw failure;
  })();return shutdownPromise;
 }
 return Object.freeze({executor,shutdown,
  suspendBusiness({stopEpoch}){return establishBusinessStop(store,stopEpoch);},
  businessStopEvidence({revision,reviewDigest}){
   const participantStates=store.snapshot().projects.map(row=>entry(row.project).participant.snapshot());
   return signRuntimeBusinessStop({store,role:'app',signingKey,grant,release,revision,reviewDigest,
    busy:liveLifecycle+inflight.size+rotations.size+(tickRunning?1:0)+stoppedCleanups+(draining?1:0),participantStates,now:now()});
  },
  reconcileStopped(){check(!closed&&!draining,'APP_SHUTDOWN');return tracked(async()=>{check(store.snapshot().businessStop,'STOP_NOT_ESTABLISHED');stoppedCleanups++;try{return await Promise.all(store.snapshot().projects.map(row=>reconcile(entry(row.project))));}finally{stoppedCleanups--;}});},
  runtimeDependencies:{projectForgeCrownExecutor:executor,resolveProjectForgeCrownContext,
  projectForgeCrownDiscovery:Object.freeze({logical_name:'ProjectForge',tool:'vcp_project_forge',channel:'crown',capability_status:'not_evaluated',source:'approved_host_manifest'})},
  tick(){if(tickRunning||closed||draining)return Promise.resolve();tickRunning=true;
   tickPromise=(async()=>{try{
   if(store.snapshot().businessStop){for(const row of store.snapshot().projects)await reconcile(entry(row.project));return;}
   if(store.snapshot().revoked){if(!store.snapshot().revocationAcknowledged)await acknowledgeRevocation();return;}
   await freshApp();await bridgeConnected();await recoverAllocations();
   for(const p of store.snapshot().projects){const e=entry(p.project);if(e.project.id.startsWith('pending-')){
    const a=store.snapshot().allocations.find(x=>x.project?.id===e.project.id),snapshot=e.participant.snapshot();
    const unknown=store.snapshot().operations.some(o=>o.projectId===e.project.id&&(o.status==='UNKNOWN'||(o.status==='INFLIGHT'&&!inflight.has(o.id))));
    if(((a?.actualProjectId||a?.creationRejected)&&a.status!=='CLOSED')||unknown||(snapshot.active&&now()>=snapshot.active.lease.body.expiresAt))await retire(e);
    else if(p.transition)await ensure(e);
   }else await ensure(e);}
   await heartbeat();
  }catch(error){
   // Disconnect blocks fresh business admission, while authenticated heartbeat
   // and close remain reachable so the old generation can finish normally.
   if(!store.snapshot().revoked){try{const policy=await heartbeat();if(policy.connectRequested===false)return;}catch{}}
   markError(error);throw error;
  }finally{tickRunning=false;}})();return tickPromise;},
  // tick records its failure while its stores remain open; the timer only consumes it.
  start(){check(!timer&&!closed&&!draining);timer=setInterval(()=>this.tick().catch(()=>{}),15000);timer.unref();},
  close(){
   if(closePromise)return closePromise;
   check(!shutdownPromise&&!closed,'APP_SHUTDOWN');stopAdmission();
   closePromise=(async()=>{
    await drainWork();
    await Promise.allSettled([...liveWork]);
    await Promise.allSettled([...rotations.values()]);
    await Promise.allSettled([...inflight.values()].map(x=>x.promise));
    for(const project of store.snapshot().projects)await retire(entry(project.project));
    check(store.snapshot().operations.every(o=>o.status==='KNOWN'),'RECOVERY_UNRESOLVED');
    executor.close();for(const e of entries.values()){e.participant.disconnect();e.store.close();}closed=true;store.close();
   })();return closePromise;
  },
  status:()=>store.snapshot().status
 });
}