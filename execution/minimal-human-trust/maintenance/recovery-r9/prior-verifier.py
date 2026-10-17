"""Read-only provenance for a NEW ordinary stopped-source maintenance plan.

The old compensation is historical evidence. Its expired authority never admits
the new installer. No old entrypoint, journal reader or mutator is invoked.
"""
import hashlib,json,os,socket,stat,subprocess,sys,types
from pathlib import Path
PROVENANCE={
 'schema':'r16.recovered-source-provenance.v1',
 'originalPlanHash':'45b7880b1f95cedba470e1c7d97f1656f4c77784d1c4b260861b7609d11d1c24',
 'originalCapsuleHash':'e7c8dbe016c2a36f0a1929ab52d5d0ad19ca7217c505f6c138cc64f32c595dad',
 'originalRollbackDeadline':1792175013109,
 'compensationCompletionHash':'2ed7c5d22c2a854c7f47310d49fe3c5a093300ba34fdf6826a79f3e786fe0f6d',
 'compensationRelationHash':'462298d6b03e14d4c2bc9da6e7d8b6c4861886b6eb78a8741d96ca48f7ea5e3b',
 'cloudProofHash':'6e6ed5742c4caea3090c3d298b9e5f419723ce5120810044cc5f3e698fd4d55c',
 'originalStopApprovalHash':'d26ce58948f4a09fb7aa2442458ee2028ea68a85fe687cfde206816899bf558f',
 'originalCheckpointDigest':'36bccee6812eb1c04d198868a572d049a8b4433d4d66332df12b30f1e7212a2c',
 'historicalSourceStopForceUsed':True,'drainStatus':'UNPROVEN',
 'sourceAppBaseline':'STOPPED','oldPlanRenewed':False,'businessAcceptance':False}
PINS={'prior-compensation.py':'abf23a3859136d789a2e3239a8c6e5205c3a7c34b33e2faad97c9aa4222e4253',
 'prior-native-guard.py':'21ebbb865bbd84d22aa2aa9160353c9e4ad26672edc1fa0b51a37709e8b6a51b',
 'prior-evidence.json':'057d698d69297a014357dfb0d630af59c0960ac1ad82512e06dbb5b27a605518'}
REMOTE_PROOF_READER=r'''import os,stat,sys
from pathlib import Path
p=Path('/run/r16-abort-compensation-r1/45b7880b1f95cedba470e1c7d97f1656f4c77784d1c4b260861b7609d11d1c24/cloud-proof.json')
cur=Path('/')
for name in p.parts[1:-1]:
 cur/=name;s=cur.lstat()
 if not stat.S_ISDIR(s.st_mode) or s.st_uid!=0 or s.st_mode&0o022:raise SystemExit(78)
fd=os.open(p,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
try:
 a=os.fstat(fd)
 if not stat.S_ISREG(a.st_mode) or a.st_uid!=0 or stat.S_IMODE(a.st_mode)!=0o644 or a.st_nlink!=1 or a.st_size>65536:raise SystemExit(78)
 raw=b''
 while len(raw)<=65536:
  block=os.read(fd,min(65536,65537-len(raw)))
  if not block:break
  raw+=block
 stamp=lambda s:(s.st_dev,s.st_ino,s.st_mode,s.st_uid,s.st_gid,s.st_nlink,s.st_size,s.st_mtime_ns,s.st_ctime_ns)
 if len(raw)!=a.st_size or stamp(a)!=stamp(os.fstat(fd)) or stamp(a)!=stamp(p.lstat()):raise SystemExit(78)
 sys.stdout.buffer.write(raw)
finally:os.close(fd)
'''
def verify_prior(manifest,sources):
 def need(v,c):
  if not v:raise ValueError(c)
 need(os.getuid()==os.geteuid()==0,'PRIOR_READBACK_ROOT_REQUIRED')
 need(manifest.get('planTemplate',{}).get('sourceRecoveryEvidence')==PROVENANCE,'PRIOR_PLAN_IDENTITY_DRIFT')
 for name,pin in PINS.items():need(type(sources.get(name)) is bytes and hashlib.sha256(sources[name]).hexdigest()==pin,'PRIOR_READER_INPUT_DRIFT')
 name='r9_readonly_prior_compensation';need(name not in sys.modules,'PRIOR_MODULE_COLLISION')
 module=types.ModuleType(name);module.__file__='<sealed-prior-compensation>';sys.modules[name]=module
 try:
  exec(compile(sources['prior-compensation.py'],module.__file__,'exec'),module.__dict__)
  prior={'compensation.py':sources['prior-compensation.py'],'native_guard.py':sources['prior-native-guard.py'],'LOCAL_EVIDENCE.json':sources['prior-evidence.json']}
  b=module.FixedBackend(socket.gethostname(),module.parse(prior['LOCAL_EVIDENCE.json']),prior)
  facts=b.cloud_facts(fenced=False) if b.host==module.CLOUD else b.local_facts()
  if b.host==module.CLOUD:
   proof=module.parse(b.read(module.PUBLIC,65536,0o644)[0]);a=proof['newAuthority'];native=module.parse(b.record('native-'+a['nonce']+'.json'))
   need(native['authority']==a,'PRIOR_NATIVE_AUTHORITY_DRIFT');module.check_authority(a,native['challenge'],proof['capturedAt'])
   need(module.digest(proof)==PROVENANCE['cloudProofHash'] and facts['checkpointDigest']==PROVENANCE['originalCheckpointDigest'],'PRIOR_CLOUD_OR_CHECKPOINT_DRIFT')
   operation=module.parse(b.record('operation.json'));need(operation['phase']=='CLOUD_VERIFIED' and operation['before']['oldHashes']==facts['oldHashes'],'PRIOR_COMPENSATION_NOT_CLOSED')
   module.validate_cloud_proof(proof,b.scope_hash,proof['capturedAt'])
  else:
   receipt=module.parse(b.record('completion.json'));relation=module.parse(b.record(receipt['relationFile']))
   need(module.digest(receipt)==PROVENANCE['compensationCompletionHash'] and module.digest(relation)==PROVENANCE['compensationRelationHash'] and relation==module.relation_for(receipt),'PRIOR_COMPLETION_PAIR_DRIFT')
   nonce=receipt['relationFile'].removeprefix('relation-').removesuffix('.json');native=module.parse(b.record('native-'+nonce+'.json'))
   module.check_authority(native['authority'],native['challenge'],receipt['completedAt'])
   need(module.digest(native['authority'])==receipt['localAuthorityHash'],'PRIOR_LOCAL_AUTHORITY_DRIFT')
   import shlex
   result=subprocess.run((*module.SSH,shlex.join(('/usr/bin/python3','-I','-B','-c',REMOTE_PROOF_READER))),stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,timeout=20,check=False)
   need(result.returncode==0 and len(result.stdout)<=65536,'PRIOR_CLOUD_RECORD_READBACK_REFUSED');proof=module.parse(result.stdout)
   need(module.digest(proof)==receipt['cloudProofHash']==PROVENANCE['cloudProofHash'] and module.digest(proof['newAuthority'])==receipt['cloudAuthorityHash'],'PRIOR_CROSS_HOST_LINK_DRIFT')
   module.validate_cloud_proof(proof,b.scope_hash,receipt['completedAt'])
  return {'schema':'r16.r9.source-recovery-readback.v1','host':b.host,'factsHash':module.digest(facts),'sourceRecoveryEvidence':PROVENANCE,'sourceAppExpectedState':'STOPPED','businessAcceptance':False}
 finally:sys.modules.pop(name,None)
