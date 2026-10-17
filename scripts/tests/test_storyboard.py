#!/usr/bin/env python3
"""Regression tests for reference-first storyboards and frame coverage."""
import copy
import json
import sys
import subprocess
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from validate_storyboard import validate
from build_render_plan import normalize_scenes, build_segments, build_resource_tuning
from verify_master_media import verify

SAMPLE = Path(__file__).resolve().parents[2] / "assets/templates/storyboard-example.json"

class StoryboardTests(unittest.TestCase):
    def setUp(self):
        self.data = json.loads(SAMPLE.read_text(encoding="utf-8"))
    def reject(self):
        self.assertFalse(validate(self.data)["ok"])
    def test_example(self):
        self.assertTrue(validate(self.data)["ok"])
    def test_wrong_engine(self):
        self.data["engine"] = "p5"
        self.reject()
    def test_missing_engine_does_not_crash(self):
        del self.data["engine"]
        self.reject()
    def test_unknown_source_sentence(self):
        self.data["scenes"][0]["source_ids"] = ["invented"]
        self.reject()
    def test_required_user_reference(self):
        self.data["reference_sources"][0]["origin"] = "legacy"
        self.data["reference_sources"][1]["origin"] = "legacy"
        self.reject()
    def test_original_design_is_allowed(self):
        scene = self.data["scenes"][0]
        for use in scene["reference_uses"]:
            use["status"] = "considered_not_used"
        scene["original_design_reason"] = "This sentence needs an original reveal after studying the supplied approaches."
        self.assertTrue(validate(self.data)["ok"])
    def test_reference_names_alone_are_not_enough(self):
        del self.data["scenes"][0]["reference_uses"][0]["adaptation"]
        self.reject()
    def test_gap(self):
        self.data["scenes"][1]["start_frame"] += 1
        self.reject()
    def test_end_is_exclusive(self):
        self.data["scenes"][0]["settled_frame"] = 180
        self.reject()
    def test_beats_cannot_overrun(self):
        self.data["scenes"][0]["motion_beats"][0]["settled_frame"] = 180
        self.reject()
    def test_shared_handoff_geometry(self):
        self.data["scenes"][1]["transition_in"]["boundary_state"]["x"] += 10
        self.reject()
    def test_shared_handoff_window(self):
        self.data["scenes"][1]["transition_in"]["window_frames"] = [180, 210]
        self.reject()
    def test_fake_rendered_status(self):
        self.data["scenes"][0]["verification"] = "rendered"
        self.reject()
    def test_duplicate_scene_id(self):
        self.data["scenes"][1]["id"] = self.data["scenes"][0]["id"]
        self.reject()
    def test_malformed_objects(self):
        self.data["scenes"].append(None)
        self.reject()
    def test_fractional_fps_not_truncated(self):
        self.data["fps"] = 29.97
        self.reject()
    def test_missing_media(self):
        self.data["scenes"][0]["media_layers"] = [{
            "asset_id":"missing", "path":"never-present.jpg",
            "visible_start_frame":0, "visible_end_frame_exclusive":180
        }]
        self.assertFalse(validate(self.data, SAMPLE.parent)["ok"])
    def test_cannot_claim_zero_duration_media(self):
        self.data["scenes"][0]["media_layers"] = [{
            "asset_id":"demo", "path":"demo.png",
            "visible_start_frame":100, "visible_end_frame_exclusive":100
        }]
        self.reject()

class ProductionPolicyTests(unittest.TestCase):
    def setUp(self):
        self.data = json.loads(SAMPLE.read_text(encoding="utf-8"))
    def test_subtitles_off_requires_empty_projection(self):
        self.data["scenes"][0]["texts"][0]["role"] = "subtitle_zh"
        self.assertFalse(validate(self.data)["ok"])
    def test_no_subtitle_switch_without_policy_change(self):
        self.data["production_policy"]["subtitles"]["mode"] = "burned"
        self.assertFalse(validate(self.data)["ok"])
    def test_safe_area_must_be_inside_frame(self):
        self.data["production_policy"]["subtitles"]["safe_area"]["y"] = 0.99
        self.assertFalse(validate(self.data)["ok"])
    def test_legacy_compatibility_is_explicit(self):
        self.data["schema_version"] = 4
        del self.data["production_policy"]
        result = validate(self.data)
        self.assertTrue(result["ok"])
        self.assertTrue(any("Legacy" in w for w in result["warnings"]))
    def test_conflicting_stable_text_id(self):
        self.data["scenes"][1]["texts"][0]["zh"] = "不同文本"
        self.assertFalse(validate(self.data)["ok"])
    def add_video(self):
        self.data["duration_frames"] = 600
        self.data["scenes"][-1]["end_frame_exclusive"] = 600
        video = {"asset_id": "V001", "playback_id": "PLAY001", "kind": "ai_video",
                 "availability": "pending", "path": None, "source_in_seconds": 0,
                 "source_out_seconds": 10, "playback_rate": 1,
                 "visible_start_frame": 0, "visible_end_frame_exclusive": 600}
        for scene in self.data["scenes"]:
            scene["media_layers"] = [copy.deepcopy(video)]
        return self.data["scenes"][0]["media_layers"][0]
    def test_pending_full_video_across_scenes_is_valid_plan(self):
        self.add_video()
        self.assertTrue(validate(self.data)["ok"])
    def test_pending_video_not_production_ready(self):
        self.add_video()
        self.assertFalse(validate(self.data, SAMPLE.parent)["ok"])
    def test_trim_speed_and_short_window_rejected(self):
        for key, value in (("source_in_seconds", 1), ("source_out_seconds", 8),
                           ("playback_rate", 0.5), ("visible_end_frame_exclusive", 480)):
            self.setUp()
            self.add_video()[key] = value
            self.assertFalse(validate(self.data)["ok"], key)
    def test_repeat_video_rejected(self):
        self.add_video()
        self.data["scenes"][1]["media_layers"][0]["playback_id"] = "PLAY002"
        self.assertFalse(validate(self.data)["ok"])
    def test_fake_path_for_pending_asset_rejected(self):
        self.add_video()["path"] = "not-generated.mp4"
        self.assertFalse(validate(self.data)["ok"])

class RenderPlanTests(unittest.TestCase):
    def test_multiple_fps_and_contiguous_chunks(self):
        for fps in (24, 30, 60):
            raw = {"scenes":[{"id":"A","start":0,"end":200},{"id":"B","start":200,"end":400}]}
            scenes = normalize_scenes(raw, fps)
            segments = build_segments(scenes, fps)
            self.assertEqual(len(segments), 2)
            self.assertEqual(sum(s["frame_count"] for s in segments), 400 * fps)
            self.assertEqual(segments[1]["global_start_frame"], segments[0]["global_end_frame_inclusive"] + 1)
    def test_render_gap_rejected(self):
        with self.assertRaises(SystemExit):
            normalize_scenes({"scenes":[{"start":0,"end":2},{"start":2.1,"end":3}]}, 60)

class MediaProfileTests(unittest.TestCase):
    def setUp(self):
        self.metadata = {"format":{"format_name":"mov,mp4"}, "streams":[{
            "codec_type":"video", "codec_name":"h264", "profile":"100", "width":1920,
            "height":1080, "pix_fmt":"yuv420p", "color_range":"tv", "color_space":"bt709",
            "color_transfer":"bt709", "color_primaries":"bt709", "avg_frame_rate":"60/1",
            "r_frame_rate":"60/1", "nb_frames":"960"}]}
    def run_verify(self, **kwargs):
        return verify(self.metadata, width=1920, height=1080, expected_frames=960, **kwargs)[0]
    def test_numeric_h264_high_profile(self):
        self.assertEqual(self.run_verify(), [])
    def test_wrong_profile_still_fails(self):
        self.metadata["streams"][0]["profile"] = "77"
        self.assertTrue(self.run_verify())
    def test_requested_sound_missing(self):
        self.assertTrue(self.run_verify(audio_policy="required"))
    def test_requested_sound_present(self):
        self.metadata["streams"].append({"codec_type":"audio","codec_name":"aac"})
        self.assertEqual(self.run_verify(audio_policy="required"), [])
        self.assertTrue(self.run_verify(audio_policy="none"))
    def test_wrong_frame_count(self):
        self.metadata["streams"][0]["nb_frames"] = "959"
        self.assertTrue(self.run_verify())

class PreflightNoticeTests(unittest.TestCase):
    def test_unused_caches_do_not_create_notices(self):
        with tempfile.TemporaryDirectory() as folder:
            script = Path(__file__).resolve().parents[1] / "preflight_check.py"
            run = subprocess.run([sys.executable, "-X", "utf8", str(script), "--project-root", folder,
                                  "--cache-root", folder, "--stage", "text"], capture_output=True, text=True, encoding="utf-8")
            self.assertEqual(run.returncode, 0, run.stderr)
            report = json.loads(run.stdout)
            self.assertEqual(report["planning_status"], "REFERENCES_NOT_REQUESTED")
            self.assertFalse(report["reference_notice"]["required"])
            self.assertEqual(report["reference_libraries"], [])
    def test_only_selected_missing_caches_are_reported(self):
        with tempfile.TemporaryDirectory() as folder:
            script = Path(__file__).resolve().parents[1] / "preflight_check.py"
            run = subprocess.run([sys.executable, "-X", "utf8", str(script), "--project-root", folder,
                                  "--cache-root", folder, "--stage", "text",
                                  "--library", "lemo-opuscar", "--library", "wtt-code-animation-studio",
                                  "--library", "lemo-opuscar"], capture_output=True, text=True, encoding="utf-8")
            self.assertEqual(run.returncode, 0, run.stderr)
            report = json.loads(run.stdout)
            self.assertEqual(report["planning_status"], "SELECTED_REFERENCES_MISSING")
            self.assertEqual([r["name"] for r in report["reference_libraries"]],
                             ["lemo-opuscar", "wtt-code-animation-studio"])
    def test_no_blanket_install(self):
        script = Path(__file__).resolve().parents[1] / "bootstrap_motion_libraries.py"
        run = subprocess.run([sys.executable, "-X", "utf8", str(script), "--library", "all", "--install-missing"], capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(run.returncode, 2)
        self.assertIn("Select one", run.stderr)

if __name__ == "__main__":
    unittest.main(verbosity=2)
