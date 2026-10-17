"""Disposable public-code/base/Git fixtures. No root, live config, key or service."""
import base64
import contextlib
import copy
import importlib.util
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch

HERE=Path(__file__).resolve().parent
PRODUCT=HERE.parents[1]
spec=importlib.util.spec_from_file_location('native_maintenance_builder',HERE/'build.py')
B=importlib.util.module_from_spec(spec);spec.loader.exec_module(B)

class Fixture(unittest.TestCase):
    def setUp(self):
        tmp=tempfile.TemporaryDirectory(prefix='source19-native-maintenance-');self.addCleanup(tmp.cleanup)
        self.root=Path(tmp.name);self.repo=self.root/'repo';self.base=self.root/'base';self.out=self.root/'output';self.public=self.root/'public.json';self.bridge=self.root/'bridge-manifest.json'
        self.repo.mkdir(mode=0o755);self.base.mkdir(mode=0o755)
        self.content={n:(PRODUCT/'test/fixtures/source19-first-stop'/n).read_bytes() for n in (B.DISPATCHER,'host/headless-host.mjs','host/native-runner.mjs','app/workspace-host.mjs')}
        self.content['app/app-runner.mjs']=(PRODUCT/'app/app-runner.mjs').read_bytes()
        self.content[B.SERVICE]=b'module.exports={syntheticOldBackend:true};\n';self.content[B.INDEXER]=b'module.exports={syntheticOldIndexer:true};\n'
        self.content['src/shared.mjs']=b'export const syntheticShared=1;\n';self.content['host/executable-fixture.py']=b'# only mode preservation, never run\n';self.content['bridge/bridge-runner.mjs']=b'export const syntheticBridge=1;\n'
        for n,raw in self.content.items():self.emit(self.base/n,raw,0o755 if n.endswith('.py') else 0o644)
        self.roles={
            'app':self.role('app','app/app-runner.mjs',('app/app-runner.mjs','app/workspace-host.mjs','src/shared.mjs')),
            'bridge':self.role('bridge','bridge/bridge-runner.mjs',('bridge/bridge-runner.mjs','src/shared.mjs')),
            'native':self.role('native','host/native-runner.mjs',(*B.OVERLAY_PINS,'src/shared.mjs','host/executable-fixture.py'))}
        self.emit(self.base/'app-manifest.json',B.canonical(self.roles['app']).encode())
        self.emit(self.base/'native-manifest.json',B.canonical(self.roles['native']).encode())
        self.emit(self.bridge,B.canonical(self.roles['bridge']).encode())
        self.emit(self.base/'.maintenance-capsule.json',b'ROOT MARKER MUST NOT BE OPENED',0o600)
        self.overlay={n:(HERE/'payload'/n if n in (B.DISPATCHER,'host/native-runner.mjs') else PRODUCT/n).read_bytes() for n in B.OVERLAY_PINS}
        for n,raw in self.overlay.items():self.emit(self.repo/B.PRODUCT/('maintenance/source19-native-transition-r1/payload/'+n if n in (B.DISPATCHER,'host/native-runner.mjs') else n),raw)
        self.versions={r:B.digest(m) for r,m in self.roles.items()}
        self.pub={'versions':self.versions,'release':{'body':{'id':B.SOURCE_RELEASE,'versions':self.versions},'signature':'SYNTHETIC_NOT_AUTHORITY'},'grant':{'body':{'id':'fixture-not-a-real-grant'},'signature':'SYNTHETIC_NOT_AUTHORITY'}}
        self.emit(self.public,B.canonical(self.pub).encode())
        self.stack=contextlib.ExitStack();self.addCleanup(self.stack.close)
        for name,value in [('BASE_OWNER',os.geteuid()),('BRIDGE_MANIFEST',self.bridge),('SOURCE_VERSIONS',self.versions),('SOURCE_PUBLIC',B.digest(self.pub)),('BASE_PINS',{n:B.sha(self.content[n]) for n in B.BASE_PINS})]:self.stack.enter_context(patch.object(B,name,value))
        self.git('init','-q');self.git('config','user.name','Synthetic maintenance fixture');self.git('config','user.email','synthetic@invalid.example');self.commit()
    def emit(self,file,raw,mode=0o644):
        file.parent.mkdir(parents=True,exist_ok=True,mode=0o755)
        parent=file.parent
        while parent.is_relative_to(self.root):
            parent.chmod(0o755)
            if parent==self.root:break
            parent=parent.parent
        file.write_bytes(raw);file.chmod(mode)
    def git(self,*args):return subprocess.check_output(('/usr/bin/git','-c','core.hooksPath=/dev/null','-c','commit.gpgsign=false','-C',str(self.repo),*args),stderr=subprocess.DEVNULL)
    def commit(self):self.git('add','.');self.git('commit','-qm','synthetic immutable source');self.head=self.git('rev-parse','HEAD').decode().strip()
    def role(self,role,entry,names):return {'schema':'r16.runtime-code.v1','role':role,'entry':entry,'files':{n:B.sha(self.content[n]) for n in names}}
    def build(self,plan=False):return B.build(self.repo,self.base,self.public,self.out,self.head,plan)
    def change_overlay(self,name,raw):
        rel=B.PRODUCT+('maintenance/source19-native-transition-r1/payload/'+name if name in (B.DISPATCHER,'host/native-runner.mjs') else name)
        self.emit(self.repo/rel,raw);self.commit();pins={**B.OVERLAY_PINS,name:B.sha(raw)};self.stack.enter_context(patch.object(B,'OVERLAY_PINS',pins))
    def assert_refused(self,code):
        with self.assertRaisesRegex(B.Refused,'^'+code+'$'):self.build()
        self.assertFalse(self.out.exists())
    def test_full_only_five_delta_unsigned_manifest_bindings_and_modes(self):
        original_app=(self.base/'app-manifest.json').read_bytes();original_bridge=self.bridge.read_bytes()
        result=self.build();self.assertEqual(result['changedFiles'],sorted(B.OVERLAY_PINS));self.assertEqual(result['targetReleaseId'],'r16-daily-20261017-source19-native-lifecycle-r1')
        self.assertEqual((self.out/'metadata/app-manifest.json').read_bytes(),original_app);self.assertEqual((self.out/'metadata/bridge-manifest.json').read_bytes(),original_bridge)
        target=B.parse((self.out/'metadata/native-manifest.json').read_bytes());self.assertEqual(target['entry'],self.roles['native']['entry']);self.assertEqual(set(target['files']),set(self.roles['native']['files']))
        self.assertEqual({n for n,h in target['files'].items() if h!=self.roles['native']['files'][n]},set(B.OVERLAY_PINS))
        self.assertEqual(result['targetVersions']['app'],self.versions['app']);self.assertEqual(result['targetVersions']['bridge'],self.versions['bridge']);self.assertNotEqual(result['targetVersions']['native'],self.versions['native'])
        self.assertEqual(result['signaturesIssued'],0);self.assertEqual(result['productionEffectsIssued'],0)
        for k in ('configurationRevision','forwardRevision','rollbackRevision','releaseEnvelope','grantEnvelope','signedAt','installedAt','activatedAt'):self.assertIsNone(result[k])
        for k in ('maySign','mayInstall','mayActivate','mayChangeOwner','maySettleUnknown'):self.assertIs(result[k],False)
        inventory=B.parse((self.out/'metadata/PAYLOAD_INVENTORY.json').read_bytes())['files'];self.assertEqual(set(inventory),set(self.content))
        for n,row in inventory.items():
            file=self.out/'payload'/n;self.assertEqual(B.sha(file.read_bytes()),row['sha256']);self.assertEqual(file.stat().st_mode&0o777,row['mode'])
        self.assertEqual((self.out/'payload/host/executable-fixture.py').stat().st_mode&0o777,0o755)
        for root,dirs,files in os.walk(self.out):self.assertEqual(Path(root).stat().st_mode&0o777,0o755)
        bindings=B.parse((self.out/'metadata/LOCAL_FILE_BINDINGS.json').read_bytes())['files'];self.assertEqual(len(bindings),sum(len(m['files']) for m in self.roles.values()))
        for row in bindings:self.assertEqual(row['sha256'],inventory[row['artifactPath']]['sha256'])
    def test_plan_only_does_not_create_output(self):self.assertFalse(self.build(True)['outputCreated']);self.assertFalse(self.out.exists())
    def test_marker_is_never_opened(self):
        original=B.read
        def guarded(file,*args):self.assertNotEqual(Path(file).name,'.maintenance-capsule.json');return original(file,*args)
        with patch.object(B,'read',guarded):self.build()
    def test_source19_public_drift(self):self.emit(self.public,B.canonical({**self.pub,'versions':{}}).encode());self.assert_refused('SOURCE19_PUBLIC_REQUIRED')
    def test_wrong_base_role_digest(self):self.emit(self.bridge,b'{}');self.assert_refused('SOURCE_ROLE_PIN')
    def test_base_payload_tamper(self):self.emit(self.base/'src/shared.mjs',b'changed');self.assert_refused('BASE_BYTES_OR_MODE')
    def test_base_mode_drift(self):(self.base/'src/shared.mjs').chmod(0o600);self.assert_refused('BASE_BYTES_OR_MODE')
    def test_base_extra_file_or_directory(self):
        self.emit(self.base/'extra.json',b'{}');self.assert_refused('BASE_EXACT_SET_REQUIRED');(self.base/'extra.json').unlink();(self.base/'extra-empty').mkdir(mode=0o755);(self.base/'extra-empty').chmod(0o755);self.assert_refused('BASE_EXACT_SET_REQUIRED')
    def test_base_hardlink_refused(self):
        os.link(self.base/'src/shared.mjs',self.root/'extra-hardlink');self.assert_refused('BASE_FILE_UNSAFE')
    def test_base_directory_symlink_refused(self):
        (self.base/'extra-link').symlink_to(self.root,target_is_directory=True);self.assert_refused('BASE_DIRECTORY_LINK')
    def test_dirty_head_refused(self):
        self.emit(self.repo/'untracked.txt',b'x');self.assert_refused('CLEAN_EXACT_HEAD_REQUIRED')
    def test_wrong_lifecycle_bytes_even_with_clean_git_refused(self):
        file=self.repo/B.PRODUCT/'host/headless-host.mjs';self.emit(file,file.read_bytes()+b'// drift\n');self.commit();self.assert_refused('EXACT_LIFECYCLE_OVERLAY_REQUIRED')
    def test_whole_r17_dispatcher_cannot_be_disguised_as_backport(self):
        self.change_overlay(B.DISPATCHER,(PRODUCT/'host/workspace-dispatcher.mjs').read_bytes());self.assert_refused('R17_FEATURE_NOT_ALLOWED')
    def test_recovery_guard_cannot_be_changed(self):
        self.change_overlay(B.DISPATCHER,self.overlay[B.DISPATCHER].replace(b'allowClosedRelease&&state.recoveryOnly',b'allowClosedRelease||state.recoveryOnly'));self.assert_refused('R15_RECOVERY_REPAIR_LOST')
    def test_legacy_reconcile_not_settled_or_rewritten(self):
        self.change_overlay(B.DISPATCHER,self.overlay[B.DISPATCHER].replace(b'const receipt=p.complete(',b'const receipt=p.fakeComplete('));self.assert_refused('LEGACY_RECONCILE_CHANGED')
    def test_strict_unknown_close_not_removed(self):
        self.change_overlay(B.DISPATCHER,self.overlay[B.DISPATCHER].replace(b"check(entry.participant.status().unresolved.length===0,'RECOVERY_UNRESOLVED');",b'/* forbidden removed legacy close guard */'));self.assert_refused('STRICT_UNKNOWN_CLOSE_LOST')
    def test_output_existing_or_repository_refused_without_writes(self):
        self.out.mkdir();self.emit(self.out/'keep',b'keep');
        with self.assertRaisesRegex(B.Refused,'NEW_ISOLATED_OUTPUT_REQUIRED'):self.build()
        self.assertEqual((self.out/'keep').read_bytes(),b'keep');self.out=self.repo/'forbidden-output';self.assert_refused('NEW_ISOLATED_OUTPUT_REQUIRED')
    def test_root_identity_refused_without_effects(self):
        with patch.object(B.os,'geteuid',return_value=0):self.assert_refused('ORDINARY_USER_ABSOLUTE_PATHS_REQUIRED')
    def test_umask_group_write_not_inherited(self):
        old=os.umask(0o002)
        try:self.build()
        finally:os.umask(old)
        for root,dirs,files in os.walk(self.out):
            self.assertEqual(Path(root).stat().st_mode&0o777,0o755)
            for n in files:self.assertEqual((Path(root)/n).stat().st_mode&0o022,0)
    def test_backport_executes_portable_lifecycle_cases_with_exact_old_source19_core(self):
        # Execute the real backported dispatcher, not the general R17 dispatcher.
        # The original signed Source19 core remains byte-for-byte unmodified.
        core=PRODUCT/'test/fixtures/source19-first-stop/src/lease-core.mjs'
        self.assertEqual(B.sha(core.read_bytes()),'889232f53d5c014138a7004df32c8e4f4f6c16703b6d53fa75ce0cbcf53e43b9')
        dispatcher_uri=(PRODUCT/'test/fixtures/source19-first-stop/host/workspace-dispatcher.mjs').as_uri()
        source=(HERE/'payload'/B.DISPATCHER).read_text()
        module=source.replace("from '../src/lease-core.mjs'", "from '"+core.as_uri()+"'").replace("from '../src/control-clock.mjs'", "from '"+(core.parent/'control-clock.mjs').as_uri()+"'")
        module_uri='data:text/javascript;base64,'+base64.b64encode(module.encode()).decode()
        original_test=PRODUCT/'test/native-physical-shutdown.test.mjs'
        test=original_test.read_text()
        test=test.replace("from '../src/lease-core.mjs'", "from '"+core.as_uri()+"'")
        test=test.replace("from '../host/workspace-dispatcher.mjs'", "from '"+module_uri+"'")
        test=test.replace("from '../host/headless-host.mjs'", "from '"+(PRODUCT/'host/headless-host.mjs').as_uri()+"'")
        test=test.replace("createRequire(import.meta.url)","createRequire("+B.canonical(original_test.as_uri())+")")
        test=test.replace("fs.readFileSync(new URL('../host/workspace-dispatcher.mjs',import.meta.url),'utf8')",B.canonical(source))
        test=test.replace("new URL('../host/workspace-dispatcher.mjs',import.meta.url)","new URL("+B.canonical(dispatcher_uri)+")")
        file=self.root/'backport-actual-lifecycle.test.mjs';file.write_text(test)
        node=shutil.which('node');self.assertIsNotNone(node,'Node is required, not skipped')
        result=subprocess.run([node,'--test',str(file)],capture_output=True,text=True,timeout=20)
        self.assertEqual(result.returncode,0,result.stdout[-10000:]+result.stderr[-2000:])
        self.assertIn('# tests 16',result.stdout);self.assertIn('# pass 16',result.stdout);self.assertIn('# skipped 0',result.stdout)
    def test_backport_source_only_preserves_declared_legacy_and_local_api(self):
        source=(HERE/'payload'/B.DISPATCHER).read_text()
        self.assertTrue(all(t not in source for t in B.FORBIDDEN));self.assertIn('shutdownLocalResources',source);self.assertIn("scope:'LOCAL_ONLY'",source);self.assertIn("firstStopProof:'NOT_PROVEN'",source)
        self.assertIn("if(invalidate){fresh=false;",source)
        # Four reused files are pinned, exact lifecycle additions already reviewed
        # against original Source19. They are never replaced by general repo overlay.
        for n,pin in B.OVERLAY_PINS.items():self.assertEqual(B.sha(self.overlay[n]),pin)

if __name__=='__main__':unittest.main()
