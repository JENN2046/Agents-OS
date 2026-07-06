#!/usr/bin/env bash
set -euo pipefail

echo "[validate-no-secrets] path-only scan started"

# Migrated as a validation candidate, not execution authorization.
# This scanner prints suspicious paths only; it must not print file contents or
# secret values. Path names can still be sensitive, so do not copy full output
# into receipts or public reports without separate approval.

patterns=(
  ".env"
  ".env."
  "config.env"
  "id_rsa"
  "id_ed25519"
  "credentials.json"
  "token.json"
  ".pem"
  ".key"
  ".p12"
  ".pfx"
)

found=0
for pattern in "${patterns[@]}"; do
  while IFS= read -r path; do
    case "$path" in
      *".example"|*".template"|*"README.AGENTS_OS.md") continue ;;
    esac
    echo "suspicious_path: $path"
    found=1
  done < <(find . -type f -name "*${pattern}*" 2>/dev/null || true)
done

if [[ "$found" -eq 1 ]]; then
  echo "[validate-no-secrets] suspicious paths found. Review paths without printing file contents."
  exit 1
fi

echo "[validate-no-secrets] no suspicious paths found"
