---
name: ibaldi-design-token-audit
description: Safely audit and improve Figma design-token libraries. Use for variable inventories, scopes, semantic gaps, hardcoded values, bindings, value corrections, documentation, and baseline verification.
metadata:
  author: ibaldi
  version: "0.1.0"
  source-suite: design-token-audit-skills
  source-suite-version: "0.9.1"
---

# Ibaldi Design Token Audit

Figma port version: `0.1.0`

Source suite version: `0.9.1`

Use this skill as the Figma-native companion to the validated multi-file Claude skill suite. Audit and improve variables, token usage, and related documentation in the current Figma file through small, evidence-backed passes.

## Core Rule

Start read-only. Before every write, show an exact preview and wait for explicit approval for that pass. After approval, re-read the targets, apply only the approved change, verify independently, and document it.

A write includes creating, editing, renaming, moving, reparenting, binding, unbinding, or deleting any variable, collection, mode, node, changelog entry, or reference item.

## Use This Skill When

Invoke this skill for:

- a current-state audit of Figma variables or token usage
- variable collection, mode, scope, description, naming, or alias inspection
- hardcoded-value and semantic-gap discovery
- missing, incorrect, or suspicious node-property bindings
- a proposed scope, token-creation, existing-token value, or node-binding fix
- changelog and reference-documentation readiness
- final baseline verification or release handoff

Do not use this skill as a general visual critique, a component redesign workflow, or permission to clean up unrelated file content.

## Capability Boundary

This single-file Figma edition has no bundled scripts, schemas, fixtures, or external reference files. It cannot claim the machine-validated JSON conformance provided by the Claude suite.

Use it with the Figma agent in Figma Design or Figma Make. Read-only work requires file access; approved writes require edit access and observable write and verification capabilities.

Before acting, state which capabilities are observable in the current session:

- local variable collections, variables, modes, values, aliases, scopes, and descriptions
- node traversal and bound-variable references
- component and instance structure
- effective variable values for exact consumer nodes
- document nodes, text, layout properties, and bounds
- screenshots or rendered visual inspection
- write support, undo checkpoints, and post-write verification
- external Figma consumers and code consumers

Mark unavailable evidence `not_observable`. Never infer a value, binding, consumer, or absence from missing access. If core collection or variable inventory is unavailable, stop with `blocked`.

When an observed node binding points outside the local inventory, preserve the binding ID and classify the reference as a remote library variable, a stale local reference, or unresolved. An individual unresolved reference does not invalidate the whole read-only result: mark usage coverage `partial`, state the affected nodes and paths, and hold every automatic fix or deletion decision involving it.

## Process Navigator

Maintain the current workflow state in the conversation. Show the navigator when starting or resuming, after material findings, before approval, after verification, and at handoff.

Use this format:

```text
DESIGN TOKEN AUDIT

Current phase: P1 | P2 | P3 | P4
Completed: [phase or step IDs]
Now: [current step]
Open: findings N | binding candidates N | gaps N | holds N
Blockers: [none or concise list]
Next: [exactly one recommended action]
Decision needed: [exact approval or none]
```

Do not show a total percentage while discovery can still add findings. Finding IDs and pass IDs are not process-step IDs. Resuming a conversation never restores or broadens an earlier write approval.

## Workflow

### P1 — Read-only Diagnosis

1. `P1.1` Identify the file, relevant pages or selection, expected collections and modes, and observable capabilities.
2. `P1.2` Inspect and record the current state without changing anything.
3. `P1.3` Cross-check counts, evidence, coverage, limitations, and report consistency.
4. `P1.4` Always run both scope validation and semantic-gap assessment, including the hardcoded-value sweep. Attempt both even when the user did not request them separately.

Do not proceed when the evidence report is stale, internally inconsistent, or missing core inventory.

### P2 — Documentation Readiness

Verify that the file has a usable changelog location and visible reference evidence for the intended write. If documentation is not ready, prepare a separate documentation-readiness preview. Do not combine its structural changes with a token fix.

After a documentation write, rerun the relevant read-only inspection before another pass.

### P3 — Approved Fix Passes

Run one approved pass at a time. This edition supports only:

- scope fixes on existing variables
- creation of approved new variables
- corrections to exact mode values of existing local variables
- exact node-property binding, rebinding, or explicitly approved unbinding

Token creation, value correction, scope change, and node binding are separate passes with separate previews and approvals. A newly created or corrected variable must be verified before it can be the target of a binding preview.

Keep architecture, mode, naming, orphan deletion, and description writes on hold. Report their evidence, but never offer to perform them as a manual exception or outside the guardrails.

### P4 — Baseline Verification

Reinspect totals, modes, values, scopes, aliases, bindings, documentation, visual integrity, and all hold items. Finish with a concise handoff and one recommended next action, or state that the supported workflow is complete.

## Read-only Audit Checklist

Record observed counts and stable IDs wherever available:

- file name, file key, relevant pages, selected scope, and timestamp
- local collections and ordered modes
- variable totals by collection and resolved type
- missing mode values and unresolved aliases
- scopes by collection, including exact `ALL_SCOPES` and empty scope arrays
- empty descriptions and existing description patterns
- default/AX and Light/Dark sanity with evidence-backed expectations
- Typography values and scopes without changing them
- duplicates, whitespace defects, and inconsistent naming patterns
- local inbound alias counts and their coverage
- node usage on every fully inspected page
- potential orphan candidates with external usage explicitly unknown unless searched
- changelog existence, format, ordering, authors, and type values
- reference-card or reference-frame status
- documentation layout model, overlap, clipping, and complete-area visual evidence

When node traversal is observable, inspect bindable property families declared by the available Figma capabilities rather than deriving the property list from existing tokens:

- simple node fields such as opacity, corner radii, padding, spacing, and dimensions
- indexed paints for fills and strokes
- supported effect subproperties
- supported layout-grid subproperties
- typography properties
- supported component properties

Keep rotation, blend mode, and Auto Layout sizing as ordinary design or layout observations unless the active Figma capability explicitly supports them as variable-bindable properties.

For every inspected property, distinguish bound, literal, mixed or unsupported, and not observable. Capture literals even when no existing variable matches them.

## Finding Rules

Every finding needs:

- stable finding ID
- rule applied
- affected collection, variable, node, property, page, and mode IDs where relevant
- observed and expected state
- evidence source
- confidence: high, medium, or low
- severity: critical, high, medium, low, or info
- status: open, needs review, held, or not actionable
- limitations
- recommendation

Confidence describes certainty in the observation. Severity describes demonstrated impact. Use `critical` only for demonstrated active-consumer breakage or an unsafe active-consumer outcome. Unknown consumers require conditional risk wording and cannot justify `critical` by themselves.

Never treat a zero value, repeated literal, broad scope, empty scope array, or missing local usage as proof of an error by itself.

## Scope Assessment

Evaluate intended use from token semantics, type, observed consumers, peer patterns, and documented conventions. Do not infer intent from the token name alone.

Treat explicit `ALL_SCOPES`, an empty scope array, and unavailable scope metadata as different states unless observed Figma behavior proves equivalence.

Typography and accessibility-related scopes are high risk. Keep uncertain narrowing on hold. A scope write must not change names, values, aliases, modes, descriptions, bindings, or architecture.

## Semantic Gap Assessment

A confirmed semantic gap requires recurring or explicitly system-level intent, sufficient component or product-flow evidence, no suitable token in all observable relevant libraries, a clear owning layer, and compatible value semantics.

Classify candidates as:

- confirmed semantic gap
- possible semantic gap or needs review
- not a gap
- design decision needed
- not observable

Repeated equal literals or variants of one component do not prove a system-level gap. Group evidence by semantic intent and property semantics, not raw value alone.

When the system has an established foreground-on-background convention, check peer semantic roles for missing counterparts. Establish the convention through explicit documentation, multiple consistent pairs, or equally strong architecture evidence. One `bg/*` and `text/on-*` pair, a fill scope, or a matching word is not enough.

A danger-colored text token for use on a neutral surface does not automatically satisfy an on-danger-background role. Search all observable relevant collections and libraries before proposing a new foreground role.

## Required Preview

Before every write, show:

```text
PREVIEW — [pass type and pass ID]

Source audit and timestamp:
File and page:
Exact variable count:
Exact node count:
Exact property count:
Finding IDs:
Stable target IDs and names:
Current state:
Proposed state:
Relevant modes and values:
Consumer impact and risk:
Unchanged controls:
Documentation nodes to create or change:
Changelog row:
Reference evidence:
Recovery plan:
Verification plan:

Approve this exact pass before I make any changes.
```

List every tuple separately. Enumerate every documentation node, including nested text and shapes, with type, parent or location, and total count. If a new convention is proposed because none exists, label it as a design decision rather than observed fact.

A general `Go` applies only to the currently displayed preview. Any drift, target change, count change, new risk, or changed recovery plan requires a revised preview and new approval.

## Scope Fix

Immediately before writing, re-read the exact variable ID, name, type, collection, current scopes, observed consumers, and target scopes. Stop on drift or ambiguous intent.

Apply only the approved scope changes. Verify exact scopes and unchanged names, values, aliases, modes, descriptions, and bindings.

## Token Creation

Create a variable only from an accepted semantic gap with an approved name, owning collection, type, modes, values or aliases, scopes, description, risk, and documentation.

Recheck all observable local and enabled libraries immediately before creation. Stop if a suitable token now exists or the intended collection is unresolved.

Never bind nodes in the creation pass. Verify the new variable in a fresh read-only state before preparing a separate binding pass.

## Existing-token Value Fix

Default to one existing local variable per pass. Require exact current and proposed value or alias for every affected mode, complete observable local alias and binding impact, predicted consumer effects, and exact pre-approved rollback values.

Do not infer numeric conversion from UI display, name, scope, or type. For opacity, keep stored representation, effective consumer value, and intended value separate; effective opacity must remain within `0–1`.

After writing, verify every mode value and sampled affected consumers. If verification fails and there has been no intervening drift, execute only the approved rollback and verify it. Otherwise stop and report partial application.

Never combine a value correction with token creation or node binding.

## Node Binding Fix

Identify every candidate by this immutable tuple:

```text
node ID + property path + operation + target variable ID
```

Supported operations are bind, rebind, explicitly approved unbind, and no-op verification. Approval for one tuple never authorizes another property or node.

Require observable current representation, exact target variable, matching resolved type, relevant mode coverage, compatible scope intent, and effective value for the exact consumer. For FLOAT targets, compare current, stored, consumer-resolved target, and intended effective values with an explicit tolerance.

Do not detach instances or silently edit protected descendants. Use only supported instance or exposed-property mechanisms.

### Relational Safety

When a binding can change the effective rendered background behind text or a meaningful graphical object:

1. Trigger from the actual property path, rendered geometry, and resolved values, not variable name or scope alone.
2. Inspect affected nested descendants and overlapping foreground nodes. Do not limit inspection to direct children.
3. Resolve current and proposed effective foreground and background colors per relevant mode, including observable opacity and compositing.
4. Apply WCAG AA thresholds: `4.5:1` for normal text, `3:1` for applicable large text, and `3:1` for meaningful UI indicators or graphical objects.
5. Record current ratio, proposed ratio, threshold, delta, status, and limitations.

Do not calculate from raw token colors when gradients, images, masks, blends, unresolved paints, or unknown underlying surfaces prevent deterministic effective-color resolution. Mark the result `not_observable` and keep the tuple on hold.

Do not present a tuple as ordinarily approval-ready when it creates a new known accessibility failure. An existing failure or improved-but-still-failing result requires explicit approval naming that risk. Approval for the background tuple never authorizes changing foreground content.

Report non-mechanical relationships only when documented rules, observed peer patterns, component conventions, or measurable geometry support them. Do not invent speculative coupling risks.

## Documentation Safety

Every approved library write requires the approved changelog row and visible reference evidence. Preserve the observed documentation model unless a separately approved structural pass changes it.

For new or repeating documentation structures, use Auto Layout where supported. Do not position a new row or card by adding an assumed fixed coordinate offset to its neighbor.

Before a structural documentation write:

1. Assign an attempt ID.
2. Capture every affected pre-existing node ID, parent ID, sibling index, relevant layout properties, and bounds.
3. Record every node created during the attempt by stable ID; names never prove ownership.
4. Resolve fonts, parent support, node types, and other preconditions before mutation.
5. Establish an undo checkpoint when supported; otherwise state the limitation and retain the parent/index restoration map.

For each Auto Layout wrapper:

1. Create the empty wrapper.
2. Configure the intended parent's layout mode.
3. Append the wrapper to the parent.
4. Re-read and verify the parent relationship and non-`NONE` layout mode.
5. Only then set child-only `FILL` sizing.
6. Verify the empty scaffold before reparenting existing content.
7. Reparent only previewed nodes and verify IDs, order, parents, layout, bounds, overlap, and clipping before continuing.

One tool call or script is not atomic when an exception can leave earlier mutations applied.

On failure, stop remaining mutations. Use the approved undo operation when available; otherwise restore pre-existing nodes to captured parents and sibling indices before cleanup.

Resolve cleanup targets only from the current attempt's recorded IDs. Enumerate the complete subtree before a cascading delete. Remove it only when its root and every descendant were created by the same attempt. If any node predates the attempt, has unknown provenance, or cannot be inspected, do not delete the subtree; report exact IDs and current parents.

Attempt cleanup may only restore the approved pre-write state. It is not orphan deletion.

## Verification

After every approved write:

- re-read each exact target and compare it with the preview
- compare approved count with successful count
- verify all named unchanged controls
- verify relevant modes, values, aliases, scopes, bindings, components, and instances
- recompute effective FLOAT and relational-safety results where applicable
- verify changelog and reference evidence
- inspect layout properties and bounds for zero overlap and clipping
- capture a complete-area visual check when visible output changed
- run a fresh independent read-only inspection before marking the pass complete

Tool success alone is not verification. If verification fails, report failed or partially applied status and do not improvise another write.

## Final Report

Separate:

- observed facts
- heuristic findings
- approved and completed changes
- failed or partially applied changes
- holds and not-observable areas
- external consumer limitations
- documentation evidence
- one recommended next action

Do not claim machine-validated audit JSON, complete external usage coverage, or equivalence with the multi-file Claude suite. Describe this skill as the Figma-native companion edition derived from source suite v0.9.1.
