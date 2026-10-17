"""Only disposable-user files. OS metadata adapter maps this fixture owner to root."""
import copy,hashlib,importlib.util,os,stat,subprocess,sys,tempfile,types,unittest
from pathlib import Path
from unittest.mock import patch
P=Path(__file__).with_name('cache-cleanup.py');sp=importlib.util.spec_from_file_location('r9_cache_test',P);m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m)
class Crash(Exception):pass
class Tests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.base=Path(self.tmp.name);self.lists=self.base/'lists';self.lists.mkdir();self.journal=self.base/'journal';self.journal.mkdir();self.journal.chmod(0o700)
  for name in ('partial','auxfiles'):(self.lists/name).mkdir();(self.lists/name).chmod(0o755)
  (self.lists/'lock').write_bytes(b'');(self.lists/'lock').chmod(0o640)
  (self.lists/'mirrors.tencentyun.com_ubuntu_dists_noble-backports_InRelease').write_bytes(b'index-one');(self.lists/'mirrors.tencentyun.com_ubuntu_dists_noble-backports_main_binary-amd64_Packages').write_bytes(b'index-two')

  for p in self.lists.iterdir():
   if p.name not in ('lock','partial','auxfiles'):p.chmod(0o644)
  self.clock=1000;self.cap='c'*64;self.pendingBody={'test':'isolated-exact-native-pending'};self.pending=m.digest(self.pendingBody);self.authority={'schema':'r16.r9.native-install-confirmation.v1','pendingHash':self.pending,'nonce':'b'*32,'issuedAt':1000,'expiresAt':301000}
  self.realstat=os.stat;self.realfstat=os.fstat
  def rootmeta(s):
   class Proxy:
    def __getattr__(self,k):return getattr(s,k)
    st_uid=0
   return Proxy()
  def fake_directory(p):
   p=Path(p);self.assertTrue(p.is_relative_to(self.base));self.assertFalse(p.is_symlink());return os.open(p,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
  self.contexts=[patch.object(m,'LISTS',self.lists),patch.object(m,'JOURNAL',self.journal),patch.object(m,'root'),patch.object(m,'directory',side_effect=fake_directory),patch.object(m.os,'stat',side_effect=lambda *a,**k:rootmeta(self.realstat(*a,**k))),patch.object(m.os,'fstat',side_effect=lambda *a,**k:rootmeta(self.realfstat(*a,**k)))]
  for c in self.contexts:c.start();self.addCleanup(c.stop)
 def execute(self,expected,**kw):return m.execute(expected,self.authority,self.pending,self.cap,pending=self.pendingBody,clock=lambda:self.clock,**kw)
 def test_prepare_readonly_and_complete_hash_inventory_no_journal(self):
  before=sorted(self.lists.iterdir());p=m.prepare();self.assertEqual(len(p['files']),2);self.assertEqual(p['logicalBytes'],18);self.assertEqual(p['files']['mirrors.tencentyun.com_ubuntu_dists_noble-backports_InRelease']['sha256'],hashlib.sha256(b'index-one').hexdigest());self.assertEqual(sorted(self.lists.iterdir()),before);self.assertEqual(list(self.journal.iterdir()),[])
 def test_exact_delete_preserves_lock_directories_inode_and_durable_receipt(self):
  preserved={n:self.realstat(self.lists/n).st_ino for n in ('lock','partial','auxfiles')};p=m.prepare();result=self.execute(p);self.assertEqual(result['removedFiles'],2);self.assertEqual(set(os.listdir(self.lists)),set(preserved))
  for n,ino in preserved.items():self.assertEqual(self.realstat(self.lists/n).st_ino,ino)
  self.assertEqual(stat.S_IMODE(self.realstat(self.journal/self.cap).st_mode),0o700);self.assertTrue((self.journal/self.cap/'COMPLETED.json').exists())
 def test_changed_bytes_same_length_refuses_without_effect_or_intent(self):
  p=m.prepare();(self.lists/'mirrors.tencentyun.com_ubuntu_dists_noble-backports_InRelease').write_bytes(b'INDEX-ONE')
  with self.assertRaisesRegex(m.Refused,'INVENTORY_CHANGED'):self.execute(p)
  self.assertEqual(list(self.journal.iterdir()),[]);self.assertEqual(len(m.prepare()['files']),2)
 def test_extra_file_foreign_mode_symlink_hardlink_refuses(self):
  p=m.prepare();x=self.lists/'bad'
  for kind in ('mode','symlink','hardlink'):
   if kind=='mode':x.write_bytes(b'bad');x.chmod(0o666)
   elif kind=='symlink':x.symlink_to('lock')
   else:os.link(self.lists/'mirrors.tencentyun.com_ubuntu_dists_noble-backports_InRelease',x)
   with self.assertRaises((m.Refused,OSError)):self.execute(p)
   x.unlink()
  self.assertEqual(len(m.prepare()['files']),2)
 def test_expiry_before_effect_and_after_delete_intent(self):
  p=m.prepare();self.clock=301000
  with self.assertRaisesRegex(m.Refused,'EXPIRED'):self.execute(p)
  self.assertTrue((self.lists/'mirrors.tencentyun.com_ubuntu_dists_noble-backports_InRelease').exists());self.clock=1000
  def expiry(point):
   if point=='delete-intent':self.clock=301000
  with self.assertRaisesRegex(m.Refused,'EXPIRED'):self.execute(p,fault=expiry)
  self.assertEqual(len(m.prepare()['files']),2);self.assertFalse((self.journal/self.cap/'COMPLETED.json').exists())
 def test_crash_after_unlink_preserves_unknown_and_never_replays(self):
  p=m.prepare()
  def crash(point):
   if point=='delete-effect':raise Crash()
  with self.assertRaises(Crash):self.execute(p,fault=crash)
  self.assertEqual(len(m.prepare()['files']),1)
  with self.assertRaises(m.Refused):self.execute(p)
  p2=m.prepare()
  with self.assertRaisesRegex(m.Refused,'PRIOR_ATTEMPT'):self.execute(p2)
  self.assertEqual(len(m.prepare()['files']),1)
 def test_last_inode_change_after_durable_intent_refuses(self):
  p=m.prepare()
  def drift(point):
   if point=='delete-intent':
    n=sorted(p['files'])[0];(self.lists/n).unlink();(self.lists/n).write_bytes(b'changed');(self.lists/n).chmod(0o644)
  with self.assertRaisesRegex(m.Refused,'LAST_INODE'):self.execute(p,fault=drift)
  self.assertEqual(len(m.prepare()['files']),2)
 def test_budget_uses_bavail_and_allocated_not_reserved_blocks(self):
  p=m.prepare();fs=types.SimpleNamespace(f_bavail=10,f_bfree=10**12,f_frsize=4096)
  with patch.object(m.os,'statvfs',return_value=fs):
   with self.assertRaisesRegex(m.Refused,'INSUFFICIENT_UNRESERVED'):m.space_budget(p,1,1,filesystem_paths=[self.base])
  fs.f_bavail=100000
  with patch.object(m.os,'statvfs',return_value=fs):
   b=m.space_budget(p,100,200,filesystem_paths=[self.base]);self.assertEqual(b['availableBytes'],409600000);self.assertFalse(b['usesRootReservedBlocks']);self.assertEqual(b['allocatedCleanableBytes'],p['allocatedBytes'])
 def test_projected_freed_blocks_are_not_credited_after_cleanup(self):
  p=m.prepare();fs=types.SimpleNamespace(f_bavail=0,f_frsize=4096)
  with patch.object(m.os,'statvfs',return_value=fs),patch.object(m,'RESERVE',p['allocatedBytes']):
   m.space_budget(p,0,0,filesystem_paths=[self.base])
   with self.assertRaisesRegex(m.Refused,'INSUFFICIENT_UNRESERVED'):m.space_budget(p,0,0,filesystem_paths=[self.base],credit_cleanup=False)
 def test_unrelated_root_owned_regular_file_is_not_an_apt_index(self):
  p=self.lists/'unrelated_public_file';p.write_bytes(b'not an apt index');p.chmod(0o644)
  with self.assertRaisesRegex(m.Refused,'UNREVIEWED_INDEX_NAME'):m.prepare()
  self.assertTrue(p.exists());self.assertEqual(list(self.journal.iterdir()),[])
 def test_native_wrong_hash_or_no_new_authority_refuses(self):
  p=m.prepare()
  for field,value in (('pendingHash','0'*64),('nonce','bad'),('expiresAt',301001)):
   a={**self.authority,field:value}
   with self.assertRaises(m.Refused):m.execute(p,a,self.pending,self.cap,pending=self.pendingBody,clock=lambda:self.clock)
  self.assertEqual(list(self.journal.iterdir()),[])
 def test_prior_attempt_is_rejected_by_readonly_preflight(self):
  m.assert_fresh(self.cap);d=self.journal/self.cap;d.mkdir(0o700)
  with self.assertRaisesRegex(m.Refused,'PRIOR_ATTEMPT'):m.assert_fresh(self.cap)
  self.assertEqual(list(d.iterdir()),[]);self.assertEqual(len(m.prepare()['files']),2)
 def test_actual_nonroot_fixture_uid_is_refused_without_metadata_adapter(self):
  with patch.object(m.os,'fstat',side_effect=self.realfstat),patch.object(m.os,'stat',side_effect=self.realstat):
   fd=os.open(self.lists,os.O_RDONLY|os.O_DIRECTORY)
   try:
    with self.assertRaisesRegex(m.Refused,'METADATA_REFUSED'):m.read_at(fd,'mirrors.tencentyun.com_ubuntu_dists_noble-backports_InRelease')
   finally:os.close(fd)
 def test_real_independent_posix_lock_holder_blocks_cleanup(self):
  p=m.prepare();script='import fcntl,sys; f=open(sys.argv[1],"r+b"); fcntl.lockf(f,fcntl.LOCK_EX); print("LOCKED",flush=True); sys.stdin.buffer.read(1)'
  child=subprocess.Popen([sys.executable,'-I','-B','-c',script,str(self.lists/'lock')],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
  try:
   self.assertEqual(child.stdout.readline(),b'LOCKED\n')
   with self.assertRaises(BlockingIOError):self.execute(p)
   self.assertEqual(list(self.journal.iterdir()),[]);self.assertEqual(len(m.prepare()['files']),2)
  finally:
   child.communicate(input=b'x',timeout=5)
  self.assertEqual(child.returncode,0)
 def test_posix_apt_lock_contention_precedes_any_journal(self):
  p=m.prepare()
  with patch.object(m.fcntl,'lockf',side_effect=BlockingIOError()):
   with self.assertRaises(BlockingIOError):self.execute(p)
  self.assertEqual(list(self.journal.iterdir()),[])
if __name__=='__main__':unittest.main()
