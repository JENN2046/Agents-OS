#!/usr/bin/env python3
"""Build an isolated, unsigned R15 App+Native fix payload from signed public files."""
import pathlib,json,hashlib,os,stat,subprocess,base64,datetime,argparse
from cryptography.hazmat.primitives.serialization import load_der_public_key
BASE=pathlib.Path('/opt/r16/releases/r16-daily-20261012-r15')
WORK=pathlib.Path('/home/jenn/AGENTS_OS_Workspace/ops/g1d-native-recovery-reconnect-20261014-r1/r15-backport')
REPO=WORK.parent/'repo'
OUT=pathlib.Path('/home/jenn/Documents/Codex/2026-10-15/G1D-R15-APP-RECOVERY-R6')
PRIOR=pathlib.Path('/home/jenn/Documents/Codex/2026-10-14/G1D-R15-RECOVERY-PATCH-R1/package/metadata')
HEAD='0cd4ed954052557341c9c8687febc62076d56a22'
parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=pathlib.Path,default=OUT)
OUT=parser.parse_args().output
if not OUT.is_absolute() or OUT.resolve()!=OUT:raise SystemExit('ABSOLUTE_OUTPUT_REQUIRED')
if os.geteuid()==0:raise SystemExit('NON_PRIVILEGED_BUILD_REQUIRED')
DELTAS={
 'host/workspace-dispatcher.mjs':(WORK/'host/workspace-dispatcher.mjs','ba4ef78187a8701b97bd03461faed44771c4d71b8541681a6d573e3f35ed079c'),
 'app/workspace-host.mjs':(REPO/'execution/minimal-human-trust/maintenance/r15-app-backport/app/workspace-host.mjs','bfef60223b8fd186f2e96887b770678777bf99ff2a5c84a3c36273d8f172a6ab'),
 'app/app-runner.mjs':(REPO/'execution/minimal-human-trust/maintenance/r15-app-backport/app/app-runner.mjs','feaf51d26f5ef56cdfe013b65fe3faef37f91bc26391835810deb655e51f14d7')}
def need(v,c):
 if not v:raise ValueError(c)
def sha(b):return hashlib.sha256(b).hexdigest()
def canonical(v):
 if isinstance(v,dict):return '{'+','.join(canonical(k)+':'+canonical(v[k]) for k in sorted(v,key=lambda s:s.encode('utf-16-be')))+'}'
 if isinstance(v,list):return '['+','.join(map(canonical,v))+']'
 return json.dumps(v,ensure_ascii=False,separators=(',',':'),allow_nan=False)
def digest(v):return sha(canonical(v).encode())
def read(p,patch=False):
 cursor=pathlib.Path('/')
 for part in p.parts[1:]:
  cursor/=part;s=cursor.lstat();need(not stat.S_ISLNK(s.st_mode) and s.st_uid in (0,os.getuid()) and not s.st_mode&0o002,'SOURCE_PATH_UNSAFE')
 s=p.stat();need(stat.S_ISREG(s.st_mode) and s.st_nlink==1 and not s.st_mode&(0o7002 if patch else 0o7022),'SOURCE_FILE_UNSAFE')
 return p.read_bytes(),stat.S_IMODE(s.st_mode)
def dec(v):return base64.urlsafe_b64decode(v+'='*((-len(v))%4))
def verify(e,key,schema):
 need(e['body']['schema']==schema,'SCHEMA');load_der_public_key(dec(key)).verify(dec(e['signature']),b'R16-SIGNED\0'+canonical(e['body']).encode())
def write(p,raw,mode=0o644):
 p.parent.mkdir(parents=True,exist_ok=True,mode=0o755)
 with p.open('xb') as f:f.write(raw)
 p.chmod(mode)
def save(name,obj):write(OUT/'package/metadata'/name,(canonical(obj)+'\n').encode())
need(subprocess.run(['git','merge-base','--is-ancestor',HEAD,'HEAD'],cwd=REPO).returncode==0,'RUNTIME_FIX_NOT_ANCESTOR')
need(not subprocess.check_output(['git','status','--porcelain'],cwd=REPO,text=True),'DIRTY_SOURCE')
need(not (OUT/'package').exists(),'OUTPUT_EXISTS')
pub=json.loads(read(PRIOR/'R15_PUBLIC_CONFIG.json')[0]);need(digest(pub)=='be3ff2b5125f8212206d2848bb32889c3c6b50a8ca56aa3b1a4bc4359591bbdb','BASE_PUBLIC_PIN')
verify(pub['release'],pub['releasePublicKey'],'r16.release.v1');verify(pub['grant'],pub['issuerPublicKey'],'r16.workspace.v1')
old={r:json.loads(read(BASE/(r+'-manifest.json'))[0]) for r in ['app','bridge','native']}
new=json.loads(json.dumps(old));union={};bindings=0
for role,m in old.items():
 need(digest(m)==pub['versions'][role],'BASE_ROLE_PIN')
 for name,h in m['files'].items():
  need(not pathlib.PurePosixPath(name).is_absolute() and all(x not in ('','.','..') for x in name.split('/')) and '\\' not in name,'PATH')
  need(name not in union or union[name]==h,'OVERLAP');union[name]=h;bindings+=1
need(len(union)==12592 and bindings==16591,'BASE_COUNTS')
patches={n:read(p,patch=True)[0] for n,(p,h) in DELTAS.items()}
for n,(p,h) in DELTAS.items():need(sha(patches[n])==h,'FIX_PIN')
inventory={};base_bytes=0;total=0
for name,h in sorted(union.items()):
 raw,mode=read(BASE/name);need(sha(raw)==h,'BASE_BYTES:'+name);base_bytes+=len(raw)
 raw=patches.get(name,raw);newh=sha(raw)
 need(not any(x=='.env' or x.startswith('.env.') or x in ('id_rsa','id_ed25519') for x in name.split('/')) and not name.endswith(('.cred','.pem','.key','.p12','.pfx')),'DENIED_FILE')
 import re
 need(not re.search(rb'-----BEGIN (?:RSA |EC |OPENSSH |ENCRYPTED )?PRIVATE KEY-----\r?\n[A-Za-z0-9+/=\r\n]{32,}-----END ',raw),'PRIVATE_KEY_OBJECT')
 write(OUT/'package/payload'/name,raw,mode)
 inventory[name]={'sha256':newh,'bytes':len(raw),'mode':mode,'source':'REVIEWED_R15_BACKPORT' if name in DELTAS else 'VERIFIED_SIGNED_R15_REUSE','baselineSha256':h}
 for role,m in new.items():
  if name in m['files']:m['files'][name]=newh
 total+=len(raw)
need(base_bytes==149497453 and total==149502002,'SIZE')
versions={r:digest(m) for r,m in new.items()}
need(versions['app']=='34731b300ccad9a1fbfd45b07422d847e8989d7e9dc052b0dda939cd99adb500' and versions['bridge']==pub['versions']['bridge'] and versions['native']=='2516e881b0622b3ac2d53c454e6ccf9950441c5cb3c26a53500b45d3b1dbe7b4','TARGET_VERSIONS')
save('R15_PUBLIC_CONFIG.json',pub);save('BASE_ROLE_MANIFESTS.json',old)
for role,m in new.items():save(role+'-manifest.json',m)
save('PAYLOAD_INVENTORY.json',inventory)
write(OUT/'package/metadata/SHA256SUMS_PAYLOAD.txt',''.join(v['sha256']+'  '+n+'\n' for n,v in inventory.items()).encode())
summary={'schema':'g1d.r15-app-recovery-physical-candidate.v1','status':'ISOLATED_UNSIGNED_NOT_AUTHORIZED_FOR_INSTALL','sourceFixCommit':HEAD,'sourcePr':'https://github.com/JENN2046/Agents-OS/pull/49','baseReleaseId':pub['release']['body']['id'],'proposedReleaseId':'r16-daily-20261015-r15-app-recovery-r6','basePublicConfigDigest':digest(pub),'originalVersions':pub['versions'],'candidateVersions':versions,'changedFiles':sorted(DELTAS),'changedFileSha256':{n:h for n,(p,h) in DELTAS.items()},'payloadUniqueFiles':len(union),'roleBindings':bindings,'payloadBytes':total,'baseBytes':base_bytes,'payloadInventoryHash':digest({n:v['sha256'] for n,v in inventory.items()}),'authority':False,'maySign':False,'mayInstall':False,'mayStartServices':False,'maySettleUnknown':False,'mayReplayUnknown':False,'releaseIssuedAt':None,'releaseNotAfter':None,'releaseSignature':None,'originalUnknownSettlementIncluded':False,'issuerGrantKeysPeersAndScopeUnchanged':True,'builderSha256':sha(pathlib.Path(__file__).read_bytes())}
save('CANDIDATE.json',summary)
# Explicit modes on every newly created candidate directory; mkdir(parents=True)
# applies its mode only to the last component and the caller may have umask002.
for directory,dirs,files in os.walk(OUT/'package',followlinks=False):
 need(not pathlib.Path(directory).is_symlink(),'OUTPUT_LINK');pathlib.Path(directory).chmod(0o755)
print(json.dumps(summary,indent=2))
