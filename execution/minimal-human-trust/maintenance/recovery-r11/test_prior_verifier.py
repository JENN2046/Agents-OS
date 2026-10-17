"""R11 isolated historical18, actual validator and memory Node IO regression.
No root/SSH/production state/credentials/services. Signature fixtures use new keys.
"""
import contextlib,copy,hashlib,importlib.util,json,sys,types,unittest
from contextlib import ExitStack
from pathlib import Path
from unittest.mock import patch,Mock
HERE=Path(__file__).parent
REPO=HERE.parent/'first-stop-r8'
def load(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);sys.modules[name]=m;s.loader.exec_module(m);return m
p=load('r11_prior_tested',HERE/'prior-verifier.py')
k=load('r11_prior_constants_test',HERE/'constants.py')
f=load('r11_synthetic_original_ledger_fixture',REPO/'test_ledger_checkpoint.py');L=f.m
D=load('r11_original_manifest_validator_test',REPO/'stop_driver.py')
class SharedConstants(unittest.TestCase):
 def test_exact_source18_scope_and_original_asset_literals(self):
  self.assertEqual(k.SOURCE_DELIVERY_HASH,p.ROLLBACK_DELIVERY);self.assertEqual(k.SOURCE_REVISION,18);self.assertEqual(k.FORWARD_REVISION,19);self.assertEqual(k.ROLLBACK_REVISION,20)
  self.assertIn("B=Path("+repr(k.CLOUD_SOURCE)+")",p.REMOTE_READER)
  self.assertNotIn('import constants',(HERE/'prior-verifier.py').read_text())
 def test_source18_template_gate_precedes_any_sealed_component_execution(self):
  with patch.object(p.os,'getuid',return_value=0),patch.object(p.os,'geteuid',return_value=0),patch.object(p.socket,'gethostname',return_value=p.CLOUD):
   for revision in (16,17,19):
    with self.subTest(revision=revision),self.assertRaisesRegex(p.Refused,'REAL_REVISION18_SOURCE_REQUIRED'):p.validate_inputs({'planTemplate':{'sourceRecoveryEvidence':p.PROVENANCE,'sourceDeliveryRevision':revision,'sourceDeliveryHash':p.ROLLBACK_DELIVERY}},{})
class HistoricalRecords(unittest.TestCase):
 def setUp(self):
  self.provenance=copy.deepcopy(p.PROVENANCE);v=self.provenance['r10ClosedRollback'];self.capraw=b'synthetic-original-capsule';self.cap=p.sha(self.capraw)
  plan={'capsuleHash':self.cap,'sourceFreezeHash':self.cap,'rollbackDeadline':v['rollbackDeadline']};planraw=p.canonical(plan);v['planHash']=p.sha(planraw)
  delivery={'body':{'revision':18},'signature':'synthetic-only'};v['deliveryHash']=p.digest(delivery)
  signed={'delivery':delivery,'preserveCurrentLedgers':True,'restoreHistoricalLedgerSnapshot':False}
  tx={'schema':'r16.maintenance-transaction.v3','mode':'ROLLBACK','steps':{n:{'status':'DONE'} for n in ('rollback-signed','rollback-cloud','rollback-local','rollback-activate','rollback-readback')}};tx['steps']['activate']={'status':'INTENT'};tx['steps']['rollback-signed']['resultHash']=p.digest(signed)
  journal={'schema':'r16.os-maintenance-journal.v3','planHash':v['planHash'],'cycle':1,'pending':None}
  receipt={'schema':'r16.maintenance-completion.v3','status':v['status'],'configurationRevision':18,'completedAt':v['completedAt'],'businessAcceptance':False}
  self.docs={'capsule.json':self.capraw,'plan.json':planraw,'context.json':b'{"syntheticContext":true}','transaction-transaction.json':p.canonical(tx)+b'\n','transaction-receipt.json':p.canonical(receipt)+b'\n','transaction-rollback-signed.json':p.canonical(signed)+b'\n','os-journal.json':p.canonical({**journal,'phase':'OS_ACTIVE'}),'cloud-os-journal.json':p.canonical({**journal,'phase':'RECOVERY_STOPPING'}),'cloud-commit-18.json':p.canonical({'revision':18,'deliveryHash':v['deliveryHash'],'businessLedgerMutationPerformed':False})}
  self.keys={'context.json':'contextHash','transaction-transaction.json':'transactionHash','transaction-receipt.json':'canonicalReceiptHash','transaction-rollback-signed.json':'rollbackSignedHash','os-journal.json':'localOsJournalHash','cloud-os-journal.json':'cloudOsJournalHash','cloud-commit-18.json':'cloudCommitHash'}
  for name,key in self.keys.items():v[key]=p.sha(self.docs[name])
  self.asset=types.SimpleNamespace(read=lambda path,*args:(self.docs[Path(path).name],{}),parse=json.loads)
  for x in (patch.object(p,'PROVENANCE',self.provenance),patch.object(p,'R10_CAP',self.cap)):
   x.start();self.addCleanup(x.stop)
 def test_realistic_closed_rollback_retains_intent_history_and_cloud_recovery_stopping(self):
  with patch.object(p.time,'time',return_value=999999999999):
   local=p.old_records(self.asset,p.LOCAL);cloud=p.old_records(self.asset,p.CLOUD)
  self.assertEqual(local['journal']['phase'],'OS_ACTIVE');self.assertEqual(cloud['journal']['phase'],'RECOVERY_STOPPING');self.assertNotIn('transaction-receipt.json',cloud['hashes'])
 def test_raw_receipt_context_or_transaction_drift_is_not_recannonicalized(self):
  for name in ('transaction-receipt.json','context.json','transaction-transaction.json'):
   original=self.docs[name];self.docs[name]+=b' '
   with self.subTest(name=name),self.assertRaises(p.Refused):p.old_records(self.asset,p.LOCAL)
   self.docs[name]=original
 def altered(self,name,change):
  value=json.loads(self.docs[name]);change(value);self.docs[name]=p.canonical(value);self.provenance['r10ClosedRollback'][self.keys[name]]=p.sha(self.docs[name])
 def test_cloud_history_cannot_be_relabelled_active_even_with_synthetic_matching_pin(self):
  self.altered('cloud-os-journal.json',lambda v:v.update(phase='OS_ACTIVE'))
  with self.assertRaisesRegex(p.Refused,'OS_HISTORY_DRIFT'):p.old_records(self.asset,p.CLOUD)
 def test_pending_journal_or_unfinished_rollback_is_not_closed(self):
  self.altered('os-journal.json',lambda v:v.update(pending={'operation':'start'}))
  with self.assertRaisesRegex(p.Refused,'OS_HISTORY_DRIFT'):p.old_records(self.asset,p.LOCAL)
  self.altered('os-journal.json',lambda v:v.update(pending=None));self.altered('transaction-transaction.json',lambda v:v['steps']['rollback-activate'].update(status='INTENT'))
  with self.assertRaisesRegex(p.Refused,'ROLLBACK_NOT_CLOSED'):p.old_records(self.asset,p.LOCAL)
 def test_terminal_revision_or_historical_time_drift_refuses(self):
  self.altered('transaction-receipt.json',lambda v:v.update(configurationRevision=16))
  with self.assertRaisesRegex(p.Refused,'CANONICAL_ROLLBACK'):p.old_records(self.asset,p.LOCAL)
 def test_historical_signed_record_cannot_authorize_restoring_snapshot(self):
  self.altered('transaction-rollback-signed.json',lambda v:v.update(restoreHistoricalLedgerSnapshot=True))
  with self.assertRaisesRegex(p.Refused,'SIGNED_ROLLBACK_SCOPE'):p.old_records(self.asset,p.LOCAL)
class TransportAndBoundary(unittest.TestCase):
 def test_local_reread_drift_refuses_and_cloud_does_not_recurse(self):
  with patch.object(p,'validate_inputs'),patch.object(p.socket,'gethostname',return_value=p.CLOUD),patch.object(p,'host_facts',return_value={'constant':'facts'}),patch.object(p,'fresh_cloud') as remote:
   first=p.verify_prior({},{});self.assertEqual(first['schema'],'r16.r11.source-recovery-readback.v1');self.assertEqual(first,p.verify_prior({},{}));remote.assert_not_called()
  with patch.object(p,'validate_inputs'),patch.object(p.socket,'gethostname',return_value=p.LOCAL),patch.object(p,'host_facts',side_effect=[{'before':1},{'after':2}]),patch.object(p,'fresh_cloud',return_value={}):
   with self.assertRaisesRegex(p.Refused,'LOCAL_CHANGED'):p.verify_prior({},{})
 def test_fresh_cloud_uses_only_new_sealed_source_stdin_and_actual18_digest(self):
  manifest={'files':{},'payloadFiles':{},'planTemplate':{}};facts={'host':p.CLOUD,'originalCheckpointDigest':p.CHECKPOINT,'oldR10AuthorityReused':False};packet={'schema':'r16.r11.sealed-cloud-facts.v1','capsuleHash':p.digest(manifest),'facts':facts}
  with patch.object(p.subprocess,'run',return_value=types.SimpleNamespace(returncode=0,stdout=p.canonical(packet))) as run:self.assertEqual(p.fresh_cloud(manifest),facts)
  argv=run.call_args.args[0];self.assertIn('-T',argv);self.assertIn('sudo -n',argv[-1]);self.assertIn('/usr/bin/python3 -I -B -',argv[-1]);self.assertNotIn('/usr/libexec/',argv[-1]);self.assertIn(b'EXPECTED_CAP=',run.call_args.kwargs['input'])
 def test_original_reader_tamper_refused_before_module_execution(self):
  with patch.object(p,'protected',return_value=b'tampered public reader'),patch.object(p,'component') as component:
   with self.assertRaisesRegex(p.Refused,'ORIGINAL_READER_SOURCE_DRIFT'):p.cloud_checkpoint(None,{})
   component.assert_not_called()
 def test_old_maintenance_cgroup_walk_failure_is_not_empty(self):
  good=b'Id=r16-native-recovery-maintenance-r10.service\nActiveState=failed\nMainPID=0\nControlPID=0\nJob=0\n'
  def fail(root,**kw):kw['onerror'](PermissionError('synthetic'));return []
  with patch.object(p.subprocess,'run',return_value=types.SimpleNamespace(returncode=0,stdout=good)),patch.object(Path,'exists',return_value=True),patch.object(p.os,'walk',side_effect=fail):
   with self.assertRaises(PermissionError):p.manager_inactive()
class Authority(unittest.TestCase):
 def setUp(self):
  _,_,pub,_,issuer,_=f.fixture();self.pub=pub;self.issuer=issuer
  self.plan={'approvedAt':10,'rollbackDeadline':200};self.control={'grantId':'r16-projects-daily','grantVersion':1,'status':'ACTIVE','connectRequested':True}
  self.manifest={'role':'app','files':{}};self.selector={'schema':'r16.app-host.v1','publicConfiguration':str(L.PUBLIC),'codeManifest':str(L.SOURCE/'app-manifest.json')}
  self.cutover={'schema':'r16.cloud-cutover.v1','phase':'ACTIVE','grantId':'r16-projects-daily','releaseId':'r16-daily-20261012-r15'};self.token={'schema':'r16.cloud-start-attempt.v1','grantId':'r16-projects-daily','revision':18}
  self.delivery=f.sign({'schema':'r16.configuration-delivery.v1','revision':18,'issuedAt':20,'publicConfig':pub,'control':self.control},issuer)
  self.accepted={'schema':1,'revision':1,'maxNow':100,'data':{'kind':'r16.cloud-publication.v1','accepted':self.delivery}}
  self.commit={'status':'CONFIGURATION_COMMITTED_SERVICES_FENCED','revision':18,'businessLedgerMutationPerformed':False,'deliveryHash':L.digest(self.delivery),'publicConfigHash':L.digest(pub)}
  self.stack=ExitStack();self.addCleanup(self.stack.close)
  for obj,key,value in ((p,'PUBLIC',L.digest(pub)),(p,'ROLLBACK_DELIVERY',L.digest(self.delivery)),(L,'PUBLIC_DIGEST',L.digest(pub)),(L,'GRANT_DIGEST',L.digest(pub['grant'])),(L,'APP_VERSION',L.digest(self.manifest))):self.stack.enter_context(patch.object(obj,key,value))
 def call(self):return p.validate_authority(L,self.pub,self.selector,self.manifest,self.control,self.cutover,self.token,self.accepted,self.plan,self.commit,100)
 def test_real_signed18_is_accepted_without_old_rev16_gate(self):self.assertEqual(self.call()['revision'],18)
 def test_signature_revision_control_selector_cutover_token_and_receipt_drift_refuse(self):
  cases=[(self.delivery,'signature','A'*86),(self.delivery['body'],'revision',17),(self.delivery['body'],'revision',True),(self.delivery['body'],'issuedAt',201),(self.control,'connectRequested',False),(self.selector,'codeManifest','/other/app-manifest.json'),(self.cutover,'releaseId','other'),(self.token,'revision',16),(self.commit,'deliveryHash','0'*64)]
  for obj,key,value in cases:
   with self.subTest(key=key,value=value):
    old=obj[key];obj[key]=value
    with self.assertRaises(Exception):self.call()
    obj[key]=old
 def test_other_valid_issuer_signed18_is_not_the_real_rollback_delivery(self):
  replacement=f.sign({**self.delivery['body'],'issuedAt':21},self.issuer);self.accepted['data']['accepted']=replacement;self.commit['deliveryHash']=L.digest(replacement)
  with self.assertRaisesRegex(p.Refused,'COMMIT_MISMATCH'):self.call()
 def test_wrapper_clock_may_advance_but_data_or_rollback_cannot(self):
  before={'revision':3,'maxNow':100,'acceptedData':{'kind':'same'},'proof':{'revision':18}};after={**before,'revision':4,'maxNow':101};p.same_authority(L,before,after)
  for after in ({**after,'revision':2},{**after,'maxNow':99},{**after,'acceptedData':{'kind':'changed'}}):
   with self.assertRaises(p.Refused):p.same_authority(L,before,after)

class FullCapture(unittest.TestCase):
 def setUp(self):
  self.c,self.target,self.pub,self.pins,_,_=f.fixture();self.stack=ExitStack();self.addCleanup(self.stack.close)
  for key,value in (('PUBLIC_DIGEST',L.digest(self.pub)),('GRANT_DIGEST',L.digest(self.pub['grant'])),('PINS',self.pins)):self.stack.enter_context(patch.object(L,key,value))
  result=L.validate_checkpoint(self.c,self.target,self.pub,100);self.c.update(result)
  self.approval={'target':self.target,**{k:result[k] for k in ('expectedOriginalUnknown','expectedLeaseBindings','expectedSemanticBindingsDigest')}}
  self.manifest=D.checkpoint_manifest(self.c,self.approval);self.original={'checkpoint':self.manifest}
  self.dirs={name.rsplit('/',1)[0]:(7,index+1) for index,name in enumerate(self.c['files'])};self.ids={name:(8,index+1) for index,name in enumerate(self.c['files'])}
  registration={'app':self.dirs['host']};self.tree=Mock(side_effect=lambda **kw:(copy.deepcopy(self.c['files']),self.ids.copy(),self.dirs.copy()));self.scan=Mock()
  self.authority={'public':self.pub,'revision':1,'maxNow':100,'proof':{'revision':18}}
  patches=[patch.object(p,'CHECKPOINT',D.digest(self.manifest)),patch.object(p,'EXPECTED_FILES',len(self.c['files'])),patch.object(p,'exited',return_value={'stopped':True}),patch.object(p,'authority_snapshot',return_value=self.authority),patch.object(p.time,'time',return_value=.1),patch.object(L,'_target_state',return_value='EXITED'),patch.object(L,'read_registration',return_value=({},'a'*64)),patch.object(L,'registration_bindings',return_value=registration),patch.object(L,'read_store_tree',self.tree),patch.object(L,'_scan_writers',self.scan)]
  for x in patches:self.stack.enter_context(x)
 def call(self):return p.full_checkpoint_capture(L,D,self.approval,self.original,{'approvedAt':10,'rollbackDeadline':200})
 def test_full_real_old_crypto_and_manifest_validators_double_read_and_scan(self):
  result=self.call();self.assertEqual(result['status'],'FULL_ORIGINAL_APP_CHECKPOINT_READONLY_PASS');self.assertEqual(result['originalUnknownCount'],2);self.assertEqual(self.tree.call_count,2);self.assertEqual(self.scan.call_count,2)
 def test_second_full_tree_drift_is_refused(self):
  rows=copy.deepcopy(self.c['files']);rows['host/state.json']['bytes']+=b' '
  self.tree.side_effect=[(self.c['files'],self.ids,self.dirs),(rows,self.ids,self.dirs)]
  with self.assertRaisesRegex(p.Refused,'CHECKPOINT_CHANGED'):self.call()
 def test_corrupt_signature_in_unchanged_but_invalid_tree_is_refused(self):
  host=L.parse(self.c['files']['host/state.json']['bytes']);host['data']['operations'][0]['operation']['signature']='A'*86;self.c['files']['host/state.json']['bytes']=f.raw(host)
  with self.assertRaises(Exception):self.call()
 def test_original_full_manifest_or_expected_count_mismatch_refuses(self):
  self.original['checkpoint']={}
  with self.assertRaisesRegex(p.Refused,'FULL_ORIGINAL_APP_CHECKPOINT_CHANGED'):self.call()
  self.original['checkpoint']=self.manifest
  with patch.object(p,'EXPECTED_FILES',3555):
   with self.assertRaisesRegex(p.Refused,'FULL_ORIGINAL_APP_CHECKPOINT_CHANGED'):self.call()
 def test_real_foreign_writer_or_registry_error_is_not_suppressed(self):
  self.scan.side_effect=L.Refused('FOREIGN_WRITABLE_FD')
  with self.assertRaisesRegex(L.Refused,'FOREIGN_WRITABLE_FD'):self.call()

class SourceBoundary(unittest.TestCase):
 def test_exact_frozen_original_source_pins_and_no_mutating_interfaces(self):
  for name,pin in p.READER_PINS.items():self.assertEqual(p.sha((REPO/name).read_bytes()),pin)
  source=(HERE/'prior-verifier.py').read_text()
  for bad in ('LedgerCheckpoint().capture','validate_cloud_authority(','.write_text(','.write_bytes(','os.kill(','SIGKILL','daemon-reload','systemctl\x27,\x27start','ProtectedStore('):self.assertNotIn(bad,source)

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
const accepted={body:{schema:'r16.configuration-delivery.v1',revision:18,publicConfig:pub,control},signature:'synthetic-signature'};
const app={schema:'r16.app-host.v1',codeManifest:'/opt/r16/releases/r16-daily-20261012-r15/app-manifest.json',publicConfiguration:'/etc/r16-cloud/public-config.json'};
const values={'/etc/r16-cloud/app-host.json':app,'/etc/r16-cloud/public-config.json':pub,'/etc/r16-cloud/authority-control.json':control,'/etc/r16-cloud/cutover.json':{schema:'r16.cloud-cutover.v1',phase:'ACTIVE',grantId:'r16-projects-daily',releaseId:'r16-daily-20261012-r15'},'/var/lib/r16-cloud/start-attempt.json':{schema:'r16.cloud-start-attempt.v1',grantId:'r16-projects-daily',revision:18}};
let acceptedReads=0;
const read=path=>{
 if(path==='/var/lib/r16-maintenance/recovery-r9/package/metadata/R15_PUBLIC_CONFIG.json')return pub;
 if(path==='/var/lib/r16-maintenance/recovery-r10/cloud-source-app.json')return app;
 if(path==='/var/lib/r16-cloud/authority/state.json'){
  acceptedReads++;const result={schema:1,revision:acceptedReads,maxNow:100+acceptedReads,data:{kind:'r16.cloud-publication.v1',accepted:structuredClone(accepted)}};
  if(scenario==='badInteger')result.revision=true;
  if(scenario==='old16')result.data.accepted.body.revision=16;
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
globalThis.FIXTURE_IO={protectedBytes:path=>Buffer.from(JSON.stringify(read(path))),same:(a,b)=>canon(a)===canon(b),need:(v,c)=>{if(!v)throw Error(c)},digest:x=>canon(x)===canon(pub)?'be3ff2b5125f8212206d2848bb32889c3c6b50a8ca56aa3b1a4bc4359591bbdb':canon(x)===canon(accepted)?'6bd634f3cc4e9335acaff00286ed7f885df5f03b97deec0ac33286f759328c51':createHash('sha256').update(canon(x)).digest('hex')};
globalThis.FIXTURE_CRYPTO={verified:x=>{if(canon(x)!==canon(accepted))throw Error('FIXTURE_SIGNED_ENVELOPE_CHANGED');return x.body;}};
'''
  script=fixture.replace('SCENARIO',json.dumps(scenario)).replace('const scenario=','{\nconst scenario=',1)+'\n}\n'+body
  return subprocess.run([node,'--input-type=module','-e',script,'cloud'],capture_output=True,text=True,timeout=10)
 def test_clock_only_wrapper_change_is_ignored_but_business_changes_refuse(self):
  good=self.node_capture('clock');self.assertEqual(good.returncode,0,good.stderr);first=json.loads(good.stdout)
  again=self.node_capture('clock');self.assertEqual(again.returncode,0,again.stderr);self.assertEqual(first,json.loads(again.stdout))
  for scenario in ('old16','data','envelope','selector','badInteger','badMaxNow','badSchema','badTopShape','revisionRollback','maxNowRollback'):
   with self.subTest(scenario=scenario):self.assertNotEqual(self.node_capture(scenario).returncode,0)

class LocalNodeMemoryProtocol(unittest.TestCase):
 """Actual Node local control flow; synthetic IO/state/crypto import seams.
 Real Ed25519 and full old L/D validators are exercised in Authority/FullCapture.
 """
 def capture(self,scenario):
  import shutil,subprocess
  node=shutil.which('node');self.assertIsNotNone(node,'Node required, never skip');body=p.NODE_READONLY
  for old,new in (("await import(pathToFileURL(R+'/io.mjs'))","globalThis.FIXTURE_IO"),("await import(pathToFileURL(R+'/legacy/lease-core.mjs'))","globalThis.FIXTURE_CRYPTO"),("await import(pathToFileURL(R+'/state.mjs'))","globalThis.FIXTURE_STATE")):
   self.assertEqual(body.count(old),1);body=body.replace(old,new)
  body=body.replace("'9f238a13a8d4179748de57c4f416e856601c6975fb54506c699984113bc408dc'",'globalThis.FIXTURE_CONTEXT_HASH')
  fixture=r'''import {createHash}from'node:crypto';
{
const scenario=SCENARIO,canon=x=>x===null||typeof x!=='object'?JSON.stringify(x):Array.isArray(x)?'['+x.map(canon).join(',')+']':'{'+Object.keys(x).sort().map(k=>JSON.stringify(k)+':'+canon(x[k])).join(',')+'}';
const pub={issuerPublicKey:'synthetic-issuer',grant:{body:{id:'r16-projects-daily'}},release:{body:{id:'r16-daily-20261012-r15'}},versions:{app:'source-app',native:'source-native',bridge:'source-bridge'}};
const control={grantId:'r16-projects-daily',grantVersion:1,status:'ACTIVE',connectRequested:true};
const envelope={body:{schema:'r16.configuration-delivery.v1',revision:18,issuedAt:20,publicConfig:pub,control},signature:'synthetic-signature'};
const digest=x=>canon(x)===canon(pub)?'be3ff2b5125f8212206d2848bb32889c3c6b50a8ca56aa3b1a4bc4359591bbdb':canon(x)===canon(envelope)?'6bd634f3cc4e9335acaff00286ed7f885df5f03b97deec0ac33286f759328c51':createHash('sha256').update(canon(x)).digest('hex');
const snapshots={proposal:{release:pub.release,versions:pub.versions},reviewed:{source:true},native:{codeManifest:'/opt/r16/releases/r16-daily-20261012-r15/native-manifest.json'},cutover:{phase:'ACTIVE'}};
const before={issuerDataHash:'issuer',configurationInvariantHash:'config',originalUnknown:{p2vox:'UNKNOWN',pmog2:'UNKNOWN'},projectBusinessHashes:{p2vox:'old',pmog2:'old'}};
const context={schema:'r16.native-recovery-context.v3',planHash:'9d9d329749c4c1ec52fd49c6827881593cc043e80af9d5550b742c22bae307f1',inputs:{sourcePublicConfig:pub},snapshots,before};
const contextRaw=Buffer.from(JSON.stringify(context));globalThis.FIXTURE_CONTEXT_HASH=createHash('sha256').update(contextRaw).digest('hex');let contextReads=0,captures=0;
const PATHS={public:'/run/r16-owner/public-config.json',proposal:'/etc/r16-owner/release-proposal.json',reviewed:'/etc/r16-owner/reviewed-installation.json',native:'/etc/r16/native-host.json',localCutover:'/etc/r16/cutover.json'};
const values={[PATHS.public]:pub,[PATHS.proposal]:snapshots.proposal,[PATHS.reviewed]:snapshots.reviewed,[PATHS.native]:snapshots.native,[PATHS.localCutover]:snapshots.cutover};
globalThis.FIXTURE_IO={digest,same:(a,b)=>canon(a)===canon(b),need:(v,c)=>{if(!v)throw Error(c)},protectedBytes:path=>{
 if(path==='/var/lib/r16-maintenance/recovery-r9/package/metadata/R15_PUBLIC_CONFIG.json')return Buffer.from(JSON.stringify(pub));
 if(path==='/var/lib/r16-maintenance/recovery-r10/context.json'){contextReads++;return scenario==='contextDrift'&&contextReads>1?Buffer.concat([contextRaw,Buffer.from(' ')]):contextRaw;}
 if(!(path in values))throw Error('UNEXPECTED_FIXTURE_READ');let value=structuredClone(values[path]);
 if(scenario==='selector'&&path===PATHS.native)value.codeManifest='/target/native-manifest.json';
 if(scenario==='publication'&&path===PATHS.public)value.versions.native='target';
 if(scenario==='proposal'&&path===PATHS.proposal)value.versions.native='target';
 return Buffer.from(JSON.stringify(value));}};
globalThis.FIXTURE_CRYPTO={verified:x=>{if(x?.signature!=='synthetic-signature')throw Error('FIXTURE_BAD_SIGNATURE');return x.body;}};
globalThis.FIXTURE_STATE={PATHS,assertPreserved:(a,b)=>{for(const k of Object.keys(before))if(canon(a[k])!==canon(b[k]))throw Error('FIXTURE_ORIGINALS_CHANGED')},captureLocal:()=>{
 captures++;const configuration={connectionNonce:1,delivery:{envelope:structuredClone(envelope),revision:18,hash:digest({publicConfig:pub,control,connectionNonce:1})}};
 if(scenario==='old16'){configuration.delivery.revision=16;configuration.delivery.envelope.body.revision=16;}
 if(scenario==='badSignature')configuration.delivery.envelope.signature='changed';
 if(scenario==='ownerHash')configuration.delivery.hash='f'.repeat(64);
 if(scenario==='connectionNonce')configuration.connectionNonce=2;
 if(scenario==='deliveryDrift'&&captures>1)configuration.delivery.revision=19;
 const current={...structuredClone(before),configuration};if(scenario==='issuer')current.issuerDataHash='changed';return current;
}};
}
'''
  return subprocess.run([node,'--input-type=module','-e',fixture.replace('SCENARIO',json.dumps(scenario))+'\n'+body,'local'],capture_output=True,text=True,timeout=10)
 def test_real18_owner_publication_and_originals_return_stable_facts(self):
  first=self.capture('good');self.assertEqual(first.returncode,0,first.stderr);again=self.capture('good');self.assertEqual(again.returncode,0,again.stderr);self.assertEqual(json.loads(first.stdout),json.loads(again.stdout));self.assertEqual(json.loads(first.stdout)['sourceDeliveryHash'],p.ROLLBACK_DELIVERY)
 def test_old16_or_owner_binding_selector_context_or_business_drift_refuse(self):
  for scenario in ('old16','badSignature','ownerHash','connectionNonce','selector','publication','proposal','contextDrift','deliveryDrift','issuer'):
   with self.subTest(scenario=scenario):self.assertNotEqual(self.capture(scenario).returncode,0)

if __name__=='__main__':unittest.main()
