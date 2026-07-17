CREATE TABLE IF NOT EXISTS moderation_assets (
    asset_id        TEXT PRIMARY KEY,
    source_path     TEXT NOT NULL,
    media_type      TEXT NOT NULL,        -- 'image' | 'video'
    created_at      TEXT NOT NULL,
    status          TEXT NOT NULL,        -- pending|allowed|blocked|in_review|resolved_allow|resolved_block|error
    max_score       REAL,
    decision        TEXT,                 -- auto_allow|auto_block|review
    decision_reason TEXT                  -- JSON: which frame/class/score triggered it
);

CREATE TABLE IF NOT EXISTS moderation_frames (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    asset_id        TEXT NOT NULL REFERENCES moderation_assets(asset_id),
    frame_index     INTEGER,
    timestamp_sec   REAL,
    frame_path      TEXT,
    detections      TEXT,                 -- JSON list of {class, score, box}
    max_score       REAL,
    band            TEXT                  -- allow|review|block
);

CREATE TABLE IF NOT EXISTS review_queue (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    asset_id          TEXT NOT NULL REFERENCES moderation_assets(asset_id),
    enqueued_at       TEXT NOT NULL,
    priority          REAL,               -- derived from max_score / flagged-frame ratio
    status            TEXT NOT NULL,      -- pending|claimed|resolved
    reviewer_id       TEXT,
    resolution        TEXT,               -- approved|rejected|escalated
    resolution_notes  TEXT,
    resolved_at       TEXT
);

-- Phase 2 table, created now (harmless no-op until a real provider is wired in).
CREATE TABLE IF NOT EXISTS csam_scan_results (
    asset_id      TEXT NOT NULL REFERENCES moderation_assets(asset_id),
    provider      TEXT,                 -- 'thorn_safer'|'photodna'|'csai_match'|'not_configured'
    scan_status   TEXT NOT NULL,        -- not_configured|pending|clear|match|error
    scanned_at    TEXT,
    raw_response  TEXT
);
