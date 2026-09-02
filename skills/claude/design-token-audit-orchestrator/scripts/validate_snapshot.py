#!/usr/bin/env python3
"""Validate canonical Figma token snapshots and compare semantic equivalence."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


COVERAGE_STATUSES = {"complete", "partial", "not_observable", "not_configured", "failed"}
SOURCE_TYPES = {"plugin_api", "mcp", "api", "export", "mixed"}
CAPABILITY_STATUSES = {"available", "partial", "unavailable", "unknown", "failed"}
VALUE_KINDS = {"literal", "alias", "missing", "not_observable"}
PAGE_STATUSES = {"complete", "partial", "not_observable", "failed"}
EVIDENCE_TYPES = {"changelog", "reference", "other"}
VARIABLE_TYPES = {"BOOLEAN", "COLOR", "FLOAT", "STRING"}
CORE_CAPABILITIES = {"identify_file", "read_local_collections", "read_local_variables"}
TOP_FIELDS = {
    "schema_version", "snapshot_type", "snapshot_id", "captured_at", "source", "adapter",
    "coverage", "collections", "variables", "pages", "usages", "document_evidence", "warnings",
}


def obj(value: Any) -> bool:
    return isinstance(value, dict)


def required(value: Any, keys: set[str], path: str, errors: list[str]) -> None:
    if not obj(value):
        errors.append(f"{path}: expected object")
        return
    for key in sorted(keys - value.keys()):
        errors.append(f"{path}.{key}: missing required field")


def nonempty(value: Any, path: str, errors: list[str]) -> None:
    if not isinstance(value, str) or not value.strip():
        errors.append(f"{path}: expected non-empty string")


def nonnegative_int(value: Any, path: str, errors: list[str]) -> None:
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        errors.append(f"{path}: expected non-negative integer")


def string_array(value: Any, path: str, errors: list[str]) -> bool:
    if not array(value, path, errors):
        return False
    for index, item in enumerate(value):
        nonempty(item, f"{path}[{index}]", errors)
    return True


def utc_timestamp(value: Any, path: str, errors: list[str]) -> None:
    if not isinstance(value, str):
        errors.append(f"{path}: expected UTC ISO-8601 string")
        return
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        errors.append(f"{path}: invalid ISO-8601 timestamp")
        return
    if parsed.tzinfo is None or parsed.utcoffset() != timezone.utc.utcoffset(parsed):
        errors.append(f"{path}: expected UTC ISO-8601 timestamp")


def array(value: Any, path: str, errors: list[str]) -> bool:
    if not isinstance(value, list):
        errors.append(f"{path}: expected array")
        return False
    return True


def enum(value: Any, allowed: set[str], path: str, errors: list[str]) -> None:
    if value not in allowed:
        errors.append(f"{path}: expected one of {sorted(allowed)}, got {value!r}")


def provenance(value: Any, path: str, adapter_id: Any, source_type: Any, errors: list[str]) -> None:
    required(value, {"adapter_id", "source_path"}, path, errors)
    if not obj(value):
        return
    nonempty(value.get("adapter_id"), f"{path}.adapter_id", errors)
    nonempty(value.get("source_path"), f"{path}.source_path", errors)
    if source_type != "mixed" and value.get("adapter_id") != adapter_id:
        errors.append(f"{path}.adapter_id: must match adapter.adapter_id")
    if source_type == "mixed":
        utc_timestamp(value.get("captured_at"), f"{path}.captured_at", errors)
        field_sources = value.get("field_sources")
        if field_sources is not None:
            if not obj(field_sources) or not field_sources:
                errors.append(f"{path}.field_sources: expected non-empty object when present")
            else:
                for field, source in field_sources.items():
                    nonempty(field, f"{path}.field_sources key", errors)
                    nonempty(source, f"{path}.field_sources.{field}", errors)


def validate_literal(value: Any, resolved_type: Any, path: str, errors: list[str]) -> None:
    if resolved_type == "BOOLEAN":
        if not isinstance(value, bool):
            errors.append(f"{path}: expected Boolean literal")
    elif resolved_type == "FLOAT":
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            errors.append(f"{path}: expected numeric literal")
    elif resolved_type == "STRING":
        if not isinstance(value, str):
            errors.append(f"{path}: expected string literal")
    elif resolved_type == "COLOR":
        if not obj(value) or set(value) != {"r", "g", "b", "a"}:
            errors.append(f"{path}: expected RGBA object")
        else:
            for channel in ("r", "g", "b", "a"):
                component = value.get(channel)
                if not isinstance(component, (int, float)) or isinstance(component, bool) or not 0 <= component <= 1:
                    errors.append(f"{path}.{channel}: expected number from 0 to 1")


def validate(data: Any) -> list[str]:
    errors: list[str] = []
    required(data, TOP_FIELDS, "$", errors)
    if not obj(data):
        return errors
    if data.get("schema_version") != "1.0.0":
        errors.append("schema_version: expected '1.0.0'")
    if data.get("snapshot_type") != "figma_token_snapshot":
        errors.append("snapshot_type: expected 'figma_token_snapshot'")
    nonempty(data.get("snapshot_id"), "snapshot_id", errors)
    utc_timestamp(data.get("captured_at"), "captured_at", errors)

    source = data.get("source")
    required(source, {"file_key", "file_name"}, "source", errors)
    if obj(source):
        nonempty(source.get("file_key"), "source.file_key", errors)
        nonempty(source.get("file_name"), "source.file_name", errors)

    adapter = data.get("adapter")
    required(adapter, {"adapter_id", "adapter_version", "source_type", "capabilities"}, "adapter", errors)
    adapter_id = adapter.get("adapter_id") if obj(adapter) else None
    source_type = adapter.get("source_type") if obj(adapter) else None
    if obj(adapter):
        nonempty(adapter_id, "adapter.adapter_id", errors)
        nonempty(adapter.get("adapter_version"), "adapter.adapter_version", errors)
        enum(adapter.get("source_type"), SOURCE_TYPES, "adapter.source_type", errors)
        capabilities = adapter.get("capabilities")
        if not obj(capabilities):
            errors.append("adapter.capabilities: expected object")
        else:
            for name, capability in capabilities.items():
                path = f"adapter.capabilities.{name}"
                required(capability, {"status", "evidence"}, path, errors)
                if obj(capability):
                    enum(capability.get("status"), CAPABILITY_STATUSES, f"{path}.status", errors)
                    nonempty(capability.get("evidence"), f"{path}.evidence", errors)
            for name in CORE_CAPABILITIES:
                status = capabilities.get(name, {}).get("status") if obj(capabilities.get(name)) else None
                if status != "available":
                    errors.append(f"adapter.capabilities.{name}.status: core capability must be available")

    coverage = data.get("coverage")
    coverage_fields = {"collections", "variables", "pages", "usages", "document_evidence"}
    required(coverage, coverage_fields, "coverage", errors)
    if obj(coverage):
        for name in coverage_fields:
            section = coverage.get(name)
            required(section, {"status"}, f"coverage.{name}", errors)
            if obj(section):
                enum(section.get("status"), COVERAGE_STATUSES, f"coverage.{name}.status", errors)
        for name in ("collections", "variables"):
            section = coverage.get(name)
            if obj(section):
                nonnegative_int(section.get("captured"), f"coverage.{name}.captured", errors)
                nonnegative_int(section.get("failed"), f"coverage.{name}.failed", errors)
                if section.get("status") == "complete" and section.get("failed") != 0:
                    errors.append(f"coverage.{name}.failed: must be zero when complete")
        pages_coverage = coverage.get("pages")
        if obj(pages_coverage):
            string_array(pages_coverage.get("captured_ids"), "coverage.pages.captured_ids", errors)
            string_array(pages_coverage.get("omitted_ids"), "coverage.pages.omitted_ids", errors)
            captured_ids = pages_coverage.get("captured_ids") if isinstance(pages_coverage.get("captured_ids"), list) else []
            omitted_ids = pages_coverage.get("omitted_ids") if isinstance(pages_coverage.get("omitted_ids"), list) else []
            if set(captured_ids) & set(omitted_ids):
                errors.append("coverage.pages: captured and omitted IDs must be disjoint")
            if pages_coverage.get("status") == "complete" and omitted_ids:
                errors.append("coverage.pages.omitted_ids: must be empty when complete")

    collections = data.get("collections")
    variables = data.get("variables")
    pages = data.get("pages")
    usages = data.get("usages")
    evidence = data.get("document_evidence")
    warnings = data.get("warnings")
    for value, path in ((collections, "collections"), (variables, "variables"), (pages, "pages"),
                        (usages, "usages"), (evidence, "document_evidence"), (warnings, "warnings")):
        array(value, path, errors)
    collections = collections if isinstance(collections, list) else []
    variables = variables if isinstance(variables, list) else []
    pages = pages if isinstance(pages, list) else []
    usages = usages if isinstance(usages, list) else []
    evidence = evidence if isinstance(evidence, list) else []

    collection_ids: set[str] = set()
    modes_by_collection: dict[str, set[str]] = {}
    declared_variables: dict[str, str] = {}
    for index, collection in enumerate(collections):
        path = f"collections[{index}]"
        required(collection, {"id", "name", "default_mode_id", "modes", "variable_ids", "provenance"}, path, errors)
        if not obj(collection):
            continue
        cid = collection.get("id")
        nonempty(cid, f"{path}.id", errors)
        nonempty(collection.get("name"), f"{path}.name", errors)
        if cid in collection_ids:
            errors.append(f"{path}.id: duplicate collection ID")
        if isinstance(cid, str):
            collection_ids.add(cid)
        modes = collection.get("modes")
        mode_ids: set[str] = set()
        mode_positions: set[int] = set()
        if array(modes, f"{path}.modes", errors):
            for mode_index, mode in enumerate(modes):
                mode_path = f"{path}.modes[{mode_index}]"
                required(mode, {"id", "name", "position"}, mode_path, errors)
                if obj(mode):
                    mid = mode.get("id")
                    nonempty(mid, f"{mode_path}.id", errors)
                    nonempty(mode.get("name"), f"{mode_path}.name", errors)
                    position = mode.get("position")
                    nonnegative_int(position, f"{mode_path}.position", errors)
                    if mid in mode_ids:
                        errors.append(f"{mode_path}.id: duplicate mode ID")
                    if isinstance(position, int) and position in mode_positions:
                        errors.append(f"{mode_path}.position: duplicate mode position")
                    if isinstance(mid, str):
                        mode_ids.add(mid)
                    if isinstance(position, int):
                        mode_positions.add(position)
        if collection.get("default_mode_id") not in mode_ids:
            errors.append(f"{path}.default_mode_id: must reference a collection mode")
        if isinstance(cid, str):
            modes_by_collection[cid] = mode_ids
        variable_ids = collection.get("variable_ids")
        if array(variable_ids, f"{path}.variable_ids", errors):
            for variable_id in variable_ids:
                nonempty(variable_id, f"{path}.variable_ids[]", errors)
                if variable_id in declared_variables:
                    errors.append(f"{path}.variable_ids: variable declared by multiple collections")
                elif isinstance(variable_id, str) and isinstance(cid, str):
                    declared_variables[variable_id] = cid
        provenance(collection.get("provenance"), f"{path}.provenance", adapter_id, source_type, errors)

    variable_ids: set[str] = set()
    alias_targets: list[tuple[str, str]] = []
    for index, variable in enumerate(variables):
        path = f"variables[{index}]"
        required(variable, {"id", "name", "collection_id", "resolved_type", "description", "scopes", "values_by_mode", "provenance"}, path, errors)
        if not obj(variable):
            continue
        vid = variable.get("id")
        cid = variable.get("collection_id")
        nonempty(vid, f"{path}.id", errors)
        nonempty(variable.get("name"), f"{path}.name", errors)
        nonempty(cid, f"{path}.collection_id", errors)
        enum(variable.get("resolved_type"), VARIABLE_TYPES, f"{path}.resolved_type", errors)
        description = variable.get("description")
        if not isinstance(description, str):
            if not obj(description) or description.get("status") != "not_observable":
                errors.append(f"{path}.description: expected string or not_observable status object")
        if vid in variable_ids:
            errors.append(f"{path}.id: duplicate variable ID")
        if isinstance(vid, str):
            variable_ids.add(vid)
        if cid not in collection_ids:
            errors.append(f"{path}.collection_id: unknown collection")
        if isinstance(vid, str) and declared_variables.get(vid) != cid:
            errors.append(f"{path}: collection variable_ids relationship is inconsistent")
        scopes = variable.get("scopes")
        if isinstance(scopes, list):
            string_array(scopes, f"{path}.scopes", errors)
        elif not obj(scopes) or scopes.get("status") != "not_observable":
            errors.append(f"{path}.scopes: expected string array or not_observable status object")
        values = variable.get("values_by_mode")
        if not obj(values):
            errors.append(f"{path}.values_by_mode: expected object")
        else:
            allowed_modes = modes_by_collection.get(cid, set())
            if set(values) != allowed_modes:
                errors.append(f"{path}.values_by_mode: keys must exactly match collection modes")
            for mode_id, value in values.items():
                value_path = f"{path}.values_by_mode.{mode_id}"
                required(value, {"kind"}, value_path, errors)
                if not obj(value):
                    continue
                kind = value.get("kind")
                enum(kind, VALUE_KINDS, f"{value_path}.kind", errors)
                if kind == "literal" and "value" not in value:
                    errors.append(f"{value_path}.value: missing literal value")
                elif kind == "literal":
                    validate_literal(value.get("value"), variable.get("resolved_type"), f"{value_path}.value", errors)
                if kind == "alias":
                    nonempty(value.get("target_variable_id"), f"{value_path}.target_variable_id", errors)
                    if isinstance(value.get("target_variable_id"), str):
                        alias_targets.append((value_path, value["target_variable_id"]))
                if kind == "not_observable":
                    nonempty(value.get("reason"), f"{value_path}.reason", errors)
                    if value.get("target_variable_id") is not None:
                        nonempty(value.get("target_variable_id"), f"{value_path}.target_variable_id", errors)
        provenance(variable.get("provenance"), f"{path}.provenance", adapter_id, source_type, errors)

    for path, target in alias_targets:
        if target not in variable_ids:
            errors.append(f"{path}.target_variable_id: unresolved local alias target")
    for declared_id in declared_variables:
        if declared_id not in variable_ids:
            errors.append(f"collections.variable_ids: unknown variable {declared_id!r}")

    page_ids: set[str] = set()
    for index, page in enumerate(pages):
        path = f"pages[{index}]"
        required(page, {"id", "name", "traversal_status", "provenance"}, path, errors)
        if obj(page):
            pid = page.get("id")
            nonempty(pid, f"{path}.id", errors)
            nonempty(page.get("name"), f"{path}.name", errors)
            if pid in page_ids:
                errors.append(f"{path}.id: duplicate page ID")
            if isinstance(pid, str):
                page_ids.add(pid)
            enum(page.get("traversal_status"), PAGE_STATUSES, f"{path}.traversal_status", errors)
            provenance(page.get("provenance"), f"{path}.provenance", adapter_id, source_type, errors)

    for index, usage in enumerate(usages):
        path = f"usages[{index}]"
        required(usage, {"variable_id", "node_id", "page_id", "binding_path", "binding_kind", "provenance"}, path, errors)
        if obj(usage):
            for key in ("variable_id", "node_id", "page_id", "binding_path", "binding_kind"):
                nonempty(usage.get(key), f"{path}.{key}", errors)
            if usage.get("variable_id") not in variable_ids:
                errors.append(f"{path}.variable_id: unknown variable")
            pages_complete = obj(coverage) and obj(coverage.get("pages")) and coverage["pages"].get("status") == "complete"
            if pages_complete and usage.get("page_id") not in page_ids:
                errors.append(f"{path}.page_id: unknown page")
            provenance(usage.get("provenance"), f"{path}.provenance", adapter_id, source_type, errors)

    for index, item in enumerate(evidence):
        path = f"document_evidence[{index}]"
        required(item, {"evidence_type", "node_id", "page_id", "node_name", "node_type", "matched_by", "provenance"}, path, errors)
        if obj(item):
            enum(item.get("evidence_type"), EVIDENCE_TYPES, f"{path}.evidence_type", errors)
            for key in ("node_id", "page_id", "node_name", "node_type", "matched_by"):
                nonempty(item.get(key), f"{path}.{key}", errors)
            pages_complete = obj(coverage) and obj(coverage.get("pages")) and coverage["pages"].get("status") == "complete"
            if pages_complete and item.get("page_id") not in page_ids:
                errors.append(f"{path}.page_id: unknown page")
            provenance(item.get("provenance"), f"{path}.provenance", adapter_id, source_type, errors)

    if obj(coverage):
        expected_counts = {"collections": len(collections), "variables": len(variables)}
        for name, count in expected_counts.items():
            section = coverage.get(name)
            if obj(section) and section.get("captured") != count:
                errors.append(f"coverage.{name}.captured: must equal captured array length")
        pages_coverage = coverage.get("pages")
        if obj(pages_coverage):
            captured_ids = pages_coverage.get("captured_ids")
            if isinstance(captured_ids, list) and set(captured_ids) != page_ids:
                errors.append("coverage.pages.captured_ids: must equal captured page IDs")
    return errors


def semantic_projection(data: dict[str, Any]) -> dict[str, Any]:
    """Return adapter-independent token semantics for contract comparison."""
    collection_names = {item["id"]: item["name"] for item in data["collections"]}
    variable_names = {item["id"]: item["name"] for item in data["variables"]}
    collection_name_counts: dict[str, int] = {}
    variable_name_counts: dict[tuple[str, str], int] = {}
    for collection in data["collections"]:
        collection_name_counts[collection["name"]] = collection_name_counts.get(collection["name"], 0) + 1
    for variable in data["variables"]:
        key = (collection_names[variable["collection_id"]], variable["name"])
        variable_name_counts[key] = variable_name_counts.get(key, 0) + 1
    if any(count > 1 for count in collection_name_counts.values()):
        raise ValueError("semantic comparison requires unique collection names")
    if any(count > 1 for count in variable_name_counts.values()):
        raise ValueError("semantic comparison requires unique variable names within each collection")

    collections = []
    for item in data["collections"]:
        local_mode_names = {mode["id"]: mode["name"] for mode in item["modes"]}
        collections.append({
            "name": item["name"],
            "default_mode": local_mode_names[item["default_mode_id"]],
            "modes": [mode["name"] for mode in sorted(item["modes"], key=lambda mode: mode["position"])],
        })
    variables = []
    for item in data["variables"]:
        collection = next(collection for collection in data["collections"] if collection["id"] == item["collection_id"])
        local_mode_names = {mode["id"]: mode["name"] for mode in collection["modes"]}
        values: dict[str, Any] = {}
        for mode_id, value in item["values_by_mode"].items():
            normalized = dict(value)
            if normalized.get("kind") == "alias":
                normalized["target_variable"] = variable_names[normalized.pop("target_variable_id")]
            values[local_mode_names[mode_id]] = normalized
        variables.append({
            "name": item["name"],
            "collection": collection_names[item["collection_id"]],
            "resolved_type": item["resolved_type"],
            "description": item["description"],
            "scopes": sorted(item["scopes"]) if isinstance(item["scopes"], list) else item["scopes"],
            "values_by_mode": values,
        })
    return {
        "file_key": data["source"]["file_key"],
        "collections": sorted(collections, key=lambda item: item["name"]),
        "variables": sorted(variables, key=lambda item: (item["collection"], item["name"])),
    }


def load(path: str) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="+", help="One or more canonical snapshot JSON files")
    parser.add_argument("--compare", action="store_true", help="Require semantic equivalence across snapshots")
    args = parser.parse_args()
    loaded: list[tuple[str, Any]] = []
    failed = False
    for path in args.paths:
        try:
            data = load(path)
        except (OSError, json.JSONDecodeError) as exc:
            print(f"ERROR: {path}: {exc}", file=sys.stderr)
            failed = True
            continue
        errors = validate(data)
        if errors:
            for error in errors:
                print(f"ERROR: {path}: {error}", file=sys.stderr)
            failed = True
        else:
            print(f"valid snapshot: {path}")
            loaded.append((path, data))
    if failed:
        return 1
    if args.compare and len(loaded) < 2:
        print("ERROR: --compare requires at least two valid snapshots", file=sys.stderr)
        return 2
    if args.compare:
        baseline_path, baseline = loaded[0]
        try:
            projection = semantic_projection(baseline)
        except (KeyError, TypeError, ValueError) as exc:
            print(f"ERROR: {baseline_path}: cannot compare semantic projection: {exc}", file=sys.stderr)
            return 1
        for path, data in loaded[1:]:
            try:
                candidate_projection = semantic_projection(data)
            except (KeyError, TypeError, ValueError) as exc:
                print(f"ERROR: {path}: cannot compare semantic projection: {exc}", file=sys.stderr)
                return 1
            if candidate_projection != projection:
                print(f"ERROR: {path}: semantic projection differs from {baseline_path}", file=sys.stderr)
                return 1
        print(f"semantic equivalence confirmed across {len(loaded)} snapshots")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
