---
name: token-readonly-scan
description: Perform a read-only current-state scan of a Figma design token library. Use when the user asks to inspect collections, modes, token counts, descriptions, scopes, ALL_SCOPES, missing mode values, naming issues, aliases, orphan candidates, changelog structure, reference cards, or baseline readiness. Never make changes in this skill.
---

# Token Read-only Scan

Use this skill to inspect a design token library without changing anything.

Before inspecting Figma, read and follow:

- [references/figma-adapter-contract.md](references/figma-adapter-contract.md) to negotiate capabilities and select a non-blocking read path
- [references/canonical-figma-token-model.md](references/canonical-figma-token-model.md) to normalize source data before applying audit rules
- [references/figma-adapter-mappings.md](references/figma-adapter-mappings.md) to map Plugin API, MCP, API, export, or mixed sources
- [references/figma-execution-contract.md](references/figma-execution-contract.md) for collection, derivation, evidence, and coverage
- [references/audit-output-contract.md](references/audit-output-contract.md) for the versioned Markdown and JSON outputs

## Rule

Do not write, rename, delete, create, move, or edit any Figma variable, token, node, changelog row, or reference card.

Do not infer fields the available Figma access cannot expose. Mark them `not observable` and include them in the coverage statement.

Do not run audit rules directly on adapter-specific responses. Normalize and integrity-check the canonical snapshot first, then gate each rule by its required capabilities.

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

## Output

Produce both required representations from the same evidence:

1. a concise Markdown report
2. one JSON object with `schema_version: 1.0.0`

Validate that inventory and summary counts are derivable from the captured evidence and findings before delivering the report.

When the JSON is saved as a file, run:

```bash
python3 scripts/validate_audit_json.py <audit.json>
```

Correct every reported error before delivery. If scripts cannot be executed in the current environment, apply the same checks manually and disclose that automated validation was unavailable.

## Final Response

Clearly state that the scan was read-only and that no changes were made. Distinguish observed facts from heuristic findings and unknown external consumer usage.
