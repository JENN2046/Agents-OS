#!/usr/bin/env bash
set -euo pipefail

echo "[validate-extension-manifests] started"

# Migrated as a validation candidate, not execution authorization.
# Scope intentionally remains workspace-relative ./extensions. Do not narrow
# this to a currently observed extension directory until extension-assets
# placement is separately decided.

missing=0

# This README kit contains placeholder container directories such as:
# plugin-packs/, agent-packs/, admin-extensions/, bridge-plugins/.
# These are not concrete extensions and do not need manifests.
#
# A concrete extension is considered manifest-required when it contains
# implementation/config files beyond AGENTS OS doorplates and templates.
while IFS= read -r dir; do
  base="$(basename "$dir")"

  case "$base" in
    plugin-packs|agent-packs|admin-extensions|bridge-plugins|templates|docs|examples)
      continue
      ;;
  esac

  if [[ -f "$dir/jenn-extension.manifest.json" ]]; then
    continue
  fi

  # Skip pure placeholder directories that only contain README.AGENTS_OS.md.
  non_doorplate_count="$(
    find "$dir" -maxdepth 1 -type f \
      ! -name 'README.AGENTS_OS.md' \
      ! -name '.gitkeep' \
      | wc -l | tr -d ' '
  )"

  child_count="$(
    find "$dir" -mindepth 1 -maxdepth 1 -type d | wc -l | tr -d ' '
  )"

  if [[ "$non_doorplate_count" -eq 0 && "$child_count" -eq 0 ]]; then
    continue
  fi

  echo "extension_missing_manifest: $dir"
  missing=1
done < <(find ./extensions -mindepth 2 -maxdepth 5 -type d \( -name "*extension*" -o -name "*pack*" -o -name "*Bridge*" -o -name "*bridge*" \) 2>/dev/null || true)

if [[ "$missing" -eq 1 ]]; then
  echo "[validate-extension-manifests] some concrete extension-like directories have no manifest"
  exit 1
fi

echo "[validate-extension-manifests] complete"
