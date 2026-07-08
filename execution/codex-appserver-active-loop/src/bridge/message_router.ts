import type { CodexMessageBus } from "./message_bus.js";
import type { CodexThreadRegistry } from "./thread_registry.js";
import {
  validateCodexMessageReply,
  validateMessageToCodex,
  type CodexMessageReply,
  type CodexPeerRole,
  type MessageToCodex,
} from "../types/messages.js";

// Routes valid envelopes only; role/workspace authority belongs to AGENTS.md and working context.

export type CodexMessageDeliveryMode = "normal" | "observe_only";
export type CodexMessageDeliveryStatus = "MESSAGE_ROUTED" | "REPLY_ROUTED" | "DRY_ROUTE_RECORDED" | "DRY_REPLY_RECORDED";

export interface CodexMessageDelivery {
  readonly deliveryId: string;
  readonly mode: CodexMessageDeliveryMode;
  readonly status: CodexMessageDeliveryStatus;
  readonly conversationId: string;
  readonly messageId: string;
  readonly replyTo?: string;
  readonly correlationId: string;
  readonly from: CodexPeerRole;
  readonly to: CodexPeerRole;
  readonly fromThreadId: string;
  readonly toThreadId: string;
  readonly at: string;
}

export interface CodexMessageRouter {
  routeMessage(message: unknown, at?: string): CodexMessageDelivery;
  routeReply(reply: unknown, at?: string): CodexMessageDelivery;
}

export function createMessageRouter(input: {
  readonly bus: CodexMessageBus;
  readonly registry: CodexThreadRegistry;
  readonly mode?: CodexMessageDeliveryMode;
}): CodexMessageRouter {
  return new BridgeMessageRouter(input.bus, input.registry, input.mode ?? input.bus.mode);
}

class BridgeMessageRouter implements CodexMessageRouter {
  constructor(
    private readonly bus: CodexMessageBus,
    private readonly registry: CodexThreadRegistry,
    private readonly mode: CodexMessageDeliveryMode,
  ) {}

  routeMessage(message: unknown, at = new Date().toISOString()): CodexMessageDelivery {
    const validation = validateMessageToCodex(message);
    if (!validation.ok) throw new Error(validation.error);
    const envelope: MessageToCodex = validation.value;
    const fromThread = this.registry.requireByRole(envelope.from);
    const toThread = this.registry.requireByRole(envelope.to);
    this.bus.captureMessage(envelope, at);
    if (this.mode === "observe_only") {
      this.bus.observeMessage(envelope.message_id, toThread.threadId, at, fromThread.threadId);
    } else {
      this.bus.markRouted(envelope.message_id, toThread.threadId, at, fromThread.threadId);
    }
    return {
      deliveryId: `${envelope.message_id}:to:${toThread.threadId}`,
      mode: this.mode,
      status: this.mode === "observe_only" ? "DRY_ROUTE_RECORDED" : "MESSAGE_ROUTED",
      conversationId: envelope.conversation_id,
      messageId: envelope.message_id,
      correlationId: envelope.correlation_id,
      from: envelope.from,
      to: envelope.to,
      fromThreadId: fromThread.threadId,
      toThreadId: toThread.threadId,
      at,
    };
  }

  routeReply(reply: unknown, at = new Date().toISOString()): CodexMessageDelivery {
    const validation = validateCodexMessageReply(reply);
    if (!validation.ok) throw new Error(validation.error);
    const envelope: CodexMessageReply = validation.value;
    const fromThread = this.registry.requireByRole(envelope.from);
    const toThread = this.registry.requireByRole(envelope.to);
    if (this.mode === "observe_only") {
      this.bus.observeReply(envelope, toThread.threadId, at, fromThread.threadId);
    } else {
      this.bus.captureReply(envelope, toThread.threadId, at, fromThread.threadId);
    }
    return {
      deliveryId: `${envelope.message_id}:reply-to:${envelope.reply_to}:to:${toThread.threadId}`,
      mode: this.mode,
      status: this.mode === "observe_only" ? "DRY_REPLY_RECORDED" : "REPLY_ROUTED",
      conversationId: envelope.conversation_id,
      messageId: envelope.message_id,
      replyTo: envelope.reply_to,
      correlationId: envelope.correlation_id,
      from: envelope.from,
      to: envelope.to,
      fromThreadId: fromThread.threadId,
      toThreadId: toThread.threadId,
      at,
    };
  }
}
