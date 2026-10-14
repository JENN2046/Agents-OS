import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import {spawnSync} from 'node:child_process';
import {digest,signed,exportPublicKey,ProtectedStore} from '../src/lease-core.mjs';
import {validateInstalledTrustPolicy} from '../src/minimal-trust-issuer-once.mjs';
import {runMinimalTrustOnce} from '../src/minimal-trust-issuer.mjs';
import {rehearseRecoveryCutover,productionCutoverGate} from '../release/stage-installer-reviewed.mjs';
import {stagedRecoveryFixture} from './fixtures/staged-recovery-fixture.mjs';
import {inspectStagedR17HandoffAdmission} from '../release/staged-r17-handoff-admission.mjs';

function fixture(t){
  const directory=fs.mkdtempSync(path.join(os.tmpdir(),'mht-recovery-rehearsal-'));
  fs.chmodSync(directory,0o700);
  t.after(()=>fs.rmSync(directory,{recursive:true,force:true}));
  const f=stagedRecoveryFixture();let time=f.args.now;
  return {f,directory,now:()=>time,setNow:t=>{time=t;},
    run:extra=>rehearseRecoveryCutover({directory,handoffArgs:f.args,now:()=>time,...extra})};
}
test('v2 fresh signed observation does not rewrite an old ledger maxNow',()=>{
  const f=stagedRecoveryFixture(),before=structuredClone(f.snapshot);
  assert.ok(f.args.now-f.snapshot.maxNow>3600000);
  assert.equal(inspectStagedR17HandoffAdmission(f.args).status,'STAGED_R17_STOP_AND_FENCED_OWNER_INSPECTED');
  assert.deepEqual(f.snapshot,before);
});
test('v2 admission must bind original source/stage/review/evidence before any file write',t=>{
  for(const key of ['sourceReleaseHash','stageAuthorizationHash','reviewedManifestHash','recoveryEvidenceDigest']){
    const x=fixture(t);x.f.admission[key]=digest('wrong-'+key);
    x.f.args.handoff=signed({...x.f.args.handoff.body,recoveryAdmission:x.f.admission},x.f.enroller);
    assert.throws(()=>x.run());assert.deepEqual(fs.readdirSync(x.directory),[]);
  }
});
test('missing physical role file is rejected before transaction or target directories exist',t=>{
  const x=fixture(t);x.f.physicalFiles.delete([...x.f.physicalFiles.keys()][0]);
  assert.throws(()=>x.run());assert.deepEqual(fs.readdirSync(x.directory),[]);
});
test('signed R17 STOP does not substitute for actual fenced old writer observation',t=>{
  const x=fixture(t);x.f.args.readUnit=()=>({ActiveState:'active',SubState:'running',MainPID:'99',UnitFileState:'enabled'});
  assert.throws(()=>x.run(),{code:'OWNER_WRITER_STILL_ACTIVE'});
  assert.deepEqual(fs.readdirSync(x.directory),[]);
});
test('isolated rehearsal publishes byte-identical ledger and permits first recovery grant only',t=>{
  const x=fixture(t),f=x.f,before=JSON.stringify(f.snapshot);
  const receipt=x.run();assert.equal(receipt.status,'RECOVERY_SHADOW_REHEARSED_NOT_INSTALLED');
  assert.equal(receipt.transaction.status,'CUTOVER_COMMITTED');
  assert.equal(receipt.realHumanEnrolled,false);assert.equal(receipt.realOsStopAttested,false);
  assert.equal(receipt.productionChanged,false);assert.equal(receipt.maySettleUnknown,false);
  assert.deepEqual(JSON.parse(fs.readFileSync(receipt.layout.issuerState)),f.snapshot);
  const cfg=JSON.parse(fs.readFileSync(receipt.layout.issuerConfig));
  const roots=JSON.parse(fs.readFileSync(receipt.layout.roots));
  const policy=validateInstalledTrustPolicy(cfg,{trustRoots:roots,now:x.now()});
  const call=(action,payload={})=>runMinimalTrustOnce({
    issuerDirectory:path.dirname(receipt.layout.issuerState),replayDirectory:path.dirname(receipt.layout.replayState),
    issuerPrivateKey:f.issuer,issuerPublicKey:roots.issuerPublicKey,releasePublicKey:roots.releasePublicKey,
    enrollmentAuthorityPublicKey:roots.enrollmentAuthorityPublicKey,release:cfg.release,
    grantId:cfg.grantId,humanAuthorityPublicKey:cfg.humanAuthorityPublicKey,
    mode:policy.mode,handoffBinding:policy.handoffBinding,now:x.now,resolveProject:()=>{throw Error('no new business');},
    envelope:signed({schema:'r16.issuer-call.v1',role:'native',peerId:f.args.priorPublicConfig.peers.native.id,
      action,payload,issuedAt:x.now(),nonce:'synthetic-recovery-'+action},f.signers.native),
  });
  assert.deepEqual(call('grant'),f.args.priorPublicConfig.grant);
  assert.throws(()=>call('prepare'),{code:'RECOVERY_ONLY'});
  assert.equal(JSON.stringify(f.snapshot),before);
  assert.deepEqual(JSON.parse(fs.readFileSync(receipt.layout.issuerState)),f.snapshot);
  // A lost final response reads the historical commit without resetting the
  // replay binding or new issuer activity, even after the original short window.
  const replayBefore=fs.readFileSync(receipt.layout.replayState);
  x.setNow(f.args.now+60000);
  const again=x.run();assert.equal(again.transaction.status,'CUTOVER_ALREADY_COMMITTED');
  assert.equal(again.transaction.historical,true);
  assert.ok(fs.readFileSync(receipt.layout.replayState).equals(replayBefore));
});
test('systemd-style precreated empty directories do not skip replay state creation',t=>{
  const x=fixture(t);fs.mkdirSync(x.directory+'/installed',{mode:0o700});
  fs.mkdirSync(x.directory+'/installed/issuer',{mode:0o700});
  fs.mkdirSync(x.directory+'/installed/replay',{mode:0o700});
  const receipt=x.run();const replay=JSON.parse(fs.readFileSync(receipt.layout.replayState));
  assert.equal(replay.data.handoff,null);assert.deepEqual(replay.data.used,[]);
});
test('TMPDIR cannot move isolated cutover outside the fixed /tmp boundary',t=>{
  const directory=fs.mkdtempSync(path.join(os.homedir(),'mht-rehearsal-env-negative-'));
  fs.chmodSync(directory,0o700);t.after(()=>fs.rmSync(directory,{recursive:true,force:true}));
  const moduleUrl=new URL('../release/stage-installer-reviewed.mjs',import.meta.url).href;
  const code=`import {isolatedCutoverLayout} from ${JSON.stringify(moduleUrl)};
    try {isolatedCutoverLayout(process.argv[1]);process.exit(2);}
    catch(e){if(e.code!=='ISOLATED_REHEARSAL_DIRECTORY')throw e;}`;
  const result=spawnSync(process.execPath,['--input-type=module','-e',code,directory],
    {env:{PATH:'/usr/bin:/bin',TMPDIR:os.homedir()},encoding:'utf8'});
  assert.equal(result.status,0,result.stderr);assert.deepEqual(fs.readdirSync(directory),[]);
});
test('partial roots/issuer publication resumes exact artifacts without re-producing them',t=>{
  const x=fixture(t);assert.throws(()=>x.run({fault:point=>{
    if(point==='after-file:roots')throw Error('crash after roots');
  }}));
  const artifactBytes=fs.readFileSync(x.directory+'/transaction/ARTIFACTS.json');
  const resumed=x.run();assert.equal(resumed.transaction.status,'CUTOVER_COMMITTED');
  assert.equal(resumed.transaction.signerCalled,false);
  assert.ok(fs.readFileSync(x.directory+'/transaction/ARTIFACTS.json').equals(artifactBytes));
});
test('intent-only rehearsal is UNKNOWN and never repeats materialization',t=>{
  const x=fixture(t);assert.throws(()=>x.run({fault:p=>{if(p==='after-intent')throw Error('crash');}}),
    {code:'CUTOVER_EFFECT_UNKNOWN'});
  assert.throws(()=>x.run(),{code:'CUTOVER_EFFECT_UNKNOWN'});
  assert.equal(fs.existsSync(x.directory+'/installed/issuer/state.json'),false);
});
test('writer restart during a publication checkpoint preserves pending artifacts',t=>{
  const x=fixture(t);let restarted=false;
  x.f.args.readUnit=()=>restarted?{ActiveState:'active',SubState:'running',MainPID:'99',UnitFileState:'enabled'}:
    {ActiveState:'inactive',SubState:'dead',MainPID:'0',UnitFileState:'masked'};
  assert.throws(()=>x.run({fault:p=>{if(p==='after-file:issuerState')restarted=true;}}));
  assert.equal(fs.existsSync(x.directory+'/transaction/ARTIFACTS.json'),true);
  assert.equal(fs.existsSync(x.directory+'/transaction/COMMIT.json'),false);
});
test('expired STOP window cannot resume or silently extend an incomplete attempt',t=>{
  const x=fixture(t);assert.throws(()=>x.run({fault:p=>{if(p==='after-artifacts')throw Error('crash');}}));
  const original=fs.readFileSync(x.directory+'/transaction/INTENT.json');
  x.setNow(x.f.args.now+15000);assert.throws(()=>x.run());
  assert.ok(fs.readFileSync(x.directory+'/transaction/INTENT.json').equals(original));
  assert.equal(fs.existsSync(x.directory+'/transaction/COMMIT.json'),false);
});
test('production profile and production path are refused before any rehearsal effect',t=>{
  const x=fixture(t);x.f.args.roots.installationProfile='production';
  assert.throws(()=>x.run(),{code:'ISOLATED_REHEARSAL_ONLY'});
  assert.deepEqual(fs.readdirSync(x.directory),[]);
  assert.throws(()=>rehearseRecoveryCutover({directory:'/opt/r16/releases',handoffArgs:x.f.args}),
    {code:'ISOLATED_REHEARSAL_DIRECTORY'});
});
test('formal CLI is explicitly blocked and never treats stage consent as installation authority',()=>{
  const gate=productionCutoverGate();assert.equal(gate.mayInstall,false);assert.equal(gate.mayStartIssuer,false);
  const child=spawnSync(process.execPath,[new URL('../release/stage-installer-reviewed.mjs',import.meta.url).pathname],
    {encoding:'utf8',timeout:5000,env:{PATH:'/usr/bin:/bin'},maxBuffer:4096});
  assert.equal(child.status,1);assert.deepEqual(JSON.parse(child.stdout),gate);
});
