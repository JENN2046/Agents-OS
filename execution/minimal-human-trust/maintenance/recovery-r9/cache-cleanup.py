"""One native-approved exact APT lists cleanup; no CLI or general path facility.
Indexes can be reconstructed with apt-get update; this module never runs it.
No raw index backup/upload is performed. Historical packages/ledgers are untouched.
"""
import contextlib,fcntl,hashlib,json,os,pwd,re,stat,time
from pathlib import Path
LISTS=Path('/var/lib/apt/lists')
JOURNAL=Path('/var/lib/r16-maintenance/recovery-r9-cache-prep')
RESERVE=256*1024*1024
class Refused(Exception):
 def __init__(self,code):self.code=code;super().__init__(code)
def need(value,code):
 if not value:raise Refused(code)
def canonical(value):return json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()
def digest(value):return hashlib.sha256(canonical(value)).hexdigest()
def now_ms():return time.time_ns()//1000000
def root():need(os.getuid()==os.geteuid()==0,'CACHE_NATIVE_ROOT_REQUIRED')
def stamp(s):return {'dev':str(s.st_dev),'ino':str(s.st_ino),'uid':s.st_uid,'gid':s.st_gid,'mode':stat.S_IMODE(s.st_mode),'nlink':s.st_nlink,'bytes':s.st_size,'allocatedBytes':s.st_blocks*512,'mtimeNs':str(s.st_mtime_ns),'ctimeNs':str(s.st_ctime_ns)}
def directory(path):
 cursor=Path('/')
 for bit in Path(path).parts[1:]:
  cursor/=bit;s=cursor.lstat();need(stat.S_ISDIR(s.st_mode) and s.st_uid==0 and not s.st_mode&0o022,'CACHE_DIRECTORY_REFUSED')
 return os.open(path,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
def read_at(parent,name):
 fd=os.open(name,os.O_RDONLY|os.O_NONBLOCK|os.O_NOFOLLOW,dir_fd=parent)
 try:
  a=os.fstat(fd);need(stat.S_ISREG(a.st_mode) and a.st_uid==0 and a.st_nlink==1 and stat.S_IMODE(a.st_mode) in (0o600,0o644),'CACHE_INDEX_METADATA_REFUSED')
  h=hashlib.sha256();total=0
  while True:
   block=os.read(fd,1024*1024)
   if not block:break
   h.update(block);total+=len(block)
  need(total==a.st_size and stamp(a)==stamp(os.fstat(fd))==stamp(os.stat(name,dir_fd=parent,follow_symlinks=False)),'CACHE_INDEX_CHANGED')
  return {**stamp(a),'sha256':h.hexdigest()}
 finally:os.close(fd)
def snapshot_fd(fd):
 a=os.fstat(fd);rows={};names=sorted(os.listdir(fd))
 for name in sorted(names):
  if name in ('partial','auxfiles'):
   s=os.stat(name,dir_fd=fd,follow_symlinks=False);need(stat.S_ISDIR(s.st_mode) and s.st_uid in (0,pwd.getpwnam('_apt').pw_uid) and not s.st_mode&0o022,'CACHE_PRESERVED_DIRECTORY_REFUSED');continue
  if name=='lock':
   s=os.stat(name,dir_fd=fd,follow_symlinks=False);need(stat.S_ISREG(s.st_mode) and s.st_uid==0 and s.st_nlink==1 and stat.S_IMODE(s.st_mode) in (0o600,0o640),'CACHE_LOCK_REFUSED');continue
  need(re.fullmatch(r'mirrors\.tencentyun\.com_ubuntu_dists_noble(?:-backports|-security|-updates)?_(?:InRelease|(?:main|multiverse|restricted|universe)_(?:binary-amd64_Packages|cnf_Commands-amd64|dep11_Components-amd64\.yml\.gz|i18n_Translation-en))',name) is not None,'CACHE_UNREVIEWED_INDEX_NAME');rows[name]=read_at(fd,name)
 need('lock' in names and names==sorted(os.listdir(fd)) and stamp(a)==stamp(os.fstat(fd)),'CACHE_DIRECTORY_CHANGED')
 return {'schema':'r16.r9.exact-apt-index-inventory.v1','directory':{'dev':str(a.st_dev),'ino':str(a.st_ino),'uid':a.st_uid,'gid':a.st_gid,'mode':stat.S_IMODE(a.st_mode)},'files':rows,'logicalBytes':sum(x['bytes'] for x in rows.values()),'allocatedBytes':sum(x['allocatedBytes'] for x in rows.values()),'preservedNames':['lock','partial','auxfiles'],'rebuildMethod':'apt-get update (not executed here)','rawBackedUp':False}
def prepare():
 root();fd=directory(LISTS)
 try:
  value=snapshot_fd(fd);return {**value,'inventoryHash':digest(value)}
 finally:os.close(fd)
def verify_inventory(value):
 need(type(value) is dict and value.get('schema')=='r16.r9.exact-apt-index-inventory.v1','CACHE_INVENTORY_REQUIRED')
 need(value.get('inventoryHash')==digest({k:v for k,v in value.items() if k!='inventoryHash'}),'CACHE_INVENTORY_HASH_DRIFT')
def space_budget(inventory,root_allocated,target_allocated,*,filesystem_paths,credit_cleanup=True):
 verify_inventory(inventory);need(type(root_allocated) is int and type(target_allocated) is int and root_allocated>=0 and target_allocated>=0,'CACHE_BUDGET_REFUSED')
 dev=os.stat(LISTS).st_dev
 need(all(os.stat(p).st_dev==dev for p in filesystem_paths),'CACHE_SPACE_FILESYSTEM_MISMATCH')
 s=os.statvfs(LISTS);available=s.f_bavail*s.f_frsize;credited=inventory['allocatedBytes'] if credit_cleanup else 0;remaining=available+credited-root_allocated-target_allocated
 need(remaining>=RESERVE,'INSUFFICIENT_UNRESERVED_ROOT_SPACE')
 return {'availableBytes':available,'allocatedCleanableBytes':inventory['allocatedBytes'],'creditedCleanupBytes':credited,'allocatedNewRootBytes':root_allocated,'allocatedTargetGrowthBytes':target_allocated,'projectedRemainingBytes':remaining,'requiredReserveBytes':RESERVE,'usesRootReservedBlocks':False}
def authority_valid(authority,pending_hash,clock):
 need(type(authority) is dict and authority.get('schema')=='r16.r9.native-install-confirmation.v1' and authority.get('pendingHash')==pending_hash and re.fullmatch('[a-f0-9]{32}',authority.get('nonce','')) is not None,'CACHE_EXACT_NATIVE_CONFIRMATION_REQUIRED')
 a,z=authority.get('issuedAt'),authority.get('expiresAt');need(type(a) is int and type(z) is int and z-a==300000 and a<=clock()<z,'CACHE_NATIVE_CONFIRMATION_EXPIRED')
def assert_fresh(cap):
 root();need(re.fullmatch('[a-f0-9]{64}',cap) is not None,'CACHE_CAPSULE_HASH_REQUIRED')
 if os.path.lexists(JOURNAL):
  fd=directory(JOURNAL)
  try:need(stat.S_IMODE(os.fstat(fd).st_mode)==0o700,'CACHE_JOURNAL_DIRECTORY_REFUSED')
  finally:os.close(fd)
 for path in (JOURNAL/cap,JOURNAL/(cap+'.pending'),JOURNAL/('.'+cap+'.pending')):
  need(not os.path.lexists(path),'CACHE_PRIOR_ATTEMPT_REQUIRES_READONLY_REVIEW')
def journal_directory(cap):
 need(re.fullmatch('[a-f0-9]{64}',cap) is not None,'CACHE_CAPSULE_HASH_REQUIRED')
 for path in (JOURNAL,JOURNAL/cap):
  parent=directory(path.parent)
  try:
   try:os.mkdir(path.name,0o700,dir_fd=parent)
   except FileExistsError:pass
   fd=os.open(path.name,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW,dir_fd=parent);s=os.fstat(fd);need(s.st_uid==0 and stat.S_IMODE(s.st_mode)==0o700,'CACHE_JOURNAL_DIRECTORY_REFUSED');os.fsync(parent);os.close(fd)
  finally:os.close(parent)
 return directory(JOURNAL/cap)
def persist(fd,name,value):
 raw=canonical(value);out=os.open(name,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600,dir_fd=fd)
 try:
  os.fchmod(out,0o600);offset=0
  while offset<len(raw):
   written=os.write(out,raw[offset:]);need(written>0,'CACHE_JOURNAL_WRITE_FAILED');offset+=written
  os.fsync(out)
 finally:os.close(out)
 os.fsync(fd)
@contextlib.contextmanager
def apt_lock(fd):
 lock=os.open('lock',os.O_RDWR|os.O_NOFOLLOW|os.O_NONBLOCK,dir_fd=fd)
 try:
  s=os.fstat(lock);need(stat.S_ISREG(s.st_mode) and s.st_uid==0 and s.st_nlink==1 and stat.S_IMODE(s.st_mode) in (0o600,0o640),'CACHE_LOCK_REFUSED')
  fcntl.lockf(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  need(stamp(s)==stamp(os.stat('lock',dir_fd=fd,follow_symlinks=False)),'CACHE_LOCK_CHANGED');yield
 finally:os.close(lock)
def execute(expected,authority,pending_hash,cap,*,pending,clock=now_ms,fault=lambda point:None):
 root();verify_inventory(expected);need(type(pending) is dict and digest(pending)==pending_hash,'CACHE_NATIVE_PENDING_DIGEST_DRIFT');authority_valid(authority,pending_hash,clock);fd=directory(LISTS)
 try:
  with apt_lock(fd):
   current=snapshot_fd(fd);need(digest(current)==expected['inventoryHash'],'CACHE_PREPARED_INVENTORY_CHANGED')
   authority_valid(authority,pending_hash,clock);j=journal_directory(cap)
   try:
    need(not os.listdir(j),'CACHE_PRIOR_ATTEMPT_REQUIRES_READONLY_REVIEW')
    persist(j,'INTENT.json',{'schema':'r16.r9.exact-cache-cleanup-intent.v1','capsuleHash':cap,'pendingHash':pending_hash,'authority':authority,'pending':pending,'inventory':expected,'noRawBackup':True});fault('intent')
    removed=[]
    for n,(name,row) in enumerate(sorted(expected['files'].items())):
     need(read_at(fd,name)==row,'CACHE_FILE_CAS_REFUSED');authority_valid(authority,pending_hash,clock)
     persist(j,f'{n:06d}-DELETE_INTENT.json',{'name':name,'metadata':row});fault('delete-intent')
     # Recheck effect authority and inode at the actual unlink boundary.
     need(stamp(os.stat(name,dir_fd=fd,follow_symlinks=False))=={k:v for k,v in row.items() if k!='sha256'},'CACHE_LAST_INODE_CAS_REFUSED');authority_valid(authority,pending_hash,clock)
     os.unlink(name,dir_fd=fd);os.fsync(fd);fault('delete-effect')
     persist(j,f'{n:06d}-REMOVED.json',{'name':name,'sha256':row['sha256'],'allocatedBytes':row['allocatedBytes']});removed.append(name)
    after=snapshot_fd(fd);need(after['files']=={} and after['directory']==expected['directory'],'CACHE_FINAL_CONTENT_UNPROVEN')
    result={'schema':'r16.r9.exact-cache-cleanup-receipt.v1','status':'EXACT_APT_INDEXES_REMOVED','inventoryHash':expected['inventoryHash'],'capsuleHash':cap,'pendingHash':pending_hash,'removedFiles':len(removed),'removedLogicalBytes':expected['logicalBytes'],'removedAllocatedBytes':expected['allocatedBytes'],'preservedNames':['lock','partial','auxfiles'],'rebuildMethod':expected['rebuildMethod'],'businessFilesTouched':False,'rawBackedUp':False}
    authority_valid(authority,pending_hash,clock);persist(j,'COMPLETED.json',result);return result
   finally:os.close(j)
 finally:os.close(fd)
