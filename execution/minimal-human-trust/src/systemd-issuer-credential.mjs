// G1-D: read and authenticate systemd's root credential mount, not any
// environment, caller-specified file, or synthetic "I am root" boolean.
// The privileged entrypoint invokes this with NO caller-controlled arguments.
import fs from 'node:fs';
import {createPrivateKey} from 'node:crypto';

const reject=()=>{throw Object.assign(new Error('CREDENTIAL_PROVENANCE_REJECTED'),
  {code:'CREDENTIAL_PROVENANCE_REJECTED'});};
const ensure=condition=>{if(!condition)reject();};
const UNIT=/^minimal-human-trust-(issuer|human)@[a-zA-Z0-9_-]{1,96}\.service$/;
const FILE='issuer-signing-key';
const statMode=s=>s.mode&0o777;
function unitFromCgroup(value){
  ensure(typeof value==='string'&&value.length<=8192);
  const rows=value.trim().split('\n').map(line=>line.split(':'));
  ensure(rows.length>=1);
  const found=rows.filter(row=>row.length===3&&row[0]==='0'&&row[1]==='').map(row=>row[2]);
  ensure(found.length===1);
  const components=found[0].split('/');
  const name=components.at(-1);
  ensure(UNIT.test(name)&&components.includes('system.slice'));
  return {name,lane:name.startsWith('minimal-human-trust-issuer@')?'issuer':'human'};
}
function secureStat(io,p){
  let s;
  try{s=io.lstatSync(p);}catch{reject();}
  ensure(s.isDirectory()&&!s.isSymbolicLink()&&s.uid===0&&!(s.mode&0o022));
  return s;
}
export function verifyIssuerSystemdCredentialOrigin({
  io=fs,euid=process.geteuid(),
  cgroup=undefined,mountinfo=undefined,
}={}){
  ensure(euid===0);
  const service=unitFromCgroup(cgroup??io.readFileSync('/proc/self/cgroup','utf8'));
  const name=service.name,dir='/run/credentials/'+name;
  const info=mountinfo??io.readFileSync('/proc/self/mountinfo','utf8');
  ensure(typeof info==='string'&&info.length<4*1024*1024);
  const mounts=info.trim().split('\n').map(line=>line.split(' ')).filter(parts=>parts[4]===dir);
  ensure(mounts.length===1);
  const parts=mounts[0],separator=parts.indexOf('-');
  ensure(separator>5&&parts[5].split(',').includes('ro')&&
    ['tmpfs','ramfs'].includes(parts[separator+1]));
  secureStat(io,'/run');
  secureStat(io,'/run/credentials');
  const dstat=secureStat(io,dir);
  let fd;
  try{fd=io.openSync(dir+'/'+FILE,fs.constants.O_RDONLY|fs.constants.O_NOFOLLOW);}
  catch{reject();}
  try{
    const st=io.fstatSync(fd);
    ensure(st.isFile()&&st.nlink===1&&st.uid===0&&
      [0o400,0o440].includes(statMode(st))&&st.dev===dstat.dev&&
      st.size>0&&st.size<=4096);
    const bytes=io.readFileSync(fd);
    ensure(Buffer.isBuffer(bytes)&&bytes.length===st.size);
    return {unit:name,lane:service.lane,credentialBytes:bytes};
  }finally{io.closeSync(fd);}
}
export function loadRootIssuerPrivateKey(){
  const proof=verifyIssuerSystemdCredentialOrigin();
  const bytes=proof.credentialBytes;
  try{
    const key=createPrivateKey({key:bytes,format:'der',type:'pkcs8'});
    ensure(key.type==='private'&&key.asymmetricKeyType==='ed25519');
    return {key,unit:proof.unit,lane:proof.lane};
  }finally{bytes.fill(0);}
}
