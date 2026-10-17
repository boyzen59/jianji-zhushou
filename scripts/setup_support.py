#!/usr/bin/env python3
"""Check support, or install it in an explicit Remotion project with --install."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys

from check_installation import SKILL_ROOT, FEATURES, selected_features, requirements, command_path, node_packages, collect

def run(args: list[str], root: Path) -> None:
    print("RUN " + json.dumps(args, ensure_ascii=False), flush=True)
    subprocess.run(args, cwd=root, check=True, timeout=900)

def prepare_project(root: Path) -> None:
    if root == root.parent or root == Path.home().resolve() or root == SKILL_ROOT or SKILL_ROOT in root.parents:
        raise ValueError("Choose a dedicated production project outside the installed skill.")
    root.mkdir(parents=True, exist_ok=True)
    for name in ("node_modules", ".venv"):
        location = root / name
        if location.exists() and location.resolve() != location.absolute():
            raise ValueError(f"{name} points to a shared environment; choose an isolated production project.")
    package = root / "package.json"
    if not package.is_file():
        if any(root.iterdir()):
            raise ValueError("Nonempty folder has no package.json; choose an empty production folder.")
        shutil.copytree(SKILL_ROOT / "assets/remotion-kit", root, dirs_exist_ok=True)
    else:
        meta = json.loads(package.read_text(encoding="utf-8-sig"))
        if "remotion" not in {**meta.get("dependencies", {}), **meta.get("devDependencies", {})}:
            raise ValueError("Existing project does not declare Remotion; choose its actual Remotion folder or a new empty folder.")

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", required=True, type=Path)
    parser.add_argument("--feature", choices=("all", *FEATURES), action="append", default=[])
    parser.add_argument("--install", action="store_true", help="Install selected support into this project's .venv/node_modules.")
    parser.add_argument("--with-references", action="store_true", help="Also cache selected pinned reference text.")
    args = parser.parse_args()
    root = args.project_root.expanduser().resolve()
    features = selected_features(args.feature)
    if not args.install:
        from check_installation import main as check_main
        forwarded = ["--project-root", str(root)]
        for feature in args.feature:
            forwarded += ["--feature", feature]
        sys.argv = [sys.argv[0], *forwarded]
        return check_main()
    try:
        if sys.version_info < (3, 10):
            raise ValueError("Python 3.10+ required; use Python 3.11/3.12.")
        node = command_path("node", root)
        npm = command_path("npm", root)
        npx = command_path("npx", root)
        if not all((node, npm, npx)):
            raise ValueError("Install Node.js LTS and npm first, then run setup again.")
        prepare_project(root)
        venv = root / ".venv"
        py = venv / ("Scripts/python.exe" if sys.platform == "win32" else "bin/python")
        if not py.is_file():
            run([sys.executable, "-m", "venv", str(venv)], root)
        need = requirements(features)
        if need["python"]:
            run([str(py), "-m", "pip", "install", *[item["requirement"] for item in need["python"]]], root)
        run([npm, "ci" if (root / "package-lock.json").is_file() else "install"], root)
        installed = node_packages(root, [item["name"] for item in need["npm"]], node)
        kit = json.loads((SKILL_ROOT / "assets/remotion-kit/package.json").read_text(encoding="utf-8"))
        base = {**kit["dependencies"], **kit["devDependencies"]}
        missing_core = [name for name in base if not installed[name]["installed"]]
        if missing_core:
            raise ValueError("Core packages still missing after project install: " + ", ".join(missing_core) +
                             ". Preserve the project's versions and complete its package.json before retrying.")
        for dev in (False, True):
            selected = [item["spec"] for item in need["npm"] if item["name"] not in base and
                        bool(item.get("dev")) == dev and not installed[item["name"]]["installed"]]
            if selected:
                run([npm, "install", *(["--save-dev"] if dev else []), *selected], root)
        run([npx, "remotion", "browser", "ensure"], root)
        # Reference text is cached; upstream setup scripts and paid APIs are not executed.
        if args.with_references:
            from bootstrap_motion_libraries import WEB_SOURCES, PRIMARY_SOURCES
            for source in need["sources"]:
                command = [str(py), "-X", "utf8", str(SKILL_ROOT / "scripts/bootstrap_motion_libraries.py"),
                           "--library", source, "--install-missing"]
                if source in PRIMARY_SOURCES:
                    command += ["--text-only"]
                run(command, root)
        report = root / ".jianji" / "installation.json"
        command = [str(py), "-X", "utf8", str(SKILL_ROOT / "scripts/check_installation.py"),
                   "--project-root", str(root), "--json-output", str(report)]
        for feature in features:
            command += ["--feature", feature]
        run(command, root)
        print("Support report: " + str(report))
        return 0
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        print("Setup incomplete: " + str(exc), file=sys.stderr)
        print("Existing files and downloaded dependencies are retained; inspect the error and rerun.")
        return 1

if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    raise SystemExit(main())
