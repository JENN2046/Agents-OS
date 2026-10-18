import {controlWindow,waitUntilIssued} from '../src/control-clock.mjs';
import fs from 'node:fs';
import path from 'node:path';
import {createPublicKey,randomUUID,createHash} from 'node:crypto';
import {ProtectedStore,createParticipant,participantInitialState,signed,verified,digest,canonical,resolveRegisteredProject,verifyRelease,LEASE_MS,RENEW_BEFORE_MS} from '../src/lease-core.mjs';

const check=(ok,code='AUTHORITY_REJECTED')=>{if(!ok)throw Object.assign(new Error(code),{code});};
const same=(a,b)=>canonical(a)===canonical(b);
const exact=(object,names)=>check(object&&same(Object.keys(object).sort(),names.slice().sort()),'INVALID_REQUEST');
const id=value=>check(typeof value==='string'&&/^[A-Za-z0-9_-]{1,128}$/.test(value),'INVALID_REQUEST');
const publicKey=value=>createPublicKey({key:Buffer.from(value,'base64url'),format:'der',type:'spki'});
const clone=value=>JSON.parse(canonical(value));
// Historical signed reads only. These pins never authorize execution or settle a result.
const HISTORICAL_LOCAL_READS=Object.freeze([
 {projectId:'p2vox',operationId:'c434da49-055a-43dc-a3e3-695cce137909',generation:30,operationHash:'fd13e74ce69cb8ec30817ca0a48631cf3a6b6b2b08a410cc1b442df41992cc1f'},
 {projectId:'pmog2',operationId:'d0364f8b-3a68-4ca2-a396-7953b29cee4c',generation:38,operationHash:'38f6af1386e78e5d7ccd0710077d6a3a5e753e81722dd10f11a3a2ff9bd85da1'}]);
const HISTORICAL_LEASE_VERSIONS=Object.freeze({app:'235a5b919c65ac1d73290732d2b2014c24a338cc4b6795a5064e804803ec1e7a',bridge:'9c58c33478388003fd52da0cb15736ec951a9bfc9cf29738e20de5d741921352',native:'76319c50acaec649967986c1f12e6923ba4f664ac3230596ed2703fce3470ae6'});
const CLEANUP=new Set(['status','close','drain','stop','reconcile','control_status','fresh']);
const DISCOVERY=new Set(['list_workspaces','list_projects']);
const controlNames=new Set(['describe','resolve','allocate','list_workspaces','list_projects','sign_prepare','issuer','prepare','close','drain','stop','activate','status','fresh','reconcile','control_status']);

function immutableResult(directory,name,value) {
  id(name);const file=path.join(directory,name+'.json'),bytes=canonical(value);
  check(Buffer.byteLength(bytes)<=2*1024*1024,'RESULT_TOO_LARGE');
  let fd;
  try{fd=fs.openSync(file,fs.constants.O_WRONLY|fs.constants.O_CREAT|fs.constants.O_EXCL|fs.constants.O_NOFOLLOW,0o600);}
  catch(error){if(error.code==='EEXIST'){check(same(readResult(directory,name),value),'RESULT_CONFLICT');return;}throw error;}
  try{fs.writeFileSync(fd,bytes);fs.fsyncSync(fd);}finally{fs.closeSync(fd);}
  const dir=fs.openSync(directory,fs.constants.O_RDONLY|fs.constants.O_DIRECTORY|fs.constants.O_NOFOLLOW);try{fs.fsyncSync(dir);}finally{fs.closeSync(dir);}
}
function readResult(directory,name) {
  id(name);const fd=fs.openSync(path.join(directory,name+'.json'),fs.constants.O_RDONLY|fs.constants.O_NOFOLLOW);
  try{const st=fs.fstatSync(fd);check(st.isFile()&&st.nlink===1&&(st.mode&0o777)===0o600&&st.uid===process.geteuid()&&st.size<=2*1024*1024,'STATE_UNAVAILABLE');return JSON.parse(fs.readFileSync(fd,'utf8'));}finally{fs.closeSync(fd);}
}
export function assertNativeRuntimeStart(store){
  check(store instanceof ProtectedStore&&store.snapshot().kind==='r16.native-dispatch.v1','STATE_UNAVAILABLE');
  check(!store.snapshot().physicalStop,'PHYSICAL_STOP_FENCED');
}
export const NATIVE_HISTORY_PATH='/etc/r16-maintenance/source19-native-transition-r1-native-history.json';
export const NATIVE_HISTORY_POLICY='EXACT_INHERITED_LOCAL_UNCERTAINTY_ONLY';
const HISTORY_SOURCE={grantHash:'00ac437d66143e627132975555d06396d69ff69616f630d19e3622627e15c5e6',publicHash:'56e1df18a54950ea346a51654e61df60afe33cb9928ae77293b2cf336fd8a5ec',deliveryHash:'b8645f6fe206e84dd07c2c6c166bfe4016d1deefca28bf9545dcfa1560f013e9',nativeVersion:'2516e881b0622b3ac2d53c454e6ccf9950441c5cb3c26a53500b45d3b1dbe7b4'};
const HISTORY_TARGET='r16-daily-20261017-source19-native-lifecycle-r1';
const historyBrands=new WeakMap();
const historyHash=value=>typeof value==='string'&&/^[a-f0-9]{64}$/.test(value);
const historyNumber=value=>Number.isSafeInteger(value)&&value>=0;
function unknownControlProjection(state){
  check(Array.isArray(state.controls)&&state.controls.length<=100000,'CONTROL_HISTORY_SHAPE');
  const seen=new Set(),unknown=[];
  for(const row of state.controls){
    exact(row,['id','hash','status']);id(row.id);
    check(!seen.has(row.id)&&historyHash(row.hash)&&['KNOWN','NOT_EXECUTED','UNKNOWN'].includes(row.status),'CURRENT_WORK_UNRESOLVED');seen.add(row.id);
    if(row.status==='UNKNOWN')unknown.push(clone(row));
  }
  unknown.sort((a,b)=>a.id<b.id?-1:a.id>b.id?1:0);
  return {hash:digest(unknown),count:unknown.length};
}
function protectedHistoryBytes(file=NATIVE_HISTORY_PATH){
  check([NATIVE_HISTORY_PATH,'/etc/r16/native-host.json','/etc/r16/native-ledgers.json'].includes(file),'HISTORY_FIXED_PATH_REQUIRED');
  let cursor='';for(const bit of file.split('/').filter(Boolean)){
    cursor+='/'+bit;const st=fs.lstatSync(cursor);
    check(!st.isSymbolicLink()&&st.uid===0&&st.gid===0&&!(st.mode&0o022),'HISTORY_ROOT_SOURCE_UNSAFE');
    if(cursor!==file)check(st.isDirectory(),'HISTORY_ROOT_SOURCE_UNSAFE');
  }
  const fd=fs.openSync(file,fs.constants.O_RDONLY|fs.constants.O_NOFOLLOW);
  const stamp=st=>[st.dev,st.ino,st.uid,st.gid,st.mode,st.nlink,st.size,String(st.mtimeMs),String(st.ctimeMs)];
  try{const st=fs.fstatSync(fd);check(st.isFile()&&st.nlink===1&&(st.mode&0o7777)===0o644&&st.size<=128*1024,'HISTORY_DESCRIPTOR_UNSAFE');
    const raw=fs.readFileSync(fd);check(raw.length===st.size&&same(stamp(st),stamp(fs.fstatSync(fd)))&&same(stamp(st),stamp(fs.lstatSync(file))),'HISTORY_DESCRIPTOR_CHANGED');return raw;
  }finally{fs.closeSync(fd);}
}
function historyStoreIdentity(store){
  check(store instanceof ProtectedStore&&store.dir==='/var/lib/r16-native/grants/r16-projects-daily/dispatcher'&&fs.realpathSync(store.dir)===store.dir,'HISTORY_STORE_IDENTITY');
  const st=fs.lstatSync(store.dir);check(st.isDirectory()&&!st.isSymbolicLink()&&(st.mode&0o7777)===0o700,'HISTORY_STORE_IDENTITY');
  return {directory:store.dir,dev:st.dev,ino:st.ino};
}
// Only this fixed root-file reader can brand an inherited local baseline.
// It creates no STOP authority and never treats an unknown control as terminal.
export function loadNativeHistoryBaseline({store,config,publicConfig,manifest,ledgerRegistry,ledgerRegistryRaw,now=Date.now()}){
  if(config.nativeHistory===undefined)return null;
  exact(config.nativeHistory,['policy','descriptorSha256']);
  check(config.nativeHistory.policy===NATIVE_HISTORY_POLICY&&historyHash(config.nativeHistory.descriptorSha256),'HISTORY_POLICY_REQUIRED');
  check(same(JSON.parse(protectedHistoryBytes('/etc/r16/native-host.json').toString('utf8')),config),'HISTORY_ROOT_CONFIG_DRIFT');
  const raw=protectedHistoryBytes();check(digestBytes(raw)===config.nativeHistory.descriptorSha256,'HISTORY_DESCRIPTOR_DIGEST');
  const d=JSON.parse(raw.toString('utf8'));check(canonical(d)===raw.toString('utf8'),'HISTORY_DESCRIPTOR_CANONICAL');
  exact(d,['historicalOperations','schema','policy','planHash','stopProof','stopProofHash','checkpointHash','controlUnknownHash','controlUnknownCount','sourceNativeInstance','nativeTargetHash','sourcePublicConfigHash','sourceDeliveryHash','sourceNativeVersion','grantHash','targetReleaseId','targetNativeVersion','nativeHostBaseConfigHash','nativeLedgerRegistration','originalLeaseBindingsHash','registeredRootsHash','globalExecution','firstStopProof','authority']);
  const g=verified(publicConfig.grant,publicConfig.issuerPublicKey,'r16.workspace.v1');
  verifyRelease(publicConfig.release,publicConfig.releasePublicKey,{versions:publicConfig.versions,actions:g.actions,now});
  const baseConfig=clone(config);delete baseConfig.nativeHistory;
  check(d.schema==='r16.native-inherited-local-history.v1'&&d.policy===NATIVE_HISTORY_POLICY&&d.authority===false&&d.globalExecution==='UNPROVEN'&&d.firstStopProof==='NOT_PROVEN'&&
    d.sourcePublicConfigHash===HISTORY_SOURCE.publicHash&&d.sourceDeliveryHash===HISTORY_SOURCE.deliveryHash&&d.sourceNativeVersion===HISTORY_SOURCE.nativeVersion&&
    g.id==='r16-projects-daily'&&d.grantHash===HISTORY_SOURCE.grantHash&&d.grantHash===digest(publicConfig.grant)&&d.targetReleaseId===HISTORY_TARGET&&publicConfig.release.body.id===HISTORY_TARGET&&
    d.targetNativeVersion===publicConfig.versions.native&&digest(manifest)===d.targetNativeVersion&&manifest.role==='native'&&
    publicConfig.versions.app==='34731b300ccad9a1fbfd45b07422d847e8989d7e9dc052b0dda939cd99adb500'&&publicConfig.versions.bridge==='9c58c33478388003fd52da0cb15736ec951a9bfc9cf29738e20de5d741921352'&&
    config.codeManifest==='/opt/r16/releases/'+HISTORY_TARGET+'/native-manifest.json'&&d.nativeHostBaseConfigHash===digest(baseConfig),'HISTORY_TARGET_BINDING');
  for(const name of ['planHash','checkpointHash','stopProofHash','nativeTargetHash','controlUnknownHash','originalLeaseBindingsHash','registeredRootsHash'])check(historyHash(d[name]),'HISTORY_HASH_REQUIRED');
  check(historyNumber(d.controlUnknownCount)&&d.controlUnknownCount<=100000,'HISTORY_CONTROL_COUNT');
  const p=d.stopProof;check(p?.schema==='r16.source19-native-transition.stopped-fenced.v1'&&digest(p)===d.stopProofHash&&
    p.environment==='PRODUCTION'&&p.status==='STOPPED_FENCED_NOT_DRAINED'&&p.planHash===d.planHash&&p.checkpointHash===d.checkpointHash&&p.nativeTargetHash===d.nativeTargetHash&&
    p.sourcePublicConfigHash===d.sourcePublicConfigHash&&p.sourceDeliveryHash===d.sourceDeliveryHash&&p.grantHash===d.grantHash&&
    p.controlUnknownHash===d.controlUnknownHash&&p.controlUnknownCount===d.controlUnknownCount&&p.relayStopped===true&&p.noForeignWriters===true&&p.originalUnknownPreserved===true&&
    p.globalExecution==='UNPROVEN'&&p.roleStopReceipt===false&&p.businessAcceptance===false&&typeof p.forceTerminationUsed==='boolean'&&
    historyNumber(p.issuedAt)&&historyNumber(p.expiresAt)&&p.issuedAt<p.expiresAt,'HISTORY_STOP_PROOF');
  const units={'r16-owner.service':'jenn-System-Product-Name','r16-native.service':'jenn-System-Product-Name','r16-app.service':'VM-0-12-ubuntu','r16-bridge.service':'VM-0-12-ubuntu'};
  check(same(Object.keys(p.actors??{}).sort(),Object.keys(units).sort()),'HISTORY_ACTORS_REQUIRED');
  for(const [unit,host]of Object.entries(units)){const a=p.actors[unit];check(a.unit===unit&&a.host===host&&a.mainPid===0&&a.controlPid===0&&a.cgroupEmpty===true&&a.pendingJob===false&&a.ownedPersistentFence===true,'HISTORY_OLD_EXECUTOR_UNPROVEN');}
  const old=d.sourceNativeInstance;
  check(old&&digest(old)===d.nativeTargetHash&&old.unit==='r16-native.service'&&old.host==='jenn-System-Product-Name'&&Number.isSafeInteger(old.pid)&&old.pid>0&&typeof old.startTicks==='string'&&/^[0-9]+$/.test(old.startTicks)&&
    typeof old.bootId==='string'&&/^[a-f0-9]{8}(?:-[a-f0-9]{4}){3}-[a-f0-9]{12}$/.test(old.bootId)&&typeof old.invocationId==='string'&&/^[a-f0-9]{32}$/.test(old.invocationId)&&old.cgroup==='/system.slice/r16-native.service'&&old.nativeVersion===HISTORY_SOURCE.nativeVersion,'HISTORY_SOURCE_INSTANCE');
  const identity=historyStoreIdentity(store),registration=ledgerRegistry?.grants?.find(x=>x.grantId===g.id);
  check(ledgerRegistry.schema==='r16.native-ledgers.v1'&&registration?.status==='READY'&&registration.grantHash===d.grantHash&&registration.directory===identity.directory&&registration.dev===identity.dev&&registration.ino===identity.ino&&
    Buffer.isBuffer(ledgerRegistryRaw)&&same(JSON.parse(ledgerRegistryRaw.toString('utf8')),ledgerRegistry)&&same(d.nativeLedgerRegistration,{...identity,registryHash:digestBytes(ledgerRegistryRaw)}),'HISTORY_REGISTRATION_DRIFT');
  check(digestBytes(protectedHistoryBytes('/etc/r16/native-ledgers.json'))===d.nativeLedgerRegistration.registryHash,'HISTORY_REGISTRATION_DRIFT');
  const controls=unknownControlProjection(store.snapshot());check(controls.hash===d.controlUnknownHash&&controls.count===d.controlUnknownCount,'HISTORY_CONTROL_SET_DRIFT');
  check(Array.isArray(d.historicalOperations)&&d.historicalOperations.length===2,'HISTORY_SIGNED_OPERATIONS_REQUIRED');
  const appKey=publicKey(g.peers.app.publicKey);
  const operations=HISTORICAL_LOCAL_READS.map(pin=>{
    const found=d.historicalOperations.filter(op=>op?.body?.id===pin.operationId);check(found.length===1&&digest(found[0])===pin.operationHash,'HISTORY_SIGNED_OPERATIONS_REQUIRED');
    const op=verified(found[0],appKey,'r16.operation.v1');exact(op,['schema','id','grantId','projectId','generation','leaseHash','channel','action','payloadHash']);
    check(op.projectId===pin.projectId&&op.generation===pin.generation&&op.grantId===g.id&&op.channel===g.channel&&op.action==='find_symbol'&&historyHash(op.leaseHash)&&historyHash(op.payloadHash),'HISTORY_SIGNED_OPERATIONS_REQUIRED');return clone(found[0]);
  });
  const result=Object.freeze({scope:'LOCAL_ONLY',globalExecution:'UNPROVEN',firstStopProof:'NOT_PROVEN',controlUnknownHash:controls.hash,controlUnknownCount:controls.count,checkpointHash:d.checkpointHash,planHash:d.planHash});
  historyBrands.set(result,{historicalOperations:operations,...identity,pid:process.pid,start:processStart(process.pid),grantHash:d.grantHash,nativeVersion:d.targetNativeVersion,descriptorSha256:digestBytes(raw),configHash:digest(config),registryHash:d.nativeLedgerRegistration.registryHash});return result;
}
function digestBytes(raw){return createHash('sha256').update(raw).digest('hex');}
function inspectNativeHistoryBaseline(baseline,store,grant,versions){
  const binding=historyBrands.get(baseline);check(binding&&Object.isFrozen(baseline)&&binding.pid===process.pid&&binding.start===processStart(process.pid)&&binding.grantHash===digest(grant)&&binding.nativeVersion===versions.native&&same(historyStoreIdentity(store),{directory:binding.directory,dev:binding.dev,ino:binding.ino}),'HISTORY_BRANDED_BASELINE_REQUIRED');
  check(digestBytes(protectedHistoryBytes())===binding.descriptorSha256&&digest(JSON.parse(protectedHistoryBytes('/etc/r16/native-host.json').toString('utf8')))===binding.configHash,'HISTORY_ROOT_BINDING_DRIFT');
  check(digestBytes(protectedHistoryBytes('/etc/r16/native-ledgers.json'))===binding.registryHash,'HISTORY_REGISTRATION_DRIFT');
  const current=unknownControlProjection(store.snapshot());check(current.hash===baseline.controlUnknownHash&&current.count===baseline.controlUnknownCount,'HISTORY_CONTROL_SET_DRIFT');return baseline;
}
export const dispatcherInitialState=()=>({kind:'r16.native-dispatch.v1',controls:[],pending:[],projects:[],revoked:false,version:0});
function processStart(pid){try{const raw=fs.readFileSync('/proc/'+pid+'/stat','utf8');return raw.slice(raw.lastIndexOf(')')+2).split(' ')[19];}catch(error){if(error.code==='ENOENT')return null;throw Object.assign(Error('RECOVERY_REQUIRED'),{code:'RECOVERY_REQUIRED'});}}

// This composition creates real participants, journals native results, and calls
// the exact ProjectForge workspace engine. The issuer client must connect only
// to the private protected issuer socket; no authorization callback is accepted.
export function createWorkspaceDispatcher({store,directory,native,crown,grant,release,versions,
  signingKey,issuerKey,releaseKey,issuer,workspaceAlias,databasePath,now=Date.now,
  historicalOperations=[],beforePhysicalClose,inheritedHistory=null}) {
  check(store instanceof ProtectedStore&&store.snapshot().kind==='r16.native-dispatch.v1');
  const g=verified(grant,issuerKey,'r16.workspace.v1');
  const appKey=publicKey(g.peers.app.publicKey);
  check(typeof issuer?.fresh==='function'&&native?.createWorkspaceCrownPort&&typeof workspaceAlias==='string');
  const resultDirectory=path.join(directory,'results');
  if(!fs.existsSync(resultDirectory))fs.mkdirSync(resultDirectory,{mode:0o700});
  const resultStat=fs.lstatSync(resultDirectory);
  check(resultStat.isDirectory()&&!resultStat.isSymbolicLink()&&resultStat.uid===process.geteuid()&&(resultStat.mode&0o777)===0o700,'STATE_UNAVAILABLE');
  assertNativeRuntimeStart(store);
  check(beforePhysicalClose===undefined||typeof beforePhysicalClose==='function','INVALID_REQUEST');
  const initialControls=clone(store.snapshot().controls);
  if(inheritedHistory)inspectNativeHistoryBaseline(inheritedHistory,store,grant,versions);
  store.transact(s=>{for(const c of s.controls)if(c.status==='INFLIGHT')c.status='UNKNOWN';});
  let engine=null,identity=null,transportIdentity=null,fresh=false,closing=false;
  const participants=new Map(),contexts=new Map(),active=new Set(),physicalStores=new Map(),initialParticipants=new Map(),outerWork=new Set();
  let localShutdownPromise=null,localResourcesClosed=false,storesReleased=false;
  let controlQueue=Promise.resolve(),pendingWork=0;
  function queueWork(callback){pendingWork++;const work=controlQueue.then(callback);controlQueue=work.catch(()=>{});return work.finally(()=>{pendingWork--;});}
  function validateWorkspace() {
    let cursor=path.parse(g.workspace.root).root;
    for(const segment of g.workspace.root.slice(cursor.length).split(path.sep)){
      cursor=path.join(cursor,segment);const st=fs.lstatSync(cursor);check(st.isDirectory()&&!st.isSymbolicLink(),'PATH_SYMLINK');
    }
    const st=fs.statSync(g.workspace.root);check(st.dev===g.workspace.dev&&st.ino===g.workspace.ino,'WORKSPACE_REPLACED');
  }
  function assertCurrent() {
    check((!closing||active.size>0)&&fresh&&!store.snapshot().revoked&&!store.snapshot().admissionStopped&&!store.snapshot().recoveryOnly,'GRANT_REVOKED');validateWorkspace();
    verifyRelease(release,releaseKey,{versions,actions:g.actions,now:now()});
  }
  function lookup(projectId) {check(engine,'AUTHORITY_UNAVAILABLE');const p=engine.lookupProject(projectId);return {id:p.id,workspaceId:p.workspaceId,root:p.root};}
  function resolveProject(workspace,project,options={}) {
    check(same(workspace,g.workspace),'PROJECT_BINDING');
    const pending=store.snapshot().pending.find(p=>p.project.id===project.id);
    if(pending){check(same(pending.project,project)&&pending.status==='ALLOCATED'&&(!options.actions||same(options.actions,['create_project'])),'PROJECT_BINDING');validateWorkspace();const st=fs.lstatSync(project.root);check(st.isDirectory()&&!st.isSymbolicLink()&&st.dev===pending.dev&&st.ino===pending.ino&&fs.realpathSync(project.root)===project.root,'PROJECT_BINDING');return clone(project);}
    return resolveRegisteredProject(workspace,project,lookup);
  }
  async function freshParticipant(entry,{allowRevoked=false}={}) {
    const request=entry.participant.freshRequest(g.id);
    const response=await issuer.fresh({request});
    const state=entry.participant.acceptFresh({response,grant});
    check(state.status==='CONNECTED'||allowRevoked&&state.status==='REVOKED','GRANT_REVOKED');
    return state;
  }
  function participant(projectId) {
    id(projectId);let entry=participants.get(projectId);if(entry)return entry;
    const dir=path.join(directory,'project-'+projectId);
    const pstore=new ProtectedStore({directory:dir,create:!fs.existsSync(dir),initial:participantInitialState('native'),now});
    initialParticipants.set(projectId,clone(pstore.snapshot()));
    const p=createParticipant({store:pstore,role:'native',signingKey,issuerKey,releaseKey,resolveProject});
    p.pair({grant});entry={participant:p,store:pstore};participants.set(projectId,entry);
    store.transact(s=>{if(!s.projects.includes(projectId))s.projects.push(projectId);});return entry;
  }
  function recoveryFence({allowClosedRelease=false}={}) {
    const state=store.snapshot();
    const projects=state.projects.map(projectId=>{
      const p=participant(projectId).participant;
      return {state:p.snapshot(),status:p.status()};
    });
    // A lost result fences business, not the authenticated transport needed to
    // recover it. Persist this independently of Owner's connectRequested flag.
    if(projects.some(p=>p.status.unresolved.length>0)){
      if(!state.recoveryOnly||!state.admissionStopped)
        store.transact(s=>{s.recoveryOnly=true;s.admissionStopped=true;});
    }else if(allowClosedRelease&&state.recoveryOnly&&
      projects.every(p=>!p.state.active&&!p.state.pending&&!p.state.closing)&&
      !state.controls.some(c=>['UNKNOWN','INFLIGHT'].includes(c.status))&&
      state.pending.every(p=>p.status==='CREATED')){
      // Only a successful live ACTIVE freshness check may reach this branch.
      // Preserve independent STOP/disconnect fences. Owner must still confirm
      // connection and every new lease still needs its normal signed admission.
      try{validateWorkspace();verifyRelease(release,releaseKey,{versions,actions:g.actions,now:now()});}
      catch{return true;} // Expiry/drift must not cut off cleanup transport.
      store.transact(s=>{s.recoveryOnly=false;});
    }
    return store.snapshot().recoveryOnly===true;
  }
  function authorizeCall(p) {
    const context=contexts.get(p.request_id);
    check(context&&same(context.payload,p),'AUTHORITY_REJECTED');
    assertCurrent();
    if(!context.discovery){
      const snapshot=context.entry.participant.snapshot(),l=snapshot.active?.lease.body;
      check(l&&!snapshot.pending&&l.generation===context.operation.generation&&now()<l.expiresAt,'LEASE_EXPIRED');
      const target=p.binding?{id:p.binding.projectId,workspaceId:p.binding.workspaceId,root:p.binding.projectRoot}:
        p.request.action==='create_project'?{id:context.operation.projectId,workspaceId:p.workspace.id,root:p.workspace.path}:l.project;
      check(same(target,l.project),'PROJECT_BINDING');resolveProject(g.workspace,target);
      if(p.request.project_id)check(p.request.project_id===l.project.id,'PROJECT_BINDING');
    }
    return {authorized:true,trusted_client:true,explicit_intent:true,authorization_ref:p.authorization_ref,
      request_sha256:crown.digest(p.request),target_sha256:crown.digest(crown.callTarget(p))};
  }
  function describe(nextIdentity) {
    crown.identityCheck(nextIdentity);
    check(!transportIdentity||same(nextIdentity,transportIdentity),'IDENTITY_MISMATCH');
    if(engine&&same(identity,nextIdentity))return engine.callStatus();
    check(active.size===0,'RECOVERY_UNRESOLVED');
    for(const entry of participants.values())check(entry.participant.status().unresolved.length===0,'RECOVERY_UNRESOLVED');
    if(engine)engine.close();
    identity=clone(nextIdentity);
    engine=native.createWorkspaceCrownPort({publicKey:appKey,callIdentity:identity,authorizeCall,
      workspace:{id:g.workspace.id,alias:workspaceAlias,path:g.workspace.root},databasePath,validateAuthority:assertCurrent,now});
    return engine.callStatus();
  }
  function drainBusiness() {
    for(const projectId of store.snapshot().projects){
      const entry=participant(projectId),s=entry.participant.snapshot(),lease=s.pending?.lease??s.closing??s.active?.lease;
      if(lease)entry.participant.drain({lease});
    }
  }
  async function refresh(invalidate=true,{allowRevoked=false}={}) {
    if(invalidate){fresh=false;for(const entry of participants.values())entry.participant.disconnect();}
    const challenge=randomUUID(),issuedAt=now();
    const request=signed({schema:'r16.fresh-request.v1',grantId:g.id,role:'native',peerId:g.peers.native.id,challenge,issuedAt},signingKey);
    let envelope;
    try{envelope=await issuer.fresh({request});}
    catch(error){
      const s=store.snapshot();
      // Owner deliberately denies business freshness while disconnected. Only
      // a just-confirmed private Owner heartbeat permits a cleanup reconnect.
      if(allowRevoked&&s.admissionStopped&&s.ownerSeenVersion===s.version&&Number.isSafeInteger(s.ownerSeenAt)&&s.ownerSeenAt<=now()&&now()-s.ownerSeenAt<30000)return {status:s.revoked?'REVOKED':'CLEANUP_ONLY',verifiedLiveFresh:false};
      throw error;
    }
    const response=verified(envelope,issuerKey,'r16.fresh.v1');
    check(response.grantId===g.id&&response.role==='native'&&response.peerId===g.peers.native.id&&response.challenge===challenge&&response.issuedAt>=issuedAt&&response.issuedAt<=now()&&now()<response.expiresAt&&response.expiresAt-response.issuedAt<=30000,'STALE_CHALLENGE');
    const previous=store.snapshot().version;check(response.version>=previous,'GRANT_VERSION');
    check(['ACTIVE','REVOKED'].includes(response.status),'GRANT_VERSION');
    store.transact(s=>{s.version=response.version;s.revoked=s.revoked||response.status!=='ACTIVE'||response.version!==g.version;});
    if(store.snapshot().revoked){
      fresh=false;drainBusiness();
      check(response.status==='REVOKED','GRANT_REVOKED');
      // The durable dispatcher fence is checked before every business call and
      // control. Its ACK asserts admission is stopped, never result closure.
      const proof=signed({schema:'r16.revocation-ack.v1',grantId:g.id,version:response.version,role:'native',peerId:g.peers.native.id,newOperationsStopped:true},signingKey);
      if(store.snapshot().revocationAckVersion!==response.version){
        await issuer.acknowledgeRevocation({proof});
        store.transact(s=>{s.revocationAckVersion=response.version;});
      }
      check(allowRevoked,'GRANT_REVOKED');return {status:'REVOKED',verifiedLiveFresh:true};
    }
    for(const projectId of store.snapshot().projects)await freshParticipant(participant(projectId));
    fresh=true;recoveryFence({allowClosedRelease:true});
    if(store.snapshot().admissionStopped||store.snapshot().recoveryOnly){check(allowRevoked,'GRANT_REVOKED');return {status:'CLEANUP_ONLY',verifiedLiveFresh:true};}assertCurrent();return {status:'CONNECTED',verifiedLiveFresh:true};
  }
  async function discovery(operation,data) {
    exact(data,['proof']);check(engine,'AUTHORITY_UNAVAILABLE');
    const p=crown.verifyCall(data.proof,appKey,now());
    check(p.request.action===operation&&p.mode==='execute'&&!p.binding&&!p.workspace&&g.actions.includes(operation),'AUTHORITY_REJECTED');
    check(!contexts.has(p.request_id),'REPLAY_REJECTED');contexts.set(p.request_id,{discovery:true,payload:p});
    try{return await engine.handleCall({command:'CrownCall',proof:data.proof});}finally{contexts.delete(p.request_id);}
  }
  function controlRecord(controlId){
    return store.snapshot().controls.find(x=>x.id===controlId)||store.archived('control-'+digest(controlId));
  }
  function compactControls(){
    const terminal=store.snapshot().controls.filter(c=>['KNOWN','NOT_EXECUTED'].includes(c.status));
    if(terminal.length<=128)return;
    const saved=terminal.slice(0,terminal.length-64),ids=new Set(saved.map(c=>c.id));
    for(const c of saved)store.archive('control-'+digest(c.id),c);
    store.transact(s=>{s.controls=s.controls.filter(c=>!ids.has(c.id));});
  }
  async function control(proof) {
    const c=verified(proof,appKey,'r16.workspace-control.v1');
    exact(c,['schema','id','grantId','channel','operation','data','issuedAt','expiresAt']);id(c.id);
    check(c.grantId===g.id&&c.channel===g.channel&&controlNames.has(c.operation)&&controlWindow(c,now()),'AUTHORITY_REJECTED');
    await waitUntilIssued(c.issuedAt,c.expiresAt,{now});
    const prior=controlRecord(c.id),hash=digest(proof);
    if(prior){check(prior.hash===hash,'OPERATION_CONFLICT');check(prior.status==='KNOWN','RECOVERY_UNRESOLVED');return readResult(resultDirectory,'control-'+c.id);}
    const cleanupOnly=CLEANUP.has(c.operation)||(c.operation==='issuer'&&['fresh','acknowledgeRevocation','closeLease','prepareStatus','heartbeat'].includes(c.data?.operation));
    if(!cleanupOnly){await refresh(false);assertCurrent();}
    check(c.issuedAt<=now()&&now()<c.expiresAt,'CONTROL_EXPIRED');check(!controlRecord(c.id),'REPLAY_REJECTED');
    store.transact(s=>{check(!s.controls.some(x=>x.id===c.id),'REPLAY_REJECTED');s.controls.push({id:c.id,hash,status:'INFLIGHT'});});
    let result;
    const d=c.data;
    if(c.operation==='control_status'){
      exact(d,Object.hasOwn(d,'originalProof')?['id','originalProof']:['id']);id(d.id);
      let original=null;
      if(d.originalProof){
        original=verified(d.originalProof,appKey,'r16.workspace-control.v1');
        exact(original,['schema','id','grantId','channel','operation','data','issuedAt','expiresAt']);
        check(original.id===d.id&&original.id!==c.id&&original.grantId===g.id&&original.channel===g.channel&&original.operation==='allocate','OPERATION_CONFLICT');
        exact(original.data,[]);
        check(Number.isSafeInteger(original.issuedAt)&&Number.isSafeInteger(original.expiresAt)&&original.issuedAt<=now()&&original.expiresAt>original.issuedAt&&original.expiresAt-original.issuedAt<=30000,'AUTHORITY_REJECTED');
      }
      const old=controlRecord(d.id),pending=store.snapshot().pending.filter(x=>x.controlId===d.id);
      if(old&&original)check(old.hash===digest(d.originalProof),'OPERATION_CONFLICT');
      if(old?.status==='NOT_EXECUTED')result={status:'NOT_EXECUTED'};
      else if(!old){
        if(original&&now()>=original.expiresAt&&pending.length===0){
          store.transact(s=>{check(!s.controls.some(x=>x.id===d.id)&&!s.pending.some(x=>x.controlId===d.id),'OPERATION_CONFLICT');s.controls.push({id:d.id,hash:digest(d.originalProof),status:'NOT_EXECUTED'});});
          result={status:'NOT_EXECUTED'};
        }else result={status:'NOT_SEEN'};
      }else{
        try{result={status:'KNOWN',response:readResult(resultDirectory,'control-'+d.id)};}
        catch(error){
          result={status:'UNKNOWN'};
          if(error.code==='ENOENT'&&original&&pending.length===1&&pending[0].status==='ALLOCATED'){
            resolveProject(g.workspace,pending[0].project,{actions:['create_project']});
            const response=signed({schema:'r16.workspace-control-result.v1',id:d.id,operation:'allocate',ok:true,result:{project:pending[0].project,pending:true}},signingKey);
            immutableResult(resultDirectory,'control-'+d.id,response);
            store.transact(s=>{s.controls.find(x=>x.id===d.id).status='KNOWN';});
            result={status:'KNOWN',response};
          }
        }
      }
    }
    else if(c.operation==='describe'){exact(d,['identity']);result=describe(d.identity);}
    else if(c.operation==='resolve'){exact(d,['projectId']);const project=lookup(d.projectId);resolveProject(g.workspace,project);result={project,pending:false};}
    else if(c.operation==='allocate'){
      exact(d,[]);check(g.actions.includes('create_project'),'AUTHORITY_REJECTED');validateWorkspace();
      const pendingId='pending-'+randomUUID(),root=path.join(g.workspace.root,'project-'+randomUUID());
      const project={id:pendingId,workspaceId:g.workspace.id,root};
      store.transact(s=>{s.pending.push({project,status:'CREATING',controlId:c.id});});
      fs.mkdirSync(root,{mode:0o700});const st=fs.lstatSync(root);
      store.transact(s=>{const pending=s.pending.find(x=>x.project.id===pendingId);pending.status='ALLOCATED';pending.dev=st.dev;pending.ino=st.ino;});
      result={project,pending:true};
    }else if(DISCOVERY.has(c.operation))result=await discovery(c.operation,d);
    else if(c.operation==='sign_prepare'){
      exact(d,['request','release']);const r=d.request;
      exact(r,['schema','requestId','grantId','grantVersion','project','channel','versions','actions','issuedAt']);
      check(r.schema==='r16.prepare.v1'&&r.grantId===g.id&&r.grantVersion===g.version&&r.channel===g.channel&&same(r.versions,versions)&&same(d.release,release),'GRANT_BINDING');
      id(r.requestId);check(Number.isSafeInteger(r.issuedAt)&&r.issuedAt<=now()&&now()-r.issuedAt<=30000,'STALE_REQUEST');
      check(Array.isArray(r.actions)&&r.actions.length>0&&r.actions.every(a=>g.actions.includes(a))&&new Set(r.actions).size===r.actions.length,'OPERATION_SCOPE');
      resolveProject(g.workspace,r.project,{actions:r.actions});result=signed(r,signingKey);
    }else if(c.operation==='issuer'){
      exact(d,['operation','params']);check(['fresh','prepare','prepareStatus','activate','acknowledgeRevocation','closeLease','heartbeat'].includes(d.operation)&&typeof issuer[d.operation]==='function','AUTHORITY_REJECTED');
      result=await issuer[d.operation](d.params);
    }
    else {
      id(d.projectId);const entry=participant(d.projectId),p=entry.participant;
      if(c.operation==='prepare'){
        exact(d,['projectId','lease','release']);check(d.lease?.body?.project?.id===d.projectId&&same(d.release,release),'LEASE_BINDING');
        const pending=store.snapshot().pending.find(x=>x.project.id===d.projectId);
        if(pending)check(same(d.lease.body.actions,['create_project']),'OPERATION_SCOPE');
        await freshParticipant(entry);result=p.prepare({lease:d.lease,grant,release:d.release});
      }else if(c.operation==='activate'){exact(d,['projectId','activation']);result=p.activate({activation:d.activation});}
      else if(c.operation==='close'){exact(d,['projectId']);result=p.closeEvidence();}
      else if(c.operation==='drain'){exact(d,['projectId','lease']);check(d.lease?.body?.project?.id===d.projectId,'PROJECT_BINDING');result=p.drain({lease:d.lease});}
      else if(c.operation==='stop'){exact(d,['projectId','lease']);check(d.lease?.body?.project?.id===d.projectId,'PROJECT_BINDING');result=p.stop({lease:d.lease});}
      else if(c.operation==='status'){exact(d,['projectId']);result=p.status();}
      else if(c.operation==='fresh'){
        exact(d,['projectId']);await freshParticipant(entry,{allowRevoked:true});
        const s=p.snapshot();
        result={status:p.status(),activeLeaseHash:s.active?digest(s.active.lease):null,activeGeneration:s.active?.lease.body.generation??0,
          pendingLeaseHash:s.pending?digest(s.pending.lease):null,closingLeaseHash:s.closing?digest(s.closing):null};
      }
      else if(c.operation==='reconcile'){
        exact(d,Object.hasOwn(d,'operation')?['projectId','operationId','operation']:['projectId','operationId']);
        let saved;
        try{saved=readResult(resultDirectory,'operation-'+d.operationId);}
        catch(error){if(error.code!=='ENOENT'||!d.operation)throw error;}
        if(saved){
          check(saved.operation.body.projectId===d.projectId,'PROJECT_BINDING');
          const receipt=p.complete({operationId:d.operationId,outcome:saved.outcome,resultHash:digest(saved.nativeResult)});
          result={nativeResult:saved.nativeResult,receipt};
        }else{
          check(d.operation?.body?.id===d.operationId&&d.operation?.body?.projectId===d.projectId,'PROJECT_BINDING');
          const receipt=p.refuseUndispatched({operation:d.operation});
          check(receipt.body.outcome==='NOT_EXECUTED','RECOVERY_UNRESOLVED');
          const nativeResult={notExecuted:true,operationHash:digest(d.operation)};
          check(digest(nativeResult)===receipt.body.resultHash,'RESULT_CONFLICT');
          immutableResult(resultDirectory,'operation-'+d.operationId,{operation:d.operation,nativeResult,outcome:'NOT_EXECUTED'});
          result={nativeResult,receipt};
        }
      }
    }
    const response=signed({schema:'r16.workspace-control-result.v1',id:c.id,operation:c.operation,ok:true,result},signingKey);
    immutableResult(resultDirectory,'control-'+c.id,response);
    store.transact(s=>{s.controls.find(x=>x.id===c.id).status='KNOWN';});compactControls();return response;
  }
  function signedCallAtIssue(proof) {
    // Decode only a bounded timestamp, then authenticate the complete canonical
    // envelope and shape before any wait. This is not permission to execute.
    check(typeof proof?.payload_b64==='string'&&proof.payload_b64.length<=4*Math.ceil(crown.CALL_MAX_PAYLOAD_BYTES/3),'PROOF_REJECTED');
    let claimed;try{claimed=JSON.parse(Buffer.from(proof.payload_b64,'base64').toString('utf8')).issued_at;}catch{check(false,'PROOF_REJECTED');}
    return crown.verifyCall(proof,appKey,claimed);
  }
  async function call(args) {
    exact(args,['command','operation','proof']);assertCurrent();check(engine,'AUTHORITY_UNAVAILABLE');
    const p=signedCallAtIssue(args.proof),o=verified(args.operation,appKey,'r16.operation.v1');
    exact(o,['schema','id','grantId','projectId','generation','leaseHash','channel','action','payloadHash']);
    check(o.id===p.request_id&&o.payloadHash===digest(p)&&o.action===p.request.action&&o.grantId===g.id&&o.channel===g.channel&&p.mode!=='reconcile','OPERATION_SCOPE');
    const entry=participant(o.projectId),snapshot=entry.participant.snapshot();
    const previous=snapshot.operations.find(x=>x.id===o.id);
    if(!previous){
      const l=snapshot.active?.lease.body;check(l,'NOT_ACTIVE');
      check(o.projectId===l.project.id&&o.generation===l.generation&&o.leaseHash===digest(snapshot.active.lease)&&l.actions.includes(o.action),'OPERATION_SCOPE');
      const target=p.binding?{id:p.binding.projectId,workspaceId:p.binding.workspaceId,root:p.binding.projectRoot}:
        p.request.action==='create_project'?{id:o.projectId,workspaceId:p.workspace?.id,root:p.workspace?.path}:l.project;
      check(same(target,l.project),'PROJECT_BINDING');if(p.request.project_id)check(p.request.project_id===l.project.id,'PROJECT_BINDING');
    }
    // Independent WorkspaceCall has no outer WorkspaceControl timestamp.
    // Preserve strict business not-before by waiting only after signed binding,
    // and rechecking live authority/time before the first durable begin.
    await waitUntilIssued(p.issued_at,p.expires_at,{now});
    crown.verifyCall(args.proof,appKey,now());assertCurrent();
    const decision=entry.participant.begin({operation:args.operation});
    if(decision.decision==='UNKNOWN')return {nativeResult:{...crown.reply(args.proof,p,'unknown'),identity,native_epoch:engine.callStatus().epoch,isolated:false},receipt:null};
    if(decision.decision==='KNOWN'){
      const saved=readResult(resultDirectory,'operation-'+o.id);check(digest(saved.nativeResult)===decision.resultHash,'RESULT_CONFLICT');
      return {nativeResult:saved.nativeResult,receipt:entry.participant.receipt(o.id)};
    }
    check(!contexts.has(p.request_id),'REPLAY_REJECTED');contexts.set(p.request_id,{payload:p,operation:o,entry});
    const work=(async()=>{
      const nativeResult=await engine.handleCall({command:'CrownCall',proof:args.proof});
      if(nativeResult.status!=='verified'){entry.participant.markUnknown(o.id);return {nativeResult,receipt:null};}
      const outcome=nativeResult.fields?.ok===false?'REJECTED':'COMPLETED';
      immutableResult(resultDirectory,'operation-'+o.id,{operation:args.operation,nativeResult,outcome});
      if(p.request.action==='create_project'&&p.mode==='execute'&&nativeResult.fields?.ok===true){
        const actual=lookup(nativeResult.fields.project_id);
        store.transact(s=>{const pending=s.pending.find(x=>x.project.id===o.projectId);check(pending&&actual.root===pending.project.root,'PROJECT_BINDING');pending.status='CREATED';pending.actualProject=actual;});
      }
      const receipt=entry.participant.complete({operationId:o.id,outcome,resultHash:digest(nativeResult)});
      if(p.mode==='execute'&&crown.CALL_WRITES.includes(p.request.action))engine.acknowledgeReceipt({requestId:p.request_id,fieldsHash:crown.digest(nativeResult.fields)});
      return {nativeResult,receipt};
    })();
    active.add(work);try{return await work;}catch(error){entry.participant.markUnknown(o.id);throw error;}finally{active.delete(work);contexts.delete(p.request_id);}
  }
  function physicalSnapshot(projectId){
    const existing=participants.get(projectId);if(existing)return existing.store.snapshot();
    let ps=physicalStores.get(projectId);
    if(!ps){ps=new ProtectedStore({directory:path.join(directory,'project-'+projectId),create:false,now});physicalStores.set(projectId,ps);}
    return ps.snapshot();
  }
  function inspectRetainedHistory(){
    const state=store.snapshot();
    if(inheritedHistory)inspectNativeHistoryBaseline(inheritedHistory,store,grant,versions);
    else check(!initialControls.some(c=>['INFLIGHT','UNKNOWN'].includes(c.status))&&!state.controls.some(c=>!['KNOWN','NOT_EXECUTED'].includes(c.status)),'CURRENT_WORK_UNRESOLVED');
    check(!state.controls.some(c=>c.status==='INFLIGHT')&&state.pending.every(p=>p.status==='CREATED'),'CURRENT_WORK_UNRESOLVED');
    const retained=[];
    for(const projectId of state.projects){
      const snapshot=physicalSnapshot(projectId),initial=initialParticipants.get(projectId)??snapshot;
      check(same(snapshot.grant,grant)&&!initial.operations.some(o=>o.status==='INFLIGHT'),'CURRENT_WORK_UNRESOLVED');
      for(const row of snapshot.operations){
        if(row.status==='KNOWN')continue;
        const pin=HISTORICAL_LOCAL_READS.find(p=>p.projectId===projectId&&p.operationId===row.id);
        check(pin&&row.status==='UNKNOWN'&&row.hash===pin.operationHash&&row.generation===pin.generation&&row.projectId===projectId&&row.outcome===null&&row.resultHash===null,'UNPROVEN_EXECUTION_RISK');
        let operation=(inheritedHistory?historyBrands.get(inheritedHistory).historicalOperations:historicalOperations).find(o=>o?.body?.id===row.id);
        if(!operation){try{operation=readResult(resultDirectory,'operation-'+row.id).operation;}catch(error){if(error.code!=='ENOENT')throw error;}}
        check(operation&&digest(operation)===pin.operationHash,'HISTORICAL_OPERATION_REQUIRED');
        const o=verified(operation,appKey,'r16.operation.v1');
        exact(o,['schema','id','grantId','projectId','generation','leaseHash','channel','action','payloadHash']);
        const lease=snapshot.active?.lease;
        check(lease&&!snapshot.pending&&(!snapshot.closing||same(snapshot.closing,lease))&&digest(lease)===o.leaseHash,'HISTORICAL_LEASE_BINDING');
        const l=verified(lease,issuerKey,'r16.lease.v1');
        exact(l,['schema','phase','grantId','grantVersion','grantHash','project','channel','versions','actions','generation','previousGeneration','issuedAt','expiresAt','renewAt','requestId','releaseHash']);
        check(o.id===pin.operationId&&o.projectId===projectId&&o.generation===pin.generation&&o.grantId===g.id&&o.channel===g.channel&&o.action==='find_symbol'&&
          l.phase==='PREPARED'&&l.grantId===g.id&&l.grantVersion===g.version&&l.grantHash===digest(grant)&&l.project.id===projectId&&l.project.workspaceId===g.workspace.id&&
          l.generation===pin.generation&&l.previousGeneration===l.generation-1&&l.channel===g.channel&&same(l.versions,HISTORICAL_LEASE_VERSIONS)&&
          l.actions.includes(o.action)&&l.actions.every(a=>g.actions.includes(a))&&Number.isSafeInteger(l.issuedAt)&&l.expiresAt===l.issuedAt+LEASE_MS&&l.renewAt===l.expiresAt-RENEW_BEFORE_MS,'HISTORICAL_LEASE_BINDING');
        retained.push({projectId,operationId:row.id,operationHash:row.hash,leaseHash:digest(lease)});
      }
    }
    if(inheritedHistory)check(retained.length===HISTORICAL_LOCAL_READS.length&&HISTORICAL_LOCAL_READS.every(pin=>retained.filter(row=>row.projectId===pin.projectId&&row.operationId===pin.operationId&&row.operationHash===pin.operationHash).length===1),'HISTORY_ORIGINAL_OPERATIONS_DRIFT');
    return retained;
  }
  function releaseStores({signal,deadline=Infinity,monotonicDeadline=Infinity}={}){
    const current=()=>check(!signal?.aborted&&Date.now()<deadline&&performance.now()<monotonicDeadline,'LOCAL_SHUTDOWN_TIMEOUT');current();
    check(closing&&active.size===0&&pendingWork===0&&outerWork.size===0&&(!localShutdownPromise||localResourcesClosed),'RECOVERY_REQUIRED');
    if(storesReleased)return;
    for(const entry of participants.values()){current();entry.store.close();}
    for(const ps of physicalStores.values()){current();ps.close();}current();store.close();storesReleased=true;
  }
  // Explicit LOCAL resource shutdown. Default close()/SIGTERM remain strict.
  // The callback is trusted composition-time observation, never network input,
  // and its return value is not evidence or an authority override.
  function shutdownLocalResources({timeoutMs=15000,signal,deadline=Infinity,monotonicDeadline=Infinity}={}){
    if(localShutdownPromise)return localShutdownPromise;
    check(Number.isSafeInteger(timeoutMs)&&timeoutMs>0&&timeoutMs<=15000,'INVALID_REQUEST');
    check(signal===undefined||signal instanceof AbortSignal,'INVALID_REQUEST');
    deadline=Math.min(deadline,Date.now()+timeoutMs);monotonicDeadline=Math.min(monotonicDeadline,performance.now()+timeoutMs);
    const abort=new AbortController(),combined=signal?AbortSignal.any([signal,abort.signal]):abort.signal;
    const stillCurrent=()=>check(!combined.aborted&&Date.now()<deadline&&performance.now()<monotonicDeadline,'LOCAL_SHUTDOWN_TIMEOUT');stillCurrent();
    closing=true;
    let timer;
    const work=(async()=>{
      store.transact(s=>{s.physicalStop={schema:'r16.native-local-stop.v1',phase:'ADMISSION_CLOSED',globalExecution:'UNPROVEN'};});
      await controlQueue;await Promise.allSettled([...outerWork]);await Promise.allSettled([...active]);stillCurrent();
      check(pendingWork===0&&active.size===0&&contexts.size===0&&outerWork.size===0,'CURRENT_WORK_UNRESOLVED');
      const retained=inspectRetainedHistory();
      check(typeof native.quiesceExecution==='function','LOCAL_EXECUTION_UNPROVEN');
      const local=await native.quiesceExecution({signal:combined,deadline,monotonicDeadline});stillCurrent();
      check(local?.schema==='r16.native-local-execution.v1'&&local.scope==='PROCESS_AND_OWNED_INDEXERS_ONLY'&&local.admissionClosed===true&&
        local.workspaceCalls===0&&local.queuedWriters===0&&local.lifecycleCalls===0&&local.indexers.every(i=>i.children.length===0&&!i.starting&&i.requests===0&&i.pending===0&&i.unconfirmed===0),'LOCAL_EXECUTION_UNPROVEN');
      const observation=Object.freeze({schema:'r16.native-local-quiescence.v1',scope:'LOCAL_ONLY',globalExecution:'UNPROVEN',retainedHistory:clone(retained),inheritedControlUncertainty:inheritedHistory?clone(inheritedHistory):null,local:clone(local)});
      if(beforePhysicalClose)await beforePhysicalClose(observation);stillCurrent();
      if(inheritedHistory)inspectNativeHistoryBaseline(inheritedHistory,store,grant,versions);
      engine?.close();stillCurrent();await native.cleanup({signal:combined,deadline,monotonicDeadline});stillCurrent();
      fresh=false;
      store.transact(s=>{s.admissionStopped=true;s.physicalStop.phase='LOCAL_RESOURCES_CLOSED';});localResourcesClosed=true;
      return Object.freeze({status:'LOCAL_RESOURCES_CLOSED',scope:'LOCAL_ONLY',globalExecution:'UNPROVEN',firstStopProof:'NOT_PROVEN',retainedHistory:clone(retained),inheritedControlUncertainty:inheritedHistory?clone(inheritedHistory):null});
    })();
    localShutdownPromise=Promise.race([work,new Promise((_,reject)=>{timer=setTimeout(()=>{abort.abort();reject(Object.assign(Error('LOCAL_SHUTDOWN_TIMEOUT'),{code:'LOCAL_SHUTDOWN_TIMEOUT'}));},Math.max(1,Math.min(timeoutMs,deadline-Date.now(),monotonicDeadline-performance.now())));})]).finally(()=>clearTimeout(timer));
    return localShutdownPromise;
  }
  return Object.freeze({
    refresh(...args){
      // External reconnect/heartbeat refresh must not replace a participant's
      // single pending challenge while a control is preparing or activating.
      check(!closing,'AUTHORITY_REJECTED');
      return queueWork(()=>{check(!closing,'AUTHORITY_REJECTED');return refresh(...args);});
    },
    suspendBusiness(){
      // Transport uncertainty fences new calls without inventing an Owner
      // disconnect or making an otherwise unexecuted pending lease terminal.
      fresh=false;if(!closing)store.transact(s=>{s.admissionStopped=true;});
      return {businessStopped:true};
    },
    admissionStatus(){const s=store.snapshot();return {revoked:s.revoked,version:s.version,admissionStopped:!!s.admissionStopped};},
    noteOwnerStatus(response){
      check(response&&typeof response.connectRequested==='boolean'&&typeof response.revoked==='boolean'&&Number.isSafeInteger(response.grantVersion)&&response.grantVersion===store.snapshot().version,'GRANT_VERSION');
      store.transact(s=>{s.ownerSeenAt=now();s.ownerSeenVersion=response.grantVersion;});
    },
    setConnectionRequested(requested){
      check(typeof requested==='boolean','INVALID_REQUEST');
      check(!closing&&!store.snapshot().physicalStop,'PHYSICAL_STOP_FENCED');
      store.transact(s=>{s.admissionStopped=!!s.recoveryOnly||!requested||s.revoked;});
      if(!requested||store.snapshot().revoked)drainBusiness();
      return {businessStopped:store.snapshot().admissionStopped};
    },
    prepareConnection(remote){
      check(!closing,'RECOVERY_REQUIRED');
      const work=(async()=>{await controlQueue;await Promise.allSettled([...active]);check(!closing,'RECOVERY_REQUIRED');
      const recovering=recoveryFence();
      const cleanup=recovering||store.snapshot().revoked||store.snapshot().admissionStopped;
      if(!cleanup)assertCurrent();
      const snapshots=[...participants.entries()].map(([projectId,entry])=>({projectId,state:entry.participant.snapshot(),status:entry.participant.status()}));
      check(cleanup||snapshots.every(x=>x.status.unresolved.length===0),'RECOVERY_UNRESOLVED');
      check(remote.peerId===g.peers.native.id&&remote.grantId===g.id&&remote.channel===g.channel&&Number.isSafeInteger(remote.generation)&&remote.generation>=0,'CONNECTION_STALE');
      const previousDrainHash=digest(snapshots.map(x=>({projectId:x.projectId,operations:x.state.operations})).sort((a,b)=>a.projectId.localeCompare(b.projectId)));
      return store.transact(s=>{
        const old=s.connection;
        if(old&&!old.closed)check(Number.isSafeInteger(old.pid)&&typeof old.start==='string'&&processStart(old.pid)!==old.start,'RECOVERY_REQUIRED');
        check(old?remote.generation<=old.generation:remote.generation===0&&s.projects.length===0,'CONNECTION_STALE');
        const generation=Math.max(old?.generation??0,remote.generation)+1;
        s.connection={generation,origin:null,pid:process.pid,start:processStart(process.pid),closed:false,previousDrainHash};
        return {generation,previousGeneration:remote.generation,previousOrigin:remote.origin,oldLocalSocketClosed:true,previousDrainHash};
      });})();
      outerWork.add(work);return work.finally(()=>outerWork.delete(work));
    },
    connectionClosed(generation){
      check(!storesReleased,'PHYSICAL_STOP_FENCED');
      store.transact(s=>{if(s.connection?.generation===generation){s.connection.closed=true;}});
    },
    connectedIdentity(value,generation){
      check(!closing&&!store.snapshot().physicalStop,'PHYSICAL_STOP_FENCED');
      crown.identityCheck(value);
      const recovering=recoveryFence();
      const cleanup=recovering||store.snapshot().revoked||store.snapshot().admissionStopped;
      if(!cleanup)assertCurrent();
      if(generation!==undefined)store.transact(s=>{check(s.connection?.generation===generation&&!s.connection.closed,'CONNECTION_STALE');s.connection.origin=value.originId;});
      transportIdentity=clone(value);return cleanup?{cleanupOnly:true}:describe(value);
    },
    heartbeatProjections(){
      const values=[...participants.entries()].sort(([a],[b])=>a.localeCompare(b)).map(([projectId,entry])=>{
        const s=entry.participant.snapshot(),status=entry.participant.status(),lease=s.pending?.lease??s.closing??s.active?.lease;
        return {phase:status.available?'ACTIVE':lease?'DRAINING':'CLOSED',projectId,generation:lease?.body?.generation??status.generation,
          leaseHash:lease?digest(lease):'',unresolved:status.unresolved.length>0,credentialValid:true};
      });
      return values.length?values:[{phase:'CLOSED',projectId:'',generation:0,leaseHash:'',unresolved:false,credentialValid:true}];
    },
    async handle(args){
      check(!closing,'AUTHORITY_REJECTED');
      if(args?.command==='WorkspaceCall'){
        // Wait for freshness/control work once, then revalidate inside call.
        // Keep the full business call ahead of later refreshes; never replay it.
        return queueWork(()=>{check(!closing,'AUTHORITY_REJECTED');return call(args);});
      }
      exact(args,['command','proof']);check(args.command==='WorkspaceControl','AUTHORITY_REJECTED');
      return queueWork(()=>{check(!closing,'AUTHORITY_REJECTED');return control(args.proof);});
    },
    shutdownLocalResources,
    releaseStores,
    async close({retainTransport=false,signal,deadline=Infinity,monotonicDeadline=Infinity}={}){
      check(!localShutdownPromise,'PHYSICAL_STOP_FENCED');
      const boundary={signal,deadline,monotonicDeadline};
      const current=()=>check(!signal?.aborted&&Date.now()<deadline&&performance.now()<monotonicDeadline,'LOCAL_SHUTDOWN_TIMEOUT');current();
      closing=true;
      await controlQueue;current();await Promise.allSettled([...active]);current();
      fresh=false;
      for(const entry of participants.values()){
        current();const snapshot=entry.participant.snapshot(),lease=snapshot.pending?.lease??snapshot.active?.lease??snapshot.closing;
        if(lease)entry.participant.stop({lease});entry.participant.disconnect();check(entry.participant.status().unresolved.length===0,'RECOVERY_UNRESOLVED');
      }
      current();engine?.close();current();await native.cleanup(boundary);current();
      for(const entry of participants.values()){current();entry.store.close();}if(!retainTransport){current();store.close();}
    }
  });
}
