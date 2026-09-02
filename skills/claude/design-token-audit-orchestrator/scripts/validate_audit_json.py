#!/usr/bin/env python3
"""Validate a design-token read-only audit JSON artifact."""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


TOP_STATUSES = {"complete", "complete_with_limitations", "blocked", "failed"}
METHODS = {"figma_plugin_api", "connected_figma_tool", "user_supplied_export", "mixed"}
COVERAGE_STATUSES = {"complete", "partial", "not_observable", "not_configured", "failed"}
DOCUMENTATION_STATUSES = {
    "ready", "ready_with_limitations", "not_ready", "not_observable", "not_configured", "failed",
}
DOCUMENT_CHECK_STATUSES = {"pass", "needs_review", "missing", "not_observable", "not_configured", "failed"}
CATEGORIES = {
    "collection", "mode", "description", "scope", "naming", "alias", "usage",
    "accessibility", "typography", "changelog", "reference", "other",
}
SEVERITIES = {"critical", "high", "medium", "low", "info"}
CONFIDENCES = {"high", "medium", "low"}
FINDING_STATUSES = {"open", "needs_review", "held", "not_actionable"}
TARGET_KINDS = {"collection", "variable", "mode", "node", "page", "external_consumer"}
BINDING_OPERATIONS = {"bind", "rebind", "unbind", "no_op"}
BINDING_STATUSES = {"proposed", "held", "not_actionable", "verified"}
BINDING_VALUE_TYPES = {"COLOR", "FLOAT", "STRING", "BOOLEAN"}
BINDING_CURRENT_KINDS = {"literal", "variable", "unbound"}
BINDING_EXPECTED_KINDS = {"variable", "unbound"}
BINDING_SCOPE_STATUSES = {"compatible", "needs_review", "incompatible"}
NUMERIC_FAMILIES = {"opacity", "dimension", "typography", "unitless", "other"}
NUMERIC_EQUIVALENCE = {"equivalent", "mismatch", "not_observable"}
NUMERIC_RESOLUTION_METHODS = {
    "figma_resolve_for_consumer", "adapter_consumer_resolution", "not_observable",
}
PROPERTY_PATH_RE = re.compile(r"^[A-Za-z][A-Za-z0-9]*(?:\[\d+\])?(?:\.[A-Za-z][A-Za-z0-9]*)*$")
PROPERTY_FAMILIES = {
    "simple_node_fields": {
        "height", "width", "characters", "itemSpacing", "paddingLeft", "paddingRight",
        "paddingTop", "paddingBottom", "visible", "cornerRadius", "topLeftRadius",
        "topRightRadius", "bottomLeftRadius", "bottomRightRadius", "minWidth", "maxWidth",
        "minHeight", "maxHeight", "counterAxisSpacing", "strokeWeight", "strokeTopWeight",
        "strokeRightWeight", "strokeBottomWeight", "strokeLeftWeight", "opacity",
        "gridRowGap", "gridColumnGap",
    },
    "paints": {"fills[*].color", "strokes[*].color", "textRangeFills[*].color"},
    "effects": {
        "effects[*].radius", "effects[*].color", "effects[*].spread",
        "effects[*].offsetX", "effects[*].offsetY",
    },
    "layout_grids": {
        "layoutGrids[*].sectionSize", "layoutGrids[*].count",
        "layoutGrids[*].offset", "layoutGrids[*].gutterSize",
    },
    "typography": {
        "fontFamily", "fontSize", "fontStyle", "fontWeight", "letterSpacing",
        "lineHeight", "paragraphSpacing", "paragraphIndent",
    },
    "component_properties": {"componentProperties[*]"},
}
PROPERTY_CAPABILITY_BASES = {"official_figma_plugin_api", "adapter_declared", "structured_export", "mixed"}
PROPERTY_SUPPORT_STATUSES = {"supported", "unsupported", "not_observable"}
PROPERTY_FAMILY_STATUSES = {"complete", "partial", "not_observable", "unsupported", "not_applicable", "failed"}
PROPERTY_RECORD_STATUSES = {"complete", "partial", "not_applicable", "failed"}
NON_BINDABLE_PROPERTIES = {"rotation", "blendMode", "layoutSizingHorizontal", "layoutSizingVertical"}
REQUIRED_TOP = {
    "schema_version", "audit_id", "audit_type", "status", "read_only", "started_at",
    "completed_at", "source", "inspection", "coverage", "inventory", "documentation_readiness",
    "derived_metrics", "property_coverage", "binding_findings", "binding_summary", "findings", "summary",
    "recommended_next_pass",
}
REQUIRED_COVERAGE = {"collections", "variables", "pages", "aliases", "external_consumers"}
REQUIRED_SOURCE = {"file_key", "file_name", "pages_requested"}
REQUIRED_INSPECTION = {"method", "tool_name", "capabilities", "unavailable_operations"}
REQUIRED_INVENTORY = {
    "collections_total", "variables_total", "variables_by_collection", "variables_by_type",
    "modes_by_collection", "descriptions", "missing_mode_values", "all_scopes",
    "unresolved_aliases", "potential_orphan_candidates",
}
REQUIRED_FINDING = {
    "id", "fingerprint", "rule_id", "category", "severity", "confidence", "title",
    "status", "targets", "observed", "expected", "evidence", "risk", "recommendation",
    "limitations",
}
REQUIRED_BINDING_FINDING = {
    "finding_id", "fingerprint", "source_audit_id", "page_id", "node_id", "node_name",
    "node_type", "property_path", "property_value_type", "current", "expected", "operation",
    "confidence", "status", "evidence", "risk", "limitations",
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


def require_nonnegative_int(value: Any, path: str, errors: list[str]) -> None:
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        errors.append(f"{path}: expected non-negative integer")


def require_finite_number(value: Any, path: str, errors: list[str]) -> bool:
    if not isinstance(value, (int, float)) or isinstance(value, bool) or not math.isfinite(value):
        errors.append(f"{path}: expected finite number")
        return False
    return True


def require_string_list(value: Any, path: str, errors: list[str]) -> bool:
    if not require_list(value, path, errors):
        return False
    for index, item in enumerate(value):
        require_nonempty_string(item, f"{path}[{index}]", errors)
    return True


def parse_timestamp(value: Any, path: str, errors: list[str]) -> datetime | None:
    if not isinstance(value, str):
        errors.append(f"{path}: expected ISO-8601 string")
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if parsed.tzinfo is None or parsed.utcoffset() != timezone.utc.utcoffset(parsed):
            errors.append(f"{path}: expected UTC ISO-8601 timestamp")
            return None
        return parsed
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
            require_string_list(coverage[key], f"coverage.{key}", errors)

    collections = coverage.get("collections")
    if is_object(collections):
        for key in ("observed", "expected"):
            value = collections.get(key)
            if value is not None:
                require_nonnegative_int(value, f"coverage.collections.{key}", errors)
        if collections.get("status") == "complete":
            if collections.get("expected") is None:
                errors.append("coverage.collections.expected: required when status is complete")
            elif collections.get("observed") != collections.get("expected"):
                errors.append("coverage.collections: observed must equal expected when complete")

    variables = coverage.get("variables")
    if is_object(variables):
        for key in ("captured", "failed"):
            require_nonnegative_int(variables.get(key), f"coverage.variables.{key}", errors)
        if variables.get("status") == "complete" and variables.get("failed") != 0:
            errors.append("coverage.variables.failed: must be zero when status is complete")

    pages = coverage.get("pages")
    if is_object(pages):
        require_string_list(pages.get("fully_traversed_ids"), "coverage.pages.fully_traversed_ids", errors)
        require_string_list(pages.get("not_traversed_ids"), "coverage.pages.not_traversed_ids", errors)
        traversed = pages.get("fully_traversed_ids") if isinstance(pages.get("fully_traversed_ids"), list) else []
        not_traversed = pages.get("not_traversed_ids") if isinstance(pages.get("not_traversed_ids"), list) else []
        if set(traversed) & set(not_traversed):
            errors.append("coverage.pages: traversed and not-traversed IDs must be disjoint")
        if pages.get("status") == "complete" and not_traversed:
            errors.append("coverage.pages.not_traversed_ids: must be empty when status is complete")

    aliases = coverage.get("aliases")
    if is_object(aliases):
        require_nonnegative_int(aliases.get("unresolved_remote"), "coverage.aliases.unresolved_remote", errors)

    external = coverage.get("external_consumers")
    if is_object(external):
        require_string_list(external.get("searched"), "coverage.external_consumers.searched", errors)
        require_string_list(external.get("not_searched"), "coverage.external_consumers.not_searched", errors)

    if top_status == "complete" and any(status != "complete" for status in statuses):
        errors.append("status: cannot be complete when a required coverage section is not complete")
    if top_status == "complete_with_limitations":
        limitations = coverage.get("limitations") if isinstance(coverage.get("limitations"), list) else []
        if all(status == "complete" for status in statuses) and not limitations:
            errors.append("status: complete_with_limitations requires incomplete coverage or a limitation")
    if top_status == "blocked":
        core_statuses = [
            coverage.get(name, {}).get("status") if is_object(coverage.get(name)) else None
            for name in ("collections", "variables")
        ]
        if all(status == "complete" for status in core_statuses):
            errors.append("status: blocked requires incomplete or failed core inventory coverage")


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
            require_keys(
                target, {"kind", "id", "name", "collection_id", "mode_id", "page_id"},
                target_path, errors,
            )
            require_enum(target.get("kind"), TARGET_KINDS, f"{target_path}.kind", errors)
            require_nonempty_string(target.get("id"), f"{target_path}.id", errors)
            if target.get("name") is not None:
                require_nonempty_string(target.get("name"), f"{target_path}.name", errors)
            for nullable_id in ("collection_id", "mode_id", "page_id"):
                if target.get(nullable_id) is not None:
                    require_nonempty_string(target.get(nullable_id), f"{target_path}.{nullable_id}", errors)

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
        if not is_object(finding.get(key)) or not finding.get(key):
            errors.append(f"{path}.{key}: expected object")

    if finding.get("severity") == "critical":
        observed = finding.get("observed")
        active_impact = observed.get("active_consumer_impact") if is_object(observed) else None
        if not isinstance(active_impact, str) or not active_impact.strip():
            errors.append(f"{path}.observed.active_consumer_impact: required for critical severity")

    risk = finding.get("risk")
    if isinstance(risk, str):
        risk_label = re.fullmatch(r"\s*(critical|high|medium|low|info)(?:\s+risk)?\s*[:.]?\s*", risk, re.IGNORECASE)
        if risk_label and risk_label.group(1).lower() != finding.get("severity"):
            errors.append(f"{path}.risk: severity label conflicts with finding severity")

    if isinstance(targets, list) and all(is_object(target) for target in targets):
        target_ids = sorted(target.get("id") for target in targets if isinstance(target.get("id"), str))
        mode_ids = sorted({target.get("mode_id") for target in targets if isinstance(target.get("mode_id"), str)})
        expected_fingerprint = "|".join(
            [str(finding.get("rule_id")), ",".join(target_ids)] + ([",".join(mode_ids)] if mode_ids else [])
        )
        if finding.get("fingerprint") != expected_fingerprint:
            errors.append(f"{path}.fingerprint: expected {expected_fingerprint!r}")


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
        if set(actual_severity) != SEVERITIES:
            errors.append("summary.by_severity: must contain exactly all severity keys")
        for severity in SEVERITIES:
            require_nonnegative_int(actual_severity.get(severity), f"summary.by_severity.{severity}", errors)
            if actual_severity.get(severity, 0) != expected_severity.get(severity, 0):
                errors.append(f"summary.by_severity.{severity}: count does not match findings")

    expected_category = Counter(finding.get("category") for finding in valid_findings)
    actual_category = summary.get("by_category")
    if not is_object(actual_category):
        errors.append("summary.by_category: expected object")
    else:
        for category, count in actual_category.items():
            require_enum(category, CATEGORIES, f"summary.by_category.{category}", errors)
            require_nonnegative_int(count, f"summary.by_category.{category}", errors)
        if {key: value for key, value in actual_category.items() if value} != dict(expected_category):
            errors.append("summary.by_category: counts do not match findings")

    expected_holds = sum(finding.get("status") == "held" for finding in valid_findings)
    if summary.get("holds") != expected_holds:
        errors.append("summary.holds: count does not match held findings")
    require_nonempty_string(summary.get("risk_statement"), "summary.risk_statement", errors)


def validate_inventory(inventory: Any, errors: list[str]) -> None:
    require_keys(inventory, REQUIRED_INVENTORY, "inventory", errors)
    if not is_object(inventory):
        return
    require_nonnegative_int(inventory.get("collections_total"), "inventory.collections_total", errors)
    total = inventory.get("variables_total")
    require_nonnegative_int(total, "inventory.variables_total", errors)
    by_collection = inventory.get("variables_by_collection")
    by_type = inventory.get("variables_by_type")
    for value, path in ((by_collection, "inventory.variables_by_collection"), (by_type, "inventory.variables_by_type")):
        if not is_object(value):
            errors.append(f"{path}: expected object")
        else:
            for name, count in value.items():
                require_nonempty_string(name, f"{path} key", errors)
                require_nonnegative_int(count, f"{path}.{name}", errors)
    if isinstance(total, int):
        if is_object(by_collection) and all(isinstance(value, int) for value in by_collection.values()):
            if sum(by_collection.values()) != total:
                errors.append("inventory.variables_by_collection: counts must sum to variables_total")
        if is_object(by_type) and all(isinstance(value, int) for value in by_type.values()):
            if sum(by_type.values()) != total:
                errors.append("inventory.variables_by_type: counts must sum to variables_total")
        descriptions = inventory.get("descriptions")
        if not is_object(descriptions):
            errors.append("inventory.descriptions: expected object")
        elif all(isinstance(descriptions.get(key), int) for key in ("complete", "empty")):
            require_nonnegative_int(descriptions.get("complete"), "inventory.descriptions.complete", errors)
            require_nonnegative_int(descriptions.get("empty"), "inventory.descriptions.empty", errors)
            if descriptions["complete"] + descriptions["empty"] != total:
                errors.append("inventory.descriptions: complete plus empty must equal variables_total")
        else:
            errors.append("inventory.descriptions: requires complete and empty integer counts")
    modes = inventory.get("modes_by_collection")
    if not is_object(modes):
        errors.append("inventory.modes_by_collection: expected object")
    else:
        for collection, collection_modes in modes.items():
            require_nonempty_string(collection, "inventory.modes_by_collection key", errors)
            if require_list(collection_modes, f"inventory.modes_by_collection.{collection}", errors):
                for index, mode in enumerate(collection_modes):
                    path = f"inventory.modes_by_collection.{collection}[{index}]"
                    require_keys(mode, {"id", "name"}, path, errors)
                    if is_object(mode):
                        require_nonempty_string(mode.get("id"), f"{path}.id", errors)
                        require_nonempty_string(mode.get("name"), f"{path}.name", errors)
    for key in ("missing_mode_values", "all_scopes", "unresolved_aliases", "potential_orphan_candidates"):
        value = inventory.get(key)
        if is_object(value):
            if value.get("status") not in {"not_observable", "not_configured"}:
                errors.append(f"inventory.{key}.status: expected not_observable or not_configured")
        else:
            require_nonnegative_int(value, f"inventory.{key}", errors)


def validate_document_check(value: Any, path: str, errors: list[str]) -> Any:
    require_keys(value, {"status", "observed", "evidence"}, path, errors)
    if not is_object(value):
        return None
    status = value.get("status")
    require_enum(status, DOCUMENT_CHECK_STATUSES, f"{path}.status", errors)
    require_string_list(value.get("evidence"), f"{path}.evidence", errors)
    if status == "pass" and value.get("observed") is None:
        errors.append(f"{path}.observed: required when status is pass")
    return status


def validate_document_layout_observation(value: Any, path: str, check_name: str, errors: list[str]) -> None:
    if not is_object(value) or value.get("status") != "pass":
        return
    observed = value.get("observed")
    if check_name == "layout_structure":
        require_keys(observed, {"layout_model", "dynamic_content_safe"}, f"{path}.observed", errors)
        if is_object(observed):
            require_enum(
                observed.get("layout_model"), {"auto_layout", "absolute", "mixed"},
                f"{path}.observed.layout_model", errors,
            )
            if observed.get("dynamic_content_safe") is not True:
                errors.append(f"{path}.observed.dynamic_content_safe: pass requires true")
    elif check_name == "visual_integrity":
        require_keys(
            observed, {"overlap_count", "clipped_content_count", "screenshot_evidence"},
            f"{path}.observed", errors,
        )
        if is_object(observed):
            for field in ("overlap_count", "clipped_content_count"):
                require_nonnegative_int(observed.get(field), f"{path}.observed.{field}", errors)
                if observed.get(field) != 0:
                    errors.append(f"{path}.observed.{field}: pass requires zero")
            screenshots = observed.get("screenshot_evidence")
            require_string_list(screenshots, f"{path}.observed.screenshot_evidence", errors)
            if isinstance(screenshots, list) and not screenshots:
                errors.append(f"{path}.observed.screenshot_evidence: pass requires at least one screenshot")


def validate_document_component(
    value: Any, path: str, required_checks: set[str], errors: list[str],
) -> list[Any]:
    require_keys(value, {"status", "node_ids", "checks", "limitations"}, path, errors)
    if not is_object(value):
        return []
    status = value.get("status")
    require_enum(status, DOCUMENT_CHECK_STATUSES, f"{path}.status", errors)
    require_string_list(value.get("node_ids"), f"{path}.node_ids", errors)
    require_string_list(value.get("limitations"), f"{path}.limitations", errors)
    checks = value.get("checks")
    require_keys(checks, required_checks, f"{path}.checks", errors)
    statuses: list[Any] = []
    if is_object(checks):
        if set(checks) != required_checks:
            errors.append(f"{path}.checks: expected exactly {sorted(required_checks)}")
        for name in sorted(required_checks):
            check_path = f"{path}.checks.{name}"
            statuses.append(validate_document_check(checks.get(name), check_path, errors))
            validate_document_layout_observation(checks.get(name), check_path, name, errors)
    if status == "pass" and any(check_status != "pass" for check_status in statuses):
        errors.append(f"{path}.status: pass requires every check to pass")
    if status == "pass" and not value.get("node_ids"):
        errors.append(f"{path}.node_ids: pass requires at least one evidence node")
    return [status] + statuses


def validate_documentation_readiness(value: Any, errors: list[str]) -> None:
    path = "documentation_readiness"
    require_keys(value, {"status", "changelog", "reference", "limitations"}, path, errors)
    if not is_object(value):
        return
    overall = value.get("status")
    require_enum(overall, DOCUMENTATION_STATUSES, f"{path}.status", errors)
    require_string_list(value.get("limitations"), f"{path}.limitations", errors)
    statuses = []
    statuses.extend(validate_document_component(
        value.get("changelog"), f"{path}.changelog",
        {"format", "sort_order", "author_values", "type_values", "layout_structure", "visual_integrity"}, errors,
    ))
    statuses.extend(validate_document_component(
        value.get("reference"), f"{path}.reference",
        {"location", "required_evidence", "layout_structure", "visual_integrity"}, errors,
    ))
    component_statuses = [status for status in statuses if status is not None]
    limitations = value.get("limitations") if isinstance(value.get("limitations"), list) else []
    if overall == "ready" and (any(status != "pass" for status in component_statuses) or limitations):
        errors.append(f"{path}.status: ready requires all components and checks to pass without limitations")
    if overall == "ready_with_limitations" and all(status == "pass" for status in component_statuses) and not limitations:
        errors.append(f"{path}.status: ready_with_limitations requires a limitation or incomplete check")
    if overall == "not_ready" and not any(
        status in {"needs_review", "missing", "failed"} for status in component_statuses
    ):
        errors.append(f"{path}.status: not_ready requires a missing, failed, or needs-review component")


def validate_metric_status(value: Any, path: str, errors: list[str]) -> Any:
    if not is_object(value):
        errors.append(f"{path}: expected object")
        return None
    status = value.get("status")
    require_enum(status, COVERAGE_STATUSES, f"{path}.status", errors)
    if "limitations" in value:
        require_string_list(value.get("limitations"), f"{path}.limitations", errors)
    if status == "partial" and not value.get("limitations"):
        errors.append(f"{path}.limitations: partial status requires at least one limitation")
    return status


def validate_derived_metrics(value: Any, coverage: Any, errors: list[str]) -> None:
    path = "derived_metrics"
    required_metrics = {"local_inbound_aliases", "description_patterns", "scopes_by_collection"}
    require_keys(value, required_metrics, path, errors)
    if not is_object(value):
        return

    aliases = value.get("local_inbound_aliases")
    alias_status = validate_metric_status(aliases, f"{path}.local_inbound_aliases", errors)
    coverage_alias_status = coverage.get("aliases", {}).get("status") if is_object(coverage) else None
    if alias_status == "complete" and coverage_alias_status != "complete":
        errors.append(
            f"{path}.local_inbound_aliases.status: cannot be complete when coverage.aliases is not complete"
        )
    if is_object(aliases) and alias_status in {"complete", "partial"}:
        require_keys(
            aliases, {"status", "edges_total", "targets_with_inbound_aliases", "counts_by_target_id"},
            f"{path}.local_inbound_aliases", errors,
        )
        require_nonnegative_int(aliases.get("edges_total"), f"{path}.local_inbound_aliases.edges_total", errors)
        require_nonnegative_int(
            aliases.get("targets_with_inbound_aliases"),
            f"{path}.local_inbound_aliases.targets_with_inbound_aliases", errors,
        )
        counts = aliases.get("counts_by_target_id")
        if not is_object(counts):
            errors.append(f"{path}.local_inbound_aliases.counts_by_target_id: expected object")
        else:
            for target_id, count in counts.items():
                require_nonempty_string(target_id, f"{path}.local_inbound_aliases.counts_by_target_id key", errors)
                require_nonnegative_int(count, f"{path}.local_inbound_aliases.counts_by_target_id.{target_id}", errors)
                if count == 0:
                    errors.append(f"{path}.local_inbound_aliases.counts_by_target_id.{target_id}: omit zero counts")
            if aliases.get("edges_total") != sum(counts.values()):
                errors.append(f"{path}.local_inbound_aliases.edges_total: must equal the sum of target counts")
            if aliases.get("targets_with_inbound_aliases") != len(counts):
                errors.append(f"{path}.local_inbound_aliases.targets_with_inbound_aliases: must equal target count")

    descriptions = value.get("description_patterns")
    description_status = validate_metric_status(descriptions, f"{path}.description_patterns", errors)
    if is_object(descriptions) and description_status in {"complete", "partial"}:
        require_keys(
            descriptions, {"status", "evaluated_variables", "patterns", "unclassified"},
            f"{path}.description_patterns", errors,
        )
        require_nonnegative_int(
            descriptions.get("evaluated_variables"), f"{path}.description_patterns.evaluated_variables", errors,
        )
        require_nonnegative_int(descriptions.get("unclassified"), f"{path}.description_patterns.unclassified", errors)
        patterns = descriptions.get("patterns")
        pattern_total = 0
        pattern_ids: list[Any] = []
        if require_list(patterns, f"{path}.description_patterns.patterns", errors):
            for index, pattern in enumerate(patterns):
                pattern_path = f"{path}.description_patterns.patterns[{index}]"
                require_keys(
                    pattern, {"pattern_id", "label", "count", "confidence", "example_variable_ids"},
                    pattern_path, errors,
                )
                if is_object(pattern):
                    require_nonempty_string(pattern.get("pattern_id"), f"{pattern_path}.pattern_id", errors)
                    require_nonempty_string(pattern.get("label"), f"{pattern_path}.label", errors)
                    require_nonnegative_int(pattern.get("count"), f"{pattern_path}.count", errors)
                    if pattern.get("count") == 0:
                        errors.append(f"{pattern_path}.count: omit zero-count patterns")
                    require_enum(pattern.get("confidence"), CONFIDENCES, f"{pattern_path}.confidence", errors)
                    require_string_list(pattern.get("example_variable_ids"), f"{pattern_path}.example_variable_ids", errors)
                    pattern_total += pattern.get("count") if isinstance(pattern.get("count"), int) else 0
                    pattern_ids.append(pattern.get("pattern_id"))
        if len(pattern_ids) != len(set(pattern_ids)):
            errors.append(f"{path}.description_patterns.patterns: duplicate pattern IDs")
        if isinstance(descriptions.get("unclassified"), int):
            if descriptions.get("evaluated_variables") != pattern_total + descriptions["unclassified"]:
                errors.append(f"{path}.description_patterns: pattern counts plus unclassified must equal evaluated_variables")

    scopes = value.get("scopes_by_collection")
    scope_status = validate_metric_status(scopes, f"{path}.scopes_by_collection", errors)
    if is_object(scopes) and scope_status in {"complete", "partial"}:
        require_keys(scopes, {"status", "collections"}, f"{path}.scopes_by_collection", errors)
        collections = scopes.get("collections")
        if not is_object(collections):
            errors.append(f"{path}.scopes_by_collection.collections: expected object")
        else:
            for collection_id, collection in collections.items():
                collection_path = f"{path}.scopes_by_collection.collections.{collection_id}"
                require_nonempty_string(collection_id, f"{path}.scopes_by_collection.collections key", errors)
                require_keys(
                    collection, {"name", "variables_total", "scope_counts", "unobservable"},
                    collection_path, errors,
                )
                if not is_object(collection):
                    continue
                require_nonempty_string(collection.get("name"), f"{collection_path}.name", errors)
                require_nonnegative_int(collection.get("variables_total"), f"{collection_path}.variables_total", errors)
                require_nonnegative_int(collection.get("unobservable"), f"{collection_path}.unobservable", errors)
                if isinstance(collection.get("variables_total"), int) and isinstance(collection.get("unobservable"), int):
                    if collection["unobservable"] > collection["variables_total"]:
                        errors.append(f"{collection_path}.unobservable: cannot exceed variables_total")
                scope_counts = collection.get("scope_counts")
                if not is_object(scope_counts):
                    errors.append(f"{collection_path}.scope_counts: expected object")
                else:
                    for scope, count in scope_counts.items():
                        require_nonempty_string(scope, f"{collection_path}.scope_counts key", errors)
                        require_nonnegative_int(count, f"{collection_path}.scope_counts.{scope}", errors)


def validate_property_coverage(value: Any, errors: list[str]) -> None:
    path = "property_coverage"
    required = {"contract_version", "status", "source", "families", "excluded_non_bindable_properties", "limitations"}
    require_keys(value, required, path, errors)
    if not is_object(value):
        return
    if value.get("contract_version") != "1.0.0":
        errors.append(f"{path}.contract_version: expected '1.0.0'")
    require_enum(value.get("status"), {"complete", "partial", "not_observable", "failed"}, f"{path}.status", errors)

    source = value.get("source")
    require_keys(source, {"adapter_id", "capability_basis", "canonical_profile", "capability_evidence"}, f"{path}.source", errors)
    basis = None
    if is_object(source):
        require_nonempty_string(source.get("adapter_id"), f"{path}.source.adapter_id", errors)
        basis = source.get("capability_basis")
        require_enum(basis, PROPERTY_CAPABILITY_BASES, f"{path}.source.capability_basis", errors)
        require_nonempty_string(source.get("capability_evidence"), f"{path}.source.capability_evidence", errors)
        profile = source.get("canonical_profile")
        if basis == "official_figma_plugin_api":
            if profile != "figma_plugin_api_2026_09":
                errors.append(f"{path}.source.canonical_profile: official profile must be 'figma_plugin_api_2026_09'")
        elif profile is not None:
            require_nonempty_string(profile, f"{path}.source.canonical_profile", errors)

    exclusions = value.get("excluded_non_bindable_properties")
    if require_string_list(exclusions, f"{path}.excluded_non_bindable_properties", errors):
        if len(exclusions) != len(set(exclusions)):
            errors.append(f"{path}.excluded_non_bindable_properties: entries must be unique")
        missing = NON_BINDABLE_PROPERTIES - set(exclusions)
        if missing:
            errors.append(f"{path}.excluded_non_bindable_properties: missing {sorted(missing)}")
    require_string_list(value.get("limitations"), f"{path}.limitations", errors)

    families = value.get("families")
    if not is_object(families):
        errors.append(f"{path}.families: expected object")
        return
    missing_families = PROPERTY_FAMILIES.keys() - families.keys()
    extra_families = families.keys() - PROPERTY_FAMILIES.keys()
    if missing_families:
        errors.append(f"{path}.families: missing {sorted(missing_families)}")
    if extra_families:
        errors.append(f"{path}.families: unsupported {sorted(extra_families)}")

    observed_family_statuses: list[str] = []
    for family_name in sorted(PROPERTY_FAMILIES.keys() & families.keys()):
        family = families[family_name]
        family_path = f"{path}.families.{family_name}"
        require_keys(family, {"support_status", "status", "declared_paths", "properties", "limitations"}, family_path, errors)
        if not is_object(family):
            continue
        support_status = family.get("support_status")
        family_status = family.get("status")
        require_enum(support_status, PROPERTY_SUPPORT_STATUSES, f"{family_path}.support_status", errors)
        require_enum(family_status, PROPERTY_FAMILY_STATUSES, f"{family_path}.status", errors)
        observed_family_statuses.append(family_status)
        declared_paths = family.get("declared_paths")
        if not require_string_list(declared_paths, f"{family_path}.declared_paths", errors):
            declared_paths = []
        elif len(declared_paths) != len(set(declared_paths)):
            errors.append(f"{family_path}.declared_paths: entries must be unique")
        declared_set = set(declared_paths)
        invalid_paths = declared_set - PROPERTY_FAMILIES[family_name]
        if invalid_paths:
            errors.append(f"{family_path}.declared_paths: unsupported paths {sorted(invalid_paths)}")
        limitations = family.get("limitations")
        if not require_string_list(limitations, f"{family_path}.limitations", errors):
            limitations = []
        properties = family.get("properties")
        if not require_list(properties, f"{family_path}.properties", errors):
            properties = []

        if support_status == "supported":
            if not declared_paths:
                errors.append(f"{family_path}.declared_paths: supported family requires at least one path")
            if family_status not in {"complete", "partial", "not_applicable", "failed"}:
                errors.append(f"{family_path}.status: supported family has incompatible status")
            if basis == "official_figma_plugin_api" and declared_set != PROPERTY_FAMILIES[family_name]:
                errors.append(f"{family_path}.declared_paths: official profile requires the complete canonical set")
        elif support_status == "unsupported":
            if family_status != "unsupported" or declared_paths or properties or not limitations:
                errors.append(f"{family_path}: unsupported family requires unsupported status, empty data, and a limitation")
        elif support_status == "not_observable":
            if family_status != "not_observable" or declared_paths or properties or not limitations:
                errors.append(f"{family_path}: not_observable family requires matching status, empty data, and a limitation")

        property_paths: list[Any] = []
        property_statuses: list[str] = []
        for index, record in enumerate(properties):
            record_path = f"{family_path}.properties[{index}]"
            required_record = {
                "property_path", "status", "eligible_nodes", "inspected_nodes", "bound_count",
                "literal_count", "mixed_or_unsupported_count", "limitations",
            }
            require_keys(record, required_record, record_path, errors)
            if not is_object(record):
                continue
            property_path = record.get("property_path")
            property_paths.append(property_path)
            require_nonempty_string(property_path, f"{record_path}.property_path", errors)
            if property_path not in declared_set:
                errors.append(f"{record_path}.property_path: must be declared by the family")
            record_status = record.get("status")
            property_statuses.append(record_status)
            require_enum(record_status, PROPERTY_RECORD_STATUSES, f"{record_path}.status", errors)
            for field in ("eligible_nodes", "inspected_nodes", "bound_count", "literal_count", "mixed_or_unsupported_count"):
                require_nonnegative_int(record.get(field), f"{record_path}.{field}", errors)
            record_limitations = record.get("limitations")
            if not require_string_list(record_limitations, f"{record_path}.limitations", errors):
                record_limitations = []
            counts = [record.get(field) for field in ("eligible_nodes", "inspected_nodes", "bound_count", "literal_count", "mixed_or_unsupported_count")]
            if all(isinstance(item, int) and not isinstance(item, bool) and item >= 0 for item in counts):
                eligible, inspected, bound, literal, mixed = counts
                if inspected != bound + literal + mixed:
                    errors.append(f"{record_path}.inspected_nodes: must equal bound + literal + mixed_or_unsupported")
                if inspected > eligible:
                    errors.append(f"{record_path}.inspected_nodes: cannot exceed eligible_nodes")
                if record_status == "complete" and inspected != eligible:
                    errors.append(f"{record_path}.status: complete requires every eligible node inspected")
                if record_status == "partial" and (inspected >= eligible or not record_limitations):
                    errors.append(f"{record_path}.status: partial requires an uninspected eligible node and a limitation")
                if record_status == "not_applicable" and (eligible != 0 or inspected != 0):
                    errors.append(f"{record_path}.status: not_applicable requires zero eligible and inspected nodes")
                if record_status == "failed" and not record_limitations:
                    errors.append(f"{record_path}.status: failed requires a limitation")

        if len(property_paths) != len(set(property_paths)):
            errors.append(f"{family_path}.properties: property paths must be unique")
        if support_status == "supported" and set(property_paths) != declared_set:
            errors.append(f"{family_path}.properties: must contain exactly one record per declared path")
        if support_status == "supported" and property_statuses:
            expected_family_status = (
                "failed" if "failed" in property_statuses
                else "partial" if "partial" in property_statuses
                else "not_applicable" if all(item == "not_applicable" for item in property_statuses)
                else "complete"
            )
            if family_status != expected_family_status:
                errors.append(f"{family_path}.status: expected {expected_family_status!r} from property records")

    if len(observed_family_statuses) == len(PROPERTY_FAMILIES):
        expected_status = (
            "failed" if "failed" in observed_family_statuses
            else "not_observable" if all(item == "not_observable" for item in observed_family_statuses)
            else "partial" if any(item in {"partial", "not_observable", "unsupported"} for item in observed_family_statuses)
            else "complete"
        )
        if value.get("status") != expected_status:
            errors.append(f"{path}.status: expected {expected_status!r} from family statuses")


def validate_numeric_semantics(
    value: Any, path: str, status: Any, property_path: Any, errors: list[str],
) -> None:
    required = {
        "family", "current_effective_value", "target_variable_value",
        "target_resolved_consumer_value", "expected_effective_value", "tolerance",
        "equivalence", "resolution_method",
    }
    require_keys(value, required, path, errors)
    if not is_object(value):
        return

    family = value.get("family")
    equivalence = value.get("equivalence")
    resolution_method = value.get("resolution_method")
    require_enum(family, NUMERIC_FAMILIES, f"{path}.family", errors)
    require_enum(equivalence, NUMERIC_EQUIVALENCE, f"{path}.equivalence", errors)
    require_enum(resolution_method, NUMERIC_RESOLUTION_METHODS, f"{path}.resolution_method", errors)

    numeric_fields = (
        "current_effective_value", "target_variable_value",
        "target_resolved_consumer_value", "expected_effective_value", "tolerance",
    )
    valid_numbers = {
        field: require_finite_number(value.get(field), f"{path}.{field}", errors)
        for field in numeric_fields
    }
    tolerance = value.get("tolerance")
    if valid_numbers["tolerance"] and tolerance < 0:
        errors.append(f"{path}.tolerance: must be non-negative")

    if all(valid_numbers[field] for field in ("target_resolved_consumer_value", "expected_effective_value", "tolerance")):
        computed = (
            "equivalent"
            if abs(value["target_resolved_consumer_value"] - value["expected_effective_value"]) <= tolerance
            else "mismatch"
        )
        if equivalence != computed:
            errors.append(f"{path}.equivalence: expected {computed!r} from resolved and expected values")

    if family == "opacity":
        if not (isinstance(property_path, str) and (property_path == "opacity" or property_path.endswith(".opacity"))):
            errors.append(f"{path}.family: opacity requires an opacity property path")
        for field in ("current_effective_value", "target_resolved_consumer_value", "expected_effective_value"):
            number = value.get(field)
            if valid_numbers[field] and not 0 <= number <= 1:
                errors.append(f"{path}.{field}: opacity consumer value must be between 0 and 1")

    if status == "proposed":
        if resolution_method == "not_observable" or equivalence == "not_observable":
            errors.append(f"{path}: proposed FLOAT binding requires observable consumer resolution")
        if equivalence != "equivalent":
            errors.append(f"{path}: proposed FLOAT binding requires equivalent resolved and expected values")


def validate_binding_finding(finding: Any, index: int, audit_id: Any, errors: list[str]) -> None:
    path = f"binding_findings[{index}]"
    require_keys(finding, REQUIRED_BINDING_FINDING, path, errors)
    if not is_object(finding):
        return

    for key in (
        "finding_id", "fingerprint", "source_audit_id", "page_id", "node_id", "node_name",
        "node_type", "property_path", "risk",
    ):
        require_nonempty_string(finding.get(key), f"{path}.{key}", errors)
    if finding.get("source_audit_id") != audit_id:
        errors.append(f"{path}.source_audit_id: must equal audit_id")
    if not isinstance(finding.get("finding_id"), str) or not re.fullmatch(r"DTA-BINDING-\d{3}", finding["finding_id"]):
        errors.append(f"{path}.finding_id: expected DTA-BINDING-{{NNN}}")

    property_path = finding.get("property_path")
    if not isinstance(property_path, str) or not PROPERTY_PATH_RE.fullmatch(property_path):
        errors.append(f"{path}.property_path: invalid explicit property path")
    property_type = finding.get("property_value_type")
    require_enum(property_type, BINDING_VALUE_TYPES, f"{path}.property_value_type", errors)
    operation = finding.get("operation")
    status = finding.get("status")
    require_enum(operation, BINDING_OPERATIONS, f"{path}.operation", errors)
    require_enum(status, BINDING_STATUSES, f"{path}.status", errors)
    require_enum(finding.get("confidence"), CONFIDENCES, f"{path}.confidence", errors)
    require_string_list(finding.get("limitations"), f"{path}.limitations", errors)

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

    current = finding.get("current")
    expected = finding.get("expected")
    require_keys(current, {"kind"}, f"{path}.current", errors)
    require_keys(expected, {"kind"}, f"{path}.expected", errors)
    current_kind = current.get("kind") if is_object(current) else None
    expected_kind = expected.get("kind") if is_object(expected) else None
    require_enum(current_kind, BINDING_CURRENT_KINDS, f"{path}.current.kind", errors)
    require_enum(expected_kind, BINDING_EXPECTED_KINDS, f"{path}.expected.kind", errors)

    if is_object(current):
        if current_kind == "literal" and "value" not in current:
            errors.append(f"{path}.current.value: required for literal representation")
        if current_kind == "variable":
            require_keys(current, {"kind", "variable_id", "variable_name", "variable_type"}, f"{path}.current", errors)
            require_nonempty_string(current.get("variable_id"), f"{path}.current.variable_id", errors)
            require_nonempty_string(current.get("variable_name"), f"{path}.current.variable_name", errors)
            require_enum(current.get("variable_type"), BINDING_VALUE_TYPES, f"{path}.current.variable_type", errors)
            if current.get("variable_type") != property_type:
                errors.append(f"{path}.current.variable_type: must equal property_value_type")

    target_id = None
    if is_object(expected) and expected_kind == "variable":
        require_keys(
            expected,
            {
                "kind", "variable_id", "variable_name", "variable_type", "collection_id",
                "relevant_mode_ids", "missing_mode_ids", "scopes", "scope_compatibility",
            },
            f"{path}.expected", errors,
        )
        require_nonempty_string(expected.get("variable_id"), f"{path}.expected.variable_id", errors)
        require_nonempty_string(expected.get("variable_name"), f"{path}.expected.variable_name", errors)
        require_nonempty_string(expected.get("collection_id"), f"{path}.expected.collection_id", errors)
        require_enum(expected.get("variable_type"), BINDING_VALUE_TYPES, f"{path}.expected.variable_type", errors)
        relevant_modes = expected.get("relevant_mode_ids")
        require_string_list(relevant_modes, f"{path}.expected.relevant_mode_ids", errors)
        require_string_list(expected.get("missing_mode_ids"), f"{path}.expected.missing_mode_ids", errors)
        require_string_list(expected.get("scopes"), f"{path}.expected.scopes", errors)
        require_enum(
            expected.get("scope_compatibility"), BINDING_SCOPE_STATUSES,
            f"{path}.expected.scope_compatibility", errors,
        )
        if expected.get("variable_type") != property_type:
            errors.append(f"{path}.expected.variable_type: must equal property_value_type")
        if status == "proposed":
            if isinstance(relevant_modes, list) and not relevant_modes:
                errors.append(f"{path}.expected.relevant_mode_ids: proposed write requires at least one relevant mode")
            if expected.get("missing_mode_ids"):
                errors.append(f"{path}.expected.missing_mode_ids: proposed write requires complete relevant mode coverage")
            if expected.get("scope_compatibility") != "compatible":
                errors.append(f"{path}.expected.scope_compatibility: proposed write requires compatible scope")
        target_id = expected.get("variable_id")

    if property_type == "FLOAT" and expected_kind == "variable":
        if "numeric_semantics" not in finding:
            errors.append(f"{path}.numeric_semantics: missing required field for FLOAT variable target")
        else:
            validate_numeric_semantics(
                finding.get("numeric_semantics"), f"{path}.numeric_semantics", status,
                property_path, errors,
            )

    if operation == "bind" and not (current_kind in {"literal", "unbound"} and expected_kind == "variable"):
        errors.append(f"{path}.operation: bind requires literal/unbound current and variable expected")
    if operation == "rebind":
        if not (current_kind == "variable" and expected_kind == "variable"):
            errors.append(f"{path}.operation: rebind requires variable current and variable expected")
        elif is_object(current) and current.get("variable_id") == target_id:
            errors.append(f"{path}.operation: rebind target must differ from current variable")
    if operation == "unbind" and not (current_kind == "variable" and expected_kind == "unbound"):
        errors.append(f"{path}.operation: unbind requires variable current and unbound expected")
    if operation == "no_op":
        if not (current_kind == "variable" and expected_kind == "variable"):
            errors.append(f"{path}.operation: no_op requires variable current and variable expected")
        elif is_object(current) and current.get("variable_id") != target_id:
            errors.append(f"{path}.operation: no_op requires matching variable IDs")
        if status == "proposed":
            errors.append(f"{path}.status: no_op cannot be a proposed write")

    expected_fingerprint = f"binding|{finding.get('node_id')}|{property_path}|{target_id or 'null'}"
    if finding.get("fingerprint") != expected_fingerprint:
        errors.append(f"{path}.fingerprint: expected {expected_fingerprint!r}")


def validate_binding_summary(summary: Any, findings: list[Any], errors: list[str]) -> None:
    path = "binding_summary"
    require_keys(summary, {"findings_total", "by_operation", "by_status", "write_candidates"}, path, errors)
    if not is_object(summary):
        return
    valid = [finding for finding in findings if is_object(finding)]
    if summary.get("findings_total") != len(findings):
        errors.append(f"{path}.findings_total: must equal binding_findings length")
    for field, allowed in (("by_operation", BINDING_OPERATIONS), ("by_status", BINDING_STATUSES)):
        value = summary.get(field)
        if not is_object(value):
            errors.append(f"{path}.{field}: expected object")
            continue
        if set(value) != allowed:
            errors.append(f"{path}.{field}: must contain exactly {sorted(allowed)}")
        expected_counts = Counter(finding.get(field.removeprefix("by_")) for finding in valid)
        for key in allowed:
            require_nonnegative_int(value.get(key), f"{path}.{field}.{key}", errors)
            if value.get(key, 0) != expected_counts.get(key, 0):
                errors.append(f"{path}.{field}.{key}: count does not match binding_findings")
    expected_candidates = sum(
        finding.get("status") == "proposed" and finding.get("operation") in {"bind", "rebind", "unbind"}
        for finding in valid
    )
    if summary.get("write_candidates") != expected_candidates:
        errors.append(f"{path}.write_candidates: count does not match proposed write operations")


def coverage_pattern_for_explicit_path(path: Any) -> Any:
    if not isinstance(path, str):
        return path
    normalized = re.sub(r"\[\d+\]", "[*]", path)
    if normalized.startswith("componentProperties."):
        return "componentProperties[*]"
    return normalized


def validate_binding_property_coverage(findings: list[Any], coverage: Any, errors: list[str]) -> None:
    records: dict[str, Any] = {}
    if is_object(coverage) and is_object(coverage.get("families")):
        for family in coverage["families"].values():
            if not is_object(family):
                continue
            for record in family.get("properties", []):
                if is_object(record) and isinstance(record.get("property_path"), str):
                    records[record["property_path"]] = record
    for index, finding in enumerate(findings):
        if not is_object(finding):
            continue
        pattern = coverage_pattern_for_explicit_path(finding.get("property_path"))
        record = records.get(pattern)
        if record is None:
            errors.append(f"binding_findings[{index}].property_path: missing matching property_coverage record for {pattern!r}")
        elif not isinstance(record.get("inspected_nodes"), int) or record.get("inspected_nodes", 0) < 1:
            errors.append(f"binding_findings[{index}].property_path: property_coverage must include an inspected node")


def validate(data: Any) -> list[str]:
    errors: list[str] = []
    require_keys(data, REQUIRED_TOP, "$", errors)
    if not is_object(data):
        return errors

    if data.get("schema_version") != "1.5.0":
        errors.append("schema_version: expected '1.5.0'")
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

    source = data.get("source")
    require_keys(source, REQUIRED_SOURCE, "source", errors)
    if is_object(source):
        require_nonempty_string(source.get("file_key"), "source.file_key", errors)
        require_nonempty_string(source.get("file_name"), "source.file_name", errors)
        pages_requested = source.get("pages_requested")
        if require_list(pages_requested, "source.pages_requested", errors):
            for index, page in enumerate(pages_requested):
                path = f"source.pages_requested[{index}]"
                require_keys(page, {"id", "name"}, path, errors)
                if is_object(page):
                    require_nonempty_string(page.get("id"), f"{path}.id", errors)
                    require_nonempty_string(page.get("name"), f"{path}.name", errors)
    inspection = data.get("inspection")
    require_keys(inspection, REQUIRED_INSPECTION, "inspection", errors)
    if is_object(inspection):
        require_enum(inspection.get("method"), METHODS, "inspection.method", errors)
        require_nonempty_string(inspection.get("tool_name"), "inspection.tool_name", errors)
        require_string_list(inspection.get("capabilities"), "inspection.capabilities", errors)
        require_string_list(inspection.get("unavailable_operations"), "inspection.unavailable_operations", errors)

    validate_coverage(data.get("coverage"), data.get("status"), errors)
    validate_inventory(data.get("inventory"), errors)
    validate_documentation_readiness(data.get("documentation_readiness"), errors)
    validate_derived_metrics(data.get("derived_metrics"), data.get("coverage"), errors)
    validate_property_coverage(data.get("property_coverage"), errors)

    binding_findings = data.get("binding_findings")
    if not require_list(binding_findings, "binding_findings", errors):
        binding_findings = []
    for index, finding in enumerate(binding_findings):
        validate_binding_finding(finding, index, data.get("audit_id"), errors)
    validate_binding_property_coverage(binding_findings, data.get("property_coverage"), errors)
    binding_ids = [finding.get("finding_id") for finding in binding_findings if is_object(finding)]
    binding_fingerprints = [finding.get("fingerprint") for finding in binding_findings if is_object(finding)]
    if len(binding_ids) != len(set(binding_ids)):
        errors.append("binding_findings: duplicate finding IDs")
    if len(binding_fingerprints) != len(set(binding_fingerprints)):
        errors.append("binding_findings: duplicate fingerprints")
    binding_tuples = []
    for finding in binding_findings:
        if not is_object(finding):
            continue
        expected = finding.get("expected")
        target_id = expected.get("variable_id") if is_object(expected) and expected.get("kind") == "variable" else None
        binding_tuples.append((finding.get("node_id"), finding.get("property_path"), finding.get("operation"), target_id))
    if len(binding_tuples) != len(set(binding_tuples)):
        errors.append("binding_findings: duplicate change tuples")
    ordered_bindings = sorted(
        (finding for finding in binding_findings if is_object(finding)),
        key=lambda finding: (str(finding.get("node_id")), str(finding.get("property_path")), str(finding.get("operation"))),
    )
    for index, finding in enumerate(ordered_bindings, start=1):
        expected_id = f"DTA-BINDING-{index:03d}"
        if finding.get("finding_id") != expected_id:
            errors.append(f"binding_findings: deterministic ID expected {expected_id!r}")
    validate_binding_summary(data.get("binding_summary"), binding_findings, errors)

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

    ordered = sorted(
        (finding for finding in findings if is_object(finding)),
        key=lambda finding: (
            str(finding.get("category")), str(finding.get("rule_id")),
            ",".join(sorted(str(target.get("id")) for target in finding.get("targets", []) if is_object(target))),
            ",".join(sorted(str(target.get("mode_id")) for target in finding.get("targets", []) if is_object(target) and target.get("mode_id") is not None)),
        ),
    )
    counters: Counter[str] = Counter()
    for finding in ordered:
        category = finding.get("category")
        if isinstance(category, str) and category in CATEGORIES:
            counters[category] += 1
            expected_id = f"DTA-{category.upper()}-{counters[category]:03d}"
            if finding.get("id") != expected_id:
                errors.append(f"findings: deterministic ID expected {expected_id!r}")

    validate_summary(data.get("summary"), findings, errors)
    next_pass = data.get("recommended_next_pass")
    if next_pass is not None:
        require_nonempty_string(next_pass, "recommended_next_pass", errors)
    return errors


def self_test() -> int:
    sample = {
        "schema_version": "1.5.0",
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
            "collections": {"status": "complete", "observed": 1, "expected": 1},
            "variables": {"status": "complete", "captured": 1, "failed": 0},
            "pages": {"status": "not_configured", "fully_traversed_ids": [], "not_traversed_ids": []},
            "aliases": {"status": "complete", "unresolved_remote": 0},
            "external_consumers": {"status": "not_observable", "searched": [], "not_searched": ["consumer files"]},
            "unobservable_fields": [], "limitations": ["External consumers not searched"],
        },
        "inventory": {
            "collections_total": 1, "variables_total": 1, "variables_by_collection": {"Global": 1},
            "variables_by_type": {"COLOR": 1}, "descriptions": {"complete": 1, "empty": 0},
            "modes_by_collection": {"Global": [{"id": "mode-1", "name": "Default"}]},
            "missing_mode_values": 0, "all_scopes": 0, "unresolved_aliases": 0,
            "potential_orphan_candidates": 0,
        },
        "documentation_readiness": {
            "status": "not_observable",
            "changelog": {
                "status": "not_observable", "node_ids": [],
                "checks": {
                    "format": {"status": "not_observable", "observed": None, "evidence": []},
                    "sort_order": {"status": "not_observable", "observed": None, "evidence": []},
                    "author_values": {"status": "not_observable", "observed": None, "evidence": []},
                    "type_values": {"status": "not_observable", "observed": None, "evidence": []},
                    "layout_structure": {"status": "not_observable", "observed": None, "evidence": []},
                    "visual_integrity": {"status": "not_observable", "observed": None, "evidence": []},
                },
                "limitations": ["Document nodes not observable"],
            },
            "reference": {
                "status": "not_observable", "node_ids": [],
                "checks": {
                    "location": {"status": "not_observable", "observed": None, "evidence": []},
                    "required_evidence": {"status": "not_observable", "observed": None, "evidence": []},
                    "layout_structure": {"status": "not_observable", "observed": None, "evidence": []},
                    "visual_integrity": {"status": "not_observable", "observed": None, "evidence": []},
                },
                "limitations": ["Document nodes not observable"],
            },
            "limitations": ["Documentation readiness not observable"],
        },
        "derived_metrics": {
            "local_inbound_aliases": {
                "status": "complete", "edges_total": 0,
                "targets_with_inbound_aliases": 0, "counts_by_target_id": {},
            },
            "description_patterns": {
                "status": "complete", "evaluated_variables": 1,
                "patterns": [{
                    "pattern_id": "usage-oriented", "label": "Usage-oriented",
                    "count": 1, "confidence": "high", "example_variable_ids": ["variable-1"],
                }],
                "unclassified": 0,
            },
            "scopes_by_collection": {
                "status": "complete",
                "collections": {
                    "collection-1": {
                        "name": "Global", "variables_total": 1,
                        "scope_counts": {"ALL_SCOPES": 1}, "unobservable": 0,
                    }
                },
            },
        },
        "property_coverage": {
            "contract_version": "1.0.0", "status": "not_observable",
            "source": {
                "adapter_id": "figma-plugin-api", "capability_basis": "adapter_declared",
                "canonical_profile": None, "capability_evidence": "Document traversal is unavailable in this self-test",
            },
            "families": {
                name: {
                    "support_status": "not_observable", "status": "not_observable",
                    "declared_paths": [], "properties": [], "limitations": ["Document nodes not observable"],
                }
                for name in PROPERTY_FAMILIES
            },
            "excluded_non_bindable_properties": sorted(NON_BINDABLE_PROPERTIES),
            "limitations": ["Document nodes not observable"],
        },
        "binding_findings": [],
        "binding_summary": {
            "findings_total": 0,
            "by_operation": {"bind": 0, "rebind": 0, "unbind": 0, "no_op": 0},
            "by_status": {"proposed": 0, "held": 0, "not_actionable": 0, "verified": 0},
            "write_candidates": 0,
        },
        "findings": [],
        "summary": {
            "findings_total": 0,
            "by_severity": {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0},
            "by_category": {}, "holds": 0,
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
