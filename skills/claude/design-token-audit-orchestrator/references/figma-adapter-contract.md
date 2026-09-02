# Figma Adapter Contract

Use an adapter to isolate audit rules from a specific Figma plugin, MCP server, API client, or export format. An adapter reads source data and emits the canonical snapshot defined in [canonical-figma-token-model.md](canonical-figma-token-model.md).

## Core Rule

Do not select an adapter by product name alone. Negotiate capabilities first. Missing optional capabilities reduce coverage; missing core capabilities block the token scan.

The read-only scan must never invoke a write operation, even when the selected adapter advertises write support.

## Capability Negotiation

Before reading token data, build a capability record:

```json
{
  "adapter_id": "figma-plugin-api",
  "adapter_version": "1",
  "source_type": "plugin_api",
  "capabilities": {
    "identify_file": {"status": "available", "evidence": "figma.fileKey"},
    "read_local_collections": {"status": "available", "evidence": "getLocalVariableCollectionsAsync"},
    "read_local_variables": {"status": "available", "evidence": "getLocalVariablesAsync"},
    "resolve_local_aliases": {"status": "available", "evidence": "getVariableByIdAsync"},
    "read_remote_alias_targets": {"status": "partial", "evidence": "depends on library access"},
    "traverse_document_nodes": {"status": "available", "evidence": "page node traversal"},
    "read_bound_variables": {"status": "available", "evidence": "node boundVariables"},
    "read_node_text": {"status": "available", "evidence": "text node characters"},
    "search_external_figma_consumers": {"status": "unavailable", "evidence": "outside current file"},
    "search_code_consumers": {"status": "unavailable", "evidence": "outside current file"}
  }
}
```

Allowed capability statuses:

- `available`: sufficient for the declared operation
- `partial`: usable with an explicit scope or known omissions
- `unavailable`: confirmed unsupported
- `unknown`: not tested or not exposed
- `failed`: supported in principle, but the current attempt failed

Do not equate `unknown` with `unavailable`. Record the evidence used to assign every status.

## Capability Classes

Core capabilities:

- `identify_file`
- `read_local_collections`
- `read_local_variables`

If any core capability is not `available`, set the scan status to `blocked`. Do not produce token-quality findings from incomplete core inventory.

Optional capabilities:

- `identify_branch_or_version`
- `resolve_local_aliases`
- `read_remote_alias_targets`
- `traverse_document_nodes`
- `read_bound_variables`
- `read_node_text`
- `read_code_syntax`
- `search_external_figma_consumers`
- `search_code_consumers`

An optional capability with `partial`, `unavailable`, `unknown`, or `failed` must create a corresponding coverage limitation. Continue with rules whose requirements are satisfied.

Write capabilities are outside a read-only scan. Record but never invoke:

- `create_variables`
- `update_variables`
- `delete_variables`
- `update_document_nodes`

## Rule Gating

Before evaluating a rule:

1. Read its required capabilities.
2. Run it only when every required capability is `available` or the rule explicitly accepts `partial`.
3. Mark the rule `not_observable` when a required optional capability is unavailable or unknown.
4. Mark the rule `failed` when collection was attempted but failed.
5. Do not emit a finding for a condition that could not be evaluated.

Examples:

| Check | Required capabilities | Missing-capability result |
| --- | --- | --- |
| Collection and variable counts | Core capabilities | Block scan |
| Missing mode values | Core capabilities | Block scan |
| Local alias integrity | `resolve_local_aliases` | `not_observable` |
| Usage in inspected pages | `traverse_document_nodes`, `read_bound_variables` | `not_observable` |
| Changelog content | `traverse_document_nodes`, `read_node_text` | `not_observable` |
| External orphan confirmation | external Figma and code consumer search | Hold; never confirm deletion |

## Adapter Selection

Choose the adapter that provides all core capabilities and the greatest relevant optional coverage with the least privilege. Prefer a read-only adapter over a write-capable adapter when coverage is equivalent.

Use `source_type` values:

- `plugin_api`
- `mcp`
- `api`
- `export`
- `mixed`

Use a mixed adapter only when records can retain field-level provenance and refer to the same file version or compatible snapshot. Do not silently merge stale export data with live Figma data.

## Fallback Sequence

1. Try the preferred configured adapter.
2. Negotiate and record capabilities.
3. If a core capability is missing, try the next available adapter.
4. If different adapters jointly satisfy core capabilities, use `mixed` only after verifying source identity and freshness.
5. If core capabilities remain missing, return a blocked report with the missing capability list.
6. If only optional capabilities are missing, continue with `complete_with_limitations`.

Do not request installation of a specific plugin when another available path satisfies the required capabilities.

## Errors And Recovery

Normalize adapter errors as:

- `AUTH_REQUIRED`
- `FILE_NOT_FOUND`
- `ACCESS_DENIED`
- `CAPABILITY_UNAVAILABLE`
- `RATE_LIMITED`
- `STALE_SOURCE`
- `INVALID_SOURCE_DATA`
- `PARTIAL_RESULT`
- `ADAPTER_FAILURE`

Retry only transient failures such as rate limits. Do not retry permission or capability failures without a changed condition. Preserve partial data for diagnostics, but do not treat it as a complete core inventory.

## Required Adapter Output

Every adapter must emit:

- adapter identity and version
- negotiated capabilities with evidence
- source identity and timestamp
- canonical snapshot or normalized error
- record- and field-level provenance where sources are mixed
- warnings and omissions

Audit rules must consume only the canonical snapshot, never adapter-specific raw fields.
