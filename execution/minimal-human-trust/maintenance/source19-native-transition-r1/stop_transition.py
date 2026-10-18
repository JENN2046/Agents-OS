"""Same-plan external Native maintenance stop, never a business STOP.

The admitted installer's fixed OS adapter owns native approval and real effects.
No CLI, arbitrary PID input, privilege escalation, signer or production default
backend is supplied. A lost effect is observed; it is never replayed here.
"""
from copy import deepcopy
import hashlib
import json
import re

LOCAL = 'jenn-System-Product-Name'
CLOUD = 'VM-0-12-ubuntu'
NATIVE = 'r16-native.service'
RELAY = 'r16-native-link.service'
HOSTS = {'r16-app.service': CLOUD, 'r16-bridge.service': CLOUD,
         RELAY: LOCAL, 'r16-owner.service': LOCAL, NATIVE: LOCAL}
GRACEFUL_ORDER = ('r16-app.service', 'r16-bridge.service', RELAY, 'r16-owner.service')
PUBLIC = '56e1df18a54950ea346a51654e61df60afe33cb9928ae77293b2cf336fd8a5ec'
DELIVERY = 'b8645f6fe206e84dd07c2c6c166bfe4016d1deefca28bf9545dcfa1560f013e9'
GRANT = '00ac437d66143e627132975555d06396d69ff69616f630d19e3622627e15c5e6'
SOURCE_NATIVE = '2516e881b0622b3ac2d53c454e6ccf9950441c5cb3c26a53500b45d3b1dbe7b4'
TARGET_RELEASE = 'r16-daily-20261017-source19-native-lifecycle-r1'
SCHEMA = 'r16.source19-native-transition.plan.v1'
BRIDGE_SCHEMA = 'r16.source19-native-transition.stopped-fenced.v1'
SCOPE = 'SAME_PLAN_SOURCE19_NATIVE_MAINTENANCE_NOT_DRAINED'
UNKNOWN = {
 'p2vox': {'id':'c434da49-055a-43dc-a3e3-695cce137909','generation':30,
           'hash':'fd13e74ce69cb8ec30817ca0a48631cf3a6b6b2b08a410cc1b442df41992cc1f'},
 'pmog2': {'id':'d0364f8b-3a68-4ca2-a396-7953b29cee4c','generation':38,
           'hash':'38f6af1386e78e5d7ccd0710077d6a3a5e753e81722dd10f11a3a2ff9bd85da1'}}

class Refused(Exception):
 def __init__(self, code): self.code = code; super().__init__(code)
def need(value, code):
 if not value: raise Refused(code)
def canonical(value):
 def ordered(x):
  if isinstance(x, dict): return {k:ordered(x[k]) for k in sorted(x, key=lambda k:k.encode('utf-16-be'))}
  if isinstance(x, list): return [ordered(v) for v in x]
  need(x is None or type(x) in (int, bool, str), 'CANONICAL_VALUE')
  return x
 return json.dumps(ordered(value), ensure_ascii=False, separators=(',',':')).encode()
def digest(value): return hashlib.sha256(canonical(value)).hexdigest()
def ishash(value): return isinstance(value,str) and re.fullmatch('[a-f0-9]{64}',value) is not None

def fence_bytes(plan_hash):
 need(ishash(plan_hash),'PLAN_HASH')
 # /etc drop-in + /var/lib missing condition survive reboot. No start token
 # is created by this module, including on recovery or a repeated invocation.
 return ('# Source19 Native maintenance '+plan_hash+'\n[Unit]\nRefuseManualStart=yes\n'
         'ConditionPathExists=/var/lib/r16-maintenance/source19-native-transition-r1/never-start-implicitly\n'
         '[Service]\nRestart=no\nKillSignal=SIGTERM\nSendSIGKILL=no\n').encode()
def fence_path(unit):
 need(unit in HOSTS,'FIXED_UNIT_REQUIRED')
 return '/etc/systemd/system/'+unit+'.d/96-source19-native-transition-r1.conf'

def validate_plan(p, now, *, historical=False):
 fields={'schema','scope','sourcePublicConfigHash','sourceDeliveryHash','grantHash','sourceNativeVersion',
         'targetReleaseId','targetNativeVersion','targetInventoryHash','codeFreezeHash','originalBaselineHash',
         'nativeTargetHash','stopEpoch','nonce','approvedAt','expiresAt','recoveryDeadline',
         'allowNativeNonGracefulOnce','acceptUnprovenInflight','acceptPossibleUpstreamContinuation',
         'recoveryPolicy','revisionPlanHash','approvedControlUnknownHash','approvedControlUnknownCount'}
 need(isinstance(p,dict) and set(p)==fields,'EXACT_PLAN_FIELDS')
 need(p['schema']==SCHEMA and p['scope']==SCOPE,'EXACT_MAINTENANCE_SCOPE')
 need((p['sourcePublicConfigHash'],p['sourceDeliveryHash'],p['grantHash'],p['sourceNativeVersion'])==
      (PUBLIC,DELIVERY,GRANT,SOURCE_NATIVE),'SOURCE19_IDENTITY')
 need(p['targetReleaseId']==TARGET_RELEASE and p['targetNativeVersion']!=SOURCE_NATIVE,'NEW_NATIVE_IDENTITY_REQUIRED')
 for key in ('targetNativeVersion','targetInventoryHash','codeFreezeHash','originalBaselineHash','nativeTargetHash','revisionPlanHash','approvedControlUnknownHash'):
  need(ishash(p[key]),'PLAN_CONTENT_HASH')
 need(re.fullmatch('[a-f0-9]{32}',p['nonce'] or '') and re.fullmatch('[a-f0-9]{8}(?:-[a-f0-9]{4}){3}-[a-f0-9]{12}',p['stopEpoch'] or ''),'PLAN_NONCE')
 a,e,r=(p[k] for k in ('approvedAt','expiresAt','recoveryDeadline'))
 need(all(type(t) is int for t in (a,e,r,now)) and 0<e-a<=300000 and e<=r<=a+1800000,'PLAN_TIME')
 if not historical: need(a<=now<e,'PLAN_EXPIRED')
 need(all(p[k] is True for k in ('allowNativeNonGracefulOnce','acceptUnprovenInflight','acceptPossibleUpstreamContinuation')),'EXPLICIT_NON_DRAINED_APPROVAL_REQUIRED')
 need(type(p['approvedControlUnknownCount']) is int and 0<=p['approvedControlUnknownCount']<=100000,'EXACT_CONTROL_UNCERTAINTY_COUNT')
 need(p['recoveryPolicy']=='KEEP_CRASHED_NATIVE_STOPPED_NO_AUTOMATIC_BUSINESS_REOPEN','RECOVERY_POLICY')
 return digest(p)

def validate_checkpoint(c,p=None):
 need(isinstance(c,dict) and c.get('schema')=='r16.source19-native-checkpoint.v1','NATIVE_CHECKPOINT_REQUIRED')
 need(c.get('completeRegisteredFileSet') is True and c.get('noForeignWriters') is True and c.get('noTemporaryFiles') is True,'COMPLETE_NATIVE_WRITER_CHECKPOINT_REQUIRED')
 need(c.get('newUnknown')==[] and c.get('inflight')==[],'CURRENT_WORK_UNRESOLVED')
 controls=c.get('controlUnknownRows')
 need(isinstance(controls,list) and len(controls)<=100000 and all(isinstance(x,dict) and set(x)=={'id','hash','status'} and isinstance(x['id'],str) and ishash(x['hash']) and x['status']=='UNKNOWN' for x in controls),'CONTROL_UNCERTAINTY_SET_REQUIRED')
 need(len({x['id'] for x in controls})==len(controls),'CONTROL_ID_CONFLICT')
 control_hash=digest(sorted(controls,key=lambda x:x['id']))
 need(c.get('controlUnknownHash')==control_hash and c.get('controlUnknownCount')==len(controls),'CONTROL_UNCERTAINTY_HASH')
 if p:need(control_hash==p['approvedControlUnknownHash'] and len(controls)==p['approvedControlUnknownCount'],'UNAPPROVED_CONTROL_UNCERTAINTY')
 reg=c.get('nativeLedgerRegistration',{})
 need(set(reg)=={'directory','dev','ino','registryHash'} and isinstance(reg['directory'],str) and reg['directory'].startswith('/') and all(type(reg[k]) is int and reg[k]>0 for k in ('dev','ino')) and ishash(reg['registryHash']),'NATIVE_LEDGER_REGISTRATION_REQUIRED')
 need(c.get('originalUnknown')==UNKNOWN and c.get('originalSignaturesAndLeasesVerified') is True,'ORIGINAL_UNKNOWN_IDENTITY')
 need(ishash(c.get('originalLeaseBindingsHash')) and ishash(c.get('registeredRootsHash')),'LEASE_AND_REGISTRY_BINDING')
 rows=c.get('files');need(isinstance(rows,dict) and 3<=len(rows)<=100000,'CHECKPOINT_FILES')
 for name,row in rows.items():
  need(isinstance(name,str) and not name.startswith('/') and '\\' not in name and all(x not in ('','.','..') for x in name.split('/')),'CHECKPOINT_PATH')
  need(isinstance(row,dict) and set(row)=={'sha256','bytes','mode','dev','ino'} and ishash(row['sha256']) and
       type(row['bytes']) is int and row['bytes']>=0 and row['mode'] in (384,420) and all(type(row[k]) is int and row[k]>0 for k in ('dev','ino')),'CHECKPOINT_FILE')
 need(c.get('sqliteFilesEnumerated') is True and c.get('liveDatabaseOpened') is False,'SQLITE_CRASH_SNAPSHOT_REQUIRED')
 return digest(c)

class Driver:
 """The existing trusted installer injects admission, locked journal and IO.

 backend.require(plan,operation) verifies its actual native admission before
 every effect, not a boolean from the caller. capture_original() returns all
 FIVE fixed units. observe_native() binds the exact original PID/start/boot/
 invocation/cgroup/code; Native must be singleton or already exited. Scope is
 intentionally not widened to killing arbitrary children.
 """
 def __init__(self,backend,journal,now,fault=lambda _:None):
  need(getattr(backend,'environment',None) in ('ISOLATED_TEST','PRODUCTION'),'BACKEND_ENVIRONMENT_REQUIRED')
  self.b=backend;self.j=journal;self.now=now;self.fault=fault
 def save(self,r): self.b.require(r['planHash'],'journal');self.j.write(deepcopy(r));self.fault('saved:'+r['phase'])
 def current(self,p): need(p['approvedAt']<=self.now()<p['expiresAt'],'PLAN_EXPIRED')
 def effect(self,p,r,name,fn):
  self.current(p);self.b.require(r['planHash'],name)
  need(name not in r['effects'],'EFFECT_ALREADY_CONSUMED')
  r['effects'][name]={'state':'INTENT'};r['phase']=name
  if name=='native-signal':r['signalAttemptConsumed']=True
  self.save(r);self.current(p);self.b.require(r['planHash'],name)
  result=fn();self.fault('effect:'+name)
  r['effects'][name]={'state':'RETURNED'};self.save(r);return result
 def observe_stopped(self,p,r):
  # Read-only reconciliation is allowed after expiry. It cannot renew authority,
  # issue another signal, unfreeze, remove a fence or start any role.
  self.b.require(r['planHash'],'observe')
  rows=self.b.observe_all(r['originalBaseline'],r['planHash'])
  need(set(rows)==set(HOSTS),'EXACT_FIVE_ROLES_REQUIRED')
  for unit,row in rows.items():
   need(row.get('host')==HOSTS[unit] and row.get('unit')==unit and row.get('mainPid')==0 and row.get('controlPid')==0 and
        row.get('cgroupEmpty') is True and row.get('ownedPersistentFence') is True and row.get('pendingJob') is False,'STOPPED_FENCED_SCOPE_UNPROVEN')
  checkpoint=self.b.checkpoint_native();need(validate_checkpoint(checkpoint,p)==r['checkpointHash'],'CHECKPOINT_CHANGED_AFTER_STOP')
  actors={unit:deepcopy(row) for unit,row in rows.items() if unit!=RELAY}
  proof={'schema':BRIDGE_SCHEMA,'status':'STOPPED_FENCED_NOT_DRAINED','planHash':r['planHash'],'environment':self.b.environment,
   'controlUnknownHash':p['approvedControlUnknownHash'],'controlUnknownCount':p['approvedControlUnknownCount'],
   **{k:p[k] for k in ('sourcePublicConfigHash','sourceDeliveryHash','grantHash','codeFreezeHash','originalBaselineHash','nativeTargetHash','stopEpoch')},
   'checkpointHash':r['checkpointHash'],'actors':actors,'relayStopped':True,'noForeignWriters':True,'originalUnknownPreserved':True,
   'globalExecution':'UNPROVEN','forceTerminationUsed':r['signalAttemptConsumed'],'issuedAt':self.now(),'expiresAt':min(self.now()+30000,p['recoveryDeadline']),
   'businessAcceptance':False,'roleStopReceipt':False}
  r['proof']=proof;r['phase']='STOPPED_FENCED_NOT_DRAINED';self.save(r);return deepcopy(proof)
 def run(self,p):
  h=validate_plan(p,self.now(),historical=self.j.read() is not None)
  self.b.require(h,'bind')
  old=self.j.read()
  if old:
   need(old.get('schema')=='r16.source19-native-transition.journal.v1' and old.get('planHash')==h,'JOURNAL_PLAN_CONFLICT')
   need(digest(old.get('originalBaseline'))==p['originalBaselineHash'] and digest(old.get('originalBaseline',{}).get(NATIVE))==p['nativeTargetHash'],'JOURNAL_BASELINE_CORRUPT')
   need(type(old.get('signalAttemptConsumed')) is bool and old['signalAttemptConsumed']==('native-signal' in old.get('effects',{})),'JOURNAL_SIGNAL_STATE_CORRUPT')
   if old.get('checkpointHash'):need(validate_checkpoint(old.get('checkpoint'),p)==old['checkpointHash'],'JOURNAL_CHECKPOINT_CORRUPT')
   if old.get('checkpointHash'):
    try:return self.observe_stopped(p,old)
    except Refused:return {'status':'RECOVERY_REQUIRED_READBACK_ONLY','planHash':h,'signalAttemptConsumed':old['signalAttemptConsumed'],'automaticRetry':False,'businessAcceptance':False}
   return {'status':'RECOVERY_REQUIRED_READBACK_ONLY','planHash':h,'signalAttemptConsumed':old['signalAttemptConsumed'],'automaticRetry':False,'businessAcceptance':False}
  self.current(p);baseline=self.b.capture_original()
  need(set(baseline)==set(HOSTS) and digest(baseline)==p['originalBaselineHash'],'ORIGINAL_BASELINE_DRIFT')
  need(digest(baseline[NATIVE])==p['nativeTargetHash'],'NATIVE_INSTANCE_DRIFT')
  r={'schema':'r16.source19-native-transition.journal.v1','planHash':h,'phase':'BOUND','originalBaseline':deepcopy(baseline),'effects':{},'signalAttemptConsumed':False}
  self.save(r);handle=None
  try:
   for unit in HOSTS:
    self.effect(p,r,'fence:'+unit,lambda unit=unit:self.b.fence(unit,h,fence_path(unit),fence_bytes(h)))
   self.b.verify_all_fences(h)
   for unit in GRACEFUL_ORDER:
    self.effect(p,r,'graceful:'+unit,lambda unit=unit:self.b.graceful_stop(unit,h))
    self.b.verify_original_native_or_exited(baseline[NATIVE])
   native=self.b.observe_native(baseline[NATIVE])
   if not native['exited']:
    self.effect(p,r,'graceful:'+NATIVE,lambda:self.b.graceful_native_once(baseline[NATIVE],p['expiresAt']))
    native=self.b.observe_native(baseline[NATIVE])
   if not native['exited']:
    need(native.get('members')==[baseline[NATIVE]['pid']],'NATIVE_NON_SINGLETON_REFUSED')
    handle=self.b.open_native_pidfd(baseline[NATIVE])
    self.effect(p,r,'native-freeze',lambda:self.b.freeze_native(baseline[NATIVE],h))
    self.b.verify_frozen_singleton(baseline[NATIVE],h)
   checkpoint=self.b.checkpoint_native();r['checkpointHash']=validate_checkpoint(checkpoint,p);r['checkpoint']=checkpoint;r['phase']='CHECKPOINT_SAVED';self.save(r)
   if not native['exited']:
    # A queued dependency stop may have modified closing before the freeze.
    # This checkpoint is B, after those legal effects, not a fabricated A==B.
    self.b.verify_frozen_singleton(baseline[NATIVE],h)
    self.effect(p,r,'native-signal',lambda:self.b.kill_native_pidfd_once(handle,baseline[NATIVE],p['expiresAt']))
   return self.observe_stopped(p,r)
  except Exception as error:
   if getattr(error,'simulatedCrash',False):raise
   r['phase']='RECOVERY_REQUIRED_READBACK_ONLY';r['failureCode']=error.code if isinstance(error,Refused) else 'OS_EFFECT_UNCONFIRMED';self.save(r)
   return {'status':r['phase'],'planHash':h,'failureCode':r['failureCode'],'signalAttemptConsumed':r['signalAttemptConsumed'],'automaticRetry':False,'businessAcceptance':False}
  finally:
   if handle is not None:self.b.close_pidfd(handle)

if __name__=='__main__':
 print(json.dumps({'status':'PROTECTED_INSTALLER_ADMISSION_REQUIRED','productionEffects':0,'businessAcceptance':False}));raise SystemExit(78)
