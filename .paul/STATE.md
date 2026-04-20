# Project State

## Project Reference

See: .paul/PROJECT.md (updated 2026-04-20)

**Core value:** Users can evolve clean modular NixOS configs safely with guided automation.
**Current focus:** v0.4 Phase 11 planning — preparing Phase 11 plan 11-01

## Current Position

Milestone: v0.4 Reliability and Delivery Hardening (v0.4.0)
Phase: 11 of 12 (Operator Policy and Controls) — Not started
Plan: 10-03 completed
Status: APPLY and verification complete; ready for 11-01 planning
Last activity: 2026-04-20T12:58:57-10:00 — Completed .paul/phases/10-runtime-reliability-and-resume/10-03-SUMMARY.md

Progress:
- v0.1 Initial Release: [██████████] 100% ✓
- v0.2 Execution and Context Expansion: [██████████] 100% ✓
- v0.3 Operational Workflow Intelligence: [██████████] 100% ✓
- v0.4 Reliability and Delivery Hardening: [███░░░░░░░] 33%

## Loop Position

Current loop state:
```
PLAN ──▶ APPLY ──▶ UNIFY
  ✓        ✓        ✓     [10-03 complete]
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
- Git ledger baseline contract landed in pipeline summary for Phase 7 plan 07-01
- Ledger change classification and drift signal contract landed for Phase 7 plan 07-02
- Ledger-aware guidance/next-action tuning landed for Phase 7 plan 07-03
- Apply safety escalation tier contract landed for Phase 8 plan 08-01
- Recovery playbook contract integration landed for Phase 8 plan 08-02
- High-risk mutation guardrail regressions landed for Phase 8 plan 08-03
- Operator run manifest contract landed for Phase 9 plan 09-01
- Release-readiness gate expansion landed for Phase 9 plan 09-02
- End-to-end operational acceptance hardening landed for Phase 9 plan 09-03
- v0.4 milestone scaffold initialized with phases 10-12 and plan 10-01 as next action
- Run failure classification contract landed for Phase 10 plan 10-01
- Resume-safe checkpoint contract landed for Phase 10 plan 10-02
- Retry/backoff guardrail contract landed for Phase 10 plan 10-03

### Deferred Issues
None yet.

### Blockers/Concerns
None yet.

## Session Continuity

Last session: 2026-04-20T12:58:57-10:00
Stopped at: Phase 10 plan 10-03 completed and summarized
Next action: Create and approve `.paul/phases/11-operator-policy-and-controls/11-01-PLAN.md`
Resume file: .paul/phases/10-runtime-reliability-and-resume/10-03-SUMMARY.md

---
*STATE.md — Updated after every significant action*
