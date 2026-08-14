#!/usr/bin/env python3
"""Code-quality metrics across the sandboxed tool trees. Emits JSON on stdout.

Run it inside the sandbox created by scripts/sandbox.sh, which is where the source
trees live (they are never cloned onto a workstation):

    ssh <box> 'docker exec -i antidetect-box python3 -' < scripts/codemetrics.py

Files are read as text only; no project code is imported or executed.

Counting rules that make the numbers comparable:
  * vendored and generated trees are excluded (node_modules, bundles, dist, target,
    vendor, third_party, minified JS, lockfiles, vendored json.hpp, .patch files);
  * test files are excluded from production counts and reported separately.

Both rules matter. An earlier revision applied the exclusions to the line counts but
not to the pattern searches, which reported 116 `eval` calls in a 304-line project
because it was scanning a vendored bundle.
"""
import json
import os
import subprocess
from pathlib import Path

SRC = Path("/src")

TOOLS = {
    "Camoufox": ["camoufox"],
    "Patchright": ["patchright", "patchright-python"],
    "SeleniumBase": ["SeleniumBase"],
    "Botasaurus": ["botasaurus", "botasaurus-driver"],
    "XDriver": ["XDriver"],
    "CloakBrowser": ["CloakBrowser"],
    "Scrapling": ["Scrapling"],
    "Obscura": ["obscura"],
    "Clearcote": ["clearcote-browser"],
}

EXCLUDE = ["!.git", "!node_modules", "!bundles", "!dist", "!build", "!target",
           "!__pycache__", "!.venv", "!venv", "!vendor", "!third_party",
           "!*.min.js", "!package-lock.json", "!json.hpp", "!*.patch"]
TESTGLOBS = ["tests", "test", "*_test.*", "test_*.*", "*.test.*", "spec"]


def rg(pattern, root, extra=None, only_tests=False, exclude_tests=False):
    cmd = ["rg", "--no-messages", "-c", "-e", pattern, str(root)]
    for g in EXCLUDE:
        cmd += ["--glob", g]
    if exclude_tests:
        for t in TESTGLOBS:
            cmd += ["--glob", f"!{t}"]
    if only_tests:
        cmd += ["--glob", "tests/**"]
    if extra:
        cmd += extra
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=180).stdout
        return sum(int(l.rsplit(":", 1)[1]) for l in out.strip().split("\n") if ":" in l)
    except Exception:
        return 0


def loc(root, exts, exclude_tests=True):
    """Line count over first-party source of the given extensions."""
    cmd = ["rg", "--no-messages", "--stats", "-c", "-e", r"^", str(root)]
    for g in EXCLUDE:
        cmd += ["--glob", g]
    for e in exts:
        cmd += ["--glob", f"*.{e}"]
    if exclude_tests:
        for t in TESTGLOBS:
            cmd += ["--glob", f"!{t}"]
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=180).stdout
        return sum(int(l.rsplit(":", 1)[1]) for l in out.strip().split("\n") if ":" in l)
    except Exception:
        return 0


def count_test_files(root):
    cmd = ["rg", "--no-messages", "--files", str(root)]
    for g in EXCLUDE:
        cmd += ["--glob", g]
    try:
        files = subprocess.run(cmd, capture_output=True, text=True, timeout=180).stdout.split("\n")
    except Exception:
        return 0, []
    hits = [f for f in files if f and (
        "/tests/" in f or "/test/" in f
        or os.path.basename(f).startswith("test_")
        or os.path.basename(f).rsplit(".", 1)[0].endswith("_test")
        or ".test." in os.path.basename(f)
        or "/spec/" in f)]
    return len(hits), hits[:3]


EXTS = ["py", "js", "ts", "rs", "cc", "cpp", "h", "hpp", "cs"]
out = {}
for tool, repos in TOOLS.items():
    entry = []
    for rp in repos:
        root = SRC / rp
        if not root.exists():
            continue
        prod = loc(root, EXTS, exclude_tests=True)
        tf, sample = count_test_files(root)
        e = {
            "repo": rp,
            "prod_loc": prod,
            "test_files": tf,
            "test_sample": sample,
            "smells": {
                "bare_except": rg(r"except\s*:", root, exclude_tests=True),
                "broad_except": rg(r"except\s+(Exception|BaseException)\s*[:,]", root, exclude_tests=True),
                "todo": rg(r"\b(TODO|FIXME|HACK|XXX)\b", root, exclude_tests=True),
                "print": rg(r"^\s*print\(", root, exclude_tests=True),
                "sleep": rg(r"\b(time\.sleep|asyncio\.sleep)\s*\(", root, exclude_tests=True),
            },
            "security": {
                "shell_true": rg(r"shell\s*=\s*True", root, exclude_tests=True),
                "eval_exec": rg(r"(?<![\w.])(eval|exec)\s*\(", root, exclude_tests=True),
                "pickle": rg(r"\bpickle\.(load|loads)\b", root, exclude_tests=True),
                "verify_false": rg(r"verify\s*=\s*False|rejectUnauthorized\s*:\s*false", root, exclude_tests=True),
                "no_sandbox": rg(r"--no-sandbox", root, exclude_tests=True),
                "unsafe_rust": rg(r"\bunsafe\s*\{", root, exclude_tests=True),
                "unwrap_prod": rg(r"\.unwrap\(\)", root, exclude_tests=True),
                "panic": rg(r"\bpanic!\(", root, exclude_tests=True),
            },
        }
        entry.append(e)
    out[tool] = entry
print(json.dumps(out))
