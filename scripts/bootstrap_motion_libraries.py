#!/usr/bin/env python3
"""Check/install external motion libraries and the Spec Mono layout source cache."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
from datetime import datetime
from pathlib import Path


LIBRARIES = {
    "video-shotcraft": "https://github.com/Vincentwei1021/video-shotcraft.git",
    "rve-remotion-templates": "https://github.com/reactvideoeditor/remotion-templates.git",
    "remotion-scenes": "https://github.com/lifeprompt-team/remotion-scenes.git",
    "video-spec-builder": "https://github.com/feicaiclub/video-spec-builder.git",
}
DEFAULT_ROOT = Path.home() / ".codex" / "cache" / "jian-ji-zhu-shou-2.0" / "motion-libraries"
TEMPLATE_FILES = (
    "Full Code/sections/aroll.jsx", "Full Code/sections/broll-charts.jsx",
    "Full Code/sections/broll-thinking.jsx", "spec-mono/spec-mono-components.md",
    "spec-mono/tokens.css", "spec-mono/design.md", "LICENSE",
)

LAYOUT_ALIASES = {
    "LineChart": "line", "BarChart": "bar", "HBarChart": "h-bar",
    "StackedBar": "stacked", "AreaChart": "area", "FlashCard": "inversion-flash",
    "ComplexFlow": "complex", "LoopFlow": "loop", "TreeChart": "tree",
    "VennDiagram": "venn", "KanbanBoard": "kanban", "AbstractSpectrum": "spectrum",
    "Matrix2x2": "matrix-2x2",
}


def approved_template_paths() -> dict[str, str]:
    catalog = Path(__file__).resolve().parents[1] / "references" / "v2-templates.md"
    return dict(re.findall(
        r"^\| ([a-z0-9-]+) \|[^\n]+\| ([\w-]+\.jsx) \|$",
        catalog.read_text(encoding="utf-8"), flags=re.MULTILINE,
    ))


def library_kind(name: str) -> str:
    return "layout-template" if name == "video-spec-builder" else "motion"


def run(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, text=True, capture_output=True, encoding="utf-8", errors="replace")


def valid_repo(path: Path, name: str = "") -> bool:
    if not (path / ".git").is_dir():
        return False
    if name == "video-spec-builder":
        return all((path / item).is_file() for item in TEMPLATE_FILES)
    useful = list(path.rglob("*.tsx")) + list(path.rglob("*.jsx")) + list(path.rglob("*.md"))
    return len(useful) >= 3


def template_sources(base: Path) -> list[dict]:
    """Locate JSX functions without executing upstream showcase code."""
    sources = []
    approved = approved_template_paths()
    for path in sorted((base / "Full Code" / "sections").glob("*.jsx")):
        body = path.read_text(encoding="utf-8")
        matches = list(re.finditer(r"^function\s+(\w+)\s*\(", body, flags=re.MULTILINE))
        for index, match in enumerate(matches):
            symbol = match.group(1)
            if symbol.endswith("Section"):
                continue
            slug = re.sub(r"([a-z0-9])([A-Z])", r"\1-\2", symbol).lower()
            layout_id = LAYOUT_ALIASES.get(symbol, slug)
            start = body.count("\n", 0, match.start()) + 1
            stop = body.count("\n", 0, matches[index + 1].start()) if index + 1 < len(matches) else len(body.splitlines())
            sources.append({
                "id": layout_id, "symbol": symbol, "relative_path": path.relative_to(base).as_posix(),
                "line": start, "end_line": stop, "source_kind": "jsx-reference",
                "requires_adaptation": True, "direct_import_ready": False,
                "enabled": approved.get(layout_id) == path.name,
            })
    for rel in ("spec-mono/spec-mono-components.md", "spec-mono/tokens.css", "spec-mono/design.md", "references/components-catalog.md"):
        path = base / rel
        if path.is_file():
            sources.append({"id": path.stem, "relative_path": rel, "line": 1, "source_kind": "upstream-reference", "requires_adaptation": True, "enabled": False})
    return sources


def main() -> int:
    parser = argparse.ArgumentParser(description="Install/check external motion libraries and Spec Mono layout sources.")
    parser.add_argument("--cache-root", type=Path, default=DEFAULT_ROOT)
    parser.add_argument("--library", choices=("all",) + tuple(LIBRARIES), default="all")
    parser.add_argument("--install-missing", action="store_true")
    parser.add_argument("--update", action="store_true")
    parser.add_argument("--git", help="Explicit git executable")
    args = parser.parse_args()

    git = args.git or shutil.which("git")
    if not git:
        raise SystemExit("git is required; install Git or pass --git with an absolute path")
    root = args.cache_root.expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)
    records = []
    for name, url in LIBRARIES.items():
        if args.library != "all" and name != args.library:
            continue
        target = root / name
        action = "checked"
        error = ""
        if not target.exists() and args.install_missing:
            result = run([git, "clone", "--depth", "1", url, str(target)])
            action = "cloned"
            if result.returncode:
                error = result.stderr.strip() or result.stdout.strip()
        elif target.exists() and args.update:
            result = run([git, "-C", str(target), "pull", "--ff-only"])
            action = "updated"
            if result.returncode:
                error = result.stderr.strip() or result.stdout.strip()
        ok = valid_repo(target, name) and not error
        head = ""
        if ok:
            result = run([git, "-C", str(target), "rev-parse", "HEAD"])
            if result.returncode == 0:
                head = result.stdout.strip()
        record = {"name": name, "kind": library_kind(name), "motion_share_eligible": library_kind(name) == "motion", "url": url, "path": str(target), "ok": ok, "action": action, "head": head, "error": error}
        if name == "video-spec-builder" and ok:
            index_path = root / "video-spec-builder-index.json"
            index = {
                "library": name, "kind": "layout-template", "url": url, "head": head,
                "path": str(target), "license": "MIT", "license_path": str(target / "LICENSE"),
                "motion_share_eligible": False, "direct_import_ready": False,
                "usage": "Adapt selected JSX layout functions to project components and frame-based timing. Apply the local visual rules; upstream theme, subtitles and showcase metadata are not defaults.",
                "sources": template_sources(target),
            }
            index_path.write_text(json.dumps(index, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            record.update({"license": "MIT", "license_path": str(target / "LICENSE"), "source_index": str(index_path), "source_count": len(index["sources"]), "direct_import_ready": False})
        records.append(record)

    manifest = {
        "checked_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "cache_root": str(root),
        "libraries": records,
    }
    manifest_path = root / "motion-libraries.json"
    if args.library != "all" and manifest_path.is_file():
        previous = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["libraries"] = [item for item in previous.get("libraries", []) if item["name"] != args.library] + records
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    return 0 if all(item["ok"] for item in records) else 1


if __name__ == "__main__":
    raise SystemExit(main())
