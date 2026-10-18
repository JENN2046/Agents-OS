"""Fixed foreground HostAdmin admission. Default describe is effect-free.
Only a human at a verified sudo/PTY may authorize the new maintenance plan.
"""
import importlib.util,json,os,resource,secrets,socket,subprocess,sys,time
from pathlib import Path
from common import *
import native_guard
_BRAND=object()
def boot_id():return Path('/proc/sys/kernel/random/boot_id').read_text().strip()
class Authority:
 def __init__(self,brand,plan,record,host,clock=now,mono=time.monotonic_ns):
  need(brand is _BRAND,'NATIVE_AUTHORITY_REQUIRED');self.plan=plan;self.record=record;self.host=host;self.clock=clock;self.mono=mono
  self.plan_hash=digest(plan);self.approval_hash=digest(record);self.original_baseline=record['pending'].get('originalBaseline',{})
 def require(self,plan_hash,operation,target=None):
  need(operation in {'bind','observe','inspect','checkpoint','history-collect'},'READONLY_SOURCE_NATIVE_EFFECTS_DISABLED')
  root(self.host);need(plan_hash==self.plan_hash,'AUTHORITY_PLAN_DRIFT')
  roles={'r16-native.service','r16-owner.service','r16-native-link.service','r16-app.service','r16-bridge.service'}
  base,sep,unit=operation.partition(':')
  if sep:need(base in('fence','graceful','restore','activate','requiesce')and unit in roles,'AUTHORITY_FIXED_ROLE_OPERATION')
  else:need(operation in {'bind','observe','checkpoint','inspect','history-collect','open-native-pidfd','native-freeze','native-signal','thaw-native','daemon-reload','os-write','journal-lock','journal-write','journal','rpc','stage','sign','commit','submit'},'AUTHORITY_OPERATION_REFUSED')
  if target is not None:
   if type(target)is dict and set(target)=={'unit'}:need(target['unit']in roles and(self.host==LOCAL or target['unit']in('r16-app.service','r16-bridge.service')),'AUTHORITY_ROLE_DRIFT')
   else:need(digest(target)==self.plan['nativeTargetHash'],'AUTHORITY_TARGET_DRIFT')
  # Read-only observations and append-only audit remain inside the original
  # recovery deadline. This never extends OS forward, key or publication use.
  recovery=operation in {'bind','observe','inspect','checkpoint','history-collect','journal','journal-lock','journal-write','rpc'}
  if base=='restore':
   need(unit not in('r16-native.service','r16-app.service'),'CRASHED_NATIVE_OR_BUSINESS_APP_REOPEN_REFUSED')
   baseline=self.original_baseline.get(unit);need(baseline is not None and baseline.get('active')=='active'and baseline.get('mainPid',baseline.get('pid',0))>0,'ORIGINAL_RESTORE_ROLE_NOT_ACTIVE');recovery=True
  if base=='requiesce':
   try:activation=parse(read(STATE/'lifecycle'/('activate-'+unit+'.json'),mode=0o600))
   except FileNotFoundError:
    need(target=={'unit':unit},'ACTUAL_ACTIVATION_INTENT_REQUIRED');activation=None
   if activation is not None:need(activation.get('planHash')==self.plan_hash and activation.get('scope')=='activate:'+unit and activation.get('state')in('INTENT','RETURNED'),'ACTUAL_ACTIVATION_INTENT_REQUIRED')
   recovery=True
  r=self.record;need(r['bootId']==boot_id(),'NATIVE_BOOT_CHANGED')
  end=self.plan['recoveryDeadline']if recovery else self.plan['expiresAt'];elapsed=self.mono()-int(r['acceptedMonotonicNs'])
  need(self.plan['approvedAt']<=self.clock()<end and 0<=elapsed<(end-r['acceptedAt'])*1000000,'NATIVE_WINDOW_EXPIRED')
 def __getstate__(self):raise Refused('AUTHORITY_NOT_SERIALIZABLE')
def load_adapter(manifest,authority,host):
 # Full closure was sealed before loading any backend, no caller path/module.
 import importlib
 module=importlib.import_module('orchestration')
 return module.EntryAdapter(authority,manifest,host)

def identity(host):
 # Normalize tuple metadata to JSON, never read argv/environ/passwords.
 return json.loads(json.dumps(native_guard.native_root_context(host)))
def native_confirm(pending,host,clock=now,mono=time.monotonic_ns):
 actor=identity(host);challenge={**pending,'nativeHostAdmin':actor};h=digest(challenge)
 fd=os.open('/dev/tty',os.O_RDWR|os.O_NOFOLLOW|os.O_CLOEXEC)
 try:
  need(os.isatty(fd)and os.tcgetpgrp(fd)==os.getpgrp(),'NATIVE_FOREGROUND_REQUIRED')
  word='AUTHORIZE CLOUD 'if host==CLOUD else 'MAINTAIN SOURCE19 '
  expected=(word+h).encode()
  effects=('云端本次准确授权将停止/围栏本机App和Bridge、保全原账与历史签名、stage并接受同计划的新配置；恢复仅按已批准原基线，不允许自动重开业务。\n'if host==CLOUD else'本机本次准确授权将停止/围栏Owner/relay/Native；仅准确旧Native在优雅失败后可冻结及一次pidfd SIGKILL，随后同计划签发/选择新Native。\n')
  text=('\nHOST_ADMIN_CUSTODY / TRUSTED_HOST_ADMIN 准确维护对象\n'+json.dumps(challenge,ensure_ascii=False,indent=2)+'\n'+effects+'这不是排空证明。旧 Native 可能被一次受控中止；已接收的上游工作仍可能继续。原 UNKNOWN 不结清、不重派。\n本机阶段将按同计划停止/围栏五角色，使用原 Release/Issuer 受保护密钥签新 Native 维护发行及明确的新修订，并双机接受/选择；不是 R17、不是新 Owner/Crown。\n失败保持旧 Native 停止，不自动重开业务 App。不明结果不重发。\n接受后才开始本次5分钟效果窗口/最多30分钟恢复，不延长任何旧计划。\n请本人输入完整一行：'+expected.decode()+'\n> ').encode()
  at=0
  while at<len(text):at+=os.write(fd,text[at:])
  line=b''
  while len(line)<=256:
   b=os.read(fd,1)
   need(b!=b'','NATIVE_CONFIRMATION_EOF_CANCELLED')
   if b in(b'\n',b'\r'):break
   line+=b
  need(line==expected,'NATIVE_CONFIRMATION_CANCELLED');need(identity(host)==actor,'NATIVE_ACTOR_CHANGED')
  return {'schema':'r16.source19-native-transition.native-acceptance.v1','pendingHash':h,'pending':challenge,'acceptedAt':clock(),'acceptedMonotonicNs':str(mono()),'bootId':boot_id(),'authorityType':'TRUSTED_HOST_ADMIN_NATIVE_MAINTENANCE','humanIdentityConfirmed':False}
 finally:os.close(fd)
def plan_from_acceptance(template,fields,acceptance,cloud_deadline):
 # B/proof/artifacts are not in this pre-stop plan. All content and targets are.
 need(not({'approvedAt','expiresAt','recoveryDeadline','checkpointHash','artifactsHash','stoppedProof'}&set(template)),'PRESTOP_TEMPLATE_CYCLE_OR_TIME')
 need(set(fields)=={'originalBaselineHash','nativeTargetHash','approvedControlUnknownHash','approvedControlUnknownCount','revisionPlanHash'},'PREPARED_FIELDS_REQUIRED')
 start=acceptance['acceptedAt'];end=min(start+300000,cloud_deadline);recovery=min(start+1800000,cloud_deadline)
 need(start<end<=recovery,'CLOUD_ADMISSION_EXPIRED')
 return {**template,**fields,'nonce':acceptance['pending']['nonce'],'stopEpoch':acceptance['pending']['stopEpoch'],'approvedAt':start,'expiresAt':end,'recoveryDeadline':recovery}
def command(args,timeout=30,input=None):
 try:r=subprocess.run(args,input=input,stdin=None if input is not None else subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,timeout=timeout,check=False,env={'PATH':'/usr/bin:/bin','LANG':'C','LC_ALL':'C'})
 except subprocess.TimeoutExpired:raise Refused('FIXED_EFFECT_REPLY_UNKNOWN_NO_AUTOMATIC_RETRY')
 need(len(r.stdout)<=4*1024*1024,'FIXED_REPLY_TOO_LARGE');need(r.returncode==0,'FIXED_COMMAND_FAILED_NO_AUTOMATIC_RETRY');return r.stdout

def validate_acceptance(record,host,manifest):
 need(type(record)is dict and record.get('schema')=='r16.source19-native-transition.native-acceptance.v1'and record.get('authorityType')=='TRUSTED_HOST_ADMIN_NATIVE_MAINTENANCE'and record.get('humanIdentityConfirmed')is False,'PROTECTED_NATIVE_ACCEPTANCE_REQUIRED')
 pending=record.get('pending');need(type(pending)is dict and record.get('pendingHash')==digest(pending)and pending.get('host')==host and pending.get('planTemplate')==manifest['planTemplate'],'NATIVE_PENDING_BINDING_DRIFT')
 need(type(record.get('acceptedAt'))is int and type(record.get('acceptedMonotonicNs'))is str and record['acceptedMonotonicNs'].isdigit()and record.get('bootId')==boot_id(),'NATIVE_ACCEPTANCE_CLOCK_OR_BOOT')
 need(digest(pending.get('originalBaseline'))==(pending.get('originalBaselineHash')if host==CLOUD else pending.get('planFields',{}).get('originalBaselineHash')),'NATIVE_ORIGINAL_BASELINE_BINDING')
 return None

def assert_capability(value,plan_hash=None,operation=None,target=None):
 need(type(value)is Authority and value.record.get('schema')=='r16.source19-native-transition.native-acceptance.v1','BRANDED_NATIVE_AUTHORITY_REQUIRED')
 if plan_hash is not None:value.require(plan_hash,operation or'inspect',target)
 return None

def describe():return {'schema':'r16.source19-native-transition.entry-description.v1','sourcePublicConfigHash':SOURCE,'sourceDeliveryHash':DELIVERY,'targetReleaseId':TARGET,'unit':UNIT,'productionEffects':0,'rootInstalled':False,'mode':MODE,'executionReady':False,'scope':'PROTECTED_READONLY_PREFLIGHT_SOURCE_ONLY','authorityType':'TRUSTED_HOST_ADMIN_NATIVE_MAINTENANCE','humanIdentityConfirmed':False,'globalExecution':'UNPROVEN','businessAcceptance':False}
def main(argv=None):
 args=sys.argv[1:]if argv is None else argv
 if args in([],['--describe']):return describe()
 need(len(args)==2 and args[0]in('preflight','prepare-cloud','approve-local','status'),'FIXED_FOREGROUND_ARGUMENTS')
 host=root();resource.setrlimit(resource.RLIMIT_CORE,(0,0));os.umask(0o077);capsule=args[1];manifest=verify_capsule(capsule)
 need(args[0]in('preflight','status'),'READONLY_SOURCE_NATIVE_EFFECTS_DISABLED')
 if args[0]=='status':
  try:value=parse(read(STATE/'entry-result.json',mode=0o600))
  except FileNotFoundError:return {'status':'NO_ENTRY_RESULT','automaticRetry':False}
  return {'status':value['status'],'planHash':value['planHash'],'historicalReadOnly':True,'businessAcceptance':False}
 if args[0]not in('preflight','status'):
  need(not(STATE/'entry-acceptance.json').exists()and not(STATE/'cloud-admission.json').exists()and not(STATE/'service-start-intent.json').exists(),'EXISTING_ADMISSION_STATUS_ONLY_NO_AUTOMATIC_RETRY')
 adapter=load_adapter(manifest,None,host);prepared=adapter.prepare()
 if host==CLOUD:
  need(type(prepared)is dict and prepared.get('schema')=='r16.source19-native-transition.cloud-preparation.v1'and set(prepared.get('originalBaseline',{}))=={'r16-app.service','r16-bridge.service'}and ishash(prepared.get('factsHash')),'CLOUD_TWO_ROLE_PREPARATION_REQUIRED')
 else:
  need(type(prepared)is dict and set(prepared)=={'planFields','factsHash','revisionInventory','revisionPlan','originalBaseline','historyInput'},'FIXED_PREPARATION_SCHEMA')
  need(ishash(prepared['factsHash'])and digest(prepared['originalBaseline'])==prepared['planFields']['originalBaselineHash'],'REAL_BASELINE_REQUIRED')
 if args[0]=='preflight':return {**({'revisionInventory':prepared['revisionInventory'],'revisionPlan':prepared['revisionPlan']}if host==LOCAL else{}),'status':'READONLY_PREFLIGHT_PASS','host':host,'capsuleHash':capsule,'factsHash':prepared['factsHash'],'originalBaselineHash':digest(prepared['originalBaseline']),'productionEffects':0,'nativeIntentCreated':False,'executionReady':False,'revisionAllocation':'BLOCKED_UNSIGNED_REQUEST_NOT_ALLOCATED'}
 raise Refused('READONLY_SOURCE_NATIVE_EFFECTS_DISABLED')
if __name__=='__main__':
 try:
  result=main();print(json.dumps(result,separators=(',',':')));raise SystemExit(75 if result.get('status')=='SERVICE_START_SUBMITTED_NOT_COMPLETED'else 0)
 except (Exception,KeyboardInterrupt)as e:
  c=getattr(e,'code',str(e));c=c if type(c)is str and re.fullmatch('[A-Z0-9_]{1,100}',c)else'FOREGROUND_REFUSED_OR_READBACK_REQUIRED';print(json.dumps({'status':'REFUSED_OR_READBACK_REQUIRED','code':c,'automaticRetry':False,'businessAcceptance':False}));raise SystemExit(78)
