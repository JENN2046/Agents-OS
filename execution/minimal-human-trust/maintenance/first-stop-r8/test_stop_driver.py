import copy
import importlib.util
import json
from pathlib import Path
import unittest

HERE=Path(__file__).parent
spec=importlib.util.spec_from_file_location('controlled_crash_r7_tested',HERE/'stop_driver.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class PowerLoss(BaseException): pass
class MemoryJournal:
 def __init__(self): self.value=None;self.writes=[]
 def read(self): return copy.deepcopy(self.value)
 def write(self,value): self.value=copy.deepcopy(value);self.writes.append(copy.deepcopy(value))

def fixture():
 now=[1000000]
 target={'unit':m.UNIT,'host':m.HOST,'bootId':'00000000-1111-2222-3333-444444444444','pid':4343,'startTicks':'456789','cgroup':m.CGROUP,'sourceHashes':copy.deepcopy(m.SOURCE_HASHES),'invocationId':'1'*32,'nRestarts':0}
 files={};unknown={};leases={}
 def put(name,data): files[name]={'regular':True,'symlink':False,'uid':1000,'nlink':1,'mode':0o600,'bytes':m.canonical(data)}
 def state(data): return {'schema':1,'revision':12,'maxNow':999000,'data':data}
 host={'kind':'r16.app-workspace.v1','projects':[],'operations':[],'allocations':[],'status':'recovery_pending'}
 for project,(operation,generation) in m.ORIGINAL_IDS.items():
  envelope={'body':{'schema':'r16.operation.v1','id':operation,'projectId':project,'generation':generation,'synthetic':True},'signature':'SYNTHETIC_ONLY_NOT_PRODUCTION'}
  host['projects'].append({'project':{'id':project}})
  h=m.digest(envelope);unknown[project]={'operationId':operation,'operationHash':h,'generation':generation,'status':'UNKNOWN','resultHash':None}
  host['operations'].append({'id':operation,'projectId':project,'operation':envelope,'status':'UNKNOWN'})
  lease={'body':{'schema':'r16.lease.v1','id':'synthetic-'+project,'generation':generation},'signature':'SYNTHETIC_ONLY_NOT_PRODUCTION'}
  leases[project]={'activeLeaseHash':m.digest(lease),'closingLeaseHash':m.digest(lease),'pendingLeaseHash':None}
  participant={'kind':'r16.participant.v1','role':'app','active':{'lease':lease},'closing':lease,'pending':None,'operations':[{'id':operation,'hash':h,'projectId':project,'generation':generation,'status':'UNKNOWN','resultHash':None}]}
  put('host/project-'+project+'/state.json',state(participant))
 put('host/state.json',state(host))
 for parent in ['host',*['host/project-'+p for p in m.ORIGINAL_IDS]]:
  put(parent+'/.lock',{'schema':1,'pid':target['pid'],'start':target['startTicks'],'nonce':'synthetic-lock-nonce-'+parent})
  put(parent+'/archive-example.json',{'syntheticHistory':'MUST_REMAIN_EXACT'})
 approval={'schema':m.SCHEMA,'environment':'ISOLATED_TEST','approvalId':'synthetic-r7-once','allowNonGracefulOnce':True,'acceptUnprovenInflight':True,'acceptPossibleUpstreamContinuation':True,'drainStatus':'UNPROVEN','approvedAt':now[0],'deadline':now[0]+300000,'target':target,'expectedOriginalUnknown':unknown,'expectedLeaseBindings':leases,'expectedSemanticBindingsDigest':m.digest({'originalUnknown':unknown,'leaseBindings':leases})}
 journal=MemoryJournal()
 class Backend:
  environment='ISOLATED_TEST'
  def __init__(self):
   self.row={**copy.deepcopy(target),'processExited':False,'members':[target['pid']],'fenceOwner':None,'frozen':False,'freezeOwner':None}
   self.files=copy.deepcopy(files);self.effects=[];self.kill_calls=0;self.signal_mode='exit';self.checkpoint_calls=0;self.other_writers=[];self.complete=True;self.before_signal=None
  def inspect(self,target): return copy.deepcopy(self.row)
  def open_pidfd(self,target): self.effects.append('open-pidfd');return ('synthetic-pidfd',target['bootId'],target['pid'],target['startTicks'])
  def fence(self,target,owner): self.effects.append('fence');self.row['fenceOwner']=owner
  def freeze(self,target,owner): self.effects.append('freeze');self.row.update(frozen=True,freezeOwner=owner)
  def checkpoint(self,target):
   self.checkpoint_calls+=1
   return {'schema':'r16.source-app-durable-checkpoint.v1','completeRegisteredFileSet':self.complete,'otherWriterPids':list(self.other_writers),'files':copy.deepcopy(self.files)}
  def send_pidfd_sigkill(self,handle,deadline):
   if self.before_signal: self.before_signal()
   m.need(now[0]<deadline,'SIGNAL_DEADLINE_EXPIRED')
   self.kill_calls+=1;self.effects.append('SIGKILL');assert journal.value['signalAttemptConsumed'] is True;assert journal.value['phase']=='SIGNAL_INTENT'
   assert handle==('synthetic-pidfd',target['bootId'],target['pid'],target['startTicks'])
   if self.signal_mode=='unknown-live': raise RuntimeError('untrusted raw provider text')
   self.row.update(processExited=True,members=[],frozen=False,freezeOwner=None)
   if self.signal_mode=='unknown-dead': raise RuntimeError('lost return')
  def unfreeze(self,target,owner): assert self.row['freezeOwner']==owner;self.effects.append('unfreeze');self.row.update(frozen=False,freezeOwner=None)
  def unfence(self,target,owner): assert self.row['fenceOwner']==owner;self.effects.append('unfence');self.row['fenceOwner']=None
 backend=Backend()
 return approval,backend,journal,now

class Tests(unittest.TestCase):
 def invoke(self,a,b,j,now,fault=lambda point:None): return m.Driver(b,j,lambda:now[0],fault).run(a)
 def mutate(self,b,name,fn):
  x=json.loads(b.files[name]['bytes']);fn(x);b.files[name]['bytes']=m.canonical(x)
 def test_success_exact_local_checkpoint_and_historical_no_effects_after_expiry(self):
  a,b,j,t=fixture();before=copy.deepcopy(b.files);result=self.invoke(a,b,j,t)
  self.assertEqual(result['status'],'CONTROLLED_CRASH_STOPPED_NOT_DRAINED');self.assertEqual(result['drainStatus'],'UNPROVEN');self.assertFalse(result['gracefulStop']);self.assertTrue(result['upstreamContinuationPossible']);self.assertEqual(b.files,before);self.assertEqual(b.kill_calls,1)
  self.assertEqual(b.effects,['open-pidfd','fence','freeze','SIGKILL']);self.assertEqual(j.value['checkpoint']['otherDurableInflight'],0)
  count=len(b.effects);t[0]=a['deadline']+1000000;self.assertTrue(self.invoke(a,b,j,t)['historicalReadOnly']);self.assertEqual(len(b.effects),count)
 def test_all_risk_flags_and_drain_truth_are_required(self):
  for flag in ('allowNonGracefulOnce','acceptUnprovenInflight','acceptPossibleUpstreamContinuation','drainStatus'):
   with self.subTest(flag=flag):
    a,b,j,t=fixture();a[flag]=False if flag!='drainStatus' else 'DRAINED'
    with self.assertRaises(m.Refused): self.invoke(a,b,j,t)
    self.assertEqual(b.effects,[])
 def test_source_boot_pid_start_cgroup_and_unit_drift_reject_before_effect(self):
  for field,value in [('bootId','11111111-1111-2222-3333-444444444444'),('pid',999),('startTicks','999'),('unit','other.service'),('cgroup','/other'),('sourceHashes',{})]:
   with self.subTest(field=field):
    a,b,j,t=fixture();b.row[field]=value
    with self.assertRaisesRegex(m.Refused,'TARGET_IDENTITY_DRIFT'): self.invoke(a,b,j,t)
    self.assertEqual(b.effects,[])
 def test_only_original_single_main_process_is_allowed(self):
  for members in ([],[4343,777],[777],[4343,4343],[True]):
   with self.subTest(members=members):
    a,b,j,t=fixture();b.row['members']=members
    with self.assertRaises(m.Refused): self.invoke(a,b,j,t)
    self.assertEqual(b.effects,[])
 def test_extra_member_after_open_prevents_signal(self):
  a,b,j,t=fixture()
  def fault(point):
   if point=='effect:open-pidfd': b.row['members'].append(777)
  result=self.invoke(a,b,j,t,fault);self.assertEqual(result['status'],'RECOVERY_REQUIRED_BEFORE_SIGNAL');self.assertEqual(b.kill_calls,0)
 def test_own_fence_and_frozen_readback_are_required(self):
  for method in ('fence','freeze'):
   with self.subTest(method=method):
    a,b,j,t=fixture();setattr(b,method,lambda *args:None)
    result=self.invoke(a,b,j,t);self.assertEqual(result['status'],'ABORTED_BEFORE_SIGNAL_ORIGINAL_RUNTIME_RESTORED');self.assertEqual(b.kill_calls,0)
 def test_temporary_reclaim_and_incomplete_archives_refuse_without_deleting(self):
  for name,raw in [('host/.next-interrupted',b'{}'),('host/.reclaim',b'{}'),('host/archive-incomplete.json',b'{')]:
   with self.subTest(name=name):
    a,b,j,t=fixture();b.files[name]={**copy.deepcopy(b.files['host/state.json']),'bytes':raw};before=copy.deepcopy(b.files)
    result=self.invoke(a,b,j,t);self.assertEqual(result['status'],'ABORTED_BEFORE_SIGNAL_ORIGINAL_RUNTIME_RESTORED');self.assertEqual(b.kill_calls,0);self.assertEqual(b.files,before);self.assertEqual(b.effects[-2:],['unfreeze','unfence'])
 def test_duplicate_json_keys_and_invalid_wrappers_refuse(self):
  for raw in (b'{"schema":1,"schema":1}',b'[]',b'{"schema":1,"data":{}}'):
   a,b,j,t=fixture();b.files['host/state.json']['bytes']=raw
   self.assertEqual(self.invoke(a,b,j,t)['status'],'ABORTED_BEFORE_SIGNAL_ORIGINAL_RUNTIME_RESTORED');self.assertEqual(b.kill_calls,0)
 def test_original_unknown_and_lease_bytes_semantics_cannot_drift(self):
  cases=[('host/state.json',lambda v:v['data']['operations'][0].update(status='KNOWN')),
         ('host/state.json',lambda v:v['data']['operations'][0]['operation']['body'].update(generation=31)),
         ('host/project-p2vox/state.json',lambda v:v['data']['active']['lease']['body'].update(generation=31)),
         ('host/project-pmog2/state.json',lambda v:v['data']['operations'][0].update(resultHash='f'*64))]
  for name,change in cases:
   with self.subTest(name=name):
    a,b,j,t=fixture();self.mutate(b,name,change)
    self.assertEqual(self.invoke(a,b,j,t)['status'],'ABORTED_BEFORE_SIGNAL_ORIGINAL_RUNTIME_RESTORED');self.assertEqual(b.kill_calls,0)
 def test_non_original_durable_inflight_and_unresolved_allocation_refuse(self):
  for field,status in [('operations','INFLIGHT'),('allocations','INFLIGHT'),('allocations','UNKNOWN'),('operations','UNKNOWN')]:
   a,b,j,t=fixture();self.mutate(b,'host/state.json',lambda v:v['data'][field].append({'id':'not-original','status':status}))
   self.assertEqual(self.invoke(a,b,j,t)['status'],'ABORTED_BEFORE_SIGNAL_ORIGINAL_RUNTIME_RESTORED');self.assertEqual(b.kill_calls,0)
 def test_additional_unknown_in_any_participant_collection_or_wrong_project_refuses(self):
  for field in ('operations','controls','allocations'):
   with self.subTest(field=field):
    a,b,j,t=fixture();self.mutate(b,'host/project-p2vox/state.json',lambda v:v['data'].setdefault(field,[]).append({'id':'unexpected-unknown','status':'UNKNOWN'}))
    self.assertEqual(self.invoke(a,b,j,t)['status'],'ABORTED_BEFORE_SIGNAL_ORIGINAL_RUNTIME_RESTORED');self.assertEqual(b.kill_calls,0)
  a,b,j,t=fixture();foreign=json.loads(b.files['host/project-pmog2/state.json']['bytes'])['data']['operations'][0]
  self.mutate(b,'host/project-p2vox/state.json',lambda v:v['data']['operations'].append(foreign))
  self.assertEqual(self.invoke(a,b,j,t)['status'],'ABORTED_BEFORE_SIGNAL_ORIGINAL_RUNTIME_RESTORED');self.assertEqual(b.kill_calls,0)
 def test_omitted_registered_project_graph_or_extra_project_refuses(self):
  for projects in ([],[{'project':{'id':'p2vox'}}],[{'project':{'id':'p2vox'}},{'project':{'id':'unreviewed'}}]):
   a,b,j,t=fixture();self.mutate(b,'host/state.json',lambda v:v['data'].update(projects=projects))
   self.assertEqual(self.invoke(a,b,j,t)['status'],'ABORTED_BEFORE_SIGNAL_ORIGINAL_RUNTIME_RESTORED');self.assertEqual(b.kill_calls,0)
 def test_missing_registration_other_writer_and_unsafe_file_metadata_refuse(self):
  for kind in ('registration','writer','lock','mode','uid','nlink','symlink','missing'):
   with self.subTest(kind=kind):
    a,b,j,t=fixture()
    if kind=='registration': b.complete=False
    elif kind=='writer': b.other_writers=[123]
    elif kind=='lock': self.mutate(b,'host/.lock',lambda v:v.update(pid=777))
    elif kind=='missing': del b.files['host/project-p2vox/.lock']
    else: b.files['host/state.json'][kind]={'mode':0o644,'uid':0,'nlink':2,'symlink':True}[kind]
    self.assertEqual(self.invoke(a,b,j,t)['status'],'ABORTED_BEFORE_SIGNAL_ORIGINAL_RUNTIME_RESTORED');self.assertEqual(b.kill_calls,0)
 def test_deadline_before_effect_and_after_checkpoint_never_signals(self):
  a,b,j,t=fixture();t[0]=a['deadline']
  with self.assertRaisesRegex(m.Refused,'SIGNAL_DEADLINE_EXPIRED'): self.invoke(a,b,j,t)
  self.assertEqual(b.effects,[])
  a,b,j,t=fixture()
  def fault(point):
   if point=='journal:CHECKPOINT_SAVED': t[0]=a['deadline']
  self.assertEqual(self.invoke(a,b,j,t,fault)['status'],'ABORTED_BEFORE_SIGNAL_ORIGINAL_RUNTIME_RESTORED');self.assertEqual(b.kill_calls,0)
 def test_deadline_after_signal_intent_never_replays_or_auto_thaws(self):
  a,b,j,t=fixture()
  def fault(point):
   if point=='journal:SIGNAL_INTENT': t[0]=a['deadline']
  result=self.invoke(a,b,j,t,fault);self.assertEqual(result['status'],'RECOVERY_REQUIRED_AFTER_SIGNAL');self.assertEqual(b.kill_calls,0);self.assertTrue(b.row['frozen'])
  self.invoke(a,b,j,t);self.assertEqual(b.kill_calls,0);self.assertNotIn('unfreeze',b.effects)
 def test_backend_last_deadline_check_does_not_signal(self):
  a,b,j,t=fixture();b.before_signal=lambda:t.__setitem__(0,a['deadline'])
  self.assertEqual(self.invoke(a,b,j,t)['status'],'RECOVERY_REQUIRED_AFTER_SIGNAL');self.assertEqual(b.kill_calls,0)
 def test_signal_unknown_live_is_readback_only_even_after_deadline(self):
  a,b,j,t=fixture();b.signal_mode='unknown-live'
  self.assertEqual(self.invoke(a,b,j,t)['status'],'RECOVERY_REQUIRED_AFTER_SIGNAL');t[0]=a['deadline']+1
  self.assertEqual(self.invoke(a,b,j,t)['status'],'RECOVERY_REQUIRED_AFTER_SIGNAL');self.assertEqual(b.kill_calls,1);self.assertNotIn('unfreeze',b.effects)
  b.row.update(processExited=True,members=[],frozen=False,freezeOwner=None)
  self.assertEqual(self.invoke(a,b,j,t)['status'],'CONTROLLED_CRASH_STOPPED_NOT_DRAINED');self.assertEqual(b.kill_calls,1)
 def test_lost_signal_return_can_only_finish_from_fresh_exit_proof(self):
  a,b,j,t=fixture();b.signal_mode='unknown-dead';self.assertEqual(self.invoke(a,b,j,t)['status'],'CONTROLLED_CRASH_STOPPED_NOT_DRAINED');self.assertEqual(b.kill_calls,1)
 def test_after_signal_ledger_mode_or_byte_drift_never_claims_preserved(self):
  for change in ('bytes','mode','extra'):
   a,b,j,t=fixture();b.signal_mode='unknown-live';self.invoke(a,b,j,t);b.row.update(processExited=True,members=[],frozen=False,freezeOwner=None)
   if change=='bytes': self.mutate(b,'host/state.json',lambda v:v.update(revision=v['revision']+1))
   elif change=='mode': b.files['host/state.json']['mode']=0o644
   else: b.files['host/archive-new.json']={**copy.deepcopy(b.files['host/state.json']),'bytes':b'{"new":"archive"}'}
   self.assertEqual(self.invoke(a,b,j,t)['status'],'RECOVERY_REQUIRED_AFTER_SIGNAL');self.assertEqual(b.kill_calls,1)
 def test_pid_reuse_or_nonempty_cgroup_after_signal_never_thaws_or_repeats(self):
  for change in ({'startTicks':'999'},{'members':[777]},{'fenceOwner':None}):
   a,b,j,t=fixture();b.signal_mode='unknown-live';self.invoke(a,b,j,t);b.row.update(processExited=True,members=[],frozen=False,freezeOwner=None);b.row.update(change)
   self.assertEqual(self.invoke(a,b,j,t)['status'],'RECOVERY_REQUIRED_AFTER_SIGNAL');self.assertEqual(b.kill_calls,1);self.assertNotIn('unfreeze',b.effects)
 def test_pre_signal_crash_reentry_restores_owned_runtime_without_continuing_signal(self):
  for point in ('journal:BOUND','journal:FENCE_INTENT','effect:fence','journal:FREEZE_INTENT','effect:freeze','effect:checkpoint','journal:CHECKPOINT_SAVED'):
   with self.subTest(point=point):
    a,b,j,t=fixture()
    def fault(p):
     if p==point: raise PowerLoss()
    with self.assertRaises(PowerLoss): self.invoke(a,b,j,t,fault)
    result=self.invoke(a,b,j,t);self.assertEqual(result['status'],'ABORTED_BEFORE_SIGNAL_ORIGINAL_RUNTIME_RESTORED');self.assertEqual(b.kill_calls,0);self.assertFalse(b.row['frozen']);self.assertIsNone(b.row['fenceOwner'])
 def test_signal_intent_crash_consumes_attempt_even_if_no_syscall_happened(self):
  a,b,j,t=fixture()
  def fault(point):
   if point=='journal:SIGNAL_INTENT': raise PowerLoss()
  with self.assertRaises(PowerLoss): self.invoke(a,b,j,t,fault)
  self.assertEqual(self.invoke(a,b,j,t)['status'],'RECOVERY_REQUIRED_AFTER_SIGNAL');self.assertEqual(b.kill_calls,0)
 def test_effect_signal_and_return_journal_crashes_reconcile_no_second_signal(self):
  for point in ('effect:signal','journal:SIGNAL_RETURNED'):
   a,b,j,t=fixture()
   def fault(p):
    if p==point: raise PowerLoss()
   with self.assertRaises(PowerLoss): self.invoke(a,b,j,t,fault)
   self.assertEqual(self.invoke(a,b,j,t)['status'],'CONTROLLED_CRASH_STOPPED_NOT_DRAINED');self.assertEqual(b.kill_calls,1)
 def test_changed_approval_journal_checkpoint_cannot_reuse_attempt(self):
  a,b,j,t=fixture();b.signal_mode='unknown-live';self.invoke(a,b,j,t)
  changed=copy.deepcopy(a);changed['approvalId']='another-approval'
  with self.assertRaisesRegex(m.Refused,'JOURNAL_BINDING_DRIFT'): self.invoke(changed,b,j,t)
  j.value['checkpoint']['files']['host/state.json']['sha256']='f'*64
  with self.assertRaisesRegex(m.Refused,'JOURNAL_CHECKPOINT_DRIFT'): self.invoke(a,b,j,t)
  self.assertEqual(b.kill_calls,1)
 def test_corrupt_journal_phase_cannot_turn_signal_intent_into_auto_restore(self):
  a,b,j,t=fixture();b.signal_mode='unknown-live';self.invoke(a,b,j,t);j.value['signalAttemptConsumed']=False
  with self.assertRaisesRegex(m.Refused,'JOURNAL_PHASE_DRIFT'): self.invoke(a,b,j,t)
  self.assertEqual(b.kill_calls,1);self.assertNotIn('unfreeze',b.effects)
 def test_last_pre_signal_identity_or_member_drift_consumes_attempt_without_signal(self):
  for change in ({'members':[4343,777]},{'startTicks':'999'},{'frozen':False,'freezeOwner':None},{'fenceOwner':None}):
   a,b,j,t=fixture()
   def fault(point):
    if point=='journal:SIGNAL_INTENT': b.row.update(change)
   self.assertEqual(self.invoke(a,b,j,t,fault)['status'],'RECOVERY_REQUIRED_AFTER_SIGNAL');self.assertEqual(b.kill_calls,0);self.assertNotIn('unfreeze',b.effects)
 def test_backend_cannot_self_declare_production_environment(self):
  a,b,j,t=fixture();b.environment='PRODUCTION'
  with self.assertRaisesRegex(m.Refused,'NATIVE_ENVIRONMENT_MISMATCH'): self.invoke(a,b,j,t)
  self.assertEqual(b.effects,[])

class AttestedLockTests(unittest.TestCase):
 def test_missing_lock_requires_bound_attestation_not_empty_directory_assumption(self):
  a,b,j,t=fixture();c=b.checkpoint(a['target']);name='host/project-pmog2/.lock';del c['files'][name]
  with self.assertRaisesRegex(m.Refused,'REGISTERED_WRITER_LOCK_MISSING'):m.checkpoint_manifest(c,a)
  c['missingLockProofs']={name:{'stateSha256':m.sha(c['files']['host/project-pmog2/state.json']['bytes']),'dirDev':1,'dirIno':2,'targetBootId':a['target']['bootId'],'capturePhase':'FROZEN'}}
  m.checkpoint_manifest(c,a);c['missingLockProofs'][name]['stateSha256']='f'*64
  with self.assertRaisesRegex(m.Refused,'REGISTERED_WRITER_LOCK_MISSING'):m.checkpoint_manifest(c,a)
 def test_stale_lock_requires_exact_dead_or_reused_process_proof(self):
  a,b,j,t=fixture();c=b.checkpoint(a['target']);name='host/project-pmog2/.lock'
  lock=json.loads(c['files'][name]['bytes']);lock.update(pid=999999,start='11111');c['files'][name]['bytes']=m.canonical(lock)
  with self.assertRaisesRegex(m.Refused,'OTHER_OR_AMBIGUOUS_STORE_WRITER'):m.checkpoint_manifest(c,a)
  c['staleLockProofs']={name:{'lockSha256':m.sha(c['files'][name]['bytes']),'pid':999999,'startTicks':'11111','observedStartTicks':None,'bootId':a['target']['bootId']}}
  m.checkpoint_manifest(c,a);c['staleLockProofs'][name]['observedStartTicks']='11111'
  with self.assertRaisesRegex(m.Refused,'OTHER_OR_AMBIGUOUS_STORE_WRITER'):m.checkpoint_manifest(c,a)
 def test_boolean_schema_is_corrupt_under_original_Node_strict_schema(self):
  a,b,j,t=fixture();c=b.checkpoint(a['target']);name='host/state.json';row=json.loads(c['files'][name]['bytes']);row['schema']=True;c['files'][name]['bytes']=m.canonical(row)
  with self.assertRaisesRegex(m.Refused,'CORRUPT_STORE_STATE'):m.checkpoint_manifest(c,a)
 def test_production_backend_requires_protected_admission_even_with_same_environment(self):
  a,b,j,t=fixture();a['environment']='PRODUCTION';b.environment='PRODUCTION'
  with self.assertRaisesRegex(m.Refused,'PROTECTED_NATIVE_ADMISSION_REQUIRED'):m.Driver(b,j,lambda:t[0]).run(a)
 def test_foreign_backend_error_code_is_bounded_without_raw_exception_export(self):
  class BackendError(Exception):code='FREEZER_TRANSITION_UNPROVEN'
  self.assertEqual(m.code(BackendError('private bytes must not escape')),'FREEZER_TRANSITION_UNPROVEN')
  BackendError.code='secret/raw-message';self.assertEqual(m.code(BackendError()),'BOUNDED_BACKEND_FAILURE')

if __name__=='__main__': unittest.main()
