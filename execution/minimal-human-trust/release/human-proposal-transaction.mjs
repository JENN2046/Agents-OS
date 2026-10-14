// Proposal signing is an exact-once effect, never enrollment or installation.
// A durable INTENT without RESULT is UNKNOWN and must never be retried.
import fs from 'node:fs';
import path from 'node:path';
import {spawnSync} from 'node:child_process';
import {canonical,digest} from '../src/lease-core.mjs';

const fail=code=>{throw Object.assign(new Error(code),{code});};
const need=(condition,code)=>{if(!condition)fail(code);};
const MAX_BYTES=8*1024*1024;
const IDENTITY_KEYS=['action','policyTemplateHash','proposalBodyHash','requestHash','schema','sourceFreezeDigest'];
const record=value=>value!==null&&typeof value==='object'&&!Array.isArray(value);
const sameFile=(a,b)=>a.dev===b.dev&&a.ino===b.ino;
const callSync=(fn,...args)=>{
 const value=fn(...args);
 need(!value||typeof value.then!=='function','HUMAN_PROPOSAL_ASYNC_CALLBACK');
 need(value!==false,'HUMAN_PROPOSAL_CALLBACK_REFUSED');
 return value;
};
function strictDirectory(io,directory,uid){
 need(path.isAbsolute(directory)&&path.normalize(directory)===directory,'HUMAN_PROPOSAL_DIRECTORY');
 const st=io.lstatSync(directory);
 need(st.isDirectory()&&!st.isSymbolicLink()&&st.uid===uid&&(st.mode&0o7777)===0o700,
  'HUMAN_PROPOSAL_DIRECTORY');
 // Production root must not reach its journal through writable or symlinked
 // ancestors. Disposable non-root test directories retain ordinary /tmp use.
 if(uid===0){
  for(let parent=path.dirname(directory);;parent=path.dirname(parent)){
   const ps=io.lstatSync(parent);
   need(ps.isDirectory()&&!ps.isSymbolicLink()&&ps.uid===0&&(ps.mode&0o022)===0,
    'HUMAN_PROPOSAL_PARENT_UNTRUSTED');
   if(parent==='/')break;
  }
 }
 return st;
}
function strictRead(io,directory,name,uid){
 const file=path.join(directory,name);
 let fd;
 try{fd=io.openSync(file,fs.constants.O_RDONLY|fs.constants.O_NOFOLLOW);}
 catch(error){if(error?.code==='ENOENT')return null;throw error;}
 try{
  const st=io.fstatSync(fd);
  need(st.isFile()&&st.uid===uid&&st.nlink===1&&(st.mode&0o7777)===0o600&&
   st.size>0&&st.size<=MAX_BYTES,'HUMAN_PROPOSAL_STATE_UNTRUSTED');
  const bytes=io.readFileSync(fd),after=io.fstatSync(fd),named=io.lstatSync(file);
  need(bytes.length===st.size&&after.size===st.size&&sameFile(st,named)&&
   !named.isSymbolicLink()&&named.nlink===1,'HUMAN_PROPOSAL_STATE_UNTRUSTED');
  let value;try{value=JSON.parse(bytes);}catch{fail('HUMAN_PROPOSAL_STATE_UNTRUSTED');}
  need(bytes.equals(Buffer.from(canonical(value))),'HUMAN_PROPOSAL_STATE_UNTRUSTED');
  return value;
 }finally{io.closeSync(fd);}
}
function writeExclusive(io,directory,name,value,uid){
 const bytes=Buffer.from(canonical(value));
 need(bytes.length>0&&bytes.length<=MAX_BYTES,'HUMAN_PROPOSAL_RESULT_TOO_LARGE');
 const file=path.join(directory,name);
 let fd;
 try{fd=io.openSync(file,fs.constants.O_WRONLY|fs.constants.O_CREAT|fs.constants.O_EXCL|
  fs.constants.O_NOFOLLOW,0o600);}
 catch(error){fail(error?.code==='EEXIST'?'HUMAN_PROPOSAL_TARGET_EXISTS':'HUMAN_PROPOSAL_WRITE_FAILED');}
 try{
  const st=io.fstatSync(fd);
  need(st.isFile()&&st.uid===uid&&st.nlink===1&&(st.mode&0o7777)===0o600,
   'HUMAN_PROPOSAL_STATE_UNTRUSTED');
  for(let at=0;at<bytes.length;){
   const written=io.writeSync(fd,bytes,at,bytes.length-at,at);
   need(Number.isInteger(written)&&written>0,'HUMAN_PROPOSAL_WRITE_FAILED');
   at+=written;
  }
  io.fsyncSync(fd);
 }finally{io.closeSync(fd);}
 const dfd=io.openSync(directory,fs.constants.O_RDONLY|fs.constants.O_DIRECTORY|fs.constants.O_NOFOLLOW);
 try{io.fsyncSync(dfd);}finally{io.closeSync(dfd);}
}
function lockExclusive(io,run,directory,uid){
 const fd=io.openSync(path.join(directory,'.lock'),fs.constants.O_RDWR|fs.constants.O_CREAT|
  fs.constants.O_NOFOLLOW,0o600);
 try{
  const st=io.fstatSync(fd);
  need(st.isFile()&&st.uid===uid&&st.nlink===1&&(st.mode&0o7777)===0o600,
   'HUMAN_PROPOSAL_LOCK_UNTRUSTED');
  // Child and parent share the same open file description; closing the child
  // does not drop flock while this parent descriptor stays open.
  const locked=run('/usr/bin/flock',['-n','3'],{stdio:['ignore','ignore','ignore',fd],
   timeout:5000,env:{PATH:'/usr/bin:/bin'}});
  need(locked?.status===0&&!locked.signal&&!locked.error,'HUMAN_PROPOSAL_LOCK_BUSY');
  return fd;
 }catch(error){io.closeSync(fd);throw error;}
}
/** All callbacks must be synchronous. The caller supplies the cryptographic
 * verifier and exact immutable publisher, after its own root/source admission.
 * A callback or this public receipt is never an authority credential.
 */
export function issueHumanProposalOnce({directory,identity,produce,verifyResult,publish,
 guard=()=>{},io=fs,uid=process.geteuid(),run=spawnSync,fault=()=>{}}){
 need(record(identity)&&Object.keys(identity).sort().join('|')===IDENTITY_KEYS.join('|')&&
  identity.schema==='mht.human-proposal-signing-intent.v1'&&
  ['enroll_human','first_cutover_handoff'].includes(identity.action)&&
  IDENTITY_KEYS.filter(key=>key.endsWith('Hash')||key==='sourceFreezeDigest')
   .every(key=>typeof identity[key]==='string'&&/^[0-9a-f]{64}$/.test(identity[key]))&&
  [produce,verifyResult,publish,guard,run,fault].every(fn=>typeof fn==='function')&&
  Number.isInteger(uid)&&uid>=0,'HUMAN_PROPOSAL_INTENT_INVALID');
 // Freeze the canonical identity before any caller code can mutate it.
 const admittedIdentity=JSON.parse(canonical(identity)),intentHash=digest(admittedIdentity);
 const directoryStat=strictDirectory(io,directory,uid);
 const fd=lockExclusive(io,run,directory,uid);
 const namespace=()=>{
  need(sameFile(directoryStat,strictDirectory(io,directory,uid)),'HUMAN_PROPOSAL_DIRECTORY_DRIFT');
  const lock=io.fstatSync(fd),named=io.lstatSync(path.join(directory,'.lock'));
  need(sameFile(lock,named)&&named.isFile()&&!named.isSymbolicLink()&&named.nlink===1&&
   named.uid===uid&&(named.mode&0o7777)===0o600,'HUMAN_PROPOSAL_LOCK_UNTRUSTED');
 };
 const checkedGuard=()=>{namespace();callSync(guard);namespace();};
 const validate=result=>{
  need(record(result)&&Object.keys(result).sort().join('|')==='artifacts|intentHash|schema'&&
   result.schema==='mht.human-proposal-signing-result.v1'&&result.intentHash===intentHash&&
   record(result.artifacts),'HUMAN_PROPOSAL_RESULT_CONFLICT');
  callSync(verifyResult,result.artifacts);namespace();
 };
 try{
  checkedGuard();
  const prior=strictRead(io,directory,'intent.json',uid);
  let result=strictRead(io,directory,'result.json',uid),signerCalled=false;
  namespace();
  if(prior!==null){
   need(digest(prior)===intentHash,'HUMAN_PROPOSAL_INTENT_CONFLICT');
   if(result===null)fail('HUMAN_PROPOSAL_EFFECT_UNKNOWN');
   validate(result);
  }else{
   need(result===null,'HUMAN_PROPOSAL_ORPHAN_RESULT');
   writeExclusive(io,directory,'intent.json',admittedIdentity,uid);
   callSync(fault,'after_intent');
   checkedGuard();
   need(digest(strictRead(io,directory,'intent.json',uid))===intentHash,'HUMAN_PROPOSAL_INTENT_CONFLICT');
   const artifacts=callSync(produce);
   signerCalled=true;
   checkedGuard();
   result={schema:'mht.human-proposal-signing-result.v1',intentHash,artifacts};
   validate(result);
   callSync(fault,'after_effect');
   namespace();
   writeExclusive(io,directory,'result.json',result,uid);
   callSync(fault,'after_result');
  }
  const resultHash=digest(result);
  const readback=()=>{
   namespace();
   need(digest(strictRead(io,directory,'intent.json',uid))===intentHash,'HUMAN_PROPOSAL_INTENT_CONFLICT');
   const saved=strictRead(io,directory,'result.json',uid);
   need(saved!==null&&digest(saved)===resultHash,'HUMAN_PROPOSAL_RESULT_CONFLICT');
   validate(saved);
   return saved.artifacts;
  };
  checkedGuard();
  const artifacts=readback();
  const artifactsHash=digest(artifacts);
  callSync(publish,artifacts);
  need(digest(artifacts)===artifactsHash,'HUMAN_PROPOSAL_RESULT_CONFLICT');
  callSync(fault,'after_publish');
  checkedGuard();
  readback();
  return Object.freeze({status:signerCalled?'SIGNED_PROPOSAL_ONLY':'SIGNED_PROPOSAL_ALREADY',
   intentHash,resultHash,artifactsHash,signerCalled,
   mayEnroll:false,maySignRelease:false,mayInstall:false,mayCutover:false});
 }finally{io.closeSync(fd);}
}
