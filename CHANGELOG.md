# Changelog

## 0.8.0 - 2026-09-03

- Updated the read-only audit schema to `1.5.0` with mandatory property traversal coverage.
- Added property traversal contract `1.0.0` covering simple node fields, paints, effects, layout grids, typography, and component properties.
- Required property capabilities to come from the adapter declaration rather than tokens or bindings already present in the file.
- Added eligible, inspected, bound, literal, and mixed/unsupported counts for every declared property pattern.
- Linked every binding finding to a matching inspected property-coverage record.
- Required the official Figma Plugin API profile to declare the complete canonical bindable-property set.
- Preserved unmatched literals for the mandatory hardcoded-value sweep and propagated incomplete property coverage to semantic gap-finding.
- Explicitly excluded rotation, blend mode, and Auto Layout sizing behavior from the current variable-binding profile.
- Added validator regressions for opacity coverage, missing records, invalid counts, incomplete official profiles, and uncovered binding findings.
- Limited release-source hygiene checks to files that can enter the published packages, so unrelated local workspace artifacts do not block a valid release.

## 0.7.1 - 2026-09-02

- Made both Phase-1 specialized assessments mandatory regardless of whether the user requests them separately.
- Updated workflow-state contract to `1.1.0` with structured evidence records for scope validation and semantic gap-finding.
- Blocked completion of `P1.4` and entry into Phase 2 when either assessment record is absent or invalid.
- Prohibited skipping `P1.4`; user-request scope, time, and effort are not valid inapplicability reasons.
- Added a mandatory hardcoded-value sweep covering unmatched literals and observable in-scope bindable properties.
- Tightened semantic-gap confirmation so repeated raw values or variants of one component are not sufficient by themselves.
- Prevented unresolved token ownership or collection choices from being presented as write-ready confirmed gaps.
- Kept empty scope arrays distinct from explicit `ALL_SCOPES` unless adapter evidence establishes their meaning.
- Added workflow validator regressions for missing assessments, invalid skips, unsupported inapplicability, and coverage/status consistency.

## 0.7.0 - 2026-09-02

- Added a persistent high-level Process Navigator to the orchestrator with stable steps `P1.1` through `P4.3`.
- Added a compact visual dashboard for resumes, material results, approval requests, blockers, verification, and handoff.
- Added workflow-state contract `1.0.0`, a dependency-free validator, a valid example fixture, and explicit iteration handling for repeated Phase-3 fix passes.
- Added deterministic next-action resolution and explicit state-reconciliation behavior for missing, invalid, stale, or contradictory state.
- Kept finding/pass IDs separate from workflow-step IDs and prohibited misleading total percentages while discovery remains open.
- Prevented restored navigation state from restoring or broadening previous write approval.
- Added standardized specialist-skill handoffs while keeping canonical workflow advancement under orchestrator control.
- Added validator regressions for approval state, phase/step consistency, premature completion, blocked state, and final completeness.

## 0.6.1 - 2026-09-02

- Added documentation layout safety across the orchestrator, read-only scan, and every documentation-writing fix skill.
- Updated the audit schema to `1.4.0` with structured `layout_structure` and `visual_integrity` checks for changelog and reference documentation.
- Required dynamic internal and repeating structures to use compatible Auto Layout unless an observed approved convention requires another model.
- Prohibited positioning repeating rows or cards through assumed fixed coordinate offsets while preserving deliberate top-level canvas placement.
- Required node-exact previews before converting existing absolute-positioned documentation to Auto Layout.
- Added bounds, overlap, clipping, and complete-area screenshot verification without weakening the successor-audit gate.
- Added validator and behavioral regressions for unsafe dynamic layout, overlap, missing screenshots, and invalid blanket HUG/FILL usage.

## 0.6.0 - 2026-09-02

- Added `token-value-fix` as a seventh specialized workflow for exact value or alias corrections to existing local variables.
- Added a standalone value-evidence contract, dependency-free validator, and validated opacity correction fixture.
- Required complete local alias and bound-node impact inspection, explicit numeric semantics, consumer prediction evidence, and exact per-mode change tuples.
- Added pre-approved rollback values and immediate rollback verification for failed writes without intervening drift.
- Kept token creation, value correction, scope changes, and node binding as separately previewed and approved passes.
- Added automated regressions for remote variables, incomplete consumer coverage, unsupported predictions, invalid opacity outcomes, missing rollback, and no-op value proposals.

## 0.5.2 - 2026-09-02

- Updated the audit schema to `1.3.0` with required numeric semantics for FLOAT binding targets.
- Added a consumer-resolution preflight that compares the target variable's resolved value with the intended effective node value using an explicit tolerance.
- Added normalized `0–1` range validation for effective opacity values while keeping stored or adapter-reported values separate.
- Added a regression fixture for the observed `0.45` stored value, `0.0045` resolved opacity, and `0.45` intended effective value; this candidate is valid only as a hold.
- Prevented `token-binding-fix` and `token-creation-proposal` from turning a discovered existing-variable value error into an unsupported corrective write.
- Preserved every safety invariant carried forward from 0.4.3 and 0.5.1.

## 0.5.1 - 2026-09-02

- Rebuilt the release from the hardened 0.4.3 source instead of carrying forward the weakened 0.5.0 merge.
- Added `token-binding-fix` for exact, separately previewed and approved node-property binding, rebinding, and unbinding passes.
- Updated the audit schema to `1.2.0` with structured `binding_findings` and a derived `binding_summary`.
- Added the A00-A07 binding fixture and binding validator coverage for explicit property paths, types, modes, scopes, no-op controls, unique tuples, and summary consistency.
- Preserved the hard validator gate, unsupported-write prohibition, MVP hold boundary, node-exact documentation preview, and validated successor-audit requirement from 0.4.3.
- Added automated safety-invariant regression checks so those five protections cannot be removed unnoticed in a future release.

## 0.4.3 - 2026-09-02

- Bundled the Phase 1 contracts and dependency-free validators in the orchestrator ZIP so a standalone installation can produce and validate the canonical scan.
- Closed the validation fallback: unavailable or failed validation now yields a blocked, explicitly unvalidated draft and prevents all later phases.
- Added conservative severity and alias-evidence rules for scans without active-consumer or exhaustive inbound-alias coverage.
- Required node-exact documentation previews, explicit approval of newly proposed documentation conventions, and a validated successor audit after documentation writes.
- Prohibited unsupported writes as manual exceptions or actions outside the guardrails.
- Added release checks for bundled-resource parity and manual regressions for the demo-file failure modes.

## 0.4.2 - 2026-09-01

- Updated the audit-output schema from `1.0.0` to `1.1.0`.
- Added structured changelog and reference-card readiness so Phase 2 no longer reconstructs normal state from findings.
- Added derived metrics for local inbound aliases, description patterns, and scopes by collection.
- Added cross-field validation for documentation readiness, alias totals, description-pattern coverage, and collection scope metrics.
- Added positive and adversarial regression coverage for the new schema sections.

## 0.4.1 - 2026-09-01

- Limited the orchestrator's specialized MVP workflow to the passes implemented by the current skill suite.
- Clarified that architecture, mode, naming, orphan-candidate, and description results are read-only scan observations, not specialized validation or write passes.
- Added an explicit hold rule for unsupported fix areas until dedicated workflows define their evidence, approval, drift, verification, and documentation requirements.
- Shortened every skill description to the current Claude metadata limit and reduced trigger overlap.
- Made source-audit, approval, documentation-readiness, drift, verification, and hold gates self-contained in specialized skills.
- Hardened audit and snapshot validators for required fields, types, UTC timestamps, coverage, provenance, literal values, finding identity, and summary consistency.
- Fixed collection-local mode handling during adapter-independent semantic comparison.
- Added adversarial validator cases, trigger evals, and a dependency-free release check.

## 0.4.0 - 2026-08-22

- Added a dependency-free validator for canonical Figma token snapshots.
- Added equivalent Plugin API, MCP, and structured-export snapshot fixtures.
- Added adapter-independent semantic contract comparison across snapshots.

## 0.3.1 - 2026-08-13

- Updated the orchestrator from a linear pass order to a phased audit model.
- Separated read-only diagnosis from write-capable fix passes.
- Added Documentation Readiness as a required gate before the first fix pass.
- Clarified that architecture, scope, mode, naming, orphan, description, and token-creation changes are fix passes when they write.

## 0.3.0 - 2026-08-13

- Added `token-scope-validation` skill for general scope-intent validation.
- Added scope intent heuristics for background, foreground, border, radius, spacing, sizing, opacity, effect, and Typography tokens.
- Defined `ALL_SCOPES` as a scope review signal rather than the only scope rule.
- Added scope finding, preview, risk, and verification formats.
- Updated README to list five Claude-ready skills.

## 0.2.2 - 2026-08-12

- Added visible `Version: 0.2.2` metadata to each Claude skill body.
- Documented the current skill package version in the README.
- Added maintainer guidance to update skill-visible versions during releases.

## 0.2.1 - 2026-08-12

- Clarified README language for the current MVP skill suite.
- Added a minimal valid audit JSON fixture for validator testing.
- Documented fixture validation in the README.
- Strengthened the orchestrator gate so later audit passes require a valid read-only JSON scan first.
- Clarified the pre-write drift check for approved write passes.

## 0.2.0 - 2026-08-11

- Added a concrete Figma read execution contract for token audits.
- Added deterministic derivation and alias-resolution rules.
- Added conservative usage and orphan evidence classifications.
- Added mandatory inspection-method, coverage, and limitation reporting.
- Added a versioned JSON audit-output contract with stable finding fingerprints.
- Added synchronized human-readable and machine-readable scan outputs.
- Added a dependency-free audit JSON validator with structural and cross-field checks.
- Added capability negotiation and fallback rules for plugin-independent Figma access.
- Added a canonical Figma token snapshot model with provenance and integrity rules.
- Added adapter mappings for Plugin API, generic MCP, API, export, and mixed sources.
- Added a pre-write drift check to the audit orchestrator.

## 0.1.0

- Added initial Claude skill suite.
- Added end-to-end audit orchestrator skill.
- Added read-only scan skill.
- Added semantic gap-finding skill.
- Added token creation proposal skill.
- Added build script for Claude ZIP packages.
- Added release script for publishing ZIP artifacts to GitHub Releases.
