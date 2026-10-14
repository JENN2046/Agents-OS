import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {createHash} from 'node:crypto';
import {HUMAN_PROPOSAL_REQUIRED_FILES,checkHumanProposalFreeze,runHumanProposalBootstrap,readProposalProtectedFile}
 from '../release/human-proposal-bootstrap.mjs';
import {REVIEWED_SOURCE_FILES} from '../release/publisher-bootstrap.mjs';

const sha=bytes=>createHash('sha256').update(bytes).digest('hex');
const base=fileURLToPath(new URL('../',import.meta.url));
const root='/usr/lib/minimal-human-trust/',freeze='/etc/minimal-human-trust/first-trust-code.json';
const unit='minimal-human-trust-proposal.service';
function fixture(){
 const files=new Map(HUMAN_PROPOSAL_REQUIRED_FILES.map(name=>[root+name,fs.readFileSync(path.join(base,name))]));
 const manifest={schema:'mht.first-trust-code-freeze.v1',sourceCommit:'a'.repeat(40),
  files:Object.fromEntries(HUMAN_PROPOSAL_REQUIRED_FILES.map(name=>[name,sha(files.get(root+name))]))};
 files.set(freeze,Buffer.from(JSON.stringify(manifest)));
 const seen=[];
 return {files,manifest,seen,euid:0,argv:['/usr/bin/node',root+'release/human-proposal-bootstrap.mjs'],
  read:name=>{seen.push(name);assert.ok(files.has(name),'Unexpected protected read '+name);return files.get(name);},
  cgroup:()=>`0::/system.slice/${unit}\n`};
}
test('full actual source freeze precedes dynamic operation import and is reread before execution',async()=>{
 const f=fixture(),events=[];
 const result=await runHumanProposalBootstrap({...f,load:async()=>{
  events.push('import');assert.equal(f.seen.length,1+HUMAN_PROPOSAL_REQUIRED_FILES.length);
  return {runHumanProposalOnce:opts=>{
   events.push('run');assert.equal(f.seen.length,2+2*HUMAN_PROPOSAL_REQUIRED_FILES.length);
   assert.deepEqual(opts.frozenManifest,f.manifest);
   assert.equal(opts.frozenRawDigest,sha(f.files.get(freeze)));
   return {status:'ISOLATED_TEST_ONLY'};
  }};
 }});
 assert.deepEqual(events,['import','run']);assert.equal(result.status,'ISOLATED_TEST_ONLY');
});
test('proposal and publisher freeze cover exactly the same complete 44-file boundary',()=>{
 assert.equal(HUMAN_PROPOSAL_REQUIRED_FILES.length,44);
 assert.equal(new Set(HUMAN_PROPOSAL_REQUIRED_FILES).size,44);
 assert.deepEqual([...HUMAN_PROPOSAL_REQUIRED_FILES].sort(),[...REVIEWED_SOURCE_FILES].sort());
 for(const name of HUMAN_PROPOSAL_REQUIRED_FILES.filter(n=>n.endsWith('.mjs'))){
  const source=fs.readFileSync(path.join(base,name),'utf8');
  for(const match of source.matchAll(/(?:from\s+|import\s*\(\s*)['"]([^'"]+)['"]/g)){
   const specifier=match[1];if(specifier.startsWith('node:'))continue;
   assert.ok(specifier.startsWith('.'),'Unexpected external signing dependency '+specifier);
   const target=path.posix.normalize(path.posix.join(path.posix.dirname(name),specifier));
   assert.ok(HUMAN_PROPOSAL_REQUIRED_FILES.includes(target),`${name} imports unfrozen ${target}`);
  }
 }
});
test('bootstrap imports only Node builtins before frozen implementation admission',()=>{
 const source=fs.readFileSync(path.join(base,'release/human-proposal-bootstrap.mjs'),'utf8');
 const imports=[...source.matchAll(/^import\b[^\n]*from ['"]([^'"]+)['"]/gm)].map(m=>m[1]);
 assert.ok(imports.length>0);assert.ok(imports.every(name=>name.startsWith('node:')));
});
test('each frozen file corruption and omission prevents implementation import',async()=>{
 for(const name of HUMAN_PROPOSAL_REQUIRED_FILES){
  const f=fixture();f.files.set(root+name,Buffer.from('tampered actual source'));
  await assert.rejects(runHumanProposalBootstrap({...f,load:()=>assert.fail('No import before freeze')}),
   /HUMAN_PROPOSAL_BOOTSTRAP_REFUSED/);
  const g=fixture();delete g.manifest.files[name];
  assert.throws(()=>checkHumanProposalFreeze({...g,read:()=>assert.fail('No source read for incomplete manifest')}),
   /HUMAN_PROPOSAL_BOOTSTRAP_REFUSED/);
 }
});
test('untrusted manifest shape, prototype, commit or external path cannot authorize reads',()=>{
 for(const patch of [{schema:'other'},{sourceCommit:'a'.repeat(39)},{sourceCommit:'A'.repeat(40)},
  {extra:true},{files:null},{files:[]}]){
  const f=fixture();Object.assign(f.manifest,patch);
  assert.throws(()=>checkHumanProposalFreeze({...f,read:()=>assert.fail('No read for invalid manifest')}),
   /HUMAN_PROPOSAL_BOOTSTRAP_REFUSED/);
 }
 const proto=fixture();Object.setPrototypeOf(proto.manifest,{extra:true});
 assert.throws(()=>checkHumanProposalFreeze(proto),/HUMAN_PROPOSAL_BOOTSTRAP_REFUSED/);
 for(const foreign of ['../secret','/etc/private-key','x\\secret','__proto__']){
  const f=fixture(),first=HUMAN_PROPOSAL_REQUIRED_FILES[0];delete f.manifest.files[first];
  Object.defineProperty(f.manifest.files,foreign,{enumerable:true,value:'a'.repeat(64)});
  assert.throws(()=>checkHumanProposalFreeze({...f,read:()=>assert.fail('No foreign source read')}),
   /HUMAN_PROPOSAL_BOOTSTRAP_REFUSED/);
 }
});
test('bad digest values fail before dynamic implementation import',async()=>{
 for(const value of ['a'.repeat(63),'A'.repeat(64),null,0]){
  const f=fixture();f.manifest.files[HUMAN_PROPOSAL_REQUIRED_FILES[0]]=value;
  f.files.set(freeze,Buffer.from(JSON.stringify(f.manifest)));
  await assert.rejects(runHumanProposalBootstrap({...f,load:()=>assert.fail('No import for wrong digest')}),
   /HUMAN_PROPOSAL_BOOTSTRAP_REFUSED/);
 }
});
test('nonroot, argv override and malformed or duplicate service membership fail before protected reads',async()=>{
 const f=fixture();
 for(const patch of [{euid:1000},{argv:['node','entry','--request=/tmp/attacker']},{argv:null},
  {cgroup:()=>`0::/user.slice/${unit}`},{cgroup:()=>`0::/system.slice/other.service`},
  {cgroup:()=>f.cgroup()+f.cgroup()},{cgroup:()=>f.cgroup()+'bad'},
  {cgroup:()=>`0::/system.slice/${unit}/subgroup`},{cgroup:()=>''},{cgroup:()=>null},
  {cgroup:()=> 'x'.repeat(8193)}]){
  await assert.rejects(runHumanProposalBootstrap({...f,...patch,read:()=>assert.fail('No protected read'),
   load:()=>assert.fail('No import')}),/HUMAN_PROPOSAL_BOOTSTRAP_REFUSED/);
 }
});
test('manifest and every source drift across dynamic import prevents operation execution',async()=>{
 for(const name of [freeze,...HUMAN_PROPOSAL_REQUIRED_FILES.map(n=>root+n)]){
  const f=fixture();await assert.rejects(runHumanProposalBootstrap({...f,load:async()=>{
   f.files.set(name,Buffer.from('changed after first admission'));
   return {runHumanProposalOnce:()=>assert.fail('No operation after import drift')};
  }}),/HUMAN_PROPOSAL_BOOTSTRAP_REFUSED/);
 }
});
test('absent exported operation cannot become an admitted signing entry',async()=>{
 const f=fixture();await assert.rejects(runHumanProposalBootstrap({...f,load:async()=>({})}),
  /HUMAN_PROPOSAL_BOOTSTRAP_REFUSED/);
});
test('protected reader checks real ownership/mode/link and read stability semantics using isolated fs mocks',t=>{
 const bytes=Buffer.from('disposable public source bytes'),closed=[];
 let parentPatch={},filePatch={},afterPatch={},calls=0,opens=0;
 t.mock.method(fs,'lstatSync',()=>({uid:0,mode:0o40755,isDirectory:()=>true,
  isSymbolicLink:()=>false,...parentPatch}));
 t.mock.method(fs,'openSync',(name,flags)=>{
  assert.equal(name,root+'disposable-source.mjs');
  assert.equal(flags,fs.constants.O_RDONLY|fs.constants.O_NOFOLLOW);opens++;calls=0;return 70;
 });
 t.mock.method(fs,'fstatSync',()=>({uid:0,dev:7,ino:12,nlink:1,mode:0o100644,size:bytes.length,
  mtimeMs:10,ctimeMs:20,isFile:()=>true,...filePatch,...(++calls===2?afterPatch:{})}));
 t.mock.method(fs,'readFileSync',fd=>{assert.equal(fd,70);return bytes;});
 t.mock.method(fs,'closeSync',fd=>closed.push(fd));
 assert.deepEqual(readProposalProtectedFile(root+'disposable-source.mjs'),bytes);
 for(const patch of [{uid:1000},{mode:0o40777},{isSymbolicLink:()=>true},{isDirectory:()=>false}]){
  parentPatch=patch;const before=opens;
  assert.throws(()=>readProposalProtectedFile(root+'disposable-source.mjs'),/HUMAN_PROPOSAL_BOOTSTRAP_REFUSED/);
  assert.equal(opens,before);
 }
 parentPatch={};
 for(const patch of [{uid:1000},{nlink:2},{mode:0o100666},{mode:0o104644},{size:0},{size:67108865},
  {isFile:()=>false}]){
  filePatch=patch;
  assert.throws(()=>readProposalProtectedFile(root+'disposable-source.mjs'),/HUMAN_PROPOSAL_BOOTSTRAP_REFUSED/);
 }
 filePatch={};
 for(const patch of [{dev:8},{ino:13},{size:bytes.length+1},{mtimeMs:11},{ctimeMs:21}]){
  afterPatch=patch;
  assert.throws(()=>readProposalProtectedFile(root+'disposable-source.mjs'),/HUMAN_PROPOSAL_BOOTSTRAP_REFUSED/);
 }
 assert.equal(closed.length,opens);
 assert.throws(()=>readProposalProtectedFile(root+'../escape'),/HUMAN_PROPOSAL_BOOTSTRAP_REFUSED/);
});
