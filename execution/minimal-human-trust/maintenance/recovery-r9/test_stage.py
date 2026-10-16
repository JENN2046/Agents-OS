"""Run real staging IO/rename on small disposable ordinary-user packages."""
import base64,hashlib,importlib.util,json,os,subprocess,sys,tempfile,unittest
from pathlib import Path
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('r9_stage_tested',HERE/'stage.py');stage=importlib.util.module_from_spec(spec);spec.loader.exec_module(stage)
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
  freeze=canon({'files':{n:sha(raw) for n,raw in sources.items()},'payloadFiles':{n:sha(raw) for n,raw in package.items()}})
  (old/'SOURCE_FREEZE.json').write_bytes(freeze);(old/'SOURCE_FREEZE.json').chmod(0o644)
  data={'manifest':base64.b64encode(freeze).decode(),'capsuleHash':sha(freeze),'sources':{n:base64.b64encode(raw).decode() for n,raw in sources.items()}}
  # Only fixture cardinalities and fixed public closure differ. All validation,
  # byte reads, identity checks, writes, fsyncs and NOREPLACE rename are real.
  code=stage.REMOTE.replace('1000',str(os.getuid())).replace("len(f['files'])==19 and len(f['payloadFiles'])==12600","len(f['files'])==2 and len(f['payloadFiles'])==2").replace('c7bc7ba7fa3fb0fbc5099ef28709059a5116a5943cc9aecd75bc17cb1abbafd8',sha(canon(closure)))
  prefix='OLD='+repr(str(old))+'\nNEW='+repr(str(new))+'\nOLD_CAP='+repr(sha(freeze))+'\n'
  return old,new,data,prefix,code
 def run_code(self,data,prefix,code):return subprocess.run((sys.executable,'-I','-B','-c',prefix+code),input=json.dumps(data).encode(),capture_output=True,timeout=10)
 def test_move_preserves_inode_and_final_bytes_then_publishes_manifest(self):
  with tempfile.TemporaryDirectory(dir=Path.home()) as tmp:
   old,new,data,prefix,code=self.setup_fixture(Path(tmp));identity=(old/'package').stat().st_ino
   result=self.run_code(data,prefix,code);self.assertEqual(result.returncode,0,result.stderr.decode());report=json.loads(result.stdout)
   self.assertTrue(report['publicPackageMoved']);self.assertFalse((old/'package').exists());self.assertEqual((new/'package').stat().st_ino,identity);self.assertEqual(sha((new/'SOURCE_FREEZE.json').read_bytes()),data['capsuleHash'])
   again=self.run_code(data,prefix,code);self.assertEqual(again.returncode,0,again.stderr.decode());self.assertFalse(json.loads(again.stdout)['publicPackageMoved'])
 def test_post_move_bytes_drift_cannot_publish_verified_manifest(self):
  with tempfile.TemporaryDirectory(dir=Path.home()) as tmp:
   old,new,data,prefix,code=self.setup_fixture(Path(tmp))
   code=code.replace("closure=verify_package(new/'package')","(new/'package/payload/fixture.mjs').write_bytes(b'concurrent drift')\nclosure=verify_package(new/'package')")
   result=self.run_code(data,prefix,code);self.assertNotEqual(result.returncode,0);self.assertIn(b'PUBLIC_PACKAGE_BYTE_OR_MODE_DRIFT',result.stderr);self.assertFalse((new/'SOURCE_FREEZE.json').exists());self.assertFalse(result.stdout)
 def test_existing_destination_package_refuses_ambiguous_second_move(self):
  with tempfile.TemporaryDirectory(dir=Path.home()) as tmp:
   old,new,data,prefix,code=self.setup_fixture(Path(tmp));new.mkdir(mode=0o755);(new/'package').mkdir(mode=0o755)
   result=self.run_code(data,prefix,code);self.assertNotEqual(result.returncode,0);self.assertTrue((old/'package').is_dir());self.assertFalse((new/'SOURCE_FREEZE.json').exists())
 def test_source_symlink_directory_refuses_without_move(self):
  with tempfile.TemporaryDirectory(dir=Path.home()) as tmp:
   old,new,data,prefix,code=self.setup_fixture(Path(tmp));(old/'package/foreign').symlink_to(old/'package/payload',target_is_directory=True)
   result=self.run_code(data,prefix,code);self.assertNotEqual(result.returncode,0);self.assertIn(b'PUBLIC_PACKAGE_SYMLINK_DIRECTORY_REFUSED',result.stderr);self.assertTrue((old/'package').is_dir());self.assertFalse((new/'SOURCE_FREEZE.json').exists())
if __name__=='__main__':unittest.main()
