import json
import os
from datetime import datetime, timezone

import config


def log_frame(asset_id, frame_result):
    os.makedirs(os.path.dirname(config.LOG_PATH) or ".", exist_ok=True)
    entry = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "asset_id": asset_id,
        "frame_path": frame_result.frame_path,
        "detections": [
            {"class": d.cls, "score": d.score, "box": d.box}
            for d in frame_result.detections
        ],
        "max_score": frame_result.max_score,
        "band": frame_result.band.value,
        "error": frame_result.error,
        "model_version": config.MODEL_VERSION,
    }
    with open(config.LOG_PATH, "a") as f:
        f.write(json.dumps(entry) + "\n")


def _read_entries(log_path=None):
    log_path = config.LOG_PATH if log_path is None else log_path
    if not os.path.exists(log_path):
        return []
    with open(log_path) as f:
        return [json.loads(line) for line in f if line.strip()]


def stats(log_path=None):
    """Report score-distribution percentiles and band counts across all
    logged frames. On-demand drift-monitoring hook, not a running service.

    Real false-positive/negative rate tracking requires a labeling workflow
    (ground truth) that doesn't exist yet; entries are logged in a shape
    that lets a `label` field be joined in later without restructuring.
    """
    entries = _read_entries(log_path)
    if not entries:
        return {"count": 0, "band_counts": {}, "percentiles": {}}

    scores = sorted(e["max_score"] for e in entries)
    band_counts = {}
    for e in entries:
        band_counts[e["band"]] = band_counts.get(e["band"], 0) + 1

    def percentile(p):
        idx = min(len(scores) - 1, int(p * len(scores)))
        return scores[idx]

    return {
        "count": len(entries),
        "band_counts": band_counts,
        "percentiles": {
            "p50": percentile(0.5),
            "p90": percentile(0.9),
            "p99": percentile(0.99),
            "max": scores[-1],
        },
    }
