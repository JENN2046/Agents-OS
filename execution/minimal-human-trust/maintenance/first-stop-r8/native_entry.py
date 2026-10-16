"""Trusted-host-admin terminal admission. No generic command or path authority.

Imported only by the reviewed hash-pinned bootstrap, after copying the complete
capsule into its fixed root-owned directory. Importing does not stop anything.
"""
import os,resource,secrets,socket,sys,time
from pathlib import Path
from common_safe import Refused,need,parse,canonical,digest,sha,secure_read,immutable
import stop_driver as core
from linux_backend import LinuxBackend,RootJournal
from ledger_checkpoint import LedgerCheckpoint
STATE=Path('/var/lib/r16-maintenance/first-stop-r8')
ROOT=Path('/usr/lib/r16-maintenance/first-stop-r8')
HOST='VM-0-12-ubuntu'
POLICY_PROPOSAL='98552704b8bb8be9881318e8e8b12406448ea25f60951715a437198004ac4234'
_BRAND=object()
READ_OPERATIONS={'inspect','checkpoint','journal-lock','journal-read','driver'}
FORWARD_OPERATIONS={'open-pidfd','fence','freeze','signal'}

def now_ms(): return time.time_ns()//1000000

def root():
 resource.setrlimit(resource.RLIMIT_CORE,(0,0))
 need(os.getuid()==0 and os.geteuid()==0 and socket.gethostname()==HOST,'FIXED_CLOUD_ROOT_REQUIRED')

class NativeAdmission:
 """Process-local admission; a JSON boolean or model response cannot construct it."""
 def __init__(self,brand,target,capsule_hash):
  need(brand is _BRAND,'NATIVE_ADMISSION_REQUIRED');root()
  self.target_hash=digest(target);self.approval_hash=None;self.capsule_hash=capsule_hash
  self.approval=None;self.confirmed=False;self.monotonic_end=0
  self.recovery_approved=False;self.handoff_approved=False
 def bind(self,approval,historical=False):
  need(digest(approval['target'])==self.target_hash and approval['capsuleHash']==self.capsule_hash,'NATIVE_BINDING_DRIFT')
  self.approval=approval;self.approval_hash=digest(approval);self.confirmed=True
  self.monotonic_end=time.monotonic()+max(0,(approval['deadline']-now_ms())/1000)
 def require(self,operation,target=None):
  root();need(operation in READ_OPERATIONS|FORWARD_OPERATIONS|{'journal-write','unfreeze','unfence','unfreeze-exited','unfreeze-transition'},'NATIVE_OPERATION_REFUSED')
  if target is not None: need(digest(target)==self.target_hash,'NATIVE_TARGET_DRIFT')
  if operation in READ_OPERATIONS: return
  need(self.confirmed and self.approval_hash is not None,'NATIVE_INTENT_REQUIRED')
  if operation in FORWARD_OPERATIONS:
   need(now_ms()<self.approval['deadline'] and time.monotonic()<self.monotonic_end,'NATIVE_WINDOW_EXPIRED')
  if operation in ('unfreeze','unfence','unfreeze-exited','unfreeze-transition'):
   record=parse(secure_read(STATE/'transaction.json'))
   need(record.get('approvalHash')==self.approval_hash and record.get('targetHash')==self.target_hash,'POST_STOP_JOURNAL_BINDING_DRIFT')
   if record.get('signalAttemptConsumed') is False:
    need(operation!='unfreeze-exited','POST_STOP_SCOPE_REQUIRED')
    if operation=='unfreeze-transition':
     scope=self.recovery_approved;phase=parse(secure_read(STATE/'pre-signal-restore.json'))
     need(isinstance(scope,dict) and scope.get('preSignal') is True and phase.get('scope')==scope and
          phase.get('phase')=='RESTORE_INTENT' and scope.get('stopApprovalHash')==self.approval_hash and
          scope.get('targetHash')==self.target_hash and scope.get('recoveryHash')==digest(phase.get('recovery')),
          'NATIVE_TRANSITION_RECOVERY_REQUIRED')
     intent=phase['recovery'];need(intent['approvedAt']<=now_ms()<intent['deadline'],'NATIVE_RECOVERY_EXPIRED')
    return
   recovery=self.recovery_approved;handoff=self.handoff_approved
   if isinstance(recovery,dict):
    phase=parse(secure_read(STATE/'restore-original.json'))
    need(phase.get('scope')==recovery and phase.get('phase')=='START_INTENT' and
         recovery.get('stopApprovalHash')==self.approval_hash and recovery.get('targetHash')==self.target_hash and
         recovery.get('recoveryHash')==digest(phase.get('recovery')),'NATIVE_RECOVERY_PHASE_REQUIRED')
    intent=phase['recovery'];need(intent['approvedAt']<=now_ms()<intent['deadline'],'NATIVE_RECOVERY_EXPIRED');return
   if isinstance(handoff,dict):
    phase=parse(secure_read(STATE/'handoff.json'))
    intent=parse(secure_read(STATE/'handoff-native-intent.json'))
    need(phase.get('scope')==handoff and intent.get('scope')==handoff and
         phase.get('phase') in ('SUCCESSOR_FENCE_INTENT','REMOVE_STOP_INTENT') and
         handoff.get('stopApprovalHash')==self.approval_hash and handoff.get('targetHash')==self.target_hash,
         'NATIVE_HANDOFF_PHASE_REQUIRED')
    need(intent['approvedAt']<=now_ms()<intent['deadline'],'NATIVE_HANDOFF_EXPIRED');return
   need(False,'POST_SIGNAL_AUTOMATIC_RESTORE_REFUSED')


class Terminal:
 def __init__(self):
  root();self.fd=os.open('/dev/tty',os.O_RDWR|os.O_NOCTTY|os.O_CLOEXEC)
  need(os.isatty(self.fd) and os.tcgetpgrp(self.fd)==os.getpgrp(),'FOREGROUND_NATIVE_TERMINAL_REQUIRED')
 def close(self): os.close(self.fd)
 def say(self,text):
  raw=(text+'\n').encode();at=0
  while at<len(raw): at+=os.write(self.fd,raw[at:])
 def confirm(self,pending,word):
  h=digest(pending)
  self.say('Exact pending authority target SHA-256: '+h)
  self.say('This is NOT a graceful drain. Requests can disconnect; accepted upstream work may continue.')
  self.say('Original two UNKNOWN records stay unchanged. No replay, settlement, signing, installation or Owner switch.')
  self.say('Type '+word+' '+h[:16]+' to confirm this exact target, or press Enter to cancel:')
  raw=b''
  while len(raw)<=128:
   part=os.read(self.fd,1)
   if part in (b'',b'\n'): break
   raw+=part
  need(raw.decode('ascii','strict').strip()==word+' '+h[:16],'EXACT_NATIVE_INTENT_CANCELLED')
  return h

def load_capsule(capsule_hash):
 root();need(len(capsule_hash)==64 and all(c in '0123456789abcdef' for c in capsule_hash),'CAPSULE_HASH_REQUIRED')
 directory=ROOT/capsule_hash
 raw=secure_read(directory/'CAPSULE.json');need(sha(raw)==capsule_hash,'CAPSULE_HASH_DRIFT');m=parse(raw)
 need(m.get('schema')=='r16.first-stop-capsule.v1' and m.get('policyExceptionProposalHash')==POLICY_PROPOSAL,'CAPSULE_SCOPE_DRIFT')
 need(m.get('acceptedPolicyException') is True and m.get('productionStopAlreadyAuthorized') is False,'POLICY_EXCEPTION_NOT_NATIVE_INTENT')
 for name,pin in m['files'].items():
  need(name and '/' not in name and name not in ('.','..'),'CAPSULE_MEMBER_REFUSED')
  need(sha(secure_read(directory/name))==pin,'ROOT_SOURCE_DRIFT')
 target=parse(secure_read(directory/'TARGET.json'))
 need(target['sourceHashes']==core.SOURCE_HASHES,'SOURCE_BINDING_DRIFT')
 return directory,target

def run_driver(backend,journal,approval):
 try: return core.Driver(backend,journal,now_ms).run(approval)
 finally:
  for handle in list(backend.handles): backend.close_pidfd(handle)

def stop(capsule_hash,terminal_factory=Terminal):
 directory,target=load_capsule(capsule_hash)
 admission=NativeAdmission(_BRAND,target,capsule_hash);reader=LedgerCheckpoint()
 backend=LinuxBackend(admission,reader)
 journal=RootJournal(admission)
 # The root exclusive lock spans old receipt read, terminal intent and every
 # effect. A new pending object never resets an earlier consumed signal.
 with journal.locked():
  existing=journal.read()
  if existing:
   approval=parse(secure_read(STATE/'approval.json'));admission.bind(approval,historical=True)
   need(digest(approval)==existing['approvalHash'],'ROOT_APPROVAL_DRIFT')
   return run_driver(backend,journal,approval)
  observation=backend.inspect(target)
  need(not observation['processExited'] and not observation['frozen'] and observation['fenceOwner'] is None,'ORIGINAL_APP_NOT_UNTOUCHED')
  baseline=reader.capture_baseline(target)
  approved_at=now_ms()
  candidate={'schema':core.SCHEMA,'environment':'PRODUCTION','approvalId':secrets.token_hex(16),
   'allowNonGracefulOnce':True,'acceptUnprovenInflight':True,'acceptPossibleUpstreamContinuation':True,
   'drainStatus':'UNPROVEN','approvedAt':approved_at,'deadline':approved_at+300000,
   'target':target,'expectedOriginalUnknown':baseline['expectedOriginalUnknown'],
   'expectedLeaseBindings':baseline['expectedLeaseBindings'],
   'expectedSemanticBindingsDigest':baseline['expectedSemanticBindingsDigest'],
   'capsuleHash':capsule_hash,'policyExceptionProposalHash':POLICY_PROPOSAL}
  try: approval=parse(secure_read(STATE/'approval.json'))
  except FileNotFoundError: approval=candidate
  need(approval.get('capsuleHash')==capsule_hash and approval.get('target')==target,'PREVIOUS_PENDING_TARGET_DRIFT')
  core.validate_approval(approval,now_ms())
  need(now_ms()<approval['deadline'],'NATIVE_WINDOW_EXPIRED')
  core.checkpoint_manifest(baseline,approval)
  try: previous_intent=parse(secure_read(STATE/'native-intent.json'))
  except FileNotFoundError: previous_intent=None
  if previous_intent is not None:
   need(previous_intent.get('pendingHash')==digest(approval) and previous_intent.get('capsuleHash')==capsule_hash and
        previous_intent.get('trustedClient')=='FOREGROUND_CLOUD_ROOT_TTY' and previous_intent.get('scope')=='ONE_TIME_CONTROLLED_CRASH_STOP_SOURCE_APP',
        'PREVIOUS_NATIVE_INTENT_DRIFT')
   admission.bind(approval);return run_driver(backend,journal,approval)
  terminal=terminal_factory()
  try:
   terminal.say('ONE-TIME STOP: '+HOST+' / '+target['unit']+' / PID '+str(target['pid'])+' / start '+target['startTicks'])
   terminal.say('Boot '+target['bootId']+'; invocation '+target['invocationId'])
   terminal.say('Freeze -> authenticated complete ledger checkpoint -> ONE pidfd SIGKILL -> keep restart fenced.')
   confirmed=terminal.confirm(approval,'STOP')
  finally: terminal.close()
  need(now_ms()<approval['deadline'],'NATIVE_WINDOW_EXPIRED')
  immutable(STATE/'approval.json',canonical(approval)+b'\n')
  immutable(STATE/'native-intent.json',canonical({'schema':'r16.first-stop-native-intent.v1','pendingHash':confirmed,'capsuleHash':capsule_hash,'confirmedAt':now_ms(),'trustedClient':'FOREGROUND_CLOUD_ROOT_TTY','scope':'ONE_TIME_CONTROLLED_CRASH_STOP_SOURCE_APP'})+b'\n')
  admission.bind(approval)
  return run_driver(backend,journal,approval)

def entry(mode,capsule_hash):
 need(mode in ('stop','status','recover-original'),'FIXED_ENTRY_MODE_REQUIRED')
 if mode=='stop': return stop(capsule_hash)
 directory,target=load_capsule(capsule_hash)
 admission=NativeAdmission(_BRAND,target,capsule_hash);journal=RootJournal(admission)
 with journal.locked():
  record=journal.read();need(record is not None,'NO_STOP_TRANSACTION')
  approval=parse(secure_read(STATE/'approval.json'));admission.bind(approval,historical=True)
  need(digest(approval)==record['approvalHash'],'ROOT_APPROVAL_DRIFT')
  if mode=='status':
   backend=LinuxBackend(admission,LedgerCheckpoint())
   try:
    row=backend.inspect(target)
    actual={'originalProcessExited':row['processExited'],'cgroupMembers':row['members'],
            'restartFenceOwned':row['fenceOwner']==admission.approval_hash,'frozen':row['frozen']}
   except Exception as error:
    actual={'readbackConfirmed':False,'code':getattr(error,'code','TARGET_READBACK_UNPROVEN')}
   result=record.get('receipt',{'status':record['phase'],'signalAttemptConsumed':record.get('signalAttemptConsumed',False)})
   return {**result,'historicalReadOnly':True,'liveTargetReadback':actual,'freshStopAcceptance':False,'businessAcceptance':False}
  if record.get('signalAttemptConsumed') is False:
   return recover_before_signal_native(admission,approval,journal,Terminal,LedgerCheckpoint())
  # A separate native recovery intent is obtained here by the reviewed module.
  from handoff import recover_original_native
  return recover_original_native(admission,approval,journal,Terminal,LedgerCheckpoint())

if __name__=='__main__':
 print('{"status":"PINNED_NATIVE_BOOTSTRAP_REQUIRED","productionExecutionPerformed":false}');raise SystemExit(78)


def adopt_from_successor_plan(capsule_hash,successor_plan_hash):
 """Fixed new maintenance caller, delegated by its exact native-admitted plan.

 The new capsule template explicitly pins this first-stop capsule and exception.
 No JSON supplied to this function can grant authority: both installed capsules,
 the cloud admission and their exact root-owned plans are verified afresh.
 """
 from handoff import RootSuccessorCapsule,RootPhaseJournal,handoff_to_successor,SUCCESSOR_ROOT,SUCCESSOR_STATE
 directory,target=load_capsule(capsule_hash)
 raw=secure_read(SUCCESSOR_ROOT/'SOURCE_FREEZE.json');plan=parse(secure_read(SUCCESSOR_STATE/'plan.json'))
 manifest=parse(raw);admitted=parse(secure_read(SUCCESSOR_STATE/'admission.json'))
 need(plan.get('firstStopCapsuleHash')==capsule_hash and plan.get('firstStopPolicyExceptionProposalHash')==POLICY_PROPOSAL and
      manifest.get('planTemplate',{}).get('firstStopCapsuleHash')==capsule_hash and
      digest(plan)==successor_plan_hash and plan['approvedAt']<=now_ms()<plan['expiresAt'], 'EXACT_SUCCESSOR_NATIVE_PLAN_REQUIRED')
 need(admitted.get('unused') is False and admitted.get('planHash')==successor_plan_hash and admitted.get('capsuleHash')==sha(raw) and
      now_ms()<admitted['expiresAt'] and plan['rollbackDeadline']<=admitted['expiresAt'],'SUCCESSOR_CLOUD_ADMISSION_REQUIRED')
 admission=NativeAdmission(_BRAND,target,capsule_hash);parent=RootJournal(admission)
 with parent.locked():
  approval=parse(secure_read(STATE/'approval.json'));admission.bind(approval,historical=True)
  need(approval['capsuleHash']==capsule_hash,'STOP_CAPSULE_BINDING_DRIFT')
  record=parent.read();need(record is not None,'STOP_TERMINAL_REQUIRED')
  scope={'successorPlanHash':successor_plan_hash,'successorCapsuleHash':sha(raw),
         'stopApprovalHash':digest(approval),'targetHash':digest(target)}
  successor=RootSuccessorCapsule(scope);journal=RootPhaseJournal(parent,'handoff.json')
  intent_path=STATE/'handoff-native-intent.json'
  try: intent=parse(secure_read(intent_path))
  except FileNotFoundError:
   intent={'schema':'r16.first-stop-native-successor-intent.v1','scope':scope,
           'approvedAt':plan['approvedAt'],'deadline':plan['expiresAt'],
           'trustedClient':'EXACT_NATIVE_ADMITTED_SUCCESSOR_PLAN',
           'checkpointDigest':record['checkpointDigest'],'mayStart':False,'maySign':False,'mayInstall':False,'drainStatus':'UNPROVEN'}
   parent.files.atomic(intent_path,canonical(intent),immutable=True)
  need(intent.get('scope')==scope and intent.get('trustedClient')=='EXACT_NATIVE_ADMITTED_SUCCESSOR_PLAN' and
       intent['approvedAt']<=now_ms()<intent['deadline'],'NATIVE_HANDOFF_INTENT_DRIFT')
  admission.handoff_approved=scope
  return handoff_to_successor(backend=LinuxBackend(admission,LedgerCheckpoint()),approval=approval,
      stop_record=record,journal=journal,successor=successor,capability=admission)


def recover_before_signal_native(admission,approval,journal,terminal_factory,reader):
 """Undo only this operation's pre-signal freeze/fence on the original live PID.

 A pending kernel transition is never treated as unfrozen. A fresh terminal
 scope permits cancellation of its own freeze request, followed by actual kernel
 thaw verification; no signal, new start or ledger mutation is authorized.
 """
 backend=LinuxBackend(admission,reader);target=approval['target'];owner=digest(approval)
 record=journal.read();need(record is not None and record.get('signalAttemptConsumed') is False,'PRE_SIGNAL_RECOVERY_ONLY')
 row=backend._inspect(target,allow_transition=True)
 need(not row['processExited'] and row['members']==[target['pid']] and row['fenceOwner'] in (None,owner),'ORIGINAL_LIVE_TARGET_UNPROVEN')
 baseline=reader.capture_baseline(target)
 need(baseline['expectedSemanticBindingsDigest']==approval['expectedSemanticBindingsDigest'],'ORIGINAL_SEMANTIC_DRIFT')
 path=STATE/'pre-signal-restore.json'
 try: previous=parse(secure_read(path))
 except FileNotFoundError: previous=None
 if previous is None:
  at=now_ms();recovery={'schema':'r16.first-stop-pre-signal-restore-intent.v1','targetHash':digest(target),
   'stopApprovalHash':owner,'approvedAt':at,'deadline':at+120000,'nonce':secrets.token_hex(16),
   'actions':['CANCEL_OWN_FREEZE_REQUEST','VERIFY_KERNEL_THAW','REMOVE_OWN_RESTART_FENCE'],
   'maySignal':False,'mayStart':False,'maySign':False,'mayInstall':False}
  terminal=terminal_factory()
  try:
   terminal.say('Cancel this attempt before any kill: thaw only the same original live App and remove only our restart fence. No new process is started.')
   terminal.confirm(recovery,'RESTORE_RUNNING')
  finally:terminal.close()
  scope={'preSignal':True,'recoveryHash':digest(recovery),'stopApprovalHash':owner,'targetHash':digest(target)}
  previous={'schema':'r16.first-stop-pre-signal-restore-journal.v1','scope':scope,'phase':'RESTORE_INTENT','recovery':recovery}
  journal.files.atomic(path,canonical(previous),immutable=True)
 else:
  recovery=previous['recovery'];scope=previous['scope']
 need(previous.get('phase')=='RESTORE_INTENT' and scope=={'preSignal':True,'recoveryHash':digest(recovery),'stopApprovalHash':owner,'targetHash':digest(target)} and
      recovery['approvedAt']<=now_ms()<recovery['deadline'],'PRE_SIGNAL_RESTORE_SCOPE_EXPIRED_OR_DRIFT')
 admission.recovery_approved=scope
 if row['frozen'] or row.get('freezeRequested'):
  need(row['freezeOwner']==owner and row['fenceOwner']==owner,'OWNED_FREEZE_REQUIRED');backend.unfreeze(target,owner)
 row=backend.inspect(target);need(not row['frozen'] and not row.get('freezeRequested') and not row['processExited'],'ORIGINAL_THAW_UNPROVEN')
 return run_driver(backend,journal,approval)
