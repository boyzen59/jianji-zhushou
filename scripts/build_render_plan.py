#!/usr/bin/env python3
"""Build an adaptive, GPU-preferred render plan with <=5-minute scene-boundary chunks."""

from __future__ import annotations

import argparse
import ctypes
import json
import math
import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")


MAX_SEGMENT_SECONDS = 300
PROGRESS_REPORT_INTERVAL_SECONDS = 300
RESOURCE_SAMPLE_INTERVAL_SECONDS = 15
LOW_UTILIZATION_WINDOW_SECONDS = 90
STALL_DIAGNOSTIC_SECONDS = 180
HARD_STALL_SECONDS = 300


def now_local() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def load_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except FileNotFoundError as exc:
        raise SystemExit(f"Missing required file: {path}") from exc
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Invalid JSON {path}: {exc}") from exc


def parse_tc(value: Any) -> float:
    if isinstance(value, (int, float)):
        return float(value)
    parts = str(value).replace(",", ".").split(":")
    try:
        if len(parts) == 3:
            return int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2])
        if len(parts) == 2:
            return int(parts[0]) * 60 + float(parts[1])
        return float(parts[0])
    except (ValueError, IndexError) as exc:
        raise SystemExit(f"Invalid timecode: {value!r}") from exc


def format_tc(seconds: float) -> str:
    seconds = max(0.0, seconds)
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    remainder = seconds % 60
    return f"{hours:02d}:{minutes:02d}:{remainder:06.3f}"


def total_memory_bytes() -> int | None:
    """Return physical memory without requiring psutil."""
    if os.name == "nt":
        class MemoryStatusEx(ctypes.Structure):
            _fields_ = [
                ("dwLength", ctypes.c_ulong),
                ("dwMemoryLoad", ctypes.c_ulong),
                ("ullTotalPhys", ctypes.c_ulonglong),
                ("ullAvailPhys", ctypes.c_ulonglong),
                ("ullTotalPageFile", ctypes.c_ulonglong),
                ("ullAvailPageFile", ctypes.c_ulonglong),
                ("ullTotalVirtual", ctypes.c_ulonglong),
                ("ullAvailVirtual", ctypes.c_ulonglong),
                ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
            ]

        status = MemoryStatusEx()
        status.dwLength = ctypes.sizeof(status)
        if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status)):
            return int(status.ullTotalPhys)
        return None
    try:
        pages = os.sysconf("SC_PHYS_PAGES")
        page_size = os.sysconf("SC_PAGE_SIZE")
        return int(pages * page_size)
    except (AttributeError, OSError, ValueError):
        return None


def detect_nvidia_gpu() -> dict[str, Any]:
    executable = shutil.which("nvidia-smi")
    if not executable:
        return {"available": False, "reason": "nvidia-smi not found"}
    query = (
        "name,driver_version,memory.total,utilization.gpu,utilization.memory,"
        "utilization.encoder"
    )
    try:
        completed = subprocess.run(
            [executable, f"--query-gpu={query}", "--format=csv,noheader,nounits"],
            check=True,
            capture_output=True,
            text=True,
            timeout=8,
        )
        first = completed.stdout.strip().splitlines()[0]
        values = [value.strip() for value in first.split(",")]
        return {
            "available": True,
            "name": values[0],
            "driver_version": values[1],
            "vram_total_mib": int(float(values[2])),
            "gpu_utilization_percent_at_plan_time": float(values[3]),
            "memory_utilization_percent_at_plan_time": float(values[4]),
            "encoder_utilization_percent_at_plan_time": float(values[5]),
        }
    except (OSError, subprocess.SubprocessError, ValueError, IndexError) as exc:
        return {"available": False, "reason": f"nvidia-smi query failed: {exc}"}


def build_resource_tuning() -> tuple[dict[str, Any], dict[str, Any]]:
    logical_cpus = max(1, os.cpu_count() or 1)
    memory_bytes = total_memory_bytes()
    memory_gib = round(memory_bytes / 2**30, 2) if memory_bytes else None
    candidates = sorted({
        max(1, round(logical_cpus * 0.50)),
        max(1, round(logical_cpus * 0.75)),
        max(1, round(logical_cpus * 0.90)),
    })
    initial = min(candidates, key=lambda value: abs(value - logical_cpus * 0.75))
    maximum = max(candidates)
    if logical_cpus >= 12 and (memory_gib or 0) >= 24:
        offthread_threads = 4
    elif logical_cpus >= 8 and (memory_gib or 0) >= 16:
        offthread_threads = 3
    else:
        offthread_threads = 2

    # Remotion's two media caches can each default to half of available memory.
    # Bound each cache so a long render cannot consume most RAM before Chromium,
    # FFmpeg and source media are accounted for.
    if memory_bytes:
        cache_bytes = int(min(6 * 2**30, max(1 * 2**30, memory_bytes * 0.125)))
    else:
        cache_bytes = 2 * 2**30
    gpu = detect_nvidia_gpu()
    hardware = {
        "logical_cpu_threads": logical_cpus,
        "physical_memory_gib": memory_gib,
        "nvidia_gpu": gpu,
    }
    tuning = {
        "adaptive_concurrency": True,
        "apply_adjustments_between_segments_only": True,
        "parallel_encoding": True,
        "initial_concurrency": initial,
        "concurrency_candidates": candidates,
        "minimum_concurrency": min(candidates),
        "maximum_concurrency": maximum,
        "adjustment_step_threads": max(1, round(logical_cpus * 0.125)),
        "offthreadvideo_video_threads": offthread_threads,
        "media_cache_size_in_bytes": cache_bytes,
        "offthreadvideo_cache_size_in_bytes": cache_bytes,
        "targets_percent": {
            "cpu_working_range": [75, 95],
            "gpu_working_range_when_eligible": [65, 95],
            "ram_working_range": [55, 78],
            "vram_working_range": [55, 85],
        },
        "safety_caps_percent": {"ram_soft": 78, "ram_hard": 85, "vram_hard": 92},
        "increase_rule": (
            "After a >=90s representative window, increase by one step for the next segment "
            "when CPU is below 75% and RAM is below 70%; GPU-eligible scenes should also be below 65%."
        ),
        "decrease_rule": (
            "Reduce concurrency for the next segment when RAM reaches 78%, VRAM reaches 85%, "
            "CPU is pinned above 95% without throughput gain, or decode/render errors appear."
        ),
        "hard_cap_rule": "At RAM >=85% or VRAM >=92%, stop raising load and reduce the current-segment retry.",
    }
    return hardware, tuning


def normalize_scenes(spec: dict[str, Any], fps: int) -> list[dict[str, Any]]:
    raw = spec.get("scenes", [])
    if not isinstance(raw, list) or not raw:
        raise SystemExit("video-spec scenes must be a non-empty list")
    scenes: list[dict[str, Any]] = []
    previous_end_frame = 0
    for index, scene in enumerate(raw, 1):
        start = parse_tc(scene.get("start"))
        end = parse_tc(scene.get("end"))
        if not math.isfinite(start) or not math.isfinite(end) or start < 0:
            raise SystemExit(f"Scene {scene.get('id', index)} requires finite, nonnegative times")
        if end <= start:
            raise SystemExit(f"Scene {scene.get('id', index)} must end after it starts")
        if end - start > MAX_SEGMENT_SECONDS + 0.001:
            raise SystemExit(
                f"Scene {scene.get('id', index)} is longer than {MAX_SEGMENT_SECONDS}s; split the scene first"
            )
        start_frame = round(start * fps)
        end_frame_exclusive = round(end * fps)
        if start_frame != previous_end_frame:
            raise SystemExit(
                f"Scene {scene.get('id', index)} starts at frame {start_frame}; "
                f"expected {previous_end_frame} (timeline must start at zero and remain gap-free)"
            )
        if end_frame_exclusive <= start_frame:
            raise SystemExit(f"Scene {scene.get('id', index)} must contain at least one frame")
        scenes.append({
            "id": str(scene.get("scene_id", scene.get("id", f"S{index:03d}"))),
            "chapter": str(scene.get("chapter", "")),
            "start_seconds": start,
            "end_seconds": end,
            "start_frame": start_frame,
            "end_frame_exclusive": end_frame_exclusive,
        })
        previous_end_frame = end_frame_exclusive
    return scenes


def build_segments(scenes: list[dict[str, Any]], fps: int) -> list[dict[str, Any]]:
    groups: list[list[dict[str, Any]]] = []
    current: list[dict[str, Any]] = []
    segment_start = scenes[0]["start_seconds"]
    for scene in scenes:
        if current and scene["end_seconds"] - segment_start > MAX_SEGMENT_SECONDS + 0.001:
            groups.append(current)
            current = []
            segment_start = scene["start_seconds"]
        current.append(scene)
    if current:
        groups.append(current)

    segments: list[dict[str, Any]] = []
    for index, group in enumerate(groups, 1):
        start_seconds = group[0]["start_seconds"]
        end_seconds = group[-1]["end_seconds"]
        start_frame = group[0]["start_frame"]
        end_frame_exclusive = group[-1]["end_frame_exclusive"]
        end_frame_inclusive = end_frame_exclusive - 1
        chapters = list(dict.fromkeys(item["chapter"] for item in group if item["chapter"]))
        segment_id = f"SEG-{index:03d}"
        segments.append({
            "id": segment_id,
            "start": format_tc(start_seconds),
            "end": format_tc(end_seconds),
            "duration_seconds": round(end_seconds - start_seconds, 3),
            "global_start_frame": start_frame,
            "global_end_frame_inclusive": end_frame_inclusive,
            "frame_count": end_frame_exclusive - start_frame,
            "remotion_frames_arg": f"{start_frame}-{end_frame_inclusive}",
            "scene_ids": [item["id"] for item in group],
            "chapters": chapters,
            "output": f"09_qa/render-segments/{segment_id}.mp4",
            "status": "PENDING",
            "render_path": "GPU_IF_POSSIBLE_THEN_CPU_FALLBACK",
            "elapsed_seconds": None,
            "sha256": None,
            "log": f"09_qa/render-segments/{segment_id}.log",
        })
    return segments


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a <=300s segmented Remotion render plan.")
    parser.add_argument("project_root", type=Path)
    parser.add_argument("--composition", default="Master")
    parser.add_argument("--overwrite", action="store_true", help="Explicitly rebuild an existing plan after backing it up; ordinary resume must reuse it.")
    args = parser.parse_args()

    root = args.project_root.expanduser().resolve()
    output = root / "09_qa" / "render-plan.json"
    if output.exists() and not args.overwrite:
        raise SystemExit(f"Render plan already exists: {output}. Reuse its checkpoint; use --overwrite only for an intentional rebuild with backup.")
    project = load_json(root / "project.json")
    spec = load_json(root / "04_spec" / "video-spec.json")
    fps = int(spec.get("fps") or project.get("spec", {}).get("fps") or 60)
    if fps != 60:
        raise SystemExit(f"Fixed workflow requires 60fps; got {fps}")

    scenes = normalize_scenes(spec, fps)
    segments = build_segments(scenes, fps)
    detected_hardware, resource_tuning = build_resource_tuning()
    concurrency = resource_tuning["initial_concurrency"]
    offthread_threads = resource_tuning["offthreadvideo_video_threads"]
    media_cache = resource_tuning["media_cache_size_in_bytes"]
    offthread_cache = resource_tuning["offthreadvideo_cache_size_in_bytes"]
    plan = {
        "schema_version": 2,
        "project": project.get("project", spec.get("project", "")),
        "source_spec": str((root / "04_spec" / "video-spec.json").resolve()),
        "source_version": spec.get("version", ""),
        "generated_at": now_local(),
        "composition": args.composition,
        "fps": fps,
        "max_segment_seconds": MAX_SEGMENT_SECONDS,
        "progress_report_interval_seconds": PROGRESS_REPORT_INTERVAL_SECONDS,
        "prefer_gpu": True,
        "detected_hardware": detected_hardware,
        "resource_tuning": resource_tuning,
        "progress_monitor": {
            "script": "scripts/watch_render_progress.py",
            "resource_sample_interval_seconds": RESOURCE_SAMPLE_INTERVAL_SECONDS,
            "heartbeat_interval_seconds": PROGRESS_REPORT_INTERVAL_SECONDS,
            "low_utilization_window_seconds": LOW_UTILIZATION_WINDOW_SECONDS,
            "stall_diagnostic_seconds": STALL_DIAGNOSTIC_SECONDS,
            "hard_stall_seconds": HARD_STALL_SECONDS,
            "heartbeat_is_required_even_without_progress": False,
            "user_notification_policy": "meaningful_change_completion_failure_or_required_action",
            "automatic_diagnostic_on_stall": True,
            "diagnostic_directory": "09_qa/stall-diagnostics",
        },
        "gpu_preflight": {
            "status": "DETECTED" if detected_hardware["nvidia_gpu"].get("available") else "CPU_FALLBACK_READY",
            "remotion_version": "[待探测]",
            "gpu": detected_hardware["nvidia_gpu"].get("name", "not detected"),
            "driver": detected_hardware["nvidia_gpu"].get("driver_version", "not detected"),
            "vram_mib": detected_hardware["nvidia_gpu"].get("vram_total_mib"),
            "gl_backend": "auto_by_remotion_version",
            "hardware_acceleration": "if-possible",
            "ffmpeg_h264_nvenc": "[待探测]",
            "cpu_fallback": True,
            "benchmark_required": False,
            "validation_strategy": "Use the first actual production segment; benchmark only to diagnose measured failures or throughput issues.",
        },
        "render_template": (
            "npx remotion render <entry-point> {composition} <segment-output> "
            "--frames=<global-start>-<global-end-inclusive> --codec=h264 --muted "
            "--hardware-acceleration if-possible --color-space=bt709 --log=verbose "
            "--concurrency={concurrency} --offthreadvideo-video-threads={offthread_threads} "
            "--media-cache-size-in-bytes={media_cache} "
            "--offthreadvideo-cache-size-in-bytes={offthread_cache}"
        ).format(
            composition=args.composition,
            concurrency=concurrency,
            offthread_threads=offthread_threads,
            media_cache=media_cache,
            offthread_cache=offthread_cache,
        ),
        "monitor_template": (
            "python scripts/watch_render_progress.py <project-root> --segment-id <segment-id> "
            "--log <segment-log> --output <segment-output> --pid <render-pid>"
        ),
        "version_notes": [
            "Check the installed Remotion CLI for supported frame-range, GL and hardware-acceleration flags; do not upgrade merely to match an old template.",
            "Hardware H.264 uses bitrate control, not CRF. Keep CPU libx264 as the verified fallback.",
            "Keep parallel encoding enabled; do not add --disallow-parallel-encoding unless recovering from a measured memory failure.",
            "Apply concurrency changes between segments, never mutate a running segment blindly.",
            "Local progress logging is optional; do not notify the user repeatedly when state is unchanged or create a scheduled monitor without a request.",
            "Do not use --enforce-audio-track. The fixed master must contain no audio stream.",
        ],
        "progress_fields": [
            "completed_segments", "total_segments", "current_time_range", "gpu_or_cpu",
            "elapsed", "estimated_remaining", "cpu_percent", "gpu_percent", "ram_percent",
            "vram_percent", "latest_frame", "output_bytes", "stall_state", "error_or_retry",
        ],
        "concat_policy": {
            "preserve_global_frames": True,
            "single_final_normalization": True,
            "audio": "none",
            "verify_with": "scripts/verify_master_media.py",
        },
        "segments": segments,
    }

    output.parent.mkdir(parents=True, exist_ok=True)
    backup = None
    if output.exists():
        if not args.overwrite:
            raise SystemExit(f"Render plan appeared while planning; refusing to replace it: {output}")
        backup = output.with_name(f"render-plan.backup-{datetime.now().strftime('%Y%m%d-%H%M%S-%f')}.json")
        with output.open("rb") as source, backup.open("xb") as target:
            shutil.copyfileobj(source, target)
    with output.open("w" if args.overwrite else "x", encoding="utf-8") as handle:
        handle.write(json.dumps(plan, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({
        "output": str(output),
        "previous_plan_backup": str(backup) if backup else None,
        "segments": len(segments),
        "total_duration_seconds": round(scenes[-1]["end_seconds"] - scenes[0]["start_seconds"], 3),
        "max_segment_seconds": max(segment["duration_seconds"] for segment in segments),
        "initial_concurrency": concurrency,
        "concurrency_candidates": resource_tuning["concurrency_candidates"],
        "logical_cpu_threads": detected_hardware["logical_cpu_threads"],
        "physical_memory_gib": detected_hardware["physical_memory_gib"],
        "gpu": detected_hardware["nvidia_gpu"],
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
