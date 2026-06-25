// CopilotKit runtime route — bridges the browser to the backend AG-UI endpoint.
//
// The CopilotKit runtime already forwards the Authorization header that the
// CopilotKitProvider sends, so we must NOT set it again on the HttpAgent —
// doing so produced a duplicated "Bearer x, Bearer x" header that failed JWT
// parsing on the backend.

import {
  CopilotRuntime,
  ExperimentalEmptyAdapter,
  copilotRuntimeNextJSAppRouterEndpoint,
} from "@copilotkit/runtime";
import { HttpAgent } from "@ag-ui/client";
import { NextRequest } from "next/server";

const AGUI_URL = process.env.AGUI_URL ?? "http://localhost:8000/helpdesk";

const runtime = new CopilotRuntime({
  agents: {
    helpdesk: new HttpAgent({ url: AGUI_URL }),
  },
});

export const POST = async (req: NextRequest) => {
  const { handleRequest } = copilotRuntimeNextJSAppRouterEndpoint({
    runtime,
    serviceAdapter: new ExperimentalEmptyAdapter(),
    endpoint: "/api/copilotkit",
  });
  return handleRequest(req);
};
