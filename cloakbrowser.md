# CloakBrowser - Deep Technical Analysis

> **Tool Type:** Custom Chromium Build (Anti-Detect Browser)
> **Repository:** [github.com/CloakHQ/CloakBrowser](https://github.com/CloakHQ/CloakBrowser)
> **Approach:** C++ source-level fingerprint patches + CDP input behavior mimicking
> **Language:** Python, Node.js (TypeScript), .NET (C#)
> **What is verified:** the patch counts and platform matrix, read from the project's own README (**Tier A** that they are *claimed*; the binary itself is closed, so what the patches do cannot be verified here)
> **Anti-bot service claims:** Turnstile, FingerprintJS, **reCAPTCHA v3 score 0.9**, "tested against 30+ detection sites" — all **Tier B**, all gated to the **Pro** binary. The free binary is not claimed to reach these numbers.
> **Maintenance:** Very active — wrapper **0.5.7** (2026-08-11); Pro binary `chromium-v150.0.7871.114.6-pro` (2026-08-11). 30.0k stars, 19 contributors, 194 open issues. MIT wrapper, **proprietary binary**.
> **Verified:** 2026-08-14 against `CloakHQ/CloakBrowser` @ `2488311`.

> ### Patch counts — current as of 2026-08-14
>
> | Platform | Free | Pro |
> |---|---|---|
> | Linux x86_64 / arm64 | Chromium 146 (**58** patches) | Chromium 150 (**71** patches) |
> | Windows x86_64 | Chromium 146 (**58** patches) | Chromium 150 (**71** patches) |
> | macOS arm64 / x86_64 | Chromium 145 (**26** patches) | Chromium 150 (**71** patches) |
>
> Earlier revisions of this report cited "66" (Chromium 148) and, in one stale
> sentence, "33". Both are superseded. **Patch count is a measure of surface area
> touched, not of quality** — it is not comparable across projects that split changes
> differently.

---

## Table of Contents

- [What is CloakBrowser?](#what-is-cloakbrowser)
- [Current State (2026-08)](#current-state-2026-08)
- [How It Works](#how-it-works)
- [Free vs Pro (Delayed Free-Release Model)](#free-vs-pro-delayed-free-release-model)
- [Human Behavior System](#human-behavior-system)
- [GeoIP + WebRTC Integration](#geoip--webrtc-integration)
- [Framework Integrations](#framework-integrations)
- [Test Results](#test-results)
- [Security Audit](#security-audit)
- [Pros and Cons](#pros-and-cons)
- [Installation & Usage](#installation--usage)
- [When to Use](#when-to-use)

---

## What is CloakBrowser?

CloakBrowser is a **patched Chromium binary** with source-level C++ modifications that spoof browser fingerprints at the engine level. It ships as a drop-in replacement for Playwright and Puppeteer — same API, same code, just swap the import.

**Key differentiator:** Unlike JavaScript injection or config-level patches, CloakBrowser compiles fingerprint spoofing directly into the Chromium binary. Detection scripts see native browser behavior because the modifications happen at the C++ layer — before JavaScript can inspect them.

**Second differentiator:** It targets **Chromium** (not Firefox), which means native Playwright API support, TLS fingerprints that match real Chrome, and compatibility with Chrome's ~65% market share.

**What changed since the last analysis:** the tool has moved fast. The patch count has grown (33 → 66 → **71** on the newest binary), Chromium has advanced (145 → **146 free / 150 Pro**), a **paid Pro tier** now gates the newest binary, a **.NET/C# client** was added alongside Python and Node.js, and binary downloads are now protected by a **pinned Ed25519 signature** rather than the old self-referential checksums. See [Current State](#current-state-2026-08).

---

## Current State (2026-08)

Verified against the repo source and release history (repo cloned at `2488311`, 2026-08-11):

| Fact | Value | Evidence |
|------|-------|----------|
| Wrapper version | **0.5.7** (2026-08-11) | `cloakbrowser/_version.py`, `pyproject.toml`, PyPI |
| Free binary (default) | **Chromium 146.0.7680.177.5** (Linux/Windows x64), 146.0.7680.177.3 (Linux arm64), 145.0.7632.109.2 (macOS) | `cloakbrowser/config.py` → `PLATFORM_CHROMIUM_VERSIONS` |
| Pro binary (latest) | **Chromium 150.0.7871.114.6** | GitHub release `chromium-v150.0.7871.114.6-pro` (2026-08-11), README |
| C++ patch count | **71** on Chromium 150 (Pro); **58** on 146 (free); **26** on macOS 145 | README lines 39/277/846–850 |
| CDP input mimicking | Included in the patch set (input behavior mimicking) | README "How It Works" |
| Languages | Python (≥3.9), Node.js/TypeScript, **.NET 8 / C# (NuGet, community-maintained, since 0.4.3)** | `dotnet/`, `js/`, CHANGELOG |
| License (wrapper) | **MIT** (free forever) | `LICENSE`, `pyproject.toml` |
| License (binary) | Proprietary; **delayed free-release model** (v146 free, v148+ Pro) | `BINARY-LICENSE.md`, README |
| Platforms | Linux x64/arm64, macOS arm64/x64, Windows x64 | `config.py` → `SUPPORTED_PLATFORMS` |
| Maintenance | Very active — last push 2026-08-11; 19 contributors, 194 open issues | GitHub API |
| Last tested (by author) | Aug 2026 (Chromium 150) | README "Test Results" |

> **Note on the "33 patches" claim from the previous analysis:** it is now **outdated**. The patch count is versioned to the binary — the newest Pro build (Chromium 150) has **71**, the free build (146) has **58**, and the older macOS build (145) has **26**. There is no longer a single "33" number.

---

## How It Works

### Architecture Overview

```
┌──────────────────────────────────────────────────────────────────┐
│                    CLOAKBROWSER ARCHITECTURE                       │
├──────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────────┐    ┌──────────────────────┐                │
│  │  Python / JS /   │    │  Platform Detection   │                │
│  │  .NET Wrapper     │    │  (macOS/Linux/Win)    │                │
│  └────────┬─────────┘    └─────────┬────────────┘                │
│           │                        │                              │
│           ▼                        ▼                              │
│  ┌──────────────────────────────────────────────┐                │
│  │     Stealth Args + Fingerprint Seed           │                │
│  │  --fingerprint=<random 10000-99999>           │                │
│  │  --fingerprint-platform=windows|macos         │                │
│  │  --no-sandbox                                  │                │
│  │  (ignore --enable-automation,                  │                │
│  │   --enable-unsafe-swiftshader)                 │                │
│  └──────────────────────┬───────────────────────┘                │
│                          │                                        │
│                          ▼                                        │
│  ┌──────────────────────────────────────────────┐                │
│  │  PATCHED CHROMIUM BINARY (~200MB download)   │                │
│  │  Free: Chromium 146 (58 patches)             │                │
│  │  Pro:  Chromium 150 (71 patches)             │                │
│  │  ┌────────────────────────────────────────┐  │                │
│  │  │  Source-Level C++ Patches               │  │                │
│  │  │  - Canvas fingerprint randomization     │  │                │
│  │  │  - WebGL/WebGPU vendor/renderer spoof   │  │                │
│  │  │  - Audio context noise injection        │  │                │
│  │  │  - Screen/hardware/memory spoofing      │  │                │
│  │  │  - CDP input behavior mimicking          │  │                │
│  │  │  - Font enumeration + Windows metrics   │  │                │
│  │  │  - WebRTC / network-timing hardening     │  │                │
│  │  │  - navigator.webdriver = false           │  │                │
│  │  │  - Automation signal removal             │  │                │
│  │  │  - Coherent seed-built hardware identity │  │                │
│  │  │  - Native locale/timezone spoofing       │  │                │
│  │  └────────────────────────────────────────┘  │                │
│  └──────────────────────────────────────────────┘                │
│                                                                   │
│  ┌──────────────────────────────────────────────┐                │
│  │  Optional: humanize=True                     │                │
│  │  - Bézier curve mouse movement               │                │
│  │  - Per-character typing with typo simulation  │                │
│  │  - Scroll acceleration/deceleration           │                │
│  └──────────────────────────────────────────────┘                │
│                                                                   │
└──────────────────────────────────────────────────────────────────┘
```

CloakBrowser is a thin wrapper around a custom-built Chromium binary:

1. **You install** → `pip install cloakbrowser` / `npm install cloakbrowser` / NuGet `CloakBrowser`
2. **First launch** → binary auto-downloads for your platform (free Chromium 146; Pro fetches 148 with a license key)
3. **Every launch** → Playwright or Puppeteer starts with the CloakBrowser binary + stealth args
4. **You write code** → standard Playwright/Puppeteer API, nothing new to learn

### 1. Fingerprint Seed System

Every launch generates a **random seed** (`--fingerprint=<10000..99999>`) that deterministically controls all fingerprint values. Same seed = same fingerprint across launches (useful for returning-visitor patterns; the README explicitly recommends a fixed seed when hitting the same site repeatedly).

The stealth-args builder is now much leaner than in earlier versions. From `cloakbrowser/config.py`:

```python
def get_default_stealth_args() -> list[str]:
    """Build stealth args with a random fingerprint seed per launch.

    On macOS, skips platform/GPU spoofing — runs as a native Mac browser.
    Spoofing Windows on Mac creates detectable mismatches (fonts, GPU, etc.).
    """
    seed = random.randint(10000, 99999)
    system = platform.system()

    base = [
        "--no-sandbox",
        f"--fingerprint={seed}",
    ]

    if system == "Darwin":
        # Tell the fingerprint patches we're on macOS so GPU/UA match natively
        return base + ["--fingerprint-platform=macos"]

    # Linux/Windows: Windows fingerprint profile.
    return base + ["--fingerprint-platform=windows"]
```

> **Changed since the previous analysis:** the wrapper no longer hardcodes `--fingerprint-gpu-vendor` / `--fingerprint-gpu-renderer` / `--disable-blink-features=AutomationControlled` in the default args. The binary now derives a **coherent hardware identity** (screen, GPU, RAM, CPU cores, color depth, fonts, audio) from the seed itself — "chosen together so they form a popular, self-consistent device with no internal contradictions" (CHANGELOG 0.4.8). Automation-signal suppression happens at the C++ level, and Playwright's `--enable-automation` / `--enable-unsafe-swiftshader` are stripped via `IGNORE_DEFAULT_ARGS`.

**Why platform-aware defaults matter:**
- macOS binary runs as a native Mac browser (Apple GPU, macOS UA) — spoofing Windows on Mac creates detectable font/GPU mismatches
- Linux/Windows binary uses a Windows fingerprint profile (more common, harder to cluster)
- Screen/window size come from the real display, not a flag — so in headed mode the wrapper deliberately does **not** emulate a viewport on top (that would break `outerWidth >= innerWidth` coherence)

### 2. C++ Source-Level Patches (66 on the latest binary)

The patches are compiled into the Chromium binary. They cannot be detected by JavaScript because the modifications happen at the native code level. The binary covers **canvas, WebGL, audio, fonts, GPU, screen properties, WebRTC, network timing, hardware reporting, automation-signal removal, and CDP input behavior mimicking**.

| Patch Area | What It Does |
|------------|--------------|
| Canvas fingerprint | Seed-based randomized noise on canvas operations |
| WebGL/WebGPU | Vendor/renderer spoofing, adapter features, timing-consistent behavior |
| Audio context | Noise injection in audio fingerprinting |
| Screen/Window | Dimensions, pixel ratio, coherent geometry (headed + headless) |
| Hardware | concurrency, deviceMemory, color depth from seed — coherent with GPU/CPU/RAM |
| CDP input mimicking | Pointer/keyboard/mouse events match real user signals |
| Automation signals | webdriver=false, plugin list, window.chrome, UA cleanup |
| Font enumeration | Font-list masking; optional Windows font-metric alignment (`--fingerprint-windows-font-metrics`, 148+) |
| WebRTC / network | Exit-IP injection, network-timing signals matched to real Chrome |
| Locale/timezone | Native C++ locale spoofing (not CDP emulation) |
| Storage quota | Normalized to pass FingerprintJS |

Patch counts by binary (README lines 846–850):

| Platform | Free binary | Pro binary |
|----------|-------------|------------|
| Linux x86_64 | Chromium 146 (**58 patches**) | Chromium 150 (**71 patches**) |
| Linux arm64 | Chromium 146 (58) | Chromium 150 (71) |
| macOS arm64 / x86_64 | Chromium 145 (**26 patches**) | Chromium 150 (71) |
| Windows x86_64 | Chromium 146 (58) | Chromium 150 (71) |

**Why C++ patches are hard to detect:**
- `navigator.webdriver` returns `false` from native code
- `navigator.plugins.length` returns `5` (real Chrome plugin list)
- `window.chrome` is present as an `object` (not `undefined`)
- User-Agent has no `HeadlessChrome` leak
- Canvas/WebGL noise is applied at the rendering level, not via JavaScript injection
- `Object.getOwnPropertyDescriptor()` shows native functions
- No timing differences between real and spoofed values

### 3. CDP Input Behavior Mimicking

CloakBrowser includes source-level patches that make CDP-dispatched input events produce the same signals as real user interactions. This is critical because:

```
Normal Playwright:
  page.click() → CDP Input.dispatchMouseEvent → DETECTABLE timing/signal pattern

CloakBrowser:
  page.click() → CDP Input.dispatchMouseEvent → Patched to produce REAL user signals
```

This is part of why CloakBrowser reports a **0.9 reCAPTCHA v3 score** on the Pro/current build — the input events look human at the browser engine level.

### 4. Binary Download & Verification (Ed25519-signed)

From `cloakbrowser/download.py` + `config.py`:

```
pip install cloakbrowser
    → first launch triggers binary resolution
    → free: downloads Chromium 146 from GitHub Releases
    → Pro (license key set): downloads latest (148) from cloakbrowser.dev
    → fetches SHA256SUMS + detached SHA256SUMS.sig
    → verifies the Ed25519 signature against a PINNED public key,
      then verifies the file hash against the signed manifest
    → extracts to ~/.cloakbrowser/chromium-{version}[-pro]/
    → background update check
```

> **Changed since the previous analysis:** downloads are no longer protected only by same-origin checksums. Since 0.4.0, the wrapper verifies a **pinned Ed25519 signature** (`BINARY_SIGNING_PUBKEYS` in `config.py`) on the published `SHA256SUMS`, so a compromised mirror can no longer certify a tampered or downgraded binary. Verification is mandatory on the official download path. This closes the "self-referential checksums" gap the earlier audit flagged.

Binary size: ~200MB compressed download, cached under `~/.cloakbrowser/`. Runtime footprint (README): ~190MB RAM idle, ~280MB with 3 tabs, ~30MB per additional tab.

---

## Free vs Pro (Delayed Free-Release Model)

New since the previous analysis. The **wrapper (Python + JS + .NET) is MIT, free forever.** The **binary** uses a delayed free-release model:

| Tier | Binary | Where | Notes |
|------|--------|-------|-------|
| **Free** | Chromium **146** (58 patches) | GitHub Releases | Auto-downloads, no key. "Goes stale within weeks as detection evolves." |
| **Pro** | Chromium **150.0.7871.114.6** (71 patches) | cloakbrowser.dev | Newest patches/Chromium first. Set `license_key` / `CLOAKBROWSER_LICENSE_KEY` / `~/.cloakbrowser/license.key` |

- License keys are opaque strings (the wrapper enforces no particular format); validation is cached locally for 24h. The `info` diagnostics command surfaces a `plan` field (default `solo`) (`cloakbrowser/license.py`).
- The Pro test claims (0.9 reCAPTCHA v3, FingerprintJS pass) are explicitly labeled **"Pro/current build"** in the README — the free v146 binary is not guaranteed to hit those. As of 0.4.7 the public Docker `cloaktest` suite was switched to free-tier-stable checks (Sannysoft, Incolumitas, Rebrowser, deviceandbrowserinfo, BrowserScan, CreepJS lies/noise=false); FingerprintJS and reCAPTCHA v3 are no longer hard-pass checks for the free image.
- A valid Pro key now **hard-fails** on a Pro download/signature error instead of silently downgrading to the free binary.

---

## Human Behavior System

CloakBrowser includes a human-behavior simulation system activated with a single flag: `humanize=True`. Playwright API calls are transparently replaced with human-like equivalents. It is mirrored across Python, JS, and .NET.

### Mouse Movement — Bézier Curves

From `cloakbrowser/human/mouse.py`:

```python
def _bezier(p0: Point, p1: Point, p2: Point, p3: Point, t: float) -> Point:
    """Cubic Bézier curve with 4 control points."""
    u = 1 - t
    uu = u * u
    uuu = uu * u
    tt = t * t
    ttt = tt * t
    return Point(
        uuu * p0.x + 3 * uu * t * p1.x + 3 * u * tt * p2.x + ttt * p3.x,
        uuu * p0.y + 3 * uu * t * p1.y + 3 * u * tt * p2.y + ttt * p3.y,
    )

def _ease_in_out(t: float) -> float:
    """Cubic ease-in-out for natural acceleration/deceleration."""
    if t < 0.5:
        return 4 * t * t * t
    return 1 - pow(-2 * t + 2, 3) / 2
```

The mouse movement system:
1. Calculates distance-proportional step count
2. Generates random control points with perpendicular bias for natural curves
3. Applies cubic easing (accelerate → cruise → decelerate)
4. Adds sinusoidal wobble proportional to curve progress
5. Chance of overshoot past target, then correction
6. Burst pauses (mimics micro-hesitations)

### Keyboard Typing — Per-Character Simulation

From `cloakbrowser/human/keyboard.py` (config values in `cloakbrowser/human/config.py`):

- Default typing delay **70ms** ± **40ms** spread; `careful` preset **100ms** ± **50ms**
- **2%** mistype chance (`mistype_chance = 0.02`) — types a keyboard-layout-adjacent key, then backspace-corrects with a "notice" delay (100–300ms) before correction (50–150ms)
- **10%** thinking-pause chance (`typing_pause_chance = 0.1`, 400–1000ms; `careful` = 15%, 500–1200ms)
- Different handling for uppercase (Shift down → char → Shift up), shift-symbols, and normal chars; individual key hold durations
- Non-ASCII characters (Cyrillic, CJK, emoji) use an `insertText` fallback

### Interaction Summary

| Interaction | Default Playwright | With `humanize=True` |
|---|---|---|
| Mouse movement | Instant teleport | Bézier curve with easing and overshoot |
| Clicks | Instant | Aim delay (inputs 60–140ms / buttons 80–200ms) + hold duration |
| Keyboard | Instant fill | Per-character with 70ms ± 40ms variance |
| Scroll | Jump | Accelerate → cruise → decelerate micro-steps |
| `fill()` | Instant value set | Clear field + type character by character |
| Between actions | Nothing | Optional idle micro-movements (`careful` preset) |

### Presets

| Preset | Typing Speed | Aim Delay (button) | Description |
|--------|:-----------:|:---------:|-------------|
| `default` | 70ms/char | 80–200ms | Normal browsing speed |
| `careful` | 100ms/char | 120–280ms | Slower, more deliberate, idle between actions |

Select with `humanize=True, human_preset="careful"`.

---

## GeoIP + WebRTC Integration

CloakBrowser can automatically detect timezone and locale from the proxy exit IP — and, since 0.4.8, from the machine's own public IP even **without a proxy**:

```python
from cloakbrowser import launch

# Auto-detect timezone/locale from proxy exit IP (also injects WebRTC exit IP)
browser = launch(proxy="http://user:pass@us-proxy:8080", geoip=True)
# → Detects America/New_York timezone, en-US locale

# NEW in 0.4.8: geoip works with no proxy (resolves your own public IP)
browser = launch(geoip=True)
```

How it works:
1. Uses MaxMind GeoLite2 data (via the `geoip2` optional dep)
2. Caches in `~/.cloakbrowser/`
3. Resolves the exit IP via HTTP echo services (ipify.org, checkip.amazonaws.com)
4. Extracts country → locale mapping — **expanded from 50 to 132 countries** in 0.4.8
5. Sets `--fingerprint-timezone` and `--lang` binary flags (not detectable CDP emulation)
6. **Auto-injects `--fingerprint-webrtc-ip`** to prevent WebRTC IP leaks (no extra cost)

Explicit timezone/locale always override auto-detection. Failures degrade gracefully. WebRTC IP spoofing can also be used standalone: `args=["--fingerprint-webrtc-ip=auto"]` (resolves exit IP) or `--fingerprint-webrtc-ip=1.2.3.4` (explicit, no network call).

---

## Framework Integrations

New since the previous analysis. CloakBrowser ships example integrations (`examples/integrations/`) for AI-agent and scraping frameworks, in two modes: (1) the framework launches the CloakBrowser binary directly, or (2) CloakBrowser launches first and the framework connects over CDP via `cloakserve`.

| Framework | Language | Example |
|-----------|----------|---------|
| browser-use | Python | `examples/integrations/browser_use_example.py` |
| Crawl4AI | Python | `examples/integrations/crawl4ai_example.py` |
| Crawlee | Python | `examples/integrations/crawlee_example.py` |
| Scrapling | Python | `examples/integrations/scrapling_example.py` |
| Stagehand | TypeScript | `js/examples/stagehand.ts` |
| LangChain | Python | `examples/integrations/langchain_loader.py` |
| Selenium | Python | `examples/integrations/selenium_example.py` |
| undetected-chromedriver | Python | `examples/integrations/undetected_chromedriver.py` |
| agent-browser | Shell | `examples/integrations/agent_browser.sh` |
| AWS Lambda (container) | — | `examples/integrations/aws_lambda/` |

`cloakserve` runs the binary as a CDP server (`docker run -d -p 127.0.0.1:9222:9222 cloakhq/cloakbrowser cloakserve`), rewrites the CDP WebSocket discovery URLs so clients connect through the proxy, and keeps per-seed process routing. `cloaktest` runs the bundled bot-detection smoke suite. Widevine/DRM is supported via an opt-in CDM auto-fetch (`CLOAKBROWSER_FETCH_WIDEVINE`).

---

## Test results — the author's own, mostly on the paid binary

> **Tier B throughout.** These are the maintainer's published results, not independent
> reproductions, and the strongest of them require a Pro licence. The binary is closed,
> so nothing in this table can be verified from source — only that it is claimed.

Results are for the **latest Pro/current build** unless noted. **Last tested by the author: Aug 2026 (Chromium 150).**

| Detection Service | Stock Playwright | CloakBrowser | Notes |
|---|---|---|---|
| **reCAPTCHA v3** | 0.1 (bot) | **0.9** (human) | Pro/current build; server-side verified |
| **Cloudflare Turnstile** (non-interactive) | FAIL | **PASS** | Auto-resolve |
| **Cloudflare Turnstile** (managed) | FAIL | **PASS** | Single click |
| **ShieldSquare** | BLOCKED | **PASS** | Production site |
| **FingerprintJS** bot detection | DETECTED | **PASS** | Pro/current build; demo.fingerprint.com |
| **BrowserScan** bot detection | DETECTED | **NORMAL** (4/4) | browserscan.net |
| **bot.incolumitas.com** | 13 fails | **1 fail** | WEBDRIVER spec only |
| **deviceandbrowserinfo.com** | 6 true flags | **0 true flags** | `isBot: false`; 24/24 signals with `humanize=True` |
| `navigator.webdriver` | `true` | **`false`** | Source-level patch |
| `navigator.plugins.length` | 0 | **5** | Real plugin list |
| `window.chrome` | `undefined` | **`object`** | Present like real Chrome |
| UA string | `HeadlessChrome` | **`Chrome/146.0.0.0`** | No headless leak |
| CDP detection | Detected | **Not detected** | `isAutomatedWithCDP: false` |
| TLS fingerprint | Mismatch | **Identical to Chrome** | ja3n/ja4/akamai match |
| Overall | — | **"Tested against 30+ detection sites"** | Author's claim |

> **How to read these:** these are the tool author's own reported results, not independent reproductions. The strongest ones (0.9 reCAPTCHA v3, FingerprintJS pass) are gated to the **Pro** binary. The **free** v146 binary passes the free-tier `cloaktest` suite (Sannysoft, Incolumitas, Rebrowser, deviceandbrowserinfo, BrowserScan, CreepJS lies/noise=false) but is not claimed to hit the Pro numbers. As always, real-world results depend heavily on IP reputation and per-site behavior.

### Known Acceptable Failures

| Test | Result | Why |
|------|--------|-----|
| WEBDRIVER spec (incolumitas) | False positive | Spec-level detection, expected |
| connectionRTT | Flagged | Datacenter latency, not browser fingerprint |

---

## Security Audit

> **Full audit:** [CloakBrowser Security Audit](https://github.com/pim97/cloakbrowser-analyze)
> **Audit date:** March 2026 | **Binary:** Chromium 145.0.7632.159.7 (Linux x64)

> **Caveat (2026-08):** the public audit was done on the **Chromium 145** binary. The current free binary is **146** and the Pro binary is **150**, neither of which the audit covers. The audit's behavioral conclusions do not automatically transfer to the newer binaries.

### Trust Model

| Component | Source Available | Can You Audit It? |
|-----------|:-:|---|
| Python wrapper (`cloakbrowser/`) | Yes (MIT) | Fully readable |
| JavaScript wrapper (`js/`) | Yes (MIT) | Fully readable |
| .NET/C# wrapper (`dotnet/`) | Yes (MIT) | Fully readable |
| Chromium binary (`chrome`) | **No** (Proprietary) | **Cannot inspect the C++ patches** |
| SHA-256 checksums | **Ed25519-signed** (pinned pubkey) | Authenticity now verifiable, not just integrity |

> **Improvement since the previous analysis:** the old "self-referential checksums" weakness is materially reduced. Since wrapper 0.4.0, `SHA256SUMS` carries a detached Ed25519 signature verified against a public key pinned in the wrapper source (`BINARY_SIGNING_PUBKEYS`). A compromised download mirror can no longer certify a tampered or downgraded binary. This proves the download is genuinely CloakHQ's — it still does **not** let you read the closed-source patches.

### Audit Results: 9/9 Tests Passed (on the Chromium 145 binary)

```
✓ No suspicious strings/URLs in binary (2.9M strings analyzed)
✓ No unexpected network connections (only update check from wrapper)
✓ No sensitive file access (.ssh, .aws, .env, wallets)
✓ No unknown processes spawned (standard Chromium architecture)
✓ No suspicious DNS queries
✓ Standard ELF binary with standard shared libraries
✓ No environment variable sniffing or exfiltration (canary test passed)
✓ Works fine with network completely blocked (no C2 dependency)
✓ Not flagged by VirusTotal (hash not in database)
```

Audit conclusion: the binary "appears to be doing exactly what it claims — and nothing more." The authors emphasize behavioral testing cannot guarantee safety — only open-source code review can.

### What the Audit Cannot Prove

| Evasion Technique | Detectable by Audit? |
|---|:-:|
| Always-on data exfiltration | Yes |
| Time bomb (activates after N days) | **No** |
| Conditional trigger (specific sites) | **No** |
| Encrypted exfiltration (HTTPS traffic) | **No** |
| Targeted payload (specific users) | **No** |

### Risk Level: MEDIUM

The binary behaved legitimately in all tests, but it remains closed-source, and the audited version (145) is now behind the shipping versions (146 free / 148 Pro). The license prohibits reverse engineering.

### Mitigation Recommendations

```bash
# Disable auto-update (prevents silent binary replacement)
export CLOAKBROWSER_AUTO_UPDATE=false

# Pin an exact binary version (rollback / reproducibility)
export CLOAKBROWSER_VERSION=146.0.7680.177.5

# Run in Docker with restricted network
docker run --network=none cloakbrowser-app

# Use your own Chromium build (bypass proprietary binary)
export CLOAKBROWSER_BINARY_PATH=/path/to/your/chromium
```

### Risk Comparison

| Tool | Source Available | Binary Auditable | Risk Level |
|------|:-:|:-:|---|
| **Camoufox** | Fully open source | Yes — compile yourself | Lowest |
| **Clearcote** | Fully open source | Yes — reproducible builds | Lowest |
| **Patchright** | Fully open source | Yes — compile yourself | Lowest |
| **SeleniumBase** | Fully open source | Uses stock ChromeDriver | Low |
| **CloakBrowser** | Wrapper only | **No** — proprietary binary | **Medium** |

---

## Pros and Cons

### Advantages

| Pro | Details |
|-----|---------|
| **C++ Chromium patches** | 71 source-level modifications on the latest Pro binary (Chromium 150) — not JS injection, not config flags |
| **Chromium engine** | TLS fingerprint matches real Chrome, ~65% market share |
| **Drop-in Playwright/Puppeteer** | Same API — swap the import, keep your code |
| **`humanize=True`** | One flag for Bézier mouse, typing simulation, scroll patterns |
| **0.9 reCAPTCHA v3** (Pro) | Human-level score with CDP input mimicking patches |
| **Multi-language** | Python + Node.js (TypeScript) + **.NET 8 / C#** with full type definitions |
| **Cross-platform** | Linux x64/arm64, macOS arm64/x64, Windows x64 |
| **Platform-aware defaults** | macOS runs native; Linux/Windows use a Windows persona automatically |
| **Coherent seed identity** | Screen/GPU/RAM/CPU/fonts/audio chosen together as a plausible real device |
| **Signed downloads** | Pinned Ed25519 signature on checksums — authenticity, not just integrity |
| **GeoIP + WebRTC coherence** | Timezone/locale/WebRTC-IP from proxy or own IP (132 countries) |
| **Framework integrations** | browser-use, Crawl4AI, Crawlee, Scrapling, Stagehand, LangChain, Selenium, UC |
| **`cloakserve` CDP server** | Per-seed CDP routing for framework/Docker deployments |
| **Version pinning/rollback** | `browser_version=` / `CLOAKBROWSER_VERSION` for Free and Pro binaries |
| **Widevine/DRM** | Opt-in CDM auto-fetch for persistent contexts |
| **Persistent profiles** | Cookies/localStorage across sessions |
| **Zero config** | Stealthy by default — no flags needed |

### Disadvantages

| Con | Details |
|-----|---------|
| **Closed-source binary** | Proprietary Chromium — cannot verify the C++ patches |
| **Best results are paid** | 0.9 reCAPTCHA v3 / FingerprintJS pass are gated to the **Pro** binary (v148+); free is v146 and "goes stale within weeks" |
| **Audit lags shipping version** | Public audit covers Chromium 145; free is 146, Pro is 148 |
| **`--no-sandbox`** | Runs with the Chromium sandbox disabled by default |
| **Large download** | ~200MB compressed binary on first run |
| **Auto-update** | Background update check (can be disabled) |
| **No CAPTCHA solving** | Prevents CAPTCHAs from appearing, doesn't solve them |
| **License restrictions** | Binary license prohibits redistribution and reverse engineering |
| **Author-reported tests** | Detection results are the vendor's own, not independent reproductions |

---

## Installation & Usage

### Quick Start

```bash
# Python
pip install cloakbrowser

# Python with GeoIP support
pip install "cloakbrowser[geoip]"

# Node.js (Playwright)
npm install cloakbrowser playwright-core

# Node.js (Puppeteer)
npm install cloakbrowser puppeteer-core

# .NET / C#
dotnet add package CloakBrowser
```

### Basic Usage

```python
from cloakbrowser import launch

browser = launch()
page = browser.new_page()
page.goto("https://protected-site.com")
browser.close()
```

```javascript
import { launch } from 'cloakbrowser';

const browser = await launch();
const page = await browser.newPage();
await page.goto('https://protected-site.com');
await browser.close();
```

### Pro (latest binary)

```python
# Pass a key, or set CLOAKBROWSER_LICENSE_KEY / ~/.cloakbrowser/license.key
browser = launch(license_key="cb_xxxxxxxx")
```

### With Human Behavior

```python
browser = launch(humanize=True)                       # default preset
browser = launch(humanize=True, human_preset="careful")  # slower, more deliberate
page = browser.new_page()
page.goto("https://example.com")
page.locator("#email").fill("user@example.com")  # per-character typing
page.locator("button[type=submit]").click()       # Bézier curve movement
```

### With Proxy + GeoIP + WebRTC

```python
# proxy: timezone/locale + WebRTC exit IP auto-detected
browser = launch(proxy="http://user:pass@proxy:8080", geoip=True)

# SOCKS5 also supported
browser = launch(proxy="socks5://user:pass@proxy:1080", geoip=True)

# no proxy: resolves your own public IP (new in 0.4.8)
browser = launch(geoip=True)
```

### Persistent Profile

```python
from cloakbrowser import launch_persistent_context

ctx = launch_persistent_context("./my-profile", headless=False)
page = ctx.new_page()
page.goto("https://protected-site.com")
ctx.close()  # cookies/localStorage saved and restored next run
```

### Fixed Fingerprint Seed / Version Pin

```python
# Same seed = same identity across launches (returning visitor)
browser = launch(args=["--fingerprint=42069"])

# Pin an exact binary (rollback if a new build regresses)
browser = launch(browser_version="148.0.7778.215.2")
```

### CLI / Docker

```bash
# Diagnostics: which binary launches, license tier, fonts, geoip, deps
cloakbrowser info

# Quick bot-detection smoke test
docker run --rm cloakhq/cloakbrowser cloaktest

# CDP server mode (per-seed routing)
docker run -d --name cloak -p 127.0.0.1:9222:9222 cloakhq/cloakbrowser cloakserve
```

---

## When to Use

### Recommended For

- Chromium-required targets (sites that block or flag Firefox)
- Need Playwright/Puppeteer API compatibility (existing code)
- Python, Node.js, **or .NET/C#** projects
- High stealth with zero configuration
- Behavioral detection bypass (`humanize=True`)
- Sites with reCAPTCHA v3 scoring (Pro binary for the 0.9 score)
- AI-agent / framework stacks (browser-use, Crawl4AI, Stagehand, LangChain, Scrapling)
- Persistent sessions with fingerprint consistency
- Docker/VPS/Lambda deployments (works identically everywhere)

### Not Recommended For

- Security-critical environments (closed-source binary risk)
- Need to audit every component (use Camoufox, Clearcote, or Patchright)
- CAPTCHA solving (use SeleniumBase)
- Statistical fingerprint rotation (use Camoufox + BrowserForge)
- Free-only projects that need the very latest patches (best numbers are Pro-gated)
- Minimal footprint (~200MB binary)

---

## Key Files

| File | Purpose |
|------|---------|
| `cloakbrowser/_version.py` | Wrapper version (`0.4.8`) |
| `cloakbrowser/config.py` | Stealth args, platform detection, seed, Chromium version map, signed-download config |
| `cloakbrowser/browser.py` | `launch()`, `launch_async()`, `launch_context()`, `launch_persistent_context()` |
| `cloakbrowser/download.py` | Binary download, Ed25519-signed verification, auto-update |
| `cloakbrowser/license.py` | Pro license validation/caching, tier resolution, Pro version check |
| `cloakbrowser/geoip.py` | MaxMind GeoIP timezone/locale + WebRTC-IP detection |
| `cloakbrowser/widevine.py` | Widevine CDM handling for DRM playback |
| `cloakbrowser/human/mouse.py` | Bézier curve movement, click targeting, overshoot |
| `cloakbrowser/human/keyboard.py` | Per-character typing, typo simulation, shift handling |
| `cloakbrowser/human/scroll.py` | Accelerate → cruise → decelerate scroll physics |
| `cloakbrowser/human/config.py` | `HumanConfig` dataclass, `default` / `careful` presets |
| `js/src/` | Node.js/TypeScript wrapper (Playwright + Puppeteer + human) |
| `dotnet/src/CloakBrowser/` | .NET 8 / C# wrapper (NuGet `CloakBrowser`) |
| `CHANGELOG.md` | Full wrapper + binary changelog |
| `BINARY-LICENSE.md` | Proprietary binary license (delayed free-release model) |

---

## Comparison

> **Star ratings below are the author's editorial judgment, not measurement.**
> No rubric defines the scale and no benchmark backs any cell. They are retained
> only as a rough relative ordering — see [METHODOLOGY.md](METHODOLOGY.md#rating-policy).


| Feature | CloakBrowser | Camoufox | Patchright | SeleniumBase | Botasaurus |
|---------|:----------:|:--------:|:----------:|:------------:|:----------:|
| Spoofing Level | C++ (Chromium) | C++ (Firefox) | Binary patch | Config + UC | JS wrapper |
| Browser | Chromium | Firefox | Chromium | Chrome | Chrome |
| Playwright API | ✅ Native | Via Juggler | ✅ Native | ❌ Selenium | ❌ Selenium |
| Fingerprint Rotation | Seed-based | ✅ BrowserForge | Partial | Partial | Partial |
| Human Simulation | ✅ Full (Bézier + typing) | ✅ Good | ⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| reCAPTCHA v3 Score | **0.9** (Pro) | 0.7-0.9 | 0.3-0.7 | 0.3-0.7 | 0.3-0.5 |
| CAPTCHA Solving | ❌ | ❌ | ❌ | ✅ Built-in | ⭐⭐ |
| Languages | Py / JS / .NET | Python | Py / JS / .NET | Python | Python |
| Source Available | Wrapper only | Fully open | Fully open | Fully open | Fully open |
| Detection Difficulty | Very Hard | Very Hard | Hard | Hard | Medium |

---

## Conclusion

CloakBrowser remains the **strongest Chromium-based anti-detection tool** in this comparison. By modifying Chromium at the C++ source level (**66 patches** on the latest Pro binary, 58 on the free binary), it achieves native-appearing fingerprint spoofing that the author reports passes all major detection services including reCAPTCHA v3 (0.9 score) and Cloudflare Turnstile. Since the last analysis it has added a **.NET/C# client**, **coherent seed-built hardware identities**, **Ed25519-signed downloads**, **WebRTC-IP coherence**, **132-country GeoIP**, **version pinning/rollback**, **Widevine/DRM**, and a broad set of **AI-agent/framework integrations**.

The `humanize=True` flag still adds comprehensive behavioral simulation (Bézier mouse curves, realistic typing with typos, scroll physics), making it effective against both fingerprint and behavioral detection layers.

**The trade-offs are now sharper.** The Chromium binary is **closed-source** and proprietary, and the strongest results are gated behind a **paid Pro tier** — the free binary (Chromium 146) "goes stale within weeks." The independent security audit (9/9 tests passed, no malicious behavior) covers the **older Chromium 145** binary, not the 146/148 builds now shipping, so its conclusions do not fully transfer. The Ed25519 signing does close the old self-referential-checksum gap, but it proves authenticity, not what the patches actually do.

**Best for:** Maximum Chromium stealth with Playwright API compatibility, zero configuration, and (for the top numbers) a Pro subscription.

**Limitation:** Proprietary binary requires trust in the CloakBrowser team; the best-performing binary is paid. If auditability is critical, use Camoufox, Clearcote, or Patchright instead.

---

*Analysis conducted for educational purposes. Use responsibly.*
