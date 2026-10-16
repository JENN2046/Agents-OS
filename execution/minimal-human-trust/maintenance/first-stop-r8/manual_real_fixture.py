"""Real disposable user service through the R8 driver and LinuxBackend.

Unit/kernel/source namespace translation is explicit test injection, never a
production admission. Original R15 ProtectedStore, real signed synthetic state,
real freeze, pidfd SIGKILL and dead-writer reclaim; no root/provider/network.
Run manually on Jenn's user-systemd host. CI does not run this OS fixture.
"""
import copy,json,os,select,shutil,signal,stat,subprocess,sys,tempfile,time
from pathlib import Path
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE))
import linux_backend as lb
import stop_driver as d
import ledger_checkpoint as ledger
import test_ledger_checkpoint as fixture
BASE=Path('/home/jenn/AGENTS_OS_Workspace/ops/g1d-native-recovery-reconnect-20261014-r1/r15-backport/first-stop-r8-validation')

def run():
 assert os.geteuid()==1000
 BASE.mkdir(mode=0o755,exist_ok=True)
 unit='codex-first-stop-r8-integrated-'+str(os.getpid())+'.service'
 root=Path(tempfile.mkdtemp(prefix='isolated-r8-',dir=BASE));root.chmod(0o700)
 drop=Path('/run/user/1000/systemd/user')/(unit+'.d')/'92-r16-first-stop-r8.conf'
 def ctl(*args,check=True):
  return subprocess.run(['/usr/bin/systemctl','--user',*args],capture_output=True,check=check,timeout=15)
 def props():
  raw=ctl('show',unit,'--property='+','.join(lb.PROPERTIES)).stdout.decode()
  return dict(x.split('=',1) for x in raw.splitlines() if '=' in x)
 def wait(fn):
  end=time.monotonic()+10
  while not fn():
   assert time.monotonic()<end;time.sleep(.03)
 child=root/'child.mjs';started=False;backend=None;result=None
 try:
  c,t,pub,pins,_,_=fixture.fixture()
  for name,row in c['files'].items():
   if name.endswith('/.lock'):continue
   dest=root/name;dest.parent.mkdir(parents=True,exist_ok=True,mode=0o700);dest.write_bytes(row['bytes']);dest.chmod(0o600)
  for folder in (root/'host').rglob('*'):
   if folder.is_dir():folder.chmod(0o700)
  (root/'host').chmod(0o700)
  child.write_text("import fs from 'node:fs';\nimport {ProtectedStore} from '/opt/r16/releases/r16-daily-20261012-r15/src/lease-core.mjs';\nconst [root,mode]=process.argv.slice(2);\nlet stores;try{stores=['host','host/project-p2vox','host/project-pmog2'].map(x=>new ProtectedStore({directory:root+'/'+x,create:false}));}catch(e){fs.writeFileSync(root+'/start-error',String(e.code||e.message));process.exit(78);}\nfs.writeFileSync(root+'/'+mode+'-ready','READY');\nif(mode==='reopen'){for(const s of stores)s.close();process.exit(0);}\nsetInterval(()=>{},1000);\n")
  subprocess.run(['/usr/bin/systemd-run','--user','--unit='+unit,'--property=Restart=no','--property=SendSIGKILL=no','--property=KillSignal=SIGTERM','--property=LimitCORE=0','/usr/bin/node',str(child),str(root),'start'],capture_output=True,check=True,timeout=15);started=True
  wait(lambda:(root/'start-ready').exists() or (root/'start-error').exists());assert not (root/'start-error').exists(),(root/'start-error').read_text() if (root/'start-error').exists() else '';before=props();pid=int(before['MainPID']);group=before['ControlGroup']
  assert [int(x) for x in Path('/sys/fs/cgroup'+group+'/cgroup.procs').read_text().split()]==[pid]
  target={**t,'pid':pid,'startTicks':Path('/proc/'+str(pid)+'/stat').read_text().rsplit(')',1)[1].split()[19],
          'bootId':Path('/proc/sys/kernel/random/boot_id').read_text().strip(),'invocationId':before['InvocationID'],'nRestarts':int(before['NRestarts']),'sourceHashes':d.SOURCE_HASHES}
  paths=lb.Paths(state=root/'root-state',fence=root/'protected-dropin'/'92-r16-first-stop-r8.conf',condition=root/'blocked'/'never-exists')
  class System(lb.LinuxSystem):
   isolated=True;owner_uid=1000
   def require_root(self):assert os.geteuid()==1000
   def source_read(self,path):
    if path==lb.LAUNCHER:path=lb.SOURCE/'deployment/cloud-trusted-launcher.mjs'
    return Path(path).read_bytes()
   def run(self,argv):
    if argv[0]=='/usr/bin/systemctl':
     args=[unit if x==lb.UNIT else x for x in argv[1:]]
     if args[0]=='daemon-reload':
      if paths.fence.exists():
       drop.parent.mkdir(mode=0o755,parents=True,exist_ok=True)
       if not drop.is_symlink():drop.symlink_to(paths.fence)
       assert drop.is_symlink() and drop.readlink()==paths.fence
      elif drop.is_symlink():drop.unlink()
     r=ctl(*args)
     if args[0]=='show':
      actual=dict(x.split('=',1) for x in r.stdout.decode().splitlines() if '=' in x)
      actual['Id']=lb.UNIT
      if str(drop) in actual['DropInPaths'].split():actual['DropInPaths']=actual['DropInPaths'].replace(str(drop),str(paths.fence))
      if actual['ControlGroup']==group:actual['ControlGroup']=lb.CGROUP
      return ''.join(k+'='+v+'\n' for k,v in actual.items()).encode()
     return r.stdout
    if argv[0]=='/usr/bin/busctl':
     escaped=''.join(ch if ch.isascii() and ch.isalnum() else '_'+format(ord(ch),'02x') for ch in unit)
     args=list(argv[1:]);args[0]='--user';args[args.index('/org/freedesktop/systemd1/unit/r16_2dapp_2eservice')]='/org/freedesktop/systemd1/unit/'+escaped
     return subprocess.run(['/usr/bin/busctl',*args],capture_output=True,check=True,timeout=10).stdout
    raise AssertionError(argv)
   def kernel_read(self,path,maximum=65536):
    if path.startswith('/sys/fs/cgroup'+lb.CGROUP):path='/sys/fs/cgroup'+group+path[len('/sys/fs/cgroup'+lb.CGROUP):]
    if path=='/proc/'+str(pid)+'/cgroup':
     assert Path(path).read_text().strip()=='0::'+group;return ('0::'+lb.CGROUP).encode()
    if path=='/proc/'+str(pid)+'/cmdline':
     actual=Path(path).read_bytes().split(b'\0');assert actual[:3]==[b'/usr/bin/node',str(child).encode(),str(root).encode()]
     return b'\0'.join(x.encode() for x in lb.ARGV)+b'\0'
    return super().kernel_read(path,maximum)
   def freezer_write(self,value):
    assert value in (b'0',b'1');fd=os.open('/sys/fs/cgroup'+group+'/cgroup.freeze',os.O_WRONLY|os.O_NOFOLLOW)
    try:assert os.write(fd,value)==1
    finally:os.close(fd)
   signals=0
   def pidfd_signal(self,fd):self.signals+=1;return super().pidfd_signal(fd)
  class Reader:
   def capture(self,target):
    files={}
    for path in sorted((root/'host').rglob('*')):
     if not path.is_file():continue
     s=path.lstat();files[str(path.relative_to(root))]={'bytes':path.read_bytes(),'regular':stat.S_ISREG(s.st_mode),'symlink':path.is_symlink(),'uid':s.st_uid,'nlink':s.st_nlink,'mode':stat.S_IMODE(s.st_mode)}
    value={'schema':'r16.source-app-durable-checkpoint.v1','completeRegisteredFileSet':True,'otherWriterPids':[],'files':files}
    value.update(ledger._validate(value,target,pub,100,ledger.digest(pub),ledger.digest(pub['grant']),pins));return value
  reader=Reader();initial=reader.capture(target);at=time.time_ns()//1000000
  approval={'schema':d.SCHEMA,'environment':'ISOLATED_TEST','approvalId':'synthetic-r8-real-kernel','allowNonGracefulOnce':True,'acceptUnprovenInflight':True,'acceptPossibleUpstreamContinuation':True,'drainStatus':'UNPROVEN','approvedAt':at,'deadline':at+300000,'target':target,**{k:initial[k] for k in ('expectedOriginalUnknown','expectedLeaseBindings','expectedSemanticBindingsDigest')}}
  class Admission:
   approval_hash=d.digest(approval);target_hash=d.digest(target)
   def require(self,operation,value=None):
    if value is not None:assert d.digest(value)==self.target_hash
  system=System();backend=lb.LinuxBackend(Admission(),reader,system=system,paths=paths);backend.environment='ISOLATED_TEST'
  journal=lb.RootJournal(backend.admission,system=system,paths=paths)
  with journal.locked():
   receipt=d.Driver(backend,journal,lambda:time.time_ns()//1000000).run(approval)
   assert receipt['status']=='CONTROLLED_CRASH_STOPPED_NOT_DRAINED',receipt
   assert journal.read()['signalAttemptConsumed'] and system.signals==1
   for _ in range(2):assert d.Driver(backend,journal,lambda:time.time_ns()//1000000).run(approval)['historicalReadOnly']
  assert system.signals==1;after=reader.capture(target)
  assert initial['files']==after['files'];assert props()['MainPID']=='0'
  assert ctl('start',unit,check=False).returncode!=0
  state_bytes={name:row['bytes'] for name,row in after['files'].items() if name.endswith('state.json')}
  subprocess.run(['/usr/bin/node',str(child),str(root),'reopen'],capture_output=True,check=True,timeout=15)
  assert all((root/name).read_bytes()==raw for name,raw in state_bytes.items())
  assert all(not (root/parent/'.lock').exists() for parent in ('host','host/project-p2vox','host/project-pmog2'))
  result={'schema':'r16.r8.real-isolated-integration.v1','result':'PASS_ISOLATED_ONLY','rootUsed':False,'productionUnitTouched':False,'fixtureUnit':unit,'actualR8DriverAndLinuxBackend':True,'realKernelFreeze':True,'pidfdSigkillCount':system.signals,'sameFrozenAllFileBytesAndModes':True,'signedSyntheticOriginalTwoUnknownAndLeaseBindings':True,'originalR15ProtectedStoreReopen':True,'repeatEntryDoesNotSignal':True,'manualRestartBlocked':True,'drainStatus':'UNPROVEN','productionAuthorityCreated':False}
 finally:
  if backend:
   for handle in list(backend.handles):backend.close_pidfd(handle)
  if started:
   # Fixture cleanup only; never a production recovery instruction.
   ctl('thaw',unit,check=False)
   if drop.is_symlink() or drop.exists():drop.unlink()
   if drop.parent.exists():drop.parent.rmdir()
   ctl('daemon-reload',check=False);ctl('stop',unit,check=False);ctl('reset-failed',unit,check=False)
  shutil.rmtree(root)
 if result:
  result['allDisposableResourcesCleaned']=True
  dest=Path('/home/jenn/Documents/Codex/2026-10-15/G1D-R15-FIRST-STOP-R8/REAL_INTEGRATION_RESULT.json')
  with dest.open('x') as f:json.dump(result,f,indent=2);f.write('\n')
  print(json.dumps(result))
if __name__=='__main__':run()
