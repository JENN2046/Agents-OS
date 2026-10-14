// G1-D signed stop barrier. An untrusted evidence validator, never an OS
// admission stop itself. Each actual runtime must stop business before it signs.
import {verified,verifyRelease,digest,canonical,ROLES,ACTIONS} from './lease-core.mjs';
import {verifyHistoricalRecoveryRelease} from './cloud-delivery-projector.mjs';
const reject=c=>{throw Object.assign(new Error(c),{code:c});};
const check=(x,c='ADMISSION_STOP_UNVERIFIED')=>{if(!x)reject(c);};
const same=(a,b)=>canonical(a)===canonical(b);
const exact=(a,fields)=>check(a&&typeof a==='object'&&!Array.isArray(a)&&
 same(Object.keys(a).sort(),fields.slice().sort()),'STOP_SHAPE');
const boundedId=id=>typeof id==='string'&&/^[A-Za-z0-9_-]{1,128}$/.test(id);
export function verifySignedBusinessStop({
  grant,issuerPublicKey,release,releasePublicKey,delivery,receipts,
  expectedRevision,expectedReviewDigest,expectedUnresolvedIds,expectedResultsHashes,stopEpoch,now=Date.now(),
}){
  const g=verified(grant,issuerPublicKey,'r16.workspace.v1');
  const r=verified(release,releasePublicKey,'r16.release.v1');
  verifyHistoricalRecoveryRelease(release,releasePublicKey,{versions:r.versions,actions:g.actions,now,priorRelease:release});
  check(same(g.actions,ACTIONS)&&Number.isSafeInteger(expectedRevision)&&expectedRevision>0,
    'STOP_GRANT_SCOPE');
  check(/^[0-9a-f]{64}$/.test(expectedReviewDigest)&&boundedId(stopEpoch)&&
    Array.isArray(expectedUnresolvedIds)&&expectedUnresolvedIds.length<=4096&&
    expectedUnresolvedIds.every(boundedId)&&
    new Set(expectedUnresolvedIds).size===expectedUnresolvedIds.length,'STOP_EXACT_TARGET');
  exact(expectedResultsHashes,ROLES);
  check(ROLES.every(role=>/^[0-9a-f]{64}$/.test(expectedResultsHashes[role])),
    'STOP_RESULTS_TARGET');
  const envelope=verified(delivery,issuerPublicKey,'r16.configuration-delivery.v1');
  check(envelope.revision===expectedRevision&&
    envelope.control?.connectRequested===false&&
    envelope.control?.grantId===g.id&&
    ['ACTIVE','REVOKED'].includes(envelope.control?.status)&&
    Number.isSafeInteger(envelope.control?.grantVersion)&&envelope.control.grantVersion>=g.version&&
    envelope.publicConfig?.issuerPublicKey===issuerPublicKey&&
    envelope.publicConfig?.releasePublicKey===releasePublicKey&&
    same(envelope.publicConfig?.versions,r.versions)&&
    same(envelope.publicConfig?.peers,g.peers)&&
    envelope.publicConfig?.channel===g.channel&&
    envelope.publicConfig?.grant&&same(envelope.publicConfig.grant,grant)&&
    envelope.publicConfig?.release&&same(envelope.publicConfig.release,release),
    'STOP_CLOUD_CONTROL');
  exact(receipts,ROLES);
  const all=[];
  const sorted=[...expectedUnresolvedIds].sort();
  for(const role of ROLES){
    const body=verified(receipts[role],g.peers[role].publicKey,'mht.business-stopped.v2');
    exact(body,['schema','role','peerId','grantId','releaseId','revision','reviewDigest',
      'stopEpoch','issuedAt','expiresAt','stopped','inflight','unresolved',
      'grantVersion','releaseHash','runtimeVersion','resultsHash']);
    check(body.role===role&&body.peerId===g.peers[role].id&&body.grantId===g.id&&
      body.releaseId===r.id&&body.releaseHash===digest(release)&&
      body.runtimeVersion===r.versions[role]&&
      body.grantVersion===envelope.control.grantVersion&&
      body.resultsHash===expectedResultsHashes[role]&&body.revision===expectedRevision&&
      body.reviewDigest===expectedReviewDigest&&body.stopEpoch===stopEpoch&&
      body.stopped===true&&body.inflight===0&&
      Number.isSafeInteger(body.issuedAt)&&Number.isSafeInteger(body.expiresAt)&&
      body.issuedAt<=now&&now<body.expiresAt&&body.expiresAt-body.issuedAt<=30000&&
      Array.isArray(body.unresolved)&&body.unresolved.every(boundedId)&&
      same([...body.unresolved].sort(),sorted),'STOP_ROLE_MISMATCH');
    all.push({role,proofDigest:digest(receipts[role]),resultsHash:body.resultsHash});
  }
  return Object.freeze({schema:'mht.stop-evidence-inspection.v1',result:'SIGNED_ROLES_MATCH',
    stopEpoch,reviewDigest:expectedReviewDigest,releaseId:r.id,releaseHash:digest(release),revision:expectedRevision,
    proofHashes:all,signerAuthority:false,
    runtimeStateAttested:false,mayDeploy:false,mayClearUnknown:false});
}
