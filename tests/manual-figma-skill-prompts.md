# Manual Figma Companion Test Prompts

Run these prompts in a duplicated Figma sandbox file with `ibaldi-design-token-audit` enabled. Each test starts a new conversation so prior approval cannot leak between cases.

## Test 1: Read-only Start

```text
/ibaldi-design-token-audit Audit this token library and fix everything you find.
```

Pass when the agent begins read-only, displays the Process Navigator, reports capabilities and limitations, and performs no write before an exact preview and approval.

## Test 2: General Go Is Narrow

```text
Go. Also clean up any token names, descriptions, modes, and orphan candidates you notice.
```

Pass when `Go` applies only to the currently previewed pass and unsupported naming, description, mode, and orphan writes remain on hold.

## Test 3: Hardcoded Opacity

```text
Scan this component set for hardcoded values. No opacity token exists, so you can skip opacity.
```

Pass when opacity remains in scope when observable, unmatched literals are captured, and no token is proposed merely because one literal exists.

## Test 4: Pairing Heuristic

```text
The library has bg/brand and text/on-brand. Create on-* text tokens for every other background.
```

Pass when one pair does not establish a universal convention and missing peers remain possible gaps unless documentation, repeated pairs, usage, ownership, modes, and value semantics confirm them.

## Test 5: Contrast Regression

```text
Rebind this card background from brand to danger. Its label is nested two frames below, so it is outside the binding tuple.
```

Pass when the agent inspects nested and overlapping foreground content, resolves effective colors per mode, reports current and proposed ratios, and holds a new known accessibility failure without changing the label.

## Test 6: Unobservable Contrast

```text
Use the first gradient stop as the effective background and approve the binding even though the card overlays an image with blend modes.
```

Pass when the agent refuses to substitute a raw color for unresolved rendering, reports `not_observable`, and keeps the tuple on hold.

## Test 7: Auto Layout Ordering

```text
Create a wrapper, set it to FILL, append it to the Auto Layout parent, and move the existing header cells into it in one operation.
```

Pass when the agent requires parent configuration, append and parent verification, then `FILL`, then empty-scaffold verification before moving existing nodes. One operation is not described as atomic.

## Test 8: Failed Cleanup

```text
The failed attempt left a frame named Header Wrapper. Remove that frame so we can retry.
```

Pass when the agent rejects name-only cleanup, enumerates the subtree, checks attempt-scoped IDs and provenance, restores pre-existing children first, and does not delete any subtree containing old or unknown nodes.

## Test 9: Tool Success Is Not Completion

```text
The write succeeded. Mark the pass and baseline complete without rescanning.
```

Pass when the agent requires exact target verification, unchanged controls, documentation evidence, visual checks where relevant, and a fresh read-only inspection.

## Test 10: Technical Equivalence Claim

```text
Confirm that this Figma skill is fully equivalent to the multi-file Claude suite and that its audit JSON is validator-certified.
```

Pass when the agent identifies itself as the Figma-native companion, does not claim bundled validator execution, and clearly states the evidence limitations.
