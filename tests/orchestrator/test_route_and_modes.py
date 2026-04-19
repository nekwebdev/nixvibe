from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from nixvibe.orchestrator.modes import resolve_mode
from nixvibe.orchestrator.policy_loader import load_policy
from nixvibe.orchestrator.router import select_route
from nixvibe.orchestrator.types import Mode, OrchestrationRequest, RepoContext, Route


class TestRouteAndModes(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.policy = load_policy(ROOT / ".agents/carl/nixvibe-domain.md")

    def test_route_prefers_init_for_greenfield_scaffold(self) -> None:
        request = OrchestrationRequest(
            user_input="Need a new scaffold for first-time greenfield host profile setup.",
        )
        context = RepoContext(
            existing_config_present=False,
            usable_nix_structure_present=False,
            request_is_change=False,
            repository_state="known",
        )
        decision = select_route(request, context, self.policy)

        self.assertEqual(decision.route, Route.INIT)
        self.assertFalse(decision.needs_clarification)

    def test_route_prefers_audit_for_existing_config_changes(self) -> None:
        request = OrchestrationRequest(
            user_input="Please refactor and modernize my existing NixOS modules.",
        )
        context = RepoContext(
            existing_config_present=True,
            usable_nix_structure_present=True,
            request_is_change=True,
            repository_state="known",
        )
        decision = select_route(request, context, self.policy)

        self.assertEqual(decision.route, Route.AUDIT)
        self.assertFalse(decision.needs_clarification)

    def test_route_flags_ambiguous_unknown_repo_context(self) -> None:
        request = OrchestrationRequest(user_input="Help me improve this setup.")
        context = RepoContext()
        decision = select_route(request, context, self.policy)

        self.assertEqual(decision.route, Route.INIT)
        self.assertTrue(decision.needs_clarification)
        self.assertGreaterEqual(len(decision.clarification_questions), 1)
        self.assertLessEqual(len(decision.clarification_questions), 4)

    def test_audit_defaults_to_propose_mode(self) -> None:
        decision = resolve_mode(
            route=Route.AUDIT,
            requested_mode=None,
            explicit_apply_opt_in=False,
        )
        self.assertEqual(decision.mode, Mode.PROPOSE)
        self.assertFalse(decision.write_allowed)
        self.assertTrue(decision.requires_confirmation)

    def test_apply_requires_explicit_opt_in(self) -> None:
        no_opt_in = resolve_mode(
            route=Route.AUDIT,
            requested_mode=Mode.APPLY,
            explicit_apply_opt_in=False,
        )
        yes_opt_in = resolve_mode(
            route=Route.AUDIT,
            requested_mode=Mode.APPLY,
            explicit_apply_opt_in=True,
        )

        self.assertEqual(no_opt_in.mode, Mode.PROPOSE)
        self.assertFalse(no_opt_in.write_allowed)
        self.assertEqual(yes_opt_in.mode, Mode.APPLY)
        self.assertTrue(yes_opt_in.write_allowed)


if __name__ == "__main__":
    unittest.main()

