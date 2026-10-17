#!/usr/bin/env python3
"""Check/install external motion libraries and the Spec Mono layout source cache."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import hashlib
from urllib.request import Request, urlopen
from urllib.parse import quote
from urllib.error import URLError
from prompt_motion_index import cache_index, valid_index
from datetime import datetime
from pathlib import Path


LEGACY_LIBRARIES = {
    "remotion-official": "https://github.com/remotion-dev/skills.git",
    "huashu-art-motion": "https://github.com/alchaincyf/huashu-art-motion.git",
    "motion-video-kit": "https://github.com/echris6/motion-video-kit.git",
    "motion-graphics-skills": "https://github.com/charlie947/motion-graphics-skills.git",
    "motion-graphics": "https://github.com/Barty-Bart/motion-graphics.git",
    "claude-remotion-skill": "https://github.com/haidrrrry/claude-remotion-skill.git",
    "motion-design-skills": "https://github.com/iart-ai/motion-design-skills.git",
    "lottiefiles-motion-design": "https://github.com/LottieFiles/motion-design-skill.git",
    "klik-anim": "https://github.com/t3knobox/klik-anim-skill-creation.git",
    "product-launch-motion": "https://github.com/AbubakrChan/product-launch-motion.git",
    "claude-motion": "https://github.com/whaleyxbt/claude-motion.git",
    "animate": "https://github.com/cth9191/animate.git",
    "claude-motion-design": "https://github.com/howseen-ai/claude-motion-design.git",
    "hyperframes-motion-reel": "https://github.com/Sunwood-ai-labs/hyperframes-motion-reel-skill.git",
    "hyperframes-student-kit": "https://github.com/nateherkai/hyperframes-student-kit.git",
    "video-shotcraft": "https://github.com/Vincentwei1021/video-shotcraft.git",
    "rve-remotion-templates": "https://github.com/reactvideoeditor/remotion-templates.git",
    "remotion-scenes": "https://github.com/lifeprompt-team/remotion-scenes.git",
    "video-spec-builder": "https://github.com/feicaiclub/video-spec-builder.git",
}
REGISTRY_PATH = Path(__file__).resolve().parents[1] / "references" / "motion-sources.json"
PRIMARY_SOURCES = {item["id"]: item for item in json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))["sources"]}
WEB_SOURCES = {item["id"]: item for item in json.loads(REGISTRY_PATH.read_text(encoding="utf-8")).get("web_sources", [])}
LIBRARIES = {**{name: item["url"] for name, item in PRIMARY_SOURCES.items()}, **LEGACY_LIBRARIES,
             **{name: item["url"] for name, item in WEB_SOURCES.items()}}
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
    if name in WEB_SOURCES:
        return "web-reference-index"
    return "layout-template" if name == "video-spec-builder" else "motion"


def reference_origin(name: str) -> str:
    if name in PRIMARY_SOURCES or name in WEB_SOURCES:
        return "user_supplied"
    return "legacy" if name in {"video-shotcraft", "rve-remotion-templates", "remotion-scenes", "video-spec-builder"} else "user_supplied"


def run(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, text=True, capture_output=True, encoding="utf-8", errors="replace", timeout=180)


def valid_repo(path: Path, name: str = "") -> bool:
    if name in WEB_SOURCES:
        return valid_index(path)
    snapshot = path / "reference-snapshot"
    marker = snapshot / "source.json"
    if name in PRIMARY_SOURCES and marker.is_file():
        try:
            record = json.loads(marker.read_text(encoding="utf-8"))
            files = record["files"]
            if (record.get("url") == PRIMARY_SOURCES[name]["url"] and
                all(item in files for item in PRIMARY_SOURCES[name]["required_files"]) and
                all((snapshot / item).is_file() and hashlib.sha256((snapshot / item).read_bytes()).hexdigest() == digest
                    for item, digest in files.items())):
                return True
        except (OSError, ValueError, KeyError, TypeError):
            pass
    if not (path / ".git").exists():
        return False
    if name in PRIMARY_SOURCES:
        return all((path / item).is_file() for item in PRIMARY_SOURCES[name]["required_files"])
    if name == "video-spec-builder":
        return all((path / item).is_file() for item in TEMPLATE_FILES)
    useful = list(path.rglob("*.tsx")) + list(path.rglob("*.jsx")) + list(path.rglob("*.md"))
    return len(useful) >= 3


def download_reference_snapshot(name: str, target: Path) -> dict:
    """Pinned text-only cache; no code execution, media download, or overwrite of Git files."""
    source = PRIMARY_SOURCES[name]
    snapshot = target / "reference-snapshot"
    marker = snapshot / "source.json"
    if marker.is_file():
        return {"action": "snapshot-retained", "error": "" if valid_repo(target, name) else
                "Snapshot differs from its recorded hashes; preserve edits and use a fresh --cache-root."}
    snapshot.mkdir(parents=True, exist_ok=True)
    base = source["url"].removeprefix("https://github.com/").removesuffix(".git")
    files, downloaded = {}, {}
    for relative in source["reference_files"]:
        destination = snapshot / relative
        # Preserve partially downloaded or locally edited files rather than overwrite them.
        if destination.exists():
            return {"action": "snapshot-partial", "error": f"Partial file already exists: {destination}; use a fresh --cache-root."}
        url = f"https://raw.githubusercontent.com/{base}/{source['audited_commit']}/{quote(relative, safe='/')}"
        try:
            with urlopen(Request(url, headers={"User-Agent": "jianji-reference-cache/3.1"}), timeout=25) as response:
                body = response.read(2_000_001)
            if len(body) > 2_000_000:
                raise ValueError(f"Reference exceeds 2 MB: {relative}")
            body.decode("utf-8")  # This cache intentionally excludes binary media.
        except (OSError, URLError, ValueError) as exc:
            return {"action": "snapshot-partial", "error": f"{relative}: {exc}"}
        downloaded[relative] = body
        files[relative] = hashlib.sha256(body).hexdigest()
    for relative, body in downloaded.items():
        destination = snapshot / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(body)
    record = {"url": source["url"], "head": source["audited_commit"], "license": source["license"], "files": files}
    marker.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {"action": "snapshot-downloaded", "error": ""}


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
    parser.add_argument("--text-only", action="store_true", help="Cache a small pinned reference snapshot over HTTPS, without Git or media.")
    parser.add_argument("--git", help="Explicit git executable")
    args = parser.parse_args()

    if args.library == "all" and (args.install_missing or args.update):
        parser.error("Select one --library for download/update after reading its reference and license; all is read-only")
    if args.text_only and (args.library not in PRIMARY_SOURCES or not args.install_missing or args.update):
        parser.error("--text-only requires one primary --library and --install-missing, without --update")

    git = args.git or shutil.which("git")
    if not git and not args.text_only and args.library not in WEB_SOURCES:
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
        if name in WEB_SOURCES and (args.install_missing or args.update):
            try:
                snapshot_result = cache_index(target)
                action, error = snapshot_result["action"], snapshot_result["error"]
            except (OSError, ValueError) as exc:
                action, error = "web-index-failed", str(exc)
        elif args.text_only:
            snapshot_result = download_reference_snapshot(name, target)
            action, error = snapshot_result["action"], snapshot_result["error"]
        elif not target.exists() and args.install_missing:
            metadata = PRIMARY_SOURCES.get(name, {})
            patterns = metadata.get("sparse_patterns", [])
            commands = [[git, "clone", "--depth", "1", "--filter=blob:none", "--no-checkout", url, str(target)],
                        [git, "-C", str(target), "sparse-checkout", "set", "--no-cone", *patterns],
                        [git, "-C", str(target), "checkout"]] if patterns else [[git, "clone", "--depth", "1", url, str(target)]]
            action = "sparse-cloned" if patterns else "cloned"
            try:
                for command in commands:
                    result = run(command)
                    if result.returncode:
                        error = result.stderr.strip() or result.stdout.strip()
                        break
            except subprocess.TimeoutExpired:
                error = "Download timed out; partial cache retained for inspection, not marked ready."
        elif target.exists() and args.update:
            state = run([git, "-C", str(target), "status", "--porcelain"])
            remote = run([git, "-C", str(target), "remote", "get-url", "origin"])
            if state.returncode or state.stdout.strip():
                error = "Refusing update: not a clean Git checkout; preserve local changes."
            elif remote.returncode or remote.stdout.strip().removesuffix(".git").rstrip("/") != url.removesuffix(".git"):
                error = "Refusing update: origin does not match the registered source."
            else:
                try:
                    result = run([git, "-C", str(target), "pull", "--ff-only"])
                    action = "updated"
                    if result.returncode:
                        error = result.stderr.strip() or result.stdout.strip()
                except subprocess.TimeoutExpired:
                    error = "Update timed out; inspect the retained checkout before retrying."
        ok = valid_repo(target, name) and not error
        head = ""
        if ok and (target / "reference-snapshot" / "source.json").is_file():
            head = json.loads((target / "reference-snapshot" / "source.json").read_text(encoding="utf-8"))["head"]
        elif ok and name not in WEB_SOURCES:
            result = run([git, "-C", str(target), "rev-parse", "HEAD"])
            if result.returncode == 0:
                head = result.stdout.strip()
        record = {"name": name, "kind": library_kind(name), "origin": reference_origin(name), "url": url, "path": str(target), "ok": ok, "action": action, "head": head, "error": error}
        if name in PRIMARY_SOURCES:
            source = PRIMARY_SOURCES[name]
            record.update({"license": source["license"], "audited_commit": source["audited_commit"],
                           "matches_audit": head == source["audited_commit"] if head else None,
                           "cache_scope": "reference files; upstream demos may need additional assets",
                           "direct_import_ready": False})
        if name in WEB_SOURCES:
            record.update({"license": WEB_SOURCES[name]["license"], "cache_scope": "entry metadata only; no media copied",
                           "direct_import_ready": False})
        if name == "video-spec-builder" and ok:
            index_path = root / "video-spec-builder-index.json"
            index = {
                "library": name, "kind": "layout-template", "url": url, "head": head,
                "path": str(target), "license": "MIT", "license_path": str(target / "LICENSE"),
                "origin": "legacy", "direct_import_ready": False,
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
    # Independent selected caches can be prepared concurrently without clobbering each other's manifests.
    manifest_path = root / ("motion-libraries.json" if args.library == "all" else f"{args.library}.cache.json")
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    return 0 if all(item["ok"] for item in records) else 1


if __name__ == "__main__":
    raise SystemExit(main())
