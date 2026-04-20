# Project State

## Project Reference

See: .paul/PROJECT.md (updated 2026-04-19)

**Core value:** Users can evolve clean modular NixOS configs safely with guided automation.
**Current focus:** v0.1 Initial Release — all phases complete, ready for release/tagging

## Current Position

Milestone: v0.1 Initial Release (v0.1.0)
Phase: 3 of 3 (Validation and Acceptance) — Complete
Plan: 03-03 completed
Status: UNIFY complete for all planned slices in milestone v0.1
Last activity: 2026-04-19T15:35:41-10:00 — Completed .paul/phases/03-validation-and-acceptance/03-03-SUMMARY.md

Progress:
- Milestone: [██████████] 100%
- Phase 3: [██████████] 100%

## Loop Position

Current loop state:
```
PLAN ──▶ APPLY ──▶ UNIFY
  ✓        ✓        ✓     [03-03 complete]
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

### Deferred Issues
None yet.

### Blockers/Concerns
None yet.

## Session Continuity

Last session: 2026-04-19T15:35:41-10:00
Stopped at: Phase 3 complete (03-01, 03-02, 03-03)
Next action: Tag/release v0.1.0 and open next milestone planning
Resume file: .paul/phases/03-validation-and-acceptance/03-03-SUMMARY.md

---
*STATE.md — Updated after every significant action*
