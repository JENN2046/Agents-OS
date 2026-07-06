# Validation Scripts

Status: validation script index. Guidance only; not authorization to execute
scripts.

Source reference:

```text
A:\AGENTS_OS_Workspace\ops\scripts\README.AGENTS_OS.md
```

Canonical security authority:

```text
governance/SECURITY_BOUNDARIES.md
```

## Included Validation Files

```text
validate-no-secrets.sh
validate-extension-manifests.sh
validate-workspace.sh
```

These files are migrated as reviewed validation candidates. They are not made
executable by default, and this README intentionally avoids copy-ready command
examples.

## Not Included In This Batch

```text
sync-upstream-vcp.sh
validate-domain-bridges.sh
validate-execution-profiles.sh
validate-policy-packs.sh
validate-vcp-runtime.sh
```

`sync-upstream-vcp.sh` is maintenance/sync-sensitive and remains deferred.

The domain bridge, execution profile, and policy pack validators are placeholder
or future validators and remain deferred.

`validate-vcp-runtime.sh` is runtime/git-adjacent and waits for runtime
migration and git-output policy.

`validate-workspace.sh` is present as a reviewed workspace-path validation
candidate. It references the current WSL control-plane registry path and remains
non-executable by default.

## Execution Boundary

Validation script invocation is deferred until a separate explicit validation
approval.

Any future script use must state:

```text
scope
working directory
expected output
whether full paths may be reported
whether failures stop the calling task
receipt location
```

Do not treat the existence of these files as permission to run them.

## Output Boundary

`validate-no-secrets.sh` is path-only, but path-only output can still reveal
sensitive filenames. Future receipts or reports should prefer counts or
redacted summaries unless the user separately approves full path disclosure.

The validation scripts must not print secret values or file contents.

## Scope Boundary

`validate-extension-manifests.sh` preserves workspace-relative `./extensions`
scope. This batch does not narrow it to `extensions/vcp-toolbox-jenn/` and does
not treat that observed directory as a final extension-assets target.

## Default Safety Rules

```text
no script execution by default
no executable-bit changes by default
no remote actions
no branch movement
no release
no deploy
no secret value printing
no private-state reading
```
