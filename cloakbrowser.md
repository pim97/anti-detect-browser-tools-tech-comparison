# CloakBrowser - Deep Technical Analysis

> **Tool Type:** Custom Chromium Build (Anti-Detect Browser)
> **Repository:** [github.com/CloakHQ/CloakBrowser](https://github.com/CloakHQ/CloakBrowser)
> **Approach:** C++ source-level fingerprint patches + CDP input behavior mimicking
> **Language:** Python, Node.js (TypeScript)
> **Effectiveness:** Very High (33 C++ patches, 0.9 reCAPTCHA v3 score)
> **Maintenance:** Active development (Chromium 145, Mar 2026)

---

## Table of Contents

- [What is CloakBrowser?](#what-is-cloakbrowser)
- [How It Works](#how-it-works)
- [Human Behavior System](#human-behavior-system)
- [GeoIP Integration](#geoip-integration)
- [Test Results](#test-results)
- [Security Audit](#security-audit)
- [Pros and Cons](#pros-and-cons)
- [Installation & Usage](#installation--usage)
- [When to Use](#when-to-use)

---

## What is CloakBrowser?

CloakBrowser is a **patched Chromium binary** with 33 source-level C++ modifications that spoof browser fingerprints at the engine level. It ships as a drop-in replacement for Playwright and Puppeteer — same API, same code, just swap the import.

**Key differentiator:** Unlike JavaScript injection or config-level patches, CloakBrowser compiles fingerprint spoofing directly into the Chromium binary. Detection scripts see native browser behavior because the modifications happen at the C++ layer — before JavaScript can inspect them.

**Second differentiator:** It targets **Chromium** (not Firefox), which means native Playwright API support, TLS fingerprints that match real Chrome, and compatibility with Chrome's ~65% market share.

---

## How It Works

### Architecture Overview

```
┌──────────────────────────────────────────────────────────────────┐
│                    CLOAKBROWSER ARCHITECTURE                       │
├──────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────────┐    ┌──────────────────────┐                │
│  │  Python / JS     │    │  Platform Detection   │                │
│  │  Wrapper          │    │  (macOS/Linux/Win)    │                │
│  └────────┬─────────┘    └─────────┬────────────┘                │
│           │                        │                              │
│           ▼                        ▼                              │
│  ┌──────────────────────────────────────────────┐                │
│  │     Stealth Args + Fingerprint Seed           │                │
│  │  --fingerprint=<random>                       │                │
│  │  --fingerprint-platform=windows               │                │
│  │  --fingerprint-gpu-vendor=Google Inc. (NVIDIA) │                │
│  │  --fingerprint-gpu-renderer=ANGLE (NVIDIA...) │                │
│  │  --disable-blink-features=AutomationControlled│                │
│  └──────────────────────┬───────────────────────┘                │
│                          │                                        │
│                          ▼                                        │
│  ┌──────────────────────────────────────────────┐                │
│  │      PATCHED CHROMIUM BINARY (441 MB)        │                │
│  │  ┌────────────────────────────────────────┐  │                │
│  │  │  33 C++ Source-Level Patches            │  │                │
│  │  │  - Canvas fingerprint randomization     │  │                │
│  │  │  - WebGL/WebGPU vendor/renderer spoof   │  │                │
│  │  │  - Audio context noise injection        │  │                │
│  │  │  - Screen/hardware/memory spoofing      │  │                │
│  │  │  - CDP input behavior mimicking (5 new) │  │                │
│  │  │  - Font enumeration masking             │  │                │
│  │  │  - navigator.webdriver = false           │  │                │
│  │  │  - Automation signal removal             │  │                │
│  │  │  - Plugin list (5 real Chrome plugins)   │  │                │
│  │  │  - Native locale spoofing (C++ level)    │  │                │
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

### 1. Fingerprint Seed System

Every launch generates a **random seed** that deterministically controls all fingerprint values. Same seed = same fingerprint across launches (useful for returning visitor patterns).

From `cloakbrowser/config.py`:

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
        "--disable-blink-features=AutomationControlled",
        f"--fingerprint={seed}",
    ]

    if system == "Darwin":
        return base + [
            "--fingerprint-platform=macos",
            "--fingerprint-gpu-vendor=Google Inc. (Apple)",
            "--fingerprint-gpu-renderer=ANGLE (Apple, ANGLE Metal Renderer: Apple M3, ...)",
        ]

    # Linux/Windows: Windows fingerprint profile
    return base + [
        "--fingerprint-platform=windows",
        "--fingerprint-gpu-vendor=Google Inc. (NVIDIA)",
        "--fingerprint-gpu-renderer=ANGLE (NVIDIA, NVIDIA GeForce RTX 3070 ...)",
    ]
```

**Why platform-aware defaults matter:**
- macOS binary runs as a native Mac browser (Apple GPU, macOS UA) — spoofing Windows on Mac creates detectable font/GPU mismatches
- Linux binary spoofs as Windows (more common fingerprint, harder to cluster)
- The seed auto-generates hardware concurrency (8), device memory (8), screen dimensions (1920x1080)

### 2. C++ Source-Level Patches (33 Patches)

The patches are compiled into the Chromium binary. They cannot be detected by JavaScript because the modifications happen at the native code level:

| Patch Category | Count | What It Does |
|---------------|:-----:|--------------|
| Canvas fingerprint | 1 | Randomized noise on canvas operations based on seed |
| WebGL/WebGPU | 3 | Vendor/renderer string spoofing, adapter features |
| Audio context | 1 | Noise injection in audio fingerprinting |
| Screen/Window | 2 | Dimensions, pixel ratio, taskbar height |
| Hardware | 2 | concurrency, deviceMemory from seed |
| CDP input mimicking | 5 | Pointer, keyboard, mouse events match real user signals |
| Automation signals | 4 | webdriver=false, plugin list, window.chrome, UA cleanup |
| Font enumeration | 1 | Font list masking and cross-platform dir |
| Locale/timezone | 2 | Native C++ locale spoofing (not CDP emulation) |
| Storage quota | 1 | Normalized to pass FingerprintJS |
| Other | 11 | Brand spoofing, geolocation, platform version, etc. |

**Why C++ patches are hard to detect:**
- `navigator.webdriver` returns `false` from native code
- `navigator.plugins.length` returns `5` (real Chrome plugin list)
- `window.chrome` is present as an `object` (not `undefined`)
- User-Agent has no `HeadlessChrome` leak
- Canvas/WebGL noise is applied at the rendering level, not via JavaScript injection
- `Object.getOwnPropertyDescriptor()` shows native functions
- No timing differences between real and spoofed values

### 3. CDP Input Behavior Mimicking

One of CloakBrowser's newer innovations: **5 source-level patches** that make CDP-dispatched input events produce the same signals as real user interactions. This is critical because:

```
Normal Playwright:
  page.click() → CDP Input.dispatchMouseEvent → DETECTABLE timing/signal pattern

CloakBrowser:
  page.click() → CDP Input.dispatchMouseEvent → Patched to produce REAL user signals
```

This is why CloakBrowser achieves a **0.9 reCAPTCHA v3 score** — the input events look human at the browser engine level.

### 4. Binary Download & Verification

From `cloakbrowser/download.py`:

```
pip install cloakbrowser
    → first launch triggers ensure_binary()
    → downloads from cloakbrowser.dev (primary) or GitHub Releases (fallback)
    → fetches SHA256SUMS from same server
    → verifies hash matches
    → extracts to ~/.cloakbrowser/chromium-{version}/
    → background thread checks for updates every hour
```

Binary sizes: ~200MB compressed, 441MB extracted (Linux x64).

---

## Human Behavior System

CloakBrowser includes a comprehensive human behavior simulation system activated with a single flag: `humanize=True`. All Playwright API calls are transparently replaced with human-like equivalents.

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
5. 15% chance of overshoot past target, then correction
6. Burst pauses every few steps (mimics micro-hesitations)

### Keyboard Typing — Per-Character Simulation

From `cloakbrowser/human/keyboard.py`:

```python
NEARBY_KEYS = {
    'a': 'sqwz', 'b': 'vghn', 'c': 'xdfv', 'd': 'sfecx',
    'e': 'wrsdf', 'f': 'dgrtcv', 'g': 'fhtyb', ...
}

def human_type(page, raw, text, cfg):
    for i, ch in enumerate(text):
        # 2% mistype chance — types nearby key, then backspace corrects
        if random.random() < cfg.mistype_chance and ch.isalnum():
            wrong = _get_nearby_key(ch)  # keyboard-layout-aware typo
            _type_normal_char(raw, wrong, cfg)
            sleep_ms(rand_range(cfg.mistype_delay_notice))  # "notice" delay
            raw.down("Backspace")
            sleep_ms(rand_range(cfg.key_hold))
            raw.up("Backspace")
            sleep_ms(rand_range(cfg.mistype_delay_correct))

        # Different handling for uppercase, symbols, normal chars
        if ch.isupper() and ch.isalpha():
            _type_shifted_char(page, raw, ch, cfg)  # Shift down → char → Shift up
        elif ch in SHIFT_SYMBOLS:
            _type_shift_symbol(page, raw, ch, cfg)
        else:
            _type_normal_char(raw, ch, cfg)

        # Random thinking pauses (10% chance)
        if random.random() < cfg.typing_pause_chance:
            sleep_ms(rand_range(cfg.typing_pause_range))
```

**What makes this realistic:**
- Typos use keyboard-layout proximity (e.g., 'a' → 'sqwz'), not random characters
- Different timing for shift keys, alphanumeric, and symbols
- Individual key hold durations (down → delay → up)
- Thinking pauses every ~1-10 characters
- Non-ASCII characters (Cyrillic, CJK, emoji) use `insertText` fallback

### Interaction Summary

| Interaction | Default Playwright | With `humanize=True` |
|---|---|---|
| Mouse movement | Instant teleport | Bézier curve with easing and overshoot |
| Clicks | Instant | Aim delay (60-200ms) + hold duration (40-150ms) |
| Keyboard | Instant fill | Per-character with 70ms ± 40ms variance |
| Scroll | Jump | Accelerate → cruise → decelerate micro-steps |
| `fill()` | Instant value set | Clear field + type character by character |
| Between actions | Nothing | Optional idle micro-movements |

### Presets

| Preset | Typing Speed | Aim Delay | Description |
|--------|:-----------:|:---------:|-------------|
| `default` | 70ms/char | 60-140ms | Normal browsing speed |
| `careful` | 100ms/char | 80-200ms | Slower, more deliberate, idle between actions |

---

## GeoIP Integration

CloakBrowser can automatically detect timezone and locale from proxy IP addresses:

```python
from cloakbrowser import launch

# Auto-detect timezone/locale from proxy exit IP
browser = launch(proxy="http://user:pass@us-proxy:8080", geoip=True)
# → Detects America/New_York timezone, en-US locale
```

How it works:
1. Downloads MaxMind GeoLite2-City database (~70MB) on first use
2. Caches in `~/.cloakbrowser/geoip/` with 30-day refresh cycle
3. Resolves proxy exit IP against 3 IP echo services
4. Extracts country → locale mapping (50+ countries)
5. Extracts timezone from MaxMind data
6. Sets `--fingerprint-timezone` and `--lang` binary flags (not detectable CDP emulation)

Explicit timezone/locale always override auto-detection. Failures degrade gracefully (never crashes).

---

## Test Results

All tests verified against live detection services (Chromium 145, Mar 2026):

| Detection Service | Stock Playwright | CloakBrowser | Notes |
|---|---|---|---|
| **reCAPTCHA v3** | 0.1 (bot) | **0.9** (human) | Server-side verified |
| **Cloudflare Turnstile** (non-interactive) | FAIL | **PASS** | Auto-resolve |
| **Cloudflare Turnstile** (managed) | FAIL | **PASS** | Single click |
| **ShieldSquare** | BLOCKED | **PASS** | Production site |
| **FingerprintJS** bot detection | DETECTED | **PASS** | demo.fingerprint.com |
| **BrowserScan** bot detection | DETECTED | **NORMAL** (4/4) | browserscan.net |
| **bot.incolumitas.com** | 13 fails | **1 fail** | WEBDRIVER spec only |
| **deviceandbrowserinfo.com** | 6 true flags | **0 true flags** | `isBot: false` |
| `navigator.webdriver` | `true` | **`false`** | Source-level patch |
| `navigator.plugins.length` | 0 | **5** | Real plugin list |
| `window.chrome` | `undefined` | **`object`** | Present like real Chrome |
| UA string | `HeadlessChrome` | **`Chrome/145.0.0.0`** | No headless leak |
| CDP detection | Detected | **Not detected** | `isAutomatedWithCDP: false` |
| TLS fingerprint | Mismatch | **Identical to Chrome** | ja3n/ja4/akamai match |

### Known Acceptable Failures

| Test | Result | Why |
|------|--------|-----|
| WEBDRIVER spec (incolumitas) | False positive | Spec-level detection, expected |
| connectionRTT | Flagged | Datacenter latency, not browser fingerprint |

---

## Security Audit

> **Full audit:** [CloakBrowser Security Audit](https://github.com/pim97/cloakbrowser-analyze)
> **Audit date:** March 2026 | **Binary:** Chromium 145.0.7632.159.7 (Linux x64)

### Trust Model

| Component | Source Available | Can You Audit It? |
|-----------|:-:|---|
| Python wrapper (`cloakbrowser/`) | Yes (MIT) | Fully readable |
| JavaScript wrapper (`js/`) | Yes (MIT) | Fully readable |
| Chromium binary (`chrome`) | **No** (Proprietary) | **Cannot inspect the 33 C++ patches** |
| SHA-256 checksums | Same server | Self-referential |

### Audit Results: 9/9 Tests Passed

```
✓ No suspicious strings/URLs in binary (2.9M strings analyzed)
✓ No unexpected network connections (only PyPI/GitHub update check from wrapper)
✓ No sensitive file access (.ssh, .aws, .env, wallets)
✓ No unknown processes spawned (standard Chromium architecture)
✓ No suspicious DNS queries
✓ Standard ELF binary with standard shared libraries
✓ No environment variable sniffing or exfiltration (canary test passed)
✓ Works fine with network completely blocked (no C2 dependency)
✓ Not flagged by VirusTotal (hash not in database)
```

### What the Audit Cannot Prove

| Evasion Technique | Detectable by Audit? |
|---|:-:|
| Always-on data exfiltration | Yes |
| Time bomb (activates after N days) | **No** |
| Conditional trigger (specific sites) | **No** |
| Encrypted exfiltration (HTTPS traffic) | **No** |
| Targeted payload (specific users) | **No** |

### Risk Level: MEDIUM

The binary behaves legitimately in all tests, but it remains closed-source. The license prohibits reverse engineering.

### Mitigation Recommendations

```bash
# Disable auto-update (prevents silent binary replacement)
export CLOAKBROWSER_AUTO_UPDATE=false

# Run in Docker with restricted network
docker run --network=none cloakbrowser-app

# Use your own Chromium build (bypass proprietary binary)
export CLOAKBROWSER_BINARY_PATH=/path/to/your/chromium

# Pin binary version and verify SHA-256
# f1783cf24eb9abdf262a607c2a41be23e28343000849dde81a452adb0ff9d8fa
```

### Risk Comparison

| Tool | Source Available | Binary Auditable | Risk Level |
|------|:-:|:-:|---|
| **Camoufox** | Fully open source | Yes — compile yourself | Lowest |
| **Patchright** | Fully open source | Yes — compile yourself | Lowest |
| **SeleniumBase** | Fully open source | Uses stock ChromeDriver | Low |
| **CloakBrowser** | Wrapper only | **No** — proprietary binary | **Medium** |

---

## Pros and Cons

### Advantages

| Pro | Details |
|-----|---------|
| **C++ Chromium patches** | 33 source-level modifications — not JS injection, not config flags |
| **Chromium engine** | TLS fingerprint matches real Chrome, ~65% market share |
| **Drop-in Playwright/Puppeteer** | Same API — swap the import, keep your code |
| **`humanize=True`** | One flag for Bézier mouse, typing simulation, scroll patterns |
| **0.9 reCAPTCHA v3** | Human-level score with CDP input mimicking patches |
| **Multi-language** | Python + Node.js (TypeScript) with full type definitions |
| **Cross-platform** | Linux x64/arm64, macOS arm64/x64, Windows x64 |
| **Platform-aware defaults** | macOS runs native; Linux spoofs as Windows automatically |
| **Persistent profiles** | Cookies/localStorage across sessions, bypasses incognito detection |
| **GeoIP auto-detection** | Timezone/locale from proxy IP (MaxMind integration) |
| **Auto-updating** | Background binary updates, always latest stealth build |
| **Zero config** | Stealthy by default — no flags needed |

### Disadvantages

| Con | Details |
|-----|---------|
| **Closed-source binary** | 441MB proprietary Chromium — cannot verify the 33 C++ patches |
| **Auto-update daemon** | Background thread checks every hour (can be disabled) |
| **`--no-sandbox`** | Runs with Chromium sandbox disabled by default |
| **Large download** | ~200MB compressed binary on first run |
| **Self-referential checksums** | SHA-256 hashes hosted on same server as binary |
| **No CAPTCHA solving** | Prevents CAPTCHAs from appearing, doesn't solve them |
| **License restrictions** | Binary license prohibits redistribution and reverse engineering |

---

## Installation & Usage

### Quick Start

```bash
# Python
pip install cloakbrowser

# Node.js (Playwright)
npm install cloakbrowser playwright-core

# Node.js (Puppeteer)
npm install cloakbrowser puppeteer-core
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

### With Human Behavior

```python
browser = launch(humanize=True)
page = browser.new_page()
page.goto("https://example.com")
page.locator("#email").fill("user@example.com")  # per-character typing
page.locator("button[type=submit]").click()       # Bézier curve movement
```

### With Proxy + GeoIP

```python
browser = launch(
    proxy="http://user:pass@proxy:8080",
    geoip=True,  # auto-detect timezone/locale from proxy IP
)
```

### Persistent Profile

```python
from cloakbrowser import launch_persistent_context

# First run — creates profile
ctx = launch_persistent_context("./my-profile", headless=False)
page = ctx.new_page()
page.goto("https://protected-site.com")
ctx.close()  # profile saved

# Next run — cookies, localStorage restored
ctx = launch_persistent_context("./my-profile", headless=False)
```

### Fixed Fingerprint Seed

```python
# Same seed = same identity across launches (returning visitor)
browser = launch(args=["--fingerprint=42069"])
```

### Docker

```bash
# Quick test
docker run --rm cloakhq/cloakbrowser cloaktest

# CDP server mode
docker run -d --name cloak -p 127.0.0.1:9222:9222 cloakhq/cloakbrowser cloakserve
```

---

## When to Use

### Recommended For

- Chromium-required targets (sites that block or flag Firefox)
- Need Playwright/Puppeteer API compatibility (existing code)
- High stealth with zero configuration
- Behavioral detection bypass (`humanize=True`)
- Both Python and Node.js projects
- Persistent sessions with fingerprint consistency
- Sites with reCAPTCHA v3 scoring
- Docker/VPS deployments (works identically everywhere)

### Not Recommended For

- Security-critical environments (closed-source binary risk)
- Need to audit every component (use Camoufox or Patchright instead)
- CAPTCHA solving (use SeleniumBase)
- Statistical fingerprint rotation (use Camoufox + BrowserForge)
- Minimal footprint (441MB binary)

---

## Key Files

| File | Purpose |
|------|---------|
| `cloakbrowser/config.py` | Stealth args, platform detection, fingerprint seed |
| `cloakbrowser/browser.py` | `launch()`, `launch_async()`, `launch_persistent_context()` |
| `cloakbrowser/download.py` | Binary download, SHA-256 verification, auto-update |
| `cloakbrowser/geoip.py` | MaxMind GeoIP timezone/locale detection |
| `cloakbrowser/human/mouse.py` | Bézier curve movement, click targeting, overshoot |
| `cloakbrowser/human/keyboard.py` | Per-character typing, typo simulation, shift handling |
| `cloakbrowser/human/config.py` | `HumanConfig` dataclass, presets |

---

## Comparison

| Feature | CloakBrowser | Camoufox | Patchright | SeleniumBase | Botasaurus |
|---------|:----------:|:--------:|:----------:|:------------:|:----------:|
| Spoofing Level | C++ (Chromium) | C++ (Firefox) | Binary patch | Config + UC | JS wrapper |
| Browser | Chromium | Firefox | Chromium | Chrome | Chrome |
| Playwright API | ✅ Native | Via Juggler | ✅ Native | ❌ Selenium | ❌ Selenium |
| Fingerprint Rotation | Seed-based | ✅ BrowserForge | Partial | Partial | Partial |
| Human Simulation | ✅ Full (Bézier + typing) | ✅ Good | ⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| reCAPTCHA v3 Score | **0.9** | 0.7-0.9 | 0.3-0.7 | 0.3-0.7 | 0.3-0.5 |
| CAPTCHA Solving | ❌ | ❌ | ❌ | ✅ Built-in | ⭐⭐ |
| Source Available | Wrapper only | Fully open | Fully open | Fully open | Fully open |
| Detection Difficulty | Very Hard | Very Hard | Hard | Hard | Medium |

---

## Conclusion

CloakBrowser represents the **strongest Chromium-based anti-detection tool** currently available. By modifying Chromium at the C++ source level (33 patches), it achieves native-appearing fingerprint spoofing that passes all major detection services including reCAPTCHA v3 (0.9 score) and Cloudflare Turnstile.

The `humanize=True` flag adds comprehensive behavioral simulation (Bézier mouse curves, realistic typing with typos, scroll patterns) — making it effective against both fingerprint and behavioral detection layers.

**The trade-off:** The Chromium binary is **closed-source** and proprietary. An independent security audit (9/9 tests passed) found no malicious behavior, but the binary cannot be fully verified. If auditability is critical, use Camoufox (open-source Firefox) or Patchright (open-source Playwright patches) instead.

**Best for:** Maximum Chromium stealth with Playwright API compatibility and zero configuration.

**Limitation:** Proprietary binary requires trust in the CloakBrowser team.

---

*Analysis conducted for educational purposes. Use responsibly.*
