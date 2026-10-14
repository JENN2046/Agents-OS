import {test} from 'node:test';
import {PassThrough} from 'node:stream';
import assert from 'node:assert/strict';
import {generateKeyPairSync,randomUUID} from 'node:crypto';
import {signed,exportPublicKey,digest,ACTIONS} from '../src/lease-core.mjs';
import {validateInstalledTrustPolicy,validateTrustRoots,parseOnceRequest,runProtectedOnce,readBoundedOnceInput,TRUST_ROOTS_PATH}
 from '../src/minimal-trust-issuer-once.mjs';
import {inspectReviewedTrustRuntime,BOOTSTRAP_CONFIG,ENTRY}
 from '../src/trusted-launcher.mjs';
import {runtimeVersion} from '../authority/runtime-manifest.mjs';
const key=()=>generateKeyPairSync('ed25519').privateKey;
function setup(){
 const issuer=key(),releaseKey=key(),human=key(),enroller=key(),now=1791870000000;
 const release=signed({schema:'r16.release.v1',id:'r16-daily-20261012-r17',
   issuedAt:now-3600000,notAfter:now+86400000,
   formats:['r16.workspace.v1'],
   versions:{app:digest('app'),bridge:digest('bridge'),native:digest('native')},
   actions:ACTIONS,permissionVersion:1},releaseKey);
 const grantHash=digest('real-signed-grant-fixture');
 const enrollment=signed({schema:'mht.human-enrollment.v1',grantId:'r16-projects-daily',
   grantHash,releaseId:release.body.id,releaseHash:digest(release),enrolledAt:now-1000,expiresAt:now+86400000,
   humanUid:1000,humanSubject:'local-human:1000',humanPublicKey:exportPublicKey(human)},enroller);
 const handoff=signed({schema:'mht.issuer-handoff.v1',grantId:'r16-projects-daily',grantHash,
   releaseHash:digest(release),issuerSnapshotHash:digest('closed-synthetic-ledger'),installationProfile:'isolated',
   epoch:1,mode:'recovery_only',oldWriterClosed:true,
   participantClosureHashes:{app:digest('app-closed'),bridge:digest('bridge-closed'),native:digest('native-closed')},
   issuedAt:now-1000,expiresAt:now+86400000},enroller);
 const roots={schema:'mht.trust-roots.v1',grantId:'r16-projects-daily',issuerPublicKey:exportPublicKey(issuer),
   releasePublicKey:exportPublicKey(releaseKey),enrollmentAuthorityPublicKey:exportPublicKey(enroller),
   releaseHash:digest(release),installationProfile:'isolated',handoffHash:digest(handoff)};
 const config={schema:'mht.installed-issuer.v1',enrollment,handoff,
   enrollmentAuthorityPublicKey:exportPublicKey(enroller),
   grantId:'r16-projects-daily',humanAuthorityPublicKey:exportPublicKey(human),
   issuerPublicKey:exportPublicKey(issuer),mode:'recovery_only',release,
   releasePublicKey:exportPublicKey(releaseKey),trustCutoverPhase:'RECOVERY_SHADOW'};
 return{issuer,releaseKey,human,enroller,now,release,enrollment,config,grantHash,roots,handoff};
}
test('human identity enrollment binds registered UID, subject, grant hash and exact signed Release',()=>{
 const f=setup(),p=validateInstalledTrustPolicy(f.config,{trustRoots:f.roots,now:f.now,publicKeyHint:f.config.issuerPublicKey});
 assert.equal(p.mode,'recovery_only');
 assert.equal(p.grantHash,f.grantHash);
 assert.equal(p.humanAuthorityPublicKey,exportPublicKey(f.human));
});
test('unregistered human identity cannot substitute its own enrollment public key',()=>{
 const f=setup();f.config.enrollmentAuthorityPublicKey=exportPublicKey(key());
 assert.throws(()=>validateInstalledTrustPolicy(f.config,{trustRoots:f.roots,now:f.now}));
});
test('human UID drift rejects approval even if enrollment issuer signs it',()=>{
 const f=setup();f.config.enrollment=signed({...f.enrollment.body,humanUid:999},f.enroller);
 assert.throws(()=>validateInstalledTrustPolicy(f.config,{trustRoots:f.roots,now:f.now}));
});
test('expired enrollment authenticates recovery identity without extending business authorization',()=>{
 const f=setup();assert.equal(validateInstalledTrustPolicy(f.config,{trustRoots:f.roots,now:f.now+86400001}).mode,'recovery_only');
 f.config.mode='active';assert.throws(()=>validateInstalledTrustPolicy(f.config,{trustRoots:f.roots,now:f.now+86400001}));
});
test('new issuer key replacement cannot be selected by caller',()=>{
 const f=setup();assert.throws(()=>validateInstalledTrustPolicy(f.config,{trustRoots:f.roots,now:f.now,publicKeyHint:exportPublicKey(key())}));
});
test('ordinary business mode cannot start before a formal cutover',()=>{
 const f=setup();f.config.mode='active';
 assert.throws(()=>validateInstalledTrustPolicy(f.config,{trustRoots:f.roots,now:f.now}));
});
test('extra config field cannot smuggle a user chosen credential path',()=>{
 const f=setup();f.config.credentialPath='/tmp/attacker';
 assert.throws(()=>validateInstalledTrustPolicy(f.config,{trustRoots:f.roots,now:f.now}));
});
test('socket line framing forbids second JSON message, trailing junk and a null request',()=>{
 const base={schema:'mht.once-request.v1',operation:'issuer',envelope:{body:{}}};
 const one=Buffer.from(JSON.stringify(base)+'\n');
 assert.deepEqual(parseOnceRequest(one,'issuer').envelope,base.envelope);
 for(const bad of [Buffer.from(JSON.stringify(base)+'\n'+JSON.stringify(base)+'\n'),
   Buffer.from(JSON.stringify(base)+'\nanything'),Buffer.from('null\n')]){
   assert.throws(()=>parseOnceRequest(bad,'issuer'));
 }
});
test('human approval cannot cross the Issuer socket lane',()=>{
 const p={schema:'mht.once-request.v1',operation:'revoke',ownerApproval:{}};
 assert.throws(()=>parseOnceRequest(Buffer.from(JSON.stringify(p)+'\n'),'issuer'));
});
test('issuer envelope cannot cross the root-only Human socket lane',()=>{
 const p={schema:'mht.once-request.v1',operation:'issuer',envelope:{}};
 assert.throws(()=>parseOnceRequest(Buffer.from(JSON.stringify(p)+'\n'),'human'));
});
test('trusted per-request entry derives mode, keys, human identity and fixed store paths from installed policy',async()=>{
 const f=setup(),request={schema:'mht.once-request.v1',operation:'issuer',envelope:{payload:'synthetic'}};
 let seen;
 const result=await runProtectedOnce({
 loadCredential:()=>({key:f.issuer,unit:'minimal-human-trust-issuer@10.service',lane:'issuer'}),
 loadConfig:()=>JSON.stringify(f.config),
 loadTrustRoots:()=>JSON.stringify(f.roots),
 readStdin:()=>Buffer.from(JSON.stringify(request)+'\n'),
 now:()=>f.now,
 resolveProject:()=>{},
 runIssuer:options=>{seen=options;return {simulated:true};}
 });
 assert.deepEqual(result,{simulated:true});
 assert.equal(seen.mode,'recovery_only');
 assert.equal(seen.grantId,f.config.grantId);
 assert.equal(seen.issuerPublicKey,f.config.issuerPublicKey);
 assert.equal(seen.expectedGrantHash,f.grantHash);
 assert.equal(seen.humanAuthorityPublicKey,f.config.humanAuthorityPublicKey);
 assert.equal(seen.issuerDirectory,'/var/lib/minimal-human-trust/isolated/issuer');
 assert.equal(seen.replayDirectory,'/var/lib/minimal-human-trust/isolated/replay');
 assert.deepEqual(seen.envelope,request.envelope);
 assert.equal(seen.ownerApproval,null);
});
test('root-only human socket passes only the exact human proof',async()=>{
 const f=setup(),request={schema:'mht.once-request.v1',operation:'revoke',ownerApproval:{source:'test'}};
 let seen;
 await runProtectedOnce({
 loadCredential:()=>({key:f.issuer,lane:'human'}),
 loadConfig:()=>JSON.stringify(f.config),
 loadTrustRoots:()=>JSON.stringify(f.roots),
 readStdin:()=>Buffer.from(JSON.stringify(request)+'\n'),
 now:()=>f.now,
 runIssuer:options=>{seen=options;return {simulated:true};}
 });
 assert.deepEqual(seen.ownerApproval,request.ownerApproval);assert.equal(seen.envelope,null);
});
test('trusted launcher rejects execution under a regular user in the real runtime',()=>{
 assert.throws(()=>inspectReviewedTrustRuntime({euid:1000,readFile:()=>{throw Error('must not read');}}));
});
test('trusted launcher binds proposed Native runtime to signed Release before importing its entry',()=>{
 const f=setup();
 const files=Object.fromEntries([ENTRY,'src/systemd-issuer-credential.mjs',
   'src/minimal-trust-issuer.mjs','src/lease-core.mjs','src/control-clock.mjs',
   'authority/recovery-handoff.mjs','migration/r17-one-time-recovery-admission.mjs']
     .map(x=>[x,digest('tested-bundle:'+x)]));
 const manifest={schema:'r16.runtime-code.v1',role:'native',entry:'host/native-runner.mjs',
   files:{...files,'host/native-runner.mjs':digest('existing-native')}};
 const version=runtimeVersion(manifest,'native');
 const release=signed({...f.release.body,versions:{...f.release.body.versions,native:version}},f.releaseKey);
 const handoff=signed({...f.handoff.body,releaseHash:digest(release)},f.enroller);
 const enrollment=signed({...f.enrollment.body,releaseHash:digest(release)},f.enroller);
 const cfg={...f.config,release,handoff,enrollment};
 const roots={...f.roots,releaseHash:digest(release),handoffHash:digest(handoff)};
 const directory='/opt/r16/releases/'+release.body.id;
 const paths=new Map([[BOOTSTRAP_CONFIG,Buffer.from(JSON.stringify(cfg))],
 [TRUST_ROOTS_PATH,Buffer.from(JSON.stringify(roots))],
 [directory+'/native-manifest.json',Buffer.from(JSON.stringify(manifest))]]);
 const approved=inspectReviewedTrustRuntime({euid:0,now:()=>f.now,readFile:path=>{
   assert.ok(paths.has(path),'unexpected root-protected read '+path);
   return paths.get(path);
 },verify:()=>version});
 assert.ok(approved.entry.endsWith('/'+ENTRY));
 assert.equal(approved.release,release.body.id);
 for(const dependency of ['authority/recovery-handoff.mjs','migration/r17-one-time-recovery-admission.mjs']){
   const incomplete={...manifest,files:{...manifest.files}};
   delete incomplete.files[dependency];
   paths.set(directory+'/native-manifest.json',Buffer.from(JSON.stringify(incomplete)));
   assert.throws(()=>inspectReviewedTrustRuntime({euid:0,now:()=>f.now,
     readFile:p=>paths.get(p),verify:()=>version}));
 }
 const changed={...manifest,files:{...manifest.files,[ENTRY]:digest('tampered')}};
 paths.set(directory+'/native-manifest.json',Buffer.from(JSON.stringify(changed)));
 assert.throws(()=>inspectReviewedTrustRuntime({euid:0,now:()=>f.now,
   readFile:p=>paths.get(p),verify:()=>version}));
});

test('coherent attacker config and self-signed enrollment cannot replace independent roots',()=>{
 const f=setup(),attacker=setup();
 assert.throws(()=>validateInstalledTrustPolicy(attacker.config,{trustRoots:f.roots,now:f.now}));
 assert.throws(()=>validateInstalledTrustPolicy(f.config,{now:f.now}));
 assert.throws(()=>validateTrustRoots({...f.roots,arbitrary:'field'}));
});
test('same release id with different signed body fails exact release binding',()=>{
 const f=setup();f.config.release=signed({...f.release.body,notAfter:f.release.body.notAfter+1},f.releaseKey);
 assert.throws(()=>validateInstalledTrustPolicy(f.config,{trustRoots:f.roots,now:f.now}));
});
test('unsigned handoff, open writer, or missing participant evidence prevents activation admission',()=>{
 for(const patch of [{oldWriterClosed:false},{participantClosureHashes:{app:digest('app')}}]){
   const f=setup();f.config.handoff=signed({...f.handoff.body,...patch},f.enroller);
   f.roots.handoffHash=digest(f.config.handoff);
   assert.throws(()=>validateInstalledTrustPolicy(f.config,{trustRoots:f.roots,now:f.now}));
 }
});
test('bounded socket input accepts one line without waiting for EOF',async()=>{
 const stream=new PassThrough(),pending=readBoundedOnceInput(stream);
 stream.write('{"message":"test"}\n');
 assert.equal((await pending).toString(),'{"message":"test"}\n');stream.destroy();
});
test('bounded socket input refuses oversized and multi-frame input before parse',async()=>{
 for(const bytes of [Buffer.alloc(262145,65),Buffer.from('{}\n{}\n')]){
   const stream=new PassThrough(),pending=readBoundedOnceInput(stream);
   stream.write(bytes);await assert.rejects(pending);stream.destroy();
 }
});
test('socket input deadline refuses a client that never sends a complete line',async()=>{
 const stream=new PassThrough(),pending=readBoundedOnceInput(stream);stream.write('{');
 await assert.rejects(pending,{code:'MHT_INPUT_TIMEOUT'});stream.destroy();
});
