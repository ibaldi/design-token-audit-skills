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

The first version contains four Claude-ready skills:

| Skill | Purpose |
| --- | --- |
| `design-token-audit-orchestrator` | Runs the end-to-end audit workflow step by step. |
| `token-readonly-scan` | Performs the initial read-only scan and reports the current state. |
| `token-semantic-gap-finding` | Finds missing semantic token coverage without creating tokens. |
| `token-creation-proposal` | Turns approved semantic gaps into exact token creation proposals. |

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

## Install In Claude

Build the ZIP packages:

```bash
./scripts/build-claude-zips.sh
```

Upload the ZIP files from:

```text
dist/claude/
```

In Claude, enable Skills and upload each ZIP as a custom skill.

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

## Updating The Skills

Edit the relevant `SKILL.md` file under:

```text
skills/claude/
```

Then rebuild the ZIPs:

```bash
./scripts/build-claude-zips.sh
```

Commit and push:

```bash
git add .
git commit -m "Update skills"
git push
```

The generated ZIP files in `dist/claude/` are ignored by Git. They can be rebuilt locally or attached to a GitHub Release.

## Creating A GitHub Release

Use the release script:

```bash
./scripts/release.sh v0.1.0
```

This rebuilds the Claude ZIP packages and creates a GitHub Release with the ZIPs attached as downloadable artifacts.

## Suggested Roadmap

- Add mode cleanup skill
- Add scope cleanup skill
- Add changelog alignment skill
- Add naming cleanup skill
- Add orphan review skill
- Add description pass skill
- Add baseline release skill
- Add Codex skill variants from the same source structure

## Repository Status

Initial MVP skill suite for Claude. The repository is intentionally small so the workflow can be tested in a Figma sandbox before more specialized audit passes are added.
