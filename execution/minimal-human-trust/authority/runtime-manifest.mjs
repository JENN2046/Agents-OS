import fs from 'node:fs';
import path from 'node:path';
import {createHash} from 'node:crypto';
const reject=()=>{throw new Error('R16_RELEASE_REJECTED');};
const canonical=x=>x===null||typeof x!=='object'?JSON.stringify(x):Array.isArray(x)?'['+x.map(canonical).join(',')+']':'{'+Object.keys(x).sort().map(k=>JSON.stringify(k)+':'+canonical(x[k])).join(',')+'}';
export function validateRuntimeManifest(m,role){
 if(!m||Object.getPrototypeOf(m)!==Object.prototype||Object.keys(m).sort().join(',')!=='entry,files,role,schema'||m.schema!=='r16.runtime-code.v1'||!['app','bridge','native'].includes(m.role)||(role&&m.role!==role)||!m.files||Object.getPrototypeOf(m.files)!==Object.prototype||Object.keys(m.files).length===0||Object.keys(m.files).length>100000||typeof m.entry!=='string'||!Object.hasOwn(m.files,m.entry))reject();
 for(const [name,hash]of Object.entries(m.files))if(!name||name.length>4096||path.isAbsolute(name)||name.includes('\\')||name.includes('\0')||name.split('/').some(p=>!p||p==='.'||p==='..')||['__proto__','constructor','prototype'].includes(name)||typeof hash!=='string'||!/^[a-f0-9]{64}$/.test(hash))reject();
 return m;
}
export function runtimeVersion(m,role){validateRuntimeManifest(m,role);return createHash('sha256').update(canonical(m)).digest('hex');}
export function protectedRuntimeFile(filename){
 if(!path.isAbsolute(filename)||path.resolve(filename)!==filename)reject();let current='/';for(const part of filename.split('/').filter(Boolean)){current=path.join(current,part);const s=fs.lstatSync(current);if(s.isSymbolicLink()||s.uid!==0||(s.mode&0o022))reject();}
 const fd=fs.openSync(filename,fs.constants.O_RDONLY|fs.constants.O_NOFOLLOW);try{const s=fs.fstatSync(fd);if(!s.isFile()||s.nlink!==1||s.size>64*1024*1024)reject();return fs.readFileSync(fd);}finally{fs.closeSync(fd);}
}
export function verifyInstalledManifest(m,directory,{role,readFile=protectedRuntimeFile}={}){validateRuntimeManifest(m,role);if(!path.isAbsolute(directory)||path.resolve(directory)!==directory)reject();for(const [name,expected]of Object.entries(m.files)){const actual=createHash('sha256').update(readFile(path.join(directory,name))).digest('hex');if(actual!==expected)reject();}return runtimeVersion(m,role);}