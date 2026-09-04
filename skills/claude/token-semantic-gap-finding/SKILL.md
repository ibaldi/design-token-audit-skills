---
name: token-semantic-gap-finding
description: Find evidence-backed semantic token gaps without creating tokens. Use for hardcoded values, primitive usage, missing states, or incomplete semantic coverage.
---

# Token Semantic Gap-finding

Version: 0.8.1

Use this skill to identify semantic token gaps. This pass is read-only.

## Rule

Do not create tokens during gap-finding. Produce evidence-backed findings and proposals only.

## Required Input

Start from a validated read-only scan and record its audit ID, scan timestamp, schema version, validation result, coverage, and limitations.

Read its validated `property_coverage`. Complete semantic-gap coverage is impossible when a relevant adapter-declared property family is partial, unsupported, not observable, or failed; propagate that limitation into the Phase-1 assessment.

Gap confirmation also requires observable component, state, usage, or product-flow evidence. If this evidence is partial or unavailable:

- mark the affected check `not observable` or classify it as `Possible semantic gap / needs review`
- state which pages, components, states, or consumers were not inspected
- do not classify a recurring intent as confirmed

If the core token inventory is invalid or stale, stop and refresh the read-only scan.

## Mandatory Hardcoded-value Sweep

Run this assessment whenever the orchestrator reaches `P1.4`; it is not optional merely because the user did not request it separately. When node traversal is observable, inspect all in-scope component nodes and relevant bindable properties, including literals with no existing-variable match. Record component/state context and traversal coverage rather than reviewing only values already surfaced as binding candidates.

Group candidates by semantic intent and property semantics, not by raw value alone. Before classifying a gap, check suitable existing tokens in every observable relevant local or enabled library. Distinguish separate component consumers from variants or instances of the same component; repeated equal literals alone do not prove a system-level semantic gap.

Use `partial` or `not_observable` when coverage is insufficient. Use `inapplicable` only after an attempted assessment establishes a concrete reason such as no in-scope components or no relevant bindable properties. "Not requested", "not mentioned", time constraints, and effort are never valid reasons.

## Semantic Foreground Pairing Check

When observable evidence shows that tokens serve as semantic backgrounds and the design system has an established foreground-on-background convention, compare peer semantic roles for missing foreground counterparts. Establish the convention from explicit documentation, multiple consistent pairs, or equally strong architecture evidence. One coincidental pair, a `FRAME_FILL` or `SHAPE_FILL` scope, or a token name containing `bg` is not sufficient by itself.

Search all observable relevant local and enabled libraries because background and foreground roles may live in different collections or layers. Check semantic purpose, not substring similarity: a token for danger-colored text on a neutral surface does not automatically satisfy a foreground-on-danger-background role.

Classify a missing counterpart as `Possible semantic gap / needs review` unless recurring active usage, clear owning-layer evidence, compatible mode/value semantics, and the existing confirmation rules support a confirmed gap. If emitted into the audit JSON, use the existing `other` category with stable `rule_id: missing-semantic-foreground-pairing`; do not add a new schema category in this release.

## What Counts As A Semantic Gap

A semantic gap exists when recurring design intent is represented through primitives, local styles, detached values, hardcoded component decisions, or inconsistent aliases instead of a clear semantic token.

Examples:

- destructive action background uses a primitive red value
- selected navigation item uses a local fill
- disabled text color appears in multiple components without a semantic foreground token
- focus, validation, warning, success, selected, disabled, pressed, hover, loading, or elevated states are inconsistent
- platform-specific surfaces are not represented in the platform token layer
- a component has multiple states, but only default state has token coverage

## Classification

Classify each finding as:

- **Confirmed semantic gap:** recurring or explicitly system-level intent, no suitable token in all observable relevant libraries, clear owning layer, compatible value semantics, and sufficient component or product-flow evidence. Multiple variants or instances of one component and a shared raw value do not by themselves satisfy recurrence.
- **Possible semantic gap / needs review:** pattern found, but ownership, naming, or existing-token fit is uncertain.
- **Not a gap:** existing token covers it, usage is one-off, or tokenizing adds unnecessary complexity.
- **Design decision needed:** behavior is inconsistent or unresolved.
- **Not observable:** available capabilities cannot establish the required component, usage, or library evidence.

If the proposed collection or owning layer is unresolved, classify the candidate as `Design decision needed` or `Possible semantic gap / needs review`; do not present it as a write-ready confirmed gap.

## Candidate Format

```text
Semantic gap candidate

Source audit:
Intent:
Evidence:
Coverage and limitations:
Current representation:
Nearest existing token:
Why this is a gap:
Proposed token name:
Proposed collection/layer:
Type:
Modes and values/aliases:
Scopes:
Description:
Risk:
Consumer impact:
Recommendation:
```

## Summary Format

```text
Confirmed gaps:
Possible gaps / needs review:
Not gaps:
Design decisions needed:
Recommended creation proposals:
Recommended mapping fixes:
Recommended holds:
```

## Orchestrator Handoff

When this skill runs inside the audit workflow, return a compact handoff with `skill`, `result_status`, `source_audit_id`, `produced_artifacts`, `blockers`, and `recommended_next_action`. Include a `phase1_assessment` record containing `status`, `artifact_id`, `coverage`, and `reason` for `semantic_gap_finding`. Report observed facts only. The orchestrator owns workflow-step completion and `workflow-state.json`; this skill must not advance the global dashboard itself.

## Next Step

If a gap should become a token, move to `token-creation-proposal`. If an existing variable already covers the intent but a node uses a literal or the wrong variable, route the mapping fix to `token-binding-fix`. If the existing variable itself has the wrong mode value, route a separately evidenced correction to `token-value-fix`. Do not create, correct, or bind anything without the corresponding separate approved pass.
