"""
repositories/  (DAO layer)

각 모듈은 한 테이블의 SQL 접근을 담당한다. 비즈니스 코드는 Repo 클래스를
import 해서 models.py 의 dataclass 로 데이터를 주고받는다.
sqlite3.Row <-> dataclass 변환은 _mapper.py 가 담당.
"""

from .app_settings_repo import AppSettingsRepo
from .daily_log_repo import DailyLogRepo
from .db import get_connection, init_db
from .exercise_library_repo import ExerciseLibraryRepo
from .stats_repo import DailyHistorySummary, RecentStats, StatsRepo
from .user_profile_repo import UserProfileRepo
from .workout_history_repo import WorkoutHistoryRepo
from .workout_session_repo import WorkoutSessionRepo

__all__ = [
    "get_connection",
    "init_db",
    "UserProfileRepo",
    "DailyLogRepo",
    "WorkoutSessionRepo",
    "WorkoutHistoryRepo",
    "ExerciseLibraryRepo",
    "StatsRepo",
    "RecentStats",
    "DailyHistorySummary",
    "AppSettingsRepo",
]
