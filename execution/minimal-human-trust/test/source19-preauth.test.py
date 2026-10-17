#!/usr/bin/env python3
"""Review-object boundary tests; no production reads or private signing material."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('source19_preauth', ROOT / 'tools/source19-preauth.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class PreauthBoundaryTest(unittest.TestCase):
    def test_relative_escape_and_sensitive_paths_refused(self):
        for name in ('../a', '/a', 'a//b', 'a/./b', 'a\\b', 'a\x00b',
                     'credentials/x.json', '.env', 'x/signing.key', 'x/a.cred'):
            with self.subTest(name=name), self.assertRaises(ValueError):
                m.relative(name)

    def test_regular_file_identity_and_ancestor_links(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'safe').mkdir()
            f = root / 'safe/a.json'
            f.write_text('{}')
            self.assertEqual(len(m.file_sha(f)), 64)
            (root / 'alias').symlink_to(root / 'safe', target_is_directory=True)
            with self.assertRaisesRegex(ValueError, 'SOURCE_LINK_REFUSED'):
                m.file_sha(root / 'alias/a.json')
            (root / 'hard').hardlink_to(f)
            with self.assertRaisesRegex(ValueError, 'SOURCE_NOT_REGULAR'):
                m.file_sha(f)

    def complete_fixture(self, root):
        package = root / 'package'
        meta = package / 'metadata'
        meta.mkdir(parents=True)
        payload = package / 'payload'
        payload.mkdir()
        public = json.loads((ROOT / 'test/fixtures/SOURCE19_PUBLIC_CONFIG.json').read_text())
        (meta / 'SOURCE_PUBLIC_CONFIG.json').write_text(json.dumps(public))
        (root / 'G1_FROZEN_SOURCE19_BASELINE.json').write_text(json.dumps({
            'configurationRevision': 19, 'publicConfigHash': m.PUBLIC, 'deliveryHash': m.DELIVERY}))
        (root / 'G4_FIRST_TRUST_READINESS.json').write_text(json.dumps({
            'human': {'realPublicKey': None}, 'enrollmentAuthority': {'realPublicKey': None}, 'signable': False}))
        (root / 'REVISION_INVENTORY.json').write_text(json.dumps({
            'acceptedRevision': 19, 'highestObservedSignedRevision': 19,
            'highestHistoricalReservedRevision': 20}))
        names = ['app/tool', 'release/stage-installer-reviewed.mjs', 'authority/code-admission.py',
                 'authority/identity-admission.py', 'packaging/minimal-human-trust-identity-admission'] + [
            'packaging/' + n for n in ['minimal-human-trust-proposal.service',
            'minimal-human-trust-publisher.service', 'minimal-human-trust-identity-admission.service',
            'org.jenn.r16.minimal-human-trust.identity-admission.policy', 'minimal-human-trust-approval.socket',
            'minimal-human-trust-approval@.service', 'minimal-human-trust-approval.desktop',
            'minimal-human-trust-first-cutover.desktop', 'org.jenn.r16.minimal-human-trust.policy']]
        inventory = {}
        for name in names:
            file = payload / name
            file.parent.mkdir(parents=True, exist_ok=True)
            file.write_text('isolated fixture')
            mode = 0o755 if name == 'app/tool' else 0o644
            file.chmod(mode)
            inventory[name] = {'sha256': m.file_sha(file), 'bytes': file.stat().st_size, 'mode': mode}
        head = 'a' * 40
        (meta / 'PAYLOAD_INVENTORY.json').write_text(json.dumps({
            'sourceHead': head, 'uniqueFiles': len(inventory), 'files': inventory}))
        (meta / 'REVIEWED_SOURCE_FREEZE.json').write_text(json.dumps({
            'sourceCommit': head, 'files': {'release/stage-installer-reviewed.mjs':
                                          inventory['release/stage-installer-reviewed.mjs']['sha256']}}))
        identity = {'/usr/lib/minimal-human-trust/authority/identity-admission.py': 'authority/identity-admission.py',
            '/usr/lib/minimal-human-trust/packaging/minimal-human-trust-identity-admission': 'packaging/minimal-human-trust-identity-admission',
            '/etc/systemd/system/minimal-human-trust-identity-admission.service': 'packaging/minimal-human-trust-identity-admission.service',
            '/usr/share/polkit-1/actions/org.jenn.r16.minimal-human-trust.identity-admission.policy': 'packaging/org.jenn.r16.minimal-human-trust.identity-admission.policy'}
        (meta / 'IDENTITY_ADMISSION_FREEZE.json').write_text(json.dumps({
            'schema': 'mht.identity-admission-code-freeze.v1', 'sourceCommit': head,
            'files': {p: inventory[n]['sha256'] for p, n in identity.items()}}))
        for role in ['app', 'bridge', 'native']:
            (meta / (role + '-manifest.json')).write_text('{}')
        return package

    def test_complete_unsigned_review_preserves_executable_mode(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            package = self.complete_fixture(root)
            prepared, blocked = m.generate(root, package)
            tool = next(r for r in prepared['targets'] if r['target'].endswith('/app/tool'))
            self.assertEqual(tool['mode'], '0755')
            wrapper = next(r for r in prepared['targets'] if r['target'] ==
                           '/usr/lib/minimal-human-trust/packaging/minimal-human-trust-identity-admission')
            self.assertEqual(wrapper['mode'], '0755')
            self.assertTrue(any(r['target'] == '/etc/minimal-human-trust/identity-admission-code.json'
                                and r['mode'] == '0600' for r in prepared['targets']))
            self.assertFalse(prepared['executable'])
            self.assertFalse(prepared['signable'])
            self.assertIsNone(prepared['timeWindow']['expiresAt'])
            self.assertFalse(blocked['signable'])
            self.assertEqual(blocked['unsignedVersionPlanning']['candidateForward'], 21)
            self.assertFalse(blocked['unsignedVersionPlanning']['oldReserved20IsAuthority'])
            self.assertIn('OWNER_SWITCH', prepared['forbiddenEffects'])
            self.assertEqual(list(root.glob('G5*')), [])

    def test_identity_freeze_must_match_actual_exact_source_files(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); package = self.complete_fixture(root)
            (package / 'metadata/IDENTITY_ADMISSION_FREEZE.json').write_text('{}')
            with self.assertRaisesRegex(ValueError, 'IDENTITY_CODE_FREEZE_DRIFT'): m.generate(root, package)

    def test_same_public_wrong_delivery_refuses_review_generation(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            package = self.complete_fixture(root)
            baseline = root / 'G1_FROZEN_SOURCE19_BASELINE.json'
            value = json.loads(baseline.read_text())
            value['deliveryHash'] = 'b' * 64
            baseline.write_text(json.dumps(value))
            with self.assertRaisesRegex(ValueError, 'SOURCE19_BASELINE_DRIFT'):
                m.generate(root, package)

    def test_payload_mode_drift_refuses_review_generation(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            package = self.complete_fixture(root)
            (package / 'payload/app/tool').chmod(0o644)
            with self.assertRaisesRegex(ValueError, 'PAYLOAD_MODE_DRIFT'):
                m.generate(root, package)

    def test_wrong_public_baseline_never_generates_approval(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            meta = root / 'package/metadata'
            meta.mkdir(parents=True)
            (meta / 'SOURCE_PUBLIC_CONFIG.json').write_text('{}')
            with self.assertRaisesRegex(ValueError, 'SOURCE19_PUBLIC_DRIFT'):
                m.generate(root, root / 'package')
            self.assertEqual(list(root.glob('G5*')), [])


if __name__ == '__main__':
    unittest.main()
