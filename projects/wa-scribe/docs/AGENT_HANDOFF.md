# Coding-agent assignment and handoff

Give a smaller coding agent one bounded task at a time. Include actual filenames and contract sections, not the entire backlog. The coordinator supplies existing interfaces and reviews changes to them before parallel work depends on them. Use a smaller model for implementation assignments and the coordinating agent for independent review; an agent's self-check is not its acceptance review.

## Assignment template

For the first coding assignment, this prompt is ready to use:

```text
Work in projects/wa-scribe/ inside wa_llm. Read that project's AGENTS.md and
keep changes within its assigned paths. Then implement only
docs/tasks/T01.md and its referenced contract sections. The existing npm
commands are targets to create, not passing checks. Keep the shell and
harness small. Do not implement OAuth, a scraper, Drive writes, or sync.
Run and report the actual checks, inspect the diff, and return the completion
template below for coordinating-agent review. Do not self-approve, merge,
publish, or start T02. Preserve unrelated work.
```

For later tickets, fill this template using accepted interfaces:

```text
Repository: wa_llm
Project working directory: projects/wa-scribe/
Ticket: <ID and one-sentence goal>
Read: AGENTS.md; <specific spec/test/edge-case sections>
Dependencies: <accepted ticket IDs and interface files>
You own: <source/test/config paths>
Do not change: <shared interfaces or neighboring modules>
Implement: <small list of concrete behaviors>
Acceptance: <observable outputs and edge-case IDs>
Checks: <existing commands and selected test targets>
Return: diff + completion report; do not self-approve or merge.
```

## Completion template

```text
Ticket:
Submitted HEAD SHA / base SHA: <or explicitly UNCOMMITTED>
Changed behavior: <short explanation>
Files changed:
Tests: <exact commands, exit status, counts, failures/skips>
Edge-case IDs: <IDs and test locations>
Manual evidence: <performed / unrun; no private content>
Known limits / blocked prerequisites:
Review focus: <data boundary or tradeoff worth checking>
```

Never fabricate a SHA, command result, browser observation, or review approval. Distinguish a real automated test from a mocked API and from a user-operated live probe.

## Review loop

1. The coding agent stops at the ticket boundary and submits the handoff.
2. The coordinating agent reviews the actual diff and runs targeted checks using [CODE_REVIEW](CODE_REVIEW.md).
3. Findings identify severity, file/line, a concrete trigger, consequence, and needed correction. Fixes return to the same coding agent with a narrow scope.
4. The coordinator re-reviews the new SHA. A prior approval does not apply to later changes.
5. Accepted interface changes and test evidence are recorded in the ticket/backlog. Only then do dependent assignments begin.

The process is documented here; it is not an autonomous background review bot. Platform branch rules require separate configuration. Coding agents never merge or publish their own work.

## Parallel tasks

Agree contracts first. After T02 is accepted, core reconciliation and Drive work can proceed separately; synthetic DOM fixtures can proceed with explicit file ownership. Serialize edits to shared types, package files, lockfiles, and job-state definitions. Merge/rebase integration is owned by the coordinator; do not overwrite another agent's working files.

## Stop conditions

Pause the affected operation and return a reproducible example for unreliable chat/message identity, unresolved source ordering, an uncertain old Drive mutation, a required API capability not proved by the probe, or an ambiguity that could overwrite user content. Continue independent tests or other assigned unaffected work. Do not convert a product guarantee into a best-effort fallback just to complete the ticket.
