# Changelog

## Unreleased

- No unreleased changes.

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
