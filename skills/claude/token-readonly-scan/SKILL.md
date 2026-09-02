---
name: token-readonly-scan
description: Audit a Figma token library read-only with canonical snapshots. Use for inventory, bindings, coverage, modes, aliases, usage evidence, or baselines.
---

# Token Read-only Scan

Version: 0.8.0

Use this skill to inspect a design token library without changing anything.

Before inspecting Figma, read and follow:

- [references/figma-adapter-contract.md](references/figma-adapter-contract.md) to negotiate capabilities and select a non-blocking read path
- [references/canonical-figma-token-model.md](references/canonical-figma-token-model.md) to normalize source data before applying audit rules
- [references/figma-adapter-mappings.md](references/figma-adapter-mappings.md) to map Plugin API, MCP, API, export, or mixed sources
- [references/figma-execution-contract.md](references/figma-execution-contract.md) for collection, derivation, evidence, and coverage
- [references/audit-output-contract.md](references/audit-output-contract.md) for the versioned Markdown and JSON outputs
- [references/property-traversal-contract.md](references/property-traversal-contract.md) for the adapter-derived bindable-property matrix and coverage rules

## Rule

Do not write, rename, delete, create, move, or edit any Figma variable, token, node, changelog row, or reference card.

Do not infer fields the available Figma access cannot expose. Mark them `not observable` and include them in the coverage statement.

Do not run audit rules directly on adapter-specific responses. Normalize and integrity-check the canonical snapshot first, then gate each rule by its required capabilities.

When the canonical snapshot is saved as a file, run `python3 scripts/validate_snapshot.py <snapshot.json>` before applying audit rules.

## Scan Checklist

Report:

- file key and relevant pages
- local variable collections
- modes per collection
- variable counts by collection
- variable counts by type
- empty descriptions
- existing description patterns
- missing mode values
- scopes by collection
- tokens with `ALL_SCOPES`
- Light/Dark or default/AX sanity
- suspicious AX values, especially zero values
- Typography values and scopes, without changing them
- duplicate names
- leading or trailing spaces
- double spaces
- unwanted spaces around hyphens
- legacy or inconsistent naming patterns
- unresolved aliases
- local inbound alias counts
- possible orphan candidates
- changelog existence and format
- changelog sort order
- author and type values
- reference card or frame status
- documentation layout model, dynamic-content safety, overlap, clipping, and screenshot evidence when document traversal is observable
- node-property literals, including literals with no existing-variable match, plus literals that match existing variables, mismatched bindings, and already-correct no-op controls when node traversal is observable

Derive the traversal property set from the adapter capability declaration, not from tokens or bindings present in the file. Account for all six contract families: simple node fields, paints, effects, layout grids, typography, and component properties. Report every declared property as complete, partial, not applicable, or failed with eligible and inspected counts. Never use `numeric_semantics.family` as proof that a property was searched.

Do not classify `rotation`, `blendMode`, `layoutSizingHorizontal`, or `layoutSizingVertical` as variable-bindable properties under the current canonical profile. They may remain ordinary design or layout observations.

## Output

Produce both required representations from the same evidence:

1. a concise Markdown report
2. one JSON object with `schema_version: 1.5.0`

Include structured `documentation_readiness` with `layout_structure` and `visual_integrity` checks for both changelog and reference documentation, `derived_metrics` for local inbound aliases, description patterns, and scopes by collection, validated `property_coverage`, plus `binding_findings` and `binding_summary`. Validate that inventory, derived metrics, documentation status, property coverage, binding counts, and general summary counts are derivable from the captured evidence and findings before delivering the report.

A documentation layout passes only when dynamically sized content is safe under its observed layout model and bounds inspection finds no overlap or clipping. Require screenshot evidence of the complete affected area for `visual_integrity: pass`; screenshots do not replace layout-property and bounds evidence.

Binding findings are read-only evidence and proposals, never write authorization. Route supported binding changes to a separate `token-binding-fix` preview and approval after this scan validates successfully.

Do not treat the binding scan as the complete hardcoded-value assessment. Preserve unmatched in-scope literals and their node, property, component/state, value, and traversal evidence so the mandatory semantic gap-finding pass can evaluate recurring intent. Absence of a matching local variable is a candidate signal, not proof that a new token is required.

For every FLOAT binding target, capture numeric semantics and resolve the target variable for the exact consumer node. Record current, stored/adapter, resolved-target, and intended effective values separately. A type match is insufficient; hold the finding when consumer resolution is unavailable or differs from the intended effective value.

When evidence indicates that an existing local variable's mode value is wrong, report the observation without changing it. A correction requires a separate validated `token-value-fix` evidence record, exact preview, approval, rollback, and post-write scan.

Use the exact field names and object shapes in the output contract. Do not replace them with plausible alternatives such as `file`, `scan_timestamp`, `mode`, `changes_made`, `inspection_method`, or `recommended_next_steps`.

When the JSON is saved as a file, run:

```bash
python3 scripts/validate_audit_json.py <audit.json>
```

Correct every reported error before delivery. If the contract or validator is unavailable, cannot run, or reports an error, label the artifact as an **unvalidated draft**, set the scan status to `blocked` when a valid JSON artifact cannot be produced, and stop. Do not claim schema conformance, baseline readiness, or permission to begin a later pass. Manual review does not replace this gate.

If local inbound aliases were not counted exhaustively for every captured variable and mode, set `derived_metrics.local_inbound_aliases.status` to `partial` and state the limitation. Do not derive a complete no-inbound list or orphan candidates from missing counts.

Apply severity conservatively. `critical` requires demonstrated active-consumer breakage or an unsafe value with active-consumer evidence. When consumer usage is not observable, describe impact conditionally and do not elevate a value issue above `high` solely because its literal value looks suspicious. Keep `severity` as the only classification; `risk` is explanatory prose and must not contain a conflicting risk label.

## Orchestrator Handoff

When this skill runs inside the audit workflow, return a compact handoff with `skill`, `result_status`, `source_audit_id`, `produced_artifacts`, `blockers`, and `recommended_next_action`. Report observed facts only. The orchestrator owns workflow-step completion and `workflow-state.json`; this skill must not advance the global dashboard itself.

## Final Response

Clearly state that the scan was read-only and that no changes were made. Distinguish observed facts from heuristic findings and unknown external consumer usage.

Recommend only supported next passes. Architecture, mode, naming, orphan, and description writes remain on hold; never offer to perform them as a manual one-off or "outside the guardrails."
