import { describe, expect, it } from "vitest";
import {
  createConversationObserverModel,
  createObserverLiveSnapshot,
  renderObserverHtml,
  renderObserverTranscript,
} from "../../src/bridge/conversation_observer.js";

describe("conversation observer", () => {
  it("renders local Commander dialogue content with route metadata and secret-like field redaction", () => {
    const model = createConversationObserverModel({
      projectFolder: "codex-appserver-active-loop",
      selectedLogPath: "data/message-logs/job-observer.json",
      logs: [
        {
          jobId: "job-observer",
          label: "job-observer",
          filePath: "data/message-logs/job-observer.json",
          selected: true,
        },
      ],
      selectedLog: {
        job_id: "job-observer",
        message_events: [
          {
            event: "MESSAGE_ROUTED",
            timestamp: "2026-07-08T00:00:00.000Z",
            message_id: "msg_worker_001",
            conversation_id: "conv_observer_001",
            correlation_id: "corr_observer_001",
            from: "worker",
            to: "reviewer",
            fromThreadId: "thread_worker_001",
            toThreadId: "thread_reviewer_001",
            state: "ROUTED",
            round: 1,
          },
          {
            event: "REPLY_ROUTED",
            timestamp: "2026-07-08T00:00:01.000Z",
            message_id: "msg_reviewer_001",
            reply_to: "msg_worker_001",
            conversation_id: "conv_observer_001",
            correlation_id: "corr_observer_001",
            from: "reviewer",
            to: "worker",
            fromThreadId: "thread_reviewer_001",
            toThreadId: "thread_worker_001",
            round: 1,
          },
          {
            event: "CHANNEL_DONE",
            timestamp: "2026-07-08T00:00:02.000Z",
            conversation_id: "conv_observer_001",
            round: 1,
          },
        ],
      },
      companionReport: {
        job_id: "job-observer",
        messages: {
          worker_message: {
            type: "MESSAGE_TO_CODEX",
            message_id: "msg_worker_001",
            correlation_id: "corr_observer_001",
            conversation_id: "conv_observer_001",
            from: "worker",
            to: "reviewer",
            kind: "question",
            payload: {
              question: "Please review this decision point.",
              context: ["route metadata should be visible"],
              expected_response: "decision",
            },
          },
          reviewer_reply: {
            type: "CODEX_MESSAGE_REPLY",
            message_id: "msg_reviewer_001",
            reply_to: "msg_worker_001",
            correlation_id: "corr_observer_001",
            conversation_id: "conv_observer_001",
            from: "reviewer",
            to: "worker",
            kind: "answer",
            payload: {
              decision: "continue",
              reason: "The local observer can show dialogue content.",
              next_instruction: "Continue.",
              api_key: "should-not-render",
            },
          },
          worker_done: {
            type: "DONE",
            summary: "Observer flow completed.",
            evidence: ["timeline rendered"],
          },
        },
      },
      filters: {
        conversationId: "conv_observer_001",
      },
    });

    const transcript = renderObserverTranscript(model);
    const html = renderObserverHtml(model);

    expect(model.boundary.message_bus_mutation).toBe("NOT_USED");
    expect(model.boundary.external_review_package_raw_payload).toBe("DEFAULT_DENY");
    expect(model.cards.some((card) => card.state === "ROUTED")).toBe(true);
    expect(model.cards.some((card) => card.state === "REPLIED")).toBe(true);
    expect(transcript).toContain("Please review this decision point.");
    expect(transcript).toContain("The local observer can show dialogue content.");
    expect(transcript).toContain("thread_worker_001");
    expect(transcript).toContain("<REDACTED_SECRET_LIKE_FIELD>");
    expect(transcript).not.toContain("should-not-render");
    expect(html).toContain("project-group");
    expect(html).toContain("thread-queue");
    expect(html).toContain("timeline-card");
    expect(html).toContain("Please review this decision point.");
  });

  it("filters by role and distinguishes observed, rejected, expired, blocked, and done states", () => {
    const model = createConversationObserverModel({
      projectFolder: "codex-appserver-active-loop",
      selectedLogPath: "data/message-logs/job-observer-states.json",
      logs: [
        {
          jobId: "job-observer-states",
          label: "job-observer-states",
          filePath: "data/message-logs/job-observer-states.json",
          selected: true,
        },
      ],
      selectedLog: {
        job_id: "job-observer-states",
        message_events: [
          {
            event: "MESSAGE_OBSERVED",
            timestamp: "2026-07-08T00:00:00.000Z",
            message_id: "msg_observed",
            conversation_id: "conv_states",
            from: "worker",
            to: "reviewer",
          },
          {
            event: "MESSAGE_REJECTED",
            timestamp: "2026-07-08T00:00:01.000Z",
            message_id: "msg_rejected",
            conversation_id: "conv_states",
            from: "worker",
            to: "reviewer",
          },
          {
            event: "MESSAGE_EXPIRED",
            timestamp: "2026-07-08T00:00:02.000Z",
            message_id: "msg_expired",
            conversation_id: "conv_states",
            from: "worker",
            to: "reviewer",
          },
          {
            event: "CONVERSATION_BLOCKED",
            timestamp: "2026-07-08T00:00:03.000Z",
            conversation_id: "conv_states",
            from: "worker",
            to: "reviewer",
          },
          {
            event: "CHANNEL_DONE",
            timestamp: "2026-07-08T00:00:04.000Z",
            conversation_id: "conv_states",
            from: "worker",
            to: "reviewer",
          },
        ],
      },
      filters: {
        role: "reviewer",
      },
    });

    expect(model.stateCounts.OBSERVED).toBe(1);
    expect(model.stateCounts.REJECTED).toBe(1);
    expect(model.stateCounts.EXPIRED).toBe(1);
    expect(model.stateCounts.BLOCKED).toBe(1);
    expect(model.stateCounts.DONE).toBe(1);
    expect(model.cards.every((card) => card.to === "reviewer" || card.from === "reviewer")).toBe(true);
  });

  it("renders live-tail status, auto-refresh, raw toggle, and live snapshot metadata", () => {
    const model = createConversationObserverModel({
      projectFolder: "codex-appserver-active-loop",
      selectedLogPath: "data/message-logs/job-live.messages.jsonl",
      logs: [
        {
          jobId: "job-live",
          label: "job-live",
          filePath: "data/message-logs/job-live.messages.jsonl",
          selected: true,
        },
      ],
      selectedLog: {
        job_id: "job-live",
        message_events: [
          {
            event: "MESSAGE_OBSERVED",
            timestamp: "2026-07-08T00:00:00.000Z",
            message_id: "msg_live_001",
            conversation_id: "conv_live",
            from: "worker",
            to: "reviewer",
          },
        ],
      },
      companionReport: {
        job_id: "job-live",
        messages: {
          worker_message: {
            type: "MESSAGE_TO_CODEX",
            message_id: "msg_live_001",
            conversation_id: "conv_live",
            correlation_id: "corr_live",
            from: "worker",
            to: "reviewer",
            kind: "question",
            payload: {
              question: "This local live tail entry is visible only in the observer.",
            },
          },
        },
      },
      live: {
        status: "LIVE",
        watchedPath: "data/message-logs/job-live.messages.jsonl",
        snapshotPath: "data/observer/job-live.live.json",
        lastUpdatedAt: "2026-07-08T00:00:01.000Z",
        lastEventAt: "2026-07-08T00:00:00.000Z",
        pollMs: 1000,
        staleAfterMs: 10000,
        sourceSizeBytes: 256,
      },
      rawContentVisible: false,
      autoScroll: true,
    });

    const transcript = renderObserverTranscript(model);
    const html = renderObserverHtml(model);
    const snapshot = createObserverLiveSnapshot(model);

    expect(model.live?.status).toBe("LIVE");
    expect(transcript).toContain("Live status: LIVE");
    expect(transcript).toContain("<HIDDEN_IN_OBSERVER_VIEW>");
    expect(transcript).not.toContain("This local live tail entry is visible only in the observer.");
    expect(html).toContain('http-equiv="refresh"');
    expect(html).toContain("Toggle Raw");
    expect(html).toContain("live-live");
    expect(html).toContain("star-drift");
    expect(snapshot).toMatchObject({
      mode: "live-tail",
      raw_content_visible: false,
      live: {
        status: "LIVE",
        watchedPath: "data/message-logs/job-live.messages.jsonl",
      },
    });
  });
});
