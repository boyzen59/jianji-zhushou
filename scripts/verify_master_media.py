#!/usr/bin/env python3
"""Verify an explicit delivery profile; defaults preserve the legacy editing-master profile."""

from __future__ import annotations

import argparse
from fractions import Fraction
import json
from pathlib import Path
import shutil
import subprocess
import sys
from typing import Any


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


def resolve_ffprobe(explicit: str | None) -> str:
    if explicit:
        candidate = Path(explicit).expanduser().resolve()
        if not candidate.is_file():
            raise FileNotFoundError(f"ffprobe not found: {candidate}")
        return str(candidate)
    found = shutil.which("ffprobe")
    if not found:
        raise FileNotFoundError("ffprobe is not on PATH; pass --ffprobe with an absolute path")
    return found


def probe(path: Path, ffprobe: str) -> dict[str, Any]:
    command = [
        ffprobe,
        "-v",
        "error",
        "-show_streams",
        "-show_format",
        "-of",
        "json",
        str(path),
    ]
    completed = subprocess.run(command, check=True, capture_output=True, text=True, encoding="utf-8")
    return json.loads(completed.stdout)


def fps(value: Any) -> float | None:
    if not value or value == "0/0":
        return None
    try:
        return float(Fraction(str(value)))
    except (ValueError, ZeroDivisionError):
        return None


def verify(metadata: dict[str, Any], *, width: int = 2560, height: int = 1440,
           frame_rate: float = 60, audio_policy: str = "none",
           expected_frames: int | None = None) -> tuple[list[str], dict[str, Any]]:
    streams = metadata.get("streams", [])
    video = next((item for item in streams if item.get("codec_type") == "video"), None)
    audio = next((item for item in streams if item.get("codec_type") == "audio"), None)
    errors: list[str] = []

    if video is None:
        return ["missing video stream"], {}
    if audio is not None and audio_policy == "none":
        errors.append("unexpected audio stream: the selected profile requires no audio stream")
    if audio is None and audio_policy == "required":
        errors.append("missing audio stream: the selected profile requires audio")
    if any(item.get("codec_type") == "subtitle" for item in streams):
        errors.append("unexpected subtitle stream: the fixed master must have no subtitle stream")

    expected_video = {
        "codec_name": "h264",
        "profile": "High",
        "width": width,
        "height": height,
        "pix_fmt": "yuv420p",
        "color_range": "tv",
        "color_space": "bt709",
        "color_transfer": "bt709",
        "color_primaries": "bt709",
    }
    for key, expected in expected_video.items():
        actual = video.get(key)
        # Small FFprobe builds can return the H.264 profile_idc instead of its name.
        # AV_PROFILE_H264_HIGH = 100: https://ffmpeg.org/doxygen/trunk/defs_8h.html
        if key == "profile" and video.get("codec_name") == "h264" and str(actual) == "100":
            actual = "High"
        if actual != expected:
            errors.append(f"video.{key}: expected {expected!r}, got {actual!r}")

    average_fps = fps(video.get("avg_frame_rate"))
    nominal_fps = fps(video.get("r_frame_rate"))
    if average_fps is None or abs(average_fps - frame_rate) > 0.001:
        errors.append(f"video.avg_frame_rate: expected {frame_rate}, got {video.get('avg_frame_rate')!r}")
    if nominal_fps is None or abs(nominal_fps - frame_rate) > 0.001:
        errors.append(f"video.r_frame_rate: expected {frame_rate}, got {video.get('r_frame_rate')!r}")
    if expected_frames is not None and str(video.get("nb_frames")) != str(expected_frames):
        errors.append(f"video.nb_frames: expected {expected_frames}, got {video.get('nb_frames')!r}")

    format_name = str(metadata.get("format", {}).get("format_name", ""))
    if "mp4" not in format_name:
        errors.append(f"container: expected MP4, got {format_name!r}")

    summary = {
        "container": format_name,
        "video": {
            key: video.get(key)
            for key in [
                "codec_name",
                "profile",
                "level",
                "width",
                "height",
                "pix_fmt",
                "r_frame_rate",
                "avg_frame_rate",
                "color_range",
                "color_space",
                "color_transfer",
                "color_primaries",
            ]
        },
        "audio": None
        if audio is None
        else {key: audio.get(key) for key in ["codec_name", "sample_rate", "channels", "channel_layout"]},
    }
    return errors, summary


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Verify H.264 High / Rec.709 MP4 against the selected dimensions, fps and audio policy; defaults are a silent 1440p60 editing master"
    )
    parser.add_argument("media", type=Path, help="Final MP4 to inspect")
    parser.add_argument("--ffprobe", help="Absolute ffprobe executable path when it is not on PATH")
    parser.add_argument("--json", action="store_true", help="Print machine-readable result")
    parser.add_argument("--width", type=int, default=2560)
    parser.add_argument("--height", type=int, default=1440)
    parser.add_argument("--fps", type=float, default=60)
    parser.add_argument("--audio", choices=("none", "required", "either"), default="none")
    parser.add_argument("--expected-frames", type=int)
    args = parser.parse_args()
    if args.width <= 0 or args.height <= 0 or not 0 < args.fps <= 240:
        parser.error("dimensions and fps must be positive; fps must be at most 240")
    if args.expected_frames is not None and args.expected_frames <= 0:
        parser.error("expected frames must be positive")

    media = args.media.expanduser().resolve()
    if not media.is_file():
        print(f"ERROR: media not found: {media}", file=sys.stderr)
        return 2
    try:
        ffprobe = resolve_ffprobe(args.ffprobe)
        errors, summary = verify(probe(media, ffprobe), width=args.width, height=args.height,
                                 frame_rate=args.fps, audio_policy=args.audio, expected_frames=args.expected_frames)
    except (FileNotFoundError, subprocess.CalledProcessError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    result = {"status": "PASS" if not errors else "FAIL", "file": str(media), "errors": errors, "probe": summary}
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"Master media: {result['status']}")
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
