"""Complete-count synthetic asset inventories; no production reads or effects."""
import copy,hashlib,importlib.util,json,stat,types,unittest
from pathlib import Path
from unittest.mock import patch
HERE=Path(__file__).parent
def load(name,file):
 s=importlib.util.spec_from_file_location(name,HERE/file);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
a=load('r12_asset_tested','asset-verifier.py');k=load('r12_constants_asset_test','constants.py')
class Constants(unittest.TestCase):
 def test_exact_shared_literals_and_no_runtime_constants_dependency(self):
  self.assertEqual(a.ASSET_REUSE,k.ASSET_REUSE);self.assertEqual(a.TARGET_ROLE_PINS,k.TARGET_ROLE_PINS);self.assertNotIn('import constants',(HERE/'asset-verifier.py').read_text());self.assertNotIn('Documents',(HERE/'asset-verifier.py').read_text().split('import hashlib')[1])
class AssetTests(unittest.TestCase):
 def setUp(self):
  self.rows={};self.metadata={};self.package=Path(a.ASSET_REUSE['packageRoot']);self.target=Path(a.ASSET_REUSE['targetRoot']);self.original_read=a.read;self.original_sha=a.sha
  self.inventory={f'f{i:05d}':{'sha256':a.sha(b'original'),'bytes':8,'mode':0o644} for i in range(12592)}
  invhash=a.digest({n:x['sha256'] for n,x in self.inventory.items()});rolebytes={n:a.canonical({'schema':'synthetic-runtime-only','role':n.split('-')[0],'files':{}}) for n in ('app-manifest.json','native-manifest.json')}
  metadata={'PAYLOAD_INVENTORY.json':a.canonical(self.inventory),**rolebytes,'BASE_ROLE_MANIFESTS.json':b'{}','CANDIDATE.json':b'{}','R15_PUBLIC_CONFIG.json':b'{}','SHA256SUMS_PAYLOAD.txt':b'','bridge-manifest.json':b'{}'}
  self.pins={**{'payload/'+n:x['sha256'] for n,x in self.inventory.items()},**{'metadata/'+n:a.sha(raw) for n,raw in metadata.items()}}
  for name in self.inventory:self.put(self.package/'payload'/name,b'original',0o644);self.put(self.target/name,b'original',0o644)
  for name,raw in metadata.items():self.put(self.package/'metadata'/name,raw,0o644)
  for name,raw in rolebytes.items():self.put(self.target/name,raw,0o644)
  self.frozen=a.canonical({'payloadFiles':self.pins});cap=a.sha(self.frozen);self.put(a.R9_ROOT/'SOURCE_FREEZE.json',self.frozen,0o644)
  marker=a.canonical({'schema':'r16.native-recovery-payload.v3','capsuleHash':cap,'inventoryHash':invhash})+b'\n';self.put(self.target/'.maintenance-capsule.json',marker,0o600)
  closure={n:{'sha256':self.pins[n],'mode':0o644,'bytes':len(self.rows[str(self.package/n)])} for n in self.pins}
  self.policy={**a.ASSET_REUSE,'packageClosureHash':a.digest(closure),'targetInventoryHash':invhash,'targetOriginCapsuleHash':cap};self.manifest={'planTemplate':{'assetReuse':self.policy},'payloadFiles':self.pins}
  self.trees={str(self.package):(set(self.pins),{n:{'mode':0o700,'uid':0} for n in ('.','payload','metadata')}),str(self.target):(set(self.inventory)|{'app-manifest.json','native-manifest.json','.maintenance-capsule.json'},{'.':{'mode':0o755,'uid':0}})}
  self.patches=[patch.object(a,'ASSET_REUSE',self.policy),patch.object(a,'R9_CAP',cap),patch.object(a,'MARKER_SHA',a.sha(marker)),patch.object(a,'TARGET_ROLE_PINS',{n:{'sha256':a.sha(raw),'bytes':len(raw),'mode':'0o644'} for n,raw in rolebytes.items()}),patch.object(a.os,'getuid',return_value=0),patch.object(a.os,'geteuid',return_value=0),patch.object(a,'read',side_effect=self.read),patch.object(a,'tree',side_effect=self.tree),patch.object(Path,'lstat',lambda path:self.lstat(path))]
  for p in self.patches:p.start();self.addCleanup(p.stop)
 def put(self,path,raw,mode):
  key=str(path);self.rows[key]=raw;self.metadata[key]={'dev':'42','ino':str(len(self.rows)+100),'mode':mode,'uid':0,'gid':0,'nlink':1,'bytes':len(raw),'mtimeNs':'100','ctimeNs':'100'}
 def read(self,path,mode=None,maximum=64*1024*1024):
  key=str(path);raw=self.rows[key];m=self.metadata[key];a.need(mode is None or m['mode']==mode,'SYNTHETIC_MODE_REFUSED');a.need(len(raw)<=maximum,'SYNTHETIC_LIMIT_REFUSED');return raw,dict(m)
 def tree(self,path,mode):
  files,dirs=self.trees[str(path)];a.need(all(d['mode']==mode for d in dirs.values()),'ASSET_DIRECTORY_MODE_OR_OWNER');return copy.deepcopy((files,dirs))
 def lstat(self,path):
  m=self.metadata[str(path)];return types.SimpleNamespace(st_dev=int(m['dev']),st_ino=int(m['ino']),st_mode=stat.S_IFREG|m['mode'],st_uid=m['uid'],st_gid=m['gid'],st_nlink=m['nlink'],st_size=m['bytes'],st_mtime_ns=int(m['mtimeNs']),st_ctime_ns=int(m['ctimeNs']))
 def test_complete_12600_and_12595_unchanged_zero_growth_pass_stable(self):
  first=a.verify_assets(self.manifest);self.assertEqual(first,a.verify_assets(self.manifest));self.assertEqual(first['packageFiles'],12600);self.assertEqual(first['targetFiles'],12595);self.assertEqual(first['rootAndTargetGrowthBytes'],0)
 def test_scope_must_match_before_old_file_read(self):
  bad=copy.deepcopy(self.manifest);bad['planTemplate']['assetReuse']['originPlanHash']='0'*64
  with self.assertRaisesRegex(a.Refused,'EXACT_ASSET_REUSE'):a.verify_assets(bad)
 def test_missing_or_extra_package_file_is_not_a_complete_reuse(self):
  for mode in ('missing','extra'):
   original=copy.deepcopy(self.trees[str(self.package)]);files=self.trees[str(self.package)][0]
   if mode=='missing':files.remove(next(iter(files)))
   else:files.add('metadata/unreviewed.json')
   with self.assertRaisesRegex(a.Refused,'PACKAGE_FILE_SET'):a.verify_assets(self.manifest)
   self.trees[str(self.package)]=original
 def test_payload_pins_cannot_be_rebased_to_new_marker(self):
  bad=copy.deepcopy(self.manifest);bad['payloadFiles']['payload/f00000']='0'*64
  with self.assertRaisesRegex(a.Refused,'PAYLOAD_PINS'):a.verify_assets(bad)
 def test_package_byte_or_mode_drift_is_rejected(self):
  key=str(self.package/'payload/f00000');self.rows[key]=b'changed!'
  with self.assertRaisesRegex(a.Refused,'PACKAGE_BYTE'):a.verify_assets(self.manifest)
  self.rows[key]=b'original';self.metadata[key]['mode']=0o600
  with self.assertRaisesRegex(a.Refused,'MODE_REFUSED'):a.verify_assets(self.manifest)
 def test_target_byte_mode_missing_and_extra_drift_rejects(self):
  key=str(self.target/'f00000');self.rows[key]=b'changed!'
  with self.assertRaisesRegex(a.Refused,'TARGET_BYTE'):a.verify_assets(self.manifest)
  self.rows[key]=b'original';self.trees[str(self.target)][0].add('unreviewed')
  with self.assertRaisesRegex(a.Refused,'TARGET_FILE_SET'):a.verify_assets(self.manifest)
 def test_target_manifest_same_semantics_different_whitespace_is_rejected(self):
  key=str(self.target/'app-manifest.json');self.rows[key]=json.dumps(json.loads(self.rows[key]),indent=2).encode()
  with self.assertRaisesRegex(a.Refused,'ROLE_MANIFEST'):a.verify_assets(self.manifest)
 def test_old_marker_bytes_mode_and_inode_are_never_adopted(self):
  key=str(self.target/'.maintenance-capsule.json');raw=self.rows[key];self.rows[key]=raw.replace(b'r16.',b'r17.',1)
  with self.assertRaisesRegex(a.Refused,'OLD_MARKER'):a.verify_assets(self.manifest)
  self.rows[key]=raw;count=0;original=self.read
  def changed(path,*args):
   nonlocal count
   if str(path)==key:
    count+=1
    if count==2:self.metadata[key]['ino']='999999'
   return original(path,*args)
  with patch.object(a,'read',side_effect=changed):
   with self.assertRaisesRegex(a.Refused,'MARKER_IDENTITY'):a.verify_assets(self.manifest)
 def test_package700_target755_are_distinct_contracts(self):
  self.trees[str(self.package)][1]['.']['mode']=0o755
  with self.assertRaisesRegex(a.Refused,'DIRECTORY_MODE'):a.verify_assets(self.manifest)
  self.trees[str(self.package)][1]['.']['mode']=0o700;self.trees[str(self.target)][1]['.']['mode']=0o700
  with self.assertRaisesRegex(a.Refused,'DIRECTORY_MODE'):a.verify_assets(self.manifest)
 def test_metadata_change_after_read_is_not_ignored(self):
  original=self.tree;count=0
  def changed(path,mode):
   nonlocal count
   if str(path)==str(self.target):
    count+=1
    if count==2:self.metadata[str(self.target/'f00000')]['ctimeNs']='101'
   return original(path,mode)
  with patch.object(a,'tree',side_effect=changed):
   with self.assertRaisesRegex(a.Refused,'FILE_METADATA_CHANGED'):a.verify_assets(self.manifest)
 def test_extra_empty_directory_in_package_or_target_is_not_exact_reuse(self):
  for root in (self.package,self.target):
   with self.subTest(root=str(root)):
    self.trees[str(root)][1]['extra-empty']={'mode':0o700 if root==self.package else 0o755,'uid':0}
    with self.assertRaisesRegex(a.Refused,'DIRECTORY_SET_DRIFT'):a.verify_assets(self.manifest)
    del self.trees[str(root)][1]['extra-empty']
if __name__=='__main__':unittest.main()
