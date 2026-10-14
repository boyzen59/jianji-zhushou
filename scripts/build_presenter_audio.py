#!/usr/bin/env python3
"""Split narration into exact clips, 3-second countdown guides and reading text.

Plan: {"source_audio": "long.wav", "segments": [{"id": "P001",
"source_start": 12.5, "source_end": 20, "narration_zh": "中文口播文稿"}]}.
Legacy start/end and caption_zh/text_zh input keys remain supported.
Only exact WAVs belong on the video timeline. Guides are recording aids:
Three cue tones at 0, 1 and 2 seconds; the exact clip begins at 3.00 seconds.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import re
import shutil
import subprocess
from pathlib import Path


SAMPLE_RATE = 48000
COUNTDOWN_SECONDS = 3.0
BEEP_SECONDS = 0.15
BEEP_HZ = 880
METADATA_FIELDS = ("review_id", "scene_id", "chapter", "presenter_arrangement_zh", "selection_reason_zh", "target_range_zh")
FIELDS = [
    "id", *METADATA_FIELDS, "narration_zh", "source_audio", "source_start", "source_end",
    "voice_seconds", "exact_audio_seconds", "guide_audio_seconds",
    "guide_countdown_seconds", "guide_cue_start_seconds",
    "guide_beep_seconds", "guide_beep_hz", "guide_voice_start_seconds",
    "exact_wav", "guide_wav", "reading_text",
]


def seconds(value) -> float:
    if isinstance(value, bool):
        raise ValueError("time cannot be a boolean")
    parts = str(value).replace(",", ".").split(":")
    if not 1 <= len(parts) <= 3:
        raise ValueError(f"invalid time: {value}")
    numbers = [float(part) for part in parts]
    if any(not math.isfinite(part) or part < 0 for part in numbers):
        raise ValueError(f"time must be finite and nonnegative: {value}")
    if len(parts) > 1 and (any(part >= 60 for part in numbers[1:]) or any(part != int(part) for part in numbers[:-1])):
        raise ValueError(f"invalid timecode: {value}")
    return sum(part * (60 ** i) for i, part in enumerate(reversed(numbers)))


def run(command: list[str]) -> str:
    result = subprocess.run(command, text=True, capture_output=True, encoding="utf-8", errors="replace")
    if result.returncode:
        raise ValueError(result.stderr.strip() or result.stdout.strip())
    return result.stdout


def probe_duration(ffmpeg: str, source: Path) -> float:
    ffprobe = Path(ffmpeg).with_name("ffprobe.exe" if Path(ffmpeg).suffix.lower() == ".exe" else "ffprobe")
    executable = str(ffprobe) if ffprobe.is_file() else shutil.which("ffprobe")
    if not executable:
        raise ValueError("ffprobe is required beside ffmpeg or on PATH to validate source ranges")
    metadata = json.loads(run([
        executable, "-v", "error", "-select_streams", "a:0", "-show_entries",
        "stream=duration:format=duration", "-of", "json", str(source),
    ]))
    if not metadata.get("streams"):
        raise ValueError("source has no audio stream")
    for candidate in (metadata["streams"][0].get("duration"), metadata.get("format", {}).get("duration")):
        if candidate not in (None, "N/A"):
            duration = float(candidate)
            if math.isfinite(duration) and duration > 0:
                return duration
    raise ValueError("cannot determine source audio duration")


def source_time(segment: dict, name: str) -> float:
    preferred = f"source_{name}"
    value = seconds(segment[preferred] if preferred in segment else segment[name])
    if preferred in segment and name in segment and value != seconds(segment[name]):
        raise ValueError(f"conflicting {preferred}/{name} values")
    return value


def validate_segments(plan: dict, source_duration: float) -> list[dict]:
    segments = plan.get("segments")
    if not isinstance(segments, list) or not segments:
        raise ValueError("segments must be a nonempty list")
    validated = []
    seen = set()
    for segment in segments:
        if not isinstance(segment, dict):
            raise ValueError("each segment must be an object")
        ident = str(segment["id"])
        if not re.fullmatch(r"[\w-]{1,100}", ident) or re.fullmatch(r"(?i:CON|PRN|AUX|NUL|COM[0-9]|LPT[0-9])", ident):
            raise ValueError(f"unsafe segment id: {ident!r}; use letters, digits, underscores or hyphens")
        if ident.casefold() in seen:
            raise ValueError(f"duplicate segment id: {ident}")
        seen.add(ident.casefold())
        start, end = source_time(segment, "start"), source_time(segment, "end")
        if end <= start or end - start < 1 / SAMPLE_RATE:
            raise ValueError(f"invalid or empty range for {ident}: {start}..{end}")
        if end > source_duration + 0.5 / SAMPLE_RATE:
            raise ValueError(f"range for {ident} ends at {end}s, beyond source duration {source_duration}s")
        narration = segment.get("narration_zh", segment.get("caption_zh", segment.get("text_zh", "")))
        if not isinstance(narration, str) or not narration.strip():
            raise ValueError(f"narration_zh must contain the complete reading passage for {ident}")
        metadata = {key: segment.get(key, "") for key in METADATA_FIELDS}
        if any(not isinstance(value, str) for value in metadata.values()):
            raise ValueError(f"recording metadata must be text for {ident}")
        validated.append({"id": ident, "start": start, "end": end, "narration_zh": narration, **metadata})
    return validated


def main() -> int:
    parser = argparse.ArgumentParser(description="Create exact WAVs, 3-second countdown guides and full reading text.")
    parser.add_argument("plan", type=Path, help="JSON with source_audio and segments")
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--ffmpeg", help="FFmpeg executable; ffprobe must be beside it or on PATH")
    args = parser.parse_args()
    ffmpeg = shutil.which(args.ffmpeg or "ffmpeg")
    if not ffmpeg:
        raise SystemExit("ffmpeg is required")
    try:
        plan_path = args.plan.expanduser().resolve()
        plan = json.loads(plan_path.read_text(encoding="utf-8-sig"))
        if not isinstance(plan, dict):
            raise ValueError("plan must be an object")
        source = Path(plan["source_audio"]).expanduser()
        source = (plan_path.parent / source).resolve() if not source.is_absolute() else source.resolve()
        if not source.is_file():
            raise ValueError(f"source audio not found: {source}")
        segments = validate_segments(plan, probe_duration(ffmpeg, source))
        out = args.output_dir.expanduser().resolve()
        exact_dir, guide_dir, text_dir = out / "exact", out / "guide", out / "reading"
        for folder in (exact_dir, guide_dir, text_dir):
            folder.mkdir(parents=True, exist_ok=True)
        rows = []
        for segment in segments:
            ident, start, end = segment["id"], segment["start"], segment["end"]
            exact = exact_dir / f"{ident}_exact.wav"
            guide = guide_dir / f"{ident}_3s-countdown-guide.wav"
            reading = text_dir / f"{ident}_完整朗读文案.txt"
            if source in (exact, guide):
                raise ValueError("output path must not overwrite the source audio")
            # Standardize the split once; the guide reuses its exact PCM voice samples.
            run([ffmpeg, "-hide_banner", "-loglevel", "error", "-y", "-i", str(source),
                 "-map", "0:a:0", "-af", f"atrim=start={start:.9f}:end={end:.9f},asetpts=PTS-STARTPTS",
                 "-ar", str(SAMPLE_RATE), "-ac", "2", "-c:a", "pcm_s24le", str(exact)])
            graph = (
                f"aevalsrc=exprs='0.12*sin(2*PI*{BEEP_HZ}*t)*lt(mod(t,1),{BEEP_SECONDS})':s={SAMPLE_RATE}:d={COUNTDOWN_SECONDS},"
                "aformat=sample_fmts=s32:channel_layouts=stereo[pre];"
                "[0:a]aformat=sample_fmts=s32,asetpts=PTS-STARTPTS[voice];"
                "[pre][voice]concat=n=2:v=0:a=1[out]"
            )
            run([ffmpeg, "-hide_banner", "-loglevel", "error", "-y", "-i", str(exact),
                 "-filter_complex", graph, "-map", "[out]", "-c:a", "pcm_s24le", str(guide)])
            reading.write_text(segment['narration_zh'].strip() + '\n', encoding='utf-8')
            rows.append({
                "id": ident, "narration_zh": segment["narration_zh"], "source_audio": str(source),
                **{key: segment[key] for key in METADATA_FIELDS},
                "source_start": start, "source_end": end, "voice_seconds": end - start,
                "exact_audio_seconds": probe_duration(ffmpeg, exact), "guide_audio_seconds": probe_duration(ffmpeg, guide),
                "guide_countdown_seconds": COUNTDOWN_SECONDS,
                "guide_cue_start_seconds": "0;1;2", "guide_beep_seconds": BEEP_SECONDS,
                "guide_beep_hz": BEEP_HZ, "guide_voice_start_seconds": COUNTDOWN_SECONDS,
                "exact_wav": str(exact), "guide_wav": str(guide), "reading_text": str(reading),
            })
        manifest = out / "presenter-recording-list.csv"
        with manifest.open("w", newline="", encoding="utf-8-sig") as handle:
            writer = csv.DictWriter(handle, fieldnames=FIELDS)
            writer.writeheader()
            writer.writerows(rows)
        handbook = out / '真人露脸录制手册.md'
        sections = ['# 真人露脸录制手册', '每段先读完整文案，再播放录制版准备。提示音在0、1、2秒响起，第3秒开始对应原声。倒计时不进入成片。']
        for row in rows:
            sections.extend([
                f"## {row['id']} {row['chapter']}",
                f"选用原因：{row['selection_reason_zh']}。出镜范围：{row['target_range_zh']}。{row['presenter_arrangement_zh']}",
                f"原录音截取：{row['source_start']:.3f}–{row['source_end']:.3f}秒。",
                row['narration_zh'],
                f"[原声切片](exact/{Path(row['exact_wav']).name}) · [3秒倒计时录制版](guide/{Path(row['guide_wav']).name})",
            ])
        handbook.write_text('\n\n'.join(sections) + '\n', encoding='utf-8')
        incomplete = [row["id"] for row in rows if any(not row[key].strip() for key in (*METADATA_FIELDS, "narration_zh"))]
        print(json.dumps({
            "segments": len(rows), "manifest": str(manifest), "handbook": str(handbook), "guide_voice_start_seconds": COUNTDOWN_SECONDS,
            "incomplete_recording_metadata_ids": incomplete,
            "recording_list_complete": not incomplete,
        }, ensure_ascii=False, indent=2))
    except (OSError, ValueError, KeyError, TypeError) as exc:
        raise SystemExit(f"Recording plan error: {exc}") from None
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
