"""Code placement tests: private /tmp filesystem only, never root effects."""
import copy
import importlib.util
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('code_admission', Path(__file__).resolve().parents[1] / 'authority/code-admission.py')
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)


class CodeAdmissionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='mht-code-admission-')
        self.root = Path(self.tmp.name); self.root.chmod(0o700)
        self.packet = self.root / 'packet'; (self.packet / 'payload').mkdir(parents=True)
        self.backend = m.FileBackend(self.root)
        self.catalog = {'schema': 'r17.source19.protected-code-preparation-review.v1', 'authority': False,
                        'signable': False, 'executable': False, 'sourceRevision': 19,
                        'sourcePublicConfigHash': m.PUB19, 'sourceDeliveryHash': m.DELIVERY19,
                        'host': 'jenn-System-Product-Name', 'targets': []}
        for n in ('a.py', 'b.py'):
            raw = ('# reviewed ' + n + '\n').encode(); (self.packet / 'payload' / n).write_bytes(raw)
            self.catalog['targets'].append({'source': 'payload/' + n, 'target': m.LIB + n,
                'sha256': m.sha(raw), 'bytes': len(raw), 'uid': 0, 'gid': 0, 'mode': '0644',
                'operation': 'EXCLUSIVE_CREATE_IF_ABSENT'})
        self.bind(); self.clock = 1000

    def tearDown(self): self.tmp.cleanup()
    def bind(self): self.catalog['contentRoot'] = m.digest(self.catalog['targets'])
    def install(self, **kw):
        return m.install(self.catalog, self.packet, self.backend, kw.pop('approve', lambda _: True),
                         kw.pop('fresh', lambda: None), now=lambda: self.clock, **kw)
    def raises(self, code, fn):
        with self.assertRaisesRegex((ValueError, FileExistsError), code): fn()
    def target(self, n=0): return self.backend.path(self.catalog['targets'][n]['target'])

    def test_cancel_has_no_journal_or_effect(self):
        self.raises('CODE_ADMISSION_CANCELLED', lambda: self.install(approve=lambda _: False))
        self.assertFalse(self.backend.exists(m.STATE)); self.assertFalse(self.target().exists())

    def test_full_install_and_immutable_readback_no_reapply(self):
        result = self.install(); self.assertEqual(result['installedFiles'], 2)
        self.assertEqual(result['serviceActions'], 0); self.assertFalse(result['keysChanged'])
        self.assertEqual(self.install(approve=lambda _: self.fail('reconfirmation')), m.readback(self.catalog, self.backend))
        self.assertEqual(m.readback(self.catalog, self.backend)['createdFiles'], 2)

    def test_held_reviewed_bytes_cannot_change_during_consent(self):
        def approve(_):
            (self.packet / 'payload/a.py').write_bytes(b'unreviewed')
            return True
        self.install(approve=approve)
        self.assertEqual(m.sha(self.target().read_bytes()), self.catalog['targets'][0]['sha256'])

    def test_declared_source_hash_drift_refuses_before_consent(self):
        (self.packet / 'payload/a.py').write_bytes(b'drift')
        self.raises('PACKET_BYTES_DRIFT', lambda: self.install(approve=lambda _: self.fail('prompt')))

    def test_symlink_source_refuses(self):
        p = self.packet / 'payload/a.py'; p.unlink(); p.symlink_to(self.packet / 'payload/b.py')
        self.raises('PATH_LINK_REFUSED', self.install)

    def test_scope_and_sensitive_paths_refuse(self):
        for field, bad in [('target', '/run/r16-owner/public-config.json'), ('source', 'payload/../a.py'),
                           ('source', 'payload/secrets/a.py'), ('source', 'payload/a.key')]:
            c = copy.deepcopy(self.catalog); c['targets'][0][field] = bad; c['contentRoot'] = m.digest(c['targets'])
            self.raises('SCOPE|SENSITIVE', lambda: m.prepare(c, self.packet))

    def test_catalog_content_tamper_refuses(self):
        self.catalog['targets'][0]['mode'] = '0755'
        self.raises('CONTENT_ROOT', self.install)

    def test_foreign_protected_root_not_overwritten(self):
        self.backend.mkdir(m.LIB.rstrip('/'), 0o755)
        self.raises('FOREIGN_PROTECTED_ROOT', self.install)

    def test_trust_usage_prevents_install(self):
        self.backend.mkdir(m.USES[0], 0o700)
        self.raises('PREVIOUS_TRUST_USAGE', self.install)

    def test_expiry_between_intent_and_create_does_not_write(self):
        def fault(event):
            if event == 'before_write': self.clock += 300000
        self.raises('CODE_ADMISSION_EXPIRED', lambda: self.install(fault=fault))
        self.assertFalse(self.target().exists())
        self.raises('OUTCOME_UNKNOWN', lambda: self.install())

    def test_expiry_inside_mkdir_prevents_actual_create(self):
        original = self.backend.mkdir
        def late(name, mode, before_effect=lambda: None):
            if name == str(Path(self.catalog['targets'][0]['target']).parent): self.clock += 300000
            return original(name, mode, before_effect)
        self.backend.mkdir = late
        self.raises('CODE_ADMISSION_EXPIRED', self.install)
        self.assertFalse(self.target().exists())

    def test_known_partial_install_readback_never_continues(self):
        def fault(event):
            if event == 'after_known_write': raise ValueError('simulated crash')
        self.raises('simulated crash', lambda: self.install(fault=fault))
        r = self.install(approve=lambda _: self.fail('retry'))
        self.assertEqual(r['createdFiles'], 1); self.assertFalse(self.target(1).exists())

    def test_unknown_write_never_retries_or_removes(self):
        original = self.backend.write_new
        def crash(name, *a, **kw):
            result = original(name, *a, **kw)
            if name == self.catalog['targets'][0]['target']: raise ValueError('write outcome unknown')
            return result
        self.backend.write_new = crash
        self.raises('write outcome unknown', self.install)
        self.raises('OUTCOME_UNKNOWN', self.install)
        self.raises('OUTCOME_UNKNOWN', lambda: m.remove_unused(self.catalog, self.backend, lambda _: True, lambda: None))
        self.assertTrue(self.target().exists())

    def test_post_install_drift_not_called_success(self):
        self.install(); self.target().write_bytes(b'drift')
        self.raises('INSTALLED_CODE_DRIFT', lambda: m.readback(self.catalog, self.backend))

    def test_unused_removal_is_exact_and_history_preserved(self):
        self.install()
        r = m.remove_unused(self.catalog, self.backend, lambda _: True, lambda: None, now=lambda: self.clock)
        self.assertEqual(r['removedFiles'], 2); self.assertFalse(self.target().exists())
        self.assertEqual(m.readback(self.catalog, self.backend)['status'], 'CODE_REMOVED_UNUSED_HISTORY_ONLY')
        self.backend.write_new(self.catalog['targets'][0]['target'], b'foreign', 0o644)
        self.raises('REMOVED_CODE_REAPPEARED', lambda: m.readback(self.catalog, self.backend))

    def test_usage_blocks_even_unused_removal(self):
        self.install(); self.backend.mkdir(m.USES[4], 0o700)
        self.raises('CODE_ALREADY_USED', lambda: m.remove_unused(self.catalog, self.backend, lambda _: True, lambda: None))
        self.assertTrue(self.target().exists())

    def test_removal_expiry_in_fresh_check_prevents_unlink(self):
        self.install(); calls = 0
        def fresh():
            nonlocal calls
            calls += 1
            if calls > 1: self.clock += 300000
        self.raises('CODE_REMOVAL_EXPIRED', lambda: m.remove_unused(self.catalog, self.backend, lambda _: True, fresh, now=lambda: self.clock))
        self.assertTrue(self.target().exists()); self.assertTrue(self.target(1).exists())

    def test_loaded_services_block_removal_without_touching_files(self):
        self.install()
        def used(): raise ValueError('CODE_SERVICES_LOADED_PRESERVE_REQUIRED')
        self.backend.unused_services = used
        self.raises('CODE_SERVICES_LOADED', lambda: m.remove_unused(self.catalog, self.backend, lambda _: True, lambda: None))
        self.assertTrue(self.target().exists())

    def test_removal_cancel_preserves_files(self):
        self.install()
        self.raises('CODE_REMOVAL_CANCELLED', lambda: m.remove_unused(self.catalog, self.backend, lambda _: False, lambda: None))
        self.assertTrue(self.target().exists())

    def test_native_context_rejects_unprivileged_or_remote_foreground(self):
        from unittest.mock import patch
        with patch.object(m.os, 'getuid', return_value=1000):
            self.raises('LOCAL_HOST_ADMIN', m.native_root_context)
        with patch.object(m.os, 'getuid', return_value=0), patch.object(m.os, 'geteuid', return_value=0), \
             patch.object(m.socket, 'gethostname', return_value='remote'):
            self.raises('LOCAL_HOST_ADMIN', m.native_root_context)

    def test_source19_real_public_fixtures_cache_format(self):
        fixture = Path(__file__).parent / 'fixtures'
        pub = json.loads((fixture / 'SOURCE19_PUBLIC_CONFIG.json').read_text())
        env = json.loads((fixture / 'SOURCE19_DELIVERY_ENVELOPE.json').read_text())
        old = m.read
        config = {'schema': 1, 'data': {'connectionNonce': 3, 'delivery': {'revision': 19, 'envelope': env,
            'hash': m.digest({'publicConfig': pub, 'control': env['body']['control'], 'connectionNonce': 3})}}}
        def read(p, **_): return m.canonical(pub if 'public-config' in p else config)
        m.read = read
        try:
            m.fresh_source19()
            config['data']['delivery']['hash'] = m.digest(env)
            self.raises('CACHE_DRIFT', m.fresh_source19)
        finally: m.read = old

    def test_real_main_prompt_hash_and_receipt_bind_exact_hostadmin_actor(self):
        catalog = self.root / 'catalog.json'; raw = m.canonical(self.catalog); catalog.write_bytes(raw)
        actor = {'authorityType': 'TRUSTED_HOST_ADMIN_CODE_ONLY', 'humanIdentityConfirmed': False,
                 'callerLocalness': 'NOT_ASSERTED_BY_CODE_ADMISSION', 'process': {'pid': 123, 'startTicks': '4'}}
        output = io.StringIO(); observed = []
        def accept(prompt):
            challenge = json.loads(output.getvalue().splitlines()[-1])
            observed.append(challenge)
            self.assertEqual(challenge['nativeHostAdmin'], actor)
            self.assertIn('INSTALL_CODE ' + m.digest(challenge), prompt)
            return 'INSTALL_CODE ' + m.digest(challenge)
        argv = ['code-admission.py', 'apply', '--catalog', str(catalog), '--catalog-sha256', m.sha(raw), '--packet', str(self.packet)]
        with patch.object(m.sys, 'argv', argv), patch.object(m, 'native_root_context', return_value=actor), \
             patch.object(m, 'fresh_source19'), patch.object(m, 'FileBackend', return_value=self.backend), \
             patch('builtins.input', side_effect=accept), patch.object(m.sys, 'stdout', output):
            self.assertEqual(m.main(), 0)
        root = m.STATE + '/' + m.digest(self.catalog)
        intent = self.backend.load(root + '/intent.json'); result = self.backend.load(root + '/result.json')
        self.assertEqual(intent['challengeHash'], m.digest(observed[0]))
        for record in (intent, result):
            self.assertEqual(record['nativeHostAdmin'], actor)
            self.assertIs(record['humanIdentityConfirmed'], False)
            self.assertEqual(record['authorityType'], 'TRUSTED_HOST_ADMIN_CODE_ONLY')

    def test_main_context_drift_after_confirmation_refuses_before_any_write(self):
        catalog = self.root / 'catalog.json'; raw = m.canonical(self.catalog); catalog.write_bytes(raw)
        actor = {'authorityType': 'TRUSTED_HOST_ADMIN_CODE_ONLY', 'humanIdentityConfirmed': False, 'process': {'pid': 123}}
        output = io.StringIO()
        def accept(_):
            challenge = json.loads(output.getvalue().splitlines()[-1])
            return 'INSTALL_CODE ' + m.digest(challenge)
        argv = ['code-admission.py', 'apply', '--catalog', str(catalog), '--catalog-sha256', m.sha(raw), '--packet', str(self.packet)]
        with patch.object(m.sys, 'argv', argv), \
             patch.object(m, 'native_root_context', side_effect=[actor, actor, dict(actor, process={'pid': 124})]), \
             patch.object(m, 'fresh_source19'), patch.object(m, 'FileBackend', return_value=self.backend), \
             patch('builtins.input', side_effect=accept), patch.object(m.sys, 'stdout', output):
            self.assertEqual(m.main(), 78)
        self.assertFalse(self.target().exists())
        self.assertFalse(self.backend.exists(m.STATE))

    def test_confirmation_eof_is_bounded_refusal_without_writes(self):
        catalog = self.root / 'catalog.json'; raw = m.canonical(self.catalog); catalog.write_bytes(raw)
        argv = ['code-admission.py', 'apply', '--catalog', str(catalog), '--catalog-sha256', m.sha(raw), '--packet', str(self.packet)]
        with patch.object(m.sys, 'argv', argv), patch.object(m, 'native_root_context', return_value={'humanIdentityConfirmed': False}), \
             patch.object(m, 'fresh_source19'), patch.object(m, 'FileBackend', return_value=self.backend), \
             patch('builtins.input', side_effect=EOFError), patch.object(m.sys, 'stdout', io.StringIO()):
            self.assertEqual(m.main(), 78)
        self.assertFalse(self.target().exists())
        self.assertFalse(self.backend.exists(m.STATE))


class NativeSudoPTYTests(unittest.TestCase):
    """Synthetic kernel/proc metadata, never sudo, root or terminal input."""
    def setup_chain(self, count=2, root_inner=True):
        self.rows = {
            500: {'pid': 500, 'ppid': 400, 'pgrp': 500, 'sid': 400, 'startTicks': '100', 'uids': (0, 0, 0, 0)},
            400: {'pid': 400, 'ppid': 300 if count == 2 else 200, 'pgrp': 400, 'sid': 400, 'startTicks': '90', 'uids': (0, 0, 0, 0)},
            # Distinct outer SID is normal sudo use_pty behavior.
            300: {'pid': 300, 'ppid': 200, 'pgrp': 300, 'sid': 300, 'startTicks': '80', 'uids': (1000, 0, 0, 0)},
            200: {'pid': 200, 'ppid': 100, 'pgrp': 200, 'sid': 200, 'startTicks': '70', 'uids': (1000, 1000, 1000, 1000)},
        }
        self.root_inner = root_inner
        self.drift = None
        self.reads = {}
        self.bad_exe = None
        self.bad_fd = None
        self.bad_node = False
        self.exec_mode = 0o4755
        self.outer_foreground = 300 if root_inner else 500
        self.caller_session_missing = False
        self.caller_session_id = '3'
        self.caller_remote = 'no'
        for pid, row in self.rows.items():
            row['ttyNr'] = 200 if root_inner and pid in (500, 400) else 100
            row['foregroundPgrp'] = 500 if pid in (500, 400) else self.outer_foreground

    def proc_text(self, path):
        parts = str(path).split('/')
        pid = int(parts[2]); row = self.rows[pid]
        if parts[-1] == 'status':
            return 'Name: fixture\nUid:\t' + '\t'.join(map(str, row['uids'])) + '\n'
        self.reads[pid] = self.reads.get(pid, 0) + 1
        row = dict(row)
        if self.drift and self.drift[0] == pid and self.reads[pid] > 1:
            row[self.drift[1]] = self.drift[2]
        if pid in (300, 200):
            row['foregroundPgrp'] = self.outer_foreground
        fields = ['S', str(row['ppid']), str(row['pgrp']), str(row['sid']), str(row['ttyNr']), str(row['foregroundPgrp'])] + ['0'] * 13 + [row['startTicks']]
        return str(pid) + ' (fixture name) ' + ' '.join(fields)

    def tty_row(self, inner=False):
        uid = 0 if inner and self.root_inner else 1000
        return SimpleNamespace(st_mode=m.stat.S_IFCHR | 0o620, st_dev=1,
                               st_ino=20 if uid == 0 else 10, st_rdev=200 if uid == 0 else 100,
                               st_uid=uid, st_gid=5)

    def stat(self, path, **kwargs):
        parts = str(path).split('/')
        if parts[-1] == 'exe':
            pid = int(parts[2]); inode = 7 if pid in (400, 300) else 8
            if pid == self.bad_exe:
                inode = 99
            return SimpleNamespace(st_mode=m.stat.S_IFREG | self.exec_mode, st_uid=0, st_dev=2, st_ino=inode)
        row = self.tty_row()
        if self.bad_fd == (int(parts[2]), int(parts[-1])):
            row.st_ino += 1
        return row

    def invoke(self):
        opened = {}
        counter = [20]
        def open_(name, flags, **kw):
            counter[0] += 1
            opened[counter[0]] = str(name)
            return counter[0]
        def fstat(fd):
            inner = fd in (0, 1, 2) or opened.get(fd) == '1'
            row = self.tty_row(inner)
            if self.bad_fd == (500, fd):
                row.st_ino += 1
            if self.bad_node and fd > 2 and opened.get(fd) in ('0', '1'):
                row.st_ino += 1
            return row
        def ttyname(fd):
            return '/dev/pts/1' if self.root_inner else '/dev/pts/0'
        def run(argv, **kw):
            if 'show-user' in argv:
                return SimpleNamespace(returncode=0, stdout=b'3\n')  # A local Display alone is insufficient.
            if 'GetSessionByPID' in argv:
                self.assertEqual(argv[-2:], ['u', '200'])
                return SimpleNamespace(returncode=1 if self.caller_session_missing else 0,
                                       stdout=b'{"type":"o","data":["/org/freedesktop/login1/session/_33"]}')
            if 'get-property' in argv:
                return SimpleNamespace(returncode=0, stdout=m.canonical({'type': 's', 'data': [self.caller_session_id]}))
            self.assertIn('show-session', argv)
            return SimpleNamespace(returncode=0, stdout=('User=1000\nName=jenn\nRemote=' + self.caller_remote + '\nActive=yes\n').encode())
        with patch.object(m.os, 'getuid', return_value=0), patch.object(m.os, 'geteuid', return_value=0), \
             patch.object(m.socket, 'gethostname', return_value='jenn-System-Product-Name'), \
             patch.object(m.sys, 'stdin', SimpleNamespace(isatty=lambda: True)), \
             patch.object(m.os, 'isatty', return_value=True), patch.object(m.os, 'getpgrp', return_value=500), \
             patch.object(m.os, 'tcgetpgrp', side_effect=lambda fd: (_ for _ in ()).throw(OSError(25, 'outer ENOTTY')) if self.root_inner and opened.get(fd) == '0' else 500), \
             patch.object(m.os, 'getpid', return_value=500), \
             patch.object(m.os, 'open', side_effect=open_), patch.object(m.os, 'close'), \
             patch.object(m.os, 'fstat', side_effect=fstat), patch.object(m.os, 'stat', side_effect=self.stat), \
             patch.object(m.os, 'ttyname', side_effect=ttyname), patch.object(m.os, 'readlink', return_value='/dev/pts/0'), \
             patch.object(m.Path, 'read_text', autospec=True, side_effect=self.proc_text), \
             patch.object(m, '_native_executable', side_effect=lambda p: (2, 7 if p.endswith('sudo') else 8)), \
             patch.object(m.subprocess, 'run', side_effect=run) as global_session_queries:
            context = m.native_root_context()
            self.assertFalse(global_session_queries.called, 'G1 cannot use global GUI state as Human authority')
            return context

    def test_two_sudo_root_inner_pts_with_distinct_outer_sid(self):
        self.setup_chain()
        r = self.invoke()
        self.assertEqual(r['inner']['identity'][3], 0)
        self.assertEqual(r['outer']['identity'][3], 1000)
        self.assertEqual(len(r['sudoAncestors']), 2)
        self.assertNotEqual(r['sudoAncestors'][0]['sid'], r['sudoAncestors'][1]['sid'])

    def test_no_use_pty_keeps_exact_original_user_terminal(self):
        self.setup_chain(count=1, root_inner=False)
        r = self.invoke()
        self.assertEqual(r['inner'], r['outer'])
        self.assertEqual(len(r['sudoAncestors']), 1)

    def test_arbitrary_root_parent_is_not_sudo(self):
        self.setup_chain()
        self.bad_exe = 400
        with self.assertRaisesRegex(ValueError, 'NATIVE_EXECUTABLE_REFUSED'):
            self.invoke()

    def test_foreign_user_launcher_rejected(self):
        self.setup_chain()
        self.rows[200]['uids'] = (1001, 1001, 1001, 1001)
        with self.assertRaisesRegex(ValueError, 'JENN_LAUNCHER_REQUIRED'):
            self.invoke()

    def test_sudo_real_uid_other_than_jenn_or_root_rejected(self):
        self.setup_chain()
        self.rows[300]['uids'] = (1001, 0, 0, 0)
        with self.assertRaisesRegex(ValueError, 'NATIVE_SUDO_UID_REFUSED'):
            self.invoke()

    def test_parent_start_drift_rejected(self):
        self.setup_chain(); self.drift = (400, 'startTicks', '91')
        with self.assertRaisesRegex(ValueError, 'NATIVE_PROCESS_ANCESTRY_CHANGED'):
            self.invoke()

    def test_parent_ppid_drift_rejected(self):
        self.setup_chain(); self.drift = (400, 'ppid', 399)
        with self.assertRaisesRegex(ValueError, 'NATIVE_PROCESS_ANCESTRY_CHANGED'):
            self.invoke()

    def test_parent_uid_drift_rejected(self):
        self.setup_chain(); self.drift = (400, 'uids', (1001, 0, 0, 0))
        # status is read after stat; simulate a changed status on the second pair.
        old = self.proc_text
        def text(path):
            raw = old(path)
            if str(path) == '/proc/400/status' and self.reads.get(400, 0) > 1:
                return 'Uid:\t1001\t0\t0\t0\n'
            return raw
        self.proc_text = text
        with self.assertRaisesRegex(ValueError, 'NATIVE_PROCESS_ANCESTRY_CHANGED'):
            self.invoke()

    def test_inner_stdio_mismatch_rejected(self):
        self.setup_chain(); self.bad_fd = (500, 2)
        with self.assertRaisesRegex(ValueError, 'SAME_FOREGROUND_JENN_TTY_REQUIRED'):
            self.invoke()

    def test_outer_stdio_mismatch_rejected(self):
        self.setup_chain(); self.bad_fd = (200, 2)
        with self.assertRaisesRegex(ValueError, 'SAME_FOREGROUND_JENN_TTY_REQUIRED'):
            self.invoke()

    def test_named_pts_inode_replacement_rejected(self):
        self.setup_chain(); self.bad_node = True
        with self.assertRaisesRegex(ValueError, 'NATIVE_PTS_NODE_DRIFT'):
            self.invoke()

    def test_sudo_exe_writable_rejected(self):
        self.setup_chain(); self.exec_mode = 0o4777
        with self.assertRaisesRegex(ValueError, 'NATIVE_EXECUTABLE_REFUSED'):
            self.invoke()

    def test_third_sudo_not_a_jenn_launcher(self):
        self.setup_chain(); self.rows[200]['uids'] = (0, 0, 0, 0)
        with self.assertRaisesRegex(ValueError, 'JENN_LAUNCHER_REQUIRED'):
            self.invoke()

    def test_outer_background_pgrp_rejected_despite_inner_foreground(self):
        self.setup_chain(); self.outer_foreground = 999
        with self.assertRaisesRegex(ValueError, 'OUTER_NATIVE_TTY_BACKGROUND'):
            self.invoke()

    def test_remote_caller_not_blessed_by_local_display(self):
        self.setup_chain(); self.caller_session_id = 'ssh7'; self.caller_remote = 'yes'
        r = self.invoke()
        self.assertEqual(r['authorityType'], 'TRUSTED_HOST_ADMIN_CODE_ONLY')
        self.assertIs(r['humanIdentityConfirmed'], False)
        self.assertEqual(r['callerLocalness'], 'NOT_ASSERTED_BY_CODE_ADMISSION')

    def test_missing_caller_session_never_fabricates_human_identity(self):
        self.setup_chain(); self.caller_session_missing = True
        r = self.invoke()
        self.assertNotIn('session', r)
        self.assertIs(r['humanIdentityConfirmed'], False)

    def test_global_display_does_not_supply_physical_caller_localness(self):
        self.setup_chain(); self.caller_remote = 'yes'
        r = self.invoke()
        self.assertEqual(r['callerLocalness'], 'NOT_ASSERTED_BY_CODE_ADMISSION')
        self.assertIs(r['humanIdentityConfirmed'], False)

    def test_real_nested_forkpty_reads_outer_kernel_foreground_without_outer_ioctl(self):
        # Ordinary disposable processes only. This reproduces sudo use_pty's
        # two controlling-terminal topology without executing sudo or a gate.
        import errno
        import select
        import signal
        reader, writer = os.pipe()
        outer_pid, outer_master = os.forkpty()
        if outer_pid == 0:
            os.close(reader)
            inner_pid, inner_master = os.forkpty()
            if inner_pid == 0:
                try:
                    outer = m._native_pts(os.getppid())
                    inner = m._native_pts()
                    proc = m._native_proc(os.getppid())
                    fd = os.open(outer['path'], os.O_RDWR | os.O_NOCTTY)
                    try:
                        try:
                            os.tcgetpgrp(fd)
                            denied = False
                        except OSError as e:
                            denied = e.errno == errno.ENOTTY
                    finally:
                        os.close(fd)
                    passed = (denied and inner['path'] != outer['path']
                              and proc['ttyNr'] == outer['identity'][2]
                              and proc['foregroundPgrp'] == proc['pgrp'])
                    os.write(writer, b'PASS' if passed else b'FAIL')
                    os._exit(0 if passed else 1)
                except BaseException:
                    os.write(writer, b'ERROR')
                    os._exit(1)
            _, status = os.waitpid(inner_pid, 0)
            os.close(inner_master)
            os._exit(os.waitstatus_to_exitcode(status))
        os.close(writer)
        try:
            ready = select.select([reader], [], [], 10)[0]
            if not ready:
                os.kill(outer_pid, signal.SIGKILL)
            self.assertTrue(ready, 'disposable nested PTY test timed out')
            self.assertEqual(os.read(reader, 64), b'PASS')
        finally:
            os.close(reader)
            _, status = os.waitpid(outer_pid, 0)
            os.close(outer_master)
        self.assertEqual(os.waitstatus_to_exitcode(status), 0)


if __name__ == '__main__': unittest.main()
