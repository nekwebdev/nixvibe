# Roadmap: nixvibe

## Overview

Ship a policy-driven NixOS guidance engine in phased slices: first lock governance and contracts, then deliver orchestration and artifact generation, then harden through validation and acceptance.

## Current Milestone

**v0.2 Execution and Context Expansion** (v0.2.0)
Status: 🚧 In progress
Phases: 2 of 3 complete

## Phases

| Phase | Name | Plans | Status | Completed |
|-------|------|-------|--------|-----------|
| 4 | Workspace Intake and Reference Adaptation | 3 (`04-01`, `04-02`, `04-03`) | ✅ Complete | 2026-04-19 |
| 5 | Runtime Agent Execution and Patch Orchestration | 3 (`05-01`, `05-02`, `05-03`) | ✅ Complete | 2026-04-20 |
| 6 | Guidance UX and Safety Guardrails | 3 (`06-01`, `06-02`, `06-03`) | Not started | - |

## Phase Details

### Phase 4: Workspace Intake and Reference Adaptation

**Goal:** Add bounded repository intake so orchestration can inspect real workspace shape and user-provided references safely.
**Depends on:** v0.1 baseline
**Research:** Medium (input boundaries and adaptation rules)

**Scope:**
- Bounded workspace snapshot reader contract
- Reference repo adaptation policy hooks
- Context profiling improvements for init/audit routing

**Plans:**
- [x] 04-01: Bounded workspace/reference profile intake baseline
- [x] 04-02: Reference adaptation policy integration
- [x] 04-03: Intake-driven specialist dispatch context wiring

### Phase 5: Runtime Agent Execution and Patch Orchestration

**Goal:** Replace placeholder specialist behavior with executable task runners and deterministic patch set generation.
**Depends on:** Phase 4
**Research:** Medium (runner contracts + patch lifecycle)

**Scope:**
- Runtime specialist task runner interfaces
- Patch proposal pipeline hardening (propose/apply boundaries)
- Validation preflight/checkpoint integration for write paths

**Plans:**
- [x] 05-01: Runtime specialist execution contract
- [x] 05-02: Patch orchestration integration
- [x] 05-03: Validation checkpoints in write flows

### Phase 6: Guidance UX and Safety Guardrails

**Goal:** Improve user-facing guidance quality across skill levels while preserving safety gates.
**Depends on:** Phase 5
**Research:** Medium (content strategy + guardrails)

**Scope:**
- Skill-adaptive explanation output structure
- Stronger remediation output for failed validations/conflicts
- Journey-level regression scenarios for novice-to-expert interactions

**Plans:**
- [ ] 06-01: Skill-adaptive output contract
- [ ] 06-02: Safety/remediation guidance hardening
- [ ] 06-03: Novice-to-expert journey regressions

## Completed Milestones

<details>
<summary>v0.1 Initial Release (v0.1.0) — completed 2026-04-19</summary>

### Milestone Snapshot

Status: ✅ Complete  
Phases: 3 of 3 complete  
Plans completed: 7

| Phase | Name | Plans | Status | Completed |
|-------|------|-------|--------|-----------|
| 1 | Core Policy and Contracts | 1 (`01-01`) | ✅ Complete | 2026-04-19 |
| 2 | Orchestration and Artifact Engine | 3 (`02-01`, `02-02`, `02-03`) | ✅ Complete | 2026-04-19 |
| 3 | Validation and Acceptance | 3 (`03-01`, `03-02`, `03-03`) | ✅ Complete | 2026-04-19 |

Archive: `.paul/milestones/v0.1.0-ROADMAP.md`

</details>

---
*Roadmap created: 2026-04-18*
*Last updated: 2026-04-20*
