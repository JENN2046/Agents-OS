import {readSystemdCredential} from '../src/systemd-credentials.mjs';
import fs from 'node:fs';
import path from 'node:path';
import {createPrivateKey} from 'node:crypto';
import {parseEnv} from 'node:util';
import {pathToFileURL} from 'node:url';
import {ProtectedStore,verified,exportPublicKey} from '../src/lease-core.mjs';
import {createWorkspaceHost,createWorkspaceClient} from './workspace-host.mjs';
const check=x=>{if(!x)throw Error('R16_APP_START_REFUSED');};
function credential(name){check(['app-signing-key','channel-capability','legacy-app-settings'].includes(name));return readSystemdCredential('r16-app.service',name,65536);}
// This reviewed host is installed only as the system r16-app.service.
// A legacy user-service setting cannot select another upstream manager here.
export function createSystemAppConfig(createAppConfig,legacy){
 return createAppConfig({...legacy,HOST:'127.0.0.1',PORT:'3010',VCP_UPSTREAM_SYSTEMD_SCOPE:'system',VCP_UPSTREAM_RUNTIME_ROOT:'/mnt/datadisk0/apps/AGENTS_OS_Workspace/runtime/VCPToolBox/releases/2835f6a4-r16-g7-production-recovery-r1',VCP_CROWN_ENABLED:'false',VCP_CROWN_ADMISSION_FILE:'',VCP_CROWN_MATERIAL_FILE:''});
}
export async function startAppService({config,publicConfig,manifest,directory}){
 check(manifest.role==='app'&&config.schema==='r16.app-host.v1'&&publicConfig.grant);
 const grant=verified(publicConfig.grant,publicConfig.issuerPublicKey,'r16.workspace.v1');
 const privateBytes=credential('app-signing-key');let signingKey;try{signingKey=createPrivateKey({key:privateBytes,format:'der',type:'pkcs8'});}finally{privateBytes.fill(0);}
 check(exportPublicKey(signingKey)===grant.peers.app.publicKey);
 const cap=credential('channel-capability'),legacyBytes=credential('legacy-app-settings');let legacy;
 try{legacy=parseEnv(legacyBytes.toString('utf8'));}finally{legacyBytes.fill(0);}
 check(config.host==='127.0.0.1'&&config.port===3010&&config.bridgeUrl==='http://127.0.0.1:6016/workspace/exchange');
 const load=async name=>{check(typeof name==='string'&&manifest.files[name]);return import(pathToFileURL(path.join(directory,name)));};
 const {createAppConfig}=await load(config.configModule),{createHttpApp}=await load(config.serverModule),{VcpClient}=await load(config.clientModule),crown=await load(config.crownModule),{createCrownExecutor}=await load(config.executorModule);
 const appConfig=createSystemAppConfig(createAppConfig,legacy);legacy=null;
 const vcpClient=new VcpClient({baseUrl:appConfig.vcpBaseUrl,apiKey:appConfig.vcpApiKey,timeoutMs:appConfig.vcpTimeoutMs,chatPath:appConfig.vcpChatPath,defaultModel:appConfig.vcpDefaultModel,systemPrompt:appConfig.vcpSystemPrompt});
 const stateDirectory='/var/lib/r16-app/grants/'+grant.id+'/host';
 const store=new ProtectedStore({directory:stateDirectory,create:false});
 const exchange=createWorkspaceClient({url:config.bridgeUrl,grant:publicConfig.grant,signingKey});
 const host=createWorkspaceHost({store,directory:stateDirectory,grant:publicConfig.grant,release:publicConfig.release,versions:publicConfig.versions,signingKey,issuerKey:publicConfig.issuerPublicKey,releaseKey:publicConfig.releasePublicKey,channelCapability:cap,crown,createCrownExecutor,exchange});cap.fill(0);
 const app=createHttpApp({appConfig,vcpClient,runtimeDependencies:host.runtimeDependencies,sanitizeMcpErrors:true});
 const listener=await new Promise((resolve,reject)=>{const server=app.listen(3010,'127.0.0.1',()=>resolve(server));server.once('error',reject);});
 host.start();const stop=createAppShutdown({host,listener});
 return {host,listener,stop};
}
// One physical shutdown flight: block host admission synchronously, stop HTTP
// accepts immediately, drain existing work, and close both resources even if
// either one fails. Business close/retirement is a separate signed protocol.
export function createAppShutdown({host,listener,signals=process,onError=()=>{process.stderr.write('R16_APP_RECOVERY_REQUIRED; details suppressed.\n');process.exitCode=1;}}){
 let stopping=null;
 const signal=()=>{void stop();};
 function stop(){
  if(stopping)return stopping;
  let hostWork;try{hostWork=Promise.resolve(host.shutdown());}catch(error){hostWork=Promise.reject(error);}
  const httpWork=new Promise((resolve,reject)=>{try{listener.close(error=>error?reject(error):resolve());}catch(error){reject(error);}});
  stopping=Promise.allSettled([hostWork,httpWork]).then(results=>{
   signals.removeListener('SIGTERM',signal);signals.removeListener('SIGINT',signal);
   const failed=results.some(r=>r.status==='rejected');if(failed)onError();
   return {status:failed?'APP_OS_CLOSE_FAILED':'APP_OS_CLOSED',businessClosed:false};
  });return stopping;
 }
 signals.on('SIGTERM',signal);signals.on('SIGINT',signal);return stop;
}