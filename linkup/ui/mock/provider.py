from __future__ import annotations

from linkup.ui.port import (
    DailyLog,
    DataProvider,
    Exercise,
    RecentStats,
    Routine,
    SessionRecord,
    SessionSummary,
    UserProfile,
)


class MockDataProvider(DataProvider):
    def __init__(self, *, has_profile: bool = True) -> None:
        self._profile = (
            UserProfile(
                nickname="김동민",
                birth_year=2002,
                gender="male",
                pain_points=["neck", "shoulder"],
                pushup_max=12,
                plank_max_sec=60,
                squat_max=30,
                height_cm=175,
                weight_kg=59,
            )
            if has_profile
            else None
        )
        self._today_log: DailyLog | None = None
        self._routine = Routine(
            items=[
                Exercise(
                    "ex-1",
                    "목 측면 스트레칭",
                    "승모근, 목빗근",
                    "30초x2",
                    "낮음",
                    "천천히 좌우로 기울입니다.",
                ),
                Exercise(
                    "ex-2",
                    "견갑골 후인 스트레칭",
                    "승모근, 능형근",
                    "10회x2",
                    "낮음",
                    "어깨를 뒤로 당기고 모읍니다.",
                    "ex-2-easy",
                ),
                Exercise(
                    "ex-3",
                    "고양이-소 자세",
                    "척추 기립근",
                    "10회x2",
                    "보통",
                    "등을 말았다 펴세요.",
                ),
                Exercise(
                    "ex-4",
                    "호흡 이완 운동",
                    "횡격막",
                    "1분",
                    "낮음",
                    "깊게 들이쉬고 천천히 내쉽니다.",
                ),
            ],
            expected_minutes=12,
        )
        self._session_records: list[SessionRecord] = [
            SessionRecord("05/17 (오늘)", 4, 11, "적당해요", "없음", "목 가동성 좋음"),
            SessionRecord("05/16", 4, 13, "적당해요", "없음", ""),
            SessionRecord("05/15", 3, 9, "쉬웠어요", "조금", "허리 부담 낮춤"),
        ]
        self._current_session_id = ""
        self.last_available_min = 0
        self.history_events: list[tuple[str, str, bool]] = []

    def has_user_profile(self) -> bool:
        return self._profile is not None

    def get_user_profile(self) -> UserProfile:
        assert self._profile is not None
        return self._profile

    def save_user_profile(self, profile: UserProfile) -> None:
        self._profile = profile

    def get_today_log(self) -> DailyLog | None:
        return self._today_log

    def upsert_today_log(self, log: DailyLog) -> None:
        self._today_log = log

    def get_modified_exercise(self, ex_id: str) -> Exercise:
        return Exercise(
            ex_id="ex-2-easy",
            name="벽 기대 견갑 스트레칭",
            target_muscle="승모근",
            duration_text="8회x2",
            intensity="낮음",
            guide="벽에 기대어 천천히 수행하세요.",
        )

    def generate_routine(self, available_min: int) -> Routine:
        self.last_available_min = available_min
        return self._routine

    def get_recent_stats(self) -> RecentStats:
        return RecentStats(streak_days=8, workout_days_7d=6, total_sessions=24, total_hours=5.2)

    def get_session_list(self) -> list[SessionRecord]:
        return list(self._session_records)

    def start_session(self, routine: Routine) -> str:
        self._current_session_id = "session-1"
        return self._current_session_id

    def record_history(self, session_id: str, ex_id: str, completed: bool) -> None:
        self.history_events.append((session_id, ex_id, completed))

    def end_session(self, session_id: str, difficulty: str, pain: str, memo: str) -> SessionSummary:
        latest = SessionRecord("05/17 (오늘)", len(self._routine.items), 11, difficulty, pain, memo)
        if self._session_records:
            self._session_records[0] = latest
        return SessionSummary(duration_min=11, completed_count=len(self._routine.items), streak_days=8)
