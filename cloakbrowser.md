# CloakBrowser - Deep Technical Analysis

> **Tool Type:** Custom Chromium Build (Anti-Detect Browser)
> **Repository:** [github.com/CloakHQ/CloakBrowser](https://github.com/CloakHQ/CloakBrowser)
> **Approach:** C++ source-level fingerprint patches + CDP input behavior mimicking
> **Language:** Python, Node.js (TypeScript), .NET (C#)
> **What is verified:** the wrapper source (default arguments, licence-key and download routing, signature verification, humanize module) read at the commit below (**Tier A**), plus the patch counts and platform matrix read from the project's own README (**Tier A** that they are *claimed*; the binary itself is closed, so what the patches do cannot be verified here)
> **Anti-bot service claims:** Turnstile, FingerprintJS, **reCAPTCHA v3 score 0.9**, "tested against 50+ detection sites" — all **Tier B**, stated for the README's "latest Pro/current build" (`README.md:42`, `README.md:220-238`). The README says free and Pro keys get the same build (`README.md:861`).
> **Licence key required (0.7.0, breaking):** since wrapper 0.7.0 (2026-11-01) every launch needs a licence key; the keyless Chromium 146 download is gone from the wrappers. A free key is obtained by email and allows one concurrent session (`cloakbrowser/download.py:195-197`, `:347-394`; CHANGELOG 0.7.0).
> **Maintenance:** wrapper **0.7.3** (2026-11-20, PyPI and npm); latest GitHub release `chromium-v156.0.8078.47.1-pro` (2026-11-03); last push 2026-11-20. 33.0k stars, 2.7k forks, 27 contributors, 170 open issues. MIT wrapper, **proprietary binary**.
> **Verified:** 2026-11-20 against `CloakHQ/CloakBrowser` @ `fa3716e` (0.7.3 release commit; previous revision `485f678`, 2026-10-13).

> ### Patch counts — current as of 2026-11-20
>
> | Platform | Binary served to a free or paid key | Last keyless build (wrapper ≤ 0.6.5 only) |
> |---|---|---|
> | Linux x86_64 / arm64 | Chromium 156 (**87** patches) | Chromium 146 (58 patches) |
> | Windows x86_64 | Chromium 156 (**87** patches) | Chromium 146 (58 patches) |
> | macOS arm64 / x86_64 | Chromium 156 (**87** patches) | Chromium 145 (26 patches) |
>
> Source: the vendor README (`README.md:855-861`, Tier B); the keyless column is the 2026-10-13 reading of `cloakbrowser/config.py:25-31` at `485f678`. At `fa3716e` the wrapper has no built-in version table: `PLATFORM_CHROMIUM_VERSIONS` and the GitHub Releases fallback were removed in 0.7.0, and the build is whatever `cloakbrowser.dev/api/download/version` names (`cloakbrowser/license.py:28`, `:559-616`). The README directs anyone who wants the keyless build to pin the wrapper below 0.7 (`README.md:1353-1354`).
> Earlier revisions of this report cited "33", "66" (Chromium 148) and "71" (Chromium 150); all are superseded. The count stayed at 87 through Chromium 152, 154, 155 and 156. **Patch count is a measure of surface area
> touched, not of quality** — it is not comparable across projects that split changes
> differently.

---

## Table of Contents

- [What is CloakBrowser?](#what-is-cloakbrowser)
- [Current State (2026-11)](#current-state-2026-11)
- [How It Works](#how-it-works)
- [Free Key vs Pro (key required since 0.7.0)](#free-key-vs-pro-key-required-since-070)
- [Human Behavior System](#human-behavior-system)
- [GeoIP + WebRTC Integration](#geoip--webrtc-integration)
- [Framework Integrations](#framework-integrations)
- [Test results — the author's own, on the current build](#test-results--the-authors-own-on-the-current-build)
- [Security Audit](#security-audit)
- [Pros and Cons](#pros-and-cons)
- [Installation & Usage](#installation--usage)
- [When to Use](#when-to-use)

---

## What is CloakBrowser?

CloakBrowser is a **patched Chromium binary** with source-level C++ modifications that spoof browser fingerprints at the engine level. It ships as a drop-in replacement for Playwright and Puppeteer — same API, same code, just swap the import.

**Approach:** the vendor states that fingerprint changes are compiled into the Chromium binary rather than injected through JavaScript or configuration (`README.md:22`, `README.md:180`, `README.md:291`; Tier B, the binary is closed). Whether any individual patch is observable from page JavaScript is not established here (Tier D).

**Engine:** it targets **Chromium** (not Firefox), which gives native Playwright/Puppeteer API support; the vendor reports TLS fingerprints identical to Chrome (README test table, Tier B).

**What changed since the last analysis (2026-10-13):** the wrapper went from 0.6.2 to **0.7.3** and Pro Stable from Chromium 154 to **156** on every platform (87 claimed patches, unchanged). **0.7.0 removed keyless use:** a launch without a key either shows a terminal menu to obtain a free key by email or raises `CloakBrowserLicenseError` with a sign-up link; the GitHub sign-in route, the GitHub Releases download fallback and the self-hosted download variables are gone, and the Docker image no longer contains a binary. Humanized input was retuned (0.6.3) around measured keystroke timing, Fitts'-law mouse strokes and whole-notch wheel scrolling. 0.7.1 exported `build_launch_options()` and licence-guard helpers for callers who run their own Playwright instance. The `--no-sandbox` default is unchanged. See [Current State](#current-state-2026-11).

---

## Current State (2026-11)

Verified against the repo source and release history (repo read at `fa3716e`, 2026-11-20; previous revisions `485f678`, 2026-10-13, and `f44864b`, 2026-09-29):

| Fact | Value | Evidence |
|------|-------|----------|
| Wrapper version | **0.7.3** (2026-11-20; release commit is the HEAD read) | `cloakbrowser/_version.py:1`, `js/package.json:3`, `dotnet/src/CloakBrowser/CloakBrowser.csproj:13`, PyPI / npm |
| Licence key | **Required for every launch** since 0.7.0. Resolution order: `license_key=`, `CLOAKBROWSER_LICENSE_KEY`, `<cache>/license.key`; with none, a free-key claim starts (terminal menu, or an error carrying the link) | `cloakbrowser/download.py:191-232`, `cloakbrowser/license.py:261-301`, CHANGELOG 0.7.0 |
| Binary (free or paid key) | **Chromium 156.0.8078.47.1** on Linux x64/arm64, Windows x64, macOS arm64/x64; the README says free and Pro keys get the same build | GitHub release `chromium-v156.0.8078.47.1-pro` (2026-11-03); `README.md:155-157`, `README.md:855-861` (Tier B) |
| Keyless binary | No longer downloaded by the wrappers. The README points to wrapper < 0.7 / Docker `0.6.5` for the old v146 (v145 macOS) build, "no longer updated" | `README.md:1353-1354`; `download.py` has no keyless path |
| C++ patch count | **87** on Chromium 156, every platform | `README.md:39`, `README.md:289`, `README.md:855-859` (Tier B) |
| CDP input mimicking | Included in the patch set (input behavior mimicking) | `README.md:289` (Tier B) |
| Languages | Python (≥3.9; `playwright>=1.53,<1.66` since 0.7.3), Node.js/TypeScript (20.19+ or 22.12+; peer `playwright-core >=1.53.0 <1.66.0`), **.NET 8 / C# (NuGet; built against Microsoft.Playwright `[1.64.1,1.65)` since 0.6.4/0.7.3; contributed by an outside author in PR #385, CHANGELOG 0.4.3)** | `pyproject.toml:11`, `pyproject.toml:52`, `js/package.json:57-63`, `dotnet/src/CloakBrowser/CloakBrowser.csproj:4`, `:31`, `CHANGELOG.md:298` |
| License (wrapper) | **MIT** | `LICENSE`, `pyproject.toml:10` |
| License (binary) | Proprietary (`BINARY-LICENSE.md` v1.3, July 2026, unchanged since `485f678`) | `BINARY-LICENSE.md` ("Version-Specific Terms", "Restrictions") |
| Platforms | Linux x64/arm64, macOS arm64/x64, Windows x64 | `cloakbrowser/config.py:167-174` → `SUPPORTED_PLATFORMS` |
| Maintenance | Last push 2026-11-20; 27 contributors, 170 open issues, 32,997 stars | GitHub API (`STATUS.md`) |
| Last tested (by author) | Nov 2026 (Chromium 156) | `README.md:220` (Tier B) |

> **Note on patch counts:** the README now states a single figure, **87**, for the one build every key receives (Chromium 156). The 58 (Chromium 146) and 26 (macOS 145) figures describe the keyless builds that only wrapper 0.6.x and older download.

> **Free-key version:** the wrapper fetches the same `latest` build for free and paid keys (`download.py:439-450`) and only drops a version pin for `plan == "free"` (`download.py:204-205`). Which build a free key is actually served is decided server-side; the README says it is the same as Pro (`README.md:191`, `README.md:861`; Tier B).

---

## How It Works

### Architecture Overview

```
┌──────────────────────────────────────────────────────────────────┐
│                    CLOAKBROWSER ARCHITECTURE                       │
├──────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────────┐    ┌──────────────────────┐                │
│  │  Python / JS /   │    │  Licence key (req'd)  │                │
│  │  .NET Wrapper     │    │  free (email) or paid │                │
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
│  │  Chromium 156 (87 patches), every platform   │                │
│  │  ┌────────────────────────────────────────┐  │                │
│  │  │  Source-Level C++ Patches               │  │                │
│  │  │  - Canvas fingerprint randomization     │  │                │
│  │  │  - WebGL/WebGPU vendor/renderer spoof   │  │                │
│  │  │  - Audio context noise injection        │  │                │
│  │  │  - Screen/hardware/memory spoofing      │  │                │
│  │  │  - CDP input behavior mimicking          │  │                │
│  │  │  - Font enumeration                      │  │                │
│  │  │  - WebRTC / network-timing hardening     │  │                │
│  │  │  - navigator.webdriver = false           │  │                │
│  │  │  - Automation signal removal             │  │                │
│  │  │  - Coherent seed-built hardware identity │  │                │
│  │  │  - Native locale/timezone spoofing       │  │                │
│  │  │  - Licence/session calls (Pro build)     │  │                │
│  │  └────────────────────────────────────────┘  │                │
│  └──────────────────────────────────────────────┘                │
│                                                                   │
│  ┌──────────────────────────────────────────────┐                │
│  │  Optional: humanize=True                     │                │
│  │  - Fitts'-law Bézier strokes, ~60 Hz events  │                │
│  │  - Keystroke timing with rollover and typos  │                │
│  │  - Whole-notch mouse-wheel scrolling         │                │
│  └──────────────────────────────────────────────┘                │
│                                                                   │
└──────────────────────────────────────────────────────────────────┘
```

CloakBrowser is a thin wrapper around a custom-built Chromium binary:

1. **You install** → `pip install cloakbrowser` / `npm install cloakbrowser` / NuGet `CloakBrowser`
2. **First launch** → the wrapper resolves a licence key (or starts a free-key claim), validates it with cloakbrowser.dev, then downloads the latest build for the platform (Chromium 156 on every platform at the time of reading)
3. **Every launch** → Playwright or Puppeteer starts with the CloakBrowser binary + stealth args
4. **You write code** → standard Playwright/Puppeteer API, nothing new to learn

### 1. Fingerprint Seed System

Every launch generates a **random seed** (`--fingerprint=<10000..99999>`, `config.py:43`, `:50-51`) that deterministically controls all fingerprint values. Same seed = same fingerprint across launches (useful for returning-visitor patterns).

**Persistent profiles keep their seed (since 0.6.0).** `launch_persistent_context()` stores the seed in `<user_data_dir>/.cloakbrowser-seed` on first launch and reuses it afterwards; an explicit `--fingerprint=` in `args` or `stealth_args=False` leaves the file alone, a corrupt file is replaced with a warning, and concurrent first launches agree on one seed through an exclusive hard link (`config.py:54-136`, `browser.py:820`, `browser.py:977`). The file format is shared with the JS and .NET wrappers (`config.py:45-47`). Non-persistent launches stay random. Deleting the file rotates the identity (`README.md:414`). Unchanged at `fa3716e`.

The stealth-args builder, from `cloakbrowser/config.py:139-161` (comments abridged):

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

> The wrapper does not hardcode `--fingerprint-gpu-vendor` / `--fingerprint-gpu-renderer` / `--disable-blink-features=AutomationControlled` in the default args. The binary derives a **coherent hardware identity** (screen, GPU, RAM, CPU cores, color depth, fonts, audio) from the seed — "chosen together so they form a popular, self-consistent device with no internal contradictions" (CHANGELOG 0.4.8, Tier B). Playwright's `--enable-automation` / `--enable-unsafe-swiftshader` are stripped via `IGNORE_DEFAULT_ARGS` (`config.py:36`, passed at `browser.py:440`).

**`--no-sandbox` default:** `--no-sandbox` is the first entry of the default list (`config.py:148-151`, literal at `config.py:149`) in the Python, JavaScript (`js/src/config.ts:193-196`, literal at `:194`) and .NET (`dotnet/src/CloakBrowser/Config.cs:183-187`, literal at `:185`) wrappers, and `cloakserve` builds its Chrome arguments with `build_args(stealth_args=True, ...)` (`bin/cloakserve:367-373`). Caller `args` can override a flag but cannot remove it (`browser.py:1564-1569`); `stealth_args=False` skips the whole default list (`browser.py:1550-1552`), and the README shows supplying `--fingerprint` and `--fingerprint-platform` manually in that case (`README.md:780-783`). The string `--no-sandbox` occurs once in each wrapper. The README does not mention the flag; CHANGELOG 0.5.2 records that the binary stops showing an unsupported-flag warning bar when the sandbox is disabled, "as required when running as root (e.g. in Docker)" (`CHANGELOG.md:216`), and the 0.3.4 entry at `CHANGELOG.md:553` names the flag. Unchanged at `fa3716e`.

**Why platform-aware defaults matter:**
- macOS binary runs as a native Mac browser (Apple GPU, macOS UA) — spoofing Windows on Mac creates detectable font/GPU mismatches
- Linux/Windows binary uses a Windows fingerprint profile (more common, harder to cluster)
- Screen/window size come from the real display, not a flag — so the wrapper defaults `new_page()` / `new_context()` to `no_viewport=True` (`browser.py:259-303`, applied at `browser.py:621-624`). Since 0.7.0 this applies to headless launches too (the old fixed 1920x947 headless viewport is gone), and `--start-maximized` is added whenever no window size or position is given (`browser.py:1594-1600`; CHANGELOG 0.7.0)

### 2. C++ Source-Level Patches (87 on the current binary)

The vendor states the patches are compiled into the Chromium binary (Tier B; the binary is closed and cannot be inspected here). The binary covers **canvas, WebGL, audio, fonts, GPU, screen properties, WebRTC, network timing, hardware reporting, automation-signal removal, and CDP input behavior mimicking** (`README.md:289`).

| Patch Area | What It Does |
|------------|--------------|
| Canvas fingerprint | Seed-based randomized noise on canvas operations |
| WebGL/WebGPU | Vendor/renderer spoofing, adapter features, timing-consistent behavior; the README notes that Windows now passes real GPU values through (`README.md:161`) |
| Audio context | Noise injection in audio fingerprinting |
| Screen/Window | Dimensions, pixel ratio, coherent geometry (headed + headless) |
| Hardware | concurrency, deviceMemory, color depth from seed — coherent with GPU/CPU/RAM; `--fingerprint-max-touch-points=<N>` reports a touch screen (156+, `README.md:713`) |
| CDP input mimicking | Pointer/keyboard/mouse events match real user signals |
| Automation signals | webdriver=false, plugin list, window.chrome, UA cleanup |
| Font enumeration | Font-list masking. The opt-in `--fingerprint-windows-font-metrics` flag is no longer in the README's flag table, and the wrappers dropped their handling for it as "retired" in `b2d7789` (2026-10-31); whether the 156 binary still reads it is not established (Tier D) |
| WebRTC / network | Exit-IP injection, network-timing signals matched to real Chrome; an opt-in `--fingerprint-transparent-proxy` connection mode with DNS over HTTPS through the proxy (`README.md:717-718`) |
| Locale/timezone | Native C++ locale spoofing (not CDP emulation) |
| Storage quota | `--fingerprint-storage-quota` sets the reported headroom; the README now gives the default as 10 GiB, "like a regular Chrome profile" (`README.md:706`). The earlier README note that BrowserScan reads the default as incognito is gone |

Patch counts by binary (`README.md:855-859`):

| Platform | Binary (free or paid key) |
|----------|---------------------------|
| Linux x86_64 | Chromium 156 (**87 patches**) |
| Linux arm64 | Chromium 156 (87) |
| macOS arm64 / x86_64 | Chromium 156 (87) |
| Windows x86_64 | Chromium 156 (87) |

**Properties the vendor reports for the patched binary (Tier B):**
- `navigator.webdriver` returns `false`
- `navigator.plugins.length` returns `5`
- `window.chrome` is present as an `object`
- User-Agent has no `HeadlessChrome` leak (README test table: `Chrome/156.0.0.0`, `README.md:235`)
- CDP detection `isAutomatedWithCDP: false`; TLS fingerprint reported identical to Chrome (ja3n / ja4 / akamai)
- Changes are described as compiled into the binary rather than injected via JavaScript (`README.md:22`, `README.md:180`, `README.md:291`)

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

### 4. Licence Key, Binary Download & Verification (Ed25519-signed)

From `cloakbrowser/download.py` + `license.py` + `config.py` at `fa3716e`:

```
pip install cloakbrowser
    → first launch triggers binary resolution (ensure_binary, download.py:164)
    → CLOAKBROWSER_BINARY_PATH set: use that file, no key, no download
      (download.py:180-189)
    → resolve a key (param > env > <cache>/license.key); none → free-key claim
      (download.py:195-196, 347-394)
    → POST the key to cloakbrowser.dev/api/license/validate (24 h cache keyed
      by SHA-256 of the key; stale cache if unreachable) (license.py:514-556)
    → invalid key, or unvalidatable with no cache → CloakBrowserLicenseError
      (download.py:223-232)
    → GET cloakbrowser.dev/api/download/version (once per hour per channel)
      (license.py:36, 559-616); free key drops any version pin (download.py:204-205)
    → GET cloakbrowser.dev/api/download/<version> with the key as a bearer token
      (download.py:574-605)
    → fetches .../releases/pro/chromium-v<version>/SHA256SUMS + SHA256SUMS.sig
    → verifies the Ed25519 signature against a PINNED public key, checks that the
      signed manifest's version= line matches the requested version, then verifies
      the archive hash (download.py:608-669, 685-724)
    → extracts into a private staging dir, then renames it to
      ~/.cloakbrowser/chromium-{version}-pro/ (download.py:813-888; config.py:239-241)
```

> **Removed in 0.7.0:** the keyless download, the GitHub Releases fallback (no `releases/download` or `api.github.com` URL remains in `cloakbrowser/`, `js/src/` or `dotnet/src/`), `CLOAKBROWSER_DOWNLOAD_URL`, `CLOAKBROWSER_SKIP_CHECKSUM`, `PLATFORM_CHROMIUM_VERSIONS` and `check_for_update`. Every download now goes through the keyed path, where verification has no bypass (`download.py:600`). Cached builds are named `chromium-<version>-pro` (`config.py:239-241`).

> **Signature check.** The wrapper verifies a **pinned Ed25519 signature** (`BINARY_SIGNING_PUBKEYS`, `config.py:26-28`; one key is pinned) on the published `SHA256SUMS`, and the signed manifest's `version=` line must match the requested version, so a mirror cannot substitute a genuinely signed older build (`download.py:649-657`). A verification failure raises `BinaryVerificationError` and is never masked by the cached-build fallback (`download.py:46-54`, `:215-217`, `:543-546`). This closes the "self-referential checksums" gap the earlier audit flagged.

> **Extraction.** Once the signature and checksum verify, archives are unpacked directly with `tarfile.extractall(filter="fully_trusted")` and `zipfile.extractall`, with no per-entry path or symlink screening (`download.py:891-907`; removed in 0.5.11, `CHANGELOG.md:129`). The trust boundary for extraction is therefore the signature check. Each download extracts into its own `<dir>.partial-<uuid>` staging directory that is renamed into place; the first complete install wins and Windows renames are retried for about 2.5 s (`download.py:65-72`, `:813-888`).

> **Update behaviour.** An unpinned launch asks the server for the latest version (rate-limited to once per hour, `license.py:36`, `:572-581`) and downloads it when newer than the cached build; a failed download falls back to the cached build (`download.py:480-571`). `CLOAKBROWSER_AUTO_UPDATE=false` keeps a cached build without the server check (`download.py:486-490`) and skips the PyPI check (`download.py:1070-1071`); licence validation still runs.

The README also documents manual verification (`README.md:1376-1390`): a GPG-signed release tag, `gh attestation verify` for the binary archives, and a Cosign signature for the Docker image (vendor-documented, Tier B). The manual-dispatch workflow that attested release archives, `.github/workflows/attest-release.yml`, was **deleted** in `91effe4` (2026-11-07); `.github/workflows/publish.yml:159-163` still Cosign-signs and attests the Docker image. Whether binary releases published after that commit carry a GitHub attestation is not established here (Tier D).

Binary size: ~200MB compressed download (`README.md:127`), cached under `~/.cloakbrowser/`. Runtime footprint (`README.md:1043`): ~190MB RAM idle, ~280MB with 3 tabs, ~30MB per additional tab.

---

## Free Key vs Pro (key required since 0.7.0)

The **wrapper (Python + JS + .NET) is MIT.** The **binary** is proprietary (`BINARY-LICENSE.md` v1.3, July 2026). Since wrapper 0.7.0 it is obtained only with a licence key:

| Tier | Binary | Where | Notes |
|------|--------|-------|-------|
| **Free key (email)** | Latest build; README: Chromium 156, "the same build" as Pro (`README.md:191`, `README.md:861`) | cloakbrowser.dev (`/api/download/<version>`, key as bearer token) | Obtained through a claim link (`https://cloakbrowser.dev/#claim=<code>`, `license.py:33`, `:379-380`) and an email confirmation; **one concurrent session**; a version pin is ignored (`download.py:204-205`); the welcome banner repeats once a day (`download.py:60-63`, `:75-90`) |
| **Pro, paid key** | Chromium **156.0.8078.47.1** (all platforms); 87 patches | cloakbrowser.dev | The README lists plans of 5, 20, 200 or 2,000+ concurrent sessions (`README.md:192`). Set `license_key` / `CLOAKBROWSER_LICENSE_KEY` / `~/.cloakbrowser/license.key` |
| **Keyless (legacy)** | Chromium 146 (58 patches); 145 (26) on macOS | GitHub Releases, through wrapper ≤ 0.6.5 only | The README calls it "no longer updated" and says it "ages fast" (`README.md:1353-1354`). Not reachable from the current wrappers |

- **Free-key claim (0.7.0).** With no key anywhere, a launch on the main thread with stdin and stderr attached to a terminal shows a two-option menu (get a free key by email, or paste one) and continues once the key is saved (`download.py:247-253`, `:268-344`). Anywhere else (CI, Docker without `-it`, an MCP server, `launch_async`'s worker thread) the launch prints the claim link, raises `CloakBrowserLicenseError`, and starts a daemon thread that polls `cloakbrowser.dev/api/license/free/claim` every 15 s for up to 10 min, saving the key if it arrives (`download.py:235-236`, `:347-394`, `:410-428`; `license.py:389-422`). The claim code is a 32-byte random token stored in `<cache>/.free_claim` (mode 0600, 7-day life) and sent in the POST body, not the URL (`license.py:306`, `:343-376`, `:393-396`). On a machine with a display the link is also opened in the default browser (`download.py:329-336`, `:397-404`). `cloakbrowser login` shows the same menu and needs a terminal on both stdin and stderr, otherwise it exits 2; GitHub sign-in is gone from the CLI (`__main__.py:561-607`).
- **Key handling.** Resolution order is explicit parameter, then `CLOAKBROWSER_LICENSE_KEY`, then `license.key` in the cache directory (`license.py:261-301`). A key saved by the wrapper must match `cb_[A-Za-z0-9_-]+` and is written 0600 (`license.py:304`, `:309-340`); a key passed as a parameter or environment variable is not format-checked before validation. Validation is a POST to `cloakbrowser.dev/api/license/validate` (`license.py:27`, `:514-546`), cached locally for 24 h keyed by a SHA-256 of the key (`license.py:35`, `:522-527`, `:711-727`), and a stale cache is used if the server is unreachable (`license.py:548-554`). The plan defaults to `solo` when the server omits it (`license.py:540`). `cloakbrowser info` reports the licence tier (`none` without a key) and, for keyed plans, live session seats as used/limit (`__main__.py:111-130`, `:244-255`; `license.py:647-699`).
- **Server-side enforcement.** The wrapper docstring states that the server enforces the concurrency cap (`download.py:446-449`). The binary reports licence denials through process exit codes 76-79 (`license.py:104-128`) and, for denials after the CDP handshake, a per-launch status file under `~/.cloakbrowser/denials/` named by `CLOAKBROWSER_LICENSE_STATUS_FILE` (`license.py:152-159`, `:236-251`), which the wrapper converts to `CloakBrowserLicenseError`. Since 0.7.1 the same conversion is exported for callers with their own Playwright: `build_launch_options()`, `license_error_from()`, `guard_browser()` and `license_denial()` (`browser.py:87`, `:377-444`, `:451-480`), and `close()` no longer throws after a denial in JS and .NET (CHANGELOG 0.7.1). Code 76 states that a crashed session frees its seat within 4 min (free/trial/solo), 15 min (team) or 30 min (business/scale); code 78 means the licence server could not be reached; code 79 also covers an invalid `--license-route` (`license.py:108-127`). `--license-route=auto|direct|proxy` decides whether the binary's licence and session calls go direct to cloakbrowser.dev or through `--proxy-server` (`README.md:715-716`, Tier B). Wrapper-side facts are Tier A; what the binary does is Tier B.
- **No silent downgrade.** A key the server rejects, or one that cannot be validated (server unreachable and no cached result), raises `CloakBrowserLicenseError` (`download.py:223-232`; CHANGELOG 0.5.10, `CHANGELOG.md:138`). A valid key raises on a download error when no build is cached (`download.py:218-222`, `:517-520`).
- **Local binary.** `CLOAKBROWSER_BINARY_PATH` returns before any key is resolved (`download.py:180-189`), so a self-built Chromium still launches without a key; since 0.7.0 it no longer needs its version declared (CHANGELOG 0.7.0).
- **Test claims.** The test claims (0.9 reCAPTCHA v3, FingerprintJS pass) are labelled "Pro/current build" in the README (`README.md:220-228`); the README states that free keys get the same build (`README.md:861`). All Tier B. The Docker `cloaktest` suite still uses the free-tier-stable checks introduced in 0.4.7 (`CHANGELOG.md:277`) and, since 0.7.0, prints a short message when there is no key.
- **Release channel.** `release_channel="preview"` / `CLOAKBROWSER_RELEASE_CHANNEL=preview` selects the newest build available for the platform and falls back to Stable (`config.py:180-187`, `download.py:497-505`; `README.md:1179-1205`). The current Preview version is not stated in the README and is not established here (Tier D).
- **Version pinning.** `browser_version=` / `CLOAKBROWSER_VERSION` (numeric dotted versions only, `config.py:177`, `:190-208`) launches the exact build with no server cross-check (`download.py:456-478`). The README documents it as paid-key only (`README.md:652`, `README.md:1211`); in the code a free key drops the pin (`download.py:204-205`), and since 0.7.0 there is no keyless path left that could honour one.
- **Binary license terms** (`BINARY-LICENSE.md`): the latest major version requires an active paid subscription at a tier CloakHQ designates; the license prohibits redistribution, resale or repackaging, reverse engineering, and modification, and forbids sharing license keys. The README separately offers the free-key tier above and calls the binary "free for personal and commercial use, no redistribution" (`README.md:1395`).

---

## Human Behavior System

CloakBrowser includes a human-behavior simulation system activated with a single flag: `humanize=True`. Playwright API calls are transparently replaced with human-like equivalents. It is mirrored across Python, JS (Playwright and Puppeteer), and .NET. 0.6.3 (2026-10-14) retuned all three input channels; the figures below are the `fa3716e` defaults.

### Mouse Movement — Fitts'-law Bézier strokes

From `cloakbrowser/human/mouse.py` (`_bezier` at :32-41, stroke planning at :71-163):

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

def stroke_duration(dist: float, cfg: HumanConfig) -> float:
    """Milliseconds for a ``dist`` px stroke (Fitts' law, log-normal spread)."""
    median = cfg.mouse_time_base + cfg.mouse_time_per_bit * math.log2(1 + dist / 8)
    return max(FRAME_MS * 2, rand_lognormal(median, cfg.mouse_time_spread))
```

The mouse movement system (`mouse.py:44-163`, defaults in `human/config.py:105-119`):
1. Stroke duration from Fitts' law: median `160 + 75·log2(1 + d/8)` ms with a log-normal spread of 0.3 (`careful`: 220 + 95)
2. Control points bent the same way 80% of the time (an arc rather than an S)
3. A time-warped minimum-jerk progress curve whose speed peaks at 22-38% of the stroke (`mouse.py:72-84`); the old cubic `_ease_in_out` is still defined (`mouse.py:26-29`) but no longer called
4. Pointer events at about display frame rate (`FRAME_MS = 1000/60`), 2-200 per stroke, never a zero-distance move (`mouse.py:71`, `:93-137`)
5. A low-frequency sideways drift of at most `min(1.5 px, 2% of distance)`, zero at both ends (`mouse.py:107-110`, `:129`)
6. For moves over 40 px, a 35% chance (`careful` 45%) of landing slightly past or short of the target, then a short corrective stroke after a 40-140 ms pause (`mouse.py:140-163`)

The 0.5.x burst-pause settings (`mouse_burst_size`, `mouse_burst_pause`, `mouse_steps_divisor`) were removed; Python drops them with a `FutureWarning` (`human/config.py:195-221`).

### Keyboard Typing — measured keystroke timing

From the engine's `_Typist` (`cloakbrowser/human/engine.py:137-277`) and `cloakbrowser/human/keyboard.py`, with config values in `cloakbrowser/human/config.py:77-101`:

- Median gap between key presses **150 ms**, log-normal, spread 70 ms, adjusted by key pair (other hand faster, same finger slower, slower after a space) (`keyboard.py:89-125`); `careful` preset **210 ms** ± 100 ms. The config cites the 136M Keystrokes study (Dhakal et al., CHI 2018)
- Keys held **60-175 ms** (log-normal), so the next key often goes down before the previous one is released (rollover); a key is never pressed again while still held (`engine.py:196-201`)
- Shift goes down 60-220 ms before a capital and usually comes up before the letter (`shift_up_delay = (-60, 30)`)
- **4%** mistype chance (`mistype_chance = 0.04`; `careful` 5%) — a keyboard-adjacent key, then a Backspace after a 100-300 ms "notice" delay. Digit typos stay digits (`keyboard.py:33-36`); typos are skipped in number, email, password, tel and url inputs (`human/fields.py:25`, `:56-60`), and a typo the page rejects is not corrected (`engine.py:1280-1299`)
- **15%** thinking-pause chance before a word (`typing_pause_chance = 0.15`, 300-1000 ms; `careful` 25%, 500-1200 ms)
- Non-ASCII characters (Cyrillic, CJK, emoji) are inserted as text, like an IME (`engine.py:225-227`)
- Shift-symbols are sent through CDP `Input.dispatchKeyEvent` with the Shift modifier (`engine.py:228-236`). The `page.evaluate` fallback that the source comments call detectable remains only in the exported legacy `human_type` helper (`human/keyboard.py:143-183`, fallback at `:243-247`), which the engine does not call

### Scrolling — whole wheel notches

Since 0.6.3 every wheel event is exactly one notch of the persona platform's size — 100 px on a Windows persona, 40 px on macOS, 120 px on Linux, or `scroll_notch_px` when set — so `deltaY` and `wheelDeltaY` agree as they do for a real wheel. Notches go out in flicks of 2-5 with short pauses, slower at the start and end (`engine.py:642-684`; `human/config.py:132-146`). Previously the layer sent 20-40 px chunks with a one-notch `wheelDeltaY` (CHANGELOG 0.6.3). In JS Puppeteer, `page.mouse.wheel({ deltaY })` now scrolls at least one whole notch (CHANGELOG 0.6.3, behaviour change).

### Selector Handling and Patched Methods (engine since 0.6.0)

Every humanized action in Python, JavaScript (Playwright) and .NET runs through one engine (`cloakbrowser/human/engine.py`, `js/src/human/engine.ts`, `dotnet/src/CloakBrowser/Human/HumanEngine.cs`). The engine creates a CDP isolated world per frame (`Page.createIsolatedWorld`, `human/world.py:503-508`) and evaluates Playwright's own InjectedScript there, extracted from the installed Playwright driver bundle (`human/injected.py:1-13`):

- **Selectors:** full Playwright selector syntax, including `get_by_role`, `>>` chains, `filter(has=/has_text=)`, `:visible`, `nth` and `frame_locator`. Strict mode applies: an ambiguous locator raises Playwright's `strict mode violation` instead of using the first match (`human/world.py:168-175`). `UnsupportedHumanizeSelectorError` and the other 0.5.x error classes stay importable, but actions no longer raise them (`human/__init__.py:23-29`). Since 0.6.5 iframes are mapped to CDP frames by URL rather than `window.name` (#624).
- **Pipeline:** resolve, then wait for element states (visible, enabled, editable, stable), then scroll into view with mouse-wheel bursts, then a Bézier move, then a hit-target check through every ancestor `<iframe>`, then press or type (`human/engine.py:1-14`). Failures raise Playwright `Error` / `TimeoutError` with a call log instead of falling back to Playwright's stock action. The one exception: an `ElementHandle` read or `dispatch_event` on an element the isolated world cannot uniquely locate (or a `dispatch_event` whose init holds a JSHandle) runs Playwright's own call (`RawFallback`, `human/patch.py:14-18`, `human/engine.py:116-121`, `:390-415`, `:446-478`). Since 0.6.5 `timeout=` bounds every browser call an action makes, so a page that stops answering raises `TimeoutError` (`human/patch.py:275-289`).
- **Patching (Python):** class-level on Playwright's `Page`, `Frame`, `Locator`, `ElementHandle`, `Mouse` and `Keyboard`; each wrapper checks whether its page was humanized and otherwise calls the original method (`human/patch.py:1-6`, `:318-374`). Patched: `click`, `dblclick`, `hover`, `tap`, `fill`, `type`, `press`, `check`, `uncheck`, `set_checked`, `select_option`, `focus`, the element reads `input_value`, `text_content`, `inner_text`, `inner_html`, `get_attribute` and `dispatch_event`, `drag_and_drop` (page, frame), `clear`, `press_sequentially`, `drag_to` (locator), `scroll_into_view_if_needed`, `mouse.move` / `click` / `dblclick` and `keyboard.type` (`human/patch.py:171-316`). `goto` is not wrapped. `page._original` gives the raw Playwright calls and `page._stealth_world.evaluate()` evaluates in the isolated world (`human/patch.py:377-425`).
- **Requirements:** Playwright 1.53 or newer and below 1.66 (`pyproject.toml:52`); on an older or internals-incompatible Playwright, `humanize=True` raises instead of running actions un-humanized (`human/patch.py:83-109`, which also accepts the module layout Playwright 1.65 introduced). 0.7.2 capped Playwright below 1.65 after 1.65.0 broke `import cloakbrowser`; 0.7.3 supports 1.65 (CHANGELOG 0.7.2, 0.7.3, #641).
- **Value fields:** date and time inputs are typed part by part in the locale's order, sliders are clicked and nudged with arrow keys, `select_option` opens the dropdown and uses type-ahead plus arrow keys and, since 0.6.3, returns once the pick navigates the page (`engine.py:1067-1213`); `fill()` on `<input type=color>` raises. Select-all and `ControlOrMeta` follow the persona (`--fingerprint-platform=macos` uses Meta), not the host OS.
- **Composing with your own Playwright (0.7.1):** `humanize_browser()` / `humanize_browser_async()` apply the layer to a browser launched with `pw.chromium.launch(**build_launch_options())` (`browser.py:482-506`).

### Interaction Summary

| Interaction | Default Playwright | With `humanize=True` |
|---|---|---|
| Mouse movement | Instant teleport | Fitts'-law Bézier stroke at ~60 Hz, early speed peak, occasional corrective stroke |
| Clicks | Instant | Aim delay (inputs 60–140ms / buttons 80–200ms) + hold duration (`human/config.py:121-126`) |
| Keyboard | Instant fill | ~150 ms median gap between presses, ~60-175 ms holds with rollover, 4% typos |
| Scroll | Jump | Whole wheel notches in flicks (`human/engine.py:642-684`) |
| `fill()` | Instant value set | Clear field + type character by character |
| Between actions | Nothing | Optional idle micro-movements (`careful` preset) |

### Presets

| Preset | Typing gap (median) | Aim Delay (button) | Description |
|--------|:-----------:|:---------:|-------------|
| `default` | 150ms | 80–200ms | Normal browsing speed |
| `careful` | 210ms | 120–280ms | Slower, more deliberate, idle between actions |

Select with `humanize=True, human_preset="careful"` (`human/config.py:161-192`).

### Sync `time.sleep` (0.7.3)

While a sync browser or persistent context is open, the Python wrapper replaces the module-global `time.sleep` with a version that, on the thread owning the browser and for sleeps of 0.1 s or longer, waits inside Playwright's event loop so the page keeps processing (`browser.py:48-85`; restored when the last browser closes). Other threads and shorter sleeps get the original function. The CHANGELOG describes the problem it fixes as challenge pages stuck on "Verifying" on Windows during a long sleep (CHANGELOG 0.7.3, Tier B for the symptom).

---

## GeoIP + WebRTC Integration

CloakBrowser can automatically detect timezone and locale from the proxy exit IP — and, without a proxy, from the machine's own public IP:

```python
from cloakbrowser import launch

# Auto-detect timezone/locale from proxy exit IP (also injects WebRTC exit IP)
browser = launch(proxy="http://user:pass@us-proxy:8080", geoip=True)
# → Detects America/New_York timezone, en-US locale

# geoip with no proxy resolves your own public IP (since 0.4.8)
browser = launch(geoip=True)
```

How it works:
1. Uses MaxMind GeoLite2-City data via the optional `geoip2` dependency; the database is downloaded on first use from a third-party GitHub mirror (`P3TERX/GeoLite.mmdb`, `geoip.py:26-28`) and refreshed every 30 days (`geoip.py:31`)
2. Caches the database in `~/.cloakbrowser/geoip/` (`geoip.py:302-305`)
3. Resolves the exit IP via HTTP echo services (ipify.org, checkip.amazonaws.com, ifconfig.me; `geoip.py:208-210`)
4. Maps country → locale for **133 countries** (Seychelles added in 0.6.3); since 0.6.3 an unmapped country logs a warning and uses `en-US` instead of aborting (`geoip.py:147-151`)
5. Sets `--fingerprint-timezone`, `--lang` and `--fingerprint-locale` binary flags rather than CDP emulation (`browser.py:1571-1583`)
6. **Auto-injects `--fingerprint-webrtc-ip`** to prevent WebRTC IP leaks (`browser.py:1519-1531`)

Explicit timezone/locale always override auto-detection. A requested resolution that fails (timeout, missing database, unresolved timezone) **aborts the launch**; the default timeout is 20 s, configurable with `CLOAKBROWSER_GEOIP_TIMEOUT_SECONDS` (`browser.py:1470-1474`, `geoip.py:32-33`, `CHANGELOG.md:137`). Since 0.6.5 a proxy host that resolves to a non-global address (a local forwarding proxy, a LAN gateway, CGNAT `100.64.0.0/10`, IPv6 ULA) is not used as the exit IP (`geoip.py:127-133`, `:197-203`). The async launchers run the licence/binary check and the GeoIP and WebRTC exit-IP lookups in a worker thread (`browser.py:685-701`, `:973`, `:1231`). WebRTC IP spoofing can also be used standalone: `args=["--fingerprint-webrtc-ip=auto"]` (resolves the proxy exit IP; requires a proxy, otherwise the flag is removed with a warning, `browser.py:1495-1500`) or `--fingerprint-webrtc-ip=1.2.3.4` (explicit, no network call).

**Proxy routing.** SOCKS5 proxies and HTTP proxies with credentials are passed to the browser as `--proxy-server` with inline credentials; only credential-less HTTP proxies use Playwright's `proxy` option (`browser.py:1871-1915`). Since 0.7.0 credentialed HTTP proxies always go inline, independent of binary version (CHANGELOG 0.7.0). As a consequence `context.request`, `page.request` and `route.fetch()` do not use those proxies and send from the machine's own IP; the wrapper writes a one-time warning to stderr when they are first used (`browser.py:614-619`, `:1835-1868`; #579), and the README suggests an in-page `fetch()` instead (`README.md:1361`).

---

## Framework Integrations

CloakBrowser ships example integrations (`examples/integrations/`) for AI-agent and scraping frameworks, in two modes: (1) the framework launches the CloakBrowser binary directly, or (2) CloakBrowser launches first and the framework connects over CDP via `cloakserve`. Since 0.7.1 `build_launch_options()` (Python), `buildLaunchOptions()` (JS) and `CloakLauncher.BuildLaunchOptionsAsync()` (.NET) return the launch options for frameworks that own their Playwright instance.

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

`cloakserve` (`bin/cloakserve`) runs the binary as a CDP server (`docker run -d -p 127.0.0.1:9222:9222 -e CLOAKBROWSER_LICENSE_KEY cloakhq/cloakbrowser cloakserve`), rewrites the CDP WebSocket discovery URLs so clients connect through the proxy, and keeps per-seed process routing. It binds `0.0.0.0` inside a container and `127.0.0.1` otherwise (`bin/cloakserve:962-964`), starts each per-seed Chrome with `--remote-debugging-address=127.0.0.1` (`bin/cloakserve:387`), keeps idle cleanup off by default (`--idle-timeout`, `bin/cloakserve:185`, `:820-824`) and exposes `POST /fingerprint/{seed}/close` (`bin/cloakserve:941`). A browser started with no WebSocket client attached is scheduled for idle cleanup (`bin/cloakserve:423-424`). New since 0.6.5: `--exit-after-idle` shuts the server down after a period with no CDP connection (`bin/cloakserve:855`, `:877-878`), `--keep-profiles` keeps each seed's profile on cleanup (`bin/cloakserve:211-215`), Chrome is stopped with SIGINT (not SIGTERM) on Linux and macOS with a 10 s grace period so the licence session can end (`bin/cloakserve:433-445`), and clients get a 30 s WebSocket heartbeat (`bin/cloakserve:759`, `:783`). 0.7.3 fixed `--idle-timeout` closing Chrome under clients on the default path (#643). `cloaktest` runs the bundled bot-detection smoke suite. Widevine/DRM: an opt-in CDM fetch in the Docker entrypoint (`CLOAKBROWSER_FETCH_WIDEVINE`, `bin/docker-entrypoint.sh:29-51`) from Google's component server (`bin/fetch-widevine.py:38`); the wrapper itself only seeds the hint file for a CDM the user supplies (`cloakbrowser/widevine.py:1-20`). The README's Widevine section was removed in `b2d7789`.

**Docker image (0.7.0).** The image no longer contains a binary; the latest build downloads on the first launch with a key passed as `-e CLOAKBROWSER_LICENSE_KEY` or entered under `docker run -it` (`Dockerfile`, comment after `COPY examples/`; `README.md:869`).

---

## Test results — the author's own, on the current build

> **Tier B throughout.** These are the maintainer's published results, not independent
> reproductions, stated for the Pro/current build. The binary is closed,
> so nothing in this table can be verified from source — only that it is claimed.

Results are for the **latest Pro/current build** unless noted. **Last tested by the author: Nov 2026 (Chromium 156)** (`README.md:220`).

| Detection Service | Stock Playwright | CloakBrowser | Notes |
|---|---|---|---|
| **reCAPTCHA v3** | 0.1 (bot) | **0.9** (human) | Pro/current build; server-side verified |
| **Cloudflare Turnstile** (non-interactive) | FAIL | **PASS** | Auto-resolve |
| **Cloudflare Turnstile** (managed) | FAIL | **PASS** | Single click |
| **ShieldSquare** | BLOCKED | **PASS** | Production site |
| **FingerprintJS** bot detection | DETECTED | **PASS** | Pro/current build; demo.fingerprint.com |
| **BrowserScan** bot detection | DETECTED | **NORMAL** (4/4) | browserscan.net |
| **bot.incolumitas.com** | 13 fails | **1 fail** | WEBDRIVER spec only |
| **deviceandbrowserinfo.com** | 6 true flags | **0 true flags** | `isBot: false` |
| `navigator.webdriver` | `true` | **`false`** | Source-level patch |
| `navigator.plugins.length` | 0 | **5** | Real plugin list |
| `window.chrome` | `undefined` | **`object`** | Present like real Chrome |
| UA string | `HeadlessChrome` | **`Chrome/156.0.0.0`** | No headless leak |
| CDP detection | Detected | **Not detected** | `isAutomatedWithCDP: false` |
| TLS fingerprint | Mismatch | **Identical to Chrome** | ja3n/ja4/akamai match |
| Overall | — | **"Tested against 50+ detection sites"** | Author's claim (was "30+" at `485f678`) |

> **How to read these:** these are the tool author's own reported results, not independent reproductions. The strongest ones (0.9 reCAPTCHA v3, FingerprintJS pass) are stated for the **Pro/current** build; the README says free keys get the same build. The legacy keyless v146 binary is not claimed to hit them. As always, real-world results depend heavily on IP reputation and per-site behavior.

### Known Acceptable Failures

| Test | Result | Why |
|------|--------|-----|
| WEBDRIVER spec (incolumitas) | False positive | Spec-level detection, expected |
| connectionRTT | Flagged | Datacenter latency, not browser fingerprint |

---

## Security Audit

> **Full audit:** [CloakBrowser Security Audit](https://github.com/pim97/cloakbrowser-analyze)
> **Audit date:** March 2026 | **Binary:** Chromium 145.0.7632.159.7 (Linux x64)

> **Caveat (2026-11):** the public audit was done on a keyless **Chromium 145** binary. The current wrappers download only the keyed **156** build, which the audit does not cover, and they no longer download any keyless build. The audit's behavioral conclusions do not automatically transfer, and its network results (including "works with network completely blocked") concern a keyless binary: the README states that licensed binaries make licence/session calls to cloakbrowser.dev (`README.md:715-716`; Tier B), and the wrapper maps exit code 78 to "license server unreachable" (`license.py:119-122`).

### Trust Model

| Component | Source Available | Can You Audit It? |
|-----------|:-:|---|
| Python wrapper (`cloakbrowser/`) | Yes (MIT) | Fully readable |
| JavaScript wrapper (`js/`) | Yes (MIT) | Fully readable |
| .NET/C# wrapper (`dotnet/`) | Yes (MIT) | Fully readable |
| Chromium binary (`chrome`) | **No** (Proprietary) | **Cannot inspect the C++ patches** |
| SHA-256 checksums | **Ed25519-signed** (pinned pubkey) | Authenticity verifiable, not just integrity |

> The old "self-referential checksums" weakness is materially reduced. Since wrapper 0.4.0, `SHA256SUMS` carries a detached Ed25519 signature verified against a public key pinned in the wrapper source (`BINARY_SIGNING_PUBKEYS`), and since 0.7.0 no environment variable or alternate origin bypasses it. A compromised download mirror can no longer certify a tampered or downgraded binary. This establishes that the download originates from the holder of the pinned signing key. It does not make the closed-source patches readable.

### Network Behaviour Visible in the Wrapper (Tier A)

Outbound destinations found in the Python wrapper source; the JS and .NET wrappers use the same cloakbrowser.dev endpoints (`js/src/license.ts:16-18`, `:398`; `dotnet/src/CloakBrowser/License.cs:94-96`, `:368`):

| Destination | Purpose | Evidence |
|---|---|---|
| `cloakbrowser.dev` | Licence validation (POST of the key, 24 h cache), latest-version lookup (hourly), binary and signed-manifest download (key as bearer token), session-seat count (`info`), free-key claim (POST of the claim code; polled every 15 s for up to 10 min after a non-interactive no-key launch) | `config.py:295`, `license.py:27-33`, `download.py:580`, `:621`, `:235-236`, `:410-428` |
| `github.com` | GeoLite2 database mirror only; no binary download | `geoip.py:26-28` |
| `pypi.org` (npm registry in JS, NuGet in .NET) | Wrapper update check, once per process, after a valid licence | `download.py:198-199`, `:1064-1087`, `js/src/download.ts:1127`, `dotnet/src/CloakBrowser/Download.cs:1177` |
| `api.ipify.org`, `checkip.amazonaws.com`, `ifconfig.me` | Exit-IP lookup, only with `geoip=True` or `--fingerprint-webrtc-ip=auto` | `geoip.py:208-210` |
| `update.googleapis.com` | Widevine CDM fetch, only through `CLOAKBROWSER_FETCH_WIDEVINE` / `bin/fetch-widevine.py` | `bin/fetch-widevine.py:38` |

A search of `cloakbrowser/`, `js/src/`, `dotnet/src/` and `bin/` for `telemetry`, `analytics`, `posthog`, `sentry`, `beacon`, `mixpanel`, `amplitude` and `datadog` returns no matches. `CLOAKBROWSER_AUTO_UPDATE=false` disables the PyPI check and the binary update check when a build is cached (`download.py:486-490`, `:1070-1071`) but not licence validation, which every keyed launch performs (24 h cache). The binary's own network behavior is outside what the wrapper shows; the README states that the binary's licence and session calls go to cloakbrowser.dev, directly or through the proxy depending on `--license-route` (`README.md:715-716`; Tier B).

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

The binary behaved legitimately in all tests, but it remains closed-source, the audited version (keyless 145) is no longer what any current wrapper downloads (keyed 156), and the keyed binary contacts a licence server by design (Tier B). The license prohibits reverse engineering. Separately, the wrapper's default arguments include `--no-sandbox` (see [How It Works §1](#1-fingerprint-seed-system)).

### Mitigation Recommendations

```bash
# Freeze binary updates once a build is cached (licence validation still runs)
export CLOAKBROWSER_AUTO_UPDATE=false

# Pin an exact binary version (rollback / reproducibility); paid key only —
# a free key ignores the pin (download.py:204-205)
export CLOAKBROWSER_VERSION=155.0.8059.39.1

# Use your own Chromium build (bypasses the proprietary binary and the licence check)
export CLOAKBROWSER_BINARY_PATH=/path/to/your/chromium
```

Running the vendor binary in a network-isolated container (`docker run --network=none`), recommended by earlier revisions, is not compatible with the keyed binary: the wrapper must reach cloakbrowser.dev to validate an uncached key, and the binary's licence calls fail with exit code 78 when the server is unreachable (`license.py:119-122`; binary behaviour Tier B). Network isolation now applies only to a self-supplied `CLOAKBROWSER_BINARY_PATH` build.

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
| **C++ Chromium patches** | 87 source-level modifications stated for the current binary (Chromium 156); vendor-stated, not JS injection or config flags |
| **Chromium engine** | TLS fingerprint reported to match real Chrome (Tier B) |
| **Drop-in Playwright/Puppeteer** | Same API — swap the import, keep your code; `build_launch_options()` for an existing Playwright instance (0.7.1) |
| **`humanize=True`** | One flag for Fitts'-law mouse strokes, measured keystroke timing, whole-notch wheel scrolling; full Playwright selector syntax and strict mode |
| **0.9 reCAPTCHA v3** | Vendor-reported score on the Pro/current build (Tier B) |
| **Latest build on a free key** | The README says a free email key gets the same build as Pro, limited to one concurrent session (Tier B) |
| **Multi-language** | Python + Node.js (TypeScript) + **.NET 8 / C#** with full type definitions |
| **Cross-platform** | Linux x64/arm64, macOS arm64/x64, Windows x64 |
| **Platform-aware defaults** | macOS runs native; Linux/Windows use a Windows persona automatically |
| **Coherent seed identity** | Screen/GPU/RAM/CPU/fonts/audio chosen together as a plausible real device |
| **Signed downloads** | Pinned Ed25519 signature on checksums, no bypass variable — authenticity, not just integrity |
| **GeoIP + WebRTC coherence** | Timezone/locale/WebRTC-IP from proxy or own IP (133 countries) |
| **Framework integrations** | browser-use, Crawl4AI, Crawlee, Scrapling, Stagehand, LangChain, Selenium, UC |
| **`cloakserve` CDP server** | Per-seed CDP routing for framework/Docker deployments; idle exit and kept profiles (0.6.5) |
| **Version pinning/rollback** | `browser_version=` / `CLOAKBROWSER_VERSION` for paid keys; a free key ignores it (`download.py:204-205`) |
| **Persistent profiles** | Cookies/localStorage across sessions; one fingerprint seed per profile |
| **Zero config** | Launch sets the seed and platform flags; no arguments required beyond a key |

### Disadvantages

| Con | Details |
|-----|---------|
| **Closed-source binary** | Proprietary Chromium — cannot verify the C++ patches |
| **Licence key on every launch** | Since 0.7.0 no launch works without a key (free by email, one concurrent session; paid for more). Non-interactive first runs fail with a sign-up link. The key is validated against cloakbrowser.dev (24 h cache) and the binary makes licence/session calls (Tier B) |
| **Audit lags shipping version** | Public audit covers a keyless Chromium 145; every current download is the keyed 156 |
| **`--no-sandbox`** | Runs with the Chromium sandbox disabled by default (`config.py:149`); `stealth_args=False` omits the default list |
| **Large download** | ~200MB compressed binary on first run |
| **Auto-update** | Binary update check on launch (hourly, can be frozen once a build is cached) |
| **No CAPTCHA solving** | Prevents CAPTCHAs from appearing, doesn't solve them |
| **License restrictions** | Binary license prohibits redistribution and reverse engineering |
| **Author-reported tests** | Detection results are the vendor's own, not independent reproductions |
| **Global side effects (Python sync)** | `time.sleep` is replaced process-wide while a sync browser is open (0.7.3) |
| **Playwright upper bound** | Python and JS cap Playwright below 1.66, .NET below 1.65; each newer Playwright is allowed only after testing (CHANGELOG 0.7.3) |

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

browser = launch()   # first run in a terminal asks for a key (free by email)
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

### License Key (Free Email Key or Pro)

```python
# Pass a key, or set CLOAKBROWSER_LICENSE_KEY / ~/.cloakbrowser/license.key
browser = launch(license_key="cb_xxxxxxxx")
```

`cloakbrowser login` (interactive) offers the free-key email flow or a pasted key; `cloakbrowser login <key>` validates and saves a key; `cloakbrowser logout` removes it and any pending claim (`cloakbrowser/__main__.py:561-625`).

### With Human Behavior

```python
browser = launch(humanize=True)                       # default preset
browser = launch(humanize=True, human_preset="careful")  # slower, more deliberate
page = browser.new_page()
page.goto("https://example.com")
page.locator("#email").fill("user@example.com")  # per-character typing
page.locator("button[type=submit]").click()       # Bézier stroke
```

### With Proxy + GeoIP + WebRTC

```python
# proxy: timezone/locale + WebRTC exit IP auto-detected
browser = launch(proxy="http://user:pass@proxy:8080", geoip=True)

# SOCKS5 also supported
browser = launch(proxy="socks5://user:pass@proxy:1080", geoip=True)

# no proxy: resolves your own public IP
browser = launch(geoip=True)
```

### Persistent Profile

```python
from cloakbrowser import launch_persistent_context

ctx = launch_persistent_context("./my-profile", headless=False)  # seed kept in ./my-profile/.cloakbrowser-seed
page = ctx.new_page()
page.goto("https://protected-site.com")
ctx.close()  # cookies/localStorage saved and restored next run
```

### Your Own Playwright Instance (0.7.1)

```python
from playwright.sync_api import sync_playwright
from cloakbrowser import build_launch_options, guard_browser, license_error_from

with sync_playwright() as pw:
    opts = build_launch_options(proxy="http://user:pass@proxy:8080", geoip=True)
    try:
        browser = pw.chromium.launch(**opts)
    except Exception as e:
        raise license_error_from(e, opts) or e
    guard_browser(browser, opts)
```

(Usage as given in the `build_launch_options` docstring, `browser.py:392-406`.)

### Fixed Fingerprint Seed / Version Pin

```python
# Same seed = same identity across launches (returning visitor)
browser = launch(args=["--fingerprint=42069"])

# Pin an exact binary (rollback if a new build regresses); paid key only
browser = launch(license_key="cb_xxxxxxxx", browser_version="155.0.8059.39.1")
```

### CLI / Docker

```bash
# Get a free key by email, or save a key you have
cloakbrowser login

# Diagnostics: which binary launches, license tier, session seats, fonts, geoip, deps
cloakbrowser info

# Quick bot-detection smoke test (the image has no binary; it needs a key)
docker run --rm -e CLOAKBROWSER_LICENSE_KEY cloakhq/cloakbrowser cloaktest

# CDP server mode (per-seed routing)
docker run -d --name cloak -p 127.0.0.1:9222:9222 -e CLOAKBROWSER_LICENSE_KEY cloakhq/cloakbrowser cloakserve
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
- Docker/VPS/Lambda deployments where a licence key can be supplied (a Docker image, `cloakserve` and an AWS Lambda example ship in the repo)

### Not Recommended For

- Security-critical environments (closed-source binary; sandbox disabled by default)
- Need to audit every component (use Camoufox, Clearcote, or Patchright)
- Air-gapped or network-isolated runs of the vendor binary (licence calls, Tier B)
- Projects that cannot register a licence key (the keyless build needs wrapper < 0.7 and is no longer updated)
- CAPTCHA solving (use SeleniumBase)
- Statistical fingerprint rotation (Camoufox draws statistical identities with fpgen)
- More than one concurrent session without a paid plan
- Minimal footprint (~200MB binary)

---

## Key Files

| File | Purpose |
|------|---------|
| `cloakbrowser/_version.py` | Wrapper version (`0.7.3`) |
| `cloakbrowser/config.py` | Stealth args, platform detection, seed (incl. per-profile `.cloakbrowser-seed`), signing keys, cache paths |
| `cloakbrowser/browser.py` | `launch()`, `launch_async()`, `launch_context()`, `launch_persistent_context()`, `build_launch_options()`, licence guards, proxy routing, sync-sleep pump |
| `cloakbrowser/__main__.py` | CLI: `install`, `info` / `doctor`, `update`, `clear-cache`, `login`, `logout` |
| `cloakbrowser/download.py` | Licence-gated binary download, free-key claim flow, Ed25519-signed verification, update logic |
| `cloakbrowser/license.py` | Key resolution and storage, validation/caching, free-key claim, session seats, denial-code mapping, latest-version lookup |
| `cloakbrowser/geoip.py` | MaxMind GeoIP timezone/locale + WebRTC-IP detection |
| `cloakbrowser/widevine.py` | Widevine CDM hint-file seeding |
| `cloakbrowser/human/engine.py` | Unified humanize engine: resolve, element states, wheel scrolling, hit-target check, keystroke scheduler |
| `cloakbrowser/human/world.py` | Per-frame CDP isolated worlds and helper library |
| `cloakbrowser/human/injected.py` | Loads Playwright's InjectedScript from the installed driver |
| `cloakbrowser/human/patch.py` | Class-level wiring into Playwright's sync and async APIs |
| `cloakbrowser/human/fields.py` | Per-input-type rules (typo suppression, value normalisation) |
| `cloakbrowser/human/mouse.py` | Fitts'-law stroke planning, Bézier paths, corrective strokes |
| `cloakbrowser/human/keyboard.py` | Adjacent-key and shift-symbol tables, key-pair gap model; legacy `human_type` helper |
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
| Human input simulation | `humanize` (Fitts'-law Bézier + keystroke timing; wrapper source, Tier A) | `humanize` config | none | PyAutoGUI clicks + jitter | Bézier + Gaussian noise |
| CAPTCHA handling | none | none | none | click-solving, several vendors | Cloudflare challenge only |
| Languages | Py / JS / .NET | Python | Py / JS / .NET | Python | Python |
| Source Available | Wrapper only | Fully open | Fully open | Fully open | Fully open |
| Key required | Yes (free or paid) | No | No | No | No |

---

## Conclusion

CloakBrowser modifies Chromium at the C++ source level (vendor-stated: **87 patches** on the current Chromium 156 build), and the author reports passes on major detection services including reCAPTCHA v3 (0.9 score) and Cloudflare Turnstile (Tier B). It has a **.NET/C# client**, **coherent seed-built hardware identities**, **Ed25519-signed downloads** with no bypass, **WebRTC-IP coherence**, **133-country GeoIP**, **version pinning for paid keys**, a **macOS persona**, **per-profile persistent seeds**, and a broad set of **AI-agent/framework integrations**.

The `humanize=True` flag adds behavioral simulation (Fitts'-law Bézier mouse strokes, keystroke timing with rollover and typos, whole-notch wheel scrolling) in readable wrapper code; the layer reads the DOM in a CDP isolated world and runs Playwright's own selector engine there (full selector syntax, strict mode, errors instead of fallbacks).

**The trade-offs.** The Chromium binary is **closed-source** and proprietary, and since wrapper 0.7.0 **every launch needs a licence key** (a free email key limited to one concurrent session, or a paid plan) that the wrapper validates against cloakbrowser.dev; the vendor states that the binary itself makes licence and session calls. The public security audit (9/9 tests passed, no malicious behavior found) covers a **keyless Chromium 145** binary, not the keyed 156 build now shipping, so its conclusions, including its offline result, do not transfer. The Ed25519 signing closes the old self-referential-checksum gap, but it proves authenticity, not what the patches do. The wrapper's default arguments include `--no-sandbox`.

**Applicability:** Chromium automation via the Playwright or Puppeteer API where engine-level fingerprint control and built-in humanized input are required, a closed binary is acceptable, and the deployment can supply a licence key and reach cloakbrowser.dev. The published figures (reCAPTCHA v3 0.9, FingerprintJS pass) are Tier B and stated for the Pro/current build.

**Constraints:** the engine is proprietary — the 87 patches cannot be read or independently verified, and the MIT license covers only the wrapper. The independent audit covered Chromium 145, which no current wrapper downloads. CloakBrowser's engine source is unpublished (the repository contains the wrapper only); Camoufox, Clearcote, and Obscura publish theirs.

---

*Analysis conducted for educational purposes. Use responsibly.*
