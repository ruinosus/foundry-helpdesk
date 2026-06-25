"use client";

// Phase 0: minimal chat that round-trips through the AG-UI agent.
// The `agent="helpdesk"` prop selects the agent registered in the runtime route.
// Generative UI for workflow steps / approval cards arrives in later phases.

import { CopilotKit } from "@copilotkit/react-core";
import { CopilotChat } from "@copilotkit/react-ui";

export default function Page() {
  return (
    <CopilotKit runtimeUrl="/api/copilotkit" agent="helpdesk">
      <main
        style={{
          height: "100vh",
          display: "flex",
          flexDirection: "column",
          maxWidth: 768,
          margin: "0 auto",
        }}
      >
        <h1 style={{ padding: "16px 24px", fontFamily: "system-ui" }}>
          Helpdesk Concierge
        </h1>
        <div style={{ flex: 1, minHeight: 0 }} className="copilotkit-chat-host">
          <CopilotChat
            labels={{
              title: "Helpdesk Concierge",
              initial: "Hi! Ask me an engineering support question.",
            }}
          />
        </div>
      </main>
    </CopilotKit>
  );
}
