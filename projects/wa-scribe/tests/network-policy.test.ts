import { describe, expect, it } from "vitest";
import { isAllowedTestRequest } from "./network-policy";

describe("isAllowedTestRequest", () => {
  it("allows the fixture origin and this extension's resources", () => {
    expect(isAllowedTestRequest("http://127.0.0.1:4179")).toBe(true);
    expect(isAllowedTestRequest("http://127.0.0.1:4179/")).toBe(true);
    expect(isAllowedTestRequest("http://127.0.0.1:4179/chat.html")).toBe(true);
    expect(isAllowedTestRequest("http://127.0.0.1:4179/chat.html?replyDelay=800")).toBe(true);
    expect(isAllowedTestRequest("chrome-extension://abcdefghijklmnop/panel.html")).toBe(true);
    expect(isAllowedTestRequest("chrome-extension://abcdefghijklmnop/background.js")).toBe(true);
  });

  it("blocks other destinations, including Drive file URLs", () => {
    expect(isAllowedTestRequest("https://drive.google.com/file/example")).toBe(false);
    expect(isAllowedTestRequest("https://drive.google.com/file/d/abc/view")).toBe(false);
    expect(isAllowedTestRequest("https://web.whatsapp.com/")).toBe(false);
    expect(isAllowedTestRequest("https://www.googleapis.com/drive/v3/files")).toBe(false);
    expect(isAllowedTestRequest("https://accounts.google.com/o/oauth2/v2/auth")).toBe(false);
    expect(isAllowedTestRequest("https://google.com/drive")).toBe(false);
    expect(isAllowedTestRequest("http://127.0.0.1:4179.evil.example/chat.html")).toBe(false);
    expect(isAllowedTestRequest("https://evil.example/?next=http://127.0.0.1:4179/")).toBe(false);
  });
});
