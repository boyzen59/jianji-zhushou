#!/usr/bin/env python3
"""Report installation support and a project-local installation plan; no automatic downloads."""
from __future__ import annotations
import argparse
import importlib.metadata
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

SKILL_ROOT = Path(__file__).resolve().parents[1]
MANIFEST = json.loads((SKILL_ROOT / "references/support-manifest.json").read_text(encoding="utf-8"))
FEATURES = MANIFEST["features"]
NODE_PROBE = r"""
const fs=require('fs'), path=require('path');
const root=process.argv[1], names=JSON.parse(process.argv[2]), out={};
for(const name of names){
 try{
  let file=path.join(root,'node_modules',...name.split('/'),'package.json');
  if(!fs.existsSync(file)){
   let dir=path.dirname(require.resolve(name,{paths:[root]}));
   while(true){
    const candidate=path.join(dir,'package.json');
    if(fs.existsSync(candidate) && JSON.parse(fs.readFileSync(candidate,'utf8')).name===name){file=candidate;break;}
    const parent=path.dirname(dir);if(parent===dir)throw Error('package metadata unavailable');dir=parent;
   }
  }
  const meta=JSON.parse(fs.readFileSync(file,'utf8'));
  out[name]={installed:true,version:meta.version,path:file};
 }catch(e){out[name]={installed:false,version:null};}
}
process.stdout.write(JSON.stringify(out));
"""

def selected_features(requested: list[str] | None) -> list[str]:
    chosen = list(FEATURES) if requested and "all" in requested else ["core", *(requested or ["documents"])]
    unknown = set(chosen) - set(FEATURES)
    if unknown:
        raise ValueError("Unknown features: " + ", ".join(sorted(unknown)))
    return list(dict.fromkeys(chosen))

def requirements(features: list[str]) -> dict:
    kit = json.loads((SKILL_ROOT / MANIFEST["runtime"]["remotion_kit"]).read_text(encoding="utf-8"))
    npm = {}
    for section in ("dependencies", "devDependencies"):
        for name, version in kit[section].items():
            npm[name] = {"name": name, "spec": f"{name}@{version}", "dev": section == "devDependencies"}
    python, skills, sources = {}, [], []
    for name in features:
        feature = FEATURES[name]
        for item in feature["python"]:
            python[item["distribution"].lower().replace("_", "-")] = item
        for item in feature["npm"]:
            npm[item["name"]] = item
        skills.extend(feature["skills"])
        sources.extend(feature["sources"])
    return {"python": list(python.values()), "npm": list(npm.values()),
            "skills": list(dict.fromkeys(skills)), "sources": list(dict.fromkeys(sources))}

def command_path(name: str, root: Path) -> str | None:
    found = shutil.which(name)
    if found:
        return found
    if name in ("ffmpeg", "ffprobe"):
        for suffix in (".exe", ""):
            found = next(root.glob(f"node_modules/@remotion/compositor-*/{name}{suffix}"), None)
            if found:
                return str(found.resolve())
    return None

def probe_version(path: str) -> str:
    try:
        args = [path, "-version"] if Path(path).stem in ("ffmpeg", "ffprobe") else [path, "--version"]
        result = subprocess.run(args, capture_output=True, text=True, timeout=10, errors="replace")
        return (result.stdout or result.stderr).strip().splitlines()[0][:180] if result.returncode == 0 else ""
    except (OSError, subprocess.SubprocessError, IndexError):
        return ""

def version_at_least(value: str, minimum: tuple[int, int]) -> bool:
    match = re.search(r"(\d+)\.(\d+)", value)
    return bool(match and tuple(map(int, match.groups())) >= minimum)

def python_requirement_ok(version: str | None, requirement: str) -> bool:
    """Evaluate the simple inclusive lower bounds declared by our manifest."""
    if version is None:
        return False
    if ">=" not in requirement:
        return True
    minimum = requirement.split(">=", 1)[1].strip()
    def release(value: str) -> tuple[int, ...]:
        match = re.match(r"\d+(?:\.\d+)*", value)
        return tuple(map(int, match.group().split("."))) if match else ()
    actual, wanted = release(version), release(minimum)
    width = max(len(actual), len(wanted))
    return bool(actual and wanted and actual + (0,) * (width - len(actual)) >= wanted + (0,) * (width - len(wanted)))

def node_packages(root: Path, names: list[str], node: str | None) -> dict:
    if not node or not root.is_dir():
        return {name: {"installed": False, "version": None} for name in names}
    try:
        result = subprocess.run([node, "-e", NODE_PROBE, str(root), json.dumps(names)],
                                capture_output=True, text=True, timeout=15)
        if result.returncode:
            return {name: {"installed": False, "version": None} for name in names}
        return json.loads(result.stdout)
    except (OSError, ValueError, subprocess.SubprocessError):
        return {name: {"installed": False, "version": None} for name in names}

def remotion_version_errors(packages: dict) -> list[str]:
    versions = {name: item.get("version") for name, item in packages.items()
                if (name == "remotion" or name.startswith("@remotion/")) and item.get("installed")}
    return ["Installed Remotion packages have different versions: " + json.dumps(versions)] if len(set(versions.values())) > 1 else []

def skill_status(name: str, codex_root: Path) -> dict:
    spec = MANIFEST["skill_catalog"][name]
    paths = sorted({str(p) for pattern in spec["paths"] for p in codex_root.glob(pattern)})
    return {"name": name, "purpose": spec["purpose"], "file_found": bool(paths), "paths": paths,
            "tool_state": "not_verified_by_filesystem", "availability": spec["availability"]}

def collect(root: Path, features: list[str], codex_root: Path) -> dict:
    need = requirements(features)
    errors, warnings = [], []
    if sys.version_info < (3, 10):
        errors.append("Python 3.10+ required; recommended 3.11/3.12.")
    commands = []
    for name in MANIFEST["runtime"]["commands"] + MANIFEST["runtime"]["reference_tools"]:
        path = command_path(name, root)
        version = probe_version(path) if path else ""
        required = name not in MANIFEST["runtime"]["reference_tools"]
        commands.append({"name": name, "path": path, "version": version, "required": required, "ok": bool(path and version)})
        if required and not (path and version):
            errors.append("Missing or unusable command: " + name)
    node = next((item for item in commands if item["name"] == "node"), {})
    if node.get("ok") and not version_at_least(node["version"], (18, 0)):
        errors.append("Node.js 18+ required; recommended 22/24 LTS.")
    packages = node_packages(root, [item["name"] for item in need["npm"]], node.get("path"))
    for item in need["npm"]:
        packages[item["name"]].update(spec=item["spec"], dev=item.get("dev", False))
        if not packages[item["name"]]["installed"]:
            errors.append("Missing project npm package: " + item["name"])
    # Include every declared @remotion package in the alignment check.
    package_file = root / "package.json"
    if package_file.is_file():
        try:
            declared = json.loads(package_file.read_text(encoding="utf-8-sig"))
            names = [name for section in ("dependencies", "devDependencies")
                     for name in declared.get(section, {}) if name.startswith("@remotion/")]
            extras = node_packages(root, names, node.get("path"))
            packages.update({name: item for name, item in extras.items() if name not in packages})
        except (OSError, ValueError) as exc:
            errors.append(f"Cannot read project package.json: {exc}")
    errors.extend(remotion_version_errors(packages))
    python = []
    for item in need["python"]:
        try:
            version = importlib.metadata.version(item["distribution"])
        except importlib.metadata.PackageNotFoundError:
            version = None
        compatible = python_requirement_ok(version, item["requirement"])
        python.append({**item, "version": version, "installed": version is not None, "compatible": compatible})
        if version is None:
            errors.append("Missing Python distribution in checked interpreter: " + item["distribution"])
        elif not compatible:
            errors.append("Python distribution below required minimum: " + item["requirement"] + " (found " + version + ")")
    skills = [skill_status(name, codex_root) for name in need["skills"]]
    for item in skills:
        if not item["file_found"]:
            warnings.append("Skill file not found in configured Codex folders: " + item["name"])
    from bootstrap_motion_libraries import DEFAULT_ROOT, valid_repo
    references = [{"name": name, "ready": valid_repo(DEFAULT_ROOT / name, name)} for name in need["sources"]]
    venv_python = root / ".venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    production = [item["spec"] for item in need["npm"] if not item.get("dev")]
    development = [item["spec"] for item in need["npm"] if item.get("dev")]
    kit = json.loads((SKILL_ROOT / MANIFEST["runtime"]["remotion_kit"]).read_text(encoding="utf-8"))
    core_names = {*kit["dependencies"], *kit["devDependencies"]}
    plan = {
        "template": {"from": str(SKILL_ROOT / "assets/remotion-kit"), "to": str(root),
                     "rule": "Copy only into an empty new project; preserve existing projects and their lockfiles."},
        "venv": None if venv_python.is_file() else [sys.executable, "-m", "venv", str(root / ".venv")],
        "python_packages": [str(venv_python), "-m", "pip", "install", *[item["requirement"] for item in need["python"]]] if need["python"] else [],
        "npm_core": ["npm", "ci"] if (root / "package-lock.json").is_file() else ["npm", "install"],
        "new_project_npm_specs": production,
        "new_project_dev_specs": development,
        "optional_npm": [item["spec"] for item in need["npm"] if item["name"] not in core_names],
        "browser": ["npx", "remotion", "browser", "ensure"],
        "smoke_test": ["npx", "remotion", "still", "src/index.tsx", "MotionStudy", ".jianji/install-smoke.png", "--frame=0"],
        "reference_cache": [name for name in need["sources"] if not next(item["ready"] for item in references if item["name"] == name)],
        "skill_installation": "Use the available skill-installer for standalone skills or enable the relevant PDF/Documents plugin. Built-in skills do not need duplicate installation.",
    }
    warnings.append("Browser launch, image-tool access and plugin availability require a smoke test/live tool check; files alone do not prove them.")
    return {"ok": not errors, "scope": "Selected interpreter, project npm packages and configured skill folders; no software installed.",
            "skill": MANIFEST["display_name"], "features": features,
            "python_runtime": {"path": sys.executable, "version": sys.version.split()[0], "recommended": "3.11/3.12"},
            "commands": commands, "npm": packages, "python_packages": python, "skills": skills,
            "conditional_skills": MANIFEST["conditional_skills"], "references": references,
            "install_plan": plan, "errors": errors, "warnings": warnings}

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", required=True, type=Path)
    parser.add_argument("--feature", action="append", choices=("all", *FEATURES), default=[])
    parser.add_argument("--codex-root", type=Path, default=Path(os.environ.get("CODEX_HOME", Path.home() / ".codex")))
    parser.add_argument("--json-output", type=Path)
    parser.add_argument("--format", choices=("text", "json"), default="text")
    args = parser.parse_args()
    result = collect(args.project_root.expanduser().resolve(), selected_features(args.feature), args.codex_root.expanduser().resolve())
    if args.json_output:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if args.format == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"{result['skill']} installation support: {'READY' if result['ok'] else 'NEEDS SUPPORT'}")
        print("Features: " + ", ".join(result["features"]))
        print("Python checked: " + result["python_runtime"]["path"] + " (" + result["python_runtime"]["version"] + ")")
        print("Core npm pins come from assets/remotion-kit/package.json; existing project versions are preserved.")
        for item in result["errors"]:
            print("MISSING: " + item)
        for item in result["skills"]:
            print("SKILL: " + item["name"] + (" file found; live tools not checked" if item["file_found"] else " file not found"))
        print("Reference caches: " + ", ".join(item["name"] + (" ready" if item["ready"] else " optional/missing") for item in result["references"]))
        print("INSTALL PLAN (argv; run in the selected project, using its .venv):")
        print(json.dumps(result["install_plan"], ensure_ascii=False, indent=2))
        for item in result["warnings"]:
            print("NOTE: " + item)
    return 0 if result["ok"] else 1

if __name__ == "__main__":
    raise SystemExit(main())
