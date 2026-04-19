# nixvibe CARL Domain

## Scope

This domain defines runtime policy for nixvibe orchestration behavior.
It is the source of truth for route selection, safety gates, conflict resolution, and validation expectations.

## Route Selection Policy

### Primary routes
- `init`: Use when user intent is new scaffold, first-time structure, or greenfield host/profile setup.
- `audit`: Use when user intent is refactor, repair, modernization, or analysis of existing config.

### Route tie-breakers
- If repository state is unknown and request is ambiguous, ask focused clarification (max 4 questions), then route.
- If existing config is present and user asks for changes, prefer `audit`.
- If no usable Nix structure is present, prefer `init`.

## Write-Mode Policy

### Modes
- `advice`: no file writes, guidance only.
- `propose`: create plan and patch artifacts, confirm-first before apply.
- `apply`: explicit user opt-in, writes files.

### Safety gates
- Default mode for `audit` is `propose`.
- `audit` must never auto-apply without explicit user opt-in.
- Mode must be made explicit by behavior (no surprise writes).

## Conflict Resolution Policy

Merge and decision priority is strict:

1. `safety`
2. `correctness`
3. `reversibility`
4. `simplicity`
5. `user preference`
6. `style`

Specialist outputs are merged using this order; lower-priority items cannot override higher-priority constraints.

## Validation Policy

For V1 flake-first workflow, required gates are:
- `nix flake check`
- `nix fmt`

If validation fails, output must remain in `propose` state with actionable remediation.

## User-Skill Adaptation Policy

User skill spectrum may range from veteran developer to beginner.
Adapt explanation depth and pacing without changing safety gates:

- Expert: concise, high-signal output.
- Beginner: clearer step-by-step framing.

Safety, validation, and confirm-first requirements stay constant for all users.

## Contract Notes

- This file is consumed by orchestrator policy implementation in Phase 2.
- Changes to this domain require synchronized update to `docs/contracts/local-mcp-contract.md` and `docs/contracts/specialist-output-schema.md` if policy contracts shift.
