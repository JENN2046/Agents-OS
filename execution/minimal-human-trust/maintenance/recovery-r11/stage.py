"""Ordinary-user R11 staging. Cloud copies one exact public candidate without changing the old one.

No root, service, cache cleanup, credentials inspection or protected install.
The old ROOT/STATE package and all historical maintenance records are untouched.
"""
import argparse,base64,hashlib,json,os,shlex,stat,subprocess
from pathlib import Path
import importlib.util
_spec=importlib.util.spec_from_file_location('r11_stage_constants',Path(__file__).with_name('constants.py'));C=importlib.util.module_from_spec(_spec);_spec.loader.exec_module(C)
SOURCE=C.OUT
OLD_CLOUD='/home/ubuntu/r16-maintenance-recovered-r10-r2-candidate'
NEW_CLOUD=C.CLOUD_SOURCE
OLD_CAP='8a48d26dc3d44b3bccc868c3a2da34eaeb729416babafa0d7db45183dba2cb59'
SSH=('/usr/bin/ssh','-F','/dev/null','-T','-o','BatchMode=yes','-o','IdentityAgent=none','-o','IdentitiesOnly=yes','-i','/home/jenn/.ssh/TXY_159_75_139_246_ed25519','-o','StrictHostKeyChecking=yes','-o','UpdateHostKeys=no','-o','UserKnownHostsFile=/etc/r16-owner/ssh_known_hosts','-o','GlobalKnownHostsFile=/dev/null','-o','ConnectTimeout=8','-o','ClearAllForwardings=yes','ubuntu@159.75.139.246')
REMOTE=r'''
import base64,hashlib,json,os,stat,sys
from pathlib import Path
def need(v,c):
 if not v:raise ValueError(c)
def sha(b):return hashlib.sha256(b).hexdigest()
def canon(v):return json.dumps(v,sort_keys=True,separators=(',',':')).encode()
need(os.getuid()==os.geteuid()==1000,'ORDINARY_UID1000_REQUIRED')
data=json.load(sys.stdin);old=Path(OLD);new=Path(NEW);f=json.loads(base64.b64decode(data['manifest'],validate=True));need(sha(base64.b64decode(data['manifest']))==data['capsuleHash'] and len(f['files'])==19 and len(f['payloadFiles'])==12600,'R11_CAPSULE_OR_COUNTS_DRIFT')
need(f.get('planTemplate',{}).get('assetReuse')==ASSET_REUSE,'STAGED_ASSET_REUSE_SCOPE_DRIFT')
def name(n):need(isinstance(n,str) and not n.startswith('/') and '\\' not in n and all(x not in ('','.','..') for x in n.split('/')),'STAGE_RELATIVE_PATH_REFUSED');return n
def safe_dir(p,create=False,private=False):
 cur=Path('/')
 for bit in p.parts[1:]:
  cur/=bit
  if create and cur==p:
   try:cur.mkdir(mode=0o755);cur.chmod(0o755)
   except FileExistsError:pass
  s=cur.lstat();need(stat.S_ISDIR(s.st_mode) and s.st_uid in (0,1000) and not s.st_mode&0o022,'STAGE_PARENT_REFUSED')
 need(p.lstat().st_uid==1000 and stat.S_IMODE(p.lstat().st_mode) in ((0o700,0o755) if private else (0o755,)),'STAGE_CANDIDATE_OWNER_REFUSED')
def read(p,maximum=67108864):
 fd=os.open(p,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
 try:
  a=os.fstat(fd);need(stat.S_ISREG(a.st_mode) and a.st_uid==1000 and a.st_nlink==1 and not a.st_mode&0o7022 and a.st_size<=maximum,'STAGE_REGULAR_FILE_REFUSED');raw=b''
  while len(raw)<=maximum:
   b=os.read(fd,min(1048576,maximum+1-len(raw)))
   if not b:break
   raw+=b
  stamp=lambda s:(s.st_dev,s.st_ino,s.st_mode,s.st_uid,s.st_gid,s.st_nlink,s.st_size,s.st_mtime_ns,s.st_ctime_ns)
  need(len(raw)==a.st_size and stamp(a)==stamp(os.fstat(fd))==stamp(p.lstat()),'STAGE_FILE_CHANGED');return raw,stat.S_IMODE(a.st_mode)
 finally:os.close(fd)
safe_dir(old);safe_dir(new,True)
old_freeze=json.loads(read(old/'SOURCE_FREEZE.json')[0]);need(sha(read(old/'SOURCE_FREEZE.json')[0])==OLD_CAP and old_freeze['payloadFiles']==f['payloadFiles'],'EXACT_OLD_PUBLIC_PACKAGE_REQUIRED')
old_sources={}
for n,pin in old_freeze['files'].items():
 raw,mode=read(old/name(n));need(sha(raw)==pin and mode==0o644,'OLD_PUBLIC_RUNTIME_DRIFT');old_sources[n]=(raw,mode)
def source_closure(root,freeze,with_package,freeze_optional=False):
 actual=set()
 def fail(error):raise error
 for directory,children,files in os.walk(root,followlinks=False,onerror=fail):
  safe_dir(Path(directory))
  for n in children:need(stat.S_ISDIR((Path(directory)/n).lstat().st_mode),'CANDIDATE_SYMLINK_DIRECTORY_REFUSED')
  for n in files:actual.add(str((Path(directory)/n).relative_to(root)))
 expected=set(freeze['files'])
 if not freeze_optional or os.path.lexists(root/'SOURCE_FREEZE.json'):expected|={'SOURCE_FREEZE.json'}
 if freeze_optional and os.path.lexists(root/'SOURCE_FREEZE.json'):need(read(root/'SOURCE_FREEZE.json')==(base64.b64decode(data['manifest'],validate=True),0o644),'FOREIGN_STAGED_MANIFEST_REFUSED')
 if with_package:expected|={'package/'+n for n in freeze['payloadFiles']}
 need(actual==expected,'CANDIDATE_COMPLETE_FILE_SET_DRIFT')
source_closure(old,old_freeze,os.path.lexists(old/'package'))
package=old/'package';safe_dir(package)
def verify_package(package,private=False):
 actual=set();directory_pins={}
 def fail(e):raise e
 for directory,children,files in os.walk(package,followlinks=False,onerror=fail):
  p=Path(directory);safe_dir(p,private=private);s=p.lstat();directory_pins[str(p.relative_to(package))]=(s.st_dev,s.st_ino,s.st_uid,s.st_gid,stat.S_IMODE(s.st_mode))
  for n in children:need(stat.S_ISDIR((p/n).lstat().st_mode),'PUBLIC_PACKAGE_SYMLINK_DIRECTORY_REFUSED')
  for n in files:actual.add(str((p/n).relative_to(package)))
 need(actual==set(f['payloadFiles']),'PUBLIC_PACKAGE_FILE_SET_DRIFT');inventory=json.loads(read(package/'metadata/PAYLOAD_INVENTORY.json')[0]);closure={}
 for n,pin in f['payloadFiles'].items():
  raw,mode=read(package/name(n));expected=inventory[n[8:]]['mode'] if n.startswith('payload/') else 0o644
  need(sha(raw)==pin and mode==expected,'PUBLIC_PACKAGE_BYTE_OR_MODE_DRIFT');closure[n]={'sha256':pin,'mode':mode,'bytes':len(raw)}
 need(sha(canon(closure))=='c7bc7ba7fa3fb0fbc5099ef28709059a5116a5943cc9aecd75bc17cb1abbafd8','INDEPENDENT_PUBLIC_PACKAGE_CLOSURE_DRIFT')
 return closure,directory_pins
closure,directory_pins=verify_package(package)
def emit(p,raw,mode=0o644):
 cursor=new
 for bit in p.parent.relative_to(new).parts:cursor/=bit;safe_dir(cursor,True)
 try:fd=os.open(p,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,mode)
 except FileExistsError:need(read(p)==(raw,mode),'FOREIGN_STAGED_SOURCE_REFUSED');return
 try:
  os.fchmod(fd,mode);offset=0
  while offset<len(raw):offset+=os.write(fd,raw[offset:])
  os.fsync(fd)
 finally:os.close(fd)
# Reserve the actual ordinary copy plus the later bounded root metadata budget.
v=os.statvfs(new);block=v.f_frsize;rounded=lambda n:((n+block-1)//block)*block
copy_budget=sum(rounded(row['bytes']) for row in closure.values())+block*len(directory_pins)+16*1024*1024
need(v.f_bavail*block>=copy_budget+64*1024*1024+256*1024*1024,'ORDINARY_COPY_DISK_BUDGET_REFUSED')
need(set(data['sources'])==set(f['files']),'STAGED_RUNTIME_SET_DRIFT')
for n,pin in f['files'].items():
 raw=base64.b64decode(data['sources'][name(n)],validate=True);need(sha(raw)==pin,'STAGED_RUNTIME_PIN_DRIFT');emit(new/n,raw)
for n,row in sorted(closure.items()):
 raw,mode=read(package/name(n));need(sha(raw)==row['sha256'] and len(raw)==row['bytes'] and mode==row['mode'],'SOURCE_COPY_DRIFT');emit(new/'package'/n,raw,mode)
# All old directories/files remain in place; no copy can be a hard link.
for n in closure:
 a=(old/'package'/n).lstat();b=(new/'package'/n).lstat();need((a.st_dev,a.st_ino)!=(b.st_dev,b.st_ino),'STAGED_COPY_IS_OLD_INODE')
after=(new/'package').lstat()
closure,_=verify_package(new/'package')
for n,pin in f['files'].items():need(sha(read(new/name(n))[0])==pin,'FINAL_STAGED_RUNTIME_DRIFT')
source_closure(new,f,True,freeze_optional=True)
source_closure(old,old_freeze,True)
for n,(raw,mode) in old_sources.items():need(read(old/name(n))==(raw,mode),'OLD_PUBLIC_RUNTIME_CHANGED')
emit(new/'SOURCE_FREEZE.json',base64.b64decode(data['manifest'],validate=True))
need(read(new/'SOURCE_FREEZE.json')==(base64.b64decode(data['manifest'],validate=True),0o644),'FINAL_STAGED_MANIFEST_DRIFT')
need(verify_package(old/'package')==(closure,directory_pins),'OLD_PUBLIC_PACKAGE_CHANGED')
source_closure(new,f,True)
source_closure(old,old_freeze,True)
for n,(raw,mode) in old_sources.items():need(read(old/name(n))==(raw,mode),'OLD_PUBLIC_RUNTIME_CHANGED')
print(json.dumps({'status':'R11_ORDINARY_PUBLIC_STAGE_VERIFIED','capsuleHash':data['capsuleHash'],'packageFiles':12600,'packageClosureHash':sha(canon(closure)),'publicPackageMoved':False,'ordinaryPackageCopied':True,'ordinaryCopyBudgetBytes':copy_budget,'publicDirectoriesNormalized':0,'directoryMetadataBeforeHash':sha(canon(directory_pins)),'packageDirectoryDev':str(after.st_dev),'packageDirectoryInode':str(after.st_ino),'protectedPathsWritten':False,'oldSourceFilesPreserved':True,'sourceUserDirectory':OLD,'destinationUserDirectory':NEW,'rootActions':False,'rollbackEngineeringMove':'Old complete candidate is unchanged. Preserve or remove only the separately verified ordinary R11 candidate under a distinct cleanup scope; no service action.'},sort_keys=True))
'''
def local_inputs(cap):
 def need(value,code):
  if not value:raise ValueError(code)
 def sha(raw):return hashlib.sha256(raw).hexdigest()
 def canonical(value):return json.dumps(value,sort_keys=True,separators=(',',':')).encode()
 def relative(name):
  need(isinstance(name,str) and name and not name.startswith('/') and '\\' not in name and all(x not in ('','.','..') for x in name.split('/')),'LOCAL_RELATIVE_PATH_REFUSED');return name
 def read(path,limit=64*1024*1024):
  fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
  try:
   a=os.fstat(fd);need(stat.S_ISREG(a.st_mode) and a.st_uid==os.getuid() and a.st_nlink==1 and not a.st_mode&0o7022 and a.st_size<=limit,'LOCAL_REGULAR_FILE_REFUSED');raw=b''
   while len(raw)<=limit:
    block=os.read(fd,min(1048576,limit+1-len(raw)))
    if not block:break
    raw+=block
   stamp=lambda v:(v.st_dev,v.st_ino,v.st_mode,v.st_uid,v.st_gid,v.st_nlink,v.st_size,v.st_mtime_ns,v.st_ctime_ns)
   need(len(raw)==a.st_size and stamp(a)==stamp(os.fstat(fd))==stamp(path.lstat()),'LOCAL_FILE_CHANGED');return raw,stat.S_IMODE(a.st_mode)
  finally:os.close(fd)
 raw,mode=read(SOURCE/'SOURCE_FREEZE.json');need(sha(raw)==cap and mode==0o644,'EXACT_REVIEWED_CAPSULE_REQUIRED');f=json.loads(raw)
 need(len(f['files'])==19 and len(f['payloadFiles'])==12600 and f.get('planTemplate',{}).get('assetReuse')==C.ASSET_REUSE,'LOCAL_CAPSULE_SCOPE_DRIFT')
 actual=set()
 def denied(error):raise error
 for directory,children,files in os.walk(SOURCE,followlinks=False,onerror=denied):
  p=Path(directory);v=p.lstat();need(stat.S_ISDIR(v.st_mode) and v.st_uid==os.getuid() and stat.S_IMODE(v.st_mode)==0o755,'LOCAL_CANDIDATE_DIRECTORY_REFUSED')
  for name in children:need(stat.S_ISDIR((p/name).lstat().st_mode),'LOCAL_CANDIDATE_SYMLINK_REFUSED')
  for name in files:actual.add(str((p/name).relative_to(SOURCE)))
 need(actual==set(f['files'])|{'SOURCE_FREEZE.json'}|{'package/'+n for n in f['payloadFiles']},'LOCAL_CANDIDATE_FILE_SET_DRIFT')
 sources={}
 for name,pin in f['files'].items():
  value,mode=read(SOURCE/relative(name));need(sha(value)==pin and mode==0o644,'RUNTIME_SOURCE_DRIFT');sources[name]=value
 inventory=json.loads(read(SOURCE/'package/metadata/PAYLOAD_INVENTORY.json')[0]);closure={}
 for name,pin in f['payloadFiles'].items():
  value,mode=read(SOURCE/'package'/relative(name));expected=inventory[name[8:]]['mode'] if name.startswith('payload/') else 0o644
  need(sha(value)==pin and mode==expected,'LOCAL_PACKAGE_BYTE_OR_MODE_DRIFT');closure[name]={'sha256':pin,'mode':mode,'bytes':len(value)}
 need(sha(canonical(closure))==C.PACKAGE_CLOSURE,'LOCAL_PACKAGE_CLOSURE_DRIFT')
 return {'capsuleHash':cap,'manifest':base64.b64encode(raw).decode(),'sources':{n:base64.b64encode(value).decode() for n,value in sources.items()}}
def stage(cap):
 if os.getuid()!=1000 or os.geteuid()!=1000:raise SystemExit('ORDINARY_USER_REQUIRED')
 data=local_inputs(cap)
 code='OLD='+repr(OLD_CLOUD)+'\nNEW='+repr(NEW_CLOUD)+'\nOLD_CAP='+repr(OLD_CAP)+'\nASSET_REUSE='+repr(C.ASSET_REUSE)+'\n'+REMOTE
 r=subprocess.run((*SSH,shlex.join(('/usr/bin/python3','-I','-B','-c',code))),input=json.dumps(data).encode(),stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=150)
 if r.returncode:raise SystemExit('ORDINARY_STAGE_REFUSED_NO_NATIVE_EXECUTION')
 print(r.stdout.decode().strip())
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('capsule_sha256');a=p.parse_args();stage(a.capsule_sha256)
