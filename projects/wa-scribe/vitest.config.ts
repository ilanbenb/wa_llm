import { defineConfig } from "vitest/config";

export default defineConfig({
  test: {
    passWithNoTests: false,
    include: ["tests/**/*.test.ts"],
  },
});
