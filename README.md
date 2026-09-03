# Chat Status Moderation Service

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python&logoColor=white" alt="Python 3.11+"/>
  <img src="https://img.shields.io/badge/FastAPI-service-009688?logo=fastapi&logoColor=white" alt="FastAPI service"/>
  <img src="https://img.shields.io/badge/pytest-tested-0A9EDC?logo=pytest&logoColor=white" alt="pytest tested"/>
  <img src="https://img.shields.io/badge/NudeNet-3.4.2-111827" alt="NudeNet 3.4.2"/>
  <a href="https://github.com/oseijoel6111/chat-status-moderation-service/stargazers">
    <img src="https://img.shields.io/github/stars/oseijoel6111/chat-status-moderation-service?style=social" alt="GitHub stars"/>
  </a>
</p>

Content moderation pipeline for chat status images and videos. The service
samples media, runs nudity detection, scores each frame, stores audit records,
and returns an asset-level decision that can be used by a chat application
before media is published.

## What It Does

- Scans image and video uploads through a single moderation pipeline.
- Samples video frames with OpenCV before running detection.
- Filters detection output to policy-relevant exposed-body classes.
- Aggregates frame-level scores into an asset-level allow/block decision.
- Persists asset decisions, frame scores, and scan metadata to SQLite.
- Provides both a FastAPI HTTP surface and a local CLI.
- Keeps observability data in JSONL so moderation behavior can be audited.

## Architecture

```text
media path
  |
  v
pipeline.py
  |
  +-- extraction.py      video frame sampling
  +-- detection.py       NudeNet inference wrapper
  +-- scoring.py         threshold bands and asset decision
  +-- csam.py            CSAM provider placeholder
  +-- review_queue.py    SQLite persistence and queue helpers
  +-- observability.py   JSONL score logging and stats
```

## Quick Start

Create a virtual environment and install the runtime dependencies:

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Run the test suite:

```bash
pytest
```

Scan an image:

```bash
python cli.py scan-image ./sample.jpg
```

Scan a video:

```bash
python cli.py scan-video ./sample.mp4
```

Start the API:

```bash
uvicorn api:app --reload
```

Then call the moderation endpoint:

```bash
curl -X POST http://127.0.0.1:8000/moderate \
  -H "Content-Type: application/json" \
  -d '{"path":"./sample.jpg","media_type":"image"}'
```

Example response:

```json
{
  "decision": "auto_allow",
  "max_score": 0.0,
  "reason": {
    "frame_path": "./sample.jpg",
    "frame_index": 0,
    "max_score": 0.0,
    "band": "allow",
    "classes": []
  }
}
```

## Configuration

The service is configured with environment variables:

| Variable | Default | Purpose |
| --- | --- | --- |
| `MODERATION_REVIEW_THRESHOLD` | `0.75` | Score where content enters the internal review band. |
| `MODERATION_BLOCK_THRESHOLD` | `0.75` | Score where content is treated as blocked. |
| `MODERATION_SAMPLE_FPS` | `1.0` | Video frame sampling rate. |
| `MODERATION_MAX_FRAMES` | `300` | Maximum sampled frames per video. |
| `MODERATION_BATCH_SIZE` | `4` | Detection batch size. |
| `MODERATION_DB_PATH` | `data/moderation.db` | SQLite database path. |
| `MODERATION_SCHEMA_PATH` | `db/schema.sql` | Schema file used to initialize SQLite. |
| `MODERATION_LOG_PATH` | `logs/scores.jsonl` | JSONL score log path. |

## CLI Reference

```bash
python cli.py scan-image <path>
python cli.py scan-video <path>
python cli.py review list --limit 50
python cli.py review resolve <id> approved --notes "manual review passed"
python cli.py stats
```

## Moderation Policy Notes

This project is designed for defensive moderation workflows. It stores the
decision path for every asset so teams can audit false positives, threshold
changes, and model behavior over time.

The current scoring policy is intentionally conservative around scan failures:
assets that cannot be read or scored are not silently treated as clean.

## Data Storage

SQLite tables are defined in `db/schema.sql`:

- `moderation_assets` stores the asset-level decision.
- `moderation_frames` stores per-frame scores and detected classes.
- `review_queue` stores manual review state.
- `csam_scan_results` stores provider scan metadata when a provider is wired in.

Runtime data is written under `data/` and `logs/` by default.

## Contributing

Useful contributions include:

- Per-class threshold tuning for lower false-positive rates.
- A real CSAM provider integration behind the existing `csam.py` interface.
- Async/background processing for larger video queues.
- Better review tooling and reviewer assignment workflows.
- CI coverage for detection, scoring, and API behavior.

For profile achievements, make changes through pull requests when possible.
That keeps the project easier to review and naturally builds toward GitHub
collaboration achievements.
