"""Exact empty artifact quarantine protocol; no OS, ledger or network access.

The admitted backend is the sole reader/effect adapter. This driver persists
metadata/hashes only, never private ledger bytes. Durable effect intents are
consumed before invocation. Re-entry only observes; inverse recovery needs a
new native intent and cannot replay an uncertain rename.
"""
from copy import deepcopy
import hashlib
import json
import re

SCHEMA='r16.exact-empty-artifact-quarantine.v1'
RECOVERY_SCHEMA='r16.exact-empty-artifact-quarantine-recovery.v1'
INVENTORY_SCHEMA='r16.exact-empty-artifact-full-inventory.v1'
POLICY_HASH='1ee6217b557dbce981211929201864bfbdde0b278e84b4081937354b09300a9c'
ARTIFACT_PATH='/var/lib/r16-app/grants/r16-projects-daily/host/.next-6f6c6887-4fa7-450a-a199-683eadfde1b5'
ARTIFACT_NAME='host/.next-6f6c6887-4fa7-450a-a199-683eadfde1b5'
EMPTY_SHA=hashlib.sha256(b'').hexdigest()
ARTIFACT={'dev':64770,'ino':1039403,'bytes':0,'sha256':EMPTY_SHA,'uid':1000,'gid':1001,'mode':0o600,'nlink':1,'mtimeNs':'1792126254419345897','ctimeNs':'1792126254419345897'}
SOURCE_HASHES={
 'app/app-runner.mjs':'9fa13d0fe708d62e8ec34db680212d9d1857014c4e08bbaf1b00c60c8f602737',
 'app/workspace-host.mjs':'119756c7bb950308a1edb062b93c4848b5280e9ba356c13d6660f96b192915d2',
 'app/upstream/src/server.mjs':'08524d426f543b10e3806204111d4ed979c300baf220b5afb10f08c1da856912',
 'app/upstream/src/project-forge-crown-executor.mjs':'01f09efacf4169f88215815824acec8f4e9e1c5d2451d3e872dd4dad2bb49033',
 'src/lease-core.mjs':'889232f53d5c014138a7004df32c8e4f4f6c16703b6d53fa75ce0cbcf53e43b9',
}
TARGET={'host':'VM-0-12-ubuntu','unit':'r16-app.service','pid':1442662,'startTicks':'188708415','bootId':'cbe93e9f-9f2d-4139-8b94-3ffbcc8e43fe','invocationId':'bd1db422e3404b6984961c5215374e98','nRestarts':0,'cgroup':'/system.slice/r16-app.service','sourceHashes':SOURCE_HASHES}
TERMINAL=('EMPTY_ARTIFACT_QUARANTINED_ORIGINAL_RUNTIME_RESTORED','QUARANTINE_ABORTED_ORIGINAL_ARTIFACT_AND_RUNTIME_RESTORED','ARTIFACT_RESTORED_NOT_BUSINESS_ACCEPTED')

class Refused(Exception):
 def __init__(self,code):self.code=code;super().__init__(code)
def need(ok,code):
 if not ok:raise Refused(code)
def ishash(v):return isinstance(v,str) and re.fullmatch('[0-9a-f]{64}',v) is not None
def ns(v):return isinstance(v,str) and re.fullmatch('0|[1-9][0-9]{0,19}',v) is not None
def canonical(v):
 if v is None:return 'null'
 if type(v) is bool:return 'true' if v else 'false'
 if type(v) is int:
  need(abs(v)<=9007199254740991,'NONCANONICAL_JSON');return str(v)
 if isinstance(v,str):
  raw=json.dumps(v,ensure_ascii=False,separators=(',',':'))
  return ''.join('\\u%04x'%ord(c) if 0xD800<=ord(c)<=0xDFFF else c for c in raw)
 if isinstance(v,list):return '['+','.join(canonical(x) for x in v)+']'
 need(type(v) is dict and all(isinstance(k,str) and k not in ('__proto__','prototype','constructor') for k in v),'NONCANONICAL_JSON')
 return '{'+','.join(canonical(k)+':'+canonical(v[k]) for k in sorted(v,key=lambda k:k.encode('utf-16-be','surrogatepass')))+'}'
def digest(v):return hashlib.sha256(canonical(v).encode()).hexdigest()
def code(e):
 value=getattr(e,'code',None)
 return value if isinstance(value,str) and re.fullmatch('[A-Z0-9_]{1,100}',value) else 'BOUNDED_BACKEND_FAILURE'

def validate_approval(a,now):
 fields={'schema','environment','approvalId','approvedAt','deadline','policyProposalHash','sourceCapsuleHash','capsuleHash','target','artifact','allowExactEmptyArtifactQuarantine','acceptPossibleInMemoryStorePoisoning','drainStatus'}
 need(type(a) is dict and set(a)==fields and a['schema']==SCHEMA,'EXACT_QUARANTINE_APPROVAL_REQUIRED')
 need(a['environment'] in ('ISOLATED_TEST','PRODUCTION'),'NATIVE_ENVIRONMENT_REQUIRED')
 need(isinstance(a['approvalId'],str) and re.fullmatch('[A-Za-z0-9_-]{8,80}',a['approvalId']),'APPROVAL_ID_REQUIRED')
 need(type(a['approvedAt']) is int and type(a['deadline']) is int and a['approvedAt']<=now and 0<a['deadline']-a['approvedAt']<=300000,'APPROVAL_WINDOW_REFUSED')
 need(a['policyProposalHash']==POLICY_HASH and ishash(a['sourceCapsuleHash']) and ishash(a['capsuleHash']),'POLICY_OR_CAPSULE_BINDING_REQUIRED')
 need(a['target']==TARGET and type(a['target']['pid']) is int and type(a['target']['nRestarts']) is int,'EXACT_SOURCE_TARGET_REQUIRED')
 need(a['artifact']=={'path':ARTIFACT_PATH,**ARTIFACT} and all(type(a['artifact'][k]) is int for k in ('dev','ino','bytes','uid','gid','mode','nlink')),'EXACT_EMPTY_ARTIFACT_REQUIRED')
 need(a['allowExactEmptyArtifactQuarantine'] is True and a['acceptPossibleInMemoryStorePoisoning'] is True and a['drainStatus']=='UNPROVEN','EXPLICIT_QUARANTINE_SCOPE_REQUIRED')
 canonical(a)
 return deepcopy(a['target'])

def validate_inventory(value,*,before,inverse=False):
 need(type(value) is dict and type(value.get('files')) is dict and type(value.get('directories')) is dict,'FORENSIC_INVENTORY_REQUIRED')
 if before:
  base={'schema','files','directories','noOpenArtifactHandles','otherWriterPids','registrationHash','registeredProjectCount','drainStatus','artifact','artifactLocation'}
  need(set(value)==base|({'ledgerAttestation'} if inverse else set()) and value['schema']==INVENTORY_SCHEMA and value['noOpenArtifactHandles'] is True and value['otherWriterPids']==[] and ishash(value['registrationHash']) and type(value['registeredProjectCount']) is int and value['registeredProjectCount']==len(value['directories'])-1 and value['drainStatus']=='UNPROVEN','FORENSIC_INVENTORY_REQUIRED')
 files=value['files'];dirs=value['directories'];need(3<=len(files)<=100000 and 3<=len(dirs)<=4097,'INVENTORY_CAPACITY_REFUSED')
 need('host' in dirs and 'host/state.json' in files,'INCOMPLETE_FORENSIC_INVENTORY')
 identities=set();total=0
 for directory,row in dirs.items():
  need(isinstance(directory,str) and re.fullmatch('host(?:/project-[A-Za-z0-9_-]{1,128})?',directory) and type(row) is dict and set(row)=={'dev','ino','uid','gid','mode','mtimeNs','ctimeNs'} and all(type(row[k]) is int for k in ('dev','ino','uid','gid','mode')) and row['dev']>=0 and row['ino']>0 and row['uid']==1000 and row['gid']>=0 and row['mode']==0o700 and ns(row['mtimeNs']) and ns(row['ctimeNs']),'DIRECTORY_INVENTORY_REFUSED')
  need(directory+'/state.json' in files,'INCOMPLETE_FORENSIC_INVENTORY')
 for name,row in files.items():
  need(isinstance(name,str) and '/' in name and len(name)<=512,'FILE_INVENTORY_REFUSED')
  parent,base=name.rsplit('/',1)
  need(parent in dirs and (name==ARTIFACT_NAME or base in ('state.json','.lock') or re.fullmatch('archive-[A-Za-z0-9_-]+[.]json',base)),'UNEXPECTED_STORE_ARTIFACT')
  need(type(row) is dict and set(row)==set(ARTIFACT) and all(type(row.get(k)) is int for k in ('dev','ino','bytes','uid','gid','mode','nlink')) and row['dev']>=0 and row['ino']>0 and row['uid']==1000 and row['gid']>=0 and row['mode']==0o600 and row['nlink']==1 and ns(row['mtimeNs']) and ns(row['ctimeNs']) and ishash(row['sha256']),'FILE_INVENTORY_REFUSED')
  need(0<=row['bytes']<=16*1024*1024 and (name==ARTIFACT_NAME or row['bytes']>0),'FILE_INVENTORY_REFUSED')
  identity=(row['dev'],row['ino']);need(identity not in identities,'ALIASED_STORE_INODE');identities.add(identity)
  total+=row['bytes'];need(total<=64*1024*1024,'INVENTORY_CAPACITY_REFUSED')
 if before:
  if inverse:need(value['artifactLocation']=='QUARANTINE' and ARTIFACT_NAME not in files and artifact_matches(value['artifact']),'EXACT_EMPTY_ARTIFACT_REQUIRED')
  else:need(value['artifactLocation']=='SOURCE' and files.get(ARTIFACT_NAME)==ARTIFACT and value['artifact']==ARTIFACT,'EXACT_EMPTY_ARTIFACT_REQUIRED')
 return deepcopy(value)

def artifact_matches(row):
 return type(row) is dict and set(row)==set(ARTIFACT) and ns(row.get('ctimeNs')) and all(row[k]==v and (type(row[k]) is int if type(v) is int else True) for k,v in ARTIFACT.items() if k!='ctimeNs')

class Driver:
 """Injected fixed backend, atomic durable journal, integer clock; no I/O here."""
 def __init__(self,backend,journal,now,fault=lambda point:None):
  need(getattr(backend,'environment',None) in ('ISOLATED_TEST','PRODUCTION'),'NATIVE_ENVIRONMENT_REQUIRED')
  self.backend=backend;self.journal=journal;self.now=now;self.fault=fault
 def save(self,r):self.journal.write(deepcopy(r));self.fault('journal:'+r['phase'])
 def window(self,a):need(self.now()<a['deadline'],'APPROVAL_EXPIRED')
 def observe(self,a,owner,*,recovery=False):
  o=(self.backend.inspect_recovery if recovery else self.backend.inspect)(a['target'])
  need(type(o) is dict and all(o.get(k)==v and (type(o[k]) is int if type(v) is int else True) for k,v in a['target'].items()),'TARGET_IDENTITY_DRIFT')
  need(o.get('processExited') is False and o.get('members')==[a['target']['pid']] and o.get('activeState')=='active' and o.get('subState')=='running','ORIGINAL_LIVE_PROCESS_REQUIRED')
  need(type(o.get('frozen')) is bool and type(o.get('freezeRequested')) is bool and (recovery or o['frozen']==o['freezeRequested']),'FREEZE_TRANSITION_UNPROVEN')
  need(o.get('fenceOwner') in (None,owner) and o.get('freezeOwner') in (None,owner),'FOREIGN_PROTECTION_REFUSED')
  need(((o['frozen'] or o['freezeRequested']) and o['freezeOwner']==owner and o['fenceOwner']==owner) or (not o['frozen'] and not o['freezeRequested'] and o['freezeOwner'] is None),'FREEZE_OWNERSHIP_DRIFT')
  return o
 def frozen(self,a,r):
  o=self.observe(a,r['approvalHash']);need(o['frozen'] and o['fenceOwner']==r['approvalHash'],'OWNED_FROZEN_PROCESS_REQUIRED');return o
 def intent(self,r,phase,flag=None):
  r['phase']=phase
  if flag:r[flag]=True
  self.save(r)
 def proof(self,r,value,location,*,validated):
  validate_inventory(value,before=False)
  need(value.get('artifactLocation')==location and artifact_matches(value.get('artifact')),'EXACT_ARTIFACT_LOCATION_UNPROVEN')
  baseline=r.get('inverseBefore',r['before'])
  if location=='QUARANTINE':
   expected=baseline['artifact'] if 'inverseBefore' in r else r.get('quarantinedArtifact')
   need(value['artifact']==expected,'QUARANTINED_CTIME_BINDING_UNPROVEN')
  expected={n:v for n,v in baseline['files'].items() if n!=ARTIFACT_NAME}
  actual={n:v for n,v in value['files'].items() if n!=ARTIFACT_NAME}
  olddirs=deepcopy(baseline['directories']);newdirs=deepcopy(value['directories'])
  for dirs in (olddirs,newdirs):
   for k in ('mtimeNs','ctimeNs'):dirs['host'].pop(k)
  need(actual==expected and newdirs==olddirs and value.get('registrationHash')==baseline['registrationHash'] and value.get('registeredProjectCount')==baseline['registeredProjectCount'],'NORMAL_STORE_INVENTORY_CHANGED')
  need((location=='SOURCE' and value['files'].get(ARTIFACT_NAME)==value['artifact']) or (location=='QUARANTINE' and ARTIFACT_NAME not in value['files']),'ARTIFACT_PATH_PROOF_DRIFT')
  if validated:
   att=value.get('ledgerAttestation')
   need(type(att) is dict and att.get('schema')=='r16.r15-app-ledger-attestation.v1' and att.get('signatureVerification') is True and att.get('sealedRegistrationVerified') is True and att.get('oldGrantActive') is True and type(att.get('sourceDeliveryRevision')) is int and att['sourceDeliveryRevision']==16 and type(att.get('originalUnknownCount')) is int and att['originalUnknownCount']==2 and type(att.get('registeredProjectCount')) is int and att['registeredProjectCount']==len(baseline['directories'])-1 and att.get('drainStatus')=='UNPROVEN' and all(ishash(att.get(k)) for k in ('sourcePublicConfigDigest','grantHash','checkpointManifestDigest','semanticBindingsDigest','registrationHash')),'UNCHANGED_R8_VERIFIER_PROOF_REQUIRED')
   r['ledgerProofHash']=digest(att)
  r['verifiedManifestHash']=digest(value['files']);r['artifactCtimeNs']=value['artifact']['ctimeNs']
 def terminal(self,r,status):
  receipt={'schema':'r16.exact-empty-artifact-quarantine-receipt.v1','status':status,'approvalHash':r['approvalHash'],'targetHash':r['targetHash'],'beforeManifestHash':r.get('beforeManifestHash'),'inverseBeforeManifestHash':r.get('inverseBeforeManifestHash'),'verifiedManifestHash':r.get('verifiedManifestHash'),'ledgerProofHash':r.get('ledgerProofHash'),'ledgerValidatedWhileFrozen':r.get('ledgerProofHash') is not None,'fileCount':len(r.get('before',{}).get('files',{})),'quarantineAttemptConsumed':r.get('quarantineAttemptConsumed',False),'inverseAttemptConsumed':r.get('inverseAttemptConsumed',False),'automaticRenameReplayAllowed':False,'drainStatus':'UNPROVEN','inMemoryStoreHealth':'UNPROVEN','originalProcessRunning':True,'signalOrRestartPerformed':False,'inverseRecoveryScope':'NEW_NATIVE_EXACT_INTENT_AND_FRESH_BASELINE','environment':self.backend.environment,'productionExecutionPerformed':self.backend.environment=='PRODUCTION'}
  receipt['businessAcceptance']=False
  r['phase']='TERMINAL';r['receipt']=receipt;self.save(r);return receipt
 def pending(self,r,failure=None):
  if failure:r['phase']='RECOVERY_REQUIRED';r['failureCode']=failure;self.save(r)
  return {'status':'RECOVERY_REQUIRED','phase':r['phase'],'approvalHash':r['approvalHash'],'failureCode':r.get('failureCode'),'quarantineAttemptConsumed':r.get('quarantineAttemptConsumed',False),'inverseAttemptConsumed':r.get('inverseAttemptConsumed',False),'automaticRenameReplayAllowed':False,'newNativeRecoveryIntentRequired':True,'drainStatus':'UNPROVEN','signalOrRestartPerformed':False,'businessAcceptance':False}
 def status(self,a):
  validate_approval(a,self.now())
  r=self.journal.read();need(type(r) is dict and r.get('approvalHash')==digest(a),'JOURNAL_APPROVAL_DRIFT')
  if r.get('phase')=='TERMINAL':return deepcopy(r['receipt'])
  # Read-only reconciliation never makes an unresolved intent replayable.
  try:
   self.observe(a,r['approvalHash']);where=self.backend.inspect_artifact(a['target'],r['approvalHash'])
   need(where.get('location') in ('SOURCE','QUARANTINE') and artifact_matches(where.get('artifact')),'ARTIFACT_LOCATION_UNPROVEN')
   result=self.pending(r);result['artifactLocation']=where['location'];return result
  except Exception as e:
   result=self.pending(r);result['observationCode']=code(e);return result
 def release(self,a,r,rollback):
  self.frozen(a,r);self.window(a)
  r['releaseResultStatus']=TERMINAL[2] if r.get('postSuccessInverse') else TERMINAL[1] if rollback else TERMINAL[0]
  r['releaseResultCycle']=r['releaseCycle'];r['thawIntentCycle']=r['releaseCycle']
  self.intent(r,'THAW_INTENT','thawAttemptConsumed')
  self.backend.unfreeze(a['target'],r['approvalHash']);self.fault('effect:thaw')
  o=self.observe(a,r['approvalHash']);need(not o['frozen'] and o['fenceOwner']==r['approvalHash'],'THAW_UNPROVEN')
  self.window(a);r['unfenceIntentCycle']=r['releaseCycle'];self.intent(r,'UNFENCE_INTENT','unfenceAttemptConsumed')
  self.backend.unfence(a['target'],r['approvalHash']);self.fault('effect:unfence')
  o=self.observe(a,r['approvalHash']);need(not o['frozen'] and o['fenceOwner'] is None,'ORIGINAL_RUNTIME_RESTORE_UNPROVEN')
  return self.terminal(r,r['releaseResultStatus'])
 def restore_and_release(self,a,r):
  self.frozen(a,r);where=self.backend.inspect_artifact(a['target'],r['approvalHash'])
  need(where.get('location') in ('SOURCE','QUARANTINE') and artifact_matches(where.get('artifact')),'ARTIFACT_LOCATION_UNPROVEN')
  baseline=r.get('inverseBefore',r['before'])
  if where['location']=='QUARANTINE':
   need(not r.get('inverseAttemptConsumed'),'INVERSE_INTENT_ALREADY_CONSUMED');self.window(a)
   expected=r.get('quarantinedArtifact') if 'inverseBefore' not in r else baseline['artifact']
   need(expected is not None and where['artifact']==expected,'QUARANTINED_CTIME_BINDING_UNPROVEN')
   baseline=deepcopy(baseline);baseline['expectedQuarantinedArtifact']=expected
   self.intent(r,'RESTORE_INTENT','inverseAttemptConsumed')
   self.backend.restore(a['target'],r['approvalHash'],baseline);self.fault('effect:restore')
  proof=self.backend.verify_restored(a['target'],baseline,r['approvalHash']);self.proof(r,proof,'SOURCE',validated=False)
  self.intent(r,'RESTORED');return self.release(a,r,True)
 def run(self,a):
  validate_approval(a,self.now());need(a['environment']==self.backend.environment,'NATIVE_ENVIRONMENT_REQUIRED')
  if self.journal.read() is not None:return self.status(a)
  self.window(a);owner=digest(a);o=self.observe(a,owner)
  need(not o['frozen'] and o['fenceOwner'] is None,'SOURCE_PROTECTION_NOT_EMPTY')
  r={'schema':'r16.exact-empty-artifact-quarantine-journal.v1','approvalHash':owner,'targetHash':digest(a['target']),'phase':'BOUND','releaseCycle':'FORWARD','quarantineAttemptConsumed':False,'inverseAttemptConsumed':False}
  self.save(r)
  try:
   self.window(a);self.intent(r,'FENCE_INTENT');self.backend.fence(a['target'],owner);self.fault('effect:fence')
   o=self.observe(a,owner);need(not o['frozen'] and o['fenceOwner']==owner,'FENCE_UNPROVEN');self.intent(r,'FENCED')
   self.window(a);self.intent(r,'FREEZE_INTENT');self.backend.freeze(a['target'],owner);self.fault('effect:freeze');self.frozen(a,r);self.intent(r,'FROZEN')
   before=validate_inventory(self.backend.capture_before(a['target']),before=True)
   self.frozen(a,r);r['before']=before;r['beforeManifestHash']=digest(before);self.intent(r,'BASELINED')
   self.window(a);self.frozen(a,r);self.intent(r,'MOVE_INTENT','quarantineAttemptConsumed')
   moved=self.backend.quarantine(a['target'],owner,before);self.fault('effect:quarantine')
   need(type(moved) is dict and moved.get('location')=='QUARANTINE' and artifact_matches(moved.get('artifact')),'RELOCATION_RECEIPT_UNPROVEN')
   r['quarantinedArtifact']=deepcopy(moved['artifact']);self.frozen(a,r);self.intent(r,'MOVED')
   try:
    after=self.backend.verify_after(a['target'],before);self.proof(r,after,'QUARANTINE',validated=True)
   except Exception as e:
    r['validationFailureCode']=code(e);self.save(r)
    return self.restore_and_release(a,r)
   self.intent(r,'VALIDATION_PASSED');return self.release(a,r,False)
  except Exception as e:return self.pending(r,code(e))
 def recover(self,a,intent):
  validate_approval(a,self.now());need(a['environment']==self.backend.environment,'NATIVE_ENVIRONMENT_REQUIRED')
  r=self.journal.read();need(type(r) is dict and r.get('approvalHash')==digest(a),'JOURNAL_APPROVAL_DRIFT')
  was_terminal=r.get('phase')=='TERMINAL'
  if was_terminal:need(r.get('receipt',{}).get('status')==TERMINAL[0] and not r.get('inverseAttemptConsumed'),'TERMINAL_RECOVERY_NOT_SUPPORTED')
  fields={'schema','intentId','approvalHash','targetHash','scope','approvedAt','deadline'}
  need(type(intent) is dict and set(intent)==fields and intent['schema']==RECOVERY_SCHEMA and isinstance(intent['intentId'],str) and re.fullmatch('[A-Za-z0-9_-]{8,80}',intent['intentId']) and intent['approvalHash']==r['approvalHash'] and intent['targetHash']==r['targetHash'] and intent['scope']=='RESTORE_ORIGINAL_EMPTY_ARTIFACT' and type(intent['approvedAt']) is int and type(intent['deadline']) is int and intent['approvedAt']<=self.now()<intent['deadline'] and 0<intent['deadline']-intent['approvedAt']<=120000,'NEW_NATIVE_RECOVERY_INTENT_REQUIRED')
  if r.get('recoveryIntentHash')==digest(intent):return self.status(a)
  r['recoveryIntentHash']=digest(intent)
  if was_terminal:
   r['forwardReceipt']=deepcopy(r['receipt']);r['postSuccessInverse']=True;r['phase']='INVERSE_RECOVERY_BOUND';r['releaseCycle']='INVERSE'
  self.save(r)
  recovery={**a,'deadline':intent['deadline']}
  try:
   o=self.observe(a,r['approvalHash'],recovery=True)
   # A completed unfence followed by a failed journal/receipt write does not
   # authorize another effect. Fresh exact OS readback can close that receipt.
   if r.get('unfenceIntentCycle')==r.get('releaseCycle') and r.get('releaseResultCycle')==r.get('releaseCycle') and r.get('unfenceAttemptConsumed') and r.get('releaseResultStatus') in TERMINAL and not o['frozen'] and not o['freezeRequested'] and o['fenceOwner'] is None:
    return self.terminal(r,r['releaseResultStatus'])
   if not r.get('quarantineAttemptConsumed'):
    where=self.backend.inspect_artifact(a['target'],r['approvalHash'])
    need(where.get('location')=='SOURCE' and where.get('artifact')==ARTIFACT,'ORIGINAL_ARTIFACT_UNPROVEN')
    r['releaseResultStatus']=TERMINAL[1];r['releaseResultCycle']=r['releaseCycle']
    if o['frozen'] or o['freezeRequested']:
     self.window(recovery);r['thawIntentCycle']=r['releaseCycle'];self.intent(r,'THAW_INTENT','thawAttemptConsumed')
     self.backend.unfreeze(a['target'],r['approvalHash']);self.fault('effect:thaw')
     o=self.observe(a,r['approvalHash'])
    if o['fenceOwner']==r['approvalHash']:
     self.window(recovery);r['unfenceIntentCycle']=r['releaseCycle'];self.intent(r,'UNFENCE_INTENT','unfenceAttemptConsumed')
     self.backend.unfence(a['target'],r['approvalHash']);self.fault('effect:unfence')
    o=self.observe(a,r['approvalHash']);need(not o['frozen'] and o['fenceOwner'] is None,'ORIGINAL_RUNTIME_RESTORE_UNPROVEN')
    return self.terminal(r,TERMINAL[1])
   need('before' in r,'BASELINE_MISSING_RECOVERY_REQUIRED')
   if o['frozen']!=o['freezeRequested']:
    # The new native recovery scope specifically admits canceling this own
    # request. No freeze or artifact relocation can occur in a transition.
    self.window(recovery);self.intent(r,'RECOVERY_CANCEL_FREEZE_INTENT')
    self.backend.unfreeze(a['target'],r['approvalHash']);self.fault('effect:cancel-freeze')
    o=self.observe(a,r['approvalHash'])
   if o['fenceOwner'] is None:
    need(r.get('postSuccessInverse') is True,'OWNED_FENCE_REQUIRED')
    self.window(recovery);self.intent(r,'RECOVERY_FENCE_INTENT');self.backend.fence(a['target'],r['approvalHash']);self.fault('effect:recovery-fence')
    o=self.observe(a,r['approvalHash']);need(o['fenceOwner']==r['approvalHash'],'FENCE_UNPROVEN')
   if not o['frozen']:
    # A prior thaw may have succeeded. Re-freezing is a new explicit recovery
    # effect, never an automatic run/re-entry continuation.
    need(o['fenceOwner']==r['approvalHash'],'OWNED_FENCE_REQUIRED')
    self.window(recovery);self.intent(r,'RECOVERY_FREEZE_INTENT')
    self.backend.freeze(a['target'],r['approvalHash']);self.fault('effect:recovery-freeze')
   self.frozen(a,r)
   where=self.backend.inspect_artifact(a['target'],r['approvalHash'])
   if where.get('location')=='QUARANTINE' and not r.get('inverseAttemptConsumed'):
    fresh=validate_inventory(self.backend.capture_inverse_before(a['target'],r['approvalHash']),before=True,inverse=True)
    # This fresh inventory replaces no old business state. Persist both the
    # original forward baseline and the newly admitted inverse baseline.
    r['inverseBefore']=fresh;r['inverseBeforeManifestHash']=digest(fresh);self.intent(r,'INVERSE_BASELINED')
    self.proof(r,{**fresh,'artifactLocation':'QUARANTINE'},'QUARANTINE',validated=True)
   return self.restore_and_release(recovery,r)
  except Exception as e:return self.pending(r,code(e))

if __name__=='__main__':
 print(json.dumps({'status':'LIBRARY_ONLY_NATIVE_ADMISSION_REQUIRED','productionExecutionPerformed':False}))
 raise SystemExit(78)
