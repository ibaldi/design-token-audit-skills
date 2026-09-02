# Property Traversal Contract

Contract version: `1.0.0`

Use this contract to prove which variable-bindable Figma node properties were inspected. It closes the gap between accepting a binding finding and demonstrating that the scan looked for every property family supported by the active adapter.

This contract is capability-driven. Build the declared property list from the adapter's documented capabilities, never from the variables or bindings already present in the file. A property with no matching token still belongs in traversal coverage.

## Canonical Property Families

For the official Figma Plugin API profile, declare these patterns:

- `simple_node_fields`: `height`, `width`, `characters`, `itemSpacing`, `paddingLeft`, `paddingRight`, `paddingTop`, `paddingBottom`, `visible`, `cornerRadius`, `topLeftRadius`, `topRightRadius`, `bottomLeftRadius`, `bottomRightRadius`, `minWidth`, `maxWidth`, `minHeight`, `maxHeight`, `counterAxisSpacing`, `strokeWeight`, `strokeTopWeight`, `strokeRightWeight`, `strokeBottomWeight`, `strokeLeftWeight`, `opacity`, `gridRowGap`, `gridColumnGap`
- `paints`: `fills[*].color`, `strokes[*].color`, `textRangeFills[*].color`
- `effects`: `effects[*].radius`, `effects[*].color`, `effects[*].spread`, `effects[*].offsetX`, `effects[*].offsetY`
- `layout_grids`: `layoutGrids[*].sectionSize`, `layoutGrids[*].count`, `layoutGrids[*].offset`, `layoutGrids[*].gutterSize`
- `typography`: `fontFamily`, `fontSize`, `fontStyle`, `fontWeight`, `letterSpacing`, `lineHeight`, `paragraphSpacing`, `paragraphIndent`
- `component_properties`: `componentProperties[*]`

Apply node-type and subtype conditions before counting a property as eligible. For example, shadow and blur effects expose different bindable subfields, layout-grid fields depend on pattern and alignment, and independent-corner nodes may report four corner bindings instead of one `cornerRadius` binding.

`rotation`, `blendMode`, `layoutSizingHorizontal`, and `layoutSizingVertical` are not part of this variable-binding profile. They may be audited separately as ordinary design or layout observations, but must not be reported as variable-binding candidates unless a future adapter version supplies explicit bindable-property evidence.

## Audit Object

Audit schema 1.5 requires a top-level `property_coverage` object:

```json
{
  "contract_version": "1.0.0",
  "status": "partial",
  "source": {
    "adapter_id": "connected-figma-tool",
    "capability_basis": "adapter_declared",
    "canonical_profile": null
  },
  "families": {
    "simple_node_fields": {
      "support_status": "supported",
      "status": "complete",
      "declared_paths": ["opacity"],
      "properties": [
        {
          "property_path": "opacity",
          "status": "complete",
          "eligible_nodes": 18,
          "inspected_nodes": 18,
          "bound_count": 2,
          "literal_count": 16,
          "mixed_or_unsupported_count": 0,
          "limitations": []
        }
      ],
      "limitations": []
    }
  },
  "excluded_non_bindable_properties": [
    "rotation",
    "blendMode",
    "layoutSizingHorizontal",
    "layoutSizingVertical"
  ],
  "limitations": ["The connected adapter did not expose effect bindings."]
}
```

All six family keys are required even when a family is unavailable.

## Source Rules

`capability_basis` is one of:

- `official_figma_plugin_api`: use `canonical_profile: figma_plugin_api_2026_09` and declare the complete canonical property patterns above.
- `adapter_declared`: use the exact property patterns the connected adapter says it can read.
- `structured_export`: use the exact property patterns present in the export specification, not merely those observed in one file.
- `mixed`: declare the union of capabilities and state source-specific limitations.

The source capability declaration is part of the evidence. Never reduce it because a file has no variables of a matching type or because a property produced no findings.

## Family And Property Rules

Family `support_status` is `supported`, `unsupported`, or `not_observable`.

- `supported` requires declared paths and one property record for every declared path. Family status is `complete`, `partial`, `not_applicable`, or `failed`.
- `unsupported` requires status `unsupported`, empty paths and records, and a limitation.
- `not_observable` requires status `not_observable`, empty paths and records, and a limitation.

For each property record:

- `inspected_nodes = bound_count + literal_count + mixed_or_unsupported_count`
- `inspected_nodes <= eligible_nodes`
- `complete` requires all eligible nodes inspected
- `partial` requires uninspected eligible nodes and a limitation
- `not_applicable` requires zero eligible and inspected nodes
- `failed` requires a limitation

Literal counts include values with no existing-variable match. A complete traversal may legitimately produce no binding findings; coverage proves that the absence is meaningful.

Top-level status is:

- `complete` only when every family is complete or not applicable
- `not_observable` when every family is not observable
- `failed` when any family failed
- `partial` for every other mixture, including unsupported or partially observable families

## Downstream Use

Binding findings remain exact proposals under the audit-output contract. Property coverage is not a proposal and never authorizes a write.

Semantic gap-finding must consume literal counts and the underlying node/property evidence, including unmatched literals. If relevant property coverage is partial or unavailable, its Phase-1 assessment cannot claim complete coverage.
