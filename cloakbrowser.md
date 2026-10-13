# CloakBrowser - Deep Technical Analysis

> **Tool Type:** Custom Chromium Build (Anti-Detect Browser)
> **Repository:** [github.com/CloakHQ/CloakBrowser](https://github.com/CloakHQ/CloakBrowser)
> **Approach:** C++ source-level fingerprint patches + CDP input behavior mimicking
> **Language:** Python, Node.js (TypeScript), .NET (C#)
> **What is verified:** the wrapper source (default arguments, download and signature verification, license handling, humanize module) read at the commit below (**Tier A**), plus the patch counts and platform matrix read from the project's own README (**Tier A** that they are *claimed*; the binary itself is closed, so what the patches do cannot be verified here)
> **Anti-bot service claims:** Turnstile, FingerprintJS, **reCAPTCHA v3 score 0.9**, "tested against 30+ detection sites" — all **Tier B**, stated for the README's "latest Pro/current build". The keyless free binary (Chromium 146) is not claimed to reach these numbers.
> **Maintenance:** wrapper **0.6.2** (2026-10-12); latest GitHub release `chromium-v154.0.8037.57.1-pro` (2026-10-06); last push 2026-10-13. 32.1k stars, 2.7k forks, 23 contributors, 244 open issues. MIT wrapper, **proprietary binary**.
> **Verified:** 2026-10-13 against `CloakHQ/CloakBrowser` @ `485f678` (0.6.2 plus two later commits; previous revision `f44864b`, 2026-09-30).

> ### Patch counts — current as of 2026-10-13
>
> | Platform | Free | Pro |
> |---|---|---|
> | Linux x86_64 / arm64 | Chromium 146 (**58** patches) | Chromium 154 (**87** patches) |
> | Windows x86_64 | Chromium 146 (**58** patches) | Chromium 154 (**87** patches) |
> | macOS arm64 / x86_64 | Chromium 145 (**26** patches) | Chromium 154 (**87** patches) |
>
> Source: the vendor README (`README.md:897-901`). The Free column is the binary the wrapper downloads without a key (`cloakbrowser/config.py:25-31`); the README separately offers the latest build on a free GitHub-sign-in key (see [Free vs Pro](#free-vs-pro-delayed-free-release-model)) and states no patch count for it.
> Earlier revisions of this report cited "33", "66" (Chromium 148) and "71" (Chromium 150); all are superseded. The count stayed at 87 when Pro moved from Chromium 152 (151 on macOS) to 154 on every platform (0.6.0). **Patch count is a measure of surface area
> touched, not of quality** — it is not comparable across projects that split changes
> differently.

---

## Table of Contents

- [What is CloakBrowser?](#what-is-cloakbrowser)
- [Current State (2026-10)](#current-state-2026-10)
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

**What changed since the last analysis:** the tool has moved fast. The patch count has grown (33 → 66 → 71 → **87** on the newest binaries), Chromium has advanced (145 → **146 keyless free / 154 Pro**, macOS included), a **keyed tier** now gates the newest binary (a **free GitHub-sign-in key** limited to one concurrent session, and paid plans), a **.NET/C# client** was added alongside Python and Node.js, and binary downloads are protected by a **pinned Ed25519 signature** rather than the old self-referential checksums. Since 0.6.0 the `humanize` layer runs on one engine built on Playwright's own selector engine, and persistent profiles keep one fingerprint seed. See [Current State](#current-state-2026-10).

---

## Current State (2026-10)

Verified against the repo source and release history (repo read at `485f678`, 2026-10-13; previous revisions `f44864b`, 2026-09-29, and `2488311`, 2026-08-11):

| Fact | Value | Evidence |
|------|-------|----------|
| Wrapper version | **0.6.2** (2026-10-12); one unreleased code commit after it (async launches, below) | `cloakbrowser/_version.py:1`, `js/package.json:3`, `dotnet/src/CloakBrowser/CloakBrowser.csproj:13`, PyPI / npm |
| Free binary (keyless default) | **Chromium 146.0.7680.177.5** (Linux/Windows x64), 146.0.7680.177.3 (Linux arm64), 145.0.7632.109.2 (macOS) | `cloakbrowser/config.py:25-31` → `PLATFORM_CHROMIUM_VERSIONS` (unchanged since `2488311`) |
| Free binary with GitHub-sign-in key | "Latest build", one concurrent session; `cloakbrowser login` (since 0.5.0). The README names Chromium 154 for this tier | `README.md:190-197`, `cloakbrowser/__main__.py:584-660`, `cloakbrowser/download.py:234-253`, CHANGELOG 0.5.0 |
| Pro binary (latest) | **Chromium 154.0.8037.57.1** on every platform (Linux x64/arm64, Windows x64, macOS arm64/x64; macOS moved up from 151). Linux Preview channel: 154.0.8037.57.2 | GitHub release `chromium-v154.0.8037.57.1-pro` (2026-10-06); `README.md:153-158`; CHANGELOG 0.6.0 |
| C++ patch count | **87** on Chromium 154 (Pro); **58** on 146 (free); **26** on macOS 145 | `README.md:39`, `README.md:289`, `README.md:897-901` |
| CDP input mimicking | Included in the patch set (input behavior mimicking) | README "How It Works" (`README.md:289`) |
| Languages | Python (≥3.9; depends on `playwright>=1.53` since 0.6.0, was `>=1.40`), Node.js/TypeScript (20.19+ or 22.12+ since 0.6.0, which also added CommonJS `require()`), **.NET 8 / C# (NuGet; contributed by an outside author in PR #385, CHANGELOG 0.4.3)** | `pyproject.toml:11`, `pyproject.toml:52`, `js/package.json:57-59`, `dotnet/src/CloakBrowser/CloakBrowser.csproj:4`, `CHANGELOG.md:237-239` |
| License (wrapper) | **MIT** | `LICENSE`, `pyproject.toml:10` |
| License (binary) | Proprietary (`BINARY-LICENSE.md` v1.3, July 2026): the latest major requires a subscription at a tier CloakHQ designates; other versions stay under the same restrictions | `BINARY-LICENSE.md` ("Version-Specific Terms", "Restrictions") |
| Platforms | Linux x64/arm64, macOS arm64/x64, Windows x64 | `cloakbrowser/config.py:192-199` → `SUPPORTED_PLATFORMS` |
| Maintenance | Last push 2026-10-13; 23 contributors, 244 open issues, 32,143 stars | GitHub API (`STATUS.md`) |
| Last tested (by author) | Oct 2026 (Chromium 154) | `README.md:220` |

> **Note on patch counts:** there is no single number. The patch count is versioned to the binary: the newest Pro builds (Chromium 154 on every platform) are stated as **87**, the keyless free build (146) as **58**, and the older macOS free build (145) as **26**. The "33" figure from an earlier analysis and the "71" figure from the 2026-08-14 revision are outdated.

> **Free-key version:** `README.md:190` names Chromium 154 for the free-key tier, the same major as Pro Stable (`README.md:153`); at `f44864b` the README named 151 for the free key and 152 for Pro. The wrapper selects the binary the same way for free and paid keys (`cloakbrowser/download.py:411-414`), so the build a free key resolves to is decided server-side and is not established here (Tier D).

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
│  │  Pro:  Chromium 154 (87 patches)             │                │
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
2. **First launch** → binary auto-downloads for your platform (no key: free Chromium 146; with a free or paid license key: the latest keyed build, Pro Stable being Chromium 154 on every platform)
3. **Every launch** → Playwright or Puppeteer starts with the CloakBrowser binary + stealth args
4. **You write code** → standard Playwright/Puppeteer API, nothing new to learn

### 1. Fingerprint Seed System

Every launch generates a **random seed** (`--fingerprint=<10000..99999>`, `config.py:59`) that deterministically controls all fingerprint values. Same seed = same fingerprint across launches (useful for returning-visitor patterns; the README explicitly recommends a fixed seed when hitting the same site repeatedly).

**Persistent profiles keep their seed (0.6.0, behaviour change).** `launch_persistent_context()` stores the seed in `<user_data_dir>/.cloakbrowser-seed` on first launch and reuses it afterwards; an explicit `--fingerprint=` in `args` or `stealth_args=False` leaves the file alone, a corrupt file is replaced with a warning, and concurrent first launches agree on one seed through an exclusive hard link (`config.py:63-152`, `browser.py:659`). The file format is shared with the JS and .NET wrappers. Non-persistent launches stay random. Deleting the file rotates the identity (`README.md:420`).

The stealth-args builder is now much leaner than in earlier versions. From `cloakbrowser/config.py:155-177` (comments abridged):

```python
def get_default_stealth_args() -> list[str]:
    """Build stealth args with a random fingerprint seed per launch.

    On macOS, skips platform/GPU spoofing — runs as a native Mac browser.
    Spoofing Windows on Mac creates detectable mismatches (fonts, GPU, etc.).
    """
    seed = _random_seed()  # SEED_MIN..SEED_MAX = 10000..99999
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

**`--no-sandbox` default:** `--no-sandbox` is the first entry of the default list (`config.py:165`) in the Python, JavaScript (`js/src/config.ts:433`) and .NET (`dotnet/src/CloakBrowser/Config.cs:207`) wrappers, and `cloakserve` builds its Chrome arguments from the same list (`bin/cloakserve:354-355`). Caller `args` can override a flag but cannot remove it (`browser.py:1455-1460`); `stealth_args=False` omits the whole default list, and the README shows supplying `--fingerprint` and `--fingerprint-platform` manually in that case (`README.md:822-825`). The README does not mention the flag; CHANGELOG 0.5.2 records that the binary stops showing an unsupported-flag warning bar when the sandbox is disabled, which it describes as required when running as root, for example in Docker (`CHANGELOG.md:157`). Unchanged at `485f678`.

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
| Storage quota | Normalized by default (also hides the real disk size); `--fingerprint-storage-quota` overrides it. The README notes BrowserScan's incognito check reads the default as incognito (`README.md:454`, `README.md:751`) |

Patch counts by binary (`README.md:897-901`):

| Platform | Free binary | Pro binary |
|----------|-------------|------------|
| Linux x86_64 | Chromium 146 (**58 patches**) | Chromium 154 (**87 patches**) |
| Linux arm64 | Chromium 146 (58) | Chromium 154 (87) |
| macOS arm64 / x86_64 | Chromium 145 (**26 patches**) | Chromium 154 (87) |
| Windows x86_64 | Chromium 146 (58) | Chromium 154 (87) |

**Properties the vendor reports for the patched binary (Tier B):**
- `navigator.webdriver` returns `false`
- `navigator.plugins.length` returns `5`
- `window.chrome` is present as an `object`
- User-Agent has no `HeadlessChrome` leak (the README test table still shows `Chrome/151.0.0.0` although its header now says Oct 2026, Chromium 154; `README.md:220`, `README.md:235`)
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
    → first launch triggers binary resolution (ensure_binary, download.py:194)
    → no key: downloads the free binary (Chromium 146) from cloakbrowser.dev,
      falling back to GitHub Releases (download.py:371-380)
    → license key set (free GitHub key or paid): POSTs the key to
      cloakbrowser.dev/api/license/validate, then downloads the latest build from
      cloakbrowser.dev/api/download/<version> with the key as a bearer token
      (download.py:234-253, 540-575)
    → fetches SHA256SUMS + detached SHA256SUMS.sig
    → verifies the Ed25519 signature against a PINNED public key, checks that the
      signed manifest's version= line matches the requested version, then verifies
      the file hash against the signed manifest (download.py:643-713)
    → extracts into a private staging dir, then renames it to
      ~/.cloakbrowser/chromium-{version}[-pro]/ (download.py:906-966)
    → background update check (rate-limited to once per hour, download.py:68, 1319-1330)
```

> **Changed since the previous analysis:** downloads are no longer protected only by same-origin checksums. Since 0.4.0, the wrapper verifies a **pinned Ed25519 signature** (`BINARY_SIGNING_PUBKEYS`, `config.py:42-44`; one key is pinned) on the published `SHA256SUMS`, and the signed manifest's `version=` line must match the requested version, so a mirror cannot substitute a genuinely signed older build (`download.py:694-704`). Verification is mandatory on the official and Pro download paths. `CLOAKBROWSER_SKIP_CHECKSUM` and `CLOAKBROWSER_DOWNLOAD_URL` apply only to a self-hosted origin, where the Pro path and background updates are switched off (`download.py:231-232, 643-680, 1188`). This closes the "self-referential checksums" gap the earlier audit flagged.

> **Extraction (0.5.11, 0.6.0):** once the signature and checksum verify, archives are unpacked directly with `tarfile.extractall(filter="fully_trusted")` and `zipfile.extractall`; the earlier per-entry path-traversal and symlink screening was removed in 0.5.11 (`download.py:986-1002`, `CHANGELOG.md:70`). The trust boundary for extraction is therefore the signature check. Since 0.6.0 each download extracts into its own `<dir>.partial-<uuid>` staging directory that is renamed into place (the first complete install wins; Windows renames are retried for about 2.5 s), so concurrent first launches no longer delete each other's half-written install (`download.py:906-984`; CHANGELOG 0.6.0, #555).

The README also documents manual verification (`README.md:1432-1449`): a GPG-signed release tag, GitHub/Sigstore build attestation for the binary archives, and a Cosign signature for the Docker image (vendor-documented, Tier B). The repository contains the workflows for the last two: `.github/workflows/attest-release.yml` (manual dispatch, attests release archives) and `.github/workflows/publish.yml:155-159` (Cosign signing and attestation of the Docker image).

Binary size: ~200MB compressed download (`README.md:127`), cached under `~/.cloakbrowser/`. Runtime footprint (`README.md:1078`): ~190MB RAM idle, ~280MB with 3 tabs, ~30MB per additional tab.

---

## Free vs Pro (Delayed Free-Release Model)

The **wrapper (Python + JS + .NET) is MIT.** The **binary** is proprietary (`BINARY-LICENSE.md` v1.3, July 2026) and is delivered in three ways, selected by the key the wrapper resolves:

| Tier | Binary | Where | Notes |
|------|--------|-------|-------|
| **Free, no key** | Chromium **146** (58 patches); 145 (26) on macOS | cloakbrowser.dev, GitHub Releases as fallback | Auto-downloads, no key. The README says this older build "ages fast as detection evolves" (`README.md:192`); the launch banner invites the free login (`download.py:173-184`) |
| **Free, GitHub-sign-in key** | "Latest build" (README names Chromium 154, see [Current State](#current-state-2026-10)) | cloakbrowser.dev (`/api/download/<version>`, key as bearer token) | `cloakbrowser login` opens a GitHub sign-in and the key is emailed to the GitHub address (`__main__.py:601-615`); **one concurrent session**; a version pin is ignored for this plan (`download.py:241-242`) |
| **Pro, paid key** | Chromium **154.0.8037.57.1** (all platforms); 87 patches | cloakbrowser.dev | Newest patches first; the README lists plans of 5, 20, 200 or 2,000+ concurrent sessions (`README.md:191`). Set `license_key` / `CLOAKBROWSER_LICENSE_KEY` / `~/.cloakbrowser/license.key` |

- **Key handling.** Resolution order is explicit parameter, then `CLOAKBROWSER_LICENSE_KEY`, then `license.key` in the cache directory (`cloakbrowser/license.py:266-296`). Keys are opaque strings to the wrapper (no format is enforced); validation is a POST to `cloakbrowser.dev/api/license/validate` (`license.py:26, 403-408`), cached locally for 24h keyed by a SHA-256 of the key (`license.py:30, 396-399, 626-638`), and a stale cache is used if the server is unreachable (`license.py:425-428`). `cloakbrowser info` reports the plan (default `solo` when the server omits it, `license.py:414`) as `tier` (`__main__.py:144`) and, for keyed plans, live session seats as used/limit (`__main__.py:267-278`, `license.py:521-573`).
- **Server-side enforcement.** The wrapper comments state that the server enforces the concurrency cap (`download.py:411-414`). The Pro binary reports license denials through process exit codes 76-79 (`license.py:102-123`) and, for denials after the CDP handshake, a per-launch status file named by `CLOAKBROWSER_LICENSE_STATUS_FILE` (`license.py:147-154, 231-246`), which the wrapper converts to `CloakBrowserLicenseError`; since 0.6.1 the JS Puppeteer and .NET launchers also read that file when a launch fails, instead of surfacing a raw launch crash. The session-limit message (code 76) now states that a crashed or killed session frees its seat within 4 min (free/trial/solo), 15 min (team) or 30 min (business/scale), and code 79 also names an invalid `--license-route` value (`license.py:103-121`); `--license-route=auto|direct|proxy` is a flag of the 154 Preview binary per CHANGELOG 0.6.0 (Tier B). These are wrapper-side facts (Tier A); what the binary does is Tier B.
- **No silent downgrade.** A key the server rejects, or one that cannot be validated (server unreachable and no cached result), now raises `CloakBrowserLicenseError` instead of falling back to the free binary (`download.py:266-279`; CHANGELOG 0.5.10, `CHANGELOG.md:79`). A valid key also hard-fails on a download or signature error (`download.py:247-265`).
- **Test claims.** The Pro test claims (0.9 reCAPTCHA v3, FingerprintJS pass) are labeled "Pro/current build" in the README (`README.md:220-228`); the keyless free v146 binary is not claimed to hit them. As of 0.4.7 the public Docker `cloaktest` suite uses free-tier-stable checks (Sannysoft, Incolumitas, Rebrowser, deviceandbrowserinfo, BrowserScan, CreepJS lies/noise=false); FingerprintJS and reCAPTCHA v3 are not hard-pass checks for the free image (`CHANGELOG.md:218`).
- **Release channel.** Since 0.5.2 `release_channel="preview"` / `CLOAKBROWSER_RELEASE_CHANNEL=preview` selects the newest build available for the platform and falls back to Stable (`config.py:208-215`, `CHANGELOG.md:147`).
- **Version pinning.** Since `485f678` the README documents `browser_version=` / `CLOAKBROWSER_VERSION` as paid-key only (`README.md:692`, `README.md:1299`; at `f44864b` it said the pin worked for Free and Pro). In the wrapper code a free GitHub key drops the pin (`download.py:241-242`), while the keyless path still downloads and launches a pinned public build (`download.py:284-305`); that commit changed documentation only.
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
- **2%** mistype chance (`mistype_chance = 0.02`) — types a keyboard-layout-adjacent key, then backspace-corrects with a "notice" delay (100–300ms) before correction (50–150ms). Digit typos stay digits (0.5.12, `human/keyboard.py:32-35`); typos are skipped in number, email, password, tel and url inputs (`human/fields.py:56-60`), and a typo the page rejects is not corrected (`human/engine.py:1085-1103`)
- **10%** thinking-pause chance (`typing_pause_chance = 0.1`, 400–1000ms; `careful` = 15%, 500–1200ms)
- Different handling for uppercase (Shift down → char → Shift up), shift-symbols, and normal chars; individual key hold durations
- Non-ASCII characters (Cyrillic, CJK, emoji) use an `insertText` fallback
- Shift-symbols are sent through CDP `Input.dispatchKeyEvent` (`human/engine.py:1111-1139`). The `page.evaluate` fallback that the source comments call detectable remains only in the exported `human_type` helper (`human/keyboard.py:125-183`), which the 0.6.0 engine does not call

### Selector Handling and Patched Methods (engine rewritten in 0.6.0)

Since 0.6.0 every humanized action in Python, JavaScript (Playwright) and .NET runs through one engine (`cloakbrowser/human/engine.py`, `js/src/human/engine.ts`, `dotnet/src/CloakBrowser/Human/HumanEngine.cs`; CHANGELOG 0.6.0, #578). The 0.5.x modules `stealth_dom.py`, `actionability.py` and `scroll.py` were removed. The engine creates a CDP isolated world per frame (`Page.createIsolatedWorld`, `human/world.py:412-428`) and evaluates Playwright's own InjectedScript there, extracted from the installed Playwright driver bundle (`human/injected.py:1-12`):

- **Selectors:** full Playwright selector syntax, including `get_by_role`, `>>` chains, `filter(has=/has_text=)`, `:visible`, `nth` and `frame_locator`. Strict mode applies: an ambiguous locator raises `strict mode violation` instead of using the first match (`human/world.py:99-106`; behaviour change in 0.6.0). Through 0.5.x the layer used its own subset of the grammar and rejected `get_by_role`, chained locators and `frame_locator`; `UnsupportedHumanizeSelectorError` and the other 0.5.x error classes stay importable, but actions no longer raise them (`human/__init__.py:23-28`).
- **Pipeline:** resolve, then wait for element states (visible, enabled, editable, stable), then scroll into view with mouse-wheel bursts on both axes, then a Bézier move, then a hit-target check through every ancestor `<iframe>`, then press or type (`human/engine.py:1-14`). Failures raise Playwright `Error` / `TimeoutError` with a call log (for example `... intercepts pointer events`, `element is outside of the viewport`) instead of falling back to Playwright's stock action. The one exception: an `ElementHandle` read or `dispatch_event` on an element the isolated world cannot uniquely locate runs Playwright's own call (`RawFallback`, `human/patch.py:14-18`, `human/engine.py:262-290`).
- **Patching (Python):** class-level on Playwright's `Page`, `Frame`, `Locator`, `ElementHandle`, `Mouse` and `Keyboard`; each wrapper checks whether its page was humanized and otherwise calls the original method (`human/patch.py:1-6, 293-349`). Patched: `click`, `dblclick`, `hover`, `tap`, `fill`, `type`, `press`, `check`, `uncheck`, `set_checked`, `select_option`, `focus`, the element reads `input_value`, `text_content`, `inner_text`, `inner_html`, `get_attribute` and `dispatch_event` (0.6.1), `drag_and_drop` (page, frame), `clear`, `press_sequentially`, `drag_to` (locator), `scroll_into_view_if_needed`, `mouse.move` / `click` / `dblclick` and `keyboard.type` (`human/patch.py:163-286`). `goto` is no longer wrapped. `page._original` gives the raw Playwright calls and `page._stealth_world.evaluate()` evaluates in the isolated world (`human/patch.py:357-400`).
- **Requirements:** Playwright 1.53 or newer; on an older or internals-incompatible Playwright, `humanize=True` raises instead of running actions un-humanized (`human/patch.py:63-101`). 0.6.1 accepted compiled (Nuitka) Playwright builds; 0.6.2 fixed humanized actions timing out with `element is not visible` on Playwright 1.64 (CHANGELOG 0.6.1, 0.6.2).
- **Value fields (0.6.0, 0.6.1):** date and time inputs are typed part by part in the locale's order, sliders are clicked and nudged with arrow keys, `select_option` opens the dropdown and uses type-ahead plus arrow keys (on a macOS host the label is typed; emoji-led labels raise there), and `fill()` on `<input type=color>` raises. Select-all and `ControlOrMeta` follow the persona (`--fingerprint-platform=macos` uses Meta), not the host OS.
- **Removed in 0.6.0 (Python):** `scroll_to_element`, `human_scroll_into_view`, the `async_human_*` helpers, the `RawMouse` / `RawKeyboard` re-exports and `ensure_actionable` / `ensure_stable` / `check_pointer_events` (CHANGELOG 0.6.0).

### Interaction Summary

| Interaction | Default Playwright | With `humanize=True` |
|---|---|---|
| Mouse movement | Instant teleport | Bézier curve with easing and overshoot |
| Clicks | Instant | Aim delay (inputs 60–140ms / buttons 80–200ms) + hold duration |
| Keyboard | Instant fill | Per-character with 70ms ± 40ms variance |
| Scroll | Jump | Mouse-wheel bursts: accelerate → cruise → decelerate (`human/engine.py:496-525`) |
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
5. Sets `--fingerprint-timezone`, `--lang` and `--fingerprint-locale` binary flags rather than CDP emulation (`browser.py:1474-1486`)
6. **Auto-injects `--fingerprint-webrtc-ip`** to prevent WebRTC IP leaks (no extra cost)

Explicit timezone/locale always override auto-detection. Since 0.5.10, a requested resolution that fails (timeout, missing database, unresolved timezone or locale) **aborts the launch** instead of continuing; the default timeout is 20 s (was 5 s), configurable with `CLOAKBROWSER_GEOIP_TIMEOUT_SECONDS` (`browser.py:1361-1365`, `geoip.py:32-33`, `CHANGELOG.md:78`). After 0.6.2 (commit `89fb671`, unreleased), the async launchers run the binary/license check and the GeoIP and WebRTC exit-IP lookups in a worker thread instead of on the caller's event loop (`browser.py:513-516`, `browser.py:826-829`). WebRTC IP spoofing can also be used standalone: `args=["--fingerprint-webrtc-ip=auto"]` (resolves the proxy exit IP; requires a proxy, otherwise the flag is removed with a warning, `browser.py:1386-1389`) or `--fingerprint-webrtc-ip=1.2.3.4` (explicit, no network call).

**Proxy and Playwright's request client (0.6.0).** A SOCKS5 or credentialed HTTP proxy is passed to the browser as `--proxy-server`, so `context.request`, `page.request` and `route.fetch()` do not use it and send from the machine's own IP. The wrapper logs a one-time warning when they are used (`browser.py:434-438`, `browser.py:1774`; #579), and the README suggests an in-page `fetch()` instead.

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

`cloakserve` (`bin/cloakserve`) runs the binary as a CDP server (`docker run -d -p 127.0.0.1:9222:9222 cloakhq/cloakbrowser cloakserve`), rewrites the CDP WebSocket discovery URLs so clients connect through the proxy, and keeps per-seed process routing. It binds `0.0.0.0` inside a container and `127.0.0.1` otherwise (`bin/cloakserve:908-910`), starts each per-seed Chrome with `--remote-debugging-address=127.0.0.1` (`bin/cloakserve:374`), keeps idle cleanup off by default (`--idle-timeout`, `bin/cloakserve:184`) and exposes `POST /fingerprint/{seed}/close` (`bin/cloakserve:893`). Since 0.6.0 a browser started through `/json/version` or `/json/list` with no WebSocket client attached is also scheduled for idle cleanup (`bin/cloakserve:410-411`, #558). `cloaktest` runs the bundled bot-detection smoke suite. Widevine/DRM is supported through an opt-in CDM fetch in the Docker entrypoint (`CLOAKBROWSER_FETCH_WIDEVINE`, `bin/docker-entrypoint.sh:29-33`) from Google's component server (`bin/fetch-widevine.py:38`); the wrapper itself only seeds the hint file for a CDM the user supplies (`cloakbrowser/widevine.py:1-20`).

---

## Test results — the author's own, mostly on the paid binary

> **Tier B throughout.** These are the maintainer's published results, not independent
> reproductions, and the strongest of them are stated for the Pro/current build. The binary is closed,
> so nothing in this table can be verified from source — only that it is claimed.

Results are for the **latest Pro/current build** unless noted. **Last tested by the author: Oct 2026 (Chromium 154)** (`README.md:220`).

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
| UA string | `HeadlessChrome` | **`Chrome/151.0.0.0`** | No headless leak; row not updated for the Oct 2026 run |
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

> **Caveat (2026-10):** the public audit was done on the **Chromium 145** binary. The current keyless free binary is **146** and the Pro binary is **154** on every platform, none of which the audit covers. The audit's behavioral conclusions do not automatically transfer to the newer binaries, and its network results concern a keyless free binary: the README states that licensed binaries make license/session calls to cloakbrowser.dev (`README.md:759`; Tier B).

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
| `cloakbrowser.dev` | Binary download (keyless and keyed), license validation (POST of the key), Pro version lookup, session-seat count, GitHub-sign-in start URL | `config.py:378-381`, `license.py:26-28`, `__main__.py:584` |
| `github.com`, `api.github.com` | Fallback binary and signed-manifest download; hourly latest-release check on the keyless path; GeoLite2 database mirror | `config.py:383-385`, `download.py:1202-1221`, `geoip.py:26-29` |
| `pypi.org` (npm registry in JS, NuGet in .NET) | Wrapper update check, once per process | `download.py:1256-1281`, `js/src/download.ts:1266`, `dotnet/src/CloakBrowser/Download.cs:1362` |
| `api.ipify.org`, `checkip.amazonaws.com`, `ifconfig.me` | Exit-IP lookup, only with `geoip=True` or `--fingerprint-webrtc-ip=auto` | `geoip.py:197-199` |
| `update.googleapis.com` | Widevine CDM fetch, only through `CLOAKBROWSER_FETCH_WIDEVINE` / `bin/fetch-widevine.py` | `bin/fetch-widevine.py:38` |

A search of `cloakbrowser/`, `js/src/`, `dotnet/src/` and `bin/` for `telemetry`, `analytics`, `posthog`, `sentry`, `beacon`, `mixpanel`, `amplitude` and `datadog` returns no matches. `CLOAKBROWSER_AUTO_UPDATE=false` disables the PyPI and release checks (`download.py:1184, 1262`) but not license validation. The binary's own network behavior is outside what the wrapper shows; the README states that licensed (Pro) binaries contact cloakbrowser.dev for license and session calls (`README.md:759`; Tier B).

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

The binary behaved legitimately in all tests, but it remains closed-source, and the audited version (145) is now behind the shipping versions (146 keyless free / 154 Pro). The license prohibits reverse engineering. Separately, the wrapper's default arguments include `--no-sandbox` (see [How It Works §1](#1-fingerprint-seed-system)).

### Mitigation Recommendations

```bash
# Disable auto-update (prevents silent binary replacement)
export CLOAKBROWSER_AUTO_UPDATE=false

# Pin an exact binary version (rollback / reproducibility); the README documents
# pinning for paid keys, the keyless code path also honours it (see Free vs Pro)
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
| **C++ Chromium patches** | 87 source-level modifications stated for the latest Pro binaries (Chromium 154); vendor-stated, not JS injection or config flags |
| **Chromium engine** | TLS fingerprint reported to match real Chrome (Tier B) |
| **Drop-in Playwright/Puppeteer** | Same API — swap the import, keep your code |
| **`humanize=True`** | One flag for Bézier mouse, typing simulation, wheel scrolling; full Playwright selector syntax and strict mode since 0.6.0 |
| **0.9 reCAPTCHA v3** (Pro) | Vendor-reported score on the Pro/current build (Tier B) |
| **Multi-language** | Python + Node.js (TypeScript) + **.NET 8 / C#** with full type definitions |
| **Cross-platform** | Linux x64/arm64, macOS arm64/x64, Windows x64 |
| **Platform-aware defaults** | macOS runs native; Linux/Windows use a Windows persona automatically |
| **Coherent seed identity** | Screen/GPU/RAM/CPU/fonts/audio chosen together as a plausible real device |
| **Signed downloads** | Pinned Ed25519 signature on checksums — authenticity, not just integrity |
| **GeoIP + WebRTC coherence** | Timezone/locale/WebRTC-IP from proxy or own IP (132 countries) |
| **Framework integrations** | browser-use, Crawl4AI, Crawlee, Scrapling, Stagehand, LangChain, Selenium, UC |
| **`cloakserve` CDP server** | Per-seed CDP routing for framework/Docker deployments |
| **Version pinning/rollback** | `browser_version=` / `CLOAKBROWSER_VERSION`; the README documents it for paid keys only, the keyless code path also honours it (`download.py:284-305`), a free GitHub key ignores it (`download.py:241-242`) |
| **Widevine/DRM** | Opt-in CDM auto-fetch for persistent contexts |
| **Persistent profiles** | Cookies/localStorage across sessions; one fingerprint seed per profile since 0.6.0 |
| **Zero config** | Launch sets the seed and platform flags; no arguments required |

### Disadvantages

| Con | Details |
|-----|---------|
| **Closed-source binary** | Proprietary Chromium — cannot verify the C++ patches |
| **Best results are paid** | 0.9 reCAPTCHA v3 / FingerprintJS pass are stated for the Pro/current build; the keyless free binary is v146 and the README says it "ages fast"; a free GitHub-sign-in key (one concurrent session) provides the latest build |
| **Audit lags shipping version** | Public audit covers Chromium 145; keyless free is 146, Pro is 154 |
| **`--no-sandbox`** | Runs with the Chromium sandbox disabled by default (`config.py:165`); `stealth_args=False` omits the default list |
| **Large download** | ~200MB compressed binary on first run |
| **Auto-update** | Background update check (can be disabled) |
| **No CAPTCHA solving** | Prevents CAPTCHAs from appearing, doesn't solve them |
| **License restrictions** | Binary license prohibits redistribution and reverse engineering |
| **Author-reported tests** | Detection results are the vendor's own, not independent reproductions |
| **0.6.0 behaviour changes** | Humanized actions use strict mode and raise instead of falling back; several Python helpers were removed; Playwright 1.53+ required |

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

ctx = launch_persistent_context("./my-profile", headless=False)  # seed kept in ./my-profile/.cloakbrowser-seed (0.6.0)
page = ctx.new_page()
page.goto("https://protected-site.com")
ctx.close()  # cookies/localStorage saved and restored next run
```

### Fixed Fingerprint Seed / Version Pin

```python
# Same seed = same identity across launches (returning visitor)
browser = launch(args=["--fingerprint=42069"])

# Pin an exact binary (rollback if a new build regresses); the README shows this with a paid key
browser = launch(license_key="cb_xxxxxxxx", browser_version="154.0.8037.57.1")
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
| `cloakbrowser/_version.py` | Wrapper version (`0.6.2`) |
| `cloakbrowser/config.py` | Stealth args, platform detection, seed (incl. per-profile `.cloakbrowser-seed`), Chromium version map, signed-download config |
| `cloakbrowser/browser.py` | `launch()`, `launch_async()`, `launch_context()`, `launch_persistent_context()` |
| `cloakbrowser/__main__.py` | CLI: `install`, `info` / `doctor`, `update`, `clear-cache`, `login`, `logout` |
| `cloakbrowser/download.py` | Binary download, Ed25519-signed verification, auto-update, keyless / keyed routing |
| `cloakbrowser/license.py` | License validation/caching, session seats, denial-code mapping, Pro version check |
| `cloakbrowser/geoip.py` | MaxMind GeoIP timezone/locale + WebRTC-IP detection |
| `cloakbrowser/widevine.py` | Widevine CDM handling for DRM playback |
| `cloakbrowser/human/engine.py` | Unified humanize engine: resolve, element states, wheel scrolling, hit-target check, press/type (0.6.0) |
| `cloakbrowser/human/world.py` | Per-frame CDP isolated worlds and helper library |
| `cloakbrowser/human/injected.py` | Loads Playwright's InjectedScript from the installed driver |
| `cloakbrowser/human/patch.py` | Class-level wiring into Playwright's sync and async APIs |
| `cloakbrowser/human/fields.py` | Per-input-type rules (typo suppression, value normalisation) |
| `cloakbrowser/human/mouse.py` | Bézier curve movement, click targeting, overshoot |
| `cloakbrowser/human/keyboard.py` | Adjacent-key and shift-symbol tables; legacy `human_type` helper |
| `cloakbrowser/human/config.py` | `HumanConfig` dataclass, `default` / `careful` presets |
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

CloakBrowser modifies Chromium at the C++ source level (vendor-stated: **87 patches** on the latest Pro binaries, 58 on the keyless free binary), and the author reports passes on major detection services including reCAPTCHA v3 (0.9 score) and Cloudflare Turnstile (Tier B). Since the last analysis it has added a **free GitHub-sign-in key tier**, a **.NET/C# client**, **coherent seed-built hardware identities**, **Ed25519-signed downloads**, **WebRTC-IP coherence**, **132-country GeoIP**, **version pinning/rollback**, **Widevine/DRM**, a **macOS persona**, **per-profile persistent seeds**, and a broad set of **AI-agent/framework integrations**.

The `humanize=True` flag adds behavioral simulation (Bézier mouse curves, typing with typos, scroll physics) in readable wrapper code; the layer reads the DOM in a CDP isolated world and, since 0.6.0, runs Playwright's own selector engine there (full selector syntax, strict mode, errors instead of fallbacks).

**The trade-offs.** The Chromium binary is **closed-source** and proprietary, and the newest builds are delivered through license keys (a free key limited to one concurrent session, and paid plans); the keyless free binary (Chromium 146) is older. The public security audit (9/9 tests passed, no malicious behavior found) covers the **older Chromium 145** binary, not the 146/154 builds now shipping, so its conclusions do not fully transfer. The Ed25519 signing closes the old self-referential-checksum gap, but it proves authenticity, not what the patches do. The wrapper's default arguments include `--no-sandbox`.

**Applicability:** Chromium automation via the Playwright or Puppeteer API where engine-level fingerprint control and built-in humanized input are required and a closed binary is acceptable. The published figures (reCAPTCHA v3 0.9, FingerprintJS pass) are Tier B and stated for the Pro/current build.

**Constraints:** the engine is proprietary — the 87 patches cannot be read or independently verified, and the MIT license covers only the wrapper. Free and Pro binaries differ in Chromium version (146 vs 154) and patch count (58 vs 87). The independent audit covered Chromium 145, which no current binary matches. CloakBrowser's engine source is unpublished (the repository contains the wrapper only); Camoufox, Clearcote, and Obscura publish theirs.

---

*Analysis conducted for educational purposes. Use responsibly.*
