#!/usr/bin/env python3
"""Check Claude skill metadata, versions, references, tests, and ZIP layout."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / "skills" / "claude"
DESCRIPTION_LIMIT = 200
VERSION_RE = re.compile(r"\d+\.\d+\.\d+")
FRONTMATTER_RE = re.compile(r"\A---\n(?P<body>.*?)\n---\n", re.DOTALL)
LINK_RE = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
ORCHESTRATOR_SHARED_FILES = (
    "references/audit-output-contract.md",
    "references/canonical-figma-token-model.md",
    "references/figma-adapter-contract.md",
    "references/figma-adapter-mappings.md",
    "references/figma-execution-contract.md",
    "references/property-traversal-contract.md",
    "scripts/validate_audit_json.py",
    "scripts/validate_snapshot.py",
)
DOCUMENTATION_WRITE_SKILLS = (
    "token-creation-proposal",
    "token-scope-validation",
    "token-binding-fix",
    "token-value-fix",
)


def parse_frontmatter(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8")
    match = FRONTMATTER_RE.match(text)
    if not match:
        raise ValueError("missing YAML frontmatter")
    result: dict[str, str] = {}
    for line in match.group("body").splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        result[key.strip()] = value.strip().strip("'\"")
    return result


def check_skill(path: Path, version: str, errors: list[str]) -> None:
    skill_file = path / "SKILL.md"
    try:
        metadata = parse_frontmatter(skill_file)
    except (OSError, ValueError) as exc:
        errors.append(f"{skill_file}: {exc}")
        return
    if metadata.get("name") != path.name:
        errors.append(f"{skill_file}: name must match folder {path.name!r}")
    description = metadata.get("description", "")
    if not description:
        errors.append(f"{skill_file}: description is required")
    elif len(description) > DESCRIPTION_LIMIT:
        errors.append(f"{skill_file}: description has {len(description)} characters; maximum is {DESCRIPTION_LIMIT}")
    text = skill_file.read_text(encoding="utf-8")
    version_match = re.search(r"^Version: (\d+\.\d+\.\d+)$", text, re.MULTILINE)
    if not version_match or version_match.group(1) != version:
        errors.append(f"{skill_file}: visible Version must be {version}")
    if re.search(r"\b(?:TODO|TBD|PLACEHOLDER)\b", text, re.IGNORECASE):
        errors.append(f"{skill_file}: contains unfinished placeholder text")
    for target in LINK_RE.findall(text):
        if target.startswith(("http://", "https://", "#")):
            continue
        resolved = (skill_file.parent / target).resolve()
        if not resolved.exists():
            errors.append(f"{skill_file}: missing referenced file {target!r}")


def check_versions(version: str, errors: list[str]) -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    if f"Current skill package version: `{version}`" not in readme:
        errors.append(f"README.md: current package version must be {version}")
    changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    if not re.search(rf"^## {re.escape(version)} - \d{{4}}-\d{{2}}-\d{{2}}$", changelog, re.MULTILINE):
        errors.append(f"CHANGELOG.md: missing dated {version} release heading")
    prompts = (ROOT / "tests" / "manual-claude-test-prompts.md").read_text(encoding="utf-8")
    if f"should be `{version}`" not in prompts or f"names `{version}`" not in prompts:
        errors.append(f"manual test prompts: version expectations must be {version}")


def check_local_links(errors: list[str]) -> None:
    for markdown in ROOT.rglob("*.md"):
        if "dist" in markdown.parts:
            continue
        text = markdown.read_text(encoding="utf-8")
        for target in LINK_RE.findall(text):
            if target.startswith(("http://", "https://", "#", "mailto:")):
                continue
            clean_target = target.split("#", 1)[0]
            if clean_target and not (markdown.parent / clean_target).resolve().exists():
                errors.append(f"{markdown.relative_to(ROOT)}: missing referenced file {target!r}")


def read_package_version() -> str | None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    match = re.search(r"Current skill package version: `(\d+\.\d+\.\d+)`", readme)
    return match.group(1) if match else None


def check_trigger_evals(errors: list[str]) -> None:
    path = ROOT / "tests" / "skill-trigger-evals.json"
    try:
        evals = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"{path}: {exc}")
        return
    if not isinstance(evals, list) or len(evals) < 20:
        errors.append(f"{path}: expected at least 20 trigger evals")
        return
    positives = sum(item.get("should_trigger") is True for item in evals if isinstance(item, dict))
    negatives = sum(item.get("should_trigger") is False for item in evals if isinstance(item, dict))
    if positives < 8 or negatives < 8:
        errors.append(f"{path}: expected at least 8 positive and 8 negative evals")
    for index, item in enumerate(evals):
        if not isinstance(item, dict) or not isinstance(item.get("query"), str) or not item["query"].strip():
            errors.append(f"{path}[{index}]: query must be a non-empty string")


def check_generated_files(errors: list[str]) -> None:
    for path in ROOT.rglob("*"):
        if "dist" in path.parts:
            continue
        if path.name == "__pycache__" or path.name == ".DS_Store" or path.suffix == ".pyc":
            errors.append(f"{path.relative_to(ROOT)}: generated file must not enter a package")


def check_orchestrator_bundle(errors: list[str]) -> None:
    canonical = SKILLS / "token-readonly-scan"
    bundled = SKILLS / "design-token-audit-orchestrator"
    for relative in ORCHESTRATOR_SHARED_FILES:
        canonical_path = canonical / relative
        bundled_path = bundled / relative
        if not bundled_path.exists():
            errors.append(f"{bundled_path.relative_to(ROOT)}: required bundled Phase 1 resource is missing")
        elif bundled_path.read_bytes() != canonical_path.read_bytes():
            errors.append(f"{bundled_path.relative_to(ROOT)}: bundled copy differs from token-readonly-scan/{relative}")


def check_binding_release(errors: list[str]) -> None:
    binding = SKILLS / "token-binding-fix"
    evidence = binding / "references" / "binding-evidence-contract.md"
    relational = binding / "references" / "relational-safety-contract.md"
    fixture_path = SKILLS / "token-readonly-scan" / "fixtures" / "binding-findings-a00-a07.json"
    if not binding.is_dir() or not evidence.is_file():
        errors.append("token-binding-fix: skill or binding evidence contract is missing")
    if not relational.is_file():
        errors.append("token-binding-fix: relational safety contract is missing")
    else:
        relational_text = relational.read_text(encoding="utf-8")
        for phrase in (
            "Do not limit discovery to direct children.",
            "normal text: `4.5:1`",
            "meaningful graphical objects and UI indicators: `3:1`",
            "Do not present a tuple as ordinarily approval-ready when it creates a new known accessibility failure.",
            "Do not generate speculative coupling warnings",
        ):
            if phrase not in relational_text:
                errors.append(f"token-binding-fix relational safety: missing invariant {phrase!r}")
    try:
        fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"{fixture_path.relative_to(ROOT)}: {exc}")
        return
    findings = fixture.get("binding_findings")
    summary = fixture.get("binding_summary")
    if not isinstance(findings, list) or len(findings) != 8:
        errors.append("binding fixture: expected exactly eight A00-A07 findings")
    if not isinstance(summary, dict) or summary.get("write_candidates") != 7:
        errors.append("binding fixture: expected exactly seven write candidates")

    mismatch_path = SKILLS / "token-readonly-scan" / "fixtures" / "binding-opacity-scale-mismatch.json"
    try:
        mismatch = json.loads(mismatch_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"{mismatch_path.relative_to(ROOT)}: {exc}")
        return
    mismatch_findings = mismatch.get("binding_findings")
    mismatch_summary = mismatch.get("binding_summary")
    numeric = mismatch_findings[0].get("numeric_semantics") if isinstance(mismatch_findings, list) and mismatch_findings else None
    if not isinstance(numeric, dict) or numeric.get("equivalence") != "mismatch":
        errors.append("opacity mismatch fixture: expected explicit numeric mismatch")
    if not isinstance(mismatch_summary, dict) or mismatch_summary.get("write_candidates") != 0:
        errors.append("opacity mismatch fixture: mismatch must not be a write candidate")


def check_value_release(errors: list[str]) -> None:
    value_skill = SKILLS / "token-value-fix"
    required_paths = (
        value_skill / "SKILL.md",
        value_skill / "references" / "value-evidence-contract.md",
        value_skill / "scripts" / "validate_value_fix.py",
        value_skill / "fixtures" / "opacity-disabled-correction.json",
    )
    for path in required_paths:
        if not path.is_file():
            errors.append(f"{path.relative_to(ROOT)}: required token-value-fix resource is missing")
    fixture_path = required_paths[-1]
    if not fixture_path.is_file():
        return
    try:
        fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        errors.append(f"{fixture_path.relative_to(ROOT)}: {exc}")
        return
    if fixture.get("contract_version") != "1.0.0":
        errors.append("token-value-fix fixture: expected contract version 1.0.0")
    if fixture.get("summary", {}).get("rollback_tuples") != len(fixture.get("changes", [])):
        errors.append("token-value-fix fixture: every change requires a rollback tuple")


def check_documentation_layout_release(errors: list[str]) -> None:
    fixture_path = SKILLS / "token-readonly-scan" / "fixtures" / "minimal-valid-audit.json"
    try:
        fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"{fixture_path.relative_to(ROOT)}: {exc}")
        return
    if fixture.get("schema_version") != "1.5.0":
        errors.append("minimal audit fixture: current release requires schema 1.5.0")
    readiness = fixture.get("documentation_readiness", {})
    for component in ("changelog", "reference"):
        checks = readiness.get(component, {}).get("checks", {})
        for required in ("layout_structure", "visual_integrity"):
            if required not in checks:
                errors.append(f"minimal audit fixture: documentation_readiness.{component}.checks.{required} is missing")

    safety_phrase = "never position a repeating row or card solely by adding an assumed fixed offset"
    recovery_reference = "references/documentation-structural-write-safety.md"
    canonical_recovery = SKILLS / "design-token-audit-orchestrator" / recovery_reference
    if not canonical_recovery.is_file():
        errors.append("design-token-audit-orchestrator: documentation structural-write safety contract is missing")
        canonical_bytes = None
    else:
        canonical_bytes = canonical_recovery.read_bytes()
    for skill_name in DOCUMENTATION_WRITE_SKILLS:
        text = (SKILLS / skill_name / "SKILL.md").read_text(encoding="utf-8").lower()
        if safety_phrase not in text:
            errors.append(f"skills/claude/{skill_name}/SKILL.md: missing documentation layout safety invariant")
        if recovery_reference.lower() not in text:
            errors.append(f"skills/claude/{skill_name}/SKILL.md: missing structural-write safety reference")
        recovery_path = SKILLS / skill_name / recovery_reference
        if not recovery_path.is_file():
            errors.append(f"skills/claude/{skill_name}/{recovery_reference}: missing")
        elif canonical_bytes is not None and recovery_path.read_bytes() != canonical_bytes:
            errors.append(f"skills/claude/{skill_name}/{recovery_reference}: differs from orchestrator contract")

    if canonical_bytes is not None:
        recovery_text = canonical_bytes.decode("utf-8")
        for phrase in (
            "Names are descriptive evidence only and must never establish ownership.",
            "figma.commitUndo()",
            "figma.triggerUndo()",
            "Only then set child-only values",
            "Do not describe a multi-mutation script as atomic",
            "Remove a cleanup subtree only when its root and every descendant were created by the current attempt.",
        ):
            if phrase not in recovery_text:
                errors.append(f"documentation structural-write safety: missing invariant {phrase!r}")


def check_process_navigator_release(errors: list[str]) -> None:
    orchestrator = SKILLS / "design-token-audit-orchestrator"
    required_paths = (
        orchestrator / "references" / "workflow-state-contract.md",
        orchestrator / "scripts" / "validate_workflow_state.py",
        orchestrator / "fixtures" / "minimal-valid-workflow-state.json",
    )
    for path in required_paths:
        if not path.is_file():
            errors.append(f"{path.relative_to(ROOT)}: required process navigator resource is missing")

    fixture_path = required_paths[-1]
    if fixture_path.is_file():
        try:
            fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            errors.append(f"{fixture_path.relative_to(ROOT)}: {exc}")
        else:
            if fixture.get("workflow_schema_version") != "1.1.0":
                errors.append("workflow state fixture: expected contract version 1.1.0")
            if fixture.get("status") == "waiting_for_approval" and not fixture.get("pending_approval"):
                errors.append("workflow state fixture: waiting state requires pending approval")
            assessments = fixture.get("phase1_assessments", {})
            if set(assessments) != {"scope_validation", "semantic_gap_finding"}:
                errors.append("workflow state fixture: both Phase-1 assessments are required")

    orchestrator_text = (orchestrator / "SKILL.md").read_text(encoding="utf-8")
    for phrase in (
        "## Process Navigator",
        "show exactly one recommended next action",
        "STATE RECONCILIATION REQUIRED",
        "Restored navigation never restores or broadens a previous write approval",
        "`P1.4` cannot be skipped",
        "Do not begin Phase 2 until `P1.4` has run",
    ):
        if phrase.lower() not in orchestrator_text.lower():
            errors.append(f"design-token-audit-orchestrator/SKILL.md: missing process invariant {phrase!r}")

    for skill in SKILLS.iterdir():
        if not skill.is_dir() or skill.name == "design-token-audit-orchestrator":
            continue
        text = (skill / "SKILL.md").read_text(encoding="utf-8")
        if "## Orchestrator Handoff" not in text or "must not advance the global dashboard itself" not in text:
            errors.append(f"skills/claude/{skill.name}/SKILL.md: missing orchestrator handoff boundary")


def check_property_coverage_release(errors: list[str]) -> None:
    scan = SKILLS / "token-readonly-scan"
    contract = scan / "references" / "property-traversal-contract.md"
    fixture_path = scan / "fixtures" / "minimal-valid-audit.json"
    if not contract.is_file():
        errors.append("token-readonly-scan: property traversal contract is missing")
    try:
        fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"{fixture_path.relative_to(ROOT)}: {exc}")
        return
    coverage = fixture.get("property_coverage", {})
    if coverage.get("contract_version") != "1.0.0":
        errors.append("minimal audit fixture: property coverage contract must be 1.0.0")
    expected_families = {
        "simple_node_fields", "paints", "effects", "layout_grids", "typography", "component_properties",
    }
    if set(coverage.get("families", {})) != expected_families:
        errors.append("minimal audit fixture: all six property coverage families are required")
    exclusions = set(coverage.get("excluded_non_bindable_properties", []))
    if not {"rotation", "blendMode", "layoutSizingHorizontal", "layoutSizingVertical"} <= exclusions:
        errors.append("minimal audit fixture: required non-bindable exclusions are missing")


def check_safety_invariants(errors: list[str]) -> None:
    required = {
        SKILLS / "design-token-audit-orchestrator" / "SKILL.md": (
            "the gate is closed",
            "Manual review does not replace this gate.",
            "Never offer or perform an unsupported write as a manual one-off",
            "do not describe unsupported observations as eligible for a fix pass in this release",
            "Produce a successor audit with a new audit ID and timestamps",
            "every node to be created or changed with exact name, node type, parent/location, and total count",
            "Never place a new repeating row or card solely by incrementing a previous element's coordinate",
            "verify zero overlap and clipped content",
        ),
        SKILLS / "token-readonly-scan" / "SKILL.md": (
            "label the artifact as an **unvalidated draft**",
            "set the scan status to `blocked`",
            "Manual review does not replace this gate.",
            "Require screenshot evidence of the complete affected area",
            "including literals with no existing-variable match",
        ),
        SKILLS / "token-semantic-gap-finding" / "SKILL.md": (
            "## Mandatory Hardcoded-value Sweep",
            "repeated equal literals alone do not prove a system-level semantic gap",
            "do not present it as a write-ready confirmed gap",
            "One coincidental pair, a `FRAME_FILL` or `SHAPE_FILL` scope, or a token name containing `bg` is not sufficient by itself.",
            "rule_id: missing-semantic-foreground-pairing",
        ),
        SKILLS / "token-scope-validation" / "SKILL.md": (
            "An empty scope array is not interchangeable with explicit `ALL_SCOPES`",
        ),
        SKILLS / "token-creation-proposal" / "SKILL.md": (
            "Never combine token creation with node-binding changes",
            "route it to a separate `token-value-fix` pass",
        ),
        SKILLS / "token-binding-fix" / "SKILL.md": (
            "variable.resolveForConsumer(node)",
            "consumer resolution is unavailable",
            "Changing an existing variable value is outside this skill",
            "Do not limit inspection to direct children.",
            "creates a new known accessibility failure",
            "Approval for the background tuple never authorizes changing a foreground property.",
        ),
        SKILLS / "token-readonly-scan" / "scripts" / "validate_audit_json.py": (
            "proposed FLOAT binding requires observable consumer resolution",
            "proposed FLOAT binding requires equivalent resolved and expected values",
            "opacity consumer value must be between 0 and 1",
        ),
        SKILLS / "token-value-fix" / "SKILL.md": (
            "Default to one variable per pass",
            "exact pre-approved rollback values",
            "Do not infer a conversion from the UI display, scope, name, or type",
            "A general `Go`, a prior token-creation approval, or a binding approval is insufficient",
            "run a fresh independent `token-readonly-scan` with a new audit ID",
        ),
    }
    for path, phrases in required.items():
        text = path.read_text(encoding="utf-8")
        for phrase in phrases:
            if phrase not in text:
                errors.append(f"{path.relative_to(ROOT)}: missing safety invariant {phrase!r}")


def run_tests(errors: list[str]) -> None:
    result = subprocess.run(
        [sys.executable, "-B", "-m", "unittest", "-q", "tests/test_validators.py"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode:
        errors.append("validator regression tests failed:\n" + result.stdout + result.stderr)


def check_dist(errors: list[str]) -> None:
    dist = ROOT / "dist" / "claude"
    expected = {path.name for path in SKILLS.iterdir() if path.is_dir()}
    actual = {path.stem for path in dist.glob("*.zip")} if dist.exists() else set()
    if actual != expected:
        errors.append(f"dist/claude: expected ZIPs {sorted(expected)}, got {sorted(actual)}")
        return
    for skill_name in sorted(expected):
        archive = dist / f"{skill_name}.zip"
        with zipfile.ZipFile(archive) as bundle:
            names = bundle.namelist()
        prefix = f"{skill_name}/"
        if f"{prefix}SKILL.md" not in names:
            errors.append(f"{archive}: missing {prefix}SKILL.md")
        if any(not name.startswith(prefix) for name in names):
            errors.append(f"{archive}: every entry must be inside the root skill folder")
        prohibited = [name for name in names if "__pycache__" in name or name.endswith((".pyc", ".DS_Store"))]
        if prohibited:
            errors.append(f"{archive}: contains prohibited generated files {prohibited}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", help="Expected package version without a v prefix; defaults to README")
    parser.add_argument("--dist", action="store_true", help="Also validate built ZIP packages")
    args = parser.parse_args()
    version = args.version or read_package_version()
    if not version or not VERSION_RE.fullmatch(version):
        parser.error("--version must use MAJOR.MINOR.PATCH")

    errors: list[str] = []
    skill_dirs = sorted(path for path in SKILLS.iterdir() if path.is_dir())
    if not skill_dirs:
        errors.append("No Claude skill directories found")
    for skill_dir in skill_dirs:
        check_skill(skill_dir, version, errors)
    check_versions(version, errors)
    check_local_links(errors)
    check_trigger_evals(errors)
    check_generated_files(errors)
    check_orchestrator_bundle(errors)
    check_binding_release(errors)
    check_value_release(errors)
    check_documentation_layout_release(errors)
    check_process_navigator_release(errors)
    check_property_coverage_release(errors)
    check_safety_invariants(errors)
    run_tests(errors)
    if args.dist:
        check_dist(errors)

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        print(f"release check failed with {len(errors)} error(s)", file=sys.stderr)
        return 1
    scope = "source and packages" if args.dist else "source"
    print(f"release check passed for {scope}, version {version}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
