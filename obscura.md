# Obscura - Deep Technical Analysis

> **Tool Type:** Custom Headless Browser Engine (built from scratch in Rust)
> **Repository:** [github.com/h4ckf0r0day/obscura](https://github.com/h4ckf0r0day/obscura)
> **Approach:** V8 runtime + html5ever DOM tree + JavaScript shim + native Rust layout/paint engine (v0.2.0) + optional TLS impersonation
> **Language:** Rust (CLI / engine / embeddable library), Puppeteer / Playwright clients (any language) via CDP, plus a built-in MCP server
> **Anti-bot service claims:** **none published** by the project (evidence **Tier D**). It makes no claims about Cloudflare, DataDome, Kasada, or any commercial WAF, and none were tested here. Its stealth documentation states the scope the other way round: it addresses checks on TLS fingerprint and User-Agent, and lists Cloudflare interactive challenges, DataDome and Akamai active challenges, and CAPTCHAs as **not** handled (**Tier B**, `docs/Configure-stealth-and-proxies.md`).
> **Maintenance:** latest release **v0.2.3** (2026-09-20), after v0.2.1 (2026-08-23) and v0.2.2 (2026-09-05); `main` is 66 commits (36 non-merge) past the v0.2.3 tag. Last push 2026-09-30; 28.2k stars, 2.1k forks, 69 contributors, 178 open issues. Apache-2.0 across the board.
> **Verified:** 2026-09-30 against `h4ckf0r0day/obscura` @ `a005d16`; `h4ckf0r0day/obscura-benchmark` @ `e4a5490` (Tier B figures only).

> ### ⚠️ This page was substantially wrong before 2026-08-14
>
> Previous revisions stated that Obscura "contains no layout engine, no CSS cascade,
> no compositor" and that `getBoundingClientRect` returned synthesized rects. **That
> was accurate for v0.1.x and is obsolete as of v0.2.0** (2026-08-08), which added a
> native Rust rendering engine (`crates/obscura-render`, ~66.8k LOC at v0.2.0, 69.9k at `a005d16`) covering block and
> inline layout, flexbox, grid, tables, floats, positioning, transforms, text shaping,
> images, canvas, gradients and shadows — plus screenshots and PDF export over CDP.
> The sections below have been corrected; see [CHANGELOG.md](CHANGELOG.md).
>
> **Second correction, 2026-09-30.** Re-reading the tree at `a005d16` showed that several statements that survived the first rewrite still described v0.1.x-era code: the WebGL shim (removed before v0.2.0), the canvas description, the `bootstrap.js` / op / MCP-tool counts and line numbers, the CDP domain count, and a release-CI `continue-on-error` note. Each is corrected inline below.

---

## Table of Contents

- [What is Obscura?](#what-is-obscura)
- [How It Works](#how-it-works)
- [Anti-Detection Mechanisms](#anti-detection-mechanisms)
- [Network Layer & Stealth Mode](#network-layer--stealth-mode)
- [CDP Implementation](#cdp-implementation)
- [MCP Server](#mcp-server)
- [Embeddable Rust Library](#embeddable-rust-library)
- [Performance](#performance)
- [Pros and Cons](#pros-and-cons)
- [Installation & Usage](#installation--usage)
- [Comparison with Alternatives](#comparison-with-alternatives)
- [When to Use](#when-to-use)

---

## What is Obscura?

Obscura is an **open-source headless browser engine written in Rust**, built specifically for web scraping and AI agent automation. It runs JavaScript via V8 (through the `deno_core` crate: `0.412` with V8 `150.4.0` in `Cargo.lock` at `a005d16`; `0.350` with V8 `137.3.0` at v0.2.0) and exposes a Chrome DevTools Protocol server so it can be driven by Puppeteer or Playwright clients. As of v0.1.7 it also ships as an **embeddable Rust library** (the `obscura` crate) and as a **built-in MCP server** (the `obscura mcp` subcommand) for AI-agent tool use.

**Key differentiator:** Unlike every other tool analyzed in this repository, Obscura is not a patched, forked, or wrapped version of Chrome or Firefox. It is a **from-scratch engine** that reimplements a subset of the browser surface in Rust: DOM, CSSOM and Web APIs, and, in render builds, layout and paint.

**The v0.2.0 shift (2026-08-08).** Obscura is no longer "a JS runtime bolted to an HTML tree." It now has a real layout and paint pipeline written in Rust. Verified in source (Tier A):

| Module | Lines | Role |
|--------|------:|------|
| `crates/obscura-render/src/dom.rs` | 21,602 | box tree, layout |
| `crates/obscura-render/src/paint.rs` | 17,949 | rasterization |
| `crates/obscura-render/src/style.rs` | 11,094 | computed style, cascade |
| `crates/obscura-render/src/css.rs` | 10,359 | CSS parsing, rule matching |
| `crates/obscura-render/src/inline.rs` | 5,459 | inline/text layout |
| other (`lib.rs` 2,931, `border.rs` 452, `bin/paint_file.rs` 20) | 3,403 | |
| **Total** (`wc -l`, `src/`, `a005d16`) | **69,866** | 66,826 at `f458a7f`; the earlier total included the "other" files without listing them |

In render builds `getComputedStyle` is served by the native op `op_computed_style` (`crates/obscura-js/src/ops.rs:7477`), whose doc comment describes a CSSOM snapshot plus a completeness flag: non-geometric reads can resolve only the ancestor cascade while layout work stays pending (`ops.rs:7473-7474`). It takes a pseudo-element and an optional single property as arguments. It is not the old synthesized defaults table. Element geometry comes from `op_layout_geometry` (`ops.rs:7239`), which calls `viewport_client_rects_with_scroll` (`crates/obscura-render/src/paint.rs:1917`). `Page.captureScreenshot`, `Page.printToPDF` and `Page.startScreencast`, previously hard-coded errors, are implemented.

**Important caveat — rendering is a build-time feature, not an unconditional one.**
In `crates/obscura-js/Cargo.toml` the feature set is `default = []`, with the comment
"Off by default so the scraping build stays lean." What you get depends on how you
obtained the binary:

| How you got it | Rendering |
|----------------|-----------|
| Release archive, no suffix (the default download) | **Yes** |
| Release archive `-stealth` | **Yes** (+ TLS impersonation) |
| Release archive `-no-render` / `-no-render-stealth` | No |
| Official Docker image | **Yes**, no stealth transport (`Dockerfile` builds `--features render` only) |
| `cargo build` from source without flags | **No** — needs `--features render` |

So a *download* exposes renderer-backed layout and style; a naive *source build*
does not. Any analysis of Obscura — including this one — has to say which build it
means. Where this page discusses layout behaviour, it means a render-enabled build.

What it still is not: a Chromium-equivalent. There is no GPU rasterization path; WebGL is unavailable (`getContext('webgl')` returns `null`, see [Canvas and WebGL](#canvas-and-webgl)) and audio is stubbed. The project's own figures put a no-render build at ≈30 MB resident and ≈85 ms page load (**Tier B**, not reproduced here; the benchmark repo labels its throughput results as the no-render profile). No such figures are published for the render-enabled default archive (**Tier D**).

---

## How It Works

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                       OBSCURA ARCHITECTURE                           │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────┐ │
│  │ obscura-cli  │  │ obscura-cdp  │  │ obscura-mcp  │  │ obscura  │ │
│  │ fetch/scrape │  │ WebSocket    │  │ MCP server   │  │ (crate)  │ │
│  │ /serve/mcp   │  │ CDP server   │  │ 37 tools     │  │ embed    │ │
│  │ + balancer   │  │ (14 domains) │  │ stdio/HTTP   │  │ Rust API │ │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └────┬─────┘ │
│         │                 │                 │               │       │
│         └─────────────────┴────────┬────────┴───────────────┘       │
│                                     ▼                                │
│  ┌──────────────────────────────────────────────┐                   │
│  │             obscura-browser (Page)            │                   │
│  │  Navigation + lifecycle + script orchestration│                   │
│  │  + request/response interception (v0.1.9)     │                   │
│  └────┬──────────────────┬──────────────┬───────┘                   │
│       │                  │              │                            │
│       ▼                  ▼              ▼                            │
│  ┌──────────┐    ┌──────────────┐  ┌──────────────┐                │
│  │ obscura- │    │ obscura-js   │  │ obscura-net  │                │
│  │ dom      │    │              │  │              │                │
│  │          │    │ V8 +         │  │ reqwest      │                │
│  │ html5    │    │ deno_core    │  │ (default)    │                │
│  │ ever     │    │ 0.412        │  │ + wreq       │                │
│  │ DOM      │    │ + 64 ops     │  │ (--features  │                │
│  │ tree     │    │ + 16,770-line│  │   stealth,   │                │
│  │ + CSS    │    │  bootstrap.js│  │   Chrome 145 │                │
│  │ selectors│    │  (DOM shim)  │  │   TLS)       │                │
│  └──────────┘    └──────────────┘  └──────────────┘                │
│                                                                      │
│  Supporting: 3,520-domain tracker blocklist (PGL list)              │
│              CookieJar, robots.txt cache, proxy support,            │
│              SSRF / DNS-rebind protection, V8 watchdogs             │
│  Optional (render feature): obscura-render (layout + paint)         │
│  Shared: obscura-ssrf (IP deny-set for net + renderer loader)       │
└─────────────────────────────────────────────────────────────────────┘
```

The repository is a Cargo workspace of **ten member crates** at `a005d16` (nine at v0.2.0; `obscura-ssrf` was added later), plus a non-member `crates/test-support/` helper. The earlier "eight crates" count left out `obscura-render`.

| Crate | Rust LOC (`src/`) | Responsibility |
|---|---:|---|
| `obscura-cli` | 3,004 | clap-based CLI (`fetch`, `scrape`, `serve`, `mcp`) + multi-worker TCP load balancer; also builds the `obscura-worker` binary |
| `obscura-cdp` | 15,117 | WebSocket server speaking the Chrome DevTools Protocol (14 domains), one OS thread per connection |
| `obscura-browser` | 11,405 | `Page` abstraction: navigation, subresource fetching, script execution, interception, persona profiles (`profiles.rs`) |
| `obscura-net` | 6,546 | HTTP client (reqwest baseline + optional `wreq` for TLS impersonation) + blocklist + cookies + robots.txt + interceptor |
| `obscura-js` | 32,217 Rust + 16,770 JS | V8 runtime via `deno_core` (64 registered ops: 43 always-on + 21 render-only) + `bootstrap.js` DOM/Web API shim |
| `obscura-dom` | 5,585 | html5ever-backed DOM tree + `selectors` crate for CSS queries |
| `obscura-render` | 69,866 | optional layout (`taffy`) and paint (`tiny-skia`, `cosmic-text`, `resvg`) layer, compiled in with the `render` feature |
| `obscura-mcp` | 3,259 | Model Context Protocol server (37 tools, 35 without `render`; stdio + HTTP transports) |
| `obscura-ssrf` | 139 | shared SSRF deny-set (`is_forbidden_ip`) used by `obscura-net` and the renderer's loader |
| `obscura` | 525 | Embeddable Rust library (`Browser::builder()...`) |

LOC is `wc -l` over `crates/<crate>/src/**/*.rs` at `a005d16`, including inline unit-test modules. The v0.1.x-era figures previously shown here (for example ~2,130 for `obscura-cli`, ~4,833 Rust + 7,878 JS for `obscura-js`) were already out of date at v0.2.0.

### Page Lifecycle

When `obscura fetch <url>` runs, the navigation path in `obscura-browser` executes roughly:

```
1. (optional) robots.txt           fetch and check if --obey-robots (crates/obscura-browser/src/page.rs:3373)
2. fetch                           validate_url() SSRF guard (obscura-net/src/client.rs:643): http/https/file only,
                                   private/loopback IPs refused; file:// also gated by allow_file_access (page.rs:3290);
                                   reqwest, or wreq in a stealth build run with --stealth
3. decode + parse_html()           charset from header, then <meta> sniff, then UTF-8; html5ever produces a DomTree
4. init V8 runtime                 load bootstrap.js (V8 snapshot); re-seed fingerprint
5. fetch <link rel=stylesheet>     bounded @import graph (page.rs:1881); installed into the DOM with
                                   append_external_stylesheet (page.rs:3515)
6. (render builds) resource warm-up  bounded image/font prefetch, OBSCURA_RENDER_RESOURCE_WARMUP_MS (default 1,000 ms)
7. classify + execute <script>     regular / defer / async / module; phase budget OBSCURA_SCRIPT_DEADLINE_MS (default 30 s)
8. DOMContentLoaded                iframe realms are built before the wait condition can return
9. (optional) network idle wait    networkidle0 / networkidle2 (500 ms idle window, 5 s cap)
10. dump HTML / text / markdown / links / assets / eval result
```

Two consequences of this pipeline are worth flagging:

- **External CSS is resolved (render builds, v0.2.0+).** `obscura-render` parses and cascades stylesheets — `css.rs` sorts matching rules by specificity and source order (`css.rs:8`, `:1559-1565`) and `style.rs` applies the cascade; linked stylesheets, `@import` graphs, web fonts and images are fetched through the page transport before layout. In a **`-no-render` build the old limitation still applies**: CSS is fetched but never resolved into computed style, so JS depending on external stylesheets sees nothing.
- **Layout is computed, not synthesized (render builds).** `getBoundingClientRect` is backed by real box geometry via `op_layout_geometry`, replacing the v0.1.x deterministic 12-column grid derived from node id. In non-render builds the synthesized grid remains — it exists so Playwright actionability polling and virtualization libraries don't stall (`bootstrap.js:5173-5226`; the comment at `:5203` cites issue #45).

### V8 Snapshotting

`obscura-js` builds a V8 startup snapshot at compile time (`crates/obscura-js/build.rs`, which embeds `js/bootstrap.js` with `include_str!("js/bootstrap.js")` at `build.rs:16`; cross-compiles use the target's `mksnapshot`), so the bootstrap script is not re-evaluated for every page. `__obscura_init()` (`bootstrap.js:16070`) runs on each new runtime instance. The release workflow smoke-tests every archive variant with `obscura fetch data:... --eval "1+1"` and checks that screenshots work only in the render variants, so a mismatched snapshot is not published (issue #290). Containment of runaway pages: `arm_watchdog` (`runtime.rs:3437`), a per-command CDP watchdog (`cdp_watchdog.rs:94`, budget `OBSCURA_CDP_COMMAND_TIMEOUT_MS`) and a V8 near-heap-limit guard (`runtime.rs:157`). DOM ops are wrapped in `catch_unwind` (`ops.rs:1527`, commented as an anti-panic boundary) so an op panic degrades to a null result instead of unwinding into V8's FFI frame, and `Cargo.toml:72-73` sets `panic = "unwind"` for the release profile so that boundary can work.

---

## Anti-Detection Mechanisms

The fingerprint surface is implemented mostly in `crates/obscura-js/js/bootstrap.js` (16,770 lines at `a005d16`). There are no C++ or binary-level patches: the overrides are JavaScript executed before any page script runs. Persona selection lives in `crates/obscura-browser/src/profiles.rs`, HTTP client hints and TLS in `obscura-net`, and the timezone in the process `TZ` set by the CLI (`crates/obscura-cli/src/main.rs:360-373`). Since v0.1.0 the fields a profile carries (UA, platform, UA-CH) are **internally coherent per platform profile** rather than a fixed Linux persona with mismatched sub-fields.

### `navigator` overrides

```javascript
// bootstrap.js:7255 (object literal) and :7352-7406 (thin-prototype getters)
globalThis.navigator = {
  onLine: true, cookieEnabled: true, maxTouchPoints: 0,
  vendor: "Google Inc.", product: "Gecko", productSub: "20030107",
  doNotTrack: null, connection: new NetworkInformation(), pdfViewerEnabled: true,
  userAgentData: {
    mobile: false,
    get brands() { return _uaBrands(); },   // GREASE brand + order derived from the Chrome major
    get platform() { return globalThis.__obscura_ua_platform || "Windows"; },
    getHighEntropyValues(hints) { return Promise.resolve({
      architecture: "x86", bitness: "64", wow64: false, model: "", mobile: false,
      platform: globalThis.__obscura_ua_platform || "Windows",
      platformVersion: globalThis.__obscura_ua_platform_version || "15.0.0",
      /* brands, fullVersionList, uaFullVersion */ }); },
  },
  // ... mediaDevices, getBattery, serviceWorker, permissions, geolocation, storage, etc.
};
// Spoofed properties are getters on a thin prototype above Navigator.prototype (defGetter):
//   webdriver -> false, userAgent / appVersion (fallback Chrome/145, Windows), platform ("Win32"),
//   language / languages (from __obscura_language), plugins / mimeTypes,
//   hardwareConcurrency (__obscura_hw || 8), deviceMemory (__obscura_mem || 8)
```

What it covers:
- `navigator.webdriver` is a getter on a **thin prototype** (`bootstrap.js:7361`), so `Object.getOwnPropertyDescriptor(navigator, 'webdriver')` returns `undefined` (as in real Chrome) rather than exposing an own property. The getter returns `false`; the README's "`navigator.webdriver = undefined`" describes the descriptor, not the value (**Tier B** vs **Tier A**).
- Full `navigator.userAgentData` with a `getHighEntropyValues` payload whose `platform` / `platformVersion` come from the same page globals that set the UA string and `navigator.platform`.
- `userAgentData.brands` and its order are derived deterministically from the Chrome major version in the UA by a port of Chromium's GREASE algorithm (`_uaBrands`, `bootstrap.js:7238`, helper `_chromeMajor` `:7226`); they are not permuted per session seed.
- Plugin and mimeType lists (5 plugins, 2 mimeTypes), `connection` (NetworkInformation), faked `getBattery` with per-session values.

What is now **coherent** (previously flagged as tells, now fixed):
- **The default persona is Windows, not Linux**: `navigator.platform` `Win32`, UA-CH `platform` `Windows`. The Chrome version depends on the build. An ordinary build uses `PROFILES[0]`: Chrome 143, `platformVersion` `10.0.0` (`profiles.rs:8-14`, `select_profile` `:76-91`). A build with the `stealth` feature run with `--stealth` fixes Chrome 145, `Win32`, `Windows`, `15.0.0` (`page.rs:1783-1790`, constants at `wreq_client.rs:61-73`); a test asserts both user agents (`crates/obscura/tests/stealth_transport.rs:9-12,71-74`). The `bootstrap.js` fallbacks (Chrome 145, `15.0.0`) apply only when the host sets no UA. The Rust list has 8 profiles, Chrome 143–146 on Windows and on macOS; none is Linux.
- `hardwareConcurrency` and `deviceMemory` are **re-randomized per runtime** in `__obscura_init` (`bootstrap.js:16115-16118`): `[4,6,8,12,16]` and `[4,8]` when the stealth feature is active, `[2,4,6,8,12,16]` and `[0.25,0.5,1,2,4,8]` otherwise; not static `8`.
- Platform, UA and UA-CH track a single chosen profile (Windows / macOS). The timezone is not part of the profile: it comes from the process `TZ` (default `Europe/Berlin`; `OBSCURA_TIMEZONE` changes it). See "Per-session fingerprint" below.

What may still be detectable:
- The plugin list includes a `"WebKit built-in PDF"` entry (5 plugins total, `bootstrap.js:7383-7388`), which does not appear in real Chrome's plugin set.
- `Function.prototype.toString` itself is marked native (the masking function reporting as native) — a detector comparing the masking chain can still observe the override in principle.
- Fingerprint pools are finite (8 screens, 2 audio sample rates, 5–6 hardware-concurrency values), so a detector aggregating values across many requests from one source can still recognize the distribution.

### `Function.prototype.toString` masking

```javascript
// bootstrap.js:161-182
const _nativeFns = new Set();
const _nativeStr = new Map();   // exact strings for accessors, via _markNativeAs
const _origToString = Function.prototype.toString;
const _functionToString = {     // method syntax: no own `prototype`, like a native function
  toString() {
    if (_nativeStr.has(this)) { return _nativeStr.get(this); }
    if (_nativeFns.has(this)) { return `function ${this.name || ''}() { [native code] }`; }
    return _origToString.call(this);
  },
}.toString;
Function.prototype.toString = _functionToString;
function _markNative(fn) { if (typeof fn === 'function') _nativeFns.add(fn); return fn; }
_nativeFns.add(_functionToString);
```

More than 110 call sites mark functions native via `_markNative(...)` (114 at `f458a7f`, 117 at `a005d16`, counted by occurrence; the earlier "~96" used a different count). Accessors that need an exact native string use `_markNativeAs`. This handles the common `Function.prototype.toString().includes('[native code]')` check, including on `toDataURL`, media element methods and `getComputedStyle`. Engine-internal globals are additionally filtered out of `Object.getOwnPropertyNames` / `Reflect.ownKeys` results on the global object (`_hideInternalsFromReflection`, `bootstrap.js:193`).

### Per-session fingerprint

```javascript
// bootstrap.js:673-741  (_getFp)
const _uaPlat = globalThis.__obscura_ua_platform || 'Windows';
const isMac = _uaPlat === 'macOS';
const isLinux = _uaPlat === 'Linux';
const gpuPool = isMac ? [ /* 6 x ANGLE Metal Renderer (Apple M1..M3, Intel Iris Plus) */ ]
             : isLinux ? [ /* 7 x ANGLE ... Mesa ... OpenGL 4.6 */ ]
             :           [ /* 12 x ANGLE ... Direct3D11 vs_5_0 ps_5_0, D3D11 */ ];
const idx = Math.floor(_fpRand(42) * gpuPool.length);
const screenPool = [[1920,1080],[2560,1440],[1366,768],[1536,864],[1440,900],[1680,1050],[1280,720],[3840,2160]];
_fpCache = {
  gpu: gpuPool[idx], gpuVendor: gpuVendorPool[idx],   // assigned; no reader found at a005d16
  audioBaseLatency, audioSampleRate: [44100, 48000][...], compThreshold, compKnee, compRatio,
  batteryLevel, batteryCharging, screen: screenPool[...],
  canvasFingerprint: cfp,                             // assigned; no reader found at a005d16
};
```

The platform-matched GPU pools (Windows → ANGLE Direct3D11, macOS → ANGLE Metal, Linux → ANGLE/Mesa OpenGL) still exist, but nothing reads the `gpu`, `gpuVendor` or `canvasFingerprint` fields: the only `_fp(...)` readers in `bootstrap.js` at `a005d16` are `screen` (`:7485`, `:16093`), `batteryCharging` / `batteryLevel` (`:7306`) and the `audio*` / `comp*` fields (`:14136-14141`). Upstream's own docs dropped the "WebGL/GPU renderer internally consistent" sentence for this reason (commit `d415fe6`, 2026-08-26). The README still lists GPU among the per-session randomized values (**Tier B**). `__obscura_init` (`bootstrap.js:16070`) re-seeds `_fpSeed = Date.now() ^ (Math.random()*0xFFFFFFFF >>> 0)` (`:16075`) for each new runtime, and `Page::init_js` creates a new runtime for every navigation (`page.rs:1745`).

Profile selection is controllable:
- `OBSCURA_PROFILE=<n>` pins a specific index of the 8-entry Rust `PROFILES` list (`profiles.rs:76-91`).
- `OBSCURA_ROTATE_PROFILE=1` picks a random profile per browser context.
- Default is `PROFILES[0]` (rotation is opt-in because one IP cycling identities is itself a signal; the code comment adds that a rotated profile does not yet carry a matching TLS or timezone fingerprint).
- A build with the `stealth` feature run with `--stealth` ignores the pool and uses the fixed Chrome 145 / Windows identity (`page.rs:1783-1790`).

### Canvas and WebGL

**WebGL is unavailable.** `HTMLCanvasElement.prototype.getContext` returns `null` for `'webgl'`, `'experimental-webgl'` and `'webgl2'` (`bootstrap.js:14009-14026`). The code comment says failing is the only truthful behaviour until the renderer has a real WebGL backend, because the former shim reported successful shader and program creation while every draw call was a no-op. A unit test asserts it (`runtime.rs:14593`), and `WebGLRenderingContext` / `WebGL2RenderingContext` exist as empty classes (`bootstrap.js:7443-7444`). A page therefore cannot read `UNMASKED_VENDOR_WEBGL` / `UNMASKED_RENDERER_WEBGL` or read back GL pixels, and a page that treats missing WebGL as a signal sees it. The WebGL shim with `getParameter` and random `readPixels` output that earlier revisions of this page described was already removed at v0.2.0 (it was still present at v0.1.11).

**Canvas 2D is a JavaScript software rasterizer.**

```javascript
// bootstrap.js:14027-14034
HTMLCanvasElement.prototype.toDataURL = function(type) {
  const ctx = this._ctx || this.getContext('2d');
  if (ctx && ctx._buf) {
    if (ctx._w === 0 || ctx._h === 0) return 'data:,';
    return _encodePNG(ctx._w, ctx._h, ctx._buf);
  }
  return 'data:,';
};
```

`getContext('2d')` returns `_Canvas2D` (`bootstrap.js:13597`), which draws into an RGBA `Uint8ClampedArray`: `fillRect`, `strokeRect`, `clearRect`, `drawImage`, `getImageData` / `putImageData`, linear and radial gradients and, since commit `98d779b` (2026-09-19), `stroke()`. `toDataURL` and `toBlob` encode that buffer as a valid PNG with uncompressed (stored) DEFLATE blocks (`_encodePNG`, `bootstrap.js:13527`); the `type` argument is ignored, so the output is always PNG. `translate`, `rotate`, `scale`, `setTransform`, `clip`, `bezierCurveTo`, `quadraticCurveTo` and `arcTo` are no-ops. **`fillText` does not rasterize fonts** (`bootstrap.js:13719`): each character is drawn as a 5×7 dot pattern derived from `_fpRand(<char code> ...)`, so text drawn to a canvas depends on the per-session seed and matches no real font. In render builds each canvas is registered with the renderer as a surface (`op_canvas_register_surface`, `op_canvas_paint_damage`) so it appears in screenshots. A script that hashes canvas output therefore receives a valid PNG whose pixels are a per-session synthetic result rather than the output of a real text stack; one that decodes it does not get a non-image, as earlier revisions of this page stated.

### Audio

Audio context, compressor parameters and analyser data are synthetic values derived from `_fpSeed` (`AudioContext` at `bootstrap.js:14135`; the sample rate is drawn from `[44100, 48000]`). Oscillator, gain, filter and buffer-source nodes are inert objects, so no DSP graph runs. `OfflineAudioContext.startRendering` (`bootstrap.js:14170`) does not process a graph either: it synthesizes a 10 kHz triangle wave and scales it so that the sum of absolute values over samples 4500–4999 equals 124.04347527516074 plus a seed-derived jitter of at most 0.001; the code comment says the target is the value measured on Chrome for Linux. A fingerprinter that hashes a rendered buffer therefore receives a buffer whose checked sum is pinned to that reference rather than the result of a real signal chain.

### `event.isTrusted` (now correct)

```javascript
// bootstrap.js:10353-10354, 10415-10417
const _trustedEvents = new WeakSet();
globalThis.__obscura_markTrusted = function(ev) { try { if (ev) _trustedEvents.add(ev); } catch (_e) {} return ev; };
globalThis.Event = class Event {
  ...
  get isTrusted() { return _trustedEvents.has(this); }
};
```

This is a **fix** relative to the previous analysis. Page-created events (`new Event(...)`, `new MouseEvent(...)`) now report `isTrusted === false`, per spec, because only events Obscura's CDP input pipeline dispatches are added to the closure-private `_trustedEvents` WeakSet (via the non-enumerable `__obscura_markTrusted`). The old "always `true`" tell is gone.

### Mouse and keyboard input (now hit-tested)

```javascript
// crates/obscura-cdp/src/domains/input.rs:138-345 (mousePressed excerpt from :184)
"dispatchMouseEvent" => {
  // mousePressed:
  var target = (document.elementFromPoint && document.elementFromPoint(x,y))
            || globalThis.__obscura_click_target
            || document.activeElement || document.body;
  globalThis.__obscura_click_target = target;
  // dispatch trusted MouseEvent on target
}
```

Also a **fix**: dispatched mouse coordinates are resolved through `document.elementFromPoint(x, y)` first, so `elementFromPoint` recurses into the tree properly. Coordinate-driven clicks (not just selector-driven `page.click('selector')`) hit the intended element. The v0.1.x "coordinates are ignored, target is always `__obscura_click_target`" limitation no longer holds. In a render build, hit-testing now runs against real measured boxes rather than the synthesized grid. `mouseMoved` hit-tests the same way and dispatches `mouseover` / `mouseenter` / `mouseout` transitions, presses dispatch pointer and mouse events, and wheel events are dispatched too (`input.rs:138-350`); `dispatchTouchEvent` and `setIgnoreInputEvents` return an empty result without dispatching anything (`input.rs:500-501`).

### `getComputedStyle` — renderer-backed in v0.2.0

In a **render build**, `getComputedStyle` is served by a native op:

```rust
// crates/obscura-js/src/ops.rs:7473-7482 (doc comment paraphrased: CSSOM snapshot plus a
// completeness flag; non-geometric reads may resolve only the ancestor cascade)
#[cfg(feature = "render")]
#[op2]
#[string]
fn op_computed_style(
    state: &OpState,
    #[string] nid_str: String,
    #[string] pseudo: String,
    #[string] property: String,
) -> String {
```

Values come from the actual cascade and layout, so the v0.1.x tells are gone: no
defaults table, no rect-derived dimensions, no `font-family: 'Times'` giveaway.

In a **non-render build** the old JS-synthesized implementation is still what runs —
inline style, then dimensions from the bounding rect, then a defaults table (`bootstrap.js:8832-8940`) — with all
the detectability that implies. This is the single biggest behavioural difference
between the two builds and the main reason to check which one you are shipping. In render builds `innerText` also returns the rendered text (`bootstrap.js:3631-3636`, commit `55e76f0`).

---

## Network Layer & Stealth Mode

Obscura has **two independent stealth levers** that are easy to conflate:

1. The **runtime `--stealth` flag** (global; applies to `fetch`, `serve`, `scrape`, `mcp`). Tracker blocking is switched on in any build (`crates/obscura-browser/src/context.rs:107-109`). The wreq transport and the JS-level stealth identity (fixed Chrome 145 / Windows persona, narrower hardware pools) only take effect in a binary compiled with the `stealth` feature (`page.rs:1782-1790`); the project's docs say the flag requires a build that includes it (`docs/Configure-stealth-and-proxies.md`, **Tier B**).
2. The **`stealth` build feature** (`cargo build --features stealth`, or a `-stealth` / `-no-render-stealth` release archive). It compiles in `wreq` so the HTTP client can impersonate Chrome's TLS ClientHello. Without this feature the binary falls back to `reqwest`/rustls.

### Default HTTP client (`reqwest`)

The baseline client is `reqwest` with rustls, gzip/brotli/deflate, and SOCKS support. Chrome-shaped headers are added manually; `sec-ch-ua` and `sec-ch-ua-platform` are derived from the current UA string, so they follow the selected profile:

```rust
// crates/obscura-net/src/client.rs:1445-1466 (remaining headers to :1496)
let ua = self.user_agent.read().await.clone();
let (sec_ch_ua, sec_ch_ua_platform) = chrome_client_hints(&ua);   // derived from the UA string (:995)
headers.insert("sec-ch-ua", sec_ch_ua);                           // fallback literal: Chrome 145
headers.insert("sec-ch-ua-mobile", "?0");
headers.insert("sec-ch-ua-platform", sec_ch_ua_platform);         // fallback literal: "Windows"
headers.insert("upgrade-insecure-requests", "1");                 // navigations only
headers.insert(USER_AGENT, ua);
// then accept, sec-fetch-site / -mode / -user / -dest, referer, origin, accept-language, cookie
```

The headers look like Chrome, but without the stealth feature the TLS handshake is whatever rustls produces, so JA3 / JA4 will match a Rust HTTP client, not Chrome.

### `--features stealth` build (`wreq`)

```rust
// crates/obscura-net/src/wreq_client.rs:207-210
let emulation_opts = wreq_util::Emulation::builder()
    .profile(wreq_util::Profile::Chrome145)
    .platform(wreq_util::Platform::Windows)
    .build();
```

`wreq` is a TLS-impersonation library (BoringSSL-backed, similar in spirit to `curl_cffi`). With the feature enabled the client is configured with wreq-util's **Chrome 145 / Windows** emulation profile, which is intended to reproduce Chrome's JA3 / JA4, ALPN and cipher order (the wire output was not captured in this review; **Tier B**). The profile is hardcoded — no rotation, no per-session variation, and no alternative emulation targets. The `wreq` / `wreq-util` deps are pinned to exact pre-release RCs (`wreq =6.0.0-rc.29`, `wreq-util =3.0.0-rc.12`) because their API churns between RCs (issue #234), and `prefix-symbols` is enabled only on Linux/Android to avoid BoringSSL/OpenSSL symbol clashes (issue #39).

**Release binaries:** the release workflow builds four variants per target on native runners (`.github/workflows/release.yml:80-122`): `default` (`--features render`), `stealth` (`--features render,stealth`), `no-render` and `no-render-stealth`, packaged as `obscura-<target>.tar.gz`, `-stealth`, `-no-render` and `-no-render-stealth` (`.zip` on Windows). **Only the `-stealth` and `-no-render-stealth` archives contain the wreq transport**; the unsuffixed archive and the Docker image (built with `--features render`) do not. No build step is marked `continue-on-error` at v0.2.0 or later, so a failed stealth compile fails the release job instead of silently shipping the default client; earlier revisions of this page described a `continue-on-error: true` fallback that is not in the tree. The smoke-test step runs `fetch data:... --eval 1+1` on all four variants.

### Tracker blocking

```rust
// crates/obscura-net/src/blocklist.rs
const PGL_LIST: &str = include_str!("pgl_domains.txt");  // 3,520 domains
// test asserts blocklist().len() > 3500
```

Peter Lowe's tracker domain list (**3,520 domains**, unchanged) is embedded at compile time. Lookup is exact plus suffix match. Blocked domains are never fetched — privacy hygiene that also speeds loads and prevents third-party fingerprinting scripts from running, but it does not itself disguise the client. `OBSCURA_BLOCK_TRACKERS=0` turns blocking off in the stealth client (`wreq_client.rs:268`, `:657`; commit `9ced496`).

### Request/response interception (new in v0.1.9)

The `obscura-net` interceptor and `obscura-browser`'s `InterceptedRequest` / `InterceptResolution` expose callbacks to observe, block, modify headers on, or fulfill requests from Rust (embeddable API) and via CDP `Fetch`. As of `a005d16`, JS-initiated requests (both `fetch()` and XHR) are reported with resource type `Fetch` (`crates/obscura-js/src/ops.rs:3297`, `:3664`, `:3953`), although the `ResourceType` enum has an `Xhr` variant (`crates/obscura-net/src/client.rs:150-159`).

---

## CDP Implementation

`obscura-cdp` implements a subset of the Chrome DevTools Protocol sufficient to support Puppeteer and Playwright clients connecting via `connectOverCDP` / `puppeteer.connect`. It implements **14 domains** (`crates/obscura-cdp/src/dispatch.rs:793-811`; the page previously listed 12 and omitted `IO` and `Emulation`) and accepts 11 further domains as no-ops (`Log`, `Performance`, `Security`, `CSS`, `ServiceWorker`, `Inspector`, `Debugger`, `Profiler`, `HeapProfiler`, `Overlay`, `Audits`; `dispatch.rs:814-815`) so that Puppeteer's connect handshake does not fail:

| Domain | Implemented (selected) | Notable Gaps |
|---|---|---|
| Target | getTargets, createTarget, closeTarget, attachToTarget, attachToBrowserTarget, setAutoAttach, createBrowserContext, disposeBrowserContext, getTargetInfo | no `targetCrashed` event |
| Browser | getVersion, close, getWindowForTarget, getWindowBounds / setWindowBounds, setDownloadBehavior, grantPermissions, resetPermissions | `getVersion` reports a Linux user agent (Chrome 145) regardless of persona (`domains/browser.rs:7-9`) |
| Page | navigate, reload, getFrameTree, createIsolatedWorld, getLayoutMetrics, getNavigationHistory, navigateToHistoryEntry, addScriptToEvaluateOnNewDocument, lifecycle events, captureScreenshot, printToPDF, startScreencast / stopScreencast / screencastFrameAck | screenshot, PDF and screencast need a render build; `fromSurface=false` unsupported |
| Runtime | enable, disable, evaluate, callFunctionOn, getProperties, addBinding, removeBinding, releaseObject, getExceptionDetails | `Debugger` is accepted as a no-op |
| DOM | getDocument, querySelector, querySelectorAll, getOuterHTML, describeNode, resolveNode, setAttributeValue, removeNode, focus, scrollIntoViewIfNeeded, setFileInputFiles, getBoxModel, getContentQuads | content / padding / border / margin quads in getBoxModel are all one `getBoundingClientRect` quad (`dom.rs:296-345`); real geometry only in render builds |
| DOMSnapshot | enable, disable, captureSnapshot | geometry and styles are synthesized in every build (`domsnapshot.rs:1-20`) |
| Accessibility | enable, getFullAXTree (roles / names) | — |
| Network | enable, disable, setCookie / setCookies, getCookies, getAllCookies, deleteCookies, clearBrowserCookies, setExtraHTTPHeaders, setUserAgentOverride, setCacheDisabled, setRequestInterception, setBlockedURLs, getResponseBody | no WebSocket frame events |
| Fetch | enable, disable, continueRequest, fulfillRequest, failRequest, getResponseBody, takeResponseBodyAsStream | — |
| IO | read, close | — |
| Storage | getCookies, setCookies, clearCookies, deleteCookies | no IndexedDB or storage events (cookie methods only) |
| Input | dispatchMouseEvent (hit-tested), dispatchKeyEvent, insertText | dispatchTouchEvent and setIgnoreInputEvents are empty stubs (`input.rs:500-501`) |
| Emulation | setDeviceMetricsOverride, clearDeviceMetricsOverride, setDefaultBackgroundColorOverride, setUserAgentOverride, setLocaleOverride, setTouchEmulationEnabled | — |
| LP | getMarkdown (DOM-to-Markdown, custom domain) | — |

`Page.printToPDF` and `Page.captureScreenshot` are **implemented as of v0.2.0** in render builds — viewport, clipped, scrolled and full-page capture with PNG/JPEG/WebP output, plus paginated PDF export with paper sizes, margins, scale and page ranges. Screencasting is supported with acknowledgement backpressure. In a non-render build these still return an explanatory error (`domains/page.rs:1847`; `"Page.{method} is not supported by Obscura: no layout or paint engine"`), and `fromSurface=false` is unsupported in every build (`domains/page.rs:1722`) since there is no separate browser-window compositor surface. The main frame's `frameId` equals its `targetId` (`crates/obscura-browser/src/page.rs:1080`, for Playwright compatibility); child iframe frames are reported as `<frameId>-frame-<n>` (`domains/page.rs:18-19`). Each CDP command has a deadline (`OBSCURA_CDP_COMMAND_TIMEOUT_MS`, `dispatch.rs:763-780`) so one wedged page cannot stall other sessions, and each CDP connection runs on its own OS thread with its own Tokio runtime and `LocalSet` (`server.rs:761-800`), up to 128 connections by default (`DEFAULT_MAX_CONNECTIONS`, `server.rs:44`). A non-loopback bind is refused unless `OBSCURA_CDP_TOKEN` (at least 32 bytes) is set (`server.rs:58-62`, `:359`). Counting the string match arms in the 14 domain handlers gives 111 distinct method names at `a005d16` and 105 at `f458a7f`; the earlier "~244 method-handler arms" figure could not be reproduced. New since `f458a7f`: `Browser.grantPermissions` / `resetPermissions`, `Runtime.disable`, `Input.insertText`, `Emulation.setUserAgentOverride` / `setLocaleOverride`.

---

## MCP Server

New since v0.1.4 and expanded through v0.1.9: `obscura mcp` runs a Model Context Protocol server so an AI agent (Claude, Cursor, etc.) can drive the browser as a tool. It defines **37 tools** in `handle_tools_list` (`crates/obscura-mcp/src/lib.rs:318`); `browser_screenshot` and `browser_pdf` are listed only in render builds (`lib.rs:696-712`), so a no-render build exposes 35. Examples: `browser_navigate`, `browser_snapshot`, `browser_click`, `browser_fill_form`, `browser_extract`, `browser_tab_new`, `browser_tab_switch`, `browser_storage_state`. It supports **multiple tabs / isolated pages** and offers both **stdio and HTTP transports** (`obscura mcp` / `obscura mcp --http --host <addr> --port <n>`; defaults 127.0.0.1:3000, `main.rs:194-210`). A non-loopback HTTP bind is refused unless `OBSCURA_MCP_TOKEN` (at least 32 bytes) is set (`crates/obscura-mcp/src/http.rs:61-65`, `:281`), and browser requests are refused unless their `Origin` is listed in `OBSCURA_MCP_ALLOWED_ORIGINS` (`http.rs:234-241`, `:367`). The `--stealth` global flag applies here too.

---

## Embeddable Rust Library

New since v0.1.7: the `obscura` crate is a first-class Rust API rather than only a CLI.

```rust
use obscura::Browser;

#[tokio::main]
async fn main() -> anyhow::Result<()> {
    let browser = Browser::builder()
        .stealth(true)
        .build()?;
    let mut page = browser.new_page().await?;
    page.goto("https://example.com").await?;
    println!("Content: {} bytes", page.content().len());
    Ok(())
}
```

It re-exports the interception types (`InterceptedRequest`, `InterceptResolution`, `RequestCallback`, `RequestInfo`, `Response`, `ResponseCallback`, `ResourceType`; `crates/obscura/src/lib.rs:19-27`) so a Rust program can observe and modify traffic without going through CDP.

---

## Performance

The project publishes these figures in its README and in the separate `obscura-benchmark` repo. They are the maintainer's, not independently reproduced here (**Tier B**):

| Operation | Obscura | Headless Chrome |
|---|---|---|
| Memory | ~30 MB | 200+ MB |
| Binary size | ~70 MB | 300+ MB |
| Startup | Instant (V8 snapshot) | ~2 s |
| Static HTML page load | ~51 ms | ~500 ms |
| JS + XHR + fetch | ~84 ms | ~800 ms |
| Dynamic scripts | ~78 ms | ~700 ms |

The benchmark repo's latest published pass (2026-09-11, against Obscura `01e1caa`) builds its WPT binary with `--no-default-features` (a no-render build), and its README labels the concurrency and memory results as the no-render scraping profile; its WPT run covers only the classic DOM/JavaScript profile (reftests are not run, and rendering regressions are tracked by the main repo's `render-repros/` suite). Its published results are WPT Core tier 327,094 / 392,547 subtests (83.3%; Relevant 86.8%, Full 67.6%), 33 / 33 obstacle-course stages, 94 / 98 pages rendered in the real-world corpus (headless Chrome 85 / 98) and 1,432 / 1,500 pages rendered in the reliability sweep with 0 crashes and 0 panics. Its `stealth-bench/run.py` is an internal fingerprint-consistency check served from a local HTTP server (the docstring says no outbound requests are made), not a run against third-party detectors. All of these are the maintainer's figures (**Tier B**). No memory, startup or load-time figures are published for the render-enabled default archive (**Tier D**). In a no-render build the savings come from skipping work a real browser performs: layout, style cascade, font shaping, image decode and raster; a render build performs layout and CPU rasterization as well (there is still no GPU compositor). The full suite lives at `github.com/h4ckf0r0day/obscura-benchmark`; the numbers above have not been independently verified for this analysis.

For multi-URL workloads, `obscura scrape` runs `obscura-worker` child processes with a configurable concurrency limit (default 10), and `obscura serve --workers N` runs N CDP server child processes behind a TCP load balancer. `--v8-flags` can raise the V8 heap cap for JS-heavy pages.

---

## Pros and Cons

### Advantages

| Advantage | Description |
|---|---|
| Lightweight footprint | ~30 MB resident, ~70 MB binary (project figures, **Tier B**; the benchmark repo labels its throughput results as the no-render profile), no Chrome / Node.js dependency |
| V8 startup snapshot | bootstrap script compiled into a snapshot at build time (`build.rs`); the README lists startup as instant (**Tier B**) |
| Prebuilt releases | Linux x86_64 + aarch64, macOS Intel + ARM, Windows x86_64 (built on native CI runners); Docker image for linux/amd64 + arm64 |
| CDP API surface | 14 domains plus 11 accepted no-ops; documented for use with `puppeteer-core` and `playwright-core` |
| Built-in MCP server | 37 tools (35 without `render`), multi-tab, stdio + HTTP; token required for non-loopback HTTP |
| Embeddable Rust library | `Browser::builder()` API + request/response interception |
| Profile-derived persona | 8 Windows / macOS profiles with matching UA, platform, UA-CH; fixed Chrome 145 / Windows identity in stealth builds; timezone from the process `TZ` |
| Tracker blocking | 3,520-domain PGL list embedded at compile time |
| Multi-worker mode | Built-in process supervisor + TCP load balancer for parallel scraping |
| Optional TLS impersonation | `--features stealth` (or a `-stealth` archive) enables Chrome 145 (Windows) JA3 / JA4 via `wreq` |
| Containment mechanisms | V8 termination watchdogs and near-heap-limit guard, per-command deadlines, `catch_unwind` around DOM and URL ops, SSRF / DNS-rebind guards, token-gated non-loopback CDP / MCP binds |
| Rust workspace | Ten member crates, `deno_core` foundation, Apache-2.0 throughout |

### Limitations

| Limitation | Description |
|---|---|
| **Rendering is build-gated** | `default = []` in Cargo — a source build without `--features render` has none of the v0.2.0 layout work. Release archives (no suffix / `-stealth`) and the Docker image do include it; `-no-render*` archives do not. Know which binary you have. |
| Non-render builds keep every v0.1.x layout limitation | No cascade, synthesized `getBoundingClientRect` grid, defaults-table `getComputedStyle`, `captureScreenshot`/`printToPDF` return errors |
| No GPU rasterization | Painting is CPU-side; there is no compositor surface (`fromSurface=false` is unsupported in all builds) |
| WebGL unavailable; canvas 2D is a JS software rasterizer | `getContext('webgl')` returns `null`; `fillText` draws seed-derived dot glyphs rather than fonts; transforms, `clip` and curves are no-ops; `toDataURL` is a valid PNG of the buffer |
| Young rendering engine | `obscura-render` is 69.9k lines at `a005d16` and was introduced in v0.2.0 (2026-08-08). The README states that long-tail CSS, some Web APIs, media playback, compositor effects and platform font rasterization may differ from Chromium (**Tier B**) |
| No Service Workers or audio DSP | `navigator.serviceWorker.register()` resolves without registering a worker; `AudioContext` graph nodes are inert (`bootstrap.js:14135`) |
| Finite fingerprint pools | 8 screens, 2 audio sample rates, 5–6 hardware-concurrency values (GPU pools of 6–12 entries exist but are not exposed) — aggregatable across many requests |
| Plugin list tell | Includes `"WebKit built-in PDF"` (`bootstrap.js:7388`), not present in real Chrome |
| Single TLS profile in stealth mode | Chrome 145 Windows only; no rotation or alternative targets |
| Default build has no TLS impersonation | Needs the `stealth` feature: a `-stealth` / `-no-render-stealth` archive or `--features stealth`; the unsuffixed archive and the Docker image do not include it |
| wreq on pinned pre-release RCs | TLS impersonation depends on exact `wreq` RC pins that churn |
| Interception resource typing | JS-initiated requests (fetch and XHR) are reported as `Fetch` (`ops.rs:3297`, `:3664`, `:3953`) |

Resolved since the previous analysis: the license inconsistency (now Apache-2.0 everywhere), the hardcoded Linux `navigator.platform`, `getBoundingClientRect` all-zeros, `event.isTrusted` always-true, static `hardwareConcurrency`/`deviceMemory`, and input ignoring coordinates. The GPU-vs-platform inconsistency is gone by removal rather than by correction: WebGL is unavailable, so no renderer string is exposed.

---

## Installation & Usage

### Pre-built binaries

```bash
# Linux x86_64
curl -LO https://github.com/h4ckf0r0day/obscura/releases/latest/download/obscura-x86_64-linux.tar.gz
tar xzf obscura-x86_64-linux.tar.gz

# This unsuffixed archive includes rendering and no stealth transport. Add -stealth,
# -no-render or -no-render-stealth before .tar.gz for the other variants.
# Linux aarch64, macOS (Intel + Apple Silicon), Windows x86_64 (.zip) also published.
```

The project docs also list Arch Linux AUR (`docs/Installation.md:39`) and NixOS (`nix-env -iA nixpkgs.obscura`, README). The Docker image is built on `gcr.io/distroless/cc-debian12:nonroot` (uid 65532, ~57 MB compressed per the README) for linux/amd64 and linux/arm64, with `--features render` and without the stealth feature (`Dockerfile`, `.github/workflows/docker.yml:45`).

### Build from source

```bash
git clone https://github.com/h4ckf0r0day/obscura.git
cd obscura
# Rendering (layout, screenshots, PDF)
cargo build --release -p obscura-cli --bins --features render

# Rendering + TLS impersonation (BoringSSL: needs CMake, Clang, libclang)
cargo build --release -p obscura-cli --bins --features render,stealth

# No rendering
cargo build --release -p obscura-cli --bins --no-default-features

# No rendering, with TLS impersonation
cargo build --release -p obscura-cli --bins --no-default-features --features stealth
```

First build compiles V8 from source (several minutes); subsequent builds are cached.

### Fetch a page

```bash
obscura fetch https://example.com --eval "document.title"
obscura fetch https://example.com --dump links      # or: text | markdown | assets
obscura fetch https://example.com --wait-until networkidle0
obscura fetch https://example.com --stealth          # global flag; tracker blocking, plus wreq TLS and the Chrome 145 identity in stealth builds
obscura fetch https://example.com --screenshot page.png   # render builds only
```

### Start a CDP server

```bash
obscura serve --port 9222 --stealth
# a non-loopback --host requires OBSCURA_CDP_TOKEN (at least 32 bytes)
```

### Run the MCP server

```bash
obscura mcp                          # stdio transport (for local agents)
OBSCURA_MCP_TOKEN="$(openssl rand -hex 32)" obscura mcp --http --host 0.0.0.0 --port 8080   # HTTP; a non-loopback bind needs the token
```

### Use from Puppeteer

```javascript
import puppeteer from 'puppeteer-core';

const browser = await puppeteer.connect({
  browserWSEndpoint: 'ws://127.0.0.1:9222/devtools/browser',
});
const page = await browser.newPage();
await page.goto('https://example.com');
console.log(await page.title());
await browser.disconnect();
```

### Use from Playwright

```javascript
import { chromium } from 'playwright-core';

const browser = await chromium.connectOverCDP({ endpointURL: 'ws://127.0.0.1:9222' });
const page = await browser.newContext().then(ctx => ctx.newPage());
await page.goto('https://example.com');
await browser.close();
```

### Use as a Rust library

```rust
let browser = obscura::Browser::builder().stealth(true).build()?;
let mut page = browser.new_page().await?;
page.goto("https://example.com").await?;
```

### Parallel scraping

```bash
obscura scrape url1 url2 url3 \
  --concurrency 25 \
  --eval "document.querySelector('h1').textContent" \
  --format json \
  --stealth
```

### Environment knobs (selected)

```
OBSCURA_PROFILE=2            # pin a fingerprint profile by index
OBSCURA_ROTATE_PROFILE=1     # random profile per browser context
OBSCURA_TIMEZONE=America/New_York   # Date + Intl report the same zone (default Europe/Berlin)
OBSCURA_CDP_COMMAND_TIMEOUT_MS, OBSCURA_FETCH_TIMEOUT_MS   # deadlines
OBSCURA_SCRIPT_DEADLINE_MS   # page script-execution budget (default 30 s)
OBSCURA_ALLOW_PRIVATE_NETWORK=1   # lift the SSRF deny-set for localhost / LAN targets
OBSCURA_BLOCK_TRACKERS=0     # disable tracker blocking in the stealth client
OBSCURA_CDP_TOKEN, OBSCURA_MCP_TOKEN   # bearer tokens (non-loopback binds need one)
```

---

## Comparison with Alternatives

| Dimension | Obscura | Patchright | Camoufox | CloakBrowser | Scrapling (HTTP tier) |
|---|---|---|---|---|---|
| Underlying engine | V8 + html5ever + own Rust layout/paint engine | Real Chromium | Real Firefox | Real Chromium | curl_cffi |
| Renders pages | Yes (render builds); No (`-no-render`) | Yes | Yes | Yes | No |
| Real Canvas / WebGL | Canvas 2D: JS software rasterizer (synthetic text glyphs); WebGL unavailable (`null`) | Yes | Yes (C++ noise) | Yes (C++ noise) | N/A |
| Fingerprint coherence | Per-profile UA / platform / UA-CH; timezone from process `TZ`; no WebGL surface | Native | Native + BrowserForge | Native | N/A |
| TLS impersonation | Optional, single profile (`wreq`) | None | None | None | Yes, multiple profiles |
| Layout / `getComputedStyle` | Renderer-computed (render builds); synthesized otherwise | Native | Native | Native | N/A |
| Memory footprint | ~30 MB (project figure, **Tier B**) | ~200 MB | ~200 MB | ~200 MB | ~10 MB |
| Stealth approach | JS-level shim + optional TLS | CDP protocol patches | C++ source patches | C++ source patches | TLS only |
| MCP server | Built-in (37 tools) | No | No | No | Yes (separate) |

Obscura runs JavaScript and, in render builds, its own layout and paint engine without a Chromium or Gecko process; the rendering output is its own implementation rather than Blink's or Gecko's. An HTTP-only client such as `curl_cffi` runs no JavaScript.

---

## Anti-Bot Service Coverage

> **These are architectural expectations, not test results.** Nothing below was
> benchmarked — not by this report, and not publicly by the project, which makes **no
> anti-bot service claims** (evidence **Tier D**); its stealth documentation instead lists
> Cloudflare interactive challenges, DataDome and Akamai active challenges and CAPTCHAs as
> not handled (**Tier B**). What follows is reasoning from what the engine demonstrably
> does and does not implement. Treat it as a hypothesis to test against your own targets,
> never as a pass/fail record.

| Check type | Expectation | Reasoning from the architecture |
|---|:---:|---|
| Static HTML behind UA filter | likely fine | UA, headers, and UA-CH look like Chrome and agree with each other |
| Layout-probing checks (`getBoundingClientRect`, `getComputedStyle`) | **materially improved in v0.2.0 render builds** | Real measured geometry and renderer-computed style replace the v0.1.x synthesized grid and defaults table. Non-render builds are unchanged and keep the synthesized grid and defaults table. |
| Canvas-pixel checks | synthetic output | Canvas 2D is a JS software rasterizer: `toDataURL` is a valid PNG, but `fillText` draws seed-derived dot glyphs rather than a font, so text-based canvas hashes are per-session synthetic values |
| WebGL / audio-DSP checks | not implemented | WebGL is unavailable (`getContext` returns `null`); audio graph nodes are inert and `OfflineAudioContext` returns a scaled synthetic wave |
| Behavioural / sensor telemetry | unaddressed | No mouse-motion model, no human input timing — nothing in the engine targets this layer |
| TLS-fingerprint checks | addressed in stealth builds | `wreq` is configured with a Chrome 145 emulation profile; single profile, so it is aggregatable across many requests |

Summary of the table: **v0.2.0 added renderer-backed layout and style in render builds; the canvas-text, WebGL, audio and behavioural rows remain open.** Anti-bot systems that depend on real pixel output or input telemetry would see an engine that does not implement them.

Note: the v0.1.9 release notes claimed "creepjs reports 0% detection" (release-note text; it is not in the source tree and was not re-checked in this pass). That is the
maintainer's result (**Tier B**), plausible for CreepJS's consistency-oriented checks
given a coherent persona, and not reproduced here. CreepJS is a consistency auditor,
not a commercial anti-bot — an internal-consistency pass is not evidence about
DataDome- or Kasada-class systems.

---

## When to Use

### Best For
- Scraping server-rendered HTML at high concurrency where memory and startup time are the bottlenecks
- Sites with light-to-moderate protection (UA/TLS filters, basic JS challenges) that don't require real rendering
- CDP-driven prototypes and AI-agent tool use (via the built-in MCP server) without installing Chrome
- Embedding a browser in a Rust service (the `obscura` crate) with request interception
- JavaScript-driven content where the JS extracts data rather than measuring real layout/render output (no-render builds; render builds provide measured layout)

### Not Ideal For
- Sites protected by enterprise anti-bot services (Turnstile, DataDome, Akamai, Kasada, Imperva)
- Anything depending on video playback or GPU compositing (screenshots and PDF export need a render build)
- Pages that hash real canvas / WebGL / audio output or read back rendered pixels
- Sites depending on real Service Workers or a real audio DSP graph
- High-volume scraping needing TLS-profile diversity (stealth mode is a single Chrome 145 Windows profile)
- Use cases where the User-Agent claim must accurately reflect the client (compliance / legal contexts)

---

## Resources

- [GitHub Repository](https://github.com/h4ckf0r0day/obscura)
- [Documentation](https://docs.obscura.sh)
- [obscura-benchmark](https://github.com/h4ckf0r0day/obscura-benchmark) — the separate benchmark/conformance suite
- [deno_core](https://github.com/denoland/deno_core) — V8 runtime crate used by Obscura
- [wreq](https://crates.io/crates/wreq) — TLS impersonation library used in stealth mode
- [html5ever](https://github.com/servo/html5ever) — HTML parser used for the DOM tree

---

## Summary

Obscura is a **from-scratch browser engine** that uses V8 for JavaScript execution and html5ever for HTML parsing, with a large JavaScript shim providing `navigator`, `document`, `window`, and the rest of the browser globals — and, since v0.2.0, a native Rust layout and paint engine underneath it. The project reports lower memory and page-load figures than headless Chrome (**Tier B**, not reproduced here; the benchmark repo labels its throughput results as the no-render profile). It also ships an embeddable Rust library, a 37-tool MCP server (35 without `render`), and request/response interception.

Across v0.1.x and v0.2.x the fingerprint surface changed: the persona fields (UA, platform, UA-CH) derive from one profile (Windows by default; Chrome 143 in ordinary builds, Chrome 145 in stealth builds), `event.isTrusted` is false for page-created events, `getBoundingClientRect` and `getComputedStyle` are renderer-backed in render builds, input events hit-test, and TLS impersonation ships in the `-stealth` archives. Still absent: WebGL (unavailable), real font rasterization in canvas, an audio DSP graph and a pointer-motion model; the fingerprint pools are finite and the timezone is a process-level setting rather than part of the profile. No anti-bot service result is published or tested here (**Tier D**).

**Complexity:** Low — single binary, CDP server, MCP server, embeddable crate; driven by Puppeteer / Playwright clients over CDP

**Applicability:** high-concurrency fetching where per-instance memory matters and the targets do not probe canvas, WebGL, or audio, plus AI-agent browsing over the MCP server. Layout-probing targets require a render-enabled build (release archive with no suffix or `-stealth`, or `--features render` from source). Memory and page-load figures are the project's own (Tier B).

*Verified against the source at `github.com/h4ckf0r0day/obscura` @ `a005d16` (`main`, 66 commits past the v0.2.3 tag) and `h4ckf0r0day/obscura-benchmark` @ `e4a5490`, 2026-09-30. Read in an isolated container — see [METHODOLOGY.md](METHODOLOGY.md#source-handling).*
