// FIRST_TRUST_BOOTSTRAP_R1: release-root-pinned first Human OS approval readback.
// Pure, read-only admission. This module NEVER signs, enrolls, installs a key,
// releases R17, clears UNKNOWN, or stops the existing Owner writer.
import fs from 'node:fs';
import {canonical,digest,verified,verifyRelease} from '../src/lease-core.mjs';
import {protectedRuntimeFile} from '../authority/runtime-manifest.mjs';
import {validateHumanProposal,firstTrustReviewedIntent,PROJECTS_ROOT} from './approval-policy.mjs';

const ROOT='/var/lib/minimal-human-trust/human-approval';
const PRESENT='/etc/minimal-human-trust/issuer.json';
const fail=code=>{throw Object.assign(new Error(code),{code});};
const need=(ok,code='FIRST_TRUST_REJECTED')=>{if(!ok)fail(code);};
const equals=(a,b)=>canonical(a)===canonical(b);
const exact=(v,keys)=>need(v!==null&&typeof v==='object'&&!Array.isArray(v)&&
  equals(Object.keys(v).sort(),keys.slice().sort()),'FIRST_TRUST_SHAPE');
const hash=s=>typeof s==='string'&&/^[a-f0-9]{64}$/.test(s);
const readOne=(p,read)=>JSON.parse(read(p).toString());

/** Root-owned OS intent and result are the BROKER'S durable account of a
 * real local polkit check. They are not a cryptographic Human signature.
 * The trusted publisher must subsequently attest the actual ceremony and
 * use the EXISTING OS-protected Release signing root for endorsement.
 */
export function inspectFirstTrustJournal({
  proposal,policy,trustRoots,sourceRelease,sourceGrant,reviewManifest,
  now=Date.now(),readProtected=protectedRuntimeFile,
  isInstalled=()=>fs.existsSync(PRESENT),
}){
  need(typeof now==='number'&&Number.isSafeInteger(now)&&now>0&&
    typeof readProtected==='function'&&typeof isInstalled==='function','FIRST_TRUST_INPUT');
  need(isInstalled()===false,'FIRST_TRUST_ALREADY_INSTALLED');
  const checked=validateHumanProposal({proposal,policy,roots:trustRoots,now});
  need(checked.body.action==='enroll_human','FIRST_TRUST_ACTION');
  const intent=firstTrustReviewedIntent(checked);
  const source=verified(sourceRelease,trustRoots.releasePublicKey,'r16.release.v1');
  const grant=verified(sourceGrant,trustRoots.issuerPublicKey,'r16.workspace.v1');
  // Historical R15 may have expired; verify its original signature/issue window
  // but do NOT treat its expiry as renewed business permission.
  verifyRelease(sourceRelease,trustRoots.releasePublicKey,
    {versions:source.versions,actions:grant.actions,now:source.issuedAt});
  need(source.id==='r16-daily-20261012-r15'&&
    intent.sourceReleaseId===source.id&&intent.sourceReleaseHash===digest(sourceRelease)&&
    intent.grantId===grant.id&&intent.grantHash===digest(sourceGrant)&&
    intent.grantVersion===grant.version&&grant.id==='r16-projects-daily'&&
    grant.workspace.root===PROJECTS_ROOT&&grant.channel==='main'&&
    trustRoots.grantId===grant.id&&trustRoots.releaseHash===digest(sourceRelease),
    'FIRST_TRUST_SOURCE_CHANGED');
  need(reviewManifest?.schema==='r16.reviewed-installation.v1'&&
    reviewManifest.releaseId===intent.targetReleaseId&&
    digest(reviewManifest)===intent.reviewedManifestHash,'FIRST_TRUST_REVIEW_CHANGED');
  need(intent.humanUid===1000&&intent.humanSubject==='local-human:1000'&&
    checked.body.issuedAt<=now&&now<checked.body.expiresAt,'FIRST_TRUST_HUMAN_TARGET');
  const base=ROOT+'/'+checked.proposalHash;
  const osIntent=readOne(base+'.intent.json',readProtected);
  const osResult=readOne(base+'.result.json',readProtected);
  exact(osIntent,['schema','proposalHash','peerUid','processStart','confirmedAt','challengeHash']);
  need(osIntent.schema==='mht.human-os-intent.v1'&&
    osIntent.proposalHash===checked.proposalHash&&osIntent.peerUid===1000&&
    Number.isSafeInteger(osIntent.processStart)&&osIntent.processStart>0&&
    Number.isSafeInteger(osIntent.confirmedAt)&&osIntent.confirmedAt>=checked.body.issuedAt&&
    osIntent.confirmedAt<checked.body.expiresAt&&osIntent.confirmedAt<=now&&
    now-osIntent.confirmedAt<=300000&&hash(osIntent.challengeHash),
    'FIRST_TRUST_OS_CONFIRMATION');
  exact(osResult,['ok','status','firstTrustOsConfirmationOnly','proposalHash','reviewedIntent','approval']);
  need(osResult.ok===true&&osResult.status==='APPROVED_NOT_APPLIED'&&
    osResult.firstTrustOsConfirmationOnly===true&&osResult.approval===null&&
    osResult.proposalHash===checked.proposalHash&&equals(osResult.reviewedIntent,intent),
    'FIRST_TRUST_RESULT_CONFLICT');
  return Object.freeze({schema:'mht.first-trust-journal-inspection.v1',
    status:'OS_CONFIRMED_NOT_APPLIED',sourceReleaseId:source.id,
    targetReleaseId:intent.targetReleaseId,reviewedManifestHash:intent.reviewedManifestHash,
    grantHash:intent.grantHash,grantId:intent.grantId,
    humanUid:intent.humanUid,humanPublicKey:intent.humanPublicKey,
    enrollmentExpiresAt:intent.enrollmentExpiresAt,
    proposalHash:intent.proposalHash,osReceiptHash:digest({osIntent,osResult}),
    // The verified file mode matters, but this helper cannot itself
    // substitute for the trusted Release signer and its systemd credential.
    signerAuthority:false,mayInstall:false,maySignRelease:false,mayHandoffIssuer:false});
}
