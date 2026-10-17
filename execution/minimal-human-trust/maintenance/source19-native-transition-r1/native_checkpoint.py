"""Root-only read-only Native crash checkpoint; never SQLite-connect or lock Store.

Safety IO is adapted from first-stop-r8/ledger_checkpoint.py _read_at,
_open_directory, read_store_tree and _scan_writers: nofollow dirfd traversal,
stable full metadata, twice enumerated graph, writable fd/shared-map rejection.
Unlike the old App capture, this explicitly validates Source19 and Native data.
No CLI, arbitrary paths, auth authority, effects or database library are present.
"""
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import stat
import subprocess
import time

HOST='jenn-System-Product-Name'
NATIVE_ROOT=Path('/var/lib/r16-native')
STORE=NATIVE_ROOT/'grants/r16-projects-daily/dispatcher'
REGISTRY=Path('/etc/r16/native-ledgers.json')
PUBLIC=Path('/run/r16-owner/public-config.json')
CONFIG=Path('/etc/r16/native-host.json')
# Set only from reviewed public deployment fact; missing fact refuses capture.
DATABASE=Path('/home/jenn/AGENTS_OS_Workspace/runtime/VCPChat/AppData/ProjectForge/projectforge.db')
PUBLIC_HASH='56e1df18a54950ea346a51654e61df60afe33cb9928ae77293b2cf336fd8a5ec'
GRANT_HASH='00ac437d66143e627132975555d06396d69ff69616f630d19e3622627e15c5e6'
MAX_JSON=32*1024*1024
MAX_BYTES=2*1024*1024*1024
MAX_FILES=100000
PUBLIC_CHECKER=Path(__file__).with_name('checkpoint_public.mjs')
NODE_BINARIES={'jenn-System-Product-Name':'/usr/bin/node','VM-0-12-ubuntu':'/opt/r16/runtime/node-v24.15.0/bin/node'}

class Refused(Exception):
 def __init__(self,code):self.code=code;super().__init__(code)
def need(v,c):
 if not v:raise Refused(c)
def canonical(v):
 if isinstance(v,dict):return '{'+','.join(json.dumps(k,ensure_ascii=False)+':'+canonical(v[k]) for k in sorted(v,key=lambda x:x.encode('utf-16-be'))) +'}'
 if isinstance(v,list):return '['+','.join(canonical(x) for x in v)+']'
 need(v is None or type(v) in (str,int,bool),'NONCANONICAL_JSON')
 if type(v) is int:need(abs(v)<=9007199254740991,'NONCANONICAL_JSON')
 return json.dumps(v,ensure_ascii=False,separators=(',',':'))
def digest(v):return hashlib.sha256(canonical(v).encode()).hexdigest()
def sha(raw):return hashlib.sha256(raw).hexdigest()
def parse(raw):
 def pairs(items):
  out={}
  for k,v in items:need(k not in out and k not in ('__proto__','prototype','constructor'),'CORRUPT_JSON');out[k]=v
  return out
 def bad(_):raise Refused('NONCANONICAL_JSON')
 try:v=json.loads(raw,object_pairs_hook=pairs,parse_float=bad,parse_constant=bad);canonical(v);return v
 except (ValueError,UnicodeError,RecursionError):raise Refused('CORRUPT_JSON') from None

def identity(s):return (s.st_dev,s.st_ino,s.st_mode,s.st_uid,s.st_gid,s.st_nlink,s.st_size,s.st_mtime_ns,s.st_ctime_ns)
def open_directory(path,*,uid=None,mode=None):
 need(path.is_absolute() and str(path)==os.path.normpath(path),'FIXED_PATH_REQUIRED');fd=os.open('/',os.O_RDONLY|os.O_DIRECTORY)
 try:
  for part in path.parts[1:]:
   child=os.open(part,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW,dir_fd=fd);os.close(fd);fd=child;s=os.fstat(fd)
   need(s.st_uid in (0,1000) and not s.st_mode&0o7022,'DIRECTORY_METADATA_REFUSED')
  s=os.fstat(fd)
  if uid is not None:need(s.st_uid==uid and (mode is None or stat.S_IMODE(s.st_mode)==mode),'STORE_DIRECTORY_REFUSED')
  return fd
 except BaseException:os.close(fd);raise

def read_at(fd,name,*,uid,modes=(0o600,),retain=True,max_bytes=MAX_JSON):
 h=os.open(name,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK,dir_fd=fd)
 try:
  before=os.fstat(h);need(stat.S_ISREG(before.st_mode) and before.st_uid==uid and before.st_nlink==1 and stat.S_IMODE(before.st_mode) in modes and 0<=before.st_size<=max_bytes,'READ_METADATA_REFUSED')
  hasher=hashlib.sha256();chunks=[];count=0
  while True:
   b=os.read(h,65536)
   if not b:break
   count+=len(b);need(count<=max_bytes,'READ_CAPACITY_REFUSED');hasher.update(b)
   if retain:chunks.append(b)
  need(count==before.st_size and identity(before)==identity(os.fstat(h))==identity(os.stat(name,dir_fd=fd,follow_symlinks=False)),'READ_CHANGED')
  return b''.join(chunks) if retain else None, before, hasher.hexdigest()
 finally:os.close(h)

def public_file(path):
 fd=open_directory(path.parent)
 try:raw,s,h=read_at(fd,path.name,uid=0,modes=(0o644,),max_bytes=MAX_JSON);return parse(raw),raw,identity(s)
 finally:os.close(fd)
def wrapper(v,kind):
 need(type(v) is dict and set(v)=={'schema','revision','maxNow','data'} and type(v['schema']) is int and v['schema']==1 and all(type(v[k]) is int and v[k]>=0 for k in ('revision','maxNow')) and v['data'].get('kind')==kind,'STORE_WRAPPER_INVALID');return v['data']
def row(st,h):return {'sha256':h,'bytes':st.st_size,'mode':stat.S_IMODE(st.st_mode),'dev':st.st_dev,'ino':st.st_ino}

def read_native_tree(expected_registration=None):
 """Full Native root, not a filtered subset presented as complete inventory."""
 files={};jsons={};ids={};dirs={};stamps={};total=0;projects=None;root_graph=None
 def walk(fd,relative):
  nonlocal total,projects,root_graph
  before=os.fstat(fd);need(before.st_uid==1000 and stat.S_IMODE(before.st_mode)==0o700,'STORE_DIRECTORY_REFUSED');dirs[relative]=(before.st_dev,before.st_ino);stamps['dir:'+relative]=identity(before)
  names=sorted(os.listdir(fd));need(len(names)<=MAX_FILES,'STORE_CAPACITY_REFUSED')
  if relative=='native/grants/r16-projects-daily/dispatcher':
   need(expected_registration is not None and (before.st_dev,before.st_ino)==expected_registration,'NATIVE_REGISTRATION_DRIFT')
   raw,_,_=read_at(fd,'state.json',uid=1000);root_graph=raw;s=wrapper(parse(raw),'r16.native-dispatch.v1');projects=s.get('projects')
   need(isinstance(projects,list) and len(projects)==len(set(projects)) and all(isinstance(p,str) and re.fullmatch('[A-Za-z0-9_-]{1,128}',p) for p in projects),'PROJECT_GRAPH_INVALID')
   need(set(n for n in names if n.startswith('project-'))=={'project-'+p for p in projects},'UNREGISTERED_STORE_DIRECTORY')
  for name in names:
   need(not name.startswith(('.next','.reclaim')) and '.reclaim' not in name,'TEMPORARY_STORE_FILE_PRESENT')
   st=os.stat(name,dir_fd=fd,follow_symlinks=False);rel=relative+'/'+name
   if stat.S_ISDIR(st.st_mode):
    allowed=(relative=='native' and name=='grants') or (relative=='native/grants' and name=='r16-projects-daily') or (relative=='native/grants/r16-projects-daily' and name=='dispatcher') or (relative=='native/grants/r16-projects-daily/dispatcher' and (name=='results' or name in {'project-'+p for p in projects}))
    need(allowed,'UNREGISTERED_STORE_DIRECTORY');child=os.open(name,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW,dir_fd=fd)
    try:need(identity(os.fstat(child))==identity(st),'STORE_DIRECTORY_CHANGED');walk(child,rel)
    finally:os.close(child)
   else:
    if relative=='native':need(name in ('native-writer.lock','.native-writer.guard'),'UNREVIEWED_STORE_FILE')
    elif relative.endswith('/results'):need(re.fullmatch('(control|operation)-[A-Za-z0-9_-]+[.]json',name),'UNREVIEWED_STORE_FILE')
    elif relative.endswith('/dispatcher') or '/project-' in relative:need(name in ('state.json','.lock') or re.fullmatch('archive-[A-Za-z0-9_-]+[.]json',name),'UNREVIEWED_STORE_FILE')
    else:need(False,'UNREVIEWED_STORE_FILE')
    raw,st,h=read_at(fd,name,uid=1000);total+=len(raw);need(total<=MAX_BYTES and len(files)<MAX_FILES,'STORE_CAPACITY_REFUSED')
    files[rel]=row(st,h);ids[rel]=(st.st_dev,st.st_ino);stamps[rel]=identity(st)
    if name.endswith('.json'):jsons[rel.removeprefix('native/grants/r16-projects-daily/')]=parse(raw)
    elif name!='.native-writer.guard':jsons[rel]=parse(raw)
    if relative=='native/grants/r16-projects-daily/dispatcher' and name=='state.json':need(raw==root_graph,'REGISTERED_PROJECT_GRAPH_CHANGED')
  need(names==sorted(os.listdir(fd)) and identity(before)==identity(os.fstat(fd)),'STORE_DIRECTORY_CHANGED')
 fd=open_directory(NATIVE_ROOT,uid=1000,mode=0o700)
 try:walk(fd,'native')
 finally:os.close(fd)
 need('native/grants/r16-projects-daily/dispatcher/state.json' in files,'REGISTERED_STORE_MISSING')
 return files,jsons,ids,dirs,stamps

def read_database():
 need(DATABASE is not None,'FIXED_DATABASE_PATH_REQUIRED')
 files={};jsons={};ids={};dirs={};stamps={};fd=open_directory(DATABASE.parent,uid=1000)
 try:
  before=os.fstat(fd);dirs['database']=(before.st_dev,before.st_ino);stamps['dir:database']=identity(before);names=sorted(os.listdir(fd))
  allowed={DATABASE.name,DATABASE.name+'-wal',DATABASE.name+'-shm',DATABASE.name+'.r16-writer.lock'}
  need(set(names)<=allowed and DATABASE.name in names,'DATABASE_FILESET_REFUSED')
  for name in names:
   raw,st,h=read_at(fd,name,uid=1000,modes=(0o600,0o644),retain=name.endswith('.lock'),max_bytes=MAX_BYTES)
   key='database/'+name;files[key]=row(st,h);ids[key]=(st.st_dev,st.st_ino);stamps[key]=identity(st)
   if raw is not None:jsons[key]=parse(raw)
  need(names==sorted(os.listdir(fd)) and identity(before)==identity(os.fstat(fd)),'DATABASE_DIRECTORY_CHANGED')
 finally:os.close(fd)
 return files,jsons,ids,dirs,stamps

def proc_start(path):
 text=path.read_text();return text[text.rfind(')')+2:].split()[19]
def scan_writers(ids,dirs,target):
 """Existing R8 fd/maps strategy, covering Native AND SQLite file capabilities."""
 inodes=set(ids.values());directories=set(dirs.values());selfpid=os.getpid();own_start=proc_start(Path('/proc')/str(selfpid)/'stat')
 for proc in Path('/proc').iterdir():
  if not proc.name.isdecimal():continue
  pid=int(proc.name)
  if pid==selfpid:
   need(proc_start(proc/'stat')==own_start,'COLLECTOR_IDENTITY_CHANGED');continue
  try:
   before=proc_start(proc/'stat')
   if pid==target['pid'] and before==target['startTicks']:continue # only the exact frozen original, never a reused PID
   for item in (proc/'fd').iterdir():
    try:
     st=item.stat();ident=(st.st_dev,st.st_ino);link=os.readlink(item)
     in_scope=link==str(NATIVE_ROOT) or link.startswith(str(NATIVE_ROOT)+'/') or link==str(DATABASE.parent) or link.startswith(str(DATABASE.parent)+'/')
     need(ident not in directories and not (in_scope and stat.S_ISDIR(st.st_mode)),'FOREIGN_STORE_DIRECTORY_FD')
     if ident in inodes or in_scope:
      m=re.search(r'^flags:\s*([0-7]+)$',(proc/'fdinfo'/item.name).read_text(),re.M);need(m is not None,'FD_ACCESS_UNPROVEN');need(int(m[1],8)&os.O_ACCMODE==os.O_RDONLY,'FOREIGN_WRITABLE_FD')
    except FileNotFoundError:continue
   for line in (proc/'maps').read_text().splitlines():
    p=line.split(None,5);need(len(p)>=5,'MAP_ACCESS_UNPROVEN')
    if len(p[1])>=4 and p[1][1]=='w' and p[1][3]=='s':
     dev=p[3].split(':');ident=(os.makedev(int(dev[0],16),int(dev[1],16)),int(p[4]));path=p[5] if len(p)==6 else ''
     need(ident not in inodes and not(path==str(NATIVE_ROOT) or path.startswith(str(NATIVE_ROOT)+'/') or path==str(DATABASE.parent) or path.startswith(str(DATABASE.parent)+'/')),'FOREIGN_WRITABLE_SHARED_MAPPING')
   need(before==proc_start(proc/'stat'),'PROCESS_SCAN_CHANGED')
  except FileNotFoundError:continue
  except Refused:raise
  except (PermissionError,OSError,ValueError,IndexError):raise Refused('FOREIGN_WRITER_SCAN_UNPROVEN') from None
 need(own_start==proc_start(Path('/proc')/str(selfpid)/'stat'),'COLLECTOR_IDENTITY_CHANGED')

def check_locks(jsons,target):
 for name,value in jsons.items():
  if not name.endswith(('/.lock','native-writer.lock','.r16-writer.lock')):continue
  need(isinstance(value,dict) and type(value.get('pid')) is int and value['pid']>1 and isinstance(value.get('start'),str) and re.fullmatch('[0-9]+',value['start']),'LOCK_SHAPE_REFUSED')
  if name.endswith('/native-writer.lock'):
   need(set(value)=={'pid','start','started_at'} and type(value['started_at']) is int and value['started_at']>=0,'LOCK_SHAPE_REFUSED')
  else:
   need(set(value)=={'schema','pid','start','nonce'} and type(value['schema']) is int and value['schema']==1 and isinstance(value['nonce'],str) and re.fullmatch('[a-f0-9]{8}(?:-[a-f0-9]{4}){3}-[a-f0-9]{12}',value['nonce']),'LOCK_SHAPE_REFUSED')
  if value['pid']==target['pid'] and value['start']==target['startTicks']:continue
  try:current=proc_start(Path('/proc')/str(value['pid'])/'stat')
  except FileNotFoundError:current=None
  need(current!=value['start'],'FOREIGN_STORE_WRITER')

def public_validation(value):
 raw=canonical(value).encode();need(len(raw)<=64*1024*1024,'PUBLIC_CHECKPOINT_CAPACITY')
 host=platform.node();need(host in NODE_BINARIES,'FIXED_VALIDATOR_HOST_REQUIRED')
 p=subprocess.run([NODE_BINARIES[host],str(PUBLIC_CHECKER)],input=raw,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=30,env={'PATH':'/usr/bin:/bin'})
 if p.returncode:
  try:code=parse(p.stderr.strip()).get('code')
  except Exception:code=None
  raise Refused(code if isinstance(code,str) and re.fullmatch('[A-Z][A-Z0-9_]{1,63}',code) else 'PUBLIC_CRYPTO_REFUSED')
 out=parse(p.stdout);need(type(out) is dict,'PUBLIC_PROJECTION_INVALID');return out

class NativeCheckpoint:
 """Only a trusted admitted installer injects OS verifier + authenticated RPC.

 assert_checkpoint_safe(plan_hash,target) re-reads actual fixed kernel/cgroup,
 fence, target identity and returns None on success, otherwise raises. A JSON
 frozen/stopped boolean is not accepted. No default or caller-path backend.
 authenticated_app_history(plan_hash) comes from same-plan authenticated cloud
 root collector; independent exact original App signatures are still verified.
 """
 def __init__(self,admission,os_backend):
  need(callable(getattr(admission,'require',None)) and callable(getattr(os_backend,'assert_checkpoint_safe',None)) and callable(getattr(os_backend,'authenticated_app_history',None)),'TRUSTED_CHECKPOINT_BACKEND_REQUIRED');self.admission=admission;self.os=os_backend
 def boundary(self,h,target):
  self.admission.require(h,'checkpoint');need(self.os.assert_checkpoint_safe(h,target) is None,'OS_CHECKPOINT_BOOLEAN_NOT_EVIDENCE')
 def capture(self,plan_hash,target):
  need(os.geteuid()==0 and platform.node()==HOST,'FIXED_ROOT_NATIVE_REQUIRED');need(isinstance(plan_hash,str) and re.fullmatch('[a-f0-9]{64}',plan_hash),'PLAN_HASH');self.boundary(plan_hash,target)
  pub,praw,pstamp=public_file(PUBLIC);need(digest(pub)==PUBLIC_HASH,'SOURCE19_PUBLIC_DRIFT')
  config,craw,cstamp=public_file(CONFIG);need(DATABASE is not None and config.get('databasePath')==str(DATABASE),'FIXED_DATABASE_PATH_REQUIRED')
  registry,rraw,rstamp=public_file(REGISTRY);need(registry.get('schema')=='r16.native-ledgers.v1' and isinstance(registry.get('grants'),list) and len(registry['grants'])==1,'NATIVE_REGISTRY_SCOPE')
  reg=registry['grants'][0];need(reg.get('status')=='READY' and reg.get('directory')==str(STORE) and reg.get('grantId')=='r16-projects-daily' and reg.get('grantHash')==GRANT_HASH and type(reg.get('dev')) is int and reg['dev']>0 and type(reg.get('ino')) is int and reg['ino']>0,'NATIVE_REGISTRY_SCOPE')
  history=self.os.authenticated_app_history(plan_hash)
  a=read_native_tree((reg['dev'],reg['ino']));db=read_database();allids={**a[2],**db[2]};alldirs={**a[3],**db[3]}
  need(len(allids.values())==len(set(allids.values())) and len(alldirs.values())==len(set(alldirs.values())),'STORE_PATH_ALIAS');need(alldirs.get('native/grants/r16-projects-daily/dispatcher')==(reg['dev'],reg['ino']),'NATIVE_REGISTRATION_DRIFT');check_locks({**a[1],**db[1]},target);scan_writers(allids,alldirs,target);self.boundary(plan_hash,target)
  result=public_validation({'files':a[1],'publicConfig':pub,'history':history,'planHash':plan_hash,'now':int(time.time()*1000)})
  b=read_native_tree((reg['dev'],reg['ino']));db2=read_database();need(a==b and db==db2,'CHECKPOINT_CHANGED_DURING_CAPTURE');scan_writers({**b[2],**db2[2]},{**b[3],**db2[3]},target);self.boundary(plan_hash,target)
  for path,raw,stamp in [(PUBLIC,praw,pstamp),(CONFIG,craw,cstamp),(REGISTRY,rraw,rstamp)]:
   _,after,meta=public_file(path);need(raw==after and stamp==meta,'PUBLIC_BINDING_CHANGED_DURING_CAPTURE')
  out={'schema':'r16.source19-native-checkpoint.v1','completeRegisteredFileSet':True,'noForeignWriters':True,'noTemporaryFiles':True,'sqliteFilesEnumerated':True,'liveDatabaseOpened':False,'nativeLedgerRegistration':{'directory':str(STORE),'dev':reg['dev'],'ino':reg['ino'],'registryHash':sha(rraw)},'registeredRootsHash':digest({'directories':{k:{'dev':v[0],'ino':v[1],'mode':stat.S_IMODE(({**a[4],**db[4]})['dir:'+k][2]),'uid':({**a[4],**db[4]})['dir:'+k][3],'gid':({**a[4],**db[4]})['dir:'+k][4]} for k,v in alldirs.items()},'registryHash':sha(rraw)}),'files':{**a[0],**db[0]},**result}
  # Only hashes/metadata and original public signed operations leave this call.
  return out

CLOUD='VM-0-12-ubuntu'
APP_STORE=Path('/var/lib/r16-app/grants/r16-projects-daily/host')
CLOUD_PUBLIC=Path('/etc/r16-cloud/public-config.json')
APP_REGISTRY_DIRECTORY=Path('/var/lib/r16-cloud/ledger-registry')
APP_REGISTRY=APP_REGISTRY_DIRECTORY/(hashlib.sha256(b'"r16-projects-daily"').hexdigest()+'.json')
APP_REGISTRY_SPECS=[{'role':'app','path':str(APP_STORE)}, {'role':'bridge','path':'/var/lib/r16-bridge/grants/r16-projects-daily/bridge'}, {'role':'gateway','path':'/var/lib/r16-bridge/grants/r16-projects-daily/gateway'}]

def _read_app_registration():
 # Original initialize-cloud-ledger sealed record, never modified/initialized.
 fd=open_directory(APP_REGISTRY_DIRECTORY,uid=0,mode=0o700)
 try:raw,st,_=read_at(fd,APP_REGISTRY.name,uid=0,modes=(0o600,),max_bytes=32767)
 finally:os.close(fd)
 value=parse(raw);need(type(value) is dict and set(value)=={'schema','grantId','phase','specs','identities'} and value['schema']=='r16.cloud-ledger-registration.v1' and value['grantId']=='r16-projects-daily' and value['phase']=='SEALED' and value['specs']==APP_REGISTRY_SPECS,'SEALED_APP_REGISTRATION_SCOPE')
 identities=value['identities'];need(isinstance(identities,list) and len(identities)==3,'SEALED_APP_REGISTRATION_IDENTITIES');seen={};inodes=set()
 for r in identities:
  need(type(r) is dict and set(r)=={'role','dev','ino'} and r['role'] in ('app','bridge','gateway') and r['role'] not in seen and type(r['dev']) is int and r['dev']>0 and type(r['ino']) is int and r['ino']>0 and (r['dev'],r['ino']) not in inodes,'SEALED_APP_REGISTRATION_IDENTITIES');seen[r['role']]=(r['dev'],r['ino']);inodes.add((r['dev'],r['ino']))
 return raw,identity(st),seen['app']

def _app_history(admission,backend,h):
 need(os.geteuid()==0 and platform.node()==CLOUD,'FIXED_ROOT_CLOUD_REQUIRED')
 need(h is None or (isinstance(h,str) and re.fullmatch('[a-f0-9]{64}',h)),'PLAN_HASH')
 need(callable(getattr(admission,'require',None)) and callable(getattr(backend,'assert_app_history_safe',None)),'TRUSTED_APP_HISTORY_BACKEND_REQUIRED')
 operation='history-preflight' if h is None else 'history-collect'
 def boundary():
  admission.require(h,operation);need(backend.assert_app_history_safe(h) is None,'OS_CHECKPOINT_BOOLEAN_NOT_EVIDENCE')
 boundary();pub,praw,pstamp=public_file(CLOUD_PUBLIC);need(digest(pub)==PUBLIC_HASH,'SOURCE19_PUBLIC_DRIFT')
 regraw,regstamp,registered=_read_app_registration();fd=open_directory(APP_STORE,uid=1000,mode=0o700)
 try:
  dstat=os.fstat(fd);need((dstat.st_dev,dstat.st_ino)==registered,'SEALED_APP_DIRECTORY_IDENTITY_DRIFT')
  raw,before,_=read_at(fd,'state.json',uid=1000)
  result=public_validation({'operation':'collect-app','appHostState':parse(raw),'publicConfig':pub,'planHash':h if h is not None else '0'*64,'now':int(time.time()*1000)})
  boundary();again,after,_=read_at(fd,'state.json',uid=1000);need(raw==again and identity(before)==identity(after) and identity(dstat)==identity(os.fstat(fd)),'APP_HISTORY_CHANGED_DURING_CAPTURE')
 finally:os.close(fd)
 r2,s2,i2=_read_app_registration();need(regraw==r2 and regstamp==s2 and registered==i2,'SEALED_APP_REGISTRATION_CHANGED')
 _,p2,m2=public_file(CLOUD_PUBLIC);need(praw==p2 and pstamp==m2,'SOURCE19_PUBLIC_DRIFT');boundary()
 need(result.get('schema')=='r16.source19-native-transition.public-history.v1' and result.get('planHash')==(h if h is not None else '0'*64) and result.get('sourcePublicConfigHash')==PUBLIC_HASH and isinstance(result.get('historicalOperations'),list) and len(result['historicalOperations'])==2,'PUBLIC_PROJECTION_INVALID')
 if h is None:
  return {'schema':'r16.source19-native-transition.public-history-preflight.v1','sourcePublicConfigHash':PUBLIC_HASH,'historicalOperations':result['historicalOperations'],'atomicStoppedCheckpoint':False,'globalExecution':'UNPROVEN','authority':False}
 return result

def read_app_history_preflight(admission,os_backend):
 """Fixed active Source19 App only; proves public material, never a stopped DB."""
 return _app_history(admission,os_backend,None)
def collect_app_history(h,admission,backend):
 """Same-plan fixed App/Bridge stopped+owned96 verified by actual OS backend."""
 return _app_history(admission,backend,h)


def read_native_preflight(admission,backend):
 """Live Source19 public/history sample, NOT checkpoint B or writer closure.

 The actual fixed OS adapter checks source code/identity/singleton every time.
 Live Native FDs/SQLite are not presented as closed or globally quiescent; no DB
 bytes are opened and no foreign-writer or atomic stopped proof is returned.
 """
 need(os.geteuid()==0 and platform.node()==HOST,'FIXED_ROOT_NATIVE_REQUIRED')
 need(callable(getattr(admission,'require',None)) and callable(getattr(backend,'assert_native_preflight_safe',None)) and callable(getattr(backend,'authenticated_app_history',None)),'TRUSTED_NATIVE_PREFLIGHT_BACKEND_REQUIRED')
 def boundary():
  admission.require(None,'native-preflight');need(backend.assert_native_preflight_safe() is None,'OS_CHECKPOINT_BOOLEAN_NOT_EVIDENCE')
 boundary();pub,praw,pstamp=public_file(PUBLIC);need(digest(pub)==PUBLIC_HASH,'SOURCE19_PUBLIC_DRIFT');registry,rraw,rstamp=public_file(REGISTRY)
 need(registry.get('schema')=='r16.native-ledgers.v1' and isinstance(registry.get('grants'),list) and len(registry['grants'])==1,'NATIVE_REGISTRY_SCOPE');reg=registry['grants'][0]
 need(reg.get('status')=='READY' and reg.get('directory')==str(STORE) and reg.get('grantId')=='r16-projects-daily' and reg.get('grantHash')==GRANT_HASH and type(reg.get('dev')) is int and reg['dev']>0 and type(reg.get('ino')) is int and reg['ino']>0,'NATIVE_REGISTRY_SCOPE')
 history=backend.authenticated_app_history(None);a=read_native_tree((reg['dev'],reg['ino']));boundary()
 result=public_validation({'operation':'validate-native-preflight','files':a[1],'publicConfig':pub,'history':history,'now':int(time.time()*1000)})
 b=read_native_tree((reg['dev'],reg['ino']));need(a==b,'CHECKPOINT_CHANGED_DURING_CAPTURE');boundary()
 for p,raw,meta in [(PUBLIC,praw,pstamp),(REGISTRY,rraw,rstamp)]:
  _,other,m=public_file(p);need(raw==other and meta==m,'PUBLIC_BINDING_CHANGED_DURING_CAPTURE')
 return {'schema':'r16.source19-native-transition.native-preflight.v1','sourcePublicConfigHash':PUBLIC_HASH,'controlUnknownHash':result['controlUnknownHash'],'controlUnknownCount':result['controlUnknownCount'],'originalUnknown':result['originalUnknown'],'originalSignaturesAndLeasesVerified':True,'originalLeaseBindingsHash':result['originalLeaseBindingsHash'],'historicalOperations':result['historicalOperations'],'nativeLedgerRegistration':{'directory':str(STORE),'dev':reg['dev'],'ino':reg['ino'],'registryHash':sha(rraw)},'sampledNativeFileCount':len(a[0]),'nativeFilesHash':digest(a[0]),'atomicStoppedCheckpoint':False,'foreignWriterClosure':'NOT_PROVEN_LIVE_PREFLIGHT','sqliteFilesEnumerated':False,'liveDatabaseOpened':False,'globalExecution':'UNPROVEN','authority':False}
