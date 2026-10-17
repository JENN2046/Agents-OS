"""Sealed loader/TTY contracts, entirely synthetic source and temp files.

No SSH/root authentication, protected paths, service effects or private state.
"""
import ast
import copy
import importlib.util
import io
import json
from pathlib import Path
import shlex
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

HERE=Path(__file__).resolve().parent
def load(name,path):
 spec=importlib.util.spec_from_file_location(name,path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module
b=load('quarantine_bootstrap_tested',HERE/'bootstrap.py')
launcher=load('quarantine_launcher_tested',HERE/'launch_terminal.py')

class BootstrapTests(unittest.TestCase):
 def setUp(self):
  self.prior_modules={name:sys.modules.pop(name,None) for name,_ in b.LOAD_ORDER}
  self.addCleanup(self.restore_loaded_names)
  self.probe=types.ModuleType('quarantine_bootstrap_test_probe');self.probe.copies=[];self.probe.calls=[]
  self.oldprobe=sys.modules.get(self.probe.__name__);sys.modules[self.probe.__name__]=self.probe
  self.addCleanup(self.restore_probe)
 def restore_loaded_names(self):
  for name,value in self.prior_modules.items():
   sys.modules.pop(name,None)
   if value is not None:sys.modules[name]=value
 def restore_probe(self):
  if self.oldprobe is None:sys.modules.pop(self.probe.__name__,None)
  else:sys.modules[self.probe.__name__]=self.oldprobe
 def fixture(self):
  source={name:b'{}' if name.endswith('.json') else b'# isolated inert member\n' for name in b.REQUIRED}
  source['r8/TARGET.json']=b'{"unit":"synthetic-original-service","pid":12345}'
  source['r8/common_safe.py']=b'import quarantine_bootstrap_test_probe as p\ndef immutable(path,raw,mode):p.copies.append((str(path),raw,mode))\n'
  source['entry.py']=b"import quarantine_bootstrap_test_probe as p\ndef entry(mode,pin,target):\n p.calls.append((mode,pin,target))\n return {'status':'SYNTHETIC_ENTRY_RESULT'}\n"
  r8={'schema':'r16.first-stop-capsule.v1','files':{name:b.sha(source['r8/'+name]) for name in b.R8_NAMES}}
  source['r8/CAPSULE.json']=json.dumps(r8).encode();r8hash=b.sha(source['r8/CAPSULE.json'])
  return self.reseal(source,r8hash)
 def reseal(self,source,r8hash):
  manifest={'schema':'r16.empty-temp-quarantine-capsule.v1','policyProposalSha256':b.POLICY,'sourceCapsuleHash':r8hash,'nativeExecutionAlreadyAuthorized':False,'files':{name:b.sha(value) for name,value in source.items()}}
  raw=json.dumps(manifest).encode();reads=[];base=[b.CANDIDATE]
  result=types.SimpleNamespace(source=source,manifest=manifest,raw=raw,pin=b.sha(raw),r8hash=r8hash,reads=reads,base=base)
  def read(path,root_only=False):
   reads.append((Path(path),root_only))
   return result.raw if Path(path).name=='CAPSULE.json' and Path(path).parent.name!='r8' else source[str(Path(path).relative_to(base[0]))]
  result.read=read;return result
 def invoke(self,mode,fixture,capacity=100*1024*1024):
  fixture.base[0]=b.CANDIDATE if mode in ('preflight','execute') else b.ROOT/fixture.pin
  with patch.object(b,'R8_CAPSULE',fixture.r8hash),patch.object(b,'read',side_effect=fixture.read),patch.object(b.os,'getuid',return_value=0),patch.object(b.os,'geteuid',return_value=0),patch.object(b.socket,'gethostname',return_value='VM-0-12-ubuntu'),patch.object(b.resource,'setrlimit'),patch.object(b.os,'statvfs',return_value=types.SimpleNamespace(f_bavail=capacity,f_frsize=1)):
   return b.run(mode,fixture.pin)
 def test_complete_seal_before_memory_load_and_no_candidate_path_import(self):
  f=self.fixture();path=list(sys.path);prior=set(sys.modules)
  result=self.invoke('preflight',f)
  self.assertEqual(result['status'],'SYNTHETIC_ENTRY_RESULT');self.assertEqual(self.probe.copies,[])
  self.assertEqual(len(f.reads),len(b.REQUIRED)+1);self.assertEqual(sys.path,path);self.assertFalse(set(sys.modules)-prior)
  self.assertEqual(self.probe.calls,[('preflight',f.pin,{'unit':'synthetic-original-service','pid':12345})])
  self.assertTrue(all(not root for _,root in f.reads))
 def test_execute_copies_only_already_sealed_bytes_before_entry(self):
  f=self.fixture();self.invoke('execute',f)
  copied={Path(path).relative_to(b.ROOT/f.pin).as_posix():(raw,mode) for path,raw,mode in self.probe.copies}
  self.assertEqual(copied,{**{name:(raw,0o644) for name,raw in f.source.items()},'CAPSULE.json':(f.raw,0o644)})
  self.assertEqual(self.probe.calls[0][0],'execute')
 def test_execute_insufficient_root_space_refuses_before_any_source_install(self):
  f=self.fixture()
  with self.assertRaisesRegex(ValueError,'QUARANTINE_SOURCE_INSTALL_SPACE_UNPROVEN'):self.invoke('execute',f,capacity=1)
  self.assertEqual(self.probe.copies,[]);self.assertEqual(self.probe.calls,[]);self.assertTrue(all(name not in sys.modules for name,_ in b.LOAD_ORDER))

 def test_preflight_status_and_recovery_never_install_any_source(self):
  for mode in ('preflight','status','recover'):
   with self.subTest(mode=mode):
    f=self.fixture();self.invoke(mode,f);self.assertEqual(self.probe.copies,[])
    self.assertEqual({root for _,root in f.reads},{mode!='preflight'})
    self.assertTrue(all(p.is_relative_to(f.base[0]) for p,_ in f.reads))
 def test_tamper_any_member_refuses_before_any_module_exec_or_copy(self):
  f=self.fixture();f.source['driver.py']+=b'\nraise AssertionError("unverified source executed")'
  with self.assertRaisesRegex(ValueError,'CAPSULE_MEMBER_CHANGED'):self.invoke('execute',f)
  self.assertEqual(self.probe.copies,[]);self.assertEqual(self.probe.calls,[])
 def test_valid_outer_seal_cannot_replace_pinned_r8_dependency(self):
  f=self.fixture();f.source['r8/linux_backend.py']+=b'\n# malicious replacement'
  f=self.reseal(f.source,f.r8hash)
  with self.assertRaisesRegex(ValueError,'SOURCE_DEPENDENCY_DRIFT'):self.invoke('preflight',f)
  self.assertEqual(self.probe.calls,[])
 def test_native_authorization_claim_and_unexpected_members_are_rejected(self):
  for change in ('authority','set'):
   f=self.fixture()
   if change=='authority':f.manifest['nativeExecutionAlreadyAuthorized']=True
   else:f.manifest['files']['unreviewed.py']='1'*64
   f.raw=json.dumps(f.manifest).encode();f.pin=b.sha(f.raw)
   with self.subTest(change=change),self.assertRaisesRegex(ValueError,'CAPSULE_SCOPE_REFUSED' if change=='authority' else 'CAPSULE_FILE_SET_REFUSED'):self.invoke('preflight',f)
   self.assertEqual(self.probe.calls,[])
 def test_failed_memory_module_load_cleans_all_names(self):
  f=self.fixture();f.source['backend.py']=b'raise ValueError("SYNTHETIC_LOAD_FAILURE")';f=self.reseal(f.source,f.r8hash)
  with self.assertRaisesRegex(ValueError,'SYNTHETIC_LOAD_FAILURE'):self.invoke('preflight',f)
  self.assertTrue(all(name not in sys.modules for name,_ in b.LOAD_ORDER));self.assertEqual(self.probe.calls,[])
 def test_foreign_module_collision_refuses_and_does_not_replace_foreign_code(self):
  foreign=types.ModuleType('r8_linux_backend');sys.modules['r8_linux_backend']=foreign
  with self.assertRaisesRegex(ValueError,'SEALED_MODULE_COLLISION'):self.invoke('preflight',self.fixture())
  self.assertIs(sys.modules['r8_linux_backend'],foreign);self.assertNotIn('r8_common_safe',sys.modules);self.assertEqual(self.probe.calls,[])

 def test_nonroot_or_wrong_host_refuse_before_read_and_core_disabled_first(self):
  for uid,host in ((1000,'VM-0-12-ubuntu'),(0,'different-host')):
   events=[]
   with patch.object(b.resource,'setrlimit',side_effect=lambda *a:events.append('core-disabled')),patch.object(b.os,'getuid',return_value=uid),patch.object(b.os,'geteuid',return_value=uid),patch.object(b.socket,'gethostname',return_value=host),patch.object(b,'read',side_effect=AssertionError('unauthorized read')):
    with self.assertRaisesRegex(ValueError,'FIXED_CLOUD_ROOT_REQUIRED'):b.run('preflight','1'*64)
   self.assertEqual(events,['core-disabled'])
 def test_actual_cli_tail_success_and_refusal_exit_codes_and_redaction(self):
  # Execute the actual unmodified __main__ AST, replacing only its run adapter.
  tree=ast.parse((HERE/'bootstrap.py').read_text());cli=compile(ast.Module(body=[tree.body[-1]],type_ignores=[]),'<actual-bootstrap-cli>','exec')
  success=('QUARANTINE_READ_ONLY_PREFLIGHT_PASS','EMPTY_ARTIFACT_QUARANTINED_ORIGINAL_RUNTIME_RESTORED','ARTIFACT_RESTORED_NOT_BUSINESS_ACCEPTED','QUARANTINE_ABORTED_ORIGINAL_ARTIFACT_AND_RUNTIME_RESTORED','READ_ONLY_STATUS')
  for status in (*success,'RECOVERY_REQUIRED','NATIVE_APPROVAL_PENDING'):
   stdout=io.StringIO();namespace={'__name__':'__main__','sys':types.SimpleNamespace(argv=['bootstrap.py','preflight','1'*64]),'json':json,'need':b.need,'bounded_code':b.bounded_code,'run':lambda *args:{'status':status}}
   with self.subTest(status=status),patch('sys.stdout',stdout),self.assertRaises(SystemExit) as stop:exec(cli,namespace)
   self.assertEqual(stop.exception.code,0 if status in success else 78);self.assertEqual(json.loads(stdout.getvalue())['status'],status)
  stdout=io.StringIO();namespace['run']=lambda *args:(_ for _ in ()).throw(RuntimeError('PRIVATE_UNSAFE_RAW_ERROR'))
  with patch('sys.stdout',stdout),self.assertRaises(SystemExit) as stop:exec(cli,namespace)
  self.assertEqual(stop.exception.code,78);self.assertNotIn('PRIVATE',stdout.getvalue());self.assertEqual(json.loads(stdout.getvalue())['code'],'PROTECTED_QUARANTINE_ENTRY_REFUSED')

class LauncherTests(unittest.TestCase):
 def fixture(self,root):
  folder=root/'capsule';folder.mkdir();source={'bootstrap.py':b'# inert pinned bootstrap\n','driver.py':b'# inert driver\n'}
  for name,raw in source.items():(folder/name).write_bytes(raw)
  raw=json.dumps({'files':{name:b.sha(value) for name,value in source.items()}}).encode();(folder/'CAPSULE.json').write_bytes(raw)
  return b.sha(raw),b.sha(source['bootstrap.py'])
 def invoke(self,root,pin,boot,mode,tty):
  stream=io.StringIO();stream.isatty=lambda:tty
  return patch.multiple(launcher,CAPSULE_SHA=pin,BOOTSTRAP_SHA=boot,__file__=str(root/'launcher.py')),patch.object(launcher.sys,'argv',['launcher.py',mode]),patch.object(launcher.sys,'stdin',stream),patch.object(launcher.sys,'stdout',stream)
 def test_readonly_vs_native_ssh_tty_sudo_and_installed_candidate_paths(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);pin,boot=self.fixture(root)
   for mode in ('preflight','execute','status','recover'):
    contexts=self.invoke(root,pin,boot,mode,mode in ('execute','recover'))
    with self.subTest(mode=mode),contexts[0],contexts[1],contexts[2],contexts[3],patch.object(launcher.subprocess,'run',return_value=types.SimpleNamespace(returncode=0)) as run:
     self.assertEqual(launcher.main(),0)
    command=run.call_args.args[0];kwargs=run.call_args.kwargs;remote=shlex.split(command[-1]);readonly=mode in ('preflight','status')
    self.assertEqual(remote[:7],['/usr/bin/sudo','-n' if readonly else '-k','--','/usr/bin/python3','-I','-B','-c']);self.assertIn('-T' if readonly else '-tt',command)
    for field in ('stdin','stdout','stderr','capture_output','input'):self.assertNotIn(field,kwargs)
    loader=remote[-1];self.assertIn('MODE='+repr(mode),loader)
    self.assertIn('OWNERS=(0, 1000)' if mode in ('preflight','execute') else 'OWNERS=(0,)',loader)
    self.assertIn('/home/ubuntu/r16-empty-temp-quarantine-r1-candidate' if mode in ('preflight','execute') else '/usr/lib/r16-maintenance/empty-temp-quarantine-r1/'+pin,loader)
    self.assertIn('RLIMIT_CORE',loader);self.assertIn('PINNED_BOOTSTRAP_CHANGED',loader)
 def test_non_tty_execute_and_recover_refuse_before_any_ssh(self):
  for mode in ('execute','recover'):
   with tempfile.TemporaryDirectory() as tmp:
    root=Path(tmp);pin,boot=self.fixture(root);contexts=self.invoke(root,pin,boot,mode,False)
    with contexts[0],contexts[1],contexts[2],contexts[3],patch.object(launcher.subprocess,'run') as run:
     with self.assertRaises(SystemExit):launcher.main()
     run.assert_not_called()
 def test_local_member_tamper_and_symlink_prevent_all_remote_action(self):
  for change in ('bytes','symlink'):
   with tempfile.TemporaryDirectory() as tmp:
    root=Path(tmp);pin,boot=self.fixture(root);member=root/'capsule/driver.py'
    if change=='bytes':member.write_bytes(b'modified')
    else:member.unlink();member.symlink_to(root/'capsule/bootstrap.py')
    contexts=self.invoke(root,pin,boot,'preflight',False)
    with contexts[0],contexts[1],contexts[2],contexts[3],patch.object(launcher.subprocess,'run') as run:
     with self.assertRaises(SystemExit):launcher.main()
     run.assert_not_called()
 def test_local_manifest_tamper_prevents_ssh(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);pin,boot=self.fixture(root);(root/'capsule/CAPSULE.json').write_bytes(b'{}');contexts=self.invoke(root,pin,boot,'preflight',False)
   with contexts[0],contexts[1],contexts[2],contexts[3],patch.object(launcher.subprocess,'run') as run:
    with self.assertRaises(SystemExit):launcher.main()
    run.assert_not_called()

if __name__=='__main__':unittest.main()
