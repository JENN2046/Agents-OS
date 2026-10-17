"""Run real staging exclusive copy on small disposable ordinary-user packages."""
import ast,base64,hashlib,importlib.util,inspect,json,os,subprocess,sys,tempfile,types,unittest
from unittest.mock import patch
from pathlib import Path
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('r12_stage_tested',HERE/'stage.py');stage=importlib.util.module_from_spec(spec);spec.loader.exec_module(stage)
def sha(b):return hashlib.sha256(b).hexdigest()
def canon(v):return json.dumps(v,sort_keys=True,separators=(',',':')).encode()
class StageTests(unittest.TestCase):
 def setup_fixture(self,root):
  old=root/'old';new=root/'new';old.mkdir(mode=0o755);(old/'package/payload').mkdir(parents=True,mode=0o755);(old/'package/metadata').mkdir(mode=0o755)
  for directory in (old/'package',old/'package/payload',old/'package/metadata'):directory.chmod(0o755)
  package={'payload/fixture.mjs':b'export const fixture=true;','metadata/PAYLOAD_INVENTORY.json':canon({'fixture.mjs':{'mode':0o644}})}
  for n,raw in package.items():(old/'package'/n).write_bytes(raw);(old/'package'/n).chmod(0o644)
  closure={n:{'sha256':sha(raw),'mode':0o644,'bytes':len(raw)} for n,raw in package.items()}
  sources={'entry.py':b'fixture = True\n','metadata.json':b'{}'}
  for n,raw in sources.items():(old/n).write_bytes(raw);(old/n).chmod(0o644)
  freeze=canon({'planTemplate':{'assetReuse':stage.C.ASSET_REUSE},'files':{n:sha(raw) for n,raw in sources.items()},'payloadFiles':{n:sha(raw) for n,raw in package.items()}})
  (old/'SOURCE_FREEZE.json').write_bytes(freeze);(old/'SOURCE_FREEZE.json').chmod(0o644)
  data={'manifest':base64.b64encode(freeze).decode(),'capsuleHash':sha(freeze),'sources':{n:base64.b64encode(raw).decode() for n,raw in sources.items()}}
  # Only fixture cardinalities and fixed public closure differ. All validation,
  # byte reads, identity checks, writes, fsyncs and exclusive copy are real.
  code=stage.REMOTE.replace('1000',str(os.getuid())).replace("len(f['files'])==19 and len(f['payloadFiles'])==12600","len(f['files'])==2 and len(f['payloadFiles'])==2").replace('c7bc7ba7fa3fb0fbc5099ef28709059a5116a5943cc9aecd75bc17cb1abbafd8',sha(canon(closure)))
  prefix='OLD='+repr(str(old))+'\nNEW='+repr(str(new))+'\nOLD_CAP='+repr(sha(freeze))+'\nASSET_REUSE='+repr(stage.C.ASSET_REUSE)+'\n'
  return old,new,data,prefix,code
 def run_code(self,data,prefix,code):return subprocess.run((sys.executable,'-I','-B','-c',prefix+code),input=json.dumps(data).encode(),capture_output=True,timeout=10)
 def test_copy_preserves_old_bytes_inodes_and_independent_new_package(self):
  with tempfile.TemporaryDirectory(dir=Path.home()) as tmp:
   old,new,data,prefix,code=self.setup_fixture(Path(tmp));inode=(old/'package').stat().st_ino;oldraw=(old/'package/payload/fixture.mjs').read_bytes();oldfile=(old/'package/payload/fixture.mjs').stat().st_ino
   result=self.run_code(data,prefix,code);self.assertEqual(result.returncode,0,result.stderr.decode());report=json.loads(result.stdout)
   self.assertFalse(report['publicPackageMoved']);self.assertTrue(report['ordinaryPackageCopied']);self.assertEqual((old/'package').stat().st_ino,inode);self.assertNotEqual((new/'package').stat().st_ino,inode);self.assertEqual((old/'package/payload/fixture.mjs').stat().st_ino,oldfile);self.assertNotEqual((new/'package/payload/fixture.mjs').stat().st_ino,oldfile);self.assertEqual((old/'package/payload/fixture.mjs').read_bytes(),oldraw);self.assertEqual(sha((new/'SOURCE_FREEZE.json').read_bytes()),data['capsuleHash'])
   again=self.run_code(data,prefix,code);self.assertEqual(again.returncode,0,again.stderr.decode());self.assertEqual((old/'package/payload/fixture.mjs').stat().st_ino,oldfile)
 def test_wrong_public_directory_mode_refuses_without_chmod_or_copy(self):
  with tempfile.TemporaryDirectory(dir=Path.home()) as tmp:
   old,new,data,prefix,code=self.setup_fixture(Path(tmp));(old/'package').chmod(0o700)
   result=self.run_code(data,prefix,code);self.assertNotEqual(result.returncode,0)
   self.assertTrue((old/'package').exists());self.assertEqual((old/'package').stat().st_mode&0o777,0o700)
   self.assertFalse((new/'SOURCE_FREEZE.json').exists())
 def test_post_copy_bytes_drift_cannot_publish_verified_manifest(self):
  with tempfile.TemporaryDirectory(dir=Path.home()) as tmp:
   old,new,data,prefix,code=self.setup_fixture(Path(tmp))
   code=code.replace("closure,_=verify_package(new/'package')","(new/'package/payload/fixture.mjs').write_bytes(b'concurrent drift')\nclosure,_=verify_package(new/'package')")
   result=self.run_code(data,prefix,code);self.assertNotEqual(result.returncode,0);self.assertIn(b'PUBLIC_PACKAGE_BYTE_OR_MODE_DRIFT',result.stderr);self.assertFalse((new/'SOURCE_FREEZE.json').exists());self.assertFalse(result.stdout)
 def test_existing_foreign_destination_file_is_not_overwritten(self):
  with tempfile.TemporaryDirectory(dir=Path.home()) as tmp:
   old,new,data,prefix,code=self.setup_fixture(Path(tmp));(new/'package/payload').mkdir(parents=True,mode=0o755);target=new/'package/payload/fixture.mjs';target.write_bytes(b'foreign');target.chmod(0o644)
   for directory in (new,new/'package',new/'package/payload'):directory.chmod(0o755)
   result=self.run_code(data,prefix,code);self.assertNotEqual(result.returncode,0);self.assertIn(b'FOREIGN_STAGED_SOURCE_REFUSED',result.stderr);self.assertEqual(target.read_bytes(),b'foreign');self.assertTrue((old/'package').is_dir());self.assertFalse((new/'SOURCE_FREEZE.json').exists())
 def test_source_symlink_directory_refuses_without_move(self):
  with tempfile.TemporaryDirectory(dir=Path.home()) as tmp:
   old,new,data,prefix,code=self.setup_fixture(Path(tmp));(old/'package/foreign').symlink_to(old/'package/payload',target_is_directory=True)
   result=self.run_code(data,prefix,code);self.assertNotEqual(result.returncode,0);self.assertIn(b'CANDIDATE_SYMLINK_DIRECTORY_REFUSED',result.stderr);self.assertTrue((old/'package').is_dir());self.assertFalse((new/'SOURCE_FREEZE.json').exists())
 def test_old_source_runtime_drift_refuses_before_package_move(self):
  with tempfile.TemporaryDirectory(dir=Path.home()) as tmp:
   old,new,data,prefix,code=self.setup_fixture(Path(tmp));(old/'entry.py').write_bytes(b'changed old source')
   result=self.run_code(data,prefix,code);self.assertNotEqual(result.returncode,0);self.assertIn(b'OLD_PUBLIC_RUNTIME_DRIFT',result.stderr)
   self.assertTrue((old/'package').exists());self.assertFalse((new/'SOURCE_FREEZE.json').exists())
 def test_foreign_new_extra_file_cannot_publish_manifest(self):
  with tempfile.TemporaryDirectory(dir=Path.home()) as tmp:
   old,new,data,prefix,code=self.setup_fixture(Path(tmp));new.mkdir(mode=0o755);(new/'foreign').write_bytes(b'not in capsule');(new/'foreign').chmod(0o644)
   result=self.run_code(data,prefix,code);self.assertNotEqual(result.returncode,0);self.assertIn(b'CANDIDATE_COMPLETE_FILE_SET_DRIFT',result.stderr)
   self.assertFalse((new/'SOURCE_FREEZE.json').exists());self.assertTrue((new/'foreign').exists())
 def test_hardlinked_file_refuses_before_move(self):
  with tempfile.TemporaryDirectory(dir=Path.home()) as tmp:
   old,new,data,prefix,code=self.setup_fixture(Path(tmp));os.link(old/'package/payload/fixture.mjs',Path(tmp)/'other-link')
   result=self.run_code(data,prefix,code);self.assertNotEqual(result.returncode,0);self.assertIn(b'STAGE_REGULAR_FILE_REFUSED',result.stderr)
   self.assertTrue((old/'package').exists());self.assertFalse((new/'SOURCE_FREEZE.json').exists())
 def test_disk_budget_refuses_before_runtime_or_copy_file_writes(self):
  with tempfile.TemporaryDirectory(dir=Path.home()) as tmp:
   old,new,data,prefix,code=self.setup_fixture(Path(tmp));code=code.replace('need(v.f_bavail*block>=copy_budget+64*1024*1024+256*1024*1024,','need(False,')
   result=self.run_code(data,prefix,code);self.assertNotEqual(result.returncode,0);self.assertIn(b'ORDINARY_COPY_DISK_BUDGET_REFUSED',result.stderr);self.assertFalse((new/'entry.py').exists());self.assertFalse((new/'package').exists());self.assertTrue((old/'package').exists())
 def test_crash_after_copy_can_reconcile_exact_source_without_touching_old(self):
  with tempfile.TemporaryDirectory(dir=Path.home()) as tmp:
   old,new,data,prefix,code=self.setup_fixture(Path(tmp));inode=(old/'package').stat().st_ino;crash=code.replace("closure,_=verify_package(new/'package')","raise ValueError('SYNTHETIC_AFTER_COPY')\nclosure,_=verify_package(new/'package')")
   first=self.run_code(data,prefix,crash);self.assertNotEqual(first.returncode,0);self.assertTrue((old/'package').exists());self.assertFalse((new/'SOURCE_FREEZE.json').exists())
   second=self.run_code(data,prefix,code);self.assertEqual(second.returncode,0,second.stderr.decode());self.assertTrue(json.loads(second.stdout)['ordinaryPackageCopied']);self.assertEqual((old/'package').stat().st_ino,inode)
 def test_wrong_asset_reuse_declaration_refuses_before_move(self):
  with tempfile.TemporaryDirectory(dir=Path.home()) as tmp:
   old,new,data,prefix,code=self.setup_fixture(Path(tmp));prefix=prefix.replace(repr(stage.C.ASSET_REUSE),'{}')
   result=self.run_code(data,prefix,code);self.assertNotEqual(result.returncode,0);self.assertIn(b'STAGED_ASSET_REUSE_SCOPE_DRIFT',result.stderr)
   self.assertTrue((old/'package').exists());self.assertFalse((new/'SOURCE_FREEZE.json').exists())
 def local_reader(self):
  # Only the two fixture cardinalities differ from 19/12600; the exact real
  # function bytecode/global imports and all IO/owner/hash/mode checks execute.
  class Cardinality(ast.NodeTransformer):
   def visit_Constant(self,node):
    if type(node.value) is int and node.value in (19,12600):return ast.copy_location(ast.Constant(2),node)
    return node
  tree=Cardinality().visit(ast.parse(inspect.getsource(stage.local_inputs)));ast.fix_missing_locations(tree)
  namespace=dict(stage.__dict__);exec(compile(tree,'<same-local-reader-fixture-counts>','exec'),namespace)
  return namespace['local_inputs']

 def test_actual_local_input_reader_checks_closure_without_ssh(self):
  with tempfile.TemporaryDirectory(dir=Path.home()) as tmp:
   old,new,data,prefix,code=self.setup_fixture(Path(tmp));f=json.loads((old/'SOURCE_FREEZE.json').read_bytes())
   closure={n:{'sha256':pin,'mode':0o644,'bytes':len((old/'package'/n).read_bytes())} for n,pin in f['payloadFiles'].items()}
   with patch.object(stage,'SOURCE',old),patch.object(stage.C,'PACKAGE_CLOSURE',sha(canon(closure))),patch.object(stage.subprocess,'run',side_effect=AssertionError('NO_NETWORK_OR_CHILD')):
    result=self.local_reader()(data['capsuleHash']);self.assertEqual(result,data)
 def test_actual_local_input_reader_refuses_drift_and_extras_before_transport(self):
  for drift in ('byte','hardlink','extra'):
   with self.subTest(drift=drift),tempfile.TemporaryDirectory(dir=Path.home()) as tmp:
    old,new,data,prefix,code=self.setup_fixture(Path(tmp));f=json.loads((old/'SOURCE_FREEZE.json').read_bytes())
    closure={n:{'sha256':pin,'mode':0o644,'bytes':len((old/'package'/n).read_bytes())} for n,pin in f['payloadFiles'].items()}
    if drift=='byte':(old/'package/payload/fixture.mjs').write_bytes(b'drift')
    elif drift=='hardlink':os.link(old/'package/payload/fixture.mjs',Path(tmp)/'outside-link')
    else:(old/'extra').write_bytes(b'extra')
    with patch.object(stage,'SOURCE',old),patch.object(stage.C,'PACKAGE_CLOSURE',sha(canon(closure))),patch.object(stage.subprocess,'run',side_effect=AssertionError('NO_NETWORK_OR_CHILD')),self.assertRaises(ValueError):self.local_reader()(data['capsuleHash'])
if __name__=='__main__':unittest.main()
