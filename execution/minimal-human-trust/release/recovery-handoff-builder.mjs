// Pure construction of a receiver attestation AFTER the original exhaustive
// R15 migration verifier. No signing, OS admission, installation or settlement.
import {canonical,digest} from '../src/lease-core.mjs';
import {inspectReviewedR17MigrationEvidence,EXACT_R17_MIGRATION_SCOPE}
  from '../migration/r17-one-time-recovery-admission.mjs';
import {inspectRecoveryIssuerSnapshot} from '../authority/recovery-handoff.mjs';
import {validateStageAuthorization} from '../authority/stage-authorization.mjs';

const need=(ok,code)=>{if(!ok)throw Object.assign(new Error(code),{code});};
const same=(a,b)=>canonical(a)===canonical(b);
export function buildRecoveryHandoffAdmission({evidence,wrapper,stageAuthorization,
  priorPublicConfig,reviewManifest,verifyCrownCall,approvedAt,now=Date.now()}){
  // A historical stage binding is evidence, not renewed signing authority.
  // approvedAt is the historical durable signer intent, supplied only after
  // staged admission. Evidence can precede consent; this does not renew either.
  need(Number.isSafeInteger(approvedAt)&&Number.isSafeInteger(evidence?.now)&&
    evidence.now<=approvedAt&&approvedAt-evidence.now<=300000&&approvedAt<=now,
    'RECOVERY_HISTORICAL_APPROVAL_TIME');
  stageAuthorization=validateStageAuthorization(stageAuthorization,{now:approvedAt});
  need(digest(evidence)===stageAuthorization.recoveryEvidenceDigest&&
    digest(reviewManifest)===stageAuthorization.reviewedManifestHash&&
    digest(priorPublicConfig)===stageAuthorization.r15PublicConfigDigest&&
    same(evidence.publicConfiguration,priorPublicConfig)&&
    same(evidence.issuerState,wrapper?.data)&&
    stageAuthorization.issuerSnapshotHash===digest(wrapper?.data)&&
    stageAuthorization.sourceReleaseId===EXACT_R17_MIGRATION_SCOPE.sourceRelease&&
    stageAuthorization.targetReleaseId===EXACT_R17_MIGRATION_SCOPE.targetRelease&&
    stageAuthorization.grantId===priorPublicConfig.grant.body.id&&
    stageAuthorization.grantHash===digest(priorPublicConfig.grant)&&
    stageAuthorization.grantVersion===priorPublicConfig.grant.body.version,
    'RECOVERY_SOURCE_EVIDENCE_DRIFT');
  const inspected=inspectReviewedR17MigrationEvidence(evidence,digest(reviewManifest),verifyCrownCall);
  need(inspected.status==='PENDING_TRUSTED_QUIESCENCE_AND_SIGNER'&&
    inspected.other_projects_closed===true,'RECOVERY_OTHER_PROJECTS_NOT_CLOSED');
  const operations=EXACT_R17_MIGRATION_SCOPE.projects.map(row=>{
    const project=wrapper.data.grants[0].projects.find(p=>p.projectId===row.projectId);
    return {...row,leaseHash:digest(project.active.lease),action:'find_symbol',
      outcome:'UNRESOLVED',originalResultAvailable:false,replayAllowed:false};
  });
  const certificate={schema:'mht.r17-recovery-handoff-admission.v1',
    sourceReleaseId:EXACT_R17_MIGRATION_SCOPE.sourceRelease,
    sourceReleaseHash:digest(priorPublicConfig.release),
    targetReleaseId:EXACT_R17_MIGRATION_SCOPE.targetRelease,
    stageAuthorizationHash:digest(stageAuthorization),
    reviewedManifestHash:digest(reviewManifest),recoveryEvidenceDigest:digest(evidence),
    issuerSnapshotHash:digest(wrapper.data),issuerStateFileHash:digest(wrapper),observedAt:now,operations};
  inspectRecoveryIssuerSnapshot({snapshot:wrapper.data,wrapper,admission:certificate,
    grantId:priorPublicConfig.grant.body.id,issuerPublicKey:priorPublicConfig.issuerPublicKey,
    releasePublicKey:priorPublicConfig.releasePublicKey,now});
  return certificate;
}
