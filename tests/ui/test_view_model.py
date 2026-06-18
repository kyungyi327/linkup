from __future__ import annotations

import pytest

from linkup.ui.constants import FATIGUE_MAX, MENTAL_CONDITION_MAX
from linkup.ui.mock import MockDataProvider
from linkup.ui.view_model import AppViewModel


def test_view_model_uses_initial_provider_state() -> None:
    assert AppViewModel(MockDataProvider()).screen == "dashboard"
    assert AppViewModel(MockDataProvider(has_profile=False)).screen == "onboarding"


def test_dashboard_and_condition_save_clamp_and_filter_values() -> None:
    provider = MockDataProvider()
    view_model = AppViewModel(provider)
    emissions: list[str] = []
    view_model.changed.connect(lambda: emissions.append(view_model.screen))

    dashboard = view_model.dashboard
    assert dashboard["greeting"] == "안녕하세요, 김동민님"
    assert dashboard["conditionStatus"] == "미입력"
    assert dashboard["conditionEntered"] is False
    assert dashboard["completionRate"] == "86%"

    view_model.open_condition()
    view_model.save_condition(
        mental_condition_score=99,
        outdoor_hours=1.5,
        fatigue_by_part={"neck": 99, "wrist": 0, "invalid": 7},
    )

    saved_log = provider.get_today_log()
    assert saved_log is not None
    assert saved_log.mental_condition_score == MENTAL_CONDITION_MAX
    assert saved_log.outdoor_hours == 1.5
    assert saved_log.fatigue_by_part == {"neck": FATIGUE_MAX, "wrist": 1}
    assert view_model.screen == "dashboard"
    assert view_model.dashboard["conditionStatus"] == "보통"
    assert "컨디션 10/10" in str(view_model.dashboard["conditionDetail"])
    assert emissions == ["daily_log", "dashboard"]


def test_condition_defaults_when_log_is_missing() -> None:
    condition = AppViewModel(MockDataProvider()).condition

    assert condition["mentalConditionScore"] == 5
    assert condition["outdoorHours"] == "1.0"
    assert all(value == 3 for value in condition["fatigueByPart"].values())


def test_profile_defaults_and_save_from_onboarding() -> None:
    provider = MockDataProvider(has_profile=False)
    view_model = AppViewModel(provider)
    assert view_model.profile["gender"] == "남"

    view_model.save_profile(
        nickname="",
        birth_year=1999,
        gender="여",
        pain_points=["neck", "invalid"],
        pushup_max=20,
        plank_max_sec=90,
        squat_max=40,
        height="",
        weight="",
    )

    saved_profile = provider.get_user_profile()
    assert view_model.screen == "dashboard"
    assert saved_profile.nickname == "김동민"
    assert saved_profile.birth_year == 1999
    assert saved_profile.gender == "female"
    assert saved_profile.pain_points == ["neck"]
    assert saved_profile.pushup_max == 20
    assert saved_profile.plank_max_sec == 90
    assert saved_profile.squat_max == 40
    assert saved_profile.height_cm == 175
    assert saved_profile.weight_kg == 59


def test_profile_save_requires_profile_state() -> None:
    view_model = AppViewModel(MockDataProvider())

    with pytest.raises(RuntimeError, match="profile state is required"):
        view_model.save_profile(
            nickname="사용자",
            birth_year=2000,
            gender="남",
            pain_points=["neck"],
            pushup_max=1,
            plank_max_sec=1,
            squat_max=1,
            height="170",
            weight="60",
        )


def test_navigation_methods_require_expected_source_state() -> None:
    view_model = AppViewModel(MockDataProvider())

    with pytest.raises(RuntimeError, match="routine preview state is required"):
        view_model.start_session()

    view_model.open_history()
    assert view_model.screen == "history"
    view_model.back_to_dashboard()
    assert view_model.screen == "dashboard"

    view_model.open_profile()
    assert view_model.screen == "profile_edit"
    view_model.back_to_dashboard()
    assert view_model.screen == "dashboard"

    view_model.open_condition()
    assert view_model.screen == "daily_log"
    view_model.cancel_condition()
    assert view_model.screen == "dashboard"


def test_routine_loading_uses_clamped_available_minutes() -> None:
    provider = MockDataProvider()
    view_model = AppViewModel(provider)

    view_model.begin_routine_load(1)
    assert view_model.screen == "routine_loading"
    assert view_model.loading["message"] == "오늘 컨디션에 맞는 루틴을 준비하고 있어요"

    view_model.complete_routine_load()
    assert view_model.screen == "routine_preview"
    assert provider.last_available_min == 3
    assert view_model.routine["summary"] == "예상 소요 시간: 약 12분"
    assert len(view_model.routine["items"]) == 4


def test_session_flow_records_history_and_completion_summary() -> None:
    provider = MockDataProvider()
    view_model = AppViewModel(provider)
    emissions: list[str] = []
    view_model.changed.connect(lambda: emissions.append(view_model.screen))

    view_model.open_routine()
    assert view_model.screen == "routine_preview"
    view_model.start_session()
    assert view_model.exercise["title"] == "목 측면 스트레칭"

    view_model.request_modified_exercise()
    assert view_model.exercise["title"] == "벽 기대 견갑 스트레칭"

    for _index in range(4):
        view_model.complete_current_exercise()

    assert view_model.screen == "complete"
    assert provider.history_events == [
        ("session-1", "ex-1", True),
        ("session-1", "ex-2", True),
        ("session-1", "ex-3", True),
        ("session-1", "ex-4", True),
    ]
    assert view_model.complete["duration"] == "12분"
    assert view_model.complete["completedCount"] == "4개"

    view_model.finish_session("힘들었어요", "조금 있었어요", "메모")

    assert view_model.screen == "dashboard"
    assert provider.get_session_list()[0].difficulty_feedback == "힘들었어요"
    assert provider.get_session_list()[0].pain_feedback == "조금 있었어요"
    assert provider.get_session_list()[0].memo == "메모"
    assert emissions[-1] == "dashboard"


def test_history_formats_stats_and_rows() -> None:
    history = AppViewModel(MockDataProvider()).history

    assert history["completionRate"] == "86%"
    assert history["streak"] == "8일"
    assert history["totalSessions"] == "24회"
    assert history["totalHours"] == "5.2h"
    assert len(history["rows"]) == 3
    assert history["rows"][0]["duration"] == "11분"
