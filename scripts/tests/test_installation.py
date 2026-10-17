"""Behavioral tests for content-wide discovery and project-local support setup."""
import contextlib
import io
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import check_installation as check
import setup_support as setup
import query_motion_library as query
from bootstrap_motion_libraries import PRIMARY_SOURCES, WEB_SOURCES


class SupportTests(unittest.TestCase):
    def test_features_deduplicate_and_keep_core(self):
        self.assertEqual(check.selected_features(["maps", "charts", "maps"]), ["core", "maps", "charts"])
        need = check.requirements(check.selected_features(["maps", "charts"]))
        self.assertEqual(sum(p["name"] == "d3" for p in need["npm"]), 1)
        self.assertIn("iart-map-animation", need["sources"])
        self.assertIn("iart-data-animation", need["sources"])

    def test_all_references_can_be_prepared_together(self):
        need = check.requirements(check.selected_features(["all"]))
        self.assertTrue((set(PRIMARY_SOURCES) | set(WEB_SOURCES)).issubset(need["sources"]))
        self.assertEqual(len(need["sources"]), len(set(need["sources"])))
        self.assertEqual({p["name"] for p in need["npm"] if p["name"] in ("mermaid", "roughjs")}, {"mermaid", "roughjs"})

    def test_unknown_feature_fails(self):
        with self.assertRaises(ValueError):
            check.selected_features(["typo"])

    def test_minimum_python_distribution_versions(self):
        self.assertTrue(check.python_requirement_ok("4.0.1", "reportlab>=4"))
        self.assertTrue(check.python_requirement_ok("0.11.0", "pdfplumber>=0.11"))
        self.assertFalse(check.python_requirement_ok("0.10.9", "pdfplumber>=0.11"))
        self.assertFalse(check.python_requirement_ok(None, "numpy"))

    def test_remotion_alignment_not_forced_to_starter_version(self):
        packages = {name: {"installed": True, "version": "4.0.500"} for name in ("remotion", "@remotion/cli", "@remotion/three")}
        self.assertEqual(check.remotion_version_errors(packages), [])
        packages["@remotion/three"]["version"] = "4.0.499"
        self.assertTrue(check.remotion_version_errors(packages))

    @unittest.skipUnless(shutil.which("node"), "Node unavailable")
    def test_export_restricted_package_metadata_resolves_without_execution(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            package = root / "node_modules" / "d3"
            package.mkdir(parents=True)
            (package / "package.json").write_text(json.dumps({"name": "d3", "version": "7.9.0", "type": "module", "exports": "./src/index.js"}))
            result = check.node_packages(root, ["d3", "not-present"], shutil.which("node"))
            self.assertEqual(result["d3"]["version"], "7.9.0")
            self.assertFalse(result["not-present"]["installed"])

    def test_catalog_does_not_filter_uninstalled_sources_or_include_rejected_four(self):
        with tempfile.TemporaryDirectory() as folder:
            result = query.analysis_catalog(Path(folder))
        ids = [p["source_id"] for p in result["sources"]]
        self.assertTrue(set(PRIMARY_SOURCES) | set(WEB_SOURCES) <= set(ids))
        self.assertEqual(len(ids), len(set(ids)))
        registry = json.loads((check.SKILL_ROOT / "references/motion-sources.json").read_text(encoding="utf-8"))
        self.assertTrue(set(ids).isdisjoint(registry["excluded_sources"]))
        self.assertNotIn("hyperframes-student-kit", ids)
        self.assertTrue(all(not p["cache_ready"] for p in result["sources"]))
        self.assertTrue(all(p["analysis_status"] == "unassessed" for p in result["sources"]))

    def test_feature_search_cannot_leak_unrelated_cached_effect(self):
        with tempfile.TemporaryDirectory() as folder:
            for name in ("iart-map-animation", "mg-styles-15"):
                target = Path(folder) / name
                target.mkdir()
                (target / "reference.md").write_text("route animation", encoding="utf-8")
            output = io.StringIO()
            with patch.object(sys, "argv", ["query", "route", "--feature", "maps", "--cache-root", folder]), contextlib.redirect_stdout(output):
                self.assertEqual(query.main(), 0)
            result = json.loads(output.getvalue())
            self.assertEqual(result["selected_libraries"], ["iart-map-animation"])
            self.assertEqual({x["library"] for x in result["results"]}, {"iart-map-animation"})


class SetupTests(unittest.TestCase):
    def test_new_empty_project_scaffold(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder) / "film"
            setup.prepare_project(root)
            package = json.loads((root / "package.json").read_text(encoding="utf-8"))
            self.assertIn("remotion", package["dependencies"])
            self.assertTrue((root / "src/index.tsx").is_file())

    def test_nonempty_user_folder_preserved(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            note = root / "user.txt"
            note.write_text("keep me")
            with self.assertRaises(ValueError):
                setup.prepare_project(root)
            self.assertEqual(note.read_text(), "keep me")
            self.assertFalse((root / "package.json").exists())

    def test_foreign_project_preserved(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            package = root / "package.json"
            original = '{"name":"other-project"}'
            package.write_text(original)
            with self.assertRaises(ValueError):
                setup.prepare_project(root)
            self.assertEqual(package.read_text(), original)

    def test_existing_remotion_lockfile_preserved(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "package.json").write_text('{"dependencies":{"remotion":"4.0.500"}}')
            lock = root / "package-lock.json"
            lock.write_text('{"user":"locked"}')
            setup.prepare_project(root)
            self.assertEqual(lock.read_text(), '{"user":"locked"}')
            self.assertFalse((root / "src").exists())

    def test_check_only_never_runs_install_commands_or_creates_project(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder) / "not-created"
            with patch.object(sys, "argv", ["setup", "--project-root", str(root)]), patch("check_installation.main", return_value=1), patch.object(setup, "run") as execute:
                self.assertEqual(setup.main(), 1)
            execute.assert_not_called()
            self.assertFalse(root.exists())

    def test_install_plan_adds_only_missing_optional_not_downgrading_core(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "package.json").write_text('{"dependencies":{"remotion":"4.0.500"}}')
            lock = root / "package-lock.json"
            lock.write_text('{"user":"locked"}')
            need = check.requirements(check.selected_features(["maps"]))
            packages = {p["name"]: {"installed": p["name"] not in ("d3", "@types/d3"), "version": "4.0.500"} for p in need["npm"]}
            with patch.object(sys, "argv", ["setup", "--project-root", str(root), "--feature", "maps", "--install"]), patch.object(setup, "command_path", side_effect=lambda name, _: name), patch.object(setup, "node_packages", return_value=packages), patch.object(setup, "run") as execute, contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(setup.main(), 0)
            commands = [call.args[0] for call in execute.call_args_list]
            self.assertIn(["npm", "ci"], commands)
            self.assertIn(["npm", "install", "d3@7.9.0"], commands)
            self.assertIn(["npm", "install", "--save-dev", "@types/d3"], commands)
            self.assertFalse(any(any("remotion@" in arg for arg in cmd) for cmd in commands))
            self.assertEqual(lock.read_text(), '{"user":"locked"}')


if __name__ == "__main__":
    unittest.main()
