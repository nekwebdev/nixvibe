# Roadmap: nixvibe

## Overview

Ship a policy-driven NixOS guidance engine in phased slices: first lock governance and contracts, then deliver orchestration and artifact generation, then harden through validation and acceptance.

## Current Milestone

**v0.3 Operational Workflow Intelligence** (v0.3.0)
Status: 🚧 In progress
Phases: 2 of 3 complete

## Phases

| Phase | Name | Plans | Status | Completed |
|-------|------|-------|--------|-----------|
| 7 | Git Ledger and Change Intelligence | 3 (`07-01`, `07-02`, `07-03`) | ✅ Complete | 2026-04-20 |
| 8 | Apply Safety Escalation and Recovery | 3 (`08-01`, `08-02`, `08-03`) | ✅ Complete | 2026-04-20 |
| 9 | Operator Surfaces and Release Ops | 3 (`09-01`, `09-02`, `09-03`) | 🚧 In progress | - |

## Phase Details

### Phase 7: Git Ledger and Change Intelligence

**Goal:** Treat Git workspace state as first-class runtime context for safer orchestration decisions.
**Depends on:** v0.2 baseline
**Research:** Medium (change classification + ledger semantics)

**Scope:**
- Git ledger snapshot contract in pipeline output
- Change classification (staged/unstaged/untracked/drift)
- Ledger-aware action guidance hooks

**Plans:**
- [x] 07-01: Git ledger baseline contract integration
- [x] 07-02: Ledger change classification and drift signals
- [x] 07-03: Ledger-aware guidance/next-action tuning

### Phase 8: Apply Safety Escalation and Recovery

**Goal:** Strengthen apply-time safety escalation and remediation workflows.
**Depends on:** Phase 7
**Research:** Medium (recovery policy semantics)

**Scope:**
- Escalation tiers for apply failures and repeated validation breakage
- Recovery playbook contract for reversible remediation
- Additional guardrails for high-risk mutation paths

**Plans:**
- [x] 08-01: Apply escalation tier contract
- [x] 08-02: Recovery playbook integration
- [x] 08-03: High-risk mutation guardrail regressions

### Phase 9: Operator Surfaces and Release Ops

**Goal:** Improve operational usability and release confidence for daily assistant-driven workflows.
**Depends on:** Phase 8
**Research:** Medium (operator ergonomics + release criteria)

**Scope:**
- Operator-facing run summaries/manifests
- Release-readiness checks and failure reporting
- End-to-end milestone acceptance scenarios

**Plans:**
- [x] 09-01: Operator run manifest contract
- [ ] 09-02: Release-readiness gate expansion
- [ ] 09-03: End-to-end acceptance hardening

## Completed Milestones

<details>
<summary>v0.2 Execution and Context Expansion (v0.2.0) — completed 2026-04-20</summary>

### Milestone Snapshot

Status: ✅ Complete  
Phases: 3 of 3 complete  
Plans completed: 9

| Phase | Name | Plans | Status | Completed |
|-------|------|-------|--------|-----------|
| 4 | Workspace Intake and Reference Adaptation | 3 (`04-01`, `04-02`, `04-03`) | ✅ Complete | 2026-04-19 |
| 5 | Runtime Agent Execution and Patch Orchestration | 3 (`05-01`, `05-02`, `05-03`) | ✅ Complete | 2026-04-20 |
| 6 | Guidance UX and Safety Guardrails | 3 (`06-01`, `06-02`, `06-03`) | ✅ Complete | 2026-04-20 |

Archive: `.paul/milestones/v0.2.0-ROADMAP.md`

</details>

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
