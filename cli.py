import argparse
import json
import sys

import observability
import review_queue
from pipeline import run_moderation


def cmd_scan(args, media_type):
    result = run_moderation(args.path, media_type=media_type)
    print(f"asset_id: {result.asset_id}")
    print(f"decision: {result.decision.value}")
    print(f"max_score: {result.max_score:.3f}")
    print(f"flagged_ratio: {result.flagged_ratio * 100:.1f}%")
    print(f"reason: {json.dumps(result.decision_reason)}")
    for fr in result.frames:
        if fr.detections or fr.error:
            print(f"  {fr.frame_path}: band={fr.band.value} "
                  f"max_score={fr.max_score:.3f} error={fr.error}")


def cmd_review_list(args):
    conn = review_queue.get_connection()
    try:
        for row in review_queue.list_pending(conn, limit=args.limit):
            print(row)
    finally:
        conn.close()


def cmd_review_resolve(args):
    conn = review_queue.get_connection()
    try:
        review_queue.resolve(conn, args.id, args.resolution, args.notes)
        print(f"resolved review_queue id={args.id} as {args.resolution}")
    finally:
        conn.close()


def cmd_stats(args):
    print(json.dumps(observability.stats(), indent=2))


def main():
    parser = argparse.ArgumentParser(description="Blummify content moderation CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    p_image = sub.add_parser("scan-image", help="Scan a single image")
    p_image.add_argument("path")

    p_video = sub.add_parser("scan-video", help="Scan a video file")
    p_video.add_argument("path")

    p_review = sub.add_parser("review", help="Review queue operations")
    review_sub = p_review.add_subparsers(dest="review_command", required=True)

    p_review_list = review_sub.add_parser("list", help="List pending reviews")
    p_review_list.add_argument("--limit", type=int, default=50)

    p_review_resolve = review_sub.add_parser("resolve", help="Resolve a review item")
    p_review_resolve.add_argument("id", type=int)
    p_review_resolve.add_argument(
        "resolution", choices=["approved", "rejected", "escalated"]
    )
    p_review_resolve.add_argument("--notes", default=None)

    sub.add_parser("stats", help="Show score distribution and band counts")

    args = parser.parse_args()

    if args.command == "scan-image":
        cmd_scan(args, media_type="image")
    elif args.command == "scan-video":
        cmd_scan(args, media_type="video")
    elif args.command == "review":
        if args.review_command == "list":
            cmd_review_list(args)
        elif args.review_command == "resolve":
            cmd_review_resolve(args)
    elif args.command == "stats":
        cmd_stats(args)


if __name__ == "__main__":
    sys.exit(main())
