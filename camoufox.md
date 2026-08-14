# Camoufox - Deep Technical Analysis

> **Tool Type:** Custom Firefox Build (Anti-Detect Browser)
> **Repository:** [github.com/daijro/camoufox](https://github.com/daijro/camoufox)
> **Approach:** C++ level fingerprint injection + Juggler protocol isolation
> **Verified in source (Tier A):** 34 C++ patch files in `patches/` plus 2 in `patches/playwright/`, including `fingerprint-injection`, `navigator-spoofing`, `screen-spoofing`, `locale-spoofing`, `webrtc-ip-spoofing`, `anti-font-fingerprinting`, `audio-fingerprint-manager`. Input simulation is exposed as the `humanize`, `humanize:minTime`, `humanize:maxTime` config properties (`settings/properties.json:69-71`). `Runtime.enable` is not applicable: automation runs over Juggler, not CDP.
> **Anti-bot service claims:** **none** — the project makes no claims about Cloudflare, DataDome, Kasada or similar, and its README instead **documents a limitation**: some WAFs probe SpiderMonkey engine behaviour, which a Firefox fork cannot disguise (**Tier D** for coverage; the limitation is **Tier B**)
> **Maintenance:** Actively developed — browser `v152.0.4-beta.28` (2026-07-19); Python wrapper `camoufox` **0.5.4** on PyPI (2026-07-16; repo `pythonlib` at 0.5.5 dev). 11.1k stars, 30 contributors, last push 2026-08-12. MPL-2.0.
> **Verified:** 2026-08-14 against `daijro/camoufox` @ `7add1ef`.

---

## Table of Contents

- [What is Camoufox?](#what-is-camoufox)
- [Version & Status (2026-08)](#version--status-2026-08)
- [How It Works](#how-it-works)
- [Properties of C++-Level Spoofing](#properties-of-c-level-spoofing)
- [Fingerprint Capabilities](#fingerprint-capabilities)
- [What's New Since the Last Analysis](#whats-new-since-the-last-analysis)
- [Pros and Cons](#pros-and-cons)
- [Installation & Usage](#installation--usage)
- [When to Use](#when-to-use)
- [Key Files](#key-files)

---

## What is Camoufox?

Camoufox is a **custom-built Firefox browser** designed specifically for web scraping and automation stealth. Unlike tools that patch or inject into existing browsers, Camoufox compiles Firefox from source with modifications at the C++ implementation level.

**Mechanism:** fingerprint values are substituted inside Firefox's C++ getters, before any value reaches JavaScript. Consequently the substitution is not observable through the techniques that detect JS-level patching — property-descriptor inspection, prototype-chain checks, or `Function.prototype.toString` comparison — because no JS-level wrapper exists. This constrains one detection method; it does not make the browser undetectable, and the project's own README documents a residual signal (SpiderMonkey engine behaviour identifies the browser as Firefox-based).

The project is authored by **daijro** (also the author of [BrowserForge](https://github.com/daijro/browserforge)). As of 2026-08-14 it has ~11.1k GitHub stars and 30 contributors. The C++ browser fork tracks upstream Firefox — the current base is **Firefox 152.0.4** (`upstream.sh`). A thin Python library (`camoufox`) wraps Playwright's Firefox driver to launch the binary and feed it a fingerprint config.

---

## Version & Status (2026-08)

| Item | Value | Evidence |
|------|-------|----------|
| Latest release | `v152.0.4-beta.28`, 2026-07-19 | GitHub Releases API |
| Latest non-pre-release | `v152.0.4-beta.28`, 2026-07-19 | GitHub Releases API |
| Upstream Firefox base | **152.0.4** | `upstream.sh` → `version=152.0.4` |
| Python package (PyPI) | **0.5.4** (2026-07-16) | `pip index` / PyPI |
| Python package (repo dev) | **0.5.5** | `pythonlib/pyproject.toml` → `version = "0.5.5"` |
| Browser license | **MPL-2.0** (Firefox fork) | root `LICENSE` |
| Python wrapper license | **MIT** | `pythonlib/pyproject.toml` → `license = "MIT"` |
| Primary language | **C++** (browser), Python (wrapper) | GitHub repo language stats |
| Last commit | 2026-08-12 (`7add1ef`) | `git log` |
| Camoufox source patches | **34** stealth/debloat patches + **2** Playwright/Juggler patches | `patches/*.patch` (34), `patches/playwright/*.patch` (2) |

> Note the two-license split: the browser is a Firefox fork and is therefore **MPL-2.0**, while the `camoufox` Python launcher library is **MIT**. Earlier analyses that called the whole project "MIT" or "MPL" were only half right.

> The `v152.0.x` line **drops support for 32-bit systems and macOS x86_64** (Apple Silicon / x86_64-Linux / x86_64-Windows / arm64 going forward).

---

## How It Works

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    CAMOUFOX ARCHITECTURE                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────────┐    ┌─────────────────┐                     │
│  │  Python Library │───▶│  BrowserForge   │                     │
│  │  (camoufox)     │    │  Fingerprints   │                     │
│  │                 │    │  OR real presets│                     │
│  └────────┬────────┘    └────────┬────────┘                     │
│           │                      │                               │
│           ▼                      ▼                               │
│  ┌─────────────────────────────────────────┐                    │
│  │      JSON Config Generation (MaskConfig) │                    │
│  │   (Statistically accurate profiles OR    │                    │
│  │    real in-the-wild fingerprint presets) │                    │
│  └────────────────────┬────────────────────┘                    │
│                       │  (passed via CAMOU_CONFIG env / config)  │
│                       ▼                                          │
│  ┌─────────────────────────────────────────┐                    │
│  │      CUSTOM FIREFOX 152 BUILD            │                    │
│  │  ┌───────────────────────────────────┐  │                    │
│  │  │  C++ Fingerprint Injection        │  │                    │
│  │  │  (MaskConfig::Get* lookups)       │  │                    │
│  │  │  - Navigator properties           │  │                    │
│  │  │  - Screen/Window dimensions       │  │                    │
│  │  │  - WebGL params + shader precision│  │                    │
│  │  │  - Audio context (seeded noise)   │  │                    │
│  │  │  - Fonts / voices / media devices │  │                    │
│  │  │  - HTTP UA + Accept-Language      │  │                    │
│  │  └───────────────────────────────────┘  │                    │
│  │  ┌───────────────────────────────────┐  │                    │
│  │  │  Patched Juggler Protocol         │  │                    │
│  │  │  - Isolated execution scope       │  │                    │
│  │  │  - No page-visible artifacts      │  │                    │
│  │  │  - webdriver = false (C++ level)  │  │                    │
│  │  │  - Optional main-world eval (mw:) │  │                    │
│  │  └───────────────────────────────────┘  │                    │
│  └─────────────────────────────────────────┘                    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

The config is read by a single C++ helper, `additions/camoucfg/MaskConfig.hpp`, which every patch calls into. Patches ask it for a value (`MaskConfig::GetDouble("window.innerWidth")`, `MaskConfig::GetString("headers.User-Agent")`, etc.); if the user/BrowserForge set one, the spoofed value is returned, otherwise the code falls through to the real Firefox implementation.

### C++ Level Fingerprint Injection

The core innovation is modifying Firefox's C++ source code to intercept property getters. From `patches/fingerprint-injection.patch` (real, current source):

```cpp
// dom/base/nsGlobalWindowInner.cpp
double nsGlobalWindowInner::GetInnerWidth(ErrorResult& aError) {
  // Camoufox intercepts BEFORE the original implementation
  if (auto value = MaskConfig::GetDouble("window.innerWidth"))
    return value.value();  // Return spoofed value
  // Fall through to original only if no spoof configured
  FORWARD_TO_OUTER_OR_THROW(GetInnerWidthOuter, (aError), aError, 0);
}

int32_t nsGlobalWindowInner::GetScreenX(CallerType aCallerType,
                                        ErrorResult& aError) {
  if (auto value = MaskConfig::GetInt32("window.screenX")) return value.value();
  FORWARD_TO_OUTER_OR_THROW(GetScreenXOuter, (aCallerType, aError), aError, 0);
}
```

The same `patches/fingerprint-injection.patch` also hooks `GetInnerHeight`, `GetOuterWidth/Height`, `GetScreenY`, `GetDevicePixelRatio`, scroll min/max and more — all through `MaskConfig::Get*`.

**Why this is undetectable:**
- The getter returns the spoofed value directly from C++
- There's no JavaScript wrapper or proxy
- `Object.getOwnPropertyDescriptor()` shows a native function
- `toString()` returns `[native code]`
- No timing difference between real and spoofed values

### HTTP Header Spoofing (network layer, not TLS)

`patches/network-patches.patch` hooks `netwerk/protocol/http/nsHttpHandler.cpp` to override the `User-Agent` and `Accept-Language` request headers from the config:

```cpp
// netwerk/protocol/http/nsHttpHandler.cpp
if (auto value = MaskConfig::GetString("headers.User-Agent")) { /* use spoofed UA */ }
...
if (auto value = MaskConfig::GetString("headers.Accept-Language")) { /* use spoofed AL */ }
```

> **Important limitation:** this is HTTP-header spoofing, **not TLS/JA3/JA4 fingerprint impersonation.** Camoufox sends a real Firefox TLS ClientHello (because it *is* Firefox), which is coherent for a Firefox persona but cannot be changed to look like Chrome. There is no ja3/ja4 rewriting in the source.

### Juggler Protocol Isolation

Camoufox uses **Juggler** (Firefox's automation protocol used by Playwright) instead of CDP. The full Juggler implementation lives under `additions/juggler/` and is patched to run in an isolated scope:

```
┌─────────────────────────────────────────────────────────────┐
│                    PAGE EXECUTION                            │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────────────┐  ┌──────────────────────┐         │
│  │   PAGE SCOPE         │  │   JUGGLER SCOPE      │         │
│  │   (Visible to JS)    │  │   (Isolated)         │         │
│  │                      │  │                      │         │
│  │  - User's website    │  │  - Playwright code   │         │
│  │  - Detection scripts │  │  - Element queries   │         │
│  │  - Anti-bot checks   │  │  - Script injection  │         │
│  │                      │  │  - Event listeners   │         │
│  │  ❌ Cannot see       │  │                      │         │
│  │     Juggler scope    │  │  ✅ Can read/modify  │         │
│  │                      │  │     page scope       │         │
│  └──────────────────────┘  └──────────────────────┘         │
│                                                              │
│  🔒 Complete isolation - no __playwright__ variables leak   │
│  🔓 Opt-in main-world eval via "mw:" script prefix          │
└─────────────────────────────────────────────────────────────┘
```

From `patches/playwright/1-leak-fixes.patch` — the webdriver property fix at C++ level. Upstream Firefox's `Navigator::Webdriver()` returns `true` under automation; Camoufox rewrites it to a flat `false`:

```cpp
// dom/base/Navigator.cpp
/* static */
bool Navigator::Webdriver() {
  // Camoufox: strip the Marionette/RemoteAgent checks and just return false
  return false;
}
```

The same leak-fixes patch also neutralizes Playwright's other automation tells (enterprise-policy hints, etc.). A separate opt-in, `main_world_eval=True`, lets you run a script in the page's main world by prefixing it with `mw:` (e.g. `page.evaluate("mw:" + script)`) — otherwise Playwright scripts stay in the isolated world.

### BrowserForge Integration (default fingerprint synthesis)

When you don't supply values, Camoufox fills them with **BrowserForge**, which models the real-world statistical distribution of device characteristics:

```python
# pythonlib/camoufox/fingerprints.py
from browserforge.fingerprints import FingerprintGenerator

FP_GENERATOR = FingerprintGenerator(browser='firefox', os=('linux', 'macos', 'windows'))
```

This means:
- ~5% of fingerprints will be Linux (matching real market share)
- Screen resolutions follow actual usage distribution
- Hardware combinations are realistic (no Windows + Apple GPU)

### Real Fingerprint Presets (newer, opt-in)

For evasion against consistency checks that BrowserForge synthesis can trip, Camoufox now ships a bundle of **real** fingerprints scraped from in-the-wild Firefox traffic (`pythonlib/camoufox/fingerprint-presets-v150.json`). Verified counts from the file: **312 presets** — 180 Windows / 67 macOS / 65 Linux — covering Firefox v149–v152 (`min_firefox_version: 149`, `source: roverfox_fingerprints`). Opt in with `fingerprint_preset=True`; the library auto-routes by binary version and rewrites UA strings to match the active binary. Pass a preset dict instead of `True` to pin a specific identity.

---

## Properties of C++-Level Spoofing

### vs. JavaScript Injection (puppeteer-extra-stealth, etc.)

| Detection Method | JS Injection | Camoufox |
|-----------------|--------------|----------|
| `Object.getOwnPropertyDescriptor` check | ❌ Detectable | ✅ Native |
| `Function.toString()` returns `[native code]` | ❌ Often fails | ✅ Always |
| Worker vs main context mismatch | ❌ Detectable | ✅ Consistent (C++ applies everywhere) |
| Property access timing analysis | ❌ Delay | ✅ Native speed |

### vs. CDP-based Solutions (Playwright/Chrome, Puppeteer)

| Detection Method | CDP-based | Camoufox |
|-----------------|-----------|----------|
| `navigator.webdriver` | Patchable but leaky | ✅ C++ level false |
| `window.__playwright__` | ❌ Present | ✅ Isolated Juggler scope |
| `Runtime.enable` detection | ❌ Detectable | ✅ Uses Juggler, not CDP |

---

## Fingerprint Capabilities

Coverage is broad and applied natively. The 32 source patches map onto these areas:

| Category | Properties Spoofed | Patch(es) |
|----------|-------------------|-----------|
| **Navigator** | userAgent, platform, vendor, hardwareConcurrency, deviceMemory, languages, oscpu | `navigator-spoofing.patch`, `fingerprint-injection.patch` |
| **Screen** | width, height, availWidth/Height, colorDepth, pixelDepth | `screen-spoofing.patch` |
| **Window** | innerWidth/Height, outerWidth/Height, screenX/Y, devicePixelRatio | `fingerprint-injection.patch` |
| **WebGL** | vendor, renderer (UNMASKED_*), supported extensions, context attributes, shader precision formats | `webgl-spoofing.patch` |
| **Audio** | sampleRate, output latency, channel counts + seeded per-context noise | `audio-context-spoofing.patch`, `audio-fingerprint-manager.patch` |
| **Fonts** | font list + metrics spoofing, anti font-fingerprinting, system-UI font | `font-list-spoofing.patch`, `font-hijacker.patch`, `anti-font-fingerprinting.patch`, `system-ui-font-spoofing.patch` |
| **Speech/Voices** | speechSynthesis voices | `speech-voices-spoofing.patch`, `voice-spoofing.patch` |
| **Media devices** | enumerateDevices output | `media-device-spoofing.patch` |
| **Network** | WebRTC ICE IP (protocol level), HTTP User-Agent + Accept-Language | `webrtc-ip-spoofing.patch`, `network-patches.patch` |
| **Geo/Locale** | geolocation, timezone, locale (Intl) | `geolocation-spoofing.patch`, `timezone-spoofing.patch`, `locale-spoofing.patch` |
| **DOM/behavior** | closed shadow-root piercing for automation, forced default pointer, disabled CSS animations | `shadow-root-bypass.patch`, `force-default-pointer.patch`, `no-css-animations.patch` |

WebRTC spoofing is a real protocol-level implementation (implemented in `webrtc-ip-spoofing.patch`, keyed per user-context), not just a JS toggle — though you can also fully disable WebRTC with `block_webrtc=True`.

---

## What's New Since the Last Analysis

The prior page was accurate on the core architecture, but a lot has shipped:

- **Firefox base moved to 152** (from the 130s era). Releases now track modern Firefox; the current line is `v152.0.4-beta.28` (2026-07-19).
- **Real fingerprint presets** (`fingerprint_preset=True`): 312 real Firefox fingerprints (180 Win / 67 macOS / 65 Linux, v149–v152) as an alternative to synthetic BrowserForge output. `pythonlib/camoufox/fingerprint-presets-v150.json`.
- **Per-context fingerprint identities**: `new_context()` now mints a fresh real-preset identity (navigator, screen, WebGL, fonts) per context, with **unique per-context seeds for audio, canvas, and font-spacing noise**, plus per-context proxy, geolocation, and WebRTC IP — the values are applied via `addInitScript` that **self-destructs before page scripts can observe it** (`pythonlib/camoufox/async_api.py`, `sync_api.py`).
- **Auto geo/timezone/WebRTC-IP from proxy exit IP**: when a per-context proxy is set, Camoufox derives WebRTC IP and timezone from the proxy's exit IP automatically.
- **`disable_coop`**: disables Cross-Origin-Opener-Policy so elements inside cross-origin iframes (e.g. a Turnstile checkbox) can be clicked.
- **Main-world eval** (`main_world_eval=True` + `"mw:"` script prefix) to run scripts in the page's main world when needed.
- **Human-like cursor is native C++**: `additions/camoucfg/MouseTrajectories.hpp`, ported to C++ from riflosnake/HumanCursor; enabled with `humanize=True` (or a float max-duration in seconds; ~1.5s typical across-window move).
- **Font control**: `fonts=[...]`, `custom_fonts_only=True`.
- **Rich launch flags**: `block_images`, `block_webgl`, `screen`, `window`, `ff_version`, `virtual_display`, `enable_cache`, `exclude_addons`, `addons` (load unpacked Firefox addons with no debug server).
- **Platform support tightened**: the `v152.0.x` line drops 32-bit and macOS x86_64.

---

## Pros and Cons

### Advantages

| Pro | Details |
|-----|---------|
| **C++ level spoofing** | Completely native, undetectable via JS descriptor/prototype/timing checks |
| **Juggler isolation** | No page-visible automation artifacts; not CDP, so no `Runtime.enable` tell |
| **Statistical accuracy** | BrowserForge mimics real traffic; or opt into 312 real fingerprint presets |
| **Per-context identities** | Fresh real-preset identity + seeded noise + proxy/geo per context, applied via self-destructing init script |
| **Comprehensive** | Navigator, Screen, WebGL (+shader precision), Audio, Fonts, Voices, WebRTC, geo/locale |
| **Active development** | Tracks current Firefox (base 152); latest release 2026-07 |
| **Human-like mouse** | Native C++ cursor trajectories (`humanize=True`) |
| **Debloated** | Stripped Mozilla services; README states ~200 MB (less than stock Firefox) |
| **Open source** | Browser MPL-2.0, Python wrapper MIT — patches are all readable in `patches/` |

### Disadvantages

| Con | Details |
|-----|---------|
| **Firefox only** | Cannot impersonate Chrome; Firefox is a small share of real traffic |
| **No TLS impersonation** | Sends genuine Firefox TLS (coherent, but can't be reshaped to Chrome JA3/JA4) |
| **SpiderMonkey detection** | Some WAFs treat Firefox engine more suspiciously |
| **Build complexity** | Building the browser from source needs a Linux toolchain (most users just download the prebuilt binary) |
| **Platform trims** | Latest alpha drops 32-bit and macOS x86_64 |
| **PyPI lag** | Newest launcher code (repo `pythonlib` 0.5.5 dev) may be ahead of the last PyPI publish (0.5.4) |

---

## Installation & Usage

### Quick Start

```bash
pip install -U camoufox[geoip]
# fetch the matching Camoufox browser binary:
python -m camoufox fetch
```

```python
# Sync API
from camoufox.sync_api import Camoufox

with Camoufox() as browser:
    page = browser.new_page()
    page.goto("https://example.com")
```

```python
# Async API
from camoufox.async_api import AsyncCamoufox

async with AsyncCamoufox() as browser:
    page = await browser.new_page()
    await page.goto("https://example.com")
```

### Custom Fingerprint (raw config)

```python
config = {
    "window.innerWidth": 1920,
    "window.innerHeight": 1080,
    "navigator.platform": "Win32",
}

with Camoufox(config=config) as browser:
    page = browser.new_page()
```

### Real Fingerprint Preset

```python
# Use a real in-the-wild fingerprint instead of synthetic BrowserForge output
with Camoufox(fingerprint_preset=True, os="macos") as browser:
    page = browser.new_page()
```

### With Proxy + Auto Geo/Timezone + Humanized Cursor

```python
with Camoufox(
    proxy={"server": "http://user:pass@proxy:8080"},
    geoip=True,        # derive lat/long/timezone/locale from the proxy's exit IP
    humanize=True,     # native C++ human-like cursor movement
    block_webrtc=True, # or leave it on and let webrtc-ip-spoofing use the proxy IP
) as browser:
    page = browser.new_page()
```

### Useful launch options (from `pythonlib/camoufox/utils.py`)

`os`, `block_images`, `block_webrtc`, `block_webgl`, `disable_coop`, `webgl_config`, `geoip` / `geoip_db`, `humanize`, `locale`, `addons` / `exclude_addons`, `fonts` / `custom_fonts_only`, `screen`, `window`, `fingerprint` / `fingerprint_preset`, `ff_version`, `headless`, `main_world_eval`, `enable_cache`, `virtual_display`, `firefox_user_prefs`, `proxy`.

---

## When to Use

### Recommended For

- Firefox-tolerant targets
- High stealth requirements (JS injection fails)
- Fingerprint rotation needs (BrowserForge synthesis or real presets)
- Per-identity isolation at scale (per-context presets + proxy/geo)
- Python projects
- Long-running sessions

### Not Recommended For

- Chrome-only sites (cannot present a Chromium engine or Chrome TLS)
- SpiderMonkey-detecting WAFs
- Workflows that need TLS/JA3 impersonation of a non-Firefox client
- Quick prototyping (heavier setup than a pip-only stealth shim)
- Non-Python projects (use the CLI/server mode via `python -m camoufox server`)

---

## Key Files

| File | Purpose |
|------|---------|
| `additions/camoucfg/MaskConfig.hpp` | Central C++ config reader every patch calls into |
| `patches/fingerprint-injection.patch` | C++ hooks for window/screen/navigator values |
| `patches/playwright/1-leak-fixes.patch` | `webdriver=false`, Playwright leak fixes |
| `patches/playwright/0-playwright.patch` | Juggler/Playwright integration |
| `patches/webgl-spoofing.patch` | WebGL params, extensions, shader precision |
| `patches/webrtc-ip-spoofing.patch` | Protocol-level WebRTC ICE IP (see `webrtc-ip-spoofing.patch`) |
| `patches/network-patches.patch` | HTTP User-Agent + Accept-Language override |
| `patches/audio-context-spoofing.patch`, `patches/audio-fingerprint-manager.patch` | Audio spoofing + seeded noise |
| `patches/shadow-root-bypass.patch` | Closed shadow-root piercing for automation |
| `additions/camoucfg/MouseTrajectories.hpp` | Native C++ human-like cursor movement |
| `additions/juggler/` | Full patched Juggler automation protocol |
| `pythonlib/camoufox/fingerprints.py` | BrowserForge integration + config synthesis |
| `pythonlib/camoufox/fingerprint-presets-v150.json` | 312 real fingerprint presets (v149–v152) |
| `pythonlib/camoufox/async_api.py` / `sync_api.py` | Per-context real-preset identity + self-destructing init scripts |
| `upstream.sh` | Pins the upstream Firefox base version (currently 152.0.4) |

---

## Comparison

| Feature | Camoufox | XDriver | Patchright | puppeteer-stealth |
|---------|:--------:|:-------:|:----------:|:-----------------:|
| Spoofing Level | C++ | CDP | Binary | JavaScript |
| Browser | Firefox | Chromium | Chromium | Chromium |
| Fingerprint Rotation | ✅ Full (+real presets) | ❌ None | Partial | Partial |
| Automation Isolation | ✅ Complete (Juggler) | ✅ Good | ✅ Good | ❌ Partial |
| TLS impersonation | ❌ (real Firefox TLS) | ❌ | ❌ | ❌ |
| Detection Difficulty | Very Hard | Hard | Hard | Medium |

---

## Conclusion

Camoufox is the only tool of the nine that forks Firefox rather than Chromium. Fingerprint values are substituted in C++ getters, so the substitution is not observable through JS property-descriptor or prototype inspection. Verified capabilities at the 2026-08-14 snapshot: Firefox 152.0.4 base, 34 patches in `patches/` plus 2 Playwright/Juggler patches, real-fingerprint presets, per-context seeded-noise identities, proxy-derived geo/WebRTC, and `humanize` cursor configuration.

**Applicability constraint:** the engine is Firefox. Targets that treat Firefox differently from Chrome, or that probe SpiderMonkey engine behaviour (a residual signal the project documents), will identify the browser family regardless of fingerprint configuration.

**Limitation:** It is Firefox — small real-world share, and its genuine (unmodifiable) TLS fingerprint means you cannot masquerade as Chrome at the network layer.

---

*Analysis conducted for educational purposes. Facts verified against the cloned source tree and GitHub/PyPI release metadata as of 2026-08-14. Use responsibly.*
