// Existing-root publication adapter SOURCE ONLY. No CLI, installed bootstrap,
// native authorization reader, production key access or production activation.
import fs from 'node:fs';
import path from 'node:path';
import os from 'node:os';
import {createPrivateKey,createPublicKey,generateKeyPairSync,sign,verify} from 'node:crypto';
import {spawnSync} from 'node:child_process';
import {FIXED,canonical,digest,inspectPhysicalPackage} from './maintenance-release-base.mjs';
export {FIXED,canonical,digest};
export const UNIT='r16-native-recovery-maintenance-r6.service';
export const SOURCE_REVISION=16;
export const SOURCE_DELIVERY_HASH='5ee11707da0d3a524550db92f8c0a5a80b7a8dac8c97f5a907b47fc956c6ec44';
export const FIXTURE_DOMAIN='R16-PUBLICATION-ISOLATED-NOT-A-RELEASE\0';
const PRODUCTION_DOMAIN='R16-SIGNED\0';
const need=(v,code)=>{if(!v)throw Object.assign(Error(code),{code});};
const same=(a,b)=>canonical(a)===canonical(b),hash=v=>typeof v==='string'&&/^[a-f0-9]{64}$/.test(v);
const clone=x=>structuredClone(x),bindings=new WeakMap();
const roles=['app','bridge','native'];
function freeze(x){if(x&&typeof x==='object'){Object.values(x).forEach(freeze);Object.freeze(x);}return x;}
function pub(key){return createPublicKey(key).export({format:'der',type:'spki'}).toString('base64url');}
function decodePublic(key){let p;try{p=createPublicKey({key:Buffer.from(key,'base64url'),format:'der',type:'spki'});}catch{need(false,'PUBLIC_KEY_INVALID');}need(p.asymmetricKeyType==='ed25519'&&p.export({format:'der',type:'spki'}).toString('base64url')===key,'PUBLIC_KEY_INVALID');return p;}
function verifyEnvelope(envelope,key,domain,schema){
  need(envelope&&same(Object.keys(envelope).sort(),['body','signature'])&&envelope.body?.schema===schema&&typeof envelope.signature==='string','ENVELOPE_INVALID');
  const b=Buffer.from(envelope.signature,'base64url');need(b.length===64&&b.toString('base64url')===envelope.signature&&verify(null,Buffer.from(domain+canonical(envelope.body)),decodePublic(key),b),'SIGNATURE_INVALID');return envelope.body;
}
function validateSource({sourcePublicConfig:p,sourceProposal:s,sourceDelivery:d,inspection,profile,approvedAt}){
  need(digest(p)===profile.publicHash&&digest(p.grant)===profile.grantHash,'SOURCE_PUBLIC_DRIFT');
  need(p.releasePublicKey!==p.issuerPublicKey,'SIGNING_ROLES_NOT_SEPARATE');
  const g=verifyEnvelope(p.grant,p.issuerPublicKey,profile.domain,'r16.workspace.v1');
  const r=verifyEnvelope(p.release,p.releasePublicKey,profile.domain,'r16.release.v1');
  need(g.id==='r16-projects-daily'&&g.version===1&&r.id===FIXED.sourceReleaseId&&r.issuedAt<=approvedAt&&approvedAt<r.notAfter,'SOURCE_BINDING_INVALID');
  need(s?.schema==='r16.owner-installation.v1'&&s.grantId===g.id&&s.workspace===g.workspace.root&&s.workspaceId===g.workspace.id&&s.channel===g.channel,'SOURCE_PROPOSAL_INVALID');
  for(const k of ['release','versions','peers','issuerPublicKey','releasePublicKey'])need(same(s[k],p[k]),'SOURCE_PROPOSAL_DRIFT');
  need(same(s.artifacts,inspection.baseManifests)&&hash(s.reviewedManifestHash),'SOURCE_MANIFEST_DRIFT');
  const expected=roles.flatMap(role=>Object.entries(s.artifacts[role].files).map(([artifactPath,sha256])=>({artifactPath,path:FIXED.sourceDirectory+'/'+artifactPath,role,sha256})));
  need(same([...s.localFiles].sort((a,b)=>canonical(a).localeCompare(canonical(b))),expected.sort((a,b)=>canonical(a).localeCompare(canonical(b)))),'SOURCE_LOCAL_BINDINGS_INCOMPLETE');
  const b=verifyEnvelope(d,p.issuerPublicKey,profile.domain,'r16.configuration-delivery.v1');
  if(!profile.fixture)need(digest(d)===SOURCE_DELIVERY_HASH,'SOURCE_DELIVERY_HASH_DRIFT');
  need(same(Object.keys(b).sort(),['control','issuedAt','publicConfig','revision','schema'])&&b.revision===SOURCE_REVISION&&Number.isSafeInteger(b.issuedAt)&&b.issuedAt<=approvedAt,'SOURCE_REVISION_DRIFT');
  need(same(b.publicConfig,p)&&same(b.control,{grantId:g.id,grantVersion:1,status:'ACTIVE',connectRequested:true}),'SOURCE_DELIVERY_DRIFT');
  need(same(p.versions,{app:FIXED.sourceAppVersion,bridge:FIXED.bridgeVersion,native:FIXED.oldNativeVersion}),'SOURCE_ROLE_DRIFT');
  return {grant:g,release:r};
}
function build({inspection,sourcePublicConfig,sourceProposal,sourceDelivery,approvedAt,expiresAt,releaseNotAfter,freezeDigest,nonce},profile){
  need(Number.isSafeInteger(approvedAt)&&Number.isSafeInteger(expiresAt)&&approvedAt<expiresAt&&expiresAt-approvedAt<=300000&&Number.isSafeInteger(releaseNotAfter)&&releaseNotAfter>expiresAt,'WINDOW_INVALID');
  need(hash(freezeDigest)&&typeof nonce==='string'&&/^[A-Za-z0-9_-]{16,128}$/.test(nonce),'EXACT_TARGET_REQUIRED');
  const {release}=validateSource({sourcePublicConfig,sourceProposal,sourceDelivery,inspection,profile,approvedAt});
  need(releaseNotAfter<=release.notAfter,'RELEASE_LIFETIME_EXPANDED');
  const targetVersions={app:FIXED.targetAppVersion,bridge:FIXED.bridgeVersion,native:FIXED.nativeVersion};
  need(same(inspection.versions,targetVersions)&&inspection.payloadBytes===149502002,'FIXED_PAYLOAD_DRIFT');
  const artifacts=clone(inspection.manifests),localFiles=sourceProposal.localFiles.map(row=>['app','native'].includes(row.role)
    ?{...row,path:FIXED.targetDirectory+'/'+row.artifactPath,sha256:artifacts[row.role].files[row.artifactPath]}:clone(row));
  const reviewedInstallation={schema:'r16.reviewed-installation.v1',releaseId:FIXED.targetReleaseId,issuedAt:approvedAt,notAfter:releaseNotAfter,artifacts,localFiles};
  const releaseBody={...clone(sourcePublicConfig.release.body),id:FIXED.targetReleaseId,issuedAt:approvedAt,notAfter:releaseNotAfter,versions:targetVersions};
  const proposalTemplate={...clone(sourceProposal),release:null,versions:targetVersions,artifacts,localFiles,reviewedManifestHash:digest(reviewedInstallation)};
  const result=freeze({schema:'r16.maintenance-publication-artifacts.v2',environment:profile.fixture?'ISOLATED_TEST':'SOURCE_ONLY_NOT_APPROVED',
    authority:false,mayExecute:false,sourcePublicConfig:clone(sourcePublicConfig),sourceProposal:clone(sourceProposal),sourceDelivery:clone(sourceDelivery),
    sourcePublicConfigHash:profile.publicHash,sourceGrantHash:profile.grantHash,sourceDeliveryHash:digest(sourceDelivery),
    payloadInventoryHash:inspection.payloadInventoryHash,packageMetadataHash:inspection.metadataHash,
    payloadUniqueFiles:12592,roleBindings:16591,approvedAt,expiresAt,freezeDigest,nonce,
    reviewedInstallation,reviewedInstallationHash:digest(reviewedInstallation),releaseBody,proposalTemplate,
    nextRevision:SOURCE_REVISION+1,originalUnknownDisposition:'PRESERVE_ALL_BUSINESS_LEDGERS_AND_UNKNOWN_UNCHANGED',
    mayCreateGrant:false,maySettleUnknown:false,mayReplaceRoot:false});
  bindings.set(result,profile);return result;
}
export function buildPublicationArtifacts(args){
  const inspection=inspectPhysicalPackage({directory:args.packageDirectory||FIXED.packageDirectory,now:args.approvedAt});
  return build({...args,inspection},{domain:PRODUCTION_DOMAIN,publicHash:FIXED.publicConfigDigest,grantHash:FIXED.grantHash,fixture:false});
}
function profileFor(a){const p=bindings.get(a);need(p,'VERIFIED_ARTIFACTS_REQUIRED');return p;}
export function configurationBody(artifacts,signedRelease){
  const p=profileFor(artifacts);verifyEnvelope(signedRelease,artifacts.sourcePublicConfig.releasePublicKey,p.domain,'r16.release.v1');
  need(same(signedRelease.body,artifacts.releaseBody),'RELEASE_TARGET_DRIFT');
  return freeze({...clone(artifacts.sourceDelivery.body),revision:artifacts.nextRevision,issuedAt:artifacts.approvedAt,
    publicConfig:{...clone(artifacts.sourcePublicConfig),release:clone(signedRelease),versions:clone(artifacts.releaseBody.versions)}});
}
export function assemblePublication({artifacts,signedRelease,signedDelivery}){
  const p=profileFor(artifacts),body=configurationBody(artifacts,signedRelease);
  verifyEnvelope(signedDelivery,artifacts.sourcePublicConfig.issuerPublicKey,p.domain,'r16.configuration-delivery.v1');
  need(same(signedDelivery.body,body),'CONFIGURATION_TARGET_DRIFT');
  const proposal={...clone(artifacts.proposalTemplate),release:clone(signedRelease)};
  return freeze({schema:'r16.maintenance-publication-result.v2',environment:artifacts.environment,authority:false,mayExecute:false,
    artifactsHash:digest(artifacts),release:clone(signedRelease),delivery:clone(signedDelivery),proposal,
    reviewedInstallation:clone(artifacts.reviewedInstallation),nativeManifest:clone(artifacts.reviewedInstallation.artifacts.native),
    publicConfig:clone(body.publicConfig),control:clone(body.control),revision:body.revision,
    businessLedgerWrites:false,originalUnknownSettled:false,productionInstallationPerformed:false});
}
export function buildForwardRollback({artifacts,currentAcceptedDelivery,issuedAt}){
  const p=profileFor(artifacts),key=artifacts.sourcePublicConfig.issuerPublicKey;
  const b=verifyEnvelope(currentAcceptedDelivery,key,p.domain,'r16.configuration-delivery.v1');
  need(same(Object.keys(b).sort(),['control','issuedAt','publicConfig','revision','schema']),'ROLLBACK_SOURCE_DRIFT');
  const expected=configurationBody(artifacts,b.publicConfig.release);
  need(same(b.publicConfig,expected.publicConfig)&&same(b.control,artifacts.sourceDelivery.body.control),'ROLLBACK_SOURCE_DRIFT');
  need(Number.isSafeInteger(b.revision)&&b.revision>=artifacts.nextRevision&&b.revision<Number.MAX_SAFE_INTEGER&&Number.isSafeInteger(issuedAt)&&issuedAt>=b.issuedAt,'ROLLBACK_REVISION_INVALID');
  need(issuedAt<artifacts.sourcePublicConfig.release.body.notAfter,'ROLLBACK_RELEASE_EXPIRED');
  return freeze({schema:'r16.maintenance-forward-rollback-artifacts.v2',authority:false,mayExecute:false,
    environment:artifacts.environment,currentAcceptedHash:digest(currentAcceptedDelivery),
    deliveryBody:{...clone(artifacts.sourceDelivery.body),revision:b.revision+1,issuedAt},
    nativeManifest:clone(artifacts.sourceProposal.artifacts.native),sourceProposal:clone(artifacts.sourceProposal),
    preserveCurrentLedgers:true,restoreHistoricalLedgerSnapshot:false,requiresFreshExactNativeAdministratorConfirmation:true});
}

// Fixed original credential sources, no environment directory, caller path,
// alternate service, private key fallback or generic root command interface.
const credentialNames={release:'release-signing-key',issuer:'issuer-signing-key'};
function inspectContext(context){
  need(context.uid===0&&context.euid===0&&context.hostname==='jenn-System-Product-Name'&&context.argvLength===2,'FIXED_SERVICE_CONTEXT_REQUIRED');
  need(context.cgroup.trim().split('\n').some(l=>l.split(':').length===3&&l.split(':')[2]==='/system.slice/'+UNIT),'FIXED_SERVICE_CGROUP_REQUIRED');
}
function readCredential(role,io,context){
  need(Object.hasOwn(credentialNames,role),'CREDENTIAL_ROLE_INVALID');inspectContext(context);
  const directory='/run/credentials/'+UNIT;
  const rows=io.readFileSync('/proc/self/mountinfo','utf8').trim().split('\n').map(x=>x.split(' ')).filter(x=>x[4]===directory);
  need(rows.length===1,'CREDENTIAL_MOUNT_INVALID');const m=rows[0],split=m.indexOf('-');
  need(split>5&&m[5].split(',').includes('ro')&&['tmpfs','ramfs'].includes(m[split+1]),'CREDENTIAL_MOUNT_INVALID');
  let root;for(const p of ['/run','/run/credentials',directory]){const s=io.lstatSync(p);need(s.isDirectory()&&!s.isSymbolicLink()&&s.uid===0&&!(s.mode&0o022),'CREDENTIAL_PATH_INVALID');if(p===directory)root=s;}
  const fd=io.openSync(directory+'/'+credentialNames[role],fs.constants.O_RDONLY|fs.constants.O_NOFOLLOW);
  try{const s=io.fstatSync(fd);need(s.isFile()&&s.uid===0&&[0o400,0o440].includes(s.mode&0o7777)&&s.nlink===1&&s.dev===root.dev&&s.size>0&&s.size<=4096,'CREDENTIAL_FILE_INVALID');const b=io.readFileSync(fd);need(Buffer.isBuffer(b)&&b.length===s.size,'CREDENTIAL_CHANGED');return b;}finally{io.closeSync(fd);}
}
function actualFixedCredential(role){
  const context={uid:process.getuid(),euid:process.geteuid(),hostname:os.hostname(),argvLength:process.argv.length,
    cgroup:fs.readFileSync('/proc/self/cgroup','utf8')};return readCredential(role,fs,context);
}
function signOriginalRootBody(artifacts,role,signedRelease){
  const profile=profileFor(artifacts);need(!profile.fixture&&Object.hasOwn(credentialNames,role),'PRODUCTION_ARTIFACTS_REQUIRED');
  const body=role==='release'?artifacts.releaseBody:configurationBody(artifacts,signedRelease);
  const expected=artifacts.sourcePublicConfig[role==='release'?'releasePublicKey':'issuerPublicKey'];
  const raw=actualFixedCredential(role);
  try{
    const key=createPrivateKey({key:raw,format:'der',type:'pkcs8'});
    need(key.asymmetricKeyType==='ed25519'&&pub(key)===expected,'ORIGINAL_CREDENTIAL_ROOT_MISMATCH');
    const result={body:clone(body),signature:sign(null,Buffer.from(PRODUCTION_DOMAIN+canonical(body)),key).toString('base64url')};
    verifyEnvelope(result,expected,PRODUCTION_DOMAIN,body.schema);return result;
  }finally{raw.fill(0);}
}
// Retain concrete production loader source for the future reviewed bootstrap.
// No exported path invokes it while the actual protected entry is absent.
void signOriginalRootBody;
export function runProtectedPublication(){need(false,'PROTECTED_NATIVE_BOOTSTRAP_NOT_IMPLEMENTED');}
export function capabilities(){return freeze({authority:false,mayExecute:false,installed:false,
  implemented:['fixed_publication_and_forward_rollback_artifacts','separate_existing_release_and_issuer_signature_validation','fixed_systemd_credential_reader_source','durable_known_signature_capture'],
  missing:['reviewed_root_owned_bootstrap_and_complete_source_freeze','actual_native_administrator_receipt_reader','real_same_epoch_quiescence_adapter','credential_mount_unit_installation','root_proposal_and_cloud_configuration_commit_adapter'],
  newAuthorizationRootRequired:false,newGrantRequired:false,newHumanEnrollmentRequired:false});}
export const MAINTENANCE_UNIT_SOURCE=`[Unit]\nDescription=Fixed same-Grant Native recovery maintenance (SOURCE ONLY, NOT INSTALLED)\n[Service]\nType=oneshot\nUser=root\nGroup=root\nExecStart=/usr/libexec/r16-native-recovery-maintenance\nLoadCredentialEncrypted=release-signing-key:/etc/credstore.encrypted/r16-release/release-signing-key.cred\nLoadCredentialEncrypted=issuer-signing-key:/etc/credstore.encrypted/r16-issuer/issuer-signing-key.cred\nUMask=0077\nRestart=no\nLimitCORE=0\nNoNewPrivileges=yes\nProtectSystem=strict\nProtectHome=read-only\nPrivateTmp=yes\nPrivateDevices=yes\nRestrictAddressFamilies=AF_UNIX\n`;

function journalDirectory(directory){
  need(process.geteuid()!==0&&path.isAbsolute(directory)&&path.resolve(directory)===directory&&directory.startsWith('/tmp/'),'ISOLATED_PRIVATE_JOURNAL_REQUIRED');
  let cursor='/';for(const part of directory.split('/').filter(Boolean)){cursor=path.join(cursor,part);const s=fs.lstatSync(cursor);need(s.isDirectory()&&!s.isSymbolicLink(),'JOURNAL_PATH_INVALID');}
  const s=fs.lstatSync(directory);need(s.uid===process.geteuid()&&(s.mode&0o7777)===0o700,'JOURNAL_MODE_INVALID');
}
function saved(directory,name){
  let fd;try{fd=fs.openSync(path.join(directory,name),fs.constants.O_RDONLY|fs.constants.O_NOFOLLOW);}catch(e){if(e.code==='ENOENT')return null;throw e;}
  try{const s=fs.fstatSync(fd);need(s.isFile()&&s.uid===process.geteuid()&&s.nlink===1&&(s.mode&0o7777)===0o600&&s.size<32*1024*1024,'JOURNAL_FILE_INVALID');return JSON.parse(fs.readFileSync(fd,'utf8'));}finally{fs.closeSync(fd);}
}
function durable(directory,name,value){
  const old=saved(directory,name);if(old){need(same(old,value),'PUBLICATION_JOURNAL_CONFLICT');return;}
  const temp=path.join(directory,'.'+name+'.pending'),target=path.join(directory,name);
  const fd=fs.openSync(temp,fs.constants.O_WRONLY|fs.constants.O_CREAT|fs.constants.O_EXCL|fs.constants.O_NOFOLLOW,0o600);
  try{fs.writeFileSync(fd,canonical(value)+'\n');fs.fsyncSync(fd);}finally{fs.closeSync(fd);}
  fs.linkSync(temp,target);fs.unlinkSync(temp);const d=fs.openSync(directory,fs.constants.O_RDONLY|fs.constants.O_DIRECTORY);try{fs.fsyncSync(d);}finally{fs.closeSync(d);}
}
export async function executeIsolatedPublication({directory,artifacts,signRelease,signDelivery,now=Date.now}){
  journalDirectory(directory);const profile=profileFor(artifacts);need(profile.fixture&&profile.domain===FIXTURE_DOMAIN,'ISOLATED_ARTIFACTS_REQUIRED');
  const lock=fs.openSync(path.join(directory,'.lock'),fs.constants.O_RDWR|fs.constants.O_CREAT|fs.constants.O_NOFOLLOW,0o600);
  try{
    const st=fs.fstatSync(lock);need(st.isFile()&&st.nlink===1&&st.uid===process.geteuid()&&(st.mode&0o7777)===0o600,'JOURNAL_LOCK_INVALID');
    const acquired=spawnSync('/usr/bin/flock',['-n','3'],{stdio:['ignore','ignore','ignore',lock],env:{PATH:'/usr/bin:/bin'}});need(acquired.status===0,'PUBLICATION_BUSY');
    const check=()=>{need(Number.isSafeInteger(now())&&artifacts.approvedAt<=now()&&now()<artifacts.expiresAt,'PUBLICATION_WINDOW_EXPIRED');};
    const binding=digest(artifacts),intent={schema:'r16.isolated-publication-intent.v2',binding,environment:'ISOLATED_TEST',authority:false};
    const existing=saved(directory,'intent.json');if(existing)need(same(existing,intent),'PUBLICATION_JOURNAL_CONFLICT');
    check();durable(directory,'intent.json',intent);
    const signing=async(role,body,key,callback)=>{
      const resultName=role+'-result.json',intentName=role+'-intent.json',target={binding,bodyHash:digest(body),role};
      let result=saved(directory,resultName);const oldIntent=saved(directory,intentName);
      if(oldIntent)need(same(oldIntent,target),'SIGNING_INTENT_CONFLICT');
      const validate=x=>{verifyEnvelope(x,key,FIXTURE_DOMAIN,body.schema);need(same(x.body,body),'SIGNED_TARGET_DRIFT');};
      if(result){need(oldIntent,'SIGNING_INTENT_MISSING');validate(result);return result;}
      need(!oldIntent,'SIGNER_EFFECT_UNKNOWN');check();durable(directory,intentName,target);
      result=await callback({body:clone(body),domain:FIXTURE_DOMAIN,role});validate(result);
      // A valid known signature is evidence already obtained, not a new effect.
      // Save it before any subsequent deadline or live-state check can refuse.
      durable(directory,resultName,result);check();return result;
    };
    const release=await signing('release',artifacts.releaseBody,artifacts.sourcePublicConfig.releasePublicKey,signRelease);
    const deliveryBody=configurationBody(artifacts,release);
    const delivery=await signing('issuer',deliveryBody,artifacts.sourcePublicConfig.issuerPublicKey,signDelivery);
    const result=assemblePublication({artifacts,signedRelease:release,signedDelivery:delivery});check();
    durable(directory,'result.json',result);return result;
  }finally{fs.closeSync(lock);}
}
export function readIsolatedPublication({directory,artifacts}){
  journalDirectory(directory);const p=profileFor(artifacts);need(p.fixture,'ISOLATED_ARTIFACTS_REQUIRED');
  const intent=saved(directory,'intent.json');need(intent?.binding===digest(artifacts),'PUBLICATION_JOURNAL_CONFLICT');
  const release=saved(directory,'release-result.json'),delivery=saved(directory,'issuer-result.json');
  if(release){verifyEnvelope(release,artifacts.sourcePublicConfig.releasePublicKey,FIXTURE_DOMAIN,'r16.release.v1');need(same(release.body,artifacts.releaseBody),'SIGNED_TARGET_DRIFT');}
  if(delivery)assemblePublication({artifacts,signedRelease:release,signedDelivery:delivery});
  return freeze({environment:'ISOLATED_TEST',authority:false,mayExecute:false,historicalReadOnly:true,
    releaseKnown:!!release,configurationKnown:!!delivery,release,delivery});
}

// Synthetic roots are created only inside this isolated harness, are never
// registered, and every signature uses the incompatible fixture domain.
export function createIsolatedPublicationHarness({inspection=inspectPhysicalPackage(),now=Date.now()}={}){
  need(process.geteuid()!==0,'ISOLATED_NONROOT_REQUIRED');
  const releaseKey=generateKeyPairSync('ed25519').privateKey,issuerKey=generateKeyPairSync('ed25519').privateKey;
  const envelope=(body,key)=>({body:clone(body),signature:sign(null,Buffer.from(FIXTURE_DOMAIN+canonical(body)),key).toString('base64url')});
  const sourcePublicConfig=clone(inspection.publicConfig);sourcePublicConfig.releasePublicKey=pub(releaseKey);sourcePublicConfig.issuerPublicKey=pub(issuerKey);
  sourcePublicConfig.grant=envelope(sourcePublicConfig.grant.body,issuerKey);sourcePublicConfig.release=envelope(sourcePublicConfig.release.body,releaseKey);
  const g=sourcePublicConfig.grant.body,localFiles=roles.flatMap(role=>Object.entries(inspection.baseManifests[role].files).map(([artifactPath,sha256])=>({artifactPath,path:FIXED.sourceDirectory+'/'+artifactPath,role,sha256})));
  const reviewed={schema:'r16.reviewed-installation.v1',releaseId:FIXED.sourceReleaseId,issuedAt:sourcePublicConfig.release.body.issuedAt,notAfter:sourcePublicConfig.release.body.notAfter,artifacts:inspection.baseManifests,localFiles};
  const sourceProposal={schema:'r16.owner-installation.v1',workspace:g.workspace.root,workspaceId:g.workspace.id,channel:g.channel,grantId:g.id,
    issuerPublicKey:sourcePublicConfig.issuerPublicKey,peers:g.peers,releasePublicKey:sourcePublicConfig.releasePublicKey,release:sourcePublicConfig.release,
    versions:sourcePublicConfig.versions,artifacts:inspection.baseManifests,localFiles,reviewedManifestHash:digest(reviewed)};
  const sourceDelivery=envelope({schema:'r16.configuration-delivery.v1',revision:SOURCE_REVISION,issuedAt:now-1000,publicConfig:sourcePublicConfig,control:{grantId:g.id,grantVersion:1,status:'ACTIVE',connectRequested:true}},issuerKey);
  const profile={fixture:true,domain:FIXTURE_DOMAIN,publicHash:digest(sourcePublicConfig),grantHash:digest(sourcePublicConfig.grant)};
  return Object.freeze({sourcePublicConfig,sourceProposal,sourceDelivery,
    build:args=>build({inspection,sourcePublicConfig,sourceProposal,sourceDelivery,...args},profile),
    sign:({body,role})=>{need(Object.hasOwn(credentialNames,role),'CREDENTIAL_ROLE_INVALID');return envelope(body,role==='release'?releaseKey:issuerKey);},
    inspectCredential:({role,io,context,expectedPublicKey})=>{need(io&&io!==fs,'FIXTURE_IO_REQUIRED');const b=readCredential(role,io,context);try{const k=createPrivateKey({key:b,format:'der',type:'pkcs8'});need(k.asymmetricKeyType==='ed25519','FIXTURE_KEY_INVALID');need(pub(k)===expectedPublicKey,'ORIGINAL_CREDENTIAL_ROOT_MISMATCH');return {environment:'ISOLATED_TEST',authority:false,mayExecute:false,publicKey:pub(k)};}finally{b.fill(0);}},
  });
}
