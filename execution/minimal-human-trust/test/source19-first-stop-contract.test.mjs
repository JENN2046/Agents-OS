// Read-only negative contract diagnostic, not a STOP implementation or V1 PASS.
// Exact public Source19 fixture bytes, copied from the installed release and
// independently pinnable. No production state/credentials/network/services.
// Synthetic journals below are created only under a disposable private /tmp.
import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import os from 'node:os';
import {createHash,generateKeyPairSync,randomUUID} from 'node:crypto';
import {pathToFileURL} from 'node:url';
import {verifySignedBusinessStop} from '../src/signed-business-stop.mjs';

const ROOT=new URL('./fixtures/source19-first-stop/',import.meta.url).pathname;
const sha=b=>createHash('sha256').update(b).digest('hex');
const pins={
 'app/workspace-host.mjs':'bfef60223b8fd186f2e96887b770678777bf99ff2a5c84a3c36273d8f172a6ab',
 'bridge/workspace-private-router.mjs':'480498c6286a6990e7fe4c95cf5928111cd6925d8804cf68ef7b836eedb15404',
 'host/workspace-dispatcher.mjs':'ba4ef78187a8701b97bd03461faed44771c4d71b8541681a6d573e3f35ed079c',
 'host/native-runner.mjs':'0f30ebe457764265b2b8dad630f1a68f6e7251911c94da8a48362c6a0bfe089c',
 'src/lease-core.mjs':'889232f53d5c014138a7004df32c8e4f4f6c16703b6d53fa75ce0cbcf53e43b9',
};
const pinBytes=fs.readFileSync(path.join(ROOT,'PUBLIC_SOURCE_PINS.json'));
assert.equal(sha(pinBytes),'5f850ff19dc8cf4406e3cf600fae0005e54ab879ab5f086f67f909708d3cd916');
for(const [rel,pin]of Object.entries(JSON.parse(pinBytes).files))
 assert.equal(sha(fs.readFileSync(path.join(ROOT,rel))),pin,'complete public fixture bytes: '+rel);
for(const [rel,pin]of Object.entries(pins))assert.equal(sha(fs.readFileSync(path.join(ROOT,rel))),pin,'exact public Source19 input required: '+rel);
const text=rel=>fs.readFileSync(path.join(ROOT,rel),'utf8');
const core=await import(pathToFileURL(path.join(ROOT,'src/lease-core.mjs')));
const {createHeadlessHost}=await import(pathToFileURL(path.join(ROOT,'host/headless-host.mjs')));
const {createWorkspaceDispatcher,dispatcherInitialState}=await import(pathToFileURL(path.join(ROOT,'host/workspace-dispatcher.mjs')));

test('negative: actual signed19 is not a disconnect delivery; no role receipt is fabricated',()=>{
 const pub=JSON.parse(fs.readFileSync(new URL('./fixtures/SOURCE19_PUBLIC_CONFIG.json',import.meta.url)));
 const delivery=JSON.parse(fs.readFileSync(new URL('./fixtures/SOURCE19_DELIVERY_ENVELOPE.json',import.meta.url)));
 assert.equal(core.digest(pub),'56e1df18a54950ea346a51654e61df60afe33cb9928ae77293b2cf336fd8a5ec');
 assert.equal(core.digest(delivery),'b8645f6fe206e84dd07c2c6c166bfe4016d1deefca28bf9545dcfa1560f013e9');
 assert.equal(delivery.body.control.connectRequested,true);
 assert.throws(()=>verifySignedBusinessStop({grant:pub.grant,issuerPublicKey:pub.issuerPublicKey,
  release:pub.release,releasePublicKey:pub.releasePublicKey,delivery,receipts:{},
  expectedRevision:19,expectedReviewDigest:'a'.repeat(64),expectedUnresolvedIds:[],
  expectedResultsHashes:{app:'b'.repeat(64),bridge:'c'.repeat(64),native:'d'.repeat(64)},
  stopEpoch:'readonly-negative-contract',now:delivery.body.issuedAt+1}),{code:'STOP_CLOUD_CONTROL'});
});

test('negative: pinned Source19 roles do not export the new runtime STOP evidence interface',()=>{
 for(const rel of ['app/workspace-host.mjs','bridge/workspace-private-router.mjs','host/workspace-dispatcher.mjs'])
  assert.doesNotMatch(text(rel),/businessStopEvidence|signRuntimeBusinessStop|establishBusinessStop/);
 assert.match(text('host/workspace-dispatcher.mjs'),/s\.admissionStopped=!!s\.recoveryOnly\|\|!requested\|\|s\.revoked/);
});

function unknownParticipant(){
 const key=()=>generateKeyPairSync('ed25519').privateKey;
 const issuer=key(),roleKeys=Object.fromEntries(core.ROLES.map(r=>[r,key()]));
 const peers=Object.fromEntries(core.ROLES.map(r=>[r,{id:'fixture-'+r,publicKey:core.exportPublicKey(roleKeys[r])}]));
 const workspace={id:'fixture-workspace',root:'/tmp/source19-readonly-uncreated',dev:1,ino:2};
 const grant=core.signed({schema:'r16.workspace.v1',id:'fixture-grant',workspace,actions:core.ACTIONS,
  channel:'main',peers,version:1,createdAt:1000},issuer);
 const lease=core.signed({schema:'r16.lease.v1',phase:'PREPARED',grantId:grant.body.id,grantVersion:1,
  grantHash:core.digest(grant),project:{id:'fixture-project',workspaceId:workspace.id,root:workspace.root+'/project'},
  channel:'main',versions:{app:'a'.repeat(64),bridge:'b'.repeat(64),native:'c'.repeat(64)},
  actions:core.ACTIONS,generation:1,previousGeneration:0,issuedAt:1000,expiresAt:1000+core.LEASE_MS,
  renewAt:1000+core.LEASE_MS-core.RENEW_BEFORE_MS,requestId:randomUUID(),releaseHash:'d'.repeat(64)},issuer);
 // In-memory persistence boundary only. Actual published participant.stop is
 // executed below; no absent Source19 STOP method is added or mocked to pass.
 let state={...core.participantInitialState('native'),grant,version:1,lastGeneration:1,
  active:{lease},operations:[{id:'fixture-historical-read',hash:'e'.repeat(64),projectId:'fixture-project',
   generation:1,status:'UNKNOWN',outcome:null,resultHash:null}]};
 const store=Object.create(core.ProtectedStore.prototype);
 Object.assign(store,{snapshot:()=>structuredClone(state),transact:fn=>{
  const next=structuredClone(state),result=fn(next,2000);state=next;return structuredClone(result);
 },archived:()=>null,archive:()=>assert.fail('UNKNOWN cannot produce stop/archive proof')});
 const p=core.createParticipant({store,role:'native',signingKey:roleKeys.native,
  issuerKey:core.exportPublicKey(issuer),releaseKey:core.exportPublicKey(key()),resolveProject:(_w,p)=>p});
 return {p,lease,snapshot:()=>structuredClone(state)};
}

test('negative: actual published participant.stop persists closing then rejects a historical UNKNOWN',()=>{
 const f=unknownParticipant(),before=f.snapshot().operations;
 assert.throws(()=>f.p.stop({lease:f.lease}),{code:'RECOVERY_UNRESOLVED'});
 assert.deepEqual(f.snapshot().operations,before);
 assert.deepEqual(f.snapshot().closing,f.lease);
 assert.deepEqual(f.snapshot().stopped,[]);
 assert.match(text('host/workspace-dispatcher.mjs'),/if\(lease\)entry\.participant\.stop\(\{lease\}\);entry\.participant\.disconnect\(\);check\(entry\.participant\.status\(\)\.unresolved\.length===0,'RECOVERY_UNRESOLVED'\)/);
});

test('negative: actual headless stop cannot reach socket/store/writer release after that real refusal',async()=>{
 const f=unknownParticipant(),effects=[];
 // The transport is inert. close invokes the actual published participant
 // refusal above, exactly the Source19 dispatcher's unconditional lease path.
 // This is not a complete Native runner/process-exit test.
 const port={refresh:async()=>({status:'CLEANUP_ONLY'}),handle:async()=>assert.fail('no business dispatch'),
  close:async()=>f.p.stop({lease:f.lease}),releaseStores:()=>effects.push('stores')};
 const peer={send(){},onMessage(){},closed:new Promise(()=>{}),close:async()=>effects.push('socket')};
 const host=createHeadlessHost({port,manifest:{name:'ProjectForge'},serverName:'fixture',
  connect:async()=>peer,acquireLease:async()=>({release:async()=>effects.push('writer')}),shutdownMs:1000});
 await host.start();await assert.rejects(host.stop(),{code:'RECOVERY_REQUIRED'});
 assert.deepEqual(effects,[]);
 assert.equal(host.state,'恢复待核实');
 assert.match(text('host/native-runner.mjs'),/await host\.stop\(\)/);
 assert.match(text('host/native-runner.mjs'),/process\.exitCode=1/);
 assert.doesNotMatch(text('host/native-runner.mjs'),/process\.exit\(/);
});

async function realDispatcherFixture(t,{withLease=true}={}){
 const root=fs.mkdtempSync(path.join(os.tmpdir(),'source19-negative-stop-'));fs.chmodSync(root,0o700);
 const workspaceRoot=path.join(root,'projects');fs.mkdirSync(workspaceRoot,{mode:0o700});
 const st=fs.statSync(workspaceRoot),workspace={id:'fixture-workspace',root:workspaceRoot,dev:st.dev,ino:st.ino};
 const key=()=>generateKeyPairSync('ed25519').privateKey,issuerKey=key(),releaseKey=key();
 const keys=Object.fromEntries(core.ROLES.map(r=>[r,key()]));
 const peers=Object.fromEntries(core.ROLES.map(r=>[r,{id:'fixture-'+r,publicKey:core.exportPublicKey(keys[r])}]));
 const pub=JSON.parse(fs.readFileSync(new URL('./fixtures/SOURCE19_PUBLIC_CONFIG.json',import.meta.url)));
 const grant=core.signed({schema:'r16.workspace.v1',id:'fixture-source19-contract',workspace,
  actions:core.ACTIONS,channel:'main',peers,version:1,createdAt:1000},issuerKey);
 const release=core.signed({...pub.release.body,issuedAt:1000,notAfter:1000+7*86400000},releaseKey);
 const rows=[{projectId:'p2vox',id:'c434da49-055a-43dc-a3e3-695cce137909',generation:30,
  hash:'fd13e74ce69cb8ec30817ca0a48631cf3a6b6b2b08a410cc1b442df41992cc1f'},
  {projectId:'pmog2',id:'d0364f8b-3a68-4ca2-a396-7953b29cee4c',generation:38,
   hash:'38f6af1386e78e5d7ccd0710077d6a3a5e753e81722dd10f11a3a2ff9bd85da1'}];
 const ds=new core.ProtectedStore({directory:path.join(root,'dispatcher'),create:true,
  initial:{...dispatcherInitialState(),projects:rows.map(r=>r.projectId)},now:()=>2000});
 const projectFiles=[];
 for(const row of rows){
  const project={id:row.projectId,workspaceId:workspace.id,root:path.join(workspaceRoot,row.projectId)};
  fs.mkdirSync(project.root,{mode:0o700});
  const lease=core.signed({schema:'r16.lease.v1',phase:'PREPARED',grantId:grant.body.id,grantVersion:1,
   grantHash:core.digest(grant),project,channel:'main',versions:pub.versions,actions:core.ACTIONS,
   generation:row.generation,previousGeneration:row.generation-1,issuedAt:1000,expiresAt:1000+core.LEASE_MS,
   renewAt:1000+core.LEASE_MS-core.RENEW_BEFORE_MS,requestId:randomUUID(),releaseHash:core.digest(release)},issuerKey);
  const participantStore=new core.ProtectedStore({directory:path.join(ds.dir,'project-'+row.projectId),create:true,
   initial:{...core.participantInitialState('native'),grant,version:1,lastGeneration:row.generation,
    active:withLease?{lease}:null,operations:[{...row,status:'UNKNOWN',outcome:null,resultHash:null}]},now:()=>2000});
  projectFiles.push(path.join(participantStore.dir,'state.json'));participantStore.close();
 }
 const before=projectFiles.map(p=>JSON.parse(fs.readFileSync(p)).data.operations);
 let cleanup=0,portCreations=0;
 const issuer={fresh:async({request})=>{
  const r=core.verified(request,peers.native.publicKey,'r16.fresh-request.v1');
  return core.signed({schema:'r16.fresh.v1',grantId:grant.body.id,version:1,status:'ACTIVE',role:'native',
   peerId:peers.native.id,challenge:r.challenge,issuedAt:2000,expiresAt:32000},issuerKey);
 }};
 const dispatcher=createWorkspaceDispatcher({store:ds,directory:ds.dir,
  native:{cleanup:async()=>{cleanup++;},createWorkspaceCrownPort(){portCreations++;assert.fail('no Native engine needed for this counterexample');}},
  crown:{identityCheck:()=>assert.fail('no business identity registration')},grant,release,versions:pub.versions,
  signingKey:keys.native,issuerKey:core.exportPublicKey(issuerKey),releaseKey:core.exportPublicKey(releaseKey),
  issuer,workspaceAlias:'projects',databasePath:path.join(root,'never-created.sqlite'),now:()=>2000});
 t.after(()=>{
  // Explicit fixture disposal, not a claimed production cleanup/recovery path.
  try{dispatcher.releaseStores();}catch{}try{ds.close();}catch{}
  fs.rmSync(root,{recursive:true,force:true});
 });
 assert.equal((await dispatcher.refresh(true,{allowRevoked:true})).status,'CLEANUP_ONLY');
 return {dispatcher,root,ds,projectFiles,before,cleanup:()=>cleanup,portCreations:()=>portCreations};
}

for(const withLease of [true,false])test('negative: real pinned dispatcher close refuses both UNKNOWNs '+(withLease?'with leases':'even without leases'),async t=>{
 const f=await realDispatcherFixture(t,{withLease});
 const effects=[],peer={send(){},onMessage(){},closed:new Promise(()=>{}),close:async()=>effects.push('socket')};
 const host=createHeadlessHost({port:f.dispatcher,manifest:{name:'ProjectForge'},serverName:'fixture',
  connect:async()=>peer,acquireLease:async()=>({release:async()=>effects.push('writer')}),shutdownMs:1000});
 await host.start();await assert.rejects(host.stop(),{code:'RECOVERY_REQUIRED'});
 // HeadlessHost deliberately normalizes the port failure; the real underlying
 // close remains rejected and cannot proceed to cleanup or releaseStores.
 await assert.rejects(f.dispatcher.close({retainTransport:true}),{code:'RECOVERY_UNRESOLVED'});
 assert.deepEqual(f.projectFiles.map(p=>JSON.parse(fs.readFileSync(p)).data.operations),f.before);
 for(const p of f.projectFiles)assert.equal(fs.existsSync(path.join(path.dirname(p),'.lock')),true);
 assert.equal(fs.existsSync(path.join(f.ds.dir,'.lock')),true);
 assert.deepEqual(effects,[]);assert.equal(f.cleanup(),0);assert.equal(f.portCreations(),0);
 assert.equal(fs.existsSync(path.join(f.root,'never-created.sqlite')),false);
});

test('negative: local 6016 is an SSH relay, not the Cloud Bridge role or its signer',()=>{
 const link=text('host/link-runner.py'),unit=text('packaging/r16-native-link.service');
 assert.match(link,/'-L','127\.0\.0\.1:6016:127\.0\.0\.1:6016'/);
 assert.match(unit,/PartOf=r16-native\.service/);
 assert.doesNotMatch(unit,/LoadCredentialEncrypted=bridge-signing-key/);
 assert.match(text('packaging/r16-bridge.service'),/LoadCredentialEncrypted=bridge-signing-key/);
 assert.match(text('bridge/bridge-runner.mjs'),/storeDir='\/var\/lib\/r16-bridge\/grants\/\'\+grant\.id/);
});

test('negative: App has generic upstream dispatch whose timeout is not a remote cancellation receipt',()=>{
 const server=text('app/upstream/src/server.mjs'),client=text('app/upstream/src/vcp-client.mjs');
 assert.match(server,/await vcp\.callTool\(tool_name, args\)/);
 assert.match(client,/controller\.abort\(\)/);
 assert.match(client,/return this\.request\("\/v1\/human\/tool"/);
 assert.doesNotMatch(client,/remoteCancellationReceipt|cancelAcknowledgement|cancelledJobReceipt/);
 // Thus a whole-App/upstream drain claim requires additional real evidence;
 // role process exit and stable paired ledgers alone cannot establish it.
});
