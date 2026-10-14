import importlib.util,json,struct,unittest,unittest.mock as mock
from pathlib import Path
spec=importlib.util.spec_from_file_location('broker',Path(__file__).parent.parent/'human'/'approval-broker.py')
b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)
class Peer:
 def __init__(self,uid=1000,confirm=True,lane='standard',selection=None):
  self.uid=uid;self.confirm=confirm;self.sent=[];self.reads=0
  self.selection=selection if selection is not None else {'operation':'select_confirmation','lane':lane}
 def getsockopt(self,*args):return struct.pack('3i',123,self.uid,self.uid)
 def settimeout(self,*args):pass
 def sendall(self,raw):self.sent.append(json.loads(raw))
 def recv(self,size):
  self.reads+=1
  if self.reads==1:return (json.dumps(self.selection)+'\n').encode()
  preview=self.sent[0]
  return (json.dumps({'confirm':self.confirm,'proposalHash':preview['proposalHash'],'challenge':preview['challenge']})+'\n').encode()
class Tests(unittest.TestCase):
 def setUp(self):
  self.records=[];self.calls=[];self.peer=Peer()
  self.preview=lambda *args:{'summary':{'action':'revoke_grant','grantId':'fixed'},'proposalHash':'a'*64}
  self.sign=lambda *args:(self.calls.append('sign') or {'ok':True,'status':'APPROVED_NOT_APPLIED'})
  self.auth=lambda subject,summary:self.calls.append(('polkit',subject,summary))
  self.patches=[mock.patch.object(b,'process_identity',lambda pid,uid:(pid,777,uid)),
   mock.patch.object(b,'protected_state',lambda:None),mock.patch.object(b,'write_once',lambda name,value:self.records.append((name,value)))]
  for p in self.patches:p.start();self.addCleanup(p.stop)
 def test_exact_confirmation_plus_os_auth_precedes_durable_intent_and_signature(self):
  b.handle(self.peer,self.preview,self.auth,self.sign)
  self.assertEqual(self.calls[0][0],'polkit');self.assertEqual(self.calls[0][1],(123,777,1000))
  self.assertIn('confirmationChallenge',self.calls[0][2]);self.assertEqual(self.calls[1],'sign')
  self.assertEqual(len(self.records),2);self.assertEqual(self.peer.sent[-1]['status'],'APPROVED_NOT_APPLIED')
 def test_uid_only_is_not_authorization(self):
  def deny(*args):raise b.Refused()
  with self.assertRaises(b.Refused):b.handle(self.peer,self.preview,deny,self.sign)
  self.assertEqual(self.records,[]);self.assertEqual(self.calls,[])
 def test_cancel_never_authenticates_or_signs(self):
  with self.assertRaises(b.Refused):b.handle(Peer(confirm=False),self.preview,self.auth,self.sign)
  self.assertEqual(self.records,[]);self.assertEqual(self.calls,[])
 def test_foreign_uid_rejects_before_preview(self):
  with self.assertRaises(b.Refused):b.handle(Peer(uid=999),lambda *args:self.fail(),self.auth,self.sign)
 def test_pid_reuse_between_preview_and_approval_rejects(self):
  with mock.patch.object(b,'process_identity',side_effect=[(123,777,1000),(123,778,1000)]):
   with self.assertRaises(b.Refused):b.handle(self.peer,self.preview,self.auth,self.sign)
  self.assertEqual(self.records,[])
 def test_signer_failure_retains_intent_and_never_sends_success(self):
  def fail(*args):raise b.Refused()
  with self.assertRaises(b.Refused):b.handle(self.peer,self.preview,self.auth,fail)
  self.assertEqual(len(self.records),1);self.assertEqual(len(self.peer.sent),1)
 def test_repeated_proposal_intent_refuses_before_sign(self):
  with mock.patch.object(b,'write_once',side_effect=FileExistsError):
   with self.assertRaises(FileExistsError):b.handle(self.peer,self.preview,self.auth,self.sign)
  self.assertNotIn('sign',self.calls)
 def test_polkit_command_has_exact_process_target_and_no_shell(self):
  seen={}
  class Child:
   def wait(self,timeout):return 0
  def call(command,**options):seen.update(command=command,options=options);return Child()
  b.fresh_polkit((123,777,1000),{'action':'revoke_grant','nonce':'exact'},call)
  self.assertIn('123,777,1000',seen['command']);self.assertIn('--allow-user-interaction',seen['command'])
  self.assertEqual(seen['command'].count('--details'),2);self.assertNotIn('--detail',seen['command']);
  self.assertNotIn('shell',seen['options']);self.assertEqual(seen['command'][0],'/usr/bin/pkcheck')
 def test_exact_system_cgroup_and_template_slice_only(self):
  unit='minimal-human-trust-approval@2.service'
  direct='0::/system.slice/'+unit
  nested=r'0::/system.slice/system-minimal\x2dhuman\x2dtrust\x2dapproval.slice/'+unit
  self.assertEqual(b.approval_unit(direct),unit);self.assertEqual(b.approval_unit(nested),unit)
  for value in [direct+'\n'+direct,'0::/user.slice/system.slice/'+unit,
    '0::/system.slice/arbitrary.slice/'+unit,direct+'/child',direct+'\nmalformed']:
   with self.assertRaises(b.Refused):b.approval_unit(value)
 def test_confirmation_wait_is_total_sixty_seconds_not_five(self):
  class P:
   def settimeout(self,seconds):self.seconds=seconds
   def recv(self,size):return b'{"confirm":false}\n'
  p=P()
  with mock.patch.object(b.time,'monotonic',side_effect=[100,111]):
   self.assertEqual(b.read_request(p),{'confirm':False})
  self.assertEqual(p.seconds,49)
  with mock.patch.object(b.time,'monotonic',side_effect=[100,161]):
   with self.assertRaises(b.Refused):b.read_request(p)
 def test_complete_stage_plan_is_identical_in_native_preview_and_polkit(self):
  core={'schema':'mht.first-trust-stage-authorization.v2','phase':'STAGE_ONLY',
    'sourceReleaseId':'r16-daily-20261012-r15','targetReleaseId':'r16-daily-20261012-r17',
    'grantId':'r16-projects-daily','grantHash':'5'*64,'grantVersion':1,
    'r15PublicConfigDigest':'6'*64,'reviewedManifestHash':'7'*64,'recoveryEvidenceDigest':'8'*64,
    'sourceFreezeDigest':'1'*64,'installerHash':'2'*64,'issuerSnapshotHash':'3'*64,'trustRootsDigest':'9'*64,
    'stopEpoch':'12345678-1234-1234-1234-123456789abc','handoffEpoch':7,
    'issuedAt':1792000000000,'expiresAt':1792000060000,
    'constraints':{'mayInstall':False,'mayActivateBusiness':False,'mayHandoffIssuer':False,
      'maySettleUnknown':False,'requireSignedThreeRoleStop':True,
      'requireProtectedSameEpochIssuerSnapshot':True,'requireOldWriterFenced':True}}
  summary={'action':'enroll_human','target':{'stageAuthorizationHash':'4'*64,'stageAuthorization':core}}
  self.assertLess(len(json.dumps(summary).encode()),8192)
  preview=lambda *args:{'summary':summary,'proposalHash':'a'*64}
  b.handle(self.peer,preview,self.auth,self.sign)
  self.assertEqual(self.peer.sent[0]['summary'],summary)
  authorized=self.calls[0][2]
  self.assertEqual(authorized['target'],summary['target'])
  self.assertEqual(authorized['target']['stageAuthorization'],core)
  self.assertIn('confirmationChallenge',authorized)
 def cutover_fixture(self):
  summary={'action':'first_cutover_handoff','target':{'schema':'mht.first-cutover-target.v1',
    'phase':'FIRST_NATIVE_RECOVERY_CUTOVER','stopEpoch':'12345678-1234-1234-1234-123456789abc',
    'stageIntentHash':'1'*64,'stageResultHash':'2'*64,'installerHash':'3'*64,'sourceFreezeDigest':'4'*64,
    'constraints':{'mayActivateBusiness':False,'maySettleUnknown':False,'mayReplayUnknown':False}}}
  preview=lambda operation,digest:(self.calls.append(('preview-operation',operation)) or
    {'ok':True,'summary':summary,'proposalHash':'a'*64})
  def sign(operation,digest):
   self.calls.append(('sign-operation',operation))
   return {'ok':True,'status':'APPROVED_NOT_APPLIED','proposalHash':digest,
    'approval':{'body':{'schema':'mht.first-cutover-authorization.v1','action':'first_cutover_handoff',
      'proposalHash':digest},'signature':'S'*86}}
  return summary,preview,sign
 def test_cutover_lane_selects_exact_bootstrap_operations_and_preserves_target_in_os_journal(self):
  summary,preview,sign=self.cutover_fixture()
  b.handle(Peer(lane='first_cutover'),preview,self.auth,sign)
  self.assertEqual(self.calls[0],('preview-operation','preview_first_cutover'))
  self.assertEqual(self.calls[1][0],'polkit');self.assertEqual(self.calls[1][2]['target'],summary['target'])
  self.assertEqual(self.calls[2],('sign-operation','sign_first_cutover'))
  self.assertEqual(len(self.records),2)
  self.assertEqual(self.records[1][1]['approval']['body']['schema'],'mht.first-cutover-authorization.v1')
  self.assertEqual(self.records[0][1]['peerUid'],1000)
 def test_missing_extra_or_unknown_lane_frame_has_no_legacy_fallback(self):
  for selection in [{},{'confirm':True},{'operation':'select_confirmation','lane':'admin'},
   {'operation':'select_confirmation','lane':'standard','extra':True},
   {'operation':'run_command','lane':'first_cutover'},['standard']]:
   with self.subTest(selection=selection):
    with self.assertRaises(b.Refused):b.handle(Peer(selection=selection),lambda *args:self.fail('preview'),self.auth,self.sign)
  self.assertEqual(self.records,[]);self.assertEqual(self.calls,[])
 def test_cutover_and_standard_actions_cannot_cross_selected_lanes(self):
  summary,preview,sign=self.cutover_fixture()
  with self.assertRaises(b.Refused):b.handle(Peer(lane='standard'),preview,self.auth,sign)
  with self.assertRaises(b.Refused):b.handle(Peer(lane='first_cutover'),self.preview,self.auth,self.sign)
  self.assertEqual(self.records,[])
  self.assertFalse(any(isinstance(value,tuple) and value[0]=='polkit' for value in self.calls))
 def test_cutover_cancel_or_denied_fresh_polkit_never_creates_identity_or_intent(self):
  summary,preview,sign=self.cutover_fixture()
  with self.assertRaises(b.Refused):b.handle(Peer(lane='first_cutover',confirm=False),preview,self.auth,sign)
  self.assertEqual(self.records,[])
  self.assertFalse(any(isinstance(value,tuple) and value[0]=='sign-operation' for value in self.calls))
  self.calls.clear()
  def deny(*args):raise b.Refused()
  with self.assertRaises(b.Refused):b.handle(Peer(lane='first_cutover'),preview,deny,sign)
  self.assertEqual(self.records,[])
  self.assertFalse(any(isinstance(value,tuple) and value[0]=='sign-operation' for value in self.calls))
 def test_oversize_complete_target_refuses_before_preview_prompt_and_polkit(self):
  preview=lambda *args:{'summary':{'action':'first_cutover_handoff','target':{'data':'x'*9000}},'proposalHash':'a'*64}
  peer=Peer(lane='first_cutover')
  with self.assertRaises(b.Refused):b.handle(peer,preview,self.auth,self.sign)
  self.assertEqual(peer.sent,[]);self.assertEqual(self.records,[]);self.assertEqual(self.calls,[])
 def test_cutover_result_substitution_retains_intent_and_never_sends_success(self):
  for change in [lambda r:r.update(status='INSTALLED'),lambda r:r.update(proposalHash='b'*64),
   lambda r:r.update(extra='authority'),lambda r:r['approval']['body'].update(proposalHash='b'*64),
   lambda r:r['approval']['body'].update(action='change_trust'),lambda r:r.update(approval=None)]:
   with self.subTest(change=change):
    self.records.clear();self.calls.clear();summary,preview,sign=self.cutover_fixture();peer=Peer(lane='first_cutover')
    def wrong(operation,digest):
     value=sign(operation,digest);change(value);return value
    with self.assertRaises(b.Refused):b.handle(peer,preview,self.auth,wrong)
    self.assertEqual(len(self.records),1);self.assertEqual(len(peer.sent),1)
 def test_bad_standard_status_retains_intent_and_never_claims_application(self):
  with self.assertRaises(b.Refused):b.handle(self.peer,self.preview,self.auth,
   lambda *args:{'ok':True,'status':'APPLIED'})
  self.assertEqual(len(self.records),1);self.assertEqual(len(self.peer.sent),1)
 def test_bootstrap_fixed_path_cannot_be_selected_by_client_frame(self):
  self.assertEqual(b.SIGNER,'/usr/lib/minimal-human-trust/human/approval-bootstrap.mjs')
  with self.assertRaises(b.Refused):b.handle(Peer(selection={'operation':'select_confirmation',
   'lane':'first_cutover','signer':'/tmp/unsafe.mjs'}),self.preview,self.auth,self.sign)
  self.assertEqual(self.records,[])
if __name__=='__main__':unittest.main()
