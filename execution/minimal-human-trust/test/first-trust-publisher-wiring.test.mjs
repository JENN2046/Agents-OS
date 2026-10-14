import test from 'node:test';
import assert from 'node:assert/strict';
import {generateKeyPairSync,createHash} from 'node:crypto';
import {digest,signed,verified,ACTIONS,ROLES,exportPublicKey} from '../src/lease-core.mjs';
import {runtimeVersion} from '../authority/runtime-manifest.mjs';
import {REVIEWED_SOURCE_FILES,checkReviewedSourceFreeze}
  from '../release/publisher-bootstrap.mjs';
import {verifiedR15CrownVerifier,validateStagedPublisherResult,runPublisherOnce}
  from '../release/publisher-once.mjs';
import {inspectPublisherInputs} from '../release/publisher-inputs.mjs';

const pair=()=>generateKeyPairSync('ed25519').privateKey;
const sha=b=>createHash('sha256').update(b).digest('hex');
const refuse=f=>assert.throws(f);
function fixture(){
 const now=1792040000000,releaseKey=pair(),enrollmentKey=pair(),issuerKey=pair(),humanKey=pair();
 const peers=Object.fromEntries(ROLES.map(role=>[role,{id:'peer-'+role,publicKey:exportPublicKey(pair())}]));
 const grant=signed({schema:'r16.workspace.v1',id:'r16-projects-daily',
   version:1,createdAt:now-86400000,
   workspace:{id:'ws_8c7dd971e518',root:'/home/jenn/AGENTS_OS_Workspace/projects',dev:1,ino:2},
   actions:ACTIONS,channel:'main',peers},issuerKey);
 const roots={releasePublicKey:exportPublicKey(releaseKey),
   enrollmentAuthorityPublicKey:exportPublicKey(enrollmentKey),
   issuerPublicKey:exportPublicKey(issuerKey)};
 const r17={schema:'r16.release.v1',id:'r16-daily-20261012-r17',
   issuedAt:now-1000,notAfter:now+86400000,formats:['r16.workspace.v1'],
   versions:Object.fromEntries(ROLES.map(x=>[x,digest('version-'+x)])),
   actions:ACTIONS,permissionVersion:1};
 const release=signed(r17,releaseKey);
 const admission={admission:{reviewedManifestHash:digest('reviewed-r17'),
   humanApprovalReceiptHash:digest('human-os-approval'),
   admissionDigest:digest('first-trust-inspected'),grantId:grant.body.id,
   grantHash:digest(grant),humanPublicKey:exportPublicKey(humanKey),
   humanUid:1000}};
 const enrolled=signed({schema:'mht.human-enrollment.v1',
   enrolledAt:now,expiresAt:now+86400000,
   grantId:grant.body.id,grantHash:digest(grant),
   humanPublicKey:exportPublicKey(humanKey),humanUid:1000,
   humanSubject:'local-human:1000',releaseHash:digest(release),
   releaseId:r17.id},enrollmentKey);
 const signedResult={schema:'mht.first-trust-staged-signatures.v1',
   status:'SIGNED_STAGED_NOT_INSTALLED',
   oldReleaseId:'r16-daily-20261012-r15',
   reviewedManifestHash:admission.admission.reviewedManifestHash,
   osApprovalReceiptHash:admission.admission.humanApprovalReceiptHash,
   firstTrustAdmissionDigest:admission.admission.admissionDigest,
   release,enrollment:enrolled,grantUnchanged:true,mayInstall:false,
   mayActivateBusiness:false,mayHandoffIssuer:false,maySettleUnknown:false};
 const pub={grant};
 return {now,grant,roots,releaseKey,enrollmentKey,issuerKey,humanKey,r17,
   release,enrolled,admission,signedResult,pub};
}
test('publisher validates independently signed R17 and Human enrollment only as staged',()=>{
 const f=fixture();
 assert.equal(validateStagedPublisherResult(f.signedResult,{pub:f.pub,roots:f.roots,
   admission:f.admission,now:f.now}),true);
});
test('an invalid enrollment signer cannot be smuggled into signed stage',()=>{
 const f=fixture();f.signedResult.enrollment=signed(f.signedResult.enrollment.body,pair());
 refuse(()=>validateStagedPublisherResult(f.signedResult,{
   pub:f.pub,roots:f.roots,admission:f.admission,now:f.now}));
});
test('enrolled identity cannot be changed after Human reviewed exact public key',()=>{
 const f=fixture();
 f.signedResult.enrollment=signed({...f.enrolled.body,humanPublicKey:exportPublicKey(pair())},f.enrollmentKey);
 refuse(()=>validateStagedPublisherResult(f.signedResult,{
   pub:f.pub,roots:f.roots,admission:f.admission,now:f.now}));
});
test('changing verified R17 permissions is always rejected',()=>{
 const f=fixture();
 const wrong=signed({...f.r17,permissionVersion:2},f.releaseKey);
 f.signedResult.release=wrong;
 refuse(()=>validateStagedPublisherResult(f.signedResult,{
   pub:f.pub,roots:f.roots,admission:f.admission,now:f.now}));
});
test('staged release cannot claim it has been installed or activated',()=>{
 const f=fixture();f.signedResult.mayInstall=true;
 refuse(()=>validateStagedPublisherResult(f.signedResult,{
   pub:f.pub,roots:f.roots,admission:f.admission,now:f.now}));
});
test('an unsigned foreign Release cannot be passed to output verifier',()=>{
 const f=fixture();f.signedResult.release=signed(f.r17,pair());
 refuse(()=>validateStagedPublisherResult(f.signedResult,{
   pub:f.pub,roots:f.roots,admission:f.admission,now:f.now}));
});
test('root-reviewed source freeze requires all required transitive files and hashes',()=>{
 const bytes=Buffer.from('reviewed-synthetic-code-v1');
 const manifest={schema:'mht.first-trust-code-freeze.v1',
   sourceCommit:'a'.repeat(40),
   files:Object.fromEntries(REVIEWED_SOURCE_FILES.map(file=>[file,sha(bytes)]))};
 let count=0;
 const result=checkReviewedSourceFreeze({manifest,read:()=>{count++;return bytes;}});
 assert.equal(result.filesChecked,REVIEWED_SOURCE_FILES.length);
 assert.equal(count,REVIEWED_SOURCE_FILES.length);
});
test('missing publisher itself in protected source freeze fails closed',()=>{
 const bytes=Buffer.from('synthetic'),
  manifest={schema:'mht.first-trust-code-freeze.v1',sourceCommit:'b'.repeat(40),
    files:Object.fromEntries(REVIEWED_SOURCE_FILES.map(file=>[file,sha(bytes)]))};
 delete manifest.files['release/publisher-bootstrap.mjs'];
 refuse(()=>checkReviewedSourceFreeze({manifest,read:()=>bytes}));
});
test('tampered transitive dependency fails before dynamic import and before key access',()=>{
 const bytes=Buffer.from('synthetic'),
  manifest={schema:'mht.first-trust-code-freeze.v1',sourceCommit:'b'.repeat(40),
    files:Object.fromEntries(REVIEWED_SOURCE_FILES.map(file=>[file,sha(bytes)]))};
 refuse(()=>checkReviewedSourceFreeze({
   manifest,read:file=>file.endsWith('lease-core.mjs')?Buffer.from('tampered'):bytes}));
});
test('real installed Crown verifier path and R15 manifest binding are enforced',async()=>{
 const f=fixture(),bytes=Buffer.from('synthetic-pinned-crown-verifier');
 const target='app/upstream/src/project-forge-crown-transport.mjs';
 const manifest={schema:'r16.runtime-code.v1',role:'app',entry:target,files:{[target]:sha(bytes)}};
 const r15=signed({...f.r17,id:'r16-daily-20261012-r15',
   versions:{...f.r17.versions,app:runtimeVersion(manifest,'app')}},f.releaseKey);
 const pub={release:r15,releasePublicKey:f.roots.releasePublicKey,
   versions:r15.body.versions};
 const trusted=async()=>({verifyCall:()=>({validated:true})});
 const readProtected=file=>file.endsWith('app-manifest.json')?
   Buffer.from(JSON.stringify(manifest)):bytes;
 const verifyCall=await verifiedR15CrownVerifier({pub,readProtected,importModule:trusted});
 assert.deepEqual(verifyCall(),{validated:true});
 await assert.rejects(()=>verifiedR15CrownVerifier({pub,importModule:trusted,
   readProtected:file=>file.endsWith('app-manifest.json')?
     Buffer.from(JSON.stringify(manifest)):Buffer.from('tampered')}));
});
test('unprivileged process cannot run root-only publisher',async()=>{
 await assert.rejects(()=>runPublisherOnce({frozenManifest:{schema:'mht.first-trust-code-freeze.v1'},
    frozenRawDigest:digest('fixture')}));
});
test('unsigned or incomplete OS inputs cannot reach the protected sign operation',()=>{
 const plan={schema:'mht.first-trust-publisher-plan.v1'};
 refuse(()=>inspectPublisherInputs({plan,roots:{},publicConfig:{},
   evidence:{},firstTrust:{},verifyCrownCall:()=>{}}));
});
