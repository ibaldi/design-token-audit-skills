---
name: design-token-audit-orchestrator
description: Coordinate a safe Figma token audit through approved scope, token-creation, value, or node-binding fixes. Use for baselines or multi-pass cleanup.
---

# Design Token Audit Orchestrator

Version: 0.8.0

Use this skill to run the full audit workflow step by step.

This package carries the read-only contracts and validators needed to run Phase 1 even when sibling skills are not installed. Before inspecting Figma, read and follow:

- [references/figma-adapter-contract.md](references/figma-adapter-contract.md)
- [references/canonical-figma-token-model.md](references/canonical-figma-token-model.md)
- [references/figma-adapter-mappings.md](references/figma-adapter-mappings.md)
- [references/figma-execution-contract.md](references/figma-execution-contract.md)
- [references/audit-output-contract.md](references/audit-output-contract.md)
- [references/property-traversal-contract.md](references/property-traversal-contract.md)
- [references/workflow-state-contract.md](references/workflow-state-contract.md)

## Core Contract

Start read-only. Do not change Figma variables, tokens, scopes, modes, descriptions, aliases, nodes, changelog rows, or reference cards until a concrete preview has been approved for that exact pass.

Approval for one pass does not approve any other pass.

## Process Navigator

Own and persist the high-level workflow state using `workflow-state.json` contract version `1.1.0`. Validate it with `python3 scripts/validate_workflow_state.py <workflow-state.json>` before presenting it as current. This navigation state does not replace audit evidence, a gate, a preview, approval, drift detection, or verification.

Use these stable workflow steps:

- Phase 1: `P1.1` capabilities, `P1.2` scan, `P1.3` audit validation, `P1.4` specialized read-only validation
- Phase 2: `P2.1` changelog, `P2.2` references, `P2.3` documentation layout, `P2.4` readiness gate
- Phase 3: `P3.1` prioritization, `P3.2` preview, `P3.3` approval, `P3.4` write, `P3.5` verification, `P3.6` successor audit, `P3.7` next-fix decision
- Phase 4: `P4.1` final audit, `P4.2` holds, `P4.3` baseline and handoff

Finding and pass IDs such as `A00` or `B03` are separate from workflow-step IDs.

At the start of a resumed audit and at the end of every material result, preview, approval request, blocker, verification, or handoff, render a compact monospace dashboard from the validated workflow state. Keep ordinary progress commentary shorter, but never omit the dashboard where the user must decide or where control passes back to the user.

```text
╭──────────────────────────────────────────────╮
│ DESIGN TOKEN AUDIT                           │
│ Phase 3 of 4 · Fix passes                    │
│ STATUS: WAITING FOR APPROVAL                 │
╰──────────────────────────────────────────────╯

  ✓ 1  READ-ONLY AUDIT
  ✓ 2  DOCUMENTATION READINESS
  ➜ 3  FIX PASSES
  ○ 4  BASELINE & HANDOFF

CURRENT   Approve binding pass B03
NEXT      Apply B03 → verify → successor audit
OPEN      Bindings 2 · Values 1 · Holds 2
YOU       Reply `Go B03` or `Hold B03`
```

Use `✓` for complete, `➜` for current, `○` for not started, `⏸` for held, and `!` for blocked or failed. Show exactly one recommended next action. If user input is required, show the exact accepted command or decision in `YOU`; otherwise use `YOU none`.

Do not report a total percentage while discovery can add findings. A within-phase `completed / currently known` count is allowed only when explicitly labeled as currently known. Initialize a brand-new audit at `P1.1`. For a resumed audit, if the persisted state is absent, invalid, stale, or contradicts the latest audit or observed Figma records, show `STATUS: BLOCKED — STATE RECONCILIATION REQUIRED` and reconcile read-only before continuing. Never advance the dashboard from a write-tool success response alone.

Phase 3 is iterative. Track `pass_iteration`; when `P3.7` selects another supported fix, increment it and reset the Phase-3 step markers for the new traversal. Do not erase the completed pass from audit history or handoff evidence.

Resolve the next action in this order:

1. Invalid, stale, or contradictory audit or workflow state: correct or reconcile it read-only.
2. Documentation not ready: preview the documentation-readiness pass.
3. Exact approval pending: wait for that pass-specific approval.
4. Approved write completed but not independently verified: verify it.
5. Verification failed: stop and offer only the validated rollback or a refreshed investigation.
6. Successor audit missing after a write: produce and validate it.
7. Supported fix candidates remain: select and preview the next prioritized pass.
8. Only holds remain: proceed to final audit and hold documentation.
9. Everything is verified: complete baseline and handoff.

On resume, load and validate the workflow state, identify the source audit, compare it with the latest available audit and relevant live records, then display the restored dashboard. Restored navigation never restores or broadens a previous write approval.

## Flow

Run the audit as phases, not as a linear list of write-capable passes.

### Phase 1: Read-only Diagnosis

1. Negotiate available Figma read capabilities, select a conforming adapter, and run the read-only scan on a canonical snapshot.
2. Report current state with counts, inspection method, coverage, and limitations in synchronized Markdown and versioned JSON.
3. Save and validate the schema 1.5 read-only JSON, including documentation layout and visual integrity, derived metrics, adapter-derived property coverage, binding findings, FLOAT consumer semantics, and the binding summary, with `python3 scripts/validate_audit_json.py <audit.json>`.
4. Stop and correct the scan if the JSON is invalid, stale, missing coverage, or inconsistent with the Markdown.
5. Always run both specialized MVP validation passes read-only: scope validation and semantic gap-finding. Their results may be `partial`, `not_observable`, or `inapplicable` when supported by evidence, but attempting and reporting both assessments is mandatory and does not depend on a separate user request.
6. Report findings, risks, holds, and possible fix proposals. Do not change anything in this phase.

Record both results under workflow-state `phase1_assessments`, including status, coverage, artifact ID, and any required reason. `P1.4` cannot be skipped. "Not requested", "not mentioned", time constraints, or effort are never valid inapplicability reasons.

The read-only scan may also surface architecture, mode, naming, orphan-candidate, and description observations. Treat those as scan observations only. This release does not define specialized validation or write workflows for those areas.

### Phase 2: Documentation Readiness

Before the first approved fix pass, use the audit JSON `documentation_readiness` section to verify that changelog and reference documentation can be created correctly. Use related findings for issue details; do not reconstruct the normal readiness state from findings alone.

Check:

- changelog existence
- changelog format
- author and type conventions
- newest-first ordering
- reference section, card, or frame location
- required reference evidence for the intended fix

If documentation readiness is missing, run changelog/reference alignment as its own previewed and approved fix pass before other writes. The preview must enumerate every node to be created or changed with exact name, node type, parent/location, and total count, including nested text and shape nodes.

### Documentation Layout Safety

Apply this to changelog tables, reference cards, audit or baseline frames, matrices, lists, and other documentation with repeating or dynamically sized content.

- Use Auto Layout for new internal and repeating structures unless an observed and approved documentation convention requires another layout model. Use child order, padding, and spacing rather than positioning repeating siblings from assumed fixed coordinate offsets.
- Set `layoutMode` before dependent Auto Layout properties. Use `primaryAxisSizingMode` or `counterAxisSizingMode: AUTO` only for axes that should hug content. Use `layoutSizingHorizontal` and `layoutSizingVertical` only where the node type and parent relationship support `HUG` or `FILL`; avoid conflicting stretch or grow behavior.
- Preserve the observed layout model when extending existing documentation. Converting an existing absolute-positioned structure to Auto Layout is a separate structural change: preview the container, every affected descendant, all layout-property changes, and expected position and size effects before approval.
- Absolute `x` and `y` remain allowed for deliberate top-level canvas placement or an approved existing convention. Never place a new repeating row or card solely by incrementing a previous element's coordinate by an assumed fixed offset.
- Include the exact layout model and sizing properties in the node-exact preview. After every documentation write, re-read layout properties and bounds, verify zero overlap and clipped content, and capture a screenshot of the complete affected documentation area. Screenshot review does not replace the successor audit and JSON validation.

When no existing author, type, row, or reference-card convention is observable, do not present an invented convention as an observed fact. State the proposed convention as a design decision and obtain explicit approval for it as part of the exact preview.

After an approved documentation write, rerun the relevant read-only inspection. Produce a successor audit with a new audit ID and timestamps, update `documentation_readiness` from observed nodes, validate the JSON successfully, and only then continue to another pass.

### Phase 3: Approved Fix Passes

Run one fix pass at a time. For every write-capable pass:

1. Create an exact preview.
2. Wait for explicit approval for that pass only.
3. Re-read the affected records immediately before writing.
4. Stop if drift is detected.
5. Apply only approved changes.
6. Verify after the pass.
7. Document with changelog and reference evidence.

Scope, token-creation, existing-token value, and node-binding changes are the specialized fix passes defined by this release. Do not use the orchestrator to apply architecture, mode, naming, orphan, or description changes; keep those findings on hold until a specialized workflow defines their evidence, preview, drift, verification, and documentation requirements.

Token creation, existing-token value correction, and node binding are separate write passes with separate evidence, previews, approvals, drift checks, and verification. A newly created or value-corrected token must be verified by a fresh read-only state before it can appear as the target of a later binding preview.

Never offer or perform an unsupported write as a manual one-off, custom exception, or action "outside the guardrails." The allowed outcomes are to keep it on hold, ask the user to make an explicitly manual change themselves, or author and install a dedicated workflow before the agent performs it.

### Phase 4: Baseline Release

Finish with final verification, hold-item documentation, changelog/reference evidence, and handoff or release notes.

## Read-only Gate

Do not begin scope validation, semantic gap-finding, token creation proposals, supported fix passes, or baseline release until the read-only scan has produced:

- a Markdown report
- a JSON object with `schema_version: 1.5.0`
- explicit inspection method, coverage, and limitations
- valid inventory and summary counts
- structured documentation readiness with layout and visual-integrity checks, derived metrics, validated property coverage for all six adapter-declared property families, binding findings with required FLOAT consumer semantics, and binding summary
- validation success from the bundled read-only scan validator

If a required contract or validator is unavailable, cannot run, or reports any error, the gate is closed. The scan may be returned only as an explicitly **unvalidated draft** with `status: blocked`; do not claim schema conformance and do not begin Phase 2, a specialized pass, a write, or baseline release. Manual review does not replace this gate.

If the JSON is invalid or contradicts the Markdown, correct the read-only scan before continuing.

Do not begin Phase 2 until `P1.4` has run and the workflow-state validator accepts evidence records for both scope validation and semantic gap-finding. Insufficient evidence changes an assessment result to `partial` or `not_observable`; it does not make execution optional.

## MVP Boundary

This release provides specialized workflows for:

- read-only inventory and current-state reporting
- scope validation
- semantic gap-finding
- token creation proposals
- approved scope, token-creation, existing-token value, and node-binding fixes
- final verification and baseline handoff

The read-only scan can report architecture, mode, naming, orphan-candidate, and description observations. It does not turn those observations into specialized validation or write passes. For these areas:

- state the evidence and coverage available from the scan
- classify uncertainty and consumer risk conservatively
- do not imply that a complete specialized review was performed
- do not apply fixes through this orchestrator release
- place proposed follow-up work on hold for a future specialized workflow
- do not describe unsupported observations as eligible for a fix pass in this release

## Recommended MVP Order

1. Read-only scan
2. Always run scope validation; report `partial`, `not_observable`, or evidence-based `inapplicable` when full evaluation is impossible
3. Always run semantic gap-finding, including a hardcoded-value sweep; report `partial`, `not_observable`, or evidence-based `inapplicable` when full evaluation is impossible
4. Token creation proposal, only after a semantic gap is accepted
5. Approved scope or token-creation fix pass
6. Independent read-only verification after any token creation
7. Existing-token value proposal and separately approved value fix, when validated evidence supports it
8. Independent read-only verification after any value write
9. Node-binding proposal and separately approved binding fix, when evidence supports it
10. Independent read-only verification after any binding write
11. Final verification and baseline handoff

Before any fix proposal is applied, complete Documentation Readiness.

## Specialized Skill Availability

The suite packages these specialized workflows separately:

- `token-readonly-scan` for the initial current-state report and its required Figma execution contract. Do not begin later passes until the scan states what was and was not observable.
- `token-scope-validation` for validating token scopes against intended usage, including `ALL_SCOPES`, missing scopes, irrelevant scopes, and Typography/AX exceptions.
- `token-semantic-gap-finding` for missing semantic token coverage.
- `token-creation-proposal` for exact token creation proposals after a gap is accepted.
- `token-binding-fix` for exact, separately approved binding, rebinding, or unbinding of node properties to existing variables.
- `token-value-fix` for exact, separately approved value or alias corrections to existing local variables, with consumer-impact evidence and pre-approved rollback.

Do not claim that this release includes separate hierarchy, mode, naming, orphan, or description validation skills.

Do not assume that naming another skill loads it. If the matching specialized workflow is unavailable, stop at the evidence-backed observation or proposal and do not improvise a write procedure.

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
- for binding passes, every exact node ID, property path, operation, current representation, and target variable ID
- for value passes, every exact variable ID, mode ID, current and proposed representation, consumer impact, and rollback representation

Immediately before applying an approved write, re-read the affected records and stop if they no longer match the approved preview.

Then stop and wait for approval.
