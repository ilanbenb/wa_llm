# wa-scribe development plan

Planning baseline: [SPEC.md](SPEC.md), with Google Drive first and Google connection initiated from the user's existing signed-in Chrome browser. Local-folder export follows later. This is a plan, not an implementation or a claim that tests have passed.

## First result and release boundary

The first demonstration is: open the extension, connect Drive, select one chat, click Download, and inspect a Markdown transcript and metadata in the designated Drive tree. Repeat the pass and see no duplicate messages.

That demonstration is an internal alpha. V1 also requires Edit mode, Notes/local-deletion preservation, recoverable writes, media, bounded history/progress, pause/delete controls, and the real pilot. A failed required capability is a blocker or an explicit scope decision, not a silently dropped feature.

## Proposed tools and boundaries

Use `projects/wa-scribe/` inside the `wa_llm` repository for the package manifest, lockfile, source, and tests. Run project commands from that directory; keep the Python bot's configuration independent. Use TypeScript, Manifest V3, Vite for build output, Vitest for pure tests, and Playwright for browser tests in a persistent Chromium context. Start with a small side-panel UI; no backend or database is needed. The dedicated GitHub Actions workflow belongs at the shared Git root in `.github/workflows/wa-scribe.yml`, with project path filters and working directories.

Keep five boundaries: WhatsApp page adapter; pure message/file reconciliation; recoverable export storage; Drive authorization/API adapter; panel and job coordinator. The core consumes normalized observations rather than reading the DOM or calling Drive. Choose the long-running job context after testing extension lifecycle behavior; persistent state must survive service-worker termination.

This environment has Node, npm, and a Chromium binary. The extension build and browser harness still need to be installed and verified. Existing Python tests do not validate wa-scribe.

## Milestones and acceptance gates

### M0 — Scaffold and establish the test harness

Deliver an unpacked extension with a side panel, a synthetic fixture page, normalized observation/storage interfaces, and separate automatic versus live-test entry points. Define the reversible Markdown grammar, metadata version, and golden file examples before real scraper integration.

Automatic checks: build/type-check, load the extension in Chromium, exchange a panel/content-script message, and render/parse synthetic message blocks without losing text. Include multiline/RTL text and content resembling document headings. Fixture tests block Google and WhatsApp network requests.

Gate: the extension loads, the harness demonstrably exercises it, and checks run from a clean install using the committed lockfile.

### M1 — Prove browser and Drive capabilities

Deliver two small probes, not a full exporter:

- Drive: Connect from the extension in signed-in Chrome, show the connected account, obtain `drive.file` consent when needed, and create/read/update synthetic raw Markdown, JSON, and media in an isolated owned test subtree. Restart the browser and test reconnect/permission failure. Verify an intact-tree download and relative media link.
- WhatsApp: first provide the non-collecting selector diagnostic. Then, after its fixture checks pass, the user explicitly runs a bounded capability probe on one chosen low-sensitivity chat. Establish stable account/chat/message identity, ordering, timestamp interpretation, source edit/delete evidence, and original media access. Keep the probe separate from the selector diagnostic, which must not collect messages or scroll.

Record minimum Chrome version, tested locale, observable history boundaries, execution context, and initial history/media budgets. Determine the actual media access path before adding permissions.

Gate: both probes have actual browser evidence. Prove the chosen Drive operation-identity and conditional/version behavior for timeout-after-acceptance and stale late writes; do not assume a client timeout undoes a remote mutation. If identity, required media, or necessary write protection is unavailable, stop the dependent feature and resolve the limitation before building around an assumption. Pure core work can continue independently.

### M2 — Build the reconciliation core

Deliver pure functions that turn observed source messages plus existing files/state into a proposed set of changes. Finish this before applying source-driven replacements or deletions to a live export.

Automatic checks cover:

- Append, prepend, middle insertion, equal timestamps, repeated passes, and overlapping history windows.
- Download versus Edit, including Download ignoring an edit followed by Edit applying it.
- Exact Notes-byte preservation, local whole-block deletions, and local/source edit conflicts.
- Identical rendered blocks that cannot be aligned safely, missing/corrupt metadata, and recovery choices.
- Multiple successful passes followed by older and middle-gap history, missing anchors, and retained coverage gaps; use the [edge-case sequences](EDGECASES.md).

Gate: each Download/Edit rule has an explicit expected-file test; ambiguity leaves existing files untouched. Pure tests do not need the user's accounts.

### M3 — Complete one-chat Download to Drive

Deliver the first end-to-end alpha: explicit selection, bounded text collection, normalized source observations, Markdown/metadata, Drive commit, progress, and result. Include persistent single-writer coordination and the basic transaction journal now, before repeated live writes.

Automatic checks drive the real extension against the fake page and mocked Drive. Cover virtualization, overlapping rows, unselected chats, renamed/duplicate names, Stop, and two simultaneous starts. Inject a failure between transcript and metadata writes and prove a retry recovers without duplicates.

Manual gate: on a chosen pilot chat, Download to Drive, inspect its files, and repeat. Confirm the correct account/chat, ordering, no duplicates, accurate coverage, and no unselected export. Keep the build labeled alpha; a successful text pass does not verify other capabilities.

### M4 — Finish Edit, media, and failure handling

Deliver Edit mode; source/local conflict handling; attachment save/retry/enrichment; multi-chat results; pause; explicit delete; and complete recovery controls.

Automatic checks run the full [test matrix](TESTPLAN.md) and catalog P0 sequences. Inject failure at every transaction boundary, including apply-then-response-lost and apply-late, plus Drive quota/auth errors, cancellation, worker termination, tab closure/navigation, changed destination content, and damaged state. Simulate interruption first in repeatable browser tests; retain physical browser/sleep checks in the manual checklist. Test bounded browser staging and cleanup after a coherent commit separately from collection and saved counts.

Test image, voice, video, sticker, and document independently, including captions, original-versus-thumbnail, collisions, missing bytes, and size/time limits. None is considered supported from an image-only demonstration. Complete controls and formatting without expanding into agents, summaries, or sending messages.

Gate: automated checks pass, retries preserve coherent generations, and failed/partial operations do not show a successful result. Each required media type has capability evidence or a recorded unresolved blocker.

### M5 — Pilot and release candidate

Produce a reproducible extension ZIP, loading instructions, OAuth setup instructions, and a short user checklist. The user runs the pilot on 2–3 chosen chats using their normal Chrome and Drive account; no second WhatsApp account is needed.

Verify Download, repeat Download, source edit/delete followed by both modes, Notes, local deletion, media, interruption/retry, pause, and the downloaded Drive tree. Use content the user chooses for destructive source checks; the extension never sends messages automatically.

Gate: record extension revision, browser/OS, locale, tested media, actual outcomes, and limitations without putting chat content or credentials in shared logs. Only exercised behavior becomes real-WhatsApp verified. Public Chrome Web Store distribution and any additional Google publishing requirements are a separate delivery step; the pilot uses the unpacked build.

## Testing on every change

| Suite | Runs where | When |
| --- | --- | --- |
| Type-check, unit/golden-file and fake-store recovery tests | Cloud/CI | Every relevant change and pull request. |
| Extension plus virtualized fake-page tests | Cloud/CI Chromium | Every adapter/UI/storage change and pull request. |
| Authorized Drive smoke | User's Chrome/test subtree | First integration, then OAuth/storage changes and release candidates. |
| WhatsApp selector/capability checks | User's selected tab | First adapter validation and relevant page/adapter changes. |
| Full real pilot | User's Chrome and selected chats | First release candidate and changes affecting verified behavior. |

Proposed package commands are `npm run typecheck`, `npm run test:unit`, `npm run test:browser`, and `npm run build`. These must be added in M0; they do not exist yet. CI uses `npm ci` and never requires a real WhatsApp session or Google token. Live suites remain explicit opt-in actions.

## What requires the user's browser

Chrome sign-in supplies an identity, but Drive access still requires OAuth application configuration and consent. Before the Drive probe, configure a Google Cloud project with Drive API enabled, the appropriate consent/test-user setup, and a Chrome-extension OAuth client tied to a stable development extension ID. The client ID is configuration, not a password; no client secret or account password belongs in the extension.

The development team can prepare the manifest and exact setup guide. The account owner handles any console access unavailable to the team, approves the browser's Google consent, and runs the selected-chat probes/pilot. Passwords, tokens, and WhatsApp session files are never requested in chat. Cloud automation does not assume access to that signed-in browser.

## Parallel work and immediate sequence

After M0 defines the interfaces, Drive/auth, synthetic WhatsApp fixtures, and pure reconciliation can proceed in parallel. Agree the file grammar and store contract first; do not let separate streams invent incompatible formats. Recoverable storage can be developed against a fake store while Drive authorization is being configured.

Start with M0, then the M1 probes and M2 core in parallel. M3 depends on their relevant gates. Finish M4 before the M5 release pilot. Estimate the remaining work after M1 reveals identity/media accessibility and actual browser/Drive behavior; do not promise a release date from fixture tests alone.
