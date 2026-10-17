"""Portable generation and actual disposable read-only reuse tests; no root/SSH."""
import ast,base64,copy,hashlib,importlib.util,json,os,shutil,subprocess,sys,tempfile,types,unittest
from pathlib import Path
from unittest.mock import patch
HERE=Path(__file__).resolve().parent
def load(name,path):
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m
b=load('r12_builder_tested',HERE/'build.py')
def canon(v):return json.dumps(v,sort_keys=True,separators=(',',':')).encode()
def sha(v):return hashlib.sha256(v).hexdigest()
class BuildTests(unittest.TestCase):
 def entry(self):
  raw=b.transform('os_entry.py',b.reviewed_override_path('os_entry.py').read_bytes());m=types.ModuleType('r12_generated_entry_tested');m.__file__='<isolated-r12-entry>';exec(compile(raw,m.__file__,'exec'),m.__dict__);return m
 def test_namespace_still_same_payload_and_only_fixed_old_package_reads(self):
  q=b.transform('quiescence.py',(HERE.parent/'release-r6/quiescence.py').read_bytes()).decode()
  self.assertIn("DROPIN_NAME = '97-r16-maintenance-recovery-r12.conf'",q);self.assertIn('r16-maintenance-os-r12',q)
  self.assertIn(b.C.TARGET,q);self.assertNotIn('adopt-first-stop',q)
  for name in ('context.mjs','cloud.mjs','local.mjs','publication.mjs','maintenance-release-base.mjs'):
   source=b.transform(name,b.reviewed_override_path(name).read_bytes()).decode()
   self.assertIn(str(b.C.R9_STATE/'package'),source);self.assertNotIn("STATE+'/package",source);self.assertNotIn("ROOT_JOURNAL+'/package'",source)
  e=self.entry();self.assertEqual(str(e.ROOT),'/usr/lib/r16-maintenance/recovery-r12');self.assertEqual(str(e.STATE),'/var/lib/r16-maintenance/recovery-r12')
  self.assertEqual(str(e.SOURCE),str(b.C.OUT));self.assertEqual(str(e.CLOUD_SOURCE),b.C.CLOUD_SOURCE)
  self.assertEqual(b.C.OUT.name,'maintenance-recovered-r12-r2');self.assertEqual(b.C.CLOUD_SOURCE,'/home/ubuntu/r16-maintenance-recovered-r12-r2-candidate')
 def test_reviewed_overrides_preserve_all_four_exact_historical_hashes(self):
  self.assertEqual(set(b.OVERRIDE_PINS),{'quiescence.py','os_entry.py','run.mjs','io.mjs'})
  for name,pin in b.OVERRIDE_PINS.items():self.assertEqual(sha(b.reviewed_override_path(name).read_bytes()),pin)
 def test_reviewed_entry_is_exact_a3_readiness_source(self):
  self.assertEqual(b.reviewed_override_path('os_entry.py'),HERE.parent/'release-r6/os_entry.py')
  self.assertEqual(sha(b.reviewed_override_path('os_entry.py').read_bytes()),'d9203c884668bab611cd1cc4d98b37cbc3911dacc1367298efb68ccfbfd22b03')
  e=self.entry();source=b.transform('os_entry.py',b.reviewed_override_path('os_entry.py').read_bytes()).decode()
  self.assertIn('def await_restore_ready(',source)
  self.assertIn('EXACT_REVISION_CHAIN_NATIVE_TARGET_REQUIRED',source)
  self.assertEqual(str(e.ROOT),'/usr/lib/r16-maintenance/recovery-r12')
 def test_revision_chain_is_exact_signed18_then19_then20(self):
  self.assertEqual((b.C.SOURCE_REVISION,b.C.FORWARD_REVISION,b.C.ROLLBACK_REVISION),(18,19,20))
  src={n:b.transform(n,b.reviewed_override_path(n).read_bytes()).decode() for n in ('state.mjs','release-publication-base.mjs','cloud.mjs')}
  self.assertIn('d.revision===18&&b.revision===18',src['state.mjs'])
  self.assertIn('export const SOURCE_REVISION=18;',src['release-publication-base.mjs'])
  for n in ('state.mjs','release-publication-base.mjs'):
   self.assertIn(b.C.SOURCE_DELIVERY_HASH,src[n]);self.assertNotIn('5ee11707da0d3a524550db92f8c0a5a80b7a8dac8c97f5a907b47fc956c6ec44',src[n])
  self.assertIn('b.revision===19&&',src['cloud.mjs']);self.assertIn('b.revision===20&&',src['cloud.mjs']);self.assertIn('[18,19,20].includes(token.revision)',src['cloud.mjs'])
 def test_generated_chain_uses_real_fixture_signatures_and_refuses_old_revisions(self):
  # Execute all transformed production JS modules, with synthetic Ed25519
  # roots in the deliberately incompatible isolated fixture domain only.
  with tempfile.TemporaryDirectory(dir=Path.home()) as tmp:
   out=Path(tmp)
   original=json.loads((HERE.parent/'first-stop-r8/fixtures/R6_SOURCE_PINS.json').read_bytes())
   for name in original['files']:
    file=out/name;file.parent.mkdir(parents=True,exist_ok=True)
    file.write_bytes(b.transform(name,b.reviewed_override_path(name).read_bytes()))
   # The module's internal verifier is exposed in this disposable test copy;
   # the actual emitted capsule has no such test export.
   with (out/'release-publication-base.mjs').open('a') as file:file.write('\nexport {verifyEnvelope};\n')
   fixture=json.loads((HERE.parent/'release-r6/fixtures/R15_PUBLIC_CONFIG.json').read_bytes())
   (out/'public.json').write_text(json.dumps(fixture))
   script=r'''
import assert from 'node:assert/strict';
import fs from 'node:fs';
import * as P from './release-publication-base.mjs';
import {validateDelivery} from './cloud.mjs';
const pub=JSON.parse(fs.readFileSync(new URL('./public.json',import.meta.url)));
const roles=['app','bridge','native'],baseManifests=Object.fromEntries(roles.map(role=>[role,{schema:'ISOLATED_ONLY',role,files:{['test/'+role+'.mjs']:'a'.repeat(64)}}]));
const inspection={publicConfig:pub,baseManifests,manifests:baseManifests,versions:{app:P.FIXED.targetAppVersion,bridge:P.FIXED.bridgeVersion,native:P.FIXED.nativeVersion},payloadBytes:149502002,payloadInventoryHash:'b'.repeat(64),metadataHash:'c'.repeat(64)};
const now=Date.now(),h=P.createIsolatedPublicationHarness({inspection,now});
const args={approvedAt:now,expiresAt:now+300000,releaseNotAfter:pub.release.body.notAfter,freezeDigest:'d'.repeat(64),nonce:'isolated_r12_18_19_20'};
assert.equal(h.sourceDelivery.body.revision,18);
const a=h.build(args);assert.equal(a.nextRevision,19);
const signedRelease=h.sign({role:'release',body:a.releaseBody}),forward=h.sign({role:'issuer',body:P.configurationBody(a,signedRelease)});
assert.equal(P.assemblePublication({artifacts:a,signedRelease,signedDelivery:forward}).revision,19);
const rollback=h.sign({role:'issuer',body:P.buildForwardRollback({artifacts:a,currentAcceptedDelivery:forward,issuedAt:now+1}).deliveryBody});assert.equal(rollback.body.revision,20);
const plan={approvedAt:now,expiresAt:now+300000,rollbackDeadline:now+1800000};
const options={plan,sourcePublicConfig:h.sourcePublicConfig,now:now+2,domainVerify:(e,k,schema)=>P.verifyEnvelope(e,k,P.FIXTURE_DOMAIN,schema)};
assert.equal(validateDelivery(forward,options).revision,19);assert.equal(validateDelivery(rollback,{...options,previous:forward}).revision,20);
assert.throws(()=>validateDelivery(forward,{...options,now:plan.expiresAt}),{code:'FORWARD_COMMIT_EXPIRED'});
assert.throws(()=>validateDelivery(rollback,{...options,now:plan.rollbackDeadline+1}),{code:'ROLLBACK_DELIVERY_TARGET_CHANGED'});
for(const revision of [16,17,18,20]){const old=h.sign({role:'issuer',body:{...forward.body,revision}});assert.throws(()=>validateDelivery(old,options),{code:'FORWARD_DELIVERY_TARGET_CHANGED'});}
for(const revision of [16,17,18,19]){const old=h.sign({role:'issuer',body:{...rollback.body,revision}});assert.throws(()=>validateDelivery(old,options),{code:'ROLLBACK_DELIVERY_TARGET_CHANGED'});}
const saved=structuredClone(h.sourceDelivery),old=h.sign({role:'issuer',body:{...saved.body,revision:16}});Object.assign(h.sourceDelivery,old);assert.throws(()=>h.build(args),{code:'SOURCE_REVISION_DRIFT'});Object.assign(h.sourceDelivery,saved);
const invalid={...forward,signature:'A'.repeat(86)};assert.throws(()=>validateDelivery(invalid,options));
assert.deepEqual(rollback.body.publicConfig,h.sourcePublicConfig);assert.deepEqual(forward.body.publicConfig.grant,h.sourcePublicConfig.grant);
console.log('R12_FIXTURE_SIGNATURE_CHAIN_18_19_20_PASS');
'''
   (out/'case.mjs').write_text(script)
   node=shutil.which('node');self.assertIsNotNone(node,'NODE_REQUIRED_NO_SKIP')
   result=subprocess.run([node,str(out/'case.mjs')],capture_output=True,text=True,timeout=30)
   self.assertEqual(result.returncode,0,result.stderr[-2000:]);self.assertIn('R12_FIXTURE_SIGNATURE_CHAIN_18_19_20_PASS',result.stdout)
 def test_no_package_ensure_or_old_writer_is_reachable_in_generated_install(self):
  e=self.entry();tree=ast.parse(b.transform('os_entry.py',b.reviewed_override_path('os_entry.py').read_bytes()))
  fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='install_capsule');body=ast.unparse(fn)
  self.assertIn('verify_reused_package(manifest)',body);self.assertNotIn("STATE / 'package'",body);self.assertNotIn('candidate_source()',body)
  self.assertIn("'r16.r12.native-install-pending.v1'",ast.unparse(tree));self.assertIn('EXACT_ASSET_REUSE_NATIVE_TARGET_REQUIRED',ast.unparse(tree))
  self.assertIn("'assetReuse': read_json",ast.unparse(tree));self.assertIn('recovery-r12-bootstrap.lock',ast.unparse(tree))
  self.assertNotIn('cache-cleanup.py',ast.unparse(tree))
 def test_stage_generated_has_no_copy_fallback_even_when_reuse_field_missing(self):
  source=b.transform('local.mjs',(HERE.parent/'release-r6/local.mjs').read_bytes()).decode()
  stage=source.split('export function stagePayload',1)[1].split('export const stageNative',1)[0]
  self.assertIn("need(same(plan.assetReuse,ASSET_REUSE)",stage);self.assertIn('return verifyReusedTarget',stage)
  for name in ('mkdir(root)','writeImmutableFile','immutableJson','fs.renameSync','atomicBytes'):self.assertNotIn(name,stage)
 def test_expired_native_window_still_refuses_before_source_or_root_copy(self):
  e=self.entry();e.NATIVE_ACCEPTED_AT=1000
  with patch.object(e,'root'),patch.object(e,'now_ms',return_value=301000),patch.object(e,'verify_capsule',side_effect=AssertionError('expired read/copy')):
   with self.assertRaisesRegex(e.Refused,'NEW_NATIVE_BOOTSTRAP_WINDOW_REQUIRED'):e.bootstrap_locked('bootstrap-cloud','a'*64)
 def test_target_and_manifest_original_pins_are_not_derived_from_caller(self):
  source=b.transform('local.mjs',(HERE.parent/'release-r6/local.mjs').read_bytes()).decode()
  for value in [b.C.TARGET_MARKER_SHA,*[row['sha256'] for row in b.C.TARGET_ROLE_PINS.values()]]:self.assertIn(value,source)
  self.assertIn('raw.length===pin.bytes&&sha(raw)===pin.sha256',source)
 def test_existing_output_or_root_build_cannot_write(self):
  with tempfile.TemporaryDirectory() as tmp:
   out=Path(tmp)/'out';out.mkdir();(out/'foreign').write_text('keep')
   with self.assertRaisesRegex(ValueError,'EMPTY_NON_ROOT_OUTPUT_REQUIRED'):b.build(out)
   self.assertEqual((out/'foreign').read_text(),'keep')
   with patch.object(b.os,'getuid',return_value=0),self.assertRaisesRegex(ValueError,'EMPTY_NON_ROOT_OUTPUT_REQUIRED'):b.build(Path(tmp)/'root-output')
   self.assertFalse((Path(tmp)/'root-output').exists())

class SyntheticPhysicalBuildTests(unittest.TestCase):
 def setup_build(self,base):
  frozen=base/'frozen';(frozen/'package/payload/bin').mkdir(parents=True);(frozen/'package/metadata').mkdir()
  raw=b'isolated executable payload';payload=frozen/'package/payload/bin/tool';payload.write_bytes(raw);payload.chmod(0o755)
  inventory={'bin/tool':{'sha256':sha(raw),'bytes':len(raw),'mode':0o755}};(frozen/'package/metadata/PAYLOAD_INVENTORY.json').write_bytes(canon(inventory));(frozen/'package/metadata/PAYLOAD_INVENTORY.json').chmod(0o644)
  for p in frozen.rglob('*'):
   if p.is_dir():p.chmod(0o755)
  template=json.loads((HERE.parent/'first-stop-r8/fixtures/R6_SOURCE_PINS.json').read_bytes())
  original={name:b.reviewed_override_path(name).read_bytes() for name in template['files']}
  files={str(p.relative_to(frozen/'package')):sha(p.read_bytes()) for p in (frozen/'package').rglob('*') if p.is_file()}
  closure={n:{'sha256':h,'bytes':len((frozen/'package'/n).read_bytes()),'mode':(frozen/'package'/n).stat().st_mode&0o777} for n,h in files.items()}
  template['payloadFiles']=files;template['planTemplate']['packageInventoryHash']=sha(canon({'bin/tool':sha(raw)}))
  prior=base/'prior';prior.mkdir();pins={}
  for new,old in {'prior-compensation.py':'compensation.py','prior-native-guard.py':'native_guard.py','prior-evidence.json':'LOCAL_EVIDENCE.json'}.items():
   value=b'{}' if old.endswith('.json') else b'pass\n';(prior/old).write_bytes(value);pins[new]=sha(value)
  return frozen,template,original,prior,types.SimpleNamespace(PROVENANCE={'schema':'ISOLATED_SOURCE_TEST_ONLY'},PINS=pins),sha(canon(closure))
 def run_build(self,base,drift=None):
  frozen,template,original,prior,proof,closure=self.setup_build(base);out=base/'candidate';original_read=b.read
  def read(path,*args,**kw):
   if Path(path) in (HERE/'prior-verifier.py',HERE/'asset-verifier.py'):return b'pass\n',0o644
   return original_read(path,*args,**kw)
  if drift=='byte':(frozen/'package/payload/bin/tool').write_bytes(b'changed')
  if drift=='extra':(frozen/'package/extra').write_bytes(b'extra');(frozen/'package/extra').chmod(0o644)
  with patch.object(b,'FROZEN',frozen),patch.object(b,'reviewed_inputs',return_value=(template,original)),patch.object(b.base,'PRIOR',prior),patch.object(b.C,'PACKAGE_CLOSURE',closure),patch.object(b,'load',return_value=proof),patch.object(b,'read',side_effect=read),patch.object(b.subprocess,'check_output',side_effect=lambda args,**kw:'a'*40+'\n' if args[1]=='rev-parse' else ''):
   if drift:
    with self.assertRaises(ValueError):b.build(out)
    self.assertFalse(out.exists());return
   result=b.build(out)
  freeze=json.loads((out/'SOURCE_FREEZE.json').read_bytes());self.assertEqual(len(freeze['files']),19);self.assertEqual(len(freeze['payloadFiles']),2)
  self.assertEqual(result['status'],'ISOLATED_UNSIGNED_NOT_INSTALLED');self.assertFalse(result['protectedPackageCopied']);self.assertFalse(result['targetPayloadCopied']);self.assertFalse(result['productionExecuted'])
  self.assertEqual(freeze['planTemplate']['assetReuse'],b.C.ASSET_REUSE);self.assertEqual(freeze['planTemplate']['sourceRecoveryEvidence'],proof.PROVENANCE)
  self.assertNotIn('cache-cleanup.py',freeze['files']);self.assertEqual(sha((out/'SOURCE_FREEZE.json').read_bytes()),result['capsuleHash'])
  for n,h in freeze['files'].items():self.assertEqual(sha((out/n).read_bytes()),h)
  for n,h in freeze['payloadFiles'].items():self.assertEqual(sha((out/'package'/n).read_bytes()),h)
  self.assertEqual((out/'package/payload/bin/tool').stat().st_mode&0o777,0o755)
  self.assertTrue(all(p.stat().st_mode&0o777==0o755 for p in out.rglob('*') if p.is_dir()))
 def test_complete_19_source_builder_emits_exact_manifest_last_and_preserves_mode(self):
  # Only payload cardinality/data are synthetic; actual 14 source transforms,
  # sealed 19 file assembly, package copy, digest and emission paths execute.
  with tempfile.TemporaryDirectory(dir=Path.home()) as tmp:self.run_build(Path(tmp))
 def test_package_byte_or_extra_file_drift_never_publishes_candidate(self):
  for drift in ('byte','extra'):
   with self.subTest(drift=drift),tempfile.TemporaryDirectory(dir=Path.home()) as tmp:self.run_build(Path(tmp),drift)
 def test_wrong_frozen_capsule_is_rejected_before_source_or_payload_copy(self):
  with tempfile.TemporaryDirectory() as tmp:
   frozen=Path(tmp);(frozen/'SOURCE_FREEZE.json').write_bytes(b'{}')
   with patch.object(b,'FROZEN',frozen),self.assertRaisesRegex(ValueError,'FROZEN_R6_CAPSULE_DRIFT'):b.reviewed_inputs()

class ReusedTargetTests(unittest.TestCase):
 def scenario(self,drift='none'):
  with tempfile.TemporaryDirectory(dir=Path.home()) as tmp:
   root=Path(tmp);package=root/'package';target=root/'target';package.mkdir(mode=0o700);(package/'metadata').mkdir(mode=0o700);target.mkdir(mode=0o755)
   payload=b'isolated immutable payload';(target/'fixture.mjs').write_bytes(payload);(target/'fixture.mjs').chmod(0o644)
   inventory={'fixture.mjs':{'bytes':len(payload),'sha256':sha(payload),'mode':0o644}};inventory_hash=sha(canon({n:r['sha256'] for n,r in inventory.items()}))
   (package/'metadata/PAYLOAD_INVENTORY.json').write_bytes(canon(inventory));(package/'metadata/PAYLOAD_INVENTORY.json').chmod(0o644)
   manifests={role:{'schema':'r16.runtime-code.v1','role':role,'files':{'fixture.mjs':sha(payload)}} for role in ('app','native')}
   roles={}
   for role,manifest in manifests.items():
    raw=canon(manifest);p=target/(role+'-manifest.json');p.write_bytes(raw);p.chmod(0o644);roles[p.name]={'sha256':sha(raw),'bytes':len(raw),'mode':'0o644'}
   reuse={**b.C.ASSET_REUSE,'packageRoot':str(package),'targetRoot':str(target),'targetInventoryHash':inventory_hash}
   marker=canon({'schema':'r16.native-recovery-payload.v3','capsuleHash':reuse['targetOriginCapsuleHash'],'inventoryHash':inventory_hash})+b'\n'
   (target/'.maintenance-capsule.json').write_bytes(marker);(target/'.maintenance-capsule.json').chmod(0o600)
   with patch.object(b.C,'R9_STATE',root),patch.object(b.C,'ASSET_REUSE',reuse),patch.object(b.C,'TARGET_ROLE_PINS',roles),patch.object(b,'MARKER_SHA',sha(marker)),patch.object(b,'MARKER_BYTES',len(marker)):
    source=b.transform('local.mjs',(HERE.parent/'release-r6/local.mjs').read_bytes()).decode()
   source='\n'.join(line for line in source.splitlines() if not line.startswith('import ')).replace('export function ','function ').replace('export const ','const ')
   # Real disposable files, with only UID metadata projected as root. Every
   # write primitive is a fail-fast spy; production paths are never accessed.
   script=r'''
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto'),assert=require('node:assert/strict');
const root=INPUT.root,target=INPUT.target,package=INPUT.package;let writes=0;
const fail=()=>{writes++;throw Error('UNEXPECTED_WRITE');};
const safe=p=>{assert(p.startsWith(root+'/')||p===root,'NO_PRODUCTION_PATH');return p;};
const meta=s=>Object.assign(Object.create(Object.getPrototypeOf(s)),s,{uid:0});
const fakeFs=new Proxy(fs,{get(o,n){if(n==='lstatSync')return p=>meta(fs.lstatSync(safe(p)));if(n==='readdirSync')return (p,...a)=>fs.readdirSync(safe(p),...a);if(['mkdirSync','writeFileSync','openSync','chmodSync','renameSync','unlinkSync','linkSync','fsyncSync'].includes(n))return fail;return o[n];}});
const canonical=x=>x===null||typeof x!=='object'?JSON.stringify(x):Array.isArray(x)?'['+x.map(canonical).join(',')+']':'{'+Object.keys(x).sort().map(k=>JSON.stringify(k)+':'+canonical(x[k])).join(',')+'}';
const digest=x=>sha(Buffer.from(canonical(x))),sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const need=(v,c)=>{if(!v)throw Object.assign(Error(c),{code:c});};
const protectedBytes=(p,{max=64*1024*1024}={})=>{const a=fs.lstatSync(safe(p));assert(a.isFile()&&!a.isSymbolicLink()&&a.nlink===1&&a.size<=max);return fs.readFileSync(p);};
const json=p=>JSON.parse(protectedBytes(p)),same=(a,b)=>canonical(a)===canonical(b),safeRelative=p=>{assert(!p.startsWith('/')&&!p.includes('..'));return p;};
const stage=new Function('fx','const {fs,path,STATE,protectedBytes,protectedDirectory,json,atomicBytes,atomicJson,immutableJson,syncDir,digest,sha,same,need,safeRelative,FIXED}=fx;\n'+INPUT.source+'\nreturn stagePayload;')({fs:fakeFs,path,STATE:'/unreachable-new-state',protectedBytes,protectedDirectory:p=>{assert(fs.lstatSync(safe(p)).isDirectory());},json,atomicBytes:fail,atomicJson:fail,immutableJson:fail,syncDir:fail,digest,sha,same,need,safeRelative,FIXED:{targetDirectory:target,targetAppVersion:digest(INPUT.manifests.app),nativeVersion:digest(INPUT.manifests.native)}});
let plan={assetReuse:INPUT.reuse,capsuleHash:'new-capsule'},artifacts={payloadInventoryHash:INPUT.reuse.targetInventoryHash,reviewedInstallation:{artifacts:INPUT.manifests}};
const drift=INPUT.drift;
if(drift==='missing')delete plan.assetReuse;
if(drift==='bad-scope')plan.assetReuse={...plan.assetReuse,originPlanHash:'changed'};
if(drift==='payload')fs.writeFileSync(target+'/fixture.mjs','changed');
if(drift==='mode')fs.chmodSync(target+'/fixture.mjs',0o600);
if(drift==='marker')fs.writeFileSync(target+'/.maintenance-capsule.json','changed');
if(drift==='marker-mode')fs.chmodSync(target+'/.maintenance-capsule.json',0o644);
if(drift==='manifest-whitespace')fs.appendFileSync(target+'/app-manifest.json','\n');
if(drift==='extra')fs.writeFileSync(target+'/foreign','foreign');
if(drift==='extra-directory')fs.mkdirSync(target+'/foreign');
if(drift==='missing-file')fs.unlinkSync(target+'/fixture.mjs');
if(drift==='hardlink')fs.linkSync(target+'/fixture.mjs',root+'/outside-link');
if(drift==='symlink'){fs.renameSync(target+'/fixture.mjs',root+'/original');fs.symlinkSync(root+'/original',target+'/fixture.mjs');}
const snapshot=()=>{const result={};for(const p of fs.readdirSync(target)){const s=fs.lstatSync(target+'/'+p);result[p]=[s.ino,s.mode,s.nlink,s.size,s.mtimeMs,s.ctimeMs,s.isFile()?sha(fs.readFileSync(target+'/'+p)):null];}return JSON.stringify(result);};
const before=snapshot();
if(drift==='none'){const result=stage({artifacts,plan},{packageDirectory:package,targetDirectory:target});assert.equal(result.status,'PAYLOAD_REUSED_COMPLETE_NOT_SELECTED');assert.equal(result.newTargetBytesWritten,0);}
else assert.throws(()=>stage({artifacts,plan},{packageDirectory:package,targetDirectory:target}));
assert.equal(snapshot(),before);assert.equal(writes,0);
'''
   data={'root':str(root),'target':str(target),'package':str(package),'source':source,'manifests':manifests,'reuse':reuse,'drift':drift}
   code='const INPUT=JSON.parse(Buffer.from('+json.dumps(base64.b64encode(json.dumps(data).encode()).decode())+',"base64"));\n'+script
   r=subprocess.run(('node','-e',code),capture_output=True,timeout=10);self.assertEqual(r.returncode,0,r.stderr.decode())
 def test_real_complete_target_is_reused_without_any_write(self):self.scenario()
 def test_missing_or_changed_asset_policy_never_falls_back_to_copy(self):
  for drift in ('missing','bad-scope'):self.scenario(drift)
 def test_payload_mode_marker_and_raw_role_manifest_drift_refuse_readonly(self):
  for drift in ('payload','mode','marker','marker-mode','manifest-whitespace'):self.scenario(drift)
 def test_full_set_symlink_hardlink_and_missing_file_refuse_readonly(self):
  for drift in ('extra','extra-directory','missing-file','hardlink','symlink'):self.scenario(drift)

class ProtectedPackageTests(unittest.TestCase):
 def fixture(self,root):
  e=BuildTests().entry();package=root/'package';package.mkdir(mode=0o700);(package/'metadata').mkdir(mode=0o700);(package/'payload').mkdir(mode=0o700)
  raw=b'isolated protected payload';payload=package/'payload/fixture.mjs';payload.write_bytes(raw);payload.chmod(0o644)
  inventory={'fixture.mjs':{'sha256':sha(raw),'bytes':len(raw),'mode':0o644}};(package/'metadata/PAYLOAD_INVENTORY.json').write_bytes(canon(inventory));(package/'metadata/PAYLOAD_INVENTORY.json').chmod(0o644)
  files={str(p.relative_to(package)):sha(p.read_bytes()) for p in package.rglob('*') if p.is_file()}
  old=canon({'payloadFiles':files});closure={n:{'sha256':pin,'mode':0o644,'bytes':len((package/n).read_bytes())} for n,pin in files.items()}
  e.ASSET_REUSE={**e.ASSET_REUSE,'packageRoot':str(package),'packageClosureHash':sha(canon(closure)),'targetOriginCapsuleHash':sha(old)}
  return e,package,{'payloadFiles':files,'planTemplate':{'assetReuse':e.ASSET_REUSE}},old
 def capture(self,e,manifest,old):
  old_read=e.secure_read;old_stat=os.fstat;old_lstat=Path.lstat
  class RootMetadata:
   def __init__(self,v):self.value=v
   def __getattr__(self,n):return 0 if n=='st_uid' else getattr(self.value,n)
  def read(path,*args,**kw):
   if str(path)=='/usr/lib/r16-maintenance/recovery-r9/SOURCE_FREEZE.json':return old
   return old_read(path,*args,**kw)
  with patch.object(e,'secure_read',side_effect=read),patch.object(e.os,'fstat',side_effect=lambda fd:RootMetadata(old_stat(fd))),patch.object(Path,'lstat',lambda path:RootMetadata(old_lstat(path))),patch.object(e,'ensure_file',side_effect=AssertionError('PROTECTED_PACKAGE_MUST_NOT_BE_WRITTEN')):
   return e.verify_reused_package(manifest)
 def test_real_protected_package_is_verified_in_place_without_copy(self):
  with tempfile.TemporaryDirectory(dir=Path.home()) as tmp:
   e,package,manifest,old=self.fixture(Path(tmp));before={str(p.relative_to(package)):(p.stat().st_ino,p.stat().st_mode,p.read_bytes()) for p in package.rglob('*') if p.is_file()}
   result=self.capture(e,manifest,old);self.assertEqual(result['newPackageBytesWritten'],0);self.assertEqual(result['packageFiles'],2)
   self.assertEqual(before,{str(p.relative_to(package)):(p.stat().st_ino,p.stat().st_mode,p.read_bytes()) for p in package.rglob('*') if p.is_file()})
 def test_byte_mode_hardlink_extra_file_and_empty_directory_all_refuse(self):
  for drift in ('byte','mode','hardlink','extra','directory'):
   with self.subTest(drift=drift),tempfile.TemporaryDirectory(dir=Path.home()) as tmp:
    e,package,manifest,old=self.fixture(Path(tmp));payload=package/'payload/fixture.mjs'
    if drift=='byte':payload.write_bytes(b'changed')
    elif drift=='mode':payload.chmod(0o600)
    elif drift=='hardlink':os.link(payload,Path(tmp)/'foreign-link')
    elif drift=='extra':(package/'foreign').write_bytes(b'foreign')
    else:(package/'foreign').mkdir(mode=0o700)
    with self.assertRaises(e.Refused):self.capture(e,manifest,old)
 def test_unmatched_policy_and_origin_capsule_refuse(self):
  for drift in ('policy','origin'):
   with self.subTest(drift=drift),tempfile.TemporaryDirectory(dir=Path.home()) as tmp:
    e,package,manifest,old=self.fixture(Path(tmp))
    if drift=='policy':manifest['planTemplate']['assetReuse']={}
    else:old+=b' '
    with self.assertRaises(e.Refused):self.capture(e,manifest,old)

if __name__=='__main__':unittest.main()
