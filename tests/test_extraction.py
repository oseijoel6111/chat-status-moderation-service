import os
import tempfile

import pytest

from extraction import video_to_frames

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VIDEO_PATH = os.path.join(REPO_ROOT, "video.mp4")

pytestmark = pytest.mark.skipif(
    not os.path.exists(VIDEO_PATH), reason="sample video.mp4 fixture not present"
)


def test_default_1fps_sampling_matches_known_duration():
    # video.mp4 is ~29.03s at 30fps -> ~30 frames at 1fps sampling.
    with tempfile.TemporaryDirectory() as tmp_dir:
        results = video_to_frames(VIDEO_PATH, tmp_dir, fps=1.0)
        assert 28 <= len(results) <= 31
        for path, _, _ in results:
            assert os.path.exists(path)


def test_max_frames_cap_is_respected():
    with tempfile.TemporaryDirectory() as tmp_dir:
        results = video_to_frames(VIDEO_PATH, tmp_dir, fps=1.0, max_frames=5)
    assert len(results) <= 5


def test_frame_indices_and_timestamps_are_monotonic():
    with tempfile.TemporaryDirectory() as tmp_dir:
        results = video_to_frames(VIDEO_PATH, tmp_dir, fps=1.0)
    indices = [idx for _, idx, _ in results]
    timestamps = [ts for _, _, ts in results]
    assert indices == sorted(indices)
    assert timestamps == sorted(timestamps)


def test_invalid_video_path_raises():
    with tempfile.TemporaryDirectory() as tmp_dir:
        with pytest.raises(ValueError):
            video_to_frames(os.path.join(tmp_dir, "does-not-exist.mp4"), tmp_dir)
