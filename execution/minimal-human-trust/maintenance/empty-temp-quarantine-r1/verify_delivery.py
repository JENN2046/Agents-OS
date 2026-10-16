"""Offline byte verifier. Never imports or executes the sealed maintenance code."""
import hashlib,json,stat,sys
from pathlib import Path
EXPECTED_CAPSULE='@CAPSULE_SHA@'
EXPECTED_LAUNCHER='@LAUNCHER_SHA@'
ORIGINAL_R8='cfa55305623727e1b7607705c7b7a8eb76d2221250368828d21b7779da75af41'
POLICY='1ee6217b557dbce981211929201864bfbdde0b278e84b4081937354b09300a9c'
def sha(raw):return hashlib.sha256(raw).hexdigest()
def need(ok,code):
 if not ok:raise ValueError(code)
def read(path):
 s=path.lstat();need(stat.S_ISREG(s.st_mode) and s.st_nlink==1 and stat.S_IMODE(s.st_mode)==0o644,'PHYSICAL_FILE_TYPE_OR_MODE')
 raw=path.read_bytes();z=path.lstat()
 need((s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns)==(z.st_dev,z.st_ino,z.st_size,z.st_mtime_ns,z.st_ctime_ns),'PHYSICAL_FILE_CHANGED');return raw
def parse(raw):
 def unique(rows):
  result={}
  for k,v in rows:need(k not in result,'DUPLICATE_KEY');result[k]=v
  return result
 return json.loads(raw,object_pairs_hook=unique)
def verify(base):
 cap=base/'capsule';raw=read(cap/'CAPSULE.json');need(sha(raw)==EXPECTED_CAPSULE,'CAPSULE_PIN_DRIFT');m=parse(raw)
 old={'bootstrap.py','common_safe.py','native_entry.py','stop_driver.py','linux_backend.py','ledger_checkpoint.py','handoff.py','TARGET.json'}
 expected={'bootstrap.py','entry.py','backend.py','driver.py','r8/CAPSULE.json',*{'r8/'+p for p in old}}
 need(set(m)=={'schema','policyProposalSha256','sourceCapsuleHash','nativeExecutionAlreadyAuthorized','files'} and m['schema']=='r16.empty-temp-quarantine-capsule.v1' and m['nativeExecutionAlreadyAuthorized'] is False and m['policyProposalSha256']==POLICY and m['sourceCapsuleHash']==ORIGINAL_R8 and set(m['files'])==expected,'CAPSULE_SCOPE_DRIFT')
 actual=set();total=0
 for path in cap.rglob('*'):
  s=path.lstat();need(not stat.S_ISLNK(s.st_mode),'PHYSICAL_SYMLINK_REFUSED')
  if stat.S_ISDIR(s.st_mode):need(stat.S_IMODE(s.st_mode)==0o755,'PHYSICAL_DIRECTORY_MODE');continue
  name=path.relative_to(cap).as_posix();actual.add(name);value=read(path);total+=len(value)
  if name!='CAPSULE.json':need(sha(value)==m['files'].get(name),'PHYSICAL_MEMBER_HASH_DRIFT')
 need(actual==expected|{'CAPSULE.json'},'PHYSICAL_FILE_SET_DRIFT')
 original=read(cap/'r8/CAPSULE.json');need(sha(original)==ORIGINAL_R8,'ORIGINAL_R8_CAPSULE_DRIFT');source=parse(original)
 need(set(source['files'])==old,'ORIGINAL_R8_SET_DRIFT')
 for name,pin in source['files'].items():need(sha(read(cap/'r8'/name))==pin,'ORIGINAL_R8_MEMBER_DRIFT')
 need(sha(read(base/'RUN_IN_DESKTOP_TERMINAL.py'))==EXPECTED_LAUNCHER,'LAUNCHER_PIN_DRIFT')
 return {'status':'OFFLINE_SOURCE_BYTES_VERIFIED','capsuleHash':EXPECTED_CAPSULE,'sealedMembers':len(expected),'sourceBytesIncludingManifest':total,'unchangedR8Dependencies':True,'sealedCodeExecuted':False,'productionExecutionPerformed':False,'businessAcceptance':False}
if __name__=='__main__':
 try:print(json.dumps(verify(Path(__file__).resolve().parent),separators=(',',':')))
 except Exception:print(json.dumps({'status':'OFFLINE_SOURCE_VERIFICATION_FAILED','businessAcceptance':False}));sys.exit(78)
