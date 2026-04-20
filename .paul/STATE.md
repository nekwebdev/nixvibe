# Project State

## Project Reference

See: .paul/PROJECT.md (updated 2026-04-19)

**Core value:** Users can evolve clean modular NixOS configs safely with guided automation.
**Current focus:** v0.1 Initial Release — Phase 3 plan 03-01 completed, preparing 03-02

## Current Position

Milestone: v0.1 Initial Release (v0.1.0)
Phase: 3 of 3 (Validation and Acceptance) — In progress
Plan: 03-01 completed
Status: APPLY and verification complete; ready to move to 03-02 planning
Last activity: 2026-04-19T15:15:53-10:00 — Completed .paul/phases/03-validation-and-acceptance/03-01-SUMMARY.md

Progress:
- Milestone: [█████████░] 90%
- Phase 3: [███░░░░░░░] 33%

## Loop Position

Current loop state:
```
PLAN ──▶ APPLY ──▶ UNIFY
  ✓        ✓        ✓     [03-01 complete]
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

### Deferred Issues
None yet.

### Blockers/Concerns
None yet.

## Session Continuity

Last session: 2026-04-19T15:15:53-10:00
Stopped at: Plan 03-01 completed and summarized
Next action: Create and approve `.paul/phases/03-validation-and-acceptance/03-02-PLAN.md`
Resume file: .paul/phases/03-validation-and-acceptance/03-01-SUMMARY.md

---
*STATE.md — Updated after every significant action*
