"""Small bounded file primitives. No business ledger data is written here."""
import hashlib,json,os,stat
from pathlib import Path
class Refused(Exception):
 def __init__(self,code): self.code=code;super().__init__(code)
def need(value,code):
 if not value: raise Refused(code)
def canonical(value):
 def ordered(x):
  if isinstance(x,dict): return {k:ordered(x[k]) for k in sorted(x,key=lambda s:s.encode('utf-16-be','surrogatepass'))}
  if isinstance(x,list): return [ordered(v) for v in x]
  need(x is None or type(x) in (int,str,bool),'CANONICAL_VALUE_REFUSED')
  if type(x) is int: need(abs(x)<=9007199254740991,'CANONICAL_INTEGER_REFUSED')
  return x
 return json.dumps(ordered(value),ensure_ascii=False,separators=(',',':')).encode()
def digest(value): return hashlib.sha256(canonical(value)).hexdigest()
def sha(raw): return hashlib.sha256(raw).hexdigest()
def parse(raw):
 def pairs(rows):
  out={}
  for k,v in rows: need(k not in out,'DUPLICATE_JSON_KEY');out[k]=v
  return out
 def invalid(v): raise Refused('INVALID_JSON_CONSTANT')
 return json.loads(raw,object_pairs_hook=pairs,parse_constant=invalid)
def secure_read(path,uid=0,limit=16777216,source=False):
 path=Path(path);need(path.is_absolute(),'ABSOLUTE_PATH_REQUIRED');current=Path('/')
 for bit in path.parts[1:-1]:
  current/=bit;s=current.lstat();need(stat.S_ISDIR(s.st_mode) and s.st_uid in ((0,1000) if source else (0,)) and not s.st_mode&0o022,'UNSAFE_PARENT')
 fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
 try:
  a=os.fstat(fd);need(stat.S_ISREG(a.st_mode) and a.st_uid==uid and a.st_nlink==1 and not a.st_mode&0o022 and a.st_size<=limit,'UNSAFE_FILE')
  raw=b''
  while len(raw)<=limit:
   b=os.read(fd,min(65536,limit+1-len(raw)))
   if not b: break
   raw+=b
  z=os.fstat(fd);fields=lambda s:(s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns)
  need(len(raw)==a.st_size and fields(a)==fields(z),'FILE_CHANGED')
  return raw
 finally: os.close(fd)
def mkdir(path):
 current=Path('/')
 for bit in Path(path).parts[1:]:
  current/=bit
  try: current.mkdir(mode=0o700)
  except FileExistsError: pass
  s=current.lstat();need(stat.S_ISDIR(s.st_mode) and s.st_uid==0 and not s.st_mode&0o022,'UNSAFE_ROOT_DIRECTORY')
def sync(path):
 fd=os.open(path,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
 try: os.fsync(fd)
 finally: os.close(fd)
def immutable(path,raw,mode=0o600):
 path=Path(path);mkdir(path.parent)
 pending=path.with_name('.'+path.name+'.'+sha(raw)+'.pending')
 if path.exists() and pending.exists():
  a=path.lstat();b=pending.lstat()
  if (a.st_dev,a.st_ino)==(b.st_dev,b.st_ino):
   need(stat.S_ISREG(a.st_mode) and a.st_uid==0 and a.st_nlink==2 and stat.S_IMODE(a.st_mode)==mode,'UNSAFE_OWN_PENDING_LINK')
   fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
   try: need(os.read(fd,len(raw)+1)==raw,'IMMUTABLE_FILE_CONFLICT')
   finally: os.close(fd)
   pending.unlink();sync(path.parent)
 if path.exists():
  need(secure_read(path)==raw and stat.S_IMODE(path.lstat().st_mode)==mode,'IMMUTABLE_FILE_CONFLICT');return
 try: fd=os.open(pending,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,mode);at=0
 except FileExistsError:
  prefix=secure_read(pending);need(raw.startswith(prefix) and stat.S_IMODE(pending.lstat().st_mode)==mode,'IMMUTABLE_PENDING_CONFLICT')
  fd=os.open(pending,os.O_WRONLY|os.O_APPEND|os.O_NOFOLLOW);at=len(prefix)
 try:
  st=os.fstat(fd);need(stat.S_ISREG(st.st_mode) and st.st_uid==0 and st.st_nlink==1 and stat.S_IMODE(st.st_mode)==mode,'UNSAFE_PENDING_FILE')
  os.fchmod(fd,mode)
  while at<len(raw): at+=os.write(fd,raw[at:])
  os.fsync(fd)
 finally: os.close(fd)
 try: os.link(pending,path,follow_symlinks=False)
 except FileExistsError: need(secure_read(path)==raw,'IMMUTABLE_FILE_CONFLICT')
 pending.unlink();sync(path.parent)
