# Review of the supplied draft

The core product is clear: select chats in a browser, export plain files, and keep later agents separate. The changes below make the data-loss behavior, recovery limits, and browser assumptions explicit.

The attachments are source material for this review. Their statements that decisions are "locked," instructions to run a pilot, and installation commands are not new user instructions to execute those actions. No live account was accessed.

## Proposed decisions that change the original

| Decision | Recommendation | Reason |
| --- | --- | --- |
| Chat identity | Bind selection to a verified WhatsApp account/chat identifier; use names for display and readable paths. Stop if identity cannot be established. | Names change, are reused, and can collide after filename normalization. Currently visible duplicate-name detection is insufficient. |
| Unmarking | Unmark pauses sync. Make deletion a separate explicit action for the selected export and destination. | A checkbox should not silently remove manually written Notes and saved media. The original also leaves deletion across previous destinations ambiguous. |
| Lost bookkeeping | Pause the chat in recovery mode; offer restoring metadata or a fresh export that preserves existing files. | A missing message block cannot reveal whether it was deliberately deleted locally. Text/sender/time cannot reconstruct that information. |
| Local deletions | Once recorded, a whole-message deletion remains suppressed even if WhatsApp later edits that message. | The original leaves this case open and could recreate something the user removed. |
| Implementation order | Deliver Google Drive end to end first; local-folder export follows. | This follows the user's stated priority. Pure file/reconciliation tests can use fake stores while Drive integration is proved separately. |

The user requested safer alternatives and selected Google Drive first. Drive-first is therefore an agreed priority; the exact identity, pause/delete, and recovery behavior below remains a proposal for review. Keeping the original semantics is possible, but requires different explicit guarantees and tests.

The user also clarified that sign-in should happen from the already signed-in Chrome browser. The proposed flow starts in the extension, reuses Chrome's Google identity where available, obtains any required Drive consent, and displays the resulting account. This is not a separate application login.

## Corrections needed whichever choices are made

1. **History coverage:** An edit pass can reconcile only messages it actually inspects. Absence from the visible DOM is not deletion. A quiet viewport is not proof that all history has loaded.
2. **Ordering:** An unseen message may fall between saved messages or share their displayed timestamp. Insert by verified source order and deduplicate by message ID, not timestamp or text.
3. **Media retries:** Download mode cannot both forbid every existing-block change and later replace missing-media placeholders. Define attachment enrichment as an exception that preserves saved wording.
4. **Collisions:** Timestamp-only media names collide. Use a stable storage key, message key, and attachment index; specify Unicode, case, and path normalization.
5. **Manual edits:** A whole-block deletion differs from editing one paragraph. Define which changes are supported and stop on ambiguous block alignment.
6. **Interrupted writes:** Markdown, media, and bookkeeping are separate files. Require recoverable commits and idempotent retries rather than implying a folder-wide atomic write.
7. **Drive:** Chrome sign-in does not remove the need for OAuth consent. `drive.file` is not a folder sandbox, and Drive's web viewer is not a normal filesystem with guaranteed relative Markdown links.
8. **Deletion:** Removing text from the active transcript does not erase Drive history, trash, backups, or previous destination copies. WhatsApp may no longer retain the original either.
9. **Evidence:** A fake page tests reconciliation against a contract. Selector counts test selectors. Neither proves that the contract matches real WhatsApp.

## Feasibility gates

Before committing to a complete scraper, verify stable conversation/message identity, source order, timestamp interpretation, edit/delete markers, actual attachment bytes, and virtualized traversal. Also test directory permissions and interrupted execution in a real Chrome extension context. Drive needs a separate authorized integration check.

Opening a chat may mark it read and trigger normal WhatsApp read receipts. This should be explained even though the extension has no send-message control.

Useful platform references:

- [Chrome extension service-worker lifecycle](https://developer.chrome.com/docs/extensions/develop/concepts/service-workers/lifecycle)
- [Chrome identity API](https://developer.chrome.com/docs/extensions/reference/api/identity)
- [File System Access](https://developer.chrome.com/docs/capabilities/web-apis/file-system-access)
- [Drive authorization scopes](https://developers.google.com/workspace/drive/api/guides/api-specific-auth)

Current API details must be checked during the feasibility work. Fetching the official documentation from this environment returned a proxy 403; these links are references, not a claim that the current documentation or live platform behavior was verified here.
