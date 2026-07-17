import json
import os
import tempfile
import uuid
from dataclasses import asdict
from datetime import datetime, timezone

import config
import csam
import detection
import observability
import review_queue
from extraction import video_to_frames
from models import Decision, ModerationResult
from scoring import aggregate, score_frame

VIDEO_EXTENSIONS = {".mp4", ".mov", ".avi", ".mkv", ".webm"}
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}


def _infer_media_type(source_path):
    ext = os.path.splitext(source_path)[1].lower()
    if ext in VIDEO_EXTENSIONS:
        return "video"
    if ext in IMAGE_EXTENSIONS:
        return "image"
    raise ValueError(f"Cannot infer media type for {source_path}")


def _now():
    return datetime.now(timezone.utc).isoformat()


def run_moderation(source_path, media_type=None, conn=None):
    """Run the full moderation pipeline on a single image or video: extract
    frames (if video), run batched nudity detection, score/band each frame,
    aggregate to an asset-level decision, persist everything, log every
    score, run the (currently stubbed) CSAM stage, and enqueue for human
    review if the decision requires it.
    """
    media_type = media_type or _infer_media_type(source_path)
    asset_id = str(uuid.uuid4())
    own_conn = conn is None
    conn = conn or review_queue.get_connection()

    try:
        if media_type == "video":
            with tempfile.TemporaryDirectory() as tmp_dir:
                sampled = video_to_frames(source_path, tmp_dir)
                frame_paths = [p for p, _, _ in sampled]
                detected = detection.detect_frames(frame_paths)
                frame_results = [
                    score_frame(path, idx, ts, *detected[path])
                    for path, idx, ts in sampled
                ]
        else:
            detected = detection.detect_frames([source_path])
            frame_results = [score_frame(source_path, 0, 0.0, *detected[source_path])]

        max_score, decision, decision_reason, flagged_ratio = aggregate(frame_results)

        for fr in frame_results:
            observability.log_frame(asset_id, fr)

        status = {
            Decision.AUTO_ALLOW: "allowed",
            Decision.AUTO_BLOCK: "blocked",
            Decision.REVIEW: "in_review",
        }[decision]

        conn.execute(
            "INSERT INTO moderation_assets "
            "(asset_id, source_path, media_type, created_at, status, max_score, "
            "decision, decision_reason) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                asset_id,
                source_path,
                media_type,
                _now(),
                status,
                max_score,
                decision.value,
                json.dumps(decision_reason),
            ),
        )

        for fr in frame_results:
            conn.execute(
                "INSERT INTO moderation_frames "
                "(asset_id, frame_index, timestamp_sec, frame_path, detections, "
                "max_score, band) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    asset_id,
                    fr.frame_index,
                    fr.timestamp_sec,
                    fr.frame_path,
                    json.dumps([asdict(d) for d in fr.detections]),
                    fr.max_score,
                    fr.band.value,
                ),
            )

        scanner = csam.get_scanner()
        csam_result = scanner.scan(source_path)
        conn.execute(
            "INSERT INTO csam_scan_results "
            "(asset_id, provider, scan_status, scanned_at, raw_response) "
            "VALUES (?, ?, ?, ?, ?)",
            (
                asset_id,
                csam_result.provider,
                csam_result.status,
                _now(),
                json.dumps(csam_result.raw) if csam_result.raw else None,
            ),
        )

        if decision == Decision.REVIEW:
            priority = max_score + flagged_ratio
            review_queue.enqueue(conn, asset_id, priority)

        conn.commit()

        return ModerationResult(
            asset_id=asset_id,
            source_path=source_path,
            media_type=media_type,
            frames=frame_results,
            max_score=max_score,
            decision=decision,
            decision_reason=decision_reason,
            flagged_ratio=flagged_ratio,
        )
    finally:
        if own_conn:
            conn.close()
