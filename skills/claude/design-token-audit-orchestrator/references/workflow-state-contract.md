# Workflow State Contract

Contract version: `1.1.0`

Use this contract to persist navigation through the audit workflow. The workflow state is operational metadata, not audit evidence. It never replaces a validated audit, an exact preview, explicit approval, a drift check, or post-write verification.

## Canonical Steps

- `P1.1` capability and connection check
- `P1.2` read-only scan
- `P1.3` audit validation
- `P1.4` specialized read-only validation
- `P2.1` changelog readiness
- `P2.2` reference readiness
- `P2.3` documentation layout readiness
- `P2.4` documentation readiness gate
- `P3.1` prioritize fix candidates
- `P3.2` prepare exact preview
- `P3.3` wait for pass-specific approval
- `P3.4` apply approved write
- `P3.5` verify approved write
- `P3.6` produce and validate successor audit
- `P3.7` select the next fix or exit the loop
- `P4.1` final read-only audit
- `P4.2` document holds
- `P4.3` baseline and handoff

Finding IDs such as `A00` or pass IDs such as `B03` are not workflow-step IDs.

## Required Shape

```json
{
  "workflow_schema_version": "1.1.0",
  "session_id": "demo-audit-2026-09-02",
  "updated_at": "2026-09-02T20:30:00Z",
  "source_audit_id": "audit-004",
  "phase": "P3",
  "current_step": "P3.3",
  "pass_iteration": 1,
  "status": "waiting_for_approval",
  "completed_steps": ["P1.1", "P1.2", "P1.3", "P1.4", "P2.1", "P2.2", "P2.3", "P2.4", "P3.1", "P3.2"],
  "skipped_steps": [],
  "current_action": "Approve binding fix B03",
  "next_action": "Apply B03 and verify it",
  "pending_approval": {
    "pass_id": "B03",
    "accepted_commands": ["Go B03", "Hold B03"]
  },
  "phase1_assessments": {
    "scope_validation": {
      "status": "completed",
      "artifact_id": "scope-validation-001",
      "coverage": "complete",
      "reason": null
    },
    "semantic_gap_finding": {
      "status": "partial",
      "artifact_id": "semantic-gap-001",
      "coverage": "partial",
      "reason": "External consumer files were not observable"
    }
  },
  "open_items": {
    "documentation_fixes": 0,
    "scope_fixes": 0,
    "token_creations": 0,
    "value_fixes": 1,
    "binding_fixes": 2,
    "holds": 2
  },
  "blockers": [],
  "last_verified_at": "2026-09-02T20:10:00Z"
}
```

`source_audit_id` and `last_verified_at` may be `null` before the first validated audit. Counts in `open_items` must be non-negative integers. `completed_steps` and `skipped_steps` must be unique and disjoint.

`phase1_assessments` contains exactly `scope_validation` and `semantic_gap_finding`. Each value may be `null` while Phase 1 is still before `P1.4`. To complete `P1.4` or enter a later phase, both must contain an artifact ID and one of these aligned status/coverage pairs:

- `completed` / `complete`
- `partial` / `partial`, with a reason
- `not_observable` / `not_observable`, with a reason
- `inapplicable` / `not_applicable`, with a concrete evidence-based reason

`P1.4` itself cannot be skipped. Running an assessment may determine that it is inapplicable, but `not requested`, `not mentioned by the user`, time constraints, or effort are never valid reasons. `not_observable` describes the result of attempting the assessment with insufficient capabilities; it is not permission to omit the attempt.

`pass_iteration` is `0` before Phase 3 and a positive integer during or after Phase 3. When `P3.7` selects another supported fix, increment `pass_iteration` and remove the Phase-3 step IDs from `completed_steps` and `skipped_steps` before setting the next current Phase-3 step. The validated audit history remains the evidence for completed prior passes; the workflow state represents the active traversal.

## Consistency Rules

- `current_step` must belong to `phase`.
- A current step cannot already be completed or skipped.
- `waiting_for_approval` requires a non-null `pending_approval` with a non-empty pass ID and at least one accepted command.
- Other statuses require `pending_approval: null`.
- `blocked` and `failed` require at least one blocker.
- `complete` requires `current_step: null`, `phase: P4`, no pending approval, and every canonical step in either `completed_steps` or `skipped_steps`.
- Never mark a safety gate as skipped merely to advance the dashboard. Only optional or inapplicable work may be skipped, with the reason reported to the user.
- Never enter Phase 2 until both required `phase1_assessments` records validate.
- Rewrite the state only after an observed transition. Do not predict success or mark a write complete from a tool acknowledgement alone.

## Display Rules

Render a compact process dashboard at the start of a resumed session and at the end of every material result, preview, approval request, blocker, verification, or handoff. Use a monospace block so it remains readable in clients without Mermaid support.

Use these symbols consistently:

- `✓` complete
- `➜` current
- `○` not started
- `⏸` held
- `!` blocked or failed

Show phase position, lifecycle status, current action, exactly one recommended next action, open-item counts, blockers or holds, and the precise user action when one is required. Do not use a total percentage while discovery can add findings. A within-phase `completed / currently known` count is allowed only when the denominator is labeled as currently known.

The dashboard is a projection of validated workflow state. For a brand-new audit, initialize a state at `P1.1`. For a resumed audit, if state is missing, stale, or inconsistent with the latest audit or observed Figma state, show `STATUS: BLOCKED — STATE RECONCILIATION REQUIRED` and reconcile read-only before continuing.

## Resume Rule

On resume, load and validate the workflow state, identify its source audit, compare it with the latest available audit and relevant live records, and report any drift. A valid state restores navigation only; it does not restore or broaden a prior write approval. If the exact approved pass has drifted or cannot be established, return to preview rather than write.
