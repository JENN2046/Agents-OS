import {readSystemdCredential} from '../src/systemd-credentials.mjs';
import fs from 'node:fs';
import path from 'node:path';
import {createPrivateKey,createHash} from 'node:crypto';
import {createRequire,Module} from 'node:module';
import {spawnSync} from 'node:child_process';
import {ProtectedStore,signed,verified,exportPublicKey,digest} from '../src/lease-core.mjs';
import {createHeadlessHost,acquireProcessLease,reportStopPhase} from './headless-host.mjs';
import {createRecoverableConnector} from './connection-v2.mjs';
import {createWorkspaceDispatcher} from './workspace-dispatcher.mjs';
import {createIssuerClient,checkProtectedRootFile} from './issuer-client.mjs';

const check=(ok,code)=>{if(!ok)throw Object.assign(new Error(code),{code});};
function credential(name){check(name==='native-signing-key','CREDENTIAL_UNAVAILABLE');return readSystemdCredential('r16-native.service',name,16383);}
function guardCjs(directory,manifest){
 for(const extension of ['.js','.json','.node']){
  const previous=Module._extensions[extension];
  Module._extensions[extension]=(module,filename)=>{
   const relative=path.relative(directory,filename).split(path.sep).join('/'),expected=manifest.files[relative];
   check(expected&&fs.realpathSync(filename)===filename,'RELEASE_NOT_APPROVED');
   const stat=fs.lstatSync(filename);check(stat.isFile()&&stat.uid===0&&(stat.mode&0o022)===0&&stat.nlink===1,'RELEASE_NOT_APPROVED');
   check(createHash('sha256').update(fs.readFileSync(filename)).digest('hex')===expected,'RELEASE_NOT_APPROVED');previous(module,filename);
  };
 }
}

// A disconnected Owner rejects business freshness but still answers heartbeat.
// Keep the cleanup transport until issuer projects are closed; revocation ACKs
// confirm the admission fence and do not themselves mean results are resolved.
export async function synchronizeOwnerAdmission({dispatcher,issuer,report}){
 let verifiedLiveFresh=false;
 try{verifiedLiveFresh=(await dispatcher.refresh(false,{allowRevoked:true})).verifiedLiveFresh===true;}
 catch{/* A transport/freshness failure is not an Owner disconnect. */}
 if(!verifiedLiveFresh)dispatcher.suspendBusiness();
 const response=await issuer.heartbeat(report());
 if(response.revoked&&!dispatcher.admissionStatus().revoked)await dispatcher.refresh(false,{allowRevoked:true});
 dispatcher.noteOwnerStatus(response);
 if(response.connectRequested!==true||response.revoked)dispatcher.setConnectionRequested(false);
 else if(verifiedLiveFresh)dispatcher.setConnectionRequested(true);
 return {stop:response.connectRequested===false&&response.closeComplete===true&&(!response.revoked||response.revocationComplete===true)};
}

// Called only by the small root-protected launcher after every release file is
// checked against an Owner-approved signed release manifest.
export async function startNativeService({config,publicConfig,manifest,directory}){
 check(config.schema==='r16.native-host.v1'&&manifest.role==='native','CONFIGURATION_UNSAFE');
 check(process.geteuid()===1000,'SERVICE_IDENTITY');
 check(publicConfig.grant,'OWNER_SETUP_REQUIRED');
 const grant=verified(publicConfig.grant,publicConfig.issuerPublicKey,'r16.workspace.v1');
 check(grant.channel===publicConfig.channel&&/^[A-Za-z0-9_-]{1,128}$/.test(grant.id),'GRANT_BINDING');
 const privateBytes=credential('native-signing-key');let signingKey;
 try{signingKey=createPrivateKey({key:privateBytes,format:'der',type:'pkcs8'});}finally{privateBytes.fill(0);}
 check(exportPublicKey(signingKey)===grant.peers.native.publicKey,'PAIRING_FAILED');
 // An installer-created grant directory is required. Missing state is never
 // silently recreated after a crash or tampering.
 const stateDirectory='/var/lib/r16-native/grants/'+grant.id+'/dispatcher';
 checkProtectedRootFile('/etc/r16/native-ledgers.json');
 const ledgerRegistry=JSON.parse(fs.readFileSync('/etc/r16/native-ledgers.json','utf8'));
 const ledger=ledgerRegistry.grants?.find(r=>r.grantId===grant.id),ledgerStat=fs.lstatSync(stateDirectory);
 check(ledgerRegistry.schema==='r16.native-ledgers.v1'&&ledger?.status==='READY'&&ledger.grantHash===digest(publicConfig.grant)&&ledger.directory===stateDirectory&&ledgerStat.dev===ledger.dev&&ledgerStat.ino===ledger.ino,'STATE_UNAVAILABLE');
 const lease=acquireProcessLease('/var/lib/r16-native');
 let dispatcher,host,heartbeatTimer,sessionTimer,stopping=false;
 try{
  guardCjs(directory,manifest);
  // Linter config resolution starts at the reviewed Native dependency root.
  // This is a fixed protected release path, never a caller-selected project.
  const nativeRoot=path.join(directory,'native/upstream'),nativeRootStat=fs.lstatSync(nativeRoot);
  check(fs.realpathSync(nativeRoot)===nativeRoot&&nativeRootStat.isDirectory()&&nativeRootStat.uid===0&&(nativeRootStat.mode&0o022)===0&&config.nativeModule.startsWith('native/upstream/')&&manifest.files[config.nativeModule],'RELEASE_NOT_APPROVED');
  process.chdir(nativeRoot);
  const require=createRequire(import.meta.url);
  const load=relative=>{check(typeof relative==='string'&&manifest.files[relative],'RELEASE_NOT_APPROVED');return require(path.join(directory,relative));};
  const native=load(config.nativeModule),crown=load(config.crownModule),WebSocket=load(config.websocketModule);
  const issuer=createIssuerClient({signingKey,peerId:grant.peers.native.id});
  const store=new ProtectedStore({directory:stateDirectory,create:false});
  check(process.env.VCP_CROWN_ENABLED!=='true','LEGACY_ENVIRONMENT_PRESENT');
  native.initialize({dbPath:config.databasePath,workspaceService:{list:()=>[{id:grant.workspace.id,alias:config.workspaceAlias,path:grant.workspace.root,enabled:true}],getActiveWorkspaceId:()=>grant.workspace.id},config:{ALLOWED_DIRECTORIES:'',AST_INDEX_ENABLED:false},logger:{log(){},warn(){},error(){}}});
  dispatcher=createWorkspaceDispatcher({store,directory:stateDirectory,native,crown,grant:publicConfig.grant,release:publicConfig.release,versions:publicConfig.versions,
   signingKey,issuerKey:publicConfig.issuerPublicKey,releaseKey:publicConfig.releasePublicKey,issuer,workspaceAlias:config.workspaceAlias,databasePath:config.databasePath});
  const stopReporter=row=>process.stderr.write('R16_NATIVE_STOP '+JSON.stringify(row)+'\n');
  host=createHeadlessHost({port:dispatcher,manifest:config.toolManifest,serverName:'R16 Native',
   connect:createRecoverableConnector({WebSocket,baseUrl:config.cloudBaseUrl,signingKey,peerId:grant.peers.native.id,grantId:grant.id,channel:grant.channel,nativeVersion:publicConfig.versions.native,
     bridgePublicKey:grant.peers.bridge.publicKey,bridgeId:grant.peers.bridge.id,prepareConnection:status=>dispatcher.prepareConnection(status),onClosed:generation=>dispatcher.connectionClosed(generation)}),
   acquireLease:async()=>lease,onState:()=>{},onStopPhase:stopReporter});
  function heartbeatReport(closed=false,finalVersion=grant.version){
   const projections=closed?[]:dispatcher.heartbeatProjections().filter(p=>p.projectId),issuedAt=Date.now();
   return {report:signed({schema:'r16.participant-heartbeat.v1',role:'native',peerId:grant.peers.native.id,grantId:grant.id,grantVersion:closed?finalVersion:dispatcher.admissionStatus().version||grant.version,issuedAt,expiresAt:issuedAt+30000,
    ready:!closed&&!dispatcher.admissionStatus().revoked&&!dispatcher.admissionStatus().admissionStopped&&host.state==='可用',credentialValid:closed||host.state!=='凭据失效',unresolved:projections.some(p=>p.unresolved),
    projects:projections.map(({projectId,generation,leaseHash,phase})=>({projectId,generation,leaseHash,phase}))},signingKey)};
  }
  async function stop(){
   if(stopping)return;stopping=true;clearInterval(heartbeatTimer);clearInterval(sessionTimer);
   let phase='RUNNER_VERSION';
   try{reportStopPhase(stopReporter,phase,'BEGIN');const finalVersion=dispatcher.admissionStatus().version;reportStopPhase(stopReporter,phase,'DONE');
    phase='RUNNER_HOST_STOP';reportStopPhase(stopReporter,phase,'BEGIN');await host.stop();reportStopPhase(stopReporter,phase,'DONE');
    phase='RUNNER_FINAL_HEARTBEAT';reportStopPhase(stopReporter,phase,'BEGIN');await issuer.heartbeat(heartbeatReport(true,finalVersion));reportStopPhase(stopReporter,phase,'DONE');}
   catch(error){reportStopPhase(stopReporter,phase,'FAILED',error);process.stderr.write('R16_NATIVE_RECOVERY_REQUIRED; details suppressed.\n');process.exitCode=1;}
  }
  process.once('SIGTERM',()=>void stop());process.once('SIGINT',()=>void stop());
  let initial;
  try{initial=await synchronizeOwnerAdmission({dispatcher,issuer,report:heartbeatReport});}
  catch{dispatcher.suspendBusiness();}
  await host.start();
  if(initial?.stop){await stop();return host;}
  let heartbeatBusy=false;
  heartbeatTimer=setInterval(async()=>{
   if(heartbeatBusy||stopping)return;heartbeatBusy=true;
   try{const response=await synchronizeOwnerAdmission({dispatcher,issuer,report:heartbeatReport});if(response.stop)await stop();}
   catch{if(!stopping)dispatcher.suspendBusiness();/* No raw transport or provider responses are logged. */}finally{heartbeatBusy=false;}
  },10000);
  const checker=path.join(directory,config.graphicalSessionCheck);check(manifest.files[config.graphicalSessionCheck],'RELEASE_NOT_APPROVED');
  sessionTimer=setInterval(()=>{
   if(stopping)return;const result=spawnSync('/usr/bin/python3',['-I',checker],{stdio:'ignore',timeout:5000,env:{PATH:'/usr/bin:/bin'}});
   if(result.status!==0)void stop();
  },10000);
  return host;
 }catch(error){
  // Once the native dispatcher exists it owns shutdown and unknown-state
  // preservation. Never release the writer lease after uncertain initialization.
  if(dispatcher){try{await dispatcher.close();lease.release();}catch{}}
  throw error;
 }
}