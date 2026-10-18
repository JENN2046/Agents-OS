"""Isolated protocol/syscall/tempfile tests. No sudo, SSH, root or real service."""
import importlib.util,json,os,stat,sys,tempfile,time,unittest
from contextlib import ExitStack,contextmanager
from pathlib import Path
from unittest.mock import Mock,patch
HERE=Path(__file__).resolve().parent
@contextmanager
def modules():
 with patch.dict(sys.modules):
  loaded={}
  for name in('common','native_guard','foreground','rpc','transport','service_main','bootstrap'):
   spec=importlib.util.spec_from_file_location(name,HERE/(name+'.py'));m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);loaded[name]=m
  yield loaded
class EntryTests(unittest.TestCase):
 def setUp(self):
  self.exit=ExitStack();self.addCleanup(self.exit.close);self.m=self.exit.enter_context(modules());self.c=self.m['common'];self.f=self.m['foreground'];self.r=self.m['rpc']
 def acceptance(self):return {'schema':'r16.source19-native-transition.native-acceptance.v1','acceptedAt':1000,'acceptedMonotonicNs':'2000000','bootId':'boot','pending':{'targetHashes':{'native':'d'*64}}}
 def plan(self):return {'approvedAt':1000,'expiresAt':301000,'recoveryDeadline':1801000,'nativeTargetHash':'d'*64}
 def packet(self,op='readback',payload=None):return self.c.canonical({'schema':'r16.source19-native-transition.rpc.v1','capsuleHash':'a'*64,'planHash':'b'*64,'requestId':'c'*32,'payload':{}if payload is None else payload})
 def test_describe_does_not_read_write_or_authenticate(self):
  with patch.object(self.f,'root',side_effect=AssertionError('no root')),patch.object(self.f,'verify_capsule',side_effect=AssertionError('no filesystem')):
   self.assertEqual(self.f.main([])['productionEffects'],0);self.assertFalse(self.f.main(['--describe'])['humanIdentityConfirmed'])
 def test_no_boolean_or_serialized_authority(self):
  with self.assertRaisesRegex(Exception,'NATIVE_AUTHORITY_REQUIRED'):self.f.Authority(True,self.plan(),self.acceptance(),self.c.LOCAL)
  with self.assertRaisesRegex(Exception,'BRANDED_NATIVE_AUTHORITY_REQUIRED'):self.f.assert_capability({'environment':'PRODUCTION','approved':True})
 def test_authority_wall_mono_boot_and_exact_plan_limits(self):
  t=[1000];mono=[2000000];a=self.f.Authority(self.f._BRAND,self.plan(),self.acceptance(),self.c.LOCAL,clock=lambda:t[0],mono=lambda:mono[0]);h=self.c.digest(self.plan())
  with patch.object(self.f,'root'),patch.object(self.f,'boot_id',return_value='boot'):
   a.require(h,'checkpoint');self.assertRaisesRegex(Exception,'AUTHORITY_PLAN_DRIFT',a.require,'f'*64,'inspect')
   mono[0]+=1800000000000;self.assertRaisesRegex(Exception,'NATIVE_WINDOW_EXPIRED',a.require,h,'inspect')
   mono[0]=2000000;t[0]=1801000;self.assertRaisesRegex(Exception,'NATIVE_WINDOW_EXPIRED',a.require,h,'inspect')
  with patch.object(self.f,'root'),patch.object(self.f,'boot_id',return_value='newboot'):self.assertRaisesRegex(Exception,'NATIVE_BOOT_CHANGED',a.require,h,'inspect')
 def test_forward_cannot_borrow_recovery_window(self):
  a=self.f.Authority(self.f._BRAND,self.plan(),self.acceptance(),self.c.LOCAL,clock=lambda:400000,mono=lambda:3000000)
  with patch.object(self.f,'root'),patch.object(self.f,'boot_id',return_value='boot'):
   self.assertRaisesRegex(Exception,'READONLY_SOURCE_NATIVE_EFFECTS_DISABLED',a.require,self.c.digest(self.plan()),'stage')
 def test_template_has_no_unknown_poststop_hash_or_oldtime(self):
  acceptance={**self.acceptance(),'pending':{'nonce':'e'*32,'stopEpoch':'epoch'}};fields={'originalBaselineHash':'a'*64,'nativeTargetHash':'b'*64,'approvedControlUnknownHash':'c'*64,'approvedControlUnknownCount':0,'revisionPlanHash':'d'*64}
  p=self.f.plan_from_acceptance({'schema':'plan'},fields,acceptance,600000);self.assertEqual(p['expiresAt'],301000);self.assertEqual(p['recoveryDeadline'],600000)
  self.assertRaisesRegex(Exception,'PRESTOP_TEMPLATE_CYCLE_OR_TIME',self.f.plan_from_acceptance,{'checkpointHash':'f'*64},fields,acceptance,600000)
 def test_cancelled_or_partial_human_line_mints_no_authority(self):
  pending={'nonce':'e'*32};actor={'launcher':{'pid':19},'humanIdentityConfirmed':False}
  with patch.object(self.f,'identity',return_value=actor),patch.object(self.f.os,'open',return_value=91),patch.object(self.f.os,'close'),patch.object(self.f.os,'isatty',return_value=True),patch.object(self.f.os,'tcgetpgrp',return_value=12),patch.object(self.f.os,'getpgrp',return_value=12),patch.object(self.f.os,'write',side_effect=lambda fd,b:len(b)),patch.object(self.f.os,'read',side_effect=[b'M',b'\n']):
   self.assertRaisesRegex(Exception,'NATIVE_CONFIRMATION_CANCELLED',self.f.native_confirm,pending,self.c.LOCAL)
 def test_full_line_then_identity_reread_then_window_mint(self):
  pending={'nonce':'e'*32};actor={'launcher':{'pid':19},'humanIdentityConfirmed':False};words=b'MAINTAIN SOURCE19 '+self.c.digest({**pending,'nativeHostAdmin':actor}).encode()+b'\n';reads=iter(bytes([b])for b in words);order=[]
  with patch.object(self.f,'identity',side_effect=lambda host:order.append('identity')or actor),patch.object(self.f,'boot_id',return_value='boot'),patch.object(self.f.os,'open',return_value=91),patch.object(self.f.os,'close'),patch.object(self.f.os,'isatty',return_value=True),patch.object(self.f.os,'tcgetpgrp',return_value=12),patch.object(self.f.os,'getpgrp',return_value=12),patch.object(self.f.os,'write',side_effect=lambda fd,b:len(b)),patch.object(self.f.os,'read',side_effect=lambda *a:next(reads)):
   a=self.f.native_confirm(pending,self.c.LOCAL,clock=lambda:order.append('clock')or 1000,mono=lambda:2000)
  self.assertEqual(order,['identity','identity','clock']);self.assertEqual(a['acceptedAt'],1000);self.assertFalse(a['humanIdentityConfirmed'])
 def test_foreground_identity_changes_no_mint(self):
  pending={};actor={'p':1};words=b'MAINTAIN SOURCE19 '+self.c.digest({'nativeHostAdmin':actor}).encode()+b'\n';reads=iter(bytes([b])for b in words)
  with patch.object(self.f,'identity',side_effect=[actor,{'p':2}]),patch.object(self.f.os,'open',return_value=91),patch.object(self.f.os,'close'),patch.object(self.f.os,'isatty',return_value=True),patch.object(self.f.os,'tcgetpgrp',return_value=1),patch.object(self.f.os,'getpgrp',return_value=1),patch.object(self.f.os,'write',side_effect=lambda fd,b:len(b)),patch.object(self.f.os,'read',side_effect=lambda *a:next(reads)):
   self.assertRaisesRegex(Exception,'NATIVE_ACTOR_CHANGED',self.f.native_confirm,pending,self.c.LOCAL)
 def test_rpc_exact_scope_rejects_shell_pid_path_role_and_oversize(self):
  self.r.packet(self.packet(),'readback','b'*64)
  for op,payload in [('shell',{}),('stop',{'unit':'r16-native.service'}),('stage',{'path':'/tmp/a'}),('stop',{'unit':'r16-app.service','pid':99})]:self.assertRaises(Exception,self.r.packet,self.packet(op,payload),op,'b'*64)
  self.assertRaisesRegex(Exception,'RPC_INPUT_TOO_LARGE',self.r.packet,b'x'*(4*1024*1024+1),'readback','b'*64)
 def test_cloud_admit_cannot_replace_its_native_baseline_or_template(self):
  cloud={'templateHash':self.c.digest({'target':'fixed'}),'capsuleHash':'a'*64,'originalBaseline':{'r16-app.service':{'pid':5}}};p={'payload':{'plan':{},'originalBaseline':{'r16-app.service':{'pid':7}},'localAcceptanceHash':'c'*64},'planHash':self.c.digest({}),'capsuleHash':'a'*64}
  with patch.object(self.r,'immutable',side_effect=AssertionError('no effect')):self.assertRaisesRegex(Exception,'READONLY_SOURCE_RPC_EFFECTS_DISABLED',self.r.admit,{'planTemplate':{'target':'fixed'}},p,cloud)
 def test_transport_timeout_no_retry_or_stderr_leak(self):
  transport=self.m['transport']
  with patch.object(transport,'root'):
   a=transport.CloudTransport('a'*64,'b'*64)
  import subprocess
  with patch.object(transport.subprocess,'run',side_effect=subprocess.TimeoutExpired('fixed',1))as run:
   self.assertRaisesRegex(Exception,'RPC_REPLY_UNKNOWN_NOT_RETRIED',a.call,'stop',{'unit':'r16-app.service'},'c'*32);self.assertEqual(run.call_count,1)
 def test_transport_stage_budget_exceeds_cloud_inner_and_nohuman_capture(self):
  transport=self.m['transport']
  with patch.object(transport,'root'):a=transport.CloudTransport('a'*64,'b'*64)
  with patch.object(transport.subprocess,'run',return_value=Mock(returncode=0,stdout=b'{"planHash":"'+b'b'*64+b'"}'))as run:
   a.call('stage',{},'c'*32);self.assertEqual(run.call_args.kwargs['timeout'],150);self.assertNotIn('-tt',run.call_args.args[0]);self.assertIn('BatchMode=yes',run.call_args.args[0])
   a.call('readback',{},'d'*32);self.assertEqual(run.call_args.kwargs['timeout'],30)
 def test_service_cannot_mint_authority_or_load_any_key(self):
  self.assertRaisesRegex(Exception,'READONLY_SOURCE_NATIVE_EFFECTS_DISABLED',self.m['service_main'].service_authority)
  self.assertRaisesRegex(Exception,'READONLY_SOURCE_NATIVE_EFFECTS_DISABLED',self.m['service_main'].main,[])

 def test_bootstrap_memory_import_never_rereads_mutable_source(self):
  loader=self.m['bootstrap'].SealedModules({'example.py':b'VALUE=42'});loader.names['entry_example']='example.py';sys.meta_path.insert(0,loader);self.addCleanup(lambda:sys.meta_path.remove(loader));self.addCleanup(lambda:sys.modules.pop('entry_example',None))
  import entry_example
  self.assertEqual(entry_example.VALUE,42)
 def test_real_noreplace_preserves_existing_bytes_inode_and_pending(self):
  with tempfile.TemporaryDirectory()as d:
   a=Path(d)/'a';b=Path(d)/'b';a.write_bytes(b'new');b.write_bytes(b'old');ino=b.stat().st_ino
   self.assertRaises(FileExistsError,self.c.noreplace,a,b);self.assertEqual(b.read_bytes(),b'old');self.assertEqual(b.stat().st_ino,ino);self.assertEqual(a.read_bytes(),b'new')
 def test_templates_only_fixed_original_credentials_no_restart(self):
  unit=(HERE/'r16-source19-native-transition-r1.service').read_text();self.assertIn('Restart=no',unit);self.assertIn('SendSIGKILL=no',unit);self.assertEqual(unit.count('LoadCredentialEncrypted='),0);self.assertNotIn('EnvironmentFile=',unit);self.assertNotIn('r16-owner.service',unit)
 def test_preflight_verifies_real_inputs_without_creating_state_lock_or_native_intent(self):
  baseline={'r16-native.service':{'pid':12}};prepared={'planFields':{'originalBaselineHash':self.c.digest(baseline)},'factsHash':'f'*64,'revisionInventory':{},'revisionPlan':{},'originalBaseline':baseline,'historyInput':{}}
  adapter=Mock();adapter.prepare.return_value=prepared
  with patch.object(self.f,'root',return_value=self.c.LOCAL),patch.object(self.f.resource,'setrlimit'),patch.object(self.f.os,'umask'),patch.object(self.f,'verify_capsule',return_value={'planTemplate':{}}),patch.object(self.f,'load_adapter',return_value=adapter),patch.object(self.f,'mkdir',side_effect=AssertionError('no state create')),patch.object(self.f,'lock',side_effect=AssertionError('no lock')),patch.object(self.f,'native_confirm',side_effect=AssertionError('no approval')):
   result=self.f.main(['preflight','a'*64]);self.assertEqual(result['productionEffects'],0);self.assertFalse(result['nativeIntentCreated'])
 def test_real_full_source_package_byte_set_validation_and_drift(self):
  # Only root metadata reading is substituted. Hashing, exact membership,
  # relative path/mode/schema and real files remain the production verifier.
  with tempfile.TemporaryDirectory()as d:
   root=Path(d)/'root';state=Path(d)/'state';runtime=root/'runtime';package=state/'package';runtime.mkdir(parents=True);package.mkdir(parents=True)
   import ast
   tree=ast.parse((HERE/'common.py').read_text());names=None
   for node in ast.walk(tree):
    if isinstance(node,ast.Assign)and any(isinstance(t,ast.Name)and t.id=='required'for t in node.targets):names=ast.literal_eval(node.value)
   files={}
   for name in names:
    raw=b'public source';path=runtime/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(raw);path.chmod(0o644);files[name]={'sha256':self.c.sha(raw),'mode':0o644,'bytes':len(raw)}
   package_rows={}
   for n in range(10):
    name='payload/public-'+str(n);path=package/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(b'payload');path.chmod(0o644);package_rows[name]={'sha256':self.c.sha(b'payload'),'bytes':7,'mode':0o644}
   m={'mode':'READONLY_PREFLIGHT_SOURCE','schema':'r16.source19-native-transition.entry-freeze.v1','files':files,'packageFiles':package_rows,'revisionRequest':{'forward':None,'recovery':None,'legacy21_22Disposition':'CANCELLED_UNALLOCATED_REPLAN'},'planTemplate':{'sourcePublicConfigHash':self.c.SOURCE,'sourceDeliveryHash':self.c.DELIVERY,'targetReleaseId':self.c.TARGET}};raw=self.c.canonical(m);(root/'ENTRY_FREEZE.json').write_bytes(raw);capsule=self.c.sha(raw)
   for directory,children,fsnames in os.walk(d):Path(directory).chmod(0o755)
   real_lstat=Path.lstat
   class Meta:
    def __init__(self,row):self.row=row;self.st_uid=0
    def __getattr__(self,n):return getattr(self.row,n)
   def fixture_read(path,maximum=32*1024*1024,mode=None):
    raw=Path(path).read_bytes();self.assertLessEqual(len(raw),maximum)
    # Original manifest is required root600 but this is only a tmp fixture;
    # all ordinary source/payload rows retain real byte/mode assertions.
    if mode not in(None,0o600):self.assertEqual(stat.S_IMODE(Path(path).stat().st_mode),mode)
    return raw
   with patch.object(self.c,'ROOT',root),patch.object(self.c,'STATE',state),patch.object(self.c,'read',side_effect=fixture_read),patch.object(Path,'lstat',side_effect=lambda p:Meta(real_lstat(p)),autospec=True):
    self.assertEqual(self.c.verify_capsule(capsule),m)
    (package/'payload/public-0').write_bytes(b'changed');self.assertRaisesRegex(Exception,'PACKAGE_BYTES_DRIFT',self.c.verify_capsule,capsule);(package/'payload/public-0').write_bytes(b'payload')
    (runtime/'foreign.py').write_bytes(b'extra');self.assertRaisesRegex(Exception,'SOURCE_EXACT_SET_DRIFT',self.c.verify_capsule,capsule);(runtime/'foreign.py').unlink()
    (package/'foreign').write_bytes(b'extra');self.assertRaisesRegex(Exception,'PACKAGE_EXACT_SET_DRIFT',self.c.verify_capsule,capsule)
 def test_readonly_authority_rejects_every_effect_even_with_old_native_acceptance(self):
  a=self.f.Authority(self.f._BRAND,self.plan(),self.acceptance(),self.c.LOCAL,clock=lambda:1001,mono=lambda:2000001)
  for op in('stage','sign','commit','native-signal','native-freeze','thaw-native','os-write','journal-write','restore:r16-owner.service','activate:r16-native.service','requiesce:r16-native.service'):
   self.assertRaisesRegex(Exception,'READONLY_SOURCE_NATIVE_EFFECTS_DISABLED',a.require,self.c.digest(self.plan()),op)

 def test_complete_human_operator_cloud_failure_never_enters_local_and_inherits_tty(self):
  import io
  spec=importlib.util.spec_from_file_location('entry_operator',HERE/'operator.py');operator=importlib.util.module_from_spec(spec);spec.loader.exec_module(operator)
  with patch.object(operator.os,'getuid',return_value=1000),patch.object(operator.os,'geteuid',return_value=1000),patch.object(operator.socket,'gethostname',return_value=operator.LOCAL),patch.object(operator.os,'isatty',return_value=True),patch('builtins.input',return_value=''),patch.object(operator.subprocess,'run',return_value=Mock(returncode=78))as run,patch('sys.stdout',new_callable=io.StringIO):
   self.assertEqual(operator.main(['--preflight']),78);self.assertEqual(run.call_count,1);self.assertNotIn('stdout',run.call_args.kwargs);self.assertNotIn('stdin',run.call_args.kwargs);self.assertIn('-tt',run.call_args.args[0]);self.assertIn('/usr/bin/sudo',run.call_args.args[0][-1])
 def test_human_operator_cancellation_zero_subprocess_and_local75_preserved(self):
  import io
  spec=importlib.util.spec_from_file_location('entry_operator',HERE/'operator.py');operator=importlib.util.module_from_spec(spec);spec.loader.exec_module(operator)
  with patch.object(operator.os,'getuid',return_value=1000),patch.object(operator.os,'geteuid',return_value=1000),patch.object(operator.socket,'gethostname',return_value=operator.LOCAL),patch.object(operator.os,'isatty',return_value=True),patch('builtins.input',return_value='cancel'),patch.object(operator.subprocess,'run')as run,patch('sys.stdout',new_callable=io.StringIO):
   self.assertRaisesRegex(Exception,'HUMAN_START_CANCELLED',operator.main,['--preflight']);run.assert_not_called()
  with patch.object(operator.os,'getuid',return_value=1000),patch.object(operator.os,'geteuid',return_value=1000),patch.object(operator.socket,'gethostname',return_value=operator.LOCAL),patch.object(operator.os,'isatty',return_value=True),patch('builtins.input',return_value=''),patch.object(operator.subprocess,'run',side_effect=[Mock(returncode=0),Mock(returncode=75)])as run,patch('sys.stdout',new_callable=io.StringIO):
   self.assertEqual(operator.main(['--preflight']),75);self.assertEqual(run.call_count,2);self.assertEqual(run.call_args.args[0][:3],['/usr/bin/sudo','-k','--'])
 def test_backend_transport_fixed_role_contract(self):
  transport=self.m['transport']
  with patch.object(transport,'root'):a=transport.CloudTransport('a'*64,'b'*64)
  with patch.object(transport.subprocess,'run',return_value=Mock(returncode=0,stdout=b'{}'))as run:
   a.call('inspect','r16-app.service','b'*64,{'phase':'SOURCE'});raw=self.c.parse(run.call_args.kwargs['input']);self.assertEqual(raw['payload'],{'unit':'r16-app.service','phase':'SOURCE'})
   self.assertRaisesRegex(Exception,'RPC_BACKEND_PLAN_DRIFT',a.call,'inspect','r16-app.service','f'*64,{})
 def test_rpc_all_effects_refuse_without_loading_adapter_or_writing_record(self):
  with patch.object(self.r,'root'),patch.object(self.r.resource,'setrlimit'),patch.object(self.r.os,'umask'),patch.object(self.r,'verify_capsule',return_value={'mode':'READONLY_PREFLIGHT_SOURCE'}),patch.object(self.r,'load_adapter',side_effect=AssertionError('effect adapter must not load')),patch.object(self.r,'immutable',side_effect=AssertionError('must not write')):
   for op,payload in [('stop',{'unit':'r16-app.service'}),('fence',{'unit':'r16-app.service'}),('stage',{}),('commit',{'publication':{},'rollback':False}),('admission',{})]:
    self.assertRaisesRegex(Exception,'READONLY_SOURCE_RPC_EFFECTS_DISABLED',self.r.main,[op,'b'*64],self.packet(op,payload))
 def test_rpc_readonly_preflight_needs_no_fake_native_admission_or_plan_state(self):
  result={'schema':'r16.source19-native-transition.cloud-preparation.v1','host':self.c.CLOUD,'authority':False};adapter=Mock();adapter.cloud_preflight.return_value=result
  with patch.object(self.r,'root'),patch.object(self.r.resource,'setrlimit'),patch.object(self.r.os,'umask'),patch.object(self.r,'verify_capsule',return_value={'mode':'READONLY_PREFLIGHT_SOURCE'}),patch.object(self.r,'load_adapter',return_value=adapter),patch.object(self.r,'read',side_effect=AssertionError('no plan/admission state')),patch.object(self.r,'lock',side_effect=AssertionError('no lock')),patch.object(self.r,'immutable',side_effect=AssertionError('no record')):
   self.assertEqual(self.r.main(['preflight','0'*64],self.packet().replace(b'"'+b'b'*64+b'"',b'"'+b'0'*64+b'"')),result)

 def test_full_expected_text_followed_by_eof_is_cancelled(self):
  pending={};actor={'p':1};words=b'MAINTAIN SOURCE19 '+self.c.digest({'nativeHostAdmin':actor}).encode();reads=iter([*(bytes([b])for b in words),b''])
  with patch.object(self.f,'identity',return_value=actor),patch.object(self.f.os,'open',return_value=91),patch.object(self.f.os,'close'),patch.object(self.f.os,'isatty',return_value=True),patch.object(self.f.os,'tcgetpgrp',return_value=1),patch.object(self.f.os,'getpgrp',return_value=1),patch.object(self.f.os,'write',side_effect=lambda fd,b:len(b)),patch.object(self.f.os,'read',side_effect=lambda *a:next(reads)):
   self.assertRaisesRegex(Exception,'NATIVE_CONFIRMATION_EOF_CANCELLED',self.f.native_confirm,pending,self.c.LOCAL)
 def test_cold_bootstrap_preloads_real_backend_aliases_in_mock_root_process(self):
  # A new ordinary subprocess starts with no cached aliases/modules. Only root
  # identity and protected-file metadata/reads are virtual; all Python source
  # bytes and the bootstrap/import/backend chain are the real reviewed files.
  import subprocess
  script=r"""
import hashlib,importlib.util,json,sys,stat
from pathlib import Path
from unittest.mock import patch
entry=Path(sys.argv[1]);project=entry.parents[2];prefix='maintenance/source19-native-transition-r1/'
files={}
for p in (entry.parent).glob('*.py'):
 if not p.name.startswith('test_')and p.name not in('build.py','verify.py'):files[prefix+p.name]=p.read_bytes()
for p in entry.glob('*.py'):
 if not p.name.startswith('test_')and p.name not in('operator.py','bootstrap.py'):files[prefix+'entry/'+p.name]=p.read_bytes()
files['maintenance/first-stop-r8/linux_backend.py']=(entry.parents[1]/'first-stop-r8/linux_backend.py').read_bytes()
manifest={'schema':'r16.source19-native-transition.entry-freeze.v1','mode':'READONLY_PREFLIGHT_SOURCE','files':{n:{'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b),'mode':420}for n,b in files.items()},'packageFiles':{},'planTemplate':{},'revisionRequest':{}}
raw=json.dumps(manifest,separators=(',',':')).encode();cap=hashlib.sha256(raw).hexdigest()
spec=importlib.util.spec_from_file_location('isolated_boot',entry/'bootstrap.py');b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)
root=Path('/virtual/root');pin=Path('/virtual/pin');b.ROOT=root;b.PIN=pin
read=lambda p,*a:json.dumps({'schema':'r16.source19-native-transition.installed-entry.v1','capsuleHash':cap}).encode()if p==pin else raw if p==root/'ENTRY_FREEZE.json'else files[p.relative_to(root/'runtime').as_posix()]
assert '_source19_stop_contract'not in sys.modules and '_source19_protected_files'not in sys.modules
with patch.object(b,'read',side_effect=read),patch.object(b.os,'getuid',return_value=0),patch.object(b.os,'geteuid',return_value=0),patch.object(b.os,'umask'),patch.object(b.resource,'setrlimit'):
 # Rows require 0644, the two fixed external freeze records require 0600.
 with patch.object(Path,'lstat',side_effect=lambda p:type('Meta',(),{'st_mode':stat.S_IFREG|(0o600 if p in(pin,root/'ENTRY_FREEZE.json')else 0o644)})(),autospec=True):
  loader,_=b.sealed();assert '_source19_stop_contract'in sys.modules and '_source19_protected_files'in sys.modules
  import foreground,orchestration,linux_backend
  assert linux_backend.S is sys.modules['_source19_stop_contract']
  assert linux_backend.R8 is sys.modules['_source19_protected_files']
print('COLD_SEALED_BACKEND_IMPORT_PASS')
"""
  result=subprocess.run([sys.executable,'-I','-B','-c',script,str(HERE)],stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=15,check=False)
  self.assertEqual(result.returncode,0,result.stderr.decode()[-2000:]);self.assertEqual(result.stdout.strip(),b'COLD_SEALED_BACKEND_IMPORT_PASS')
if __name__=='__main__':unittest.main()
