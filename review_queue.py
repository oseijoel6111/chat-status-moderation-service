import os
import sqlite3
from datetime import datetime, timezone

import config


def get_connection(db_path=None):
    db_path = config.DB_PATH if db_path is None else db_path
    os.makedirs(os.path.dirname(db_path) or ".", exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    init_db(conn)
    return conn


def init_db(conn):
    with open(config.SCHEMA_PATH) as f:
        conn.executescript(f.read())
    conn.commit()


def _now():
    return datetime.now(timezone.utc).isoformat()


def enqueue(conn, asset_id, priority):
    conn.execute(
        "INSERT INTO review_queue (asset_id, enqueued_at, priority, status) "
        "VALUES (?, ?, ?, 'pending')",
        (asset_id, _now(), priority),
    )
    conn.commit()


def list_pending(conn, limit=50):
    rows = conn.execute(
        "SELECT * FROM review_queue WHERE status = 'pending' "
        "ORDER BY priority DESC, enqueued_at ASC LIMIT ?",
        (limit,),
    ).fetchall()
    return [dict(r) for r in rows]


def claim(conn, review_id, reviewer_id):
    conn.execute(
        "UPDATE review_queue SET status = 'claimed', reviewer_id = ? WHERE id = ?",
        (reviewer_id, review_id),
    )
    conn.commit()


def resolve(conn, review_id, resolution, notes=None):
    conn.execute(
        "UPDATE review_queue SET status = 'resolved', resolution = ?, "
        "resolution_notes = ?, resolved_at = ? WHERE id = ?",
        (resolution, notes, _now(), review_id),
    )
    conn.commit()
