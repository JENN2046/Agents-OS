import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import {generateKeyPairSync,randomUUID,createHash} from 'node:crypto';
import {createRequire} from 'node:module';
import http from 'node:http';
import {ProtectedStore,createIssuer,issuerInitialState,createParticipant,participantInitialState,
  signed,verified,digest,exportPublicKey,ROLES,ACTIONS,LEASE_MS} from '../src/lease-core.mjs';
import {createWorkspaceDispatcher,dispatcherInitialState} from '../host/workspace-dispatcher.mjs';

// Only the ProjectForge engine is stubbed: no database, production keys or
// production state. Grants, challenges, leases, activations, results, closure
// proofs and both kinds of protected journal use their real implementations.
async function fixture(t,{phase='closed',fenced=true,extraPendingProject=false}={}){
  const dir=fs.mkdtempSync(path.join(os.tmpdir(),'native-recovery-release-'));
  fs.chmodSync(dir,0o700);
  const stores=[];
  let time=1791630000000;
  const now=()=>time,advance=ms=>{time+=ms;};
  const store=(name,initial)=>{
    const value=new ProtectedStore({directory:path.join(dir,name),initial,create:true,now});
    stores.push(value);return value;
  };
  const root=path.join(dir,'projects');fs.mkdirSync(root,{mode:0o700});
  const st=fs.statSync(root),workspace={id:'fixture-workspace',root,dev:st.dev,ino:st.ino};
  const project={id:'fixture-project',workspaceId:workspace.id,root:path.join(root,'project')};
  fs.mkdirSync(project.root,{mode:0o700});
  const registry=new Map([[project.id,project]]);
  const resolveProject=(w,p)=>{assert.deepEqual(w,workspace);assert.deepEqual(p,registry.get(p.id));return p;};
  const key=()=>generateKeyPairSync('ed25519').privateKey;
  const issuerKey=key(),releaseKey=key(),peerKeys=Object.fromEntries(ROLES.map(role=>[role,key()]));
  const peers=Object.fromEntries(ROLES.map(role=>[role,{id:'peer-'+role,publicKey:exportPublicKey(peerKeys[role])}]));
  const versions=Object.fromEntries(ROLES.map(role=>[role,digest(role)])),approval={fixture:true};
  const issuer=createIssuer({store:store('issuer',issuerInitialState()),signingKey:issuerKey,
    releaseKey:exportPublicKey(releaseKey),authorizeOwner:args=>args.approval===approval,resolveProject});
  const grant=issuer.createGrant({approval,grant:{id:'fixture-grant',workspace,actions:ACTIONS.slice(),channel:'main',peers}});
  const release=signed({schema:'r16.release.v1',id:'fixture-release',issuedAt:now(),notAfter:now()+10*LEASE_MS,
    formats:['r16.workspace.v1'],versions,actions:ACTIONS.slice(),permissionVersion:1},releaseKey);
  const ds=store('dispatcher',{...dispatcherInitialState(),projects:[project.id],
    connection:{generation:1,origin:'fixture-previous',closed:true},
    // This durable bit records earlier recovery, never substitutes for a lease
    // or for fresh authority. Each state underneath it is built by the protocol.
    recoveryOnly:fenced,admissionStopped:fenced});
  const peerStores=Object.fromEntries(ROLES.map(role=>[role,store(role==='native'?'dispatcher/project-'+project.id:role,participantInitialState(role))]));
  const participants=Object.fromEntries(ROLES.map(role=>[role,createParticipant({store:peerStores[role],role,
    signingKey:peerKeys[role],issuerKey:exportPublicKey(issuerKey),releaseKey:exportPublicKey(releaseKey),resolveProject})]));
  const fresh=p=>{p.pair({grant});const request=p.freshRequest(grant.body.id);p.acceptFresh({response:issuer.fresh({request}),grant});};
  for(const p of Object.values(participants))fresh(p);
  const request={schema:'r16.prepare.v1',requestId:randomUUID(),grantId:grant.body.id,grantVersion:1,
    project,channel:'main',versions,actions:ACTIONS.slice(),issuedAt:now()};
  const proofs=Object.fromEntries(ROLES.map(role=>[role,signed(request,peerKeys[role])]));
  const lease=issuer.prepare({grantId:grant.body.id,request,proofs,release});
  for(const p of Object.values(participants))p.prepare({lease,grant,release});
  let operation=null;
  if(phase!=='pending'){
    const evidence=Object.fromEntries(ROLES.map(role=>[role,participants[role].closeEvidence()]));
    const activation=issuer.activate({grantId:grant.body.id,projectId:project.id,evidence});
    for(const p of Object.values(participants))p.activate({activation});
    operation=signed({schema:'r16.operation.v1',id:randomUUID(),grantId:grant.body.id,projectId:project.id,
      generation:lease.body.generation,leaseHash:digest(lease),channel:'main',action:'find_symbol',
      payloadHash:digest({symbol:'fixture'})},peerKeys.app);
    for(const p of Object.values(participants)){p.begin({operation});p.markUnknown(operation.body.id);}
    if(phase!=='unknown'){
      const receipt=participants.native.complete({operationId:operation.body.id,outcome:'COMPLETED',resultHash:digest('fixture-result')});
      for(const role of ['app','bridge'])participants[role].reconcile({receipt});
      if(phase==='closing')for(const p of Object.values(participants))p.drain({lease});
      if(phase==='closed'){
        const stopped=Object.fromEntries(ROLES.map(role=>[role,participants[role].stop({lease})]));
        const closed=issuer.closeLease({grantId:grant.body.id,projectId:project.id,lease,evidence:stopped});
        assert.equal(verified(closed,exportPublicKey(issuerKey),'r16.closed.v1').leaseHash,digest(lease));
      }
    }
  }
  if(extraPendingProject){
    const extra={id:'second-project',workspaceId:workspace.id,root:path.join(root,'second-project')};
    fs.mkdirSync(extra.root,{mode:0o700});registry.set(extra.id,extra);
    const extraRequest={...request,requestId:randomUUID(),project:extra};
    const extraProofs=Object.fromEntries(ROLES.map(role=>[role,signed(extraRequest,peerKeys[role])]));
    const extraLease=issuer.prepare({grantId:grant.body.id,request:extraRequest,proofs:extraProofs,release});
    const extraStore=store('dispatcher/project-'+extra.id,participantInitialState('native'));
    const extraParticipant=createParticipant({store:extraStore,role:'native',signingKey:peerKeys.native,
      issuerKey:exportPublicKey(issuerKey),releaseKey:exportPublicKey(releaseKey),resolveProject});
    fresh(extraParticipant);extraParticipant.prepare({lease:extraLease,grant,release});
    extraStore.close();ds.transact(s=>{s.projects.push(extra.id);});
  }
  peerStores.native.close();
  let engineCreations=0,dispatcher;
  const identity={logicalName:'ProjectForge',originKind:'distributed',originId:'fixture',originKey:'distributed:fixture:ProjectForge'};
  const crown={identityCheck:value=>{
    assert.equal(value.logicalName,'ProjectForge');assert.equal(value.originKind,'distributed');
    assert.equal(value.originKey,'distributed:'+value.originId+':ProjectForge');
  }};
  const native={cleanup:async()=>{},createWorkspaceCrownPort(){
    engineCreations++;
    return {callStatus:()=>({epoch:'fixture-epoch'}),close(){},lookupProject:id=>{
      assert.equal(registry.has(id),true);return registry.get(id);
    }};
  }};
  dispatcher=createWorkspaceDispatcher({store:ds,directory:ds.dir,native,crown,grant,release,versions,
    signingKey:peerKeys.native,issuerKey:exportPublicKey(issuerKey),releaseKey:exportPublicKey(releaseKey),
    issuer,workspaceAlias:'projects',databasePath:path.join(dir,'unused.sqlite'),now});
  t.after(async()=>{
    try{await dispatcher.close();}catch{}
    // A deliberately unresolved fixture cannot use normal graceful close.
    // Release its exact synthetic participant store after the queue drains.
    try{dispatcher.releaseStores();}catch{}
    for(const value of stores)try{value.close();}catch{}
    fs.rmSync(dir,{recursive:true,force:true});
  });
  async function control(operation,data){
    const proof=signed({schema:'r16.workspace-control.v1',id:randomUUID(),grantId:grant.body.id,
      channel:'main',operation,data,issuedAt:now(),expiresAt:now()+30000},peerKeys.app);
    const response=await dispatcher.handle({command:'WorkspaceControl',proof});
    return verified(response,peers.native.publicKey,'r16.workspace-control-result.v1').result;
  }
  return {dir,ds,d:dispatcher,grant,release,lease,operation,participants,peerStores,issuer,peerKeys,
    project,workspace,identity,versions,now,advance,control,engineCreations:()=>engineCreations,
    async cleanupConnection(){
      const connection=await dispatcher.prepareConnection({peerId:peers.native.id,grantId:grant.body.id,channel:'main',generation:1,origin:'fixture-previous'});
      assert.deepEqual(dispatcher.connectedIdentity(identity,connection.generation),{cleanupOnly:true});
      assert.equal(engineCreations,0);return connection;
    }};
}

async function expectFenced(f){
  assert.deepEqual(await f.d.refresh(true,{allowRevoked:true}),{status:'CLEANUP_ONLY',verifiedLiveFresh:true});
  assert.equal(f.ds.snapshot().recoveryOnly,true);
  assert.equal(f.d.admissionStatus().admissionStopped,true);
  f.d.setConnectionRequested(true);
  assert.equal(f.d.admissionStatus().admissionStopped,true);
  await assert.rejects(f.control('resolve',{projectId:f.project.id}),{code:'GRANT_REVOKED'});
}

for(const phase of ['unknown','active','closing','pending']){
  test('live signed freshness cannot clear recovery with a '+phase+' participant',async t=>{
    const f=await fixture(t,{phase});
    const stateBefore=JSON.parse(fs.readFileSync(path.join(f.ds.dir,'project-'+f.project.id,'state.json'))).data;
    if(phase==='active'||phase==='closing')assert.equal(stateBefore.operations[0].status,'KNOWN');
    await expectFenced(f);
    await f.cleanupConnection();
    const stateAfter=JSON.parse(fs.readFileSync(path.join(f.ds.dir,'project-'+f.project.id,'state.json'))).data;
    assert.deepEqual(stateAfter.operations,stateBefore.operations);
    assert.deepEqual(stateAfter.active,stateBefore.active);
    assert.deepEqual(stateAfter.pending,stateBefore.pending);
    assert.deepEqual(stateAfter.closing,stateBefore.closing);
  });
}

test('a closed first project cannot release recovery while another signed project lease is pending',async t=>{
  const f=await fixture(t,{extraPendingProject:true});
  await expectFenced(f);
  assert.deepEqual(f.ds.snapshot().projects,[f.project.id,'second-project']);
  const first=await f.control('status',{projectId:f.project.id});
  const second=await f.control('status',{projectId:'second-project'});
  assert.equal(first.pendingGeneration,null);assert.equal(first.expiresAt,null);
  assert.equal(second.pendingGeneration,1);
  await f.cleanupConnection();
});

for(const status of ['UNKNOWN','INFLIGHT']){
  test('an unresolved durable '+status+' control independently keeps recovery fenced',async t=>{
    const f=await fixture(t);
    const proof=signed({schema:'r16.workspace-control.v1',id:randomUUID(),grantId:f.grant.body.id,
      channel:'main',operation:'allocate',data:{},issuedAt:f.now(),expiresAt:f.now()+30000},f.peerKeys.app);
    const record={id:proof.body.id,hash:digest(proof),status};
    f.ds.transact(s=>{s.controls.push(record);});
    await expectFenced(f);
    assert.deepEqual(f.ds.snapshot().controls.find(c=>c.id===record.id),record);
    await f.cleanupConnection();
  });
}

for(const status of ['CREATING','ALLOCATED']){
  test('a '+status+' allocation keeps recovery fenced after all project leases close',async t=>{
    const f=await fixture(t,{fenced:false});
    assert.equal((await f.d.refresh()).status,'CONNECTED');
    f.d.connectedIdentity(f.identity);
    const allocated=await f.control('allocate',{});
    assert.equal(fs.statSync(allocated.project.root).isDirectory(),true);
    f.ds.transact(s=>{
      assert.equal(s.pending.length,1);assert.equal(s.pending[0].status,'ALLOCATED');
      s.pending[0].status=status;s.recoveryOnly=true;s.admissionStopped=true;
    });
    await expectFenced(f);
    assert.equal(f.ds.snapshot().pending[0].status,status);
  });
}

for(const failure of ['release expired','workspace replaced']){
  test(failure+' prevents recovery release but preserves authenticated cleanup transport',async t=>{
    const f=await fixture(t);
    if(failure==='release expired')f.advance(f.release.body.notAfter-f.now()+1);
    else{
      fs.renameSync(f.workspace.root,f.workspace.root+'-original');
      fs.mkdirSync(f.workspace.root,{mode:0o700});
      assert.notEqual(fs.statSync(f.workspace.root).ino,f.workspace.ino);
    }
    await expectFenced(f);
    await f.cleanupConnection();
    assert.equal((await f.control('status',{projectId:f.project.id})).unresolved.length,0);
  });
}

for(const fence of ['Owner disconnect','durable business STOP']){
  test('closed recovery does not erase the independent '+fence+' fence',async t=>{
    const f=await fixture(t);
    if(fence==='durable business STOP')f.d.suspendBusiness({stopEpoch:'fixture-business-stop'});
    else f.d.setConnectionRequested(false);
    const businessStop=f.ds.snapshot().businessStop;
    assert.deepEqual(await f.d.refresh(true,{allowRevoked:true}),{status:'CLEANUP_ONLY',verifiedLiveFresh:true});
    assert.equal(f.ds.snapshot().recoveryOnly,false);
    assert.equal(f.d.admissionStatus().admissionStopped,true);
    assert.deepEqual(f.ds.snapshot().businessStop,businessStop);
    await assert.rejects(f.control('resolve',{projectId:f.project.id}),{code:'GRANT_REVOKED'});
    if(fence==='durable business STOP'){
      assert.deepEqual(f.d.setConnectionRequested(true),{businessStopped:true});
      assert.deepEqual(f.ds.snapshot().businessStop,businessStop);
    }
  });
}

test('only fully closed valid recovery plus renewed Owner request admits the normal signed lease protocol',async t=>{
  const f=await fixture(t);
  assert.deepEqual(await f.d.refresh(true,{allowRevoked:true}),{status:'CLEANUP_ONLY',verifiedLiveFresh:true});
  assert.equal(f.ds.snapshot().recoveryOnly,false);
  assert.equal(f.d.admissionStatus().admissionStopped,true);
  await assert.rejects(f.control('resolve',{projectId:f.project.id}),{code:'GRANT_REVOKED'});
  assert.deepEqual(f.d.setConnectionRequested(true),{businessStopped:false});
  assert.deepEqual(await f.d.refresh(),{status:'CONNECTED',verifiedLiveFresh:true});
  f.d.connectedIdentity(f.identity);
  assert.equal(f.engineCreations(),1);
  assert.deepEqual(await f.control('resolve',{projectId:f.project.id}),{project:f.project,pending:false});
  const request={schema:'r16.prepare.v1',requestId:randomUUID(),grantId:f.grant.body.id,grantVersion:1,
    project:f.project,channel:'main',versions:f.versions,actions:ACTIONS.slice(),issuedAt:f.now()};
  const proofs={app:signed(request,f.peerKeys.app),bridge:signed(request,f.peerKeys.bridge),
    native:await f.control('sign_prepare',{request,release:f.release})};
  const lease=f.issuer.prepare({grantId:f.grant.body.id,request,proofs,release:f.release});
  const evidence={};
  for(const role of ['app','bridge']){
    const p=f.participants[role],challenge=p.freshRequest(f.grant.body.id);
    p.acceptFresh({response:f.issuer.fresh({request:challenge}),grant:f.grant});
    p.prepare({lease,grant:f.grant,release:f.release});evidence[role]=p.closeEvidence();
  }
  await f.control('prepare',{projectId:f.project.id,lease,release:f.release});
  evidence.native=await f.control('close',{projectId:f.project.id});
  const activation=f.issuer.activate({grantId:f.grant.body.id,projectId:f.project.id,evidence});
  await f.control('activate',{projectId:f.project.id,activation});
  const state=await f.control('fresh',{projectId:f.project.id});
  assert.equal(state.status.available,true);
  assert.equal(state.activeGeneration,2);
  assert.equal(state.activeLeaseHash,digest(lease));
  assert.equal(f.ds.snapshot().recoveryOnly,false);
});

// Explicit local-system acceptance; not a claim of portable CI coverage.
if(process.env.MHT_R15_HEADLESS_ACCEPTANCE==='1')test('verified installed R15 headless transport reconnects through real loopback WebSocket with UNKNOWN fenced',async t=>{
  const base='/opt/r16/releases/r16-daily-20261012-r15';
  const pub=JSON.parse(fs.readFileSync('/run/r16-owner/public-config.json'));
  const official=verified(pub.release,pub.releasePublicKey,'r16.release.v1');
  assert.equal(official.id,'r16-daily-20261012-r15');
  const manifest=JSON.parse(fs.readFileSync(base+'/native-manifest.json'));
  assert.equal(digest(manifest),official.versions.native);
  const imported=['host/headless-host.mjs','host/connection-v2.mjs','host/native-gateway.mjs',
    'src/lease-core.mjs','src/control-clock.mjs'];
  for(const name of Object.keys(manifest.files))if(name.startsWith('native/upstream/node_modules/ws/'))imported.push(name);
  for(const name of imported){
    assert.equal(createHash('sha256').update(fs.readFileSync(base+'/'+name)).digest('hex'),manifest.files[name],name);
  }
  const [{createHeadlessHost},{createRecoverableConnector},{createNativeGateway,gatewayInitialState},legacy]=await Promise.all([
    import(base+'/host/headless-host.mjs'),import(base+'/host/connection-v2.mjs'),
    import(base+'/host/native-gateway.mjs'),import(base+'/src/lease-core.mjs')]);
  const require=createRequire(base+'/native/upstream/package.json');
  // Keep this checked dependency closure on the signed JS implementation;
  // optional native acceleration modules are unnecessary for the acceptance.
  const oldBufferUtil=process.env.WS_NO_BUFFER_UTIL,oldUtf8=process.env.WS_NO_UTF_8_VALIDATE;
  process.env.WS_NO_BUFFER_UTIL='1';process.env.WS_NO_UTF_8_VALIDATE='1';
  let WebSocket,WebSocketServer;
  try{({WebSocket,WebSocketServer}=require('ws'));}finally{
    if(oldBufferUtil===undefined)delete process.env.WS_NO_BUFFER_UTIL;else process.env.WS_NO_BUFFER_UTIL=oldBufferUtil;
    if(oldUtf8===undefined)delete process.env.WS_NO_UTF_8_VALIDATE;else process.env.WS_NO_UTF_8_VALIDATE=oldUtf8;
  }
  const f=await fixture(t,{phase:'unknown',fenced:false});
  const ledger=new legacy.ProtectedStore({directory:path.join(f.dir,'gateway'),create:true,initial:gatewayInitialState(),now:f.now});
  const server=http.createServer((_req,res)=>{res.writeHead(404);res.end();});
  const gateway=createNativeGateway({httpServer:server,WebSocketServer,store:ledger,grant:f.grant,
    bridgeSigningKey:f.peerKeys.bridge,versions:f.versions,now:f.now});
  await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
  const peers=[],states=[];
  const connect=createRecoverableConnector({WebSocket,baseUrl:'http://127.0.0.1:'+server.address().port,
    signingKey:f.peerKeys.native,peerId:f.grant.body.peers.native.id,grantId:f.grant.body.id,
    channel:'main',nativeVersion:f.versions.native,bridgePublicKey:f.grant.body.peers.bridge.publicKey,
    bridgeId:f.grant.body.peers.bridge.id,prepareConnection:r=>f.d.prepareConnection(r),
    onClosed:generation=>f.d.connectionClosed(generation),now:f.now,handshakeMs:2000,closeMs:2000});
  const host=createHeadlessHost({port:f.d,manifest:{name:'ProjectForge'},serverName:'Synthetic recovery acceptance',
    connect:async()=>{const peer=await connect();peers.push(peer);return peer;},
    acquireLease:()=>({release(){}}),onState:value=>states.push(value),shutdownMs:2000,
    setTimer:(fn)=>setTimeout(fn,20),clearTimer:clearTimeout});
  const wait=async predicate=>{
    const deadline=Date.now()+3000;
    while(!predicate()){if(Date.now()>deadline)throw Error('LOOPBACK_ACCEPTANCE_TIMEOUT');await new Promise(resolve=>setTimeout(resolve,5));}
  };
  try{
    const file=path.join(f.ds.dir,'project-'+f.project.id,'state.json');
    const unknown=JSON.parse(fs.readFileSync(file)).data.operations;
    await host.start();await wait(()=>gateway.getDistributedServerSnapshot().length===1);
    assert.equal(host.state,'恢复待核实');assert.equal(f.engineCreations(),0);
    const first=gateway.getDistributedServerSnapshot()[0].serverId;
    await peers[0].close();
    await wait(()=>peers.length>=2&&gateway.getDistributedServerSnapshot()[0]?.serverId!==first&&gateway.getDistributedServerSnapshot().length===1&&host.state==='恢复待核实');
    assert.equal(peers[1].generation,peers[0].generation+1);
    assert.equal(states.includes('可用'),false);assert.equal(f.engineCreations(),0);
    const origin=gateway.getDistributedServerSnapshot()[0].serverId;
    const proof=signed({schema:'r16.workspace-control.v1',id:randomUUID(),grantId:f.grant.body.id,
      channel:'main',operation:'resolve',data:{projectId:f.project.id},issuedAt:f.now(),expiresAt:f.now()+30000},f.peerKeys.app);
    await assert.rejects(gateway.executeDistributedTool(origin,'ProjectForge',{command:'WorkspaceControl',proof},2000),{code:'AUTHORITY_REJECTED'});
    const cleanup=signed({...proof.body,id:randomUUID(),operation:'status'},f.peerKeys.app);
    const response=await gateway.executeDistributedTool(origin,'ProjectForge',{command:'WorkspaceControl',proof:cleanup},2000);
    const result=verified(response,f.grant.body.peers.native.publicKey,'r16.workspace-control-result.v1').result;
    assert.deepEqual(result.unresolved,[f.operation.body.id]);
    assert.deepEqual(JSON.parse(fs.readFileSync(file)).data.operations,unknown);
    assert.equal(f.ds.snapshot().recoveryOnly,true);assert.equal(f.d.admissionStatus().admissionStopped,true);
    assert.equal(f.engineCreations(),0);
  }finally{
    // UNKNOWN deliberately prevents graceful business shutdown; do not forge
    // closure. Close only this test's sockets and release synthetic stores.
    try{await assert.rejects(host.stop(),{code:'RECOVERY_REQUIRED'});}finally{
      await Promise.allSettled(peers.map(peer=>peer.close()));
      await gateway.close();await new Promise(resolve=>server.close(resolve));ledger.close();
    }
  }
});
