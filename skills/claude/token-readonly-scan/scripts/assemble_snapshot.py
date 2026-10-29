#!/usr/bin/env python3
"""Assemble Figma Console collector chunks into the canonical suite snapshot."""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ADAPTER_ID = "figma-console-plugin-api"
PROPERTY_PATTERNS = {
    "simple_node_fields": [
        "height", "width", "characters", "itemSpacing", "paddingLeft", "paddingRight", "paddingTop",
        "paddingBottom", "visible", "cornerRadius", "topLeftRadius", "topRightRadius", "bottomLeftRadius",
        "bottomRightRadius", "minWidth", "maxWidth", "minHeight", "maxHeight", "counterAxisSpacing",
        "strokeWeight", "strokeTopWeight", "strokeRightWeight", "strokeBottomWeight", "strokeLeftWeight",
        "opacity", "gridRowGap", "gridColumnGap",
    ],
    "paints": ["fills[*].color", "strokes[*].color", "textRangeFills[*].color"],
    "effects": ["effects[*].radius", "effects[*].color", "effects[*].spread", "effects[*].offsetX", "effects[*].offsetY"],
    "layout_grids": ["layoutGrids[*].sectionSize", "layoutGrids[*].count", "layoutGrids[*].offset", "layoutGrids[*].gutterSize"],
    "typography": ["fontFamily", "fontSize", "fontStyle", "fontWeight", "letterSpacing", "lineHeight", "paragraphSpacing", "paragraphIndent"],
    "component_properties": ["componentProperties[*]"],
}


def load_validator() -> Any:
    path = Path(__file__).resolve().parent / "validate_snapshot.py"
    spec = importlib.util.spec_from_file_location("snapshot_validator", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load validate_snapshot.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


VALIDATOR = load_validator()


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def provenance(source_path: str, captured_at: str | None = None) -> dict[str, Any]:
    result: dict[str, Any] = {"adapter_id": ADAPTER_ID, "source_path": source_path}
    if captured_at:
        result["captured_at"] = captured_at
    return result


def without_provenance(item: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in item.items() if key != "provenance"}


def merge_unique(target: dict[str, Any], item: dict[str, Any], label: str, errors: list[str]) -> None:
    item_id = item.get("id")
    if not isinstance(item_id, str) or not item_id:
        errors.append(f"{label}: record has no non-empty id")
    elif item_id in target and without_provenance(target[item_id]) != without_provenance(item):
        errors.append(f"{label}: conflicting duplicate id {item_id!r}")
    else:
        target[item_id] = item


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("chunks", nargs="+", help="Collector chunk JSON files")
    parser.add_argument("--out", required=True, help="Canonical snapshot JSON path")
    parser.add_argument("--out-observations", help="Optional property-observation sidecar for Audit 1.5")
    parser.add_argument("--snapshot-id", help="Stable snapshot identifier; generated when omitted")
    parser.add_argument("--file-key", help="Required only when the collector cannot expose figma.fileKey")
    args = parser.parse_args()

    errors: list[str] = []
    warnings: list[str] = []
    chunks: list[tuple[Path, dict[str, Any]]] = []
    for raw_path in args.chunks:
        path = Path(raw_path)
        try:
            value = load(path)
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"{path}: {exc}")
            continue
        if not isinstance(value, dict):
            errors.append(f"{path}: expected a JSON object")
            continue
        if value.get("chunk_version") != "1.0.0":
            errors.append(f"{path}: unsupported chunk_version {value.get('chunk_version')!r}")
        if value.get("adapter_id") != ADAPTER_ID:
            errors.append(f"{path}: adapter_id must be {ADAPTER_ID!r}")
        if value.get("error"):
            errors.append(f"{path}: collector error: {value['error']}")
        chunks.append((path, value))

    source_names = {chunk.get("source", {}).get("file_name") for _, chunk in chunks}
    source_keys = {chunk.get("source", {}).get("file_key") for _, chunk in chunks if chunk.get("source", {}).get("file_key")}
    if len(source_names) != 1 or None in source_names or "" in source_names:
        errors.append("collector chunks must have one non-empty source.file_name")
    if len(source_keys) > 1:
        errors.append("collector chunks refer to different source.file_key values")
    file_key = args.file_key or (next(iter(source_keys)) if source_keys else None)
    if not file_key:
        errors.append("source file key is unavailable; pass --file-key with a verified key")

    inventory_chunks = [item for item in chunks if item[1].get("chunk_type") == "figma_token_variables" and item[1].get("operation") == "inventory"]
    variable_chunks = [item for item in chunks if item[1].get("chunk_type") == "figma_token_variables" and item[1].get("operation") == "variables"]
    page_inventory_chunks = [item for item in chunks if item[1].get("chunk_type") == "figma_token_properties" and item[1].get("operation") == "page_inventory"]
    page_chunks = [item for item in chunks if item[1].get("chunk_type") == "figma_token_properties" and item[1].get("operation") == "pages"]
    if len(inventory_chunks) != 1:
        errors.append("exactly one complete variable inventory chunk is required")
    if inventory_chunks and inventory_chunks[0][1].get("complete") is not True:
        errors.append("variable inventory chunk is not complete")

    collections: dict[str, Any] = {}
    variables: dict[str, Any] = {}
    pages: dict[str, Any] = {}
    usages: dict[tuple[str, str, str, str], Any] = {}
    referenced_variables: dict[str, Any] = {}
    observations: list[dict[str, Any]] = []
    expected_collection_ids: set[str] = set()
    completed_collection_ids: set[str] = set()
    expected_page_ids: set[str] = set()
    completed_page_ids: set[str] = set()
    adapter_versions: set[str] = set()

    for path, chunk in chunks:
        if isinstance(chunk.get("adapter_version"), str):
            adapter_versions.add(chunk["adapter_version"])
        captured_at = chunk.get("captured_at") if isinstance(chunk.get("captured_at"), str) else None
        source_path = f"collector chunk {path.name}"
        if chunk.get("operation") == "inventory":
            for raw in chunk.get("collections", []):
                record = dict(raw)
                record["provenance"] = provenance(source_path, captured_at)
                merge_unique(collections, record, str(path), errors)
                if isinstance(record.get("id"), str):
                    expected_collection_ids.add(record["id"])
        elif chunk.get("operation") == "variables":
            if chunk.get("truncated"):
                warnings.append(f"{path.name}: variable collection was truncated")
            completed_collection_ids.update(item for item in chunk.get("completed_collection_ids", []) if isinstance(item, str))
            for raw in chunk.get("variables", []):
                record = dict(raw)
                record["provenance"] = provenance(source_path, captured_at)
                merge_unique(variables, record, str(path), errors)
        elif chunk.get("operation") == "page_inventory":
            if chunk.get("complete") is not True:
                warnings.append(f"{path.name}: page inventory is incomplete")
            for raw in chunk.get("pages", []):
                if isinstance(raw, dict) and isinstance(raw.get("id"), str):
                    expected_page_ids.add(raw["id"])
        elif chunk.get("operation") == "pages":
            completed_page_ids.update(item for item in chunk.get("completed_page_ids", []) if isinstance(item, str))
            for raw_page in chunk.get("pages", []):
                if not isinstance(raw_page, dict):
                    errors.append(f"{path}: page record must be an object")
                    continue
                page = {
                    "id": raw_page.get("id"),
                    "name": raw_page.get("name"),
                    "traversal_status": raw_page.get("traversal_status"),
                    "node_count": raw_page.get("node_count"),
                    "provenance": provenance(source_path, captured_at),
                }
                merge_unique(pages, page, str(path), errors)
                for raw_usage in raw_page.get("usages", []):
                    if not isinstance(raw_usage, dict):
                        errors.append(f"{path}: usage record must be an object")
                        continue
                    usage = dict(raw_usage)
                    usage["provenance"] = provenance(source_path, captured_at)
                    key = tuple(usage.get(field) for field in ("node_id", "page_id", "binding_path", "variable_id"))
                    if not all(isinstance(item, str) and item for item in key):
                        errors.append(f"{path}: usage has an incomplete identity")
                    elif key in usages and without_provenance(usages[key]) != without_provenance(usage):
                        errors.append(f"{path}: conflicting duplicate usage {key!r}")
                    else:
                        usages[key] = usage
                for raw_observation in raw_page.get("observations", []):
                    if isinstance(raw_observation, dict):
                        observation = dict(raw_observation)
                        observation["provenance"] = provenance(source_path, captured_at)
                        observations.append(observation)
            for raw in chunk.get("referenced_variables", []):
                record = dict(raw)
                record["provenance"] = provenance(source_path, captured_at)
                merge_unique(referenced_variables, record, str(path), errors)

    unresolved_reference_ids = sorted(
        reference_id for reference_id, reference in referenced_variables.items()
        if reference.get("origin") == "unresolved_reference"
    )

    if len(adapter_versions) != 1:
        errors.append("collector chunks must use exactly one adapter version")
    unknown_completed = completed_collection_ids - expected_collection_ids
    if unknown_completed:
        errors.append(f"completed variable chunks contain unknown collections: {sorted(unknown_completed)}")
    missing_collections = expected_collection_ids - completed_collection_ids
    # A complete inventory with no local collections is a valid, complete (empty) result.
    variable_status = "complete" if not missing_collections else "partial"
    if missing_collections:
        warnings.append(f"variable chunks missing complete collections: {sorted(missing_collections)}")

    if page_inventory_chunks:
        missing_pages = expected_page_ids - completed_page_ids
        page_status = "complete" if not missing_pages else "partial"
        if missing_pages:
            warnings.append(f"page chunks missing complete pages: {sorted(missing_pages)}")
    else:
        missing_pages = set()
        page_status = "not_configured"
    usage_status = page_status if page_inventory_chunks else "not_configured"
    if unresolved_reference_ids and usage_status == "complete":
        usage_status = "partial"
        warnings.append(
            f"{len(unresolved_reference_ids)} bound variable reference(s) could not be resolved: "
            f"{unresolved_reference_ids}"
        )

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    captured_times = sorted(chunk.get("captured_at") for _, chunk in chunks if isinstance(chunk.get("captured_at"), str))
    snapshot = {
        "schema_version": "1.1.0",
        "snapshot_type": "figma_token_snapshot",
        "snapshot_id": args.snapshot_id or f"dts-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}",
        "captured_at": captured_times[-1] if captured_times else utc_now(),
        "source": {"file_key": file_key, "file_name": next(iter(source_names))},
        "adapter": {
            "adapter_id": ADAPTER_ID,
            "adapter_version": next(iter(adapter_versions)),
            "source_type": "plugin_api",
            "capabilities": {
                "identify_file": {"status": "available", "evidence": "verified collector source"},
                "read_local_collections": {"status": "available", "evidence": "inventory chunk"},
                "read_local_variables": {"status": "available", "evidence": "variable chunks"},
                "traverse_nodes": {"status": "available" if page_inventory_chunks else "unavailable", "evidence": "page collector" if page_inventory_chunks else "not requested"},
                "read_bound_variables": {"status": "available" if page_inventory_chunks else "unavailable", "evidence": "property collector" if page_inventory_chunks else "not requested"},
            },
            "raw_source_timestamp": captured_times[0] if captured_times else None,
        },
        "coverage": {
            "collections": {"status": "complete", "captured": len(collections), "failed": 0},
            "variables": {"status": variable_status, "captured": len(variables), "failed": len(missing_collections)},
            "pages": {"status": page_status, "captured_ids": sorted(pages), "omitted_ids": sorted(missing_pages)},
            "usages": {"status": usage_status},
            "document_evidence": {"status": "not_configured"},
        },
        "collections": sorted(collections.values(), key=lambda item: item["id"]),
        "variables": sorted(variables.values(), key=lambda item: item["id"]),
        "pages": sorted(pages.values(), key=lambda item: item["id"]),
        "usages": sorted(usages.values(), key=lambda item: (item["page_id"], item["node_id"], item["binding_path"], item["variable_id"])),
        "referenced_variables": sorted(referenced_variables.values(), key=lambda item: item["id"]),
        "document_evidence": [],
        "warnings": warnings,
    }
    validation_errors = VALIDATOR.validate(snapshot)
    if validation_errors:
        for error in validation_errors:
            print(f"ERROR: assembled snapshot: {error}", file=sys.stderr)
        return 1
    write(Path(args.out), snapshot)
    if args.out_observations:
        families: dict[str, Any] = {}
        for family_name, patterns in PROPERTY_PATTERNS.items():
            records = []
            for pattern in patterns:
                matching = [item for item in observations if item.get("family") == family_name and item.get("property_pattern") == pattern]
                records.append({
                    "property_path": pattern,
                    "status": "complete" if matching else "not_applicable",
                    "eligible_nodes": len(matching),
                    "inspected_nodes": len(matching),
                    "bound_count": sum(item.get("state") == "bound" for item in matching),
                    "literal_count": sum(item.get("state") == "literal" for item in matching),
                    "mixed_or_unsupported_count": sum(item.get("state") == "mixed_or_unsupported" for item in matching),
                    "limitations": [],
                })
            family_status = "not_applicable" if all(item["status"] == "not_applicable" for item in records) else "complete"
            families[family_name] = {
                "support_status": "supported",
                "status": family_status,
                "declared_paths": patterns,
                "properties": records,
                "limitations": [],
            }
        property_coverage = None
        if page_status == "complete":
            property_coverage = {
                "contract_version": "1.0.0",
                "status": "complete",
                "source": {
                    "adapter_id": ADAPTER_ID,
                    "capability_basis": "official_figma_plugin_api",
                    "canonical_profile": "figma_plugin_api_2026_09",
                    "capability_evidence": "collect_figma_properties.js 0.9.1 canonical property declaration",
                },
                "families": families,
                "excluded_non_bindable_properties": ["rotation", "blendMode", "layoutSizingHorizontal", "layoutSizingVertical"],
                "limitations": [],
            }
        write(Path(args.out_observations), {
            "schema_version": "1.0.0",
            "evidence_type": "figma_property_observations",
            "source_snapshot_id": snapshot["snapshot_id"],
            "property_coverage_status": page_status,
            "property_coverage": property_coverage,
            "observations": observations,
            "warnings": warnings,
        })
    print(f"assembled canonical snapshot: {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
