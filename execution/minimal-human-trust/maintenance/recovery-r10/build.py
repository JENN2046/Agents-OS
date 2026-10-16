"""Build a new unsigned R10 capsule; R9 protected assets remain read-only."""
import argparse,ast,hashlib,importlib.util,json,os,re,stat,subprocess
from pathlib import Path
HERE=Path(__file__).resolve().parent
def load(name,path):
 spec=importlib.util.spec_from_file_location(name,path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module
C=load('r10_build_constants',HERE/'constants.py')
base=load('r10_build_reviewed_transform',HERE.parent/'recovery-r9/build.py')
FROZEN=base.FROZEN;FROZEN_SHA=base.FROZEN_SHA;OUT=C.OUT
OVERRIDE_PINS={'quiescence.py':'279193bdc2457444d455bf35d48e9bf3f98d0483efddac6138fd40dccf417f74',
 'os_entry.py':'d6e8f1262910adf60688770bc7794a14aeb56c8075e75020e74f400fe098d41b',
 'run.mjs':'40db856df7c994665db1f281afc6e5e8c62b4f42645e5f8faf3055b15d79a0c4',
 'io.mjs':'4eaeca0eddf957f260157bf49b42c1a8b9f5318e019e5546e3407f51d181e4b2'}
need=base.need;sha=base.sha;canon=base.canon;read=base.read;replace_once=base.replace_once
MARKER_SHA=C.TARGET_MARKER_SHA
MARKER_BYTES=C.TARGET_MARKER_BYTES
PACKAGE_VERIFY=r'''
def verify_reused_package(manifest):
    # Fixed read-only assets from the completed R9 transaction, never a link or
    # a second package copy in the new namespace.
    need(manifest['planTemplate'].get('assetReuse')==ASSET_REUSE,'ASSET_REUSE_SCOPE_DRIFT')
    root=Path(ASSET_REUSE['packageRoot'])
    old=secure_read(Path('/usr/lib/r16-maintenance/recovery-r9/SOURCE_FREEZE.json'),max_bytes=CAPSULE_LIMIT)
    need(sha(old)==ASSET_REUSE['targetOriginCapsuleHash'] and json.loads(old)['payloadFiles']==manifest['payloadFiles'],'REUSED_PACKAGE_ORIGIN_DRIFT')
    def metadata(path):
        s=path.lstat()
        return (s.st_dev,s.st_ino,s.st_mode,s.st_uid,s.st_gid,s.st_nlink,s.st_size,s.st_mtime_ns,s.st_ctime_ns)
    def enumerate_tree():
        files=set();directories={}
        def denied(error):raise error
        for directory,children,names in os.walk(root,followlinks=False,onerror=denied):
            p=Path(directory);s=p.lstat()
            need(stat.S_ISDIR(s.st_mode) and s.st_uid==0 and stat.S_IMODE(s.st_mode)==0o700,'REUSED_PACKAGE_DIRECTORY_REFUSED')
            directories[str(p.relative_to(root))]=metadata(p)
            for child in children:need(stat.S_ISDIR((p/child).lstat().st_mode),'REUSED_PACKAGE_SYMLINK_REFUSED')
            for name in names:files.add(str((p/name).relative_to(root)))
        need(files==set(manifest['payloadFiles']),'REUSED_PACKAGE_FILE_SET_DRIFT')
        expected_dirs={'.'}
        for rel in files:
            expected_dirs.update(str(parent) for parent in Path(rel).parents)
        need(set(directories)==expected_dirs,'REUSED_PACKAGE_DIRECTORY_SET_DRIFT')
        return directories
    directories=enumerate_tree()
    inventory=json.loads(secure_read(root/'metadata/PAYLOAD_INVENTORY.json',max_bytes=16*MAX_JSON))
    need(isinstance(inventory,dict),'REUSED_PACKAGE_INVENTORY_REFUSED')
    modes={}
    for rel,row in inventory.items():
        safe_rel(rel);mode=row.get('mode')
        need(type(mode) is int and mode&~0o755==0 and not mode&0o022,'REUSED_PACKAGE_MODE_REFUSED')
        modes['payload/'+rel]=mode
    closure={};identities={}
    for rel,pin in manifest['payloadFiles'].items():
        safe_rel(rel);path=root/rel;before=metadata(path)
        mode=modes.get(rel) if rel.startswith('payload/') else 0o644
        need(mode is not None and stat.S_IMODE(before[2])==mode,'REUSED_PACKAGE_MODE_REFUSED')
        raw=secure_read(path,max_bytes=64*MAX_JSON)
        need(before==metadata(path) and sha(raw)==pin,'REUSED_PACKAGE_BYTE_DRIFT')
        closure[rel]={'sha256':pin,'mode':mode,'bytes':len(raw)};identities[rel]=before
    need(digest(closure)==ASSET_REUSE['packageClosureHash'],'REUSED_PACKAGE_CLOSURE_DRIFT')
    need(directories==enumerate_tree() and all(metadata(root/rel)==value for rel,value in identities.items()),'REUSED_PACKAGE_CHANGED')
    need(secure_read(Path('/usr/lib/r16-maintenance/recovery-r9/SOURCE_FREEZE.json'),max_bytes=CAPSULE_LIMIT)==old,'REUSED_PACKAGE_ORIGIN_DRIFT')
    return {'status':'EXACT_PROTECTED_PACKAGE_REUSED_READONLY','packageFiles':len(closure),'packageClosureHash':digest(closure),'newPackageBytesWritten':0}
'''
LOCAL_REUSE=r'''
function verifyReusedTarget({artifacts,plan},packageDirectory,targetDirectory,inventory){
  need(same(plan.assetReuse,ASSET_REUSE),'ASSET_REUSE_SCOPE_DRIFT');
  need(packageDirectory===ASSET_REUSE.packageRoot&&targetDirectory===ASSET_REUSE.targetRoot,'ASSET_REUSE_PATH_DRIFT');
  need(artifacts.payloadInventoryHash===ASSET_REUSE.targetInventoryHash,'REUSED_TARGET_INVENTORY_DRIFT');
  protectedDirectory(targetDirectory);
  const stamp=s=>[s.dev,s.ino,s.mode,s.uid,s.gid,s.nlink,s.size,s.mtimeMs,s.ctimeMs];
  const scan=(dir,prefix='')=>{
    const s=fs.lstatSync(dir);need(s.isDirectory()&&!s.isSymbolicLink()&&s.uid===0&&(s.mode&0o7777)===0o755,'REUSED_TARGET_DIRECTORY_REFUSED');
    const directories={[prefix]:stamp(s)},files=[];
    for(const e of fs.readdirSync(dir,{withFileTypes:true})){
      const rel=prefix+e.name,p=path.join(dir,e.name),v=fs.lstatSync(p);need(!v.isSymbolicLink(),'REUSED_TARGET_SYMLINK_REFUSED');
      if(v.isDirectory()){const child=scan(p,rel+'/');files.push(...child.files);Object.assign(directories,child.directories);}
      else {need(v.isFile()&&v.uid===0&&v.nlink===1,'REUSED_TARGET_FILE_REFUSED');files.push(safeRelative(rel));}
    }
    return {files:files.sort(),directories};
  };
  const before=scan(targetDirectory),expected=[...Object.keys(inventory),'.maintenance-capsule.json','app-manifest.json','native-manifest.json'].sort();
  need(same(before.files,expected),'REUSED_TARGET_FILE_SET_DRIFT');
  const expectedDirs=new Set(['']);for(const name of expected){const bits=name.split('/');bits.pop();while(bits.length){expectedDirs.add(bits.join('/')+'/');bits.pop();}}
  need(same(Object.keys(before.directories).sort(),[...expectedDirs].sort()),'REUSED_TARGET_DIRECTORY_SET_DRIFT');
  const identities={};
  const checked=(name,mode,max=64*1024*1024)=>{
    const file=path.join(targetDirectory,name),a=fs.lstatSync(file);
    need(a.isFile()&&!a.isSymbolicLink()&&a.uid===0&&a.nlink===1&&(a.mode&0o7777)===mode,'REUSED_TARGET_FILE_REFUSED');
    const raw=protectedBytes(file,{max});need(same(stamp(a),stamp(fs.lstatSync(file))),'REUSED_TARGET_CHANGED');identities[name]=stamp(a);return raw;
  };
  const marker=checked('.maintenance-capsule.json',0o600,32768);
  need(marker.length===ORIGIN_MARKER_BYTES&&sha(marker)===ORIGIN_MARKER_SHA,'REUSED_TARGET_MARKER_BYTES_DRIFT');
  need(same(JSON.parse(marker),{schema:'r16.native-recovery-payload.v3',capsuleHash:ASSET_REUSE.targetOriginCapsuleHash,inventoryHash:ASSET_REUSE.targetInventoryHash}),'REUSED_TARGET_MARKER_DRIFT');
  for(const [name,row]of Object.entries(inventory)){
    safeRelative(name);need(Number.isSafeInteger(row.mode)&&!(row.mode&0o7022),'PAYLOAD_MODE_INVALID');
    const raw=checked(name,row.mode&0o755);need(sha(raw)===row.sha256&&raw.length===row.bytes,'REUSED_TARGET_PAYLOAD_DRIFT');
  }
  for(const role of ['app','native']){
    const raw=checked(role+'-manifest.json',0o644,8*1024*1024),pin=ORIGIN_ROLE_PINS[role+'-manifest.json'];
    need(pin&&pin.mode==='0o644'&&raw.length===pin.bytes&&sha(raw)===pin.sha256,'REUSED_TARGET_ROLE_MANIFEST_BYTES_DRIFT');
    need(same(JSON.parse(raw),artifacts.reviewedInstallation.artifacts[role]),'REUSED_TARGET_ROLE_MANIFEST_DRIFT');
  }
  const after=scan(targetDirectory);
  need(same(before,after)&&Object.entries(identities).every(([name,value])=>same(stamp(fs.lstatSync(path.join(targetDirectory,name))),value)),'REUSED_TARGET_CHANGED');
  return {status:'PAYLOAD_REUSED_COMPLETE_NOT_SELECTED',directory:targetDirectory,uniqueFiles:Object.keys(inventory).length,inventoryHash:artifacts.payloadInventoryHash,originCapsuleHash:ASSET_REUSE.targetOriginCapsuleHash,newTargetBytesWritten:0};
}
'''
def transform(name,raw):
 if not name.endswith(('.py','.mjs')):return raw
 s=base.transform(name,raw).decode()
 s=s.replace(str(base.OUT),str(C.OUT)).replace(base.CLOUD,C.CLOUD_SOURCE)
 s=s.replace('/r16-maintenance/recovery-r9','/r16-maintenance/recovery-r10').replace('r16-native-recovery-maintenance-r9.service','r16-native-recovery-maintenance-r10.service').replace('r16-maintenance-os-r9','r16-maintenance-os-r10')
 s=s.replace('r16-maintenance-recovery-r9','r16-maintenance-recovery-r10').replace('94-r16-maintenance-recovery-r10.conf','95-r16-maintenance-recovery-r10.conf')
 s=s.replace('recovery-r6-bootstrap.lock','recovery-r10-bootstrap.lock')
 s=s.replace('r16.r9.native-install-','r16.r10.native-install-').replace('r9_prior_readonly','r10_prior_readonly')
 package_root=str(C.R9_STATE/'package')
 if name in ('context.mjs','cloud.mjs','local.mjs'):s=s.replace("STATE+'/package","'"+package_root)
 if name=='publication.mjs':s=replace_once(s,"ROOT_JOURNAL+'/package'",json.dumps(package_root))
 if name=='maintenance-release-base.mjs':s=replace_once(s,str(C.OUT/'package'),package_root)
 if name=='local.mjs':
  consts='const ASSET_REUSE='+canon(C.ASSET_REUSE).decode()+';\nconst ORIGIN_MARKER_SHA='+json.dumps(MARKER_SHA)+';\nconst ORIGIN_MARKER_BYTES='+str(MARKER_BYTES)+';\nconst ORIGIN_ROLE_PINS='+canon(C.TARGET_ROLE_PINS).decode()+';\n'
  s=replace_once(s,'function mkdir(dir)',consts+LOCAL_REUSE+'\nfunction mkdir(dir)')
  s=replace_once(s,"  const inventory=json(packageDirectory+'/metadata/PAYLOAD_INVENTORY.json');","  need(same(plan.assetReuse,ASSET_REUSE),'ASSET_REUSE_SCOPE_DRIFT');\n  const inventory=json(packageDirectory+'/metadata/PAYLOAD_INVENTORY.json');")
  start=s.index('  const final=targetDirectory,temp=');end=s.index('\n}\nexport const stageNative',start)
  s=s[:start]+'  return verifyReusedTarget({artifacts,plan},packageDirectory,targetDirectory,inventory);'+s[end:]
 if name=='run.mjs':
  s=replace_once(s,"if(name==='receipt')need(same(value.sourceRecoveryEvidence,json(STATE+'/plan.json').sourceRecoveryEvidence),'RECOVERED_SOURCE_RECEIPT_DRIFT');", "if(name==='receipt'){const plan=json(STATE+'/plan.json');need(same(value.sourceRecoveryEvidence,plan.sourceRecoveryEvidence)&&same(value.assetReuse,plan.assetReuse),'RECOVERED_SOURCE_RECEIPT_DRIFT');}")
  s=replace_once(s,"sourceRecoveryEvidence:json(STATE+'/plan.json').sourceRecoveryEvidence,historicalSourceStopForceUsed", "sourceRecoveryEvidence:json(STATE+'/plan.json').sourceRecoveryEvidence,assetReuse:json(STATE+'/plan.json').assetReuse,historicalSourceStopForceUsed")
 if name=='os_entry.py':
  tree=ast.parse(s);count=0
  for node in tree.body:
   if isinstance(node,ast.FunctionDef) and node.name=='install_capsule':
    start=next(i for i,n in enumerate(node.body) if isinstance(n,ast.Assign) and isinstance(n.value,ast.Call) and isinstance(n.value.func,ast.Name) and n.value.func.id=='candidate_source')
    end=next(i for i,n in enumerate(node.body) if isinstance(n,ast.Expr) and isinstance(n.value,ast.Call) and isinstance(n.value.func,ast.Name) and n.value.func.id=='ensure_file' and "'capsule.json'" in ast.unparse(n.value.args[0]))
    need(start<end,'PACKAGE_COPY_CONTEXT_DRIFT');node.body[start:end]=ast.parse('verify_reused_package(manifest)').body;count+=1
  need(count==1,'PACKAGE_COPY_CONTEXT_DRIFT')
  helpers=ast.parse('ASSET_REUSE='+repr(C.ASSET_REUSE)+'\n'+PACKAGE_VERIFY).body
  tree.body[-1:-1]=helpers;ast.fix_missing_locations(tree);s=ast.unparse(tree)+'\n'
  s=replace_once(s,"prior_namespace = {'__name__': 'r10_prior_readonly'}", "need(pending.get('assetReuse') == manifest['planTemplate'].get('assetReuse') == ASSET_REUSE, 'EXACT_ASSET_REUSE_NATIVE_TARGET_REQUIRED')\n    prior_namespace = {'__name__': 'r10_prior_readonly'}")
  s=replace_once(s,"need(receipt.get('sourceRecoveryEvidence') == prior, 'RECOVERED_SOURCE_RECEIPT_DRIFT')", "need(receipt.get('sourceRecoveryEvidence') == prior and receipt.get('assetReuse') == read_json(STATE / 'plan.json')['assetReuse'], 'RECOVERED_SOURCE_RECEIPT_DRIFT')")
  s=replace_once(s,"'sourceRecoveryEvidence': prior, 'historicalSourceStopForceUsed':", "'sourceRecoveryEvidence': prior, 'assetReuse': read_json(STATE / 'plan.json')['assetReuse'], 'historicalSourceStopForceUsed':")
 return s.encode()
def reviewed_inputs():
 raw,_=read(FROZEN/'SOURCE_FREEZE.json');need(sha(raw)==FROZEN_SHA,'FROZEN_R6_CAPSULE_DRIFT');f=json.loads(raw)
 need(len(f['files'])==14 and len(f['payloadFiles'])==12600,'FROZEN_COUNTS_DRIFT')
 original={}
 for name,pin in f['files'].items():
  raw,_=read(FROZEN/name);need(sha(raw)==pin,'FROZEN_RUNTIME_DRIFT:'+name);original[name]=raw
 for name,pin in OVERRIDE_PINS.items():
  raw,_=read(HERE.parent/'release-r6'/name);need(sha(raw)==pin,'REVIEWED_OVERRIDE_DRIFT:'+name);original[name]=raw
 return f,original

def build(out=OUT):
 out=Path(out);need(os.getuid()!=0 and out.is_absolute() and not out.is_symlink() and (not out.exists() or out.is_dir() and not any(out.iterdir())),'EMPTY_NON_ROOT_OUTPUT_REQUIRED')
 f,original=reviewed_inputs();result={name:transform(name,raw) for name,raw in original.items()}
 qsha=sha(result['quiescence.py']);entry,count=re.subn(rb"(?m)^Q_SHA = '[a-f0-9]{64}'$",('Q_SHA = '+repr(qsha)).encode(),result['os_entry.py']);need(count==1,'NEW_Q_PIN_REQUIRED');result['os_entry.py']=entry
 prior=load('r10_build_provenance',HERE/'prior-verifier.py');evidence=prior.PROVENANCE
 for name in ('prior-verifier.py','asset-verifier.py'):result[name]=read(HERE/name)[0]
 for new,old in {'prior-compensation.py':'compensation.py','prior-native-guard.py':'native_guard.py','prior-evidence.json':'LOCAL_EVIDENCE.json'}.items():
  raw,_=read(base.PRIOR/old);need(sha(raw)==prior.PINS[new],'PRIOR_REVIEWED_INPUT_DRIFT');result[new]=raw
 need(len(result)==19 and 'cache-cleanup.py' not in result,'R10_EXACT_RUNTIME_SET_REQUIRED')
 inventory=json.loads(read(FROZEN/'package/metadata/PAYLOAD_INVENTORY.json')[0]);package={};closure={}
 for name,pin in f['payloadFiles'].items():
  need(not Path(name).is_absolute() and '\\' not in name and all(x not in ('','.','..') for x in name.split('/')),'PACKAGE_PATH_REFUSED')
  raw,mode=read(FROZEN/'package'/name);expected=inventory[name[8:]]['mode'] if name.startswith('payload/') else 0o644
  need(sha(raw)==pin and mode==expected,'FROZEN_PACKAGE_BYTES_OR_MODE_DRIFT:'+name);package[name]=(raw,mode);closure[name]={'sha256':pin,'mode':mode,'bytes':len(raw)}
 need(sha(canon(closure))==C.PACKAGE_CLOSURE,'INDEPENDENT_PACKAGE_CLOSURE_DRIFT')
 actual=set()
 for path in (FROZEN/'package').rglob('*'):
  st=path.lstat();need(stat.S_ISDIR(st.st_mode) or stat.S_ISREG(st.st_mode),'FROZEN_PACKAGE_SPECIAL_FILE')
  if stat.S_ISDIR(st.st_mode):need(stat.S_IMODE(st.st_mode)==0o755,'FROZEN_PACKAGE_DIRECTORY_MODE')
  else:actual.add(str(path.relative_to(FROZEN/'package')))
 need(actual==set(package),'FROZEN_PACKAGE_EXTRA_FILE')
 for name,raw in result.items():
  if name.endswith('.py'):compile(raw,name,'exec')
 head=subprocess.check_output(('git','rev-parse','HEAD'),cwd=HERE,text=True).strip();need(re.fullmatch('[a-f0-9]{40}',head),'SOURCE_HEAD_REQUIRED')
 need(not subprocess.check_output(('git','status','--porcelain'),cwd=HERE,text=True),'DIRTY_SOURCE_BUILD_REFUSED')
 freeze={**f,'files':{name:sha(raw) for name,raw in sorted(result.items())},'planTemplate':{**f['planTemplate'],'sourceRecoveryEvidence':evidence,'assetReuse':C.ASSET_REUSE,'maintenanceSourceHead':head}}
 out.mkdir(parents=True,exist_ok=True);out.chmod(0o755)
 def emit(name,raw,mode):
  path=out/name;path.parent.mkdir(parents=True,exist_ok=True);cursor=path.parent
  while cursor!=out:cursor.chmod(0o755);cursor=cursor.parent
  with path.open('xb') as file:file.write(raw)
  path.chmod(mode)
 for name,raw in result.items():emit(name,raw,0o644)
 for name,(raw,mode) in package.items():emit('package/'+name,raw,mode)
 emit('SOURCE_FREEZE.json',canon(freeze),0o644)
 return {'schema':'r16.r10-recovered-source-physical-build.v1','status':'ISOLATED_UNSIGNED_NOT_INSTALLED','frozenBaseSha256':FROZEN_SHA,'capsuleHash':sha(canon(freeze)),'osEntryHash':sha(entry),'quiescenceHash':qsha,'runtimeFiles':len(result),'packageFiles':len(package),'payloadFiles':len(inventory),'packageClosureHash':sha(canon(closure)),'planTemplate':freeze['planTemplate'],'protectedPackageCopied':False,'targetPayloadCopied':False,'oldPlanRenewed':False,'physicalOutput':str(out),'productionExecuted':False}
if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,default=OUT);args=parser.parse_args();print(json.dumps(build(args.output),indent=2))
