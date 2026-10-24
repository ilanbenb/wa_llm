# Instructions for coding agents

## Assignment and ownership

Implement only the assigned ticket. Start with its listed dependencies and acceptance criteria in [docs/BACKLOG.md](docs/BACKLOG.md). The coordinating agent owns architecture decisions, ticket acceptance, and code reviews. Do not self-approve, merge, publish, or start the next dependent ticket without its review result.

Read the ticket's referenced sections of [SPEC](docs/SPEC.md), [TESTPLAN](docs/TESTPLAN.md), and [EDGECASES](docs/EDGECASES.md). Requirements in those documents are contracts to implement, not authorization to operate real accounts. If a conflict changes product behavior or can lose data, describe one concrete example to the coordinator and keep working on unaffected parts. Do not invent a silent fallback.

This project lives at `projects/wa-scribe/` inside the `wa_llm` Git repository. Run npm/build/test commands from this project directory. Keep its package manifest, lockfile, source, tests, and build outputs here; do not create nested Git metadata, a Git submodule, a second project folder, or a root npm workspace. Keep Python dependencies and bot source unchanged. Existing cloud tasks are isolated; use the checkout provided and create no Git worktree unless explicitly requested. Inspect Git status first and preserve other agents' work. Coordinate file ownership before parallel edits.

The only planned shared-repository exception is a dedicated `.github/workflows/wa-scribe.yml` workflow at the Git root. Scope it to this project with path filters and project working directories/cache paths; leave the existing Python workflow unchanged. Root Git commands operate on the shared repository, so inspect and stage only assigned paths.

## Keep code compact and readable

- Use strict TypeScript, plain functions, ordinary objects, and explicit discriminated states. Prefer a small plain-DOM panel; the initial stack is npm/Vite/Vitest/Playwright.
- Add a type or helper when it captures an actual boundary or repeated operation. Use small interfaces at external I/O boundaries so real and fake stores can share behavioral tests. Do not build a generic repository framework.
- Avoid speculative abstractions: base classes, plugin registries, DI containers, event buses, multiple retry wrappers, or a service per function. Do not add React, state-management libraries, databases, a backend, or new runtime dependencies without a concrete need reviewed by the coordinator.
- One feature per diff. Aim for roughly 250 changed production lines and a few source files; this is a review-size guide, not a limit for scaffolding/configuration or meaningful test fixtures. Split at behavior boundaries. Never shorten code by removing checks, golfing names, or squeezing statements onto one line.
- Validate unknown input at the DOM, message-passing, storage, and HTTP boundaries. Use `unknown` and narrow it. Do not silence issues with `any`, unsafe casts, `@ts-ignore`, or blanket lint/test exclusions.
- Put retries and state transitions in one obvious place. Preserve original causes; no empty catches, success-shaped defaults, broad catch-and-continue, or hidden unbounded loops.
- Comments explain non-obvious invariants. Avoid comments that merely narrate a line, public APIs used once, placeholder layers, and unrelated cleanup.

## Non-negotiable behavior

- Identity is account/chat/message based, never filename, display name, timestamp, or message text alone. Unverifiable identity/order means partial/conflict, not guessed data.
- Unseen IDs may appear before or inside history saved across many earlier passes. Preserve observed segments, gaps, and tombstones. A last-sync timestamp is not a discard cutoff.
- Download preserves wording; Edit changes only positively observed known messages according to the contract. Missing DOM rows are not deletions. Notes stay byte-identical; ambiguous manual edits are preserved and reported.
- Unmark pauses. Explicit delete affects only owned files in its bound export generation. Late retries must not resurrect deleted blocks/exports.
- Treat source disconnection, pending destination writes, and committed state separately. A timed-out Drive mutation may have succeeded. No blind create retry, newer generation over an unresolved older mutation, or atomic/exactly-once claim without evidence of the storage primitive.
- V1 has one owning profile/device per export. A local lock or pre-write fingerprint is not cross-device exclusion or atomic protection against concurrent manual editing.
- Unknown attachment format is not a reason to lose a recognized message. Save delivered verified original bytes opaquely when possible; otherwise show a limitation. A thumbnail/truncated response is not an original. Media retries cannot recreate a tombstoned message.
- No model calls, send-message controls, server-held WhatsApp login, hidden/private endpoint discovery, or automatic view-once consumption. Keep permissions narrow and diagnostics free of message contents, credentials, and temporary signed URLs.

## Tests and completion

Until T01 is accepted, package commands are planned only. Afterward use the repository scripts and committed npm lockfile; `npm ci` is the clean-install path. Node 24 is the initial runtime target; pin the actual chosen tool versions in T01.

Write tests for behaviors that can lose/mix/duplicate data, parsing, and real external boundaries. Prefer golden files, sequential sync histories, fake-store faults, and real extension/fixture interactions over assertions that mirror implementation details. Map covered edge-case IDs to meaningful assertions. Do not add trivial tests to increase counts.

Ordinary automatic tests must block real Google/WhatsApp requests and work without credentials. Keep authorized live probes explicit and separate. A fake page passing does not verify real WhatsApp; a skipped/zero-test run is not a pass. Do not disable assertions, quietly skip failures, or mark unrun checks green.

Run the relevant tests and required build/type checks for the diff, then inspect the final diff. Use [AGENT_HANDOFF](docs/AGENT_HANDOFF.md) to report exactly what changed, command outcomes/counts, edge cases covered, remaining failures, and the exact submitted SHA (or clearly label uncommitted work). Return to the coordinating reviewer. Approval is for that commit only.
