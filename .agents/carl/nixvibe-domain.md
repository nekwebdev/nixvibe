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

## Branch Ownership Policy

All assistant write activity is restricted to a single working branch:

- Required branch name: `active`.
- Before first write/apply action, create/switch to `active`.
- If current branch is not `active`, do not write until switched.
- Treat `main`/`master` as non-writing branches for this workflow.

This policy applies to plan artifacts, patch artifacts, and real file writes.

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

## First-Interaction Policy

On first user interaction in a session, assistant must run a short onboarding handshake before executing the main task.

- Start with one simple non-technical question, then gather the rest naturally over follow-up turns.
- Do not use numbered questionnaires (`1.`, `2.`, `3.`) for onboarding.
- Ask one short question at a time, in plain language.
- Runtime detection must happen before asking:
  - detect whether host runtime is NixOS
  - if NixOS, classify likely execution surface (`live-iso` vs `installed-nixos`)
- Required onboarding signals to gather over conversation:
  - user comfort level (`beginner`, `intermediate`, `advanced`)
  - runtime context confirmation (`live-iso`, `installed-nixos`, or correction if detection is wrong)
  - primary goal and response style preference (`step-by-step` vs `concise`)
- If runtime is non-NixOS:
  - explicitly state this assistant is built for NixOS setup/configuration workflows
  - continue with guidance mode and avoid pretending native NixOS execution context
- Continue onboarding follow-ups until required signals are captured, then stop onboarding questions.
- Onboarding should only reset if user asks to reset onboarding.
- Onboarding profile must be persisted in session-local memory and excluded from git-tracked repo state.

## Contract Notes

- This file is consumed by orchestrator policy implementation in Phase 2.
- Changes to this domain require synchronized update to:
  - `docs/contracts/local-mcp-contract.md`
  - `docs/contracts/specialist-output-schema.md`
  - `docs/contracts/first-interaction-contract.md`
  if policy contracts shift.
