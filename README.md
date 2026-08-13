# Design Token Audit Skills

Reusable AI skills for safe, repeatable design token audits in Figma design systems.

This repository turns a design token audit playbook into a small skill suite for AI-supported design system work. The skills are designed to help an agent inspect, reason about, and propose changes to token libraries without making uncontrolled edits.

The operating model is deliberately conservative:

```text
Read-only scan -> Preview -> Approval -> Change -> Verify -> Document -> Baseline
```

## Why This Exists

Design token audits are risky when an AI agent moves too quickly from finding an issue to changing a library. Token names, modes, aliases, scopes, Typography values, AX/accessibility values, and orphan candidates can all affect downstream consumers.

These skills encode a governance-first workflow:

- inspect before changing
- propose before writing
- require explicit approval per pass
- verify after every approved change
- document every library change with changelog and reference evidence
- separate semantic gap-finding from token creation

The goal is not only cleanup. The goal is a token library whose intent is readable by designers, engineers, and AI-supported workflows.

## Skill Suite

The current MVP contains five Claude-ready skills:

Current skill package version: `0.3.1`

| Skill | Purpose |
| --- | --- |
| `design-token-audit-orchestrator` | Runs the end-to-end audit workflow step by step. |
| `token-readonly-scan` | Performs the initial read-only scan and reports the current state. |
| `token-scope-validation` | Validates token scopes against intended usage, including but not limited to `ALL_SCOPES`. |
| `token-semantic-gap-finding` | Finds missing semantic token coverage without creating tokens. |
| `token-creation-proposal` | Turns approved semantic gaps into exact token creation proposals. |

The read-only scan includes a concrete Figma execution contract. It defines the preferred read paths, required collection and variable fields, alias resolution, node-usage evidence, deterministic finding rules, and mandatory coverage reporting. Data that the available Figma access cannot expose must be reported as `not observable`, not inferred.

Every scan produces synchronized Markdown and JSON. The versioned JSON contract provides stable finding fingerprints, explicit evidence and confidence, inventory totals, coverage status, limitations, and machine-comparable summaries for later baseline checks.

The read-only skill includes a dependency-free validator for generated audit JSON artifacts. It checks structural requirements and cross-field consistency before a report is delivered or stored as a baseline.

The scan is not tied to a named Figma plugin. A capability-based adapter contract supports the Figma Plugin API, compatible MCP tools, structured exports, other APIs, and carefully verified mixed sources. Every adapter normalizes its data into the same canonical token snapshot before audit rules run. Missing optional capabilities reduce coverage; missing collection or variable inventory capabilities block the scan.

## Safety Model

The skills should never automatically change:

- Typography values
- AX or accessibility values
- token names that may be used by consumers
- modes that consumer files may expect
- alias structures with platform logic
- direct alpha values
- documented special cases
- orphan candidates without consumer usage validation

If impact is unclear, the agent should document the risk instead of changing the library.

## Download The Skills

For normal use, download the latest ZIP files from GitHub Releases:

```text
https://github.com/ibaldi/design-token-audit-skills/releases
```

Then upload the ZIP files to Claude as custom skills.

## Install In Claude

In Claude, enable Skills and upload each ZIP as a custom skill.

Use the ZIP files from the latest GitHub Release:

```text
design-token-audit-orchestrator.zip
token-readonly-scan.zip
token-scope-validation.zip
token-semantic-gap-finding.zip
token-creation-proposal.zip
```

## Recommended First Test

Use a Figma sandbox library, not a production design system.

Start with:

```text
Use the design-token-audit-orchestrator skill.

Start read-only. Audit this Figma token library and do not change anything before showing a concrete preview and waiting for approval.
```

Then provide:

```text
Library:
Figma file key:
Relevant pages:
Collections:
Expected modes:
Owner for changelog:
Target baseline:
```

For a fuller manual test checklist, see:

```text
tests/manual-claude-test-prompts.md
```

## For Maintainers

This section is for people who want to edit, rebuild, or release the skills.

Edit the relevant `SKILL.md` file under:

```text
skills/claude/
```

Then rebuild the ZIPs locally:

```text
./scripts/build-claude-zips.sh
```

Commit and push the source changes:

```bash
git add .
git commit -m "Update skills"
git push
```

The generated ZIP files in `dist/claude/` are ignored by Git. They can be rebuilt locally or attached to a GitHub Release.

## Validation Fixtures

The read-only scan skill includes a minimal valid audit JSON fixture:

```text
skills/claude/token-readonly-scan/fixtures/minimal-valid-audit.json
```

Validate it with:

```bash
python3 skills/claude/token-readonly-scan/scripts/validate_audit_json.py skills/claude/token-readonly-scan/fixtures/minimal-valid-audit.json
```

## Creating A GitHub Release

Use the release script:

```bash
./scripts/release.sh v0.3.1
```

This rebuilds the Claude ZIP packages and creates a GitHub Release with the ZIPs attached as downloadable artifacts.

Use a new semantic version for each public update, for example `v0.3.2` or `v0.4.0`.

When releasing, update the visible `Version:` line in each `SKILL.md` so users can confirm which package they have installed inside Claude.

## Repository Status

MVP Claude skill suite with a hardened read-only scan contract, canonical Figma token snapshot model, validated JSON output, scope validation, semantic gap-finding, and token creation proposals. The repository is intentionally small so the workflow can be tested in a Figma sandbox before more specialized audit passes are added.
