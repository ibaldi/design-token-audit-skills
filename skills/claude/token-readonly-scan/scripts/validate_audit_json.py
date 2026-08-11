#!/usr/bin/env python3
"""Validate a design-token read-only audit JSON artifact."""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any


TOP_STATUSES = {"complete", "complete_with_limitations", "blocked", "failed"}
METHODS = {"figma_plugin_api", "connected_figma_tool", "user_supplied_export", "mixed"}
COVERAGE_STATUSES = {"complete", "partial", "not_observable", "not_configured", "failed"}
CATEGORIES = {
    "collection", "mode", "description", "scope", "naming", "alias", "usage",
    "accessibility", "typography", "changelog", "reference", "other",
}
SEVERITIES = {"critical", "high", "medium", "low", "info"}
CONFIDENCES = {"high", "medium", "low"}
FINDING_STATUSES = {"open", "needs_review", "held", "not_actionable"}
TARGET_KINDS = {"collection", "variable", "mode", "node", "page", "external_consumer"}
REQUIRED_TOP = {
    "schema_version", "audit_id", "audit_type", "status", "read_only", "started_at",
    "completed_at", "source", "inspection", "coverage", "inventory", "findings",
    "summary", "recommended_next_pass",
}
REQUIRED_COVERAGE = {"collections", "variables", "pages", "aliases", "external_consumers"}
REQUIRED_FINDING = {
    "id", "fingerprint", "rule_id", "category", "severity", "confidence", "title",
    "status", "targets", "observed", "expected", "evidence", "risk", "recommendation",
    "limitations",
}


def is_object(value: Any) -> bool:
    return isinstance(value, dict)


def require_keys(value: Any, keys: set[str], path: str, errors: list[str]) -> None:
    if not is_object(value):
        errors.append(f"{path}: expected object")
        return
    for key in sorted(keys - value.keys()):
        errors.append(f"{path}.{key}: missing required field")


def require_enum(value: Any, allowed: set[str], path: str, errors: list[str]) -> None:
    if value not in allowed:
        errors.append(f"{path}: expected one of {sorted(allowed)}, got {value!r}")


def require_list(value: Any, path: str, errors: list[str]) -> bool:
    if not isinstance(value, list):
        errors.append(f"{path}: expected array")
        return False
    return True


def require_nonempty_string(value: Any, path: str, errors: list[str]) -> None:
    if not isinstance(value, str) or not value.strip():
        errors.append(f"{path}: expected non-empty string")


def parse_timestamp(value: Any, path: str, errors: list[str]) -> datetime | None:
    if not isinstance(value, str):
        errors.append(f"{path}: expected ISO-8601 string")
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        errors.append(f"{path}: invalid ISO-8601 timestamp")
        return None


def validate_coverage(coverage: Any, top_status: Any, errors: list[str]) -> None:
    require_keys(coverage, REQUIRED_COVERAGE, "coverage", errors)
    if not is_object(coverage):
        return
    statuses: list[Any] = []
    for name in sorted(REQUIRED_COVERAGE):
        section = coverage.get(name)
        if not is_object(section):
            errors.append(f"coverage.{name}: expected object")
            continue
        status = section.get("status")
        require_enum(status, COVERAGE_STATUSES, f"coverage.{name}.status", errors)
        statuses.append(status)
    for key in ("unobservable_fields", "limitations"):
        if key in coverage:
            require_list(coverage[key], f"coverage.{key}", errors)
    if top_status == "complete" and any(status != "complete" for status in statuses):
        errors.append("status: cannot be complete when a required coverage section is not complete")


def validate_finding(finding: Any, index: int, errors: list[str]) -> None:
    path = f"findings[{index}]"
    require_keys(finding, REQUIRED_FINDING, path, errors)
    if not is_object(finding):
        return

    category = finding.get("category")
    require_enum(category, CATEGORIES, f"{path}.category", errors)
    require_enum(finding.get("severity"), SEVERITIES, f"{path}.severity", errors)
    require_enum(finding.get("confidence"), CONFIDENCES, f"{path}.confidence", errors)
    require_enum(finding.get("status"), FINDING_STATUSES, f"{path}.status", errors)
    for key in ("fingerprint", "rule_id", "title", "risk", "recommendation"):
        require_nonempty_string(finding.get(key), f"{path}.{key}", errors)

    finding_id = finding.get("id")
    expected_prefix = category.upper() if isinstance(category, str) else "[CATEGORY]"
    if not isinstance(finding_id, str) or not re.fullmatch(r"DTA-[A-Z]+-\d{3}", finding_id):
        errors.append(f"{path}.id: expected DTA-{{CATEGORY}}-{{NNN}}")
    elif isinstance(category, str) and not finding_id.startswith(f"DTA-{expected_prefix}-"):
        errors.append(f"{path}.id: category prefix does not match {category!r}")

    targets = finding.get("targets")
    if require_list(targets, f"{path}.targets", errors):
        if not targets:
            errors.append(f"{path}.targets: must contain at least one target")
        for target_index, target in enumerate(targets):
            target_path = f"{path}.targets[{target_index}]"
            if not is_object(target):
                errors.append(f"{target_path}: expected object")
                continue
            require_enum(target.get("kind"), TARGET_KINDS, f"{target_path}.kind", errors)
            require_nonempty_string(target.get("id"), f"{target_path}.id", errors)

    evidence = finding.get("evidence")
    if require_list(evidence, f"{path}.evidence", errors):
        if not evidence:
            errors.append(f"{path}.evidence: must contain at least one evidence item")
        for evidence_index, item in enumerate(evidence):
            item_path = f"{path}.evidence[{evidence_index}]"
            if not is_object(item):
                errors.append(f"{item_path}: expected object")
                continue
            require_nonempty_string(item.get("source"), f"{item_path}.source", errors)
            require_nonempty_string(item.get("detail"), f"{item_path}.detail", errors)

    for key in ("limitations",):
        require_list(finding.get(key), f"{path}.{key}", errors)
    for key in ("observed", "expected"):
        if not is_object(finding.get(key)):
            errors.append(f"{path}.{key}: expected object")


def validate_summary(summary: Any, findings: list[Any], errors: list[str]) -> None:
    required = {"findings_total", "by_severity", "by_category", "holds", "risk_statement"}
    require_keys(summary, required, "summary", errors)
    if not is_object(summary):
        return

    valid_findings = [finding for finding in findings if is_object(finding)]
    if summary.get("findings_total") != len(findings):
        errors.append("summary.findings_total: must equal the findings array length")

    expected_severity = Counter(finding.get("severity") for finding in valid_findings)
    actual_severity = summary.get("by_severity")
    if not is_object(actual_severity):
        errors.append("summary.by_severity: expected object")
    else:
        for severity in SEVERITIES:
            if actual_severity.get(severity, 0) != expected_severity.get(severity, 0):
                errors.append(f"summary.by_severity.{severity}: count does not match findings")

    expected_category = Counter(finding.get("category") for finding in valid_findings)
    actual_category = summary.get("by_category")
    if not is_object(actual_category):
        errors.append("summary.by_category: expected object")
    else:
        if {key: value for key, value in actual_category.items() if value} != dict(expected_category):
            errors.append("summary.by_category: counts do not match findings")

    expected_holds = sum(finding.get("status") == "held" for finding in valid_findings)
    if summary.get("holds") != expected_holds:
        errors.append("summary.holds: count does not match held findings")
    require_nonempty_string(summary.get("risk_statement"), "summary.risk_statement", errors)


def validate_inventory(inventory: Any, errors: list[str]) -> None:
    if not is_object(inventory):
        errors.append("inventory: expected object")
        return
    total = inventory.get("variables_total")
    by_collection = inventory.get("variables_by_collection")
    by_type = inventory.get("variables_by_type")
    if isinstance(total, int):
        if is_object(by_collection) and all(isinstance(value, int) for value in by_collection.values()):
            if sum(by_collection.values()) != total:
                errors.append("inventory.variables_by_collection: counts must sum to variables_total")
        if is_object(by_type) and all(isinstance(value, int) for value in by_type.values()):
            if sum(by_type.values()) != total:
                errors.append("inventory.variables_by_type: counts must sum to variables_total")
        descriptions = inventory.get("descriptions")
        if is_object(descriptions) and all(isinstance(descriptions.get(key), int) for key in ("complete", "empty")):
            if descriptions["complete"] + descriptions["empty"] != total:
                errors.append("inventory.descriptions: complete plus empty must equal variables_total")


def validate(data: Any) -> list[str]:
    errors: list[str] = []
    require_keys(data, REQUIRED_TOP, "$", errors)
    if not is_object(data):
        return errors

    if data.get("schema_version") != "1.0.0":
        errors.append("schema_version: expected '1.0.0'")
    if data.get("audit_type") != "figma_token_readonly_scan":
        errors.append("audit_type: expected 'figma_token_readonly_scan'")
    if data.get("read_only") is not True:
        errors.append("read_only: must be true")
    require_nonempty_string(data.get("audit_id"), "audit_id", errors)
    require_enum(data.get("status"), TOP_STATUSES, "status", errors)

    started = parse_timestamp(data.get("started_at"), "started_at", errors)
    completed = parse_timestamp(data.get("completed_at"), "completed_at", errors)
    if started and completed and completed < started:
        errors.append("completed_at: must not be earlier than started_at")

    require_keys(data.get("source"), {"file_key", "file_name", "pages_requested"}, "source", errors)
    inspection = data.get("inspection")
    require_keys(inspection, {"method", "tool_name", "capabilities", "unavailable_operations"}, "inspection", errors)
    if is_object(inspection):
        require_enum(inspection.get("method"), METHODS, "inspection.method", errors)
        require_nonempty_string(inspection.get("tool_name"), "inspection.tool_name", errors)
        require_list(inspection.get("capabilities"), "inspection.capabilities", errors)
        require_list(inspection.get("unavailable_operations"), "inspection.unavailable_operations", errors)

    validate_coverage(data.get("coverage"), data.get("status"), errors)
    validate_inventory(data.get("inventory"), errors)

    findings = data.get("findings")
    if not require_list(findings, "findings", errors):
        findings = []
    for index, finding in enumerate(findings):
        validate_finding(finding, index, errors)

    ids = [finding.get("id") for finding in findings if is_object(finding)]
    fingerprints = [finding.get("fingerprint") for finding in findings if is_object(finding)]
    if len(ids) != len(set(ids)):
        errors.append("findings: duplicate display IDs")
    if len(fingerprints) != len(set(fingerprints)):
        errors.append("findings: duplicate fingerprints")

    validate_summary(data.get("summary"), findings, errors)
    return errors


def self_test() -> int:
    sample = {
        "schema_version": "1.0.0",
        "audit_id": "dta-self-test",
        "audit_type": "figma_token_readonly_scan",
        "status": "complete_with_limitations",
        "read_only": True,
        "started_at": "2026-08-11T17:30:00Z",
        "completed_at": "2026-08-11T17:31:00Z",
        "source": {"file_key": "abc", "file_name": "Test", "pages_requested": []},
        "inspection": {
            "method": "figma_plugin_api", "tool_name": "Figma Plugin API",
            "capabilities": ["local_variables"], "unavailable_operations": ["external_consumer_search"],
        },
        "coverage": {
            "collections": {"status": "complete"},
            "variables": {"status": "complete"},
            "pages": {"status": "not_configured"},
            "aliases": {"status": "complete"},
            "external_consumers": {"status": "not_observable"},
            "unobservable_fields": [], "limitations": ["External consumers not searched"],
        },
        "inventory": {
            "variables_total": 1, "variables_by_collection": {"Global": 1},
            "variables_by_type": {"COLOR": 1}, "descriptions": {"complete": 1, "empty": 0},
        },
        "findings": [],
        "summary": {
            "findings_total": 0, "by_severity": {}, "by_category": {}, "holds": 0,
            "risk_statement": "No findings; external consumers were not observable.",
        },
        "recommended_next_pass": None,
    }
    if validate(sample):
        print("self-test failed: valid sample rejected", file=sys.stderr)
        return 1
    sample["read_only"] = False
    if not validate(sample):
        print("self-test failed: invalid sample accepted", file=sys.stderr)
        return 1
    print("self-test passed")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", nargs="?", help="Audit JSON path, or - for stdin")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        return self_test()
    if not args.path:
        parser.error("path is required unless --self-test is used")

    try:
        raw = sys.stdin.read() if args.path == "-" else Path(args.path).read_text(encoding="utf-8")
        data = json.loads(raw)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"invalid audit JSON: {exc}", file=sys.stderr)
        return 2

    errors = validate(data)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        print(f"validation failed with {len(errors)} error(s)", file=sys.stderr)
        return 1
    print("audit JSON is valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
