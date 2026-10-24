import { describe, expect, it } from "vitest";
import { PROTOCOL, contentHello, decide, invalidRequest, panelPing } from "../src/protocol";

const own = "extension-id";
const panelSender = { extensionId: own, url: `chrome-extension://${own}/panel.html` };
const contentSender = { extensionId: own, url: "http://127.0.0.1:4179/chat.html" };

describe("decide", () => {
  it("accepts a panel ping only from an extension page", () => {
    expect(decide(panelPing(), panelSender, own)).toEqual({
      protocol: PROTOCOL,
      type: "panel-pong",
      requestId: "panel-ping",
      context: "panel",
    });
    expect(decide(panelPing("content-as-panel"), contentSender, own)).toEqual({
      protocol: PROTOCOL,
      type: "rejected",
      requestId: "content-as-panel",
      reason: "unexpected-sender",
    });
  });

  it("accepts a fixture hello only from a content-script tab", () => {
    expect(decide(contentHello(), contentSender, own)).toEqual({
      protocol: PROTOCOL,
      type: "content-ack",
      requestId: "content-hello",
      context: "content",
    });
    expect(decide(contentHello("panel-as-content"), panelSender, own)).toEqual({
      protocol: PROTOCOL,
      type: "rejected",
      requestId: "panel-as-content",
      reason: "unexpected-sender",
    });
  });

  it("rejects a malformed request and a foreign extension id", () => {
    expect(decide(invalidRequest(), panelSender, own)).toEqual({
      protocol: PROTOCOL,
      type: "rejected",
      requestId: "invalid",
      reason: "invalid-request",
    });
    expect(decide(null, panelSender, own)).toMatchObject({ reason: "invalid-request" });
    expect(decide(["panel-ping"], panelSender, own)).toMatchObject({ reason: "invalid-request" });
    expect(decide({ ...panelPing(), requestId: "" }, panelSender, own)).toMatchObject({
      reason: "invalid-request",
    });
    expect(
      decide(
        { protocol: PROTOCOL, type: "content-hello", requestId: "content-hello", fixture: "other" },
        contentSender,
        own,
      ),
    ).toMatchObject({ reason: "invalid-request" });
    expect(decide(panelPing(), { extensionId: "other", url: panelSender.url }, own)).toMatchObject({
      reason: "unexpected-sender",
    });
  });
});
