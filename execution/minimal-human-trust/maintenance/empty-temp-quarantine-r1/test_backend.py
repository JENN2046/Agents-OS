"""Real temporary inode/rename/fsync plus synthetic signed R8 ledger fixtures.

No production paths, root operations, service commands, signals or SSH occur.
"""
from contextlib import ExitStack
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import stat
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

HERE=Path(__file__).resolve().parent
def load(name,path):
 spec=importlib.util.spec_from_file_location(name,path);module=importlib.util.module_from_spec(spec);sys.modules[name]=module;spec.loader.exec_module(module);return module
R=load('r8_linux_backend',HERE.parent/'first-stop-r8/linux_backend.py')
L=load('r8_ledger_checkpoint',HERE.parent/'first-stop-r8/ledger_checkpoint.py')
f=load('quarantine_synthetic_ledger_fixture',HERE.parent/'first-stop-r8/test_ledger_checkpoint.py')
b=load('quarantine_backend_tested',HERE/'backend.py')

class TempFiles:
 def __init__(self,root):self.root=root
 def directory(self,path,mode=0o700,create=False,allow_missing=False):
  path=Path(path);assert path.is_relative_to(self.root)
  if not path.exists():
   if create:path.mkdir(parents=True,mode=mode)
   elif allow_missing:return None
   else:raise FileNotFoundError()
  s=path.lstat();b.need(stat.S_ISDIR(s.st_mode) and not stat.S_ISLNK(s.st_mode) and stat.S_IMODE(s.st_mode)==0o700,'ROOT_DIRECTORY_UNSAFE')
  return path

class BackendTests(unittest.TestCase):
 def setUp(self):
  self.stack=ExitStack();self.addCleanup(self.stack.close)
  self.tmp=Path(self.stack.enter_context(tempfile.TemporaryDirectory()))
  self.store=self.tmp/'store';self.store.mkdir(mode=0o700)
  c,self.target,self.pub,self.pins,self.issuer,self.peers=f.fixture();self.target['sourceHashes']=copy.deepcopy(R.SOURCE_HASHES)
  for name,row in c['files'].items():
   path=self.store/name.removeprefix('host/');path.parent.mkdir(parents=True,exist_ok=True,mode=0o700);path.write_bytes(row['bytes']);path.chmod(0o600)
  self.artifact=self.store/b.ARTIFACT;self.artifact.write_bytes(b'');self.artifact.chmod(0o600)
  self.expected={**b.metadata(self.artifact.stat(),b''),'uid':1000} # Same synthetic UID mapping as the descriptor fixture below.
  self.owner='8'*64;self.qdir=self.tmp/'quarantine'
  self.cap=types.SimpleNamespace(approval_hash=self.owner,target_hash=R.digest(self.target),require=lambda *a:None)
  self.backend=b.QuarantineBackend(self.cap)
  self.backend.system=types.SimpleNamespace(isolated=True,owner_uid=1000,require_root=lambda:None)
  self.backend.files=TempFiles(self.tmp)
  self.backend.paths=R.Paths(state=self.tmp/'state',fence=self.tmp/'fence',condition=self.tmp/'condition')
  self.observation={**self.target,'frozen':False,'freezeRequested':False,'processExited':False,'members':[self.target['pid']],'fenceOwner':None,'freezeOwner':None}
  self.backend.inspect=lambda target:copy.deepcopy(self.observation)
  st=self.store.stat();record={'schema':'r16.cloud-ledger-registration.v1','grantId':'r16-projects-daily','phase':'SEALED','specs':copy.deepcopy(L.REGISTRY_SPECS),'identities':[{'role':'app','dev':st.st_dev,'ino':st.st_ino},{'role':'bridge','dev':9,'ino':8},{'role':'gateway','dev':9,'ino':9}]}
  control={'grantId':'r16-projects-daily','grantVersion':1,'status':'ACTIVE','connectRequested':True}
  delivery=f.sign({'schema':'r16.configuration-delivery.v1','revision':16,'publicConfig':self.pub,'control':control},self.issuer)
  accepted={'schema':1,'revision':1,'maxNow':100,'data':{'kind':'r16.cloud-publication.v1','accepted':delivery}}
  cutover={'schema':'r16.cloud-cutover.v1','phase':'ACTIVE','grantId':'r16-projects-daily','releaseId':'r16-daily-20261012-r15'}
  def read_public(path):
   if path==L.PUBLIC:return self.pub
   if path==L.SELECTOR:return {'schema':'r16.app-host.v1','publicConfiguration':str(L.PUBLIC),'codeManifest':str(L.SOURCE/'app-manifest.json')}
   if path==L.CONTROL:return control
   if path==L.CUTOVER:return cutover
   if path==L.SOURCE/'app-manifest.json':return {'role':'app','files':{}}
   raise AssertionError('unexpected public path')
  def open_directory(path,**kwargs):
   assert Path(path)==self.store
   fd=os.open(path,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
   s=os.fstat(fd);assert stat.S_IMODE(s.st_mode)==0o700
   return fd
  original_tree=L.read_store_tree
  patches=[patch.object(b,'EXPECTED',self.expected),patch.object(b,'SOURCE_APP',{k:self.target[k] for k in b.SOURCE_APP}),patch.object(b,'QUARANTINE',self.qdir),patch.object(L,'STORE',self.store),patch.object(L,'PUBLIC_DIGEST',L.digest(self.pub)),patch.object(L,'GRANT_DIGEST',L.digest(self.pub['grant'])),patch.object(L,'DELIVERY_DIGEST',L.digest(delivery)),patch.object(L,'APP_VERSION',self.pub['versions']['app']),patch.object(L,'PINS',self.pins),patch.object(L,'read_public',side_effect=read_public),patch.object(L,'read_accepted',return_value=accepted),patch.object(L,'read_registration',return_value=(record,L.digest(record))),patch.object(L,'_open_directory',side_effect=open_directory),patch.object(L,'read_store_tree',side_effect=lambda **kwargs:original_tree(self.store,**kwargs)),patch.object(L,'_scan_writers'),patch.object(b,'scan_artifact_handles'),patch.object(L,'_target_state',return_value='FROZEN'),patch.object(L.os,'geteuid',return_value=0),patch.object(L.platform,'node',return_value=L.HOST),patch.object(L.time,'time',return_value=.1)]
  for item in patches:self.stack.enter_context(item)
  # Metadata seam only changes synthetic tree UID for non-1000 CI runners.
  self.stack.enter_context(f.fixture_metadata_uid())

 def freeze(self):self.observation.update(frozen=True,freezeRequested=True,fenceOwner=self.owner,freezeOwner=self.owner)
 def moved(self):
  before=self.backend.capture_before(self.target);self.freeze();receipt=self.backend.quarantine(self.target,self.owner,before)
  before['expectedQuarantinedArtifact']=receipt['artifact'];return before,receipt

 def test_original_r8_components_are_byte_exact_pinned_sources(self):
  self.assertEqual(hashlib.sha256(Path(R.__file__).read_bytes()).hexdigest(),'ce35535d2b29210d2ea099aff80fcf8ec6f718efa2e313c2490b299c3346ab2c')
  self.assertEqual(hashlib.sha256(Path(L.__file__).read_bytes()).hexdigest(),'98dbbc1d960bf9674735a17990be590e7e8f1516c125ab88c20231f24594547b')

 def test_preflight_full_manifest_includes_empty_artifact_but_is_not_ledger_pass(self):
  before=self.backend.capture_before(self.target)
  self.assertIn('host/'+b.ARTIFACT,before['files']);self.assertEqual(before['artifact'],self.expected)
  self.assertIn('host/project-p2vox/state.json',before['files']);self.assertFalse(self.qdir.exists())
  projection=self.backend.preflight(self.target);self.assertFalse(projection['completeLedgerVerified']);self.assertEqual(projection['effectsIssued'],0)
  self.assertNotIn('operation',json.dumps(before));self.assertNotIn('bytes": "',json.dumps(before));self.assertEqual(before['drainStatus'],'UNPROVEN')

 def test_real_atomic_move_preserves_inode_owner_mode_mtime_and_all_normal_files(self):
  before,receipt=self.moved();self.assertFalse(self.artifact.exists())
  moved=self.qdir/b.DESTINATION;self.assertEqual(moved.stat().st_ino,self.expected['ino']);self.assertEqual(moved.stat().st_size,0)
  self.assertEqual(stat.S_IMODE(self.qdir.stat().st_mode),0o700)
  for key in self.expected:
   if key!='ctimeNs':self.assertEqual(receipt['artifact'][key],self.expected[key])
  verified=self.backend.verify_after(self.target,before)
  self.assertEqual(verified['artifactLocation'],'QUARANTINE');self.assertTrue(verified['ledgerAttestation']['signatureVerification']);self.assertTrue(verified['ledgerAttestation']['oldGrantActive'])
  self.assertEqual(verified['ledgerAttestation']['originalUnknownCount'],2)
  self.assertEqual(verified['drainStatus'],'UNPROVEN')

 def test_real_inverse_relocation_restores_only_original_inode(self):
  before,receipt=self.moved();self.backend.restore(self.target,self.owner,before)
  result=self.backend.verify_restored(self.target,before,self.owner)
  self.assertEqual(result['artifactLocation'],'SOURCE');self.assertEqual(self.artifact.stat().st_ino,self.expected['ino']);self.assertFalse((self.qdir/b.DESTINATION).exists())

 def test_post_success_inverse_uses_fresh_normal_baseline(self):
  old,_=self.moved();self.backend.verify_after(self.target,old)
  path=self.store/'state.json';v=L.parse(path.read_bytes());v['revision']+=1;path.write_bytes(f.raw(v))
  fresh=self.backend.capture_inverse_before(self.target,self.owner)
  self.assertNotEqual(fresh['files']['host/state.json'],old['files']['host/state.json'])
  normal=path.read_bytes();self.backend.restore(self.target,self.owner,fresh)
  self.backend.verify_restored(self.target,fresh,self.owner);self.assertEqual(path.read_bytes(),normal)

 def test_original_metadata_or_nonzero_artifact_drift_refused(self):
  self.artifact.write_bytes(b'not empty')
  with self.assertRaises(b.Refused):self.backend.capture_before(self.target)

 def test_other_next_reclaim_or_unregistered_directory_refused(self):
  for name,folder in [('.next-foreign',False),('.reclaim-foreign',False),('project-foreign',True)]:
   p=self.store/name
   if folder:p.mkdir(mode=0o700)
   else:p.write_bytes(b'')
   with self.assertRaises(Exception):self.backend.capture_before(self.target)
   if folder:p.rmdir()
   else:p.unlink()

 def test_missing_or_replaced_original_inode_refused(self):
  self.artifact.unlink()
  with self.assertRaises(b.Refused):self.backend.capture_before(self.target)
  self.artifact.write_bytes(b'');self.artifact.chmod(0o600)
  with self.assertRaises(b.Refused):self.backend.capture_before(self.target)

 def test_symlink_hardlink_and_wrong_mode_refused(self):
  self.artifact.chmod(0o644)
  with self.assertRaises(b.Refused):self.backend.capture_before(self.target)
  self.artifact.chmod(0o600);extra=self.tmp/'hardlink';os.link(self.artifact,extra)
  with self.assertRaises(b.Refused):self.backend.capture_before(self.target)
  extra.unlink();self.artifact.unlink();self.artifact.symlink_to(self.store/'state.json')
  with self.assertRaises((b.Refused,OSError)):self.backend.capture_before(self.target)

 def test_mutation_requires_owned_frozen_singleton(self):
  before=self.backend.capture_before(self.target)
  with self.assertRaisesRegex(b.Refused,'OWNED_FROZEN_SINGLETON_REQUIRED'):self.backend.quarantine(self.target,self.owner,before)
  self.freeze();self.observation['members'].append(99)
  with self.assertRaises(b.Refused):self.backend.quarantine(self.target,self.owner,before)
  self.assertTrue(self.artifact.exists());self.assertFalse(self.qdir.exists())

 def test_destination_conflict_never_overwrites(self):
  before=self.backend.capture_before(self.target);self.freeze();self.qdir.mkdir(mode=0o700);dest=self.qdir/b.DESTINATION;dest.write_bytes(b'foreign')
  with self.assertRaises(b.Refused):self.backend.quarantine(self.target,self.owner,before)
  self.assertEqual(dest.read_bytes(),b'foreign');self.assertTrue(self.artifact.exists())

 def test_real_noreplace_syscall_refuses_existing_destination(self):
  self.qdir.mkdir(mode=0o700);dest=self.qdir/b.DESTINATION;dest.write_bytes(b'foreign')
  a=os.open(self.store,os.O_RDONLY|os.O_DIRECTORY);z=os.open(self.qdir,os.O_RDONLY|os.O_DIRECTORY)
  try:
   with self.assertRaisesRegex(b.Refused,'RELOCATION_DESTINATION_EXISTS'):b._rename_noreplace(a,b.ARTIFACT,z,b.DESTINATION)
  finally:os.close(a);os.close(z)
  self.assertTrue(self.artifact.exists());self.assertEqual(dest.read_bytes(),b'foreign')

 def test_lost_reply_after_rename_is_observed_and_not_relocated_again(self):
  before=self.backend.capture_before(self.target);self.freeze()
  real_sync=b.os.fsync;calls=[]
  def fail_after_directory_creation(fd):
   calls.append(fd)
   if len(calls)==2:raise OSError('synthetic lost reply')
   real_sync(fd)
  with patch.object(b.os,'fsync',side_effect=fail_after_directory_creation):
   with self.assertRaises(OSError):self.backend.quarantine(self.target,self.owner,before)
  self.assertEqual(self.backend.inspect_artifact(self.target,self.owner)['location'],'QUARANTINE')
  with self.assertRaises(b.Refused):self.backend.quarantine(self.target,self.owner,before)
  self.assertTrue(self.observation['frozen']);self.assertEqual(self.observation['fenceOwner'],self.owner)

 def test_inverse_requires_persisted_postrename_ctime_receipt(self):
  before,receipt=self.moved();del before['expectedQuarantinedArtifact']
  with self.assertRaisesRegex(b.Refused,'QUARANTINE_RECEIPT_METADATA_REQUIRED'):self.backend.restore(self.target,self.owner,before)
  before['expectedQuarantinedArtifact']={**receipt['artifact'],'ctimeNs':'1'}
  with self.assertRaises(b.Refused):self.backend.restore(self.target,self.owner,before)
  self.assertFalse(self.artifact.exists())

 def test_inverse_ctime_is_rechecked_at_last_syscall_boundary(self):
  before,_=self.moved();original=b._artifact_at;calls=[]
  def drift(fd,name):
   row=original(fd,name)
   if name==b.DESTINATION:
    calls.append(name)
    if len(calls)==2:return {**row,'ctimeNs':str(int(row['ctimeNs'])+1)}
   return row
  with patch.object(b,'_artifact_at',side_effect=drift):
   with self.assertRaisesRegex(b.Refused,'RELOCATION_LAST_IDENTITY_DRIFT'):self.backend.restore(self.target,self.owner,before)
  self.assertFalse(self.artifact.exists());self.assertTrue((self.qdir/b.DESTINATION).exists())

 def test_effect_admission_expiring_after_full_scan_refuses_last_syscall(self):
  before=self.backend.capture_before(self.target);self.freeze();calls=[]
  def admission(operation,target):
   if operation=='quarantine':
    calls.append(operation)
    if len(calls)==2:raise b.Refused('NATIVE_EFFECT_DEADLINE_EXPIRED')
  self.cap.require=admission
  with patch.object(b,'_rename_noreplace',side_effect=AssertionError('expired effect reached rename')):
   with self.assertRaisesRegex(b.Refused,'NATIVE_EFFECT_DEADLINE_EXPIRED'):self.backend.quarantine(self.target,self.owner,before)
  self.assertEqual(len(calls),2);self.assertTrue(self.artifact.exists());self.assertFalse((self.qdir/b.DESTINATION).exists())
  self.assertTrue(self.observation['frozen']);self.assertEqual(self.observation['fenceOwner'],self.owner)

 def test_normal_file_bytes_or_metadata_drift_blocks_after_and_inverse(self):
  before,_=self.moved();path=self.store/'state.json';v=L.parse(path.read_bytes());v['revision']+=1;path.write_bytes(f.raw(v))
  with self.assertRaisesRegex(b.Refused,'COMMITTED_LEDGER_OR_REGISTRATION_CHANGED'):self.backend.verify_after(self.target,before)
  with self.assertRaises(b.Refused):self.backend.restore(self.target,self.owner,before)

 def test_post_move_uses_unchanged_real_reader_not_filtered_temp_subset(self):
  before,_=self.moved();p=self.store/'.next-extra';p.write_bytes(b'')
  with self.assertRaisesRegex(L.Refused,'TEMPORARY_STORE_FILE_PRESENT'):self.backend.verify_after(self.target,before)

 def test_forbidden_signal_and_pidfd_apis_always_refuse(self):
  for operation in (self.backend.open_pidfd,self.backend.send_pidfd_sigkill):
   with self.assertRaisesRegex(b.Refused,'SIGNAL_AND_RESTART_FORBIDDEN'):operation(self.target)

class HandleScanTests(unittest.TestCase):
 def proc(self,root,pid,*,fd=None,mapping=None):
  p=root/str(pid);p.mkdir();(p/'fd').mkdir();(p/'stat').write_text(str(pid)+' (fixture) '+' '.join(['S']+['0']*18+['123']))
  (p/'maps').write_text(mapping or '')
  if fd:(p/'fd'/'3').symlink_to(fd)
 def test_actual_target_app_readonly_fd_is_not_exempt(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);artifact=root/'artifact';artifact.write_bytes(b'');s=artifact.stat();self.proc(root,1442662,fd=artifact)
   with self.assertRaisesRegex(b.Refused,'ARTIFACT_OPEN_HANDLE_PRESENT'):b.scan_artifact_handles((s.st_dev,s.st_ino),root)
 def test_even_readonly_mapping_is_refused(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);self.proc(root,1442662,mapping='1000-2000 r--p 00000000 08:01 42 synthetic\n')
   with self.assertRaisesRegex(b.Refused,'ARTIFACT_MAPPING_PRESENT'):b.scan_artifact_handles((os.makedev(8,1),42),root)
 def test_missing_process_is_harmless_but_inaccessible_scan_refuses(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);(root/'99').mkdir();b.scan_artifact_handles((1,2),root)
   with patch.object(Path,'read_text',side_effect=PermissionError('synthetic denied')):
    with self.assertRaisesRegex(b.Refused,'ARTIFACT_HANDLE_SCAN_UNPROVEN'):b.scan_artifact_handles((1,2),root)

if __name__=='__main__':unittest.main()
