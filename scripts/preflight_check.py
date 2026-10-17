#!/usr/bin/env python3
"""Project preflight for the compact historical-video editing skill."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from pathlib import Path

from bootstrap_motion_libraries import DEFAULT_ROOT, LIBRARIES, library_kind, reference_origin, valid_repo

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
    result = {"name": name, "kind": library_kind(name), "origin": reference_origin(name), "ok": valid_repo(path, name), "path": str(path)}
    result["reference_path"] = str(path / "reference-snapshot" if (path / "reference-snapshot" / "source.json").is_file() else path)
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
    parser.add_argument("--library", action="append", choices=("all",) + tuple(LIBRARIES), default=[],
                        help="Check only selected reference caches; repeat for multiple libraries.")
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
    selected = list(LIBRARIES) if "all" in args.library else list(dict.fromkeys(args.library))
    libraries = [repo_status(name, args.cache_root.expanduser().resolve()) for name in selected]
    errors = []
    warnings = []
    if not root.is_dir():
        errors.append(f"project root not found: {root}")
    if counts.get(".docx", 0) + counts.get(".srt", 0) == 0:
        warnings.append("no DOCX or SRT found under project root")
    for item in commands:
        item["required"] = item["name"] in STAGE_RUNTIMES[args.stage]
        if not item["ok"] and item["required"]:
            errors.append(f"missing runtime: {item['name']}")
    # A missing optional reference cache is not an approval gate or engine failure.
    for item in libraries:
        item["required"] = False
    missing_references = [item for item in libraries if not item["ok"]]
    for item in missing_references:
        warnings.append(f"selected reference cache missing/incomplete: {item['name']} at {item['path']}; use verified online or other local sources if available")
    reference_notice = {
        "required": bool(missing_references),
        "missing_cache": [{"name": item["name"], "path": item["path"], "origin": item["origin"]} for item in missing_references],
        "plugin_check": "not_checked_by_filesystem_script; inspect only actual required tools/connections",
        "scope": "configured cache only; not a whole-machine skill installation audit",
        "next_action": "Resolve only the selected references needed for this task; continue independent work. Do not infer that all creation is blocked." if missing_references else "No selected reference gaps; inspect project-specific tools only when needed.",
    }
    remotion = {"required": args.stage in {"motion", "render"}, "declared": False, "installed": False}
    package_path = root / "package.json"
    if package_path.is_file():
        try:
            package = json.loads(package_path.read_text(encoding="utf-8-sig"))
            deps = {**package.get("dependencies", {}), **package.get("devDependencies", {})}
            remotion["declared"] = "remotion" in deps
            remotion["version"] = deps.get("remotion", "")
        except (OSError, ValueError) as exc:
            errors.append(f"cannot read package.json: {exc}")
    node_path = next((item["path"] for item in commands if item["name"] == "node" and item["ok"]), None)
    if remotion["required"] and node_path and root.is_dir():
        import subprocess
        try:
            result = subprocess.run([node_path, "-e", "console.log(require.resolve('remotion'))"], cwd=root, capture_output=True, text=True, timeout=10)
            remotion["installed"] = result.returncode == 0
        except (OSError, subprocess.SubprocessError):
            pass
    if remotion["required"] and not remotion["installed"]:
        errors.append("Remotion is not installed in the selected production project; pass the actual Remotion project root")
    report = {"ok": not errors, "ok_scope": "technical runtime checks, not design approval", "stage": args.stage, "planning_status": "SELECTED_REFERENCES_MISSING" if missing_references else "SELECTED_REFERENCES_READY" if selected else "REFERENCES_NOT_REQUESTED", "reference_notice": reference_notice, "project_root": str(root), "input_counts": counts, "commands": commands, "remotion": remotion, "reference_libraries": libraries, "errors": errors, "warnings": warnings}
    rendered = json.dumps(report, ensure_ascii=False, indent=2)
    print(rendered)
    if args.json_output:
        target = args.json_output.expanduser().resolve()
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(rendered + "\n", encoding="utf-8")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
