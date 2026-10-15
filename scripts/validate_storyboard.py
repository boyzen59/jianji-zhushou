#!/usr/bin/env python3
"""Validate storyboard traceability and global, half-open frame ranges; not aesthetics."""
from __future__ import annotations
import argparse
import json
import math
from pathlib import Path

def validate_v3_policy(data: dict) -> list[str]:
    """Check declared v3 policy, not pixel visibility, motion quality or user approval."""
    errors = []
    def fail(message):
        errors.append(f"production_policy: {message}")
    def number(value):
        return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)
    policy = data.get("production_policy")
    if not isinstance(policy, dict):
        return ["production_policy: v3 policy object required"]
    expected = {
        "subtitles": {"mode": "off", "reserve_space": True},
        "ai_video": {"source_in_seconds": 0, "duration_seconds": 10, "playback_rate": 1, "plays": 1},
        "presenter": {"opening_fullscreen_seconds": 15, "later_mode": "bottom_right_pip"},
        "review": {"storyboard_approval_required": False, "word_language": "zh", "pdf_aspect": "16:9",
                   "english": "placeholder_until_zh_revision"},
    }
    for section, fields in expected.items():
        actual = policy.get(section)
        if not isinstance(actual, dict):
            fail(f"{section} object required")
            continue
        for key, value in fields.items():
            found = actual.get(key)
            valid = (found is value if isinstance(value, bool) else
                     number(found) and found == value if isinstance(value, (int, float)) else found == value)
            if not valid:
                fail(f"{section}.{key} must be {value!r} under the v3 default policy")
    sub = policy.get("subtitles", {})
    area = sub.get("safe_area") if isinstance(sub, dict) else None
    if not isinstance(area, dict) or not all(number(area.get(k)) for k in ("x", "y", "width", "height")):
        fail("subtitles.safe_area requires finite normalized x/y/width/height")
    elif not (0 <= area["x"] < 1 and 0 <= area["y"] < 1 and
              0 < area["width"] <= 1 and 0 < area["height"] <= 1 and
              area["x"] + area["width"] <= 1.000001 and area["y"] + area["height"] <= 1.000001):
        fail("subtitles.safe_area must fit within the frame")
    playbacks, asset_plays, text_values = {}, {}, {}
    scenes = data.get("scenes", [])
    for scene in scenes if isinstance(scenes, list) else []:
        if not isinstance(scene, dict):
            continue
        sid = scene.get("id", "scene")
        texts = scene.get("texts")
        if not isinstance(texts, list):
            fail(f"{sid}.texts list required (empty is allowed)")
            texts = []
        local_ids = set()
        for item in texts:
            if not isinstance(item, dict):
                fail(f"{sid}.texts item must be object")
                continue
            tid, role, zh = item.get("id"), item.get("role"), item.get("zh")
            if not all(isinstance(v, str) and v.strip() for v in (tid, role, zh)):
                fail(f"{sid}.texts requires stable id, content role and Chinese text")
                continue
            if role in ("subtitle", "subtitle_zh", "subtitle_en", "narration_subtitle", "narration"):
                fail(f"{sid}/{tid}: narration/subtitle text cannot be projected in subtitle-off mode")
            if tid in local_ids:
                fail(f"{sid}: duplicate text id {tid}")
            local_ids.add(tid)
            signature = (role, zh, item.get("en"))
            if tid in text_values and text_values[tid] != signature:
                fail(f"{tid}: conflicting text under the same stable id")
            text_values[tid] = signature
        layers = scene.get("media_layers", [])
        for layer in layers if isinstance(layers, list) else []:
            if not isinstance(layer, dict):
                continue
            if layer.get("availability") not in ("pending", "available"):
                fail(f"{sid}: media availability must be pending/available")
            if layer.get("kind") not in ("ai_video", "ai_image", "historical_image", "presenter", "other"):
                fail(f"{sid}: media kind missing or unknown")
            if layer.get("kind") != "ai_video":
                continue
            aid, pid = layer.get("asset_id"), layer.get("playback_id")
            if not all(isinstance(v, str) and v.strip() for v in (aid, pid)):
                fail(f"{sid}: AI video needs asset_id and playback_id")
                continue
            for key, expected_value in (("source_in_seconds", 0), ("source_out_seconds", 10), ("playback_rate", 1)):
                if not number(layer.get(key)) or layer[key] != expected_value:
                    fail(f"{sid}/{aid}: {key} must be {expected_value}; play the full 10 seconds once")
            start, end, fps = layer.get("visible_start_frame"), layer.get("visible_end_frame_exclusive"), data.get("fps")
            if not all(number(v) for v in (start, end, fps)) or end - start != 10 * fps:
                fail(f"{sid}/{aid}: AI video playback window must cover exactly 10 seconds")
            signature = (aid, start, end, layer.get("source_in_seconds"), layer.get("source_out_seconds"),
                         layer.get("playback_rate"), layer.get("path"), layer.get("availability"))
            if pid in playbacks and playbacks[pid] != signature:
                fail(f"{pid}: cross-scene playback must keep the same source and global clock")
            playbacks[pid] = signature
            if aid in asset_plays and asset_plays[aid] != pid:
                fail(f"{aid}: repeated AI video playback is not allowed")
            asset_plays[aid] = pid
    return errors

def validate(data: object, root: Path | None = None) -> dict:
    errors: list[str] = []
    warnings: list[str] = []
    def error(where, message):
        errors.append(f"{where}: {message}")
    def text(value):
        return isinstance(value, str) and bool(value.strip())
    def integer(value):
        return isinstance(value, int) and not isinstance(value, bool)
    def objects(value, where, nonempty=False):
        if not isinstance(value, list) or (nonempty and not value):
            error(where, "expected " + ("nonempty " if nonempty else "") + "list")
            return []
        result = []
        for i, item in enumerate(value):
            if not isinstance(item, dict):
                error(f"{where}[{i}]", "expected object")
            else:
                result.append(item)
        return result
    def index(items, where):
        result = {}
        for i, item in enumerate(items):
            key = item.get("id")
            if not text(key):
                error(f"{where}[{i}]", "missing string id")
            elif key in result:
                error(where, f"duplicate id {key}")
            else:
                result[key] = item
        return result
    if not isinstance(data, dict):
        return {"ok": False, "errors": ["root: expected object"], "warnings": []}
    schema = data.get("schema_version")
    if not integer(schema) or schema not in (4, 5):
        error("schema_version", "expected 4 (legacy) or 5 (v3 policy)")
    elif schema == 5:
        errors.extend(validate_v3_policy(data))
    else:
        warnings.append("Legacy schema 4: v3 subtitle, presenter and full-clip policy not validated.")
    if data.get("engine") != "remotion":
        error("engine", "must be remotion")
    fps, duration = data.get("fps"), data.get("duration_frames")
    if not integer(fps) or not 0 < fps <= 240:
        error("fps", "expected integer 1..240 (no silent fractional-rate conversion)")
    if not integer(duration) or duration <= 0:
        error("duration_frames", "expected positive integer")
    sentences = index(objects(data.get("source_sentences"), "source_sentences", True), "source_sentences")
    for key, sentence in sentences.items():
        if not text(sentence.get("text")):
            error(key, "source sentence text missing")
    refs = index(objects(data.get("reference_sources"), "reference_sources", True), "reference_sources")
    for key, ref in refs.items():
        if ref.get("origin") not in ("user_supplied", "supplementary", "legacy"):
            error(key, "reference origin must identify user_supplied/supplementary/legacy")
        if not text(ref.get("location")):
            error(key, "reference location (URL or document + section) missing")
    scenes = objects(data.get("scenes"), "scenes", True)
    index(scenes, "scenes")
    previous_end = 0
    for i, scene in enumerate(scenes):
        sid = scene.get("id", f"scene[{i}]")
        start, end = scene.get("start_frame"), scene.get("end_frame_exclusive")
        valid_range = integer(start) and integer(end) and 0 <= start < end
        if not valid_range:
            error(sid, "invalid half-open frame range")
        else:
            if start != previous_end:
                error(sid, f"gap/overlap: starts {start}, expected {previous_end}")
            previous_end = end
            settled = scene.get("settled_frame")
            if not integer(settled) or not start <= settled < end:
                error(sid, "settled_frame must be inside scene")
        if scene.get("engine", data.get("engine")) != "remotion":
            error(sid, "scene engine must be remotion")
        for field in ("narrative_intent", "start_state", "end_state", "component"):
            if not text(scene.get(field)):
                error(sid, f"missing {field}")
        source_ids = scene.get("source_ids")
        if not isinstance(source_ids, list) or not source_ids:
            error(sid, "source_ids must be a nonempty list")
        elif any(not text(key) or key not in sentences for key in source_ids):
            error(sid, "source_ids contains unknown sentence id")
        cue = scene.get("cue")
        if not isinstance(cue, dict) or not text(cue.get("precision")) or not text(cue.get("anchor")):
            error(sid, "cue must record precision and anchor (do not invent word accuracy)")
        uses = objects(scene.get("reference_uses"), f"{sid}.reference_uses", True)
        priority_seen = False
        adopted = False
        for use in uses:
            ref_id = use.get("source_id")
            ref = refs.get(ref_id) if isinstance(ref_id, str) else None
            if ref is None:
                error(sid, f"unknown reference source {ref_id!r}")
            else:
                priority_seen |= ref.get("origin") == "user_supplied"
            status = use.get("status")
            if status not in ("adopted", "considered_not_used"):
                error(sid, "reference use status must be adopted/considered_not_used")
            adopted |= status == "adopted"
            for field in ("mechanism", "reason", "adaptation"):
                if not text(use.get(field)):
                    error(sid, f"reference use missing {field}")
        if not priority_seen:
            error(sid, "user-supplied primary references have not been considered")
        if not adopted and not text(scene.get("original_design_reason")):
            error(sid, "original design needs reason after considering supplied references")
        beats = objects(scene.get("motion_beats"), f"{sid}.motion_beats", True)
        for beat in beats:
            for field in ("subject", "action", "parameters"):
                if not text(beat.get(field)):
                    error(sid, f"motion beat missing {field}")
            values = [beat.get(k) for k in ("start_frame", "peak_frame", "settled_frame")]
            if not all(integer(v) for v in values):
                error(sid, "beat frames must be integers")
            elif valid_range and not start <= values[0] <= values[1] <= values[2] < end:
                error(sid, "beat frame order/range invalid; cross-boundary motion belongs in transitions")
        for direction in ("transition_in", "transition_out"):
            transition = scene.get(direction)
            if not isinstance(transition, dict):
                error(sid, f"{direction} object missing")
                continue
            if not text(transition.get("type")) or not text(transition.get("description")):
                error(sid, f"{direction} requires type and description")
            window = transition.get("window_frames")
            if window is not None:
                if (not isinstance(window, list) or len(window) != 2 or
                    not all(integer(v) for v in window) or
                    not (0 <= window[0] < window[1]) or
                    (integer(duration) and window[1] > duration)):
                    error(sid, f"{direction} invalid global window_frames")
                elif valid_range:
                    boundary = start if direction == "transition_in" else end
                    if not window[0] <= boundary <= window[1]:
                        error(sid, f"{direction} window does not touch scene boundary")
            if transition.get("type") == "shared":
                if not text(transition.get("object_id")) or not isinstance(transition.get("boundary_state"), dict):
                    error(sid, f"{direction} shared transition needs object_id and boundary_state")
        layers = objects(scene.get("media_layers"), f"{sid}.media_layers")
        for layer in layers:
            pending = schema == 5 and layer.get("availability") == "pending"
            for field in (("asset_id",) if pending else ("asset_id", "path")):
                if not text(layer.get(field)):
                    error(sid, f"media layer missing {field}")
            a, b = layer.get("visible_start_frame"), layer.get("visible_end_frame_exclusive")
            if not integer(a) or not integer(b) or not 0 <= a < b or (integer(duration) and b > duration):
                error(sid, "media visibility window is invalid")
            elif valid_range and (b <= start or a >= end):
                error(sid, "media layer has no visible overlap with scene")
            if pending and layer.get("path") not in (None, ""):
                error(sid, "pending media must not claim a real path; store expected filename separately")
            if root is not None and pending:
                error(sid, f"media pending generation/delivery: {layer.get('asset_id')}")
            elif root is not None and text(layer.get("path")):
                actual = Path(layer["path"])
                if not actual.is_absolute():
                    actual = root / actual
                if not actual.is_file():
                    error(sid, f"media file not found: {actual}")
        status = scene.get("verification")
        if status not in ("planned", "implemented", "rendered", "reviewed"):
            error(sid, "verification must be planned/implemented/rendered/reviewed")
        if status in ("rendered", "reviewed") and not text(scene.get("evidence")):
            error(sid, "rendered/reviewed status needs actual evidence location")
    if integer(duration) and previous_end != duration:
        error("timeline", f"ends at {previous_end}, expected {duration}")
    for left, right in zip(scenes, scenes[1:]):
        outgoing, incoming = left.get("transition_out", {}), right.get("transition_in", {})
        if not isinstance(outgoing, dict) or not isinstance(incoming, dict):
            continue
        if outgoing.get("type") == "shared" or incoming.get("type") == "shared":
            for field in ("type", "object_id", "boundary_state", "window_frames"):
                if outgoing.get(field) != incoming.get(field):
                    error(f"{left.get('id')} -> {right.get('id')}", f"shared handoff mismatch: {field}")
    warnings.append("Structural validation only: no claim of factual, visual, audio-sync or aesthetic approval.")
    return {"ok": not errors, "scene_count": len(scenes), "errors": errors, "warnings": warnings}

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("storyboard", type=Path)
    parser.add_argument("--check-files", type=Path, metavar="MEDIA_ROOT", help="Also check media paths, relative to this directory.")
    parser.add_argument("--json-output", type=Path)
    args = parser.parse_args()
    try:
        data = json.loads(args.storyboard.read_text(encoding="utf-8-sig"))
        result = validate(data, args.check_files)
    except (OSError, ValueError) as exc:
        result = {"ok": False, "errors": [str(exc)], "warnings": []}
    rendered = json.dumps(result, ensure_ascii=False, indent=2)
    print(rendered)
    if args.json_output:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(rendered + "\n", encoding="utf-8")
    return 0 if result["ok"] else 1

if __name__ == "__main__":
    raise SystemExit(main())
