// Protocol tests with synthetic authorities and real temporary journal files.
// No actual OS consent, production signing/STOP/fencing/install or cutover.
import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {generateKeyPairSync,randomUUID} from 'node:crypto';
import {digest,signed,verified} from '../src/lease-core.mjs';
import {REVIEWED_SOURCE_FILES} from '../release/publisher-bootstrap.mjs';
import {validateHumanProposal,humanApprovalBody} from '../human/approval-policy.mjs';
import {validateFirstCutoverTarget,FIRST_CUTOVER_CONSTRAINTS,
  firstCutoverApprovalBody} from '../authority/first-cutover-authorization.mjs';
import {inspectPublishedFirstTrustStage} from '../release/staged-r17-handoff-admission.mjs';
import {deriveFirstCutoverTarget,inspectFirstCutoverInputs,
  inspectFirstCutoverHumanJournal,inspectFirstCutoverHandoffAdmission}
  from '../human/first-cutover-admission.mjs';
import {firstCutoverFixture,FIRST_CUTOVER_PENDING,FIRST_CUTOVER_POLICY,
  SOURCE_FREEZE,INSTALLER,OLD_SNAPSHOT,STAGE_TX} from './fixtures/first-cutover-fixture.mjs';

const key=()=>generateKeyPairSync('ed25519').privateKey;
const input=x=>inspectFirstCutoverInputs(x.humanArgs());
const journal=x=>inspectFirstCutoverHumanJournal(x.humanArgs());
const handoff=x=>inspectFirstCutoverHandoffAdmission({humanArgs:x.humanArgs(),
  finalRoots:x.finalRoots(),handoffArgs:x.f.args,now:x.now()});
const noWrites=(x,fn)=>{
  const before=new Map([...x.protectedFiles].map(([p,file])=>[p,fs.readFileSync(file)]));
  const result=fn();
  for(const [p,bytes] of before)assert.ok(fs.readFileSync(x.protectedFiles.get(p)).equals(bytes),p);
  return result;
};

test('synthetic complete historical stage remains distinct from a fresh first-cutover Human proposal',t=>{
  const x=firstCutoverFixture(t);
  assert.ok(x.f.authorization.expiresAt<x.now(),'old enrollment window already expired');
  assert.ok(x.proposal.body.issuedAt<=x.now()&&x.now()<x.proposal.body.expiresAt);
  const stage=inspectPublishedFirstTrustStage({...x.humanArgs(),priorPublicConfig:x.f.args.priorPublicConfig});
  assert.equal(stage.status,'PUBLISHED_R17_STAGE_INSPECTED');
  assert.deepEqual(deriveFirstCutoverTarget({stage,roots:x.f.args.roots,wrapper:x.f.snapshot,
    sourceFreeze:x.sourceFreeze}),x.target);
  assert.deepEqual(Object.keys(x.sourceFreeze.files).sort(),[...REVIEWED_SOURCE_FILES].sort());
  assert.notEqual(x.proposal.body.nonce,x.f.proposal.body.nonce);
  assert.notEqual(digest(x.proposal),digest(x.f.proposal));
  assert.deepEqual(x.target.constraints,FIRST_CUTOVER_CONSTRAINTS);
  assert.equal(Object.hasOwn(x.target.newRootTemplate,'handoffHash'),false);
  assert.deepEqual(x.target.newRootTemplate,{...Object.fromEntries(Object.entries(x.f.args.roots)
    .filter(([k])=>k!=='handoffHash')),releaseHash:digest(x.f.r17)});
  const inspected=noWrites(x,()=>input(x));
  assert.equal(inspected.signerAuthority,false);assert.equal(inspected.mayExecute,false);
});

test('actual synthetic Human signature and real tempfile OS journals are consumed read-only',t=>{
  const x=firstCutoverFixture(t),body=verified(x.approval,x.humanPublicKey,'mht.first-cutover-authorization.v1');
  assert.equal(body.targetHash,digest(x.target));assert.equal(body.proposalHash,digest(x.proposal));
  assert.equal(body.nonce,x.proposal.body.nonce);assert.equal(body.expiresAt,x.proposal.body.expiresAt);
  assert.equal(Object.hasOwn(body,'target'),false,'proposal hash binds the full concrete target');
  assert.equal(x.readJson(x.journalBase+'.result.json').approval.signature,x.approval.signature);
  const inspected=noWrites(x,()=>journal(x));
  assert.equal(inspected.signerAuthority,false);assert.equal(inspected.mayExecute,false);
});

test('synthetic fresh STOP and fenced-writer proof still require the new Human signature',t=>{
  const x=firstCutoverFixture(t);
  const inspected=noWrites(x,()=>handoff(x));
  assert.equal(inspected.signerAuthority,false);assert.equal(inspected.mayExecute,false);
  const record=x.readJson(x.journalBase+'.result.json');
  record.approval=signed(record.approval.body,key());x.writeJson(x.journalBase+'.result.json',record);
  assert.throws(()=>handoff(x));
});

test('all exact artifact/snapshot/source hashes reject a new publisher signature over a substituted target',t=>{
  const fields=['sourceReleaseHash','grantHash','targetReleaseHash','stageIntentHash','stageResultHash',
    'stageAuthorizationHash','reviewedManifestHash','recoveryEvidenceDigest','issuerSnapshotHash',
    'issuerStateFileHash','sourceFreezeDigest','installerHash','oldRootHash'];
  for(const field of fields){
    const x=firstCutoverFixture(t),target={...x.target,[field]:digest('substitution-'+field)};
    x.resignProposal({target});assert.throws(()=>input(x),field);
  }
});

test('first-cutover target rejects hidden paths, unrestricted commands and old action enrollment consent',t=>{
  for(const extra of [{installerPath:'/tmp/other.mjs'},{issuerPath:'/var/lib/other'},
    {command:'sudo systemctl stop r16-owner'},{mayExecute:true}]){
    const x=firstCutoverFixture(t);x.resignProposal({target:{...x.target,...extra}});
    assert.throws(()=>input(x));
  }
  const x=firstCutoverFixture(t);
  assert.throws(()=>inspectFirstCutoverInputs({...x.humanArgs(),proposal:x.f.proposal,policy:x.f.policy}));
});

test('root template permits only the same protected roots plus signed R17 release hash',t=>{
  const x=firstCutoverFixture(t),roots=x.f.args.roots;
  assert.equal(validateFirstCutoverTarget(x.target,{roots}),x.target);
  const substitutions=[{...x.target.newRootTemplate,handoffHash:digest('premature')},
    {...x.target.newRootTemplate,extraAuthority:true},
    {...x.target.newRootTemplate,installationProfile:'production'},
    {...x.target.newRootTemplate,issuerPublicKey:x.humanPublicKey},
    {...x.target.newRootTemplate,releaseHash:digest(x.f.r15)}];
  for(const newRootTemplate of substitutions){
    const target={...x.target,newRootTemplate,newRootTemplateHash:digest(newRootTemplate)};
    assert.throws(()=>validateFirstCutoverTarget(target,{roots}));
  }
  const missing={...x.target.newRootTemplate};delete missing.releasePublicKey;
  assert.throws(()=>validateFirstCutoverTarget({...x.target,newRootTemplate:missing,
    newRootTemplateHash:digest(missing)},{roots}));
});

test('none of the Human constraints may be expanded or weakened',t=>{
  const x=firstCutoverFixture(t);
  for(const field of Object.keys(FIRST_CUTOVER_CONSTRAINTS)){
    const target={...x.target,constraints:{...x.target.constraints,[field]:!x.target.constraints[field]}};
    assert.throws(()=>validateFirstCutoverTarget(target,{roots:x.f.args.roots}),field);
  }
  assert.equal(x.target.constraints.mayActivateBusiness,false);
  assert.equal(x.target.constraints.maySettleUnknown,false);
  assert.equal(x.target.constraints.mayReplayUnknown,false);
});

test('epoch and grant substitutions cannot detach Human consent from the one staged transaction',t=>{
  for(const patch of [{stopEpoch:randomUUID()},{handoffEpoch:1235},{grantVersion:2},
    {sourceReleaseId:'r16-daily-20261012-r14'},{targetReleaseId:'r16-daily-20261012-r18'},
    {grantId:'another-grant'},{phase:'ACTIVATE_BUSINESS'}]){
    const x=firstCutoverFixture(t);x.resignProposal({target:{...x.target,...patch}});
    assert.throws(()=>input(x));
  }
});

test('tampered stage RESULT or signed Release cannot become a new Human first-cutover target',t=>{
  for(const mutate of [result=>{result.intentHash=digest('foreign-intent');},
    result=>{result.signedArtifacts.release=signed(result.signedArtifacts.release.body,key());},
    result=>{result.signedArtifacts.enrollment=signed(result.signedArtifacts.enrollment.body,key());},
    result=>{result.signedArtifacts.mayHandoffIssuer=true;}]){
    const x=firstCutoverFixture(t),result=x.readJson(STAGE_TX+'/result.json');mutate(result);
    x.writeJson(STAGE_TX+'/result.json',result);assert.throws(()=>input(x));
  }
});

test('complete freeze and installer dependency byte tampering reject before a Human receipt is accepted',t=>{
  for(const logical of [INSTALLER,'/usr/lib/minimal-human-trust/release/cutover-transaction.mjs',
    '/usr/lib/minimal-human-trust/src/lease-core.mjs']){
    const x=firstCutoverFixture(t);x.writeBytes(logical,Buffer.from('tampered source bytes'));
    assert.throws(()=>input(x),logical);
  }
  const x=firstCutoverFixture(t),freeze=x.readJson(SOURCE_FREEZE);
  delete freeze.files['src/lease-core.mjs'];x.writeJson(SOURCE_FREEZE,freeze);
  assert.throws(()=>input(x));
});

test('whole snapshot wrapper is immutable even when inner issuer data has not changed',t=>{
  const x=firstCutoverFixture(t),wrapper=x.readJson(OLD_SNAPSHOT);
  wrapper.revision++;x.writeJson(OLD_SNAPSHOT,wrapper);assert.throws(()=>input(x));
});

test('wrapper, freeze and installer changing between bounded reads are refused',t=>{
  for(const logical of [OLD_SNAPSHOT,SOURCE_FREEZE,INSTALLER]){
    const x=firstCutoverFixture(t);let count=0;
    const readProtected=file=>{
      if(file===logical&&++count===2){
        if(logical===INSTALLER)x.writeBytes(file,Buffer.from('changed-between-reads'));
        else {const value=x.readJson(file);
          if(logical===OLD_SNAPSHOT)value.revision++;
          else value.sourceCommit='b'.repeat(40);
          x.writeJson(file,value);}
      }
      return x.readProtected(file);
    };
    assert.throws(()=>inspectFirstCutoverInputs({...x.humanArgs(),readProtected}),logical);
    assert.ok(count>=2,logical);
  }
});

test('a forged publisher proposal cannot be admitted by merely changing its policy digest',t=>{
  const x=firstCutoverFixture(t),proposal=signed(x.proposal.body,key());
  assert.throws(()=>inspectFirstCutoverInputs({...x.humanArgs(),proposal,
    policy:{...x.policy,proposalHash:digest(proposal)}}),{code:'BAD_SIGNATURE'});
});

test('future, expired and overlong first-cutover windows cannot reuse historical stage approval',t=>{
  for(const patch of [{issuedAt:1792200000001},{expiresAt:1792200000000},
    {issuedAt:1792199699999,expiresAt:1792200000001}]){
    const x=firstCutoverFixture(t);x.resignProposal(patch);assert.throws(()=>input(x));
  }
  const x=firstCutoverFixture(t),checked=validateHumanProposal({...x.humanArgs(),now:x.now()});
  assert.equal(humanApprovalBody(checked,{now:x.approvedAt}).schema,'mht.first-cutover-authorization.v1');
  assert.throws(()=>firstCutoverApprovalBody(checked,{now:x.proposal.body.expiresAt}));
  x.setNow(x.proposal.body.expiresAt);assert.throws(()=>journal(x));
});

test('intent-only native Human attempt is unusable and no missing result is synthesized',t=>{
  const x=firstCutoverFixture(t),file=x.protectedFiles.get(x.journalBase+'.result.json');
  fs.unlinkSync(file);assert.throws(()=>journal(x));assert.equal(fs.existsSync(file),false);
  assert.equal(x.readJson(x.journalBase+'.intent.json').proposalHash,digest(x.proposal));
});

test('OS uid, time, proposal and signed Human result substitutions cannot authorize the target',t=>{
  for(const patch of [{peerUid:0},{processStart:0},{proposalHash:digest('other')},
    {confirmedAt:1792200000001},{confirmedAt:1792199000000},{challengeHash:'invalid'}]){
    const x=firstCutoverFixture(t);x.writeJson(x.journalBase+'.intent.json',{...x.osIntent,...patch});
    assert.throws(()=>journal(x));
  }
  for(const patch of [{approval:null},{approval:signed({schema:'mht.first-cutover-authorization.v1'},key())},
    {proposalHash:digest('other')},{firstTrustOsConfirmationOnly:true},{status:'APPLIED'}]){
    const x=firstCutoverFixture(t);x.writeJson(x.journalBase+'.result.json',{...x.osResult,...patch});
    assert.throws(()=>journal(x));
  }
});

test('nonce replacement or a signature from another Human cannot replay the original OS journal',t=>{
  const x=firstCutoverFixture(t),oldJournal=x.journalBase;
  x.resignProposal({nonce:randomUUID()});assert.throws(()=>journal(x));
  assert.equal(x.readJson(oldJournal+'.result.json').proposalHash,x.osResult.proposalHash);
  const y=firstCutoverFixture(t);y.writeJson(y.journalBase+'.result.json',{
    ...y.osResult,approval:signed(y.approval.body,key())});assert.throws(()=>journal(y));
});

test('even correctly Human-signed authorization must bind every exact target and nonce field',t=>{
  for(const field of ['proposalHash','grantId','grantHash','grantVersion','sourceReleaseHash',
    'targetReleaseHash','nonce','expiresAt','targetHash']){
    const x=firstCutoverFixture(t),body={...x.approval.body};
    body[field]=typeof body[field]==='number'?body[field]+1:field==='grantId'?'other-grant':digest('other-'+field);
    x.writeJson(x.journalBase+'.result.json',{...x.osResult,approval:signed(body,x.humanKey)});
    assert.throws(()=>journal(x),field);
  }
  for(const issuedAt of [1792200000001,1792199997998]){
    const x=firstCutoverFixture(t);
    x.writeJson(x.journalBase+'.result.json',{...x.osResult,
      approval:signed({...x.approval.body,issuedAt},x.humanKey)});
    assert.throws(()=>journal(x));
  }
});

test('a stage-era STOP, handoff or recovery observation cannot predate new Human consent',t=>{
  for(const field of ['issuedAt','observedAt']){
    const x=firstCutoverFixture(t),body=structuredClone(x.f.args.handoff.body);
    if(field==='observedAt')body.recoveryAdmission.observedAt=x.approvedAt-1;
    else body.issuedAt=x.approvedAt-1;
    x.f.args.handoff=signed(body,x.f.enroller);assert.throws(()=>handoff(x));
  }
  const x=firstCutoverFixture(t);
  const role='app';x.f.args.receipts[role]=signed({...x.f.args.receipts[role].body,
    issuedAt:x.approvedAt-1},x.f.signers[role]);
  x.f.args.handoff=signed({...x.f.args.handoff.body,participantClosureHashes:{
    ...x.f.args.handoff.body.participantClosureHashes,[role]:digest(x.f.args.receipts[role])}},x.f.enroller);
  assert.throws(()=>handoff(x));
});

test('final protected root and handoff must match the exact template and admitted signed certificate',t=>{
  const x=firstCutoverFixture(t);
  for(const patch of [{handoffHash:digest('other')},{releaseHash:digest(x.f.r15)},
    {extraAuthority:true},{enrollmentAuthorityPublicKey:x.humanPublicKey}]){
    assert.throws(()=>inspectFirstCutoverHandoffAdmission({humanArgs:x.humanArgs(),
      handoffArgs:x.f.args,finalRoots:{...x.finalRoots(),...patch},now:x.now()}));
  }
});

test('pending proposal drift and unprivileged admission fail without changing any journal bytes',t=>{
  const x=firstCutoverFixture(t);
  assert.throws(()=>inspectFirstCutoverInputs({...x.humanArgs(),euid:1000}));
  x.writeJson(FIRST_CUTOVER_PENDING,signed({...x.proposal.body,nonce:randomUUID()},x.f.releaseKey));
  // Inputs receive the signer-loaded fixed proposal/policy; they do not
  // independently invent another pending-file load operation.
  assert.throws(()=>inspectFirstCutoverInputs({...x.humanArgs(),
    proposal:x.readJson(FIRST_CUTOVER_PENDING),policy:x.readJson(FIRST_CUTOVER_POLICY)}));
  const y=firstCutoverFixture(t),policy={...y.policy,humanPublicKey:exportHumanOther()};
  y.writeJson(FIRST_CUTOVER_POLICY,policy);
  assert.throws(()=>inspectFirstCutoverHumanJournal({...y.humanArgs(),
    proposal:y.readJson(FIRST_CUTOVER_PENDING),policy:y.readJson(FIRST_CUTOVER_POLICY)}));
});
function exportHumanOther(){
  // Use an actual valid public key, so refusal is caused by the wrong binding.
  return generateKeyPairSync('ed25519').publicKey.export({type:'spki',format:'der'}).toString('base64url');
}
