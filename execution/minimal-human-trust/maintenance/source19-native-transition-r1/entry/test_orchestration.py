"""Read-only source composition tests with explicit isolated OS/Node boundaries."""
import copy,importlib.util,sys,types,unittest
from pathlib import Path
from unittest.mock import Mock,patch
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('entry_test_helpers',HERE/'test_entry.py');helpers=importlib.util.module_from_spec(spec);spec.loader.exec_module(helpers)
class OrchestrationTests(unittest.TestCase):
 def setUp(self):
  self.context=helpers.modules();self.m=self.context.__enter__();self.addCleanup(lambda:self.context.__exit__(None,None,None));c=self.m['common'];self.c=c
  linux=types.ModuleType('linux_backend');linux.HOSTS={'r16-owner.service':c.LOCAL,'r16-native-link.service':c.LOCAL,'r16-native.service':c.LOCAL,'r16-app.service':c.CLOUD,'r16-bridge.service':c.CLOUD};linux.FixedLinuxBackend=Mock()
  native=types.ModuleType('native_checkpoint');native.read_app_history_preflight=Mock(return_value={'schema':'r16.source19-native-transition.public-history-preflight.v1','atomicStoppedCheckpoint':False,'authority':False});native.read_native_preflight=Mock(return_value={'schema':'r16.source19-native-transition.native-preflight.v1','atomicStoppedCheckpoint':False,'controlUnknownHash':c.digest([]),'controlUnknownCount':0,'authority':False})
  self.patch=patch.dict(sys.modules,{'linux_backend':linux,'native_checkpoint':native});self.patch.start();self.addCleanup(self.patch.stop)
  s=importlib.util.spec_from_file_location('entry_orchestration',HERE.parent/'orchestration.py');self.o=importlib.util.module_from_spec(s);s.loader.exec_module(self.o);self.linux=linux;self.native=native
 def row(self,u):return {'unit':u,'host':self.linux.HOSTS[u],'mainPid':9,'controlPid':0,'active':'active','sub':'running','pendingJob':False,'ownedPersistentFence':False,'cgroupEmpty':False}
 def cloud(self):
  rows={u:self.row(u)for u in self.o.CLOUD_ROLES};return {'schema':'r16.source19-native-transition.cloud-preparation.v1','host':self.c.CLOUD,'originalBaseline':rows,'factsHash':'a'*64,'publicState':{'evidence':{'inventoryStatus':'COMPLETE','observedAt':1000}},'historyPreflight':self.native.read_app_history_preflight.return_value,'authority':False}
 def adapter(self,host):
  a=self.o.EntryAdapter.__new__(self.o.EntryAdapter);a.host=host;a.authority=None;a.readonly=self.o.ReadOnlyContext(host);a.backend=Mock();a.backend.snapshot.side_effect=lambda unit,h:self.row(unit);a.manifest={'mode':'READONLY_PREFLIGHT_SOURCE','planTemplate':{},'revisionRequest':{'forward':None,'recovery':None,'legacy21_22Disposition':'CANCELLED_UNALLOCATED_REPLAN'}};a._cloud_projection=None;a._cloud_call=Mock(return_value=self.cloud());return a
 def test_readonly_context_no_effect_and_no_nonfixed_target(self):
  a=self.o.ReadOnlyContext(self.c.LOCAL)
  with patch.object(self.o.foreground,'root'):
   a.require(None,'native-preflight');self.assertRaisesRegex(Exception,'PREPARATION_EFFECT_REFUSED',a.require,None,'native-signal');self.assertRaisesRegex(Exception,'PREPARATION_FIXED_ROLE_REQUIRED',a.require,None,'inspect',{'unit':'other.service'});self.assertRaisesRegex(Exception,'PREPARATION_EFFECT_REFUSED',a.require,'a'*64,'inspect')
 def test_cloud_capture_is_exact_own_two_roles_no_native_fields(self):
  a=self.adapter(self.c.CLOUD)
  with patch.object(self.o,'public_state',return_value={'evidence':{'observedAt':1000}}):result=a.prepare()
  self.assertEqual(set(result['originalBaseline']),set(self.o.CLOUD_ROLES));self.assertNotIn('nativeTargetHash',result);self.assertNotIn('planFields',result);self.assertFalse(result['authority']);self.assertEqual(a.backend.snapshot.call_count,4)
 def test_cloud_changed_instance_or_pendingjob_rejected_without_statewrite(self):
  for mode in('pending','instance'):
   a=self.adapter(self.c.CLOUD);calls=[0]
   def sample(unit,h):
    calls[0]+=1;row=self.row(unit)
    if mode=='pending':row['pendingJob']=True
    elif calls[0]>2:row['mainPid']=10
    return row
   a.backend.snapshot.side_effect=sample
   with patch.object(self.o,'public_state',return_value={'evidence':{}}):self.assertRaises(Exception,a.prepare)
 def test_real_three_plus_two_merge_does_not_allocate_revisions_or_fabricate_empty_controls(self):
  a=self.adapter(self.c.LOCAL);rev={'revisionInventory':{'complete':True,'observedAt':1000},'revisionPlan':{'status':'BLOCKED_UNSIGNED_REQUEST_NOT_ALLOCATED','forward':None,'recovery':None}}
  with patch.object(self.o,'public_state',return_value={'evidence':{'inventoryStatus':'COMPLETE'}}),patch.object(self.o,'node',return_value=rev):result=a.prepare()
  self.assertEqual(set(result['originalBaseline']),set(self.linux.HOSTS));self.assertIsNone(result['planFields']['revisionPlanHash']);self.assertIsNone(result['revisionPlan']['forward']);self.native.read_native_preflight.assert_called_once();self.assertEqual(result['planFields']['approvedControlUnknownHash'],self.c.digest([]))
 def test_missing_real_native_collector_never_falls_back_to_zero(self):
  a=self.adapter(self.c.LOCAL);del self.native.read_native_preflight
  self.assertRaisesRegex(Exception,'REGISTERED_NATIVE_PREFLIGHT_COLLECTOR_REQUIRED',a._native_live_control_inventory)
 def test_incomplete_revision_inventory_is_explicitly_blocked_not_complete(self):
  a=self.adapter(self.c.LOCAL)
  with patch.object(self.o,'public_state',return_value={'evidence':{'inventoryStatus':'BLOCKED'}}),patch.object(self.o,'node',side_effect=AssertionError('no invented plan')):result=a.prepare()
  self.assertFalse(result['revisionInventory']['complete']);self.assertEqual(result['revisionInventory']['status'],'BLOCKED_ACTUAL_INVENTORY_NOT_COMPLETE')
 def test_stable_compare_ignores_only_diagnostics_and_keeps_real_identity_changes(self):
  a=self.adapter(self.c.LOCAL);old={'factsHash':'a','rows':{'pid':8},'revisionInventory':{'observedAt':1000},'revisionPlan':{'inventoryHash':'b'}};new=copy.deepcopy(old);new['revisionInventory']['observedAt']=1001;new['factsHash']='c';a.prepare=Mock(return_value=new);self.assertEqual(a.verify_prepared(old),new)
  new['rows']['pid']=9;self.assertRaisesRegex(Exception,'SOURCE_CHANGED_DURING_NATIVE_CONFIRMATION',a.verify_prepared,old)
 def test_no_stub_installer_or_rpc_effect_can_claim_success(self):
  a=self.adapter(self.c.LOCAL)
  for fn in(a.admit_cloud,a.run_local,a.dispatch_cloud):self.assertRaisesRegex(Exception,'READONLY_SOURCE_',fn)
 def test_public_state_metadata_timestamp_alone_does_not_change_facts_hash(self):
  a=self.adapter(self.c.CLOUD)
  with patch.object(self.o,'public_state',side_effect=[{'evidence':{'observedAt':1000}},{'evidence':{'observedAt':2000}}]):first=a.prepare();second=a.prepare()
  self.assertEqual(first['factsHash'],second['factsHash'])
if __name__=='__main__':unittest.main()
