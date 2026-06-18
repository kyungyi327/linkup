"""
linkup/db/tools/etl_fitteum.py
이경 운동 데이터(fitteum_db.db / bodyweight_exercises 325행)를
딩정 사용자 DB(linkup.db / Exercise_Library)로 변환·삽입하는 ETL.

- append-only (INSERT OR IGNORE): 기존 EX_* seed 는 건드리지 않음.
- 런타임 코드(알고리즘/DAO/UI) 수정 0줄. 이 스크립트만 실행하면 됨.
- 실행: python3 -m linkup.db.tools.etl_fitteum   (레포 루트에서)

매핑 규칙:
- ex_id   : int 1~325 → 'LK_0001'~'LK_0325' (기존 EX_* 와 네임스페이스 분리)
- category: 근력→strength / 스트레칭→stretch / 유산소→cardio (미지값은 에러)
- contraindications: 이경 'bodyPart'(신체부위) → 딩정 BodyPart enum CSV.
    이경 원본 'contraindications'(근육명)는 통증회피와 의미가 달라 폐기.
    매핑 없는 부위(chest/cardio)는 빈값 → 통증회피 필터에서 절대 안 걸림.
- target_muscle: 이경 'bodyPart' 원문 (NOT NULL 충족 + 표시용)
- duration_sec: category 별 기본값 (strength 45 / stretch 30 / cardio 60)
- description / instruction_steps: 이경 'instructions' 텍스트 (이미지 대신)
- media_path: NULL (gifUrl 만료 → 폐기, 회의 결정)
"""

import json
import sqlite3
import sys
from pathlib import Path

# linkup/db/ 디렉터리
_DB_DIR = Path(__file__).resolve().parent.parent
# 입력: 이경 운동 DB (linkup/data/fitteum_db.db)
SRC = _DB_DIR.parent / "data" / "fitteum_db.db"
# 출력: 딩정 사용자 DB
DST = _DB_DIR / "linkup.db"

CATEGORY_MAP = {"근력": "strength", "스트레칭": "stretch", "유산소": "cardio"}

# 이경 bodyPart → 딩정 BodyPart enum CSV (과회피 > 과추천 원칙)
BODYPART_MAP = {
    "neck": "neck",
    "shoulders": "shoulder",
    "back": "upper_back,lower_back",
    "waist": "lower_back",
    "upper legs": "hip,knee",
    "lower legs": "knee,ankle",
    "upper arms": "elbow",
    "lower arms": "wrist,elbow",
    "chest": "",     # 딩정 enum 에 가슴 없음 → 회피대상 아님
    "cardio": "",    # 전신, 특정 관절 무관
}

DURATION_BY_CAT = {"strength": 45, "stretch": 30, "cardio": 60}


def map_category(kor: str) -> str:
    v = CATEGORY_MAP.get((kor or "").strip())
    if v is None:
        raise ValueError(f"미지 category: {kor!r} — CATEGORY_MAP 에 추가 필요")
    return v


def map_contraindications(body_part: str) -> str:
    return BODYPART_MAP.get((body_part or "").strip().lower(), "")


def main() -> None:
    if not SRC.exists():
        sys.exit(f"[중단] 입력 DB 없음: {SRC}")
    if not DST.exists():
        sys.exit(f"[중단] 대상 DB 없음: {DST} — 먼저 init_db() 로 생성하세요")

    src = sqlite3.connect(str(SRC))
    src.row_factory = sqlite3.Row
    dst = sqlite3.connect(str(DST))

    params = []
    unmapped_parts = set()
    for r in src.execute("SELECT * FROM bodyweight_exercises"):
        bp = (r["bodyPart"] or "").strip().lower()
        if bp not in BODYPART_MAP:
            unmapped_parts.add(r["bodyPart"])  # 로깅만, 버리지 않음 (빈 contra 로 삽입)
        cat = map_category(r["category"])
        instr = (r["instructions"] or "").strip()
        steps = [s.strip() for s in instr.split(".") if s.strip()]
        params.append((
            f"LK_{int(r['ex_id']):04d}",          # ex_id
            r["name"],                              # name
            cat,                                    # category
            r["bodyPart"] or "unknown",             # target_muscle (NOT NULL)
            int(r["difficulty_level"]),             # difficulty_level
            map_contraindications(r["bodyPart"]),   # contraindications
            None,                                   # modified_ex_id
            "office,home",                          # suitable_scenes
            1,                                      # default_sets
            1,                                      # default_reps
            DURATION_BY_CAT.get(cat, 30),           # duration_sec
            instr or None,                          # description
            json.dumps(steps, ensure_ascii=False) if steps else None,  # instruction_steps
            None,                                   # media_path
        ))

    cur = dst.executemany(
        """
        INSERT OR IGNORE INTO Exercise_Library
        (ex_id, name, category, target_muscle, difficulty_level, contraindications,
         modified_ex_id, suitable_scenes, default_sets, default_reps, duration_sec,
         description, instruction_steps, media_path)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        params,
    )
    dst.commit()

    total = dst.execute("SELECT COUNT(*) FROM Exercise_Library").fetchone()[0]
    lk = dst.execute(
        "SELECT COUNT(*) FROM Exercise_Library WHERE ex_id LIKE 'LK_%'"
    ).fetchone()[0]
    print(f"입력 325행 처리 / 삽입 시도 {cur.rowcount}행")
    print(f"Exercise_Library 총 {total}행 (LK_* {lk}행)")
    if unmapped_parts:
        print(f"[참고] BodyPart 매핑 없는 부위(빈 contra 로 삽입됨): {unmapped_parts}")

    src.close()
    dst.close()


if __name__ == "__main__":
    main()
