"""
OIL-Track AI - Module 1
db_manager.py: SQLite schema management and schedule ingestion parser.
"""

import os
import sqlite3
import pandas as pd
from datetime import datetime

DEFAULT_DB_PATH = os.path.join("database", "oil_track.db")

REQUIRED_COLUMNS = [
    "activity_id",
    "level",
    "discipline",
    "wbs_package",
    "activity_description",
    "planned_start",
    "planned_finish",
    "baseline_status"
]

def get_db_connection(db_path=DEFAULT_DB_PATH):
    """Establishes connection to the SQLite database with busy timeout."""
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path, timeout=10.0) # 10s wait for lock release
    conn.row_factory = sqlite3.Row
    return conn

def init_db(db_path=DEFAULT_DB_PATH):
    """Initializes the planned_activities and audit trail tables with indexes."""
    conn = get_db_connection(db_path)
    cursor = conn.cursor()

    # 1. Master Planned Schedule Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS planned_activities (
        activity_id TEXT PRIMARY KEY,
        level TEXT NOT NULL,
        discipline TEXT NOT NULL,
        wbs_package TEXT NOT NULL,
        activity_description TEXT NOT NULL,
        planned_start TEXT NOT NULL,
        planned_finish TEXT NOT NULL,
        baseline_status TEXT DEFAULT 'PLANNED',
        actual_start TEXT,
        actual_finish TEXT,
        progress_pct REAL DEFAULT 0.0,
        status TEXT DEFAULT 'NOT_STARTED',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 2. Human-in-the-Loop Audit Trail Table (Updated with media paths)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS activity_updates_audit (
        audit_id INTEGER PRIMARY KEY AUTOINCREMENT,
        report_date TEXT NOT NULL,
        discipline TEXT NOT NULL,
        raw_site_text TEXT NOT NULL,
        matched_activity_id TEXT NOT NULL,
        matched_description TEXT NOT NULL,
        confidence REAL NOT NULL,
        event_type TEXT NOT NULL,
        reported_progress REAL,
        decision TEXT NOT NULL,          -- 'APPROVED', 'MANUAL_OVERRIDE', 'REJECTED'
        reviewer_comments TEXT,
        image_path TEXT,                 -- Path to saved site photo proof
        audio_path TEXT,                 -- Path to saved site audio recording
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    cursor.execute("CREATE INDEX IF NOT EXISTS idx_discipline ON planned_activities(discipline);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_level ON planned_activities(level);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_audit_act ON activity_updates_audit(matched_activity_id);")

    conn.commit()
    conn.close()
    print(f"[OK] Database initialized with audit trail at {db_path}")

def normalize_column_name(col: str) -> str:
    """Normalizes column names to lowercase snake_case for robust matching."""
    return (
        col.strip()
        .lower()
        .replace(" ", "_")
        .replace("/", "_")
        .replace("-", "_")
    )

def validate_schedule_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Validates schema, normalizes column names, strips whitespace, and ensures valid ISO date strings."""
    col_mapping = {col: normalize_column_name(col) for col in df.columns}
    df = df.rename(columns=col_mapping)

    missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing:
        raise ValueError(
            f"Schedule missing mandatory columns: {missing}.\n"
            f"Detected columns: {list(df.columns)}"
        )

    df = df[REQUIRED_COLUMNS].copy()

    text_cols = ["activity_id", "level", "discipline", "wbs_package", "activity_description", "baseline_status"]
    for col in text_cols:
        df[col] = df[col].astype(str).str.strip()

    for col in ["planned_start", "planned_finish"]:
        parsed_dates = pd.to_datetime(df[col], errors="coerce")
        if parsed_dates.isna().any():
            invalid_rows = df[parsed_dates.isna()][col].tolist()
            raise ValueError(f"Invalid date format found in {col}: {invalid_rows}")
        df[col] = parsed_dates.dt.strftime("%Y-%m-%d")

    return df

def ingest_schedule_file(file_path: str, db_path=DEFAULT_DB_PATH) -> int:
    """Reads CSV or Excel, validates it, and upserts into SQLite."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    if file_path.endswith(".csv"):
        df = pd.read_csv(file_path)
    elif file_path.endswith((".xlsx", ".xls")):
        df = pd.read_excel(file_path, engine="openpyxl")
    else:
        raise ValueError("Unsupported format. Use .csv or .xlsx")

    validated_df = validate_schedule_dataframe(df)

    conn = get_db_connection(db_path)
    cursor = conn.cursor()

    upsert_query = """
    INSERT INTO planned_activities (
        activity_id, level, discipline, wbs_package, 
        activity_description, planned_start, planned_finish, baseline_status
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ON CONFLICT(activity_id) DO UPDATE SET
        level=excluded.level,
        discipline=excluded.discipline,
        wbs_package=excluded.wbs_package,
        activity_description=excluded.activity_description,
        planned_start=excluded.planned_start,
        planned_finish=excluded.planned_finish,
        baseline_status=excluded.baseline_status;
    """

    records = validated_df.to_records(index=False)
    cursor.executemany(upsert_query, list(records))

    conn.commit()
    row_count = cursor.rowcount
    conn.close()

    print(f"[OK] Ingested {len(validated_df)} activities from '{file_path}' into {db_path}.")
    return len(validated_df)

def fetch_all_activities(db_path=DEFAULT_DB_PATH) -> pd.DataFrame:
    """Helper function to load the entire schedule into a DataFrame."""
    conn = get_db_connection(db_path)
    df = pd.read_sql_query("SELECT * FROM planned_activities ORDER BY planned_start ASC", conn)
    conn.close()
    return df

def log_audit_record(record: dict, db_path=DEFAULT_DB_PATH):
    """Logs an approved or reviewed progress record into the audit table with optional media paths."""
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO activity_updates_audit (
        report_date, discipline, raw_site_text, matched_activity_id,
        matched_description, confidence, event_type, reported_progress,
        decision, reviewer_comments, image_path, audio_path
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        record["report_date"],
        record["discipline"],
        record["raw_site_text"],
        record["matched_activity_id"],
        record["matched_description"],
        record["confidence"],
        record["event_type"],
        record.get("reported_progress", 0.0),
        record.get("decision", "APPROVED"),
        record.get("reviewer_comments", ""),
        record.get("image_path", None),
        record.get("audio_path", None)
    ))
    conn.commit()
    conn.close()

def sync_actual_progress(activity_id: str, report_date: str, event_type: str, progress_pct: float, db_path=DEFAULT_DB_PATH) -> dict:
    """
    Synchronizes an approved site event into the planned_activities table,
    updating actual dates, status, and computing start/finish variances in days.
    """
    conn = get_db_connection(db_path)
    cursor = conn.cursor()

    cursor.execute(
        "SELECT planned_start, planned_finish, actual_start, actual_finish FROM planned_activities WHERE activity_id = ?",
        (activity_id,)
    )
    row = cursor.fetchone()

    if not row:
        conn.close()
        raise ValueError(f"Activity ID '{activity_id}' not found in database.")

    p_start = datetime.strptime(row["planned_start"], "%Y-%m-%d")
    p_finish = datetime.strptime(row["planned_finish"], "%Y-%m-%d")
    existing_act_start = row["actual_start"]
    existing_act_finish = row["actual_finish"]

    act_start = existing_act_start
    act_finish = existing_act_finish
    new_status = "IN_PROGRESS"

    if event_type in ["STARTED", "IN_PROGRESS"]:
        if not act_start:
            act_start = report_date
        new_status = "IN_PROGRESS"
    elif event_type == "COMPLETED":
        if not act_start:
            act_start = row["planned_start"]
        act_finish = report_date
        progress_pct = 100.0
        new_status = "COMPLETED"

    cursor.execute("""
    UPDATE planned_activities SET
        actual_start = ?,
        actual_finish = ?,
        progress_pct = ?,
        status = ?
    WHERE activity_id = ?
    """, (act_start, act_finish, progress_pct, new_status, activity_id))

    conn.commit()
    conn.close()

    start_var_days = None
    finish_var_days = None

    if act_start:
        a_start_dt = datetime.strptime(act_start, "%Y-%m-%d")
        start_var_days = (a_start_dt - p_start).days

    if act_finish:
        a_finish_dt = datetime.strptime(act_finish, "%Y-%m-%d")
        finish_var_days = (a_finish_dt - p_finish).days

    return {
        "activity_id": activity_id,
        "status": new_status,
        "actual_start": act_start,
        "actual_finish": act_finish,
        "start_variance_days": start_var_days,
        "finish_variance_days": finish_var_days
    }

def get_reviewed_events_map(db_path=DEFAULT_DB_PATH) -> dict:
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT report_date, raw_site_text, matched_activity_id, decision FROM activity_updates_audit")
    rows = cursor.fetchall()
    conn.close()

    reviewed = {}
    for r in rows:
        key = f"{r['report_date']}||{r['raw_site_text'].strip()}"
        reviewed[key] = {
            "matched_activity_id": r["matched_activity_id"],
            "decision": r["decision"]
        }
    return reviewed

def clear_audit_trail(db_path=DEFAULT_DB_PATH):
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM activity_updates_audit")
    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    sample_file = os.path.join("data", "schedule", "project_schedule.xlsx")
    ingest_schedule_file(sample_file)
    df_loaded = fetch_all_activities()
    print(f"[OK] Verified: {len(df_loaded)} rows read back from SQLite.")