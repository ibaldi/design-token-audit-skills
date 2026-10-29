# Figma Console Collector

Collector contract version: `1.0.0`

Use this path only when the connected Figma execution environment exposes the Plugin API and can run read-only JavaScript. It is one concrete adapter for the capability-based contract, not a requirement to use a named plugin.

## Files

- `scripts/collect_figma_variables.js` collects the complete collection inventory and chunked variable records.
- `scripts/collect_figma_properties.js` collects the page inventory, exact binding usages, and property observations required for Audit `1.5.0` traversal evidence.
- `scripts/assemble_snapshot.py` merges chunks into `figma_token_snapshot` `1.1.0` and can write a property-observation sidecar.
- `scripts/diff_snapshots.py` performs pre-write drift checks and exact post-write verification.

All JavaScript collectors are read-only. Do not add Figma mutation APIs to them.

## Collection Sequence

1. Confirm the connected file and obtain its stable file key.
2. Run the variable collector once with `mode: "inventory"`.
3. Run it with `mode: "variables"` in bounded collection chunks. For a collection larger than `maxVariables`, continue from the reported `collection_progress.end` with `startByCollection`. Every collection from the inventory must eventually appear in `completed_collection_ids` before variable coverage can be complete.
4. When node usage, bindings, hardcoded values, or semantic gaps matter, run the property collector once with `mode: "page_inventory"`.
5. Run it with `mode: "pages"` in bounded page chunks. Every page from the inventory must complete before page, usage, or property coverage can be complete.
6. Save each returned JSON object unchanged. Never edit counts or completion markers manually.

The variable collector normalizes a COLOR mode value that combines a color and an opacity as a `composite` value. The page collector looks up every distinct bound variable ID outside the local inventory in bounded batches and records it in `referenced_variables` as `remote_library`, `stale_local_reference`, or `unresolved_reference`. A failed or empty lookup preserves the binding ID and node evidence, keeps the snapshot valid, and reduces usage coverage to `partial` instead of aborting the scan. Referenced variables never enter the local inventory.

If a read call times out, rerunning the same read-only chunk is safe. Deduplicate only by stable IDs and reject conflicting duplicate records.

## Assemble And Validate

```bash
python3 scripts/assemble_snapshot.py raw/*.json \
  --file-key VERIFIED_FILE_KEY \
  --out snapshot.json \
  --out-observations property-observations.json

python3 scripts/validate_snapshot.py snapshot.json
```

`--file-key` is required only when the execution environment does not expose `figma.fileKey`. Supply it only from verified file context.

The observation sidecar is audit evidence, not a second canonical snapshot. With complete page traversal it contains a ready-to-validate `property_coverage` object for all six families and preserves unmatched literals for semantic gap-finding. With partial traversal, `property_coverage` is `null`; complete the missing page chunks instead of inventing eligible-node totals. Validate the resulting Audit `1.5.0` object with `validate_audit_json.py`.

The assembler must not claim complete coverage when:

- any collection or page chunk is missing;
- a collector reports truncation or partial traversal;
- source file identities conflict;
- chunks use incompatible adapter versions;
- a chunk contains a collector error.
- any bound variable reference is `unresolved_reference`; page traversal may remain complete, but usage coverage must be `partial`.

## Drift And Verification

Before an approved variable write, collect and assemble a fresh snapshot, then compare only the approved variable IDs:

```bash
python3 scripts/diff_snapshots.py approved-baseline.json pre-write.json \
  --only-variable-ids approved-variable-ids.txt
```

Exit `0` means no drift, `2` means drift, `4` means the filter matched nothing, and `1` means the evidence is invalid or incomplete. Never interpret exit `4` as no drift.

For binding writes, add `--include-usages`. This requires complete page and usage coverage in both snapshots.

After a write, compare the pre-write and post-write snapshots against an exact expectation file:

```bash
python3 scripts/diff_snapshots.py pre-write.json post-write.json \
  --include-usages \
  --expect approved-changes.json
```

An expectation is the complete change object emitted by the diff, including:

- `target_kind`
- `target_id`
- `path`
- `change`
- exact `before`
- exact `after`

Exit `0` proves the detected set equals the expected set exactly. Exit `3` reports missing or unexpected changes. Do not reduce expectations to IDs and change labels.

## Boundary

The collectors and assembler produce evidence. They do not classify findings, approve changes, or write to Figma. The canonical snapshot remains the only raw-data contract and Audit `1.5.0` remains the only audit-output contract.
