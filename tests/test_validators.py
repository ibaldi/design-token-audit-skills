#!/usr/bin/env python3
"""Regression tests for valid and adversarial audit artifacts."""

from __future__ import annotations

import copy
import importlib.util
import json
import unittest
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SCAN = ROOT / "skills" / "claude" / "token-readonly-scan"
VALUE_FIX = ROOT / "skills" / "claude" / "token-value-fix"
ORCHESTRATOR = ROOT / "skills" / "claude" / "design-token-audit-orchestrator"


def load_module(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


AUDIT_VALIDATOR = load_module("audit_validator", SCAN / "scripts" / "validate_audit_json.py")
SNAPSHOT_VALIDATOR = load_module("snapshot_validator", SCAN / "scripts" / "validate_snapshot.py")
VALUE_FIX_VALIDATOR = load_module("value_fix_validator", VALUE_FIX / "scripts" / "validate_value_fix.py")
WORKFLOW_VALIDATOR = load_module("workflow_validator", ORCHESTRATOR / "scripts" / "validate_workflow_state.py")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def set_path(data: Any, path: list[Any], value: Any) -> None:
    target = data
    for segment in path[:-1]:
        target = target[segment]
    target[path[-1]] = value


class ValidatorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        fixtures = SCAN / "fixtures"
        cls.audit = read_json(fixtures / "minimal-valid-audit.json")
        cls.binding_fixture = read_json(fixtures / "binding-findings-a00-a07.json")
        cls.opacity_mismatch_fixture = read_json(fixtures / "binding-opacity-scale-mismatch.json")
        cls.value_fix = read_json(VALUE_FIX / "fixtures" / "opacity-disabled-correction.json")
        cls.workflow_state = read_json(ORCHESTRATOR / "fixtures" / "minimal-valid-workflow-state.json")
        cls.snapshots = [
            read_json(fixtures / "snapshot-plugin-api.json"),
            read_json(fixtures / "snapshot-mcp.json"),
            read_json(fixtures / "snapshot-export.json"),
        ]
        cls.negative_cases = read_json(ROOT / "tests" / "negative-validator-cases.json")

    def test_positive_audit_fixture(self) -> None:
        self.assertEqual(AUDIT_VALIDATOR.validate(self.audit), [])

    def test_demo_style_field_aliases_do_not_replace_contract_fields(self) -> None:
        artifact = copy.deepcopy(self.audit)
        replacements = {
            "source": ("file", artifact["source"]),
            "inspection": ("inspection_method", artifact["inspection"]),
            "read_only": ("changes_made", False),
            "recommended_next_pass": ("recommended_next_steps", []),
        }
        for canonical, (alias, value) in replacements.items():
            artifact.pop(canonical)
            artifact[alias] = value
        artifact.pop("started_at")
        artifact.pop("completed_at")
        artifact["scan_timestamp"] = "2026-08-12T08:00:00Z"

        errors = AUDIT_VALIDATOR.validate(artifact)
        for required in (
            "source",
            "inspection",
            "read_only",
            "recommended_next_pass",
            "started_at",
            "completed_at",
        ):
            self.assertIn(f"$.{required}: missing required field", errors)

    def test_critical_requires_demonstrated_active_consumer_impact(self) -> None:
        artifact = copy.deepcopy(self.audit)
        artifact["findings"][0]["severity"] = "critical"
        artifact["summary"]["by_severity"]["low"] = 0
        artifact["summary"]["by_severity"]["critical"] = 1
        errors = AUDIT_VALIDATOR.validate(artifact)
        self.assertIn(
            "findings[0].observed.active_consumer_impact: required for critical severity",
            errors,
        )

    def test_partial_alias_coverage_cannot_claim_complete_metric(self) -> None:
        artifact = copy.deepcopy(self.audit)
        artifact["coverage"]["aliases"]["status"] = "partial"
        errors = AUDIT_VALIDATOR.validate(artifact)
        self.assertIn(
            "derived_metrics.local_inbound_aliases.status: cannot be complete when coverage.aliases is not complete",
            errors,
        )

    def test_ready_documentation_is_structured_without_findings(self) -> None:
        artifact = copy.deepcopy(self.audit)
        artifact["documentation_readiness"] = {
            "status": "ready",
            "changelog": {
                "status": "pass",
                "node_ids": ["Node:changelog"],
                "checks": {
                    "format": {"status": "pass", "observed": "valid", "evidence": ["Node:changelog"]},
                    "sort_order": {"status": "pass", "observed": "newest_first", "evidence": ["Node:changelog"]},
                    "author_values": {"status": "pass", "observed": ["Design Systems"], "evidence": ["Node:changelog"]},
                    "type_values": {"status": "pass", "observed": ["Added"], "evidence": ["Node:changelog"]},
                    "layout_structure": {"status": "pass", "observed": {"layout_model": "auto_layout", "dynamic_content_safe": True}, "evidence": ["Node:changelog"]},
                    "visual_integrity": {"status": "pass", "observed": {"overlap_count": 0, "clipped_content_count": 0, "screenshot_evidence": ["changelog-after.png"]}, "evidence": ["Node:changelog"]},
                },
                "limitations": [],
            },
            "reference": {
                "status": "pass",
                "node_ids": ["Node:reference"],
                "checks": {
                    "location": {"status": "pass", "observed": "Foundations", "evidence": ["Node:reference"]},
                    "required_evidence": {"status": "pass", "observed": "present", "evidence": ["Node:reference"]},
                    "layout_structure": {"status": "pass", "observed": {"layout_model": "auto_layout", "dynamic_content_safe": True}, "evidence": ["Node:reference"]},
                    "visual_integrity": {"status": "pass", "observed": {"overlap_count": 0, "clipped_content_count": 0, "screenshot_evidence": ["reference-after.png"]}, "evidence": ["Node:reference"]},
                },
                "limitations": [],
            },
            "limitations": [],
        }
        self.assertEqual(AUDIT_VALIDATOR.validate(artifact), [])

    def ready_documentation_audit(self) -> Any:
        artifact = copy.deepcopy(self.audit)
        artifact["documentation_readiness"] = {
            "status": "ready",
            "changelog": {
                "status": "pass", "node_ids": ["Node:changelog"],
                "checks": {
                    "format": {"status": "pass", "observed": "valid", "evidence": ["Node:changelog"]},
                    "sort_order": {"status": "pass", "observed": "newest_first", "evidence": ["Node:changelog"]},
                    "author_values": {"status": "pass", "observed": ["Design Systems"], "evidence": ["Node:changelog"]},
                    "type_values": {"status": "pass", "observed": ["Added"], "evidence": ["Node:changelog"]},
                    "layout_structure": {"status": "pass", "observed": {"layout_model": "auto_layout", "dynamic_content_safe": True}, "evidence": ["Node:changelog"]},
                    "visual_integrity": {"status": "pass", "observed": {"overlap_count": 0, "clipped_content_count": 0, "screenshot_evidence": ["changelog-after.png"]}, "evidence": ["Node:changelog"]},
                }, "limitations": [],
            },
            "reference": {
                "status": "pass", "node_ids": ["Node:reference"],
                "checks": {
                    "location": {"status": "pass", "observed": "Foundations", "evidence": ["Node:reference"]},
                    "required_evidence": {"status": "pass", "observed": "present", "evidence": ["Node:reference"]},
                    "layout_structure": {"status": "pass", "observed": {"layout_model": "auto_layout", "dynamic_content_safe": True}, "evidence": ["Node:reference"]},
                    "visual_integrity": {"status": "pass", "observed": {"overlap_count": 0, "clipped_content_count": 0, "screenshot_evidence": ["reference-after.png"]}, "evidence": ["Node:reference"]},
                }, "limitations": [],
            },
            "limitations": [],
        }
        return artifact

    def test_documentation_layout_pass_requires_dynamic_safety(self) -> None:
        artifact = self.ready_documentation_audit()
        artifact["documentation_readiness"]["changelog"]["checks"]["layout_structure"]["observed"]["dynamic_content_safe"] = False
        errors = AUDIT_VALIDATOR.validate(artifact)
        self.assertTrue(any("dynamic_content_safe: pass requires true" in error for error in errors))

    def test_documentation_visual_pass_rejects_overlap(self) -> None:
        artifact = self.ready_documentation_audit()
        artifact["documentation_readiness"]["reference"]["checks"]["visual_integrity"]["observed"]["overlap_count"] = 1
        errors = AUDIT_VALIDATOR.validate(artifact)
        self.assertTrue(any("overlap_count: pass requires zero" in error for error in errors))

    def test_documentation_visual_pass_requires_screenshot(self) -> None:
        artifact = self.ready_documentation_audit()
        artifact["documentation_readiness"]["reference"]["checks"]["visual_integrity"]["observed"]["screenshot_evidence"] = []
        errors = AUDIT_VALIDATOR.validate(artifact)
        self.assertTrue(any("pass requires at least one screenshot" in error for error in errors))

    def binding_audit(self) -> Any:
        artifact = copy.deepcopy(self.audit)
        artifact.update(copy.deepcopy(self.binding_fixture))
        coverage = artifact["property_coverage"]
        coverage["status"] = "partial"
        coverage["source"] = {
            "adapter_id": "test-adapter", "capability_basis": "adapter_declared",
            "canonical_profile": None, "capability_evidence": "Test fixture binding-property declaration",
        }
        grouped: dict[str, dict[str, list[Any]]] = {}
        for finding in artifact["binding_findings"]:
            pattern = AUDIT_VALIDATOR.coverage_pattern_for_explicit_path(finding["property_path"])
            family_name = next(
                name for name, paths in AUDIT_VALIDATOR.PROPERTY_FAMILIES.items() if pattern in paths
            )
            grouped.setdefault(family_name, {}).setdefault(pattern, []).append(finding)
        for family_name, paths in grouped.items():
            family = coverage["families"][family_name]
            family.update({
                "support_status": "supported", "status": "complete",
                "declared_paths": sorted(paths), "properties": [], "limitations": [],
            })
            for property_path, findings in sorted(paths.items()):
                bound = sum(item["current"]["kind"] == "variable" for item in findings)
                literal = sum(item["current"]["kind"] == "literal" for item in findings)
                mixed = len(findings) - bound - literal
                family["properties"].append({
                    "property_path": property_path, "status": "complete",
                    "eligible_nodes": len(findings), "inspected_nodes": len(findings),
                    "bound_count": bound, "literal_count": literal,
                    "mixed_or_unsupported_count": mixed, "limitations": [],
                })
        return artifact

    def opacity_property_coverage(self) -> Any:
        artifact = copy.deepcopy(self.audit)
        artifact["property_coverage"]["status"] = "partial"
        family = artifact["property_coverage"]["families"]["simple_node_fields"]
        family.update({
            "support_status": "supported", "status": "complete", "declared_paths": ["opacity"],
            "properties": [{
                "property_path": "opacity", "status": "complete", "eligible_nodes": 3,
                "inspected_nodes": 3, "bound_count": 0, "literal_count": 3,
                "mixed_or_unsupported_count": 0, "limitations": [],
            }], "limitations": [],
        })
        return artifact

    def test_property_coverage_accepts_complete_opacity_traversal(self) -> None:
        self.assertEqual(AUDIT_VALIDATOR.validate(self.opacity_property_coverage()), [])

    def test_property_coverage_requires_record_for_declared_path(self) -> None:
        artifact = self.opacity_property_coverage()
        artifact["property_coverage"]["families"]["simple_node_fields"]["properties"] = []
        errors = AUDIT_VALIDATOR.validate(artifact)
        self.assertTrue(any("exactly one record per declared path" in error for error in errors))

    def test_property_coverage_counts_are_derived(self) -> None:
        artifact = self.opacity_property_coverage()
        record = artifact["property_coverage"]["families"]["simple_node_fields"]["properties"][0]
        record["literal_count"] = 2
        errors = AUDIT_VALIDATOR.validate(artifact)
        self.assertTrue(any("must equal bound + literal + mixed_or_unsupported" in error for error in errors))

    def test_official_profile_requires_complete_property_set(self) -> None:
        artifact = self.opacity_property_coverage()
        artifact["property_coverage"]["source"].update({
            "capability_basis": "official_figma_plugin_api",
            "canonical_profile": "figma_plugin_api_2026_09",
        })
        errors = AUDIT_VALIDATOR.validate(artifact)
        self.assertTrue(any("official profile requires the complete canonical set" in error for error in errors))

    def test_binding_finding_requires_matching_property_coverage(self) -> None:
        artifact = self.binding_audit()
        family = artifact["property_coverage"]["families"]["simple_node_fields"]
        if "opacity" in family["declared_paths"]:
            family["declared_paths"].remove("opacity")
            family["properties"] = [item for item in family["properties"] if item["property_path"] != "opacity"]
        else:
            family = artifact["property_coverage"]["families"]["paints"]
            removed = family["declared_paths"].pop()
            family["properties"] = [item for item in family["properties"] if item["property_path"] != removed]
        errors = AUDIT_VALIDATOR.validate(artifact)
        self.assertTrue(any("missing matching property_coverage record" in error for error in errors))

    def test_a00_a07_binding_fixture(self) -> None:
        artifact = self.binding_audit()
        self.assertEqual(AUDIT_VALIDATOR.validate(artifact), [])
        self.assertEqual(artifact["binding_summary"]["write_candidates"], 7)
        self.assertEqual(artifact["binding_findings"][0]["operation"], "no_op")

    def test_binding_no_op_cannot_be_write_candidate(self) -> None:
        artifact = self.binding_audit()
        artifact["binding_findings"][0]["status"] = "proposed"
        artifact["binding_summary"]["by_status"]["not_actionable"] = 0
        artifact["binding_summary"]["by_status"]["proposed"] = 8
        errors = AUDIT_VALIDATOR.validate(artifact)
        self.assertTrue(any("no_op cannot be a proposed write" in error for error in errors))

    def test_binding_target_type_must_match_property(self) -> None:
        artifact = self.binding_audit()
        artifact["binding_findings"][1]["expected"]["variable_type"] = "FLOAT"
        errors = AUDIT_VALIDATOR.validate(artifact)
        self.assertTrue(any("must equal property_value_type" in error for error in errors))

    def test_rebind_must_change_variable(self) -> None:
        artifact = self.binding_audit()
        finding = artifact["binding_findings"][2]
        finding["expected"]["variable_id"] = finding["current"]["variable_id"]
        finding["fingerprint"] = (
            f"binding|{finding['node_id']}|{finding['property_path']}|{finding['expected']['variable_id']}"
        )
        errors = AUDIT_VALIDATOR.validate(artifact)
        self.assertTrue(any("rebind target must differ" in error for error in errors))

    def test_binding_summary_is_derived(self) -> None:
        artifact = self.binding_audit()
        artifact["binding_summary"]["write_candidates"] = 6
        errors = AUDIT_VALIDATOR.validate(artifact)
        self.assertTrue(any("write_candidates" in error for error in errors))

    def test_proposed_binding_requires_complete_mode_coverage(self) -> None:
        artifact = self.binding_audit()
        artifact["binding_findings"][1]["expected"]["missing_mode_ids"] = ["Mode:missing"]
        errors = AUDIT_VALIDATOR.validate(artifact)
        self.assertTrue(any("requires complete relevant mode coverage" in error for error in errors))

    def test_proposed_binding_requires_compatible_scope(self) -> None:
        artifact = self.binding_audit()
        artifact["binding_findings"][1]["expected"]["scope_compatibility"] = "needs_review"
        errors = AUDIT_VALIDATOR.validate(artifact)
        self.assertTrue(any("proposed write requires compatible scope" in error for error in errors))

    def test_binding_property_path_is_explicit(self) -> None:
        artifact = self.binding_audit()
        artifact["binding_findings"][1]["property_path"] = "fill color"
        errors = AUDIT_VALIDATOR.validate(artifact)
        self.assertTrue(any("invalid explicit property path" in error for error in errors))

    def test_opacity_scale_mismatch_is_valid_only_as_hold(self) -> None:
        artifact = self.opacity_property_coverage()
        artifact.update(copy.deepcopy(self.opacity_mismatch_fixture))
        self.assertEqual(AUDIT_VALIDATOR.validate(artifact), [])
        self.assertEqual(artifact["binding_summary"]["write_candidates"], 0)

    def test_opacity_scale_mismatch_cannot_be_proposed(self) -> None:
        artifact = self.opacity_property_coverage()
        artifact.update(copy.deepcopy(self.opacity_mismatch_fixture))
        artifact["binding_findings"][0]["status"] = "proposed"
        artifact["binding_summary"]["by_status"]["held"] = 0
        artifact["binding_summary"]["by_status"]["proposed"] = 1
        artifact["binding_summary"]["write_candidates"] = 1
        errors = AUDIT_VALIDATOR.validate(artifact)
        self.assertTrue(any("requires equivalent resolved and expected values" in error for error in errors))

    def test_numeric_equivalence_must_be_derived(self) -> None:
        artifact = self.opacity_property_coverage()
        artifact.update(copy.deepcopy(self.opacity_mismatch_fixture))
        artifact["binding_findings"][0]["numeric_semantics"]["equivalence"] = "equivalent"
        errors = AUDIT_VALIDATOR.validate(artifact)
        self.assertTrue(any("expected 'mismatch' from resolved and expected values" in error for error in errors))

    def test_float_target_requires_numeric_semantics(self) -> None:
        artifact = self.binding_audit()
        artifact["binding_findings"][4].pop("numeric_semantics")
        errors = AUDIT_VALIDATOR.validate(artifact)
        self.assertTrue(any("missing required field for FLOAT variable target" in error for error in errors))

    def test_opacity_effective_values_must_be_normalized(self) -> None:
        artifact = self.opacity_property_coverage()
        artifact.update(copy.deepcopy(self.opacity_mismatch_fixture))
        numeric = artifact["binding_findings"][0]["numeric_semantics"]
        numeric["target_resolved_consumer_value"] = 45
        numeric["expected_effective_value"] = 45
        numeric["equivalence"] = "equivalent"
        errors = AUDIT_VALIDATOR.validate(artifact)
        self.assertTrue(any("opacity consumer value must be between 0 and 1" in error for error in errors))

    def test_positive_value_fix_fixture(self) -> None:
        self.assertEqual(VALUE_FIX_VALIDATOR.validate(self.value_fix), [])

    def test_value_fix_rejects_remote_variable(self) -> None:
        proposal = copy.deepcopy(self.value_fix)
        proposal["variable"]["remote"] = True
        errors = VALUE_FIX_VALIDATOR.validate(proposal)
        self.assertIn("variable.remote: proposed change requires a local variable", errors)

    def test_value_fix_requires_complete_local_binding_coverage(self) -> None:
        proposal = copy.deepcopy(self.value_fix)
        proposal["changes"][0]["consumer_impact"]["local_binding_coverage"] = "partial"
        errors = VALUE_FIX_VALIDATOR.validate(proposal)
        self.assertTrue(any("proposed change requires complete coverage" in error for error in errors))

    def test_value_fix_requires_supported_numeric_prediction(self) -> None:
        proposal = copy.deepcopy(self.value_fix)
        numeric = proposal["changes"][0]["numeric_semantics"]
        numeric["prediction_method"] = "not_observable"
        numeric["prediction_status"] = "not_observable"
        errors = VALUE_FIX_VALIDATOR.validate(proposal)
        self.assertTrue(any("proposed change requires supported prediction" in error for error in errors))

    def test_value_fix_rejects_invalid_opacity_outcome(self) -> None:
        proposal = copy.deepcopy(self.value_fix)
        proposal["changes"][0]["consumer_impact"]["consumers"][0]["expected_after_effective_value"] = 45
        errors = VALUE_FIX_VALIDATOR.validate(proposal)
        self.assertTrue(any("expected opacity must be between 0 and 1" in error for error in errors))

    def test_value_fix_rollback_must_match_current_value(self) -> None:
        proposal = copy.deepcopy(self.value_fix)
        proposal["changes"][0]["rollback"]["representation"]["value"] = 1
        errors = VALUE_FIX_VALIDATOR.validate(proposal)
        self.assertTrue(any("must exactly equal current representation" in error for error in errors))

    def test_value_fix_rejects_no_op_proposal(self) -> None:
        proposal = copy.deepcopy(self.value_fix)
        proposal["changes"][0]["proposed"] = copy.deepcopy(proposal["changes"][0]["current"])
        errors = VALUE_FIX_VALIDATOR.validate(proposal)
        self.assertTrue(any("must differ from current representation" in error for error in errors))

    def test_value_fix_consumer_count_is_derived(self) -> None:
        proposal = copy.deepcopy(self.value_fix)
        proposal["changes"][0]["consumer_impact"]["local_bound_node_count"] = 2
        errors = VALUE_FIX_VALIDATOR.validate(proposal)
        self.assertTrue(any("must equal unique consumer node count" in error for error in errors))

    def test_value_fix_external_limitations_require_high_risk(self) -> None:
        proposal = copy.deepcopy(self.value_fix)
        proposal["changes"][0]["risk"] = "medium"
        proposal["summary"]["risk"] = "medium"
        proposal["changes"][0]["limitations"] = []
        errors = VALUE_FIX_VALIDATOR.validate(proposal)
        self.assertTrue(any("requires high risk and a limitation" in error for error in errors))

    def test_value_fix_numeric_values_match_representations(self) -> None:
        proposal = copy.deepcopy(self.value_fix)
        proposal["changes"][0]["numeric_semantics"]["proposed_stored_value"] = 44
        errors = VALUE_FIX_VALIDATOR.validate(proposal)
        self.assertTrue(any("must equal proposed literal" in error for error in errors))

    def test_positive_snapshot_fixtures(self) -> None:
        for snapshot in self.snapshots:
            with self.subTest(adapter=snapshot["adapter"]["adapter_id"]):
                self.assertEqual(SNAPSHOT_VALIDATOR.validate(snapshot), [])

    def test_adapter_snapshots_are_semantically_equivalent(self) -> None:
        baseline = SNAPSHOT_VALIDATOR.semantic_projection(self.snapshots[0])
        for snapshot in self.snapshots[1:]:
            self.assertEqual(SNAPSHOT_VALIDATOR.semantic_projection(snapshot), baseline)

    def test_negative_audit_cases(self) -> None:
        for case in self.negative_cases["audit_cases"]:
            with self.subTest(case=case["name"]):
                artifact = copy.deepcopy(self.audit)
                set_path(artifact, case["path"], case["value"])
                errors = AUDIT_VALIDATOR.validate(artifact)
                self.assertTrue(
                    any(case["expected_error"] in error for error in errors),
                    f"Expected {case['expected_error']!r}; received {errors!r}",
                )

    def test_negative_snapshot_cases(self) -> None:
        for case in self.negative_cases["snapshot_cases"]:
            with self.subTest(case=case["name"]):
                artifact = copy.deepcopy(self.snapshots[0])
                set_path(artifact, case["path"], case["value"])
                errors = SNAPSHOT_VALIDATOR.validate(artifact)
                self.assertTrue(
                    any(case["expected_error"] in error for error in errors),
                    f"Expected {case['expected_error']!r}; received {errors!r}",
                )

    def test_mode_ids_are_scoped_to_their_collection(self) -> None:
        artifact = copy.deepcopy(self.snapshots[0])
        artifact["collections"].append({
            "id": "Collection:secondary",
            "name": "Secondary",
            "default_mode_id": "Mode:light",
            "modes": [
                {"id": "Mode:light", "name": "Default", "position": 0},
                {"id": "Mode:dark", "name": "Contrast", "position": 1},
            ],
            "variable_ids": [],
            "remote": False,
            "hidden_from_publishing": False,
            "provenance": {"adapter_id": "figma-plugin-api", "source_path": "local collections"},
        })
        artifact["coverage"]["collections"]["captured"] = 2
        self.assertEqual(SNAPSHOT_VALIDATOR.validate(artifact), [])
        projection = SNAPSHOT_VALIDATOR.semantic_projection(artifact)
        semantic = next(item for item in projection["collections"] if item["name"] == "Semantic")
        danger = next(item for item in projection["variables"] if item["name"] == "Semantic/action/danger")
        self.assertEqual(semantic["default_mode"], "Light")
        self.assertEqual(set(danger["values_by_mode"]), {"Light", "Dark"})

    def test_ambiguous_names_block_semantic_comparison_only(self) -> None:
        artifact = copy.deepcopy(self.snapshots[0])
        duplicate = copy.deepcopy(artifact["collections"][0])
        duplicate["id"] = "Collection:duplicate"
        duplicate["variable_ids"] = []
        artifact["collections"].append(duplicate)
        artifact["coverage"]["collections"]["captured"] = 2
        self.assertEqual(SNAPSHOT_VALIDATOR.validate(artifact), [])
        with self.assertRaisesRegex(ValueError, "unique collection names"):
            SNAPSHOT_VALIDATOR.semantic_projection(artifact)

    def test_positive_workflow_state_fixture(self) -> None:
        self.assertEqual(WORKFLOW_VALIDATOR.validate(self.workflow_state), [])

    def test_workflow_waiting_state_requires_exact_approval(self) -> None:
        state = copy.deepcopy(self.workflow_state)
        state["pending_approval"] = None
        errors = WORKFLOW_VALIDATOR.validate(state)
        self.assertIn("$.pending_approval: required when status is waiting_for_approval", errors)

    def test_workflow_phase_and_current_step_must_agree(self) -> None:
        state = copy.deepcopy(self.workflow_state)
        state["phase"] = "P2"
        errors = WORKFLOW_VALIDATOR.validate(state)
        self.assertIn("$.current_step: must belong to $.phase", errors)

    def test_workflow_phase_three_requires_positive_iteration(self) -> None:
        state = copy.deepcopy(self.workflow_state)
        state["pass_iteration"] = 0
        errors = WORKFLOW_VALIDATOR.validate(state)
        self.assertIn("$.pass_iteration: must be positive in P3", errors)

    def test_workflow_phase_two_requires_both_phase_one_assessments(self) -> None:
        state = copy.deepcopy(self.workflow_state)
        state["phase1_assessments"]["semantic_gap_finding"] = None
        errors = WORKFLOW_VALIDATOR.validate(state)
        self.assertIn("$.phase1_assessments: both required assessments must have evidence before Phase 2", errors)

    def test_workflow_p1_4_cannot_be_skipped(self) -> None:
        state = copy.deepcopy(self.workflow_state)
        state["completed_steps"].remove("P1.4")
        state["skipped_steps"].append("P1.4")
        errors = WORKFLOW_VALIDATOR.validate(state)
        self.assertIn("$.skipped_steps: P1.4 cannot be skipped", errors)

    def test_inapplicable_assessment_requires_evidence_reason(self) -> None:
        state = copy.deepcopy(self.workflow_state)
        state["phase1_assessments"]["semantic_gap_finding"] = {
            "status": "inapplicable", "artifact_id": "gap-001", "coverage": "not_applicable", "reason": None,
        }
        errors = WORKFLOW_VALIDATOR.validate(state)
        self.assertIn("$.phase1_assessments.semantic_gap_finding.reason: required for inapplicable assessment", errors)

    def test_not_requested_is_not_valid_inapplicability(self) -> None:
        state = copy.deepcopy(self.workflow_state)
        state["phase1_assessments"]["semantic_gap_finding"] = {
            "status": "inapplicable", "artifact_id": "gap-001", "coverage": "not_applicable", "reason": "Not requested by user",
        }
        errors = WORKFLOW_VALIDATOR.validate(state)
        self.assertIn(
            "$.phase1_assessments.semantic_gap_finding.reason: user request, time, or effort is not a valid inapplicability reason",
            errors,
        )

    def test_workflow_cannot_complete_current_step_in_advance(self) -> None:
        state = copy.deepcopy(self.workflow_state)
        state["completed_steps"].append("P3.3")
        errors = WORKFLOW_VALIDATOR.validate(state)
        self.assertIn("$.current_step: cannot already be completed or skipped", errors)

    def test_workflow_blocked_state_requires_blocker(self) -> None:
        state = copy.deepcopy(self.workflow_state)
        state["status"] = "blocked"
        state["pending_approval"] = None
        errors = WORKFLOW_VALIDATOR.validate(state)
        self.assertIn("$.blockers: at least one blocker is required when status is blocked", errors)

    def test_complete_workflow_accounts_for_every_step(self) -> None:
        state = copy.deepcopy(self.workflow_state)
        state.update({"phase": "P4", "current_step": None, "status": "complete", "pending_approval": None})
        errors = WORKFLOW_VALIDATOR.validate(state)
        self.assertIn("$: complete workflow must account for every canonical step", errors)


if __name__ == "__main__":
    unittest.main()
