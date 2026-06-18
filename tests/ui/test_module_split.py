from __future__ import annotations

from typing import TYPE_CHECKING

from linkup.ui.mock import MockDataProvider
from linkup.ui.state import AppStateMachine
from linkup.ui.view_model import AppViewModel

if TYPE_CHECKING:
    from linkup.ui.port import DataProvider


def test_mock_provider_exposes_data_provider_contract() -> None:
    provider: DataProvider = MockDataProvider()

    assert provider.has_user_profile()
    assert provider.get_user_profile().nickname == "김동민"


def test_view_model_uses_initial_provider_state() -> None:
    assert AppViewModel(MockDataProvider()).screen == "dashboard"
    assert AppViewModel(MockDataProvider(has_profile=False)).screen == "onboarding"


def test_state_machine_initial_screen_depends_on_profile() -> None:
    assert AppStateMachine(has_profile=True).state.screen_key == "dashboard"
    assert AppStateMachine(has_profile=False).state.screen_key == "onboarding"
