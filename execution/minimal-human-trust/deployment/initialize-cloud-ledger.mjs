// Root-only initial ledger registration. A sealed registration is never reset.
import fs from 'node:fs';
import path from 'node:path';
import {digest,canonical,ProtectedStore} from '../src/lease-core.mjs';
const check=x=>{if(!x)throw Error('CLOUD_LEDGER_REFUSED');};
const initial={
 app:{kind:'r16.app-workspace.v1',projects:[],allocations:[],operations:[],status:'native_offline'},
 bridge:{kind:'r16.workspace-bridge.v1',projects:[],approvals:[],calls:[],routes:[],challenge:null,version:0,revoked:false},
 gateway:{kind:'r16.transport.v1',generation:0,origin:null,nonces:[],retired:[],late:[]},
};
function protectedDirectory(p,uid=0,mode=0o700){const s=fs.lstatSync(p);check(s.isDirectory()&&!s.isSymbolicLink()&&s.uid===uid&&(s.mode&0o777)===mode);return s;}
function sync(dir){const fd=fs.openSync(dir,fs.constants.O_DIRECTORY|fs.constants.O_NOFOLLOW);try{fs.fsyncSync(fd);}finally{fs.closeSync(fd);}}
function write(file,body){const temp=file+'.pending-'+process.pid;const fd=fs.openSync(temp,fs.constants.O_CREAT|fs.constants.O_EXCL|fs.constants.O_WRONLY|fs.constants.O_NOFOLLOW,0o600);try{fs.writeFileSync(fd,canonical(body));fs.fsyncSync(fd);}finally{fs.closeSync(fd);}fs.renameSync(temp,file);sync(path.dirname(file));}
function read(file){const fd=fs.openSync(file,fs.constants.O_RDONLY|fs.constants.O_NOFOLLOW);try{const s=fs.fstatSync(fd);check(s.isFile()&&s.uid===0&&s.nlink===1&&(s.mode&0o777)===0o600&&s.size<32768);return JSON.parse(fs.readFileSync(fd));}finally{fs.closeSync(fd);}}
export function initializeCloudLedgers(grantId,{root='/',uid=1000,gid=1000,fault=()=>{}}={}){
 check(process.geteuid()===0&&typeof grantId==='string'&&/^[A-Za-z0-9_-]{1,128}$/.test(grantId));
 const at=p=>path.join(root,p),registry=at('/var/lib/r16-cloud/ledger-registry');protectedDirectory(registry);
 const file=path.join(registry,digest(grantId)+'.json');
 const specs=[{role:'app',path:at('/var/lib/r16-app/grants/'+grantId+'/host')},{role:'bridge',path:at('/var/lib/r16-bridge/grants/'+grantId+'/bridge')},{role:'gateway',path:at('/var/lib/r16-bridge/grants/'+grantId+'/gateway')}];
 let record=fs.existsSync(file)?read(file):null;
 if(record){check(record.schema==='r16.cloud-ledger-registration.v1'&&record.grantId===grantId&&['PREPARING','SEALED'].includes(record.phase)&&canonical(record.specs)===canonical(specs));}
 else{for(const s of specs)check(!fs.existsSync(s.path));record={schema:'r16.cloud-ledger-registration.v1',grantId,phase:'PREPARING',specs,identities:[]};write(file,record);fault('registered');}
 if(record.phase==='SEALED'){
  for(const s of specs){const stat=protectedDirectory(s.path,uid);const binding=record.identities.find(x=>x.role===s.role);check(binding&&stat.dev===binding.dev&&stat.ino===binding.ino);const fd=fs.openSync(path.join(s.path,'state.json'),fs.constants.O_RDONLY|fs.constants.O_NOFOLLOW);try{const v=fs.fstatSync(fd);check(v.isFile()&&v.uid===uid&&v.nlink===1&&(v.mode&0o777)===0o600);}finally{fs.closeSync(fd);}}
  return {initialized:true,existing:true};
 }
 const identities=[];
 for(const s of specs){
  const grants=path.dirname(path.dirname(s.path));protectedDirectory(grants,uid);
  const parent=path.dirname(s.path);if(!fs.existsSync(parent)){fs.mkdirSync(parent,{mode:0o700});sync(grants);}const ps=fs.lstatSync(parent);check(ps.isDirectory()&&!ps.isSymbolicLink()&&[0,uid].includes(ps.uid)&&(ps.mode&0o777)===0o700);
  if(!fs.existsSync(s.path)){const store=new ProtectedStore({directory:s.path,create:true,initial:initial[s.role]});store.close();fault('created_'+s.role);}
  const stat=fs.lstatSync(s.path);check(stat.isDirectory()&&!stat.isSymbolicLink()&&[0,uid].includes(stat.uid)&&(stat.mode&0o777)===0o700);
  check(canonical(fs.readdirSync(s.path).sort())===canonical(['state.json']));
  const state=path.join(s.path,'state.json'),fd=fs.openSync(state,fs.constants.O_RDONLY|fs.constants.O_NOFOLLOW);try{const ss=fs.fstatSync(fd);check(ss.isFile()&&[0,uid].includes(ss.uid)&&ss.nlink===1&&(ss.mode&0o777)===0o600);check(canonical(JSON.parse(fs.readFileSync(fd)))===canonical({schema:1,revision:0,maxNow:0,data:initial[s.role]}));}finally{fs.closeSync(fd);}
  fs.chownSync(state,uid,gid);fs.chownSync(s.path,uid,gid);fs.chownSync(parent,uid,gid);sync(s.path);sync(parent);identities.push({role:s.role,dev:stat.dev,ino:stat.ino});fault('owned_'+s.role);
 }
 record={...record,phase:'SEALED',identities};write(file,record);return {initialized:true,existing:false};
}