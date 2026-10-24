import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "tests/browser",
  fullyParallel: false,
  workers: 1,
  forbidOnly: true,
  retries: 0,
  timeout: 30_000,
  webServer: {
    command: "node tests/serve-fixture.mjs",
    url: "http://127.0.0.1:4179/chat.html",
    reuseExistingServer: false,
  },
});
