# XDriver - Technical Analysis

> **Repository:** [arjun-sha/XDriver](https://github.com/arjun-sha/XDriver) *(the old `nicebots-xyz/x_driver` URL now 404s)*
> **Category:** Playwright Driver Patcher (rebrowser-patches derivative)
> **Language:** Python (CLI) + bundled JavaScript (patched `playwright-core`)
> **Type:** File-replacement patching of the local Playwright driver
> **Version:** v1.0.1 (released 2025-09-10) — **unchanged as of 2026-08-14**
> **What is verified:** the bundled "patched" driver identifies itself as `turnstilebrowser-playwright-core` **1.49.0**; XDriver's own Python is ~295 lines doing file backup/replace and version validation, with no browser-patching logic of its own (**Tier A**)
> **Anti-bot service claims:** the README claims **Cloudflare WAF, Turnstile, DataDome, Kasada** and "undetectable even against vendors like Kasada" (**Tier B**). The claims are dated September 2025 and describe a bundle pinned to `playwright-core` 1.49.0; no re-test has been published since.
> **Maintenance:** No commits since 2025-09-10 (~11 months before the verification date). 5 stars, 4 forks, 2 contributors, no PyPI package. Apache-2.0.
> **Verified:** 2026-08-14 against `arjun-sha/XDriver` @ `b610852`.

> ### Status
>
> XDriver repackages a [rebrowser-patches](https://github.com/rebrowser/rebrowser-patches)-lineage
> `playwright-core` fork. Its last commit is 2025-09-10 and its bundle targets
> `playwright-core` 1.49.0, against a current Playwright of 1.61.x.
> [Patchright](./patchright.md) implements the same `Runtime.enable` countermeasure and
> tracks Playwright releases automatically. This page documents XDriver because it
> still appears in tool recommendations.

---

## Overview

XDriver is a stealth patching tool that swaps out the JavaScript files inside a locally installed Playwright's `driver/package` directory with a pre-patched copy, then prints an "XDriver Session Active" banner from Playwright's `__init__.py`. Unlike script-injection approaches, it replaces Playwright's bundled Node driver payload with a hardened build.

**What it actually ships (verified from source):** the bundled "patched" driver is **not original work**. `x_driver/bundles/package/package.json` identifies it as `turnstilebrowser-playwright-core` v1.49.0 — a `playwright-core` fork carrying the `turnstilebrowser-patches` set (a [rebrowser-patches](https://github.com/rebrowser/rebrowser-patches) lineage). Every stealth modification in the bundle is gated behind `TURNSTILEBROWSER_PATCHES_*` environment variables. XDriver's own Python code (295 lines across `x_driver/*.py`, excluding the bundle) only does file backup/replace and version validation; it contains no browser-patching logic of its own.

## Technical summary

| Property | Verified state |
|---|---|
| **Original code** | ~295 lines of Python performing file backup, file replacement, and version validation. No browser-patching logic. **Tier A** |
| **Shipped bundle** | `turnstilebrowser-playwright-core` 1.49.0 — a prebuilt `playwright-core` fork of [rebrowser-patches](https://github.com/rebrowser/rebrowser-patches) lineage. Not built from sources published in this repository. **Tier A** |
| **`Runtime.enable` tell** | Addressed by the bundle, gated behind `TURNSTILEBROWSER_PATCHES_*` environment variables. Implementation is upstream, not this project's. **Tier A** |
| **Fingerprint spoofing** | None in source. **Tier A** |
| **Input simulation** | None. The only matches for Bézier/humanize strings are in bundled Playwright vendor assets (`codeMirrorModule`, `zipBundleImpl`). **Tier A** |
| **Pinned Playwright version** | 1.49.0. Current Playwright at the verification date is 1.61.x |
| **Commit activity** | Last commit 2025-09-10, approximately 11 months before the verification date |
| **Distribution** | No PyPI package |
| **Project state** | 5 stars, 4 forks, 2 contributors, 0 open issues |
| **Documented claims vs. source** | The README claims Kasada, DataDome, PerimeterX, Imperva, and Fingerprint.com coverage. No code addressing any of them exists in the repository |

Functional overlap: [Patchright](./patchright.md) implements the same `Runtime.enable`
countermeasure, tracks Playwright releases automatically, and was last pushed
2026-08-05.

---

## How It Works - Technical Deep Dive

### The Real Mechanism (verified in `x_driver/activator_script.py`)

XDriver does **not** inject scripts or wrap APIs at runtime. On `x_driver activate` it:

1. Renames the existing `playwright/driver/package` → `package_1` (backup).
2. `shutil.copytree`s its own `x_driver/bundles/package` into `playwright/driver/package`.
3. Prepends a green `[-] XDriver INFO: Session Active` `print(...)` line to `playwright/__init__.py`.

That is the entire patch. Notably, the Node binary swap is **commented out** in the source (`# os.rename(NODE_PATH, ...)` / `# shutil.copy2(PATCH_NODE, ...)`), so only the JS driver payload is replaced. The `x_driver/bundles/node` file is a **82 MB Git-LFS pointer**, not a real binary, and is never installed.

```
Original Playwright:
playwright/
├── driver/
│   └── package/           ← Upstream playwright-core (1.52.0)
│       └── lib/server/... (compiled JS)
└── __init__.py

After `x_driver activate`:
playwright/
├── driver/
│   ├── package/           ← REPLACED with turnstilebrowser-playwright-core 1.49.0
│   │   └── lib/server/... (6 files carry TURNSTILEBROWSER_PATCHES_*)
│   └── package_1/         ← Backup of original
└── __init__.py            ← 1 print() line prepended
```

> **⚠️ Version mismatch (verified):** `x_driver/utils.py` and `rolling.yml` require the *host* `playwright==1.52.0`, but the bundled replacement `package.json` declares `"version": "1.49.0"`. Activation copies the 1.49.0 driver over a 1.52.0 install. In practice the patched `playwright-core` still functions because the Python client talks to the driver over the wire protocol, but the version pin is cosmetic/inconsistent, and `--force` bypasses the check entirely.

### What the Bundled Driver Actually Patches

Grepping the bundle, exactly **6 JavaScript files** (out of 282 in `lib/`) carry the `turnstilebrowser-patches` changes:

| File | Patch |
|------|-------|
| `lib/server/chromium/crConnection.js` | Utility-world binding setup (`RUNTIME_FIX_MODE`, `UTILITY_WORLD_NAME`, `getIsolatedWorld`) |
| `lib/server/chromium/crPage.js` | Isolated-world execution context handling gated on `RUNTIME_FIX_MODE` |
| `lib/server/chromium/crServiceWorker.js` | Conditionally skips `Runtime.enable` for service workers |
| `lib/server/chromium/crDevTools.js` | `Runtime.enable` behavior gated on `RUNTIME_FIX_MODE` |
| `lib/server/page.js` | Execution-context creation path for the fix |
| `lib/server/frames.js` | World/context resolution for the isolated utility world |

The central technique is the **Runtime.enable leak fix**, the same well-known evasion popularized by rebrowser-patches: instead of calling `Runtime.enable` (which lets detectors observe a CDP-controlled execution context), the driver creates an isolated world via `Page.createIsolatedWorld` and adds bindings there.

#### A. Runtime.enable Leak Fix (`crConnection.js`)

The real, verified code (paraphrased from the bundle) is env-var driven, not the hand-written `_shouldHideMessage`/`PatchedTransport` class the previous version of this page showed (that code does not exist):

```javascript
// x_driver/bundles/package/lib/server/chromium/crConnection.js
const fixMode = process.env['TURNSTILEBROWSER_PATCHES_RUNTIME_FIX_MODE'] || 'addBinding';
const utilityWorldName =
  process.env['TURNSTILEBROWSER_PATCHES_UTILITY_WORLD_NAME'] !== '0'
    ? process.env['TURNSTILEBROWSER_PATCHES_UTILITY_WORLD_NAME'] || 'util'
    : '__playwright_utility_world__';

if (fixMode === 'addBinding') {
  await client.send('Runtime.addBinding', { name: '...', /* worldName: utilityWorldName */ });
}
// getIsolatedWorld(): Page.createIsolatedWorld({ worldName }) → returns executionContextId
```

Default behavior (no env vars set): `RUNTIME_FIX_MODE = 'addBinding'` and the utility world is renamed to `util`. Setting `RUNTIME_FIX_MODE='0'` reverts to stock (leaky) Playwright behavior — you can see the `=== '0'` guards throughout the six files.

#### B. Service Worker Runtime Isolation (`crServiceWorker.js`)

```javascript
// Only call Runtime.enable for workers when the fix is disabled:
if (process.env['TURNSTILEBROWSER_PATCHES_RUNTIME_FIX_MODE'] === '0') {
  session.send('Runtime.enable', {}).catch(e => {});
}
```

This is the real basis for the README's "runs in an isolated Service Worker scope" line — it does not *block* service workers (the previous page's `_blockServiceWorkers`/`navigator.serviceWorker.register` override does **not** exist in the source).

#### C. What Is NOT in the Source (claims that don't hold up)

The following, claimed in the README and/or the prior version of this page, have **no corresponding code** in the repository:

- **"Stealth-hardened … at C-level" / C++ patches** — there is no C/C++ in the repo; the patches are pure JavaScript in `playwright-core`, and the browser binary itself is stock Chromium.
- **WebRTC Leak Protection** — no ICE-candidate / `.local` filtering, no `RTCPeerConnection` override anywhere in the tree.
- **Script-marker scrubbing** (`_removePlaywrightMarkers`, `__pwInitScripts` string-replacement) — not present; the isolated-world approach is what hides the init-script context, not string rewriting.
- **Binding name obfuscation** (`_obfuscateName` / random binding names) — not present.
- **Behavioral / mouse patches** — `crInput.js` is unmodified (0 patch markers); there is no human-movement layer.

---

## Architecture

```
XDriver Patching Flow (verified):
┌────────────────────────────────────────────────────────┐
│  pip install git+https://github.com/arjun-sha/XDriver  │
│               .git@v1.0.1                              │
│  (NOTE: not on PyPI — git install only)                │
└────────────────────────────────────────────────────────┘
                          ↓
┌────────────────────────────────────────────────────────┐
│  x_driver activate   [--force to skip version check]   │
│  ┌──────────────────────────────────────────────────┐ │
│  │ 1. validate_playwright(): require ==1.52.0       │ │
│  │ 2. rename driver/package → driver/package_1      │ │
│  │ 3. copytree bundles/package → driver/package     │ │
│  │    (= turnstilebrowser-playwright-core 1.49.0)   │ │
│  │ 4. prepend banner print() to __init__.py         │ │
│  │    (node binary swap is COMMENTED OUT)           │ │
│  └──────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────┘
                          ↓
┌────────────────────────────────────────────────────────┐
│  from playwright.async_api import async_playwright     │
│  # Patched driver runs the Runtime.enable-leak fix     │
│  # (TURNSTILEBROWSER_PATCHES_RUNTIME_FIX_MODE default) │
└────────────────────────────────────────────────────────┘
                          ↓
┌────────────────────────────────────────────────────────┐
│  x_driver deactivate                                   │
│  # rmtree package; rename package_1 → package          │
│  # strip banner line from __init__.py                  │
└────────────────────────────────────────────────────────┘
```

---

## Documented claims versus source

> **Every row below is a vendor claim from September 2025** (README "Performance"
> table), never independently benchmarked, about a bundle pinned to `playwright-core`
> 1.49.0 that has received no updates in ~11 months. **Tier B, and decaying.**
>
> Two structural reasons to discount them heavily:
>
> 1. **The mechanism doesn't reach most of these.** The entire evasion is one
>    `Runtime.enable` leak fix over stock Chromium — no fingerprint spoofing, no TLS
>    work, no behavioural layer (verified: XDriver's own Python is ~295 lines of file
>    backup/replace). A single protocol-level fix cannot plausibly account for defeating
>    fingerprint- and behaviour-driven systems.
> 2. **Anti-bot claims decay.** Even if each was true when published, an unmaintained
>    stealth patch loses ground continuously. Nothing here has been re-tested since.
>
> Where the technique genuinely works is the rebrowser bot-detector — its designed
> target — and that result is inherited from
> [rebrowser-patches](https://github.com/rebrowser/rebrowser-patches), not original.

| Service | README claims | What the source actually supports |
|---------|:-------------:|-----------------------------------|
| Cloudflare WAF / Turnstile | claimed pass | Plausible for the interstitial/WAF via the `Runtime.enable` fix; **no CAPTCHA-solving code exists** |
| Kasada | claimed pass | No Kasada-specific code. Claim rests entirely on the leak fix + your IP |
| DataDome | claimed pass | No DataDome-specific code |
| PerimeterX | claimed pass | No behavioural layer, which is what PerimeterX primarily scores |
| Imperva | claimed pass | Nothing specific in source |
| Fingerprint.com | claimed pass | **No fingerprint spoofing in source at all** — the least supportable claim in the table |

### Detector test results (README claims, Sept 2025, unverified)

| Test | Claimed result | Comment |
|------|----------------|---------|
| Rebrowser Bot Detector | Passed all tests | The detector this technique targets; the implementation is rebrowser-patches upstream |
| CreepJS | "100% Anonymous" | CreepJS is a consistency auditor, not an anti-bot; the phrasing does not correspond to a CreepJS output field |
| BrowserScan | 87% | No methodology or date given |
| Whoer.net | High Anonymity | No methodology or date given |
| AmIUnique | No unique fingerprint | No methodology or date given |
| Cover Your Tracks (EFF) | Strong protection | No methodology or date given |
| TLS Fingerprint (browserleaks) | "No anomalies" | Consistent with stock Chromium TLS; the repository contains no TLS impersonation code, so this reflects Chrome's own signature rather than a project feature |

> The TLS and WebRTC rows are the clearest tells that the README's table is aspirational: **neither TLS impersonation nor WebRTC filtering exists in the source.** Stock Chromium TLS "having no anomalies" is true because it *is* a real browser, not because XDriver does anything.

---

## Usage

### Installation & Activation
```bash
# NOT on PyPI — install straight from GitHub:
pip install git+https://github.com/arjun-sha/XDriver.git@v1.0.1

# Windows only, before installing:
set PYTHONUTF8=1

pip install playwright==1.52.0   # required by the version check
playwright install chromium

# Activate patching
x_driver activate                # add --force to skip the version check
```

### Basic Usage (No Code Changes)
```python
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        await page.goto("https://bot-detector.rebrowser.net/")  # its actual target
        await browser.close()

import asyncio
asyncio.run(main())
```

Optional tuning (from the bundled patch set — undocumented in XDriver's README):
```bash
export TURNSTILEBROWSER_PATCHES_RUNTIME_FIX_MODE=addBinding   # default; '0' = disable fix
export TURNSTILEBROWSER_PATCHES_UTILITY_WORLD_NAME=util       # default; '0' = legacy name
```

### Deactivation
```bash
x_driver deactivate  # restores original Playwright from package_1 backup
```

---

## Pros and Cons

### Advantages

| Advantage | Details |
|-----------|---------|
| **One-Command Activation** | `x_driver activate` — done, no code changes |
| **Reversible** | `deactivate` restores from the `package_1` backup |
| **Real Runtime.enable fix** | The bundled rebrowser/turnstilebrowser patch genuinely closes the Runtime.enable leak |
| **Transparent** | Existing Playwright scripts run unchanged |
| **Open Source** | Apache-2.0 (the wrapper); bundled core is the turnstilebrowser fork |

### Limitations

| Limitation | Details |
|------------|---------|
| **Not original stealth** | Bundles `turnstilebrowser-playwright-core` 1.49.0; XDriver adds only a copy/backup CLI |
| **No PyPI package** | `x-driver`/`x_driver` 404 on PyPI; the README's PyPI badge is fake (v0.0.1, links nowhere). Git install only |
| **Overstated README** | "C-level," WebRTC protection, marker scrubbing, binding obfuscation — none exist in the source |
| **Version mismatch** | Requires host `playwright==1.52.0` but ships a 1.49.0 driver |
| **Version-locked** | Hard-pinned to `["1.52.0"]`; `--force` needed for anything else |
| **Dormant** | No commits since 2025-09-10; single author; 5 stars / 4 forks |
| **Chromium only** | No Firefox/WebKit stealth |
| **No fingerprint/behavior layer** | No canvas/WebGL/screen spoofing, no mouse/timing simulation |
| **Empty examples** | `examples/playwright_async.py` and `playwright_sync.py` are 0-byte files (still, as of v1.0.1) |
| **Backup dependency** | A corrupted/lost `package_1` means manual recovery |
| **LFS node stub** | `bundles/node` is an 82 MB LFS pointer that is never actually installed (swap is commented out) |

---

## Comparison with Patchright

Both are rebrowser-patches-lineage Runtime.enable-leak fixes for Playwright. The practical difference is packaging and upkeep.

| Feature | XDriver | Patchright |
|---------|:-------:|:----------:|
| **Underlying technique** | rebrowser/turnstilebrowser Runtime.enable fix | rebrowser-lineage Runtime.enable fix |
| **Patching approach** | Copies a pre-patched `playwright-core` over your install | Ships as a separate patched package you import |
| **Installation** | `pip install git+…` (no PyPI) + `activate` | `pip install patchright` (real PyPI/npm) |
| **Version flexibility** | Hard-locked to 1.52.0 (bundle is 1.49.0) | Tracks Playwright releases |
| **Reversibility** | `deactivate` restores backup | N/A (separate package) |
| **Code changes** | None (patches your real Playwright) | Import from `patchright` instead |
| **Maintenance** | Dormant since 2025-09, single author | Actively maintained community |
| **Maturity** | v1.0.1, 5 stars | Established, widely used |
| **Multi-Language** | Python only | Python, Node.js, .NET |

### When to Choose XDriver over Patchright

**Choose XDriver only if:**
- You specifically want to patch your *existing* `playwright==1.52.0` install in place with no import changes and easy on/off switching.

**Choose Patchright (recommended for almost everyone) if:**
- You want a maintained package, real registry distribution, version flexibility, or Node.js / .NET support. Patchright delivers the same core evasion without the dormancy and the git-only install.

---

## When to Use XDriver

### Best For:
- Quick, throwaway testing of the Runtime.enable-leak fix against the rebrowser bot-detector **without touching your imports**
- Existing `playwright==1.52.0` codebases where you want a one-command on/off toggle

### Not Ideal For:
- Anything production (dormant, no PyPI, version-locked, bundle/host version mismatch)
- Fingerprint spoofing or behavioral evasion (neither exists here)
- Firefox/WebKit
- Users who want a maintained, distributable dependency — use **Patchright** instead

---

## Key Files (verified paths in the repo)

| Path | Role |
|------|------|
| `x_driver/activator_script.py` | The actual patcher: backup → copytree → banner |
| `x_driver/utils.py` | `validate_playwright()` (pins `["1.52.0"]`), `get_playwright_path()` |
| `x_driver/__main__.py` | argparse CLI: `activate [--force]` / `deactivate` |
| `x_driver/rolling.yml` | Supported versions list (`1.52.0`) |
| `x_driver/bundles/package/package.json` | Reveals the bundle = `turnstilebrowser-playwright-core` **1.49.0** |
| `x_driver/bundles/package/lib/server/chromium/crConnection.js` | Utility-world / Runtime.enable fix core |
| `x_driver/bundles/package/lib/server/{page,frames}.js` | Execution-context handling for the fix |
| `x_driver/bundles/node` | 82 MB **Git-LFS pointer**, never installed (swap commented out) |
| `examples/playwright_async.py`, `examples/playwright_sync.py` | **Empty (0-byte) stubs** |
| `setup.py` | `name="x_driver"`, author Arjun Shankar, Apache-2.0, console_script `x_driver` |

---

## Bottom Line

XDriver is a **thin, single-author CLI** that copies a third-party rebrowser-patched Playwright driver (`turnstilebrowser-playwright-core` 1.49.0) over your local `playwright==1.52.0` install. The one real capability — the **Runtime.enable leak fix** — works and is exactly what passes the rebrowser bot-detector. Everything else the README advertises ("C-level" hardening, WebRTC leak protection, marker scrubbing, binding obfuscation, broad enterprise-anti-bot bypass) is **not present in the source**.

**Good for:** a quick, reversible, no-import-changes toggle to test the Runtime.enable fix.

**Functional overlap with Patchright:** both implement the same `Runtime.enable` countermeasure of rebrowser-patches lineage. Patchright is published to PyPI and npm, tracks Playwright releases automatically, supports Python/Node/.NET, and was last pushed 2026-08-05. XDriver has no registry package, pins `playwright-core` 1.49.0, is Python-only, and was last pushed 2025-09-10.

**Layers addressed:** 1 only (`Runtime.enable`, via the bundle). Not Layer 2 (fingerprinting), 3 (behaviour), or 4 (TLS). **Applicability:** reproducing or testing the `Runtime.enable` leak fix against a Playwright 1.52.0 host install.

---

## Resources

- [GitHub Repository](https://github.com/arjun-sha/XDriver) *(old `nicebots-xyz/x_driver` is dead)*
- Upstream patch lineage: [rebrowser-patches](https://github.com/rebrowser/rebrowser-patches) — the technique XDriver's bundle is built on
- [Playwright Documentation](https://playwright.dev/python/)
- ~~PyPI Package~~ — **does not exist**; install via `pip install git+https://github.com/arjun-sha/XDriver.git@v1.0.1`
