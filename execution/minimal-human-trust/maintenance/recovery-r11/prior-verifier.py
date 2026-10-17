"""R11 real revision18 source proof. All old plans and deadlines are history only."""
import contextlib,fcntl,hashlib,json,os,re,shlex,socket,stat,subprocess,sys,time,types
from pathlib import Path
PROVENANCE={'schema': 'r16.recovered-source-provenance.v1', 'originalPlanHash': '45b7880b1f95cedba470e1c7d97f1656f4c77784d1c4b260861b7609d11d1c24', 'originalCapsuleHash': 'e7c8dbe016c2a36f0a1929ab52d5d0ad19ca7217c505f6c138cc64f32c595dad', 'originalRollbackDeadline': 1792175013109, 'compensationCompletionHash': '2ed7c5d22c2a854c7f47310d49fe3c5a093300ba34fdf6826a79f3e786fe0f6d', 'compensationRelationHash': '462298d6b03e14d4c2bc9da6e7d8b6c4861886b6eb78a8741d96ca48f7ea5e3b', 'cloudProofHash': '6e6ed5742c4caea3090c3d298b9e5f419723ce5120810044cc5f3e698fd4d55c', 'originalStopApprovalHash': 'd26ce58948f4a09fb7aa2442458ee2028ea68a85fe687cfde206816899bf558f', 'originalCheckpointDigest': '36bccee6812eb1c04d198868a572d049a8b4433d4d66332df12b30f1e7212a2c', 'historicalSourceStopForceUsed': True, 'drainStatus': 'UNPROVEN', 'sourceAppBaseline': 'STOPPED', 'oldPlanRenewed': False, 'businessAcceptance': False, 'r9ClosedAbort': {'schema': 'r16.r9.closed-abort-provenance.v1', 'planHash': '341625cdc01bc2ffb0db0ad45500e581f798fdb681ccbd7b9decab6742b29ae7', 'capsuleHash': '831e82dc470f354e7812b775a6d8e7ea7a6d340bea337ef177aa86f9f00d05af', 'canonicalReceiptHash': '6dc49b29225788411be367ad4676a94922934e43475b674ab88b7685bc8a5be0', 'transactionHash': '19a8286a967b575dac6e66958f7823d6c32aebc4d43ba7694a75223f02c443b4', 'localOsJournalHash': '976062efdc7da9f3d72f524e4a3c965c7db5860003f66e7e8d4d4d2cde90db50', 'cloudOsJournalHash': '45e59d72807c8b9dcff1ac7dec43ffdfabeed1f4f0e437da67bb0dc561f9b929', 'rollbackDeadline': 1792181748074, 'completedAt': 1792180641752, 'status': 'ABORTED_BEFORE_CONFIGURATION_CHANGE', 'oldPlanRenewed': False, 'authority': False}, 'r10ClosedRollback': {'schema': 'r16.r10.closed-rollback-provenance.v1', 'planHash': '9d9d329749c4c1ec52fd49c6827881593cc043e80af9d5550b742c22bae307f1', 'capsuleHash': '8a48d26dc3d44b3bccc868c3a2da34eaeb729416babafa0d7db45183dba2cb59', 'canonicalReceiptHash': 'd508d8bbe434bd38a0f6d307666f831f90ba746ae89b8e2039d644218c288961', 'transactionHash': 'fcce1d16f73c75d405ba831b23fa82d988f3827bfeeb174c6b06f7f6f0b7a38e', 'localOsJournalHash': 'dbd116caa72bc0a6a4499e8b2e72905af7ddf508e8f12dd226854e76c4e88bef', 'cloudOsJournalHash': 'bec0d74fa708c5b0122aea9fb185cab8e8fb8e794067846c50cf7c138cfad821', 'contextHash': '9f238a13a8d4179748de57c4f416e856601c6975fb54506c699984113bc408dc', 'rollbackSignedHash': 'c5247e802fd8e3cbb44582c53ac8854ab1f3f0ef272d39e2aafec0ee55b88d14', 'cloudCommitHash': '3a394a31a488c1031af289e63b38e885ecdc4e6d00775c09f0a31a69a53be9d3', 'deliveryHash': '6bd634f3cc4e9335acaff00286ed7f885df5f03b97deec0ac33286f759328c51', 'configurationRevision': 18, 'rollbackDeadline': 1792206440089, 'completedAt': 1792205681313, 'status': 'ROLLED_BACK_TO_R15_WITH_NEWER_REVISION', 'localHistoricalOsPhase': 'OS_ACTIVE', 'cloudHistoricalOsPhase': 'RECOVERY_STOPPING', 'oldPlanRenewed': False, 'authority': False}}
PINS={'prior-compensation.py': 'abf23a3859136d789a2e3239a8c6e5205c3a7c34b33e2faad97c9aa4222e4253', 'prior-native-guard.py': '21ebbb865bbd84d22aa2aa9160353c9e4ad26672edc1fa0b51a37709e8b6a51b', 'prior-evidence.json': '057d698d69297a014357dfb0d630af59c0960ac1ad82512e06dbb5b27a605518'}
LOCAL='jenn-System-Product-Name';CLOUD='VM-0-12-ubuntu'
R10_ROOT=Path('/usr/lib/r16-maintenance/recovery-r10');R10_STATE=Path('/var/lib/r16-maintenance/recovery-r10')
R10_CAP='8a48d26dc3d44b3bccc868c3a2da34eaeb729416babafa0d7db45183dba2cb59'
Q_SHA='d68e11dd01fbd41495f907f525511a2d334dae350cda502a8a6ab453bcdaa403'
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
 need(name not in sys.modules,'R11_READER_MODULE_COLLISION');m=types.ModuleType(name);m.__file__='<sealed-r11/'+name+'>';sys.modules[name]=m
 try:exec(compile(raw,m.__file__,'exec'),m.__dict__)
 except BaseException:sys.modules.pop(name,None);raise
 return m
@contextlib.contextmanager
def component(name,raw):
 m=module(name,raw)
 try:yield m
 finally:sys.modules.pop(name,None)
def validate_inputs(manifest,sources):
 need(os.getuid()==os.geteuid()==0 and socket.gethostname() in (LOCAL,CLOUD),'R11_ROOT_FIXED_HOST_REQUIRED')
 need(manifest.get('planTemplate',{}).get('sourceRecoveryEvidence')==PROVENANCE,'R11_EXACT_PRIOR_PROVENANCE_REQUIRED')
 need(manifest['planTemplate'].get('sourceDeliveryRevision')==18 and manifest['planTemplate'].get('sourceDeliveryHash')==PROVENANCE['r10ClosedRollback']['deliveryHash'],'R11_REAL_REVISION18_SOURCE_REQUIRED')
 need(type(sources) is dict and type(manifest.get('files')) is dict,'R11_SEALED_SOURCES_REQUIRED')
 for name in ('asset-verifier.py','prior-verifier.py',*PINS):
  need(type(sources.get(name)) is bytes and sha(sources[name])==manifest['files'].get(name),'R11_NEW_SOURCE_PIN_DRIFT')
 for name,pin in PINS.items():need(sha(sources[name])==pin,'R11_FROZEN_PRIOR_COMPONENT_DRIFT')
def old_source(asset):
 raw,meta=asset.read(R10_ROOT/'SOURCE_FREEZE.json',0o644,16*1024*1024);need(sha(raw)==R10_CAP,'R11_OLD_SOURCE_FREEZE_DRIFT');freeze=asset.parse(raw)
 expected={'asset-verifier.py','cloud.mjs','context.mjs','io.mjs','legacy/control-clock.mjs','legacy/lease-core.mjs','local.mjs','maintenance-release-base.mjs','os_entry.py','prior-compensation.py','prior-evidence.json','prior-native-guard.py','prior-verifier.py','publication.mjs','quiescence.py','release-publication-base.mjs','run.mjs','state.mjs','transaction-driver.mjs'}
 need(set(freeze.get('files',{}))==expected and freeze['files']['quiescence.py']==Q_SHA,'R11_OLD_SOURCE_SCOPE_DRIFT');rows={}
 for name,pin in freeze['files'].items():
  asset.safe(name);b,_=asset.read(R10_ROOT/name,0o644,16*1024*1024);need(sha(b)==pin,'R11_OLD_SOURCE_CODE_DRIFT');rows[name]=b
 return raw,meta,freeze,rows
def pinned_json(asset,name,pin,maximum=8*1024*1024):
 raw,meta=asset.read(R10_STATE/name,0o600,maximum);need(sha(raw)==pin,'R11_OLD_'+name.replace('.','_').replace('-','_').upper()+'_DRIFT');return asset.parse(raw),raw,meta
def old_records(asset,host):
 p=PROVENANCE['r10ClosedRollback'];plan,raw,_=pinned_json(asset,'plan.json',p['planHash']);need(plan.get('capsuleHash')==plan.get('sourceFreezeHash')==R10_CAP and plan.get('rollbackDeadline')==p['rollbackDeadline'],'R11_OLD_PLAN_BINDING_DRIFT')
 cap,_=asset.read(R10_STATE/'capsule.json',0o600,16*1024*1024);need(sha(cap)==R10_CAP,'R11_OLD_INSTALLED_CAPSULE_DRIFT')
 names={'os-journal.json':p['localOsJournalHash'],'transaction-transaction.json':p['transactionHash'],'transaction-receipt.json':p['canonicalReceiptHash'],'transaction-rollback-signed.json':p['rollbackSignedHash']} if host==LOCAL else {'cloud-os-journal.json':p['cloudOsJournalHash'],'cloud-commit-18.json':p['cloudCommitHash']}
 docs={};hashes={'plan':sha(raw),'capsule':sha(cap)}
 for name,pin in names.items():docs[name],b,_=pinned_json(asset,name,pin,32*1024*1024);hashes[name]=sha(b)
 journal=docs['os-journal.json' if host==LOCAL else 'cloud-os-journal.json'];expected_phase=p['localHistoricalOsPhase'] if host==LOCAL else p['cloudHistoricalOsPhase']
 need(journal.get('schema')=='r16.os-maintenance-journal.v3' and journal.get('planHash')==p['planHash'] and journal.get('cycle')==1 and journal.get('pending') is None and journal.get('phase')==expected_phase,'R11_OLD_OS_HISTORY_DRIFT')
 if host==LOCAL:
  context_raw,_=asset.read(R10_STATE/'context.json',0o600,64*1024*1024);need(sha(context_raw)==p['contextHash'],'R11_OLD_CONTEXT_RAW_DRIFT');hashes['context.json']=sha(context_raw)
  tx=docs['transaction-transaction.json'];receipt=docs['transaction-receipt.json'];signed=docs['transaction-rollback-signed.json'];steps=tx.get('steps',{})
  need(tx.get('schema')=='r16.maintenance-transaction.v3' and tx.get('mode')=='ROLLBACK' and all(steps.get(n,{}).get('status')=='DONE' for n in ('rollback-signed','rollback-cloud','rollback-local','rollback-activate','rollback-readback')),'R11_OLD_ROLLBACK_NOT_CLOSED')
  need(digest(signed)==steps['rollback-signed'].get('resultHash') and digest(signed.get('delivery'))==p['deliveryHash'] and signed.get('preserveCurrentLedgers') is True and signed.get('restoreHistoricalLedgerSnapshot') is False,'R11_OLD_SIGNED_ROLLBACK_SCOPE_DRIFT')
  need(receipt.get('schema')=='r16.maintenance-completion.v3' and receipt.get('status')==p['status'] and receipt.get('configurationRevision')==18 and receipt.get('completedAt')==p['completedAt']<p['rollbackDeadline'] and receipt.get('businessAcceptance') is False,'R11_OLD_CANONICAL_ROLLBACK_NOT_PROVEN')
 else:
  commit=docs['cloud-commit-18.json'];need(commit.get('revision')==18 and commit.get('deliveryHash')==p['deliveryHash'] and commit.get('businessLedgerMutationPerformed') is False,'R11_OLD_CLOUD_ROLLBACK_COMMIT_DRIFT')
 return {'hashes':hashes,'journal':journal,'plan':plan}
def manager_inactive():
 unit='r16-native-recovery-maintenance-r10.service';keys=('Id','ActiveState','MainPID','ControlPID','Job')
 r=subprocess.run(('/usr/bin/systemctl','show',unit,'--property='+','.join(keys)),stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,env=ENV,timeout=10,check=False);need(r.returncode==0 and len(r.stdout)<8192,'R11_OLD_MANAGER_READBACK_REFUSED');p=dict(x.split('=',1) for x in r.stdout.decode().splitlines() if '=' in x)
 need(set(p)==set(keys) and p['Id']==unit and p['ActiveState'] in ('inactive','failed') and p['MainPID']==p['ControlPID']=='0' and p['Job'] in ('','0'),'R11_OLD_MAINTENANCE_STILL_ACTIVE')
 root=Path('/sys/fs/cgroup/system.slice')/unit
 if root.exists():
  for d,children,_ in os.walk(root,followlinks=False,onerror=lambda e:(_ for _ in ()).throw(e)):
   need(not Path(d).is_symlink() and all(not (Path(d)/x).is_symlink() for x in children),'R11_OLD_CGROUP_SYMLINK');need((Path(d)/'cgroup.procs').read_text().strip()=='','R11_OLD_MAINTENANCE_WRITER_PRESENT')
def roles(old_sources,host):
 with component('r11_old_source_q',old_sources['quiescence.py']) as q:
  need(sha(old_sources['quiescence.py'])==Q_SHA,'R11_OLD_QUIESCENCE_DRIFT');backend=q.RealBackend();result={}
  for unit in (('r16-owner.service','r16-native.service') if host==LOCAL else ('r16-app.service','r16-bridge.service')):
   s=backend.inspect(unit,PROVENANCE['r10ClosedRollback']['planHash']);phase='SOURCE' if unit in ('r16-app.service','r16-native.service') else 'STATIC'
   need(s.code_phase==phase and s.fence_hash is None and not s.pending_job and not s.daemon_reload_needed and s.graceful_only(),'R11_SOURCE_ROLE_POLICY_OR_CODE_DRIFT')
   if unit=='r16-app.service':need(s.stopped(),'R11_SOURCE_APP_NOT_STOPPED')
   else:need(s.active=='active' and s.sub=='running' and s.main_pid>0 and s.main_start>0 and s.main_pid in s.members,'R11_SOURCE_ROLE_NOT_RUNNING')
   result[unit]={'active':s.active,'sub':s.sub,'mainPid':s.main_pid,'mainStartTicks':str(s.main_start),'controlPid':s.control_pid,'members':sorted(s.members),'restarts':s.restarts,'codePhase':phase,'fenced':False,'pendingJob':False}
  return result
NODE_READONLY=r'''import fs from 'node:fs';import {pathToFileURL}from'node:url';
const R='/usr/lib/r16-maintenance/recovery-r10',S='/var/lib/r16-maintenance/recovery-r10';
const {protectedBytes,digest,same,need}=await import(pathToFileURL(R+'/io.mjs'));
const json=p=>JSON.parse(protectedBytes(p,{max:64*1024*1024}));
const {verified}=await import(pathToFileURL(R+'/legacy/lease-core.mjs'));
const pub=json('/var/lib/r16-maintenance/recovery-r9/package/metadata/R15_PUBLIC_CONFIG.json');need(digest(pub)==='be3ff2b5125f8212206d2848bb32889c3c6b50a8ca56aa3b1a4bc4359591bbdb','SOURCE_PUBLIC_DRIFT');
let result;
if(process.argv[1]==='local'){
 const {captureLocal,assertPreserved,PATHS}=await import(pathToFileURL(R+'/state.mjs'));
 const raw=protectedBytes(S+'/context.json',{max:64*1024*1024}),context=JSON.parse(raw);need((await import('node:crypto')).createHash('sha256').update(raw).digest('hex')==='9f238a13a8d4179748de57c4f416e856601c6975fb54506c699984113bc408dc','OLD_CONTEXT_RAW_DRIFT');need(context.schema==='r16.native-recovery-context.v3'&&context.planHash==='9d9d329749c4c1ec52fd49c6827881593cc043e80af9d5550b742c22bae307f1'&&same(context.inputs.sourcePublicConfig,pub),'OLD_CONTEXT_SCOPE_DRIFT');
 const currentPub=json(PATHS.public);need(same(currentPub,pub),'SOURCE_PUBLIC_SELECTED_TARGET');const current=captureLocal(pub);assertPreserved(context.before,current);const d=current.configuration.delivery,b=verified(d?.envelope,pub.issuerPublicKey,'r16.configuration-delivery.v1');need(d.revision===18&&b.revision===18&&digest(d.envelope)==='6bd634f3cc4e9335acaff00286ed7f885df5f03b97deec0ac33286f759328c51'&&same(b.publicConfig,pub)&&same(b.control,{grantId:'r16-projects-daily',grantVersion:1,status:'ACTIVE',connectRequested:true})&&d.hash===digest({publicConfig:pub,control:b.control,connectionNonce:current.configuration.connectionNonce||0}),'REAL_SOURCE18_OWNER_DELIVERY_DRIFT');
 const snapshots={proposal:json(PATHS.proposal),reviewed:json(PATHS.reviewed),native:json(PATHS.native),cutover:json(PATHS.localCutover)};
 for(const [k,v]of Object.entries(snapshots))need(same(v,context.snapshots[k]),'SOURCE_SELECTOR_CHANGED');need(snapshots.native.codeManifest==='/opt/r16/releases/r16-daily-20261012-r15/native-manifest.json'&&snapshots.cutover.phase==='ACTIVE','SOURCE_NATIVE_SELECTOR_DRIFT');
 const again=captureLocal(pub);assertPreserved(current,again);need(same(again.configuration.delivery,current.configuration.delivery),'SOURCE_DELIVERY_CHANGED_DURING_READ');
 for(const [k,p]of Object.entries({proposal:PATHS.proposal,reviewed:PATHS.reviewed,native:PATHS.native,cutover:PATHS.localCutover}))need(same(json(p),snapshots[k]),'SOURCE_SELECTOR_CHANGED_DURING_READ');need(same(json(PATHS.public),pub),'SOURCE_PUBLIC_CHANGED_DURING_READ');
 need(protectedBytes(S+'/context.json',{max:64*1024*1024}).equals(raw),'OLD_CONTEXT_CHANGED_DURING_READ');need(same(json('/etc/r16-owner/release-proposal.json').release,pub.release)&&same(json('/etc/r16-owner/release-proposal.json').versions,pub.versions),'SOURCE_OWNER_PROPOSAL_PUBLICATION_DRIFT');
 result={publicConfigHash:digest(pub),snapshotHashes:Object.fromEntries(Object.entries(snapshots).map(([k,v])=>[k,digest(v)])),issuerDataHash:current.issuerDataHash,configurationInvariantHash:current.configurationInvariantHash,originalUnknownHash:digest(current.originalUnknown),projectBusinessHashes:current.projectBusinessHashes,sourceDeliveryHash:digest(current.configuration.delivery.envelope),contextSha256:(await import('node:crypto')).createHash('sha256').update(raw).digest('hex')};
}else{
 const paths={app:'/etc/r16-cloud/app-host.json',public:'/etc/r16-cloud/public-config.json',control:'/etc/r16-cloud/authority-control.json',cutover:'/etc/r16-cloud/cutover.json',startAttempt:'/var/lib/r16-cloud/start-attempt.json',accepted:'/var/lib/r16-cloud/authority/state.json'};
 function cloudData(w){need(w&&typeof w==='object'&&!Array.isArray(w)&&same(Object.keys(w).sort(),['data','maxNow','revision','schema'])&&w.schema===1&&Number.isSafeInteger(w.revision)&&w.revision>=0&&Number.isSafeInteger(w.maxNow)&&w.maxNow>=0&&w.data&&typeof w.data==='object'&&!Array.isArray(w.data)&&w.data.kind==='r16.cloud-publication.v1','SOURCE_CLOUD_WRAPPER_INVALID');return w.data;}
 const values=Object.fromEntries(Object.entries(paths).map(([k,p])=>[k,json(p)])),w=values.accepted,data=cloudData(w),accepted=data.accepted,b=verified(accepted,pub.issuerPublicKey,'r16.configuration-delivery.v1');
 need(b.revision===18&&digest(accepted)==='6bd634f3cc4e9335acaff00286ed7f885df5f03b97deec0ac33286f759328c51'&&same(b.publicConfig,pub)&&same(values.public,pub)&&same(values.control,b.control)&&same(b.control,{grantId:'r16-projects-daily',grantVersion:1,status:'ACTIVE',connectRequested:true}),'SOURCE_CLOUD_DELIVERY_DRIFT');
 need(values.app.codeManifest==='/opt/r16/releases/r16-daily-20261012-r15/app-manifest.json'&&values.app.publicConfiguration===paths.public&&same(values.app,json(S+'/cloud-source-app.json')),'SOURCE_APP_SELECTOR_DRIFT');
 need(values.cutover.schema==='r16.cloud-cutover.v1'&&values.cutover.phase==='ACTIVE'&&values.cutover.grantId==='r16-projects-daily'&&values.cutover.releaseId==='r16-daily-20261012-r15'&&same(values.startAttempt,{schema:'r16.cloud-start-attempt.v1',grantId:'r16-projects-daily',revision:18}),'SOURCE_CLOUD_CUTOVER_DRIFT');
 for(const [k,p]of Object.entries(paths)){const again=json(p);if(k==='accepted'){const after=cloudData(again);need(again.revision>=w.revision&&again.maxNow>=w.maxNow,'SOURCE_CLOUD_WRAPPER_CLOCK_ROLLBACK');need(same(after,data),'SOURCE_CLOUD_CHANGED_DURING_READ');}else need(same(again,values[k]),'SOURCE_CLOUD_CHANGED_DURING_READ');}result={publicConfigHash:digest(pub),deliveryHash:digest(accepted),sourceFileHashes:Object.fromEntries(Object.entries(values).map(([k,v])=>[k,digest(k==='accepted'?data:v)])),sourceAppConfigHash:digest(values.app)};
}
console.log(JSON.stringify(result));
'''
def node_facts(host):
 binary='/usr/bin/node' if host==LOCAL else '/opt/r16/runtime/node-v24.15.0/bin/node';phase='local' if host==LOCAL else 'cloud';r=subprocess.run((binary,'--input-type=module','-e',NODE_READONLY,phase),stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,env=ENV,timeout=90,check=False)
 need(r.returncode==0 and 0<len(r.stdout)<=65536,'R11_SOURCE_BUSINESS_OR_SELECTORS_NOT_PRESERVED');value=json.loads(r.stdout);need(type(value) is dict and value.get('publicConfigHash')==PUBLIC_SHA,'R11_SOURCE_PUBLIC_CONFIG_DRIFT');return value

HOST=CLOUD;STATE=R10_STATE;PLAN=PROVENANCE['r10ClosedRollback']['planHash'];CAP=R10_CAP;PUBLIC=PUBLIC_SHA
STOP=Path('/var/lib/r16-maintenance/first-stop-r8');OLD=Path('/usr/lib/r16-maintenance/first-stop-r8/cfa55305623727e1b7607705c7b7a8eb76d2221250368828d21b7779da75af41')
APPROVAL=PROVENANCE['originalStopApprovalHash'];ROLLBACK_DELIVERY=PROVENANCE['r10ClosedRollback']['deliveryHash'];COMMIT18_RAW=PROVENANCE['r10ClosedRollback']['cloudCommitHash'];EXPECTED_FILES=3555
READER_PINS={'ledger_checkpoint.py': '98dbbc1d960bf9674735a17990be590e7e8f1516c125ab88c20231f24594547b', 'stop_driver.py': 'ee74716174e7ae645a6558d26b50a7cadc43d422a78ca575d1d32bcf82d2c23b'}
def stamp(s):return (s.st_dev,s.st_ino,s.st_mode,s.st_uid,s.st_gid,s.st_nlink,s.st_size,s.st_mtime_ns,s.st_ctime_ns)
def protected(path,mode=0o600,maximum=32*1024*1024):
 cursor=Path('/')
 for bit in path.parts[1:-1]:
  cursor/=bit;s=cursor.lstat();need(stat.S_ISDIR(s.st_mode) and s.st_uid==0 and not s.st_mode&0o022,'PROTECTED_ANCESTOR_REFUSED')
 fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
 try:
  before=os.fstat(fd);need(stat.S_ISREG(before.st_mode) and before.st_uid==0 and before.st_nlink==1 and stat.S_IMODE(before.st_mode)==mode and 0<before.st_size<=maximum,'PROTECTED_METADATA_REFUSED');raw=b''
  while len(raw)<=maximum:
   block=os.read(fd,min(1048576,maximum+1-len(raw)))
   if not block:break
   raw+=block
  need(len(raw)==before.st_size and stamp(before)==stamp(os.fstat(fd))==stamp(path.lstat()),'PROTECTED_READ_CHANGED');return raw
 finally:os.close(fd)
def exited():
 keys=('Id','ActiveState','SubState','MainPID','ControlPID','Job')
 r=subprocess.run(('/usr/bin/systemctl','show','r16-app.service','--property='+','.join(keys)),stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,env=ENV,timeout=10,check=False)
 need(r.returncode==0 and 0<len(r.stdout)<8192,'APP_MANAGER_READBACK_REFUSED');p=dict(line.split('=',1) for line in r.stdout.decode().splitlines() if '=' in line)
 need(set(p)==set(keys) and p['Id']=='r16-app.service' and p['ActiveState'] in ('inactive','failed') and p['MainPID']==p['ControlPID']=='0' and p['Job'] in ('','0'),'APP_NOT_STOPPED');return p
def validate_authority(L,pub,selector,manifest,control,cutover,token,accepted,plan,commit,now):
 need(L.digest(pub)==PUBLIC,'SOURCE_PUBLIC_CONFIG_CHANGED')
 L._public(pub,now,L.PUBLIC_DIGEST,L.GRANT_DIGEST)
 need(selector.get('schema')=='r16.app-host.v1' and selector.get('publicConfiguration')==str(L.PUBLIC) and selector.get('codeManifest')==str(L.SOURCE/'app-manifest.json'),'SOURCE_APP_SELECTOR_DRIFT')
 need(manifest.get('role')=='app' and L.digest(manifest)==L.APP_VERSION and pub['versions']['app']==L.APP_VERSION,'SOURCE_APP_MANIFEST_DRIFT')
 data=L._wrapper(accepted,'r16.cloud-publication.v1');delivery=data.get('accepted');b=L.verified(delivery,pub['issuerPublicKey'],'r16.configuration-delivery.v1')
 need(set(b)=={'schema','revision','issuedAt','publicConfig','control'} and type(b['revision']) is int and b['revision']==18 and type(b['issuedAt']) is int and plan['approvedAt']<=b['issuedAt']<=plan['rollbackDeadline'] and b['issuedAt']<=now,'ROLLBACK18_DELIVERY_STRUCTURE_REFUSED')
 expected={'grantId':'r16-projects-daily','grantVersion':1,'status':'ACTIVE','connectRequested':True}
 need(L.canonical(b['publicConfig'])==L.canonical(pub) and L.canonical(b['control'])==L.canonical(control)==L.canonical(expected),'ROLLBACK18_AUTHORITY_SCOPE_CHANGED')
 need(L.digest(delivery)==ROLLBACK_DELIVERY and commit.get('status')=='CONFIGURATION_COMMITTED_SERVICES_FENCED' and type(commit.get('revision')) is int and commit['revision']==18 and commit.get('businessLedgerMutationPerformed') is False and commit.get('deliveryHash')==L.digest(delivery) and commit.get('publicConfigHash')==L.digest(pub),'R10_ROLLBACK18_COMMIT_MISMATCH')
 need(cutover.get('schema')=='r16.cloud-cutover.v1' and cutover.get('phase')=='ACTIVE' and cutover.get('grantId')=='r16-projects-daily' and cutover.get('releaseId')=='r16-daily-20261012-r15','SOURCE_CUTOVER_DRIFT')
 need(L.canonical(token)==L.canonical({'schema':'r16.cloud-start-attempt.v1','grantId':'r16-projects-daily','revision':18}),'START_ATTEMPT_NOT_REVISION18')
 return {'deliveryHash':L.digest(delivery),'publicConfigHash':L.digest(pub),'revision':18,'acceptedDataHash':L.digest(data)}
def authority_snapshot(L,plan):
 pub=L.read_public(L.PUBLIC);selector=L.read_public(L.SELECTOR);manifest=L.read_public(L.SOURCE/'app-manifest.json');control=L.read_public(L.CONTROL);cutover=L.read_public(L.CUTOVER);token=L.read_public(Path('/var/lib/r16-cloud/start-attempt.json'));accepted=L.read_accepted();raw=protected(STATE/'cloud-commit-18.json');need(sha(raw)==COMMIT18_RAW,'R10_CLOUD_COMMIT18_RAW_DRIFT');commit=L.parse(raw)
 proof=validate_authority(L,pub,selector,manifest,control,cutover,token,accepted,plan,commit,int(time.time()*1000))
 return {'public':pub,'selector':selector,'manifest':manifest,'control':control,'cutover':cutover,'token':token,'acceptedData':accepted['data'],'revision':accepted['revision'],'maxNow':accepted['maxNow'],'commitRawHash':sha(raw),'proof':proof}
def same_authority(L,before,after):
 need(after['revision']>=before['revision'] and after['maxNow']>=before['maxNow'],'ACCEPTED_WRAPPER_CLOCK_ROLLBACK')
 need({k:v for k,v in before.items() if k not in ('revision','maxNow')}=={k:v for k,v in after.items() if k not in ('revision','maxNow')},'ROLLBACK18_AUTHORITY_CHANGED_DURING_CAPTURE')
def full_checkpoint_capture(L,D,approval,original,plan):
 target=approval['target'];phase=L._target_state(target,False);need(phase=='EXITED','ORIGINAL_APP_NOT_EXITED');manager=exited();before=authority_snapshot(L,plan)
 registration,registration_hash=L.read_registration();registered=L.registration_bindings(registration)
 one,ids,dirs=L.read_store_tree(expected_root_identity=registered['app']);need(dirs.get('host')==registered['app'],'SEALED_APP_DIRECTORY_IDENTITY_DRIFT');L._scan_writers(ids,dirs,target['pid'])
 two,ids2,dirs2=L.read_store_tree(expected_root_identity=registered['app']);need(one==two and ids==ids2 and dirs==dirs2,'CHECKPOINT_CHANGED');L._scan_writers(ids2,dirs2,target['pid'])
 need(L._target_state(target,False)==phase and exited()==manager,'APP_STATE_CHANGED_DURING_CAPTURE')
 after_registration,after_hash=L.read_registration();need(registration_hash==after_hash and registration==after_registration and L.registration_bindings(after_registration)==registered,'SEALED_REGISTRATION_CHANGED')
 same_authority(L,before,authority_snapshot(L,plan))
 checkpoint={'schema':'r16.source-app-durable-checkpoint.v1','completeRegisteredFileSet':True,'otherWriterPids':[],'files':two,'staleLockProofs':L._stale_lock_proofs(two,target),'missingLockProofs':L._missing_lock_proofs(two,dirs2,target,phase)}
 checkpoint.update(L.validate_checkpoint(checkpoint,target,before['public'],int(time.time()*1000)))
 manifest=D.checkpoint_manifest(checkpoint,approval)
 need(manifest==original.get('checkpoint') and D.digest(manifest)==CHECKPOINT and len(two)==EXPECTED_FILES,'FULL_ORIGINAL_APP_CHECKPOINT_CHANGED')
 att=checkpoint['attestation'];need(att['signatureVerification'] is True and att['originalUnknownCount']==2 and att['otherDurableInflight']==0 and att['foreignOpenWriters']==0,'FULL_LEDGER_SIGNATURE_BINDING_REFUSED')
 return {'status':'FULL_ORIGINAL_APP_CHECKPOINT_READONLY_PASS','schema':'r16.r11.original-app-checkpoint-readback.v1','host':HOST,'planHash':PLAN,'capsuleHash':CAP,'checkpointDigest':CHECKPOINT,'files':len(two),'registeredProjectCount':att['registeredProjectCount'],'originalUnknownCount':2,'originalLeaseBindingsPreserved':True,'completeRegisteredFileSet':True,'sealedRegistrationHash':registration_hash,'signatureVerification':True,'authority':before['proof'],'sourceAppStopped':True,'drainStatus':'UNPROVEN','effectsIssued':0,'businessAcceptance':False}
def cloud_checkpoint(asset,plan):
 raw={n:protected(OLD/n,0o644) for n in READER_PINS}
 for n,pin in READER_PINS.items():need(sha(raw[n])==pin,'R11_ORIGINAL_READER_SOURCE_DRIFT')
 with component('r11_original_full_ledger',raw['ledger_checkpoint.py']) as L,component('r11_original_full_validator',raw['stop_driver.py']) as D:
  approval_raw=protected(STOP/'approval.json');approval=L.parse(approval_raw);original_raw=protected(STOP/'transaction.json');original=L.parse(original_raw)
  need(D.digest(approval)==APPROVAL and original.get('approvalHash')==APPROVAL and original.get('targetHash')==D.digest(approval['target']) and original.get('phase')=='TERMINAL' and original.get('signalAttemptConsumed') is True and original.get('checkpointDigest')==CHECKPOINT,'R11_ORIGINAL_STOP_PROVENANCE_DRIFT')
  proof=full_checkpoint_capture(L,D,approval,original,plan)
  need(proof['registeredProjectCount']==9 and protected(STOP/'approval.json')==approval_raw and protected(STOP/'transaction.json')==original_raw and all(protected(OLD/n,0o644)==b for n,b in raw.items()),'R11_FULL_CHECKPOINT_PROVENANCE_DRIFT')
  return proof
@contextlib.contextmanager
def old_read_locks(asset,host):
 fds=[]
 try:
  for name in ('entry.lock', '.transaction-lock') if host==LOCAL else ('entry.lock',):
   path=R10_STATE/name;_,meta=asset.read(path,0o600,4096);fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW);fds.append(fd);need(asset.stamp(os.fstat(fd))==meta,'R11_OLD_LOCK_CHANGED');fcntl.flock(fd,fcntl.LOCK_SH|fcntl.LOCK_NB)
  yield
 finally:
  for fd in reversed(fds):os.close(fd)
def host_facts(manifest,sources,host):
 validate_inputs(manifest,sources);need(socket.gethostname()==host,'R11_READER_HOST_MISMATCH')
 with component('r11_assets_readonly',sources['asset-verifier.py']) as asset:
  old_raw,old_meta,freeze,old_sources=old_source(asset)
  with old_read_locks(asset,host):
   manager_inactive();before=old_records(asset,host);assets=asset.verify_assets(manifest,sources);actors=roles(old_sources,host);business=node_facts(host)
   checkpoint=cloud_checkpoint(asset,before['plan']) if host==CLOUD else None
   need(roles(old_sources,host)==actors and node_facts(host)==business,'R11_SOURCE_CHANGED_DURING_CAPTURE');need(before==old_records(asset,host),'R11_OLD_RECORDS_CHANGED_DURING_CAPTURE');manager_inactive()
   need(old_source(asset)==(old_raw,old_meta,freeze,old_sources),'R11_OLD_SOURCE_CHANGED_DURING_CAPTURE')
  return {'schema':'r16.r11.host-source-facts.v1','host':host,'oldR10Hashes':before['hashes'],'assets':assets,'actors':actors,'business':business,'originalCheckpointDigest':checkpoint['checkpointDigest'] if checkpoint else None,'fullAppCheckpoint':checkpoint,'oldCanonicalReceiptLocallyVerified':host==LOCAL,'oldR10AuthorityReused':False,'businessAcceptance':False}
def cloud_facts(manifest,sources):return host_facts(manifest,sources,CLOUD)
REMOTE_READER=r'''import hashlib,json,os,stat,sys,types
from pathlib import Path
B=Path('/home/ubuntu/r16-maintenance-recovered-r11-candidate')
def need(v):
 if not v:raise ValueError('R11_SEALED_CLOUD_READER_REFUSED')
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
m=types.ModuleType('r11_remote_prior_reader');m.__file__='<sealed-r11-remote-prior>';sys.modules[m.__name__]=m;exec(compile(sources['prior-verifier.py'],m.__file__,'exec'),m.__dict__);facts=m.cloud_facts(manifest,sources)
print(json.dumps({'schema':'r16.r11.sealed-cloud-facts.v1','capsuleHash':EXPECTED_CAP,'facts':facts},sort_keys=True,separators=(',',':')))
'''
def fresh_cloud(manifest):
 # The R11 candidate SOURCE_FREEZE bytes are canonical builder output, no newline.
 cap=digest(manifest);code='EXPECTED_CAP='+repr(cap)+'\nEXPECTED_MANIFEST='+repr(manifest)+'\n'+REMOTE_READER
 # No payload pins/manifest on argv: 1.85MiB is beyond ARG_MAX. Pipe only public reader source.
 command=shlex.join(('/usr/bin/sudo','-n','--','/usr/bin/python3','-I','-B','-'))
 r=subprocess.run((*SSH,command),input=code.encode(),stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,env=ENV,timeout=240,check=False)
 need(r.returncode==0 and 0<len(r.stdout)<=65536,'R11_FRESH_CLOUD_READBACK_REFUSED');packet=json.loads(r.stdout);need(packet.get('schema')=='r16.r11.sealed-cloud-facts.v1' and packet.get('capsuleHash')==cap,'R11_FRESH_CLOUD_CAPSULE_DRIFT');facts=packet.get('facts');need(type(facts) is dict and facts.get('host')==CLOUD and facts.get('originalCheckpointDigest')==CHECKPOINT and facts.get('oldR10AuthorityReused') is False,'R11_FRESH_CLOUD_FACTS_SCOPE_DRIFT');return facts
def verify_prior(manifest,sources):
 validate_inputs(manifest,sources);host=socket.gethostname();facts=host_facts(manifest,sources,host)
 if host==LOCAL:
  cloud=fresh_cloud(manifest);again=host_facts(manifest,sources,LOCAL);need(again==facts,'R11_LOCAL_CHANGED_DURING_CLOUD_READBACK');facts={'local':facts,'cloud':cloud}
 return {'schema':'r16.r11.source-recovery-readback.v1','host':host,'factsHash':digest(facts),'sourceRecoveryEvidence':PROVENANCE,'sourceAppExpectedState':'STOPPED','businessAcceptance':False}
