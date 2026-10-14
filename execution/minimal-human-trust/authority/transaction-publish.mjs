import fs from 'node:fs';
import path from 'node:path';
import {createHash} from 'node:crypto';
const fail=()=>{throw Error('PUBLISH_STATE_UNCERTAIN');};
function read(file){const fd=fs.openSync(file,fs.constants.O_RDONLY|fs.constants.O_NOFOLLOW);try{const s=fs.fstatSync(fd);if(!s.isFile()||s.uid!==process.geteuid()||(s.mode&0o777)!==0o600||s.nlink!==1||s.size>96*1024*1024)fail();return fs.readFileSync(fd);}finally{fs.closeSync(fd);}}
function syncDir(dir){const fd=fs.openSync(dir,fs.constants.O_DIRECTORY);try{fs.fsyncSync(fd);}finally{fs.closeSync(fd);}}
function create(file,data){const fd=fs.openSync(file,fs.constants.O_WRONLY|fs.constants.O_CREAT|fs.constants.O_EXCL|fs.constants.O_NOFOLLOW,0o600);try{fs.writeFileSync(fd,data);fs.fsyncSync(fd);}finally{fs.closeSync(fd);}syncDir(path.dirname(file));}
export function pendingTransaction(file){if(!fs.existsSync(file))return null;const t=JSON.parse(read(file));if(t.schema!=='r16.encrypted-publish.v1'||!Array.isArray(t.targets)||!t.targets.length)fail();return t;}
export function publishTransaction({file,binding,targets,result,fault=()=>{}}){
 let t=pendingTransaction(file);
 if(!t){if(targets.some(x=>fs.existsSync(x.path)))fail();t={schema:'r16.encrypted-publish.v1',binding,targets:targets.map(x=>({path:x.path,bytes:Buffer.from(x.bytes).toString('base64'),sha256:createHash('sha256').update(x.bytes).digest('hex')})),result};create(file,Buffer.from(JSON.stringify(t)));fault('after_transaction');}
 if(t.binding!==binding)fail();
 for(const [index,target]of t.targets.entries()){
  if(!path.isAbsolute(target.path)||path.resolve(target.path)!==target.path)fail();const bytes=Buffer.from(target.bytes,'base64');if(createHash('sha256').update(bytes).digest('hex')!==target.sha256)fail();
  if(fs.existsSync(target.path)){if(!read(target.path).equals(bytes))fail();}else create(target.path,bytes);
  fault('after_target_'+index);
 }
 return t.result;
}