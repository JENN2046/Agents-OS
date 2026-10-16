"""Hash-pinned native bootstrap. No imports from candidate before full validation.

This file itself is hashed by the generated terminal launcher's stdlib-only
loader before root execution. No signing key or credential path is accepted.
"""
import hashlib,importlib,json,os,re,resource,socket,stat,sys
from pathlib import Path
CANDIDATE=Path('/home/ubuntu/r16-first-stop-r8-candidate')
ROOT=Path('/usr/lib/r16-maintenance/first-stop-r8')
POLICY='98552704b8bb8be9881318e8e8b12406448ea25f60951715a437198004ac4234'
def need(ok,code):
 if not ok: raise ValueError(code)
def secure_read(path,root_only=False):
 path=Path(path);p=Path('/')
 for bit in path.parts[1:-1]:
  p/=bit;s=p.lstat();need(stat.S_ISDIR(s.st_mode) and s.st_uid in ((0,) if root_only else (0,1000)) and not s.st_mode&0o022,'BOOTSTRAP_PARENT_REFUSED')
 fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
 try:
  a=os.fstat(fd);need(stat.S_ISREG(a.st_mode) and a.st_uid in ((0,) if root_only else (0,1000)) and a.st_nlink==1 and not a.st_mode&0o022 and a.st_size<=1048576,'BOOTSTRAP_FILE_REFUSED')
  raw=b''
  while len(raw)<=1048576:
   b=os.read(fd,65536)
   if not b:break
   raw+=b
  z=os.fstat(fd);fields=lambda s:(s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns)
  need(len(raw)==a.st_size and fields(a)==fields(z),'BOOTSTRAP_FILE_CHANGED');return raw
 finally:os.close(fd)
def parse(raw):
 def pairs(rows):
  out={}
  for k,v in rows:need(k not in out,'BOOTSTRAP_JSON_DUPLICATE');out[k]=v
  return out
 return json.loads(raw,object_pairs_hook=pairs)
def sha(raw):return hashlib.sha256(raw).hexdigest()
def run(mode,capsule_hash):
 resource.setrlimit(resource.RLIMIT_CORE,(0,0))
 need(os.getuid()==0 and os.geteuid()==0 and socket.gethostname()=='VM-0-12-ubuntu','BOOTSTRAP_FIXED_ROOT_REQUIRED')
 need(mode in ('stop','status','recover-original') and re.fullmatch('[0-9a-f]{64}',capsule_hash),'BOOTSTRAP_ARGUMENTS_REFUSED')
 base=CANDIDATE if mode=='stop' else ROOT/capsule_hash
 raw=secure_read(base/'CAPSULE.json',root_only=mode!='stop');need(sha(raw)==capsule_hash,'CAPSULE_HASH_DRIFT');manifest=parse(raw)
 need(set(manifest)=={'schema','files','policyExceptionProposalHash','acceptedPolicyException','productionStopAlreadyAuthorized'} and manifest['schema']=='r16.first-stop-capsule.v1' and manifest['policyExceptionProposalHash']==POLICY and manifest['acceptedPolicyException'] is True and manifest['productionStopAlreadyAuthorized'] is False,'CAPSULE_SCOPE_REFUSED')
 required={'bootstrap.py','common_safe.py','native_entry.py','stop_driver.py','linux_backend.py','ledger_checkpoint.py','handoff.py','TARGET.json'}
 need(set(manifest['files'])==required,'CAPSULE_FILE_SET_REFUSED')
 sealed={}
 for name,pin in manifest['files'].items():
  need(re.fullmatch('[A-Za-z_][A-Za-z0-9_]*[.](py|json)',name) and re.fullmatch('[0-9a-f]{64}',pin),'CAPSULE_PIN_REFUSED')
  value=secure_read(base/name,root_only=mode!='stop');need(sha(value)==pin,'CAPSULE_FILE_DRIFT');sealed[name]=value
 # No unverified candidate import. Execute common primitives only after every
 # file was sealed; copy sealed bytes rather than rereading mutable candidates.
 ns={'__name__':'r8_sealed_file_primitives'};exec(compile(sealed['common_safe.py'],'<r8-verified-file-primitives>','exec'),ns)
 target=ROOT/capsule_hash
 if mode=='stop':
  for name,value in sealed.items():ns['immutable'](target/name,value,0o644)
  ns['immutable'](target/'CAPSULE.json',raw,0o644)
 sys.path.insert(0,str(target))
 entry=importlib.import_module('native_entry')
 try:return entry.entry(mode,capsule_hash)
 except Exception as e:
  code=getattr(e,'code','NATIVE_ENTRY_REFUSED')
  return {'status':'REFUSED_OR_RECOVERY_REQUIRED','code':code if isinstance(code,str) and re.fullmatch('[A-Z0-9_]{1,100}',code) else 'NATIVE_ENTRY_REFUSED','businessAcceptance':False}
if __name__=='__main__':
 try:
  need(len(sys.argv)==3,'BOOTSTRAP_ARGUMENTS_REFUSED');result=run(sys.argv[1],sys.argv[2]);print(json.dumps(result,separators=(',',':')))
  status=result.get('status','')
  ok=status in ('CONTROLLED_CRASH_STOPPED_NOT_DRAINED','ABORTED_BEFORE_SIGNAL_ORIGINAL_RUNTIME_RESTORED','ORIGINAL_R15_RESTORED_NOT_DRAINED')
  raise SystemExit(0 if ok else 78)
 except (ValueError,OSError) as e:
  code=str(e);print(json.dumps({'status':'BOOTSTRAP_REFUSED','code':code if re.fullmatch('[A-Z0-9_]{1,100}',code) else 'PROTECTED_BOOTSTRAP_INVALID','businessAcceptance':False}));raise SystemExit(78)
