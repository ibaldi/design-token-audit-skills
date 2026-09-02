#!/usr/bin/env python3
"""Validate a token-value-fix evidence proposal."""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any


TYPES = {"COLOR", "FLOAT", "STRING", "BOOLEAN"}
STATUSES = {"proposed", "held", "not_actionable", "verified"}
OPERATIONS = {"set_literal", "set_alias"}
COVERAGE = {"complete", "partial", "not_observable", "failed"}
RISKS = {"low", "medium", "high"}
FAMILIES = {"opacity", "dimension", "typography", "unitless", "other"}
PREDICTION_METHODS = {"sandbox_round_trip", "adapter_documentation", "observed_equivalent", "not_observable"}
PREDICTION_STATUSES = {"supported", "mismatch", "not_observable"}
REQUIRED_TOP = {
    "contract_version", "proposal_id", "source_audit_id", "source_audit_timestamp",
    "file_key", "read_only_evidence", "status", "variable", "changes", "summary",
    "documentation", "verification",
}


def is_object(value: Any) -> bool:
    return isinstance(value, dict)


def require_keys(value: Any, keys: set[str], path: str, errors: list[str]) -> None:
    if not is_object(value):
        errors.append(f"{path}: expected object")
        return
    for key in sorted(keys - value.keys()):
        errors.append(f"{path}.{key}: missing required field")


def require_string(value: Any, path: str, errors: list[str]) -> None:
    if not isinstance(value, str) or not value.strip():
        errors.append(f"{path}: expected non-empty string")


def require_enum(value: Any, allowed: set[str], path: str, errors: list[str]) -> None:
    if value not in allowed:
        errors.append(f"{path}: expected one of {sorted(allowed)}, got {value!r}")


def finite_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def require_timestamp(value: Any, path: str, errors: list[str]) -> None:
    require_string(value, path, errors)
    if isinstance(value, str):
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
            if parsed.utcoffset() is None:
                errors.append(f"{path}: expected timezone-aware ISO-8601 timestamp")
        except ValueError:
            errors.append(f"{path}: invalid ISO-8601 timestamp")


def validate_literal(value: Any, resolved_type: Any, path: str, errors: list[str]) -> None:
    if resolved_type == "FLOAT" and not finite_number(value):
        errors.append(f"{path}: expected finite FLOAT")
    elif resolved_type == "STRING" and not isinstance(value, str):
        errors.append(f"{path}: expected STRING")
    elif resolved_type == "BOOLEAN" and not isinstance(value, bool):
        errors.append(f"{path}: expected BOOLEAN")
    elif resolved_type == "COLOR":
        require_keys(value, {"r", "g", "b", "a"}, path, errors)
        if is_object(value):
            for channel in ("r", "g", "b", "a"):
                channel_value = value.get(channel)
                if not finite_number(channel_value) or not 0 <= channel_value <= 1:
                    errors.append(f"{path}.{channel}: expected normalized channel from 0 to 1")


def validate_representation(value: Any, resolved_type: Any, path: str, errors: list[str]) -> None:
    require_keys(value, {"kind"}, path, errors)
    if not is_object(value):
        return
    kind = value.get("kind")
    require_enum(kind, {"literal", "alias"}, f"{path}.kind", errors)
    if kind == "literal":
        if "value" not in value:
            errors.append(f"{path}.value: missing required field")
        else:
            validate_literal(value.get("value"), resolved_type, f"{path}.value", errors)
    elif kind == "alias":
        require_keys(value, {"target_variable_id", "target_variable_name", "target_variable_type"}, path, errors)
        require_string(value.get("target_variable_id"), f"{path}.target_variable_id", errors)
        require_string(value.get("target_variable_name"), f"{path}.target_variable_name", errors)
        require_enum(value.get("target_variable_type"), TYPES, f"{path}.target_variable_type", errors)
        if value.get("target_variable_type") != resolved_type:
            errors.append(f"{path}.target_variable_type: must equal variable resolved_type")


def representation_fingerprint(value: Any) -> str:
    if not is_object(value):
        return "invalid"
    if value.get("kind") == "alias":
        return f"alias:{value.get('target_variable_id')}"
    return "literal:" + json.dumps(value.get("value"), sort_keys=True, separators=(",", ":"))


def validate_numeric_semantics(value: Any, path: str, status: Any, consumers: Any, errors: list[str]) -> None:
    required = {
        "family", "current_stored_value", "proposed_stored_value", "effective_unit",
        "acceptable_effective_range", "prediction_method", "prediction_status",
    }
    require_keys(value, required, path, errors)
    if not is_object(value):
        return
    family = value.get("family")
    require_enum(family, FAMILIES, f"{path}.family", errors)
    require_string(value.get("effective_unit"), f"{path}.effective_unit", errors)
    require_enum(value.get("prediction_method"), PREDICTION_METHODS, f"{path}.prediction_method", errors)
    require_enum(value.get("prediction_status"), PREDICTION_STATUSES, f"{path}.prediction_status", errors)
    for field in ("current_stored_value", "proposed_stored_value"):
        if not finite_number(value.get(field)):
            errors.append(f"{path}.{field}: expected finite number")
    if value.get("prediction_method") == "not_observable" and value.get("prediction_status") != "not_observable":
        errors.append(f"{path}.prediction_status: not_observable method requires not_observable status")
    effective_range = value.get("acceptable_effective_range")
    if not isinstance(effective_range, list) or len(effective_range) != 2 or not all(finite_number(item) for item in effective_range):
        errors.append(f"{path}.acceptable_effective_range: expected two finite numbers")
    elif effective_range[0] > effective_range[1]:
        errors.append(f"{path}.acceptable_effective_range: lower bound must not exceed upper bound")
    if family == "opacity" and effective_range != [0, 1]:
        errors.append(f"{path}.acceptable_effective_range: opacity must use [0, 1]")
    if status == "proposed" and value.get("prediction_status") != "supported":
        errors.append(f"{path}.prediction_status: proposed change requires supported prediction")
    if family == "opacity" and isinstance(consumers, list):
        for index, consumer in enumerate(consumers):
            expected = consumer.get("expected_after_effective_value") if is_object(consumer) else None
            if not finite_number(expected) or not 0 <= expected <= 1:
                errors.append(f"{path}: consumer[{index}] expected opacity must be between 0 and 1")


def validate(data: Any) -> list[str]:
    errors: list[str] = []
    require_keys(data, REQUIRED_TOP, "$", errors)
    if not is_object(data):
        return errors
    if data.get("contract_version") != "1.0.0":
        errors.append("contract_version: expected '1.0.0'")
    for field in ("proposal_id", "source_audit_id", "file_key"):
        require_string(data.get(field), field, errors)
    require_timestamp(data.get("source_audit_timestamp"), "source_audit_timestamp", errors)
    if data.get("read_only_evidence") is not True:
        errors.append("read_only_evidence: must be true")
    status = data.get("status")
    require_enum(status, STATUSES, "status", errors)

    variable = data.get("variable")
    require_keys(variable, {"id", "name", "collection_id", "resolved_type", "remote"}, "variable", errors)
    resolved_type = variable.get("resolved_type") if is_object(variable) else None
    variable_id = variable.get("id") if is_object(variable) else None
    if is_object(variable):
        for field in ("id", "name", "collection_id"):
            require_string(variable.get(field), f"variable.{field}", errors)
        require_enum(resolved_type, TYPES, "variable.resolved_type", errors)
        if status == "proposed" and variable.get("remote") is not False:
            errors.append("variable.remote: proposed change requires a local variable")

    changes = data.get("changes")
    if not isinstance(changes, list) or not changes:
        errors.append("changes: expected non-empty array")
        changes = []
    ids: list[Any] = []
    fingerprints: list[Any] = []
    for index, change in enumerate(changes):
        path = f"changes[{index}]"
        require_keys(change, {
            "change_id", "fingerprint", "mode_id", "mode_name", "operation", "current",
            "proposed", "alias_cycle_check", "consumer_impact", "risk", "limitations", "rollback",
        }, path, errors)
        if not is_object(change):
            continue
        ids.append(change.get("change_id"))
        fingerprints.append(change.get("fingerprint"))
        for field in ("change_id", "fingerprint", "mode_id", "mode_name"):
            require_string(change.get(field), f"{path}.{field}", errors)
        operation = change.get("operation")
        require_enum(operation, OPERATIONS, f"{path}.operation", errors)
        current = change.get("current")
        proposed = change.get("proposed")
        validate_representation(current, resolved_type, f"{path}.current", errors)
        validate_representation(proposed, resolved_type, f"{path}.proposed", errors)
        if current == proposed:
            errors.append(f"{path}.proposed: must differ from current representation")
        if operation == "set_literal" and (not is_object(proposed) or proposed.get("kind") != "literal"):
            errors.append(f"{path}.operation: set_literal requires literal proposed representation")
        if operation == "set_alias" and (not is_object(proposed) or proposed.get("kind") != "alias"):
            errors.append(f"{path}.operation: set_alias requires alias proposed representation")
        if change.get("alias_cycle_check") not in {"pass", "not_applicable"}:
            errors.append(f"{path}.alias_cycle_check: expected pass or not_applicable")
        if operation == "set_alias" and change.get("alias_cycle_check") != "pass":
            errors.append(f"{path}.alias_cycle_check: set_alias requires a passing cycle check")
        rollback = change.get("rollback")
        require_keys(rollback, {"representation"}, f"{path}.rollback", errors)
        if is_object(rollback) and rollback.get("representation") != current:
            errors.append(f"{path}.rollback.representation: must exactly equal current representation")

        impact = change.get("consumer_impact")
        require_keys(impact, {
            "local_alias_coverage", "local_inbound_alias_count", "local_binding_coverage",
            "local_bound_node_count", "external_consumer_coverage", "consumers",
        }, f"{path}.consumer_impact", errors)
        consumers: Any = []
        if is_object(impact):
            for field in ("local_alias_coverage", "local_binding_coverage", "external_consumer_coverage"):
                require_enum(impact.get(field), COVERAGE, f"{path}.consumer_impact.{field}", errors)
            for field in ("local_inbound_alias_count", "local_bound_node_count"):
                value = impact.get(field)
                if not isinstance(value, int) or isinstance(value, bool) or value < 0:
                    errors.append(f"{path}.consumer_impact.{field}: expected non-negative integer")
            consumers = impact.get("consumers")
            if not isinstance(consumers, list):
                errors.append(f"{path}.consumer_impact.consumers: expected array")
                consumers = []
            for consumer_index, consumer in enumerate(consumers):
                consumer_path = f"{path}.consumer_impact.consumers[{consumer_index}]"
                require_keys(consumer, {"node_id", "property_path", "before_effective_value", "expected_after_effective_value", "tolerance"}, consumer_path, errors)
                if is_object(consumer):
                    require_string(consumer.get("node_id"), f"{consumer_path}.node_id", errors)
                    require_string(consumer.get("property_path"), f"{consumer_path}.property_path", errors)
                    for field in ("before_effective_value", "expected_after_effective_value", "tolerance"):
                        if not finite_number(consumer.get(field)):
                            errors.append(f"{consumer_path}.{field}: expected finite number")
                    if finite_number(consumer.get("tolerance")) and consumer["tolerance"] < 0:
                        errors.append(f"{consumer_path}.tolerance: must be non-negative")
            bound_node_count = impact.get("local_bound_node_count")
            unique_nodes = {consumer.get("node_id") for consumer in consumers if is_object(consumer)}
            if isinstance(bound_node_count, int) and bound_node_count != len(unique_nodes):
                errors.append(f"{path}.consumer_impact.local_bound_node_count: must equal unique consumer node count")
            if status == "proposed" and impact.get("local_alias_coverage") != "complete":
                errors.append(f"{path}.consumer_impact.local_alias_coverage: proposed change requires complete coverage")
            if status == "proposed" and impact.get("local_binding_coverage") != "complete":
                errors.append(f"{path}.consumer_impact.local_binding_coverage: proposed change requires complete coverage")
        require_enum(change.get("risk"), RISKS, f"{path}.risk", errors)
        if not isinstance(change.get("limitations"), list):
            errors.append(f"{path}.limitations: expected array")
        else:
            for limitation_index, limitation in enumerate(change["limitations"]):
                require_string(limitation, f"{path}.limitations[{limitation_index}]", errors)
        if is_object(impact) and impact.get("external_consumer_coverage") != "complete":
            if change.get("risk") != "high" or not change.get("limitations"):
                errors.append(f"{path}: incomplete external-consumer coverage requires high risk and a limitation")
        if resolved_type == "FLOAT":
            if "numeric_semantics" not in change:
                errors.append(f"{path}.numeric_semantics: required for FLOAT change")
            else:
                validate_numeric_semantics(change.get("numeric_semantics"), f"{path}.numeric_semantics", status, consumers, errors)
                numeric = change.get("numeric_semantics")
                if is_object(numeric) and is_object(current) and current.get("kind") == "literal":
                    if numeric.get("current_stored_value") != current.get("value"):
                        errors.append(f"{path}.numeric_semantics.current_stored_value: must equal current literal")
                if is_object(numeric) and is_object(proposed) and proposed.get("kind") == "literal":
                    if numeric.get("proposed_stored_value") != proposed.get("value"):
                        errors.append(f"{path}.numeric_semantics.proposed_stored_value: must equal proposed literal")

        expected_fingerprint = f"value|{variable_id}|{change.get('mode_id')}|{operation}|{representation_fingerprint(proposed)}"
        if change.get("fingerprint") != expected_fingerprint:
            errors.append(f"{path}.fingerprint: expected {expected_fingerprint!r}")

    if len(ids) != len(set(ids)):
        errors.append("changes: duplicate change IDs")
    if len(fingerprints) != len(set(fingerprints)):
        errors.append("changes: duplicate fingerprints")
    summary = data.get("summary")
    require_keys(summary, {"changes_total", "by_operation", "risk", "rollback_tuples"}, "summary", errors)
    if is_object(summary):
        if summary.get("changes_total") != len(changes):
            errors.append("summary.changes_total: must equal changes length")
        expected_operations = Counter(change.get("operation") for change in changes if is_object(change))
        if summary.get("by_operation") != {operation: expected_operations.get(operation, 0) for operation in sorted(OPERATIONS)}:
            errors.append("summary.by_operation: must be derived from changes")
        if summary.get("rollback_tuples") != len(changes):
            errors.append("summary.rollback_tuples: must equal changes length")
        risk_rank = {"low": 0, "medium": 1, "high": 2}
        risks = [change.get("risk") for change in changes if is_object(change) and change.get("risk") in risk_rank]
        expected_risk = max(risks, key=risk_rank.get) if risks else None
        if summary.get("risk") != expected_risk:
            errors.append("summary.risk: must equal highest change risk")
    documentation = data.get("documentation")
    require_keys(documentation, {"changelog", "reference"}, "documentation", errors)
    if is_object(documentation):
        for field in ("changelog", "reference"):
            require_string(documentation.get(field), f"documentation.{field}", errors)
    verification = data.get("verification")
    require_keys(verification, {"consumer_resolution", "visual_check", "independent_scan"}, "verification", errors)
    if is_object(verification):
        for field in ("consumer_resolution", "visual_check", "independent_scan"):
            require_string(verification.get(field), f"verification.{field}", errors)
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("proposal", type=Path)
    args = parser.parse_args()
    try:
        data = json.loads(args.proposal.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    errors = validate(data)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print("token value fix evidence is valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
