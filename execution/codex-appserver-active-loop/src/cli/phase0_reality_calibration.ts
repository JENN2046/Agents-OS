import { spawn } from "node:child_process";
import { createHash } from "node:crypto";
import { mkdir, readdir, readFile, writeFile } from "node:fs/promises";
import path from "node:path";

type CommandResult = {
  readonly ok: boolean;
  readonly command: string;
  readonly exitCode: number | null;
  readonly stdout: string;
  readonly stderrPreview: string;
};

type HandshakeResult = {
  readonly ok: boolean;
  readonly initializedSent: boolean;
  readonly experimentalApiUsed: false;
  readonly response?: {
    readonly userAgent?: string;
    readonly codexHomeReturned: boolean;
    readonly codexHomeRedacted: true;
    readonly platformFamily?: string;
    readonly platformOs?: string;
  };
  readonly error?: string;
  readonly stderrPreview: string;
};

const root = process.cwd();
const tsSchemaDir = path.join(root, "src", "generated", "appserver");
const jsonSchemaDir = path.join(root, "schemas", "appserver");
const reportPath = path.join(root, "data", "reports", "phase0_reality_calibration.json");

function runCodexCommand(command: string, timeoutMs = 60_000): Promise<CommandResult> {
  return new Promise((resolve) => {
    const child = spawn("cmd.exe", ["/d", "/s", "/c", command], {
      cwd: root,
      stdio: ["ignore", "pipe", "pipe"],
      windowsHide: true,
    });

    let stdout = "";
    let stderr = "";
    let settled = false;
    const timer = setTimeout(() => {
      if (settled) {
        return;
      }
      settled = true;
      child.kill();
      resolve({
        ok: false,
        command,
        exitCode: null,
        stdout,
        stderrPreview: sanitize(stderr).slice(0, 1000),
      });
    }, timeoutMs);

    child.stdout.setEncoding("utf8");
    child.stderr.setEncoding("utf8");
    child.stdout.on("data", (chunk) => {
      stdout += chunk;
    });
    child.stderr.on("data", (chunk) => {
      stderr += chunk;
    });
    child.on("error", (error) => {
      if (settled) {
        return;
      }
      settled = true;
      clearTimeout(timer);
      resolve({
        ok: false,
        command,
        exitCode: null,
        stdout,
        stderrPreview: sanitize(error.message).slice(0, 1000),
      });
    });
    child.on("exit", (code) => {
      if (settled) {
        return;
      }
      settled = true;
      clearTimeout(timer);
      resolve({
        ok: code === 0,
        command,
        exitCode: code,
        stdout,
        stderrPreview: sanitize(stderr).slice(0, 1000),
      });
    });
  });
}

function runHandshake(timeoutMs = 15_000): Promise<HandshakeResult> {
  return new Promise((resolve) => {
    const child = spawn("cmd.exe", ["/d", "/s", "/c", "codex app-server --stdio"], {
      cwd: root,
      stdio: ["pipe", "pipe", "pipe"],
      windowsHide: true,
    });

    const initialize = {
      id: 1,
      method: "initialize",
      params: {
        clientInfo: {
          name: "cea-phase0-calibration",
          title: "CEA Phase 0 Calibration",
          version: "0.0.0",
        },
        capabilities: {
          experimentalApi: false,
          requestAttestation: false,
          optOutNotificationMethods: [],
        },
      },
    };

    let stdout = "";
    let stderr = "";
    let settled = false;
    let initializedSent = false;
    let responseHandled = false;

    const finish = (result: HandshakeResult) => {
      if (settled) {
        return;
      }
      settled = true;
      clearTimeout(timer);
      try {
        child.stdin.end();
      } catch {
        // The app-server may already have closed stdin.
      }
      setTimeout(() => {
        try {
          child.kill();
        } catch {
          // The process may already be gone.
        }
      }, 50);
      resolve(result);
    };

    const timer = setTimeout(() => {
      finish({
        ok: false,
        initializedSent,
        experimentalApiUsed: false,
        error: "initialize timed out",
        stderrPreview: sanitize(stderr).slice(0, 1000),
      });
    }, timeoutMs);

    child.stdout.setEncoding("utf8");
    child.stderr.setEncoding("utf8");
    child.stderr.on("data", (chunk) => {
      stderr += chunk;
    });
    child.stdin.on("error", () => {
      // The server may close stdin during shutdown after the calibration result is known.
    });
    child.stdout.on("data", (chunk) => {
      if (settled || responseHandled) {
        return;
      }
      stdout += chunk;
      const line = stdout.split(/\r?\n/).find((candidate) => candidate.trim().length > 0);
      if (!line) {
        return;
      }
      responseHandled = true;

      try {
        const message = JSON.parse(line) as {
          id?: unknown;
          result?: {
            userAgent?: string;
            codexHome?: string;
            platformFamily?: string;
            platformOs?: string;
          };
          error?: { message?: string };
        };
        if (message.error) {
          finish({
            ok: false,
            initializedSent,
            experimentalApiUsed: false,
            error: sanitize(message.error.message ?? "initialize returned error"),
            stderrPreview: sanitize(stderr).slice(0, 1000),
          });
          return;
        }
        if (child.stdin.destroyed || child.stdin.writableEnded) {
          finish({
            ok: false,
            initializedSent,
            experimentalApiUsed: false,
            error: "app-server stdin closed before initialized notification",
            stderrPreview: sanitize(stderr).slice(0, 1000),
          });
          return;
        }
        child.stdin.write(`${JSON.stringify({ method: "initialized" })}\n`, (error) => {
          if (error) {
            finish({
              ok: false,
              initializedSent,
              experimentalApiUsed: false,
              error: sanitize(error.message),
              stderrPreview: sanitize(stderr).slice(0, 1000),
            });
            return;
          }
          initializedSent = true;
          finish({
            ok: true,
            initializedSent,
            experimentalApiUsed: false,
            response: {
              userAgent: message.result?.userAgent,
              codexHomeReturned: typeof message.result?.codexHome === "string",
              codexHomeRedacted: true,
              platformFamily: message.result?.platformFamily,
              platformOs: message.result?.platformOs,
            },
            stderrPreview: sanitize(stderr).slice(0, 1000),
          });
        });
      } catch (error) {
        finish({
          ok: false,
          initializedSent,
          experimentalApiUsed: false,
          error: sanitize(error instanceof Error ? error.message : "failed to parse initialize response"),
          stderrPreview: sanitize(stderr).slice(0, 1000),
        });
      }
    });
    child.on("error", (error) => {
      finish({
        ok: false,
        initializedSent,
        experimentalApiUsed: false,
        error: sanitize(error.message),
        stderrPreview: sanitize(stderr).slice(0, 1000),
      });
    });
    child.on("exit", (code) => {
      if (!settled) {
        finish({
          ok: false,
          initializedSent,
          experimentalApiUsed: false,
          error: `app-server exited before initialize response: ${code}`,
          stderrPreview: sanitize(stderr).slice(0, 1000),
        });
      }
    });

    child.stdin.write(`${JSON.stringify(initialize)}\n`);
  });
}

async function collectDirEvidence(dir: string) {
  const files = await listFiles(dir);
  const hashes = await Promise.all(
    files.map(async (file) => {
      const content = await readFile(file);
      return {
        path: path.relative(root, file).replaceAll("\\", "/"),
        sha256: createHash("sha256").update(content).digest("hex"),
        bytes: content.byteLength,
      };
    }),
  );
  return {
    fileCount: hashes.length,
    files: hashes.sort((a, b) => a.path.localeCompare(b.path)),
  };
}

async function listFiles(dir: string): Promise<string[]> {
  const entries = await readdir(dir, { withFileTypes: true });
  const results = await Promise.all(
    entries
      .filter((entry) => entry.name !== ".gitkeep")
      .map(async (entry) => {
        const fullPath = path.join(dir, entry.name);
        return entry.isDirectory() ? listFiles(fullPath) : [fullPath];
      }),
  );
  return results.flat();
}

function sanitize(text: string): string {
  return text
    .replace(/[A-Za-z]:\\Users\\[^\\\r\n]+\\\.codex/g, "<REDACTED_CODEX_HOME>")
    .replace(/Bearer\s+[A-Za-z0-9._~+/=-]+/gi, "Bearer <REDACTED>")
    .replace(/sk-[A-Za-z0-9._-]+/g, "sk-<REDACTED>");
}

async function main() {
  await mkdir(path.dirname(reportPath), { recursive: true });

  const codexVersion = await runCodexCommand("codex --version", 30_000);
  const generateTs = await runCodexCommand("codex app-server generate-ts --out .\\src\\generated\\appserver", 120_000);
  const generateJsonSchema = await runCodexCommand(
    "codex app-server generate-json-schema --out .\\schemas\\appserver",
    120_000,
  );
  const handshake = await runHandshake();
  const tsEvidence = await collectDirEvidence(tsSchemaDir);
  const jsonEvidence = await collectDirEvidence(jsonSchemaDir);

  const report = {
    task_id: "CEA-002",
    title: "Phase 0 Reality Calibration",
    result:
      codexVersion.ok &&
      generateTs.ok &&
      generateJsonSchema.ok &&
      handshake.ok &&
      handshake.initializedSent
        ? "PASS"
        : "BLOCK",
    generated_at: new Date().toISOString(),
    project_path: root,
    commands: {
      codex_version: {
        ok: codexVersion.ok,
        output: codexVersion.stdout.trim(),
        stderr_preview: codexVersion.stderrPreview,
      },
      generate_ts: {
        ok: generateTs.ok,
        exit_code: generateTs.exitCode,
        out_dir: "src/generated/appserver",
        stderr_preview: generateTs.stderrPreview,
      },
      generate_json_schema: {
        ok: generateJsonSchema.ok,
        exit_code: generateJsonSchema.exitCode,
        out_dir: "schemas/appserver",
        stderr_preview: generateJsonSchema.stderrPreview,
      },
    },
    schema_evidence: {
      typescript: tsEvidence,
      json_schema: jsonEvidence,
    },
    app_server_stdio: {
      started: handshake.ok,
      initialize_succeeded: handshake.ok,
      initialized_sent: handshake.initializedSent,
      experimental_api_used: false,
      response: handshake.response,
      error: handshake.error,
      stderr_preview: handshake.stderrPreview,
    },
    boundaries: {
      workspace_agents_api: "NOT_USED",
      responses_api: "NOT_USED",
      browser_automation: "NOT_USED",
      websocket: "NOT_USED",
      non_loopback_websocket: "NOT_USED",
      experimental_api: "NOT_USED",
      thread_shell_command: "NOT_USED",
      command_exec: "NOT_USED",
      process_api: "NOT_USED",
      full_access: "NOT_USED",
      danger_full_access: "NOT_USED",
      real_repo_smoke: "NOT_USED",
      secrets_read: "NOT_USED",
      codex_home_value: "REDACTED",
    },
  };

  await writeFile(reportPath, `${JSON.stringify(report, null, 2)}\n`, "utf8");
  console.log(JSON.stringify({ result: report.result, report: path.relative(root, reportPath) }, null, 2));
  if (report.result !== "PASS") {
    process.exitCode = 1;
  }
}

await main();
