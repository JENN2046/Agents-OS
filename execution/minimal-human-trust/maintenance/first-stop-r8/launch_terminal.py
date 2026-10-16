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
 if mode not in ('stop','status','recover-original'):raise SystemExit('Allowed: stop, status, recover-original')
 if not sys.stdin.isatty() or not sys.stdout.isatty():raise SystemExit('Run in your real desktop terminal; terminal input must remain with you.')
 if mode=='stop':
  source=Path(__file__).resolve().parent/'first-stop-capsule';raw=(source/'CAPSULE.json').read_bytes()
  if hashlib.sha256(raw).hexdigest()!=CAPSULE_SHA:raise SystemExit('Local capsule changed; no remote action.')
  manifest=json.loads(raw)
  for name,pin in manifest['files'].items():
   if '/' in name or name in ('.','..') or hashlib.sha256((source/name).read_bytes()).hexdigest()!=pin:raise SystemExit('Local sealed source changed; no remote action.')
 filename=('/home/ubuntu/r16-first-stop-r8-candidate' if mode=='stop' else '/usr/lib/r16-maintenance/first-stop-r8/'+CAPSULE_SHA)+'/bootstrap.py'
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
 loader='FILENAME='+repr(filename)+'\nALLOWED_UIDS='+repr((0,1000) if mode=='stop' else (0,))+'\nBOOT_PIN='+repr(BOOTSTRAP_SHA)+'\nCAP_PIN='+repr(CAPSULE_SHA)+'\nMODE='+repr(mode)+'\n'+loader
 remote=shlex.join(('/usr/bin/sudo','-k','--','/usr/bin/python3','-I','-B','-c',loader))
 print('云机首次停机入口：'+mode,flush=True)
 print('规则例外已批准；现场目标与 STOP / RESTORE_RUNNING / RESTORE_ORIGINAL 摘要仍由你核对。',flush=True)
 print('此入口不签发、不安装、不切换 Owner。停机成功后插件暂时不可用，重启保护保留。',flush=True)
 code=subprocess.run([*SSH,remote],check=False).returncode
 print('入口退出码：'+str(code)+'。以屏幕终态回执为准；不明结果不要重复杀进程。',flush=True)
 return code
if __name__=='__main__':raise SystemExit(main())
