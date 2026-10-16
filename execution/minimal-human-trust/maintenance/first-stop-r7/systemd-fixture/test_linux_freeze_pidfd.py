#!/usr/bin/python3
"""Real local disposable user-systemd/cgroup fixture, never a production adapter."""
import os,pathlib,subprocess,time,json,signal,hashlib,select,tempfile,shutil,stat
HERE=pathlib.Path(__file__).resolve().parent
assert os.geteuid()==1000
UNIT='codex-firststop-r7-fixture-'+str(os.getpid())+'.service'
RUNTIME=pathlib.Path('/run/user/1000/systemd/user')
DROP=RUNTIME/(UNIT+'.d')/'zz-first-stop-fixture.conf'
root=pathlib.Path(tempfile.mkdtemp(prefix='first-stop-r7-',dir=HERE));root.chmod(0o700)
BLOCK=root/'must-never-exist'
def run(args,check=True):
 return subprocess.run(args,capture_output=True,text=True,check=check,timeout=20)
def ctl(*args,check=True):return run(['/usr/bin/systemctl','--user',*args],check)
def properties():
 r=ctl('show',UNIT,'--property=MainPID','--property=ControlPID','--property=ControlGroup','--property=ActiveState','--property=SubState','--property=Restart','--property=NRestarts','--property=RefuseManualStart','--property=SendSIGKILL','--property=NeedDaemonReload')
 return dict(line.split('=',1) for line in r.stdout.splitlines() if '=' in line)
def wait(fn,seconds=10):
 end=time.monotonic()+seconds
 while not fn():
  if time.monotonic()>=end:raise RuntimeError('FIXTURE_TIMEOUT')
  time.sleep(.03)
def inventory():
 data={}
 for p in (root/'host').iterdir():
  s=p.lstat();assert stat.S_ISREG(s.st_mode) and s.st_nlink==1 and s.st_uid==1000 and stat.S_IMODE(s.st_mode)==0o600
  assert not p.name.startswith(('.next-','.reclaim'))
  raw=p.read_bytes();json.loads(raw)
  data[p.name]={'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw),'mode':stat.S_IMODE(s.st_mode)}
 return data
fd=None;started=False;result={}
try:
 run(['/usr/bin/systemd-run','--user','--unit='+UNIT,'--property=Restart=always','--property=RestartSec=100ms','--property=SendSIGKILL=no','--property=KillSignal=SIGTERM','--property=TimeoutStopSec=2s','--property=LimitCORE=0','/usr/bin/node',str(HERE/'child.mjs'),str(root),'create']);started=True
 wait(lambda:(root/'create-ready.json').exists())
 before=properties();pid=int(before['MainPID']);assert pid>1 and int(before['ControlPID'])==0 and before['Restart']=='always'
 group=pathlib.Path('/sys/fs/cgroup'+before['ControlGroup']);assert before['ControlGroup'].endswith('/'+UNIT)
 identity={'bootId':pathlib.Path('/proc/sys/kernel/random/boot_id').read_text().strip(),'pid':pid,'startTicks':pathlib.Path('/proc/'+str(pid)+'/stat').read_text().rsplit(')',1)[1].split()[19],'cgroup':before['ControlGroup']}
 assert set(map(int,(group/'cgroup.procs').read_text().split()))=={pid}
 fd=os.pidfd_open(pid)
 assert not DROP.exists();DROP.parent.mkdir(parents=True,mode=0o755)
 DROP.write_text('[Unit]\nRefuseManualStart=yes\nConditionPathExists='+str(BLOCK)+'\n[Service]\nRestart=no\n');DROP.chmod(0o644)
 ctl('daemon-reload');fenced=properties();assert fenced['Restart']=='no' and fenced['RefuseManualStart']=='yes' and fenced['NeedDaemonReload']=='no' and fenced['MainPID']==str(pid) and fenced['SendSIGKILL']=='no'
 ctl('freeze',UNIT)
 wait(lambda:'frozen 1' in (group/'cgroup.events').read_text())
 assert set(map(int,(group/'cgroup.procs').read_text().split()))=={pid}
 checkpoint=inventory();assert checkpoint.keys()=={'.lock','state.json'}
 original_state=(root/'host/state.json').read_bytes()
 # One signal, to a stable pidfd, while frozen. No systemctl stop/kill job:
 # systemd stop would thaw the service before its stop job.
 signal.pidfd_send_signal(fd,signal.SIGKILL);poller=select.poll();poller.register(fd,select.POLLIN);assert poller.poll(10000)
 wait(lambda:int(properties()['MainPID'])==0)
 after=properties();assert int(after['ControlPID'])==0 and after['NRestarts']==before['NRestarts']
 if group.exists():assert not (group/'cgroup.procs').read_text().strip()
 assert inventory()==checkpoint and (root/'host/state.json').read_bytes()==original_state
 blocked=ctl('start',UNIT,check=False);assert blocked.returncode!=0
 time.sleep(.3);assert int(properties()['MainPID'])==0
 # Recovery proof uses original R15 writer's actual dead-PID/start lock reclaim.
 run(['/usr/bin/node',str(HERE/'child.mjs'),str(root),'reopen'])
 assert (root/'host/state.json').read_bytes()==original_state and not (root/'host/.lock').exists()
 assert json.loads((root/'reopen-ready.json').read_text())['operations']==[{'id':'original-one','status':'UNKNOWN','resultHash':None},{'id':'original-two','status':'UNKNOWN','resultHash':None}]
 result={'schema':'r15.r7.real-user-systemd-freeze-pidfd-fixture.v1','result':'PASS_ISOLATED_ONLY','fixtureUnit':UNIT,'productionUnitTouched':False,'rootUsed':False,'fencePropertiesVerified':True,'cgroupFrozenVerified':True,'pidfdSignalCalls':1,'signal':'SIGKILL','frozenFilesByteAndModeUnchanged':True,'oldR15DeadWriterLockReclaim':'PASS','originalUnknownAndLeaseBytesPreserved':True,'automaticRestartObserved':False,'manualRestartBlocked':True,'allToolDrained':'UNPROVEN','upstreamWorkFinished':'UNPROVEN','productionPermissionCreated':False}
finally:
 if fd is not None:os.close(fd)
 if started:
  ctl('thaw',UNIT,check=False)
  if DROP.exists():DROP.unlink()
  if DROP.parent.exists():DROP.parent.rmdir()
  ctl('daemon-reload',check=False);ctl('stop',UNIT,check=False);ctl('reset-failed',UNIT,check=False)
 shutil.rmtree(root)
if result:
 with (HERE/'LINUX_FIXTURE_RESULT.json').open('x') as out:json.dump(result,out,indent=2);out.write('\n')
 print(json.dumps(result))
