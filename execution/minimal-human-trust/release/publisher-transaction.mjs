// FIRST_TRUST_BOOTSTRAP_R1: durable exact-once staging journal.
// Intent is fsynced BEFORE any private-key operation. An INTENT without
// a durable RESULT is UNKNOWN, NEVER permission to sign a second time.
import fs from 'node:fs';
import path from 'node:path';
import {spawnSync} from 'node:child_process';
import {canonical,digest} from '../src/lease-core.mjs';

const fail=code=>{throw Object.assign(new Error(code),{code});};
const need=(x,code='PUBLISHER_TRANSACTION_REFUSED')=>{if(!x)fail(code);};
const MAX_RESULT=8*1024*1024;
const dirSync=(io,dir)=>{
 const fd=io.openSync(dir,fs.constants.O_RDONLY|fs.constants.O_DIRECTORY|fs.constants.O_NOFOLLOW);
 try{io.fsyncSync(fd);}finally{io.closeSync(fd);}
};
function strictDir(io,dir,uid){
 need(path.isAbsolute(dir)&&path.normalize(dir)===dir,'PUBLISHER_DIRECTORY');
 const s=io.lstatSync(dir);
 need(s.isDirectory()&&!s.isSymbolicLink()&&s.uid===uid&&(s.mode&0o7777)===0o700,
   'PUBLISHER_DIRECTORY');
}
function strictRead(io,dir,name,uid){
 const file=path.join(dir,name);
 let fd;
 try{fd=io.openSync(file,fs.constants.O_RDONLY|fs.constants.O_NOFOLLOW);}
 catch(e){if(e?.code==='ENOENT')return null;throw e;}
 try{
  const st=io.fstatSync(fd);
  need(st.isFile()&&st.uid===uid&&st.nlink===1&&(st.mode&0o7777)===0o600&&
    st.size>0&&st.size<=MAX_RESULT,'PUBLISHER_STATE_UNTRUSTED');
  const bytes=io.readFileSync(fd);
  need(bytes.length===st.size,'PUBLISHER_STATE_UNTRUSTED');
  let data;try{data=JSON.parse(bytes);}catch{fail('PUBLISHER_STATE_UNTRUSTED');}
  need(bytes.equals(Buffer.from(canonical(data))),'PUBLISHER_STATE_UNTRUSTED');
  return data;
 }finally{io.closeSync(fd);}
}
function writeExclusive(io,dir,name,data,uid){
 const bytes=Buffer.from(canonical(data)),file=path.join(dir,name);
 need(bytes.length>0&&bytes.length<=MAX_RESULT,'PUBLISHER_RESULT_TOO_LARGE');
 let fd;
 try{fd=io.openSync(file,fs.constants.O_WRONLY|fs.constants.O_CREAT|fs.constants.O_EXCL|
     fs.constants.O_NOFOLLOW,0o600);}
 catch(e){fail(e?.code==='EEXIST'?'PUBLISHER_TARGET_EXISTS':'PUBLISHER_WRITE_FAILED');}
 try{
  const stat=io.fstatSync(fd);
  need(stat.isFile()&&stat.uid===uid&&stat.nlink===1&&(stat.mode&0o7777)===0o600);
  let at=0;
  while(at<bytes.length)at+=io.writeSync(fd,bytes,at,bytes.length-at,at);
  io.fsyncSync(fd);
 }finally{io.closeSync(fd);}
 dirSync(io,dir);
}
function lockExclusive(io,run,dir,uid){
 const file=path.join(dir,'.lock');
 const fd=io.openSync(file,fs.constants.O_RDWR|fs.constants.O_CREAT|fs.constants.O_NOFOLLOW,0o600);
 try{
  const st=io.fstatSync(fd);
  need(st.isFile()&&st.uid===uid&&st.nlink===1&&(st.mode&0o7777)===0o600,
    'PUBLISHER_LOCK_UNTRUSTED');
  const result=run('/usr/bin/flock',['-n','3'],{
    stdio:['ignore','ignore','ignore',fd],timeout:5000,env:{PATH:'/usr/bin:/bin'}});
  need(result?.status===0&&!result.signal&&!result.error,'PUBLISHER_LOCK_BUSY');
  return fd;
 }catch(e){io.closeSync(fd);throw e;}
}
/** Returns only public digests. Signed payload remains root-only in result.json.
 * Existing result is verified but NEVER signed twice.
 * The writer lock stays open for the whole synchronous check-sign-commit chain.
 */
export function stagePublisherOnce({
 directory,identity,sign,verifyResult,io=fs,run=spawnSync,
 uid=process.geteuid(),fault=()=>{},
}){
 need(identity?.schema==='mht.first-trust-signer-intent.v1'&&
   typeof sign==='function'&&typeof verifyResult==='function'&&
   typeof fault==='function','PUBLISHER_INTENT_INVALID');
 strictDir(io,directory,uid);
 const fd=lockExclusive(io,run,directory,uid);
 try{
  const intentHash=digest(identity);
  const prior=strictRead(io,directory,'intent.json',uid);
  const result=strictRead(io,directory,'result.json',uid);
  if(prior!==null){
   need(digest(prior)===intentHash,'PUBLISHER_INTENT_CONFLICT');
   if(result===null)fail('PUBLISHER_EFFECT_UNKNOWN');
   need(result.schema==='mht.first-trust-publisher-result.v1'&&
     result.intentHash===intentHash,'PUBLISHER_RESULT_CONFLICT');
   verifyResult(result.signedArtifacts);
   return Object.freeze({status:'SIGNED_STAGED_ALREADY',intentHash,
     resultHash:digest(result),replayed:false,signerCalled:false,
     mayActivate:false});
  }
  need(result===null,'PUBLISHER_ORPHAN_RESULT');
  writeExclusive(io,directory,'intent.json',identity,uid);
  fault('after_intent');
  const signedArtifacts=sign();
  // verifyResult must verify BOTH cryptographic signatures and all public
  // hashes against the already admitted exact source and root public keys.
  verifyResult(signedArtifacts);
  fault('after_effect');
  const saved={schema:'mht.first-trust-publisher-result.v1',
    intentHash,signedArtifacts};
  writeExclusive(io,directory,'result.json',saved,uid);
  fault('after_result');
  return Object.freeze({status:'SIGNED_STAGED',intentHash,
    resultHash:digest(saved),replayed:false,signerCalled:true,mayActivate:false});
 }finally{io.closeSync(fd);}
}
