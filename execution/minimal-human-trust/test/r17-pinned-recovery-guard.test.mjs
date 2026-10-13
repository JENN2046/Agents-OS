import test from 'node:test';
import assert from 'node:assert/strict';
import {EXACT_R17_MIGRATION_SCOPE,inspectRecoveryMigrationEvidence,
  inspectReviewedR17MigrationEvidence}
  from '../migration/r17-one-time-recovery-admission.mjs';

const digest='c'.repeat(64);
const policy=()=>({
  ...EXACT_R17_MIGRATION_SCOPE,reviewDigest:digest,
  projects:EXACT_R17_MIGRATION_SCOPE.projects.map(x=>({...x}))
});
const nope=(e,code)=>assert.throws(e,{code});
test('only two fixed original read-result operation identities may enter recovery',()=>{
 const pins=EXACT_R17_MIGRATION_SCOPE.projects;
 assert.equal(pins.length,2);
 assert.deepEqual(pins.map(x=>x.projectId).sort(),['p2vox','pmog2']);
 assert.deepEqual(pins.map(x=>x.generation).sort((a,b)=>a-b),[30,38]);
 assert.equal(pins[0].operationId,'c434da49-055a-43dc-a3e3-695cce137909');
 assert.equal(pins[1].operationId,'d0364f8b-3a68-4ca2-a396-7953b29cee4c');
});
test('caller cannot replace historical operation ID or old signed hash',()=>{
 for(const patch of [{operationId:'fake-read'},{operationHash:'a'.repeat(64)},{generation:37}]){
   const p=policy();p.projects[1]={...p.projects[1],...patch};
   nope(()=>inspectRecoveryMigrationEvidence({},p,()=>{}),'R17_SCOPE_NOT_PINNED');
 }
});
test('unreviewed Release ID and missing exact digest refuse admission',()=>{
 const p=policy();p.targetRelease='r16-daily-20261012-r18';
 nope(()=>inspectRecoveryMigrationEvidence({},p,()=>{}),'R17_SCOPE_NOT_PINNED');
 nope(()=>inspectReviewedR17MigrationEvidence({},'abc',()=>{}),'REVIEW_NOT_EXACT');
});
test('non-live Crown proof verifier does not authorize recovery',()=>{
 const p=policy();nope(()=>inspectRecoveryMigrationEvidence({},p,null),'R17_MIGRATION_REJECTED');
});
test('even a correctly pinned policy with no production states is denied',()=>{
 const p=policy();assert.throws(()=>inspectRecoveryMigrationEvidence({},p,()=>{}));
});
