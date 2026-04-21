# Milestones

Completed milestone log for this project.

| Milestone | Completed | Duration | Stats |
|-----------|-----------|----------|-------|
| v0.7 Release Automation and Governance Hardening (v0.7.0) | 2026-04-21 | 40m | 3 phases, 9 plans |
| v0.6 Trend Persistence and Outcome Signal Governance (v0.6.0) | 2026-04-21 | 1h 02m | 3 phases, 9 plans |
| v0.5 Measured Outcomes and Benchmark Baselines (v0.5.0) | 2026-04-20 | 1h 17m | 3 phases, 9 plans |
| v0.4 Reliability and Delivery Hardening (v0.4.0) | 2026-04-20 | 1h 09m | 3 phases, 9 plans |
| v0.3 Operational Workflow Intelligence (v0.3.0) | 2026-04-20 | 8h 49m | 3 phases, 9 plans |
| v0.2 Execution and Context Expansion (v0.2.0) | 2026-04-20 | 10h 03m | 3 phases, 9 plans |
| v0.1 Initial Release (v0.1.0) | 2026-04-19 | 15h 34m | 3 phases, 7 plans |

---

## ✅ v0.7 Release Automation and Governance Hardening (v0.7.0)

**Completed:** 2026-04-21  
**Duration:** 40m

### Stats

| Metric | Value |
|--------|-------|
| Phases | 3 |
| Plans | 9 |
| Files changed | 58 |

### Key Accomplishments

- Added release execution gate and release policy execution contracts.
- Added operator observability digest and governance hardening escalation contracts.
- Added v0.7 closeout evidence and v1.0 pathway scaffold contracts.
- Added phase20 end-to-end observability-governance acceptance coverage.
- Added v0.7 end-to-end milestone acceptance coverage across phase19-21 contract chain.
- Published v0.7 release notes and roadmap archive artifacts.

### Key Decisions

- Keep release automation explicit through gate and policy execution contracts.
- Keep governance hardening deterministic via observability digest and escalation posture.
- Keep milestone closeout readiness machine-readable with closeout evidence and pathway scaffold contracts.
- Transition to v1.0 with scaffolded phases focused on compatibility hardening, operator consolidation, and GA closeout.

---

## ✅ v0.6 Trend Persistence and Outcome Signal Governance (v0.6.0)

**Completed:** 2026-04-21  
**Duration:** 1h 02m

### Stats

| Metric | Value |
|--------|-------|
| Phases | 3 |
| Plans | 9 |
| Files changed | 66 |

### Key Accomplishments

- Added benchmark trend entry, delta, and bounded history persistence contracts.
- Added deterministic outcome alert and alert-aware policy gate contracts.
- Added release candidate evidence bundle and v0.6 readiness summary contracts.
- Added phase17 end-to-end alert-policy acceptance coverage.
- Added v0.6 end-to-end milestone acceptance coverage across phase16-18 contract chain.
- Published v0.6 release notes and roadmap archive artifacts.

### Key Decisions

- Keep trend continuity explicit through entry -> history -> delta chain before alerting.
- Keep policy routing explicit via outcome alerts and alert-aware apply/release gates.
- Keep milestone closeout readiness machine-readable with evidence and readiness summary contracts.
- Transition to v0.7 with scaffolded phases focused on release automation and governance hardening.

---

## ✅ v0.5 Measured Outcomes and Benchmark Baselines (v0.5.0)

**Completed:** 2026-04-20  
**Duration:** 1h 17m

### Stats

| Metric | Value |
|--------|-------|
| Phases | 3 |
| Plans | 9 |
| Files changed | 52 |

### Key Accomplishments

- Added deterministic run telemetry and benchmark baseline eligibility contracts.
- Added telemetry regression threshold contract and benchmark scenario harness contracts.
- Added benchmark runner, baseline snapshot, and regression consistency contracts.
- Added outcome scorecard contract tied to milestone success metrics.
- Added benchmark-aware release readiness integration contract.
- Added v0.5 end-to-end milestone acceptance coverage plus release/archive artifacts.

### Key Decisions

- Keep benchmark confidence layered: telemetry -> baseline -> regression -> scenario runner -> snapshot.
- Keep closeout confidence machine-readable via scorecard and benchmark-aware release gates.
- Preserve backward compatibility by layering benchmark release readiness over base release readiness.
- Treat milestone closeout as validated contract continuity plus published archive artifacts.

---

## ✅ v0.4 Reliability and Delivery Hardening (v0.4.0)

**Completed:** 2026-04-20  
**Duration:** 1h 09m

### Stats

| Metric | Value |
|--------|-------|
| Phases | 3 |
| Plans | 9 |
| Files changed | 48 |

### Key Accomplishments

- Added run failure classification contract with deterministic severity mapping.
- Added resume-safe checkpoint contract and bounded retry/backoff guardrails.
- Added policy decision explainability and controlled override workflow contracts.
- Added operator audit-trail summary integration.
- Added release artifact manifest/checklist and automated release-check command contracts.
- Added v0.4 milestone closeout acceptance regression suite.

### Key Decisions

- Keep reliability contracts staged: failure classification -> resume checkpoint -> retry guardrails.
- Require policy controls to be machine-readable via explainability and override contracts.
- Make release delivery explicit through manifest and release-check command contracts.
- Treat milestone closeout as tested, versioned artifact publishing, not documentation-only.

---

## ✅ v0.3 Operational Workflow Intelligence (v0.3.0)

**Completed:** 2026-04-20  
**Duration:** 8h 49m

### Stats

| Metric | Value |
|--------|-------|
| Phases | 3 |
| Plans | 9 |
| Files changed | 41 |

### Key Accomplishments

- Added git-ledger baseline, change classification, and drift intelligence contracts.
- Added ledger-aware next-action and guidance tuning for propose/apply flows.
- Added tiered apply-safety escalation contract and deterministic recovery playbook contract.
- Added high-risk mutation guardrails to block unsafe apply attempts.
- Added operator run-manifest contract for operational run summaries.
- Added release-readiness gate contract with deterministic failure reporting.
- Added end-to-end operational acceptance coverage for release-ready and release-hold journeys.

### Key Decisions

- Treat git workspace state as first-class orchestration memory for runtime decisions.
- Keep apply safety deterministic through explicit escalation tiers and recovery stages.
- Require release handoff to pass explicit gate contracts, not ad hoc operator judgment.
- Treat operational acceptance as cross-contract validation, not single-surface assertions.

---

## ✅ v0.2 Execution and Context Expansion (v0.2.0)

**Completed:** 2026-04-20  
**Duration:** 10h 03m

### Stats

| Metric | Value |
|--------|-------|
| Phases | 3 |
| Plans | 9 |
| Files changed | 31 |

### Key Accomplishments

- Added bounded workspace intake and reference adaptation contracts for real repo context.
- Added deterministic specialist dispatch context wiring into runtime task execution.
- Added typed runtime specialist contract planning and contract-driven pipeline execution path.
- Added deterministic patch orchestration with explicit summary metadata.
- Added checkpointed apply validation flow with pre-write and post-write checkpoints.
- Added skill-adaptive guidance output contract for novice/intermediate/expert users.
- Added structured remediation contract for validation and conflict safety failures.
- Added novice-to-expert end-to-end journey regression suite.

### Key Decisions

- Keep guidance adaptation and remediation as explicit structured contracts in `artifact_summary`.
- Preserve apply safety with deterministic validation checkpoints and conflict-forced propose fallback.
- Treat novice-to-expert journey regressions as mandatory guardrails for future changes.

---

## ✅ v0.1 Initial Release (v0.1.0)

**Completed:** 2026-04-19  
**Duration:** 15h 34m

### Stats

| Metric | Value |
|--------|-------|
| Phases | 3 |
| Plans | 7 |
| Files changed | 34 |

### Key Accomplishments

- Locked CARL policy source-of-truth and deterministic conflict priority rules.
- Enforced local MCP contracts for Codex and Claude with repo-level configuration.
- Implemented route and mode orchestration primitives with confirm-first safety.
- Added parallel specialist execution with structured payload validation and deterministic merge behavior.
- Delivered route-aware scaffold/refactor artifact generation with mode-gated materialization.
- Integrated required validation gates (`nix flake check`, `nix fmt`) before apply writes.
- Added acceptance journey coverage for init/audit flows and apply safety behavior.
- Standardized patch artifact hygiene and release-check workflow script.

### Key Decisions

- Keep conflict resolution deterministic: `safety > correctness > reversibility > simplicity > user preference > style`.
- Default audit flow to `propose`; require explicit opt-in for `apply`.
- Treat local MCP parity (Codex + Claude) as required project contract in V1.
- Keep patch artifacts in gitignored `patches/` with normalized safe naming.

---
