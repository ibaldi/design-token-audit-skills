---
name: token-binding-fix
description: Preview, approve, apply, and verify exact Figma node-property bindings to existing variables. Use for binding, rebinding, or explicitly approved unbinding.
---

# Token Binding Fix

Version: 0.8.0

Use this skill only to change bindings between existing Figma node properties and existing variables. Read [references/binding-evidence-contract.md](references/binding-evidence-contract.md) before preparing or applying a binding pass.

## Boundary

This skill supports:

- `Bind`: replace a literal or unbound property with an existing variable binding
- `Rebind`: replace one existing variable binding with another existing variable
- `Unbind`: remove a binding only when that exact operation is separately and explicitly approved
- `No-op`: verify an already correct binding without changing it

Do not create or delete variables, change variable values, modes, scopes, names, descriptions, or aliases, restructure components, detach instances, or perform unrelated documentation cleanup. Create missing variables through `token-creation-proposal`, verify that pass, and only then prepare a separate binding pass.

## Required Input

Require:

- a validated read-only audit using schema `1.5.0`
- a structured binding finding with a stable finding ID and fingerprint
- observable node, page, property, and current-binding evidence
- an existing target variable with stable ID, name, resolved type, collection, relevant mode values, and compatible scope
- for every FLOAT target, the stored or adapter-reported value, effective current value, intended effective value, and target value resolved for the exact consumer node
- documentation readiness for the intended write

Keep the item on hold if the node or property is not observable, the source audit is stale, the target variable does not exist, type or mode compatibility is unclear, a FLOAT target cannot be resolved for the exact consumer, the resolved value differs from the intended effective value, a component-instance restriction would require detaching or restructuring, or consumer impact cannot be bounded.

## Exact Change Tuple

Every write candidate is identified by this immutable tuple:

```text
node_id + property_path + operation + target_variable_id
```

For `Unbind`, use `null` as the target variable ID. Approval for one tuple does not authorize another property on the same node or another finding in the same report.

## Required Preview

Before writing, show:

```text
Preview: Token Binding Fix

Source audit ID and timestamp:
Library and page:
Finding IDs:
Exact node count:
Exact property count:
Node ID and name:
Node type:
Property path:
Current representation:
Operation: Bind | Rebind | Unbind | No-op
Target variable ID and name:
Resolved type and mode coverage:
Scope compatibility:
FLOAT semantic family and stored/adapter value:
Current, resolved-target, and intended effective values:
Tolerance and equivalence result:
Risk and consumer impact:
Unchanged controls:
Changelog row:
Reference evidence:
Verification plan:

Please approve this exact binding pass before I make any changes.
```

List every tuple individually. Do not include `No-op` records in the write count. Name every control node that must remain unchanged.

## Documentation Layout Safety

For changelog rows, reference cards, and other repeating or dynamically sized documentation, use Auto Layout internally unless an observed approved convention requires another model. Preserve existing layout when extending it; converting absolute content to Auto Layout requires a separate node-exact preview of every affected descendant and geometry effect. Absolute coordinates remain valid for deliberate top-level placement, but never position a repeating row or card solely by adding an assumed fixed offset to its neighbor.

Set `layoutMode` before dependent properties, use `AUTO`, `HUG`, and `FILL` only where the node and parent relationship support them, and avoid stretch/grow conflicts. Include layout and sizing properties in the preview. After the documentation write, re-read layout properties and bounds, verify zero overlap and clipping, and capture the complete affected area in a screenshot; screenshot review does not replace structural verification or the successor audit.

## Approved Write Gate

After approval and immediately before writing:

1. Re-read every approved node and target variable.
2. Confirm the node ID, name, type, page, property path, current literal or binding, target variable ID and type, mode coverage, scope compatibility, counts, risk, changelog location, and reference location still match the approved preview.
3. Confirm the requested property is supported by the active Figma write adapter.
4. For every FLOAT target, resolve the variable for the exact consumer node with `variable.resolveForConsumer(node)` or a documented adapter-equivalent operation. Compare that effective value with the intended effective property value using the previewed tolerance. Never derive this from the variable's stored value, UI display, name, scope, or type alone.
5. For opacity, require the current, resolved-target, and intended effective consumer values to be within `0–1`. Treat percentage display and raw adapter representation as separate evidence, not as an implicit conversion rule.
6. Stop and produce a revised preview if consumer resolution is unavailable, the effective values differ, any record drifted, or any tuple cannot be applied atomically and verified.
7. For component instances, use supported instance-property or exposed-property mechanisms only. Never detach an instance or silently edit a protected descendant.
8. Apply only the approved tuples. A partial batch is a failed pass; stop, report exactly what changed, and do not continue with remaining tuples.
9. Add only the approved changelog row and reference evidence.

Never treat a general `Go`, approval for token creation, or approval for a different binding batch as permission for this pass.

## Verification

After the write:

- re-read each approved property and confirm the exact target variable or approved unbound state
- confirm the resolved variable type and relevant mode values remain compatible
- for FLOAT bindings, confirm the post-write effective property value equals the previewed intended value within tolerance, not merely that the variable ID is attached
- compare the approved tuple count with the successful write count
- confirm no unapproved binding changed
- confirm all named `No-op` controls are unchanged
- confirm component and instance integrity without detachment or structural mutation
- verify the changelog row and reference evidence
- compare before/after screenshots when the binding affects visible output
- run a fresh independent `token-readonly-scan`; do not mark the pass complete from write-tool success alone

If verification fails, report the pass as failed or partially applied. Do not improvise a repair outside a new preview and approval.

Changing an existing variable value is outside this skill. Even when a bad binding exposes a likely value error, do not request ordinary approval for a corrective value write. Keep the binding on hold and route the value evidence to a separate `token-value-fix` pass. Its approval never authorizes this binding pass.

## Orchestrator Handoff

When this skill runs inside the audit workflow, return a compact handoff with `skill`, `result_status`, `source_audit_id`, `produced_artifacts`, `blockers`, and `recommended_next_action`. Report observed facts only. The orchestrator owns workflow-step completion and `workflow-state.json`; this skill must not advance the global dashboard itself.

## Final Response

Report approved tuples, successful writes, failed or held tuples, unchanged controls, documentation evidence, visual result, and independent read-only verification status.
