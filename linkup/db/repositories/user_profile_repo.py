"""
repositories/user_profile_repo.py
User_Profile 테이블 DAO. 로컬 단일 사용자라 항상 id=1 한 행.
"""

from pathlib import Path

from linkup.db.models import UserProfile

from ._mapper import row_to_user_profile, user_profile_to_params
from .db import get_connection


class UserProfileRepo:
    def __init__(self, db_path: Path | None = None) -> None:
        self._db_path = db_path

    def has_profile(self) -> bool:
        """id=1 행이 있고 nickname 이 채워져 있으면 작성 완료로 본다."""
        with get_connection(self._db_path) as conn:
            row = conn.execute("SELECT nickname FROM User_Profile WHERE id = 1").fetchone()
        return row is not None and row["nickname"] is not None

    def get(self) -> UserProfile | None:
        with get_connection(self._db_path) as conn:
            row = conn.execute("SELECT * FROM User_Profile WHERE id = 1").fetchone()
        return row_to_user_profile(row) if row else None

    def save(self, profile: UserProfile) -> None:
        """id=1 행 UPSERT. updated_at 은 트리거가 갱신."""
        params = user_profile_to_params(profile)
        params["id"] = 1
        with get_connection(self._db_path) as conn:
            conn.execute(
                """
                INSERT INTO User_Profile
                    (id, nickname, avatar_path, gender, birth_year, height_cm,
                     weight_kg, job_type, goals, goal_duration_weeks,
                     weekly_frequency, pain_points, pushup_max, plank_max_sec,
                     squat_max, notification_enabled)
                VALUES
                    (:id, :nickname, :avatar_path, :gender, :birth_year, :height_cm,
                     :weight_kg, :job_type, :goals, :goal_duration_weeks,
                     :weekly_frequency, :pain_points, :pushup_max, :plank_max_sec,
                     :squat_max, :notification_enabled)
                ON CONFLICT(id) DO UPDATE SET
                    nickname=:nickname, avatar_path=:avatar_path, gender=:gender,
                    birth_year=:birth_year, height_cm=:height_cm, weight_kg=:weight_kg,
                    job_type=:job_type, goals=:goals,
                    goal_duration_weeks=:goal_duration_weeks,
                    weekly_frequency=:weekly_frequency, pain_points=:pain_points,
                    pushup_max=:pushup_max, plank_max_sec=:plank_max_sec,
                    squat_max=:squat_max, notification_enabled=:notification_enabled
                """,
                params,
            )
            conn.commit()
