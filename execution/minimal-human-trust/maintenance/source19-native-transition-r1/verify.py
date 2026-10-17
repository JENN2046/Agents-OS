#!/usr/bin/python3
"""Independent read-only byte verifier; never imports the builder/runtime."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess

SOURCE = 'r16-daily-20261015-r15-app-recovery-r6'
TARGET = 'r16-daily-20261017-source19-native-lifecycle-r1'
VERSIONS = {'app':'34731b300ccad9a1fbfd45b07422d847e8989d7e9dc052b0dda939cd99adb500',
 'bridge':'9c58c33478388003fd52da0cb15736ec951a9bfc9cf29738e20de5d741921352',
 'native':'2516e881b0622b3ac2d53c454e6ccf9950441c5cb3c26a53500b45d3b1dbe7b4'}
PUBLIC = '56e1df18a54950ea346a51654e61df60afe33cb9928ae77293b2cf336fd8a5ec'
OVERLAYS = {'host/workspace-dispatcher.mjs','host/native-runner.mjs','host/headless-host.mjs',
 'native/upstream/VCPDistributedServer/Plugin/ProjectForge/ProjectForgeService.js',
 'native/upstream/VCPDistributedServer/Plugin/ProjectForge/indexerClient.js'}
META = {'UNSIGNED_MAINTENANCE.json','PAYLOAD_INVENTORY.json','LOCAL_FILE_BINDINGS.json',
 'PROVENANCE.json','SOURCE_PUBLIC_CONFIG.json','SOURCE_ROLE_MANIFESTS.json',
 'app-manifest.json','bridge-manifest.json','native-manifest.json','SHA256SUMS.txt'}

def need(ok, code):
 if not ok: raise ValueError(code)
def sha(b): return hashlib.sha256(b).hexdigest()
def canon(v):
 if isinstance(v,dict): return '{'+','.join(canon(k)+':'+canon(v[k]) for k in sorted(v,key=lambda x:x.encode('utf-16-be')))+'}'
 if isinstance(v,list): return '['+','.join(canon(x) for x in v)+']'
 need(v is None or type(v) in (str,bool,int),'CANONICAL_TYPE')
 return json.dumps(v,ensure_ascii=False,separators=(',',':'))
def digest(v): return sha(canon(v).encode())
def parse(b):
 def pairs(rows):
  out={}
  for k,v in rows:
   need(k not in out,'DUPLICATE_KEY');out[k]=v
  return out
 return json.loads(b,object_pairs_hook=pairs)
def safe(n):
 need(isinstance(n,str) and n and not n.startswith('/') and '\\' not in n and all(x not in ('','.','..') for x in n.split('/')) and all(ord(c)>=32 and ord(c)!=127 for c in n),'PATH')
 return n
def stamp(s): return (s.st_dev,s.st_ino,s.st_uid,s.st_gid,s.st_mode,s.st_nlink,s.st_size,s.st_mtime_ns,s.st_ctime_ns)
def read(p):
 p=Path(p);need(not any(x.is_symlink() for x in (p,*p.parents)),'LINK')
 fd=os.open(p,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
 try:
  s=os.fstat(fd);need(stat.S_ISREG(s.st_mode) and s.st_nlink==1 and s.st_size<=128*1024*1024,'FILE')
  with os.fdopen(fd,'rb',closefd=False) as f: raw=f.read(128*1024*1024+1)
  need(len(raw)==s.st_size and stamp(s)==stamp(os.fstat(fd))==stamp(p.lstat()),'READ_CHANGED')
  return raw,stat.S_IMODE(s.st_mode)
 finally: os.close(fd)
def tree(root,expected):
 files=set();dirs=set()
 for r,children,names in os.walk(root,followlinks=False,onerror=lambda e:(_ for _ in ()).throw(e)):
  p=Path(r);s=p.lstat();need(stat.S_ISDIR(s.st_mode) and not p.is_symlink() and stat.S_IMODE(s.st_mode)==0o755,'DIRECTORY')
  dirs.add(str(p.relative_to(root)))
  for n in children: need(not (p/n).is_symlink(),'DIRECTORY_LINK')
  for n in names:
   q=p/n;s=q.lstat();need(stat.S_ISREG(s.st_mode) and s.st_nlink==1,'SPECIAL_OR_HARDLINK');files.add(str(q.relative_to(root)))
 need(files==expected and dirs=={'.'}|{str(p) for n in expected for p in Path(n).parents},'EXACT_TREE')
def git(repo,*args): return subprocess.check_output(['/usr/bin/git','-c','core.hooksPath=/dev/null','-C',str(repo),*args],stderr=subprocess.DEVNULL)

def verify(package,repo,base,head,inventory_sha):
 need(all(p.is_absolute() for p in (package,repo,base)),'ABSOLUTE_PATHS')
 need(git(repo,'rev-parse','HEAD').decode().strip()==head and git(repo,'status','--porcelain=v1')==b'','CLEAN_EXACT_HEAD')
 metadata={n:read(package/'metadata'/n)[0] for n in META}
 need(all(read(package/'metadata'/n)[1]==0o644 for n in META),'METADATA_MODE')
 need(sha(metadata['PAYLOAD_INVENTORY.json'])==inventory_sha,'EXTERNAL_INVENTORY_PIN')
 docs={n:parse(b) for n,b in metadata.items() if n.endswith('.json')}
 inv=docs['PAYLOAD_INVENTORY.json'];scope=docs['UNSIGNED_MAINTENANCE.json'];pub=docs['SOURCE_PUBLIC_CONFIG.json']
 need(inv['sourceHead']==scope['sourceHead']==head and digest(pub)==PUBLIC,'SOURCE_PIN')
 need(scope['status']=='UNSIGNED_ISOLATED_NOT_ACTIVATED' and scope['sourceConfigurationRevision']==19 and scope['sourceReleaseId']==SOURCE and scope['targetReleaseId']==TARGET,'UNSIGNED_SCOPE')
 need(all(scope[k] is None for k in ('configurationRevision','forwardRevision','rollbackRevision','releaseEnvelope','grantEnvelope','signedAt','installedAt','activatedAt')),'NO_AUTHORITY')
 need(all(scope[k] is False for k in ('maySign','mayInstall','mayActivate','mayChangeOwner','maySettleUnknown')) and scope['globalFirstStopProof']=='NOT_PROVEN','NO_PRODUCTION_CLAIM')
 source_raw={r:read(base/(r+'-manifest.json'))[0] if r!='bridge' else read(Path('/opt/r16/releases/r16-daily-20261012-r15/bridge-manifest.json'))[0] for r in VERSIONS}
 source={r:parse(b) for r,b in source_raw.items()}
 need({r:digest(m) for r,m in source.items()}==VERSIONS and pub['versions']==VERSIONS,'SOURCE_ROLE_PIN')
 need(docs['SOURCE_ROLE_MANIFESTS.json']['artifacts']==source,'SOURCE_MANIFEST_SET')
 roles={r:docs[r+'-manifest.json'] for r in VERSIONS};union={}
 for r,m in source.items():
  need(roles[r]['schema']==m['schema'] and roles[r]['role']==r and roles[r]['entry']==m['entry'] and set(roles[r]['files'])==set(m['files']),'ROLE_MEMBERSHIP')
  for n,h in m['files'].items():
   safe(n);need(n not in union or union[n]==h,'BASE_ROLE_CONFLICT');union[n]=h
 need(set(inv['files'])==set(union),'INVENTORY_SET')
 tree(package,{'payload/'+n for n in union}|{'metadata/'+n for n in META})
 changed=set();total=0;verified={}
 for n,old_pin in sorted(union.items()):
  raw,mode=read(package/'payload'/n);old,old_mode=read(base/n)
  need(sha(old)==old_pin and old_mode in (0o644,0o755),'BASE_BYTES')
  if n in OVERLAYS:
   need(n in source['native']['files'] and all(n not in source[r]['files'] for r in ('app','bridge')),'OVERLAY_NATIVE_ONLY')
   rel='execution/minimal-human-trust/'+('maintenance/source19-native-transition-r1/payload/'+n if n in ('host/workspace-dispatcher.mjs','host/native-runner.mjs') else n)
   expected=git(repo,'show',head+':'+rel);need(raw==expected and mode==0o644,'EXACT_REVIEWED_OVERLAY')
   need(raw!=old,'OVERLAY_NOT_CHANGED');changed.add(n)
  else: need(raw==old and mode==old_mode,'BASE_REPLACED')
  row={'sha256':sha(raw),'bytes':len(raw),'mode':mode,'origin':'EXACT_NATIVE_LIFECYCLE_BACKPORT' if n in OVERLAYS else 'EXACT_SOURCE19_BASE'}
  need(inv['files'][n]==row,'INVENTORY_BYTES_MODE');total+=len(raw);verified[n]=row
  for r,m in roles.items():
   if n in m['files']: need(m['files'][n]==row['sha256'],'ROLE_BYTES')
 for r,m in source.items():
  expected={**m,'files':{n:verified[n]['sha256'] for n in m['files']}}
  need(roles[r]==expected,'EXACT_TARGET_ROLE_OBJECT')
 expected_provenance={'schema':'r16.source19-native-transition.provenance.v1','sourceHead':head,
  'sourceRoleManifestPaths':{r:str(base/(r+'-manifest.json')) if r!='bridge' else '/opt/r16/releases/r16-daily-20261012-r15/bridge-manifest.json' for r in VERSIONS},
  'baseDirectory':str(base),'baseFiles':len(union),
  'baseOverlayPins':{n:union[n] for n in OVERLAYS},
  'candidateOverlayPins':{n:verified[n]['sha256'] for n in OVERLAYS},
  'sourceCrypto':'EXACT_PUBLIC19_DIGEST_REQUIRES_EXTERNAL_G1_CRYPTO_RECEIPT',
  'rootMarkerRead':False,'liveBusinessStateRead':False,'productionEffects':0}
 need(docs['PROVENANCE.json']==expected_provenance,'EXACT_PROVENANCE')
 need(changed==OVERLAYS and scope['changedFiles']==sorted(OVERLAYS),'ONLY_FIVE_NATIVE_CHANGES')
 need(all(metadata[r+'-manifest.json']==source_raw[r] for r in ('app','bridge')),'APP_BRIDGE_RAW_CHANGED')
 target_versions={r:digest(m) for r,m in roles.items()}
 need(scope['targetVersions']==target_versions and scope['sourceVersions']==VERSIONS and target_versions['native']!=VERSIONS['native'],'TARGET_VERSIONS')
 bindings=[{'role':r,'artifactPath':n,'path':'/opt/r16/releases/'+TARGET+'/'+n,'sha256':h} for r,m in sorted(roles.items()) for n,h in sorted(m['files'].items())]
 need(docs['LOCAL_FILE_BINDINGS.json']['files']==bindings and scope['roleBindings']==len(bindings) and scope['payloadFiles']==len(union) and inv['totalBytes']==total,'BINDINGS')
 need(metadata['SHA256SUMS.txt']==''.join(verified[n]['sha256']+'  payload/'+n+'\n' for n in sorted(verified)).encode(),'SHA256_LIST')
 need(git(repo,'status','--porcelain=v1')==b'','SOURCE_CHANGED')
 return {'schema':'r16.source19-native-transition.independent-byte-verification.v1','status':'PASS_UNSIGNED_BYTES_ONLY','sourceHead':head,'inventorySha256':inventory_sha,'payloadFiles':len(union),'roleBindings':len(bindings),'payloadBytes':total,'changedFiles':sorted(changed),'targetVersions':target_versions,'metadataSha256':{n:sha(b) for n,b in sorted(metadata.items())},'productionAdmission':'BLOCKED_NOT_INSTALLED','productionEffects':0,'businessAcceptance':False}

if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__)
 for n in ('package','repo','base'):p.add_argument('--'+n,type=Path,required=True)
 p.add_argument('--source-head',required=True);p.add_argument('--inventory-sha256',required=True);a=p.parse_args()
 try:print(json.dumps(verify(a.package,a.repo,a.base,a.source_head,a.inventory_sha256),sort_keys=True))
 except (OSError,ValueError,KeyError,subprocess.SubprocessError):print('{"status":"VERIFICATION_REFUSED","productionEffects":0}');raise SystemExit(78)
