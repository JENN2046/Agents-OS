import test from 'node:test';
import assert from 'node:assert/strict';
import childProcess from 'node:child_process';
import {syncBuiltinESMExports} from 'node:module';
import {command,digest} from './io.mjs';
import {remote} from './run.mjs';
import {drive} from './transaction-driver.mjs';

// Exercise the actual adapter and command implementation while prohibiting any
// SSH, root helper or service invocation. Restore ESM builtin bindings per test.
function fakeSpawn(t,fn){
  const original=childProcess.spawnSync;
  childProcess.spawnSync=fn;syncBuiltinESMExports();
  t.after(()=>{childProcess.spawnSync=original;syncBuiltinESMExports();});
}
const success={status:0,stdout:'{"status":"OFFLINE_RESPONSE"}'};
const timeout=()=>({status:null,signal:'SIGTERM',error:Object.assign(Error('synthetic child timeout'),{code:'ETIMEDOUT'}),stdout:'',stderr:'must not be disclosed'});

test('fixed SSH stage outer budget exceeds 120s helper while readback and commit stay at 30s',t=>{
  const calls=[];fakeSpawn(t,(...args)=>{calls.push(args);return success;});
  const plan={schema:'isolated-transport-budget',nonce:'fixed-offline-plan'};
  for(const action of ['stage','readback','commit']){
    assert.equal(remote(action,plan,{sourceAppSelectorHash:'a'.repeat(64)}).status,'OFFLINE_RESPONSE');
    const [file,args,options]=calls.at(-1);
    assert.equal(file,'/usr/bin/ssh');
    assert.equal(args.at(-1),'/usr/bin/sudo -n /usr/libexec/r16-maintenance-os-r6 '+action+' '+digest(plan));
    assert.equal(options.timeout,action==='stage'?150000:30000);
    assert.equal(JSON.parse(options.input).planHash,digest(plan));
    assert.deepEqual(options.stdio,['pipe','pipe','ignore']);
  }
  assert.equal(calls.length,3);
});

test('ETIMEDOUT has a fixed low-disclosure error even when stdout contains a success JSON',t=>{
  fakeSpawn(t,()=>({...timeout(),status:0,stdout:'{"status":"PAYLOAD_INSTALLED_NOT_SELECTED"}'}));
  assert.throws(()=>command('/fixed/offline-child',[],undefined,5),error=>{
    assert.equal(error.code,'FIXED_COMMAND_TIMEOUT');
    assert.equal(error.message,'FIXED_COMMAND_TIMEOUT');
    assert(!JSON.stringify(error).includes('must not be disclosed'));
    return true;
  });
});

test('non-timeout child refusals preserve safe typed codes and keep malformed output generic',t=>{
  const results=[{status:1,stdout:'{"code":"CLOUD_PAYLOAD_INVENTORY_DRIFT"}'},
    {status:null,error:{code:'ENOENT'},stdout:'',stderr:'private synthetic diagnostic'},
    {status:1,stdout:'{"code":"not a safe fixed code"}',stderr:'private synthetic diagnostic'}];
  fakeSpawn(t,()=>results.shift());
  for(const code of ['CLOUD_PAYLOAD_INVENTORY_DRIFT','FIXED_COMMAND_FAILED','FIXED_COMMAND_FAILED']){
    assert.throws(()=>command('/fixed/offline-child',[]),{code,message:code});
  }
});

test('a real disposable child timeout is reported without any network or root command',()=>{
  assert.throws(()=>command(process.execPath,['-e','setTimeout(()=>{},10000)'],undefined,20),{code:'FIXED_COMMAND_TIMEOUT'});
});

test('late payload-stage completion cannot take a persisted ABORT back to stage or signing',async t=>{
  const transport=[];fakeSpawn(t,(file,args,options)=>{transport.push({file,args,timeout:options.timeout});return timeout();});
  const records=new Map(),calls=[];
  const journal={read:name=>records.get(name),write:(name,value)=>records.set(name,structuredClone(value))};
  let lateStageResult=null,restores=0;
  const adapters={baseline:()=>({status:'BASELINE_SAVED'}),quiesce:()=>({status:'OS_QUIESCENT_FIXED_ROLES_ONLY'}),observe:()=>{},
    stage:()=>{calls.push('stage');return lateStageResult||remote('stage',{schema:'isolated-stage-plan'});},
    resume:()=>{calls.push('resume');return {status:restores++?'OS_ACTIVE':'RESTORE_PARTIAL'};}};
  for(const name of ['sign','cloudCommit','localCommit','activate','requiesce','accepted','signRollback','confirmUncommitted']){
    adapters[name]=()=>{calls.push(name);throw Error('FORWARD_OR_SIGNING_MUST_NOT_BE_CALLED');};
  }
  const first=await drive({journal,adapters});
  assert.equal(first.status,'RECOVERY_REQUIRED_SERVICES_MAY_REMAIN_FENCED');
  assert.equal(first.failureCode,'FIXED_COMMAND_TIMEOUT');
  assert.equal(records.get('transaction').mode,'ABORT');
  assert.equal(records.get('transaction').steps.payload.status,'INTENT');
  const attempt1=structuredClone(records.get('abort-resume-attempt-1'));
  // The remote filesystem operation can finish after the SSH client timed out.
  // Its late result is available to stage, which the ABORT path must not call.
  lateStageResult={status:'PAYLOAD_INSTALLED_NOT_SELECTED'};
  const second=await drive({journal,adapters});
  assert.equal(second.status,'ABORTED_BEFORE_CONFIGURATION_CHANGE');
  assert.equal(second.businessAcceptance,false);
  assert.equal(records.get('transaction').mode,'ABORT');
  assert.equal(records.get('transaction').steps.payload.status,'INTENT');
  assert.deepEqual(records.get('abort-resume-attempt-1'),attempt1);
  assert.deepEqual(calls,['stage','resume','resume']);
  assert.equal(transport.length,1);
  assert(!records.has('payload'));assert(!records.has('signed'));
  const before=structuredClone([...records]);
  assert.equal((await drive({journal,adapters})).historicalReadOnly,true);
  assert.deepEqual([...records],before);assert.equal(transport.length,1);
});

test('a cloud commit timeout remains uncertain and is never reclassified as a harmless precommit refusal',async t=>{
  fakeSpawn(t,()=>timeout());
  const records=new Map(),calls=[];
  const journal={read:name=>records.get(name),write:(name,value)=>records.set(name,structuredClone(value))};
  const adapters={baseline:()=>({}),quiesce:()=>({}),observe:()=>{},stage:()=>({}),
    sign:()=>({delivery:{body:{revision:17}}}),cloudCommit:()=>remote('commit',{schema:'isolated-commit-plan'}),
    requiesce:()=>{throw Object.assign(Error('ISOLATED_ROLLBACK_REFUSED'),{code:'ISOLATED_ROLLBACK_REFUSED'});},
    confirmUncommitted:()=>calls.push('confirm'),resume:()=>calls.push('resume')};
  const result=await drive({journal,adapters});
  assert.equal(result.status,'RECOVERY_REQUIRED_SERVICES_MAY_REMAIN_FENCED');
  assert.equal(result.failureCode,'FIXED_COMMAND_TIMEOUT');
  assert.equal(records.get('transaction').mode,'ROLLBACK');
  assert.equal(records.get('transaction').steps['cloud-commit'].status,'INTENT');
  assert.deepEqual(calls,[]);assert(!records.has('receipt'));
});
