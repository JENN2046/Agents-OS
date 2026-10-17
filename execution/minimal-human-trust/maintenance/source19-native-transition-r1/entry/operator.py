#!/usr/bin/python3
"""Ordinary HostAdmin foreground wrapper. No auto approval/password capture."""
import json,os,shlex,socket,subprocess,sys
LOCAL='jenn-System-Product-Name'
BOOTSTRAP='/usr/lib/r16-maintenance/source19-native-transition-r1/runtime/maintenance/source19-native-transition-r1/entry/bootstrap.py'
SSH=('/usr/bin/ssh','-F','/dev/null','-tt','-o','BatchMode=yes','-o','IdentityAgent=none','-o','IdentitiesOnly=yes','-i','/home/jenn/.ssh/TXY_159_75_139_246_ed25519','-o','StrictHostKeyChecking=yes','-o','UpdateHostKeys=no','-o','UserKnownHostsFile=/etc/r16-owner/ssh_known_hosts','-o','GlobalKnownHostsFile=/dev/null','-o','ConnectTimeout=8','-o','ClearAllForwardings=yes','ubuntu@159.75.139.246')
def need(v,c):
 if not v:raise ValueError(c)
def main(argv=None):
 args=sys.argv[1:]if argv is None else argv
 need(args in([],['--describe'],['--run'],['--preflight']),'FIXED_OPERATOR_ARGUMENTS')
 description={'schema':'r16.source19-native-transition.human-entry.v1','mode':'DESCRIBE_ONLY'if args!=['--preflight']else'PROTECTED_READONLY_REQUEST','sourceRevision':19,'revisionPolicy':'EXPLICIT_FRESH_INVENTORY_NO20_REPLAN21_22','targetReleaseId':'r16-daily-20261017-source19-native-lifecycle-r1','requiredProtectedCodeInstall':'SEPARATE_NATIVE_APPROVAL_NOT_PERFORMED_BY_WRAPPER','sameOwnerGrant':True,'nativeEffects':'HARD_REFUSED_READONLY_SOURCE_MODE','globalExecution':'UNPROVEN','productionEffects':0,'humanIdentityConfirmed':False,'executionReady':False,'entryMode':'READONLY_PREFLIGHT_SOURCE','automaticRetry':False,'businessAcceptance':False}
 print(json.dumps(description,ensure_ascii=False,indent=2),flush=True)
 need(args!=['--run'],'READONLY_SOURCE_NATIVE_EFFECTS_DISABLED')
 if args!=['--preflight']:return 0
 need(os.getuid()==os.geteuid()==1000 and socket.gethostname()==LOCAL,'ORDINARY_FIXED_HOST_ADMIN_LAUNCHER_REQUIRED')
 need(all(os.isatty(fd)for fd in(0,1,2)),'REAL_FOREGROUND_TTY_REQUIRED')
 print('先本人阅读，再 Enter。此入口不会安装受保护代码；两机代码必须已由另一次准确准入安装。',flush=True)
 print('云/本机分别 fresh sudo -k，只核已保护代码及真实Source19公开配置/完整历史准入依据，仅读受保护状态并输出有界摘要；不产生Native批准、围栏、信号、签名或安装。',flush=True)
 print('只读预检不加载/解封Release、Issuer或角色签发私钥；沿既有SSH认证只读核查，不操作服务。缺实际完整库存/历史或安全恢复合同就BLOCK；不存在可执行维护入口。',flush=True)
 print('本次没有维护授权窗口；不创建/续期任何计划。全量只读核查可能需要几分钟，不要重试或关闭窗口。',flush=True)
 need(input('本人按 Enter 开始；其他内容取消：')=='','HUMAN_START_CANCELLED')
 # A fixed ordinary Python launcher remains the outer ancestor on cloud too;
 # the kernel sudo/PTY guard must not be bypassed with env/process-name claims.
 remote='import subprocess;raise SystemExit(subprocess.run('+repr(['/usr/bin/sudo','-k','--','/usr/bin/python3','-I','-B',BOOTSTRAP,'foreground','preflight'])+',check=False).returncode)'
 command=shlex.join(['/usr/bin/python3','-I','-B','-c',remote])
 cloud=subprocess.run([*SSH,command],check=False).returncode
 print('云端退出码 '+str(cloud),flush=True)
 if cloud!=0:return cloud
 local=subprocess.run(['/usr/bin/sudo','-k','--','/usr/bin/python3','-I','-B',BOOTSTRAP,'foreground','preflight'],check=False).returncode
 print('本机退出码 '+str(local)+'；75仅已提交/待恢复，78拒绝或未知。须读真实终态回执，不可重发。',flush=True);return local
if __name__=='__main__':
 code=78;hold=sys.argv[1:]==['--preflight']and sys.stdin.isatty()
 try:code=main()
 except(EOFError,KeyboardInterrupt):print('HUMAN_CANCELLED_OR_UNKNOWN_RESULT_NO_AUTOMATIC_RETRY',flush=True)
 except Exception as e:
  value=str(e);print(value if value.isascii()and value.replace('_','').isalnum()and len(value)<=100 else'OPERATOR_REFUSED_OR_UNKNOWN_RESULT',flush=True)
 finally:
  if hold:
   print('退出码 '+str(code),flush=True)
   try:input('读完退出状态后按 Enter 关闭：')
   except(EOFError,KeyboardInterrupt):pass
 raise SystemExit(code)
