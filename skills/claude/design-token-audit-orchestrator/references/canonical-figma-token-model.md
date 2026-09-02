# Canonical Figma Token Snapshot

Normalize all supported Figma read paths into this model before applying audit rules. Preserve source IDs and values; do not clean or rename data during normalization.

## Snapshot Envelope

```json
{
  "schema_version": "1.0.0",
  "snapshot_type": "figma_token_snapshot",
  "snapshot_id": "dts-20260811T173000Z-abc123",
  "captured_at": "2026-08-11T17:30:00Z",
  "source": {},
  "adapter": {},
  "coverage": {},
  "collections": [],
  "variables": [],
  "pages": [],
  "usages": [],
  "document_evidence": [],
  "warnings": []
}
```

Use UTC ISO-8601 timestamps with `Z` or `+00:00`. IDs are opaque strings and must never be parsed for business meaning.

## Source

```json
{
  "file_key": "abc123",
  "file_name": "Design System",
  "branch_or_version": null,
  "source_revision": null,
  "export_fingerprint": null
}
```

At least `file_key` and `file_name` are required. For an export without a native file key, use its declared source identifier and set a warning that stable Figma identity was unavailable.

## Adapter

Use the capability record from the adapter contract:

```json
{
  "adapter_id": "generic-mcp",
  "adapter_version": "1",
  "source_type": "mcp",
  "capabilities": {},
  "raw_source_timestamp": null
}
```

## Coverage

Record normalization coverage separately from audit-result coverage:

```json
{
  "collections": {"status": "complete", "captured": 3, "failed": 0},
  "variables": {"status": "complete", "captured": 240, "failed": 0},
  "pages": {"status": "partial", "captured_ids": ["1:2"], "omitted_ids": ["1:3"]},
  "usages": {"status": "partial"},
  "document_evidence": {"status": "not_configured"}
}
```

Allowed status values are `complete`, `partial`, `not_observable`, `not_configured`, and `failed`.

## Collections

```json
{
  "id": "VariableCollectionId:1",
  "name": "Semantic",
  "default_mode_id": "ModeId:1",
  "modes": [
    {"id": "ModeId:1", "name": "Light", "position": 0},
    {"id": "ModeId:2", "name": "Dark", "position": 1}
  ],
  "variable_ids": ["VariableId:1"],
  "remote": false,
  "hidden_from_publishing": false,
  "provenance": {"adapter_id": "figma-plugin-api", "source_path": "local collections"}
}
```

Required fields: `id`, `name`, `default_mode_id`, `modes`, `variable_ids`, and `provenance`. Use `null` for a supported field with no value; use a field-status object for an unobservable field.

## Variables

```json
{
  "id": "VariableId:1",
  "name": "Semantic/action/danger",
  "collection_id": "VariableCollectionId:1",
  "resolved_type": "COLOR",
  "description": "Destructive action foreground",
  "scopes": ["ALL_SCOPES"],
  "remote": false,
  "hidden_from_publishing": false,
  "code_syntax": {"WEB": "--action-danger"},
  "values_by_mode": {
    "ModeId:1": {"kind": "alias", "target_variable_id": "VariableId:20"},
    "ModeId:2": {"kind": "literal", "value": {"r": 1, "g": 0, "b": 0, "a": 1}}
  },
  "provenance": {"adapter_id": "figma-plugin-api", "source_path": "local variables"}
}
```

Required fields: `id`, `name`, `collection_id`, `resolved_type`, `description`, `scopes`, `values_by_mode`, and `provenance`.

Use these normalized mode-value variants:

```json
{"kind": "literal", "value": true}
```

```json
{"kind": "alias", "target_variable_id": "VariableId:20"}
```

```json
{"kind": "missing"}
```

```json
{"kind": "not_observable", "reason": "remote target value unavailable", "target_variable_id": "VariableId:remote-20"}
```

Preserve `target_variable_id` when the unavailable value is a known remote alias target. The field is optional when no target identity is observable.

Preserve literal types exactly: Boolean, number, string, or RGBA object with `r`, `g`, `b`, and `a` values from 0 through 1. Do not convert colors into hex strings or resolve aliases into copied literals.

## Pages

```json
{
  "id": "1:2",
  "name": "Foundations",
  "traversal_status": "complete",
  "node_count": 430,
  "provenance": {"adapter_id": "figma-plugin-api", "source_path": "document page"}
}
```

Allowed traversal statuses: `complete`, `partial`, `not_observable`, `failed`.

## Usages

Represent each observed binding as a separate record:

```json
{
  "variable_id": "VariableId:1",
  "node_id": "4:8",
  "page_id": "1:2",
  "binding_path": "fills[0].color",
  "binding_kind": "bound_variable",
  "provenance": {"adapter_id": "figma-plugin-api", "source_path": "node.boundVariables"}
}
```

Absence from `usages` proves no usage only when every requested page has complete traversal and `read_bound_variables` is available.

## Document Evidence

Represent changelog and reference-card evidence without embedding full node trees:

```json
{
  "evidence_type": "changelog",
  "node_id": "7:9",
  "page_id": "1:5",
  "node_name": "Token changelog",
  "node_type": "FRAME",
  "matched_by": "configured_id",
  "text_excerpt": "2026-08-11 ...",
  "provenance": {"adapter_id": "figma-plugin-api", "source_path": "document node"}
}
```

Allowed `evidence_type` values: `changelog`, `reference`, `other`.

## Provenance

Every collection, variable, usage, and document-evidence record requires:

- `adapter_id`
- `source_path` or equivalent query description

For mixed adapters, the top-level `adapter_id` identifies the mixed adapter while each record's provenance identifies the contributing adapter. Add:

- `captured_at`
- `source_revision` when available
- `field_sources` when fields in one record came from different sources

Reject conflicting values from mixed sources unless precedence is explicit. Preserve both values in a warning; do not silently choose one.

## Identity And Integrity

Before audit evaluation, verify:

- unique collection IDs
- unique variable IDs
- unique mode IDs within each collection
- every local variable references an observed collection
- every collection `variable_id` resolves to the same collection
- every `values_by_mode` key belongs to the variable's collection
- every local alias target resolves or is explicitly classified as remote/unobservable
- usage records reference observed variables and pages when those inventories are complete

A failed core integrity check makes the snapshot invalid. Do not run token-quality rules on an invalid snapshot.

## Validation And Contract Comparison

Validate one normalized snapshot with:

```bash
python3 scripts/validate_snapshot.py <snapshot.json>
```

Compare two or more adapter snapshots of the same source with:

```bash
python3 scripts/validate_snapshot.py --compare <snapshot-a.json> <snapshot-b.json>
```

Comparison ignores adapter metadata, provenance, optional page usage, timestamps, and snapshot IDs. It requires equivalent source identity, collections, ordered modes, variables, descriptions, scopes, literals, and alias semantics.

Semantic comparison resolves mode IDs inside their owning collection. Because adapter-independent comparison cannot disambiguate duplicate semantic names without shared stable IDs, comparison is blocked when collection names repeat or variable names repeat within one collection. The individual snapshots remain valid and duplicate names can still be reported as audit findings.
