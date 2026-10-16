"""One-shot controlled crash stop for separately native-admitted root execution.

A checkpoint proves preservation of the local durable set, never all-tool drain.
An intent consumes the signal attempt even when the caller never learns whether
it was delivered. Re-entry only reads the original target; it never re-signals.
"""
from copy import deepcopy
import hashlib
import json
import re

SCHEMA = 'r16.source-app-controlled-crash-stop.v2'
UNIT = 'r16-app.service'
HOST = 'VM-0-12-ubuntu'
CGROUP = '/system.slice/r16-app.service'
SOURCE_HASHES = {
 'app/app-runner.mjs':'9fa13d0fe708d62e8ec34db680212d9d1857014c4e08bbaf1b00c60c8f602737',
 'app/workspace-host.mjs':'119756c7bb950308a1edb062b93c4848b5280e9ba356c13d6660f96b192915d2',
 'app/upstream/src/server.mjs':'08524d426f543b10e3806204111d4ed979c300baf220b5afb10f08c1da856912',
 'app/upstream/src/project-forge-crown-executor.mjs':'01f09efacf4169f88215815824acec8f4e9e1c5d2451d3e872dd4dad2bb49033',
 'src/lease-core.mjs':'889232f53d5c014138a7004df32c8e4f4f6c16703b6d53fa75ce0cbcf53e43b9',
}
ORIGINAL_IDS = {'p2vox':('c434da49-055a-43dc-a3e3-695cce137909',30),
                'pmog2':('d0364f8b-3a68-4ca2-a396-7953b29cee4c',38)}
TERMINAL = ('CONTROLLED_CRASH_STOPPED_NOT_DRAINED', 'ABORTED_BEFORE_SIGNAL_ORIGINAL_RUNTIME_RESTORED')

def canonical(value): return json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()
def digest(value): return hashlib.sha256(canonical(value)).hexdigest()
def sha(raw): return hashlib.sha256(raw).hexdigest()
def need(ok,code):
 if not ok: raise Refused(code)
def ishash(value): return isinstance(value,str) and re.fullmatch('[0-9a-f]{64}',value) is not None
class Refused(Exception):
 def __init__(self,code): self.code=code;super().__init__(code)
def code(error):
 value=getattr(error,'code',None)
 return value if isinstance(value,str) and re.fullmatch('[A-Z0-9_]{1,100}',value) else 'BOUNDED_BACKEND_FAILURE'

def validate_approval(a,now):
 need(isinstance(a,dict) and a.get('schema')==SCHEMA,'EXACT_EXCEPTION_REQUIRED')
 need(a.get('environment') in ('ISOLATED_TEST','PRODUCTION'),'NATIVE_ENVIRONMENT_REQUIRED')
 for flag in ('allowNonGracefulOnce','acceptUnprovenInflight','acceptPossibleUpstreamContinuation'):
  need(a.get(flag) is True,'EXPLICIT_CRASH_RISK_ACCEPTANCE_REQUIRED')
 need(a.get('drainStatus')=='UNPROVEN','DRAIN_CLAIM_REFUSED')
 need(isinstance(a.get('approvalId'),str) and re.fullmatch('[A-Za-z0-9_-]{8,80}',a['approvalId']),'APPROVAL_ID_REQUIRED')
 need(type(a.get('approvedAt')) is int and type(a.get('deadline')) is int and a['approvedAt']<=now and 0<a['deadline']-a['approvedAt']<=300000,'APPROVAL_WINDOW_REFUSED')
 target=a.get('target',{})
 need(isinstance(target,dict) and set(target)=={'unit','host','bootId','cgroup','pid','startTicks','sourceHashes','invocationId','nRestarts'},'TARGET_FIELDS_REFUSED')
 need(target.get('unit')==UNIT and target.get('host')==HOST and target.get('cgroup')==CGROUP,'FIXED_SOURCE_APP_REQUIRED')
 need(isinstance(target.get('bootId'),str) and re.fullmatch('[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}',target['bootId']),'BOOT_BINDING_REQUIRED')
 need(type(target.get('pid')) is int and target['pid']>1 and isinstance(target.get('startTicks'),str) and re.fullmatch('[1-9][0-9]*',target['startTicks']),'PROCESS_BINDING_REQUIRED')
 need(isinstance(target.get('invocationId'),str) and re.fullmatch('[0-9a-f]{32}',target['invocationId']),'INVOCATION_BINDING_REQUIRED')
 need(type(target.get('nRestarts')) is int and target['nRestarts']>=0,'RESTART_BINDING_REQUIRED')
 need(target.get('sourceHashes')==SOURCE_HASHES,'ORIGINAL_SOURCE_PIN_REQUIRED')
 expected=a.get('expectedOriginalUnknown',{})
 need(set(expected)==set(ORIGINAL_IDS),'ORIGINAL_UNKNOWN_BINDING_REQUIRED')
 for project,(operation,generation) in ORIGINAL_IDS.items():
  row=expected[project]
  need(set(row)=={'operationId','operationHash','generation','status','resultHash'} and row['operationId']==operation and row['generation']==generation and row['status']=='UNKNOWN' and row['resultHash'] is None and ishash(row['operationHash']),'ORIGINAL_UNKNOWN_BINDING_REQUIRED')
 leases=a.get('expectedLeaseBindings',{})
 need(set(leases)==set(ORIGINAL_IDS),'ORIGINAL_LEASE_BINDING_REQUIRED')
 for row in leases.values():
  need(set(row)=={'activeLeaseHash','closingLeaseHash','pendingLeaseHash'} and ishash(row['activeLeaseHash']) and all(v is None or ishash(v) for v in row.values()),'ORIGINAL_LEASE_BINDING_REQUIRED')
 need(a.get('expectedSemanticBindingsDigest')==digest({'originalUnknown':expected,'leaseBindings':leases}),'SEMANTIC_BINDINGS_DIGEST_DRIFT')
 return deepcopy(target)

def validate_observation(o,target,owner,*,allow_exited=False):
 need(isinstance(o,dict) and all(o.get(k)==target[k] for k in ('unit','host','bootId','cgroup','pid','startTicks','sourceHashes','invocationId','nRestarts')),'TARGET_IDENTITY_DRIFT')
 need(type(o.get('processExited')) is bool and isinstance(o.get('members'),list),'PROCESS_OBSERVATION_REQUIRED')
 members=o['members']
 need(all(type(pid) is int for pid in members) and len(members)==len(set(members)),'CGROUP_MEMBERSHIP_UNPROVEN')
 if o['processExited']:
  need(allow_exited and members==[],'EXIT_OR_CGROUP_NOT_PROVEN')
 else:
  need(members==[target['pid']],'EXTRA_OR_MISSING_CGROUP_MEMBER')
 need(o.get('fenceOwner') in (None,owner),'FOREIGN_FENCE_REFUSED')
 need(type(o.get('frozen')) is bool,'FREEZER_OBSERVATION_REQUIRED')
 if o['frozen']: need(o.get('freezeOwner')==owner,'FOREIGN_FREEZE_REFUSED')
 else: need(o.get('freezeOwner') is None,'FREEZER_OWNERSHIP_DRIFT')
 return o

def checkpoint_manifest(checkpoint,a):
 """Validate local store bytes; signatures/authority stay the existing root's job.

 The fixed future reader must enumerate the complete registered App store tree.
 No public path, caller-supplied filename, or production reader is provided here.
 """
 need(checkpoint.get('schema')=='r16.source-app-durable-checkpoint.v1' and checkpoint.get('completeRegisteredFileSet') is True,'COMPLETE_CHECKPOINT_REQUIRED')
 need(checkpoint.get('otherWriterPids')==[],'OTHER_STORE_WRITER_PRESENT')
 rows=checkpoint.get('files');need(isinstance(rows,dict) and 3<=len(rows)<=100000,'CHECKPOINT_FILES_REQUIRED')
 parsed={};manifest={};total_bytes=0
 required={'host/state.json',*[f'host/project-{p}/state.json' for p in ORIGINAL_IDS]}
 for name,row in rows.items():
  need(isinstance(name,str) and len(name)<=512 and not name.startswith('/') and '\\' not in name and '\0' not in name and all(x not in ('','.','..') for x in name.split('/')),'CHECKPOINT_PATH_REFUSED')
  parts=name.split('/');need(parts[0]=='host' and len(parts) in (2,3) and (len(parts)==2 or parts[1] in ['project-'+p for p in ORIGINAL_IDS]),'CHECKPOINT_SCOPE_REFUSED')
  base=parts[-1]
  need(not base.startswith(('.next','.reclaim')),'TEMPORARY_STORE_FILE_PRESENT')
  need(base in ('state.json','.lock') or re.fullmatch('archive-[A-Za-z0-9_-]+[.]json',base),'UNREVIEWED_STORE_FILE_PRESENT')
  need(row.get('regular') is True and row.get('symlink') is False and row.get('uid')==1000 and row.get('nlink')==1 and row.get('mode')==0o600,'CHECKPOINT_FILE_METADATA_REFUSED')
  raw=row.get('bytes');need(isinstance(raw,bytes) and 0<len(raw)<=16*1024*1024,'CHECKPOINT_FILE_BYTES_REFUSED')
  total_bytes+=len(raw);need(total_bytes<=64*1024*1024,'CHECKPOINT_CAPACITY_REFUSED')
  def unique(pairs):
   out={}
   for key,value in pairs:
    need(key not in out,'CORRUPT_STORE_FILE');out[key]=value
   return out
  def bad_constant(value): raise Refused('CORRUPT_STORE_FILE')
  try: value=json.loads(raw,object_pairs_hook=unique,parse_constant=bad_constant)
  except (ValueError,UnicodeError): raise Refused('CORRUPT_STORE_FILE')
  need(isinstance(value,dict),'CORRUPT_STORE_FILE')
  if base=='.lock':
   need(set(value)=={'schema','pid','start','nonce'} and type(value['schema']) is int and value['schema']==1 and type(value['pid']) is int and value['pid']>1 and isinstance(value['start'],str) and re.fullmatch('[1-9][0-9]*',value['start']) and isinstance(value['nonce'],str) and len(value['nonce'])>=16,'OTHER_OR_AMBIGUOUS_STORE_WRITER')
   if (value['pid'],value['start'])!=(a['target']['pid'],a['target']['startTicks']):
    proof=checkpoint.get('staleLockProofs',{}).get(name)
    need(isinstance(proof,dict) and set(proof)=={'lockSha256','pid','startTicks','observedStartTicks','bootId'} and proof['lockSha256']==sha(raw) and proof['pid']==value['pid'] and proof['startTicks']==value['start'] and proof['bootId']==a['target']['bootId'] and (proof['observedStartTicks'] is None or isinstance(proof['observedStartTicks'],str) and re.fullmatch('[1-9][0-9]*',proof['observedStartTicks'])) and proof['observedStartTicks']!=value['start'],'OTHER_OR_AMBIGUOUS_STORE_WRITER')
  parsed[name]=value;manifest[name]={'sha256':sha(raw),'mode':row['mode'],'uid':row['uid'],'nlink':row['nlink'],'bytes':len(raw)}
 need(required<=set(parsed),'REGISTERED_STORE_MISSING')
 for state_name in required:
  lock_name=state_name.rsplit('/',1)[0]+'/.lock'
  if lock_name in parsed: continue
  proof=checkpoint.get('missingLockProofs',{}).get(lock_name)
  need(isinstance(proof,dict) and set(proof)=={'stateSha256','dirDev','dirIno','targetBootId','capturePhase'} and proof['stateSha256']==manifest[state_name]['sha256'] and type(proof['dirDev']) is int and proof['dirDev']>=0 and type(proof['dirIno']) is int and proof['dirIno']>0 and proof['targetBootId']==a['target']['bootId'] and proof['capturePhase'] in ('BASELINE_NOT_DRAIN_PROOF','FROZEN','EXITED'),'REGISTERED_WRITER_LOCK_MISSING')
 def state(name,kind):
  wrapper=parsed[name]
  need(set(wrapper)=={'schema','revision','maxNow','data'} and type(wrapper['schema']) is int and wrapper['schema']==1 and type(wrapper['revision']) is int and wrapper['revision']>=0 and type(wrapper['maxNow']) is int and wrapper['maxNow']>=0 and isinstance(wrapper['data'],dict) and wrapper['data'].get('kind')==kind,'CORRUPT_STORE_STATE')
  return wrapper['data']
 host=state('host/state.json','r16.app-workspace.v1');unknown={};leases={};other_inflight=0
 projects=host.get('projects');need(isinstance(projects,list) and len(projects)==len(ORIGINAL_IDS) and all(isinstance(x,dict) and isinstance(x.get('project'),dict) for x in projects),'REGISTERED_PROJECT_GRAPH_DRIFT')
 need(sorted(x['project'].get('id','') for x in projects)==sorted(ORIGINAL_IDS),'REGISTERED_PROJECT_GRAPH_DRIFT')
 for name,value in parsed.items():
  if name.endswith('/state.json'):
   data=value.get('data',{})
   for field in ('operations','allocations','controls'):
    items=data.get(field,[]);need(isinstance(items,list),'CORRUPT_STORE_STATE')
    other_inflight+=sum(1 for row in items if row.get('status')=='INFLIGHT')
    for row in items:
     if row.get('status')!='UNKNOWN': continue
     need(field=='operations','ADDITIONAL_DURABLE_UNKNOWN_PRESENT')
     project=next((p for p,(operation,_) in ORIGINAL_IDS.items() if row.get('id')==operation),None)
     need(project is not None,'ADDITIONAL_DURABLE_UNKNOWN_PRESENT')
     expected=a['expectedOriginalUnknown'][project]
     need(row.get('projectId')==project and row.get('resultHash') is None,'ADDITIONAL_DURABLE_UNKNOWN_PRESENT')
     if name=='host/state.json':
      need(isinstance(row.get('operation'),dict) and digest(row['operation'])==expected['operationHash'],'ORIGINAL_UNKNOWN_CHANGED')
     else:
      need(name==f'host/project-{project}/state.json' and row.get('hash')==expected['operationHash'] and row.get('generation')==expected['generation'],'ADDITIONAL_DURABLE_UNKNOWN_PRESENT')
 need(other_inflight==0,'OTHER_DURABLE_INFLIGHT_PRESENT')
 operations=host.get('operations',[])
 need(not any(o.get('status')=='UNKNOWN' and o.get('id') not in [x[0] for x in ORIGINAL_IDS.values()] for o in operations),'ADDITIONAL_DURABLE_UNKNOWN_PRESENT')
 need(not any(x.get('status') in ('UNKNOWN','INFLIGHT') for x in host.get('allocations',[])),'UNRESOLVED_ALLOCATION_PRESENT')
 for project,(operation,generation) in ORIGINAL_IDS.items():
  matches=[o for o in operations if o.get('id')==operation];need(len(matches)==1,'ORIGINAL_UNKNOWN_CHANGED');o=matches[0]
  envelope=o.get('operation');need(isinstance(envelope,dict) and envelope.get('body',{}).get('id')==operation and envelope['body'].get('projectId')==project and envelope['body'].get('generation')==generation and o.get('projectId')==project,'ORIGINAL_UNKNOWN_CHANGED')
  actual={'operationId':operation,'operationHash':digest(envelope),'generation':generation,'status':o.get('status'),'resultHash':o.get('resultHash')}
  need(actual==a['expectedOriginalUnknown'][project],'ORIGINAL_UNKNOWN_CHANGED');unknown[project]=actual
  participant=state(f'host/project-{project}/state.json','r16.participant.v1');need(participant.get('role')=='app','PARTICIPANT_ROLE_DRIFT')
  matches=[o for o in participant.get('operations',[]) if o.get('id')==operation];need(len(matches)==1,'PARTICIPANT_ORIGINAL_UNKNOWN_CHANGED');p=matches[0]
  need(p.get('hash')==actual['operationHash'] and p.get('projectId')==project and p.get('generation')==generation and p.get('status')=='UNKNOWN' and p.get('resultHash') is None,'PARTICIPANT_ORIGINAL_UNKNOWN_CHANGED')
  leases[project]={'activeLeaseHash':digest(participant['active']['lease']) if participant.get('active') else None,'closingLeaseHash':digest(participant['closing']) if participant.get('closing') else None,'pendingLeaseHash':digest(participant['pending']['lease']) if participant.get('pending') else None}
 need(leases==a['expectedLeaseBindings'],'ORIGINAL_LEASE_CHANGED')
 bindings=digest({'originalUnknown':unknown,'leaseBindings':leases});need(bindings==a['expectedSemanticBindingsDigest'],'SEMANTIC_BINDINGS_DIGEST_DRIFT')
 return {'schema':'r16.source-app-checkpoint-manifest.v1','files':manifest,'semanticBindingsDigest':bindings,'validatedOriginalBindings':True,'noTemporaryFiles':True,'otherDurableInflight':0,'drainStatus':'UNPROVEN'}

class Driver:
 """Backend and journal are injected isolated adapters, not authorization roots.

 backend: environment='ISOLATED_TEST'; inspect(target), open_pidfd(target),
 fence(target,owner), freeze(target,owner), checkpoint(target),
 send_pidfd_sigkill(handle,deadline), unfreeze(target,owner), unfence(target,owner).
 journal: read()->dict|None, write(dict) atomically durable before returning.
 now: integer milliseconds. fault(point) may simulate a process crash.
 """
 def __init__(self,backend,journal,now,fault=lambda point:None):
  need(getattr(backend,'environment',None) in ('ISOLATED_TEST','PRODUCTION'),'NATIVE_ENVIRONMENT_REQUIRED')
  self.backend=backend;self.journal=journal;self.now=now;self.fault=fault
 def save(self,value): self.journal.write(deepcopy(value));self.fault('journal:'+value['phase'])
 def inspect(self,a,owner,allow_exited=False): return validate_observation(self.backend.inspect(a['target']),a['target'],owner,allow_exited=allow_exited)
 def receipt(self,status,record,**extra):
  value={'schema':'r16.controlled-crash-stop-receipt.v1','status':status,'approvalHash':record['approvalHash'],'targetHash':record['targetHash'],'environment':self.backend.environment,'drainStatus':'UNPROVEN','gracefulStop':False,'upstreamContinuationPossible':True,'productionExecutionPerformed':self.backend.environment=='PRODUCTION',**extra}
  record['receipt']=value;record['phase']='TERMINAL';self.save(record);return value
 def recover_before_signal(self,a,r,failure):
  try:
   row=self.inspect(a,r['approvalHash']);need(not row['processExited'],'SOURCE_EXIT_UNEXPECTED')
   if row['frozen']:
    self.backend.unfreeze(a['target'],r['approvalHash']);self.fault('effect:unfreeze');row=self.inspect(a,r['approvalHash']);need(not row['frozen'],'THAW_UNCONFIRMED')
   if row['fenceOwner']:
    self.backend.unfence(a['target'],r['approvalHash']);self.fault('effect:unfence');row=self.inspect(a,r['approvalHash'])
   need(not row['frozen'] and row['fenceOwner'] is None,'ORIGINAL_RUNTIME_NOT_RESTORED')
   return self.receipt('ABORTED_BEFORE_SIGNAL_ORIGINAL_RUNTIME_RESTORED',r,failureCode=failure,signalAttemptConsumed=False)
  except Exception as error:
   r['phase']='RECOVERY_REQUIRED_BEFORE_SIGNAL';r['failureCode']=failure;r['recoveryCode']=code(error);self.save(r)
   return self.pending(r)
 def pending(self,r):
  return {'status':r['phase'],'approvalHash':r['approvalHash'],'drainStatus':'UNPROVEN','signalAttemptConsumed':r.get('signalAttemptConsumed',False),'automaticSignalReplayAllowed':False,'productionExecutionPerformed':self.backend.environment=='PRODUCTION'}
 def reconcile(self,a,r):
  try:
   row=self.inspect(a,r['approvalHash'],allow_exited=True)
   need(row['processExited'] and row['members']==[],'EXIT_OR_CGROUP_NOT_PROVEN')
   need(row['fenceOwner']==r['approvalHash'],'OWNED_RESTART_FENCE_LOST')
   current=checkpoint_manifest(self.backend.checkpoint(a['target']),a)
   need(current==r['checkpoint'],'CHECKPOINT_CHANGED_AFTER_SIGNAL')
   return self.receipt('CONTROLLED_CRASH_STOPPED_NOT_DRAINED',r,checkpointDigest=digest(current),signalAttemptConsumed=True,originalLedgerBytesPreserved=True,originalUnknownPreserved=True,originalLeasesPreserved=True,cgroupEmpty=True,originalProcessExited=True,automaticRestartStillFenced=True)
  except Exception as error:
   r['phase']='RECOVERY_REQUIRED_AFTER_SIGNAL';r['recoveryCode']=code(error);self.save(r);return self.pending(r)
 def run(self,a):
  target=validate_approval(a,self.now());owner=digest(a)
  need(a['environment']==self.backend.environment,'NATIVE_ENVIRONMENT_MISMATCH')
  if self.backend.environment=='PRODUCTION':
   need(callable(getattr(self.backend,'assert_admitted',None)),'PROTECTED_NATIVE_ADMISSION_REQUIRED');self.backend.assert_admitted(a)
  r=self.journal.read()
  if r:
   need(r.get('schema')=='r16.controlled-crash-stop-journal.v1' and r.get('approvalHash')==owner and r.get('targetHash')==digest(target),'JOURNAL_BINDING_DRIFT')
   need(type(r.get('signalAttemptConsumed')) is bool,'JOURNAL_PHASE_DRIFT')
   need(r.get('phase') in ('BOUND','FENCE_INTENT','FREEZE_INTENT','CHECKPOINT_SAVED','RECOVERY_REQUIRED_BEFORE_SIGNAL','SIGNAL_INTENT','SIGNAL_RETURNED','RECOVERY_REQUIRED_AFTER_SIGNAL','TERMINAL'),'JOURNAL_PHASE_DRIFT')
   if r['phase'] in ('SIGNAL_INTENT','SIGNAL_RETURNED','RECOVERY_REQUIRED_AFTER_SIGNAL'): need(r['signalAttemptConsumed'],'JOURNAL_PHASE_DRIFT')
   if r['phase'] in ('BOUND','FENCE_INTENT','FREEZE_INTENT','CHECKPOINT_SAVED','RECOVERY_REQUIRED_BEFORE_SIGNAL'): need(not r['signalAttemptConsumed'],'JOURNAL_PHASE_DRIFT')
   if r.get('phase')=='TERMINAL':
    receipt=r.get('receipt',{});need(receipt.get('status') in TERMINAL and receipt.get('approvalHash')==owner and receipt.get('targetHash')==digest(target),'JOURNAL_RECEIPT_DRIFT')
    return {**deepcopy(receipt),'historicalReadOnly':True}
   if r.get('signalAttemptConsumed'):
    need(isinstance(r.get('checkpoint'),dict) and r.get('checkpointDigest')==digest(r['checkpoint']),'JOURNAL_CHECKPOINT_DRIFT')
    return self.reconcile(a,r)
   return self.recover_before_signal(a,r,'INTERRUPTED_BEFORE_SIGNAL')
  need(self.now()<a['deadline'],'SIGNAL_DEADLINE_EXPIRED')
  row=self.inspect(a,owner);need(not row['frozen'] and row['fenceOwner'] is None,'PREEXISTING_FENCE_OR_FREEZE')
  r={'schema':'r16.controlled-crash-stop-journal.v1','approvalHash':owner,'targetHash':digest(target),'phase':'BOUND','signalAttemptConsumed':False};self.save(r)
  try:
   handle=self.backend.open_pidfd(target);self.fault('effect:open-pidfd')
   self.inspect(a,owner)
   r['phase']='FENCE_INTENT';self.save(r);self.backend.fence(target,owner);self.fault('effect:fence')
   row=self.inspect(a,owner);need(row['fenceOwner']==owner,'FENCE_NOT_EFFECTIVE')
   r['phase']='FREEZE_INTENT';self.save(r);self.backend.freeze(target,owner);self.fault('effect:freeze')
   row=self.inspect(a,owner);need(row['frozen'] and row['freezeOwner']==owner and row['fenceOwner']==owner,'FREEZE_NOT_EFFECTIVE')
   checkpoint=checkpoint_manifest(self.backend.checkpoint(target),a);self.fault('effect:checkpoint')
   r.update(phase='CHECKPOINT_SAVED',checkpoint=checkpoint,checkpointDigest=digest(checkpoint));self.save(r)
   row=self.inspect(a,owner);need(row['frozen'] and row['fenceOwner']==owner,'FREEZE_OR_FENCE_DRIFT')
   need(self.now()<a['deadline'],'SIGNAL_DEADLINE_EXPIRED')
   # This durable intent is the irreversible boundary. Even a crash immediately
   # before the syscall consumes the attempt; a source readback cannot authorize
   # another signal or prove that an earlier caller will never resume its call.
   r.update(phase='SIGNAL_INTENT',signalAttemptConsumed=True);self.save(r)
   row=self.inspect(a,owner);need(row['frozen'] and row['freezeOwner']==owner and row['fenceOwner']==owner,'FREEZE_OR_FENCE_DRIFT')
   need(self.now()<a['deadline'],'SIGNAL_DEADLINE_EXPIRED')
   self.backend.send_pidfd_sigkill(handle,a['deadline']);self.fault('effect:signal')
   r['phase']='SIGNAL_RETURNED';self.save(r)
   return self.reconcile(a,r)
  except Exception as error:
   if r['signalAttemptConsumed']:
    r.update(phase='RECOVERY_REQUIRED_AFTER_SIGNAL',failureCode=code(error));self.save(r);return self.reconcile(a,r)
   return self.recover_before_signal(a,r,code(error))

if __name__=='__main__':
 print(json.dumps({'status':'NATIVE_ENTRY_REQUIRED','drainStatus':'UNPROVEN','productionExecutionPerformed':False}));raise SystemExit(78)
