---
name: token-creation-proposal
description: Prepare exact design token creation proposals after semantic gaps have been identified. Use when the user wants proposed new Figma variables or tokens with names, collections, types, modes, values, aliases, scopes, descriptions, changelog rows, reference cards, and verification plans. Do not create tokens unless the exact proposal is explicitly approved.
---

# Token Creation Proposal

Version: 0.2.2

Use this skill to turn accepted semantic gaps into concrete token creation proposals.

## Rule

Do not create variables or tokens until the exact proposal is approved.

## Required Proposal

For every proposed token, include:

- token name
- target collection
- token layer, such as Global, Alias, Platform, Component, or Typography
- type, such as Color, Float, String, Boolean, Effect, or Typography
- modes
- values or aliases per mode
- scopes
- description
- reason this token is needed
- nearest existing token
- consumer impact
- risk level

## Required Write Preview

Before creating anything, show:

```text
Preview: Token Creation

Library:
Collection:
Tokens to create:
Modes:
Values or aliases:
Scopes:
Descriptions:
Risk:
Consumer impact:
Changelog:
Reference:
Verification:

Please approve this exact token creation pass before I make any changes.
```

## Verification

After approval and creation, verify:

- exact tokens exist
- correct collection
- correct type
- correct modes
- correct values or aliases
- correct scopes
- descriptions present
- changelog row present
- reference card or frame visible
- no unexpected variables were created

## Final Response

Summarize what was proposed, what was approved, what was created, and what remains on hold.
