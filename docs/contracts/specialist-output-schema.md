# Specialist Output Schema Contract

## Purpose

Define structured payload contract for specialist agents and deterministic merge semantics for the orchestrator.

## Required Payload Fields

| Field | Type | Required | Notes |
|---|---|---|---|
| `agent_id` | string | yes | stable specialist id (`architecture`, `module`, `audit`, `explain`, `validate`) |
| `task_scope` | string | yes | bounded assignment summary |
| `status` | string | yes | `ok` \| `warning` \| `error` |
| `findings` | array<object> | yes | normalized findings list |
| `recommendations` | array<object> | yes | proposed actions |
| `confidence` | number | yes | 0.0 to 1.0 |
| `risks` | array<object> | yes | explicit risk items |
| `artifacts` | object | yes | structured outputs for downstream merge |
| `checks` | object | yes | validation/check results observed by specialist |
| `timestamp` | string | yes | ISO-8601 |

## Finding Object

| Field | Type | Required |
|---|---|---|
| `id` | string | yes |
| `severity` | string (`low`/`medium`/`high`/`critical`) | yes |
| `summary` | string | yes |
| `evidence` | array<string> | yes |
| `impact` | string | yes |

## Recommendation Object

| Field | Type | Required |
|---|---|---|
| `id` | string | yes |
| `action` | string | yes |
| `priority` | string (`now`/`next`/`later`) | yes |
| `maps_to_findings` | array<string> | yes |
| `reversible` | boolean | yes |

## Risk Object

| Field | Type | Required |
|---|---|---|
| `id` | string | yes |
| `category` | string | yes |
| `severity` | string | yes |
| `mitigation` | string | yes |

## Artifacts Object Contract

`artifacts` may include:
- `target_tree` (object): proposed structure tree
- `patches` (array<object>): patch metadata
- `notes` (array<string>): concise constraints/assumptions
- `next_actions` (array<string>): immediate steps

## Merge Semantics

Orchestrator merge order:
1. safety
2. correctness
3. reversibility
4. simplicity
5. user preference
6. style

Rules:
- Higher-priority conflicts always win.
- Equal-priority conflicts resolved by higher confidence.
- If confidence ties, choose more reversible recommendation.
- Contradictory `critical` findings force `propose` mode and request clarification/mitigation.

## Error and Null Handling

- Missing required field: payload rejected, specialist status marked `error`.
- Empty `findings` with `status=ok`: accepted only if `checks` shows evidence of evaluation.
- `confidence` outside range: clamp rejected; payload invalid.
- Any parse failure: specialist result excluded from merge and logged.

## Minimum Validation Before Final Response

Before orchestrator emits unified output:
- At least one successful specialist payload in scope.
- All included payloads pass required field checks.
- Conflict policy applied and documented.
- Final output includes:
  - selected mode (`advice`/`propose`/`apply`)
  - artifact summary
  - one immediate next action

## Normalized Example Payload

```json
{
  "agent_id": "audit",
  "task_scope": "Assess existing module structure and propose safe refactor sequence",
  "status": "warning",
  "findings": [
    {
      "id": "F-001",
      "severity": "high",
      "summary": "Service options are duplicated across host and shared module",
      "evidence": ["hosts/lotus/configuration.nix", "modules/services/default.nix"],
      "impact": "Increases drift risk and unsafe edits"
    }
  ],
  "recommendations": [
    {
      "id": "R-001",
      "action": "Move duplicated options into shared service module and keep host overrides minimal",
      "priority": "now",
      "maps_to_findings": ["F-001"],
      "reversible": true
    }
  ],
  "confidence": 0.87,
  "risks": [
    {
      "id": "K-001",
      "category": "regression",
      "severity": "medium",
      "mitigation": "Apply as patch set in propose mode and run validation gates before apply"
    }
  ],
  "artifacts": {
    "target_tree": {
      "modules": {
        "services": ["default.nix"],
        "roles": ["default.nix"]
      }
    },
    "patches": [
      {
        "id": "P-001",
        "path": "patches/001-service-dedup.patch"
      }
    ],
    "notes": ["Preserve existing host-level identity settings"],
    "next_actions": ["Review patch P-001"]
  },
  "checks": {
    "flake_check_required": true,
    "fmt_required": true
  },
  "timestamp": "2026-04-19T00:00:00-10:00"
}
```
