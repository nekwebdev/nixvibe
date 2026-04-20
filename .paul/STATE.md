# Project State

## Project Reference

See: .paul/PROJECT.md (updated 2026-04-19)

**Core value:** Users can evolve clean modular NixOS configs safely with guided automation.
**Current focus:** Milestone boundary — v0.1 complete, next milestone definition pending

## Current Position

Milestone: Awaiting next milestone
Phase: None active
Plan: None
Status: Milestone v0.1 Initial Release complete — ready for next milestone setup
Last activity: 2026-04-19T15:45:37-10:00 — Finalized milestone records and release notes for v0.1.0

Progress:
- v0.1 Initial Release: [██████████] 100% ✓

## Loop Position

Current loop state:
```
PLAN ──▶ APPLY ──▶ UNIFY
  ○        ○        ○     [Milestone complete - ready for next]
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

### Deferred Issues
None yet.

### Blockers/Concerns
None yet.

## Session Continuity

Last session: 2026-04-19T15:45:37-10:00
Stopped at: Milestone v0.1 Initial Release complete
Next action: `/paul:discuss-milestone` or `/paul:milestone`
Resume file: .paul/MILESTONES.md

---
*STATE.md — Updated after every significant action*
