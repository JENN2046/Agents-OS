"""Isolated R10 provenance/protocol tests. Never root, SSH, services or real ledgers."""
import contextlib,copy,hashlib,importlib.util,json,types,unittest
from pathlib import Path
from unittest.mock import patch,Mock
HERE=Path(__file__).parent
def load(n,f):
 s=importlib.util.spec_from_file_location(n,HERE/f);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
p=load('r10_prior_under_test','prior-verifier.py');k=load('r10_prior_constants','constants.py')
class Constants(unittest.TestCase):
 def test_pins_exact_raw_bytes_not_parsed_digest(self):
  v=p.PROVENANCE['r9ClosedAbort'];self.assertEqual(v['planHash'],k.R9_PLAN);self.assertEqual(v['capsuleHash'],k.R9_CAP);self.assertEqual(v['canonicalReceiptHash'],k.R9_RECEIPT);self.assertEqual(v['transactionHash'],k.R9_TX);self.assertEqual(v['localOsJournalHash'],k.R9_LOCAL_OS);self.assertEqual(v['cloudOsJournalHash'],k.R9_CLOUD_OS)
  raw=b'{"x":1}\n';self.assertNotEqual(p.sha(raw),p.digest(json.loads(raw)));self.assertNotIn('import constants',(HERE/'prior-verifier.py').read_text())
 def test_only_readonly_old_node_functions_no_old_entrypoints(self):
  for call in ('captureLocal','assertPreserved','verifySourceDelivery'):self.assertIn(call,p.NODE_READONLY)
  for call in ('runFixedMaintenance','installed_context','cloud-helper','/usr/libexec/','native_approval','drive('):self.assertNotIn(call,p.NODE_READONLY+p.REMOTE_READER)
  self.assertNotIn('Date.now()',p.NODE_READONLY);self.assertNotIn('node:child_process',p.NODE_READONLY)
class Records(unittest.TestCase):
 def setUp(self):
  self.provenance=copy.deepcopy(p.PROVENANCE);v=self.provenance['r9ClosedAbort'];plan={'capsuleHash':p.R9_CAP,'sourceFreezeHash':p.R9_CAP,'rollbackDeadline':v['rollbackDeadline']}
  osj={'schema':'r16.os-maintenance-journal.v3','planHash':v['planHash'],'pending':None};tx={'mode':'ABORT','steps':{'baseline':{'status':'DONE'},'payload':{'status':'INTENT'}}};receipt={'schema':'r16.maintenance-completion.v3','status':v['status'],'completedAt':v['completedAt'],'businessAcceptance':False}
  self.docs={'plan.json':p.canonical(plan),'capsule.json':b'exact synthetic old source','os-journal.json':p.canonical(osj)+b'\n','cloud-os-journal.json':p.canonical(osj),'transaction-transaction.json':p.canonical(tx)+b'\n','transaction-receipt.json':p.canonical(receipt)+b'\n'}
  v.update(planHash=p.sha(self.docs['plan.json']),canonicalReceiptHash=p.sha(self.docs['transaction-receipt.json']),transactionHash=p.sha(self.docs['transaction-transaction.json']),localOsJournalHash=p.sha(self.docs['os-journal.json']),cloudOsJournalHash=p.sha(self.docs['cloud-os-journal.json']))
  for n in ('os-journal.json','cloud-os-journal.json'):
   j=json.loads(self.docs[n]);j['planHash']=v['planHash'];self.docs[n]=p.canonical(j)+b'\n'
  v['localOsJournalHash']=p.sha(self.docs['os-journal.json']);v['cloudOsJournalHash']=p.sha(self.docs['cloud-os-journal.json'])
  self.asset=types.SimpleNamespace(read=lambda path,*args:(self.docs[Path(path).name],{'fixture':True}),parse=json.loads)
  self.patchers=[patch.object(p,'PROVENANCE',self.provenance),patch.object(p,'R9_CAP',p.sha(self.docs['capsule.json'])),patch.object(p.os,'listdir',return_value=list(self.docs))]
  for x in self.patchers:x.start();self.addCleanup(x.stop)
  # Synthetic plan must bind the same synthetic capsule hash.
  plan['capsuleHash']=plan['sourceFreezeHash']=p.R9_CAP;self.docs['plan.json']=p.canonical(plan);v['planHash']=p.sha(self.docs['plan.json'])
  for n in ('os-journal.json','cloud-os-journal.json'):
   j=json.loads(self.docs[n]);j['planHash']=v['planHash'];self.docs[n]=p.canonical(j)+b'\n'
  v['localOsJournalHash']=p.sha(self.docs['os-journal.json']);v['cloudOsJournalHash']=p.sha(self.docs['cloud-os-journal.json'])
 def test_historical_closed_abort_survives_expiry_without_new_authority(self):
  local=p.old_records(self.asset,p.LOCAL);cloud=p.old_records(self.asset,p.CLOUD);self.assertIn('transaction-receipt.json',local['hashes']);self.assertNotIn('transaction-receipt.json',cloud['hashes'])
 def test_receipt_same_semantics_different_whitespace_or_newline_refuses(self):
  self.docs['transaction-receipt.json']=self.docs['transaction-receipt.json'].rstrip(b'\n')
  with self.assertRaisesRegex(p.Refused,'TRANSACTION_RECEIPT_JSON_DRIFT'):p.old_records(self.asset,p.LOCAL)
 def test_tx_or_journal_raw_drift_refuses(self):
  for n in ('transaction-transaction.json','os-journal.json','cloud-os-journal.json'):
   old=self.docs[n];self.docs[n]=old+b' '
   with self.assertRaises(p.Refused):p.old_records(self.asset,p.CLOUD if n.startswith('cloud') else p.LOCAL)
   self.docs[n]=old
 def test_sign_commit_pending_variants_refuse(self):
  for name in ('release-signature.json','.delivery-signature.json.pending','transaction-signed.json','transaction-cloud-commit.json','transaction-local-commit.json'):
   with patch.object(p.os,'listdir',return_value=[*self.docs,name]):
    with self.assertRaisesRegex(p.Refused,'SIGN_OR_COMMIT'):p.old_records(self.asset,p.LOCAL)
 def test_wrong_mode_or_unclosed_pending_refuses_even_with_new_synthetic_pin(self):
  for n,field,value in (('transaction-transaction.json','mode','FORWARD'),('os-journal.json','pending',{'operation':'start'}),('transaction-receipt.json','completedAt',self.provenance['r9ClosedAbort']['rollbackDeadline']+1)):
   original=self.docs[n];old_pin=copy.deepcopy(self.provenance['r9ClosedAbort']);doc=json.loads(original);doc[field]=value;self.docs[n]=p.canonical(doc);key={'transaction-transaction.json':'transactionHash','os-journal.json':'localOsJournalHash','transaction-receipt.json':'canonicalReceiptHash'}[n];self.provenance['r9ClosedAbort'][key]=p.sha(self.docs[n])
   with self.assertRaises(p.Refused):p.old_records(self.asset,p.LOCAL)
   self.docs[n]=original;self.provenance['r9ClosedAbort']=old_pin
class Protocol(unittest.TestCase):
 def test_cloud_is_nonrecursive_and_local_rechecks_own_facts(self):
  own={'schema':'fake','unchanged':True}
  with patch.object(p,'validate_inputs'),patch.object(p.socket,'gethostname',return_value=p.CLOUD),patch.object(p,'host_facts',return_value=own),patch.object(p,'fresh_cloud') as remote:
   r=p.verify_prior({},{});self.assertEqual(r['schema'],'r16.r10.source-recovery-readback.v1');remote.assert_not_called()
  with patch.object(p,'validate_inputs'),patch.object(p.socket,'gethostname',return_value=p.LOCAL),patch.object(p,'host_facts',side_effect=[own,{'changed':True}]),patch.object(p,'fresh_cloud',return_value={'cloud':'fresh'}):
   with self.assertRaisesRegex(p.Refused,'LOCAL_CHANGED'):p.verify_prior({},{})
 def test_facts_hash_is_stable_not_nonce_or_time(self):
  own={'host':p.LOCAL,'facts':'same'}
  with patch.object(p,'validate_inputs'),patch.object(p.socket,'gethostname',return_value=p.LOCAL),patch.object(p,'host_facts',return_value=own),patch.object(p,'fresh_cloud',return_value={'host':p.CLOUD,'facts':'same'}):
   self.assertEqual(p.verify_prior({},{}),p.verify_prior({},{}))
 def test_remote_transport_uses_stdin_not_oversize_argv_and_no_old_helper(self):
  manifest={'schema':'synthetic','files':{},'payloadFiles':{},'planTemplate':{}};facts={'schema':'r16.r10.host-source-facts.v1','host':p.CLOUD,'originalCheckpointDigest':p.CHECKPOINT,'oldR9AuthorityReused':False};packet={'schema':'r16.r10.sealed-cloud-facts.v1','capsuleHash':p.digest(manifest),'facts':facts}
  with patch.object(p.subprocess,'run',return_value=types.SimpleNamespace(returncode=0,stdout=p.canonical(packet))) as run:self.assertEqual(p.fresh_cloud(manifest),facts)
  argv=run.call_args.args[0];self.assertIn('-T',argv);self.assertIn('sudo -n',argv[-1]);self.assertIn('/usr/bin/python3 -I -B -',argv[-1]);self.assertNotIn('/usr/libexec/',argv[-1]);self.assertIn(b'EXPECTED_CAP=',run.call_args.kwargs['input']);self.assertNotIn('native_identity',p.REMOTE_READER);self.assertNotIn('bootstrap',p.REMOTE_READER)
 def test_remote_mismatch_timeout_or_extra_output_never_passes(self):
  for stdout,status in ((b'{}',0),(b'{bad}',0),(b'{}',78),(b'x'*65537,0)):
   with patch.object(p.subprocess,'run',return_value=types.SimpleNamespace(returncode=status,stdout=stdout)):
    with self.assertRaises((p.Refused,ValueError)):p.fresh_cloud({})
 def test_no_root_or_wrong_new_provenance_refused_before_component_compile(self):
  with patch.object(p.os,'getuid',return_value=1000),patch.object(p.os,'geteuid',return_value=1000):
   with self.assertRaisesRegex(p.Refused,'ROOT_FIXED_HOST'):p.validate_inputs({},{})
  with patch.object(p.os,'getuid',return_value=0),patch.object(p.os,'geteuid',return_value=0),patch.object(p.socket,'gethostname',return_value=p.CLOUD):
   with self.assertRaisesRegex(p.Refused,'EXACT_PRIOR_PROVENANCE'):p.validate_inputs({'planTemplate':{'sourceRecoveryEvidence':{}}},{})
 def test_old_maintenance_group_unreadable_is_not_empty(self):
  good=b'Id=r16-native-recovery-maintenance-r9.service\nActiveState=failed\nMainPID=0\nControlPID=0\nJob=0\n'
  def fail(root,**kw):kw['onerror'](PermissionError('synthetic'));return []
  with patch.object(p.subprocess,'run',return_value=types.SimpleNamespace(returncode=0,stdout=good)),patch.object(Path,'exists',return_value=True),patch.object(p.os,'walk',side_effect=fail):
   with self.assertRaises(PermissionError):p.manager_inactive()
 def test_active_maintenance_or_pending_job_is_not_historical(self):
  good=b'Id=r16-native-recovery-maintenance-r9.service\nActiveState=failed\nMainPID=0\nControlPID=0\nJob=0\n'
  for raw in (good.replace(b'failed',b'active'),good.replace(b'MainPID=0',b'MainPID=42'),good.replace(b'Job=0',b'Job=21')):
   with patch.object(p.subprocess,'run',return_value=types.SimpleNamespace(returncode=0,stdout=raw)):
    with self.assertRaisesRegex(p.Refused,'STILL_ACTIVE'):p.manager_inactive()

class NodeMemoryProtocol(unittest.TestCase):
 """Execute actual cloud branch with ONLY import boundaries replaced by synthetic IO.
 Signature verification is a fixture stub here; production uses frozen real crypto.
 """
 def node_capture(self,scenario):
  import shutil,subprocess
  node=shutil.which('node');self.assertIsNotNone(node,'Node is required, never skip')
  body=p.NODE_READONLY
  for old,new in (("await import(pathToFileURL(R+'/io.mjs'))","globalThis.FIXTURE_IO"),("await import(pathToFileURL(R+'/legacy/lease-core.mjs'))","globalThis.FIXTURE_CRYPTO")):
   self.assertEqual(body.count(old),1);body=body.replace(old,new)
  fixture=r'''import {createHash}from'node:crypto';
const scenario=SCENARIO;
const canon=x=>x===null||typeof x!=='object'?JSON.stringify(x):Array.isArray(x)?'['+x.map(canon).join(',')+']':'{'+Object.keys(x).sort().map(k=>JSON.stringify(k)+':'+canon(x[k])).join(',')+'}';
const pub={issuerPublicKey:'synthetic',release:{body:{id:'r16-daily-20261012-r15'}}};
const control={grantId:'r16-projects-daily',grantVersion:1,status:'ACTIVE',connectRequested:true};
const accepted={body:{schema:'r16.configuration-delivery.v1',revision:16,publicConfig:pub,control},signature:'synthetic-signature'};
const app={schema:'r16.app-host.v1',codeManifest:'/opt/r16/releases/r16-daily-20261012-r15/app-manifest.json',publicConfiguration:'/etc/r16-cloud/public-config.json'};
const values={'/etc/r16-cloud/app-host.json':app,'/etc/r16-cloud/public-config.json':pub,'/etc/r16-cloud/authority-control.json':control,'/etc/r16-cloud/cutover.json':{schema:'r16.cloud-cutover.v1',phase:'ACTIVE',grantId:'r16-projects-daily',releaseId:'r16-daily-20261012-r15'},'/var/lib/r16-cloud/start-attempt.json':{schema:'r16.cloud-start-attempt.v1',grantId:'r16-projects-daily',revision:16}};
let acceptedReads=0;
const read=path=>{
 if(path==='/var/lib/r16-maintenance/recovery-r9/package/metadata/R15_PUBLIC_CONFIG.json')return pub;
 if(path==='/var/lib/r16-maintenance/recovery-r9/cloud-source-app.json')return app;
 if(path==='/var/lib/r16-cloud/authority/state.json'){
  acceptedReads++;const result={schema:1,revision:acceptedReads,maxNow:100+acceptedReads,data:{kind:'r16.cloud-publication.v1',accepted:structuredClone(accepted)}};
  if(scenario==='badInteger')result.revision=true;
  if(scenario==='badMaxNow')result.maxNow=-1;
  if(scenario==='badSchema')result.schema=2;
  if(scenario==='badTopShape')result.unreviewed=true;
  if(acceptedReads>1&&scenario==='revisionRollback')result.revision=0;
  if(acceptedReads>1&&scenario==='maxNowRollback')result.maxNow=0;
  if(acceptedReads>1&&scenario==='data')result.data.unexpected='changed';
  if(acceptedReads>1&&scenario==='envelope')result.data.accepted.signature='changed';
  return result;
 }
 if(!(path in values))throw Error('FIXTURE_UNEXPECTED_PATH');
 const result=structuredClone(values[path]);if(scenario==='selector'&&acceptedReads>0&&path==='/etc/r16-cloud/app-host.json')result.codeManifest='/opt/unreviewed/app-manifest.json';return result;
};
globalThis.FIXTURE_IO={protectedBytes:path=>Buffer.from(JSON.stringify(read(path))),same:(a,b)=>canon(a)===canon(b),need:(v,c)=>{if(!v)throw Error(c)},digest:x=>canon(x)===canon(pub)?'be3ff2b5125f8212206d2848bb32889c3c6b50a8ca56aa3b1a4bc4359591bbdb':canon(x)===canon(accepted)?'5ee11707da0d3a524550db92f8c0a5a80b7a8dac8c97f5a907b47fc956c6ec44':createHash('sha256').update(canon(x)).digest('hex')};
globalThis.FIXTURE_CRYPTO={verified:x=>{if(canon(x)!==canon(accepted))throw Error('FIXTURE_SIGNED_ENVELOPE_CHANGED');return x.body;}};
'''
  script=fixture.replace('SCENARIO',json.dumps(scenario)).replace('const scenario=','{\nconst scenario=',1)+'\n}\n'+body
  return subprocess.run([node,'--input-type=module','-e',script,'cloud'],capture_output=True,text=True,timeout=10)
 def test_clock_only_wrapper_change_is_ignored_but_business_changes_refuse(self):
  good=self.node_capture('clock');self.assertEqual(good.returncode,0,good.stderr);first=json.loads(good.stdout)
  again=self.node_capture('clock');self.assertEqual(again.returncode,0,again.stderr);self.assertEqual(first,json.loads(again.stdout))
  for scenario in ('data','envelope','selector','badInteger','badMaxNow','badSchema','badTopShape','revisionRollback','maxNowRollback'):
   with self.subTest(scenario=scenario):self.assertNotEqual(self.node_capture(scenario).returncode,0)

if __name__=='__main__':unittest.main()
