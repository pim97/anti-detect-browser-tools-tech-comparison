# Obscura - Deep Technical Analysis

> **Tool Type:** Custom Headless Browser Engine (built from scratch in Rust)
> **Repository:** [github.com/h4ckf0r0day/obscura](https://github.com/h4ckf0r0day/obscura)
> **Approach:** V8 runtime + html5ever DOM tree + JavaScript shim + optional TLS impersonation
> **Language:** Rust (CLI / engine), Puppeteer / Playwright clients (any language) via CDP
> **Effectiveness:** Moderate (basic detection bypass; weak against fingerprint-aware anti-bots)
> **Maintenance:** Active development (v0.1.0, license declared as both Apache 2.0 and MIT in different files)

---

## Table of Contents

- [What is Obscura?](#what-is-obscura)
- [How It Works](#how-it-works)
- [Anti-Detection Mechanisms](#anti-detection-mechanisms)
- [Network Layer & Stealth Mode](#network-layer--stealth-mode)
- [CDP Implementation](#cdp-implementation)
- [Performance](#performance)
- [Pros and Cons](#pros-and-cons)
- [Installation & Usage](#installation--usage)
- [Comparison with Alternatives](#comparison-with-alternatives)
- [When to Use](#when-to-use)

---

## What is Obscura?

Obscura is an **open-source headless browser engine written in Rust**, built specifically for web scraping and AI agent automation. It runs JavaScript via V8 (through the `deno_core` crate) and exposes a Chrome DevTools Protocol server so it can be driven by Puppeteer or Playwright clients.

**Key differentiator:** Unlike every other tool analyzed in this repository, Obscura is not a patched, forked, or wrapped version of Chrome or Firefox. It is a **from-scratch engine** that reimplements just enough of the browser surface to run JavaScript against an HTML document.

**Important caveat:** Obscura is not a full browser. It contains no layout engine, no CSS cascade, no compositor, no GPU rasterization, and no real Canvas / WebGL / audio implementations. CSS files are fetched but stored as a string variable and never applied. This is what makes it lightweight (≈30 MB binary, ≈85 ms page load), and what limits its effectiveness against anti-bot systems that probe layout, rendering, or fingerprinting APIs.

---

## How It Works

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                       OBSCURA ARCHITECTURE                           │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌──────────────────┐    ┌──────────────────────┐                   │
│  │  obscura-cli     │    │  obscura-cdp          │                   │
│  │  fetch / scrape  │    │  WebSocket CDP server │                   │
│  │  /serve commands │    │  (~9 domains)         │                   │
│  └────────┬─────────┘    └─────────┬────────────┘                   │
│           │                        │                                 │
│           ▼                        ▼                                 │
│  ┌──────────────────────────────────────────────┐                   │
│  │             obscura-browser (Page)            │                   │
│  │  Navigation + lifecycle + script orchestration│                   │
│  └────┬──────────────────┬──────────────┬───────┘                   │
│       │                  │              │                            │
│       ▼                  ▼              ▼                            │
│  ┌──────────┐    ┌──────────────┐  ┌──────────────┐                │
│  │ obscura- │    │ obscura-js   │  │ obscura-net  │                │
│  │ dom      │    │              │  │              │                │
│  │          │    │ V8 +         │  │ reqwest      │                │
│  │ html5    │    │ deno_core    │  │ (default)    │                │
│  │ ever     │    │ + 3,035-line │  │ + wreq       │                │
│  │ DOM      │    │ bootstrap.js │  │ (--features  │                │
│  │ tree     │    │ (DOM shim    │  │   stealth,   │                │
│  │ + CSS    │    │  in JS)      │  │   Chrome 145 │                │
│  │ selectors│    │              │  │   TLS)       │                │
│  └──────────┘    └──────────────┘  └──────────────┘                │
│                                                                      │
│  Supporting: 3,520-domain tracker blocklist (PGL list)              │
│              CookieJar, robots.txt cache, proxy support             │
└─────────────────────────────────────────────────────────────────────┘
```

The repository is a Cargo workspace of six crates:

| Crate | Approx. LOC | Responsibility |
|---|---:|---|
| `obscura-cli` | ~700 | clap-based CLI (`fetch`, `scrape`, `serve`) + multi-worker TCP load balancer |
| `obscura-cdp` | ~1,800 | WebSocket server speaking the Chrome DevTools Protocol |
| `obscura-browser` | ~970 | `Page` abstraction: navigation, subresource fetching, script execution |
| `obscura-net` | ~600 | HTTP client (reqwest baseline + optional `wreq` for TLS impersonation) |
| `obscura-js` | ~2,200 Rust + 3,035 JS | V8 runtime via `deno_core` + bootstrap.js DOM shim |
| `obscura-dom` | ~600 | html5ever-backed DOM tree + `selectors` crate for CSS queries |

### Page Lifecycle

When `obscura fetch <url>` runs, the `navigate_single` function ([page.rs:424](https://github.com/h4ckf0r0day/obscura/blob/main/crates/obscura-browser/src/page.rs)) executes:

```
1. validate_url()                  reject private IPs, localhost, non-http schemes
2. (optional) robots.txt           fetch and check if --obey-robots
3. http_client.fetch()             reqwest (or wreq if stealth feature)
4. parse_html()                    html5ever produces a DomTree
5. extract <link rel=stylesheet>   fetch all CSS in parallel
                                   stored in globalThis.__obscura_css as a string
6. init V8 runtime                 load bootstrap.js (V8 snapshot)
7. classify <script> tags          regular / defer / async / module
8. fetch + execute scripts         js.execute_script_guarded() per script
9. (optional) network idle wait    5-second timeout, 500 ms idle window
10. dump HTML / text / links / eval result
```

Two consequences of this pipeline are worth flagging:

- **CSS is never applied.** It is fetched and exposed as a string in `globalThis.__obscura_css` ([page.rs:570](https://github.com/h4ckf0r0day/obscura/blob/main/crates/obscura-browser/src/page.rs)). There is no cascade, specificity resolution, or computed style. JavaScript that reads `getComputedStyle` will get stub values.
- **Layout is not computed.** `Element.prototype.getBoundingClientRect` returns `{x:0, y:0, width:0, height:0, top:0, right:0, bottom:0, left:0}` for every element ([bootstrap.js:1998](https://github.com/h4ckf0r0day/obscura/blob/main/crates/obscura-js/js/bootstrap.js)).

### V8 Snapshotting

`obscura-js` builds a V8 startup snapshot at compile time so that per-page initialization is microseconds rather than milliseconds. The bootstrap script is included via `include_str!("../js/bootstrap.js")` and executed via `runtime.execute_script("<obscura:init>", "globalThis.__obscura_init();")` on each new runtime instance.

---

## Anti-Detection Mechanisms

All anti-detection lives in `crates/obscura-js/js/bootstrap.js`. There are no C++ or binary-level patches — every override is JavaScript executed before any page script runs.

### `navigator` overrides

```javascript
// bootstrap.js:1043-1123
globalThis.navigator = {
  get userAgent() { return globalThis.__obscura_ua || "Mozilla/5.0 (X11; Linux x86_64) ... Chrome/145.0.0.0 ..."; },
  language: "en-US", languages: ["en-US","en"], platform: "Linux x86_64",
  hardwareConcurrency: 8, deviceMemory: 8,
  get webdriver() { return undefined; },
  userAgentData: {
    brands: [{brand:"Google Chrome",version:"145"}, {brand:"Chromium",version:"145"}, {brand:"Not=A?Brand",version:"24"}],
    mobile: false, platform: "Linux",
    getHighEntropyValues(hints) { return Promise.resolve({ /* full UA-CH payload */ }); },
  },
  plugins: [ /* 5 PDF-viewer entries */ ],
  // ... mediaDevices, getBattery, permissions, etc.
}
```

What it covers:
- `navigator.webdriver` returns `undefined` (matches real Chrome)
- Full `navigator.userAgentData` with `getHighEntropyValues` payload
- Plugin and mimeType lists matching modern Chrome
- Faked `getBattery` using per-session randomized values

What is hardcoded and may be detectable:
- `navigator.platform: "Linux x86_64"` is fixed regardless of the OS the binary runs on.
- `hardwareConcurrency: 8` and `deviceMemory: 8` are static.
- `userAgentData.platformVersion: "6.8.0"` is static.
- The plugin list includes a `"WebKit built-in PDF"` entry, which does not appear in real Chrome.

### `Function.prototype.toString` masking

```javascript
// bootstrap.js:30-39
const _nativeFns = new Set();
const _origToString = Function.prototype.toString;
Function.prototype.toString = function() {
  if (_nativeFns.has(this)) return `function ${this.name || ''}() { [native code] }`;
  return _origToString.call(this);
};
function _markNative(fn) { if (typeof fn === 'function') _nativeFns.add(fn); return fn; }
```

About 80 functions are marked as native via `_markNative(...)`. This handles the common `Function.prototype.toString().includes('[native code]')` check. Detectors that compare `Function.prototype.toString.toString()` (the masking function itself reporting as native) can still observe the override.

### Per-session fingerprint randomization

```javascript
// bootstrap.js:62-116
let _fpSeed = 0;
function _fpRand(salt) { /* xorshift over _fpSeed */ }

const gpuPool = [
  'ANGLE (NVIDIA, NVIDIA GeForce RTX 3060 Direct3D11 vs_5_0 ps_5_0, D3D11)',
  'ANGLE (Intel, Intel(R) UHD Graphics 630 Direct3D11 vs_5_0 ps_5_0, D3D11)',
  // ... 12 entries total, all Direct3D11 / D3D11
];
const screenPool = [[1920,1080],[2560,1440],[1366,768],[1536,864],[1440,900],[1680,1050],[1280,720],[3840,2160]];
```

`__obscura_init` re-seeds with `Date.now() ^ (Math.random() * 0xFFFFFFFF)` so each new V8 runtime instance hits a different pool entry. The pools cover GPU strings (12), screens (8), audio sample rates (2), and randomized compressor / battery values.

Observations:
- The 12 GPU strings all reference `Direct3D11`. If `navigator.platform` reports `"Linux x86_64"`, real Linux Chrome would expose OpenGL ANGLE strings, not Direct3D11. A consistency-checking detector flags this.
- `WebGL.getParameter` returns `"WebKit WebGL"` for the renderer constant ([bootstrap.js:2406](https://github.com/h4ckf0r0day/obscura/blob/main/crates/obscura-js/js/bootstrap.js)), which is a Safari string rather than Chrome.
- The pool size is small enough that a detector aggregating values across requests can recognize the distribution.

### Canvas

```javascript
// bootstrap.js:99-101, 2434-2455
let cfp = 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUg';
for (let i = 0; i < 40; i++) cfp += chars[Math.floor(_fpRand(500 + i) * 64)];
cfp += '==';
// ...
Element.prototype.toDataURL = function(type) { return _fp('canvasFingerprint'); };
```

`toDataURL` returns a fixed-per-session string starting with a real PNG header, but the bytes after are random base64 characters and do not decode to a valid image. There is no underlying canvas rasterizer. Anti-bot scripts that decode the data URL or compare it against known reference outputs will see a non-image.

### Audio

```javascript
// bootstrap.js:2535-2559
globalThis.AudioContext = class AudioContext {
  constructor() { this.sampleRate=_fp('audioSampleRate'); this.baseLatency=_fp('audioBaseLatency'); ... }
  createDynamicsCompressor() { return {threshold:{value:_fp('compThreshold')}, ...}; }
  createAnalyser() { return { getByteFrequencyData(a) { for(let i=0;i<a.length;i++) a[i]=Math.floor(_fpRand(600+i)*10); }, ... }; }
};
```

Audio context, compressor parameters, and analyser data are all synthetic. There is no real digital signal processing. Audio fingerprinters that run a real DSP graph and hash the output will get values that don't match any real Chrome.

### `event.isTrusted`

```javascript
// bootstrap.js:1839-1840
class Event {
  constructor(t,o={}) { ... }
  get isTrusted() { return true; }
}
```

`isTrusted` is the browser's signal that an event came from real user input rather than `dispatchEvent`. Setting it to `true` for all events — including ones explicitly created via `new MouseEvent(...)` — is a known anti-bot tell.

### Mouse and keyboard input

```rust
// crates/obscura-cdp/src/domains/input.rs
"mousePressed" => {
    var target = globalThis.__obscura_click_target || document.activeElement || document.body;
    var click = new MouseEvent('click', {clientX: x, clientY: y});
    target.dispatchEvent(click);
}
```

Mouse coordinates passed by Puppeteer or Playwright are not used for hit testing. The dispatched event carries `clientX` / `clientY`, but the *target* is `__obscura_click_target` (set by the JS layer when a selector is resolved) or `document.activeElement`. This works correctly for `await page.click('selector')` flows but breaks scenarios that require hit testing at coordinates. Combined with `getBoundingClientRect` returning all-zeros, anti-bot scripts that verify click geometry against element bounds will detect inconsistency.

---

## Network Layer & Stealth Mode

### Default build (no feature flags)

The HTTP client is `reqwest` with `native-tls-vendored`. Chrome-shaped headers are added manually:

```rust
// crates/obscura-net/src/client.rs:285-330
headers.insert(USER_AGENT, ...);
headers.insert("sec-ch-ua", "\"Google Chrome\";v=\"145\", ...");
headers.insert("sec-ch-ua-mobile", "?0");
headers.insert("sec-ch-ua-platform", "\"Linux\"");
headers.insert("sec-fetch-dest", "document");
headers.insert("upgrade-insecure-requests", "1");
// ...
```

The headers look like Chrome, but the TLS handshake is whatever `native-tls` produces. JA3 / JA4 fingerprints will match a Rust HTTP client, not Chrome. CDNs that compare TLS fingerprint against User-Agent can detect the mismatch.

### `--features stealth` build

```rust
// crates/obscura-net/src/wreq_client.rs
let emulation_opts = wreq_util::EmulationOption::builder()
    .emulation(wreq_util::Emulation::Chrome145)
    .emulation_os(wreq_util::EmulationOS::Linux)
    .build();
```

`wreq` is a TLS impersonation library similar to `curl_cffi`. With this feature enabled, JA3 / JA4 fingerprints match Chrome 145 on Linux. The profile is hardcoded — there is no rotation, no per-session variation, and no other emulation targets. Pre-built release binaries that aren't compiled with `--features stealth` fall back to the default `reqwest` client.

### Tracker blocking

```rust
// crates/obscura-net/src/blocklist.rs
const PGL_LIST: &str = include_str!("pgl_domains.txt");  // 3,520 domains
```

Peter Lowe's tracker domain list is embedded at compile time. Lookup is exact match plus suffix match (so `www.google-analytics.com` matches `google-analytics.com`). When a script or subresource references a blocked domain, it is never fetched. This is privacy hygiene rather than stealth — it speeds up loads and prevents fingerprinting scripts from running, but doesn't itself disguise the client.

---

## CDP Implementation

`obscura-cdp` implements a subset of the Chrome DevTools Protocol sufficient to support Puppeteer and Playwright clients connecting via `connectOverCDP` / `puppeteer.connect`.

| Domain | Implemented Methods | Notable Gaps |
|---|---|---|
| Target | createTarget, closeTarget, attachToTarget, createBrowserContext | targetCrashed events |
| Page | navigate, getFrameTree, addScriptToEvaluateOnNewDocument, lifecycleEvents | captureScreenshot (no rendering), printToPDF |
| Runtime | evaluate, callFunctionOn, getProperties, addBinding | exception details, async stack traces |
| DOM | getDocument, querySelector, querySelectorAll, getOuterHTML, resolveNode | layout queries |
| Network | enable, setCookies, getCookies, setExtraHTTPHeaders, setUserAgentOverride | response body retrieval, websocket frames |
| Fetch | enable, continueRequest, fulfillRequest, failRequest | rules-based interception |
| Storage | getCookies, setCookies, deleteCookies | IndexedDB, localStorage events |
| Input | dispatchMouseEvent, dispatchKeyEvent | hit testing, modifier state, dispatchTouchEvent (stubbed) |
| LP | getMarkdown (DOM-to-Markdown, custom domain) | — |

The frame-ID convention deliberately sets `frame_id == target_id` ([page.rs:49-54](https://github.com/h4ckf0r0day/obscura/blob/main/crates/obscura-browser/src/page.rs)) for Playwright compatibility, with an inline comment explaining the rationale. This indicates the implementation has been tested against real Playwright clients.

`Page.captureScreenshot` is unimplemented because there is nothing to render — there is no compositor or raster output.

---

## Performance

The README's benchmark numbers are consistent with the architecture:

| Operation | Obscura | Headless Chrome |
|---|---|---|
| Memory | ~30 MB | 200+ MB |
| Binary size | ~70 MB | 300+ MB |
| Startup | Instant (V8 snapshot) | ~2 s |
| Static HTML page load | ~51 ms | ~500 ms |
| JS + XHR + fetch | ~84 ms | ~800 ms |

The savings come from skipping work a real browser performs: layout, style cascade, font shaping (HarfBuzz), image decode, raster, GPU compositor, and the surrounding Chromium infrastructure.

For multi-URL workloads, `obscura scrape` spawns child worker processes (`obscura-worker` binary) and communicates over stdin / stdout with a JSON protocol, with a configurable concurrency limit. `obscura serve --workers N` runs N CDP server child processes behind a TCP load balancer.

---

## Pros and Cons

### Advantages

| Advantage | Description |
|---|---|
| Lightweight footprint | ~30 MB resident, ~70 MB binary, no Chrome / Node.js dependency |
| Fast startup | V8 snapshot brings per-runtime init to microseconds |
| Single-binary deployment | Cross-compiled releases for Linux x86_64, macOS (Intel + ARM), Windows |
| CDP API surface | Compatible with `puppeteer-core` and `playwright-core` for common flows |
| Tracker blocking | 3,520-domain PGL list embedded at compile time |
| Multi-worker mode | Built-in process supervisor + TCP load balancer for parallel scraping |
| Optional TLS impersonation | `--features stealth` enables Chrome 145 JA3 / JA4 via `wreq` |
| Clean Rust workspace | Six small crates, readable code, deno_core foundation |

### Limitations

| Limitation | Description |
|---|---|
| No layout engine | CSS is fetched but never applied; `getComputedStyle` returns stubs |
| No real rendering | No painting, no compositor, no GPU; `captureScreenshot` is unimplemented |
| `getBoundingClientRect` returns zeros | Any script depending on element geometry sees `{0,0,0,0,...}` |
| Canvas / WebGL are stubs | `toDataURL` returns a fixed string; WebGL renderer reports `"WebKit WebGL"` |
| No real Service Workers / Web Workers | All stubbed as no-ops |
| Hit testing absent in input | Mouse `(x,y)` coordinates are not used to resolve targets |
| Hardcoded `navigator.platform` | Reports `"Linux x86_64"` regardless of host OS |
| GPU strings inconsistent with platform | All ANGLE entries reference Direct3D11 |
| Default build has no TLS impersonation | Without `--features stealth`, JA3 / JA4 looks like a Rust HTTP client |
| Single TLS profile in stealth mode | Chrome 145 Linux only; no rotation or alternative targets |
| Pool sizes for fingerprints are small | 12 GPUs, 8 screens, 2 sample rates |
| `event.isTrusted` always `true` | Including for events created via `new MouseEvent(...)` |
| License inconsistency | LICENSE file says Apache 2.0; `Cargo.toml` declares MIT |

---

## Installation & Usage

### Pre-built binaries

```bash
# Linux x86_64
curl -LO https://github.com/h4ckf0r0day/obscura/releases/latest/download/obscura-x86_64-linux.tar.gz
tar xzf obscura-x86_64-linux.tar.gz

# macOS Apple Silicon
curl -LO https://github.com/h4ckf0r0day/obscura/releases/latest/download/obscura-aarch64-macos.tar.gz

# Windows: download .zip from the releases page
```

### Build from source

```bash
git clone https://github.com/h4ckf0r0day/obscura.git
cd obscura
cargo build --release

# With TLS impersonation + tracker blocking
cargo build --release --features stealth
```

Requires Rust 1.75+. First build takes about five minutes because V8 compiles from source; subsequent builds are cached.

### Fetch a page

```bash
obscura fetch https://example.com --eval "document.title"
obscura fetch https://example.com --dump links
obscura fetch https://example.com --wait-until networkidle0
```

### Start a CDP server

```bash
obscura serve --port 9222 --stealth
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

const browser = await chromium.connectOverCDP({
  endpointURL: 'ws://127.0.0.1:9222',
});
const page = await browser.newContext().then(ctx => ctx.newPage());
await page.goto('https://example.com');
await browser.close();
```

### Parallel scraping

```bash
obscura scrape url1 url2 url3 \
  --concurrency 25 \
  --eval "document.querySelector('h1').textContent" \
  --format json
```

---

## Comparison with Alternatives

| Dimension | Obscura | Patchright | Camoufox | CloakBrowser | Scrapling (HTTP tier) |
|---|---|---|---|---|---|
| Underlying engine | V8 + html5ever (no layout) | Real Chromium | Real Firefox | Real Chromium | curl_cffi |
| Renders pages | No | Yes | Yes | Yes | No |
| Real Canvas / WebGL | No (stubs) | Yes | Yes (C++ noise) | Yes (C++ noise) | N/A |
| TLS impersonation | Optional, single profile | None | None | None | Yes, multiple profiles |
| Layout / `getComputedStyle` | Not implemented | Native | Native | Native | N/A |
| Memory footprint | ~30 MB | ~200 MB | ~200 MB | ~200 MB | ~10 MB |
| Stealth approach | JS-level shim | CDP protocol patches | C++ source patches | C++ source patches | TLS only |
| Detection ceiling | Basic anti-bot | Enterprise anti-bot | Enterprise anti-bot | Enterprise anti-bot | High for HTTP-only targets |

Obscura sits between an HTTP-only client like `curl_cffi` (very fast, no JS) and a real headless Chromium fork (heavy, real fingerprints). It runs JavaScript that pure HTTP clients cannot, while remaining far lighter than any actual browser.

---

## Anti-Bot Service Coverage

| Service | Verdict | Reasoning |
|---|:---:|---|
| Static HTML behind UA filter | ✅ | UA and headers look like Chrome |
| Cloudflare WAF (free tier) | ⚠️ | Stealth mode TLS helps; managed challenges may break on missing layout / canvas |
| Cloudflare Turnstile | ❌ | Requires real canvas / WebGL / audio |
| DataDome | ❌ | Cross-checks GPU vs platform, BoundingClientRect, audio DSP |
| Akamai Bot Manager | ❌ | Sensor data uses real input timing + layout |
| PerimeterX / HUMAN | ❌ | Behavioral and layout-aware |
| Kasada | ❌ | Heavy on canvas / WebGL |
| Imperva | ❌ | Layout and rendering checks |
| reCAPTCHA v3 | ❌ | Score depends on real browser signals |
| Sannysoft basic checks | ✅ | Passes `webdriver`, plugins, languages |
| Sannysoft layout-aware checks | ❌ | `getBoundingClientRect` returns zeros |

Legend: ✅ Reliably bypasses · ⚠️ Partial / conditional · ❌ Not effective.

---

## When to Use

### Best For
- Scraping server-rendered HTML at high concurrency where memory and startup time are bottlenecks
- Sites with light protection (UA filters, basic JS challenges) that don't run fingerprint-aware scripts
- Quick CDP-driven prototypes without installing Chrome
- Disposable workers (one URL per process) where TLS fingerprint reuse isn't a concern
- JavaScript-driven content where the JS does data extraction rather than DOM measurement

### Not Ideal For
- Sites protected by enterprise anti-bot services (Cloudflare Turnstile, DataDome, Akamai, Kasada)
- Pages whose JS calls `getComputedStyle`, `getBoundingClientRect`, or expects layout to actually run
- Anything visual: screenshots, PDF rendering, video playback, image decoding
- Sites that rely on Service Workers or Web Workers
- High-volume scraping where TLS fingerprint diversity is needed
- Use cases where the User-Agent claim must accurately reflect the client (compliance / legal contexts)

---

## Resources

- [GitHub Repository](https://github.com/h4ckf0r0day/obscura)
- [deno_core](https://github.com/denoland/deno_core) — V8 runtime crate used by Obscura
- [wreq](https://crates.io/crates/wreq) — TLS impersonation library used in stealth mode
- [html5ever](https://github.com/servo/html5ever) — HTML parser used for the DOM tree

---

## Summary

Obscura is a **from-scratch headless browser engine** that uses V8 for JavaScript execution and html5ever for HTML parsing, with a JavaScript shim providing the `navigator`, `document`, `window`, and other browser globals. It is a careful piece of Rust engineering that delivers genuine performance gains over headless Chrome by skipping layout, rendering, and the surrounding browser infrastructure.

The trade-off is that the same architectural choices that make it fast also limit its anti-detection ceiling. The stealth surface covers the obvious checks (`navigator.webdriver`, UA-CH, plugin list, function masking, per-session randomization) but does not extend to the layers anti-bot vendors actually probe at the high end: real layout, real canvas / WebGL output, audio DSP, and consistency between GPU strings and platform.

**Effectiveness Rating:** Moderate — passes basic detection, fails layout / canvas-aware probes

**Complexity:** Low — single binary, CDP server, drop-in for Puppeteer / Playwright clients

**Best Use Case:** Lightweight, high-concurrency scraping of server-rendered HTML or lightly-protected sites
