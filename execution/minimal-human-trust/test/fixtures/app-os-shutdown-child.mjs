// Local disposable fixture: actual App host/runner, signed synthetic records,
// real HTTP and SIGTERM. No execution engine, production credentials or RPC.
import fs from 'node:fs';
import path from 'node:path';
import http from 'node:http';
import {generateKeyPairSync,createHash,createPrivateKey} from 'node:crypto';
import {pathToFileURL} from 'node:url';
const [root,mode,crownDirectory='']=process.argv.slice(2);
const core=await import(pathToFileURL(root+'/src/lease-core.mjs'));
const {ProtectedStore,participantInitialState,signed,digest,exportPublicKey,ACTIONS}=core;
const {createWorkspaceHost,appHostInitialState}=await import(pathToFileURL(root+'/app/workspace-host.mjs'));
const {createAppShutdown}=await import(pathToFileURL(root+'/app/app-runner.mjs'));
const materialFile=root+'/synthetic-test-keys.json',reopening=fs.existsSync(materialFile);
const saved=reopening?JSON.parse(fs.readFileSync(materialFile)):null;
const keys=saved?Object.fromEntries(Object.entries(saved).map(([r,b])=>[r,createPrivateKey({key:Buffer.from(b,'base64'),format:'der',type:'pkcs8'})])):Object.fromEntries(['issuer','release','app','bridge','native'].map(r=>[r,generateKeyPairSync('ed25519').privateKey]));
if(!saved)fs.writeFileSync(materialFile,JSON.stringify(Object.fromEntries(Object.entries(keys).map(([r,k])=>[r,k.export({format:'der',type:'pkcs8'}).toString('base64')]))),{mode:0o600});
const now=Date.now(),peers=Object.fromEntries(['app','bridge','native'].map(r=>[r,{id:'isolated-'+r,publicKey:exportPublicKey(keys[r])}]));
const stat=fs.statSync(root),workspace={id:'isolated-ws',root,dev:stat.dev,ino:stat.ino};
const grant=saved?JSON.parse(fs.readFileSync(root+'/synthetic-public.json')).grant:signed({schema:'r16.workspace.v1',id:'isolated-grant',version:1,createdAt:now-10000,workspace,actions:ACTIONS,channel:'main',peers},keys.issuer);
const versions=Object.fromEntries(['app','bridge','native'].map(r=>[r,digest('isolated-'+r)]));
const release=saved?JSON.parse(fs.readFileSync(root+'/synthetic-public.json')).release:signed({schema:'r16.release.v1',id:'isolated-r15',issuedAt:now-10000,notAfter:now+86400000,formats:['r16.workspace.v1'],versions,actions:ACTIONS,permissionVersion:1},keys.release);
if(!saved)fs.writeFileSync(root+'/synthetic-public.json',JSON.stringify({grant,release}),{mode:0o600});
const initial=appHostInitialState(),originals=[];
const store=new ProtectedStore({directory:root+'/host',create:!reopening,initial});
for(const [id,generation,operationId]of [['p2vox',30,'c434da49-055a-43dc-a3e3-695cce137909'],['pmog2',38,'d0364f8b-3a68-4ca2-a396-7953b29cee4c']]){
 if(reopening){originals.push({id,operationId});continue;}
 const project={id,workspaceId:workspace.id,root:root+'/'+id};fs.mkdirSync(project.root);
 const lease=signed({schema:'r16.lease.v1',phase:'PREPARED',grantId:grant.body.id,grantVersion:1,grantHash:digest(grant),project,channel:'main',versions,actions:ACTIONS,generation,previousGeneration:generation-1,issuedAt:now-1000,expiresAt:now-1000+3600000,renewAt:now-1000+2700000,requestId:'isolated-'+id,releaseHash:digest(release)},keys.issuer);
 const operation=signed({schema:'r16.operation.v1',id:operationId,grantId:grant.body.id,projectId:id,generation,leaseHash:digest(lease),channel:'main',action:'get_project',payloadHash:digest('isolated-payload-'+id)},keys.app);
 const s=participantInitialState('app');s.grant=grant;s.version=1;s.active={lease,activation:signed({schema:'r16.activation.v1',grantId:grant.body.id,grantVersion:1,projectId:id,generation,leaseHash:digest(lease),activatedAt:now-900},keys.issuer)};s.closing=lease;s.lastGeneration=generation;
 s.operations=[{id:operationId,hash:digest(operation),projectId:id,generation,status:'UNKNOWN',outcome:null,resultHash:null}];
 const file=root+'/host/project-'+id;const store=new ProtectedStore({directory:file,create:true,initial:s});store.close();
 initial.projects.push({project,transition:null,retirement:null,initialized:true});initial.operations.push({id:operationId,projectId:id,operation,status:'UNKNOWN'});originals.push({id,operationId});
}
if(!reopening)store.transact(s=>Object.assign(s,initial));
let captured,executorClosed=0,releaseFlight,releaseHold;const calls=[];
let crown={verifyCall(){throw Error('EXECUTION_ENGINE_DISABLED');}},factory=options=>{captured=options;const execute=()=>{throw Error('EXECUTION_ENGINE_DISABLED');};execute.close=()=>{executorClosed++;if(mode==='resource-failure')throw Error('SYNTHETIC_RESOURCE_CLOSE_FAILURE');};return execute;};
if(crownDirectory){
 crown=await import(pathToFileURL(crownDirectory+'/project-forge-crown-transport.mjs'));
 const {createCrownExecutor}=await import(pathToFileURL(crownDirectory+'/project-forge-crown-executor.mjs'));
 factory=options=>{captured=options;const execute=createCrownExecutor(options),close=execute.close;execute.close=()=>{close();executorClosed++;if(mode==='resource-failure')throw Error('SYNTHETIC_RESOURCE_CLOSE_FAILURE');};return execute;};
}
const host=createWorkspaceHost({store,directory:root+'/host',grant,release,versions,signingKey:keys.app,issuerKey:exportPublicKey(keys.issuer),releaseKey:exportPublicKey(keys.release),channelCapability:Buffer.alloc(32,65),crown,createCrownExecutor:factory,
 exchange:async(target,payload)=>{
  const op=target==='bridge'?payload.operation:payload.proof.body.operation;calls.push(op);
  if(op==='allocate'){
   process.send({event:'flight'});await new Promise(resolve=>{releaseFlight=resolve;});
   throw Object.assign(Error('NATIVE_OFFLINE'),{code:'NATIVE_OFFLINE'});
  }
  if(target==='bridge'&&op==='drain')return {draining:true};
  if(target==='native'&&['drain','reconcile'].includes(op))return signed({schema:'r16.workspace-control-result.v1',id:payload.proof.body.id,operation:op,ok:true,result:{}},keys.native);
  throw Error('UNEXPECTED_FIXTURE_EXCHANGE_'+op);
 }});
host.start();let duplicateStartRejected=false;try{host.start();}catch{duplicateStartRejected=true;}let closeError=null;
if(mode==='business-rejection'){try{await host.close();}catch(e){closeError=e.code;}}
function states(){return Object.fromEntries(['host/state.json',...originals.map(x=>'host/project-'+x.id+'/state.json')].map(n=>[n,fs.readFileSync(root+'/'+n).toString('base64')]));}
const before=states(),callsBefore=calls.length;
const server=http.createServer(async(req,res)=>{
 if(req.url==='/hold'){process.send({event:'hold'});await new Promise(resolve=>{releaseHold=resolve;});res.end('drained');return;}
 if(req.url==='/work'){try{await captured.transport.allocateProject({request:{action:'create_project'},workspace:{id:workspace.id,path:workspace.root}});res.end('unexpected');}catch(e){res.statusCode=503;res.end(e.code||'FAILED');}return;}
 res.end('up');
});
await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
const stop=createAppShutdown({host,listener:server});let reported=false;
function report(){if(reported)return;reported=true;stop().then(result=>{
 const after=states();process.send({event:'closed',result,before,after,calls:calls.slice(callsBefore),closeError,executorClosed,duplicateStartRejected,locks:fs.readdirSync(root+'/host').filter(n=>n==='.lock'),allocation:JSON.parse(Buffer.from(after['host/state.json'],'base64')).data.allocations});process.disconnect();
});}
process.on('SIGTERM',report);process.on('SIGINT',report);
process.on('message',async message=>{
 if(message==='release'){releaseFlight?.();releaseHold?.();}
 if(message==='late'){try{await captured.transport.allocateProject({request:{action:'create_project'},workspace:{id:workspace.id,path:workspace.root}});process.send({event:'late',allowed:true});}catch(e){process.send({event:'late',code:e.code});}}
 if(message==='stop'){const a=stop(),b=stop();process.send({event:'samePromise',same:a===b});report();}
});
process.send({event:'ready',port:server.address().port,closeError,before,realCrown:!!crownDirectory});
