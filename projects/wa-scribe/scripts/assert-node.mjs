const required = "24.22.0";

if (process.versions.node !== required) {
  console.error(`wa-scribe requires Node ${required}, got ${process.versions.node}`);
  process.exit(1);
}
