"""Trusted-host native intent for one exact artifact; never a stop authority."""
from contextlib import contextmanager
from copy import deepcopy
import fcntl,os,resource,secrets,select,socket,stat,time
from pathlib import Path
import r8_common_safe as C
import r8_linux_backend as R
import quarantine_driver as D
from quarantine_backend import QuarantineBackend
STATE=Path('/var/lib/r16-maintenance/empty-temp-quarantine-r1')
SOURCE_CAPSULE='cfa55305623727e1b7607705c7b7a8eb76d2221250368828d21b7779da75af41'
READ_OPS={'inspect','capture-before','inspect-artifact','verify-after','capture-inverse-before','verify-restored','checkpoint'}
EFFECT_OPS={'fence','freeze','quarantine','restore','unfreeze','unfence','unfreeze-transition'}
BRAND=object()
def now():return time.time_ns()//1000000
def root():
 resource.setrlimit(resource.RLIMIT_CORE,(0,0))
 C.need(os.getuid()==0 and os.geteuid()==0 and socket.gethostname()=='VM-0-12-ubuntu','FIXED_CLOUD_ROOT_REQUIRED')
def encode(x):return D.canonical(x).encode()
class Journal:
 """Separate root lock and metadata-only transaction; never a business store."""
 def __init__(self):self.files=R.ProtectedFiles();self.fd=None
 @property
 def is_locked(self):return self.fd is not None
 def read(self):
  root();raw=self.files.read(STATE/'transaction.json',maximum=16*1024*1024,mode=0o600,allow_missing=True)
  return None if raw is None else C.parse(raw)
 def write(self,value):
  root();C.need(self.is_locked,'ROOT_JOURNAL_LOCK_REQUIRED')
  st=os.fstat(self.fd);current=(STATE/'exclusive.lock').lstat()
  C.need(st.st_ino==current.st_ino and st.st_dev==current.st_dev and current.st_nlink==1,'ROOT_JOURNAL_LOCK_REPLACED')
  C.need(type(value) is dict and value.get('schema')=='r16.exact-empty-artifact-quarantine-journal.v1','ROOT_JOURNAL_SCHEMA_REFUSED')
  previous=self.read()
  if previous is not None:
   C.need(previous['approvalHash']==value.get('approvalHash') and previous['targetHash']==value.get('targetHash'),'ROOT_JOURNAL_BINDING_RESET_REFUSED')
   for flag in ('quarantineAttemptConsumed','inverseAttemptConsumed'):
    C.need(previous.get(flag) is not True or value.get(flag) is True,'ROOT_EFFECT_INTENT_RESET_REFUSED')
  self.files.atomic(STATE/'transaction.json',encode(value))
 @contextmanager
 def locked(self):
  root();C.need(not self.is_locked,'ROOT_JOURNAL_ALREADY_LOCKED');self.files.directory(STATE,create=True)
  s=STATE.lstat();C.need(s.st_uid==0 and stat.S_IMODE(s.st_mode)==0o700,'ROOT_STATE_DIRECTORY_REFUSED')
  fd=os.open(STATE/'exclusive.lock',os.O_WRONLY|os.O_CREAT|os.O_NOFOLLOW,0o600)
  try:
   s=os.fstat(fd);C.need(stat.S_ISREG(s.st_mode) and s.st_uid==0 and s.st_nlink==1 and stat.S_IMODE(s.st_mode)==0o600,'ROOT_LOCK_REFUSED')
   try:fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
   except BlockingIOError:raise C.Refused('ROOT_TRANSACTION_BUSY') from None
   self.fd=fd;yield self
  finally:
   self.fd=None;os.close(fd)
class Admission:
 def __init__(self,brand,target,pin,journal):
  root();C.need(brand is BRAND and target==D.TARGET,'EXACT_NATIVE_TARGET_REQUIRED')
  self.target_hash=D.digest(target);self.capsule_hash=pin;self.journal=journal
  self.approval_hash=None;self.approval=None;self.recovery_approved=None;self.recovery=None;self.monotonic_end=0
 def bind(self,approval,recovery=None):
  root();D.validate_approval(approval,now())
  C.need(approval['environment']=='PRODUCTION' and approval['capsuleHash']==self.capsule_hash and approval['sourceCapsuleHash']==SOURCE_CAPSULE and D.digest(approval['target'])==self.target_hash,'NATIVE_CAPSULE_TARGET_DRIFT')
  self.approval=deepcopy(approval);self.approval_hash=D.digest(approval);self.recovery=deepcopy(recovery)
  limit=approval['deadline'] if recovery is None else recovery['deadline']
  self.monotonic_end=time.monotonic()+max(0,(limit-now())/1000)
  if recovery is not None:self.recovery_approved={'stopApprovalHash':self.approval_hash,'targetHash':self.target_hash,'recoveryHash':D.digest(recovery)}
 def require(self,operation,target=None):
  root();C.need(operation in READ_OPS|EFFECT_OPS,'QUARANTINE_OPERATION_FORBIDDEN')
  if target is not None:C.need(D.digest(target)==self.target_hash,'EXACT_NATIVE_TARGET_DRIFT')
  if operation in READ_OPS:return
  C.need(self.approval is not None and self.journal.is_locked,'NATIVE_EXACT_INTENT_REQUIRED')
  record=self.journal.read();C.need(record is not None and record['approvalHash']==self.approval_hash and record['targetHash']==self.target_hash,'NATIVE_ROOT_TRANSACTION_REQUIRED')
  if self.recovery is None:
   C.need(operation not in ('unfreeze-transition',),'NEW_NATIVE_RECOVERY_INTENT_REQUIRED')
   deadline=self.approval['deadline']
  else:
   C.need(self.recovery.get('approvalHash')==self.approval_hash and self.recovery.get('targetHash')==self.target_hash and self.recovery.get('scope')=='RESTORE_ORIGINAL_EMPTY_ARTIFACT' and record.get('recoveryIntentHash')==D.digest(self.recovery),'NATIVE_RECOVERY_BINDING_REQUIRED')
   C.need(operation!='quarantine','RECOVERY_CANNOT_QUARANTINE');deadline=self.recovery['deadline']
  C.need(now()<deadline and time.monotonic()<self.monotonic_end,'NATIVE_EFFECT_WINDOW_EXPIRED')
  if operation in ('fence','freeze','quarantine') and self.recovery is None:
   v=os.statvfs(STATE);C.need(v.f_bavail*v.f_frsize>=32*1024*1024,'QUARANTINE_TRANSACTION_SPACE_UNPROVEN')
class Terminal:
 def __init__(self):
  root();self.fd=os.open('/dev/tty',os.O_RDWR|os.O_NOCTTY|os.O_CLOEXEC)
  try:C.need(os.isatty(self.fd) and os.tcgetpgrp(self.fd)==os.getpgrp(),'FOREGROUND_NATIVE_TERMINAL_REQUIRED')
  except BaseException:os.close(self.fd);raise
 def close(self):os.close(self.fd)
 def say(self,text):
  raw=(text+'\n').encode();at=0
  while at<len(raw):at+=os.write(self.fd,raw[at:])
 def confirm(self,pending,word):
  self.say('准确待执行对象：'+D.canonical(pending));h=D.digest(pending)
  self.say('仅短暂冻结原 App 并迁移这一个空文件；服务可能短暂无响应。文件原物留证，可按准确新恢复对象还原。')
  self.say('不发停机信号、不重启、不签发、不安装发行版、不切换 Owner；不改 state.json、锁、历史审计和两笔 UNKNOWN。')
  self.say('旧 App 内存状态与业务可用性仍未获证明，隔离成功不等于业务恢复。')
  self.say('核对后输入 '+word+' '+h[:16]+' ：')
  value=b''
  while len(value)<=128:
   remaining=(pending['deadline']-now())/1000;C.need(remaining>0,'NATIVE_CONFIRMATION_WINDOW_EXPIRED')
   ready,_,_=select.select([self.fd],[],[],remaining);C.need(bool(ready),'NATIVE_CONFIRMATION_WINDOW_EXPIRED')
   part=os.read(self.fd,1)
   if part in (b'',b'\n'):break
   value+=part
  C.need(value==word.encode()+b' '+h[:16].encode(),'EXACT_NATIVE_INTENT_CANCELLED')
  C.need(now()<pending['deadline'],'NATIVE_CONFIRMATION_WINDOW_EXPIRED');return h

def source_approval(pin,target):
 at=now();return {'schema':D.SCHEMA,'environment':'PRODUCTION','approvalId':secrets.token_hex(16),'approvedAt':at,'deadline':at+300000,'policyProposalHash':D.POLICY_HASH,'sourceCapsuleHash':SOURCE_CAPSULE,'capsuleHash':pin,'target':deepcopy(target),'artifact':{'path':D.ARTIFACT_PATH,**deepcopy(D.ARTIFACT)},'allowExactEmptyArtifactQuarantine':True,'acceptPossibleInMemoryStorePoisoning':True,'drainStatus':'UNPROVEN'}
def read_approval(pin,target):
 record=Journal().read();C.need(record is not None,'NO_QUARANTINE_TRANSACTION')
 h=record.get('approvalHash');C.need(D.ishash(h),'ROOT_APPROVAL_HASH_REFUSED')
 intent=C.parse(C.secure_read(STATE/'approved-intents'/(h+'.json')));a=intent.get('approval')
 D.validate_approval(a,now())
 C.need(a['capsuleHash']==pin and a['sourceCapsuleHash']==SOURCE_CAPSULE and a['target']==target and D.digest(a)==h,'ROOT_APPROVAL_SOURCE_DRIFT')
 C.need(set(intent)=={'schema','approval','pendingHash','capsuleHash','trustedClient','confirmedAt'} and intent['schema']=='r16.exact-empty-artifact-native-intent.v1' and intent['pendingHash']==h and intent['capsuleHash']==pin and intent['trustedClient']=='FOREGROUND_CLOUD_ROOT_TTY','ROOT_NATIVE_INTENT_DRIFT')
 return a

def unused_intent_metadata(j):
 # Unconsumed immutable native-intent records are audit, not reset authority.
 # Only a published transaction can authorize an effect. An interrupted first
 # intent write therefore does not require deleting history or reusing a nonce.
 if not STATE.exists():return
 j.files.directory(STATE);s=STATE.lstat()
 C.need(s.st_uid==0 and stat.S_IMODE(s.st_mode)==0o700 and set(os.listdir(STATE))<= {'exclusive.lock','approved-intents'},'UNREVIEWED_ROOT_STATE')
 folder=STATE/'approved-intents'
 if folder.exists():
  j.files.directory(folder);C.need(stat.S_IMODE(folder.lstat().st_mode)==0o700,'UNSAFE_INTENT_AUDIT_DIRECTORY')
  import re
  names=set(os.listdir(folder));groups={}
  for name in names:
   C.need(re.fullmatch(r'[a-f0-9]{64}[.]json|[.][a-f0-9]{64}[.]json[.][a-f0-9]{64}[.]pending',name) is not None,'UNREVIEWED_INTENT_AUDIT_FILE')
   st=(folder/name).lstat();C.need(stat.S_ISREG(st.st_mode) and st.st_uid==0 and st.st_nlink in (1,2) and stat.S_IMODE(st.st_mode)==0o600 and st.st_size<=32768,'UNSAFE_INTENT_AUDIT_FILE')
   groups.setdefault((st.st_dev,st.st_ino),[]).append((name,st))
  for identity,rows in groups.items():
   if rows[0][1].st_nlink==1:
    C.need(len(rows)==1,'UNSAFE_INTENT_AUDIT_LINKS');continue
   # immutable() can crash after its own link but before unlink. Retain both
   # audit names without granting old authority or changing the filesystem.
   C.need(len(rows)==2 and all(st.st_nlink==2 for _,st in rows),'UNSAFE_INTENT_AUDIT_LINKS')
   finals=[name for name,_ in rows if not name.startswith('.')]
   C.need(len(finals)==1,'UNSAFE_INTENT_AUDIT_LINKS');final=finals[0]
   pending=next(name for name,_ in rows if name!=final)
   match=re.fullmatch(r'[.]'+re.escape(final)+r'[.]([a-f0-9]{64})[.]pending',pending)
   C.need(match is not None,'UNSAFE_INTENT_AUDIT_LINKS')
   fd=os.open(folder/final,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
   try:
    before=os.fstat(fd);raw=os.read(fd,32769);after=os.fstat(fd)
    fields=lambda st:(st.st_dev,st.st_ino,st.st_uid,st.st_mode,st.st_nlink,st.st_size,st.st_mtime_ns,st.st_ctime_ns)
    C.need((before.st_dev,before.st_ino)==identity and fields(before)==fields(after)==fields(rows[0][1]) and len(raw)==before.st_size and C.sha(raw)==match[1],'UNSAFE_INTENT_AUDIT_LINK_CONTENT')
   finally:os.close(fd)
   C.need(all(fields((folder/name).lstat())==fields(before) for name,_ in rows),'INTENT_AUDIT_CHANGED')
  C.need(set(os.listdir(folder))==names,'INTENT_AUDIT_CHANGED')

def preflight(pin,target):
 root();j=Journal();C.need(j.read() is None,'EXISTING_TRANSACTION_USE_STATUS_OR_RECOVER')
 # No mkdir/lock/source install. Unknown pending state is never ignored.
 unused_intent_metadata(j)
 a=Admission(BRAND,target,pin,j);b=QuarantineBackend(a);observation=b.inspect(target)
 C.need(not observation['processExited'] and not observation['frozen'] and not observation['freezeRequested'] and observation['fenceOwner'] is None,'ORIGINAL_RUNTIME_NOT_UNTOUCHED')
 before=b.capture_before(target);D.validate_inventory(before,before=True)
 C.need(b.inspect(target)==observation,'READ_ONLY_TARGET_CHANGED');v=os.statvfs('/var/lib/r16-app');space=v.f_bavail*v.f_frsize
 C.need(space>=32*1024*1024,'QUARANTINE_TRANSACTION_SPACE_UNPROVEN')
 return {'schema':'r16.exact-empty-artifact-readonly-preflight.v1','status':'QUARANTINE_READ_ONLY_PREFLIGHT_PASS','capsuleHash':pin,'sourceCapsuleHash':SOURCE_CAPSULE,'policyProposalHash':D.POLICY_HASH,'targetHash':D.digest(target),'artifactIdentityHash':D.digest(before['artifact']),'completeInventoryHash':D.digest(before),'registeredProjectCount':before['registeredProjectCount'],'fileCount':len(before['files']),'noOpenArtifactHandles':True,'completeLedgerVerifiedBeforeQuarantine':False,'completeLedgerMustPassAfterQuarantine':True,'normalBusinessFilesModified':False,'ordinaryAvailableBytes':space,'minimumRepairHeadroomBytes':32*1024*1024,'fullInstallationSpaceApproved':False,'rootSourceInstalled':False,'journalWritten':False,'nativeIntentCreated':False,'freezeIssued':False,'signalsIssued':0,'businessCallsIssued':0,'drainStatus':'UNPROVEN','businessAcceptance':False}
def status(pin,target):
 root();j=Journal();record=j.read()
 if record is None:return {'status':'READ_ONLY_STATUS','transactionExists':False,'businessAcceptance':False}
 a=read_approval(pin,target);cap=Admission(BRAND,target,pin,j);cap.bind(a);b=QuarantineBackend(cap)
 projection=D.Driver(b,j,now).status(a)
 return {'status':'READ_ONLY_STATUS','transactionExists':True,'recordedPhase':record.get('phase'),'recordedOutcome':projection,'observedAt':now(),'historicalOutcomeIsNotCurrentBusinessHealth':True,'businessAcceptance':False}
def execute(pin,target,terminal_factory=Terminal):
 root();j=Journal()
 with j.locked():
  if j.read() is not None:return status(pin,target)
  cap=Admission(BRAND,target,pin,j);backend=QuarantineBackend(cap)
  preflight(pin,target)
  approval=source_approval(pin,target);D.validate_approval(approval,now());terminal=terminal_factory()
  try:h=terminal.confirm(approval,'QUARANTINE')
  finally:terminal.close()
  C.need(h==D.digest(approval) and now()<approval['deadline'],'EXACT_NATIVE_INTENT_REFUSED')
  C.immutable(STATE/'approved-intents'/(h+'.json'),encode({'schema':'r16.exact-empty-artifact-native-intent.v1','approval':approval,'pendingHash':h,'capsuleHash':pin,'trustedClient':'FOREGROUND_CLOUD_ROOT_TTY','confirmedAt':now()}))
  cap.bind(approval);return D.Driver(backend,j,now).run(approval)
def recover(pin,target,terminal_factory=Terminal):
 root();j=Journal()
 with j.locked():
  record=j.read();C.need(record is not None,'NO_QUARANTINE_TRANSACTION')
  approval=read_approval(pin,target);at=now();intent={'schema':D.RECOVERY_SCHEMA,'intentId':secrets.token_hex(16),'approvalHash':D.digest(approval),'targetHash':D.digest(target),'scope':'RESTORE_ORIGINAL_EMPTY_ARTIFACT','approvedAt':at,'deadline':at+120000}
  cap=Admission(BRAND,target,pin,j);cap.bind(approval);backend=QuarantineBackend(cap)
  def artifact_observation():
   try:return backend.inspect_artifact(target,D.digest(approval))
   except Exception as e:
    value=getattr(e,'code','UNPROVEN');return {'location':'UNPROVEN','artifact':None,'code':value if isinstance(value,str) and value.isascii() and value.replace('_','').isalnum() else 'UNPROVEN'}
  observed=artifact_observation()
  pending={'schema':'r16.exact-empty-artifact-native-recovery-pending.v1','deadline':intent['deadline'],'capsuleHash':pin,'intent':intent,'journalHash':D.digest(record),'artifactObservation':observed}
  terminal=terminal_factory()
  try:h=terminal.confirm(pending,'RESTORE_EMPTY')
  finally:terminal.close()
  C.need(h==D.digest(pending) and now()<intent['deadline'],'EXACT_NATIVE_RECOVERY_INTENT_REFUSED')
  C.need(D.digest(j.read())==pending['journalHash'] and artifact_observation()==observed,'NATIVE_RECOVERY_PENDING_OBJECT_CHANGED')
  C.immutable(STATE/('recovery-native-intent-'+h+'.json'),encode({'schema':'r16.exact-empty-artifact-native-recovery-intent.v1','pending':pending,'pendingHash':h,'trustedClient':'FOREGROUND_CLOUD_ROOT_TTY','confirmedAt':now()}))
  cap.bind(approval,intent)
  return D.Driver(backend,j,now).recover(approval,intent)

def entry(mode,pin,target):
 root();C.need(target==D.TARGET and isinstance(pin,str) and D.ishash(pin),'EXACT_SOURCE_CAPSULE_REQUIRED')
 C.need(mode in ('preflight','execute','status','recover'),'FIXED_MODE_REQUIRED')
 return {'preflight':preflight,'execute':execute,'status':status,'recover':recover}[mode](pin,target)
