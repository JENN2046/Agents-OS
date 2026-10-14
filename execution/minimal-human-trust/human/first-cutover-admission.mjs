// First Native consent and its later read-only machine admission. No signing,
// installation, service control, identity registration or UNKNOWN settlement.
import {canonical,digest,verified,publicKey} from '../src/lease-core.mjs';
import {validateTrustRoots} from '../src/minimal-trust-issuer-once.mjs';
import {protectedRuntimeFile} from '../authority/runtime-manifest.mjs';
import {checkReviewedSourceFreeze} from '../release/publisher-bootstrap.mjs';
import {inspectPublishedFirstTrustStage,inspectStagedR17HandoffAdmission}
  from '../release/staged-r17-handoff-admission.mjs';
import {validateHumanProposal} from './approval-policy.mjs';
import {FIRST_CUTOVER_CONSTRAINTS,validateFirstCutoverTarget,firstCutoverApprovalBody}
  from '../authority/first-cutover-authorization.mjs';
import {createHash} from 'node:crypto';

export const FIRST_CUTOVER_PENDING='/etc/minimal-human-trust/first-cutover-human-pending.json';
export const FIRST_CUTOVER_POLICY='/etc/minimal-human-trust/first-cutover-human-policy.json';
const FREEZE='/etc/minimal-human-trust/first-trust-code.json';
const INSTALLER='/etc/minimal-human-trust/stage-installer-reviewed.mjs';
const OLD='/var/lib/r16-owner/issuer/state.json';
const JOURNAL='/var/lib/minimal-human-trust/human-approval/';
const need=(ok,code='FIRST_CUTOVER_ADMISSION_REFUSED')=>{if(!ok)throw Object.assign(new Error(code),{code});};
const same=(a,b)=>canonical(a)===canonical(b);
const hash=x=>typeof x==='string'&&/^[a-f0-9]{64}$/.test(x);
const exact=(x,keys)=>need(x&&Object.getPrototypeOf(x)===Object.prototype&&
  same(Object.keys(x).sort(),keys.slice().sort()),'FIRST_CUTOVER_SHAPE');
const sha=b=>createHash('sha256').update(b).digest('hex');
const readJson=(read,file)=>JSON.parse(read(file).toString());

export function deriveFirstCutoverTarget({stage,roots,wrapper,sourceFreeze}){
  need(stage?.status==='PUBLISHED_R17_STAGE_INSPECTED','FIRST_CUTOVER_STAGE_REQUIRED');
  const a=stage.a,{handoffHash,...template}=roots;
  const newRootTemplate={...template,releaseHash:digest(stage.staged.release)};
  return validateFirstCutoverTarget({schema:'mht.first-cutover-target.v1',
    phase:'FIRST_NATIVE_RECOVERY_CUTOVER',sourceReleaseId:a.sourceReleaseId,
    sourceReleaseHash:roots.releaseHash,
    grantId:a.grantId,grantHash:a.grantHash,grantVersion:a.grantVersion,
    targetReleaseId:a.targetReleaseId,targetReleaseHash:digest(stage.staged.release),
    stageIntentHash:digest(stage.intent),stageResultHash:digest(stage.result),
    stageAuthorizationHash:digest(a),reviewedManifestHash:a.reviewedManifestHash,
    recoveryEvidenceDigest:a.recoveryEvidenceDigest,issuerSnapshotHash:digest(wrapper.data),
    issuerStateFileHash:digest(wrapper),sourceFreezeDigest:digest(sourceFreeze),
    installerHash:sourceFreeze.files['release/stage-installer-reviewed.mjs'],
    oldRootHash:digest(roots),newRootTemplate,newRootTemplateHash:digest(newRootTemplate),
    stopEpoch:a.stopEpoch,handoffEpoch:a.handoffEpoch,constraints:{...FIRST_CUTOVER_CONSTRAINTS},
  },{roots});
}

export function inspectFirstCutoverInputs({proposal,policy,roots,priorPublicConfig,
  reviewManifest,readProtected=protectedRuntimeFile,now=Date.now(),euid=process.geteuid()}={}){
  need(euid===0&&Number.isSafeInteger(now)&&now>0&&typeof readProtected==='function',
    'FIRST_CUTOVER_NATIVE_CONTEXT');
  validateTrustRoots(roots);
  const checked=validateHumanProposal({proposal,policy,roots,now});
  need(checked.body.action==='first_cutover_handoff','FIRST_CUTOVER_ACTION_REQUIRED');
  const sourceFreeze=readJson(readProtected,FREEZE);
  checkReviewedSourceFreeze({manifest:sourceFreeze,read:readProtected});
  const installer=readProtected(INSTALLER),wrapper=readJson(readProtected,OLD);
  const stage=inspectPublishedFirstTrustStage({priorPublicConfig,roots,reviewManifest,
    readProtected,now,euid});
  exact(wrapper,['schema','revision','maxNow','data']);
  need(wrapper.schema===1&&Number.isSafeInteger(wrapper.revision)&&wrapper.revision>=0&&
    Number.isSafeInteger(wrapper.maxNow)&&wrapper.maxNow>=0&&wrapper.maxNow<=now&&
    digest(wrapper.data)===stage.a.issuerSnapshotHash&&
    digest(sourceFreeze)===stage.a.sourceFreezeDigest&&
    sha(installer)===stage.a.installerHash&&
    sha(installer)===sourceFreeze.files['release/stage-installer-reviewed.mjs'],
    'FIRST_CUTOVER_FROZEN_SOURCE_DRIFT');
  need(policy.humanPublicKey===stage.enrollment.humanPublicKey&&
    publicKey(policy.humanPublicKey).export({format:'der',type:'spki'}).toString('base64url')===policy.humanPublicKey&&
    checked.body.issuedAt>=stage.intent.approvedAt&&
    same(checked.body.target,deriveFirstCutoverTarget({stage,roots,wrapper,sourceFreeze})),
    'FIRST_CUTOVER_EXACT_STAGE_TARGET');
  need(same(readJson(readProtected,FREEZE),sourceFreeze)&&
    same(readJson(readProtected,OLD),wrapper)&&sha(readProtected(INSTALLER))===sha(installer),
    'FIRST_CUTOVER_INPUT_CHANGED');
  return Object.freeze({status:'FIRST_CUTOVER_INPUTS_INSPECTED',checked,stage,sourceFreeze,
    wrapper,humanPublicKey:stage.enrollment.humanPublicKey,targetHash:digest(checked.body.target),
    mayExecute:false,signerAuthority:false});
}

export function inspectFirstCutoverSigningIntent({checked,readProtected=protectedRuntimeFile,now=Date.now()}={}){
  const p=checked.body;
  need(p.action==='first_cutover_handoff'&&Number.isSafeInteger(now)&&p.issuedAt<=now&&now<p.expiresAt,
    'FIRST_CUTOVER_CONFIRMATION_EXPIRED');
  const osIntent=readJson(readProtected,JOURNAL+checked.proposalHash+'.intent.json');
  exact(osIntent,['schema','proposalHash','peerUid','processStart','confirmedAt','challengeHash']);
  need(osIntent.schema==='mht.human-os-intent.v1'&&osIntent.proposalHash===checked.proposalHash&&
    osIntent.peerUid===1000&&Number.isSafeInteger(osIntent.processStart)&&osIntent.processStart>0&&
    Number.isSafeInteger(osIntent.confirmedAt)&&p.issuedAt<=osIntent.confirmedAt&&
    osIntent.confirmedAt<=now&&now-osIntent.confirmedAt<=300000&&hash(osIntent.challengeHash),
    'FIRST_CUTOVER_OS_CONFIRMATION');
  return osIntent;
}

export function inspectFirstCutoverHumanJournal(args={}){
  const input=inspectFirstCutoverInputs(args),read=args.readProtected??protectedRuntimeFile;
  const now=args.now??Date.now(),osIntent=inspectFirstCutoverSigningIntent({checked:input.checked,readProtected:read,now});
  const osResult=readJson(read,JOURNAL+input.checked.proposalHash+'.result.json');
  exact(osResult,['ok','status','proposalHash','approval']);
  need(osResult.ok===true&&osResult.status==='APPROVED_NOT_APPLIED'&&
    osResult.proposalHash===input.checked.proposalHash,'FIRST_CUTOVER_RESULT_CONFLICT');
  const approval=verified(osResult.approval,input.humanPublicKey,'mht.first-cutover-authorization.v1');
  need(Number.isSafeInteger(approval.issuedAt)&&osIntent.confirmedAt<=approval.issuedAt&&
    approval.issuedAt<=now&&now<approval.expiresAt&&
    same(approval,firstCutoverApprovalBody(input.checked,{now:approval.issuedAt})),
    'FIRST_CUTOVER_HUMAN_AUTHORIZATION');
  need(same(readJson(read,JOURNAL+input.checked.proposalHash+'.intent.json'),osIntent)&&
    same(readJson(read,JOURNAL+input.checked.proposalHash+'.result.json'),osResult),
    'FIRST_CUTOVER_JOURNAL_CHANGED');
  return Object.freeze({...input,status:'FIRST_CUTOVER_HUMAN_CONFIRMED_NOT_APPLIED',
    approval,approvalEnvelope:osResult.approval,osIntent,
    humanProposalHash:input.checked.proposalHash,humanApprovalHash:digest(osResult.approval),
    humanOsReceiptHash:digest({osIntent,osResult}),nonce:approval.nonce,
    issuedAt:approval.issuedAt,expiresAt:approval.expiresAt,mayExecute:false,signerAuthority:false});
}

export function inspectFirstCutoverHandoffAdmission({humanArgs,finalRoots,handoffArgs,now=Date.now()}={}){
  const human=inspectFirstCutoverHumanJournal({...humanArgs,now}),t=human.checked.body.target;
  need(same(humanArgs.roots,handoffArgs.roots)&&
    same(humanArgs.priorPublicConfig,handoffArgs.priorPublicConfig)&&
    same(humanArgs.reviewManifest,handoffArgs.reviewManifest)&&
    handoffArgs.handoff?.body?.schema==='mht.issuer-handoff.v2','FIRST_CUTOVER_HANDOFF_CONTEXT');
  const machine=inspectStagedR17HandoffAdmission({...handoffArgs,now});
  const b=handoffArgs.handoff.body,c=b.recoveryAdmission;
  const deliveredAt=handoffArgs.delivery?.body?.issuedAt;
  need(Number.isSafeInteger(deliveredAt)&&human.issuedAt<=deliveredAt&&deliveredAt<=now,
    'FIRST_CUTOVER_DELIVERY_NOT_AFTER_HUMAN');
  validateTrustRoots(finalRoots);
  const {handoffHash,...template}=finalRoots;
  need(same(template,t.newRootTemplate)&&handoffHash===digest(handoffArgs.handoff)&&
    machine.stageIntentHash===t.stageIntentHash&&machine.stageResultHash===t.stageResultHash&&
    machine.stageAuthorizationHash===t.stageAuthorizationHash&&machine.releaseHash===t.targetReleaseHash&&
    b.epoch===t.handoffEpoch&&b.issuedAt>=human.issuedAt&&c.observedAt>=human.issuedAt&&
    c.issuerSnapshotHash===t.issuerSnapshotHash&&c.issuerStateFileHash===t.issuerStateFileHash&&
    Object.values(handoffArgs.receipts).every(r=>r.body.issuedAt>=human.issuedAt),
    'FIRST_CUTOVER_POST_CONFIRMATION_DRIFT');
  const again=inspectFirstCutoverHumanJournal({...humanArgs,now});
  need(again.humanApprovalHash===human.humanApprovalHash&&
    again.humanOsReceiptHash===human.humanOsReceiptHash,'FIRST_CUTOVER_JOURNAL_CHANGED');
  return Object.freeze({schema:'mht.first-cutover-handoff-admission.v1',
    status:'HUMAN_AND_FRESH_MACHINE_GATES_INSPECTED',humanProposalHash:human.humanProposalHash,
    humanApprovalHash:human.humanApprovalHash,humanOsReceiptHash:human.humanOsReceiptHash,
    nonce:human.nonce,issuedAt:human.issuedAt,
    expiresAt:Math.min(human.expiresAt,b.expiresAt,...Object.values(handoffArgs.receipts).map(r=>r.body.expiresAt)),
    targetHash:human.targetHash,stageIntentHash:t.stageIntentHash,stageResultHash:t.stageResultHash,
    handoffHash:handoffHash,finalRootsHash:digest(finalRoots),newRootTemplateHash:t.newRootTemplateHash,
    mayExecute:false,signerAuthority:false,mayActivateBusiness:false,maySettleUnknown:false,mayReplayUnknown:false});
}
