import test from 'node:test';
import assert from 'node:assert/strict';
import {drive} from './transaction-driver.mjs';
const error=code=>Object.assign(Error(code),{code});
function fixture({code='CLOUD_APP_SELECTOR_CAS_CONFLICT',proof='unchanged',restore=['OS_ACTIVE']}={}){
 const records=new Map(),calls=[];
 const journal={read:n=>records.get(n),write:(n,v)=>records.set(n,structuredClone(v))};
 const publication={delivery:{body:{revision:17}}};let restores=0;
 const adapters={baseline:()=>({}),quiesce:()=>({}),observe:()=>{},stage:()=>({}),sign:()=>{calls.push('sign');return publication;},
  cloudCommit:()=>{calls.push('cloudCommit');throw error(code);},localCommit:()=>{calls.push('localCommit');},
  confirmUncommitted:()=>{calls.push('confirm');if(proof==='refused')throw error('SOURCE_CONFIGURATION_DRIFT');return {status:proof==='unchanged'?'SOURCE_CONFIGURATION_UNCHANGED':'NOT_PROVEN',sourceDeliveryHash:'a'.repeat(64)};},
  resume:()=>{calls.push('resume');return {status:restore[Math.min(restores++,restore.length-1)]};},
  requiesce:()=>{calls.push('requiesce');return {};},accepted:()=>{calls.push('accepted');return {};},
  signRollback:()=>{calls.push('rollbackSign');throw error('ROLLBACK_ACCEPTED_SCOPE_CHANGED');}};
 return {records,journal,calls,adapters};
}
test('R6 definitive remote precommit refusal plus fresh source proof aborts without rollback signing',async()=>{
 const f=fixture(),r=await drive(f);assert.equal(r.status,'ABORTED_BEFORE_CONFIGURATION_CHANGE');
 assert.deepEqual(f.calls,['sign','cloudCommit','confirm','resume']);assert(f.records.has('signed'));
 assert.equal(f.records.get('transaction').steps['cloud-commit'].status,'INTENT');assert.equal(f.records.get('transaction').mode,'ABORT');
 const before=structuredClone([...f.records]);assert.equal((await drive(f)).historicalReadOnly,true);assert.deepEqual([...f.records],before);
});
test('R6 partial abort restore rechecks unchanged source and completes without reentering forward',async()=>{
 const f=fixture({restore:['RESTORE_PARTIAL','OS_ACTIVE']});assert.equal((await drive(f)).status,'RECOVERY_REQUIRED_SERVICES_MAY_REMAIN_FENCED');
 const first=f.records.get('uncommitted-readback-attempt-1');assert.equal((await drive(f)).status,'ABORTED_BEFORE_CONFIGURATION_CHANGE');
 assert.deepEqual(f.records.get('uncommitted-readback-attempt-1'),first);
 for(const name of ['sign','cloudCommit'])assert.equal(f.calls.filter(x=>x===name).length,1);
 assert.equal(f.calls.filter(x=>x==='confirm').length,2);assert(!f.calls.includes('rollbackSign'));
});
for(const proof of ['refused','not-proven'])test('R6 refuses original-state abort when fresh proof is '+proof,async()=>{
 const f=fixture({proof});assert.equal((await drive(f)).status,'RECOVERY_REQUIRED_SERVICES_MAY_REMAIN_FENCED');
 assert(!f.calls.includes('resume'));assert(!f.calls.includes('rollbackSign'));assert(!f.records.has('receipt'));
});
for(const code of ['FIXED_COMMAND_FAILED','REMOTE_TIMEOUT','EFFECT_UNKNOWN'])test('R6 '+code+' cannot use a momentary source readback as a completed no-effect proof',async()=>{
 const f=fixture({code});assert.equal((await drive(f)).status,'RECOVERY_REQUIRED_SERVICES_MAY_REMAIN_FENCED');
 assert(!f.calls.includes('confirm'));assert(!f.calls.includes('resume'));assert(!f.records.has('receipt'));
});
test('R6 durable accepted cloud-commit is never reclassified as a precommit abort',async()=>{
 const f=fixture();f.adapters.cloudCommit=()=>({status:'CONFIGURATION_COMMITTED_SERVICES_FENCED'});
 f.adapters.localCommit=()=>{throw error('CLOUD_APP_SELECTOR_CAS_CONFLICT');};
 assert.equal((await drive(f)).status,'RECOVERY_REQUIRED_SERVICES_MAY_REMAIN_FENCED');
 assert.equal(f.records.get('transaction').steps['cloud-commit'].status,'DONE');assert(!f.calls.includes('confirm'));assert(!f.calls.includes('resume'));
});
