# Project State

## Project Reference

See: .paul/PROJECT.md (updated 2026-04-19)

**Core value:** Users can evolve clean modular NixOS configs safely with guided automation.
**Current focus:** v0.2 Phase 4 in progress — 04-01 complete, preparing 04-02

## Current Position

Milestone: v0.2 Execution and Context Expansion (v0.2.0)
Phase: 4 of 6 (Workspace Intake and Reference Adaptation) — In progress
Plan: 04-01 completed
Status: APPLY and verification complete; ready for 04-02 planning
Last activity: 2026-04-19T17:53:19-10:00 — Completed .paul/phases/04-workspace-intake-and-reference-adaptation/04-01-SUMMARY.md

Progress:
- v0.1 Initial Release: [██████████] 100% ✓
- v0.2 Execution and Context Expansion: [██░░░░░░░░] 20%

## Loop Position

Current loop state:
```
PLAN ──▶ APPLY ──▶ UNIFY
  ✓        ✓        ✓     [04-01 complete]
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

### Deferred Issues
None yet.

### Blockers/Concerns
None yet.

## Session Continuity

Last session: 2026-04-19T17:53:19-10:00
Stopped at: Phase 4 plan 04-01 completed and summarized
Next action: Create and approve `.paul/phases/04-workspace-intake-and-reference-adaptation/04-02-PLAN.md`
Resume file: .paul/phases/04-workspace-intake-and-reference-adaptation/04-01-SUMMARY.md

---
*STATE.md — Updated after every significant action*
