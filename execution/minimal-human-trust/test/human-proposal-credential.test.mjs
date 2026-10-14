import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {generateKeyPairSync,sign,verify} from 'node:crypto';
import {exportPublicKey} from '../src/lease-core.mjs';
import {HUMAN_PROPOSAL_UNIT,readHumanProposalReleaseKey} from '../release/human-proposal-credential.mjs';
const refuse=fn=>assert.throws(fn,{code:'HUMAN_PROPOSAL_CREDENTIAL_REFUSED'});
function fixture(){
 const privateKey=generateKeyPairSync('ed25519').privateKey;
 const privateBytes=privateKey.export({format:'der',type:'pkcs8'});
 const directory='/run/credentials/'+HUMAN_PROPOSAL_UNIT;
 const cgroup=`0::/system.slice/${HUMAN_PROPOSAL_UNIT}\n`;
 const mountinfo=`20 13 0:20 / ${directory} ro,nosuid,nodev - tmpfs tmpfs ro\n`;
 const stats={
  '/run':{uid:0,mode:0o40755,isDirectory:()=>true,isSymbolicLink:()=>false},
  '/run/credentials':{uid:0,mode:0o40755,isDirectory:()=>true,isSymbolicLink:()=>false},
  [directory]:{uid:0,dev:92,mode:0o40500,isDirectory:()=>true,isSymbolicLink:()=>false},
 };
 const meta={uid:0,dev:92,ino:77,nlink:1,mode:0o100400,size:privateBytes.length,
  mtimeMs:10,ctimeMs:20,isFile:()=>true};
 const opened=[],reads=[],closed=[],delivered=[];
 const io={lstatSync:file=>{assert.ok(Object.hasOwn(stats,file),'Unexpected directory '+file);return stats[file];},
  openSync:(file,flags)=>{
   assert.equal(file,directory+'/release-signing-key');
   assert.equal(flags,fs.constants.O_RDONLY|fs.constants.O_NOFOLLOW);opened.push(file);return 70;
  },fstatSync:fd=>{assert.equal(fd,70);return {...meta};},
  readFileSync:file=>{
   reads.push(file);
   if(file===70){const copy=Buffer.from(privateBytes);delivered.push(copy);return copy;}
   if(file==='/proc/self/cgroup')return cgroup;
   if(file==='/proc/self/mountinfo')return mountinfo;
   assert.fail('No alternate credential read '+file);
  },closeSync:fd=>closed.push(fd)};
 const args={io,euid:0,argv:['/usr/bin/node','/usr/lib/minimal-human-trust/release/human-proposal-bootstrap.mjs'],
  expectedReleaseKey:exportPublicKey(privateKey)};
 return {privateKey,privateBytes,directory,cgroup,mountinfo,stats,meta,opened,reads,closed,delivered,io,args};
}
test('only fixed root systemd credential supplies synthetic Ed25519 key, consumed bytes are wiped',()=>{
 const f=fixture(),key=readHumanProposalReleaseKey(f.args),body=Buffer.from('synthetic-disposable-test');
 assert.equal(exportPublicKey(key),f.args.expectedReleaseKey);
 assert.equal(verify(null,body,generateKeyPairSync('ed25519').publicKey,sign(null,body,key)),false);
 assert.equal(verify(null,body,key,sign(null,body,key)),true);
 assert.deepEqual(f.opened,[f.directory+'/release-signing-key']);assert.deepEqual(f.closed,[70]);
 assert.equal(f.delivered.length,1);assert.ok(f.delivered[0].every(b=>b===0));
});
test('nonroot, keypath argv and duplicate or wrong unit membership reject before private bytes',()=>{
 const f=fixture();for(const patch of [{euid:1000},{argv:['node','entry','--key=/tmp/attacker']},{argv:null},
  {cgroup:`0::/system.slice/minimal-human-trust-publisher.service`},
  {cgroup:`0::/user.slice/${HUMAN_PROPOSAL_UNIT}`},{cgroup:f.cgroup+f.cgroup},
  {cgroup:f.cgroup+'bad'},{cgroup:`0::/system.slice/${HUMAN_PROPOSAL_UNIT}/child`},
  {cgroup:''},{cgroup:'x'.repeat(8193)}]){
  refuse(()=>readHumanProposalReleaseKey({...f.args,...patch}));
 }
 assert.equal(f.opened.length,0);assert.equal(f.delivered.length,0);
});
test('caller expected public key cannot replace the admitted Release signing identity',()=>{
 const f=fixture();refuse(()=>readHumanProposalReleaseKey({...f.args,
  expectedReleaseKey:exportPublicKey(generateKeyPairSync('ed25519').privateKey)}));
 assert.ok(f.delivered[0].every(b=>b===0));assert.deepEqual(f.closed,[70]);
});
test('noncanonical and missing expected public keys reject before credential reads',()=>{
 for(const expectedReleaseKey of [undefined,'invalid','',null]){
  const f=fixture();assert.throws(()=>readHumanProposalReleaseKey({...f.args,expectedReleaseKey}));
  assert.equal(f.opened.length,0);
 }
 const f=fixture();refuse(()=>readHumanProposalReleaseKey({...f.args,
  expectedReleaseKey:f.args.expectedReleaseKey+'='}));assert.equal(f.opened.length,0);
});
test('credential mount requires unique exact read-only tmpfs or ramfs',()=>{
 for(const mountinfo of ['',`20 13 0:20 / ${fixture().directory} rw - tmpfs tmpfs rw`,
  `20 13 0:20 / ${fixture().directory} ro - ext4 /dev/sda ro`,
  fixture().mountinfo+fixture().mountinfo,
  `20 13 0:20 / /tmp/attacker ro - tmpfs tmpfs ro`]){
  const f=fixture();refuse(()=>readHumanProposalReleaseKey({...f.args,mountinfo}));assert.equal(f.opened.length,0);
 }
 const f=fixture();assert.equal(exportPublicKey(readHumanProposalReleaseKey({...f.args,
  mountinfo:f.mountinfo.replace(' - tmpfs tmpfs ',' - ramfs ramfs ')})),f.args.expectedReleaseKey);
});
test('writable, wrong-owner and symlinked credential ancestors reject before opening',()=>{
 for(const dir of ['/run','/run/credentials','credential'])for(const patch of [
  {uid:1000},{mode:0o40777},{isSymbolicLink:()=>true},{isDirectory:()=>false}]){
  const f=fixture();Object.assign(f.stats[dir==='credential'?f.directory:dir],patch);
  refuse(()=>readHumanProposalReleaseKey(f.args));assert.equal(f.opened.length,0);
 }
});
test('different credential device, writable modes, hardlinks, ownership and size refuse reading DER',()=>{
 for(const patch of [{dev:4},{nlink:2},{uid:1000},{mode:0o100600},{mode:0o100444},{mode:0o100660},
  {mode:0o104400},{size:0},{size:4097},{isFile:()=>false}]){
  const f=fixture();Object.assign(f.meta,patch);refuse(()=>readHumanProposalReleaseKey(f.args));
  assert.equal(f.delivered.length,0);assert.deepEqual(f.closed,[70]);
 }
 const f=fixture();f.meta.mode=0o100440;
 assert.equal(exportPublicKey(readHumanProposalReleaseKey(f.args)),f.args.expectedReleaseKey);
});
test('credential inode, device, time and size drift is caught and consumed bytes are wiped',()=>{
 for(const patch of [{ino:78},{dev:93},{mtimeMs:11},{ctimeMs:21},{size:999}]){
  const f=fixture();let reads=0;f.io.fstatSync=()=>({...f.meta,...(++reads===2?patch:{})});
  refuse(()=>readHumanProposalReleaseKey(f.args));
  assert.ok(f.delivered[0].every(b=>b===0));assert.deepEqual(f.closed,[70]);
 }
});
test('bad DER and mismatched buffer length are wiped; no fallback path is read',()=>{
 for(const mode of ['bad-der','wrong-length']){
  const f=fixture();let bytes;
  const original=f.io.readFileSync;f.io.readFileSync=file=>{
   if(file!==70)return original(file);
   bytes=mode==='bad-der'?Buffer.alloc(f.meta.size,1):Buffer.from('short');return bytes;
  };
  assert.throws(()=>readHumanProposalReleaseKey(f.args));assert.ok(bytes.every(b=>b===0));
  assert.deepEqual(f.closed,[70]);assert.equal(f.opened.length,1);
 }
});
test('other valid private-key algorithms cannot supply the Release Ed25519 signer',()=>{
 const f=fixture(),ec=generateKeyPairSync('ec',{namedCurve:'prime256v1'}).privateKey,
  ecBytes=ec.export({format:'der',type:'pkcs8'}),original=f.io.readFileSync;
 f.meta.size=ecBytes.length;
 f.io.readFileSync=file=>file===70?ecBytes:original(file);
 refuse(()=>readHumanProposalReleaseKey(f.args));
 assert.ok(ecBytes.every(b=>b===0));assert.deepEqual(f.closed,[70]);
});
test('missing fixed credential fails without environment or caller fallback',()=>{
 const f=fixture();f.io.openSync=(file,flags)=>{
  assert.equal(file,f.directory+'/release-signing-key');assert.ok(flags&fs.constants.O_NOFOLLOW);
  f.opened.push(file);throw Object.assign(Error('missing synthetic credential'),{code:'ENOENT'});
 };
 assert.throws(()=>readHumanProposalReleaseKey({...f.args,privateKey:f.privateKey,credentialPath:'/tmp/attacker'}),
  {code:'ENOENT'});assert.equal(f.opened.length,1);assert.equal(f.delivered.length,0);
});
test('environment credential and policy redirection cannot change the fixed key source',()=>{
 const f=fixture(),variables=['CREDENTIALS_DIRECTORY','HUMAN_PROPOSAL_KEY','RELEASE_SIGNING_KEY'],
  prior=Object.fromEntries(variables.map(name=>[name,process.env[name]]));
 try{
  for(const name of variables)process.env[name]='/tmp/attacker-test-only';
  assert.equal(exportPublicKey(readHumanProposalReleaseKey(f.args)),f.args.expectedReleaseKey);
  assert.deepEqual(f.opened,[f.directory+'/release-signing-key']);
 }finally{for(const name of variables)if(prior[name]===undefined)delete process.env[name];else process.env[name]=prior[name];}
});
