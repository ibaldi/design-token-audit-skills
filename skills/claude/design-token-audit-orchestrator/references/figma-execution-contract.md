# Figma Read Execution Contract

Use this contract to collect evidence for a token read-only scan. Do not infer unavailable data.

## 1. Record The Inspection Context

Before querying data, record:

- file key and file name
- inspected branch or version, when available
- relevant page IDs and names
- inspection timestamp
- Figma tool or API used
- tool capabilities and unavailable operations

If the file cannot be identified, stop and request the missing context. Treat an unavailable branch/version as a limitation. Treat requested pages as a blocking requirement only when the user or audit configuration explicitly requires page-level inspection.

## 2. Use The Best Available Read Path

Select the read path through capability negotiation in the adapter contract. Prefer the source with complete core capabilities and the greatest relevant optional coverage; prefer least privilege when coverage is equal. Do not require the Plugin API when another adapter satisfies the same capabilities.

For Plugin API access, use asynchronous methods where available:

- `figma.variables.getLocalVariableCollectionsAsync()`
- `figma.variables.getLocalVariablesAsync()`
- `figma.variables.getVariableByIdAsync(id)` for alias resolution
- `figma.getNodeByIdAsync(id)` for named evidence nodes

Do not substitute screenshots, rendered frames, or CSS output for variable metadata. If the available tool cannot expose a required field, mark that field `not observable`.

## 3. Capture Raw Collection Records

For every local collection, capture:

- collection ID and name
- default mode ID
- ordered mode IDs and names
- variable IDs
- remote or local status when exposed
- hidden-from-publishing status when exposed

Preserve IDs in the working evidence even if the human-facing report primarily uses names.

## 4. Capture Raw Variable Records

For every local variable, capture:

- variable ID and name
- collection ID
- resolved type
- description
- scopes
- values keyed by mode ID
- remote or local status
- hidden-from-publishing status when exposed
- code syntax mappings when exposed

For each mode value, preserve whether it is:

- a literal
- a `VARIABLE_ALIAS`, including the target variable ID
- missing
- unresolvable with the available access

Never rewrite values merely to normalize the evidence.

## 5. Derive Findings Deterministically

Calculate:

- collection counts from captured collection records
- variable counts from captured variable records
- type counts from `resolvedType`
- empty descriptions after trimming whitespace
- missing mode values when a collection mode ID has no corresponding entry in `valuesByMode`
- `ALL_SCOPES` from the exact scopes metadata, not from visual usage
- duplicate names within the same collection; report cross-collection duplicates separately
- leading/trailing spaces from `name !== name.trim()`
- double spaces from two or more consecutive spaces
- spaces around hyphens from whitespace immediately before or after `-`

Do not label a value suspicious only because it is zero. Report a suspicious AX/accessibility value only when an expected value, comparison mode, documented rule, or inconsistent peer pattern provides evidence.

## 6. Resolve Alias Evidence

For every `VARIABLE_ALIAS` value:

1. Record source variable ID, source mode ID, and target variable ID.
2. Resolve the target with the available variable lookup.
3. Follow the chain until reaching a literal, an unavailable remote variable, a missing target, or a cycle.
4. Record the full chain of IDs and names.

Classify outcomes as:

- resolved to literal
- remote target not observable
- missing target
- cycle detected
- lookup unavailable

Count local inbound aliases by target variable ID. Do not treat absence of local inbound aliases as proof that a token is unused.

The count is exhaustive only when every captured variable and every captured mode value was inspected for aliases. Otherwise mark the metric `partial`, identify the uninspected records or modes, and do not publish a complete list of targets with zero inbound aliases. Missing evidence is not a zero count.

## 7. Handle Usage And Orphan Evidence Conservatively

Classify possible orphan evidence as:

- `no local inbound alias`: no captured local variable aliases the token
- `no usage in inspected pages`: a complete traversal of the declared pages found no bound variable reference
- `external usage unknown`: consumer files or code were not searched
- `externally confirmed unused`: a separate consumer inventory provides evidence

Only use `potential orphan candidate` when the evidence scope is stated. Never recommend deletion from local evidence alone.

When node traversal is supported, inspect the declared pages and record bound variable references exposed on nodes. Report which pages were fully traversed. If traversal is partial or unsupported, do not claim absence of node usage.

## 8. Inspect Changelog And Reference Evidence

Treat changelog and reference-card findings as document-node evidence, not variable metadata.

For each relevant node, record:

- node ID, name, type, and page
- how it was located: configured ID, exact name, or search pattern
- inspected fields or visible text

If no expected location or naming rule was provided, report `not configured` instead of `missing`.

## 9. Attach Evidence To Every Finding

Every finding must include:

- stable finding ID within the report
- rule applied
- collection and variable/node IDs
- affected names
- observed value or metadata
- evidence source
- confidence: high, medium, or low
- limitation, when applicable

Use high confidence only for complete metadata returned directly by the Figma read path. Use lower confidence for partial traversal, naming heuristics, or exported data with unknown freshness.

Confidence describes certainty in the observation, not the severity of downstream impact. Use `critical` only when active-consumer evidence demonstrates broad breakage or an unsafe value. If external consumers were not observed, phrase impact as conditional and cap suspicious value findings at `high`. Keep the `risk` field as prose; never put a second, conflicting severity classification in it.

## 10. State Coverage And Limits

End the scan with:

- collections observed versus expected
- variables successfully captured
- pages fully traversed
- unresolved remote aliases
- fields that were not observable
- external consumer sources searched
- external consumer sources not searched

Never describe the scan as complete without this coverage statement.
