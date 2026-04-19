---
name: "carl"
description: "Use when tasks need persistent engineering rules, domain memory, or decision logs via CARL. Provides a workflow for CARL v2 MCP tools and carl.json-backed context management."
---

# CARL

CARL stores persistent rules and decisions in `./.carl/carl.json` and exposes MCP tools for domain, rule, and decision management.

## Workflow

1. Inspect domains with `carl_v2_list_domains` and `carl_v2_get_domain`.
2. Add or revise rules with `carl_v2_add_rule`, `carl_v2_remove_rule`, or `carl_v2_replace_rules`.
3. Capture key technical decisions with `carl_v2_log_decision` and search via `carl_v2_search_decisions`.
4. Stage and approve rule proposals with `carl_v2_stage_proposal` and `carl_v2_approve_proposal`.
5. Tune runtime behavior with `carl_v2_get_config` and `carl_v2_update_config`.

## Installed paths

- Rules + decisions: `./.carl/carl.json`
- MCP server: `./.agents/carl/runtime/carl-mcp/`
- MCP registration: `./.codex/config.toml`
