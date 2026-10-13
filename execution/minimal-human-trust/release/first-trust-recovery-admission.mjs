// FIRST_TRUST_BOOTSTRAP_R1: strict conjunction of physical Human review
// and the existing exact two-UNKNOWN signed R17 admission evidence.
// This is an OS-protected publisher INPUT CHECK, never a signing capability.
import {digest} from '../src/lease-core.mjs';
import {inspectFirstTrustJournal} from '../human/first-trust-journal.mjs';
import {inspectReviewedR17MigrationEvidence} from '../migration/r17-one-time-recovery-admission.mjs';

const deny=code=>{throw Object.assign(new Error(code),{code});};
const need=(x,code='FIRST_TRUST_RELEASE_BLOCKED')=>{if(!x)deny(code);};

export function inspectFirstTrustRecoveryPublication({
  firstTrust,existingR15Evidence,verifyCrownCall,
}){
  need(firstTrust&&existingR15Evidence&&typeof verifyCrownCall==='function',
    'MISSING_TRUSTED_EVIDENCE');
  // In production, firstTrust.readProtected MUST be the fixed root-owned
  // reader and existingR15Evidence MUST come from verified fixed OS paths.
  const human=inspectFirstTrustJournal(firstTrust);
  const recovery=inspectReviewedR17MigrationEvidence(existingR15Evidence,
    human.reviewedManifestHash,verifyCrownCall);
  need(recovery.status==='PENDING_TRUSTED_QUIESCENCE_AND_SIGNER'&&
    recovery.other_projects_closed===true,'R17_OTHER_PROJECTS_NOT_QUIESCENT');
  need(recovery.old_release===human.sourceReleaseId&&
    recovery.proposed_release===human.targetReleaseId&&
    recovery.grant_id===human.grantId&&
    recovery.review_sha256===human.reviewedManifestHash,
    'FIRST_TRUST_AND_R17_DIVERGED');
  const rows=recovery.operations;
  need(Array.isArray(rows)&&rows.length===2&&
    rows.every(x=>x.action==='find_symbol'&&x.outcome==='UNRESOLVED'&&
      x.replay_allowed===false&&x.original_result_available===false),
    'R17_READ_RESULT_NOT_PROVEN');
  return Object.freeze({
    schema:'mht.first-trust-r17-signer-admission.v1',
    status:'HUMAN_AND_SIGNED_RECOVERY_INSPECTED',
    grantId:human.grantId,sourceReleaseId:human.sourceReleaseId,
    targetReleaseId:human.targetReleaseId,
    reviewedManifestHash:human.reviewedManifestHash,
    humanApprovalReceiptHash:human.osReceiptHash,
    oldOwnerSnapshotDigest:recovery.exact_owner_snapshot_digest,
    operations:rows.map(x=>Object.freeze({projectId:x.project_id,operationId:x.operation_id,
      generation:x.generation,operationHash:x.operation_sha256,replayAllowed:false})),
    admissionDigest:digest({human,recovery}),
    // A different, installed, protected single-use Release signer must
    // atomically reserve its intent and use the already installed key.
    signerAuthority:false,maySignRelease:false,mayInstall:false,
    mayChangeGrant:false,mayActivateBusiness:false,maySettleUnknown:false});
}
