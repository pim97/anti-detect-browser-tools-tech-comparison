# Camoufox - Deep Technical Analysis

> **Tool Type:** Custom Firefox Build (Anti-Detect Browser)
> **Repository:** [github.com/daijro/camoufox](https://github.com/daijro/camoufox)
> **Approach:** C++ level fingerprint injection + Juggler protocol isolation
> **Verified in source (Tier A):** 65 patch files in `browser/patches/` plus 2 in `browser/patches/playwright/` (51 of the 65 diff C/C++ sources; the other 14 diff JS, WebIDL, manifest or build files), including `fingerprint-injection`, `navigator-spoofing`, `screen-spoofing`, `locale-spoofing`, `webrtc-ip-spoofing`, `webrtc-socks5-udp`, `anti-font-fingerprinting`, `cpu-vendor-estimates`. The audio-noise patch (`audio-fingerprint-manager`) is gone. On `main`, humanized input is no longer in the browser: the `humanize*` config keys are marked `removed` (`browser/settings/properties.json:84-91`) and `humanize=True` runs the external `myuri` package in the launcher process (`python/src/camoufox/humanize.py:1-29`; `python/pyproject.toml`, `myuri = "4.0.0"`). The latest release, `v159.0-beta.42` (`340cf16`), still replays vendored Cursory movements in Juggler (`browser/additions/juggler/input/CursorTrajectory.js` at that tag). `Runtime.enable` is not applicable: automation runs over Juggler, not CDP.
> **Anti-bot service claims:** **none** — the project makes no claims about Cloudflare, DataDome, Kasada or similar, and its README instead **documents limitations**: some WAFs test SpiderMonkey engine behaviour, which no spoofing turns into Chromium (`README.md:591-592`), and "Camoufox can still be detected" because anti-bot vendors look for the one value that does not agree with the rest (`README.md:611-614`) (**Tier D** for coverage; the limitations are **Tier B**)
> **Maintenance:** Actively developed — browser `v159.0-beta.42` (2026-11-15, pre-release, Firefox 159.0); the latest non-pre-release is `v158.0.1-beta.41` (2026-10-29, GitHub API). Python wrapper `camoufox` **0.5.9** on PyPI (2026-11-01; upstream has tags `v0.5.9b1` to `v0.5.9b6` but no `v0.5.9` tag, so which commit it was built from is not recorded); library pre-release tag `v0.5.10b1` = `340cf16`. Releases now ride a twice-monthly train (1st and 15th). 13,488 stars, 1,154 forks, 51 contributors, 77 open issues, last push 2026-11-19. MPL-2.0.
> **Verified:** 2026-11-20 against `daijro/camoufox` @ `4c909d6` (previous pass: `4559d01`, 2026-10-13).

---

## Table of Contents

- [What is Camoufox?](#what-is-camoufox)
- [Version & Status (2026-11)](#version--status-2026-11)
- [How It Works](#how-it-works)
- [Properties of C++-Level Spoofing](#properties-of-c-level-spoofing)
- [Fingerprint Capabilities](#fingerprint-capabilities)
- [What Changed Since the 2026-10-13 Analysis](#what-changed-since-the-2026-10-13-analysis)
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

The project is authored by **daijro** (also the author of [BrowserForge](https://github.com/daijro/browserforge)). As of 2026-11-20 it has ~13.5k GitHub stars and 51 contributors. The C++ browser fork tracks upstream Firefox — the current base is **Firefox 159.0** (`browser/upstream.sh`). A thin Python library (`camoufox`) wraps Playwright's Firefox driver to launch the binary and feed it a fingerprint config; the repository also carries a TypeScript/JavaScript launcher (`typescript/`). Since `cbca509` (2026-10-10) the repository is split into `browser/` (patches, additions, settings, build), `python/` (formerly `pythonlib/`) and `typescript/`.

---

## Version & Status (2026-11)

| Item | Value | Evidence |
|------|-------|----------|
| Latest release | `v159.0-beta.42`, 2026-11-15 (pre-release) | GitHub Releases API (`STATUS.md`); tag at `340cf16`, the same commit as library tag `v0.5.10b1` |
| Latest non-pre-release | `v158.0.1-beta.41` (2026-10-29, GitHub API); `browser/settings/properties.json` marks keys removed in `158.0-beta.41` and `159.0-beta.35` | — |
| Upstream Firefox base | **159.0** | `browser/upstream.sh` → `version=159.0` (`release=beta.35`; a browser release's number is taken from its tag at build time, `ci/release.py:22-24`) |
| Python package (PyPI) | **0.5.9** (2026-11-01) | PyPI (latest as listed in `STATUS.md`); no `v0.5.9` tag in the clone, so the commit it was built from was not identified (**Tier D** for its contents) |
| Python package (repo) | **0.5.7** in tree; the release pipeline writes the published version into `pyproject.toml` (`ci/release.py:32`, `:667-668`); library tags in the clone since the previous pass: `v0.5.10b1` only | `python/pyproject.toml:7` → `version = "0.5.7"` |
| Python requirement (repo) | `^3.11` on `main` (was `^3.10`; raised for `myuri`) | `python/pyproject.toml` (`python = "^3.11"`) |
| TypeScript package (repo) | `camoufox` **0.5.7** | `typescript/package.json:2-3`; npm publication not checked |
| Browser license | **MPL-2.0** (Firefox fork) | root `LICENSE`; `README.md:852-856` |
| Python wrapper license | **MIT** | `python/pyproject.toml:10` → `license = "MIT"` |
| Humanize engine | `main`: external `myuri` 4.0.0 (Python) / `@jwriter20/myuri` 4.0.0 (npm), pinned; its licence is not in the clone (**Tier D**). Release `v159.0-beta.42`: vendored Cursory (cursory-js) in Juggler, LGPLv3-or-later per its `NOTICE` at that tag | `python/pyproject.toml`; `typescript/package.json`; `README.md:867` |
| Primary language | **C++** patches over Firefox, Juggler in JavaScript, launchers in Python and TypeScript | tree layout (`browser/patches/`, `browser/additions/`, `python/`, `typescript/`) |
| Last commit | 2026-11-18/19 (`4c909d6`) | `git log` |
| Camoufox source patches | **65** stealth/parity/debloat patches + **2** Playwright/Juggler patches (plus 2 vendored debloat patches, one LibreWolf and one Ghostery); 64 at release tag `340cf16` (`input-timestamp-tick` came after it) | `browser/patches/*.patch` (65), `browser/patches/playwright/*.patch` (2), `browser/patches/librewolf/`, `browser/patches/ghostery/` |

> Note the licence split: the browser is a Firefox fork and is therefore **MPL-2.0**, while the `camoufox` Python launcher library and the TypeScript launcher are **MIT** (`README.md:852-858`). The README's licensing table no longer has a Cursory/LGPL row: on `main` no Cursory code is vendored in the tree (`browser/additions/juggler/input/` holds only `HumanDelay.js` and `MouseDispatch.js`); it credits Cursory's recordings as what `myuri` replays (`README.md:867`). Builds up to `v159.0-beta.42` still ship the vendored LGPLv3-or-later cursory-js inside Juggler.

> Build matrix (`.github/workflows/release.yml:216-227`): Linux, Windows and macOS for x86_64, arm64 and i686, minus Windows arm64 (commented "Fails (.mozbuild does not include clang++-cl)"), macOS i686 and Linux i686; every target now builds to the end (`fail-fast: false`). `README.md:770` states that `i686` builds Windows only; the launcher's platform table (`python/src/camoufox/pkgman.py:75-78`) lists Windows x86_64/i686, macOS x86_64/arm64 and Linux x86_64/arm64/i686. Which archives are published for each release was not checked (**Tier D**).

> Release flow (`ci/release.py:1-24`, `.github/workflows/release.yml:44-45`, rule `releases-ride-a-twice-monthly-train`, `ci/tribal-rules.yml:996`): releases ride a train on the 1st and 15th of each month. The scheduled run promotes the newest pre-release to stable (browser marked latest, library without its `bN` suffix to PyPI and npm `latest`), refused while an issue labelled `regression` is open, then cuts the next pre-release from `main` (browser rebuilt only when its sources changed; libraries to PyPI and npm `next`). Before issue #863 every merge was released. A published library carries `python/src/camoufox/browser-pin.json` naming the browser build it was released with (`{}` in the repository). A downloaded browser archive is checked against the sha256 digest GitHub publishes for the asset (`python/src/camoufox/pkgman.py:1097-1119`, called from `multiversion.py:379`). Each browser release declares an `interface` number and both libraries refuse a browser outside `MIN_INTERFACE` to `INTERFACE` (`python/src/camoufox/__version__.py:19-27`, both still 1).

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
│  │      CUSTOM FIREFOX 159 BUILD            │                    │
│  │  ┌───────────────────────────────────┐  │                    │
│  │  │  C++ Fingerprint Injection        │  │                    │
│  │  │  (MaskConfig::Get* lookups)       │  │                    │
│  │  │  - Navigator properties           │  │                    │
│  │  │  - Screen dims (window is resized)│  │                    │
│  │  │  - WebGL params + shader precision│  │                    │
│  │  │  - CPU-vendor arithmetic, no noise│  │                    │
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

The config is read by a single C++ helper, `browser/additions/camoucfg/MaskConfig.hpp`, which every patch calls into. It parses the JSON that the launcher passes in the `CAMOU_CONFIG` environment variable (split across `CAMOU_CONFIG_1..N` when long). Patches ask it for a value (`MaskConfig::GetUint32("screen.colorDepth")`, `MaskConfig::GetString("headers.User-Agent")`, etc.); if the user or the fingerprint draw set one, the spoofed value is returned, otherwise the code falls through to the real Firefox implementation. Per-context values (one identity per Playwright context) bypass `CAMOU_CONFIG`: they are set through `window.setXxx()` helpers and stored per `userContextId` by `RoverfoxStorageManager` (`browser/patches/cross-process-storage.patch`, `docs/per-context-patches.md`). Since `0c98d2b` (2026-10-09) every per-context lookup takes the user context from the document's own principal, node or window (`RoverfoxStorageManager::UserContextId()`); before, a document without a browsing context (from `createHTMLDocument()` or `DOMParser`) read context 0, which could expose another context's GPU or font list (#839, per the commit message).

### C++ Level Fingerprint Injection

The core innovation is modifying Firefox's C++ source code to intercept property getters. From `browser/patches/fingerprint-injection.patch` (current source):

```cpp
// dom/base/nsScreen.cpp
int32_t nsScreen::PixelDepth() {
  if (auto value = MaskConfig::GetUint32("screen.colorDepth"))
    return value.value();
  if (auto value = MaskConfig::GetUint32("screen.pixelDepth"))
    return value.value();
  // Return 24 to prevent fingerprinting.
  ...
}

CSSIntRect nsScreen::GetAvailRect() {
  auto rect = MaskConfig::GetRect("screen.availLeft", "screen.availTop",
                                  "screen.availWidth", "screen.availHeight");
  if (rect.has_value()) { ... }
  ...
}
```

The same patch hooks `GetDevicePixelRatio` (the config value is read once per process and zoom scales it as stock scales the real one) and the worker-side `WorkerNavigator` getters (platform, appVersion, userAgent, hardwareConcurrency, GPC) — all through `MaskConfig::Get*`. **Window geometry is no longer read from the config in any getter**: `innerWidth`/`innerHeight`, `outerWidth`/`outerHeight` and `screenX`/`screenY` forward to stock, with comments in the patch saying that `CamoufoxWindow.sys.mjs` sizes the real content area to the identity's inner size and moves the first window to the identity's position, so iframes, popups and moved windows report their own values as in stock (`fingerprint-injection.patch`, `GetOuterWidth`, `GetScreenX`, `GetScreenY` hunks). At `4559d01` `GetInnerWidth`, `GetInnerHeight`, `GetScreenX` and `GetScreenY` still returned the config value. The sizing is in `browser/additions/browser/modules/CamoufoxWindow.sys.mjs:144-280` (`applyWindowSize`, holding the size through a late window-manager frame) and the positioning in `:111-142` (`applyWindowPosition`), registered by `camoufox-window-module.patch`; the module's header comment says `chrome://browser/content/` is content-accessible and must stay byte-identical to stock. A window a page opened keeps the size its `window.open()` features ask for (`CamoufoxWindow.sys.mjs:145-155`).

**What this changes:**
- The getter returns the configured value directly from C++
- There is no JavaScript wrapper or proxy on the property, so `Object.getOwnPropertyDescriptor()` shows a native accessor and `toString()` returns `[native code]`
- Getter cost is matched to stock in both directions. Per-context reads are memoised: `browser/patches/cross-process-storage.patch` records 380-680 ns for `navigator.hardwareConcurrency` and 820-940 ns for `screen.width` against stock 152.0.4's 45 ns and 130 ns before the memo (`:64-69`). `zz-stock-cost-parity.patch` then makes the spoofed getters do stock's own work first and substitute afterwards, because returning early had made them several times *faster* than stock (`screen.width` 18-24 ns vs 107 ns, `colorDepth` 10-15 vs 93, `maxTouchPoints` 18 vs 81; comment at `zz-stock-cost-parity.patch:240-244`). Both are timings a page can measure

### HTTP Header Spoofing (network layer, not TLS)

`browser/patches/network-patches.patch` hooks `netwerk/protocol/http/nsHttpHandler.cpp` to override the `User-Agent`, `Accept-Language` and `Accept-Encoding` request headers from the config (the User-Agent falls back to `navigator.userAgent` when `headers.User-Agent` is unset; it is now read once per process into a constant string because `UserAgent()` also runs off the main thread):

```cpp
// netwerk/protocol/http/nsHttpHandler.cpp (paraphrased)
for (const char* key : {"headers.User-Agent", "navigator.userAgent"})
  if (auto value = MaskConfig::GetString(key)) { /* spoofed UA, read once */ }
...
if (auto value = MaskConfig::GetString("headers.Accept-Language")) { /* use spoofed AL */ }
if (auto value = MaskConfig::GetString("headers.Accept-Encoding")) { /* use spoofed AE */ }
```

New since the previous pass: `per-context-http-user-agent.patch` sends a `NewContext()` identity's own User-Agent on requests that have no browsing context of their own (shared and service workers, CSP reports, keepalive fetches; `netwerk/protocol/http/HttpBaseChannel.cpp`), and `network-patches.patch` reads a `network:ipv4Only` key (rule `ipv4-only-network-not-disable-ipv6`, `ci/tribal-rules.yml:931`). Per the title of commit `46a8d92` (#989), a routed request now keeps its header order on the wire (not read in source, **Tier B**).

> **Important limitation:** this is HTTP-header spoofing, **not TLS/JA3/JA4 fingerprint impersonation.** Camoufox sends a real Firefox TLS ClientHello (because it *is* Firefox), which is coherent for a Firefox persona but cannot be changed to look like Chrome. There is no ja3/ja4 rewriting in the source (no `ja3`, `ja4`, `ClientHello` or TLS-fingerprint reference in `browser/patches/`, `browser/additions/`, `browser/settings/`, `browser/scripts/`, `python/src/`, `typescript/src/` or `docs/`, re-checked at `4c909d6`).

### Juggler Protocol Isolation

Camoufox uses **Juggler** (Firefox's automation protocol used by Playwright) instead of CDP. The full Juggler implementation lives under `browser/additions/juggler/` and is patched to run in an isolated scope (as described in the project README, **Tier B**; the isolated and main worlds are implemented in `browser/additions/juggler/content/FrameTree.js` and `Runtime.js`). Since `e3f9a20` (#847, 2026-10-12) Juggler is no longer registered as a `chrome://` package: its files are installed under `modules/juggler/` and loaded from `resource://gre/modules/juggler/` (e.g. `browser/additions/juggler/protocol/Dispatcher.js:5-7`; rule `juggler-is-not-a-chrome-package`, `ci/tribal-rules.yml:976`), and the browser is built with `MOZILLA_OFFICIAL` (`browser/assets/base.mozconfig:36`). New since the previous pass: `isolated-world-global-order.patch` keeps driver calls from defining interfaces on the page's window, and `debugger-invisible-to-content.patch` now also keeps Juggler's and the isolated world's frames out of stacks and `caller` a page reads while a driver call runs, and names `mw:` code after the document rather than `debugger eval code` (`README.md:529`, `:534-536`, **Tier B** for the behaviour; patch files present). The commit message reports that hCaptcha's script probed `chrome://juggler/content/content/WorkerMain.js` with `new Worker()`, so any build that registered a `juggler` package could be told apart from stock Firefox (**Tier B**):

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

This is still the patch's only change (it diffs only `dom/base/Navigator.cpp`). Its former second hunk, which reverted Playwright's `new PlaywrightPoliciesProvider()` in `EnterprisePoliciesParent.sys.mjs`, was dropped when `658806e` removed that hunk (and the `chrome/juggler` packaging entries) from `0-playwright.patch` itself; the project now ships no `policies.json` at all (`browser/settings/distribution/policies.json` deleted; rule `no-enterprise-policies`, `ci/tribal-rules.yml:897`, which records that any policy file puts Firefox in visible enterprise mode, e.g. DNS over HTTPS stands down). A separate opt-in, `main_world_eval=True` (config key `allowMainWorld`), lets you run a script in the page's main world by prefixing it with `mw:` (e.g. `page.evaluate("mw:" + script)`) — otherwise Playwright scripts stay in the isolated world (`browser/additions/juggler/content/Runtime.js` refuses an `mw:` call unless the flag is set). Two further patches touch what content can observe: `debugger-invisible-to-content.patch` adds a Debugger flag so that attaching a Debugger does not cause content-visible side effects (extra stack capture, a disabled Promise return-value optimisation, wasm deoptimisation), and `window-setter-seal.patch` keeps the per-context `window.setXxx()` helpers off `window` once init scripts have run.

### fpgen Integration (default fingerprint synthesis)

When you don't supply values, the launcher fills them with **fpgen** ([scrapfly/fingerprint-generator](https://github.com/scrapfly/fingerprint-generator)), which the project README describes as "a model of real traffic" (`README.md:433-434`, **Tier B** for the distribution claim), and then runs the draw through a coherence check:

```python
# python/src/camoufox/fingerprints.py
_FP_GENERATOR = load_fpgen().Generator()   # built on first use (_generator(), lines 51-57)
fingerprint = _generator().generate(browser='Firefox', **conditions, **screen_conditions)   # generate_fingerprint(), line 1867
```

- The launcher drew from **BrowserForge** (`browserforge = "^1.2.4"`) until repo commit `6daae88` (2026-09-24); `python/pyproject.toml:37` declares `fpgen = "^1.3.0"`. PyPI 0.5.8 (`ac2ce31`) already declared `fpgen`; 0.5.6 (`eb5dc3b`) still declared `browserforge`. The TypeScript launcher depends on the published `fpgen-js` package, pinned at `1.3.0` (`typescript/package.json`).
- fpgen's model (tag `model-2/2026`) is installed from a release pinned by sha256 (`python/src/camoufox/fpgen-model.json`; `fpgen_model.py:123-130`) by `camoufox fetch` or on the first draw, in place of fpgen's own unpinned download. The pinned files are dated 2038-01-01 so that file systems with 32-bit timestamps keep the date and fpgen's refresh does not replace them (`fpgen_model.py:44`).
- With no `os` argument the OS is not picked by the launcher: `generate_fingerprint()` passes no OS condition and fpgen draws one from its model (`fingerprints.py:1857-1867`; `docs/HOST-PARITY.md:22-23`, "draws its OS from fpgen's mix"). The `launch_options` docstring still says `Default: ["windows", "macos", "linux"]` (`utils.py:1194-1197`). fpgen's OS weights were not read (fpgen is not in the sandbox; **Tier D**). A new `cpu` option (`utils.py:1292-1308`) narrows the OS to those with a recorded GPU for that CPU.
- `python/src/camoufox/coherence.py` (`validate()` / `apply()`) holds whole-identity rules — Apple-Silicon core counts, GPU vs OS, Intel-Mac GPU vs core count and screen, `colorDepth` in {24, 30}, `maxTouchPoints`, per-OS `devicePixelRatio` steps, window chrome, avail bounds, UA/platform architecture — and is applied to generated fingerprints, bundled presets and hand-written configs.
- fpgen supplies navigator, screen, window and headers; the GPU comes from fpgen's WebGL records, and fonts, speech voices and media devices are drawn from catalogues in the package (`fonts.json`, `voice-manifests.json`, `media-devices.json`) (`coherence.py:1-9`, module docstring).
- **GPU and canvas planning**: one function per launcher (`plan_rendering`, `python/src/camoufox/utils.py:930-953`; `planRendering` in TypeScript) decides the GPU. On the host's OS, with no GPU named, the identity claims what Firefox actually renders with, if fpgen has recorded it — including a software renderer: a host without a working GPU driver claims `llvmpipe` rather than a GPU name over software pixels (rule `cross-os-canvas-is-the-rfp-placeholder`, `ci/tribal-rules.yml:455-494`; `README.md:490-504`). `headless="virtual-gpu"` (new) runs a private Xorg display on a named GPU so a Linux server can claim it. When the identity claims another OS or another GPU (`webgl_config`, a preset's GPU, or a host GPU fpgen never recorded), canvas and WebGL readback are replaced by `privacy.resistFingerprinting`'s random placeholder (`canvas_noise`, `LeakWarning` at `utils.py:1855-1864`; see *Canvas* below). A `webgl_config` pair must be one fpgen recorded for Firefox on that OS, otherwise `ValueError` (`webgl_for_gpu`, `python/src/camoufox/webgl.py:225-236`). Spoofed avail-screen and touch values are claimed as Firefox's baseline fingerprinting protection reports them: the screen less 48 px on Windows, 76 px on macOS and nothing on Linux; more than one touch point becomes 5 (`follow_baseline_protection`, `fingerprints.py:897`; `ci/tribal-rules.yml:455-494`).
- **CPU vendor** (new, `21fdf1c` #1024, 2026-11-12): canvas readback and encoded Opus differ between Intel and AMD (the RCPPS/RSQRTPS estimate tables), and far more between x86-64 and ARM64 (Web Audio, composite operations, NaN signs, relaxed-SIMD wasm). `cpu-vendor-estimates.patch` makes the build compute as the claimed CPU, Intel, AMD or ARM64, emulating the other architecture's code paths in C (`ci/tribal-rules.yml:424-454`, rule `canvas-follows-the-claimed-cpu-vendor`). The launcher draws the CPU with the identity: from the GPU where only one vendor fits (Intel iGPU, Radeon APU, every x86 Mac, Apple GPU = ARM), otherwise x86 at 81.4% Intel, a figure taken from the Firefox Public Data Report (`utils.py:1292-1308`; `README.md:467`). The patch is 28,237 lines, mostly translated vector code.

### Real Fingerprint Presets (opt-in)

For evasion against consistency checks that generated identities can trip, Camoufox also ships bundles of **real** fingerprints scraped from in-the-wild Firefox traffic. `python/src/camoufox/fingerprint-presets-v150.json` holds **284 presets** — 168 Windows / 57 macOS / 59 Linux — with Firefox v149–v152 user agents (`min_firefox_version: 149`, `source: roverfox_fingerprints`); `fingerprint-presets.json` is an older bundle of 112 presets (71 / 24 / 17, Firefox 119–148 user agents). One macOS preset was removed from each bundle since `4559d01` (in the v150 bundle, an Intel Mac reporting "Radeon R9 200 Series, or similar"); the change predates the oldest commit in the sandbox's shallow (depth-50) clone, so its commit message was not read. `_select_presets_file()` (`fingerprints.py:1251-1265`) picks the v150 bundle for binaries at Firefox 149 or later, and `from_preset()` rewrites the UA's Firefox version to the active binary's (`fingerprints.py:1370-1373`). Opt in with `fingerprint_preset=True`; pass a preset dict instead of `True` to pin a specific identity. `ROADMAP.md` at `2f30fea` noted that presets naming GPUs with no recorded WebGL parameters (Windows on ARM/Adreno, Direct3D 10-level hardware, some Mesa and older Intel Linux drivers) were dropped; the file was deleted in `658806e`. A preset's GPU counts as a named GPU, so with the default `canvas_noise=None` a preset launch gets the canvas placeholder (see above).

---

## Properties of C++-Level Spoofing

### vs. JavaScript Injection (puppeteer-extra-stealth, etc.)

| Detection Method | JS Injection | Camoufox |
|-----------------|--------------|----------|
| `Object.getOwnPropertyDescriptor` check | ❌ Detectable | ✅ Native |
| `Function.toString()` returns `[native code]` | ❌ Often fails | ✅ Native (no JS wrapper) |
| Worker vs main context mismatch | ❌ Detectable | ✅ Worker getters are hooked as well (`WorkerNavigator.cpp`); main/worker mismatches have occurred as bugs and were fixed (e.g. GPC, #760) |
| Property access timing analysis | ❌ Delay | ✅ No JS wrapper call; per-context reads are memoised, and spoofed getters do stock's work before substituting so they are not faster than stock either (`zz-stock-cost-parity.patch`, see above) |

### vs. CDP-based Solutions (Playwright/Chrome, Puppeteer)

| Detection Method | CDP-based | Camoufox |
|-----------------|-----------|----------|
| `navigator.webdriver` | Patchable but leaky | ✅ C++ level false |
| `window.__playwright__` | ❌ Present | ✅ Isolated Juggler scope |
| `Runtime.enable` detection | ❌ Detectable | ✅ Uses Juggler, not CDP |

---

## Fingerprint Capabilities

Coverage is broad and applied natively. The patches map onto these areas (non-exhaustive; 65 top-level patch files):

| Category | Properties Spoofed | Patch(es) |
|----------|-------------------|-----------|
| **Navigator** | userAgent, platform, hardwareConcurrency, oscpu, appVersion (now also per context, `setNavigatorAppVersion`), language, globalPrivacyControl (window and workers), maxTouchPoints; `doNotTrack` is set as a pref by the launcher; a context's own User-Agent on worker and other context-less requests | `navigator-spoofing.patch`, `fingerprint-injection.patch`, `touchscreen-fingerprint-spoofing.patch`, `locale-spoofing.patch`, `per-context-http-user-agent.patch` |
| **Screen** | width, height, availLeft/Top/Width/Height, colorDepth, pixelDepth (the CSS `color` media feature follows `colorDepth`); under the launcher's Xvfb display the X screen itself reports the claimed screen when it is smaller | `screen-spoofing.patch`, `fingerprint-injection.patch`, `virtual-display-claimed-screen.patch` |
| **Window** | devicePixelRatio (zoom-scaled as in stock). `innerWidth`/`innerHeight`, `outerWidth`/`outerHeight` and `screenX`/`screenY` are **not** read from the config in any getter: the real window is sized and placed to the identity's values | `fingerprint-injection.patch`, `camoufox-window-module.patch` (`CamoufoxWindow.sys.mjs`), `window-position-wm-placement.patch` |
| **WebGL / WebGPU** | UNMASKED_VENDOR/RENDERER (after stock's fingerprinting-protection checks, as for `RENDERER`), parameter table, supported extensions, shader precision formats; `getContextAttributes()` and live state (e.g. `lineWidth`, viewport) come from the real context. Browser-owned values follow Firefox 159 (e.g. `EXT_texture_norm16` on WebGL2, `EXT_clip_control`, the 64 KiB `MAX_UNIFORM_BLOCK_SIZE` cap; WebGL1 reports WebGL2's value for every shared parameter) rather than fpgen's Firefox 146 recordings (rule `webgl-browser-owned-values-follow-firefox`, `ci/tribal-rules.yml:516-546`). On the host's OS the claimed GPU is the host's own, or `llvmpipe` on a software-rendering host. A display-less headless Linux launch renders WebGL on Mesa's software device rather than the first GPU EGL enumerates (`headless-software-webgl.patch`). `navigator.gpu` exists only where Firefox exposes it for the claimed device (Windows, Apple Silicon), and the adapter is the host's only when the identity claims the host's GPU; otherwise the `gfx.blacklist.webgpu` pref blocks it (`ci/tribal-rules.yml:495-515`) | `webgl-spoofing.patch`, `offscreen-webgl2-pref.patch`, `headless-software-webgl.patch`; WebGPU through launcher prefs (`host_rendering.py`) |
| **Audio** | sampleRate, output latency, max channel count. **No audio noise any more**: `audio-fingerprint-manager.patch`, its per-context setter and the `audio:seed` key are gone (key marked `removed` in `158.0-beta.41`, `browser/settings/properties.json:146`); the render is stock's, one value per CPU architecture, the same in every context and launch (rule `audio-is-not-noised`, `ci/tribal-rules.yml:396-422`, which records 106 stock runs giving one value per architecture). A caller passing `audio:seed` gets a `FutureWarning` and the key is dropped (`python/src/camoufox/fingerprints.py:149-157`) | `audio-context-spoofing.patch` |
| **CPU arithmetic** | canvas composite operations, encoded Opus, and on an x86-64/ARM64 mismatch also Web Audio, NaN signs and relaxed-SIMD wasm, computed as the claimed CPU (Intel, AMD or ARM64) computes them (new config keys `cpu:arch`, `cpu:manufacturer`) | `cpu-vendor-estimates.patch` |
| **Fonts** | per-context installed-font list, system-UI and CSS2 system fonts following the context's own claimed OS, per-context font-group plumbing; no glyph-spacing or metrics noise (rule `no-glyph-spacing-noise`, `ci/tribal-rules.yml:358`) | `font-list-spoofing.patch`, `font-hijacker.patch`, `system-ui-font-spoofing.patch`, `font-system-fonts-css2.patch`, `anti-font-fingerprinting.patch`, `fontfaceset-privileged-ready.patch` |
| **Canvas** | not noised when the identity claims the host's OS and GPU: pixels are what the GPU and fonts render, with stock's per-session PNG `deBG` chunk left on (`ci/tribal-rules.yml:373-395`, rule `canvas-is-not-noised`; no `canvas:seed`), but the arithmetic follows the claimed CPU vendor (row above). When the identity claims another OS or GPU, the launchers turn on Firefox's `privacy.resistFingerprinting` canvas targets through the baseline overrides, so canvas and WebGL readback return random placeholder data, as in LibreWolf, Tor Browser and Mullvad Browser; stock Firefox does not do this, and the launch emits a `LeakWarning` (`canvas_noise`, default `None` = on only in that case; `ci/tribal-rules.yml:455-494`, `python/src/camoufox/utils.py:1855-1864`). With no `os` argument fpgen draws the OS (see *fpgen Integration*), so whether a default launch claims the host's OS depends on fpgen's OS mix and the host | — |
| **Speech/Voices** | speechSynthesis voices (`speak()` on a spoofed voice starts and ends after the text's duration); new `voices:speechd` key | `speech-voices-spoofing.patch`, `voice-spoofing.patch` |
| **Media** | enumerateDevices output with labels and group ids (a fake media engine, so a claimed device captures), codec-support probes (`media:spoof_codecs`) | `media-device-spoofing.patch`, `media-codec-spoofing.patch` |
| **Network** | WebRTC ICE IP (protocol level; fabricated host candidates take a port in the claimed OS's ephemeral range); a srflx candidate comes only from a real STUN answer and is never invented (rule `no-made-up-srflx`, `ci/tribal-rules.yml:329-342`, #997); behind a SOCKS5 proxy, STUN/TURN/peer UDP goes through the proxy's UDP relay (UDP ASSOCIATE; `README.md:476`, **Tier B** for the end-to-end behaviour), and behind a proxy with no UDP path the page sees a machine whose UDP is blocked (host candidates only); Juggler records which contexts are proxied (`ci/tribal-rules.yml:344-356`); HTTP User-Agent + Accept-Language + Accept-Encoding; `network:ipv4Only`; the build's own User-Agent app name is set to `Firefox` (`MOZ_APP_UA_NAME`) | `webrtc-ip-spoofing.patch`, `webrtc-socks5-udp.patch`, `webrtc-proxy-local-network.patch`, `zz-webrtc-proxied-context.patch`, `network-patches.patch`, `user-agent-app-name.patch` |
| **Geo/Locale** | geolocation, timezone (per realm), locale (Intl; the OS/default locale only), browser UI strings through packaged language packs; `geoip=True` reads the GeoIP AIO database by default (GeoLite2 `deprecated: true`, `python/src/camoufox/repos.yml:48-73`) | `geolocation-spoofing.patch`, `timezone-spoofing.patch`, `locale-spoofing.patch` |
| **Host parity (Windows identity on a non-Windows host)** | `Math.sin/cos/tan/pow` computed with the Windows CRT's algorithms (`javascript.options.use_ucrt_math`); Windows shortcut tables and AltGr behaviour (`input:windowsKeyboard`); Windows behaviour prefs and scrollbars from the launcher. Browser-wide, not per context (`docs/HOST-PARITY.md`) | `windows-crt-math.patch`, `windows-keyboard.patch` |
| **DOM/behavior** | closed shadow-root piercing for automation, forced default pointer (any-pointer gains coarse only when `maxTouchPoints` > 0), optional instant CSS animations (`instantAnimations`, off by default), option-targeted events on `<select>` commits, mouse moves coalesced per frame like a 125 Hz mouse, `drag` events at the drag source, a pointer-lock crash fix for windows partly off-screen on X11, for a Windows identity, driven input events stamped on Windows' 15.625 ms tick (`MaskConfig::InputTimeStamp`, `browser/additions/camoucfg/MaskConfig.hpp:440-454`; `input-timestamp-tick.patch`, on `main` only, after `v159.0-beta.42`) | `shadow-root-bypass.patch`, `force-default-pointer.patch`, `no-css-animations.patch`, `trusted-automation-events.patch`, `input-coalescing-parity.patch`, `drag-source-events.patch`, `pointer-lock-offscreen.patch`, `input-timestamp-tick.patch` |
| **Background traffic** | Remote Settings collections come only from the build's pinned dumps; Push connects only once a page subscribes; Nimbus starts without Normandy; `about:studies` registered as in stock (rule `no-background-traffic`, `ci/tribal-rules.yml:911-930`) | `bundled-remote-settings.patch`, `push-connect-on-demand.patch`, `nimbus-without-normandy.patch`, `about-pages-parity.patch` |

WebRTC spoofing is a real protocol-level implementation (`WebRTCIPManager` plus hooks in `PeerConnectionImpl.cpp` for SDP, ICE candidates and `getStats()`, keyed per user context), not just a JS toggle — though you can also fully disable WebRTC with `block_webrtc=True`.

---

## What Changed Since the 2026-10-13 Analysis

`4c909d6` (2026-11-18/19) is 196 commits ahead of the previous pin `4559d01` with none behind (GitHub compare API); history was not rewritten. The sandbox clone is shallow (depth 50, oldest commit `10accea`, 2026-11-09), so the comparison below is a tree diff (`git diff 4559d01 4c909d6`: 522 files), and commits between the two pins older than `10accea` were not read individually. Browser releases since the previous pass (GitHub API): `v156.0.1-beta.39` (pre), `v158.0-beta.40` (pre), `v158.0.1-beta.41` (2026-10-29, the latest non-pre-release) and `v159.0-beta.42` (2026-11-15, pre, `340cf16`, also tagged library `v0.5.10b1`). PyPI 0.5.9 (2026-11-01) has no `v0.5.9` tag upstream.

- **Firefox 156.0.1 → 159.0** (`browser/upstream.sh`). WebGL browser-owned values updated for 159 (`EXT_texture_norm16` on WebGL2 including Windows, `EXT_clip_control`, `EXT_texture_mirror_clamp_to_edge`, the 64 KiB uniform-block cap; rule at `ci/tribal-rules.yml:516-546`).
- **Patch set 42 → 65** (64 at the `v159.0-beta.42` tag). Removed: `audio-fingerprint-manager` and `no-search-engines`. Added: `about-pages-parity`, `bundled-remote-settings`, `cpu-vendor-estimates`, `drag-source-events`, `fontfaceset-privileged-ready`, `headless-software-webgl`, `input-coalescing-parity`, `input-timestamp-tick` (after the tag), `isolated-world-global-order`, `nimbus-without-normandy`, `offscreen-webgl2-pref`, `per-context-http-user-agent`, `pointer-lock-offscreen`, `process-title-environ-leak`, `push-connect-on-demand`, `virtual-display-claimed-screen`, `virtual-display-off-root-not-occluded`, `webdriver-bidi-app-name`, `webrtc-proxy-local-network`, `webrtc-socks5-udp`, `window-position-wm-placement`, `windows-crt-math`, `windows-keyboard`, `zz-stock-cost-parity`, `zz-webrtc-proxied-context`. 51 of the 65 diff C/C++ sources.
- **Audio noise removed**: no per-identity audio seed; the render is stock's for the host (or claimed) CPU architecture (rule `audio-is-not-noised`, `ci/tribal-rules.yml:396-422`). The page previously listed "seeded per-context noise" as a capability.
- **CPU-vendor arithmetic** (`21fdf1c`, #1024): canvas and Opus follow a claimed Intel/AMD vendor, and an ARM64/x86-64 mismatch is emulated; new `cpu` launch option and `cpu:arch`/`cpu:manufacturer` keys.
- **Window geometry no longer spoofed in getters**: `innerWidth`/`innerHeight`/`screenX`/`screenY` now report the real (resized, repositioned) window; the window module holds the size through a late window-manager frame (`ce83ab8`, #973).
- **Getter timing parity**: `zz-stock-cost-parity.patch` makes spoofed getters do stock's work first, because early returns were measurably faster than stock.
- **WebRTC**: no fabricated srflx candidate (#997); WebRTC UDP over a SOCKS5 proxy's UDP relay; Juggler records which contexts are proxied.
- **Humanized input moved out of the browser** (`8b64b52`, #1000, 2026-11-19, **after** the `v159.0-beta.42` tag): `humanize=True` runs `myuri` 4.0.0 in the launcher process, per channel (mouse, keyboard, scroll), with replaceable parts; the browser sends one native event per Playwright call. The vendored cursory-js and `CursorTrajectory.js` are gone from `main`, and `humanize`, `humanize:minTime`, `humanize:maxTime` are marked `removed` (`browser/settings/properties.json:84-86`). `humanize` defaults to `None` (raw Playwright) (`python/src/camoufox/humanize.py:30-32`; `README.md:616-649`).
- **Host parity for Windows identities on other hosts**: Windows CRT math and keyboard tables (`docs/HOST-PARITY.md`).
- **Config keys**: 79 live and 65 marked `removed` (were 78 and 54). New: `network:ipv4Only`, `cpu:arch`, `cpu:manufacturer`, `voices:speechd`, `input:windowsKeyboard`. Newly `removed`: `audio:seed`, the three `humanize*` keys, five `humanize:*` keys added and retired in between, `cpu:vendor`, `webrtc:proxied`.
- **Debloat and background traffic**: no `policies.json` (enterprise mode was visible); stock search engines are back (the previous `no-search-engines` result differed from stock, rule at `ci/tribal-rules.yml:897-909`); Remote Settings from pinned dumps, Push on demand (`ci/tribal-rules.yml:911-930`); uBlock Origin bundled from a pinned release (`ci/tribal-rules.yml:274`).
- **Build and release**: builds use stock's PGO profile and LTO mode (rule `builds-are-optimized-like-stock`, `ci/tribal-rules.yml:1030`); twice-monthly release train (`ci/tribal-rules.yml:996`); `headless="virtual-gpu"`; Python `^3.11` on `main`.
- **Per-context proxy placement** (`c39c5dc`, #990): a proxied `NewContext()` now also takes geolocation and locale from the proxy's exit IP unless all four of `webrtc_ip`, `timezone_id`, `locale` and `geolocation` are given (`python/src/camoufox/async_api.py:252-268`).

Re-verified at `4c909d6`:

- **Exit-IP lookup** through the proxy to `ip-api.com` (`python/src/camoufox/ip.py:157-177`; a failed lookup raises `InvalidIP`); launch-level `geoip=True` derives location, timezone and locale.
- **`disable_coop`**, **`main_world_eval` with the `mw:` prefix** (`browser/additions/juggler/content/Runtime.js:56-94`), **`fonts` / `custom_fonts_only`**, `pin_cpu_cores`, `canvas_noise`, and the launch flags `block_images`, `block_webgl`, `screen`, `window`, `ff_version`, `virtual_display`, `enable_cache`, `exclude_addons`, `addons` (`python/src/camoufox/utils.py:1147-1186`).
- **14 `window.setXxx()` helpers** and their seal (`window-setter-seal.patch`; rule `fingerprint-setters-sealed-per-window`, `ci/tribal-rules.yml:655`): `setAudioFingerprintSeed` was dropped and `setNavigatorAppVersion` added, so the count is unchanged.
- **`navigator.webdriver`** is a flat `false` (`browser/patches/playwright/1-leak-fixes.patch`, its only change).
- **No TLS fingerprint code** anywhere in the browser or launcher trees.

---

## What Changed Since the 2026-09-30 Analysis

*(Paths and line numbers in this section are as of `4559d01`; the commit hashes predate the sandbox clone's depth-50 window.)*

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
| **Distribution-based draws** | fpgen model plus `coherence.py` rules (README, Tier B for the model's accuracy); or opt into 284 real fingerprint presets |
| **Per-context identities** | `NewContext()` gives each context a fresh fpgen-drawn (or preset) identity, plus per-context proxy, with timezone, locale, geolocation and WebRTC IP taken from the proxy's exit IP; setters sealed before page script runs. Without `canvas_noise`, contexts keep the host's OS and GPU |
| **Coverage** | Navigator, Screen, WebGL/WebGPU, audio device values, CPU-vendor arithmetic, Fonts, Voices, Media devices, WebRTC (including UDP through a SOCKS5 relay), geo/locale (canvas is not noised on the host's OS; random placeholder readback on another OS or GPU) |
| **No noise by design** | Canvas, audio render and text widths are left as stock renders them for the claimed hardware; the project's rules record that noise produces values no real machine produces (`ci/tribal-rules.yml:358-422`) |
| **Active development** | Tracks current Firefox (base 159.0); latest release 2026-11-15; last push 2026-11-19 |
| **Humanized input** | `humanize=True` drives Playwright through `myuri` in the launcher process on `main` (per-channel, replaceable parts, one seed for Python and TypeScript); release `v159.0-beta.42` still replays recorded Cursory movements in Juggler |
| **Debloated** | Telemetry and data reporting removed at compile time, onboarding disabled, Mozilla services and background traffic turned off in `camoufox.cfg` (`README.md:580-588`); no enterprise policy file. Stock search engines are kept (rule at `ci/tribal-rules.yml:897`) |
| **Open source** | Browser MPL-2.0, Python and TypeScript launchers MIT — patches are all readable in `browser/patches/`. Releases up to `v159.0-beta.42` also contain the vendored Cursory code (LGPLv3-or-later) |

### Disadvantages

| Con | Details |
|-----|---------|
| **Firefox only** | Cannot impersonate Chrome; Firefox is a small share of real traffic |
| **No TLS impersonation** | Sends genuine Firefox TLS (coherent, but can't be reshaped to Chrome JA3/JA4) |
| **SpiderMonkey detection** | Some WAFs treat Firefox engine more suspiciously |
| **Build complexity** | Building the browser from source needs a Linux host (Windows and macOS are cross-compiled; `AGENTS.md:142-143`, `README.md:716`), with stock's PGO profiles and LTO; the font bundle is a separate 843 MB download (`docs/FONTS.md:15-16`). Most users fetch the prebuilt binary. The previous "about 40 minutes for a cold build" figure is no longer in `AGENTS.md` |
| **No Windows ARM64 build** | `release.yml` excludes Windows arm64 (commented "Fails (.mozbuild does not include clang++-cl)", `.github/workflows/release.yml:220-222`) |
| **Release lag** | By design the newest browser build is a pre-release: each train run promotes the previous pre-release and cuts a new one (`ci/release.py:4-11`). The newest, `v159.0-beta.42`, predates the move of humanize into the launcher. PyPI's latest is 0.5.9 (2026-11-01), whose source commit is not identifiable in the clone; which browser build is currently marked stable was not checked (**Tier D**) |
| **Cross-OS canvas differs from stock** | An identity claiming another OS or GPU than the host's gets random canvas/WebGL readback, which stock Firefox does not produce (the launcher warns; `ci/tribal-rules.yml:455`) |
| **Host-OS rendering** | The project docs state that the per-context patches control what APIs report, not how the host OS renders: text rasterisation, GPU rasterisation, system colours and real shader precision still show the host (`docs/per-context-patches.md:217-234`, "Known limitations", Tier B); the same section recommends running each identity on the OS it claims, or `canvas_noise=True`. Host-parity settings for Windows identities are browser-wide, not per context (`docs/HOST-PARITY.md`) |
| **Server hosts read as servers** | A host with no working GPU driver claims `llvmpipe`, which the project itself rates "less stealthy" (`README.md:490-504`); `headless="virtual-gpu"` needs a real GPU |

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

(`typescript/README.md:7`, `:49-52`; install with `npm install camoufox playwright-core`; npm publication not verified.)

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

### With Proxy + Auto Geo/Timezone + Humanized Input

```python
with Camoufox(
    proxy={"server": "http://user:pass@proxy:8080"},
    geoip=True,        # derive lat/long/timezone/locale from the proxy's exit IP
    humanize=True,     # main: myuri in the driver on every channel; beta.42: recorded-movement replay in Juggler
    block_webrtc=True, # or leave it on and let webrtc-ip-spoofing use the proxy IP
) as browser:
    page = browser.new_page()
```

### Useful launch options (from `python/src/camoufox/utils.py`)

`os`, `cpu`, `block_images`, `block_webrtc`, `block_webgl`, `disable_coop`, `webgl_config`, `geoip` / `geoip_db`, `humanize` (on `main`: `True`, or a per-channel dict of `myuri(...)` / `raw()` plus `seed`), `locale`, `addons` / `exclude_addons` / `allow_addon_new_tab`, `fonts` / `custom_fonts_only`, `screen`, `window`, `fingerprint` / `fingerprint_preset`, `ff_version`, `headless` (also `"virtual"` for a private Xvfb display and `"virtual-gpu"` for a private Xorg display on a named GPU), `main_world_eval`, `enable_cache`, `virtual_display`, `pin_cpu_cores`, `canvas_noise`, `executable_path` / `browser` (mutually exclusive), `firefox_user_prefs`, `proxy` (`python/src/camoufox/utils.py:1147-1186`).

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
| `browser/patches/fingerprint-injection.patch` | C++ hooks for screen values, `devicePixelRatio` and the worker-side navigator getters (window size and position are not hooked) |
| `browser/patches/playwright/1-leak-fixes.patch` | `webdriver=false` (its only change) |
| `browser/patches/playwright/0-playwright.patch` | Juggler/Playwright integration |
| `browser/patches/webgl-spoofing.patch` | WebGL params, extensions, shader precision, UNMASKED_* |
| `browser/patches/webrtc-ip-spoofing.patch` | WebRTC IP replacement in SDP, ICE candidates and `getStats()`, per user context |
| `browser/patches/network-patches.patch` | HTTP User-Agent, Accept-Language and Accept-Encoding override; `network:ipv4Only` |
| `browser/patches/webrtc-socks5-udp.patch` | WebRTC UDP through a SOCKS5 proxy's UDP relay |
| `browser/patches/cpu-vendor-estimates.patch` | Canvas/Opus (and on an architecture mismatch, more) computed as the claimed CPU vendor |
| `browser/patches/zz-stock-cost-parity.patch` | Spoofed getters do stock's work first, so their cost matches stock |
| `browser/patches/audio-context-spoofing.patch` | AudioContext sample rate, output latency, channel count (no render noise; `audio-fingerprint-manager.patch` removed) |
| `browser/patches/shadow-root-bypass.patch` | Closed shadow-root piercing for automation |
| `browser/patches/window-setter-seal.patch` | Seals the per-context `window.setXxx()` helpers once init scripts have run |
| `browser/patches/cross-process-storage.patch` | `RoverfoxStorageManager`: per-user-context value store and cache |
| `browser/additions/browser/modules/CamoufoxWindow.sys.mjs` | Window sizing, positioning and startup work (replaces `browser-init.patch`) |
| `python/src/camoufox/humanize.py`, `_humanize_playwright.py` | Humanized input on `main`: per-channel `myuri()` / `raw()` run by the launcher (the Juggler `CursorTrajectory.js` and vendored cursory-js exist only up to release `v159.0-beta.42`) |
| `browser/additions/juggler/input/MouseDispatch.js` | The one chokepoint every synthesized input event goes through (rule `input-through-one-chokepoint`, `ci/tribal-rules.yml:678`) |
| `browser/additions/juggler/` | Full patched Juggler automation protocol (loaded from `resource://gre/modules/juggler/`) |
| `python/src/camoufox/fingerprints.py` | fpgen integration, preset routing, per-context init script |
| `python/src/camoufox/coherence.py` | Whole-identity coherence rules |
| `python/src/camoufox/fingerprint-presets-v150.json` | 284 real fingerprint presets (v149–v152); `fingerprint-presets.json` holds 112 older ones |
| `python/src/camoufox/async_api.py` / `sync_api.py` | Per-context identity (`NewContext`) and init-script helpers |
| `python/src/camoufox/utils.py`, `host_rendering.py` | Launch options; `plan_rendering` (host GPU vs canvas placeholder), WebGPU prefs |
| `browser/settings/properties.json` | Every declared config key and its type (79 live, plus 65 marked `removed` kept for older libraries) |
| `ci/tribal-rules.yml` | Settled design decisions with their evidence (e.g. no canvas or audio noise, CPU-vendor arithmetic, cross-OS canvas placeholder, no glyph-spacing noise, Juggler not a chrome package, release train) |
| `docs/HOST-PARITY.md` | What a Windows identity on a Linux host still leaked and how each was closed |
| `typescript/` | TypeScript/JavaScript launcher |
| `browser/upstream.sh` | Pins the upstream Firefox base version (currently 159.0) |

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

Camoufox is one of two tools of the ten that fork Firefox rather than Chromium (the other is invisible_playwright). Fingerprint values are substituted in C++ getters, so the substitution is not observable through JS property-descriptor or prototype inspection. Verified capabilities at the 2026-11-20 snapshot (`4c909d6`): Firefox 159.0 base, 65 patches in `browser/patches/` plus 2 Playwright/Juggler patches, fpgen-drawn identities with a coherence check, real-fingerprint presets, per-context identities with proxy-derived timezone, locale, geolocation and WebRTC IP, CPU-vendor arithmetic, Juggler loaded from `resource://gre`, and humanized input moved out of the browser into the launcher (`myuri`, after the latest release). The project has removed its last noise feature (audio): canvas, audio and text are left as stock renders them for the claimed hardware, and for an identity on another OS or GPU the launchers switch canvas and WebGL readback to Firefox's resistFingerprinting placeholder.

**Applicability constraint:** the engine is Firefox. Targets that treat Firefox differently from Chrome, or that probe SpiderMonkey engine behaviour (a residual signal the project documents), will identify the browser family regardless of fingerprint configuration.

**Limitation:** It is Firefox — small real-world share, and its genuine (unmodifiable) TLS fingerprint means you cannot masquerade as Chrome at the network layer.

---

*Analysis conducted for educational purposes. Facts verified against the cloned source tree and GitHub/PyPI release metadata as of 2026-11-20. Use responsibly.*
