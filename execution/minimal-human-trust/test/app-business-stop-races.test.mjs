import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import {generateKeyPairSync,randomUUID} from 'node:crypto';
import {ProtectedStore,createIssuer,issuerInitialState,signed,exportPublicKey,digest,ACTIONS} from '../src/lease-core.mjs';
import {createWorkspaceHost,appHostInitialState} from '../app/workspace-host.mjs';
import * as crown from '/home/jenn/AGENTS_OS_Workspace/projects/vcp-app-r16-working-source-r2/src/project-forge-crown-transport.mjs';
function setup(t){
 const root=fs.mkdtempSync(path.join(os.tmpdir(),'g1d-stop-app-race-'));fs.chmodSync(root,0o700);
 const workspaceRoot=path.join(root,'projects');fs.mkdirSync(workspaceRoot,{mode:0o700});const st=fs.statSync(workspaceRoot);
 const workspace={id:'ws',root:workspaceRoot,dev:st.dev,ino:st.ino},project={id:'project',workspaceId:'ws',root:path.join(workspaceRoot,'project')};fs.mkdirSync(project.root,{mode:0o700});
 const keys=Object.fromEntries(['issuer','release','app','bridge','native'].map(role=>[role,generateKeyPairSync('ed25519').privateKey]));
 const peers=Object.fromEntries(['app','bridge','native'].map(role=>[role,{id:'peer-'+role,publicKey:exportPublicKey(keys[role])}]));
 const now=()=>1791859000000;
 const issuerStore=new ProtectedStore({directory:path.join(root,'issuer'),create:true,initial:issuerInitialState(),now});
 const issuer=createIssuer({store:issuerStore,signingKey:keys.issuer,releaseKey:exportPublicKey(keys.release),authorizeOwner:()=>true,resolveProject:(_w,p)=>p});
 const grant=issuer.createGrant({approval:{synthetic:true},grant:{id:'grant',workspace,actions:ACTIONS.slice(),channel:'main',peers}});
 const versions=Object.fromEntries(['app','bridge','native'].map(r=>[r,digest(r)]));
 const release=signed({schema:'r16.release.v1',id:'release',issuedAt:now(),notAfter:now()+86400000,formats:['r16.workspace.v1'],versions,actions:ACTIONS.slice(),permissionVersion:1},keys.release);
 const store=new ProtectedStore({directory:path.join(root,'app'),create:true,initial:appHostInitialState(),now});
 let captured,rawExecutor,releaseControl,notify;const entered=new Promise(resolve=>{notify=resolve;});const calls=[];
 const app=createWorkspaceHost({store,directory:store.dir,grant,release,versions,signingKey:keys.app,issuerKey:exportPublicKey(keys.issuer),releaseKey:exportPublicKey(keys.release),channelCapability:Buffer.alloc(32,65),crown,now,
  createCrownExecutor:options=>{captured=options;const execute=async()=>{throw Error('NOT_AN_EXECUTOR_TEST');};execute.close=()=>{};execute.resolvePending=(...args)=>args;execute.pending=()=>[];execute.reconcile=async(...args)=>args;Object.defineProperty(execute,'requiresTrustedContext',{value:true});rawExecutor=execute;return execute;},
  exchange:async(target,payload)=>{assert.equal(target,'native');const c=payload.proof.body;calls.push(c.operation);notify();return new Promise(resolve=>{releaseControl=result=>resolve(signed({schema:'r16.workspace-control-result.v1',id:c.id,operation:c.operation,ok:true,result},keys.native));});}
 });
 t.after(async()=>{await app.close();issuerStore.close();fs.rmSync(root,{recursive:true,force:true});});
 return {app,store,workspace,project,captured,rawExecutor,calls,entered,release:result=>releaseControl(result)};
}
test('stop during allocation recovery refuses evidence while live and never sends new allocation afterwards',async t=>{
 const f=setup(t),id=randomUUID();f.store.transact(s=>s.allocations.push({id,status:'UNKNOWN',proof:{synthetic:'not replayed'}}));
 const work=f.captured.transport.allocateProject({request:{action:'create_project'},workspace:{id:f.workspace.id,path:f.workspace.root,alias:'projects'}});
 await f.entered;assert.deepEqual(f.calls,['control_status']);
 f.app.suspendBusiness({stopEpoch:'stop-during-allocation'});
 assert.throws(()=>f.app.businessStopEvidence({revision:88,reviewDigest:digest('review')}),{code:'STOP_BUSY'});
 const rejection=assert.rejects(work,{code:'GRANT_REVOKED'});f.release({status:'NOT_EXECUTED'});await rejection;
 assert.deepEqual(f.calls,['control_status']);assert.equal(f.store.snapshot().allocations.length,1);
 assert.equal(f.store.snapshot().allocations[0].status,'NOT_EXECUTED');
 const evidence=f.app.businessStopEvidence({revision:88,reviewDigest:digest('review')});assert.equal(evidence.body.inflight,0);
});
test('stop during admission resolve tracks live control and prevents post-await participant preparation',async t=>{
 const f=setup(t);const work=f.captured.admission.authorize({channel:'main'},{request_id:randomUUID(),request:{action:'get_project',project_id:f.project.id}});
 await f.entered;assert.deepEqual(f.calls,['resolve']);f.app.suspendBusiness({stopEpoch:'stop-during-admission'});
 assert.throws(()=>f.app.businessStopEvidence({revision:88,reviewDigest:digest('review')}),{code:'STOP_BUSY'});
 const rejection=assert.rejects(work,{code:'GRANT_REVOKED'});f.release({project:f.project,pending:false});await rejection;
 assert.deepEqual(f.calls,['resolve']);assert.deepEqual(f.store.snapshot().projects,[]);
 assert.equal(f.app.businessStopEvidence({revision:88,reviewDigest:digest('review')}).body.inflight,0);
});

test('lifecycle wrapper preserves hidden trusted-context marker and every public executor method',async t=>{
 const f=setup(t),executor=f.app.executor;
 assert.deepEqual(Object.getOwnPropertyDescriptor(executor,'requiresTrustedContext'),Object.getOwnPropertyDescriptor(f.rawExecutor,'requiresTrustedContext'));
 assert.equal(executor.requiresTrustedContext,true);assert.equal(Object.keys(executor).includes('requiresTrustedContext'),false);
 for(const name of ['pending','resolvePending','close'])assert.equal(executor[name],f.rawExecutor[name]);
 assert.deepEqual(executor.pending(),[]);assert.deepEqual(executor.resolvePending('id',{fixture:true}),['id',{fixture:true}]);
 assert.deepEqual(await executor.reconcile('id',{trustedContext:'fixture'}),['id',{trustedContext:'fixture'}]);
});
