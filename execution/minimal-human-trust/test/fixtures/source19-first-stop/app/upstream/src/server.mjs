import express from "express";
import { memorySearchWithProjection } from './retrieval-projection.mjs';
import { describeColdBinding } from './cold-runtime-authority.mjs';
import path from "node:path";
import { pathToFileURL } from "node:url";
import { resolveRuntimeHotAuthority, verifyRuntimeBinding, describeHotMemoryBinding } from "./upstream-runtime-authority.mjs";
import { z } from "zod";
import { ResolverMcpServer, RESOLVER_INPUT_SCHEMA, RESOLVER_OUTPUT_SCHEMA, resolveVcpTool, resolverToolResult } from './vcp-tool-resolver.mjs';
import { ListToolsRequestSchema } from "@modelcontextprotocol/sdk/types.js";
import { normalizeObjectSchema } from "@modelcontextprotocol/sdk/server/zod-compat.js";
import { toJsonSchemaCompat } from "@modelcontextprotocol/sdk/server/zod-json-schema-compat.js";
import { StreamableHTTPServerTransport } from "@modelcontextprotocol/sdk/server/streamableHttp.js";
import { config } from "./config.mjs";
import { OUTPUT_SCHEMAS, makeStructuredResult, makeToolError } from "./output-contracts.mjs";
import { CODE_SESSION_ACTIONS, CodeSessionError, executeCodeSessionAction } from "./code-session.mjs";
import { DEVSPACE_ACTIONS, DevspaceClient, executeDevspaceAction } from "./devspace-client.mjs";
import { VcpClient, VcpHttpError, describeNativeToolOutcome } from "./vcp-client.mjs";
import { CROWN_INPUT_SCHEMA, PROJECT_FORGE_CROWN_TOOL_NAME, executeCrownFacade, validateCrownRequest, CROWN_ACTIONS } from "./project-forge-crown.mjs";
import { LIMITS as CROWN_TRANSPORT_LIMITS, canonical, digest, freeze, requireThat } from "./project-forge-crown-transport.mjs";
import { createCrownHostRuntime, createCrownTaskHost, CROWN_READINESS_PATH, verifyCrownAppEvidence, verifyCrownRouteEvidence } from "./project-forge-crown-admission.mjs";
import {
  KNOWLEDGE_UPSERT_LIMITS,
  KnowledgeAuthorityError,
  discoverKnowledgeLibraries,
  resolveKnowledgeAuthority,
  upsertKnowledgeSource,
} from "./knowledge-authority.mjs";
import {
  MEMORY_READ_LIMITS,
  MEMORY_UPDATE_LIMITS,
  MemoryAuthorityError,
  assertMemoryOwnerAssertion,
  assertUtf8Limit,
  preflightMemoryCreate,
  preflightMemoryRead,
  preflightMemoryUpdate,
  prepareMemoryUpdateProof,
  verifyMemoryUpdatePersistence,
  snapshotMemoryCreateInventory,
  verifyMemoryCreatePersistence,
  verifyMemoryPreflight,
} from "./memory-authority.mjs";

const VCP_APP_VERSION = "0.3.15";
const VCP_APP_SCHEMA_REVISION = "vcp-app-mcp-schema-2026-10-03-r16";
// The endpoint is mounted only by the private production assembly below.
const CROWN_READINESS_READER = Symbol('controlled Crown readiness reader');

// DailyNote processTags exposes no structured code for this terminal failure.
// Keep compatibility tied to its exact message, not arbitrary tag-related errors.
const DAILYNOTE_MISSING_TAG_ERROR = "Tag is missing. Please provide a 'Tag' argument or add a 'Tag:' line at the end of the 'Content'.";

const vcp = new VcpClient({
  baseUrl: config.vcpBaseUrl,
  apiKey: config.vcpApiKey,
  timeoutMs: config.vcpTimeoutMs,
  chatPath: config.vcpChatPath,
  defaultModel: config.vcpDefaultModel,
  systemPrompt: config.vcpSystemPrompt,
});

function modelList(data) {
  return Array.isArray(data?.data)
    ? data.data.map((item) => item?.id).filter(Boolean)
    : [];
}

const devspaceClientCache = new Map();

function resolveDevspaceClient(appConfig, runtimeDependencies = {}) {
  if (runtimeDependencies.devspaceClient) return runtimeDependencies.devspaceClient;
  if (!appConfig.devspaceBaseUrl || !appConfig.devspaceTokenStateFile) return null;

  const key = JSON.stringify([
    appConfig.devspaceBaseUrl,
    appConfig.devspaceTokenStateFile,
    appConfig.devspaceTimeoutMs,
  ]);
  if (!devspaceClientCache.has(key)) {
    devspaceClientCache.set(
      key,
      new DevspaceClient({
        baseUrl: appConfig.devspaceBaseUrl,
        tokenStateFile: appConfig.devspaceTokenStateFile,
        timeoutMs: appConfig.devspaceTimeoutMs,
        fetchImpl: runtimeDependencies.fetchImpl ?? globalThis.fetch,
      })
    );
  }
  return devspaceClientCache.get(key);
}

function resolveNativeDailyNoteTarget(targetFile, dailyNoteRoot) {
  const raw = String(targetFile || "").trim();
  if (!raw) return null;

  if (path.isAbsolute(raw)) {
    return path.resolve(raw);
  }

  const normalized = raw.replaceAll("\\", "/");
  const root = path.resolve(dailyNoteRoot);
  const rootBase = path.basename(root);

  let relative = normalized;
  if (relative.startsWith(`${rootBase}/`)) {
    relative = relative.slice(rootBase.length + 1);
  }

  return path.resolve(root, relative);
}

function isSafeNativeFileName(fileName) {
  if (typeof fileName !== "string" || !fileName) return false;
  if (fileName === "." || fileName === "..") return false;
  if (path.isAbsolute(fileName) || path.win32.isAbsolute(fileName)) return false;
  if (path.basename(fileName) !== fileName) return false;
  if (path.win32.basename(fileName) !== fileName) return false;
  return !fileName.includes("/") && !fileName.includes("\\");
}

function resultText(value) {
  if (typeof value === "string") return value;
  return JSON.stringify(value, null, 2);
}

function errorResult(error, { structured = true } = {}) {
  const detail =
    error instanceof VcpHttpError
      ? {
          type: error.name,
          message: error.message,
          status: error.status ?? null,
          path: error.path ?? null,
          body: error.body ?? null,
        }
      : error instanceof MemoryAuthorityError
        ? {
            type: error.name,
            code: error.code,
            message: error.message,
          }
      : error instanceof KnowledgeAuthorityError
        ? {
            type: error.name,
            code: error.code,
            message: error.message,
          }
      : error instanceof CodeSessionError
        ? {
            type: error.name,
            code: error.code,
            message: error.message,
            detail: error.detail || {},
          }
      : {
          type: error?.name || "Error",
          message: error?.message || String(error),
        };

  const text = `VCP call failed: ${(error instanceof KnowledgeAuthorityError || error instanceof MemoryAuthorityError || error instanceof CodeSessionError) ? `${detail.code}: ` : ""}${detail.message}`;
  return makeToolError(text, structured ? { ok: false, error: detail } : undefined);
}

function guarded(handler, { structuredErrors = true, sanitizeMcpErrors = false } = {}) {
  return async (args) => {
    try {
      return await handler(args);
    } catch (error) {
      if (sanitizeMcpErrors) return makeToolError("VCP call failed: UPSTREAM_UNAVAILABLE", structuredErrors ? {ok:false,error:{type:"Error",message:"UPSTREAM_UNAVAILABLE"}} : undefined);
      console.error("[tool]", error);
      return errorResult(error, { structured: structuredErrors });
    }
  };
}

export function createMcpServer({ appConfig = config, vcpClient = vcp, runtimeDependencies = {}, sanitizeMcpErrors = false } = {}) {
  const guardedTool = (handler, options={}) => guarded(handler, {...options,sanitizeMcpErrors});
  const config = appConfig;
  const vcp = vcpClient;
  const devspace = resolveDevspaceClient(config, runtimeDependencies);
  const server = new ResolverMcpServer(
    {
      name: "vcp-app",
      version: VCP_APP_VERSION,
    },
    {
      instructions:
        "VCP-APP direct integration. Use vcp_memory_search for semantic memory retrieval. Successful search structuredContent includes an additive projection of retrieval evidence; interpret rank, scope and provenance as evidence from that retrieval only, not as canonical/current truth or a normalized cross-engine score. Use vcp_memory_read for an exact stable readback of one server-authorized Hot DailyNote document. Use vcp_memory_create only when the user explicitly wants a new persistent Hot memory written. Use vcp_memory_update only when the user explicitly wants an existing persistent Hot memory updated. Use vcp_knowledge_libraries when the caller or planner needs to discover current Cold source libraries or server-authorized write targets. It is read-only and does not prove TDB indexing readiness. It is not a mandatory preflight when the exact authorized library is already known. Use vcp_knowledge_upsert only when the user explicitly wants a source-grounded Cold knowledge document created or replaced in a server-authorized library; it writes the source document and relies on the existing TDBKnowledge watcher/indexing lifecycle rather than editing .tdb files directly. Use vcp_devspace for project-bound coding work delegated to the configured DevSpace execution backend. Reuse the returned workspace_id across read/patch/command/process/review calls; command defaults to yield_time_ms=0 so tracked process state is returned before long work continues. VCP-APP retries only an explicit DevSpace 401 after refreshing OAuth and never replays network timeouts or unknown outcomes. Use vcp_code_session only for the legacy native VCP coding facade; it never widens native tool authority, never retries a rejected action through a broader route, and its v1 Git route is read-only. Use vcp_call_tool for other known VCP native tools within the user-authorized scope. Use vcp_chat only when the user intends the full VCP pipeline, including possible tool actions. Neither broader entry inherits the dedicated Hot/Cold authority preflight; authorization of one action does not authorize unrelated actions.",
    }
  );

  // Keep APP-owned registration references. The SDK's public tools/list handler
  // normalizes object schemas only, which loses Crown's strict root union.
  const registeredTools = new Map();
  const registerTool = (name, metadata, callback) => {
    const tool = server.registerTool(name, metadata, callback);
    registeredTools.set(name, tool);
    return tool;
  };

  registerTool(
    "vcp_status",
    {
      title: "Check VCP connectivity",
      description:
        "Use this to verify that VCP-APP can authenticate to the VCPToolBox main server, retrieve its model list, and report the live app/schema revision for stale-session diagnosis.",
      inputSchema: {},
      outputSchema: OUTPUT_SCHEMAS.vcp_status,
      annotations: {
        readOnlyHint: true,
        destructiveHint: false,
        openWorldHint: false,
        idempotentHint: true,
      },
    },
    guardedTool(async () => {
      const data = await vcp.listModels();
      const models = modelList(data);
      return makeStructuredResult(
        `VCP is reachable and authenticated. ${models.length} model(s) reported.`,
        {
          ok: true,
          reachable: true,
          app_version: VCP_APP_VERSION,
          schema_revision: VCP_APP_SCHEMA_REVISION,
          models,
          hot_memory_binding: await describeHotMemoryBinding(config, vcp, runtimeDependencies),
          cold_memory_binding: await describeColdBinding(config, runtimeDependencies),
        }
      );
    })
  );

  registerTool(
    "vcp_memory_read",
    {
      title: "Read one exact VCP memory document",
      description:
        "Use this for authoritative exact readback of one existing server-authorized Hot DailyNote document after its exact folder and file name are known. This is read-only and does not perform semantic retrieval or Cold TDB routing.",
      inputSchema: {
        folder: z.string().min(1).max(100),
        file_name: z.string().min(1).max(MEMORY_READ_LIMITS.fileNameMaxChars),
        maid: z.string().min(1).optional(),
      },
      outputSchema: OUTPUT_SCHEMAS.vcp_memory_read,
      annotations: {
        readOnlyHint: true,
        destructiveHint: false,
        openWorldHint: false,
        idempotentHint: true,
      },
    },
    guardedTool(async ({ folder, file_name, maid }) => {
      const binding = await resolveRuntimeHotAuthority(config, vcp, runtimeDependencies);
      const authority = binding.authority;
      assertMemoryOwnerAssertion(maid, authority.maid);
      const snapshot = await preflightMemoryRead({
        root: authority.root,
        ownedFolders: authority.ownedFolders,
        folder,
        fileName: file_name,
      });
      await verifyRuntimeBinding(binding, config, runtimeDependencies);

      return makeStructuredResult(snapshot.content, {
        ok: true,
        memory_owner: authority.maid,
        folder: snapshot.folder,
        file_name: snapshot.name,
        body: snapshot.content,
        content_sha256: snapshot.sha256,
        size_bytes: snapshot.size,
        mtime_ms: snapshot.mtimeMs,
        read_status: "exact_stable",
      });
    }, { structuredErrors: false })
  );

  registerTool(
    "vcp_memory_update",
    {
      title: "Update an existing VCP-APP memory",
      description:
        "Use only when the user explicitly wants an existing server-authorized VCP-APP DailyNote memory persistently updated. The target must identify exactly one literal occurrence in one server-authorized memory document; zero or ambiguous matches fail without mutation.",
      inputSchema: {
        folder: z.string().min(1).max(100),
        target: z
          .string()
          .min(MEMORY_UPDATE_LIMITS.targetMinChars)
          .max(MEMORY_UPDATE_LIMITS.targetMaxChars),
        replace: z
          .string()
          .min(MEMORY_UPDATE_LIMITS.replaceMinChars)
          .max(MEMORY_UPDATE_LIMITS.replaceMaxChars),
      },
      outputSchema: OUTPUT_SCHEMAS.vcp_memory_update,
      annotations: {
        readOnlyHint: false,
        destructiveHint: true,
        openWorldHint: false,
        idempotentHint: false,
      },
    },
    guardedTool(async ({ folder, target, replace }) => {
      assertUtf8Limit(target, MEMORY_UPDATE_LIMITS.targetMaxBytes, "target");
      assertUtf8Limit(replace, MEMORY_UPDATE_LIMITS.replaceMaxBytes, "replace");

      const binding = await resolveRuntimeHotAuthority(config, vcp, runtimeDependencies);
      const authority = binding.authority;
      const preflight = await preflightMemoryUpdate({
        root: authority.root,
        ownedFolders: authority.ownedFolders,
        folder,
        target,
      });
      const expected = await prepareMemoryUpdateProof(authority, preflight, target, replace);
      await verifyMemoryPreflight(preflight);
      await verifyRuntimeBinding(binding, config, runtimeDependencies);

      const data = await vcp.memoryUpdate({
        maid: authority.maid,
        folder,
        target,
        replace,
      });

      if (data?.status === "error" || data?.ok === false || data?.error) {
        throw new MemoryAuthorityError(
          "MEMORY_NATIVE_UPDATE_FAILED",
          "Native DailyNote update reported failure."
        );
      }

      const nativeResult =
        data?.status === "success" &&
        data?.result &&
        typeof data.result === "object" &&
        !Array.isArray(data.result)
          ? data.result
          : data;

      if (
        !nativeResult ||
        typeof nativeResult !== "object" ||
        Array.isArray(nativeResult)
      ) {
        throw new MemoryAuthorityError(
          "MEMORY_NATIVE_UPDATE_RESULT_UNVERIFIED",
          "Native DailyNote update returned a result whose mutation target cannot be verified."
        );
      }

      const nativeFolder = String(nativeResult.folder || "");
      const nativeFileName = String(nativeResult.fileName || "");
      const nativeTarget = resolveNativeDailyNoteTarget(
        nativeResult.targetFile,
        authority.root
      );

      if (!nativeFolder || !nativeFileName || !nativeTarget) {
        throw new MemoryAuthorityError(
          "MEMORY_NATIVE_UPDATE_RESULT_UNVERIFIED",
          "Native DailyNote update returned a result whose mutation target cannot be verified."
        );
      }

      const expectedTarget = path.resolve(preflight.filePath);
      if (
        nativeFolder !== preflight.folder ||
        nativeFileName !== preflight.fileName ||
        nativeTarget !== expectedTarget
      ) {
        throw new MemoryAuthorityError(
          "MEMORY_NATIVE_TARGET_MISMATCH",
          "Native DailyNote did not confirm the preflight-selected document."
        );
      }

      await verifyRuntimeBinding(binding, config, runtimeDependencies);
      const persisted = await verifyMemoryUpdatePersistence(authority, preflight, expected);
      const message =
        typeof nativeResult.message === "string" && nativeResult.message
          ? nativeResult.message
          : `Updated ${preflight.folder}/${preflight.fileName}.`;
      return makeStructuredResult(message, {
        ok: true,
        tool: "DailyNote",
        command: "update",
        memory_owner: authority.maid,
        folder: preflight.folder,
        file_name: preflight.fileName,
        index_status: nativeResult.indexStatus || "queued",
        persistence_status: "exact_readback_confirmed",
        content_sha256: persisted.sha256,
        size_bytes: persisted.size,
      });
    }, { structuredErrors: false })
  );

  registerTool(
    "vcp_memory_search",
    {
      title: "Search VCP memory",
      description:
        "Read-only LightMemo retrieval. For Hot memory provide query plus folder or maid. For Cold TDB use knowledge_base or one [知识库:Library] query selector; [知识库] selects all Cold libraries. Do not mix Hot and Cold scope. search_all_knowledge_bases is a legacy Hot-only flag, not a Cold selector. Advanced options are optional; defaults are k=5, rivermemo, rerank=false, bm25=true, aimemo off.",
      inputSchema: {
        query: z.string().trim().min(1).describe("Search text; whitespace or a Cold selector alone is invalid."),
        folder: z.string().trim().min(1).optional().describe("Hot folder selector; native multi-folder matching, not exact file authority. Never a Cold library."),
        knowledge_base: z.string().trim().min(1).optional().describe("One or more Cold library names, separated by commas. Omit Hot scope and advanced Hot overrides."),
        maid: z.string().trim().min(1).optional().describe("Native Hot name/scoped-folder selector. With folder, native folder selection takes precedence over signature filtering."),
        k: z.number().int().min(1).max(25).default(5).describe("Maximum returned results, not a similarity threshold."),
        enginemode: z.enum(["rivermemo", "tagmemo", "knn"]).default("rivermemo").describe("Hot engine. Cold keeps its own hybrid engine; leave this default for Cold."),
        rerank: z.union([z.boolean(), z.number().min(0).max(1), z.string()]).default(false).describe("false/0 disable; true enables standard rerank; (0,1] or rrf/rrf0.7 enable RRF. Explicit rrf0 remains enabled. Unknown strings are rejected."),
        bm25: z.boolean().default(true).describe("Hot BM25 option; false is invalid for Cold, whose hybrid retrieval is independent."),
        search_all_knowledge_bases: z.boolean().default(false).describe("Legacy Hot-only global flag: true bypasses Hot folder/signature filtering; native still requires folder or maid. It never selects Cold libraries."),
        aimemo: z.union([z.boolean(), z.string()]).optional().describe("Hot-only optional AI summary or preset; disabled by default. Native summary can fall back to raw results. Not a persistent-memory write request."),
      },
      outputSchema: OUTPUT_SCHEMAS.vcp_memory_search,
      annotations: {
        readOnlyHint: true,
        destructiveHint: false,
        openWorldHint: false,
        idempotentHint: true,
      },
    },
    guardedTool(async ({
      query,
      folder,
      knowledge_base,
      maid,
      k,
      enginemode,
      rerank,
      bm25,
      search_all_knowledge_bases,
      aimemo,
    }) => {
      const { result, projection } = await memorySearchWithProjection(vcp, {
        query,
        folder,
        knowledgeBase: knowledge_base,
        maid,
        k,
        enginemode,
        rerank,
        bm25,
        searchAll: search_all_knowledge_bases,
        aimemo,
      }, config, runtimeDependencies);
      return makeStructuredResult(resultText(result), {
        ok: true,
        tool: "LightMemo",
        result,
        projection,
      });
    })
  );

  registerTool(
    "vcp_memory_create",
    {
      title: "Create a VCP memory",
      description:
        "Use this only when the user explicitly wants the current information persisted into a server-authorized VCP DailyNote memory namespace.",
      inputSchema: {
        date: z.string().regex(/^\d{4}-\d{2}-\d{2}$/),
        content: z.string().min(1),
        maid: z.string().min(1).optional(),
        folder: z.string().min(1).max(100),
        file_name: z.string().optional(),
        tag: z.string().optional(),
      },
      outputSchema: OUTPUT_SCHEMAS.vcp_memory_create,
      annotations: {
        readOnlyHint: false,
        destructiveHint: false,
        openWorldHint: false,
        idempotentHint: false,
      },
    },
    guardedTool(async ({ date, content, maid, folder, file_name, tag }) => {
      const binding = await resolveRuntimeHotAuthority(config, vcp, runtimeDependencies);
      const authority = binding.authority;
      assertMemoryOwnerAssertion(maid, authority.maid);
      const preflight = await preflightMemoryCreate({
        root: authority.root,
        ownedFolders: authority.ownedFolders,
        folder,
      });

      const inventory = await snapshotMemoryCreateInventory(preflight);
      await verifyRuntimeBinding(binding, config, runtimeDependencies);
      const data = await vcp.memoryCreate({
        date,
        content,
        maid: authority.maid,
        folder: preflight.folder,
        fileName: file_name,
        tag,
      });

      const nativeResult =
        data?.status === "success" &&
        data?.result &&
        typeof data.result === "object" &&
        !Array.isArray(data.result)
          ? data.result
          : data;

      // Only classify after Native has had the opportunity to generate tags.
      // Reuse the existing one-level result envelope; an outer error wins.
      const nativeError = data?.error || nativeResult?.error;
      if (typeof nativeError === "string" && nativeError.trim() === DAILYNOTE_MISSING_TAG_ERROR) {
        throw new MemoryAuthorityError(
          "MEMORY_TAG_REQUIRED",
          "DailyNote could not obtain tags for this memory. Provide `tag` or add a valid terminal `Tag:` line to `content`."
        );
      }

      if (data?.status === "error" || data?.ok === false || data?.error) {
        throw new MemoryAuthorityError(
          "MEMORY_NATIVE_CREATE_FAILED",
          "Native DailyNote create reported failure."
        );
      }

      if (
        !nativeResult ||
        typeof nativeResult !== "object" ||
        Array.isArray(nativeResult)
      ) {
        throw new MemoryAuthorityError(
          "MEMORY_NATIVE_CREATE_RESULT_UNVERIFIED",
          "Native DailyNote create returned a result whose mutation target cannot be verified."
        );
      }

      const nativeFolder = nativeResult.folder;
      const nativeFileName = nativeResult.fileName;
      if (
        typeof nativeFolder !== "string" ||
        !nativeFolder ||
        !isSafeNativeFileName(nativeFileName)
      ) {
        throw new MemoryAuthorityError(
          "MEMORY_NATIVE_CREATE_RESULT_UNVERIFIED",
          "Native DailyNote create returned a result whose mutation target cannot be verified."
        );
      }
      if (nativeFolder !== preflight.folder) {
        throw new MemoryAuthorityError(
          "MEMORY_NATIVE_TARGET_MISMATCH",
          "Native DailyNote create did not confirm the preflight-approved folder."
        );
      }

      await verifyRuntimeBinding(binding, config, runtimeDependencies);
      const persisted = await verifyMemoryCreatePersistence(authority, preflight, inventory, nativeFileName);
      const message =
        typeof nativeResult.message === "string" && nativeResult.message
          ? nativeResult.message
          : `Created ${preflight.folder}/${nativeFileName}.`;
      const indexStatus =
        typeof nativeResult.indexStatus === "string" && nativeResult.indexStatus.trim()
          ? nativeResult.indexStatus.trim()
          : "queued";
      const retrievalReadiness =
        indexStatus.toLowerCase() === "queued" ? "pending" : "unverified";
      return makeStructuredResult(message, {
        ok: true,
        tool: "DailyNote",
        command: "create",
        memory_owner: authority.maid,
        folder: preflight.folder,
        file_name: nativeFileName,
        persistence_status: "exact_readback_confirmed",
        content_sha256: persisted.sha256,
        size_bytes: persisted.size,
        index_status: indexStatus,
        retrieval_readiness: retrievalReadiness,
      });
    }, { structuredErrors: false })
  );

  registerTool(
    "vcp_knowledge_libraries",
    {
      title: "Discover Cold knowledge libraries and write targets",
      description:
        "Use this for source-side discovery of safe first-level source directories under the configured Cold root and VCP-APP server-authorized write targets. This is not an authoritative TDB index inventory and does not prove TDB indexing or retrieval readiness. It does not read or modify .tdb files and produces no filesystem mutation.",
      inputSchema: z.object({}).strict(),
      outputSchema: OUTPUT_SCHEMAS.vcp_knowledge_libraries,
      annotations: {
        readOnlyHint: true,
        destructiveHint: false,
        openWorldHint: false,
        idempotentHint: true,
      },
    },
    guardedTool(async () => {
      const discovered = await discoverKnowledgeLibraries(config);
      return makeStructuredResult("Cold source libraries and server-authorized write targets; TDB indexing readiness is not verified.", discovered);
    }, { structuredErrors: false })
  );

  registerTool(
    "vcp_knowledge_upsert",
    {
      title: "Upsert a Cold knowledge source document",
      description:
        "Use only when the user explicitly wants source-grounded Cold knowledge persisted. Creates or replaces one source document inside an explicitly selected server-authorized knowledge library. A missing library may be created only when that exact library is already in the server-configured writable allowlist. This writes knowledge/<library>/<file_name> only; it never writes .tdb files directly and relies on the existing TDBKnowledge watcher/indexing lifecycle.",
      inputSchema: {
        library: z.string().min(1).max(KNOWLEDGE_UPSERT_LIMITS.libraryMaxChars),
        file_name: z.string().min(1).max(KNOWLEDGE_UPSERT_LIMITS.fileNameMaxChars),
        content: z.string().min(1).max(KNOWLEDGE_UPSERT_LIMITS.contentMaxChars),
      },
      outputSchema: OUTPUT_SCHEMAS.vcp_knowledge_upsert,
      annotations: {
        readOnlyHint: false,
        destructiveHint: true,
        openWorldHint: false,
        idempotentHint: false,
      },
    },
    guardedTool(async ({ library, file_name, content }) => {
      const authority = resolveKnowledgeAuthority(config);
      const receipt = await upsertKnowledgeSource({
        root: authority.root,
        ownedLibraries: authority.ownedLibraries,
        library,
        fileName: file_name,
        content,
      });

      return makeStructuredResult(
        `${receipt.operation === "created" ? "Created" : "Replaced"} Cold knowledge source ${receipt.library}/${receipt.fileName}. TDB indexing is asynchronous.`,
        {
          ok: true,
          library: receipt.library,
          library_operation: receipt.libraryOperation,
          file_name: receipt.fileName,
          operation: receipt.operation,
          content_sha256: receipt.contentSha256,
          size_bytes: receipt.sizeBytes,
          persistence_status: "source_confirmed",
          index_status: "watcher_pending",
          retrieval_readiness: "pending",
        }
      );
    }, { structuredErrors: false })
  );

  registerTool('vcp_tool_resolve', {
    title: 'Resolve VCP tool',
    description: 'Read the current VCP catalog to resolve a capability intent, exact tool identifier, or returned tool_ref. Returns identity, catalog availability and bounded native descriptive contracts only. enabled, online and available describe dynamic_tool_catalog only; the separate ProjectForge Crown channel is not evaluated. Resolution does not execute tools, establish safety, infer parameter schemas, or authorize execution. Use vcp_project_forge separately for authorized ProjectForge actions; use vcp_call_tool separately for other authorized native actions. Neither catalog availability nor resolution establishes Crown execution capability.',
    inputSchema: RESOLVER_INPUT_SCHEMA,
    outputSchema: RESOLVER_OUTPUT_SCHEMA,
    annotations: { readOnlyHint: true, destructiveHint: false, openWorldHint: false, idempotentHint: true },
  }, async args => resolverToolResult(await resolveVcpTool(args, config, runtimeDependencies)));

  registerTool(
    PROJECT_FORGE_CROWN_TOOL_NAME,
    {
      title: "Use the governed ProjectForge Crown facade",
      description:
        "Strict ProjectForge Crown facade. Public callers choose only a frozen action and its action-specific fields. VCP-APP deterministically selects helper versus internal exact routing; callers cannot request raw/exact/helper transport modes. Schema-invalid requests fail before ProjectForge dispatch. Until the bounded Crown executor is configured, schema-valid requests fail closed with UPSTREAM_UNAVAILABLE. ProjectForge Crown uses a separate governed channel; dynamic_tool_catalog availability does not establish its current execution capability. Each request still requires current admission and a verified result.",
      inputSchema: CROWN_INPUT_SCHEMA,
      outputSchema: OUTPUT_SCHEMAS.vcp_project_forge,
      annotations: {
        readOnlyHint: false,
        destructiveHint: true,
        openWorldHint: true,
        idempotentHint: false,
      },
    },
    async (args) => {
      const executor = runtimeDependencies.projectForgeCrownExecutor;
      if (executor?.requiresTrustedContext !== true) return executeCrownFacade(args, executor);
      let observedContext;
      const response=await executeCrownFacade(args, async input => {
        let trustedContext;
        try {
          trustedContext = typeof runtimeDependencies.projectForgeCrownContext === "function"
            ? await runtimeDependencies.projectForgeCrownContext()
            : runtimeDependencies.projectForgeCrownContext;
        } catch { /* Missing host proof is denied by private admission. */ }
        observedContext=trustedContext;
        return executor({...input, trustedContext});
      });
      if(observedContext && typeof runtimeDependencies.observeProjectForgeCrownCompletion==='function') {
        try {runtimeDependencies.observeProjectForgeCrownCompletion({trustedContext:observedContext,request:args,response});}
        catch { /* Observation cannot change the original tool result. */ }
      }
      return response;
    }
  );

  registerTool(
    "vcp_devspace",
    {
      title: "Use the configured DevSpace coding backend",
      description:
        "Thin VCP-to-DevSpace adapter. open binds a project (worktree by default); read/patch map to DevSpace file tools; command maps to exec_command and defaults yield_time_ms=0 so a process session is returned as early as possible; process polls or writes to that tracked process; review maps to show_changes. Reuse workspace_id and session_id. Explicit HTTP 401 may be retried once after OAuth refresh; network timeout/unknown outcome is never replayed.",
      inputSchema: {
        action: z.enum(DEVSPACE_ACTIONS),
        path: z.string().min(1).optional(),
        mode: z.enum(["checkout", "worktree"]).optional(),
        base_ref: z.string().min(1).optional(),
        workspace_id: z.string().min(1).optional(),
        offset: z.number().int().positive().optional(),
        limit: z.number().int().positive().optional(),
        patch: z.string().min(1).optional(),
        cmd: z.string().min(1).optional(),
        tty: z.boolean().optional(),
        columns: z.number().int().min(1).max(1000).optional(),
        rows: z.number().int().min(1).max(1000).optional(),
        working_directory: z.string().optional(),
        yield_time_ms: z.number().int().min(0).max(12000).optional(),
        max_output_tokens: z.number().int().positive().max(100000).optional(),
        session_id: z.number().int().nonnegative().optional(),
        chars: z.string().optional(),
        timeout_ms: z.number().int().min(100).max(300000).optional(),
      },
      outputSchema: OUTPUT_SCHEMAS.vcp_devspace,
      annotations: {
        readOnlyHint: false,
        destructiveHint: true,
        openWorldHint: true,
        idempotentHint: false,
      },
    },
    guardedTool(async (args) => {
      if (!devspace) {
        throw new Error(
          "DEVSPACE_NOT_CONFIGURED: set DEVSPACE_BASE_URL and DEVSPACE_TOKEN_STATE_FILE before using vcp_devspace"
        );
      }
      const result = await executeDevspaceAction(devspace, args);
      return makeStructuredResult(
        `DevSpace ${result.action} completed via ${result.tool}.`,
        result
      );
    })
  );

  registerTool(
    "vcp_code_session",
    {
      title: "Run a project-bound VCP CodeSession",
      description:
        "Unified project-bound coding facade. action=open binds an absolute project_root into a short-lived process-local session; status/close manage that session. inspect/read/search/patch/write/command/git route only to admitted existing VCP native tools and preserve their own authority/failure checks. The facade does not emulate a shell cwd, does not bypass native permissions, does not retry rejected actions, and Git is read-only in v1.",
      inputSchema: {
        action: z.enum(CODE_SESSION_ACTIONS),
        session_id: z.string().uuid().optional(),
        project_root: z.string().min(1).optional(),
        repo: z.string().max(512).optional(),
        branch: z.string().max(255).optional(),
        git_profile: z.string().max(255).optional(),
        tool_name: z.string().min(1).optional(),
        arguments: z.record(z.any()).default({}),
        command_kind: z.enum(["none", "command", "test", "build"]).default("none"),
      },
      outputSchema: OUTPUT_SCHEMAS.vcp_code_session,
      annotations: {
        readOnlyHint: false,
        destructiveHint: true,
        openWorldHint: true,
        idempotentHint: false,
      },
    },
    guardedTool(async ({
      action,
      session_id,
      project_root,
      repo,
      branch,
      git_profile,
      tool_name,
      arguments: args,
      command_kind,
    }) => {
      const receipt = await executeCodeSessionAction({
        vcpClient: vcp,
        action,
        sessionId: session_id,
        projectRoot: project_root,
        repo,
        branch,
        gitProfile: git_profile,
        toolName: tool_name,
        arguments: args,
        commandKind: command_kind,
      });
      return makeStructuredResult(resultText(receipt), receipt);
    })
  );

  registerTool(
    "vcp_call_tool",
    {
      title: "Call any VCP native tool",
      description:
        "Use this when the exact VCP native plugin/tool name is known, no more specific MCP tool exists, and its concrete action is within the user-authorized scope. It forwards to /v1/human/tool and may write, execute or contact external systems. Native plugin checks still apply; dedicated memory owner/folder preflight does not apply. Do not use it to retry a rejected dedicated memory operation through a broader entry.",
      inputSchema: {
        tool_name: z.string().min(1),
        arguments: z.record(z.any()).default({}).describe("Native parameters only: names use ASCII letters, digits or underscore. Reserved routing/control names tool_name, archery, ink, river, vref and __proto__ are rejected, as are native framing markers and their fuzzy/ESCAPE variants."),
      },
      outputSchema: OUTPUT_SCHEMAS.vcp_call_tool,
      annotations: {
        readOnlyHint: false,
        destructiveHint: true,
        openWorldHint: true,
        idempotentHint: false,
      },
    },
    guardedTool(async ({ tool_name, arguments: args }) => {
      const data = await vcp.callTool(tool_name, args);
      const outcome = describeNativeToolOutcome(data);
      const result = outcome.result;
      if (!outcome.ok) {
        return makeToolError(outcome.message, {
          ok: false, tool: tool_name, result,
          error: { type: "NativeToolResultError", code: outcome.code, message: outcome.message },
        });
      }
      return makeStructuredResult(resultText(result), {
        ok: true,
        tool: tool_name,
        result,
      });
    })
  );

  registerTool(
    "vcp_chat",
    {
      title: "Run the full VCP pipeline",
      description:
        "Use this when the request should enter VCPToolBox /v1/chat/completions, including configured message preprocessors, RAG/TagMemo/RiverMemo/OneRing/Timeline/ContextFolding activation present in the configured VCP system prompt, and VCP's own tool loop. This may perform writes, execute tools, contact external systems or schedule work. Use only within the user-authorized action scope; a read-only prompt or caller-supplied system text does not enforce that scope. Dedicated memory owner/folder preflight does not apply.",
      inputSchema: {
        prompt: z.string().min(1),
        model: z.string().optional(),
        system: z.string().optional(),
        temperature: z.number().min(0).max(2).optional(),
      },
      outputSchema: OUTPUT_SCHEMAS.vcp_chat,
      annotations: {
        readOnlyHint: false,
        destructiveHint: true,
        openWorldHint: true,
        idempotentHint: false,
      },
    },
    guardedTool(async ({ prompt, model, system, temperature }) => {
      const data = await vcp.chat({ prompt, model, system, temperature });
      const content =
        data?.choices?.[0]?.message?.content ??
        data?.choices?.[0]?.text ??
        data;

      return makeStructuredResult(resultText(content), {
        ok: true,
        model: data?.model ?? model ?? config.vcpDefaultModel ?? "",
        response: content,
      });
    })
  );

  server.server.setRequestHandler(ListToolsRequestSchema, () => ({
    tools: [...registeredTools].filter(([, tool]) => tool.enabled).map(([name, tool]) => {
      const input = name === PROJECT_FORGE_CROWN_TOOL_NAME
        ? {type: 'object', ...toJsonSchemaCompat(CROWN_INPUT_SCHEMA, {strictUnions:true, pipeStrategy:'input'})}
        : (() => {const object = normalizeObjectSchema(tool.inputSchema);
          return object ? toJsonSchemaCompat(object, {strictUnions:true, pipeStrategy:'input'}) : {type:'object',properties:{}};})();
      const definition = {name,title:tool.title,description:tool.description,inputSchema:input,
        annotations:tool.annotations,execution:tool.execution,_meta:tool._meta};
      const output = tool.outputSchema && normalizeObjectSchema(tool.outputSchema);
      if (output) definition.outputSchema = toJsonSchemaCompat(output, {strictUnions:true,pipeStrategy:'output'});
      return definition;
    }),
  }));
  return server;
}

const globalConfig=config,globalVcp=vcp;
export function createHttpApp(options = {}) {
const config = options.appConfig ?? globalConfig;
const vcp = options.vcpClient ?? globalVcp;
const app = express();
app.disable("x-powered-by");
const readinessReader = options[CROWN_READINESS_READER];
if (typeof readinessReader === "function") {
  // Run before the general JSON parser: this exact private read accepts no body.
  app.all(CROWN_READINESS_PATH, async (req,res) => {
    res.set("Cache-Control", "no-store");
    res.set("Pragma", "no-cache");
    try {
      const snapshot = await readinessReader(req);
      const body = JSON.stringify(snapshot);
      if (Buffer.byteLength(body) > 8192) throw new Error("AUTHORITY_UNAVAILABLE");
      res.status(200).type("application/json").send(body);
    } catch {
      res.status(403).json({ok:false,code:"AUTHORITY_UNAVAILABLE"});
    }
  });
}
app.use(express.json({
  limit: CROWN_TRANSPORT_LIMITS.MAX_CROWN_HTTP_BYTES,
  verify(req, _res, buffer) {
    let frame;
    try { frame = JSON.parse(buffer.toString("utf8")); } catch { /* express retains its JSON parse error */ }
    const crown = req.method === "POST" && req.path === "/mcp" &&
      frame?.jsonrpc === "2.0" && frame?.method === "tools/call" &&
      frame?.params?.name === PROJECT_FORGE_CROWN_TOOL_NAME &&
      frame.params.arguments && typeof frame.params.arguments === "object" &&
      !Array.isArray(frame.params.arguments);
    let reject = !crown && buffer.length > CROWN_TRANSPORT_LIMITS.LEGACY_HTTP_BYTES;
    if (crown) {
      const argsBytes = Buffer.byteLength(JSON.stringify(frame.params.arguments), "utf8");
      const metadataBytes = Buffer.byteLength(JSON.stringify({...frame, params: {...frame.params, arguments: null}}), "utf8");
      reject = argsBytes > CROWN_TRANSPORT_LIMITS.MAX_CROWN_REQUEST_BYTES ||
        metadataBytes > CROWN_TRANSPORT_LIMITS.MCP_METADATA_BYTES;
    }
    if (reject) {
      const error = new Error("JSON request exceeds its bounded transport capacity.");
      error.status = 413;
      throw error;
    }
  },
}));

app.get("/", (_req, res) => {
  res.json({
    name: "vcp-chatgpt-app-r0a",
    version: VCP_APP_VERSION,
    mcp: "/mcp",
    upstream: config.vcpBaseUrl,
  });
});

app.get("/healthz", (_req, res) => {
  res.json({ ok: true, service: "vcp-chatgpt-app-r0a" });
});

app.get("/readyz", async (_req, res) => {
  try {
    const data = await vcp.listModels();
    res.json({ ok: true, models: modelList(data) });
  } catch (error) {
    res.status(503).json({
      ok: false,
      error: options.sanitizeMcpErrors ? "UPSTREAM_UNAVAILABLE" : error?.message || String(error),
    });
  }
});

app.post("/mcp", async (req, res) => {
  // Only the controlled host supplies this resolver. Ordinary headers/body never
  // become authority, and no public route can register or widen an Owner task.
  const dependencies = options.runtimeDependencies ?? {};
  const server = createMcpServer({...options, runtimeDependencies: {...dependencies,
    projectForgeCrownContext: typeof dependencies.resolveProjectForgeCrownContext === "function"
      ? (() => {let context; return () => context ??= Promise.resolve().then(() => dependencies.resolveProjectForgeCrownContext(req));})()
      : dependencies.projectForgeCrownContext}});
  const transport = new StreamableHTTPServerTransport({
    sessionIdGenerator: undefined,
  });

  res.on("close", () => {
    Promise.resolve(transport.close()).catch(() => {});
    Promise.resolve(server.close()).catch(() => {});
  });

  try {
    await server.connect(transport);
    await transport.handleRequest(req, res, req.body);
  } catch (error) {
    if (!options.sanitizeMcpErrors) console.error("[mcp]", error);
    if (!res.headersSent) {
      res.status(500).json({
        jsonrpc: "2.0",
        id: req.body?.id ?? null,
        error: {
          code: -32603,
          message: options.sanitizeMcpErrors ? "Internal MCP error" : error?.message || "Internal MCP error",
        },
      });
    }
  }
});

app.get("/mcp", (_req, res) => {
  res.status(405).json({
    error: "Stateless MCP endpoint: POST is supported; standalone GET stream is not enabled.",
  });
});

app.delete("/mcp", (_req, res) => {
  res.status(405).json({
    error: "Stateless MCP endpoint: sessions are disabled.",
  });
});

return app;
}

// Process-private actual-request observation. JSON reports contain no ticket or
// context authority. This facade waits; it never sends HTTP/MCP requests itself.
let currentCrownAcceptanceHost=null;
const productionAcceptanceHosts=new WeakMap();
export function getCurrentCrownAcceptanceHost(){return currentCrownAcceptanceHost;}
const CROWN_MUTATIONS=new Set(['create_project','create_file','edit_code','rollback','update_todos','submit_report']);
function createCrownAcceptanceObserver({runtime,host,now}) {
  const record=host.registration;
  if(!record || typeof host.verifyTaskAuthorization!=='function')return null;
  const tickets=new WeakMap(),pending=new Map(),active=new Map(),byContext=new WeakMap(),evidenceBrands=new WeakSet(),
    receiptBrands=new WeakMap(),routeBrands=new WeakMap(),rollbackTargets=new Set();
  let closed=false,fresh=false,uncertain=false,reportSink=null,projectId=record.target.projectId,sequence=0;
  const exact=value=>freeze(structuredClone(value));
  function expire(){for(const state of active.values())if(now()>=state.expires_at)stop(state,'PROOF_EXPIRED');}
  async function current(){
    return !closed && Number.isSafeInteger(now()) && now()>=record.issued_at && now()<record.expires_at &&
      await host.verifyTaskAuthorization(record)===true && !closed &&
      Number.isSafeInteger(now()) && now()>=record.issued_at && now()<record.expires_at;
  }
  function owner(evidence){return evidenceBrands.has(evidence) && evidence.expires_at===record.expires_at;}
  function owned(ticket){const state=tickets.get(ticket);requireThat(state,'AUTHORITY_REJECTED');return state;}
  function stop(state,code){if(state.status==='PENDING'||state.status==='BOUND'){
    if(state.status==='BOUND')uncertain=true;
    state.status=code;pending.delete(state.sha);active.delete(state.number);clearTimeout(state.timer);state.reject(Object.assign(new Error(code),{code}));}}
  const expected=(request,state)=>({request,trustedContext:state.context,authorization_sha256:record.authorization_sha256,
    client_binding:record.client_binding,targetRoot:record.target.projectRoot});
  const facade={
    async activationEvidence(){requireThat(await current(),'AUTHORITY_REJECTED');
      const evidence=exact({synthetic:/^\/tmp\/r16-[A-Za-z0-9_-]+\//.test(record.target.projectRoot),task_id:record.task_id,expires_at:record.expires_at,
        target_root:record.target.projectRoot,authorization_sha256:record.authorization_sha256,
        client_binding:record.client_binding,workspace:{id:record.target.workspaceId,alias:record.target.workspaceAlias,
          path:path.posix.dirname(record.target.projectRoot)}});evidenceBrands.add(evidence);return evidence;},
    async verifyActivation(evidence){return owner(evidence)&&await current();},
    async verifyTarget({request,projectId:id,targetRoot,evidence}){
      return owner(evidence)&&await current()&&targetRoot===record.target.projectRoot &&
        validateCrownRequest(request).ok && record.actions.includes(request.action) &&
        (id==null||id===projectId) && (!request.project_id||request.project_id===projectId);
    },
    async admitAction(request,evidence){
      requireThat(owner(evidence)&&await current(),'AUTHORITY_REJECTED');expire();
      const validation=validateCrownRequest(request);requireThat(validation.ok && record.actions.includes(request.action),'AUTHORITY_REJECTED');
      requireThat(!CROWN_MUTATIONS.has(request.action)||!uncertain,'UNKNOWN_OUTCOME');
      requireThat(!CROWN_MUTATIONS.has(request.action)||fresh,'FRESH_TASK_INGRESS_PENDING');
      const sha=digest(validation.request);requireThat(!pending.has(sha)&&active.size<32,'AUTHORITY_REJECTED');
      // Only the first unbound discovery waits for the existing Owner window.
      // Task expiry is immutable; binding starts the ordinary 60-second budget.
      const firstReadWait=sequence===0 && !fresh && request.action==='list_workspaces';
      const registeredAt=now();
      const state={request:exact(validation.request),sha,number:++sequence,registered_at:registeredAt,firstReadWait,
        expires_at:Math.min(record.expires_at,registeredAt+(firstReadWait?48*60*60*1000:60000)),
        status:'PENDING',context:null,response:null,timer:null};
      state.completion=new Promise((resolve,reject)=>{state.resolve=resolve;state.reject=reject;});
      state.completion.catch(()=>{});
      const ticket=Object.freeze({get trustedContext(){return state.context;}});
      tickets.set(ticket,state);pending.set(sha,state);active.set(state.number,state);
      state.timer=setTimeout(()=>stop(state,'PROOF_EXPIRED'),Math.max(1,state.expires_at-now()));
      try{reportSink?.(facade.report());}catch { /* Report delivery adds no execution authority. */ }
      return ticket;
    },
    createObserverClient(evidence){requireThat(owner(evidence)&&!closed,'AUTHORITY_REJECTED');return Object.freeze({
      waitForCompletion:async ticket=>{const state=owned(ticket);requireThat(await current(),'AUTHORITY_REJECTED');
        const response=await state.completion;requireThat(await current() && state.status==='COMPLETE' &&
          now()<state.expires_at,'PROOF_EXPIRED');return response;},
      close(){for(const state of active.values())stop(state,'AUTHORITY_UNAVAILABLE');}
    });},
    observeIngress({trustedContext,request}){
      const state=pending.get(digest(request));if(!state)return;
      if(closed||state.status!=='PENDING'||now()>=state.expires_at){stop(state,'PROOF_EXPIRED');return;}
      if(state.firstReadWait){
        clearTimeout(state.timer);state.expires_at=Math.min(now()+60000,record.expires_at);
        state.timer=setTimeout(()=>stop(state,'PROOF_EXPIRED'),Math.max(1,state.expires_at-now()));
      }
      state.context=trustedContext;state.status='BOUND';byContext.set(trustedContext,state);pending.delete(state.sha);
    },
    observeCompletion({trustedContext,request,response}){
      const state=byContext.get(trustedContext);
      if(state && response?.structuredContent?.error?.code==='UNKNOWN_OUTCOME')uncertain=true;
      if(!state||state.status!=='BOUND'||state.sha!==digest(request))return;
      if(closed||now()>=state.expires_at){stop(state,'PROOF_EXPIRED');return;}
      state.response=response;state.status='COMPLETE';active.delete(state.number);clearTimeout(state.timer);
      if(response?.structuredContent?.error?.code==='UNKNOWN_OUTCOME')uncertain=true;
      if(response?.structuredContent && typeof response.structuredContent==='object')receiptBrands.set(response.structuredContent,state);
      state.resolve(response);
    },
    async verifyReceipt({request,fields,evidence,targetRoot}){
      const state=receiptBrands.get(fields);
      if(!state||!owner(evidence)||state.sha!==digest(request)||targetRoot!==record.target.projectRoot||!await current())return false;
      if(request.action==='create_project'&&fields.ok&&fields.completion_verified){
        if(projectId!==null||typeof fields.project_id!=='string')return false;projectId=fields.project_id;
      }
      return fields.ok===true&&fields.completion_verified===true;
    },
    async readAppEvidence({request,fields,admitted,evidence}){
      const state=owned(admitted);requireThat(owner(evidence)&&await current()&&state.response?.structuredContent===fields &&
        state.sha===digest(request),'AUTHORITY_REJECTED');
      return runtime.readEvidence({trustedContext:state.context,request});
    },
    async observeRoute({request,admitted,snapshot,evidence}){
      const state=owned(admitted);requireThat(owner(evidence)&&await current(),'AUTHORITY_REJECTED');
      const routes=await runtime.readRoutes({trustedContext:state.context,request,snapshot});
      requireThat(await current(),'AUTHORITY_REJECTED');routeBrands.set(snapshot,routes);return routes;
    },
    async verifyRoute({request,admitted,observation,snapshot,evidence}){
      const state=owned(admitted),routes=routeBrands.get(snapshot);
      return owner(evidence)&&routes?.includes(observation)&&await current()&&
        await verifyCrownRouteEvidence(routes,{snapshot,...expected(request,state)})===true && await current();
    },
    async verifyFreshTaskIngress({request,admitted,fields,snapshot,evidence}){
      const state=owned(admitted);
      if(!owner(evidence)||request.action!=='list_workspaces'||state.status!=='COMPLETE'||
        state.response?.structuredContent!==fields||!fields.ok||!fields.completion_verified||!await current())return false;
      const verified=await verifyCrownAppEvidence(snapshot,expected(request,state));
      const main=snapshot?.calls?.some(call=>call.mode==='execute'&&call.request_sha256===state.sha &&
        call.native_epoch===record.native_epoch && canonical(call.identity)===canonical(record.identity));
      if(!verified||!main||snapshot.incomplete||!await current())return false;fresh=true;return true;
    },
    async registerRollback({request,receipt,evidence,targetRoot,projectId:id}){
      const state=receiptBrands.get(receipt);if(request?.action!=='rollback'||!validateCrownRequest(request).ok||
        !owner(evidence)||!fresh||!state||!await current()||
        targetRoot!==record.target.projectRoot||id!==projectId||receipt.project_id!==projectId)return false;
      if(request.batch_id && request.batch_id!==receipt.batch_id || request.to_node_id &&
        (request.to_node_id!==receipt.node_id || request.path!==state.request.path))return false;
      rollbackTargets.add(digest(request));return true;
    },
    canExecute(request){const sha=digest(request),state=pending.get(sha);
      return !CROWN_MUTATIONS.has(request.action)||!uncertain && fresh && state?.status==='PENDING' && now()<state.expires_at &&
        (request.action!=='rollback'||rollbackTargets.has(sha));},
    setReportSink(sink){requireThat(typeof sink==='function','AUTHORITY_UNAVAILABLE');reportSink=sink;},
    report(){expire();return exact({schema:1,status:closed?'CLOSED':uncertain?'UNKNOWN_OUTCOME':fresh?'FRESH_TASK_INGRESS_VERIFIED':'WAITING_READ_ONLY',
      task_sha256:digest(record),expires_at:record.expires_at,fresh_task_ingress:fresh,
      pending:[...pending.values()].slice(0,32).map(state=>({sequence:state.number,request_sha256:state.sha,
        expires_at:state.expires_at,request:state.request}))});},
    close(){closed=true;fresh=false;for(const state of active.values())stop(state,'AUTHORITY_UNAVAILABLE');pending.clear();active.clear();}
  };
  return Object.freeze(facade);
}

// Concrete private task assembly is default off. Task files are installed by the
// controlled deployer; public MCP data cannot register or expand a task.
export async function createProductionHttpApp({appConfig = config, crownHost, crownEvidenceAdapter, crownAcceptance = false, crownObservationSink, now = Date.now, ...options} = {}) {
  const host = crownHost ?? await createCrownTaskHost({config:appConfig,now});
  let runtime,acceptance;
  try {
    runtime = await createCrownHostRuntime({config:appConfig,host,now});
    // This callback is an in-process host dependency, never supplied by JSON,
    // headers or a public registration route. It receives the actual admitted
    // context and no raw ingress headers. Observation failure only marks a gap.
    const enabled=runtime && typeof crownEvidenceAdapter==='function';
    acceptance=runtime && crownAcceptance === true ? createCrownAcceptanceObserver({runtime,host,now}) : null;
    const dependencies={...runtime?.runtimeDependencies};
    if(runtime) {
      const resolve=dependencies.resolveProjectForgeCrownContext;
      dependencies.resolveProjectForgeCrownContext=async req=>{
        const trustedContext=await resolve(req);
        if(trustedContext && acceptance && !acceptance.canExecute(req.body.params.arguments))return null;
        if(trustedContext) {
          try{acceptance?.observeIngress({trustedContext,request:req.body.params.arguments});}
          catch {runtime.markEvidenceIncomplete(trustedContext);}
        }
        if(trustedContext && enabled) {
          try {
            const request=Object.freeze(structuredClone(req.body.params.arguments));
            const requestId=req.body.id;
            let timer;
            try {
              await Promise.race([Promise.resolve().then(()=>crownEvidenceAdapter(Object.freeze({trustedContext,request,
                requestId:typeof requestId==='string' && requestId.length<=128 || Number.isSafeInteger(requestId)?requestId:null}))),
                new Promise((_resolve,reject)=>{timer=setTimeout(()=>reject(new Error('EVIDENCE_TIMEOUT')),50);})]);
            } finally {clearTimeout(timer);}
          } catch {runtime.markEvidenceIncomplete(trustedContext);}
        }
        return trustedContext;
      };
    }
    // Bounded observation of already admitted calls. This private dependency
    // enrolls nothing, sends no public tool request and never logs request bytes.
    const observationJobs=new Set();let observationTail=Promise.resolve(),observationCount=0,observationClosing=false,observationCapacityReported=false;
    const observing=runtime && typeof crownObservationSink==='function';
    const emitObservation=row=>{try{Promise.resolve(crownObservationSink(freeze(row))).catch(()=>{});}catch{}};
    async function observeCompleted({trustedContext,request,response}) {
      requireThat(!observationClosing,'AUTHORITY_UNAVAILABLE');
      const expected={trustedContext,request,authorization_sha256:host.registration.authorization_sha256,
        client_binding:host.registration.client_binding,targetRoot:host.registration.target.projectRoot};
      const snapshot=await runtime.readEvidence({trustedContext,request});
      requireThat(await verifyCrownAppEvidence(snapshot,expected)===true,'PROOF_REJECTED');
      requireThat(!observationClosing,'AUTHORITY_UNAVAILABLE');
      const routes=snapshot.calls.length?await runtime.readRoutes({trustedContext,request,snapshot}):[];
      requireThat(!observationClosing && (!routes.length || await verifyCrownRouteEvidence(routes,{snapshot,...expected})===true),'PROOF_REJECTED');
      const {projectR16ObservedRoute,emitR16ControlledAcceptanceEvidence,R16_ROUTE_BOUNDARIES}=await import('../scripts/e2e-r16-production-acceptance.mjs');
      const projected=routes.map(route=>{
        const call=snapshot.calls.find(call=>call.request_id===route.request_id);
        requireThat(call && route.incomplete!==true,'PROOF_REJECTED');
        const projected=projectR16ObservedRoute(route,call,snapshot.observed_at);
        requireThat(canonical([...new Set(projected.boundaries.filter(row=>row.kind!=='source-attestation').map(row=>row.boundary))].sort())===canonical([...R16_ROUTE_BOUNDARIES].sort()),'PROOF_REJECTED');
        return projected;
      });
      const fields=response?.structuredContent;
      requireThat(fields && fields.action===request.action,'PROOF_REJECTED');
      emitR16ControlledAcceptanceEvidence({synthetic:/^\/tmp\/r16-[^/]+\//.test(expected.targetRoot),
        authorization_sha256:expected.authorization_sha256,
        receipts:[{action:request.action,request_sha256:digest(request),project_id:fields.project_id,
          node_id:fields.node_id,batch_id:fields.batch_id,completion_verified:fields.completion_verified}],
        appEvidence:[snapshot],routeProof:projected},emitObservation);
    }
    dependencies.observeProjectForgeCrownCompletion=value=>{
      try {acceptance?.observeCompletion(value);}catch {runtime?.markEvidenceIncomplete(value.trustedContext);}
      if(!observing||observationClosing)return;
      if(observationCount++>=128||observationJobs.size>=32){
        runtime.markEvidenceIncomplete(value.trustedContext);
        if(!observationCapacityReported){observationCapacityReported=true;emitObservation({schema:1,type:'R16_CONTROLLED_OBSERVATION_PENDING',code:'EVIDENCE_CAPACITY'});}return;
      }
      const job=observationTail.then(()=>observeCompleted(value)).catch(()=>{
        runtime.markEvidenceIncomplete(value.trustedContext);
        emitObservation({schema:1,type:'R16_CONTROLLED_OBSERVATION_PENDING',code:'PROOF_UNAVAILABLE',
          action:value.request.action,request_sha256:digest(value.request)});
      });
      observationJobs.add(job);observationTail=job;job.then(()=>observationJobs.delete(job),()=>observationJobs.delete(job));
    };
    const app = createHttpApp({...options, appConfig,
      [CROWN_READINESS_READER]:runtime?.readReadiness,
      runtimeDependencies:{...options.runtimeDependencies, ...dependencies}});
    const production=Object.freeze({app,acceptance, executor:runtime?.runtimeDependencies.projectForgeCrownExecutor,
      authorityExpiresAt:runtime?.authorityExpiresAt??null,authorityNow:runtime?.authorityNow??now,
      stopIngress:()=>runtime?.stopIngress(),
      closureSnapshot:()=>runtime?.closureSnapshot()??null,
      disposeClosure:()=>runtime?.disposeClosure(),
      close:options => {observationClosing=true;runtime?.stopIngress();acceptance?.close();
        if(currentCrownAcceptanceHost===acceptance)currentCrownAcceptanceHost=null;
        // Observation cannot extend the shared shutdown budget. Queued jobs
        // stop before further reads; an unfinished proof remains PENDING.
        return runtime?.close(options);},
      evidence:enabled?Object.freeze({readAppEvidence:runtime.readEvidence,readRoutes:runtime.readRoutes}):null});
    if(acceptance)productionAcceptanceHosts.set(production,Object.freeze({host:acceptance,now}));return production;
  } catch (error) { if(runtime) await runtime.close(); else await host?.abort?.(); throw error; }
}

export async function startCrownAcceptanceObservation(production,{onReport,fixturePolicy}={}) {
  const entry=productionAcceptanceHosts.get(production),host=entry?.host;requireThat(host,'AUTHORITY_UNAVAILABLE');
  if(typeof onReport==='function')host.setReportSink(onReport);
  const {runR16ProductionAcceptance}=await import('../scripts/e2e-r16-production-acceptance.mjs');
  return runR16ProductionAcceptance({host,fixturePolicy,now:entry.now});
}

// One process signal/expiry path: stop new Crown ingress, finish accepted calls,
// verify the existing close ACKs, close HTTP, then release the local writer lease.
// No timeout retries cleanup, replays a tool, kills a socket, or grants later authority.
export function attachProductionShutdown(listener, production, {
  processLike = process, drainTimeoutMs = 10000, expiryLeadMs = 15000,
  reportComplete = () => {},
  reportFailure = message => console.error(message),
  markFailure = () => { processLike.exitCode = 1; },
} = {}) {
  requireThat(Number.isSafeInteger(drainTimeoutMs)&&drainTimeoutMs>0&&drainTimeoutMs<=60000 &&
    Number.isSafeInteger(expiryLeadMs)&&expiryLeadMs>=drainTimeoutMs+1000,'AUTHORITY_REJECTED');
  let attempt=null,expiryTimer,deadlineTimer,failureHold,resolveFinished,disposed=false,retryReady=false;
  const finished=new Promise(resolve=>{resolveFinished=resolve;});
  const signals=new Map();
  function detach() {
    clearTimeout(expiryTimer);
    for(const [signal,handler] of signals)processLike.removeListener(signal,handler);
    listener.removeListener('close',onClose);
  }
  function shutdown(reason) {
    if(attempt&&!retryReady)return attempt;
    retryReady=false;
    production.stopIngress?.();clearTimeout(expiryTimer);
    const remaining=Number.isSafeInteger(production.authorityExpiresAt)
      ? production.authorityExpiresAt-production.authorityNow() : drainTimeoutMs;
    const timeoutMs=Math.max(1,Math.min(drainTimeoutMs,remaining));
    let expired=false,closingSettled=false,failed=false;
    const closing=(async()=>{
      await production.close({timeoutMs});
      requireThat(!expired,'AUTHORITY_UNAVAILABLE');
      if(listener.listening!==false && reason!=='listener-close') {
        await new Promise((resolve,reject)=>listener.close(error=>error?reject(error):resolve()));
      }
      requireThat(!expired,'AUTHORITY_UNAVAILABLE');
      const lifecycleSnapshot=production.closureSnapshot?.()??null;
      production.disposeClosure?.();
      return {status:'CLOSED',reason,lifecycleSnapshot};
    })();
    // A deadline does not cancel close(). Never overlap its late effects with a
    // retry. Only a later explicit shutdown call may retry a settled failure.
    const settled=()=>{closingSettled=true;if(failed)retryReady=true;};
    closing.then(settled,settled);
    attempt=Promise.race([closing,new Promise((_,reject)=>{
      deadlineTimer=setTimeout(()=>{expired=true;reject(new Error('AUTHORITY_UNAVAILABLE'));},timeoutMs);
    })]).then(result=>{
      clearTimeout(deadlineTimer);clearInterval(failureHold);failureHold=null;detach();
      try{reportComplete(result);}catch{markFailure();}
      resolveFinished(result);return result;
    },()=>{
      expired=true;failed=true;retryReady=closingSettled;clearTimeout(deadlineTimer);clearTimeout(expiryTimer);markFailure();
      // Retain process ownership on failure even if HTTP was already closed.
      failureHold??=setInterval(()=>{},1000);
      try{reportFailure('[VCP-APP] Crown shutdown failed: AUTHORITY_UNAVAILABLE; external cleanup remains pending.');}catch{}
      const result={status:'BLOCK',reason};resolveFinished(result);return result;
    });
    return attempt;
  }
  function onClose(){if(!attempt)shutdown('listener-close');}
  listener.on('close',onClose);
  for(const signal of ['SIGTERM','SIGINT']) {
    const handler=()=>shutdown(signal);signals.set(signal,handler);processLike.on(signal,handler);
  }
  if(Number.isSafeInteger(production.authorityExpiresAt)) {
    expiryTimer=setTimeout(()=>shutdown('authority-expiry'),
      Math.max(1,production.authorityExpiresAt-production.authorityNow()-expiryLeadMs));
    expiryTimer.unref?.();
  }
  return Object.freeze({finished,shutdown,dispose(){
    if(disposed)return;disposed=true;detach();clearTimeout(deadlineTimer);clearInterval(failureHold);
  }});
}

if (process.argv[1] && import.meta.url === pathToFileURL(path.resolve(process.argv[1])).href) {
const production = await createProductionHttpApp({
  crownObservationSink:config.crownEnabled?row=>console.log(JSON.stringify(row)):undefined
});
currentCrownAcceptanceHost=production.acceptance;
const listener = production.app.listen(config.port, config.host, () => {
  console.log(
    `[VCP-APP] MCP listening on http://${config.host}:${config.port}/mcp`
  );
  console.log(`[VCP-APP] Direct VCP upstream: ${config.vcpBaseUrl}`);
  console.log(`[VCP-APP] VCP chat path: ${config.vcpChatPath}`);
  console.log(
    `[VCP-APP] Fixed VCP system prompt: ${config.vcpSystemPrompt ? "loaded" : "not configured"}`
  );
});
attachProductionShutdown(listener, production);
listener.once('listening',()=>{
if(production.acceptance) {
  const emit=row=>console.log(JSON.stringify(row));
  const evidence=async result=>{
    const {emitR16ControlledAcceptanceEvidence}=await import('../scripts/e2e-r16-production-acceptance.mjs');
    return emitR16ControlledAcceptanceEvidence(result,emit);
  };
  startCrownAcceptanceObservation(production,{onReport:report=>{
    const text=JSON.stringify({type:'R16_CONTROLLED_PENDING_REQUEST',...report});
    if(Buffer.byteLength(text)<=32768)console.log(text);
  }}).then(async result=>{
    const reporting=await evidence(result);
    emit({type:'R16_CONTROLLED_ACCEPTANCE_RESULT',status:result.status,synthetic:result.synthetic,
      actions:result.actions,missingProof:result.missingProof,error:result.error??null,reporting});
  }).catch(async error=>{
    const reporting=error?.evidence?await evidence(error.evidence):{status:'PENDING',emitted:0,dropped:0};
    console.error(JSON.stringify({type:'R16_CONTROLLED_ACCEPTANCE_RESULT',status:'BLOCK',reporting,
      code:['AUTHORITY_UNAVAILABLE','AUTHORITY_REJECTED','PROOF_REJECTED','PROOF_EXPIRED','UNKNOWN_OUTCOME'].includes(error?.code)?error.code:'ACCEPTANCE_FAILED'}));
  });
}
});
}
