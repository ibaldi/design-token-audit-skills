---
name: token-scope-validation
description: Validate Figma variable scopes for design tokens, including ALL_SCOPES, missing expected scopes, irrelevant scopes, type-scope mismatches, Typography exceptions, AX/accessibility exceptions, and documented special cases. Use after a validated read-only scan when the user asks to review, audit, clean, narrow, or propose fixes for token scopes. Start read-only, treat names as intent signals rather than proof, classify risk, and never change scopes without an exact approved preview.
---

# Token Scope Validation

Version: 0.4.0

Use this skill to validate whether token scopes match intended usage. `ALL_SCOPES` is only one finding type; the broader task is scope-intent validation.

## Required Input

Start from a validated read-only scan. Do not run scope validation if collection, variable, type, scope, and coverage evidence are missing or invalid.

If the source scan is missing scope data, report scope validation as blocked or `not observable`.

## Rule

Do not change scopes during validation. Produce findings and proposed scope changes only.

Before any scope write, show a preview and wait for explicit approval.

## What To Validate

Check whether scopes are:

- too broad, including `ALL_SCOPES`
- too narrow for the intended usage
- missing an expected usage scope
- irrelevant to token type or intent
- inconsistent with nearby peer tokens
- inconsistent with collection or naming patterns
- inconsistent with description, when descriptions are available
- affected by Typography or AX/accessibility exceptions
- accepted documented exceptions

Use [references/scope-intent-heuristics.md](references/scope-intent-heuristics.md) for common intent signals and risk rules.

## Intent Classification

Classify likely token intent from multiple signals:

- variable type
- collection name
- token path/name
- description
- existing scopes
- peer tokens
- known platform/library conventions

Never treat the token name alone as proof. Use wording such as "appears intended for" when the evidence is heuristic.

Common intent groups:

- background / surface
- foreground / text
- border / stroke
- radius / corner
- spacing / gap / padding
- sizing / width / height
- opacity
- effect / elevation
- typography
- icon
- state, such as disabled, selected, focused, warning, error, success, pressed, or hover

## Finding Classification

Classify each issue as:

- **Scope mismatch:** current scope conflicts with observed intent.
- **Scope too broad:** token is available in more properties than intended.
- **Scope too narrow:** token is not available where intended.
- **ALL_SCOPES review:** token has `ALL_SCOPES`; decide whether it is intentional.
- **Typography / AX exception:** broad or unusual scope may be intentional; hold unless explicitly approved.
- **Accepted exception:** unusual scope is documented and should not be changed.
- **Needs design decision:** intent is unclear or inconsistent.

## Risk Classification

High risk:

- Typography scopes
- AX/accessibility-related sizing or text behavior
- production-used tokens
- cross-platform semantic tokens
- tokens with uncertain consumer usage
- scope changes that may hide a token from existing component workflows
- broad batch changes
- documented exceptions

Medium risk:

- non-Typography scope narrowing with clear evidence
- adding a missing expected scope
- aligning a small peer group with clear intent

Low risk:

- read-only findings
- documentation-only recommendations
- obvious proposals that are not applied

## Candidate Format

```text
Scope validation candidate

Token:
Collection:
Type:
Current scopes:
Likely intent:
Evidence:
Issue:
Proposed scopes:
Risk:
Consumer impact:
Recommendation:
Confidence:
Limitations:
```

## Write Preview Format

Before changing scopes, show:

```text
Preview: Scope Validation / Scope Change

Source audit:
Library:
Collection:
Affected tokens:
Current scopes:
Proposed scopes:
Reason:
Risk:
Consumer impact:
Changelog:
Reference:
Verification:

Please approve this exact scope-change pass before I make any changes.
```

## Verification

After an approved scope change, verify:

- exact affected token count
- each token has the approved scopes
- no unapproved tokens changed
- Typography and AX exceptions remain untouched unless explicitly approved
- changelog row exists, if the library was changed
- reference card or frame exists, if the library was changed
- source scan and post-change verification are documented

## Final Response

Summarize scope findings by risk:

- high-risk holds
- medium-risk proposals
- low-risk observations
- accepted exceptions
- blocked / not observable areas
- recommended next pass
