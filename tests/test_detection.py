import os

import pytest

import detection

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SAMPLE_IMAGE = os.path.join(REPO_ROOT, "man.jpeg")

pytestmark = pytest.mark.skipif(
    not os.path.exists(SAMPLE_IMAGE), reason="sample image fixture not present"
)


def test_corrupt_file_reported_as_error_not_raised(tmp_path):
    bogus = tmp_path / "not_an_image.jpg"
    bogus.write_bytes(b"this is not image data")

    results = detection.detect_frames([str(bogus)])

    detections, error = results[str(bogus)]
    assert detections == []
    assert error is not None


def test_missing_file_reported_as_error_not_raised(tmp_path):
    missing = tmp_path / "does-not-exist.jpg"

    results = detection.detect_frames([str(missing)])

    detections, error = results[str(missing)]
    assert detections == []
    assert error is not None


def test_valid_image_is_detected_without_error():
    results = detection.detect_frames([SAMPLE_IMAGE])

    detections, error = results[SAMPLE_IMAGE]
    assert error is None
    assert isinstance(detections, list)


def test_mixed_valid_and_corrupt_batch(tmp_path):
    bogus = tmp_path / "bad.jpg"
    bogus.write_bytes(b"garbage")

    results = detection.detect_frames([SAMPLE_IMAGE, str(bogus)])

    assert results[SAMPLE_IMAGE][1] is None
    assert results[str(bogus)][1] is not None
