"""Portable transformation/real bootstrap-window tests. No production paths."""
import base64,hashlib,importlib.util,json,subprocess,sys,tempfile,types,unittest
from pathlib import Path
from unittest.mock import patch
HERE=Path(__file__).resolve().parent
def load(name,path):
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m
b=load('r9_builder_tested',HERE/'build.py');p=load('r9_prior_tested',HERE/'prior-verifier.py')
class BuildTests(unittest.TestCase):
 def entry(self):
  raw=b.transform('os_entry.py',b.reviewed_override_path('os_entry.py').read_bytes());m=types.ModuleType('r9_generated_entry_tested');m.__file__='<isolated-r9-entry>';exec(compile(raw,m.__file__,'exec'),m.__dict__);return m
 def test_new_namespace_keeps_original_release_and_no_old_adoption(self):
  q=b.transform('quiescence.py',(HERE.parent/'release-r6/quiescence.py').read_bytes()).decode()
  self.assertIn("REMOTE_HELPER = '/usr/libexec/r16-maintenance-os-r9'",q);self.assertIn("DROPIN_NAME = '94-r16-maintenance-recovery-r9.conf'",q)
  self.assertIn("TARGET_RELEASE = '/opt/r16/releases/r16-daily-20261015-r15-app-recovery-r6'",q)
  self.assertNotIn('/r16-maintenance/recovery-r8',q);self.assertNotIn('adopt-first-stop',q)
 def test_arbitrary_nonruntime_payload_is_byte_preserved(self):
  raw=b'\x00frozen package bytes\xff';self.assertEqual(b.transform('metadata.bin',raw),raw)
 def test_reviewed_source_overrides_exact_hashes(self):
  for name,pin in b.OVERRIDE_PINS.items():self.assertEqual(hashlib.sha256(b.reviewed_override_path(name).read_bytes()).hexdigest(),pin)
 def test_r9_historical_entry_matches_exact_git_1697_pin(self):
  self.assertEqual(b.reviewed_override_path('os_entry.py'),HERE/'fixtures/os-entry-at-1697b82.txt')
  self.assertEqual(hashlib.sha256(b.reviewed_override_path('os_entry.py').read_bytes()).hexdigest(),'d6e8f1262910adf60688770bc7794a14aeb56c8075e75020e74f400fe098d41b')
  self.assertEqual(b.reviewed_override_path('quiescence.py'),HERE.parent/'release-r6/quiescence.py')
 def test_r9_real_build_and_entry_tests_do_not_read_mutable_future_entry(self):
  # Exercise the production build override selection as well as generated AST.
  # Abort before output: all frozen material is an inert read-only dictionary.
  mutable=HERE.parent/'release-r6/os_entry.py';old_read_bytes=Path.read_bytes
  def guarded(path):
   if path==mutable:raise AssertionError('MUTABLE_FUTURE_ENTRY_READ')
   return old_read_bytes(path)
  with patch.object(Path,'read_bytes',guarded):
   e=self.entry();self.assertEqual(str(e.ROOT),'/usr/lib/r16-maintenance/recovery-r9')
  frozen={'files':{},'payloadFiles':{}};seen=[];original_read=b.read
  class AfterOverrides(BaseException):pass
  def read(path,*args,**kw):
   path=Path(path);seen.append(path)
   if path==b.FROZEN/'SOURCE_FREEZE.json':return b.canon(frozen),0o644
   if path==mutable:raise AssertionError('MUTABLE_FUTURE_ENTRY_READ')
   return original_read(path,*args,**kw)
  frozen['files']={'isolated.mjs':'a'*64};frozen['payloadFiles']={str(i):'b'*64 for i in range(12600)}
  # Preserve all production cardinality guards: fake 14 source rows resolve
  # only in the read adapter and matching test hashes, never on production IO.
  raw=b'isolated source';frozen['files']={str(i)+'.mjs':b.sha(raw) for i in range(14)}
  def source_read(path,*args,**kw):
   path=Path(path)
   if path.parent==b.FROZEN and path.name.endswith('.mjs'):seen.append(path);return raw,0o644
   return read(path,*args,**kw)
  with tempfile.TemporaryDirectory() as tmp,patch.object(b,'FROZEN_SHA',b.sha(b.canon(frozen))),patch.object(b,'read',side_effect=source_read),patch.object(b,'transform',side_effect=AfterOverrides):
   with self.assertRaises(AfterOverrides):b.build(Path(tmp)/'never-emitted')
   self.assertFalse((Path(tmp)/'never-emitted').exists())
  self.assertIn(b.reviewed_override_path('os_entry.py'),seen);self.assertNotIn(mutable,seen)
 def test_missing_or_expired_native_window_cannot_even_verify_or_copy(self):
  for accepted,now in ((None,1000),(1000,300999+1),(1001,1000)):
   e=self.entry()
   if accepted is not None:e.NATIVE_ACCEPTED_AT=accepted
   with patch.object(e,'root'),patch.object(e,'now_ms',return_value=now),patch.object(e,'verify_capsule',side_effect=AssertionError('expired window reached capsule')),patch.object(e,'install_capsule',side_effect=AssertionError('expired window wrote root')):
    with self.assertRaisesRegex(e.Refused,'NEW_NATIVE_BOOTSTRAP_WINDOW_REQUIRED'):e.bootstrap_locked('bootstrap-cloud','a'*64)
 def test_cloud_admission_begins_at_native_acceptance_not_copy_clock(self):
  e=self.entry();accepted=1000000;e.NATIVE_ACCEPTED_AT=accepted
  manifest={'files':{'os_entry.py':'b'*64},'planTemplate':{'sourceRecoveryEvidence':p.PROVENANCE}};sources={'prior-verifier.py':b'def verify_prior(manifest,sources): return {"readonly":True}\n'}
  e.NATIVE_PENDING={'schema':'r16.r9.native-install-pending.v1','host':e.CLOUD,'capsuleHash':'a'*64,'entrySha256':'b'*64,'sourceRecoveryEvidence':p.PROVENANCE,'sourceAppBaseline':'STOPPED','oldPlanRenewed':False,'nonce':'c'*32}
  e.NATIVE_CONFIRMATION={'schema':'r16.r9.native-install-confirmation.v1','issuedAt':accepted,'expiresAt':accepted+300000,'pendingHash':e.digest(e.NATIVE_PENDING),'nonce':'c'*32}
  record={'state':'COPIED','capsuleHash':'a'*64,'createdAt':accepted+60000,'nativeAcceptedAt':accepted}
  with tempfile.TemporaryDirectory() as tmp,patch.object(e,'root'),patch.object(e,'now_ms',return_value=accepted+120000),patch.object(e,'STATE',Path(tmp)),patch.object(e,'verify_capsule',return_value=(manifest,sources,b'{}')),patch.object(e,'install_capsule',return_value=record),patch.object(e,'ensure_file'),patch.object(e,'command'),patch.object(e,'checkpoint_bootstrap'):
   result=e.bootstrap_locked('bootstrap-cloud','a'*64)
  self.assertEqual(result['expiresAt'],accepted+1800000)
 def test_fresh_human_confirmation_cannot_renew_existing_bootstrap(self):
  e=self.entry();e.NATIVE_ACCEPTED_AT=2000000
  with tempfile.TemporaryDirectory() as tmp:
   e.STATE=Path(tmp)/'state';e.ROOT=Path(tmp)/'root';e.STATE.mkdir();e.ROOT.mkdir();(e.STATE/'bootstrap.json').write_text('{}')
   record={'state':'COPIED','capsuleHash':'a'*64,'createdAt':1000000,'nativeAcceptedAt':1000000}
   with patch.object(e,'recover_json',return_value=record),patch.object(e,'mkdir'),patch.object(e,'now_ms',return_value=2000000),patch.object(e,'ensure_file',side_effect=AssertionError('old transaction renewed')):
    with self.assertRaisesRegex(e.Refused,'NEW_NATIVE_BOOTSTRAP_WINDOW_EXPIRED'):e.install_capsule({'payloadFiles':{}},{},'a'*64,b'{}')
 def test_expiry_during_real_temp_copy_stops_next_file_and_root_helper(self):
  e=self.entry();clock=[1000000];e.NATIVE_ACCEPTED_AT=clock[0];e.NATIVE_PENDING={'scope':'isolated'};e.NATIVE_CONFIRMATION={'scope':'isolated'}
  with tempfile.TemporaryDirectory() as tmp:
   base=Path(tmp);e.STATE=base/'state';e.ROOT=base/'root';e.SOURCE=base/'source';e.SOURCE.mkdir();e.HELPER=base/'helper';e.UNIT_FILE=base/'unit'
   real_ensure=e.ensure_file
   def slow_ensure(path,*args,**kw):
    result=real_ensure(path,*args,**kw)
    if Path(path)==e.ROOT/'a.mjs':clock[0]=1300000
    return result
   with patch.object(e,'now_ms',side_effect=lambda:clock[0]),patch.object(e.socket,'gethostname',return_value=e.LOCAL),patch.object(e,'mkdir',side_effect=lambda path:Path(path).mkdir(parents=True,exist_ok=True,mode=0o700)),patch.object(e,'secure_read',side_effect=lambda path,**kw:Path(path).read_bytes()),patch.object(e,'ensure_file',side_effect=slow_ensure):
    with self.assertRaisesRegex(e.Refused,'NEW_NATIVE_BOOTSTRAP_WINDOW_EXPIRED'):e.install_capsule({'payloadFiles':{}},{'a.mjs':b'first admitted file','b.mjs':b'must not be copied'},'a'*64,b'{}')
   self.assertTrue((e.ROOT/'a.mjs').exists());self.assertFalse((e.ROOT/'b.mjs').exists());self.assertFalse(e.HELPER.exists());self.assertFalse(e.UNIT_FILE.exists())
 def test_last_command_and_write_guard_refuse_expired_native_window(self):
  e=self.entry();e.NATIVE_ACCEPTED_AT=1000000
  with patch.object(e,'now_ms',return_value=1300000),patch.object(e,'root'),patch.object(e.subprocess,'run',side_effect=AssertionError('expired service command reached kernel')):
   with self.assertRaisesRegex(e.Refused,'NEW_NATIVE_BOOTSTRAP_WINDOW_EXPIRED'):e.command(('/usr/bin/systemctl','start','not-a-real-unit'))
   with tempfile.TemporaryDirectory() as tmp:
    with self.assertRaisesRegex(e.Refused,'NEW_NATIVE_BOOTSTRAP_WINDOW_EXPIRED'):e.ensure_file(Path(tmp)/'never',b'never')
    self.assertFalse((Path(tmp)/'never').exists())
 def test_context_work_crossing_expiry_cannot_write_context_or_freeze(self):
  source=b.transform('context.mjs',(HERE.parent/'release-r6/context.mjs').read_bytes()).decode()
  # Execute the actual generated prepareContext body with memory-only IO and
  # public synthetic inputs. The expensive artifact build crosses the deadline.
  body='\n'.join(line for line in source.splitlines() if not line.startswith('import ')).split("if(process.argv[1]===")[0].replace('export function prepareContext','function prepareContext')
  script=r'''
const assert=require('node:assert/strict');let clock=1000,writes=0,expireDuringBuild=true;
const digest=x=>JSON.stringify(x),same=(a,b)=>digest(a)===digest(b),pub={grant:{body:{id:'fixture-grant'}},release:{body:{notAfter:999999}}};
const FIXED={publicConfigDigest:digest(pub),grantHash:digest(pub.grant),targetReleaseId:'fixture-target',nativeVersion:'fixture-native',targetAppVersion:'fixture-app',sourceDirectory:'/fixture/source'};
const plan={schema:'r16.native-recovery-maintenance.plan.v3',approvedAt:1000,expiresAt:301000,rollbackDeadline:1801000,targetReleaseId:FIXED.targetReleaseId,targetNativeVersion:FIXED.nativeVersion,targetAppVersion:FIXED.targetAppVersion,packageInventoryHash:'inventory',nonce:'fixture'};
const PATHS={public:'public',proposal:'proposal',reviewed:'reviewed',native:'native',localCutover:'cutover'};
const records={plan,proposal:{fixture:true},reviewed:{fixture:true},native:{codeManifest:'/fixture/source/native-manifest.json'},cutover:{phase:'ACTIVE',grantId:'fixture-grant'}};
function json(p){return p.endsWith('/plan.json')?plan:records[p];}
function need(v,c){if(!v)throw Object.assign(Error(c),{code:c});}
const fn=new Function('fx','const {ROOT,STATE,json,protectedBytes,atomicJson,digest,sha,need,rootContext,verifyCapsule,same,buildPublicationArtifacts,FIXED,PATHS,captureLocal,verifySourceDelivery,Date,process}=fx;\n'+BODY+'\nreturn prepareContext;')({
ROOT:'/fixture/root',STATE:'/fixture/state',json,protectedBytes:()=>Buffer.from(JSON.stringify(pub)),atomicJson:()=>{writes++;if(!expireDuringBuild)clock=301000;},digest,sha:digest,need,rootContext(){},verifyCapsule:()=>({files:{fixture:'hash'}}),same,
buildPublicationArtifacts:()=>{if(expireDuringBuild)clock=301000;return {payloadInventoryHash:'inventory'};},FIXED,PATHS,captureLocal:()=>({configuration:{fixture:true}}),verifySourceDelivery:()=>({fixture:true}),Date:{now:()=>clock},process:{argv:['node','fixture']}});
assert.throws(fn,{code:'NATIVE_WINDOW_INVALID'});assert.equal(writes,0);
clock=1000;expireDuringBuild=false;assert.throws(fn,{code:'NATIVE_WINDOW_INVALID'});assert.equal(writes,1);
'''
  script='const BODY=Buffer.from('+json.dumps(base64.b64encode(body.encode()).decode())+',"base64").toString();\n'+script
  result=subprocess.run(('node','-e',script),capture_output=True,timeout=10)
  self.assertEqual(result.returncode,0,result.stderr.decode())
 def test_native_pending_target_or_hash_substitution_refuses_before_copy(self):
  for bad in ('hash','target'):
   e=self.entry();e.NATIVE_ACCEPTED_AT=1000000
   pending={'schema':'r16.r9.native-install-pending.v1','host':e.CLOUD,'capsuleHash':'a'*64,'entrySha256':'b'*64,'sourceRecoveryEvidence':p.PROVENANCE,'sourceAppBaseline':'STOPPED','oldPlanRenewed':False,'nonce':'c'*32}
   native={'schema':'r16.r9.native-install-confirmation.v1','issuedAt':1000000,'expiresAt':1300000,'pendingHash':e.digest(pending),'nonce':'c'*32}
   if bad=='hash':native['pendingHash']='0'*64
   else:pending['capsuleHash']='0'*64;native['pendingHash']=e.digest(pending)
   e.NATIVE_PENDING=pending;e.NATIVE_CONFIRMATION=native
   with patch.object(e,'root'),patch.object(e,'now_ms',return_value=1000000),patch.object(e,'verify_capsule',return_value=({'files':{'os_entry.py':'b'*64},'planTemplate':{'sourceRecoveryEvidence':p.PROVENANCE}}, {},b'{}')),patch.object(e,'install_capsule',side_effect=AssertionError('substitution reached copy')):
    with self.assertRaisesRegex(e.Refused,'EXACT_NEW_NATIVE_'):e.bootstrap_locked('bootstrap-cloud','a'*64)
 def test_receipt_carries_exact_historical_evidence_without_new_force_claim(self):
  raw=b.transform('run.mjs',(HERE.parent/'release-r6/run.mjs').read_bytes()).decode()
  self.assertIn('sourceRecoveryEvidence:',raw);self.assertIn('historicalSourceStopForceUsed:true,forceTerminationUsed:false',raw)
  e=self.entry()
  with tempfile.TemporaryDirectory() as tmp:
   e.STATE=Path(tmp);receipt={'schema':'r16.maintenance-completion.v3','status':'ABORTED_BEFORE_CONFIGURATION_CHANGE','sourceRecoveryEvidence':p.PROVENANCE}
   (e.STATE/'transaction-receipt.json').write_text(json.dumps(receipt));(e.STATE/'plan.json').write_text(json.dumps({'sourceRecoveryEvidence':p.PROVENANCE}))
   with patch.object(e,'secure_read',side_effect=lambda path,**kw:Path(path).read_bytes()):result=e.receipt_projection('a'*64)
   self.assertEqual(result['receipt']['sourceRecoveryEvidence'],p.PROVENANCE);self.assertFalse(result['receipt']['forceTerminationUsed'])
   receipt['sourceRecoveryEvidence']={};(e.STATE/'transaction-receipt.json').write_text(json.dumps(receipt))
   with patch.object(e,'secure_read',side_effect=lambda path,**kw:Path(path).read_bytes()),self.assertRaisesRegex(e.Refused,'RECOVERED_SOURCE_RECEIPT_DRIFT'):e.receipt_projection('a'*64)
 def test_wrong_prior_template_never_loads_old_backend(self):
  with patch.object(p.os,'getuid',return_value=0),patch.object(p.os,'geteuid',return_value=0),self.assertRaisesRegex(ValueError,'PRIOR_PLAN_IDENTITY_DRIFT'):p.verify_prior({'planTemplate':{'sourceRecoveryEvidence':{}}},{})
 def test_replaced_public_prior_reader_never_reaches_root_records(self):
  with patch.object(p.os,'getuid',return_value=0),patch.object(p.os,'geteuid',return_value=0),self.assertRaisesRegex(ValueError,'PRIOR_READER_INPUT_DRIFT'):p.verify_prior({'planTemplate':{'sourceRecoveryEvidence':p.PROVENANCE}},{name:b'foreign' for name in p.PINS})
if __name__=='__main__':unittest.main()
