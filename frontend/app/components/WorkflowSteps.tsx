"use client";

// Live view of the multi-agent workflow. Driven by useCoAgent's `running` +
// `nodeName` (the current executor the AG-UI workflow is on). As the backend
// runs triage -> retrieve -> resolve, nodeName advances and the steps light up.
//
// This is the Phase 2 green signal: the 3 steps appear as they execute, not just
// the final answer. (Even if nodeName lags, the per-step outputs still stream
// into the chat below.)

import { useCoAgent } from "@copilotkit/react-core";
import { useEffect, useState } from "react";

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
  const { running, nodeName } = useCoAgent({ name: "helpdesk" });
  const [hasRun, setHasRun] = useState(false);

  useEffect(() => {
    if (running) setHasRun(true);
  }, [running]);

  const activeIdx = STEPS.findIndex((s) => s.id === nodeName);

  function stateFor(i: number): StepState {
    if (running) {
      if (activeIdx < 0) return i === 0 ? "active" : "pending"; // running, node unknown yet
      if (i < activeIdx) return "done";
      if (i === activeIdx) return "active";
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
    </section>
  );
}
