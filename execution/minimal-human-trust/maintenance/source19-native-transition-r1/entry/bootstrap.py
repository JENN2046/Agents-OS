"""Stdlib sealed loader for the already code-admitted fixed root tree.
No candidate source, arbitrary module/path or authority is accepted from argv.
The external capsule pin is a code-installation record, not stop permission.
"""
import hashlib,importlib.abc,importlib.util,json,os,re,resource,stat,sys,types
from pathlib import Path
ROOT=Path('/usr/lib/r16-maintenance/source19-native-transition-r1')
PIN=Path('/etc/r16-maintenance/source19-native-transition-r1-entry-capsule.json')
PREFIX='maintenance/source19-native-transition-r1/'
def need(v,c):
 if not v:raise ValueError(c)
def read(path,limit=32*1024*1024):
 cursor=Path('/')
 for n in path.parts[1:]:
  cursor/=n;s=cursor.lstat();need(s.st_uid==0 and not s.st_mode&0o022 and not stat.S_ISLNK(s.st_mode),'BOOTSTRAP_ROOT_PATH_REFUSED')
 fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
 try:
  a=os.fstat(fd);need(stat.S_ISREG(a.st_mode)and a.st_nlink==1 and a.st_size<=limit,'BOOTSTRAP_FILE_REFUSED');raw=b''
  while len(raw)<=limit:
   b=os.read(fd,min(65536,limit+1-len(raw)))
   if not b:break
   raw+=b
  fields=lambda s:(s.st_dev,s.st_ino,s.st_mode,s.st_uid,s.st_gid,s.st_nlink,s.st_size,s.st_mtime_ns,s.st_ctime_ns)
  need(len(raw)==a.st_size and fields(a)==fields(os.fstat(fd))==fields(path.lstat()),'BOOTSTRAP_CHANGED');return raw
 finally:os.close(fd)
def parse(raw):
 def pairs(rows):
  out={}
  for k,v in rows:need(k not in out,'BOOTSTRAP_DUPLICATE_KEY');out[k]=v
  return out
 return json.loads(raw,object_pairs_hook=pairs)
class SealedModules(importlib.abc.MetaPathFinder,importlib.abc.Loader):
 def __init__(self,sealed):self.sealed=sealed;self.names={}
 def find_spec(self,fullname,path=None,target=None):
  if fullname in self.names:return importlib.util.spec_from_loader(fullname,self)
 def create_module(self,spec):return None
 def exec_module(self,module):
  name=self.names[module.__name__];module.__file__=str(ROOT/'runtime'/name);exec(compile(self.sealed[name],module.__file__,'exec'),module.__dict__)
def sealed():
 need(os.getuid()==os.geteuid()==0,'BOOTSTRAP_ROOT_REQUIRED');resource.setrlimit(resource.RLIMIT_CORE,(0,0));os.umask(0o077)
 need(stat.S_IMODE(PIN.lstat().st_mode)==0o600 and stat.S_IMODE((ROOT/'ENTRY_FREEZE.json').lstat().st_mode)==0o600,'BOOTSTRAP_FREEZE_MODE');pin=parse(read(PIN,65536));need(set(pin)=={'schema','capsuleHash'}and pin['schema']=='r16.source19-native-transition.installed-entry.v1'and re.fullmatch('[a-f0-9]{64}',pin['capsuleHash']),'INSTALLED_ENTRY_PIN_REQUIRED')
 raw=read(ROOT/'ENTRY_FREEZE.json');need(hashlib.sha256(raw).hexdigest()==pin['capsuleHash'],'INSTALLED_ENTRY_CAPSULE_DRIFT');manifest=parse(raw);need(manifest.get('schema')=='r16.source19-native-transition.entry-freeze.v1'and manifest.get('mode')=='READONLY_PREFLIGHT_SOURCE','BOOTSTRAP_FREEZE_SCHEMA')
 sources={}
 for name,row in manifest['files'].items():
  need(type(name)is str and not name.startswith('/')and '\\'not in name and all(n not in('','.','..')for n in name.split('/')),'BOOTSTRAP_RELATIVE_SOURCE')
  value=read(ROOT/'runtime'/name);need(hashlib.sha256(value).hexdigest()==row['sha256']and len(value)==row['bytes']and stat.S_IMODE((ROOT/'runtime'/name).lstat().st_mode)==row['mode'],'BOOTSTRAP_SOURCE_DRIFT');sources[name]=value
 loader=SealedModules(sources)
 for name in sources:
  if name.startswith(PREFIX)and name.endswith('.py'):
   short=name.removeprefix(PREFIX).removeprefix('entry/').removesuffix('.py')
   if short.startswith('test_')or short in('bootstrap','operator'):continue
   need('/'not in short,'BOOTSTRAP_MODULE_SCOPE');need(short not in loader.names,'BOOTSTRAP_MODULE_COLLISION');loader.names[short]=name
 for alias,name in {'_source19_stop_contract':PREFIX+'stop_transition.py','_source19_protected_files':'maintenance/first-stop-r8/linux_backend.py'}.items():
  need(name in sources,'BOOTSTRAP_FIXED_DEPENDENCY_MISSING');loader.names[alias]=name
 need(all(n in loader.names for n in('common','native_guard','foreground','service_main','rpc','orchestration','linux_backend','native_checkpoint')),'BOOTSTRAP_REQUIRED_SOURCE_MISSING')
 need(not(set(loader.names)&set(sys.modules)),'BOOTSTRAP_PRELOADED_MODULE_REFUSED');sys.meta_path.insert(0,loader)
 # The backend's root-only dependency loader intentionally refuses disk
 # fallback. Materialize both already-hashed aliases before backend import.
 importlib.import_module('_source19_stop_contract');importlib.import_module('_source19_protected_files')
 return loader,pin['capsuleHash']
def main(argv=None):
 args=sys.argv[1:]if argv is None else argv;need(args and args[0]in('foreground','service','rpc'),'BOOTSTRAP_FIXED_MODE');loader,capsule=sealed()
 if args[0]=='foreground':
  import foreground
  need(len(args)==2,'BOOTSTRAP_FOREGROUND_ARGUMENTS');return foreground.main([args[1],capsule])
 if args[0]=='service':
  need(len(args)==1,'BOOTSTRAP_SERVICE_ARGUMENTS');import service_main;return service_main.main([])
 import rpc
 need(len(args)==3,'BOOTSTRAP_RPC_ARGUMENTS');return rpc.main(args[1:])
if __name__=='__main__':
 try:
  result=main()
  if type(result)is int:raise SystemExit(result)
  print(json.dumps(result,separators=(',',':')));raise SystemExit(75 if result.get('status')=='SERVICE_START_SUBMITTED_NOT_COMPLETED'else 0)
 except(Exception,KeyboardInterrupt)as e:
  c=getattr(e,'code',str(e));c=c if type(c)is str and re.fullmatch('[A-Z0-9_]{1,100}',c)else'SEALED_ENTRY_REFUSED_OR_UNKNOWN_RESULT';print(json.dumps({'status':'REFUSED_OR_READBACK_REQUIRED','code':c,'automaticRetry':False,'businessAcceptance':False}));raise SystemExit(78)
