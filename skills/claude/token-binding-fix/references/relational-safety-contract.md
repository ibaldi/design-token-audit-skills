# Binding Relational Safety Contract

Contract version: `1.0.0`

Read this contract when an approved binding candidate can change the effective rendered background behind text or a meaningful graphical object. This is a preflight and reporting requirement; it does not authorize a second binding or any token creation or value change.

## Trigger

Trigger this check from the actual property path, rendered geometry, and resolved current/proposed values. A variable scope such as `FRAME_FILL` or `SHAPE_FILL` is supporting evidence, not proof that the node is a background.

Run the check when the tuple changes a visible surface paint, or another property whose resolved value changes the composited background behind foreground content. Do not trigger solely because a variable name contains `bg`, a variable permits a fill scope, or an unrelated node shares the same token.

## Affected Foreground Discovery

Inspect all foreground nodes whose rendered bounds intersect the changed surface and whose visual output depends on it, including nested descendants and overlapping siblings when observable. Do not limit discovery to direct children.

Classify candidates as:

- text or image-of-text
- meaningful UI indicator or graphical object
- decorative, inactive, hidden, or otherwise exempt
- not observable

An icon is not automatically subject to a contrast threshold. Apply the non-text threshold only when the graphical object or UI indicator is required for understanding, identification, or state perception. Record the evidence for that classification.

## Effective Color And Mode Evidence

For each affected foreground candidate and relevant mode, record:

- foreground node ID and property path
- background node ID and changed tuple
- current and proposed resolved foreground colors
- current and proposed resolved background colors
- node and paint opacity used in compositing
- visible paint index and any additional paints, effects, or ancestors that affect the result
- text size and weight when text is evaluated
- current ratio, proposed ratio, threshold, delta, and result
- limitations and inspection method

Compute a ratio only when the effective adjacent foreground and background colors can be resolved deterministically. Account for alpha compositing and inherited node opacity. For gradients, images, blend modes, masks, effects, multiple unresolved paints, or unknown underlying surfaces, report `not_observable` unless the adapter can determine the least-contrast rendered color pair. Never substitute raw token values for effective rendered colors.

For deterministic solid-color pairs, composite transparency against the observed underlying color before calculating luminance. Convert each normalized sRGB channel `c` to linear light as `c / 12.92` when `c <= 0.04045`, otherwise `((c + 0.055) / 1.055) ^ 2.4`. Calculate relative luminance as `0.2126R + 0.7152G + 0.0722B`, then contrast as `(lighter + 0.05) / (darker + 0.05)`. Keep unrounded values for the pass/fail decision and round only the displayed ratio.

## Thresholds

Use WCAG AA thresholds:

- normal text: `4.5:1`
- large-scale text: `3:1`, using the applicable size-and-weight criteria
- meaningful graphical objects and UI indicators: `3:1` against adjacent colors

Record exemptions rather than silently dropping them.

## Gate And Preview

Add a `Relational safety` block under `Risk and consumer impact` for every triggered tuple. It must enumerate the affected foreground nodes and mode results and distinguish:

- `pass`
- `new_failure`
- `existing_failure_unchanged`
- `improved_but_failing`
- `not_observable`
- `not_applicable`

Do not present a tuple as ordinarily approval-ready when it creates a new known accessibility failure. Hold it and route the missing foreground role to semantic-gap review or another separately approved pass. An existing or improved-but-still-failing result requires explicit approval naming the accessibility risk. A required but unresolved effective-color check remains on hold because consumer impact is not bounded.

Approval for the background tuple never authorizes changing a foreground node. Any foreground binding, token creation, or value correction requires its own evidence, preview, approval, drift check, and verification.

## Evidence-backed Relationship Notes

Report a non-mechanical relationship as an open risk only when an observed peer pattern, documented design-system rule, component-state convention, or measurable geometry relationship supports it. Name the affected nodes and the evidence. Do not generate speculative coupling warnings merely because two properties are nearby.

Examples include a demonstrated icon-and-label color convention or a documented nested-radius rule. These notes are not pass/fail assertions and do not authorize an additional write.
