import os

import cv2

import config


def video_to_frames(video_path, out_dir, fps=None, max_frames=None):
    """Uniformly sample frames from video_path at approximately `fps` frames
    per second, writing JPEGs into out_dir. Falls back to even spacing across
    the video's duration if fps sampling would exceed max_frames.

    Returns a list of (frame_path, frame_index, timestamp_sec) tuples.
    """
    fps = config.SAMPLE_FPS if fps is None else fps
    max_frames = config.MAX_FRAMES if max_frames is None else max_frames

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError(f"Could not open video: {video_path}")

    try:
        native_fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
        total_native_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration_sec = total_native_frames / native_fps if native_fps else 0

        step_sec = 1.0 / fps
        sample_count = int(duration_sec / step_sec) + 1 if duration_sec else 0

        if max_frames and sample_count > max_frames:
            step_sec = duration_sec / max_frames
            sample_count = max_frames

        os.makedirs(out_dir, exist_ok=True)

        results = []
        for i in range(sample_count):
            timestamp_sec = i * step_sec
            cap.set(cv2.CAP_PROP_POS_MSEC, timestamp_sec * 1000)
            ok, frame = cap.read()
            if not ok:
                break
            frame_path = os.path.join(out_dir, f"frame_{i:04d}.jpg")
            cv2.imwrite(frame_path, frame)
            results.append((frame_path, i, timestamp_sec))

        return results
    finally:
        cap.release()
