import copy
import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

HERE=Path(__file__).parent
spec=importlib.util.spec_from_file_location('linux_backend_r8_tested',HERE/'linux_backend.py');m=importlib.util.module_from_spec(spec);sys.modules[spec.name]=m;spec.loader.exec_module(m)

class FakeAdmission:
 def __init__(self,target):self.target_hash=m.digest(target);self.approval_hash='a'*64;self.calls=[];self.refused=None
 def require(self,operation,target):
  self.calls.append(operation)
  m.need(operation!=self.refused,'NATIVE_ADMISSION_REFUSED')
  if target is not None:m.need(m.digest(target)==self.target_hash,'CAP_TARGET_DRIFT')
class FakeCheckpoint:
 def __init__(self):self.calls=[]
 def capture(self,target):self.calls.append(copy.deepcopy(target));return {'syntheticCheckpointOnly':True}
class FakeSystem:
 isolated=True
 def __init__(self,paths,target,sources):
  self.owner_uid=os.geteuid();self.paths=paths;self.target=target;self.sources=sources;self.commands=[];self.signals=[];self.closed=[];self.fd=100;self.live=True;self.extra=[];self.frozen=False;self.time=1000000;self.monotime=0;self.root=True;self.host=m.HOST;self.freeze_delay=0;self.freeze_requested=False;self.never_freeze=False;self.never_thaw=False;self.conditions_override=None;self.fail_reload=False;self.fail_signal=False;self.sources_drift=False;self.missing_events=False;self.missing_group=False;self.freezer_writes=[];self.lost_freeze_reply=False;self.manager_exit_delay=0;self.proc_start=target['startTicks'];self.argv=m.ARGV;self.control_group=m.CGROUP
  self.props={name:'' for name in m.PROPERTIES};self.props.update(Id=m.UNIT,LoadState='loaded',ActiveState='active',SubState='running',MainPID=str(target['pid']),ControlPID='0',ControlGroup=m.CGROUP,InvocationID=target['invocationId'],NRestarts=str(target['nRestarts']),Restart='no',RefuseManualStart='no',DropInPaths='',NeedDaemonReload='no',SendSIGKILL='no',KillSignal='15',LimitCORE='0')
 def require_root(self):m.need(self.root and self.host==m.HOST,'FIXED_CLOUD_ROOT_REQUIRED')
 def now(self):return self.time
 def monotonic(self):return self.monotime
 def sleep(self,seconds):self.monotime+=seconds
 def run(self,argv):
  self.commands.append(tuple(argv))
  if argv[:3]==('/usr/bin/systemctl','show',m.UNIT):
   if not self.live and self.manager_exit_delay:
    self.manager_exit_delay-=1
    if self.manager_exit_delay==0:self.props.update(MainPID='0',ActiveState='failed',SubState='failed')
   return ''.join(k+'='+self.props[k]+'\n' for k in m.PROPERTIES).encode()
  if argv[0]=='/usr/bin/busctl':
   data=self.conditions_override if self.conditions_override is not None else [['ConditionPathExists',False,False,str(self.paths.condition),0]]
   return m.canonical({'type':'a(sbbsi)','data':data})
  if argv==('/usr/bin/systemctl','daemon-reload'):
   if self.fail_reload:raise m.Refused('FIXED_MANAGER_COMMAND_FAILED')
   self.props.update(Restart='no',RefuseManualStart='yes' if self.paths.fence.exists() else 'no',DropInPaths=str(self.paths.fence) if self.paths.fence.exists() else '',NeedDaemonReload='no');return b''
  if argv==('/usr/bin/systemctl','freeze',m.UNIT):self.freeze_requested=True;return b''
  if argv==('/usr/bin/systemctl','thaw',m.UNIT):
   if not self.never_thaw:self.frozen=False;self.freeze_requested=False
   return b''
  raise AssertionError('UNREVIEWED_REAL_COMMAND '+repr(argv))
 def source_read(self,path):return b'drift' if self.sources_drift else self.sources[str(path)]
 def kernel_read(self,path,maximum=65536):
  t=self.target
  if path=='/proc/sys/kernel/random/boot_id':return (t['bootId']+'\n').encode()
  if path.endswith('/cgroup.procs'):
   if self.missing_group:raise FileNotFoundError()
   return ('\n'.join(map(str,([t['pid']] if self.live else [])+self.extra))+'\n').encode()
  if path.endswith('/cgroup.freeze'):
   if self.missing_group:raise FileNotFoundError()
   return b'1\n' if self.freeze_requested else b'0\n'
  if path.endswith('/cgroup.events'):
   if self.missing_events or self.missing_group:raise FileNotFoundError()
   if self.freeze_requested and not self.never_freeze:
    if self.freeze_delay:self.freeze_delay-=1
    else:self.frozen=True
   return ('populated '+('1' if self.live else '0')+'\nfrozen '+('1' if self.frozen else '0')+'\n').encode()
  if path=='/proc/'+str(t['pid'])+'/stat':
   if not self.live:raise FileNotFoundError()
   return (str(t['pid'])+' (node) '+' '.join(['S']+['0']*18+[self.proc_start]+['0']*10)).encode()
  if path=='/proc/'+str(t['pid'])+'/cgroup':return ('0::'+self.control_group+'\n').encode()
  if path=='/proc/'+str(t['pid'])+'/cmdline':return b'\0'.join(x.encode() for x in self.argv)+b'\0'
  raise AssertionError('ARBITRARY_KERNEL_PATH '+path)
 def freezer_write(self,value):
  assert value in (b'0',b'1');self.freezer_writes.append(value)
  if value==b'1':
   self.freeze_requested=True
   if self.lost_freeze_reply:raise m.Refused('FREEZER_WRITE_UNCERTAIN')
  else:
   self.freeze_requested=False
   if not self.never_thaw:self.frozen=False
 def pidfd_open(self,pid):assert pid==self.target['pid'];self.fd+=1;return self.fd
 def pidfd_ready(self,fd):return not self.live
 def pidfd_close(self,fd):self.closed.append(fd)
 def pidfd_signal(self,fd):
  self.signals.append(fd)
  if self.fail_signal:raise m.Refused('UNKNOWN_SIGNAL_RETURN')
  self.live=False;self.frozen=False;self.freeze_requested=False
  if not self.manager_exit_delay:self.props.update(MainPID='0',ActiveState='failed',SubState='failed')

class Tests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory(prefix='.r8-linux-test-',dir=Path.home());self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name);self.root.chmod(0o700)
  self.paths=m.Paths(self.root/'state',self.root/'runtime/systemd/r16-app.service.d/92-r16-first-stop-r8.conf',self.root/'runtime/guard/source-app-start-not-authorized')
  self.sources={str(m.SOURCE/name):('synthetic-public-source-'+name).encode() for name in m.SOURCE_HASHES};self.sources[str(m.LAUNCHER)]=b'synthetic-trusted-launcher'
  self.pins={name:m.sha(self.sources[str(m.SOURCE/name)]) for name in m.SOURCE_HASHES}
  patch=mock.patch.object(m,'SOURCE_HASHES',self.pins);patch.start();self.addCleanup(patch.stop)
  patch=mock.patch.object(m,'LAUNCHER_SHA',m.sha(self.sources[str(m.LAUNCHER)]));patch.start();self.addCleanup(patch.stop)
  self.target={'unit':m.UNIT,'host':m.HOST,'bootId':'00000000-1111-2222-3333-444444444444','pid':1234,'startTicks':'555','invocationId':'b'*32,'nRestarts':0,'cgroup':m.CGROUP,'sourceHashes':self.pins}
  self.cap=FakeAdmission(self.target);self.system=FakeSystem(self.paths,self.target,self.sources);self.checkpointer=FakeCheckpoint();self.backend=m.LinuxBackend(self.cap,self.checkpointer,system=self.system,paths=self.paths);self.owner=self.cap.approval_hash
 def ready(self):self.backend.fence(self.target,self.owner);self.backend.freeze(self.target,self.owner)
 def test_full_fixed_fence_frozen_pidfd_exit_and_checkpoint(self):
  handle=self.backend.open_pidfd(self.target);self.system.freeze_delay=2;self.ready();self.assertGreater(self.system.monotime,0)
  self.assertTrue(self.backend.inspect(self.target)['frozen']);self.assertEqual(self.backend.checkpoint(self.target),{'syntheticCheckpointOnly':True})
  self.backend.send_pidfd_sigkill(handle,self.system.time+1000);row=self.backend.inspect(self.target)
  self.assertTrue(row['processExited']);self.assertEqual(row['members'],[]);self.assertEqual(row['fenceOwner'],self.owner);self.assertEqual(self.system.signals,[handle]);self.backend.close_pidfd(handle);self.assertEqual(self.system.closed,[handle])
  self.assertFalse(any('stop' in c or 'kill' in c or 'start' in c for c in self.system.commands))
 def test_capability_and_exact_approval_hash_are_required(self):
  with self.assertRaises(m.Refused):m.LinuxBackend(True,self.checkpointer,system=self.system,paths=self.paths)
  approval={'target':self.target};self.cap.approval_hash=m.digest(approval);self.assertTrue(self.backend.assert_admitted(approval))
  with self.assertRaisesRegex(m.Refused,'NATIVE_APPROVAL_HASH_DRIFT'):self.backend.assert_admitted({**approval,'changed':True})
  self.cap.refused='fence'
  with self.assertRaises(m.Refused):self.backend.fence(self.target,self.cap.approval_hash)
  self.assertEqual(self.system.commands,[])
 def test_real_system_does_not_allow_test_path_override(self):
  with self.assertRaisesRegex(m.Refused,'PRODUCTION_PATH_OVERRIDE_REFUSED'):m.LinuxBackend(self.cap,self.checkpointer,paths=self.paths)
 def test_root_and_hostname_are_required_before_any_fixed_command(self):
  for field,value in [('root',False),('host','other')]:
   setattr(self.system,field,value)
   with self.assertRaises(m.Refused):self.backend.inspect(self.target)
   self.assertEqual(self.system.commands,[]);setattr(self.system,field,True if field=='root' else m.HOST)
 def test_boot_invocation_restart_and_source_drift_are_rejected(self):
  for prop,value in [('InvocationID','c'*32),('NRestarts','1'),('ControlGroup','/wrong'),('SendSIGKILL','yes'),('KillSignal','9'),('LimitCORE','1'),('ControlPID','777')]:
   with self.subTest(prop=prop):
    original=self.system.props[prop];self.system.props[prop]=value
    with self.assertRaises(m.Refused):self.backend.inspect(self.target)
    self.system.props[prop]=original
  self.system.sources_drift=True
  with self.assertRaisesRegex(m.Refused,'ORIGINAL_SOURCE_DRIFT'):self.backend.inspect(self.target)
 def test_members_start_argv_and_process_cgroup_are_independent_guards(self):
  for attr,value in [('extra',[777]),('proc_start','999'),('argv',('/usr/bin/node','injected')),('control_group','/other')]:
   with self.subTest(attr=attr):
    old=getattr(self.system,attr);setattr(self.system,attr,value)
    with self.assertRaises(m.Refused):self.backend.inspect(self.target)
    setattr(self.system,attr,old)
 def test_partial_missing_cgroup_metadata_is_never_empty_evidence(self):
  self.system.missing_events=True
  with self.assertRaisesRegex(m.Refused,'CGROUP_METADATA_PARTLY_MISSING'):self.backend.inspect(self.target)
 def test_foreign_runtime_dropin_and_guard_file_are_not_overwritten(self):
  self.backend.files.directory(self.paths.fence.parent,mode=0o755,create=True);self.paths.fence.write_bytes(b'foreign');self.paths.fence.chmod(0o644)
  with self.assertRaises(m.Refused):self.backend.fence(self.target,self.owner)
  self.assertEqual(self.paths.fence.read_bytes(),b'foreign')
  self.paths.fence.unlink();self.backend.files.directory(self.paths.condition.parent,create=True);self.paths.condition.touch();self.paths.condition.chmod(0o600)
  with self.assertRaises(m.Refused):self.backend.fence(self.target,self.owner)
  self.assertFalse(self.paths.fence.exists())
 def test_condition_uses_actual_typed_busctl_and_never_historical_result(self):
  for data in ([],[['ConditionPathExists',True,False,str(self.paths.condition),1]],[['ConditionPathExists',False,True,str(self.paths.condition),0]],[['ConditionPathExists',False,False,'/foreign',0]]):
   with self.subTest(data=data):
    self.system.conditions_override=data
    with self.assertRaises(m.Refused):self.backend.fence(self.target,self.owner)
  self.system.conditions_override=[['ConditionPathExists',False,False,str(self.paths.condition),1]];self.backend.fence(self.target,self.owner)
  self.assertEqual(self.backend.inspect(self.target)['fenceOwner'],self.owner)
 def test_owned_fence_daemon_reload_failure_can_recover_without_foreign_overwrite(self):
  self.system.fail_reload=True
  with self.assertRaises(m.Refused):self.backend.fence(self.target,self.owner)
  raw=self.paths.fence.read_bytes();self.system.fail_reload=False;self.backend.fence(self.target,self.owner);self.assertEqual(self.paths.fence.read_bytes(),raw)
 def test_freeze_waits_actual_frozen_and_timeout_never_signals(self):
  self.backend.fence(self.target,self.owner);self.system.never_freeze=True
  with self.assertRaisesRegex(m.Refused,'FREEZE_NOT_CONFIRMED'):self.backend.freeze(self.target,self.owner)
  self.assertEqual(self.system.signals,[]);self.assertGreaterEqual(self.system.monotime,10)
 def test_foreign_freeze_or_owner_metadata_is_rejected(self):
  self.backend.fence(self.target,self.owner);self.system.frozen=True;self.system.freeze_requested=True
  with self.assertRaisesRegex(m.Refused,'FOREIGN_FREEZE'):self.backend.inspect(self.target)
 def test_checkpoint_delegates_no_arbitrary_path_and_requires_freeze_or_exit(self):
  with self.assertRaisesRegex(m.Refused,'FROZEN_CHECKPOINT_REQUIRED'):self.backend.checkpoint(self.target)
  self.assertEqual(self.checkpointer.calls,[]);self.ready();self.backend.checkpoint(self.target);self.assertEqual(self.checkpointer.calls,[self.target])
 def test_unknown_signal_exception_consumes_pidfd_attempt(self):
  handle=self.backend.open_pidfd(self.target);self.ready();self.system.fail_signal=True
  with self.assertRaisesRegex(m.Refused,'UNKNOWN_SIGNAL_RETURN'):self.backend.send_pidfd_sigkill(handle,self.system.time+1000)
  with self.assertRaisesRegex(m.Refused,'PIDFD_ATTEMPT_ALREADY_CONSUMED'):self.backend.send_pidfd_sigkill(handle,self.system.time+1000)
  self.assertEqual(self.system.signals,[handle]);self.assertTrue(self.system.frozen)
 def test_deadline_and_admission_refusal_never_signal(self):
  handle=self.backend.open_pidfd(self.target);self.ready()
  with self.assertRaisesRegex(m.Refused,'SIGNAL_DEADLINE_EXPIRED'):self.backend.send_pidfd_sigkill(handle,self.system.time)
  self.cap.refused='signal'
  with self.assertRaises(m.Refused):self.backend.send_pidfd_sigkill(handle,self.system.time+1000)
  self.assertEqual(self.system.signals,[])
 def test_pid_or_membership_race_before_open_and_signal_never_uses_numeric_pid(self):
  handle=self.backend.open_pidfd(self.target);self.ready();self.system.extra=[777]
  with self.assertRaises(m.Refused):self.backend.send_pidfd_sigkill(handle,self.system.time+1000)
  self.assertEqual(self.system.signals,[])
 def test_owned_abort_thaws_then_unfences_without_start(self):
  self.ready();self.backend.unfreeze(self.target,self.owner);self.backend.unfence(self.target,self.owner)
  row=self.backend.inspect(self.target);self.assertFalse(row['frozen']);self.assertIsNone(row['fenceOwner']);self.assertTrue(self.system.live);self.assertFalse(any('start' in c for c in self.system.commands))
 def test_frozen_or_foreign_policy_cannot_be_unfenced(self):
  self.ready()
  with self.assertRaises(m.Refused):self.backend.unfence(self.target,self.owner)
  self.backend.unfreeze(self.target,self.owner);self.paths.fence.write_bytes(b'foreign')
  with self.assertRaises(m.Refused):self.backend.unfence(self.target,self.owner)
  self.assertEqual(self.paths.fence.read_bytes(),b'foreign')
 def test_unfence_stopped_target_leaves_other_successor_dropin_untouched(self):
  handle=self.backend.open_pidfd(self.target);self.ready();self.backend.send_pidfd_sigkill(handle,self.system.time+1000)
  successor=self.paths.fence.parent/'93-successor.conf';successor.write_bytes(b'successor-only');successor.chmod(0o644)
  self.backend.unfence(self.target,self.owner);self.assertEqual(successor.read_bytes(),b'successor-only');self.assertEqual(self.system.signals,[handle])
 def test_pidfd_exit_waits_for_manager_and_empty_cgroup_bounded(self):
  handle=self.backend.open_pidfd(self.target);self.ready();self.system.manager_exit_delay=4
  self.backend.send_pidfd_sigkill(handle,self.system.time+1000);self.assertGreater(self.system.monotime,0);self.assertTrue(self.backend.inspect(self.target)['processExited']);self.assertEqual(self.system.signals,[handle])
 def test_exit_readback_timeout_never_repeats_or_removes_fence(self):
  handle=self.backend.open_pidfd(self.target);self.ready();self.system.manager_exit_delay=10000
  with self.assertRaisesRegex(m.Refused,'EXIT_NOT_CONFIRMED'):self.backend.send_pidfd_sigkill(handle,self.system.time+1000)
  with self.assertRaisesRegex(m.Refused,'PIDFD_ATTEMPT_ALREADY_CONSUMED'):self.backend.send_pidfd_sigkill(handle,self.system.time+1000)
  self.assertTrue(self.paths.fence.exists());self.assertEqual(self.system.signals,[handle])
 def test_exited_empty_frozen_cgroup_thaw_requires_distinct_bound_native_scope(self):
  handle=self.backend.open_pidfd(self.target);self.ready();self.backend.send_pidfd_sigkill(handle,self.system.time+1000);self.system.frozen=True;self.system.freeze_requested=True
  with self.assertRaisesRegex(m.Refused,'EXITED_THAW_NATIVE_SCOPE_REQUIRED'):self.backend.unfreeze(self.target,self.owner)
  self.cap.handoff_approved={'successorPlanHash':'f'*64,'stopApprovalHash':self.owner,'targetHash':self.cap.target_hash}
  self.backend.unfreeze(self.target,self.owner);self.assertFalse(self.backend.inspect(self.target)['frozen']);self.assertIn('unfreeze-exited',self.cap.calls)
 def test_requested_freeze_transition_refuses_public_inspect_and_auto_unfence(self):
  self.backend.fence(self.target,self.owner);self.system.never_freeze=True
  with self.assertRaisesRegex(m.Refused,'FREEZE_NOT_CONFIRMED'):self.backend.freeze(self.target,self.owner)
  with self.assertRaisesRegex(m.Refused,'FREEZER_TRANSITION_UNPROVEN'):self.backend.inspect(self.target)
  with self.assertRaises(m.Refused):self.backend.unfence(self.target,self.owner)
  with self.assertRaisesRegex(m.Refused,'TRANSITION_THAW_NATIVE_SCOPE_REQUIRED'):self.backend.unfreeze(self.target,self.owner)
  self.cap.recovery_approved={'recoveryHash':'f'*64,'stopApprovalHash':self.owner,'targetHash':self.cap.target_hash}
  self.backend.unfreeze(self.target,self.owner);self.backend.unfence(self.target,self.owner)
  self.assertEqual(self.system.freezer_writes,[b'1',b'0']);self.assertFalse(self.system.frozen)
 def test_freezer_write_lost_reply_has_no_late_dbus_effect_or_automatic_unfence(self):
  self.backend.fence(self.target,self.owner);self.system.never_freeze=True;self.system.lost_freeze_reply=True
  with self.assertRaisesRegex(m.Refused,'FREEZER_WRITE_UNCERTAIN'):self.backend.freeze(self.target,self.owner)
  with self.assertRaisesRegex(m.Refused,'FREEZER_TRANSITION_UNPROVEN'):self.backend.inspect(self.target)
  self.assertTrue(self.paths.fence.exists());self.assertEqual(self.system.freezer_writes,[b'1'])
  self.assertFalse(any('freeze' in command or 'thaw' in command for command in self.system.commands))
 def journal(self):return m.RootJournal(self.cap,system=self.system,paths=self.paths)
 def record(self,phase='BOUND',consumed=False):return {'schema':'r16.controlled-crash-stop-journal.v1','approvalHash':self.owner,'targetHash':self.cap.target_hash,'phase':phase,'signalAttemptConsumed':consumed,'checkpoint':{'synthetic':'checkpoint'},'checkpointDigest':'f'*64}
 def test_journal_lock_required_and_exclusive_across_instances(self):
  j=self.journal()
  with self.assertRaisesRegex(m.Refused,'JOURNAL_LOCK_REQUIRED'):j.read()
  with j.locked():
   with self.assertRaisesRegex(m.Refused,'JOURNAL_BUSY'):
    with self.journal().locked():pass
   j.write(self.record());self.assertEqual(j.read(),self.record());self.assertEqual(self.paths.state.stat().st_mode&0o7777,0o700);self.assertEqual((self.paths.state/'transaction.json').stat().st_mode&0o7777,0o600)
 def test_journal_consumed_intent_and_checkpoint_cannot_reset_or_change_approval(self):
  j=self.journal()
  with j.locked():
   r=self.record('SIGNAL_INTENT',True);j.write(r)
   for changed in (self.record(),{**r,'checkpoint':{}},{**r,'approvalHash':'b'*64}):
    with self.assertRaises(m.Refused):j.write(changed)
   self.assertEqual(j.read(),r);done={**r,'phase':'TERMINAL','receipt':{'status':'done'}};j.write(done)
   with self.assertRaises(m.Refused):j.write({**done,'extra':True})
 def test_journal_symlink_hardlink_or_writable_file_refuses(self):
  j=self.journal()
  with j.locked():
   j.write(self.record());path=self.paths.state/'transaction.json';path.chmod(0o644)
   with self.assertRaises(m.Refused):j.read()
   path.chmod(0o600);link=self.paths.state/'link';os.link(path,link)
   with self.assertRaises(m.Refused):j.read()
   link.unlink();path.unlink();path.symlink_to(self.root/'unrelated')
   with self.assertRaises(OSError):j.write(self.record())
 def test_atomic_known_partial_prefix_repairs_but_foreign_prefix_and_modes_refuse(self):
  files=self.backend.files;path=self.root/'private'/'immutable.json';raw=b'{"bound":"own bytes"}';files.directory(path.parent,create=True)
  pending=path.with_name('.'+path.name+'.'+m.sha(raw)+'.pending');pending.write_bytes(raw[:5]);pending.chmod(0o600);files.atomic(path,raw,immutable=True);self.assertEqual(path.read_bytes(),raw);self.assertFalse(pending.exists())
  other=path.with_name('other.json');tmp=other.with_name('.other.json.'+m.sha(raw)+'.pending');tmp.write_bytes(b'foreign');tmp.chmod(0o600)
  with self.assertRaises(m.Refused):files.atomic(other,raw,immutable=True)
  self.assertFalse(other.exists());self.assertEqual(tmp.read_bytes(),b'foreign')
 def test_existing_public_state_directory_and_duplicate_root_journal_refuse(self):
  self.paths.state.mkdir(mode=0o755)
  with self.assertRaisesRegex(m.Refused,'STATE_DIRECTORY_MODE_REFUSED'):self.backend.inspect(self.target)
  self.paths.state.chmod(0o700);j=self.journal()
  with j.locked():
   path=self.paths.state/'transaction.json';path.write_bytes(b'{"signalAttemptConsumed":true,"signalAttemptConsumed":false}');path.chmod(0o600)
   with self.assertRaisesRegex(m.Refused,'DUPLICATE_ROOT_JSON_KEY'):j.read()
 def test_fifo_root_metadata_refuses_without_blocking(self):
  self.paths.state.mkdir(mode=0o700);path=self.paths.state/'fence-owner.json';os.mkfifo(path,0o600)
  with self.assertRaises(m.Refused):self.backend.inspect(self.target)
 def test_root_parent_symlink_and_writable_directory_refused(self):
  unsafe=self.root/'unsafe';unsafe.mkdir();unsafe.chmod(0o775)
  with self.assertRaises(m.Refused):self.backend.files.directory(unsafe)
  link=self.root/'link';link.symlink_to(unsafe,target_is_directory=True)
  with self.assertRaises(m.Refused):self.backend.files.directory(link)

if __name__=='__main__':unittest.main()
