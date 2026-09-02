# Audit Output Contract

Produce two synchronized outputs for every read-only scan:

1. a concise human-readable Markdown report
2. one machine-readable JSON object conforming to this contract

Do not put comments in the JSON. Use `null` only for a known field with no value. Use `not_observable` or `not_configured` status values for unavailable or unspecified checks; do not encode either state as an empty array or zero.

## Schema Version

Set `schema_version` to `1.5.0`. Version 1.5 adds required adapter-derived property traversal coverage. Version 1.4 added structured documentation layout and visual-integrity checks. Version 1.3 added numeric semantics and resolved-consumer equivalence for FLOAT binding targets. Version 1.2 added structured node-property binding findings and a binding summary. Version 1.1 added structured documentation readiness and derived scan metrics. A consumer may reject unsupported major versions. Additive fields require a minor version; incompatible changes require a major version.

## Top-level Shape

```json
{
  "schema_version": "1.5.0",
  "audit_id": "dta-20260811T173000Z-abc123",
  "audit_type": "figma_token_readonly_scan",
  "status": "complete_with_limitations",
  "read_only": true,
  "started_at": "2026-08-11T17:30:00Z",
  "completed_at": "2026-08-11T17:31:12Z",
  "source": {},
  "inspection": {},
  "coverage": {},
  "inventory": {},
  "documentation_readiness": {},
  "derived_metrics": {},
  "property_coverage": {},
  "binding_findings": [],
  "binding_summary": {},
  "findings": [],
  "summary": {},
  "recommended_next_pass": null
}
```

Use UTC ISO-8601 timestamps with `Z` or `+00:00`.

Allowed top-level `status` values:

- `complete`
- `complete_with_limitations`
- `blocked`
- `failed`

Use `complete` only when every configured target and required field was observed and every declared page was fully traversed. A scan may be useful while `complete_with_limitations`.

## Source

```json
{
  "file_key": "string",
  "file_name": "string",
  "branch_or_version": null,
  "pages_requested": [{"id": "1:2", "name": "Foundations"}],
  "collections_expected": null,
  "export_fingerprint": null
}
```

Use `export_fingerprint` for user-supplied exports when a checksum is available. Do not invent branch, version, or expected collections.

## Inspection

```json
{
  "method": "figma_plugin_api",
  "tool_name": "string",
  "capabilities": ["local_variables", "document_nodes"],
  "unavailable_operations": ["external_consumer_search"]
}
```

Allowed `method` values:

- `figma_plugin_api`
- `connected_figma_tool`
- `user_supplied_export`
- `mixed`

Map canonical adapter `source_type` to audit inspection `method` explicitly:

| Adapter `source_type` | Audit inspection `method` |
| --- | --- |
| `plugin_api` | `figma_plugin_api` |
| `mcp` or `api` | `connected_figma_tool` |
| `export` | `user_supplied_export` |
| `mixed` | `mixed` |

## Coverage

```json
{
  "collections": {"status": "complete", "observed": 3, "expected": 3},
  "variables": {"status": "complete", "captured": 240, "failed": 0},
  "pages": {
    "status": "partial",
    "fully_traversed_ids": ["1:2"],
    "not_traversed_ids": ["1:3"]
  },
  "aliases": {"status": "complete", "unresolved_remote": 2},
  "external_consumers": {
    "status": "not_observable",
    "searched": [],
    "not_searched": ["consumer Figma files", "code repositories"]
  },
  "unobservable_fields": ["remote variable values"],
  "limitations": ["Remote alias targets could not be inspected"]
}
```

Allowed coverage `status` values:

- `complete`
- `partial`
- `not_observable`
- `not_configured`
- `failed`

## Inventory

Report aggregates, not a duplicate raw-variable export:

```json
{
  "collections_total": 3,
  "variables_total": 240,
  "variables_by_collection": {"Global": 120, "Semantic": 100, "Typography": 20},
  "variables_by_type": {"COLOR": 180, "FLOAT": 40, "STRING": 20},
  "modes_by_collection": {
    "Global": [{"id": "m1", "name": "Light"}, {"id": "m2", "name": "Dark"}]
  },
  "descriptions": {"complete": 220, "empty": 20},
  "missing_mode_values": 2,
  "all_scopes": 4,
  "unresolved_aliases": 2,
  "potential_orphan_candidates": 5
}
```

Use exact Figma type names returned by the read path. If a metric is not observable, use an object such as `{"status":"not_observable"}` instead of a numeric value.

## Documentation Readiness

Represent the normal state as well as problems. Do not rely on findings to reconstruct whether Phase 2 can proceed.

```json
{
  "status": "not_observable",
  "changelog": {
    "status": "not_observable",
    "node_ids": [],
    "checks": {
      "format": {"status": "not_observable", "observed": null, "evidence": []},
      "sort_order": {"status": "not_observable", "observed": null, "evidence": []},
      "author_values": {"status": "not_observable", "observed": null, "evidence": []},
      "type_values": {"status": "not_observable", "observed": null, "evidence": []},
      "layout_structure": {"status": "not_observable", "observed": null, "evidence": []},
      "visual_integrity": {"status": "not_observable", "observed": null, "evidence": []}
    },
    "limitations": ["Document text was not available"]
  },
  "reference": {
    "status": "not_observable",
    "node_ids": [],
    "checks": {
      "location": {"status": "not_observable", "observed": null, "evidence": []},
      "required_evidence": {"status": "not_observable", "observed": null, "evidence": []},
      "layout_structure": {"status": "not_observable", "observed": null, "evidence": []},
      "visual_integrity": {"status": "not_observable", "observed": null, "evidence": []}
    },
    "limitations": ["Reference frames were not traversed"]
  },
  "limitations": ["Documentation readiness could not be established"]
}
```

Allowed overall statuses:

- `ready`
- `ready_with_limitations`
- `not_ready`
- `not_observable`
- `not_configured`
- `failed`

Allowed component and check statuses:

- `pass`
- `needs_review`
- `missing`
- `not_observable`
- `not_configured`
- `failed`

Use `ready` only when every changelog and reference check passes and no limitation remains. Use `not_ready` when any required component is missing, failed, or needs review. Phase 2 must use this section as its primary readiness input and use related findings for issue details.

For a passing `layout_structure` check, `observed` contains `layout_model` (`auto_layout`, `absolute`, or `mixed`) and `dynamic_content_safe: true`. Absolute positioning can pass for deliberate top-level canvas placement or an approved existing convention; repeating or dynamically sized content must not rely on assumed fixed coordinate offsets.

For a passing `visual_integrity` check, `observed` contains `overlap_count: 0`, `clipped_content_count: 0`, and at least one screenshot reference covering the complete affected documentation area. Re-read node bounds and layout properties as well; screenshot review complements rather than replaces structural verification.

## Derived Metrics

Preserve required scan results even when they are not problems and therefore should not become findings.

```json
{
  "local_inbound_aliases": {
    "status": "complete",
    "edges_total": 18,
    "targets_with_inbound_aliases": 7,
    "counts_by_target_id": {"VariableId:1": 3}
  },
  "description_patterns": {
    "status": "complete",
    "evaluated_variables": 47,
    "patterns": [
      {
        "pattern_id": "usage-oriented-sentence",
        "label": "Usage-oriented sentence",
        "count": 42,
        "confidence": "high",
        "example_variable_ids": ["VariableId:1"]
      }
    ],
    "unclassified": 5
  },
  "scopes_by_collection": {
    "status": "complete",
    "collections": {
      "VariableCollectionId:1": {
        "name": "Semantic",
        "variables_total": 100,
        "scope_counts": {"ALL_SCOPES": 4, "FRAME_FILL": 28, "TEXT_FILL": 16},
        "unobservable": 0
      }
    }
  }
}
```

Each metric status uses the coverage statuses `complete`, `partial`, `not_observable`, `not_configured`, or `failed`. `counts_by_target_id` is a compact derived index, not a raw variable export. Alias edge totals must equal the sum of its counts, and `targets_with_inbound_aliases` must equal the number of positive-count targets. Description pattern counts plus `unclassified` must equal the number of variables whose description evidence was evaluated. Scope counts may exceed `variables_total` because one variable can expose multiple scopes.

Use `local_inbound_aliases.status: complete` only when every captured variable and every captured mode value was checked. With partial alias inspection, use `partial`, state the limitation in coverage, and include only measured counts. Do not infer zero-inbound targets or orphan candidates for records that were not inspected.

## Property Traversal Coverage

Include `property_coverage` exactly as defined in [property-traversal-contract.md](property-traversal-contract.md). It records the adapter capability basis, all six property families, one coverage record per declared path, explicit non-bindable exclusions, and limitations.

The traversal declaration comes from adapter capabilities, not from variables or bindings already present in the file. Literal counts include properties with no existing-variable match. `numeric_semantics.family` classifies an encountered FLOAT target; it is not evidence that the corresponding property family was searched.

A scan with partial, unsupported, or unobservable property families may remain `complete_with_limitations`, but it must not claim complete binding or hardcoded-value coverage. An empty `binding_findings` array is conclusive only within the declared and validated property coverage.

## Binding Findings

Record node-property mapping evidence separately from general audit findings. An empty array means no binding candidates were found within the declared traversal coverage; coverage and limitations determine whether that absence is conclusive.

```json
{
  "finding_id": "DTA-BINDING-001",
  "fingerprint": "binding|1:231|fills[0].color|VariableID:1:16",
  "source_audit_id": "dta-20260811T173000Z-abc123",
  "page_id": "1:50",
  "node_id": "1:231",
  "node_name": "Card surface",
  "node_type": "FRAME",
  "property_path": "fills[0].color",
  "property_value_type": "COLOR",
  "current": {"kind": "literal", "value": "#FFFFFF"},
  "expected": {
    "kind": "variable",
    "variable_id": "VariableID:1:16",
    "variable_name": "color/bg/surface",
    "variable_type": "COLOR",
    "collection_id": "VariableCollectionId:1:14",
    "relevant_mode_ids": ["ModeID:light", "ModeID:dark"],
    "missing_mode_ids": [],
    "scopes": ["FRAME_FILL"],
    "scope_compatibility": "compatible"
  },
  "operation": "bind",
  "confidence": "high",
  "status": "proposed",
  "evidence": [
    {"source": "figma_node_binding", "detail": "Fill is literal and matches the Light value of color/bg/surface."}
  ],
  "risk": "The literal does not follow mode changes.",
  "limitations": []
}
```

Allowed values:

- `property_value_type`: `COLOR`, `FLOAT`, `STRING`, `BOOLEAN`
- `current.kind`: `literal`, `variable`, `unbound`
- `expected.kind`: `variable`, `unbound`
- `operation`: `bind`, `rebind`, `unbind`, `no_op`
- `status`: `proposed`, `held`, `not_actionable`, `verified`
- `confidence`: `high`, `medium`, `low`
- `expected.scope_compatibility`: `compatible`, `needs_review`, `incompatible`

Classification rules:

- `bind` requires a literal or unbound current representation and a variable target.
- `rebind` requires a current variable and a different variable target.
- `unbind` requires a current variable and an expected `unbound` state.
- `no_op` requires matching current and expected variable IDs and cannot have `status: proposed`.
- For variable targets, `property_value_type` must equal `expected.variable_type`.
- Every FLOAT variable target requires `numeric_semantics` with `family`, `current_effective_value`, `target_variable_value`, `target_resolved_consumer_value`, `expected_effective_value`, `tolerance`, `equivalence`, and `resolution_method`.
- `equivalence` must be derived by comparing `target_resolved_consumer_value` with `expected_effective_value` using `tolerance`. Do not infer equivalence from the stored variable value, token name, scope, UI display, or numeric type alone.
- A proposed FLOAT write requires observable consumer resolution and `equivalence: equivalent`. A mismatch or unavailable consumer resolution must remain held.
- For the `opacity` family, current, resolved, and expected effective consumer values must be between `0` and `1`. The stored or adapter-reported variable value is recorded separately because UI, API, and adapter representations may use different scales.
- A proposed write requires at least one relevant mode, no missing relevant mode values, and compatible scope intent.
- Every property path must identify one explicit property or indexed paint property, such as `fills[0].color`, `opacity`, `paddingTop`, or `topLeftRadius`.
- Finding IDs and fingerprints must be unique. The exact write identity is `node_id + property_path + operation + target_variable_id`; use `null` as the target for `unbind`.

Binding findings are proposals, not write authorization. Apply them only through `token-binding-fix` after its independent preview, approval, drift, compatibility, documentation, and verification gates.

## Binding Summary

```json
{
  "findings_total": 4,
  "by_operation": {"bind": 2, "rebind": 1, "unbind": 0, "no_op": 1},
  "by_status": {"proposed": 3, "held": 0, "not_actionable": 1, "verified": 0},
  "write_candidates": 3
}
```

All counts must be derivable from `binding_findings`. `write_candidates` counts records with `status: proposed` and operations `bind`, `rebind`, or `unbind`; it never counts `no_op` controls.

## Findings

Each finding must have this shape:

```json
{
  "id": "DTA-MODE-001",
  "fingerprint": "missing-mode-value|VariableID:42|ModeID:7",
  "rule_id": "missing-mode-value",
  "category": "mode",
  "severity": "high",
  "confidence": "high",
  "title": "Semantic/action/danger lacks a Dark value",
  "status": "open",
  "targets": [
    {
      "kind": "variable",
      "id": "VariableID:42",
      "name": "Semantic/action/danger",
      "collection_id": "VariableCollectionId:2",
      "mode_id": "ModeID:7",
      "page_id": null
    }
  ],
  "observed": {"value_status": "missing"},
  "expected": {"value_status": "present"},
  "evidence": [
    {
      "source": "figma_variable_metadata",
      "detail": "valuesByMode contains no ModeID:7 entry"
    }
  ],
  "risk": "Consumers in Dark mode may receive fallback or undefined behavior.",
  "recommendation": "Review the intended Dark alias in a separate approved pass.",
  "limitations": []
}
```

Allowed values:

- `category`: `collection`, `mode`, `description`, `scope`, `naming`, `alias`, `usage`, `accessibility`, `typography`, `changelog`, `reference`, `other`
- `severity`: `critical`, `high`, `medium`, `low`, `info`
- `confidence`: `high`, `medium`, `low`
- `status`: `open`, `needs_review`, `held`, `not_actionable`
- target `kind`: `collection`, `variable`, `mode`, `node`, `page`, `external_consumer`

Apply severity by impact:

- `critical`: demonstrated broad breakage or unsafe value in active consumers
- `high`: likely functional, accessibility, or cross-mode failure
- `medium`: inconsistent semantics or metadata with meaningful maintenance cost
- `low`: localized hygiene issue with low consumer risk
- `info`: observation or coverage note requiring no correction

Do not raise severity merely because many records match a low-risk hygiene rule.

Confidence and severity are independent: confidence states how certain the observation is, while severity states demonstrated impact. Without active-consumer evidence, describe possible downstream impact with conditional language and do not classify a suspicious literal value as `critical`. The `risk` field is prose, not a second severity field; it must not state a risk label that conflicts with `severity`.

For every `critical` finding, include a non-empty `observed.active_consumer_impact` string that states the demonstrated breakage or unsafe active-consumer outcome. A hypothetical impact does not satisfy this requirement.

## Finding Identity

Assign display IDs as `DTA-{CATEGORY}-{NNN}` with deterministic ordering by category, rule ID, target ID, and mode ID.

Build `fingerprint` from:

```text
rule_id|sorted target IDs|mode ID when relevant
```

The fingerprint must not contain mutable token names. Use it to compare findings across scans. If stable Figma IDs are unavailable in an export, prefix the fallback identity with `unstable-name:` and lower confidence.

Use this exact delimiter rule:

```text
rule_id|target_id_1,target_id_2|mode_id_1,mode_id_2
```

Sort target and mode IDs. Omit the final mode segment when no mode is relevant. Every target object includes `kind`, `id`, `name`, `collection_id`, `mode_id`, and `page_id`; use `null` for non-applicable nullable fields.

## Summary

```json
{
  "findings_total": 9,
  "by_severity": {"critical": 0, "high": 1, "medium": 3, "low": 5, "info": 0},
  "by_category": {"mode": 1, "description": 3, "naming": 5},
  "holds": 2,
  "risk_statement": "One missing mode value requires review; external usage was not observable."
}
```

Counts must be derivable from `findings`. Do not count coverage limitations as findings unless they prevent a configured audit requirement.

## Markdown Report

Render the human report from the same facts as the JSON object. Include:

1. audit identity and source
2. inspection method
3. inventory, derived-metrics, and binding summary
4. documentation readiness
5. binding findings and controls
6. findings grouped by severity
7. coverage and limitations
8. risk statement
9. recommended next pass
10. explicit confirmation that no changes were made

If the Markdown and JSON conflict, treat the JSON as invalid and correct both before delivery.

## Validation

When the JSON exists as a file, validate it before delivery:

```bash
python3 scripts/validate_audit_json.py <audit.json>
```

Exit code `0` means valid, `1` means contract violations, and `2` means the file could not be read or parsed. The validator checks required fields, enums, timestamps, coverage consistency, finding identity, duplicate IDs and fingerprints, binding operation consistency, property and variable type compatibility, inventory totals, binding-summary counts, and general summary counts.
