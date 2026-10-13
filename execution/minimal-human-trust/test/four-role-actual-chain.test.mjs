// Actual public App/Bridge/Native adapters and ProjectForge engine. Transport is
// in-process and all keys/ledgers are disposable; not an OS Human admission test.
import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import {createRequire} from 'node:module';
import {generateKeyPairSync,randomUUID,createHash} from 'node:crypto';
import {ProtectedStore,createIssuer,issuerInitialState,signed,verified,digest,exportPublicKey,ACTIONS} from '../src/lease-core.mjs';
import {verifySignedBusinessStop} from '../src/signed-business-stop.mjs';
import {runMinimalTrustOnce,replayInitialState} from '../src/minimal-trust-issuer.mjs';
import {createWorkspaceDispatcher,dispatcherInitialState} from '../host/workspace-dispatcher.mjs';
import {createWorkspaceHost,createWorkspaceClient,appHostInitialState} from '../app/workspace-host.mjs';
import {createWorkspaceBridge,bridgeInitialState,calculateRuntimeVersion} from '../bridge/workspace-private-router.mjs';
import * as crown from '/home/jenn/AGENTS_OS_Workspace/projects/vcp-app-r16-working-source-r2/src/project-forge-crown-transport.mjs';
import {createCrownExecutor} from '/home/jenn/AGENTS_OS_Workspace/projects/vcp-app-r16-working-source-r2/src/project-forge-crown-executor.mjs';
const require=createRequire(import.meta.url),native=require('/home/jenn/AGENTS_OS_Workspace/projects/r16-vcpchat-pinned/VCPDistributedServer/Plugin/ProjectForge/ProjectForgeService.js'),C=require('/home/jenn/AGENTS_OS_Workspace/projects/r16-vcpchat-pinned/VCPDistributedServer/Plugin/ProjectForge/crownAuthority.js');

test('actual App Bridge Native ProjectForge execute under on-demand Minimal Trust, then refuse new business and retain reconcile',async()=>{
 const manifest=JSON.parse(fs.readFileSync(new URL('./fixtures/actual-adapters-manifest.json',import.meta.url)));
 for(const [name,pin]of Object.entries(manifest.files))assert.equal(createHash('sha256').update(fs.readFileSync(new URL('../'+name,import.meta.url))).digest('hex'),pin.sha256,'PUBLIC_ADAPTER_DRIFT');
 for(const pin of manifest.externalTestDependencies)assert.equal(createHash('sha256').update(fs.readFileSync(pin.path)).digest('hex'),pin.sha256,'EXTERNAL_DEPENDENCY_DRIFT');
 const root=fs.mkdtempSync(path.join(os.tmpdir(),'g1d-actual-chain-'));fs.chmodSync(root,0o700);
 const projects=path.join(root,'projects');fs.mkdirSync(projects,{mode:0o700});const st=fs.statSync(projects);
 const workspace={id:'isolated-ws',root:projects,dev:st.dev,ino:st.ino},db=path.join(root,'history.sqlite');
 native.initialize({dbPath:db,workspaceService:{list:()=>[{id:workspace.id,alias:'projects',path:projects,enabled:true}]},config:{AST_INDEX_ENABLED:false},logger:{log(){},warn(){}}});
 const old=(await native.processToolCall({command:'CreateProject',name:'isolated',workspace:'projects',dir:'isolated'})).details.project;
 const project={id:old.id,workspaceId:workspace.id,root:old.root};
 const keys=Object.fromEntries(['issuer','release','human','app','bridge','native'].map(r=>[r,generateKeyPairSync('ed25519').privateKey]));
 const peers=Object.fromEntries(['app','bridge','native'].map(r=>[r,{id:'peer-'+r,publicKey:exportPublicKey(keys[r])}]));
 const runtimeFiles={'workspace-private-router.mjs':path.resolve('bridge/workspace-private-router.mjs')};
 const versions={app:digest(fs.readFileSync('app/workspace-host.mjs','utf8')),bridge:calculateRuntimeVersion(runtimeFiles),native:digest(fs.readFileSync('host/workspace-dispatcher.mjs','utf8'))};
 let time=Date.now();const now=()=>time,stores=[];
 const make=(name,initial)=>{const s=new ProtectedStore({directory:path.join(root,name),create:true,initial,now});stores.push(s);return s;};
 const issuerStore=make('issuer',issuerInitialState());
 const resolveProject=(_w,p)=>{assert.deepEqual(p,project);return p;};
 const initializer=createIssuer({store:issuerStore,signingKey:keys.issuer,releaseKey:exportPublicKey(keys.release),authorizeOwner:()=>true,resolveProject});
 const grant=initializer.createGrant({approval:{syntheticHumanOnly:true},grant:{id:'isolated-grant',workspace,actions:ACTIONS.slice(),channel:'main',peers}});
 issuerStore.close();make('replay',replayInitialState()).close();
 const release=signed({schema:'r16.release.v1',id:'isolated-signed-release',issuedAt:time-1000,notAfter:time+86400000,formats:['r16.workspace.v1'],versions,actions:ACTIONS.slice(),permissionVersion:1},keys.release);
 let mode='active',nativeCalls=0,dropNext=false;const actualClosures=[];
 const args={issuerDirectory:path.join(root,'issuer'),replayDirectory:path.join(root,'replay'),issuerPrivateKey:keys.issuer,
  issuerPublicKey:exportPublicKey(keys.issuer),releasePublicKey:exportPublicKey(keys.release),grantId:grant.body.id,release,resolveProject,humanAuthorityPublicKey:exportPublicKey(keys.human),now};
 // Identical outer signer/role contract to the production issuer-client.
 const issuer=Object.fromEntries(['fresh','prepare','prepareStatus','activate','closeLease','acknowledgeRevocation','grant','heartbeat'].map(action=>[action,payload=>{const result=runMinimalTrustOnce({...args,mode,envelope:signed({schema:'r16.issuer-call.v1',role:'native',peerId:peers.native.id,issuedAt:now(),nonce:randomUUID(),action,payload},keys.native)});if(action==='closeLease')actualClosures.push(payload);return result;}]));
 const ds=make('native',dispatcherInitialState()),bs=make('bridge',bridgeInitialState()),as=make('app',appHostInitialState());
 const common={grant,release,versions,issuerKey:args.issuerPublicKey,releaseKey:args.releasePublicKey,now};
 const d=createWorkspaceDispatcher({...common,store:ds,directory:ds.dir,native,crown:C,signingKey:keys.native,issuer,workspaceAlias:'projects',databasePath:db});
 const origin='isolated-native',identity={logicalName:'ProjectForge',originKind:'distributed',originId:origin,originKey:'distributed:'+origin+':ProjectForge'};
 const pluginManager={plugins:new Map([['ProjectForge',{isDistributed:true,serverId:origin}]]),async processToolCall(name,input){assert.equal(name,'ProjectForge');if(input.command==='WorkspaceCall')nativeCalls++;const result=await d.handle(input);if(dropNext&&input.command==='WorkspaceCall'&&input.operation.body.action==='create_file'&&JSON.parse(Buffer.from(input.proof.payload_b64,'base64')).mode==='execute'){dropNext=false;throw Error('SYNTHETIC_REPLY_LOST');}return result;}};
 const b=createWorkspaceBridge({...common,store:bs,directory:bs.dir,signingKey:keys.bridge,pluginManager,wss:{getDistributedServerSnapshot:()=>[{serverId:origin,connected:true,tools:['ProjectForge']}]},crown:C,runtimeFiles});
 const exchange=createWorkspaceClient({url:'http://127.0.0.1:39999/workspace/exchange',grant,signingKey:keys.app,now,fetchImpl:async(_url,options)=>new Response(JSON.stringify(await b.exchange(JSON.parse(options.body))),{status:200})});
 const capability=Buffer.alloc(32,65);
 const app=createWorkspaceHost({...common,store:as,directory:as.dir,signingKey:keys.app,channelCapability:capability,crown,createCrownExecutor,exchange});
 const execute=request=>{
  const context=app.runtimeDependencies.resolveProjectForgeCrownContext({socket:{remoteAddress:'127.0.0.1'},rawHeaders:['x-r16-task-capability',capability.toString()],headers:{'x-r16-task-capability':capability.toString()},body:{params:{arguments:request}}});
  return app.executor({request,trustedContext:context});
 };
 try{
  await d.refresh();d.connectedIdentity(identity);
  const binding=await execute({action:'bind_project',project_id:project.id});
  assert.equal(binding.ok,true,JSON.stringify(binding));assert.equal(binding.completion_verified,true);
  const session=binding.project_session_id;
  const created=await execute({action:'create_file',project_session_id:session,path:'proof.txt',content:'actual native write',reason:'isolated G1D proof'});
  assert.equal(created.ok,true,JSON.stringify(created));assert.equal(created.completion_verified,true);
  assert.equal(fs.readFileSync(path.join(project.root,'proof.txt'),'utf8'),'actual native write');
  const read=await execute({action:'read_code',project_session_id:session,path:'proof.txt'});
  assert.equal(read.ok,true,JSON.stringify(read));
  assert.ok(nativeCalls>=3);
  dropNext=true;
  const lost=await execute({action:'create_file',project_session_id:session,path:'lost-reply.txt',content:'exactly once',reason:'isolated response loss'});
  assert.equal(lost.ok,false);assert.equal(fs.existsSync(path.join(project.root,'lost-reply.txt')),true,JSON.stringify(lost));assert.equal(fs.readFileSync(path.join(project.root,'lost-reply.txt'),'utf8'),'exactly once');
  const unknown=as.snapshot().operations.find(x=>x.status==='UNKNOWN');assert.ok(unknown);
  assert.equal(bs.snapshot().calls.find(x=>x.id===unknown.id).status,'UNKNOWN');
  const stopEpoch=randomUUID(),revision=88,reviewDigest=digest('isolated-review');
  const roles={app,bridge:b,native:d};
  for(const role of Object.values(roles))assert.throws(()=>role.businessStopEvidence({revision,reviewDigest}),{code:'STOP_NOT_ESTABLISHED'});
  for(const role of Object.values(roles))role.suspendBusiness({stopEpoch});
  mode='recovery_only';
  d.setConnectionRequested(true);assert.equal(d.admissionStatus().admissionStopped,true);
  const delivery=signed({schema:'r16.configuration-delivery.v1',revision,issuedAt:time,
   publicConfig:{schema:'r16.runtime-configuration.v1',issuerPublicKey:args.issuerPublicKey,releasePublicKey:args.releasePublicKey,grant,release,peers,versions,channel:'main'},
   control:{grantId:grant.body.id,grantVersion:1,status:'ACTIVE',connectRequested:false}},keys.issuer);
  const inspect=expectedUnresolvedIds=>{const receipts=Object.fromEntries(Object.entries(roles).map(([role,runtime])=>[role,runtime.businessStopEvidence({revision,reviewDigest})]));
   return {grant,issuerPublicKey:args.issuerPublicKey,release,releasePublicKey:args.releasePublicKey,delivery,receipts,expectedRevision:revision,expectedReviewDigest:reviewDigest,stopEpoch,now:time,expectedUnresolvedIds,expectedResultsHashes:Object.fromEntries(Object.entries(receipts).map(([role,receipt])=>[role,receipt.body.resultsHash]))};};
  const beforeReconcile=inspect([unknown.id]);
  assert.throws(()=>verifySignedBusinessStop(beforeReconcile),{code:'STOP_ROLE_MISMATCH'});
  assert.equal(as.snapshot().operations.find(x=>x.id===unknown.id).status,'UNKNOWN');
  const callsAfterLost=nativeCalls;await app.reconcileStopped();
  assert.equal(nativeCalls,callsAfterLost);
  assert.equal((as.snapshot().operations.find(x=>x.id===unknown.id)||as.archived('app-operation-'+unknown.id)).status,'KNOWN');
  assert.equal(bs.snapshot().calls.find(x=>x.id===unknown.id).status,'KNOWN');
  const verifiedStop=inspect([]);assert.equal(verifySignedBusinessStop(verifiedStop).result,'SIGNED_ROLES_MATCH');
  for(const [role,receipt]of Object.entries(verifiedStop.receipts)){assert.equal(receipt.body.stopEpoch,stopEpoch);assert.equal(receipt.body.runtimeVersion,versions[role]);assert.equal(receipt.body.releaseHash,digest(release));}
  const recorded=unknown;
  const before=nativeCalls;
  assert.throws(()=>execute({action:'read_code',project_session_id:session,path:'proof.txt'}),{code:'GRANT_REVOKED'});assert.equal(nativeCalls,before);
  const control=signed({schema:'r16.workspace-control.v1',id:randomUUID(),grantId:grant.body.id,channel:'main',operation:'reconcile',data:{projectId:project.id,operationId:recorded.id,operation:recorded.operation},issuedAt:time,expiresAt:time+30000},keys.app);
  const reconciled=verified(await d.handle({command:'WorkspaceControl',proof:control}),peers.native.publicKey,'r16.workspace-control-result.v1').result;
  assert.equal(reconciled.receipt.body.outcome,'COMPLETED');assert.equal(nativeCalls,before);
  const approval=signed({schema:'mht.human-authorization.v1',action:'revoke_grant',grantId:grant.body.id,expectedVersion:1,expectedGrantHash:digest(grant),releaseId:release.body.id,issuedAt:now(),nonce:randomUUID()},keys.human);
  const revoked=runMinimalTrustOnce({...args,mode,ownerApproval:approval});assert.equal(revoked.body.version,2);
  await app.close();
  assert.ok(actualClosures.length>=1);
  for(const closure of actualClosures){
   assert.equal(closure.lease.body.releaseHash,digest(release));
   assert.deepEqual(closure.lease.body.versions,versions);
   assert.equal(new Set(Object.values(closure.evidence).map(e=>e.body.resultsHash)).size,1);
   for(const role of ['app','bridge','native']){const receipt=verified(closure.evidence[role],peers[role].publicKey,'r16.stopped.v1');assert.equal(receipt.role,role);assert.equal(receipt.pending,0);}
  }
  await b.close();await d.close();
 }finally{
  try{await app.close();}catch{}try{await b.close();}catch{}try{await d.close();}catch{}
  await native.cleanup();for(const s of stores)try{s.close();}catch{}
  fs.rmSync(root,{recursive:true,force:true});
 }
});
