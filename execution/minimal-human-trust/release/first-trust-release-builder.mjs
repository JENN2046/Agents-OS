// FIRST_TRUST_BOOTSTRAP_R1: stage exact cryptographic outputs for a trusted
// root-only, single-use publisher. No CLI, no credential loading, no install,
// no Owner shutdown, no business activation and no production side effects.
import {createHash} from 'node:crypto';
import {inspectSourceRelease} from '../authority/source-baseline.mjs';
import {canonical,digest,publicKey,verified,verifyRelease,
  signed,exportPublicKey,ACTIONS,ROLES} from '../src/lease-core.mjs';
import {validateRuntimeManifest,runtimeVersion,
  protectedRuntimeFile} from '../authority/runtime-manifest.mjs';
import {inspectFirstTrustRecoveryPublication} from './first-trust-recovery-admission.mjs';

const fail=c=>{throw Object.assign(new Error(c),{code:c});};
const need=(x,c='FIRST_TRUST_SIGNER_REJECTED')=>{if(!x)fail(c);};
const same=(a,b)=>canonical(a)===canonical(b);
const hash=s=>typeof s==='string'&&/^[a-f0-9]{64}$/.test(s);
const sha=b=>createHash('sha256').update(b).digest('hex');

/** Pure, unsigned, closed-form R17 release body. This function cannot sign.
 * A parent trusted root service must already have inspected Human confirmation,
 * both original read-UNKNOWN states and the exact stage-only plan. The signed
 * stop barrier remains mandatory before installation/handoff, not staging.
 */
export function deriveExactR17Release({
  sourceRelease,reviewManifest,reviewedManifestHash,now=Date.now(),
  readFile=protectedRuntimeFile
}){
  inspectSourceRelease(sourceRelease);
  const m=reviewManifest;
  need(m?.schema==='r16.reviewed-installation.v1'&&
    m.releaseId==='r16-daily-20261012-r17'&&
    digest(m)===reviewedManifestHash&&hash(reviewedManifestHash)&&
    Number.isSafeInteger(m.issuedAt)&&Number.isSafeInteger(m.notAfter)&&
    Number.isSafeInteger(now)&&m.issuedAt>=sourceRelease.issuedAt&&
    m.issuedAt<=now&&now-m.issuedAt<=300000&&
    m.notAfter>now&&m.notAfter>m.issuedAt&&
    m.notAfter-m.issuedAt<=7*86400000,'FIRST_TRUST_RELEASE_WINDOW');
  need(m.artifacts&&same(Object.keys(m.artifacts).sort(),ROLES)&&
    Array.isArray(m.localFiles)&&m.localFiles.length>0&&
    typeof readFile==='function','FIRST_TRUST_REVIEW_FORMAT');
  const versions={},physicalFiles=new Map();
  let expectedBindings=0;
  for(const role of ROLES){
    validateRuntimeManifest(m.artifacts[role],role);
    versions[role]=runtimeVersion(m.artifacts[role],role);
    for(const [artifactPath,expected] of Object.entries(m.artifacts[role].files)){
      need(!/[\x00-\x1f\x7f]/.test(artifactPath),'FIRST_TRUST_FILE_SCOPE');
      const target='/opt/r16/releases/r16-daily-20261012-r17/'+artifactPath;
      need(!physicalFiles.has(target)||physicalFiles.get(target)===expected,
        'FIRST_TRUST_ROLE_OVERLAP');
      physicalFiles.set(target,expected);
      expectedBindings++;
    }
  }
  need(m.localFiles.length===expectedBindings,'FIRST_TRUST_FILE_COVERAGE');
  const seen=new Set();
  for(const file of m.localFiles){
    need(file&&Object.keys(file).sort().join(',')==='artifactPath,path,role,sha256'&&
      ROLES.includes(file.role)&&hash(file.sha256)&&
      typeof file.artifactPath==='string'&&
      file.path==='/opt/r16/releases/r16-daily-20261012-r17/'+file.artifactPath&&
      Object.hasOwn(m.artifacts[file.role].files,file.artifactPath)&&
      !seen.has(file.role+'\0'+file.artifactPath)&&
      m.artifacts[file.role].files[file.artifactPath]===file.sha256,
      'FIRST_TRUST_FILE_SCOPE');
    seen.add(file.role+'\0'+file.artifactPath);
  }
  // The full role binding set is required, but shared physical paths are read
  // exactly once only after all mappings and overlaps have been validated.
  for(const [target,expected] of physicalFiles)
    need(sha(readFile(target))===expected,'FIRST_TRUST_FILE_DRIFT');
  need(same(sourceRelease.formats,['r16.workspace.v1'])&&
    sourceRelease.permissionVersion===1&&same(sourceRelease.actions,ACTIONS),
    'FIRST_TRUST_PERMISSION_DRIFT');
  return Object.freeze({schema:'r16.release.v1',id:m.releaseId,
    issuedAt:m.issuedAt,notAfter:m.notAfter,
    formats:sourceRelease.formats,versions,actions:sourceRelease.actions,
    permissionVersion:sourceRelease.permissionVersion});
}

/** This cryptographic operation must be called ONLY by a separately installed
 * root-only one-shot service after an immutable intent has been durably reserved.
 * The Release and enrollment private keys are never read by this module; they
 * are passed from pre-verified systemd credential sources by that service.
 * Its outputs are STAGED, never an authorization to install or enter business.
 */
export function signFirstTrustRecoveryArtifacts({
  firstTrust,existingR15Evidence,verifyCrownCall,
  releaseSigningKey,enrollmentSigningKey,
  readFile=protectedRuntimeFile,now=Date.now(),guard=()=>{},
}){
  need(typeof guard==='function','FIRST_TRUST_SIGN_GUARD_REQUIRED');
  const admission=inspectFirstTrustRecoveryPublication({
    firstTrust,existingR15Evidence,verifyCrownCall});
  need(releaseSigningKey?.type==='private'&&enrollmentSigningKey?.type==='private'&&
    exportPublicKey(releaseSigningKey)===firstTrust.trustRoots.releasePublicKey&&
    exportPublicKey(enrollmentSigningKey)===firstTrust.trustRoots.enrollmentAuthorityPublicKey&&
    exportPublicKey(releaseSigningKey)!==exportPublicKey(enrollmentSigningKey),
    'FIRST_TRUST_KEY_ORIGIN');
  const oldRelease=verified(firstTrust.sourceRelease,
    firstTrust.trustRoots.releasePublicKey,'r16.release.v1');
  const body=deriveExactR17Release({sourceRelease:oldRelease,
    reviewManifest:firstTrust.reviewManifest,
    reviewedManifestHash:admission.reviewedManifestHash,now,readFile});
  guard();
  const release=signed(body,releaseSigningKey);
  verifyRelease(release,firstTrust.trustRoots.releasePublicKey,
    {versions:body.versions,actions:ACTIONS,now});
  const enrolledAt=now;
  const enrollmentBody={schema:'mht.human-enrollment.v1',enrolledAt,
    expiresAt:admission.enrollmentExpiresAt,
    grantId:admission.grantId,grantHash:admission.grantHash,
    humanPublicKey:admission.humanPublicKey,humanUid:admission.humanUid,
    humanSubject:'local-human:1000',releaseHash:digest(release),releaseId:body.id};
  need(enrollmentBody.expiresAt>enrolledAt,'FIRST_TRUST_ENROLLMENT_EXPIRED');
  guard();
  const enrollment=signed(enrollmentBody,enrollmentSigningKey);
  verified(enrollment,firstTrust.trustRoots.enrollmentAuthorityPublicKey,
    'mht.human-enrollment.v1');
  return Object.freeze({schema:'mht.first-trust-staged-signatures.v2',
    status:'SIGNED_STAGED_NOT_INSTALLED',oldReleaseId:oldRelease.id,
    reviewedManifestHash:admission.reviewedManifestHash,
    osApprovalReceiptHash:admission.humanApprovalReceiptHash,
    firstTrustAdmissionDigest:admission.admissionDigest,
    stageAuthorizationHash:admission.stageAuthorizationHash,
    release,enrollment,
    grantUnchanged:true,mayInstall:false,mayActivateBusiness:false,
    mayHandoffIssuer:false,maySettleUnknown:false});
}
