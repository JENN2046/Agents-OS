import {test} from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {verifyIssuerSystemdCredentialOrigin} from '../src/systemd-issuer-credential.mjs';
const gate=()=>{const service='minimal-human-trust-issuer@123.service';
 const dir='/run/credentials/'+service;
 const flags={dir:true,file:false,link:false,uid:0,dev:13,mode:0o700,nlink:1,size:0};
 const cred={...flags,dir:false,file:true,mode:0o400,size:52};
 const stats={'/run':{...flags},'/run/credentials':{...flags},[dir]:{...flags},[dir+'/issuer-signing-key']:{...cred}};
 const binary=Buffer.alloc(52,0x3b);
 const io={
   readFileSync:p=>typeof p==='number'?Buffer.from(binary):p==='/proc/self/cgroup'?'0::/system.slice/'+service:
     p==='/proc/self/mountinfo'?'40 29 0:11 / '+dir+' ro,nosuid - tmpfs tmpfs ro\n':'',
   lstatSync:p=>{const s=stats[p];if(!s)throw Error('ENOENT');return {uid:s.uid,mode:s.mode,dev:s.dev,
     isDirectory:()=>s.dir,isSymbolicLink:()=>s.link};},
   openSync:(p,fl)=>{assert.equal(p,dir+'/issuer-signing-key');assert.ok(fl&fs.constants.O_NOFOLLOW);return 19;},
   fstatSync:n=>{assert.equal(n,19);const s=stats[dir+'/issuer-signing-key'];
     return {uid:s.uid,mode:s.mode,dev:s.dev,size:s.size,nlink:s.nlink,isFile:()=>s.file};},
   closeSync:n=>{assert.equal(n,19);},
 };
 return {service,dir,stats,binary,io};
};
const reject=f=>assert.throws(f,{code:'CREDENTIAL_PROVENANCE_REJECTED'});
test('kernel cgroup and read-only tmpfs bind the exact privileged credential',()=>{
 const f=gate(),res=verifyIssuerSystemdCredentialOrigin({io:f.io,euid:0});
 assert.equal(res.lane,'issuer');assert.equal(res.unit,f.service);assert.deepEqual(res.credentialBytes,f.binary);
});
test('human lane is derived from cgroup, not caller input',()=>{
 const f=gate(),name='minimal-human-trust-human@12.service',dir='/run/credentials/'+name;
 f.stats[dir]={...f.stats[f.dir]};f.stats[dir+'/issuer-signing-key']={...f.stats[f.dir+'/issuer-signing-key']};
 f.io.readFileSync=p=>typeof p==='number'?Buffer.from(f.binary):p==='/proc/self/cgroup'?'0::/system.slice/'+name:
   p==='/proc/self/mountinfo'?'40 29 0:11 / '+dir+' ro,nosuid - tmpfs tmpfs ro\n':'';
 f.io.openSync=(p)=>{assert.equal(p,dir+'/issuer-signing-key');return 19;};
 f.io.fstatSync=()=>{const s=f.stats[dir+'/issuer-signing-key'];return {uid:s.uid,mode:s.mode,dev:s.dev,size:s.size,nlink:s.nlink,isFile:()=>s.file};};
 assert.equal(verifyIssuerSystemdCredentialOrigin({io:f.io,euid:0}).lane,'human');
});
test('non-root cannot impersonate system service',()=>{
 const f=gate();reject(()=>verifyIssuerSystemdCredentialOrigin({io:f.io,euid:1000}));
});
for(const [name,cgroup] of [
 ['non-system unit','0::/user.slice/minimal-human-trust-issuer@123.service'],
 ['legacy Owner unit','0::/system.slice/r16-owner.service'],
 ['duplicated cgroup','0::/system.slice/minimal-human-trust-issuer@123.service\n0::/system.slice/minimal-human-trust-issuer@123.service']]){
 test('rejects '+name,()=>{const f=gate();reject(()=>verifyIssuerSystemdCredentialOrigin({io:f.io,euid:0,cgroup}));});
}
for(const [name,line] of [
 ['missing real mount',''],['regular disk','40 29 0:11 / PLACE ro,nosuid - ext4 /dev/sda ro'],
 ['writable tmpfs','40 29 0:11 / PLACE rw,nosuid - tmpfs tmpfs rw'],
 ['duplicated mount','40 29 0:11 / PLACE ro,nosuid - tmpfs tmpfs ro\n40 29 0:11 / PLACE ro,nosuid - tmpfs tmpfs ro']]){
 test('rejects '+name,()=>{const f=gate();reject(()=>verifyIssuerSystemdCredentialOrigin({
 io:f.io,euid:0,mountinfo:line.replaceAll('PLACE',f.dir)}));});
}
for(const [name,alter] of [
 ['symlinked credential directory',f=>{f.stats[f.dir].link=true;}],
 ['group-writable parent',f=>{f.stats['/run/credentials'].mode=0o775;}],
 ['foreign-owned credential',f=>{f.stats[f.dir+'/issuer-signing-key'].uid=1000;}],
 ['hardlink credential',f=>{f.stats[f.dir+'/issuer-signing-key'].nlink=2;}],
 ['wrong credential device',f=>{f.stats[f.dir+'/issuer-signing-key'].dev=999;}],
 ['oversized credential',f=>{f.stats[f.dir+'/issuer-signing-key'].size=5000;}],
 ['weak credential mode',f=>{f.stats[f.dir+'/issuer-signing-key'].mode=0o660;}]]){
 test('rejects '+name,()=>{const f=gate();alter(f);reject(()=>verifyIssuerSystemdCredentialOrigin({io:f.io,euid:0}));});
}
test('CREDENTIALS_DIRECTORY cannot redirect a kernel-bound path',()=>{
 const f=gate(),old=process.env.CREDENTIALS_DIRECTORY;
 process.env.CREDENTIALS_DIRECTORY='/tmp/attacker';
 try{assert.equal(verifyIssuerSystemdCredentialOrigin({io:f.io,euid:0}).unit,f.service);}
 finally{if(old===undefined)delete process.env.CREDENTIALS_DIRECTORY;else process.env.CREDENTIALS_DIRECTORY=old;}
});
