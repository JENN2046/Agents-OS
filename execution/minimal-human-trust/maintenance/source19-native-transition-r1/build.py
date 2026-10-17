#!/usr/bin/python3
"""Unsigned, ordinary-user five-file Native maintenance assembly. No deployment API."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess

HERE = Path(__file__).resolve().parent
PRODUCT = 'execution/minimal-human-trust/'
SOURCE_RELEASE = 'r16-daily-20261015-r15-app-recovery-r6'
TARGET_RELEASE = 'r16-daily-20261017-source19-native-lifecycle-r1'
SOURCE_PUBLIC = '56e1df18a54950ea346a51654e61df60afe33cb9928ae77293b2cf336fd8a5ec'
SOURCE_DELIVERY = 'b8645f6fe206e84dd07c2c6c166bfe4016d1deefca28bf9545dcfa1560f013e9'
BRIDGE_MANIFEST = Path('/opt/r16/releases/r16-daily-20261012-r15/bridge-manifest.json')
SOURCE_VERSIONS = {'app':'34731b300ccad9a1fbfd45b07422d847e8989d7e9dc052b0dda939cd99adb500',
 'bridge':'9c58c33478388003fd52da0cb15736ec951a9bfc9cf29738e20de5d741921352',
 'native':'2516e881b0622b3ac2d53c454e6ccf9950441c5cb3c26a53500b45d3b1dbe7b4'}
BASE_OWNER = 0
DISPATCHER = 'host/workspace-dispatcher.mjs'
SERVICE = 'native/upstream/VCPDistributedServer/Plugin/ProjectForge/ProjectForgeService.js'
INDEXER = 'native/upstream/VCPDistributedServer/Plugin/ProjectForge/indexerClient.js'
OVERLAY_PINS = {DISPATCHER:'f99830fea07c8ab7cd8873910f31ff5e6ac74d71cfd4b88fab3c2f35f64429cb',
 'host/headless-host.mjs':'070d22210d7c6df733aa337b6ddd6e49c1e4ec1a479d59357515f0533e81f06f',
 'host/native-runner.mjs':'990e3f186c45c2db377181aeda9204d64372544ddfcb40f9b83aa6d65ba1b0c2',
 SERVICE:'e3739ed2c91d96dd79eb7596ef0cf3cf95800971f330823e916c5ddb35e736f5',
 INDEXER:'1e5f91e7021fc914b2dbe66323ccc1632ad6a14f05e476a7cdb1a088d33f9c8e'}
BASE_PINS = {DISPATCHER:'ba4ef78187a8701b97bd03461faed44771c4d71b8541681a6d573e3f35ed079c',
 'host/headless-host.mjs':'64c6d929f2c438206bfd78b7ea0ba985509e2f1dfda103f8429b441e47aec2ac',
 'host/native-runner.mjs':'0f30ebe457764265b2b8dad630f1a68f6e7251911c94da8a48362c6a0bfe089c',
 SERVICE:'acff4b23e28cb406081a169251ffbd96efc23cf3901517aa7d9c1e24fbbd48a4',
 INDEXER:'c603d3fa35a78f6843b708c2c0cd6d890f627601d2e081395789219616c11ef0'}
RECOVERY_GUARD = '10ab0bce9f12555284ebe570cc8803bb0328bf0d273ea7648ca2b76c40fcd454'
APP_REPAIR_PINS = {'app/workspace-host.mjs':'bfef60223b8fd186f2e96887b770678777bf99ff2a5c84a3c36273d8f172a6ab',
 'app/app-runner.mjs':'feaf51d26f5ef56cdfe013b65fe3faef37f91bc26391835810deb655e51f14d7'}
FORBIDDEN = ('establishBusinessStop','signRuntimeBusinessStop','businessStopEvidence','settleUnavailableRead',
 'unavailableReadResult','READ_RESULT_UNAVAILABLE','runtime-business-stop.mjs','source-baseline.mjs')

class Refused(ValueError):
    pass

def need(ok, code):
    if not ok:
        raise Refused(code)

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def canonical(value):
    if value is None or type(value) in (str, bool):
        return json.dumps(value, ensure_ascii=False, separators=(',', ':'))
    if type(value) is int:
        need(abs(value) <= 9007199254740991, 'UNSAFE_INTEGER')
        return str(value)
    if type(value) is list:
        return '[' + ','.join(canonical(x) for x in value) + ']'
    need(type(value) is dict and all(type(k) is str for k in value), 'CANONICAL_TYPE')
    return '{' + ','.join(canonical(k)+':'+canonical(value[k]) for k in sorted(value, key=lambda s:s.encode('utf-16-be'))) + '}'

def digest(value):
    return sha(canonical(value).encode())

def parse(raw):
    def pairs(rows):
        out = {}
        for k,v in rows:
            need(k not in out, 'DUPLICATE_JSON_KEY')
            out[k] = v
        return out
    return json.loads(raw, object_pairs_hook=pairs)

def relative(name):
    need(type(name) is str and name and not name.startswith('/') and '\\' not in name and all(p not in ('','.','..') for p in name.split('/')) and not any(ord(c)<32 or ord(c)==127 for c in name), 'UNSAFE_PATH')
    return name

def stamp(st):
    return (st.st_dev,st.st_ino,st.st_uid,st.st_gid,st.st_mode,st.st_nlink,st.st_size,st.st_mtime_ns,st.st_ctime_ns)

def read(file, owner=None):
    file = Path(file)
    need(not any(p.is_symlink() for p in (file,*file.parents)), 'SYMLINK_SOURCE')
    fd = os.open(file, os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
    try:
        st = os.fstat(fd)
        need(stat.S_ISREG(st.st_mode) and st.st_nlink==1 and st.st_size<=128*1024*1024 and (owner is None or st.st_uid==owner), 'FILE_TYPE_OR_OWNER')
        with os.fdopen(fd,'rb',closefd=False) as f:
            raw = f.read(128*1024*1024+1)
        need(stamp(st)==stamp(os.fstat(fd))==stamp(file.lstat()) and len(raw)==st.st_size, 'READ_CHANGED')
        return raw,stat.S_IMODE(st.st_mode)
    finally:
        os.close(fd)

def git(repo,*args):
    return subprocess.check_output(('/usr/bin/git','-c','core.hooksPath=/dev/null','-C',str(repo),*args),stderr=subprocess.DEVNULL)

def clean(repo,head):
    need(re.fullmatch('[0-9a-f]{40}',head) and git(repo,'rev-parse','HEAD').decode().strip()==head and git(repo,'status','--porcelain=v1')==b'', 'CLEAN_EXACT_HEAD_REQUIRED')

def tree(base, expected):
    files,dirs = {},{}
    for root,children,names in os.walk(base,followlinks=False,onerror=lambda e:(_ for _ in ()).throw(e)):
        root = Path(root)
        st = root.lstat()
        need(stat.S_ISDIR(st.st_mode) and not root.is_symlink() and st.st_uid==BASE_OWNER and stat.S_IMODE(st.st_mode)==0o755, 'BASE_DIRECTORY_UNSAFE')
        dirs[str(root.relative_to(base))] = stamp(st)
        for name in children:
            need(not (root/name).is_symlink(), 'BASE_DIRECTORY_LINK')
        for name in names:
            p=root/name;st=p.lstat()
            need(stat.S_ISREG(st.st_mode) and st.st_nlink==1 and st.st_uid==BASE_OWNER,'BASE_FILE_UNSAFE')
            files[str(p.relative_to(base))]=stamp(st)
    expected_dirs={'.'}|{str(p) for n in expected for p in Path(n).parents}
    need(set(files)==expected and set(dirs)==expected_dirs,'BASE_EXACT_SET_REQUIRED')
    need(files['.maintenance-capsule.json'][4]&0o777==0o600,'BASE_MARKER_MODE')
    return {'files':files,'directories':dirs}

def segment(text,start,end):
    need(text.count(start)==1,'GUARD_MARKERS')
    i=text.index(start)
    need(end in text[i:],'GUARD_MARKERS')
    return text[i:text.index(end,i)]

def assembly(repo,base,public_file,head):
    clean(repo,head)
    public_raw,mode=read(public_file)
    pub=parse(public_raw)
    need(mode==0o644 and digest(pub)==SOURCE_PUBLIC and pub.get('versions')==SOURCE_VERSIONS and pub.get('release',{}).get('body',{}).get('id')==SOURCE_RELEASE and pub['release']['body'].get('versions')==SOURCE_VERSIONS,'SOURCE19_PUBLIC_REQUIRED')
    paths={'app':base/'app-manifest.json','bridge':BRIDGE_MANIFEST,'native':base/'native-manifest.json'}
    roles,role_raw={},{}
    for role,file in paths.items():
        raw,mode=read(file,BASE_OWNER);m=parse(raw)
        need(mode==0o644 and digest(m)==SOURCE_VERSIONS[role],'SOURCE_ROLE_PIN')
        need(set(m)=={'schema','role','entry','files'} and m['schema']=='r16.runtime-code.v1' and m['role']==role and m['entry'] in m['files'],'SOURCE_ROLE_SHAPE')
        need(all(relative(n) and re.fullmatch('[a-f0-9]{64}',h) for n,h in m['files'].items()),'SOURCE_ROLE_FILES')
        roles[role]=m;role_raw[role]=raw
    union={}
    for m in roles.values():
        for name,pin in m['files'].items():
            need(name not in union or union[name]==pin,'ROLE_OVERLAP')
            union[name]=pin
    expected=set(union)|{'app-manifest.json','native-manifest.json','.maintenance-capsule.json'}
    before=tree(base,expected)
    payload={}
    for name,pin in sorted(union.items()):
        raw,mode=read(base/relative(name),BASE_OWNER)
        need(sha(raw)==pin and mode in (0o644,0o755),'BASE_BYTES_OR_MODE')
        payload[name]=(raw,mode)
    need(before==tree(base,expected),'BASE_CHANGED_DURING_CAPTURE')
    for name,pin in {**BASE_PINS,**APP_REPAIR_PINS}.items():
        need(name in payload and sha(payload[name][0])==pin,'EXACT_REPAIRED_BASE_REQUIRED')
    overlay={}
    for name,pin in OVERLAY_PINS.items():
        need(name in roles['native']['files'] and all(name not in roles[r]['files'] for r in ('app','bridge')),'NATIVE_ONLY_OVERLAY')
        rel=PRODUCT+('maintenance/source19-native-transition-r1/payload/'+name if name in (DISPATCHER,'host/native-runner.mjs') else name)
        raw,mode=read(repo/rel)
        need(mode==0o644 and sha(raw)==pin and raw==git(repo,'show',head+':'+rel),'EXACT_LIFECYCLE_OVERLAY_REQUIRED')
        overlay[name]=(raw,mode)
    old,new=payload[DISPATCHER][0].decode(),overlay[DISPATCHER][0].decode()
    need(all(token not in new for token in FORBIDDEN),'R17_FEATURE_NOT_ALLOWED')
    recovery=segment(old,'  function recoveryFence(','  function authorizeCall(')
    need(sha(recovery.encode())==RECOVERY_GUARD and recovery==segment(new,'  function recoveryFence(','  function authorizeCall('),'R15_RECOVERY_REPAIR_LOST')
    need(segment(old,"      else if(c.operation==='reconcile')","    const response=signed({schema:'r16.workspace-control-result.v1'")==segment(new,"      else if(c.operation==='reconcile')","    const response=signed({schema:'r16.workspace-control-result.v1'"),'LEGACY_RECONCILE_CHANGED')
    strict="if(lease)entry.participant.stop({lease});entry.participant.disconnect();check(entry.participant.status().unresolved.length===0,'RECOVERY_UNRESOLVED');"
    need(strict in old and strict in new,'STRICT_UNKNOWN_CLOSE_LOST')
    payload.update(overlay)
    target_roles={r:{**m,'files':dict(m['files'])} for r,m in roles.items()}
    for name,(raw,_) in overlay.items():
        target_roles['native']['files'][name]=sha(raw)
    target_versions={r:digest(m) for r,m in target_roles.items()}
    need(all(target_versions[r]==SOURCE_VERSIONS[r] for r in ('app','bridge')) and target_versions['native']!=SOURCE_VERSIONS['native'],'ROLE_SCOPE_DRIFT')
    bindings=[{'role':r,'artifactPath':n,'path':'/opt/r16/releases/'+TARGET_RELEASE+'/'+n,'sha256':h} for r,m in sorted(target_roles.items()) for n,h in sorted(m['files'].items())]
    inventory={n:{'sha256':sha(raw),'bytes':len(raw),'mode':mode,'origin':'EXACT_NATIVE_LIFECYCLE_BACKPORT' if n in overlay else 'EXACT_SOURCE19_BASE'} for n,(raw,mode) in sorted(payload.items())}
    scope={'schema':'r16.source19-native-transition.unsigned.v1','status':'UNSIGNED_ISOLATED_NOT_ACTIVATED','sourceHead':head,'sourcePublicConfigDigest':SOURCE_PUBLIC,'sourceDeliveryHash':SOURCE_DELIVERY,'sourceConfigurationRevision':19,'sourceReleaseId':SOURCE_RELEASE,'targetReleaseId':TARGET_RELEASE,'sourceVersions':SOURCE_VERSIONS,'targetVersions':target_versions,'payloadFiles':len(payload),'roleBindings':len(bindings),'changedFiles':sorted(overlay),'configurationRevision':None,'forwardRevision':None,'rollbackRevision':None,'releaseEnvelope':None,'grantEnvelope':None,'signedAt':None,'installedAt':None,'activatedAt':None,'maySign':False,'mayInstall':False,'mayActivate':False,'mayChangeOwner':False,'maySettleUnknown':False,'globalFirstStopProof':'NOT_PROVEN'}
    meta={'UNSIGNED_MAINTENANCE.json':canonical(scope).encode(),'PAYLOAD_INVENTORY.json':canonical({'schema':'r16.source19-native-transition.inventory.v1','sourceHead':head,'files':inventory,'totalBytes':sum(x['bytes'] for x in inventory.values())}).encode(),'LOCAL_FILE_BINDINGS.json':canonical({'schema':'r16.source19-native-transition.bindings.v1','files':bindings}).encode(),'PROVENANCE.json':canonical({'schema':'r16.source19-native-transition.provenance.v1','sourceHead':head,'sourceRoleManifestPaths':{r:str(p) for r,p in paths.items()},'baseDirectory':str(base),'baseFiles':len(union),'baseOverlayPins':BASE_PINS,'candidateOverlayPins':OVERLAY_PINS,'sourceCrypto':'EXACT_PUBLIC19_DIGEST_REQUIRES_EXTERNAL_G1_CRYPTO_RECEIPT','rootMarkerRead':False,'liveBusinessStateRead':False,'productionEffects':0}).encode(),'SOURCE_PUBLIC_CONFIG.json':public_raw}
    meta['SOURCE_ROLE_MANIFESTS.json']=canonical({'schema':'r16.source19-native-transition.source-role-manifests.v1','artifacts':roles}).encode()
    for r,m in target_roles.items():
        meta[r+'-manifest.json']=canonical(m).encode() if r=='native' else role_raw[r]
    meta['SHA256SUMS.txt']=''.join(row['sha256']+'  payload/'+n+'\n' for n,row in inventory.items()).encode()
    clean(repo,head)
    return payload,meta,scope

def build(repo,base,public_file,output,head,plan_only=False):
    need(os.geteuid()!=0 and all(p.is_absolute() for p in (repo,base,public_file,output)),'ORDINARY_USER_ABSOLUTE_PATHS_REQUIRED')
    need(not any(p.is_symlink() for p in (output,*output.parents)) and not output.exists() and not output.is_relative_to(repo) and not output.is_relative_to(base),'NEW_ISOLATED_OUTPUT_REQUIRED')
    payload,metadata,scope=assembly(repo,base,public_file,head)
    if not plan_only:
        output.mkdir(parents=True,mode=0o755);output.chmod(0o755)
        for prefix,rows in (('payload',payload),('metadata',{n:(raw,0o644) for n,raw in metadata.items()})):
            for name,(raw,mode) in rows.items():
                file=output/prefix/relative(name);file.parent.mkdir(parents=True,exist_ok=True,mode=0o755)
                parent=file.parent
                while parent!=output:
                    parent.chmod(0o755);parent=parent.parent
                fd=os.open(file,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,mode)
                with os.fdopen(fd,'wb') as stream:
                    stream.write(raw)
                file.chmod(mode)
    return {**scope,'outputCreated':not plan_only,'metadataSha256':{n:sha(b) for n,b in metadata.items()},'signaturesIssued':0,'productionEffectsIssued':0}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('repo','base','source-public-json','output'):
        p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--source-head',required=True)
    p.add_argument('--plan-only',action='store_true')
    a=p.parse_args()
    try:
        result=build(a.repo,a.base,a.source_public_json,a.output,a.source_head,a.plan_only)
        print(json.dumps(result,sort_keys=True));return 0
    except (OSError,ValueError,KeyError,subprocess.SubprocessError):
        print('{"status":"UNSIGNED_MAINTENANCE_REFUSED","productionEffectsIssued":0}');return 78

if __name__=='__main__':
    raise SystemExit(main())
