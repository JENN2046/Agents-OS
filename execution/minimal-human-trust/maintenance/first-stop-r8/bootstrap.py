"""Hash-pinned native bootstrap. No imports from candidate before full validation.

This file itself is hashed by the generated terminal launcher's stdlib-only
loader before root execution. No signing key or credential path is accepted.
"""
import hashlib,importlib,json,os,re,resource,socket,stat,sys,time,types
from pathlib import Path
CANDIDATE=Path('/home/ubuntu/r16-first-stop-r8-candidate')
ROOT=Path('/usr/lib/r16-maintenance/first-stop-r8')
POLICY='98552704b8bb8be9881318e8e8b12406448ea25f60951715a437198004ac4234'
def need(ok,code):
 if not ok: raise ValueError(code)
def secure_read(path,root_only=False):
 path=Path(path);p=Path('/')
 for bit in path.parts[1:-1]:
  p/=bit;s=p.lstat();need(stat.S_ISDIR(s.st_mode) and s.st_uid in ((0,) if root_only else (0,1000)) and not s.st_mode&0o022,'BOOTSTRAP_PARENT_REFUSED')
 fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
 try:
  a=os.fstat(fd);need(stat.S_ISREG(a.st_mode) and a.st_uid in ((0,) if root_only else (0,1000)) and a.st_nlink==1 and not a.st_mode&0o022 and a.st_size<=1048576,'BOOTSTRAP_FILE_REFUSED')
  raw=b''
  while len(raw)<=1048576:
   b=os.read(fd,65536)
   if not b:break
   raw+=b
  z=os.fstat(fd);fields=lambda s:(s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns)
  need(len(raw)==a.st_size and fields(a)==fields(z),'BOOTSTRAP_FILE_CHANGED');return raw
 finally:os.close(fd)
def parse(raw):
 def pairs(rows):
  out={}
  for k,v in rows:need(k not in out,'BOOTSTRAP_JSON_DUPLICATE');out[k]=v
  return out
 return json.loads(raw,object_pairs_hook=pairs)
def sha(raw):return hashlib.sha256(raw).hexdigest()
def _bounded_code(error):
 value=getattr(error,'code',str(error) if isinstance(error,ValueError) else '')
 return value if isinstance(value,str) and re.fullmatch('[A-Z0-9_]{1,100}',value) else 'PROTECTED_READONLY_PREFLIGHT_FAILED'

def _preflight_state(backend):
 # Never acquire RootJournal's writing lock. A historical empty exclusive.lock
 # is allowed, but all intent, transaction, ownership or unknown pending files
 # make this a recovery/status case, not a new untouched-stop baseline.
 state=backend.paths.state
 if not backend._private_state():return
 names=os.listdir(state)
 need(set(names)<= {'exclusive.lock'},'READONLY_ACTIVE_OR_UNREVIEWED_STOP_STATE')
 if 'exclusive.lock' in names:backend.files.read(state/'exclusive.lock',mode=0o600,maximum=65536)

def _readonly_projection(capsule,target,backend_module,ledger_module,checkpoint):
 a=checkpoint.get('attestation',{})
 need(a.get('capturePhase')=='BASELINE_NOT_DRAIN_PROOF' and a.get('drainStatus')=='UNPROVEN','READONLY_BASELINE_PHASE_REFUSED')
 for field in ('signatureVerification','sealedRegistrationVerified'):need(a.get(field) is True,'READONLY_ATTESTATION_REFUSED')
 for field,value in (('sourcePublicConfigDigest',ledger_module.PUBLIC_DIGEST),('grantHash',ledger_module.GRANT_DIGEST),('sourceDeliveryHash',ledger_module.DELIVERY_DIGEST),('sourceDeliveryRevision',16),('originalUnknownCount',2),('otherDurableInflight',0),('foreignOpenWriters',0)):
  need(type(a.get(field)) is type(value) and a.get(field)==value,'READONLY_ATTESTATION_REFUSED')
 for field in ('registrationHash','checkpointManifestDigest','semanticBindingsDigest'):need(isinstance(a.get(field),str) and re.fullmatch('[0-9a-f]{64}',a[field]),'READONLY_ATTESTATION_REFUSED')
 for field,minimum,maximum in (('registeredProjectCount',2,100000),('fileCount',3,100000),('totalBytes',1,67108864)):
  need(type(a.get(field)) is int and minimum<=a[field]<=maximum,'READONLY_ATTESTATION_REFUSED')
 return {'schema':'r16.first-stop-readonly-preflight.v1','status':'READ_ONLY_PREFLIGHT_PASS','capsuleHash':capsule,'targetHash':backend_module.digest(target),'observedAt':time.time_ns()//1000000,
  **{key:a[key] for key in ('sourcePublicConfigDigest','grantHash','sourceDeliveryHash','sourceDeliveryRevision','registrationHash','checkpointManifestDigest','semanticBindingsDigest','registeredProjectCount','fileCount','totalBytes','originalUnknownCount','otherDurableInflight','foreignOpenWriters','signatureVerification','sealedRegistrationVerified')},
  'originalRuntimeUntouched':True,'baselineStable':True,'drainStatus':'UNPROVEN','nativeIntentCreated':False,'rootSourceInstalled':False,'journalWritten':False,'freezeIssued':False,'signalsIssued':0,'businessCallsIssued':0,'mayStop':False,'businessAcceptance':False}

def readonly_preflight(sealed,capsule):
 loaded=[]
 try:
  modules=[]
  # Dependencies are fixed OS libraries. No candidate import, sys.path entry,
  # common_safe, native_entry, journal, source copy or lock is executed.
  # The driver module only supplies its pure in-memory checkpoint validator;
  # no Driver is constructed and no authority-bearing approval is generated.
  for filename in ('linux_backend.py','ledger_checkpoint.py','stop_driver.py'):
   name='_r8_verified_preflight_'+filename.removesuffix('.py')+'_'+capsule
   need(name not in sys.modules,'READONLY_MODULE_NAME_COLLISION')
   module=types.ModuleType(name);module.__file__='<verified-memory/'+filename+'>';sys.modules[name]=module;loaded.append(name)
   exec(compile(sealed[filename],module.__file__,'exec'),module.__dict__);modules.append(module)
  backend_module,ledger_module,validator_module=modules;target=parse(sealed['TARGET.json'])
  class ReadOnlyAdmission:
   approval_hash=None
   target_hash=backend_module.digest(target)
   def require(self,operation,observed=None):
    need(os.getuid()==0 and os.geteuid()==0 and socket.gethostname()=='VM-0-12-ubuntu','READONLY_FIXED_ROOT_REQUIRED')
    need(operation=='inspect' and observed is not None and backend_module.digest(observed)==self.target_hash,'READONLY_EFFECT_REFUSED')
  backend=backend_module.LinuxBackend(ReadOnlyAdmission(),ledger_module.LedgerCheckpoint())
  _preflight_state(backend);before=backend.inspect(target)
  need(before.get('processExited') is False and before.get('frozen') is False and before.get('freezeRequested',False) is False and before.get('fenceOwner') is None and before.get('freezeOwner') is None,'READONLY_ORIGINAL_RUNTIME_NOT_UNTOUCHED')
  checkpoint=backend.checkpointer.capture_baseline(target)
  # These are semantic expectations freshly authenticated by the reader, not
  # a stop approval (no schema, authority, window, risk flags or native intent).
  expectations={'target':target,**{key:checkpoint[key] for key in ('expectedOriginalUnknown','expectedLeaseBindings','expectedSemanticBindingsDigest')}}
  validated=validator_module.checkpoint_manifest(checkpoint,expectations)
  need(validated.get('validatedOriginalBindings') is True and validated.get('noTemporaryFiles') is True and type(validated.get('otherDurableInflight')) is int and validated['otherDurableInflight']==0 and validated.get('drainStatus')=='UNPROVEN' and validated.get('semanticBindingsDigest')==checkpoint['expectedSemanticBindingsDigest'],'READONLY_CHECKPOINT_VALIDATOR_REFUSED')
  after=backend.inspect(target);_preflight_state(backend)
  need(before==after,'READONLY_RUNTIME_OBSERVATION_CHANGED')
  return {**_readonly_projection(capsule,target,backend_module,ledger_module,checkpoint),'checkpointValidatorPassed':True,'checkpointValidatorManifestDigest':validator_module.digest(validated)}
 except Exception as error:
  return {'schema':'r16.first-stop-readonly-preflight.v1','status':'READ_ONLY_PREFLIGHT_REFUSED','code':_bounded_code(error),'capsuleHash':capsule,'drainStatus':'UNPROVEN','nativeIntentCreated':False,'rootSourceInstalled':False,'journalWritten':False,'freezeIssued':False,'signalsIssued':0,'businessCallsIssued':0,'mayStop':False,'businessAcceptance':False}
 finally:
  for name in loaded:sys.modules.pop(name,None)

def run(mode,capsule_hash):
 resource.setrlimit(resource.RLIMIT_CORE,(0,0))
 need(os.getuid()==0 and os.geteuid()==0 and socket.gethostname()=='VM-0-12-ubuntu','BOOTSTRAP_FIXED_ROOT_REQUIRED')
 need(mode in ('stop','status','recover-original','preflight') and re.fullmatch('[0-9a-f]{64}',capsule_hash),'BOOTSTRAP_ARGUMENTS_REFUSED')
 base=CANDIDATE if mode in ('stop','preflight') else ROOT/capsule_hash
 raw=secure_read(base/'CAPSULE.json',root_only=mode not in ('stop','preflight'));need(sha(raw)==capsule_hash,'CAPSULE_HASH_DRIFT');manifest=parse(raw)
 need(set(manifest)=={'schema','files','policyExceptionProposalHash','acceptedPolicyException','productionStopAlreadyAuthorized'} and manifest['schema']=='r16.first-stop-capsule.v1' and manifest['policyExceptionProposalHash']==POLICY and manifest['acceptedPolicyException'] is True and manifest['productionStopAlreadyAuthorized'] is False,'CAPSULE_SCOPE_REFUSED')
 required={'bootstrap.py','common_safe.py','native_entry.py','stop_driver.py','linux_backend.py','ledger_checkpoint.py','handoff.py','TARGET.json'}
 need(set(manifest['files'])==required,'CAPSULE_FILE_SET_REFUSED')
 sealed={}
 for name,pin in manifest['files'].items():
  need(re.fullmatch('[A-Za-z_][A-Za-z0-9_]*[.](py|json)',name) and re.fullmatch('[0-9a-f]{64}',pin),'CAPSULE_PIN_REFUSED')
  value=secure_read(base/name,root_only=mode not in ('stop','preflight'));need(sha(value)==pin,'CAPSULE_FILE_DRIFT');sealed[name]=value
 if mode=='preflight':return readonly_preflight(sealed,capsule_hash)
 # No unverified candidate import. Execute common primitives only after every
 # file was sealed; copy sealed bytes rather than rereading mutable candidates.
 ns={'__name__':'r8_sealed_file_primitives'};exec(compile(sealed['common_safe.py'],'<r8-verified-file-primitives>','exec'),ns)
 target=ROOT/capsule_hash
 if mode=='stop':
  for name,value in sealed.items():ns['immutable'](target/name,value,0o644)
  ns['immutable'](target/'CAPSULE.json',raw,0o644)
 sys.path.insert(0,str(target))
 entry=importlib.import_module('native_entry')
 try:return entry.entry(mode,capsule_hash)
 except Exception as e:
  code=getattr(e,'code','NATIVE_ENTRY_REFUSED')
  return {'status':'REFUSED_OR_RECOVERY_REQUIRED','code':code if isinstance(code,str) and re.fullmatch('[A-Z0-9_]{1,100}',code) else 'NATIVE_ENTRY_REFUSED','businessAcceptance':False}
if __name__=='__main__':
 try:
  need(len(sys.argv)==3,'BOOTSTRAP_ARGUMENTS_REFUSED');result=run(sys.argv[1],sys.argv[2]);print(json.dumps(result,separators=(',',':')))
  status=result.get('status','')
  ok=(sys.argv[1]=='preflight' and status=='READ_ONLY_PREFLIGHT_PASS') or (sys.argv[1]!='preflight' and status in ('CONTROLLED_CRASH_STOPPED_NOT_DRAINED','ABORTED_BEFORE_SIGNAL_ORIGINAL_RUNTIME_RESTORED','ORIGINAL_R15_RESTORED_NOT_DRAINED'))
  raise SystemExit(0 if ok else 78)
 except (ValueError,OSError) as e:
  code=str(e);print(json.dumps({'status':'BOOTSTRAP_REFUSED','code':code if re.fullmatch('[A-Z0-9_]{1,100}',code) else 'PROTECTED_BOOTSTRAP_INVALID','businessAcceptance':False}));raise SystemExit(78)
