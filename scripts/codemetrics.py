#!/usr/bin/env python3
"""Code-quality metrics across the sandboxed tool trees. Emits JSON on stdout.

Run it inside the sandbox created by scripts/sandbox.sh, which is where the source
trees live (they are never cloned onto a workstation):

    ssh <box> 'docker exec -i antidetect-box python3 -' < scripts/codemetrics.py

Every number in the CODE-REVIEW.md metrics tables comes from this script. To run it
against an older snapshot (e.g. `git archive <sha> | tar -x` into /src/_old/<repo>),
pass `-e METRICS_SRC=/src/_old` to `docker exec`.

Files are read as text only (Python through `ast.parse`); no project code is imported
or executed.

Counting rules that make the numbers comparable:
  * vendored and generated trees are excluded (node_modules, bundles, dist, target,
    vendor, third_party, minified JS, lockfiles, vendored json.hpp, .patch files);
  * test files are excluded from production counts and reported separately;
  * Rust items gated by #[cfg(test)] are stripped before the Rust-only counts
    (`unsafe`, `.unwrap()`, `panic!`), because Rust unit tests live inline.

Both rules matter. An earlier revision applied the exclusions to the line counts but
not to the pattern searches, which reported 116 `eval` calls in a 304-line project
because it was scanning a vendored bundle.
"""
import ast
import json
import os
import re
import subprocess
import warnings
from pathlib import Path

# ast.parse on third-party files emits SyntaxWarnings (invalid escapes) on stderr.
warnings.filterwarnings("ignore", category=SyntaxWarning)

SRC = Path(os.environ.get("METRICS_SRC", "/src"))

TOOLS = {
    "Camoufox": ["camoufox"],
    "Patchright": ["patchright", "patchright-python"],
    "SeleniumBase": ["SeleniumBase"],
    "Botasaurus": ["botasaurus", "botasaurus-driver"],
    "XDriver": ["XDriver"],
    "CloakBrowser": ["CloakBrowser"],
    "Scrapling": ["Scrapling"],
    "Obscura": ["obscura"],
    "invisible_playwright": ["invisible_playwright", "invisible_core"],
    "Clearcote": ["clearcote-browser"],
}

EXCLUDE = ["!.git", "!node_modules", "!bundles", "!dist", "!build", "!target",
           "!__pycache__", "!.venv", "!venv", "!vendor", "!third_party",
           "!*.min.js", "!package-lock.json", "!json.hpp", "!*.patch",
           # invisible_playwright vendors a Playwright-Python fork in _pw/ (see its
           # THIRD_PARTY_FORK.md) and ships an esbuild bundle of Playwright's
           # injectedScript.ts as _juggler/injected.js.
           "!_pw", "!**/_juggler/injected.js"]
TESTGLOBS = ["tests", "test", "*_test.*", "test_*.*", "*.test.*", "spec"]
EXTS = ["py", "js", "ts", "rs", "cc", "cpp", "h", "hpp", "cs"]


def run(cmd):
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=180).stdout
    except Exception:
        return ""


def per_file_counts(out):
    """Parse `rg -c` output into {path: count}."""
    counts = {}
    for line in out.strip().split("\n"):
        if ":" in line:
            path, n = line.rsplit(":", 1)
            try:
                counts[path] = int(n)
            except ValueError:
                pass
    return counts


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
    return sum(per_file_counts(run(cmd)).values())


def line_counts(root, exts, exclude_tests=True):
    """Per-file line counts over first-party source of the given extensions."""
    cmd = ["rg", "--no-messages", "-c", "-e", r"^", str(root)]
    # ripgrep gives the LAST matching glob precedence, so the extension includes go
    # first. With the excludes first, `*.hpp` re-included json.hpp and `*.js`
    # re-included minified bundles.
    for e in exts:
        cmd += ["--glob", f"*.{e}"]
    for g in EXCLUDE:
        cmd += ["--glob", g]
    if exclude_tests:
        for t in TESTGLOBS:
            cmd += ["--glob", f"!{t}"]
    return per_file_counts(run(cmd))


def loc(root, exts, exclude_tests=True):
    """Line count over first-party source of the given extensions."""
    return sum(line_counts(root, exts, exclude_tests).values())


def is_test_path(f):
    base = os.path.basename(f)
    return ("/tests/" in f or "/test/" in f or base.startswith("test_")
            or base.rsplit(".", 1)[0].endswith("_test") or ".test." in base
            or "/spec/" in f)


def list_files(root, hidden=False):
    cmd = ["rg", "--no-messages", "--files", str(root)]
    if hidden:
        cmd.insert(2, "--hidden")
    for g in EXCLUDE:
        cmd += ["--glob", g]
    return [f for f in run(cmd).split("\n") if f]


def count_test_files(root):
    hits = [f for f in list_files(root) if is_test_path(f)]
    return len(hits), hits[:3]


def test_loc(root):
    """Lines in test files (same path rule as count_test_files), source extensions only."""
    return sum(n for f, n in line_counts(root, EXTS, exclude_tests=False).items()
               if is_test_path(f))


def largest_file(root):
    counts = line_counts(root, EXTS, exclude_tests=True)
    if not counts:
        return None
    path, n = max(counts.items(), key=lambda kv: kv[1])
    return {"path": os.path.relpath(path, root), "lines": n}


# #[cfg(test)], #[cfg(all(test, feature = ...))], and #[test] / #[tokio::test] functions.
CFG_TEST = re.compile(r"#\[cfg\((?:all\()?test\b[^\]]*\]|#\[(?:tokio::)?test\]")
RUST_PATTERNS = {
    "unsafe_rust": re.compile(r"\bunsafe\s*\{"),
    "unwrap_prod": re.compile(r"\.unwrap\(\)"),
    "panic": re.compile(r"\bpanic!\("),
}


def strip_rust_tests(text):
    """Drop test-gated items (usually an inline `mod tests { ... }`) by brace
    matching. Rust keeps unit tests in the same file as the code, so a path-based test
    filter alone counts them as production."""
    out, i = [], 0
    while True:
        m = CFG_TEST.search(text, i)
        if not m:
            out.append(text[i:])
            return "".join(out)
        out.append(text[i:m.start()])
        brace = text.find("{", m.end())
        semi = text.find(";", m.end())
        if brace == -1 or (semi != -1 and semi < brace):  # e.g. `#[cfg(test)] mod tests;`
            i = semi + 1 if semi != -1 else len(text)
            continue
        depth, k = 0, brace
        while k < len(text):
            if text[k] == "{":
                depth += 1
            elif text[k] == "}":
                depth -= 1
                if depth == 0:
                    break
            k += 1
        i = k + 1


def rust_counts(root):
    """Matching lines (as `rg -c` counts them) in non-test Rust, test items stripped."""
    counts = dict.fromkeys(RUST_PATTERNS, 0)
    for f in list_files(root):
        if not f.endswith(".rs") or is_test_path(f) or os.path.basename(f) == "tests.rs":
            continue
        text = strip_rust_tests(Path(f).read_text(encoding="utf-8", errors="replace"))
        for line in text.split("\n"):
            for k, pat in RUST_PATTERNS.items():
                if pat.search(line):
                    counts[k] += 1
    return counts


def python_typing(root):
    """AST over non-test Python: a function counts as annotated if any parameter or
    the return carries an annotation."""
    files = [f for f in list_files(root) if f.endswith(".py") and not is_test_path(f)]
    total = annotated = documented = 0
    for f in files:
        try:
            tree = ast.parse(Path(f).read_text(encoding="utf-8", errors="replace"))
        except (SyntaxError, ValueError):
            continue
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            total += 1
            a = node.args
            params = a.posonlyargs + a.args + a.kwonlyargs + [x for x in (a.vararg, a.kwarg) if x]
            if node.returns is not None or any(p.annotation is not None for p in params):
                annotated += 1
            if ast.get_docstring(node) is not None:
                documented += 1
    if not total:
        return None
    return {"functions": total,
            "annotated_pct": round(100 * annotated / total, 1),
            "docstring_pct": round(100 * documented / total, 1)}


def hygiene(root):
    wf = root / ".github" / "workflows"
    workflows = len([p for p in wf.iterdir() if p.suffix in (".yml", ".yaml")]) if wf.is_dir() else 0
    rel = [os.path.relpath(f, root) for f in list_files(root, hidden=True)]
    # Community files count at the repo root, in .github/ or in docs/.
    top = [os.path.basename(r).lower() for r in rel
           if "/" not in r or r.startswith((".github/", "docs/")) and r.count("/") == 1]

    def has(*prefixes):
        return any(b.startswith(prefixes) for b in top)

    return {
        "ci_workflows": workflows,
        "py_typed": any(os.path.basename(r) == "py.typed" for r in rel),
        "pre_commit": (root / ".pre-commit-config.yaml").exists(),
        "dependabot": any((root / ".github" / n).exists() for n in ("dependabot.yml", "dependabot.yaml")),
        "contributing": has("contributing"),
        "security_md": has("security"),
        "changelog": has("changelog"),
    }


out = {}
for tool, repos in TOOLS.items():
    entry = []
    for rp in repos:
        root = SRC / rp
        if not root.exists():
            continue
        prod = loc(root, EXTS, exclude_tests=True)
        tf, sample = count_test_files(root)
        rc = rust_counts(root)
        e = {
            "repo": rp,
            "prod_loc": prod,
            "test_files": tf,
            "test_sample": sample,
            "test_loc": test_loc(root),
            "largest_file": largest_file(root),
            "py": python_typing(root),
            "hygiene": hygiene(root),
            "smells": {
                "bare_except": rg(r"except\s*:", root, exclude_tests=True),
                "broad_except": rg(r"except\s+(Exception|BaseException)\s*[:,]", root, exclude_tests=True),
                "todo": rg(r"\b(TODO|FIXME|HACK|XXX)\b", root, exclude_tests=True),
                "print": rg(r"^\s*print\(", root, exclude_tests=True),
                "sleep": rg(r"\b(time\.sleep|asyncio\.sleep)\s*\(", root, exclude_tests=True),
            },
            "security": {
                "shell_true": rg(r"shell\s*=\s*True", root, exclude_tests=True),
                # Lookbehind needs PCRE2; without -P ripgrep rejects the pattern and
                # this silently counted 0 for every repo.
                "eval_exec": rg(r"(?<![\w.])(eval|exec)\s*\(", root, extra=["-P"], exclude_tests=True),
                "pickle": rg(r"\bpickle\.(load|loads)\b", root, exclude_tests=True),
                "verify_false": rg(r"verify\s*=\s*False|rejectUnauthorized\s*:\s*false", root, exclude_tests=True),
                "no_sandbox": rg(r"--no-sandbox", root, exclude_tests=True),
                "unsafe_rust": rc["unsafe_rust"],
                "unwrap_prod": rc["unwrap_prod"],
                "panic": rc["panic"],
            },
        }
        entry.append(e)
    out[tool] = entry
print(json.dumps(out))
