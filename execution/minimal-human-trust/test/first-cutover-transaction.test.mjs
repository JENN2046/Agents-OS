// Real isolated multi-file transactions and fsync journals, synthetic signatures.
// No production Human ceremony, credential, root/service operation or business.
import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {generateKeyPairSync,randomUUID} from 'node:crypto';
import {digest,signed} from '../src/lease-core.mjs';
import {rehearseFirstNativeHumanCutover} from '../release/stage-installer-reviewed.mjs';
import {firstCutoverFixture,SOURCE_FREEZE} from './fixtures/first-cutover-fixture.mjs';

const key=()=>generateKeyPairSync('ed25519').privateKey;
const load=file=>JSON.parse(fs.readFileSync(file));
function fixture(t){
  const x=firstCutoverFixture(t);
  return {...x,source:x,run:extra=>rehearseFirstNativeHumanCutover({directory:x.directory,
    humanArgs:x.humanArgs(),handoffArgs:x.f.args,now:x.now,...extra}),
    tx:name=>x.directory+'/transaction/'+name,
    target:slot=>x.directory+'/installed/'+({issuerState:'issuer/state.json',
      replayState:'replay/state.json',roots:'trust-roots.json',issuerConfig:'issuer.json',
      receipt:'handoff-cutover.receipt.json'}[slot])};
}
const noTargets=x=>{
  assert.equal(fs.existsSync(x.directory+'/installed'),false);
  assert.equal(fs.existsSync(x.directory+'/transaction'),false);
};
const partial=(x,point='after-artifacts')=>{
  assert.throws(()=>x.run({fault:p=>{if(p===point)throw Error('isolated crash '+point);}}));
  assert.equal(fs.existsSync(x.tx('ARTIFACTS.json')),true);
  assert.equal(fs.existsSync(x.tx('COMMIT.json')),false);
  return {intent:fs.readFileSync(x.tx('INTENT.json')),artifacts:fs.readFileSync(x.tx('ARTIFACTS.json'))};
};
const preserved=(x,saved)=>{
  assert.ok(fs.readFileSync(x.tx('INTENT.json')).equals(saved.intent));
  assert.ok(fs.readFileSync(x.tx('ARTIFACTS.json')).equals(saved.artifacts));
  assert.equal(fs.existsSync(x.tx('COMMIT.json')),false);
};

test('first native Human isolated transaction binds exact proposal/OS/signature in durable identity, evidence and receipt',t=>{
  const x=fixture(t),result=x.run();assert.equal(result.transaction.status,'CUTOVER_COMMITTED');
  const intent=load(x.tx('INTENT.json')),artifacts=load(x.tx('ARTIFACTS.json'));
  const admission=intent.identity.nativeHumanAdmission;
  assert.equal(admission.humanProposalHash,digest(x.source.proposal));
  assert.equal(admission.humanApprovalHash,digest(x.source.approval));
  assert.equal(admission.humanOsReceiptHash,digest({osIntent:x.source.osIntent,osResult:x.source.osResult}));
  assert.equal(admission.nonce,x.source.proposal.body.nonce);
  assert.equal(admission.targetHash,digest(x.source.target));
  assert.equal(admission.finalRootsHash,digest(x.source.finalRoots()));
  assert.equal(admission.handoffHash,digest(x.f.args.handoff));
  assert.deepEqual(artifacts.artifacts.evidence.nativeHumanAdmission,admission);
  assert.deepEqual(artifacts.artifacts.evidence.receipt.nativeHumanAdmission,admission);
  assert.deepEqual(load(result.layout.receipt).nativeHumanAdmission,admission);
  assert.deepEqual(result.nativeHumanAdmission,admission);
  assert.equal(intent.identity.expiresAt,Math.min(x.source.proposal.body.expiresAt,
    x.f.args.handoff.body.expiresAt,...Object.values(x.f.args.receipts).map(r=>r.body.expiresAt)));
  for(const flag of ['realHumanEnrolled','realOsStopAttested','productionChanged',
    'mayActivateBusiness','maySettleUnknown','mayReplayUnknown','mayInstall','mayStartIssuer'])assert.equal(result[flag],false,flag);
  assert.equal(admission.mayExecute,false);assert.equal(admission.signerAuthority,false);
  assert.deepEqual(load(result.layout.issuerState),x.f.snapshot);
});

test('missing native Human gate and wrong synthetic Human signature fail before any transaction target exists',t=>{
  const x=fixture(t);assert.throws(()=>x.run({humanArgs:null}),{code:'ISOLATED_REHEARSAL_HUMAN_REQUIRED'});noTargets(x);
  const y=fixture(t);y.source.writeJson(y.source.journalBase+'.result.json',{
    ...y.source.osResult,approval:signed(y.source.approval.body,key())});
  assert.throws(()=>y.run());noTargets(y);
});

test('old stage-only enrollment OS receipt cannot satisfy the new native Human transaction',t=>{
  const x=fixture(t);
  assert.throws(()=>x.run({humanArgs:{...x.source.humanArgs(),
    proposal:x.f.proposal,policy:x.f.policy}}));noTargets(x);
});

test('native Human partial transaction resumes original exact artifacts without rematerialization',t=>{
  const x=fixture(t),saved=partial(x,'after-file:roots');
  const roots=fs.readFileSync(x.target('roots'));
  const result=x.run();assert.equal(result.transaction.status,'CUTOVER_COMMITTED');
  assert.equal(result.transaction.signerCalled,false);
  assert.ok(fs.readFileSync(x.tx('INTENT.json')).equals(saved.intent));
  assert.ok(fs.readFileSync(x.tx('ARTIFACTS.json')).equals(saved.artifacts));
  assert.ok(fs.readFileSync(x.target('roots')).equals(roots));
});

test('new valid Human nonce and OS journal cannot replace an existing partial transaction identity',t=>{
  const x=fixture(t),saved=partial(x);
  x.source.resignProposal({nonce:randomUUID()});x.source.journalize();
  assert.throws(()=>x.run(),{code:'ISOLATED_REHEARSAL_INTENT_DRIFT'});
  preserved(x,saved);assert.equal(fs.existsSync(x.target('issuerState')),false);
});

test('protected OS journal drift after partial roots publication preserves existing bytes and original artifacts',t=>{
  const x=fixture(t),saved=partial(x,'after-file:roots');
  const roots=fs.readFileSync(x.target('roots'));
  x.source.writeJson(x.source.journalBase+'.intent.json',{
    ...x.source.osIntent,challengeHash:digest('different-OS-challenge')});
  assert.throws(()=>x.run(),{code:'ISOLATED_REHEARSAL_INTENT_DRIFT'});
  preserved(x,saved);assert.ok(fs.readFileSync(x.target('roots')).equals(roots));
  assert.equal(fs.existsSync(x.target('issuerConfig')),false);
});

test('Human expiry alone leaves pending durable artifacts without extending or rolling back the attempt',t=>{
  const x=fixture(t);x.source.resignProposal({expiresAt:x.now()+5000});x.source.journalize();
  const saved=partial(x,'after-file:issuerState'),state=fs.readFileSync(x.target('issuerState'));
  x.setNow(x.now()+5000);assert.ok(x.now()<x.f.args.receipts.app.body.expiresAt);
  assert.throws(()=>x.run());preserved(x,saved);
  assert.ok(fs.readFileSync(x.target('issuerState')).equals(state));
  assert.equal(fs.existsSync(x.target('issuerConfig')),false);
});

test('STOP expiry alone leaves pending Human-bound artifacts and never fabricates a newer STOP',t=>{
  const x=fixture(t),saved=partial(x);const before=structuredClone(x.f.args.receipts);
  x.setNow(x.f.args.receipts.app.body.expiresAt);
  assert.ok(x.now()<x.source.proposal.body.expiresAt);
  assert.throws(()=>x.run());preserved(x,saved);
  assert.deepEqual(x.f.args.receipts,before);assert.equal(fs.existsSync(x.target('issuerState')),false);
});

test('fresh Human journal check at a file boundary stops later publication',t=>{
  const x=fixture(t);
  assert.throws(()=>x.run({fault:p=>{
    if(p==='after-file:roots')x.source.writeJson(x.source.journalBase+'.result.json',{
      ...x.source.osResult,approval:signed(x.source.approval.body,key())});
  }}));
  assert.equal(fs.existsSync(x.target('roots')),true);
  assert.equal(fs.existsSync(x.tx('ARTIFACTS.json')),true);
  assert.equal(fs.existsSync(x.tx('COMMIT.json')),false);
  assert.equal(fs.existsSync(x.target('issuerConfig')),false);
});

test('native Human intent-only interruption remains UNKNOWN and never creates replacement artifacts',t=>{
  const x=fixture(t);
  assert.throws(()=>x.run({fault:p=>{if(p==='after-intent')throw Error('isolated crash');}}),{code:'CUTOVER_EFFECT_UNKNOWN'});
  const intent=fs.readFileSync(x.tx('INTENT.json'));
  assert.throws(()=>x.run(),{code:'CUTOVER_EFFECT_UNKNOWN'});
  assert.ok(fs.readFileSync(x.tx('INTENT.json')).equals(intent));
  assert.equal(fs.existsSync(x.tx('ARTIFACTS.json')),false);
  assert.equal(fs.existsSync(x.target('issuerState')),false);
});

test('historical native Human COMMIT after expired windows never restores advanced issuer or replay data',t=>{
  const x=fixture(t),result=x.run();
  const advancedState={...load(result.layout.issuerState),revision:99};
  const advancedReplay={...load(result.layout.replayState),revision:7,
    data:{kind:'mht.issuer-replay.v2',handoff:{epoch:1234},used:[{nonce:'later-result',phase:'RESULT'}]}};
  fs.writeFileSync(result.layout.issuerState,JSON.stringify(advancedState));
  fs.writeFileSync(result.layout.replayState,JSON.stringify(advancedReplay));
  const state=fs.readFileSync(result.layout.issuerState),replay=fs.readFileSync(result.layout.replayState);
  const intent=fs.readFileSync(x.tx('INTENT.json')),artifacts=fs.readFileSync(x.tx('ARTIFACTS.json'));
  const commit=fs.readFileSync(x.tx('COMMIT.json'));
  x.setNow(x.now()+86400000);
  const again=x.run();assert.equal(again.transaction.status,'CUTOVER_ALREADY_COMMITTED');
  assert.equal(again.transaction.historical,true);assert.equal(again.transaction.signerCalled,false);
  assert.ok(fs.readFileSync(result.layout.issuerState).equals(state));
  assert.ok(fs.readFileSync(result.layout.replayState).equals(replay));
  assert.ok(fs.readFileSync(x.tx('INTENT.json')).equals(intent));
  assert.ok(fs.readFileSync(x.tx('ARTIFACTS.json')).equals(artifacts));
  assert.ok(fs.readFileSync(x.tx('COMMIT.json')).equals(commit));
  assert.equal(again.productionChanged,false);assert.equal(again.realHumanEnrolled,false);
});

test('even historical COMMIT refuses a replacement native Human identity without touching advanced replay',t=>{
  const x=fixture(t),result=x.run();
  const advanced=Buffer.from(JSON.stringify({...load(result.layout.replayState),revision:8}));
  fs.writeFileSync(result.layout.replayState,advanced);
  x.source.resignProposal({nonce:randomUUID()});x.source.journalize();
  x.setNow(x.now()+60000);assert.throws(()=>x.run());
  assert.ok(fs.readFileSync(result.layout.replayState).equals(advanced));
});

test('complete source freeze or physical source tampering refuses Human transaction before target effects',t=>{
  for(const mutate of [x=>{
    const freeze=x.source.readJson(SOURCE_FREEZE);delete freeze.files['human/first-cutover-admission.mjs'];
    x.source.writeJson(SOURCE_FREEZE,freeze);
  },x=>x.source.writeBytes('/usr/lib/minimal-human-trust/human/first-cutover-admission.mjs',Buffer.from('unreviewed'))]){
    const x=fixture(t);mutate(x);assert.throws(()=>x.run());noTargets(x);
  }
});

test('source tampering after partial attempt preserves Human-bound journals and blocks resumption',t=>{
  const x=fixture(t),saved=partial(x);
  x.source.writeBytes('/usr/lib/minimal-human-trust/release/cutover-transaction.mjs',Buffer.from('drift'));
  assert.throws(()=>x.run());preserved(x,saved);
  assert.equal(fs.existsSync(x.target('issuerState')),false);
});
