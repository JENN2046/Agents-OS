"""Bounded protected entry IO. Never reads credential contents or business stores."""
import ctypes,errno,fcntl,hashlib,json,os,re,socket,stat,time
from contextlib import contextmanager
from pathlib import Path
LOCAL='jenn-System-Product-Name';CLOUD='VM-0-12-ubuntu'
ROOT=Path('/usr/lib/r16-maintenance/source19-native-transition-r1')
STATE=Path('/var/lib/r16-maintenance/source19-native-transition-r1')
UNIT='r16-source19-native-transition-r1.service'
SOURCE='56e1df18a54950ea346a51654e61df60afe33cb9928ae77293b2cf336fd8a5ec'
DELIVERY='b8645f6fe206e84dd07c2c6c166bfe4016d1deefca28bf9545dcfa1560f013e9'
MODE='READONLY_PREFLIGHT_SOURCE'
TARGET='r16-daily-20261017-source19-native-lifecycle-r1'
class Refused(Exception):
 def __init__(self,code):self.code=code;super().__init__(code)
def need(v,c):
 if not v:raise Refused(c)
def canonical(v):
 def order(x):
  if type(x)is dict:return {k:order(x[k])for k in sorted(x,key=lambda s:s.encode('utf-16-be','surrogatepass'))}
  if type(x)is list:return [order(y)for y in x]
  need(x is None or type(x)in(str,int,bool),'CANONICAL_TYPE')
  if type(x)is int:need(abs(x)<=9007199254740991,'CANONICAL_INTEGER')
  return x
 return json.dumps(order(v),ensure_ascii=False,separators=(',',':')).encode()
def sha(b):return hashlib.sha256(b).hexdigest()
def digest(v):return sha(canonical(v))
def ishash(x):return type(x)is str and re.fullmatch('[a-f0-9]{64}',x)is not None
def parse(raw):
 def unique(rows):
  d={}
  for k,v in rows:need(k not in d,'DUPLICATE_JSON_KEY');d[k]=v
  return d
 def bad(_):raise Refused('JSON_CONSTANT')
 return json.loads(raw,object_pairs_hook=unique,parse_constant=bad)
def now():return time.time_ns()//1000000
def root(host=None):
 need(os.getuid()==os.geteuid()==0,'ROOT_REQUIRED');actual=socket.gethostname()
 need(actual in(LOCAL,CLOUD)and(host is None or actual==host),'FIXED_HOST_REQUIRED');return actual
def relative(n):
 need(type(n)is str and n and not n.startswith('/')and '\\'not in n and all(x not in('','.','..')for x in n.split('/')),'RELATIVE_PATH_REQUIRED');return n
def stamp(s):return(s.st_dev,s.st_ino,s.st_uid,s.st_gid,s.st_mode,s.st_nlink,s.st_size,s.st_mtime_ns,s.st_ctime_ns)
def read(path,maximum=32*1024*1024,mode=None):
 path=Path(path);need(path.is_absolute(),'ABSOLUTE_FIXED_PATH_REQUIRED');p=Path('/')
 for n in path.parts[1:-1]:
  p/=n;s=p.lstat();need(stat.S_ISDIR(s.st_mode)and s.st_uid==0 and not s.st_mode&0o022,'ROOT_PARENT_REFUSED')
 fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
 try:
  a=os.fstat(fd);need(stat.S_ISREG(a.st_mode)and a.st_uid==0 and a.st_nlink==1 and not a.st_mode&0o7022 and a.st_size<=maximum and(mode is None or stat.S_IMODE(a.st_mode)==mode),'ROOT_FILE_REFUSED')
  raw=b''
  while len(raw)<=maximum:
   b=os.read(fd,min(65536,maximum+1-len(raw)))
   if not b:break
   raw+=b
  need(len(raw)==a.st_size and stamp(a)==stamp(os.fstat(fd))==stamp(path.lstat()),'ROOT_FILE_CHANGED');return raw
 finally:os.close(fd)
def mkdir(path,guard):
 p=Path('/')
 for n in Path(path).parts[1:]:
  p/=n
  if not p.exists():guard();p.mkdir(mode=0o700)
  s=p.lstat();need(stat.S_ISDIR(s.st_mode)and s.st_uid==0 and not s.st_mode&0o022,'ROOT_DIRECTORY_REFUSED')
def sync(path):
 fd=os.open(path,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
 try:os.fsync(fd)
 finally:os.close(fd)
def noreplace(source,target):
 libc=ctypes.CDLL(None,use_errno=True);result=libc.renameat2(-100,os.fsencode(source),-100,os.fsencode(target),1)
 if result:raise OSError(ctypes.get_errno(),os.strerror(ctypes.get_errno()))
def immutable(path,value,guard=lambda:None,mode=0o600):
 path=Path(path);raw=value if isinstance(value,bytes)else canonical(value)
 if path.exists():need(read(path,mode=mode)==raw,'IMMUTABLE_CONFLICT');return
 mkdir(path.parent,guard);pending=path.with_name('.'+path.name+'.'+sha(raw)+'.pending');guard()
 try:fd=os.open(pending,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,mode);at=0
 except FileExistsError:
  old=read(pending,mode=mode);need(raw.startswith(old),'PENDING_CONFLICT');fd=os.open(pending,os.O_WRONLY|os.O_NOFOLLOW);at=len(old)
 try:
  while at<len(raw):guard();at+=os.write(fd,raw[at:]) if at==0 else os.pwrite(fd,raw[at:],at)
  os.fsync(fd)
 finally:os.close(fd)
 guard()
 try:noreplace(pending,path)
 except FileExistsError:need(read(path,mode=mode)==raw,'IMMUTABLE_CONFLICT')
 sync(path.parent)
@contextmanager
def lock(path):
 # Caller must already possess native authority before the first file creation.
 fd=os.open(path,os.O_RDWR|os.O_CREAT|os.O_NOFOLLOW,0o600)
 try:
  s=os.fstat(fd);need(stat.S_ISREG(s.st_mode)and s.st_uid==0 and s.st_nlink==1 and stat.S_IMODE(s.st_mode)==0o600,'LOCK_REFUSED')
  try:fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
  except BlockingIOError:raise Refused('ENTRY_BUSY')
  yield fd
 finally:os.close(fd)
def verify_capsule(capsule):
 need(ishash(capsule),'EXTERNAL_CAPSULE_PIN_REQUIRED');raw=read(ROOT/'ENTRY_FREEZE.json',mode=0o600);need(sha(raw)==capsule,'ENTRY_CAPSULE_DRIFT');m=parse(raw)
 need(set(m)=={'schema','files','packageFiles','planTemplate','revisionRequest','mode'}and m['schema']=='r16.source19-native-transition.entry-freeze.v1'and m['mode']==MODE,'ENTRY_FREEZE_SCHEMA')
 required={'src/lease-core.mjs','src/control-clock.mjs','authority/source-baseline.mjs','maintenance/source19-native-transition-r1/entry/bootstrap.py','maintenance/source19-native-transition-r1/entry/transport.py','maintenance/source19-native-transition-r1/entry/foreground.py','maintenance/source19-native-transition-r1/entry/service_main.py','maintenance/source19-native-transition-r1/entry/common.py','maintenance/source19-native-transition-r1/entry/native_guard.py','maintenance/source19-native-transition-r1/entry/rpc.py','maintenance/source19-native-transition-r1/entry/public-state.mjs','maintenance/source19-native-transition-r1/entry/revision-plan.mjs','maintenance/source19-native-transition-r1/entry/service-run.mjs','maintenance/source19-native-transition-r1/publication.mjs','maintenance/source19-native-transition-r1/transaction.mjs','maintenance/source19-native-transition-r1/history-baseline.mjs','maintenance/source19-native-transition-r1/stop_transition.py','maintenance/source19-native-transition-r1/linux_backend.py','maintenance/source19-native-transition-r1/native_checkpoint.py','maintenance/source19-native-transition-r1/checkpoint_public.mjs','maintenance/source19-native-transition-r1/orchestration.py','maintenance/first-stop-r8/linux_backend.py'}
 need(type(m['files'])is dict and required<=set(m['files'])and type(m['packageFiles'])is dict and len(m['packageFiles'])>=0,'ENTRY_CLOSURE_INCOMPLETE')
 actual_sources=set()
 for p,dirs,files in os.walk(ROOT/'runtime',followlinks=False,onerror=lambda e:(_ for _ in()).throw(e)):
  for n in dirs:need(not(Path(p)/n).is_symlink(),'SOURCE_LINK_REFUSED')
  actual_sources.update((Path(p)/n).relative_to(ROOT/'runtime').as_posix()for n in files)
 need(actual_sources==set(m['files']),'SOURCE_EXACT_SET_DRIFT')
 for name,row in m['files'].items():
  name=relative(name);need(set(row)=={'sha256','bytes','mode'}and ishash(row['sha256'])and type(row['bytes'])is int and row['mode']in(0o644,0o755),'SOURCE_ROW_REFUSED')
  b=read(ROOT/'runtime'/name,mode=row['mode']);need(sha(b)==row['sha256']and len(b)==row['bytes'],'SOURCE_BYTES_DRIFT')
 actual=set()
 def error(e):raise e
 for p,dirs,files in os.walk(STATE/'package',followlinks=False,onerror=error)if m['packageFiles']else[]:
  s=Path(p).lstat();need(stat.S_ISDIR(s.st_mode)and s.st_uid==0 and not s.st_mode&0o022,'PACKAGE_DIRECTORY_REFUSED')
  for n in dirs:need(not(Path(p)/n).is_symlink(),'PACKAGE_LINK_REFUSED')
  actual.update((Path(p)/n).relative_to(STATE/'package').as_posix()for n in files)
 need(actual==set(m['packageFiles']),'PACKAGE_EXACT_SET_DRIFT')
 for name,row in m['packageFiles'].items():
  name=relative(name);need(set(row)=={'sha256','bytes','mode'}and ishash(row['sha256'])and type(row['bytes'])is int and row['mode']in(0o644,0o755),'PACKAGE_ROW_REFUSED')
  b=read(STATE/'package'/name,maximum=128*1024*1024,mode=row['mode']);need(sha(b)==row['sha256']and len(b)==row['bytes'],'PACKAGE_BYTES_DRIFT')
 need(m['revisionRequest']=={'forward':None,'recovery':None,'legacy21_22Disposition':'CANCELLED_UNALLOCATED_REPLAN'},'READONLY_NO_REVISION_ALLOCATION')
 t=m['planTemplate'];need(t.get('sourcePublicConfigHash')==SOURCE and t.get('sourceDeliveryHash')==DELIVERY and t.get('targetReleaseId')==TARGET,'SOURCE19_TEMPLATE_DRIFT')
 return m
