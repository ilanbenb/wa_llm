# wa-scribe: proposed v1 specification

**Status: review draft; real WhatsApp not verified.** No extension implementation or automated test results are claimed. Behavior that changes the supplied draft is listed in [REVIEW.md](REVIEW.md).

## 1. Outcome and scope

From Chrome, the user selects WhatsApp Web chats and explicitly starts an export to Google Drive. Each chat produces a UTF-8 Markdown transcript, delivered attachments, and synchronization metadata. Drive is the first working release. A local-directory destination is a later milestone and does not block Drive acceptance; its requirements are included to keep the file contract portable.

There is no backend logged into WhatsApp, background scheduled sync, message-send control, model call, transcription, or agent-access configuration. The existing Python bot is a separate application and is not a dependency.

The browser uses the user's WhatsApp session. Opening chats during collection may mark them read and trigger ordinary read receipts. Closing or navigating the tab, browser shutdown, sleep, and extension-context termination can interrupt a pass.

## 2. Selection and identity

Nothing is selected initially. Mark all is explicit. Optional labels organize the panel and confer no access rights. The panel shows the chat name, selection, last successful commit, and last-pass result; it does not capture or display previews from unselected chats.

Selection binds to the WhatsApp account and a stable conversation identifier verified by the page adapter. A persistent generated `chat_key` identifies its exported files. The display name is not a unique key. Renaming a chat updates its displayed title without associating another chat with its export or moving existing paths automatically. Account changes pause sync until the selection and destination are reviewed.

Reliable source identity is a feasibility gate, not an assumed DOM capability. If it cannot be established, the extension must stop affected writes. A name-bound fallback would require a separately agreed limitation: ambiguous names, renames, and name reuse cannot be followed automatically.

Chat-list traversal must report its scope, including filters and archived chats. A filtered or incomplete list is labeled partial. A chat disappearing from the list does not unselect it or delete its export.

**Proposed change:** Unmarking stops future sync and keeps existing files. Deletion is a separate explicit action described in section 9.

## 3. Destination

All selected chats use one active destination. The initial release exposes Drive only. When local-directory support is added, switching changes future writes and leaves prior destinations untouched. State is scoped to account, chat, destination, and export generation. The extension never assumes an export exists in a new destination because it existed elsewhere, and never moves or deletes previous copies automatically.

For the later local-directory milestone, the user grants write access through a directory picker. Retain its handle where supported; request permission again when necessary. Lost permission pauses sync without choosing a replacement directory.

For Drive, the user clicks Connect Google Drive in the extension while using their already signed-in Chrome browser. Start Chrome's identity flow from that action and reuse the profile's Google identity where available. Google may show a consent screen for the requested Drive permission; this does not require a separate application login. Show the connected account before export and on the panel thereafter. Handle missing accounts, denied consent, expiry, revocation, and account changes. Use the platform token cache; do not create a custom password or refresh-token store or write credentials to exported files.

Request only the Drive `drive.file` scope. Create an export root named `WhatsApp Desk`, record its Drive ID, and enforce writes to the recorded export tree and owned file IDs. Folder names are not unique, and the scope alone does not enforce this tree boundary. A missing root or revoked access pauses sync; it must not silently adopt a same-named folder.

Drive files remain raw Markdown, JSON, and media; never convert transcripts to Google Docs. Relative links are intended to work when the directory tree is downloaded or mirrored intact. They are not promised to resolve in Drive's web viewer. The Drive milestone must document how users obtain that intact tree. Export content is readable by people and tools with access to the destination; labels do not restrict access.

## 4. File contract

Example:

```text
WhatsApp Desk/
  chats/class-3a-parents--c7a18d2f.md
  media/c7a18d2f/m91b2-01.jpg
  media/c7a18d2f/m94d8-01.ogg
  sync/c7a18d2f.json
```

Readable names use deterministic filename normalization plus a collision-resistant storage-key suffix. Handle Unicode, case-insensitive filesystems, reserved names, and path separators. Media keys include the message identity and attachment index, never just a timestamp. Detect a storage-key collision rather than overwriting another file.

Metadata has a format version and records source/destination identity, message IDs and source order, source-content baselines, committed block fingerprints, local-deletion tombstones, attachment status/paths, coverage, and commit generation. Coverage records observed segments and stable boundary anchors, unresolved gaps, requested scope, and stop reasons; an oldest/newest timestamp pair is insufficient. Message IDs remain outside the prose.

Before scraper integration, the format-contract ticket must publish a reversible Markdown block grammar and golden examples. It must distinguish structural boundaries from message text containing headings, sender-looking headers, Markdown, or code. Arbitrary message text must round-trip without becoming file structure.

The extension does not create `## Notes`. When the user adds Notes above the top-level `## Transcript`, preserve its original UTF-8 bytes, including blank lines. Keep user content outside recognized generated blocks unchanged. If the parser cannot establish boundaries or align blocks to metadata unambiguously, stop that chat before writing.

Store sender identity when observed separately from its display name. Preserve the timestamp's precision and timezone information when available; do not invent seconds, an offset, or UTC certainty from a minute-only/localized display. Chronology uses verified source order, not the rendered timestamp string.

## 5. One sync pass

The user chooses Download or Edit mode and a history scope before starting. The panel explains that Edit mode can remove saved content. Freeze mode, source/destination identities, and an upper message anchor for the pass. Newly arriving messages beyond that anchor wait for the next pass. Newly selected chats, mode changes, and destination changes take effect next pass; unmarking/Stop cancels new collection and retries for the affected chat at a safe boundary. Resolve in-flight write outcomes before final status or explicit export deletion.

Before writes, verify the source account/chat, destination access, export format, and any interrupted transaction. Revalidate account/chat identity for every observation batch. Permit one active writer per export within the Chrome profile; reject duplicate starts and conflicting tabs. V1 supports one owning profile/device per export; other profiles use separate roots. Cross-device exclusion is not established by a local lock.

The history scope has explicit date/message limits or an explicit all-available choice. All-available is best effort with bounded work, not a promise that WhatsApp exposes everything. Concrete duration/message budgets must be chosen after measuring the browser prototype and recorded before v1 acceptance; they cannot remain implicit. Show the inspected interval, stop reason, message/media counts, and a Stop action.

Collect from the verified conversation, deduplicate by stable message ID, and insert unseen messages in source order. This covers older history, newer arrivals, gaps inside the saved range, overlapping viewports, and equal timestamps. Without reliable ordering, stop rather than guess.

Last-commit time and the newest saved timestamp are never discard cutoffs for unseen IDs. After multiple syncs, newly revealed older or middle-of-range history still inserts at its verified position. A successful recent-history pass does not clear earlier gaps. Resume uses verified surviving anchors/overlap; if segments cannot be ordered, preserve committed data and report the unresolved segment. Source presentation changes such as locale/DST alone are not source-content edits.

History and media loading have bounded retries. Unknown history boundaries, timeout, unloaded content, interrupted browsing, or reaching a budget produce a partial/interrupted result. They never imply a complete archive. Apply source edits/deletions only to positively observed messages; absence from a virtualized window is not deletion.

Persist progress and commit generations; do not rely on an indefinitely running Manifest V3 service worker or volatile global state. Interrupted work may be inspected at startup, but collecting more WhatsApp content requires another user click.

Per-chat results are `complete for requested scope`, `partial`, `interrupted`, `needs permission`, `conflict`, `recovery required`, or `failed`. Track attempt time separately from the last successful commit. Partial commits report their exact coverage; one failed chat does not turn other pending chats into successes.

Distinguish source disconnection from destination unavailability: the former freezes collection/coverage, while the latter leaves a pending save. A captured coherent subset may commit as partial; collected bytes alone do not advance last-success. Show collection, saved, and attachment-availability counts separately. Source collection after interruption requires a user resume action. Retry only classified transient failures with bounded backoff/jitter and applicable Retry-After; permission/quota/unsupported cases need their own action rather than endless retry.

## 6. Reconciliation

| Observed situation | Download | Edit |
| --- | --- | --- |
| Unseen message ID | Insert at its source position. | Same. |
| Saved source message has changed | Preserve stored wording. | Replace stored wording if the generated block is locally unchanged. |
| Positive delete-for-everyone marker for a known ID | Preserve stored block. | Remove that generated block without a deletion placeholder. |
| Message absent from inspected history | No change. | No change. |
| Entire generated block was removed locally | Record/retain its tombstone; do not recreate it. | Same, including after a later source edit. |
| User partially changed a generated block | Preserve it. Stop if alignment becomes ambiguous. | If source reconciliation would overwrite it, report a conflict and preserve it. |
| Previously unavailable attachment now delivered | Save it and replace its pending marker/link if that region is locally unchanged; otherwise report conflict. Preserve saved wording. | Same. |

A source edit means observed content changed from the recorded source baseline; a persistent edited badge alone is insufficient. After Download ignores an edit, record that the stored block still differs so a later Edit pass can apply the current observed wording.

Local deletion support means deletion of an entire generated message block. It does not mean arbitrary deletion of a paragraph within a multi-paragraph message. Such changes are local edits. Tombstones can be cleared only through an explicit restore action. Preserve Notes in both modes.

If two blocks have identical rendered content and a local change makes their alignment to message IDs ambiguous, stop that chat without assigning a guessed tombstone or applying a guessed source update.

Edit removes earlier wording from the active transcript; it does not keep an application revision log. WhatsApp may no longer contain that wording either. Drive version history, trash, external backups, and old destination copies are outside any erasure guarantee.

## 7. Attachments

Save only attachment bytes that WhatsApp Web actually delivers during the pass. Preserve captions and attachment order. Never report a thumbnail as a successfully saved original. Keep distinctions between pending, unavailable, unsupported, and failed attachments; record a concise visible placeholder and retry status.

Images, voice notes, video, stickers, and documents each require capability evidence before being marked supported. No voice transcription or image description is generated. Record MIME type and an appropriate extension, and ensure attachment paths stay inside the export.

A recognized message can contain an unknown attachment format. If verified original bytes are delivered, preserve them as an opaque file with a safe extension such as `.bin`, retaining observed type/name information in metadata. Otherwise retain an explicit unavailable/unsupported marker and continue independent content. An unrecognized message envelope with no reliable identity/order instead creates a reported coverage gap. Unsupported formats do not trigger endless retries.

Stage and verify bytes before publishing a successful link. Bounded size/time limits must be established by the capability milestone; exceeded limits become explicit partial results. Retry does not create a second message or overwrite a different attachment. Attachment enrichment is the stated exception to Download's wording-preservation rule.

Validate available length/type/checksum evidence; a thumbnail, truncated response, or error page is not an original, and a self-computed hash alone does not establish completeness. Attachment identity uses message/slot/revision rather than an expiring URL. Do not persist temporary signed URLs in exports/logs. Reacquire only through media actually delivered by the verified browser adapter. Tombstones suppress attachment retry as well as message recreation; revalidate source revisions before linking transferred bytes.

After Edit removes a message, schedule deletion of attachments owned exclusively by that message. Perform cleanup only after the replacement transcript/metadata commit is coherent, preserving files needed by the last committed generation if a write fails. Retain shared/foreign files and retryable cleanup state. This does not erase copies retained by the destination's history/trash.

Known rich-message envelopes may retain observed text/quote/forward fields and an unsupported-content marker; v1 does not promise full poll/reaction/contact/location fidelity. Do not retrieve quoted content from an unselected chat or operate its controls. Do not automatically open/consume view-once media. Later absence of disappearing content is not a positive deletion.

## 8. Writes, manual editing, and recovery

Manual edits are supported between syncs. The UI asks the user to finish editing before starting a pass. Before replacing a transcript, recheck it against the captured version/fingerprint; a detected change aborts that chat. Simultaneous external editing during a write is outside the v1 guarantee and must not be described as safely merged.

Use a persistent per-chat transaction journal, staged artifacts, and commit generations to recover from interruption between Markdown, media, and metadata writes. Keep enough previous committed state to recover the interrupted transaction. Do not mark a pass committed until its transcript and metadata agree. Retrying an interrupted commit must not duplicate or lose messages.

This is recoverable multi-file writing, not a claim that local folders or Drive provide an atomic folder transaction. The storage milestone must prove the protocol under injected failures. Temporary recovery state is removed after a successful commit and does not become a permanent revision archive.

A timeout/cancellation after a mutating Drive request has an unknown outcome: the server may still create/update the file. Persist intended owned file/operation/generation identities and reconcile before replaying; never blindly recreate by filename. Do not begin a newer mutation generation while an older outcome remains unresolved. An immediate read after client abort is not proof that the old write cannot complete later. The Drive feasibility milestone must prove its chosen duplicate/stale-write protection using supported API behavior; otherwise leave uncertainty paused as recovery-required.

Keep only bounded pending batch/journal content in Chrome storage, with byte/retention limits established during feasibility. Clear content after commit or explicit discard except what active recovery still needs. A Drive outage must not cause unbounded collection. On extension/schema changes, recover/migrate compatible pending state or pause without discarding it.

First resolve an intact interrupted transaction journal; absent or mismatched metadata may be an expected mid-commit state. **Proposed change:** If no valid journal/checkpoint can resolve missing, unreadable, invalid, or unsupported metadata, enter recovery mode. Preserve existing Markdown and media without an automatic merge. Unique text/sender/time matches may assist a preview, but they are not proof of identity or of past local deletions.

Offer restoring a valid checkpoint/metadata copy, or explicitly starting a new export generation in a fresh, noncolliding root/subtree while preserving the previous tree. Record its separate root identity and generation; never overwrite the old export to simulate a fresh start. Warn that a fresh export cannot inherit local-deletion tombstones from missing metadata. Ambiguous matches never receive guessed IDs, and recovery cannot promise both duplicate-free merging and preservation of unknown local deletions.

## 9. Pause and deletion

Unmarking pauses collection and leaves every destination copy unchanged. It does not clear tombstones, metadata, or Notes.

Delete export is an explicit action for one account/chat/export generation in the currently selected destination. Show the affected transcript, Notes, owned media, and metadata before confirmation. Remove only owned files and report partial failure with enough state to retry. Earlier destinations and unknown files remain untouched. Never infer deletion from a missing source chat or an unchecked row.

## 10. Delivery gates and later work

1. **Browser and Drive feasibility:** Verify identity, source order, localized timestamps, edit/delete observations, actual media access, traversal limits, extension lifecycle, and an authorized Drive create/read/update round trip. Record minimum supported Chrome version and measured budgets. If a capability fails, narrow the product claim before implementation proceeds.
2. **Reconciliation and recovery:** Prove file grammar, Notes preservation, both modes, cancellation, and interrupted-write recovery against fixtures and fake stores, plus a real unpacked extension using synthetic content.
3. **Drive workflow:** Prove consent, account display, raw-file create/update, root-ID enforcement, permission loss, recoverable commits, and intact-tree download. Never equate a mock token test with this gate.
4. **WhatsApp-to-Drive pilot:** The user runs the agreed pilot on 2–3 low-sensitivity chats. Selector counts alone do not satisfy this gate. Record outcomes separately for each media kind. This gate determines the first release's live verification status.
5. **Later local-folder adapter:** Prove directory picking, handle/permission recovery, and the same file/reconciliation contract. Repeat destination-specific checks and a local pilot before claiming support; it does not block the Drive release.

Release claims follow completed gates. Only a successful real pilot changes the applicable verification status. Automated tests and selector diagnostics cannot do so.

The [edge-case catalog](EDGECASES.md) defines required outcomes for late history, disconnections, uncertain writes, media, and lifecycle changes. P0 outcomes are release gates; unsupported or partial content must remain visible rather than being counted as full success.

Later agents may read exports and write derived pages under `agents/<chat_key>/`; no such integration is in v1. Prefer a separate derived-text layer for future transcriptions/descriptions. If later agents are allowed to modify raw blocks, define ownership and deletion semantics before adding that feature.
