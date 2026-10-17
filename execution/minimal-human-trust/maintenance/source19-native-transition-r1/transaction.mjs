// Fixed file receivers + existing monotonic r6 driver. No installed native CLI.
import fs from 'node:fs';
import path from 'node:path';
import os from 'node:os';
import {createHash} from 'node:crypto';
import {drive} from '../release-r6/transaction-driver.mjs';
import {buildNativeHistoryDescriptor,nativeHistoryConfigBinding,HISTORY_PATH} from './history-baseline.mjs';
import {ProtectedStore} from '../../src/lease-core.mjs';
import {locked} from '../release-r6/io.mjs';
import {STATE,TARGET_DIRECTORY,TARGET_RELEASE,canonical,digest,need,assertArtifacts,assertStoppedProof,acceptSignedPublication,verifyPublicationBodies,signFixedPublication} from './publication.mjs';
const same=(a,b)=>canonical(a)===canonical(b),clone=x=>JSON.parse(canonical(x));
const PATHS=Object.freeze({proposal:'/etc/r16-owner/release-proposal.json',reviewed:'/etc/r16-owner/reviewed-installation.json',native:'/etc/r16/native-host.json',
 configuration:'/var/lib/r16-owner/configuration',app:'/etc/r16-cloud/app-host.json',public:'/etc/r16-cloud/public-config.json',control:'/etc/r16-cloud/authority-control.json',
 cloudCutover:'/etc/r16-cloud/cutover.json',startAttempt:'/var/lib/r16-cloud/start-attempt.json',accepted:'/var/lib/r16-cloud/authority'});
const sha=b=>createHash('sha256').update(b).digest('hex');

export class FixedReceivers{
 constructor(a,{fixtureRoot=null,host,baseline,proof,clock=Date.now,fault=()=>{}}){
  assertArtifacts(a);this.a=a;this.clock=clock;this.proof=proof;this.fault=fault;this.baseline=clone(baseline);this.fixtureRoot=fixtureRoot;this.host=host;
  need(['jenn-System-Product-Name','VM-0-12-ubuntu'].includes(host),'FIXED_HOST_REQUIRED');
  if(fixtureRoot!==null){const s=fs.lstatSync(fixtureRoot);need(a.environment==='ISOLATED_TEST'&&process.geteuid()!==0&&fixtureRoot.startsWith('/tmp/')&&s.isDirectory()&&!s.isSymbolicLink()&&s.uid===process.geteuid()&&(s.mode&0o7777)===0o700,'FIXTURE_ROOT_REQUIRED');}
  else need(a.environment==='PROTECTED_SOURCE'&&process.getuid()===0&&process.geteuid()===0&&os.hostname()===host,'ROOT_RECEIVER_REQUIRED');
  const b=this.baseline,p=a.sourcePublicConfig,dir='/opt/r16/releases/'+p.release.body.id;
  need(same(b.proposal.release,p.release)&&same(b.proposal.versions,p.versions)&&same(b.proposal.artifacts,a.sourceManifests)&&
   b.reviewed.releaseId===p.release.body.id&&same(b.reviewed.artifacts,a.sourceManifests)&&
   b.native.schema==='r16.native-host.v1'&&b.native.codeManifest===dir+'/native-manifest.json'&&
   b.app.schema==='r16.app-host.v1'&&b.app.codeManifest===dir+'/app-manifest.json'&&
   b.ownerConfiguration.kind==='r16.owner.configuration.v1'&&b.ownerConfiguration.connected===true&&b.ownerConfiguration.activeGrantId==='r16-projects-daily'&&same(b.ownerConfiguration.delivery?.envelope,a.sourceDelivery), 'SOURCE_SELECTOR_BASELINE_DRIFT');
  const bindings=Object.entries(a.sourceManifests).flatMap(([role,m])=>Object.entries(m.files).map(([artifactPath,sha256])=>({role,artifactPath,sha256,path:(role==='bridge'?'/opt/r16/releases/r16-daily-20261012-r15':dir)+'/'+artifactPath}))).sort((x,y)=>canonical(x).localeCompare(canonical(y)));
  need(same([...b.proposal.localFiles].sort((x,y)=>canonical(x).localeCompare(canonical(y))),bindings)&&same(b.reviewed.localFiles,b.proposal.localFiles),'SOURCE_LOCAL_FILE_BASELINE_DRIFT');
 }
 file(p){need(Object.values(PATHS).some(n=>p===n||p===n+'/state.json')||p.startsWith(STATE+'/')||p===HISTORY_PATH||p===TARGET_DIRECTORY||p.startsWith(TARGET_DIRECTORY+'/'),'FIXED_RECEIVER_PATH');return this.fixtureRoot?this.fixtureRoot+p:p;}
 bytes(file){
  const root=this.fixtureRoot||'/';need(file.startsWith(root+'/')||root==='/', 'RECEIVER_PATH_OUTSIDE_ROOT');
  let cursor=root;for(const bit of path.relative(root,file).split(path.sep)){cursor=path.join(cursor,bit);const s=fs.lstatSync(cursor);need(!s.isSymbolicLink()&&s.uid===process.geteuid()&&!(s.mode&0o022),'RECEIVER_PATH_UNSAFE');}
  const fd=fs.openSync(file,fs.constants.O_RDONLY|fs.constants.O_NOFOLLOW);try{const s=fs.fstatSync(fd);need(s.isFile()&&s.nlink===1&&s.size<=128*1024*1024,'RECEIVER_FILE_REFUSED');const b=fs.readFileSync(fd),z=fs.fstatSync(fd),named=fs.lstatSync(file);const stamp=x=>[x.dev,x.ino,x.mode,x.uid,x.gid,x.nlink,x.size,String(x.mtimeMs),String(x.ctimeMs)];need(b.length===s.size&&same(stamp(s),stamp(z))&&same(stamp(s),stamp(named)),'RECEIVER_FILE_CHANGED');return b;}finally{fs.closeSync(fd);}
 }
 directory(dir,beforeEffect=()=>{},mode=0o700){if(!fs.existsSync(dir)){this.directory(path.dirname(dir),beforeEffect,mode);beforeEffect();fs.mkdirSync(dir,{mode});}if(dir===this.fixtureRoot||dir==='/')return;const s=fs.lstatSync(dir);need(s.isDirectory()&&!s.isSymbolicLink()&&s.uid===process.geteuid()&&!(s.mode&0o022),'RECEIVER_DIRECTORY_REFUSED');const target=this.fixtureRoot?this.fixtureRoot+TARGET_DIRECTORY:TARGET_DIRECTORY;if(dir===target||dir.startsWith(target+'/'))need((s.mode&0o7777)===0o755,'TARGET_DIRECTORY_MODE_REFUSED');}
 rawWrite(file,raw,mode=0o600,beforeEffect=()=>{}){
  this.directory(path.dirname(file),beforeEffect);const pending=file+'.next-'+sha(raw);let fd;
  try{beforeEffect();fd=fs.openSync(pending,fs.constants.O_WRONLY|fs.constants.O_CREAT|fs.constants.O_EXCL|fs.constants.O_NOFOLLOW,mode);beforeEffect();fs.writeFileSync(fd,raw);fs.fchmodSync(fd,mode);fs.fsyncSync(fd);}catch(e){if(e.code!=='EEXIST')throw e;const b=this.bytes(pending);need(b.length<=raw.length&&b.equals(raw.subarray(0,b.length)),'PENDING_BYTES_CONFLICT');beforeEffect();fd=fs.openSync(pending,fs.constants.O_WRONLY|fs.constants.O_NOFOLLOW);let offset=b.length;while(offset<raw.length){beforeEffect();offset+=fs.writeSync(fd,raw,offset,raw.length-offset,offset);}fs.fchmodSync(fd,mode);fs.fsyncSync(fd);}finally{if(fd!==undefined)fs.closeSync(fd);}
  beforeEffect();fs.renameSync(pending,file);const d=fs.openSync(path.dirname(file),fs.constants.O_RDONLY|fs.constants.O_DIRECTORY);try{fs.fsyncSync(d);}finally{fs.closeSync(d);}
 }
 read(p){return JSON.parse(this.bytes(this.file(p)));}
 gate(rollback=false){
  const now=this.clock();need(now<(rollback?this.a.plan.recoveryDeadline:this.a.plan.expiresAt),'RECEIVER_WINDOW_EXPIRED');
  const proof=this.fixtureRoot?this.proof():this.read(STATE+'/stop-proof.json');assertStoppedProof(proof,this.a,now);
  if(!this.fixtureRoot)need(same(this.read(STATE+'/plan.json'),this.a.plan),'PROTECTED_RECEIVER_PLAN_DRIFT');
  return proof;
 }
 write(p,value,rollback=false,mode=0o600){this.gate(rollback);const f=this.file(p);this.rawWrite(f,Buffer.from(canonical(value)),mode,()=>this.gate(rollback));this.fault('write:'+p);}
 cas(p,source,forward,next,rollback=false,mode=0o600){const actual=this.read(p);need(same(actual,source)||same(actual,forward)||same(actual,next),'FIXED_SELECTOR_CAS_CONFLICT');if(!same(actual,next))this.write(p,next,rollback,mode);}
 journal(){return {read:name=>{need(/^[a-z0-9-]+$/.test(name),'JOURNAL_NAME_REFUSED');try{return this.read(STATE+'/journal/'+name+'.json');}catch(e){if(e.code==='ENOENT')return null;throw e;}},write:(name,value)=>{need(/^[a-z0-9-]+$/.test(name),'JOURNAL_NAME_REFUSED');const f=this.file(STATE+'/journal/'+name+'.json');this.directory(path.dirname(f));this.rawWrite(f,Buffer.from(canonical(value)));}};}
 stage(packageRoot){
  this.gate();need(packageRoot===(this.fixtureRoot?this.fixtureRoot+'/package':STATE+'/package'),'FIXED_PACKAGE_REQUIRED');
  const expected=this.a.inventory,inventory=JSON.parse(this.bytes(packageRoot+'/metadata/PAYLOAD_INVENTORY.json')).files;
  need(same(inventory,expected),'PACKAGE_INVENTORY_CHANGED');
  const walk=(dir,prefix='')=>fs.readdirSync(dir,{withFileTypes:true}).flatMap(e=>{const p=path.join(dir,e.name);need(!fs.lstatSync(p).isSymbolicLink(),'PAYLOAD_LINK_REFUSED');return e.isDirectory()?walk(p,prefix+e.name+'/'):[prefix+e.name];});
  need(same(walk(packageRoot+'/payload').sort(),Object.keys(expected).sort()),'PACKAGE_EXACT_SET_REQUIRED');
  // Validate the entire input before creating any target file.
  const bytes={};for(const [n,row]of Object.entries(expected)){const f=packageRoot+'/payload/'+n,b=this.bytes(f);need(sha(b)===row.sha256&&b.length===row.bytes&&(fs.lstatSync(f).mode&0o7777)===row.mode,'PACKAGE_BYTES_OR_MODE');bytes[n]=b;}
  for(const [n,b]of Object.entries(bytes)){this.gate();const dst=this.file(TARGET_DIRECTORY+'/'+n);this.directory(path.dirname(dst),()=>this.gate(),0o755);try{need(this.bytes(dst).equals(b)&&(fs.lstatSync(dst).mode&0o7777)===expected[n].mode,'STAGED_FILE_CONFLICT');}catch(e){if(e.code!=='ENOENT')throw e;this.gate();this.rawWrite(dst,b,expected[n].mode,()=>this.gate());}}
  for(const role of ['app','bridge','native']){this.gate();const f=this.file(TARGET_DIRECTORY+'/'+role+'-manifest.json');try{need(same(JSON.parse(this.bytes(f)),this.a.targetManifests[role]),'STAGED_MANIFEST_CONFLICT');}catch(e){if(e.code!=='ENOENT')throw e;this.gate();this.rawWrite(f,Buffer.from(canonical(this.a.targetManifests[role])),0o644,()=>this.gate());}}
  need(same(walk(this.file(TARGET_DIRECTORY)).sort(),[...Object.keys(expected),'app-manifest.json','bridge-manifest.json','native-manifest.json'].sort()),'TARGET_EXACT_SET_REQUIRED');
  return {status:'NATIVE_MAINTENANCE_STAGED_NOT_SELECTED',inventoryHash:this.a.inventoryHash,nativeVersion:this.a.targetVersions.native};
 }
 desired(publication,rollback=false,historical=false){
  if(historical)verifyPublicationBodies(this.a,publication,rollback);else acceptSignedPublication(this.a,publication,rollback,this.clock());const b=this.baseline,p=this.a,reviewed=rollback?b.reviewed:{...clone(b.reviewed),releaseId:TARGET_RELEASE,issuedAt:p.plan.approvedAt,notAfter:publication.release.body.notAfter,artifacts:clone(p.targetManifests)};
  const localFiles=b.proposal.localFiles.map(r=>r.role==='native'?{...r,path:TARGET_DIRECTORY+'/'+r.artifactPath,sha256:p.targetManifests.native.files[r.artifactPath]}:clone(r));
  if(!rollback)reviewed.localFiles=localFiles;
  return {reviewed,proposal:rollback?b.proposal:{...clone(b.proposal),release:publication.release,versions:p.targetVersions,artifacts:p.targetManifests,localFiles,reviewedManifestHash:digest(reviewed)},
   native:rollback?b.native:{...clone(b.native),codeManifest:TARGET_DIRECTORY+'/native-manifest.json'}};
 }
 commitLocal(publication,rollback=false){
  need(this.host==='jenn-System-Product-Name','LOCAL_RECEIVER_REQUIRED');this.gate(rollback);
  // This is the existing Owner lock, not a second revision authority. It is
  // held before any selector INTENT and until every projection has completed.
  const store=new ProtectedStore({directory:this.file(PATHS.configuration),create:false,now:this.clock});
  try{
   const s=store.snapshot(),before=clone(this.baseline.ownerConfiguration),actual=clone(s);delete before.delivery;delete actual.delivery;need(same(before,actual),'OWNER_AUTHORITY_CHANGED');
   const d=publication.delivery,cache={revision:d.body.revision,envelope:d,hash:digest({publicConfig:d.body.publicConfig,control:d.body.control,connectionNonce:s.connectionNonce||0})};
   acceptSignedPublication(this.a,publication,rollback,this.clock());
   need([this.a.sourceDelivery,this.baseline.forwardPublication?.delivery,d].filter(Boolean).some(x=>same(s.delivery?.envelope,x))&&s.delivery?.revision===s.delivery?.envelope?.body?.revision&&s.delivery.hash===digest({publicConfig:s.delivery.envelope.body.publicConfig,control:s.delivery.envelope.body.control,connectionNonce:s.connectionNonce||0}),'OWNER_PREVIOUS_ACCEPTED_DRIFT');
   need(s.delivery.revision<=cache.revision,'OWNER_REVISION_ROLLBACK');if(s.delivery.revision===cache.revision)need(same(s.delivery,cache),'OWNER_SAME_REVISION_CONFLICT');
   const next=this.desired(publication,rollback),forward=this.desired(rollback?this.baseline.forwardPublication:publication,false,true);
   if(!rollback){
    const h=this.baseline.history;need(h&&digest(h.checkpoint)===this.a.checkpointHash,'COMPLETE_HISTORY_INPUT_REQUIRED');
    const descriptor=buildNativeHistoryDescriptor({...h,plan:this.a.plan,stoppedProof:this.gate(),nativeHostConfig:next.native,targetPublicConfig:d.body.publicConfig,targetManifest:this.a.targetManifests.native,ledgerRegistryRaw:Buffer.from(h.ledgerRegistryRaw,'base64'),now:this.clock()});
    next.native.nativeHistory=nativeHistoryConfigBinding(descriptor);forward.native=clone(next.native);
    const raw=Buffer.from(canonical(descriptor));let old;try{old=this.bytes(this.file(HISTORY_PATH));}catch(e){if(e.code!=='ENOENT')throw e;}
    need(!old||old.equals(raw),'HISTORY_DESCRIPTOR_CAS_CONFLICT');
    // Validate every selector before the first descriptor/selector write.
    for(const key of ['reviewed','native','proposal']){const v=this.read(PATHS[key]);need([this.baseline[key],forward[key],next[key]].some(x=>same(x,v)),'FIXED_SELECTOR_CAS_CONFLICT');}
    if(!old){this.gate();this.rawWrite(this.file(HISTORY_PATH),raw,0o644,()=>this.gate());this.fault('write:history-descriptor');}
   }else{
    // Forward selector includes the immutable evidence binding retained on disk.
    try{forward.native.nativeHistory=nativeHistoryConfigBinding(JSON.parse(this.bytes(this.file(HISTORY_PATH))));}catch(e){if(e.code!=='ENOENT')throw e;}
    for(const key of ['reviewed','native','proposal']){const v=this.read(PATHS[key]);need([this.baseline[key],forward[key],next[key]].some(x=>same(x,v)),'FIXED_SELECTOR_CAS_CONFLICT');}
   }
   for(const key of ['reviewed','native','proposal'])this.cas(PATHS[key],this.baseline[key],forward[key],next[key],rollback,key==='native'?0o644:0o600);
   if(s.delivery.revision!==cache.revision){this.gate(rollback);store.transact(x=>{x.delivery=cache;});}this.fault('write:owner-cache');
   this.gate(rollback);return {status:'LOCAL_NATIVE_SELECTOR_AND_OWNER_CACHE_COMMITTED',revision:d.body.revision,nativeSelectorHash:digest(next.native),originalUnknownDisposition:'PRESERVED_NOT_SETTLED'};
  }finally{store.close();}
 }
 commitCloud(publication,rollback=false){
  need(this.host==='VM-0-12-ubuntu','CLOUD_RECEIVER_REQUIRED');this.gate(rollback);acceptSignedPublication(this.a,publication,rollback,this.clock());const b=publication.delivery.body;
  const store=new ProtectedStore({directory:this.file(PATHS.accepted),create:false,now:this.clock});
  try{
   const s=store.snapshot();need(s.kind==='r16.cloud-publication.v1','CLOUD_STATE_KIND');const old=s.accepted;
   need([this.a.sourceDelivery,this.baseline.forwardPublication?.delivery,publication.delivery].filter(Boolean).some(d=>same(old,d))&&old.body.revision<=b.revision,'PREVIOUS_ACCEPTED_DRIFT');
   if(old.body.revision===b.revision)need(same(old,publication.delivery),'CLOUD_SAME_REVISION_CONFLICT');
   need(same(this.read(PATHS.app),this.baseline.app),'UNCHANGED_APP_SELECTOR_DRIFT');
   const token=this.read(PATHS.startAttempt);need(token.schema==='r16.cloud-start-attempt.v1'&&token.grantId==='r16-projects-daily'&&[19,this.a.revisionPlan.forward,this.a.revisionPlan.recovery].includes(token.revision)&&token.revision<=b.revision,'CLOUD_START_TOKEN_CAS_CONFLICT');
   const forward=this.baseline.forwardPublication?.delivery||publication.delivery;
   for(const [p,source,fw,next]of [[PATHS.public,this.a.sourcePublicConfig,forward.body.publicConfig,b.publicConfig],[PATHS.control,this.a.sourceDelivery.body.control,forward.body.control,b.control]])need([source,fw,next].some(x=>same(x,this.read(p))),'FIXED_SELECTOR_CAS_CONFLICT');
   const gate=this.read(PATHS.cloudCutover);need(gate.schema==='r16.cloud-cutover.v1'&&gate.phase==='ACTIVE'&&gate.grantId==='r16-projects-daily'&&[this.a.sourcePublicConfig.release.body.id,TARGET_RELEASE].includes(gate.releaseId),'CLOUD_CUTOVER_DRIFT');
   if(old.body.revision!==b.revision){this.gate(rollback);store.transact(x=>{x.accepted=publication.delivery;});}this.fault('write:cloud-accepted');
   this.cas(PATHS.public,this.a.sourcePublicConfig,forward.body.publicConfig,b.publicConfig,rollback,0o644);
   this.cas(PATHS.control,this.a.sourceDelivery.body.control,forward.body.control,b.control,rollback,0o644);
   if(gate.releaseId!==b.publicConfig.release.body.id)this.write(PATHS.cloudCutover,{...gate,releaseId:b.publicConfig.release.body.id},rollback);
   this.write(PATHS.startAttempt,{schema:'r16.cloud-start-attempt.v1',grantId:'r16-projects-daily',revision:b.revision},rollback);
   return {status:'CLOUD_NATIVE_VERSION_ACCEPTED_APP_SELECTOR_UNCHANGED',revision:b.revision,deliveryHash:digest(publication.delivery)};
  }finally{store.close();}
 }
 accepted(){need(this.host==='VM-0-12-ubuntu','CLOUD_RECEIVER_REQUIRED');return this.read(PATHS.accepted+'/state.json').data.accepted;}
 readback(delivery){
  if(this.host==='VM-0-12-ubuntu')need(same(this.accepted(),delivery)&&same(this.read(PATHS.public),delivery.body.publicConfig)&&same(this.read(PATHS.control),delivery.body.control)&&same(this.read(PATHS.app),this.baseline.app)&&same(this.read(PATHS.startAttempt),{schema:'r16.cloud-start-attempt.v1',grantId:'r16-projects-daily',revision:delivery.body.revision})&&this.read(PATHS.cloudCutover).releaseId===delivery.body.publicConfig.release.body.id,'CLOUD_READBACK_MISMATCH');
  else {need(same(this.read(PATHS.configuration+'/state.json').data.delivery.envelope,delivery),'LOCAL_DELIVERY_READBACK_MISMATCH');const source=same(delivery.body.publicConfig,this.a.sourcePublicConfig),native=this.read(PATHS.native);need(native.codeManifest===(source?this.baseline.native.codeManifest:TARGET_DIRECTORY+'/native-manifest.json'),'NATIVE_SELECTOR_READBACK_DRIFT');}
  return {status:'EXACT_CONFIGURATION_AND_NATIVE_SELECTOR_READBACK',revision:delivery.body.revision,nativeVersion:delivery.body.publicConfig.versions.native,businessAcceptance:false,drainStatus:'UNPROVEN'};
 }
}
export async function runTransition({artifacts:a,local,cloud,osAdapter,packageRoot,signer,now=Date.now,fault=()=>{}}){
 assertArtifacts(a);need(local.a===a&&cloud.a===a,'RECEIVER_ARTIFACT_MISMATCH');
 need(a.environment==='ISOLATED_TEST'||signer===undefined,'PRODUCTION_SIGNER_OVERRIDE_REFUSED');
 const journal=local.journal(),proof=()=>assertStoppedProof(osAdapter.observe(),a,now());
 const savedForward=journal.read('signed')||journal.read('signing-forward-result');if(savedForward){local.baseline.forwardPublication=savedForward;cloud.baseline.forwardPublication=savedForward;}
 const sign=rollback=>{
  proof();const kind=rollback?'rollback':'forward',result=journal.read('signing-'+kind+'-result');if(result)return acceptSignedPublication(a,result,rollback,now());
  need(!journal.read('signing-'+kind+'-intent'),'UNKNOWN_SIGNING_NOT_REPLAYED');
  const intent={planHash:a.planHash,artifactsHash:digest(a),kind,proofHash:proof()};journal.write('signing-'+kind+'-intent',intent);fault('signing-intent:'+kind);
  const value=a.environment==='ISOLATED_TEST'?signer(a,rollback):signFixedPublication(a,osAdapter.observe(),{rollback});
  acceptSignedPublication(a,value,rollback,now());journal.write('signing-'+kind+'-result',value);return value;
 };
 const phase=()=>{const mode=journal.read('transaction')?.mode,d=cloud.accepted();
  if(mode==='FORWARD'){need(same(d,local.baseline.forwardPublication?.delivery),'FORWARD_ACCEPTED_DELIVERY_REQUIRED');acceptSignedPublication(a,{release:d.body.publicConfig.release,delivery:d},false,now());return 'FORWARD';}
  need(['ABORT','ROLLBACK'].includes(mode),'RECOVERY_MODE_REQUIRED');
  need((mode==='ABORT'&&same(d,a.sourceDelivery))||(mode==='ROLLBACK'&&d.body.revision===a.revisionPlan.recovery&&same(d.body.publicConfig,a.sourcePublicConfig)),'RECOVERY_ACCEPTED_SOURCE_REQUIRED');if(mode==='ROLLBACK')acceptSignedPublication(a,{release:d.body.publicConfig.release,delivery:d},true,now());else need(now()<a.plan.recoveryDeadline,'RECOVERY_WINDOW_EXPIRED');return mode;
 };
 const expected=(d,recovery)=>{const state=osAdapter.expectedState(d);need(state?.verified===true&&state.planHash===a.planHash,'ACTUAL_EXPECTED_OS_STATE_UNPROVEN');
  if(recovery)need(state.nativeStopped===true&&state.nativeSelectorHash===digest(local.baseline.native)&&same(local.read(PATHS.native),local.baseline.native),'RECOVERY_NATIVE_SOURCE_STOPPED_UNPROVEN');return state;
 };
 const adapters={baseline:()=>{need(same(osAdapter.originalBaselineHash(),a.plan.originalBaselineHash),'ORIGINAL_BASELINE_DRIFT');return {originalBaselineHash:a.plan.originalBaselineHash};},
  quiesce:()=>{proof();return {status:'STOPPED_FENCED_NOT_DRAINED',planHash:a.planHash};},observe:proof,
  stage:()=>{proof();return {local:local.stage(packageRoot.local),cloud:cloud.stage(packageRoot.cloud)};},
  sign:()=>{const p=sign(false);local.baseline.forwardPublication=p;cloud.baseline.forwardPublication=p;return p;},
  cloudCommit:d=>cloud.commitCloud({release:d.body.publicConfig.release,delivery:d},d.body.revision===a.revisionPlan.recovery),
  localCommit:(p,rollback=false)=>local.commitLocal({release:p.delivery.body.publicConfig.release,delivery:p.delivery},rollback),
  activate:async()=>{const p=phase(),recovery=p!=='FORWARD';const scope={planHash:a.planHash,phase:p,nativeMustRemainStopped:recovery,appMustRemainClosedUntilSafe:recovery,nativeAbortPolicy:a.plan.recoveryPolicy};const r=recovery?await osAdapter.resume(scope):await osAdapter.activate(scope);if(r.status==='OS_ACTIVE')expected(cloud.accepted(),recovery);return r;},
  resume:async()=>{need(phase()==='ABORT','ABORT_RESUME_ONLY');const r=await osAdapter.resume({planHash:a.planHash,phase:'ABORT',nativeMustRemainStopped:true,appMustRemainClosedUntilSafe:true});if(r.status==='OS_ACTIVE')expected(cloud.accepted(),true);return r;},
  requiesce:()=>{const r=osAdapter.requiesce();proof();return r;},accepted:()=>cloud.accepted(),
  signRollback:()=>sign(true),verify:d=>{const r=local.readback(d),remote=cloud.readback(d);const p=phase(),state=expected(d,p!=='FORWARD');return {...r,cloud:remote,actualOSState:state};}};
 const run=()=>drive({journal,adapters,now,fault});
 // The fixture uses the same actual flock and atomic journal as production.
 const lock=local.file(STATE+'/.transaction-lock');local.directory(path.dirname(lock));return locked(lock,run);
}
