import config
from models import Band, Decision, FrameResult


def band_for_score(score):
    if score >= config.BLOCK_THRESHOLD:
        return Band.BLOCK
    if score >= config.REVIEW_THRESHOLD:
        return Band.REVIEW
    return Band.ALLOW


def score_frame(frame_path, frame_index, timestamp_sec, detections, error=None):
    max_score = max((d.score for d in detections), default=0.0)
    band = band_for_score(max_score)
    return FrameResult(
        frame_path=frame_path,
        frame_index=frame_index,
        timestamp_sec=timestamp_sec,
        detections=detections,
        max_score=max_score,
        band=band,
        error=error,
    )


def aggregate(frame_results):
    """Aggregate per-frame results into an asset-level decision using
    worst-frame-wins: any single frame's band governs the whole asset. The
    flagged-frame ratio is computed for review-queue prioritization only, not
    used as a gate.
    """
    if not frame_results:
        return 0.0, Decision.AUTO_ALLOW, {"reason": "no frames scored"}, 0.0

    worst = max(frame_results, key=lambda f: f.max_score)
    flagged = sum(1 for f in frame_results if f.band != Band.ALLOW)
    flagged_ratio = flagged / len(frame_results)

    if worst.band == Band.BLOCK:
        decision = Decision.AUTO_BLOCK
    elif worst.band == Band.REVIEW:
        decision = Decision.REVIEW
    else:
        decision = Decision.AUTO_ALLOW

    reason = {
        "frame_path": worst.frame_path,
        "frame_index": worst.frame_index,
        "max_score": worst.max_score,
        "band": worst.band.value,
        "classes": [d.cls for d in worst.detections],
    }
    return worst.max_score, decision, reason, flagged_ratio
