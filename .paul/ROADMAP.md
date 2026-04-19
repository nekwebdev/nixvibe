# Roadmap: nixvibe

## Overview

Ship a policy-driven NixOS guidance engine in phased slices: first lock governance and contracts, then deliver orchestration and artifact generation, then harden through validation and acceptance.

## Current Milestone

**v0.1 Initial Release** (v0.1.0)
Status: In progress
Phases: 1 of 3 complete

## Phases

| Phase | Name | Plans | Status | Completed |
|-------|------|-------|--------|-----------|
| 1 | Core Policy and Contracts | 1 (`01-01`) | ✅ Complete | 2026-04-19 |
| 2 | Orchestration and Artifact Engine | TBD | Not started | - |
| 3 | Validation and Acceptance | TBD | Not started | - |

## Phase Details

### Phase 1: Core Policy and Contracts

**Goal:** Lock CARL policy rules, local MCP contracts, and output schema contracts.
**Depends on:** Nothing (first phase)
**Research:** Unlikely (requirements already defined)

**Scope:**
- CARL domain file and policy set
- Local Codex/Claude MCP contracts
- `.codex` file-to-directory migration handling
- Specialist output schema and merge contract

**Plans:**
- [x] 01-01: Lock CARL domain, local MCP contracts, and specialist schema contracts

### Phase 2: Orchestration and Artifact Engine

**Goal:** Deliver route selection, parallel execution, structured artifact generation.
**Depends on:** Phase 1
**Research:** Unlikely (architecture decisions captured)

**Scope:**
- Orchestrator route logic (`init` / `audit`)
- Parallel specialist execution
- Write-mode enforcement and confirm-first flow
- Artifact generation for scaffold/refactor

**Plans:**
- [ ] 02-01: Implement route + mode gating
- [ ] 02-02: Implement parallel specialists + merge policy
- [ ] 02-03: Implement artifact output pipeline

### Phase 3: Validation and Acceptance

**Goal:** Enforce quality gates and verify production behavior.
**Depends on:** Phase 2
**Research:** Unlikely (internal verification)

**Scope:**
- Validation gate enforcement (`nix flake check`, `nix fmt`)
- Acceptance tests for init/audit
- Patch artifact hygiene (`patches/`, naming convention)

**Plans:**
- [ ] 03-01: Validation runner integration
- [ ] 03-02: Acceptance test suite
- [ ] 03-03: Patch hygiene + release checks

---
*Roadmap created: 2026-04-18*
*Last updated: 2026-04-19*
