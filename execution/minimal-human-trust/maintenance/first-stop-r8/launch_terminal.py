#!/usr/bin/python3
"""Generated native terminal launcher. Never capture passwords or terminal input."""
import hashlib,json,os,shlex,stat,subprocess,sys
from pathlib import Path
CAPSULE_SHA='@CAPSULE_SHA@'
BOOTSTRAP_SHA='@BOOTSTRAP_SHA@'
SSH=['/usr/bin/ssh','-F','/dev/null','-tt','-o','BatchMode=yes','-o','IdentityAgent=none','-o','IdentitiesOnly=yes','-i','/home/jenn/.ssh/TXY_159_75_139_246_ed25519','-o','StrictHostKeyChecking=yes','-o','UpdateHostKeys=no','-o','UserKnownHostsFile=/etc/r16-owner/ssh_known_hosts','-o','GlobalKnownHostsFile=/dev/null','-o','ConnectTimeout=8','-o','ClearAllForwardings=yes','ubuntu@159.75.139.246']

def main():
 if len(sys.argv)>2 or any(len(x)!=64 or any(c not in '0123456789abcdef' for c in x) for x in (CAPSULE_SHA,BOOTSTRAP_SHA)):
  raise SystemExit('Reviewed physical delivery launcher required.')
 mode=sys.argv[1] if len(sys.argv)==2 else 'stop'
 if mode not in ('stop','status','recover-original','preflight'):raise SystemExit('Allowed: preflight, stop, status, recover-original')
 if mode!='preflight' and (not sys.stdin.isatty() or not sys.stdout.isatty()):raise SystemExit('Run in your real desktop terminal; terminal input must remain with you.')
 if mode in ('stop','preflight'):
  source=Path(__file__).resolve().parent/'first-stop-capsule';raw=(source/'CAPSULE.json').read_bytes()
  if hashlib.sha256(raw).hexdigest()!=CAPSULE_SHA:raise SystemExit('Local capsule changed; no remote action.')
  manifest=json.loads(raw)
  for name,pin in manifest['files'].items():
   if '/' in name or name in ('.','..') or hashlib.sha256((source/name).read_bytes()).hexdigest()!=pin:raise SystemExit('Local sealed source changed; no remote action.')
 filename=('/home/ubuntu/r16-first-stop-r8-candidate' if mode in ('stop','preflight') else '/usr/lib/r16-maintenance/first-stop-r8/'+CAPSULE_SHA)+'/bootstrap.py'
 # stdlib-only first loader; candidate Python never runs before its reviewed
 # digest and protected file metadata are checked. All arguments are fixed.
 loader="""import hashlib,os,pathlib,resource,stat,sys
resource.setrlimit(resource.RLIMIT_CORE,(0,0))
p=pathlib.Path(FILENAME)
c=pathlib.Path('/')
for part in p.parts[1:-1]:
 c/=part;s=c.lstat()
 if not stat.S_ISDIR(s.st_mode) or s.st_uid not in ALLOWED_UIDS or s.st_mode&0o022:raise SystemExit('PINNED_LOADER_PARENT_REFUSED')
fd=os.open(p,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
try:
 s=os.fstat(fd)
 if not stat.S_ISREG(s.st_mode) or s.st_uid not in ALLOWED_UIDS or s.st_nlink!=1 or s.st_mode&0o022 or s.st_size>1048576:raise SystemExit('PINNED_LOADER_FILE_REFUSED')
 raw=b''
 while len(raw)<=1048576:
  b=os.read(fd,65536)
  if not b:break
  raw+=b
 z=os.fstat(fd)
 if (s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns)!=(z.st_dev,z.st_ino,z.st_size,z.st_mtime_ns,z.st_ctime_ns) or len(raw)!=s.st_size:raise SystemExit('PINNED_LOADER_FILE_CHANGED')
finally:os.close(fd)
if hashlib.sha256(raw).hexdigest()!=BOOT_PIN:raise SystemExit('PINNED_LOADER_HASH_REFUSED')
sys.argv=['bootstrap.py',MODE,CAP_PIN]
exec(compile(raw,str(p),'exec'),{'__name__':'__main__'})
"""
 loader='FILENAME='+repr(filename)+'\nALLOWED_UIDS='+repr((0,1000) if mode in ('stop','preflight') else (0,))+'\nBOOT_PIN='+repr(BOOTSTRAP_SHA)+'\nCAP_PIN='+repr(CAPSULE_SHA)+'\nMODE='+repr(mode)+'\n'+loader
 sudo=('/usr/bin/sudo','-n','--') if mode=='preflight' else ('/usr/bin/sudo','-k','--')
 remote=shlex.join((*sudo,'/usr/bin/python3','-I','-B','-c',loader))
 print('云机首次停机入口：'+mode,flush=True)
 if mode=='preflight':
  print('仅受保护只读预检：不安装 root 源码、不写 journal/批准、不冻结、不发信号、不调用业务。',flush=True)
  print('只输出计数和摘要；PASS 不构成 STOP 授权，正式停机仍会重新核查并由你确认。',flush=True)
  print('预检使用 ssh -T + sudo -n；不交互、不收密码，也不会自动改为停机。',flush=True)
 else:
  print('规则例外已批准；现场目标与 STOP / RESTORE_RUNNING / RESTORE_ORIGINAL 摘要仍由你核对。',flush=True)
  print('此入口不签发、不安装、不切换 Owner。停机成功后插件暂时不可用，重启保护保留。',flush=True)
 ssh=[('-T' if arg=='-tt' else arg) for arg in SSH] if mode=='preflight' else SSH
 code=subprocess.run([*ssh,remote],check=False).returncode
 if mode=='preflight' and code==1:print('若只读管理员认证被 sudo -n 拒绝，请在你的云端终端自行完成 sudo -v 后重跑 preflight。',flush=True)
 print('入口退出码：'+str(code)+'。以屏幕终态回执为准；不明结果不要重复杀进程。',flush=True)
 return code
if __name__=='__main__':raise SystemExit(main())
