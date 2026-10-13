import importlib.util,json,struct,unittest,unittest.mock as mock
from pathlib import Path
spec=importlib.util.spec_from_file_location('broker',Path(__file__).parent.parent/'human'/'approval-broker.py')
b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)
class Peer:
 def __init__(self,uid=1000,confirm=True):self.uid=uid;self.confirm=confirm;self.sent=[]
 def getsockopt(self,*args):return struct.pack('3i',123,self.uid,self.uid)
 def settimeout(self,*args):pass
 def sendall(self,raw):self.sent.append(json.loads(raw))
 def recv(self,size):
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
if __name__=='__main__':unittest.main()
