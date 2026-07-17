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
    # A frame we failed to read/scan carries no safety signal — treat it as
    # not-confidently-clean (REVIEW) rather than ALLOW, so it can never
    # silently resolve to auto_allow. Consistent with the fail-closed policy:
    # "couldn't scan it" must never be indistinguishable from "scanned clean."
    band = Band.REVIEW if error else band_for_score(max_score)
    return FrameResult(
        frame_path=frame_path,
        frame_index=frame_index,
        timestamp_sec=timestamp_sec,
        detections=detections,
        max_score=max_score,
        band=band,
        error=error,
    )


_BAND_RANK = {Band.ALLOW: 0, Band.REVIEW: 1, Band.BLOCK: 2}


def aggregate(frame_results):
    """Aggregate per-frame results into an asset-level decision using
    worst-frame-wins: any single frame's band governs the whole asset. The
    flagged-frame ratio is computed for review-queue prioritization only, not
    used as a gate.

    No human-review step: REVIEW-band frames are not confident violations,
    but policy is to auto-block rather than hold them for a moderator, so
    they resolve to AUTO_BLOCK alongside BLOCK-band frames. Band still
    distinguishes the two internally (moderation_frames.band, observability
    stats) even though both map to the same decision.

    Frames scored zero because nothing could be read (extraction/detection
    failure) must not be treated as "worst" by raw score alone — that would
    let a corrupt/unreadable asset win the max() comparison against genuine
    ALLOW frames and silently pass. Worst-frame selection ranks by band
    first, score second, so an errored (REVIEW-band) frame always outranks
    an ALLOW frame regardless of score.
    """
    if not frame_results:
        return 0.0, Decision.AUTO_BLOCK, {"reason": "no frames scored"}, 0.0

    worst = max(frame_results, key=lambda f: (_BAND_RANK[f.band], f.max_score))
    flagged = sum(1 for f in frame_results if f.band != Band.ALLOW)
    flagged_ratio = flagged / len(frame_results)

    if worst.band in (Band.BLOCK, Band.REVIEW):
        decision = Decision.AUTO_BLOCK
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
