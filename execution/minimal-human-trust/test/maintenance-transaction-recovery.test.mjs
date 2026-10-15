import test from 'node:test';
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {drive} from '../maintenance/transaction-driver.mjs';

const copy=structuredClone;
const canonical=x=>x===null||typeof x!=='object'?JSON.stringify(x):Array.isArray(x)?'['+x.map(canonical).join(',')+']':'{'+Object.keys(x).sort().map(k=>JSON.stringify(k)+':'+canonical(x[k])).join(',')+'}';
const digest=x=>createHash('sha256').update(canonical(x)).digest('hex');
const failure=code=>Object.assign(Error(code),{code});
function fixture(seed={}){
  const data=new Map(Object.entries(seed).map(([k,v])=>[k,copy(v)]));
  const journal={read:k=>data.has(k)?copy(data.get(k)):null,write:(k,v)=>data.set(k,copy(v))};
  const calls=[],state={revision:16,signs:0,rollbackSigns:0,starts:0,running:true};
  const publication={delivery:{body:{revision:17}}};
  const adapters={
    baseline:()=>{calls.push('baseline');return {running:true};},
    quiesce:()=>{calls.push('quiesce');state.running=false;return {quiet:true};},
    observe:()=>{assert.equal(state.running,false);return {quiet:true};},
    stage:()=>({installed:true}),
    sign:()=>{calls.push('sign');state.signs++;return copy(publication);},
    cloudCommit:d=>{calls.push('cloud'+d.body.revision);state.revision=d.body.revision;return {revision:state.revision};},
    localCommit:p=>{calls.push('local'+p.delivery.body.revision);return {revision:p.delivery.body.revision};},
    activate:()=>{calls.push('activate');if(!state.running){state.starts++;state.running=true;}return {status:'OS_ACTIVE'};},
    requiesce:()=>{calls.push('requiesce');state.running=false;return {quiet:true};},
    resume:()=>{calls.push('resume');if(!state.running){state.starts++;state.running=true;}return {status:'OS_ACTIVE'};},
    accepted:()=>({body:{revision:state.revision}}),
    signRollback:()=>{state.rollbackSigns++;return {delivery:{body:{revision:18}}};},
    verify:d=>{calls.push('verify');assert(state.running);assert.equal(d.body.revision,state.revision);return {revision:state.revision};},
  };
  return {journal,data,calls,state,adapters,run:options=>drive({journal,adapters,now:()=>1000,...options})};
}
const aborted=steps=>({schema:'r16.maintenance-transaction.v3',mode:'ABORT',steps:{quiesce:{status:'INTENT'},...steps},failures:[{at:900,code:'GRACEFUL_STOP_INCOMPLETE'}],nonce:'unchanged-authority-nonce'});

test('partial abort remains pending, then fresh restoration closes without re-entering forward work',async()=>{
  const f=fixture();f.adapters.sign=()=>{f.state.signs++;throw failure('SIGNER_EFFECT_UNKNOWN');};
  let resumes=0;f.adapters.resume=()=>++resumes===1?{status:'RESTORE_PARTIAL'}:{status:'OS_ACTIVE'};
  assert.equal((await f.run()).status,'RECOVERY_REQUIRED_SERVICES_MAY_REMAIN_FENCED');
  const first=f.journal.read('abort-resume-attempt-1');
  assert.equal(first.status,'RESTORE_PARTIAL');assert.equal(f.journal.read('receipt'),null);
  assert.equal(f.journal.read('transaction').steps['abort-resume'].status,'INTENT');
  const forwardCount=f.calls.filter(x=>x==='quiesce').length;
  const result=await f.run();assert.equal(result.status,'ABORTED_BEFORE_CONFIGURATION_CHANGE');
  assert.equal(resumes,2);assert.equal(f.state.signs,1);assert.equal(f.state.rollbackSigns,0);
  assert.equal(f.calls.filter(x=>x==='quiesce').length,forwardCount);
  assert.deepEqual(f.journal.read('abort-resume-attempt-1'),first);
  assert.deepEqual(f.journal.read('transaction').reconciliationAttempts['abort-resume'].map(a=>a.status),['PENDING','DONE']);
});

test('legacy DONE(partial) is preserved as history and cannot block fresh reconciliation',async()=>{
  const old={status:'RESTORE_PARTIAL',activeUnits:['owner'],unconfirmedUnits:['app']};
  const step={status:'DONE',resultHash:digest(old)};
  const f=fixture({transaction:aborted({'abort-resume':step}),'abort-resume':old});
  const before=copy(old);assert.equal((await f.run()).status,'ABORTED_BEFORE_CONFIGURATION_CHANGE');
  assert.deepEqual(f.journal.read('abort-resume'),before);
  assert.deepEqual(f.journal.read('transaction').steps['abort-resume'],step);
  assert.equal(f.journal.read('transaction').nonce,'unchanged-authority-nonce');
  assert.deepEqual(f.calls,['resume']);assert.equal(f.state.signs,0);
});

test('legacy cached OS_ACTIVE never substitutes for a current failed restoration',async()=>{
  const old={status:'OS_ACTIVE'},f=fixture({transaction:aborted({'abort-resume':{status:'DONE',resultHash:digest(old)}}),'abort-resume':old});
  f.adapters.resume=()=>({status:'RESTORE_PARTIAL'});
  assert.equal((await f.run()).status,'RECOVERY_REQUIRED_SERVICES_MAY_REMAIN_FENCED');
  assert.equal(f.journal.read('receipt'),null);assert.deepEqual(f.journal.read('abort-resume'),old);
});

test('legacy completed result corruption is refused before a restoration action',async()=>{
  const old={status:'RESTORE_PARTIAL'};
  const f=fixture({transaction:aborted({'abort-resume':{status:'DONE',resultHash:digest(old)}}),'abort-resume':{status:'OS_ACTIVE'}});
  assert.equal((await f.run()).recoveryCode,'TRANSACTION_RESULT_CORRUPT');
  assert.deepEqual(f.calls,[]);assert.equal(f.journal.read('receipt'),null);
  assert.deepEqual(f.journal.read('abort-resume'),{status:'OS_ACTIVE'});
});

test('repeated partial results append attempts without replacing previous evidence',async()=>{
  const f=fixture({transaction:aborted()});let n=0;f.adapters.resume=()=>({status:'RESTORE_PARTIAL',observation:++n});
  await f.run();const first=f.journal.read('abort-resume-attempt-1');await f.run();
  assert.deepEqual(f.journal.read('abort-resume-attempt-1'),first);
  assert.equal(f.journal.read('abort-resume-attempt-2').observation,2);
  assert.equal(f.journal.read('receipt'),null);assert.equal(f.state.signs,0);
});

test('expired adapter authority leaves recovery pending without new signing or nonce',async()=>{
  const f=fixture({transaction:aborted()});f.adapters.resume=()=>{throw failure('RECOVERY_WINDOW_EXPIRED');};
  const result=await f.run();assert.equal(result.recoveryCode,'RECOVERY_WINDOW_EXPIRED');
  assert.equal(f.journal.read('receipt'),null);assert.equal(f.journal.read('transaction').nonce,'unchanged-authority-nonce');
  assert.equal(f.state.signs,0);assert.equal(f.state.rollbackSigns,0);
});

test('reconciliation attempts have a fixed bound and do not refresh their authority',async()=>{
  const state=aborted();state.reconciliationAttempts={'abort-resume':Array.from({length:64},(_,i)=>({sequence:i+1,status:'PENDING'}))};
  const f=fixture({transaction:state});const result=await f.run();
  assert.equal(result.recoveryCode,'RECOVERY_ATTEMPTS_EXHAUSTED');assert.deepEqual(f.calls,[]);
  assert.equal(f.journal.read('receipt'),null);
});

for(const point of ['intent','effect','done'])test('crash '+point+' during abort restoration preserves evidence and reconciles once per continuation',async()=>{
  const f=fixture({transaction:aborted()});f.state.running=false;let once=false;
  await assert.rejects(f.run({fault:p=>{if(p===point+':abort-resume'&&!once){once=true;throw Object.assign(Error('CRASH'),{simulatedCrash:true});}}}));
  assert.equal(f.journal.read('receipt'),null);
  const result=await f.run();assert.equal(result.status,'ABORTED_BEFORE_CONFIGURATION_CHANGE');
  assert.equal(f.state.starts,1);assert.equal(f.state.signs,0);
  assert.equal(f.journal.read('transaction').reconciliationAttempts['abort-resume'].length,2);
});

test('partial rollback activation is not cached as complete and can finish on fresh readback',async()=>{
  const f=fixture();let attempts=0;
  f.adapters.activate=()=>{
    if(f.state.revision===17)return {status:'RESTORE_PARTIAL'};
    if(++attempts===1)return {status:'RESTORE_PARTIAL'};
    f.state.running=true;return {status:'OS_ACTIVE'};
  };
  assert.equal((await f.run()).status,'RECOVERY_REQUIRED_SERVICES_MAY_REMAIN_FENCED');
  assert.equal(f.journal.read('transaction').steps['rollback-activate'].status,'INTENT');
  const forwardCalls=f.calls.filter(x=>x==='cloud17').length;
  const result=await f.run();assert.equal(result.status,'ROLLED_BACK_TO_R15_WITH_NEWER_REVISION');
  assert.equal(result.configurationRevision,18);assert.equal(f.state.rollbackSigns,1);
  assert.equal(f.calls.filter(x=>x==='cloud17').length,forwardCalls);
});

test('completed readback without terminal receipt is checked again after a crash',async()=>{
  const f=fixture();let once=false;
  await assert.rejects(f.run({fault:p=>{if(p==='done:readback'&&!once){once=true;throw Object.assign(Error('CRASH'),{simulatedCrash:true});}}}));
  assert.equal(f.journal.read('receipt'),null);const before=f.calls.filter(x=>x==='verify').length;
  assert.equal((await f.run()).status,'MAINTENANCE_COMMITTED');
  assert.equal(f.calls.filter(x=>x==='verify').length,before+1);assert.equal(f.state.signs,1);
});

test('terminal receipt stays historical and never triggers a new action',async()=>{
  const receipt={schema:'r16.maintenance-completion.v3',status:'ABORTED_BEFORE_CONFIGURATION_CHANGE'};
  const f=fixture({receipt});assert.deepEqual(await f.run(),{...receipt,historicalReadOnly:true});assert.deepEqual(f.calls,[]);
});
