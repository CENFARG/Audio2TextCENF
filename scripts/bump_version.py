"""bump_version.py — Atomic version bump for Audio2Text (CENF GIT-007 SemVer 2.0.0).

Canonical source: pyproject.toml [project] version.
This script updates ALL version sources in one shot, then optionally commits and tags.

Sources updated on every bump:
  1. pyproject.toml                        (canonical)
  2. backend/config_manager.py             (default_config app_version)
  3. lang/es.json + lang/en.json           (app_title "Audio2Text CENF vX.Y.Z")
  4. config/version_info.txt               (filevers/FileVersion/ProductVersion)
  5. config/version_info_GENERAL.txt
  6. config/version_info_CONTRERAS.txt
  7. config/version_info_CUTIGNOLA.txt
  8. scripts/build_GENERAL_v2.py           (APP_VERSION)
  9. setup.py                              (reads pyproject dynamically — no bump needed,
                                            validated by check_version.py)

Release-only (requires --release; do this ONLY when publishing the installer):
  - config/version.json (version + release_date + min_version)
    NOTE: version.json is the updater manifest served from `main`. Bumping it in a
    dev branch has no effect until merged; bump it with --release right after the
    installer for that version is published to GitHub Releases.

Usage:
  python scripts/bump_version.py 0.16.0            # bump everything + commit + tag
  python scripts/bump_version.py 0.16.0 --dry-run  # show what would change
  python scripts/bump_version.py 0.16.0 --no-tag   # bump + commit, skip tag
  python scripts/bump_version.py 0.16.0 --release  # ALSO bump version.json

After bumping, always run: python scripts/check_version.py
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import re
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

INFO_FILES = [
    PROJECT_ROOT / "config" / "version_info.txt",
    PROJECT_ROOT / "config" / "version_info_GENERAL.txt",
    PROJECT_ROOT / "config" / "version_info_CONTRERAS.txt",
    PROJECT_ROOT / "config" / "version_info_CUTIGNOLA.txt",
]


def _load_json(p: Path) -> dict:
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        raise SystemExit(f"[ERR] reading {p}: {e}") from e


def _save_json(p: Path, data: dict, indent: int) -> None:
    try:
        p.write_text(json.dumps(data, ensure_ascii=False, indent=indent) + "\n", encoding="utf-8")
    except OSError as e:
        raise SystemExit(f"[ERR] writing {p}: {e}") from e


def read_canonical_version() -> str:
    text = (PROJECT_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    m = re.search(r'^\s*version\s*=\s*["\']([^"\']+)["\']', text, re.MULTILINE)
    if not m:
        raise SystemExit("[ERR] cannot read canonical version from pyproject.toml")
    return m.group(1).strip()


def valid_semver(version: str) -> bool:
    return bool(re.fullmatch(r"\d+\.\d+\.\d+", version))


def replace_version_in_text(text: str, old: str, new: str) -> tuple[str, int]:
    """Replace exact-version occurrences, longest-literal first to avoid prefix hits."""
    count = text.count(old)
    return text.replace(old, new), count


def bump_pyproject(new: str) -> int:
    p = PROJECT_ROOT / "pyproject.toml"
    text = p.read_text(encoding="utf-8")
    text, n = re.subn(
        r'(?m)^(\s*version\s*=\s*["\'])[^"\']+(["\'])',
        rf"\g<1>{new}\g<2>",
        text,
        count=1,
    )
    p.write_text(text, encoding="utf-8")
    return n


def bump_config_manager(new: str) -> int:
    p = PROJECT_ROOT / "backend" / "config_manager.py"
    text = p.read_text(encoding="utf-8")
    text, n = re.subn(r'("app_version"\s*:\s*")[^"]+(")', rf"\g<1>{new}\g<2>", text, count=1)
    p.write_text(text, encoding="utf-8")
    return n


def bump_lang_titles(new: str) -> int:
    total = 0
    for name in ("es", "en"):
        p = PROJECT_ROOT / "lang" / f"{name}.json"
        data = _load_json(p)
        title = data.get("app_title", "")
        m = re.search(r"(\d+\.\d+\.\d+)", title)
        if m:
            data["app_title"] = title.replace(m.group(1), new)
            _save_json(p, data, indent=2)
            total += 1
    return total


def bump_info_files(new: str) -> int:
    total = 0
    parts = new.split(".")
    tuple_ver = f"({', '.join(parts + ['0'])})"  # (0, 16, 0, 0)
    for p in INFO_FILES:
        text = p.read_text(encoding="utf-8")
        text, n1 = re.subn(r"filevers=\(\d+, \d+, \d+, \d+\)", f"filevers={tuple_ver}", text)
        text, n2 = re.subn(r"(u'FileVersion',\s*u')[^']+(')", rf"\g<1>{new}.0\g<2>", text)
        text, n3 = re.subn(r"(u'ProductVersion',\s*u')[^']+(')", rf"\g<1>{new}\g<2>", text)
        p.write_text(text, encoding="utf-8")
        total += n1 + n2 + n3
    return total


def bump_build_script(new: str) -> int:
    p = PROJECT_ROOT / "scripts" / "build_GENERAL_v2.py"
    if not p.exists():
        return 0
    text = p.read_text(encoding="utf-8")
    text, n = re.subn(
        r'(?m)^(\s*APP_VERSION\s*=\s*["\'])[^"\']+(["\'])', rf"\g<1>{new}\g<2>", text, count=1
    )
    p.write_text(text, encoding="utf-8")
    return n


def bump_release_manifest(new: str) -> int:
    p = PROJECT_ROOT / "config" / "version.json"
    data = _load_json(p)
    data["version"] = new
    data["min_version"] = new
    data["release_date"] = _dt.date.today().isoformat()
    data["download_url"] = (
        f"https://github.com/CENFARG/Audio2TextCENF/releases/download/v{new}/"
        f"Audio2Text_CENF_v{new}.exe"
    )
    _save_json(p, data, indent=4)
    return 1


def run_git(*args: str) -> None:
    subprocess.run(["git", *args], check=True, cwd=PROJECT_ROOT)


def main() -> None:
    parser = argparse.ArgumentParser(description="Atomic version bump (CENF GIT-007)")
    parser.add_argument("version", help="target version, SemVer X.Y.Z (no pre-suffix)")
    parser.add_argument("--dry-run", action="store_true", help="show plan, change nothing")
    parser.add_argument("--no-tag", action="store_true", help="skip git tag vX.Y.Z")
    parser.add_argument(
        "--release",
        action="store_true",
        help="also bump config/version.json (updater manifest) — ONLY at publish time",
    )
    args = parser.parse_args()

    if not valid_semver(args.version):
        raise SystemExit("[ERR] version must be SemVer X.Y.Z (e.g. 0.16.0)")

    old = read_canonical_version()
    new = args.version
    if old == new and not args.dry_run:
        raise SystemExit(f"[ERR] canonical version is already {new}")

    print(f"Bump plan: {old} -> {new}")
    if args.dry_run:
        print("Dry run — nothing was modified.")
        return

    steps: list[tuple[str, int]] = [
        ("pyproject.toml", bump_pyproject(new)),
        ("backend/config_manager.py", bump_config_manager(new)),
        ("lang/app_title (es+en)", bump_lang_titles(new)),
        ("version_info x4", bump_info_files(new)),
        ("scripts/build_GENERAL_v2.py", bump_build_script(new)),
    ]
    if args.release:
        steps.append(("config/version.json (RELEASE)", bump_release_manifest(new)))

    for name, count in steps:
        print(f"  [{'OK' if count else '!!'}] {name}: {count} replacement(s)")

    run_git("add", "-A")
    tag = f"v{new}"
    run_git("commit", "-m", f"chore(version): atomic bump {old} -> {new}")
    if not args.no_tag:
        run_git("tag", "-a", tag, "-m", f"Release {new}")
        print(f"Tagged {tag}.")
    print(f"Done: {old} -> {new}. Run scripts/check_version.py to validate.")


if __name__ == "__main__":
    main()
