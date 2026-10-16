// Journalled maintenance state machine. Authority and real effects belong to
// the fixed admitted adapters. This module cannot sign, stop or install itself.
import {createHash} from 'node:crypto';
const canonical=x=>x===null||typeof x!=='object'?JSON.stringify(x):Array.isArray(x)?'['+x.map(canonical).join(',')+']':'{'+Object.keys(x).sort().map(k=>JSON.stringify(k)+':'+canonical(x[k])).join(',')+'}';
const digest=x=>createHash('sha256').update(canonical(x)).digest('hex');
const need=(ok,code)=>{if(!ok)throw Object.assign(Error(code),{code});};
// Only an exact returned refusal which precedes the first remote configuration
// write can establish that the call finished without committing. A timeout or
// unknown remote effect may still complete later; a momentary source readback
// must never turn that uncertainty into an abort receipt.
const PRECOMMIT_REFUSALS=new Set(['SOURCE_APP_SELECTOR_INVALID','CLOUD_APP_SELECTOR_CAS_CONFLICT',
  'CLOUD_START_TOKEN_CAS_CONFLICT','FORWARD_COMMIT_EXPIRED','FORWARD_DELIVERY_TARGET_CHANGED',
  'CLOUD_ADMISSION_EXPIRED','DELIVERY_STRUCTURE_INVALID','DELIVERY_AUTHORITY_CHANGED',
  'DELIVERY_PUBLIC_SCOPE_EXPANDED','DELIVERY_CONTROL_CHANGED','DELIVERY_REVISION_ROLLBACK',
  'SAME_REVISION_CONFLICT','PREVIOUS_AUTHORITY_CHANGED']);

export async function drive({journal,adapters,now=Date.now,fault=()=>{}}){
  const old=journal.read('receipt');if(old)return {...old,historicalReadOnly:true};
  let state=journal.read('transaction')||{schema:'r16.maintenance-transaction.v3',steps:{},failures:[]};
  const save=()=>journal.write('transaction',state);
  const step=async(name,fn)=>{
    const record=state.steps[name];
    if(record?.status==='DONE'){const result=journal.read(name);need(result&&digest(result)===record.resultHash,'TRANSACTION_RESULT_CORRUPT');return result;}
    // Each actual adapter has exact-byte reconciliation or durable OS/signing
    // effect handling. An unresolved signing intent is never replayed here.
    state.steps[name]={status:'INTENT'};save();fault('intent:'+name);
    const result=await fn();fault('effect:'+name);journal.write(name,result);
    state.steps[name]={status:'DONE',resultHash:digest(result)};save();fault('done:'+name);return result;
  };
  // Restoration and final readback reconcile live state on every continuation.
  // Keep each attempt separately, including legacy DONE(partial) records.
  const reconcile=async(name,fn,accept,code)=>{
    const previous=state.steps[name];
    if(previous?.status==='DONE'){
      const recorded=journal.read(previous.recordName||name);
      need(recorded&&digest(recorded)===previous.resultHash,'TRANSACTION_RESULT_CORRUPT');
    }
    const groups=state.reconciliationAttempts ||= {};
    const attempts=groups[name] ||= [];
    need(attempts.length<64,'RECOVERY_ATTEMPTS_EXHAUSTED');
    const attempt={sequence:attempts.length+1,status:'INTENT',at:now()};
    if(!state.steps[name])state.steps[name]={status:'INTENT'};
    attempts.push(attempt);save();fault('intent:'+name);
    const result=await fn();fault('effect:'+name);
    need(result&&typeof result==='object'&&!Array.isArray(result),'RECOVERY_RESPONSE_INVALID');
    const recordName=name+'-attempt-'+attempt.sequence;
    journal.write(recordName,result);
    const complete=accept(result);
    attempt.recordName=recordName;attempt.resultHash=digest(result);
    attempt.status=complete?'DONE':'PENDING';
    if(complete&&state.steps[name].status!=='DONE')state.steps[name]={status:'DONE',recordName,resultHash:attempt.resultHash};
    save();fault('done:'+name);need(complete,code);return result;
  };
  const restore=(name,fn)=>reconcile(name,fn,r=>r.status==='OS_ACTIVE','OS_RESTORATION_INCOMPLETE');
  let publication=journal.read('signed');
  const finish=async()=>{
    await restore('activate',adapters.activate);
    const verified=await reconcile('readback',()=>adapters.verify(publication.delivery),()=>true,'READBACK_UNCONFIRMED');
    const receipt={schema:'r16.maintenance-completion.v3',status:'MAINTENANCE_COMMITTED',configurationRevision:publication.delivery.body.revision,readback:verified,completedAt:now(),businessAcceptance:false,originalUnknownDisposition:'PRESERVED_NOT_SETTLED'};
    journal.write('receipt',receipt);return receipt;
  };
  const finishRollback=async rollback=>{
    await restore('rollback-activate',adapters.activate);
    const verified=await reconcile('rollback-readback',()=>adapters.verify(rollback.delivery),()=>true,'READBACK_UNCONFIRMED');
    const receipt={schema:'r16.maintenance-completion.v3',status:'ROLLED_BACK_TO_R15_WITH_NEWER_REVISION',configurationRevision:rollback.delivery.body.revision,readback:verified,failureCode:state.failures.at(-1).code,completedAt:now(),businessAcceptance:false,originalUnknownDisposition:'PRESERVED_NOT_SETTLED'};
    journal.write('receipt',receipt);return receipt;
  };
  try{
    if(state.mode==='ROLLBACK'||state.mode==='ABORT')throw Object.assign(Error('RESUME_PERSISTED_RECOVERY'),{code:state.failures.at(-1)?.code||'RESUME_PERSISTED_RECOVERY'});
    state.mode='FORWARD';save();
    // Once activation started, do not demand an obsolete stopped observation or
    // repeat a configuration write. Reconcile the OS activation then read back.
    if(state.steps.activate){need(publication,'ACTIVATION_WITHOUT_DURABLE_PUBLICATION');return await finish();}
    await step('baseline',adapters.baseline);
    await step('quiesce',adapters.quiesce);await adapters.observe();
    await step('payload',adapters.stage);await adapters.observe();
    publication=await step('signed',adapters.sign);await adapters.observe();
    await step('cloud-commit',()=>adapters.cloudCommit(publication.delivery));
    await adapters.observe();await step('local-commit',()=>adapters.localCommit(publication));
    return await finish();
  }catch(e){
    if(e?.simulatedCrash)throw e; // Test crash bypasses in-process recovery.
    state.failures.push({at:now(),code:e.code||'MAINTENANCE_EFFECT_UNCONFIRMED'});state.failures=state.failures.slice(-8);save();
    let committed=!!state.steps['cloud-commit']||!!state.steps['local-commit'];
    state.mode=committed?'ROLLBACK':'ABORT';save();
    try{
      const canProveUncommitted=state.steps['cloud-commit']?.status==='INTENT'&&
        !state.steps['local-commit']&&!state.steps['rollback-signed']&&
        PRECOMMIT_REFUSALS.has(e.code)&&typeof adapters.confirmUncommitted==='function';
      if(canProveUncommitted){
        await reconcile('uncommitted-readback',adapters.confirmUncommitted,
          r=>r.status==='SOURCE_CONFIGURATION_UNCHANGED'&&/^[a-f0-9]{64}$/.test(r.sourceDeliveryHash),
          'SOURCE_CONFIGURATION_NOT_PROVEN_UNCHANGED');
        committed=false;state.mode='ABORT';save();
      }
      if(committed){
        need(publication||journal.read('signed'),'SIGNED_PUBLICATION_REQUIRED_FOR_ROLLBACK');publication=publication||journal.read('signed');
        if(state.steps['rollback-activate']){const rollback=journal.read('rollback-signed');need(rollback,'ROLLBACK_ACTIVATION_WITHOUT_DURABLE_PUBLICATION');return await finishRollback(rollback);}
        await step('rollback-quiesce',adapters.requiesce);await adapters.observe();
        const accepted=await adapters.accepted();
        const rollback=await step('rollback-signed',()=>adapters.signRollback(accepted));
        await adapters.observe();await step('rollback-cloud',()=>adapters.cloudCommit(rollback.delivery));
        await adapters.observe();await step('rollback-local',()=>adapters.localCommit({...publication,delivery:rollback.delivery},true));
        return await finishRollback(rollback);
      }
      if(!state.steps.quiesce){const receipt={schema:'r16.maintenance-completion.v3',status:'ABORTED_BEFORE_SERVICE_CHANGES',failureCode:state.failures.at(-1).code,completedAt:now(),businessAcceptance:false};journal.write('receipt',receipt);return receipt;}
      const recovery=await restore('abort-resume',adapters.resume);
      delete state.recovery;save();
      const receipt={schema:'r16.maintenance-completion.v3',status:'ABORTED_BEFORE_CONFIGURATION_CHANGE',recovery,failureCode:state.failures.at(-1).code,completedAt:now(),businessAcceptance:false};
      journal.write('receipt',receipt);return receipt;
    }catch(recoveryError){
      if(recoveryError?.simulatedCrash)throw recoveryError;
      state.recovery={status:'RECOVERY_REQUIRED_SERVICES_MAY_REMAIN_FENCED',code:recoveryError.code||'RECOVERY_EFFECT_UNCONFIRMED',at:now()};save();
      return {schema:'r16.maintenance-completion.v3',status:state.recovery.status,failureCode:state.failures.at(-1).code,recoveryCode:state.recovery.code,businessAcceptance:false,automaticForceTermination:false};
    }
  }
}
