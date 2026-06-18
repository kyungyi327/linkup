from __future__ import annotations

from datetime import date

from linkup.ui.constants import (
    BODY_PART_LABEL_TO_KEY,
    BODY_PARTS,
    CURRENT_YEAR,
    FATIGUE_MAX,
    FATIGUE_PART_KEYS,
    GENDER_LABELS,
    GENDER_VALUES,
    MENTAL_CONDITION_MAX,
    PAIN_OPTIONS,
)


def test_body_part_derived_constants_match_source_tuple() -> None:
    expected_label_to_key = {label: key for label, key, _prefix in BODY_PARTS}

    assert BODY_PART_LABEL_TO_KEY == expected_label_to_key
    assert FATIGUE_PART_KEYS == expected_label_to_key
    assert PAIN_OPTIONS == tuple(label for label, _key, _prefix in BODY_PARTS)
    assert len(PAIN_OPTIONS) == len({key for _label, key, _prefix in BODY_PARTS})


def test_gender_maps_are_bidirectional_for_supported_labels() -> None:
    assert GENDER_LABELS == {"male": "남", "female": "여"}
    assert GENDER_VALUES["남"] == "male"
    assert GENDER_VALUES["여"] == "female"
    assert GENDER_VALUES["male"] == "male"
    assert GENDER_VALUES["female"] == "female"


def test_ui_numeric_limits_and_current_year() -> None:
    assert MENTAL_CONDITION_MAX == 10
    assert FATIGUE_MAX == 10
    assert CURRENT_YEAR == date.today().year
