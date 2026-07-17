import os
import sqlite3

import pytest

import config
import review_queue
from models import Decision
from pipeline import run_moderation

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BENIGN_IMAGE = os.path.join(REPO_ROOT, "man.jpeg")
EXPLICIT_FRAME = os.path.join(REPO_ROOT, "frames", "frame_0003.jpg")
VIDEO_PATH = os.path.join(REPO_ROOT, "video.mp4")


@pytest.fixture
def conn(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "SCHEMA_PATH", os.path.join(REPO_ROOT, "db", "schema.sql"))
    monkeypatch.setattr(config, "LOG_PATH", str(tmp_path / "scores.jsonl"))
    c = sqlite3.connect(":memory:")
    c.row_factory = sqlite3.Row
    review_queue.init_db(c)
    yield c
    c.close()


@pytest.mark.skipif(not os.path.exists(BENIGN_IMAGE), reason="fixture not present")
def test_benign_image_is_auto_allowed(conn):
    result = run_moderation(BENIGN_IMAGE, media_type="image", conn=conn)
    assert result.decision == Decision.AUTO_ALLOW

    row = conn.execute(
        "SELECT * FROM moderation_assets WHERE asset_id = ?", (result.asset_id,)
    ).fetchone()
    assert row["status"] == "allowed"

    csam_row = conn.execute(
        "SELECT * FROM csam_scan_results WHERE asset_id = ?", (result.asset_id,)
    ).fetchone()
    assert csam_row["scan_status"] == "not_configured"


@pytest.mark.skipif(not os.path.exists(EXPLICIT_FRAME), reason="fixture not present")
def test_explicit_frame_is_queued_for_review(conn):
    result = run_moderation(EXPLICIT_FRAME, media_type="image", conn=conn)
    assert result.decision == Decision.REVIEW
    assert result.max_score >= config.REVIEW_THRESHOLD

    queued = review_queue.list_pending(conn)
    assert any(item["asset_id"] == result.asset_id for item in queued)


@pytest.mark.skipif(not os.path.exists(VIDEO_PATH), reason="fixture not present")
def test_video_end_to_end_smoke(conn):
    result = run_moderation(VIDEO_PATH, media_type="video", conn=conn)
    assert result.decision in (
        Decision.AUTO_ALLOW,
        Decision.REVIEW,
        Decision.AUTO_BLOCK,
    )
    assert len(result.frames) > 0

    frame_rows = conn.execute(
        "SELECT * FROM moderation_frames WHERE asset_id = ?", (result.asset_id,)
    ).fetchall()
    assert len(frame_rows) == len(result.frames)
