# Snapshot-Bound Worker Pilot Prep

CEA-016 prepares a snapshot-bound Worker pilot without starting a managed Worker
session.

The prep step verifies that the CEA-011 snapshot manifest and CEA-015 prompt
annex agree on the same snapshot ID. It then writes a Worker plan that pins
`cwd` to the snapshot root and uses read-only sandbox policy.

## Boundary

- Mode is `PREP_ONLY`.
- Managed Worker is not started.
- Managed Reviewer is not started.
- Worker `cwd` is the snapshot root only.
- Sandbox policy is `{ "type": "readOnly", "networkAccess": false }`.
- Prompt annex use remains explicit and packet-only.
- Direct real repository `cwd` remains blocked.

## Plan Shape

```json
{
  "planVersion": 1,
  "planId": "cea-016-snapshot-worker-plan-20260707000000",
  "mode": "PREP_ONLY",
  "snapshotId": "cea-011-safe-snapshot-20260707080426",
  "workerCwd": "data/snapshots/cea-011-safe-snapshot-20260707080426",
  "annexId": "cea-015-prompt-annex-20260707000000",
  "sandboxPolicy": {
    "type": "readOnly",
    "networkAccess": false
  },
  "boundary": {
    "managedWorkerStarted": false,
    "managedReviewerStarted": false,
    "directRealRepo": "BLOCKED",
    "workerCwdPolicy": "SNAPSHOT_ONLY",
    "autoInjection": "DISABLED",
    "rawContentIncluded": false
  }
}
```

## Storage

Worker prep plans are written under:

```text
data/worker-pilots/<plan_id>.worker-plan.json
```

## Pilot Command

```bash
npm run worker:prepare
```

The command reads the CEA-011 manifest and CEA-015 annex, verifies the
snapshot-bound chain, and writes a prep-only Worker plan. It does not call App
Server or start managed sessions.

## Live Worker Command

```bash
npm run worker:live
```

The live command reads the prep plan, starts `codex app-server --stdio` with the
process cwd set to the snapshot root, starts one managed Worker thread with the
same snapshot cwd, and runs one read-only, network-off Worker turn.

The live Worker is instructed to return structured `DONE` JSON only. Reviewer is
not started by this command.

Required live boundary:

- App Server process cwd: snapshot root
- Worker thread cwd: snapshot root
- Worker turn cwd: snapshot root
- sandbox policy: `{ "type": "readOnly", "networkAccess": false }`
- direct real repository cwd: `BLOCKED`
- Reviewer: `NOT_STARTED`

## Live Reviewer Command

```bash
npm run reviewer:live
```

CEA-017 starts one managed Reviewer thread using the same snapshot root as cwd.
It consumes the CEA-016 Worker DONE evidence and returns structured
`REVIEWER_DECISION`.

Required Reviewer boundary:

- App Server process cwd: snapshot root
- Reviewer thread cwd: snapshot root
- Reviewer turn cwd: snapshot root
- sandbox policy: `{ "type": "readOnly", "networkAccess": false }`
- Worker DONE evidence used: `YES`
- direct real repository cwd: `BLOCKED`
