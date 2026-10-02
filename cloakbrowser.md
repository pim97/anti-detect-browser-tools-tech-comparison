# CloakBrowser - Deep Technical Analysis

> **Tool Type:** Custom Chromium Build (Anti-Detect Browser)
> **Repository:** [github.com/CloakHQ/CloakBrowser](https://github.com/CloakHQ/CloakBrowser)
> **Approach:** C++ source-level fingerprint patches + CDP input behavior mimicking
> **Language:** Python, Node.js (TypeScript), .NET (C#)
> **What is verified:** the wrapper source (default arguments, download and signature verification, license handling, humanize module) read at the commit below (**Tier A**), plus the patch counts and platform matrix read from the project's own README (**Tier A** that they are *claimed*; the binary itself is closed, so what the patches do cannot be verified here)
> **Anti-bot service claims:** Turnstile, FingerprintJS, **reCAPTCHA v3 score 0.9**, "tested against 30+ detection sites" — all **Tier B**, stated for the README's "latest Pro/current build". The keyless free binary (Chromium 146) is not claimed to reach these numbers.
> **Maintenance:** wrapper **0.5.11** (2026-09-24); latest GitHub release `chromium-v152.0.7977.82.1-pro` (2026-09-23); last push 2026-09-29. 31.8k stars, 2.6k forks, 20 contributors, 237 open issues. MIT wrapper, **proprietary binary**.
> **Verified:** 2026-09-30 against `CloakHQ/CloakBrowser` @ `f44864b`.

> ### Patch counts — current as of 2026-09-30
>
> | Platform | Free | Pro |
> |---|---|---|
> | Linux x86_64 / arm64 | Chromium 146 (**58** patches) | Chromium 152 (**87** patches) |
> | Windows x86_64 | Chromium 146 (**58** patches) | Chromium 152 (**87** patches) |
> | macOS arm64 / x86_64 | Chromium 145 (**26** patches) | Chromium 151 (**87** patches) |
>
> Source: the vendor README (`README.md:893-897`). The Free column is the binary the wrapper downloads without a key (`cloakbrowser/config.py:18-26`); the README separately offers the latest build on a free GitHub-sign-in key (see [Free vs Pro](#free-vs-pro-delayed-free-release-model)) and states no patch count for it.
> Earlier revisions of this report cited "33", "66" (Chromium 148) and "71" (Chromium 150); all are superseded. **Patch count is a measure of surface area
> touched, not of quality** — it is not comparable across projects that split changes
> differently.

---

## Table of Contents

- [What is CloakBrowser?](#what-is-cloakbrowser)
- [Current State (2026-09)](#current-state-2026-09)
- [How It Works](#how-it-works)
- [Free vs Pro (Delayed Free-Release Model)](#free-vs-pro-delayed-free-release-model)
- [Human Behavior System](#human-behavior-system)
- [GeoIP + WebRTC Integration](#geoip--webrtc-integration)
- [Framework Integrations](#framework-integrations)
- [Test results — the author's own, mostly on the paid binary](#test-results--the-authors-own-mostly-on-the-paid-binary)
- [Security Audit](#security-audit)
- [Pros and Cons](#pros-and-cons)
- [Installation & Usage](#installation--usage)
- [When to Use](#when-to-use)

---

## What is CloakBrowser?

CloakBrowser is a **patched Chromium binary** with source-level C++ modifications that spoof browser fingerprints at the engine level. It ships as a drop-in replacement for Playwright and Puppeteer — same API, same code, just swap the import.

**Approach:** the vendor states that fingerprint changes are compiled into the Chromium binary rather than injected through JavaScript or configuration (`README.md:22`, `README.md:179`; Tier B, the binary is closed). Whether any individual patch is observable from page JavaScript is not established here (Tier D).

**Engine:** it targets **Chromium** (not Firefox), which gives native Playwright/Puppeteer API support; the vendor reports TLS fingerprints identical to Chrome (README test table, Tier B).

**What changed since the last analysis:** the tool has moved fast. The patch count has grown (33 → 66 → 71 → **87** on the newest binaries), Chromium has advanced (145 → **146 keyless free / 152 Pro**), a **keyed tier** now gates the newest binary (a **free GitHub-sign-in key** limited to one concurrent session, and paid plans), a **.NET/C# client** was added alongside Python and Node.js, and binary downloads are protected by a **pinned Ed25519 signature** rather than the old self-referential checksums. See [Current State](#current-state-2026-09).

---

## Current State (2026-09)

Verified against the repo source and release history (repo cloned at `f44864b`, 2026-09-29; previous revision `2488311`, 2026-08-11):

| Fact | Value | Evidence |
|------|-------|----------|
| Wrapper version | **0.5.11** (2026-09-24) | `cloakbrowser/_version.py:1`, `js/package.json:3`, `dotnet/src/CloakBrowser/CloakBrowser.csproj:13`, PyPI / npm |
| Free binary (keyless default) | **Chromium 146.0.7680.177.5** (Linux/Windows x64), 146.0.7680.177.3 (Linux arm64), 145.0.7632.109.2 (macOS) | `cloakbrowser/config.py:18-26` → `PLATFORM_CHROMIUM_VERSIONS` (unchanged since `2488311`) |
| Free binary with GitHub-sign-in key | "Latest build", one concurrent session; `cloakbrowser login` (since 0.5.0). The README names Chromium 151 for this tier | `README.md:190-197`, `cloakbrowser/__main__.py:584-660`, `cloakbrowser/download.py:224-243`, CHANGELOG 0.5.0 |
| Pro binary (latest) | **Chromium 152.0.7977.82.1** (Linux x64/arm64, Windows x64); **151.0.7922.108.3** (macOS) | GitHub release `chromium-v152.0.7977.82.1-pro` (2026-09-23); `README.md:153-156` |
| C++ patch count | **87** on Chromium 152 / 151 (Pro); **58** on 146 (free); **26** on macOS 145 | `README.md:39`, `README.md:289`, `README.md:893-897` |
| CDP input mimicking | Included in the patch set (input behavior mimicking) | README "How It Works" (`README.md:289`) |
| Languages | Python (≥3.9), Node.js/TypeScript (≥20), **.NET 8 / C# (NuGet; contributed by an outside author in PR #385, CHANGELOG 0.4.3)** | `pyproject.toml:11`, `js/package.json:57-59`, `dotnet/src/CloakBrowser/CloakBrowser.csproj:4`, `CHANGELOG.md:180-182` |
| License (wrapper) | **MIT** | `LICENSE`, `pyproject.toml:10` |
| License (binary) | Proprietary (`BINARY-LICENSE.md` v1.3, July 2026): the latest major requires a subscription at a tier CloakHQ designates; other versions stay under the same restrictions | `BINARY-LICENSE.md` ("Version-Specific Terms", "Restrictions") |
| Platforms | Linux x64/arm64, macOS arm64/x64, Windows x64 | `cloakbrowser/config.py:91-98` → `SUPPORTED_PLATFORMS` |
| Maintenance | Last push 2026-09-29; 20 contributors, 237 open issues, 31,814 stars | GitHub API (`STATUS.md`) |
| Last tested (by author) | Aug 2026 (Chromium 151) | `README.md:220` |

> **Note on patch counts:** there is no single number. The patch count is versioned to the binary: the newest Pro builds (Chromium 152, macOS 151) are stated as **87**, the keyless free build (146) as **58**, and the older macOS free build (145) as **26**. The "33" figure from an earlier analysis and the "71" figure from the 2026-08-14 revision are outdated.

> **Free-key version:** `README.md:190` names Chromium 151 for the free-key tier while `README.md:153` gives 152 as Pro Stable; the wrapper selects the binary the same way for free and paid keys (`cloakbrowser/download.py:401-404`), so the build a free key resolves to is decided server-side and is not established here (Tier D).

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
│  │  Pro:  Chromium 152 (87 patches)             │                │
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
2. **First launch** → binary auto-downloads for your platform (no key: free Chromium 146; with a free or paid license key: the latest keyed build, Pro Stable being Chromium 152 on Linux/Windows)
3. **Every launch** → Playwright or Puppeteer starts with the CloakBrowser binary + stealth args
4. **You write code** → standard Playwright/Puppeteer API, nothing new to learn

### 1. Fingerprint Seed System

Every launch generates a **random seed** (`--fingerprint=<10000..99999>`) that deterministically controls all fingerprint values. Same seed = same fingerprint across launches (useful for returning-visitor patterns; the README explicitly recommends a fixed seed when hitting the same site repeatedly).

The stealth-args builder is now much leaner than in earlier versions. From `cloakbrowser/config.py:54-76` (comments abridged):

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

**`--no-sandbox` default:** `--no-sandbox` is the first entry of the default list (`config.py:64`) in the Python, JavaScript (`js/src/config.ts:426`) and .NET (`dotnet/src/CloakBrowser/Config.cs:77`) wrappers, and `cloakserve` builds its Chrome arguments from the same list (`bin/cloakserve:354-355`). Caller `args` can override a flag but cannot remove it (`browser.py:1424-1429`); `stealth_args=False` omits the whole default list, and the README shows supplying `--fingerprint` and `--fingerprint-platform` manually in that case (`README.md:818-821`). The README does not mention the flag; CHANGELOG 0.5.2 records that the binary stops showing an unsupported-flag warning bar when the sandbox is disabled, which it describes as required when running as root, for example in Docker (`CHANGELOG.md:100`).

**Why platform-aware defaults matter:**
- macOS binary runs as a native Mac browser (Apple GPU, macOS UA) — spoofing Windows on Mac creates detectable font/GPU mismatches
- Linux/Windows binary uses a Windows fingerprint profile (more common, harder to cluster)
- Screen/window size come from the real display, not a flag — so in headed mode the wrapper deliberately does **not** emulate a viewport on top (that would break `outerWidth >= innerWidth` coherence)

### 2. C++ Source-Level Patches (87 on the latest binaries)

The vendor states the patches are compiled into the Chromium binary (Tier B; the binary is closed and cannot be inspected here). The binary covers **canvas, WebGL, audio, fonts, GPU, screen properties, WebRTC, network timing, hardware reporting, automation-signal removal, and CDP input behavior mimicking** (`README.md:289`).

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
| Storage quota | Normalized by default (also hides the real disk size); `--fingerprint-storage-quota` overrides it. The README notes BrowserScan's incognito check reads the default as incognito (`README.md:452`, `README.md:747`) |

Patch counts by binary (`README.md:893-897`):

| Platform | Free binary | Pro binary |
|----------|-------------|------------|
| Linux x86_64 | Chromium 146 (**58 patches**) | Chromium 152 (**87 patches**) |
| Linux arm64 | Chromium 146 (58) | Chromium 152 (87) |
| macOS arm64 / x86_64 | Chromium 145 (**26 patches**) | Chromium 151 (87) |
| Windows x86_64 | Chromium 146 (58) | Chromium 152 (87) |

**Properties the vendor reports for the patched binary (Tier B):**
- `navigator.webdriver` returns `false`
- `navigator.plugins.length` returns `5`
- `window.chrome` is present as an `object`
- User-Agent has no `HeadlessChrome` leak (`Chrome/151.0.0.0` in the latest test run)
- CDP detection `isAutomatedWithCDP: false`; TLS fingerprint reported identical to Chrome (ja3n / ja4 / akamai)
- Changes are described as compiled into the binary rather than injected via JavaScript (`README.md:22`, `README.md:179`)

The README makes no claim about native-looking property descriptors or about the absence of timing differences; neither is established here (Tier D).

### 3. CDP Input Behavior Mimicking

The README lists "CDP input behavior mimicking" among the binary's patch areas (`README.md:289`): source-level patches intended to make CDP-dispatched input events carry the same signals as real user interactions. This is the vendor's description (Tier B); the patch is in the closed binary:

```
Normal Playwright:
  page.click() → CDP Input.dispatchMouseEvent → DETECTABLE timing/signal pattern

CloakBrowser:
  page.click() → CDP Input.dispatchMouseEvent → Patched to produce REAL user signals
```

The README reports a **0.9 reCAPTCHA v3 score** on the Pro/current build (`README.md:224`, Tier B) and does not isolate the contribution of this patch. The wrapper-side `humanize` module (below) is separate and is readable source (Tier A).

### 4. Binary Download & Verification (Ed25519-signed)

From `cloakbrowser/download.py` + `config.py`:

```
pip install cloakbrowser
    → first launch triggers binary resolution (ensure_binary, download.py:184)
    → no key: downloads the free binary (Chromium 146) from cloakbrowser.dev,
      falling back to GitHub Releases (download.py:361-370)
    → license key set (free GitHub key or paid): POSTs the key to
      cloakbrowser.dev/api/license/validate, then downloads the latest build from
      cloakbrowser.dev/api/download/<version> with the key as a bearer token
      (download.py:224-243, 530-565)
    → fetches SHA256SUMS + detached SHA256SUMS.sig
    → verifies the Ed25519 signature against a PINNED public key, checks that the
      signed manifest's version= line matches the requested version, then verifies
      the file hash against the signed manifest (download.py:633-703)
    → extracts to ~/.cloakbrowser/chromium-{version}[-pro]/
    → background update check (rate-limited to once per hour, download.py:67, 1268-1279)
```

> **Changed since the previous analysis:** downloads are no longer protected only by same-origin checksums. Since 0.4.0, the wrapper verifies a **pinned Ed25519 signature** (`BINARY_SIGNING_PUBKEYS`, `config.py:37-39`; one key is pinned) on the published `SHA256SUMS`, and the signed manifest's `version=` line must match the requested version, so a mirror cannot substitute a genuinely signed older build (`download.py:684-694`). Verification is mandatory on the official and Pro download paths. `CLOAKBROWSER_SKIP_CHECKSUM` and `CLOAKBROWSER_DOWNLOAD_URL` apply only to a self-hosted origin, where the Pro path and background updates are switched off (`download.py:221-222, 633-670, 1137`). This closes the "self-referential checksums" gap the earlier audit flagged.

> **Extraction (0.5.11):** once the signature and checksum verify, archives are unpacked directly with `tarfile.extractall(filter="fully_trusted")` and `zipfile.extractall`; the earlier per-entry path-traversal and symlink screening was removed (`download.py:935-951`, `CHANGELOG.md:13`). The trust boundary for extraction is therefore the signature check.

The README also documents manual verification (`README.md:1432-1449`): a GPG-signed release tag, GitHub/Sigstore build attestation for the binary archives, and a Cosign signature for the Docker image (vendor-documented, Tier B). The repository contains the workflows for the last two: `.github/workflows/attest-release.yml` (manual dispatch, attests release archives) and `.github/workflows/publish.yml:155-159` (Cosign signing and attestation of the Docker image).

Binary size: ~200MB compressed download (`README.md:127`), cached under `~/.cloakbrowser/`. Runtime footprint (`README.md:1074`): ~190MB RAM idle, ~280MB with 3 tabs, ~30MB per additional tab.

---

## Free vs Pro (Delayed Free-Release Model)

The **wrapper (Python + JS + .NET) is MIT.** The **binary** is proprietary (`BINARY-LICENSE.md` v1.3, July 2026) and is delivered in three ways, selected by the key the wrapper resolves:

| Tier | Binary | Where | Notes |
|------|--------|-------|-------|
| **Free, no key** | Chromium **146** (58 patches); 145 (26) on macOS | cloakbrowser.dev, GitHub Releases as fallback | Auto-downloads, no key. The README says this older build "ages fast as detection evolves" (`README.md:192`); the launch banner invites the free login (`download.py:163-174`) |
| **Free, GitHub-sign-in key** | "Latest build" (README names Chromium 151, see [Current State](#current-state-2026-09)) | cloakbrowser.dev (`/api/download/<version>`, key as bearer token) | `cloakbrowser login` opens a GitHub sign-in and the key is emailed to the GitHub address (`__main__.py:601-615`); **one concurrent session**; a version pin is ignored for this plan (`download.py:231-232`) |
| **Pro, paid key** | Chromium **152.0.7977.82.1** (Linux/Windows), 151 (macOS); 87 patches | cloakbrowser.dev | Newest patches first; the README lists plans of 5, 20, 200 or 2,000+ concurrent sessions (`README.md:191`). Set `license_key` / `CLOAKBROWSER_LICENSE_KEY` / `~/.cloakbrowser/license.key` |

- **Key handling.** Resolution order is explicit parameter, then `CLOAKBROWSER_LICENSE_KEY`, then `license.key` in the cache directory (`cloakbrowser/license.py:262-292`). Keys are opaque strings to the wrapper (no format is enforced); validation is a POST to `cloakbrowser.dev/api/license/validate` (`license.py:26, 399-404`), cached locally for 24h keyed by a SHA-256 of the key (`license.py:30, 392-395, 622-634`), and a stale cache is used if the server is unreachable (`license.py:421-424`). `cloakbrowser info` reports the plan (default `solo` when the server omits it, `license.py:410`) as `tier` (`__main__.py:144`) and, for keyed plans, live session seats as used/limit (`__main__.py:267-278`, `license.py:517-569`).
- **Server-side enforcement.** The wrapper comments state that the server enforces the concurrency cap (`download.py:401-404`). The Pro binary reports license denials through process exit codes 76-79 (`license.py:102-119`) and, for denials after the CDP handshake, a per-launch status file named by `CLOAKBROWSER_LICENSE_STATUS_FILE` (`license.py:143-150, 227-242`), which the wrapper converts to `CloakBrowserLicenseError`. These are wrapper-side facts (Tier A); what the binary does is Tier B.
- **No silent downgrade.** A key the server rejects, or one that cannot be validated (server unreachable and no cached result), now raises `CloakBrowserLicenseError` instead of falling back to the free binary (`download.py:256-269`; CHANGELOG 0.5.10, `CHANGELOG.md:22`). A valid key also hard-fails on a download or signature error (`download.py:237-255`).
- **Test claims.** The Pro test claims (0.9 reCAPTCHA v3, FingerprintJS pass) are labeled "Pro/current build" in the README (`README.md:220-228`); the keyless free v146 binary is not claimed to hit them. As of 0.4.7 the public Docker `cloaktest` suite uses free-tier-stable checks (Sannysoft, Incolumitas, Rebrowser, deviceandbrowserinfo, BrowserScan, CreepJS lies/noise=false); FingerprintJS and reCAPTCHA v3 are not hard-pass checks for the free image (`CHANGELOG.md:161`).
- **Release channel.** Since 0.5.2 `release_channel="preview"` / `CLOAKBROWSER_RELEASE_CHANNEL=preview` selects the newest build available for the platform and falls back to Stable (`config.py:107-114`, `CHANGELOG.md:90`).
- **Binary license terms** (`BINARY-LICENSE.md`): the latest major version requires an active paid subscription at a tier CloakHQ designates; the license prohibits redistribution, resale or repackaging, reverse engineering, and modification, and forbids sharing license keys. The README separately offers the free-key tier above.

---

## Human Behavior System

CloakBrowser includes a human-behavior simulation system activated with a single flag: `humanize=True`. Playwright API calls are transparently replaced with human-like equivalents. It is mirrored across Python, JS, and .NET.

### Mouse Movement — Bézier Curves

From `cloakbrowser/human/mouse.py` (`_bezier` at :32-41, `_ease_in_out` at :26-29):

```python
def _bezier(p0: Point, p1: Point, p2: Point, p3: Point, t: float) -> Point:
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
    if t < 0.5:
        return 4 * t * t * t
    return 1 - pow(-2 * t + 2, 3) / 2
```

The mouse movement system:
1. Calculates distance-proportional step count
2. Generates random control points with perpendicular bias for natural curves
3. Applies cubic easing (accelerate → cruise → decelerate)
4. Adds a sinusoidal wobble (amplitude `sin(pi * progress) * mouse_wobble_max`, 1.5 px by default)
5. Chance of overshoot past target, then correction
6. Burst pauses (mimics micro-hesitations)

### Keyboard Typing — Per-Character Simulation

From `cloakbrowser/human/keyboard.py` (config values in `cloakbrowser/human/config.py`):

- Default typing delay **70ms** ± **40ms** spread; `careful` preset **100ms** ± **50ms**
- **2%** mistype chance (`mistype_chance = 0.02`) — types a keyboard-layout-adjacent key, then backspace-corrects with a "notice" delay (100–300ms) before correction (50–150ms)
- **10%** thinking-pause chance (`typing_pause_chance = 0.1`, 400–1000ms; `careful` = 15%, 500–1200ms)
- Different handling for uppercase (Shift down → char → Shift up), shift-symbols, and normal chars; individual key hold durations
- Non-ASCII characters (Cyrillic, CJK, emoji) use an `insertText` fallback
- Shift-symbols are sent through CDP `Input.dispatchKeyEvent` when a CDP session is available (`isTrusted=true`); otherwise a `page.evaluate` fallback that the source comments call detectable (`human/keyboard.py:123-181`)

### Selector Handling and Patched Methods

The humanize layer reads element state and geometry in a CDP isolated world (`Page.createIsolatedWorld`, `cloakbrowser/human/__init__.py:76-106`) instead of through Playwright's selector/evaluate machinery, so it reimplements a subset of Playwright's selector grammar (`cloakbrowser/human/stealth_dom.py:1-32`):

- **Supported:** CSS (including `:has-text`), `text=`, `xpath=`, `get_by_test_id`, `get_by_placeholder`, `get_by_alt_text`, `get_by_title`, `get_by_text`, `get_by_label`, and a trailing `.first` / `.nth()` / `.last`.
- **Not supported** (raises `UnsupportedHumanizeSelectorError`; there is no fallback to Playwright DOM reads): `get_by_role`, chained locators (`>>`, `.filter()`, `.and_()`, `.or_()`), `frame_locator`, `:visible`, `:nth-match` (`stealth_dom.py:54-72`).
- **Patched page methods (Python):** `goto`, `click`, `dblclick`, `hover`, `type`, `fill`, `check`, `uncheck`, `select_option`, `press`, plus `query_selector`, `query_selector_all`, `wait_for_selector`, locators, element handles and frames (`human/__init__.py:1233-1242, 1655-1657`). Actions run actionability checks (attached, visible, stable, enabled, editable, receives events) before the cursor moves (`human/actionability.py`).
- **Scrolling:** scroll-into-view now works on both axes (`human/scroll.py:236-278`); the x-axis handling landed after the 0.5.11 release commit.

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
1. Uses MaxMind GeoLite2-City data via the optional `geoip2` dependency; the ~70 MB database is downloaded on first use from a third-party GitHub mirror (`P3TERX/GeoLite.mmdb`, `geoip.py:26-29`) and refreshed every 30 days (`geoip.py:31`)
2. Caches the database in `~/.cloakbrowser/geoip/` (`geoip.py:291-294`)
3. Resolves the exit IP via HTTP echo services (ipify.org, checkip.amazonaws.com, ifconfig.me; `geoip.py:197-199`)
4. Extracts country → locale mapping — **expanded from 50 to 132 countries** in 0.4.8
5. Sets `--fingerprint-timezone`, `--lang` and `--fingerprint-locale` binary flags rather than CDP emulation (`browser.py:1443-1455`)
6. **Auto-injects `--fingerprint-webrtc-ip`** to prevent WebRTC IP leaks (no extra cost)

Explicit timezone/locale always override auto-detection. Since 0.5.10, a requested resolution that fails (timeout, missing database, unresolved timezone or locale) **aborts the launch** instead of continuing; the default timeout is 20 s (was 5 s), configurable with `CLOAKBROWSER_GEOIP_TIMEOUT_SECONDS` (`browser.py:1330-1334`, `geoip.py:32-33`, `CHANGELOG.md:21`). WebRTC IP spoofing can also be used standalone: `args=["--fingerprint-webrtc-ip=auto"]` (resolves the proxy exit IP; requires a proxy, otherwise the flag is removed with a warning, `browser.py:1355-1358`) or `--fingerprint-webrtc-ip=1.2.3.4` (explicit, no network call).

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

`cloakserve` (`bin/cloakserve`) runs the binary as a CDP server (`docker run -d -p 127.0.0.1:9222:9222 cloakhq/cloakbrowser cloakserve`), rewrites the CDP WebSocket discovery URLs so clients connect through the proxy, and keeps per-seed process routing. It binds `0.0.0.0` inside a container and `127.0.0.1` otherwise (`bin/cloakserve:906-908`), starts each per-seed Chrome with `--remote-debugging-address=127.0.0.1` (`bin/cloakserve:374`), keeps idle cleanup off by default (`--idle-timeout`, `bin/cloakserve:184`) and exposes `POST /fingerprint/{seed}/close` (`bin/cloakserve:891`). `cloaktest` runs the bundled bot-detection smoke suite. Widevine/DRM is supported through an opt-in CDM fetch in the Docker entrypoint (`CLOAKBROWSER_FETCH_WIDEVINE`, `bin/docker-entrypoint.sh:29-33`) from Google's component server (`bin/fetch-widevine.py:38`); the wrapper itself only seeds the hint file for a CDM the user supplies (`cloakbrowser/widevine.py:1-20`).

---

## Test results — the author's own, mostly on the paid binary

> **Tier B throughout.** These are the maintainer's published results, not independent
> reproductions, and the strongest of them are stated for the Pro/current build. The binary is closed,
> so nothing in this table can be verified from source — only that it is claimed.

Results are for the **latest Pro/current build** unless noted. **Last tested by the author: Aug 2026 (Chromium 151)** (`README.md:220`).

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
| UA string | `HeadlessChrome` | **`Chrome/151.0.0.0`** | No headless leak |
| CDP detection | Detected | **Not detected** | `isAutomatedWithCDP: false` |
| TLS fingerprint | Mismatch | **Identical to Chrome** | ja3n/ja4/akamai match |
| Overall | — | **"Tested against 30+ detection sites"** | Author's claim |

> **How to read these:** these are the tool author's own reported results, not independent reproductions. The strongest ones (0.9 reCAPTCHA v3, FingerprintJS pass) are stated for the **Pro/current** build. The keyless **free** v146 binary passes the free-tier `cloaktest` suite (Sannysoft, Incolumitas, Rebrowser, deviceandbrowserinfo, BrowserScan, CreepJS lies/noise=false) but is not claimed to hit the Pro numbers. As always, real-world results depend heavily on IP reputation and per-site behavior.

### Known Acceptable Failures

| Test | Result | Why |
|------|--------|-----|
| WEBDRIVER spec (incolumitas) | False positive | Spec-level detection, expected |
| connectionRTT | Flagged | Datacenter latency, not browser fingerprint |

---

## Security Audit

> **Full audit:** [CloakBrowser Security Audit](https://github.com/pim97/cloakbrowser-analyze)
> **Audit date:** March 2026 | **Binary:** Chromium 145.0.7632.159.7 (Linux x64)

> **Caveat (2026-09):** the public audit was done on the **Chromium 145** binary. The current keyless free binary is **146** and the Pro binary is **152** (Linux/Windows) / **151** (macOS), none of which the audit covers. The audit's behavioral conclusions do not automatically transfer to the newer binaries, and its network results concern a keyless free binary: the README states that licensed binaries make license/session calls to cloakbrowser.dev (`README.md:755`; Tier B).

### Trust Model

| Component | Source Available | Can You Audit It? |
|-----------|:-:|---|
| Python wrapper (`cloakbrowser/`) | Yes (MIT) | Fully readable |
| JavaScript wrapper (`js/`) | Yes (MIT) | Fully readable |
| .NET/C# wrapper (`dotnet/`) | Yes (MIT) | Fully readable |
| Chromium binary (`chrome`) | **No** (Proprietary) | **Cannot inspect the C++ patches** |
| SHA-256 checksums | **Ed25519-signed** (pinned pubkey) | Authenticity now verifiable, not just integrity |

> **Improvement since the previous analysis:** the old "self-referential checksums" weakness is materially reduced. Since wrapper 0.4.0, `SHA256SUMS` carries a detached Ed25519 signature verified against a public key pinned in the wrapper source (`BINARY_SIGNING_PUBKEYS`). A compromised download mirror can no longer certify a tampered or downgraded binary. This establishes that the download originates from the holder of the pinned signing key. It does not make the closed-source patches readable.

### Network Behaviour Visible in the Wrapper (Tier A)

Outbound destinations found in the Python wrapper source; the JS and .NET wrappers use the same cloakbrowser.dev endpoints (`js/src/license.ts:16-18`, `dotnet/src/CloakBrowser/License.cs:84-86`):

| Destination | Purpose | Evidence |
|---|---|---|
| `cloakbrowser.dev` | Binary download (keyless and keyed), license validation (POST of the key), Pro version lookup, session-seat count, GitHub-sign-in start URL | `config.py:277-280`, `license.py:26-28`, `__main__.py:584` |
| `github.com`, `api.github.com` | Fallback binary and signed-manifest download; hourly latest-release check on the keyless path; GeoLite2 database mirror | `config.py:282-284`, `download.py:1151-1170`, `geoip.py:26-29` |
| `pypi.org` (npm registry in JS, NuGet in .NET) | Wrapper update check, once per process | `download.py:1205-1230`, `js/src/download.ts:1202`, `dotnet/src/CloakBrowser/Download.cs:1278` |
| `api.ipify.org`, `checkip.amazonaws.com`, `ifconfig.me` | Exit-IP lookup, only with `geoip=True` or `--fingerprint-webrtc-ip=auto` | `geoip.py:197-199` |
| `update.googleapis.com` | Widevine CDM fetch, only through `CLOAKBROWSER_FETCH_WIDEVINE` / `bin/fetch-widevine.py` | `bin/fetch-widevine.py:38` |

A search of `cloakbrowser/`, `js/src/`, `dotnet/src/` and `bin/` for `telemetry`, `analytics`, `posthog`, `sentry`, `beacon`, `mixpanel`, `amplitude` and `datadog` returns no matches. `CLOAKBROWSER_AUTO_UPDATE=false` disables the PyPI and release checks (`download.py:1133, 1211`) but not license validation. The binary's own network behavior is outside what the wrapper shows; the README states that licensed (Pro) binaries contact cloakbrowser.dev for license and session calls (`README.md:755`; Tier B).

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

The binary behaved legitimately in all tests, but it remains closed-source, and the audited version (145) is now behind the shipping versions (146 keyless free / 152 Pro). The license prohibits reverse engineering. Separately, the wrapper's default arguments include `--no-sandbox` (see [How It Works §1](#1-fingerprint-seed-system)).

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
| **C++ Chromium patches** | 87 source-level modifications stated for the latest Pro binaries (Chromium 152); vendor-stated, not JS injection or config flags |
| **Chromium engine** | TLS fingerprint reported to match real Chrome (Tier B) |
| **Drop-in Playwright/Puppeteer** | Same API — swap the import, keep your code |
| **`humanize=True`** | One flag for Bézier mouse, typing simulation, scroll patterns |
| **0.9 reCAPTCHA v3** (Pro) | Vendor-reported score on the Pro/current build (Tier B) |
| **Multi-language** | Python + Node.js (TypeScript) + **.NET 8 / C#** with full type definitions |
| **Cross-platform** | Linux x64/arm64, macOS arm64/x64, Windows x64 |
| **Platform-aware defaults** | macOS runs native; Linux/Windows use a Windows persona automatically |
| **Coherent seed identity** | Screen/GPU/RAM/CPU/fonts/audio chosen together as a plausible real device |
| **Signed downloads** | Pinned Ed25519 signature on checksums — authenticity, not just integrity |
| **GeoIP + WebRTC coherence** | Timezone/locale/WebRTC-IP from proxy or own IP (132 countries) |
| **Framework integrations** | browser-use, Crawl4AI, Crawlee, Scrapling, Stagehand, LangChain, Selenium, UC |
| **`cloakserve` CDP server** | Per-seed CDP routing for framework/Docker deployments |
| **Version pinning/rollback** | `browser_version=` / `CLOAKBROWSER_VERSION` for keyless Free and paid keys; ignored with a free GitHub key (`download.py:231-232`) |
| **Widevine/DRM** | Opt-in CDM auto-fetch for persistent contexts |
| **Persistent profiles** | Cookies/localStorage across sessions |
| **Zero config** | Launch sets the seed and platform flags; no arguments required |

### Disadvantages

| Con | Details |
|-----|---------|
| **Closed-source binary** | Proprietary Chromium — cannot verify the C++ patches |
| **Best results are paid** | 0.9 reCAPTCHA v3 / FingerprintJS pass are stated for the Pro/current build; the keyless free binary is v146 and the README says it "ages fast"; a free GitHub-sign-in key (one concurrent session) provides the latest build |
| **Audit lags shipping version** | Public audit covers Chromium 145; keyless free is 146, Pro is 152 |
| **`--no-sandbox`** | Runs with the Chromium sandbox disabled by default (`config.py:64`); `stealth_args=False` omits the default list |
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

### License Key (Free GitHub Key or Pro)

```python
# Pass a key, or set CLOAKBROWSER_LICENSE_KEY / ~/.cloakbrowser/license.key
browser = launch(license_key="cb_xxxxxxxx")
```

`cloakbrowser login` saves a key to `~/.cloakbrowser/license.key` or opens a GitHub sign-in to obtain a free key; `cloakbrowser logout` removes it (`cloakbrowser/__main__.py:584-676`).

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
browser = launch(browser_version="146.0.7680.177.5")
```

### CLI / Docker

```bash
# Sign in with GitHub for a free key, or save a paid key
cloakbrowser login

# Diagnostics: which binary launches, license tier, session seats, fonts, geoip, deps
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
- Launches that need no manual fingerprint flags (the wrapper sets seed and platform)
- Humanized input (`humanize=True`) for mouse, typing and scroll
- Sites with reCAPTCHA v3 scoring (the 0.9 score is vendor-reported for the Pro/current build)
- AI-agent / framework stacks (browser-use, Crawl4AI, Stagehand, LangChain, Scrapling)
- Persistent sessions with fingerprint consistency
- Docker/VPS/Lambda deployments (a Docker image, `cloakserve` and an AWS Lambda example ship in the repo)

### Not Recommended For

- Security-critical environments (closed-source binary; sandbox disabled by default)
- Need to audit every component (use Camoufox, Clearcote, or Patchright)
- CAPTCHA solving (use SeleniumBase)
- Statistical fingerprint rotation (Camoufox draws statistical identities with fpgen)
- Projects that cannot use a license key but need the newest patches (the keyless free binary is Chromium 146)
- Minimal footprint (~200MB binary)

---

## Key Files

| File | Purpose |
|------|---------|
| `cloakbrowser/_version.py` | Wrapper version (`0.5.11`) |
| `cloakbrowser/config.py` | Stealth args, platform detection, seed, Chromium version map, signed-download config |
| `cloakbrowser/browser.py` | `launch()`, `launch_async()`, `launch_context()`, `launch_persistent_context()` |
| `cloakbrowser/__main__.py` | CLI: `install`, `info` / `doctor`, `update`, `clear-cache`, `login`, `logout` |
| `cloakbrowser/download.py` | Binary download, Ed25519-signed verification, auto-update, keyless / keyed routing |
| `cloakbrowser/license.py` | License validation/caching, session seats, denial-code mapping, Pro version check |
| `cloakbrowser/geoip.py` | MaxMind GeoIP timezone/locale + WebRTC-IP detection |
| `cloakbrowser/widevine.py` | Widevine CDM handling for DRM playback |
| `cloakbrowser/human/mouse.py` | Bézier curve movement, click targeting, overshoot |
| `cloakbrowser/human/keyboard.py` | Per-character typing, typo simulation, shift handling |
| `cloakbrowser/human/scroll.py` | Accelerate → cruise → decelerate scroll physics |
| `cloakbrowser/human/config.py` | `HumanConfig` dataclass, `default` / `careful` presets |
| `cloakbrowser/human/stealth_dom.py` | Isolated-world DOM reads and the supported selector-grammar subset |
| `cloakbrowser/human/actionability.py` | Pre-action checks (attached, visible, stable, enabled, editable, receives events) |
| `js/src/` | Node.js/TypeScript wrapper (Playwright + Puppeteer + human) |
| `dotnet/src/CloakBrowser/` | .NET 8 / C# wrapper (NuGet `CloakBrowser`) |
| `bin/cloakserve` | CDP multiplexer: one Chrome process per fingerprint seed |
| `CHANGELOG.md` | Full wrapper + binary changelog |
| `BINARY-LICENSE.md` | Proprietary binary license (v1.3, July 2026) |

---

## Comparison

| Feature | CloakBrowser | Camoufox | Patchright | SeleniumBase | Botasaurus |
|---------|:----------:|:--------:|:----------:|:------------:|:----------:|
| Spoofing Level | C++ (Chromium) | C++ (Firefox) | Driver source patch (TypeScript) | Config + UC | JS wrapper |
| Browser | Chromium | Firefox | Chromium | Chrome | Chrome |
| Playwright API | ✅ Native | Via Juggler | ✅ Native | ❌ Selenium | ❌ Selenium |
| Fingerprint Rotation | Seed-based | ✅ fpgen (repo HEAD) | ❌ None in driver source | Partial | Partial |
| Human input simulation | `humanize` (Bézier + typing; wrapper source, Tier A) | `humanize` config | none | PyAutoGUI clicks + jitter | Bézier + Gaussian noise |
| CAPTCHA handling | none | none | none | click-solving, several vendors | Cloudflare challenge only |
| Languages | Py / JS / .NET | Python | Py / JS / .NET | Python | Python |
| Source Available | Wrapper only | Fully open | Fully open | Fully open | Fully open |

---

## Conclusion

CloakBrowser modifies Chromium at the C++ source level (vendor-stated: **87 patches** on the latest Pro binaries, 58 on the keyless free binary), and the author reports passes on major detection services including reCAPTCHA v3 (0.9 score) and Cloudflare Turnstile (Tier B). Since the last analysis it has added a **free GitHub-sign-in key tier**, a **.NET/C# client**, **coherent seed-built hardware identities**, **Ed25519-signed downloads**, **WebRTC-IP coherence**, **132-country GeoIP**, **version pinning/rollback**, **Widevine/DRM**, a **macOS persona**, and a broad set of **AI-agent/framework integrations**.

The `humanize=True` flag adds behavioral simulation (Bézier mouse curves, typing with typos, scroll physics) in readable wrapper code; the layer reads the DOM in a CDP isolated world and supports a subset of Playwright's selector grammar.

**The trade-offs.** The Chromium binary is **closed-source** and proprietary, and the newest builds are delivered through license keys (a free key limited to one concurrent session, and paid plans); the keyless free binary (Chromium 146) is older. The public security audit (9/9 tests passed, no malicious behavior found) covers the **older Chromium 145** binary, not the 146/151/152 builds now shipping, so its conclusions do not fully transfer. The Ed25519 signing closes the old self-referential-checksum gap, but it proves authenticity, not what the patches do. The wrapper's default arguments include `--no-sandbox`.

**Applicability:** Chromium automation via the Playwright or Puppeteer API where engine-level fingerprint control and built-in humanized input are required and a closed binary is acceptable. The published figures (reCAPTCHA v3 0.9, FingerprintJS pass) are Tier B and stated for the Pro/current build.

**Constraints:** the engine is proprietary — the 87 patches cannot be read or independently verified, and the MIT license covers only the wrapper. Free and Pro binaries differ in Chromium version (146 vs 152) and patch count (58 vs 87). The independent audit covered Chromium 145, which no current binary matches. CloakBrowser's engine source is unpublished (the repository contains the wrapper only); Camoufox, Clearcote, and Obscura publish theirs.

---

*Analysis conducted for educational purposes. Use responsibly.*
