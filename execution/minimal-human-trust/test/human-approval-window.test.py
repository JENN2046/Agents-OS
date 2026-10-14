"""Pure display/protocol tests only. Never creates Tk, GUI, socket or polkit."""
import base64,hashlib,importlib.util,json,unittest,unittest.mock as mock
import builtins
from pathlib import Path
spec=importlib.util.spec_from_file_location('approval_window',Path(__file__).parent.parent/'human'/'approval-window.py')
w=importlib.util.module_from_spec(spec);spec.loader.exec_module(w)
def cutover():
 raw=bytes.fromhex('302a300506032b6570032100')+bytes(range(32))
 key=base64.urlsafe_b64encode(raw).decode().rstrip('=')
 return {'action':'first_cutover_handoff','grantId':'r16-projects-daily','issuedAt':1792000000000,
  'expiresAt':1792000300000,'target':{'schema':'mht.first-cutover-target.v1',
   'phase':'FIRST_NATIVE_RECOVERY_CUTOVER','oldRootHash':'1'*64,'newRootTemplateHash':'2'*64,
   'newRootTemplate':{'issuerPublicKey':key,'releasePublicKey':key,'enrollmentAuthorityPublicKey':key},
   'sourceFreezeDigest':'3'*64,'installerHash':'4'*64,'stageIntentHash':'5'*64,
   'stopEpoch':'12345678-1234-1234-1234-123456789abc','handoffEpoch':1,
   'constraints':{'mayActivateBusiness':False,'maySettleUnknown':False,'mayReplayUnknown':False}}},raw
class Tests(unittest.TestCase):
 def test_exact_command_line_selects_one_lane_without_fallback(self):
  self.assertEqual(w.confirmation_lane([]),'standard')
  self.assertEqual(w.confirmation_lane(['--first-cutover']),'first_cutover')
  for args in [['--first-cutover','extra'],['--lane','first_cutover'],['--first-cutover','--first-cutover'],['--unsafe']]:
   with self.assertRaises(RuntimeError):w.confirmation_lane(args)
 def test_first_cutover_displays_impact_complete_target_and_public_fingerprints_without_gui(self):
  summary,raw=cutover();original=json.dumps(summary,sort_keys=True)
  display=w.format_confirmation_summary(summary,'a'*64)
  self.assertFalse(hasattr(w,'tk'),'pure formatter must not load the GUI toolkit')
  self.assertIn('首次恢复接管',display['title'])
  for text in ['当前尚未执行','停业务','封锁旧写者','UNKNOWN','不结算','不重放','不启用正常业务','向前修复','尚未应用']:
   self.assertIn(text,display['intro'])
  self.assertIn('旧信任根 SHA-256：'+'1'*64,display['details'])
  self.assertIn('新公开模板 SHA-256：'+'2'*64,display['details'])
  self.assertIn(hashlib.sha256(raw).hexdigest(),display['details'])
  self.assertIn('UTC',display['details'])
  shown=json.loads(display['details'].split('完整待确认对象：\n',1)[1])
  self.assertEqual(shown,summary);self.assertEqual(json.dumps(summary,sort_keys=True),original)
 def test_standard_lane_retains_full_existing_summary(self):
  summary={'action':'change_trust','target':{'oldRootHash':'a'*64,'newRootHash':'b'*64,'permissionsUnchanged':True}}
  display=w.format_confirmation_summary(summary,'a'*64)
  self.assertEqual(json.loads(display['details'].split('完整待确认对象：\n',1)[1]),summary)
  self.assertIn('尚未应用',display['intro']);self.assertNotIn('首次',display['title'])
 def test_unknown_action_bad_hash_and_incomplete_cutover_never_format_an_approval_button(self):
  summary,_=cutover()
  for value,digest in [({'action':'run_command'},'a'*64),(summary,'b'*63),
   ({'action':'first_cutover_handoff','target':{}},'a'*64)]:
   with self.assertRaises(RuntimeError):w.format_confirmation_summary(value,digest)
 def test_public_fingerprint_rejects_private_or_malformed_key_shapes(self):
  for value in [None,'bad',base64.urlsafe_b64encode(b'private-key-bytes').decode()]:
   with self.assertRaises(RuntimeError):w.public_fingerprint(value)
 def test_template_digest_or_phase_cannot_be_hidden_with_fallback_display(self):
  for field,value in [('phase','STAGE_ONLY'),('oldRootHash',None),('newRootTemplateHash','bad')]:
   summary,_=cutover();summary['target'][field]=value
   with self.assertRaises(RuntimeError):w.format_confirmation_summary(summary,'a'*64)
 def test_module_and_formatter_work_when_tkinter_is_unavailable(self):
  original=builtins.__import__
  def no_gui(name,*args,**kwargs):
   if name=='tkinter' or name.startswith('tkinter.'):
    raise ModuleNotFoundError('GUI toolkit intentionally unavailable in pure test')
   return original(name,*args,**kwargs)
  with mock.patch.object(builtins,'__import__',side_effect=no_gui):
   isolated=importlib.util.module_from_spec(spec);spec.loader.exec_module(isolated)
   summary,_=cutover();display=isolated.format_confirmation_summary(summary,'a'*64)
   self.assertIn('首次恢复接管',display['title'])
if __name__=='__main__':unittest.main()
