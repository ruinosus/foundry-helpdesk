"use client";

// Live view of the multi-agent workflow. Driven by useCoAgent's `running`,
// `nodeName` (current executor) and `state` (accumulated workflow state).
//
// We persist every executor we've seen active so the steps accumulate
// triage -> retrieve -> resolve even when transitions are fast. The collapsible
// "debug" dump shows the raw coagent state so we can wire richer per-step
// rendering to whatever the backend actually emits.

import { useCoAgent } from "@copilotkit/react-core";
import { useEffect, useRef, useState } from "react";

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
  const { running, nodeName, state } = useCoAgent({ name: "helpdesk" });
  const [hasRun, setHasRun] = useState(false);
  const [seen, setSeen] = useState<string[]>([]);
  const seenRef = useRef<Set<string>>(new Set());

  useEffect(() => {
    if (running) setHasRun(true);
    // reset the per-run progress when a new run starts
    if (running && nodeName === STEPS[0].id) {
      seenRef.current = new Set();
      setSeen([]);
    }
  }, [running, nodeName]);

  useEffect(() => {
    if (running && nodeName && !seenRef.current.has(nodeName)) {
      seenRef.current.add(nodeName);
      setSeen(Array.from(seenRef.current));
    }
  }, [running, nodeName]);

  const activeIdx = STEPS.findIndex((s) => s.id === nodeName);

  function stateFor(i: number): StepState {
    const id = STEPS[i].id;
    if (running) {
      if (i === activeIdx) return "active";
      if (seen.includes(id)) return "done";
      if (activeIdx >= 0 && i < activeIdx) return "done";
      return "pending";
    }
    return hasRun ? "done" : "idle";
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
        Workflow {running ? "· running…" : hasRun ? "· done" : "· idle"}
        {nodeName ? ` · node: ${nodeName}` : ""}
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
        {STEPS.map((s, i) => {
          const st = stateFor(i);
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
                background: st === "active" ? "#eff6ff" : "transparent",
                opacity: st === "pending" || st === "idle" ? 0.6 : 1,
              }}
            >
              <span
                style={{
                  width: 8,
                  height: 8,
                  borderRadius: "50%",
                  background: DOT[st],
                  boxShadow: st === "active" ? `0 0 0 3px ${DOT.active}33` : "none",
                }}
              />
              <span style={{ fontSize: 13, fontWeight: 600 }}>{s.label}</span>
              <span style={{ fontSize: 12, color: "#94a3b8" }}>{s.desc}</span>
            </li>
          );
        })}
      </ol>

      {/* Temporary: shows the raw coagent state so we can wire per-step content. */}
      <details style={{ marginTop: 10 }}>
        <summary style={{ fontSize: 11, color: "#94a3b8", cursor: "pointer" }}>
          debug: coagent state
        </summary>
        <pre
          style={{
            fontSize: 11,
            background: "#0f172a",
            color: "#e2e8f0",
            padding: 10,
            borderRadius: 8,
            overflow: "auto",
            maxHeight: 240,
          }}
        >
          {JSON.stringify({ nodeName, running, seen, state }, null, 2)}
        </pre>
      </details>
    </section>
  );
}
