import fs from 'node:fs';
import path from 'node:path';
import os from 'node:os';
import {createHash} from 'node:crypto';
import {spawnSync} from 'node:child_process';

export const ROOT='/usr/lib/r16-maintenance/recovery-r6';
export const STATE='/var/lib/r16-maintenance/recovery-r6';
export const UNIT='r16-native-recovery-maintenance-r6.service';
export const canonical=x=>x===null||typeof x!=='object'?JSON.stringify(x):Array.isArray(x)?'['+x.map(canonical).join(',')+']':'{'+Object.keys(x).sort().map(k=>JSON.stringify(k)+':'+canonical(x[k])).join(',')+'}';
export const sha=x=>createHash('sha256').update(x).digest('hex');
export const digest=x=>sha(canonical(x));
export const same=(a,b)=>canonical(a)===canonical(b);
export function need(ok,code){if(!ok)throw Object.assign(Error(code),{code});}
export function safeRelative(s){need(typeof s==='string'&&!path.isAbsolute(s)&&!s.includes('\\')&&!s.includes('\0')&&s.split('/').every(p=>p&&p!=='.'&&p!=='..'),'UNSAFE_RELATIVE_PATH');return s;}
export function protectedBytes(file,{uid=process.geteuid(),max=32*1024*1024}={}){
  need(path.resolve(file)===file,'PROTECTED_PATH_INVALID');
  let p='/';for(const bit of file.split('/').filter(Boolean)){p=path.join(p,bit);const st=fs.lstatSync(p);need(!st.isSymbolicLink()&&!(st.mode&0o022)&&(p===file?st.uid===uid:(st.uid===0||st.uid===uid)),'PROTECTED_PATH_UNSAFE');}
  const fd=fs.openSync(file,fs.constants.O_RDONLY|fs.constants.O_NOFOLLOW);
  try{const a=fs.fstatSync(fd);need(a.isFile()&&a.nlink===1&&a.uid===uid&&a.size<=max,'PROTECTED_FILE_INVALID');const b=fs.readFileSync(fd),z=fs.fstatSync(fd);need(b.length===a.size&&a.ino===z.ino&&a.dev===z.dev&&a.mtimeMs===z.mtimeMs&&a.ctimeMs===z.ctimeMs,'PROTECTED_FILE_CHANGED');return b;}finally{fs.closeSync(fd);}
}
export const json=file=>JSON.parse(protectedBytes(file));
export function syncDir(dir){const fd=fs.openSync(dir,fs.constants.O_RDONLY|fs.constants.O_DIRECTORY|fs.constants.O_NOFOLLOW);try{fs.fsyncSync(fd);}finally{fs.closeSync(fd);}}
export function atomicBytes(file,raw,mode=0o600){
  const dir=path.dirname(file);protectedDirectory(dir);
  try{protectedBytes(file);}catch(e){if(e.code!=='ENOENT')throw e;}
  const tmp=file+'.next-'+sha(raw);
  // A crash before rename leaves only candidate bytes. Reconcile exact bytes;
  // never delete an unrelated pending file or overwrite it blindly.
  let fd;try{
    fd=fs.openSync(tmp,fs.constants.O_WRONLY|fs.constants.O_CREAT|fs.constants.O_EXCL|fs.constants.O_NOFOLLOW,mode);fs.writeFileSync(fd,raw);fs.fchmodSync(fd,mode);fs.fsyncSync(fd);
  }catch(e){
    if(e.code!=='EEXIST')throw e;
    const prefix=protectedBytes(tmp);need(prefix.length<=raw.length&&prefix.equals(raw.subarray(0,prefix.length)),'PENDING_FILE_CONFLICT');
    fd=fs.openSync(tmp,fs.constants.O_WRONLY|fs.constants.O_NOFOLLOW);const st=fs.fstatSync(fd);need(st.isFile()&&st.nlink===1&&st.uid===process.geteuid()&&st.size===prefix.length,'PENDING_FILE_CHANGED');
    let offset=prefix.length;while(offset<raw.length)offset+=fs.writeSync(fd,raw,offset,raw.length-offset,offset);fs.fchmodSync(fd,mode);fs.fsyncSync(fd);
  }finally{if(fd!==undefined)fs.closeSync(fd);}
  fs.renameSync(tmp,file);syncDir(dir);
}
export const atomicJson=(file,value,mode=0o600)=>atomicBytes(file,Buffer.from(canonical(value)+'\n'),mode);
export function protectedDirectory(dir){
  let cursor='/';for(const part of dir.split('/').filter(Boolean)){cursor=path.join(cursor,part);const s=fs.lstatSync(cursor);need(s.isDirectory()&&!s.isSymbolicLink()&&(s.uid===0||s.uid===process.geteuid())&&!(s.mode&0o022),'PROTECTED_DIRECTORY_INVALID');}
}
export function immutableJson(file,value){try{need(same(json(file),value),'JOURNAL_CONFLICT');}catch(e){if(e.code!=='ENOENT')throw e;atomicJson(file,value);}}
export function rootContext(host='jenn-System-Product-Name',service=true){
  need(process.getuid()===0&&process.geteuid()===0&&os.hostname()===host,'FIXED_ROOT_HOST_REQUIRED');
  if(service){need(process.argv.length===2,'FIXED_SERVICE_ARGUMENTS_REQUIRED');need(fs.readFileSync('/proc/self/cgroup','utf8').trim().split('\n').some(l=>l.split(':')[2]==='/system.slice/'+UNIT),'FIXED_SERVICE_CGROUP_REQUIRED');}
}
export function verifyCapsule(plan){
  const raw=protectedBytes(ROOT+'/SOURCE_FREEZE.json'),capsule=JSON.parse(raw);
  need(sha(raw)===plan.capsuleHash&&plan.sourceFreezeHash===plan.capsuleHash&&capsule.schema==='r16.native-recovery-source-freeze.v3','CAPSULE_HASH_DRIFT');
  const files={};for(const [name,h]of Object.entries(capsule.files)){safeRelative(name);const file=ROOT+'/'+name;need(sha(protectedBytes(file))===h,'SOURCE_FREEZE_DRIFT');files[file]=h;}
  return {capsule,files};
}
export function command(file,args,input,timeout=30000){
  const r=spawnSync(file,args,{input:input===undefined?undefined:Buffer.from(canonical(input)),encoding:'utf8',timeout,maxBuffer:16*1024*1024,env:{PATH:'/usr/bin:/bin',LANG:'C'},stdio:['pipe','pipe','ignore']});
  // A terminated SSH client does not establish whether its remote stage ended.
  // Never accept partial JSON as success after the child deadline was exceeded.
  need(r.error?.code!=='ETIMEDOUT','FIXED_COMMAND_TIMEOUT');
  let value;try{value=JSON.parse(r.stdout);}catch{}
  if(r.status!==0)need(false,typeof value?.code==='string'&&/^[A-Z0-9_]{1,80}$/.test(value.code)?value.code:'FIXED_COMMAND_FAILED');
  need(value&&typeof value==='object'&&!Array.isArray(value),'FIXED_COMMAND_RESPONSE_INVALID');return value;
}
export function locked(file,fn){
  const fd=fs.openSync(file,fs.constants.O_RDWR|fs.constants.O_CREAT|fs.constants.O_NOFOLLOW,0o600);
  try{const s=fs.fstatSync(fd);need(s.isFile()&&s.uid===process.geteuid()&&s.nlink===1&&(s.mode&0o7777)===0o600,'LOCK_INVALID');const r=spawnSync('/usr/bin/flock',['-n','3'],{stdio:['ignore','ignore','ignore',fd],env:{PATH:'/usr/bin:/bin'}});need(r.status===0,'MAINTENANCE_BUSY');return Promise.resolve(fn()).finally(()=>fs.closeSync(fd));}catch(e){fs.closeSync(fd);throw e;}
}
