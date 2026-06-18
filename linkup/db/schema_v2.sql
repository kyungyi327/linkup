-- ============================================================
-- schema_v2.sql
-- Team LinkUp — DB Schema Migration v1 → v2
-- Engine   : SQLite 3.35+ (DROP COLUMN support required)
-- Encoding : UTF-8
-- Status   : init_db() 가 자동 적용 (gender 컬럼 유무로 idempotent 판단)
-- Apply    : init_db() 호출 시 적용. 수동 적용은 sqlite3 linkup.db < schema_v2.sql
-- Rollback : restore DB file backup
-- ============================================================


PRAGMA foreign_keys = ON;

BEGIN TRANSACTION;


-- ============================================================
-- 1. User_Profile  — drop abstract self-rating, add chunk-based fields
-- ============================================================

-- Dropped: fitness_level (1~5 self-rating) → replaced by 3 raw counts (INPUT.md 2-7)
ALTER TABLE User_Profile DROP COLUMN fitness_level;

-- Dropped (회의 결정): preferred_duration_min → replaced by chunk-based fields below
ALTER TABLE User_Profile DROP COLUMN preferred_duration_min;

-- Dropped (정리): daily_step_goal — 앱이 걸음 수를 추적하지 않음 (불필요한 v1 잔재)
ALTER TABLE User_Profile DROP COLUMN daily_step_goal;

-- Dropped (정리): reminder_interval_min — INPUT.md 2-9 는 알림 on/off 만 묻고 간격은 안 묻음
ALTER TABLE User_Profile DROP COLUMN reminder_interval_min;

-- INPUT.md 1-2 — profile photo (local file path)
ALTER TABLE User_Profile ADD COLUMN avatar_path TEXT;

-- UI 요청 — 성별 (male / female)
ALTER TABLE User_Profile ADD COLUMN gender TEXT
    CHECK (gender IS NULL OR gender IN ('male', 'female'));

-- INPUT.md 2-2 — workout goals (CSV of Goal enum)
ALTER TABLE User_Profile ADD COLUMN goals TEXT DEFAULT '';

-- INPUT.md 2-3 — goal duration in weeks (1~24)
ALTER TABLE User_Profile ADD COLUMN goal_duration_weeks INTEGER
    CHECK (goal_duration_weeks IS NULL
        OR (goal_duration_weeks >= 1 AND goal_duration_weeks <= 24));

-- INPUT.md 2-4 — weekly frequency (1~7)
ALTER TABLE User_Profile ADD COLUMN weekly_frequency INTEGER
    CHECK (weekly_frequency IS NULL
        OR (weekly_frequency >= 1 AND weekly_frequency <= 7));

-- INPUT.md 2-9 — notifications on/off (0 or 1)
ALTER TABLE User_Profile ADD COLUMN notification_enabled INTEGER DEFAULT 1
    CHECK (notification_enabled IN (0, 1));

-- INPUT.md 2-7 — fitness benchmark: max push-ups (NULL = "I don't know")
ALTER TABLE User_Profile ADD COLUMN pushup_max INTEGER
    CHECK (pushup_max IS NULL OR pushup_max >= 0);

-- INPUT.md 2-7 — fitness benchmark: max plank hold in seconds
ALTER TABLE User_Profile ADD COLUMN plank_max_sec INTEGER
    CHECK (plank_max_sec IS NULL OR plank_max_sec >= 0);

-- INPUT.md 2-7 — fitness benchmark: max squats
ALTER TABLE User_Profile ADD COLUMN squat_max INTEGER
    CHECK (squat_max IS NULL OR squat_max >= 0);


-- ============================================================
-- 2. Daily_Log  — merge sleep+mood+stress into one score, per-part fatigue
-- ============================================================

-- Dropped (team meeting): sleep_hours + mood_score → merged into mental_condition_score
ALTER TABLE Daily_Log DROP COLUMN sleep_hours;
ALTER TABLE Daily_Log DROP COLUMN mood_score;

-- Dropped (INPUT.md 3-2-2): single fatigue_score → replaced by per-body-part fatigue_by_part
ALTER TABLE Daily_Log DROP COLUMN fatigue_score;

-- Dropped (정리): step_count — INPUT.md 3-x 는 걸음 수를 묻지 않음
ALTER TABLE Daily_Log DROP COLUMN step_count;

-- Team meeting — unified mental condition score 0~10, 10 = best
-- (covers sleep, mood, stress in one subjective rating)
ALTER TABLE Daily_Log ADD COLUMN mental_condition_score INTEGER
    CHECK (mental_condition_score IS NULL
        OR (mental_condition_score >= 0 AND mental_condition_score <= 10));

-- INPUT.md 3-2-1 — outdoor activity time in hours (0~16)
ALTER TABLE Daily_Log ADD COLUMN outdoor_hours REAL
    CHECK (outdoor_hours IS NULL
        OR (outdoor_hours >= 0 AND outdoor_hours <= 16));

-- INPUT.md 3-2-2 — per-body-part fatigue as JSON.
-- Format: {"neck": 7, "shoulder": 3}  (sparse — omit parts with no pain)
-- Empty object '{}' = no fatigue anywhere.
ALTER TABLE Daily_Log ADD COLUMN fatigue_by_part TEXT DEFAULT '{}';


-- ============================================================
-- 3. Workout_History  — distinguish skipped / aborted from completed
-- ============================================================

-- INPUT.md 5 — "현재 진행 중인 동작 제외" / "그만두기" need to be distinguished
-- from normal completion. Existing `is_completed BOOLEAN` is kept for
-- backward compatibility and auto-synced by the DAO layer.
ALTER TABLE Workout_History ADD COLUMN status TEXT DEFAULT 'pending'
    CHECK (status IN ('pending', 'completed', 'skipped', 'aborted'));


-- ============================================================
-- 3b. Workout_Session  — UI 세션 완료 화면의 메모(선택)
-- ============================================================
ALTER TABLE Workout_Session ADD COLUMN memo TEXT;


-- ============================================================
-- 4. Bump db_version in App_Settings
-- ============================================================
UPDATE App_Settings SET value = '2' WHERE key = 'db_version';


COMMIT;


-- ============================================================
-- Post-migration verification (run manually):
--
--   sqlite3 linkup.db ".schema User_Profile"
--     expect: fitness_level / preferred_duration_min 없음,
--             goals / goal_duration_weeks / weekly_frequency /
--             avatar_path / notification_enabled / pushup_max / etc. 있음
--   sqlite3 linkup.db ".schema Daily_Log"
--     expect: sleep_hours / mood_score / fatigue_score 없음,
--             mental_condition_score / outdoor_hours / fatigue_by_part 있음
--   sqlite3 linkup.db ".schema Workout_History"
--     expect: status 컬럼 있음
--   sqlite3 linkup.db "SELECT value FROM App_Settings WHERE key='db_version';"
--     expect: '2'
-- ============================================================
