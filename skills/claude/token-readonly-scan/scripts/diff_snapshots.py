#!/usr/bin/env python3
"""Diff canonical snapshots for pre-write drift and exact post-write verification."""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent


def load_validator() -> Any:
    spec = importlib.util.spec_from_file_location("snapshot_validator", SCRIPT_DIR / "validate_snapshot.py")
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load validate_snapshot.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


VALIDATOR = load_validator()


def load(path: str) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def read_ids(path: str | None) -> set[str] | None:
    if not path:
        return None
    return {
        line.strip()
        for line in Path(path).read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    }


def change(kind: str, target_id: str, path: str, before: Any, after: Any) -> dict[str, Any]:
    operation = "added" if before is None else "removed" if after is None else "changed"
    return {
        "target_kind": kind,
        "target_id": target_id,
        "path": path,
        "change": operation,
        "before": before,
        "after": after,
    }


def field_changes(kind: str, target_id: str, before: dict[str, Any], after: dict[str, Any], fields: list[str]) -> list[dict[str, Any]]:
    result = []
    for field in fields:
        if before.get(field) != after.get(field):
            result.append(change(kind, target_id, field, before.get(field), after.get(field)))
    return result


def diff_records(before: dict[str, Any], after: dict[str, Any], variable_ids: set[str] | None, include_usages: bool) -> tuple[list[dict[str, Any]], set[str]]:
    result: list[dict[str, Any]] = []
    matched: set[str] = set()
    before_collections = {item["id"]: item for item in before["collections"]}
    after_collections = {item["id"]: item for item in after["collections"]}
    for item_id in sorted(before_collections.keys() | after_collections.keys()):
        left, right = before_collections.get(item_id), after_collections.get(item_id)
        if left is None or right is None:
            result.append(change("collection", item_id, "$", left, right))
        else:
            result.extend(field_changes("collection", item_id, left, right, ["name", "default_mode_id", "modes", "variable_ids", "remote", "hidden_from_publishing"]))

    before_variables = {item["id"]: item for item in before["variables"]}
    after_variables = {item["id"]: item for item in after["variables"]}
    candidate_ids = before_variables.keys() | after_variables.keys()
    for item_id in sorted(candidate_ids):
        if variable_ids is not None and item_id not in variable_ids:
            continue
        matched.add(item_id)
        left, right = before_variables.get(item_id), after_variables.get(item_id)
        if left is None or right is None:
            result.append(change("variable", item_id, "$", left, right))
        else:
            result.extend(field_changes("variable", item_id, left, right, [
                "name", "collection_id", "resolved_type", "description", "scopes", "remote",
                "hidden_from_publishing", "code_syntax", "values_by_mode",
            ]))

    if include_usages:
        def usages(snapshot: dict[str, Any]) -> dict[tuple[str, str, str], dict[str, Any]]:
            records = {}
            for item in snapshot["usages"]:
                if variable_ids is not None and item["variable_id"] not in variable_ids:
                    continue
                locator = (item["page_id"], item["node_id"], item["binding_path"])
                records[locator] = {"variable_id": item["variable_id"], "binding_kind": item["binding_kind"]}
                matched.add(item["variable_id"])
            return records
        before_usages, after_usages = usages(before), usages(after)
        for locator in sorted(before_usages.keys() | after_usages.keys()):
            left, right = before_usages.get(locator), after_usages.get(locator)
            if left != right:
                page_id, node_id, binding_path = locator
                result.append(change("usage", f"{page_id}|{node_id}", binding_path, left, right))
    return result, matched


def canonical_expected(item: Any) -> str:
    return json.dumps(item, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("before")
    parser.add_argument("after")
    parser.add_argument("--only-variable-ids", help="One variable ID per line")
    parser.add_argument("--include-usages", action="store_true", help="Also compare exact node/property bindings")
    parser.add_argument("--expect", help="JSON list of exact change objects including before and after")
    parser.add_argument("--json", help="Write detected changes as JSON")
    args = parser.parse_args()

    try:
        before, after = load(args.before), load(args.after)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    for label, snapshot in (("before", before), ("after", after)):
        errors = VALIDATOR.validate(snapshot)
        if errors:
            for error in errors:
                print(f"ERROR: {label}: {error}", file=sys.stderr)
            return 1
        for section in ("collections", "variables"):
            if snapshot["coverage"][section]["status"] != "complete":
                print(f"ERROR: {label}: coverage.{section} must be complete for drift comparison", file=sys.stderr)
                return 1
        if args.include_usages:
            for section in ("pages", "usages"):
                if snapshot["coverage"][section]["status"] != "complete":
                    print(f"ERROR: {label}: coverage.{section} must be complete with --include-usages", file=sys.stderr)
                    return 1
    if before["source"]["file_key"] != after["source"]["file_key"]:
        print("ERROR: snapshots refer to different source.file_key values", file=sys.stderr)
        return 1

    selected = read_ids(args.only_variable_ids)
    changes, matched = diff_records(before, after, selected, args.include_usages)
    if selected is not None and not matched:
        print("NOTHING MATCHED — the variable filter selected no records", file=sys.stderr)
        return 4
    if args.json:
        Path(args.json).write_text(json.dumps(changes, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    for item in changes:
        print(json.dumps(item, ensure_ascii=False, sort_keys=True))

    if args.expect:
        try:
            expected = load(args.expect)
        except (OSError, json.JSONDecodeError) as exc:
            print(f"ERROR: expected changes: {exc}", file=sys.stderr)
            return 1
        if not isinstance(expected, list):
            print("ERROR: expected changes must be a JSON list", file=sys.stderr)
            return 1
        got_set = {canonical_expected(item) for item in changes}
        expected_set = {canonical_expected(item) for item in expected}
        if len(got_set) != len(changes) or len(expected_set) != len(expected):
            print("ERROR: duplicate change records are not allowed", file=sys.stderr)
            return 1
        missing = expected_set - got_set
        unexpected = got_set - expected_set
        for item in sorted(missing):
            print(f"MISSING expected change: {item}")
        for item in sorted(unexpected):
            print(f"UNEXPECTED change: {item}")
        if missing or unexpected:
            return 3
        print(f"OK — exactly {len(changes)} expected change(s)")
        return 0

    if changes:
        print(f"DRIFT — {len(changes)} difference(s)")
        return 2
    print("NO DRIFT")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
