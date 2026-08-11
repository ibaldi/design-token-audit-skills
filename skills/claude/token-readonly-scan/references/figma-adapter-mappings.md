# Figma Adapter Mappings

Use these mappings to produce the canonical snapshot. Tool-specific names may differ; map by semantics and verify capability evidence instead of assuming equivalence.

## Figma Plugin API Adapter

Use asynchronous APIs where available.

| Canonical field | Plugin API source |
| --- | --- |
| `source.file_key` | `figma.fileKey` |
| `source.file_name` | `figma.root.name` or file context |
| collections | `figma.variables.getLocalVariableCollectionsAsync()` |
| variables | `figma.variables.getLocalVariablesAsync()` |
| alias target | `figma.variables.getVariableByIdAsync(id)` |
| collection modes | collection `modes` |
| variable modes | variable `valuesByMode` |
| scopes | variable `scopes` |
| code syntax | variable `codeSyntax` when exposed |
| page identity | page node `id` and `name` |
| bound usage | node `boundVariables` and supported bound-variable fields |
| document text | text node `characters` after font-safe read access |

Normalize `VARIABLE_ALIAS` as `{"kind":"alias","target_variable_id":"..."}`. Normalize a missing collection mode key as `{"kind":"missing"}`. Do not resolve an alias by replacing it with its terminal literal.

Plugin API access is scoped to the current file. Set external-consumer capabilities to `unavailable` unless a separate verified source is combined.

## Generic MCP Adapter

Do not assume that a Figma MCP exposes Plugin API parity. Inspect its declared tools and, when safe, perform minimal read probes.

Map semantically equivalent fields:

| Canonical requirement | Acceptable MCP evidence |
| --- | --- |
| File identity | explicit file key/ID returned by the tool |
| Local collections | structured collection records with stable IDs and modes |
| Local variables | structured variable records with stable IDs, collection ID, type, and mode values |
| Alias resolution | alias target IDs plus a variable lookup operation |
| Node traversal | explicit enumeration/traversal result for declared pages |
| Bound usage | structured variable-binding metadata, not rendered appearance |
| Document text | node text content tied to node and page IDs |

Do not infer variables from screenshots, generated code, CSS, or design-context summaries. If the MCP returns names but not stable IDs, the core inventory may be used only when the export/source provides a stable fallback identity; mark identity confidence and fingerprints as unstable.

If an MCP exposes one combined response, retain its tool name and query as `source_path`. If it paginates, continue until the tool reports completion; otherwise coverage is `partial`.

## REST Or Other API Adapter

Use an API adapter only when its responses expose the required local variable metadata. Record endpoint versions and pagination completion. Normalize remote/published resources separately from local variables and never mix them solely by matching names.

Authentication errors, missing scopes, and rate-limited partial responses must use the normalized adapter errors. A successful HTTP response does not imply complete capability coverage.

## Export Adapter

Accept JSON or another structured export only when it can provide all core fields:

- stable source identifier
- collection IDs and names
- mode IDs and names
- variable IDs and names
- collection relationship
- resolved type
- values keyed by mode

Record:

- export format and producer
- export creation time when supplied
- file checksum as `export_fingerprint` when calculable
- fields omitted by the exporter

Exports normally cannot prove current node usage or external consumption. Mark those capabilities `not_observable`. If stable Figma IDs are absent, prefix derived identities with `unstable-name:` and do not use the snapshot as a deletion baseline.

## Mixed Adapter

Use a mixed adapter only when one source provides core variable metadata and another adds optional evidence.

Verify before merging:

1. same file key or independently verified source identity
2. compatible branch/version
3. timestamps within an acceptable audit window
4. matching stable IDs for overlapping records
5. no unresolved conflicting field values

Core records must have one authoritative source. Optional sources may add usage, document evidence, or external-consumer evidence. They must not overwrite core values without an explicit precedence rule.

## Capability And Fallback Matrix

| Capability | Plugin API | Generic MCP | Structured export | Missing behavior |
| --- | --- | --- | --- | --- |
| Identify file | normally available | probe | required in export | block |
| Read local collections | available | probe | required | block |
| Read local variables | available | probe | required | block |
| Resolve local aliases | available | tool-dependent | export-dependent | skip alias rules |
| Read remote aliases | access-dependent | tool-dependent | uncommon | limit alias coverage |
| Traverse nodes | available | tool-dependent | uncommon | usage not observable |
| Read variable bindings | available | tool-dependent | uncommon | usage not observable |
| Read changelog/reference text | available | tool-dependent | uncommon | evidence not observable |
| Search external Figma consumers | unavailable alone | uncommon | unavailable | hold orphan decisions |
| Search code consumers | unavailable alone | separate connector | unavailable | hold orphan decisions |

## Adapter Decision Procedure

```text
Discover available read paths
  -> negotiate capabilities for each path
  -> discard paths missing core capabilities
  -> choose greatest relevant optional coverage
  -> prefer least privilege when coverage is equal
  -> normalize into canonical snapshot
  -> validate snapshot integrity
  -> gate audit rules by capabilities
  -> report coverage and limitations
```

If no path provides core capabilities, return a blocked result listing acceptable alternatives. Do not prescribe a vendor when any conforming adapter would satisfy the contract.
