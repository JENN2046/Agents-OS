"""R12 operator boundary and honest metadata-only disk budget; no real root/SSH."""
import hashlib,importlib.util,json,subprocess,sys,types,unittest
from pathlib import Path
from unittest.mock import patch
HERE=Path(__file__).resolve().parent
def load(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);sys.modules[name]=m;s.loader.exec_module(m);return m
r=load('r12_root_operator_test',HERE/'root-loader.py');o=load('r12_outer_operator_test',HERE/'operator.py')
class OperatorTests(unittest.TestCase):
 def budget(self,available,free=None,device=1):
  allocation={'rootAllocatedBytes':53*1024*1024,'targetAllocatedBytes':0,'packageCopyAllocatedBytes':0}
  v=types.SimpleNamespace(f_bavail=available//4096,f_bfree=(available if free is None else free)//4096,f_frsize=4096)
  with patch.object(r.os,'statvfs',return_value=v),patch.object(r.os,'stat',return_value=types.SimpleNamespace(st_dev=device)):return r.space_budget(allocation)
 def test_only_metadata_context_growth_counted_and_reserve_retained(self):
  b=self.budget(356*1024*1024);self.assertEqual(b['packageCopyBytes'],0);self.assertEqual(b['targetGrowthBytes'],0);self.assertEqual(b['projectedRemainingBytes'],303*1024*1024);self.assertFalse(b['usesRootReservedBlocks'])
 def test_root_reserved_free_blocks_never_admit_install(self):
  with self.assertRaisesRegex(r.Refused,'R12_INSUFFICIENT_UNRESERVED_SPACE'):self.budget(280*1024*1024,free=3*1024**3)
 def test_budget_exact_reserve_boundary(self):
  self.assertEqual(self.budget(309*1024*1024)['projectedRemainingBytes'],256*1024*1024)
  with self.assertRaisesRegex(r.Refused,'R12_INSUFFICIENT_UNRESERVED_SPACE'):self.budget(309*1024*1024-4096)
 def test_new_package_or_target_allocation_is_rejected(self):
  with patch.object(r.os,'statvfs',return_value=types.SimpleNamespace(f_bavail=1000000,f_frsize=4096)),patch.object(r.os,'stat',return_value=types.SimpleNamespace(st_dev=1)):
   for bad in ('targetAllocatedBytes','packageCopyAllocatedBytes'):
    a={'rootAllocatedBytes':1000,'targetAllocatedBytes':0,'packageCopyAllocatedBytes':0};a[bad]=1
    with self.assertRaisesRegex(r.Refused,'R12_UNEXPECTED_PACKAGE_OR_TARGET_COPY'):r.space_budget(a)
 def test_reused_assets_require_same_filesystem_for_truthful_budget(self):
  with patch.object(r.os,'statvfs',return_value=types.SimpleNamespace(f_bavail=1000000,f_frsize=4096)),patch.object(r.os,'stat',side_effect=[types.SimpleNamespace(st_dev=n) for n in (1,1,2)]):
   with self.assertRaisesRegex(r.Refused,'R12_REUSED_ASSETS_FILESYSTEM_DRIFT'):r.space_budget({'rootAllocatedBytes':1,'targetAllocatedBytes':0,'packageCopyAllocatedBytes':0})
 def test_describe_cannot_run_any_external_program(self):
  with patch.object(o.subprocess,'run',side_effect=AssertionError('describe executed external process')),patch('builtins.print'):
   self.assertEqual(o.main(['--describe']),0)
  d=o.description();self.assertEqual(d['newNamespace'],'recovery-r12');self.assertFalse(d['cacheCleanup']);self.assertFalse(d['packageOrTargetCopy']);self.assertFalse(d['oldPlanRenewed'])
  self.assertEqual((d['sourceDeliveryRevision'],d['forwardRevision'],d['rollbackRevision']),(18,19,20))
 def test_native_seal_rejects_old_or_unbound_revision_chain_before_inspection(self):
  plan={'targetReleaseId':r.TARGET,'activationScope':'START_REVIEWED_TARGET_APP_IF_SOURCE_ALREADY_STOPPED','sourceRecoveryEvidence':{},**r.REVISION_SCOPE}
  files={name:'a'*64 for name in r.REQUIRED}
  while len(files)<19:files['test-'+str(len(files))]='a'*64
  for change in ({'sourceDeliveryRevision':16},{'forwardRevision':17},{'rollbackRevision':18},{'sourceDeliveryHash':'b'*64},{'forwardRevision':None}):
   f={'schema':'r16.native-recovery-source-freeze.v3','files':files,'payloadFiles':{str(i):'c'*64 for i in range(12600)},'planTemplate':{**plan,**change}}
   raw=r.canonical(f);cap=hashlib.sha256(raw).hexdigest()
   with self.subTest(change=change),patch.object(r,'read_public',return_value=(raw,0o644)),patch.object(r.os,'statvfs',side_effect=AssertionError('inspection before chain rejection')):
    with self.assertRaisesRegex(r.Refused,'R12_REVISION_CHAIN_REFUSED'):r.seal_candidate(Path('/unopened-fixture'),cap,'a'*64)
 def test_unsealed_template_refuses_before_any_native_action(self):
  with patch.object(o.subprocess,'run',side_effect=AssertionError('unsealed template executed native')):
   with self.assertRaisesRegex(ValueError,'R12_FINAL_REVIEWED_SEAL_REQUIRED'):o.verify_local()
 def test_human_cancel_starts_neither_ssh_nor_local_auth(self):
  with patch.object(o.os,'getuid',return_value=1000),patch.object(o.os,'geteuid',return_value=1000),patch.object(o.socket,'gethostname',return_value=o.LOCAL),patch.object(o.sys.stdin,'isatty',return_value=True),patch.object(o.sys.stdout,'isatty',return_value=True),patch.object(o.sys.stderr,'isatty',return_value=True),patch.object(o,'verify_local',return_value={'status':'isolated'}),patch.object(o.subprocess,'run',side_effect=AssertionError('cancel executed native')),patch('builtins.input',return_value='cancel'),patch('builtins.print'):
   with self.assertRaisesRegex(ValueError,'R12_HUMAN_START_CANCELLED'):o.main([])
 def test_cloud_failure_prevents_local_phase(self):
  with patch.object(o.os,'getuid',return_value=1000),patch.object(o.os,'geteuid',return_value=1000),patch.object(o.socket,'gethostname',return_value=o.LOCAL),patch.object(o.sys.stdin,'isatty',return_value=True),patch.object(o.sys.stdout,'isatty',return_value=True),patch.object(o.sys.stderr,'isatty',return_value=True),patch.object(o,'verify_local',return_value={'status':'isolated'}),patch.object(o,'loader',return_value='isolated code'),patch.object(o.subprocess,'run',return_value=types.SimpleNamespace(returncode=78)) as call,patch('builtins.input',return_value=''),patch('builtins.print'):
   self.assertEqual(o.main([]),78);self.assertEqual(call.call_count,1);self.assertIn('-tt',call.call_args.args[0]);self.assertIn('sudo',call.call_args.args[0][-1])
 def test_window_expiry_refuses_and_pending_tamper_cannot_reauthorize(self):
  pending={'schema':'r16.r12.native-install-pending.v1','assetReuse':{'fixed':'reviewed'},'nonce':'fixed'};authority={'pendingHash':r.digest(pending),'issuedAt':1000,'expiresAt':301000}
  r.check_window(authority,pending,clock=lambda:300999)
  with self.assertRaisesRegex(r.Refused,'R12_NATIVE_APPLY_EXPIRED'):r.check_window(authority,pending,clock=lambda:301000)
  pending['assetReuse']['fixed']='substituted'
  with self.assertRaisesRegex(r.Refused,'R12_NATIVE_APPLY_EXPIRED'):r.check_window(authority,pending,clock=lambda:1001)
if __name__=='__main__':unittest.main()
