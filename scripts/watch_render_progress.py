#!/usr/bin/env python3
"""Monitor one render segment, emit five-minute heartbeats, and diagnose stalls."""

from __future__ import annotations

import argparse
import ctypes
import json
import os
import re
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")


FRAME_PATTERNS = [
    re.compile(r"(?:rendered|frame|frames)\D{0,16}(\d+)", re.IGNORECASE),
    re.compile(r"(\d+)\s*/\s*(\d+)\s*(?:frames?)?", re.IGNORECASE),
]


def now_local() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def load_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return {}


def file_state(path: Path) -> dict[str, Any]:
    try:
        stat = path.stat()
        return {"exists": True, "bytes": stat.st_size, "mtime": stat.st_mtime}
    except OSError:
        return {"exists": False, "bytes": 0, "mtime": None}


def tail_text(path: Path, max_bytes: int = 32768) -> str:
    try:
        with path.open("rb") as handle:
            handle.seek(0, os.SEEK_END)
            size = handle.tell()
            handle.seek(max(0, size - max_bytes))
            return handle.read().decode("utf-8", errors="replace")
    except OSError:
        return ""


def latest_frame(log_text: str) -> int | None:
    matches: list[int] = []
    for pattern in FRAME_PATTERNS:
        for match in pattern.finditer(log_text):
            try:
                matches.append(int(match.group(1)))
            except (IndexError, ValueError):
                continue
    return max(matches) if matches else None


class CpuSampler:
    def __init__(self) -> None:
        self.previous: tuple[int, int, int] | None = None

    @staticmethod
    def _windows_times() -> tuple[int, int, int] | None:
        if os.name != "nt":
            return None

        class FileTime(ctypes.Structure):
            _fields_ = [("low", ctypes.c_ulong), ("high", ctypes.c_ulong)]

        def integer(value: FileTime) -> int:
            return (int(value.high) << 32) | int(value.low)

        idle, kernel, user = FileTime(), FileTime(), FileTime()
        ok = ctypes.windll.kernel32.GetSystemTimes(
            ctypes.byref(idle), ctypes.byref(kernel), ctypes.byref(user)
        )
        return (integer(idle), integer(kernel), integer(user)) if ok else None

    def sample(self) -> float | None:
        current = self._windows_times()
        if current is None:
            try:
                load_1m = os.getloadavg()[0]
                return round(min(100.0, load_1m / max(1, os.cpu_count() or 1) * 100), 1)
            except (AttributeError, OSError):
                return None
        previous, self.previous = self.previous, current
        if previous is None:
            return None
        idle_delta = current[0] - previous[0]
        total_delta = (current[1] - previous[1]) + (current[2] - previous[2])
        if total_delta <= 0:
            return None
        return round(max(0.0, min(100.0, (1 - idle_delta / total_delta) * 100)), 1)


def memory_sample() -> dict[str, float | None]:
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
            return {
                "ram_percent": float(status.dwMemoryLoad),
                "ram_used_gib": round((status.ullTotalPhys - status.ullAvailPhys) / 2**30, 2),
                "ram_total_gib": round(status.ullTotalPhys / 2**30, 2),
            }
    return {"ram_percent": None, "ram_used_gib": None, "ram_total_gib": None}


def gpu_sample() -> dict[str, Any]:
    executable = shutil.which("nvidia-smi")
    if not executable:
        return {"gpu_available": False}
    query = (
        "utilization.gpu,utilization.memory,utilization.encoder,"
        "memory.used,memory.total,temperature.gpu"
    )
    try:
        completed = subprocess.run(
            [executable, f"--query-gpu={query}", "--format=csv,noheader,nounits"],
            check=True,
            capture_output=True,
            text=True,
            timeout=8,
        )
        values = [value.strip() for value in completed.stdout.strip().splitlines()[0].split(",")]
        return {
            "gpu_available": True,
            "gpu_percent": float(values[0]),
            "gpu_memory_controller_percent": float(values[1]),
            "encoder_percent": float(values[2]),
            "vram_used_mib": float(values[3]),
            "vram_total_mib": float(values[4]),
            "vram_percent": round(float(values[3]) / max(1.0, float(values[4])) * 100, 1),
            "temperature_c": float(values[5]),
        }
    except (OSError, subprocess.SubprocessError, ValueError, IndexError):
        return {"gpu_available": False}


def process_alive(pid: int | None) -> bool | None:
    if pid is None:
        return None
    if os.name == "nt":
        process_query_limited_information = 0x1000
        still_active = 259
        handle = ctypes.windll.kernel32.OpenProcess(
            process_query_limited_information, False, pid
        )
        if not handle:
            return False
        try:
            exit_code = ctypes.c_ulong()
            if not ctypes.windll.kernel32.GetExitCodeProcess(handle, ctypes.byref(exit_code)):
                return False
            return int(exit_code.value) == still_active
        finally:
            ctypes.windll.kernel32.CloseHandle(handle)
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def tuning_recommendation(
    current: int,
    minimum: int,
    maximum: int,
    step: int,
    sample: dict[str, Any],
    low_utilization_confirmed: bool,
) -> dict[str, Any]:
    cpu = sample.get("cpu_percent")
    ram = sample.get("ram_percent")
    gpu = sample.get("gpu_percent")
    vram = sample.get("vram_percent")
    next_value = current
    reason = "hold: remain inside the measured working range"
    if (ram is not None and ram >= 85) or (vram is not None and vram >= 92):
        next_value = max(minimum, current - max(step, 2))
        reason = "decrease: hard RAM/VRAM safety cap reached"
    elif (ram is not None and ram >= 78) or (vram is not None and vram >= 85):
        next_value = max(minimum, current - step)
        reason = "decrease: soft RAM/VRAM cap reached"
    elif low_utilization_confirmed and cpu is not None and cpu < 75 and (ram is None or ram < 70):
        if gpu is None or gpu < 65:
            next_value = min(maximum, current + step)
            reason = "increase next segment: CPU/GPU below target with memory headroom"
    return {
        "current_concurrency": current,
        "recommended_next_segment_concurrency": next_value,
        "reason": reason,
        "applies_between_segments_only": True,
        "low_utilization_window_confirmed": low_utilization_confirmed,
    }


def write_jsonl(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False) + "\n")


def emit(payload: dict[str, Any], telemetry_path: Path) -> None:
    write_jsonl(telemetry_path, payload)
    print(json.dumps(payload, ensure_ascii=False), flush=True)


def main() -> int:
    parser = argparse.ArgumentParser(description="Monitor one segmented Remotion render.")
    parser.add_argument("project_root", type=Path)
    parser.add_argument("--segment-id", required=True)
    parser.add_argument("--log", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--pid", type=int)
    parser.add_argument("--sample-interval", type=int, default=15)
    parser.add_argument("--heartbeat-seconds", type=int, default=300)
    parser.add_argument("--low-utilization-seconds", type=int, default=90)
    parser.add_argument("--stall-seconds", type=int, default=180)
    parser.add_argument("--hard-stall-seconds", type=int, default=300)
    parser.add_argument("--once", action="store_true")
    args = parser.parse_args()

    if args.sample_interval <= 0 or args.heartbeat_seconds <= 0:
        parser.error("sample and heartbeat intervals must be positive")
    if args.low_utilization_seconds < 0:
        parser.error("low-utilization threshold must be non-negative")
    if args.stall_seconds < 0 or args.hard_stall_seconds < args.stall_seconds:
        parser.error("stall thresholds must be non-negative and ordered")

    root = args.project_root.expanduser().resolve()
    log_path = args.log if args.log.is_absolute() else root / args.log
    output_path = args.output if args.output.is_absolute() else root / args.output
    plan = load_json(root / "09_qa" / "render-plan.json")
    # Older project plans may be a bare segment list without resource_tuning.
    tuning = plan.get("resource_tuning", {}) if isinstance(plan, dict) else {}
    current_concurrency = int(tuning.get("initial_concurrency", max(1, round((os.cpu_count() or 1) * 0.75))))
    minimum = int(tuning.get("minimum_concurrency", 1))
    maximum = int(tuning.get("maximum_concurrency", max(1, os.cpu_count() or 1)))
    step = int(tuning.get("adjustment_step_threads", 1))

    telemetry_path = root / "09_qa" / "render-monitor" / f"{args.segment_id}.jsonl"
    diagnostic_dir = root / "09_qa" / "stall-diagnostics"
    cpu_sampler = CpuSampler()
    previous_marker: tuple[Any, ...] | None = None
    last_progress = time.monotonic()
    last_heartbeat = 0.0
    diagnostic_written = False
    hard_stall_written = False
    low_utilization_since: float | None = None

    while True:
        loop_started = time.monotonic()
        log_state = file_state(log_path)
        output_state = file_state(output_path)
        log_tail = tail_text(log_path)
        frame = latest_frame(log_tail)
        marker = (log_state["bytes"], log_state["mtime"], output_state["bytes"], output_state["mtime"], frame)
        if previous_marker is None:
            previous_marker = marker
        elif marker != previous_marker:
            previous_marker = marker
            last_progress = loop_started
            diagnostic_written = False
            hard_stall_written = False

        resources: dict[str, Any] = {"cpu_percent": cpu_sampler.sample()}
        resources.update(memory_sample())
        resources.update(gpu_sample())
        cpu = resources.get("cpu_percent")
        ram = resources.get("ram_percent")
        gpu = resources.get("gpu_percent")
        low_now = (
            cpu is not None
            and cpu < 75
            and (ram is None or ram < 70)
            and (gpu is None or gpu < 65)
        )
        if low_now:
            if low_utilization_since is None:
                low_utilization_since = loop_started
        else:
            low_utilization_since = None
        low_utilization_seconds = (
            loop_started - low_utilization_since if low_utilization_since is not None else 0.0
        )
        stalled_for = max(0.0, loop_started - last_progress)
        alive = process_alive(args.pid)
        state = "RUNNING"
        if stalled_for >= args.hard_stall_seconds:
            state = "HARD_STALL"
        elif stalled_for >= args.stall_seconds:
            state = "DIAGNOSING_STALL"

        recommendation = tuning_recommendation(
            current_concurrency,
            minimum,
            maximum,
            step,
            resources,
            low_utilization_seconds >= args.low_utilization_seconds,
        )
        heartbeat = {
            "event": "render_heartbeat",
            "timestamp": now_local(),
            "segment_id": args.segment_id,
            "state": state,
            "process_alive": alive,
            "seconds_without_progress": round(stalled_for, 1),
            "seconds_below_utilization_target": round(low_utilization_seconds, 1),
            "latest_frame": frame,
            "log_bytes": log_state["bytes"],
            "output_bytes": output_state["bytes"],
            "resources": resources,
            "tuning": recommendation,
        }

        if stalled_for >= args.stall_seconds and not diagnostic_written:
            diagnostic_written = True
            disk = shutil.disk_usage(root)
            diagnostic = dict(heartbeat)
            diagnostic.update({
                "event": "automatic_stall_diagnostic",
                "log_tail": log_tail[-8000:],
                "disk_free_gib": round(disk.free / 2**30, 2),
                "checks": [
                    "render process liveness",
                    "frame/log/output growth",
                    "CPU/GPU/RAM/VRAM pressure",
                    "available disk space",
                    "last render log lines",
                ],
            })
            diagnostic_dir.mkdir(parents=True, exist_ok=True)
            diagnostic_path = diagnostic_dir / f"{args.segment_id}-{datetime.now():%Y%m%d-%H%M%S}.json"
            diagnostic["diagnostic_path"] = str(diagnostic_path)
            diagnostic_path.write_text(
                json.dumps(diagnostic, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
            )
            emit(diagnostic, telemetry_path)

        if stalled_for >= args.hard_stall_seconds and not hard_stall_written:
            hard_stall_written = True
            hard_stall = dict(heartbeat)
            hard_stall.update({
                "event": "hard_stall_requires_intervention",
                "action": (
                    "Report immediately. Inspect the diagnostic, then retry only this segment with "
                    "the recommended lower concurrency or CPU fallback; never rerun accepted segments."
                ),
            })
            emit(hard_stall, telemetry_path)

        if loop_started - last_heartbeat >= args.heartbeat_seconds or args.once:
            emit(heartbeat, telemetry_path)
            last_heartbeat = loop_started

        if args.once:
            return 0
        if alive is False:
            final = dict(heartbeat)
            final["event"] = "render_process_ended"
            emit(final, telemetry_path)
            return 0
        elapsed = time.monotonic() - loop_started
        time.sleep(max(0.25, args.sample_interval - elapsed))


if __name__ == "__main__":
    raise SystemExit(main())
