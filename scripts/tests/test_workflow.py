"""Behavioral regression tests for selective references and explicit project overrides."""
import json
import io
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from urllib.error import URLError
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from bootstrap_motion_libraries import PRIMARY_SOURCES, WEB_SOURCES, LIBRARIES, valid_repo, reference_origin, download_reference_snapshot
from prompt_motion_index import parse_entries
from validate_storyboard import validate
import test_storyboard

ROOT = Path(__file__).resolve().parents[2]

class OverrideTests(unittest.TestCase):
    def setUp(self):
        self.data = json.loads((ROOT / "assets/templates/storyboard-example.json").read_text(encoding="utf-8"))
    def change(self, section, field, value):
        self.data["production_policy"][section][field] = value
        self.data["production_policy"].setdefault("overrides", {})[f"{section}.{field}"] = "用户明确要求本片使用此设置"
    def test_subtitles_can_be_requested(self):
        self.change("subtitles", "mode", "burned")
        self.data["scenes"][0]["texts"][0]["role"] = "subtitle_zh"
        self.data["scenes"][1]["texts"][0]["role"] = "subtitle_zh"
        self.assertTrue(validate(self.data)["ok"], validate(self.data))
    def test_external_subtitles_are_not_projected(self):
        self.change("subtitles", "mode", "external")
        self.data["scenes"][0]["texts"][0]["role"] = "subtitle_zh"
        self.assertFalse(validate(self.data)["ok"])
    def test_override_needs_nonempty_basis(self):
        self.change("presenter", "opening_fullscreen_seconds", 0)
        self.data["production_policy"]["overrides"]["presenter.opening_fullscreen_seconds"] = ""
        self.assertFalse(validate(self.data)["ok"])
    def test_no_presenter_and_explicit_approval_supported(self):
        self.change("presenter", "opening_fullscreen_seconds", 0)
        self.change("presenter", "later_mode", "none")
        self.change("review", "storyboard_approval_required", True)
        self.assertTrue(validate(self.data)["ok"], validate(self.data))
    def test_invalid_override_values_still_fail(self):
        for value in (-1, float("nan"), "ten", True):
            self.setUp()
            self.change("ai_video", "duration_seconds", value)
            self.assertFalse(validate(self.data)["ok"], value)
    def test_unknown_override_rejected(self):
        self.data["production_policy"]["overrides"] = {"typo": "user choice"}
        self.assertFalse(validate(self.data)["ok"])
    def test_custom_video_clock(self):
        # Same 10-second timeline, but an explicitly requested 5-second source at half speed.
        fixture = test_storyboard.ProductionPolicyTests()
        fixture.setUp()
        fixture.add_video()
        self.data = fixture.data
        self.change("ai_video", "source_in_seconds", 2)
        self.change("ai_video", "duration_seconds", 5)
        self.change("ai_video", "playback_rate", 0.5)
        for scene in self.data["scenes"]:
            layer = scene["media_layers"][0]
            layer.update(source_in_seconds=2, source_out_seconds=7, playback_rate=0.5)
        self.assertTrue(validate(self.data)["ok"], validate(self.data))
        self.data["scenes"][1]["media_layers"][0]["visible_end_frame_exclusive"] = 540
        self.assertFalse(validate(self.data)["ok"])
    def test_override_does_not_disable_structural_checks(self):
        self.change("review", "storyboard_approval_required", True)
        self.data["scenes"][1]["start_frame"] += 1
        self.assertFalse(validate(self.data)["ok"])

class RegistryTests(unittest.TestCase):
    def test_snapshot_hashes_and_preserves_local_changes(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            with patch("bootstrap_motion_libraries.urlopen", side_effect=lambda *a, **k: io.BytesIO(b"reference fixture")):
                result = download_reference_snapshot("xilo-opus-video", root)
            self.assertFalse(result["error"])
            self.assertTrue(valid_repo(root, "xilo-opus-video"))
            edited = root / "reference-snapshot" / "skills/xilo-opus-video/SKILL.md"
            edited.write_text("local edit", encoding="utf-8")
            self.assertFalse(valid_repo(root, "xilo-opus-video"))
            self.assertTrue(download_reference_snapshot("xilo-opus-video", root)["error"])
            self.assertEqual(edited.read_text(encoding="utf-8"), "local edit")
    def test_failed_snapshot_does_not_write_a_partial_ready_cache(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            with patch("bootstrap_motion_libraries.urlopen", side_effect=[io.BytesIO(b"ok"), URLError("offline")]):
                result = download_reference_snapshot("xilo-opus-video", root)
            self.assertTrue(result["error"])
            self.assertFalse(valid_repo(root, "xilo-opus-video"))
            self.assertEqual(list((root / "reference-snapshot").rglob("*")), [])
    def test_all_primary_sources_are_registered(self):
        self.assertEqual(len(PRIMARY_SOURCES), 17)
        self.assertIn("prompt-motion-charts", WEB_SOURCES)
        for name, source in PRIMARY_SOURCES.items():
            self.assertEqual(reference_origin(name), "user_supplied")
            self.assertEqual(LIBRARIES[name], source["url"])
            self.assertEqual(len(source["audited_commit"]), 40)
            self.assertTrue(source["required_files"])
    def test_web_index_filters_charts_and_rejects_unrelated_items(self):
        entries = [{"slug":"chart-demo","title":"Chart","contentTags":["charts"],"handle":"author"},
                   {"slug":"unrelated","contentTags":["phone"]}]
        chunk = "0:" + json.dumps(entries, separators=(",", ":"))
        html = "<script>self.__next_f.push(" + json.dumps([1, chunk]) + ")</script>"
        found = parse_entries(html)
        self.assertEqual([item["id"] for item in found], ["chart-demo"])
        self.assertEqual(found[0]["status"], "index_only")
        self.assertEqual(parse_entries("<html>changed</html>"), [])
    def test_no_fake_ready_from_unrelated_markdown(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / ".git").mkdir()
            for i in range(4):
                (root / f"unrelated{i}.md").write_text("unrelated", encoding="utf-8")
            self.assertFalse(valid_repo(root, "lemo-opuscar"))
            for relative in PRIMARY_SOURCES["lemo-opuscar"]["required_files"]:
                p = root / relative
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_text("style index", encoding="utf-8")
            self.assertTrue(valid_repo(root, "lemo-opuscar"))
    def test_search_wtt_is_enabled_and_labels_scope(self):
        with tempfile.TemporaryDirectory() as folder:
            p = Path(folder) / "wtt-code-animation-studio" / "scene.md"
            p.parent.mkdir()
            p.write_text("timing continuity", encoding="utf-8")
            run = subprocess.run([sys.executable, "-X", "utf8", str(ROOT / "scripts/query_motion_library.py"),
                                  "timing", "--library", "wtt-code-animation-studio", "--cache-root", folder],
                                 capture_output=True, text=True, encoding="utf-8")
            self.assertEqual(run.returncode, 0, run.stderr)
            report = json.loads(run.stdout)
            self.assertEqual(report["results"][0]["library"], "wtt-code-animation-studio")
            self.assertIn("cached text", report["scope"])

if __name__ == "__main__":
    unittest.main()
