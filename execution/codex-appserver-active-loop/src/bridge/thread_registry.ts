import { rolePattern, type CodexPeerRole } from "../types/messages.js";

// Enforces delivery identity only; role/workspace authority belongs to AGENTS.md and working context.

export type CodexThreadStatus = "STARTED" | "COMPLETED" | "FAILED";

export interface CodexThreadRegistration {
  readonly role: CodexPeerRole;
  readonly threadId: string;
  readonly cwd: string;
  readonly startedAt: string;
  readonly status: CodexThreadStatus;
  readonly label?: string;
}

export interface RegisterCodexThreadInput {
  readonly role: CodexPeerRole;
  readonly threadId: string;
  readonly cwd: string;
  readonly startedAt?: string;
  readonly label?: string;
}

export interface ThreadRegistrySnapshot {
  readonly threads: readonly CodexThreadRegistration[];
}

export interface CodexThreadRegistry {
  register(input: RegisterCodexThreadInput): CodexThreadRegistration;
  markStatus(threadId: string, status: CodexThreadStatus): CodexThreadRegistration;
  getByRole(role: CodexPeerRole): CodexThreadRegistration | undefined;
  requireByRole(role: CodexPeerRole): CodexThreadRegistration;
  getByThreadId(threadId: string): CodexThreadRegistration | undefined;
  list(): readonly CodexThreadRegistration[];
  snapshot(): ThreadRegistrySnapshot;
}

export function createThreadRegistry(): CodexThreadRegistry {
  return new InMemoryThreadRegistry();
}

class InMemoryThreadRegistry implements CodexThreadRegistry {
  readonly #byThreadId = new Map<string, CodexThreadRegistration>();
  readonly #threadIdByRole = new Map<CodexPeerRole, string>();

  register(input: RegisterCodexThreadInput): CodexThreadRegistration {
    assertSafeRole(input.role);
    assertSafeThreadId(input.threadId);
    assertSafeCwd(input.cwd);
    if (this.#byThreadId.has(input.threadId)) {
      throw new Error(`thread already registered: ${input.threadId}`);
    }
    if (this.#threadIdByRole.has(input.role)) {
      throw new Error(`role already registered: ${input.role}`);
    }
    const registration: CodexThreadRegistration = {
      role: input.role,
      threadId: input.threadId,
      cwd: input.cwd,
      startedAt: input.startedAt ?? new Date().toISOString(),
      status: "STARTED",
      label: input.label,
    };
    this.#byThreadId.set(registration.threadId, registration);
    this.#threadIdByRole.set(registration.role, registration.threadId);
    return registration;
  }

  markStatus(threadId: string, status: CodexThreadStatus): CodexThreadRegistration {
    const current = this.#byThreadId.get(threadId);
    if (!current) {
      throw new Error(`unknown thread: ${threadId}`);
    }
    const next = { ...current, status };
    this.#byThreadId.set(threadId, next);
    return next;
  }

  getByRole(role: CodexPeerRole): CodexThreadRegistration | undefined {
    assertSafeRole(role);
    const threadId = this.#threadIdByRole.get(role);
    return threadId ? this.#byThreadId.get(threadId) : undefined;
  }

  requireByRole(role: CodexPeerRole): CodexThreadRegistration {
    const registration = this.getByRole(role);
    if (!registration) {
      throw new Error(`missing registered ${role} thread`);
    }
    if (registration.status !== "STARTED") {
      throw new Error(`${role} thread is not active: ${registration.status}`);
    }
    return registration;
  }

  getByThreadId(threadId: string): CodexThreadRegistration | undefined {
    return this.#byThreadId.get(threadId);
  }

  list(): readonly CodexThreadRegistration[] {
    return [...this.#byThreadId.values()];
  }

  snapshot(): ThreadRegistrySnapshot {
    return { threads: this.list() };
  }
}

function assertSafeRole(role: CodexPeerRole): void {
  if (typeof role !== "string" || role.trim() === "" || !rolePattern.test(role)) {
    throw new Error(`unsafe role label: ${String(role)}`);
  }
}

function assertSafeThreadId(threadId: string): void {
  if (!/^[A-Za-z0-9._:-]{1,300}$/.test(threadId)) {
    throw new Error(`unsafe thread id: ${threadId}`);
  }
}

function assertSafeCwd(cwd: string): void {
  if (!cwd || cwd.includes("\0")) {
    throw new Error("unsafe thread cwd");
  }
}
