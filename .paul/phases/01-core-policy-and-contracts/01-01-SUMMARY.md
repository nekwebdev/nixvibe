---
phase: 01-core-policy-and-contracts
plan: 01
subsystem: infra
tags: [carl, mcp, contracts, schema, policy]
requires: []
provides:
  - CARL policy source-of-truth domain
  - Local MCP contracts for Codex and Claude
  - Specialist output schema with merge semantics
affects: [phase-02, orchestration, routing, merge]
tech-stack:
  added: [none]
  patterns: [policy-contract-first, forced-local-mcp]
key-files:
  created:
    - .agents/carl/nixvibe-domain.md
    - .codex/config.toml
    - .mcp.json
    - docs/contracts/local-mcp-contract.md
    - docs/contracts/specialist-output-schema.md
  modified: []
key-decisions:
  - "Local MCP contracts are mandatory and project-local."
  - "Conflict merge order is fixed and encoded in CARL."
patterns-established:
  - "Contract docs precede orchestration implementation."
  - "Structured specialist payloads required for merge."
duration: 8min
started: 2026-04-19T00:00:53-10:00
completed: 2026-04-19T00:08:32-10:00
---

# Phase 1 Plan 1: Core Policy and Contracts Summary

**Locked deterministic policy and contract foundation for nixvibe orchestration before implementation begins.**

## Performance

| Metric | Value |
|--------|-------|
| Duration | ~8 min |
| Started | 2026-04-19T00:00:53-10:00 |
| Completed | 2026-04-19T00:08:32-10:00 |
| Tasks | 3 completed |
| Files modified | 5 created |

## Acceptance Criteria Results

| Criterion | Status | Notes |
|-----------|--------|-------|
| AC-1: CARL Domain Locked | Pass | `.agents/carl/nixvibe-domain.md` created with route, mode, conflict, validation, and skill adaptation policy |
| AC-2: Local MCP Contracts Locked | Pass | `.codex/config.toml`, `.mcp.json`, and contract doc created with forced-local behavior and `.codex` migration guidance |
| AC-3: Specialist Output Schema Locked | Pass | Schema/merge contract documented with required fields and normalized example payload |

## Accomplishments

- Created CARL source-of-truth policy file at `.agents/carl/nixvibe-domain.md`.
- Locked Codex + Claude project-local MCP contracts with portability and migration rules.
- Defined specialist payload contract and deterministic merge semantics for Phase 2 implementation.

## Task Commits

Execution was completed in one APPLY loop without per-task commits.
Phase commit is created during transition.

## Files Created/Modified

| File | Change | Purpose |
|------|--------|---------|
| `.agents/carl/nixvibe-domain.md` | Created | CARL policy source-of-truth for route/mode/merge/validation behavior |
| `.codex/config.toml` | Created | Codex local MCP contract baseline |
| `.mcp.json` | Created | Claude local MCP contract baseline |
| `docs/contracts/local-mcp-contract.md` | Created | Explicit local MCP requirements, env portability, and `.codex` migration behavior |
| `docs/contracts/specialist-output-schema.md` | Created | Specialist output schema and merge behavior contract |

## Decisions Made

| Decision | Rationale | Impact |
|----------|-----------|--------|
| Force project-local MCP contracts | Deterministic behavior across environments | Blocks global-only drift |
| Encode fixed conflict priority in CARL | Prevent ad hoc merge outcomes | Stable orchestration decisions |
| Require structured specialist payloads | Merge logic must operate on normalized data | Enables predictable Phase 2 implementation |

## Deviations from Plan

### Summary

| Type | Count | Impact |
|------|-------|--------|
| Auto-fixed | 0 | None |
| Scope additions | 0 | None |
| Deferred | 0 | None |

**Total impact:** Plan executed as written, no scope drift.

## Issues Encountered

| Issue | Resolution |
|-------|------------|
| None | N/A |

## Next Phase Readiness

**Ready:**
- Policy and contract artifacts are in place for orchestration implementation.
- Merge and payload expectations are explicit for specialist integration work.

**Concerns:**
- CARL runtime install still pending and must occur before first Phase 2 orchestration APPLY.

**Blockers:**
- None for planning Phase 2.

---
*Phase: 01-core-policy-and-contracts, Plan: 01*
*Completed: 2026-04-19*
