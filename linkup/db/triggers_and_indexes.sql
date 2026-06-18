-- ============================================================
-- triggers_and_indexes.sql
-- Team LinkUp — Triggers & Indexes
-- Run AFTER schema.sql
-- ============================================================

PRAGMA foreign_keys = ON;


-- ============================================================
-- TRIGGERS
-- ============================================================

-- [TRG-1] Auto-update User_Profile.updated_at on every UPDATE
CREATE TRIGGER IF NOT EXISTS trg_user_profile_updated_at
AFTER UPDATE ON User_Profile
FOR EACH ROW
BEGIN
    UPDATE User_Profile
       SET updated_at = datetime('now','localtime')
     WHERE id = NEW.id;
END;


-- [TRG-2] Auto-compute Workout_Session.total_duration_sec when ended_at is set
--         Calculates the elapsed seconds between started_at and ended_at.
CREATE TRIGGER IF NOT EXISTS trg_session_calc_duration
AFTER UPDATE OF ended_at ON Workout_Session
FOR EACH ROW
WHEN NEW.ended_at IS NOT NULL AND OLD.ended_at IS NULL
BEGIN
    UPDATE Workout_Session
       SET total_duration_sec = (
               strftime('%s', NEW.date || ' ' || NEW.ended_at)
             - strftime('%s', NEW.date || ' ' || NEW.started_at)
           )
     WHERE session_id = NEW.session_id;
END;


-- [TRG-3] Prevent inserting Workout_Session if Daily_Log for that date
--         does not exist yet. Forces the user to log daily status first.
CREATE TRIGGER IF NOT EXISTS trg_session_require_daily_log
BEFORE INSERT ON Workout_Session
FOR EACH ROW
WHEN NOT EXISTS (SELECT 1 FROM Daily_Log WHERE date = NEW.date)
BEGIN
    SELECT RAISE(ABORT,
        'ERROR: Daily_Log record must exist before creating a Workout_Session. Insert into Daily_Log first.');
END;


-- ============================================================
-- INDEXES
-- ============================================================

-- Speed up session lookup by date (common: "show today's sessions")
CREATE INDEX IF NOT EXISTS idx_session_date
    ON Workout_Session(date);

-- Speed up history lookup by session (common: "show all exercises in session X")
CREATE INDEX IF NOT EXISTS idx_history_session
    ON Workout_History(session_id);

-- Speed up Pain-Filter & Adaptive Scheduler queries
CREATE INDEX IF NOT EXISTS idx_exercise_category
    ON Exercise_Library(category);

CREATE INDEX IF NOT EXISTS idx_exercise_difficulty
    ON Exercise_Library(difficulty_level);

-- Composite index for the most frequent query pattern:
--   "Get easy stretch exercises suitable for office"
CREATE INDEX IF NOT EXISTS idx_exercise_cat_diff
    ON Exercise_Library(category, difficulty_level);
