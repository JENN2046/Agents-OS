"""Isolated native-entry tests: memory journals, fake TTY and no OS effects."""
from contextlib import ExitStack,contextmanager
from copy import deepcopy
import importlib.util
import os
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

HERE=Path(__file__).resolve().parent
def load(name,path):
 spec=importlib.util.spec_from_file_location(name,path);module=importlib.util.module_from_spec(spec)
 sys.modules[name]=module;spec.loader.exec_module(module);return module

# Load original dependencies as in the sealed loader, then restore the global
# module registry. No class constructor, root check or file helper executes.
with patch.dict(sys.modules):
 C=load('r8_common_safe',HERE.parent/'first-stop-r8/common_safe.py')
 R=load('r8_linux_backend',HERE.parent/'first-stop-r8/linux_backend.py')
 L=load('r8_ledger_checkpoint',HERE.parent/'first-stop-r8/ledger_checkpoint.py')
 D=load('quarantine_driver',HERE/'driver.py')
 B=load('quarantine_backend',HERE/'backend.py')
 E=load('quarantine_entry',HERE/'entry.py')
 F=load('quarantine_pure_protocol_test_fixture',HERE/'test_driver.py')

class MemoryJournal:
 def __init__(self):self.value=None;self.history=[];self.is_locked=False;self.lock_calls=0;self.read_calls=0
 def read(self):self.read_calls+=1;return deepcopy(self.value)
 def write(self,value):
  C.need(self.is_locked,'ISOLATED_LOCK_REQUIRED');self.value=deepcopy(value);self.history.append(deepcopy(value))
 @contextmanager
 def locked(self):
  C.need(not self.is_locked,'ISOLATED_REENTRANT_LOCK');self.lock_calls+=1;self.is_locked=True
  try:yield self
  finally:self.is_locked=False

class FakeBackend:
 environment='PRODUCTION' # Exercise production native admission using NO OS.
 def __init__(self,cap,physical=None):self.cap=cap;self.physical=physical or F.Backend()
 def __getattr__(self,name):return getattr(self.physical,name)
 def inspect(self,target):self.cap.require('inspect',target);return self.physical.inspect(target)
 def inspect_recovery(self,target):self.cap.require('inspect',target);return self.physical.inspect_recovery(target)
 def capture_before(self,target):self.cap.require('capture-before',target);return self.physical.capture_before(target)
 def inspect_artifact(self,target,owner):self.cap.require('inspect-artifact',target);return self.physical.inspect_artifact(target,owner)
 def fence(self,target,owner):self.cap.require('fence',target);return self.physical.fence(target,owner)
 def freeze(self,target,owner):self.cap.require('freeze',target);return self.physical.freeze(target,owner)
 def unfreeze(self,target,owner):self.cap.require('unfreeze',target);return self.physical.unfreeze(target,owner)
 def unfence(self,target,owner):self.cap.require('unfence',target);return self.physical.unfence(target,owner)
 def quarantine(self,target,owner,before):self.cap.require('quarantine',target);return self.physical.quarantine(target,owner,before)
 def restore(self,target,owner,before):self.cap.require('restore',target);return self.physical.restore(target,owner,before)
 def verify_after(self,target,before):self.cap.require('verify-after',target);return self.physical.verify_after(target,before)
 def verify_restored(self,target,before,owner):self.cap.require('verify-restored',target);return self.physical.verify_restored(target,before,owner)
 def capture_inverse_before(self,target,owner):self.cap.require('capture-inverse-before',target);return self.physical.capture_inverse_before(target,owner)

class NativeEntryTests(unittest.TestCase):
 def setUp(self):
  self.stack=ExitStack();self.addCleanup(self.stack.close)
  self.clock=F.Clock();self.monotonic=50.0;self.pin='b'*64;self.journal=MemoryJournal();self.audit={};self.backend=None;self.constructed=[]
  self.real_unused=E.unused_intent_metadata
  def backend(cap):
   if self.backend is None:self.backend=FakeBackend(cap)
   adapter=FakeBackend(cap,self.backend.physical)
   self.constructed.append(cap);return adapter
  def immutable(path,raw,*args,**kwargs):
   name=str(path);previous=self.audit.get(name)
   C.need(previous is None or previous==raw,'ISOLATED_IMMUTABLE_CONFLICT');self.audit[name]=raw
  self.patches=[patch.object(E,'root'),patch.object(E,'Journal',return_value=self.journal),patch.object(E,'now',self.clock),patch.object(E.time,'monotonic',side_effect=lambda:self.monotonic),patch.object(E.secrets,'token_hex',return_value='1'*32),patch.object(E,'QuarantineBackend',side_effect=backend),patch.object(E,'unused_intent_metadata'),patch.object(E.C,'immutable',side_effect=immutable),patch.object(E.C,'secure_read',side_effect=lambda path,*a,**k:self.audit[str(path)]),patch.object(E.os,'statvfs',return_value=types.SimpleNamespace(f_bavail=100000,f_frsize=4096))]
  for item in self.patches:self.stack.enter_context(item)
 def terminal(self,*,confirm=None):
  outer=self
  class TTY:
   def __init__(self):self.closed=False
   def confirm(self,pending,word):
    outer.pending=deepcopy(pending);outer.word=word
    if confirm:return confirm(pending,word)
    return D.digest(pending)
   def close(self):self.closed=True;outer.closed=True
  return TTY
 def approved(self):return E.source_approval(self.pin,D.TARGET)
 def cap(self,approval=None,recovery=None):
  cap=E.Admission(E.BRAND,D.TARGET,self.pin,self.journal)
  if approval is not None:cap.bind(approval,recovery)
  return cap
 def seed_record(self,a):self.journal.value={'schema':'r16.exact-empty-artifact-quarantine-journal.v1','approvalHash':D.digest(a),'targetHash':D.digest(a['target']),'phase':'BOUND','quarantineAttemptConsumed':False,'inverseAttemptConsumed':False}
 def execute(self):return E.execute(self.pin,D.TARGET,terminal_factory=self.terminal())
 def test_brand_target_and_source_capsule_cannot_be_replaced(self):
  with self.assertRaisesRegex(C.Refused,'EXACT_NATIVE_TARGET_REQUIRED'):E.Admission(object(),D.TARGET,self.pin,self.journal)
  with self.assertRaisesRegex(C.Refused,'EXACT_NATIVE_TARGET_REQUIRED'):E.Admission(E.BRAND,{**D.TARGET,'pid':4},self.pin,self.journal)
  for k,v in [('capsuleHash','f'*64),('sourceCapsuleHash','f'*64),('environment','ISOLATED_TEST')]:
   a=self.approved();a[k]=v
   with self.assertRaisesRegex(C.Refused,'NATIVE_CAPSULE_TARGET_DRIFT'):self.cap(a)
 def test_all_read_operations_work_without_a_native_intent_and_never_mutate(self):
  cap=self.cap()
  for operation in E.READ_OPS:cap.require(operation,D.TARGET)
  self.assertEqual(self.journal.history,[]);self.assertEqual(self.audit,{})
  for operation in E.EFFECT_OPS:
   with self.assertRaisesRegex(C.Refused,'NATIVE_EXACT_INTENT_REQUIRED'):cap.require(operation,D.TARGET)
 def test_unlisted_signal_start_stop_or_arbitrary_command_is_never_an_admission(self):
  for operation in ('signal','open-pidfd','stop','start','restart','exec','install','issue','read-any-path'):
   with self.assertRaisesRegex(C.Refused,'QUARANTINE_OPERATION_FORBIDDEN'):self.cap().require(operation,D.TARGET)
 def test_admission_needs_held_journal_and_matching_published_transaction(self):
  a=self.approved();cap=self.cap(a)
  with self.assertRaisesRegex(C.Refused,'NATIVE_EXACT_INTENT_REQUIRED'):cap.require('quarantine',D.TARGET)
  self.journal.is_locked=True
  with self.assertRaisesRegex(C.Refused,'NATIVE_ROOT_TRANSACTION_REQUIRED'):cap.require('quarantine',D.TARGET)
  self.seed_record(a);cap.require('quarantine',D.TARGET)
  self.journal.value['approvalHash']='f'*64
  with self.assertRaisesRegex(C.Refused,'NATIVE_ROOT_TRANSACTION_REQUIRED'):cap.require('quarantine',D.TARGET)
 def test_admission_requires_exact_target_and_both_epoch_and_monotonic_deadline(self):
  a=self.approved();self.seed_record(a);self.journal.is_locked=True;cap=self.cap(a)
  with self.assertRaisesRegex(C.Refused,'EXACT_NATIVE_TARGET_DRIFT'):cap.require('inspect',{**D.TARGET,'startTicks':'99'})
  cap.require('freeze',D.TARGET);self.clock.value=a['deadline']
  with self.assertRaisesRegex(C.Refused,'NATIVE_EFFECT_WINDOW_EXPIRED'):cap.require('freeze',D.TARGET)
  self.clock.value=a['approvedAt'];self.monotonic=cap.monotonic_end
  with self.assertRaisesRegex(C.Refused,'NATIVE_EFFECT_WINDOW_EXPIRED'):cap.require('freeze',D.TARGET)
  cap.require('inspect',D.TARGET) # Historical read never extends effect scope.
 def test_recovery_cap_cannot_forward_quarantine_and_needs_published_new_intent(self):
  a=self.approved();self.seed_record(a);self.journal.is_locked=True
  intent={'schema':D.RECOVERY_SCHEMA,'intentId':'new-native-recovery','approvalHash':D.digest(a),'targetHash':D.digest(D.TARGET),'scope':'RESTORE_ORIGINAL_EMPTY_ARTIFACT','approvedAt':self.clock(),'deadline':self.clock()+120000}
  cap=self.cap(a,intent)
  with self.assertRaisesRegex(C.Refused,'NATIVE_RECOVERY_BINDING_REQUIRED'):cap.require('restore',D.TARGET)
  self.journal.value['recoveryIntentHash']=D.digest(intent)
  cap.require('restore',D.TARGET);cap.require('unfreeze-transition',D.TARGET)
  with self.assertRaisesRegex(C.Refused,'RECOVERY_CANNOT_QUARANTINE'):cap.require('quarantine',D.TARGET)
  self.assertEqual(cap.recovery_approved['stopApprovalHash'],D.digest(a))
  self.clock.value=intent['deadline']
  with self.assertRaisesRegex(C.Refused,'NATIVE_EFFECT_WINDOW_EXPIRED'):cap.require('restore',D.TARGET)
 def test_forward_cap_cannot_cancel_freeze_transition_without_new_native_scope(self):
  a=self.approved();self.seed_record(a);self.journal.is_locked=True;cap=self.cap(a)
  with self.assertRaisesRegex(C.Refused,'NEW_NATIVE_RECOVERY_INTENT_REQUIRED'):cap.require('unfreeze-transition',D.TARGET)
 def test_insufficient_forward_headroom_refuses_effect_before_backend(self):
  a=self.approved();self.seed_record(a);self.journal.is_locked=True;cap=self.cap(a)
  with patch.object(E.os,'statvfs',return_value=types.SimpleNamespace(f_bavail=0,f_frsize=4096)):
   for op in ('fence','freeze','quarantine'):
    with self.assertRaisesRegex(C.Refused,'QUARANTINE_TRANSACTION_SPACE_UNPROVEN'):cap.require(op,D.TARGET)
 def test_preflight_reads_complete_forensic_inventory_without_lock_intent_or_effect(self):
  result=E.preflight(self.pin,D.TARGET)
  self.assertEqual(result['status'],'QUARANTINE_READ_ONLY_PREFLIGHT_PASS');self.assertFalse(result['completeLedgerVerifiedBeforeQuarantine'])
  self.assertTrue(result['completeLedgerMustPassAfterQuarantine']);self.assertFalse(result['freezeIssued']);self.assertFalse(result['rootSourceInstalled'])
  self.assertEqual(result['signalsIssued'],0);self.assertEqual(self.journal.lock_calls,0);self.assertEqual(self.journal.history,[]);self.assertEqual(self.audit,{})
  self.assertEqual(self.backend.effects,[]);self.assertIn(D.ARTIFACT_NAME,self.backend.tree['files'])
 def test_status_without_transaction_never_constructs_backend_or_takes_lock(self):
  result=E.status(self.pin,D.TARGET)
  self.assertFalse(result['transactionExists']);self.assertEqual(self.constructed,[]);self.assertEqual(self.journal.lock_calls,0);self.assertEqual(self.audit,{})
 def test_status_existing_terminal_remains_readonly_even_after_original_deadline(self):
  self.execute();before=deepcopy(self.backend.effects);history=deepcopy(self.journal.history);audit=deepcopy(self.audit);locks=self.journal.lock_calls
  self.clock.value+=900000;result=E.status(self.pin,D.TARGET)
  self.assertEqual(result['status'],'READ_ONLY_STATUS');self.assertTrue(result['historicalOutcomeIsNotCurrentBusinessHealth'])
  self.assertEqual(self.backend.effects,before);self.assertEqual(self.journal.history,history);self.assertEqual(self.audit,audit);self.assertEqual(self.journal.lock_calls,locks)
 def test_execute_cancelled_confirmation_closes_tty_and_creates_no_intent_or_effect(self):
  def cancelled(pending,word):raise C.Refused('EXACT_NATIVE_INTENT_CANCELLED')
  with self.assertRaisesRegex(C.Refused,'EXACT_NATIVE_INTENT_CANCELLED'):E.execute(self.pin,D.TARGET,self.terminal(confirm=cancelled))
  self.assertTrue(self.closed);self.assertEqual(self.audit,{});self.assertEqual(self.journal.history,[]);self.assertEqual(self.backend.effects,[])
 def test_execute_wrong_confirmation_hash_or_expired_confirmation_never_mints_intent(self):
  for expire in (False,True):
   def invalid(pending,word):
    if expire:self.clock.value=pending['deadline'];return D.digest(pending)
    return 'f'*64
   with self.assertRaisesRegex(C.Refused,'EXACT_NATIVE_INTENT_REFUSED'):E.execute(self.pin,D.TARGET,self.terminal(confirm=invalid))
   self.assertEqual(self.audit,{});self.assertEqual(self.journal.history,[]);self.assertEqual(self.backend.effects,[])
   self.clock.value=1000
 def test_execute_valid_confirmation_publishes_exact_intent_then_real_protocol_only_fake_effects(self):
  result=self.execute();self.assertEqual(result['status'],D.TERMINAL[0]);self.assertEqual(self.word,'QUARANTINE');self.assertTrue(self.closed)
  self.assertEqual(len(self.audit),1);saved=C.parse(next(iter(self.audit.values())))
  self.assertEqual(saved['pendingHash'],D.digest(self.pending));self.assertEqual(saved['approval'],self.pending)
  self.assertEqual(saved['trustedClient'],'FOREGROUND_CLOUD_ROOT_TTY');self.assertEqual(self.journal.value['approvalHash'],saved['pendingHash'])
  self.assertEqual(self.backend.effects,['fence','freeze','quarantine','unfreeze','unfence'])
  self.assertFalse(self.journal.is_locked)
 def test_existing_transaction_execute_only_returns_status_without_second_confirmation(self):
  self.execute();before=deepcopy(self.backend.effects);audit=deepcopy(self.audit)
  def forbidden():raise AssertionError('second native confirmation must not occur')
  result=E.execute(self.pin,D.TARGET,forbidden)
  self.assertEqual(result['status'],'READ_ONLY_STATUS');self.assertEqual(self.backend.effects,before);self.assertEqual(self.audit,audit)
 def test_recovery_pending_binds_journal_hash_even_when_original_phase_did_not_change(self):
  self.execute();before=deepcopy(self.backend.effects);audit=deepcopy(self.audit)
  def drift(pending,word):self.journal.value['extraAuditHash']='f'*64;return D.digest(pending)
  with self.assertRaisesRegex(C.Refused,'NATIVE_RECOVERY_PENDING_OBJECT_CHANGED'):E.recover(self.pin,D.TARGET,self.terminal(confirm=drift))
  self.assertEqual(self.backend.effects,before);self.assertEqual(self.audit,audit);self.assertEqual(self.word,'RESTORE_EMPTY')
 def test_recovery_pending_binds_artifact_ctime_only_change_before_effects(self):
  self.execute();before=deepcopy(self.backend.effects);audit=deepcopy(self.audit)
  def drift(pending,word):self.backend.artifact['ctimeNs']=str(int(self.backend.artifact['ctimeNs'])+1);return D.digest(pending)
  with self.assertRaisesRegex(C.Refused,'NATIVE_RECOVERY_PENDING_OBJECT_CHANGED'):E.recover(self.pin,D.TARGET,self.terminal(confirm=drift))
  self.assertEqual(self.backend.effects,before);self.assertEqual(self.audit,audit)
 def test_recovery_cancelled_confirmation_has_no_new_intent_or_effect(self):
  self.execute();before=deepcopy(self.backend.effects);audit=deepcopy(self.audit)
  def cancelled(pending,word):raise C.Refused('EXACT_NATIVE_INTENT_CANCELLED')
  with self.assertRaisesRegex(C.Refused,'EXACT_NATIVE_INTENT_CANCELLED'):E.recover(self.pin,D.TARGET,self.terminal(confirm=cancelled))
  self.assertTrue(self.closed);self.assertEqual(self.backend.effects,before);self.assertEqual(self.audit,audit)
 def test_valid_new_recovery_native_intent_really_runs_inverse_with_fresh_baseline(self):
  self.execute();self.backend.tree['files']['host/state.json'].update(ino=777,sha256='f'*64,mtimeNs='1792126254419350000',ctimeNs='1792126254419350000')
  updated=deepcopy(self.backend.tree['files']['host/state.json']);result=E.recover(self.pin,D.TARGET,self.terminal())
  self.assertEqual(result['status'],D.TERMINAL[2]);self.assertEqual(self.backend.tree['files']['host/state.json'],updated)
  self.assertEqual(self.backend.effects.count('restore'),1);self.assertEqual(self.backend.effects.count('quarantine'),1)
  self.assertEqual(len(self.audit),2);self.assertIsNotNone(self.journal.value.get('recoveryIntentHash'))
  self.assertTrue(self.journal.value.get('forwardReceipt'));self.assertFalse(self.journal.is_locked)
 @contextmanager
 def audit_pair(self):
  """Real private temp inode/link pair; UID alone is a root-test seam.

  Only this freshly created temporary tree may be observed by the metadata
  seam. Production fixed paths, ownership guards and file helpers are unchanged.
  """
  with tempfile.TemporaryDirectory() as tmp:
   base=Path(tmp);state=base/'state';state.mkdir(mode=0o700);folder=state/'approved-intents';folder.mkdir(mode=0o700)
   approval=self.approved();raw=E.encode({'schema':'r16.exact-empty-artifact-native-intent.v1','approval':approval,'pendingHash':D.digest(approval),'capsuleHash':self.pin,'trustedClient':'FOREGROUND_CLOUD_ROOT_TTY','confirmedAt':self.clock()})
   final=folder/(D.digest(approval)+'.json');final.write_bytes(raw);final.chmod(0o600)
   pending=folder/('.'+final.name+'.'+C.sha(raw)+'.pending');os.link(final,pending)
   real_lstat=Path.lstat;real_fstat=os.fstat
   class RootMetadata:
    def __init__(self,actual):self.actual=actual;self.st_uid=0
    def __getattr__(self,name):return getattr(self.actual,name)
   def lstat(path,*args,**kwargs):
    self.assertTrue(path.is_relative_to(base),'fixture metadata must never read a production path')
    return RootMetadata(real_lstat(path,*args,**kwargs))
   def directory(path,*args,**kwargs):
    self.assertTrue(Path(path).is_relative_to(base));return path
   self.journal.files=types.SimpleNamespace(directory=directory)
   with patch.object(E,'STATE',state),patch.object(E,'unused_intent_metadata',self.real_unused),patch.object(Path,'lstat',autospec=True,side_effect=lstat),patch.object(E.os,'fstat',side_effect=lambda fd:RootMetadata(real_fstat(fd))):
    yield base,final,pending,raw
 def test_exact_immutable_nlink2_audit_pair_is_retained_and_preflight_can_continue(self):
  with self.audit_pair() as (_,final,pending,raw):
   identity=(final.lstat().st_dev,final.lstat().st_ino);names=set(os.listdir(final.parent))
   result=E.preflight(self.pin,D.TARGET)
   self.assertEqual(result['status'],'QUARANTINE_READ_ONLY_PREFLIGHT_PASS')
   self.assertEqual(final.read_bytes(),raw);self.assertEqual(pending.read_bytes(),raw)
   self.assertEqual(final.lstat().st_nlink,2);self.assertEqual(pending.lstat().st_nlink,2)
   self.assertEqual((pending.lstat().st_dev,pending.lstat().st_ino),identity);self.assertEqual(set(os.listdir(final.parent)),names)
   self.assertEqual(self.audit,{});self.assertIsNone(self.journal.value);self.assertEqual(self.journal.history,[])
   self.assertEqual(self.journal.lock_calls,0);self.assertEqual(self.backend.effects,[])
 def test_unknown_second_link_does_not_become_a_permitted_immutable_pair(self):
  with self.audit_pair() as (base,final,pending,raw):
   pending.unlink();outside=base/'unknown-link';os.link(final,outside)
   with self.assertRaisesRegex(C.Refused,'UNSAFE_INTENT_AUDIT_LINKS'):E.preflight(self.pin,D.TARGET)
   self.assertEqual(final.read_bytes(),raw);self.assertEqual(outside.read_bytes(),raw)
   self.assertEqual(final.lstat().st_nlink,2);self.assertEqual(self.constructed,[]);self.assertEqual(self.audit,{})
 def test_pair_pending_name_hash_content_or_third_link_mismatch_is_refused_without_effect(self):
  for drift in ('hash','name','content','third-link'):
   with self.audit_pair() as (base,final,pending,raw):
    if drift=='hash':pending.rename(pending.with_name('.'+final.name+'.'+'0'*64+'.pending'))
    elif drift=='name':pending.rename(pending.with_name('.'+'f'*64+'.json.'+C.sha(raw)+'.pending'))
    elif drift=='content':final.write_bytes(raw+b' ')
    else:os.link(final,base/'third-link')
    with self.assertRaises(C.Refused):E.preflight(self.pin,D.TARGET)
    self.assertTrue(final.exists());self.assertEqual(self.constructed,[]);self.assertEqual(self.audit,{})

class RootIdentityTests(unittest.TestCase):
 def test_fixed_root_and_host_guard_drops_core_limit_before_rejecting_wrong_identity(self):
  for uid,euid,host in ((1000,1000,'VM-0-12-ubuntu'),(0,1000,'VM-0-12-ubuntu'),(0,0,'untrusted-host')):
   with patch.object(E.resource,'setrlimit') as no_core,patch.object(E.os,'getuid',return_value=uid),patch.object(E.os,'geteuid',return_value=euid),patch.object(E.socket,'gethostname',return_value=host):
    with self.assertRaisesRegex(C.Refused,'FIXED_CLOUD_ROOT_REQUIRED'):E.root()
    no_core.assert_called_once_with(E.resource.RLIMIT_CORE,(0,0))

if __name__=='__main__':unittest.main()
