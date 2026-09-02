---
name: token-creation-proposal
description: Prepare exact Figma token-creation proposals for accepted semantic gaps. Use when modes, aliases, scopes, documentation, approval, and verification are required.
---

# Token Creation Proposal

Version: 0.8.0

Use this skill to turn accepted semantic gaps into concrete token creation proposals.

## Rule

Do not create variables or tokens until the exact proposal is approved.

Approval applies only to the exact token IDs or proposed names, collection, modes, values or aliases, scopes, descriptions, documentation, and count shown in the preview.

## Required Input

Require both:

- an accepted semantic-gap record with stable gap ID, evidence, owning layer, nearest existing token, risk, consumer impact, and decision owner
- a validated read-only scan with audit ID, scan timestamp, schema version, validation result, collection and mode coverage, alias coverage, and limitations

If the gap is only possible, the source scan is invalid or stale, the target collection or modes are not observable, or a suitable existing token has not been ruled out, keep the proposal on hold.

## Required Proposal

For every proposed token, include:

- token name
- target collection
- token layer, such as Global, Alias, Platform, Component, or Typography
- type, such as Color, Float, String, Boolean, Effect, or Typography
- modes
- values or aliases per mode
- scopes
- description
- reason this token is needed
- nearest existing token
- consumer impact
- risk level

For every FLOAT token, also state its numeric family (`opacity`, `dimension`, `typography`, `unitless`, or `other`), intended consumer property, effective consumer unit/range, and how the active adapter represents the stored value. Do not copy a node literal into a FLOAT variable merely because the numbers look equal.

## Required Write Preview

Before creating anything, show:

```text
Preview: Token Creation

Source audit:
Accepted gap ID:
Library:
Collection:
Tokens to create:
Modes:
Values or aliases:
Scopes:
Descriptions:
Risk:
Consumer impact:
Changelog:
Reference:
Verification:

Please approve this exact token creation pass before I make any changes.
```

## Documentation Layout Safety

For changelog rows, reference cards, and other repeating or dynamically sized documentation, use Auto Layout internally unless an observed approved convention requires another model. Preserve existing layout when extending it; converting absolute content to Auto Layout requires a separate node-exact preview of every affected descendant and geometry effect. Absolute coordinates remain valid for deliberate top-level placement, but never position a repeating row or card solely by adding an assumed fixed offset to its neighbor.

Set `layoutMode` before dependent properties, use `AUTO`, `HUG`, and `FILL` only where the node and parent relationship support them, and avoid stretch/grow conflicts. Include layout and sizing properties in the preview. After the documentation write, re-read layout properties and bounds, verify zero overlap and clipping, and capture the complete affected area in a screenshot; screenshot review does not replace structural verification or the successor audit.

## Approved Write Gate

Before creating an approved token:

1. Verify that changelog and reference documentation are ready.
2. Re-read the target collection, ordered modes, existing names, nearest tokens, alias targets, scopes, and documentation locations.
3. Compare the current records with the approved preview and source audit.
4. Stop and request a revised proposal if the proposed name now exists or any collection, mode, alias, scope, count, documentation, or risk assumption drifted.
5. Create only the approved tokens and documentation.
6. Verify the result before proposing another pass.

Never combine token creation with node-binding changes, scope changes to existing tokens, renames, deletions, mode edits, architecture changes, or unrelated documentation cleanup.

After the creation pass verifies successfully, use a new read-only state and `token-binding-fix` for any node-property mappings. Creation approval does not authorize those bindings.

## Verification

After approval and creation, verify:

- exact tokens exist
- correct collection
- correct type
- correct modes
- correct values or aliases
- correct scopes
- descriptions present
- changelog row present
- reference card or frame visible
- no unexpected variables were created
- for FLOAT tokens intended for later binding, the stored value and `resolveForConsumer` or adapter-equivalent value are recorded separately on representative intended consumers

If a FLOAT token does not resolve to the intended effective value, mark creation verification failed and do not proceed to a binding proposal. Correcting that existing variable value is not authorized by this skill; after a fresh read-only scan, route it to a separate `token-value-fix` pass.

## Orchestrator Handoff

When this skill runs inside the audit workflow, return a compact handoff with `skill`, `result_status`, `source_audit_id`, `produced_artifacts`, `blockers`, and `recommended_next_action`. Report observed facts only. The orchestrator owns workflow-step completion and `workflow-state.json`; this skill must not advance the global dashboard itself.

## Final Response

Summarize what was proposed, what was approved, what was created, and what remains on hold.
