// Pure, closed-form Human authorization for one staged R17 signing attempt.
// No STOP receipt is invented here; actual handoff keeps every hard gate.
import {canonical} from '../src/lease-core.mjs';
import {sourceBaselineId,SOURCE19_BASELINE} from './source-baseline.mjs';

const reject=()=>{throw Object.assign(new Error('STAGE_AUTHORIZATION_REJECTED'),
  {code:'STAGE_AUTHORIZATION_REJECTED'});};
const need=value=>{if(!value)reject();};
const exact=(value,keys)=>need(value&&Object.getPrototypeOf(value)===Object.prototype&&
  canonical(Object.keys(value).sort())===canonical(keys.slice().sort()));
const hash=value=>typeof value==='string'&&/^[a-f0-9]{64}$/.test(value);
export const STAGE_CONSTRAINTS=Object.freeze({
  mayInstall:false,mayActivateBusiness:false,mayHandoffIssuer:false,maySettleUnknown:false,
  requireSignedThreeRoleStop:true,requireProtectedSameEpochIssuerSnapshot:true,
  requireOldWriterFenced:true,
});
export function validateStageAuthorization(core,{now=Date.now()}={}){
  exact(core,['schema','phase','sourceReleaseId','targetReleaseId','grantId','grantHash',
    'grantVersion','r15PublicConfigDigest','reviewedManifestHash','recoveryEvidenceDigest',
    'sourceFreezeDigest','installerHash','issuerSnapshotHash','trustRootsDigest','stopEpoch','handoffEpoch',
    'issuedAt','expiresAt','constraints']);
  const source=sourceBaselineId(core.sourceReleaseId);
  if(source===SOURCE19_BASELINE)need(core.r15PublicConfigDigest===source.publicConfigDigest);
  need(core.schema==='mht.first-trust-stage-authorization.v2'&&core.phase==='STAGE_ONLY'&&
    core.sourceReleaseId===source.releaseId&&
    core.targetReleaseId==='r16-daily-20261012-r17'&&core.grantId==='r16-projects-daily');
  need(['grantHash','r15PublicConfigDigest','reviewedManifestHash','recoveryEvidenceDigest',
    'sourceFreezeDigest','installerHash','issuerSnapshotHash','trustRootsDigest'].every(name=>hash(core[name])));
  need(Number.isSafeInteger(core.grantVersion)&&core.grantVersion>0&&
    Number.isSafeInteger(core.handoffEpoch)&&core.handoffEpoch>0&&
    typeof core.stopEpoch==='string'&&
    /^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$/.test(core.stopEpoch));
  need(Number.isSafeInteger(now)&&now>0&&Number.isSafeInteger(core.issuedAt)&&
    Number.isSafeInteger(core.expiresAt)&&core.issuedAt>0&&core.issuedAt<=now&&
    now<core.expiresAt&&core.expiresAt-core.issuedAt<=300000);
  exact(core.constraints,Object.keys(STAGE_CONSTRAINTS));
  need(canonical(core.constraints)===canonical(STAGE_CONSTRAINTS));
  return core;
}
