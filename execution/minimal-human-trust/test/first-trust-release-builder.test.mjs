import test from 'node:test';
import assert from 'node:assert/strict';
import {createHash,generateKeyPairSync} from 'node:crypto';
import {ACTIONS,ROLES,digest,verified,signed,exportPublicKey} from '../src/lease-core.mjs';
import {runtimeVersion} from '../authority/runtime-manifest.mjs';
import {deriveExactR17Release,signFirstTrustRecoveryArtifacts}
  from '../release/first-trust-release-builder.mjs';

const sha=b=>createHash('sha256').update(b).digest('hex');
function fixture(){
 const now=1792000000000;
 const old={schema:'r16.release.v1',id:'r16-daily-20261012-r15',
   issuedAt:now-86400000,notAfter:now-1000,formats:['r16.workspace.v1'],
   versions:{app:digest('oldapp'),bridge:digest('oldbridge'),native:digest('oldnative')},
   actions:ACTIONS,permissionVersion:1};
 const bytes=Buffer.from('reviewed harmless fixture bytes');
 const artifacts={},localFiles=[];
 for(const role of ROLES){
   const entry=role+'/main.mjs',hash=sha(bytes);
   artifacts[role]={schema:'r16.runtime-code.v1',role,entry,files:{[entry]:hash}};
   localFiles.push({artifactPath:entry,
     path:'/opt/r16/releases/r16-daily-20261012-r17/'+entry,role,sha256:hash});
 }
 const manifest={schema:'r16.reviewed-installation.v1',releaseId:'r16-daily-20261012-r17',
   issuedAt:now-1000,notAfter:now+86400000,artifacts,localFiles};
 const readFile=()=>Buffer.from(bytes);
 const arg={sourceRelease:old,reviewManifest:manifest,reviewedManifestHash:digest(manifest),now,readFile};
 return {arg,manifest,old,now,bytes};
}
const reject=fn=>assert.throws(fn);
test('only exact reviewed R17 body can be produced without signing authority',()=>{
 const f=fixture(),body=deriveExactR17Release(f.arg);
 assert.equal(body.id,'r16-daily-20261012-r17');
 assert.equal(body.permissionVersion,1);
 assert.deepEqual(body.actions,ACTIONS);
 for(const role of ROLES)assert.equal(body.versions[role],runtimeVersion(f.manifest.artifacts[role],role));
 const key=generateKeyPairSync('ed25519').privateKey;
 const env=signed(body,key);
 assert.deepEqual(verified(env,exportPublicKey(key),'r16.release.v1'),body);
});
test('review hash drift is rejected before reading staged files',()=>{
 const f=fixture();f.arg.reviewedManifestHash=digest('other');
 reject(()=>deriveExactR17Release(f.arg));
});
test('target different from exact R17 is rejected',()=>{
 const f=fixture();f.manifest.releaseId='r16-daily-20261012-r18';
 f.arg.reviewedManifestHash=digest(f.manifest);
 reject(()=>deriveExactR17Release(f.arg));
});
test('root-staged file bytes must match manifest hash',()=>{
 const f=fixture();f.arg.readFile=()=>Buffer.from('changed');
 reject(()=>deriveExactR17Release(f.arg));
});
test('refuse missing role or malformed role manifest',()=>{
 const f=fixture();delete f.manifest.artifacts.native;
 f.arg.reviewedManifestHash=digest(f.manifest);
 reject(()=>deriveExactR17Release(f.arg));
});
test('refuse a target path belonging to a different artifact',()=>{
 const f=fixture();f.manifest.localFiles[1].path=f.manifest.localFiles[0].path;
 f.arg.reviewedManifestHash=digest(f.manifest);
 reject(()=>deriveExactR17Release(f.arg));
});
function overlappingFixture(){
 const f=fixture(),artifactPath='src/shared.mjs',hash=sha(f.bytes);
 for(const role of ROLES){
   f.manifest.artifacts[role].files[artifactPath]=hash;
   f.manifest.localFiles.push({role,artifactPath,sha256:hash,
     path:'/opt/r16/releases/r16-daily-20261012-r17/'+artifactPath});
 }
 f.arg.reviewedManifestHash=digest(f.manifest);
 return f;
}
function refresh(f){f.arg.reviewedManifestHash=digest(f.manifest);}
function rejectBeforeRead(f,code){
 let reads=0;f.arg.readFile=()=>{reads++;return f.bytes;};
 assert.throws(()=>deriveExactR17Release(f.arg),{code});
 assert.equal(reads,0);
}
test('complete overlapping role bindings read every distinct physical file once',()=>{
 const f=overlappingFixture(),reads=[];
 f.manifest.localFiles.reverse();refresh(f);
 f.arg.readFile=target=>{reads.push(target);return f.bytes;};
 const body=deriveExactR17Release(f.arg);
 assert.equal(f.manifest.localFiles.length,6);
 assert.deepEqual(reads.sort(),[
   '/opt/r16/releases/r16-daily-20261012-r17/app/main.mjs',
   '/opt/r16/releases/r16-daily-20261012-r17/bridge/main.mjs',
   '/opt/r16/releases/r16-daily-20261012-r17/native/main.mjs',
   '/opt/r16/releases/r16-daily-20261012-r17/src/shared.mjs',
 ]);
 for(const role of ROLES)
   assert.equal(body.versions[role],runtimeVersion(f.manifest.artifacts[role],role));
});
test('one-file subset cannot approve all three runtime manifests',()=>{
 const f=overlappingFixture();f.manifest.localFiles=f.manifest.localFiles.slice(0,1);refresh(f);
 rejectBeforeRead(f,'FIRST_TRUST_FILE_COVERAGE');
});
test('omitting one shared-role binding is rejected even when its physical file remains mapped',()=>{
 const f=overlappingFixture();f.manifest.localFiles.pop();refresh(f);
 rejectBeforeRead(f,'FIRST_TRUST_FILE_COVERAGE');
});
test('duplicate role/artifact binding cannot replace another required binding',()=>{
 const f=overlappingFixture();f.manifest.localFiles[1]={...f.manifest.localFiles[0]};refresh(f);
 rejectBeforeRead(f,'FIRST_TRUST_FILE_SCOPE');
});
test('overlapping role hashes must agree before any byte is read',()=>{
 const f=overlappingFixture();f.manifest.artifacts.bridge.files['src/shared.mjs']=sha('different');
 f.manifest.localFiles.find(x=>x.role==='bridge'&&x.artifactPath==='src/shared.mjs').sha256=sha('different');
 refresh(f);rejectBeforeRead(f,'FIRST_TRUST_ROLE_OVERLAP');
});
test('foreign mapping and role hash drift are rejected despite a freshly pinned review digest',()=>{
 for(const patch of [
   {artifactPath:'src/foreign.mjs',path:'/opt/r16/releases/r16-daily-20261012-r17/src/foreign.mjs'},
   {role:'bridge'},
   {sha256:sha('foreign bytes')},
 ]){
   const f=overlappingFixture();Object.assign(f.manifest.localFiles[0],patch);refresh(f);
   rejectBeforeRead(f,'FIRST_TRUST_FILE_SCOPE');
 }
});
test('extra physical mapping cannot extend the exact manifest file set',()=>{
 const f=overlappingFixture();f.manifest.localFiles.push({
   role:'app',artifactPath:'app/extra.mjs',sha256:sha(f.bytes),
   path:'/opt/r16/releases/r16-daily-20261012-r17/app/extra.mjs'});refresh(f);
 rejectBeforeRead(f,'FIRST_TRUST_FILE_COVERAGE');
});
test('legacy relocation, suffix mismatch and noncanonical target aliases are refused',()=>{
 for(const path of [
   '/usr/lib/r16-owner/app/main.mjs',
   '/opt/r16/releases/r16-daily-20261012-r17/app/elsewhere.mjs',
   '/opt/r16/releases/r16-daily-20261012-r17//app/main.mjs',
   '/opt/r16/releases/r16-daily-20261012-r17/app/./main.mjs',
 ]){
   const f=fixture();f.manifest.localFiles[0].path=path;refresh(f);
   rejectBeforeRead(f,'FIRST_TRUST_FILE_SCOPE');
 }
});
test('control characters in manifest paths cannot enter physical mappings',()=>{
 const f=fixture(),name='app/main\n.mjs',old=f.manifest.localFiles[0];
 f.manifest.artifacts.app.files={[name]:old.sha256};f.manifest.artifacts.app.entry=name;
 old.artifactPath=name;old.path='/opt/r16/releases/r16-daily-20261012-r17/'+name;refresh(f);
 rejectBeforeRead(f,'FIRST_TRUST_FILE_SCOPE');
});
test('never stage files outside exact reviewed R17 locations',()=>{
 const f=fixture();f.manifest.localFiles[0].path='/tmp/untrusted/main.mjs';
 f.arg.reviewedManifestHash=digest(f.manifest);
 reject(()=>deriveExactR17Release(f.arg));
});
test('no backslash or parent-path traversal',()=>{
 for(const path of [
   '/opt/r16/releases/r16-daily-20261012-r17/../secret.mjs',
   '/opt/r16/releases/r16-daily-20261012-r17/app\\evil.mjs']){
   const f=fixture();f.manifest.localFiles[0].path=path;
   f.arg.reviewedManifestHash=digest(f.manifest);
   reject(()=>deriveExactR17Release(f.arg));
 }
});
test('expired, future and excessive Release windows never sign',()=>{
 for(const patch of [
   {issuedAt:1792000000001},{issuedAt:1791990000000},
   {notAfter:1791999999999},{notAfter:1792000000000+30*86400000}]){
   const f=fixture();Object.assign(f.manifest,patch);
   f.arg.reviewedManifestHash=digest(f.manifest);
   reject(()=>deriveExactR17Release(f.arg));
 }
});
test('legacy permissions cannot be silently expanded by an R17 publisher',()=>{
 const f=fixture();f.old.actions=[...ACTIONS,'run_shell'];
 reject(()=>deriveExactR17Release(f.arg));
});
test('signing without authenticated Human and two original read UNKNOWN proofs fails',()=>{
 const key=generateKeyPairSync('ed25519').privateKey;
 reject(()=>signFirstTrustRecoveryArtifacts({
   firstTrust:{},existingR15Evidence:{},verifyCrownCall:()=>{},
   releaseSigningKey:key,enrollmentSigningKey:key
 }));
});
