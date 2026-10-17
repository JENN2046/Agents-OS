"""Isolated identity admission tests. No root, real credentials, units or keys."""
import copy
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('identity_admission', ROOT / 'authority/identity-admission.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def authority():
    return {'schema': 'mht.identity-native-authority.v1', 'custodyModel': m.MODEL, 'nonce': 'a' * 32,
            'challengeHash': 'b' * 64, 'codeFreezeHash': 'c' * 64,
            'actor': {'pid': 123, 'startTicks': '456', 'uid': 1000}, 'targets': m.TARGETS,
            'source': {'issuerPublicKey': 'oldIssuer', 'releasePublicKey': 'oldRelease'},
            'acceptedAt': 1000, 'expiresAt': 301000, 'acceptedMonotonicNs': str(m.time.monotonic_ns()),
            'bootId': Path('/proc/sys/kernel/random/boot_id').read_text().strip()}


class Fake:
    def __init__(self):
        self.records = {}
        self.files = {}
        self.effects = []
        self.fail = None
        self.open_wrong = False
        self.drift_at = None
        self.calls = 0

    def load(self, name):
        return self.records.get(name)

    def exists(self, p):
        return p in self.files

    def record(self, name, value):
        if self.fail == name:
            raise ValueError('SIMULATED_CRASH')
        if name in self.records:
            raise ValueError('DUPLICATE_RECORD')
        self.records[name] = copy.deepcopy(value)

    def fresh(self, a):
        self.calls += 1
        if self.drift_at == self.calls:
            raise ValueError('ADMITTED_SOURCE_DRIFT')

    def seal(self, role, private, a):
        self.fresh(a)
        self.effects.append(('encrypt', role))
        if self.fail == role + '-encrypt':
            raise ValueError('FIXED_COMMAND_TIMEOUT')
        opened = m.keypair()[0] if self.open_wrong else bytearray(private)
        return b'ciphertext-' + role.encode(), opened

    def publish(self, role, encrypted, a):
        self.fresh(a)
        self.effects.append(('publish', role))
        self.files[m.TARGETS[role]] = encrypted

    def publish_source(self, value, a):
        self.fresh(a)
        self.files[m.SOURCE] = m.canonical(value)

    def historical(self, result):
        for k in m.TARGETS:
            m.need(m.sha(self.files[m.TARGETS[k]]) == result['ciphertextSha256'][k], 'SEALED_CREDENTIAL_DRIFT')
        m.need(m.sha(self.files[m.SOURCE]) == result['publicSourceSha256'], 'CUSTODY_PUBLIC_SOURCE_DRIFT')
        return dict(result, historicalReadOnly=True)


class Protocol(unittest.TestCase):
    def test_defaults_describe_no_backend_no_secret(self):
        with patch.object(m, 'FixedBackend', side_effect=AssertionError('effect')):
            r = m.main([])
        self.assertEqual(r['defaultEffects'], 0)
        self.assertEqual(r['custodyModel'], m.MODEL)
        self.assertFalse(r['humanExclusivePossession'])

    def test_real_keypair_roundtrip_and_four_distinct_keys(self):
        b = Fake()
        r = m.work(b, authority(), clock=lambda: 2000)
        self.assertEqual(r['status'], 'HOST_ADMIN_CUSTODY_SEALED_NOT_ENROLLED')
        self.assertFalse(r['enrolled'])
        self.assertFalse(r['businessAcceptance'])
        self.assertNotEqual(*r['publicKeys'].values())
        source = json.loads(b.files[m.SOURCE])
        self.assertFalse(source['civilIdentityVerified'])
        for role, row in source['keys'].items():
            from cryptography.hazmat.primitives.serialization import load_der_public_key
            p = row['keypairProof']
            load_der_public_key(m.unb64(row['publicKey'])).verify(m.unb64(p['signature']), m.canonical(p['message']))
            self.assertEqual(row['target'], m.TARGETS[role])

    def test_success_reentry_only_historical(self):
        b = Fake()
        m.work(b, authority(), clock=lambda: 2000)
        before = copy.deepcopy(b.effects)
        r = m.work(b, authority(), generate=lambda: self.fail('regenerate'), clock=lambda: 999999)
        self.assertTrue(r['historicalReadOnly'])
        self.assertEqual(before, b.effects)

    def test_existing_target_refused_before_generation(self):
        b = Fake()
        b.files[m.TARGETS['human']] = b'foreign'
        with self.assertRaisesRegex(ValueError, 'IDENTITY_TARGET_ALREADY_EXISTS'):
            m.work(b, authority(), generate=lambda: self.fail('keygen'), clock=lambda: 2000)
        self.assertEqual(b.effects, [])

    def test_partial_second_seal_cannot_regenerate_or_republish(self):
        b = Fake()
        b.fail = 'enrollment-encrypt'
        with self.assertRaisesRegex(ValueError, 'FIXED_COMMAND_TIMEOUT'):
            m.work(b, authority(), clock=lambda: 2000)
        self.assertIn(m.TARGETS['human'], b.files)
        self.assertNotIn(m.TARGETS['enrollment'], b.files)
        before = copy.deepcopy(b.effects)
        with self.assertRaisesRegex(ValueError, 'PARTIAL_SEAL_NO_REGENERATION'):
            m.work(b, authority(), generate=lambda: self.fail('regenerated'), clock=lambda: 2000)
        self.assertEqual(before, b.effects)

    def test_crash_after_keygen_intent_never_regenerates(self):
        b = Fake()
        with self.assertRaisesRegex(ValueError, 'KEYGEN_CRASH'):
            m.work(b, authority(), generate=lambda: (_ for _ in ()).throw(ValueError('KEYGEN_CRASH')), clock=lambda: 2000)
        with self.assertRaisesRegex(ValueError, 'PARTIAL_SEAL_NO_REGENERATION'):
            m.work(b, authority(), clock=lambda: 2000)
        self.assertEqual(b.effects, [])

    def test_wrong_decrypted_key_refused_before_publication(self):
        b = Fake()
        b.open_wrong = True
        with self.assertRaises(Exception):
            m.work(b, authority(), clock=lambda: 2000)
        self.assertNotIn(m.TARGETS['human'], b.files)
        self.assertNotIn('result', b.records)

    def test_duplicate_human_enrollment_public_refused(self):
        b = Fake()
        private, public = m.keypair()
        with self.assertRaisesRegex(ValueError, 'FOUR_PUBLIC_KEYS_MUST_BE_DISTINCT'):
            m.work(b, authority(), generate=lambda: (bytearray(private), public), clock=lambda: 2000)
        self.assertNotIn(m.TARGETS['enrollment'], b.files)
        private[:] = b'\0' * len(private)

    def test_old_root_public_cannot_be_generated_identity(self):
        b = Fake()
        a = authority()
        private, public = m.keypair()
        a['source']['issuerPublicKey'] = public
        with self.assertRaisesRegex(ValueError, 'FOUR_PUBLIC_KEYS_MUST_BE_DISTINCT'):
            m.work(b, a, generate=lambda: (private, public), clock=lambda: 2000)
        self.assertEqual(b.effects, [])

    def test_expiry_before_keygen_no_effects(self):
        b = Fake()
        with self.assertRaisesRegex(ValueError, 'AUTHORITY_EXPIRED'):
            m.work(b, authority(), generate=lambda: self.fail('keygen'), clock=lambda: 301000)
        self.assertEqual(b.effects, [])
        self.assertEqual(b.records, {})

    def test_wallclock_rollback_cannot_extend_native_window(self):
        b = Fake()
        a = authority()
        a['acceptedMonotonicNs'] = str(m.time.monotonic_ns() - 300001000000)
        with self.assertRaisesRegex(ValueError, 'AUTHORITY_EXPIRED'):
            m.work(b, a, generate=lambda: self.fail('keygen'), clock=lambda: 2000)
        self.assertEqual(b.effects, [])

    def test_cross_boot_authority_cannot_be_reused(self):
        b = Fake()
        a = authority()
        a['bootId'] = 'foreign-boot'
        with self.assertRaisesRegex(ValueError, 'AUTHORITY_EXPIRED'):
            m.work(b, a, generate=lambda: self.fail('keygen'), clock=lambda: 2000)
        self.assertEqual(b.effects, [])

    def test_source_or_public_drift_before_second_key_no_second_effect(self):
        b = Fake()
        b.drift_at = 5  # Initial, human pre-key, seal, publish, enrollment pre-key.
        with self.assertRaisesRegex(ValueError, 'ADMITTED_SOURCE_DRIFT'):
            m.work(b, authority(), clock=lambda: 2000)
        self.assertEqual(b.effects, [('encrypt', 'human'), ('publish', 'human')])
        self.assertNotIn('result', b.records)

    def test_final_receipt_write_failure_not_success(self):
        b = Fake()
        b.fail = 'result'
        with self.assertRaisesRegex(ValueError, 'SIMULATED_CRASH'):
            m.work(b, authority(), clock=lambda: 2000)
        self.assertIn(m.SOURCE, b.files)
        with self.assertRaisesRegex(ValueError, 'PARTIAL_SEAL_NO_REGENERATION'):
            m.work(b, authority(), clock=lambda: 2000)

    def test_historical_public_drift_refused(self):
        b = Fake()
        m.work(b, authority(), clock=lambda: 2000)
        b.files[m.SOURCE] += b' '
        with self.assertRaisesRegex(ValueError, 'CUSTODY_PUBLIC_SOURCE_DRIFT'):
            m.work(b, authority(), clock=lambda: 2000)


class PublicSourceAndOS(unittest.TestCase):
    def source_fixture(self):
        pub = json.loads((ROOT / 'test/fixtures/SOURCE19_PUBLIC_CONFIG.json').read_bytes())
        envelope = json.loads((ROOT / 'test/fixtures/SOURCE19_DELIVERY_ENVELOPE.json').read_bytes())
        config = {'kind': 'r16.owner.configuration.v1', 'connectionNonce': 7,
                  'delivery': {'revision': 19, 'envelope': envelope,
                               'hash': m.digest({'publicConfig': pub, 'control': envelope['body']['control'], 'connectionNonce': 7})}}
        return pub, config

    def test_actual_public_signed_source19_fixture(self):
        pub, config = self.source_fixture()
        r = m.source19(lambda p, *_: m.canonical(pub if p == m.PUBLIC_PATH else {'data': config}))
        self.assertEqual(r['revision'], 19)
        self.assertEqual(r['publicConfigDigest'], m.PUB)

    def test_same_public_different_revision_cache_refused(self):
        pub, config = self.source_fixture()
        config['delivery']['revision'] = 20
        with self.assertRaisesRegex(ValueError, 'SOURCE19_DELIVERY_DRIFT'):
            m.source19(lambda p, *_: m.canonical(pub if p == m.PUBLIC_PATH else {'data': config}))

    def test_same_revision_wrong_nonce_cache_refused(self):
        pub, config = self.source_fixture()
        config['connectionNonce'] = 8
        with self.assertRaisesRegex(ValueError, 'OWNER_CACHE_DRIFT'):
            m.source19(lambda p, *_: m.canonical(pub if p == m.PUBLIC_PATH else {'data': config}))

    def test_private_only_stdin_and_captured_never_args_env(self):
        calls = []
        private = b'test-only-private-material'
        a = authority()
        b = m.FixedBackend()
        def command(argv, data=None, **kw):
            calls.append((argv, data))
            self.assertNotIn(private.decode(), ' '.join(argv))
            return b'encrypted' if 'encrypt' in argv else private
        with patch.object(b, 'fresh'), patch.object(m, 'checked_command', side_effect=command):
            sealed, opened = b.seal('human', private, a)
        self.assertEqual(calls[0][1], private)
        self.assertEqual(calls[0][0][-2:], ['-', '-'])
        self.assertEqual(calls[1][1], sealed)
        self.assertEqual(bytes(opened), private)

    def test_timeout_fixed_code_no_stderr_exposure(self):
        with patch.object(m.subprocess, 'run', side_effect=subprocess.TimeoutExpired(['fixed'], 1, stderr=b'secret')):
            with self.assertRaisesRegex(ValueError, '^FIXED_COMMAND_TIMEOUT$'):
                m.checked_command(['/usr/bin/systemd-creds'])

    def test_nonroot_native_refused_without_prompt_or_command(self):
        with patch.object(m.os, 'getuid', return_value=1000), patch.object(m.os, 'geteuid', return_value=1000), \
             patch.object(m, 'checked_command', side_effect=AssertionError('command')):
            with self.assertRaisesRegex(ValueError, 'LOCAL_JENN_ROOT_REQUIRED'):
                m.native_identity()

    def test_foreign_worker_not_allowed_even_as_mock_root(self):
        with patch.object(m.os, 'getuid', return_value=0), patch.object(m.os, 'geteuid', return_value=0), \
             patch.object(m.socket, 'gethostname', return_value=m.HOST), patch.object(m.Path, 'read_text', return_value='0::/user.slice/fixture'):
            with self.assertRaisesRegex(ValueError, 'FIXED_ONESHOT_REQUIRED'):
                m.worker_admission(Fake())

    def test_unit_no_swap_no_core_no_existing_key_load(self):
        text = (ROOT / 'packaging' / m.UNIT).read_text()
        for line in ('MemorySwapMax=0', 'LimitCORE=0', 'Restart=no', 'StandardOutput=null', 'StandardError=null'):
            self.assertIn(line, text.splitlines())
        self.assertNotIn('LoadCredential', text)
        self.assertNotIn('StateDirectory=', text)  # Cannot create a state directory before native admission.

    def test_atomic_noreplace_preserves_existing_and_no_partial_final(self):
        with tempfile.TemporaryDirectory(prefix='mht-identity-test-') as tmp:
            b = m.FixedBackend(clock=lambda: 2000)
            b.authority = authority()
            b.mkdir = lambda *_: None
            p = str(Path(tmp) / 'public-record')
            b.put(p, b'first')
            with self.assertRaisesRegex(ValueError, 'EXCLUSIVE_PUBLICATION_REFUSED'):
                b.put(p, b'second')
            self.assertEqual(Path(p).read_bytes(), b'first')
            self.assertEqual(Path(p).stat().st_nlink, 1)
            self.assertEqual(Path(p + '.pending').read_bytes(), b'second')

    def test_expired_last_publish_guard_leaves_only_pending(self):
        with tempfile.TemporaryDirectory(prefix='mht-identity-test-') as tmp:
            b = m.FixedBackend(clock=lambda: 2000)
            b.authority = authority()
            b.mkdir = lambda *_: None
            p = str(Path(tmp) / 'ciphertext')
            calls = []
            def guard():
                calls.append(1)
                if len(calls) == 3:
                    raise ValueError('EXPIRED')
            with self.assertRaisesRegex(ValueError, 'EXPIRED'):
                b.put(p, b'ciphertext-only', guard)
            self.assertFalse(Path(p).exists())
            self.assertTrue(Path(p + '.pending').exists())

    def test_expired_before_pending_create_does_not_write(self):
        with tempfile.TemporaryDirectory(prefix='mht-identity-test-') as tmp:
            b = m.FixedBackend(clock=lambda: 301000)
            b.authority = authority()
            b.mkdir = lambda *_: None
            p = str(Path(tmp) / 'ciphertext')
            with self.assertRaisesRegex(ValueError, 'AUTHORITY_EXPIRED'):
                b.put(p, b'ciphertext-only')
            self.assertEqual(list(Path(tmp).iterdir()), [])

    def test_expiry_after_pending_open_refuses_write_and_final(self):
        with tempfile.TemporaryDirectory(prefix='mht-identity-test-') as tmp:
            ticks = iter((2000, 301000))
            b = m.FixedBackend(clock=lambda: next(ticks))
            b.authority = authority()
            b.mkdir = lambda *_: None
            p = str(Path(tmp) / 'ciphertext')
            with self.assertRaisesRegex(ValueError, 'AUTHORITY_EXPIRED'):
                b.put(p, b'ciphertext-only')
            self.assertFalse(Path(p).exists())
            self.assertEqual(Path(p + '.pending').read_bytes(), b'')

    def test_description_subprocess_is_ordinary_and_zero_effect(self):
        r = subprocess.run([sys.executable, '-I', '-B', str(ROOT / 'authority/identity-admission.py')], capture_output=True, check=True)
        self.assertEqual(json.loads(r.stdout)['defaultEffects'], 0)
        self.assertEqual(r.stderr, b'')


class NativePrompt(unittest.TestCase):
    def setUp(self):
        self.actor = {'uid': 1000, 'pid': 123, 'startTicks': '456', 'session': '3', 'tty': '/dev/pts/1'}
        self.c = m.challenge(authority()['source'], 'c' * 64, self.actor)

    def prompt(self, raw, second=None, ready=True):
        chars = iter(bytes([b]) for b in raw)
        # Only the native prompt is isolated: actual generation and root CLI are
        # never invoked, and no confirmation is sent to a production terminal.
        with patch.object(m, 'native_identity', side_effect=[(90, self.actor), (91, second or self.actor)]), \
             patch.object(m.os, 'read', side_effect=lambda *_: next(chars, b'')), \
             patch.object(m.os, 'write'), patch.object(m.os, 'close'), \
             patch('select.select', return_value=([90] if ready else [], [], [])), patch.object(m, 'now', return_value=7000):
            return m.approve_native(self.c)

    def test_decline_exact_target_no_authority(self):
        with self.assertRaisesRegex(ValueError, 'NATIVE_CONFIRMATION_CANCELLED'):
            self.prompt(b'no\n')

    def test_partial_or_prefix_confirmation_refused(self):
        with self.assertRaisesRegex(ValueError, 'NATIVE_CONFIRMATION_CANCELLED'):
            self.prompt(('ADMIT HOST_ADMIN_CUSTODY ' + m.digest(self.c)[:16] + '\n').encode())

    def test_confirmation_timeout_no_authority(self):
        with self.assertRaisesRegex(ValueError, 'NATIVE_CONFIRMATION_TIMEOUT'):
            self.prompt(b'', ready=False)

    def test_authority_minted_after_complete_line_and_recheck(self):
        a = self.prompt(('ADMIT HOST_ADMIN_CUSTODY ' + m.digest(self.c) + '\n').encode())
        self.assertEqual((a['acceptedAt'], a['expiresAt']), (7000, 307000))
        self.assertEqual(a['challengeHash'], m.digest(self.c))

    def test_foreground_identity_drift_during_read_refuses_authority(self):
        with self.assertRaisesRegex(ValueError, 'NATIVE_ACTOR_DRIFT'):
            self.prompt(('ADMIT HOST_ADMIN_CUSTODY ' + m.digest(self.c) + '\n').encode(), dict(self.actor, session='4'))


class NativeIdentityGuards(unittest.TestCase):
    def invoke(self, uid=1000, foreground=50, remote='no', mixed=False):
        row = SimpleNamespace(st_mode=m.stat.S_IFCHR | 0o620, st_dev=1, st_ino=2,
                              st_rdev=123, st_uid=uid, st_gid=5)
        other = SimpleNamespace(**vars(row))
        other.st_ino = 3
        props = ('User=1000\nName=jenn\nActive=yes\nRemote=' + remote + '\nType=wayland\nClass=user\nState=active\n').encode()
        with patch.object(m.os, 'getuid', return_value=0), patch.object(m.os, 'geteuid', return_value=0), \
             patch.dict(m.os.environ, {'PKEXEC_UID': '1000'}), patch.object(m.socket, 'gethostname', return_value=m.HOST), \
             patch.object(m.Path, 'read_text', return_value='ID=ubuntu\n'), \
             patch.object(m.pwd, 'getpwuid', return_value=SimpleNamespace(pw_name='jenn', pw_gid=1000)), \
             patch.object(m.os, 'fstat', side_effect=lambda fd: other if mixed and fd == 2 else row), \
             patch.object(m.os, 'ttyname', return_value='/dev/pts/42'), patch.object(m.os, 'isatty', return_value=True), \
             patch.object(m.os, 'open', side_effect=[10, 11, 12, 13]), patch.object(m.os, 'close'), \
             patch.object(m.os, 'tcgetpgrp', return_value=foreground), patch.object(m.os, 'getpgrp', return_value=50), \
             patch.object(m, 'checked_command', side_effect=[b'3\n', props]), patch.object(m, 'start_ticks', return_value='456'):
            return m.native_identity()

    def test_actual_named_pty_and_local_graphical_subject_accepted(self):
        fd, actor = self.invoke()
        self.assertEqual(fd, 13)
        self.assertEqual(actor['subject'], 'local-human:1000')

    def test_wrong_pty_owner_refused(self):
        with self.assertRaisesRegex(ValueError, 'PTY_IDENTITY_REFUSED'):
            self.invoke(uid=1001)

    def test_mixed_stdio_pty_refused(self):
        with self.assertRaisesRegex(ValueError, 'PTY_IDENTITY_REFUSED'):
            self.invoke(mixed=True)

    def test_background_group_refused(self):
        with self.assertRaisesRegex(ValueError, 'NATIVE_FOREGROUND_REQUIRED'):
            self.invoke(foreground=51)

    def test_remote_graphical_session_refused(self):
        with self.assertRaisesRegex(ValueError, 'LOCAL_ACTIVE_GUI_REQUIRED'):
            self.invoke(remote='yes')


if __name__ == '__main__':
    unittest.main()
