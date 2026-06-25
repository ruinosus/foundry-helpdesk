"use client";

// Human-in-the-loop ticket approval.
//
// The workflow's escalate executor calls ctx.request_info(TicketApprovalRequest,
// response_type=bool), which surfaces as an AG-UI interrupt
// ({ id, value: { summary } }). useInterrupt renders the card in the chat;
// resolve(true|false) sends the boolean back to the executor's @response_handler,
// which opens the ticket only on `true`.

import { useInterrupt } from "@copilotkit/react-core/v2";

const card: React.CSSProperties = {
  border: "1px solid #2563eb33",
  borderLeft: "3px solid #2563eb",
  borderRadius: 8,
  padding: 12,
  margin: "8px 0",
  background: "#eff6ff",
  fontFamily: "system-ui",
  maxWidth: 520,
};
const btn = (bg: string): React.CSSProperties => ({
  padding: "6px 14px",
  borderRadius: 6,
  border: "none",
  background: bg,
  color: "white",
  cursor: "pointer",
  fontSize: 13,
  fontWeight: 600,
});

export function TicketApproval() {
  useInterrupt({
    agentId: "helpdesk",
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    render: (props: any) => {
      // TEMP: confirm the hook fires and inspect the payload shape.
      // eslint-disable-next-line no-console
      console.log("[TicketApproval] useInterrupt render fired:", props);
      const { interrupt, resolve } = props;
      const value = interrupt?.value ?? props?.event?.value ?? {};
      // The interrupt value may be the request data object, or a JSON string.
      let data: any = value;
      if (typeof value === "string") {
        try {
          data = JSON.parse(value);
        } catch {
          data = {};
        }
      }
      const summary =
        data.summary ?? data.data?.summary ?? data.value?.summary ?? "(see debug)";

      const respond = (approved: boolean) => resolve(approved);

      return (
        <div style={card}>
          <div style={{ fontWeight: 600, marginBottom: 6 }}>
            Open a support ticket?
          </div>
          <div style={{ fontSize: 13, marginBottom: 10 }}>
            <b>Summary:</b> {String(summary)}
          </div>
          <div style={{ display: "flex", gap: 8 }}>
            <button style={btn("#16a34a")} onClick={() => respond(true)}>
              Approve
            </button>
            <button style={btn("#dc2626")} onClick={() => respond(false)}>
              Reject
            </button>
          </div>
          <details style={{ marginTop: 8 }}>
            <summary style={{ fontSize: 11, color: "#94a3b8", cursor: "pointer" }}>
              debug: interrupt
            </summary>
            <pre style={{ fontSize: 11, overflow: "auto", maxHeight: 200 }}>
              {JSON.stringify(props, null, 2)}
            </pre>
          </details>
        </div>
      );
    },
  });

  return null;
}
