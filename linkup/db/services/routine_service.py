"""
services/routine_service.py
운동 routine 생성 비즈니스 로직.

DAO 를 조합해서 사용한다. SQL 은 직접 다루지 않는다.
generate() 의 동작 선택 규칙은 초기 버전이며, 추후 팀 협의로 조정 예정.
"""

from pathlib import Path

from linkup.db.constants import BodyPart
from linkup.db.models import DailyLog, ExerciseLibraryItem, UserProfile
from linkup.db.repositories import (
    DailyLogRepo,
    ExerciseLibraryRepo,
    UserProfileRepo,
)

# 초기 규칙용 상수
_FATIGUE_AVOID_THRESHOLD = 7  # 부위별 피로도 이 값 이상이면 회피
_AVG_SEC_PER_EXERCISE = 90  # 동작 1개 평균 소요(초) 가정


class RoutineService:
    def __init__(self, db_path: Path | None = None) -> None:
        self._user_repo = UserProfileRepo(db_path)
        self._log_repo = DailyLogRepo(db_path)
        self._lib_repo = ExerciseLibraryRepo(db_path)

    def generate(self, date: str, available_min: int) -> list[ExerciseLibraryItem]:
        """입력한 가용 분에 맞춰 동작 list 반환.

        초기 규칙:
          - 회피 부위 = 프로필 통증 부위 ∪ 오늘 피로도 높은 부위
          - 난이도 상한 = 체력 측정값에서 추정 (없으면 보통)
          - 가용 분 / 평균 동작 시간 만큼 동작 선택
        """
        profile = self._user_repo.get()
        log = self._log_repo.get(date)

        avoid = self._avoid_parts(profile, log)
        max_diff = self._max_difficulty(profile)

        candidates = self._lib_repo.query(
            max_difficulty=max_diff,
            avoid_body_parts=avoid,
        )

        target_count = max(1, (available_min * 60) // _AVG_SEC_PER_EXERCISE)
        return candidates[:target_count]

    def _avoid_parts(self, profile: UserProfile | None, log: DailyLog | None) -> list[BodyPart]:
        avoid: set[BodyPart] = set()
        if profile and profile.pain_points:
            avoid.update(profile.pain_points)
        if log and log.fatigue_by_part:
            for part, level in log.fatigue_by_part.items():
                if level >= _FATIGUE_AVOID_THRESHOLD:
                    avoid.add(part)
        return list(avoid)

    @staticmethod
    def _max_difficulty(profile: UserProfile | None) -> int:
        """체력 측정값으로 난이도 상한(1~3) 추정. 측정값 없으면 보통(2)."""
        if not profile:
            return 2
        pushup = profile.pushup_max
        if pushup is None:
            return 2
        if pushup < 10:
            return 1
        if pushup < 30:
            return 2
        return 3
