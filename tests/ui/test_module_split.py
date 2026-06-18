from __future__ import annotations

from typing import TYPE_CHECKING
from unittest import TestCase

from linkup.ui.mock import MockDataProvider
from linkup.ui.state import AppStateMachine
from linkup.ui.view_model import AppViewModel

if TYPE_CHECKING:
    from linkup.ui.port import DataProvider


class TestModuleSplit(TestCase):
    def test_mock_provider_exposes_data_provider_contract(self) -> None:
        provider: DataProvider = MockDataProvider()

        self.assertTrue(provider.has_user_profile())
        self.assertEqual(provider.get_user_profile().nickname, "김동민")

    def test_view_model_uses_initial_provider_state(self) -> None:
        self.assertEqual(AppViewModel(MockDataProvider()).screen, "dashboard")
        self.assertEqual(
            AppViewModel(MockDataProvider(has_profile=False)).screen,
            "onboarding",
        )

    def test_state_machine_initial_screen_depends_on_profile(self) -> None:
        self.assertEqual(
            AppStateMachine(has_profile=True).state.screen_key,
            "dashboard",
        )
        self.assertEqual(
            AppStateMachine(has_profile=False).state.screen_key,
            "onboarding",
        )
