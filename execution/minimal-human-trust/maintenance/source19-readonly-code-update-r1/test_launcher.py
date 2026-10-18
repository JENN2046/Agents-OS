"""Isolated ordinary-user fixtures. No sudo, SSH, production files or services.
Root identity/TTY syscalls are mocked only for held-loader protocol tests.
"""
import contextlib,io,importlib.util,json,os,stat,subprocess,sys,tempfile,unittest
from pathlib import Path
from unittest import mock
sys.dont_write_bytecode=True
REAL_UID=os.getuid()
REAL_FSTAT,REAL_STAT,REAL_LSTAT=os.fstat,os.stat,os.lstat
HERE=Path(__file__).parent
spec=importlib.util.spec_from_file_location('native_entry_launcher_test',HERE/'launch_code_update.py')
L=importlib.util.module_from_spec(spec);spec.loader.exec_module(L)

class LauncherTests(unittest.TestCase):
 def setUp(self):
  # Explicit fixture metadata seam for hosted CI uid1001. Production code
  # still accepts only actual uid1000; no runtime UID override is added.
  if REAL_UID!=1000:
   class StatView:
    def __init__(self,row):self.row=row
    def __getattr__(self,key):return 1000 if key=='st_uid'and self.row.st_uid==REAL_UID else getattr(self.row,key)
   mappings={'getuid':lambda:1000,'geteuid':lambda:1000,'fstat':lambda *a,**kw:StatView(REAL_FSTAT(*a,**kw)),'stat':lambda *a,**kw:StatView(REAL_STAT(*a,**kw)),'lstat':lambda *a,**kw:StatView(REAL_LSTAT(*a,**kw))}
   for key,value in mappings.items():
    pin=mock.patch.object(os,key,value);pin.start();self.addCleanup(pin.stop)
  self.tmp=tempfile.TemporaryDirectory(prefix='.launcher-fixture-',dir=HERE);self.addCleanup(self.tmp.cleanup);self.base=Path(self.tmp.name)
  self.source=self.base/'source';self.bundle=self.base/'bundle';self.source.mkdir(mode=0o700);self.bundle.mkdir(mode=0o700)
  self.previous=self.base/'previous';self.previous.mkdir(mode=0o700)
  self.cache=self.base/'cache';self.cache.mkdir(mode=0o700)
  self.stage=self.cache/'review'
  for key,val in {'SOURCE':self.source,'BUNDLE':self.bundle,'PREVIOUS':self.previous,'LOCAL_STAGE':self.stage}.items():
   patch=mock.patch.object(L,key,val);patch.start();self.addCleanup(patch.stop)
  self.data={'native_guard.py':b'GUARD_WAS_HELD=True\n','code_update.py':b'def main():\n print("HELD_MAIN_EXPLICIT_ONCE")\n return 0\n','review.json':b'{"separateReview":true}'}
  self.data.update({'support_admission.py':b'SUPPORT_WAS_HELD=True\n','launch_code_update.py':b'# inert fixture\n','legacy_supplement.json':b'{}'})
  for i in range(34):
   self.data['bundle/root/file-'+str(i)+'.txt']=('public-code-'+str(i)).encode()
   self.data['previous/root/file-'+str(i)+'.txt']=('previous-code-'+str(i)).encode()
  self.write_fixture()
 def write_fixture(self):
  files={}
  for name,raw in self.data.items():
   p=self.bundle/name[7:]if name.startswith('bundle/')else self.previous/name[9:]if name.startswith('previous/')else self.source/name
   p.parent.mkdir(parents=True,exist_ok=True,mode=0o700);p.write_bytes(raw);p.chmod(0o644)
   files[name]={'path':name,'sha256':L.sha(raw),'bytes':len(raw),'mode':0o644}
  self.manifest={'schema':L.SCHEMA,'files':files}
  self.save_manifest()
 def save_manifest(self):
  p=self.source/'ENTRY_FREEZE.json';p.write_text(json.dumps(self.manifest,separators=(',',':')));p.chmod(0o600)
 def packet(self):return L.capture()
 def run_main(self,args,answer='',result=0):
  with mock.patch.object(L.os,'isatty',return_value=True),mock.patch.object(L.socket,'gethostname',return_value=L.LOCAL),mock.patch('builtins.input',return_value=answer),mock.patch.object(L,'local_stage',return_value={'status':'ISOLATED_STAGE'})as local,mock.patch.object(L,'cloud_stage',return_value={'status':'ISOLATED_STAGE'})as cloud,mock.patch.object(L.subprocess,'run',return_value=mock.Mock(returncode=result))as run,contextlib.redirect_stdout(io.StringIO()):
   value=L.main(args)
  return value,local,cloud,run
 def run_loader(self,packet,core=None,tamper=False,tty=True,redirect_parent=False):
  if core is not None:
   self.data['code_update.py']=core;self.write_fixture();packet=self.packet()
  code=L.root_loader(packet,L.LOCAL,'review');compile(code,'<root-loader-isolated>','exec')
  L.local_stage(packet)
  if tamper:(self.stage/'packet.json').write_bytes(b'{}')
  if redirect_parent:
   retained=self.stage.with_name('retained');self.stage.rename(retained);self.stage.symlink_to(retained,target_is_directory=True)
  out=io.StringIO();scope={}
  with mock.patch.object(L.os,'getuid',return_value=0),mock.patch.object(L.os,'geteuid',return_value=0),mock.patch.object(L.os,'isatty',return_value=tty),mock.patch.object(L.os,'getpgrp',return_value=42),mock.patch.object(L.os,'tcgetpgrp',return_value=42),mock.patch.object(L.os,'umask'),mock.patch('resource.setrlimit'),mock.patch.object(L.socket,'gethostname',return_value=L.LOCAL),mock.patch.dict(sys.modules),mock.patch.object(sys,'argv',list(sys.argv)),contextlib.redirect_stdout(out):
   sys.modules.pop('native_guard',None);sys.modules.pop('support_admission',None)
   with self.assertRaises(SystemExit)as raised:exec(compile(code,'<root-loader-isolated>','exec'),scope)
  return raised.exception.code,out.getvalue(),scope
 def test_default_describe_never_reads_packet_or_runs_commands(self):
  with mock.patch.object(L,'capture',side_effect=AssertionError),mock.patch.object(L.subprocess,'run',side_effect=AssertionError),contextlib.redirect_stdout(io.StringIO())as out:self.assertEqual(L.main([]),0)
  self.assertEqual(json.loads(out.getvalue())['status'],'DESCRIBE_ONLY')
 def test_verify_all_74_files_without_executing_any_source(self):
  self.data['code_update.py']=b'raise RuntimeError("MUST_NOT_EXECUTE")';self.write_fixture()
  with mock.patch.object(L.subprocess,'run',side_effect=AssertionError),contextlib.redirect_stdout(io.StringIO()):self.assertEqual(L.main(['--verify']),0)
  self.assertEqual(len(self.packet()['sources']),74);self.assertFalse(self.stage.exists())
 def test_bundle_extra_file_refused(self):
  (self.bundle/'extra').write_bytes(b'x')
  with self.assertRaisesRegex(ValueError,'34FILE'):self.packet()
 def test_bundle_missing_file_refused(self):
  (self.bundle/'root/file-0.txt').unlink()
  with self.assertRaisesRegex(ValueError,'34FILE'):self.packet()
 def test_changed_source_bytes_refused(self):
  (self.source/'native_guard.py').write_bytes(b'foreign')
  with self.assertRaisesRegex(ValueError,'BYTE_PIN_DRIFT'):self.packet()
 def test_changed_mode_refused(self):
  (self.source/'native_guard.py').chmod(0o600)
  with self.assertRaisesRegex(ValueError,'METADATA'):self.packet()
 def test_symlink_source_refused(self):
  p=self.source/'native_guard.py';p.unlink();p.symlink_to(self.source/'code_update.py')
  with self.assertRaises(OSError):self.packet()
 def test_hardlink_source_refused(self):
  os.link(self.source/'native_guard.py',self.base/'second-link')
  with self.assertRaisesRegex(ValueError,'METADATA'):self.packet()
 def test_duplicate_json_and_path_escape_refused(self):
  with self.assertRaisesRegex(ValueError,'DUPLICATE'):L.parse(b'{"x":1,"x":2}')
  for name in('../x','/tmp/x','bundle/../x','a\\b','a//b'):
   with self.subTest(name=name),self.assertRaises(ValueError):L.filename(name)
 def test_arbitrary_source_path_refused(self):
  self.manifest['files']['native_guard.py']['path']='/etc/shadow';self.save_manifest()
  with self.assertRaisesRegex(ValueError,'SOURCE_PIN'):self.packet()
 def test_packet_metadata_nonfinite_or_unsafe_mode_refused(self):
  with self.assertRaisesRegex(ValueError,'INVALID_JSON'):L.parse(b'{"x":NaN}')
  self.manifest['files']['native_guard.py']['mode']=0o666;self.save_manifest()
  with self.assertRaisesRegex(ValueError,'SOURCE_PIN'):self.packet()
 def test_bundle_symlink_directory_refused(self):
  (self.bundle/'foreign').symlink_to(self.source,target_is_directory=True)
  with self.assertRaisesRegex(ValueError,'SYMLINK_DIRECTORY'):self.packet()
 def test_local_stage_exact_reuse_preserves_inode_and_refuses_conflict(self):
  p=self.packet();L.local_stage(p);node=self.stage/'packet.json';identity=node.stat().st_ino;raw=node.read_bytes();L.local_stage(p)
  self.assertEqual(node.stat().st_ino,identity);self.assertEqual(node.read_bytes(),raw)
  node.write_bytes(b'bad')
  with self.assertRaisesRegex(ValueError,'CONFLICT'):L.local_stage(p)
  self.assertEqual(node.read_bytes(),b'bad')
 def test_local_stage_foreign_entry_refused_without_overwrite(self):
  self.stage.mkdir(mode=0o700);(self.stage/'foreign').write_bytes(b'keep')
  with self.assertRaisesRegex(ValueError,'FOREIGN_FILE'):L.local_stage(self.packet())
  self.assertFalse((self.stage/'packet.json').exists())
 def test_local_stage_symlink_packet_refused(self):
  self.stage.mkdir(mode=0o700);(self.stage/'packet.json').symlink_to(self.source/'native_guard.py')
  with self.assertRaises(OSError):L.local_stage(self.packet())
 def test_cancel_before_staging_authentication_or_network(self):
  with self.assertRaisesRegex(ValueError,'HUMAN_ENTRY_CANCELLED'):self.run_main(['--cloud','update'],answer='NO')
  self.assertFalse(self.stage.exists())
 def test_non_tty_and_unknown_mode_refuse_before_packet_capture(self):
  with mock.patch.object(L.socket,'gethostname',return_value=L.LOCAL),mock.patch.object(L.os,'isatty',return_value=False),mock.patch.object(L,'capture',side_effect=AssertionError):
   with self.assertRaisesRegex(ValueError,'TTY'):L.main(['--local','update'])
  with self.assertRaisesRegex(ValueError,'ARGUMENTS'):L.main(['--local','shell'])
 def test_root_phase_all_tty_inherited_and_exit_not_retried(self):
  for result in(0,75,78):
   with self.subTest(result=result):
    value,local,cloud,run=self.run_main(['--local','review'],result=result)
    self.assertEqual(value,result);local.assert_called_once();cloud.assert_not_called();run.assert_called_once();self.assertEqual(run.call_args.kwargs,{'check':False})
 def test_lost_root_transport_or_interrupt_returns_unknown75_without_retry(self):
  for error in(OSError('raw connection error'),KeyboardInterrupt()):
   with self.subTest(error=type(error).__name__),mock.patch.object(L.os,'isatty',return_value=True),mock.patch.object(L.socket,'gethostname',return_value=L.LOCAL),mock.patch('builtins.input',return_value=''),mock.patch.object(L,'local_stage',return_value={}),mock.patch.object(L.subprocess,'run',side_effect=error)as run,contextlib.redirect_stdout(io.StringIO())as out:
    self.assertEqual(L.main(['--local','update']),75)
   run.assert_called_once();self.assertIn('ROOT_TRANSPORT_RESULT_UNKNOWN',out.getvalue());self.assertNotIn('raw connection error',out.getvalue())
 def test_cloud_staging_failure_prevents_root_authentication(self):
  with mock.patch.object(L.os,'isatty',return_value=True),mock.patch.object(L.socket,'gethostname',return_value=L.LOCAL),mock.patch('builtins.input',return_value=''),mock.patch.object(L,'cloud_stage',side_effect=ValueError('STAGE_FAILURE')),mock.patch.object(L.subprocess,'run')as run,contextlib.redirect_stdout(io.StringIO()):
   with self.assertRaisesRegex(ValueError,'STAGE_FAILURE'):L.main(['--cloud','update'])
  run.assert_not_called()
 def test_fixed_ssh_stage_is_batchmode_and_not_authentication_tty(self):
  p=self.packet();answer=json.dumps({'status':'ORDINARY_CLOUD_ENTRY_SOURCE_STAGED','packetFileHash':L.sha(L.payload(p))}).encode()
  with mock.patch.object(L.subprocess,'run',return_value=mock.Mock(returncode=0,stdout=answer))as run:L.cloud_stage(p)
  command=run.call_args.args[0];self.assertIn('-T',command);self.assertNotIn('-tt',command);self.assertIn('BatchMode=yes',command);self.assertIn('UserKnownHostsFile=/etc/r16-owner/ssh_known_hosts',command)
  self.assertEqual(run.call_args.kwargs['input'],L.payload(p));self.assertNotIn('sudo',command[-1])
 def test_cloud_root_phase_fixed_host_sudo_k_and_no_packet_in_argv(self):
  p=self.packet();command=L.invocation(p,L.CLOUD,'restore')
  self.assertIn('-tt',command);self.assertEqual(command[-2],'ubuntu@159.75.139.246');self.assertIn('/usr/bin/sudo',command[-1]);self.assertIn('-k',command[-1]);self.assertIn('/usr/bin/python3',command[-1]);self.assertNotIn('MUST_NOT_EXECUTE',command[-1])
 def test_350kb_held_packet_actual_ordinary_exec_argv_below_linux_single_arg_limit(self):
  self.data['bundle/root/file-0.txt']=b'x'*350000;self.write_fixture();p=self.packet();self.assertGreater(len(L.payload(p)),400000)
  local=L.invocation(p,L.LOCAL,'review');cloud=L.invocation(p,L.CLOUD,'review')
  for command in(local,cloud):
   self.assertLess(max(len(s.encode())for s in command),32768)
   # Real ordinary exec with the exact would-be argv strings as inert arguments.
   r=subprocess.run(['/usr/bin/python3','-I','-B','-c','import sys;print(len(sys.argv))','--',*command],capture_output=True,check=False,timeout=10)
   self.assertEqual(r.returncode,0,r.stderr)
 def test_loader_cold_explicit_main_once_from_held_bytes(self):
  p=self.packet();code,out,scope=self.run_loader(p)
  self.assertEqual(code,0);self.assertEqual(out.count('HELD_MAIN_EXPLICIT_ONCE'),1)
  self.assertEqual(scope['scope']['ENTRY_PACKET_RAW'],p['raw']);self.assertEqual(scope['scope']['HELD_PACKET_FILE_SHA'],L.sha(L.payload(p)))
 def test_loader_packet_tamper_refuses_before_core_or_guard(self):
  code,out,scope=self.run_loader(self.packet(),tamper=True)
  self.assertEqual(code,78);self.assertIn('HASH_DRIFT',out);self.assertNotIn('HELD_MAIN',out);self.assertFalse(json.loads(out)['automaticRetry']);self.assertNotIn('guard',scope)
 def test_loader_rejects_symlink_parent_before_reading_packet(self):
  code,out,scope=self.run_loader(self.packet(),redirect_parent=True)
  self.assertEqual(code,78);self.assertNotIn('HELD_MAIN',out);self.assertNotIn('guard',scope)
  self.assertNotIn('fd',scope);self.assertFalse(json.loads(out)['automaticRetry'])
 def test_loader_requires_foreground_tty(self):
  code,out,_=self.run_loader(self.packet(),tty=False)
  self.assertEqual(code,78);self.assertIn('FOREGROUND_TTY',out);self.assertNotIn('HELD_MAIN',out)
 def test_loader_unknown_effect_returns_75_without_private_exception_or_traceback(self):
  code,out,_=self.run_loader(self.packet(),b'def main():\n global EFFECTS_STARTED\n EFFECTS_STARTED=True\n raise RuntimeError("secret raw text never export")\n')
  self.assertEqual(code,75);self.assertEqual(json.loads(out)['code'],'ROOT_NATIVE_ENTRY_REFUSED_OR_UNKNOWN');self.assertNotIn('secret',out);self.assertNotIn('Traceback',out)
 def test_loader_preeffect_error_returns_78_fixed_code(self):
  code,out,_=self.run_loader(self.packet(),b'def main():\n raise ValueError("FIXED_PRECONDITION_REFUSED")\n')
  self.assertEqual(code,78);self.assertEqual(json.loads(out)['code'],'FIXED_PRECONDITION_REFUSED')
 def test_real_ordinary_stager_reuses_exact_file_and_refuses_changed_bytes(self):
  # Execute only the ordinary staging script in a private test tree, never SSH.
  script=L.STAGER.replace("/home/ubuntu/source19-readonly-code-update-r1",str(self.stage)).replace(L.CLOUD,L.socket.gethostname()).replace('==1000','=='+str(REAL_UID))
  packet=L.payload(self.packet())
  def run(raw):return subprocess.run(['/usr/bin/python3','-I','-B','-c',script],input=raw,capture_output=True,check=False,timeout=10)
  first=run(packet);self.assertEqual(first.returncode,0,first.stderr);before=(self.stage/'packet.json').stat()
  self.assertEqual(run(packet).returncode,0);self.assertEqual(before.st_ino,(self.stage/'packet.json').stat().st_ino)
  self.assertNotEqual(run(b'changed').returncode,0);self.assertEqual((self.stage/'packet.json').read_bytes(),packet)
 def test_real_ordinary_stager_symlink_file_refused(self):
  self.stage.mkdir(mode=0o700);(self.stage/'packet.json').symlink_to(self.source/'native_guard.py')
  script=L.STAGER.replace("/home/ubuntu/source19-readonly-code-update-r1",str(self.stage)).replace(L.CLOUD,L.socket.gethostname()).replace('==1000','=='+str(REAL_UID))
  r=subprocess.run(['/usr/bin/python3','-I','-B','-c',script],input=L.payload(self.packet()),capture_output=True,check=False,timeout=10)
  self.assertNotEqual(r.returncode,0);self.assertTrue((self.stage/'packet.json').is_symlink())
 def test_root_never_imports_ordinary_path_or_rereads_core(self):
  p=self.packet();self.data['code_update.py']=b'raise RuntimeError("DISK_CHANGED_SOURCE")';self.write_fixture()
  code,out,_=self.run_loader(p)
  self.assertEqual(code,0);self.assertIn('HELD_MAIN_EXPLICIT_ONCE',out);self.assertNotIn('DISK_CHANGED_SOURCE',out)

if __name__=='__main__':unittest.main()
