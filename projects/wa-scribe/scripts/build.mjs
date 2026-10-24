import { build } from "vite";

const mode = process.argv[2];
if (mode !== "production" && mode !== "test") {
  console.error("usage: node scripts/build.mjs production|test");
  process.exit(1);
}

for (const entry of ["background", "content", "panel"]) {
  process.env.WA_ENTRY = entry;
  await build({ mode, configFile: "vite.config.ts" });
}
