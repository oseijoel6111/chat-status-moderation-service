import cv2
from nudenet import NudeDetector

import config
from models import Detection

_detector = None


def get_detector():
    global _detector
    if _detector is None:
        _detector = NudeDetector()
    return _detector


def _is_readable(path):
    img = cv2.imread(path)
    return img is not None


def detect_frames(frame_paths, batch_size=None):
    """Run nudity detection across a list of image paths.

    Returns a dict mapping frame_path -> (detections, error), where
    detections is a list[Detection] filtered to BLOCK_CLASSES (empty list on
    error), and error is None on success or a string describing the failure.

    Corrupt/unreadable files are skipped from the batch call and reported as
    errors individually, rather than failing the whole batch.
    """
    batch_size = config.DETECTION_BATCH_SIZE if batch_size is None else batch_size
    detector = get_detector()

    valid_paths = []
    results = {}
    for path in frame_paths:
        if _is_readable(path):
            valid_paths.append(path)
        else:
            results[path] = ([], "unreadable or corrupt image")

    if valid_paths:
        try:
            raw_results = detector.detect_batch(valid_paths, batch_size=batch_size)
        except Exception as exc:
            for path in valid_paths:
                results[path] = ([], f"detection failed: {exc}")
            raw_results = None

        if raw_results is not None:
            for path, raw in zip(valid_paths, raw_results):
                detections = [
                    Detection(cls=r["class"], score=r["score"], box=r["box"])
                    for r in raw
                    if r["class"] in config.BLOCK_CLASSES
                ]
                results[path] = (detections, None)

    return results
