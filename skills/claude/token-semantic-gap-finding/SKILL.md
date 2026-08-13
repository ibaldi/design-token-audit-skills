---
name: token-semantic-gap-finding
description: Find missing semantic token coverage in Figma design systems without creating tokens. Use when the user asks to identify missing tokens, semantic gaps, hardcoded values, primitive values used in components, incomplete state coverage, or token opportunities across component states, product flows, Global tokens, platform tokens, or component tokens.
---

# Token Semantic Gap-finding

Version: 0.3.1

Use this skill to identify semantic token gaps. This pass is read-only.

## Rule

Do not create tokens during gap-finding. Produce evidence-backed findings and proposals only.

## What Counts As A Semantic Gap

A semantic gap exists when recurring design intent is represented through primitives, local styles, detached values, hardcoded component decisions, or inconsistent aliases instead of a clear semantic token.

Examples:

- destructive action background uses a primitive red value
- selected navigation item uses a local fill
- disabled text color appears in multiple components without a semantic foreground token
- focus, validation, warning, success, selected, disabled, pressed, hover, loading, or elevated states are inconsistent
- platform-specific surfaces are not represented in the platform token layer
- a component has multiple states, but only default state has token coverage

## Classification

Classify each finding as:

- **Confirmed semantic gap:** recurring intent, no suitable existing token, clear owning layer, and evidence.
- **Possible semantic gap / needs review:** pattern found, but ownership, naming, or existing-token fit is uncertain.
- **Not a gap:** existing token covers it, usage is one-off, or tokenizing adds unnecessary complexity.
- **Design decision needed:** behavior is inconsistent or unresolved.

## Candidate Format

```text
Semantic gap candidate

Intent:
Evidence:
Current representation:
Nearest existing token:
Why this is a gap:
Proposed token name:
Proposed collection/layer:
Type:
Modes and values/aliases:
Scopes:
Description:
Risk:
Consumer impact:
Recommendation:
```

## Summary Format

```text
Confirmed gaps:
Possible gaps / needs review:
Not gaps:
Design decisions needed:
Recommended creation proposals:
Recommended mapping fixes:
Recommended holds:
```

## Next Step

If a gap should become a token, move to `token-creation-proposal`. Do not create anything without a separate approved creation proposal.
