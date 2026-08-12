---
name: design-token-audit-orchestrator
description: Run an end-to-end, plugin-independent design token audit workflow for Figma design systems using capability-based adapters and canonical snapshots. Use when the user wants to audit a token library, establish or compare a baseline, evaluate token quality, coordinate multiple audit passes, or safely move from read-only analysis to approved cleanup. Always start read-only, report coverage and limitations, require an exact preview and separate approval for every write pass, detect drift before writing, and protect Typography, accessibility values, aliases, modes, orphan candidates, changelog rows, and reference cards.
---

# Design Token Audit Orchestrator

Use this skill to run the full audit workflow step by step.

## Core Contract

Start read-only. Do not change Figma variables, tokens, scopes, modes, descriptions, aliases, nodes, changelog rows, or reference cards until a concrete preview has been approved for that exact pass.

Approval for one pass does not approve any other pass.

## Flow

1. Negotiate available Figma read capabilities, select a conforming adapter, and run the read-only scan on a canonical snapshot.
2. Report current state with counts, inspection method, coverage, and limitations in synchronized Markdown and versioned JSON.
3. Validate the read-only JSON against the audit output contract.
4. Stop and correct the scan if the JSON is invalid, stale, missing coverage, or inconsistent with the Markdown.
5. Recommend pass order.
6. Run one pass at a time.
7. Preview before any write.
8. Wait for explicit approval.
9. Re-read the affected records immediately before writing and stop if drift is detected.
10. Apply only approved changes.
11. Verify after the pass.
12. Document with changelog and reference evidence.
13. Finish with baseline verification and handoff.

## Read-only Gate

Do not begin mode cleanup, scope cleanup, changelog alignment, naming cleanup, orphan review, description passes, semantic gap-finding, token creation proposals, or baseline release until the read-only scan has produced:

- a Markdown report
- a JSON object with `schema_version: 1.0.0`
- explicit inspection method, coverage, and limitations
- valid inventory and summary counts
- validation success from the read-only scan validator, when scripts can be executed

If automated validation is unavailable, manually apply the same checks and disclose that automated validation was not run.

If the JSON is invalid or contradicts the Markdown, correct the read-only scan before continuing.

## Recommended Pass Order

1. Mode cleanup
2. Scope cleanup
3. Changelog alignment
4. Naming cleanup
5. Orphan review
6. Description passes
7. Semantic gap-finding
8. Token creation proposal, only if requested or justified
9. Baseline release

## Use Individual Skills

Use these skills when the user asks for a specific pass:

- `token-readonly-scan` for the initial current-state report and its required Figma execution contract. Do not begin later passes until the scan states what was and was not observable.
- `token-semantic-gap-finding` for missing semantic token coverage.
- `token-creation-proposal` for exact token creation proposals after a gap is accepted.

## High-risk Areas

Never change automatically:

- Typography values
- AX or accessibility values
- token names that may be consumed by design files or code
- modes that consumer files may expect
- alias structures with platform logic
- direct alpha values
- documented special cases
- orphan candidates without consumer usage validation

If impact is unclear, document the risk instead of changing.

## Required Preview

Before every write, provide:

- affected library
- affected collection
- type of change
- exact count
- affected names or pattern
- risk level
- planned changelog row
- planned reference card or frame
- verification plan
- source audit ID, scan timestamp, schema version, and coverage

Immediately before applying an approved write, re-read the affected records and stop if they no longer match the approved preview.

Then stop and wait for approval.
