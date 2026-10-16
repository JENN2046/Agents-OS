import dataclasses,importlib.util,json,sys,unittest
from pathlib import Path
HERE=Path(__file__).parent
spec=importlib.util.spec_from_file_location('r6_phase_tested',HERE/'quiescence.py');q=importlib.util.module_from_spec(spec);sys.modules[spec.name]=q;spec.loader.exec_module(q)
class AppPhaseTests(unittest.TestCase):
 def mapping(self,role,phase):
  unit='r16-'+role+'.service';directory=q.SOURCE_RELEASE if phase=='SOURCE' else q.TARGET_RELEASE
  manifest=json.loads((HERE/'package/metadata'/('BASE_ROLE_MANIFESTS.json' if phase=='SOURCE' else role+'-manifest.json')).read_bytes())
  if phase=='SOURCE':manifest=manifest[role]
  selector=q.ROLE_SELECTORS[unit][1];config={'schema':'r16.'+role+'-host.v1','publicConfiguration':q.ROLE_SELECTORS[unit][2],'codeManifest':directory+'/'+role+'-manifest.json'}
  return unit,{selector:json.dumps(config).encode(),config['codeManifest']:json.dumps(manifest).encode()}
 def test_source_target_manifest_and_changed_file_pins_are_phase_exact(self):
  for role in ('app','native'):
   for phase in ('SOURCE','TARGET'):
    with self.subTest(role=role,phase=phase):
     unit,rows=self.mapping(role,phase);got,pins=q.selected_code_pins(unit,rows.__getitem__);self.assertEqual(got,phase);self.assertEqual(pins,q.expected_code_pins(unit,phase))
     if role=='app':self.assertIn((q.SOURCE_RELEASE if phase=='SOURCE' else q.TARGET_RELEASE)+'/app/workspace-host.mjs',pins)
 def test_foreign_selector_is_rejected_without_reading_foreign_file(self):
  unit,rows=self.mapping('app','TARGET');key=q.ROLE_SELECTORS[unit][1];config=json.loads(rows[key]);config['codeManifest']='/etc/forbidden.json';rows[key]=json.dumps(config).encode()
  with self.assertRaisesRegex(q.Refused,'ROLE_SELECTOR_DRIFT'):q.selected_code_pins(unit,rows.__getitem__)
 def test_wrong_manifest_or_source_bytes_cannot_look_like_new_app(self):
  unit,rows=self.mapping('app','TARGET');name=q.TARGET_RELEASE+'/app-manifest.json';m=json.loads(rows[name]);m['files']['app/app-runner.mjs']='0'*64;rows[name]=json.dumps(m).encode()
  with self.assertRaisesRegex(q.Refused,'ROLE_MANIFEST_VERSION_DRIFT'):q.selected_code_pins(unit,rows.__getitem__)
 def test_only_pinned_phase_changes_are_accepted_after_fencing(self):
  def row(phase,pins):return q.Snapshot('r16-app.service',q.CLOUD,'inactive','dead',0,0,0,0,(),0,tuple(pins.items()),'a'*64,True,send_sigkill='no',kill_signal='15',code_phase=phase)
  old=row('SOURCE',q.expected_code_pins('r16-app.service','SOURCE'));new=row('TARGET',q.expected_code_pins('r16-app.service','TARGET'))
  self.assertTrue(q.compatible_code(old,new));self.assertTrue(q.compatible_code(new,old));self.assertFalse(q.compatible_code(old,dataclasses.replace(new,code_hashes=(('foreign','0'*64),))))
if __name__=='__main__':unittest.main()
