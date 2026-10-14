// FIRST_TRUST_BOOTSTRAP_R1: one exact OS-protected staged R15 -> R17 signer.
// Installed only after physical Human review of the exact source freeze.
// No request parameters, no shell, no Owner stop, no installation/activation.
import fs from 'node:fs';
import path from 'node:path';
import {createHash} from 'node:crypto';
import {pathToFileURL} from 'node:url';
import {canonical,digest,verified,verifyRelease,ACTIONS,ROLES} from '../src/lease-core.mjs';
import {protectedRuntimeFile,runtimeVersion} from '../authority/runtime-manifest.mjs';
import {readPublisherPrivateKeys} from './publisher-credential.mjs';
import {inspectPublisherInputs} from './publisher-inputs.mjs';
import {signFirstTrustRecoveryArtifacts} from './first-trust-release-builder.mjs';
import {stagePublisherOnce} from './publisher-transaction.mjs';

const PUB='/run/r16-owner/public-config.json';
const BASE='/etc/minimal-human-trust/';
const PLAN=BASE+'first-trust-publication.json';
const ROOTS=BASE+'trust-roots.json';
const REVIEW=BASE+'reviewed-installation.json';
const POLICY=BASE+'human-policy.json';
const PROPOSAL=BASE+'human-pending.json';
const EVIDENCE=BASE+'first-trust-evidence.json';
const OLD_ISSUER='/var/lib/r16-owner/issuer/state.json';
const TX='/var/lib/minimal-human-trust/first-trust-publication';
const R15='/opt/r16/releases/r16-daily-20261012-r15';
const CROWN_REL='app/upstream/src/project-forge-crown-transport.mjs';
const fail=c=>{throw Object.assign(new Error(c),{code:c});};
const need=(x,c='FIRST_TRUST_PUBLISHER_REJECTED')=>{if(!x)fail(c);};
const same=(a,b)=>canonical(a)===canonical(b);
const sha=b=>createHash('sha256').update(b).digest('hex');
const readJson=(file,read=protectedRuntimeFile)=>JSON.parse(read(file).toString());

export async function verifiedR15CrownVerifier({
 pub,readProtected=protectedRuntimeFile,importModule=url=>import(url)
}){
 const r=verified(pub.release,pub.releasePublicKey,'r16.release.v1');
 need(r.id==='r16-daily-20261012-r15','PUBLISHER_R15_RELEASE');
 verifyRelease(pub.release,pub.releasePublicKey,{
  versions:pub.versions,actions:ACTIONS,now:r.issuedAt});
 const manifest=readJson(R15+'/app-manifest.json',readProtected);
 need(manifest.files?.[CROWN_REL]&&
   runtimeVersion(manifest,'app')===r.versions.app,'PUBLISHER_OLD_APP_MANIFEST');
 const file=R15+'/'+CROWN_REL;
 need(sha(readProtected(file))===manifest.files[CROWN_REL],
   'PUBLISHER_CROWN_CODE_CHANGED');
 const imported=await importModule(pathToFileURL(file).href);
 need(typeof imported.verifyCall==='function','PUBLISHER_CROWN_VERIFIER_MISSING');
 return imported.verifyCall;
}

export function validateStagedPublisherResult(result,{pub,roots,admission,reviewManifest,now}){
 need(result?.schema==='mht.first-trust-staged-signatures.v1'&&
   result.status==='SIGNED_STAGED_NOT_INSTALLED'&&
   result.oldReleaseId==='r16-daily-20261012-r15'&&
   result.reviewedManifestHash===admission.admission.reviewedManifestHash&&
   result.osApprovalReceiptHash===admission.admission.humanApprovalReceiptHash&&
   result.firstTrustAdmissionDigest===admission.admission.admissionDigest&&
   result.grantUnchanged===true&&result.mayInstall===false&&
   result.mayActivateBusiness===false&&result.mayHandoffIssuer===false&&
   result.maySettleUnknown===false,'PUBLISHER_OUTPUT_SCOPE');
 // A valid Release signature does NOT by itself prove that its payload is
 // the exact Human-reviewed R17. Re-derive all signed version/clock fields
 // from the root-pinned R17 installation manifest on every result readback.
 need(reviewManifest?.schema==='r16.reviewed-installation.v1'&&
   reviewManifest.releaseId==='r16-daily-20261012-r17'&&
   digest(reviewManifest)===admission.admission.reviewedManifestHash&&
   reviewManifest.artifacts&&same(Object.keys(reviewManifest.artifacts).sort(),ROLES),
   'PUBLISHER_REVIEW_CHANGED');
 const previous=verified(pub.release,roots.releasePublicKey,'r16.release.v1');
 const signedGrant=verified(pub.grant,roots.issuerPublicKey,'r16.workspace.v1');
 need(previous.id==='r16-daily-20261012-r15'&&
   signedGrant.id==='r16-projects-daily'&&
   digest(pub.grant)===admission.admission.grantHash,
   'PUBLISHER_TRUST_ROOT_DRIFT');
 verifyRelease(pub.release,roots.releasePublicKey,
   {versions:previous.versions,actions:signedGrant.actions,now:previous.issuedAt});
 const expectedVersions=Object.fromEntries(ROLES.map(role=>
   [role,runtimeVersion(reviewManifest.artifacts[role],role)]));
 const signedRelease=verified(result.release,roots.releasePublicKey,'r16.release.v1');
 need(same(signedRelease.versions,expectedVersions)&&
   signedRelease.issuedAt===reviewManifest.issuedAt&&
   signedRelease.notAfter===reviewManifest.notAfter&&
   signedRelease.issuedAt>=previous.issuedAt&&
   same(signedRelease.formats,previous.formats)&&
   same(signedRelease.actions,previous.actions)&&
   signedRelease.permissionVersion===previous.permissionVersion,
   'PUBLISHER_RELEASE_TARGET_DRIFT');
 need(signedRelease.id==='r16-daily-20261012-r17'&&
   signedRelease.issuedAt<=now&&
   same(signedRelease.actions,ACTIONS)&&
   signedRelease.permissionVersion===1,'PUBLISHER_RELEASE_DRIFT');
 verifyRelease(result.release,roots.releasePublicKey,{
   versions:signedRelease.versions,actions:ACTIONS,now});
 const enrolled=verified(result.enrollment,roots.enrollmentAuthorityPublicKey,'mht.human-enrollment.v1');
 need(enrolled.releaseId===signedRelease.id&&
   enrolled.releaseHash===digest(result.release)&&
   enrolled.grantId===admission.admission.grantId&&
   enrolled.grantHash===admission.admission.grantHash&&
   enrolled.humanPublicKey===admission.admission.humanPublicKey&&
   enrolled.humanUid===1000&&enrolled.humanSubject==='local-human:1000'&&
   enrolled.enrolledAt<=now&&enrolled.expiresAt>now&&
   enrolled.expiresAt===admission.admission.enrollmentExpiresAt,
   'PUBLISHER_ENROLLMENT_DRIFT');
 need(pub.grant?.body?.id===enrolled.grantId,'PUBLISHER_GRANT_DRIFT');
 return true;
}

/** Root-only service entry. A synthetic test may supply dependencies, but the
 * installed service uses NO caller arguments, environment paths or identities.
 * Every source is read through a fixed OS-root-protected pathname.
 */
export async function runPublisherOnce({
 frozenManifest,frozenRawDigest,
 readProtected=protectedRuntimeFile,
 now=Date.now,
 importModule=url=>import(url),
 readKeys=readPublisherPrivateKeys,
 stage=stagePublisherOnce,
}={}){
 need(process.geteuid()===0&&process.argv.length===2,'PUBLISHER_ROOT_REQUIRED');
 need(frozenManifest?.schema==='mht.first-trust-code-freeze.v1'&&
   typeof frozenRawDigest==='string'&&/^[a-f0-9]{64}$/.test(frozenRawDigest),
   'PUBLISHER_CODE_FREEZE');
 const t=now(),plan=readJson(PLAN,readProtected);
 const roots=readJson(ROOTS,readProtected);
 need(digest(frozenManifest)===plan.sourceFreezeDigest,'PUBLISHER_SOURCE_FREEZE_CHANGED');
 const pub=readJson(PUB,readProtected);
 const reviewManifest=readJson(REVIEW,readProtected);
 const proposal=readJson(PROPOSAL,readProtected);
 const policy=readJson(POLICY,readProtected);
 const evidence=readJson(EVIDENCE,readProtected);
 need(evidence?.schema==='mht.first-trust-evidence.v1'&&
   Object.keys(evidence).sort().join(',')===
    'cloudDelivery,existingR15Evidence,schema,stopReceipts','PUBLISHER_EVIDENCE_SHAPE');
 const crown=await verifiedR15CrownVerifier({pub,readProtected,importModule});
 const firstTrust={proposal,policy,trustRoots:roots,sourceRelease:pub.release,
   sourceGrant:pub.grant,reviewManifest,now:t,readProtected};
 const inspected=inspectPublisherInputs({
   plan,roots,publicConfig:pub,evidence,firstTrust,
   verifyCrownCall:crown,now:t});
 // Existing R16 issuer may remain a read-only journal source during staging.
 // Ensure the root-protected authoritative state has not drifted, rather than
 // silently trusting a separately supplied snapshot file.
 const stable=()=>{
  need(digest(readJson(PUB,readProtected))===plan.r15PublicConfigDigest,
    'PUBLISHER_PUBLIC_STATE_DRIFT');
  const legacy=readJson(OLD_ISSUER,readProtected);
  need(legacy?.schema===1&&digest(legacy.data)===plan.issuerSnapshotHash,
    'PUBLISHER_ISSUER_STATE_DRIFT');
 };
 stable();
 const approved={schema:'mht.first-trust-signer-intent.v1',
   planHash:digest(plan),reviewedManifestHash:plan.reviewedManifestHash,
   sourceFreezeDigest:plan.sourceFreezeDigest,
   r15PublicConfigDigest:plan.r15PublicConfigDigest,
   recoveryEvidenceDigest:plan.recoveryEvidenceDigest,
   humanApprovalReceiptHash:inspected.admission.humanApprovalReceiptHash,
   stopEpoch:plan.stopEpoch,stopReceiptHashes:plan.stopProofHashes,
   grantId:inspected.admission.grantId,
   twoReadOperationIds:inspected.admission.operations.map(x=>x.operationId),
   sourceReleaseId:'r16-daily-20261012-r15',
   targetReleaseId:'r16-daily-20261012-r17'};
 const verifyResult=signedResult=>validateStagedPublisherResult(signedResult,{
   pub,roots,admission:inspected,reviewManifest,now:t});
 return stage({directory:TX,identity:approved,
   uid:0,verifyResult,
   sign:()=>{
    stable();
    const keys=readKeys({
      expectedReleaseKey:roots.releasePublicKey,
      expectedEnrollmentKey:roots.enrollmentAuthorityPublicKey});
    const result=signFirstTrustRecoveryArtifacts({
      firstTrust,existingR15Evidence:evidence.existingR15Evidence,
      verifyCrownCall:crown,
      releaseSigningKey:keys.releaseSigningKey,
      enrollmentSigningKey:keys.enrollmentSigningKey,
      readFile:readProtected,now:t});
    stable();
    return result;
   }});
}
