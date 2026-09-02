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
- separate semantic gap-finding, token creation, and node binding

The goal is not only cleanup. The goal is a token library whose intent is readable by designers, engineers, and AI-supported workflows.

## Skill Suite

The current MVP contains seven Claude-ready skills:

Current skill package version: `0.8.0`

| Skill | Purpose |
| --- | --- |
| `design-token-audit-orchestrator` | Runs the end-to-end audit workflow step by step. |
| `token-readonly-scan` | Performs the initial read-only scan and reports the current state. |
| `token-scope-validation` | Validates token scopes against intended usage, including but not limited to `ALL_SCOPES`. |
| `token-semantic-gap-finding` | Finds missing semantic token coverage without creating tokens. |
| `token-creation-proposal` | Turns approved semantic gaps into exact token creation proposals. |
| `token-binding-fix` | Applies exact, separately approved node-property binding changes to existing variables. |
| `token-value-fix` | Corrects exact mode values of existing local variables with consumer-impact evidence and pre-approved rollback. |

### MVP Scope Boundary

The specialized MVP workflow covers read-only scanning, scope validation, semantic gap-finding, token creation proposals, approved scope, token-creation, existing-token value, and node-binding fixes, and baseline handoff.

The read-only scan can surface architecture, mode, naming, orphan-candidate, and description observations. Version `0.8.0` does not provide separate validation or write workflows for those areas. Treat them as evidence-backed observations or hold items, not as completed specialized reviews or automatically actionable fixes.

The read-only scan includes a concrete Figma execution contract. It defines the preferred read paths, required collection and variable fields, alias resolution, node-usage evidence, deterministic finding rules, and mandatory coverage reporting. Data that the available Figma access cannot expose must be reported as `not observable`, not inferred. The orchestrator ZIP now bundles the Phase 1 contracts and validators as well, so installing it alone does not silently lose the schema gate.

Every scan produces synchronized Markdown and audit JSON using schema `1.5.0`. The contract provides stable finding fingerprints, explicit evidence and confidence, inventory totals, coverage status, structured documentation readiness with layout and visual-integrity checks, derived alias/description/scope metrics, adapter-derived property traversal coverage, structured node-binding findings, FLOAT consumer-value semantics, limitations, and machine-comparable summaries for later baseline checks.

Property traversal uses contract `1.0.0` and accounts for simple node fields, paints, effects, layout grids, typography, and component properties. Each adapter-declared property reports eligible, inspected, bound, literal, and mixed/unsupported counts. This prevents a scan from claiming complete binding or hardcoded-value coverage merely because no findings were emitted. Rotation, blend mode, and Auto Layout sizing behavior are explicitly outside the current variable-binding profile.

Documentation writes use dynamic-layout safeguards across changelog tables, reference cards, audit or baseline frames, matrices, and lists. Repeating content must not be positioned through assumed fixed offsets; every write is verified through layout properties, node bounds, overlap and clipping checks, and a screenshot of the complete affected area.

### Process Navigator

The orchestrator maintains a validated `workflow-state.json` using workflow contract `1.1.0`. It cannot complete `P1.4` or enter Phase 2 without evidence records for both scope validation and semantic gap-finding. At resume points, material results, approval requests, blockers, verification results, and handoff, it renders a compact visual dashboard showing the current phase, completed phases, one recommended next action, open-item counts, blockers or holds, and the exact user decision when required.

The Phase-1 semantic assessment always performs an observable hardcoded-value sweep, including unmatched literals, and distinguishes recurring semantic intent from repeated raw values or variants of one component. Empty scope arrays remain distinct from explicit `ALL_SCOPES` unless adapter evidence establishes equivalent behavior.

The navigator uses stable process IDs `P1.1` through `P4.3`; finding and pass IDs such as `A00` or `B03` remain separate. It does not use misleading total percentages while discovery may add findings. Restoring navigation state never restores a previous write approval, and invalid or stale state blocks progress until read-only reconciliation succeeds.

FLOAT binding candidates require a consumer-resolved preflight. The stored or adapter-reported variable value is recorded separately from the value resolved for the exact consumer node. A candidate stays on hold when the resolved value is unavailable or differs from the intended effective value; this prevents opacity scale mismatches such as `0.45` versus `0.0045`.

The read-only skill includes a dependency-free validator for generated audit JSON artifacts. It checks structural requirements and cross-field consistency before a report is delivered or stored as a baseline. Missing or failed validation blocks later phases; a manual plausibility review may only produce an explicitly unvalidated draft.

It also includes a dependency-free canonical snapshot validator and equivalent Plugin API, MCP, and export fixtures. Contract comparison verifies that different adapters preserve the same token semantics even when optional document coverage differs.

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

The seven ZIP files in `dist/claude/` are the installable skill packages. A separately named `design-token-audit-skills-v0.8.0-complete.zip` is a maintainer/source archive of the whole project and must not be uploaded as a single skill.

## Install In Claude

In Claude, enable Skills and upload each ZIP as a custom skill.

Use the ZIP files from the latest GitHub Release:

```text
design-token-audit-orchestrator.zip
token-readonly-scan.zip
token-scope-validation.zip
token-semantic-gap-finding.zip
token-creation-proposal.zip
token-binding-fix.zip
token-value-fix.zip
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

Validate and compare the canonical adapter fixtures with:

```bash
python3 skills/claude/token-readonly-scan/scripts/validate_snapshot.py --compare \
  skills/claude/token-readonly-scan/fixtures/snapshot-plugin-api.json \
  skills/claude/token-readonly-scan/fixtures/snapshot-mcp.json \
  skills/claude/token-readonly-scan/fixtures/snapshot-export.json
```

Run positive and adversarial validator regression tests with:

```bash
python3 -m unittest -v tests/test_validators.py
```

Validate a token value-fix evidence proposal with:

```bash
python3 skills/claude/token-value-fix/scripts/validate_value_fix.py \
  skills/claude/token-value-fix/fixtures/opacity-disabled-correction.json
```

Validate persisted workflow navigation state with:

```bash
python3 skills/claude/design-token-audit-orchestrator/scripts/validate_workflow_state.py \
  skills/claude/design-token-audit-orchestrator/fixtures/minimal-valid-workflow-state.json
```

Run all source, metadata, version, reference, fixture, and package checks with:

```bash
python3 scripts/check_release.py --version 0.8.0
```

## Creating A GitHub Release

Use the release script:

```bash
./scripts/release.sh v0.8.0
```

This rebuilds the Claude ZIP packages and creates a GitHub Release with the ZIPs attached as downloadable artifacts.

Use a new semantic version for each public update, for example `v0.3.2` or `v0.4.0`.

When releasing, update the visible `Version:` line in each `SKILL.md` so users can confirm which package they have installed inside Claude.

## Repository Status

MVP Claude skill suite with a hardened read-only scan contract, canonical Figma token snapshot model, validated JSON output, scope validation, semantic gap-finding, token creation proposals, separately approved existing-token value corrections, and node-binding fixes. The repository is intentionally small so the workflow can be tested in a Figma sandbox before more specialized audit passes are added.
