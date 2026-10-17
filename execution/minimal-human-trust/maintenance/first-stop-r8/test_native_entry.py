"""Offline native-entry fault/authority tests; never root, SSH or real state."""
import copy,importlib.util,json,sys,unittest
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import patch
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE))
import native_entry as n
import test_stop_driver as fixture
import bootstrap as bootstrap
class PowerLoss(BaseException):pass
class NativeTests(unittest.TestCase):
 def setUp(self):
  self.a,self.b,self.j,self.t=fixture.fixture();self.target=self.a['target'];self.capsule='c'*64
  self.files={};self.prompts=[];self.driver_calls=[]
  checkpoint=self.b.checkpoint(self.target)
  checkpoint.update({k:copy.deepcopy(self.a[k]) for k in ('expectedOriginalUnknown','expectedLeaseBindings','expectedSemanticBindingsDigest')})
  self.checkpoint=checkpoint
  outer=self
  class Reader:
   def capture_baseline(self,target):return copy.deepcopy(outer.checkpoint)
  class Backend:
   def __init__(self,*a): self.handles={}
   def inspect(self,t): return outer.b.inspect(t)
  class Journal:
   def __init__(self,admission): self.admission=admission
   @contextmanager
   def locked(self):yield self
   def read(self):return outer.j.read()
  class Tty:
   def say(self,msg):pass
   def close(self):pass
   def confirm(self,p,word):outer.prompts.append(copy.deepcopy(p));return n.digest(p)
  self.Tty=Tty
  def read(path,*a,**kw):
   key=Path(path).name
   if key not in self.files:raise FileNotFoundError(key)
   return self.files[key]
  def immutable(path,raw,*a):
   key=Path(path).name
   if key in self.files:n.need(self.files[key]==raw,'IMMUTABLE_FILE_CONFLICT')
   self.files[key]=raw
  self.patches=[patch.object(n,'root',lambda:None),patch.object(n,'load_capsule',lambda h:(HERE,self.target)),
   patch.object(n,'LedgerCheckpoint',Reader),patch.object(n,'LinuxBackend',Backend),patch.object(n,'RootJournal',Journal),
   patch.object(n,'secure_read',read),patch.object(n,'immutable',immutable),patch.object(n,'now_ms',lambda:self.t[0])]
  for p in self.patches:p.start()
  self.addCleanup(lambda:[p.stop() for p in reversed(self.patches)])
 def invoke(self,run):
  with patch.object(n,'run_driver',run):return n.stop(self.capsule,self.Tty)
 def crash_before_journal(self,backend,journal,approval):self.driver_calls.append(copy.deepcopy(approval));raise PowerLoss()
 def test_native_confirmation_complete_then_crash_before_BOUND_reuses_same_nonce_without_new_prompt(self):
  with self.assertRaises(PowerLoss):self.invoke(self.crash_before_journal)
  original=json.loads(self.files['approval.json']);self.assertEqual(len(self.prompts),1)
  self.t[0]+=1000
  got=self.invoke(lambda b,j,a:a)
  self.assertEqual(got,original);self.assertEqual(len(self.prompts),1)
 def test_approval_only_crash_reconfirms_same_exact_object_and_deadline(self):
  with self.assertRaises(PowerLoss):self.invoke(self.crash_before_journal)
  original=json.loads(self.files['approval.json']);del self.files['native-intent.json'];self.t[0]+=1000
  self.assertEqual(self.invoke(lambda b,j,a:a),original)
  self.assertEqual(len(self.prompts),2);self.assertEqual(self.prompts[0],self.prompts[1])
 def test_previous_pending_never_renews_expired_window(self):
  with self.assertRaises(PowerLoss):self.invoke(self.crash_before_journal)
  original=self.files['approval.json'];self.t[0]+=300001
  with self.assertRaisesRegex(n.Refused,'NATIVE_WINDOW_EXPIRED'):
   self.invoke(lambda *a:self.fail('expired driver called'))
  self.assertEqual(self.files['approval.json'],original);self.assertEqual(len(self.prompts),1)
 def test_tampered_previous_native_intent_never_runs_driver(self):
  with self.assertRaises(PowerLoss):self.invoke(self.crash_before_journal)
  bad=json.loads(self.files['native-intent.json']);bad['pendingHash']='d'*64;self.files['native-intent.json']=json.dumps(bad).encode()
  with self.assertRaisesRegex(n.Refused,'PREVIOUS_NATIVE_INTENT_DRIFT'):self.invoke(lambda *a:self.fail('driver called'))
 def test_status_does_not_call_driver_or_mutate_any_phase(self):
  with self.assertRaises(PowerLoss):self.invoke(self.crash_before_journal)
  approval=json.loads(self.files['approval.json'])
  self.j.value={'phase':'FREEZE_INTENT','approvalHash':n.digest(approval),'targetHash':n.digest(self.target),'signalAttemptConsumed':False}
  before=copy.deepcopy(self.j.value)
  with patch.object(n,'run_driver',lambda *a:self.fail('status called mutator')):
   result=n.entry('status',self.capsule)
  self.assertTrue(result['historicalReadOnly']);self.assertEqual(before,self.j.value)
 def test_no_parent_json_boolean_can_construct_native_capability(self):
  with self.assertRaisesRegex(n.Refused,'NATIVE_ADMISSION_REQUIRED'):n.NativeAdmission(True,self.target,self.capsule)
 def test_post_signal_cleanup_needs_exact_native_scope_and_durable_phase(self):
  cap=n.NativeAdmission(n._BRAND,self.target,self.capsule);a={**self.a,'capsuleHash':self.capsule};cap.bind(a)
  self.files['transaction.json']=json.dumps({'signalAttemptConsumed':True,'approvalHash':n.digest(a),'targetHash':n.digest(self.target)}).encode()
  with self.assertRaisesRegex(n.Refused,'POST_SIGNAL_AUTOMATIC_RESTORE_REFUSED'):cap.require('unfreeze-exited',self.target)
  cap.recovery_approved=True
  with self.assertRaisesRegex(n.Refused,'POST_SIGNAL_AUTOMATIC_RESTORE_REFUSED'):cap.require('unfence',self.target)
 def test_recovery_scope_needs_bound_phase_and_current_own_window(self):
  cap=n.NativeAdmission(n._BRAND,self.target,self.capsule);a={**self.a,'capsuleHash':self.capsule};cap.bind(a)
  recovery={'approvedAt':self.t[0],'deadline':self.t[0]+10000}
  scope={'stopApprovalHash':n.digest(a),'targetHash':n.digest(self.target),'recoveryHash':n.digest(recovery)}
  self.files['transaction.json']=json.dumps({'signalAttemptConsumed':True,'approvalHash':n.digest(a),'targetHash':n.digest(self.target)}).encode()
  self.files['restore-original.json']=json.dumps({'phase':'START_INTENT','scope':scope,'recovery':recovery}).encode();cap.recovery_approved=scope
  cap.require('unfreeze-exited',self.target);self.t[0]+=10001
  with self.assertRaisesRegex(n.Refused,'NATIVE_RECOVERY_EXPIRED'):cap.require('unfence',self.target)
 def test_forward_expiry_does_not_allow_new_signal_but_permits_readback(self):
  cap=n.NativeAdmission(n._BRAND,self.target,self.capsule);cap.bind({**self.a,'capsuleHash':self.capsule});self.t[0]+=300001
  with self.assertRaisesRegex(n.Refused,'NATIVE_WINDOW_EXPIRED'):cap.require('signal',self.target)
  cap.require('inspect',self.target)
 def test_foreground_terminal_required_before_any_prompt(self):
  with patch.object(n.os,'open',return_value=45),patch.object(n.os,'isatty',return_value=False):
   with self.assertRaisesRegex(n.Refused,'FOREGROUND_NATIVE_TERMINAL_REQUIRED'):n.Terminal()
class PreSignalRestoreTests(unittest.TestCase):
 setUp=NativeTests.setUp
 # Do not inherit the earlier cases into a second count.
 def setup_transition(self):
  a={**self.a,'environment':'PRODUCTION','capsuleHash':self.capsule};cap=n.NativeAdmission(n._BRAND,self.target,self.capsule);cap.bind(a)
  self.j.value={'schema':'r16.controlled-crash-stop-journal.v1','approvalHash':n.digest(a),'targetHash':n.digest(self.target),'phase':'RECOVERY_REQUIRED_BEFORE_SIGNAL','signalAttemptConsumed':False}
  self.files['transaction.json']=json.dumps(self.j.value).encode()
  self.b.row.update(frozen=False,freezeRequested=True,freezeOwner=n.digest(a),fenceOwner=n.digest(a))
  self.b.environment='PRODUCTION';self.b.handles={};self.b.assert_admitted=lambda a:cap.require('driver',a['target'])
  self.b._inspect=lambda target,allow_transition=False:copy.deepcopy(self.b.row)
  def unfreeze(target,owner):
   cap.require('unfreeze-transition',target);self.b.row.update(frozen=False,freezeRequested=False,freezeOwner=None);self.b.effects.append('undo-kernel-freeze-request')
  self.b.unfreeze=unfreeze
  checkpoint=self.checkpoint
  class Reader:
   def capture_baseline(self,target):return copy.deepcopy(checkpoint)
  self.j.files=type('Files',(),{'atomic':lambda _,path,raw,**kw:self.files.__setitem__(Path(path).name,raw)})()
  return a,cap,Reader()
 def test_transition_is_cancelled_only_after_fresh_native_scope_then_original_pid_restored_no_start_or_kill(self):
  a,cap,reader=self.setup_transition()
  with patch.object(n,'LinuxBackend',return_value=self.b):
   result=n.recover_before_signal_native(cap,a,self.j,self.Tty,reader)
  self.assertEqual(result['status'],'ABORTED_BEFORE_SIGNAL_ORIGINAL_RUNTIME_RESTORED')
  self.assertEqual(self.b.kill_calls,0);self.assertEqual(self.b.row['members'],[self.target['pid']]);self.assertIsNone(self.b.row['fenceOwner']);self.assertFalse(self.b.row['freezeRequested'])
 def test_transition_undo_refuses_after_signal_intent_before_any_new_prompt(self):
  a,cap,reader=self.setup_transition();self.j.value['signalAttemptConsumed']=True
  with patch.object(n,'LinuxBackend',return_value=self.b):
   with self.assertRaisesRegex(n.Refused,'PRE_SIGNAL_RECOVERY_ONLY'):n.recover_before_signal_native(cap,a,self.j,self.Tty,reader)
  self.assertEqual(self.prompts,[]);self.assertNotIn('undo-kernel-freeze-request',self.b.effects)
 def test_transition_undo_rejects_reused_target_and_preserves_fence(self):
  a,cap,reader=self.setup_transition();self.b.row['processExited']=True
  with patch.object(n,'LinuxBackend',return_value=self.b):
   with self.assertRaisesRegex(n.Refused,'ORIGINAL_LIVE_TARGET_UNPROVEN'):n.recover_before_signal_native(cap,a,self.j,self.Tty,reader)
  self.assertEqual(self.prompts,[]);self.assertIsNotNone(self.b.row['fenceOwner'])

if __name__=='__main__':unittest.main()
