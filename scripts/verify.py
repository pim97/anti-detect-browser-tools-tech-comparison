#!/usr/bin/env python3
"""Re-verify every tool's published version and repository health.

The comparison in this repo goes stale the moment a tool ships a release, so the
version and project-health tables are generated rather than hand-written.

    python scripts/verify.py              # print the tables
    python scripts/verify.py --write      # also regenerate STATUS.md

Uses only the standard library. Set GITHUB_TOKEN to avoid the 60 req/hour
unauthenticated rate limit (the script needs ~25 GitHub calls).
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
UA = "anti-detect-browser-tools-tech-comparison/verify.py"
TIMEOUT = 30

# One entry per tool tracked by the report. `repos` lists every upstream repo we
# clone for source verification; `primary` is the one used for health metrics.
TOOLS = [
    {
        "name": "Camoufox",
        "primary": "daijro/camoufox",
        "repos": ["daijro/camoufox", "daijro/browserforge"],
        "pypi": ["camoufox"],
        "npm": [],
        "include_prereleases": True,
    },
    {
        "name": "Patchright",
        "primary": "Kaliiiiiiiiii-Vinyzu/patchright",
        "repos": [
            "Kaliiiiiiiiii-Vinyzu/patchright",
            "Kaliiiiiiiiii-Vinyzu/patchright-python",
            "Kaliiiiiiiiii-Vinyzu/patchright-nodejs",
            "Kaliiiiiiiiii-Vinyzu/CDP-Patches",
            "DevEnterpriseSoftware/patchright-dotnet",
        ],
        "pypi": ["patchright"],
        "npm": ["patchright"],
        "include_prereleases": False,
    },
    {
        "name": "SeleniumBase",
        "primary": "seleniumbase/SeleniumBase",
        "repos": ["seleniumbase/SeleniumBase"],
        "pypi": ["seleniumbase"],
        "npm": [],
        "include_prereleases": False,
    },
    {
        "name": "Botasaurus",
        "primary": "omkarcloud/botasaurus",
        "repos": ["omkarcloud/botasaurus", "omkarcloud/botasaurus-driver"],
        "pypi": ["botasaurus", "botasaurus-driver"],
        "npm": [],
        "include_prereleases": False,
    },
    {
        "name": "XDriver",
        "primary": "arjun-sha/XDriver",
        "repos": ["arjun-sha/XDriver", "rebrowser/rebrowser-patches"],
        "pypi": [],
        "npm": [],
        "include_prereleases": False,
    },
    {
        "name": "CloakBrowser",
        "primary": "CloakHQ/CloakBrowser",
        "repos": ["CloakHQ/CloakBrowser"],
        "pypi": ["cloakbrowser"],
        "npm": ["cloakbrowser"],
        "include_prereleases": True,
    },
    {
        "name": "Scrapling",
        "primary": "D4Vinci/Scrapling",
        "repos": ["D4Vinci/Scrapling"],
        "pypi": ["scrapling"],
        "npm": [],
        "include_prereleases": False,
    },
    {
        "name": "Obscura",
        "primary": "h4ckf0r0day/obscura",
        "repos": ["h4ckf0r0day/obscura", "h4ckf0r0day/obscura-benchmark"],
        "pypi": [],
        "npm": [],
        "include_prereleases": False,
    },
    {
        "name": "Clearcote",
        "primary": "clearcotelabs/clearcote-browser",
        "repos": ["clearcotelabs/clearcote-browser", "clearcotelabs/clearcote-profiles"],
        "pypi": ["clearcote"],
        "npm": ["clearcote"],
        "include_prereleases": True,
    },
]


def fetch_json(url: str, token: str | None = None) -> dict | list | None:
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    if token and "api.github.com" in url:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            return json.load(resp)
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, json.JSONDecodeError):
        return None


def pypi_version(pkg: str) -> str:
    data = fetch_json(f"https://pypi.org/pypi/{pkg}/json")
    if not isinstance(data, dict):
        return "—"
    version = data.get("info", {}).get("version", "?")
    files = data.get("releases", {}).get(version) or []
    date = files[0]["upload_time"][:10] if files else "?"
    return f"`{version}` ({date})"


def npm_version(pkg: str) -> str:
    data = fetch_json(f"https://registry.npmjs.org/{pkg}")
    if not isinstance(data, dict):
        return "—"
    latest = data.get("dist-tags", {}).get("latest", "?")
    date = (data.get("time", {}).get(latest) or "?")[:10]
    return f"`{latest}` ({date})"


def gh_repo(repo: str, token: str | None) -> dict:
    data = fetch_json(f"https://api.github.com/repos/{repo}", token)
    if not isinstance(data, dict) or "full_name" not in data:
        return {"repo": repo, "error": True}
    return {
        "repo": repo,
        "stars": data.get("stargazers_count", 0),
        "forks": data.get("forks_count", 0),
        "pushed": (data.get("pushed_at") or "?")[:10],
        "created": (data.get("created_at") or "?")[:10],
        "license": (data.get("license") or {}).get("spdx_id") or "none",
        "open_issues": data.get("open_issues_count", 0),
        "archived": data.get("archived", False),
        "error": False,
    }


def gh_release(repo: str, token: str | None, include_prereleases: bool) -> str:
    releases = fetch_json(f"https://api.github.com/repos/{repo}/releases?per_page=20", token)
    if not isinstance(releases, list) or not releases:
        return "— (no GitHub releases)"
    if not include_prereleases:
        releases = [r for r in releases if not r.get("prerelease")] or releases
    top = releases[0]
    tag = top.get("tag_name", "?")
    date = (top.get("published_at") or "?")[:10]
    flag = " *(pre)*" if top.get("prerelease") else ""
    return f"`{tag}` ({date}){flag}"


def gh_contributors(repo: str, token: str | None) -> str:
    """Distinct contributors, capped at 100 — a rough bus-factor signal."""
    data = fetch_json(
        f"https://api.github.com/repos/{repo}/contributors?per_page=100&anon=false", token
    )
    if not isinstance(data, list):
        return "?"
    return f"{len(data)}{'+' if len(data) >= 100 else ''}"


def collect(token: str | None) -> list[dict]:
    def one(tool: dict) -> dict:
        primary = tool["primary"]
        with ThreadPoolExecutor(max_workers=8) as pool:
            f_repo = pool.submit(gh_repo, primary, token)
            f_rel = pool.submit(gh_release, primary, token, tool["include_prereleases"])
            f_contrib = pool.submit(gh_contributors, primary, token)
            f_pypi = [(p, pool.submit(pypi_version, p)) for p in tool["pypi"]]
            f_npm = [(p, pool.submit(npm_version, p)) for p in tool["npm"]]
        return {
            **tool,
            "health": f_repo.result(),
            "release": f_rel.result(),
            "contributors": f_contrib.result(),
            "pypi_versions": [(p, f.result()) for p, f in f_pypi],
            "npm_versions": [(p, f.result()) for p, f in f_npm],
        }

    with ThreadPoolExecutor(max_workers=6) as pool:
        return list(pool.map(one, TOOLS))


def render(rows: list[dict], stamp: str) -> str:
    out: list[str] = []
    out.append("# Verified Status")
    out.append("")
    out.append(
        f"Generated by [`scripts/verify.py`](scripts/verify.py) on **{stamp}**. "
        "Every number below came from the package registry or the GitHub API at that "
        "moment — nothing here is hand-edited. Re-run the script to refresh it."
    )
    out.append("")
    out.append("```bash")
    out.append("python scripts/verify.py --write")
    out.append("```")
    out.append("")
    out.append("## Latest published versions")
    out.append("")
    out.append("| Tool | Latest GitHub release | Python package | npm package |")
    out.append("|------|----------------------|----------------|-------------|")
    for r in rows:
        pypi = "<br>".join(f"`{p}` {v}" for p, v in r["pypi_versions"]) or "—"
        npm = "<br>".join(f"`{p}` {v}" for p, v in r["npm_versions"]) or "—"
        out.append(f"| **{r['name']}** | {r['release']} | {pypi} | {npm} |")
    out.append("")
    out.append("## Project health")
    out.append("")
    out.append(
        "Stars measure popularity, not stealth. The columns that matter for a build "
        "decision are **License** (can you ship it commercially), **Last push** (is "
        "anyone home), and **Contributors** (what happens if the maintainer stops)."
    )
    out.append("")
    out.append(
        "| Tool | Primary repo | License | Last push | Stars | Forks | Contributors | Open issues |"
    )
    out.append(
        "|------|--------------|---------|-----------|------:|------:|-------------:|------------:|"
    )
    for r in rows:
        h = r["health"]
        if h.get("error"):
            out.append(f"| **{r['name']}** | `{h['repo']}` | ? | ? | ? | ? | ? | ? |")
            continue
        archived = " ⚠️ archived" if h["archived"] else ""
        out.append(
            f"| **{r['name']}** | [`{h['repo']}`](https://github.com/{h['repo']}) "
            f"| {h['license']} | {h['pushed']}{archived} | {h['stars']:,} | {h['forks']:,} "
            f"| {r['contributors']} | {h['open_issues']} |"
        )
    out.append("")
    out.append("## Repos cloned for source verification")
    out.append("")
    out.append(
        "Claims marked **Tier A** in the report were read from this code. The trees are "
        "unaudited third-party projects, so they are cloned into a hardened, "
        "network-severed Docker sandbox by [`scripts/sandbox.sh`](scripts/sandbox.sh) — "
        "never onto a workstation. See [METHODOLOGY.md](METHODOLOGY.md#source-handling)."
    )
    out.append("")
    for r in rows:
        repos = " · ".join(f"[`{x}`](https://github.com/{x})" for x in r["repos"])
        out.append(f"- **{r['name']}** — {repos}")
    out.append("")
    return "\n".join(out)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--write", action="store_true", help="regenerate STATUS.md")
    args = ap.parse_args()

    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if not token:
        print("note: no GITHUB_TOKEN set — may hit the 60 req/hour limit\n", file=sys.stderr)

    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    rows = collect(token)
    # Preserve the declaration order in TOOLS regardless of completion order.
    order = {t["name"]: i for i, t in enumerate(TOOLS)}
    rows.sort(key=lambda r: order[r["name"]])

    text = render(rows, stamp)
    print(text)

    if args.write:
        target = REPO_ROOT / "STATUS.md"
        target.write_text(text, encoding="utf-8")
        print(f"\nwrote {target}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
