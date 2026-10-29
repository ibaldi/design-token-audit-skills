#!/usr/bin/env python3
"""Regression tests for collector assembly and exact snapshot diffs."""

from __future__ import annotations

import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCAN = ROOT / "skills" / "claude" / "token-readonly-scan"
ASSEMBLER = SCAN / "scripts" / "assemble_snapshot.py"
DIFF = SCAN / "scripts" / "diff_snapshots.py"
FIXTURE = SCAN / "fixtures" / "snapshot-plugin-api.json"


def read(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def write(path: Path, value) -> None:
    path.write_text(json.dumps(value), encoding="utf-8")


class SnapshotToolTests(unittest.TestCase):
    def test_assembler_produces_canonical_snapshot_and_observations(self) -> None:
        fixture = read(FIXTURE)
        source = fixture["source"]
        base = {
            "chunk_version": "1.0.0", "adapter_id": "figma-console-plugin-api",
            "adapter_version": "0.9.0", "captured_at": fixture["captured_at"],
            "source": {"file_key": source["file_key"], "file_name": source["file_name"]},
        }
        collections = [{key: value for key, value in item.items() if key != "provenance"} for item in fixture["collections"]]
        variables = [{key: value for key, value in item.items() if key != "provenance"} for item in fixture["variables"]]
        usages = [{key: value for key, value in item.items() if key != "provenance"} for item in fixture["usages"]]
        chunks = [
            dict(base, chunk_type="figma_token_variables", operation="inventory", complete=True, collections=collections),
            dict(base, chunk_type="figma_token_variables", operation="variables", requested_collection_ids=[collections[0]["id"]], completed_collection_ids=[collections[0]["id"]], truncated=False, variables=variables),
            dict(base, chunk_type="figma_token_properties", operation="page_inventory", complete=True, pages=[{"id": "Page:1", "name": "Foundations"}]),
            dict(base, chunk_type="figma_token_properties", operation="pages", requested_page_ids=["Page:1"], completed_page_ids=["Page:1"], pages=[{
                "id": "Page:1", "name": "Foundations", "traversal_status": "complete", "node_count": 1,
                "usages": usages, "observations": [{"family": "simple_node_fields", "property_path": "opacity", "node_id": "Node:1", "page_id": "Page:1", "state": "literal", "value": 1, "variable_id": None}], "limitations": [],
            }]),
        ]
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            paths = []
            for index, chunk in enumerate(chunks):
                path = directory / f"chunk-{index}.json"
                write(path, chunk)
                paths.append(path)
            output = directory / "snapshot.json"
            observations = directory / "observations.json"
            result = subprocess.run([sys.executable, str(ASSEMBLER), *map(str, paths), "--out", str(output), "--out-observations", str(observations)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            snapshot = read(output)
            self.assertEqual(snapshot["snapshot_type"], "figma_token_snapshot")
            self.assertEqual(snapshot["coverage"]["variables"]["status"], "complete")
            self.assertEqual(snapshot["coverage"]["pages"]["status"], "complete")
            observation_evidence = read(observations)
            self.assertEqual(len(observation_evidence["observations"]), 1)
            validated = subprocess.run([sys.executable, str(SCAN / "scripts" / "validate_snapshot.py"), str(output)], capture_output=True, text=True)
            self.assertEqual(validated.returncode, 0, validated.stderr)
            audit = read(SCAN / "fixtures" / "minimal-valid-audit.json")
            audit["property_coverage"] = observation_evidence["property_coverage"]
            audit_path = directory / "audit.json"
            write(audit_path, audit)
            audit_validated = subprocess.run([sys.executable, str(SCAN / "scripts" / "validate_audit_json.py"), str(audit_path)], capture_output=True, text=True)
            self.assertEqual(audit_validated.returncode, 0, audit_validated.stderr)

    def test_assembler_accepts_composite_values_and_referenced_usages(self) -> None:
        base = {
            "chunk_version": "1.0.0", "adapter_id": "figma-console-plugin-api", "adapter_version": "0.9.0",
            "captured_at": "2026-10-29T09:30:00Z", "source": {"file_key": "fixture-file", "file_name": "Fixture Library"},
        }
        collection = {
            "id": "Collection:1", "name": "System", "default_mode_id": "Mode:1",
            "modes": [{"id": "Mode:1", "name": "default", "position": 0}],
            "variable_ids": ["Variable:color", "Variable:opacity", "Variable:overlay"],
            "remote": False, "hidden_from_publishing": False,
        }
        def variable(variable_id, name, resolved_type, value):
            return {
                "id": variable_id, "name": name, "collection_id": "Collection:1", "resolved_type": resolved_type,
                "description": "", "scopes": [], "remote": False, "hidden_from_publishing": False, "code_syntax": {},
                "values_by_mode": {"Mode:1": value},
            }
        variables = [
            variable("Variable:color", "color/base", "COLOR", {"kind": "literal", "value": {"r": 0, "g": 0, "b": 0, "a": 1}}),
            variable("Variable:opacity", "opacity/15", "FLOAT", {"kind": "literal", "value": 15}),
            variable("Variable:overlay", "color/overlay/hover", "COLOR", {"kind": "composite", "components": {
                "color": {"kind": "alias", "target_variable_id": "Variable:color"},
                "opacity": {"kind": "alias", "target_variable_id": "Variable:opacity"},
            }}),
        ]
        remote_id = "VariableID:library/514:628"
        chunks = [
            dict(base, chunk_type="figma_token_variables", operation="inventory", complete=True, collections=[collection]),
            dict(base, chunk_type="figma_token_variables", operation="variables", requested_collection_ids=["Collection:1"], completed_collection_ids=["Collection:1"], truncated=False, variables=variables),
            dict(base, chunk_type="figma_token_properties", operation="page_inventory", complete=True, pages=[{"id": "Page:1", "name": "Playground"}]),
            dict(base, chunk_type="figma_token_properties", operation="pages", requested_page_ids=["Page:1"], completed_page_ids=["Page:1"], pages=[{
                "id": "Page:1", "name": "Playground", "traversal_status": "complete", "node_count": 2,
                "usages": [
                    {"variable_id": remote_id, "node_id": "Node:1", "page_id": "Page:1", "binding_path": "paddingTop", "binding_kind": "bound_variable"},
                    {"variable_id": "Variable:overlay", "node_id": "Node:2", "page_id": "Page:1", "binding_path": "fills[0].color", "binding_kind": "bound_variable"},
                ],
                "observations": [], "limitations": [],
            }], referenced_variables=[{"id": remote_id, "origin": "remote_library", "name": "spacing/xs", "key": "library", "resolved_type": "FLOAT", "remote": True, "collection_id": None}]),
        ]
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            paths = []
            for index, chunk in enumerate(chunks):
                path = directory / f"chunk-{index}.json"
                write(path, chunk)
                paths.append(path)
            output = directory / "snapshot.json"
            result = subprocess.run([sys.executable, str(ASSEMBLER), *map(str, paths), "--out", str(output)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            snapshot = read(output)
            self.assertEqual(snapshot["schema_version"], "1.1.0")
            self.assertEqual([item["id"] for item in snapshot["referenced_variables"]], [remote_id])
            self.assertEqual(len(snapshot["variables"]), 3)
            self.assertEqual(snapshot["coverage"]["variables"]["captured"], 3)

            chunks[3].pop("referenced_variables")
            write(paths[3], chunks[3])
            missing = subprocess.run([sys.executable, str(ASSEMBLER), *map(str, paths), "--out", str(directory / "missing.json")], capture_output=True, text=True)
            self.assertEqual(missing.returncode, 1)
            self.assertIn("variable_id: unknown variable", missing.stderr)

    def test_diff_expectation_is_value_exact(self) -> None:
        before = read(FIXTURE)
        after = copy.deepcopy(before)
        after["snapshot_id"] = "after"
        after["variables"][0]["description"] = "Changed"
        exact_change = {
            "target_kind": "variable", "target_id": after["variables"][0]["id"],
            "path": "description", "change": "changed",
            "before": before["variables"][0]["description"], "after": "Changed",
        }
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            before_path, after_path = directory / "before.json", directory / "after.json"
            expected_path, wrong_path = directory / "expected.json", directory / "wrong.json"
            write(before_path, before)
            write(after_path, after)
            write(expected_path, [exact_change])
            wrong = copy.deepcopy(exact_change)
            wrong["after"] = "Wrong"
            write(wrong_path, [wrong])
            correct = subprocess.run([sys.executable, str(DIFF), str(before_path), str(after_path), "--expect", str(expected_path)], capture_output=True, text=True)
            incorrect = subprocess.run([sys.executable, str(DIFF), str(before_path), str(after_path), "--expect", str(wrong_path)], capture_output=True, text=True)
            self.assertEqual(correct.returncode, 0, correct.stderr)
            self.assertEqual(incorrect.returncode, 3)

    def test_binding_diff_requires_and_reports_exact_usage(self) -> None:
        before = read(FIXTURE)
        after = copy.deepcopy(before)
        after["snapshot_id"] = "after-binding"
        after["usages"][0]["variable_id"] = before["variables"][0]["id"]
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            before_path, after_path = directory / "before.json", directory / "after.json"
            write(before_path, before)
            write(after_path, after)
            result = subprocess.run([sys.executable, str(DIFF), str(before_path), str(after_path), "--include-usages"], capture_output=True, text=True)
            self.assertEqual(result.returncode, 2, result.stderr)
            self.assertIn('"target_kind": "usage"', result.stdout)
            self.assertIn(before["variables"][0]["id"], result.stdout)


if __name__ == "__main__":
    unittest.main()
