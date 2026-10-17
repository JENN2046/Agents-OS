import {fileURLToPath} from 'node:url';
import {ROOT,STATE,json,protectedBytes,atomicJson,digest,sha,need,rootContext,verifyCapsule,same} from './io.mjs';
import {buildPublicationArtifacts} from './publication.mjs';
import {FIXED} from './maintenance-release-base.mjs';
import {PATHS,captureLocal,verifySourceDelivery} from './state.mjs';

export function prepareContext(){
  rootContext('jenn-System-Product-Name',false);
  need(process.argv.length===2,'FIXED_PREPARE_ARGUMENTS_REQUIRED');
  const plan=json(STATE+'/plan.json'),{files}=verifyCapsule(plan);
  need(plan.schema==='r16.native-recovery-maintenance.plan.v3'&&Number.isSafeInteger(plan.approvedAt)&&Number.isSafeInteger(plan.expiresAt)&&plan.approvedAt<=Date.now()&&Date.now()<plan.expiresAt&&plan.expiresAt-plan.approvedAt<=300000&&plan.rollbackDeadline<=plan.approvedAt+1800000,'NATIVE_WINDOW_INVALID');
  const sourcePublicConfig=JSON.parse(protectedBytes(PATHS.public));
  need(digest(sourcePublicConfig)===FIXED.publicConfigDigest&&digest(sourcePublicConfig.grant)===FIXED.grantHash,'SOURCE_AUTHORITY_DRIFT');
  const sourceProposal=json(PATHS.proposal),before=captureLocal(sourcePublicConfig),sourceDelivery=verifySourceDelivery(sourcePublicConfig,before.configuration);
  const inputs={packageDirectory:STATE+'/package',sourcePublicConfig,sourceProposal,sourceDelivery,approvedAt:plan.approvedAt,expiresAt:plan.expiresAt,releaseNotAfter:sourcePublicConfig.release.body.notAfter,freezeDigest:digest(files),nonce:plan.nonce};
  const artifacts=buildPublicationArtifacts(inputs);
  need(plan.targetReleaseId===FIXED.targetReleaseId&&plan.targetNativeVersion===FIXED.nativeVersion&&plan.targetAppVersion===FIXED.targetAppVersion&&plan.packageInventoryHash===artifacts.payloadInventoryHash,'CAPSULE_TARGET_DRIFT');
  const snapshots={proposal:sourceProposal,reviewed:json(PATHS.reviewed),native:json(PATHS.native),cutover:json(PATHS.localCutover)};
  need(snapshots.native.codeManifest===FIXED.sourceDirectory+'/native-manifest.json'&&snapshots.cutover.phase==='ACTIVE'&&snapshots.cutover.grantId===sourcePublicConfig.grant.body.id,'NATIVE_SELECTOR_DRIFT');
  const context={schema:'r16.native-recovery-context.v3',planHash:digest(plan),inputs,artifactsHash:digest(artifacts),before,snapshots};
  atomicJson(STATE+'/context.json',context);
  atomicJson('/etc/r16-maintenance/recovery-r6-source-freeze.json',{schema:'r16.maintenance-source-freeze.v3',files,artifactsHash:context.artifactsHash,rollbackDeadline:plan.rollbackDeadline,capsuleHash:plan.capsuleHash});
  return {status:'CONTEXT_PREPARED',artifactsHash:context.artifactsHash,sourceFreezeHash:plan.sourceFreezeHash};
}
if(process.argv[1]===fileURLToPath(import.meta.url)){
  try{process.stdout.write(JSON.stringify(prepareContext())+'\n');}catch(e){process.stdout.write(JSON.stringify({status:'CONTEXT_REFUSED',code:e.code||'PROTECTED_CONTEXT_INVALID'})+'\n');process.exitCode=1;}
}
