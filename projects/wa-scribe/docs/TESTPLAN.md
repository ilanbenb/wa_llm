# wa-scribe: proposed test plan

**Status: planned checks, not test results. Real WhatsApp not verified.** No wa-scribe tests have been implemented or executed in this repository.

The specification is [SPEC.md](SPEC.md). Drive is the first release; local-directory and destination-switch cases are acceptance criteria for the later adapter and do not block the Drive pilot. Requirements apply independently to Download and Edit unless a case explicitly distinguishes them. Every media kind and destination gets its own support status.

## Evidence layers

| Layer | Purpose | Boundary |
| --- | --- | --- |
| Pure reconciliation/storage tests | Establish ordering, ownership, file grammar, recovery, and failure behavior. | Synthetic messages and fake stores; no WhatsApp or Google access. |
| Fake-page extension tests | Exercise DOM adapters, virtualized lists, panel controls, and file outputs. | Local fixture origin only; block requests to real WhatsApp and Google. |
| Real Chrome extension harness | Prove unpacked-extension lifecycle, messaging, and browser-context behavior; directory handles are checked in the later local milestone. | Synthetic fixture and fake store; no WhatsApp account. |
| Authorized Drive integration | Prove OAuth and actual remote file behavior. | User-authorized test export; explicit cleanup of owned test files only. |
| Selector diagnostic | Report selector names, match counts, and structural failures. | User's existing tab; no navigation, scrolling, transcript/media collection, or writes. |
| Real WhatsApp pilot | Prove that the adapter contract matches real page behavior. | User-operated; 2–3 low-sensitivity chats on the existing account. |

No second WhatsApp account or automatic message sending is required. Tests must distinguish passed, failed, skipped, blocked, and unrun checks; a mocked integration does not count as a live pass.

## Multi-pass and failure sequences

The [edge-case catalog](EDGECASES.md) assigns stable IDs and expected behavior. Map every catalog ID to an automated case or explicit browser check; P0 failures block release. Single-pass fixtures do not replace these sequences:

| Sequence | Required observations |
| --- | --- |
| Three recent syncs, then older history plus an internal gap, interruption, and overlap retry; repeat in both modes. | All unseen IDs insert in verified source order; Notes/tombstones persist; no timestamp cutoff, duplicate, or falsely closed gap. |
| Source/Drive faults at different steps, then reconnect and permission/account change. | Distinct collected/saved states; no new last-success before coherent commit; no redirected or silently resumed collection. |
| Drive fail-before-apply, apply-then-response-lost, apply-late, and out-of-order callbacks. | Intended remote identity is reconciled; no blind duplicate create or stale-generation overwrite. An immediate reread does not prove a timed-out mutation stopped. |
| New arrival while backfilling; missing resume anchor; locale/date-label changes. | Captured upper boundary holds; unknown order pauses; presentation changes do not create IDs or source edits. |
| Unknown MIME, expired resource URL, missing album slot, later valid bytes, and local marker/block deletion. | Stable attachment slots; opaque-byte preservation or honest marker; no resurrection, overwrite, or duplicate message. |
| Stop/unmark/delete with a queued transfer, worker death, or schema update. | Resolve pending outcomes; stale jobs cannot recreate deleted generations; compatible recovery precedes normal sync. |

Verify text coverage and media availability independently, including a coherent partial text commit with failed/unsupported attachments. Preserve files referenced by the previous committed transcript until the new generation commits; retry cleanup separately. Do not claim multi-device exclusion from a same-profile double-click test.

## Reconciliation matrix

Run with an existing export and again with a fresh export where applicable.

| Case | Required result |
| --- | --- |
| Newer, older, and middle-of-range messages | Each unseen ID is inserted in source order; surrounding blocks are unchanged. |
| Equal displayed timestamps; identical text/sender/time | Preserve distinct message IDs and their source order. Never deduplicate by text alone. |
| Repeated pass; overlapping viewports | One committed block per message ID; no duplicate attachment. |
| Source edit | Download preserves wording; Edit replaces an unchanged generated block. |
| Download ignores edit, then Edit runs | Edit applies the current source wording despite the intervening Download observation. |
| Persistent edited badge without a new content change | No repeated rewrite solely because the badge remains. |
| Explicit delete-for-everyone | Download retains the block; Edit removes it without a placeholder. |
| Message absent from DOM/history | Neither mode treats absence as deletion. |
| Locally deleted whole block | Both modes retain its tombstone and do not restore it, including after a source edit. |
| One of two identically rendered blocks deleted locally | Ambiguous ID alignment stops the chat; no tombstone or source update is guessed. |
| Partial local edit plus source edit | Edit reports conflict; local text remains. |
| Notes present/absent | Existing Notes bytes remain exact across prepend, append, enrichment, and Edit. Absent Notes is never created. |
| Heading-like message content, multiline text, code, RTL | Golden grammar round-trips without confusing message text and document structure. |
| Malformed/ambiguous generated blocks | No rewrite; affected chat reports conflict. |

## Identity, traversal, and permissions

| Case | Required result |
| --- | --- |
| Unselected chat, including visible preview text | No captured preview, transcript, media, or sync state for that chat. |
| Duplicate display names | Verified distinct identities never merge. If source identity is unavailable, writes stop. |
| Rename, old-name reuse, slug/case/Unicode collision | Selection remains bound to identity; unrelated exports never overwrite one another. |
| WhatsApp account changes | Pause; do not apply the previous account's selection or metadata. |
| Filtered list, archived chats, virtualized rows | Scope is reported; incomplete enumeration does not claim all chats or delete missing ones. |
| Message never becomes available; budget reached | Bounded retries; partial result with coverage and stop reason. |
| Stop, tab navigation, panel close, browser exit, sleep | No false complete result; persisted state is recoverable and collection waits for another user click. |
| Worker termination/restart; two tabs; double click | One writer per export; no lost in-memory-only progress or duplicate commits. |
| Directory permission denied, revoked, or lost after restart | Pause with files/state preserved; request access again through the tested browser flow. |

## Media and storage failures

Cover image, voice, video, sticker, and document independently. Include captions, albums, two attachments in the same minute, expired object URLs, original versus thumbnail, unsupported MIME types, size/time limits, and unavailable media.

For both modes, retrying a pending attachment enriches its existing block without changing saved wording or creating a duplicate. If the user modified the pending-marker region, enrichment reports conflict instead of overwriting it. The final link appears only after bytes are saved. A removed message loses only its exclusively owned media; shared and foreign files remain.

Inject a failure after every stage of a per-chat transaction: staging media, writing the journal, replacing Markdown, replacing metadata, and cleanup. Restart and retry each case. Assert coherent committed generations, no duplicate/lost message IDs, and no successful result for unfinished work. Include disk-full, interrupted writes, Drive quota/auth failure, and external file changes detected before replacement.

Explicitly test the supported single-writer/manual-edit-between-passes contract. Do not claim cross-process atomic merging from a test that merely checks a fingerprint once.

## Metadata recovery

Run in both modes: missing file, truncated JSON, unsupported version, wrong account/destination, and interrupted generation.

Resolve a valid interrupted journal before classifying absent/mismatched metadata as unrecoverable; exercise missing-metadata mid-commit states. Otherwise, missing or invalid metadata preserves the export and pauses automatic reconciliation. The recovery preview does not guess identity. Test identical full matching tuples, a locally deleted message, a source-edited message, a sender rename, and an unmatched block whose source becomes visible later. These cases must not silently infer tombstones or safely reconstruct data that no longer exists.

Restoring a valid checkpoint resumes correctly. Starting a new export requires an explicit choice, uses a fresh noncolliding root/subtree and separate generation state, preserves the previous tree, and warns that unknown local deletions may reappear in the fresh export.

## Destination and deletion

- Switch A to B: A remains unchanged; B gets independent metadata. Switching back does not merge unrelated generations.
- Unmark: no file deletion in any destination.
- Delete export: confirmation identifies Notes and other owned content; only the selected export/destination is affected. Foreign files and earlier destinations remain.
- Interrupt deletion: report partial failure and retry only remaining owned files.

## Drive checks

Mocks verify requested scope is only `drive.file`, no credential values reach exports/logs, and writes use recorded root/file IDs. Include duplicate root names and foreign files.

Separately, an authorized integration must cover starting Connect Google Drive from the extension inside an already signed-in Chrome browser, reuse of that identity, consent/denial, shown account, raw Markdown/JSON/media create/read/update, reconnect after browser restart, token expiry/revocation, folder removal, and account change. Verify that no separate application login is required, no custom token vault is created, and no same-named folder is adopted automatically.

Download or mirror the whole export tree and resolve its relative media links locally. Do not treat Drive web-preview behavior as equivalent. Record the supported intact-tree workflow before accepting this milestone.

## User-operated WhatsApp pilot

Run only after relevant automated/browser checks pass. Use the user's existing account and 2–3 chats they are willing to export; no separate account is needed. Explain that opening chats may mark them read. The user chooses content suitable for edit/delete checks.

1. Run selector diagnostics; record counts without message text. Then separately verify account/chat/message identity and source order. Counts alone are insufficient.
2. Select the pilot chats and leave the others unselected. Connect the intended Drive account/root and choose a bounded history scope.
3. Run Download; verify correct chats, relative order, coverage report, sender/timestamp interpretation, and actual media bytes for the tested kinds. Inspect the reported stop boundary.
4. Repeat Download; verify no duplicates. Add Notes and remove one whole generated block between passes; verify preservation and the recorded tombstone.
5. The user edits one suitable source message and deletes another for everyone. Run Download and then Edit. Verify their different behavior and confirm that unrelated/unobserved messages are retained.
6. Interrupt and resume a pass; verify the reported partial/interrupted result and consistent files. Pause a chat and verify its files remain.
7. Verify the Drive tree's downloaded relative links. The later local-folder milestone repeats its own destination checks and pilot; do not generalize one destination or one media type's success to all others.

Keep a verification record containing extension revision, Chrome version/OS, WhatsApp locale, tested destination, tested media kinds, each outcome, and remaining limitations. Exclude message text, identities, and credentials from shared evidence.

Only the behaviors and destinations exercised successfully in this pilot may be labeled real-WhatsApp verified. Until then, keep the unverified status.
