// Disposable ProtectedStore/crypto + explicit fake root metadata only. No root,
// service, production descriptor, live ledger or real human admission is used.
import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import {spawn} from 'node:child_process';
import {randomUUID,generateKeyPairSync,createHash} from 'node:crypto';
import {pathToFileURL} from 'node:url';
import {ProtectedStore,signed,digest,canonical,exportPublicKey,ROLES,ACTIONS,participantInitialState,LEASE_MS,RENEW_BEFORE_MS} from '../../src/lease-core.mjs';
Error.stackTraceLimit=0;
const PATH='/etc/r16-maintenance/source19-native-transition-r1-native-history.json';
const STORE='/var/lib/r16-native/grants/r16-projects-daily/dispatcher';
const POLICY='EXACT_INHERITED_LOCAL_UNCERTAINTY_ONLY';
const GRANT='00ac437d66143e627132975555d06396d69ff69616f630d19e3622627e15c5e6';
const NATIVE='2516e881b0622b3ac2d53c454e6ccf9950441c5cb3c26a53500b45d3b1dbe7b4';
const PUB='56e1df18a54950ea346a51654e61df60afe33cb9928ae77293b2cf336fd8a5ec';
const DELIVERY='b8645f6fe206e84dd07c2c6c166bfe4016d1deefca28bf9545dcfa1560f013e9';
const TARGET='r16-daily-20261017-source19-native-lifecycle-r1';
const sha=b=>createHash('sha256').update(b).digest('hex');
const dispatcherFile=new URL('./payload/host/workspace-dispatcher.mjs',import.meta.url);
const runtimeSource=fs.readFileSync(dispatcherFile,'utf8');
const helperSource=fs.readFileSync(new URL('./history-baseline.mjs',import.meta.url),'utf8');
const coreURL=new URL('../../src/lease-core.mjs',import.meta.url).href;
const clockURL=new URL('../../src/control-clock.mjs',import.meta.url).href;
const data=source=>'data:text/javascript;base64,'+Buffer.from(source).toString('base64');
async function fixture(t,{count=3}={}){
 const dir=fs.mkdtempSync(path.join(os.tmpdir(),'native-history-'));fs.chmodSync(dir,0o700);
 const directory=path.join(dir,'dispatcher'),now=()=>1792250000000;
 const controls=Array.from({length:count},(_,i)=>({id:'inherited-'+String(i).padStart(5,'0'),hash:digest({originalUnknownControl:i}),status:'UNKNOWN'}));
 const rawStore=new ProtectedStore({directory,create:true,now,initial:{kind:'r16.native-dispatch.v1',controls,pending:[],projects:[],revoked:false,version:1}});
 t.after(()=>{try{rawStore.close();}catch{}fs.rmSync(dir,{recursive:true,force:true});});
 const st=fs.statSync(directory),store=Object.create(ProtectedStore.prototype);
 Object.assign(store,{dir:STORE,snapshot:()=>rawStore.snapshot(),transact:fn=>rawStore.transact(fn),close:()=>rawStore.close()});
 const key=()=>generateKeyPairSync('ed25519').privateKey,issuer=key(),releaseKey=key(),keys=Object.fromEntries(ROLES.map(r=>[r,key()]));
 const root=path.join(dir,'workspace');fs.mkdirSync(root,{mode:0o700});const ws=fs.statSync(root);
 const grant=signed({schema:'r16.workspace.v1',id:'r16-projects-daily',version:1,createdAt:now(),workspace:{id:'fixture-workspace',root,dev:ws.dev,ino:ws.ino},actions:ACTIONS,channel:'main',peers:Object.fromEntries(ROLES.map(r=>[r,{id:'fixture-'+r,publicKey:exportPublicKey(keys[r])}]))},issuer);
 const historicalOperations=[],participantBytes={};
 const oldVersions={app:'235a5b919c65ac1d73290732d2b2014c24a338cc4b6795a5064e804803ec1e7a',bridge:'9c58c33478388003fd52da0cb15736ec951a9bfc9cf29738e20de5d741921352',native:'76319c50acaec649967986c1f12e6923ba4f664ac3230596ed2703fce3470ae6'};
 const oldPins=['fd13e74ce69cb8ec30817ca0a48631cf3a6b6b2b08a410cc1b442df41992cc1f','38f6af1386e78e5d7ccd0710077d6a3a5e753e81722dd10f11a3a2ff9bd85da1'];
 for(const [index,projectId]of ['p2vox','pmog2'].entries()){
  const projectRoot=path.join(root,projectId);fs.mkdirSync(projectRoot,{mode:0o700});const generation=[30,38][index],id=['c434da49-055a-43dc-a3e3-695cce137909','d0364f8b-3a68-4ca2-a396-7953b29cee4c'][index];
  const lease=signed({schema:'r16.lease.v1',phase:'PREPARED',grantId:grant.body.id,grantVersion:1,grantHash:digest(grant),project:{id:projectId,workspaceId:grant.body.workspace.id,root:projectRoot},channel:'main',versions:oldVersions,actions:['find_symbol'],generation,previousGeneration:generation-1,issuedAt:1000,expiresAt:1000+LEASE_MS,renewAt:1000+LEASE_MS-RENEW_BEFORE_MS,requestId:'fixture-'+index,releaseHash:digest('old-release')},issuer);
  const operation=signed({schema:'r16.operation.v1',id,grantId:grant.body.id,projectId,generation,leaseHash:digest(lease),channel:'main',action:'find_symbol',payloadHash:digest('fixture-symbol')},keys.app);historicalOperations.push(operation);
  const ps=new ProtectedStore({directory:path.join(directory,'project-'+projectId),create:true,now,initial:{...participantInitialState('native'),grant,version:1,lastGeneration:generation,active:{lease},closing:lease,operations:[{id,hash:digest(operation),projectId,generation,status:'UNKNOWN',outcome:null,resultHash:null}]}});ps.close();participantBytes[projectId]=fs.readFileSync(path.join(directory,'project-'+projectId,'state.json'));rawStore.transact(state=>state.projects.push(projectId));
 }
 const fixturePins=source=>oldPins.reduce((value,pin,index)=>value.replaceAll(pin,digest(historicalOperations[index])),source);
 const manifest={schema:'r16.runtime-code.v1',role:'native',entry:'host/native-runner.mjs',files:{'host/native-runner.mjs':digest('SYNTHETIC_ONLY_CODE_SLOT')}};
 const versions={app:'34731b300ccad9a1fbfd45b07422d847e8989d7e9dc052b0dda939cd99adb500',bridge:'9c58c33478388003fd52da0cb15736ec951a9bfc9cf29738e20de5d741921352',native:digest(manifest)};
 const release=signed({schema:'r16.release.v1',id:TARGET,issuedAt:now()-1000,notAfter:now()+3600000,versions,actions:ACTIONS,formats:['r16.workspace.v1'],permissionVersion:1},releaseKey);
 const pub={grant,release,versions,issuerPublicKey:exportPublicKey(issuer),releasePublicKey:exportPublicKey(releaseKey)};
 const registry={schema:'r16.native-ledgers.v1',grants:[{directory:STORE,dev:st.dev,ino:st.ino,grantId:'r16-projects-daily',grantHash:digest(grant),status:'READY'}]},registryRaw=Buffer.from(canonical(registry)+'\n');
 const instance={host:'jenn-System-Product-Name',unit:'r16-native.service',pid:72,startTicks:'12345',bootId:'11111111-2222-4333-8444-555555555555',invocationId:'a'.repeat(32),cgroup:'/system.slice/r16-native.service',nativeVersion:NATIVE};
 const controlHash=digest(controls),checkpoint={controlUnknownRows:controls,originalUnknown:{p2vox:{id:'c434da49-055a-43dc-a3e3-695cce137909',generation:30,hash:'fd13e74ce69cb8ec30817ca0a48631cf3a6b6b2b08a410cc1b442df41992cc1f'},pmog2:{id:'d0364f8b-3a68-4ca2-a396-7953b29cee4c',generation:38,hash:'38f6af1386e78e5d7ccd0710077d6a3a5e753e81722dd10f11a3a2ff9bd85da1'}},schema:'r16.source19-native-checkpoint.v1',completeRegisteredFileSet:true,noForeignWriters:true,noTemporaryFiles:true,newUnknown:[],inflight:[],originalSignaturesAndLeasesVerified:true,originalLeaseBindingsHash:'b'.repeat(64),registeredRootsHash:'c'.repeat(64),controlUnknownHash:controlHash,controlUnknownCount:count,nativeLedgerRegistration:{directory:STORE,dev:st.dev,ino:st.ino,registryHash:sha(registryRaw)}};
 for(const op of historicalOperations)checkpoint.originalUnknown[op.body.projectId].hash=digest(op);
 const plan={approvedAt:now()-2000,expiresAt:now()+298000,recoveryDeadline:now()+1798000,schema:'r16.source19-native-transition.plan.v1',scope:'SAME_PLAN_SOURCE19_NATIVE_MAINTENANCE_NOT_DRAINED',sourcePublicConfigHash:PUB,sourceDeliveryHash:DELIVERY,sourceNativeVersion:NATIVE,grantHash:digest(grant),targetReleaseId:TARGET,targetNativeVersion:versions.native,approvedControlUnknownHash:controlHash,approvedControlUnknownCount:count,allowNativeNonGracefulOnce:true,acceptUnprovenInflight:true,acceptPossibleUpstreamContinuation:true,nativeTargetHash:digest(instance),codeFreezeHash:'d'.repeat(64),originalBaselineHash:'e'.repeat(64),stopEpoch:randomUUID()};
 const hosts={'r16-owner.service':'jenn-System-Product-Name','r16-native.service':'jenn-System-Product-Name','r16-app.service':'VM-0-12-ubuntu','r16-bridge.service':'VM-0-12-ubuntu'};
 const proof={schema:'r16.source19-native-transition.stopped-fenced.v1',environment:'PRODUCTION',status:'STOPPED_FENCED_NOT_DRAINED',planHash:digest(plan),checkpointHash:digest(checkpoint),nativeTargetHash:digest(instance),sourcePublicConfigHash:PUB,sourceDeliveryHash:DELIVERY,grantHash:digest(grant),codeFreezeHash:plan.codeFreezeHash,originalBaselineHash:plan.originalBaselineHash,stopEpoch:plan.stopEpoch,controlUnknownHash:controlHash,controlUnknownCount:count,relayStopped:true,noForeignWriters:true,originalUnknownPreserved:true,globalExecution:'UNPROVEN',roleStopReceipt:false,businessAcceptance:false,forceTerminationUsed:true,issuedAt:now()-1000,expiresAt:now()+29000,actors:Object.fromEntries(Object.entries(hosts).map(([unit,host])=>[unit,{unit,host,mainPid:0,controlPid:0,cgroupEmpty:true,pendingJob:false,ownedPersistentFence:true}]))};
 const baseConfig={schema:'r16.native-host.v1',codeManifest:'/opt/r16/releases/'+TARGET+'/native-manifest.json',workspaceAlias:'fixture'};
 // Explicit immutable-pin fixture substitution; production exposes no override.
 const helper=await import(data(fixturePins(helperSource).replace(GRANT,digest(grant)).replace("'../../src/lease-core.mjs'",JSON.stringify(coreURL))));
 const input={plan,stoppedProof:proof,checkpoint,sourceNativeInstance:instance,nativeHostConfig:baseConfig,targetPublicConfig:pub,targetManifest:manifest,ledgerRegistry:registry,ledgerRegistryRaw:registryRaw,historicalOperations,now:now()};
 let descriptor=helper.buildNativeHistoryDescriptor(input),raw=Buffer.from(canonical(descriptor)),config={...baseConfig,nativeHistory:helper.nativeHistoryConfigBinding(descriptor)};
 const file=path.join(dir,'descriptor.json'),configFile=path.join(dir,'native-host.json'),registryFile=path.join(dir,'native-ledgers.json');fs.writeFileSync(file,raw,{mode:0o644});fs.writeFileSync(registryFile,registryRaw,{mode:0o644});
 const state={owner:0,gid:0,mode:0o100644,nlink:1,ancestorMode:0o40755,storeDev:st.dev,storeIno:st.ino,readCount:0};let descriptorFd;
 const decorate=(real,over)=>new Proxy(real,{get(target,key){if(Object.hasOwn(over,key))return over[key];const v=Reflect.get(target,key);return typeof v==='function'?v.bind(target):v;}});
 const fake={...fs,lstatSync(p){if(p===STORE)return decorate(fs.lstatSync(directory),{dev:state.storeDev,ino:state.storeIno});if([PATH,'/etc/r16/native-host.json','/etc/r16/native-ledgers.json'].includes(p))return decorate(fs.lstatSync(p===PATH?file:p.endsWith('native-host.json')?configFile:registryFile),{uid:state.owner,gid:state.gid,mode:state.mode,nlink:state.nlink});if(['/etc','/etc/r16-maintenance','/etc/r16'].includes(p))return {uid:0,gid:0,mode:state.ancestorMode,isSymbolicLink:()=>false,isDirectory:()=>true};return fs.lstatSync(p);},realpathSync(p){return p===STORE?STORE:fs.realpathSync(p);},openSync(p,...args){if([PATH,'/etc/r16/native-host.json','/etc/r16/native-ledgers.json'].includes(p)){state.readCount++;descriptorFd=fs.openSync(p===PATH?file:p.endsWith('native-host.json')?configFile:registryFile,...args);return descriptorFd;}return fs.openSync(p,...args);},fstatSync(fd){const real=fs.fstatSync(fd);return fd===descriptorFd?decorate(real,{uid:state.owner,gid:state.gid,mode:state.mode,nlink:state.nlink}):real;}};
 const globalKey='__nativeHistoryIO_'+randomUUID().replaceAll('-','');globalThis[globalKey]=fake;t.after(()=>delete globalThis[globalKey]);
 const fsURI=data('export default globalThis['+JSON.stringify(globalKey)+'];');
 let runtime=fixturePins(runtimeSource).replace(GRANT,digest(grant)).replace("'node:fs'",JSON.stringify(fsURI)).replace("'../src/lease-core.mjs'",JSON.stringify(coreURL)).replace("'../src/control-clock.mjs'",JSON.stringify(clockURL));
 const m=await import(data(runtime));
 const load=(at=now())=>{fs.writeFileSync(configFile,canonical(config),{mode:0o644});return m.loadNativeHistoryBaseline({store,config,publicConfig:pub,manifest,ledgerRegistry:registry,ledgerRegistryRaw:registryRaw,now:at});};
 const mutate=fn=>{descriptor=structuredClone(descriptor);fn(descriptor);raw=Buffer.from(canonical(descriptor));fs.writeFileSync(file,raw);config.nativeHistory=helper.nativeHistoryConfigBinding(descriptor);};
 const native={createWorkspaceCrownPort(){throw Error('unused');},async quiesceExecution(){return {schema:'r16.native-local-execution.v1',scope:'PROCESS_AND_OWNED_INDEXERS_ONLY',admissionClosed:true,workspaceCalls:0,queuedWriters:0,lifecycleCalls:0,indexers:[]};},async cleanup(){}};
 const dispatcher=baseline=>m.createWorkspaceDispatcher({store,directory,native,crown:{},grant,release,versions,signingKey:keys.native,issuerKey:pub.issuerPublicKey,releaseKey:pub.releasePublicKey,issuer:{fresh(){}},workspaceAlias:'fixture',databasePath:dir+'/unused.sqlite',now,inheritedHistory:baseline});
 return {dir,file,configFile,registryFile,m,helper,input,load,mutate,config,pub,manifest,registry,registryRaw,state,rawStore,store,dispatcher,controls,historicalOperations,participantBytes,descriptor:()=>descriptor};
}
test('9611 exact inherited controls remain UNKNOWN through real protected local-only close',async t=>{
 const f=await fixture(t,{count:9611}),before=f.rawStore.snapshot().controls,token=f.load(),d=f.dispatcher(token);
 const result=await d.shutdownLocalResources();for(const [projectId,bytes]of Object.entries(f.participantBytes))assert.deepEqual(fs.readFileSync(path.join(f.dir,'dispatcher/project-'+projectId,'state.json')),bytes);assert.equal(result.retainedHistory.length,2);assert.equal(result.globalExecution,'UNPROVEN');assert.equal(result.firstStopProof,'NOT_PROVEN');assert.equal(result.inheritedControlUncertainty.controlUnknownCount,9611);
 assert.deepEqual(f.rawStore.snapshot().controls,before);d.releaseStores();
});
test('no descriptor binding does not read root descriptor and retains strict local refusal',async t=>{
 const f=await fixture(t);delete f.config.nativeHistory;assert.equal(f.load(),null);assert.equal(f.state.readCount,0);await assert.rejects(f.dispatcher(null).shutdownLocalResources(),{code:'CURRENT_WORK_UNRESOLVED'});
});
test('root file owner, links, mode and writable ancestors are independently rejected',async t=>{
 for(const [field,value]of [['owner',1000],['nlink',2],['mode',0o100664],['ancestorMode',0o40775]]){
  const f=await fixture(t);f.state[field]=value;assert.throws(f.load,/HISTORY_ROOT_SOURCE_UNSAFE|HISTORY_DESCRIPTOR_UNSAFE/);
 }
});
test('descriptor digest and config base digest cannot drift',async t=>{
 const f=await fixture(t);f.config.nativeHistory.descriptorSha256='f'.repeat(64);assert.throws(f.load,{code:'HISTORY_DESCRIPTOR_DIGEST'});
 const g=await fixture(t);g.config.workspaceAlias='different';assert.throws(g.load,{code:'HISTORY_TARGET_BINDING'});
});
test('source checkpoint, plan and stopped Native identity must remain the same domain',async t=>{
 const f=await fixture(t);f.mutate(d=>{d.stopProof.planHash='f'.repeat(64);d.stopProofHash=digest(d.stopProof);});assert.throws(f.load,{code:'HISTORY_STOP_PROOF'});
 const g=await fixture(t);g.mutate(d=>{d.sourceNativeInstance.startTicks='23456';});assert.throws(g.load,{code:'HISTORY_SOURCE_INSTANCE'});
});
test('current target signature, release and actual manifest are checked',async t=>{
 const f=await fixture(t);f.pub.release.signature='invalid';assert.throws(f.load);
 const g=await fixture(t);g.manifest.files['host/native-runner.mjs']='e'.repeat(64);assert.throws(g.load,{code:'HISTORY_TARGET_BINDING'});
});
test('registry raw SHA preserves newlines, and Store dev/ino drift refuses',async t=>{
 const f=await fixture(t);assert.notEqual(f.descriptor().nativeLedgerRegistration.registryHash,digest(f.registry));assert.ok(f.load());
 const g=await fixture(t);g.state.storeIno++;assert.throws(g.load,{code:'HISTORY_REGISTRATION_DRIFT'});
});
test('new UNKNOWN, changed original hash or any INFLIGHT is refused without erasing rows',async t=>{
 for(const change of [s=>s.controls.push({id:'new-unknown',hash:'f'.repeat(64),status:'UNKNOWN'}),s=>s.controls[0].hash='a'.repeat(64),s=>s.controls.push({id:'current-inflight',hash:'e'.repeat(64),status:'INFLIGHT'})]){
  const f=await fixture(t),token=f.load(),d=f.dispatcher(token);f.rawStore.transact(change);const before=f.rawStore.snapshot().controls;
  await assert.rejects(d.shutdownLocalResources(),/HISTORY_CONTROL_SET_DRIFT|CURRENT_WORK_UNRESOLVED/);assert.deepEqual(f.rawStore.snapshot().controls,before);
 }
});
test('serialized or caller-made baseline cannot replace protected reader brand',async t=>{
 const f=await fixture(t),token=f.load();assert.throws(()=>f.dispatcher(structuredClone(token)),{code:'HISTORY_BRANDED_BASELINE_REQUIRED'});
});
test('runtime rejects unsafe old actor despite valid root descriptor digest',async t=>{
 for(const patch of [a=>a.mainPid=72,a=>a.controlPid=73,a=>a.cgroupEmpty=false,a=>a.pendingJob=true,a=>a.ownedPersistentFence=false]){
  const f=await fixture(t);f.mutate(d=>{patch(d.stopProof.actors['r16-native.service']);d.stopProofHash=digest(d.stopProof);});assert.throws(f.load,{code:'HISTORY_OLD_EXECUTOR_UNPROVEN'});
 }
});
test('historical receipt expiry is not reused as new authority; strong proof remains UNPROVEN',async t=>{
 const f=await fixture(t);const token=f.load(f.input.plan.expiresAt+1);assert.equal(token.firstStopProof,'NOT_PROVEN');assert.equal(token.globalExecution,'UNPROVEN');
});
test('descriptor constructor rejects current inflight, unapproved set and registration mismatch',async t=>{
 for(const change of [i=>i.checkpoint.inflight=['current'],i=>i.plan.approvedControlUnknownHash='f'.repeat(64),i=>i.checkpoint.nativeLedgerRegistration.ino++]){
  const f=await fixture(t),i=structuredClone({...f.input,ledgerRegistryRaw:undefined});i.ledgerRegistryRaw=f.registryRaw;change(i);assert.throws(()=>f.helper.buildNativeHistoryDescriptor(i));
 }
});
test('maintenance runner selects local exit only with branded root policy, no CLOSED heartbeat in that branch',()=>{
 const s=fs.readFileSync(new URL('./payload/host/native-runner.mjs',import.meta.url),'utf8');
 assert.ok(s.indexOf('loadNativeHistoryBaseline({store')<s.indexOf('native.initialize('));
 assert.match(s,/if\(inheritedHistory\)\{[\s\S]*?host\.shutdownLocalResources\(\)/);
 const local=s.slice(s.indexOf('     if(inheritedHistory){'),s.indexOf('     }else{',s.indexOf('     if(inheritedHistory){')));
 assert.doesNotMatch(local,/heartbeatReport\(true/);assert.match(local,/firstStopProof:'NOT_PROVEN'/);
 assert.match(s,/else\{[\s\S]*?await host\.stop\(\)/);assert.match(s,/if\(stopPromise\)return stopPromise/);assert.match(s,/if\(heartbeatWork\)/);
});

test('actual maintenance runner SIGTERM handler closes local host once, preserving 9611 controls',async t=>{
 const runner=fs.readFileSync(new URL('./payload/host/native-runner.mjs',import.meta.url),'utf8');
 const stopCode=runner.slice(runner.indexOf('  function stop(){'),runner.indexOf('  let initial;',runner.indexOf('  function stop(){')));
 const tmp=fs.mkdtempSync(path.join(os.tmpdir(),'native-history-signal-'));fs.chmodSync(tmp,0o700);t.after(()=>fs.rmSync(tmp,{recursive:true,force:true}));
 const file=path.join(tmp,'actual-runner-stop.mjs'),receipt=path.join(tmp,'receipt.json');
 const coreNames='ProtectedStore,signed,digest,canonical,exportPublicKey,ROLES,ACTIONS,participantInitialState,LEASE_MS,RENEW_BEFORE_MS';
 const prefix=`import assert from 'node:assert/strict';import fs from 'node:fs';import os from 'node:os';import path from 'node:path';import {randomUUID,generateKeyPairSync,createHash} from 'node:crypto';import {${coreNames}} from ${JSON.stringify(coreURL)};import {createHeadlessHost,acquireProcessLease,reportStopPhase} from ${JSON.stringify(new URL('../../host/headless-host.mjs',import.meta.url).href)};Error.stackTraceLimit=0;`;
 const globals={PATH,STORE,POLICY,GRANT,NATIVE,PUB,DELIVERY,TARGET,coreURL,clockURL,runtimeSource,helperSource};
 const definitions=Object.entries(globals).map(([n,v])=>'const '+n+'='+JSON.stringify(v)+';').join('')+`const sha=${sha.toString()};const data=${data.toString()};const fixture=${fixture.toString()};`;
 const setup=`const cleanups=[],f=await fixture({after:fn=>cleanups.push(fn)},{count:9611}),inheritedHistory=f.load(),dispatcher=f.dispatcher(inheritedHistory);let stoppedTransport=0;const host=createHeadlessHost({port:{...dispatcher,refresh:async()=>({status:'CLEANUP_ONLY'})},manifest:{name:'ProjectForge'},connect:async()=>({closed:new Promise(()=>{}),onMessage(){},send(){},async close(){stoppedTransport++;}}),acquireLease:()=>acquireProcessLease(f.dir)});let stopPromise=null,stopping=false,heartbeatTimer,sessionTimer,heartbeatWork=null;const stopReporter=()=>{},issuer={heartbeat(){throw Error('FALSE_CLOSED_HEARTBEAT');}};function heartbeatReport(){throw Error('FALSE_CLOSED_HEARTBEAT');}await host.start();`;
 const end=`const monitor=setInterval(async()=>{if(!stopPromise)return;clearInterval(monitor);await stopPromise;const state=JSON.parse(fs.readFileSync(path.join(f.dir,'dispatcher/state.json'),'utf8')).data;fs.writeFileSync(${JSON.stringify(receipt)},JSON.stringify({unknown:state.controls.filter(x=>x.status==='UNKNOWN').length,controlsPreserved:canonical(state.controls)===canonical(f.controls),globalExecution:inheritedHistory.globalExecution,writerReleased:!fs.existsSync(path.join(f.dir,'native-writer.lock')),stoppedTransport}));for(const fn of cleanups)await fn();},5);console.log('SIGNAL_READY');`;
 fs.writeFileSync(file,prefix+definitions+setup+stopCode+end);
 const child=spawn(process.execPath,[file],{stdio:['ignore','pipe','pipe']});t.after(()=>{if(child.exitCode===null)child.kill('SIGKILL');});let stdout='',stderr='';child.stderr.on('data',b=>{stderr+=b;});
 const exit=new Promise((resolve,reject)=>{child.once('error',reject);child.once('exit',(code,signal)=>resolve({code,signal}));});
 await new Promise((resolve,reject)=>{const timer=setTimeout(()=>reject(Error('fixture did not start: '+stderr.slice(-1000))),5000);child.stdout.on('data',b=>{stdout+=b;if(stdout.includes('SIGNAL_READY')){clearTimeout(timer);resolve();}});exit.then(()=>{if(!stdout.includes('SIGNAL_READY')){clearTimeout(timer);reject(Error('early fixture exit: '+stderr.slice(-1000)));}});});
 child.kill('SIGTERM');let timer;const result=await Promise.race([exit,new Promise((_,reject)=>{timer=setTimeout(()=>reject(Error('SIGTERM fixture did not close')),5000);})]).finally(()=>clearTimeout(timer));
 assert.deepEqual(result,{code:0,signal:null});assert.deepEqual(JSON.parse(fs.readFileSync(receipt)),{unknown:9611,controlsPreserved:true,globalExecution:'UNPROVEN',writerReleased:true,stoppedTransport:1});assert.match(stderr,/R16_NATIVE_LOCAL_STOP/);assert.match(stderr,/"firstStopProof":"NOT_PROVEN"/);
});

test('startup-validated descriptor or root config drifting before close is refused',async t=>{
 for(const mutate of [f=>fs.appendFileSync(f.file,' '),f=>fs.writeFileSync(f.configFile,canonical({...f.config,workspaceAlias:'changed'})),f=>fs.appendFileSync(f.registryFile,' ')]){
  const f=await fixture(t),token=f.load(),d=f.dispatcher(token);mutate(f);await assert.rejects(d.shutdownLocalResources(),/HISTORY_ROOT_BINDING_DRIFT|HISTORY_REGISTRATION_DRIFT/);
 }
});

test('descriptor construction requires current plan and fresh stopped proof; never extends old windows',async t=>{
 for(const change of [i=>i.now=i.plan.expiresAt,i=>i.now=i.stoppedProof.expiresAt,i=>i.stoppedProof.issuedAt=i.now+1,i=>i.plan.recoveryDeadline=i.plan.approvedAt+1800001]){
  const f=await fixture(t),input=structuredClone(f.input);input.ledgerRegistryRaw=f.registryRaw;change(input);assert.throws(()=>f.helper.buildNativeHistoryDescriptor(input),/HISTORY_CURRENT_PLAN_WINDOW_REQUIRED|HISTORY_FRESH_STOP_PROOF_REQUIRED|HISTORY_STOP_PROOF_REQUIRED/);
 }
});
test('descriptor construction recomputes exact control rows and original unknown identities',async t=>{
 for(const change of [i=>i.checkpoint.controlUnknownRows[0].hash='f'.repeat(64),i=>i.checkpoint.controlUnknownRows[0].status='INFLIGHT',i=>i.checkpoint.controlUnknownRows.push(i.checkpoint.controlUnknownRows[0]),i=>i.checkpoint.originalUnknown.p2vox.generation++,i=>delete i.checkpoint.controlUnknownRows]){
  const f=await fixture(t),input=structuredClone(f.input);input.ledgerRegistryRaw=f.registryRaw;change(input);assert.throws(()=>f.helper.buildNativeHistoryDescriptor(input),/HISTORY_CONTROL_ROWS_|HISTORY_ORIGINAL_UNKNOWN_DRIFT/);
 }
});

test('existing exact signed operations are mandatory at construction and private runtime consumption',async t=>{
 for(const change of [i=>delete i.historicalOperations,i=>i.historicalOperations.pop(),i=>i.historicalOperations[0].signature='invalid',i=>i.historicalOperations[0].body.leaseHash='f'.repeat(64)]){
  const f=await fixture(t),input=structuredClone(f.input);input.ledgerRegistryRaw=f.registryRaw;change(input);assert.throws(()=>f.helper.buildNativeHistoryDescriptor(input),/HISTORY_SIGNED_OPERATIONS_REQUIRED|AUTHORITY_REJECTED/);
 }
 for(const change of [d=>delete d.historicalOperations,d=>d.historicalOperations[0].signature='invalid',d=>d.historicalOperations.reverse().pop()]){
  const f=await fixture(t);f.mutate(change);assert.throws(f.load,/INVALID_REQUEST|HISTORY_SIGNED_OPERATIONS_REQUIRED|AUTHORITY_REJECTED/);
 }
 const f=await fixture(t),baseline=f.load();assert.equal(Object.hasOwn(baseline,'historicalOperations'),false);const d=f.dispatcher(baseline);await d.shutdownLocalResources();d.releaseStores();
});

test('transported App operation never substitutes the actual old Issuer lease or its original version',async t=>{
 for(const mutate of [s=>s.active.lease.signature='invalid',s=>s.active.lease.body.versions.native='f'.repeat(64),s=>s.operations[0].hash='e'.repeat(64)]){
  const f=await fixture(t),baseline=f.load(),pdir=path.join(f.dir,'dispatcher/project-p2vox');
  const ps=new ProtectedStore({directory:pdir,create:false,now:()=>f.input.now});ps.transact(mutate);ps.close();
  const before=fs.readFileSync(path.join(pdir,'state.json')),d=f.dispatcher(baseline);
  await assert.rejects(d.shutdownLocalResources(),/HISTORICAL_LEASE_BINDING|AUTHORITY_REJECTED|UNPROVEN_EXECUTION_RISK/);
  assert.deepEqual(fs.readFileSync(path.join(pdir,'state.json')),before);
 }
});

test('branded inherited history requires both original UNKNOWN rows exactly once, never deleted or settled',async t=>{
 for(const mutate of [s=>s.operations=[],s=>s.operations[0].status='KNOWN',s=>s.operations.push(structuredClone(s.operations[0])),s=>s.operations[0].hash='e'.repeat(64)]){
  const f=await fixture(t),baseline=f.load(),pdir=path.join(f.dir,'dispatcher/project-p2vox'),ps=new ProtectedStore({directory:pdir,create:false,now:()=>f.input.now});ps.transact(mutate);ps.close();const before=fs.readFileSync(path.join(pdir,'state.json'));
  await assert.rejects(f.dispatcher(baseline).shutdownLocalResources(),/HISTORY_ORIGINAL_OPERATIONS_DRIFT|UNPROVEN_EXECUTION_RISK/);assert.deepEqual(fs.readFileSync(path.join(pdir,'state.json')),before);
 }
 const f=await fixture(t),baseline=f.load();f.rawStore.transact(s=>s.projects=s.projects.filter(p=>p!=='p2vox'));await assert.rejects(f.dispatcher(baseline).shutdownLocalResources(),{code:'HISTORY_ORIGINAL_OPERATIONS_DRIFT'});
});
