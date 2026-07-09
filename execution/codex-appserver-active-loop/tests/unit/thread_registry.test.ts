import { describe, expect, it } from "vitest";
import { createThreadRegistry } from "../../src/bridge/thread_registry.js";
import type { CodexPeerRole } from "../../src/types/messages.js";

describe("Codex thread registry", () => {
  it("registers Worker, Reviewer, and Verifier threads by role", () => {
    const registry = createThreadRegistry();

    const worker = registry.register({ role: "worker", threadId: "thread_worker_001", cwd: "A:/synthetic" });
    const reviewer = registry.register({ role: "reviewer", threadId: "thread_reviewer_001", cwd: "A:/synthetic" });
    const verifier = registry.register({ role: "verifier", threadId: "thread_verifier_001", cwd: "A:/synthetic" });

    expect(registry.requireByRole("worker")).toEqual(worker);
    expect(registry.requireByRole("reviewer")).toEqual(reviewer);
    expect(registry.requireByRole("verifier")).toEqual(verifier);
    expect(registry.snapshot().threads.map((thread) => thread.role)).toEqual(["worker", "reviewer", "verifier"]);
  });

  it("rejects duplicate role registrations", () => {
    const registry = createThreadRegistry();
    registry.register({ role: "worker", threadId: "thread_worker_001", cwd: "A:/synthetic" });

    expect(() => registry.register({ role: "worker", threadId: "thread_worker_002", cwd: "A:/synthetic" })).toThrow(
      "role already registered: worker",
    );
  });

  it("rejects duplicate thread id registrations", () => {
    const registry = createThreadRegistry();
    registry.register({ role: "worker", threadId: "thread_shared_001", cwd: "A:/synthetic" });

    expect(() => registry.register({ role: "reviewer", threadId: "thread_shared_001", cwd: "A:/synthetic" })).toThrow(
      "thread already registered: thread_shared_001",
    );
  });

  it("requires active started threads for routing", () => {
    const registry = createThreadRegistry();
    const worker = registry.register({ role: "worker", threadId: "thread_worker_001", cwd: "A:/synthetic" });
    registry.markStatus(worker.threadId, "COMPLETED");

    expect(() => registry.requireByRole("worker")).toThrow("worker thread is not active: COMPLETED");
  });

  it("rejects inactive Verifier threads for routing", () => {
    const registry = createThreadRegistry();
    const verifier = registry.register({ role: "verifier", threadId: "thread_verifier_001", cwd: "A:/synthetic" });
    registry.markStatus(verifier.threadId, "COMPLETED");

    expect(() => registry.requireByRole("verifier")).toThrow("verifier thread is not active: COMPLETED");
  });

  it("registers arbitrary safe role labels as routing identities", () => {
    const registry = createThreadRegistry();

    const planner = registry.register({ role: "planner" as CodexPeerRole, threadId: "thread_planner_001", cwd: "A:/synthetic" });
    const auditor = registry.register({ role: "auditor" as CodexPeerRole, threadId: "thread_auditor_001", cwd: "A:/synthetic" });

    expect(registry.requireByRole("planner")).toEqual(planner);
    expect(registry.requireByRole("auditor")).toEqual(auditor);
  });

  it("rejects unsafe role label syntax", () => {
    const registry = createThreadRegistry();

    expect(() => registry.register({ role: "" as CodexPeerRole, threadId: "thread_blank_001", cwd: "A:/synthetic" })).toThrow(
      "unsafe role label: ",
    );
    expect(() => registry.register({ role: "external:http" as CodexPeerRole, threadId: "thread_external_001", cwd: "A:/synthetic" })).toThrow(
      "unsafe role label: external:http",
    );
    expect(() => registry.requireByRole("../escape" as CodexPeerRole)).toThrow("unsafe role label: ../escape");
  });
});
