export const PROTOCOL = "wa-scribe.t01";

export type PanelPing = {
  protocol: typeof PROTOCOL;
  type: "panel-ping";
  requestId: string;
};

export type ContentHello = {
  protocol: typeof PROTOCOL;
  type: "content-hello";
  requestId: string;
  fixture: "chat";
};

export type Request = PanelPing | ContentHello;

export type SenderContext = {
  extensionId: string;
  url: string;
};

export type Reply =
  | { protocol: typeof PROTOCOL; type: "panel-pong"; requestId: string; context: "panel" }
  | { protocol: typeof PROTOCOL; type: "content-ack"; requestId: string; context: "content" }
  | { protocol: typeof PROTOCOL; type: "rejected"; requestId: string; reason: "invalid-request" | "unexpected-sender" };

const MAX_REQUEST_ID = 64;

export function panelPing(requestId = "panel-ping"): PanelPing {
  return { protocol: PROTOCOL, type: "panel-ping", requestId };
}

export function contentHello(requestId = "content-hello"): ContentHello {
  return { protocol: PROTOCOL, type: "content-hello", requestId, fixture: "chat" };
}

export function invalidRequest(): { protocol: typeof PROTOCOL; type: "nope"; requestId: string } {
  return { protocol: PROTOCOL, type: "nope", requestId: "invalid" };
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function requestIdOf(message: unknown): string {
  if (!isRecord(message) || typeof message.requestId !== "string") return "";
  return message.requestId;
}

function isRequestId(value: string): boolean {
  return value.length > 0 && value.length <= MAX_REQUEST_ID;
}

function isPanelUrl(url: string, ownExtensionId: string): boolean {
  const panel = `chrome-extension://${ownExtensionId}/panel.html`;
  return url === panel || url.startsWith(`${panel}?`);
}

function isWebPage(url: string): boolean {
  return url.startsWith("http://") || url.startsWith("https://");
}

export function decide(message: unknown, sender: SenderContext, ownExtensionId: string): Reply {
  const requestId = requestIdOf(message);
  if (sender.extensionId !== ownExtensionId) {
    return { protocol: PROTOCOL, type: "rejected", requestId, reason: "unexpected-sender" };
  }
  if (!isRecord(message) || message.protocol !== PROTOCOL || !isRequestId(requestId)) {
    return { protocol: PROTOCOL, type: "rejected", requestId: isRequestId(requestId) ? requestId : "", reason: "invalid-request" };
  }
  if (message.type === "panel-ping") {
    if (!isPanelUrl(sender.url, ownExtensionId)) {
      return { protocol: PROTOCOL, type: "rejected", requestId, reason: "unexpected-sender" };
    }
    return { protocol: PROTOCOL, type: "panel-pong", requestId, context: "panel" };
  }
  if (message.type === "content-hello" && message.fixture === "chat") {
    if (!isWebPage(sender.url)) {
      return { protocol: PROTOCOL, type: "rejected", requestId, reason: "unexpected-sender" };
    }
    return { protocol: PROTOCOL, type: "content-ack", requestId, context: "content" };
  }
  return { protocol: PROTOCOL, type: "rejected", requestId, reason: "invalid-request" };
}
