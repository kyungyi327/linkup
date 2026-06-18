"""
constants.py
Team LinkUp — Shared Enum Definitions

All team members MUST reference this single file.
- Frontend: dropdown menus render options from these enums.
- Backend : Pydantic / dataclass validators check against these values.
- Database: TEXT columns store these exact string values.

Usage:
    from linkup.db.constants import (
        BodyPart, ExerciseCategory, Scene, Gender, JobType, Goal, SessionStatus,
    )

    # Validate user input
    assert "neck" in BodyPart.values()

    # Iterate for UI dropdowns
    for part in BodyPart:
        print(part.value, part.label_ko)
"""

from enum import Enum
from typing import List


# ------------------------------------------------------------------
# Base class with common helpers
# ------------------------------------------------------------------
class LabeledEnum(str, Enum):
    """Enum with a Korean label for UI rendering."""

    def __new__(cls, value: str, label_ko: str = ""):
        obj = str.__new__(cls, value)
        obj._value_ = value
        obj.label_ko = label_ko
        return obj

    @classmethod
    def values(cls) -> List[str]:
        return [member.value for member in cls]

    @classmethod
    def choices_ko(cls) -> List[tuple]:
        """Returns [(value, korean_label), ...] for UI dropdowns."""
        return [(member.value, member.label_ko) for member in cls]


# ------------------------------------------------------------------
# Body parts  (pain_points & contraindications & fatigue_by_part keys)
# ------------------------------------------------------------------
class BodyPart(LabeledEnum):
    NECK       = ("neck",       "목")
    SHOULDER   = ("shoulder",   "어깨")
    UPPER_BACK = ("upper_back", "등 상부")
    LOWER_BACK = ("lower_back", "허리")
    WRIST      = ("wrist",      "손목")
    KNEE       = ("knee",       "무릎")
    ANKLE      = ("ankle",      "발목")
    HIP        = ("hip",        "고관절")
    ELBOW      = ("elbow",      "팔꿈치")
    EYE        = ("eye",        "눈")


# ------------------------------------------------------------------
# Exercise categories
# ------------------------------------------------------------------
class ExerciseCategory(LabeledEnum):
    STRETCH    = ("stretch",    "스트레칭")
    STRENGTH   = ("strength",   "근력 강화")
    CARDIO     = ("cardio",     "유산소")
    RELAXATION = ("relaxation", "이완/명상")
    MOBILITY   = ("mobility",   "관절 가동성")


# ------------------------------------------------------------------
# Scenes
# ------------------------------------------------------------------
class Scene(LabeledEnum):
    OFFICE = ("office", "사무실")
    HOME   = ("home",   "집")


# ------------------------------------------------------------------
# Gender  (User_Profile.gender)
# ------------------------------------------------------------------
class Gender(LabeledEnum):
    MALE   = ("male",   "남")
    FEMALE = ("female", "여")


# ------------------------------------------------------------------
# Job types
# ------------------------------------------------------------------
class JobType(LabeledEnum):
    IT            = ("it",            "IT/개발")
    OFFICE_WORKER = ("office_worker", "사무직")
    STUDENT       = ("student",       "학생")
    MANUAL_LABOR  = ("manual_labor",  "현장직/노동직")
    OTHER         = ("other",         "기타")


# ------------------------------------------------------------------
# Goals  (User_Profile.goals, CSV, INPUT.md 2-2)
# ------------------------------------------------------------------
class Goal(LabeledEnum):
    MUSCLE_GAIN   = ("muscle_gain",   "근육량 증가")
    DIET          = ("diet",          "다이어트")
    LIFESTYLE     = ("lifestyle",     "생활 습관 개선")
    BASIC_FITNESS = ("basic_fitness", "기초 체력 증가")
    NONE          = ("none",          "없음")


# ------------------------------------------------------------------
# Session status  (Workout_History.status, INPUT.md 5)
# ------------------------------------------------------------------
class SessionStatus(LabeledEnum):
    PENDING   = ("pending",   "대기")
    COMPLETED = ("completed", "완료")
    SKIPPED   = ("skipped",   "건너뜀")
    ABORTED   = ("aborted",   "중단됨")


# ------------------------------------------------------------------
# Numeric range constants
# ------------------------------------------------------------------
DIFFICULTY_MIN = 1
DIFFICULTY_MAX = 3
DIFFICULTY_LABELS_KO = {1: "낮음", 2: "보통", 3: "높음"}

# 운동 데이터(target_muscle) 영문 부위 → 한글 표시 라벨. 미지값은 원문 fallback.
TARGET_MUSCLE_LABELS_KO = {
    "neck": "목",
    "shoulders": "어깨",
    "back": "등",
    "waist": "허리/코어",
    "chest": "가슴",
    "upper arms": "상완",
    "lower arms": "하완",
    "upper legs": "허벅지",
    "lower legs": "종아리",
    "cardio": "유산소",
}

# mental_condition_score (수면+기분+스트레스 통합 점수)
MENTAL_CONDITION_MIN = 0
MENTAL_CONDITION_MAX = 10

# outdoor_hours (INPUT.md 3-2-1)
OUTDOOR_HOURS_MIN = 0
OUTDOOR_HOURS_MAX = 16

# goal_duration_weeks (INPUT.md 2-3)
GOAL_DURATION_MIN = 1
GOAL_DURATION_MAX = 24

# weekly_frequency (INPUT.md 2-4)
WEEKLY_FREQUENCY_MIN = 1
WEEKLY_FREQUENCY_MAX = 7

# fatigue_by_part per-part value range (INPUT.md 3-2-2)
FATIGUE_PART_MIN = 1
FATIGUE_PART_MAX = 10


# ------------------------------------------------------------------
# Validation helpers
# ------------------------------------------------------------------
def validate_pain_points(csv_string: str) -> bool:
    """Validate that every item in a comma-separated pain_points
    string is a valid BodyPart value."""
    if not csv_string or csv_string.strip() == "":
        return True
    parts = [p.strip() for p in csv_string.split(",") if p.strip()]
    valid = set(BodyPart.values())
    return all(p in valid for p in parts)


def validate_goals(csv_string: str) -> bool:
    """Validate that every item in a comma-separated goals string is a valid Goal value."""
    if not csv_string or csv_string.strip() == "":
        return True
    parts = [p.strip() for p in csv_string.split(",") if p.strip()]
    valid = set(Goal.values())
    return all(p in valid for p in parts)


def parse_csv(csv_string: str) -> List[str]:
    """Split a comma-separated TEXT field into a list."""
    if not csv_string or csv_string.strip() == "":
        return []
    return [item.strip() for item in csv_string.split(",") if item.strip()]


def join_csv(items: List[str]) -> str:
    """Inverse of parse_csv: join a list into a comma-separated string."""
    return ",".join(item for item in items if item)
