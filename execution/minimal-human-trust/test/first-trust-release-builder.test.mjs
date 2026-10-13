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
test('refuse duplicate staged path',()=>{
 const f=fixture();f.manifest.localFiles[1].path=f.manifest.localFiles[0].path;
 f.arg.reviewedManifestHash=digest(f.manifest);
 reject(()=>deriveExactR17Release(f.arg));
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
