export const FIXTURE_MATCH = "http://127.0.0.1:4179/*";

export type ExtensionTarget = "production" | "test";

export type ExtensionManifest = {
  manifest_version: 3;
  name: string;
  version: string;
  description: string;
  minimum_chrome_version: string;
  action: { default_title: string };
  side_panel: { default_path: string };
  background: { service_worker: string };
  permissions: ["sidePanel"];
  host_permissions?: [typeof FIXTURE_MATCH];
  content_scripts?: [
    {
      matches: [typeof FIXTURE_MATCH];
      js: ["content.js"];
      run_at: "document_idle";
    },
  ];
};

function shell(): ExtensionManifest {
  return {
    manifest_version: 3,
    name: "wa-scribe",
    version: "0.0.1",
    description: "Setup is not implemented.",
    minimum_chrome_version: "114",
    action: { default_title: "wa-scribe" },
    side_panel: { default_path: "panel.html" },
    background: { service_worker: "background.js" },
    permissions: ["sidePanel"],
  };
}

export function createManifest(target: ExtensionTarget): ExtensionManifest {
  const manifest = shell();
  if (target === "production") return manifest;
  // The fixture origin exists only in the test build. Production cannot read that page.
  return {
    ...manifest,
    host_permissions: [FIXTURE_MATCH],
    content_scripts: [
      {
        matches: [FIXTURE_MATCH],
        js: ["content.js"],
        run_at: "document_idle",
      },
    ],
  };
}
