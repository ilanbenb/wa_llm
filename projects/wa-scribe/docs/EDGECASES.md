# wa-scribe edge cases and expected behavior

This is an acceptance catalog for the proposed [specification](SPEC.md) and [test plan](TESTPLAN.md), not a record of executed tests. Drive remains the first destination. P0 cases block release because they can lose, mix, duplicate, or falsely report saved data; P1 cases must preserve a useful export and explain the limitation.

## History that arrives after earlier syncs

A successful commit is not proof of continuous history. Track observed segments, stable boundary anchors, unresolved gaps, requested scope, and stop reasons separately from last-commit time. Encountering a known ID can join an overlap; it is not, by itself, permission to stop searching the requested range.

Worked example; IDs below are illustrative labels, not sortable numbers:

| Pass | Source messages newly observed in verified order | Expected transcript |
| --- | --- | --- |
| 1 | `m40, m42` | `m40, m42`; no claim that the intervening history is complete. |
| 2 | `m43, m44`, with verified overlap | `m40, m42, m43, m44`. |
| 3 | Same observations | No duplicates or unnecessary block rewrites. |
| 4 | `m10, m11, m40, m41, m42` | `m10, m11, m40, m41, m42, m43, m44`. |

If the user removed the complete `m42` block between passes, its tombstone keeps it out of pass 4, including when its media becomes available. Notes and unaffected blocks remain unchanged. If old and new segments cannot be joined reliably, preserve the committed export and report an unresolved ordering gap.

| ID | Priority | Edge case | Expected behavior |
| --- | --- | --- | --- |
| H01 | P0 | Older messages appear after three successful recent-history syncs. | Insert all unseen IDs at their verified positions; never discard them because their dates precede a watermark. |
| H02 | P0 | Missing messages appear between two already saved messages. | Fill the gap without duplicating or rewriting neighbors. A saved date range is not a membership test. |
| H03 | P0 | Two disjoint windows were inspected; a later pass bridges them. | Retain separate segments/gap until verified overlap joins them. Do not infer continuity from minimum/maximum dates. |
| H04 | P0 | New messages arrive while scrolling backward. | Bound the pass with a captured upper message anchor. Leave newer arrivals to the next user-started pass; report that boundary. |
| H05 | P0 | A spinner, blank viewport, or timeout stops backfill; a later recent pass succeeds. | Keep the historical gap and stop reason. Recent success does not upgrade old coverage to complete. |
| H06 | P0 | Resume anchor vanished or order between old/new segments is unknown. | Try bounded overlap around surviving anchors; pause the unresolved segment if order remains unknown. Never guess by timestamp or ID sorting. |
| H07 | P0 | An old local-deletion tombstone reappears in loaded history, edited or with new media. | Suppress the block and media retry in both modes. Only explicit restore clears the tombstone. |
| H08 | P0 | An old message is observed edited or positively deleted during backfill. | Apply the selected mode's normal rules regardless of age. Unobserved old edits remain unverified. |
| H09 | P1 | Same minute/text/sender; changed timezone, DST, locale, or Today/Yesterday labels. | Stable IDs/order remain authoritative. Presentation changes alone create neither a message nor a source edit. Preserve timestamp uncertainty. |
| H10 | P0 | A chat switch or DOM rerender occurs while a batch is loading. | Revalidate source account/chat before accepting each batch; reject observations from another conversation. |

## Connections, saves, and competing work

Collecting, pending save, committed, recovery required, and cleanup pending are different states. A displayed last-success time changes only after a coherent durable commit. A coherent partial commit may advance that time while retaining explicit coverage/media warnings.

| ID | Priority | Edge case | Expected behavior |
| --- | --- | --- | --- |
| C01 | P0 | WhatsApp disconnects but Drive still works. | Stop collection and freeze verified observations. A coherent captured subset may commit as partial; missing DOM is never a deletion. Resume source collection requires a user action. |
| C02 | P0 | Drive disconnects after messages were collected. | Show collected versus saved counts; preserve bounded pending state. Do not advance last-success until coherent data is durable. Revalidate source/Drive/root bindings before resuming. |
| C03 | P0 | Drive applies a create/update but its response is lost. | Treat the outcome as unknown. Reconcile the intended owned file/operation identity; never blindly create another same-named file. |
| C04 | P0 | An old timed-out write completes after a newer write is planned. | Do not start a newer generation while an older mutation is unresolved. Prove supported stale-write protection; an immediate reread after abort is not proof that the server stopped. |
| C05 | P0 | Browser/worker dies between transcript and metadata writes. | Resolve the transaction journal before normal reconciliation. Do not misread a mid-commit mismatch as user deletions or a fresh export. |
| C06 | P1 | Token expiry, revoked consent, lost file permission, rate limit, quota, or server failure. | Classify the reason. Refresh expired credentials through Chrome; reconnect for permission loss; bounded backoff/jitter for transient errors; honor Retry-After within the run budget. Quota needs remediation, not endless retries. |
| C07 | P0 | Stop or browser close occurs during an upload. | Stop issuing new work. Accepted requests may still complete; reconcile their outcomes. Stop is not a remote rollback, and restart does not resume collection automatically. |
| C08 | P0 | Google/WhatsApp account changes, or an old Connect callback returns late. | Invalidate stale work/callbacks; never redirect queued files to a new account. Bind each job to source account/chat, Drive account/root, and export generation. |
| C09 | P0 | Double click, two tabs, or two devices use the same export. | Exclude concurrent work within one Chrome profile. V1 has one owning profile/device per export; different profiles use separate roots. A local lock is not cross-device protection. |
| C10 | P0 | Root/file is renamed, moved outside the export tree, trashed, deleted, or replaced with the same name. | Resolve by recorded IDs and verify ownership/tree membership. Pause on missing/outside/inaccessible objects; never adopt replacements by name. |
| C11 | P0 | User changes Notes while the extension prepares a write. | Abort on detected change. Concurrent editing is outside v1's supported contract unless a tested conditional-write mechanism protects it; a fingerprint check alone does not close the race. |
| C12 | P0 | Extension update changes state schema while work is pending. | Recover or explicitly migrate a compatible journal first; otherwise preserve files and pause. Never discard state or silently start a new export. |
| C13 | P0 | User unmarks or deletes a chat with work queued/in flight. | Cancel new reads/retries for that chat at a safe boundary. Reconcile pending mutations before explicit export deletion; stale jobs cannot recreate a deleted generation. |
| C14 | P0 | Edit removes a message, but commit or attachment cleanup fails. | Keep attachments needed by the last committed transcript. Delete exclusively owned orphans only after the new transcript/state commit; retain retryable cleanup state. |

Chrome may retain a bounded pending batch/journal locally so interrupted writes can recover. It can contain chat content; clear it after commit or explicit discard, preserve only what recovery still needs, and show storage-limit failures. Never collect indefinitely while Drive is unavailable. Exact retention/byte budgets are set during the capability milestone.

## Unknown, partial, or changing media

Distinguish a known message envelope with an unfamiliar attachment format from a message whose identity/order cannot be recognized. The former can often be preserved; the latter makes the affected range incomplete.

| ID | Priority | Edge case | Expected behavior |
| --- | --- | --- | --- |
| M01 | P1 | Original bytes are delivered for an unknown format or missing MIME. | Preserve the verified message/caption and save an opaque attachment with a safe extension such as `.bin`. Record observed type/name separately; preview support is not required to preserve bytes. |
| M02 | P1 | Neither original bytes nor a supported extraction path is available. | Keep a readable pending/unavailable/unsupported marker at that message. Continue independent text/attachments and report the exact limitation. |
| M03 | P0 | A new message envelope has no reliable ID/order. | Do not invent identity, merge it, or silently skip it. Preserve existing files; report an unresolved content/ordering gap. |
| M04 | P0 | A thumbnail, unexpected empty file, truncated file, or login/error page arrives instead of an original. | Do not publish a successful original link or replace earlier verified bytes. Validate available size/type/checksum evidence; a self-computed hash alone does not prove completeness. A valid empty document is handled separately. |
| M05 | P1 | Blob URL expires or a signed URL changes between passes. | Retry by logical message/attachment identity through a fresh delivered browser resource, not by the old URL. Do not persist temporary signed URLs in transcripts, metadata, or logs. |
| M06 | P1 | A video exceeds time/byte limits or local staging space is low. | Stop the affected transfer; keep text and independently verified media where safely committable. Report the exceeded limit; avoid unbounded memory or staging growth. |
| M07 | P0 | Album slots 1 and 3 save, slot 2 fails; different files share a timestamp/name. | Keep stable message/attachment-slot paths and order. Fill slot 2 later without renumbering, overwriting, or duplicating messages. |
| M08 | P0 | Source caption/media changes, or a deletion is observed during transfer. | Revalidate the captured message revision before linking bytes. Replan/defer conflicting observations; apply the mode's wording/deletion rules. Never pair old bytes with new metadata. |
| M09 | P0 | User deleted a block or modified its media placeholder before a later retry succeeds. | Respect the tombstone; otherwise preserve the local marker change and report conflict. Do not resurrect deleted content or overwrite user text. |
| M10 | P1 | A retry succeeds after several unsuccessful syncs. | Enrich the existing attachment slot only, preserving saved wording, Notes, and other blocks. Failed attempts do not create a new message each time. |
| M11 | P1 | A media link's owned file was removed from Drive between passes. | Report missing bytes separately from message deletion. Reacquire only if delivered again and the block is not suppressed; never silently treat a broken link as healthy. |
| M12 | P1 | The implementation cannot handle a format yet. | Do not retry forever on every viewport observation. Retry transient failures within budget; retry unsupported formats after explicit user action or a relevant support update. |

Represent collection coverage and attachment availability separately. Example result: **Text inspected for requested range; 2 attachments unavailable, 1 saved as unknown format.** This is a useful committed export, not an unqualified complete-media success.

## Other content and lifecycle boundaries

| ID | Priority | Edge case | Expected behavior |
| --- | --- | --- | --- |
| X01 | P1 | Reply/forward refers to a message outside the available or selected chat. | Preserve observed quote/forward text only. Do not fabricate a standalone original, infer its author, or visit an unselected chat to resolve it. |
| X02 | P1 | Poll, reaction, contact, location, system event, or another unsupported rich item appears. | Preserve known envelope/text fields plus a readable unsupported-content marker. Do not silently drop it or interact with its controls. Full structured export is separate feature work. |
| X03 | P1 | View-once or disappearing content is present. | Do not automatically open/consume view-once media. Save only delivered visible content; later absence is not evidence of delete-for-everyone. Show unavailable content honestly. |
| X04 | P0 | Notes or message content resembles structural headings; local blocks become ambiguous. | Apply the reversible grammar; preserve Notes bytes. Stop before rewriting ambiguous content. |
| X05 | P0 | Extension reinstall/profile reset loses local bindings while Drive files remain. | Offer verified reconnection/recovery or a separate fresh generation. Do not silently adopt a folder by name, overwrite the old export, or promise recovered tombstones. |
| X06 | P1 | Several chats run; one loses access or exceeds its history budget. | Report independent per-chat results and aggregate saved/pending counts. Preserve historical gaps and successful other commits; never turn the whole run green from one successful chat. |

## Required sequence tests

Each catalog ID needs an expected-outcome fixture or a clearly identified real-browser check. Prioritize sequences, not only one-pass examples:

1. **Late history:** three recent passes; add Notes/delete one whole block; reveal older plus middle-gap history; interrupt; resume; expose an old edit/media; repeat with no new data. Run both modes and verify IDs/order, Notes, tombstone, media ownership, and unresolved coverage.
2. **Unknown write outcome:** inject fail-before-apply, apply-then-lose-response, apply-late, and out-of-order callbacks. Assert no blind duplicate create and no newer generation while an old mutation remains uncertain.
3. **Split outage:** source disconnect during collection; recover; Drive disconnect during save; recover with a permission change. Assert collected and saved counts differ correctly and last-success advances only on a coherent commit.
4. **Media evolution:** unknown type, expired blob, failed album slot, later verified bytes, then local deletion and retry. Assert stable slots, explicit states, no resurrection, and no new message from enrichment.
5. **Lifecycle:** stop, worker termination, account switch, schema update, and explicit deletion with queued retries. Assert stale jobs cannot write to another account or recreate deleted generations.

Automated suites use synthetic content and fake services. Real browser/OAuth/media evidence remains separate; no real account action is authorized by adding this catalog.
