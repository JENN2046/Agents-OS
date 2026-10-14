// Only the existing Release key, only this fixed systemd oneshot credential mount.
import fs from 'node:fs';
import {createPrivateKey} from 'node:crypto';
import {exportPublicKey,publicKey} from '../src/lease-core.mjs';
export const HUMAN_PROPOSAL_UNIT='minimal-human-trust-proposal.service';
const DIRECTORY='/run/credentials/'+HUMAN_PROPOSAL_UNIT;
const need=x=>{if(!x)throw Object.assign(Error('HUMAN_PROPOSAL_CREDENTIAL_REFUSED'),{code:'HUMAN_PROPOSAL_CREDENTIAL_REFUSED'});};
export function readHumanProposalReleaseKey({io=fs,euid=process.geteuid(),argv=process.argv,
 cgroup=undefined,mountinfo=undefined,expectedReleaseKey}={}){
 need(euid===0&&Array.isArray(argv)&&argv.length===2);
 const cg=cgroup??io.readFileSync('/proc/self/cgroup','utf8');
 need(typeof cg==='string'&&cg.length<=8192);
 const rows=cg.trim().split('\n').map(s=>s.split(':'));
 need(rows.every(r=>r.length===3));
 const unified=rows.filter(r=>r[0]==='0'&&r[1]==='');
 need(unified.length===1&&unified[0][2]==='/system.slice/'+HUMAN_PROPOSAL_UNIT);
 const info=mountinfo??io.readFileSync('/proc/self/mountinfo','utf8');
 need(typeof info==='string'&&info.length<4*1024*1024);
 const found=info.trim().split('\n').map(s=>s.split(' ')).filter(r=>r[4]===DIRECTORY);
 const sep=found[0]?.indexOf('-');
 need(found.length===1&&sep>5&&found[0][5].split(',').includes('ro')&&
   ['tmpfs','ramfs'].includes(found[0][sep+1]));
 let directoryStat;
 for(const p of ['/run','/run/credentials',DIRECTORY]){
   const st=io.lstatSync(p);need(st.isDirectory()&&!st.isSymbolicLink()&&st.uid===0&&!(st.mode&0o022));directoryStat=st;
 }
 need(typeof expectedReleaseKey==='string'&&
   publicKey(expectedReleaseKey).export({format:'der',type:'spki'}).toString('base64url')===expectedReleaseKey);
 const fd=io.openSync(DIRECTORY+'/release-signing-key',fs.constants.O_RDONLY|fs.constants.O_NOFOLLOW);
 let bytes;
 try{
   const st=io.fstatSync(fd);need(st.isFile()&&st.uid===0&&st.nlink===1&&st.dev===directoryStat.dev&&
     [0o400,0o440].includes(st.mode&0o7777)&&st.size>0&&st.size<=4096);
   bytes=io.readFileSync(fd);need(Buffer.isBuffer(bytes)&&bytes.length===st.size);
   const after=io.fstatSync(fd);need(st.dev===after.dev&&st.ino===after.ino&&st.size===after.size&&
     st.mtimeMs===after.mtimeMs&&st.ctimeMs===after.ctimeMs);
   const key=createPrivateKey({key:bytes,format:'der',type:'pkcs8'});
   need(key.asymmetricKeyType==='ed25519'&&exportPublicKey(key)===expectedReleaseKey);return key;
 }finally{if(Buffer.isBuffer(bytes))bytes.fill(0);io.closeSync(fd);}
}
