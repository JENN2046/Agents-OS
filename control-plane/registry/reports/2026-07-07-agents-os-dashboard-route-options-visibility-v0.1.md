# AGENTS OS Dashboard Route Options Visibility v0.1

Date: 2026-07-07
Status: accepted
Owner: Jenn
Agent steward: Nobao
Scope: surface route-selection package in the preview-only Dashboard

## Purpose

This report records a Dashboard visibility change: when the Active Work Queue is
stopped at `No Active Automatic Construction Item`, the Dashboard now exposes
the local route-selection package as structured preview-only options.

This is not route selection, queue promotion, runtime activation, provider
execution, Memory writing, or external publication.

## Changed Files

```text
execution/agents-os-dashboard/dashboard.py
execution/agents-os-dashboard/test-dashboard.py
execution/agents-os-dashboard/dashboard.schemas.json
execution/agents-os-dashboard/dashboard-manifest.json
execution/agents-os-dashboard/README.md
```

## Behavior

Dashboard summary now includes:

```text
route_selection.status=awaiting_jenn_selection
route_selection.package_exists=true
route_selection.requires_jenn_decision=true
route_selection.option_count=5
route_selection.route_auto_selection_authorized=false
route_selection.queue_promotion_authorized=false
route_selection.execution_authorized=false
route_selection.raw_content_output=false
```

The exposed options come from:

```text
control-plane/registry/reports/2026-07-07-agents-os-next-route-selection-package-v0.1.md
```

The Dashboard surfaces only structured option metadata:

```text
option_id
title
first_safe_package
must_keep
```

## Route Options Surfaced

```text
A: VCPToolBox Runtime Recovery Or Controlled First-Use
B: Formal Memory Loop
C: External Git Publication Exact Gate
D: Provider Execution Design Gate
E: New AGENTS OS Construction Route
```

## Boundary

- No route was selected.
- No queue item was promoted.
- No service was started.
- No executor was run.
- No provider call was performed.
- No host dispatcher route was executed.
- No VCPToolBox runtime, config, plugin, dependency, build, or service action
  was performed.
- No formal Memory write was performed.
- No external write, push, tag, release, deploy, publish, history rewrite,
  reset, clean, bulk move, delete, rename, overwrite, or destructive operation
  was performed.
- No `state-private/` content was read.
- No secrets, tokens, cookies, credentials, private raw memory, provider raw
  responses, active runtime config values, raw logs, private Notion page
  contents, or private Notion page URLs were read or output.

## Validation

```text
test-dashboard=PASS cases=13 failures=0
dashboard summary=PASS route_selection.status=awaiting_jenn_selection option_count=5 route_auto_selection_authorized=false queue_promotion_authorized=false execution_authorized=false
dashboard validate=PASS route_selection.status=awaiting_jenn_selection option_count=5
machine preview-now=PASS source_item=No Active Automatic Construction Item blocked=true actionable=false requires_jenn_decision=true execution_authorized=false
validate-document-registry=PASS documents=295 pass=295 warn=0 fail=0
validate-federated-document-registry=PASS registries=3 pass=3 warn=0 fail=0
docctl status=PASS score=100 eligible_95=True hard_gates=0
docctl doctor=PASS registries=3 documents=337 scanned_files=358 unregistered=0 warn=0 fail=0
```

## Decision

Accepted as Dashboard visibility hardening. The Dashboard can now show Jenn the
available route choices while preserving the Machine stop-state.
