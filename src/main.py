import ultralytics
import argparse
import os


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--model", help="Path to the YOLO model file", required=True)
    parser.add_argument(
        "--video", help="Path to input video file", required=True)
    args = parser.parse_args()

    model_path = args.model
    video_path = args.video

    if not os.path.isfile(model_path):
        raise FileNotFoundError(f"Model file not found: {model_path}")
    if not os.path.isfile(video_path):
        raise FileNotFoundError(f"Video file not found: {video_path}")

    yolo = ultralytics.YOLO(args.model)
    print(f"Loaded model: {args.model}")


if __name__ == "__main__":
    main()
