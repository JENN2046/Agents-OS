"""Driver + real private inode relocation + unchanged signed R8 reader.

Only the systemd/cgroup control observations are isolated adapters. File reads,
renameat2(NOREPLACE), parent fsync and the complete ledger verifier are real,
under BackendTests' synthetic signed TemporaryDirectory fixture. This does not
exercise native admission or authorize production operations.
"""
import copy
import importlib.util
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
_fixture_spec = importlib.util.spec_from_file_location(
    'quarantine_integration_backend_fixture', HERE / 'test_backend.py')
fixture = importlib.util.module_from_spec(_fixture_spec)
sys.modules[_fixture_spec.name] = fixture
_fixture_spec.loader.exec_module(fixture)

D = fixture.load('quarantine_integration_driver', fixture.HERE / 'driver.py')


class MemoryJournal:
    value = None

    def read(self):
        return copy.deepcopy(self.value)

    def write(self, value):
        self.value = copy.deepcopy(value)


class IsolatedControls:
    environment = 'ISOLATED_TEST'

    def __init__(self, case):
        self.case = case
        self.effects = []

    def __getattr__(self, name):
        return getattr(self.case.backend, name)

    def inspect_recovery(self, target):
        return copy.deepcopy(self.case.observation)

    def fence(self, target, owner):
        self.effects.append('fence')
        self.case.observation['fenceOwner'] = owner

    def freeze(self, target, owner):
        self.effects.append('freeze')
        self.case.freeze()

    def unfreeze(self, target, owner):
        self.effects.append('unfreeze')
        self.case.observation.update(frozen=False, freezeRequested=False,
                                     freezeOwner=None)

    def unfence(self, target, owner):
        self.effects.append('unfence')
        self.case.observation['fenceOwner'] = None

    def quarantine(self, *args):
        self.effects.append('quarantine')
        return self.case.backend.quarantine(*args)

    def restore(self, *args):
        self.effects.append('restore')
        return self.case.backend.restore(*args)


class IntegrationTests(unittest.TestCase):
    def setUp(self):
        self.case = fixture.BackendTests()
        self.addCleanup(self.case.doCleanups)
        self.case.setUp()
        self.case.stack.enter_context(patch.object(D, 'ARTIFACT', self.case.expected))
        self.case.stack.enter_context(patch.object(D, 'TARGET', self.case.target))
        self.case.observation.update(activeState='active', subState='running')
        self.approval = {
            'schema': D.SCHEMA, 'environment': 'ISOLATED_TEST',
            'approvalId': 'isolated-integration-review',
            'approvedAt': 1000, 'deadline': 301000,
            'policyProposalHash': D.POLICY_HASH,
            'sourceCapsuleHash': 'a' * 64, 'capsuleHash': 'b' * 64,
            'target': copy.deepcopy(self.case.target),
            'artifact': {'path': D.ARTIFACT_PATH, **self.case.expected},
            'allowExactEmptyArtifactQuarantine': True,
            'acceptPossibleInMemoryStorePoisoning': True,
            'drainStatus': 'UNPROVEN',
        }
        self.case.owner = D.digest(self.approval)
        self.case.cap.approval_hash = self.case.owner
        self.backend = IsolatedControls(self.case)
        self.journal = MemoryJournal()
        self.driver = D.Driver(self.backend, self.journal, lambda: 1000)

    def normal_bytes(self):
        return {str(path.relative_to(self.case.store)): path.read_bytes()
                for path in self.case.store.rglob('*')
                if path.is_file() and path != self.case.artifact}

    def recovery_intent(self):
        return {
            'schema': D.RECOVERY_SCHEMA,
            'intentId': 'isolated-fresh-inverse-review',
            'approvalHash': D.digest(self.approval),
            'targetHash': D.digest(self.case.target),
            'scope': 'RESTORE_ORIGINAL_EMPTY_ARTIFACT',
            'approvedAt': 1000, 'deadline': 121000,
        }

    def assert_runtime_restored(self):
        self.assertFalse(self.case.observation['frozen'])
        self.assertFalse(self.case.observation['freezeRequested'])
        self.assertIsNone(self.case.observation['fenceOwner'])
        self.assertEqual(self.case.observation['members'], [self.case.target['pid']])

    def test_full_forward_and_fresh_inverse_preserve_current_normal_bytes(self):
        before = self.normal_bytes()
        forward = self.driver.run(self.approval)
        self.assertEqual(forward['status'], D.TERMINAL[0])
        self.assertTrue(forward['ledgerValidatedWhileFrozen'])
        self.assertEqual(self.normal_bytes(), before)
        self.assertFalse(self.case.artifact.exists())
        self.assert_runtime_restored()
        recorded_forward = copy.deepcopy(self.journal.value['receipt'])

        # Model a legitimate original-App write after thaw. Inverse must use a
        # fresh authenticated baseline and preserve these newer normal bytes.
        host = self.case.store / 'state.json'
        value = fixture.L.parse(host.read_bytes())
        value['revision'] += 1
        host.write_bytes(fixture.f.raw(value))
        current = self.normal_bytes()
        inverse = self.driver.recover(self.approval, self.recovery_intent())

        self.assertEqual(inverse['status'], D.TERMINAL[2])
        self.assertEqual(self.normal_bytes(), current)
        self.assertEqual(self.journal.value['forwardReceipt'], recorded_forward)
        self.assertIsNotNone(inverse['inverseBeforeManifestHash'])
        self.assertEqual(self.case.artifact.stat().st_ino, self.case.expected['ino'])
        self.assertEqual(self.backend.effects.count('quarantine'), 1)
        self.assertEqual(self.backend.effects.count('restore'), 1)
        self.assertFalse(inverse['signalOrRestartPerformed'])
        self.assertEqual(inverse['drainStatus'], 'UNPROVEN')
        self.assertEqual(inverse['inMemoryStoreHealth'], 'UNPROVEN')
        self.assert_runtime_restored()

    def test_real_rename_lost_reply_reentry_observes_until_fresh_inverse(self):
        before = self.normal_bytes()
        real_sync = fixture.b.os.fsync
        calls = []

        def lose_reply_after_move(fd):
            calls.append(fd)
            # First fsync persists the new quarantine directory's parent.
            # Second occurs only after the real atomic rename has succeeded.
            if len(calls) == 2:
                raise OSError('isolated lost post-rename reply')
            real_sync(fd)

        with patch.object(fixture.b.os, 'fsync', side_effect=lose_reply_after_move):
            result = self.driver.run(self.approval)
        self.assertEqual(result['status'], 'RECOVERY_REQUIRED')
        self.assertTrue(result['quarantineAttemptConsumed'])
        self.assertFalse(self.case.artifact.exists())
        self.assertEqual(self.case.backend.inspect_artifact(
            self.case.target, self.case.owner)['location'], 'QUARANTINE')
        self.assertTrue(self.case.observation['frozen'])
        self.assertEqual(self.case.observation['fenceOwner'], self.case.owner)
        self.assertEqual(self.normal_bytes(), before)

        effects = list(self.backend.effects)
        observed = self.driver.run(self.approval)
        self.assertEqual(observed['status'], 'RECOVERY_REQUIRED')
        self.assertEqual(observed['artifactLocation'], 'QUARANTINE')
        self.assertEqual(self.backend.effects, effects)

        restored = self.driver.recover(self.approval, self.recovery_intent())
        self.assertEqual(restored['status'], D.TERMINAL[1])
        self.assertEqual(self.case.artifact.stat().st_ino, self.case.expected['ino'])
        self.assertEqual(self.normal_bytes(), before)
        self.assertEqual(self.backend.effects.count('quarantine'), 1)
        self.assertEqual(self.backend.effects.count('restore'), 1)
        self.assert_runtime_restored()


if __name__ == '__main__':
    unittest.main()
