import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import {createRequire} from 'node:module';
import {generateKeyPairSync,randomUUID} from 'node:crypto';
import {ProtectedStore,createIssuer,issuerInitialState,participantInitialState,createParticipant,signed,verified,digest,exportPublicKey,ACTIONS} from '../src/lease-core.mjs';
import {createWorkspaceDispatcher,dispatcherInitialState} from '../host/workspace-dispatcher.mjs';
const require=createRequire(import.meta.url),native=require('/home/jenn/AGENTS_OS_Workspace/projects/r16-vcpchat-pinned/VCPDistributedServer/Plugin/ProjectForge/ProjectForgeService.js'),C=require('/home/jenn/AGENTS_OS_Workspace/projects/r16-vcpchat-pinned/VCPDistributedServer/Plugin/ProjectForge/crownAuthority.js');

test('real Native/SQLite grant composition preserves result and history, refuses replay and foreign paths',async()=>{
  const temp=fs.mkdtempSync(path.join(os.tmpdir(),'r16-dispatch-fixture-'));fs.chmodSync(temp,0o700);
  const wsroot=path.join(temp,'projects');fs.mkdirSync(wsroot,{mode:0o700});const st=fs.statSync(wsroot);
  const workspace={id:'ws-fixture',root:wsroot,dev:st.dev,ino:st.ino},db=path.join(temp,'history.sqlite');
  const facade={id:workspace.id,alias:'projects',path:wsroot,enabled:true};
  native.initialize({dbPath:db,workspaceService:{list:()=>[facade]},config:{AST_INDEX_ENABLED:false},logger:{log(){},warn(){}}});
  const old=(await native.processToolCall({command:'CreateProject',name:'old',workspace:'projects',dir:'old'})).details.project;
  const project={id:old.id,workspaceId:workspace.id,root:old.root};
  const key=()=>generateKeyPairSync('ed25519').privateKey,issuerKey=key(),releaseKey=key(),peerKeys={app:key(),bridge:key(),native:key()};
  const peers=Object.fromEntries(Object.keys(peerKeys).map(role=>[role,{id:'peer-'+role,publicKey:exportPublicKey(peerKeys[role])}]));
  const versions={app:digest('app'),bridge:digest('bridge'),native:digest('native')};
  let time=Date.now();const now=()=>time,stores=[];
  const makeStore=(name,initial)=>{const s=new ProtectedStore({directory:path.join(temp,name),create:true,initial,now});stores.push(s);return s;};
  const issuer=createIssuer({store:makeStore('issuer',issuerInitialState()),signingKey:issuerKey,releaseKey:exportPublicKey(releaseKey),authorizeOwner:()=>true,resolveProject:(_w,p)=>{assert.deepEqual(p,project);return p;}});
  const grant=issuer.createGrant({approval:{fixture:true},grant:{id:'grant-one',workspace,actions:ACTIONS.slice(),channel:'main',peers}});
  const release=signed({schema:'r16.release.v1',id:'release',issuedAt:time,notAfter:time+86400000,formats:['r16.workspace.v1'],versions,actions:ACTIONS.slice(),permissionVersion:1},releaseKey);
  const ds=makeStore('dispatcher',dispatcherInitialState());
  let delayFresh=0,denyFresh=false;const issuerTransport={...issuer,fresh:async args=>{if(denyFresh)throw Error('DISCONNECTED');time+=delayFresh;delayFresh=0;return issuer.fresh(args);}};
  let loseSignedReadReply=false,nativeReadCalls=0;
  const fixtureNative={...native,createWorkspaceCrownPort(options){
    const port=native.createWorkspaceCrownPort(options);
    return {...port,handleCall:async args=>{
      const payload=JSON.parse(Buffer.from(args.proof.payload_b64,'base64').toString('utf8'));
      if(loseSignedReadReply&&payload.request.action==='find_symbol'){
        nativeReadCalls++;
        await port.handleCall(args); // execute this real read once; lose its exact response
        return {status:'unknown'};
      }
      return port.handleCall(args);
    }};
  }};
  const d=createWorkspaceDispatcher({store:ds,directory:ds.dir,native:fixtureNative,crown:C,grant,release,versions,signingKey:peerKeys.native,issuerKey:exportPublicKey(issuerKey),releaseKey:exportPublicKey(releaseKey),issuer:issuerTransport,workspaceAlias:'projects',databasePath:db,now});
  const identity={logicalName:'ProjectForge',originKind:'distributed',originId:'fixture',originKey:'distributed:fixture:ProjectForge'};
  async function control(operation,data){const body={schema:'r16.workspace-control.v1',id:randomUUID(),grantId:grant.body.id,channel:'main',operation,data,issuedAt:time,expiresAt:time+30000};const result=await d.handle({command:'WorkspaceControl',proof:signed(body,peerKeys.app)});return verified(result,peers.native.publicKey,'r16.workspace-control-result.v1').result;}
  let stopped=false;
  try{
    await d.refresh();
    const remote={peerId:peers.native.id,grantId:grant.body.id,channel:'main',generation:0,origin:null};
    const connection=await d.prepareConnection(remote);assert.equal(connection.generation,1);
    await assert.rejects(d.prepareConnection(remote),{code:'RECOVERY_REQUIRED'});
    d.connectionClosed(1);const retry=await d.prepareConnection(remote);assert.equal(retry.generation,2);
    d.connectedIdentity(identity,2);
    const descriptor=await control('describe',{identity});
    assert.deepEqual((await control('resolve',{projectId:project.id})).project,project);
    const request={schema:'r16.prepare.v1',requestId:randomUUID(),grantId:grant.body.id,grantVersion:1,project,channel:'main',versions,actions:ACTIONS.slice(),issuedAt:time};
    const proofs={app:signed(request,peerKeys.app),bridge:signed(request,peerKeys.bridge),native:await control('sign_prepare',{request,release})};
    const lease=issuer.prepare({grantId:grant.body.id,request,proofs,release});
    const other=Object.fromEntries(['app','bridge'].map(role=>[role,createParticipant({store:makeStore(role,participantInitialState(role)),role,signingKey:peerKeys[role],issuerKey:exportPublicKey(issuerKey),releaseKey:exportPublicKey(releaseKey),resolveProject:(_w,p)=>p})]));
    const evidence={};for(const role of ['app','bridge']){const p=other[role];p.pair({grant});const r=p.freshRequest(grant.body.id);p.acceptFresh({response:issuer.fresh({request:r}),grant});p.prepare({lease,grant,release});evidence[role]=p.closeEvidence();}
    await control('prepare',{projectId:project.id,lease,release});evidence.native=await control('close',{projectId:project.id});
    const activation=issuer.activate({grantId:grant.body.id,projectId:project.id,evidence});
    for(const p of Object.values(other))p.activate({activation});await control('activate',{projectId:project.id,activation});
    const resumed=await control('fresh',{projectId:project.id});assert.equal(resumed.status.available,true);assert.equal(resumed.activeLeaseHash,digest(lease));assert.equal(resumed.activeGeneration,1);assert.equal(resumed.pendingLeaseHash,null);assert.equal(resumed.closingLeaseHash,null);
    const payload=(request,extra={})=>({audience:C.CALL_AUDIENCE,request_id:randomUUID(),issued_at:time,expires_at:time+30000,native_epoch:descriptor.epoch,authorization_ref:grant.body.id,identity,binding:null,workspace:null,command:C.CALL_COMMANDS[request.action],request,expected_version:null,mode:'execute',reconcile_id:null,...extra});
    const operation=p=>signed({schema:'r16.operation.v1',id:p.request_id,grantId:grant.body.id,projectId:project.id,generation:1,leaseHash:digest(lease),channel:'main',action:p.request.action,payloadHash:digest(p)},peerKeys.app);
    const call=p=>d.handle({command:'WorkspaceCall',operation:operation(p),proof:C.signCall(p,peerKeys.app)});
    const get=payload({action:'get_project',project_id:project.id});assert.equal((await call(get)).nativeResult.fields.project_id,project.id);
    const session=randomUUID(),r={action:'create_file',project_session_id:session,path:'one.txt',reason:'fixture',content:'once'};
    const p=payload(r,{binding:{projectId:project.id,workspaceId:workspace.id,workspaceAlias:'projects',projectRoot:project.root,originId:identity.originId},expected_version:{kind:'absent'}});
    const first=await call(p);assert.equal(first.nativeResult.status,'verified');assert.equal(first.nativeResult.fields.ok,true);assert.equal(first.receipt.body.outcome,'COMPLETED');
    assert.equal(fs.readFileSync(path.join(project.root,'one.txt'),'utf8'),'once');
    const second=await call(p);assert.deepEqual(second,first);
    const reconciled=await control('reconcile',{projectId:project.id,operationId:p.request_id});assert.deepEqual(reconciled,first);
    const forged={...p,request_id:randomUUID(),binding:{...p.binding,projectRoot:temp}};
    await assert.rejects(call(forged),{code:'PROJECT_BINDING'});
    // A delayed fresh check cannot turn an expired allocation into a directory.
    const allocProof=()=>signed({schema:'r16.workspace-control.v1',id:randomUUID(),grantId:grant.body.id,channel:'main',operation:'allocate',data:{},issuedAt:time,expiresAt:time+30000},peerKeys.app);
    const expired=signed({...allocProof().body,expiresAt:time+1000},peerKeys.app),before=ds.snapshot().pending.length;delayFresh=1500;
    await assert.rejects(d.handle({command:'WorkspaceControl',proof:expired}),{code:'CONTROL_EXPIRED'});
    assert.equal(ds.snapshot().pending.length,before);
    const terminal=await control('control_status',{id:expired.body.id,originalProof:expired});assert.equal(terminal.status,'NOT_EXECUTED');
    assert.equal(ds.snapshot().controls.find(x=>x.id===expired.body.id).status,'NOT_EXECUTED');
    // Completion loss after durable ALLOCATED recovers the same UUID/inode.
    const allocated=allocProof(),allocatedResponse=await d.handle({command:'WorkspaceControl',proof:allocated});
    fs.unlinkSync(path.join(ds.dir,'results','control-'+allocated.body.id+'.json'));
    ds.transact(s=>{s.controls.find(x=>x.id===allocated.body.id).status='UNKNOWN';});
    const restored=await control('control_status',{id:allocated.body.id,originalProof:allocated});
    assert.equal(restored.status,'KNOWN');assert.deepEqual(restored.response,allocatedResponse);
    const creating=allocProof();
    ds.transact(s=>{s.controls.push({id:creating.body.id,hash:digest(creating),status:'UNKNOWN'});s.pending.push({controlId:creating.body.id,status:'CREATING',project:{id:'pending-fixture',workspaceId:workspace.id,root:path.join(wsroot,'project-unresolved')}});});
    assert.equal((await control('control_status',{id:creating.body.id,originalProof:creating})).status,'UNKNOWN');
    const freshProof=allocProof();assert.equal((await control('control_status',{id:freshProof.body.id,originalProof:freshProof})).status,'NOT_SEEN');
    assert.equal(ds.snapshot().controls.some(x=>x.id===freshProof.body.id),false);
    // Archiving never loses a terminal nonexecution fence or allocation result.
    for(let i=0;i<140;i++)await control('control_status',{id:'never-seen-'+i});
    assert.ok(ds.snapshot().controls.length<128);
    assert.equal((await control('control_status',{id:expired.body.id,originalProof:expired})).status,'NOT_EXECUTED');
    assert.deepEqual((await control('control_status',{id:allocated.body.id,originalProof:allocated})).response,allocatedResponse);
    assert.equal((await control('control_status',{id:creating.body.id,originalProof:creating})).status,'UNKNOWN');
    // A real Native/SQLite protocol exercise with an intentionally lost
    // FindSymbol response; no original business operation is replayed.
    const readPayload=payload({action:'find_symbol',project_session_id:randomUUID(),symbol:'findSymbolCmd'},{
      binding:{projectId:project.id,workspaceId:workspace.id,workspaceAlias:'projects',
        projectRoot:project.root,originId:identity.originId}});
    const readOperation=operation(readPayload);
    for(const role of ['app','bridge'])other[role].begin({operation:readOperation});
    loseSignedReadReply=true;
    const lost=await call(readPayload);
    loseSignedReadReply=false;
    assert.equal(lost.receipt,null);
    assert.equal(nativeReadCalls,1);
    const nativeProjectFile=path.join(ds.dir,'project-'+project.id,'state.json');
    const nativeBefore=JSON.parse(fs.readFileSync(nativeProjectFile,'utf8')).data;
    assert.equal(nativeBefore.operations.find(x=>x.id===readPayload.request_id).status,'UNKNOWN');
    const suspend=d.suspendBusiness();
    assert.deepEqual(suspend,{businessStopped:true});
    assert.deepEqual(d.admissionStatus(),{revoked:false,version:1,admissionStopped:true});
    assert.equal(JSON.parse(fs.readFileSync(path.join(ds.dir,'state.json'),'utf8')).data.admissionStopped,true);
    await assert.rejects(call(payload({action:'get_project',project_id:project.id})),{code:'GRANT_REVOKED'});
    const afterSuspend=JSON.parse(fs.readFileSync(nativeProjectFile,'utf8')).data;
    assert.equal(afterSuspend.operations.find(x=>x.id===readPayload.request_id).status,'UNKNOWN');
    for(const role of ['app','bridge'])other[role].markUnknown(readPayload.request_id);
    await control('drain',{projectId:project.id,lease});
    for(const role of ['app','bridge'])other[role].drain({lease});
    await assert.rejects(control('reconcile',{projectId:project.id,operationId:readPayload.request_id,operation:readOperation}),{code:'LEASE_NOT_EXPIRED'});
    assert.equal(fs.existsSync(path.join(ds.dir,'results','operation-'+readPayload.request_id+'.json')),false);
    time+=3600001;
    const recovered=await control('reconcile',{projectId:project.id,operationId:readPayload.request_id,operation:readOperation});
    assert.equal(recovered.receipt.body.outcome,'READ_RESULT_UNAVAILABLE');
    assert.equal(nativeReadCalls,1); // reconciliation must never dispatch FindSymbol again
    assert.equal(recovered.nativeResult.schema,'r16.read-result-unavailable.v1');
    assert.equal(recovered.nativeResult.reason,'ORIGINAL_RESULT_NOT_DURABLE');
    assert.deepEqual(await control('reconcile',{projectId:project.id,operationId:readPayload.request_id,operation:readOperation}),recovered);
    for(const role of ['app','bridge'])assert.equal(other[role].reconcile({
      receipt:recovered.receipt,operation:readOperation}).outcome,'READ_RESULT_UNAVAILABLE');
    const nativeStop=await control('stop',{projectId:project.id,lease});
    assert.equal(nativeStop.body.schema,'r16.stopped.v1');
    assert.equal(nativeStop.body.pending,0);
    assert.equal((JSON.parse(fs.readFileSync(nativeProjectFile,'utf8')).data).operations.length,0);
    // A recent protected Owner status allows cleanup reconnect while Owner
    // deliberately rejects business freshness; stale cached status does not.
    d.setConnectionRequested(false);denyFresh=true;
    d.noteOwnerStatus({connectRequested:false,revoked:false,grantVersion:1});
    assert.deepEqual(await d.refresh(true,{allowRevoked:true}),{status:'CLEANUP_ONLY',verifiedLiveFresh:false});
    await assert.rejects(call(payload({action:'get_project',project_id:project.id})),{code:'GRANT_REVOKED'});
    assert.deepEqual(await control('reconcile',{projectId:project.id,operationId:p.request_id}),first);
    time+=30001;await assert.rejects(d.refresh(true,{allowRevoked:true}),/DISCONNECTED/);
    await d.close({retainTransport:true});assert.equal(ds.closed,false);d.connectionClosed(2);assert.equal(ds.snapshot().connection.closed,true);d.releaseStores();assert.equal(ds.closed,true);stopped=true;
    assert.equal(fs.existsSync(path.join(temp,'one.txt')),false);
  }finally{
    if(!stopped){try{await d.close();}catch{}}
    await native.cleanup();for(const s of stores){try{s.close();}catch{}}fs.rmSync(temp,{recursive:true,force:true});
  }
});