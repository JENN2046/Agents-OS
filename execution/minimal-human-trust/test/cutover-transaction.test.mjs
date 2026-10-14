// Real filesystem/flock/crash tests in disposable user-owned directories only.
// "produce" simulates a public artifact effect; no production keys or services.
import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import {createHash} from 'node:crypto';
import {spawnSync} from 'node:child_process';
import {runCutoverTransaction} from '../release/cutover-transaction.mjs';

const sha=bytes=>createHash('sha256').update(bytes).digest('hex');
const NOW=1792000000000;
const moduleUrl=new URL('../release/cutover-transaction.mjs',import.meta.url).href;
const slots=['issuerState','replayState','stageRootsArchive','roots','issuerConfig','receipt'];
const names={issuerState:'issuer/state.json',replayState:'replay/state.json',
  stageRootsArchive:'etc/stage-trust-roots.json',roots:'etc/trust-roots.json',
  issuerConfig:'etc/issuer.json',receipt:'publication/handoff-cutover.receipt.json'};
const replay=extra=>Buffer.from(JSON.stringify({schema:1,revision:0,maxNow:NOW,
  data:{kind:'mht.issuer-replay.v2',used:[],handoff:null,...extra}}));
function fixture(t){
  const base=fs.mkdtempSync(path.join(os.tmpdir(),'mht-cutover-transaction-'));
  t.after(()=>fs.rmSync(base,{recursive:true,force:true}));
  const directory=path.join(base,'transaction');fs.mkdirSync(directory,{mode:0o700});
  const plannedTargets=slots.map(slot=>({slot,path:path.join(base,names[slot]),mode:0o600,beforeSha256:null}));
  const oldRoots=Buffer.from('old exact roots\n');
  for(const target of plannedTargets)fs.mkdirSync(path.dirname(target.path),{recursive:true,mode:0o700});
  fs.writeFileSync(plannedTargets.find(s=>s.slot==='roots').path,oldRoots,{mode:0o600});
  plannedTargets.find(s=>s.slot==='roots').beforeSha256=sha(oldRoots);
  const artifacts={schema:'mht.cutover-artifacts.v1',evidence:{synthetic:true,handoff:'no production signature'},
    files:plannedTargets.map(target=>({...target,bytesBase64:(target.slot==='replayState'?replay({}):
      Buffer.from(JSON.stringify({slot:target.slot,isolated:true,value:'new exact bytes'})+'\n')).toString('base64')}))};
  const config={directory,identity:{schema:'mht.cutover-intent.v1',issuedAt:NOW-1000,expiresAt:NOW+60000,
    authorizationHash:sha('synthetic exact authorization')},plannedTargets,artifacts};
  let produced=0;const guardPoints=[];
  const args={...config,now:()=>NOW,preflight:()=>true,guard:c=>{guardPoints.push(c.point);return true;},
    produceArtifacts:()=>{produced++;return artifacts;},validateArtifacts:()=>true,verifyCommit:()=>true};
  return {base,config,args,artifacts,plannedTargets,guardPoints,produced:()=>produced,
    target:slot=>plannedTargets.find(s=>s.slot===slot).path};
}
function expectedFiles(f){
  for(const file of f.artifacts.files){assert.deepEqual(fs.readFileSync(file.path),Buffer.from(file.bytesBase64,'base64'));
    assert.equal(fs.statSync(file.path).mode&0o7777,file.mode);}
}
const childCode=`
import fs from 'node:fs';
import {runCutoverTransaction} from ${JSON.stringify(moduleUrl)};
const c=JSON.parse(process.argv[1]),point=process.argv[2],counter=process.argv[3];
runCutoverTransaction({...c,now:()=>${NOW},preflight:()=>true,guard:()=>true,
  produceArtifacts:()=>{const n=fs.existsSync(counter)?Number(fs.readFileSync(counter)):0;
    fs.writeFileSync(counter,String(n+1),{mode:0o600});return c.artifacts;},
  validateArtifacts:()=>true,verifyCommit:()=>true,
  fault:where=>{if(where===point)process.kill(process.pid,'SIGKILL');}});
`;
function crash(f,point){
  const counter=path.join(f.base,'effect-count');
  const child=spawnSync(process.execPath,['--input-type=module','-e',childCode,JSON.stringify(f.config),point,counter],
    {encoding:'utf8',timeout:10000,env:{PATH:'/usr/bin:/bin'},maxBuffer:65536});
  assert.equal(child.signal,'SIGKILL',child.stderr||child.stdout);
  return ()=>fs.existsSync(counter)?Number(fs.readFileSync(counter)):0;
}

test('complete exact publication uses real atomic files, one effect and durable commit',t=>{
  const f=fixture(t),result=runCutoverTransaction(f.args);
  assert.equal(result.status,'CUTOVER_COMMITTED');assert.equal(result.signerCalled,true);assert.equal(f.produced(),1);
  expectedFiles(f);assert.ok(fs.existsSync(path.join(f.config.directory,'COMMIT.json')));
  for(const slot of slots){assert.ok(f.guardPoints.includes(slot+':guard'));
    assert.ok(f.guardPoints.includes(slot+':before-rename'));}
});
test('preflight refusal leaves no writer lock, intent, target or artifact effect',t=>{
  const f=fixture(t);f.args.preflight=()=>false;
  assert.throws(()=>runCutoverTransaction(f.args),{code:'CUTOVER_PREFLIGHT_REFUSED'});
  assert.deepEqual(fs.readdirSync(f.config.directory),[]);assert.equal(f.produced(),0);
});
test('expired initial admission makes no writer lock or effect',t=>{
  const f=fixture(t);f.args.now=()=>f.config.identity.expiresAt;
  assert.throws(()=>runCutoverTransaction(f.args),{code:'CUTOVER_AUTHORIZATION_PENDING'});
  assert.deepEqual(fs.readdirSync(f.config.directory),[]);assert.equal(f.produced(),0);
});
test('unrelated preexisting roots are rejected before any effect',t=>{
  const f=fixture(t);fs.writeFileSync(f.target('roots'),'unrelated roots');
  assert.throws(()=>runCutoverTransaction(f.args),{code:'CUTOVER_TARGET_DRIFT'});
  assert.deepEqual(fs.readdirSync(f.config.directory),[]);assert.equal(f.produced(),0);
});
test('nonempty replay is rejected even when its old SHA is explicitly supplied',t=>{
  const f=fixture(t),bytes=replay({used:[{phase:'RESULT',id:'never overwrite'}]});
  fs.writeFileSync(f.target('replayState'),bytes,{mode:0o600});
  f.plannedTargets.find(s=>s.slot==='replayState').beforeSha256=sha(bytes);
  assert.throws(()=>runCutoverTransaction(f.args),{code:'CUTOVER_REPLAY_NOT_EMPTY'});
  assert.equal(f.produced(),0);assert.deepEqual(fs.readFileSync(f.target('replayState')),bytes);
});
test('known empty replay can be initialized and published by actual byte writer',t=>{
  const f=fixture(t),bytes=replay({});fs.writeFileSync(f.target('replayState'),bytes,{mode:0o600});
  const header=f.plannedTargets.find(s=>s.slot==='replayState');header.beforeSha256=sha(bytes);
  f.artifacts.files.find(s=>s.slot==='replayState').beforeSha256=sha(bytes);
  assert.equal(runCutoverTransaction(f.args).status,'CUTOVER_COMMITTED');expectedFiles(f);
});
test('symlink and hardlinked publication targets fail before signing',t=>{
  for(const kind of ['symlink','hardlink']){
    const f=fixture(t),original=f.target('roots'),other=path.join(f.base,'other');
    if(kind==='symlink'){fs.renameSync(original,other);fs.symlinkSync(other,original);}
    else fs.linkSync(original,other);
    assert.throws(()=>runCutoverTransaction(f.args));assert.equal(f.produced(),0);
  }
});

for(const point of ['after-intent','after-effect','ARTIFACTS.json:after-temp-fsync']){
  test('real crash '+point+' leaves UNKNOWN and never repeats an artifact effect',t=>{
    const f=fixture(t),count=crash(f,point),before=count();
    assert.throws(()=>runCutoverTransaction(f.args),{code:'CUTOVER_EFFECT_UNKNOWN'});
    assert.equal(count(),before);assert.equal(f.produced(),0);
    assert.equal(fs.existsSync(f.target('issuerConfig')),false);
  });
}
const recoveringPoints=['after-artifacts',
  ...slots.flatMap(slot=>[slot+':after-temp-fsync',slot+':after-rename',slot+':after-dir-fsync']),
  'COMMIT.json:after-temp-fsync'];
for(const point of recoveringPoints){
  test('real crash '+point+' resumes exact durable artifacts without another effect',t=>{
    const f=fixture(t),count=crash(f,point);assert.equal(count(),1);
    const result=runCutoverTransaction(f.args);assert.equal(result.status,'CUTOVER_COMMITTED');
    assert.equal(result.signerCalled,false);assert.equal(count(),1);assert.equal(f.produced(),0);expectedFiles(f);
  });
}
test('crash after durable COMMIT returns history without signing or restoring newer ledger results',t=>{
  const f=fixture(t),count=crash(f,'after-commit');
  const advanced=Buffer.from('a legitimate later issuer result');fs.writeFileSync(f.target('issuerState'),advanced);
  const replayAfter=replay({used:[{id:'later',phase:'RESULT'}]});fs.writeFileSync(f.target('replayState'),replayAfter);
  f.args.now=()=>NOW+86400000;
  const result=runCutoverTransaction(f.args);assert.equal(result.status,'CUTOVER_ALREADY_COMMITTED');
  assert.equal(result.historical,true);assert.equal(result.signerCalled,false);assert.equal(count(),1);
  assert.deepEqual(fs.readFileSync(f.target('issuerState')),advanced);
  assert.deepEqual(fs.readFileSync(f.target('replayState')),replayAfter);
});
test('target drift during recovery rejects publication and preserves original artifacts',t=>{
  const f=fixture(t),count=crash(f,'after-artifacts');
  const journal=fs.readFileSync(path.join(f.config.directory,'ARTIFACTS.json'));
  fs.writeFileSync(f.target('roots'),'unrelated after artifact staging');
  assert.throws(()=>runCutoverTransaction(f.args),{code:'CUTOVER_TARGET_DRIFT'});
  assert.equal(count(),1);assert.equal(f.produced(),0);
  assert.deepEqual(fs.readFileSync(path.join(f.config.directory,'ARTIFACTS.json')),journal);
  assert.equal(fs.existsSync(f.target('issuerState')),false);
});
test('recovery never accepts a different identity or target binding',t=>{
  const f=fixture(t);crash(f,'after-artifacts');
  const changedIdentity={...f.args.identity,authorizationHash:sha('different approval')};
  assert.throws(()=>runCutoverTransaction({...f.args,identity:changedIdentity}),{code:'CUTOVER_INTENT_CONFLICT'});
  const targets=f.plannedTargets.map(s=>({...s}));targets.find(s=>s.slot==='roots').beforeSha256=sha('different old roots');
  assert.throws(()=>runCutoverTransaction({...f.args,plannedTargets:targets}),{code:'CUTOVER_INTENT_CONFLICT'});
  assert.equal(f.produced(),0);assert.equal(fs.existsSync(f.target('issuerState')),false);
});
test('recorded commit cannot invent different file digests or approval time',t=>{
  const f=fixture(t);runCutoverTransaction(f.args);const file=path.join(f.config.directory,'COMMIT.json');
  const original=JSON.parse(fs.readFileSync(file));
  const canonical=x=>x===null||typeof x!=='object'?JSON.stringify(x):Array.isArray(x)?'['+x.map(canonical).join(',')+']':
    '{'+Object.keys(x).sort().map(k=>JSON.stringify(k)+':'+canonical(x[k])).join(',')+'}';
  for(const changed of [
    {...original,targets:{...original.targets,roots:sha('not the committed roots')}},
    {...original,committedAt:f.config.identity.expiresAt},
  ]){
    fs.writeFileSync(file,canonical(changed));
    assert.throws(()=>runCutoverTransaction(f.args),{code:'CUTOVER_COMMIT_CONFLICT'});
  }
  assert.equal(f.produced(),1);
});
test('nonempty replay after staged artifacts is never overwritten',t=>{
  const f=fixture(t);crash(f,'after-artifacts');const bytes=replay({handoff:{epoch:99},used:[]});
  fs.writeFileSync(f.target('replayState'),bytes,{mode:0o600});
  assert.throws(()=>runCutoverTransaction(f.args),{code:'CUTOVER_REPLAY_NOT_EMPTY'});
  assert.deepEqual(fs.readFileSync(f.target('replayState')),bytes);assert.equal(f.produced(),0);
});
test('expired recovery keeps pending durable artifacts and never rolls back an already published file',t=>{
  const f=fixture(t);crash(f,'issuerState:after-dir-fsync');
  const state=fs.readFileSync(f.target('issuerState')),journal=fs.readFileSync(path.join(f.config.directory,'ARTIFACTS.json'));
  f.args.now=()=>f.config.identity.expiresAt;
  assert.throws(()=>runCutoverTransaction(f.args),{code:'CUTOVER_AUTHORIZATION_PENDING'});
  assert.deepEqual(fs.readFileSync(f.target('issuerState')),state);
  assert.deepEqual(fs.readFileSync(path.join(f.config.directory,'ARTIFACTS.json')),journal);
  assert.equal(f.produced(),0);assert.equal(fs.existsSync(f.target('issuerConfig')),false);
});
test('guard is freshly called at publication boundaries and a changing Owner prevents later writes',t=>{
  const f=fixture(t);let fenced=true;
  f.args.guard=()=>fenced;
  f.args.fault=point=>{if(point==='after-file:roots')fenced=false;};
  assert.throws(()=>runCutoverTransaction(f.args),{code:'CUTOVER_GUARD_REFUSED'});
  assert.equal(fs.existsSync(f.target('issuerConfig')),false);assert.equal(fs.existsSync(f.target('receipt')),false);
  assert.equal(f.produced(),1);
});
test('clock rollback at a later publication boundary is rejected without restoring old files',t=>{
  const f=fixture(t);let clock=NOW;f.args.now=()=>clock;
  f.args.fault=point=>{if(point==='after-file:roots')clock--;};
  assert.throws(()=>runCutoverTransaction(f.args),{code:'CUTOVER_AUTHORIZATION_PENDING'});
  assert.equal(fs.existsSync(f.target('issuerConfig')),false);assert.equal(f.produced(),1);
});
test('clock rollback after verifyCommit cannot persist an invalid COMMIT or repeat its artifact effect',t=>{
  const f=fixture(t);let rollbackNext=false;
  f.args.verifyCommit=()=>{rollbackNext=true;return true;};
  f.args.now=()=>{if(rollbackNext){rollbackNext=false;return NOW-2000;}return NOW;};
  assert.throws(()=>runCutoverTransaction(f.args),{code:'CUTOVER_AUTHORIZATION_PENDING'});
  assert.equal(fs.existsSync(path.join(f.config.directory,'COMMIT.json')),false);
  const saved=fs.readFileSync(path.join(f.config.directory,'ARTIFACTS.json'));
  expectedFiles(f);assert.equal(f.produced(),1);
  f.args.verifyCommit=()=>true;
  const recovered=runCutoverTransaction(f.args);
  assert.equal(recovered.status,'CUTOVER_COMMITTED');assert.equal(recovered.signerCalled,false);
  assert.equal(f.produced(),1);
  assert.ok(fs.readFileSync(path.join(f.config.directory,'ARTIFACTS.json')).equals(saved));
  assert.equal(JSON.parse(fs.readFileSync(path.join(f.config.directory,'COMMIT.json'))).committedAt,NOW);
});
test('produced files cannot escape the admitted slot/path/old-byte plan',t=>{
  const f=fixture(t);f.artifacts.files.find(s=>s.slot==='issuerConfig').path=path.join(f.base,'foreign','issuer.json');
  assert.throws(()=>runCutoverTransaction(f.args),{code:'CUTOVER_EFFECT_UNKNOWN'});
  assert.equal(f.produced(),1);assert.equal(fs.existsSync(f.target('issuerState')),false);
  assert.equal(fs.existsSync(path.join(f.config.directory,'ARTIFACTS.json')),false);
});
test('real flock excludes a second writer over the complete publication lifetime',t=>{
  const f=fixture(t);let observed=false;
  f.args.produceArtifacts=()=>{
    const second=spawnSync(process.execPath,['--input-type=module','-e',childCode,JSON.stringify(f.config),'never',path.join(f.base,'second-effect')],
      {encoding:'utf8',timeout:10000,env:{PATH:'/usr/bin:/bin'},maxBuffer:65536});
    assert.notEqual(second.status,0);assert.match(second.stderr,/CUTOVER_LOCK_BUSY/);
    assert.equal(fs.existsSync(path.join(f.base,'second-effect')),false);observed=true;return f.artifacts;
  };
  assert.equal(runCutoverTransaction(f.args).status,'CUTOVER_COMMITTED');assert.equal(observed,true);
});
