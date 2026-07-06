# Obscura - Deep Technical Analysis

> **Tool Type:** Custom Headless Browser Engine (built from scratch in Rust)
> **Repository:** [github.com/h4ckf0r0day/obscura](https://github.com/h4ckf0r0day/obscura)
> **Approach:** V8 runtime + html5ever DOM tree + JavaScript shim + optional TLS impersonation
> **Language:** Rust (CLI / engine / embeddable library), Puppeteer / Playwright clients (any language) via CDP, plus a built-in MCP server
> **Effectiveness:** Moderate (basic detection bypass + now-coherent fingerprint surface; still weak against layout/render-aware anti-bots)
> **Maintenance:** Actively developed — **v0.1.9 as of 2026-07** (10 releases since 2026-04-13; last push 2026-07-03; ~17.7k stars). Apache-2.0 across the board.

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

Obscura is an **open-source headless browser engine written in Rust**, built specifically for web scraping and AI agent automation. It runs JavaScript via V8 (through the `deno_core` crate, currently pinned to `0.350`) and exposes a Chrome DevTools Protocol server so it can be driven by Puppeteer or Playwright clients. As of v0.1.7 it also ships as an **embeddable Rust library** (the `obscura` crate) and as a **built-in MCP server** (the `obscura mcp` subcommand) for AI-agent tool use.

**Key differentiator:** Unlike every other tool analyzed in this repository, Obscura is not a patched, forked, or wrapped version of Chrome or Firefox. It is a **from-scratch engine** that reimplements just enough of the browser surface to run JavaScript against an HTML document.

**Important caveat:** Obscura is not a full browser. It contains no layout engine, no CSS cascade, no compositor, no GPU rasterization, and no real Canvas / WebGL / audio implementations. External CSS files are fetched but stored as a string and never applied as a cascade. This is what makes it lightweight (≈30 MB resident, ≈85 ms page load per the project's own benchmarks) and what limits its effectiveness against anti-bot systems that probe real layout, rendering, or fingerprinting APIs.

**What changed since the last analysis (v0.1.0 → v0.1.9):** the JS shim grew from ~3,000 to ~7,900 lines and closed several of the tells the previous review flagged. The fingerprint surface is now **platform-coherent** (Windows / macOS / Linux profiles whose UA, `navigator.platform`, UA-CH, GPU renderer, and timezone agree), `getBoundingClientRect` returns deterministic non-zero rects, input events go through `document.elementFromPoint` hit-testing, and `event.isTrusted` is `false` for page-created events. The default persona is now **Windows / Chrome 145**, not Linux. The license inconsistency (Apache vs MIT) is resolved — everything is Apache-2.0.

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
│  │ /serve/mcp   │  │ CDP server   │  │ 32 tools     │  │ embed    │ │
│  │ + balancer   │  │ (12 domains) │  │ stdio/HTTP   │  │ Rust API │ │
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
│  │ ever     │    │ 0.350        │  │ + wreq       │                │
│  │ DOM      │    │ + 23 ops     │  │ (--features  │                │
│  │ tree     │    │ + 7,878-line │  │   stealth,   │                │
│  │ + CSS    │    │  bootstrap.js│  │   Chrome 145 │                │
│  │ selectors│    │  (DOM shim)  │  │   TLS)       │                │
│  └──────────┘    └──────────────┘  └──────────────┘                │
│                                                                      │
│  Supporting: 3,520-domain tracker blocklist (PGL list)              │
│              CookieJar, robots.txt cache, proxy support,            │
│              SSRF / DNS-rebind protection, V8 watchdogs             │
└─────────────────────────────────────────────────────────────────────┘
```

The repository is a Cargo workspace of **eight crates** (up from six — `obscura-mcp` and the embeddable `obscura` crate were added):

| Crate | Approx. LOC (Rust) | Responsibility |
|---|---:|---|
| `obscura-cli` | ~2,130 | clap-based CLI (`fetch`, `scrape`, `serve`, `mcp`) + multi-worker TCP load balancer |
| `obscura-cdp` | ~5,530 | WebSocket server speaking the Chrome DevTools Protocol (12 domains) |
| `obscura-browser` | ~2,100 | `Page` abstraction: navigation, subresource fetching, script execution, interception |
| `obscura-net` | ~2,555 | HTTP client (reqwest baseline + optional `wreq` for TLS impersonation) + blocklist + cookies + interceptor |
| `obscura-js` | ~4,833 Rust + 7,878 JS | V8 runtime via `deno_core` (23 `op2` ops) + bootstrap.js DOM shim |
| `obscura-dom` | ~2,246 | html5ever-backed DOM tree + `selectors` crate for CSS queries |
| `obscura-mcp` | ~2,094 | Model Context Protocol server (32 tools, stdio + HTTP transports) |
| `obscura` | ~483 | Embeddable Rust library (`Browser::builder()...`) |

### Page Lifecycle

When `obscura fetch <url>` runs, the navigation path in `obscura-browser` executes roughly:

```
1. validate_url()                  reject private IPs, localhost, non-http schemes (SSRF guard)
2. (optional) robots.txt           fetch and check if --obey-robots
3. http_client.fetch()             reqwest (or wreq if built with --features stealth and run with --stealth)
4. parse_html()                    html5ever produces a DomTree
5. extract <link rel=stylesheet>   fetch all CSS in parallel
                                   stored as a string; NOT applied as a cascade
6. init V8 runtime                 load bootstrap.js (V8 snapshot); re-seed fingerprint
7. classify <script> tags          regular / defer / async / module
8. fetch + execute scripts         per-script execution, timeout-bounded (OBSCURA_FETCH_TIMEOUT_MS)
9. (optional) network idle wait    networkidle0 / networkidle2 windows (500 ms idle)
10. dump HTML / text / markdown / links / assets / eval result
```

Two consequences of this pipeline are worth flagging:

- **External CSS is never applied as a cascade.** It is fetched but not resolved into computed style. `getComputedStyle` (see below) now returns *synthesized* values (inline styles, dimensions from the bounding rect, and a defaults table), not a real cascade. JavaScript that depends on styles set only via external stylesheets will not see them.
- **Layout is synthesized, not computed.** There is no layout engine, but `getBoundingClientRect` now returns deterministic per-node rects (a 12-column grid derived from the node id) instead of all-zeros, specifically so Playwright's actionability polling and virtualization libraries work (see the `bootstrap.js` comments referencing issues #45 and #324).

### V8 Snapshotting

`obscura-js` builds a V8 startup snapshot at compile time so that per-page initialization is microseconds rather than milliseconds. The bootstrap script is included via `include_str!("../js/bootstrap.js")` and its `__obscura_init()` runs on each new runtime instance. A release-CI smoke test (`obscura fetch data:... --eval "1+1"`) runs the V8 path once per target so a mismatched snapshot never ships (issue #290). The engine also arms V8 termination watchdogs (`arm_watchdog`, `cdp_watchdog`) so a runaway page cannot wedge the isolate, and DOM ops are wrapped in `catch_unwind` so an op panic degrades to a null result instead of aborting through V8's FFI frame.

---

## Anti-Detection Mechanisms

All anti-detection lives in `crates/obscura-js/js/bootstrap.js` (~7,878 lines). There are no C++ or binary-level patches — every override is JavaScript executed before any page script runs. The single biggest change since v0.1.0 is that the fingerprint surface is now **internally coherent per platform profile** rather than a fixed Linux persona with mismatched sub-fields.

### `navigator` overrides

```javascript
// bootstrap.js:2831 onward
globalThis.navigator = {
  get userAgent() { return globalThis.__obscura_ua ||
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36"; },
  language: "en-US", languages: ["en-US","en"],
  get platform() { return globalThis.__obscura_platform || "Win32"; },
  hardwareConcurrency: 8, deviceMemory: 8, maxTouchPoints: 0,
  vendor: "Google Inc.", product: "Gecko",
  get webdriver() { /* on a thin prototype, see below */ },
  userAgentData: {
    mobile: false,
    get brands() { return _uaBrands(); },   // per-seed permuted brand order
    get platform() { return globalThis.__obscura_ua_platform || "Windows"; },
    getHighEntropyValues(hints) { return Promise.resolve({
      architecture: "x86", bitness: "64",
      platform: globalThis.__obscura_ua_platform || "Windows",
      platformVersion: globalThis.__obscura_ua_platform_version || "15.0.0",
      /* full UA-CH payload */ }); },
  },
  plugins: [ /* 5 PDF-viewer entries */ ],
  // ... mediaDevices, getBattery, serviceWorker, connection, permissions, etc.
}
```

What it covers:
- `navigator.webdriver` is moved onto a **thin prototype** so `Object.getOwnPropertyDescriptor(navigator, 'webdriver')` returns `undefined` (matches real Chrome) rather than exposing the override on the instance.
- Full `navigator.userAgentData` with a `getHighEntropyValues` payload whose `platform` / `platformVersion` agree with the UA string and `navigator.platform`.
- `userAgentData.brands` order is permuted per session seed (`_uaBrands`), like real Chrome's GREASE brand.
- Plugin and mimeType lists, `connection` (NetworkInformation), faked `getBattery` with per-session values.

What is now **coherent** (previously flagged as tells, now fixed):
- **Default persona is Windows / Chrome 145**, not Linux. `navigator.platform` defaults to `Win32`; UA-CH `platform` to `Windows`; `platformVersion` to `15.0.0`.
- `hardwareConcurrency` and `deviceMemory` are **re-randomized per session** in `__obscura_init` (e.g. `[4,6,8,12,16]` and `[4,8]` under `--stealth`), not static `8`.
- Platform, UA, UA-CH, and GPU renderer all track a single chosen profile (Windows / macOS / Linux). See "Per-session fingerprint" below.

What may still be detectable:
- The plugin list includes a `"WebKit built-in PDF"` entry (5 plugins total), which does not appear in real Chrome's plugin set.
- `Function.prototype.toString` itself is marked native (the masking function reporting as native) — a detector comparing the masking chain can still observe the override in principle.
- Fingerprint pools are finite (12–13 GPUs per platform, 8 screens, 2 sample rates), so a detector aggregating values across many requests from one source can still recognize the distribution.

### `Function.prototype.toString` masking

```javascript
// bootstrap.js:72-81
const _nativeFns = new Set();
const _origToString = Function.prototype.toString;
Function.prototype.toString = function() {
  if (_nativeFns.has(this)) return `function ${this.name || ''}() { [native code] }`;
  return _origToString.call(this);
};
function _markNative(fn) { if (typeof fn === 'function') _nativeFns.add(fn); return fn; }
_nativeFns.add(Function.prototype.toString);
```

About **96 functions** are marked native via `_markNative(...)` (up from ~80). This handles the common `Function.prototype.toString().includes('[native code]')` check, including on `toDataURL`, media element methods, `getComputedStyle`, and the WebGL context methods.

### Per-session fingerprint (now platform-coherent)

```javascript
// bootstrap.js:155-224  (_getFp)
const _uaPlat = globalThis.__obscura_ua_platform || 'Windows';
const isMac = _uaPlat === 'macOS';
const isLinux = _uaPlat === 'Linux';
const gpuPool = isMac ? [ /* ANGLE Metal Renderer: Apple M1..M3 */ ]
             : isLinux ? [ /* ANGLE ... Mesa ... OpenGL 4.6 */ ]
             :           [ /* ANGLE ... Direct3D11 vs_5_0 ps_5_0, D3D11 */ ];
const gpuVendorPool = isMac ? [ 'Google Inc. (Apple)', ... ]
                    : isLinux ? [ 'Google Inc. (Intel/AMD/NVIDIA)', ... ]
                    :           [ 'Google Inc. (NVIDIA/Intel/AMD)', ... ];
const idx = Math.floor(_fpRand(42) * gpuPool.length);
// screen, audio sample rate/latency, compressor params, battery, canvas fp
// all derived from the same _fpSeed so one profile is internally consistent.
```

The GPU **renderer string and vendor string are now selected to match the OS profile**: Windows → ANGLE Direct3D11, macOS → ANGLE Metal, Linux → ANGLE/Mesa OpenGL. This directly addresses the previous review's finding that "all GPU strings referenced Direct3D11 regardless of platform." `__obscura_init` re-seeds with `Date.now() ^ (Math.random()*0xFFFFFFFF)` per new runtime.

Profile selection is controllable:
- `OBSCURA_PROFILE=<n>` pins a specific profile index.
- `OBSCURA_ROTATE_PROFILE=1` randomizes the profile per browser context.
- Default is a single stable profile (rotation is opt-in because one IP cycling identities is itself a signal).

WebGL parameters reflect this coherence:

```javascript
// bootstrap.js:5985-5996
getParameter(pname) {
  if (pname === 0x9245) return _fp('gpuVendor'); // UNMASKED_VENDOR_WEBGL (coherent)
  if (pname === 0x9246) return _fp('gpu');       // UNMASKED_RENDERER_WEBGL (coherent, platform-matched)
  if (pname === 0x1F01) return 'WebKit WebGL';   // GL_RENDERER  (this is also what real Chrome returns here)
  if (pname === 0x1F00) return 'WebKit';         // GL_VENDOR
  ...
}
```

Note: the debug-info `UNMASKED_RENDERER_WEBGL` — the string fingerprinters actually read — is now the coherent, platform-matched ANGLE string. The plain `GL_RENDERER` constant returning `'WebKit WebGL'` matches real Chrome and is not itself the tell the previous analysis implied. What remains is that these are **string reports with no real GL pipeline behind them**: there is no actual shader compilation, so a fingerprinter that reads back rendered pixels gets noise (`readPixels` fills random bytes).

### Canvas

```javascript
// bootstrap.js:215-219, 6020-6034
let cfp = 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUg';
for (let i = 0; i < 40; i++) cfp += chars[Math.floor(_fpRand(500 + i) * 64)];
cfp += '==';
// ...
Element.prototype.toDataURL = function(type) { return _fp('canvasFingerprint'); };
```

`toDataURL` returns a fixed-per-session string starting with a real PNG header, but the bytes after are random base64 and do not decode to a valid image. There is no underlying canvas rasterizer. Anti-bot scripts that decode the data URL or compare it against a known reference will see a non-image.

### Audio

Audio context, compressor parameters, and analyser data are all synthetic values derived from `_fpSeed`. There is no real DSP graph. Audio fingerprinters that run a real signal chain and hash the output will get values that match no real Chrome.

### `event.isTrusted` (now correct)

```javascript
// bootstrap.js:4297-4324
const _trustedEvents = new WeakSet();
globalThis.__obscura_markTrusted = function(ev) { _trustedEvents.add(ev); return ev; };
globalThis.Event = class Event {
  ...
  get isTrusted() { return _trustedEvents.has(this); }
};
```

This is a **fix** relative to the previous analysis. Page-created events (`new Event(...)`, `new MouseEvent(...)`) now report `isTrusted === false`, per spec, because only events Obscura's CDP input pipeline dispatches are added to the closure-private `_trustedEvents` WeakSet (via the non-enumerable `__obscura_markTrusted`). The old "always `true`" tell is gone.

### Mouse and keyboard input (now hit-tested)

```javascript
// crates/obscura-cdp/src/domains/input.rs
"dispatchMouseEvent" => {
  // mousePressed:
  var target = (document.elementFromPoint && document.elementFromPoint(x,y))
            || globalThis.__obscura_click_target
            || document.activeElement || document.body;
  globalThis.__obscura_click_target = target;
  // dispatch trusted MouseEvent on target
}
```

Also a **fix**: dispatched mouse coordinates are now resolved through `document.elementFromPoint(x, y)` first, and `getBoundingClientRect` returns stable per-node rects, so `elementFromPoint` can actually recurse into the tree. Coordinate-driven clicks (not just selector-driven `page.click('selector')`) now hit the intended element. The previous "coordinates are ignored, target is always `__obscura_click_target`" limitation no longer holds. It remains a synthesized geometry, not a real layout, so pixel-perfect hit-testing against real element bounds is still approximate.

### `getComputedStyle` (now synthesized, not a bare stub)

```javascript
// bootstrap.js:3804 onward
globalThis.getComputedStyle = (el) => {
  // 1. inline style value first
  // 2. width/height/top/left/... synthesized from getBoundingClientRect
  // 3. a defaults table (display:block, position:static, font-size:16px, ...)
  ...
};
```

`getComputedStyle` now returns inline values, dimensions pulled from the (non-zero) bounding rect, and a table of sensible defaults — added specifically so React virtualization libraries (react-window, tanstack-virtual, react-virtuoso) render content instead of zero items. It still does **not** apply the external CSS cascade, and some defaults (e.g. `font-family: 'Times'`) are giveaways to a detector that inspects computed style closely.

---

## Network Layer & Stealth Mode

Obscura has **two independent stealth levers** that are easy to conflate:

1. The **runtime `--stealth` flag** (global; applies to `fetch`, `serve`, `scrape`, `mcp`). It tightens the JS fingerprint (coherent persona, narrower hardware pools) and enables tracker blocking. It works in any build.
2. The **`stealth` build feature** (`cargo build --features stealth`). It compiles in `wreq` so the HTTP client can impersonate Chrome's TLS ClientHello. Without this feature the binary falls back to `reqwest`/rustls.

### Default HTTP client (`reqwest`)

The baseline client is `reqwest` with rustls, gzip/brotli/deflate, and SOCKS support. Chrome-shaped headers are added manually and are kept consistent with `navigator.userAgentData`:

```rust
// crates/obscura-net/src/client.rs
headers.insert(USER_AGENT, "...Chrome/145.0.0.0...");
headers.insert("sec-ch-ua", "\"Google Chrome\";v=\"145\", ...");
headers.insert("sec-ch-ua-mobile", "?0");
headers.insert("sec-ch-ua-platform", "\"Windows\"");
headers.insert("sec-fetch-dest", "document");
headers.insert("upgrade-insecure-requests", "1");
```

The headers look like Chrome, but without the stealth feature the TLS handshake is whatever rustls produces, so JA3 / JA4 will match a Rust HTTP client, not Chrome.

### `--features stealth` build (`wreq`)

```rust
// crates/obscura-net/src/wreq_client.rs
let emulation_opts = wreq_util::Emulation::builder()
    .profile(wreq_util::Profile::Chrome145)
    .platform(wreq_util::Platform::Windows)
    .build();
```

`wreq` is a TLS-impersonation library (BoringSSL-backed, similar in spirit to `curl_cffi`). With the feature enabled, JA3 / JA4, ALPN, and cipher order match **Chrome 145 on Windows**. The profile is hardcoded — no rotation, no per-session variation, and no alternative emulation targets. The `wreq` / `wreq-util` deps are pinned to exact pre-release RCs (`wreq =6.0.0-rc.29`, `wreq-util =3.0.0-rc.12`) because their API churns between RCs (issue #234), and `prefix-symbols` is enabled only on Linux/Android to avoid BoringSSL/OpenSSL symbol clashes (issue #39).

**Release binaries:** the project's stealth docs state that the binaries on the Releases page include the stealth feature, and the release workflow does run `cargo build --features stealth` for every target. Note that build step is marked `continue-on-error: true`, so if the stealth compile fails on a target the packaged binary can fall back to the default client — verify with `obscura --version` / behavior if TLS fidelity is critical. This is an improvement over the previous state, where release binaries shipped without TLS impersonation.

### Tracker blocking

```rust
// crates/obscura-net/src/blocklist.rs
const PGL_LIST: &str = include_str!("pgl_domains.txt");  // 3,520 domains
// test asserts blocklist().len() > 3500
```

Peter Lowe's tracker domain list (**3,520 domains**, unchanged) is embedded at compile time. Lookup is exact plus suffix match. Blocked domains are never fetched — privacy hygiene that also speeds loads and prevents third-party fingerprinting scripts from running, but it does not itself disguise the client.

### Request/response interception (new in v0.1.9)

The `obscura-net` interceptor and `obscura-browser`'s `InterceptedRequest` / `InterceptResolution` expose callbacks to observe, block, modify headers on, or fulfill requests from Rust (embeddable API) and via CDP `Fetch`. A known limitation in v0.1.9: JS-initiated requests report resource type `"Fetch"` and XHR is not yet distinguished separately.

---

## CDP Implementation

`obscura-cdp` implements a subset of the Chrome DevTools Protocol sufficient to support Puppeteer and Playwright clients connecting via `connectOverCDP` / `puppeteer.connect`. It now spans **12 domains** (up from ~9; `Accessibility` and `DOMSnapshot` were added):

| Domain | Implemented (selected) | Notable Gaps |
|---|---|---|
| Target | createTarget, closeTarget, attachToTarget, attachToBrowserTarget, createBrowserContext | targetCrashed events |
| Page | navigate, getFrameTree, getLayoutMetrics, addScriptToEvaluateOnNewDocument, lifecycleEvents | captureScreenshot / printToPDF (no rendering) |
| Runtime | evaluate, callFunctionOn, getProperties, addBinding | full async stack traces |
| DOM | getDocument, querySelector, querySelectorAll, getOuterHTML, resolveNode | real layout queries |
| DOMSnapshot | captureSnapshot (structural) | full computed-style snapshots |
| Accessibility | getFullAXTree (roles / names) | live AX events |
| Network | enable, setCookies, getCookies, setExtraHTTPHeaders, setUserAgentOverride | response body retrieval, websocket frames |
| Fetch | enable, continueRequest, fulfillRequest, failRequest | full rules-based interception |
| Storage | getCookies, setCookies, deleteCookies | IndexedDB, storage events |
| Input | dispatchMouseEvent (hit-tested), dispatchKeyEvent, text selection / triple-click | dispatchTouchEvent (stubbed) |
| Browser | version, getWindowForTarget | — |
| LP | getMarkdown (DOM-to-Markdown, custom domain) | — |

`Page.printToPDF` and `Page.captureScreenshot` are explicitly unimplemented and return an explanatory error (there is no compositor or raster output — split the screenshot leg of a pipeline onto a real browser). The frame-ID convention (`frame_id == target_id`) for Playwright compatibility is still in place, and there are per-command CDP deadlines (`OBSCURA_CDP_COMMAND_TIMEOUT_MS`) so one wedged page cannot stall other sessions. `obscura-cdp/src/domains/*.rs` contains ~244 method-handler arms across the domains.

---

## MCP Server

New since v0.1.4 and expanded through v0.1.9: `obscura mcp` runs a Model Context Protocol server so an AI agent (Claude, Cursor, etc.) can drive the browser as a tool. It exposes **32 tools** (`browser_navigate`, `browser_snapshot`, `browser_click`, `browser_tab_open`, `browser_tab_switch`, and more), supports **multiple tabs / isolated pages**, and offers both **stdio and HTTP transports** (`obscura mcp` / `obscura mcp --http --host 0.0.0.0 --port ...`). The `--stealth` global flag applies here too.

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

It re-exports the interception types (`InterceptedRequest`, `InterceptResolution`, `RequestCallback`, `ResponseCallback`, `ResourceType`) so a Rust program can observe and modify traffic without going through CDP.

---

## Performance

The project's own benchmark numbers (README + the separate `obscura-benchmark` repo, described as 33 capability + speed stages) are consistent with the architecture. These are the maintainer's figures, not independently reproduced here:

| Operation | Obscura | Headless Chrome |
|---|---|---|
| Memory | ~30 MB | 200+ MB |
| Binary size | ~70 MB | 300+ MB |
| Startup | Instant (V8 snapshot) | ~2 s |
| Static HTML page load | ~51 ms | ~500 ms |
| JS + XHR + fetch | ~84 ms | ~800 ms |
| Dynamic scripts | ~78 ms | ~700 ms |

The savings come from skipping work a real browser performs: layout, style cascade, font shaping, image decode, raster, GPU compositor, and the surrounding Chromium infrastructure. The full suite (WPT conformance, an "obstacle course," a real-world corpus, and vs-Chrome speed) lives at `github.com/h4ckf0r0day/obscura-benchmark`; the numbers above have not been independently verified for this analysis.

For multi-URL workloads, `obscura scrape` runs `obscura-worker` child processes with a configurable concurrency limit, and `obscura serve --workers N` runs N CDP server child processes behind a TCP load balancer. `--v8-flags` can raise the V8 heap cap for JS-heavy pages.

---

## Pros and Cons

### Advantages

| Advantage | Description |
|---|---|
| Lightweight footprint | ~30 MB resident, ~70 MB binary, no Chrome / Node.js dependency |
| Fast startup | V8 snapshot brings per-runtime init to microseconds |
| Single-binary deployment | Cross-compiled releases: Linux x86_64 + aarch64, macOS Intel + ARM, Windows x86_64 |
| CDP API surface | 12 domains; compatible with `puppeteer-core` and `playwright-core` for common flows |
| Built-in MCP server | 32 tools, multi-tab, stdio + HTTP — drop-in for AI agents |
| Embeddable Rust library | `Browser::builder()` API + request/response interception |
| Coherent fingerprint persona | Windows / macOS / Linux profiles with matching UA, platform, UA-CH, GPU, timezone |
| Tracker blocking | 3,520-domain PGL list embedded at compile time |
| Multi-worker mode | Built-in process supervisor + TCP load balancer for parallel scraping |
| Optional TLS impersonation | `--features stealth` enables Chrome 145 (Windows) JA3 / JA4 via `wreq` |
| Robustness | V8 termination watchdogs, per-command deadlines, panic-safe DOM ops, SSRF / DNS-rebind guards |
| Clean Rust workspace | Eight small crates, readable code, deno_core foundation, Apache-2.0 throughout |

### Limitations

| Limitation | Description |
|---|---|
| No layout engine | External CSS is fetched but never applied as a cascade |
| No real rendering | No painting, no compositor, no GPU; `captureScreenshot` / `printToPDF` are unimplemented |
| Synthesized geometry | `getBoundingClientRect` returns a deterministic grid rect, not a real measured box |
| `getComputedStyle` is approximate | Inline styles + rect-derived dimensions + a defaults table; no cascade, some tell-y defaults |
| Canvas / WebGL are string stubs | `toDataURL` returns a fixed non-image; no real GL pipeline (`readPixels` = noise) |
| No real Service Workers / Web Workers DSP | Service worker and audio DSP are stubbed |
| Finite fingerprint pools | 12–13 GPUs per platform, 8 screens, 2 sample rates — aggregatable across many requests |
| Plugin list tell | Includes `"WebKit built-in PDF"`, not present in real Chrome |
| Single TLS profile in stealth mode | Chrome 145 Windows only; no rotation or alternative targets |
| Default build has no TLS impersonation | Needs `--features stealth`; release-CI stealth build is `continue-on-error` |
| wreq on pinned pre-release RCs | TLS impersonation depends on exact `wreq` RC pins that churn |
| Interception resource typing | v0.1.9 reports `"Fetch"` for JS-initiated requests; XHR not distinguished |

Resolved since the previous analysis: the license inconsistency (now Apache-2.0 everywhere), the hardcoded Linux `navigator.platform`, GPU-vs-platform inconsistency, `getBoundingClientRect` all-zeros, `event.isTrusted` always-true, static `hardwareConcurrency`/`deviceMemory`, and input ignoring coordinates.

---

## Installation & Usage

### Pre-built binaries

```bash
# Linux x86_64
curl -LO https://github.com/h4ckf0r0day/obscura/releases/latest/download/obscura-x86_64-linux.tar.gz
tar xzf obscura-x86_64-linux.tar.gz

# Linux aarch64, macOS (Intel + Apple Silicon), Windows x86_64 also published
# See the Releases page for exact asset names.
```

Also available via the Arch Linux AUR and as an official distroless Docker image (~57 MB).

### Build from source

```bash
git clone https://github.com/h4ckf0r0day/obscura.git
cd obscura
cargo build --release

# With TLS impersonation + tracker blocking
cargo build --release --features stealth
```

First build compiles V8 from source (several minutes); subsequent builds are cached.

### Fetch a page

```bash
obscura fetch https://example.com --eval "document.title"
obscura fetch https://example.com --dump links      # or: text | markdown | assets
obscura fetch https://example.com --wait-until networkidle0
obscura fetch https://example.com --stealth          # global flag; consistent fingerprint + blocking
```

### Start a CDP server

```bash
obscura serve --port 9222 --stealth
```

### Run the MCP server

```bash
obscura mcp                          # stdio transport (for local agents)
obscura mcp --http --host 0.0.0.0 --port 8080   # HTTP transport
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
```

---

## Comparison with Alternatives

| Dimension | Obscura | Patchright | Camoufox | CloakBrowser | Scrapling (HTTP tier) |
|---|---|---|---|---|---|
| Underlying engine | V8 + html5ever (no layout) | Real Chromium | Real Firefox | Real Chromium | curl_cffi |
| Renders pages | No | Yes | Yes | Yes | No |
| Real Canvas / WebGL | No (string stubs) | Yes | Yes (C++ noise) | Yes (C++ noise) | N/A |
| Fingerprint coherence | Per-platform profile (UA/GPU/tz agree) | Native | Native + BrowserForge | Native | N/A |
| TLS impersonation | Optional, single profile (`wreq`) | None | None | None | Yes, multiple profiles |
| Layout / `getComputedStyle` | Synthesized (no cascade) | Native | Native | Native | N/A |
| Memory footprint | ~30 MB | ~200 MB | ~200 MB | ~200 MB | ~10 MB |
| Stealth approach | JS-level shim + optional TLS | CDP protocol patches | C++ source patches | C++ source patches | TLS only |
| MCP server | Built-in (32 tools) | No | No | No | Yes (separate) |
| Detection ceiling | Basic → mid anti-bot | Enterprise anti-bot | Enterprise anti-bot | Enterprise anti-bot | High for HTTP-only targets |

Obscura sits between an HTTP-only client like `curl_cffi` (very fast, no JS) and a real headless Chromium fork (heavy, real fingerprints). It runs JavaScript that pure HTTP clients cannot, while remaining far lighter than any actual browser, and it now presents an internally coherent fingerprint — but it still cannot produce the real render/layout output that high-end anti-bots probe.

---

## Anti-Bot Service Coverage

| Service | Verdict | Reasoning |
|---|:---:|---|
| Static HTML behind UA filter | ✅ | UA, headers, and UA-CH look like Chrome and agree with each other |
| Cloudflare WAF (free tier) | ⚠️ | Stealth-mode TLS + coherent persona help; interactive challenges break on missing render/canvas |
| Cloudflare Turnstile | ❌ | Requires real canvas / WebGL / audio |
| DataDome | ❌ | Real render pixels, audio DSP, and layout probes not satisfiable |
| Akamai Bot Manager | ❌ | Sensor data uses real input timing + layout |
| PerimeterX / HUMAN | ❌ | Behavioral and layout-aware |
| Kasada | ❌ | Heavy on canvas / WebGL |
| Imperva | ❌ | Layout and rendering checks |
| reCAPTCHA v3 | ❌ | Score depends on real browser signals |
| Sannysoft basic checks | ✅ | Passes `webdriver`, plugins, languages, UA-CH consistency |
| Sannysoft layout-aware checks | ⚠️ | `getBoundingClientRect` now returns non-zero synthesized rects, but they are not real measurements |

Legend: ✅ Reliably bypasses · ⚠️ Partial / conditional · ❌ Not effective.

Note: the v0.1.9 release notes claim "creepjs reports 0% detection." That is the maintainer's result and is plausible for CreepJS's consistency-oriented checks now that the persona is coherent — but CreepJS is a consistency auditor, not a commercial anti-bot, and this analysis did not reproduce the run. Treat it as an internal-consistency pass, not evidence of bypassing DataDome/Kasada-class systems.

---

## When to Use

### Best For
- Scraping server-rendered HTML at high concurrency where memory and startup time are the bottlenecks
- Sites with light-to-moderate protection (UA/TLS filters, basic JS challenges) that don't require real rendering
- CDP-driven prototypes and AI-agent tool use (via the built-in MCP server) without installing Chrome
- Embedding a browser in a Rust service (the `obscura` crate) with request interception
- JavaScript-driven content where the JS extracts data rather than measuring real layout/render output

### Not Ideal For
- Sites protected by enterprise anti-bot services (Turnstile, DataDome, Akamai, Kasada, Imperva)
- Anything visual: screenshots, PDF rendering, video playback, image decoding
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

Obscura is a **from-scratch headless browser engine** that uses V8 for JavaScript execution and html5ever for HTML parsing, with a large JavaScript shim providing `navigator`, `document`, `window`, and the rest of the browser globals. It is a careful piece of Rust engineering that delivers genuine performance gains over headless Chrome by skipping layout, rendering, and the surrounding browser infrastructure — and, as of v0.1.9, it now ships an embeddable Rust library, a 32-tool MCP server, and request/response interception.

The v0.1.x line has meaningfully raised the stealth floor since the first analysis: the persona is now Windows/Chrome-by-default and internally coherent (UA ↔ platform ↔ UA-CH ↔ GPU renderer ↔ timezone), `event.isTrusted` and `getBoundingClientRect` behave correctly, input events hit-test, and TLS impersonation ships in release binaries. But the architectural ceiling is unchanged: there is no real layout, no real canvas/WebGL/audio output, and finite fingerprint pools. It clears consistency-oriented auditors and basic-to-moderate defenses; it does not clear the render/behavior-aware checks that DataDome/Kasada/Akamai-class systems run.

**Effectiveness Rating:** Moderate — coherent persona + optional TLS clear basic/consistency checks; real render/layout/audio probes still fail

**Complexity:** Low — single binary, CDP server, MCP server, embeddable crate; drop-in for Puppeteer / Playwright clients

**Best Use Case:** Lightweight, high-concurrency scraping of server-rendered HTML or lightly-protected sites, and AI-agent browsing via MCP

*Verified against the source at `github.com/h4ckf0r0day/obscura` @ v0.1.9, as of 2026-07.*
