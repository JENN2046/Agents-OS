// FIRST_TRUST_BOOTSTRAP_R1: protected root publisher credential provenance.
// No arbitrary environment credential path, unit name, key filename or fallback.
import fs from 'node:fs';
import {createPrivateKey} from 'node:crypto';
import {exportPublicKey} from '../src/lease-core.mjs';

export const PUBLISHER_UNIT='minimal-human-trust-publisher.service';
const DIR='/run/credentials/'+PUBLISHER_UNIT;
const NAMES=Object.freeze(['release-signing-key','enrollment-signing-key']);
const reject=()=>{throw Object.assign(new Error('PUBLISHER_CREDENTIAL_REJECTED'),{code:'PUBLISHER_CREDENTIAL_REJECTED'});};
const requireThat=v=>{if(!v)reject();};
const parentStat=(io,p)=>{
 const s=io.lstatSync(p);
 requireThat(s.isDirectory()&&!s.isSymbolicLink()&&s.uid===0&&!(s.mode&0o022));
 return s;
};
export function verifyPublisherServiceOrigin({
 io=fs,euid=process.geteuid(),argv=process.argv,
 cgroup=undefined,mountinfo=undefined,
}={}){
 requireThat(euid===0&&Array.isArray(argv)&&argv.length===2);
 const cg=cgroup??io.readFileSync('/proc/self/cgroup','utf8');
 requireThat(typeof cg==='string'&&cg.length<=8192);
 const unified=cg.trim().split('\n').map(line=>line.split(':'));
 requireThat(unified.length>=1&&unified.every(row=>row.length===3));
 const relevant=unified.filter(row=>row[0]==='0'&&row[1]==='');
 requireThat(relevant.length===1&&relevant[0][2]==='/system.slice/'+PUBLISHER_UNIT);
 const info=mountinfo??io.readFileSync('/proc/self/mountinfo','utf8');
 requireThat(typeof info==='string'&&info.length<4*1024*1024);
 const rows=info.trim().split('\n').map(s=>s.split(' ')).filter(row=>row[4]===DIR);
 requireThat(rows.length===1);
 const row=rows[0],sep=row.indexOf('-');
 requireThat(sep>5&&row[5].split(',').includes('ro')&&['tmpfs','ramfs'].includes(row[sep+1]));
 parentStat(io,'/run');
 parentStat(io,'/run/credentials');
 const dir=parentStat(io,DIR);
 return {directory:DIR,dev:dir.dev};
}
function bytesFromMountedCredential(io,name,dev){
 requireThat(NAMES.includes(name));
 let fd;
 try{fd=io.openSync(DIR+'/'+name,fs.constants.O_RDONLY|fs.constants.O_NOFOLLOW);}
 catch{reject();}
 try{
  const st=io.fstatSync(fd);
  requireThat(st.isFile()&&st.uid===0&&st.nlink===1&&st.dev===dev&&
    [0o400,0o440].includes(st.mode&0o7777)&&st.size>0&&st.size<=4096);
  const bytes=io.readFileSync(fd);
  requireThat(Buffer.isBuffer(bytes)&&bytes.length===st.size);
  return bytes;
 }finally{io.closeSync(fd);}
}
export function readPublisherPrivateKeys({
 io=fs,euid=process.geteuid(),argv=process.argv,
 cgroup=undefined,mountinfo=undefined,expectedReleaseKey,expectedEnrollmentKey
}={}){
 const {dev}=verifyPublisherServiceOrigin({io,euid,argv,cgroup,mountinfo});
 requireThat(typeof expectedReleaseKey==='string'&&typeof expectedEnrollmentKey==='string'&&
   expectedReleaseKey!==expectedEnrollmentKey);
 const parse=(name,expected)=>{
  const bytes=bytesFromMountedCredential(io,name,dev);
  try{
   const key=createPrivateKey({key:bytes,format:'der',type:'pkcs8'});
   requireThat(key.type==='private'&&key.asymmetricKeyType==='ed25519'&&
     exportPublicKey(key)===expected);
   return key;
  }finally{bytes.fill(0);}
 };
 const releaseSigningKey=parse(NAMES[0],expectedReleaseKey);
 const enrollmentSigningKey=parse(NAMES[1],expectedEnrollmentKey);
 return Object.freeze({releaseSigningKey,enrollmentSigningKey});
}
