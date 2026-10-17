#!/usr/bin/env python3
"""Search external motion libraries and indexed Spec Mono layout source functions."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from bootstrap_motion_libraries import DEFAULT_ROOT, LIBRARIES, PRIMARY_SOURCES, WEB_SOURCES, library_kind, reference_origin, template_sources
from check_installation import FEATURES

LIBS = tuple(LIBRARIES)
ALLOWED = {".md", ".json", ".tsx", ".ts", ".jsx", ".js", ".css"}


def terms(value: str) -> list[str]:
    return [item.lower() for item in re.findall(r"[\w\-]+", value, flags=re.UNICODE) if len(item) > 1]


def analysis_catalog(root: Path) -> dict:
    """Full analysis inventory, independent of installed packages or cached text."""
    from bootstrap_motion_libraries import valid_repo
    # Herk is the current name of the old HyperFrames kit, not a second capability.
    aliases = {"hyperframes-student-kit": "herk-edit-kit"}
    entries = []
    for name in LIBS:
        if name in aliases:
            continue
        source = PRIMARY_SOURCES.get(name, WEB_SOURCES.get(name, {}))
        entries.append({"source_id": name, "url": LIBRARIES[name],
                        "scope": "primary" if source else "supplementary",
                        "role": source.get("role", "See supplementary reference routing"),
                        "cache_ready": valid_repo(root / name, name),
                        "analysis_status": "unassessed", "source_sentence_ids": [], "reason": ""})
    return {"scope": "Capability inventory; not proof of source reading, code adaptation or render validation.",
            "aliases": aliases, "sources": entries}


def main() -> int:
    parser = argparse.ArgumentParser(description="Search external motion libraries.")
    parser.add_argument("query", nargs="?")
    parser.add_argument("--catalog", action="store_true", help="List all analysis candidates without downloading or filtering by installed support.")
    parser.add_argument("--library", choices=("all",) + LIBS, default="all")
    parser.add_argument("--cache-root", type=Path, default=DEFAULT_ROOT)
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--feature", action="append", choices=tuple(FEATURES), default=[],
                        help="Search only sources assigned to the selected content feature.")
    args = parser.parse_args()
    if args.catalog:
        if args.query or args.library != "all" or args.feature:
            parser.error("--catalog is an unfiltered inventory; do not combine with a query, --library or --feature.")
        print(json.dumps(analysis_catalog(args.cache_root.expanduser().resolve()), ensure_ascii=False, indent=2))
        return 0
    if not args.query:
        parser.error("Provide a query or --catalog.")
    needles = terms(args.query)
    if not needles:
        raise SystemExit("query has no searchable terms")
    selected = LIBS if args.library == "all" else (args.library,)
    if args.feature:
        relevant = {name for feature in args.feature for name in FEATURES[feature]["sources"]}
        selected = tuple(name for name in selected if name in relevant)
        if not selected:
            parser.error("No selected library belongs to these features.")
    hits = []
    root = args.cache_root.expanduser().resolve()
    for lib in selected:
        base = root / lib
        if not base.is_dir():
            continue
        if lib in WEB_SOURCES:
            index_path = base / "index.json"
            if not index_path.is_file():
                continue
            for entry in json.loads(index_path.read_text(encoding="utf-8")).get("entries", []):
                body = " ".join([entry.get("title", ""), entry.get("creator", ""), *entry.get("tags", [])]).lower()
                score = sum(min(body.count(n), 4) for n in needles)
                if score:
                    hits.append({"library":lib, "kind":"web-reference-index", "origin":"user_supplied",
                                 "score":score, "path":str(index_path), "relative_path":"index.json#" + entry["id"], **entry})
            continue
        if (base / "reference-snapshot" / "source.json").is_file():
            base = base / "reference-snapshot"
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
                    hits.append({"library": lib, "kind": "layout-template", "origin": "legacy", "score": score, "path": str(path), "head": index.get("head", ""), "license": index.get("license", "MIT"), **source})
            continue
        for path in base.rglob("*"):
            if not path.is_file() or path.suffix.lower() not in ALLOWED or any(p in path.parts for p in (".git", "node_modules", ".venv")):
                continue
            rel = path.relative_to(base).as_posix()
            try:
                body = path.read_text(encoding="utf-8", errors="ignore")[:12000].lower()
            except OSError:
                continue
            score = sum(8 for n in needles if n in rel.lower()) + sum(min(body.count(n), 4) for n in needles)
            if score:
                metadata = PRIMARY_SOURCES.get(lib, {})
                hits.append({"library": lib, "kind": library_kind(lib), "origin": reference_origin(lib), "score": score, "path": str(path), "relative_path": rel, "source_url": metadata.get("url", LIBRARIES[lib]), "license": metadata.get("license", "check upstream"), "audited_commit": metadata.get("audited_commit", "")})
    hits.sort(key=lambda item: (item["library"] not in PRIMARY_SOURCES and item["library"] not in WEB_SOURCES, -item["score"], item["library"], item["relative_path"]))
    missing = [lib for lib in selected if not (root / lib).is_dir()]
    print(json.dumps({"query": args.query, "features": args.feature, "selected_libraries": selected,
                      "scope": "cached text only, not live upstream search", "missing_cache": missing, "results": hits[: max(1, args.limit)]}, ensure_ascii=False, indent=2))
    return 0 if hits else 1


if __name__ == "__main__":
    raise SystemExit(main())
