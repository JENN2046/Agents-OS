"""Independent Linux boundary tests: private files and synthetic kernel/manager.

No sudo, SSH, systemd, real cgroup, native keys or production paths are used.
The actual file atomics and flock are exercised under the ordinary user's home.
"""
import copy
import importlib.util
import json
import os
from pathlib import Path
import signal
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

HERE = Path(__file__).parent
spec = importlib.util.spec_from_file_location('independent_linux_backend', HERE/'linux_backend.py')
b = importlib.util.module_from_spec(spec)
import sys
sys.modules[spec.name] = b
spec.loader.exec_module(b)
HASH = 'a'*64


class Capability:
    def __init__(self, system):
        self.system = system
        self.calls = []
        self.plan_hash = HASH
        self.plan = {'targetNativeVersion': 'b'*64}
        self.original_baseline = {}
        self.expires = 100000

    def require(self, h, op, target=None):
        self.calls.append((h, op, target))
        b.need(h in (None, HASH), 'TEST_PLAN_DRIFT')
        if op not in ('inspect', 'journal-read'):
            b.need(self.system.now() < self.expires, 'TEST_WINDOW_EXPIRED')
        return None


class System:
    isolated = True
    owner_uid = os.getuid()

    def __init__(self, paths):
        self.paths = paths
        self.clock = 1000
        self.mono = 1.0
        self.calls = []
        self.closed = []
        self.signals = []
        self.pidfd = 81
        self.ready = False
        self.requested = False
        self.frozen = False
        self.freeze_completes = True
        self.term_exits = False
        self.kill_lost_reply = False
        self.on_open = None
        self.stat_reads = 0
        self.stat_drift = False
        self.extra_members = []
        self.proc_group = '/system.slice/'+b.NATIVE
        self.proc_start = '100'
        self.proc_alive = True
        self.uid = 1000
        self.argv = b.ARGV[b.NATIVE]
        self.exe_reads = 0
        self.exe_drift = False
        self.props = {k: '' for k in b.PROPS}
        self.props.update(Id=b.NATIVE, LoadState='loaded', ActiveState='active',
                          SubState='running', MainPID='123', ControlPID='0',
                          ControlGroup='/system.slice/'+b.NATIVE,
                          InvocationID='1'*32, NRestarts='0', Restart='on-failure',
                          RefuseManualStart='no', NeedDaemonReload='no',
                          SendSIGKILL='no', KillSignal='15', LimitCORE='0', User='jenn')

    def require_root(self, host):
        b.need(host in (b.LOCAL, b.CLOUD), 'TEST_HOST')

    def user_uid(self, name):
        b.need(name == 'fixture-user', 'TEST_UNEXPECTED_USER')
        return 1001

    def process_exe(self, pid, executable):
        self.exe_reads += 1
        inode = 900 if self.exe_drift and self.exe_reads > 1 else 800
        return (executable, (1, inode, 0, 0, 0o100755, 1, 100, 1, 1))

    def now(self): return self.clock
    def monotonic(self): return self.mono
    def sleep(self, seconds):
        self.mono += seconds
        self.clock += int(seconds*1000)

    def run(self, argv):
        argv = tuple(argv)
        self.calls.append(argv)
        if argv[:2] == ('/usr/bin/systemctl', 'show'):
            p = dict(self.props)
            p['Id'] = argv[2]
            fence = self.paths.fence(argv[2])
            if fence.exists():
                p.update(Restart='no', RefuseManualStart='yes', DropInPaths=str(fence))
            return ''.join(k+'='+p[k]+'\n' for k in b.PROPS).encode()
        if argv[0] == '/usr/bin/busctl':
            return json.dumps({'type':'a(sbbsi)', 'data':[
                ['ConditionPathExists', False, False, str(self.paths.condition), 0]]}).encode()
        if argv == ('/usr/bin/systemctl', 'daemon-reload'):
            return b''
        raise AssertionError('No real command adapter: '+repr(argv))

    def kernel(self, path, maximum=262144):
        if path == '/proc/sys/kernel/random/boot_id':
            return b'11111111-2222-4333-8444-555555555555\n'
        if path.endswith('/cgroup.freeze'):
            return b'1\n' if self.requested else b'0\n'
        if path.endswith('/cgroup.events'):
            return b'populated 1\nfrozen '+(b'1\n' if self.frozen else b'0\n')
        if path.startswith('/proc/123/'):
            if not self.proc_alive: raise FileNotFoundError(path)
            if path.endswith('/stat'):
                self.stat_reads += 1
                start = '999' if self.stat_drift and self.stat_reads > 1 else self.proc_start
                return ('123 (fixture) '+' '.join(['S']+['0']*18+[start]+['0']*3)).encode()
            if path.endswith('/cgroup'): return ('0::'+self.proc_group+'\n').encode()
            if path.endswith('/cmdline'): return b'\0'.join(x.encode() for x in self.argv)+b'\0'
            if path.endswith('/status'): return ('Uid:\t'+'\t'.join([str(self.uid)]*4)+'\n').encode()
        raise AssertionError('No real kernel adapter: '+path)

    def group_members(self, unit):
        return ([int(self.props['MainPID'])] if self.props['MainPID'] != '0' else [])+self.extra_members

    def freezer(self, value):
        self.calls.append(('freezer', value))
        self.requested = value == b'1'
        self.frozen = self.requested and self.freeze_completes

    def pidfd_open(self, pid):
        assert pid == 123
        if self.on_open: self.on_open()
        return self.pidfd

    def pidfd_ready(self, fd): return self.ready
    def pidfd_close(self, fd): self.closed.append(fd)

    def pidfd_signal(self, fd, sig):
        self.signals.append((fd, sig))
        if sig == signal.SIGTERM and not self.term_exits: return
        self.ready = True
        self.props.update(MainPID='0', ActiveState='inactive', SubState='dead')
        self.proc_alive = False
        if self.kill_lost_reply and sig == signal.SIGKILL:
            raise OSError('isolated lost syscall reply')


class Tests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='source19-linux-isolated-', dir=Path.home())
        self.addCleanup(self.tmp.cleanup)
        root = Path(self.tmp.name)
        self.paths = b.Paths(state=root/'state', etc=root/'etc', condition=root/'state/never')
        self.system = System(self.paths)
        self.cap = Capability(self.system)
        self.backend = b.FixedLinuxBackend(self.cap, system=self.system, paths=self.paths, host=b.LOCAL)
        # This suite isolates OS/process and file boundaries. No unverified disk
        # source is accepted by production; its separate full-byte suite covers pins.
        self.backend._code = lambda unit, phase='SOURCE': ({'fixture-code':'c'*64}, b.S.SOURCE_NATIVE, 'd'*64)
        self.backend._active_hash = HASH

    def target(self):
        return self.backend.snapshot(b.NATIVE, HASH)

    def fence(self):
        self.backend.fence(b.NATIVE, HASH, b.S.fence_path(b.NATIVE), b.S.fence_bytes(HASH))

    def test_no_dictionary_capability_or_production_system_override(self):
        self.assertRaises(Exception, b.FixedLinuxBackend, {})
        class NotIsolated(System): isolated = False
        self.assertRaisesRegex(Exception, 'ISOLATED_SYSTEM_REQUIRED', b.FixedLinuxBackend,
                               self.cap, system=NotIsolated(self.paths), paths=self.paths)
        self.assertFalse(self.paths.state.exists())

    def test_snapshot_binds_uid_argv_cgroup_and_two_proc_reads(self):
        target = self.target()
        self.assertEqual(target['startTicks'], '100')
        self.assertGreaterEqual(self.system.stat_reads, 2)
        self.system.uid = 0
        self.assertRaisesRegex(Exception, 'ROLE_UID_DRIFT', self.target)

    def test_argv_and_same_manager_pid_with_start_ticks_drift_refuse(self):
        self.system.argv = ('/bin/sh',)
        self.assertRaisesRegex(Exception, 'ROLE_ARGV_DRIFT', self.target)
        self.system.argv = b.ARGV[b.NATIVE]
        self.system.stat_reads = 0
        self.system.stat_drift = True
        self.assertRaisesRegex(Exception, 'PROCESS_INSTANCE_CHANGED', self.target)

    def test_same_argv_but_different_executable_inode_is_not_same_instance(self):
        self.system.exe_drift = True
        self.assertRaisesRegex(Exception, 'PROCESS_INSTANCE_CHANGED', self.target)
        self.assertEqual(self.system.signals, [])

    def test_real_executable_reader_binds_proc_inode_to_root_safe_named_binary(self):
        named = SimpleNamespace(st_dev=1, st_ino=10, st_uid=0, st_gid=0,
                                st_mode=0o100755, st_nlink=1, st_size=42,
                                st_mtime_ns=1, st_ctime_ns=1)
        parent = SimpleNamespace(st_mode=0o40755, st_uid=0)
        actual = SimpleNamespace(st_dev=1, st_ino=11)
        def lstat(path):
            return named if str(path) == '/usr/bin/node' else parent
        with patch.object(b.os.path, 'realpath', return_value='/usr/bin/node'), \
             patch.object(b.Path, 'lstat', new=lstat), \
             patch.object(b.os, 'stat', return_value=actual), \
             patch.object(b.os, 'readlink', return_value='/usr/bin/node'):
            reader = b.LinuxSystem()
            self.assertRaisesRegex(Exception, 'PROCESS_EXECUTABLE_DRIFT', reader.process_exe, 123, '/usr/bin/node')
            actual.st_ino = 10
            self.assertEqual(reader.process_exe(123, '/usr/bin/node')[0], '/usr/bin/node')
            named.st_uid = 1000
            self.assertRaisesRegex(Exception, 'PROCESS_EXECUTABLE_DRIFT', reader.process_exe, 123, '/usr/bin/node')

    def test_pid_outside_actual_group_refuses(self):
        self.system.group_members = lambda unit: []
        self.assertRaisesRegex(Exception, 'ROLE_PID_OUTSIDE_CGROUP', self.target)
        self.assertEqual(self.system.signals, [])

    def test_exact_owned_fence_and_condition_are_read_back(self):
        self.fence()
        self.assertTrue(self.target()['ownedPersistentFence'])
        self.assertEqual(self.paths.fence(b.NATIVE).read_bytes(), self.backend._fence_bytes(HASH))
        self.paths.condition.write_bytes(b'')
        self.assertRaisesRegex(Exception, 'FALSE_CONDITION_EXISTS', self.target)

    def test_foreign_fence_is_never_overwritten(self):
        p = self.paths.fence(b.NATIVE)
        self.backend.files.directory(p.parent, mode=0o755, create=True)
        p.write_bytes(b'foreign')
        os.chmod(p, 0o644)
        self.assertRaises(Exception, self.fence)
        self.assertEqual(p.read_bytes(), b'foreign')
        self.assertNotIn(('/usr/bin/systemctl','daemon-reload'), self.system.calls)

    def test_singleton_freeze_requires_confirmed_kernel_state(self):
        target = self.target()
        self.fence()
        self.backend.freeze_native(target, HASH)
        self.backend.verify_frozen_singleton(target, HASH)
        self.system.frozen = False
        self.assertRaisesRegex(Exception, 'FROZEN_SINGLETON_REQUIRED',
                               self.backend.verify_frozen_singleton, target, HASH)
        self.assertEqual(self.system.signals, [])

    def test_foreign_or_incomplete_freezer_cannot_consume_signal(self):
        target = self.target()
        self.fence()
        self.system.requested = True
        self.assertRaisesRegex(Exception, 'FOREIGN_OR_PRIOR_FREEZE', self.backend.freeze_native, target, HASH)
        self.assertFalse((self.paths.state/'freeze-owner.json').exists())

    def test_pidfd_open_rechecks_instance_and_closes_on_reuse(self):
        target = self.target()
        self.system.on_open = lambda: setattr(self.system, 'proc_start', '999')
        self.assertRaises(Exception, self.backend.open_native_pidfd, target)
        self.assertEqual(self.system.closed, [self.system.pidfd])
        self.assertEqual(self.backend.handles, {})

    def test_exited_original_can_have_unrelated_reused_pid_but_live_wrong_group_refuses(self):
        target = self.target()
        self.system.props.update(MainPID='0', ActiveState='inactive', SubState='dead')
        self.system.proc_start = '999'
        self.system.proc_group = '/system.slice/unrelated.service'
        self.assertTrue(self.backend.observe_native(target)['exited'])
        self.assertEqual(self.system.signals, [])
        self.system.props.update(MainPID='123', ActiveState='active', SubState='running')
        self.assertRaisesRegex(Exception, 'PROCESS_CGROUP_DRIFT', self.backend.observe_native, target)

    def test_only_one_sigkill_even_when_syscall_reply_is_lost(self):
        target = self.target()
        self.fence()
        fd = self.backend.open_native_pidfd(target)
        self.backend.freeze_native(target, HASH)
        self.system.kill_lost_reply = True
        self.assertRaises(OSError, self.backend.kill_native_pidfd_once, fd, target, 2000)
        self.assertRaisesRegex(Exception, 'PIDFD_ATTEMPT_CONSUMED', self.backend.kill_native_pidfd_once, fd, target, 2000)
        self.assertEqual(self.system.signals, [(fd, signal.SIGKILL)])
        self.assertTrue(self.target()['ownedPersistentFence'])

    def test_expired_signal_and_extra_child_never_reach_pidfd_signal(self):
        target = self.target()
        self.fence()
        fd = self.backend.open_native_pidfd(target)
        self.backend.freeze_native(target, HASH)
        self.assertRaises(Exception, self.backend.kill_native_pidfd_once, fd, target, self.system.now())
        self.system.extra_members = [456]
        self.assertRaises(Exception, self.backend.verify_frozen_singleton, target, HASH)
        self.assertEqual(self.system.signals, [])

    def test_remove_checks_window_after_read_before_unlink(self):
        p = self.paths.state/'owned'
        p.parent.mkdir(mode=0o700)
        p.write_bytes(b'owned')
        os.chmod(p, 0o600)
        files = self.backend.files
        original = files.read
        def slow_read(*args, **kw):
            raw = original(*args, **kw)
            self.system.clock = self.cap.expires
            return raw
        with patch.object(files, 'read', side_effect=slow_read):
            self.assertRaisesRegex(Exception, 'TEST_WINDOW_EXPIRED', files.remove_exact, p, b'owned', mode=0o600)
        self.assertEqual(p.read_bytes(), b'owned')

    def test_named_file_replacement_after_fd_read_is_rejected(self):
        p = self.paths.state/'owned'
        p.parent.mkdir(mode=0o700)
        p.write_bytes(b'owned')
        os.chmod(p, 0o600)
        original = b.R8.ProtectedFiles.read
        def replaced(reader, *args, **kw):
            raw = original(reader, *args, **kw)
            other = p.with_name('replacement')
            other.write_bytes(raw)
            os.chmod(other, 0o600)
            os.replace(other, p)
            return raw
        with patch.object(b.R8.ProtectedFiles, 'read', new=replaced):
            self.assertRaisesRegex(Exception, 'NAMED_ROOT_FILE_CHANGED', self.backend.files.read, p, mode=0o600)

    def test_real_immutable_atomic_and_partial_prefix_resume_never_overwrite_foreign_bytes(self):
        p = self.paths.state/'immutable'
        files = self.backend.files
        files.atomic(p, b'exact', immutable=True)
        inode = p.stat().st_ino
        files.atomic(p, b'exact', immutable=True)
        self.assertEqual(p.stat().st_ino, inode)
        self.assertRaisesRegex(Exception, 'IMMUTABLE_FILE_CONFLICT', files.atomic, p, b'foreign', immutable=True)
        q = self.paths.state/'resumed'
        pending = q.with_name('.'+q.name+'.'+b.sha(b'known-complete')+'.pending')
        pending.write_bytes(b'known-')
        os.chmod(pending, 0o600)
        files.atomic(q, b'known-complete')
        self.assertEqual(q.read_bytes(), b'known-complete')
        self.assertFalse(pending.exists())

    def test_wrong_pending_bytes_symlink_and_hardlink_refuse(self):
        files = self.backend.files
        p = self.paths.state/'target'
        files.directory(p.parent, create=True)
        pending = p.with_name('.'+p.name+'.'+b.sha(b'approved')+'.pending')
        pending.write_bytes(b'foreign')
        os.chmod(pending, 0o600)
        self.assertRaisesRegex(Exception, 'PENDING_BYTES_CONFLICT', files.atomic, p, b'approved')
        pending.unlink()
        other = p.with_name('other')
        other.write_bytes(b'approved')
        os.chmod(other, 0o600)
        pending.symlink_to(other)
        self.assertRaises(Exception, files.atomic, p, b'approved')
        pending.unlink()
        os.link(other, pending)
        self.assertRaises(Exception, files.atomic, p, b'approved')
        self.assertFalse(p.exists())

    def test_atomic_expiry_before_create_or_after_write_never_publishes(self):
        p = self.paths.state/'receipt.json'
        self.system.clock = self.cap.expires
        self.assertRaises(Exception, self.backend.files.atomic, p, b'{}')
        self.assertFalse(p.exists())
        self.system.clock = 1000
        original = b.os.pwrite
        def slow_write(*args):
            n = original(*args)
            self.system.clock = self.cap.expires
            return n
        with patch.object(b.os, 'pwrite', side_effect=slow_write):
            self.assertRaises(Exception, self.backend.files.atomic, p, b'{}')
        self.assertFalse(p.exists())
        self.assertEqual(len(list(p.parent.glob('*.pending'))), 1)

    def test_real_journal_flock_and_consumed_intent_are_preserved(self):
        first = b.RootJournal(self.backend)
        second = b.RootJournal(self.backend)
        with first.locked():
            with self.assertRaisesRegex(Exception, 'JOURNAL_BUSY'):
                with second.locked(): pass
            old = {'planHash':HASH, 'originalBaseline':{'fixed':'old'},
                   'signalAttemptConsumed':True, 'checkpoint':{'fixed':'bytes'},
                   'checkpointHash':'e'*64, 'effects':{'native-signal':{'state':'INTENT'}}}
            first.write(old)
            bad = copy.deepcopy(old)
            bad['signalAttemptConsumed'] = False
            self.assertRaises(Exception, first.write, bad)
            self.assertEqual(first.read(), old)
        self.assertRaises(Exception, first.read)

    def test_lifecycle_unknown_intent_never_replays_effect(self):
        calls = []
        def lost():
            calls.append('effect')
            raise OSError('isolated unknown reply')
        self.assertRaises(OSError, self.backend._once, 'activate-fixed', HASH,
                          'activate:r16-owner.service', {'pid':0}, lost)
        self.assertRaisesRegex(Exception, 'LIFECYCLE_EFFECT_UNKNOWN_READBACK_ONLY',
                               self.backend._once, 'activate-fixed', HASH,
                               'activate:r16-owner.service', {'pid':0}, lost)
        self.assertEqual(calls, ['effect'])
        record = b.R8.parse_json(self.backend.files.read(
            self.backend._lifecycle_record('activate-fixed'), mode=0o600))
        self.assertEqual(record['state'], 'INTENT')

    def test_lifecycle_known_returned_result_is_not_reexecuted(self):
        calls = []
        def effect(): calls.append(1); return {'observed':'same-instance'}
        first = self.backend._once('activate-fixed', HASH, 'activate:r16-owner.service', {}, effect)
        second = self.backend._once('activate-fixed', HASH, 'activate:r16-owner.service', {}, effect)
        self.assertEqual(first, second)
        self.assertEqual(calls, [1])

    def test_late_recovery_file_syscalls_use_exact_restore_scope_not_forward_os_write(self):
        p = self.paths.state/'owned'
        p.parent.mkdir(mode=0o700)
        p.write_bytes(b'owned')
        os.chmod(p, 0o600)
        self.system.clock = self.cap.expires
        scope = 'restore:r16-owner.service'
        def require(h, op, target=None):
            self.cap.calls.append((h, op, target))
            b.need(h == HASH and op in (scope, 'inspect', 'journal-write'), 'NO_FORWARD_SCOPE_IN_RECOVERY')
            return None
        self.cap.require = require
        with self.backend.write_scope(scope):
            self.backend.files.remove_exact(p, b'owned', mode=0o600)
        self.assertFalse(p.exists())
        self.assertEqual(self.backend._effect_scope, 'os-write')
        self.assertTrue(all(op == scope for _,op,_ in self.cap.calls))

    def test_recovery_cannot_unfence_or_start_source_native_or_app(self):
        self.backend.publication_guard = lambda phase,h: None
        self.cap.original_baseline = {u:{'mainPid':123,'active':'active'} for u in b.HOSTS}
        self.backend.snapshot = lambda unit,h,phase='SOURCE': {
            'mainPid':0,'controlPid':0,'cgroupEmpty':True,
            'ownedPersistentFence':True,'pendingJob':False}
        for unit in (b.NATIVE, 'r16-app.service'):
            self.backend.host = b.HOSTS[unit]
            self.assertRaisesRegex(Exception, 'SOURCE_REOPEN_POLICY_REFUSED',
                                   self.backend.start_approved_role, unit, HASH, True)
        self.assertEqual(self.system.calls, [])

    def test_thaw_requires_empty_target_and_exact_freeze_owner(self):
        self.fence()
        self.backend.snapshot = lambda *args: {
            'mainPid':123,'controlPid':0,'cgroupEmpty':False,'ownedPersistentFence':True}
        self.assertRaisesRegex(Exception, 'THAW_REQUIRES_EMPTY_FENCED_NATIVE',
                               self.backend._thaw_empty_native, HASH)
        self.assertNotIn(('freezer', b'0'), self.system.calls)

    def test_unrecorded_running_new_instance_cannot_be_requiesced(self):
        self.backend.snapshot = lambda *args: {
            'mainPid':999,'controlPid':0,'cgroupEmpty':False,'ownedPersistentFence':False}
        self.backend._phase = lambda unit: 'TARGET'
        self.assertRaisesRegex(Exception, 'UNRECORDED_RUNNING_ROLE_REFUSED',
                               self.backend.stop_activated_role, b.NATIVE, HASH)
        self.assertEqual(self.system.calls, [])


if __name__ == '__main__': unittest.main()
