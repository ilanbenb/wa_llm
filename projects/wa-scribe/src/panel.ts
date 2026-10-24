import { contentHello, invalidRequest, panelPing } from "./protocol";
import { reportExchange } from "./report";

reportExchange("#panel-pong", panelPing());
reportExchange("#panel-wrong-context", contentHello("panel-as-content"));
reportExchange("#panel-invalid", invalidRequest());
