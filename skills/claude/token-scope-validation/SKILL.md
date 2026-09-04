---
name: token-scope-validation
description: Validate Figma variable scopes after a valid read-only scan. Use for broad, narrow, missing, mismatched, Typography, accessibility, or ALL_SCOPES reviews.
---

# Token Scope Validation

Version: 0.8.1

Use this skill to validate whether token scopes match intended usage. `ALL_SCOPES` is only one finding type; the broader task is scope-intent validation.

## Required Input

Start from a validated read-only scan. Do not run scope validation if collection, variable, type, scope, and coverage evidence are missing or invalid.

If the source scan is missing scope data, report scope validation as blocked or `not observable`.

Record the source audit ID, scan timestamp, schema version, validation result, and relevant coverage. If any of these are missing, do not prepare a write-ready proposal.

## Rule

Do not change scopes during validation. Produce findings and proposed scope changes only.

Approval applies only to the exact previewed scope pass. It does not approve another collection, token set, or documentation change.

## What To Validate

Check whether scopes are:

- too broad, including `ALL_SCOPES`
- too narrow for the intended usage
- missing an expected usage scope
- irrelevant to token type or intent
- inconsistent with nearby peer tokens
- inconsistent with collection or naming patterns
- inconsistent with description, when descriptions are available
- affected by Typography or AX/accessibility exceptions
- accepted documented exceptions

Treat the exact scope representation as evidence. An empty scope array is not interchangeable with explicit `ALL_SCOPES`; do not call it unrestricted unless the active adapter contract or observed Figma behavior establishes that meaning. If the semantics of an empty array are unavailable, classify them as `not observable` or `needs design decision` rather than inferring a mismatch.

Use [references/scope-intent-heuristics.md](references/scope-intent-heuristics.md) for common intent signals and risk rules.

## Intent Classification

Classify likely token intent from multiple signals:

- variable type
- collection name
- token path/name
- description
- existing scopes
- peer tokens
- known platform/library conventions

Never treat the token name alone as proof. Use wording such as "appears intended for" when the evidence is heuristic.

Common intent groups:

- background / surface
- foreground / text
- border / stroke
- radius / corner
- spacing / gap / padding
- sizing / width / height
- opacity
- effect / elevation
- typography
- icon
- state, such as disabled, selected, focused, warning, error, success, pressed, or hover

## Finding Classification

Classify each issue as:

- **Scope mismatch:** current scope conflicts with observed intent.
- **Scope too broad:** token is available in more properties than intended.
- **Scope too narrow:** token is not available where intended.
- **ALL_SCOPES review:** token has `ALL_SCOPES`; decide whether it is intentional.
- **Typography / AX exception:** broad or unusual scope may be intentional; hold unless explicitly approved.
- **Accepted exception:** unusual scope is documented and should not be changed.
- **Needs design decision:** intent is unclear or inconsistent.

## Risk Classification

High risk:

- Typography scopes
- AX/accessibility-related sizing or text behavior
- production-used tokens
- cross-platform semantic tokens
- tokens with uncertain consumer usage
- scope changes that may hide a token from existing component workflows
- broad batch changes
- documented exceptions

Medium risk:

- non-Typography scope narrowing with clear evidence
- adding a missing expected scope
- aligning a small peer group with clear intent

Low risk:

- read-only findings
- documentation-only recommendations
- obvious proposals that are not applied

## Candidate Format

```text
Scope validation candidate

Token:
Collection:
Type:
Current scopes:
Likely intent:
Evidence:
Issue:
Proposed scopes:
Risk:
Consumer impact:
Recommendation:
Confidence:
Limitations:
```

## Write Preview Format

Before changing scopes, show:

```text
Preview: Scope Validation / Scope Change

Source audit:
Library:
Collection:
Affected tokens:
Current scopes:
Proposed scopes:
Reason:
Risk:
Consumer impact:
Changelog:
Reference:
Verification:

Please approve this exact scope-change pass before I make any changes.
```

## Documentation Layout Safety

For changelog rows, reference cards, and other repeating or dynamically sized documentation, use Auto Layout internally unless an observed approved convention requires another model. Preserve existing layout when extending it; converting absolute content to Auto Layout requires a separate node-exact preview of every affected descendant and geometry effect. Absolute coordinates remain valid for deliberate top-level placement, but never position a repeating row or card solely by adding an assumed fixed offset to its neighbor.

Set `layoutMode` before dependent properties, use `AUTO`, `HUG`, and `FILL` only where the node and parent relationship support them, and avoid stretch/grow conflicts. Include layout and sizing properties in the preview. After the documentation write, re-read layout properties and bounds, verify zero overlap and clipping, and capture the complete affected area in a screenshot; screenshot review does not replace structural verification or the successor audit.

For structural documentation writes and recovery after an error, read and follow [references/documentation-structural-write-safety.md](references/documentation-structural-write-safety.md). Configure the parent, append and verify an empty wrapper, and only then set child-only `FILL` sizing or reparent existing content. Track attempt-created nodes by ID, not name; never remove a cleanup subtree containing a pre-existing or unknown-provenance node.

## Approved Write Gate

Before applying an approved scope change:

1. Verify that changelog and reference documentation are ready for this pass.
2. Re-read every affected token's ID, name, collection, type, scopes, modes, and relevant exception metadata.
3. Compare the current records with the approved preview and source audit.
4. Stop and request a revised preview if any affected record, count, scope, mode, exception, or consumer-risk assumption drifted.
5. Apply only the approved scope values to the approved token IDs.
6. Verify and document the pass before proposing another write.

Never combine a scope write with variable-value, node-binding, naming, mode, description, orphan, architecture, or token-creation changes.

## Verification

After an approved scope change, verify:

- exact affected token count
- each token has the approved scopes
- no unapproved tokens changed
- Typography and AX exceptions remain untouched unless explicitly approved
- changelog row exists, if the library was changed
- reference card or frame exists, if the library was changed
- source scan and post-change verification are documented

## Orchestrator Handoff

When this skill runs inside the audit workflow, return a compact handoff with `skill`, `result_status`, `source_audit_id`, `produced_artifacts`, `blockers`, and `recommended_next_action`. Include a `phase1_assessment` record containing `status`, `artifact_id`, `coverage`, and `reason` for `scope_validation`. Report observed facts only. The orchestrator owns workflow-step completion and `workflow-state.json`; this skill must not advance the global dashboard itself.

## Final Response

Summarize scope findings by risk:

- high-risk holds
- medium-risk proposals
- low-risk observations
- accepted exceptions
- blocked / not observable areas
- recommended next pass
