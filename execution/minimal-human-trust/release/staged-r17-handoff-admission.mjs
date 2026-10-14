// Read-only root preflight. Durable stage signatures grant no installation or
// writer admission; fresh R17 STOP and actual fenced Owner evidence are required.
import fs from 'node:fs';
import {canonical,digest,verified,verifyRelease,publicKey,ACTIONS,ROLES} from '../src/lease-core.mjs';
import {protectedRuntimeFile,runtimeVersion} from '../authority/runtime-manifest.mjs';
import {validateStageAuthorization} from '../authority/stage-authorization.mjs';
import {EXACT_R17_MIGRATION_SCOPE} from '../migration/r17-one-time-recovery-admission.mjs';
import {verifySignedBusinessStop} from '../src/signed-business-stop.mjs';
import {inspectSingleWriterHandoff,readLegacyOwnerUnit} from './single-writer-handoff-preflight.mjs';
import {inspectFirstTrustJournal} from '../human/first-trust-journal.mjs';
import {handoffSchema,verifyRecoveryHandoff,inspectRecoveryIssuerSnapshot}
  from '../authority/recovery-handoff.mjs';

const PLAN='/etc/minimal-human-trust/first-trust-publication.json';
const TX='/var/lib/minimal-human-trust/first-trust-publication';
const BASE='/etc/minimal-human-trust/';
const SNAPSHOTS=new Set(['/var/lib/r16-owner/issuer/state.json','/var/lib/minimal-human-trust/issuer/state.json']);
const fail=code=>{throw Object.assign(new Error(code),{code});};
const need=(value,code='STAGED_HANDOFF_REJECTED')=>{if(!value)fail(code);};
const same=(a,b)=>canonical(a)===canonical(b);
const hash=value=>typeof value==='string'&&/^[a-f0-9]{64}$/.test(value);
const exact=(value,fields)=>need(value&&Object.getPrototypeOf(value)===Object.prototype&&
  same(Object.keys(value).sort(),fields.slice().sort()),'STAGED_HANDOFF_SHAPE');
const operationIds=EXACT_R17_MIGRATION_SCOPE.projects.map(row=>row.operationId);

export function inspectStagedR17HandoffAdmission({
 priorPublicConfig,roots,reviewManifest,delivery,receipts,expectedRevision,
 expectedResultsHashes,handoff,readProtected=protectedRuntimeFile,
 readUnit=readLegacyOwnerUnit,lockExists=p=>fs.existsSync(p),
 now=Date.now(),euid=process.geteuid(),
}={}){
 need(euid===0,'ROOT_REQUIRED');
 need(Number.isSafeInteger(now)&&now>0&&typeof readProtected==='function'&&
   typeof readUnit==='function'&&typeof lockExists==='function','STAGED_HANDOFF_INPUT');
 const read=file=>JSON.parse(readProtected(file).toString());
 const plan=read(PLAN),intent=read(TX+'/intent.json'),result=read(TX+'/result.json');
 exact(plan,['schema','authorization','humanProposalHash']);
 need(plan.schema==='mht.first-trust-publisher-stage-plan.v2'&&hash(plan.humanProposalHash),
   'STAGED_HANDOFF_PLAN');
 exact(intent,['schema','approvedAt','planHash','stageAuthorizationHash','phase',
   'reviewedManifestHash','sourceFreezeDigest','installerHash','r15PublicConfigDigest',
   'recoveryEvidenceDigest','humanApprovalReceiptHash','stopEpoch','handoffEpoch',
   'stopProofs','stopRequiredBeforeHandoff','grantId','twoReadOperationIds',
   'sourceReleaseId','targetReleaseId']);
 need(intent.schema==='mht.first-trust-signer-intent.v1'&&intent.phase==='STAGE_ONLY'&&
   Number.isSafeInteger(intent.approvedAt)&&intent.approvedAt<=now,'STAGED_HANDOFF_INTENT');
 // Historical validation proves the earlier one-shot plan, never renews it.
 const a=validateStageAuthorization(plan.authorization,{now:intent.approvedAt});
 need(intent.planHash===digest(plan)&&intent.stageAuthorizationHash===digest(a)&&
   intent.reviewedManifestHash===a.reviewedManifestHash&&
   intent.sourceFreezeDigest===a.sourceFreezeDigest&&intent.installerHash===a.installerHash&&
   intent.r15PublicConfigDigest===a.r15PublicConfigDigest&&
   intent.recoveryEvidenceDigest===a.recoveryEvidenceDigest&&
   hash(intent.humanApprovalReceiptHash)&&intent.stopEpoch===a.stopEpoch&&
   intent.handoffEpoch===a.handoffEpoch&&intent.stopProofs===null&&
   intent.stopRequiredBeforeHandoff===true&&intent.grantId===a.grantId&&
   intent.sourceReleaseId===a.sourceReleaseId&&intent.targetReleaseId===a.targetReleaseId&&
   Array.isArray(intent.twoReadOperationIds)&&
   same(intent.twoReadOperationIds.slice().sort(),operationIds.slice().sort()),
   'STAGED_HANDOFF_INTENT_DRIFT');
 exact(result,['schema','intentHash','signedArtifacts']);
 need(result.schema==='mht.first-trust-publisher-result.v1'&&result.intentHash===digest(intent),
   'STAGED_HANDOFF_RESULT_DRIFT');
 need(digest(roots)===a.trustRootsDigest&&digest(priorPublicConfig)===a.r15PublicConfigDigest&&
   priorPublicConfig.issuerPublicKey===roots.issuerPublicKey&&
   priorPublicConfig.releasePublicKey===roots.releasePublicKey,
   'STAGED_HANDOFF_SOURCE_DRIFT');
 const grant=verified(priorPublicConfig.grant,roots.issuerPublicKey,'r16.workspace.v1');
 const prior=verified(priorPublicConfig.release,roots.releasePublicKey,'r16.release.v1');
 need(grant.id===a.grantId&&grant.version===a.grantVersion&&
   digest(priorPublicConfig.grant)===a.grantHash&&same(grant.actions,ACTIONS)&&
   prior.id===a.sourceReleaseId&&prior.issuedAt<=intent.approvedAt&&
   roots.releaseHash===digest(priorPublicConfig.release)&&roots.grantId===a.grantId,
   'STAGED_HANDOFF_SOURCE_DRIFT');
 verifyRelease(priorPublicConfig.release,roots.releasePublicKey,
   {versions:priorPublicConfig.versions,actions:grant.actions,now:prior.issuedAt});
 need(reviewManifest?.schema==='r16.reviewed-installation.v1'&&
   reviewManifest.releaseId===a.targetReleaseId&&digest(reviewManifest)===a.reviewedManifestHash&&
   reviewManifest.artifacts&&same(Object.keys(reviewManifest.artifacts).sort(),ROLES)&&
   Array.isArray(reviewManifest.localFiles)&&reviewManifest.localFiles.length>0,
   'STAGED_HANDOFF_REVIEW_DRIFT');
 const proposal=read(BASE+'human-pending.json'),policy=read(BASE+'human-policy.json');
 need(digest(proposal)===plan.humanProposalHash,'STAGED_HANDOFF_HUMAN_PROPOSAL_DRIFT');
 // Reinspect the historical first-use receipt at the original approvedAt.
 // The current issuer may already be installed; this is not a new enrollment
 // request, a fresh Human authorization, or permission to replay that ceremony.
 const readHistoricalHuman=()=>inspectFirstTrustJournal({proposal,policy,trustRoots:roots,
   sourceRelease:priorPublicConfig.release,sourceGrant:priorPublicConfig.grant,
   reviewManifest,now:intent.approvedAt,readProtected,isInstalled:()=>false});
 const human=readHistoricalHuman();
 need(human.proposalHash===plan.humanProposalHash&&human.stageAuthorizationHash===digest(a)&&
   same(human.stageAuthorization,a)&&human.osReceiptHash===intent.humanApprovalReceiptHash,
   'STAGED_HANDOFF_HISTORICAL_HUMAN_DRIFT');
 const versions=Object.fromEntries(ROLES.map(role=>
   [role,runtimeVersion(reviewManifest.artifacts[role],role)]));
 const staged=result.signedArtifacts;
 exact(staged,['schema','status','oldReleaseId','reviewedManifestHash','osApprovalReceiptHash',
   'firstTrustAdmissionDigest','stageAuthorizationHash','release','enrollment','grantUnchanged',
   'mayInstall','mayActivateBusiness','mayHandoffIssuer','maySettleUnknown']);
 need(staged.schema==='mht.first-trust-staged-signatures.v2'&&
   staged.status==='SIGNED_STAGED_NOT_INSTALLED'&&staged.oldReleaseId===a.sourceReleaseId&&
   staged.reviewedManifestHash===a.reviewedManifestHash&&
   staged.stageAuthorizationHash===digest(a)&&
   staged.osApprovalReceiptHash===intent.humanApprovalReceiptHash&&hash(staged.firstTrustAdmissionDigest)&&
   staged.grantUnchanged===true&&staged.mayInstall===false&&staged.mayActivateBusiness===false&&
   staged.mayHandoffIssuer===false&&staged.maySettleUnknown===false,'STAGED_HANDOFF_STAGE_SCOPE');
 const r17=verified(staged.release,roots.releasePublicKey,'r16.release.v1');
 need(r17.id===a.targetReleaseId&&same(r17.versions,versions)&&
   r17.issuedAt===reviewManifest.issuedAt&&r17.notAfter===reviewManifest.notAfter&&
   Number.isSafeInteger(r17.issuedAt)&&r17.issuedAt>=prior.issuedAt&&
   r17.issuedAt<=intent.approvedAt&&intent.approvedAt-r17.issuedAt<=300000&&
   r17.notAfter>intent.approvedAt&&r17.notAfter-r17.issuedAt<=7*86400000&&
   same(r17.actions,prior.actions)&&same(r17.actions,ACTIONS)&&
   same(r17.formats,prior.formats)&&r17.permissionVersion===prior.permissionVersion&&
   r17.permissionVersion===1,'STAGED_HANDOFF_RELEASE_DRIFT');
 verifyRelease(staged.release,roots.releasePublicKey,
   {versions,actions:grant.actions,now});
 const enrollment=verified(staged.enrollment,roots.enrollmentAuthorityPublicKey,'mht.human-enrollment.v1');
 exact(enrollment,['schema','enrolledAt','expiresAt','grantId','grantHash','humanPublicKey',
   'humanUid','humanSubject','releaseHash','releaseId']);
 publicKey(enrollment.humanPublicKey);
 need(enrollment.releaseId===r17.id&&enrollment.releaseHash===digest(staged.release)&&
   enrollment.grantId===grant.id&&enrollment.grantHash===a.grantHash&&
   enrollment.humanUid===1000&&enrollment.humanSubject==='local-human:1000'&&
   enrollment.humanPublicKey===human.humanPublicKey&&
   enrollment.expiresAt===human.enrollmentExpiresAt&&
   ![roots.issuerPublicKey,roots.releasePublicKey,roots.enrollmentAuthorityPublicKey]
     .includes(enrollment.humanPublicKey)&&
   enrollment.enrolledAt===intent.approvedAt&&Number.isSafeInteger(enrollment.expiresAt)&&
   enrollment.expiresAt>enrollment.enrolledAt&&now<enrollment.expiresAt,
   'STAGED_HANDOFF_ENROLLMENT_DRIFT');
 const stopped=verifySignedBusinessStop({grant:priorPublicConfig.grant,
   issuerPublicKey:roots.issuerPublicKey,release:staged.release,
   releasePublicKey:roots.releasePublicKey,delivery,receipts,
   expectedRevision,expectedReviewDigest:a.reviewedManifestHash,
   expectedUnresolvedIds:operationIds,expectedResultsHashes,stopEpoch:a.stopEpoch,now});
 const proofHashes=Object.fromEntries(stopped.proofHashes.map(row=>[row.role,row.proofDigest]));
 const recovery=handoffSchema(handoff)==='mht.issuer-handoff.v2';
 const handoffBody=recovery?verifyRecoveryHandoff(handoff,roots.enrollmentAuthorityPublicKey,
   {grantId:grant.id,release:staged.release,mode:'recovery_only',grantHash:a.grantHash,
     issuerPublicKey:roots.issuerPublicKey}):
   verified(handoff,roots.enrollmentAuthorityPublicKey,'mht.issuer-handoff.v1');
 exact(handoffBody,['schema','grantId','grantHash','releaseHash','issuerSnapshotHash',
   'installationProfile','epoch','mode','oldWriterClosed','participantClosureHashes','issuedAt','expiresAt',
   ...(recovery?['recoveryAdmission']:[])]);
 need(handoffBody.releaseHash===digest(staged.release)&&handoffBody.epoch===a.handoffEpoch&&
   handoffBody.installationProfile===roots.installationProfile&&
   Number.isSafeInteger(handoffBody.issuedAt)&&handoffBody.issuedAt<=now&&
   now-handoffBody.issuedAt<=30000,
   'STAGED_HANDOFF_EPOCH_OR_SNAPSHOT_DRIFT');
 if(recovery){
   const certificate=handoffBody.recoveryAdmission;
   need(certificate.stageAuthorizationHash===digest(a)&&
     certificate.reviewedManifestHash===a.reviewedManifestHash&&
     certificate.recoveryEvidenceDigest===a.recoveryEvidenceDigest&&
     certificate.sourceReleaseHash===digest(priorPublicConfig.release),
     'STAGED_HANDOFF_RECOVERY_ADMISSION_DRIFT');
 }
 // Closing/fencing can legitimately change the stage-time ledger. The newly
 // signed handoff must pin the final fresh exact old/new snapshot; the earlier
 // core.issuerSnapshotHash is not a substitute for actual closed-state proof.
 const readFreshSnapshot=file=>{
   const bytes=readProtected(file);
   if(SNAPSHOTS.has(file)){
     const state=JSON.parse(bytes.toString());
     // maxNow is the ledger's last WRITE time, not the time of this READ.
     // v2 binds a fresh signed observation of the complete unchanged wrapper.
     // It never updates maxNow just to make an old ledger look fresh.
     need(Number.isSafeInteger(state?.maxNow)&&state.maxNow>=0&&state.maxNow<=now&&
       (recovery||now-state.maxNow<=30000),
       'STAGED_HANDOFF_SNAPSHOT_NOT_FRESH');
   }
   return bytes;
 };
 const readFencedUnit=()=>{
   const state=readUnit();
   need(state?.ActiveState==='inactive'&&state.SubState==='dead'&&state.MainPID==='0'&&
     ['masked','masked-runtime'].includes(state.UnitFileState),'OWNER_WRITER_STILL_ACTIVE');
   return state;
 };
 const writer=inspectSingleWriterHandoff({handoff,
   enrollmentAuthorityPublicKey:roots.enrollmentAuthorityPublicKey,
   issuerPublicKey:roots.issuerPublicKey,grant:priorPublicConfig.grant,
   verifiedStopProofHashes:proofHashes,readProtected:readFreshSnapshot,
   readUnit:readFencedUnit,lockExists,now,euid});
 if(recovery){
   const wrapper=JSON.parse(readFreshSnapshot('/var/lib/r16-owner/issuer/state.json').toString());
   inspectRecoveryIssuerSnapshot({snapshot:wrapper.data,wrapper,
     admission:handoffBody.recoveryAdmission,grantId:grant.id,
     issuerPublicKey:roots.issuerPublicKey,releasePublicKey:roots.releasePublicKey,now});
 }
 need(same(read(PLAN),plan)&&same(read(TX+'/intent.json'),intent)&&
   same(read(TX+'/result.json'),result)&&same(read(BASE+'human-pending.json'),proposal)&&
   same(read(BASE+'human-policy.json'),policy)&&digest(roots)===a.trustRootsDigest&&
   digest(reviewManifest)===a.reviewedManifestHash&&
   same(readHistoricalHuman(),human),
   'STAGED_HANDOFF_DURABLE_STATE_CHANGED');
 return Object.freeze({schema:'mht.staged-r17-handoff-inspection.v1',
   status:'STAGED_R17_STOP_AND_FENCED_OWNER_INSPECTED',
   stageAuthorizationHash:digest(a),stageIntentHash:digest(intent),stageResultHash:digest(result),
   releaseHash:digest(staged.release),reviewedManifestHash:a.reviewedManifestHash,
   stopEpoch:a.stopEpoch,handoffEpoch:a.handoffEpoch,issuerSnapshotHash:writer.issuerSnapshotHash,
   signedRoleStopHashes:proofHashes,signerAuthority:false,
   mayStartIssuer:false,mayInstall:false,mayActivate:false,mayClearUnknown:false,
   mayReplayUnknown:false,mayRetireOwner:false});
}
