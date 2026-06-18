from __future__ import annotations

from linkup.ui.mock import MockDataProvider
from linkup.ui.port import DailyLog, UserProfile


def test_mock_provider_exposes_data_provider_contract() -> None:
    provider = MockDataProvider()

    assert provider.has_user_profile()
    assert provider.get_user_profile().nickname == "김동민"


def test_mock_provider_can_start_without_profile_and_save_one() -> None:
    provider = MockDataProvider(has_profile=False)
    profile = UserProfile(
        nickname="새 사용자",
        birth_year=2001,
        gender="female",
        pain_points=["neck"],
        pushup_max=10,
        plank_max_sec=30,
        squat_max=20,
        height_cm=165,
        weight_kg=55,
    )

    assert not provider.has_user_profile()
    provider.save_user_profile(profile)

    assert provider.has_user_profile()
    assert provider.get_user_profile() is profile


def test_mock_provider_stores_today_log() -> None:
    provider = MockDataProvider()
    log = DailyLog(
        mental_condition_score=8,
        outdoor_hours=2.0,
        fatigue_by_part={"neck": 4},
    )

    assert provider.get_today_log() is None
    provider.upsert_today_log(log)

    assert provider.get_today_log() is log


def test_mock_provider_generates_routine_and_modified_exercise() -> None:
    provider = MockDataProvider()

    routine = provider.generate_routine(7)
    modified = provider.get_modified_exercise("ex-2")

    assert provider.last_available_min == 7
    assert routine.expected_minutes == 12
    assert len(routine.items) == 4
    assert modified.ex_id == "ex-2-easy"
    assert modified.name == "벽 기대 견갑 스트레칭"


def test_mock_provider_records_and_ends_session() -> None:
    provider = MockDataProvider()
    routine = provider.generate_routine(10)
    session_id = provider.start_session(routine)

    provider.record_history(session_id, "ex-1", True)
    summary = provider.end_session(session_id, "힘들었어요", "조금", "메모")

    assert session_id == "session-1"
    assert provider.history_events == [("session-1", "ex-1", True)]
    assert summary.duration_min == 11
    assert summary.completed_count == 4
    assert summary.streak_days == 8
    assert provider.get_session_list()[0].difficulty_feedback == "힘들었어요"
    assert provider.get_session_list()[0].memo == "메모"


def test_mock_provider_returns_copied_session_list() -> None:
    provider = MockDataProvider()
    rows = provider.get_session_list()

    rows.clear()

    assert len(provider.get_session_list()) == 3
