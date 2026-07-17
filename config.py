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
# Grounded in observed true-positive scores from test footage: 0.278, 0.28,
# 0.424, 0.454, 0.471, 0.519, 0.597, 0.6. These bounds are a starting point,
# not permanent — revisit using observability.stats() once real volume
# accumulates.
REVIEW_THRESHOLD = float(os.environ.get("MODERATION_REVIEW_THRESHOLD", 0.25))
BLOCK_THRESHOLD = float(os.environ.get("MODERATION_BLOCK_THRESHOLD", 0.65))

SAMPLE_FPS = float(os.environ.get("MODERATION_SAMPLE_FPS", 1.0))
MAX_FRAMES = int(os.environ.get("MODERATION_MAX_FRAMES", 300))
DETECTION_BATCH_SIZE = int(os.environ.get("MODERATION_BATCH_SIZE", 4))

DB_PATH = os.environ.get("MODERATION_DB_PATH", "data/moderation.db")
SCHEMA_PATH = os.environ.get("MODERATION_SCHEMA_PATH", "db/schema.sql")
LOG_PATH = os.environ.get("MODERATION_LOG_PATH", "logs/scores.jsonl")

MODEL_VERSION = "nudenet-3.4.2"
