// Explicit LOCAL resource lifecycle; not FIRST_STOP/global Quiescence evidence.
import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import net from 'node:net';
import {createRequire} from 'node:module';
import {generateKeyPairSync} from 'node:crypto';
import {ProtectedStore,participantInitialState,signed,digest,exportPublicKey,ROLES,ACTIONS,LEASE_MS,RENEW_BEFORE_MS} from '../src/lease-core.mjs';
import {createWorkspaceDispatcher,dispatcherInitialState,assertNativeRuntimeStart} from '../host/workspace-dispatcher.mjs';
import {createHeadlessHost,acquireProcessLease} from '../host/headless-host.mjs';
const require=createRequire(import.meta.url);
const {IndexerClient}=require('../native/upstream/VCPDistributedServer/Plugin/ProjectForge/indexerClient.js');
const delay=ms=>new Promise(r=>setTimeout(r,ms));
const source=fs.readFileSync(new URL('../host/workspace-dispatcher.mjs',import.meta.url),'utf8');
const actualPins=[...source.matchAll(/operationHash:'([a-f0-9]{64})'/g)].map(x=>x[1]);
function temp(t){const dir=fs.mkdtempSync(path.join(os.tmpdir(),'native-physical-'));fs.chmodSync(dir,0o700);t.after(()=>fs.rmSync(dir,{recursive:true,force:true}));return dir;}
function childFixture(t,{readyMs=0,shutdownMs=0,ignore=false}={}){
 const dir=temp(t),bin=path.join(dir,'indexer');
 fs.writeFileSync(bin,`#!${process.execPath}\nconst rl=require('node:readline').createInterface({input:process.stdin});\n${ignore?"process.on('SIGTERM',()=>{});":''}\nsetTimeout(()=>console.log(JSON.stringify({type:'ready',protocolVersion:2})),${readyMs});\nrl.on('line',line=>{const m=JSON.parse(line);if(m.method==='shutdown'){${ignore?'return;':`setTimeout(()=>process.exit(0),${shutdownMs});`}return;}if(m.method==='findSymbols'&&m.params.delay){setTimeout(()=>console.log(JSON.stringify({id:m.id,ok:true,result:{hits:[]}})),m.params.delay);return;}console.log(JSON.stringify({id:m.id,ok:true,result:{hits:[]}}));});\n${ignore?"setInterval(()=>{},1000);":''}\n`,{mode:0o700});
 const client=new IndexerClient({binaryPath:bin,logger:{warn(){}}});
 t.after(async()=>{for(const c of client.ownedChildren.keys())c.kill('SIGKILL');await Promise.all([...client.ownedChildren.values()]);});return client;
}
test('real owned child must close, not merely exit its request Promise',async t=>{
 const c=childFixture(t,{shutdownMs:70});assert.deepEqual(await c.findSymbols('/tmp'),{hits:[]});
 const before=Date.now(),p=c.quiesce();assert.equal(c.quiesce(),p);
 const result=await p;assert.ok(Date.now()-before>=50);assert.deepEqual(result.children,[]);assert.equal(result.requests,0);assert.equal(result.unconfirmed,0);
 assert.equal(await c.findSymbols('/tmp'),null);
});
test('ensure continuation cannot dispatch a request after quiesce seals admission',async t=>{
 const c=childFixture(t);await c._ensure();const request=c.findSymbols('/tmp');
 await assert.rejects(c.quiesce(),{code:'INDEXER_EXECUTION_UNCONFIRMED'});assert.equal(await request,null);assert.equal(c.pending.size,0);assert.equal(c.nextId,1);
});
test('handshake timeout cannot wake a late shutdown effect',async t=>{
 const c=childFixture(t,{readyMs:100});const start=c._ensure();
 const p=c.quiesce({timeoutMs:15});await assert.rejects(p,{code:'INDEXER_DRAIN_TIMEOUT'});await start;await delay(20);
 assert.equal(c.ownedChildren.size,1);assert.equal(c.child.stdin.writableEnded,false);assert.equal(c.quiesce(),p);
});
test('RPC timeout residual survives JS waiter removal until real close',async t=>{
 const c=childFixture(t,{ignore:true});await c._ensure();await c._request('findSymbols',{delay:4000},10);
 assert.equal(c.pending.size,0);assert.equal(c.unconfirmed.size,1);assert.equal(c.ownedChildren.size,1);
 await assert.rejects(c.quiesce(),{code:'INDEXER_EXECUTION_UNCONFIRMED'});assert.equal(c.ownedChildren.size,1);
});
test('child ignoring graceful shutdown retains real owned child and sticky failure',async t=>{
 const c=childFixture(t,{ignore:true});await c._ensure();const p=c.quiesce({timeoutMs:15});await assert.rejects(p,{code:'INDEXER_DRAIN_TIMEOUT'});
 assert.equal(c.ownedChildren.size,1);assert.equal(c.quiesce(),p);
});

async function dispatcherFixture(t,{unknown=false,initialInflight=false,controls=[],native:givenNative,hook,leaseVersions,issuerHeartbeat}={}){
 const dir=temp(t),root=path.join(dir,'workspace');fs.mkdirSync(root,{mode:0o700});const st=fs.statSync(root),now=()=>1792250000000;
 const workspace={id:'fixture-workspace',root,dev:st.dev,ino:st.ino},key=()=>generateKeyPairSync('ed25519').privateKey,issuerKey=key(),releaseKey=key();
 const roleKeys=Object.fromEntries(ROLES.map(r=>[r,key()])),peers=Object.fromEntries(ROLES.map(r=>[r,{id:'fixture-'+r,publicKey:exportPublicKey(roleKeys[r])}]));
 const grant=signed({schema:'r16.workspace.v1',id:'r16-projects-daily',version:1,createdAt:now(),workspace,actions:ACTIONS,channel:'main',peers},issuerKey);
 const versions={app:'a'.repeat(64),bridge:'b'.repeat(64),native:'c'.repeat(64)};
 const release=signed({schema:'r16.release.v1',id:'fixture-current-release',issuedAt:now(),notAfter:now()+LEASE_MS,formats:['r16.workspace.v1'],versions,actions:ACTIONS,permissionVersion:1},releaseKey);
 const projects=unknown?['p2vox','pmog2']:[],ops=[],rawBefore={},stores=[];
 const ds=new ProtectedStore({directory:path.join(dir,'dispatcher'),create:true,now,initial:{...dispatcherInitialState(),projects,controls}});stores.push(ds);
 const oldVersions={app:'235a5b919c65ac1d73290732d2b2014c24a338cc4b6795a5064e804803ec1e7a',bridge:'9c58c33478388003fd52da0cb15736ec951a9bfc9cf29738e20de5d741921352',native:'76319c50acaec649967986c1f12e6923ba4f664ac3230596ed2703fce3470ae6'};
 const ids=['c434da49-055a-43dc-a3e3-695cce137909','d0364f8b-3a68-4ca2-a396-7953b29cee4c'];
 for(const [index,pid] of projects.entries()){
  const proot=path.join(root,pid);fs.mkdirSync(proot,{mode:0o700});const generation=[30,38][index];
  const lease=signed({schema:'r16.lease.v1',phase:'PREPARED',grantId:grant.body.id,grantVersion:1,grantHash:digest(grant),project:{id:pid,workspaceId:workspace.id,root:proot},channel:'main',versions:leaseVersions??oldVersions,actions:['find_symbol'],generation,previousGeneration:generation-1,issuedAt:1000,expiresAt:1000+LEASE_MS,renewAt:1000+LEASE_MS-RENEW_BEFORE_MS,requestId:'fixture-request-'+index,releaseHash:digest('old-r15-release')},issuerKey);
  const operation=signed({schema:'r16.operation.v1',id:ids[index],grantId:grant.body.id,projectId:pid,generation,leaseHash:digest(lease),channel:'main',action:'find_symbol',payloadHash:digest('fixture-symbol')},roleKeys.app);ops.push(operation);
  const state={...participantInitialState('native'),grant,version:1,lastGeneration:generation,active:{lease},closing:lease,operations:[{id:ids[index],hash:digest(operation),projectId:pid,generation,status:initialInflight?'INFLIGHT':'UNKNOWN',outcome:null,resultHash:null}]};
  const pstore=new ProtectedStore({directory:path.join(ds.dir,'project-'+pid),create:true,initial:state,now});pstore.close();rawBefore[pid]=fs.readFileSync(path.join(ds.dir,'project-'+pid,'state.json'));
 }
 // Explicit fixture-only immutable hash substitution; no production override API.
 let changed;
 // Resolve imports independently, leaving all production code unchanged except exact two public hash literals.
 changed=source.replace(/from '(\.\.\/[^']+)'/g,(_,rel)=>`from '${new URL(rel,new URL('../host/workspace-dispatcher.mjs',import.meta.url)).href}'`);
 if(unknown)for(let i=0;i<2;i++)changed=changed.replace(actualPins[i],digest(ops[i]));
 const module=unknown?await import('data:text/javascript;base64,'+Buffer.from(changed).toString('base64')):{createWorkspaceDispatcher};
 let closes=0,quiesces=0;
 const native=givenNative??{createWorkspaceCrownPort(){throw Error('unused');},async quiesceExecution(){quiesces++;return {schema:'r16.native-local-execution.v1',scope:'PROCESS_AND_OWNED_INDEXERS_ONLY',admissionClosed:true,workspaceCalls:0,queuedWriters:0,lifecycleCalls:0,indexers:[],storeOpen:true,writerOpen:true,globalExecution:'UNPROVEN'};},async cleanup(){closes++;}};
 const d=module.createWorkspaceDispatcher({store:ds,directory:ds.dir,native,crown:{},grant,release,versions,signingKey:roleKeys.native,issuerKey:exportPublicKey(issuerKey),releaseKey:exportPublicKey(releaseKey),issuer:{fresh(){throw Error('unused');},heartbeat:issuerHeartbeat},workspaceAlias:'fixture',databasePath:path.join(dir,'db'),now,historicalOperations:ops,beforePhysicalClose:hook});
 t.after(()=>{try{d.releaseStores();}catch{}for(const s of stores)try{s.close();}catch{}});
 return {dir,d,ds,ops,rawBefore,native,roleKeys,now,counts:()=>({closes,quiesces}),createAgain:()=>module.createWorkspaceDispatcher({store:ds})};
}
test('exact signed historical reads retain complete participant bytes and leases during LOCAL shutdown',async t=>{
 let hook=0;const f=await dispatcherFixture(t,{unknown:true,hook:observation=>{hook++;assert.equal(observation.scope,'LOCAL_ONLY');assert.equal(observation.globalExecution,'UNPROVEN');assert.equal(f.counts().closes,0);}});
 const p=f.d.shutdownLocalResources();assert.equal(f.d.shutdownLocalResources(),p);const result=await p;
 assert.equal(result.status,'LOCAL_RESOURCES_CLOSED');assert.equal(result.firstStopProof,'NOT_PROVEN');assert.equal(result.retainedHistory.length,2);assert.equal(hook,1);
 for(const [pid,bytes] of Object.entries(f.rawBefore))assert.deepEqual(fs.readFileSync(path.join(f.ds.dir,'project-'+pid,'state.json')),bytes);
 assert.throws(()=>f.d.setConnectionRequested(true),{code:'PHYSICAL_STOP_FENCED'});assert.throws(()=>f.d.refresh(),{code:'AUTHORITY_REJECTED'});
 assert.equal(f.ds.snapshot().physicalStop.phase,'LOCAL_RESOURCES_CLOSED');f.d.releaseStores();
 const reopened=new ProtectedStore({directory:f.ds.dir,create:false});assert.throws(()=>assertNativeRuntimeStart(reopened),{code:'PHYSICAL_STOP_FENCED'});reopened.close();
});
test('current INFLIGHT is rejected before engine cleanup without settling it',async t=>{
 const f=await dispatcherFixture(t,{unknown:true,initialInflight:true});await assert.rejects(f.d.shutdownLocalResources(),{code:'CURRENT_WORK_UNRESOLVED'});assert.equal(f.counts().closes,0);assert.throws(()=>f.d.releaseStores(),{code:'RECOVERY_REQUIRED'});
 for(const [pid,bytes] of Object.entries(f.rawBefore))assert.deepEqual(fs.readFileSync(path.join(f.ds.dir,'project-'+pid,'state.json')),bytes);
});
test('historical host controls are not silently whitelisted as old business reads',async t=>{
 const f=await dispatcherFixture(t,{controls:[{id:'historical-control',hash:'d'.repeat(64),status:'UNKNOWN'}]});await assert.rejects(f.d.shutdownLocalResources(),{code:'CURRENT_WORK_UNRESOLVED'});assert.equal(f.counts().closes,0);
});
test('hook failure is single flight and retains protected writer/store, never a Quiescence success',async t=>{
 const f=await dispatcherFixture(t,{hook(){throw Object.assign(Error('private detail'),{code:'UNPROVEN_EXECUTION_RISK'});}});const p=f.d.shutdownLocalResources();await assert.rejects(p,{code:'UNPROVEN_EXECUTION_RISK'});assert.equal(f.d.shutdownLocalResources(),p);assert.equal(f.counts().closes,0);assert.throws(()=>f.d.releaseStores(),{code:'RECOVERY_REQUIRED'});
});
test('new UNKNOWN or missing full historical signed operation cannot acquire local exemption',async t=>{
 const missing=await dispatcherFixture(t,{unknown:true});missing.ops.splice(0);
 await assert.rejects(missing.d.shutdownLocalResources(),{code:'HISTORICAL_OPERATION_REQUIRED'});assert.equal(missing.counts().closes,0);
 const foreign=await dispatcherFixture(t,{unknown:true});
 const ps=new ProtectedStore({directory:path.join(foreign.ds.dir,'project-p2vox'),create:false,now:foreign.now});
 ps.transact(s=>s.operations.push({...s.operations[0],id:'new-unconfirmed-operation',hash:'f'.repeat(64)}));ps.close();
 await assert.rejects(foreign.d.shutdownLocalResources(),{code:'UNPROVEN_EXECUTION_RISK'});assert.equal(foreign.counts().closes,0);
});
test('signed old UNKNOWN may not silently be upgraded to current release versions',async t=>{
 const f=await dispatcherFixture(t,{unknown:true,leaseVersions:{app:'a'.repeat(64),bridge:'b'.repeat(64),native:'c'.repeat(64)}});
 await assert.rejects(f.d.shutdownLocalResources(),{code:'HISTORICAL_LEASE_BINDING'});assert.equal(f.counts().closes,0);
});
test('hook timeout has no late resource close or writer release',async t=>{
 let wake;const hookWait=new Promise(r=>wake=r);const f=await dispatcherFixture(t,{hook:()=>hookWait});
 const p=f.d.shutdownLocalResources({timeoutMs:10});await assert.rejects(p,{code:'LOCAL_SHUTDOWN_TIMEOUT'});wake();await delay(20);
 assert.equal(f.counts().closes,0);assert.throws(()=>f.d.releaseStores(),{code:'RECOVERY_REQUIRED'});assert.equal(f.d.shutdownLocalResources(),p);
});
test('default close still refuses UNKNOWN rather than using local-only shutdown',async t=>{
 const f=await dispatcherFixture(t,{unknown:true});
 const proof=signed({schema:'r16.workspace-control.v1',id:'fixture-status',grantId:'r16-projects-daily',channel:'main',operation:'status',data:{projectId:'p2vox'},issuedAt:f.now(),expiresAt:f.now()+30000},f.roleKeys.app);
 await f.d.handle({command:'WorkspaceControl',proof});
 await assert.rejects(f.d.close(),{code:'RECOVERY_UNRESOLVED'});
 assert.equal(f.counts().closes,0);
 let local=0,legacy=0;const h=createHeadlessHost({port:{handle(){},refresh(){},async close(){legacy++;throw Object.assign(Error('RECOVERY_UNRESOLVED'),{code:'RECOVERY_UNRESOLVED'});},shutdownLocalResources(){local++;}},manifest:{name:'ProjectForge'},connect(){throw Error('unused');},acquireLease(){throw Error('unused');}});
 await assert.rejects(h.stop(),{code:'RECOVERY_REQUIRED'});assert.equal(legacy,1);assert.equal(local,0);
});
test('explicit headless local shutdown closes a real socket and releases real writer lease once',async t=>{
 const dir=temp(t),server=net.createServer();await new Promise(r=>server.listen(0,'127.0.0.1',r));t.after(()=>server.close());
 const accepted=new Promise(r=>server.once('connection',r));const socket=net.connect(server.address().port,'127.0.0.1');await new Promise(r=>socket.once('connect',r));const other=await accepted;
 t.after(()=>{socket.destroy();other.destroy();});let closeResolve;const closed=new Promise(r=>closeResolve=r);socket.on('close',closeResolve);
 const f=await dispatcherFixture(t);let refreshCalls=0;
 const port={...f.d,refresh:async()=>{refreshCalls++;return {status:'CONNECTED'};}};
 const host=createHeadlessHost({port,manifest:{name:'ProjectForge'},serverName:'fixture',connect:async()=>({closed,onMessage(){},send(){},async close(){socket.end();other.end();await closed;}}),acquireLease:()=>acquireProcessLease(dir)});
 await host.start();assert.ok(fs.existsSync(path.join(dir,'native-writer.lock')));const p=host.shutdownLocalResources();assert.equal(host.shutdownLocalResources(),p);const receipt=await p;
 assert.equal(receipt.globalExecution,'UNPROVEN');assert.equal(receipt.transportClosed,true);assert.equal(receipt.writerReleased,true);assert.equal(socket.destroyed,true);assert.equal(fs.existsSync(path.join(dir,'native-writer.lock')),false);assert.equal(refreshCalls,1);await assert.rejects(host.start(),{code:'RECOVERY_REQUIRED'});
});

test('full queued issuer await drains before local resource close; later queued allocation is fenced',async t=>{
 let wake,calls=0;const waiting=new Promise(r=>wake=r);
 const f=await dispatcherFixture(t,{issuerHeartbeat:async()=>{calls++;await waiting;return {status:'fixture-only'};}});
 const control=(name,data,id)=>f.d.handle({command:'WorkspaceControl',proof:signed({schema:'r16.workspace-control.v1',id,grantId:'r16-projects-daily',channel:'main',operation:name,data,issuedAt:f.now(),expiresAt:f.now()+30000},f.roleKeys.app)});
 const running=control('issuer',{operation:'heartbeat',params:{}},'running-heartbeat');
 await Promise.resolve();await Promise.resolve();assert.equal(calls,1);
 const queued=control('allocate',{},'later-allocation');const refusal=assert.rejects(queued,{code:'AUTHORITY_REJECTED'});
 const stopped=f.d.shutdownLocalResources();await Promise.resolve();assert.equal(f.counts().closes,0);
 wake();await running;await refusal;await stopped;
 assert.equal(f.ds.snapshot().controls.length,1);assert.equal(f.ds.snapshot().controls[0].status,'KNOWN');assert.deepEqual(f.ds.snapshot().pending,[]);assert.equal(f.counts().closes,1);
});
test('headless shares deadline with port and never releases writer after deferred stores exceed it',async t=>{
 let wake,released=0,received;const waiting=new Promise(r=>wake=r);
 const host=createHeadlessHost({port:{handle(){},async refresh(){return {status:'CONNECTED'};},close(){throw Error('strict-unused');},async shutdownLocalResources(options){received=options;return {scope:'LOCAL_ONLY'};},async releaseStores(options){assert.equal(options.signal,received.signal);await waiting;}},manifest:{name:'ProjectForge'},connect:async()=>({closed:new Promise(()=>{}),onMessage(){},send(){},async close(){}}),acquireLease:()=>({release(){released++;}}),shutdownMs:15});
 await host.start();const p=host.shutdownLocalResources();await assert.rejects(p,{code:'RECOVERY_REQUIRED'});assert.equal(received.signal.aborted,true);wake();await delay(10);assert.equal(released,0);assert.equal(host.shutdownLocalResources(),p);
});
