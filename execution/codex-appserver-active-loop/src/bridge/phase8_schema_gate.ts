export type Phase8SchemaGateStatus = "BLOCKED" | "UNLOCK_CANDIDATE";

export interface Phase8SchemaGateFile {
  readonly path: string;
  readonly kind: "generated_type" | "json_schema";
  readonly text: string;
}

export interface Phase8SchemaFieldFinding {
  readonly file: string;
  readonly kind: Phase8SchemaGateFile["kind"];
  readonly field: string;
  readonly location: string;
  readonly classification: "unlock_candidate" | "non_unlock";
  readonly reason: string;
}

export interface Phase8SchemaGateResult {
  readonly status: Phase8SchemaGateStatus;
  readonly phase8Decision: "BLOCK" | "REVIEW_REQUIRED";
  readonly readableRootSupported: boolean;
  readonly unlockCandidates: readonly Phase8SchemaFieldFinding[];
  readonly nonUnlockFindings: readonly Phase8SchemaFieldFinding[];
  readonly scannedFiles: readonly string[];
  readonly reason: string;
}

export const readableRootUnlockFieldNames = [
  "readableRoots",
  "readableRoot",
  "readRoots",
  "readRoot",
  "restrictedReadableRoots",
  "restrictedReadableRoot",
  "restrictedReadRoots",
  "restrictedReadRoot",
  "allowedReadableRoots",
  "allowedReadableRoot",
  "allowedReadRoots",
  "allowedReadRoot",
  "permittedReadableRoots",
  "permittedReadableRoot",
  "permittedReadRoots",
  "permittedReadRoot",
] as const;

export const nonUnlockFieldNames = [
  "cwd",
  "readOnly",
  "networkAccess",
  "sandbox",
  "sandboxPolicy",
  "writableRoots",
  "permissionProfile",
] as const;

const unlockFieldSet = new Set(readableRootUnlockFieldNames.map((field) => field.toLowerCase()));
const nonUnlockFieldSet = new Set(nonUnlockFieldNames.map((field) => field.toLowerCase()));

export function evaluatePhase8SchemaGate(files: readonly Phase8SchemaGateFile[]): Phase8SchemaGateResult {
  const findings = files.flatMap((file) => inspectFile(file));
  const unlockCandidates = uniqueFindings(findings.filter((finding) => finding.classification === "unlock_candidate"));
  const nonUnlockFindings = uniqueFindings(findings.filter((finding) => finding.classification === "non_unlock"));
  const readableRootSupported = unlockCandidates.length > 0;

  return {
    status: readableRootSupported ? "UNLOCK_CANDIDATE" : "BLOCKED",
    phase8Decision: readableRootSupported ? "REVIEW_REQUIRED" : "BLOCK",
    readableRootSupported,
    unlockCandidates,
    nonUnlockFindings,
    scannedFiles: files.map((file) => file.path),
    reason: readableRootSupported
      ? "Generated App Server schema exposes a readable-root-like field; Phase 8 still requires human review before any real repository pilot."
      : "Generated App Server schema does not expose readableRoots or an equivalent restricted readable-root field; Phase 8 remains blocked.",
  };
}

function inspectFile(file: Phase8SchemaGateFile): readonly Phase8SchemaFieldFinding[] {
  if (file.kind === "json_schema") {
    return inspectJsonSchemaFile(file);
  }
  return inspectGeneratedTypeFile(file);
}

function inspectGeneratedTypeFile(file: Phase8SchemaGateFile): readonly Phase8SchemaFieldFinding[] {
  const findings: Phase8SchemaFieldFinding[] = [];
  for (const field of extractTypePropertyNames(file.text)) {
    const finding = classifyField(file, field, "type-property");
    if (finding) findings.push(finding);
  }
  for (const value of extractTypeStringLiterals(file.text)) {
    const finding = classifyNonUnlockValue(file, value, "type-literal");
    if (finding) findings.push(finding);
  }
  return findings;
}

function inspectJsonSchemaFile(file: Phase8SchemaGateFile): readonly Phase8SchemaFieldFinding[] {
  let parsed: unknown;
  try {
    parsed = JSON.parse(file.text) as unknown;
  } catch {
    return [];
  }
  const findings: Phase8SchemaFieldFinding[] = [];
  walkJson(parsed, "#", (key, location, value) => {
    const finding = classifyField(file, key, location);
    if (finding) findings.push(finding);
    const valueFinding = typeof value === "string" ? classifyNonUnlockValue(file, value, `${location}:value`) : undefined;
    if (valueFinding) findings.push(valueFinding);
  });
  return findings;
}

function classifyField(file: Phase8SchemaGateFile, field: string, location: string): Phase8SchemaFieldFinding | undefined {
  const normalized = field.toLowerCase();
  if (unlockFieldSet.has(normalized)) {
    return {
      file: file.path,
      kind: file.kind,
      field,
      location,
      classification: "unlock_candidate",
      reason: "field name is a readable-root-like session boundary",
    };
  }
  if (nonUnlockFieldSet.has(normalized)) {
    return {
      file: file.path,
      kind: file.kind,
      field,
      location,
      classification: "non_unlock",
      reason: "field is known but does not restrict readable roots",
    };
  }
  return undefined;
}

function classifyNonUnlockValue(file: Phase8SchemaGateFile, value: string, location: string): Phase8SchemaFieldFinding | undefined {
  if (!nonUnlockFieldSet.has(value.toLowerCase())) {
    return undefined;
  }
  return {
    file: file.path,
    kind: file.kind,
    field: value,
    location,
    classification: "non_unlock",
    reason: "string value is a known mode or field but does not restrict readable roots",
  };
}

function extractTypePropertyNames(text: string): readonly string[] {
  const fields: string[] = [];
  for (const match of text.matchAll(/"([A-Za-z_][A-Za-z0-9_]*)"\s*:/g)) {
    fields.push(match[1] ?? "");
  }
  for (const match of text.matchAll(/\b([A-Za-z_][A-Za-z0-9_]*)\??\s*:/g)) {
    fields.push(match[1] ?? "");
  }
  return fields.filter((field) => field.length > 0);
}

function extractTypeStringLiterals(text: string): readonly string[] {
  return [...text.matchAll(/"([A-Za-z_][A-Za-z0-9_]*)"/g)]
    .map((match) => match[1] ?? "")
    .filter((value) => value.length > 0);
}

function walkJson(value: unknown, location: string, onKey: (key: string, location: string, value: unknown) => void): void {
  if (Array.isArray(value)) {
    value.forEach((item, index) => walkJson(item, `${location}/${index}`, onKey));
    return;
  }
  if (!isRecord(value)) {
    return;
  }
  for (const [key, child] of Object.entries(value)) {
    const childLocation = `${location}/${escapeJsonPointer(key)}`;
    onKey(key, childLocation, child);
    walkJson(child, childLocation, onKey);
  }
}

function uniqueFindings(findings: readonly Phase8SchemaFieldFinding[]): readonly Phase8SchemaFieldFinding[] {
  const seen = new Set<string>();
  const unique: Phase8SchemaFieldFinding[] = [];
  for (const finding of findings) {
    const key = `${finding.file}\0${finding.field}\0${finding.location}\0${finding.classification}`;
    if (seen.has(key)) continue;
    seen.add(key);
    unique.push(finding);
  }
  return unique;
}

function escapeJsonPointer(value: string): string {
  return value.replaceAll("~", "~0").replaceAll("/", "~1");
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}
