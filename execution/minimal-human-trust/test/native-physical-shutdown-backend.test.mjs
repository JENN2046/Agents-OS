// Opt-in actual installed public dependencies; never production state/config.
// CI portable tests live in native-physical-shutdown.test.mjs. This file requires
// the exact signed base and is NOT claimed as CI-covered when absent.
import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import {Module,createRequire} from 'node:module';
import {createHash,generateKeyPairSync,createPublicKey,randomUUID} from 'node:crypto';
import {ProtectedStore,signed,digest,exportPublicKey,ROLES,ACTIONS} from '../src/lease-core.mjs';
import {createWorkspaceDispatcher,dispatcherInitialState} from '../host/workspace-dispatcher.mjs';
import {createHeadlessHost,acquireProcessLease} from '../host/headless-host.mjs';
const BASE='/opt/r16/releases/r16-daily-20261015-r15-app-recovery-r6';
const REL='native/upstream/VCPDistributedServer/Plugin/ProjectForge/';
const enabled=process.env.R16_NATIVE_PHYSICAL_BACKEND==='1';
const sha=b=>createHash('sha256').update(b).digest('hex');
const candidate=relative=>fs.readFileSync(new URL('../'+relative,import.meta.url),'utf8');
function backend(t,{childIgnore=false}={}){
 const manifestBytes=fs.readFileSync(BASE+'/native-manifest.json');
 assert.equal(sha(manifestBytes),'2516e881b0622b3ac2d53c454e6ccf9950441c5cb3c26a53500b45d3b1dbe7b4');
 const manifest=JSON.parse(manifestBytes),extensions={...Module._extensions};
 for(const extension of ['.js','.json','.node']){
  Module._extensions[extension]=(mod,file)=>{
   if(file.startsWith(BASE+'/')){const rel=file.slice(BASE.length+1);assert.equal(sha(fs.readFileSync(file)),manifest.files[rel],'real dependency pin '+rel);}
   return extensions[extension](mod,file);
  };
 }
 t.after(()=>Object.assign(Module._extensions,extensions));
 const cjs=name=>{const filename=BASE+'/'+REL+name;const m=new Module(filename);m.filename=filename;m.paths=Module._nodeModulePaths(path.dirname(filename));return m;};
 const indexer=cjs('indexerClient.js');indexer._compile(candidate(REL+'indexerClient.js'),indexer.filename);
 const native=cjs('ProjectForgeService.js'),originalRequire=native.require.bind(native);
 native.require=request=>request==='./indexerClient'?indexer.exports:originalRequire(request);
 native._compile(candidate(REL+'ProjectForgeService.js'),native.filename);
 const dir=fs.mkdtempSync(path.join(os.tmpdir(),'native-actual-backend-'));fs.chmodSync(dir,0o700);
 const root=path.join(dir,'workspace');fs.mkdirSync(root,{mode:0o700});
 const bin=path.join(dir,'indexer');fs.writeFileSync(bin,`#!${process.execPath}\nconst rl=require('node:readline').createInterface({input:process.stdin});console.log(JSON.stringify({type:'ready',protocolVersion:2}));${childIgnore?"process.on('SIGTERM',()=>{});setInterval(()=>{},1000);":''}rl.on('line',line=>{const m=JSON.parse(line);if(m.method==='shutdown'){${childIgnore?'return;':"setTimeout(()=>process.exit(0),60);"}return;}console.log(JSON.stringify({id:m.id,ok:true,result:{hits:[]}}));});\n`,{mode:0o700});
 const db=path.join(dir,'project.sqlite'),workspace={id:'fixture-workspace',alias:'fixture',path:root};
 const n=native.exports;
 n.initialize({dbPath:db,indexerBinaryPath:bin,workspaceService:{list:()=>[{...workspace,enabled:true}],getActiveWorkspaceId:()=>workspace.id},config:{AST_INDEX_ENABLED:true},logger:{log(){},warn(){},error(){}}});
 const runtime=n._test.getRuntime();
 t.after(async()=>{
  for(const c of runtime.indexer.ownedChildren.keys())c.kill('SIGKILL');await Promise.all([...runtime.indexer.ownedChildren.values()]);
  try{runtime.store?.close();}catch{}try{runtime.writerLease?.close();}catch{}fs.rmSync(dir,{recursive:true,force:true});
 });
 assert.deepEqual(n.gui.listProjects(),[]); // Real SQLite store, not a substitute.
 const C=createRequire(native.filename)('./crownAuthority');
 const key=generateKeyPairSync('ed25519').privateKey,identity={logicalName:'ProjectForge',originKind:'distributed',originId:'fixture-native',originKey:'distributed:fixture-native:ProjectForge'};
 const engineArgs={publicKey:createPublicKey(key),callIdentity:identity,workspace,databasePath:db,validateAuthority(){},authorizeCall:p=>({authorized:true,trusted_client:true,explicit_intent:true,authorization_ref:p.authorization_ref,request_sha256:C.digest(p.request),target_sha256:C.digest(C.callTarget(p))})};
 const engine=n.createWorkspaceCrownPort(engineArgs);
 function call(){const now=Date.now(),body={audience:C.CALL_AUDIENCE,request_id:randomUUID(),issued_at:now,expires_at:now+10000,native_epoch:engine.callStatus().epoch,authorization_ref:'fixture-explicit-local-call',identity,binding:null,workspace:null,command:C.CALL_COMMANDS.list_workspaces,request:{action:'list_workspaces'},expected_version:null,mode:'execute',reconcile_id:null};return engine.handleCall({command:'CrownCall',proof:C.signCall(body,key)});}
 return {n,runtime,dir,db,engine,engineArgs,call,writer:db+'.r16-writer.lock'};
}

test('actual candidate engine + SQLite + real sidecar close before writer is released',{skip:!enabled},async t=>{
 const f=backend(t);assert.equal((await f.call()).status,'verified');
 assert.deepEqual(await f.runtime.indexer.findSymbols('/tmp'),{hits:[]});assert.equal(f.runtime.indexer.ownedChildren.size,1);assert.ok(fs.existsSync(f.writer));
 const before=Date.now(),local=await f.n.quiesceExecution();assert.ok(Date.now()-before>=40);assert.equal(local.globalExecution,'UNPROVEN');assert.equal(local.indexers[0].children.length,0);
 assert.throws(()=>f.n.createWorkspaceCrownPort(f.engineArgs),/AUTHORITY_UNAVAILABLE/);
 assert.ok(fs.existsSync(f.writer),'quiescence is before writer release');assert.equal(f.runtime.store.db.open,true);
 const p=f.n.cleanup();assert.equal(f.n.cleanup(),p);const result=await p;
 assert.equal(result.storeOpen,false);assert.equal(result.writerOpen,false);assert.equal(fs.existsSync(f.writer),false);
 assert.throws(()=>f.n.gui.listProjects(),/NATIVE_ADMISSION_CLOSED/);assert.throws(()=>f.n.initialize({dbPath:f.db}),/PROJECTFORGE_BUSY/);
});
test('actual engine async outer call prevents cleanup and leaves writer owned',{skip:!enabled},async t=>{
 const f=backend(t),call=f.call();assert.ok(f.n.physicalExecutionStatus().workspaceCalls>0);
 const p=f.n.cleanup();await assert.rejects(p,/NATIVE_CURRENT_WORK_BUSY/);await call;
 assert.equal(f.n.cleanup(),p);assert.ok(fs.existsSync(f.writer));assert.equal(f.runtime.store.db.open,true);
});
test('actual DB close failure preserves real store and real writer, without retry',{skip:!enabled},async t=>{
 const f=backend(t),store=f.runtime.store,close=store.close.bind(store);let calls=0;
 store.close=()=>{calls++;throw Object.assign(Error('private SQLite detail'),{code:'SQLITE_BUSY'});};
 const p=f.n.cleanup();await assert.rejects(p,{code:'SQLITE_BUSY'});assert.equal(f.n.cleanup(),p);assert.equal(calls,1);assert.equal(f.runtime.store,store);assert.equal(store.db.open,true);assert.ok(fs.existsSync(f.writer));store.close=close;
});
test('actual writer close failure never reports resource closure or loses handle',{skip:!enabled},async t=>{
 const f=backend(t),lease=f.runtime.writerLease;let calls=0;
 f.runtime.writerLease={current:lease.current,close(){calls++;throw Object.assign(Error('private lock detail'),{code:'LEASE_CHANGED'});}};
 const p=f.n.cleanup();await assert.rejects(p,{code:'LEASE_CHANGED'});assert.equal(f.n.cleanup(),p);assert.equal(calls,1);assert.ok(fs.existsSync(f.writer));assert.equal(f.n.physicalExecutionStatus().writerOpen,true);f.runtime.writerLease=lease;
});
test('actual deferred DB close crossing shared deadline never releases writer afterward',{skip:!enabled},async t=>{
 const f=backend(t),store=f.runtime.store,close=store.close.bind(store);let wake,writerCloses=0;
 const wait=new Promise(r=>wake=r),lease=f.runtime.writerLease;
 store.close=async()=>{await wait;close();};
 f.runtime.writerLease={current:lease.current,close(){writerCloses++;return lease.close();}};
 const abort=new AbortController(),deadline=Date.now()+25,monotonicDeadline=performance.now()+25;
 const p=f.n.cleanup({signal:abort.signal,deadline,monotonicDeadline});
 await new Promise(r=>setTimeout(r,35));abort.abort();wake();
 await assert.rejects(p,/NATIVE_CLEANUP_EXPIRED/);assert.equal(f.n.cleanup(),p);
 assert.equal(writerCloses,0);assert.ok(fs.existsSync(f.writer));assert.equal(f.runtime.store,store,'uncertain store handle retained, no false closed observation');
 store.close=close;f.runtime.writerLease=lease;
});

test('default strict host close shares real DB deadline; neither Native nor host writer releases late',{skip:!enabled},async t=>{
 const f=backend(t),store=f.runtime.store,originalClose=store.close.bind(store);let wake;
 const wait=new Promise(r=>wake=r);store.close=async()=>{await wait;originalClose();};
 const key=()=>generateKeyPairSync('ed25519').privateKey,issuer=key(),releaseKey=key(),roles=Object.fromEntries(ROLES.map(r=>[r,key()]));
 const root=path.join(f.dir,'workspace'),st=fs.statSync(root),workspace={id:'fixture-workspace',root,dev:st.dev,ino:st.ino},now=Date.now();
 const grant=signed({schema:'r16.workspace.v1',id:'fixture-grant',version:1,createdAt:now,workspace,actions:ACTIONS,channel:'main',peers:Object.fromEntries(ROLES.map(r=>[r,{id:'fixture-'+r,publicKey:exportPublicKey(roles[r])}]))},issuer);
 const versions={app:digest('a'),bridge:digest('b'),native:digest('n')},release=signed({schema:'r16.release.v1',id:'fixture-release',issuedAt:now,notAfter:now+30000,formats:['r16.workspace.v1'],versions,actions:ACTIONS,permissionVersion:1},releaseKey);
 const ds=new ProtectedStore({directory:path.join(f.dir,'dispatcher'),create:true,initial:dispatcherInitialState()});
 const dispatcher=createWorkspaceDispatcher({store:ds,directory:ds.dir,native:f.n,crown:{},grant,release,versions,signingKey:roles.native,issuerKey:exportPublicKey(issuer),releaseKey:exportPublicKey(releaseKey),issuer:{fresh(){}},workspaceAlias:'fixture',databasePath:f.db});
 const lease=acquireProcessLease(f.dir),host=createHeadlessHost({port:{...dispatcher,refresh:async()=>({status:'CONNECTED'})},manifest:{name:'ProjectForge'},connect:async()=>({closed:new Promise(()=>{}),onMessage(){},send(){},async close(){}}),acquireLease:()=>lease,shutdownMs:20});
 await host.start();const p=host.stop();await assert.rejects(p,{code:'RECOVERY_REQUIRED'});wake();await new Promise(r=>setTimeout(r,20));
 assert.ok(fs.existsSync(f.writer),'real Native writer remains');assert.ok(fs.existsSync(path.join(f.dir,'native-writer.lock')),'host writer remains');assert.equal(f.n.physicalExecutionStatus().writerOpen,true);
 assert.equal(host.stop(),p);store.close=originalClose;ds.close();lease.release();
});
