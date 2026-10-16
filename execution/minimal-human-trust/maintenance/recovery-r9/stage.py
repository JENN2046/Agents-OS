"""Ordinary-user R9 staging. Cloud reuses one exact public candidate by rename.

No root, service, cache cleanup, credentials inspection or protected install.
The old ROOT/STATE package and all historical maintenance records are untouched.
"""
import argparse,base64,hashlib,json,os,shlex,subprocess
from pathlib import Path
SOURCE=Path('/home/jenn/AGENTS_OS_Workspace/ops/g1d-native-recovery-reconnect-20261014-r1/r15-backport/maintenance-recovered-r9')
OLD_CLOUD='/home/ubuntu/r16-maintenance-first-stop-r8-r3-candidate'
NEW_CLOUD='/home/ubuntu/r16-maintenance-recovered-r9-candidate'
OLD_CAP='e7c8dbe016c2a36f0a1929ab52d5d0ad19ca7217c505f6c138cc64f32c595dad'
SSH=('/usr/bin/ssh','-F','/dev/null','-T','-o','BatchMode=yes','-o','IdentityAgent=none','-o','IdentitiesOnly=yes','-i','/home/jenn/.ssh/TXY_159_75_139_246_ed25519','-o','StrictHostKeyChecking=yes','-o','UpdateHostKeys=no','-o','UserKnownHostsFile=/etc/r16-owner/ssh_known_hosts','-o','GlobalKnownHostsFile=/dev/null','-o','ConnectTimeout=8','-o','ClearAllForwardings=yes','ubuntu@159.75.139.246')
REMOTE=r'''
import base64,ctypes,hashlib,json,os,stat,sys
from pathlib import Path
def need(v,c):
 if not v:raise ValueError(c)
def sha(b):return hashlib.sha256(b).hexdigest()
def canon(v):return json.dumps(v,sort_keys=True,separators=(',',':')).encode()
need(os.getuid()==os.geteuid()==1000,'ORDINARY_UID1000_REQUIRED')
data=json.load(sys.stdin);old=Path(OLD);new=Path(NEW);f=json.loads(base64.b64decode(data['manifest'],validate=True));need(sha(base64.b64decode(data['manifest']))==data['capsuleHash'] and len(f['files'])==19 and len(f['payloadFiles'])==12600,'R9_CAPSULE_OR_COUNTS_DRIFT')
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
package=new/'package' if os.path.lexists(new/'package') else old/'package';safe_dir(package,private=True)
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
closure,directory_pins=verify_package(package,private=True)
def emit(p,raw):
 p.parent.mkdir(parents=True,exist_ok=True,mode=0o755)
 cursor=p.parent
 while cursor!=new:safe_dir(cursor);cursor=cursor.parent
 try:fd=os.open(p,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o644)
 except FileExistsError:need(read(p)==(raw,0o644),'FOREIGN_STAGED_SOURCE_REFUSED');return
 try:
  os.fchmod(fd,0o644);offset=0
  while offset<len(raw):offset+=os.write(fd,raw[offset:])
  os.fsync(fd)
 finally:os.close(fd)
for n,pin in f['files'].items():
 raw=base64.b64decode(data['sources'][name(n)],validate=True);need(sha(raw)==pin,'STAGED_RUNTIME_PIN_DRIFT');emit(new/n,raw)
before=package.lstat();moved=False
if package==old/'package':
 oldfd=os.open(old,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW);newfd=os.open(new,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
 try:
  need(os.stat('package',dir_fd=oldfd,follow_symlinks=False).st_ino==before.st_ino,'PUBLIC_PACKAGE_DIRECTORY_CHANGED')
  rename=ctypes.CDLL(None,use_errno=True).renameat2;rename.argtypes=(ctypes.c_int,ctypes.c_char_p,ctypes.c_int,ctypes.c_char_p,ctypes.c_uint);rename.restype=ctypes.c_int
  need(rename(oldfd,b'package',newfd,b'package',1)==0,'PUBLIC_PACKAGE_NOREPLACE_MOVE_REFUSED');os.fsync(oldfd);os.fsync(newfd);moved=True
 finally:os.close(oldfd);os.close(newfd)
else:need(not os.path.lexists(old/'package'),'DUPLICATED_OR_AMBIGUOUS_PUBLIC_PACKAGE')
after=(new/'package').lstat();need((before.st_dev,before.st_ino)==(after.st_dev,after.st_ino),'PUBLIC_PACKAGE_MOVE_IDENTITY_DRIFT')
normalized=0
for relative,pin in directory_pins.items():
 p=new/'package'/relative;safe_dir(p,private=True);fd=os.open(p,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
 try:
  s=os.fstat(fd);named=p.lstat();current=(s.st_dev,s.st_ino,s.st_uid,s.st_gid,stat.S_IMODE(s.st_mode))
  need(current==pin and (named.st_dev,named.st_ino)==(s.st_dev,s.st_ino),'PUBLIC_PACKAGE_DIRECTORY_CHANGED')
  if pin[-1]==0o700:os.fchmod(fd,0o755);os.fsync(fd);normalized+=1
 finally:os.close(fd)
closure,_=verify_package(new/'package')
for n,pin in f['files'].items():need(sha(read(new/name(n))[0])==pin,'FINAL_STAGED_RUNTIME_DRIFT')
emit(new/'SOURCE_FREEZE.json',base64.b64decode(data['manifest'],validate=True))
need(read(new/'SOURCE_FREEZE.json')==(base64.b64decode(data['manifest'],validate=True),0o644),'FINAL_STAGED_MANIFEST_DRIFT')
print(json.dumps({'status':'R9_ORDINARY_PUBLIC_STAGE_VERIFIED','capsuleHash':data['capsuleHash'],'packageFiles':12600,'packageClosureHash':sha(canon(closure)),'publicPackageMoved':moved,'publicDirectoriesNormalized':normalized,'packageDirectoryDev':str(after.st_dev),'packageDirectoryInode':str(after.st_ino),'oldProtectedRootAndStateUnchanged':True,'sourceUserDirectory':OLD,'destinationUserDirectory':NEW,'rootActions':False,'rollbackEngineeringMove':'If no native bootstrap has occurred, verify the same complete closure and rename package back with NOREPLACE; no service action.'},sort_keys=True))
'''
def stage(cap):
 if os.getuid()!=1000 or os.geteuid()!=1000:raise SystemExit('ORDINARY_USER_REQUIRED')
 raw=(SOURCE/'SOURCE_FREEZE.json').read_bytes()
 if hashlib.sha256(raw).hexdigest()!=cap:raise SystemExit('EXACT_REVIEWED_CAPSULE_REQUIRED')
 f=json.loads(raw);sources={n:(SOURCE/n).read_bytes() for n in f['files']}
 for n,b in sources.items():
  if hashlib.sha256(b).hexdigest()!=f['files'][n]:raise SystemExit('RUNTIME_SOURCE_DRIFT')
 data={'capsuleHash':cap,'manifest':base64.b64encode(raw).decode(),'sources':{n:base64.b64encode(b).decode() for n,b in sources.items()}}
 code='OLD='+repr(OLD_CLOUD)+'\nNEW='+repr(NEW_CLOUD)+'\nOLD_CAP='+repr(OLD_CAP)+'\n'+REMOTE
 r=subprocess.run((*SSH,shlex.join(('/usr/bin/python3','-I','-B','-c',code))),input=json.dumps(data).encode(),stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=60)
 if r.returncode:raise SystemExit('ORDINARY_STAGE_REFUSED_NO_NATIVE_EXECUTION: '+r.stderr.decode()[-300:])
 print(r.stdout.decode().strip())
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('capsule_sha256');a=p.parse_args();stage(a.capsule_sha256)
