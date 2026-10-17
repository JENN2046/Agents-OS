"""Stdlib-only R12 sealed memory entry; no root Documents import.
CAPSULE, ENTRY_SHA, PHASE and MODE are bound by the reviewed outer launcher.
"""
import hashlib,json,math,os,re,resource,secrets,socket,stat,subprocess,sys,time,types
from pathlib import Path
LOCAL='jenn-System-Product-Name';CLOUD='VM-0-12-ubuntu'
LOCAL_SOURCE=Path('/home/jenn/AGENTS_OS_Workspace/ops/g1d-native-recovery-reconnect-20261014-r1/r15-backport/maintenance-recovered-r12')
CLOUD_SOURCE=Path('/home/ubuntu/r16-maintenance-recovered-r12-candidate')
TARGET='r16-daily-20261015-r15-app-recovery-r6'
GUARD_SHA='21ebbb865bbd84d22aa2aa9160353c9e4ad26672edc1fa0b51a37709e8b6a51b'
REVISION_SCOPE={'sourceDeliveryRevision':18,'sourceDeliveryHash':'6bd634f3cc4e9335acaff00286ed7f885df5f03b97deec0ac33286f759328c51','forwardRevision':19,'rollbackRevision':20}
REQUIRED={'os_entry.py','quiescence.py','run.mjs','context.mjs','cloud.mjs','prior-verifier.py','prior-compensation.py','prior-native-guard.py','prior-evidence.json','asset-verifier.py'}
class Refused(Exception):
 def __init__(self,code):self.code=code;super().__init__(code)
def need(v,code):
 if not v:raise Refused(code)
def canonical(v):return json.dumps(v,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()
def digest(v):return hashlib.sha256(canonical(v)).hexdigest()
def now_ms():return time.time_ns()//1000000
def relative(name):need(type(name) is str and name and '\\' not in name and not name.startswith('/') and all(x not in ('','.','..') for x in name.split('/')),'R12_SOURCE_PATH_REFUSED');return name
def read_public(path,maximum=16*1024*1024):
 cursor=Path('/')
 for name in path.parts[1:-1]:
  cursor/=name;s=cursor.lstat();need(stat.S_ISDIR(s.st_mode) and s.st_uid in (0,1000) and not s.st_mode&0o022,'R12_SOURCE_PARENT_REFUSED')
 fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
 try:
  a=os.fstat(fd);need(stat.S_ISREG(a.st_mode) and a.st_uid in (0,1000) and a.st_nlink==1 and not a.st_mode&0o7022 and a.st_size<=maximum,'R12_SOURCE_FILE_REFUSED');raw=b''
  while len(raw)<=maximum:
   b=os.read(fd,min(1024*1024,maximum+1-len(raw)))
   if not b:break
   raw+=b
  stamp=lambda s:(s.st_dev,s.st_ino,s.st_mode,s.st_uid,s.st_gid,s.st_nlink,s.st_size,s.st_mtime_ns,s.st_ctime_ns)
  need(len(raw)==a.st_size and stamp(a)==stamp(os.fstat(fd))==stamp(path.lstat()),'R12_SOURCE_CHANGED');return raw,stat.S_IMODE(a.st_mode)
 finally:os.close(fd)
def parse(raw):
 def unique(rows):
  d={}
  for k,v in rows:need(k not in d,'R12_DUPLICATE_JSON_KEY');d[k]=v
  return d
 return json.loads(raw,object_pairs_hook=unique)
def seal_candidate(base,cap,entry):
 need(isinstance(cap,str) and re.fullmatch('[a-f0-9]{64}',cap) is not None and isinstance(entry,str) and re.fullmatch('[a-f0-9]{64}',entry) is not None,'R12_FINAL_SOURCE_SEAL_REQUIRED')
 raw,_=read_public(base/'SOURCE_FREEZE.json');need(hashlib.sha256(raw).hexdigest()==cap,'R12_CAPSULE_HASH_DRIFT');manifest=parse(raw)
 need(set(manifest)=={'schema','files','payloadFiles','planTemplate'} and manifest['schema']=='r16.native-recovery-source-freeze.v3' and type(manifest['files']) is dict and len(manifest['files'])==19 and REQUIRED<=set(manifest['files']) and type(manifest['payloadFiles']) is dict and len(manifest['payloadFiles'])==12600 and manifest['files']['os_entry.py']==entry,'R12_COMPLETE_SOURCE_SCOPE_REQUIRED')
 plan=manifest['planTemplate'];need(plan.get('targetReleaseId')==TARGET and plan.get('activationScope')=='START_REVIEWED_TARGET_APP_IF_SOURCE_ALREADY_STOPPED' and type(plan.get('sourceRecoveryEvidence')) is dict and not any('firstStop' in k for k in plan),'R12_PLAN_SCOPE_REFUSED')
 need(all(plan.get(k)==v for k,v in REVISION_SCOPE.items()),'R12_REVISION_CHAIN_REFUSED')
 sources={};sizes={};block=os.statvfs('/usr/lib/r16-maintenance').f_frsize
 for name,pin in manifest['files'].items():
  content,mode=read_public(base/relative(name));need(hashlib.sha256(content).hexdigest()==pin and mode==0o644,'R12_SOURCE_HASH_OR_MODE_DRIFT');sources[name]=content;sizes[name]=len(content)
 need(hashlib.sha256(sources['prior-native-guard.py']).hexdigest()==GUARD_SHA,'R12_NATIVE_GUARD_DRIFT')
 inventory=parse(read_public(base/'package/metadata/PAYLOAD_INVENTORY.json')[0]);actual=set();directories={''}
 for directory,children,files in os.walk(base/'package',followlinks=False,onerror=lambda e:(_ for _ in ()).throw(e)):
  p=Path(directory);s=p.lstat();need(stat.S_ISDIR(s.st_mode) and s.st_uid in (0,1000) and stat.S_IMODE(s.st_mode)==0o755,'R12_PACKAGE_DIRECTORY_REFUSED');directories.add(p.relative_to(base/'package').as_posix())
  for n in children:need(not (p/n).is_symlink(),'R12_PACKAGE_DIRECTORY_REFUSED')
  for n in files:actual.add((p/n).relative_to(base/'package').as_posix())
 need(actual==set(manifest['payloadFiles']),'R12_PACKAGE_FILE_SET_DRIFT');payload_sizes={};target_dirs={''}
 for name,pin in manifest['payloadFiles'].items():
  content,mode=read_public(base/'package'/relative(name));expected=inventory[name[8:]]['mode'] if name.startswith('payload/') else 0o644
  need(hashlib.sha256(content).hexdigest()==pin and mode==expected and type(expected) is int and expected in (0o644,0o755),'R12_PACKAGE_HASH_OR_MODE_DRIFT');sizes['package/'+name]=len(content)
  if name.startswith('payload/'):
   rel=name[8:];payload_sizes[rel]=len(content);target_dirs.update(str(p) for p in Path(rel).parents if str(p)!='.')
 need(len(payload_sizes)==12592,'R12_PAYLOAD_COUNT_DRIFT')
 for role in ('app','native'):payload_sizes[role+'-manifest.json']=sizes['package/metadata/'+role+'-manifest.json']
 round_block=lambda n:((n+block-1)//block)*block
 source_dirs={''}
 root_need=sum(round_block(sizes[n]) for n in manifest['files'])+2*round_block(len(raw))+4*block+32*1024*1024+16*1024*1024
 return manifest,sources,{'rootAllocatedBytes':root_need,'targetAllocatedBytes':0,'packageCopyAllocatedBytes':0,'contextBudgetBytes':32*1024*1024,'metadataAndAtomicMarginBytes':16*1024*1024,'allocationBlockBytes':block}
def assert_fresh_namespace(cap):
 fixed=(Path('/usr/lib/r16-maintenance/recovery-r12'),Path('/var/lib/r16-maintenance/recovery-r12'),Path('/etc/systemd/system/r16-native-recovery-maintenance-r12.service'),Path('/run/systemd/system/r16-native-recovery-maintenance-r12.service'),Path('/usr/libexec/r16-maintenance-os-r12'),Path('/etc/sudoers.d/r16-maintenance-os-r12'),Path('/etc/r16-maintenance/recovery-r12-source-freeze.json'),Path('/run/r16-maintenance-recovery-r12'),*(Path(root)/'r16-native-recovery-maintenance-r12.service.d' for root in ('/run/systemd/system','/etc/systemd/system')),*(Path(root)/(unit+'.d')/'97-r16-maintenance-recovery-r12.conf' for root in ('/run/systemd/system','/etc/systemd/system') for unit in ('r16-app.service','r16-bridge.service','r16-owner.service','r16-native.service')))
 for p in fixed:
  for candidate in (p,p.with_name(p.name+'.pending'),p.with_name('.'+p.name+'.pending'),p.with_name(p.name+'.next')):
   need(not os.path.lexists(candidate),'R12_EXISTING_NAMESPACE_REQUIRES_READONLY_REVIEW')
 unit='r16-native-recovery-maintenance-r12.service'
 result=subprocess.run(('/usr/bin/systemctl','show',unit,'--property=LoadState,ActiveState,MainPID,ControlPID,Job'),stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,env={'PATH':'/usr/bin:/bin','LANG':'C','LC_ALL':'C'},timeout=10,check=False)
 need(result.returncode==0 and len(result.stdout)<8192,'R12_NEW_UNIT_NAMESPACE_UNPROVEN');props=dict(x.split('=',1) for x in result.stdout.decode().splitlines() if '=' in x)
 need(set(props)=={'LoadState','ActiveState','MainPID','ControlPID','Job'} and props['LoadState']=='not-found' and props['ActiveState']=='inactive' and props['MainPID']==props['ControlPID']=='0' and props['Job'] in ('','0'),'R12_NEW_UNIT_ALREADY_KNOWN')
def memory_module(name,raw):
 need(name not in sys.modules,'R12_MEMORY_MODULE_COLLISION');m=types.ModuleType(name);m.__file__='<sealed-r12/'+name+'>';sys.modules[name]=m;exec(compile(raw,m.__file__,'exec'),m.__dict__);return m
def native_confirm(guard,pending,clock=now_ms):
 host=pending['host'];fd=guard.native_identity(host)
 try:
  words='APPLY '+('CLOUD' if host==CLOUD else 'LOCAL')+' '+digest(pending)
  text='\n新的 R12 准确待批摘要（不是旧授权续期）：\n'+json.dumps(pending,ensure_ascii=False,indent=2)+'\n'
  if host==CLOUD:text+='云端只准备新的R12维护源码、记录与固定helper/sudoers；完整复核并只读复用R9已封存包及未选择的目标文件。不清缓存、不再复制整包；此步不签发、不切换目标发行。\n'
  else:text+='本机阶段将先优雅停止仍运行的 Native、Bridge、Owner，完成既有Release/Issuer同Grant签发和双机安装后，按 Owner、Bridge、Native、目标App 顺序启动应运行角色。失败恢复保持 SOURCE App=STOPPED；旧UNKNOWN不重放、不结清；不是业务验收。\n'
  text+='旧R11云端准备记录及其期限原样保留，仅作历史；本次不继承其批准、准入或计划。\n'
  text+='真实签名配置基线18；本事务向前签发19，失败回退到更新版本20。Owner和Grant不变。\n接受完整确认后，本次引导/签发效果期5分钟，恢复最多30分钟且受云准入上限；不修改任何旧期限。\n请本人输入完整一行：'+words+'\n> '
  raw=text.encode();offset=0
  while offset<len(raw):offset+=os.write(fd,raw[offset:])
  line=b''
  while len(line)<=200:
   b=os.read(fd,1)
   if b in (b'',b'\n',b'\r'):break
   line+=b
  need(line==words.encode(),'R12_NATIVE_APPLY_CANCELLED');again=guard.native_identity(host);os.close(again);accepted=clock()
  return {'schema':'r16.r12.native-install-confirmation.v1','pendingHash':digest(pending),'nonce':pending['nonce'],'issuedAt':accepted,'expiresAt':accepted+300000}
 finally:os.close(fd)
def check_window(authority,pending,clock=now_ms):
 need(authority['pendingHash']==digest(pending) and authority['issuedAt']<=clock()<authority['expiresAt'] and authority['expiresAt']-authority['issuedAt']==300000,'R12_NATIVE_APPLY_EXPIRED')
def space_budget(allocation):
 paths=('/usr/lib/r16-maintenance','/var/lib/r16-maintenance','/opt/r16/releases')
 rows=[os.statvfs(p) for p in paths];devices=[os.stat(p).st_dev for p in paths]
 need(len(set(devices))==1,'R12_REUSED_ASSETS_FILESYSTEM_DRIFT')
 available=min(v.f_bavail*v.f_frsize for v in rows);growth=allocation['rootAllocatedBytes'];reserve=256*1024*1024
 need(allocation['targetAllocatedBytes']==allocation['packageCopyAllocatedBytes']==0,'R12_UNEXPECTED_PACKAGE_OR_TARGET_COPY')
 need(available-growth>=reserve,'R12_INSUFFICIENT_UNRESERVED_SPACE')
 return {'availableBytes':available,'newMetadataAndContextBytes':growth,'packageCopyBytes':0,'targetGrowthBytes':0,'projectedRemainingBytes':available-growth,'requiredReserveBytes':reserve,'usesRootReservedBlocks':False}
def main():
 resource.setrlimit(resource.RLIMIT_CORE,(0,0));os.umask(0o077)
 need(os.getuid()==os.geteuid()==0 and PHASE in ('cloud','local') and MODE in ('apply','preflight'),'R12_FIXED_NATIVE_ROOT_REQUIRED')
 host=CLOUD if PHASE=='cloud' else LOCAL;need(socket.gethostname()==host,'R12_FIXED_HOST_REQUIRED');base=CLOUD_SOURCE if PHASE=='cloud' else LOCAL_SOURCE
 assert_fresh_namespace(CAPSULE)
 manifest,sources,allocation=seal_candidate(base,CAPSULE,ENTRY_SHA)
 need(type(manifest['planTemplate'].get('assetReuse')) is dict,'R12_EXACT_REUSED_ASSETS_REQUIRED')
 verifier=memory_module('r12_prior_verifier',sources['prior-verifier.py']);prior=verifier.verify_prior(manifest,sources)
 need(prior.get('schema')=='r16.r12.source-recovery-readback.v1' and prior.get('host')==host and prior.get('sourceAppExpectedState')=='STOPPED' and prior.get('sourceRecoveryEvidence')==manifest['planTemplate']['sourceRecoveryEvidence'],'R12_SOURCE_RECOVERY_PROOF_REQUIRED')
 budget=space_budget(allocation)
 pending={'schema':'r16.r12.native-install-pending.v1','host':host,'capsuleHash':CAPSULE,'entrySha256':ENTRY_SHA,'targetReleaseId':TARGET,'targetAppVersion':manifest['planTemplate']['targetAppVersion'],'targetNativeVersion':manifest['planTemplate']['targetNativeVersion'],'factsHash':prior['factsHash'],'sourceRecoveryEvidence':prior['sourceRecoveryEvidence'],'assetReuse':manifest['planTemplate']['assetReuse'],'sourceAppBaseline':'STOPPED','oldPlanRenewed':False,'sameGrant':True,'ownerIdentityChanged':False,'originalUnknownReplayedOrSettled':False,'rollbackAppExpectedState':'STOPPED','rollbackAppCodePhase':'SOURCE','gracefulStopOrder':[] if PHASE=='cloud' else ['r16-native.service','r16-bridge.service','r16-owner.service'],'successfulActivationOrder':[] if PHASE=='cloud' else ['r16-owner.service','r16-bridge.service','r16-native.service','r16-app.service'],'businessAcceptance':False,'nonce':secrets.token_hex(16),'cacheCleanupPerformed':False,'packageOrTargetCopyPlanned':False,'spaceBudget':budget}
 pending.update(REVISION_SCOPE)
 if MODE=='preflight':return {'status':'R12_READONLY_PREFLIGHT_PASS','pending':pending,'productionEffects':0,'approvalCreated':False}
 guard=memory_module('native_guard',sources['prior-native-guard.py']);authority=native_confirm(guard,pending);check_window(authority,pending)
 assert_fresh_namespace(CAPSULE)
 again,again_sources,again_allocation=seal_candidate(base,CAPSULE,ENTRY_SHA);need(again==manifest and again_sources==sources and again_allocation==allocation,'R12_SOURCE_CHANGED_DURING_CONFIRMATION')
 need(verifier.verify_prior(manifest,sources)==prior,'R12_REAL_FACTS_CHANGED_DURING_CONFIRMATION');check_window(authority,pending);space_budget(allocation)
 check_window(authority,pending);sys.argv=[str(base/'os_entry.py'),'bootstrap-'+PHASE,CAPSULE]
 return exec(compile(sources['os_entry.py'],str(base/'os_entry.py'),'exec'),{'__name__':'__main__','__file__':str(base/'os_entry.py'),'NATIVE_ACCEPTED_AT':authority['issuedAt'],'NATIVE_PENDING':pending,'NATIVE_CONFIRMATION':authority})
if __name__=='__main__':
 try:
  result=main()
  if result is not None:print(json.dumps(result,ensure_ascii=False,sort_keys=True),flush=True)
 except Exception as e:
  code=getattr(e,'code','R12_ROOT_ENTRY_REFUSED_OR_UNKNOWN_RESULT');code=code if isinstance(code,str) and re.fullmatch('[A-Z0-9_]{1,100}',code) else 'R12_ROOT_ENTRY_REFUSED_OR_UNKNOWN_RESULT'
  print(json.dumps({'status':'REFUSED_OR_READBACK_REQUIRED','code':code,'automaticRetry':False,'businessAcceptance':False}),flush=True);raise SystemExit(78)
