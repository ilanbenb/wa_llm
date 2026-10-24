import { contentHello, panelPing } from "./protocol";
import { reportExchange } from "./report";

function replyDelay(): number {
  const delay = Number(new URLSearchParams(location.search).get("replyDelay"));
  if (!Number.isFinite(delay) || delay <= 0) return 0;
  return Math.min(delay, 5_000);
}

function report(): void {
  reportExchange("#content-ack", contentHello());
  reportExchange("#content-wrong-context", panelPing("content-as-panel"));
}

const delay = replyDelay();
if (delay === 0) report();
else setTimeout(report, delay);
