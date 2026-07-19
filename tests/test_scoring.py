import config
from models import Band, Decision, Detection
from scoring import aggregate, band_for_score, score_frame

# Real true-positive scores observed on test footage (see config.py comment).
# REVIEW_THRESHOLD was raised from 0.25 to 0.45 after real production volume
# showed false positives concentrated below 0.35 — three of these eight
# calibration scores now fall below the new bar. That's an accepted
# trade-off (fewer false blocks, at the cost of not catching real violations
# in this range via threshold alone), not a regression.
OBSERVED_TRUE_POSITIVES_BELOW_NEW_THRESHOLD = [0.278, 0.28, 0.424]
OBSERVED_TRUE_POSITIVES_ABOVE_NEW_THRESHOLD = [0.454, 0.471, 0.519, 0.597, 0.6]


def test_true_positives_below_045_now_auto_allow():
    for score in OBSERVED_TRUE_POSITIVES_BELOW_NEW_THRESHOLD:
        assert band_for_score(score) == Band.ALLOW, (
            f"score {score} should be in ALLOW band, got {band_for_score(score)}"
        )


def test_true_positives_at_or_above_045_still_land_in_review_band():
    for score in OBSERVED_TRUE_POSITIVES_ABOVE_NEW_THRESHOLD:
        assert band_for_score(score) == Band.REVIEW, (
            f"score {score} should be in REVIEW band, got {band_for_score(score)}"
        )


def test_band_boundaries():
    assert band_for_score(0.0) == Band.ALLOW
    assert band_for_score(config.REVIEW_THRESHOLD - 0.01) == Band.ALLOW
    assert band_for_score(config.REVIEW_THRESHOLD) == Band.REVIEW
    assert band_for_score(config.BLOCK_THRESHOLD - 0.01) == Band.REVIEW
    assert band_for_score(config.BLOCK_THRESHOLD) == Band.BLOCK
    assert band_for_score(1.0) == Band.BLOCK


def test_score_frame_no_detections_is_allow():
    result = score_frame("f.jpg", 0, 0.0, [])
    assert result.max_score == 0.0
    assert result.band == Band.ALLOW


def test_score_frame_uses_max_detection_score():
    detections = [
        Detection(cls="BUTTOCKS_EXPOSED", score=0.3, box=[0, 0, 1, 1]),
        Detection(cls="FEMALE_BREAST_EXPOSED", score=0.6, box=[0, 0, 1, 1]),
    ]
    result = score_frame("f.jpg", 0, 0.0, detections)
    assert result.max_score == 0.6
    assert result.band == Band.REVIEW


def test_aggregate_worst_frame_wins():
    frames = [
        score_frame("f0.jpg", 0, 0.0, []),
        score_frame(
            "f1.jpg",
            1,
            1.0,
            [Detection(cls="BUTTOCKS_EXPOSED", score=0.7, box=[0, 0, 1, 1])],
        ),
        score_frame(
            "f2.jpg",
            2,
            2.0,
            [Detection(cls="FEMALE_BREAST_EXPOSED", score=0.5, box=[0, 0, 1, 1])],
        ),
    ]
    max_score, decision, reason, flagged_ratio = aggregate(frames)
    assert max_score == 0.7
    assert decision == Decision.AUTO_BLOCK
    assert reason["frame_path"] == "f1.jpg"
    assert flagged_ratio == 2 / 3


def test_aggregate_all_allow():
    frames = [score_frame(f"f{i}.jpg", i, float(i), []) for i in range(3)]
    max_score, decision, reason, flagged_ratio = aggregate(frames)
    assert max_score == 0.0
    assert decision == Decision.AUTO_ALLOW
    assert flagged_ratio == 0.0


def test_aggregate_empty_frames():
    max_score, decision, reason, flagged_ratio = aggregate([])
    assert decision == Decision.AUTO_BLOCK
    assert flagged_ratio == 0.0


def test_score_frame_with_error_is_review_band_not_allow():
    result = score_frame("f.jpg", 0, 0.0, [], error="unreadable or corrupt image")
    assert result.max_score == 0.0
    assert result.band == Band.REVIEW


def test_aggregate_errored_frame_forces_auto_block_even_with_zero_score():
    frames = [
        score_frame("f0.jpg", 0, 0.0, []),
        score_frame("f1.jpg", 1, 1.0, [], error="unreadable or corrupt image"),
        score_frame("f2.jpg", 2, 2.0, []),
    ]
    max_score, decision, reason, flagged_ratio = aggregate(frames)
    assert decision == Decision.AUTO_BLOCK
    assert reason["frame_path"] == "f1.jpg"
    assert flagged_ratio == 1 / 3
