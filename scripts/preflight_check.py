#!/usr/bin/env python3
"""Project preflight for the compact historical-video editing skill."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from pathlib import Path

from bootstrap_motion_libraries import DEFAULT_ROOT, LIBRARIES, library_kind, valid_repo

STAGE_RUNTIMES = {
    "text": ("python",), "layout": ("python",), "motion": ("python", "node", "npx"),
    "audio": ("python", "ffmpeg", "ffprobe"), "render": ("python", "node", "npx", "ffmpeg", "ffprobe"),
}


def command_status(name: str, project_root: Path) -> dict:
    path = shutil.which(name)
    if not path and name == "python":
        path = sys.executable
    if not path and name in {"ffmpeg", "ffprobe"} and project_root.is_dir():
        pattern = f"**/@remotion/compositor-*/{name}.exe"
        bundled = next(project_root.glob(pattern), None)
        path = str(bundled) if bundled else None
    return {"name": name, "ok": bool(path), "path": path or ""}


def repo_status(name: str, cache_root: Path) -> dict:
    path = cache_root / name
    result = {"name": name, "kind": library_kind(name), "motion_share_eligible": library_kind(name) == "motion", "ok": valid_repo(path, name), "path": str(path)}
    if name == "video-spec-builder":
        index = cache_root / "video-spec-builder-index.json"
        result.update({"source_index": str(index), "index_ready": index.is_file(), "direct_import_ready": False})
        result["ok"] = result["ok"] and result["index_ready"]
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Check project inputs, runtimes, and external motion libraries.")
    parser.add_argument("--project-root", type=Path, required=True)
    parser.add_argument("--stage", choices=tuple(STAGE_RUNTIMES), default="text", help="Only missing dependencies needed for this stage are blocking.")
    parser.add_argument("--cache-root", type=Path, default=DEFAULT_ROOT)
    parser.add_argument("--json-output", type=Path)
    args = parser.parse_args()
    root = args.project_root.expanduser().resolve()
    counts = dict.fromkeys((".docx", ".srt", ".xlsx", ".png", ".jpg", ".jpeg", ".mp4", ".mov"), 0)
    for folder, directories, names in os.walk(root):
        directories[:] = [name for name in directories if name not in {"node_modules", ".git", ".venv", "__pycache__"}]
        for name in names:
            ext = Path(name).suffix.lower()
            if ext in counts:
                counts[ext] += 1
    commands = [command_status(name, root) for name in ("node", "npx", "python", "ffmpeg", "ffprobe")]
    libraries = [repo_status(name, args.cache_root.expanduser().resolve()) for name in LIBRARIES]
    errors = []
    warnings = []
    if not root.is_dir():
        errors.append(f"project root not found: {root}")
    if counts.get(".docx", 0) + counts.get(".srt", 0) == 0:
        warnings.append("no DOCX or SRT found under project root")
    for item in commands:
        item["required"] = item["name"] in STAGE_RUNTIMES[args.stage]
        if not item["ok"]:
            (errors if item["required"] else warnings).append(f"missing runtime: {item['name']}")
    required_library = {"layout": "video-spec-builder", "motion": "video-shotcraft"}.get(args.stage)
    for item in libraries:
        item["required"] = item["name"] == required_library
        if not item["ok"]:
            (errors if item["required"] else warnings).append(f"library/cache index missing: {item['name']}; run bootstrap_motion_libraries.py --library {item['name']} --install-missing")
    report = {"ok": not errors, "stage": args.stage, "project_root": str(root), "input_counts": counts, "commands": commands, "motion_libraries": [item for item in libraries if item["kind"] == "motion"], "layout_libraries": [item for item in libraries if item["kind"] == "layout-template"], "errors": errors, "warnings": warnings}
    rendered = json.dumps(report, ensure_ascii=False, indent=2)
    print(rendered)
    if args.json_output:
        target = args.json_output.expanduser().resolve()
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(rendered + "\n", encoding="utf-8")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
