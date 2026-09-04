# Documentation Structural Write Safety

Contract version: `1.0.0`

Use this contract for an approved documentation write that creates wrappers, reparents existing nodes, converts layout models, or performs recovery cleanup. It does not authorize the structural change; the exact nodes and geometry effects still require a separate preview and approval.

## Preflight And Recovery Boundary

Before the first mutation:

1. Assign a unique attempt ID and capture every affected pre-existing node's stable ID, original parent ID, sibling index, layout properties, and bounds.
2. Record every node created by this attempt by stable ID. Names are descriptive evidence only and must never establish ownership.
3. Resolve fonts, target parents, node types, layout-property support, and every other precondition that can be checked without mutation.
4. Record the rollback path. When the active adapter exposes undo checkpoints, create a boundary immediately before the attempt. For the Figma Plugin API, use `figma.commitUndo()` and treat `figma.triggerUndo()` as the preferred failure rollback. If undo is unavailable, state that limitation before writing and retain the captured parent/index map for explicit restoration.

Do not start when the affected subtree, rollback path, or recovery capability is not observable.

## Auto Layout Ordering

For every new wrapper:

1. Create the empty wrapper.
2. Configure the intended parent's `layoutMode` to a supported non-`NONE` value when that parent is part of the approved change.
3. Append the wrapper to that parent.
4. Re-read the wrapper's parent and the parent's `layoutMode`.
5. Only then set child-only values such as `layoutSizingHorizontal: FILL` or `layoutSizingVertical: FILL`.
6. Verify the empty scaffold before reparenting any pre-existing content into it.
7. Reparent only the previewed nodes, then verify their IDs, order, parent IDs, layout properties, bounds, overlap, and clipping before proceeding to the next wrapper.

Creation, append, and sizing may occur in one script when this order and the intermediate assertions are preserved. Do not describe a multi-mutation script as atomic merely because it is one tool call; an exception can leave earlier mutations applied.

## Failure And Cleanup

On any exception or failed intermediate assertion:

1. Stop the remaining mutations immediately and report which steps completed.
2. Use the previewed undo operation when available. Otherwise restore every pre-existing node to its captured parent and sibling index before considering scaffold cleanup.
3. Resolve cleanup targets only from the current attempt's recorded IDs. Never identify a deletion target from its name, page position, or parent alone.
4. Enumerate the complete descendant subtree before calling `.remove()` or another cascading delete.
5. Remove a cleanup subtree only when its root and every descendant were created by the current attempt. If any descendant predates the attempt, has unknown provenance, or cannot be inspected, do not remove the subtree. Restore known content where possible, leave the remainder in place, and report the exact IDs and current parents for review.
6. Re-read all affected pre-existing nodes after rollback or restoration. Do not retry the structural write until a fresh drift check succeeds and a revised preview is approved when the target set or recovery plan changed.

Attempt-scoped cleanup only restores the approved pre-write state. It is not orphan deletion and must not be used to bypass a dedicated deletion workflow.

## Success Checkpoint

After all structural and visual verification succeeds, commit an undo boundary when supported so the completed pass remains recoverable as one deliberate unit. Preserve the before/after evidence, attempt ID, created-node IDs, and recovery result in the pass report.
