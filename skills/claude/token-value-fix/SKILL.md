---
name: token-value-fix
description: Preview, approve, apply, and verify exact value corrections to existing local Figma variables. Use when a validated audit identifies a wrong mode value.
---

# Token Value Fix

Version: 0.8.0

Use this skill only to correct values of existing local Figma variables. Read [references/value-evidence-contract.md](references/value-evidence-contract.md) and validate the evidence JSON with `python3 scripts/validate_value_fix.py <proposal.json>` before presenting a write-ready preview.

## Boundary

This skill supports changing one existing variable's explicitly listed mode values to literal values or aliases. It does not create or delete variables, collections, or modes; change names, scopes, descriptions, code syntax, bindings, or component structure; detach instances; or perform unrelated documentation cleanup.

Default to one variable per pass. Token creation and node binding remain separate passes with separate approvals. Never use a value correction as an implicit repair for bindings that were not included in the approved preview.

## Required Input

Require:

- a validated schema `1.5.0` read-only audit with audit ID, timestamp, coverage, and limitations
- a validated value-fix evidence record using contract `1.0.0`
- stable local variable, collection, and mode IDs
- exact current and proposed representations for every affected mode
- complete local inbound-alias and bound-node impact inspection
- external-consumer coverage or an explicit high-risk limitation for the preview
- documentation readiness and exact rollback representations

Keep the proposal on hold if the variable is remote, evidence is stale, a mode or alias target is missing, the alias graph is unresolved or cyclic, local consumers were not inspected completely, numeric semantics are unclear, or a safe rollback cannot be stated exactly.

Typography, AX/accessibility, direct-alpha, platform-logic, and broadly consumed values are high risk. They require explicit approval naming that exact risk; never include them in a general batch approval.

## Exact Change Tuple

Every change is identified by:

```text
variable_id + mode_id + operation + proposed_value_fingerprint
```

Approval for one mode does not authorize another mode or another variable. A general `Go`, a prior token-creation approval, or a binding approval is insufficient.

## Required Preview

Before writing, show:

```text
Preview: Token Value Fix

Proposal ID and source audit:
Library and collection:
Variable ID, name, and resolved type:
Exact mode count:
For each mode: current value/alias -> proposed value/alias:
Numeric family, stored representation, and effective consumer unit/range:
Prediction method and evidence:
Local inbound aliases:
Bound node consumers and expected effective values:
External-consumer coverage and limitations:
Risk, including Typography/AX/direct-alpha/platform concerns:
Pre-approved rollback value for every tuple:
Changelog row:
Reference evidence:
Verification plan:

Please approve these exact value tuples and their exact rollback values before I make any changes.
```

## Documentation Layout Safety

For changelog rows, reference cards, and other repeating or dynamically sized documentation, use Auto Layout internally unless an observed approved convention requires another model. Preserve existing layout when extending it; converting absolute content to Auto Layout requires a separate node-exact preview of every affected descendant and geometry effect. Absolute coordinates remain valid for deliberate top-level placement, but never position a repeating row or card solely by adding an assumed fixed offset to its neighbor.

Set `layoutMode` before dependent properties, use `AUTO`, `HUG`, and `FILL` only where the node and parent relationship support them, and avoid stretch/grow conflicts. Include layout and sizing properties in the preview. After the documentation write, re-read layout properties and bounds, verify zero overlap and clipping, and capture the complete affected area in a screenshot; screenshot review does not replace structural verification or the successor audit.

## Approved Write Gate

After approval and immediately before writing:

1. Re-read the variable, collection, ordered modes, current values or aliases, alias targets, inbound aliases, bound consumers, documentation nodes, and risk evidence.
2. Stop for a revised preview if any tuple, count, consumer, coverage statement, or assumption drifted.
3. Confirm every proposed literal matches the variable type. For aliases, confirm the target exists, has the same resolved type, covers the required modes, and introduces no cycle.
4. For FLOAT values, confirm the numeric family, stored representation, effective unit/range, and prediction evidence. Do not infer a conversion from the UI display, scope, name, or type.
5. Confirm exact rollback values were approved with the write. Do not begin without a recoverable prior representation for every tuple.
6. Apply only the approved tuples to the approved local variable. Do not modify bindings or other metadata.
7. Verify immediately. If verification fails and no intervening drift is present, restore only the exact pre-approved rollback values, verify restoration, report the failed pass, and stop.
8. Add the approved changelog row and reference evidence only after the value change verifies. A rolled-back pass must not be documented as a successful library change.

## Verification

After the write:

- re-read every affected mode and compare exact stored values or alias IDs
- resolve aliases and confirm the resulting type and literal values
- re-resolve every captured bound consumer and compare effective values within the approved tolerance
- inspect visible before/after output where the value affects rendering
- confirm inbound aliases and unapproved modes remain unchanged
- confirm no binding, scope, name, description, mode, collection, or structure changed
- verify changelog and reference evidence
- run a fresh independent `token-readonly-scan` with a new audit ID

Tool success alone is not verification. If external consumers were not observable, report that limitation even after local verification.

## Orchestrator Handoff

When this skill runs inside the audit workflow, return a compact handoff with `skill`, `result_status`, `source_audit_id`, `produced_artifacts`, `blockers`, and `recommended_next_action`. Report observed facts only. The orchestrator owns workflow-step completion and `workflow-state.json`; this skill must not advance the global dashboard itself.

## Final Response

Report approved and successful tuples, any rollback, observed consumer results, unchanged controls, documentation evidence, independent scan status, and remaining limitations or holds.
