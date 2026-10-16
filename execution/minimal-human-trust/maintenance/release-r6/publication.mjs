// Internal root-oneshot signing component. Native administrator admission,
// maintenance stops and dual-host installation belong to the calling bootstrap.
import fs from 'node:fs';
import path from 'node:path';
import os from 'node:os';
import {fileURLToPath} from 'node:url';
import {createPrivateKey,createPublicKey,sign,verify,createHash} from 'node:crypto';
import {spawnSync} from 'node:child_process';
import * as base from './release-publication-base.mjs';
export const {FIXED,UNIT,canonical,digest,buildPublicationArtifacts}=base;
export const ROOT_JOURNAL='/var/lib/r16-maintenance/recovery-r6';
export const ROOT_PACKAGE=ROOT_JOURNAL+'/package';
export const SOURCE_FREEZE='/etc/r16-maintenance/recovery-r6-source-freeze.json';
const DOMAIN='R16-SIGNED\0',FIXTURE_DOMAIN=base.FIXTURE_DOMAIN;
const SELF=fileURLToPath(import.meta.url),ownSources=[SELF,...['release-publication-base.mjs','maintenance-release-base.mjs'].map(n=>path.join(path.dirname(SELF),n))];
const need=(v,c)=>{if(!v)throw Object.assign(Error(c),{code:c});};
const same=(a,b)=>canonical(a)===canonical(b),hash=x=>typeof x==='string'&&/^[a-f0-9]{64}$/.test(x),clone=x=>structuredClone(x);
const sha=b=>createHash('sha256').update(b).digest('hex');
const artifactHashes=new WeakMap();
function artifactHash(a){let h=artifactHashes.get(a);if(!h){need(Object.isFrozen(a),'FROZEN_ARTIFACTS_REQUIRED');h=digest(a);artifactHashes.set(a,h);}return h;}
function freeze(x){if(x&&typeof x==='object'){Object.values(x).forEach(freeze);Object.freeze(x);}return x;}
function directory(dir,fixture=false){
  need(path.isAbsolute(dir)&&path.resolve(dir)===dir,'DIRECTORY_INVALID');let cursor='/';
  for(const n of dir.split('/').filter(Boolean)){cursor=path.join(cursor,n);const st=fs.lstatSync(cursor);need(st.isDirectory()&&!st.isSymbolicLink(),'DIRECTORY_INVALID');if(!fixture)need(st.uid===0&&!(st.mode&0o022),'DIRECTORY_UNPROTECTED');}
  const st=fs.lstatSync(dir);need(st.uid===(fixture?process.geteuid():0)&&(st.mode&0o7777)===0o700,'JOURNAL_MODE_INVALID');
}
function readFile(filename,{fixture=false,mode,limit=32*1024*1024,optional=false,linkCount=1}={}){
  const parent=path.dirname(filename);if(!fixture){let p='/';for(const n of parent.split('/').filter(Boolean)){p=path.join(p,n);const st=fs.lstatSync(p);need(st.isDirectory()&&!st.isSymbolicLink()&&st.uid===0&&!(st.mode&0o022),'SOURCE_PATH_UNPROTECTED');}}
  let fd;try{fd=fs.openSync(filename,fs.constants.O_RDONLY|fs.constants.O_NOFOLLOW);}catch(e){if(optional&&e.code==='ENOENT')return null;throw e;}
  try{const s=fs.fstatSync(fd);need(s.isFile()&&s.nlink===linkCount&&s.uid===(fixture?process.geteuid():0)&&!(s.mode&0o022)&&(!mode||(s.mode&0o7777)===mode)&&s.size<=limit,'FILE_UNPROTECTED');const b=fs.readFileSync(fd);need(b.length===s.size,'FILE_CHANGED');return b;}finally{fs.closeSync(fd);}
}
function read(dir,name,fixture){
  const file=path.join(dir,name),pending=path.join(dir,'.'+name+'.pending');let links=1;
  try{const s=fs.lstatSync(file);if(s.nlink===2){const p=fs.lstatSync(pending);need(p.isFile()&&!p.isSymbolicLink()&&p.dev===s.dev&&p.ino===s.ino&&p.nlink===2,'JOURNAL_LINK_UNCERTAIN');links=2;}}catch(e){if(e.code!=='ENOENT')throw e;}
  const b=readFile(file,{fixture,mode:0o600,optional:true,linkCount:links});return b?JSON.parse(b):null;
}
function pendingRecord(dir,name,fixture){
  const b=readFile(path.join(dir,'.'+name+'.pending'),{fixture,mode:0o600,optional:true});if(!b)return null;
  let result;try{result=JSON.parse(b);}catch{need(false,'JOURNAL_RECORD_UNCERTAIN');}
  need(b.equals(Buffer.from(canonical(result)+'\n')),'JOURNAL_RECORD_UNCERTAIN');return result;
}
function sync(dir){const fd=fs.openSync(dir,fs.constants.O_RDONLY|fs.constants.O_DIRECTORY);try{fs.fsyncSync(fd);}finally{fs.closeSync(fd);}}
function persist(dir,name,value,fixture){
  const raw=Buffer.from(canonical(value)+'\n'),pending=path.join(dir,'.'+name+'.pending'),target=path.join(dir,name);
  const old=read(dir,name,fixture);if(old){need(same(old,value),'JOURNAL_CONFLICT');
    if(fs.existsSync(pending)){const a=fs.lstatSync(target),b=fs.lstatSync(pending);need(!b.isSymbolicLink()&&a.dev===b.dev&&a.ino===b.ino&&a.nlink===2&&b.nlink===2,'JOURNAL_LINK_UNCERTAIN');fs.unlinkSync(pending);sync(dir);}return;}
  if(fs.existsSync(pending)){const prior=pendingRecord(dir,name,fixture);need(same(prior,value),'JOURNAL_CONFLICT');fs.linkSync(pending,target);sync(dir);fs.unlinkSync(pending);sync(dir);return;}
  // Unknown prefixes remain untouched; never infer a signing result from INTENT.
  const fd=fs.openSync(pending,fs.constants.O_WRONLY|fs.constants.O_CREAT|fs.constants.O_EXCL|fs.constants.O_NOFOLLOW,0o600);
  try{fs.writeFileSync(fd,raw);fs.fsyncSync(fd);}finally{fs.closeSync(fd);}
  fs.linkSync(pending,target);sync(dir);fs.unlinkSync(pending);sync(dir);
}
async function locked(dir,fixture,work){
  directory(dir,fixture);const fd=fs.openSync(path.join(dir,'.publication-lock'),fs.constants.O_RDWR|fs.constants.O_CREAT|fs.constants.O_NOFOLLOW,0o600);
  try{const st=fs.fstatSync(fd);need(st.isFile()&&st.nlink===1&&st.uid===(fixture?process.geteuid():0)&&(st.mode&0o7777)===0o600,'LOCK_INVALID');
    const r=spawnSync('/usr/bin/flock',['-n','3'],{stdio:['ignore','ignore','ignore',fd],env:{PATH:'/usr/bin:/bin'}});need(r.status===0,'PUBLICATION_BUSY');return await work();
  }finally{fs.closeSync(fd);}
}
function verifyEnvelope(e,key,domain,schema){
  need(e&&same(Object.keys(e).sort(),['body','signature'])&&e.body?.schema===schema&&typeof e.signature==='string','SIGNED_ENVELOPE_INVALID');
  let p;try{p=createPublicKey({key:Buffer.from(key,'base64url'),type:'spki',format:'der'});}catch{need(false,'SIGNATURE_INVALID');}
  const sig=Buffer.from(e.signature,'base64url');need(p.asymmetricKeyType==='ed25519'&&p.export({type:'spki',format:'der'}).toString('base64url')===key&&sig.length===64&&sig.toString('base64url')===e.signature&&verify(null,Buffer.from(domain+canonical(e.body)),p,sig),'SIGNATURE_INVALID');return e.body;
}
function actualContext(){
  need(process.getuid()===0&&process.geteuid()===0&&os.hostname()==='jenn-System-Product-Name'&&process.argv.length===2,'FIXED_ROOT_ONESHOT_REQUIRED');
  const cgroup=fs.readFileSync('/proc/self/cgroup','utf8');need(cgroup.trim().split('\n').some(x=>x.split(':').length===3&&x.split(':')[2]==='/system.slice/'+UNIT),'FIXED_SERVICE_CGROUP_REQUIRED');
}
function verifyFreeze(artifacts){
  const raw=readFile(SOURCE_FREEZE),f=JSON.parse(raw);
  need(f.schema==='r16.maintenance-source-freeze.v3'&&f.artifactsHash===digest(artifacts)&&f.files&&Object.getPrototypeOf(f.files)===Object.prototype,'SOURCE_FREEZE_INVALID');
  need(Number.isSafeInteger(f.rollbackDeadline)&&f.rollbackDeadline>=artifacts.expiresAt&&f.rollbackDeadline<=artifacts.approvedAt+1800000,'RECOVERY_WINDOW_INVALID');
  need(artifacts.freezeDigest===digest(f.files)&&ownSources.every(n=>hash(f.files[n])),'COMPLETE_SOURCE_FREEZE_REQUIRED');
  for(const [filename,expected] of Object.entries(f.files)){
    need(path.isAbsolute(filename)&&path.resolve(filename)===filename&&hash(expected),'SOURCE_FREEZE_PATH_INVALID');
    const bytes=readFile(filename);need(sha(bytes)===expected,'SOURCE_BYTES_CHANGED');
    if(filename.endsWith('.mjs')){
      const code=bytes.toString('utf8');need(!/\bimport\s*\(/.test(code),'DYNAMIC_IMPORT_NOT_FROZEN');
      for(const match of code.matchAll(/\b(?:import|export)\s[^;\n]*?\bfrom\s*['"]([^'"]+)['"]/g)){
        if(match[1].startsWith('node:'))continue;
        need(match[1].startsWith('.')&&hash(f.files[path.resolve(path.dirname(filename),match[1])]),'TRANSITIVE_SOURCE_NOT_FROZEN');
      }
    }
  }
  return {freezeHash:sha(raw),rollbackDeadline:f.rollbackDeadline};
}
function rebuild(artifacts){
  need(artifacts?.environment==='SOURCE_ONLY_NOT_APPROVED','PRODUCTION_ARTIFACTS_REQUIRED');
  readFile(path.join(ROOT_PACKAGE,'metadata/CANDIDATE.json'));
  const walk=dir=>{for(const entry of fs.readdirSync(dir,{withFileTypes:true})){const file=path.join(dir,entry.name),s=fs.lstatSync(file);need(!s.isSymbolicLink()&&s.uid===0&&!(s.mode&0o022),'PACKAGE_OWNERSHIP_INVALID');if(s.isDirectory())walk(file);else need(s.isFile()&&s.nlink===1,'PACKAGE_OWNERSHIP_INVALID');}};walk(ROOT_PACKAGE);
  const result=base.buildPublicationArtifacts({packageDirectory:ROOT_PACKAGE,sourcePublicConfig:artifacts.sourcePublicConfig,sourceProposal:artifacts.sourceProposal,
    sourceDelivery:artifacts.sourceDelivery,approvedAt:artifacts.approvedAt,expiresAt:artifacts.expiresAt,
    releaseNotAfter:artifacts.releaseBody.notAfter,freezeDigest:artifacts.freezeDigest,nonce:artifacts.nonce});
  need(same(result,artifacts),'PUBLICATION_ARTIFACTS_DRIFT');return result;
}
function readCredential(role){
  actualContext();need(['release','issuer'].includes(role),'CREDENTIAL_ROLE_INVALID');const dir='/run/credentials/'+UNIT;
  const mounts=fs.readFileSync('/proc/self/mountinfo','utf8').trim().split('\n').map(x=>x.split(' ')).filter(x=>x[4]===dir);
  need(mounts.length===1,'CREDENTIAL_MOUNT_INVALID');const m=mounts[0],sep=m.indexOf('-');need(sep>5&&m[5].split(',').includes('ro')&&['tmpfs','ramfs'].includes(m[sep+1]),'CREDENTIAL_MOUNT_INVALID');
  let mount;for(const n of ['/run','/run/credentials',dir]){const s=fs.lstatSync(n);need(s.isDirectory()&&!s.isSymbolicLink()&&s.uid===0&&!(s.mode&0o022),'CREDENTIAL_DIRECTORY_INVALID');if(n===dir)mount=s;}
  const fd=fs.openSync(dir+'/'+(role==='release'?'release-signing-key':'issuer-signing-key'),fs.constants.O_RDONLY|fs.constants.O_NOFOLLOW);
  try{const s=fs.fstatSync(fd);need(s.isFile()&&s.uid===0&&s.nlink===1&&s.dev===mount.dev&&[0o400,0o440].includes(s.mode&0o7777)&&s.size>0&&s.size<=4096,'CREDENTIAL_FILE_INVALID');const b=fs.readFileSync(fd);need(b.length===s.size,'CREDENTIAL_CHANGED');return b;}finally{fs.closeSync(fd);}
}
function signOriginal(role,body,artifacts){
  const raw=readCredential(role),expected=artifacts.sourcePublicConfig[role==='release'?'releasePublicKey':'issuerPublicKey'];
  try{const key=createPrivateKey({key:raw,type:'pkcs8',format:'der'});need(key.asymmetricKeyType==='ed25519'&&createPublicKey(key).export({type:'spki',format:'der'}).toString('base64url')===expected,'ORIGINAL_SIGNING_ROOT_MISMATCH');return {body:clone(body),signature:sign(null,Buffer.from(DOMAIN+canonical(body)),key).toString('base64url')};}finally{raw.fill(0);}
}
function optionsForProduction({artifacts,directory:dir,now}){
  need(now===Date.now,'PRODUCTION_CLOCK_OVERRIDE_REFUSED');actualContext();need(dir===ROOT_JOURNAL,'FIXED_JOURNAL_REQUIRED');
  const frozen=verifyFreeze(artifacts),rebuilt=rebuild(artifacts);need(same(frozen,verifyFreeze(rebuilt)),'SOURCE_FREEZE_DRIFT');
  return {artifacts:rebuilt,directory:dir,fixture:false,domain:DOMAIN,now,
    rollbackDeadline:frozen.rollbackDeadline,freezeHash:frozen.freezeHash,
    checkSource:()=>{actualContext();need(same(frozen,verifyFreeze(rebuilt)),'SOURCE_FREEZE_DRIFT');},
    signer:(role,body)=>signOriginal(role,body,rebuilt),afterSave:()=>{}};
}
function checkWindow(o,rollback=false){const t=o.now();need(Number.isSafeInteger(t)&&t>=o.artifacts.approvedAt&&t<(rollback?o.rollbackDeadline:o.artifacts.expiresAt),rollback?'ROLLBACK_WINDOW_EXPIRED':'PUBLICATION_WINDOW_EXPIRED');}
function validatePublication(a,result){
  const domain=a.environment==='ISOLATED_TEST'?FIXTURE_DOMAIN:DOMAIN;
  verifyEnvelope(result.release,a.sourcePublicConfig.releasePublicKey,domain,'r16.release.v1');
  need(same(result.release.body,a.releaseBody),'PUBLICATION_RESULT_DRIFT');
  const body=base.configurationBody(a,result.release);
  verifyEnvelope(result.delivery,a.sourcePublicConfig.issuerPublicKey,domain,'r16.configuration-delivery.v1');
  need(same(result.delivery.body,body),'PUBLICATION_RESULT_DRIFT');
  need(result.artifactsHash===artifactHash(a)&&result.status==='SIGNED_NOT_INSTALLED','PUBLICATION_RESULT_DRIFT');
  const expected={proposal:{...a.proposalTemplate,release:result.release},publicConfig:body.publicConfig,control:body.control,revision:body.revision,
    reviewedInstallation:a.reviewedInstallation,nativeManifest:a.reviewedInstallation.artifacts.native};
  for(const k of Object.keys(expected))need(same(expected[k],result[k]),'PUBLICATION_RESULT_DRIFT');
  need(result.businessLedgerWrites===false&&result.originalUnknownSettled===false&&result.productionInstallationPerformed===false&&result.mayExecute===false,'PUBLICATION_RESULT_DRIFT');return result;
}
async function knownPublication(o){
  const existing=read(o.directory,'publication-intent.json',o.fixture);
  need(existing?.artifactsHash===artifactHash(o.artifacts)&&existing.freezeHash===o.freezeHash&&existing.rollbackDeadline===o.rollbackDeadline,'PUBLICATION_INTENT_CONFLICT');
  let result=read(o.directory,'publication-result.json',o.fixture);
  if(result){need(result.freezeHash===o.freezeHash,'PUBLICATION_RESULT_DRIFT');validatePublication(o.artifacts,result);persist(o.directory,'publication-result.json',result,o.fixture);return result;}
  if(!(read(o.directory,'release-signature.json',o.fixture)||pendingRecord(o.directory,'release-signature.json',o.fixture))||
    !(read(o.directory,'delivery-signature.json',o.fixture)||pendingRecord(o.directory,'delivery-signature.json',o.fixture)))return null;
  // Both valid signatures are already durable. Reconstructing their result is
  // evidence recovery, permitted even after the signing window has ended.
  const release=await capture(o,'release','release',o.artifacts.releaseBody);
  const delivery=await capture(o,'delivery','issuer',base.configurationBody(o.artifacts,release));
  result={...base.assemblePublication({artifacts:o.artifacts,signedRelease:release,signedDelivery:delivery}),
    status:'SIGNED_NOT_INSTALLED',environment:o.fixture?'ISOLATED_TEST':'PROTECTED_ONESHOT',freezeHash:o.freezeHash};
  validatePublication(o.artifacts,result);persist(o.directory,'publication-result.json',result,o.fixture);return result;
}
async function capture(o,name,role,body,rollback=false){
  const key=o.artifacts.sourcePublicConfig[role==='release'?'releasePublicKey':'issuerPublicKey'];
  const target={schema:'r16.maintenance-signing-intent.v3',artifactsHash:artifactHash(o.artifacts),freezeHash:o.freezeHash,role,bodyHash:digest(body)};
  const old=read(o.directory,name+'-intent.json',o.fixture)||pendingRecord(o.directory,name+'-intent.json',o.fixture),known=read(o.directory,name+'-signature.json',o.fixture)||pendingRecord(o.directory,name+'-signature.json',o.fixture);
  if(old)need(same(old,target),'SIGNING_INTENT_CONFLICT');
  const validate=e=>{verifyEnvelope(e,key,o.domain,body.schema);need(same(e.body,body),'SIGNING_TARGET_CHANGED');};
  if(known){need(old,'SIGNING_INTENT_MISSING');validate(known);persist(o.directory,name+'-intent.json',target,o.fixture);persist(o.directory,name+'-signature.json',known,o.fixture);return known;}
  need(!old,'SIGNER_EFFECT_UNKNOWN');checkWindow(o,rollback);o.checkSource();
  persist(o.directory,name+'-intent.json',target,o.fixture);
  const signed=await o.signer(role,clone(body));validate(signed);
  // A returned valid signature is known evidence: persist before expiry checks.
  persist(o.directory,name+'-signature.json',signed,o.fixture);o.afterSave(name);checkWindow(o,rollback);o.checkSource();return signed;
}
async function publish(o){return locked(o.directory,o.fixture,async()=>{
  const intent={schema:'r16.maintenance-publication-intent.v3',artifactsHash:artifactHash(o.artifacts),freezeHash:o.freezeHash,rollbackDeadline:o.rollbackDeadline};
  const existing=read(o.directory,'publication-intent.json',o.fixture);if(existing)need(same(existing,intent),'PUBLICATION_INTENT_CONFLICT');
  const old=existing?await knownPublication(o):null;
  if(old)return freeze({...old,historicalReadOnly:true});
  checkWindow(o);o.checkSource();persist(o.directory,'publication-intent.json',intent,o.fixture);
  const release=await capture(o,'release','release',o.artifacts.releaseBody);
  const body=base.configurationBody(o.artifacts,release),delivery=await capture(o,'delivery','issuer',body);
  const result={...base.assemblePublication({artifacts:o.artifacts,signedRelease:release,signedDelivery:delivery}),
    status:'SIGNED_NOT_INSTALLED',environment:o.fixture?'ISOLATED_TEST':'PROTECTED_ONESHOT',freezeHash:o.freezeHash};
  validatePublication(o.artifacts,result);persist(o.directory,'publication-result.json',result,o.fixture);checkWindow(o);o.checkSource();return freeze(result);
});}
export async function signPublication({artifacts,directory=ROOT_JOURNAL,now=Date.now}){return publish(optionsForProduction({artifacts,directory,now}));}
async function rollback(o,currentAcceptedDelivery,issuedAt){return locked(o.directory,o.fixture,async()=>{
  const intent=read(o.directory,'publication-intent.json',o.fixture);
  need(intent?.artifactsHash===artifactHash(o.artifacts)&&intent.freezeHash===o.freezeHash&&intent.rollbackDeadline===o.rollbackDeadline,'ORIGINAL_PUBLICATION_REQUIRED');
  const publication=await knownPublication(o);need(publication,'ORIGINAL_PUBLICATION_REQUIRED');const publicationHash=digest(publication);
  const key=o.artifacts.sourcePublicConfig.issuerPublicKey;
  const current=verifyEnvelope(currentAcceptedDelivery,key,o.domain,'r16.configuration-delivery.v1');
  need(same(Object.keys(current).sort(),['control','issuedAt','publicConfig','revision','schema'])&&same(current.control,o.artifacts.sourceDelivery.body.control),'ROLLBACK_ACCEPTED_SCOPE_CHANGED');
  need(same(current.publicConfig,o.artifacts.sourcePublicConfig)||same(current.publicConfig,publication.publicConfig),'ROLLBACK_ACCEPTED_SCOPE_CHANGED');
  const prior=read(o.directory,'rollback-intent.json',o.fixture),savedResult=read(o.directory,'rollback-result.json',o.fixture);
  const validateRollback=(result)=>{
    verifyEnvelope(result.delivery,key,o.domain,'r16.configuration-delivery.v1');
    need(prior?.schema==='r16.maintenance-rollback-intent.v3'&&prior.artifactsHash===artifactHash(o.artifacts)&&prior.publicationHash===publicationHash&&prior.bodyHash===digest(result.delivery.body),'ROLLBACK_RESULT_CONFLICT');
    need(Number.isSafeInteger(prior.acceptedRevision)&&prior.acceptedRevision>=base.SOURCE_REVISION&&result.delivery.body.revision===Math.max(prior.acceptedRevision,publication.revision)+1&&result.delivery.body.issuedAt===prior.issuedAt,'ROLLBACK_RESULT_CONFLICT');
    need(result.artifactsHash===artifactHash(o.artifacts)&&result.publicationHash===publicationHash&&result.acceptedHash===prior.acceptedHash&&same(result.delivery.body.publicConfig,o.artifacts.sourcePublicConfig)&&same(result.delivery.body.control,o.artifacts.sourceDelivery.body.control)&&result.restoreHistoricalLedgerSnapshot===false&&result.preserveCurrentLedgers===true,'ROLLBACK_RESULT_CONFLICT');
    need(result.acceptedHash===digest(currentAcceptedDelivery)||same(result.delivery,currentAcceptedDelivery),'ROLLBACK_ACCEPTED_CHANGED');return result;
  };
  if(savedResult){validateRollback(savedResult);persist(o.directory,'rollback-result.json',savedResult,o.fixture);return freeze({...savedResult,historicalReadOnly:true});}
  const makeResult=delivery=>({schema:'r16.maintenance-rollback-result.v3',status:'SIGNED_ROLLBACK_NOT_INSTALLED',environment:o.fixture?'ISOLATED_TEST':'PROTECTED_ONESHOT',
    artifactsHash:artifactHash(o.artifacts),publicationHash:publicationHash,acceptedHash:prior?prior.acceptedHash:digest(currentAcceptedDelivery),delivery,
    preserveCurrentLedgers:true,restoreHistoricalLedgerSnapshot:false,authority:false,mayExecute:false});
  const durableSignature=read(o.directory,'rollback-delivery-signature.json',o.fixture)||pendingRecord(o.directory,'rollback-delivery-signature.json',o.fixture);
  if(durableSignature){const result=validateRollback(makeResult(durableSignature));persist(o.directory,'rollback-delivery-signature.json',durableSignature,o.fixture);persist(o.directory,'rollback-result.json',result,o.fixture);return freeze({...result,historicalReadOnly:true});}
  checkWindow(o,true);o.checkSource();
  need(Number.isSafeInteger(current.revision)&&current.revision>=base.SOURCE_REVISION&&current.revision<Number.MAX_SAFE_INTEGER&&Number.isSafeInteger(current.issuedAt)&&current.issuedAt<=o.now(),'ROLLBACK_ACCEPTED_REVISION_INVALID');
  need(Number.isSafeInteger(issuedAt)&&issuedAt>=current.issuedAt&&issuedAt<=o.now()&&o.now()-issuedAt<=30000&&issuedAt<o.artifacts.sourcePublicConfig.release.body.notAfter,'ROLLBACK_TIME_INVALID');
  const revision=Math.max(current.revision,publication.revision)+1;need(Number.isSafeInteger(revision),'ROLLBACK_REVISION_OVERFLOW');
  const body={...clone(o.artifacts.sourceDelivery.body),revision,issuedAt};
  const target={schema:'r16.maintenance-rollback-intent.v3',artifactsHash:artifactHash(o.artifacts),publicationHash:publicationHash,acceptedHash:digest(currentAcceptedDelivery),acceptedRevision:current.revision,bodyHash:digest(body),issuedAt};
  if(prior)need(same(prior,target),'ROLLBACK_INTENT_CONFLICT');else persist(o.directory,'rollback-intent.json',target,o.fixture);
  const delivery=await capture(o,'rollback-delivery','issuer',body,true);
  const result=makeResult(delivery);
  persist(o.directory,'rollback-result.json',result,o.fixture);checkWindow(o,true);o.checkSource();return freeze(result);
});}
export async function signRollbackDelivery({artifacts,currentAcceptedDelivery,directory=ROOT_JOURNAL,issuedAt,now=Date.now}){
  return rollback(optionsForProduction({artifacts,directory,now}),currentAcceptedDelivery,issuedAt);
}

// Test factory is nonroot-only and cannot produce signatures in R15's domain.
export function createIsolatedSigner({harness,artifacts,directory:dir,rollbackDeadline,now=Date.now,signer,afterSave=()=>{}}){
  need(process.geteuid()!==0&&artifacts?.environment==='ISOLATED_TEST'&&dir.startsWith('/tmp/'),'ISOLATED_NONROOT_REQUIRED');directory(dir,true);
  need(Number.isSafeInteger(rollbackDeadline)&&rollbackDeadline>=artifacts.expiresAt&&rollbackDeadline<=artifacts.approvedAt+1800000,'RECOVERY_WINDOW_INVALID');
  const o={artifacts,directory:dir,fixture:true,domain:FIXTURE_DOMAIN,now,rollbackDeadline,freezeHash:digest('isolated-source-freeze'),checkSource:()=>{},afterSave,
    signer:signer||((role,body)=>harness.sign({role,body}))};
  return Object.freeze({signPublication:()=>publish(o),signRollbackDelivery:({currentAcceptedDelivery,issuedAt})=>rollback(o,currentAcceptedDelivery,issuedAt),
    readKnownSignatures:()=>({release:read(dir,'release-signature.json',true),delivery:read(dir,'delivery-signature.json',true),rollback:read(dir,'rollback-delivery-signature.json',true)})});
}
export {createIsolatedPublicationHarness} from './release-publication-base.mjs';
