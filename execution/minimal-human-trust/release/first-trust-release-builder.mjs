// FIRST_TRUST_BOOTSTRAP_R1: stage exact cryptographic outputs for a trusted
// root-only, single-use publisher. No CLI, no credential loading, no install,
// no Owner shutdown, no business activation and no production side effects.
import {createHash} from 'node:crypto';
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
 * both original read-UNKNOWN states, and the exact signed stop barrier.
 */
export function deriveExactR17Release({
  sourceRelease,reviewManifest,reviewedManifestHash,now=Date.now(),
  readFile=protectedRuntimeFile
}){
  need(sourceRelease?.schema==='r16.release.v1'&&
    sourceRelease.id==='r16-daily-20261012-r15','FIRST_TRUST_OLD_RELEASE');
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
  const versions={};
  for(const role of ROLES){
    validateRuntimeManifest(m.artifacts[role],role);
    versions[role]=runtimeVersion(m.artifacts[role],role);
  }
  const seen=new Set();
  for(const file of m.localFiles){
    need(file&&Object.keys(file).sort().join(',')==='artifactPath,path,role,sha256'&&
      ROLES.includes(file.role)&&hash(file.sha256)&&
      typeof file.path==='string'&&
      (file.path.startsWith('/opt/r16/releases/r16-daily-20261012-r17/')||
       file.path.startsWith('/usr/lib/r16-owner/'))&&
      !file.path.includes('..')&&!file.path.includes('\\')&&
      !file.path.includes('\0')&&
      !seen.has(file.path)&&
      m.artifacts[file.role].files[file.artifactPath]===file.sha256,
      'FIRST_TRUST_FILE_SCOPE');
    seen.add(file.path);
    need(sha(readFile(file.path))===file.sha256,'FIRST_TRUST_FILE_DRIFT');
  }
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
  readFile=protectedRuntimeFile,now=Date.now(),
}){
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
  const enrollment=signed(enrollmentBody,enrollmentSigningKey);
  verified(enrollment,firstTrust.trustRoots.enrollmentAuthorityPublicKey,
    'mht.human-enrollment.v1');
  return Object.freeze({schema:'mht.first-trust-staged-signatures.v1',
    status:'SIGNED_STAGED_NOT_INSTALLED',oldReleaseId:oldRelease.id,
    reviewedManifestHash:admission.reviewedManifestHash,
    osApprovalReceiptHash:admission.humanApprovalReceiptHash,
    firstTrustAdmissionDigest:admission.admissionDigest,
    release,enrollment,
    grantUnchanged:true,mayInstall:false,mayActivateBusiness:false,
    mayHandoffIssuer:false,maySettleUnknown:false});
}
