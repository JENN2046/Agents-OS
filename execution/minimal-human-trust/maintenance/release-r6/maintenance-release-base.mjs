// Fixed R15 recovery maintenance planning and durable transaction core.
// Production OS adapters are deliberately absent. No CLI or credential reader.
import fs from 'node:fs';
import path from 'node:path';
import {createHash,createPublicKey,verify} from 'node:crypto';
import {spawnSync} from 'node:child_process';

export const FIXED=Object.freeze({
  packageDirectory:'/home/jenn/AGENTS_OS_Workspace/ops/g1d-native-recovery-reconnect-20261014-r1/r15-backport/maintenance-app-recovery-r6/package',
  sourceReleaseId:'r16-daily-20261012-r15',targetReleaseId:'r16-daily-20261015-r15-app-recovery-r6',
  sourceDirectory:'/opt/r16/releases/r16-daily-20261012-r15',
  targetDirectory:'/opt/r16/releases/r16-daily-20261015-r15-app-recovery-r6',
  publicConfigDigest:'be3ff2b5125f8212206d2848bb32889c3c6b50a8ca56aa3b1a4bc4359591bbdb',
  grantHash:'00ac437d66143e627132975555d06396d69ff69616f630d19e3622627e15c5e6',
  changedFile:'host/workspace-dispatcher.mjs',
  oldDispatcherSha256:'0d0b74d1f4a7d425c17b553e08cd8b15f16ed8bfcf9c561d796354996bab6480',
  dispatcherSha256:'ba4ef78187a8701b97bd03461faed44771c4d71b8541681a6d573e3f35ed079c',
  sourceAppVersion:'235a5b919c65ac1d73290732d2b2014c24a338cc4b6795a5064e804803ec1e7a',
  targetAppVersion:'34731b300ccad9a1fbfd45b07422d847e8989d7e9dc052b0dda939cd99adb500',
  appHostSha256:'bfef60223b8fd186f2e96887b770678777bf99ff2a5c84a3c36273d8f172a6ab',
  appRunnerSha256:'feaf51d26f5ef56cdfe013b65fe3faef37f91bc26391835810deb655e51f14d7',
  bridgeVersion:'9c58c33478388003fd52da0cb15736ec951a9bfc9cf29738e20de5d741921352',
  oldNativeVersion:'76319c50acaec649967986c1f12e6923ba4f664ac3230596ed2703fce3470ae6',
  nativeVersion:'2516e881b0622b3ac2d53c454e6ccf9950441c5cb3c26a53500b45d3b1dbe7b4',
});
export const ISOLATED_RELEASE_DOMAIN='R16-MAINTENANCE-ISOLATED-NOT-A-RELEASE\0';
const roles=['app','bridge','native'];
const services=['r16-owner.service','r16-native.service','r16-app.service','r16-bridge.service'];
const stateHashes=['ownerIssuerSha256','ownerConfigurationSha256','nativeDispatcherSha256',
  'appHostSha256','bridgeStateSha256','gatewayStateSha256','sourceProposalSha256',
  'sourceReviewedInstallationSha256','nativeHostConfigSha256','localCutoverSha256',
  'cloudPublicConfigSha256','cloudAuthorityControlSha256','cloudCutoverSha256','cloudAcceptedDeliverySha256'];
const inspections=new WeakSet(),plans=new WeakSet(),admissions=new WeakMap();
const need=(ok,code)=>{if(!ok)throw Object.assign(Error(code),{code});};
export const canonical=x=>x===null||typeof x!=='object'?JSON.stringify(x):Array.isArray(x)
  ?'['+x.map(canonical).join(',')+']':'{'+Object.keys(x).sort().map(k=>JSON.stringify(k)+':'+canonical(x[k])).join(',')+'}';
export const sha256=x=>createHash('sha256').update(x).digest('hex');
export const digest=x=>sha256(Buffer.from(canonical(x)));
const same=(a,b)=>canonical(a)===canonical(b);
const hash=x=>typeof x==='string'&&/^[a-f0-9]{64}$/.test(x);
const integer=x=>Number.isSafeInteger(x)&&x>=0;
const clone=x=>structuredClone(x);
function freeze(x){if(x&&typeof x==='object'){Object.values(x).forEach(freeze);Object.freeze(x);}return x;}
function signedBody(envelope,key,domain,schema){
  need(envelope&&typeof envelope==='object'&&same(Object.keys(envelope).sort(),['body','signature']),'SIGNED_ENVELOPE_INVALID');
  need(envelope.body?.schema===schema&&typeof envelope.signature==='string'&&/^[A-Za-z0-9_-]+$/.test(envelope.signature),'SIGNED_ENVELOPE_INVALID');
  let pub,signature;try{pub=createPublicKey({key:Buffer.from(key,'base64url'),format:'der',type:'spki'});signature=Buffer.from(envelope.signature,'base64url');}catch{need(false,'SIGNATURE_INVALID');}
  need(pub.asymmetricKeyType==='ed25519'&&pub.export({type:'spki',format:'der'}).toString('base64url')===key&&signature.length===64&&signature.toString('base64url')===envelope.signature,'SIGNATURE_INVALID');
  need(verify(null,Buffer.from(domain+canonical(envelope.body)),pub,signature),'SIGNATURE_INVALID');return envelope.body;
}
function relative(name){need(typeof name==='string'&&!path.isAbsolute(name)&&!name.includes('\\')&&!name.includes('\0')&&name.split('/').every(x=>x&&x!=='.'&&x!=='..'),'PATH_INVALID');return name;}
function bytes(root,name,max=64*1024*1024){
  relative(name);let file=path.resolve(root);
  let cursor='/';for(const p of file.split('/').filter(Boolean)){cursor=path.join(cursor,p);need(!fs.lstatSync(cursor).isSymbolicLink(),'PATH_SYMLINK');}
  for(const p of name.split('/')){file=path.join(file,p);need(!fs.lstatSync(file).isSymbolicLink(),'PATH_SYMLINK');}
  const fd=fs.openSync(file,fs.constants.O_RDONLY|fs.constants.O_NOFOLLOW);
  try{const s=fs.fstatSync(fd);need(s.isFile()&&s.nlink===1&&s.size<=max&&!(s.mode&0o7022),'FILE_INVALID');const b=fs.readFileSync(fd);need(b.length===s.size,'FILE_CHANGED');return b;}finally{fs.closeSync(fd);}
}
function sourcePublic(pub,now){
  need(digest(pub)===FIXED.publicConfigDigest&&digest(pub.grant)===FIXED.grantHash,'SOURCE_PUBLIC_DRIFT');
  const grant=signedBody(pub.grant,pub.issuerPublicKey,'R16-SIGNED\0','r16.workspace.v1');
  const release=signedBody(pub.release,pub.releasePublicKey,'R16-SIGNED\0','r16.release.v1');
  need(grant.id==='r16-projects-daily'&&grant.version===1&&grant.channel==='main'&&same(grant.peers,pub.peers),'GRANT_DRIFT');
  need(release.id===FIXED.sourceReleaseId&&same(release.versions,pub.versions)&&release.issuedAt<=now&&now<release.notAfter,'SOURCE_RELEASE_INVALID');return {grant,release};
}
export function inspectPhysicalPackage({directory=FIXED.packageDirectory,now=Date.now()}={}){
  need(path.resolve(directory)===directory,'PACKAGE_PATH_INVALID');
  const read=name=>JSON.parse(bytes(directory,'metadata/'+name));
  const pub=read('R15_PUBLIC_CONFIG.json'),base=read('BASE_ROLE_MANIFESTS.json');sourcePublic(pub,now);
  const manifests=Object.fromEntries(roles.map(r=>[r,read(r+'-manifest.json')]));
  const oldVersions={app:FIXED.sourceAppVersion,bridge:FIXED.bridgeVersion,native:FIXED.oldNativeVersion};
  const newVersions={app:FIXED.targetAppVersion,bridge:FIXED.bridgeVersion,native:FIXED.nativeVersion};
  const union={};
  for(const r of roles){
    need(digest(base[r])===oldVersions[r]&&digest(manifests[r])===newVersions[r],'ROLE_MANIFEST_DRIFT');
    for(const [name,h] of Object.entries(base[r].files)){relative(name);need(hash(h)&&(!union[name]||union[name]===h),'ROLE_OVERLAP_CONFLICT');union[name]=h;}
    const expected=clone(base[r]);if(r==='native')expected.files[FIXED.changedFile]=FIXED.dispatcherSha256;
    if(r==='app'){expected.files['app/workspace-host.mjs']=FIXED.appHostSha256;expected.files['app/app-runner.mjs']=FIXED.appRunnerSha256;}
    need(same(expected,manifests[r]),'ROLE_SCOPE_EXPANDED');
  }
  need(union[FIXED.changedFile]===FIXED.oldDispatcherSha256&&Object.keys(union).length===12592,'BASE_PACKAGE_DRIFT');
  const inventory=read('PAYLOAD_INVENTORY.json');need(same(Object.keys(inventory).sort(),Object.keys(union).sort()),'PAYLOAD_INVENTORY_GAP');
  let payloadBytes=0;const payloadHashes={};
  for(const [name,old] of Object.entries(union)){
    const b=bytes(directory,'payload/'+name),h=sha256(b),expected=name===FIXED.changedFile?FIXED.dispatcherSha256:name==='app/workspace-host.mjs'?FIXED.appHostSha256:name==='app/app-runner.mjs'?FIXED.appRunnerSha256:old;
    need(h===expected&&inventory[name].sha256===h&&inventory[name].bytes===b.length&&inventory[name].baselineSha256===old,'PAYLOAD_BYTES_DRIFT');payloadBytes+=b.length;payloadHashes[name]=h;
  }
  const walk=(dir,prefix='')=>fs.readdirSync(dir,{withFileTypes:true}).flatMap(e=>{need(!e.isSymbolicLink(),'PAYLOAD_SYMLINK');return e.isDirectory()?walk(path.join(dir,e.name),prefix+e.name+'/'):[relative(prefix+e.name)];});
  need(same(walk(path.join(directory,'payload')).sort(),Object.keys(union).sort()),'PAYLOAD_EXTRA_FILE');
  const result=freeze({schema:'r16.fixed-maintenance-package-inspection.v1',authority:false,mayExecute:false,
    directory,publicConfig:pub,baseManifests:base,manifests,versions:newVersions,payloadBytes,
    payloadInventoryHash:digest(payloadHashes),metadataHash:digest({pub,base,manifests,inventory})});
  inspections.add(result);return result;
}
export function originalUnknownPins(){return [
  {projectId:'p2vox',operationId:'c434da49-055a-43dc-a3e3-695cce137909',generation:30,operationHash:'fd13e74ce69cb8ec30817ca0a48631cf3a6b6b2b08a410cc1b442df41992cc1f',status:'UNKNOWN',resultHash:null},
  {projectId:'pmog2',operationId:'d0364f8b-3a68-4ca2-a396-7953b29cee4c',generation:38,operationHash:'38f6af1386e78e5d7ccd0710077d6a3a5e753e81722dd10f11a3a2ff9bd85da1',status:'UNKNOWN',resultHash:null},
];}
export function createMaintenancePlan({packageInspection,sourcePublicConfig,statePins,approvedAt,expiresAt,releaseNotAfter,entryFreezeDigest,nativePermissionNonce}){
  need(inspections.has(packageInspection),'INDEPENDENT_PACKAGE_INSPECTION_REQUIRED');
  sourcePublic(sourcePublicConfig,approvedAt);need(same(sourcePublicConfig,packageInspection.publicConfig),'SOURCE_PUBLIC_DRIFT');
  need(integer(approvedAt)&&integer(expiresAt)&&expiresAt>approvedAt&&expiresAt-approvedAt<=300000&&integer(releaseNotAfter)&&releaseNotAfter>expiresAt,'TIME_WINDOW_INVALID');
  need(releaseNotAfter<=sourcePublicConfig.release.body.notAfter,'RELEASE_LIFETIME_EXPANDED');
  need(hash(entryFreezeDigest)&&typeof nativePermissionNonce==='string'&&/^[A-Za-z0-9_-]{16,128}$/.test(nativePermissionNonce),'NATIVE_TARGET_INCOMPLETE');
  need(statePins&&same(Object.keys(statePins).sort(),[...stateHashes,'ownerDeliveryRevision'].sort())&&stateHashes.every(k=>hash(statePins[k]))&&integer(statePins.ownerDeliveryRevision)&&statePins.ownerDeliveryRevision>0&&statePins.ownerDeliveryRevision<Number.MAX_SAFE_INTEGER,'PROTECTED_STATE_PINS_REQUIRED');
  const artifacts=packageInspection.manifests;
  const localFiles=roles.flatMap(role=>Object.entries(artifacts[role].files).map(([artifactPath,sha256])=>({role,artifactPath,sha256,
    path:(['app','native'].includes(role)?FIXED.targetDirectory:FIXED.sourceDirectory)+'/'+artifactPath})));
  const reviewedInstallation={schema:'r16.reviewed-installation.v1',releaseId:FIXED.targetReleaseId,issuedAt:approvedAt,notAfter:releaseNotAfter,artifacts,localFiles};
  const releaseBody={...clone(sourcePublicConfig.release.body),id:FIXED.targetReleaseId,issuedAt:approvedAt,notAfter:releaseNotAfter,versions:packageInspection.versions};
  const plan=freeze({schema:'r16.fixed-maintenance-plan.v1',authority:false,mayExecute:false,
    sourceReleaseId:FIXED.sourceReleaseId,targetReleaseId:FIXED.targetReleaseId,sourcePublicConfigDigest:FIXED.publicConfigDigest,grantHash:FIXED.grantHash,
    entryFreezeDigest,nativePermissionNonce,approvedAt,expiresAt,statePins:clone(statePins),statePinsHash:digest(statePins),
    packageMetadataHash:packageInspection.metadataHash,payloadInventoryHash:packageInspection.payloadInventoryHash,
    targetDirectory:FIXED.targetDirectory,sourceVersions:clone(sourcePublicConfig.versions),targetVersions:clone(packageInspection.versions),
    originalUnknown:originalUnknownPins(),businessStateDisposition:'PRESERVED_UNCHANGED_NOT_CLOSED',
    scope:'SIGN_FIXED_RELEASE_AND_INSTALL_RECOVERY_ONLY_SAME_GRANT',
    mayWriteBusinessLedger:false,maySettleUnknown:false,mayReplayUnknown:false,mayCreateGrant:false,mayReplaceTrustRoot:false,
    releaseBody,reviewedInstallation,reviewedInstallationHash:digest(reviewedInstallation),
    requiredQuiescentServices:services,expectedConfigurationRevision:statePins.ownerDeliveryRevision+1,
    rollback:'NEWER_CONFIGURATION_REVISION_WITH_PREVIOUS_SIGNED_RELEASE_PRESERVE_CURRENT_LEDGERS',
  });plans.add(plan);return freeze({plan,planHash:digest(plan)});
}
function checkedPlan(plan){
  need(plans.has(plan),'VERIFIED_PLAN_REQUIRED');
  need(plan?.schema==='r16.fixed-maintenance-plan.v1'&&plan.authority===false&&plan.mayExecute===false&&plan.sourceReleaseId===FIXED.sourceReleaseId&&plan.targetReleaseId===FIXED.targetReleaseId&&plan.sourcePublicConfigDigest===FIXED.publicConfigDigest&&plan.grantHash===FIXED.grantHash,'PLAN_SCOPE_INVALID');
  need(plan.targetDirectory===FIXED.targetDirectory&&same(plan.originalUnknown,originalUnknownPins())&&same(plan.requiredQuiescentServices,services)&&plan.statePinsHash===digest(plan.statePins),'PLAN_DRIFT');
  need(plan.mayWriteBusinessLedger===false&&plan.maySettleUnknown===false&&plan.mayReplayUnknown===false&&plan.mayCreateGrant===false&&plan.mayReplaceTrustRoot===false,'PLAN_SCOPE_EXPANDED');
  need(plan.reviewedInstallationHash===digest(plan.reviewedInstallation)&&plan.releaseBody.id===FIXED.targetReleaseId&&same(plan.releaseBody.versions,plan.targetVersions),'PLAN_DRIFT');
}
export function validateAdmission(){need(false,'NATIVE_OS_RECEIPT_ADAPTER_UNIMPLEMENTED');}
// The future production caller must obtain these exact records from a fixed,
// root-owned reader and actual OS/session checks. This isolated reader is only
// for fixture files under a private /tmp directory; it grants no OS authority.
export function inspectIsolatedNativeAdmission({directory:dir,plan,sourcePublicConfig,now=Date.now()}){
  checkedPlan(plan);
  directory(dir);need(process.geteuid()!==0&&path.resolve(dir).startsWith('/tmp/'),'ISOLATED_PRIVATE_TMP_REQUIRED');
  const nativePermission=read(dir,'native-permission.json'),protectedEvidence=read(dir,'quiescence.json'),context=read(dir,'os-context.json');
  need(context?.schema==='r16.isolated-trusted-host-context.v1'&&context.euid===0&&context.hostname==='jenn-System-Product-Name'&&context.activeUid===1000&&context.sessionActive===true&&context.sessionRemote===false&&context.fixedEntryFreezeDigest===plan.entryFreezeDigest,'TRUSTED_HOST_CONTEXT_REQUIRED');
  checkedPlan(plan);sourcePublic(sourcePublicConfig,now);need(integer(now)&&plan.approvedAt<=now&&now<plan.expiresAt,'ADMISSION_EXPIRED');
  const p=nativePermission;need(p?.schema==='r16.maintenance-native-permission.v1','NATIVE_OS_RECEIPT_REQUIRED');
  need(p.planHash===digest(plan)&&p.statePinsHash===plan.statePinsHash&&p.entryFreezeDigest===plan.entryFreezeDigest&&p.nonce===plan.nativePermissionNonce&&p.scope===plan.scope,'NATIVE_PERMISSION_TARGET_MISMATCH');
  need(integer(p.issuedAt)&&p.issuedAt>=plan.approvedAt&&p.issuedAt<=now&&integer(p.expiresAt)&&p.expiresAt<=plan.expiresAt&&now<p.expiresAt,'NATIVE_PERMISSION_EXPIRED');
  need(p.human?.uid===1000&&typeof p.human.sessionId==='string'&&/^[A-Za-z0-9_-]{1,128}$/.test(p.human.sessionId)&&typeof p.human.polkitAction==='string'&&/^[A-Za-z0-9_.-]{1,160}$/.test(p.human.polkitAction)&&p.human.interaction==='PRESENT_CONFIRMED','NATIVE_HUMAN_RECEIPT_REQUIRED');
  need(p.osEntry?.euid===0&&p.osEntry.hostname==='jenn-System-Product-Name'&&p.osEntry.entryFreezeDigest===plan.entryFreezeDigest&&hash(p.journal?.intentHash)&&hash(p.journal?.resultHash),'NATIVE_OS_RECEIPT_REQUIRED');
  const q=protectedEvidence;need(q?.schema==='r16.maintenance-quiescence.v1','NATIVE_OS_RECEIPT_REQUIRED');
  need(q.planHash===digest(plan)&&q.statePinsHash===plan.statePinsHash&&same(q.statePins,plan.statePins)&&q.sourcePublicConfigDigest===FIXED.publicConfigDigest,'QUIESCENCE_TARGET_MISMATCH');
  need(integer(q.observedAt)&&q.observedAt>=p.issuedAt&&q.observedAt<=now&&integer(q.expiresAt)&&q.expiresAt-q.observedAt<=30000&&now<q.expiresAt&&q.expiresAt<=p.expiresAt,'QUIESCENCE_EXPIRED');
  need(same(q.originalUnknown,plan.originalUnknown)&&q.businessStateDisposition===plan.businessStateDisposition&&q.openBusinessExecutions===0&&q.databaseWriterHandles===0,'BUSINESS_STATE_NOT_PRESERVED');
  need(Array.isArray(q.actors)&&q.actors.length===services.length,'QUIESCENCE_ACTORS_INCOMPLETE');
  for(const unit of services){const rows=q.actors.filter(x=>x.unit===unit),host=['r16-owner.service','r16-native.service'].includes(unit)?'jenn-System-Product-Name':'VM-0-12-ubuntu';need(rows.length===1&&rows[0].host===host&&['inactive','failed'].includes(rows[0].activeState)&&rows[0].mainPid===0&&rows[0].controlPid===0&&rows[0].cgroupEmpty===true&&rows[0].automaticStartFenced===true,'WRITER_NOT_QUIESCENT');}
  need(context.sessionId===p.human.sessionId,'NATIVE_SESSION_MISMATCH');
  const result=freeze({schema:'r16.maintenance-admission-inspection.v1',status:'OS_EVIDENCE_VALIDATED_ISOLATED_ONLY',environment:'ISOLATED_TEST',
    authority:false,mayExecute:false,planHash:digest(plan),permissionHash:digest(nativePermission),quiescenceHash:digest(protectedEvidence),
    expiresAt:Math.min(p.expiresAt,q.expiresAt),nativeEntryInstallationVerified:false});
  admissions.set(result,{planHash:digest(plan),expiresAt:result.expiresAt});return result;
}

export function describeRuntimeCapabilities(){return freeze({implemented:['fixed_package_byte_verifier','exact_plan_builder',
  'isolated_protected_os_evidence_inspector','durable_isolated_transaction_core','historical_read_only_receipt'],
  missing:['fixed_root_owned_receipt_reader_and_actual_os_session_confirmation','real_protected_state_snapshot_attestor',
    'real_service_and_automatic_restart_fence','existing_release_credential_mount_and_signer',
    'root_owned_payload_and_selector_installer','existing_owner_same_grant_configuration_delivery',
    'real_dual_host_readback_and_forward_rollback_adapter'],authority:false,mayExecute:false,
  productionAdapterStatus:'UNIMPLEMENTED',productionInstallationPerformed:false});}
export function executeMaintenanceTransaction(){need(false,'MAINTENANCE_OS_ADAPTERS_UNIMPLEMENTED');}

function directory(dir){
  need(path.isAbsolute(dir)&&path.resolve(dir)===dir,'JOURNAL_PATH_INVALID');
  let cursor='/';for(const segment of dir.split('/').filter(Boolean)){cursor=path.join(cursor,segment);const s=fs.lstatSync(cursor);need(!s.isSymbolicLink()&&s.isDirectory(),'JOURNAL_PATH_INVALID');}
  const s=fs.lstatSync(dir);need(s.uid===process.geteuid()&&(s.mode&0o7777)===0o700,'JOURNAL_MODE_INVALID');
}
function read(dir,name){try{const s=fs.lstatSync(path.join(dir,relative(name)));need(s.isFile()&&!s.isSymbolicLink()&&s.nlink===1&&s.uid===process.geteuid()&&(s.mode&0o7777)===0o600,'JOURNAL_FILE_INVALID');return JSON.parse(bytes(dir,name,32*1024*1024));}catch(e){if(e.code==='ENOENT')return null;throw e;}}
function persist(dir,name,value,fault){
  const raw=Buffer.from(canonical(value)+'\n'),target=path.join(dir,name),temp=path.join(dir,'.'+name+'.pending');
  const old=read(dir,name);if(old){need(same(old,value),'JOURNAL_CONFLICT');return;}
  const fd=fs.openSync(temp,fs.constants.O_WRONLY|fs.constants.O_CREAT|fs.constants.O_EXCL|fs.constants.O_NOFOLLOW,0o600);
  try{fs.writeFileSync(fd,raw);fs.fsyncSync(fd);}finally{fs.closeSync(fd);}
  fault('before_publish:'+name);fs.linkSync(temp,target);fs.unlinkSync(temp);
  const d=fs.openSync(dir,fs.constants.O_RDONLY|fs.constants.O_DIRECTORY);try{fs.fsyncSync(d);}finally{fs.closeSync(d);}fault('after_publish:'+name);
}
export function readMaintenanceReceipt({directory:dir,planHash}){
  directory(dir);need(hash(planHash),'PLAN_HASH_INVALID');const intent=read(dir,'intent.json'),receipt=read(dir,'receipt.json');
  if(!receipt)return null;need(intent?.planHash===planHash&&receipt.planHash===planHash&&receipt.intentHash===digest(intent),'RECEIPT_CONFLICT');
  need(receipt.schema==='r16.isolated-maintenance-receipt.v1'&&receipt.status==='ISOLATED_COMMITTED'&&receipt.authority===false&&receipt.mayExecute===false,'RECEIPT_INVALID');
  const signed=read(dir,'signed.json'),committed=read(dir,'configuration-result.json'),verified=read(dir,'readback.json');
  need(signed&&committed&&verified&&receipt.signedHash===digest(signed)&&receipt.configurationResultHash===digest(committed)&&receipt.readbackHash===digest(verified),'RECEIPT_CHAIN_INVALID');
  return freeze({...receipt,historicalReadOnly:true});
}
const adapterNames=['verifyCandidateBytes','observeQuiescence','stagePayload','readStagedPayload',
  'signFixedRelease','readConfiguration','commitConfiguration','readback'];
// Test-only execution uses an incompatible signature domain, a caller-supplied
// synthetic signing root, and a private /tmp journal. It can never issue R16.
export async function executeIsolatedMaintenanceTransaction({directory:dir,plan,admission,adapters,fixtureReleasePublicKey,now=Date.now,fault=()=>{}}){
  directory(dir);need(process.geteuid()!==0&&path.resolve(dir).startsWith('/tmp/'),'ISOLATED_PRIVATE_TMP_REQUIRED');checkedPlan(plan);
  const planHash=digest(plan),historical=readMaintenanceReceipt({directory:dir,planHash});if(historical)return historical;
  const a=admissions.get(admission);need(a?.planHash===planHash,'VALIDATED_ADMISSION_REQUIRED');
  need(adapters&&adapterNames.every(k=>typeof adapters[k]==='function'),'OS_ADAPTERS_INCOMPLETE');
  const claim=path.join(dir,'.execution-lock');
  const lock=fs.openSync(claim,fs.constants.O_RDWR|fs.constants.O_CREAT|fs.constants.O_NOFOLLOW,0o600);
  const ls=fs.fstatSync(lock);need(ls.isFile()&&ls.nlink===1&&ls.uid===process.geteuid()&&(ls.mode&0o7777)===0o600,'JOURNAL_LOCK_INVALID');
  const held=spawnSync('/usr/bin/flock',['-n','3'],{stdio:['ignore','ignore','ignore',lock],env:{PATH:'/usr/bin:/bin'}});
  if(held.status!==0){fs.closeSync(lock);need(false,'TRANSACTION_BUSY_OR_EFFECT_UNKNOWN');}
  const guard=async()=>{
    const t=now();need(integer(t)&&plan.approvedAt<=t&&t<plan.expiresAt&&t<a.expiresAt,'ADMISSION_EXPIRED');
    const q=await adapters.observeQuiescence(plan);need(q.planHash===planHash&&q.statePinsHash===plan.statePinsHash&&q.quiescenceHash===admission.quiescenceHash,'LIVE_EVIDENCE_DRIFT');
    need(now()<Math.min(plan.expiresAt,a.expiresAt),'ADMISSION_EXPIRED');
  };
  try{
    const intent={schema:'r16.isolated-maintenance-intent.v1',environment:'ISOLATED_TEST',authority:false,planHash,
      permissionHash:admission.permissionHash,statePinsHash:plan.statePinsHash,fixtureReleasePublicKey};
    const previous=read(dir,'intent.json');if(previous)need(same(previous,intent),'JOURNAL_CONFLICT');
    await guard();persist(dir,'intent.json',intent,fault);
    const content=await adapters.verifyCandidateBytes(plan);need(content.metadataHash===plan.packageMetadataHash&&content.payloadInventoryHash===plan.payloadInventoryHash,'CANDIDATE_BYTES_DRIFT');
    const payloadResult={planHash,payloadInventoryHash:plan.payloadInventoryHash},savedPayload=read(dir,'payload-result.json');
    if(savedPayload)need(same(savedPayload,payloadResult),'PAYLOAD_RESULT_CONFLICT');
    else{await guard();await adapters.stagePayload(plan);const staged=await adapters.readStagedPayload(plan);need(staged.payloadInventoryHash===plan.payloadInventoryHash,'STAGED_BYTES_DRIFT');persist(dir,'payload-result.json',payloadResult,fault);}
    const verifyStaged=async()=>{const staged=await adapters.readStagedPayload(plan);need(staged.payloadInventoryHash===plan.payloadInventoryHash,'STAGED_BYTES_DRIFT');await guard();};
    let signed=read(dir,'signed.json');
    const signingIntent={planHash,bodyHash:digest(plan.releaseBody)},savedSigningIntent=read(dir,'sign-intent.json');
    if(savedSigningIntent)need(same(savedSigningIntent,signingIntent),'SIGNER_INTENT_CONFLICT');
    const verifySigned=x=>{const body=signedBody(x,fixtureReleasePublicKey,ISOLATED_RELEASE_DOMAIN,'r16.release.v1');need(same(body,plan.releaseBody),'SIGNED_TARGET_MISMATCH');};
    if(!signed){
      need(!savedSigningIntent,'SIGNER_EFFECT_UNKNOWN');await verifyStaged();persist(dir,'sign-intent.json',signingIntent,fault);
      signed=await adapters.signFixedRelease({body:clone(plan.releaseBody),domain:ISOLATED_RELEASE_DOMAIN,planHash});verifySigned(signed);
      // Preserve a valid signature already returned even if the window expires
      // immediately afterwards. Saving known evidence grants no next action.
      persist(dir,'signed.json',signed,fault);await guard();
    }else{need(savedSigningIntent,'SIGNER_INTENT_REQUIRED');verifySigned(signed);}
    const desired={schema:'r16.isolated-maintenance-configuration.v1',planHash,release:signed,reviewedInstallationHash:plan.reviewedInstallationHash,
      nativeSelector:FIXED.targetDirectory+'/native-manifest.json',grantHash:FIXED.grantHash,revision:plan.expectedConfigurationRevision,
      sourceStatePinsHash:plan.statePinsHash,productionAuthority:false};
    let committed=read(dir,'configuration-result.json');
    const configurationIntent={planHash,desiredHash:digest(desired)},savedConfigurationIntent=read(dir,'configuration-intent.json');
    if(savedConfigurationIntent)need(same(savedConfigurationIntent,configurationIntent),'CONFIGURATION_INTENT_CONFLICT');
    if(!committed){
      await verifyStaged();const current=await adapters.readConfiguration(plan);
      if(savedConfigurationIntent){need(current.desiredHash===digest(desired)&&current.revision===plan.expectedConfigurationRevision,'CONFIGURATION_EFFECT_UNKNOWN');}
      else{
        need(current.sourceStatePinsHash===plan.statePinsHash&&current.revision===plan.statePins.ownerDeliveryRevision,'CONFIGURATION_SOURCE_DRIFT');
        persist(dir,'configuration-intent.json',configurationIntent,fault);await guard();
        await adapters.commitConfiguration(desired);const actual=await adapters.readConfiguration(plan);need(actual.desiredHash===digest(desired)&&actual.revision===plan.expectedConfigurationRevision,'CONFIGURATION_COMMIT_UNCONFIRMED');
      }
      committed={planHash,desiredHash:digest(desired),revision:plan.expectedConfigurationRevision};persist(dir,'configuration-result.json',committed,fault);
    }else need(savedConfigurationIntent&&committed.desiredHash===digest(desired)&&committed.revision===plan.expectedConfigurationRevision,'CONFIGURATION_TARGET_DRIFT');
    await verifyStaged();const current=await adapters.readConfiguration(plan);
    need(current.desiredHash===digest(desired)&&current.revision===plan.expectedConfigurationRevision,'CONFIGURATION_TARGET_DRIFT');
    const result=await adapters.readback({plan,signed,desired});
    need(result.planHash===planHash&&result.releaseHash===digest(signed)&&result.grantHash===FIXED.grantHash&&result.revision===plan.expectedConfigurationRevision&&same(result.versions,plan.targetVersions),'READBACK_TARGET_MISMATCH');
    need(result.businessStateDisposition===plan.businessStateDisposition&&same(result.originalUnknown,plan.originalUnknown)&&result.statePinsHash===plan.statePinsHash,'READBACK_LEDGER_DRIFT');
    // Readback is an assertion supplied by test adapters, never production proof.
    const readback={...result,environment:'ISOLATED_TEST',authority:false};persist(dir,'readback.json',readback,fault);await guard();
    const receipt={schema:'r16.isolated-maintenance-receipt.v1',status:'ISOLATED_COMMITTED',authority:false,mayExecute:false,
      planHash,intentHash:digest(intent),signedHash:digest(signed),configurationResultHash:digest(committed),readbackHash:digest(readback),
      productionDeploymentAccepted:false,businessLedgerWritten:false,unknownSettled:false};
    persist(dir,'receipt.json',receipt,fault);return freeze(receipt);
  }finally{fs.closeSync(lock);}
}
