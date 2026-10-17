import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {ProtectedStore} from '../../src/lease-core.mjs';
import {fixture,clone} from './test_publication.mjs';
import {pathToFileURL} from 'node:url';
import {TARGET_DIRECTORY,digest,canonical} from './publication.mjs';

async function prepared(t){
 const f=fixture(t),a=f.a;let clock=f.now;
 // Explicit synthetic immutable-pin namespace, identical implementation bytes.
 // No runtime API accepts these substitutions or caller constructors.
 const data=s=>'data:text/javascript;base64,'+Buffer.from(s).toString('base64');
 let helper=fs.readFileSync(new URL('./history-baseline.mjs',import.meta.url),'utf8');
 for(const [pin,replacement]of Object.entries({'56e1df18a54950ea346a51654e61df60afe33cb9928ae77293b2cf336fd8a5ec':a.plan.sourcePublicConfigHash,'b8645f6fe206e84dd07c2c6c166bfe4016d1deefca28bf9545dcfa1560f013e9':a.plan.sourceDeliveryHash,'2516e881b0622b3ac2d53c454e6ccf9950441c5cb3c26a53500b45d3b1dbe7b4':a.plan.sourceNativeVersion,'00ac437d66143e627132975555d06396d69ff69616f630d19e3622627e15c5e6':a.plan.grantHash,'fd13e74ce69cb8ec30817ca0a48631cf3a6b6b2b08a410cc1b442df41992cc1f':digest(f.history.historicalOperations[0]),'38f6af1386e78e5d7ccd0710077d6a3a5e753e81722dd10f11a3a2ff9bd85da1':digest(f.history.historicalOperations[1])}))helper=helper.replaceAll(pin,replacement);
 helper=helper.replace("proof.environment==='PRODUCTION'","proof.environment==='ISOLATED_TEST'");
 helper=helper.replace("'../../src/lease-core.mjs'",JSON.stringify(new URL('../../src/lease-core.mjs',import.meta.url).href));
 let source=fs.readFileSync(new URL('./transaction.mjs',import.meta.url),'utf8').replace("'./history-baseline.mjs'",JSON.stringify(data(helper)));
 source=source.replace(/from '([^']+)'/g,(match,rel)=>'from '+JSON.stringify(new URL(rel,import.meta.url).href));
 const {FixedReceivers,runTransition}=await import(data(source));
 const roots={local:f.root+'/local',cloud:f.root+'/cloud'};for(const r of Object.values(roots))fs.mkdirSync(r,{mode:0o700});
 const emit=(root,p,v,mode=0o600)=>{const file=root+p;fs.mkdirSync(file.slice(0,file.lastIndexOf('/')),{recursive:true,mode:0o700});fs.writeFileSync(file,typeof v==='string'||Buffer.isBuffer(v)?v:canonical(v),{mode});return file;};
 const baseDir='/opt/r16/releases/'+a.sourcePublicConfig.release.body.id;
 const localFiles=Object.entries(a.sourceManifests).flatMap(([role,m])=>Object.entries(m.files).map(([artifactPath,sha256])=>({role,artifactPath,sha256,path:(role==='bridge'?'/opt/r16/releases/r16-daily-20261012-r15':baseDir)+'/'+artifactPath})));
 const baseline={history:f.history,proposal:{schema:'r16.owner-installation.v1',grantId:'r16-projects-daily',release:a.sourcePublicConfig.release,versions:a.sourcePublicConfig.versions,peers:a.sourcePublicConfig.peers,artifacts:a.sourceManifests,localFiles},
 reviewed:{schema:'r16.reviewed-installation.v1',releaseId:a.sourcePublicConfig.release.body.id,artifacts:a.sourceManifests,localFiles},
 native:{schema:'r16.native-host.v1',codeManifest:baseDir+'/native-manifest.json'},app:{schema:'r16.app-host.v1',codeManifest:baseDir+'/app-manifest.json'},
 ownerConfiguration:{kind:'r16.owner.configuration.v1',activeGrantId:'r16-projects-daily',connected:true,connectionNonce:0,trust:{scope:'fixture-only'},delivery:{revision:19,envelope:a.sourceDelivery,hash:digest({publicConfig:a.sourcePublicConfig,control:a.sourceDelivery.body.control,connectionNonce:0})}}};
 for(const [k,p]of Object.entries({proposal:'/etc/r16-owner/release-proposal.json',reviewed:'/etc/r16-owner/reviewed-installation.json',native:'/etc/r16/native-host.json'}))emit(roots.local,p,baseline[k],k==='native'?0o644:0o600);
 for(const [p,v]of Object.entries({'/etc/r16-cloud/app-host.json':baseline.app,'/etc/r16-cloud/public-config.json':a.sourcePublicConfig,'/etc/r16-cloud/authority-control.json':a.sourceDelivery.body.control,
 '/etc/r16-cloud/cutover.json':{schema:'r16.cloud-cutover.v1',phase:'ACTIVE',grantId:'r16-projects-daily',releaseId:a.sourcePublicConfig.release.body.id},'/var/lib/r16-cloud/start-attempt.json':{schema:'r16.cloud-start-attempt.v1',grantId:'r16-projects-daily',revision:19}}))emit(roots.cloud,p,v,0o644);
 const createStore=(root,p,initial)=>{fs.mkdirSync((root+p).slice(0,(root+p).lastIndexOf('/')),{recursive:true,mode:0o700});const s=new ProtectedStore({directory:root+p,create:true,initial,now:()=>clock});s.close();};
 createStore(roots.local,'/var/lib/r16-owner/configuration',baseline.ownerConfiguration);
 createStore(roots.cloud,'/var/lib/r16-cloud/authority',{kind:'r16.cloud-publication.v1',accepted:a.sourceDelivery});
 const original={kind:'r16.participant.v1',operations:[{id:'c434da49-055a-43dc-a3e3-695cce137909',hash:'fd13e74ce69cb8ec30817ca0a48631cf3a6b6b2b08a410cc1b442df41992cc1f',generation:30,status:'UNKNOWN'},{id:'d0364f8b-3a68-4ca2-a396-7953b29cee4c',hash:'38f6af1386e78e5d7ccd0710077d6a3a5e753e81722dd10f11a3a2ff9bd85da1',generation:38,status:'UNKNOWN'}],closing:{opaqueHistoricalSignedLease:'fixture-only-preserved'}};
 createStore(roots.local,'/var/lib/r16-native/grants/r16-projects-daily/dispatcher',original);
 const ledger=roots.local+'/var/lib/r16-native/grants/r16-projects-daily/dispatcher/state.json',ledgerBefore=fs.readFileSync(ledger);
 const packageRoot={local:roots.local+'/package',cloud:roots.cloud+'/package'};
 for(const root of Object.values(roots)){emit(root,'/package/metadata/PAYLOAD_INVENTORY.json',{files:a.inventory},0o644);for(const [n,b]of Object.entries(f.targetBytes))emit(root,'/package/payload/'+n,b,0o644);}
 const options={baseline,proof:()=>f.proof,clock:()=>clock};
 const local=new FixedReceivers(a,{...options,fixtureRoot:roots.local,host:'jenn-System-Product-Name'}),cloud=new FixedReceivers(a,{...options,fixtureRoot:roots.cloud,host:'VM-0-12-ubuntu'});
 const calls=[];const osAdapter={originalBaselineHash:()=>a.plan.originalBaselineHash,observe:()=>f.proof,activate:scope=>{calls.push(['activate',scope]);return {status:'OS_ACTIVE'};},resume:scope=>{calls.push(['resume',scope]);return {status:'OS_ACTIVE',nativeStopped:true};},requiesce:()=>{calls.push(['requiesce']);return {status:'STOPPED_FENCED_NOT_DRAINED'};},expectedState:d=>({verified:true,planHash:a.planHash,nativeStopped:d.body.revision!==a.revisionPlan.forward,nativeSelectorHash:digest(d.body.revision===a.revisionPlan.forward?local.read('/etc/r16/native-host.json'):baseline.native)})};
 return {...f,roots,packageRoot,baseline,local,cloud,osAdapter,calls,ledger,ledgerBefore,emit,setClock:v=>clock=v,run:extra=>runTransition({artifacts:a,local,cloud,osAdapter,packageRoot,signer:f.sign,now:()=>clock,...extra})};
}
test('real temp ProtectedStores, full staging, Ed25519 receiver/CAS, Native selector and source App unchanged',async t=>{
 const f=await prepared(t),result=await f.run();assert.equal(result.status,'MAINTENANCE_COMMITTED',JSON.stringify(result));assert.equal(result.configurationRevision,21);
 assert.equal(f.local.read('/etc/r16/native-host.json').codeManifest,TARGET_DIRECTORY+'/native-manifest.json');assert.deepEqual(f.cloud.read('/etc/r16-cloud/app-host.json'),f.baseline.app);
 assert.deepEqual(fs.readFileSync(f.ledger),f.ledgerBefore);assert.equal(f.cloud.accepted().body.revision,21);assert.equal(f.local.read('/var/lib/r16-owner/configuration/state.json').data.delivery.revision,21);
 assert.equal(result.businessAcceptance,false);assert.equal(result.readback.drainStatus,'UNPROVEN');const again=await f.run();assert.equal(again.historicalReadOnly,true);assert.equal(f.calls.filter(x=>x[0]==='activate').length,1);
});
test('foreign cloud selector blocks before acceptance; source original ledger stays unchanged',async t=>{
 const f=await prepared(t),p=f.sign(f.a);f.cloud.baseline.forwardPublication=p;f.emit(f.roots.cloud,'/etc/r16-cloud/app-host.json',{...f.baseline.app,foreign:true});
 assert.throws(()=>f.cloud.commitCloud(p),/UNCHANGED_APP_SELECTOR_DRIFT/);assert.equal(f.cloud.accepted().body.revision,19);assert.deepEqual(fs.readFileSync(f.ledger),f.ledgerBefore);
});
test('package corruption or extra payload cannot select/sign, ABORT keeps Native stopped',async t=>{
 const f=await prepared(t);f.emit(f.roots.local,'/package/payload/'+Object.keys(f.a.inventory)[0],'corrupt',0o644);const r=await f.run();
 assert.equal(r.status,'ABORTED_BEFORE_CONFIGURATION_CHANGE');assert.equal(f.local.journal().read('signing-forward-intent'),null);assert.equal(f.cloud.accepted().body.revision,19);assert.equal(f.calls[0][0],'resume');assert.equal(f.calls[0][1].nativeMustRemainStopped,true);
});
test('partial local selector write triggers monotonic recovery22, never reenters FORWARD',async t=>{
 const f=await prepared(t);let fired=false;f.local.fault=point=>{if(!fired&&point==='write:/etc/r16/native-host.json'){fired=true;throw Object.assign(Error('injected'),{code:'LOCAL_WRITE_INTERRUPTED'});}};
 const r=await f.run();assert.equal(r.status,'ROLLED_BACK_TO_R15_WITH_NEWER_REVISION');assert.equal(r.configurationRevision,22);assert.deepEqual(f.local.read('/etc/r16/native-host.json'),f.baseline.native);assert.equal(f.cloud.accepted().body.revision,22);assert.deepEqual(fs.readFileSync(f.ledger),f.ledgerBefore);assert.equal(f.local.journal().read('transaction').mode,'ROLLBACK');
});
test('unknown signing intent cannot be replayed after process interruption',async t=>{
 const f=await prepared(t);let count=0;const signer=(...args)=>{count++;return f.sign(...args);};
 await assert.rejects(f.run({signer,fault:p=>{if(p==='signing-intent:forward')throw Object.assign(Error('crash'),{simulatedCrash:true});}}));
 assert.equal(count,0);const r=await f.run({signer});assert.equal(count,0);assert.equal(r.status,'ABORTED_BEFORE_CONFIGURATION_CHANGE');assert.equal(f.local.journal().read('transaction').mode,'ABORT');
});
test('lost remote commit reply cannot use momentary source observation to ABORT',async t=>{
 const f=await prepared(t);const commit=f.cloud.commitCloud.bind(f.cloud);f.cloud.commitCloud=(...args)=>{const r=commit(...args);if(r.revision===21)throw Object.assign(Error('lostreply'),{code:'FIXED_COMMAND_TIMEOUT'});return r;};
 const r=await f.run();assert.equal(r.status,'ROLLED_BACK_TO_R15_WITH_NEWER_REVISION');assert.equal(r.configurationRevision,22);assert.equal(f.local.journal().read('transaction').mode,'ROLLBACK');
});
test('expired proof or replaced epoch refuses selector/config effects',async t=>{
 const f=await prepared(t),p=f.sign(f.a);f.proof.stopEpoch='wrong-epoch';assert.throws(()=>f.cloud.commitCloud(p));assert.equal(f.cloud.accepted().body.revision,19);f.proof.stopEpoch=f.a.plan.stopEpoch;f.setClock(f.a.plan.expiresAt);assert.throws(()=>f.local.commitLocal(p),/RECEIVER_WINDOW_EXPIRED/);assert.deepEqual(f.local.read('/etc/r16/native-host.json'),f.baseline.native);
});
test('owner fields outside delivery and foreign Native selector cannot be overwritten',async t=>{
 const f=await prepared(t),p=f.sign(f.a);f.local.baseline.forwardPublication=p;f.emit(f.roots.local,'/etc/r16/native-host.json',{...f.baseline.native,foreign:true},0o644);assert.throws(()=>f.local.commitLocal(p),/FIXED_SELECTOR_CAS_CONFLICT/);assert.equal(f.local.read('/var/lib/r16-owner/configuration/state.json').data.delivery.revision,19);
});
test('unknown or partial OS restoration cannot mint terminal success',async t=>{
 const f=await prepared(t);f.osAdapter.activate=()=>({status:'RESTORE_PARTIAL'});f.osAdapter.expectedState=()=>({verified:false});const r=await f.run();assert.equal(r.status,'RECOVERY_REQUIRED_SERVICES_MAY_REMAIN_FENCED');assert.equal(f.local.journal().read('receipt'),null);assert.equal(f.local.journal().read('transaction').mode,'ROLLBACK');
});
test('fresh stopped proof within recovery permits real rollback receivers after forward expiry, never new forward',async t=>{
 const f=await prepared(t),forward=f.sign(f.a);f.local.baseline.forwardPublication=forward;f.cloud.baseline.forwardPublication=forward;
 f.cloud.commitCloud(forward);f.local.commitLocal(forward);const now=f.a.plan.expiresAt+100;f.setClock(now);f.proof.issuedAt=now;f.proof.expiresAt=now+30000;
 assert.throws(()=>f.cloud.commitCloud(forward),/RECEIVER_WINDOW_EXPIRED/);
 const recovery=f.sign(f.a,true);f.cloud.commitCloud(recovery,true);f.local.commitLocal(recovery,true);
 assert.equal(f.cloud.accepted().body.revision,22);assert.equal(f.local.read('/var/lib/r16-owner/configuration/state.json').data.delivery.revision,22);assert.deepEqual(f.local.read('/etc/r16/native-host.json'),f.baseline.native);assert.deepEqual(fs.readFileSync(f.ledger),f.ledgerBefore);
});

const filesBelow=root=>{const out={};const walk=(p,prefix='')=>{for(const e of fs.readdirSync(p,{withFileTypes:true})){if(e.isDirectory())walk(p+'/'+e.name,prefix+e.name+'/');else out[prefix+e.name]={raw:fs.readFileSync(p+'/'+e.name).toString('base64'),mode:fs.statSync(p+'/'+e.name).mode&0o7777};}};walk(root);return out;};
test('completed recovery22 makes late21 refuse before any local selector or cloud projection changes',async t=>{
 const f=await prepared(t),forward=f.sign(f.a),recovery=f.sign(f.a,true);for(const r of [f.local,f.cloud])r.baseline.forwardPublication=forward;
 f.cloud.commitCloud(forward);f.local.commitLocal(forward);f.cloud.commitCloud(recovery,true);f.local.commitLocal(recovery,true);
 const before=Object.fromEntries(Object.entries(f.roots).map(([k,r])=>[k,filesBelow(r)]));
 assert.throws(()=>f.local.commitLocal(forward),/OWNER_REVISION_ROLLBACK|OWNER_PREVIOUS_ACCEPTED_DRIFT/);
 assert.throws(()=>f.cloud.commitCloud(forward),/PREVIOUS_ACCEPTED_DRIFT/);
 for(const [k,r]of Object.entries(f.roots))assert.deepEqual(filesBelow(r),before[k]);
});
test('single existing Store lifetime lock excludes a second receiver during every physical projection',async t=>{
 const f=await prepared(t),forward=f.sign(f.a),recovery=f.sign(f.a,true);for(const r of [f.local,f.cloud])r.baseline.forwardPublication=forward;
 let localBusy=0,cloudBusy=0;
 f.local.fault=p=>{if(p==='write:/etc/r16/native-host.json'){assert.throws(()=>f.local.commitLocal(recovery,true),/STATE_BUSY/);localBusy++;}};
 f.cloud.fault=p=>{if(p==='write:cloud-accepted'||p==='write:/etc/r16-cloud/public-config.json'){assert.throws(()=>f.cloud.commitCloud(recovery,true),/STATE_BUSY/);cloudBusy++;}};
 f.cloud.commitCloud(forward);f.local.commitLocal(forward);assert.equal(localBusy,1);assert.equal(cloudBusy,2);
 f.local.fault=()=>{};f.cloud.fault=()=>{};f.cloud.commitCloud(recovery,true);f.local.commitLocal(recovery,true);
 assert.equal(f.cloud.read('/etc/r16-cloud/public-config.json').release.body.id,f.a.sourcePublicConfig.release.body.id);
 assert.equal(f.local.read('/etc/r16/native-host.json').codeManifest,f.baseline.native.codeManifest);
});
test('lost reply after accepted21 cannot leave a late projection following complete recovery22',async t=>{
 const f=await prepared(t),forward=f.sign(f.a),recovery=f.sign(f.a,true);for(const r of [f.local,f.cloud])r.baseline.forwardPublication=forward;
 let attempts=0;f.cloud.fault=p=>{if(p==='write:cloud-accepted'){attempts++;assert.throws(()=>f.cloud.commitCloud(recovery,true),/STATE_BUSY/);throw Error('lost reply');}};
 assert.throws(()=>f.cloud.commitCloud(forward),/lost reply/);assert.equal(attempts,1);f.cloud.fault=()=>{};
 f.cloud.commitCloud(recovery,true);const before=filesBelow(f.roots.cloud);assert.throws(()=>f.cloud.commitCloud(forward),/PREVIOUS_ACCEPTED_DRIFT/);assert.deepEqual(filesBelow(f.roots.cloud),before);
});
test('rollback cannot activate old crashed Native or mint a terminal receipt from verified boolean',async t=>{
 const f=await prepared(t);let once=false;f.local.fault=p=>{if(!once&&p==='write:/etc/r16/native-host.json'){once=true;throw Error('interrupt forward');}};
 f.osAdapter.expectedState=()=>({verified:true,planHash:f.a.planHash,nativeStopped:false,nativeSelectorHash:digest(f.baseline.native)});
 const r=await f.run();assert.equal(r.status,'RECOVERY_REQUIRED_SERVICES_MAY_REMAIN_FENCED');assert.equal(f.local.journal().read('receipt'),null);
 const recoveryCall=f.calls.find(([name,scope])=>name==='resume'&&scope.phase==='ROLLBACK');assert.ok(recoveryCall);assert.equal(recoveryCall[1].nativeMustRemainStopped,true);
});
test('ABORT OS_ACTIVE with active Native or wrong SOURCE selector cannot mint receipt',async t=>{
 for(const change of [state=>state.nativeStopped=false,state=>state.nativeSelectorHash='f'.repeat(64)]){
  const f=await prepared(t);f.emit(f.roots.local,'/package/payload/'+Object.keys(f.a.inventory)[0],'bad',0o644);
  f.osAdapter.expectedState=()=>{const x={verified:true,planHash:f.a.planHash,nativeStopped:true,nativeSelectorHash:digest(f.baseline.native)};change(x);return x;};
  const r=await f.run();assert.equal(r.status,'RECOVERY_REQUIRED_SERVICES_MAY_REMAIN_FENCED');assert.equal(f.local.journal().read('receipt'),null);
 }
});
test('actual canonical descriptor file precedes Native selector, retains exact signed operations on rollback',async t=>{
 const f=await prepared(t),forward=f.sign(f.a);f.local.baseline.forwardPublication=forward;
 const p='/etc/r16-maintenance/source19-native-transition-r1-native-history.json';let observed=false;
 f.local.fault=point=>{if(point==='write:/etc/r16/native-host.json'){const raw=fs.readFileSync(f.roots.local+p),d=JSON.parse(raw);assert.equal(raw.toString(),canonical(d));assert.deepEqual(d.historicalOperations,f.history.historicalOperations);assert.equal(d.checkpointHash,f.a.checkpointHash);assert.equal(fs.statSync(f.roots.local+p).mode&0o7777,0o644);assert.equal(f.local.read('/etc/r16/native-host.json').nativeHistory.descriptorSha256,digest(d));observed=true;}};
 f.local.commitLocal(forward);assert.equal(observed,true);const bytes=fs.readFileSync(f.roots.local+p);f.local.fault=()=>{};f.local.commitLocal(f.sign(f.a,true),true);assert.deepEqual(fs.readFileSync(f.roots.local+p),bytes);assert.deepEqual(f.local.read('/etc/r16/native-host.json'),f.baseline.native);
});
test('missing signed history or control/checkpoint drift refuses before any selector/cache write',async t=>{
 for(const change of [h=>delete h.historicalOperations,h=>h.historicalOperations[0].signature='invalid',h=>h.checkpoint.controlUnknownRows.push({id:'new',hash:'f'.repeat(64),status:'UNKNOWN'})]){
  const f=await prepared(t),forward=f.sign(f.a);f.local.baseline.forwardPublication=forward;change(f.local.baseline.history);const before=filesBelow(f.roots.local);
  assert.throws(()=>f.local.commitLocal(forward));assert.deepEqual(filesBelow(f.roots.local),before);
 }
});
