#!/usr/bin/env python3
"""Verify the fixed master delivery profile with ffprobe."""

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


def verify(metadata: dict[str, Any]) -> tuple[list[str], dict[str, Any]]:
    streams = metadata.get("streams", [])
    video = next((item for item in streams if item.get("codec_type") == "video"), None)
    audio = next((item for item in streams if item.get("codec_type") == "audio"), None)
    errors: list[str] = []

    if video is None:
        return ["missing video stream"], {}
    if audio is not None:
        errors.append("unexpected audio stream: the fixed master must have no audio stream")
    if any(item.get("codec_type") == "subtitle" for item in streams):
        errors.append("unexpected subtitle stream: the fixed master must have no subtitle stream")

    expected_video = {
        "codec_name": "h264",
        "profile": "High",
        "width": 2560,
        "height": 1440,
        "pix_fmt": "yuv420p",
        "color_range": "tv",
        "color_space": "bt709",
        "color_transfer": "bt709",
        "color_primaries": "bt709",
    }
    for key, expected in expected_video.items():
        actual = video.get(key)
        if actual != expected:
            errors.append(f"video.{key}: expected {expected!r}, got {actual!r}")

    average_fps = fps(video.get("avg_frame_rate"))
    nominal_fps = fps(video.get("r_frame_rate"))
    if average_fps is None or abs(average_fps - 60.0) > 0.001:
        errors.append(f"video.avg_frame_rate: expected 60 CFR, got {video.get('avg_frame_rate')!r}")
    if nominal_fps is None or abs(nominal_fps - 60.0) > 0.001:
        errors.append(f"video.r_frame_rate: expected 60, got {video.get('r_frame_rate')!r}")

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
        description="Verify silent H.264 High / Rec.709 / 2560x1440 / 60fps CFR master media"
    )
    parser.add_argument("media", type=Path, help="Final MP4 to inspect")
    parser.add_argument("--ffprobe", help="Absolute ffprobe executable path when it is not on PATH")
    parser.add_argument("--json", action="store_true", help="Print machine-readable result")
    args = parser.parse_args()

    media = args.media.expanduser().resolve()
    if not media.is_file():
        print(f"ERROR: media not found: {media}", file=sys.stderr)
        return 2
    try:
        ffprobe = resolve_ffprobe(args.ffprobe)
        errors, summary = verify(probe(media, ffprobe))
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
