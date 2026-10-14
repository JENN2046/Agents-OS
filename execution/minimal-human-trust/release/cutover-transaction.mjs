// Internal cutover publication only. No CLI, privilege escalation, service
// management or signing key access. The installed caller supplies exact native
// admission and fresh guard callbacks; this module never invents authority.
import fs from 'node:fs';
import path from 'node:path';
import {createHash,randomUUID} from 'node:crypto';
import {spawnSync} from 'node:child_process';
import {canonical,digest} from '../src/lease-core.mjs';

const MAX_FILE=16*1024*1024,MAX_JOURNAL=64*1024*1024;
const REQUIRED=['issuerState','replayState','stageRootsArchive','roots','issuerConfig','receipt'];
const SUFFIX={issuerState:'/issuer/state.json',replayState:'/replay/state.json',
  stageRootsArchive:'/stage-trust-roots.json',roots:'/trust-roots.json',
  issuerConfig:'/issuer.json',receipt:'/handoff-cutover.receipt.json',
  appManifest:'/app-manifest.json',bridgeManifest:'/bridge-manifest.json',nativeManifest:'/native-manifest.json'};
const ORDER=['issuerState','replayState','appManifest','bridgeManifest','nativeManifest',
  'stageRootsArchive','roots','issuerConfig','receipt'];
const sha=bytes=>createHash('sha256').update(bytes).digest('hex');
const hash=value=>typeof value==='string'&&/^[a-f0-9]{64}$/.test(value);
const fail=code=>{throw Object.assign(new Error(code),{code});};
const need=(value,code)=>{if(!value)fail(code);};
const copy=value=>JSON.parse(canonical(value));
function frozen(value){if(value&&typeof value==='object'){for(const v of Object.values(value))frozen(v);Object.freeze(value);}return value;}
function exact(value,fields){need(value&&Object.getPrototypeOf(value)===Object.prototype&&
  canonical(Object.keys(value).sort())===canonical(fields.slice().sort()),'CUTOVER_ARTIFACTS_INVALID');}
function safePath(value){need(typeof value==='string'&&path.isAbsolute(value)&&
  path.normalize(value)===value&&!/[\\\x00-\x1f\x7f]/.test(value),'CUTOVER_PATH_INVALID');}
function parent(io,file,uid){
  safePath(file);let cursor='/';
  for(const part of path.dirname(file).split('/').filter(Boolean)){
    cursor=path.join(cursor,part);const s=io.lstatSync(cursor);
    need(s.isDirectory()&&!s.isSymbolicLink(),'CUTOVER_PARENT_UNTRUSTED');
    // A private user-owned test directory may live beneath the system /tmp.
    need((s.uid===uid||s.uid===0)&&(!(s.mode&0o022)||(s.uid===0&&(s.mode&0o1000))),
      'CUTOVER_PARENT_UNTRUSTED');
  }
}
function readFile(io,file,uid,max=MAX_FILE){
  parent(io,file,uid);let fd;
  try{fd=io.openSync(file,fs.constants.O_RDONLY|fs.constants.O_NOFOLLOW);}
  catch(e){if(e.code==='ENOENT')return null;throw e;}
  try{
    const s=io.fstatSync(fd);
    need(s.isFile()&&s.uid===uid&&s.nlink===1&&!(s.mode&0o7022)&&s.size<=max,
      'CUTOVER_FILE_UNTRUSTED');
    const bytes=io.readFileSync(fd),after=io.fstatSync(fd);
    need(bytes.length===s.size&&after.size===s.size&&after.mtimeMs===s.mtimeMs&&after.ctimeMs===s.ctimeMs,
      'CUTOVER_FILE_CHANGED');
    return {bytes,mode:s.mode&0o7777};
  }finally{io.closeSync(fd);}
}
function readJournal(io,directory,name,uid){
  const value=readFile(io,path.join(directory,name),uid,MAX_JOURNAL);
  if(value===null)return null;
  need(value.mode===0o600&&value.bytes.length>0,'CUTOVER_JOURNAL_UNTRUSTED');
  let data;try{data=JSON.parse(value.bytes);}catch{fail('CUTOVER_JOURNAL_UNTRUSTED');}
  need(value.bytes.equals(Buffer.from(canonical(data))),'CUTOVER_JOURNAL_UNTRUSTED');return data;
}
function syncDir(io,dir){const fd=io.openSync(dir,fs.constants.O_RDONLY|fs.constants.O_DIRECTORY|fs.constants.O_NOFOLLOW);try{io.fsyncSync(fd);}finally{io.closeSync(fd);}}
function atomicFile({io,file,bytes,mode,uid,checkpoint,fault,label}){
  parent(io,file,uid);checkpoint(label+':before-write');
  const tmp=path.join(path.dirname(file),'.cutover-pending-'+path.basename(file)+'-'+randomUUID());
  const fd=io.openSync(tmp,fs.constants.O_WRONLY|fs.constants.O_CREAT|fs.constants.O_EXCL|fs.constants.O_NOFOLLOW,0o600);
  try{
    let offset=0;while(offset<bytes.length){const n=io.writeSync(fd,bytes,offset,bytes.length-offset,offset);need(n>0,'CUTOVER_WRITE_FAILED');offset+=n;}
    io.fchmodSync(fd,mode);io.fsyncSync(fd);
  }finally{io.closeSync(fd);}
  fault(label+':after-temp-fsync');checkpoint(label+':before-rename');
  io.renameSync(tmp,file);fault(label+':after-rename');syncDir(io,path.dirname(file));
  fault(label+':after-dir-fsync');
}
function emptyReplay(bytes){
  let value;try{value=JSON.parse(bytes);}catch{fail('CUTOVER_REPLAY_NOT_EMPTY');}
  need(value?.schema===1&&value.data?.kind==='mht.issuer-replay.v2'&&
    Array.isArray(value.data.used)&&value.data.used.length===0&&value.data.handoff===null,
    'CUTOVER_REPLAY_NOT_EMPTY');
}
function targetHeaders(targets,directory){
  need(Array.isArray(targets)&&targets.length>=REQUIRED.length&&targets.length<=ORDER.length,
    'CUTOVER_ARTIFACTS_INVALID');
  const slots=new Set(),paths=new Set();
  for(const file of targets){
    exact(file,['slot','path','mode','beforeSha256']);safePath(file.path);
    need(Object.hasOwn(SUFFIX,file.slot)&&file.path.endsWith(SUFFIX[file.slot])&&
      !file.path.startsWith(directory+'/')&&!slots.has(file.slot)&&!paths.has(file.path)&&
      (file.beforeSha256===null||hash(file.beforeSha256))&&
      (file.mode===0o600||(file.slot.endsWith('Manifest')&&file.mode===0o644)),
      'CUTOVER_ARTIFACTS_INVALID');
    slots.add(file.slot);paths.add(file.path);
  }
  need(REQUIRED.every(slot=>slots.has(slot)),'CUTOVER_ARTIFACTS_INVALID');
  return targets.slice().sort((a,b)=>ORDER.indexOf(a.slot)-ORDER.indexOf(b.slot));
}
function initialTargetState(io,spec,uid){
  const current=readFile(io,spec.path,uid);if(current===null)return;
  if(spec.slot==='replayState')emptyReplay(current.bytes);
  need(spec.beforeSha256!==null&&sha(current.bytes)===spec.beforeSha256,'CUTOVER_TARGET_DRIFT');
}
function fileSpecs(artifacts,directory,plannedTargets){
  exact(artifacts,['schema','files','evidence']);
  need(artifacts.schema==='mht.cutover-artifacts.v1'&&Array.isArray(artifacts.files)&&
    artifacts.files.length>=REQUIRED.length&&artifacts.files.length<=ORDER.length,
    'CUTOVER_ARTIFACTS_INVALID');
  const slots=new Set(),paths=new Set(),specs=[];let total=0;
  for(const file of artifacts.files){
    exact(file,['slot','path','mode','beforeSha256','bytesBase64']);safePath(file.path);
    need(Object.hasOwn(SUFFIX,file.slot)&&file.path.endsWith(SUFFIX[file.slot])&&
      !file.path.startsWith(directory+'/')&&!slots.has(file.slot)&&!paths.has(file.path)&&
      (file.beforeSha256===null||hash(file.beforeSha256))&&
      (file.mode===0o600||(file.slot.endsWith('Manifest')&&file.mode===0o644))&&
      typeof file.bytesBase64==='string'&&file.bytesBase64.length<=Math.ceil(MAX_FILE/3)*4,
      'CUTOVER_ARTIFACTS_INVALID');
    const bytes=Buffer.from(file.bytesBase64,'base64');
    need(bytes.length>0&&bytes.length<=MAX_FILE&&bytes.toString('base64')===file.bytesBase64,
      'CUTOVER_ARTIFACTS_INVALID');
    if(file.slot==='replayState')emptyReplay(bytes);
    total+=bytes.length;need(total<=MAX_JOURNAL/2,'CUTOVER_ARTIFACTS_TOO_LARGE');
    slots.add(file.slot);paths.add(file.path);specs.push({...file,bytes,afterSha256:sha(bytes)});
  }
  need(REQUIRED.every(slot=>slots.has(slot)),'CUTOVER_ARTIFACTS_INVALID');
  need(canonical(targetHeaders(specs.map(({slot,path,mode,beforeSha256})=>({slot,path,mode,beforeSha256})),directory))===
    canonical(targetHeaders(plannedTargets,directory)),'CUTOVER_TARGET_PLAN_CHANGED');
  return specs.sort((a,b)=>ORDER.indexOf(a.slot)-ORDER.indexOf(b.slot));
}
function targetState(io,spec,uid){
  const current=readFile(io,spec.path,uid);
  if(current===null)return 'absent';
  if(spec.slot==='replayState')emptyReplay(current.bytes);
  const currentHash=sha(current.bytes);
  if(currentHash===spec.afterSha256&&current.mode===spec.mode)return 'new';
  need(spec.beforeSha256!==null&&currentHash===spec.beforeSha256,'CUTOVER_TARGET_DRIFT');return 'old';
}

/** All callbacks are synchronous and return true to attest their checks.
 * preflight/guard receive {phase,identity,artifacts,point}; recovery callbacks
 * must admit ONLY the original exact artifacts, including already-new files.
 * INTENT without durable ARTIFACTS is UNKNOWN and never calls produce again.
 * A recorded commit is historical: it never restores an advanced new ledger.
 */
export function runCutoverTransaction({directory,identity,plannedTargets,preflight,guard,
  produceArtifacts,validateArtifacts,verifyCommit,now=Date.now,
  io=fs,run=spawnSync,uid=process.geteuid(),fault=()=>{},}={}){
  safePath(directory);
  need(identity?.schema==='mht.cutover-intent.v1'&&Number.isSafeInteger(identity.issuedAt)&&
    Number.isSafeInteger(identity.expiresAt)&&identity.issuedAt<identity.expiresAt&&
    [preflight,guard,produceArtifacts,validateArtifacts,verifyCommit,now,fault].every(fn=>typeof fn==='function'),
    'CUTOVER_INPUT_INVALID');
  const admitted=frozen(copy(identity)),identityHash=digest(admitted);
  const targets=frozen(copy(targetHeaders(plannedTargets,directory))),targetsHash=digest(targets);
  parent(io,directory+'/.lock',uid);const ds=io.lstatSync(directory);
  need(ds.isDirectory()&&!ds.isSymbolicLink()&&ds.uid===uid&&(ds.mode&0o7777)===0o700,
    'CUTOVER_DIRECTORY_UNTRUSTED');
  const peekIntent=readJournal(io,directory,'INTENT.json',uid),peekArtifacts=readJournal(io,directory,'ARTIFACTS.json',uid),peekCommit=readJournal(io,directory,'COMMIT.json',uid);
  const phase=peekCommit?'RECORDED':peekArtifacts?'RECOVER':peekIntent?'UNKNOWN':'INITIAL';
  const context=(point,artifacts=null)=>frozen({phase,identity:admitted,artifacts,point});
  // Check admission before creating even the writer lock file.
  need(preflight(context('preflight',peekArtifacts?.artifacts??null))===true,'CUTOVER_PREFLIGHT_REFUSED');
  let lastNow=admitted.issuedAt;
  if(phase==='INITIAL'||phase==='RECOVER'){
    lastNow=now();need(Number.isSafeInteger(lastNow)&&admitted.issuedAt<=lastNow&&lastNow<admitted.expiresAt,
      'CUTOVER_AUTHORIZATION_PENDING');
  }
  if(phase==='INITIAL')for(const spec of targets)initialTargetState(io,spec,uid);
  const fd=io.openSync(path.join(directory,'.lock'),fs.constants.O_RDWR|fs.constants.O_CREAT|fs.constants.O_NOFOLLOW,0o600);
  let intent=null,saved=null,lockedByThisCall=false,newAttempt=false;
  try{
    const ls=io.fstatSync(fd);need(ls.isFile()&&ls.uid===uid&&ls.nlink===1&&(ls.mode&0o7777)===0o600,'CUTOVER_LOCK_UNTRUSTED');
    const locked=run('/usr/bin/flock',['-n','3'],{stdio:['ignore','ignore','ignore',fd],timeout:5000,env:{PATH:'/usr/bin:/bin'}});
    need(locked?.status===0&&!locked.signal&&!locked.error,'CUTOVER_LOCK_BUSY');
    lockedByThisCall=true;
    intent=readJournal(io,directory,'INTENT.json',uid);saved=readJournal(io,directory,'ARTIFACTS.json',uid);
    newAttempt=intent===null;
    const committed=readJournal(io,directory,'COMMIT.json',uid);
    need(Boolean(intent)===Boolean(peekIntent)&&Boolean(saved)===Boolean(peekArtifacts)&&
      Boolean(committed)===Boolean(peekCommit)&&(!intent||digest(intent)===digest(peekIntent))&&
      (!saved||digest(saved)===digest(peekArtifacts))&&(!committed||digest(committed)===digest(peekCommit)),
      'CUTOVER_JOURNAL_CHANGED');
    if(intent)need(intent.schema==='mht.cutover-journal-intent.v1'&&intent.identityHash===identityHash&&
      digest(intent.identity)===identityHash&&intent.targetsHash===targetsHash&&
      digest(intent.plannedTargets)===targetsHash,'CUTOVER_INTENT_CONFLICT');
    need((!saved&&!committed)||intent,'CUTOVER_ORPHAN_JOURNAL');
    if(saved)need(saved.schema==='mht.cutover-artifacts-journal.v1'&&saved.intentHash===digest(intent),'CUTOVER_ARTIFACTS_CONFLICT');
    if(committed){
      need(saved&&committed.schema==='mht.cutover-commit.v1'&&committed.intentHash===digest(intent)&&
        committed.artifactsHash===digest(saved),'CUTOVER_COMMIT_CONFLICT');
      exact(committed,['schema','intentHash','artifactsHash','targets','committedAt']);
      const historicalArtifacts=frozen(copy(saved.artifacts)),specs=fileSpecs(historicalArtifacts,directory,targets);
      need(Number.isSafeInteger(committed.committedAt)&&admitted.issuedAt<=committed.committedAt&&
        committed.committedAt<admitted.expiresAt&&
        canonical(committed.targets)===canonical(Object.fromEntries(specs.map(spec=>[spec.slot,spec.afterSha256])))&&
        validateArtifacts(historicalArtifacts,context('validate-recorded',historicalArtifacts))===true,
        'CUTOVER_COMMIT_CONFLICT');
      return frozen({status:'CUTOVER_ALREADY_COMMITTED',identityHash,artifactsHash:digest(saved),
        commitHash:digest(committed),signerCalled:false,historical:true,mayStartIssuer:false});
    }
    if(intent&&!saved)fail('CUTOVER_EFFECT_UNKNOWN');
    let artifacts=saved?frozen(copy(saved.artifacts)):null;
    const checkpoint=point=>{
      const t=now();need(Number.isSafeInteger(t)&&lastNow<=t&&admitted.issuedAt<=t&&t<admitted.expiresAt,
        'CUTOVER_AUTHORIZATION_PENDING');
      lastNow=t;
      need(guard(context(point,artifacts))===true,'CUTOVER_GUARD_REFUSED');
      return t;
    };
    const journal=(name,data)=>atomicFile({io,file:path.join(directory,name),bytes:Buffer.from(canonical(data)),
      mode:0o600,uid,checkpoint,fault,label:name});
    if(!saved){
      checkpoint('before-intent');for(const spec of targets)initialTargetState(io,spec,uid);
      intent={schema:'mht.cutover-journal-intent.v1',identity:admitted,identityHash,plannedTargets:targets,targetsHash};
      journal('INTENT.json',intent);fault('after-intent');checkpoint('before-effect');
      for(const spec of targets)initialTargetState(io,spec,uid);
      const produced=produceArtifacts(context('effect'));fault('after-effect');
      artifacts=frozen(copy(produced));fileSpecs(artifacts,directory,targets);
      need(validateArtifacts(artifacts,context('validate',artifacts))===true,'CUTOVER_ARTIFACTS_REJECTED');
      saved={schema:'mht.cutover-artifacts-journal.v1',intentHash:digest(intent),artifacts};
      journal('ARTIFACTS.json',saved);fault('after-artifacts');
    }
    const specs=fileSpecs(artifacts,directory,targets);
    need(validateArtifacts(artifacts,context('validate-recovery',artifacts))===true,'CUTOVER_ARTIFACTS_REJECTED');
    // Detect every unrelated target before publishing any of the batch.
    checkpoint('before-target-set');for(const spec of specs)targetState(io,spec,uid);
    for(const spec of specs){
      checkpoint(spec.slot+':guard');const state=targetState(io,spec,uid);
      if(state!=='new')atomicFile({io,file:spec.path,bytes:spec.bytes,mode:spec.mode,uid,fault,
        label:spec.slot,checkpoint:point=>{checkpoint(point);targetState(io,spec,uid);}});
      fault('after-file:'+spec.slot);
    }
    checkpoint('verify-commit');
    for(const spec of specs)need(targetState(io,spec,uid)==='new','CUTOVER_COMMIT_NOT_EXACT');
    need(verifyCommit(artifacts,context('verify-commit',artifacts))===true,'CUTOVER_COMMIT_REJECTED');
    const committedAt=checkpoint('commit-time');
    const commit={schema:'mht.cutover-commit.v1',intentHash:digest(intent),artifactsHash:digest(saved),
      targets:Object.fromEntries(specs.map(spec=>[spec.slot,spec.afterSha256])),committedAt};
    journal('COMMIT.json',commit);fault('after-commit');
    return frozen({status:'CUTOVER_COMMITTED',identityHash,artifactsHash:digest(saved),commitHash:digest(commit),
      signerCalled:!peekArtifacts,historical:false,mayStartIssuer:false});
  }catch(e){
    // Once signing could have happened, missing ARTIFACTS never permits retry.
    if(!lockedByThisCall||!newAttempt)throw e;
    const durableIntent=readJournal(io,directory,'INTENT.json',uid);
    const durableArtifacts=readJournal(io,directory,'ARTIFACTS.json',uid);
    if(durableIntent&&!durableArtifacts&&e.code!=='CUTOVER_AUTHORIZATION_PENDING')fail('CUTOVER_EFFECT_UNKNOWN');
    throw e;
  }finally{io.closeSync(fd);}
}
