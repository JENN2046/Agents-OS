import {replyWindow} from '../src/control-clock.mjs';
import fs from 'node:fs';
import path from 'node:path';
import {createHash,randomUUID} from 'node:crypto';
import {ProtectedStore,createParticipant,participantInitialState,signed,verified,digest,canonical,publicKey,verifyRelease} from '../src/lease-core.mjs';
const check=(v,c='AUTHORITY_REJECTED')=>{if(!v)throw Object.assign(Error(c),{code:c});};
const same=(a,b)=>canonical(a)===canonical(b);
const clone=x=>JSON.parse(canonical(x));
const exact=(x,fields)=>check(x&&typeof x==='object'&&!Array.isArray(x)&&same(Object.keys(x).sort(),fields.slice().sort()),'INVALID_REQUEST');
const id=x=>check(typeof x==='string'&&/^[A-Za-z0-9_-]{1,128}$/.test(x),'INVALID_REQUEST');
const LOOPBACK=new Set(['127.0.0.1','::1','::ffff:127.0.0.1']);
export const bridgeInitialState=()=>({kind:'r16.workspace-bridge.v1',projects:[],approvals:[],calls:[],routes:[],challenge:null,version:0,revoked:false});
export function calculateRuntimeVersion(files,{entry='workspace-private-router.mjs'}={}) {
 check(files&&typeof files==='object'&&!Array.isArray(files)&&Object.keys(files).length>0,'RELEASE_NOT_APPROVED');
 check(Object.hasOwn(files,entry),'RELEASE_NOT_APPROVED');
 return digest({schema:'r16.runtime-code.v1',role:'bridge',entry,files:Object.fromEntries(Object.entries(files).map(([name,file])=>{
  check(typeof file==='string'&&path.isAbsolute(file),'RELEASE_NOT_APPROVED');
  const fd=fs.openSync(file,fs.constants.O_RDONLY|fs.constants.O_NOFOLLOW);
  try{const st=fs.fstatSync(fd);check(st.isFile(),'RELEASE_NOT_APPROVED');return [name,createHash('sha256').update(fs.readFileSync(fd)).digest('hex')];}finally{fs.closeSync(fd);}
 }))});
}
export function createWorkspaceBridge({store,directory,pluginManager,wss,crown,grant,release,versions,signingKey,issuerKey,releaseKey,runtimeFiles,runtimeEntry='workspace-private-router.mjs',now=Date.now}) {
 check(store instanceof ProtectedStore&&store.snapshot().kind==='r16.workspace-bridge.v1');
 check(typeof pluginManager?.processToolCall==='function'&&typeof wss?.getDistributedServerSnapshot==='function'&&typeof crown?.verifyCall==='function');
 const g=verified(grant,issuerKey,'r16.workspace.v1'),appKey=publicKey(g.peers.app.publicKey),nativeKey=publicKey(g.peers.native.publicKey);
 const participants=new Map(),inflight=new Map();let identity=null,closing=false,connected=false,freshUntil=0;
 const actualVersion=calculateRuntimeVersion(runtimeFiles,{entry:runtimeEntry});
 check(actualVersion===versions.bridge,'RELEASE_NOT_APPROVED');
 const approved=()=>verifyRelease(release,releaseKey,{versions,actions:g.actions,now:now()});approved();
 store.transact(s=>{s.challenge=null;for(const c of s.calls)if(c.status==='INFLIGHT')c.status='UNKNOWN';for(const r of s.routes)if(r.status==='INFLIGHT')r.status='UNKNOWN';});
 function disconnect(){connected=false;freshUntil=0;for(const e of participants.values())e.participant.disconnect();}
 function registry(){
  const plugin=pluginManager.plugins?.get('ProjectForge');
  const claims=wss.getDistributedServerSnapshot().filter(s=>s.connected===true&&s.tools?.includes('ProjectForge'));
  check(plugin?.isDistributed===true&&claims.length===1&&typeof plugin.serverId==='string'&&claims[0].serverId===plugin.serverId,'NATIVE_OFFLINE');
  const observed={logicalName:'ProjectForge',originKind:'distributed',originId:plugin.serverId,originKey:'distributed:'+plugin.serverId+':ProjectForge'};
  crown.identityCheck(observed);
  if(identity&&!same(identity,observed))disconnect();identity=observed;return clone(observed);
 }
 function resolver(workspace,project,options={}){
  check(same(workspace,g.workspace)&&project.workspaceId===workspace.id&&project.root.startsWith(workspace.root+'/'),'PROJECT_BINDING');
  const approval=store.snapshot().approvals.find(x=>same(x.request.project,project)&&(!options.actions||same(options.actions,x.request.actions)));
  check(approval,'PROJECT_BINDING');
  const proof=verified(approval.nativeProof,nativeKey,'r16.prepare.v1');check(same(proof,approval.request),'PROJECT_BINDING');return clone(project);
 }
 function participant(projectId){
  id(projectId);let e=participants.get(projectId);if(e)return e;
  const registered=store.snapshot().projects.includes(projectId),dir=path.join(directory,'project-'+projectId);
  check(registered||!fs.existsSync(dir),'STATE_UNAVAILABLE');
  const pstore=new ProtectedStore({directory:dir,create:!registered,initial:participantInitialState('bridge'),now});
  const p=createParticipant({store:pstore,role:'bridge',signingKey,issuerKey,releaseKey,resolveProject:resolver});p.pair({grant});
  e={participant:p,store:pstore};participants.set(projectId,e);
  if(!registered)store.transact(s=>{s.projects.push(projectId);});return e;
 }
 function globalFresh(data){
  if(data.phase==='request'){exact(data,['phase']);return store.transact((s,t)=>{s.challenge={nonce:randomUUID(),issuedAt:t};connected=false;freshUntil=0;return signed({schema:'r16.fresh-request.v1',grantId:g.id,role:'bridge',peerId:g.peers.bridge.id,challenge:s.challenge.nonce,issuedAt:t},signingKey);});}
  exact(data,['phase','response']);check(data.phase==='accept');const b=verified(data.response,issuerKey,'r16.fresh.v1');
  return store.transact((s,t)=>{check(s.challenge&&b.grantId===g.id&&b.role==='bridge'&&b.peerId===g.peers.bridge.id&&b.challenge===s.challenge.nonce&&replyWindow(b,s.challenge.issuedAt,t)&&b.version>=s.version,'STALE_CHALLENGE');s.version=b.version;s.revoked=b.status!=='ACTIVE'||b.version!==g.version;s.challenge=null;connected=!s.revoked;freshUntil=b.expiresAt;return {status:s.revoked?'REVOKED':'CONNECTED'};});
 }
 async function bridgeControl(payload){
  exact(payload,['operation','data']);const d=payload.data;
  if(payload.operation==='revocation_ack'){
   exact(d,[]);const state=store.snapshot();check(state.revoked===true&&state.version>g.version,'NOT_REVOKED');
   return signed({schema:'r16.revocation-ack.v1',grantId:g.id,version:state.version,role:'bridge',peerId:g.peers.bridge.id,newOperationsStopped:true},signingKey);
  }
  if(payload.operation==='heartbeat'){
   exact(d,[]);const t=now(),state=store.snapshot(),projects=[];let available=true,unresolved=false,trusted=true,online=true;
   try{approved();}catch{trusted=false;}try{registry();}catch{online=false;}
   for(const projectId of state.projects){
    const p=participant(projectId).participant,s=p.snapshot(),lease=s.pending?.lease||s.active?.lease;
    if(s.operations.some(o=>o.status==='UNKNOWN'||(o.status==='INFLIGHT'&&!inflight.has(o.id))))unresolved=true;
    if(lease){const draining=!!s.pending||!!s.closing||t>=lease.body.expiresAt;projects.push({projectId,generation:lease.body.generation,leaseHash:digest(lease),phase:draining?'DRAINING':'ACTIVE'});if(draining||!p.status().available)available=false;}
    else{const stopped=s.stopped.at(-1);if(stopped)projects.push({projectId,generation:stopped.body.generation,leaseHash:stopped.body.leaseHash,phase:'CLOSED'});else available=false;}
   }
   unresolved=unresolved||state.calls.some(o=>o.status==='UNKNOWN'||(o.status==='INFLIGHT'&&!inflight.has(o.id)));
   const credentialValid=connected&&t<freshUntil&&!state.revoked;
   return signed({schema:'r16.participant-heartbeat.v1',role:'bridge',peerId:g.peers.bridge.id,grantId:g.id,grantVersion:state.version||g.version,issuedAt:t,expiresAt:t+30000,ready:credentialValid&&trusted&&online&&available&&!unresolved&&!closing,credentialValid,unresolved,projects:projects.sort((a,b)=>a.projectId.localeCompare(b.projectId))},signingKey);
  }
  if(payload.operation==='registry'){exact(d,[]);approved();return registry();}
  if(payload.operation==='fresh'){
   if(!Object.hasOwn(d,'projectId'))return globalFresh(d);
   id(d.projectId);const p=participant(d.projectId).participant;
   if(d.phase==='request'){exact(d,['phase','projectId']);return p.freshRequest(g.id);}
   exact(d,['phase','projectId','response']);check(d.phase==='accept');return p.acceptFresh({response:d.response,grant});
  }
  if(payload.operation==='sign_prepare'){
   exact(d,['request','release','nativeProof']);approved();check(same(d.release,release),'RELEASE_NOT_APPROVED');
   const r=verified(d.nativeProof,nativeKey,'r16.prepare.v1');check(same(r,d.request),'PROJECT_BINDING');
   check(r.grantId===g.id&&r.grantVersion===g.version&&r.channel===g.channel&&same(r.versions,versions)&&r.project.workspaceId===g.workspace.id&&r.project.root.startsWith(g.workspace.root+'/'),'GRANT_BINDING');
   check(Number.isSafeInteger(r.issuedAt)&&r.issuedAt<=now()&&now()-r.issuedAt<=30000&&Array.isArray(r.actions)&&r.actions.length>0&&r.actions.every(a=>g.actions.includes(a)),'STALE_REQUEST');
   if(r.project.id.startsWith('pending-'))check(same(r.actions,['create_project']),'OPERATION_SCOPE');
   store.transact(s=>{const old=s.approvals.find(x=>x.request.requestId===r.requestId);if(old)check(same(old.request,r)&&same(old.nativeProof,d.nativeProof),'OPERATION_CONFLICT');else {const approval={request:clone(r),nativeProof:clone(d.nativeProof)};store.archive('bridge-prepare-'+digest(r.requestId),approval);s.approvals.push(approval);const own=s.approvals.filter(x=>x.request.project.id===r.project.id).slice(-2);s.approvals=s.approvals.filter(x=>x.request.project.id!==r.project.id).concat(own);}});
   return signed(r,signingKey);
  }
  id(d.projectId);const p=participant(d.projectId).participant;
  if(payload.operation==='prepare'){
   exact(d,['projectId','lease','release']);approved();check(same(d.release,release)&&d.lease?.body?.project?.id===d.projectId,'LEASE_BINDING');
   const a=store.snapshot().approvals.find(x=>x.request.requestId===d.lease.body.requestId)||store.archived('bridge-prepare-'+digest(d.lease.body.requestId));
   check(a&&same(a.request.project,d.lease.body.project)&&same(a.request.actions,d.lease.body.actions)&&same(a.request.versions,d.lease.body.versions),'PROJECT_BINDING');
   return p.prepare({lease:d.lease,grant,release});
  }
  if(payload.operation==='close'){exact(d,['projectId']);return p.closeEvidence();}
  if(payload.operation==='drain'){exact(d,['projectId','lease']);check(d.lease.body.project.id===d.projectId,'PROJECT_BINDING');return p.drain({lease:d.lease});}
  if(payload.operation==='close_current'){exact(d,['projectId','lease']);check(d.lease.body.project.id===d.projectId,'PROJECT_BINDING');return p.stop({lease:d.lease});}
  if(payload.operation==='activate'){exact(d,['projectId','activation']);approved();check(d.activation.body.projectId===d.projectId,'PROJECT_BINDING');return p.activate({activation:d.activation});}
  if(payload.operation==='status'){exact(d,['projectId']);const s=p.snapshot();return {...p.status(),activeLeaseHash:s.active?digest(s.active.lease):null,activeGeneration:s.active?.lease.body.generation||0,pendingLeaseHash:s.pending?digest(s.pending.lease):null,closingLeaseHash:s.closing?digest(s.closing):null};}
  if(payload.operation==='reconcile'){
   exact(d,Object.hasOwn(d,'operation')?['projectId','receipt','operation']:['projectId','receipt']);
   check(d.receipt?.body?.projectId===d.projectId,'PROJECT_BINDING');const result=p.reconcile({receipt:d.receipt,...(d.operation?{operation:d.operation}:{})});
   store.transact(s=>{const c=s.calls.find(x=>x.id===d.receipt.body.operationId);if(c){c.status='KNOWN';c.resultHash=d.receipt.body.resultHash;if(!store.archived('bridge-call-'+digest(c.id)))store.archive('bridge-call-'+digest(c.id),c);}s.calls=s.calls.filter(x=>x.status!=='KNOWN').concat(s.calls.filter(x=>x.status==='KNOWN').slice(-32));});return result;
  }
  check(false,'UNKNOWN_CONTROL');
 }
 async function nativeControl(args){
  exact(args,['command','proof']);const c=verified(args.proof,appKey,'r16.workspace-control.v1');
  check(c.grantId===g.id&&c.channel===g.channel&&c.issuedAt<=now()&&now()<c.expiresAt&&c.expiresAt-c.issuedAt<=30000,'AUTHORITY_REJECTED');
  // Signed Native controls enforce fresh issuer state themselves. In particular,
  // issuer:fresh must be reachable before Bridge freshness exists (no auth cycle).
  const observed=registry();const response=await pluginManager.processToolCall('ProjectForge',args);
  check(same(registry(),observed),'NATIVE_IDENTITY_CHANGED');
  const b=verified(response,nativeKey,'r16.workspace-control-result.v1');
  check(b.id===c.id&&b.operation===c.operation&&b.ok===true,'NATIVE_CONTROL_REJECTED');return response;
 }
 async function nativeCall(args){
  exact(args,['command','operation','proof']);approved();check(!store.snapshot().revoked,'GRANT_REVOKED');
  const operation=verified(args.operation,appKey,'r16.operation.v1'),payload=crown.verifyCall(args.proof,appKey,now());
  check(operation.id===payload.request_id&&operation.payloadHash===digest(payload)&&operation.action===payload.request.action&&operation.grantId===g.id&&operation.channel===g.channel,'OPERATION_SCOPE');
  const e=participant(operation.projectId),snapshot=e.participant.snapshot();
  const prior=store.archived('bridge-call-'+digest(operation.id))||store.snapshot().calls.find(x=>x.id===operation.id);
  if(prior){check(prior.hash===digest(args.operation),'OPERATION_CONFLICT');if(prior.status==='KNOWN'&&prior.result)return clone(prior.result);return {nativeResult:null,receipt:null};}
  const l=snapshot.active?.lease.body;check(l,'NOT_ACTIVE');
  const target=payload.binding?{id:payload.binding.projectId,workspaceId:payload.binding.workspaceId,root:payload.binding.projectRoot}:
   payload.request.action==='create_project'?{id:operation.projectId,workspaceId:payload.workspace?.id,root:payload.workspace?.path}:l.project;
  check(same(target,l.project),'PROJECT_BINDING');
  if(payload.request.path){check(typeof payload.request.path==='string'&&!path.isAbsolute(payload.request.path)&&!payload.request.path.includes('\\')&&payload.request.path.split('/').every(x=>x&&x!=='.'&&x!=='..'),'PATH_INVALID');}
  const observed=registry();check(same(observed,payload.identity),'NATIVE_IDENTITY_CHANGED');
  const decision=e.participant.begin({operation:args.operation});
  if(decision.decision!=='EXECUTE')return {nativeResult:null,receipt:null};
  store.transact(s=>{s.calls.push({id:operation.id,projectId:operation.projectId,hash:digest(args.operation),operation:clone(args.operation),status:'INFLIGHT',result:null,resultHash:null});});
  const work=(async()=>{
   try{
    const response=await pluginManager.processToolCall('ProjectForge',args);check(same(registry(),observed),'NATIVE_IDENTITY_CHANGED');
    check(response?.receipt&&response.nativeResult,'RECOVERY_UNRESOLVED');
    const receipt=verified(response.receipt,nativeKey,'r16.result.v1');check(receipt.operationId===operation.id&&receipt.operationHash===digest(args.operation)&&receipt.resultHash===digest(response.nativeResult),'RESULT_CONFLICT');
    e.participant.reconcile({receipt:response.receipt});
    const completed={id:operation.id,projectId:operation.projectId,hash:digest(args.operation),operation:clone(args.operation),status:'KNOWN',result:clone(response),resultHash:receipt.resultHash};store.archive('bridge-call-'+digest(operation.id),completed);store.transact(s=>{const c=s.calls.find(x=>x.id===operation.id);Object.assign(c,{...completed,result:null});s.calls=s.calls.filter(x=>x.status!=='KNOWN').concat(s.calls.filter(x=>x.status==='KNOWN').slice(-32));});return response;
   }catch{
    e.participant.markUnknown(operation.id);store.transact(s=>{s.calls.find(x=>x.id===operation.id).status='UNKNOWN';});return {nativeResult:null,receipt:null};
   }
  })();inflight.set(operation.id,work);try{return await work;}finally{inflight.delete(operation.id);}
 }
 async function exchange({route,payload}){
  check(!closing,'SERVICE_STOPPING');const r=verified(route,appKey,'r16.workspace-route.v1');
  exact(r,['schema','id','target','payloadHash','issuedAt','expiresAt']);id(r.id);
  check(['bridge','native'].includes(r.target)&&r.payloadHash===digest(payload)&&Number.isSafeInteger(r.issuedAt)&&Number.isSafeInteger(r.expiresAt)&&r.issuedAt<=now()&&now()<r.expiresAt&&r.expiresAt-r.issuedAt<=30000,'AUTHORITY_REJECTED');
  check(Buffer.byteLength(canonical(payload))<=2*1024*1024,'REQUEST_TOO_LARGE');
  const requestHash=digest(route),prior=store.archived('bridge-route-'+digest(r.id))||store.snapshot().routes.find(x=>x.id===r.id);
  if(prior){check(prior.hash===requestHash,'OPERATION_CONFLICT');check(prior.status==='KNOWN','RECOVERY_UNRESOLVED');return clone(prior.response);}
  store.transact(s=>{s.routes.push({id:r.id,hash:requestHash,status:'INFLIGHT',response:null});});
  try {
  const result=r.target==='bridge'?await bridgeControl(payload):payload.command==='WorkspaceControl'?await nativeControl(payload):payload.command==='WorkspaceCall'?await nativeCall(payload):check(false,'UNKNOWN_COMMAND');
  const response=signed({schema:'r16.workspace-route-result.v1',id:r.id,requestHash,result},signingKey);
  check(Buffer.byteLength(canonical(response))<=3*1024*1024,'RESULT_TOO_LARGE');
  store.archive('bridge-route-'+digest(r.id),{id:r.id,hash:requestHash,status:'KNOWN',response});store.transact(s=>{const record=s.routes.find(x=>x.id===r.id);record.status='KNOWN';record.response=null;s.routes=s.routes.filter(x=>x.status!=='KNOWN').concat(s.routes.filter(x=>x.status==='KNOWN').slice(-32));});return response;
  }catch(error){
   const saved=store.archived('bridge-route-'+digest(r.id));
   if(!saved)store.archive('bridge-route-'+digest(r.id),{id:r.id,hash:requestHash,status:'UNKNOWN',response:null});
   store.transact(s=>{const record=s.routes.find(x=>x.id===r.id);if(record)record.status='UNKNOWN';s.routes=s.routes.filter(x=>x.status==='INFLIGHT').concat(s.routes.filter(x=>x.status!=='INFLIGHT').slice(-32));});throw error;
  }
 }
 return Object.freeze({exchange,
  register(router){check(typeof router?.post==='function');router.post('/workspace/exchange',async(req,res)=>{
   try{check(LOOPBACK.has(req.socket?.remoteAddress),'LOOPBACK_REQUIRED');exact(req.body,['route','payload']);res.json(await exchange(req.body));}
   catch(e){const code=typeof e?.code==='string'&&/^[A-Z_]{1,64}$/.test(e.code)?e.code:'WORKSPACE_UNAVAILABLE';res.status(['BAD_SIGNATURE','LOOPBACK_REQUIRED','AUTHORITY_REJECTED'].includes(code)?403:code==='RECOVERY_UNRESOLVED'?409:503).json({status:code});}
  });},
  disconnect,
  async close(){closing=true;await Promise.allSettled([...inflight.values()]);for(const entry of participants.values()){entry.participant.disconnect();entry.store.close();}store.close();},
  status(){return {connected,revoked:store.snapshot().revoked,activeCalls:inflight.size};}
 });
}