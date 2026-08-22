#!/usr/bin/env python3
"""Validate canonical Figma token snapshots and compare semantic equivalence."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


COVERAGE_STATUSES = {"complete", "partial", "not_observable", "not_configured", "failed"}
SOURCE_TYPES = {"plugin_api", "mcp", "api", "export", "mixed"}
CAPABILITY_STATUSES = {"available", "partial", "unavailable", "unknown", "failed"}
VALUE_KINDS = {"literal", "alias", "missing", "not_observable"}
PAGE_STATUSES = {"complete", "partial", "not_observable", "failed"}
EVIDENCE_TYPES = {"changelog", "reference", "other"}
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


def array(value: Any, path: str, errors: list[str]) -> bool:
    if not isinstance(value, list):
        errors.append(f"{path}: expected array")
        return False
    return True


def enum(value: Any, allowed: set[str], path: str, errors: list[str]) -> None:
    if value not in allowed:
        errors.append(f"{path}: expected one of {sorted(allowed)}, got {value!r}")


def provenance(value: Any, path: str, adapter_id: Any, errors: list[str]) -> None:
    required(value, {"adapter_id", "source_path"}, path, errors)
    if not obj(value):
        return
    nonempty(value.get("adapter_id"), f"{path}.adapter_id", errors)
    nonempty(value.get("source_path"), f"{path}.source_path", errors)
    if value.get("adapter_id") != adapter_id:
        errors.append(f"{path}.adapter_id: must match adapter.adapter_id")


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
    try:
        datetime.fromisoformat(str(data.get("captured_at", "")).replace("Z", "+00:00"))
    except ValueError:
        errors.append("captured_at: invalid ISO-8601 timestamp")

    source = data.get("source")
    required(source, {"file_key", "file_name"}, "source", errors)
    if obj(source):
        nonempty(source.get("file_key"), "source.file_key", errors)
        nonempty(source.get("file_name"), "source.file_name", errors)

    adapter = data.get("adapter")
    required(adapter, {"adapter_id", "adapter_version", "source_type", "capabilities"}, "adapter", errors)
    adapter_id = adapter.get("adapter_id") if obj(adapter) else None
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
        if array(modes, f"{path}.modes", errors):
            for mode_index, mode in enumerate(modes):
                mode_path = f"{path}.modes[{mode_index}]"
                required(mode, {"id", "name", "position"}, mode_path, errors)
                if obj(mode):
                    mid = mode.get("id")
                    if mid in mode_ids:
                        errors.append(f"{mode_path}.id: duplicate mode ID")
                    if isinstance(mid, str):
                        mode_ids.add(mid)
        if collection.get("default_mode_id") not in mode_ids:
            errors.append(f"{path}.default_mode_id: must reference a collection mode")
        if isinstance(cid, str):
            modes_by_collection[cid] = mode_ids
        variable_ids = collection.get("variable_ids")
        if array(variable_ids, f"{path}.variable_ids", errors):
            for variable_id in variable_ids:
                if variable_id in declared_variables:
                    errors.append(f"{path}.variable_ids: variable declared by multiple collections")
                elif isinstance(variable_id, str) and isinstance(cid, str):
                    declared_variables[variable_id] = cid
        provenance(collection.get("provenance"), f"{path}.provenance", adapter_id, errors)

    variable_ids: set[str] = set()
    alias_targets: list[tuple[str, str]] = []
    for index, variable in enumerate(variables):
        path = f"variables[{index}]"
        required(variable, {"id", "name", "collection_id", "resolved_type", "description", "scopes", "values_by_mode", "provenance"}, path, errors)
        if not obj(variable):
            continue
        vid = variable.get("id")
        cid = variable.get("collection_id")
        if vid in variable_ids:
            errors.append(f"{path}.id: duplicate variable ID")
        if isinstance(vid, str):
            variable_ids.add(vid)
        if cid not in collection_ids:
            errors.append(f"{path}.collection_id: unknown collection")
        if isinstance(vid, str) and declared_variables.get(vid) != cid:
            errors.append(f"{path}: collection variable_ids relationship is inconsistent")
        array(variable.get("scopes"), f"{path}.scopes", errors)
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
                if kind == "alias":
                    nonempty(value.get("target_variable_id"), f"{value_path}.target_variable_id", errors)
                    if isinstance(value.get("target_variable_id"), str):
                        alias_targets.append((value_path, value["target_variable_id"]))
                if kind == "not_observable":
                    nonempty(value.get("reason"), f"{value_path}.reason", errors)
        provenance(variable.get("provenance"), f"{path}.provenance", adapter_id, errors)

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
            if pid in page_ids:
                errors.append(f"{path}.id: duplicate page ID")
            if isinstance(pid, str):
                page_ids.add(pid)
            enum(page.get("traversal_status"), PAGE_STATUSES, f"{path}.traversal_status", errors)
            provenance(page.get("provenance"), f"{path}.provenance", adapter_id, errors)

    for index, usage in enumerate(usages):
        path = f"usages[{index}]"
        required(usage, {"variable_id", "node_id", "page_id", "binding_path", "binding_kind", "provenance"}, path, errors)
        if obj(usage):
            if usage.get("variable_id") not in variable_ids:
                errors.append(f"{path}.variable_id: unknown variable")
            if page_ids and usage.get("page_id") not in page_ids:
                errors.append(f"{path}.page_id: unknown page")
            provenance(usage.get("provenance"), f"{path}.provenance", adapter_id, errors)

    for index, item in enumerate(evidence):
        path = f"document_evidence[{index}]"
        required(item, {"evidence_type", "node_id", "page_id", "node_name", "node_type", "matched_by", "provenance"}, path, errors)
        if obj(item):
            enum(item.get("evidence_type"), EVIDENCE_TYPES, f"{path}.evidence_type", errors)
            if page_ids and item.get("page_id") not in page_ids:
                errors.append(f"{path}.page_id: unknown page")
            provenance(item.get("provenance"), f"{path}.provenance", adapter_id, errors)

    if obj(coverage):
        expected_counts = {"collections": len(collections), "variables": len(variables)}
        for name, count in expected_counts.items():
            section = coverage.get(name)
            if obj(section) and section.get("captured") != count:
                errors.append(f"coverage.{name}.captured: must equal captured array length")
    return errors


def semantic_projection(data: dict[str, Any]) -> dict[str, Any]:
    """Return adapter-independent token semantics for contract comparison."""
    collection_names = {item["id"]: item["name"] for item in data["collections"]}
    mode_names = {
        mode["id"]: mode["name"]
        for collection in data["collections"]
        for mode in collection["modes"]
    }
    variable_names = {item["id"]: item["name"] for item in data["variables"]}
    collections = []
    for item in data["collections"]:
        collections.append({
            "name": item["name"],
            "default_mode": mode_names[item["default_mode_id"]],
            "modes": [mode["name"] for mode in sorted(item["modes"], key=lambda mode: mode["position"])],
        })
    variables = []
    for item in data["variables"]:
        values: dict[str, Any] = {}
        for mode_id, value in item["values_by_mode"].items():
            normalized = dict(value)
            if normalized.get("kind") == "alias":
                normalized["target_variable"] = variable_names[normalized.pop("target_variable_id")]
            values[mode_names[mode_id]] = normalized
        variables.append({
            "name": item["name"],
            "collection": collection_names[item["collection_id"]],
            "resolved_type": item["resolved_type"],
            "description": item["description"],
            "scopes": sorted(item["scopes"]),
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
        projection = semantic_projection(baseline)
        for path, data in loaded[1:]:
            if semantic_projection(data) != projection:
                print(f"ERROR: {path}: semantic projection differs from {baseline_path}", file=sys.stderr)
                return 1
        print(f"semantic equivalence confirmed across {len(loaded)} snapshots")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
