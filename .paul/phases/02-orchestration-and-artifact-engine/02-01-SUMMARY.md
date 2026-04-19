---
phase: 02-orchestration-and-artifact-engine
plan: 01
subsystem: orchestrator
tags: [routing, write-modes, conflicts, tests, carl]
requires:
  - .agents/carl/nixvibe-domain.md
  - docs/contracts/local-mcp-contract.md
  - docs/contracts/specialist-output-schema.md
provides:
  - Deterministic init/audit route selection
  - Write-mode resolver with confirm-first safety gates
  - Conflict resolver with fixed priority ordering
  - Contract-linked orchestration unit tests
affects: [phase-02-02, phase-02-03, phase-03]
tech-stack:
  added: [python-stdlib-unittest]
  patterns: [contract-driven-runtime, deterministic-policy-resolution]
key-files:
  created:
    - src/nixvibe/__init__.py
    - src/nixvibe/orchestrator/__init__.py
    - src/nixvibe/orchestrator/types.py
    - src/nixvibe/orchestrator/policy_loader.py
    - src/nixvibe/orchestrator/router.py
    - src/nixvibe/orchestrator/modes.py
    - src/nixvibe/orchestrator/conflicts.py
    - tests/__init__.py
    - tests/orchestrator/__init__.py
    - tests/orchestrator/test_route_and_modes.py
    - tests/orchestrator/test_conflict_priority.py
  modified:
    - README.md
    - .codex/config.toml
    - .mcp.json
key-decisions:
  - "Route/mode/conflict behavior is loaded from CARL policy and tested for drift."
  - "Audit defaults to propose mode; apply requires explicit opt-in."
  - "CARL local install is verified for both Codex and Claude before continuation."
patterns-established:
  - "Policy file parse/validation failures are explicit runtime errors."
  - "Conflict ties resolve deterministically: confidence, reversibility, stable id."
duration: 108min
started: 2026-04-19T00:16:06-10:00
completed: 2026-04-19T02:04:25-10:00
---

# Phase 2 Plan 1: Route + Mode Gating Summary

**Implemented the first executable orchestration slice from locked Phase 1 contracts, then verified CARL local installation checkpoint for both toolchains.**

## Performance

| Metric | Value |
|--------|-------|
| Duration | ~108 min (includes human checkpoint wait/install) |
| Started | 2026-04-19T00:16:06-10:00 |
| Completed | 2026-04-19T02:04:25-10:00 |
| Tasks | 3 completed (2 auto + 1 human-action checkpoint) |
| Files modified | 11 created, 3 modified |

## Acceptance Criteria Results

| Criterion | Status | Notes |
|-----------|--------|-------|
| AC-1: Deterministic Route Selection | Pass | `select_route()` returns `init`/`audit` deterministically with explicit tie/fallback behavior |
| AC-2: Write-Mode Gating Enforced | Pass | `resolve_mode()` enforces default `propose` on audit and explicit opt-in for `apply` |
| AC-3: Conflict Priority Resolver Works | Pass | `resolve_conflict()` enforces strict order: safety > correctness > reversibility > simplicity > user preference > style |
| AC-4: Contract-Driven Runtime Coverage | Pass | Route/mode/conflict tests are linked to CARL contract behavior and pass |

## Checkpoint Verification (Human Action)

Required checkpoint: local CARL install for both Codex and Claude.

Verification completed:
- `.codex/config.toml` contains `mcp_servers.carl` using local runtime entrypoint.
- `.mcp.json` contains `mcpServers.carl-mcp` using local runtime entrypoint.
- Referenced CARL runtime JS entrypoints exist on disk for both configs.
- Config parse checks passed for TOML and JSON.

## Files Created/Modified

| File | Change | Purpose |
|------|--------|---------|
| `src/nixvibe/orchestrator/types.py` | Created | Typed request/context/policy/decision models |
| `src/nixvibe/orchestrator/policy_loader.py` | Created | CARL policy parsing and validation |
| `src/nixvibe/orchestrator/router.py` | Created | Deterministic `init`/`audit` route selection |
| `src/nixvibe/orchestrator/modes.py` | Created | Write-mode resolver and guardrails |
| `src/nixvibe/orchestrator/conflicts.py` | Created | Deterministic conflict resolution |
| `tests/orchestrator/test_route_and_modes.py` | Created | Route and mode contract tests |
| `tests/orchestrator/test_conflict_priority.py` | Created | Conflict ordering/tie-break tests |
| `README.md` | Modified | Runtime orchestration behavior and coverage details |
| `.codex/config.toml` | Modified | Local CARL MCP wiring for Codex |
| `.mcp.json` | Modified | Local CARL MCP wiring for Claude |

## Verification Commands

```bash
python -m unittest discover -s tests -p 'test_*.py' -v
```

Result: 9 tests passed.

Checkpoint-specific parse/path checks:
- TOML/JSON parse passed.
- CARL runtime paths resolved.

## Deviations from Plan

| Type | Count | Impact |
|------|-------|--------|
| Auto-fixed | 1 | Added `tests/__init__.py` and `tests/orchestrator/__init__.py` after initial discovery yielded zero tests |
| Scope additions | 0 | None |
| Deferred | 0 | None |

## Next Phase Readiness

Ready:
- Runtime policy primitives are implemented and tested.
- Local CARL dependency checkpoint is complete.

Next planned continuation:
- `02-02` parallel specialists + deterministic merge pipeline.

---
*Phase: 02-orchestration-and-artifact-engine, Plan: 01*
*Completed: 2026-04-19*
