import './r15-app-shutdown-backport.test.mjs';
import './maintenance-transaction-recovery.test.mjs';
import './maintenance-os-regression.test.mjs';
import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {generateKeyPairSync,randomUUID} from 'node:crypto';
import {ProtectedStore,signed,verified,digest,exportPublicKey,ACTIONS} from '../src/lease-core.mjs';
import {establishBusinessStop} from '../src/runtime-business-stop.mjs';
import {createWorkspaceHost,appHostInitialState} from '../app/workspace-host.mjs';
import {createWorkspaceBridge,bridgeInitialState,calculateRuntimeVersion} from '../bridge/workspace-private-router.mjs';

const key=()=>generateKeyPairSync('ed25519').privateKey;
function fixture(t,{expired=true}={}){
 const directory=fs.mkdtempSync(path.join(os.tmpdir(),'g1d-recovery-shutdown-'));fs.chmodSync(directory,0o700);
 const now=1792000000000,keys=Object.fromEntries(['issuer','release','app','bridge','native'].map(k=>[k,key()]));
 const peers=Object.fromEntries(['app','bridge','native'].map(role=>[role,{id:'p-'+role,publicKey:exportPublicKey(keys[role])}]));
 const grant=signed({schema:'r16.workspace.v1',id:'isolated-grant',version:1,createdAt:now-60000,
  workspace:{id:'isolated-ws',root:directory,dev:fs.statSync(directory).dev,ino:fs.statSync(directory).ino},
  actions:ACTIONS,channel:'main',peers},keys.issuer);
 const runtimeFiles={'workspace-private-router.mjs':fileURLToPath(new URL('../bridge/workspace-private-router.mjs',import.meta.url))};
 const versions={app:digest('app-runtime'),bridge:calculateRuntimeVersion(runtimeFiles),native:digest('native-runtime')};
 const release=signed({schema:'r16.release.v1',id:'r16-test-r15',issuedAt:now-60000,
  notAfter:expired?now-1:now+60000,formats:['r16.workspace.v1'],versions,actions:ACTIONS,permissionVersion:1},keys.release);
 const stores=[];
 const make=(name,initial)=>{
  const s=new ProtectedStore({directory:path.join(directory,name),create:true,initial,now:()=>now});
  stores.push(s);return s;
 };
 t.after(()=>{for(const s of stores)try{s.close();}catch{}fs.rmSync(directory,{recursive:true,force:true});});
 const common={directory,grant,release,versions,issuerKey:exportPublicKey(keys.issuer),
  releaseKey:exportPublicKey(keys.release),now:()=>now};
 const crown={verifyCall:()=>{},identityCheck:()=>{}};
 const wss={getDistributedServerSnapshot:()=>[{connected:true,serverId:'node-1',tools:['ProjectForge']}]};
 const plugins=new Map([['ProjectForge',{isDistributed:true,serverId:'node-1'}]]);
 const bridgeArgs=(store,processToolCall=async()=>{})=>({...common,store,signingKey:keys.bridge,crown,
  pluginManager:{plugins,processToolCall},wss,runtimeFiles});
 const appArgs=store=>({...common,store,signingKey:keys.app,channelCapability:Buffer.alloc(32,1),
   crown,createCrownExecutor:()=>Object.assign(()=>{}, {close(){}}),exchange:async()=>{}});
 return {now,keys,peers,grant,release,versions,stores,make,bridgeArgs,appArgs};
}
const refusal=f=>assert.throws(f);
test('expired R15 App with durable stopped journal may reopen only to reconcile, never new business',async t=>{
 const f=fixture(t),store=f.make('app',appHostInitialState());
 establishBusinessStop(store,'single-recovery-epoch');
 const app=createWorkspaceHost(f.appArgs(store));
 const reconciled=await app.reconcileStopped();
 assert.deepEqual(reconciled,[]);
 refusal(()=>app.runtimeDependencies.resolveProjectForgeCrownContext({}),);
 await app.close();
});
test('expired R15 App with completely empty history cannot masquerade as recovery',t=>{
 const f=fixture(t),store=f.make('app',appHostInitialState());
 assert.throws(()=>createWorkspaceHost(f.appArgs(store)),{code:'RECOVERY_ONLY_REQUIRED'});
});
test('expired R15 Bridge with business stop may process signed cleanup but never new control',async t=>{
 const f=fixture(t),store=f.make('bridge',bridgeInitialState());
 establishBusinessStop(store,'same-epoch');
 let nativeCalls=0;
 const b=createWorkspaceBridge(f.bridgeArgs(store,async()=>{nativeCalls++;return {};}));
 const payload={command:'WorkspaceControl',proof:signed({schema:'r16.workspace-control.v1',id:randomUUID(),
  grantId:f.grant.body.id,channel:'main',operation:'activate',data:{},issuedAt:f.now,expiresAt:f.now+30000},f.keys.app)};
 const route=signed({schema:'r16.workspace-route.v1',id:randomUUID(),target:'native',
  payloadHash:digest(payload),issuedAt:f.now,expiresAt:f.now+30000},f.keys.app);
 await assert.rejects(()=>b.exchange({route,payload}),{code:'BUSINESS_STOPPED'});
 assert.equal(nativeCalls,0);
 await b.close();
});
test('expired R15 Bridge with nonstopped old project refuses new WorkspaceControl activation',async t=>{
 const f=fixture(t),store=f.make('bridge',bridgeInitialState());
 store.transact(s=>{s.projects=['existing-recovery-project'];});
 let nativeCalls=0;
 const b=createWorkspaceBridge(f.bridgeArgs(store,async()=>{nativeCalls++;return {};}));
 const payload={command:'WorkspaceControl',proof:signed({schema:'r16.workspace-control.v1',id:randomUUID(),
  grantId:f.grant.body.id,channel:'main',operation:'activate',data:{},issuedAt:f.now,expiresAt:f.now+30000},f.keys.app)};
 const route=signed({schema:'r16.workspace-route.v1',id:randomUUID(),target:'native',
  payloadHash:digest(payload),issuedAt:f.now,expiresAt:f.now+30000},f.keys.app);
 await assert.rejects(()=>b.exchange({route,payload}),{code:'RELEASE_EXPIRED'});
 assert.equal(nativeCalls,0);
 // Avoid creating non-existing participant store for arbitrary legacy project;
 // this test checks only admission; caller cleans the opened top-level journal.
 store.close();
});
test('Bridge close waits for entire WorkspaceControl route to archive after remote completion',async t=>{
 const f=fixture(t,{expired:false}),store=f.make('bridge',bridgeInitialState());
 let entered;
 const started=new Promise(resolve=>{entered=resolve;});
 let resume;
 const blocked=new Promise(resolve=>{resume=resolve;});
 const statusResult={answer:'durable'};
 const b=createWorkspaceBridge(f.bridgeArgs(store,async(_name,input)=>{
  entered();await blocked;
  return signed({schema:'r16.workspace-control-result.v1',id:input.proof.body.id,
   operation:input.proof.body.operation,ok:true,result:statusResult},f.keys.native);
 }));
 const proof=signed({schema:'r16.workspace-control.v1',id:randomUUID(),
   grantId:f.grant.body.id,channel:'main',operation:'status',data:{},
   issuedAt:f.now,expiresAt:f.now+30000},f.keys.app);
 const payload={command:'WorkspaceControl',proof};
 const route=signed({schema:'r16.workspace-route.v1',id:randomUUID(),
   target:'native',payloadHash:digest(payload),issuedAt:f.now,expiresAt:f.now+30000},f.keys.app);
 const exchange=b.exchange({route,payload});
 await started;
 let closed=false;
 const close=b.close().then(()=>{closed=true;});
 await Promise.resolve();
 assert.equal(closed,false);
 await assert.rejects(()=>b.exchange({route,payload}),{code:'SERVICE_STOPPING'});
 resume();
 const response=await exchange;
 assert.deepEqual(verified(response,exportPublicKey(f.keys.bridge),'r16.workspace-route-result.v1').result.body.result,statusResult);
 await close;
 assert.equal(closed,true);
 const reopened=new ProtectedStore({directory:store.dir,create:false,now:()=>f.now});
 try{
  const archived=reopened.archived('bridge-route-'+digest(route.body.id));
  assert.equal(archived.status,'KNOWN');
  assert.deepEqual(archived.response,response);
  assert.equal(reopened.snapshot().routes.find(r=>r.id===route.body.id).status,'KNOWN');
 }finally{reopened.close();}
});

import "./app-os-shutdown.test.mjs";

import "./fixtures/release-r6-regression.mjs";

import "./fixtures/first-stop-r7-regression.mjs";

import "./fixtures/first-stop-r8-regression.mjs";

import "./fixtures/empty-temp-quarantine-r1-regression.mjs";

import "./fixtures/recovery-r9-regression.mjs";
