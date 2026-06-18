"""
linkup/db/provider.py
SqliteDataProvider — UI 의 DataProvider(port.py) 계약을 SQLite DB 로 구현.

UI 는 port.py 의 DTO/메서드만 알고, 내부 DB 구조(Repo/models)는 모른다.
이 어댑터가 port DTO <-> DB DTO 변환 + Repo 호출을 담당한다.
"""

from __future__ import annotations

from datetime import date as _date, datetime

from linkup.ui import port
from linkup.db.repositories import (
    UserProfileRepo,
    DailyLogRepo,
    WorkoutSessionRepo,
    WorkoutHistoryRepo,
    ExerciseLibraryRepo,
    StatsRepo,
    init_db,
)
from linkup.db.services.routine_service import RoutineService
from linkup.db import models
from linkup.db import constants as C


# ------------------------------------------------------------------
# 변환 헬퍼
# ------------------------------------------------------------------
_DIFF_TO_INTENSITY = {1: "낮음", 2: "보통", 3: "높음"}
_INTENSITY_TO_DIFF = {v: k for k, v in _DIFF_TO_INTENSITY.items()}


def _today() -> str:
    return _date.today().isoformat()


def _now_hms() -> str:
    return datetime.now().strftime("%H:%M:%S")


def _duration_text(item: models.ExerciseLibraryItem) -> str:
    """DB 의 sets/reps/duration_sec 를 UI 표시용 텍스트로."""
    if item.default_reps and item.default_reps > 1:
        return f"{item.default_reps}회x{item.default_sets}"
    return f"{item.duration_sec}초x{item.default_sets}"


def _exercise_to_port(item: models.ExerciseLibraryItem, guide: str = "") -> port.Exercise:
    return port.Exercise(
        ex_id=item.ex_id,
        name=item.name,
        target_muscle=", ".join(item.target_muscle),
        duration_text=_duration_text(item),
        intensity=_DIFF_TO_INTENSITY.get(item.difficulty_level, "보통"),
        guide=guide or (item.description or ""),
        modified_ex_id=item.modified_ex_id,
    )


# ------------------------------------------------------------------
# Provider
# ------------------------------------------------------------------
class SqliteDataProvider(port.DataProvider):
    def __init__(self, db_path=None, auto_init: bool = True) -> None:
        self._db_path = db_path
        if auto_init:
            init_db(db_path)
        self._user = UserProfileRepo(db_path)
        self._log = DailyLogRepo(db_path)
        self._session = WorkoutSessionRepo(db_path)
        self._history = WorkoutHistoryRepo(db_path)
        self._lib = ExerciseLibraryRepo(db_path)
        self._stats = StatsRepo(db_path)
        self._routine = RoutineService(db_path)
        # start_session 시 만든 routine 을 기억 (record/end 에서 사용)
        self._cur_session_id: int | None = None
        self._cur_routine: port.Routine | None = None

    # ---------- DataCollectionPort ----------
    def has_user_profile(self) -> bool:
        return self._user.has_profile()

    def get_user_profile(self) -> port.UserProfile:
        p = self._user.get()
        assert p is not None
        return port.UserProfile(
            nickname=p.nickname or "",
            birth_year=p.birth_year,
            gender=p.gender.value if p.gender else None,
            pain_points=[bp.value for bp in p.pain_points],
            pushup_max=p.pushup_max,
            plank_max_sec=p.plank_max_sec,
            squat_max=p.squat_max,
            height_cm=int(p.height_cm) if p.height_cm is not None else None,
            weight_kg=int(p.weight_kg) if p.weight_kg is not None else None,
        )

    def save_user_profile(self, profile: port.UserProfile) -> None:
        existing = self._user.get()
        dto = models.UserProfile(
            id=1,
            nickname=profile.nickname,
            birth_year=profile.birth_year,
            gender=C.Gender(profile.gender) if profile.gender else None,
            height_cm=float(profile.height_cm) if profile.height_cm is not None else None,
            weight_kg=float(profile.weight_kg) if profile.weight_kg is not None else None,
            pain_points=[C.BodyPart(x) for x in profile.pain_points],
            pushup_max=profile.pushup_max,
            plank_max_sec=profile.plank_max_sec,
            squat_max=profile.squat_max,
            # port 에 없는 항목은 기존값 유지 (없으면 기본값)
            job_type=existing.job_type if existing else C.JobType.STUDENT,
            goals=existing.goals if existing else [],
        )
        self._user.save(dto)

    def get_today_log(self) -> port.DailyLog | None:
        log = self._log.get(_today())
        if log is None:
            return None
        return port.DailyLog(
            mental_condition_score=log.mental_condition_score,
            outdoor_hours=log.outdoor_hours,
            fatigue_by_part={bp.value: v for bp, v in log.fatigue_by_part.items()},
        )

    def upsert_today_log(self, log: port.DailyLog) -> None:
        dto = models.DailyLog(
            date=_today(),
            mental_condition_score=log.mental_condition_score,
            outdoor_hours=log.outdoor_hours,
            fatigue_by_part={C.BodyPart(k): v for k, v in log.fatigue_by_part.items()},
        )
        self._log.upsert(dto)

    # ---------- ExerciseContentPort ----------
    def get_modified_exercise(self, ex_id: str) -> port.Exercise:
        # 더 쉬운 대체 동작이 없으면(modified_ex_id 미설정) 원본 동작을 그대로 반환.
        item = self._lib.get_modified(ex_id) or self._lib.get(ex_id)
        assert item is not None
        return _exercise_to_port(item)

    # ---------- AnalysisPort ----------
    def generate_routine(self, available_min: int) -> port.Routine:
        items = self._routine.generate(_today(), available_min)
        port_items = [_exercise_to_port(it) for it in items]
        total_sec = sum(it.duration_sec * (it.default_sets or 1) for it in items)
        return port.Routine(
            items=port_items,
            expected_minutes=max(1, round(total_sec / 60)),
        )

    def get_recent_stats(self) -> port.RecentStats:
        s = self._stats.recent_stats(7)
        return port.RecentStats(
            streak_days=s.streak_days,
            workout_days_7d=s.active_days,
            total_sessions=s.total_chunks,
            total_hours=round(s.total_minutes / 60, 1),
        )

    def get_session_list(self) -> list[port.SessionRecord]:
        out: list[port.SessionRecord] = []
        for d in self._stats.daily_history(50):
            out.append(port.SessionRecord(
                date=d.date,
                exercise_count=d.chunk_count,
                duration_min=d.total_minutes,
                difficulty_feedback="",
                pain_feedback="",
                memo="",
            ))
        return out

    # ---------- SessionRecordPort ----------
    def start_session(self, routine: port.Routine) -> str:
        # 세션은 Daily_Log 가 있어야 생성됨 (TRG-3). 없으면 빈 로그 생성.
        if self._log.get(_today()) is None:
            self._log.upsert(models.DailyLog(date=_today()))
        sid = self._session.start(_today(), None, _now_hms())
        # routine 의 각 동작을 PENDING 으로 기록
        for i, ex in enumerate(routine.items, start=1):
            self._history.create(models.WorkoutHistory(
                session_id=sid,
                ex_id=ex.ex_id,
                seq_order=i,
                status=C.SessionStatus.PENDING,
            ))
        self._cur_session_id = sid
        self._cur_routine = routine
        return str(sid)

    def record_history(self, session_id: str, ex_id: str, completed: bool) -> None:
        # 해당 세션의 history 중 ex_id 매칭되는 행을 찾아 상태 갱신
        rows = self._history.list_by_session(int(session_id))
        for h in rows:
            if h.ex_id == ex_id:
                status = C.SessionStatus.COMPLETED if completed else C.SessionStatus.SKIPPED
                self._history.update_status(h.history_id, status)
                break

    def end_session(
        self, session_id: str, difficulty: str, pain: str, memo: str
    ) -> port.SessionSummary:
        sid = int(session_id)
        # UI 난이도 라벨 (view_model: 쉬웠어요/적당해요/힘들었어요) → 피드백 점수
        fb = {"힘들었어요": -1, "적당해요": 0, "쉬웠어요": 1}.get(difficulty)
        self._session.end(sid, _now_hms(), overall_feedback=fb, memo=memo)
        sess = self._session.get(sid)
        hist = self._history.list_by_session(sid)
        completed = sum(1 for h in hist if h.status == C.SessionStatus.COMPLETED)
        dur_min = round((sess.total_duration_sec or 0) / 60) if sess else 0
        stats = self._stats.recent_stats(7)
        return port.SessionSummary(
            duration_min=dur_min,
            completed_count=completed,
            streak_days=stats.streak_days,
        )
