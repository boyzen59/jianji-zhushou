#!/usr/bin/env python3
"""Search external motion libraries and indexed Spec Mono layout source functions."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from bootstrap_motion_libraries import DEFAULT_ROOT, LIBRARIES, library_kind, template_sources

LIBS = tuple(LIBRARIES)
ALLOWED = {".md", ".json", ".tsx", ".ts", ".jsx", ".js", ".css"}


def terms(value: str) -> list[str]:
    return [item.lower() for item in re.findall(r"[\w\-]+", value, flags=re.UNICODE) if len(item) > 1]


def main() -> int:
    parser = argparse.ArgumentParser(description="Search external motion libraries.")
    parser.add_argument("query")
    parser.add_argument("--library", choices=("all",) + LIBS, default="all")
    parser.add_argument("--cache-root", type=Path, default=DEFAULT_ROOT)
    parser.add_argument("--limit", type=int, default=20)
    args = parser.parse_args()
    needles = terms(args.query)
    if not needles:
        raise SystemExit("query has no searchable terms")
    selected = LIBS if args.library == "all" else (args.library,)
    hits = []
    root = args.cache_root.expanduser().resolve()
    for lib in selected:
        base = root / lib
        if not base.is_dir():
            continue
        if lib == "video-spec-builder":
            index_path = root / "video-spec-builder-index.json"
            index = json.loads(index_path.read_text(encoding="utf-8")) if index_path.is_file() else {"sources": template_sources(base)}
            bodies = {}
            compact_query = re.sub(r"[\W_]+", "", args.query.lower())
            for source in index["sources"]:
                if not source.get("enabled", True):
                    continue
                path = base / source["relative_path"]
                if not path.is_file():
                    continue
                if path not in bodies:
                    bodies[path] = path.read_text(encoding="utf-8", errors="ignore").splitlines()
                lines = bodies[path]
                body = "\n".join(lines[source["line"] - 1:source.get("end_line", len(lines))]).lower()
                exact = compact_query in {re.sub(r"[\W_]+", "", source.get(field, "").lower()) for field in ("id", "symbol")}
                score = (100 if exact else 0) + sum(8 for n in needles if n in source["relative_path"].lower()) + sum(min(body.count(n), 4) for n in needles)
                if score:
                    hits.append({"library": lib, "kind": "layout-template", "motion_share_eligible": False, "score": score, "path": str(path), "head": index.get("head", ""), "license": index.get("license", "MIT"), **source})
            continue
        for path in base.rglob("*"):
            if not path.is_file() or path.suffix.lower() not in ALLOWED or ".git" in path.parts:
                continue
            rel = path.relative_to(base).as_posix()
            try:
                body = path.read_text(encoding="utf-8", errors="ignore")[:12000].lower()
            except OSError:
                continue
            score = sum(8 for n in needles if n in rel.lower()) + sum(min(body.count(n), 4) for n in needles)
            if score:
                hits.append({"library": lib, "kind": library_kind(lib), "motion_share_eligible": True, "score": score, "path": str(path), "relative_path": rel})
    hits.sort(key=lambda item: (-item["score"], 0 if item["library"] == "video-shotcraft" else 1, item["relative_path"]))
    print(json.dumps({"query": args.query, "results": hits[: max(1, args.limit)]}, ensure_ascii=False, indent=2))
    return 0 if hits else 1


if __name__ == "__main__":
    raise SystemExit(main())
