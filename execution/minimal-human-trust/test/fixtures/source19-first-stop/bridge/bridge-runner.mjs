import {readSystemdCredential} from '../src/systemd-credentials.mjs';
import fs from 'node:fs';
import path from 'node:path';
import http from 'node:http';
import {createPrivateKey} from 'node:crypto';
import {createRequire} from 'node:module';
import {pathToFileURL} from 'node:url';
import {ProtectedStore,verified,exportPublicKey} from '../src/lease-core.mjs';
import {createWorkspaceBridge} from './workspace-private-router.mjs';
import {createNativeGateway} from '../host/native-gateway.mjs';
const check=x=>{if(!x)throw Error('R16_BRIDGE_START_REFUSED');};
function credential(){return readSystemdCredential('r16-bridge.service','bridge-signing-key',16383);}
export async function startBridgeService({config,publicConfig,manifest,directory}){
 check(config.schema==='r16.bridge-host.v1'&&manifest.role==='bridge'&&config.host==='127.0.0.1'&&config.port===6016&&process.geteuid()===1000);
 const grant=verified(publicConfig.grant,publicConfig.issuerPublicKey,'r16.workspace.v1'),bytes=credential();let signingKey;try{signingKey=createPrivateKey({key:bytes,format:'der',type:'pkcs8'});}finally{bytes.fill(0);}check(exportPublicKey(signingKey)===grant.peers.bridge.publicKey);
 const require=createRequire(import.meta.url);check(manifest.files[config.websocketModule]&&manifest.files[config.crownModule]);const WebSocket=require(path.join(directory,config.websocketModule));const crown=require(path.join(directory,config.crownModule));
 const storeDir='/var/lib/r16-bridge/grants/'+grant.id,store=new ProtectedStore({directory:storeDir+'/bridge',create:false}),gatewayStore=new ProtectedStore({directory:storeDir+'/gateway',create:false});
 let bridge;const server=http.createServer(async(req,res)=>{
  res.setHeader('content-type','application/json');
  if(req.method!=='POST'||req.url!=='/workspace/exchange'||!['127.0.0.1','::1','::ffff:127.0.0.1'].includes(req.socket.remoteAddress)){res.writeHead(404);res.end('{"status":"UNAVAILABLE"}');return;}
  try{let total=0;const chunks=[];for await(const c of req){total+=c.length;check(total<=2*1024*1024);chunks.push(c);}const value=JSON.parse(Buffer.concat(chunks));check(value&&Object.keys(value).sort().join(',')==='payload,route');const result=await bridge.exchange(value);res.end(JSON.stringify(result));}
  catch{res.writeHead(503);res.end('{"status":"WORKSPACE_UNAVAILABLE"}');}
 });
 const gateway=createNativeGateway({httpServer:server,WebSocketServer:WebSocket.WebSocketServer,store:gatewayStore,grant:publicConfig.grant,bridgeSigningKey:signingKey,versions:publicConfig.versions});
 bridge=createWorkspaceBridge({store,directory:storeDir+'/bridge',pluginManager:gateway.pluginManager,wss:gateway,crown,grant:publicConfig.grant,release:publicConfig.release,versions:publicConfig.versions,signingKey,issuerKey:publicConfig.issuerPublicKey,releaseKey:publicConfig.releasePublicKey,runtimeFiles:Object.fromEntries(Object.keys(manifest.files).map(name=>[name,path.join(directory,name)])),runtimeEntry:manifest.entry});
 await new Promise((resolve,reject)=>{server.once('error',reject);server.listen(6016,'127.0.0.1',resolve);});
 let stopping=false;async function stop(){if(stopping)return;stopping=true;try{await bridge.close();await gateway.close();await new Promise((resolve,reject)=>server.close(e=>e?reject(e):resolve()));}catch{process.stderr.write('R16_BRIDGE_RECOVERY_REQUIRED; details suppressed.\n');process.exitCode=1;}}
 process.once('SIGTERM',()=>void stop());process.once('SIGINT',()=>void stop());return {bridge,gateway,server,stop};
}