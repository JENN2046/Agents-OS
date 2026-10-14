import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {generateKeyPairSync} from 'node:crypto';
import {exportPublicKey} from '../src/lease-core.mjs';
import {PUBLISHER_UNIT,verifyPublisherServiceOrigin,
  readPublisherPrivateKeys} from '../release/publisher-credential.mjs';

const pair=()=>generateKeyPairSync('ed25519').privateKey;
function fixture(){
 const a=pair(),b=pair();
 const directory='/run/credentials/'+PUBLISHER_UNIT;
 const mount='20 13 0:20 / '+directory+' ro,nosuid,nodev - tmpfs tmpfs ro\n';
 const cgroup='0::/system.slice/'+PUBLISHER_UNIT+'\n';
 const privateBytes=[
  a.export({format:'der',type:'pkcs8'}),
  b.export({format:'der',type:'pkcs8'})
 ];
 const files=['release-signing-key','enrollment-signing-key'];
 const stats={
  '/run':{uid:0,mode:0o40755,isDirectory:()=>true,isSymbolicLink:()=>false},
  '/run/credentials':{uid:0,mode:0o40755,isDirectory:()=>true,isSymbolicLink:()=>false},
  [directory]:{uid:0,dev:92,mode:0o40500,isDirectory:()=>true,isSymbolicLink:()=>false}
 };
 const meta=privateBytes.map(bytes=>({uid:0,dev:92,nlink:1,mode:0o100400,size:bytes.length,isFile:()=>true}));
 const opened=[];
 const io={
  readFileSync:(x)=>typeof x==='number'?Buffer.from(privateBytes[x-70]):x==='/proc/self/cgroup'?cgroup:mount,
  lstatSync:path=>{assert.ok(Object.hasOwn(stats,path),'Unexpected stat '+path);return stats[path];},
  openSync:(path,flags)=>{
   assert.ok((flags&fs.constants.O_NOFOLLOW)!==0);
   const n=files.findIndex(name=>path===directory+'/'+name);
   assert.ok(n>=0);
   opened.push(n+70);return n+70;
  },
  fstatSync:fd=>meta[fd-70],
  closeSync:()=>{},
 };
 const args={io,euid:0,argv:['/usr/bin/node','/usr/lib/minimal-human-trust/release/publisher-bootstrap.mjs'],
  expectedReleaseKey:exportPublicKey(a),expectedEnrollmentKey:exportPublicKey(b)};
 return {a,b,args,opened,meta};
}
const reject=f=>assert.throws(f,{code:'PUBLISHER_CREDENTIAL_REJECTED'});
test('only exact root-owned systemd service may use private signing credentials',()=>{
 const f=fixture(),p=readPublisherPrivateKeys(f.args);
 assert.equal(exportPublicKey(p.releaseSigningKey),f.args.expectedReleaseKey);
 assert.equal(exportPublicKey(p.enrollmentSigningKey),f.args.expectedEnrollmentKey);
 assert.deepEqual(f.opened,[70,71]);
});
test('fake cgroup, duplicate unified process membership and non-root all fail closed',()=>{
 for(const data of [
  {euid:1000},{cgroup:'0::/user.slice/'+PUBLISHER_UNIT},
  {cgroup:'0::/system.slice/r16-owner.service'},
  {cgroup:'0::/system.slice/'+PUBLISHER_UNIT+'\n0::/system.slice/'+PUBLISHER_UNIT},
  {argv:['/usr/bin/node','/usr/lib/test','--key=/tmp/evil']}
 ]){
  const f=fixture();reject(()=>readPublisherPrivateKeys({...f.args,...data}));
 }
});
test('encrypted root keys are never accepted from caller supplied public key',()=>{
 const f=fixture();reject(()=>readPublisherPrivateKeys({
  ...f.args,expectedReleaseKey:exportPublicKey(pair())}));
});
test('enrollment and release signing identities must be independent',()=>{
 const f=fixture();reject(()=>readPublisherPrivateKeys({
  ...f.args,expectedEnrollmentKey:f.args.expectedReleaseKey}));
});
test('missing read-only tmpfs mount cannot become a credential',()=>{
 for(const mountinfo of ['', '20 13 0:20 / /run/credentials/'+PUBLISHER_UNIT+' rw - tmpfs tmpfs rw',
  '20 13 0:20 / /run/credentials/'+PUBLISHER_UNIT+' ro - ext4 /dev/sda ro']){
  const f=fixture();reject(()=>verifyPublisherServiceOrigin({...f.args,mountinfo}));
 }
});
test('different mount device, weak file mode or hardlink is rejected',()=>{
 for(const mutate of [s=>s.dev=4,s=>s.nlink=2,s=>s.mode=0o100660]){
  const f=fixture();mutate(f.meta[1]);
  reject(()=>readPublisherPrivateKeys(f.args));
 }
});
test('environment path override cannot redirect the systemd credentials',()=>{
 const f=fixture(),prior=process.env.CREDENTIALS_DIRECTORY;
 process.env.CREDENTIALS_DIRECTORY='/tmp/attacker';
 try{
  const p=readPublisherPrivateKeys(f.args);
  assert.equal(exportPublicKey(p.releaseSigningKey),f.args.expectedReleaseKey);
 }finally{
  if(prior===undefined)delete process.env.CREDENTIALS_DIRECTORY;
  else process.env.CREDENTIALS_DIRECTORY=prior;
 }
});
test('additional argv are rejected before any private key is read',()=>{
 const f=fixture();reject(()=>verifyPublisherServiceOrigin({
  ...f.args,argv:['node','publisher','extra']}));
});
