"""Fault tests of same-plan external transition; no real systemd/production IO."""
import copy,importlib.util,json,unittest
from pathlib import Path
spec=importlib.util.spec_from_file_location('native_stop',Path(__file__).with_name('stop_transition.py'));s=importlib.util.module_from_spec(spec);spec.loader.exec_module(s)
class Crash(Exception):simulatedCrash=True
class Journal:
 def __init__(self):self.value=None
 def read(self):return copy.deepcopy(self.value)
 def write(self,v):self.value=copy.deepcopy(v)
class Backend:
 environment='ISOLATED_TEST'
 def __init__(self):
  self.events=[];self.fenced=set();self.stopped=set();self.frozen=False;self.kills=0;self.fail=None;self.extra=False;self.drift=False;self.authorized=True
  self.baseline={u:{'unit':u,'host':h,'pid':12 if u==s.NATIVE else 1,'startTicks':'123','bootId':'fixture','invocationId':'fixture','cgroup':'/system.slice/'+u,'nativeVersion':s.SOURCE_NATIVE if u==s.NATIVE else None} for u,h in s.HOSTS.items()}
  self.c={'schema':'r16.source19-native-checkpoint.v1','completeRegisteredFileSet':True,'noForeignWriters':True,'noTemporaryFiles':True,'newUnknown':[],'inflight':[],'originalUnknown':copy.deepcopy(s.UNKNOWN),'originalSignaturesAndLeasesVerified':True,'originalLeaseBindingsHash':'b'*64,'registeredRootsHash':'c'*64,'sqliteFilesEnumerated':True,'liveDatabaseOpened':False,'controlUnknownRows':[],'controlUnknownHash':s.digest([]),'controlUnknownCount':0,'nativeLedgerRegistration':{'directory':'/tmp/isolated-fixture/dispatcher','dev':1,'ino':1,'registryHash':'3'*64},'files':{n:{'sha256':'d'*64,'bytes':10,'mode':384,'dev':1,'ino':i+1} for i,n in enumerate(['dispatcher/state.json','database/project.sqlite','database/project.sqlite-wal'])}}
 def require(self,h,operation):
  s.need(self.authorized,'REAL_NATIVE_ADMISSION_REQUIRED');self.events.append(('require',operation))
 def capture_original(self):return copy.deepcopy(self.baseline)
 def fence(self,u,h,p,b):
  s.need(p==s.fence_path(u) and b==s.fence_bytes(h),'BAD_FENCE');self.fenced.add(u)
 def verify_all_fences(self,h):s.need(self.fenced==set(s.HOSTS),'FENCE_MISSING')
 def graceful_stop(self,u,h):
  s.need(u!=s.NATIVE,'NO_NEW_SHUTDOWN_OR_NATIVE_GRACEFUL_PATH');self.stopped.add(u)
  if self.fail=='graceful':raise s.Refused('GRACEFUL_FAILED')
 def graceful_native_once(self,t,deadline):self.events.append(('original-native-SIGTERM',12));return {'status':'REFUSED_OR_TIMEOUT'}
 def verify_original_native_or_exited(self,t):s.need(not self.drift,'PID_REUSE')
 def observe_native(self,t):
  self.verify_original_native_or_exited(t);return {'exited':s.NATIVE in self.stopped,'members':[12,13] if self.extra else [12]}
 def open_native_pidfd(self,t):self.events.append(('open-pidfd',12));return 1
 def freeze_native(self,t,h):self.frozen=True
 def verify_frozen_singleton(self,t,h):s.need(self.frozen and not self.extra,'NATIVE_NON_SINGLETON_REFUSED')
 def checkpoint_native(self):
  if self.fail=='checkpoint':self.c['noForeignWriters']=False
  return copy.deepcopy(self.c)
 def kill_native_pidfd_once(self,fd,t,deadline):
  self.kills+=1;self.stopped.add(s.NATIVE)
  if self.fail=='lost-kill-reply':raise OSError('uncertain syscall reply')
 def close_pidfd(self,fd):self.events.append(('close-pidfd',fd))
 def observe_all(self,baseline,h):
  return {u:{'unit':u,'host':host,'mainPid':0 if u in self.stopped else 12,'controlPid':0,'cgroupEmpty':u in self.stopped,'ownedPersistentFence':u in self.fenced,'pendingJob':False} for u,host in s.HOSTS.items()}
def plan(b):
 return {'schema':s.SCHEMA,'scope':s.SCOPE,'sourcePublicConfigHash':s.PUBLIC,'sourceDeliveryHash':s.DELIVERY,'grantHash':s.GRANT,'sourceNativeVersion':s.SOURCE_NATIVE,'targetReleaseId':s.TARGET_RELEASE,'targetNativeVersion':'e'*64,'targetInventoryHash':'f'*64,'codeFreezeHash':'1'*64,'originalBaselineHash':s.digest(b.baseline),'nativeTargetHash':s.digest(b.baseline[s.NATIVE]),'stopEpoch':'11111111-2222-4333-8444-555555555555','nonce':'a'*32,'approvedAt':1000,'expiresAt':301000,'recoveryDeadline':1801000,'allowNativeNonGracefulOnce':True,'acceptUnprovenInflight':True,'acceptPossibleUpstreamContinuation':True,'recoveryPolicy':'KEEP_CRASHED_NATIVE_STOPPED_NO_AUTOMATIC_BUSINESS_REOPEN','revisionPlanHash':'2'*64,'approvedControlUnknownHash':s.digest([]),'approvedControlUnknownCount':0}
class Tests(unittest.TestCase):
 def fixture(self,fault=lambda _:None):
  b=Backend();j=Journal();clock=[2000];d=s.Driver(b,j,lambda:clock[0],fault);return b,j,clock,d,plan(b)
 def test_same_plan_end_to_end_keeps_fences_and_true_original_baseline(self):
  b,j,t,d,p=self.fixture();out=d.run(p)
  self.assertEqual(out['status'],'STOPPED_FENCED_NOT_DRAINED');self.assertEqual(b.kills,1);self.assertEqual(b.fenced,set(s.HOSTS));self.assertEqual(j.read()['originalBaseline'],b.baseline);self.assertTrue(out['forceTerminationUsed']);self.assertEqual(out['globalExecution'],'UNPROVEN');self.assertFalse(out['roleStopReceipt']);self.assertEqual(out['nativeTargetHash'],p['nativeTargetHash'])
 def test_foreign_extra_child_refuses_without_kill(self):
  b,j,t,d,p=self.fixture();b.extra=True;self.assertEqual(d.run(p)['failureCode'],'NATIVE_NON_SINGLETON_REFUSED');self.assertEqual(b.kills,0)
 def test_foreign_writer_retains_protection(self):
  b,j,t,d,p=self.fixture();b.fail='checkpoint';self.assertEqual(d.run(p)['status'],'RECOVERY_REQUIRED_READBACK_ONLY');self.assertEqual(b.kills,0);self.assertTrue(b.frozen)
 def test_no_force_after_prerequisite_failure(self):
  b,j,t,d,p=self.fixture();b.fail='graceful';d.run(p);d.run(p);self.assertEqual(b.kills,0);self.assertTrue(j.read()['effects']['graceful:r16-app.service'])
 def test_lost_signal_reply_is_consumed_and_only_observed(self):
  b,j,t,d,p=self.fixture();b.fail='lost-kill-reply';a=d.run(p);self.assertTrue(a['signalAttemptConsumed']);out=d.run(p);self.assertEqual(out['status'],'STOPPED_FENCED_NOT_DRAINED');self.assertEqual(b.kills,1)
 def test_crash_after_intent_before_signal_never_replays(self):
  def crash(point):
   if point=='saved:native-signal':raise Crash()
  b,j,t,d,p=self.fixture(crash)
  with self.assertRaises(Crash):d.run(p)
  d.fault=lambda _:None;out=d.run(p);self.assertTrue(out['signalAttemptConsumed']);self.assertEqual(out['status'],'RECOVERY_REQUIRED_READBACK_ONLY');self.assertEqual(b.kills,0)
 def test_deadline_during_checkpoint_prevents_signal(self):
  b,j,t,d,p=self.fixture();old=b.checkpoint_native
  def capture():c=old();t[0]=p['expiresAt'];return c
  b.checkpoint_native=capture;out=d.run(p);self.assertEqual(out['failureCode'],'PLAN_EXPIRED');self.assertEqual(b.kills,0)
 def test_expired_observation_does_not_renew_or_install(self):
  b,j,t,d,p=self.fixture();d.run(p);t[0]=p['expiresAt']+1;out=d.run(p);self.assertLessEqual(out['expiresAt'],p['recoveryDeadline']);self.assertGreater(out['expiresAt'],t[0]);self.assertEqual(j.read()['planHash'],s.digest(p));self.assertEqual(b.kills,1)
 def test_checkpoint_drift_after_consumed_signal_refuses(self):
  b,j,t,d,p=self.fixture();d.run(p);b.c['files']['dispatcher/state.json']['sha256']='a'*64;out=d.run(p);self.assertEqual(out['status'],'RECOVERY_REQUIRED_READBACK_ONLY');self.assertEqual(b.kills,1)
 def test_fence_survives_runtime_reopen_has_no_start_token(self):
  raw=s.fence_bytes('a'*64).decode();self.assertTrue(s.fence_path(s.NATIVE).startswith('/etc/'));self.assertIn('/var/lib/',raw);self.assertIn('RefuseManualStart=yes',raw);self.assertIn('Restart=no',raw);self.assertIn('SendSIGKILL=no',raw)
 def test_replaced_pid_refuses_without_signal(self):
  b,j,t,d,p=self.fixture();b.drift=True;out=d.run(p);self.assertEqual(out['failureCode'],'PID_REUSE');self.assertEqual(b.kills,0)
 def test_public_boolean_cannot_replace_native_admission(self):
  b,j,t,d,p=self.fixture();b.authorized=False
  with self.assertRaisesRegex(s.Refused,'REAL_NATIVE_ADMISSION_REQUIRED'):d.run(p)
  self.assertIsNone(j.read())
 def test_rejects_old_scope_risk_window_or_same_native_identity(self):
  for field,value in [('scope','ONE_TIME_CONTROLLED_CRASH_STOP_SOURCE_APP'),('acceptUnprovenInflight',False),('targetNativeVersion',s.SOURCE_NATIVE),('recoveryDeadline',1801001)]:
   b,j,t,d,p=self.fixture();p[field]=value
   with self.assertRaises(s.Refused):d.run(p)
 def test_exact_approved_control_uncertainty_is_preserved_not_settled(self):
  b,j,t,d,p=self.fixture();rows=[{'id':'old-uncertain-control','hash':'a'*64,'status':'UNKNOWN'}];b.c.update(controlUnknownRows=rows,controlUnknownCount=1,controlUnknownHash=s.digest(rows));p.update(approvedControlUnknownCount=1,approvedControlUnknownHash=s.digest(rows))
  out=d.run(p);self.assertEqual(out['controlUnknownCount'],1);self.assertEqual(b.c['controlUnknownRows'],rows);self.assertEqual(out['globalExecution'],'UNPROVEN')
 def test_9611_unapproved_control_records_refuse_before_kill(self):
  b,j,t,d,p=self.fixture();rows=[{'id':'fixture-'+str(i),'hash':'a'*64,'status':'UNKNOWN'}for i in range(9611)];b.c.update(controlUnknownRows=rows,controlUnknownCount=len(rows),controlUnknownHash=s.digest(sorted(rows,key=lambda x:x['id'])))
  out=d.run(p);self.assertEqual(out['failureCode'],'UNAPPROVED_CONTROL_UNCERTAINTY');self.assertEqual(b.kills,0)
 def test_corrupt_resume_baseline_checkpoint_or_signal_fails_closed(self):
  for field in ['originalBaseline','checkpoint','signalAttemptConsumed']:
   b,j,t,d,p=self.fixture();d.run(p)
   if field=='originalBaseline':j.value[field][s.NATIVE]['pid']=12345
   elif field=='checkpoint':j.value[field]['files']['dispatcher/state.json']['sha256']='a'*64
   else:j.value[field]=False
   with self.assertRaises(s.Refused):d.run(p)
   self.assertEqual(b.kills,1)
 def test_native_graceful_lost_reply_never_reissues_or_forces(self):
  b,j,t,d,p=self.fixture();attempts=[]
  def uncertain(target,deadline):attempts.append(1);raise OSError('lost response')
  b.graceful_native_once=uncertain;d.run(p);d.run(p);self.assertEqual(len(attempts),1);self.assertEqual(b.kills,0)
 def test_unknown_and_inflight_are_not_sanitized(self):
  for field in ['newUnknown','inflight']:
   b,j,t,d,p=self.fixture();b.c[field]=['new-work'];out=d.run(p);self.assertEqual(out['status'],'RECOVERY_REQUIRED_READBACK_ONLY');self.assertEqual(b.kills,0);self.assertEqual(b.c[field],['new-work'])
if __name__=='__main__':unittest.main()
