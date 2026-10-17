"""Fixed five-role Linux adapter. No CLI, admission minting or generic signals.

Production composition is the separately frozen native entry. Tests inject a
private system/paths and are always labelled ISOLATED_TEST, never PRODUCTION.
The R8 protected-file primitives are reused, not its old App authority/target.
"""
from contextlib import contextmanager
from copy import deepcopy
from dataclasses import dataclass
import fcntl
import ctypes
import hashlib
import importlib.util
import json
import os
import pwd
from pathlib import Path
import select
import signal
import socket
import stat
import subprocess
import sys
import time

HERE=Path(__file__).resolve().parent
def load(name,file):
 if name in sys.modules:return sys.modules[name]
 if os.geteuid()==0:raise RuntimeError('SEALED_ROOT_IMPORT_REQUIRED')
 spec=importlib.util.spec_from_file_location(name,file);m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m
S=load('_source19_stop_contract',HERE/'stop_transition.py')
R8=load('_source19_protected_files',HERE.parent/'first-stop-r8/linux_backend.py')
need=S.need;Refused=S.Refused;digest=S.digest;canonical=S.canonical
LOCAL=S.LOCAL;CLOUD=S.CLOUD;HOSTS=S.HOSTS;NATIVE=S.NATIVE;RELAY=S.RELAY
STATE=Path('/var/lib/r16-maintenance/source19-native-transition-r1')
CONDITION=STATE/'never-start-implicitly'
SOURCE=Path('/opt/r16/releases/r16-daily-20261015-r15-app-recovery-r6')
TARGET=Path('/opt/r16/releases/'+S.TARGET_RELEASE)
BRIDGE=Path('/opt/r16/releases/r16-daily-20261012-r15')
ENV={'PATH':'/usr/bin:/bin','LANG':'C','LC_ALL':'C','SYSTEMD_PAGER':'cat','SYSTEMD_COLORS':'0'}
PROPS=('Id','LoadState','ActiveState','SubState','MainPID','ControlPID','ControlGroup','InvocationID','NRestarts','Restart','RefuseManualStart','DropInPaths','NeedDaemonReload','SendSIGKILL','KillSignal','Job','LimitCORE','User')
STATIC_PINS={
 'r16-owner.service':{'/usr/lib/r16-owner/authority/owner_daemon.py':'85da39438068cfc6b80f3c0743dee8fa920e3fa7c1ac0ba628f1a40e6f413e9b'},
 RELAY:{'/opt/r16/trust/link-runner.py':'73802291b157cb6f7c52e0844faaa59a3fc18f7e6b95296ab4ac9f168bfca24f'},
 'r16-bridge.service':{'/opt/r16/trust/cloud-trusted-launcher.mjs':'5e4963c4078636b4c1bd9de22e12589734bfecc5c77f452f2017009921ff6231',str(BRIDGE/'bridge/bridge-runner.mjs'):'ac3d043618b6bdec7170820f3baa2f9bfdc4a6035fcf12bc0caab86f643dc584'}}
VERSIONS={'app':'34731b300ccad9a1fbfd45b07422d847e8989d7e9dc052b0dda939cd99adb500','native':S.SOURCE_NATIVE}
SOURCE_FILES={'native':{'host/native-runner.mjs':'0f30ebe457764265b2b8dad630f1a68f6e7251911c94da8a48362c6a0bfe089c','host/workspace-dispatcher.mjs':'ba4ef78187a8701b97bd03461faed44771c4d71b8541681a6d573e3f35ed079c'},'app':{'app/app-runner.mjs':'feaf51d26f5ef56cdfe013b65fe3faef37f91bc26391835810deb655e51f14d7','app/workspace-host.mjs':'bfef60223b8fd186f2e96887b770678777bf99ff2a5c84a3c36273d8f172a6ab'}}
ARGV={NATIVE:('/usr/bin/node','/opt/r16/trust/trusted-launcher.mjs','/etc/r16/native-host.json'),RELAY:('/usr/bin/python3','-I','/opt/r16/trust/link-runner.py'),'r16-owner.service':('/usr/bin/python3','-I','/usr/lib/r16-owner/authority/owner_daemon.py')}

def sha(raw):return hashlib.sha256(raw).hexdigest()
def stamp(s):return(s.st_dev,s.st_ino,s.st_mode,s.st_uid,s.st_gid,s.st_nlink,s.st_size,s.st_mtime_ns,s.st_ctime_ns)
@dataclass(frozen=True)
class Paths:
 state:Path=STATE
 etc:Path=Path('/etc/systemd/system')
 condition:Path=CONDITION
 def fence(self,unit):need(unit in HOSTS,'FIXED_UNIT_REQUIRED');return self.etc/(unit+'.d')/'96-source19-native-transition-r1.conf'

class LinuxSystem:
 isolated=False;owner_uid=0
 def require_root(self,host):need(os.getuid()==os.geteuid()==0 and socket.gethostname()==host and host in(LOCAL,CLOUD),'FIXED_HOST_ROOT_REQUIRED')
 def now(self):return time.time_ns()//1000000
 def monotonic(self):return time.monotonic()
 def sleep(self,s):time.sleep(s)
 def run(self,argv):
  result=subprocess.run(tuple(argv),stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,env=ENV,timeout=10,check=False)
  need(result.returncode==0 and len(result.stdout)<=262144,'FIXED_OS_COMMAND_FAILED');return result.stdout
 def kernel(self,path,maximum=262144):
  fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
  try:raw=os.read(fd,maximum+1);need(len(raw)<=maximum,'KERNEL_METADATA_CAPACITY');return raw
  finally:os.close(fd)
 def group_members(self,unit):
  root=Path('/sys/fs/cgroup/system.slice')/unit
  if not root.exists():return []
  members=set()
  def denied(_):raise Refused('CGROUP_UNREADABLE')
  for directory,children,_ in os.walk(root,followlinks=False,onerror=denied):
   p=Path(directory);need(not p.is_symlink() and all(not(p/n).is_symlink()for n in children),'CGROUP_LINK')
   values=self.kernel(str(p/'cgroup.procs')).split();need(all(x.isdigit()and int(x)>1 for x in values),'CGROUP_CONTENT')
   members.update(map(int,values));need(len(members)<=8192,'CGROUP_CAPACITY')
  return sorted(members)
 def freezer(self,value):
  need(value in(b'0',b'1'),'FIXED_FREEZER_VALUE');fd=os.open('/sys/fs/cgroup/system.slice/'+NATIVE+'/cgroup.freeze',os.O_WRONLY|os.O_NOFOLLOW|os.O_CLOEXEC)
  try:need(os.write(fd,value)==1,'FREEZER_WRITE_UNCERTAIN')
  finally:os.close(fd)
 def pidfd_open(self,pid):return os.pidfd_open(pid,0)
 def pidfd_ready(self,fd):
  p=select.poll();p.register(fd,select.POLLIN|select.POLLHUP|select.POLLERR);rows=p.poll(0);need(all(not bits&(select.POLLNVAL|select.POLLERR)for _,bits in rows),'PIDFD_INVALID');return bool(rows)
 def pidfd_signal(self,fd,sig):need(sig in(signal.SIGTERM,signal.SIGKILL),'FIXED_SIGNAL_REQUIRED');signal.pidfd_send_signal(fd,sig,None,0)
 def pidfd_close(self,fd):os.close(fd)
 def process_exe(self,pid,executable):
  expected=Path(os.path.realpath(executable));cursor=Path('/')
  for part in expected.parts[1:-1]:
   cursor/=part;s=cursor.lstat();need(stat.S_ISDIR(s.st_mode)and s.st_uid==0 and not s.st_mode&0o022,'PROCESS_EXECUTABLE_PARENT_UNSAFE')
  named=expected.lstat();actual=os.stat('/proc/'+str(pid)+'/exe');need(os.readlink('/proc/'+str(pid)+'/exe')==str(expected)and stat.S_ISREG(named.st_mode)and named.st_uid==0 and not named.st_mode&0o7022 and stamp(named)==stamp(expected.lstat())and(actual.st_dev,actual.st_ino)==(named.st_dev,named.st_ino),'PROCESS_EXECUTABLE_DRIFT')
  return(str(expected),stamp(named))
 def user_uid(self,user):return pwd.getpwnam(user or'root').pw_uid
 def source_read(self,p):return R8.ProtectedFiles().read(p,maximum=16*1024*1024)

class GuardedFiles(R8.ProtectedFiles):
 def __init__(self,uid,guard):super().__init__(uid);self.guard=guard
 def directory(self,path,mode=0o700,create=False,allow_missing=False):
  p=Path(path);need(p.is_absolute(),'ABSOLUTE_PATH_REQUIRED');cursor=Path('/')
  for part in p.parts[1:]:
   cursor/=part
   if create and not cursor.exists():
    self.guard()
    try:cursor.mkdir(mode=mode)
    except FileExistsError:pass
   try:s=cursor.lstat()
   except FileNotFoundError:
    if allow_missing:return None
    raise
   need(stat.S_ISDIR(s.st_mode)and s.st_uid in(0,self.owner_uid)and not s.st_mode&0o022,'ROOT_DIRECTORY_UNSAFE')
  return p
 def read(self,path,**kwargs):
  p=Path(path)
  try:before=p.lstat()
  except FileNotFoundError:
   if kwargs.get('allow_missing'):return super().read(p,**kwargs)
   raise
  raw=super().read(p,**kwargs);need(stamp(before)==stamp(p.lstat()),'NAMED_ROOT_FILE_CHANGED');return raw
 def atomic(self,path,raw,*,mode=0o600,immutable=False):
  need(isinstance(raw,bytes),'ROOT_BYTES_REQUIRED');path=Path(path);self.directory(path.parent,mode=0o700 if mode==0o600 else 0o755,create=True)
  old=self.read(path,mode=mode,allow_missing=True)
  if old is not None and immutable:need(old==raw,'IMMUTABLE_FILE_CONFLICT');return
  pending=path.with_name('.'+path.name+'.'+sha(raw)+'.pending');self.guard()
  try:fd=os.open(pending,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,mode);at=0
  except FileExistsError:
   prefix=self.read(pending,mode=mode,maximum=max(len(raw),1));need(raw.startswith(prefix),'PENDING_BYTES_CONFLICT');self.guard();fd=os.open(pending,os.O_WRONLY|os.O_NOFOLLOW);at=len(prefix)
  try:
   while at<len(raw):self.guard();at+=os.pwrite(fd,raw[at:at+65536],at)
   self.guard();os.fchmod(fd,mode);os.fsync(fd)
  finally:os.close(fd)
  self.guard()
  if immutable:
   libc=ctypes.CDLL(None,use_errno=True)
   if libc.renameat2(-100,os.fsencode(pending),-100,os.fsencode(path),1):
    error=ctypes.get_errno()
    if error==17:need(self.read(path,mode=mode)==raw,'IMMUTABLE_FILE_CONFLICT')
    else:raise OSError(error,os.strerror(error))
  else:os.replace(pending,path)
  self.sync(path.parent)
 def remove_exact(self,path,raw,*,mode):
  self.guard();path=Path(path);actual=self.read(path,mode=mode);before=path.lstat();need(actual==raw,'EXACT_REMOVE_BYTES_CHANGED')
  self.guard();after=path.lstat();need(stamp(before)==stamp(after),'EXACT_REMOVE_IDENTITY_CHANGED');self.guard();path.unlink();self.sync(path.parent)

class FixedLinuxBackend:
 def __init__(self,admission,remote=None,checkpoint=None,*,system=None,paths=None,host=None,publication_guard=None):
  need(not isinstance(admission,(dict,bool))and callable(getattr(admission,'require',None)),'NATIVE_CAPABILITY_REQUIRED')
  self.admission=admission;self.system=LinuxSystem()if system is None else system
  isolated=getattr(self.system,'isolated',False)is True
  need(system is None or isolated,'ISOLATED_SYSTEM_REQUIRED');need(paths is None or isolated,'PRODUCTION_PATH_OVERRIDE_REFUSED')
  self.environment='ISOLATED_TEST'if isolated else'PRODUCTION';self.host=(host if isolated else socket.gethostname());need(self.host in(LOCAL,CLOUD),'FIXED_HOST_REQUIRED')
  self.paths=Paths()if paths is None else paths;self.remote=remote;self.checkpointer=checkpoint;self.handles={};self._active_hash=None;self._effect_scope='os-write';self.publication_guard=publication_guard
  self.files=GuardedFiles(self.system.owner_uid,lambda:self.require(self._active_hash,self._effect_scope))
 @contextmanager
 def write_scope(self,operation):
  previous=self._effect_scope;self._effect_scope=operation
  try:yield
  finally:self._effect_scope=previous
 def require(self,plan_hash,operation,target=None):
  self.system.require_root(self.host)
  need(self.admission.require(plan_hash,operation,target)is None,'OPAQUE_ADMISSION_REQUIRED')
  self._active_hash=plan_hash
 def _route(self,operation,unit,payload=None):
  need(HOSTS.get(unit)==CLOUD and self.host==LOCAL and self.remote is not None,'FIXED_REMOTE_REQUIRED')
  return self.remote.call(operation,unit,self._active_hash,payload or{})
 def _fence_bytes(self,h):return S.fence_bytes(h).replace(str(CONDITION).encode(),str(self.paths.condition).encode())
 def _props(self,unit):
  need(unit in HOSTS and HOSTS[unit]==self.host,'WRONG_ROLE_HOST');raw=self.system.run(('/usr/bin/systemctl','show',unit,'--property='+','.join(PROPS)))
  out={}
  for line in raw.decode('ascii').splitlines():
   need('='in line,'MANAGER_METADATA');k,v=line.split('=',1);need(k not in out,'MANAGER_DUPLICATE');out[k]=v
  need(set(out)==set(PROPS)and out['Id']==unit and out['LoadState']=='loaded','MANAGER_METADATA')
  need(out['KillSignal']=='15'and out['SendSIGKILL']=='no'and out['LimitCORE']=='0'and out['NeedDaemonReload']=='no','UNSAFE_MANAGER_POLICY');return out
 def _pid_start(self,pid):
  if not pid:return '0'
  try:
   raw=self.system.kernel('/proc/'+str(pid)+'/stat');end=raw.rfind(b')');need(end>0,'PROCESS_STAT_METADATA');parts=raw[end+2:].split();need(len(parts)>19 and parts[19].isdigit(),'PROCESS_STAT_METADATA');return parts[19].decode()
  except FileNotFoundError:return None
 def _start(self,pid,group):
  start=self._pid_start(pid)
  if start is not None and pid:need(self.system.kernel('/proc/'+str(pid)+'/cgroup').decode().strip()=='0::'+group,'PROCESS_CGROUP_DRIFT')
  return start
 def _process(self,unit,pid,group,user=None):
  if not pid:return ('0',None)
  start=self._start(pid,group);need(start is not None,'ROLE_PROCESS_DISAPPEARED')
  argv=tuple(x.decode()for x in self.system.kernel('/proc/'+str(pid)+'/cmdline').split(b'\0')if x)
  if unit in ARGV:need(argv==ARGV[unit],'ROLE_ARGV_DRIFT')
  elif unit in('r16-app.service','r16-bridge.service'):
   role='app'if unit=='r16-app.service'else'bridge';need(len(argv)==3 and argv[0]=='/opt/r16/runtime/node-v24.15.0/bin/node'and argv[1]=='/opt/r16/trust/cloud-trusted-launcher.mjs'and argv[2]=='/etc/r16-cloud/'+role+'-host.json','ROLE_ARGV_DRIFT')
  status=self.system.kernel('/proc/'+str(pid)+'/status').decode();uids=[line.split()[1:]for line in status.splitlines()if line.startswith('Uid:')];expected=0 if unit=='r16-owner.service'else 1000 if unit in(NATIVE,RELAY)else self.system.user_uid(user)
  need(len(uids)==1 and len(uids[0])==4 and all(x.isdigit()for x in uids[0]),'ROLE_UID_METADATA')
  if expected is not None:need(all(int(x)==expected for x in uids[0]),'ROLE_UID_DRIFT')
  executable=self.system.process_exe(pid,argv[0]);return(start,argv,executable)
 def _code(self,unit,phase='SOURCE'):
  if unit in STATIC_PINS:pins=STATIC_PINS[unit];version=None;selector_hash=None
  else:
   role='native'if unit==NATIVE else'app';selector='/etc/r16/native-host.json'if role=='native'else'/etc/r16-cloud/app-host.json'
   config=json.loads(self.system.source_read(selector));base=TARGET if role=='native'and phase=='TARGET'else SOURCE
   need(config.get('schema')=='r16.'+role+'-host.v1'and config.get('codeManifest')==str(base/(role+'-manifest.json')),'ROLE_SELECTOR_DRIFT')
   m=json.loads(self.system.source_read(config['codeManifest']));version=digest(m)
   expected=getattr(self.admission,'plan',{}).get('targetNativeVersion')if role=='native'and phase=='TARGET'else VERSIONS[role]
   need(m.get('schema')=='r16.runtime-code.v1'and m.get('role')==role and version==expected,'ROLE_MANIFEST_DRIFT')
   names=SOURCE_FILES[role]if phase!='TARGET'else {n:m['files'].get(n)for n in SOURCE_FILES[role]}
   pins={str(base/n):pin for n,pin in names.items()};pins['/opt/r16/trust/'+('trusted-launcher.mjs'if role=='native'else'cloud-trusted-launcher.mjs')]='4583ddd8c1fca94881b5a05919ae59a173743682ae6d121c05bc6ffd10885e27'if role=='native'else'5e4963c4078636b4c1bd9de22e12589734bfecc5c77f452f2017009921ff6231'
   selector_hash=digest(config)
  actual={p:sha(self.system.source_read(p))for p in pins};need(actual==pins,'ROLE_CODE_DRIFT');return actual,version,selector_hash
 def _effective(self,unit,p,h):
  raw=self.files.read(self.paths.fence(unit),mode=0o644,allow_missing=True)
  if raw is None:return False
  need(h and raw==self._fence_bytes(h),'FOREIGN_PERSISTENT_FENCE')
  need(not os.path.lexists(self.paths.condition),'FALSE_CONDITION_EXISTS')
  obj='/org/freedesktop/systemd1/unit/'+unit.replace('-','_2d').replace('.','_2e')
  c=json.loads(self.system.run(('/usr/bin/busctl','--system','--json=short','get-property','org.freedesktop.systemd1',obj,'org.freedesktop.systemd1.Unit','Conditions')))
  need(c.get('type')=='a(sbbsi)'and isinstance(c.get('data'),list),'CONDITION_METADATA')
  matching=[x for x in c['data']if isinstance(x,list)and len(x)==5 and x[:4]==['ConditionPathExists',False,False,str(self.paths.condition)]]
  need(len(matching)==1 and p['DropInPaths'].split()[-1:]==[str(self.paths.fence(unit))]and p['Restart']=='no'and p['RefuseManualStart']=='yes','FENCE_NOT_EFFECTIVE');return True
 def snapshot(self,unit,h=None,phase='SOURCE'):
  self.require(h,'inspect',{'unit':unit})
  if HOSTS[unit]!=self.host:return self._route('inspect',unit,{'phase':phase})
  for attempt in range(3):
   p=self._props(unit);group='/system.slice/'+unit;pid=int(p['MainPID']);control=int(p['ControlPID']);members=self.system.group_members(unit)
   need(p['ControlGroup']==group or(p['ControlGroup']==''and pid==control==0),'CGROUP_IDENTITY_DRIFT')
   main_before=self._process(unit,pid,group,p['User']);start=main_before[0];control_start=self._start(control,group);pins,version,selector_hash=self._code(unit,phase)
   main_after=self._process(unit,pid,group,p['User']);control_after=self._start(control,group);after=self._props(unit)
   if p!=after or members!=self.system.group_members(unit):need(attempt<2,'UNSTABLE_ROLE_INSTANCE');continue
   need(main_before==main_after and control_start==control_after,'PROCESS_INSTANCE_CHANGED_DURING_CAPTURE')
   need((not pid or pid in members and start is not None)and(not control or control in members and control_start is not None),'ROLE_PID_OUTSIDE_CGROUP')
   boot=self.system.kernel('/proc/sys/kernel/random/boot_id').decode().strip()
   return {'unit':unit,'host':self.host,'pid':pid,'mainPid':pid,'controlPid':control,'startTicks':start or'0','controlStartTicks':control_start or'0','bootId':boot,'invocationId':p['InvocationID'],'nRestarts':int(p['NRestarts']),'cgroup':group,'members':members,'active':p['ActiveState'],'sub':p['SubState'],'pendingJob':p['Job']not in('','0'),'codePins':pins,'nativeVersion':version if unit==NATIVE else None,'selectorHash':selector_hash,'ownedPersistentFence':self._effective(unit,p,h),'cgroupEmpty':not members,'phase':phase}
  raise Refused('UNSTABLE_ROLE_INSTANCE')
 def capture_original(self):return {u:self.snapshot(u,self._active_hash)for u in HOSTS}
 def verify_all_fences(self,h):
  for u in HOSTS:need(self.snapshot(u,h)['ownedPersistentFence'],'OWNED_FIVE_ROLE_FENCES_REQUIRED')
 def fence(self,unit,h,path,raw):
  self.require(h,'fence:'+unit,{'unit':unit});need(path==S.fence_path(unit)and raw==S.fence_bytes(h),'FIXED_FENCE_REQUIRED')
  if HOSTS[unit]!=self.host:return self._route('fence',unit)
  need(not os.path.lexists(self.paths.condition),'FALSE_CONDITION_EXISTS')
  self.files.directory(self.paths.state,create=True);self.files.atomic(self.paths.fence(unit),self._fence_bytes(h),mode=0o644,immutable=True)
  self.require(h,'daemon-reload');self.system.run(('/usr/bin/systemctl','daemon-reload'));need(self.snapshot(unit,h)['ownedPersistentFence'],'FENCE_NOT_EFFECTIVE')
 def _wait_stopped(self,unit,h,phase='SOURCE',seconds=30):
  end=self.system.monotonic()+seconds
  while True:
   row=self.snapshot(unit,h,phase)
   if row['mainPid']==row['controlPid']==0 and row['cgroupEmpty']and not row['pendingJob']:return row
   need(self.system.monotonic()<end,'GRACEFUL_STOP_UNCONFIRMED');self.system.sleep(.05)
 def graceful_stop(self,unit,h):
  self.require(h,'graceful:'+unit,{'unit':unit});need(unit!=NATIVE,'NATIVE_SEPARATE_ONCE_REQUIRED')
  if HOSTS[unit]!=self.host:return self._route('stop',unit)
  row=self.snapshot(unit,h);need(row['ownedPersistentFence']and not row['pendingJob'],'STOP_REQUIRES_FENCE_AND_IDLE_MANAGER')
  self.require(h,'graceful:'+unit);self.system.run(('/usr/bin/systemctl','stop','--no-block',unit));return self._wait_stopped(unit,h)
 def _assert_original(self,target,row,allow_exit=True):
  need(target.get('unit')==NATIVE and target.get('host')==LOCAL,'EXACT_NATIVE_TARGET_REQUIRED')
  need(all(row[k]==target[k]for k in('bootId','nRestarts','codePins','nativeVersion','selectorHash')),'ORIGINAL_NATIVE_CODE_OR_BOOT_DRIFT')
  exited=row['mainPid']==row['controlPid']==0 and row['cgroupEmpty']
  if exited:
   need(allow_exit and row['invocationId']in('',target['invocationId'])and self._pid_start(target['pid'])!=target['startTicks'],'ORIGINAL_NATIVE_EXIT_UNPROVEN')
  else:need(all(row[k]==target[k]for k in('pid','startTicks','invocationId','cgroup'))and row['controlPid']==0 and row['members']==[target['pid']],'NATIVE_INSTANCE_OR_SINGLETON_DRIFT')
  return exited
 def observe_native(self,target):
  row=self.snapshot(NATIVE,self._active_hash);return {'exited':self._assert_original(target,row),'members':row['members']}
 def verify_original_native_or_exited(self,target):self.observe_native(target)
 def open_native_pidfd(self,target):
  self.require(self._active_hash,'open-native-pidfd',target);need(not self.observe_native(target)['exited'],'NATIVE_ALREADY_EXITED');fd=self.system.pidfd_open(target['pid'])
  try:need(not self.observe_native(target)['exited']and not self.system.pidfd_ready(fd),'NATIVE_ALREADY_EXITED')
  except BaseException:self.system.pidfd_close(fd);raise
  self.handles[fd]={'target':deepcopy(target),'used':False};return fd
 def close_pidfd(self,fd):
  if fd in self.handles:self.system.pidfd_close(fd);del self.handles[fd]
 def graceful_native_once(self,target,deadline):
  self.require(self._active_hash,'graceful:'+NATIVE,target);fd=self.open_native_pidfd(target)
  try:
   need(self.system.now()<deadline,'PLAN_EXPIRED');self.require(self._active_hash,'graceful:'+NATIVE,target);self.system.pidfd_signal(fd,signal.SIGTERM)
   end=min(self.system.monotonic()+5,self.system.monotonic()+max(0,(deadline-self.system.now())/1000))
   while self.system.monotonic()<end:
    if self.observe_native(target)['exited']:return {'status':'OLD_NATIVE_GRACEFULLY_EXITED'}
    self.system.sleep(.05)
   return {'status':'OLD_NATIVE_STILL_RUNNING_NOT_DRAINED'}
  finally:self.close_pidfd(fd)
 def _freeze(self):
  prefix='/sys/fs/cgroup/system.slice/'+NATIVE;values=[]
  for name in('cgroup.freeze','cgroup.events'):
   try:values.append(self.system.kernel(prefix+'/'+name))
   except FileNotFoundError:values.append(None)
  if all(x is None for x in values):return False,False
  need(all(x is not None for x in values),'PARTIAL_FREEZER_METADATA')
  events=dict(line.split()for line in values[1].decode().splitlines());need(events.get('frozen')in('0','1')and values[0].strip()in(b'0',b'1'),'FREEZER_METADATA');return values[0].strip()==b'1',events['frozen']=='1'
 def freeze_native(self,target,h):
  self.require(h,'native-freeze',target);row=self.snapshot(NATIVE,h);self._assert_original(target,row,False);need(row['ownedPersistentFence'],'OWNED_FENCE_REQUIRED')
  requested,frozen=self._freeze();need(not(requested or frozen),'FOREIGN_OR_PRIOR_FREEZE')
  self.files.atomic(self.paths.state/'freeze-owner.json',canonical({'planHash':h,'nativeTargetHash':digest(target)}),immutable=True)
  self.require(h,'native-freeze',target);self.system.freezer(b'1');end=self.system.monotonic()+10
  while True:
   self._assert_original(target,self.snapshot(NATIVE,h),False);requested,frozen=self._freeze();need(requested,'FREEZE_REQUEST_LOST')
   if frozen:return
   need(self.system.monotonic()<end,'FREEZE_NOT_CONFIRMED');self.system.sleep(.05)
 def verify_frozen_singleton(self,target,h):
  self.require(h,'inspect',target);row=self.snapshot(NATIVE,h);self._assert_original(target,row,False);need(row['ownedPersistentFence']and self._freeze()==(True,True),'FROZEN_SINGLETON_REQUIRED')
  need(json.loads(self.files.read(self.paths.state/'freeze-owner.json',mode=0o600))=={'planHash':h,'nativeTargetHash':digest(target)},'FREEZE_OWNER_DRIFT')
 def assert_checkpoint_safe(self,h,target):
  self.require(h,'checkpoint',target)
  for unit in HOSTS:
   row=self.snapshot(unit,h);need(row['ownedPersistentFence']and not row['pendingJob'],'CHECKPOINT_FENCE_REQUIRED')
   if unit==NATIVE:
    if not self._assert_original(target,row):self.verify_frozen_singleton(target,h)
   else:need(row['mainPid']==row['controlPid']==0 and row['cgroupEmpty'],'OTHER_WRITER_ROLE_STILL_RUNNING')
 def assert_native_preflight_safe(self):
  need(self.host==LOCAL,'LOCAL_NATIVE_PREFLIGHT_ONLY');self.require(None,'native-preflight')
  row=self.snapshot(NATIVE,None);need(row['mainPid']>1 and row['controlPid']==0 and row['members']==[row['mainPid']]and not row['pendingJob']and row['active']=='active'and row['sub']=='running'and not row['ownedPersistentFence']and self._freeze()==(False,False),'LIVE_SOURCE_NATIVE_SINGLETON_REQUIRED')
  return None
 def assert_app_history_safe(self,h):
  need(self.host==CLOUD,'CLOUD_APP_HISTORY_ONLY')
  for u in('r16-app.service','r16-bridge.service'):
   row=self.snapshot(u,h)
   if h is not None:need(row['ownedPersistentFence']and row['mainPid']==row['controlPid']==0 and row['cgroupEmpty']and not row['pendingJob'],'APP_HISTORY_WRITERS_NOT_STOPPED')
  return None
 def checkpoint_native(self):
  need(self.checkpointer is not None,'COMPLETE_NATIVE_CHECKPOINTER_REQUIRED');target=self.admission.original_baseline[NATIVE]
  self.assert_checkpoint_safe(self._active_hash,target);value=self.checkpointer.capture(self._active_hash,target);self.assert_checkpoint_safe(self._active_hash,target);return value
 def kill_native_pidfd_once(self,fd,target,deadline):
  self.require(self._active_hash,'native-signal',target);item=self.handles.get(fd);need(item and not item['used']and item['target']==target,'PIDFD_ATTEMPT_CONSUMED')
  self.verify_frozen_singleton(target,self._active_hash);need(not self.system.pidfd_ready(fd)and self.system.now()<deadline,'SIGNAL_WINDOW_OR_INSTANCE_EXPIRED')
  item['used']=True;self.require(self._active_hash,'native-signal',target);need(self.system.now()<deadline,'SIGNAL_WINDOW_EXPIRED');self.system.pidfd_signal(fd,signal.SIGKILL)
  end=self.system.monotonic()+10
  while True:
   if self.system.pidfd_ready(fd)and self.observe_native(target)['exited']:return
   need(self.system.monotonic()<end,'NATIVE_EXIT_UNCONFIRMED');self.system.sleep(.05)
 def observe_all(self,baseline,h):
  rows={u:self.snapshot(u,h)for u in HOSTS}
  for u,row in rows.items():
   old=baseline[u];need(row['bootId']==old['bootId']and row['nRestarts']==old['nRestarts']and row['codePins']==old['codePins'],'OBSERVATION_BASELINE_DRIFT')
   need(row['mainPid']==row['controlPid']==0 and row['cgroupEmpty']and row['invocationId']in('',old['invocationId']),'ORIGINAL_INSTANCE_NOT_STOPPED')
  return rows

 def _publication(self,phase,h):
  need(phase in('FORWARD','SOURCE')and callable(self.publication_guard),'VERIFIED_PUBLICATION_READER_REQUIRED')
  self.require(h,'inspect');need(self.publication_guard(phase,h)is None,'OPAQUE_PUBLICATION_VERIFICATION_REQUIRED')
 def _phase(self,unit):
  if unit!=NATIVE:return 'SOURCE'
  selector=json.loads(self.system.source_read('/etc/r16/native-host.json')).get('codeManifest')
  if selector==str(SOURCE/'native-manifest.json'):return 'SOURCE'
  need(selector==str(TARGET/'native-manifest.json'),'NATIVE_SELECTOR_DRIFT');return 'TARGET'
 def _lifecycle_record(self,name):
  need(name.replace('-','').replace('.','').isalnum(),'FIXED_LIFECYCLE_NAME');return self.paths.state/'lifecycle'/(name+'.json')
 def _once(self,name,h,scope,before,fn):
  # This root audit is an effect ledger, never an authority or retry grant.
  self.require(h,scope);p=self._lifecycle_record(name);raw=self.files.read(p,mode=0o600,allow_missing=True)
  if raw is not None:
   record=R8.parse_json(raw);need(record.get('planHash')==h and record.get('scope')==scope,'LIFECYCLE_RECORD_CONFLICT')
   need(record.get('state')=='RETURNED','LIFECYCLE_EFFECT_UNKNOWN_READBACK_ONLY');return record['result']
  record={'schema':'r16.source19-native-transition.os-effect.v1','planHash':h,'scope':scope,'before':before,'state':'INTENT'}
  with self.write_scope(scope):self.files.atomic(p,canonical(record),immutable=True)
  self.require(h,scope);result=fn()
  record.update(state='RETURNED',result=result)
  with self.write_scope('journal-write'):self.files.atomic(p,canonical(record))
  return result
 def _remove_fence(self,unit,h,scope):
  self.require(h,scope,{'unit':unit});row=self.snapshot(unit,h,self._phase(unit));need(row['ownedPersistentFence']and row['mainPid']==row['controlPid']==0 and row['cgroupEmpty']and not row['pendingJob'],'UNFENCE_STOPPED_OWNED_ROLE_REQUIRED')
  with self.write_scope(scope):self.files.remove_exact(self.paths.fence(unit),self._fence_bytes(h),mode=0o644)
  self.require(h,scope);self.system.run(('/usr/bin/systemctl','daemon-reload'))
  need(not self.snapshot(unit,h,self._phase(unit))['ownedPersistentFence'],'UNFENCE_NOT_EFFECTIVE')
 def _thaw_empty_native(self,h):
  self.require(h,'thaw-native');row=self.snapshot(NATIVE,h,'TARGET');need(row['mainPid']==row['controlPid']==0 and row['cgroupEmpty']and row['ownedPersistentFence'],'THAW_REQUIRES_EMPTY_FENCED_NATIVE')
  requested,frozen=self._freeze()
  if not requested and not frozen:return
  need(json.loads(self.files.read(self.paths.state/'freeze-owner.json',mode=0o600))=={'planHash':h,'nativeTargetHash':self.admission.plan['nativeTargetHash']},'FREEZE_OWNER_DRIFT')
  self.require(h,'thaw-native');self.system.freezer(b'0');end=self.system.monotonic()+10
  while self._freeze()!=(False,False):
   need(self.system.monotonic()<end,'THAW_UNCONFIRMED');self.system.sleep(.05)
 def _running(self,unit,h,phase):
  end=self.system.monotonic()+30
  while True:
   row=self.snapshot(unit,h,phase)
   if row['mainPid']>0 and row['controlPid']==0 and row['active']=='active'and row['sub']=='running'and not row['pendingJob']:
    need(not row['ownedPersistentFence'],'STARTED_ROLE_STILL_FENCED')
    if unit==NATIVE:need(row['members']==[row['mainPid']],'NEW_NATIVE_NOT_SINGLETON')
    return row
   need(self.system.monotonic()<end,'ROLE_START_UNCONFIRMED');self.system.sleep(.05)
 def start_approved_role(self,unit,h,recovery=False):
  need(unit in HOSTS,'FIXED_UNIT_REQUIRED');scope=('restore:'if recovery else'activate:')+unit;self.require(h,scope,{'unit':unit})
  if HOSTS[unit]!=self.host:return self._route('restore'if recovery else'activate',unit)
  phase='SOURCE'if recovery or unit!=NATIVE else'TARGET';self._publication('SOURCE'if recovery else'FORWARD',h)
  before=self.snapshot(unit,h,phase);need(before['mainPid']==before['controlPid']==0 and before['cgroupEmpty']and before['ownedPersistentFence']and not before['pendingJob'],'START_REQUIRES_STOPPED_OWNED_FENCE')
  if recovery:
   old=self.admission.original_baseline[unit];need(unit not in(NATIVE,'r16-app.service')and old['mainPid']>0 and old['active']=='active','SOURCE_REOPEN_POLICY_REFUSED')
  def effect():
   self._publication('SOURCE'if recovery else'FORWARD',h)
   if unit==NATIVE:self._thaw_empty_native(h)
   self._remove_fence(unit,h,scope);self._publication('SOURCE'if recovery else'FORWARD',h);self.require(h,scope)
   self.system.run(('/usr/bin/systemctl','start','--no-block',unit));return self._running(unit,h,phase)
  row=self._once(('restore-'if recovery else'activate-')+unit,h,scope,before,effect)
  actual=self.snapshot(unit,h,phase);need(actual==row,'STARTED_INSTANCE_CHANGED');return actual
 def stop_activated_role(self,unit,h):
  scope='requiesce:'+unit;self.require(h,scope,{'unit':unit})
  if HOSTS[unit]!=self.host:return self._route('requiesce',unit)
  phase=self._phase(unit);before=self.snapshot(unit,h,phase)
  # Requiesce is legal only for this plan's possible activation, not an old PID.
  raw=self.files.read(self._lifecycle_record('activate-'+unit),mode=0o600,allow_missing=True)
  if raw is None:
   need(before['mainPid']==before['controlPid']==0 and before['cgroupEmpty']and before['ownedPersistentFence'],'UNRECORDED_RUNNING_ROLE_REFUSED');return before
  record=R8.parse_json(raw);need(record.get('planHash')==h and record.get('scope')=='activate:'+unit,'ACTIVATION_RECORD_DRIFT')
  if record.get('state')=='RETURNED'and before['mainPid']:
   old=record['result'];need(all(before[k]==old[k]for k in('pid','startTicks','bootId','invocationId','codePins','selectorHash')),'ACTIVATED_INSTANCE_DRIFT')
  def effect():
   # A new stop is constrained to this recorded service. Never a second KILL.
   with self.write_scope(scope):self.files.atomic(self.paths.fence(unit),self._fence_bytes(h),mode=0o644,immutable=True)
   self.require(h,scope);self.system.run(('/usr/bin/systemctl','daemon-reload'));current=self.snapshot(unit,h,phase);need(current['ownedPersistentFence'],'RECOVERY_FENCE_NOT_EFFECTIVE')
   if current['mainPid']or current['controlPid']or not current['cgroupEmpty']:
    self.require(h,scope);self.system.run(('/usr/bin/systemctl','stop','--no-block',unit))
   return self._wait_stopped(unit,h,phase)
  self._once('requiesce-'+unit,h,scope,before,effect);return self.snapshot(unit,h,phase)
 def activate_target(self,h):
  self._publication('FORWARD',h)
  for unit in('r16-owner.service','r16-bridge.service',RELAY,NATIVE,'r16-app.service'):self.start_approved_role(unit,h)
  return {'status':'OS_ACTIVE','planHash':h,'businessAcceptance':False,'globalExecution':'UNPROVEN'}
 def requiesce_target(self,h):
  for unit in('r16-app.service',NATIVE,RELAY,'r16-bridge.service','r16-owner.service'):self.stop_activated_role(unit,h)
  return {'status':'STOPPED_FENCED_NOT_DRAINED','planHash':h,'businessAcceptance':False,'globalExecution':'UNPROVEN'}
 def restore_stopped_source(self,h):
  self._publication('SOURCE',h)
  for unit in(NATIVE,'r16-app.service'):
   row=self.snapshot(unit,h,'SOURCE');need(row['mainPid']==row['controlPid']==0 and row['cgroupEmpty']and row['ownedPersistentFence'],'CRASHED_OR_BUSINESS_ROLE_REOPEN_REFUSED')
  for unit in('r16-owner.service','r16-bridge.service',RELAY):
   old=self.admission.original_baseline[unit]
   if old['mainPid']>0 and old['active']=='active':self.start_approved_role(unit,h,True)
  return {'status':'OS_ACTIVE','planHash':h,'nativeStopped':True,'appStopped':True,'businessAcceptance':False,'globalExecution':'UNPROVEN'}
 def expected_state(self,h,recovery=False):
  self._publication('SOURCE'if recovery else'FORWARD',h);rows={}
  for unit in HOSTS:
   row=self.snapshot(unit,h,'SOURCE'if recovery or unit!=NATIVE else'TARGET');rows[unit]=row
   expected_stopped=recovery and(unit in(NATIVE,'r16-app.service')or not(self.admission.original_baseline[unit]['mainPid']>0 and self.admission.original_baseline[unit]['active']=='active'))
   if expected_stopped:need(row['mainPid']==row['controlPid']==0 and row['cgroupEmpty']and row['ownedPersistentFence']and not row['pendingJob'],'EXPECTED_STOPPED_ROLE_UNPROVEN')
   else:need(row['mainPid']>0 and row['controlPid']==0 and row['active']=='active'and row['sub']=='running'and not row['ownedPersistentFence']and not row['pendingJob'],'EXPECTED_RUNNING_ROLE_UNPROVEN')
  return {'verified':True,'planHash':h,'nativeStopped':rows[NATIVE]['mainPid']==0,'nativeSelectorHash':rows[NATIVE]['selectorHash'],'actors':rows,'businessAcceptance':False,'globalExecution':'UNPROVEN'}

class RootJournal:
 def __init__(self,backend):self.backend=backend;self.fd=None;self.path=backend.paths.state/'stop-transaction.json'
 @contextmanager
 def locked(self):
  b=self.backend;b.require(b.admission.plan_hash,'journal-lock');
  with b.write_scope('journal-lock'):b.files.directory(b.paths.state,create=True)
  p=b.paths.state/'stop-exclusive.lock';b.require(b.admission.plan_hash,'journal-lock')
  fd=os.open(p,os.O_WRONLY|os.O_CREAT|os.O_NOFOLLOW,0o600)
  try:
   s=os.fstat(fd);need(stat.S_ISREG(s.st_mode)and s.st_uid==b.system.owner_uid and s.st_nlink==1 and stat.S_IMODE(s.st_mode)==0o600,'JOURNAL_LOCK_UNSAFE')
   try:fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
   except BlockingIOError:raise Refused('JOURNAL_BUSY')
   self.fd=fd;self.lockpath=p;yield self
  finally:self.fd=None;os.close(fd)
 def _guard(self):
  need(self.fd is not None,'JOURNAL_LOCK_REQUIRED');a=os.fstat(self.fd);z=self.lockpath.lstat();need((a.st_dev,a.st_ino)==(z.st_dev,z.st_ino)and z.st_nlink==1,'JOURNAL_LOCK_REPLACED')
 def read(self):
  self._guard();raw=self.backend.files.read(self.path,mode=0o600,allow_missing=True);return None if raw is None else R8.parse_json(raw)
 def write(self,value):
  self._guard();b=self.backend;b.require(b.admission.plan_hash,'journal-write');need(value.get('planHash')==b.admission.plan_hash,'JOURNAL_PLAN_DRIFT');old=self.read()
  if old:
   need(old['originalBaseline']==value['originalBaseline'],'JOURNAL_BASELINE_RESET')
   need(not old.get('signalAttemptConsumed')or value.get('signalAttemptConsumed')is True,'JOURNAL_SIGNAL_RESET')
   if old.get('signalAttemptConsumed'):need(old.get('checkpoint')==value.get('checkpoint')and old.get('checkpointHash')==value.get('checkpointHash'),'JOURNAL_CHECKPOINT_RESET')
   need(set(old.get('effects',{}))<=set(value.get('effects',{})),'JOURNAL_EFFECT_RESET')
  with b.write_scope('journal-write'):b.files.atomic(self.path,canonical(value))
