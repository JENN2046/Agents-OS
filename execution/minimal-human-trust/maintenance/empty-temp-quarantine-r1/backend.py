"""Exact empty-artifact relocation. Only native-admitted, separately sealed entry.

No CLI, generic path, deletion, signal, restart or business API. The parent
serializes a durable intent before each relocation; unknown effects are only
observed. Private normal-file bytes exist in memory during descriptor reads and
unchanged R8 validation; they are never returned or persisted by this module.
"""
import ctypes
import errno
import hashlib
import os
from pathlib import Path
import stat
import sys
import time

R = sys.modules['r8_linux_backend']
L = sys.modules['r8_ledger_checkpoint']
STATE = Path('/var/lib/r16-maintenance/empty-temp-quarantine-r1')
FENCE = Path('/run/systemd/system/r16-app.service.d/94-r16-empty-temp-quarantine.conf')
CONDITION = Path('/run/r16-empty-temp-quarantine/source-app-start-not-authorized')
QUARANTINE = STATE / 'quarantine'
DESTINATION = 'original-empty.next'
ARTIFACT = '.next-6f6c6887-4fa7-450a-a199-683eadfde1b5'
EMPTY_SHA = hashlib.sha256(b'').hexdigest()
EXPECTED = {'dev':64770,'ino':1039403,'uid':1000,'gid':1001,'mode':0o600,
            'nlink':1,'bytes':0,'mtimeNs':'1792126254419345897',
            'ctimeNs':'1792126254419345897','sha256':EMPTY_SHA}
SOURCE_APP = {'host':'VM-0-12-ubuntu','unit':'r16-app.service','pid':1442662,
 'startTicks':'188708415','bootId':'cbe93e9f-9f2d-4139-8b94-3ffbcc8e43fe',
 'invocationId':'bd1db422e3404b6984961c5215374e98','nRestarts':0}

Refused = R.Refused
need = R.need

def metadata(st, raw):
 return {'dev':st.st_dev,'ino':st.st_ino,'uid':st.st_uid,'gid':st.st_gid,
  'mode':stat.S_IMODE(st.st_mode),'nlink':st.st_nlink,'bytes':st.st_size,
  'mtimeNs':str(st.st_mtime_ns),'ctimeNs':str(st.st_ctime_ns),
  'sha256':hashlib.sha256(raw).hexdigest()}

def directory_metadata(st):
 return {k:v for k,v in metadata(st,b'').items() if k in ('dev','ino','uid','gid','mode','mtimeNs','ctimeNs')}

def same_artifact(row, *, initial=False):
 need(isinstance(row,dict) and set(row)==set(EXPECTED),'EXACT_ARTIFACT_METADATA_REQUIRED')
 need(all(row[k]==v for k,v in EXPECTED.items() if initial or k!='ctimeNs'),'EXACT_ARTIFACT_DRIFT')
 need(isinstance(row['ctimeNs'],str) and row['ctimeNs'].isdigit(),'ARTIFACT_CTIME_UNPROVEN')

def _artifact_at(parent,name):
 try:fd=os.open(name,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK,dir_fd=parent)
 except FileNotFoundError:return None
 try:
  before=os.fstat(fd)
  need(stat.S_ISREG(before.st_mode) and before.st_size==0 and before.st_nlink==1,'EXACT_EMPTY_ARTIFACT_REQUIRED')
  need(os.read(fd,1)==b'','EXACT_EMPTY_ARTIFACT_REQUIRED')
  need(L._identity(before)==L._identity(os.fstat(fd))==L._identity(os.stat(name,dir_fd=parent,follow_symlinks=False)),'ARTIFACT_CHANGED')
  return metadata(before,b'')
 finally:os.close(fd)

def _rename_noreplace(sourcefd,source,destfd,dest):
 # No replace fallback is permitted, including kernels/libcs without renameat2.
 libc=ctypes.CDLL(None,use_errno=True)
 try:call=libc.renameat2
 except AttributeError:raise Refused('ATOMIC_NOREPLACE_UNAVAILABLE') from None
 call.argtypes=[ctypes.c_int,ctypes.c_char_p,ctypes.c_int,ctypes.c_char_p,ctypes.c_uint]
 call.restype=ctypes.c_int
 if call(sourcefd,source.encode(),destfd,dest.encode(),1)!=0:
  code=ctypes.get_errno()
  if code in (errno.EEXIST,errno.ENOTEMPTY):raise Refused('RELOCATION_DESTINATION_EXISTS')
  if code==errno.EXDEV:raise Refused('RELOCATION_CROSS_FILESYSTEM_REFUSED')
  raise Refused('ATOMIC_RELOCATION_EFFECT_UNPROVEN')

def scan_artifact_handles(identity, proc=Path('/proc')):
 """All processes, including App and self; any FD or mapping refuses.

 We do not read FD contents, argv, environments or private provider data.
 This is a live local handle observation, not proof of upstream drain.
 """
 for entry in proc.iterdir():
  if not entry.name.isdecimal():continue
  try:
   before=(entry/'stat').read_text();before=before[before.rfind(')')+2:].split()[19]
   for fd in (entry/'fd').iterdir():
    try:st=fd.stat()
    except FileNotFoundError:continue
    need((st.st_dev,st.st_ino)!=identity,'ARTIFACT_OPEN_HANDLE_PRESENT')
   for line in (entry/'maps').read_text().splitlines():
    parts=line.split(None,5);need(len(parts)>=5,'ARTIFACT_MAP_SCAN_UNPROVEN')
    dev=parts[3].split(':')
    need((os.makedev(int(dev[0],16),int(dev[1],16)),int(parts[4]))!=identity,'ARTIFACT_MAPPING_PRESENT')
   after=(entry/'stat').read_text();after=after[after.rfind(')')+2:].split()[19]
   need(before==after,'ARTIFACT_PROCESS_SCAN_CHANGED')
  except FileNotFoundError:continue
  except Refused:raise
  except (OSError,ValueError,IndexError):raise Refused('ARTIFACT_HANDLE_SCAN_UNPROVEN') from None

class QuarantineBackend(R.LinuxBackend):
 def __init__(self,admission):
  super().__init__(admission,L.LedgerCheckpoint())
  self.paths=R.Paths(state=STATE,fence=FENCE,condition=CONDITION)

 def require(self,operation,target=None):
  super().require(operation,target)
  if target is not None:need(all(target.get(k)==v for k,v in SOURCE_APP.items()),'EXACT_ORIGINAL_APP_REQUIRED')

 def inspect_recovery(self,target):return self._inspect(target,allow_transition=True)

 def open_pidfd(self,*args):raise Refused('SIGNAL_AND_RESTART_FORBIDDEN')
 def send_pidfd_sigkill(self,*args):raise Refused('SIGNAL_AND_RESTART_FORBIDDEN')
 def _fence_bytes(self,owner):
  need(R.ishash(owner),'OWNER_HASH_REQUIRED')
  return ('# Exact empty staging artifact quarantine '+owner+'\n[Unit]\nRefuseManualStart=yes\nConditionPathExists='+str(self.paths.condition)+'\n[Service]\nRestart=no\n').encode()

 def _frozen(self,target,owner):
  need(owner==self.admission.approval_hash,'OWNER_ADMISSION_DRIFT')
  row=self.inspect(target)
  need(not row['processExited'] and row['frozen'] and row['freezeRequested'] and row['fenceOwner']==owner and row['freezeOwner']==owner and row['members']==[target['pid']],'OWNED_FROZEN_SINGLETON_REQUIRED')
  return row

 def _quarantine_fd(self, *, create=False, allow_missing=False):
  if self.files.directory(QUARANTINE,create=create,allow_missing=allow_missing) is None:return None
  fd=os.open(QUARANTINE,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
  try:
   st=os.fstat(fd);need(st.st_uid==self.system.owner_uid and stat.S_IMODE(st.st_mode)==0o700,'QUARANTINE_DIRECTORY_UNSAFE')
   need(set(os.listdir(fd))<= {DESTINATION},'FOREIGN_QUARANTINE_CONTENT')
   if create:
    # Persist the new quarantine directory's name, not only its contents.
    self.files.directory(QUARANTINE.parent)
    parent=os.open(QUARANTINE.parent,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
    try:os.fsync(parent)
    finally:os.close(parent)
   return fd
  except BaseException:os.close(fd);raise

 def _inventory(self,target, *, artifact_location, initial=False):
  registration,registration_hash=L.read_registration();registered=L.registration_bindings(registration)
  pub=L.read_public(L.PUBLIC);g,_=L._public(pub,int(time.time()*1000),L.PUBLIC_DIGEST,L.GRANT_DIGEST)
  fd=L._open_directory(L.STORE,leaf_uid=1000,leaf_mode=0o700)
  files={};ids={};dirs={};total=0
  try:
   st=os.fstat(fd);need((st.st_dev,st.st_ino)==registered['app'],'SEALED_APP_DIRECTORY_IDENTITY_DRIFT')
   host_before,_=L._read_at(fd,'state.json',uid=1000,mode=0o600)
   graph=L._registered_projects(L._wrapper(L.parse(host_before),'r16.app-workspace.v1'),g)
   need(set(L.PINS)<=set(graph),'REGISTERED_PROJECT_GRAPH_DRIFT')
   allowed={'project-'+p for p in graph}
   def walk(parent,relative):
    nonlocal total
    before=os.fstat(parent);need(before.st_uid==1000 and stat.S_IMODE(before.st_mode)==0o700,'STORE_DIRECTORY_REFUSED')
    dirs[relative]=directory_metadata(before)
    names=sorted(os.listdir(parent));need(len(names)<=L.MAX_FILES,'STORE_CAPACITY_REFUSED')
    for name in names:
     s=os.stat(name,dir_fd=parent,follow_symlinks=False);rel=relative+'/'+name
     if stat.S_ISDIR(s.st_mode):
      need(relative=='host' and name in allowed,'UNREGISTERED_STORE_DIRECTORY')
      child=os.open(name,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW,dir_fd=parent)
      try:need(L._identity(os.fstat(child))==L._identity(s),'STORE_DIRECTORY_CHANGED');walk(child,rel)
      finally:os.close(child)
     elif relative=='host' and name==ARTIFACT:
      need(artifact_location=='SOURCE','SOURCE_ARTIFACT_UNEXPECTED')
      row=_artifact_at(parent,name);same_artifact(row,initial=initial);files[rel]=row;ids[rel]=(s.st_dev,s.st_ino)
     else:
      need(not name.startswith(('.next','.reclaim')),'OTHER_TEMPORARY_STORE_FILE_PRESENT')
      need(name in ('state.json','.lock') or L.re.fullmatch('archive-[A-Za-z0-9_-]+[.]json',name),'UNREVIEWED_STORE_FILE')
      raw,stable=L._read_at(parent,name,uid=1000,mode=0o600)
      if rel=='host/state.json':need(raw==host_before,'REGISTERED_PROJECT_GRAPH_CHANGED')
      total+=len(raw);need(total<=L.MAX_BYTES and len(files)<L.MAX_FILES,'STORE_CAPACITY_REFUSED')
      files[rel]=metadata(stable,raw);ids[rel]=(stable.st_dev,stable.st_ino)
    need(names==sorted(os.listdir(parent)) and L._identity(before)==L._identity(os.fstat(parent)),'STORE_DIRECTORY_CHANGED')
    if relative=='host':need({n for n in names if n.startswith('project-')}==allowed,'REGISTERED_STORE_MISSING')
   walk(fd,'host')
   need(all(d+'/state.json' in files for d in dirs),'REGISTERED_STORE_MISSING')
   need(('host/'+ARTIFACT in files)==(artifact_location=='SOURCE'),'SOURCE_ARTIFACT_LOCATION_DRIFT')
  finally:os.close(fd)
  L._scan_writers(ids,{k:(v['dev'],v['ino']) for k,v in dirs.items()},target['pid'])
  scan_artifact_handles((EXPECTED['dev'],EXPECTED['ino']))
  after,after_hash=L.read_registration();need(registration_hash==after_hash and L.canonical(registration)==L.canonical(after),'SEALED_REGISTRATION_CHANGED')
  need(L.read_public(L.PUBLIC)==pub,'PUBLIC_CONFIGURATION_CHANGED')
  return {'schema':'r16.exact-empty-artifact-full-inventory.v1','files':files,'directories':dirs,'registrationHash':registration_hash,'registeredProjectCount':len(graph),'noOpenArtifactHandles':True,'otherWriterPids':[],'drainStatus':'UNPROVEN'}

 def capture_before(self,target):
  self.require('capture-before',target)
  # Used by read-only preflight while live and by the driver after actual freeze.
  before=self.inspect(target)
  one=self._inventory(target,artifact_location='SOURCE',initial=True)
  two=self._inventory(target,artifact_location='SOURCE',initial=True)
  need(one==two and self.inspect(target)==before,'BASELINE_CHANGED')
  return {**two,'artifactLocation':'SOURCE','artifact':two['files']['host/'+ARTIFACT]}

 def preflight(self,target):
  before=self.capture_before(target)
  return {'status':'EXACT_EMPTY_ARTIFACT_INVENTORY_PASS_NOT_LEDGER_VALIDATED','manifestDigest':R.digest(before),'fileCount':len(before['files']),'registeredProjectCount':before['registeredProjectCount'],'noOpenArtifactHandles':True,'completeLedgerVerified':False,'drainStatus':'UNPROVEN','effectsIssued':0}

 def inspect_artifact(self,target,owner):
  self.require('inspect-artifact',target);need(owner==self.admission.approval_hash,'OWNER_ADMISSION_DRIFT')
  source=L._open_directory(L.STORE,leaf_uid=1000,leaf_mode=0o700);dest=None
  try:
   a=_artifact_at(source,ARTIFACT);dest=self._quarantine_fd(allow_missing=True);z=_artifact_at(dest,DESTINATION) if dest is not None else None
   if a is not None:same_artifact(a)
   if z is not None:same_artifact(z)
   if a is not None and z is None:return {'location':'SOURCE','artifact':a}
   if z is not None and a is None:return {'location':'QUARANTINE','artifact':z}
   return {'location':'CONFLICT' if a is not None else 'UNKNOWN','artifact':None}
  finally:
   os.close(source)
   if dest is not None:os.close(dest)

 def _relocate(self,target,owner,before,*,reverse):
  self.require('restore' if reverse else 'quarantine',target);self._frozen(target,owner)
  need(before.get('schema')=='r16.exact-empty-artifact-full-inventory.v1' and before.get('artifactLocation') in ('SOURCE','QUARANTINE'),'BEFORE_MANIFEST_REQUIRED')
  if before['artifactLocation']=='SOURCE':need(before.get('artifact')==before.get('files',{}).get('host/'+ARTIFACT),'BEFORE_MANIFEST_REQUIRED')
  else:need(reverse and 'host/'+ARTIFACT not in before.get('files',{}),'BEFORE_MANIFEST_REQUIRED')
  same_artifact(before['artifact'],initial=not reverse)
  location=self.inspect_artifact(target,owner);expected='QUARANTINE' if reverse else 'SOURCE'
  need(location['location']==expected,'RELOCATION_SOURCE_NOT_EXACT')
  if reverse:
   expected_artifact=before['artifact'] if before['artifactLocation']=='QUARANTINE' else before.get('expectedQuarantinedArtifact')
   need(isinstance(expected_artifact,dict) and location['artifact']==expected_artifact,'QUARANTINE_RECEIPT_METADATA_REQUIRED')
  current=self._inventory(target,artifact_location='QUARANTINE' if reverse else 'SOURCE',initial=not reverse)
  self._normal_unchanged(current,before)
  source=L._open_directory(L.STORE,leaf_uid=1000,leaf_mode=0o700);dest=None
  try:
   dest=self._quarantine_fd(create=not reverse)
   need(os.fstat(source).st_dev==os.fstat(dest).st_dev,'RELOCATION_CROSS_FILESYSTEM_REFUSED')
   need((os.fstat(source).st_dev,os.fstat(source).st_ino)==(before['directories']['host']['dev'],before['directories']['host']['ino']),'SEALED_APP_DIRECTORY_IDENTITY_DRIFT')
   scan_artifact_handles((EXPECTED['dev'],EXPECTED['ino']));self._frozen(target,owner)
   fromfd,fromname,tofd,toname=(dest,DESTINATION,source,ARTIFACT) if reverse else (source,ARTIFACT,dest,DESTINATION)
   row=_artifact_at(fromfd,fromname);same_artifact(row,initial=not reverse)
   need(row==(expected_artifact if reverse else before['artifact']),'RELOCATION_LAST_IDENTITY_DRIFT')
   need(_artifact_at(tofd,toname) is None,'RELOCATION_DESTINATION_EXISTS')
   self.require('restore' if reverse else 'quarantine',target)
   _rename_noreplace(fromfd,fromname,tofd,toname)
   # The caller has consumed its durable intent already; any failure here is
   # unknown effect, never permission to replay this syscall.
   os.fsync(fromfd);os.fsync(tofd)
   after=_artifact_at(tofd,toname);same_artifact(after)
   need(_artifact_at(fromfd,fromname) is None,'RELOCATION_SOURCE_REAPPEARED')
   return {'location':'SOURCE' if reverse else 'QUARANTINE','artifact':after,'sourceParent':directory_metadata(os.fstat(source)),'quarantineParent':directory_metadata(os.fstat(dest))}
  finally:
   os.close(source)
   if dest is not None:os.close(dest)

 def quarantine(self,target,owner,before):return self._relocate(target,owner,before,reverse=False)
 def restore(self,target,owner,before):return self._relocate(target,owner,before,reverse=True)

 def _normal_unchanged(self,after,before):
  old={k:v for k,v in before['files'].items() if k!='host/'+ARTIFACT}
  new={k:v for k,v in after['files'].items() if k!='host/'+ARTIFACT}
  def stable_dirs(value):
   return {name:{k:v for k,v in row.items() if name!='host' or k not in ('mtimeNs','ctimeNs')} for name,row in value.items()}
  need(new==old and stable_dirs(after['directories'])==stable_dirs(before['directories']) and after['registrationHash']==before['registrationHash'] and after['registeredProjectCount']==before['registeredProjectCount'],'COMMITTED_LEDGER_OR_REGISTRATION_CHANGED')

 def verify_after(self,target,before):
  self.require('verify-after',target);owner=self.admission.approval_hash;self._frozen(target,owner)
  location=self.inspect_artifact(target,owner);need(location['location']=='QUARANTINE','QUARANTINE_LOCATION_UNPROVEN')
  # The unchanged R8 reader sees the whole real post-relocation tree. No
  # filtered checkpoint/subset or boolean can substitute for this call.
  checkpoint=self.checkpointer.capture(target)
  a=checkpoint['attestation'];need(a.get('capturePhase')=='FROZEN' and a.get('signatureVerification') is True and a.get('sealedRegistrationVerified') is True and a.get('drainStatus')=='UNPROVEN','UNCHANGED_LEDGER_VERIFIER_REFUSED')
  one=self._inventory(target,artifact_location='QUARANTINE');two=self._inventory(target,artifact_location='QUARANTINE')
  need(one==two,'POST_RELOCATION_TREE_CHANGED');self._normal_unchanged(two,before)
  need(self.inspect_artifact(target,owner)==location,'QUARANTINE_ARTIFACT_CHANGED');self._frozen(target,owner)
  return {**two,'artifactLocation':'QUARANTINE','artifact':location['artifact'],'ledgerAttestation':{k:a[k] for k in ('schema','oldGrantActive','sourcePublicConfigDigest','grantHash','sourceDeliveryHash','sourceDeliveryRevision','registrationHash','checkpointManifestDigest','semanticBindingsDigest','registeredProjectCount','fileCount','totalBytes','originalUnknownCount','otherDurableInflight','foreignOpenWriters','signatureVerification','sealedRegistrationVerified','drainStatus')}}

 def capture_inverse_before(self,target,owner):
  self.require('capture-inverse-before',target);self._frozen(target,owner)
  location=self.inspect_artifact(target,owner);need(location['location']=='QUARANTINE','QUARANTINE_LOCATION_UNPROVEN')
  checkpoint=self.checkpointer.capture(target)
  a=checkpoint['attestation'];need(a.get('capturePhase')=='FROZEN' and a.get('signatureVerification') is True and a.get('sealedRegistrationVerified') is True and a.get('drainStatus')=='UNPROVEN','UNCHANGED_LEDGER_VERIFIER_REFUSED')
  one=self._inventory(target,artifact_location='QUARANTINE');two=self._inventory(target,artifact_location='QUARANTINE')
  need(one==two and self.inspect_artifact(target,owner)==location,'INVERSE_BASELINE_CHANGED');self._frozen(target,owner)
  return {**two,'artifactLocation':'QUARANTINE','artifact':location['artifact'],'ledgerAttestation':{k:a[k] for k in ('schema','oldGrantActive','sourcePublicConfigDigest','grantHash','sourceDeliveryHash','sourceDeliveryRevision','registrationHash','checkpointManifestDigest','semanticBindingsDigest','registeredProjectCount','fileCount','totalBytes','originalUnknownCount','otherDurableInflight','foreignOpenWriters','signatureVerification','sealedRegistrationVerified','drainStatus')}}

 def verify_restored(self,target,before,owner):
  self.require('verify-restored',target);self._frozen(target,owner)
  location=self.inspect_artifact(target,owner);need(location['location']=='SOURCE','RESTORE_LOCATION_UNPROVEN')
  one=self._inventory(target,artifact_location='SOURCE');two=self._inventory(target,artifact_location='SOURCE')
  need(one==two,'RESTORED_TREE_CHANGED');self._normal_unchanged(two,before)
  need(self.inspect_artifact(target,owner)==location,'RESTORED_ARTIFACT_CHANGED')
  return {**two,'artifactLocation':'SOURCE','artifact':location['artifact']}
