"""New R10 source proof. Old R9 ABORT and all old deadlines are historical only."""
import contextlib,fcntl,hashlib,json,os,re,shlex,socket,stat,subprocess,sys,types
from pathlib import Path
PROVENANCE={'schema': 'r16.recovered-source-provenance.v1', 'originalPlanHash': '45b7880b1f95cedba470e1c7d97f1656f4c77784d1c4b260861b7609d11d1c24', 'originalCapsuleHash': 'e7c8dbe016c2a36f0a1929ab52d5d0ad19ca7217c505f6c138cc64f32c595dad', 'originalRollbackDeadline': 1792175013109, 'compensationCompletionHash': '2ed7c5d22c2a854c7f47310d49fe3c5a093300ba34fdf6826a79f3e786fe0f6d', 'compensationRelationHash': '462298d6b03e14d4c2bc9da6e7d8b6c4861886b6eb78a8741d96ca48f7ea5e3b', 'cloudProofHash': '6e6ed5742c4caea3090c3d298b9e5f419723ce5120810044cc5f3e698fd4d55c', 'originalStopApprovalHash': 'd26ce58948f4a09fb7aa2442458ee2028ea68a85fe687cfde206816899bf558f', 'originalCheckpointDigest': '36bccee6812eb1c04d198868a572d049a8b4433d4d66332df12b30f1e7212a2c', 'historicalSourceStopForceUsed': True, 'drainStatus': 'UNPROVEN', 'sourceAppBaseline': 'STOPPED', 'oldPlanRenewed': False, 'businessAcceptance': False, 'r9ClosedAbort': {'schema': 'r16.r9.closed-abort-provenance.v1', 'planHash': '341625cdc01bc2ffb0db0ad45500e581f798fdb681ccbd7b9decab6742b29ae7', 'capsuleHash': '831e82dc470f354e7812b775a6d8e7ea7a6d340bea337ef177aa86f9f00d05af', 'canonicalReceiptHash': '6dc49b29225788411be367ad4676a94922934e43475b674ab88b7685bc8a5be0', 'transactionHash': '19a8286a967b575dac6e66958f7823d6c32aebc4d43ba7694a75223f02c443b4', 'localOsJournalHash': '976062efdc7da9f3d72f524e4a3c965c7db5860003f66e7e8d4d4d2cde90db50', 'cloudOsJournalHash': '45e59d72807c8b9dcff1ac7dec43ffdfabeed1f4f0e437da67bb0dc561f9b929', 'rollbackDeadline': 1792181748074, 'completedAt': 1792180641752, 'status': 'ABORTED_BEFORE_CONFIGURATION_CHANGE', 'oldPlanRenewed': False, 'authority': False}}
PINS={'prior-compensation.py': 'abf23a3859136d789a2e3239a8c6e5205c3a7c34b33e2faad97c9aa4222e4253', 'prior-native-guard.py': '21ebbb865bbd84d22aa2aa9160353c9e4ad26672edc1fa0b51a37709e8b6a51b', 'prior-evidence.json': '057d698d69297a014357dfb0d630af59c0960ac1ad82512e06dbb5b27a605518'}
LOCAL='jenn-System-Product-Name';CLOUD='VM-0-12-ubuntu'
R9_ROOT=Path('/usr/lib/r16-maintenance/recovery-r9');R9_STATE=Path('/var/lib/r16-maintenance/recovery-r9')
R9_CAP='831e82dc470f354e7812b775a6d8e7ea7a6d340bea337ef177aa86f9f00d05af'
Q_SHA='0bd50a9f396e213b0d3f0599fbf6ae34a38d822f90d46b4dda3d14772416dc6c'
PUBLIC_SHA='be3ff2b5125f8212206d2848bb32889c3c6b50a8ca56aa3b1a4bc4359591bbdb'
CHECKPOINT='36bccee6812eb1c04d198868a572d049a8b4433d4d66332df12b30f1e7212a2c'
SOURCE_RELEASE='/opt/r16/releases/r16-daily-20261012-r15'
SSH=('/usr/bin/ssh','-F','/dev/null','-T','-o','BatchMode=yes','-o','IdentityAgent=none','-o','IdentitiesOnly=yes','-i','/home/jenn/.ssh/TXY_159_75_139_246_ed25519','-o','StrictHostKeyChecking=yes','-o','UpdateHostKeys=no','-o','UserKnownHostsFile=/etc/r16-owner/ssh_known_hosts','-o','GlobalKnownHostsFile=/dev/null','-o','ConnectTimeout=8','-o','ClearAllForwardings=yes','ubuntu@159.75.139.246')
ENV={'PATH':'/usr/bin:/bin','LANG':'C','LC_ALL':'C','SYSTEMD_PAGER':'cat','SYSTEMD_COLORS':'0'}
class Refused(Exception):
 def __init__(self,code):self.code=code;super().__init__(code)
def need(v,c):
 if not v:raise Refused(c)
def canonical(v):return json.dumps(v,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()
def sha(raw):return hashlib.sha256(raw).hexdigest()
def digest(v):return sha(canonical(v))
def module(name,raw):
 need(name not in sys.modules,'R10_READER_MODULE_COLLISION');m=types.ModuleType(name);m.__file__='<sealed-r10/'+name+'>';sys.modules[name]=m
 try:exec(compile(raw,m.__file__,'exec'),m.__dict__)
 except BaseException:sys.modules.pop(name,None);raise
 return m
@contextlib.contextmanager
def component(name,raw):
 m=module(name,raw)
 try:yield m
 finally:sys.modules.pop(name,None)
def validate_inputs(manifest,sources):
 need(os.getuid()==os.geteuid()==0 and socket.gethostname() in (LOCAL,CLOUD),'R10_ROOT_FIXED_HOST_REQUIRED')
 need(manifest.get('planTemplate',{}).get('sourceRecoveryEvidence')==PROVENANCE,'R10_EXACT_PRIOR_PROVENANCE_REQUIRED')
 need(type(sources) is dict and type(manifest.get('files')) is dict,'R10_SEALED_SOURCES_REQUIRED')
 for name in ('asset-verifier.py','prior-verifier.py',*PINS):
  need(type(sources.get(name)) is bytes and sha(sources[name])==manifest['files'].get(name),'R10_NEW_SOURCE_PIN_DRIFT')
 for name,pin in PINS.items():need(sha(sources[name])==pin,'R10_FROZEN_PRIOR_COMPONENT_DRIFT')
def old_source(asset):
 raw,meta=asset.read(R9_ROOT/'SOURCE_FREEZE.json',0o644,16*1024*1024);need(sha(raw)==R9_CAP,'R10_OLD_SOURCE_FREEZE_DRIFT');freeze=asset.parse(raw)
 expected={'cache-cleanup.py','cloud.mjs','context.mjs','io.mjs','legacy/control-clock.mjs','legacy/lease-core.mjs','local.mjs','maintenance-release-base.mjs','os_entry.py','prior-compensation.py','prior-evidence.json','prior-native-guard.py','prior-verifier.py','publication.mjs','quiescence.py','release-publication-base.mjs','run.mjs','state.mjs','transaction-driver.mjs'}
 need(set(freeze.get('files',{}))==expected and freeze['files']['quiescence.py']==Q_SHA,'R10_OLD_SOURCE_SCOPE_DRIFT');rows={}
 for name,pin in freeze['files'].items():
  asset.safe(name);b,_=asset.read(R9_ROOT/name,0o644,16*1024*1024);need(sha(b)==pin,'R10_OLD_SOURCE_CODE_DRIFT');rows[name]=b
 return raw,meta,freeze,rows
def pinned_json(asset,name,pin,maximum=8*1024*1024):
 raw,meta=asset.read(R9_STATE/name,0o600,maximum);need(sha(raw)==pin,'R10_OLD_'+name.replace('.','_').replace('-','_').upper()+'_DRIFT');return asset.parse(raw),raw,meta
def old_records(asset,host):
 p=PROVENANCE['r9ClosedAbort'];plan,plan_raw,plan_meta=pinned_json(asset,'plan.json',p['planHash'])
 need(plan.get('capsuleHash')==R9_CAP and plan.get('sourceFreezeHash')==R9_CAP and plan.get('rollbackDeadline')==p['rollbackDeadline'],'R10_OLD_PLAN_BINDING_DRIFT')
 cap_raw,cap_meta=asset.read(R9_STATE/'capsule.json',0o600,16*1024*1024);need(sha(cap_raw)==R9_CAP,'R10_OLD_INSTALLED_CAPSULE_DRIFT')
 for name in os.listdir(R9_STATE):
  clean=name.lstrip('.');need(not re.match(r'^(publication-|release-|delivery-|rollback-|transaction-(?:signed|cloud-commit|local-commit)(?:[.-]|$))',clean),'R10_OLD_SIGN_OR_COMMIT_ARTIFACT_PRESENT')
 names={'os-journal.json':p['localOsJournalHash'],'transaction-transaction.json':p['transactionHash'],'transaction-receipt.json':p['canonicalReceiptHash']} if host==LOCAL else {'cloud-os-journal.json':p['cloudOsJournalHash']}
 docs={};hashes={'plan':sha(plan_raw),'capsule':sha(cap_raw)}
 for name,pin in names.items():docs[name],raw,_=pinned_json(asset,name,pin,32*1024*1024);hashes[name]=sha(raw)
 journal=docs['os-journal.json' if host==LOCAL else 'cloud-os-journal.json'];need(journal.get('schema')=='r16.os-maintenance-journal.v3' and journal.get('planHash')==p['planHash'] and journal.get('pending') is None,'R10_OLD_OS_JOURNAL_NOT_CLOSED')
 if host==LOCAL:
  tx=docs['transaction-transaction.json'];receipt=docs['transaction-receipt.json'];need(tx.get('mode')=='ABORT' and not any(k in tx.get('steps',{}) for k in ('signed','cloud-commit','local-commit','rollback-signed')),'R10_OLD_TRANSACTION_NOT_PRECOMMIT_ABORT')
  need(receipt.get('schema')=='r16.maintenance-completion.v3' and receipt.get('status')==p['status'] and receipt.get('completedAt')==p['completedAt']<p['rollbackDeadline'] and receipt.get('businessAcceptance') is False,'R10_OLD_CANONICAL_ABORT_NOT_PROVEN')
 return {'hashes':hashes,'journal':journal}
def manager_inactive():
 unit='r16-native-recovery-maintenance-r9.service';keys=('Id','ActiveState','MainPID','ControlPID','Job')
 r=subprocess.run(('/usr/bin/systemctl','show',unit,'--property='+','.join(keys)),stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,env=ENV,timeout=10,check=False);need(r.returncode==0 and len(r.stdout)<8192,'R10_OLD_MANAGER_READBACK_REFUSED');p=dict(x.split('=',1) for x in r.stdout.decode().splitlines() if '=' in x)
 need(set(p)==set(keys) and p['Id']==unit and p['ActiveState'] in ('inactive','failed') and p['MainPID']==p['ControlPID']=='0' and p['Job'] in ('','0'),'R10_OLD_MAINTENANCE_STILL_ACTIVE')
 root=Path('/sys/fs/cgroup/system.slice')/unit
 if root.exists():
  for d,children,_ in os.walk(root,followlinks=False,onerror=lambda e:(_ for _ in ()).throw(e)):
   need(not Path(d).is_symlink() and all(not (Path(d)/x).is_symlink() for x in children),'R10_OLD_CGROUP_SYMLINK');need((Path(d)/'cgroup.procs').read_text().strip()=='','R10_OLD_MAINTENANCE_WRITER_PRESENT')
def roles(old_sources,host):
 with component('r10_old_source_q',old_sources['quiescence.py']) as q:
  need(sha(old_sources['quiescence.py'])==Q_SHA,'R10_OLD_QUIESCENCE_DRIFT');backend=q.RealBackend();result={}
  for unit in (('r16-owner.service','r16-native.service') if host==LOCAL else ('r16-app.service','r16-bridge.service')):
   s=backend.inspect(unit,PROVENANCE['r9ClosedAbort']['planHash']);phase='SOURCE' if unit in ('r16-app.service','r16-native.service') else 'STATIC'
   need(s.code_phase==phase and s.fence_hash is None and not s.pending_job and not s.daemon_reload_needed and s.graceful_only(),'R10_SOURCE_ROLE_POLICY_OR_CODE_DRIFT')
   if unit=='r16-app.service':need(s.stopped(),'R10_SOURCE_APP_NOT_STOPPED')
   else:need(s.active=='active' and s.sub=='running' and s.main_pid>0 and s.main_start>0 and s.main_pid in s.members,'R10_SOURCE_ROLE_NOT_RUNNING')
   result[unit]={'active':s.active,'sub':s.sub,'mainPid':s.main_pid,'mainStartTicks':str(s.main_start),'controlPid':s.control_pid,'members':sorted(s.members),'restarts':s.restarts,'codePhase':phase,'fenced':False,'pendingJob':False}
  return result
NODE_READONLY=r'''import fs from 'node:fs';import {pathToFileURL}from'node:url';
const R='/usr/lib/r16-maintenance/recovery-r9',S='/var/lib/r16-maintenance/recovery-r9';
const {protectedBytes,digest,same,need}=await import(pathToFileURL(R+'/io.mjs'));
const json=p=>JSON.parse(protectedBytes(p,{max:64*1024*1024}));
const {verified}=await import(pathToFileURL(R+'/legacy/lease-core.mjs'));
const pub=json(S+'/package/metadata/R15_PUBLIC_CONFIG.json');need(digest(pub)==='be3ff2b5125f8212206d2848bb32889c3c6b50a8ca56aa3b1a4bc4359591bbdb','SOURCE_PUBLIC_DRIFT');
let result;
if(process.argv[1]==='local'){
 const {captureLocal,assertPreserved,PATHS,verifySourceDelivery}=await import(pathToFileURL(R+'/state.mjs'));
 const raw=protectedBytes(S+'/context.json',{max:64*1024*1024}),context=JSON.parse(raw);need(context.schema==='r16.native-recovery-context.v3'&&context.planHash==='341625cdc01bc2ffb0db0ad45500e581f798fdb681ccbd7b9decab6742b29ae7'&&same(context.inputs.sourcePublicConfig,pub),'OLD_CONTEXT_SCOPE_DRIFT');
 const currentPub=json(PATHS.public);need(same(currentPub,pub),'SOURCE_PUBLIC_SELECTED_TARGET');const current=captureLocal(pub);assertPreserved(context.before,current);verifySourceDelivery(pub,current.configuration);need(same(current.configuration.delivery,context.before.configuration.delivery),'SOURCE_DELIVERY_CHANGED');
 const snapshots={proposal:json(PATHS.proposal),reviewed:json(PATHS.reviewed),native:json(PATHS.native),cutover:json(PATHS.localCutover)};
 for(const [k,v]of Object.entries(snapshots))need(same(v,context.snapshots[k]),'SOURCE_SELECTOR_CHANGED');need(snapshots.native.codeManifest==='/opt/r16/releases/r16-daily-20261012-r15/native-manifest.json'&&snapshots.cutover.phase==='ACTIVE','SOURCE_NATIVE_SELECTOR_DRIFT');
 const again=captureLocal(pub);assertPreserved(current,again);need(same(again.configuration.delivery,current.configuration.delivery),'SOURCE_DELIVERY_CHANGED_DURING_READ');
 for(const [k,p]of Object.entries({proposal:PATHS.proposal,reviewed:PATHS.reviewed,native:PATHS.native,cutover:PATHS.localCutover}))need(same(json(p),snapshots[k]),'SOURCE_SELECTOR_CHANGED_DURING_READ');need(same(json(PATHS.public),pub),'SOURCE_PUBLIC_CHANGED_DURING_READ');
 need(protectedBytes(S+'/context.json',{max:64*1024*1024}).equals(raw),'OLD_CONTEXT_CHANGED_DURING_READ');
 result={publicConfigHash:digest(pub),snapshotHashes:Object.fromEntries(Object.entries(snapshots).map(([k,v])=>[k,digest(v)])),issuerDataHash:current.issuerDataHash,configurationInvariantHash:current.configurationInvariantHash,originalUnknownHash:digest(current.originalUnknown),projectBusinessHashes:current.projectBusinessHashes,sourceDeliveryHash:digest(current.configuration.delivery.envelope),contextSha256:(await import('node:crypto')).createHash('sha256').update(raw).digest('hex')};
}else{
 const paths={app:'/etc/r16-cloud/app-host.json',public:'/etc/r16-cloud/public-config.json',control:'/etc/r16-cloud/authority-control.json',cutover:'/etc/r16-cloud/cutover.json',startAttempt:'/var/lib/r16-cloud/start-attempt.json',accepted:'/var/lib/r16-cloud/authority/state.json'};
 function cloudData(w){need(w&&typeof w==='object'&&!Array.isArray(w)&&same(Object.keys(w).sort(),['data','maxNow','revision','schema'])&&w.schema===1&&Number.isSafeInteger(w.revision)&&w.revision>=0&&Number.isSafeInteger(w.maxNow)&&w.maxNow>=0&&w.data&&typeof w.data==='object'&&!Array.isArray(w.data)&&w.data.kind==='r16.cloud-publication.v1','SOURCE_CLOUD_WRAPPER_INVALID');return w.data;}
 const values=Object.fromEntries(Object.entries(paths).map(([k,p])=>[k,json(p)])),w=values.accepted,data=cloudData(w),accepted=data.accepted,b=verified(accepted,pub.issuerPublicKey,'r16.configuration-delivery.v1');
 need(b.revision===16&&digest(accepted)==='5ee11707da0d3a524550db92f8c0a5a80b7a8dac8c97f5a907b47fc956c6ec44'&&same(b.publicConfig,pub)&&same(values.public,pub)&&same(values.control,b.control)&&same(b.control,{grantId:'r16-projects-daily',grantVersion:1,status:'ACTIVE',connectRequested:true}),'SOURCE_CLOUD_DELIVERY_DRIFT');
 need(values.app.codeManifest==='/opt/r16/releases/r16-daily-20261012-r15/app-manifest.json'&&values.app.publicConfiguration===paths.public&&same(values.app,json(S+'/cloud-source-app.json')),'SOURCE_APP_SELECTOR_DRIFT');
 need(values.cutover.schema==='r16.cloud-cutover.v1'&&values.cutover.phase==='ACTIVE'&&values.cutover.grantId==='r16-projects-daily'&&values.cutover.releaseId==='r16-daily-20261012-r15'&&same(values.startAttempt,{schema:'r16.cloud-start-attempt.v1',grantId:'r16-projects-daily',revision:16}),'SOURCE_CLOUD_CUTOVER_DRIFT');
 for(const [k,p]of Object.entries(paths)){const again=json(p);if(k==='accepted'){const after=cloudData(again);need(again.revision>=w.revision&&again.maxNow>=w.maxNow,'SOURCE_CLOUD_WRAPPER_CLOCK_ROLLBACK');need(same(after,data),'SOURCE_CLOUD_CHANGED_DURING_READ');}else need(same(again,values[k]),'SOURCE_CLOUD_CHANGED_DURING_READ');}result={publicConfigHash:digest(pub),deliveryHash:digest(accepted),sourceFileHashes:Object.fromEntries(Object.entries(values).map(([k,v])=>[k,digest(k==='accepted'?data:v)])),sourceAppConfigHash:digest(values.app)};
}
console.log(JSON.stringify(result));
'''
def node_facts(host):
 binary='/usr/bin/node' if host==LOCAL else '/opt/r16/runtime/node-v24.15.0/bin/node';phase='local' if host==LOCAL else 'cloud';r=subprocess.run((binary,'--input-type=module','-e',NODE_READONLY,phase),stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,env=ENV,timeout=90,check=False)
 need(r.returncode==0 and 0<len(r.stdout)<=65536,'R10_SOURCE_BUSINESS_OR_SELECTORS_NOT_PRESERVED');value=json.loads(r.stdout);need(type(value) is dict and value.get('publicConfigHash')==PUBLIC_SHA,'R10_SOURCE_PUBLIC_CONFIG_DRIFT');return value
def cloud_checkpoint(sources):
 with component('r10_prior_checkpoint_only',sources['prior-compensation.py']) as m:
  prior={'compensation.py':sources['prior-compensation.py'],'native_guard.py':sources['prior-native-guard.py'],'LOCAL_EVIDENCE.json':sources['prior-evidence.json']};backend=m.FixedBackend(CLOUD,m.parse(prior['LOCAL_EVIDENCE.json']),prior);need(backend.checkpoint()==CHECKPOINT,'R10_ORIGINAL_CHECKPOINT_CHANGED');return CHECKPOINT
@contextlib.contextmanager
def old_read_locks(asset,host):
 fds=[]
 try:
  for name in ('entry.lock', '.transaction-lock') if host==LOCAL else ('entry.lock',):
   path=R9_STATE/name;_,meta=asset.read(path,0o600,4096);fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW);fds.append(fd);need(asset.stamp(os.fstat(fd))==meta,'R10_OLD_LOCK_CHANGED');fcntl.flock(fd,fcntl.LOCK_SH|fcntl.LOCK_NB)
  yield
 finally:
  for fd in reversed(fds):os.close(fd)
def host_facts(manifest,sources,host):
 validate_inputs(manifest,sources);need(socket.gethostname()==host,'R10_READER_HOST_MISMATCH')
 with component('r10_assets_readonly',sources['asset-verifier.py']) as asset:
  old_raw,old_meta,freeze,old_sources=old_source(asset)
  with old_read_locks(asset,host):
   manager_inactive();before=old_records(asset,host);assets=asset.verify_assets(manifest,sources);actors=roles(old_sources,host);business=node_facts(host)
   checkpoint=cloud_checkpoint(sources) if host==CLOUD else None
   need(roles(old_sources,host)==actors and node_facts(host)==business,'R10_SOURCE_CHANGED_DURING_CAPTURE');after=old_records(asset,host);need(before==after,'R10_OLD_RECORDS_CHANGED_DURING_CAPTURE');manager_inactive()
   need(old_source(asset)==(old_raw,old_meta,freeze,old_sources),'R10_OLD_SOURCE_CHANGED_DURING_CAPTURE')
  return {'schema':'r16.r10.host-source-facts.v1','host':host,'oldR9Hashes':before['hashes'],'assets':assets,'actors':actors,'business':business,'originalCheckpointDigest':checkpoint,'oldCanonicalReceiptLocallyVerified':host==LOCAL,'oldR9AuthorityReused':False,'businessAcceptance':False}
def cloud_facts(manifest,sources):return host_facts(manifest,sources,CLOUD)
REMOTE_READER=r'''import hashlib,json,os,stat,sys,types
from pathlib import Path
B=Path('/home/ubuntu/r16-maintenance-recovered-r10-candidate')
def need(v):
 if not v:raise ValueError('R10_SEALED_CLOUD_READER_REFUSED')
def read(p,maxsize=16*1024*1024):
 cursor=Path('/')
 for bit in p.parts[1:-1]:
  cursor/=bit;s=cursor.lstat();need(stat.S_ISDIR(s.st_mode) and s.st_uid in (0,1000) and not s.st_mode&0o022)
 fd=os.open(p,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
 try:
  a=os.fstat(fd);need(stat.S_ISREG(a.st_mode) and a.st_uid in (0,1000) and a.st_nlink==1 and stat.S_IMODE(a.st_mode)==0o644 and a.st_size<=maxsize);raw=b''
  while len(raw)<=maxsize:
   block=os.read(fd,min(1048576,maxsize+1-len(raw)))
   if not block:break
   raw+=block
  stamp=lambda s:(s.st_dev,s.st_ino,s.st_mode,s.st_uid,s.st_gid,s.st_nlink,s.st_size,s.st_mtime_ns,s.st_ctime_ns);need(len(raw)==a.st_size and stamp(a)==stamp(os.fstat(fd))==stamp(p.lstat()));return raw
 finally:os.close(fd)
need(os.getuid()==os.geteuid()==0);raw=read(B/'SOURCE_FREEZE.json');need(hashlib.sha256(raw).hexdigest()==EXPECTED_CAP);manifest=json.loads(raw);sources={}
need(type(manifest.get('files')) is dict and len(manifest['files'])==19)
for name,pin in manifest['files'].items():
 need(type(name) is str and not name.startswith('/') and '\\' not in name and all(x not in ('','.','..') for x in name.split('/')));b=read(B/name);need(hashlib.sha256(b).hexdigest()==pin);sources[name]=b
need(manifest==EXPECTED_MANIFEST and {'prior-verifier.py','asset-verifier.py','quiescence.py','prior-compensation.py','prior-native-guard.py','prior-evidence.json'}<=set(sources))
m=types.ModuleType('r10_remote_prior_reader');m.__file__='<sealed-r10-remote-prior>';sys.modules[m.__name__]=m;exec(compile(sources['prior-verifier.py'],m.__file__,'exec'),m.__dict__);facts=m.cloud_facts(manifest,sources)
print(json.dumps({'schema':'r16.r10.sealed-cloud-facts.v1','capsuleHash':EXPECTED_CAP,'facts':facts},sort_keys=True,separators=(',',':')))
'''
def fresh_cloud(manifest):
 # The R10 candidate SOURCE_FREEZE bytes are canonical builder output, no newline.
 cap=digest(manifest);code='EXPECTED_CAP='+repr(cap)+'\nEXPECTED_MANIFEST='+repr(manifest)+'\n'+REMOTE_READER
 # No payload pins/manifest on argv: 1.85MiB is beyond ARG_MAX. Pipe only public reader source.
 command=shlex.join(('/usr/bin/sudo','-n','--','/usr/bin/python3','-I','-B','-'))
 r=subprocess.run((*SSH,command),input=code.encode(),stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,env=ENV,timeout=240,check=False)
 need(r.returncode==0 and 0<len(r.stdout)<=65536,'R10_FRESH_CLOUD_READBACK_REFUSED');packet=json.loads(r.stdout);need(packet.get('schema')=='r16.r10.sealed-cloud-facts.v1' and packet.get('capsuleHash')==cap,'R10_FRESH_CLOUD_CAPSULE_DRIFT');facts=packet.get('facts');need(type(facts) is dict and facts.get('host')==CLOUD and facts.get('originalCheckpointDigest')==CHECKPOINT and facts.get('oldR9AuthorityReused') is False,'R10_FRESH_CLOUD_FACTS_SCOPE_DRIFT');return facts
def verify_prior(manifest,sources):
 validate_inputs(manifest,sources);host=socket.gethostname();facts=host_facts(manifest,sources,host)
 if host==LOCAL:
  cloud=fresh_cloud(manifest);again=host_facts(manifest,sources,LOCAL);need(again==facts,'R10_LOCAL_CHANGED_DURING_CLOUD_READBACK');facts={'local':facts,'cloud':cloud}
 return {'schema':'r16.r10.source-recovery-readback.v1','host':host,'factsHash':digest(facts),'sourceRecoveryEvidence':PROVENANCE,'sourceAppExpectedState':'STOPPED','businessAcceptance':False}
