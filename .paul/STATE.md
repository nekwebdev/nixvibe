# Project State

## Project Reference

See: .paul/PROJECT.md (updated 2026-04-20)

**Core value:** Users can evolve clean modular NixOS configs safely with guided automation.
**Current focus:** v0.2 complete — preparing next milestone definition

## Current Position

Milestone: v0.2 Execution and Context Expansion (v0.2.0)
Phase: 6 of 6 (Guidance UX and Safety Guardrails) — Complete
Plan: 06-03 completed
Status: APPLY and verification complete; milestone closeout complete
Last activity: 2026-04-20T02:56:45-10:00 — Completed .paul/phases/06-guidance-ux-and-safety-guardrails/06-03-SUMMARY.md

Progress:
- v0.1 Initial Release: [██████████] 100% ✓
- v0.2 Execution and Context Expansion: [██████████] 100% ✓

## Loop Position

Current loop state:
```
PLAN ──▶ APPLY ──▶ UNIFY
  ✓        ✓        ✓     [06-03 complete]
```

## Accumulated Context

### Decisions
- CARL required in V1 for policy enforcement
- Local MCP required for Codex and Claude
- Validation gates fixed to `nix flake check` and `nix fmt`
- Local MCP contract files locked in repo (`.codex/config.toml`, `.mcp.json`)
- Specialist payload schema and merge contract locked for orchestration phase
- Local CARL runtime installed and verified for both Codex and Claude in repo
- `.claude`, `.carl`, `.agents`, and `.codex` are versioned project artifacts (excluding transient runtime caches)
- Phase 2 runtime now covers routing, specialist merge, and artifact output with mode-gated writes
- Apply mode now enforces validation gates (`nix flake check`, `nix fmt`) before writes and downgrades to propose on failure
- Acceptance-level journey tests now cover init/audit flows and apply safety behavior
- Patch artifact hygiene and release-check command path are now standardized
- Milestone archive and release notes created for v0.1.0
- v0.2 milestone scaffold created with Phases 4-6 for post-v0.1 execution scope
- Bounded workspace/reference context profiling baseline landed for Phase 4 plan 04-01
- Reference adaptation strategy model and summary contract landed for Phase 4 plan 04-02
- Intake-driven specialist dispatch context wiring landed for Phase 4 plan 04-03
- Runtime specialist execution contract and planner landed for Phase 5 plan 05-01
- Runtime patch orchestration contract landed with deterministic patch summary metadata for Phase 5 plan 05-02
- Apply-mode validation checkpoints landed with explicit pre-write/post-write contract metadata for Phase 5 plan 05-03
- Skill-adaptive guidance contract landed with deterministic novice/intermediate/expert profiling for Phase 6 plan 06-01
- Safety/remediation guidance contract landed with validation-stage and conflict-critical remediation categories for Phase 6 plan 06-02
- Novice-to-expert journey regression matrix landed for Phase 6 plan 06-03
- v0.2 milestone archive and release notes created (`.paul/milestones/v0.2.0-ROADMAP.md`, `.paul/releases/v0.2.0.md`)

### Deferred Issues
None yet.

### Blockers/Concerns
None yet.

## Session Continuity

Last session: 2026-04-20T02:56:45-10:00
Stopped at: Phase 6 plan 06-03 completed and summarized
Next action: Define v0.3 milestone roadmap and first plan
Resume file: .paul/phases/06-guidance-ux-and-safety-guardrails/06-03-SUMMARY.md

---
*STATE.md — Updated after every significant action*
