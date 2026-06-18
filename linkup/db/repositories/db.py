"""
repositories/db.py
SQLite 연결 헬퍼.

연결 설정 단일 소스:
    - foreign_keys = ON
    - row_factory  = sqlite3.Row (컬럼명으로 접근)
    - journal_mode = WAL
"""

import sqlite3
from pathlib import Path

# linkup/db/ 디렉터리 (schema/seed 파일 위치)
_DB_DIR = Path(__file__).resolve().parent.parent
DEFAULT_DB_PATH = _DB_DIR / "linkup.db"


def get_connection(db_path: Path | None = None) -> sqlite3.Connection:
    """설정이 적용된 SQLite 연결 반환. 호출 측에서 close 또는 with 사용."""
    path = Path(db_path) if db_path else DEFAULT_DB_PATH
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA journal_mode = WAL;")
    return conn


def init_db(db_path: Path | None = None) -> None:
    """schema + triggers + schema_v2 + seed 를 순서대로 실행하여 DB 초기화.

    schema.sql / triggers 는 CREATE ... IF NOT EXISTS, seed 는 INSERT OR IGNORE
    이므로 반복 실행해도 안전. schema_v2 는 ALTER 라 이미 적용된 DB 에 다시
    실행하면 에러가 나므로, 신규 DB(컬럼 없음)일 때만 적용한다.
    """
    scripts = [
        _DB_DIR / "schema.sql",
        _DB_DIR / "triggers_and_indexes.sql",
        _DB_DIR / "seed_data.sql",
    ]
    with get_connection(db_path) as conn:
        for p in (scripts[0], scripts[1]):
            if p.exists():
                conn.executescript(p.read_text(encoding="utf-8"))
        # schema_v2 (ALTER) 는 아직 적용 안 된 경우에만
        if not _v2_applied(conn):
            v2 = _DB_DIR / "schema_v2.sql"
            if v2.exists():
                conn.executescript(v2.read_text(encoding="utf-8"))
        if scripts[2].exists():
            conn.executescript(scripts[2].read_text(encoding="utf-8"))
        conn.commit()


def _v2_applied(conn: sqlite3.Connection) -> bool:
    """User_Profile 에 v2 컬럼(gender)이 이미 있는지로 v2 적용 여부 판단."""
    rows = conn.execute("PRAGMA table_info(User_Profile)").fetchall()
    cols = {r[1] for r in rows}
    return "gender" in cols
