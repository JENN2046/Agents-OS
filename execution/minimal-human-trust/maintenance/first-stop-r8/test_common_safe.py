"""Atomic publication crash tests on disposable files; UID injection only."""
import os,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE))
import common_safe as m
class Crash(BaseException):pass
class Tests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory(prefix='r8-immutable-');self.addCleanup(self.temp.cleanup)
  self.path=Path(self.temp.name)/'sealed.py';self.raw=b'print("inert synthetic fixture")\n'
  oldstat=Path.lstat;oldfstat=os.fstat
  def uid0(s):
   fields=list(s);fields[4]=0;return os.stat_result(fields)
  self.patches=[patch.object(m,'mkdir',lambda p:None),patch.object(m,'secure_read',lambda p,**kw:Path(p).read_bytes()),
   patch.object(Path,'lstat',lambda p:uid0(oldstat(p))),patch.object(m.os,'fstat',lambda fd:uid0(oldfstat(fd)))]
  for p in self.patches:p.start()
  self.addCleanup(lambda:[p.stop() for p in reversed(self.patches)])
 def test_partial_known_pending_prefix_completes_without_publishing_partial_final(self):
  pending=self.path.with_name('.'+self.path.name+'.'+m.sha(self.raw)+'.pending');pending.write_bytes(self.raw[:8]);pending.chmod(0o644)
  self.assertFalse(self.path.exists());m.immutable(self.path,self.raw,0o644)
  self.assertEqual(self.path.read_bytes(),self.raw);self.assertFalse(pending.exists())
 def test_link_before_unlink_crash_repairs_only_same_exact_inode_and_bytes(self):
  original=m.os.link
  def crash_after_link(*args,**kw):original(*args,**kw);raise Crash()
  with patch.object(m.os,'link',side_effect=crash_after_link):
   with self.assertRaises(Crash):m.immutable(self.path,self.raw,0o644)
  self.assertEqual(self.path.lstat().st_nlink,2);m.immutable(self.path,self.raw,0o644)
  self.assertEqual(self.path.lstat().st_nlink,1);self.assertEqual(self.path.read_bytes(),self.raw)
 def test_foreign_existing_bytes_and_foreign_pending_prefix_never_overwritten(self):
  self.path.write_bytes(b'foreign');self.path.chmod(0o644)
  with self.assertRaisesRegex(m.Refused,'IMMUTABLE_FILE_CONFLICT'):m.immutable(self.path,self.raw,0o644)
  self.assertEqual(self.path.read_bytes(),b'foreign');self.path.unlink()
  pending=self.path.with_name('.'+self.path.name+'.'+m.sha(self.raw)+'.pending');pending.write_bytes(b'foreign');pending.chmod(0o644)
  with self.assertRaisesRegex(m.Refused,'IMMUTABLE_PENDING_CONFLICT'):m.immutable(self.path,self.raw,0o644)
  self.assertFalse(self.path.exists())
if __name__=='__main__':unittest.main()
