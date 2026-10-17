// FIRST_TRUST_BOOTSTRAP_R1: reuse historical R17 exhaustive proof checks.
// Current manifest digest supplied only from root-protected reviewed publisher.
// This module never signs, installs, replays, or settles an UNKNOWN.
// Read-only admissibility for a single bounded R15 -> R17 recovery migration.
// This file neither signs releases nor installs files nor accepts a user-provided
// override of the exact two production operation identities.
import {canonical,digest,publicKey,verified,verifyRelease} from '../src/lease-core.mjs';
import {SOURCE19_BASELINE,inspectSourcePublicConfiguration,inspectSourceOwnerConfiguration} from '../authority/source-baseline.mjs';

const pin=Object.freeze({
  sourceRelease:'r16-daily-20261012-r15',
  targetRelease:'r16-daily-20261012-r17',
  grantId:'r16-projects-daily',
  sourceVersions:Object.freeze({
    app:'235a5b919c65ac1d73290732d2b2014c24a338cc4b6795a5064e804803ec1e7a',
    bridge:'9c58c33478388003fd52da0cb15736ec951a9bfc9cf29738e20de5d741921352',
    native:'76319c50acaec649967986c1f12e6923ba4f664ac3230596ed2703fce3470ae6'
  }),
  projects:Object.freeze([
    Object.freeze({projectId:'p2vox',operationId:'c434da49-055a-43dc-a3e3-695cce137909',generation:30,operationHash:'fd13e74ce69cb8ec30817ca0a48631cf3a6b6b2b08a410cc1b442df41992cc1f'}),
    Object.freeze({projectId:'pmog2',operationId:'d0364f8b-3a68-4ca2-a396-7953b29cee4c',generation:38,operationHash:'38f6af1386e78e5d7ccd0710077d6a3a5e753e81722dd10f11a3a2ff9bd85da1'})
  ])
});
export const EXACT_R17_MIGRATION_SCOPE=pin;
export const EXACT_SOURCE19_R17_MIGRATION_SCOPE=Object.freeze({...pin,
 sourceRelease:SOURCE19_BASELINE.releaseId,sourceVersions:SOURCE19_BASELINE.versions});
const chk=(ok,code='R17_MIGRATION_REJECTED')=>{if(!ok)throw Object.assign(Error(code),{code});};
const eq=(a,b)=>canonical(a)===canonical(b);
const clone=x=>JSON.parse(canonical(x));
const shape=x=>x!==null&&typeof x==='object'&&!Array.isArray(x);
const entry=(rows,id,field='id')=>Array.isArray(rows)?rows.find(x=>x?.[field]===id):null;
export function certifiedClosedProject(project,grant,issuerPublicKey){
  if(project?.active!==null||project?.pending!==null||!Array.isArray(project.history)||project.history.length===0)return false;
  const last=project.history.at(-1);
  if(!last?.closed||!last?.stopEvidence||!last?.lease)return false;
  try {
    const oldLease=verified(last.lease,issuerPublicKey,'r16.lease.v1');
    const closed=verified(last.closed,issuerPublicKey,'r16.closed.v1');
    if(closed.projectId!==project.projectId||oldLease.project.id!==project.projectId||
      closed.generation!==oldLease.generation||closed.leaseHash!==digest(last.lease)||
      closed.evidenceHash!==digest(last.stopEvidence))return false;
    const hashes=new Set();
    for(const role of ['app','bridge','native']){
      const proof=verified(last.stopEvidence[role],grant.peers[role].publicKey,'r16.stopped.v1');
      if(proof.role!==role||proof.grantId!==grant.id||proof.projectId!==project.projectId||
        proof.generation!==oldLease.generation||proof.leaseHash!==digest(last.lease)||
        proof.durableClosed!==true||proof.pending!==0)return false;
      hashes.add(proof.resultsHash);
    }
    return hashes.size===1;
  } catch{return false;}
}

// A pure, unprivileged evidence validator. Its output is NEVER an Owner approval,
// systemd signing capability, or permission to run business operations.
export function inspectRecoveryMigrationEvidence(evidence,policy,verifyCrownCall) {
  const selected=policy?.sourceRelease===SOURCE19_BASELINE.releaseId?EXACT_SOURCE19_R17_MIGRATION_SCOPE:pin;
  chk(shape(evidence)&&shape(policy)&&Array.isArray(policy.projects)&&policy.projects.length===2&&
    eq(policy.projects,pin.projects)&&eq(policy.sourceVersions,selected.sourceVersions)&&
    policy.sourceRelease===selected.sourceRelease&&policy.targetRelease===pin.targetRelease&&
    policy.grantId===pin.grantId&&/^[a-f0-9]{64}$/.test(policy.reviewDigest),
    'R17_SCOPE_NOT_PINNED');
  // The trusted runtime must inject its exact, release-manifest-verified Crown
  // call verifier. Neither this helper nor caller-controlled JSON can substitute.
  chk(typeof verifyCrownCall==='function','TRUSTED_VERIFIER_MISSING');
  const {publicConfiguration,issuerState,ownerConfiguration,appState,bridgeState,nativeStates,
    appProjectStates,bridgeProjectStates,appArchives,nativeResults,reviewManifest,now}=evidence;
  chk(Number.isSafeInteger(now)&&now>0&&shape(publicConfiguration)&&shape(reviewManifest));
  chk(digest(reviewManifest)===policy.reviewDigest&&reviewManifest.releaseId===policy.targetRelease,'REVIEW_NOT_EXACT');
  const release=verified(publicConfiguration.release,publicConfiguration.releasePublicKey,'r16.release.v1');
  const grant=verified(publicConfiguration.grant,publicConfiguration.issuerPublicKey,'r16.workspace.v1');
  inspectSourcePublicConfiguration(publicConfiguration);
  // Recovery validates signed R15 at its original issuance time. It does not
  // refresh its expired business authority or run any old operation.
  chk(release.issuedAt<=now,'SOURCE_RELEASE_IN_FUTURE');
  verifyRelease(publicConfiguration.release,publicConfiguration.releasePublicKey,
    {versions:publicConfiguration.versions,actions:grant.actions,now:release.issuedAt});
  chk(release.id===policy.sourceRelease&&grant.id===policy.grantId&&grant.status!=='REVOKED','SOURCE_RELEASE_MISMATCH');
  chk(eq(publicConfiguration.versions,policy.sourceVersions)&&eq(release.versions,policy.sourceVersions),'SOURCE_VERSION_MISMATCH');
  chk(eq(Object.keys(reviewManifest.artifacts).sort(),['app','bridge','native']),'REVIEW_NOT_EXACT');
  chk(issuerState?.kind==='r16.issuer.v1'&&Array.isArray(issuerState.grants)&&issuerState.grants.length===1,'OWNER_STATE_UNTRUSTED');
  const issuerGrant=issuerState.grants[0];
  chk(eq(issuerGrant.grant,publicConfiguration.grant)&&issuerGrant.status==='ACTIVE'&&issuerGrant.version===grant.version,'GRANT_STATE_DRIFT');
  chk(ownerConfiguration?.kind==='r16.owner.configuration.v1'&&
    ownerConfiguration.activeGrantId===grant.id&&ownerConfiguration.trust?.releasePublicKey===publicConfiguration.releasePublicKey&&
    ownerConfiguration.replacement===null&&Array.isArray(ownerConfiguration.blockedProjects)&&
    ownerConfiguration.blockedProjects.length===0,'OWNER_STATE_DRIFT');
  inspectSourceOwnerConfiguration(publicConfiguration,ownerConfiguration,now);
  chk(Array.isArray(issuerGrant.projects)&&Array.isArray(appState?.operations)&&Array.isArray(bridgeState?.calls)&&
    shape(nativeStates)&&shape(appProjectStates)&&shape(bridgeProjectStates)&&
    shape(appArchives)&&shape(nativeResults),'MISSING_EVIDENCE');
  const pins=policy.projects;
  chk(new Set(pins.map(x=>x.projectId)).size===2&&new Set(pins.map(x=>x.operationId)).size===2,'DUPLICATE_TARGET');
  const pinnedIds=new Set(pins.map(x=>x.operationId));
  const pinnedProjects=new Set(pins.map(x=>x.projectId));
  for(const group of [appState.operations,bridgeState.calls]) {
    const unresolved=group.filter(x=>['UNKNOWN','INFLIGHT'].includes(x.status));
    chk(unresolved.length===2&&unresolved.every(x=>pinnedIds.has(x.id)),'FOREIGN_OPERATION_UNRESOLVED');
  }
  const inspected=[];
  for(const expected of pins) {
    const project=expected.projectId,id=expected.operationId;
    const a=entry(appState.operations,id),b=entry(bridgeState.calls,id),archive=appArchives[project];
    const native=nativeStates[project];
    chk(a?.projectId===project&&b?.projectId===project&&a.status==='UNKNOWN'&&b.status==='UNKNOWN'&&
      shape(archive)&&shape(native)&&nativeResults[project]===false,'RESULT_OR_SCOPE_MISMATCH');
    chk(eq(a.operation,b.operation)&&eq(a.operation,archive.operation),'OPERATION_DIVERGED');
    const original=verified(archive.operation,grant.peers.app.publicKey,'r16.operation.v1');
    chk(original.id===id&&original.projectId===project&&original.grantId===grant.id&&
      original.channel===grant.channel&&original.generation===expected.generation&&
      original.action==='find_symbol'&&
      digest(archive.operation)===expected.operationHash,'READ_OPERATION_NOT_EXACT');
    // Verify the expired Crown proof at its signed issuing timestamp. Never
    // reissue it, never replay FindSymbol, and never treat its result as known.
    const raw=JSON.parse(Buffer.from(archive.proof.payload_b64,'base64').toString('utf8'));
    const request=verifyCrownCall(archive.proof,publicKey(grant.peers.app.publicKey),raw.issued_at);
    chk(request.request_id===id&&request.request.action==='find_symbol'&&
      request.command==='FindSymbol'&&request.issued_at<=now&&
      original.payloadHash===digest(request),'CROWN_PROOF_NOT_EXACT');
    const row=entry(native.operations,id);
    chk(row?.status==='UNKNOWN'&&row.projectId===project&&row.generation===expected.generation&&
      row.hash===expected.operationHash,'NATIVE_RECORD_NOT_EXACT');
    chk(native.active?.lease&&eq(native.closing,native.active.lease)&&native.pending===null,'NATIVE_NOT_DRAINING');
    const lease=verified(native.active.lease,publicConfiguration.issuerPublicKey,'r16.lease.v1');
    chk(lease.grantId===grant.id&&lease.grantVersion===grant.version&&lease.project.id===project&&
      lease.generation===expected.generation&&lease.channel===grant.channel&&
      lease.actions.includes('find_symbol')&&now>=lease.expiresAt&&
      original.leaseHash===digest(native.active.lease),'LEASE_NOT_EXACT');
    chk(native.operations.filter(x=>x.status!=='KNOWN').length===1,'NATIVE_FOREIGN_UNRESOLVED');
    for(const participant of [appProjectStates[project],bridgeProjectStates[project]]){
      const originalRow=entry(participant?.operations,id);
      chk(originalRow?.status==='UNKNOWN'&&originalRow.hash===expected.operationHash&&
        originalRow.projectId===project&&originalRow.generation===expected.generation&&
        participant.pending===null&&participant.active?.lease&&
        eq(participant.active.lease,native.active.lease)&&
        eq(participant.closing,participant.active.lease)&&
        participant.operations.filter(row=>row.status!=='KNOWN').length===1,'PARTICIPANT_RECORD_DRIFT');
    }
    const ownerProject=entry(issuerGrant.projects,project,'projectId');
    chk(ownerProject?.active&&ownerProject?.pending===null&&
      eq(ownerProject.active.lease,native.active.lease),'OWNER_LEASE_DRIFT');
    const activation=verified(ownerProject.active.activation,publicConfiguration.issuerPublicKey,'r16.activation.v1');
    chk(activation.grantId===grant.id&&activation.projectId===project&&
      activation.generation===expected.generation&&activation.leaseHash===digest(native.active.lease),
      'OWNER_ACTIVATION_DRIFT');
    inspected.push({project_id:project,operation_id:id,generation:expected.generation,
      action:'find_symbol',operation_sha256:expected.operationHash,original_result_available:false,
      outcome:'UNRESOLVED',replay_allowed:false});
  }
  const elsewhere=issuerGrant.projects.filter(x=>!pinnedProjects.has(x.projectId));
  const otherProjectsClosed=elsewhere.every(x=>certifiedClosedProject(x,grant,publicConfiguration.issuerPublicKey));
  // A closed project is not authorized to run again by this evidence.
  chk(issuerGrant.projects.filter(x=>pinnedProjects.has(x.projectId)).length===2,'OWNER_TARGETS_NOT_EXACT');
  return Object.freeze({schema:'r17.one-time-recovery-admission.v1',
    status:otherProjectsClosed?'PENDING_TRUSTED_QUIESCENCE_AND_SIGNER':'OTHER_PROJECTS_MUST_QUIESCE',
    old_release:release.id,proposed_release:policy.targetRelease,grant_id:grant.id,
    review_sha256:policy.reviewDigest,old_signed_versions:clone(policy.sourceVersions),
    operations:Object.freeze(inspected.map(x=>Object.freeze(x))),other_projects_closed:otherProjectsClosed,
    exact_owner_snapshot_digest:digest({issuerState,ownerConfiguration}),
    signer_authority:false,may_install_or_activate:false,may_settle_unknown:false});
}

// The current reviewed R17 manifest SHA must be supplied by the trusted
// fixed-path Release publisher. The caller-visible result grants no authority.
export function inspectReviewedR17MigrationEvidence(evidence,rootPinnedReviewDigest,verifyCrownCall) {
  chk(typeof rootPinnedReviewDigest==='string'&&/^[a-f0-9]{64}$/.test(rootPinnedReviewDigest),
    'REVIEW_NOT_EXACT');
  const selected=evidence?.publicConfiguration?.release?.body?.id===SOURCE19_BASELINE.releaseId?EXACT_SOURCE19_R17_MIGRATION_SCOPE:pin;
  return inspectRecoveryMigrationEvidence(evidence,{...selected,reviewDigest:rootPinnedReviewDigest},verifyCrownCall);
}
