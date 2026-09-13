#!/usr/bin/env python3
"""Build a timeline-aligned 48 kHz WAV stem from AI-video source audio."""

from __future__ import annotations

import argparse
import csv
import json
import shutil
import subprocess
import tempfile
from pathlib import Path


def run(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, text=True, capture_output=True, encoding="utf-8", errors="replace")


def has_audio(ffprobe: str, path: Path) -> bool:
    if not path.is_file():
        raise SystemExit(f"AI-video source is missing: {path}")
    try:
        result = run([ffprobe, "-v", "error", "-select_streams", "a", "-show_entries", "stream=index", "-of", "csv=p=0", str(path)])
    except OSError as exc:
        raise SystemExit(f"Unable to probe AI-video source {path}: {exc}") from exc
    if result.returncode:
        raise SystemExit(f"AI-video probe failed for {path}: {result.stderr.strip() or result.stdout.strip() or result.returncode}")
    return bool(result.stdout.strip())


def main() -> int:
    parser = argparse.ArgumentParser(description="Create an AI-video original-audio stem and CSV manifest.")
    parser.add_argument("plan", type=Path, help="JSON with timeline_duration and clips")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--csv", type=Path, required=True)
    parser.add_argument("--ffmpeg")
    parser.add_argument("--ffprobe")
    args = parser.parse_args()
    ffmpeg = args.ffmpeg or shutil.which("ffmpeg")
    ffprobe = args.ffprobe or shutil.which("ffprobe")
    if not ffmpeg or not ffprobe:
        raise SystemExit("ffmpeg and ffprobe are required")
    plan_path = args.plan.expanduser().resolve()
    plan = json.loads(plan_path.read_text(encoding="utf-8-sig"))
    root = plan_path.parent
    duration = float(plan["timeline_duration"])
    rows = []
    audible = []
    for clip in plan.get("clips", []):
        source = Path(clip["source"]).expanduser()
        if not source.is_absolute():
            source = (root / source).resolve()
        voiced = has_audio(ffprobe, source)
        present = True
        row = {"id": clip.get("id", ""), "source": str(source), "timeline_start": float(clip.get("timeline_start", 0)), "source_start": float(clip.get("source_start", 0)), "duration": float(clip.get("duration", 0)), "file_exists": present, "has_audio": voiced, "decision": clip.get("decision", "REVIEW")}
        rows.append(row)
        if voiced and row["duration"] > 0:
            audible.append(row)
    output = args.output.expanduser().resolve(); output.parent.mkdir(parents=True, exist_ok=True)
    csv_path = args.csv.expanduser().resolve(); csv_path.parent.mkdir(parents=True, exist_ok=True)
    protected = {plan_path, *(Path(row["source"]).resolve() for row in rows)}
    if output == csv_path or output in protected or csv_path in protected:
        raise SystemExit("Output WAV and CSV must be distinct and must not overwrite input files")
    if audible:
        command = [ffmpeg, "-hide_banner", "-loglevel", "error", "-y"]
        for row in audible:
            command += ["-i", row["source"]]
        filters = []
        labels = []
        for i, row in enumerate(audible):
            delay = max(0, round(row["timeline_start"] * 1000))
            label = f"a{i}"
            filters.append(f"[{i}:a]atrim=start={row['source_start']:.6f}:duration={row['duration']:.6f},asetpts=PTS-STARTPTS,aresample=48000,aformat=channel_layouts=stereo,adelay={delay}|{delay}[{label}]")
            labels.append(f"[{label}]")
        filters.append(f"{''.join(labels)}amix=inputs={len(labels)}:duration=longest:normalize=0,apad=whole_dur={duration:.6f},atrim=duration={duration:.6f}[out]")
        command += ["-filter_complex", ";".join(filters), "-map", "[out]", "-c:a", "pcm_s24le", str(output)]
    else:
        command = [ffmpeg, "-hide_banner", "-loglevel", "error", "-y", "-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo", "-t", f"{duration:.6f}", "-c:a", "pcm_s24le", str(output)]
    # Only publish a complete stem; failed FFmpeg runs cannot replace a good one.
    with tempfile.NamedTemporaryFile(prefix=f"{output.stem}-", suffix=".partial.wav", dir=output.parent, delete=False) as handle:
        partial = Path(handle.name)
    command[-1] = str(partial)
    try:
        result = run(command)
        if result.returncode:
            raise SystemExit(result.stderr.strip() or result.stdout.strip())
        if not partial.is_file() or partial.stat().st_size == 0:
            raise SystemExit("FFmpeg reported success without producing a nonempty AI audio stem")
        partial.replace(output)
    except OSError as exc:
        raise SystemExit(f"AI audio stem build failed: {exc}") from exc
    finally:
        partial.unlink(missing_ok=True)
    fields = ["id", "source", "timeline_start", "source_start", "duration", "file_exists", "has_audio", "decision"]
    with csv_path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields); writer.writeheader(); writer.writerows(rows)
    print(json.dumps({"stem": str(output), "manifest": str(csv_path), "clips": len(rows), "audible_clips": len(audible)}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
