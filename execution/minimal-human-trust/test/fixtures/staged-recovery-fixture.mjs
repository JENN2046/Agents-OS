// Synthetic signed stage/OS/STOP observations, never production Human proof.
import {digest,signed} from '../../src/lease-core.mjs';
import {EXACT_R17_MIGRATION_SCOPE} from '../../migration/r17-one-time-recovery-admission.mjs';
import {stagedHandoffFixture} from './staged-handoff-fixture.mjs';
export function stagedRecoveryFixture(options={}){
  const f=stagedHandoffFixture({profile:'isolated',physical:true,...options});
  f.snapshot.maxNow=f.args.now-3600001;
  f.files.set('/var/lib/minimal-human-trust/issuer/state.json',structuredClone(f.snapshot));
  const admission={schema:'mht.r17-recovery-handoff-admission.v1',
    sourceReleaseId:f.r15.body.id,sourceReleaseHash:digest(f.r15),targetReleaseId:f.r17.body.id,
    stageAuthorizationHash:digest(f.authorization),reviewedManifestHash:digest(f.args.reviewManifest),
    recoveryEvidenceDigest:f.authorization.recoveryEvidenceDigest,
    issuerSnapshotHash:digest(f.snapshot.data),issuerStateFileHash:digest(f.snapshot),
    observedAt:f.args.now-1000,operations:EXACT_R17_MIGRATION_SCOPE.projects.map(row=>
      ({...row,leaseHash:digest(f.snapshot.data.grants[0].projects.find(p=>p.projectId===row.projectId).active.lease),
        action:'find_symbol',outcome:'UNRESOLVED',originalResultAvailable:false,replayAllowed:false}))};
  f.args.handoff=signed({...f.args.handoff.body,schema:'mht.issuer-handoff.v2',
    recoveryAdmission:admission},f.enroller);
  f.admission=admission;
  return f;
}
