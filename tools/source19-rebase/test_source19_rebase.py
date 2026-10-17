"""Disposable Git/base/package fixtures only; no live ledger/keys/service/network."""
import contextlib
import copy
import importlib.util
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


B = load('source19_builder_tested', HERE / 'build_unsigned.py')
V = load('source19_independent_tested', HERE / 'verify_unsigned.py')


class RebaseFixture(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='source19-isolated-')
        self.addCleanup(self.tmp.cleanup)
        root = Path(self.tmp.name)
        self.repo, self.base, self.output = root / 'repo', root / 'base', root / 'candidate'
        self.public = root / 'public.json'
        self.bridge = root / 'original-bridge-manifest.json'
        self.repo.mkdir(mode=0o755)
        self.base.mkdir(mode=0o755)
        product = HERE.parents[1] / 'execution/minimal-human-trust'
        # Public tracked source fixtures; none is imported or executed.
        self.content = {n: (product / n).read_bytes() for n in B.BASE_REPAIRS}
        self.content.update({'src/shared.mjs': b'export const shared=1;\n', 'bridge/entry.mjs': b'export const bridge=1;\n', 'host/helper.py': b'# fixture executable, never executed\n'})
        for name, raw in self.content.items():
            self.emit(self.base / name, raw, 0o755 if name == 'host/helper.py' else 0o644)
        self.originals = {
            'app': self.role('app', 'app/app-runner.mjs', ('app/app-runner.mjs', 'app/workspace-host.mjs', 'src/shared.mjs')),
            'bridge': self.role('bridge', 'bridge/entry.mjs', ('bridge/entry.mjs', 'src/shared.mjs')),
            'native': self.role('native', 'host/workspace-dispatcher.mjs', ('host/workspace-dispatcher.mjs', 'host/helper.py', 'src/shared.mjs'))}
        for role, path in [('app', self.base / 'app-manifest.json'), ('native', self.base / 'native-manifest.json'), ('bridge', self.bridge)]:
            self.emit(path, (B.canonical(self.originals[role]) + '\n').encode())
        self.emit(self.base / '.maintenance-capsule.json', b'{"syntheticRootMarker":true}', 0o600)
        self.versions = {r: B.digest(m) for r, m in self.originals.items()}
        self.pub = {'versions': self.versions, 'release': {'body': {'id': B.SOURCE_RELEASE, 'versions': self.versions}, 'signature': 'SYNTHETIC_NOT_AUTHORITY'}, 'grant': {'body': {'id': 'r16-projects-daily'}, 'signature': 'SYNTHETIC_NOT_AUTHORITY'}}
        self.emit(self.public, B.canonical(self.pub).encode())
        self.overlay = dict(self.content)
        for name in ('src/systemd-credentials.mjs', 'src/lease-core.mjs', 'src/control-clock.mjs', 'src/runtime-business-stop.mjs'):
            self.overlay[name] = (product / name).read_bytes()
        self.overlay.update({'authority/fixture-importer.mjs': b"import {next} from '../migration/fixture-next.mjs';\n", 'migration/fixture-next.mjs': b"export {baseline as next} from '../authority/source-baseline.mjs';\n", 'authority/source-baseline.mjs': b'export const baseline=19;\n'})
        self.overlay.update({'human/new-helper.mjs': b'export const fixture=1;\n', 'release/publisher-bootstrap.mjs': b"export const REVIEWED_SOURCE_FILES=Object.freeze(['src/shared.mjs','release/publisher-bootstrap.mjs']);\n"})
        for name, raw in self.overlay.items():
            self.emit(self.repo / B.PRODUCT / name, raw, 0o755 if name == 'host/helper.py' else 0o644)
        self.emit(self.repo / 'unrelated.txt', b'not a production component\n')
        self.git('init', '-q')
        self.git('config', 'user.name', 'Synthetic fixture')
        self.git('config', 'user.email', 'synthetic@invalid.example')
        self.commit()
        self.stack = contextlib.ExitStack()
        self.addCleanup(self.stack.close)
        repairs = {n: B.sha(self.content[n]) for n in B.BASE_REPAIRS}
        for module, name, value in [(B, 'PUBLIC_DIGEST', B.digest(self.pub)), (V, 'PUBLIC', B.digest(self.pub)), (B, 'VERSIONS', self.versions), (V, 'VERSIONS', self.versions), (B, 'BRIDGE_MANIFEST', self.bridge), (V, 'BRIDGE', self.bridge), (B, 'BASE_REPAIRS', repairs), (V, 'BASE_REPAIRS', repairs)]:
            self.stack.enter_context(patch.object(module, name, value))

    def emit(self, path, raw, mode=0o644):
        path.parent.mkdir(parents=True, exist_ok=True, mode=0o755)
        parent = path.parent
        while parent.is_relative_to(Path(self.tmp.name)):
            parent.chmod(0o755)
            if parent == Path(self.tmp.name):
                break
            parent = parent.parent
        path.write_bytes(raw)
        path.chmod(mode)

    def git(self, *args):
        return subprocess.check_output(('/usr/bin/git', '-c', 'core.hooksPath=/dev/null', '-c', 'commit.gpgsign=false', '-C', str(self.repo), *args), stderr=subprocess.DEVNULL)

    def commit(self):
        self.git('add', '.')
        self.git('commit', '-qm', 'disposable fixture')
        self.head = self.git('rev-parse', 'HEAD').decode().strip()

    def role(self, role, entry, names):
        return {'schema': 'r16.runtime-code.v1', 'role': role, 'entry': entry, 'files': {n: B.sha(self.content[n]) for n in names}}

    def build(self, plan=False):
        self.result = B.build(self.repo, self.base, self.output, self.public, self.head, plan)
        return self.result

    def verify(self, live=True):
        return V.verify(self.output, self.result['inventorySha256'], self.head, self.repo if live else None, self.base if live else None)

    def metadata(self, name):
        return json.loads((self.output / 'metadata' / name).read_bytes())

    def rewrite(self, name, mutate):
        obj = self.metadata(name)
        mutate(obj)
        (self.output / 'metadata' / name).write_text(B.canonical(obj) + '\n')

    def test_complete_real_builder_and_independent_live_verifier(self):
        r = self.build()
        v = self.verify()
        self.assertEqual(v['status'], 'PASS_UNSIGNED_PACKAGE_WITH_LIVE_PROVENANCE')
        self.assertEqual(v['liveProvenance']['exactHeadOverlayFilesVerified'], len(self.overlay))
        self.assertEqual(self.metadata('ROLE_MANIFESTS.json')['artifacts']['bridge']['entry'], self.originals['bridge']['entry'])
        self.assertFalse((self.base / 'bridge-manifest.json').exists())
        self.assertEqual(self.metadata('PROVENANCE.json')['sourceRoleManifestPaths']['bridge'], str(self.bridge))
        self.assertEqual(r['metadataFiles'], 13)
        self.assertIsNone(r['plannedConfigurationRevision'])
        self.assertIsNone(r['issuedAt'])
        self.assertFalse(r['reservedRevision20Authorized'])
        self.assertFalse(r['maySign'])
        self.assertEqual((self.output / 'payload/host/helper.py').stat().st_mode & 0o7777, 0o755)

    def test_plan_only_does_not_create_output_and_does_not_open_root_marker(self):
        original = B.read
        def guarded(path):
            self.assertNotEqual(Path(path).name, '.maintenance-capsule.json')
            return original(path)
        with patch.object(B, 'read', side_effect=guarded):
            result = self.build(True)
        self.assertFalse(result['outputCreated'])
        self.assertFalse(self.output.exists())

    def test_wrong_public19_or_wrong_base_manifest_refuses(self):
        self.public.write_text('{}')
        with self.assertRaisesRegex(B.Refused, 'PUBLIC19_DIGEST'):
            self.build()
        self.public.write_text(B.canonical(self.pub))
        path = self.base / 'app-manifest.json'
        value = json.loads(path.read_text())
        value['entry'] = 'src/shared.mjs'
        path.write_text(B.canonical(value))
        with self.assertRaisesRegex(B.Refused, 'ROLE_MANIFEST_DRIFT'):
            self.build()
        self.assertFalse(self.output.exists())

    def test_corrupt_overlaid_base_file_is_still_checked_before_overlay(self):
        (self.base / 'app/workspace-host.mjs').write_bytes(b'old or corrupt base')
        with self.assertRaisesRegex(B.Refused, 'PAYLOAD_BYTES_OR_MODE'):
            self.build()

    def test_extra_base_file_or_empty_directory_is_refused(self):
        extra = self.base / 'foreign'
        extra.mkdir()
        extra.chmod(0o755)
        with self.assertRaisesRegex(B.Refused, 'FILE_SET'):
            self.build()
        extra.rmdir()
        extra.write_bytes(b'foreign')
        with self.assertRaisesRegex(B.Refused, 'FILE_SET'):
            self.build()

    def test_clean_exact_head_and_output_no_overwrite(self):
        path = self.repo / 'unrelated.txt'
        path.write_bytes(b'dirty')
        with self.assertRaisesRegex(B.Refused, 'CLEAN_EXACT_HEAD'):
            self.build()
        self.git('checkout', '--', 'unrelated.txt')
        self.output.mkdir()
        with self.assertRaisesRegex(B.Refused, 'NEW_ISOLATED_OUTPUT'):
            self.build()
        self.assertEqual(list(self.output.iterdir()), [])

    def test_base_symlink_and_unsafe_mode_refuse(self):
        path = self.base / 'src/shared.mjs'
        original = path.read_bytes()
        path.unlink()
        path.symlink_to(self.repo / B.PRODUCT / 'src/shared.mjs')
        with self.assertRaises(B.Refused):
            self.build()
        path.unlink()
        self.emit(path, original, 0o666)
        with self.assertRaisesRegex(B.Refused, 'PAYLOAD_BYTES_OR_MODE'):
            self.build()

    def test_app_and_native_repairs_cannot_be_replaced_by_clean_older_sources(self):
        for name, marker in [('app/workspace-host.mjs', 'await drainWork();'), ('host/workspace-dispatcher.mjs', 'projects.every('), ('app/app-runner.mjs', 'host.shutdown()')]:
            path = self.repo / B.PRODUCT / name
            raw = path.read_bytes()
            self.assertIn(marker.encode(), raw)
            path.write_bytes(raw.replace(marker.encode(), b'/* broken fixture */', 1))
            self.commit()
            with self.subTest(name=name), self.assertRaises(B.Refused):
                self.build()
            path.write_bytes(raw)
            self.commit()

    def test_r17_additions_outside_physical_repair_are_preserved(self):
        path = self.repo / B.PRODUCT / 'app/workspace-host.mjs'
        path.write_bytes(path.read_bytes() + b'\n// isolated additional R17 business-stop code marker\n')
        self.commit()
        self.build()
        self.assertIn(b'additional R17', (self.output / 'payload/app/workspace-host.mjs').read_bytes())
        self.assertTrue(self.verify()['sourceRepairGuardsPreserved'])

    def test_payload_hash_and_mode_tamper_refuse(self):
        self.build()
        path = self.output / 'payload/host/helper.py'
        path.chmod(0o644)
        with self.assertRaisesRegex(ValueError, 'PAYLOAD_BYTES_OR_MODE'):
            self.verify(False)
        path.chmod(0o755)
        path.write_bytes(b'tampered')
        with self.assertRaisesRegex(ValueError, 'PAYLOAD_BYTES_OR_MODE'):
            self.verify(False)

    def test_missing_extra_empty_directory_symlink_and_hardlink_refuse(self):
        self.build()
        root = self.output / 'foreign'
        root.mkdir()
        root.chmod(0o755)
        with self.assertRaisesRegex(ValueError, 'EXACT_FILE_OR_DIRECTORY'):
            self.verify(False)
        root.rmdir()
        root.symlink_to(self.output / 'payload/src/shared.mjs')
        with self.assertRaises(ValueError):
            self.verify(False)
        root.unlink()
        os.link(self.output / 'payload/src/shared.mjs', root)
        with self.assertRaises(ValueError):
            self.verify(False)
        root.unlink()
        (self.output / 'payload/src/shared.mjs').unlink()
        with self.assertRaisesRegex(ValueError, 'EXACT_FILE_OR_DIRECTORY'):
            self.verify(False)

    def test_binding_role_manifest_and_unsigned_authority_tamper_refuse(self):
        self.build()
        for name, mutate in [('LOCAL_FILE_BINDINGS.json', lambda v: v['files'].pop()), ('ROLE_MANIFESTS.json', lambda v: v['artifacts']['app']['files'].clear()), ('UNSIGNED_CONTENT.json', lambda v: v.update(maySign=True))]:
            path = self.output / 'metadata' / name
            raw = path.read_bytes()
            self.rewrite(name, mutate)
            with self.subTest(name=name), self.assertRaises(ValueError):
                self.verify(False)
            path.write_bytes(raw)

    def test_independent_verifier_detects_repair_even_if_collector_guard_is_bypassed(self):
        guards = B.repair_guards({n: (raw, 0o644) for n, raw in self.content.items()}, {n: (raw, 0o644) for n, raw in self.overlay.items()})
        path = self.repo / B.PRODUCT / 'app/workspace-host.mjs'
        path.write_bytes(path.read_bytes().replace(b'await drainWork();', b'/* no drain */', 1))
        self.commit()
        with patch.object(B, 'repair_guards', return_value=guards):
            self.build()
        with self.assertRaisesRegex(ValueError, 'PHYSICAL_SHUTDOWN_OR_RECOVERY_REPAIR_LOST'):
            self.verify(False)

    def test_transitive_relative_imports_are_bound_in_every_selecting_role(self):
        self.build()
        files = self.metadata('ROLE_MANIFESTS.json')['artifacts']['app']['files']
        self.assertIn('authority/fixture-importer.mjs', files)
        self.assertIn('migration/fixture-next.mjs', files)
        self.assertIn('authority/source-baseline.mjs', files)
        self.assertTrue(self.verify(False)['controlledStaticRelativeImportClosureVerified'])

    def test_self_consistent_role_versions_cannot_omit_transitive_dependency(self):
        self.build()
        packet = self.metadata('ROLE_MANIFESTS.json')
        packet['artifacts']['app']['files'].pop('migration/fixture-next.mjs')
        (self.output / 'metadata/ROLE_MANIFESTS.json').write_text(B.canonical(packet) + '\n')
        (self.output / 'metadata/app-manifest.json').write_text(B.canonical(packet['artifacts']['app']) + '\n')
        self.rewrite('UNSIGNED_CONTENT.json', lambda v: (v['targetVersions'].update(app=B.digest(packet['artifacts']['app'])), v['roleCounts'].update(app=len(packet['artifacts']['app']['files'])), v.update(roleBindings=v['roleBindings'] - 1)))
        self.rewrite('LOCAL_FILE_BINDINGS.json', lambda v: v.update(files=[r for r in v['files'] if not (r['role']=='app' and r['artifactPath']=='migration/fixture-next.mjs')]))
        with self.assertRaisesRegex(ValueError, 'TARGET_ROLE_BINDINGS'):
            self.verify(False)

    def test_missing_relative_dependency_fails_before_output(self):
        path = self.repo / B.PRODUCT / 'authority/fixture-importer.mjs'
        path.write_bytes(b"import '../migration/not-present.mjs';\n")
        self.commit()
        with self.assertRaisesRegex(B.Refused, 'RELATIVE_DEPENDENCY_NOT_IN_VERIFIED_SOURCE_UNION'):
            self.build()
        self.assertFalse(self.output.exists())

    def test_external_head_inventory_pin_and_live_overlay_are_not_self_authorized(self):
        self.build()
        with self.assertRaisesRegex(ValueError, 'EXTERNAL_INVENTORY_SHA'):
            V.verify(self.output, '0' * 64, self.head)
        with self.assertRaisesRegex(ValueError, 'INVENTORY_SCOPE'):
            V.verify(self.output, self.result['inventorySha256'], '0' * 40)
        old_head = self.head
        self.git('rm', '-q', '--', B.PRODUCT + 'human/new-helper.mjs')
        self.commit()
        with self.assertRaisesRegex(ValueError, 'LIVE_CLEAN_HEAD'):
            V.verify(self.output, self.result['inventorySha256'], old_head, self.repo, self.base)

    def test_candidate_modes_do_not_inherit_group_writable_umask(self):
        old = os.umask(0o002)
        try:
            self.build()
        finally:
            os.umask(old)
        for directory, _, _ in os.walk(self.output):
            self.assertEqual(Path(directory).stat().st_mode & 0o7777, 0o755)
        self.assertTrue(self.verify(False)['sourceRepairGuardsPreserved'])

    def test_cli_runs_actual_builder_and_verifier_functions_with_fixed_fixture_pins(self):
        args = ['build_unsigned.py', '--repo', str(self.repo), '--base', str(self.base), '--output', str(self.output), '--source-public-json', str(self.public), '--source-head', self.head]
        with patch.object(sys, 'argv', args), contextlib.redirect_stdout(io.StringIO()) as out:
            self.assertEqual(B.main(), 0)
        result = json.loads(out.getvalue())
        args = ['verify_unsigned.py', '--package', str(self.output), '--inventory-sha256', result['inventorySha256'], '--source-head', self.head]
        with patch.object(sys, 'argv', args), contextlib.redirect_stdout(io.StringIO()) as out:
            self.assertEqual(V.main(), 0)
        self.assertEqual(json.loads(out.getvalue())['status'], 'PASS_EXTERNALLY_PINNED_UNSIGNED_PACKAGE_BYTES')
        args[args.index('--inventory-sha256') + 1] = '0' * 64
        with patch.object(sys, 'argv', args), contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(V.main(), 78)


if __name__ == '__main__':
    unittest.main()
