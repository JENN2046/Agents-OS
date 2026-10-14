import {test} from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import {generateKeyPairSync} from 'node:crypto';
import {spawnSync} from 'node:child_process';
import {ProtectedStore,issuerInitialState,participantInitialState,createIssuer,createParticipant,exportPublicKey,signed,verified,digest,ROLES,ACTIONS,LEASE_MS,RENEW_BEFORE_MS,unavailableReadResult,READ_RESULT_LOSS_ACTIONS,resolveRegisteredProject,resolveProjectFile} from '../src/lease-core.mjs';
const key=()=>generateKeyPairSync('ed25519').privateKey;
function fixture(t) {
  const dir=fs.mkdtempSync(path.join(os.tmpdir(),'r16-lease-test-'));fs.chmodSync(dir,0o700);
  let time=1791630000000; const now=()=>time, advance=ms=>{time+=ms;}; const stores=[];
  t.after(()=>{for(const s of stores)s.close();fs.rmSync(dir,{recursive:true,force:true});});
  const issuerKey=key(),releaseKey=key(),peerKeys=Object.fromEntries(ROLES.map(r=>[r,key()]));
  const workspaceRoot=path.join(dir,'projects');fs.mkdirSync(workspaceRoot,{mode:0o700});const wsStat=fs.statSync(workspaceRoot);
  const workspace={id:'projects',root:workspaceRoot,dev:wsStat.dev,ino:wsStat.ino};
  const project={id:'pvjul',workspaceId:'projects',root:path.join(workspaceRoot,'todo')};fs.mkdirSync(project.root,{mode:0o700});
  const registry=new Map([[project.id,project]]);const resolver=(w,p)=>resolveRegisteredProject(w,p,id=>registry.get(id));
  const peers=Object.fromEntries(ROLES.map(r=>[r,{id:'device-'+r,publicKey:exportPublicKey(peerKeys[r])}]));
  const versions=Object.fromEntries(ROLES.map(r=>[r,digest(r)]));const approval={opaque:true};
  function store(name,initial,extra={}) {const result=new ProtectedStore({directory:path.join(dir,name),create:true,initial,now,...extra});stores.push(result);return result;}
  const issuerStore=store('issuer',issuerInitialState());
  const issuer=createIssuer({store:issuerStore,signingKey:issuerKey,releaseKey:exportPublicKey(releaseKey),authorizeOwner:x=>x.approval===approval,resolveProject:resolver});
  const grantInput={id:'grant-one',workspace,actions:ACTIONS.slice(),channel:'owner-main',peers};
  const grant=issuer.createGrant({approval,grant:grantInput});
  const release=signed({schema:'r16.release.v1',id:'release-one',issuedAt:time,notAfter:time+30*24*LEASE_MS,formats:['r16.workspace.v1'],versions,actions:ACTIONS.slice(),permissionVersion:1},releaseKey);
  const peerStores=Object.fromEntries(ROLES.map(r=>[r,store(r,participantInitialState(r))]));
  const peersApi=Object.fromEntries(ROLES.map(r=>[r,createParticipant({store:peerStores[r],role:r,signingKey:peerKeys[r],issuerKey:exportPublicKey(issuerKey),releaseKey:exportPublicKey(releaseKey),resolveProject:resolver})]));
  function connect(r) {peersApi[r].pair({grant});const request=peersApi[r].freshRequest(grant.body.id);const response=issuer.fresh({request});return peersApi[r].acceptFresh({response,grant});}
  for(const r of ROLES)connect(r);
  let seq=0,lease;
  function requestFor(p=project,actions=ACTIONS.slice()) {return {schema:'r16.prepare.v1',requestId:'request-'+(++seq),grantId:grant.body.id,grantVersion:grant.body.version,project:p,channel:grant.body.channel,versions,actions,issuedAt:now()};}
  function prepare(request=requestFor(),releaseOverride=release) {const proofs=Object.fromEntries(ROLES.map(r=>[r,signed(request,peerKeys[r])]));lease=issuer.prepare({grantId:grant.body.id,request,proofs,release:releaseOverride});return {lease,request,proofs};}
  function stage(l=lease) {for(const r of ROLES)peersApi[r].prepare({lease:l,grant,release});}
  function evidence() {return Object.fromEntries(ROLES.map(r=>[r,peersApi[r].closeEvidence()]));}
  function activate(e=evidence()) {const activation=issuer.activate({grantId:grant.body.id,projectId:lease.body.project.id,evidence:e});for(const r of ROLES)peersApi[r].activate({activation});return activation;}
  function start() {prepare();stage();activate();return lease;}
  function operation(id='operation-one',action='edit_code') {return signed({schema:'r16.operation.v1',id,grantId:grant.body.id,projectId:project.id,generation:lease.body.generation,leaseHash:digest(lease),channel:grant.body.channel,action,payloadHash:digest({request:{action,path:'index.html'},binding:project.id})},peerKeys.app);}
  function execute(op=operation()) {for(const r of ROLES)assert.equal(peersApi[r].begin({operation:op}).decision,'EXECUTE');const receipt=peersApi.native.complete({operationId:op.body.id,outcome:'COMPLETED',resultHash:digest({nodeId:'n1',batchId:'b1'})});for(const r of ['app','bridge'])peersApi[r].reconcile({receipt});return receipt;}
  return {dir,now,advance,store,stores,issuer,issuerStore,issuerKey,releaseKey,peerKeys,peerStores,peersApi,workspace,project,registry,versions,grant,grantInput,approval,release,resolver,connect,requestFor,prepare,stage,evidence,activate,start,operation,execute,get lease(){return lease;}};
}
const rejects=(fn,code)=>assert.throws(fn,e=>e.code===code);

test('prepare status returns original durable lease after response loss, including revoked cleanup',t=>{
 const f=fixture(t),prepared=f.prepare(),params={grantId:f.grant.body.id,request:prepared.request,proofs:prepared.proofs,release:f.release};
 f.advance(61000);f.issuer.revoke({approval:f.approval,grantId:f.grant.body.id});
 const before=f.issuer.snapshot(),response=f.issuer.prepareStatus({...params,queryId:'status-one',queryIssuedAt:f.now()});
 const body=verified(response,exportPublicKey(f.issuerKey),'r16.prepare-status.v1');
 assert.equal(body.state,'PREPARED');assert.equal(body.queryId,'status-one');assert.equal(body.requestHash,digest(prepared.request));assert.deepEqual(body.lease,prepared.lease);assert.deepEqual(f.issuer.snapshot(),before);
 rejects(()=>f.issuer.prepareStatus({...params,queryId:'status-two',queryIssuedAt:f.now()-30001}),'STALE_QUERY');
});
test('signed NOT_ISSUED requires closed issuance window, binds fresh query and rejects late prepare',t=>{
 const f=fixture(t),request=f.requestFor(),proofs=Object.fromEntries(ROLES.map(r=>[r,signed(request,f.peerKeys[r])])),params={grantId:f.grant.body.id,request,proofs,release:f.release};
 rejects(()=>f.issuer.prepareStatus({...params,queryId:'query-early',queryIssuedAt:f.now()}),'PREPARE_WINDOW_OPEN');
 f.advance(60001);const before=f.issuer.snapshot(),response=f.issuer.prepareStatus({...params,queryId:'query-current',queryIssuedAt:f.now()});
 const body=verified(response,exportPublicKey(f.issuerKey),'r16.prepare-status.v1');assert.equal(body.state,'NOT_ISSUED');assert.equal(body.lease,null);assert.equal(body.queryId,'query-current');assert.equal(body.issuedAt,f.now());assert.deepEqual(f.issuer.snapshot(),before);
 rejects(()=>f.issuer.prepare(params),'STALE_REQUEST');
 const bad={...proofs,native:proofs.app};rejects(()=>f.issuer.prepareStatus({...params,proofs:bad,queryId:'query-forged',queryIssuedAt:f.now()}),'BAD_SIGNATURE');
 const conflict={...request,channel:'another'};rejects(()=>f.issuer.prepareStatus({...params,request:conflict,queryId:'query-conflict',queryIssuedAt:f.now()}),'PAIRING_FAILED');
 f.advance(-2);rejects(()=>f.issuer.prepare(params),'CLOCK_ROLLBACK');
});

test('three signed endpoints activate, execute exactly once, and renew twice past old two-day cutoff',t=>{
  const f=fixture(t);f.start();f.execute();
  assert.equal(f.peersApi.native.begin({operation:f.operation()}).decision,'KNOWN');
  for(let i=0;i<2;i++){f.advance(LEASE_MS-RENEW_BEFORE_MS);f.prepare();f.stage();f.activate();f.execute(f.operation('operation-'+i));}
  f.advance(2*24*LEASE_MS);rejects(()=>f.peersApi.native.begin({operation:f.operation('expired')}),'LEASE_EXPIRED');
  f.prepare();f.stage();f.activate();f.execute(f.operation('past-trial-cutoff'));
  assert.equal(f.peersApi.native.status().generation,4);
});
test('an in-flight or UNKNOWN operation blocks close; only verified native result reconciles it',t=>{
  const f=fixture(t);f.start();const op=f.operation();for(const r of ROLES)f.peersApi[r].begin({operation:op});
  f.advance(2700000);f.prepare();f.stage();rejects(()=>f.peersApi.native.closeEvidence(),'RECOVERY_UNRESOLVED');
  assert.equal(f.peersApi.native.begin({operation:op}).decision,'UNKNOWN');
  rejects(()=>f.peersApi.app.complete({operationId:op.body.id,outcome:'COMPLETED',resultHash:digest({})}),'NATIVE_RESULT_REQUIRED');
  const receipt=f.peersApi.native.complete({operationId:op.body.id,outcome:'COMPLETED',resultHash:digest({known:true})});
  for(const r of ['app','bridge'])f.peersApi[r].reconcile({receipt});f.activate();
});
test('new prepared leases cannot write; stale, missing, wrong-role, and forged close evidence reject',t=>{
  const f=fixture(t);f.prepare();f.stage();rejects(()=>f.peersApi.native.begin({operation:f.operation()}),'NOT_ACTIVE');const e=f.evidence();
  rejects(()=>f.issuer.activate({grantId:f.grant.body.id,projectId:f.project.id,evidence:{...e,native:e.app}}),'BAD_SIGNATURE');
  const forged=structuredClone(e);forged.native.body.durableClosed=false;rejects(()=>f.issuer.activate({grantId:f.grant.body.id,projectId:f.project.id,evidence:forged}),'BAD_SIGNATURE');
  f.activate(e);f.advance(2700000);f.prepare();f.stage();rejects(()=>f.issuer.activate({grantId:f.grant.body.id,projectId:f.project.id,evidence:e}),'CLOSE_EVIDENCE');
});
test('activation response loss is idempotent at issuer and participants; cannot reopen old generation',t=>{
  const f=fixture(t);f.prepare();f.stage();const e=f.evidence();const first=f.activate(e);assert.deepEqual(f.issuer.activate({grantId:f.grant.body.id,projectId:f.project.id,evidence:e}),first);
  assert.equal(f.peersApi.native.activate({activation:first}).generation,1);
  f.advance(2700000);f.prepare();f.stage();f.activate();rejects(()=>f.peersApi.native.activate({activation:first}),'CLOSE_REQUIRED');
});
test('revocation is durable, all roles ACK stop, fresh connection cannot use cached old grant',t=>{
  const f=fixture(t);f.start();f.issuer.revoke({approval:f.approval,grantId:f.grant.body.id});
  for(const r of ROLES){f.peersApi[r].disconnect();rejects(()=>f.peersApi[r].begin({operation:f.operation('blocked-'+r)}),'RECONNECT_REQUIRED');assert.equal(f.connect(r).status,'REVOKED');const result=f.issuer.acknowledgeRevocation({proof:f.peersApi[r].revocationAck()});if(r==='native')assert.equal(result.status,'REVOKED');}
  const req=f.requestFor();rejects(()=>f.prepare(req),'GRANT_REVOKED');assert.equal(f.issuer.snapshot().grants[0].version,2);
  rejects(()=>f.issuer.createGrant({approval:{opaque:true},grant:{...f.grantInput,id:'extra'}}),'OWNER_REQUIRED');
});
test('offline participant loses new-operation authority by one hour, but authenticated result cleanup remains',t=>{
  const f=fixture(t);f.start();const op=f.operation();for(const r of ROLES)f.peersApi[r].begin({operation:op});f.issuer.revoke({approval:f.approval,grantId:f.grant.body.id});f.advance(LEASE_MS);
  rejects(()=>f.peersApi.native.begin({operation:f.operation('new-after-expiry')}),'LEASE_EXPIRED');
  const receipt=f.peersApi.native.complete({operationId:op.body.id,outcome:'COMPLETED',resultHash:digest('actual-history')});f.peersApi.app.reconcile({receipt});assert.equal(f.peersApi.app.receipt(op.body.id).body.outcome,'COMPLETED');
});
test('restart invalidates cached fresh and converts interrupted operations to UNKNOWN without executing again',t=>{
  const f=fixture(t);f.start();const op=f.operation();f.peersApi.native.begin({operation:op});
  const api=createParticipant({store:f.peerStores.native,role:'native',signingKey:f.peerKeys.native,issuerKey:exportPublicKey(f.issuerKey),releaseKey:exportPublicKey(f.releaseKey),resolveProject:f.resolver});
  assert.equal(api.status().connected,false);assert.equal(api.begin({operation:op}).decision,'UNKNOWN');rejects(()=>api.begin({operation:f.operation('new')}),'RECONNECT_REQUIRED');
});
test('replay with same ID but different payload is refused and no repeated execution occurs',t=>{
  const f=fixture(t);f.start();const op=f.operation();f.peersApi.native.begin({operation:op});const different=signed({...op.body,payloadHash:digest('different')},f.peerKeys.app);
  rejects(()=>f.peersApi.native.begin({operation:different}),'OPERATION_CONFLICT');assert.equal(f.peersApi.native.begin({operation:op}).decision,'UNKNOWN');
});
test('unapproved release/signature, scope expansion, peer impersonation, and stale request fail closed',t=>{
  const f=fixture(t);const req=f.requestFor();const badRelease=signed(f.release.body,key());rejects(()=>f.prepare(req,badRelease),'BAD_SIGNATURE');
  const broad={...req,actions:['shell']};rejects(()=>f.prepare(broad),'INVALID_INPUT');
  const wrong={...req,channel:'another'};rejects(()=>f.prepare(wrong),'CHANNEL_MISMATCH');
  const stale={...req,issuedAt:f.now()-60001};rejects(()=>f.prepare(stale),'STALE_REQUEST');
  const proofs=Object.fromEntries(ROLES.map(r=>[r,signed(req,f.peerKeys.app)]));rejects(()=>f.issuer.prepare({grantId:f.grant.body.id,request:req,proofs,release:f.release}),'BAD_SIGNATURE');
});
test('pending allocation is narrowed to create_project, normal lease can only narrow signed grant',t=>{
  const f=fixture(t);const p={...f.project,id:'pending-abc',root:path.join(f.workspace.root,'pending')};fs.mkdirSync(p.root);f.registry.set(p.id,p);
  rejects(()=>f.prepare(f.requestFor(p)),'PENDING_SCOPE');const prepared=f.prepare(f.requestFor(p,['create_project']));assert.deepEqual(prepared.lease.body.actions,['create_project']);
});
test('fresh challenge is bound to current process nonce and cannot replay after disconnect',t=>{
  const f=fixture(t);const request=f.peersApi.native.freshRequest(f.grant.body.id);const response=f.issuer.fresh({request});f.peersApi.native.acceptFresh({response,grant:f.grant});f.peersApi.native.disconnect();f.peersApi.native.freshRequest(f.grant.body.id);rejects(()=>f.peersApi.native.acceptFresh({response,grant:f.grant}),'STALE_CHALLENGE');
});
test('path traversal, symlink, hardlink, workspace replacement and incorrect registry binding reject',t=>{
  const f=fixture(t),lookup=id=>f.registry.get(id);fs.writeFileSync(path.join(f.project.root,'todo.html'),'todo');
  rejects(()=>resolveProjectFile(f.workspace,f.project,'../outside',lookup),'PATH_INVALID');
  fs.symlinkSync('/tmp',path.join(f.project.root,'link'));rejects(()=>resolveProjectFile(f.workspace,f.project,'link/escape',lookup),'PATH_SYMLINK');
  fs.linkSync(path.join(f.project.root,'todo.html'),path.join(f.project.root,'alias'));rejects(()=>resolveProjectFile(f.workspace,f.project,'alias',lookup),'PATH_INVALID');
  rejects(()=>resolveRegisteredProject({...f.workspace,ino:f.workspace.ino+1},f.project,lookup),'WORKSPACE_REPLACED');
  rejects(()=>resolveRegisteredProject(f.workspace,{...f.project,id:'not-registered'},lookup),'PROJECT_BINDING');
});
test('clock rollback blocks transactions and new operation admission',t=>{const f=fixture(t);f.start();f.advance(-1);rejects(()=>f.peersApi.native.begin({operation:f.operation()}),'CLOCK_ROLLBACK');});
test('single writer lock, file mode checks, and symlink state reject unsafe stores',t=>{
  const f=fixture(t);rejects(()=>new ProtectedStore({directory:path.join(f.dir,'issuer'),now:f.now}),'STATE_BUSY');
  const d=path.join(f.dir,'unsafe');fs.mkdirSync(d,{mode:0o755});rejects(()=>new ProtectedStore({directory:d,now:f.now}),'STATE_PATH');
});
test('durable commit acknowledgement loss restores committed state; no state rollback on reopening',t=>{
  const dir=fs.mkdtempSync(path.join(os.tmpdir(),'r16-commit-test-'));fs.chmodSync(dir,0o700);t.after(()=>fs.rmSync(dir,{recursive:true,force:true}));let fault=false;
  const s=new ProtectedStore({directory:path.join(dir,'store'),create:true,initial:{counter:0},fault:point=>{if(fault&&point==='after_commit')throw Error('crash');}});fault=true;
  rejects(()=>s.transact(x=>{x.counter++;}),'STATE_COMMIT_UNCERTAIN');s.close();const reopened=new ProtectedStore({directory:path.join(dir,'store')});assert.equal(reopened.snapshot().counter,1);reopened.close();
});
test('dead process writer lock recovers without deleting live lock or replaying state',t=>{
  const dir=fs.mkdtempSync(path.join(os.tmpdir(),'r16-crash-test-'));fs.chmodSync(dir,0o700);t.after(()=>fs.rmSync(dir,{recursive:true,force:true}));const location=path.join(dir,'store');
  const script=`import {ProtectedStore} from ${JSON.stringify(new URL('../src/lease-core.mjs',import.meta.url).href)};const s=new ProtectedStore({directory:${JSON.stringify(location)},create:true,initial:{counter:0}});s.transact(x=>{x.counter=7});process.exit(0);`;
  assert.equal(spawnSync(process.execPath,['--input-type=module','-e',script],{encoding:'utf8'}).status,0);const s=new ProtectedStore({directory:location});assert.equal(s.snapshot().counter,7);s.close();
});
test('different terminal ledgers prevent activation even with otherwise valid role signatures',t=>{
  const f=fixture(t);f.prepare();f.stage();const e=f.evidence();e.native=signed({...e.native.body,resultsHash:digest('missing-result')},f.peerKeys.native);rejects(()=>f.issuer.activate({grantId:f.grant.body.id,projectId:f.project.id,evidence:e}),'RESULTS_NOT_RECONCILED');
});
test('normal final close is three-end durable and future generation never reopens closed capability',t=>{
  const f=fixture(t);f.start();f.execute();const old=f.lease;
  const evidence=Object.fromEntries(ROLES.map(r=>[r,f.peersApi[r].stop({lease:old})]));
  const closed=f.issuer.closeLease({grantId:f.grant.body.id,projectId:f.project.id,lease:old,evidence});assert.equal(closed.body.schema,'r16.closed.v1');
  assert.deepEqual(f.issuer.closeLease({grantId:f.grant.body.id,projectId:f.project.id,lease:old,evidence}),closed);
  rejects(()=>f.peersApi.native.prepare({lease:old,grant:f.grant,release:f.release}),'LEASE_CLOSED');
  f.prepare();f.stage();f.activate();assert.equal(f.lease.body.generation,2);f.execute(f.operation('new-generation'));
});
test('stop persists admission closure before reporting unresolved work, and cleanup can complete after expiry',t=>{
  const f=fixture(t);f.start();const old=f.lease,op=f.operation();for(const r of ROLES)f.peersApi[r].begin({operation:op});
  rejects(()=>f.peersApi.native.stop({lease:old}),'RECOVERY_UNRESOLVED');assert.equal(f.peersApi.native.status().closing,true);
  rejects(()=>f.peersApi.native.begin({operation:f.operation('new-after-stop')}),'NOT_ACTIVE');f.advance(LEASE_MS+1);
  const receipt=f.peersApi.native.complete({operationId:op.body.id,outcome:'COMPLETED',resultHash:digest('late-true-result')});for(const r of ['app','bridge'])f.peersApi[r].reconcile({receipt});
  const evidence=Object.fromEntries(ROLES.map(r=>[r,f.peersApi[r].stop({lease:old})]));assert.equal(f.issuer.closeLease({grantId:f.grant.body.id,projectId:f.project.id,lease:old,evidence}).body.generation,1);
});
test('expired preparation delivered to only one endpoint can retire without reusing a write credential',t=>{
  const f=fixture(t);f.start();f.execute();f.advance(2700000);f.prepare();const abandoned=f.lease;
  f.peersApi.app.prepare({lease:abandoned,grant:f.grant,release:f.release});f.advance(LEASE_MS+1);
  const evidence=Object.fromEntries(ROLES.map(r=>[r,f.peersApi[r].stop({lease:abandoned})]));f.issuer.closeLease({grantId:f.grant.body.id,projectId:f.project.id,lease:abandoned,evidence});
  f.prepare();f.stage();f.activate();assert.equal(f.lease.body.generation,3);f.execute(f.operation('after-retirement'));
});
test('Native proves never-dispatched only after durable drain; missing peers reconcile without replay',t=>{
  const f=fixture(t);f.start();const op=f.operation();f.peersApi.app.begin({operation:op});
  rejects(()=>f.peersApi.native.refuseUndispatched({operation:op}),'DRAIN_REQUIRED');
  f.advance(2700000);f.prepare();f.stage();const receipt=f.peersApi.native.refuseUndispatched({operation:op});assert.equal(receipt.body.outcome,'NOT_EXECUTED');
  f.peersApi.app.reconcile({receipt});f.peersApi.bridge.reconcile({receipt,operation:op});f.activate();
});
test('Native cannot certify never-dispatched for an in-flight operation',t=>{
  const f=fixture(t);f.start();const op=f.operation();f.peersApi.native.begin({operation:op});f.advance(2700000);f.prepare();f.stage();
  rejects(()=>f.peersApi.native.refuseUndispatched({operation:op}),'RECOVERY_UNRESOLVED');
});
test('two-stage drain reconciles an operation absent at Native before final stop',t=>{
 const f=fixture(t);f.start();const lease=f.lease,operation=f.operation();f.peersApi.app.begin({operation});
 for(const r of ROLES)f.peersApi[r].drain({lease});
 const receipt=f.peersApi.native.refuseUndispatched({operation});f.peersApi.app.reconcile({receipt});f.peersApi.bridge.reconcile({receipt,operation});
 const evidence=Object.fromEntries(ROLES.map(r=>[r,f.peersApi[r].stop({lease})]));assert.equal(f.issuer.closeLease({grantId:f.grant.body.id,projectId:f.project.id,lease,evidence}).body.generation,1);
});
test('closed generations archive durably while active snapshots remain bounded and old receipts remain available',t=>{
 const f=fixture(t);f.start();const first=f.operation('old-operation');f.execute(first);
 for(let i=0;i<12;i++){f.advance(2700000);f.prepare();f.stage();f.activate();f.execute(f.operation('next-'+i));}
 for(const r of ROLES){const state=f.peersApi[r].snapshot();assert.equal(state.operations.length,1);assert.ok(state.closed.length<=8);assert.ok(state.archiveHead);assert.equal(f.peersApi[r].begin({operation:first}).decision,'KNOWN');assert.equal(f.peersApi[r].receipt('old-operation').body.generation,1);}
 assert.ok(f.issuer.snapshot().grants[0].projects[0].history.length<=4);
});
test('UNKNOWN admission pauses only the affected project until a real terminal result is reconciled',t=>{
 const f=fixture(t);f.start();const old=f.operation();f.peersApi.native.begin({operation:old});f.peersApi.native.markUnknown(old.body.id);
 rejects(()=>f.peersApi.native.begin({operation:f.operation('later')}),'RECOVERY_UNRESOLVED');
 f.peersApi.native.complete({operationId:old.body.id,outcome:'COMPLETED',resultHash:digest('verified-late-result')});assert.equal(f.peersApi.native.begin({operation:f.operation('later')}).decision,'EXECUTE');
});
test('issuer restores archived preparation after state commit fails, without issuing a different lease',t=>{
 const f=fixture(t),request=f.requestFor(),proofs=Object.fromEntries(ROLES.map(r=>[r,signed(request,f.peerKeys[r])]));
 f.issuerStore.fault=point=>{if(point==='before_rename')throw Error('synthetic crash');};
 rejects(()=>f.issuer.prepare({grantId:f.grant.body.id,request,proofs,release:f.release}),'STATE_COMMIT_UNCERTAIN');f.issuerStore.close();
 const store=new ProtectedStore({directory:path.join(f.dir,'issuer'),now:f.now});f.stores.push(store);
 const issuer=createIssuer({store,signingKey:f.issuerKey,releaseKey:exportPublicKey(f.releaseKey),authorizeOwner:()=>false,resolveProject:f.resolver});
 const lease=issuer.prepare({grantId:f.grant.body.id,request,proofs,release:f.release});assert.deepEqual(issuer.snapshot().grants[0].projects[0].pending.lease,lease);assert.equal(lease.body.generation,1);
});
test('issuer restores the original activation certificate after its commit acknowledgement is lost',t=>{
 const f=fixture(t);f.prepare();f.stage();const evidence=f.evidence();
 f.issuerStore.fault=point=>{if(point==='before_rename')throw Error('synthetic crash');};
 rejects(()=>f.issuer.activate({grantId:f.grant.body.id,projectId:f.project.id,evidence}),'STATE_COMMIT_UNCERTAIN');f.issuerStore.close();f.advance(5000);
 const store=new ProtectedStore({directory:path.join(f.dir,'issuer'),now:f.now});f.stores.push(store);
 const issuer=createIssuer({store,signingKey:f.issuerKey,releaseKey:exportPublicKey(f.releaseKey),authorizeOwner:()=>false,resolveProject:f.resolver});
 const activation=issuer.activate({grantId:f.grant.body.id,projectId:f.project.id,evidence});assert.equal(activation.body.activatedAt,f.now()-5000);for(const r of ROLES)f.peersApi[r].activate({activation});
});
test('participant restores completed final close after archive write but failed state rename',t=>{
 const f=fixture(t);f.start();f.execute();let n=0;f.peerStores.native.fault=point=>{if(point==='before_rename'&&++n===2)throw Error('synthetic crash');};
 rejects(()=>f.peersApi.native.stop({lease:f.lease}),'STATE_COMMIT_UNCERTAIN');f.peerStores.native.close();
 const store=new ProtectedStore({directory:path.join(f.dir,'native'),now:f.now});f.stores.push(store);
 const native=createParticipant({store,role:'native',signingKey:f.peerKeys.native,issuerKey:exportPublicKey(f.issuerKey),releaseKey:exportPublicKey(f.releaseKey),resolveProject:f.resolver});
 assert.equal(native.stop({lease:f.lease}).body.durableClosed,true);assert.equal(native.status().closing,false);assert.equal(native.status().available,false);
});
test('replayed historical close ACK never discards a newer prepared generation',t=>{
 const f=fixture(t);f.start();const old=f.lease;const evidence=Object.fromEntries(ROLES.map(r=>[r,f.peersApi[r].stop({lease:old})]));f.issuer.closeLease({grantId:f.grant.body.id,projectId:f.project.id,lease:old,evidence});
 f.prepare();f.stage();const next=f.lease;
 f.issuer.closeLease({grantId:f.grant.body.id,projectId:f.project.id,lease:old,evidence});for(const r of ROLES)f.peersApi[r].stop({lease:old});
 assert.equal(f.issuer.snapshot().grants[0].projects[0].pending.lease.body.generation,next.body.generation);for(const r of ROLES)assert.equal(f.peersApi[r].status().pendingGeneration,next.body.generation);f.activate();
});
test('Owner grant remains usable five days later without reissuing a Crown time window',t=>{
 const f=fixture(t);
 f.advance(5*24*LEASE_MS);
 for(const r of ROLES)f.connect(r);
 f.start();
 f.execute(f.operation('five-days-later'));
 assert.equal(f.issuer.snapshot().grants[0].status,'ACTIVE');
});

test('signed lost FindSymbol result closes the already-draining generation without pretending execution outcome',t=>{
 const f=fixture(t),lease=f.start(),read=f.operation('read-lost','find_symbol');
 for(const role of ROLES){f.peersApi[role].begin({operation:read});f.peersApi[role].markUnknown(read.body.id);}
 const value=unavailableReadResult(read),hashValue=digest(value);
 assert.deepEqual(READ_RESULT_LOSS_ACTIONS,['find_symbol']);
 assert.equal(value.reason,'ORIGINAL_RESULT_NOT_DURABLE');
 rejects(()=>f.peersApi.native.settleUnavailableRead({operation:read,resultHash:hashValue}),'DRAIN_REQUIRED');
 for(const role of ROLES)rejects(()=>f.peersApi[role].stop({lease}),'RECOVERY_UNRESOLVED');
 rejects(()=>f.peersApi.native.settleUnavailableRead({operation:read,resultHash:hashValue}),'LEASE_NOT_EXPIRED');
 f.advance(LEASE_MS+1);
 rejects(()=>f.peersApi.app.settleUnavailableRead({operation:read,resultHash:hashValue}),'NATIVE_RESULT_REQUIRED');
 rejects(()=>f.peersApi.native.settleUnavailableRead({operation:read,resultHash:digest({forged:true})}),'RESULT_CONFLICT');
 const receipt=f.peersApi.native.settleUnavailableRead({operation:read,resultHash:hashValue});
 assert.equal(receipt.body.outcome,'READ_RESULT_UNAVAILABLE');
 assert.equal(receipt.body.resultHash,hashValue);
 assert.deepEqual(f.peersApi.native.settleUnavailableRead({operation:read,resultHash:hashValue}),receipt);
 rejects(()=>f.peersApi.app.reconcile({receipt}),'READ_RECOVERY_SCOPE');
 for(const role of ['app','bridge'])assert.equal(f.peersApi[role].reconcile({receipt,operation:read}).outcome,'READ_RESULT_UNAVAILABLE');
 const stop=Object.fromEntries(ROLES.map(role=>[role,f.peersApi[role].stop({lease})]));
 assert.equal(new Set(Object.values(stop).map(proof=>proof.body.resultsHash)).size,1);
 const close=f.issuer.closeLease({grantId:f.grant.body.id,projectId:f.project.id,lease,evidence:stop});
 assert.equal(close.body.schema,'r16.closed.v1');
 assert.equal(f.peersApi.native.status().closing,false);
 assert.equal(f.peersApi.native.snapshot().operations.length,0);
 assert.deepEqual(f.peersApi.native.settleUnavailableRead({operation:read,resultHash:hashValue}),receipt); // archived idempotence
});
test('lost read cannot terminalize writes, nonallowlisted reads, non-UNKNOWN work, or forged App requests',t=>{
 const f=fixture(t),lease=f.start(),op=f.operation('lost-write','edit_code'),read=f.operation('lost-current-read','find_symbol');
 for(const role of ROLES)f.peersApi[role].begin({operation:op});
 // Start both operations before marking one UNKNOWN; admission forbids new work afterwards.
 f.peersApi.native.begin({operation:read});
 f.peersApi.native.markUnknown(op.body.id);
 rejects(()=>unavailableReadResult(op),'READ_RECOVERY_SCOPE');
 const currentResult=unavailableReadResult(read);
 rejects(()=>f.peersApi.native.settleUnavailableRead({operation:read,resultHash:digest(currentResult)}),'DRAIN_REQUIRED');
 rejects(()=>f.peersApi.native.stop({lease}),'RECOVERY_UNRESOLVED');
 f.advance(LEASE_MS+1);
 rejects(()=>f.peersApi.native.settleUnavailableRead({operation:read,resultHash:digest(currentResult)}),'RECOVERY_UNRESOLVED');
 rejects(()=>f.peersApi.native.settleUnavailableRead({operation:op,resultHash:digest({})}),'READ_RECOVERY_SCOPE');
 const forged=structuredClone(read);forged.body.payloadHash='a'.repeat(64);
 rejects(()=>f.peersApi.native.settleUnavailableRead({operation:forged,resultHash:digest(currentResult)}),'BAD_SIGNATURE');
 const otherRead=f.operation('lost-nonallowlisted','read_code');
 rejects(()=>unavailableReadResult(otherRead),'READ_RECOVERY_SCOPE');
 assert.equal(f.peersApi.native.snapshot().operations.find(x=>x.id===read.body.id).status,'INFLIGHT');
 assert.equal(f.peersApi.native.snapshot().operations.find(x=>x.id===op.body.id).status,'UNKNOWN');
});
test('forged read-loss receipt can never settle an edit operation on App or Bridge',t=>{
 const f=fixture(t);f.start();
 const edit=f.operation('edit-to-guard','edit_code');
 for(const role of ROLES){f.peersApi[role].begin({operation:edit});f.peersApi[role].markUnknown(edit.body.id);}
 const forgedReceipt=signed({schema:'r16.result.v1',role:'native',peerId:f.grant.body.peers.native.id,
  grantId:f.grant.body.id,projectId:f.project.id,operationId:edit.body.id,operationHash:digest(edit),
  generation:edit.body.generation,outcome:'READ_RESULT_UNAVAILABLE',resultHash:digest({fake:true})},f.peerKeys.native);
 for(const role of ['app','bridge'])rejects(()=>f.peersApi[role].reconcile({receipt:forgedReceipt,operation:edit}),'READ_RECOVERY_SCOPE');
 assert.equal(f.peersApi.app.snapshot().operations[0].status,'UNKNOWN');
});
