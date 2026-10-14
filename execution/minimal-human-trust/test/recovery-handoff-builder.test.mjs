import test from 'node:test';
import assert from 'node:assert/strict';
import {digest,signed} from '../src/lease-core.mjs';
import {buildRecoveryHandoffAdmission} from '../release/recovery-handoff-builder.mjs';
import {EXACT_R17_MIGRATION_SCOPE} from '../migration/r17-one-time-recovery-admission.mjs';
import {stagedRecoveryFixture} from './fixtures/staged-recovery-fixture.mjs';

function fixture(){
  const f=stagedRecoveryFixture();const pub=f.args.priorPublicConfig;
  const records=EXACT_R17_MIGRATION_SCOPE.projects.map(row=>{
    const project=f.snapshot.data.grants[0].projects.find(p=>p.projectId===row.projectId);
    // Same labels and valid synthetic signatures cannot replace the immutable
    // original production operation envelope/hash. This is a negative fixture.
    const operation=signed({schema:'r16.operation.v1',id:row.operationId,
      grantId:pub.grant.body.id,projectId:row.projectId,generation:row.generation,
      leaseHash:digest(project.active.lease),channel:'main',action:'find_symbol',
      payloadHash:digest('synthetic-crown-call')},f.signers.app);
    return {...row,id:row.operationId,status:'UNKNOWN',operation};
  });
  const evidence={publicConfiguration:pub,issuerState:f.snapshot.data,
    ownerConfiguration:{kind:'r16.owner.configuration.v1',activeGrantId:pub.grant.body.id,
      trust:{releasePublicKey:pub.releasePublicKey},replacement:null,blockedProjects:[]},
    appState:{operations:records},bridgeState:{calls:records},nativeStates:{},
    appProjectStates:{},bridgeProjectStates:{},appArchives:Object.fromEntries(records.map(row=>
      [row.projectId,{operation:row.operation}])),nativeResults:{p2vox:false,pmog2:false},
    reviewManifest:f.args.reviewManifest,now:f.intent.approvedAt};
  const authorization={...f.authorization,recoveryEvidenceDigest:digest(evidence)};
  let crownCalls=0;
  const args={evidence,wrapper:f.snapshot,stageAuthorization:authorization,
    priorPublicConfig:pub,reviewManifest:f.args.reviewManifest,now:f.args.now,approvedAt:f.intent.approvedAt,
    verifyCrownCall:()=>{crownCalls++;throw Error('no production proof');}};
  return {f,args,crownCalls:()=>crownCalls};
}
test('receiver certificate builder requires original cryptographic operation, not matching fixture labels',()=>{
  const x=fixture();const before=structuredClone(x.args.evidence);
  assert.throws(()=>buildRecoveryHandoffAdmission(x.args),{code:'RESULT_OR_SCOPE_MISMATCH'});
  // Populate Native shape, then prove that a differently signed operation is
  // rejected even with the right two IDs/generations/actions and source digest.
  for(const row of EXACT_R17_MIGRATION_SCOPE.projects)x.args.evidence.nativeStates[row.projectId]={};
  x.args.stageAuthorization.recoveryEvidenceDigest=digest(x.args.evidence);
  assert.throws(()=>buildRecoveryHandoffAdmission(x.args),{code:'READ_OPERATION_NOT_EXACT'});
  assert.equal(x.crownCalls(),0);
  assert.deepEqual(x.f.snapshot.data,before.issuerState);
});
test('a replacement evidence digest or changed protected snapshot data cannot build an attestation',()=>{
  for(const change of [x=>{x.args.evidence.nativeResults.p2vox=true;},
    x=>{x.args.wrapper.data.grants[0].status='REVOKED';}]){
    const x=fixture();change(x);assert.throws(()=>buildRecoveryHandoffAdmission(x.args),
      {code:'RECOVERY_SOURCE_EVIDENCE_DRIFT'});
  }
});
test('invalid or expanded stage authority is rejected before the Crown verifier is invoked',()=>{
  for(const change of [x=>{x.args.stageAuthorization.constraints.mayInstall=true;},
    x=>{x.args.stageAuthorization.targetReleaseId='foreign-r17';},
    x=>{x.args.stageAuthorization.expiresAt=x.args.stageAuthorization.issuedAt+300001;}]){
    const x=fixture();change(x);assert.throws(()=>buildRecoveryHandoffAdmission(x.args));
    assert.equal(x.crownCalls(),0);
  }
});
test('historical evidence may precede stage consent but never outlive its five minute freshness',()=>{
  const x=fixture();x.args.evidence.now=x.args.stageAuthorization.issuedAt-1;
  x.args.stageAuthorization.recoveryEvidenceDigest=digest(x.args.evidence);
  assert.throws(()=>buildRecoveryHandoffAdmission(x.args),{code:'RESULT_OR_SCOPE_MISMATCH'});
  for(const evidenceTime of [x.args.approvedAt+1,x.args.approvedAt-300001]){
    const y=fixture();y.args.evidence.now=evidenceTime;
    assert.throws(()=>buildRecoveryHandoffAdmission(y.args),{code:'RECOVERY_HISTORICAL_APPROVAL_TIME'});
    assert.equal(y.crownCalls(),0);
  }
});
