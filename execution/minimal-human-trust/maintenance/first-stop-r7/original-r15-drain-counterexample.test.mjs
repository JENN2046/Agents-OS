// Isolated counterexample using unchanged signed R15 host/core, synthetic keys
// and disposable stores. No network, production state, credentials or signals.
import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import {createHash,generateKeyPairSync} from 'node:crypto';

const BASE='/opt/r16/releases/r16-daily-20261012-r15';
const PINS={
  'app/workspace-host.mjs':'119756c7bb950308a1edb062b93c4848b5280e9ba356c13d6660f96b192915d2',
  'src/lease-core.mjs':'889232f53d5c014138a7004df32c8e4f4f6c16703b6d53fa75ce0cbcf53e43b9',
  'app/app-runner.mjs':'9fa13d0fe708d62e8ec34db680212d9d1857014c4e08bbaf1b00c60c8f602737',
  'src/control-clock.mjs':'b94a364ff6738c9c924c41f9ec164234612f6803e2feee77acde24bde6fa89b1',
};
const sha=raw=>createHash('sha256').update(raw).digest('hex');

test('original R15 close rejection is not a drain barrier: an already admitted allocation writes and dispatches afterward',async t=>{
  assert.notEqual(process.geteuid(),0,'non-privileged disposable fixture only');
  for(const [name,pin] of Object.entries(PINS))assert.equal(sha(fs.readFileSync(BASE+'/'+name)),pin);
  const {ProtectedStore,signed,digest,exportPublicKey,ACTIONS}=await import(BASE+'/src/lease-core.mjs');
  const {createWorkspaceHost,appHostInitialState}=await import(BASE+'/app/workspace-host.mjs');
  const root=fs.mkdtempSync(path.join(os.tmpdir(),'r15-drain-counterexample-'));
  fs.chmodSync(root,0o700);
  let store;
  t.after(()=>{try{store?.close();}catch{}fs.rmSync(root,{recursive:true,force:true});});
  const now=Date.now(),keys=Object.fromEntries(['issuer','release','app','bridge','native'].map(r=>[r,generateKeyPairSync('ed25519').privateKey]));
  const stat=fs.statSync(root),workspace={id:'synthetic-ws',root,dev:stat.dev,ino:stat.ino};
  const peers=Object.fromEntries(['app','bridge','native'].map(r=>[r,{id:'synthetic-'+r,publicKey:exportPublicKey(keys[r])}]));
  const grant=signed({schema:'r16.workspace.v1',id:'synthetic-grant',version:1,createdAt:now-1000,workspace,actions:ACTIONS,channel:'main',peers},keys.issuer);
  const versions=Object.fromEntries(['app','bridge','native'].map(r=>[r,digest(r)]));
  const release=signed({schema:'r16.release.v1',id:'synthetic-release',issuedAt:now-1000,notAfter:now+600000,formats:['r16.workspace.v1'],versions,actions:ACTIONS,permissionVersion:1},keys.release);
  const initial=appHostInitialState();
  // Deliberately synthetic host-level history is sufficient to reach the same
  // RECOVERY_UNRESOLVED guard. This is not a copy of either real project ledger.
  initial.operations=[{id:'synthetic-old-unresolved',projectId:'synthetic-legacy',status:'UNKNOWN'}];
  initial.allocations=[{id:'synthetic-old-allocation',status:'UNKNOWN',proof:{synthetic:true}}];
  store=new ProtectedStore({directory:root+'/state',create:true,initial});
  let transport,entered,releaseWait,closeFinished=false,postCloseRpcCount=0;
  const reached=new Promise(resolve=>{entered=resolve;}),held=new Promise(resolve=>{releaseWait=resolve;});
  const host=createWorkspaceHost({store,directory:store.dir,grant,release,versions,signingKey:keys.app,
    issuerKey:exportPublicKey(keys.issuer),releaseKey:exportPublicKey(keys.release),channelCapability:Buffer.alloc(32,1),
    crown:{},createCrownExecutor:options=>{transport=options.transport;return Object.assign(()=>{}, {close(){}});},
    exchange:async(_target,payload)=>{
      const body=payload.proof.body;
      if(body.operation==='control_status'){
        entered();await held;
        return signed({schema:'r16.workspace-control-result.v1',id:body.id,operation:body.operation,ok:true,result:{status:'NOT_EXECUTED'}},keys.native);
      }
      assert.equal(body.operation,'allocate');assert.equal(closeFinished,true);
      postCloseRpcCount++;
      throw Object.assign(Error('SYNTHETIC_OFFLINE'),{code:'NATIVE_OFFLINE'});
    }});
  const running=transport.allocateProject({request:{action:'create_project'},workspace:{id:workspace.id,path:workspace.root}});
  await reached;
  await assert.rejects(host.close(),{code:'RECOVERY_UNRESOLVED'});
  closeFinished=true;
  const afterClose=store.snapshot(),previousHash=digest(afterClose);
  releaseWait();
  await assert.rejects(running,{code:'NATIVE_OFFLINE'});
  const afterLateWork=store.snapshot();
  assert.equal(postCloseRpcCount,1);
  assert.equal(afterLateWork.allocations.length,2);
  assert.equal(afterLateWork.allocations[0].status,'NOT_EXECUTED');
  assert.equal(afterLateWork.allocations[1].status,'UNKNOWN');
  assert.notEqual(digest(afterLateWork),previousHash);
  assert.deepEqual(afterLateWork.operations,afterClose.operations);
  await assert.rejects(transport.describe(),{code:'RECOVERY_UNRESOLVED'});
});
