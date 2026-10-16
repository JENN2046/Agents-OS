"""Verify sealed capsule, read-only recovery and interrupted immutable publication."""
import copy,importlib,importlib.util,io,json,shlex,sys,tempfile,types,unittest
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

class ReadonlyPreflightTests(unittest.TestCase):
 fixture=Tests.fixture
 def readonly_fixture(self,*,state=False,drift=False,effect=False,private_error=False):
  source,raw,h,reads,read=self.fixture()
  source['TARGET.json']=b'{"unit":"r16-app.service","pid":1234}'
  source['common_safe.py']=b'raise AssertionError("preflight executed mutator primitives")'
  for name in ('native_entry.py','handoff.py'):
   source[name]=b'raise AssertionError("preflight executed privileged module")'
  body="""import hashlib,json
from pathlib import Path
from types import SimpleNamespace
def digest(v):return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':')).encode()).hexdigest()
class Files:
 def read(self,path,**kwargs):return b''
class LinuxBackend:
 def __init__(self,admission,checkpointer):
  self.admission=admission;self.checkpointer=checkpointer;self.paths=SimpleNamespace(state=Path('/synthetic/root-state'));self.files=Files();self.count=0
 def _private_state(self):return STATE
 def inspect(self,target):
  self.admission.require('inspect',target);self.count+=1
  if EFFECT:self.admission.require('freeze',target)
  if PRIVATE_ERROR:raise RuntimeError('PRIVATE_LEDGER_CONTENT_MUST_NOT_LEAK')
  return {**target,'processExited':False,'frozen':False,'freezeRequested':False,'fenceOwner':None,'freezeOwner':None,'nRestarts':self.count if DRIFT else 0}
class RootJournal:
 def __init__(self,*args):raise AssertionError('preflight acquired writing journal')
"""
  source['linux_backend.py']=(f'STATE={state!r};DRIFT={drift!r};EFFECT={effect!r};PRIVATE_ERROR={private_error!r}\n'+body).encode()
  source['stop_driver.py']=b"import hashlib,json\ndef digest(v):return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':')).encode()).hexdigest()\ndef checkpoint_manifest(checkpoint,expectations):\n assert set(expectations)=={'target','expectedOriginalUnknown','expectedLeaseBindings','expectedSemanticBindingsDigest'}\n assert expectations['expectedSemanticBindingsDigest']==checkpoint['attestation']['semanticBindingsDigest']\n return {'validatedOriginalBindings':True,'noTemporaryFiles':True,'otherDurableInflight':0,'drainStatus':'UNPROVEN','semanticBindingsDigest':expectations['expectedSemanticBindingsDigest']}\nclass Driver:\n def __init__(self,*args):raise AssertionError('readonly constructed signal driver')\n"
  attestation={'sourcePublicConfigDigest':'1'*64,'grantHash':'2'*64,'sourceDeliveryHash':'3'*64,'sourceDeliveryRevision':16,'registrationHash':'4'*64,'checkpointManifestDigest':'5'*64,'semanticBindingsDigest':'6'*64,'registeredProjectCount':9,'fileCount':41,'totalBytes':12345,'originalUnknownCount':2,'otherDurableInflight':0,'foreignOpenWriters':0,'signatureVerification':True,'sealedRegistrationVerified':True,'capturePhase':'BASELINE_NOT_DRAIN_PROOF','drainStatus':'UNPROVEN','privateProof':'PRIVATE_LEDGER_CONTENT_MUST_NOT_LEAK'}
  source['ledger_checkpoint.py']=("PUBLIC_DIGEST='"+'1'*64+"'\nGRANT_DIGEST='"+'2'*64+"'\nDELIVERY_DIGEST='"+'3'*64+"'\nclass LedgerCheckpoint:\n def capture_baseline(self,target):return "+repr({'attestation':attestation,'files':{'PRIVATE_RAW_BYTES':'MUST_NOT_LEAK'},'expectedOriginalUnknown':{},'expectedLeaseBindings':{},'expectedSemanticBindingsDigest':'6'*64})+'\n').encode()
  return self.reseal(source,reads)
 def reseal(self,source,reads=None):
  if reads is None:reads=[]
  manifest={'schema':'r16.first-stop-capsule.v1','files':{n:b.sha(v) for n,v in source.items()},'policyExceptionProposalHash':b.POLICY,'acceptedPolicyException':True,'productionStopAlreadyAuthorized':False};raw=json.dumps(manifest).encode();h=b.sha(raw)
  def read(path,root_only=False):
   reads.append((Path(path),root_only))
   return raw if Path(path).name=='CAPSULE.json' else source[Path(path).name]
  return source,raw,h,reads,read
 def invoke(self,fixture,*,names=()):
  source,raw,h,reads,read=fixture
  with patch.object(b.os,'getuid',return_value=0),patch.object(b.os,'geteuid',return_value=0),patch.object(b.socket,'gethostname',return_value='VM-0-12-ubuntu'),patch.object(b.resource,'setrlimit'),patch.object(b,'secure_read',side_effect=read),patch.object(b.importlib,'import_module',side_effect=AssertionError('candidate import forbidden')),patch.object(b.os,'open',side_effect=AssertionError('preflight attempted filesystem write/open outside fixed readers')),patch.object(b.os,'listdir',return_value=list(names)):
   return b.run('preflight',h)
 def test_preflight_seals_all_candidate_but_executes_only_verified_readers_in_memory(self):
  fixture=self.readonly_fixture();before=set(sys.modules);path=list(sys.path);result=self.invoke(fixture)
  self.assertEqual(result['status'],'READ_ONLY_PREFLIGHT_PASS');self.assertEqual(result['registeredProjectCount'],9);self.assertEqual(result['originalUnknownCount'],2);self.assertTrue(result['checkpointValidatorPassed']);self.assertRegex(result['checkpointValidatorManifestDigest'],'^[0-9a-f]{64}$')
  self.assertEqual(result['drainStatus'],'UNPROVEN');self.assertFalse(result['mayStop']);self.assertFalse(result['rootSourceInstalled']);self.assertFalse(result['journalWritten']);self.assertFalse(result['nativeIntentCreated']);self.assertEqual(result['signalsIssued'],0);self.assertEqual(result['businessCallsIssued'],0)
  self.assertNotIn('PRIVATE',json.dumps(result));self.assertNotIn('files',result);self.assertEqual(sys.path,path);self.assertFalse(set(sys.modules)-before)
  self.assertTrue(all(not root for _,root in fixture[3]));self.assertTrue(all(str(p).startswith(str(b.CANDIDATE)) for p,_ in fixture[3]));self.assertEqual(len(fixture[3]),9)
 def test_preflight_allows_only_historical_exclusive_lock_and_no_active_or_unknown_state(self):
  fixture=self.readonly_fixture(state=True)
  self.assertEqual(self.invoke(fixture,names=['exclusive.lock'])['status'],'READ_ONLY_PREFLIGHT_PASS')
  for name in ('transaction.json','approval.json','native-intent.json','fence-owner.json','freeze-owner.json','.transaction.pending'):
   with self.subTest(name=name):
    result=self.invoke(fixture,names=[name]);self.assertEqual(result['status'],'READ_ONLY_PREFLIGHT_REFUSED');self.assertEqual(result['code'],'READONLY_ACTIVE_OR_UNREVIEWED_STOP_STATE')
 def test_preflight_rechecks_stop_state_after_capture(self):
  fixture=self.readonly_fixture(state=True);source,raw,h,reads,read=fixture
  with patch.object(b.os,'getuid',return_value=0),patch.object(b.os,'geteuid',return_value=0),patch.object(b.socket,'gethostname',return_value='VM-0-12-ubuntu'),patch.object(b.resource,'setrlimit'),patch.object(b,'secure_read',side_effect=read),patch.object(b.os,'listdir',side_effect=[[],['approval.json']]):
   result=b.run('preflight',h)
  self.assertEqual(result['status'],'READ_ONLY_PREFLIGHT_REFUSED')
 def test_preflight_drift_and_any_mutating_admission_are_refused(self):
  for options,code in [({'drift':True},'READONLY_RUNTIME_OBSERVATION_CHANGED'),({'effect':True},'READONLY_EFFECT_REFUSED')]:
   result=self.invoke(self.readonly_fixture(**options));self.assertEqual(result['status'],'READ_ONLY_PREFLIGHT_REFUSED');self.assertEqual(result['code'],code)
 def test_preflight_private_exception_is_redacted_and_module_namespace_removed(self):
  before=set(sys.modules);result=self.invoke(self.readonly_fixture(private_error=True));self.assertEqual(result['status'],'READ_ONLY_PREFLIGHT_REFUSED');self.assertEqual(result['code'],'PROTECTED_READONLY_PREFLIGHT_FAILED');self.assertNotIn('PRIVATE',json.dumps(result));self.assertFalse(set(sys.modules)-before)
 def test_preflight_capsule_tampering_is_rejected_before_reader_execution(self):
  fixture=self.readonly_fixture();fixture[0]['ledger_checkpoint.py']+=b'\n# tampered'
  with self.assertRaisesRegex(ValueError,'CAPSULE_FILE_DRIFT'):self.invoke(fixture)
 def test_preflight_rejects_private_or_unproven_projection_claims(self):
  for change in ("'signatureVerification': True","'originalUnknownCount': 2","'drainStatus': 'UNPROVEN'"):
   fixture=self.readonly_fixture();source=fixture[0]
   replacement={"'signatureVerification': True":"'signatureVerification': False","'originalUnknownCount': 2":"'originalUnknownCount': True","'drainStatus': 'UNPROVEN'":"'drainStatus': 'DRAINED'"}[change]
   source['ledger_checkpoint.py']=source['ledger_checkpoint.py'].replace(change.encode(),replacement.encode())
   self.assertEqual(self.invoke(self.reseal(source))['status'],'READ_ONLY_PREFLIGHT_REFUSED')
 def test_preflight_reader_checkpoint_must_pass_real_driver_validator_path(self):
  fixture=self.readonly_fixture();source=fixture[0]
  source['stop_driver.py']=source['stop_driver.py'].replace(b"assert set(expectations)",b"raise ValueError('REGISTERED_PROJECT_GRAPH_DRIFT')\n assert set(expectations)")
  result=self.invoke(self.reseal(source));self.assertEqual(result['status'],'READ_ONLY_PREFLIGHT_REFUSED');self.assertEqual(result['code'],'REGISTERED_PROJECT_GRAPH_DRIFT')
  self.assertNotIn('checkpointValidatorPassed',result)
 def test_preflight_original_frozen_exited_or_fenced_runtime_refuses(self):
  for change,replacement in [("'frozen':False","'frozen':True"),("'processExited':False","'processExited':True"),("'fenceOwner':None","'fenceOwner':'foreign'")]:
   fixture=self.readonly_fixture();source=fixture[0];source['linux_backend.py']=source['linux_backend.py'].replace(change.encode(),replacement.encode())
   self.assertEqual(self.invoke(self.reseal(source))['status'],'READ_ONLY_PREFLIGHT_REFUSED')

class LauncherTests(unittest.TestCase):
 def test_preflight_launcher_checks_complete_local_seal_and_uses_candidate_readonly_loader(self):
  spec=importlib.util.spec_from_file_location('r8_launcher_tested',HERE/'launch_terminal.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
  source,raw,h,reads,read=ReadonlyPreflightTests().readonly_fixture()
  with tempfile.TemporaryDirectory() as tmp:
   folder=Path(tmp)/'first-stop-capsule';folder.mkdir()
   for name,value in source.items():(folder/name).write_bytes(value)
   (folder/'CAPSULE.json').write_bytes(raw)
   tty=io.StringIO();tty.isatty=lambda:True
   with patch.object(module,'__file__',str(Path(tmp)/'launcher.py')),patch.object(module,'CAPSULE_SHA',h),patch.object(module,'BOOTSTRAP_SHA',b.sha(source['bootstrap.py'])),patch.object(module.sys,'argv',['launcher.py','preflight']),patch.object(module.sys,'stdin',tty),patch.object(module.sys,'stdout',tty),patch.object(module.subprocess,'run',return_value=types.SimpleNamespace(returncode=0)) as run:
    self.assertEqual(module.main(),0)
   command=run.call_args.args[0];kwargs=run.call_args.kwargs;remote=shlex.split(command[-1]);self.assertEqual(remote[:7],['/usr/bin/sudo','-n','--','/usr/bin/python3','-I','-B','-c']);self.assertNotIn('-k',remote);self.assertIn('-T',command);self.assertNotIn('-tt',command);self.assertNotIn('capture_output',kwargs);self.assertNotIn('stdout',kwargs);self.assertNotIn('stderr',kwargs)
   loader=remote[-1];self.assertIn("MODE='preflight'",loader);self.assertIn('ALLOWED_UIDS=(0, 1000)',loader);self.assertIn('/home/ubuntu/r16-first-stop-r8-candidate/bootstrap.py',loader)
   self.assertIn('只读',tty.getvalue());self.assertIn('不安装 root',tty.getvalue())
 def test_non_tty_is_allowed_only_for_preflight_never_stop_or_recovery(self):
  spec=importlib.util.spec_from_file_location('r8_launcher_nontty_tested',HERE/'launch_terminal.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
  source,raw,h,reads,read=ReadonlyPreflightTests().readonly_fixture()
  with tempfile.TemporaryDirectory() as tmp:
   folder=Path(tmp)/'first-stop-capsule';folder.mkdir()
   for name,value in source.items():(folder/name).write_bytes(value)
   (folder/'CAPSULE.json').write_bytes(raw)
   nontty=io.StringIO();nontty.isatty=lambda:False
   for mode in ('stop','status','recover-original','preflight'):
    with self.subTest(mode=mode),patch.object(module,'__file__',str(Path(tmp)/'launcher.py')),patch.object(module,'CAPSULE_SHA',h),patch.object(module,'BOOTSTRAP_SHA',b.sha(source['bootstrap.py'])),patch.object(module.sys,'argv',['launcher.py',mode]),patch.object(module.sys,'stdin',nontty),patch.object(module.sys,'stdout',nontty),patch.object(module.subprocess,'run',return_value=types.SimpleNamespace(returncode=0)) as run:
     if mode=='preflight':self.assertEqual(module.main(),0);self.assertIn('-n',shlex.split(run.call_args.args[0][-1]))
     else:
      with self.assertRaises(SystemExit):module.main()
      run.assert_not_called()
if __name__=='__main__':unittest.main()
