// Explicit first-use Human scope. No identity, consent, or authority is created.
import {canonical,digest,publicKey} from '../src/lease-core.mjs';

const need=(ok,code='FIRST_CUTOVER_TARGET_REJECTED')=>{if(!ok)throw Object.assign(new Error(code),{code});};
const hash=x=>typeof x==='string'&&/^[a-f0-9]{64}$/.test(x);
const same=(a,b)=>canonical(a)===canonical(b);
const exact=(x,keys)=>need(x&&Object.getPrototypeOf(x)===Object.prototype&&
  same(Object.keys(x).sort(),keys.slice().sort()));
export const FIRST_CUTOVER_CONSTRAINTS=Object.freeze({
  mayStopBusiness:true,mayFenceOldWriter:true,maySignExactHandoff:true,
  mayInstallRecoveryOnly:true,mayStartRecoveryIssuer:true,
  mayActivateBusiness:false,maySettleUnknown:false,mayReplayUnknown:false,
  permissionsUnchanged:true,requireThreeRoleStop:true,requireSameEpochSnapshot:true,
  requireOldWriterFenced:true,requireDurableCommit:true,requireProtectedOsReceipt:true,
});
export const FIRST_CUTOVER_TARGET_FIELDS=Object.freeze(['schema','phase',
  'sourceReleaseId','sourceReleaseHash','grantId','grantHash','grantVersion',
  'targetReleaseId','targetReleaseHash','stageIntentHash','stageResultHash',
  'stageAuthorizationHash','reviewedManifestHash','recoveryEvidenceDigest',
  'issuerSnapshotHash','issuerStateFileHash','sourceFreezeDigest','installerHash',
  'oldRootHash','newRootTemplate','newRootTemplateHash','stopEpoch','handoffEpoch','constraints']);
export function validateFirstCutoverTarget(target,{roots}={}){
  exact(target,FIRST_CUTOVER_TARGET_FIELDS);
  need(target.schema==='mht.first-cutover-target.v1'&&
    target.phase==='FIRST_NATIVE_RECOVERY_CUTOVER'&&
    target.sourceReleaseId==='r16-daily-20261012-r15'&&
    target.targetReleaseId==='r16-daily-20261012-r17'&&target.grantId==='r16-projects-daily'&&
    Number.isSafeInteger(target.grantVersion)&&target.grantVersion>0&&
    Number.isSafeInteger(target.handoffEpoch)&&target.handoffEpoch>0&&
    typeof target.stopEpoch==='string'&&/^[a-f0-9]{8}(?:-[a-f0-9]{4}){3}-[a-f0-9]{12}$/.test(target.stopEpoch));
  need(['sourceReleaseHash','grantHash','targetReleaseHash','stageIntentHash','stageResultHash',
    'stageAuthorizationHash','reviewedManifestHash','recoveryEvidenceDigest','issuerSnapshotHash',
    'issuerStateFileHash','sourceFreezeDigest','installerHash','oldRootHash','newRootTemplateHash']
    .every(k=>hash(target[k])));
  const t=target.newRootTemplate;
  exact(t,['schema','grantId','issuerPublicKey','releasePublicKey','enrollmentAuthorityPublicKey',
    'releaseHash','installationProfile']);
  need(t.schema==='mht.trust-roots.v1'&&t.grantId===target.grantId&&
    t.releaseHash===target.targetReleaseHash&&['isolated','production'].includes(t.installationProfile)&&
    digest(t)===target.newRootTemplateHash);
  for(const k of ['issuerPublicKey','releasePublicKey','enrollmentAuthorityPublicKey'])
    need(publicKey(t[k]).export({format:'der',type:'spki'}).toString('base64url')===t[k],
      'FIRST_CUTOVER_NONCANONICAL_KEY');
  need(new Set([t.issuerPublicKey,t.releasePublicKey,t.enrollmentAuthorityPublicKey]).size===3);
  if(roots){
    const {handoffHash,...priorTemplate}=roots;
    need(hash(handoffHash)&&digest(roots)===target.oldRootHash&&
      roots.releaseHash===target.sourceReleaseHash&&
      same(t,{...priorTemplate,releaseHash:target.targetReleaseHash}),
      'FIRST_CUTOVER_ROOT_TEMPLATE_DRIFT');
  }
  exact(target.constraints,Object.keys(FIRST_CUTOVER_CONSTRAINTS));
  need(same(target.constraints,FIRST_CUTOVER_CONSTRAINTS),'FIRST_CUTOVER_SCOPE_EXPANSION');
  return target;
}
export function firstCutoverApprovalBody(checked,{now=Date.now()}={}){
  const p=checked?.body;
  need(p?.action==='first_cutover_handoff'&&Number.isSafeInteger(now)&&
    p.issuedAt<=now&&now<p.expiresAt,'FIRST_CUTOVER_CONFIRMATION_EXPIRED');
  validateFirstCutoverTarget(p.target);
  return {schema:'mht.first-cutover-authorization.v1',action:p.action,
    proposalHash:checked.proposalHash,grantId:p.grantId,grantHash:p.expectedGrantHash,
    grantVersion:p.expectedVersion,sourceReleaseHash:p.releaseHash,
    targetReleaseHash:p.target.targetReleaseHash,nonce:p.nonce,issuedAt:now,
    expiresAt:p.expiresAt,targetHash:digest(p.target)};
}
