import os

BLOCK_CLASSES = {
    "FEMALE_GENITALIA_EXPOSED",
    "MALE_GENITALIA_EXPOSED",
    "FEMALE_BREAST_EXPOSED",
    "BUTTOCKS_EXPOSED",
    "ANUS_EXPOSED",
}

# Banding thresholds on the max BLOCK_CLASSES score for a frame/image.
# score < REVIEW_THRESHOLD           -> auto_allow
# REVIEW_THRESHOLD <= score < BLOCK_THRESHOLD -> review
# score >= BLOCK_THRESHOLD           -> auto_block
#
# NOTE: human review was removed downstream (scoring.aggregate() now maps
# both review and block bands to Decision.AUTO_BLOCK), so REVIEW_THRESHOLD
# is the only number that affects outcomes today — BLOCK_THRESHOLD no longer
# changes any decision, only the internal Band label used for logging/stats.
#
# Originally grounded in observed true-positive scores from test footage:
# 0.278, 0.28, 0.424, 0.454, 0.471, 0.519, 0.597, 0.6. Raised from 0.25 to
# 0.45 after real production volume (87k scored frames, 3350 assets) showed
# 15.4% of all posted content auto-blocking, 42% of those in the lowest
# [0.25, 0.35) band and dominated by FEMALE_BREAST_EXPOSED/BUTTOCKS_EXPOSED —
# the two classes NudeNet is known to false-positive on most (tight
# clothing, skin-tone/texture confusion). Accepted trade-off: 3 of the 8
# calibration true positives above (0.278, 0.28, 0.424) now fall below this
# bar and resolve to auto_allow — a deliberate reduction in false blocks at
# the cost of some real violations in that range no longer being caught by
# this threshold alone. Revisit with per-class thresholds (lower bar for
# genitalia-exposed classes, higher for breast/buttocks) if false-positive
# reports continue.
REVIEW_THRESHOLD = float(os.environ.get("MODERATION_REVIEW_THRESHOLD", 0.45))
BLOCK_THRESHOLD = float(os.environ.get("MODERATION_BLOCK_THRESHOLD", 0.65))

SAMPLE_FPS = float(os.environ.get("MODERATION_SAMPLE_FPS", 1.0))
MAX_FRAMES = int(os.environ.get("MODERATION_MAX_FRAMES", 300))
DETECTION_BATCH_SIZE = int(os.environ.get("MODERATION_BATCH_SIZE", 4))

DB_PATH = os.environ.get("MODERATION_DB_PATH", "data/moderation.db")
SCHEMA_PATH = os.environ.get("MODERATION_SCHEMA_PATH", "db/schema.sql")
LOG_PATH = os.environ.get("MODERATION_LOG_PATH", "logs/scores.jsonl")

MODEL_VERSION = "nudenet-3.4.2"
