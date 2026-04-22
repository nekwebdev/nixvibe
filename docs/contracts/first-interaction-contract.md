# First-Interaction Contract

## Intent

Define deterministic first-session onboarding behavior so assistant output adapts to:

- user technical level
- runtime environment (`live-iso`, `installed-nixos`, `non-nixos`)
- user goal and response style

This contract is runtime policy, not a loose prompt guideline.

## Trigger

- Trigger on first user prompt in a session (`prompt_count == 1`).
- Continue onboarding until required signals are captured.
- Reset onboarding only if user requests onboarding reset.

## Required Question Set

Do onboarding as a natural conversation:

- Ask one short question at a time.
- Do not use numbered `1/2/3` questionnaires.
- Start with a simple plain-language question.
- Gather these required signals across turns:
  - technical level (`beginner`, `intermediate`, `advanced`)
  - environment confirmation (detected runtime vs user correction)
  - current goal + response style preference (`step-by-step` vs `concise`)

## Runtime Detection Contract

At first interaction, runtime detection must produce:

- `runtime_environment`: `nixos`, `non-nixos`, or `unknown`
- `execution_surface`: `live-iso`, `installed-nixos`, `non-nixos`, or `unknown`
- `evidence`: bounded list of detection evidence strings

Recommended heuristics:

- `/etc/os-release` `ID=nixos` => `runtime_environment=nixos`
- `/iso` or `/iso/nixvibe` present on NixOS => `execution_surface=live-iso`
- NixOS without ISO marker => `execution_surface=installed-nixos`

## Non-NixOS Behavior

If `runtime_environment=non-nixos`, assistant must:

- explicitly state nixvibe assistant is intended for NixOS setup/configuration workflows
- avoid pretending native NixOS execution context
- continue in guidance mode with NixOS-focused next steps

## Conversation Style Guardrails

- First onboarding question should avoid jargon.
- Do not front-load all onboarding questions in one message.
- Prefer plain language first; introduce terms like `live ISO` only after context is established.
- Stop onboarding questions as soon as required signals are known.

## Session State Schema

Persist session onboarding state in session-local memory:

```json
{
  "first_interaction": {
    "completed": false,
    "asked_at_prompt": 1,
    "completed_at_prompt": null,
    "profile": {
      "skill_level": "unknown",
      "goal": "unknown",
      "response_style": "unknown"
    },
    "runtime": {
      "runtime_environment": "nixos",
      "execution_surface": "live-iso",
      "checked_at": "2026-04-21T12:00:00Z",
      "evidence": ["os-release:id=nixos", "path:/iso"]
    }
  }
}
```

## Persistence Boundaries

- Session-local storage: `.carl/sessions/<session-id>.json`
- Must be gitignored (already covered by `.carl/sessions/*` ignore rule)
- Do not persist per-user onboarding profile in git-tracked policy files

## Implementation Mapping

- Policy source: `.agents/carl/nixvibe-domain.md`
- Runtime injection + session persistence:
  - `.codex/hooks/carl-hook.py`
  - `.claude/hooks/carl-hook.py`
