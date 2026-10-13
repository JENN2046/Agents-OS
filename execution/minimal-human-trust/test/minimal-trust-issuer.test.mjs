import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import os from 'node:os';
import {randomUUID,generateKeyPairSync} from 'node:crypto';
import {spawnSync} from 'node:child_process';
import {createIssuer,createParticipant,ProtectedStore,issuerInitialState,
  participantInitialState,ROLES,ACTIONS,digest,exportPublicKey,
  signed,verified,resolveRegisteredProject} from '../src/lease-core.mjs';
import {createMinimalTrustIssuer,runMinimalTrustOnce,replayInitialState}
  from '../src/minimal-trust-issuer.mjs';

const pair=()=>generateKeyPairSync('ed25519').privateKey;
const refusal=(fn,code)=>assert.throws(fn,e=>e?.code===code,
  'Expected '+code+' from trust core');
function fixture(t){
 const temp=fs.mkdtempSync(path.join(os.tmpdir(),'mht-g1-fixture-'));
 fs.chmodSync(temp,0o700);
 const root=path.join(temp,'workspace');
 fs.mkdirSync(root,{mode:0o700});
 const stat=fs.statSync(root);
 const workspace={id:'mht-workspace',root,dev:stat.dev,ino:stat.ino};
 const project={id:'project-one',workspaceId:workspace.id,root:path.join(root,'project-one')};
 fs.mkdirSync(project.root,{mode:0o700});
 const issuerKey=pair(),releaseKey=pair(),humanKey=pair();
 const peerKeys=Object.fromEntries(ROLES.map(role=>[role,pair()]));
 const peers=Object.fromEntries(ROLES.map(role=>[role,{
   id:'peer-'+role,publicKey:exportPublicKey(peerKeys[role])}]));
 const versions=Object.fromEntries(ROLES.map(role=>[role,digest('synthetic-'+role)]));
 let time=1791859000000;
 const now=()=>time,advance=delta=>{time+=delta;};
 const issuerDirectory=path.join(temp,'issuer');
 const replayDirectory=path.join(temp,'replay');
 const store=new ProtectedStore({directory:issuerDirectory,create:true,
   initial:issuerInitialState(),now});
 const approval=Object.freeze({humanFixture:true});
 const resolveProject=(w,p)=>resolveRegisteredProject(w,p,id=>id===project.id?project:null);
 const initializer=createIssuer({store,signingKey:issuerKey,
   releaseKey:exportPublicKey(releaseKey),
   authorizeOwner:({approval:a})=>a===approval,
   resolveProject});
 const grant=initializer.createGrant({approval,grant:{id:'single-human-grant',workspace,
   actions:ACTIONS.slice(),channel:'main',peers}});
 store.close();
 const nonceStore=new ProtectedStore({directory:replayDirectory,create:true,
   initial:replayInitialState(),now});
 nonceStore.close();
 const release=signed({schema:'r16.release.v1',id:'r17-trust-fixture',
   issuedAt:now()-1000,notAfter:now()+30*86400000,
   formats:['r16.workspace.v1'],versions,actions:ACTIONS.slice(),
   permissionVersion:1},releaseKey);
 const args={issuerDirectory,replayDirectory,issuerPrivateKey:issuerKey,
   releasePublicKey:exportPublicKey(releaseKey),
   issuerPublicKey:exportPublicKey(issuerKey),grantId:grant.body.id,release,
   resolveProject,humanAuthorityPublicKey:exportPublicKey(humanKey),now};
 const callers={},participants={},stores=[];
 for(const role of ROLES){
   const ps=new ProtectedStore({directory:path.join(temp,'p-'+role),
     create:true,initial:participantInitialState(role),now});
   stores.push(ps);
   participants[role]=createParticipant({store:ps,role,
     signingKey:peerKeys[role],issuerKey:args.issuerPublicKey,
     releaseKey:args.releasePublicKey,resolveProject});
   participants[role].pair({grant});
 }
 const envelope=(role,action,payload,extra={})=>signed({
   schema:'r16.issuer-call.v1',role,peerId:peers[role].id,
   issuedAt:now(),nonce:randomUUID(),action,payload,...extra},peerKeys[role]);
 const issue=(role,action,payload,extra={})=>
   runMinimalTrustOnce({...args,envelope:envelope(role,action,payload,extra)});
 const rawIssue=(envelope,add={})=>runMinimalTrustOnce({...args,...add,envelope});
 const trust=options=>createMinimalTrustIssuer(options);
 const connect=role=>{
   const p=participants[role],request=p.freshRequest(grant.body.id);
   const response=issue(role,'fresh',{request});
   assert.equal(verified(response,args.issuerPublicKey,'r16.fresh.v1').status,'ACTIVE');
   assert.deepEqual(p.acceptFresh({response,grant}),{status:'CONNECTED'});
 };
 const readIssuer=()=>{const s=new ProtectedStore({directory:issuerDirectory,create:false,now});
   try{return s.snapshot();}finally{s.close();}};
 t.after(()=>{for(const s of stores)try{s.close();}catch{}fs.rmSync(temp,{recursive:true,force:true});});
 return {temp,now,advance,issuerKey,releaseKey,humanKey,peerKeys,peers,
   workspace,project,versions,grant,release,args,participants,stores,
   issuerDirectory,replayDirectory,envelope,issue,rawIssue,connect,readIssuer,
   trust,approval,resolveProject};
}
test('no Owner daemon: one-shot issuer opens, serves signed fresh, then releases both stores',t=>{
 const f=fixture(t);
 for(const role of ROLES)f.connect(role);
 const grant=f.issue('app','grant',{});
 assert.deepEqual(grant,f.grant);
 const snap=f.readIssuer();
 assert.equal(snap.grants.length,1);
 assert.equal(snap.grants[0].status,'ACTIVE');
 assert.equal(snap.grants[0].version,1);
});
test('full three-party signed lease lifecycle, Native result and issuer close without Owner daemon',t=>{
 const f=fixture(t);
 for(const role of ROLES)f.connect(role);
 const req={schema:'r16.prepare.v1',requestId:randomUUID(),grantId:f.grant.body.id,
   grantVersion:1,project:f.project,channel:f.grant.body.channel,
   versions:f.versions,actions:['find_symbol'],issuedAt:f.now()};
 const proofs=Object.fromEntries(ROLES.map(role=>[role,signed(req,f.peerKeys[role])]));
 const lease=f.issue('app','prepare',{grantId:req.grantId,request:req,proofs,release:f.release});
 assert.equal(verified(lease,f.args.issuerPublicKey,'r16.lease.v1').project.id,f.project.id);
 for(const role of ROLES)f.participants[role].prepare({lease,grant:f.grant,release:f.release});
 const evidence=Object.fromEntries(ROLES.map(role=>[role,f.participants[role].closeEvidence()]));
 const activation=f.issue('app','activate',{grantId:req.grantId,projectId:f.project.id,evidence});
 assert.equal(verified(activation,f.args.issuerPublicKey,'r16.activation.v1').generation,1);
 for(const role of ROLES)f.participants[role].activate({activation});
 const op=signed({schema:'r16.operation.v1',id:randomUUID(),
   grantId:req.grantId,projectId:f.project.id,generation:1,
   leaseHash:digest(lease),channel:req.channel,action:'find_symbol',
   payloadHash:digest({name:'single-grant'})},f.peerKeys.app);
 for(const role of ROLES)assert.equal(f.participants[role].begin({operation:op}).decision,'EXECUTE');
 const response=f.participants.native.complete({operationId:op.body.id,outcome:'COMPLETED',
   resultHash:digest({only_read:'yes'})});
 for(const role of ['app','bridge'])f.participants[role].reconcile({receipt:response});
 const stop=Object.fromEntries(ROLES.map(role=>[role,f.participants[role].stop({lease})]));
 assert.equal(new Set(Object.values(stop).map(x=>x.body.resultsHash)).size,1);
 const closed=f.issue('native','closeLease',{grantId:req.grantId,projectId:req.project.id,lease,evidence:stop});
 assert.equal(verified(closed,f.args.issuerPublicKey,'r16.closed.v1').generation,1);
 assert.equal(f.readIssuer().grants[0].projects[0].active,null);
});
test('persistent nonce fence refuses exact replay across separate one-shot invocations',t=>{
 const f=fixture(t);
 const env=f.envelope('app','grant',{});
 assert.deepEqual(f.rawIssue(env),f.grant);
 refusal(()=>f.rawIssue(env),'REPLAY_REJECTED');
 // New signed challenge is allowed, without extra Human license.
 assert.deepEqual(f.issue('app','grant',{}),f.grant);
});
test('wrong peer signature is rejected before committing replay nonce',t=>{
 const f=fixture(t);
 const good=f.envelope('app','grant',{});
 const bad=signed(good.body,f.peerKeys.native);
 refusal(()=>f.rawIssue(bad),'BAD_SIGNATURE');
 assert.deepEqual(f.rawIssue(good),f.grant);
});
test('stale, future and structurally expanded signed requests are denied',t=>{
 const f=fixture(t),a=f.envelope('app','grant',{});
 refusal(()=>f.rawIssue(signed({...a.body,issuedAt:f.now()-30001},f.peerKeys.app)),
   'STALE_REQUEST');
 refusal(()=>f.rawIssue(signed({...a.body,issuedAt:f.now()+1},f.peerKeys.app)),
   'STALE_REQUEST');
 refusal(()=>f.rawIssue(signed({...a.body,extra:'permission'},f.peerKeys.app)),
   'TRUST_INPUT_SHAPE');
});
test('recovery-only mode denies new business issuance, yet allows existing grant proof and fresh challenge',t=>{
 const f=fixture(t);
 refusal(()=>f.rawIssue(f.envelope('app','prepare',{}),{mode:'recovery_only'}),'RECOVERY_ONLY');
 assert.deepEqual(f.rawIssue(f.envelope('app','grant',{}),{mode:'recovery_only'}),f.grant);
 const req=f.participants.app.freshRequest(f.grant.body.id);
 const result=f.rawIssue(f.envelope('app','fresh',{request:req}),{mode:'recovery_only'});
 assert.equal(verified(result,f.args.issuerPublicKey,'r16.fresh.v1').status,'ACTIVE');
 refusal(()=>f.rawIssue(f.envelope('app','grant',{}),{mode:'halted'}),'TRUST_HALTED');
});
test('another issuer key, replaced release and foreign project are rejected',t=>{
 const f=fixture(t);
 refusal(()=>f.rawIssue(f.envelope('app','grant',{}),{issuerPrivateKey:pair()}),'ISSUER_KEY_MISMATCH');
 const alteredRelease=signed({...f.release.body,id:'altered'},pair());
 refusal(()=>f.rawIssue(f.envelope('app','grant',{}),{release:alteredRelease}),'BAD_SIGNATURE');
 const permit=f.envelope('app','grant',{});
 refusal(()=>f.rawIssue(permit,{grantId:'second-grant'}),'GRANT_BINDING');
});
test('revoke requires a distinct signed Human Authority proof and blocks replay',t=>{
 const f=fixture(t);for(const role of ROLES)f.connect(role);
 const humanApproval=signed({schema:'mht.human-authorization.v1',action:'revoke_grant',
   grantId:f.grant.body.id,expectedVersion:1,expectedGrantHash:digest(f.grant),releaseId:f.release.body.id,issuedAt:f.now(),nonce:randomUUID()},f.humanKey);
 const revoke=grant=>runMinimalTrustOnce({...f.args,ownerApproval:grant});
 const bad=signed(humanApproval.body,pair());
 refusal(()=>revoke(bad),'BAD_SIGNATURE');
 const result=revoke(humanApproval);
 assert.equal(verified(result,f.args.issuerPublicKey,'r16.revocation.v1').version,2);
 refusal(()=>revoke(humanApproval),'OWNER_TARGET_CHANGED');
 const req=f.participants.app.freshRequest(f.grant.body.id);
 const freshness=f.issue('app','fresh',{request:req});
 assert.equal(freshness.body.status,'REVOKED');
 assert.deepEqual(f.participants.app.acceptFresh({response:freshness,grant:f.grant}),{status:'REVOKED'});
 assert.equal(f.readIssuer().grants[0].status,'REVOKED');
});
test('unsigned or wrong-scope Human approval cannot revoke',t=>{
 const f=fixture(t);
 const request={schema:'mht.human-authorization.v1',action:'revoke_grant',
   grantId:'foreign',expectedVersion:1,expectedGrantHash:digest(f.grant),releaseId:f.release.body.id,issuedAt:f.now(),nonce:randomUUID()};
 refusal(()=>runMinimalTrustOnce({...f.args,ownerApproval:signed(request,f.humanKey)}),
   'OWNER_TARGET_CHANGED');
 assert.equal(f.readIssuer().grants[0].status,'ACTIVE');
});
test('missing durable replay journal refuses before emitting any issuer grant reply',t=>{
 const f=fixture(t);
 fs.renameSync(f.replayDirectory,f.replayDirectory+'-elsewhere');
 assert.throws(()=>f.issue('app','grant',{}));
 assert.equal(f.readIssuer().grants[0].status,'ACTIVE');
});
test('heartbeat is verified and returns a per-lease maintenance snapshot',t=>{
 const f=fixture(t);
 const report=signed({schema:'r16.participant-heartbeat.v1',role:'app',
   peerId:f.peers.app.id,grantId:f.grant.body.id,grantVersion:1,
   issuedAt:f.now(),expiresAt:f.now()+30000,ready:true,credentialValid:true,
   unresolved:false,projects:[]},f.peerKeys.app);
 const result=f.issue('app','heartbeat',{report});
 assert.deepEqual(result,{connectRequested:true,grantVersion:1,revoked:false,
   revocationComplete:false,closeComplete:false});
 assert.deepEqual(f.issue('native','heartbeat',{report}),result);
 refusal(()=>f.issue('bridge','heartbeat',{report}),'ROLE_BINDING');
});
test('human approval target is exact, expiry is strict, and issuer ledger stays unchanged',t=>{
 const f=fixture(t);
 const b={schema:'mht.human-authorization.v1',action:'revoke_grant',
   grantId:f.grant.body.id,expectedVersion:1,expectedGrantHash:digest(f.grant),releaseId:f.release.body.id,issuedAt:f.now()-30001,
   nonce:randomUUID()};
 refusal(()=>runMinimalTrustOnce({...f.args,ownerApproval:signed(b,f.humanKey)}),
   'HUMAN_PROOF_EXPIRED');
 assert.equal(f.readIssuer().grants[0].status,'ACTIVE');
});

test('fresh and revoke acknowledgements cannot be cross-role relayed',t=>{
 const f=fixture(t);
 const request=f.participants.app.freshRequest(f.grant.body.id);
 refusal(()=>f.issue('bridge','fresh',{request}),'ROLE_BINDING');
 // A legitimate role can still request fresh after a forged cross-role attempt.
 const response=f.issue('app','fresh',{request});
 assert.equal(response.body.role,'app');
 const ack=signed({schema:'r16.revocation-ack.v1',grantId:f.grant.body.id,
   version:2,role:'app',peerId:f.peers.app.id,newOperationsStopped:true},f.peerKeys.app);
 refusal(()=>f.issue('bridge','acknowledgeRevocation',{proof:ack}),'ROLE_BINDING');
});
test('human revocation proof must pin exact grant hash and signed release id',t=>{
 const f=fixture(t);
 const intent={schema:'mht.human-authorization.v1',action:'revoke_grant',
   grantId:f.grant.body.id,expectedVersion:1,expectedGrantHash:'0'.repeat(64),
   releaseId:f.release.body.id,issuedAt:f.now(),nonce:randomUUID()};
 refusal(()=>runMinimalTrustOnce({...f.args,ownerApproval:signed(intent,f.humanKey)}),'OWNER_TARGET_CHANGED');
 refusal(()=>runMinimalTrustOnce({...f.args,ownerApproval:signed({
   ...intent,nonce:randomUUID(),expectedGrantHash:digest(f.grant),releaseId:'wrong-release'},f.humanKey)}),'OWNER_TARGET_CHANGED');
 assert.equal(f.readIssuer().grants[0].status,'ACTIVE');
});
test('closing replay journal while one issuer session is live cannot create a second writer',t=>{
 const f=fixture(t);
 const issuerStore=new ProtectedStore({directory:f.issuerDirectory,create:false,now:f.now});
 const replayStore=new ProtectedStore({directory:f.replayDirectory,create:false,now:f.now});
 try {
   const instance=f.trust({
     issuerStore,replayStore,issuerPrivateKey:f.issuerKey,
     releasePublicKey:f.args.releasePublicKey,issuerPublicKey:f.args.issuerPublicKey,
     release:f.release,grantId:f.grant.body.id,resolveProject:f.resolveProject,
     humanAuthorityPublicKey:f.args.humanAuthorityPublicKey,now:f.now,
   });
   assert.deepEqual(instance.issue(f.envelope('app','grant',{})),f.grant);
   refusal(()=>f.issue('app','grant',{}),'STATE_BUSY');
 } finally{replayStore.close();issuerStore.close();}
 assert.deepEqual(f.issue('app','grant',{}),f.grant);
});
test('fresh challenge and repeated failed human approval cannot be silently upgraded to a grant mutation',t=>{
 const f=fixture(t);
 const approval=signed({schema:'mht.human-authorization.v1',action:'create_grant',
   grantId:f.grant.body.id,expectedVersion:1,expectedGrantHash:digest(f.grant),
   releaseId:f.release.body.id,issuedAt:f.now(),nonce:randomUUID()},f.humanKey);
 refusal(()=>runMinimalTrustOnce({...f.args,ownerApproval:approval}),'OWNER_TARGET_CHANGED');
 assert.equal(f.readIssuer().grants.length,1);
});

test('durable replay fence survives actual short-lived child process exits',t=>{
 const f=fixture(t),message=f.envelope('app','grant',{});
 const configPath=path.join(f.temp,'disposable-child-test.json');
 const input={issuerDirectory:f.issuerDirectory,replayDirectory:f.replayDirectory,
   issuerPkcs8:f.issuerKey.export({format:'der',type:'pkcs8'}).toString('base64'),
   issuerPublicKey:f.args.issuerPublicKey,
   releasePublicKey:f.args.releasePublicKey,
   release:f.release,grantId:f.grant.body.id,
   humanAuthorityPublicKey:f.args.humanAuthorityPublicKey,
   project:f.project,mode:'active',now:f.now(),envelope:message};
 fs.writeFileSync(configPath,JSON.stringify(input),{mode:0o600});
 const child=new URL('./fixtures/issuer-once-child.mjs',import.meta.url).pathname;
 const exec=()=>spawnSync(process.execPath,[child,configPath],{
   encoding:'utf8',timeout:5000,env:{PATH:process.env.PATH},maxBuffer:32768,
 });
 const one=exec();
 assert.equal(one.status,0,one.stderr.slice(0,180));
 assert.deepEqual(JSON.parse(one.stdout),{ok:true,value:f.grant});
 const second=exec();
 assert.equal(second.status,1);
 assert.deepEqual(JSON.parse(second.stdout),{ok:false,error:'REPLAY_REJECTED'});
 // The synthetic private key fixture is removed with the disposable test tree.
 fs.unlinkSync(configPath);
});

test('all three revocation acknowledgements close the signed Human revoke lifecycle',t=>{
 const f=fixture(t);
 for(const role of ROLES)f.connect(role);
 const intent=signed({schema:'mht.human-authorization.v1',action:'revoke_grant',
   grantId:f.grant.body.id,expectedVersion:1,expectedGrantHash:digest(f.grant),
   releaseId:f.release.body.id,issuedAt:f.now(),nonce:randomUUID()},f.humanKey);
 const revoked=runMinimalTrustOnce({...f.args,ownerApproval:intent});
 assert.equal(revoked.body.version,2);
 const ackStates=[];
 for(const role of ROLES){
   const p=f.participants[role],req=p.freshRequest(f.grant.body.id);
   const rep=f.issue(role,'fresh',{request:req});
   assert.equal(p.acceptFresh({response:rep,grant:f.grant}).status,'REVOKED');
   const proof=p.revocationAck();
   const result=f.issue(role,'acknowledgeRevocation',{proof});
   ackStates.push(result.status);
 }
 assert.deepEqual(ackStates,['WAITING_OFFLINE_ACK','WAITING_OFFLINE_ACK','REVOKED']);
 const report=signed({schema:'r16.participant-heartbeat.v1',role:'app',
   peerId:f.peers.app.id,grantId:f.grant.body.id,grantVersion:2,
   issuedAt:f.now(),expiresAt:f.now()+30000,ready:false,credentialValid:true,
   unresolved:false,projects:[]},f.peerKeys.app);
 const h=f.issue('app','heartbeat',{report});
 assert.equal(h.revoked,true);assert.equal(h.revocationComplete,true);
 assert.equal(h.connectRequested,false);
});
test('untrusted role request cannot create, widen, or revoke a Human grant',t=>{
 const f=fixture(t);
 for(const action of ['createGrant','revoke','updateGrant','signRelease']){
   refusal(()=>f.issue('app',action,{grantId:f.grant.body.id}),'ISSUER_ACTION');
 }
 assert.equal(f.readIssuer().grants.length,1);
});

test('configured Human enrollment Grant hash never authorizes a different persisted Grant',t=>{
 const f=fixture(t);
 refusal(()=>f.rawIssue(f.envelope('app','grant',{}),
   {expectedGrantHash:'f'.repeat(64)}),'GRANT_HASH_BINDING');
 assert.deepEqual(f.rawIssue(f.envelope('app','grant',{}),
   {expectedGrantHash:digest(f.grant)}),f.grant);
});

test('intent survives expiry and different-nonce mutation is blocked after crash before effect',t=>{
 const f=fixture(t),env=f.envelope('app','prepare',{grantId:f.grant.body.id,request:{},proofs:{},release:f.release});
 assert.throws(()=>f.rawIssue(env,{fault:stage=>{if(stage==='after_intent')throw Error('simulated-crash');}}));
 f.advance(180001);
 const status=f.issue('app','nonceStatus',{nonce:env.body.nonce,requestHash:digest(env)});
 assert.deepEqual(status,{status:'UNKNOWN',retryPermitted:false});
 refusal(()=>f.issue('app','prepare',{grantId:f.grant.body.id,request:{},proofs:{},release:f.release}),'ISSUER_RECOVERY_REQUIRED');
 assert.equal(f.readIssuer().grants[0].version,1);
});
test('crash after durable result allows result lookup without executing again',t=>{
 const f=fixture(t),env=f.envelope('app','grant',{});
 assert.throws(()=>f.rawIssue(env,{fault:stage=>{if(stage==='after_result')throw Error('lost-response');}}));
 const status=f.issue('app','nonceStatus',{nonce:env.body.nonce,requestHash:digest(env)});
 assert.deepEqual(status,{status:'RESULT',result:f.grant,resultHash:digest(f.grant),retryPermitted:false});
 refusal(()=>f.rawIssue(env),'REPLAY_REJECTED');
 const foreign=f.issue('native','nonceStatus',{nonce:env.body.nonce,requestHash:digest(env)});
 assert.deepEqual(foreign,{status:'NOT_FOUND',retryPermitted:false});
});
test('human revoke after effect crash preserves UNKNOWN and never repeats under new nonce',t=>{
 const f=fixture(t);
 const body={schema:'mht.human-authorization.v1',action:'revoke_grant',grantId:f.grant.body.id,
   expectedVersion:1,expectedGrantHash:digest(f.grant),releaseId:f.release.body.id,issuedAt:f.now(),nonce:randomUUID()};
 const approval=signed(body,f.humanKey);
 assert.throws(()=>runMinimalTrustOnce({...f.args,ownerApproval:approval,
   fault:stage=>{if(stage==='after_effect')throw Error('crash-after-revoke');}}));
 assert.equal(f.readIssuer().grants[0].status,'REVOKED');
 const status=signed({...body,action:'revoke_status',nonce:randomUUID(),targetNonce:body.nonce,requestHash:digest(approval)},f.humanKey);
 assert.deepEqual(runMinimalTrustOnce({...f.args,ownerApproval:status}),{status:'UNKNOWN',retryPermitted:false});
 refusal(()=>runMinimalTrustOnce({...f.args,ownerApproval:signed({...body,expectedVersion:2,nonce:randomUUID()},f.humanKey)}),
   'ISSUER_RECOVERY_REQUIRED');
});
test('expired release still permits authenticated recovery revoke but never new business',t=>{
 const f=fixture(t);f.advance(31*86400000);
 const body={schema:'mht.human-authorization.v1',action:'revoke_grant',grantId:f.grant.body.id,
   expectedVersion:1,expectedGrantHash:digest(f.grant),releaseId:f.release.body.id,issuedAt:f.now(),nonce:randomUUID()};
 const result=runMinimalTrustOnce({...f.args,mode:'recovery_only',ownerApproval:signed(body,f.humanKey)});
 assert.equal(result.body.version,2);
 refusal(()=>f.rawIssue(f.envelope('app','prepare',{}),{mode:'recovery_only'}),'RECOVERY_ONLY');
 assert.throws(()=>f.issue('app','grant',{}));
});
test('handoff initializes only against exact closed issuer snapshot and remains durably bound',t=>{
 const f=fixture(t),binding={handoffHash:digest('handoff'),issuerSnapshotHash:digest(f.readIssuer()),epoch:1,admissionExpiresAt:f.now()+1000};
 const a=f.envelope('app','grant',{});
 refusal(()=>f.rawIssue(a,{handoffBinding:{...binding,issuerSnapshotHash:digest('wrong')}}),'HANDOFF_SNAPSHOT');
 assert.deepEqual(f.rawIssue(a,{handoffBinding:binding}),f.grant);
 f.advance(1001);
 assert.deepEqual(f.rawIssue(f.envelope('app','grant',{}),{handoffBinding:binding}),f.grant);
 refusal(()=>f.rawIssue(f.envelope('app','grant',{}),{handoffBinding:{...binding,epoch:2}}),'HANDOFF_BINDING');
});

test('actual child exits at intent, effect and result boundaries preserve durable outcome',async t=>{
 for(const stage of ['after_intent','after_effect','after_result'])await t.test(stage,t=>{
   const f=fixture(t),body={schema:'mht.human-authorization.v1',action:'revoke_grant',grantId:f.grant.body.id,
     expectedVersion:1,expectedGrantHash:digest(f.grant),releaseId:f.release.body.id,issuedAt:f.now(),nonce:randomUUID()};
   const approval=signed(body,f.humanKey),file=path.join(f.temp,'crash-fixture.json');
   const input={...f.args,issuerPrivateKey:undefined,resolveProject:undefined,now:undefined,
     issuerPkcs8:f.issuerKey.export({format:'der',type:'pkcs8'}).toString('base64'),
     ownerApproval:approval,at:f.now(),stage};
   fs.writeFileSync(file,JSON.stringify(input),{mode:0o600});
   const moduleUrl=new URL('../src/minimal-trust-issuer.mjs',import.meta.url).href;
   const script=`import fs from 'node:fs';import {createPrivateKey} from 'node:crypto';
     import {runMinimalTrustOnce} from ${JSON.stringify(moduleUrl)};
     const f=JSON.parse(fs.readFileSync(process.argv[1],'utf8'));
     runMinimalTrustOnce({...f,issuerPrivateKey:createPrivateKey({key:Buffer.from(f.issuerPkcs8,'base64'),format:'der',type:'pkcs8'}),
       resolveProject:()=>{throw Error('unexpected-project');},now:()=>f.at,
       fault:stage=>{if(stage===f.stage)process.exit(19);}});`;
   const child=spawnSync(process.execPath,['--input-type=module','-e',script,file],{
     encoding:'utf8',timeout:5000,env:{PATH:'/usr/bin:/bin'},maxBuffer:4096});
   assert.equal(child.status,19,child.stderr);
   assert.equal(f.readIssuer().grants[0].status,stage==='after_intent'?'ACTIVE':'REVOKED');
   const query=signed({...body,action:'revoke_status',nonce:randomUUID(),targetNonce:body.nonce,requestHash:digest(approval)},f.humanKey);
   const result=runMinimalTrustOnce({...f.args,ownerApproval:query});
   assert.equal(result.status,stage==='after_result'?'RESULT':'UNKNOWN');
   assert.equal(result.retryPermitted,false);
   if(stage==='after_result')assert.equal(result.result.body.version,2);
 });
});

test('malformed close request does not consume intent or disable fresh human revocation',t=>{
 const f=fixture(t),env=f.envelope('app','closeLease',{});
 refusal(()=>f.rawIssue(env),'TRUST_INPUT_SHAPE');
 assert.deepEqual(f.issue('app','nonceStatus',{nonce:env.body.nonce,requestHash:digest(env)}),
   {status:'NOT_FOUND',retryPermitted:false});
 const approval=signed({schema:'mht.human-authorization.v1',action:'revoke_grant',grantId:f.grant.body.id,
   expectedVersion:1,expectedGrantHash:digest(f.grant),releaseId:f.release.body.id,issuedAt:f.now(),nonce:randomUUID()},f.humanKey);
 assert.equal(runMinimalTrustOnce({...f.args,ownerApproval:approval}).body.version,2);
});
test('real UNKNOWN close remains preserved while independent human revoke succeeds',t=>{
 const f=fixture(t);for(const role of ROLES)f.connect(role);
 const request={schema:'r16.prepare.v1',requestId:randomUUID(),grantId:f.grant.body.id,grantVersion:1,
   project:f.project,channel:f.grant.body.channel,versions:f.versions,actions:['find_symbol'],issuedAt:f.now()};
 const proofs=Object.fromEntries(ROLES.map(role=>[role,signed(request,f.peerKeys[role])]));
 const lease=f.issue('app','prepare',{grantId:f.grant.body.id,request,proofs,release:f.release});
 for(const role of ROLES)f.participants[role].prepare({lease,grant:f.grant,release:f.release});
 const evidence=Object.fromEntries(ROLES.map(role=>[role,f.participants[role].stop({lease})]));
 const envelope=f.envelope('native','closeLease',{grantId:f.grant.body.id,projectId:f.project.id,lease,evidence});
 assert.throws(()=>f.rawIssue(envelope,{fault:stage=>{if(stage==='after_effect')throw Error('unknown-close');}}));
 const approval=signed({schema:'mht.human-authorization.v1',action:'revoke_grant',grantId:f.grant.body.id,
   expectedVersion:1,expectedGrantHash:digest(f.grant),releaseId:f.release.body.id,issuedAt:f.now(),nonce:randomUUID()},f.humanKey);
 assert.equal(runMinimalTrustOnce({...f.args,ownerApproval:approval}).body.version,2);
 assert.deepEqual(f.issue('native','nonceStatus',{nonce:envelope.body.nonce,requestHash:digest(envelope)}),
   {status:'UNKNOWN',retryPermitted:false});
 assert.equal(f.readIssuer().grants[0].projects[0].active,null);
});
