"""Index publicly listed Prompt Motion chart entries; no media or prompt copying."""
from __future__ import annotations
import hashlib
import json
import re
from pathlib import Path
from urllib.request import Request, urlopen

URL = "https://prompt-motion.com/?tag=charts"

def parse_entries(html: str) -> list[dict]:
    decoder = json.JSONDecoder()
    result = {}
    for match in re.finditer(r"self\.__next_f\.push\(", html):
        try:
            block, _ = decoder.raw_decode(html[match.end():])
        except ValueError:
            continue
        if not isinstance(block, list) or len(block) < 2 or not isinstance(block[1], str):
            continue
        chunk = block[1]
        for start in re.finditer(r'\{"slug":', chunk):
            try:
                item, _ = decoder.raw_decode(chunk[start.start():])
            except ValueError:
                continue
            if not isinstance(item, dict) or "charts" not in item.get("contentTags", []):
                continue
            slug = item.get("slug", "")
            if not re.fullmatch(r"[a-zA-Z0-9_-]+", slug):
                continue
            result[slug] = {"id": slug, "title": item.get("title", slug),
                            "creator": item.get("handle", ""), "tags": item["contentTags"],
                            "url": "https://prompt-motion.com/" + slug,
                            "status": "index_only", "license": "check original creator",
                            "mechanism_review": "open the selected entry before adapting"}
    return list(result.values())

def valid_index(target: Path) -> bool:
    try:
        record = json.loads((target / "web-source.json").read_text(encoding="utf-8"))
        content = (target / "index.json").read_bytes()
        entries = json.loads(content)["entries"]
        return record["url"] == URL and record["sha256"] == hashlib.sha256(content).hexdigest() and bool(entries)
    except (OSError, ValueError, KeyError, TypeError):
        return False

def cache_index(target: Path) -> dict:
    if target.exists() and any(target.iterdir()):
        return {"action": "index-retained", "error": "" if valid_index(target) else
                "Existing cache is incomplete or changed; preserve it and use a fresh cache-root."}
    with urlopen(Request(URL, headers={"User-Agent":"jianji-reference-cache/3.1"}), timeout=25) as response:
        html = response.read(8_000_001)
    if len(html) > 8_000_000:
        raise ValueError("Page exceeds index limit")
    entries = parse_entries(html.decode("utf-8"))
    if not entries:
        raise ValueError("No chart entries parsed; site schema may have changed (not a successful empty cache).")
    data = {"url":URL, "scope":"discovery metadata only; videos not watched and prompts not copied", "entries":entries}
    body = (json.dumps(data,ensure_ascii=False,indent=2)+"\n").encode("utf-8")
    target.mkdir(parents=True,exist_ok=True)
    (target/"index.json").write_bytes(body)
    marker = {"url":URL,"sha256":hashlib.sha256(body).hexdigest(),"count":len(entries)}
    (target/"web-source.json").write_text(json.dumps(marker,indent=2)+"\n",encoding="utf-8")
    return {"action":"web-indexed","error":""}
