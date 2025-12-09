# Smart Head - Video Zone Intrusion Detection System

Real-time video surveillance system that detects person intrusions in user-defined restricted zones using YOLO object detection and tracking

## Installation

### Prerequisites

- Python 3.11
- uv package manager

### Setup

```bash
uv sync
```

Download YOLO model:
```bash
https://docs.ultralytics.com/ru/
```

## Usage

```bash
uv run src/main.py --model yolov11n.pt --video path/to/video.mp4
```

With custom zone file:
```bash
uv run src/main.py --model yolov11n.pt --video demo.mp4 --zones data/zones.json
```

## Controls

**Keyboard:**
- `SPACE` - Pause/play video
- `E` - Toggle edit mode (requires pause)
- `F` - Finish polygon (min 3 points)
- `S` - Save zones to file
- `C` - Clear all zones
- `M` - Toggle monitoring
- `D` - Run detection on current frame
- `Q` / `ESC` - Exit

**Mouse (Edit Mode):**
- Left click - Add polygon point
- Right click - Remove last point

## Workflow

1. Start application with video and model
2. Pause (SPACE) and enable edit mode (E)
3. Click to draw polygon around restricted area
4. Finish polygon (F) and save (S)
5. Resume playback (SPACE) to monitor intrusions

## Implementation Details

**Intrusion Detection:**
- Dual-point checking: tests person's center and bottom points
- Handles partial intrusions and various camera angles
- Uses OpenCV pointPolygonTest for geometry calculations

**Alarm System:**
- Individual tracking per person with unique IDs from YOLO
- 3-second grace period before clearing each intruder
