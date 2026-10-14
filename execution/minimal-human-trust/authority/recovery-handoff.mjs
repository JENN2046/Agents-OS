// A signed, exact R17 receiver exception. This does not issue a Release,
// approve a cutover, settle an UNKNOWN, or authorize new business.
import path from 'node:path';
import {canonical,digest,verified,verifyRelease,ACTIONS,ROLES,LEASE_MS,RENEW_BEFORE_MS}
  from '../src/lease-core.mjs';
import {EXACT_R17_MIGRATION_SCOPE,certifiedClosedProject}
  from '../migration/r17-one-time-recovery-admission.mjs';

const pin=EXACT_R17_MIGRATION_SCOPE;
const fail=code=>{throw Object.assign(new Error(code),{code});};
const need=(ok,code='RECOVERY_HANDOFF_REJECTED')=>{if(!ok)fail(code);};
const same=(a,b)=>canonical(a)===canonical(b);
const hash=x=>typeof x==='string'&&/^[a-f0-9]{64}$/.test(x);
const exact=(x,keys)=>need(x&&Object.getPrototypeOf(x)===Object.prototype&&
  same(Object.keys(x).sort(),keys.slice().sort()),'RECOVERY_HANDOFF_SHAPE');
export const HANDOFF_FIELDS=Object.freeze(['schema','grantId','grantHash','releaseHash',
  'issuerSnapshotHash','installationProfile','epoch','mode','oldWriterClosed',
  'participantClosureHashes','issuedAt','expiresAt']);

export function handoffSchema(envelope){
  const schema=envelope?.body?.schema;
  need(['mht.issuer-handoff.v1','mht.issuer-handoff.v2'].includes(schema),'HANDOFF_SCHEMA');
  return schema;
}

export function validateRecoveryAdmission(a){
  exact(a,['schema','sourceReleaseId','sourceReleaseHash','targetReleaseId',
    'stageAuthorizationHash','reviewedManifestHash','recoveryEvidenceDigest',
    'issuerSnapshotHash','issuerStateFileHash','observedAt','operations']);
  need(a.schema==='mht.r17-recovery-handoff-admission.v1'&&
    a.sourceReleaseId===pin.sourceRelease&&a.targetReleaseId===pin.targetRelease&&
    ['sourceReleaseHash','stageAuthorizationHash','reviewedManifestHash','recoveryEvidenceDigest',
      'issuerSnapshotHash','issuerStateFileHash'].every(k=>hash(a[k]))&&
    Number.isSafeInteger(a.observedAt)&&a.observedAt>0,
    'RECOVERY_HANDOFF_ADMISSION');
  need(Array.isArray(a.operations)&&a.operations.length===2,'RECOVERY_HANDOFF_OPERATIONS');
  const seen=new Set();
  for(const row of a.operations){
    exact(row,['projectId','operationId','operationHash','generation','leaseHash',
      'action','outcome','originalResultAvailable','replayAllowed']);
    const expected=pin.projects.find(p=>p.projectId===row.projectId);
    need(expected&&!seen.has(row.projectId)&&row.operationId===expected.operationId&&
      row.operationHash===expected.operationHash&&row.generation===expected.generation&&
      hash(row.leaseHash)&&row.action==='find_symbol'&&row.outcome==='UNRESOLVED'&&
      row.originalResultAvailable===false&&row.replayAllowed===false,
      'RECOVERY_HANDOFF_OPERATIONS');
    seen.add(row.projectId);
  }
  return a;
}

export function verifyRecoveryHandoff(envelope,enrollmentAuthorityPublicKey,{
  grantId,release,mode,grantHash=null,issuerPublicKey=null,
}={}){
  const b=verified(envelope,enrollmentAuthorityPublicKey,'mht.issuer-handoff.v2');
  exact(b,[...HANDOFF_FIELDS,'recoveryAdmission']);
  const a=validateRecoveryAdmission(b.recoveryAdmission);
  need(mode==='recovery_only'&&b.mode===mode&&b.grantId===pin.grantId&&
    grantId===pin.grantId&&release?.body?.id===pin.targetRelease&&
    b.releaseHash===digest(release)&&b.issuerSnapshotHash===a.issuerSnapshotHash&&
    (grantHash===null||b.grantHash===grantHash)&&
    (issuerPublicKey===null||issuerPublicKey!==enrollmentAuthorityPublicKey)&&
    b.oldWriterClosed===true&&['isolated','production'].includes(b.installationProfile)&&
    hash(b.grantHash)&&hash(b.issuerSnapshotHash)&&Number.isSafeInteger(b.epoch)&&b.epoch>0&&
    Number.isSafeInteger(b.issuedAt)&&Number.isSafeInteger(b.expiresAt)&&
    b.expiresAt>b.issuedAt&&b.expiresAt-b.issuedAt<=30000&&
    a.observedAt<=b.issuedAt&&b.issuedAt-a.observedAt<=30000,
    'RECOVERY_HANDOFF_SCOPE');
  exact(b.participantClosureHashes,ROLES);
  need(ROLES.every(role=>hash(b.participantClosureHashes[role])),'RECOVERY_HANDOFF_STOP');
  return b;
}

// Must run while BOTH issuer and replay stores are locked, before the first
// durable replay.handoff binding. The ledger has no operation hashes; those
// arrive only inside the independently signed handoff, never from project IDs.
export function inspectRecoveryIssuerSnapshot({snapshot,wrapper,admission,grantId,
  issuerPublicKey,releasePublicKey,now}){
  const a=validateRecoveryAdmission(admission);
  need(Number.isSafeInteger(now)&&now>0&&a.observedAt<=now&&now-a.observedAt<=30000,
    'RECOVERY_HANDOFF_OBSERVATION_EXPIRED');
  need(wrapper?.schema===1&&Number.isSafeInteger(wrapper.revision)&&wrapper.revision>=0&&
    Number.isSafeInteger(wrapper.maxNow)&&wrapper.maxNow>=0&&wrapper.maxNow<=now&&
    same(wrapper.data,snapshot)&&digest(wrapper)===a.issuerStateFileHash&&
    digest(snapshot)===a.issuerSnapshotHash&&snapshot?.kind==='r16.issuer.v1'&&
    Array.isArray(snapshot.grants)&&snapshot.grants.length===1,
    'RECOVERY_HANDOFF_SNAPSHOT');
  const entry=snapshot.grants[0];
  const g=verified(entry.grant,issuerPublicKey,'r16.workspace.v1');
  need(grantId===pin.grantId&&g.id===grantId&&entry.version===g.version&&
    entry.status==='ACTIVE'&&same(g.actions,ACTIONS)&&g.channel==='main'&&
    Array.isArray(entry.projects),'RECOVERY_HANDOFF_GRANT');
  const projectIds=new Set();
  let matched=0;
  for(const project of entry.projects){
    need(project&&typeof project.projectId==='string'&&!projectIds.has(project.projectId)&&
      project.pending===null&&Array.isArray(project.history),'RECOVERY_HANDOFF_PROJECTS');
    projectIds.add(project.projectId);
    const operation=a.operations.find(row=>row.projectId===project.projectId);
    if(!operation){
      need(certifiedClosedProject(project,g,issuerPublicKey),'RECOVERY_HANDOFF_FOREIGN_PROJECT');
      const last=project.history.at(-1),lease=last.lease.body,closed=last.closed.body;
      need(lease.grantId===g.id&&lease.grantHash===digest(entry.grant)&&
        closed.grantId===g.id&&
        project.generation===lease.generation,'RECOVERY_HANDOFF_FOREIGN_PROJECT');
      for(const role of ROLES){
        const stop=last.stopEvidence[role].body;
        need(stop.grantVersion===lease.grantVersion&&stop.peerId===g.peers[role].id&&
          stop.requestId===lease.requestId&&hash(stop.resultsHash),'RECOVERY_HANDOFF_FOREIGN_PROJECT');
      }
      continue;
    }
    const active=project.active;
    need(project.generation===operation.generation&&active?.lease&&active.activation&&
      active.release&&active.request&&active.evidence&&
      digest(active.lease)===operation.leaseHash&&!active.closed&&!active.stopEvidence,
      'RECOVERY_HANDOFF_LEASE');
    const l=verified(active.lease,issuerPublicKey,'r16.lease.v1');
    const r=verified(active.release,releasePublicKey,'r16.release.v1');
    const activation=verified(active.activation,issuerPublicKey,'r16.activation.v1');
    exact(l,['schema','phase','grantId','grantVersion','grantHash','project','channel','versions',
      'actions','generation','previousGeneration','issuedAt','expiresAt','renewAt','requestId','releaseHash']);
    exact(activation,['schema','grantId','grantVersion','projectId','generation','leaseHash',
      'evidenceHash','activatedAt']);
    verifyRelease(active.release,releasePublicKey,
      {versions:pin.sourceVersions,actions:g.actions,now:l.issuedAt});
    const relative=path.relative(g.workspace.root,l.project?.root??'');
    need(r.id===pin.sourceRelease&&digest(active.release)===a.sourceReleaseHash&&
      same(r.versions,pin.sourceVersions)&&l.phase==='PREPARED'&&
      l.grantId===g.id&&l.grantVersion===g.version&&l.grantHash===digest(entry.grant)&&
      l.project?.id===operation.projectId&&l.project.workspaceId===g.workspace.id&&
      relative!==''&&!path.isAbsolute(relative)&&relative!=='..'&&!relative.startsWith('../')&&
      l.generation===operation.generation&&l.previousGeneration===l.generation-1&&
      l.channel===g.channel&&same(l.versions,pin.sourceVersions)&&
      l.releaseHash===a.sourceReleaseHash&&Array.isArray(l.actions)&&
      l.actions.includes('find_symbol')&&l.actions.every(action=>g.actions.includes(action))&&
      Number.isSafeInteger(l.issuedAt)&&l.expiresAt===l.issuedAt+LEASE_MS&&
      l.renewAt===l.expiresAt-RENEW_BEFORE_MS&&l.expiresAt<=now&&
      activation.grantId===g.id&&activation.grantVersion===g.version&&
      activation.projectId===project.projectId&&activation.generation===project.generation&&
      activation.leaseHash===operation.leaseHash&&activation.evidenceHash===digest(active.evidence)&&
      Number.isSafeInteger(activation.activatedAt)&&activation.activatedAt>=l.issuedAt&&
      activation.activatedAt<l.expiresAt,
      'RECOVERY_HANDOFF_LEASE');
    const request=active.request;
    need(request.schema==='r16.prepare.v1'&&request.requestId===l.requestId&&
      request.grantId===g.id&&request.grantVersion===g.version&&
      same(request.project,l.project)&&same(request.versions,l.versions)&&
      same(request.actions,l.actions)&&request.channel===g.channel&&
      Number.isSafeInteger(request.issuedAt)&&request.issuedAt<=l.issuedAt,
      'RECOVERY_HANDOFF_LEASE');
    exact(active.evidence,ROLES);
    const resultHashes=new Set();
    for(const role of ROLES){
      const proof=verified(active.evidence[role],g.peers[role].publicKey,'r16.close.v1');
      exact(proof,['schema','role','peerId','grantId','grantVersion','projectId','oldGeneration',
        'newGeneration','leaseHash','requestId','durableClosed','pending','resultsHash']);
      need(proof.role===role&&proof.peerId===g.peers[role].id&&proof.grantId===g.id&&
        proof.grantVersion===g.version&&proof.projectId===project.projectId&&
        proof.oldGeneration===l.previousGeneration&&proof.newGeneration===l.generation&&
        proof.leaseHash===operation.leaseHash&&proof.requestId===l.requestId&&
        proof.durableClosed===true&&proof.pending===0&&hash(proof.resultsHash),
        'RECOVERY_HANDOFF_ACTIVATION');
      resultHashes.add(proof.resultsHash);
    }
    need(resultHashes.size===1&&project.history.some(row=>same(row,active)),
      'RECOVERY_HANDOFF_ACTIVATION');
    matched++;
  }
  need(matched===2,'RECOVERY_HANDOFF_PROJECTS');
  return Object.freeze({status:'EXACT_TWO_READ_UNKNOWNS_ADMITTED_FOR_RECOVERY',
    issuerSnapshotHash:a.issuerSnapshotHash,issuerStateFileHash:a.issuerStateFileHash,
    recoveryAdmissionHash:digest(a),mayActivateBusiness:false,maySettleUnknown:false,
    mayReplayUnknown:false});
}
