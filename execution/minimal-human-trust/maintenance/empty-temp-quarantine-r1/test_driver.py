"""Pure in-memory protocol tests. No OS/backend import, commands or live state."""
import copy
import importlib.util
from pathlib import Path
import unittest

spec=importlib.util.spec_from_file_location('quarantine_driver_tested',Path(__file__).with_name('driver.py'))
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

class Crash(BaseException):pass
class Clock:
 def __init__(self):self.value=1000
 def __call__(self):return self.value
class Journal:
 def __init__(self):self.value=None;self.history=[]
 def read(self):return copy.deepcopy(self.value)
 def write(self,value):self.value=copy.deepcopy(value);self.history.append(copy.deepcopy(value))

def approval():
 return {'schema':m.SCHEMA,'environment':'ISOLATED_TEST','approvalId':'isolated-approval','approvedAt':1000,'deadline':301000,'policyProposalHash':m.POLICY_HASH,'sourceCapsuleHash':'a'*64,'capsuleHash':'b'*64,'target':copy.deepcopy(m.TARGET),'artifact':{'path':m.ARTIFACT_PATH,**m.ARTIFACT},'allowExactEmptyArtifactQuarantine':True,'acceptPossibleInMemoryStorePoisoning':True,'drainStatus':'UNPROVEN'}

def metadata(ino):
 return {'dev':64770,'ino':ino,'bytes':42,'sha256':'c'*64,'uid':1000,'gid':1001,'mode':0o600,'nlink':1,'mtimeNs':'1792126254419345897','ctimeNs':'1792126254419345897'}
def inventory():
 directories={name:{'dev':64770,'ino':900+i,'uid':1000,'gid':1001,'mode':0o700,'mtimeNs':'1792126254419345897','ctimeNs':'1792126254419345897'} for i,name in enumerate(('host','host/project-p2vox','host/project-pmog2'))}
 files={}
 for i,directory in enumerate(directories):
  files[directory+'/state.json']=metadata(100+i*2)
  files[directory+'/.lock']=metadata(101+i*2)
 files[m.ARTIFACT_NAME]=copy.deepcopy(m.ARTIFACT)
 return {'schema':m.INVENTORY_SCHEMA,'files':files,'directories':directories,'noOpenArtifactHandles':True,'otherWriterPids':[],'registrationHash':'d'*64,'registeredProjectCount':2,'drainStatus':'UNPROVEN','artifact':copy.deepcopy(m.ARTIFACT),'artifactLocation':'SOURCE'}
def attestation():
 return {'schema':'r16.r15-app-ledger-attestation.v1','signatureVerification':True,'sealedRegistrationVerified':True,'oldGrantActive':True,'sourceDeliveryRevision':16,'originalUnknownCount':2,'registeredProjectCount':2,'drainStatus':'UNPROVEN',**{k:'e'*64 for k in ('sourcePublicConfigDigest','grantHash','checkpointManifestDigest','semanticBindingsDigest','registrationHash')}}

class Backend:
 environment='ISOLATED_TEST'
 def __init__(self):
  self.state={**copy.deepcopy(m.TARGET),'processExited':False,'members':[m.TARGET['pid']],'activeState':'active','subState':'running','frozen':False,'freezeRequested':False,'freezeOwner':None,'fenceOwner':None}
  self.tree=inventory();self.location='SOURCE';self.artifact=copy.deepcopy(m.ARTIFACT);self.calls=[];self.effects=[];self.fail=None;self.after_fail=None;self.bad_after=None
 def call(self,name):
  self.calls.append(name)
  if self.fail==name:raise m.Refused('ISOLATED_'+name.upper().replace('-','_')+'_FAILURE')
 def effect(self,name):
  self.effects.append(name)
  if self.after_fail==name:raise m.Refused('ISOLATED_UNKNOWN_EFFECT')
 def inspect(self,target):
  self.call('inspect');return copy.deepcopy(self.state)
 def inspect_recovery(self,target):
  self.call('inspect-recovery');return copy.deepcopy(self.state)
 def fence(self,target,owner):self.call('fence');self.state['fenceOwner']=owner;self.effect('fence')
 def freeze(self,target,owner):
  self.call('freeze');self.state.update(frozen=True,freezeRequested=True,freezeOwner=owner);self.effect('freeze')
 def unfreeze(self,target,owner):
  self.call('unfreeze');self.state.update(frozen=False,freezeRequested=False,freezeOwner=None);self.effect('unfreeze')
 def unfence(self,target,owner):self.call('unfence');self.state['fenceOwner']=None;self.effect('unfence')
 def capture_before(self,target):self.call('capture-before');return copy.deepcopy(self.tree)
 def inspect_artifact(self,target,owner):
  self.call('inspect-artifact');return {'location':self.location,'artifact':copy.deepcopy(self.artifact) if self.location in ('SOURCE','QUARANTINE') else None}
 def quarantine(self,target,owner,before):
  self.call('quarantine');assert self.location=='SOURCE'
  self.location='QUARANTINE';self.artifact['ctimeNs']='1792126254419345900';del self.tree['files'][m.ARTIFACT_NAME]
  self.tree['directories']['host'].update(mtimeNs='1792126254419345900',ctimeNs='1792126254419345900')
  self.effect('quarantine');return {'location':self.location,'artifact':copy.deepcopy(self.artifact)}
 def verify_after(self,target,before):
  self.call('verify-after');result={**copy.deepcopy(self.tree),'artifactLocation':'QUARANTINE','artifact':copy.deepcopy(self.artifact),'ledgerAttestation':attestation()}
  if self.bad_after:self.bad_after(result)
  return result
 def restore(self,target,owner,before):
  self.call('restore');assert self.location=='QUARANTINE'
  if before.get('expectedQuarantinedArtifact')!=self.artifact:raise m.Refused('QUARANTINED_CTIME_DRIFT')
  current={k:v for k,v in self.tree['files'].items() if k!=m.ARTIFACT_NAME};expected={k:v for k,v in before['files'].items() if k!=m.ARTIFACT_NAME}
  if current!=expected:raise m.Refused('NORMAL_STORE_INVENTORY_CHANGED')
  self.location='SOURCE';self.artifact['ctimeNs']='1792126254419345910';self.tree['files'][m.ARTIFACT_NAME]=copy.deepcopy(self.artifact)
  self.tree['directories']['host'].update(mtimeNs='1792126254419345910',ctimeNs='1792126254419345910')
  self.effect('restore');return {'location':self.location,'artifact':copy.deepcopy(self.artifact)}
 def verify_restored(self,target,before,owner):
  self.call('verify-restored');return {**copy.deepcopy(self.tree),'artifactLocation':'SOURCE','artifact':copy.deepcopy(self.artifact)}
 def capture_inverse_before(self,target,owner):
  self.call('capture-inverse-before');return {**copy.deepcopy(self.tree),'artifactLocation':'QUARANTINE','artifact':copy.deepcopy(self.artifact),'ledgerAttestation':attestation()}

class DriverTests(unittest.TestCase):
 def setUp(self):self.a=approval();self.clock=Clock();self.backend=Backend();self.journal=Journal();self.driver=m.Driver(self.backend,self.journal,self.clock)
 def recovery(self,suffix='new'):
  return {'schema':m.RECOVERY_SCHEMA,'intentId':'native-recovery-'+suffix,'approvalHash':m.digest(self.a),'targetHash':m.digest(self.a['target']),'scope':'RESTORE_ORIGINAL_EMPTY_ARTIFACT','approvedAt':self.clock(),'deadline':self.clock()+120000}
 def test_forward_full_inventory_verifier_then_original_process_resumes(self):
  normal=copy.deepcopy(self.backend.tree['files']);normal.pop(m.ARTIFACT_NAME)
  result=self.driver.run(self.a)
  self.assertEqual(result['status'],m.TERMINAL[0]);self.assertTrue(result['ledgerValidatedWhileFrozen'])
  self.assertEqual(self.backend.effects,['fence','freeze','quarantine','unfreeze','unfence'])
  self.assertEqual(self.backend.tree['files'],normal);self.assertEqual(self.backend.location,'QUARANTINE')
  self.assertEqual(self.backend.state['pid'],m.TARGET['pid']);self.assertFalse(self.backend.state['frozen']);self.assertIsNone(self.backend.state['fenceOwner'])
  self.assertEqual(result['drainStatus'],'UNPROVEN');self.assertEqual(result['inMemoryStoreHealth'],'UNPROVEN');self.assertFalse(result['signalOrRestartPerformed'])
  self.assertIs(result['businessAcceptance'],False)
 def test_full_journal_contains_no_private_bytes_and_receipt_no_paths(self):
  result=self.driver.run(self.a);encoded=m.canonical(self.journal.value)
  self.assertIsInstance(encoded,str);self.assertNotIn('privateState',encoded)
  self.assertNotIn(m.ARTIFACT_PATH,m.canonical(result));self.assertNotIn('host/project-',m.canonical(result))
 def test_any_new_target_path_inode_timestamp_policy_or_scope_is_rejected_before_effects(self):
  for field,value in [('policyProposalHash','0'*64),('allowExactEmptyArtifactQuarantine',False),('capsuleHash','bad'),('sourceCapsuleHash','bad'),('drainStatus','PROVEN')]:
   self.setUp();self.a[field]=value
   with self.assertRaises(m.Refused):self.driver.run(self.a)
   self.assertEqual(self.backend.effects,[])
  for field,value in [('ino',1),('bytes',1),('ctimeNs',1792126254419345897),('path','/arbitrary')]:
   self.setUp();self.a['artifact'][field]=value
   with self.assertRaises(m.Refused):self.driver.run(self.a)
   self.assertEqual(self.backend.effects,[])
  self.setUp();self.a['target']['pid']+=1
  with self.assertRaises(m.Refused):self.driver.run(self.a)
 def test_expired_oversize_future_and_boolean_windows_refuse(self):
  for changes in ({'deadline':1000},{'deadline':301001},{'approvedAt':1001},{'approvedAt':True}):
   self.setUp();self.a.update(changes)
   with self.assertRaises(m.Refused):self.driver.run(self.a)
   self.assertEqual(self.backend.effects,[])
 def test_foreign_fence_freeze_extra_member_and_reused_pid_refused(self):
  for change in ({'fenceOwner':'f'*64},{'frozen':True,'freezeRequested':True,'freezeOwner':'f'*64},{'members':[1442662,2]},{'startTicks':'999'},{'invocationId':'f'*32},{'processExited':True}):
   self.setUp();self.backend.state.update(change)
   with self.assertRaises(m.Refused):self.driver.run(self.a)
   self.assertEqual(self.backend.effects,[])
 def test_full_baseline_rejects_other_temp_missing_inode_open_handle_and_bad_metadata(self):
  for change in ('other-temp','missing','open','nlink','mtime','ctime-number','uid','aliased','missing-project-state'):
   self.setUp();tree=self.backend.tree
   if change=='other-temp':tree['files']['host/.next-foreign']=metadata(321)
   elif change=='missing':del tree['files'][m.ARTIFACT_NAME]
   elif change=='open':tree['noOpenArtifactHandles']=False
   elif change=='nlink':tree['files'][m.ARTIFACT_NAME]['nlink']=2
   elif change=='mtime':tree['files'][m.ARTIFACT_NAME]['mtimeNs']='2'
   elif change=='ctime-number':tree['files'][m.ARTIFACT_NAME]['ctimeNs']=1792126254419345897
   elif change=='uid':tree['files']['host/state.json']['uid']=0
   elif change=='aliased':tree['files']['host/.lock']['ino']=tree['files']['host/state.json']['ino']
   else:del tree['files']['host/project-pmog2/state.json']
   result=self.driver.run(self.a);self.assertEqual(result['status'],'RECOVERY_REQUIRED');self.assertNotIn('quarantine',self.backend.effects)
 def test_failing_unchanged_r8_verifier_restores_original_inode_then_thaws(self):
  normal=copy.deepcopy(self.backend.tree['files']);normal.pop(m.ARTIFACT_NAME)
  self.backend.fail='verify-after';result=self.driver.run(self.a)
  self.assertEqual(result['status'],m.TERMINAL[1]);self.assertEqual(self.backend.location,'SOURCE')
  self.assertEqual(self.backend.effects,['fence','freeze','quarantine','restore','unfreeze','unfence'])
  self.assertTrue(m.artifact_matches(self.backend.artifact));self.assertNotEqual(self.backend.artifact['ctimeNs'],m.ARTIFACT['ctimeNs'])
  self.assertEqual({k:v for k,v in self.backend.tree['files'].items() if k!=m.ARTIFACT_NAME},normal)
 def test_normal_files_each_metadata_or_hash_drift_cannot_pass_validation(self):
  for field,value in [('sha256','f'*64),('mode',0o400),('uid',0),('gid',5),('nlink',2),('dev',5),('ino',5),('bytes',43),('mtimeNs','5'),('ctimeNs','5')]:
   self.setUp()
   def corrupt(result):result['files']['host/state.json'][field]=value
   self.backend.bad_after=corrupt;result=self.driver.run(self.a)
   self.assertEqual(result['status'],m.TERMINAL[1]);self.assertFalse(result['ledgerValidatedWhileFrozen'])
 def test_actual_committed_file_drift_keeps_protection_and_never_rolls_back_state(self):
  def mutate(result):
   result['files']['host/state.json']['sha256']='f'*64;self.backend.tree['files']['host/state.json']['sha256']='f'*64
  self.backend.bad_after=mutate;result=self.driver.run(self.a)
  self.assertEqual(result['status'],'RECOVERY_REQUIRED');self.assertEqual(self.backend.location,'QUARANTINE')
  self.assertTrue(self.backend.state['frozen']);self.assertIsNotNone(self.backend.state['fenceOwner'])
  self.assertEqual(self.backend.tree['files']['host/state.json']['sha256'],'f'*64)
 def test_verifier_signature_grant_registration_revision_unknown_count_not_caller_claim(self):
  for field,value in [('signatureVerification',False),('sealedRegistrationVerified',False),('oldGrantActive',False),('sourceDeliveryRevision',17),('originalUnknownCount',3),('registeredProjectCount',3),('drainStatus','PROVEN'),('schema','fake')]:
   self.setUp();self.backend.bad_after=lambda result:result['ledgerAttestation'].update({field:value})
   result=self.driver.run(self.a);self.assertEqual(result['status'],m.TERMINAL[1]);self.assertFalse(result['ledgerValidatedWhileFrozen'])
 def test_project_directory_metadata_and_times_are_preserved_root_parent_times_may_change(self):
  self.assertEqual(self.driver.run(self.a)['status'],m.TERMINAL[0])
  self.setUp();self.backend.bad_after=lambda result:result['directories']['host/project-p2vox'].update(ctimeNs='5')
  self.assertEqual(self.driver.run(self.a)['status'],m.TERMINAL[1])
 def test_every_forward_journal_crash_reentry_is_observation_only(self):
  for phase in ('BOUND','FENCE_INTENT','FENCED','FREEZE_INTENT','FROZEN','BASELINED','MOVE_INTENT','MOVED','VALIDATION_PASSED','THAW_INTENT','UNFENCE_INTENT','TERMINAL'):
   self.setUp()
   def fault(point):
    if point=='journal:'+phase:raise Crash()
   self.driver.fault=fault
   with self.assertRaises(Crash):self.driver.run(self.a)
   before=copy.deepcopy(self.backend.effects);self.driver.fault=lambda p:None;self.driver.run(self.a)
   self.assertEqual(self.backend.effects,before)
 def test_every_effect_crash_reentry_never_repeats_move_thaw_or_unfence(self):
  for effect in ('fence','freeze','quarantine','thaw','unfence'):
   self.setUp();self.driver.fault=lambda point:(_ for _ in ()).throw(Crash()) if point=='effect:'+effect else None
   with self.assertRaises(Crash):self.driver.run(self.a)
   before=copy.deepcopy(self.backend.effects);self.driver.fault=lambda p:None;self.driver.run(self.a)
   self.assertEqual(self.backend.effects,before)
 def test_unknown_forward_effect_only_new_native_recovery_can_inverse_once(self):
  self.backend.after_fail='quarantine';result=self.driver.run(self.a)
  self.assertEqual(result['status'],'RECOVERY_REQUIRED');self.assertEqual(self.backend.effects.count('quarantine'),1)
  self.assertIs(result['businessAcceptance'],False)
  self.driver.run(self.a);self.assertEqual(self.backend.effects.count('quarantine'),1)
  self.backend.after_fail=None;recovery=self.recovery();result=self.driver.recover(self.a,recovery)
  self.assertEqual(result['status'],m.TERMINAL[1]);self.assertEqual(self.backend.effects.count('restore'),1)
  self.assertEqual(self.backend.effects.count('quarantine'),1)
 def test_unknown_inverse_effect_recovery_reads_source_and_does_not_repeat_restore(self):
  self.backend.fail='verify-after';self.backend.after_fail='restore';result=self.driver.run(self.a)
  self.assertEqual(result['status'],'RECOVERY_REQUIRED');self.assertEqual(self.backend.location,'SOURCE')
  self.backend.after_fail=None;self.backend.fail=None;result=self.driver.recover(self.a,self.recovery())
  self.assertEqual(result['status'],m.TERMINAL[1]);self.assertEqual(self.backend.effects.count('restore'),1)
 def test_inverse_intent_consumed_before_call_never_replayed_even_new_native_intent(self):
  self.backend.fail='verify-after'
  self.driver.fault=lambda point:(_ for _ in ()).throw(Crash()) if point=='journal:RESTORE_INTENT' else None
  with self.assertRaises(Crash):self.driver.run(self.a)
  self.driver.fault=lambda p:None;self.backend.fail=None
  result=self.driver.recover(self.a,self.recovery());self.assertEqual(result['status'],'RECOVERY_REQUIRED')
  self.assertEqual(self.backend.effects.count('restore'),0);self.assertTrue(self.backend.state['frozen'])
 def test_new_native_recovery_required_and_no_path_scope_or_target_override(self):
  self.backend.after_fail='quarantine';self.driver.run(self.a);before=copy.deepcopy(self.backend.effects)
  for field,value in [('schema','fake'),('scope','MOVE_ANYTHING'),('approvalHash','f'*64),('targetHash','f'*64),('deadline',self.clock()+120001),('approvedAt',True)]:
   intent=self.recovery();intent[field]=value
   with self.assertRaises(m.Refused):self.driver.recover(self.a,intent)
   self.assertEqual(self.backend.effects,before)
 def test_repeat_recovery_intent_is_observation_only(self):
  self.backend.after_fail='quarantine';self.driver.run(self.a);self.backend.fail='restore';self.backend.after_fail=None
  intent=self.recovery();self.driver.recover(self.a,intent);before=copy.deepcopy(self.backend.effects)
  self.driver.recover(self.a,intent);self.assertEqual(self.backend.effects,before)
 def test_post_success_inverse_uses_current_state_baseline_without_reverting_state(self):
  self.driver.run(self.a);forward=copy.deepcopy(self.journal.value['receipt'])
  # Original App may write after thaw. Only fresh inverse baseline owns these
  # new bytes/identities; the forward baseline must never be restored over them.
  row=self.backend.tree['files']['host/state.json'];row.update(ino=555,sha256='f'*64,mtimeNs='1792126254419346000',ctimeNs='1792126254419346000')
  current=copy.deepcopy(row);result=self.driver.recover(self.a,self.recovery())
  self.assertEqual(result['status'],m.TERMINAL[2]);self.assertEqual(self.backend.tree['files']['host/state.json'],current)
  self.assertEqual(self.journal.value['forwardReceipt'],forward);self.assertIsNotNone(result['inverseBeforeManifestHash'])
  self.assertEqual(self.backend.effects.count('quarantine'),1);self.assertEqual(self.backend.effects.count('restore'),1)
  self.assertFalse(self.backend.state['frozen']);self.assertIsNone(self.backend.state['fenceOwner'])
 def test_post_success_inverse_bound_crash_does_not_reuse_old_forward_unfence_flags(self):
  self.driver.run(self.a)
  self.driver.fault=lambda point:(_ for _ in ()).throw(Crash()) if point=='journal:INVERSE_RECOVERY_BOUND' else None
  with self.assertRaises(Crash):self.driver.recover(self.a,self.recovery('first'))
  self.driver.fault=lambda p:None;before=copy.deepcopy(self.backend.effects)
  self.driver.run(self.a);self.assertEqual(self.backend.effects,before)
  result=self.driver.recover(self.a,self.recovery('second'))
  self.assertEqual(result['status'],m.TERMINAL[2]);self.assertEqual(self.backend.effects.count('restore'),1)
  self.assertEqual(self.backend.effects.count('fence'),2)
 def test_post_success_inverse_crash_matrix_no_duplicate_move_and_current_cycle_terminal(self):
  phases=('RECOVERY_FENCE_INTENT','RECOVERY_FREEZE_INTENT','INVERSE_BASELINED','RESTORE_INTENT','RESTORED','THAW_INTENT','UNFENCE_INTENT','TERMINAL')
  for phase in phases:
   self.setUp();self.driver.run(self.a)
   self.driver.fault=lambda point:(_ for _ in ()).throw(Crash()) if point=='journal:'+phase else None
   with self.assertRaises(Crash):self.driver.recover(self.a,self.recovery('first'))
   self.driver.fault=lambda p:None;before=copy.deepcopy(self.backend.effects)
   readback=self.driver.run(self.a);self.assertEqual(self.backend.effects,before)
   if phase=='TERMINAL':self.assertEqual(readback['status'],m.TERMINAL[2]);continue
   result=self.driver.recover(self.a,self.recovery('second'))
   self.assertEqual(self.backend.effects.count('quarantine'),1);self.assertLessEqual(self.backend.effects.count('restore'),1)
   if phase=='RESTORE_INTENT':self.assertEqual(result['status'],'RECOVERY_REQUIRED')
   else:self.assertEqual(result['status'],m.TERMINAL[2])
 def test_post_success_inverse_unknown_restore_does_not_repeat_and_late_unfence_can_close(self):
  self.driver.run(self.a);self.backend.after_fail='restore'
  result=self.driver.recover(self.a,self.recovery('first'));self.assertEqual(result['status'],'RECOVERY_REQUIRED')
  self.backend.after_fail=None;result=self.driver.recover(self.a,self.recovery('second'))
  self.assertEqual(result['status'],m.TERMINAL[2]);self.assertEqual(self.backend.effects.count('restore'),1)
  self.setUp();self.driver.run(self.a)
  self.driver.fault=lambda point:(_ for _ in ()).throw(Crash()) if point=='effect:unfence' else None
  with self.assertRaises(Crash):self.driver.recover(self.a,self.recovery('first'))
  self.driver.fault=lambda p:None;before=copy.deepcopy(self.backend.effects)
  result=self.driver.recover(self.a,self.recovery('second'))
  self.assertEqual(result['status'],m.TERMINAL[2]);self.assertEqual(self.backend.effects,before)
 def test_success_inverse_wrong_new_target_or_conflicting_artifact_keeps_protection(self):
  for change in ('pid','artifact'):
   self.setUp();self.driver.run(self.a)
   if change=='pid':self.backend.state['startTicks']='999'
   else:self.backend.location='CONFLICT'
   result=self.driver.recover(self.a,self.recovery());self.assertEqual(result['status'],'RECOVERY_REQUIRED')
   self.assertEqual(self.backend.effects.count('restore'),0)
 def test_early_capture_failure_new_native_recovery_only_withdraws_own_protection(self):
  self.backend.fail='capture-before';self.driver.run(self.a);self.backend.fail=None
  result=self.driver.recover(self.a,self.recovery());self.assertEqual(result['status'],m.TERMINAL[1])
  self.assertFalse(result['ledgerValidatedWhileFrozen']);self.assertEqual(self.backend.effects,['fence','freeze','unfreeze','unfence'])
 def test_fence_intent_without_actual_effect_can_abort_without_creating_new_protection(self):
  self.backend.fail='fence';self.driver.run(self.a);self.backend.fail=None
  result=self.driver.recover(self.a,self.recovery());self.assertEqual(result['status'],m.TERMINAL[1]);self.assertEqual(self.backend.effects,[])
 def test_freeze_transition_foreign_owner_cannot_be_thawed_by_recovery(self):
  self.backend.fail='capture-before';self.driver.run(self.a);self.backend.fail=None
  self.backend.state.update(frozen=False,freezeRequested=True,freezeOwner='f'*64)
  before=copy.deepcopy(self.backend.effects);result=self.driver.recover(self.a,self.recovery())
  self.assertEqual(result['status'],'RECOVERY_REQUIRED');self.assertEqual(self.backend.effects,before)
 def test_freeze_pending_transition_new_native_recovery_cancels_only_own_request(self):
  def freeze(target,owner):
   self.backend.state.update(frozen=False,freezeRequested=True,freezeOwner=owner);self.backend.effects.append('freeze')
   raise m.Refused('FREEZE_NOT_CONFIRMED')
  self.backend.freeze=freeze;self.driver.run(self.a)
  result=self.driver.recover(self.a,self.recovery());self.assertEqual(result['status'],m.TERMINAL[1]);self.assertEqual(self.backend.effects.count('unfreeze'),1)
 def test_failed_unfence_receipt_write_recovers_by_readback_not_repeated_effect(self):
  self.driver.fault=lambda point:(_ for _ in ()).throw(Crash()) if point=='effect:unfence' else None
  with self.assertRaises(Crash):self.driver.run(self.a)
  self.driver.fault=lambda p:None;before=copy.deepcopy(self.backend.effects)
  result=self.driver.recover(self.a,self.recovery());self.assertEqual(result['status'],m.TERMINAL[0]);self.assertEqual(self.backend.effects,before)
 def test_approval_expiry_keeps_protection_new_recovery_window_does_not_reauthorize_forward(self):
  original=self.backend.verify_after
  def verify(target,before):
   result=original(target,before);self.clock.value=self.a['deadline'];return result
  self.backend.verify_after=verify;result=self.driver.run(self.a)
  self.assertEqual(result['status'],'RECOVERY_REQUIRED');self.assertTrue(self.backend.state['frozen'])
  self.backend.verify_after=original;result=self.driver.recover(self.a,self.recovery())
  self.assertEqual(result['status'],m.TERMINAL[1]);self.assertEqual(self.backend.effects.count('quarantine'),1)
 def test_lost_quarantine_receipt_or_ctime_touch_cannot_auto_inverse(self):
  original=self.backend.verify_after
  def verify(target,before):
   self.backend.artifact['ctimeNs']='1792126254419346999';raise m.Refused('CHECKPOINT_REFUSED')
  self.backend.verify_after=verify;result=self.driver.run(self.a)
  self.assertEqual(result['status'],'RECOVERY_REQUIRED');self.assertEqual(self.backend.effects.count('restore'),0)
  self.backend.verify_after=original;result=self.driver.recover(self.a,self.recovery())
  self.assertEqual(result['status'],m.TERMINAL[1]);self.assertEqual(self.backend.effects.count('restore'),1)
 def test_successful_verifier_cannot_hide_quarantine_ctime_change_after_move_receipt(self):
  original=self.backend.verify_after
  def touch(target,before):
   self.backend.artifact['ctimeNs']='1792126254419346999';return original(target,before)
  self.backend.verify_after=touch;result=self.driver.run(self.a)
  self.assertEqual(result['status'],'RECOVERY_REQUIRED');self.assertEqual(self.backend.effects.count('restore'),0)
  self.assertTrue(self.backend.state['frozen']);self.assertIsNotNone(self.backend.state['fenceOwner'])
 def test_unknown_location_never_thaws_or_repeats_move(self):
  self.backend.after_fail='quarantine';self.driver.run(self.a);self.backend.location='UNKNOWN';before=copy.deepcopy(self.backend.effects)
  result=self.driver.recover(self.a,self.recovery());self.assertEqual(result['status'],'RECOVERY_REQUIRED');self.assertEqual(self.backend.effects,before)

if __name__=='__main__':unittest.main()
