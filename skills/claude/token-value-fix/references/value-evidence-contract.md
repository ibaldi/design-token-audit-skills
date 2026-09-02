# Token Value Fix Evidence Contract

Set `contract_version` to `1.0.0`. This record is separate from the schema `1.5.0` read-only audit and must reference its `audit_id`.

## Evidence Requirements

Capture:

- proposal ID, source audit ID and timestamp, file key, and read-only evidence status
- local variable ID, name, collection ID, resolved type, and remote status
- one exact record per affected mode
- current and proposed literal or alias representation
- a deterministic proposed-value fingerprint
- alias target validity, inbound aliases, bound node consumers, and external-consumer coverage
- numeric family, representation, range, and prediction evidence for FLOAT values
- risk, limitations, exact rollback representation, documentation plan, and verification plan

The exact tuple is `variable_id + mode_id + operation + proposed_value_fingerprint`.

## Value Representations

Use `kind: literal` with a type-correct `value`, or `kind: alias` with `target_variable_id`, `target_variable_name`, and `target_variable_type`. Literal types must match the variable's resolved type. COLOR channels use normalized `0–1` RGBA values.

An alias proposal requires an existing same-type target, complete required-mode coverage, and a cycle check. Do not use this workflow to create the alias target.

## FLOAT Semantics

Every FLOAT change includes:

```json
{
  "family": "opacity",
  "current_stored_value": 0.45,
  "proposed_stored_value": 45.0,
  "effective_unit": "normalized_ratio",
  "acceptable_effective_range": [0, 1],
  "prediction_method": "sandbox_round_trip",
  "prediction_status": "supported"
}
```

Allowed families are `opacity`, `dimension`, `typography`, `unitless`, and `other`. Prediction methods are `sandbox_round_trip`, `adapter_documentation`, `observed_equivalent`, or `not_observable`. A write-ready proposal requires `prediction_status: supported`; `mismatch` or `not_observable` stays held.

For opacity, the expected effective values on bound consumers must be within `0–1`. Stored values are not constrained to that range because an adapter or UI may expose a different representation. Never infer a universal conversion rule from one observed case.

## Consumer Evidence

Local alias and bound-node coverage must be complete for a write-ready proposal. Record each observed bound consumer with node ID, property path, effective value before the change, expected effective value after the change, and tolerance. Record external-consumer coverage separately and disclose all limitations.

## Rollback

Every tuple carries the exact prior representation as its rollback value. The preview requests approval for the proposed value and that rollback together. Rollback is allowed only after failed immediate verification, only when no intervening drift is observed, and only to the captured prior representation.

## Safe Failure

Invalid or stale evidence, uncertain numeric semantics, incomplete local impact, unresolved aliases, missing rollback, or unsupported adapter behavior closes the write gate. Return a held or blocked proposal; manual plausibility review does not make it write-ready.
