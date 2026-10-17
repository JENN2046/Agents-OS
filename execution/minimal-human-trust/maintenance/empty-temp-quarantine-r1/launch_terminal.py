#!/usr/bin/python3
"""Generated sealed launcher. Passwords and native confirmation stay in the TTY."""
import hashlib,json,os,shlex,subprocess,sys
from pathlib import Path
CAPSULE_SHA='@CAPSULE_SHA@'
BOOTSTRAP_SHA='@BOOTSTRAP_SHA@'
SSH=['/usr/bin/ssh','-F','/dev/null','-T','-o','BatchMode=yes','-o','IdentityAgent=none','-o','IdentitiesOnly=yes','-i','/home/jenn/.ssh/TXY_159_75_139_246_ed25519','-o','StrictHostKeyChecking=yes','-o','UpdateHostKeys=no','-o','UserKnownHostsFile=/etc/r16-owner/ssh_known_hosts','-o','GlobalKnownHostsFile=/dev/null','-o','ConnectTimeout=8','-o','ClearAllForwardings=yes','ubuntu@159.75.139.246']
def main():
 if len(sys.argv)>2 or any(len(x)!=64 or any(v not in '0123456789abcdef' for v in x) for x in (CAPSULE_SHA,BOOTSTRAP_SHA)):raise SystemExit('Reviewed physical launcher required.')
 mode=sys.argv[1] if len(sys.argv)==2 else 'preflight'
 if mode not in ('preflight','execute','status','recover'):raise SystemExit('Allowed: preflight, execute, status, recover')
 readonly=mode in ('preflight','status')
 if not readonly and (not sys.stdin.isatty() or not sys.stdout.isatty()):raise SystemExit('Run in your real desktop terminal; native input must remain with you.')
 if mode in ('preflight','execute'):
  local=Path(__file__).resolve().parent/'capsule';raw=(local/'CAPSULE.json').read_bytes()
  if hashlib.sha256(raw).hexdigest()!=CAPSULE_SHA:raise SystemExit('Local capsule changed; no remote action.')
  m=json.loads(raw)
  for name,pin in m['files'].items():
   if not name or name.startswith('/') or any(p in ('','.','..') for p in name.split('/')):raise SystemExit('Local capsule path refused.')
   p=local/name
   if p.is_symlink() or hashlib.sha256(p.read_bytes()).hexdigest()!=pin:raise SystemExit('Local sealed source changed; no remote action.')
 filename=('/home/ubuntu/r16-empty-temp-quarantine-r1-candidate' if mode in ('preflight','execute') else '/usr/lib/r16-maintenance/empty-temp-quarantine-r1/'+CAPSULE_SHA)+'/bootstrap.py'
 loader="""import hashlib,os,resource,stat,sys
from pathlib import Path
resource.setrlimit(resource.RLIMIT_CORE,(0,0))
p=Path(FILE);cur=Path('/')
for part in p.parts[1:-1]:
 cur/=part;s=cur.lstat()
 if not stat.S_ISDIR(s.st_mode) or s.st_uid not in OWNERS or s.st_mode&0o022:raise SystemExit('PINNED_PARENT_REFUSED')
fd=os.open(p,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
try:
 s=os.fstat(fd)
 if not stat.S_ISREG(s.st_mode) or s.st_uid not in OWNERS or s.st_nlink!=1 or s.st_mode&0o022 or s.st_size>1048576:raise SystemExit('PINNED_FILE_REFUSED')
 raw=b''
 while len(raw)<=1048576:
  b=os.read(fd,65536)
  if not b:break
  raw+=b
 z=os.fstat(fd);identity=lambda q:(q.st_dev,q.st_ino,q.st_size,q.st_mtime_ns,q.st_ctime_ns)
 if len(raw)!=s.st_size or identity(s)!=identity(z):raise SystemExit('PINNED_FILE_CHANGED')
finally:os.close(fd)
if hashlib.sha256(raw).hexdigest()!=BOOT:raise SystemExit('PINNED_BOOTSTRAP_CHANGED')
sys.argv=['bootstrap.py',MODE,CAP]
exec(compile(raw,str(p),'exec'),{'__name__':'__main__'})
"""
 loader='FILE='+repr(filename)+'\nOWNERS='+repr((0,1000) if mode in ('preflight','execute') else (0,))+'\nMODE='+repr(mode)+'\nCAP='+repr(CAPSULE_SHA)+'\nBOOT='+repr(BOOTSTRAP_SHA)+'\n'+loader
 sudo=('/usr/bin/sudo','-n','--') if readonly else ('/usr/bin/sudo','-k','--')
 remote=shlex.join((*sudo,'/usr/bin/python3','-I','-B','-c',loader));ssh=SSH if readonly else [('-tt' if v=='-T' else v) for v in SSH]
 print('云机准确空文件隔离入口：'+mode,flush=True)
 print('此入口不停止或重启进程，不签发、不安装发行版、不切换 Owner；旧账保持原样。',flush=True)
 if readonly:print('仅受保护只读，不安装辅助源码、不创建批准或 journal、不冻结、不收密码。',flush=True)
 else:print('管理员认证后，请核对完整现场对象，并亲自输入 QUARANTINE / RESTORE_EMPTY 对应摘要。',flush=True)
 code=subprocess.run([*ssh,remote],check=False).returncode
 print('入口退出码：'+str(code)+'。以终态回执为准；不明结果请保留窗口，勿手动删文件或重发搬移。',flush=True);return code
if __name__=='__main__':raise SystemExit(main())
