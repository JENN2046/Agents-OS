// Pre-Human target inspection only. No fabricated journal, signature or authority.
import {createHash} from 'node:crypto';
import {inspectSourcePublicConfiguration} from '../authority/source-baseline.mjs';

import {canonical,digest,publicKey,verified,verifyRelease} from '../src/lease-core.mjs';
import {inspectUnsignedHumanProposal,validateHumanProposal} from '../human/approval-policy.mjs';
import {checkReviewedSourceFreeze} from './publisher-bootstrap.mjs';
import {deriveExactR17Release} from './first-trust-release-builder.mjs';
import {inspectReviewedR17MigrationEvidence} from '../migration/r17-one-time-recovery-admission.mjs';
import {inspectPublishedFirstTrustStage} from './staged-r17-handoff-admission.mjs';
import {deriveFirstCutoverTarget} from '../human/first-cutover-admission.mjs';
const need=(x,c='HUMAN_PROPOSAL_INPUT_REFUSED')=>{if(!x)throw Object.assign(Error(c),{code:c});};
const same=(a,b)=>canonical(a)===canonical(b);
const sha=b=>createHash('sha256').update(b).digest('hex');
const exact=(x,keys)=>need(x&&Object.getPrototypeOf(x)===Object.prototype&&same(Object.keys(x).sort(),keys.slice().sort()));
const key=x=>{need(typeof x==='string');need(publicKey(x).export({format:'der',type:'spki'}).toString('base64url')===x,'HUMAN_PROPOSAL_CANONICAL_KEY');};

export function inspectHumanProposalSource({request,roots,pub,workspaceIdentity,now=Date.now()}={}){
 exact(request,['schema','body','policyTemplate','issuerStateFileHash']);
 need(request.schema==='mht.human-proposal-request.v1'&&
   ['enroll_human','first_cutover_handoff'].includes(request.body?.action),'HUMAN_PROPOSAL_ACTION');
 const checked=inspectUnsignedHumanProposal({body:request.body,policyTemplate:request.policyTemplate,roots,now});
 const p=checked.body,policy=request.policyTemplate;
 for(const k of [roots.releasePublicKey,roots.issuerPublicKey,roots.enrollmentAuthorityPublicKey,policy.humanPublicKey])key(k);
 need(new Set([roots.releasePublicKey,roots.issuerPublicKey,roots.enrollmentAuthorityPublicKey,policy.humanPublicKey]).size===4,
   'HUMAN_PROPOSAL_KEY_SEPARATION');
 const spec=inspectSourcePublicConfiguration(pub);
 const source=verified(pub.release,roots.releasePublicKey,'r16.release.v1');
 const grant=verified(pub.grant,roots.issuerPublicKey,'r16.workspace.v1');
 verifyRelease(pub.release,roots.releasePublicKey,{versions:pub.versions,actions:grant.actions,now});
 need(source.id===spec.releaseId&&p.releaseId===source.id&&p.releaseHash===digest(pub.release)&&
   roots.releasePublicKey===pub.releasePublicKey&&roots.issuerPublicKey===pub.issuerPublicKey&&
   roots.releaseHash===digest(pub.release)&&grant.id==='r16-projects-daily'&&grant.id===p.grantId&&
   grant.version===p.expectedVersion&&digest(pub.grant)===p.expectedGrantHash,'HUMAN_PROPOSAL_R15_DRIFT');
 need(grant.workspace?.id===policy.workspaceId&&grant.workspace.root===policy.workspaceRoot&&
   grant.workspace.dev===policy.workspaceDev&&grant.workspace.ino===policy.workspaceIno&&
   workspaceIdentity?.dev===policy.workspaceDev&&workspaceIdentity.ino===policy.workspaceIno,
   'HUMAN_PROPOSAL_WORKSPACE_DRIFT');
 return {checked,source,grant};
}

export function inspectHumanProposalRequest({request,roots,pub,reviewManifest,sourceFreeze,
 installerBytes,wrapper,evidence,readProtected,verifyCrownCall,workspaceIdentity,now=Date.now()}={}){
 const {checked,source}=inspectHumanProposalSource({request,roots,pub,workspaceIdentity,now});
 const p=checked.body,policy=request.policyTemplate;
 checkReviewedSourceFreeze({manifest:sourceFreeze,read:readProtected});
 exact(wrapper,['schema','revision','maxNow','data']);
 need(typeof request.issuerStateFileHash==='string'&&/^[a-f0-9]{64}$/.test(request.issuerStateFileHash)&&
   digest(wrapper)===request.issuerStateFileHash&&wrapper.schema===1&&Number.isSafeInteger(wrapper.revision)&&wrapper.revision>=0&&
   Number.isSafeInteger(wrapper.maxNow)&&wrapper.maxNow>=0&&wrapper.maxNow<=now&&
   Buffer.isBuffer(installerBytes)&&sha(installerBytes)===sourceFreeze.files['release/stage-installer-reviewed.mjs'],
   'HUMAN_PROPOSAL_FROZEN_SOURCE');
 need(Object.entries(sourceFreeze.files).every(([rel,h])=>reviewManifest.artifacts?.native?.files?.[rel]===h),
   'HUMAN_PROPOSAL_NATIVE_FREEZE_BINDING');
 let publicationAuthorization=null;
 let dependenciesExpireAt=source.notAfter;
 if(p.action==='enroll_human'){
   const a=p.target.stageAuthorization;
   exact(evidence,['schema','existingR15Evidence']);
   const old=evidence.existingR15Evidence;
   need(evidence.schema==='mht.first-trust-stage-evidence.v2'&&old&&
     Number.isSafeInteger(old.now)&&old.now<=now&&now-old.now<=300000&&
     same(old.publicConfiguration,pub)&&same(old.reviewManifest,reviewManifest)&&
     digest(pub)===a.r15PublicConfigDigest&&digest(reviewManifest)===a.reviewedManifestHash&&
     digest(old)===a.recoveryEvidenceDigest&&same(old.issuerState,wrapper.data)&&
     digest(wrapper.data)===a.issuerSnapshotHash&&digest(roots)===a.trustRootsDigest&&
     digest(sourceFreeze)===a.sourceFreezeDigest&&sha(installerBytes)===a.installerHash,
     'HUMAN_PROPOSAL_STAGE_EVIDENCE_DRIFT');
   deriveExactR17Release({sourceRelease:source,reviewManifest,reviewedManifestHash:a.reviewedManifestHash,
     now,readFile:readProtected});
   // Exhaustive original UNKNOWN/other-project closure checks do not require,
   // invent or bypass the future Human OS confirmation.
   const recovery=inspectReviewedR17MigrationEvidence(old,a.reviewedManifestHash,verifyCrownCall);
   need(recovery.status==='PENDING_TRUSTED_QUIESCENCE_AND_SIGNER'&&recovery.other_projects_closed===true,
     'HUMAN_PROPOSAL_RECOVERY_EVIDENCE');
   dependenciesExpireAt=Math.min(dependenciesExpireAt,old.now+300000,reviewManifest.issuedAt+300000,
     reviewManifest.notAfter,p.target.enrollmentExpiresAt);
   publicationAuthorization=a;
 }else{
   const stage=inspectPublishedFirstTrustStage({priorPublicConfig:pub,roots,reviewManifest,readProtected,now,euid:0});
   const exactRelease=deriveExactR17Release({sourceRelease:source,reviewManifest,
     reviewedManifestHash:stage.a.reviewedManifestHash,now:stage.intent.approvedAt,readFile:readProtected});
   dependenciesExpireAt=Math.min(dependenciesExpireAt,stage.staged.release.body.notAfter,stage.enrollment.expiresAt);
   need(same(exactRelease,stage.staged.release.body),'HUMAN_PROPOSAL_STAGED_RELEASE_DRIFT');
   need(digest(wrapper.data)===stage.a.issuerSnapshotHash&&digest(sourceFreeze)===stage.a.sourceFreezeDigest&&
     sha(installerBytes)===stage.a.installerHash&&p.issuedAt>=stage.intent.approvedAt&&
     policy.humanPublicKey===stage.enrollment.humanPublicKey&&
     same(p.target,deriveFirstCutoverTarget({stage,roots,wrapper,sourceFreeze})),
     'HUMAN_PROPOSAL_CUTOVER_TARGET_DRIFT');
 }
 need(Number.isSafeInteger(dependenciesExpireAt)&&p.expiresAt<=dependenciesExpireAt,
   'HUMAN_PROPOSAL_DEPENDENCY_WINDOW');
 return Object.freeze({schema:'mht.human-proposal-inspection.v1',status:'UNSIGNED_EXACT_TARGET_INSPECTED',
   checked,dependenciesExpireAt,requestHash:digest(request),sourceFreezeDigest:digest(sourceFreeze),
   issuerStateFileHash:digest(wrapper),reviewedManifestHash:digest(reviewManifest),
   publicationAuthorization,signerAuthority:false,mayEnroll:false,maySignRelease:false,mayInstall:false,mayCutover:false});
}

export function proposalArtifacts({proposal,inspection,request,roots,now=Date.now()}){
 const policy={...request.policyTemplate,schema:'mht.human-pending-policy.v1',proposalHash:digest(proposal)};
 const checked=validateHumanProposal({proposal,policy,roots,now});
 need(same(checked.body,request.body)&&inspection.requestHash===digest(request),'HUMAN_PROPOSAL_SIGNED_TARGET_DRIFT');
 return {schema:'mht.human-proposal-artifacts.v1',action:checked.body.action,
   requestHash:inspection.requestHash,sourceFreezeDigest:inspection.sourceFreezeDigest,
   proposal,policy,publicationPlan:inspection.publicationAuthorization?{
     schema:'mht.first-trust-publisher-stage-plan.v2',authorization:inspection.publicationAuthorization,
     humanProposalHash:digest(proposal)}:null,
   mayEnroll:false,maySignRelease:false,mayInstall:false,mayCutover:false};
}
export function verifyHumanProposalArtifacts(artifacts,args){
 exact(artifacts,['schema','action','requestHash','sourceFreezeDigest','proposal','policy','publicationPlan',
   'mayEnroll','maySignRelease','mayInstall','mayCutover']);
 need(same(artifacts,proposalArtifacts({...args,proposal:artifacts.proposal})), 'HUMAN_PROPOSAL_RESULT_DRIFT');
 return true;
}
