import { describe, expect, it } from "vitest";
import { FIXTURE_MATCH, createManifest } from "../src/manifest";

describe("createManifest", () => {
  it("keeps fixture access out of the production manifest", () => {
    const manifest = createManifest("production");
    const text = JSON.stringify(manifest);
    expect(manifest.permissions).toEqual(["sidePanel"]);
    expect(manifest.host_permissions).toBeUndefined();
    expect(manifest.content_scripts).toBeUndefined();
    expect(text).not.toContain("127.0.0.1");
    expect(text).not.toContain("web.whatsapp.com");
    expect(text).not.toContain("googleapis");
    expect(text).not.toContain("oauth");
    expect("oauth2" in manifest).toBe(false);
  });

  it("adds only the fixture origin to the test manifest", () => {
    const manifest = createManifest("test");
    expect(manifest.permissions).toEqual(["sidePanel"]);
    expect(manifest.host_permissions).toEqual([FIXTURE_MATCH]);
    expect(manifest.content_scripts).toEqual([
      { matches: [FIXTURE_MATCH], js: ["content.js"], run_at: "document_idle" },
    ]);
  });
});
