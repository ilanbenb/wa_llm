# Code review

The coordinating agent reviews every coding-agent change before acceptance. Coding agents may check their own work, but cannot supply their own approval. Do not auto-merge or treat review approval as authorization to merge, publish, or run live account tests.

## Review record

Record the base commit and exact reviewed HEAD SHA, affected milestone, and requirements checked. Inspect the full diff and relevant callers/state transitions. Identify uncommitted files separately; an approval cannot silently cover them. Any subsequent change requires review of the new SHA.

Report findings first, ordered by severity. Each finding needs `path:line`, a reproducible trigger, the resulting failure, and a concrete correction. Use P0 for data loss, privacy/account boundary failures, or unsafe recovery; P1 for material incorrect behavior; P2 for meaningful maintainability or smaller correctness problems. Avoid speculative findings and cosmetic demands.

Then report checks actually run, their results, and remaining gaps. If there are no findings, say so without implying untested behavior is verified. Distinguish passed, failed, blocked, skipped, and unrun checks.

## Required checks

- **Identity and ownership:** Account/chat/destination/generation keys remain distinct. Renames and filename collisions cannot merge exports. Unselected content and credentials never enter files or logs. Drive writes use owned root/file IDs and only the intended scope.
- **Reconciliation:** Download preserves wording; subsequent Edit still applies ignored source changes. Local tombstones survive source edits. Notes bytes and local edits survive. Ambiguous block alignment stops writes. Missing DOM messages never imply deletion.
- **Late history:** Repeated syncs still accept unseen older and middle-range IDs. Equal timestamps and duplicate text remain distinct. Preserve unresolved coverage gaps; timestamps and last-success are never discard cutoffs.
- **Disconnect and cancellation:** Separate source loss from pending destination saves. Stop collection safely; bound retries and staging. Worker death, navigation, permission loss, and restart cannot produce false completion or silently resume collection.
- **Unknown media:** Preserve verified opaque bytes or explicit unsupported/unavailable state. Thumbnails, error pages, truncated responses, and self-computed hashes do not prove an original. Tombstones suppress retries.
- **Unknown Drive outcome:** A timeout may follow an accepted or delayed mutation. Reconcile operation/generation identity before replay; prevent duplicate creation and stale late writes. Unresolved outcomes pause newer mutations.
- **Recovery and deletion:** Faults at every write boundary retain a coherent recoverable generation. Resolve journals before declaring metadata lost. Fresh exports preserve old trees. Delete only confirmed owned content; cleanup follows coherent commit.
- **Compact implementation:** Prefer small functions and explicit state transitions. Reject speculative frameworks, unnecessary dependencies, duplicated logic, and silent fallback behavior.

## Evidence and disposition

Tests must exercise production code with representative fixtures and asserted outputs, including failure sequences from [EDGECASES.md](EDGECASES.md). Empty assertions, mocks that merely echo inputs, and skipped integration suites are not evidence of success. Fixture tests never establish live WhatsApp or Drive compatibility.

Request fixes for material findings, then review the resulting SHA and rerun affected checks. Keep unresolved blockers visible; release claims follow [TESTPLAN.md](TESTPLAN.md).
