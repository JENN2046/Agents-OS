// FIRST_TRUST_BOOTSTRAP_R1: exact, read-only trusted-publisher admission.
// Does not sign, mutate, install, activate or infer unknown results.
import {canonical,digest,verified,verifyRelease,ROLES} from '../src/lease-core.mjs';
import {verifySignedBusinessStop} from '../src/signed-business-stop.mjs';
import {EXACT_R17_MIGRATION_SCOPE} from '../migration/r17-one-time-recovery-admission.mjs';
import {inspectFirstTrustRecoveryPublication} from './first-trust-recovery-admission.mjs';
const fail=c=>{throw Object.assign(new Error(c),{code:c});};
const need=(x,c='TRUSTED_PUBLISHER_ADMISSION_REJECTED')=>{if(!x)fail(c);};
const eq=(a,b)=>canonical(a)===canonical(b);
const hash=s=>typeof s==='string'&&/^[a-f0-9]{64}$/.test(s);
const exact=(x,fields)=>need(x&&typeof x==='object'&&!Array.isArray(x)&&
  eq(Object.keys(x).sort(),fields.slice().sort()),'PUBLISHER_PLAN_SHAPE');
const roles=Object.freeze([...ROLES]);

export function inspectPublisherInputs({
 plan,roots,publicConfig,evidence,firstTrust,verifyCrownCall,now=Date.now(),
}){
 exact(plan,['schema','r15PublicConfigDigest','reviewedManifestHash','recoveryEvidenceDigest',
  'stopEpoch','stopRevision','stopResultsHashes','stopProofHashes',
  'sourceFreezeDigest','issuerSnapshotHash','humanProposalHash','issuedAt','expiresAt']);
 need(plan.schema==='mht.first-trust-publisher-plan.v1'&&
  [plan.r15PublicConfigDigest,plan.reviewedManifestHash,plan.recoveryEvidenceDigest,
   plan.sourceFreezeDigest,plan.issuerSnapshotHash,plan.humanProposalHash].every(hash)&&
  typeof plan.stopEpoch==='string'&&/^[a-f0-9-]{36}$/.test(plan.stopEpoch)&&
  Number.isSafeInteger(plan.stopRevision)&&plan.stopRevision>0&&
  Number.isSafeInteger(plan.issuedAt)&&Number.isSafeInteger(plan.expiresAt)&&
  plan.issuedAt<=now&&now<plan.expiresAt&&plan.expiresAt-plan.issuedAt<=300000,
  'PUBLISHER_PLAN_EXPIRED');
 exact(plan.stopResultsHashes,roles);
 exact(plan.stopProofHashes,roles);
 need(roles.every(role=>hash(plan.stopResultsHashes[role])&&hash(plan.stopProofHashes[role])),
   'PUBLISHER_ROLE_HASH');
 need(typeof verifyCrownCall==='function'&&publicConfig&&evidence&&firstTrust&&roots,
   'PUBLISHER_EVIDENCE_MISSING');
 need(digest(publicConfig)===plan.r15PublicConfigDigest&&
   digest(evidence)===plan.recoveryEvidenceDigest&&
   firstTrust.policy?.proposalHash===plan.humanProposalHash&&
   digest(firstTrust.reviewManifest)===plan.reviewedManifestHash,
   'PUBLISHER_SOURCE_DRIFT');
 const source=verified(publicConfig.release,roots.releasePublicKey,'r16.release.v1');
 const g=verified(publicConfig.grant,roots.issuerPublicKey,'r16.workspace.v1');
 need(source.id==='r16-daily-20261012-r15'&&g.id==='r16-projects-daily'&&
   publicConfig.issuerPublicKey===roots.issuerPublicKey&&
   publicConfig.releasePublicKey===roots.releasePublicKey&&
   source.issuedAt<=now,'PUBLISHER_R15_ROOT_DRIFT');
 verifyRelease(publicConfig.release,roots.releasePublicKey,{
   versions:publicConfig.versions,actions:g.actions,now:source.issuedAt});
 need(eq(evidence.existingR15Evidence?.publicConfiguration,publicConfig)&&
   eq(evidence.existingR15Evidence?.reviewManifest,firstTrust.reviewManifest)&&
   digest(evidence.existingR15Evidence?.issuerState)===plan.issuerSnapshotHash&&
   Number.isSafeInteger(evidence.existingR15Evidence?.now)&&
   Math.abs(now-evidence.existingR15Evidence.now)<=30000,
   'PUBLISHER_SNAPSHOT_NOT_FRESH');
 const expected=EXACT_R17_MIGRATION_SCOPE.projects.map(x=>x.operationId);
 const stopped=verifySignedBusinessStop({
   grant:publicConfig.grant,issuerPublicKey:roots.issuerPublicKey,
   release:publicConfig.release,releasePublicKey:roots.releasePublicKey,
   delivery:evidence.cloudDelivery,receipts:evidence.stopReceipts,
   expectedRevision:plan.stopRevision,expectedReviewDigest:plan.reviewedManifestHash,
   expectedUnresolvedIds:expected,expectedResultsHashes:plan.stopResultsHashes,
   stopEpoch:plan.stopEpoch,now});
 need(stopped.result==='SIGNED_ROLES_MATCH'&&stopped.mayDeploy===false&&
   roles.every(role=>stopped.proofHashes.some(x=>x.role===role&&
     x.proofDigest===plan.stopProofHashes[role])),'PUBLISHER_STOP_EVIDENCE');
 const admission=inspectFirstTrustRecoveryPublication({
   firstTrust,existingR15Evidence:evidence.existingR15Evidence,
   verifyCrownCall});
 need(admission.reviewedManifestHash===plan.reviewedManifestHash&&
   admission.oldOwnerSnapshotDigest&&
   admission.status==='HUMAN_AND_SIGNED_RECOVERY_INSPECTED',
   'PUBLISHER_FIRST_TRUST_MISSING');
 return Object.freeze({admission,stopped,
   schema:'mht.first-trust-publisher-inspection.v1',
   status:'PREPARED_FOR_SINGLE_USE_OS_SIGNER',
   maySign:false,mayInstall:false,mayRetireOwner:false});
}
