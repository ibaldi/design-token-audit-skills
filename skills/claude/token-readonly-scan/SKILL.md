---
name: token-readonly-scan
description: Perform a read-only current-state scan of a Figma design token library. Use when the user asks to inspect collections, modes, token counts, descriptions, scopes, ALL_SCOPES, missing mode values, naming issues, aliases, orphan candidates, changelog structure, reference cards, or baseline readiness. Never make changes in this skill.
---

# Token Read-only Scan

Use this skill to inspect a design token library without changing anything.

## Rule

Do not write, rename, delete, create, move, or edit any Figma variable, token, node, changelog row, or reference card.

## Scan Checklist

Report:

- file key and relevant pages
- local variable collections
- modes per collection
- variable counts by collection
- variable counts by type
- empty descriptions
- existing description patterns
- missing mode values
- scopes by collection
- tokens with `ALL_SCOPES`
- Light/Dark or default/AX sanity
- suspicious AX values, especially zero values
- Typography values and scopes, without changing them
- duplicate names
- leading or trailing spaces
- double spaces
- unwanted spaces around hyphens
- legacy or inconsistent naming patterns
- unresolved aliases
- local inbound alias counts
- possible orphan candidates
- changelog existence and format
- changelog sort order
- author and type values
- reference card or frame status

## Output Format

```text
Library:
File key:
Relevant pages:
Collections:
Total variables:
Variables by collection:
Variables by type:
Modes:
Descriptions complete:
Empty descriptions:
Missing mode values:
ALL_SCOPES:
Naming issues:
Duplicate names:
Unresolved aliases:
Potential orphan candidates:
Changelog status:
Reference status:
Initial risk summary:
Recommended next pass:
```

## Final Response

Clearly state that the scan was read-only and that no changes were made.
