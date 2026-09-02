# Binding Evidence Contract

Use this contract for binding findings, previews, writes, and verification.

## Evidence Record

Capture at least:

```text
Binding finding ID
Fingerprint
Source audit ID and timestamp
File key, page ID, and page name
Node ID, name, and type
Property path
Current representation and resolved type
Expected representation
Target variable ID, name, collection, and resolved type
Relevant mode values or aliases
Scope compatibility
For FLOAT: numeric family, current effective value, stored or adapter-reported target value, target value resolved for this consumer, intended effective value, tolerance, equivalence, and resolution method
Operation
Confidence
Risk and consumer impact
Evidence source
Limitations
```

Node names and screenshots are supporting evidence, not stable identity. Use Figma IDs when observable.

## Property Paths

Use explicit property paths. Examples:

- `fills[0].color`
- `strokes[0].color`
- `opacity`
- `paddingTop`
- `paddingRight`
- `paddingBottom`
- `paddingLeft`
- `itemSpacing`
- `topLeftRadius`
- `topRightRadius`
- `bottomRightRadius`
- `bottomLeftRadius`

For array properties, bind only the approved index. Do not replace or reorder other paints as a side effect.

## Type Compatibility

Verify the node property and variable type before preview and again before write:

| Property family | Required variable type |
| --- | --- |
| fill or stroke color | `COLOR` |
| opacity, padding, gap, radius, size, stroke weight | `FLOAT` |
| supported text content | `STRING` |
| supported visibility or toggle | `BOOLEAN` |

A matching type is necessary but not sufficient. Also verify modes, scope intent, and whether the active adapter supports that exact property.

## FLOAT Consumer Semantics

Do not assume that equal-looking numbers have equal consumer meaning. A FLOAT may represent a dimension, typography value, unitless number, or opacity. UI, API, export, and adapter representations may expose different display scales.

For every FLOAT target, resolve the variable for the exact consumer node using `variable.resolveForConsumer(node)` or a documented adapter-equivalent operation. Record the stored or adapter-reported variable value separately from the resolved consumer value. Compare the resolved consumer value with the intended effective property value using an explicit tolerance.

For opacity, effective node or paint values must be within `0–1`. A literal `0.45` may display as 45 percent, but that does not prove that a separately represented variable value of `0.45` resolves to the same consumer value. If a target resolves to `0.0045`, the candidate is a mismatch and must remain held.

Type compatibility, `OPACITY` scope, matching names, and matching displayed values do not replace this preflight. If consumer resolution is unavailable, do not make the binding write-ready.

## Classification

- `bind`: current representation is literal or unbound; expected representation is an existing variable
- `rebind`: current representation is a different existing variable
- `unbind`: current representation is a variable; expected representation is unbound
- `no_op`: current and expected variable IDs already match

Do not promote `no_op` records to write candidates. Use them as controls during verification.

## Safe Failure

Stop before writing when evidence is incomplete. If a batch applies partially, record successful tuples and failed tuples separately, do not retry automatically, and require a new read-only state plus revised approval before further mutation.
