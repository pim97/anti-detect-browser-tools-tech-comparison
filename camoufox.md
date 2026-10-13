# Camoufox - Deep Technical Analysis

> **Tool Type:** Custom Firefox Build (Anti-Detect Browser)
> **Repository:** [github.com/daijro/camoufox](https://github.com/daijro/camoufox)
> **Approach:** C++ level fingerprint injection + Juggler protocol isolation
> **Verified in source (Tier A):** 42 patch files in `browser/patches/` plus 2 in `browser/patches/playwright/` (31 of the 42 diff C/C++ sources; the other 11 diff JS, WebIDL, manifest or build files), including `fingerprint-injection`, `navigator-spoofing`, `screen-spoofing`, `locale-spoofing`, `webrtc-ip-spoofing`, `anti-font-fingerprinting`, `audio-fingerprint-manager`. Input simulation is exposed as the `humanize`, `humanize:minTime`, `humanize:maxTime` config properties (`browser/settings/properties.json:41-43`); the cursor path is generated in Juggler JavaScript from a vendored copy of Cursory (`browser/additions/juggler/input/CursorTrajectory.js`), no longer in C++. `Runtime.enable` is not applicable: automation runs over Juggler, not CDP.
> **Anti-bot service claims:** **none** — the project makes no claims about Cloudflare, DataDome, Kasada or similar (the generic "invisible to anti-bot systems" line was dropped in the 2026-10 README rewrite), and its README instead **documents limitations**: some WAFs test SpiderMonkey engine behaviour, which no spoofing turns into Chromium (`README.md:545-546`), and "Camoufox can still be detected" because anti-bot vendors look for the one value that does not agree with the rest (`README.md:565-568`) (**Tier D** for coverage; the limitations are **Tier B**)
> **Maintenance:** Actively developed — browser `v156.0.1-beta.38` (2026-10-13, pre-release; latest non-pre-release was `v152.0.4-beta.30`, 2026-09-01, when last checked on 2026-09-30); Python wrapper `camoufox` **0.5.8** on PyPI (2026-10-06; library pre-release tags up to `v0.5.9b3`); the npm package is now named `camoufox` (was `@camoufox/camoufox`). 12.5k stars, 45 contributors, last push 2026-10-13. MPL-2.0.
> **Verified:** 2026-10-13 against `daijro/camoufox` @ `4559d01` (previous pass: `2f30fea`, 2026-09-30).

---

## Table of Contents

- [What is Camoufox?](#what-is-camoufox)
- [Version & Status (2026-10)](#version--status-2026-10)
- [How It Works](#how-it-works)
- [Properties of C++-Level Spoofing](#properties-of-c-level-spoofing)
- [Fingerprint Capabilities](#fingerprint-capabilities)
- [What Changed Since the 2026-09-30 Analysis](#what-changed-since-the-2026-09-30-analysis)
- [What Changed Since the 2026-08-14 Analysis](#what-changed-since-the-2026-08-14-analysis)
- [Pros and Cons](#pros-and-cons)
- [Installation & Usage](#installation--usage)
- [When to Use](#when-to-use)
- [Key Files](#key-files)

---

## What is Camoufox?

Camoufox is a **custom-built Firefox browser** designed specifically for web scraping and automation stealth. Unlike tools that patch or inject into existing browsers, Camoufox compiles Firefox from source with modifications at the C++ implementation level.

**Mechanism:** fingerprint values are substituted inside Firefox's C++ getters, before any value reaches JavaScript. Consequently the substitution is not observable through the techniques that detect JS-level patching — property-descriptor inspection, prototype-chain checks, or `Function.prototype.toString` comparison — because no JS-level wrapper exists. This constrains one detection method; it does not make the browser undetectable, and the project's own README documents a residual signal (SpiderMonkey engine behaviour identifies the browser as Firefox-based).

The project is authored by **daijro** (also the author of [BrowserForge](https://github.com/daijro/browserforge)). As of 2026-10-13 it has ~12.5k GitHub stars and 45 contributors. The C++ browser fork tracks upstream Firefox — the current base is **Firefox 156.0.1** (`browser/upstream.sh`). A thin Python library (`camoufox`) wraps Playwright's Firefox driver to launch the binary and feed it a fingerprint config; the repository also carries a TypeScript/JavaScript launcher (`typescript/`). Since `cbca509` (2026-10-10) the repository is split into `browser/` (patches, additions, settings, build), `python/` (formerly `pythonlib/`) and `typescript/`.

---

## Version & Status (2026-10)

| Item | Value | Evidence |
|------|-------|----------|
| Latest release | `v156.0.1-beta.38`, 2026-10-13 (pre-release) | GitHub Releases API (`STATUS.md`); tag at `83ebe0d` |
| Latest non-pre-release | `v152.0.4-beta.30`, 2026-09-01 | GitHub Releases API as of 2026-09-30; not re-checked on 2026-10-13 |
| Upstream Firefox base | **156.0.1** | `browser/upstream.sh` → `version=156.0.1` (`release=beta.32`; a browser release's number is taken from its tag at build time) |
| Python package (PyPI) | **0.5.8** (2026-10-06) | PyPI (latest as listed in `STATUS.md`; pre-release versions not checked); tag `v0.5.8` is `ac2ce31` |
| Python package (repo) | **0.5.7** in tree; published versions are stamped from the release tag (`ci/release.py:27`, `:62`); library tags since the previous pass: `v0.5.7`, `v0.5.8`, `v0.5.9b1` to `v0.5.9b3` | `python/pyproject.toml:7` → `version = "0.5.7"` |
| TypeScript package (repo) | `camoufox` **0.5.7** (renamed from `@camoufox/camoufox` in `ac2ce31`, 2026-10-06) | `typescript/package.json:2-3`; npm publication not checked |
| Browser license | **MPL-2.0** (Firefox fork) | root `LICENSE` |
| Python wrapper license | **MIT** | `python/pyproject.toml:10` → `license = "MIT"` |
| Vendored cursor-path generator | **LGPLv3-or-later** (Cursory, cursory-js 2.0.2) | `browser/additions/juggler/input/cursory/NOTICE`; `README.md:583-585`, `:729` |
| Primary language | **C++** patches over Firefox, Juggler in JavaScript, launchers in Python and TypeScript | tree layout (`browser/patches/`, `browser/additions/`, `python/`, `typescript/`) |
| Last commit | 2026-10-13 (`4559d01`) | `git log` |
| Camoufox source patches | **42** stealth/parity/debloat patches + **2** Playwright/Juggler patches (plus 2 vendored debloat patches, one LibreWolf and one Ghostery; 14 before `658806e`) | `browser/patches/*.patch` (42), `browser/patches/playwright/*.patch` (2), `browser/patches/librewolf/`, `browser/patches/ghostery/` |

> Note the licence split: the browser is a Firefox fork and is therefore **MPL-2.0**, while the `camoufox` Python launcher library and the TypeScript launcher are **MIT**; the Cursory cursor-path code vendored inside Juggler is **LGPLv3-or-later**, not MPL-2.0 (`README.md:726-731`). Earlier analyses that called the whole project "MIT" or "MPL" were only half right.

> Build matrix (`.github/workflows/release.yml:144-155`): Linux, Windows and macOS for x86_64, arm64 and i686, minus Windows arm64 (commented "Fails (.mozbuild does not include clang++-cl)"), macOS i686 and Linux i686. `README.md:644` states that `i686` builds Windows only; the launcher's platform table (`python/src/camoufox/pkgman.py:69-71`) lists Windows x86_64/i686, macOS x86_64/arm64 and Linux x86_64/arm64/i686. Which archives are published for each release was not checked (**Tier D**).

> Release flow (`.github/workflows/release.yml`, `ci/README.md`): every tested merge to `main` publishes a GitHub pre-release (the browser is rebuilt only when its sources changed) and matching library pre-releases (`bN` on PyPI, `-beta.N` on npm); a `vX.Y.Z` tag promotes them. A published library carries `python/src/camoufox/browser-pin.json` naming the browser build it was tested with (`{}` in the repository). A downloaded browser archive is checked against the sha256 digest GitHub publishes for the asset (`python/src/camoufox/pkgman.py:1058-1082`, called from `multiversion.py:379`). Since `1569b98` (2026-10-06) each browser release declares an `interface` number in its manifest and both libraries refuse a browser outside `MIN_INTERFACE` to `INTERFACE` (`python/src/camoufox/__version__.py:20-27`, both 1); the Python launcher now downloads the paired browser on first launch instead of raising.

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

The config is read by a single C++ helper, `browser/additions/camoucfg/MaskConfig.hpp`, which every patch calls into. It parses the JSON that the launcher passes in the `CAMOU_CONFIG` environment variable (split across `CAMOU_CONFIG_1..N` when long). Patches ask it for a value (`MaskConfig::GetDouble("window.innerWidth")`, `MaskConfig::GetString("headers.User-Agent")`, etc.); if the user or the fingerprint draw set one, the spoofed value is returned, otherwise the code falls through to the real Firefox implementation. Per-context values (one identity per Playwright context) bypass `CAMOU_CONFIG`: they are set through `window.setXxx()` helpers and stored per `userContextId` by `RoverfoxStorageManager` (`browser/patches/cross-process-storage.patch`, `docs/per-context-patches.md`). Since `0c98d2b` (2026-10-09) every per-context lookup takes the user context from the document's own principal, node or window (`RoverfoxStorageManager::UserContextId()`); before, a document without a browsing context (from `createHTMLDocument()` or `DOMParser`) read context 0, which could expose another context's GPU or font list (#839, per the commit message).

### C++ Level Fingerprint Injection

The core innovation is modifying Firefox's C++ source code to intercept property getters. From `browser/patches/fingerprint-injection.patch` (current source):

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

The same patch also hooks `GetInnerHeight`, `GetScreenY`, `GetDevicePixelRatio`, `nsScreen::PixelDepth` and `GetAvailRect`, and the worker-side `WorkerNavigator` getters (platform, appVersion, userAgent, hardwareConcurrency, GPC) — all through `MaskConfig::Get*`. `window.outerWidth`/`outerHeight` are deliberately **not** read from the config in the getter: a comment in the patch records that the real window is resized to the drawn size instead, because a fixed outer size contradicted the real inner size (measured `innerWidth` 1853 > `outerWidth` 1680 on GNOME). The comment still names `browser-init.js`; since `658806e` (2026-10-06) `browser-init.patch` is gone and the resize is done by a separate module, `browser/additions/browser/modules/CamoufoxWindow.sys.mjs:111-126` (registered by `camoufox-window-module.patch`), whose header comment says `chrome://browser/content/` is content-accessible and must stay byte-identical to stock. Since `0c98d2b` it sizes only windows the driver opens; a page's popup keeps the size it asked for.

**What this changes:**
- The getter returns the configured value directly from C++
- There is no JavaScript wrapper or proxy on the property, so `Object.getOwnPropertyDescriptor()` shows a native accessor and `toString()` returns `[native code]`
- Per-context values are served from a cache: a comment in `browser/patches/cross-process-storage.patch:150-151` records that an uncached synchronous IPC read per unset key had made `navigator.hardwareConcurrency` and `screen.*` reads about 20x slower than stock, a timing a page can measure

### HTTP Header Spoofing (network layer, not TLS)

`browser/patches/network-patches.patch` hooks `netwerk/protocol/http/nsHttpHandler.cpp` to override the `User-Agent`, `Accept-Language` and `Accept-Encoding` request headers from the config (the User-Agent falls back to `navigator.userAgent` when `headers.User-Agent` is unset):

```cpp
// netwerk/protocol/http/nsHttpHandler.cpp
if (auto value = MaskConfig::GetString("headers.User-Agent")) { /* use spoofed UA */ }
if (auto value = MaskConfig::GetString("navigator.userAgent")) { /* ...or the navigator UA */ }
...
if (auto value = MaskConfig::GetString("headers.Accept-Language")) { /* use spoofed AL */ }
if (auto value = MaskConfig::GetString("headers.Accept-Encoding")) { /* use spoofed AE */ }
```

> **Important limitation:** this is HTTP-header spoofing, **not TLS/JA3/JA4 fingerprint impersonation.** Camoufox sends a real Firefox TLS ClientHello (because it *is* Firefox), which is coherent for a Firefox persona but cannot be changed to look like Chrome. There is no ja3/ja4 rewriting in the source (no `ja3`, `ja4`, `ClientHello` or TLS-fingerprint reference in `browser/patches/`, `browser/additions/`, `browser/settings/`, `browser/scripts/`, `python/src/`, `typescript/src/` or `docs/`, re-checked at `4559d01`).

### Juggler Protocol Isolation

Camoufox uses **Juggler** (Firefox's automation protocol used by Playwright) instead of CDP. The full Juggler implementation lives under `browser/additions/juggler/` and is patched to run in an isolated scope (as described in the project README, **Tier B**; the isolated and main worlds are implemented in `browser/additions/juggler/content/FrameTree.js` and `Runtime.js`). Since `e3f9a20` (#847, 2026-10-12) Juggler is no longer registered as a `chrome://` package: its files are installed under `modules/juggler/` and loaded from `resource://gre/modules/juggler/` (e.g. `browser/additions/juggler/protocol/Dispatcher.js:5-6`; rule `juggler-is-not-a-chrome-package`, `ci/tribal-rules.yml:519`), and the browser is built with `MOZILLA_OFFICIAL` (`browser/assets/base.mozconfig:42`). The commit message reports that hCaptcha's script probed `chrome://juggler/content/content/WorkerMain.js` with `new Worker()`, so any build that registered a `juggler` package could be told apart from stock Firefox (**Tier B**):

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

From `browser/patches/playwright/1-leak-fixes.patch` — the webdriver property fix at C++ level. The pre-image of `Navigator::Webdriver()` (Firefox with Playwright's patch applied) checks Marionette and RemoteAgent and otherwise returns `true` under a "Playwright is automating the browser" comment; Camoufox deletes those checks and returns a flat `false`:

```cpp
// dom/base/Navigator.cpp
/* static */
bool Navigator::Webdriver() {
  return false;
}
```

This is now the patch's only change (it diffs only `dom/base/Navigator.cpp`). Its former second hunk, which reverted Playwright's `new PlaywrightPoliciesProvider()` in `EnterprisePoliciesParent.sys.mjs`, was dropped when `658806e` removed that hunk (and the `chrome/juggler` packaging entries) from `0-playwright.patch` itself. A separate opt-in, `main_world_eval=True` (config key `allowMainWorld`), lets you run a script in the page's main world by prefixing it with `mw:` (e.g. `page.evaluate("mw:" + script)`) — otherwise Playwright scripts stay in the isolated world (`browser/additions/juggler/content/Runtime.js` refuses an `mw:` call unless the flag is set). Two further patches touch what content can observe: `debugger-invisible-to-content.patch` adds a Debugger flag so that attaching a Debugger does not cause content-visible side effects (extra stack capture, a disabled Promise return-value optimisation, wasm deoptimisation), and `window-setter-seal.patch` keeps the per-context `window.setXxx()` helpers off `window` once init scripts have run.

### fpgen Integration (default fingerprint synthesis)

When you don't supply values, the launcher fills them with **fpgen** ([scrapfly/fingerprint-generator](https://github.com/scrapfly/fingerprint-generator)), which the project README describes as "a model of real traffic" (`README.md:406-407`, **Tier B** for the distribution claim), and then runs the draw through a coherence check:

```python
# python/src/camoufox/fingerprints.py
_FP_GENERATOR = load_fpgen().Generator()   # built on first use (_generator(), lines 50-56)
fingerprint = _generator().generate(browser='Firefox', **conditions, **screen_conditions)   # generate_fingerprint(), line 1745
```

- The launcher drew from **BrowserForge** (`browserforge = "^1.2.4"`) until repo commit `6daae88` (2026-09-24); `python/pyproject.toml:35` now declares `fpgen = "^1.3.0"`. The latest PyPI release, 0.5.8, is tagged at `ac2ce31`, whose `pythonlib/pyproject.toml:35` declares `fpgen`; 0.5.6 (`eb5dc3b`) still declared `browserforge`. The TypeScript launcher now depends on the published `fpgen-js` package (`4ac9395`).
- fpgen's model is installed from a release pinned by sha256 (`python/src/camoufox/fpgen-model.json`, `fpgen_model.py:122`) by `camoufox fetch` or on the first draw, in place of fpgen's own unpinned download. Since `4559d01` the pinned files are dated 2038-01-01 (previously 2100-01-01) so that file systems with 32-bit timestamps keep the date and fpgen's refresh does not replace them (#854).
- `python/src/camoufox/coherence.py` (`validate()` / `apply()`) holds whole-identity rules — Apple-Silicon core counts, GPU vs OS, Intel-Mac GPU vs core count and screen, `colorDepth` in {24, 30}, `maxTouchPoints`, per-OS `devicePixelRatio` steps, window chrome, avail bounds, UA/platform architecture — and is applied to generated fingerprints, bundled presets and hand-written configs.
- fpgen supplies navigator, screen, window and headers; the GPU comes from fpgen's WebGL records, and fonts, speech voices and media devices are drawn from catalogues in the package (`fonts.json`, `voice-manifests.json`, `media-devices.json`) (`coherence.py:1-9`, module docstring).
- **GPU and canvas planning** (`159aebe`, `5c1fd57`, 2026-10-08/09): one function per launcher (`plan_rendering`, `python/src/camoufox/utils.py:722-745`; `planRendering` in TypeScript) decides the GPU. On the host's OS, with no GPU named, the identity claims the GPU Firefox actually renders with, if fpgen has recorded it. When the identity claims another OS or another GPU (`webgl_config`, a preset's GPU, or a host GPU fpgen never recorded), canvas and WebGL readback are replaced by `privacy.resistFingerprinting`'s random placeholder (`canvas_noise`; see *Canvas* below). A `webgl_config` pair must be one fpgen recorded for Firefox on that OS, otherwise `ValueError` (`utils.py:1005-1008`). Spoofed avail-screen and touch values are claimed as Firefox's baseline fingerprinting protection reports them: the screen less 48 px on Windows, 76 px on macOS and nothing on Linux; more than one touch point becomes 5 (`follow_baseline_protection`, `fingerprints.py:779`; `ci/tribal-rules.yml:226-258`).

### Real Fingerprint Presets (opt-in)

For evasion against consistency checks that generated identities can trip, Camoufox also ships bundles of **real** fingerprints scraped from in-the-wild Firefox traffic. `python/src/camoufox/fingerprint-presets-v150.json` holds **285 presets** — 168 Windows / 58 macOS / 59 Linux — with Firefox v149–v152 user agents (`min_firefox_version: 149`, `source: roverfox_fingerprints`); `fingerprint-presets.json` is an older bundle of 113 presets (71 / 25 / 17, Firefox 119–148 user agents). `_select_presets_file()` (`fingerprints.py:1133-1146`) picks the v150 bundle for binaries at Firefox 149 or later, and `from_preset()` rewrites the UA's Firefox version to the active binary's (`fingerprints.py:1252-1255`). Opt in with `fingerprint_preset=True`; pass a preset dict instead of `True` to pin a specific identity. `ROADMAP.md` at `2f30fea` noted that presets naming GPUs with no recorded WebGL parameters (Windows on ARM/Adreno, Direct3D 10-level hardware, some Mesa and older Intel Linux drivers) were dropped; the file was deleted in `658806e`. A preset's GPU counts as a named GPU, so with the default `canvas_noise=None` a preset launch gets the canvas placeholder (see above).

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

Coverage is broad and applied natively. The patches map onto these areas (non-exhaustive; 42 top-level patch files):

| Category | Properties Spoofed | Patch(es) |
|----------|-------------------|-----------|
| **Navigator** | userAgent, platform, hardwareConcurrency, oscpu, appVersion, language, globalPrivacyControl (window and workers), maxTouchPoints; `doNotTrack` is set as a pref by the launcher | `navigator-spoofing.patch`, `fingerprint-injection.patch`, `touchscreen-fingerprint-spoofing.patch`, `locale-spoofing.patch` |
| **Screen** | width, height, availLeft/Top/Width/Height, colorDepth, pixelDepth (the CSS `color` media feature follows `colorDepth`) | `screen-spoofing.patch`, `fingerprint-injection.patch` |
| **Window** | innerWidth/Height, screenX/Y, devicePixelRatio (`outerWidth`/`outerHeight` are not read from the config in the getter; the real window is resized) | `fingerprint-injection.patch`, `camoufox-window-module.patch` (`CamoufoxWindow.sys.mjs`) |
| **WebGL / WebGPU** | UNMASKED_VENDOR/RENDERER (since `0c98d2b` after stock's fingerprinting-protection checks, as for `RENDERER`), parameter table, supported extensions, shader precision formats; `getContextAttributes()` and live state (e.g. `lineWidth`, viewport) come from the real context. On the host's OS the claimed GPU is the host's own. `navigator.gpu` exists only where Firefox exposes it for the claimed device (Windows, Apple Silicon), and the adapter is the host's only when the identity claims the host's GPU; otherwise the `gfx.blacklist.webgpu` pref blocks it (`ci/tribal-rules.yml:260`) | `webgl-spoofing.patch`; WebGPU through launcher prefs (`host_rendering.py`) |
| **Audio** | sampleRate, output latency, channel counts + seeded per-context noise | `audio-context-spoofing.patch`, `audio-fingerprint-manager.patch` |
| **Fonts** | per-context installed-font list, system-UI and CSS2 system fonts following the context's own claimed OS (since `0c98d2b`), per-context font-group plumbing; no glyph-spacing or metrics noise | `font-list-spoofing.patch`, `font-hijacker.patch`, `system-ui-font-spoofing.patch`, `font-system-fonts-css2.patch`, `anti-font-fingerprinting.patch` |
| **Canvas** | not perturbed when the identity claims the host's OS and GPU: output is left as the GPU and fonts render it (`ci/tribal-rules.yml:203`, rule `canvas-is-not-noised`; no `canvas:seed`). When the identity claims another OS or GPU, the launchers turn on Firefox's `privacy.resistFingerprinting` canvas targets through the baseline overrides, so canvas and WebGL readback return random placeholder data, as in LibreWolf, Tor Browser and Mullvad Browser; stock Firefox does not do this, and the launch emits a `LeakWarning` (`canvas_noise`, default `None` = on only in that case; `ci/tribal-rules.yml:226`, `python/src/camoufox/utils.py:1009-1016`). The default `os` is a random pick of Windows, macOS and Linux (`utils.py:914-917`), so a default launch claims another OS than the host's in most draws | — |
| **Speech/Voices** | speechSynthesis voices (`speak()` on a spoofed voice starts and ends after the text's duration) | `speech-voices-spoofing.patch`, `voice-spoofing.patch` |
| **Media** | enumerateDevices output with labels and group ids (a fake media engine, so a claimed device captures), codec-support probes (`media:spoof_codecs`) | `media-device-spoofing.patch`, `media-codec-spoofing.patch` |
| **Network** | WebRTC ICE IP (protocol level; the fabricated port follows the context's OS since `0c98d2b`), HTTP User-Agent + Accept-Language + Accept-Encoding; the build's own User-Agent app name is set to `Firefox` (`MOZ_APP_UA_NAME`) | `webrtc-ip-spoofing.patch`, `network-patches.patch`, `user-agent-app-name.patch` |
| **Geo/Locale** | geolocation, timezone (per realm), locale (Intl; the OS/default locale only), browser UI strings through packaged language packs; `geoip=True` reads the GeoIP AIO database by default since `f36390a` (GeoLite2 deprecated, `python/src/camoufox/repos.yml:51-54`) | `geolocation-spoofing.patch`, `timezone-spoofing.patch`, `locale-spoofing.patch` |
| **DOM/behavior** | closed shadow-root piercing for automation, forced default pointer (any-pointer gains coarse only when `maxTouchPoints` > 0), optional instant CSS animations (`instantAnimations`, off by default), option-targeted events on `<select>` commits | `shadow-root-bypass.patch`, `force-default-pointer.patch`, `no-css-animations.patch`, `trusted-automation-events.patch` |

WebRTC spoofing is a real protocol-level implementation (`WebRTCIPManager` plus hooks in `PeerConnectionImpl.cpp` for SDP, ICE candidates and `getStats()`, keyed per user context), not just a JS toggle — though you can also fully disable WebRTC with `block_webrtc=True`.

---

## What Changed Since the 2026-09-30 Analysis

40 commits separate the previous pin (`2f30fea`, 2026-09-30) from `4559d01` (2026-10-13). The Firefox base (156.0.1), the `MaskConfig` mechanism and Juggler isolation are unchanged. Browser pre-releases `v156.0.1-beta.34` to `beta.38` and library tags `v0.5.7`, `v0.5.8` and `v0.5.9b1` to `b3` were cut in this window; the restructure and the GPU/canvas changes below are in `v0.5.9b1` and later, not in PyPI 0.5.8.

- **Repository split** (`cbca509`, #846, 2026-10-10): `patches/`, `additions/`, `settings/` and `upstream.sh` moved under `browser/`; `pythonlib/camoufox/` became `python/src/camoufox/`. All paths on this page are now the new ones.
- **Patch set 44 to 42** (`658806e`, `914b575`, `a4a9286`, 2026-10-06/07): removed `browser-init`, `global-style-sheets`, `pin-addons`, `windows-theming-bug-modified`; added `camoufox-window-module` (window sizing and startup work moved into `CamoufoxWindow.sys.mjs`, outside the content-accessible `chrome://browser/content/`) and `user-agent-app-name` (`MOZ_APP_UA_NAME` = `Firefox`). Vendored LibreWolf patches reduced to one (`disable-data-reporting-at-compile-time.patch`), plus one Ghostery patch. `1-leak-fixes.patch` now touches only `Navigator.cpp`. The per-context storage code moved from `anti-font-fingerprinting.patch` into `cross-process-storage.patch`.
- **Juggler hidden from content** (`e3f9a20`, #847, 2026-10-12): Juggler is loaded from `resource://gre/modules/juggler/` instead of a registered `chrome://juggler` package, and the build uses `MOZILLA_OFFICIAL` (official branding paths, no `browser-development-helpers.js` in a content-accessible package). Per the commit message, hCaptcha's script detected the registered package through a `new Worker()` probe.
- **Host GPU and cross-OS canvas** (`159aebe`, `5c1fd57`, `0bb4f14`, 2026-10-08/09): on the host's OS the identity claims the host's real GPU; on another OS or GPU canvas and WebGL readback become `privacy.resistFingerprinting`'s random placeholder (`canvas_noise`, on by default only in that case, with a `LeakWarning`). WebGPU follows the claimed device. Browser-owned WebGL values follow Firefox 156 rather than fpgen's Firefox 146 recordings (Windows gains `EXT_depth_clamp`; Linux WebGL1 `ALIASED_LINE_WIDTH_RANGE`). Avail-screen and touch-point values follow baseline fingerprinting protection.
- **Per-context identities bound to the host** (`5c1fd57`, `0c98d2b`): on a browser launched without the canvas placeholder, `NewContext()` contexts claim the host's OS and GPU, and asking for another OS or a preset from another OS raises `ValueError` (`python/src/camoufox/utils.py:766-791`; `docs/per-context-patches.md:212-230`). Per-context lookups now resolve the user context from the document itself (#839).
- **Config keys** (`7a4ac0d`, #836): `browser/settings/properties.json` declares 78 live keys (82 at `2f30fea`; `navigator.buildID`, `webGl:contextAttributes`, `webGl2:contextAttributes` and `disableTheming` are no longer live) and 54 more marked `removed`, restored so camoufox 0.4.x, which validates its config against the browser's file, keeps launching (#835). Rule `config-keys-are-never-deleted` (`ci/tribal-rules.yml:456`).
- **Launcher and packaging**: browser releases declare an `interface` number and libraries refuse incompatible browsers; Python installs the paired browser on first launch (`1569b98`); npm package renamed `camoufox` (`ac2ce31`); `geoip=True` defaults to the GeoIP AIO database, GeoLite2 deprecated (`f36390a`); proxy credentials are percent-encoded in the geoip lookup URL (`e8989c4`); `browser=` together with `executable_path` raises (`5c1fd57`); launch inputs are no longer modified in place (`0bb4f14`); fpgen model files re-dated for 32-bit timestamps (`4559d01`).
- **Cursor**: vendored cursory-js 2.0.2 drops one recording that idled 4.5 s before moving; 2,356 recordings (`0c43443`). `fill()` now inserts text through the control's editor so `change` fires (`ecf62d2`).
- **README rewrite**: the generic "invisible to anti-bot systems" line and the "~200 MB memory" debloat figure are gone; fpgen is described as "a model of real traffic"; the limitation statements remain (`README.md:545-546`, `:565-568`). `ROADMAP.md` was deleted (`658806e`).

Re-verified at `4559d01`:

- **Auto timezone and WebRTC IP from a per-context proxy's exit IP** (`python/src/camoufox/async_api.py:188-240`; the lookup is an HTTP request to `ip-api.com` made through the proxy, `ip.py:81-100`, and a failed lookup raises `InvalidIP`); launch-level `geoip=True` derives location, timezone and locale.
- **`disable_coop`**, **`main_world_eval` with the `mw:` prefix**, **`fonts` / `custom_fonts_only`**, `pin_cpu_cores`, and the launch flags `block_images`, `block_webgl`, `screen`, `window`, `ff_version`, `virtual_display`, `enable_cache`, `exclude_addons`, `addons`. The 14 `window.setXxx()` helpers and their seal (`window-setter-seal.patch`, rule at `ci/tribal-rules.yml:415`) are unchanged in count.

---

## What Changed Since the 2026-08-14 Analysis

*(Paths in this section are as of `2f30fea`, before the `browser/` / `python/` split.)*

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

Carried over from the 2026-08 analysis and re-verified at `2f30fea` (see the 2026-09-30 section above for the current references):

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
| **Per-context identities** | `NewContext()` gives each context a fresh fpgen-drawn (or preset) identity with its own audio seed, plus per-context proxy, geolocation and WebRTC IP; setters sealed before page script runs. Without `canvas_noise`, contexts keep the host's OS and GPU |
| **Coverage** | Navigator, Screen, WebGL/WebGPU, Audio, Fonts, Voices, Media devices, WebRTC, geo/locale (canvas is not perturbed on the host's OS; random placeholder readback on another OS or GPU) |
| **Active development** | Tracks current Firefox (base 156.0.1); latest release 2026-10-13 |
| **Recorded-movement cursor** | `humanize=True` replays recorded human mouse movements (Cursory) |
| **Debloated** | Telemetry and data reporting removed at compile time, onboarding disabled, no bundled search engines, Mozilla services turned off in `camoufox.cfg` (`README.md:534-542`); the README no longer gives a memory figure |
| **Open source** | Browser MPL-2.0, Python and TypeScript launchers MIT, vendored Cursory LGPLv3-or-later — patches are all readable in `browser/patches/` |

### Disadvantages

| Con | Details |
|-----|---------|
| **Firefox only** | Cannot impersonate Chrome; Firefox is a small share of real traffic |
| **No TLS impersonation** | Sends genuine Firefox TLS (coherent, but can't be reshaped to Chrome JA3/JA4) |
| **SpiderMonkey detection** | Some WAFs treat Firefox engine more suspiciously |
| **Build complexity** | Building the browser from source needs a Linux host (Windows and macOS are cross-compiled); `AGENTS.md` quotes about 40 minutes for a cold build, and the font bundle is a separate 843 MB download (most users fetch the prebuilt binary) |
| **No Windows ARM64 build** | `release.yml` excludes Windows arm64 (commented "Fails (.mozbuild does not include clang++-cl)") |
| **Release lag** | The latest PyPI release (0.5.8) is fpgen-based, but the repository split, host-GPU claim, cross-OS canvas placeholder and Juggler relocation are only in library pre-release tags (`v0.5.9b1` to `b3`) and browser pre-releases (`beta.37`, `beta.38`) |
| **Cross-OS canvas differs from stock** | An identity claiming another OS or GPU than the host's gets random canvas/WebGL readback, which stock Firefox does not produce (the launcher warns; `ci/tribal-rules.yml:226`) |
| **Host-OS rendering** | The project docs state that the per-context patches change what JS APIs report, not how the OS renders (font rasterisation, scrollbars, canvas device class) (`docs/per-context-patches.md:212-230`, "Known limitations", Tier B); the same section recommends `canvas_noise=True` where the claimed OS differs from the host's |

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
import { Camoufox } from "camoufox";

const browser = await Camoufox({ headless: true });
const page = await browser.newPage();
await page.goto("https://example.com");
await browser.close();
```

(`typescript/README.md:26`, `:46`; install with `npm install camoufox playwright-core`; npm publication not verified.)

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

### Useful launch options (from `python/src/camoufox/utils.py`)

`os`, `block_images`, `block_webrtc`, `block_webgl`, `disable_coop`, `webgl_config`, `geoip` / `geoip_db`, `humanize`, `locale`, `addons` / `exclude_addons` / `allow_addon_new_tab`, `fonts` / `custom_fonts_only`, `screen`, `window`, `fingerprint` / `fingerprint_preset`, `ff_version`, `headless`, `main_world_eval`, `enable_cache`, `virtual_display`, `pin_cpu_cores`, `canvas_noise`, `executable_path` / `browser` (mutually exclusive since `5c1fd57`), `firefox_user_prefs`, `proxy`.

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
| `browser/additions/camoucfg/MaskConfig.hpp` | Central C++ config reader every patch calls into |
| `browser/patches/fingerprint-injection.patch` | C++ hooks for window/screen values and the worker-side navigator getters |
| `browser/patches/playwright/1-leak-fixes.patch` | `webdriver=false` (its only change) |
| `browser/patches/playwright/0-playwright.patch` | Juggler/Playwright integration |
| `browser/patches/webgl-spoofing.patch` | WebGL params, extensions, shader precision, UNMASKED_* |
| `browser/patches/webrtc-ip-spoofing.patch` | WebRTC IP replacement in SDP, ICE candidates and `getStats()`, per user context |
| `browser/patches/network-patches.patch` | HTTP User-Agent, Accept-Language and Accept-Encoding override |
| `browser/patches/audio-context-spoofing.patch`, `browser/patches/audio-fingerprint-manager.patch` | Audio spoofing + seeded noise |
| `browser/patches/shadow-root-bypass.patch` | Closed shadow-root piercing for automation |
| `browser/patches/window-setter-seal.patch` | Seals the per-context `window.setXxx()` helpers once init scripts have run |
| `browser/patches/cross-process-storage.patch` | `RoverfoxStorageManager`: per-user-context value store and cache |
| `browser/additions/browser/modules/CamoufoxWindow.sys.mjs` | Window sizing and startup work (replaces `browser-init.patch`) |
| `browser/additions/juggler/input/CursorTrajectory.js`, `browser/additions/juggler/input/cursory/` | Humanized cursor path: replays recorded human movements (vendored cursory-js, LGPLv3-or-later) |
| `browser/additions/juggler/` | Full patched Juggler automation protocol (loaded from `resource://gre/modules/juggler/`) |
| `python/src/camoufox/fingerprints.py` | fpgen integration, preset routing, per-context init script |
| `python/src/camoufox/coherence.py` | Whole-identity coherence rules |
| `python/src/camoufox/fingerprint-presets-v150.json` | 285 real fingerprint presets (v149–v152); `fingerprint-presets.json` holds 113 older ones |
| `python/src/camoufox/async_api.py` / `sync_api.py` |
| `python/src/camoufox/utils.py`, `host_rendering.py` | Launch options; `plan_rendering` (host GPU vs canvas placeholder), WebGPU prefs | Per-context identity (`NewContext`) and init-script helpers |
| `browser/settings/properties.json` | Every declared config key and its type (78 live, plus 54 marked `removed` kept for older libraries) |
| `ci/tribal-rules.yml` | Settled design decisions with their evidence (e.g. no canvas noise on the host's OS, cross-OS canvas placeholder, no glyph-spacing noise, Juggler not a chrome package) |
| `typescript/` | TypeScript/JavaScript launcher |
| `browser/upstream.sh` | Pins the upstream Firefox base version (currently 156.0.1) |

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

Camoufox is one of two tools of the ten that fork Firefox rather than Chromium (the other is invisible_playwright). Fingerprint values are substituted in C++ getters, so the substitution is not observable through JS property-descriptor or prototype inspection. Verified capabilities at the 2026-10-13 snapshot (`4559d01`): Firefox 156.0.1 base, 42 patches in `browser/patches/` plus 2 Playwright/Juggler patches, fpgen-drawn identities with a coherence check (in PyPI 0.5.8), real-fingerprint presets, per-context identities with an audio seed, proxy-derived timezone and WebRTC IP, `humanize` cursor replay of recorded movements, and Juggler loaded from `resource://gre`. Canvas output is not perturbed when the identity claims the host's OS and GPU; for another OS or GPU the launchers switch canvas and WebGL readback to Firefox's resistFingerprinting placeholder.

**Applicability constraint:** the engine is Firefox. Targets that treat Firefox differently from Chrome, or that probe SpiderMonkey engine behaviour (a residual signal the project documents), will identify the browser family regardless of fingerprint configuration.

**Limitation:** It is Firefox — small real-world share, and its genuine (unmodifiable) TLS fingerprint means you cannot masquerade as Chrome at the network layer.

---

*Analysis conducted for educational purposes. Facts verified against the cloned source tree and GitHub/PyPI release metadata as of 2026-10-13. Use responsibly.*
