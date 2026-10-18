#!/usr/bin/python3
"""Ordinary user wrapper for a separately reviewed native code-admission packet.
Default describe/verify never invokes sudo, SSH, a Root module or installation.
"""
import base64,hashlib,json,os,re,shlex,socket,stat,subprocess,sys
from pathlib import Path
SOURCE=Path('/home/jenn/Documents/Codex/2026-10-17/SOURCE19_READONLY_CODE_UPDATE_R1/source')
CLOUD_SOURCE='/home/ubuntu/source19-readonly-code-update-r1'
LOCAL_STAGE=Path('/home/jenn/.cache/r16-readonly-code-update-r1')
BUNDLE=Path('/home/jenn/AGENTS_OS_Workspace/ops/source19-app-history-schema-20261017-r1/code-bytes-candidate-not-install-entry')
PREVIOUS=Path('/home/jenn/Documents/Codex/2026-10-17/SOURCE19_PROTECTED_PREFLIGHT_R1/code-bundle-r2')
LOCAL='jenn-System-Product-Name';CLOUD='VM-0-12-ubuntu'
SCHEMA='r16.source19-readonly-code-update.entry-freeze.v1'
MODES=frozenset({'describe','review','update','readback','restore'})
REQUIRED=frozenset({'code_update.py','support_admission.py','native_guard.py','launch_code_update.py','review.json','legacy_supplement.json'})
MAX_FILE=1024*1024;MAX_PACKET=2*1024*1024
SSH=('/usr/bin/ssh','-F','/dev/null','-o','BatchMode=yes','-o','IdentityAgent=none','-o','IdentitiesOnly=yes','-i','/home/jenn/.ssh/TXY_159_75_139_246_ed25519','-o','StrictHostKeyChecking=yes','-o','UpdateHostKeys=no','-o','UserKnownHostsFile=/etc/r16-owner/ssh_known_hosts','-o','GlobalKnownHostsFile=/dev/null','-o','ConnectTimeout=8','-o','ClearAllForwardings=yes','ubuntu@159.75.139.246')
def need(v,c):
 if not v:raise ValueError(c)
def sha(b):return hashlib.sha256(b).hexdigest()
def parse(raw):
 def unique(rows):
  result={}
  for k,v in rows:need(k not in result,'ENTRY_DUPLICATE_JSON_KEY');result[k]=v
  return result
 def invalid(_):raise ValueError('ENTRY_INVALID_JSON_CONSTANT')
 return json.loads(raw,object_pairs_hook=unique,parse_constant=invalid)
def stamp(s):return(s.st_dev,s.st_ino,s.st_uid,s.st_gid,s.st_mode,s.st_nlink,s.st_size,s.st_mtime_ns,s.st_ctime_ns)
def filename(n):
 need(type(n)is str and n and not n.startswith('/')and '\\'not in n and all(re.fullmatch('[A-Za-z0-9_][A-Za-z0-9_.-]{0,127}',part)and part not in('.','..')for part in n.split('/'))and n!='ENTRY_FREEZE.json','ENTRY_FIXED_RELATIVE_NAME_REQUIRED');return n
def read_at(directory,name,mode,maximum=MAX_FILE):
 parts=name.split('/');parent=os.dup(directory)
 try:
  for part in parts[:-1]:
   child=os.open(part,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW,dir_fd=parent);os.close(parent);parent=child;s=os.fstat(parent);need(stat.S_ISDIR(s.st_mode)and s.st_uid==1000 and not s.st_mode&0o022,'ENTRY_SOURCE_DIRECTORY_REFUSED')
  fd=os.open(parts[-1],os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK,dir_fd=parent)
  try:
   before=os.fstat(fd);need(stat.S_ISREG(before.st_mode)and before.st_uid==1000 and before.st_nlink==1 and stat.S_IMODE(before.st_mode)==mode and before.st_size<=maximum,'ENTRY_SOURCE_METADATA_REFUSED');raw=b''
   while len(raw)<=maximum:
    b=os.read(fd,min(65536,maximum+1-len(raw)))
    if not b:break
    raw+=b
   need(len(raw)==before.st_size and stamp(before)==stamp(os.fstat(fd))==stamp(os.stat(parts[-1],dir_fd=parent,follow_symlinks=False)),'ENTRY_SOURCE_CHANGED_DURING_CAPTURE');return raw
  finally:os.close(fd)
 finally:os.close(parent)
def bundle_names(base=BUNDLE,prefix='bundle/'):
 names=set()
 def error(e):raise e
 for directory,children,files in os.walk(base,followlinks=False,onerror=error):
  for n in children:need(not(Path(directory)/n).is_symlink(),'ENTRY_BUNDLE_SYMLINK_DIRECTORY')
  names.update(prefix+(Path(directory)/n).relative_to(base).as_posix()for n in files)
 need(len(names)==34,'ENTRY_BUNDLE_34FILE_CLOSURE_REQUIRED');return names

def capture():
 need(os.getuid()==os.geteuid()==1000,'ORDINARY_HOST_ADMIN_UID1000_REQUIRED')
 dirs={};stamps={}
 try:
  for key,p in [('source',SOURCE),('bundle',BUNDLE),('previous',PREVIOUS)]:
   fd=os.open(p,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW);dirs[key]=fd;row=os.fstat(fd)
   need(stat.S_ISDIR(row.st_mode)and row.st_uid==1000 and not row.st_mode&0o022 and(key!='source'or stat.S_IMODE(row.st_mode)==0o700),'ENTRY_DIRECTORY_REFUSED');stamps[key]=stamp(row)
  raw=read_at(dirs['source'],'ENTRY_FREEZE.json',0o600,262144);manifest=parse(raw)
  expected=REQUIRED|bundle_names(BUNDLE)|bundle_names(PREVIOUS,'previous/')
  need(manifest.get('schema')==SCHEMA and type(manifest.get('files'))is dict and set(manifest['files'])==expected,'ENTRY_FREEZE_SCOPE_REQUIRED')
  sealed={};total=len(raw)
  for name,row in manifest['files'].items():
   filename(name);key='bundle'if name.startswith('bundle/')else'previous'if name.startswith('previous/')else'source';relative=name.split('/',1)[1]if key!='source'else name
   need(type(row)is dict and set(row)=={'path','sha256','bytes','mode'}and row['path']==name and re.fullmatch('[a-f0-9]{64}',row.get('sha256',''))and type(row.get('bytes'))is int and 0<=row['bytes']<=MAX_FILE and type(row.get('mode'))is int and not row['mode']&0o7022,'ENTRY_SOURCE_PIN_REQUIRED')
   value=read_at(dirs[key],relative,row['mode']);need(len(value)==row['bytes']and sha(value)==row['sha256'],'ENTRY_SOURCE_BYTE_PIN_DRIFT');total+=len(value);need(total<=MAX_PACKET,'ENTRY_PACKET_TOO_LARGE');sealed[name]=value
  for key,p in [('source',SOURCE),('bundle',BUNDLE),('previous',PREVIOUS)]:need(stamp(os.fstat(dirs[key]))==stamp(p.lstat())==stamps[key],'ENTRY_DIRECTORY_CHANGED')
  need(expected==REQUIRED|bundle_names(BUNDLE)|bundle_names(PREVIOUS,'previous/'),'ENTRY_BUNDLE_SET_CHANGED')
  return {'manifest':manifest,'raw':raw,'packetHash':sha(raw),'sources':sealed}
 finally:
  for fd in dirs.values():os.close(fd)
def summary(packet=None):return {'schema':'r16.source19-readonly-code-update.operator.v1','status':'DESCRIBE_ONLY'if packet is None else'LOCAL_PACKET_BYTE_VERIFIED','packetHash':None if packet is None else packet['packetHash'],'localRootHost':LOCAL,'cloudRootHost':CLOUD,'originalCodeRetainedUntilNativeUpdate':True,'exactThreeObjectUpdateReviewRequired':True,'oldReviewOnlyDecisionIsNotInstallAuthority':True,'privateSigningKeysRead':False,'networkCommands':0,'sudoCommands':0,'installationPerformed':False,'businessAcceptance':False}
def payload(packet):return json.dumps({'entryFreeze':base64.b64encode(packet['raw']).decode(),'sources':{n:base64.b64encode(b).decode()for n,b in packet['sources'].items()}},separators=(',',':')).encode()

def root_loader(packet,host,mode):
 need(host in(LOCAL,CLOUD)and mode in MODES,'ENTRY_FIXED_HOST_MODE_REQUIRED')
 raw=payload(packet);need(len(raw)<=MAX_PACKET,'HELD_PACKET_FILE_TOO_LARGE');pin=sha(raw)
 stage=str(LOCAL_STAGE/'packet.json')if host==LOCAL else CLOUD_SOURCE+'/packet.json'
 body="""import base64,hashlib,json,os,re,resource,socket,stat,sys,types
HOST="""+repr(host)+""";MODE="""+repr(mode)+""";EXPECTED="""+repr(pin)+""";PACKET_PATH="""+repr(stage)+"""
def need(v,c):
 if not v:raise ValueError(c)
def parse(raw):
 def pairs(rows):
  out={}
  for k,v in rows:need(k not in out,'ROOT_PACKET_DUPLICATE_KEY');out[k]=v
  return out
 return json.loads(raw,object_pairs_hook=pairs)
need(os.getuid()==os.geteuid()==0 and socket.gethostname()==HOST,'ROOT_FIXED_HOST_REQUIRED')
need(MODE in('describe','review','update','readback','restore'),'ROOT_FIXED_MODE_REQUIRED')
need(all(os.isatty(fd)and os.tcgetpgrp(fd)==os.getpgrp()for fd in(0,1,2)),'ROOT_INHERITED_FOREGROUND_TTY_REQUIRED')
resource.setrlimit(resource.RLIMIT_CORE,(0,0));os.umask(0o077)
parts=PACKET_PATH.split('/')[1:];parent=os.open('/',os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
try:
 for component in parts[:-1]:
  child=os.open(component,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW,dir_fd=parent);os.close(parent);parent=child
 fd=os.open(parts[-1],os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK,dir_fd=parent)
 try:
  a=os.fstat(fd);need(stat.S_ISREG(a.st_mode)and a.st_uid==1000 and a.st_nlink==1 and stat.S_IMODE(a.st_mode)==0o600 and a.st_size<=2097152,'ROOT_PACKET_FILE_REFUSED');held=b''
  while len(held)<=2097152:
   block=os.read(fd,min(65536,2097153-len(held)))
   if not block:break
   held+=block
  stamp=lambda s:(s.st_dev,s.st_ino,s.st_uid,s.st_gid,s.st_mode,s.st_nlink,s.st_size,s.st_mtime_ns,s.st_ctime_ns)
  need(len(held)==a.st_size and stamp(a)==stamp(os.fstat(fd))==stamp(os.stat(parts[-1],dir_fd=parent,follow_symlinks=False)),'ROOT_PACKET_CHANGED')
 finally:os.close(fd)
finally:os.close(parent)
need(hashlib.sha256(held).hexdigest()==EXPECTED,'ROOT_HELD_PACKET_FILE_HASH_DRIFT')
wrapped=parse(held);raw=base64.b64decode(wrapped['entryFreeze'],validate=True);manifest=parse(raw)
need(manifest.get('schema')=="""+repr(SCHEMA)+""" and type(manifest.get('files'))is dict and {'code_update.py','support_admission.py','native_guard.py','launch_code_update.py','review.json','legacy_supplement.json'}<=set(manifest['files']),'ROOT_ENTRY_PACKET_SCOPE')
need(set(wrapped['sources'])==set(manifest['files']),'ROOT_ENTRY_SOURCE_SET_DRIFT');sealed={}
for name,row in manifest['files'].items():
 need(type(name)is str and not name.startswith('/')and '\\\\'not in name and all(re.fullmatch('[A-Za-z0-9_][A-Za-z0-9_.-]{0,127}',n)and n not in('.','..')for n in name.split('/')),'ROOT_ENTRY_SOURCE_NAME')
 value=base64.b64decode(wrapped['sources'][name],validate=True)
 need(len(value)==row['bytes']and hashlib.sha256(value).hexdigest()==row['sha256']and type(row['mode'])is int and not row['mode']&0o7022,'ROOT_ENTRY_SOURCE_HASH_DRIFT');sealed[name]=value
need('native_guard'not in sys.modules,'ROOT_NATIVE_GUARD_MODULE_COLLISION')
guard=types.ModuleType('native_guard');guard.__file__='<held-native-code-admission/native_guard.py>';sys.modules['native_guard']=guard
exec(compile(sealed['native_guard.py'],guard.__file__,'exec'),guard.__dict__)
need('support_admission'not in sys.modules,'ROOT_SUPPORT_MODULE_COLLISION')
support=types.ModuleType('support_admission');support.__file__='<held-readonly-code-update/support_admission.py>';sys.modules['support_admission']=support
exec(compile(sealed['support_admission.py'],support.__file__,'exec'),support.__dict__)
scope={'__name__':'held_readonly_code_update','__file__':'<held-native-code-admission/code_update.py>','MODE':MODE,'HOST':HOST,'SEALED_PACKET':sealed,'SEALED_SOURCES':sealed,'ENTRY_PACKET_RAW':raw,'ENTRY_PACKET_SHA':hashlib.sha256(raw).hexdigest(),'HELD_PACKET_FILE_SHA':EXPECTED}
sys.argv=[scope['__file__'],MODE]
exec(compile(sealed['code_update.py'],scope['__file__'],'exec'),scope)
need(callable(scope.get('main')),'ROOT_NATIVE_MAIN_REQUIRED')
result=scope['main']()
if isinstance(result,int):raise SystemExit(result)
if result is not None:print(json.dumps(result,separators=(',',':')))
"""

 return "import json,re,sys\nscope={}\ntry:\n"+''.join(' '+line+'\n'for line in body.splitlines())+"""except (Exception,KeyboardInterrupt) as error:
 value=str(error)
 code=value if value.isascii()and len(value)<=100 and re.fullmatch('[A-Z0-9_]+',value)else'ROOT_NATIVE_ENTRY_REFUSED_OR_UNKNOWN'
 uncertain=bool(scope.get('EFFECTS_STARTED',False))
 print(json.dumps({'status':'RECOVERY_REQUIRED'if uncertain else'REFUSED','code':code,'automaticRetry':False},separators=(',',':')),flush=True)
 raise SystemExit(75 if uncertain else 78)
"""

STAGER=r'''import hashlib,os,socket,stat,sys
from pathlib import Path
BASE=Path('/home/ubuntu/source19-readonly-code-update-r1')
def need(v,c):
 if not v:raise ValueError(c)
need(os.getuid()==os.geteuid()==1000 and socket.gethostname()=='VM-0-12-ubuntu','STAGE_FIXED_ORDINARY_CLOUD_REQUIRED')
raw=sys.stdin.buffer.read(2097153);need(len(raw)<=2097152,'STAGE_CAPACITY')
try:BASE.mkdir(mode=0o700)
except FileExistsError:pass
s=BASE.lstat();need(stat.S_ISDIR(s.st_mode)and not stat.S_ISLNK(s.st_mode)and s.st_uid==1000 and stat.S_IMODE(s.st_mode)==0o700,'STAGE_DIRECTORY_REFUSED')
fd=os.open(BASE,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
try:
 need(set(os.listdir(fd))<={'packet.json'},'STAGE_FOREIGN_FILE')
 try:f=os.open('packet.json',os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600,dir_fd=fd)
 except FileExistsError:
  f=os.open('packet.json',os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK,dir_fd=fd)
  try:s=os.fstat(f);need(stat.S_ISREG(s.st_mode)and s.st_uid==1000 and s.st_nlink==1 and stat.S_IMODE(s.st_mode)==0o600 and s.st_size==len(raw)and os.read(f,len(raw)+1)==raw,'STAGE_EXISTING_BYTES_CONFLICT')
  finally:os.close(f)
 else:
  try:
   at=0
   while at<len(raw):at+=os.write(f,raw[at:])
   os.fchmod(f,0o600);os.fsync(f)
  finally:os.close(f)
 os.fsync(fd)
finally:os.close(fd)
print('{"status":"ORDINARY_CLOUD_ENTRY_SOURCE_STAGED","packetFileHash":"'+hashlib.sha256(raw).hexdigest()+'","rootEffects":0}')
'''
def local_stage(packet):
 raw=payload(packet);need(len(raw)<=MAX_PACKET,'HELD_PACKET_FILE_TOO_LARGE')
 # Fixed private ordinary cache; no Root tree is changed by this staging.
 need(LOCAL_STAGE.parent.is_dir()and not LOCAL_STAGE.parent.is_symlink(),'LOCAL_PRIVATE_STAGE_PARENT_REQUIRED')
 try:LOCAL_STAGE.mkdir(mode=0o700)
 except FileExistsError:pass
 row=LOCAL_STAGE.lstat();need(stat.S_ISDIR(row.st_mode)and row.st_uid==1000 and stat.S_IMODE(row.st_mode)==0o700,'LOCAL_PRIVATE_STAGE_REQUIRED')
 fd=os.open(LOCAL_STAGE,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
 try:
  need(set(os.listdir(fd))<={'packet.json'},'LOCAL_STAGE_FOREIGN_FILE')
  try:f=os.open('packet.json',os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600,dir_fd=fd)
  except FileExistsError:need(read_at(fd,'packet.json',0o600,MAX_PACKET)==raw,'LOCAL_STAGE_EXISTING_BYTES_CONFLICT')
  else:
   try:
    at=0
    while at<len(raw):at+=os.write(f,raw[at:])
    os.fsync(f)
   finally:os.close(f)
  os.fsync(fd)
 finally:os.close(fd)
 return {'status':'ORDINARY_LOCAL_ENTRY_SOURCE_STAGED','packetFileHash':sha(raw),'rootEffects':0}
def cloud_stage(packet):
 # Only future explicit --cloud reaches this ordinary source-copy step.
 command=shlex.join(['/usr/bin/python3','-I','-B','-c',STAGER])
 r=subprocess.run([*SSH[:-1],'-T',SSH[-1],command],input=payload(packet),stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=False,timeout=45)
 need(r.returncode==0 and len(r.stdout)<=8192,'ORDINARY_CLOUD_STAGE_REFUSED_NO_ROOT_STARTED');value=parse(r.stdout)
 need(value.get('status')=='ORDINARY_CLOUD_ENTRY_SOURCE_STAGED'and value.get('packetFileHash')==sha(payload(packet)),'ORDINARY_CLOUD_STAGE_READBACK_DRIFT');return value

def invocation(packet,host,mode):
 code=root_loader(packet,host,mode)
 sudo=['/usr/bin/sudo','-k','--','/usr/bin/python3','-I','-B','-c',code]
 if host==LOCAL:return sudo
 # The ordinary Python ancestor is intentional: the sealed guard verifies
 # actual launcher/sudo kernel provenance, rather than process-name/env claims.
 launcher='import subprocess;raise SystemExit(subprocess.run('+repr(sudo)+',check=False).returncode)'
 return [*SSH[:-1],'-tt',SSH[-1],shlex.join(['/usr/bin/python3','-I','-B','-c',launcher])]
def main(argv=None):
 args=sys.argv[1:]if argv is None else argv
 if args in([],['--describe']):print(json.dumps(summary(),ensure_ascii=False,indent=2),flush=True);return 0
 if args==['--verify']:
  packet=capture();print(json.dumps(summary(packet),ensure_ascii=False,indent=2),flush=True);return 0
 need(len(args)==2 and args[0]in('--local','--cloud')and args[1]in MODES,'FIXED_NATIVE_ENTRY_ARGUMENTS')
 need(os.getuid()==os.geteuid()==1000 and socket.gethostname()==LOCAL,'FIXED_ORDINARY_LOCAL_LAUNCHER_REQUIRED');need(all(os.isatty(fd)for fd in(0,1,2)),'REAL_INHERITED_FOREGROUND_TTY_REQUIRED')
 packet=capture();host=LOCAL if args[0]=='--local'else CLOUD;mode=args[1]
 print(json.dumps({**summary(packet),'requestedHost':host,'requestedMode':mode},ensure_ascii=False,indent=2),flush=True)
 print('这是独立的三文件只读代码更新入口。原批准不沿用；新代码、原物身份及独立审计范围须完整核对。',flush=True)
 print('默认/verify不提权不联网。继续后使用既有SSH认证（云）及fresh sudo -k，TTY原样继承，不捕获密码、不代填确认。',flush=True)
 print('review/readback不写入；update或restore仅由本人在Root前景核对当前完整摘要并输入准确hash后授权。三文件非整体原子更新，只读预检可短暂不可用；不启停、不签发、不改业务。',flush=True)
 need(input('本人阅读后按 Enter 进入所选阶段；其他内容取消：')=='','HUMAN_ENTRY_CANCELLED')
 if host==CLOUD:print(json.dumps(cloud_stage(packet),ensure_ascii=False),flush=True)
 else:print(json.dumps(local_stage(packet),ensure_ascii=False),flush=True)
 # Explicitly inherit all TTY fds. No PIPE/stdin data on authentication/root phase.
 try:r=subprocess.run(invocation(packet,host,mode),check=False)
 except (Exception,KeyboardInterrupt):
  print(json.dumps({'status':'ROOT_TRANSPORT_RESULT_UNKNOWN','automaticRetry':False,'exitCode':75},separators=(',',':')),flush=True);return 75
 print('原生入口退出码 '+str(r.returncode)+'。未知结果不可自动重试；退出0仍须对应准确模式回执。',flush=True);return r.returncode
if __name__=='__main__':
 code=78;hold=len(sys.argv)==3 and sys.argv[1]in('--local','--cloud')and sys.stdin.isatty()
 try:code=main()
 except(KeyboardInterrupt,EOFError):print('HUMAN_CANCELLED_OR_UNKNOWN_RESULT_NO_AUTOMATIC_RETRY',flush=True)
 except Exception as e:
  value=str(e);print(value if value.isascii()and len(value)<=100 and re.fullmatch('[A-Z0-9_]+',value)else'NATIVE_ENTRY_REFUSED_OR_UNKNOWN_RESULT',flush=True)
 finally:
  if hold:
   print('退出码 '+str(code),flush=True)
   try:input('读完回执后按 Enter 关闭：')
   except(EOFError,KeyboardInterrupt):pass
 raise SystemExit(code)
