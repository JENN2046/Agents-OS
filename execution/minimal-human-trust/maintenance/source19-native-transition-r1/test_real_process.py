"""Opt-in actual OLD Native process -> external pidfd -> repaired process.

Only /tmp state, generated fixture keys, exact public installed dependencies.
SIGSTOP is an isolated process stand-in, NOT production cgroup/systemd proof.
The other four roles are isolated adapters. No root, SSH or real key use.
"""
import base64,copy,hashlib,importlib.util,json,os,select,signal,stat,subprocess,tempfile,time,unittest
from pathlib import Path
from cryptography.hazmat.primitives import serialization
HERE=Path(__file__).parent
spec=importlib.util.spec_from_file_location('fake',HERE/'test_stop_transition.py');f=importlib.util.module_from_spec(spec);spec.loader.exec_module(f);s=f.s
NODE='/usr/bin/node';BASE=Path('/opt/r16/releases/r16-daily-20261015-r15-app-recovery-r6')
def proc_start(pid):
 try:return Path('/proc',str(pid),'stat').read_text().rsplit(')',1)[1].split()[19]
 except FileNotFoundError:return None
def line(process,seconds=3):
 if not select.select([process.stdout],[],[],seconds)[0]:raise AssertionError('ISOLATED_CHILD_RESPONSE_TIMEOUT')
 raw=process.stdout.readline()
 if not raw:raise AssertionError('ISOLATED_CHILD_EXIT:'+process.stderr.read()[:600])
 return json.loads(raw)
def verify(e,key):
 sig=base64.urlsafe_b64decode(e['signature']+'==');key.verify(sig,b'R16-SIGNED\0'+s.canonical(e['body']))
class DiskJournal:
 def __init__(self,p):self.p=p
 def read(self):return json.loads(self.p.read_text()) if self.p.exists() else None
 def write(self,v):
  tmp=self.p.with_suffix('.pending');fd=os.open(tmp,os.O_WRONLY|os.O_CREAT|os.O_TRUNC,0o600)
  try:os.write(fd,s.canonical(v));os.fsync(fd)
  finally:os.close(fd)
  tmp.replace(self.p)
class RealChildBackend(f.Backend):
 def __init__(self,root,child):
  super().__init__();self.root=root;self.child=child;self.term=0;self.snapshot=None;self.closed=0
  self.baseline[s.NATIVE].update(pid=child.pid,startTicks=proc_start(child.pid),bootId=Path('/proc/sys/kernel/random/boot_id').read_text().strip())
  (root/'isolated-fences').mkdir(mode=0o700)
 def check_target(self,t):s.need(t['pid']==self.child.pid and proc_start(t['pid'])==t['startTicks'],'REAL_PID_REUSE')
 def fence(self,u,h,p,b):
  super().fence(u,h,p,b);(self.root/'isolated-fences'/u).write_bytes(b)
 def verify_all_fences(self,h):
  super().verify_all_fences(h)
  for u in s.HOSTS:s.need((self.root/'isolated-fences'/u).read_bytes()==s.fence_bytes(h),'REAL_FENCE_BYTES')
 def verify_original_native_or_exited(self,t):
  if self.child.poll() is None:self.check_target(t)
 def observe_native(self,t):
  if self.child.poll() is not None:return {'exited':True,'members':[]}
  self.check_target(t);return {'exited':False,'members':[self.child.pid]}
 def graceful_native_once(self,t,deadline):
  self.check_target(t);self.term+=1;fd=os.pidfd_open(t['pid'])
  try:signal.pidfd_send_signal(fd,signal.SIGTERM)
  finally:os.close(fd)
  result=line(self.child);s.need(result['event']=='OLD_CLOSE_REFUSED' and result['writerStillPresent'],'ACTUAL_OLD_CLOSE_NOT_REFUSED');self.old_refusal=result
 def open_native_pidfd(self,t):self.check_target(t);return os.pidfd_open(t['pid'])
 def freeze_native(self,t,h):
  self.check_target(t);fd=os.pidfd_open(t['pid'])
  try:signal.pidfd_send_signal(fd,signal.SIGSTOP)
  finally:os.close(fd)
  end=time.monotonic()+2
  while 'State:\tT' not in Path('/proc',str(t['pid']),'status').read_text():
   s.need(time.monotonic()<end,'ISOLATED_FREEZE_TIMEOUT');time.sleep(.005)
  self.frozen=True
 def verify_frozen_singleton(self,t,h):
  self.check_target(t);s.need('State:\tT' in Path('/proc',str(t['pid']),'status').read_text(),'NOT_FROZEN')
 def checkpoint_native(self):
  fixture=json.loads((self.root/'ephemeral-test-keys.json').read_text());issuer=serialization.load_der_private_key(base64.b64decode(fixture['issuer']),None).public_key();verify(fixture['grant'],issuer)
  pub=fixture['grant']['body']['peers']['app']['publicKey'];app=serialization.load_der_public_key(base64.urlsafe_b64decode(pub+'=='));leases={}
  for op in fixture['ops']:
   verify(op,app);pid=op['body']['projectId'];state=json.loads((self.root/'dispatcher'/('project-'+pid)/'state.json').read_text())['data'];row=state['operations'][0];lease=state['active']['lease'];verify(lease,issuer)
   assert row['status']=='UNKNOWN' and row['hash']==s.digest(op) and op['body']['leaseHash']==s.digest(lease)
   assert op['body']['id']==s.UNKNOWN[pid]['id'] and op['body']['generation']==s.UNKNOWN[pid]['generation'] and op['body']['action']=='find_symbol'
   leases[pid]={'active':s.digest(lease),'closing':s.digest(state['closing']) if state.get('closing') else None,'rows':state['operations']}
  files={}
  for scope in ['dispatcher','host','db']:
   for p in sorted((self.root/scope).rglob('*')):
    if not p.is_file():continue
    a=p.lstat();assert stat.S_ISREG(a.st_mode) and a.st_nlink==1
    raw=p.read_bytes();z=p.lstat();assert (a.st_dev,a.st_ino,a.st_size,a.st_mtime_ns)==(z.st_dev,z.st_ino,z.st_size,z.st_mtime_ns)
    files[p.relative_to(self.root).as_posix()]={'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw),'mode':stat.S_IMODE(a.st_mode),'dev':a.st_dev,'ino':a.st_ino}
  assert 'db/project.sqlite' in files
  out=copy.deepcopy(self.c);reg=self.root/'dispatcher';out['nativeLedgerRegistration']={'directory':str(reg),'dev':reg.stat().st_dev,'ino':reg.stat().st_ino,'registryHash':s.digest({'testNamespace':str(reg)})};out.update(files=files,originalLeaseBindingsHash=s.digest(leases),registeredRootsHash=s.digest({n:{'dev':(self.root/n).stat().st_dev,'ino':(self.root/n).stat().st_ino}for n in ['dispatcher','host','db']}))
  return out
 def kill_native_pidfd_once(self,fd,t,deadline):
  self.check_target(t);s.need(int(time.time()*1000)<deadline,'EXPIRED_BEFORE_REAL_KILL');self.kills+=1;signal.pidfd_send_signal(fd,signal.SIGKILL);self.child.wait(timeout=3);self.stopped.add(s.NATIVE)
 def close_pidfd(self,fd):os.close(fd);self.closed+=1
@unittest.skipUnless(os.environ.get('R16_NATIVE_PHYSICAL_BACKEND')=='1','opt-in exact signed public base required; NOT CI coverage')
class RealProcess(unittest.TestCase):
 def test_real_old_refusal_external_stop_dead_lock_reclaim_then_new_local_shutdown(self):
  self.assertNotEqual(os.geteuid(),0)
  with tempfile.TemporaryDirectory(prefix='source19-native-transition-') as name:
   root=Path(name);child=subprocess.Popen([NODE,str(HERE/'fixtures/native-process.mjs'),'old',name],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
   try:
    ready=line(child);self.assertEqual(ready['event'],'READY');self.assertFalse(ready['hasNewShutdown'])
    b=RealChildBackend(root,child);p=f.plan(b);now=lambda:int(time.time()*1000);p.update(approvedAt=now(),expiresAt=now()+30000,recoveryDeadline=now()+60000)
    j=DiskJournal(root/'external-maintenance-journal.json');out=s.Driver(b,j,now).run(p)
    self.assertEqual(out['status'],'STOPPED_FENCED_NOT_DRAINED');self.assertEqual(b.term,1);self.assertEqual(b.kills,1);self.assertEqual(child.returncode,-signal.SIGKILL);self.assertEqual(b.closed,1)
    self.assertTrue((root/'host/native-writer.lock').exists(),'old crash writer metadata is NOT manually deleted')
    preserved={p:p.read_bytes() for p in (root/'dispatcher').rglob('state.json')}
    newer=subprocess.run([NODE,str(HERE/'fixtures/native-process.mjs'),'new',name],capture_output=True,text=True,timeout=10)
    self.assertEqual(newer.returncode,0,newer.stderr[:1200]);closed=json.loads(newer.stdout);self.assertEqual(closed['event'],'NEW_LOCAL_CLOSED');self.assertEqual(closed['firstStopProof'],'NOT_PROVEN');self.assertEqual(closed['retainedHistory'],2);self.assertTrue(closed['writerReleased'])
    self.assertFalse((root/'db/project.sqlite.r16-writer.lock').exists());self.assertFalse((root/'host/native-writer.lock').exists())
    for path,raw in preserved.items():
     before=json.loads(raw)['data'];after=json.loads(path.read_bytes())['data']
     if 'role' in before:
      for field in ['active','pending','closing','operations','archives','stopped','lastGeneration','grant']:self.assertEqual(after.get(field),before.get(field),'original business binding '+field+' unchanged; normal startup fresh challenge is lifecycle metadata')
    self.assertEqual(s.Driver(b,j,now).run(p)['status'],'RECOVERY_REQUIRED_READBACK_ONLY','after independently authorized new start old frozen proof is no longer reusable')
   finally:
    if child.poll() is None:child.kill();child.wait(timeout=3)
    child.stdout.close();child.stderr.close()
if __name__=='__main__':unittest.main()
