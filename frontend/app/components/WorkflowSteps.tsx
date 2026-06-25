"use client";

// Live workflow steps panel, driven by the chat message store. The AG-UI
// workflow emits one activity message per executor (activityType "executor",
// content { executor_id, status: in_progress|completed }); we read them from
// useCopilotChat and light up triage -> retrieve -> resolve as they arrive.
//
// Defensive about the exact message shape (preview SDK) — unknown shapes just
// leave the steps idle rather than crashing.

import { useCopilotChat } from "@copilotkit/react-core";
import { useMemo } from "react";

const STEPS = [
  { id: "triage", label: "Triage", desc: "Classify intent & urgency" },
  { id: "retrieve", label: "Retrieve", desc: "Search the runbook knowledge base" },
  { id: "resolve", label: "Resolve", desc: "Write the grounded, cited answer" },
] as const;

type StepState = "idle" | "active" | "done" | "pending";

const DOT: Record<StepState, string> = {
  idle: "#cbd5e1",
  pending: "#cbd5e1",
  active: "#2563eb",
  done: "#16a34a",
};

export function WorkflowSteps() {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const chat = useCopilotChat() as any;

  const status = useMemo<Record<string, string>>(() => {
    const messages: unknown[] =
      chat?.messages ?? chat?.visibleMessages ?? [];
    const acc: Record<string, string> = {};
    for (const raw of messages) {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const m = raw as any;
      const activityType = m?.activityType ?? m?.payload?.activityType;
      const content = m?.content ?? m?.payload?.content;
      if (activityType === "executor" && content?.executor_id) {
        acc[content.executor_id] = content.status;
      }
    }
    return acc;
  }, [chat?.messages, chat?.visibleMessages]);

  const hasAny = Object.keys(status).length > 0;

  // TEMP debug: reveal what useCopilotChat actually exposes so we can wire the
  // activity detection to the real shape. Remove once the steps light up.
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const dbgMsgs: any[] = chat?.messages ?? chat?.visibleMessages ?? [];
  const debug = {
    chatKeys: chat ? Object.keys(chat) : null,
    messagesLen: dbgMsgs.length,
    detectedStatus: status,
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    lastMessages: dbgMsgs.slice(-8).map((m: any) => ({
      keys: Object.keys(m ?? {}),
      role: m?.role,
      type: m?.type,
      activityType: m?.activityType,
      executor_id: m?.content?.executor_id,
      status: m?.content?.status,
    })),
  };

  function stateFor(id: string): StepState {
    const s = status[id];
    if (s === "completed") return "done";
    if (s === "in_progress") return "active";
    return hasAny ? "pending" : "idle";
  }

  return (
    <section
      style={{
        borderBottom: "1px solid #e5e7eb",
        padding: "12px 24px",
        fontFamily: "system-ui",
      }}
    >
      <div style={{ fontSize: 12, color: "#64748b", marginBottom: 8 }}>
        Workflow {hasAny ? "" : "· idle"}
      </div>
      <ol
        style={{
          display: "flex",
          gap: 8,
          listStyle: "none",
          margin: 0,
          padding: 0,
          flexWrap: "wrap",
        }}
      >
        {STEPS.map((s) => {
          const st = stateFor(s.id);
          return (
            <li
              key={s.id}
              style={{
                display: "flex",
                alignItems: "center",
                gap: 8,
                padding: "6px 10px",
                border: `1px solid ${st === "active" ? DOT.active : "#e5e7eb"}`,
                borderRadius: 8,
                background:
                  st === "active" ? "#eff6ff" : st === "done" ? "#f0fdf4" : "transparent",
                opacity: st === "pending" || st === "idle" ? 0.6 : 1,
              }}
            >
              <span aria-hidden style={{ fontSize: 13, color: DOT[st] }}>
                {st === "done" ? "✓" : "●"}
              </span>
              <span style={{ fontSize: 13, fontWeight: 600 }}>{s.label}</span>
              <span style={{ fontSize: 12, color: "#94a3b8" }}>{s.desc}</span>
            </li>
          );
        })}
      </ol>

      <details style={{ marginTop: 10 }}>
        <summary style={{ fontSize: 11, color: "#94a3b8", cursor: "pointer" }}>
          debug: chat shape
        </summary>
        <pre
          style={{
            fontSize: 11,
            background: "#0f172a",
            color: "#e2e8f0",
            padding: 10,
            borderRadius: 8,
            overflow: "auto",
            maxHeight: 280,
          }}
        >
          {JSON.stringify(debug, null, 2)}
        </pre>
      </details>
    </section>
  );
}
