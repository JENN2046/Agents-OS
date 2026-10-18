"""Ordinary private /tmp trees only. No sudo, SSH, production state or keys."""
import copy
import fcntl
import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.dont_write_bytecode = True
HERE = Path(__file__).parent
spec = importlib.util.spec_from_file_location('update_builder_test', HERE / 'build_entry.py')
b = importlib.util.module_from_spec(spec);spec.loader.exec_module(b)
PACKET = b.packet_sources();u = sys.modules['code_update'];s = sys.modules['support_admission']


class Fixture:
    def __init__(self, case, host=s.CLOUD):
        self.tmp = tempfile.TemporaryDirectory(prefix='readonly-update-');case.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name);self.root.chmod(0o700)
        self.fs = s.FS(str(self.root));self.host = host;self.now = 1000.;self.mono = 20.
        self.boot = 'fixture-boot';self.native = {'identity': 'isolated-fixture-native'}
        self.source = {'configurationRevision': 19, 'grant': s.GRANT, 'owner': 'UNCHANGED'}
        self.engine = u.Update(PACKET, host, self.fs, lambda: copy.deepcopy(self.native),
            lambda: copy.deepcopy(self.source), lambda: self.boot, lambda: self.now, lambda: self.mono)
        old = self.engine.legacy
        ch = old.review('install')
        old.accept(ch, 'INSTALL_READONLY_CODE ' + ('CLOUD' if host == s.CLOUD else 'LOCAL') +
                   ' ' + s.digest(ch));old.install()
        self.before = self.engine.inventory()
        self.old_audit = {p: p.read_bytes() for p in self.path(s.STATE).rglob('*') if p.is_file()}

    def path(self, name): return self.root / name[1:]
    def challenge(self, action='update'):
        ch = self.engine.review(action)
        verb = 'UPDATE_READONLY_CODE' if action == 'update' else 'RESTORE_READONLY_CODE'
        self.engine.accept(ch, verb + ' ' + ('CLOUD' if self.host == s.CLOUD else 'LOCAL') +
                           ' ' + s.digest(ch));return ch
    def apply(self): self.challenge();return self.engine.update()
    def restore(self): self.challenge('restore');return self.engine.restore()
    def fail_at(self, point):
        def fail(p):
            if p == point:raise RuntimeError('ISOLATED_FAULT')
        self.engine.fault = fail
    def original_preserved(self, case):
        for p in self.old_audit:case.assertEqual(p.read_bytes(), self.old_audit[p])
        for p in self.before:
            if p not in u.ORDER:case.assertEqual(u.public(self.fs.inspect(p)), self.before[p])


class UpdateTests(unittest.TestCase):
    def fixture(self, host=s.CLOUD):return Fixture(self, host)

    def test_exact_three_object_update_both_hosts_then_independent_readback(self):
        for host in (s.CLOUD, s.LOCAL):
            with self.subTest(host=host):
                f = self.fixture(host);out = f.apply()
                self.assertEqual(out['status'], 'READONLY_CODE_UPDATED_EXACT')
                self.assertTrue(out['terminal']);self.assertFalse(out['businessAcceptance'])
                self.assertEqual(f.engine.readback()['status'], 'READONLY_CODE_UPDATED_EXACT_READBACK')
                for i, p in enumerate(u.ORDER):
                    self.assertEqual(f.fs.inspect(p)['sha256'], f.engine.new[p][0]['sha256'])
                    self.assertTrue(u.same_object(u.public(f.fs.inspect(u.slot('archive', i))), f.before[p]))
                f.original_preserved(self)

    def test_review_and_readback_create_no_objects_and_do_not_acquire_locks(self):
        f = self.fixture();before = set(f.root.rglob('*'))
        with patch.object(f.engine, 'lock', side_effect=AssertionError('NO_REVIEW_LOCK')):
            ch = f.engine.review('update');self.assertFalse(ch['oldApprovalOrDeadlineReused'])
            self.assertEqual(f.engine.readback()['status'], 'NO_UPDATE_INTENT_READBACK_ONLY')
        self.assertEqual(set(f.root.rglob('*')), before)

    def test_cancelled_or_incomplete_exact_intent_has_no_writes(self):
        f = self.fixture();ch = f.engine.review('update')
        for text in ('', 'UPDATE_READONLY_CODE CLOUD wrong', 'update', 'x' * 200):
            with self.assertRaisesRegex(ValueError, 'EXACT_NATIVE_INTENT_CANCELLED'):
                f.engine.accept(ch, text)
        self.assertFalse(f.path(u.STATE).exists());f.original_preserved(self)

    def test_original_installation_and_receipt_required(self):
        for p in (s.STATE + '/result.json', s.STATE + '/progress.jsonl', s.STATE + '/.lock'):
            f = self.fixture();f.path(p).unlink()
            with self.assertRaises((ValueError, FileNotFoundError)):f.engine.review('update')
            self.assertFalse(f.path(u.STATE).exists())

    def test_same_bytes_foreign_inode_never_adopted(self):
        f = self.fixture();p = f.path(u.ORDER[0]);original = p.read_bytes()
        p.rename(p.with_name(p.name + '.retained'))
        # Foreign file outside the target namespace for the metadata-only check.
        p.write_bytes(original);p.chmod(0o644)
        with self.assertRaises(ValueError):f.engine.review('update')
        self.assertFalse(f.path(u.STATE).exists())

    def test_unchanged_target_drift_and_permission_drift_refuse(self):
        for how in ('bytes', 'mode', 'inode'):
            f = self.fixture();target = next(p for p in f.before if p not in u.ORDER and p.startswith(s.ROOT + '/runtime/'))
            p = f.path(target)
            if how == 'bytes':p.write_bytes(b'foreign')
            elif how == 'mode':p.chmod(0o666)
            else:
                value = p.read_bytes();q = f.root / 'retained';p.rename(q);p.write_bytes(value);p.chmod(f.before[target]['identity']['mode'])
            with self.assertRaises(ValueError):f.engine.review('update')
            self.assertFalse(f.path(u.STATE).exists())

    def test_symlink_hardlink_and_extra_code_object_refuse(self):
        for how in ('symlink', 'hardlink', 'extra'):
            f = self.fixture();p = f.path(u.ORDER[0])
            if how == 'symlink':p.unlink();p.symlink_to(f.path(u.ORDER[1]))
            elif how == 'hardlink':os.link(p, f.root / 'retained-link')
            else:(p.parent / 'foreign').write_bytes(b'no')
            with self.assertRaises((ValueError, OSError)):f.engine.review('update')
            self.assertFalse(f.path(u.STATE).exists())

    def test_cross_filesystem_refuses_before_any_audit_write(self):
        f = self.fixture();device = f.fs.device
        with patch.object(f.fs, 'device', side_effect=lambda p: device(p) + (p == u.ORDER[0])):
            with self.assertRaisesRegex(ValueError, 'SAME_FILESYSTEM_REQUIRED'):f.engine.review('update')
        self.assertFalse(f.path(u.STATE).exists())

    def test_busy_original_lock_is_not_recreated_or_overridden(self):
        f = self.fixture();ch = f.challenge();p = f.path(s.STATE + '/.lock')
        with p.open('rb') as held:
            fcntl.flock(held, fcntl.LOCK_EX | fcntl.LOCK_NB)
            with self.assertRaises(BlockingIOError):f.engine.update()
        self.assertFalse(f.path(u.STATE).exists());self.assertEqual(f.engine.inventory(), ch['before'])

    def test_partial_namespace_created_while_waiting_for_old_lock_is_not_adopted(self):
        f = self.fixture();f.challenge();original = f.engine.lock
        def concurrent(path, expected):
            fd = original(path, expected)
            if path == s.STATE + '/.lock':
                d, _ = f.fs.parent(u.STATE + '/intent.json', True, lambda: None, 0o700)
                os.close(d)
            return fd
        with patch.object(f.engine, 'lock', side_effect=concurrent):
            with self.assertRaisesRegex(ValueError, 'UPDATE_ALREADY_ATTEMPTED'):
                f.engine.update()
        self.assertFalse(f.path(u.STATE + '/intent.json').exists())
        self.assertEqual(f.engine.inventory(), f.before)

    def test_old_lock_full_identity_and_receipt_pinned(self):
        for kind in ('lock', 'receipt'):
            f = self.fixture();f.challenge()
            p = f.path(s.STATE + ('/.lock' if kind == 'lock' else '/result.json'))
            if kind == 'lock':p.chmod(0o644)
            else:p.write_bytes(p.read_bytes() + b'\n')
            with self.assertRaises(ValueError):f.engine.update()
            self.assertFalse(f.path(u.STATE).exists())

    def test_source_native_boot_and_both_clocks_refuse_without_writes(self):
        for kind in ('source', 'native', 'boot', 'wall-forward', 'wall-back', 'mono-forward', 'mono-back'):
            f = self.fixture();f.challenge()
            if kind == 'source':f.source['configurationRevision'] = 20
            elif kind == 'native':f.native['identity'] = 'foreign'
            elif kind == 'boot':f.boot = 'new-boot'
            elif kind == 'wall-forward':f.now += 300
            elif kind == 'wall-back':f.now -= 1
            elif kind == 'mono-forward':f.mono += 300
            else:f.mono -= 1
            with self.assertRaises(ValueError):f.engine.update()
            self.assertFalse(f.path(u.STATE).exists())

    def test_slow_native_acceptance_cannot_extend_five_minutes(self):
        f = self.fixture();ch = f.engine.review('update');native = f.engine.native
        def slow():f.mono += 301;return native()
        with patch.object(f.engine, 'native', side_effect=slow):
            with self.assertRaisesRegex(ValueError, 'EXPIRED'):
                f.engine.accept(ch, 'UPDATE_READONLY_CODE CLOUD ' + s.digest(ch))
        self.assertFalse(f.path(u.STATE).exists())

    def test_every_stage_archive_publish_fault_refuses_update_replay_and_restores_original(self):
        for operation in ('stage', 'archive', 'publish'):
            for i in range(3):
                for boundary in ('before', 'after'):
                    point = operation + '-' + str(i) + ':' + boundary
                    with self.subTest(point=point):
                        f = self.fixture();f.challenge();f.fail_at(point)
                        with self.assertRaisesRegex(RuntimeError, 'ISOLATED_FAULT'):f.engine.update()
                        f.engine.fault = lambda _: None
                        with self.assertRaisesRegex(ValueError, 'UPDATE_ALREADY_ATTEMPTED'):
                            f.engine.review('update')
                        # No repeat of the unresolved syscall: fresh native
                        # restore observes actual known inode placement.
                        f.engine.readback();out = f.restore()
                        self.assertEqual(out['status'], 'ORIGINAL_READONLY_CODE_RESTORED_EXACT')
                        for p in u.ORDER:self.assertTrue(u.same_object(u.public(f.fs.inspect(p)), f.before[p]))
                        f.original_preserved(self)

    def test_completed_update_has_separate_restore_authority_and_keeps_new_and_old_history(self):
        f = self.fixture();f.apply();update_intent = f.path(u.STATE + '/intent.json').read_bytes()
        f.now += 1000;f.mono += 1000
        with self.assertRaisesRegex(ValueError, 'EXPIRED'):f.engine.restore()
        out = f.restore();self.assertFalse(out['oldApprovalOrDeadlineReused'])
        self.assertEqual(f.path(u.STATE + '/intent.json').read_bytes(), update_intent)
        for i in range(3):self.assertIsNotNone(f.fs.inspect(u.slot('reverted', i)))
        self.assertEqual(f.engine.readback()['status'], 'ORIGINAL_CODE_PRESENT_READBACK_ONLY')
        f.original_preserved(self)

    def test_restore_can_read_back_then_obtain_new_confirmation_after_each_interrupted_move(self):
        for op in ('retire', 'restore'):
            for i in range(3):
                for boundary in ('before', 'after'):
                    point = op + '-' + str(i) + ':' + boundary
                    with self.subTest(point=point):
                        f = self.fixture();f.apply();f.challenge('restore');f.fail_at(point)
                        with self.assertRaisesRegex(RuntimeError, 'ISOLATED_FAULT'):f.engine.restore()
                        f.engine.fault = lambda _: None;f.engine.readback()
                        out = f.restore();self.assertEqual(out['status'], 'ORIGINAL_READONLY_CODE_RESTORED_EXACT')
                        for p in u.ORDER:self.assertTrue(u.same_object(u.public(f.fs.inspect(p)), f.before[p]))

    def test_foreign_same_byte_inode_cannot_be_restored_or_archived(self):
        f = self.fixture();f.apply();p = f.path(u.ORDER[0]);value = p.read_bytes()
        q = f.root / 'foreign-retained';p.rename(q);p.write_bytes(value);p.chmod(0o644)
        with self.assertRaisesRegex(ValueError, 'FOREIGN_TARGET_OBJECT'):f.engine.review('restore')
        self.assertFalse(f.path(u.slot('reverted', 0)).exists())

    def test_restoration_revalidates_known_current_inode_at_each_iteration(self):
        f = self.fixture();f.apply();f.challenge('restore');original = f.engine.move
        def drift(log, op, *args):
            result = original(log, op, *args)
            if op == 'restore-0':
                p = f.path(u.ORDER[1]);value = p.read_bytes();p.rename(f.root / 'retained-foreign')
                p.write_bytes(value);p.chmod(0o600)
            return result
        with patch.object(f.engine, 'move', side_effect=drift):
            with self.assertRaisesRegex(ValueError, 'CONFIRMED_OBJECT_IDENTITY_DRIFT'):f.engine.restore()
        self.assertFalse(f.path(u.slot('reverted', 1)).exists())

    def test_restoration_refuses_ctime_only_drift_of_unprocessed_confirmed_object(self):
        f = self.fixture();f.apply();f.challenge('restore');original = f.engine.move
        def touch(log, op, *args):
            result = original(log, op, *args)
            if op == 'restore-0':
                p = f.path(u.ORDER[1]);p.chmod(0o644);p.chmod(0o600)
            return result
        with patch.object(f.engine, 'move', side_effect=touch):
            with self.assertRaisesRegex(ValueError, 'CONFIRMED_OBJECT_IDENTITY_DRIFT'):
                f.engine.restore()
        self.assertFalse(f.path(u.slot('reverted', 1)).exists())

    def test_published_object_ctime_drift_during_update_is_not_accepted(self):
        f = self.fixture();f.challenge()
        def touch(point):
            if point == 'archive-1:after':
                p = f.path(u.ORDER[0]);p.chmod(0o600);p.chmod(0o644)
        f.engine.fault = touch
        with self.assertRaisesRegex(ValueError, 'CONFIRMED_OBJECT_IDENTITY_DRIFT'):
            f.engine.update()
        self.assertFalse(f.path(u.ORDER[1]).exists())

    def test_final_receipt_cannot_succeed_after_post_observation_ctime_drift(self):
        for action in ('update', 'restore'):
            f = self.fixture()
            if action == 'restore':f.apply()
            f.challenge(action);original = f.engine.result
            def late(status, observation):
                result = original(status, observation)
                p = f.path(u.ORDER[0]);p.chmod(0o600);p.chmod(0o644)
                return result
            with patch.object(f.engine, 'result', side_effect=late):
                with self.assertRaisesRegex(ValueError, 'CONFIRMED_OBJECT_IDENTITY_DRIFT'):
                    getattr(f.engine, action)()
            if action == 'update':self.assertFalse(f.path(u.STATE + '/result.json').exists())
            else:self.assertFalse(any(f.path(u.STATE + '/restore').glob('*/result.json')))

    def test_mid_effect_unchanged_object_or_source_drift_stops_further_effects(self):
        for kind in ('source', 'other'):
            f = self.fixture();f.challenge()
            def drift(point):
                if point == 'publish-0:after':
                    if kind == 'source':f.source['configurationRevision'] = 20
                    else:
                        p = next(p for p in f.before if p not in u.ORDER and p.startswith(s.ROOT + '/runtime/'))
                        f.path(p).write_bytes(b'foreign')
            f.engine.fault = drift
            with self.assertRaises(ValueError):f.engine.update()
            self.assertEqual(u.public(f.fs.inspect(u.ORDER[1])), f.before[u.ORDER[1]])

    def test_no_unknown_overwrite_when_archive_slot_races(self):
        f = self.fixture();f.challenge()
        def race(point):
            if point == 'archive-0:before':
                p = f.path(u.slot('archive', 0));p.parent.mkdir(mode=0o700, exist_ok=True)
                p.write_bytes(b'foreign');p.chmod(0o644)
        f.engine.fault = race
        with self.assertRaises(ValueError):f.engine.update()
        self.assertEqual(f.path(u.slot('archive', 0)).read_bytes(), b'foreign')
        self.assertEqual(u.public(f.fs.inspect(u.ORDER[0])), f.before[u.ORDER[0]])

    def test_publication_gate_refuses_every_mixed_freeze_pin_state(self):
        f = self.fixture();f.challenge();seen = []
        def verify(point):
            if point.startswith(('archive-', 'publish-')) and point.endswith(':after'):
                pin = f.fs.inspect(s.PIN);freeze = f.fs.inspect(s.ROOT + '/ENTRY_FREEZE.json')
                ready = pin is not None and freeze is not None
                if ready:
                    ready = json.loads(pin['raw'])['capsuleHash'] == freeze['sha256']
                    if ready:
                        rows = json.loads(freeze['raw'])['files']
                        ready = all((obj := f.fs.inspect(s.ROOT + '/runtime/' + n)) is not None and obj['sha256'] == r['sha256']
                                    for n, r in rows.items())
                seen.append((point, ready))
        f.engine.fault = verify;f.engine.update()
        self.assertTrue(seen[-1][1]);self.assertEqual(seen[-1][0], 'publish-2:after')
        self.assertTrue(all(not ready for _, ready in seen[:-1]))

    def test_audit_or_namespace_presence_refuses_a_new_update(self):
        f = self.fixture();fd, _ = f.fs.parent(u.STATE + '/intent.json', True, lambda: None, 0o700);os.close(fd)
        with self.assertRaisesRegex(ValueError, 'ALREADY_ATTEMPTED'):f.engine.review('update')

    def test_partial_audit_without_intent_is_not_reported_as_no_attempt(self):
        f = self.fixture();d, _ = f.fs.parent(u.STATE + '/intent.json', True, lambda: None, 0o700);os.close(d)
        before = set(f.root.rglob('*'))
        self.assertEqual(f.engine.readback()['status'], 'PARTIAL_AUDIT_NO_INTENT_READBACK_REQUIRED')
        self.assertEqual(set(f.root.rglob('*')), before)

    def test_packet_scope_support_and_capsule_tamper_refuse(self):
        for name in ('support_admission.py', 'native_guard.py', 'bundle/CODE_ADMISSION_CANDIDATE.json',
                     'bundle/root/ENTRY_FREEZE.json', 'previous/CODE_ADMISSION_CANDIDATE.json'):
            packet = dict(PACKET);packet[name] += b'\n'
            with self.assertRaises(ValueError):u.targets(packet, s.CLOUD)

    def test_fixed_hosts_and_fixed_object_names(self):
        with self.assertRaises(ValueError):u.targets(PACKET, 'foreign-host')
        for kind, i in [('foreign', 0), ('stage', -1), ('stage', 3), ('stage', True)]:
            with self.assertRaises(ValueError):u.slot(kind, i)


if __name__ == '__main__':unittest.main()
