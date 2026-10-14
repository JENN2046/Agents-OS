// Stage-only is a distinct exact Human target. It grants no installation,
// business stop, activation or writer handoff. Real STOP stays at handoff.
import {canonical,digest,verified,verifyRelease} from '../src/lease-core.mjs';
import {validateStageAuthorization} from '../authority/stage-authorization.mjs';
import {inspectFirstTrustRecoveryPublication} from './first-trust-recovery-admission.mjs';
const need=(x,c)=>{if(!x)throw Object.assign(new Error(c),{code:c});};
const eq=(a,b)=>canonical(a)===canonical(b);
const hash=s=>typeof s==='string'&&/^[a-f0-9]{64}$/.test(s);

export function inspectPublisherInputs({
 plan,roots,publicConfig,evidence,firstTrust,verifyCrownCall,now=Date.now(),
}){
 need(plan&&eq(Object.keys(plan).sort(),['authorization','humanProposalHash','schema'])&&
   plan.schema==='mht.first-trust-publisher-stage-plan.v2'&&hash(plan.humanProposalHash),
   'PUBLISHER_PLAN_SHAPE');
 const a=validateStageAuthorization(plan.authorization,{now});
 need(typeof verifyCrownCall==='function'&&publicConfig&&evidence&&firstTrust&&roots,
   'PUBLISHER_EVIDENCE_MISSING');
 need(evidence.schema==='mht.first-trust-stage-evidence.v2'&&
   eq(Object.keys(evidence).sort(),['existingR15Evidence','schema']),
   'PUBLISHER_STAGE_EVIDENCE_SHAPE');
 need(digest(publicConfig)===a.r15PublicConfigDigest&&
   digest(roots)===a.trustRootsDigest&&
   digest(evidence.existingR15Evidence)===a.recoveryEvidenceDigest&&
   firstTrust.policy?.proposalHash===plan.humanProposalHash&&
   digest(firstTrust.reviewManifest)===a.reviewedManifestHash,
   'PUBLISHER_SOURCE_DRIFT');
 const source=verified(publicConfig.release,roots.releasePublicKey,'r16.release.v1');
 const g=verified(publicConfig.grant,roots.issuerPublicKey,'r16.workspace.v1');
 need(source.id===a.sourceReleaseId&&g.id===a.grantId&&
   digest(publicConfig.grant)===a.grantHash&&g.version===a.grantVersion&&
   publicConfig.issuerPublicKey===roots.issuerPublicKey&&
   publicConfig.releasePublicKey===roots.releasePublicKey&&source.issuedAt<=now,
   'PUBLISHER_R15_ROOT_DRIFT');
 verifyRelease(publicConfig.release,roots.releasePublicKey,{
   versions:publicConfig.versions,actions:g.actions,now:source.issuedAt});
 // Frozen evidence can age during the native prompt, never be replaced after
 // approval. The root entry re-reads exact state before/after signing. No STOP
 // or single-writer attestation is inferred from this stage snapshot.
 const old=evidence.existingR15Evidence;
 need(eq(old?.publicConfiguration,publicConfig)&&
   eq(old?.reviewManifest,firstTrust.reviewManifest)&&
   digest(old?.issuerState)===a.issuerSnapshotHash&&
   Number.isSafeInteger(old?.now)&&old.now<=now&&now-old.now<=300000,
   'PUBLISHER_SNAPSHOT_NOT_FRESH');
 const admission=inspectFirstTrustRecoveryPublication({
   firstTrust,existingR15Evidence:old,verifyCrownCall});
 need(admission.reviewedManifestHash===a.reviewedManifestHash&&
   admission.stageAuthorizationHash===digest(a)&&
   eq(admission.stageAuthorization,a)&&admission.oldOwnerSnapshotDigest&&
   admission.status==='HUMAN_AND_SIGNED_RECOVERY_INSPECTED',
   'PUBLISHER_FIRST_TRUST_MISSING');
 return Object.freeze({admission,authorization:a,
   schema:'mht.first-trust-publisher-inspection.v2',
   status:'PREPARED_FOR_SINGLE_USE_STAGE_ONLY_SIGNER',
   stopped:null,stopEvidenceRequiredBeforeHandoff:true,
   maySign:false,mayInstall:false,mayRetireOwner:false});
}
