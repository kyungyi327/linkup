-- ============================================================
-- schema.sql
-- Team LinkUp — Database Schema
-- Engine : SQLite 3.x
-- Encoding : UTF-8
-- ============================================================

PRAGMA journal_mode = WAL;
PRAGMA foreign_keys = ON;


-- ============================================================
-- 1. User_Profile
--    Local single-user app: always one row (id = 1).
-- ============================================================
CREATE TABLE IF NOT EXISTS User_Profile (
    id                     INTEGER PRIMARY KEY DEFAULT 1,
    nickname               TEXT,
    birth_year             INTEGER,
    height_cm              REAL,
    weight_kg              REAL,
    job_type               TEXT    NOT NULL DEFAULT 'student',
    pain_points            TEXT    DEFAULT '',
    fitness_level          INTEGER NOT NULL DEFAULT 3
                           CHECK (fitness_level >= 1 AND fitness_level <= 5),
    preferred_duration_min INTEGER DEFAULT 15,
    daily_step_goal        INTEGER DEFAULT 8000,
    reminder_interval_min  INTEGER DEFAULT 60,
    created_at             TEXT    DEFAULT (datetime('now','localtime')),
    updated_at             TEXT    DEFAULT (datetime('now','localtime'))
);

INSERT OR IGNORE INTO User_Profile (id) VALUES (1);


-- ============================================================
-- 2. Exercise_Library
--    Static seed data shipped with the application.
-- ============================================================
CREATE TABLE IF NOT EXISTS Exercise_Library (
    ex_id             TEXT    PRIMARY KEY,
    name              TEXT    NOT NULL,
    category          TEXT    NOT NULL DEFAULT 'stretch'
                      CHECK (category IN ('stretch','strength','cardio','relaxation','mobility')),
    target_muscle     TEXT    NOT NULL,
    difficulty_level  INTEGER NOT NULL DEFAULT 1
                      CHECK (difficulty_level >= 1 AND difficulty_level <= 3),
    contraindications TEXT    DEFAULT '',
    modified_ex_id    TEXT    REFERENCES Exercise_Library(ex_id),
    suitable_scenes   TEXT    NOT NULL DEFAULT 'office,home',
    default_sets      INTEGER DEFAULT 1,
    default_reps      INTEGER DEFAULT 1,
    duration_sec      INTEGER NOT NULL DEFAULT 30,
    description       TEXT,
    instruction_steps TEXT,
    media_path        TEXT
);


-- ============================================================
-- 3. Daily_Log
--    One row per calendar day.
-- ============================================================
CREATE TABLE IF NOT EXISTS Daily_Log (
    date          TEXT    PRIMARY KEY,
    sleep_hours   REAL,
    step_count    INTEGER,
    mood_score    INTEGER CHECK (mood_score IS NULL OR (mood_score >= 1 AND mood_score <= 5)),
    fatigue_score INTEGER CHECK (fatigue_score IS NULL OR (fatigue_score >= 1 AND fatigue_score <= 10)),
    manual_scene  TEXT,
    created_at    TEXT    DEFAULT (datetime('now','localtime'))
);


-- ============================================================
-- 4. Workout_Session
--    One complete workout experience (a set of exercises).
-- ============================================================
CREATE TABLE IF NOT EXISTS Workout_Session (
    session_id       INTEGER PRIMARY KEY AUTOINCREMENT,
    date             TEXT    NOT NULL REFERENCES Daily_Log(date),
    started_at       TEXT    NOT NULL,
    ended_at         TEXT,
    total_duration_sec INTEGER,
    scene            TEXT,
    overall_feedback INTEGER CHECK (overall_feedback IS NULL OR overall_feedback IN (-1, 0, 1)),
    is_completed     BOOLEAN DEFAULT 0
);


-- ============================================================
-- 5. Workout_History
--    Per-exercise record inside a session.
-- ============================================================
CREATE TABLE IF NOT EXISTS Workout_History (
    history_id         INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id         INTEGER NOT NULL REFERENCES Workout_Session(session_id),
    ex_id              TEXT    NOT NULL REFERENCES Exercise_Library(ex_id),
    seq_order          INTEGER NOT NULL,
    actual_sets        INTEGER,
    actual_duration_sec INTEGER,
    is_completed       BOOLEAN DEFAULT 0,
    used_modified      BOOLEAN DEFAULT 0,
    feedback           INTEGER CHECK (feedback IS NULL OR feedback IN (-1, 0, 1)),
    pain_during        TEXT    DEFAULT ''
);


-- ============================================================
-- 6. App_Settings  (Key-Value store)
-- ============================================================
CREATE TABLE IF NOT EXISTS App_Settings (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

INSERT OR IGNORE INTO App_Settings (key, value) VALUES
    ('theme',                'light'),
    ('language',             'ko'),
    ('onboarding_completed', 'false'),
    ('db_version',           '1');
