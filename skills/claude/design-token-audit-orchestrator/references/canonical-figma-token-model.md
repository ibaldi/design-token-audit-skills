# Canonical Figma Token Snapshot

Normalize all supported Figma read paths into this model before applying audit rules. Preserve source IDs and values; do not clean or rename data during normalization.

## Snapshot Envelope

```json
{
  "schema_version": "1.1.0",
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
  "referenced_variables": [],
  "document_evidence": [],
  "warnings": []
}
```

Snapshot schema `1.1.0` adds the `composite` mode-value kind and the optional `referenced_variables` array. A `1.0.0` snapshot remains valid when it uses neither; validators reject either feature in a `1.0.0` snapshot.

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

A COLOR mode value may combine a color and a separate opacity, each of which may be an alias. Figma exposes this as an object with `color` and `opacity` instead of an RGBA literal or a single `VARIABLE_ALIAS`. Normalize it as a composite and preserve both components exactly:

```json
{
  "kind": "composite",
  "components": {
    "color": {"kind": "alias", "target_variable_id": "VariableID:763:191"},
    "opacity": {"kind": "alias", "target_variable_id": "VariableID:1123:263"}
  }
}
```

Rules for `composite`:

- It is allowed only for `COLOR` variables and requires snapshot schema `1.1.0`.
- `components` contains exactly `color` and `opacity`.
- Each component is a `literal`, an `alias`, or a `not_observable` value with the same shape as a top-level mode value. A `color` literal is an RGBA object; an `opacity` literal is a number.
- Preserve the opacity scale reported by the read path. Figma `COLOR_OPACITY` values are commonly stored on a 0–100 scale; do not rescale them during normalization.
- Each component alias is a local alias edge. Count it for local inbound aliases and resolve it with the same integrity rules as a top-level alias.
- Never collapse a composite into a single alias or a computed RGBA literal.

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

A usage `variable_id` must reference either a captured local variable or a `referenced_variables` record.

## Referenced Variables

Nodes can bind variables that are not part of the local inventory. Record each such variable once as a reference so that its usages remain valid evidence:

```json
{
  "id": "VariableID:00b6817e1da2aec897517f2bf8bec45634be3c54/514:628",
  "origin": "remote_library",
  "name": "spacing/xs",
  "key": "00b6817e1da2aec897517f2bf8bec45634be3c54",
  "resolved_type": "FLOAT",
  "remote": true,
  "collection_id": null,
  "provenance": {"adapter_id": "figma-plugin-api", "source_path": "getVariableByIdAsync for bound variable"}
}
```

Allowed `origin` values:

- `remote_library`: the variable belongs to a subscribed library. `remote` must be `true`.
- `stale_local_reference`: the lookup still returns a non-remote variable, but the local inventory does not contain it. This is evidence of a stale local reference, not proof that a variable was deleted. Preserve the observable `collection_id`.
- `unresolved_reference`: the binding ID is observable, but the variable lookup returns no object or fails. Set `name`, `key`, `resolved_type`, `remote`, and `collection_id` to `null`, and include a non-empty `reason`.

Required fields: `id`, `origin`, `name`, `key`, `resolved_type`, `remote`, `collection_id`, and `provenance`. Use `null` for optional metadata the lookup does not expose. An ID cannot appear both as a local variable and as a reference. A `stale_local_reference` cannot point to an observed local collection.

References are usage evidence only. They are not part of the local inventory, do not count toward collection or variable totals, and are never valid targets for value, scope, or creation writes in this suite. A `remote_library` binding stays outside local orphan evidence; a library-aware workflow is required before it can become a binding target. A `stale_local_reference` is an integrity observation and must not be treated as a confirmed deletion. An `unresolved_reference` keeps the snapshot valid but requires `coverage.usages.status: partial`, an explicit limitation, and a hold on every automatic fix or deletion decision involving that reference. Any rebind or unbind must go through the separately approved `token-binding-fix` workflow.

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
- usage records reference observed local variables or referenced variables, and observed pages when those inventories are complete
- composite component aliases resolve like top-level aliases

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

Comparison ignores adapter metadata, provenance, optional page usage, referenced variables, timestamps, snapshot IDs, and the snapshot schema minor version. It requires equivalent source identity, collections, ordered modes, variables, descriptions, scopes, literals, and alias semantics, including composite components.

Semantic comparison resolves mode IDs inside their owning collection. Because adapter-independent comparison cannot disambiguate duplicate semantic names without shared stable IDs, comparison is blocked when collection names repeat or variable names repeat within one collection. The individual snapshots remain valid and duplicate names can still be reported as audit findings.
