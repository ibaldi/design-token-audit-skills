# Audit Output Contract

Produce two synchronized outputs for every read-only scan:

1. a concise human-readable Markdown report
2. one machine-readable JSON object conforming to this contract

Do not put comments in the JSON. Use `null` only for a known field with no value. Use `not_observable` or `not_configured` status values for unavailable or unspecified checks; do not encode either state as an empty array or zero.

## Schema Version

Set `schema_version` to `1.0.0`. A consumer may reject unsupported major versions. Additive fields require a minor version; incompatible changes require a major version.

## Top-level Shape

```json
{
  "schema_version": "1.0.0",
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
  "findings": [],
  "summary": {},
  "recommended_next_pass": null
}
```

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

## Finding Identity

Assign display IDs as `DTA-{CATEGORY}-{NNN}` with deterministic ordering by category, rule ID, target ID, and mode ID.

Build `fingerprint` from:

```text
rule_id|sorted target IDs|mode ID when relevant
```

The fingerprint must not contain mutable token names. Use it to compare findings across scans. If stable Figma IDs are unavailable in an export, prefix the fallback identity with `unstable-name:` and lower confidence.

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
3. inventory summary
4. findings grouped by severity
5. coverage and limitations
6. risk statement
7. recommended next pass
8. explicit confirmation that no changes were made

If the Markdown and JSON conflict, treat the JSON as invalid and correct both before delivery.

## Validation

When the JSON exists as a file, validate it before delivery:

```bash
python3 scripts/validate_audit_json.py <audit.json>
```

Exit code `0` means valid, `1` means contract violations, and `2` means the file could not be read or parsed. The validator checks required fields, enums, timestamps, coverage consistency, finding identity, duplicate IDs and fingerprints, inventory totals, and summary counts.
