# First coding assignment: T01

This is the handoff entry point for another coding agent. Start from the `codex/wa-scribe-instructions` branch of `orenda/wa_llm`; the instructions are not on `main` until separately merged. The project is `projects/wa-scribe/` inside that repository.

Read the [coding rules](AGENTS.md), [T01 assignment and acceptance criteria](docs/tasks/T01.md), and [completion template](docs/AGENT_HANDOFF.md). The [review checklist](docs/CODE_REVIEW.md) explains how the coordinating agent will review the result.

## Copy this prompt

```text
Repository: https://github.com/orenda/wa_llm
Starting branch: codex/wa-scribe-instructions
Project directory: projects/wa-scribe/

Read the project's AGENTS.md and docs/tasks/T01.md, including its linked
contract sections. Implement T01 only: a small strict-TypeScript Manifest V3
extension shell, plain-DOM side panel, Vite build, Vitest unit tests, and a
Playwright test loading the actual unpacked extension against a fake page.
Include the npm lockfile, exact tested Node 24 version, documented commands,
and a dedicated project-scoped .github/workflows/wa-scribe.yml at the Git root.

Keep source/package/tests in projects/wa-scribe/. Leave Python bot code,
Python dependencies, and existing CI unchanged. Keep code compact and direct.
No React, speculative frameworks, OAuth, Drive writes, real WhatsApp scraping,
media, sync engine, or fake export success in this task.

Add and actually run typecheck, test:unit, test:browser, and build scripts.
Required tests must execute meaningful cases and fail on zero discovery.
An empty screenshot or mocked chrome global is not the extension browser test.
Automatic tests must not contact real Google or WhatsApp services.

Return the completion template from docs/AGENT_HANDOFF.md: diff, commit/base
SHA (or explicitly uncommitted), exact test commands/results/counts, and any
blocked or unrun checks. Stop for coordinating-agent review. Do not self-approve,
merge, publish an extension, or start T02. Preserve unrelated work.
```

## Obtain the files

Use an existing authorized checkout where available. Otherwise:

```bash
git clone --branch codex/wa-scribe-instructions https://github.com/orenda/wa_llm.git
cd wa_llm/projects/wa-scribe
```

An existing checkout should fetch and switch to that branch while preserving its local changes. No additional Git worktree is required. The agent needs repository access if the repository is private.

The package and scripts do not exist yet: creating and validating them is T01. Real Google connection, WhatsApp compatibility, and future tickets are not verified by completing this assignment.
