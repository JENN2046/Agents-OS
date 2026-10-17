// Fixed same-Owner/Grant maintenance publication, not Human first-cutover STOP.
import fs from 'node:fs';
import os from 'node:os';
import {fileURLToPath} from 'node:url';
import {createPrivateKey} from 'node:crypto';
import {canonical,digest,signed,verified,exportPublicKey,verifyRelease} from '../../src/lease-core.mjs';
import {SOURCE19_BASELINE,inspectSourcePublicConfiguration} from '../../authority/source-baseline.mjs';
export {canonical,digest};
export const TARGET_RELEASE='r16-daily-20261017-source19-native-lifecycle-r1';
export const TARGET_DIRECTORY='/opt/r16/releases/'+TARGET_RELEASE;
export const UNIT='r16-source19-native-transition-r1.service';
export const ROOT='/usr/lib/r16-maintenance/source19-native-transition-r1';
export const STATE='/var/lib/r16-maintenance/source19-native-transition-r1';
export const CHANGED=Object.freeze(['host/workspace-dispatcher.mjs','host/headless-host.mjs','host/native-runner.mjs',
 'native/upstream/VCPDistributedServer/Plugin/ProjectForge/ProjectForgeService.js',
 'native/upstream/VCPDistributedServer/Plugin/ProjectForge/indexerClient.js']);
export const NATIVE_OVERLAY_PINS=Object.freeze({
 'host/workspace-dispatcher.mjs':'f99830fea07c8ab7cd8873910f31ff5e6ac74d71cfd4b88fab3c2f35f64429cb',
 'host/headless-host.mjs':'070d22210d7c6df733aa337b6ddd6e49c1e4ec1a479d59357515f0533e81f06f',
 'host/native-runner.mjs':'990e3f186c45c2db377181aeda9204d64372544ddfcb40f9b83aa6d65ba1b0c2',
 'native/upstream/VCPDistributedServer/Plugin/ProjectForge/ProjectForgeService.js':'e3739ed2c91d96dd79eb7596ef0cf3cf95800971f330823e916c5ddb35e736f5',
 'native/upstream/VCPDistributedServer/Plugin/ProjectForge/indexerClient.js':'1e5f91e7021fc914b2dbe66323ccc1632ad6a14f05e476a7cdb1a088d33f9c8e'});
const ROLES=['app','bridge','native'],brand=new WeakSet(),same=(a,b)=>canonical(a)===canonical(b);
export const need=(v,c)=>{if(!v)throw Object.assign(Error(c),{code:c});};
const hash=v=>typeof v==='string'&&/^[0-9a-f]{64}$/.test(v),integer=v=>Number.isSafeInteger(v)&&v>=0;
const copy=v=>JSON.parse(canonical(v));
function frozen(v){if(v&&typeof v==='object'){Object.values(v).forEach(frozen);Object.freeze(v);}return v;}
export function inspectSource19(pub,delivery,now=Date.now()){
 inspectSourcePublicConfiguration(pub);
 const b=verified(delivery,pub.issuerPublicKey,'r16.configuration-delivery.v1');
 need(digest(delivery)===SOURCE19_BASELINE.acceptedDeliveryHash&&b.revision===19&&same(b.publicConfig,pub)&&
  same(b.control,{grantId:'r16-projects-daily',grantVersion:1,status:'ACTIVE',connectRequested:true})&&
  integer(b.issuedAt)&&b.issuedAt<=now,'SOURCE19_ACCEPTED_DELIVERY_DRIFT');
 verifyRelease(pub.release,pub.releasePublicKey,{versions:pub.versions,actions:pub.grant.body.actions,now});
 return {publicConfigHash:digest(pub),sourceDeliveryHash:digest(delivery),revision:19};
}
export function explicitRevisionPlan(inventory,requested,now=Date.now()){
 need(inventory?.schema==='r16.fresh-revision-inventory.v1'&&inventory.acceptedRevision===19&&
  inventory.acceptedDeliveryHash===SOURCE19_BASELINE.acceptedDeliveryHash&&integer(inventory.observedAt)&&
  inventory.observedAt<=now&&now-inventory.observedAt<=60000&&inventory.complete===true&&
  integer(inventory.signedMaximum)&&inventory.signedMaximum>=19&&integer(inventory.reservedMaximum)&&inventory.reservedMaximum>=20,
  'FRESH_REVISION_INVENTORY_REQUIRED');
 need(requested?.legacy21_22Disposition==='CANCELLED_UNALLOCATED_REPLAN'&&integer(requested.forward)&&integer(requested.recovery)&&
  requested.forward>Math.max(20,inventory.signedMaximum,inventory.reservedMaximum)&&requested.recovery>requested.forward,
  'EXPLICIT_REVISION_REPLAN_REQUIRED');
 return frozen({...copy(requested),inventoryHash:digest(inventory)});
}
function manifests(source,target,inventory,sourcePub){
 need(same(Object.keys(source).sort(),ROLES.slice().sort())&&same(Object.keys(target).sort(),ROLES.slice().sort()),'THREE_MANIFESTS_REQUIRED');
 for(const r of ROLES){
  const s=source[r],t=target[r];need(s.schema===t.schema&&s.schema==='r16.runtime-code.v1'&&s.role===t.role&&s.role===r&&s.entry===t.entry&&s.files[s.entry]&&
   digest(s)===sourcePub.versions[r]&&same(Object.keys(s.files).sort(),Object.keys(t.files).sort()),'MANIFEST_SCOPE_DRIFT');
 }
 need(same(source.app,target.app)&&same(source.bridge,target.bridge),'NON_NATIVE_MANIFEST_CHANGED');
 const changed=Object.keys(source.native.files).filter(n=>source.native.files[n]!==target.native.files[n]).sort();
 need(same(changed,CHANGED.slice().sort()),'EXACT_FIVE_NATIVE_CHANGES_REQUIRED');
 const union={};for(const m of Object.values(target))for(const [n,h]of Object.entries(m.files)){
  need(!n.startsWith('/')&&!n.includes('\\')&&n.split('/').every(p=>p&&p!=='.'&&p!=='..')&&hash(h)&&(!union[n]||union[n]===h),'PAYLOAD_ROLE_OVERLAP');union[n]=h;
 }
 need(same(Object.keys(union).sort(),Object.keys(inventory).sort()),'COMPLETE_PAYLOAD_REQUIRED');
 for(const [n,h]of Object.entries(union)){const row=inventory[n];need(row.sha256===h&&integer(row.bytes)&&[420,493].includes(row.mode),'PAYLOAD_INVENTORY_DRIFT');}
 return Object.fromEntries(ROLES.map(r=>[r,digest(target[r])]));
}
function build(input,environment){
 const {sourcePublicConfig:p,sourceDelivery:d,sourceManifests,targetManifests,inventory,revisionInventory,revisionPlan:requested,plan,now=Date.now()}=input;
 if(environment==='PROTECTED_SOURCE')inspectSource19(p,d,now);
 else {const b=verified(d,p.issuerPublicKey,'r16.configuration-delivery.v1');verified(p.grant,p.issuerPublicKey,'r16.workspace.v1');verifyRelease(p.release,p.releasePublicKey,{versions:p.versions,actions:p.grant.body.actions,now});need(b.revision===19&&same(b.publicConfig,p),'FIXTURE_SOURCE_INVALID');}
 // The revision inventory was accepted with the exact pre-stop plan. Stopping
 // cannot change that plan's hash by inventing a newer observation timestamp.
 const revisionPlan=explicitRevisionPlan(revisionInventory,requested,plan.approvedAt);
 need(plan?.schema==='r16.source19-native-transition.plan.v1'&&plan.sourcePublicConfigHash===digest(p)&&plan.sourceDeliveryHash===digest(d)&&
  hash(plan.codeFreezeHash)&&hash(plan.originalBaselineHash)&&hash(plan.nativeTargetHash)&&
  typeof plan.stopEpoch==='string'&&integer(plan.approvedAt)&&integer(plan.expiresAt)&&
  plan.approvedAt<=now&&now<plan.expiresAt&&plan.expiresAt-plan.approvedAt<=300000&&
  integer(plan.recoveryDeadline)&&plan.recoveryDeadline>=plan.expiresAt&&plan.recoveryDeadline<=plan.approvedAt+1800000&&
  plan.revisionPlanHash===digest(revisionPlan)&&plan.targetReleaseId===TARGET_RELEASE&&plan.recoveryPolicy==='KEEP_CRASHED_NATIVE_STOPPED_NO_AUTOMATIC_BUSINESS_REOPEN'&&
  plan.scope==='SAME_PLAN_SOURCE19_NATIVE_MAINTENANCE_NOT_DRAINED'&&plan.grantHash===digest(p.grant)&&plan.sourceNativeVersion===p.versions.native&&
  hash(plan.approvedControlUnknownHash)&&integer(plan.approvedControlUnknownCount)&&plan.approvedControlUnknownCount<=100000&&plan.allowNativeNonGracefulOnce===true&&plan.acceptUnprovenInflight===true&&plan.acceptPossibleUpstreamContinuation===true&&/^[0-9a-f]{32}$/.test(plan.nonce)&&
  /^[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}$/.test(plan.stopEpoch),'EXACT_NATIVE_PLAN_REQUIRED');
 need(!Object.hasOwn(plan,'artifactsHash')&&!Object.hasOwn(plan,'stoppedProof'),'PLAN_HASH_CYCLE_REFUSED');
 const fields=['schema','scope','sourcePublicConfigHash','sourceDeliveryHash','grantHash','sourceNativeVersion','targetReleaseId','targetNativeVersion','targetInventoryHash','codeFreezeHash','originalBaselineHash','nativeTargetHash','stopEpoch','nonce','approvedAt','expiresAt','recoveryDeadline','allowNativeNonGracefulOnce','acceptUnprovenInflight','acceptPossibleUpstreamContinuation','recoveryPolicy','revisionPlanHash','approvedControlUnknownHash','approvedControlUnknownCount'];
 need(same(Object.keys(plan).sort(),fields.sort()),'EXACT_PLAN_FIELDS_REQUIRED');
 const versions=manifests(sourceManifests,targetManifests,inventory,p);
 need(plan.targetNativeVersion===versions.native&&plan.targetInventoryHash===digest(inventory),'APPROVED_TARGET_CONTENT_DRIFT');
 need(hash(input.stoppedProof?.checkpointHash),'POST_STOP_CHECKPOINT_REQUIRED');
 if(environment==='PROTECTED_SOURCE')need(CHANGED.every(n=>targetManifests.native.files[n]===NATIVE_OVERLAY_PINS[n]),'FIXED_NATIVE_OVERLAY_DRIFT');
 const releaseBody={...copy(p.release.body),id:TARGET_RELEASE,issuedAt:plan.approvedAt,versions};
 need(releaseBody.notAfter>plan.recoveryDeadline,'SOURCE_RELEASE_WINDOW_INSUFFICIENT');
 const a=frozen({schema:'r16.source19-native-transition.artifacts.v1',environment,plan:copy(plan),planHash:digest(plan),sourcePublicConfig:copy(p),sourceDelivery:copy(d),
  sourceManifests:copy(sourceManifests),targetManifests:copy(targetManifests),inventory:copy(inventory),inventoryHash:digest(inventory),
  targetVersions:versions,revisionPlan,releaseBody,checkpointHash:input.stoppedProof.checkpointHash,initialStopProofHash:digest(input.stoppedProof),authority:false,mayExecute:false,businessAcceptance:false});brand.add(a);assertStoppedProof(input.stoppedProof,a,now);return a;
}
export const buildPublicationArtifacts=input=>build(input,'PROTECTED_SOURCE');
export function buildIsolatedPublicationArtifacts(input,fixtureRoot){
 const s=fs.lstatSync(fixtureRoot);need(process.geteuid()!==0&&fixtureRoot.startsWith('/tmp/')&&s.isDirectory()&&!s.isSymbolicLink()&&s.uid===process.geteuid()&&(s.mode&0o7777)===0o700,'ISOLATED_PRIVATE_TMP_REQUIRED');
 return build(input,'ISOLATED_TEST');
}
export function assertArtifacts(a){need(brand.has(a)&&Object.isFrozen(a),'BRANDED_ARTIFACTS_REQUIRED');}
export function assertStoppedProof(proof,a,now=Date.now()){
 assertArtifacts(a);const p=a.plan;
 need(proof?.schema==='r16.source19-native-transition.stopped-fenced.v1'&&proof.status==='STOPPED_FENCED_NOT_DRAINED'&&
  proof.environment===(a.environment==='ISOLATED_TEST'?'ISOLATED_TEST':'PRODUCTION')&&
  proof.planHash===a.planHash&&proof.sourcePublicConfigHash===p.sourcePublicConfigHash&&proof.sourceDeliveryHash===p.sourceDeliveryHash&&
  proof.grantHash===digest(a.sourcePublicConfig.grant)&&proof.codeFreezeHash===p.codeFreezeHash&&proof.originalBaselineHash===p.originalBaselineHash&&
  proof.controlUnknownHash===p.approvedControlUnknownHash&&proof.controlUnknownCount===p.approvedControlUnknownCount&&proof.checkpointHash===a.checkpointHash&&proof.nativeTargetHash===p.nativeTargetHash&&proof.stopEpoch===p.stopEpoch&&
  integer(proof.issuedAt)&&integer(proof.expiresAt)&&p.approvedAt<=proof.issuedAt&&proof.issuedAt<=now&&now<proof.expiresAt&&proof.expiresAt<=p.recoveryDeadline&&proof.expiresAt-proof.issuedAt<=30000&&
  proof.originalUnknownPreserved===true&&proof.noForeignWriters===true&&proof.relayStopped===true&&proof.globalExecution==='UNPROVEN'&&
  typeof proof.forceTerminationUsed==='boolean'&&proof.roleStopReceipt===false&&proof.businessAcceptance===false, 'STOPPED_FENCED_PROOF_REQUIRED');
 const units={'r16-owner.service':['jenn-System-Product-Name','r16-owner.service'],'r16-native.service':['jenn-System-Product-Name','r16-native.service'],'r16-app.service':['VM-0-12-ubuntu','r16-app.service'],'r16-bridge.service':['VM-0-12-ubuntu','r16-bridge.service']};
 need(same(Object.keys(proof.actors||{}).sort(),Object.keys(units).sort()),'FOUR_ACTORS_REQUIRED');
 for(const [r,[host,unit]]of Object.entries(units)){const x=proof.actors[r];need(x.host===host&&x.unit===unit&&x.mainPid===0&&x.controlPid===0&&x.cgroupEmpty===true&&x.ownedPersistentFence===true&&x.pendingJob===false,'FIXED_ACTOR_NOT_STOPPED');}
 return digest(proof);
}
export function deliveryBody(a,release,rollback=false){assertArtifacts(a);return {...copy(a.sourceDelivery.body),issuedAt:a.plan.approvedAt,
 revision:rollback?a.revisionPlan.recovery:a.revisionPlan.forward,publicConfig:rollback?copy(a.sourcePublicConfig):{...copy(a.sourcePublicConfig),release:copy(release),versions:copy(a.targetVersions)}};}
// Cryptographic/historical body check only; this grants no effect window.
export function verifyPublicationBodies(a,publication,rollback=false){
 assertArtifacts(a);const p=a.sourcePublicConfig;
 const r=verified(publication.release,p.releasePublicKey,'r16.release.v1');
 need(same(r,rollback?p.release.body:a.releaseBody),'RELEASE_BODY_CHANGED');
 const b=verified(publication.delivery,p.issuerPublicKey,'r16.configuration-delivery.v1');
 need(same(b,deliveryBody(a,publication.release,rollback)),'DELIVERY_BODY_CHANGED');return frozen(copy(publication));
}
export function acceptSignedPublication(a,publication,rollback=false,now=Date.now()){
 need(now<(rollback?a.plan.recoveryDeadline:a.plan.expiresAt),'PUBLICATION_WINDOW_EXPIRED');return verifyPublicationBodies(a,publication,rollback);
}
function protectedBytes(path,mode){
 need(path.startsWith('/')&&!path.includes('/../'),'FIXED_ROOT_PATH_REQUIRED');let cursor='';for(const bit of path.split('/').filter(Boolean)){cursor+='/'+bit;const s=fs.lstatSync(cursor);need(!s.isSymbolicLink()&&s.uid===0&&!(s.mode&0o022),'ROOT_SOURCE_UNPROTECTED');}
 const fd=fs.openSync(path,fs.constants.O_RDONLY|fs.constants.O_NOFOLLOW);try{const s=fs.fstatSync(fd);need(s.isFile()&&s.nlink===1&&s.size<32*1024*1024&&(!mode||(s.mode&0o7777)===mode),'ROOT_FILE_REFUSED');const b=fs.readFileSync(fd);need(b.length===s.size,'ROOT_FILE_CHANGED');return b;}finally{fs.closeSync(fd);}
}
export function assertFixedSigningContext(a,proof,rollback=false){
 assertArtifacts(a);need(a.environment==='PROTECTED_SOURCE'&&process.getuid()===0&&process.geteuid()===0&&os.hostname()==='jenn-System-Product-Name','FIXED_SIGNER_CONTEXT_REQUIRED');
 need(fs.readFileSync('/proc/self/cgroup','utf8').trim()==='0::/system.slice/'+UNIT,'FIXED_SIGNER_CGROUP_REQUIRED');
 need(fileURLToPath(import.meta.url)===ROOT+'/runtime/maintenance/source19-native-transition-r1/publication.mjs','FIXED_SIGNER_SOURCE_REQUIRED');
 const plan=JSON.parse(protectedBytes(STATE+'/plan.json',0o600)),stop=JSON.parse(protectedBytes(STATE+'/stop-proof.json',0o600));
 need(same(plan,a.plan)&&same(stop,proof),'PROTECTED_STOP_OR_PLAN_DRIFT');assertStoppedProof(stop,a);
 need(Date.now()<(rollback?plan.recoveryDeadline:plan.expiresAt),'FIXED_SIGNER_WINDOW_EXPIRED');
 const freeze=JSON.parse(protectedBytes('/etc/r16-maintenance/source19-native-transition-r1-source-freeze.json',0o600));
 need(freeze.planHash===a.planHash&&freeze.artifactsHash===digest(a)&&freeze.codeFreezeHash===plan.codeFreezeHash&&digest(freeze.files)===plan.codeFreezeHash,'SIGNER_FREEZE_DRIFT');
 for(const [file,pin]of Object.entries(freeze.files||{})){need(file.startsWith(ROOT+'/runtime/')&&hash(pin),'SIGNER_FREEZE_PATH');need(digestBytes(protectedBytes(file))===pin,'SIGNER_SOURCE_CHANGED');}
 const required=['maintenance/source19-native-transition-r1/publication.mjs','maintenance/source19-native-transition-r1/transaction.mjs','maintenance/release-r6/transaction-driver.mjs','maintenance/release-r6/io.mjs','src/lease-core.mjs','src/control-clock.mjs','authority/source-baseline.mjs','maintenance/source19-native-transition-r1/history-baseline.mjs'];
 need(required.every(f=>hash(freeze.files?.[ROOT+'/runtime/'+f])),'SIGNER_FREEZE_INCOMPLETE');
 const owner=JSON.parse(protectedBytes('/var/lib/r16-owner/configuration/state.json',0o600));
 need(owner.schema===1&&owner.data?.kind==='r16.owner.configuration.v1'&&owner.data.connected===true&&owner.data.activeGrantId==='r16-projects-daily','CURRENT_OWNER_CONFIGURATION_REQUIRED');
 const accepted=owner.data.delivery?.envelope,allowed=[a.sourceDelivery];
 if(rollback){const forward=JSON.parse(protectedBytes(STATE+'/journal/signing-forward-result.json',0o600));verifyPublicationBodies(a,forward,false);allowed.push(forward.delivery);}
 need(allowed.some(d=>same(d,accepted))&&owner.data.delivery.revision===accepted?.body?.revision&&
  owner.data.delivery.hash===digest({publicConfig:accepted.body.publicConfig,control:accepted.body.control,connectionNonce:owner.data.connectionNonce||0}), 'CURRENT_OWNER_DELIVERY_DRIFT');
 const revisions=JSON.parse(protectedBytes(STATE+'/revision-inventory.json',0o600));
 need(digest(revisions)===a.revisionPlan.inventoryHash,'PROTECTED_REVISION_INVENTORY_DRIFT');
 need(Date.now()<(rollback?plan.recoveryDeadline:plan.expiresAt),'FIXED_SIGNER_WINDOW_EXPIRED');
}
import {createHash} from 'node:crypto';
const digestBytes=b=>createHash('sha256').update(b).digest('hex');
function mountedKey(name,expected,beforeRead){
 const dir='/run/credentials/'+UNIT,rows=fs.readFileSync('/proc/self/mountinfo','utf8').trim().split('\n').map(l=>l.split(' ')).filter(r=>r[4]===dir);
 need(rows.length===1,'CREDENTIAL_MOUNT_REQUIRED');const r=rows[0],i=r.indexOf('-');need(i>5&&r[5].split(',').includes('ro')&&['tmpfs','ramfs'].includes(r[i+1]),'CREDENTIAL_MOUNT_REQUIRED');
 beforeRead();const bytes=protectedBytes(dir+'/'+name);try{const s=fs.lstatSync(dir+'/'+name);need([0o400,0o440].includes(s.mode&0o7777)&&s.dev===fs.lstatSync(dir).dev,'CREDENTIAL_FILE_REFUSED');const key=createPrivateKey({key:bytes,format:'der',type:'pkcs8'});need(exportPublicKey(key)===expected&&key.asymmetricKeyType==='ed25519','SIGNER_PUBLIC_KEY_DRIFT');return key;}finally{bytes.fill(0);}
}
export function signFixedPublication(a,proof,{rollback=false}={}){
 assertFixedSigningContext(a,proof,rollback);
 const kind=rollback?'rollback':'forward',intent=JSON.parse(protectedBytes(STATE+'/journal/signing-'+kind+'-intent.json',0o600));
 need(intent.planHash===a.planHash&&intent.artifactsHash===digest(a)&&intent.kind===kind&&intent.proofHash===digest(proof),'DURABLE_SIGNING_INTENT_REQUIRED');
 // This once marker is consumed before reading any key. Lost reply never
 // permits another signing invocation, including an interrupted pre-sign read.
 need(Date.now()<(rollback?a.plan.recoveryDeadline:a.plan.expiresAt),'FIXED_SIGNER_WINDOW_EXPIRED');
 const fd=fs.openSync(STATE+'/signer-'+kind+'-consumed.json',fs.constants.O_WRONLY|fs.constants.O_CREAT|fs.constants.O_EXCL|fs.constants.O_NOFOLLOW,0o600);
 try{fs.writeFileSync(fd,canonical({planHash:a.planHash,intentHash:digest(intent),consumedAt:Date.now()}));fs.fsyncSync(fd);}finally{fs.closeSync(fd);}
 const parent=fs.openSync(STATE,fs.constants.O_RDONLY|fs.constants.O_DIRECTORY);try{fs.fsyncSync(parent);}finally{fs.closeSync(parent);}
 const releaseKey=rollback?null:mountedKey('release-signing-key',a.sourcePublicConfig.releasePublicKey,()=>assertFixedSigningContext(a,proof,rollback));
 const issuerKey=mountedKey('issuer-signing-key',a.sourcePublicConfig.issuerPublicKey,()=>assertFixedSigningContext(a,proof,rollback));
 assertFixedSigningContext(a,proof,rollback);
 const release=rollback?a.sourcePublicConfig.release:signed(a.releaseBody,releaseKey);
 assertFixedSigningContext(a,proof,rollback);
 const delivery=signed(deliveryBody(a,release,rollback),issuerKey);
 return acceptSignedPublication(a,{release,delivery},rollback);
}
