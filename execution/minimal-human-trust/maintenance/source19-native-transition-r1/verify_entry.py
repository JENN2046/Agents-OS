#!/usr/bin/python3
"""Independent stdlib verifier for an uninstalled readonly code bundle.
Does not import builder, runtime, keys or any production state.
"""
import argparse,hashlib,json,os,re,stat,subprocess
from pathlib import Path
ROOT='/usr/lib/r16-maintenance/source19-native-transition-r1'
PIN='/etc/r16-maintenance/source19-native-transition-r1-entry-capsule.json'
def need(v,c):
 if not v:raise ValueError(c)
def canonical(x):
 if type(x)is dict:return '{'+','.join(json.dumps(k)+':'+canonical(x[k])for k in sorted(x,key=lambda s:s.encode('utf-16-be')))+'}'
 if type(x)is list:return '['+','.join(map(canonical,x))+']'
 return json.dumps(x,ensure_ascii=False,separators=(',',':'))
def sha(b):return hashlib.sha256(b).hexdigest()
def parse(raw):
 def unique(items):
  out={}
  for k,v in items:need(k not in out,'DUPLICATE_KEY');out[k]=v
  return out
 return json.loads(raw,object_pairs_hook=unique)
def read(p,mode):
 need(not any(x.is_symlink()for x in(p,*p.parents)),'LINK_REFUSED');fd=os.open(p,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
 try:
  a=os.fstat(fd);need(stat.S_ISREG(a.st_mode)and a.st_uid==os.geteuid()and a.st_nlink==1 and stat.S_IMODE(a.st_mode)==mode and a.st_size<=32*1024*1024,'FILE_METADATA');b=b''
  while len(b)<=a.st_size:
   c=os.read(fd,65536)
   if not c:break
   b+=c
  stamp=lambda s:(s.st_dev,s.st_ino,s.st_mode,s.st_uid,s.st_gid,s.st_nlink,s.st_size,s.st_mtime_ns,s.st_ctime_ns)
  need(len(b)==a.st_size and stamp(a)==stamp(os.fstat(fd))==stamp(p.lstat()),'FILE_CHANGED');return b
 finally:os.close(fd)
def exact_tree(base,expected):
 dirs={'.'}
 for n in expected:
  dirs.update(str(p)for p in Path(n).parents)
 actual=set();actualdirs={'.'}
 for current,children,files in os.walk(base,followlinks=False):
  parent=Path(current);ps=parent.lstat();need(stat.S_ISDIR(ps.st_mode)and ps.st_uid==os.geteuid()and not ps.st_mode&0o022,'BUNDLE_DIRECTORY_UNSAFE')
  for n in children:
   p=parent/n;st=p.lstat();need(stat.S_ISDIR(st.st_mode)and not stat.S_ISLNK(st.st_mode),'BUNDLE_LINK_OR_SPECIAL');actualdirs.add(p.relative_to(base).as_posix())
  for n in files:
   p=parent/n;st=p.lstat();need(stat.S_ISREG(st.st_mode),'BUNDLE_LINK_OR_SPECIAL');actual.add(p.relative_to(base).as_posix())
 need(actual==expected and actualdirs==dirs,'BUNDLE_EXACT_SET')
def verify(bundle,repo,head,capsule):
 need(os.getuid()==os.geteuid()!=0,'ORDINARY_USER_VERIFICATION_ONLY');need(re.fullmatch('[a-f0-9]{64}',capsule)and re.fullmatch('[a-f0-9]{40}',head),'EXTERNAL_PINS_REQUIRED')
 raw=read(bundle/'root/ENTRY_FREEZE.json',0o600);need(sha(raw)==capsule,'EXTERNAL_CAPSULE_MISMATCH');freeze=parse(raw)
 need(raw==canonical(freeze).encode()and set(freeze)=={'schema','mode','files','packageFiles','planTemplate','revisionRequest'}and freeze['schema']=='r16.source19-native-transition.entry-freeze.v1'and freeze['mode']=='READONLY_PREFLIGHT_SOURCE'and freeze['packageFiles']=={},'READONLY_CAPSULE_REQUIRED')
 need(freeze['revisionRequest']=={'legacy21_22Disposition':'CANCELLED_UNALLOCATED_REPLAN','forward':None,'recovery':None},'NO_REVISION_ALLOCATION_REQUIRED')
 names=set(freeze['files']);minimum={'operator.py','common.py','bootstrap.py','foreground.py','rpc.py','service_main.py','service-run.mjs','public-state.mjs','revision-plan.mjs','transport.py','native_guard.py'}
 prefix='maintenance/source19-native-transition-r1/';need({prefix+'entry/'+n for n in minimum}<=names and {prefix+n for n in('stop_transition.py','linux_backend.py','native_checkpoint.py','checkpoint_public.mjs','orchestration.py')}<=names,'REQUIRED_CODE_MISSING')
 exact_tree(bundle/'root/runtime',names)
 targets={};allbytes={}
 for name,row in freeze['files'].items():
  need(name and not name.startswith('/')and '\\'not in name and all(p not in('','.','..')for p in name.split('/'))and set(row)=={'sha256','bytes','mode'}and row['mode']==0o644,'SOURCE_RECORD')
  b=read(bundle/'root/runtime'/name,row['mode']);need(sha(b)==row['sha256']and len(b)==row['bytes'],'SOURCE_BYTES_OR_SIZE');expected=subprocess.check_output(['git','-C',str(repo),'show',head+':execution/minimal-human-trust/'+name],stderr=subprocess.DEVNULL);need(expected==b,'EXACT_GIT_HEAD_BYTES');allbytes[name]=b
  targets[ROOT+'/runtime/'+name]={**row,'uid':0,'gid':0}
 # Every relative ESM import must resolve within the independently read closure.
 for name,b in allbytes.items():
  if name.endswith('.mjs'):
   for rel in re.findall(r"(?:from\s+|import\s*)['\"]([.][^'\"]+)['\"]",b.decode()):
    resolved=os.path.normpath(str(Path(name).parent/rel));need(resolved in names,'NODE_IMPORT_CLOSURE_MISSING')
 codehash=sha(canonical({ROOT+'/runtime/'+n:r['sha256']for n,r in freeze['files'].items()}).encode())
 expectedTemplate={'schema':'r16.source19-native-transition.plan.v1','scope':'SAME_PLAN_SOURCE19_NATIVE_MAINTENANCE_NOT_DRAINED','sourcePublicConfigHash':'56e1df18a54950ea346a51654e61df60afe33cb9928ae77293b2cf336fd8a5ec','sourceDeliveryHash':'b8645f6fe206e84dd07c2c6c166bfe4016d1deefca28bf9545dcfa1560f013e9','grantHash':'00ac437d66143e627132975555d06396d69ff69616f630d19e3622627e15c5e6','sourceNativeVersion':'2516e881b0622b3ac2d53c454e6ccf9950441c5cb3c26a53500b45d3b1dbe7b4','targetReleaseId':'r16-daily-20261017-source19-native-lifecycle-r1','targetNativeVersion':'085e578d4c974aa706b6980e1fd20cd9880e694c3a6edfb237924cd6c8525dcb','targetInventoryHash':'30cc64a3d3e5684a08d249d5c52bee4f3d8815833cac8399b073c0a7dc61731e','codeFreezeHash':codehash,'allowNativeNonGracefulOnce':True,'acceptUnprovenInflight':True,'acceptPossibleUpstreamContinuation':True,'recoveryPolicy':'KEEP_CRASHED_NATIVE_STOPPED_NO_AUTOMATIC_BUSINESS_REOPEN'}
 need(freeze['planTemplate']==expectedTemplate,'FIXED_TEMPLATE_MISMATCH')
 pinraw=read(bundle/'installed-entry-pin.json',0o600);need(parse(pinraw)=={'schema':'r16.source19-native-transition.installed-entry.v1','capsuleHash':capsule}and pinraw==canonical(parse(pinraw)).encode(),'INSTALLED_PIN_CANDIDATE')
 targets[ROOT+'/ENTRY_FREEZE.json']={'sha256':capsule,'bytes':len(raw),'mode':0o600,'uid':0,'gid':0};targets[PIN]={'sha256':sha(pinraw),'bytes':len(pinraw),'mode':0o600,'uid':0,'gid':0}
 cloudTargets={}
 for name,dst,mode in [('r16-source19-native-transition-r1-rpc','/usr/libexec/r16-source19-native-transition-r1-rpc',0o755),('r16-source19-native-transition-r1.sudoers','/etc/sudoers.d/r16-source19-native-transition-r1',0o440)]:
  b=read(bundle/'cloud-policy'/name,mode);need(b==allbytes[prefix+'entry/'+name],'FIXED_CLOUD_POLICY_BYTES');cloudTargets[dst]={'sha256':sha(b),'bytes':len(b),'mode':mode,'uid':0,'gid':0}
 need(allbytes[prefix+'entry/r16-source19-native-transition-r1.sudoers'].decode()=='# Template only; not installed by this source task. The helper rejects all effects.\nubuntu ALL=(root) NOPASSWD: /usr/libexec/r16-source19-native-transition-r1-rpc preflight *\n','READONLY_SUDOERS_SCOPE')
 admission=parse(read(bundle/'CODE_ADMISSION_CANDIDATE.json',0o644))
 expectedAdmission={'schema':'r16.source19-native-transition.code-admission-candidate.v1','sourceHead':head,'capsuleHash':capsule,'scope':'INSTALL_ROOT_OWNED_READONLY_PREFLIGHT_CODE_AND_FIXED_RPC_ONLY','targets':targets,'cloudOnlyTargets':cloudTargets,'directoryMode':0o755,'existingPathPolicy':'ABSENT_OR_EXACT_MATCH_ONLY_NO_OVERWRITE','rootOwned':True,'requiresRealHostAdminReview':True,'authority':False,'readyForNativeConfirmation':False,'productionEffects':0,'serviceUnitInstalled':False,'helperOrSudoersInstalled':False,'packageOrReleaseInstalled':False,'signaturesIssued':0,'ownerIdentityChanged':False,'revisionAllocated':False,'businessAcceptance':False,'blockedExecutionReasons':['TARGET_ACTIVATION_CURRENT_CHECKPOINT_RECOVERY_CONTRACT_NOT_IMPLEMENTED','REAL_TWO_HOST_ROOT_PREFLIGHT_NOT_YET_PERFORMED'],'rollback':'Archive only exact matching newly installed code, pin and cloud readonly RPC policy; leave existing services, business state and prior policy untouched.'}
 need(admission==expectedAdmission,'CODE_ADMISSION_SCOPE')
 receipt=parse(read(bundle/'BUILD_RECEIPT.json',0o644));need(receipt=={'schema':'r16.source19-native-transition.code-bundle-build.v1','sourceHead':head,'capsuleHash':capsule,'sourceFiles':len(names),'sourceBytes':sum(map(len,allbytes.values())),'authority':False,'readyForNativeConfirmation':False,'productionEffects':0,'packageCopied':False,'revisionAllocated':False,'businessAcceptance':False},'BUILD_RECEIPT_SCOPE')
 expected={'cloud-policy/r16-source19-native-transition-r1-rpc','cloud-policy/r16-source19-native-transition-r1.sudoers','root/ENTRY_FREEZE.json','installed-entry-pin.json','CODE_ADMISSION_CANDIDATE.json','BUILD_RECEIPT.json'}|{'root/runtime/'+n for n in names};exact_tree(bundle,expected)
 return {'schema':'r16.source19-native-transition.code-bundle-independent-verification.v1','status':'READONLY_CODE_BYTES_PASS_NOT_INSTALLED','sourceHead':head,'capsuleHash':capsule,'sourceFiles':len(names),'sourceBytes':sum(map(len,allbytes.values())),'authority':False,'readyForNativeConfirmation':False,'productionEffects':0,'revisionAllocated':False,'businessAcceptance':False}
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--bundle',type=Path,required=True);p.add_argument('--repo',type=Path,required=True);p.add_argument('--source-head',required=True);p.add_argument('--capsule-sha256',required=True);a=p.parse_args()
 try:print(json.dumps(verify(a.bundle,a.repo,a.source_head,a.capsule_sha256)))
 except Exception as e:print(json.dumps({'status':'REFUSED','code':str(e)if type(e)is ValueError else'INDEPENDENT_CODE_VERIFICATION_FAILED','productionEffects':0}));raise SystemExit(78)
