from __future__ import annotations

from linkup.ui.port import (
    AnalysisPort,
    DailyLog,
    DataCollectionPort,
    DataProvider,
    Exercise,
    ExerciseContentPort,
    RecentStats,
    Routine,
    SessionRecord,
    SessionRecordPort,
    SessionSummary,
    UserProfile,
)


def test_port_dataclasses_store_values() -> None:
    profile = UserProfile("사용자", 2000, "male", ["neck"], 10, 30, 20, 175, 70)
    log = DailyLog(7, 1.5, {"neck": 3})
    exercise = Exercise("ex-1", "운동", "목", "30초", "낮음", "가이드", "ex-1-easy")
    routine = Routine([exercise], 5)
    stats = RecentStats(2, 3, 4, 5.5)
    summary = SessionSummary(11, 4, 8)
    record = SessionRecord("오늘", 4, 11, "적당해요", "없음", "메모")

    assert profile.nickname == "사용자"
    assert log.fatigue_by_part == {"neck": 3}
    assert exercise.modified_ex_id == "ex-1-easy"
    assert routine.items == [exercise]
    assert stats.total_hours == 5.5
    assert summary.completed_count == 4
    assert record.memo == "메모"


def test_data_provider_protocol_combines_all_port_methods() -> None:
    collection_methods = {
        "has_user_profile",
        "get_user_profile",
        "save_user_profile",
        "get_today_log",
        "upsert_today_log",
    }
    content_methods = {"get_modified_exercise"}
    analysis_methods = {"generate_routine", "get_recent_stats", "get_session_list"}
    session_methods = {
        "start_session",
        "record_history",
        "end_session",
    }
    provider_methods = {
        *collection_methods,
        *content_methods,
        *analysis_methods,
        *session_methods,
    }

    assert collection_methods.issubset(set(dir(DataCollectionPort)))
    assert provider_methods.issubset(set(dir(DataProvider)))
    assert content_methods.issubset(set(dir(ExerciseContentPort)))
    assert analysis_methods.issubset(set(dir(AnalysisPort)))
    assert session_methods.issubset(set(dir(SessionRecordPort)))
