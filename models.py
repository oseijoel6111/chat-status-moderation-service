from dataclasses import dataclass, field
from enum import Enum


class Band(str, Enum):
    ALLOW = "allow"
    REVIEW = "review"
    BLOCK = "block"


class Decision(str, Enum):
    AUTO_ALLOW = "auto_allow"
    AUTO_BLOCK = "auto_block"
    REVIEW = "review"


@dataclass
class Detection:
    cls: str
    score: float
    box: list


@dataclass
class FrameResult:
    frame_path: str
    frame_index: int
    timestamp_sec: float
    detections: list  # list[Detection], filtered to BLOCK_CLASSES
    max_score: float
    band: Band
    error: str | None = None


@dataclass
class ModerationResult:
    asset_id: str
    source_path: str
    media_type: str  # "image" | "video"
    frames: list  # list[FrameResult]
    max_score: float
    decision: Decision
    decision_reason: dict
    flagged_ratio: float = 0.0
