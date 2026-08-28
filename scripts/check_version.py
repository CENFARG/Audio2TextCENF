"""
check_version.py — HC-05 single-source version validator

Fuenta canónica: pyproject.toml [project] version = "0.15.11"

Valida que estas 5 fuentes estén en 0.15.11:
  1. pyproject.toml
  2. backend/config_manager.py (default_config app_version)
  3. lang/es.json + lang/en.json (app_title contiene version)
  4. config/version_info.txt + config/version_info_GENERAL.txt (FileVersion/ProductVersion/filevers)
  5. scripts/build_GENERAL_v2.py (APP_VERSION)

Uso:
  python scripts/check_version.py        # usa EXPECTED = pyproject version (canónica)
  python scripts/check_version.py 0.15.11 # fuerza expected

Exit code: 0 si todas PASS, 1 si alguna FAIL.
"""
import re
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
EXPECTED_FALLBACK = "0.15.11"


def _read_pyproject_version() -> str | None:
    p = PROJECT_ROOT / "pyproject.toml"
    try:
        text = p.read_text(encoding="utf-8")
        m = re.search(r'^\s*version\s*=\s*["\']([^"\']+)["\']', text, re.MULTILINE)
        if m:
            return m.group(1).strip()
    except Exception as e:
        print(f"  [ERR] reading {p}: {e}")
    return None


def _read_config_manager_version() -> str | None:
    p = PROJECT_ROOT / "backend" / "config_manager.py"
    try:
        text = p.read_text(encoding="utf-8")
        m = re.search(r'"app_version"\s*:\s*"([^"]+)"', text)
        if m:
            return m.group(1).strip()
        m = re.search(r"'app_version'\s*:\s*'([^']+)'", text)
        if m:
            return m.group(1).strip()
    except Exception as e:
        print(f"  [ERR] reading {p}: {e}")
    return None


def _read_lang_version(lang_file: Path) -> str | None:
    try:
        data = json.loads(lang_file.read_text(encoding="utf-8"))
        title = data.get("app_title", "")
        m = re.search(r"(\d+\.\d+\.\d+)", title)
        if m:
            return m.group(1).strip()
        return title.strip() if title else None
    except Exception as e:
        print(f"  [ERR] reading {lang_file}: {e}")
    return None


def _read_version_info(path: Path) -> dict:
    """Return dict with filevers, FileVersion, ProductVersion or None values."""
    result = {"filevers": None, "FileVersion": None, "ProductVersion": None}
    try:
        text = path.read_text(encoding="utf-8")
        m = re.search(r"filevers\s*=\s*\(([^)]+)\)", text)
        if m:
            # e.g. 0, 15, 9, 0 -> 0.15.9
            parts = [p.strip() for p in m.group(1).split(",")]
            if len(parts) >= 3:
                result["filevers"] = ".".join(parts[:3])
        m = re.search(r"StringStruct\(u'FileVersion',\s*u'([^']+)'\)", text)
        if m:
            fv = m.group(1).strip()
            # 0.15.9.0 -> 0.15.9
            result["FileVersion"] = ".".join(fv.split(".")[:3])
        m = re.search(r"StringStruct\(u'ProductVersion',\s*u'([^']+)'\)", text)
        if m:
            pv = m.group(1).strip()
            result["ProductVersion"] = ".".join(pv.split(".")[:3])
    except Exception as e:
        print(f"  [ERR] reading {path}: {e}")
    return result


def _read_build_version(path: Path) -> str | None:
    try:
        text = path.read_text(encoding="utf-8")
        m = re.search(r'APP_VERSION\s*=\s*["\']([^"\']+)["\']', text)
        if m:
            return m.group(1).strip()
    except Exception as e:
        print(f"  [ERR] reading {path}: {e}")
    return None


def check_all(expected: str | None = None, verbose: bool = True) -> bool:
    """Check all sources against expected. Returns True if all PASS."""
    canonical = _read_pyproject_version()
    if expected is None:
        expected = canonical or EXPECTED_FALLBACK

    if verbose:
        print(f"Expected version: {expected}  (canonical pyproject.toml = {canonical})")
        print("=" * 60)

    all_ok = True

    # 1. pyproject.toml (canonica PEP440 sin v.)
    v = canonical
    no_v_prefix = not (v or "").lstrip().startswith("v")
    ok = (v == expected) and no_v_prefix
    status = "PASS" if ok else "FAIL"
    if verbose:
        extra = "" if no_v_prefix else " (has v prefix - should be canonical without v)"
        print(f"[{status}] pyproject.toml: {v!r} (expected {expected!r}){extra}")
    all_ok = all_ok and ok

    # 2. backend/config_manager.py
    v = _read_config_manager_version()
    ok = (v == expected)
    status = "PASS" if ok else "FAIL"
    if verbose:
        print(f"[{status}] backend/config_manager.py (app_version): {v!r} (expected {expected!r})")
    all_ok = all_ok and ok

    # 3. lang files (display v.{expected} required)
    for lang in ["es.json", "en.json"]:
        p = PROJECT_ROOT / "lang" / lang
        v = _read_lang_version(p)
        try:
            raw_title = json.loads(p.read_text(encoding="utf-8")).get("app_title", "")
        except Exception:
            raw_title = ""
        has_display = f"v.{expected}" in raw_title
        ok = (v == expected) and has_display
        status = "PASS" if ok else "FAIL"
        if verbose:
            extra = "" if has_display else " (missing display v.{})".format(expected)
            print(f"[{status}] lang/{lang} (app_title): {v!r} (expected {expected!r}){extra} raw={raw_title!r}")
        all_ok = all_ok and ok

    # 4. config version_info files
    for name in ["version_info.txt", "version_info_GENERAL.txt"]:
        p = PROJECT_ROOT / "config" / name
        info = _read_version_info(p)
        # PASS if all three extracted versions equal expected
        ok = all(val == expected for val in info.values() if val is not None) and info["filevers"] is not None
        if not ok:
            # Debug: show what was found
            pass
        status = "PASS" if ok else "FAIL"
        if verbose:
            print(f"[{status}] config/{name}: filevers={info['filevers']!r} FileVersion={info['FileVersion']!r} ProductVersion={info['ProductVersion']!r} (expected {expected!r})")
        all_ok = all_ok and ok

    # 5. scripts/build_GENERAL_v2.py
    p = PROJECT_ROOT / "scripts" / "build_GENERAL_v2.py"
    v = _read_build_version(p)
    ok = (v == expected)
    status = "PASS" if ok else "FAIL"
    if verbose:
        print(f"[{status}] scripts/build_GENERAL_v2.py (APP_VERSION): {v!r} (expected {expected!r})")
    all_ok = all_ok and ok

    if verbose:
        print("=" * 60)
        if all_ok:
            print("All version sources PASS.")
        else:
            print("Version check FAILED — sources diverge from expected.")
            print(f"Canonical source: pyproject.toml = {canonical!r}")

    return all_ok


def main():
    expected = sys.argv[1] if len(sys.argv) > 1 else None
    ok = check_all(expected=expected, verbose=True)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
