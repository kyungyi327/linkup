from pathlib import Path

import pandas as pd


def process_fitteum_csv(input_csv_path: Path, output_csv_path: Path) -> pd.DataFrame | None:

    try:
        df = pd.read_csv(input_csv_path)
    except FileNotFoundError:
        print("에러: 파일을 찾을 수 없습니다. 경로와 파일명을 다시 확인해 주세요.")
        return None

    # 1. 기구 필터링 (equipment가 'body weight'인 것만 추출)
    if "equipment" in df.columns:
        bodyweight_df = df[df["equipment"].astype(str).str.lower().str.strip() == "body weight"].copy()
    else:
        print("에러: 데이터에 'equipment' 컬럼이 존재하지 않습니다.")
        return None

    # 2. 고유 동작 ID 부여
    bodyweight_df["ex_id"] = range(1, len(bodyweight_df) + 1)

    # ⏱3. 디폴트 운동 시간 20초 부여
    bodyweight_df["duration_sec"] = 20

    # 4. 분산된 운동 방법(instructions) 컬럼 하나로 병합
    instruction_cols = [col for col in bodyweight_df.columns if "instruction" in col.lower()]

    def merge_instructions(row: pd.Series) -> str:
        steps = [
            str(row[col]).strip() for col in instruction_cols if pd.notna(row[col]) and str(row[col]).strip() != ""
        ]
        return " ".join(steps) if steps else ""

    bodyweight_df["instructions"] = bodyweight_df.apply(merge_instructions, axis=1)

    # 5. 운동 카테고리/난이도 자동 마이닝 함수
    def analyze_exercise_details(row: pd.Series) -> pd.Series:
        name_str = str(row.get("name", "")).lower()
        inst_str = str(row.get("instructions", "")).lower()
        search_text = name_str + " " + inst_str

        # A. category 분류 (스트레칭 / 유산소 / 근력)
        if any(word in search_text for word in ["cardio", "jump", "run", "burpee", "jacks", "rope"]):
            category = "유산소"
        elif any(word in search_text for word in ["stretch", "stretching", "yoga", "flexibility", "warm-up"]):
            category = "스트레칭"
        else:
            category = "근력"

        # B. difficulty_level 결정 (초급=1, 중급=2,
        if any(
            word in search_text
            for word in [
                "jump",
                "chin-up",
                "pull-up",
                "single-leg",
                "single leg",
                "inverted",
                "handstand",
                "plyometrics",
                "advanced",
                "explosive",
            ]
        ):
            difficulty_level = 3
        elif any(
            word in search_text
            for word in [
                "stretch",
                "stretching",
                "lie",
                "lying",
                "hold",
                "passive",
                "easy",
            ]
        ):
            difficulty_level = 1
        else:
            difficulty_level = 2

        return pd.Series([category, difficulty_level])

    # 카테고리와 난이도(숫자형) 적용
    bodyweight_df[["category", "difficulty_level"]] = bodyweight_df.apply(analyze_exercise_details, axis=1)

    # 6. 금기 부위(contraindications) 데이터 매핑 (답변사항 2번 반영)
    # target 데이터를 금기 부위 데이터로 활용
    if "target" in bodyweight_df.columns:
        bodyweight_df["contraindications"] = bodyweight_df["target"]
    else:
        bodyweight_df["contraindications"] = bodyweight_df["bodyPart"] if "bodyPart" in bodyweight_df.columns else ""

    # 7. 최종 전송용 테이블 규격 및 순서 정의
    requested_columns = [
        "ex_id",  # 고유 ID
        "name",  # 운동 이름
        "category",  # 운동 분류 (근력/유산소/스트레칭)
        "difficulty_level",  # 난이도 (1, 2, 3)
        "duration_sec",  # 디폴트 시간 (20)
        "contraindications",  # 금기 부위 (target 연동)
        "gifUrl",  # 이미지 URL
        "bodyPart",  # 운동 부위
        "secondaryMuscles",  # 보조 근육
        "instructions",  # 운동 방법
    ]

    for col in requested_columns:
        if col not in bodyweight_df.columns:
            bodyweight_df[col] = ""
        else:
            bodyweight_df[col] = bodyweight_df[col].fillna("")

    bodyweight_df[requested_columns].to_csv(output_csv_path, index=False, encoding="utf-8-sig")

    return bodyweight_df[requested_columns]


if __name__ == "__main__":
    target_dir = Path("C:/workspace/linkup/linkup/data")

    input_file = target_dir / "exercises.csv"
    output_file = target_dir / "labeled_exercises.csv"

    process_fitteum_csv(input_file, output_file)
