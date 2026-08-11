# Design Token Audit Skills

Reusable AI skills for safe, repeatable design token audits in Figma design systems.

The skills are based on a governance-first workflow:

```text
Read-only scan -> Preview -> Approval -> Change -> Verify -> Document -> Baseline
```

They are designed to help AI agents audit token libraries without making uncontrolled changes. The skills protect high-risk areas such as Typography, AX/accessibility values, orphan candidates, aliases, modes, and production-used token names.

## Skill Suite

This repository starts with a small, testable Claude skill suite:

- `design-token-audit-orchestrator`  
  Runs the end-to-end audit workflow step by step.

- `token-readonly-scan`  
  Performs the initial read-only audit scan and reports the current state.

- `token-semantic-gap-finding`  
  Finds missing semantic token coverage without creating tokens.

- `token-creation-proposal`  
  Turns approved semantic gaps into concrete token creation proposals, but does not create tokens without explicit approval.

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

If impact is unclear, document instead of changing.

## Repository Status

Initial MVP skill suite for Claude. Codex variants can be added later using the same source structure.
