#!/usr/bin/env bash
set -euo pipefail

required_paths=(
  "_ROOT_POLICY.md"
  "_DIRECTORY_PRINCIPLES.md"
  "_MIGRATION_MAP.md"
  "control-plane/README.md"
  "control-plane/registry/WORKSPACE_REGISTRY.yaml"
  "runtime/README.md"
  "governance/README.md"
  "governance/SECURITY_BOUNDARIES.md"
  "execution/README.md"
  "extensions/README.md"
  "domains/README.md"
  "state-private/README.md"
  "ops/README.md"
  "labs/README.md"
  "memory/README.md"
  "archive/README.md"
)

deferred_warning_paths=(
  "AGENTS.md"
  "README.md"
  "README.AGENTS_OS.md"
)

missing_required=0
deferred_missing=0

for path in "${required_paths[@]}"; do
  if [[ -e "$path" ]]; then
    printf 'required_path_present: %s\n' "$path"
  else
    printf 'missing_required_path: %s\n' "$path"
    missing_required=1
  fi
done

for path in "${deferred_warning_paths[@]}"; do
  if [[ -e "$path" ]]; then
    printf 'deferred_path_present: %s\n' "$path"
  else
    printf 'deferred_path_warning_absent: %s\n' "$path"
    deferred_missing=1
  fi
done

if [[ "$missing_required" -eq 1 ]]; then
  printf '[validate-workspace] required path check failed\n'
  exit 1
fi

if [[ "$deferred_missing" -eq 1 ]]; then
  printf '[validate-workspace] required paths present; deferred warnings reported\n'
else
  printf '[validate-workspace] required paths present; no deferred warnings\n'
fi
