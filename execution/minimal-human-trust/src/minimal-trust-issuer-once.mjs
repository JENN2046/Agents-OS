// Trust transition skeleton: uninstalled, root-only, socket-activated,
// exactly one signed request. NO production key access or service installation.
// All paths are fixed by reviewed source, not stdin/argv/environment.
import fs from 'node:fs';
import path from 'node:path';
import {spawnSync} from 'node:child_process';
import {fileURLToPath} from 'node:url';
import {verified,publicKey,exportPublicKey,digest,resolveRegisteredProject} from './lease-core.mjs';
import {loadRootIssuerPrivateKey} from './systemd-issuer-credential.mjs';
import {runMinimalTrustOnce} from './minimal-trust-issuer.mjs';
import {handoffSchema,verifyRecoveryHandoff}
  from '../authority/recovery-handoff.mjs';

export const TRUST_ROOTS_PATH='/etc/minimal-human-trust/trust-roots.json';
export const CONFIG_PATH='/etc/minimal-human-trust/issuer.json';
export const JOURNAL_ISSUER='/var/lib/minimal-human-trust/issuer';
export const JOURNAL_REPLAY='/var/lib/minimal-human-trust/replay';
export const REGISTRY_READER='/usr/libexec/minimal-human-trust/registry-reader.py';
const reject=(code)=>{throw Object.assign(new Error(code),{code});};
const need=(a,c='MHT_ENTRY_REJECTED')=>{if(!a)reject(c);};
const eq=(a,b)=>JSON.stringify(a)===JSON.stringify(b);
function trustedFile(filename,io=fs){
  need([CONFIG_PATH,TRUST_ROOTS_PATH].includes(filename),'MHT_CONFIG_PATH');
  for(let cursor='/',i=0,parts=path.dirname(filename).split('/').filter(Boolean);i<=parts.length;i++){
    if(i)cursor=path.join(cursor,parts[i-1]);
    const st=io.lstatSync(cursor);
    need(st.isDirectory()&&!st.isSymbolicLink()&&st.uid===0&&!(st.mode&0o022),'MHT_CONFIG_OWNER');
  }
  const st=io.lstatSync(filename);
  need(st.isFile()&&!st.isSymbolicLink()&&st.uid===0&&st.nlink===1&&
    !(st.mode&0o022)&&st.size>0&&st.size<=65536,'MHT_CONFIG_OWNER');
  const fd=io.openSync(filename,fs.constants.O_RDONLY|fs.constants.O_NOFOLLOW);
  try{
    const opened=io.fstatSync(fd);
    need(opened.dev===st.dev&&opened.ino===st.ino&&opened.uid===0&&opened.nlink===1&&
      opened.isFile()&&!(opened.mode&0o022)&&opened.size===st.size,'MHT_CONFIG_OWNER');
    const raw=io.readFileSync(fd,'utf8'),after=io.fstatSync(fd);
    need(Buffer.byteLength(raw)===st.size&&after.size===opened.size&&after.mtimeMs===opened.mtimeMs&&
      after.ctimeMs===opened.ctimeMs,'MHT_CONFIG_CHANGED');
    return raw;
  }finally{io.closeSync(fd);}
}
const hash=value=>typeof value==='string'&&/^[a-f0-9]{64}$/.test(value);
const exact=(value,fields)=>need(value&&typeof value==='object'&&!Array.isArray(value)&&
  Object.keys(value).sort().join(',')===fields.split(',').sort().join(','),'MHT_CONFIG_SHAPE');
export function validateTrustRoots(roots){
  exact(roots,'schema,grantId,issuerPublicKey,releasePublicKey,enrollmentAuthorityPublicKey,releaseHash,installationProfile,handoffHash');
  need(roots.schema==='mht.trust-roots.v1'&&/^[A-Za-z0-9_-]{1,128}$/.test(roots.grantId)&&
    ['isolated','production'].includes(roots.installationProfile)&&hash(roots.releaseHash)&&hash(roots.handoffHash),'MHT_ROOTS_INVALID');
  for(const name of ['issuerPublicKey','releasePublicKey','enrollmentAuthorityPublicKey'])publicKey(roots[name]);
  need(new Set([roots.issuerPublicKey,roots.releasePublicKey,roots.enrollmentAuthorityPublicKey]).size===3,'MHT_ROOTS_INVALID');
  return Object.freeze({...roots});
}
export function validateInstalledTrustPolicy(value,{trustRoots,publicKeyHint=null,now=Date.now()}={}){
  const roots=validateTrustRoots(trustRoots);
  exact(value,'enrollment,enrollmentAuthorityPublicKey,grantId,handoff,humanAuthorityPublicKey,issuerPublicKey,mode,release,releasePublicKey,schema,trustCutoverPhase');
  need(value.schema==='mht.installed-issuer.v1','MHT_CONFIG_SHAPE');
  need(value.trustCutoverPhase==='RECOVERY_SHADOW'&&value.mode==='recovery_only','MHT_ACTIVE_NOT_APPROVED');
  for(const field of ['grantId','issuerPublicKey','releasePublicKey','enrollmentAuthorityPublicKey'])
    need(value[field]===roots[field],'MHT_ROOT_BINDING');
  need(digest(value.release)===roots.releaseHash&&digest(value.handoff)===roots.handoffHash,'MHT_ROOT_BINDING');
  publicKey(value.humanAuthorityPublicKey);
  const release=verified(value.release,roots.releasePublicKey,'r16.release.v1');
  // Expired enrollment remains an authenticated identity for cleanup and
  // revocation only. This entry cannot grant, enroll, activate or widen scope.
  const enrollment=verified(value.enrollment,roots.enrollmentAuthorityPublicKey,'mht.human-enrollment.v1');
  exact(enrollment,'enrolledAt,expiresAt,grantHash,grantId,humanPublicKey,humanSubject,humanUid,releaseHash,releaseId,schema');
  need(enrollment.humanPublicKey===value.humanAuthorityPublicKey&&
    ![roots.issuerPublicKey,roots.releasePublicKey,roots.enrollmentAuthorityPublicKey].includes(enrollment.humanPublicKey)&&
    enrollment.humanUid===1000&&typeof enrollment.humanSubject==='string'&&
    /^[-_a-zA-Z0-9:.]{1,128}$/.test(enrollment.humanSubject)&&
    enrollment.releaseId===release.id&&enrollment.releaseHash===roots.releaseHash&&enrollment.grantId===value.grantId&&
    Number.isSafeInteger(enrollment.enrolledAt)&&Number.isSafeInteger(enrollment.expiresAt)&&
    enrollment.enrolledAt<=now&&enrollment.expiresAt>enrollment.enrolledAt&&hash(enrollment.grantHash),'HUMAN_ENROLLMENT_MISMATCH');
  const recovery=handoffSchema(value.handoff)==='mht.issuer-handoff.v2';
  const handoff=recovery?verifyRecoveryHandoff(value.handoff,roots.enrollmentAuthorityPublicKey,
    {grantId:value.grantId,release:value.release,mode:value.mode,grantHash:enrollment.grantHash,
      issuerPublicKey:roots.issuerPublicKey}):
    verified(value.handoff,roots.enrollmentAuthorityPublicKey,'mht.issuer-handoff.v1');
  exact(handoff,'schema,grantId,grantHash,releaseHash,issuerSnapshotHash,installationProfile,epoch,mode,oldWriterClosed,participantClosureHashes,issuedAt,expiresAt'+
    (recovery?',recoveryAdmission':''));
  exact(handoff.participantClosureHashes,'app,bridge,native');
  need(handoff.grantId===value.grantId&&handoff.grantHash===enrollment.grantHash&&
    handoff.releaseHash===roots.releaseHash&&handoff.installationProfile===roots.installationProfile&&
    handoff.mode==='recovery_only'&&handoff.oldWriterClosed===true&&hash(handoff.issuerSnapshotHash)&&
    Object.values(handoff.participantClosureHashes).every(hash)&&
    Number.isSafeInteger(handoff.epoch)&&handoff.epoch>0&&Number.isSafeInteger(handoff.issuedAt)&&
    Number.isSafeInteger(handoff.expiresAt)&&handoff.issuedAt<=now&&handoff.expiresAt>handoff.issuedAt,'MHT_HANDOFF_REQUIRED');
  need(publicKeyHint===null||publicKeyHint===roots.issuerPublicKey,'MHT_KEY_BINDING');
  return {release,grantHash:enrollment.grantHash,issuerPublicKey:roots.issuerPublicKey,
    humanAuthorityPublicKey:value.humanAuthorityPublicKey,mode:'recovery_only',installationProfile:roots.installationProfile,
    handoffBinding:{handoffHash:roots.handoffHash,issuerSnapshotHash:handoff.issuerSnapshotHash,epoch:handoff.epoch,
      admissionExpiresAt:handoff.expiresAt,...(recovery?{recoveryHandoff:value.handoff}:{})}};
}
// A single complete line is read under fixed byte/time limits. Never wait for
// EOF on an accepted socket; never read an unbounded file descriptor first.
export function readBoundedOnceInput(input=process.stdin){
  return new Promise((resolve,reject)=>{
    let chunks=[],size=0,done=false;
    const finish=(error,value)=>{
      if(done)return;done=true;clearTimeout(timer);
      input.off('data',data);input.off('end',end);input.off('error',errorEvent);input.pause();
      if(error)reject(Object.assign(new Error(error),{code:error}));else resolve(value);
    };
    const data=chunk=>{
      const bytes=Buffer.isBuffer(chunk)?chunk:Buffer.from(chunk);size+=bytes.length;
      if(size>262144)return finish('MHT_INPUT_LIMIT');
      chunks.push(bytes);
      const joined=Buffer.concat(chunks,size),at=joined.indexOf(10);
      if(at!==-1){
        if(at!==joined.length-1)return finish('MHT_INPUT_FRAMING');
        return finish(null,joined);
      }
    };
    const end=()=>finish('MHT_INPUT_FRAMING'),errorEvent=()=>finish('MHT_INPUT_IO');
    const timer=setTimeout(()=>finish('MHT_INPUT_TIMEOUT'),5000);
    input.on('data',data);input.on('end',end);input.on('error',errorEvent);input.resume();
  });
}
function safeRegistry(projectId,options,invoke=spawnSync){
  need(typeof projectId==='string'&&/^[A-Za-z0-9_-]{1,128}$/.test(projectId),'PROJECT_BINDING');
  const args=projectId.startsWith('pending-')?['-I',REGISTRY_READER,'--pending','r16-projects-daily',projectId]:['-I',REGISTRY_READER,projectId];
  const reply=invoke('/usr/bin/python3',args,{encoding:'utf8',timeout:5000,maxBuffer:8192,
    env:{PATH:'/usr/bin:/bin'},stdio:['ignore','pipe','ignore']});
  need(reply.status===0&&!reply.signal&&typeof reply.stdout==='string'&&reply.stdout.length<=8192,'PROJECT_BINDING');
  return JSON.parse(reply.stdout);
}
export function parseOnceRequest(raw,lane){
  need(Buffer.isBuffer(raw)&&raw.length<=262144&&raw.length>0,'MHT_INPUT_LIMIT');
  const lines=raw.toString('utf8').split('\n');
  need(lines.length===2&&lines[1]==='', 'MHT_INPUT_FRAMING');
  const p=JSON.parse(lines[0]);
  need(p&&typeof p==='object'&&!Array.isArray(p),'MHT_INPUT_SHAPE');
  if(lane==='issuer'){
    need(Object.keys(p).sort().join(',')==='envelope,operation,schema'&&
      p.schema==='mht.once-request.v1'&&p.operation==='issuer','MHT_ISSUER_LANE');
    return {envelope:p.envelope,ownerApproval:null};
  }
  need(lane==='human'&&Object.keys(p).sort().join(',')==='operation,ownerApproval,schema'&&
    p.schema==='mht.once-request.v1'&&['revoke','revoke_status'].includes(p.operation)&&
    (p.operation!=='revoke_status'||p.ownerApproval?.body?.action==='revoke_status'),'MHT_HUMAN_LANE');
  return {envelope:null,ownerApproval:p.ownerApproval};
}
export async function runProtectedOnce({
  loadCredential=loadRootIssuerPrivateKey,loadConfig=()=>trustedFile(CONFIG_PATH),
  loadTrustRoots=()=>trustedFile(TRUST_ROOTS_PATH),
  readStdin=readBoundedOnceInput,resolveProject=null,now=Date.now,
  runIssuer=runMinimalTrustOnce,
}={}){
  need(process.argv.length===2,'MHT_ARGS_FORBIDDEN');
  const runtime=JSON.parse(loadConfig()),trustRoots=JSON.parse(loadTrustRoots());
  const policy=validateInstalledTrustPolicy(runtime,{trustRoots,now:now()});
  const service=loadCredential(),secret=service.key;
  need(exportPublicKey(secret)===policy.issuerPublicKey,'MHT_KEY_BINDING');
  const request=parseOnceRequest(await readStdin(),service.lane);
  const resolver=resolveProject??((workspace,project,options={})=>
    resolveRegisteredProject(workspace,project,id=>safeRegistry(id,options)));
  return runIssuer({
    issuerDirectory:policy.installationProfile==='isolated'?'/var/lib/minimal-human-trust/isolated/issuer':JOURNAL_ISSUER,
    replayDirectory:policy.installationProfile==='isolated'?'/var/lib/minimal-human-trust/isolated/replay':JOURNAL_REPLAY,
    handoffBinding:policy.handoffBinding,
    enrollmentAuthorityPublicKey:runtime.enrollmentAuthorityPublicKey,
    issuerPrivateKey:secret,issuerPublicKey:runtime.issuerPublicKey,
    releasePublicKey:runtime.releasePublicKey,release:runtime.release,
    grantId:runtime.grantId,humanAuthorityPublicKey:runtime.humanAuthorityPublicKey,
    expectedGrantHash:policy.grantHash,mode:policy.mode,resolveProject:resolver,now,
    ...request,
  });
}
if(process.argv[1]===fileURLToPath(import.meta.url)){
  try{
    const value=await runProtectedOnce();
    process.stdout.write(JSON.stringify({ok:true,value})+'\n');
  }catch{process.stdout.write(JSON.stringify({ok:false,error:'MHT_ONCE_REJECTED'})+'\n');process.exitCode=1;}
}
