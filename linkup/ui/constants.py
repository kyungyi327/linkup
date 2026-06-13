from __future__ import annotations

from datetime import date
from importlib.resources import files

ASSET_FILES = files("linkup.ui.assets")
FORM_FILES = files("linkup.ui.forms")
MENTAL_CONDITION_MAX = 10
FATIGUE_MAX = 10
GENDER_LABELS = {"male": "남", "female": "여"}
GENDER_VALUES = {"남": "male", "여": "female", "male": "male", "female": "female"}
BODY_PARTS = (
    ("목", "neck", "fatigueNeckOption_"),
    ("어깨", "shoulder", "fatigueShoulderOption_"),
    ("허리", "lower_back", "fatigueLowerBackOption_"),
    ("손목", "wrist", "fatigueWristOption_"),
    ("무릎", "knee", "fatigueKneeOption_"),
    ("발목", "ankle", "fatigueAnkleOption_"),
)
BODY_PART_LABEL_TO_KEY = {label: key for label, key, _prefix in BODY_PARTS}
PAIN_OPTIONS = tuple(label for label, _key, _prefix in BODY_PARTS)
FATIGUE_PART_KEYS = {label: key for label, key, _prefix in BODY_PARTS}
CURRENT_YEAR = date.today().year
