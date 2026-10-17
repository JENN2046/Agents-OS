"""Fixed Linux effects for an independently admitted R8 source-App crash stop.

No CLI, remote executor, approval minting, general signal or arbitrary path API.
The parent native entry owns admission. Tests inject a fake OS and private paths.
"""
from contextlib import contextmanager
from dataclasses import dataclass
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import select
import signal
import socket
import stat
import subprocess
import time

HOST='VM-0-12-ubuntu'
UNIT='r16-app.service'
CGROUP='/system.slice/r16-app.service'
STATE=Path('/var/lib/r16-maintenance/first-stop-r8')
FENCE_PATH=Path('/run/systemd/system/r16-app.service.d/92-r16-first-stop-r8.conf')
FALSE_CONDITION=Path('/run/r16-first-stop-r8/source-app-start-not-authorized')
SOURCE=Path('/opt/r16/releases/r16-daily-20261012-r15')
LAUNCHER=Path('/opt/r16/trust/cloud-trusted-launcher.mjs')
LAUNCHER_SHA='5e4963c4078636b4c1bd9de22e12589734bfecc5c77f452f2017009921ff6231'
SOURCE_HASHES={
 'app/app-runner.mjs':'9fa13d0fe708d62e8ec34db680212d9d1857014c4e08bbaf1b00c60c8f602737',
 'app/workspace-host.mjs':'119756c7bb950308a1edb062b93c4848b5280e9ba356c13d6660f96b192915d2',
 'app/upstream/src/server.mjs':'08524d426f543b10e3806204111d4ed979c300baf220b5afb10f08c1da856912',
 'app/upstream/src/project-forge-crown-executor.mjs':'01f09efacf4169f88215815824acec8f4e9e1c5d2451d3e872dd4dad2bb49033',
 'src/lease-core.mjs':'889232f53d5c014138a7004df32c8e4f4f6c16703b6d53fa75ce0cbcf53e43b9',
}
ARGV=('/opt/r16/runtime/node-v24.15.0/bin/node',str(LAUNCHER),'/etc/r16-cloud/app-host.json')
PROPERTIES=('Id','LoadState','ActiveState','SubState','MainPID','ControlPID','ControlGroup','InvocationID','NRestarts','Restart','RefuseManualStart','DropInPaths','NeedDaemonReload','SendSIGKILL','KillSignal','LimitCORE')
ENV={'PATH':'/usr/bin:/bin','LANG':'C','LC_ALL':'C','SYSTEMD_PAGER':'cat','SYSTEMD_COLORS':'0'}

class Refused(Exception):
 def __init__(self,code):self.code=code;super().__init__(code)
def need(ok,code):
 if not ok:raise Refused(code)
def canonical(value):return json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()
def digest(value):return hashlib.sha256(canonical(value)).hexdigest()
def sha(raw):return hashlib.sha256(raw).hexdigest()
def ishash(value):return isinstance(value,str) and re.fullmatch('[0-9a-f]{64}',value) is not None

def parse_json(raw):
 def pairs(items):
  out={}
  for key,value in items:need(key not in out,'DUPLICATE_ROOT_JSON_KEY');out[key]=value
  return out
 def invalid(value):raise Refused('INVALID_ROOT_JSON_VALUE')
 try:return json.loads(raw,object_pairs_hook=pairs,parse_constant=invalid,parse_float=invalid)
 except (ValueError,UnicodeError):raise Refused('ROOT_JSON_CORRUPT')

def fence_bytes(owner):
 need(ishash(owner),'OWNER_HASH_REQUIRED')
 return ('# R8 one-time source-App crash stop '+owner+'\n[Unit]\nRefuseManualStart=yes\nConditionPathExists='+str(FALSE_CONDITION)+'\n[Service]\nRestart=no\n').encode()

@dataclass(frozen=True)
class Paths:
 state:Path=STATE
 fence:Path=FENCE_PATH
 condition:Path=FALSE_CONDITION

class ProtectedFiles:
 """Root-owned state, no-follow leaves, protected ancestors, exact own recovery."""
 def __init__(self,owner_uid=0):self.owner_uid=owner_uid
 def directory(self,path,mode=0o700,create=False,allow_missing=False):
  path=Path(path);need(path.is_absolute(),'ROOT_PATH_REQUIRED');cursor=Path('/')
  for part in path.parts[1:]:
   cursor/=part
   if create and not cursor.exists():
    try:cursor.mkdir(mode=mode);os.chmod(cursor,mode)
    except FileExistsError:pass
   try:s=cursor.lstat()
   except FileNotFoundError:
    if allow_missing:return None
    raise
   need(stat.S_ISDIR(s.st_mode) and s.st_uid in (0,self.owner_uid) and not s.st_mode&0o022,'ROOT_DIRECTORY_UNSAFE')
  return path
 def sync(self,path):
  self.directory(path);fd=os.open(path,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
  try:os.fsync(fd)
  finally:os.close(fd)
 def read(self,path,*,maximum=4*1024*1024,mode=None,allow_missing=False):
  path=Path(path)
  if self.directory(path.parent,allow_missing=allow_missing) is None:return None
  try:fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
  except FileNotFoundError:
   if allow_missing:return None
   raise
  try:
   a=os.fstat(fd);need(stat.S_ISREG(a.st_mode) and a.st_uid==self.owner_uid and a.st_nlink==1 and not a.st_mode&0o022 and a.st_size<=maximum and (mode is None or stat.S_IMODE(a.st_mode)==mode),'ROOT_FILE_UNSAFE')
   chunks=[];size=0
   while True:
    chunk=os.read(fd,min(65536,maximum+1-size))
    if not chunk:break
    chunks.append(chunk);size+=len(chunk);need(size<=maximum,'ROOT_FILE_CAPACITY')
   b=os.fstat(fd);need((a.st_dev,a.st_ino,a.st_size,a.st_mtime_ns,a.st_ctime_ns)==(b.st_dev,b.st_ino,b.st_size,b.st_mtime_ns,b.st_ctime_ns) and size==a.st_size,'ROOT_FILE_DRIFT')
   return b''.join(chunks)
  finally:os.close(fd)
 def atomic(self,path,raw,*,mode=0o600,immutable=False):
  path=Path(path);need(isinstance(raw,bytes),'ROOT_BYTES_REQUIRED');self.directory(path.parent,mode=0o700 if mode==0o600 else 0o755,create=True)
  pending=path.with_name('.'+path.name+'.'+sha(raw)+'.pending')
  # Repair only our exact link-before-unlink crash, never an arbitrary hardlink.
  if path.exists() and pending.exists():
   a=path.lstat();b=pending.lstat()
   if a.st_ino==b.st_ino and a.st_dev==b.st_dev:
    need(stat.S_ISREG(a.st_mode) and a.st_uid==self.owner_uid and a.st_nlink==2 and stat.S_IMODE(a.st_mode)==mode,'OWNED_PENDING_LINK_UNSAFE')
    fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
    try:need(os.read(fd,len(raw)+1)==raw,'OWNED_PENDING_BYTES_DRIFT')
    finally:os.close(fd)
    pending.unlink();self.sync(path.parent)
  old=self.read(path,mode=mode,allow_missing=True)
  if old is not None and immutable:
   need(old==raw,'FOREIGN_ROOT_FILE');return
  try:fd=os.open(pending,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,mode)
  except FileExistsError:
   prefix=self.read(pending,mode=mode,maximum=max(len(raw),1));need(len(prefix)<=len(raw) and raw.startswith(prefix),'FOREIGN_PENDING_BYTES')
   fd=os.open(pending,os.O_WRONLY|os.O_APPEND|os.O_NOFOLLOW);offset=len(prefix)
  else:offset=0
  try:
   os.fchmod(fd,mode)
   while offset<len(raw):offset+=os.write(fd,raw[offset:])
   os.fsync(fd)
  finally:os.close(fd)
  if immutable:
   try:os.link(pending,path,follow_symlinks=False)
   except FileExistsError:need(self.read(path,mode=mode)==raw,'FOREIGN_ROOT_FILE')
   pending.unlink()
  else:os.replace(pending,path)
  self.sync(path.parent)
 def remove_exact(self,path,raw,*,mode):
  need(self.read(path,mode=mode)==raw,'FOREIGN_ROOT_FILE');Path(path).unlink();self.sync(Path(path).parent)

class LinuxSystem:
 isolated=False
 owner_uid=0
 def require_root(self):need(os.getuid()==0 and os.geteuid()==0 and socket.gethostname()==HOST,'FIXED_CLOUD_ROOT_REQUIRED')
 def now(self):return int(time.time()*1000)
 def monotonic(self):return time.monotonic()
 def sleep(self,seconds):time.sleep(seconds)
 def run(self,argv):
  r=subprocess.run(tuple(argv),stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,env=ENV,timeout=10,check=False)
  need(r.returncode==0 and len(r.stdout)<=262144,'FIXED_MANAGER_COMMAND_FAILED');return r.stdout
 def kernel_read(self,path,maximum=65536):
  fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
  try:
   raw=os.read(fd,maximum+1);need(len(raw)<=maximum,'KERNEL_METADATA_CAPACITY');return raw
  finally:os.close(fd)
 def source_read(self,path):return ProtectedFiles().read(path,maximum=1024*1024)
 def freezer_write(self,value):
  need(value in (b'0',b'1'),'FIXED_FREEZER_VALUE_REQUIRED')
  fd=os.open('/sys/fs/cgroup'+CGROUP+'/cgroup.freeze',os.O_WRONLY|os.O_NOFOLLOW|os.O_CLOEXEC)
  try:need(os.write(fd,value)==1,'FREEZER_WRITE_UNCERTAIN')
  finally:os.close(fd)
 def pidfd_open(self,pid):return os.pidfd_open(pid,0)
 def pidfd_ready(self,fd):
  poll=select.poll();poll.register(fd,select.POLLIN|select.POLLHUP|select.POLLERR)
  events=poll.poll(0);need(all(not event&(select.POLLNVAL|select.POLLERR) for _,event in events),'PIDFD_INVALID');return bool(events)
 def pidfd_signal(self,fd):signal.pidfd_send_signal(fd,signal.SIGKILL,None,0)
 def pidfd_close(self,fd):os.close(fd)

class LinuxBackend:
 environment='PRODUCTION'
 def __init__(self,admission,checkpointer,*,system=None,paths=None):
  need(not isinstance(admission,(dict,bool)) and callable(getattr(admission,'require',None)),'NATIVE_ADMISSION_OBJECT_REQUIRED')
  self.admission=admission;self.checkpointer=checkpointer;self.system=LinuxSystem() if system is None else system
  need(paths is None or getattr(self.system,'isolated',False) is True,'PRODUCTION_PATH_OVERRIDE_REFUSED')
  self.paths=Paths() if paths is None else paths;self.files=ProtectedFiles(self.system.owner_uid);self.handles={}
 def require(self,operation,target):
  self.system.require_root();self.admission.require(operation,target)
  if target is not None:
   need(target.get('unit')==UNIT and target.get('host')==HOST and target.get('cgroup')==CGROUP and target.get('sourceHashes')==SOURCE_HASHES,'FIXED_SOURCE_TARGET_REQUIRED')
   need(type(target.get('pid')) is int and target['pid']>1 and isinstance(target.get('startTicks'),str) and re.fullmatch('[1-9][0-9]*',target['startTicks']),'PROCESS_BINDING_REQUIRED')
   need(re.fullmatch('[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}',target.get('bootId','')) is not None and re.fullmatch('[0-9a-f]{32}',target.get('invocationId','')) is not None and type(target.get('nRestarts')) is int and target['nRestarts']>=0,'INVOCATION_BINDING_REQUIRED')
   need(digest(target)==self.admission.target_hash,'NATIVE_TARGET_HASH_DRIFT')
 def assert_admitted(self,approval):
  self.require('driver',approval['target']);need(digest(approval)==self.admission.approval_hash,'NATIVE_APPROVAL_HASH_DRIFT');return True
 def properties(self):
  argv=('/usr/bin/systemctl','show',UNIT,*['--property='+p for p in PROPERTIES]);raw=self.system.run(argv).decode('ascii');out={}
  for line in raw.splitlines():
   need('=' in line,'MANAGER_METADATA_REFUSED');key,value=line.split('=',1);need(key not in out,'MANAGER_METADATA_REFUSED');out[key]=value
  need(set(out)==set(PROPERTIES) and out['Id']==UNIT and out['LoadState']=='loaded','MANAGER_UNIT_DRIFT');return out
 def conditions(self):
  raw=self.system.run(('/usr/bin/busctl','--system','--json=short','get-property','org.freedesktop.systemd1','/org/freedesktop/systemd1/unit/r16_2dapp_2eservice','org.freedesktop.systemd1.Unit','Conditions'))
  try:value=parse_json(raw)
  except ValueError:raise Refused('MANAGER_CONDITIONS_REFUSED')
  need(value.get('type')=='a(sbbsi)' and isinstance(value.get('data'),list),'MANAGER_CONDITIONS_REFUSED')
  matches=[]
  for row in value['data']:
   need(isinstance(row,list) and len(row)==5 and isinstance(row[0],str) and type(row[1]) is bool and type(row[2]) is bool and isinstance(row[3],str) and type(row[4]) is int,'MANAGER_CONDITIONS_REFUSED')
   if row[3]==str(self.paths.condition):matches.append(row)
  need(len(matches)==1 and matches[0][:4]==['ConditionPathExists',False,False,str(self.paths.condition)],'OWN_FALSE_CONDITION_NOT_EFFECTIVE')
 def condition_absent(self):
  self.files.directory(self.paths.condition.parent)
  need(not os.path.lexists(self.paths.condition),'FALSE_CONDITION_EXISTS')
 def _fence_record(self,target,owner):return {'schema':'r16.r8-restart-fence-owner.v1','ownerHash':owner,'targetHash':digest(target),'fenceSha256':sha(self._fence_bytes(owner))}
 def _fence_bytes(self,owner):
  # Paths differ only under explicit isolated OS injection, never in production.
  return fence_bytes(owner).replace(str(FALSE_CONDITION).encode(),str(self.paths.condition).encode())
 def _private_state(self,create=False):
  if self.files.directory(self.paths.state,create=create,allow_missing=not create) is None:return False
  st=self.paths.state.lstat();need(st.st_uid==self.system.owner_uid and stat.S_IMODE(st.st_mode)==0o700,'STATE_DIRECTORY_MODE_REFUSED');return True
 def _owner(self,target):
  if not self._private_state():return None
  raw=self.files.read(self.paths.state/'fence-owner.json',mode=0o600,allow_missing=True)
  if raw is None:return None
  try:record=parse_json(raw)
  except ValueError:raise Refused('FENCE_OWNER_CORRUPT')
  need(ishash(record.get('ownerHash')) and record==self._fence_record(target,record['ownerHash']),'FOREIGN_FENCE_OWNER');return record['ownerHash']
 def _fence_owner(self,target,props):
  raw=self.files.read(self.paths.fence,mode=0o644,allow_missing=True);owner=self._owner(target)
  if raw is None:return None
  need(owner is not None and raw==self._fence_bytes(owner),'FOREIGN_RESTART_FENCE')
  self.condition_absent();need(props['Restart']=='no' and props['RefuseManualStart']=='yes' and props['NeedDaemonReload']=='no' and str(self.paths.fence) in props['DropInPaths'].split(),'RESTART_FENCE_NOT_EFFECTIVE');self.conditions();return owner
 def _freeze_owner(self,target,frozen):
  if not frozen:return None
  need(self._private_state(),'FOREIGN_FREEZE')
  raw=self.files.read(self.paths.state/'freeze-owner.json',mode=0o600,allow_missing=True);need(raw is not None,'FOREIGN_FREEZE')
  try:record=parse_json(raw)
  except ValueError:raise Refused('FREEZE_OWNER_CORRUPT')
  need(set(record)=={'schema','ownerHash','targetHash'} and record.get('schema')=='r16.r8-freeze-owner.v1' and record.get('targetHash')==digest(target) and ishash(record.get('ownerHash')),'FOREIGN_FREEZE');return record['ownerHash']
 def _kernel_group(self):
  prefix='/sys/fs/cgroup'+CGROUP
  try:members_raw=self.system.kernel_read(prefix+'/cgroup.procs')
  except FileNotFoundError:members_raw=None
  try:events_raw=self.system.kernel_read(prefix+'/cgroup.events')
  except FileNotFoundError:events_raw=None
  try:request_raw=self.system.kernel_read(prefix+'/cgroup.freeze')
  except FileNotFoundError:request_raw=None
  if members_raw is None or events_raw is None or request_raw is None:
   need(members_raw is None and events_raw is None and request_raw is None,'CGROUP_METADATA_PARTLY_MISSING');return [],False,False
  try:
   members=[int(x) for x in members_raw.split()];events={}
   for line in events_raw.decode('ascii').splitlines():
    k,v=line.split();need(k not in events,'CGROUP_EVENTS_REFUSED');events[k]=v
  except (ValueError,UnicodeError):raise Refused('CGROUP_METADATA_REFUSED')
  need(len(members)==len(set(members)) and all(pid>1 for pid in members) and events.get('frozen') in ('0','1') and request_raw.strip() in (b'0',b'1'),'CGROUP_METADATA_REFUSED');return sorted(members),events['frozen']=='1',request_raw.strip()==b'1'
 def _proc(self,pid):
  try:raw=self.system.kernel_read('/proc/'+str(pid)+'/stat').decode('ascii')
  except FileNotFoundError:return None
  try:return raw.rsplit(')',1)[1].split()[19]
  except (IndexError,ValueError):raise Refused('PROCESS_START_REFUSED')
 def inspect(self,target):return self._inspect(target)
 def _inspect(self,target,allow_transition=False):
  self.require('inspect',target);props=self.properties()
  need(self.system.kernel_read('/proc/sys/kernel/random/boot_id').decode().strip()==target['bootId'],'BOOT_ID_DRIFT')
  need(props['ControlGroup'] in (CGROUP,'') and props['ControlPID']=='0' and props['NRestarts']==str(target['nRestarts']) and props['NeedDaemonReload']=='no' and props['SendSIGKILL']=='no' and props['KillSignal']=='15' and props['LimitCORE']=='0','MANAGER_POLICY_OR_RESTART_DRIFT')
  pins={name:sha(self.system.source_read(SOURCE/name)) for name in SOURCE_HASHES};need(pins==SOURCE_HASHES and sha(self.system.source_read(LAUNCHER))==LAUNCHER_SHA,'ORIGINAL_SOURCE_DRIFT')
  members,frozen,requested=self._kernel_group();need(allow_transition or frozen==requested,'FREEZER_TRANSITION_UNPROVEN');start=self._proc(target['pid'])
  main=int(props['MainPID']) if props['MainPID'].isdigit() else -1
  exited=main==0 and members==[] and start!=target['startTicks']
  if exited:need(props['InvocationID'] in ('',target['invocationId']) and props['ActiveState'] in ('inactive','failed'),'REPLACEMENT_INVOCATION_DETECTED')
  else:
   need(main==target['pid'] and start==target['startTicks'] and props['InvocationID']==target['invocationId'] and props['ControlGroup']==CGROUP and props['ActiveState']=='active' and props['SubState']=='running' and members==[target['pid']],'SOURCE_PROCESS_OR_CGROUP_DRIFT')
   need(self.system.kernel_read('/proc/'+str(target['pid'])+'/cgroup').decode().strip()=='0::'+CGROUP,'PROCESS_CGROUP_DRIFT')
   argv=tuple(x.decode() for x in self.system.kernel_read('/proc/'+str(target['pid'])+'/cmdline').split(b'\0') if x);need(argv==ARGV,'SOURCE_PROCESS_ARGV_DRIFT')
  owner=self._fence_owner(target,props);freeze_owner=self._freeze_owner(target,frozen or requested)
  if frozen or requested:need(owner==freeze_owner,'FREEZE_FENCE_OWNER_DRIFT')
  return {**target,'sourceHashes':pins,'processExited':exited,'members':members,'frozen':frozen,'freezeRequested':requested,'freezeOwner':freeze_owner,'fenceOwner':owner,'activeState':props['ActiveState'],'subState':props['SubState']}
 def open_pidfd(self,target):
  self.require('open-pidfd',target);row=self.inspect(target);need(not row['processExited'],'SOURCE_PROCESS_ALREADY_EXITED')
  fd=self.system.pidfd_open(target['pid'])
  try:self.inspect(target);need(not self.system.pidfd_ready(fd),'SOURCE_PROCESS_ALREADY_EXITED')
  except BaseException:self.system.pidfd_close(fd);raise
  self.handles[fd]={'target':dict(target),'used':False};return fd
 def close_pidfd(self,handle):
  if handle in self.handles:self.system.pidfd_close(handle);del self.handles[handle]
 def fence(self,target,owner):
  self.require('fence',target);need(owner==self.admission.approval_hash,'OWNER_ADMISSION_DRIFT')
  existing=self.files.read(self.paths.fence,mode=0o644,allow_missing=True)
  if existing is not None:
   need(self._owner(target)==owner and existing==self._fence_bytes(owner),'FOREIGN_RESTART_FENCE')
   self.condition_absent();self.system.run(('/usr/bin/systemctl','daemon-reload'))
  row=self.inspect(target);need(not row['processExited'] and not row['frozen'] and row['fenceOwner'] in (None,owner),'FENCE_BASELINE_REFUSED')
  self._private_state(create=True);self.files.directory(self.paths.condition.parent,mode=0o700,create=True);self.condition_absent()
  self.files.atomic(self.paths.state/'fence-owner.json',canonical(self._fence_record(target,owner)),immutable=True)
  self.files.atomic(self.paths.fence,self._fence_bytes(owner),mode=0o644,immutable=True)
  self.system.run(('/usr/bin/systemctl','daemon-reload'));self.assert_fence_owned(target,owner)
 def assert_fence_owned(self,target,owner):
  self.require('inspect',target);need(owner==self.admission.approval_hash,'OWNER_ADMISSION_DRIFT');row=self.inspect(target);need(row['fenceOwner']==owner,'OWNED_RESTART_FENCE_REQUIRED');return {'fencePath':str(self.paths.fence),'fenceSha256':sha(self._fence_bytes(owner)),'ownerHash':owner,'targetHash':digest(target),'effective':True}
 def freeze(self,target,owner):
  self.require('freeze',target);self.assert_fence_owned(target,owner);row=self.inspect(target);need(not row['processExited'],'SOURCE_PROCESS_ALREADY_EXITED')
  record={'schema':'r16.r8-freeze-owner.v1','ownerHash':owner,'targetHash':digest(target)}
  self.files.atomic(self.paths.state/'freeze-owner.json',canonical(record),immutable=True)
  if row['frozen']:need(row['freezeOwner']==owner,'FOREIGN_FREEZE');return
  self.system.freezer_write(b'1');end=self.system.monotonic()+10
  while True:
   row=self._inspect(target,allow_transition=True)
   need(row['freezeRequested'] and row['freezeOwner']==owner and row['fenceOwner']==owner,'FREEZE_REQUEST_DRIFT')
   if row['frozen']:return
   need(self.system.monotonic()<end,'FREEZE_NOT_CONFIRMED');self.system.sleep(.05)
 def checkpoint(self,target):
  self.require('checkpoint',target);row=self.inspect(target);need(row['processExited'] or (row['frozen'] and row['freezeOwner']==self.admission.approval_hash),'FROZEN_CHECKPOINT_REQUIRED')
  return self.checkpointer.capture(target)
 def send_pidfd_sigkill(self,handle,deadline):
  item=self.handles.get(handle);need(item is not None and not item['used'],'PIDFD_ATTEMPT_ALREADY_CONSUMED');target=item['target'];self.require('signal',target)
  row=self.inspect(target);need(row['frozen'] and row['freezeOwner']==self.admission.approval_hash and row['fenceOwner']==self.admission.approval_hash and not row['processExited'],'FROZEN_SINGLE_SOURCE_REQUIRED')
  need(type(deadline) is int and self.system.now()<deadline,'SIGNAL_DEADLINE_EXPIRED');need(not self.system.pidfd_ready(handle),'SOURCE_PROCESS_ALREADY_EXITED')
  # Consume before the syscall, including exceptions or unknown delivery.
  item['used']=True;need(self.system.now()<deadline,'SIGNAL_DEADLINE_EXPIRED');self.system.pidfd_signal(handle)
  # Observation may outlive the signal window; this never authorizes another
  # signal and is bounded independently from business completion.
  end=self.system.monotonic()+10
  while True:
   self.require('inspect',target);props=self.properties();members,_,_=self._kernel_group()
   need(props['NRestarts']==str(target['nRestarts']) and props['ControlPID']=='0' and props['MainPID'] in ('0',str(target['pid'])),'EXIT_REPLACEMENT_OR_RESTART')
   need(self._fence_owner(target,props)==self.admission.approval_hash,'OWNED_RESTART_FENCE_REQUIRED')
   if self.system.pidfd_ready(handle) and props['MainPID']=='0' and not members and self._proc(target['pid'])!=target['startTicks']:
    need(self.inspect(target)['processExited'],'EXIT_NOT_CONFIRMED');return
   need(self.system.monotonic()<end,'EXIT_NOT_CONFIRMED');self.system.sleep(.05)
 def unfreeze(self,target,owner):
  self.require('unfreeze',target);row=self._inspect(target,allow_transition=True)
  if row['frozen']!=row['freezeRequested']:
   self.require('unfreeze-transition',target)
   grant=getattr(self.admission,'recovery_approved',None)
   need(isinstance(grant,dict) and grant.get('stopApprovalHash')==owner and grant.get('targetHash')==digest(target) and ishash(grant.get('recoveryHash')),'TRANSITION_THAW_NATIVE_SCOPE_REQUIRED')
  need(owner==self.admission.approval_hash and row['fenceOwner']==owner and row['freezeOwner']==owner,'OWNED_FREEZE_REQUIRED')
  if row['processExited']:
   self.require('unfreeze-exited',target)
   grants=[getattr(self.admission,key,None) for key in ('handoff_approved','recovery_approved')]
   need(row['members']==[] and any(isinstance(g,dict) and g.get('stopApprovalHash')==owner and g.get('targetHash')==digest(target) and (ishash(g.get('successorPlanHash')) or ishash(g.get('recoveryHash'))) for g in grants),'EXITED_THAW_NATIVE_SCOPE_REQUIRED')
  self.system.freezer_write(b'0');end=self.system.monotonic()+10
  while True:
   row=self._inspect(target,allow_transition=True)
   need(not row['freezeRequested'],'THAW_REQUEST_DRIFT')
   if not row['frozen']:return
   need(self.system.monotonic()<end,'THAW_NOT_CONFIRMED');self.system.sleep(.05)
 def unfence(self,target,owner):
  self.require('unfence',target);row=self.inspect(target);need(owner==self.admission.approval_hash and row['fenceOwner']==owner and not row['frozen'],'OWNED_THAWED_FENCE_REQUIRED')
  self.files.remove_exact(self.paths.fence,self._fence_bytes(owner),mode=0o644);self.system.run(('/usr/bin/systemctl','daemon-reload'))
  need(self.inspect(target)['fenceOwner'] is None,'FENCE_REMOVAL_NOT_CONFIRMED')

class RootJournal:
 """Fixed root state; a single exclusive lock covers admission and Driver.run."""
 def __init__(self,admission,*,system=None,paths=None):
  need(not isinstance(admission,(bool,dict)) and callable(getattr(admission,'require',None)),'NATIVE_ADMISSION_OBJECT_REQUIRED')
  self.admission=admission;self.system=LinuxSystem() if system is None else system
  need(paths is None or getattr(self.system,'isolated',False) is True,'PRODUCTION_PATH_OVERRIDE_REFUSED')
  self.paths=Paths() if paths is None else paths;self.files=ProtectedFiles(self.system.owner_uid);self.lockfd=None
 def require(self,operation):
  self.system.require_root();self.admission.require(operation,None)
  if self.lockfd is not None:
   a=os.fstat(self.lockfd);b=(self.paths.state/'exclusive.lock').lstat();need(a.st_dev==b.st_dev and a.st_ino==b.st_ino and b.st_nlink==1,'JOURNAL_LOCK_REPLACED')
 @contextmanager
 def locked(self):
  self.require('journal-lock');need(self.lockfd is None,'JOURNAL_ALREADY_LOCKED');self.files.directory(self.paths.state,create=True)
  s=self.paths.state.lstat();need(stat.S_IMODE(s.st_mode)==0o700,'STATE_DIRECTORY_MODE_REFUSED')
  path=self.paths.state/'exclusive.lock';fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_NOFOLLOW,0o600)
  try:
   s=os.fstat(fd);need(stat.S_ISREG(s.st_mode) and s.st_uid==self.system.owner_uid and s.st_nlink==1 and stat.S_IMODE(s.st_mode)==0o600,'JOURNAL_LOCK_FILE_UNSAFE')
   try:fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
   except BlockingIOError:raise Refused('JOURNAL_BUSY')
   self.lockfd=fd;yield self
  finally:
   self.lockfd=None;os.close(fd)
 def read(self):
  self.require('journal-read');need(self.lockfd is not None,'JOURNAL_LOCK_REQUIRED')
  raw=self.files.read(self.paths.state/'transaction.json',mode=0o600,allow_missing=True)
  if raw is None:return None
  try:value=parse_json(raw)
  except ValueError:raise Refused('JOURNAL_CORRUPT')
  need(isinstance(value,dict),'JOURNAL_CORRUPT');return value
 def write(self,value):
  self.require('journal-write');need(self.lockfd is not None,'JOURNAL_LOCK_REQUIRED')
  need(value.get('approvalHash')==self.admission.approval_hash and value.get('targetHash')==self.admission.target_hash,'JOURNAL_ADMISSION_DRIFT')
  old=self.read()
  if old is not None:
   need(old.get('approvalHash')==value['approvalHash'] and old.get('targetHash')==value['targetHash'],'JOURNAL_BINDING_DRIFT')
   if old.get('signalAttemptConsumed'):
    need(value.get('signalAttemptConsumed') is True and value.get('phase') in ('SIGNAL_INTENT','SIGNAL_RETURNED','RECOVERY_REQUIRED_AFTER_SIGNAL','TERMINAL'),'SIGNAL_INTENT_RESET_REFUSED')
    need(old.get('checkpointDigest')==value.get('checkpointDigest') and old.get('checkpoint')==value.get('checkpoint'),'SIGNAL_CHECKPOINT_RESET_REFUSED')
   if old.get('phase')=='TERMINAL':need(value==old,'TERMINAL_JOURNAL_IMMUTABLE')
  self.files.atomic(self.paths.state/'transaction.json',canonical(value))
