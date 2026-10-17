"""Pinned source-only native admission. preflight/status never install a helper."""
import hashlib,json,os,re,resource,socket,stat,sys,types
from pathlib import Path
CANDIDATE=Path('/home/ubuntu/r16-empty-temp-quarantine-r1-candidate')
ROOT=Path('/usr/lib/r16-maintenance/empty-temp-quarantine-r1')
POLICY='1ee6217b557dbce981211929201864bfbdde0b278e84b4081937354b09300a9c'
R8_CAPSULE='cfa55305623727e1b7607705c7b7a8eb76d2221250368828d21b7779da75af41'
R8_NAMES={'bootstrap.py','common_safe.py','native_entry.py','stop_driver.py','linux_backend.py','ledger_checkpoint.py','handoff.py','TARGET.json'}
REQUIRED={'bootstrap.py','entry.py','backend.py','driver.py','r8/CAPSULE.json',*{'r8/'+x for x in R8_NAMES}}
def need(ok,code):
 if not ok:raise ValueError(code)
def sha(raw):return hashlib.sha256(raw).hexdigest()
def parse(raw):
 def unique(rows):
  out={}
  for k,v in rows:need(k not in out,'DUPLICATE_CAPSULE_KEY');out[k]=v
  return out
 def invalid(_):raise ValueError('NONCANONICAL_CAPSULE_JSON')
 return json.loads(raw,object_pairs_hook=unique,parse_float=invalid,parse_constant=invalid)
def read(path,root_only=False):
 p=Path('/');allowed=(0,) if root_only else (0,1000)
 for part in path.parts[1:-1]:
  p/=part;s=p.lstat();need(stat.S_ISDIR(s.st_mode) and s.st_uid in allowed and not s.st_mode&0o022,'SEALED_PARENT_REFUSED')
 fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
 try:
  s=os.fstat(fd);need(stat.S_ISREG(s.st_mode) and s.st_uid in allowed and s.st_nlink==1 and not s.st_mode&0o022 and s.st_size<=1048576,'SEALED_FILE_REFUSED')
  raw=b''
  while len(raw)<=1048576:
   part=os.read(fd,65536)
   if not part:break
   raw+=part
  z=os.fstat(fd);identity=lambda x:(x.st_dev,x.st_ino,x.st_size,x.st_mtime_ns,x.st_ctime_ns)
  need(len(raw)==s.st_size and identity(s)==identity(z),'SEALED_FILE_CHANGED');return raw
 finally:os.close(fd)
def seal(base,pin,root_only):
 raw=read(base/'CAPSULE.json',root_only);need(sha(raw)==pin,'CAPSULE_PIN_DRIFT');manifest=parse(raw)
 need(type(manifest) is dict and set(manifest)=={'schema','policyProposalSha256','sourceCapsuleHash','nativeExecutionAlreadyAuthorized','files'} and manifest['schema']=='r16.empty-temp-quarantine-capsule.v1' and manifest['policyProposalSha256']==POLICY and manifest['sourceCapsuleHash']==R8_CAPSULE and manifest['nativeExecutionAlreadyAuthorized'] is False,'CAPSULE_SCOPE_REFUSED')
 need(type(manifest['files']) is dict and set(manifest['files'])==REQUIRED,'CAPSULE_FILE_SET_REFUSED')
 sealed={}
 for name,digest in manifest['files'].items():
  need(isinstance(digest,str) and re.fullmatch('[a-f0-9]{64}',digest),'MEMBER_PIN_REFUSED')
  value=read(base/name,root_only);need(sha(value)==digest,'CAPSULE_MEMBER_CHANGED');sealed[name]=value
 need(sha(sealed['r8/CAPSULE.json'])==R8_CAPSULE,'SOURCE_CAPSULE_DRIFT');source=parse(sealed['r8/CAPSULE.json'])
 need(set(source['files'])==R8_NAMES,'SOURCE_CAPSULE_SET_DRIFT')
 for name,pin in source['files'].items():need(sha(sealed['r8/'+name])==pin,'SOURCE_DEPENDENCY_DRIFT')
 return raw,sealed
LOAD_ORDER=(('r8_common_safe','r8/common_safe.py'),('r8_linux_backend','r8/linux_backend.py'),('r8_ledger_checkpoint','r8/ledger_checkpoint.py'),('r8_stop_driver','r8/stop_driver.py'),('quarantine_driver','driver.py'),('quarantine_backend','backend.py'),('quarantine_entry','entry.py'))
def loaded(sealed):
 names=[]
 try:
  for name,file in LOAD_ORDER:
   need(name not in sys.modules,'SEALED_MODULE_COLLISION')
   m=types.ModuleType(name);m.__file__='<sealed-memory/'+file+'>';sys.modules[name]=m;names.append(name)
   exec(compile(sealed[file],m.__file__,'exec'),m.__dict__)
  return names
 except BaseException:
  for name in names:sys.modules.pop(name,None)
  raise
def run(mode,pin):
 resource.setrlimit(resource.RLIMIT_CORE,(0,0))
 need(os.getuid()==0 and os.geteuid()==0 and socket.gethostname()=='VM-0-12-ubuntu','FIXED_CLOUD_ROOT_REQUIRED')
 need(mode in ('preflight','execute','status','recover') and isinstance(pin,str) and re.fullmatch('[a-f0-9]{64}',pin),'FIXED_MODE_AND_PIN_REQUIRED')
 candidate=mode in ('preflight','execute');base=CANDIDATE if candidate else ROOT/pin
 raw,sealed=seal(base,pin,not candidate)
 names=loaded(sealed)
 try:
  if mode=='execute':
   capacity=os.statvfs('/var/lib/r16-app')
   source_bytes=len(raw)+sum(len(value) for value in sealed.values())
   need(capacity.f_bavail*capacity.f_frsize>=32*1024*1024+source_bytes+1024*1024,'QUARANTINE_SOURCE_INSTALL_SPACE_UNPROVEN')
   common=sys.modules['r8_common_safe']
   for name,value in sealed.items():common.immutable(ROOT/pin/name,value,0o644)
   common.immutable(ROOT/pin/'CAPSULE.json',raw,0o644)
  return sys.modules['quarantine_entry'].entry(mode,pin,parse(sealed['r8/TARGET.json']))
 finally:
  for name in names:sys.modules.pop(name,None)
def bounded_code(error):
 value=getattr(error,'code',str(error) if isinstance(error,ValueError) else '')
 return value if isinstance(value,str) and re.fullmatch('[A-Z0-9_]{1,100}',value) else 'PROTECTED_QUARANTINE_ENTRY_REFUSED'
if __name__=='__main__':
 try:
  need(len(sys.argv)==3,'FIXED_ARGUMENTS_REQUIRED');result=run(sys.argv[1],sys.argv[2]);print(json.dumps(result,separators=(',',':')))
  raise SystemExit(0 if result.get('status') in ('QUARANTINE_READ_ONLY_PREFLIGHT_PASS','EMPTY_ARTIFACT_QUARANTINED_ORIGINAL_RUNTIME_RESTORED','ARTIFACT_RESTORED_NOT_BUSINESS_ACCEPTED','QUARANTINE_ABORTED_ORIGINAL_ARTIFACT_AND_RUNTIME_RESTORED','READ_ONLY_STATUS') else 78)
 except Exception as error:
  print(json.dumps({'status':'REFUSED_OR_RECOVERY_REQUIRED','code':bounded_code(error),'businessAcceptance':False,'processStopOrRestartPerformed':False},separators=(',',':')));raise SystemExit(78)
