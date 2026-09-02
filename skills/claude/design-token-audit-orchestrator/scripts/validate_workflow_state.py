#!/usr/bin/env python3
"""Validate design-token audit workflow navigation state."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


STEPS = tuple(
    [f"P1.{index}" for index in range(1, 5)]
    + [f"P2.{index}" for index in range(1, 5)]
    + [f"P3.{index}" for index in range(1, 8)]
    + [f"P4.{index}" for index in range(1, 4)]
)
STEP_SET = set(STEPS)
STATUSES = {"not_started", "in_progress", "waiting_for_approval", "blocked", "failed", "complete"}
OPEN_ITEM_KEYS = {"documentation_fixes", "scope_fixes", "token_creations", "value_fixes", "binding_fixes", "holds"}
ASSESSMENT_KEYS = {"scope_validation", "semantic_gap_finding"}
ASSESSMENT_STATUSES = {"completed", "partial", "not_observable", "inapplicable"}
ASSESSMENT_COVERAGE = {"complete", "partial", "not_observable", "not_applicable"}
INVALID_SKIP_REASONS = ("not requested", "not mentioned", "time constraint", "time constraints", "too much effort")


def nonempty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def valid_timestamp(value: Any) -> bool:
    if not nonempty_string(value):
        return False
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return False
    return True


def validate(data: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(data, dict):
        return ["$: must be an object"]

    required = {
        "workflow_schema_version", "session_id", "updated_at", "source_audit_id", "phase",
        "current_step", "pass_iteration", "status", "completed_steps", "skipped_steps", "current_action",
        "next_action", "pending_approval", "phase1_assessments", "open_items", "blockers", "last_verified_at",
    }
    for key in sorted(required - data.keys()):
        errors.append(f"$.{key}: missing required field")

    if data.get("workflow_schema_version") != "1.1.0":
        errors.append("$.workflow_schema_version: must equal '1.1.0'")
    if not nonempty_string(data.get("session_id")):
        errors.append("$.session_id: must be a non-empty string")
    if not valid_timestamp(data.get("updated_at")):
        errors.append("$.updated_at: must be an ISO 8601 timestamp")
    if data.get("source_audit_id") is not None and not nonempty_string(data.get("source_audit_id")):
        errors.append("$.source_audit_id: must be null or a non-empty string")
    if data.get("last_verified_at") is not None and not valid_timestamp(data.get("last_verified_at")):
        errors.append("$.last_verified_at: must be null or an ISO 8601 timestamp")

    phase = data.get("phase")
    current_step = data.get("current_step")
    status = data.get("status")
    if phase not in {"P1", "P2", "P3", "P4"}:
        errors.append("$.phase: must be P1, P2, P3, or P4")
    if current_step is not None and current_step not in STEP_SET:
        errors.append("$.current_step: must be null or a canonical workflow step")
    elif current_step is not None and phase in {"P1", "P2", "P3", "P4"} and not current_step.startswith(f"{phase}."):
        errors.append("$.current_step: must belong to $.phase")
    if status not in STATUSES:
        errors.append(f"$.status: must be one of {sorted(STATUSES)}")
    pass_iteration = data.get("pass_iteration")
    if isinstance(pass_iteration, bool) or not isinstance(pass_iteration, int) or pass_iteration < 0:
        errors.append("$.pass_iteration: must be a non-negative integer")
    elif phase == "P3" and pass_iteration < 1:
        errors.append("$.pass_iteration: must be positive in P3")
    elif phase in {"P1", "P2"} and pass_iteration != 0:
        errors.append("$.pass_iteration: must be 0 before P3")

    step_lists: dict[str, list[str]] = {}
    for key in ("completed_steps", "skipped_steps"):
        value = data.get(key)
        if not isinstance(value, list):
            errors.append(f"$.{key}: must be an array")
            step_lists[key] = []
            continue
        if len(value) != len(set(value)):
            errors.append(f"$.{key}: entries must be unique")
        invalid = [step for step in value if step not in STEP_SET]
        if invalid:
            errors.append(f"$.{key}: contains invalid steps {invalid}")
        step_lists[key] = value
    completed = set(step_lists.get("completed_steps", []))
    skipped = set(step_lists.get("skipped_steps", []))
    if completed & skipped:
        errors.append("$.completed_steps and $.skipped_steps: must be disjoint")
    if current_step in completed or current_step in skipped:
        errors.append("$.current_step: cannot already be completed or skipped")
    if "P1.4" in skipped:
        errors.append("$.skipped_steps: P1.4 cannot be skipped")

    assessments = data.get("phase1_assessments")
    valid_assessment_count = 0
    if not isinstance(assessments, dict):
        errors.append("$.phase1_assessments: must be an object")
    else:
        missing = ASSESSMENT_KEYS - assessments.keys()
        extra = assessments.keys() - ASSESSMENT_KEYS
        if missing:
            errors.append(f"$.phase1_assessments: missing keys {sorted(missing)}")
        if extra:
            errors.append(f"$.phase1_assessments: unsupported keys {sorted(extra)}")
        for key in sorted(ASSESSMENT_KEYS & assessments.keys()):
            record = assessments[key]
            path = f"$.phase1_assessments.{key}"
            if record is None:
                continue
            if not isinstance(record, dict):
                errors.append(f"{path}: must be null or an object")
                continue
            status_value = record.get("status")
            coverage = record.get("coverage")
            artifact_id = record.get("artifact_id")
            reason = record.get("reason")
            if status_value not in ASSESSMENT_STATUSES:
                errors.append(f"{path}.status: must be one of {sorted(ASSESSMENT_STATUSES)}")
            if coverage not in ASSESSMENT_COVERAGE:
                errors.append(f"{path}.coverage: must be one of {sorted(ASSESSMENT_COVERAGE)}")
            if not nonempty_string(artifact_id):
                errors.append(f"{path}.artifact_id: must be a non-empty string")
            if reason is not None and not nonempty_string(reason):
                errors.append(f"{path}.reason: must be null or a non-empty string")
            if status_value == "completed" and coverage != "complete":
                errors.append(f"{path}.coverage: completed assessment requires complete coverage")
            if status_value == "partial" and coverage != "partial":
                errors.append(f"{path}.coverage: partial assessment requires partial coverage")
            if status_value == "not_observable" and coverage != "not_observable":
                errors.append(f"{path}.coverage: not_observable assessment requires matching coverage")
            if status_value == "inapplicable" and coverage != "not_applicable":
                errors.append(f"{path}.coverage: inapplicable assessment requires not_applicable coverage")
            if status_value in {"partial", "not_observable", "inapplicable"} and not nonempty_string(reason):
                errors.append(f"{path}.reason: required for {status_value} assessment")
            if nonempty_string(reason) and any(term in reason.lower() for term in INVALID_SKIP_REASONS):
                errors.append(f"{path}.reason: user request, time, or effort is not a valid inapplicability reason")
            expected_coverage = {
                "completed": "complete",
                "partial": "partial",
                "not_observable": "not_observable",
                "inapplicable": "not_applicable",
            }.get(status_value)
            invalid_reason = nonempty_string(reason) and any(term in reason.lower() for term in INVALID_SKIP_REASONS)
            if (
                expected_coverage == coverage
                and nonempty_string(artifact_id)
                and (status_value == "completed" or nonempty_string(reason))
                and not invalid_reason
            ):
                valid_assessment_count += 1

    phase_one_complete = "P1.4" in completed or phase in {"P2", "P3", "P4"}
    if phase_one_complete and valid_assessment_count != len(ASSESSMENT_KEYS):
        errors.append("$.phase1_assessments: both required assessments must have evidence before Phase 2")

    for key in ("current_action", "next_action"):
        if not nonempty_string(data.get(key)):
            errors.append(f"$.{key}: must be a non-empty string")

    pending = data.get("pending_approval")
    if status == "waiting_for_approval":
        if not isinstance(pending, dict):
            errors.append("$.pending_approval: required when status is waiting_for_approval")
        else:
            if not nonempty_string(pending.get("pass_id")):
                errors.append("$.pending_approval.pass_id: must be a non-empty string")
            commands = pending.get("accepted_commands")
            if not isinstance(commands, list) or not commands or any(not nonempty_string(item) for item in commands):
                errors.append("$.pending_approval.accepted_commands: must be a non-empty string array")
    elif pending is not None:
        errors.append("$.pending_approval: must be null unless status is waiting_for_approval")

    open_items = data.get("open_items")
    if not isinstance(open_items, dict):
        errors.append("$.open_items: must be an object")
    else:
        missing = OPEN_ITEM_KEYS - open_items.keys()
        extra = open_items.keys() - OPEN_ITEM_KEYS
        if missing:
            errors.append(f"$.open_items: missing keys {sorted(missing)}")
        if extra:
            errors.append(f"$.open_items: unsupported keys {sorted(extra)}")
        for key, value in open_items.items():
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                errors.append(f"$.open_items.{key}: must be a non-negative integer")

    blockers = data.get("blockers")
    if not isinstance(blockers, list) or any(not nonempty_string(item) for item in blockers):
        errors.append("$.blockers: must be an array of non-empty strings")
        blockers = []
    if status in {"blocked", "failed"} and not blockers:
        errors.append(f"$.blockers: at least one blocker is required when status is {status}")

    if status == "complete":
        if phase != "P4":
            errors.append("$.phase: complete workflow must be in P4")
        if current_step is not None:
            errors.append("$.current_step: complete workflow must use null")
        if completed | skipped != STEP_SET:
            errors.append("$: complete workflow must account for every canonical step")
    elif current_step is None:
        errors.append("$.current_step: may be null only when status is complete")

    return errors


def self_test() -> int:
    sample = {
        "workflow_schema_version": "1.1.0", "session_id": "self-test",
        "updated_at": "2026-09-02T20:30:00Z", "source_audit_id": "audit-004",
        "phase": "P3", "current_step": "P3.3", "pass_iteration": 1, "status": "waiting_for_approval",
        "completed_steps": ["P1.1", "P1.2", "P1.3", "P1.4", "P2.1", "P2.2", "P2.3", "P2.4", "P3.1", "P3.2"],
        "skipped_steps": [], "current_action": "Approve B03", "next_action": "Apply B03",
        "pending_approval": {"pass_id": "B03", "accepted_commands": ["Go B03", "Hold B03"]},
        "phase1_assessments": {
            "scope_validation": {"status": "completed", "artifact_id": "scope-001", "coverage": "complete", "reason": None},
            "semantic_gap_finding": {"status": "partial", "artifact_id": "gap-001", "coverage": "partial", "reason": "External consumers were not observable"},
        },
        "open_items": {"documentation_fixes": 0, "scope_fixes": 0, "token_creations": 0, "value_fixes": 1, "binding_fixes": 2, "holds": 2},
        "blockers": [], "last_verified_at": "2026-09-02T20:10:00Z",
    }
    errors = validate(sample)
    if errors:
        print("self-test failed: " + "; ".join(errors), file=sys.stderr)
        return 1
    print("self-test passed")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", nargs="?", type=Path)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        return self_test()
    if args.path is None:
        parser.error("path is required unless --self-test is used")
    try:
        data = json.loads(args.path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"invalid workflow state: {exc}", file=sys.stderr)
        return 2
    errors = validate(data)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print("workflow state is valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
