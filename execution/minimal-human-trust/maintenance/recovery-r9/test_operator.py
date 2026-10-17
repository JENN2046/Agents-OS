"""Offline new-R9 wrapper/loader protocol. No root/SSH/production files."""
import hashlib,importlib.util,io,json,sys,types,unittest
from pathlib import Path
from unittest.mock import patch
HERE=Path(__file__).parent
def load(name,file):
 s=importlib.util.spec_from_file_location(name,HERE/file);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
o=load('r9_operator_test','operator.py');r=load('r9_loader_test','root-loader.py')
class Tests(unittest.TestCase):
 def setup_wrapper(self,returncodes=(0,0),answer=''):
  streams=[io.StringIO(),io.StringIO(),io.StringIO()]
  for s in streams:s.isatty=lambda:True
  contexts=[patch.object(o.os,'getuid',return_value=1000),patch.object(o.os,'geteuid',return_value=1000),patch.object(o.socket,'gethostname',return_value=o.LOCAL),patch.object(o.sys,'stdin',streams[0]),patch.object(o.sys,'stdout',streams[1]),patch.object(o.sys,'stderr',streams[2]),patch.object(o,'verify_local',return_value={'status':'TEST_ONLY'}),patch.object(o,'loader',side_effect=lambda phase:'PINNED '+phase),patch('builtins.input',return_value=answer),patch.object(o.subprocess,'run',side_effect=[types.SimpleNamespace(returncode=c) for c in returncodes])]
  return streams,contexts
 def test_cancel_enter_precedes_any_authentication_or_ssh(self):
  _,p=self.setup_wrapper(answer='cancel')
  with p[0],p[1],p[2],p[3],p[4],p[5],p[6],p[7],p[8],p[9] as run:
   with self.assertRaisesRegex(ValueError,'HUMAN_START_CANCELLED'):o.main(['--install'])
   run.assert_not_called()
 def test_cloud_refusal_blocks_local(self):
  _,p=self.setup_wrapper((78,))
  with p[0],p[1],p[2],p[3],p[4],p[5],p[6],p[7],p[8],p[9] as run:self.assertEqual(o.main([]),78)
  self.assertEqual(run.call_count,1)
 def test_real_tty_inheritance_precise_cloud_then_local_and_return75(self):
  streams,p=self.setup_wrapper((0,75))
  with p[0],p[1],p[2],p[3],p[4],p[5],p[6],p[7],p[8],p[9] as run:self.assertEqual(o.main([]),75)
  first,second=run.call_args_list;self.assertIn('-tt',first.args[0]);self.assertIn('/usr/bin/sudo -k',first.args[0][-1]);self.assertEqual(second.args[0][0],'/usr/bin/pkexec')
  for call in (first,second):
   for key in ('stdin','stdout','stderr','capture_output','input'):self.assertNotIn(key,call.kwargs)
  self.assertIn('不接旧92/93',streams[1].getvalue());self.assertIn('STOPPED',streams[1].getvalue());self.assertIn('APT',streams[1].getvalue());self.assertIn('优雅停止仍运行的 Native、Bridge、Owner',streams[1].getvalue());self.assertIn('SOURCE STOPPED',streams[1].getvalue())
 def test_describe_noninteractive_no_commands_unsealed_verify_refuses(self):
  with patch.object(o.sys,'stdout',io.StringIO()),patch.object(o.subprocess,'run') as run:
   self.assertEqual(o.main(['--describe']),0)
   with self.assertRaisesRegex(ValueError,'FINAL_REVIEWED_SEAL'):o.main(['--verify'])
   run.assert_not_called()
 def test_old_continue_and_apply_modes_unavailable(self):
  for mode in ('--continue','--receipt','APPLY','bootstrap-local','--local-only'):
   with self.assertRaisesRegex(ValueError,'FIXED_OPERATOR'):o.main([mode])
 def test_non_tty_install_never_authenticates(self):
  with patch.object(o.os,'getuid',return_value=1000),patch.object(o.os,'geteuid',return_value=1000),patch.object(o.socket,'gethostname',return_value=o.LOCAL),patch.object(o.sys,'stdin',io.StringIO()),patch.object(o.sys,'stdout',io.StringIO()),patch.object(o.subprocess,'run') as run:
   with self.assertRaisesRegex(ValueError,'REAL_FOREGROUND'):o.main([])
   run.assert_not_called()
 def test_actual_loader_bytes_tamper_rejects_before_exec(self):
  source=(HERE/'root-loader.py').read_text()
  with patch.object(o,'CAPSULE','a'*64),patch.object(o,'ENTRY_SHA','b'*64),patch.object(o,'ROOT_LOADER',source),patch.object(o,'LOADER_SHA',hashlib.sha256(source.encode()).hexdigest()):
   self.assertIn("MODE='preflight'",o.loader('cloud','preflight'))
   with patch.object(o,'ROOT_LOADER',source+'\n# drift'):
    with self.assertRaisesRegex(ValueError,'FINAL_REVIEWED_SEAL'):o.loader('cloud')
 def test_full_native_line_wait_and_identity_rechecked_before_mint(self):
  for host,stage in ((r.CLOUD,'CLOUD'),(r.LOCAL,'LOCAL')):
   pending={'host':host,'nonce':'d'*32};line=bytearray(('APPLY '+stage+' '+r.digest(pending)+'\n').encode());events=[];written=[]
   guard=types.SimpleNamespace(native_identity=lambda h:(events.append('identity') or 9))
   def read(fd,n):events.append('read');return bytes([line.pop(0)])
   def clock():events.append('accepted');return 9000
   def write(fd,raw):written.append(raw);return len(raw)
   with patch.object(r.os,'write',side_effect=write),patch.object(r.os,'read',side_effect=read),patch.object(r.os,'close'):
    a=r.native_confirm(guard,pending,clock)
   self.assertEqual(events[-2:],['identity','accepted']);self.assertEqual(a['issuedAt'],9000);self.assertEqual(a['expiresAt'],309000);self.assertEqual(events.count('accepted'),1)
   if host==r.LOCAL:
    text=b''.join(written).decode();self.assertIn('优雅停止仍运行的 Native、Bridge、Owner',text);self.assertIn('按 Owner、Bridge、Native、目标App 顺序启动应运行角色',text);self.assertIn('SOURCE App=STOPPED',text)
 def loader_contexts(self,mode='apply'):
  prior={'schema':'r16.r9.source-recovery-readback.v1','host':r.CLOUD,'factsHash':'f'*64,'sourceRecoveryEvidence':{'oldPlanRenewed':False},'sourceAppExpectedState':'STOPPED','businessAcceptance':False};manifest={'planTemplate':{'sourceRecoveryEvidence':prior['sourceRecoveryEvidence'],'targetAppVersion':'a'*64,'targetNativeVersion':'b'*64}}
  sources={'prior-verifier.py':b'verifier','cache-cleanup.py':b'cache','prior-native-guard.py':b'guard','os_entry.py':b"assert NATIVE_ACCEPTED_AT==1000\nassert NATIVE_CONFIRMATION['issuedAt']==1000\nassert NATIVE_PENDING['capsuleHash']=='a'*64\n"};allocation={'rootAllocatedBytes':10,'targetAllocatedBytes':20};inventory={'inventoryHash':'c'*64,'files':{'fake':{}},'logicalBytes':50,'allocatedBytes':4096,'rebuildMethod':'apt-get update'}
  verifier=types.SimpleNamespace(verify_prior=lambda manifest,sources:prior)
  cache=types.SimpleNamespace(prepare=lambda:inventory,space_budget=lambda *a,**kw:{'test':'budget'},assert_fresh=lambda cap:None,execute=lambda *a,**kw:None)
  def memory(name,raw):return {'r9_prior_verifier':verifier,'r9_cache_cleanup':cache,'native_guard':object()}[name]
  def confirmation(guard,pending):return {'pendingHash':r.digest(pending),'issuedAt':1000,'expiresAt':301000}
  contexts=[patch.object(r,'PHASE','cloud',create=True),patch.object(r,'MODE',mode,create=True),patch.object(r,'CAPSULE','a'*64,create=True),patch.object(r,'ENTRY_SHA','b'*64,create=True),patch.object(r.os,'getuid',return_value=0),patch.object(r.os,'geteuid',return_value=0),patch.object(r.socket,'gethostname',return_value=r.CLOUD),patch.object(r,'seal_candidate',return_value=(manifest,sources,allocation)),patch.object(r,'memory_module',side_effect=memory),patch.object(r,'native_confirm',side_effect=confirmation),patch.object(r,'check_window'),patch.object(r.resource,'setrlimit'),patch.object(r.os,'umask'),patch.object(r.sys,'argv',[]),patch.object(r,'assert_fresh_namespace'),patch.object(r.sys,'stdout',io.StringIO())]
  return contexts,cache,verifier
 def run_loader(self,p):
  import contextlib
  with contextlib.ExitStack() as stack:
   for item in p:stack.enter_context(item)
   return r.main()
 def test_preflight_no_confirmation_cleanup_or_entry(self):
  p,cache,verifier=self.loader_contexts('preflight');cache.execute=unittest.mock.Mock()
  p[9]=patch.object(r,'native_confirm',side_effect=AssertionError('Preflight must never confirm'));result=self.run_loader(p);self.assertEqual(result['status'],'R9_READONLY_PREFLIGHT_PASS');cache.execute.assert_not_called()
 def test_apply_injects_actual_accepted_time_and_rechecks_seal_and_facts(self):
  p,cache,verifier=self.loader_contexts();cache.execute=unittest.mock.Mock();self.run_loader(p);self.assertEqual(cache.execute.call_count,1)
 def test_fresh_namespace_checks_pending_symlink_and_never_mutates(self):
  for suffix in ('recovery-r9','recovery-r9.pending','.recovery-r9.pending','recovery-r9.next'):
   with patch.object(r.os.path,'lexists',side_effect=lambda p:str(p).endswith('/'+suffix)),patch.object(r.subprocess,'run') as run:
    with self.assertRaisesRegex(r.Refused,'EXISTING_NAMESPACE'):r.assert_fresh_namespace('a'*64)
    run.assert_not_called()
 def test_actual_new94_fence_pending_rejects_before_any_manager_or_effect(self):
  for role in ('r16-app.service','r16-bridge.service','r16-owner.service','r16-native.service'):
   for suffix in ('94-r16-maintenance-recovery-r9.conf','94-r16-maintenance-recovery-r9.conf.pending','.94-r16-maintenance-recovery-r9.conf.pending','94-r16-maintenance-recovery-r9.conf.next'):
    exact='/run/systemd/system/'+role+'.d/'+suffix
    with patch.object(r.os.path,'lexists',side_effect=lambda p:str(p)==exact),patch.object(r.subprocess,'run') as run:
     with self.assertRaisesRegex(r.Refused,'EXISTING_NAMESPACE'):r.assert_fresh_namespace('a'*64)
     run.assert_not_called()
 def test_foreign_new_unit_override_directory_prevents_any_command(self):
  for root in ('/run/systemd/system','/etc/systemd/system'):
   exact=root+'/r16-native-recovery-maintenance-r9.service.d'
   with patch.object(r.os.path,'lexists',side_effect=lambda p:str(p)==exact),patch.object(r.subprocess,'run') as run:
    with self.assertRaisesRegex(r.Refused,'EXISTING_NAMESPACE'):r.assert_fresh_namespace('a'*64)
    run.assert_not_called()
 def test_unit_manager_existing_unit_fails_closed(self):
  good=b'LoadState=not-found\nActiveState=inactive\nMainPID=0\nControlPID=0\nJob=0\n'
  for raw,accepted in ((good,True),(good.replace(b'not-found',b'loaded'),False),(good.replace(b'MainPID=0',b'MainPID=42'),False),(b'',False)):
   with patch.object(r.os.path,'lexists',return_value=False),patch.object(r.subprocess,'run',return_value=types.SimpleNamespace(returncode=0,stdout=raw)) as run:
    if accepted:r.assert_fresh_namespace('a'*64)
    else:
     with self.assertRaises(r.Refused):r.assert_fresh_namespace('a'*64)
    self.assertEqual(run.call_args.args[0][:3],('/usr/bin/systemctl','show','r16-native-recovery-maintenance-r9.service'))
 def test_namespace_refusal_precedes_any_prior_read_or_cleanup_prepare(self):
  p,cache,verifier=self.loader_contexts('preflight');p[-2]=patch.object(r,'assert_fresh_namespace',side_effect=r.Refused('R9_EXISTING_NAMESPACE_REQUIRES_READONLY_REVIEW'));verifier.verify_prior=unittest.mock.Mock();cache.prepare=unittest.mock.Mock()
  with self.assertRaisesRegex(r.Refused,'EXISTING_NAMESPACE'):self.run_loader(p)
  verifier.verify_prior.assert_not_called();cache.prepare.assert_not_called()
 def test_missing_actual_reclaimed_blocks_after_delete_blocks_bootstrap(self):
  p,cache,verifier=self.loader_contexts();cache.execute=unittest.mock.Mock()
  def budget(*a,**kw):
   if kw.get('credit_cleanup') is False:raise r.Refused('ACTUAL_RECLAIM_INSUFFICIENT')
   return {'projected':'only'}
  cache.space_budget=budget
  with self.assertRaisesRegex(r.Refused,'ACTUAL_RECLAIM_INSUFFICIENT'):self.run_loader(p)
  self.assertEqual(cache.execute.call_count,1)
 def test_native_expiry_after_revalidation_blocks_cache_effect(self):
  p,cache,verifier=self.loader_contexts();p[10]=patch.object(r,'check_window',side_effect=[None,r.Refused('R9_NATIVE_APPLY_EXPIRED')]);cache.execute=unittest.mock.Mock()
  with self.assertRaisesRegex(r.Refused,'NATIVE_APPLY_EXPIRED'):self.run_loader(p)
  cache.execute.assert_not_called()
 def test_fact_drift_after_human_confirmation_blocks_cleanup_and_bootstrap(self):
  p,cache,verifier=self.loader_contexts();original=verifier.verify_prior;verifier.verify_prior=unittest.mock.Mock(side_effect=[original(None,None),{**original(None,None),'factsHash':'changed'}]);cache.execute=unittest.mock.Mock()
  with self.assertRaisesRegex(r.Refused,'REAL_FACTS_CHANGED'):self.run_loader(p)
  cache.execute.assert_not_called()
if __name__=='__main__':unittest.main()
