// CopilotKit runtime route — bridges the browser to the backend AG-UI endpoint.
//
// API verified against @copilotkit/runtime 1.61.2 and @ag-ui/client 0.0.57:
//   - HttpAgent lives in @ag-ui/client (extends AbstractAgent).
//   - CopilotRuntime takes agents: Record<string, AbstractAgent>.
//   - copilotRuntimeNextJSAppRouterEndpoint({ runtime, serviceAdapter, endpoint })
//     returns { handleRequest }. AG-UI agents need no LLM adapter here, so we use
//     the ExperimentalEmptyAdapter (the model runs server-side in Foundry).

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
