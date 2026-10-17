#!/usr/bin/python3
"""Human R12 install wrapper. Describe/verify are local and nonprivileged."""
import hashlib,json,os,shlex,socket,stat,subprocess,sys
from pathlib import Path
CAPSULE=None
ENTRY_SHA=None
LOADER_SHA=None
ROOT_LOADER=None
SOURCE=Path('/home/jenn/AGENTS_OS_Workspace/ops/g1d-native-recovery-reconnect-20261014-r1/r15-backport/maintenance-recovered-r12')
LOCAL='jenn-System-Product-Name'
SSH=('/usr/bin/ssh','-F','/dev/null','-tt','-o','BatchMode=yes','-o','IdentityAgent=none','-o','IdentitiesOnly=yes','-i','/home/jenn/.ssh/TXY_159_75_139_246_ed25519','-o','StrictHostKeyChecking=yes','-o','UpdateHostKeys=no','-o','UserKnownHostsFile=/etc/r16-owner/ssh_known_hosts','-o','GlobalKnownHostsFile=/dev/null','-o','ConnectTimeout=8','-o','ClearAllForwardings=yes','ubuntu@159.75.139.246')
def need(v,c):
 if not v:raise ValueError(c)
def sha(raw):return hashlib.sha256(raw).hexdigest()
def sealed_loader():
 need(isinstance(CAPSULE,str) and len(CAPSULE)==64 and isinstance(ENTRY_SHA,str) and len(ENTRY_SHA)==64 and isinstance(ROOT_LOADER,str) and sha(ROOT_LOADER.encode())==LOADER_SHA,'R12_FINAL_REVIEWED_SEAL_REQUIRED');return ROOT_LOADER

def loader(phase,mode='apply'):
 need(phase in ('cloud','local') and mode in ('apply','preflight'),'R12_FIXED_PHASE_REQUIRED')
 return 'CAPSULE='+repr(CAPSULE)+'\nENTRY_SHA='+repr(ENTRY_SHA)+'\nPHASE='+repr(phase)+'\nMODE='+repr(mode)+'\n'+sealed_loader()

def verify_local():
 # Import only reviewed stdlib loader definitions; __main__ is never executed.
 raw=sealed_loader();namespace={'__name__':'r12_outer_verify'};exec(compile(raw,'<sealed-r12-readonly-verifier>','exec'),namespace)
 manifest,sources,budget=namespace['seal_candidate'](SOURCE,CAPSULE,ENTRY_SHA)
 return {'status':'R12_LOCAL_SEALED_SOURCE_AND_PACKAGE_PASS','capsuleHash':CAPSULE,'sourceFiles':len(sources),'packageFiles':len(manifest['payloadFiles']),'authorityCreated':False,'productionEffects':0,'businessAcceptance':False,'allocationEstimate':budget}
def description():return {'schema':'r16.r12.human-install-entry.v1','capsuleHash':CAPSULE,'targetReleaseId':'r16-daily-20261015-r15-app-recovery-r6','newNamespace':'recovery-r12','sourceDeliveryRevision':18,'forwardRevision':19,'rollbackRevision':20,'sourceAppBaseline':'STOPPED','localGracefulStopOrder':['r16-native.service','r16-bridge.service','r16-owner.service'],'successfulActivationOrder':['r16-owner.service','r16-bridge.service','r16-native.service','r16-app.service'],'rollbackAppCodePhase':'SOURCE','oldPlanRenewed':False,'previousR11CloudPreparation':'PRESERVED_HISTORY_ONLY_NOT_AUTHORITY','previousR11ApprovalReused':False,'adoptsOldStopFence':False,'assetReuse':'Exact read-only R9 protected package and complete unselected target, full byte/mode verification','cacheCleanup':False,'packageOrTargetCopy':False,'sameGrant':True,'ownerIdentityChanged':False,'unknownReplayedOrSettled':False,'businessAcceptance':False}
def main(argv=None):
 args=sys.argv[1:] if argv is None else argv
 need(args in ([],['--install'],['--describe'],['--verify']),'R12_FIXED_OPERATOR_ARGUMENTS_REQUIRED')
 print(json.dumps(description(),ensure_ascii=False,indent=2),flush=True)
 if args==['--describe']:return 0
 if args==['--verify']:print(json.dumps(verify_local(),ensure_ascii=False),flush=True);return 0
 need(os.getuid()==os.geteuid()==1000 and socket.gethostname()==LOCAL,'R12_ORDINARY_LOCAL_ADMIN_REQUIRED')
 need(sys.stdin.isatty() and sys.stdout.isatty() and sys.stderr.isatty(),'R12_REAL_FOREGROUND_DESKTOP_TTY_REQUIRED')
 print(json.dumps(verify_local(),ensure_ascii=False),flush=True)
 print('这是新的 R12 安装，不续旧计划，不接旧92/93/94/95。先纯说明，等本人 Enter 才进入认证。',flush=True)
 print('云端：sudo -k + 本人 APPLY CLOUD 完整待批摘要。完整复核并只读复用R9受保护包和未选择的目标文件；准备新R12维护源码、记录/helper，不清缓存、不再复制整包、不签发、不切换目标发行。',flush=True)
 print('本机：云端成功才 pkexec + 本人 APPLY LOCAL 完整待批摘要；先优雅停止仍运行的 Native、Bridge、Owner，完成既有Release/Issuer同Grant签发和双机安装后，按 Owner、Bridge、Native、目标App 顺序启动应运行角色。',flush=True)
 print('旧R11云端准备记录、根目录和原期限原样保留，仅作历史；不继承旧批准、准入或计划，不自动清理。',flush=True)
 print('当前真实签名配置18；新事务向前19，失败回退20；不重新使用旧APPLY或旧事务。',flush=True)
 print('原Owner、Grant、两笔UNKNOWN和历史账本保留；不结清或重放。失败恢复App保持 SOURCE STOPPED；安装不是业务验收。',flush=True)
 print('新5分钟引导/签发与最多30分钟恢复从本人准确确认接受后计算，且本机受云准入期限上限。不自动重试不明签发/安装。',flush=True)
 need(input('本人阅读后按 Enter 开始；其他输入取消：')=='','R12_HUMAN_START_CANCELLED')
 command=shlex.join(('/usr/bin/sudo','-k','--','/usr/bin/python3','-I','-B','-c',loader('cloud')))
 cloud=subprocess.run([*SSH,command],check=False).returncode
 print('云端入口退出码：'+str(cloud),flush=True)
 if cloud!=0:
  print('云端未成功，本机没有开始。请只读核查精确事务，不自动重试。',flush=True);return cloud
 local=subprocess.run(['/usr/bin/pkexec','/usr/bin/python3','-I','-B','-c',loader('local')],check=False).returncode
 print('本机入口退出码：'+str(local)+'。0须对应准确终态；75待恢复，78拒绝/未完成，均不代表业务验收。',flush=True);return local
if __name__=='__main__':
 interactive=sys.argv[1:] not in (['--describe'],['--verify']) and sys.stdin.isatty() and sys.stdout.isatty();code=78
 try:code=main()
 except KeyboardInterrupt:print('HUMAN_INTERRUPTED_UNKNOWN_EFFECT_DO_NOT_RETRY',flush=True);code=130
 except Exception as e:
  value=str(e);value=value if value.isascii() and len(value)<=100 and value.replace('_','').isalnum() else 'R12_OPERATOR_REFUSED_OR_READBACK_REQUIRED';print(value,flush=True)
 finally:
  if interactive:
   print('入口退出码 '+str(code)+'。保留回执，不明结果切勿重发。',flush=True)
   try:input('读完终态后按 Enter 关闭窗口：')
   except (EOFError,KeyboardInterrupt):pass
 raise SystemExit(code)
