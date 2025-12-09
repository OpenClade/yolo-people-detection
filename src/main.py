import argparse
import os
from ultralytics import YOLO
from application import Application


def parse_args():
    parser = argparse.ArgumentParser(
        description="Video Zone Editor — draw restricted areas on paused video frames."
    )
    parser.add_argument(
        "--model",
        required=True,
        help="Path to the YOLO model file (.pt)"
    )
    parser.add_argument(
        "--video",
        required=True,
        help="Path to the input video file"
    )
    parser.add_argument(
        "--zones",
        default="data/restricted_zones.json",
        help="Path where restricted zones will be saved/loaded"
    )
    return parser.parse_args()


def validate_paths(model_path: str, video_path: str):
    if not os.path.isfile(model_path):
        raise FileNotFoundError(f"❌ Model file not found: {model_path}")
    if not os.path.isfile(video_path):
        raise FileNotFoundError(f"❌ Video file not found: {video_path}")


def main():
    args = parse_args()
    validate_paths(args.model, args.video)

    print("📦 Loading YOLO model...")
    model = YOLO(args.model)
    print(f"✅ Model loaded: {args.model}")

    editor = Application(zones_path=args.zones, model=model)
    editor.run(video_path=args.video)


if __name__ == "__main__":
    main()
