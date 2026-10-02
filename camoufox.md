# Camoufox - Deep Technical Analysis

> **Tool Type:** Custom Firefox Build (Anti-Detect Browser)
> **Repository:** [github.com/daijro/camoufox](https://github.com/daijro/camoufox)
> **Approach:** C++ level fingerprint injection + Juggler protocol isolation
> **Verified in source (Tier A):** 44 patch files in `patches/` plus 2 in `patches/playwright/` (32 of the 44 diff C/C++ sources; the other 12 diff JS, WebIDL, manifest or build files), including `fingerprint-injection`, `navigator-spoofing`, `screen-spoofing`, `locale-spoofing`, `webrtc-ip-spoofing`, `anti-font-fingerprinting`, `audio-fingerprint-manager`. Input simulation is exposed as the `humanize`, `humanize:minTime`, `humanize:maxTime` config properties (`settings/properties.json:42-44`); the cursor path is generated in Juggler JavaScript from a vendored copy of Cursory (`additions/juggler/input/CursorTrajectory.js`), no longer in C++. `Runtime.enable` is not applicable: automation runs over Juggler, not CDP.
> **Anti-bot service claims:** **none** — the project makes no claims about Cloudflare, DataDome, Kasada or similar (its README carries only a generic "invisible to anti-bot systems" line, `README.md:342`), and its README instead **documents limitations**: some WAFs probe SpiderMonkey engine behaviour, which a Firefox fork cannot disguise (`README.md:499`), and inconsistencies in a rotated fingerprint are still found and tested for by anti-bot providers (`README.md:545`) (**Tier D** for coverage; the limitations are **Tier B**)
> **Maintenance:** Actively developed — browser `v156.0.1-beta.33` (2026-09-30, pre-release; latest non-pre-release `v152.0.4-beta.30`, 2026-09-01); Python wrapper `camoufox` **0.5.6** on PyPI (2026-09-06; repo `pythonlib` at 0.5.7 dev). 12.2k stars, 44 contributors, last push 2026-09-30. MPL-2.0.
> **Verified:** 2026-09-30 against `daijro/camoufox` @ `2f30fea`.

---

## Table of Contents

- [What is Camoufox?](#what-is-camoufox)
- [Version & Status (2026-09)](#version--status-2026-09)
- [How It Works](#how-it-works)
- [Properties of C++-Level Spoofing](#properties-of-c-level-spoofing)
- [Fingerprint Capabilities](#fingerprint-capabilities)
- [What Changed Since the 2026-08-14 Analysis](#what-changed-since-the-2026-08-14-analysis)
- [Pros and Cons](#pros-and-cons)
- [Installation & Usage](#installation--usage)
- [When to Use](#when-to-use)
- [Key Files](#key-files)

---

## What is Camoufox?

Camoufox is a **custom-built Firefox browser** designed specifically for web scraping and automation stealth. Unlike tools that patch or inject into existing browsers, Camoufox compiles Firefox from source with modifications at the C++ implementation level.

**Mechanism:** fingerprint values are substituted inside Firefox's C++ getters, before any value reaches JavaScript. Consequently the substitution is not observable through the techniques that detect JS-level patching — property-descriptor inspection, prototype-chain checks, or `Function.prototype.toString` comparison — because no JS-level wrapper exists. This constrains one detection method; it does not make the browser undetectable, and the project's own README documents a residual signal (SpiderMonkey engine behaviour identifies the browser as Firefox-based).

The project is authored by **daijro** (also the author of [BrowserForge](https://github.com/daijro/browserforge)). As of 2026-09-30 it has ~12.2k GitHub stars and 44 contributors. The C++ browser fork tracks upstream Firefox — the current base is **Firefox 156.0.1** (`upstream.sh`). A thin Python library (`camoufox`) wraps Playwright's Firefox driver to launch the binary and feed it a fingerprint config; the repository also carries a TypeScript/JavaScript launcher (`typescript/`).

---

## Version & Status (2026-09)

| Item | Value | Evidence |
|------|-------|----------|
| Latest release | `v156.0.1-beta.33`, 2026-09-30 (pre-release) | GitHub Releases API |
| Latest non-pre-release | `v152.0.4-beta.30`, 2026-09-01 | GitHub Releases API |
| Upstream Firefox base | **156.0.1** | `upstream.sh` → `version=156.0.1` (`release=beta.32`; a browser release's number is taken from its tag at build time) |
| Python package (PyPI) | **0.5.6** (2026-09-06) | `pip index` / PyPI (latest as listed in `STATUS.md`; pre-release versions not checked) |
| Python package (repo dev) | **0.5.7** | `pythonlib/pyproject.toml:7` → `version = "0.5.7"` |
| TypeScript package (repo) | `@camoufox/camoufox` **0.5.7** | `typescript/package.json`; npm publication not checked |
| Browser license | **MPL-2.0** (Firefox fork) | root `LICENSE` |
| Python wrapper license | **MIT** | `pythonlib/pyproject.toml:10` → `license = "MIT"` |
| Vendored cursor-path generator | **LGPLv3-or-later** (Cursory) | `additions/juggler/input/cursory/NOTICE`; `README.md:806` |
| Primary language | **C++** patches over Firefox, Juggler in JavaScript, launchers in Python and TypeScript | tree layout (`patches/`, `additions/`, `pythonlib/`, `typescript/`) |
| Last commit | 2026-09-30 (`2f30fea`) | `git log` |
| Camoufox source patches | **44** stealth/parity/debloat patches + **2** Playwright/Juggler patches (plus 14 vendored LibreWolf/Ghostery patches) | `patches/*.patch` (44), `patches/playwright/*.patch` (2), `patches/librewolf/`, `patches/ghostery/` |

> Note the licence split: the browser is a Firefox fork and is therefore **MPL-2.0**, while the `camoufox` Python launcher library and the TypeScript launcher are **MIT**; the Cursory cursor-path code vendored inside Juggler is **LGPLv3-or-later**, not MPL-2.0 (`README.md:806-807`). Earlier analyses that called the whole project "MIT" or "MPL" were only half right.

> Build matrix (`.github/workflows/release.yml:140-152`): Linux, Windows and macOS for x86_64, arm64 and i686, minus Windows arm64 (commented "Fails (.mozbuild does not include clang++-cl)"), macOS i686 and Linux i686. `README.md:654` states that `i686` builds are supported only for Windows; the launcher's platform table (`pythonlib/camoufox/pkgman.py:66-70`) lists Windows x86_64/i686, macOS x86_64/arm64 and Linux x86_64/arm64/i686. Which archives are published for each release was not checked (**Tier D**).

> Release flow (`.github/workflows/release.yml`, `ci/README.md`): every tested merge to `main` publishes a GitHub pre-release (the browser is rebuilt only when its sources changed) and matching library pre-releases (`bN` on PyPI, `-beta.N` on npm); a `vX.Y.Z` tag promotes them. A published library carries `pythonlib/camoufox/browser-pin.json` naming the browser build it was tested with (`{}` in the repository). `camoufox fetch` checks the downloaded browser archive against the sha256 digest GitHub publishes for the asset (`pythonlib/camoufox/pkgman.py:940-962`).

---

## How It Works

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    CAMOUFOX ARCHITECTURE                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────────┐    ┌─────────────────┐                     │
│  │  Python Library │───▶│  fpgen          │                     │
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
│  │      CUSTOM FIREFOX 156 BUILD            │                    │
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

The config is read by a single C++ helper, `additions/camoucfg/MaskConfig.hpp`, which every patch calls into. It parses the JSON that the launcher passes in the `CAMOU_CONFIG` environment variable (split across `CAMOU_CONFIG_1..N` when long). Patches ask it for a value (`MaskConfig::GetDouble("window.innerWidth")`, `MaskConfig::GetString("headers.User-Agent")`, etc.); if the user or the fingerprint draw set one, the spoofed value is returned, otherwise the code falls through to the real Firefox implementation. Per-context values (one identity per Playwright context) bypass `CAMOU_CONFIG`: they are set through `window.setXxx()` helpers and stored per `userContextId` by `RoverfoxStorageManager` (`patches/anti-font-fingerprinting.patch`, `docs/per-context-patches.md`).

### C++ Level Fingerprint Injection

The core innovation is modifying Firefox's C++ source code to intercept property getters. From `patches/fingerprint-injection.patch` (current source):

```cpp
// dom/base/nsGlobalWindowInner.cpp
double nsGlobalWindowInner::GetInnerWidth(CallerType aCallerType,
                                          ErrorResult& aError) {
  if (auto value = MaskConfig::GetDouble("window.innerWidth"))
    return value.value();
  FORWARD_TO_OUTER_OR_THROW(GetInnerWidthOuter, (aCallerType, aError), aError,
                            0);
}

int32_t nsGlobalWindowInner::GetScreenX(CallerType aCallerType,
                                        ErrorResult& aError) {
  if (auto value = MaskConfig::GetInt32("window.screenX")) return value.value();
  FORWARD_TO_OUTER_OR_THROW(GetScreenXOuter, (aCallerType, aError), aError, 0);
}
```

The same patch also hooks `GetInnerHeight`, `GetScreenY`, `GetDevicePixelRatio`, `nsScreen::PixelDepth` and `GetAvailRect`, and the worker-side `WorkerNavigator` getters (platform, appVersion, userAgent, hardwareConcurrency, GPC) — all through `MaskConfig::Get*`. `window.outerWidth`/`outerHeight` are deliberately **not** read from the config: a comment in the patch records that `browser-init.patch` resizes the real window to the drawn size instead, because a fixed outer size contradicted the real inner size (measured `innerWidth` 1853 > `outerWidth` 1680 on GNOME).

**What this changes:**
- The getter returns the configured value directly from C++
- There is no JavaScript wrapper or proxy on the property, so `Object.getOwnPropertyDescriptor()` shows a native accessor and `toString()` returns `[native code]`
- Per-context values are served from a cache: a comment in `patches/anti-font-fingerprinting.patch` records that an uncached synchronous IPC read per unset key had made `navigator.hardwareConcurrency` and `screen.*` reads about 20x slower than stock, a timing a page can measure

### HTTP Header Spoofing (network layer, not TLS)

`patches/network-patches.patch` hooks `netwerk/protocol/http/nsHttpHandler.cpp` to override the `User-Agent`, `Accept-Language` and `Accept-Encoding` request headers from the config (the User-Agent falls back to `navigator.userAgent` when `headers.User-Agent` is unset):

```cpp
// netwerk/protocol/http/nsHttpHandler.cpp
if (auto value = MaskConfig::GetString("headers.User-Agent")) { /* use spoofed UA */ }
if (auto value = MaskConfig::GetString("navigator.userAgent")) { /* ...or the navigator UA */ }
...
if (auto value = MaskConfig::GetString("headers.Accept-Language")) { /* use spoofed AL */ }
if (auto value = MaskConfig::GetString("headers.Accept-Encoding")) { /* use spoofed AE */ }
```

> **Important limitation:** this is HTTP-header spoofing, **not TLS/JA3/JA4 fingerprint impersonation.** Camoufox sends a real Firefox TLS ClientHello (because it *is* Firefox), which is coherent for a Firefox persona but cannot be changed to look like Chrome. There is no ja3/ja4 rewriting in the source (no `ja3`, `ja4`, `ClientHello` or TLS-fingerprint reference in `patches/`, `additions/`, `settings/`, `pythonlib/`, `typescript/src`, `docs/` or `scripts/`).

### Juggler Protocol Isolation

Camoufox uses **Juggler** (Firefox's automation protocol used by Playwright) instead of CDP. The full Juggler implementation lives under `additions/juggler/` and is patched to run in an isolated scope (as described in the project README, **Tier B**; the isolated and main worlds are implemented in `additions/juggler/content/FrameTree.js` and `Runtime.js`):

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

From `patches/playwright/1-leak-fixes.patch` — the webdriver property fix at C++ level. The pre-image of `Navigator::Webdriver()` (Firefox with Playwright's patch applied) checks Marionette and RemoteAgent and otherwise returns `true` under a "Playwright is automating the browser" comment; Camoufox deletes those checks and returns a flat `false`:

```cpp
// dom/base/Navigator.cpp
/* static */
bool Navigator::Webdriver() {
  return false;
}
```

The patch's only other change is in `EnterprisePoliciesParent.sys.mjs`, where Playwright's `new PlaywrightPoliciesProvider()` is replaced by Firefox's own `this._buildProvider()`. A separate opt-in, `main_world_eval=True` (config key `allowMainWorld`), lets you run a script in the page's main world by prefixing it with `mw:` (e.g. `page.evaluate("mw:" + script)`) — otherwise Playwright scripts stay in the isolated world (`additions/juggler/content/Runtime.js` refuses an `mw:` call unless the flag is set). Two further patches touch what content can observe: `debugger-invisible-to-content.patch` adds a Debugger flag so that attaching a Debugger does not cause content-visible side effects (extra stack capture, a disabled Promise return-value optimisation, wasm deoptimisation), and `window-setter-seal.patch` keeps the per-context `window.setXxx()` helpers off `window` once init scripts have run.

### fpgen Integration (default fingerprint synthesis)

When you don't supply values, the launcher fills them with **fpgen** ([scrapfly/fingerprint-generator](https://github.com/scrapfly/fingerprint-generator)), which the project README describes as a Bayesian network trained on live traffic (`README.md:539`, **Tier B** for the distribution claim), and then runs the draw through a coherence check:

```python
# pythonlib/camoufox/fingerprints.py
_FP_GENERATOR = load_fpgen().Generator()   # built on first use (_generator(), line 29)
fingerprint = _generator().generate(browser='Firefox', **conditions, **screen_conditions)   # generate_fingerprint(), line 1898
```

- The launcher drew from **BrowserForge** (`browserforge = "^1.2.4"`) until repo commit `6daae88` (2026-09-24); `pythonlib/pyproject.toml:35` now declares `fpgen = "^1.3.0"`. The latest PyPI release is 0.5.6; `pyproject.toml` at the commit that set that version (`eb5dc3b`) still declares `browserforge`, so the published package appears to predate the fpgen change.
- fpgen's model is installed from a release pinned by sha256 (`pythonlib/camoufox/fpgen-model.json`, `fpgen_model.py`) by `camoufox fetch` or on the first draw, in place of fpgen's own unpinned download.
- `pythonlib/camoufox/coherence.py` (`validate()` / `apply()`) holds whole-identity rules — Apple-Silicon core counts, GPU vs OS, Intel-Mac GPU vs core count and screen, `colorDepth` in {24, 30}, `maxTouchPoints`, per-OS `devicePixelRatio` steps, window chrome, avail bounds, UA/platform architecture — and is applied to generated fingerprints, bundled presets and hand-written configs.
- fpgen supplies navigator, screen, window and headers; the GPU comes from fpgen's WebGL records, and fonts, speech voices and media devices are drawn from catalogues in the package (`fonts.json`, `voice-manifests.json`, `media-devices.json`) (`coherence.py` module docstring; `ROADMAP.md`, "Identity").

### Real Fingerprint Presets (opt-in)

For evasion against consistency checks that generated identities can trip, Camoufox also ships bundles of **real** fingerprints scraped from in-the-wild Firefox traffic. `pythonlib/camoufox/fingerprint-presets-v150.json` holds **285 presets** — 168 Windows / 58 macOS / 59 Linux — with Firefox v149–v152 user agents (`min_firefox_version: 149`, `source: roverfox_fingerprints`); `fingerprint-presets.json` is an older bundle of 113 presets (71 / 25 / 17, Firefox 119–148 user agents). `_select_presets_file()` (`fingerprints.py:1272-1285`) picks the v150 bundle for binaries at Firefox 149 or later, and `from_preset()` rewrites the UA's Firefox version to the active binary's (`fingerprints.py:1386-1389`). Opt in with `fingerprint_preset=True`; pass a preset dict instead of `True` to pin a specific identity. `ROADMAP.md` notes that presets naming GPUs with no recorded WebGL parameters (Windows on ARM/Adreno, Direct3D 10-level hardware, some Mesa and older Intel Linux drivers) were dropped.

---

## Properties of C++-Level Spoofing

### vs. JavaScript Injection (puppeteer-extra-stealth, etc.)

| Detection Method | JS Injection | Camoufox |
|-----------------|--------------|----------|
| `Object.getOwnPropertyDescriptor` check | ❌ Detectable | ✅ Native |
| `Function.toString()` returns `[native code]` | ❌ Often fails | ✅ Native (no JS wrapper) |
| Worker vs main context mismatch | ❌ Detectable | ✅ Worker getters are hooked as well (`WorkerNavigator.cpp`); main/worker mismatches have occurred as bugs and were fixed (e.g. GPC, #760) |
| Property access timing analysis | ❌ Delay | ✅ No JS wrapper call; per-context reads are cached (see above) |

### vs. CDP-based Solutions (Playwright/Chrome, Puppeteer)

| Detection Method | CDP-based | Camoufox |
|-----------------|-----------|----------|
| `navigator.webdriver` | Patchable but leaky | ✅ C++ level false |
| `window.__playwright__` | ❌ Present | ✅ Isolated Juggler scope |
| `Runtime.enable` detection | ❌ Detectable | ✅ Uses Juggler, not CDP |

---

## Fingerprint Capabilities

Coverage is broad and applied natively. The patches map onto these areas (non-exhaustive; 44 top-level patch files):

| Category | Properties Spoofed | Patch(es) |
|----------|-------------------|-----------|
| **Navigator** | userAgent, platform, hardwareConcurrency, oscpu, appVersion, language, globalPrivacyControl (window and workers), maxTouchPoints; `doNotTrack` is set as a pref by the launcher | `navigator-spoofing.patch`, `fingerprint-injection.patch`, `touchscreen-fingerprint-spoofing.patch`, `locale-spoofing.patch` |
| **Screen** | width, height, availLeft/Top/Width/Height, colorDepth, pixelDepth (the CSS `color` media feature follows `colorDepth`) | `screen-spoofing.patch`, `fingerprint-injection.patch` |
| **Window** | innerWidth/Height, screenX/Y, devicePixelRatio (`outerWidth`/`outerHeight` are not read from the config; the real window is resized) | `fingerprint-injection.patch`, `browser-init.patch` |
| **WebGL** | UNMASKED_VENDOR/RENDERER, parameter table, supported extensions, shader precision formats; `getContextAttributes()` and live state (e.g. `lineWidth`, viewport) come from the real context | `webgl-spoofing.patch` |
| **Audio** | sampleRate, output latency, channel counts + seeded per-context noise | `audio-context-spoofing.patch`, `audio-fingerprint-manager.patch` |
| **Fonts** | per-context installed-font list, system-UI and CSS2 system fonts following the claimed OS, per-context font-group plumbing; no glyph-spacing or metrics noise | `font-list-spoofing.patch`, `font-hijacker.patch`, `system-ui-font-spoofing.patch`, `font-system-fonts-css2.patch`, `anti-font-fingerprinting.patch` |
| **Canvas** | not perturbed: output is left as the GPU and fonts render it (`ci/tribal-rules.yml:203`, rule `canvas-is-not-noised`; no `canvas:seed`) | — |
| **Speech/Voices** | speechSynthesis voices (`speak()` on a spoofed voice starts and ends after the text's duration) | `speech-voices-spoofing.patch`, `voice-spoofing.patch` |
| **Media** | enumerateDevices output with labels and group ids (a fake media engine, so a claimed device captures), codec-support probes (`media:spoof_codecs`) | `media-device-spoofing.patch`, `media-codec-spoofing.patch` |
| **Network** | WebRTC ICE IP (protocol level), HTTP User-Agent + Accept-Language + Accept-Encoding | `webrtc-ip-spoofing.patch`, `network-patches.patch` |
| **Geo/Locale** | geolocation, timezone (per realm), locale (Intl; the OS/default locale only), browser UI strings through packaged language packs | `geolocation-spoofing.patch`, `timezone-spoofing.patch`, `locale-spoofing.patch` |
| **DOM/behavior** | closed shadow-root piercing for automation, forced default pointer (any-pointer gains coarse only when `maxTouchPoints` > 0), optional instant CSS animations (`instantAnimations`, off by default), option-targeted events on `<select>` commits | `shadow-root-bypass.patch`, `force-default-pointer.patch`, `no-css-animations.patch`, `trusted-automation-events.patch` |

WebRTC spoofing is a real protocol-level implementation (`WebRTCIPManager` plus hooks in `PeerConnectionImpl.cpp` for SDP, ICE candidates and `getStats()`, keyed per user context), not just a JS toggle — though you can also fully disable WebRTC with `block_webrtc=True`.

---

## What Changed Since the 2026-08-14 Analysis

88 commits separate the previous pin (`7add1ef`, 2026-08-12) from `2f30fea` (2026-09-30). The core architecture (C++ getters through `MaskConfig`, Juggler isolation) is unchanged; these items changed:

- **Firefox base 152.0.4 → 156.0.1** (`ec37d72`, `upstream.sh`). Releases are now `v156.0.1-beta.32` (2026-09-28) and `v156.0.1-beta.33` (2026-09-30), both pre-releases; the latest non-pre-release is still on the 152 line (`v152.0.4-beta.30`).
- **fpgen replaces BrowserForge** as the fingerprint generator, with a whole-identity coherence check (`coherence.py`) — in the repository since `6daae88` (2026-09-24); PyPI 0.5.6 predates it.
- **Cursor path: C++ → recorded movements.** `additions/camoucfg/MouseTrajectories.hpp` (a Bézier-curve generator) was removed. `humanize=True` now picks one of 2,357 recorded human movements (Cursory, vendored as cursory-js, LGPLv3-or-later), morphs it onto the requested endpoints and replays it with its own timing, in Juggler JavaScript (`additions/juggler/input/CursorTrajectory.js`, `cursory/trajectories.json`). `humanize:maxTime` defaults to 1.5 s.
- **Noise features removed.** The glyph-spacing perturbation (`fonts:spacing_seed`, `FontSpacingSeedManager`) and the launcher's unused `canvas:seed` are gone, and there is no canvas noise (`ci/tribal-rules.yml:188-218`). `settings/properties.json` declares 82 properties (107 at the previous pin); battery, scroll-offset, `history.length` and several `navigator.*` keys were dropped.
- **Per-context identities.** `NewContext()` / `AsyncNewContext()` draw an fpgen identity by default (a preset only when passed) and set an audio seed — no canvas or font-spacing seed (`async_api.py:188-243`, `fingerprints.py:1586-1782`). The `window.setXxx()` helpers (14 in the source) are now **sealed**: a window starts sealed, Juggler opens it only while init scripts run, then seals it again (`window-setter-seal.patch`, commit `7911f4a`, 2026-08-31). Under the earlier self-destruct scheme a helper stayed on `window` whenever its value was not set, so page script could see and call it (commit message).
- **Stock-Firefox parity pass** (`6daae88`, #779). From its commit message: synthesized input carries `pointerType` "mouse" and Shift key events; `evaluate()` no longer grants user activation; Playwright contexts are non-public identities (no automation label in the URL bar); web fonts and `local()` work again; CSS2 system fonts and `system-ui` follow the claimed OS; browser UI strings are localized through packaged language packs; media devices enumerate and capture coherently; the timezone applies from the first read; WebGL live state passes through to the real context; ICE gathering completes behind a proxy; `camoufox.exe` embeds an application manifest.
- **New patches** (top-level, absent at the previous pin): `debugger-invisible-to-content`, `trusted-automation-events`, `touchscreen-fingerprint-spoofing`, `media-codec-spoofing`, `wheel-native-ticks`, `popup-blocker-parity`, `contentaccessible-parity`, `window-setter-seal`, `windows-exe-manifest`, `rust-vendor-unknown-fallback`.
- **TypeScript/JavaScript launcher** (`typescript/`, `@camoufox/camoufox` 0.5.7; Node 22.15 or newer, `playwright-core` below 1.63): a port of the Python launcher that reads the same `properties.json`, presets and font/voice data and ports fpgen; npm publication was not verified.
- **Launcher and packaging.** Playwright ceiling raised from `<1.61` to `<1.63`, with a Playwright-keyed browser floor (`pythonlib/camoufox/__version__.py`); `pin_cpu_cores` (off by default) pins the browser to `navigator.hardwareConcurrency` cores on Linux/Windows; `lxml` and `geoip2` dependencies removed (`maxminddb` for the `geoip` extra). Bundled fonts are a pinned release asset (`font-bundle-v1`, 843 MB archive, 2.16 GB extracted per `docs/FONTS.md`) with per-OS fontconfig files; `fonts.json` lists 335 Windows, 567 macOS and 358 Linux font names.

Carried over from the 2026-08 analysis and re-verified at `2f30fea`:

- **Auto timezone and WebRTC IP from a per-context proxy's exit IP** (`async_api.py:188-243`; the lookup is an HTTP request to `ip-api.com` made through the proxy, `ip.py:78-97`); launch-level `geoip=True` derives location, timezone and locale.
- **`disable_coop`**, **`main_world_eval` with the `mw:` prefix**, **`fonts` / `custom_fonts_only`**, and the launch flags `block_images`, `block_webgl`, `screen`, `window`, `ff_version`, `virtual_display`, `enable_cache`, `exclude_addons`, `addons` (load unpacked Firefox addons with no debug server).

---

## Pros and Cons

### Advantages

| Pro | Details |
|-----|---------|
| **C++ level spoofing** | Values are substituted in native getters; no JS-level wrapper exists to inspect through descriptor, prototype or `toString()` checks |
| **Juggler isolation** | Page agent runs in an isolated scope (README, Tier B); not CDP, so no `Runtime.enable` tell |
| **Distribution-based draws** | fpgen model plus `coherence.py` rules (README, Tier B for the model's accuracy); or opt into 285 real fingerprint presets |
| **Per-context identities** | `NewContext()` gives each context a fresh fpgen-drawn (or preset) identity with its own audio seed, plus per-context proxy, geolocation and WebRTC IP; setters sealed before page script runs |
| **Coverage** | Navigator, Screen, WebGL, Audio, Fonts, Voices, Media devices, WebRTC, geo/locale (canvas is not perturbed) |
| **Active development** | Tracks current Firefox (base 156.0.1); latest release 2026-09-30 |
| **Recorded-movement cursor** | `humanize=True` replays recorded human mouse movements (Cursory) |
| **Debloated** | Stripped Mozilla services; README states ~200 MB (less than stock Firefox) |
| **Open source** | Browser MPL-2.0, Python and TypeScript launchers MIT, vendored Cursory LGPLv3-or-later — patches are all readable in `patches/` |

### Disadvantages

| Con | Details |
|-----|---------|
| **Firefox only** | Cannot impersonate Chrome; Firefox is a small share of real traffic |
| **No TLS impersonation** | Sends genuine Firefox TLS (coherent, but can't be reshaped to Chrome JA3/JA4) |
| **SpiderMonkey detection** | Some WAFs treat Firefox engine more suspiciously |
| **Build complexity** | Building the browser from source needs a Linux host (Windows and macOS are cross-compiled); `AGENTS.md` quotes about 40 minutes for a cold build, and the font bundle is a separate 843 MB download (most users fetch the prebuilt binary) |
| **No Windows ARM64 build** | `release.yml` excludes Windows arm64 (commented "Fails (.mozbuild does not include clang++-cl)") |
| **PyPI lag** | Repo `pythonlib` is 0.5.7 (fpgen-based); the latest PyPI release is 0.5.6 (BrowserForge-based) |
| **Host-OS rendering** | The project docs state that the per-context patches change what JS APIs report, not how the OS renders (font rasterisation, scrollbars, canvas device class) (`docs/per-context-patches.md`, "Known Limitations", Tier B) |

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

### TypeScript / JavaScript

```javascript
import { Camoufox } from "@camoufox/camoufox";

const browser = await Camoufox({ headless: true });
const page = await browser.newPage();
await page.goto("https://example.com");
await browser.close();
```

(`typescript/README.md`; npm publication not verified.)

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
# Use a real in-the-wild fingerprint instead of synthetic fpgen output
with Camoufox(fingerprint_preset=True, os="macos") as browser:
    page = browser.new_page()
```

### With Proxy + Auto Geo/Timezone + Humanized Cursor

```python
with Camoufox(
    proxy={"server": "http://user:pass@proxy:8080"},
    geoip=True,        # derive lat/long/timezone/locale from the proxy's exit IP
    humanize=True,     # human-like cursor movement (replays recorded movements)
    block_webrtc=True, # or leave it on and let webrtc-ip-spoofing use the proxy IP
) as browser:
    page = browser.new_page()
```

### Useful launch options (from `pythonlib/camoufox/utils.py`)

`os`, `block_images`, `block_webrtc`, `block_webgl`, `disable_coop`, `webgl_config`, `geoip` / `geoip_db`, `humanize`, `locale`, `addons` / `exclude_addons` / `allow_addon_new_tab`, `fonts` / `custom_fonts_only`, `screen`, `window`, `fingerprint` / `fingerprint_preset`, `ff_version`, `headless`, `main_world_eval`, `enable_cache`, `virtual_display`, `pin_cpu_cores`, `executable_path` / `browser`, `firefox_user_prefs`, `proxy`.

---

## When to Use

### Recommended For

- Firefox-tolerant targets
- High stealth requirements (JS injection fails)
- Fingerprint rotation needs (fpgen draws or real presets)
- Per-identity isolation at scale (per-context identities + proxy/geo)
- Python and TypeScript/JavaScript projects
- Long-running sessions

### Not Recommended For

- Chrome-only sites (cannot present a Chromium engine or Chrome TLS)
- SpiderMonkey-detecting WAFs
- Workflows that need TLS/JA3 impersonation of a non-Firefox client
- Quick prototyping (heavier setup than a pip-only stealth shim)
- Languages other than Python and TypeScript/JavaScript (use the server mode via `python -m camoufox server`)

---

## Key Files

| File | Purpose |
|------|---------|
| `additions/camoucfg/MaskConfig.hpp` | Central C++ config reader every patch calls into |
| `patches/fingerprint-injection.patch` | C++ hooks for window/screen values and the worker-side navigator getters |
| `patches/playwright/1-leak-fixes.patch` | `webdriver=false`; reverts Playwright's policies provider |
| `patches/playwright/0-playwright.patch` | Juggler/Playwright integration |
| `patches/webgl-spoofing.patch` | WebGL params, extensions, shader precision, UNMASKED_* |
| `patches/webrtc-ip-spoofing.patch` | WebRTC IP replacement in SDP, ICE candidates and `getStats()`, per user context |
| `patches/network-patches.patch` | HTTP User-Agent, Accept-Language and Accept-Encoding override |
| `patches/audio-context-spoofing.patch`, `patches/audio-fingerprint-manager.patch` | Audio spoofing + seeded noise |
| `patches/shadow-root-bypass.patch` | Closed shadow-root piercing for automation |
| `patches/window-setter-seal.patch` | Seals the per-context `window.setXxx()` helpers once init scripts have run |
| `additions/juggler/input/CursorTrajectory.js`, `additions/juggler/input/cursory/` | Humanized cursor path: replays recorded human movements (vendored cursory-js, LGPLv3-or-later) |
| `additions/juggler/` | Full patched Juggler automation protocol |
| `pythonlib/camoufox/fingerprints.py` | fpgen integration, preset routing, per-context init script |
| `pythonlib/camoufox/coherence.py` | Whole-identity coherence rules |
| `pythonlib/camoufox/fingerprint-presets-v150.json` | 285 real fingerprint presets (v149–v152); `fingerprint-presets.json` holds 113 older ones |
| `pythonlib/camoufox/async_api.py` / `sync_api.py` | Per-context identity (`NewContext`) and init-script helpers |
| `settings/properties.json` | Every declared config key and its type (82) |
| `ci/tribal-rules.yml` | Settled design decisions with their evidence (e.g. no canvas noise, no glyph-spacing noise) |
| `typescript/` | TypeScript/JavaScript launcher |
| `upstream.sh` | Pins the upstream Firefox base version (currently 156.0.1) |

---

## Comparison

| Feature | Camoufox | XDriver | Patchright | puppeteer-stealth |
|---------|:--------:|:-------:|:----------:|:-----------------:|
| Spoofing Level | C++ | CDP | Driver source patch (TypeScript) | JavaScript |
| Browser | Firefox | Chromium | Chromium | Chromium |
| Fingerprint Rotation | ✅ fpgen draws (+ real presets) | ❌ None | ❌ None in driver source | Partial |
| Automation Isolation | ✅ Isolated Juggler scope (opt-in `mw:`) | ✅ `Runtime.enable` patch in bundle, env-var gated | ✅ `Runtime.enable` sends removed in driver patch | ❌ Partial |
| TLS impersonation | ❌ (real Firefox TLS) | ❌ | ❌ | ❌ |

---

## Conclusion

Camoufox is one of two tools of the ten that fork Firefox rather than Chromium (the other is invisible_playwright). Fingerprint values are substituted in C++ getters, so the substitution is not observable through JS property-descriptor or prototype inspection. Verified capabilities at the 2026-09-30 snapshot: Firefox 156.0.1 base, 44 patches in `patches/` plus 2 Playwright/Juggler patches, fpgen-drawn identities with a coherence check (repository HEAD; PyPI 0.5.6 predates it), real-fingerprint presets, per-context identities with an audio seed, proxy-derived timezone and WebRTC IP, and `humanize` cursor replay of recorded movements. Canvas output is not perturbed.

**Applicability constraint:** the engine is Firefox. Targets that treat Firefox differently from Chrome, or that probe SpiderMonkey engine behaviour (a residual signal the project documents), will identify the browser family regardless of fingerprint configuration.

**Limitation:** It is Firefox — small real-world share, and its genuine (unmodifiable) TLS fingerprint means you cannot masquerade as Chrome at the network layer.

---

*Analysis conducted for educational purposes. Facts verified against the cloned source tree and GitHub/PyPI release metadata as of 2026-09-30. Use responsibly.*
