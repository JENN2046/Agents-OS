// Pure target validation. No authorization is inferred from UID or this module.
import {canonical,digest,verified,publicKey,ACTIONS} from '../src/lease-core.mjs';
import {validateTrustRoots} from '../src/minimal-trust-issuer-once.mjs';
const fail=code=>{throw Object.assign(new Error(code),{code});};
const need=(value,code='HUMAN_TARGET_REJECTED')=>{if(!value)fail(code);};
const exact=(value,names)=>need(value&&typeof value==='object'&&!Array.isArray(value)&&
 canonical(Object.keys(value).sort())===canonical(names.slice().sort()));
const hash=x=>typeof x==='string'&&/^[a-f0-9]{64}$/.test(x);
const id=x=>typeof x==='string'&&/^[A-Za-z0-9_-]{1,128}$/.test(x);
export const PROJECTS_ROOT='/home/jenn/AGENTS_OS_Workspace/projects';
export function validateHumanProposal({proposal,policy,roots,now=Date.now()}){
 exact(policy,['schema','proposalHash','grantId','grantHash','grantVersion','releaseHash','releaseId',
   'humanPublicKey','workspaceId','workspaceRoot','workspaceDev','workspaceIno','installationProfile']);
 need(policy.schema==='mht.human-pending-policy.v1'&&hash(policy.proposalHash)&&
   hash(policy.grantHash)&&hash(policy.releaseHash)&&id(policy.grantId)&&id(policy.releaseId)&&id(policy.workspaceId)&&
   Number.isSafeInteger(policy.grantVersion)&&policy.grantVersion>=1&&policy.workspaceRoot===PROJECTS_ROOT&&Number.isSafeInteger(policy.workspaceDev)&&policy.workspaceDev>=0&&
   Number.isSafeInteger(policy.workspaceIno)&&policy.workspaceIno>0&&
   ['isolated','production'].includes(policy.installationProfile));
 validateTrustRoots(roots);
 for(const name of ['issuerPublicKey','releasePublicKey','enrollmentAuthorityPublicKey'])publicKey(roots[name]);
 publicKey(policy.humanPublicKey);
 need(![roots.issuerPublicKey,roots.releasePublicKey,roots.enrollmentAuthorityPublicKey].includes(policy.humanPublicKey),'HUMAN_KEY_SEPARATION');
 need(roots.schema==='mht.trust-roots.v1'&&roots.grantId===policy.grantId&&
   roots.releaseHash===policy.releaseHash&&roots.installationProfile===policy.installationProfile&&
   digest(proposal)===policy.proposalHash,'HUMAN_ROOT_BINDING');
 // A separately admitted release publisher prepares a concrete proposal.
 // Merely writing an unsigned request as the desktop user grants nothing.
 const p=verified(proposal,roots.releasePublicKey,'mht.human-proposal.v1');
 exact(p,['schema','action','grantId','expectedVersion','expectedGrantHash','releaseId','releaseHash',
   'nonce','issuedAt','expiresAt','target']);
 need(['revoke_grant','create_grant','change_trust','enroll_human'].includes(p.action)&&
   p.grantId===policy.grantId&&p.expectedVersion===policy.grantVersion&&p.expectedGrantHash===policy.grantHash&&
   p.releaseId===policy.releaseId&&p.releaseHash===policy.releaseHash&&id(p.nonce)&&p.nonce.length>=16&&
   Number.isSafeInteger(p.issuedAt)&&Number.isSafeInteger(p.expiresAt)&&p.issuedAt<=now&&now<p.expiresAt&&
   p.expiresAt-p.issuedAt<=300000,'HUMAN_PROPOSAL_EXPIRED_OR_CHANGED');
 if(p.action==='revoke_grant')exact(p.target,[]);
 if(p.action==='create_grant'){
   exact(p.target,['workspaceId','workspaceRoot','channel','actions']);
   need(p.target.workspaceId===policy.workspaceId&&p.target.workspaceRoot===PROJECTS_ROOT&&p.target.channel==='main'&&
     Array.isArray(p.target.actions)&&p.target.actions.length>0&&new Set(p.target.actions).size===p.target.actions.length&&
     p.target.actions.every(a=>ACTIONS.includes(a)),'HUMAN_SCOPE_EXPANSION');
 }
 if(p.action==='change_trust'){
   exact(p.target,['oldRootHash','newRootHash','permissionsUnchanged']);
   need(p.target.oldRootHash===digest(roots)&&hash(p.target.newRootHash)&&
     p.target.newRootHash!==p.target.oldRootHash&&p.target.permissionsUnchanged===true,'HUMAN_SCOPE_EXPANSION');
 }
 if(p.action==='enroll_human'){
   exact(p.target,['humanUid','humanSubject','humanPublicKey','enrollmentExpiresAt','targetReleaseId','reviewedManifestHash']);
   publicKey(p.target.humanPublicKey);
   need(p.target.humanUid===1000&&p.target.humanSubject==='local-human:1000'&&
     p.target.humanPublicKey===policy.humanPublicKey&&p.target.targetReleaseId==='r16-daily-20261012-r17'&&
     hash(p.target.reviewedManifestHash)&&Number.isSafeInteger(p.target.enrollmentExpiresAt)&&
     p.target.enrollmentExpiresAt>now&&p.target.enrollmentExpiresAt<=now+366*86400000,'HUMAN_ENROLLMENT_TARGET');
 }
 return Object.freeze({body:p,proposalHash:policy.proposalHash,summary:{action:p.action,grantId:p.grantId,
   expectedVersion:p.expectedVersion,expectedGrantHash:p.expectedGrantHash,releaseId:p.releaseId,
   releaseHash:p.releaseHash,nonce:p.nonce,workspaceRoot:policy.workspaceRoot,workspaceDev:policy.workspaceDev,workspaceIno:policy.workspaceIno,target:p.target,
   installationProfile:policy.installationProfile}});
}
export function humanApprovalBody(checked,{now=Date.now()}={}){
 const p=checked.body;
 need(now>=p.issuedAt&&now<p.expiresAt,'HUMAN_CONFIRMATION_EXPIRED');
 if(p.action==='revoke_grant')return {schema:'mht.human-authorization.v1',action:p.action,
   grantId:p.grantId,expectedVersion:p.expectedVersion,expectedGrantHash:p.expectedGrantHash,
   releaseId:p.releaseId,issuedAt:now,nonce:p.nonce};
 // Deliberately not an issuer createGrant or a release signature: no matching
 // mutation consumer exists yet. A signed explicit approval is not activation.
 return {schema:'mht.human-reviewed-change.v1',action:p.action,proposalHash:checked.proposalHash,
   grantId:p.grantId,expectedVersion:p.expectedVersion,expectedGrantHash:p.expectedGrantHash,
   releaseHash:p.releaseHash,nonce:p.nonce,issuedAt:now,target:p.target};
}

/**
 * First enrollment has no Human signing key yet. The signed proposal may
 * be shown to the trusted OS broker, but this is NOT a signed enrollment,
 * a release, or an issuer handoff.
 */
export function firstTrustReviewedIntent(checked){
 need(checked?.body?.action==='enroll_human','FIRST_TRUST_ONLY');
 const p=checked.body,t=p.target;
 exact(t,['humanUid','humanSubject','humanPublicKey','enrollmentExpiresAt','targetReleaseId','reviewedManifestHash']);
 need(t.humanUid===1000&&t.humanSubject==='local-human:1000'&&
   t.targetReleaseId==='r16-daily-20261012-r17'&&hash(t.reviewedManifestHash),'FIRST_TRUST_SCOPE');
 return Object.freeze({schema:'mht.first-trust-reviewed-intent.v1',
   proposalHash:checked.proposalHash,grantId:p.grantId,grantVersion:p.expectedVersion,
   grantHash:p.expectedGrantHash,sourceReleaseId:p.releaseId,sourceReleaseHash:p.releaseHash,
   targetReleaseId:t.targetReleaseId,reviewedManifestHash:t.reviewedManifestHash,
   humanUid:t.humanUid,humanSubject:t.humanSubject,humanPublicKey:t.humanPublicKey,
   enrollmentExpiresAt:t.enrollmentExpiresAt,nonce:p.nonce,
   mayInstall:false,maySignRelease:false,mayHandoffIssuer:false});
}
