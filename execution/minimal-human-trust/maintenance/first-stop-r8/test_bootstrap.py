"""Verify sealed capsule, read-only recovery and interrupted immutable publication."""
import copy,importlib,json,sys,types,unittest
from pathlib import Path
from unittest.mock import patch
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE))
import bootstrap as b
class Tests(unittest.TestCase):
 def fixture(self):
  names={'bootstrap.py','common_safe.py','native_entry.py','stop_driver.py','linux_backend.py','ledger_checkpoint.py','handoff.py','TARGET.json'}
  source={n:b'{}' if n.endswith('.json') else b'# synthetic inert source' for n in names}
  # The test makes copying fatal. status/recovery must never invoke this.
  source['common_safe.py']=b'def immutable(*a):\n raise AssertionError("read-only mode copied source")\n'
  manifest={'schema':'r16.first-stop-capsule.v1','files':{n:b.sha(v) for n,v in source.items()},'policyExceptionProposalHash':b.POLICY,'acceptedPolicyException':True,'productionStopAlreadyAuthorized':False}
  raw=json.dumps(manifest).encode();h=b.sha(raw);reads=[]
  def read(path,root_only=False):
   reads.append((Path(path),root_only))
   if Path(path).name=='CAPSULE.json':return raw
   return source[Path(path).name]
  return source,raw,h,reads,read
 def test_status_and_recovery_need_only_already_installed_root_capsule_and_never_copy(self):
  for mode in ('status','recover-original'):
   source,raw,h,reads,read=self.fixture();entry=types.SimpleNamespace(entry=lambda m,c:{'status':'SAFE_READ_TEST'})
   with patch.object(b.os,'getuid',return_value=0),patch.object(b.os,'geteuid',return_value=0),patch.object(b.socket,'gethostname',return_value='VM-0-12-ubuntu'),patch.object(b.resource,'setrlimit'),patch.object(b,'secure_read',side_effect=read),patch.object(b.importlib,'import_module',return_value=entry):
    self.assertEqual(b.run(mode,h)['status'],'SAFE_READ_TEST')
   self.assertTrue(all(root for path,root in reads));self.assertTrue(all(str(path).startswith(str(b.ROOT)) for path,root in reads))
 def test_candidate_tampering_is_rejected_before_any_candidate_python_exec(self):
  source,raw,h,reads,read=self.fixture();source['native_entry.py']+=b'TAMPER'
  with patch.object(b.os,'getuid',return_value=0),patch.object(b.os,'geteuid',return_value=0),patch.object(b.socket,'gethostname',return_value='VM-0-12-ubuntu'),patch.object(b.resource,'setrlimit'),patch.object(b,'secure_read',side_effect=read),patch.object(b.importlib,'import_module',side_effect=AssertionError('unverified import')):
   with self.assertRaisesRegex(ValueError,'CAPSULE_FILE_DRIFT'):b.run('stop',h)
 def test_non_root_cannot_read_or_copy_a_capsule(self):
  with patch.object(b.os,'getuid',return_value=1000),patch.object(b.resource,'setrlimit'),patch.object(b,'secure_read',side_effect=AssertionError('file read')):
   with self.assertRaisesRegex(ValueError,'BOOTSTRAP_FIXED_ROOT_REQUIRED'):b.run('stop','a'*64)
 def test_core_dumps_are_disabled_before_any_capsule_read(self):
  seen=[]
  with patch.object(b.os,'getuid',return_value=0),patch.object(b.os,'geteuid',return_value=0),patch.object(b.socket,'gethostname',return_value='VM-0-12-ubuntu'),patch.object(b.resource,'setrlimit',side_effect=lambda *a:seen.append('core-off')),patch.object(b,'secure_read',side_effect=lambda *a,**k:(_ for _ in ()).throw(RuntimeError(str(seen)))):
   with self.assertRaisesRegex(RuntimeError,"core-off"):b.run('status','a'*64)
if __name__=='__main__':unittest.main()
