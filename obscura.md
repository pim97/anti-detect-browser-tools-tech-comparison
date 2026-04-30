# Obscura - Technical Deep Dive

> **Sponsored by [Scrappey.com](https://scrappey.com/)** — Anti-bot bypass API that handles Cloudflare, DataDome, and more without you having to read 3,000 lines of bootstrap JavaScript.

[GitHub](https://github.com/h4ckf0r0day/obscura) · Apache-2.0 (workspace says MIT) · Rust workspace · ~8k LOC

---

## TL;DR

Obscura is **not a browser** in the way Chromium, Firefox, or even WebKit are browsers. It's a **V8 runtime + html5ever DOM tree + a 3,000-line JavaScript shim that pretends to be Chrome 145**. There is no layout engine, no CSS cascade, no compositor, no GPU. Pages don't render — they get parsed, their `<script>` tags get fetched and executed against a fake DOM, and the result is dumped or exposed via a partial CDP server.

That is precisely why it's fast (30 MB, 85 ms page loads). It's also precisely why the README's "drop-in replacement for headless Chrome" claim is misleading: any site that runs real fingerprinting against `getBoundingClientRect`, `getComputedStyle`, real WebGL, or Service Workers will see straight through it.

**Stealth maturity:** Cosmetic. The surface is wide (UA-CH, plugin list, battery, GPU strings, canvas fingerprint, audio params) but riddled with internal contradictions a basic detector will spot.

---

## What It Actually Is

A Rust workspace with six crates:

| Crate | Lines | Job |
|---|---:|---|
| `obscura-cli` | ~700 | clap-based CLI (`fetch`, `scrape`, `serve`) + multi-worker load balancer |
| `obscura-cdp` | ~1,800 | Tokio WebSocket server speaking Chrome DevTools Protocol |
| `obscura-browser` | ~970 | "Page" abstraction — navigate, fetch subresources, run scripts |
| `obscura-net` | ~600 | HTTP client (reqwest baseline + optional `wreq` for TLS impersonation) |
| `obscura-js` | ~2,200 (Rust) + 3,035 (JS) | V8 runtime (deno_core) + bootstrap.js DOM shim |
| `obscura-dom` | ~600 | html5ever-backed DOM tree + selectors-crate query engine |

Build:
```bash
cargo build --release                         # baseline
cargo build --release --features stealth      # adds wreq + tracker blocking
```

The `stealth` feature flag is the only thing that gives you Chrome-like TLS fingerprints. **Pre-built release binaries that aren't compiled with this flag have a `reqwest`-shaped JA3/JA4** — i.e., they look like a Rust HTTP client, not Chrome.

---

## Architecture: The Rendering Pipeline (or lack thereof)

Here's what `obscura fetch <url>` actually does, in order ([page.rs:424-638](https://github.com/h4ckf0r0day/obscura/blob/main/crates/obscura-browser/src/page.rs)):

```
1. validate_url()          → reject private IPs / localhost / non-http schemes
2. (optional) robots.txt   → fetch + check
3. http_client.fetch()     → reqwest GET (or wreq if stealth)
4. parse_html()            → html5ever → DomTree (Rust)
5. extract <link rel=stylesheet> → fetch all CSS in parallel
   ⚠️ CSS is then stuffed into globalThis.__obscura_css as a string.
   That's it. No cascade, no specificity, no computed style.
6. init V8 runtime         → load bootstrap.js (snapshot-cached)
7. extract <script> tags   → classify regular/defer/async/module
8. fetch + execute scripts → V8.execute_script() per script
9. (optional) wait for network idle → 5s timeout, 500ms idle window
10. dump HTML / text / links / eval result
```

What's missing vs. a real browser: **layout, painting, hit testing, GPU rasterization, font shaping, image decoding, video, audio playback, real WebGL, real Canvas, Service Workers, Web Workers, IndexedDB, WebRTC, WebSockets-from-page, push notifications.** Many of these have JS-side stubs that resolve `Promise.reject` or return empty objects, but nothing functional behind them.

This is fine — *if* the target site is server-rendered HTML and the JS you care about is just data extraction or simple SPA hydration. It is not fine if the site does anything visual or fingerprint-aware.

---

## The Stealth Surface

### Where it lives

`crates/obscura-js/js/bootstrap.js`. This file is compiled into a V8 startup snapshot at build time (`build.rs`) so per-page init is microseconds, not milliseconds.

### `navigator` ([bootstrap.js:1043-1123](https://github.com/h4ckf0r0day/obscura/blob/main/crates/obscura-js/js/bootstrap.js))

```javascript
globalThis.navigator = {
  get userAgent() { return globalThis.__obscura_ua || "Mozilla/5.0 (X11; Linux x86_64) ... Chrome/145.0.0.0 ..."; },
  language: "en-US", languages: ["en-US","en"], platform: "Linux x86_64",
  hardwareConcurrency: 8, deviceMemory: 8,
  get webdriver() { return undefined; },
  userAgentData: { brands: [{brand:"Google Chrome",version:"145"}, ...], platform: "Linux", ... },
  // plugins, mimeTypes, mediaDevices, getBattery, etc. — all faked
}
```

Solid coverage of the basic detection surface. **Two giveaways:**
- **`navigator.platform: "Linux x86_64"`** is hardcoded. The macOS/Windows release binaries report Linux to JS unless you override `--user-agent` *and* nothing else queries `platform`.
- **`hardwareConcurrency: 8` / `deviceMemory: 8`** are static. Real devices vary.

### Function masking ([bootstrap.js:30-39](https://github.com/h4ckf0r0day/obscura/blob/main/crates/obscura-js/js/bootstrap.js))

```javascript
const _nativeFns = new Set();
Function.prototype.toString = function() {
  if (_nativeFns.has(this)) return `function ${this.name || ''}() { [native code] }`;
  return _origToString.call(this);
};
```

Standard `[native code]` masking. Calls `_markNative(...)` against ~80 functions. Decent coverage but `Function.prototype.toString.toString()` returning `[native code]` is itself the masking — which detectors check by patching `Function.prototype.toString` and seeing if the patched version reports as native. Fixable but not currently fixed here.

### Per-session fingerprint ([bootstrap.js:62-116](https://github.com/h4ckf0r0day/obscura/blob/main/crates/obscura-js/js/bootstrap.js))

```javascript
let _fpSeed = 0;
function _fpRand(salt) { /* xorshift over _fpSeed */ }

// Pools the seed picks from:
const gpuPool = [
  'ANGLE (NVIDIA, NVIDIA GeForce RTX 3060 Direct3D11 vs_5_0 ps_5_0, D3D11)',
  'ANGLE (Intel, Intel(R) UHD Graphics 630 Direct3D11 vs_5_0 ps_5_0, D3D11)',
  // ... 12 entries total, all Direct3D11
];
const screenPool = [[1920,1080],[2560,1440],[1366,768], /* ...8 total */];
```

Then `__obscura_init` re-seeds with `Date.now() ^ (Math.random() * 0xFFFFFFFF)` so each page session gets a different point in the pool. Solid idea, but:

- **`Direct3D11` GPU strings on a process advertising `navigator.platform: "Linux x86_64"` is an instant inconsistency.** Real Linux Chrome reports `OpenGL` ANGLE strings. Any detector cross-referencing GPU + platform flags this immediately.
- **Pool is 12 entries.** Cheap to fingerprint — repeated visits from the same Obscura instance hit one of 12 GPUs at random. Statistical detection over a few requests is trivial.
- `WebGLRenderingContext` itself is `class WebGLRenderingContext {}` — empty. The renderer returns `"WebKit WebGL"` for `GL_RENDERER` ([bootstrap.js:2406](https://github.com/h4ckf0r0day/obscura/blob/main/crates/obscura-js/js/bootstrap.js)), which is a Safari string, not Chrome.

### Canvas ([bootstrap.js:99-101, 2434-2455](https://github.com/h4ckf0r0day/obscura/blob/main/crates/obscura-js/js/bootstrap.js))

```javascript
let cfp = 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUg';
for (let i = 0; i < 40; i++) cfp += chars[Math.floor(_fpRand(500 + i) * 64)];
cfp += '==';
// ...
Element.prototype.toDataURL = function(type) { return _fp('canvasFingerprint'); };
```

This is **not canvas fingerprint protection**, it's a fixed string masquerading as a PNG. The base64 prefix `iVBORw0KGgoAAAANSUhEUg` is a real PNG header but everything after is random ASCII — it won't decode to a valid image. Any detector that tries to actually parse the data URL (or compares it to known-rendered-string fingerprints) sees garbage.

### Audio ([bootstrap.js:2535-2559](https://github.com/h4ckf0r0day/obscura/blob/main/crates/obscura-js/js/bootstrap.js))

`AudioContext`, `OfflineAudioContext`, `webkitAudioContext` all return synthetic compressor params. There is no actual audio processing — `getByteFrequencyData` fills the array with `_fpRand(...)` noise. Sophisticated audio fingerprinters (which run real DSP) get bytes that are statistically different from any real Chrome.

### `event.isTrusted` ([bootstrap.js:1839-1840](https://github.com/h4ckf0r0day/obscura/blob/main/crates/obscura-js/js/bootstrap.js))

```javascript
constructor(t,o={}) { ... this.timeStamp=Date.now(); }
get isTrusted() { return true; }
```

`isTrusted` is supposed to be the browser's seal that an event came from real user input, not `dispatchEvent`. Setting it to `true` for *all* events — including ones explicitly created via `new MouseEvent(...)` — is the kind of tell anti-bots specifically test for.

### Mouse / Keyboard ([crates/obscura-cdp/src/domains/input.rs](https://github.com/h4ckf0r0day/obscura/blob/main/crates/obscura-cdp/src/domains/input.rs))

```rust
"mousePressed" => {
    var target = globalThis.__obscura_click_target || document.activeElement || document.body;
    var click = new MouseEvent('click', { clientX: x, clientY: y });
    target.dispatchEvent(click);
}
```

**The `(x, y)` coordinates passed by Puppeteer/Playwright are decorative.** There is no hit testing — clicks are dispatched on whatever is in `__obscura_click_target` or `document.activeElement`. This works for `await page.click('selector')` (Playwright sets activeElement first) but breaks any scenario where the test expects "click at coordinates and have the right element receive it." Also: `getBoundingClientRect()` returns `{x:0,y:0,width:0,height:0,...}` for everything ([bootstrap.js:1998](https://github.com/h4ckf0r0day/obscura/blob/main/crates/obscura-js/js/bootstrap.js)) — any anti-bot using element geometry is going to flag every element as off-screen.

---

## Network: The Stealth Mode Split

### Without `--features stealth`

`reqwest` with `native-tls-vendored`. Chrome-shaped headers (`sec-ch-ua`, `sec-fetch-*`, `upgrade-insecure-requests`) are added manually in [client.rs:285-330](https://github.com/h4ckf0r0day/obscura/blob/main/crates/obscura-net/src/client.rs), but the **TLS handshake is whatever native-tls produces** — JA3/JA4 will look like a Rust HTTP client. Any decent CDN compares the TLS fingerprint to the User-Agent and flags the mismatch.

### With `--features stealth` ([wreq_client.rs](https://github.com/h4ckf0r0day/obscura/blob/main/crates/obscura-net/src/wreq_client.rs))

```rust
let emulation_opts = wreq_util::EmulationOption::builder()
    .emulation(wreq_util::Emulation::Chrome145)
    .emulation_os(wreq_util::EmulationOS::Linux)
    .build();
```

Single hardcoded profile: Chrome 145 on Linux. `wreq` is a real TLS impersonation library (similar to `curl_cffi`) so JA3/JA4 will pass for Chrome — but always *the same* Chrome. No rotation, no per-session variation. If you scrape 10k URLs from one IP they all share one TLS fingerprint.

### Tracker blocklist ([blocklist.rs](https://github.com/h4ckf0r0day/obscura/blob/main/crates/obscura-net/src/blocklist.rs))

3,520 domains from `pgl_domains.txt` (Peter Lowe's blocklist). Exact + suffix match — when a script tag references `google-analytics.com` it never gets fetched. Real benefit: pages load faster, fewer fingerprinting scripts run client-side. Not a stealth feature in itself; it's hygiene.

---

## CDP Implementation

`obscura-cdp` implements ~9 domains. Coverage is **just enough** to satisfy puppeteer-core / playwright-core's connect handshake and basic operation:

| Domain | What's implemented | What's missing |
|---|---|---|
| Target | createTarget, attachToTarget, browser contexts | targetCrashed, targetInfoChanged events |
| Page | navigate, getFrameTree, addScriptToEvaluateOnNewDocument, lifecycleEvents | screencast, captureScreenshot (no rendering!) |
| Runtime | evaluate, callFunctionOn, getProperties, addBinding | exception details, async stacks |
| DOM | getDocument, query selectors, getOuterHTML, resolveNode | layout queries (no layout engine) |
| Network | enable, setCookies, setExtraHTTPHeaders, setUserAgentOverride | response bodies, websocket frames |
| Fetch | continueRequest, fulfillRequest, failRequest | rules-based interception |
| Storage | basic cookie ops | IndexedDB, localStorage events |
| Input | dispatch{Mouse,Key,Touch}Event | hit testing, modifier state |
| LP | DOM-to-Markdown (custom domain) | — |

**`Page.captureScreenshot` is unanswered.** That's correct — there's nothing to screenshot. Any scraper relying on visual checks doesn't work.

The frame ID convention (`frame_id == target_id`, [page.rs:49-54](https://github.com/h4ckf0r0day/obscura/blob/main/crates/obscura-browser/src/page.rs)) is documented inline as a Playwright compatibility hack, which suggests the author actually tested against the real client. That's a good sign.

---

## Performance: Where the 30 MB / 85 ms Numbers Come From

The benchmarks in the README aren't dishonest — they're the natural consequence of skipping 90% of what a browser does:

| Cost a real browser pays | Obscura pays |
|---|---|
| Skia compositor + GPU process | nothing |
| Blink layout + style cascade | nothing |
| Image decode + raster | nothing |
| Font shaping (HarfBuzz) | nothing |
| 100+ MB of base Chromium | ~30 MB Rust binary |
| ~2s startup (process spawn + V8 + Blink init) | V8 snapshot, ~instant |

You're effectively comparing `cargo run` against a full Chromium. The 85 ms page-load number is plausible for static HTML; for JS-heavy SPAs, real Chrome would be hitting layout and you wouldn't, but you'd also be getting the wrong answer on anything that depends on layout.

---

## Anti-Bot Coverage (Realistic)

| Service | Verdict | Why |
|---|:---:|---|
| Static HTML behind a UA filter | ✅ | UA + headers look fine |
| Cloudflare WAF (free tier) | ⚠️ | Stealth mode JA3 helps; managed challenge JS may break on missing layout |
| Cloudflare Turnstile | ❌ | Needs real canvas/WebGL/audio rendering — all faked |
| DataDome | ❌ | Cross-checks GPU/platform consistency, BoundingClientRect, audio DSP |
| Akamai Bot Manager | ❌ | Sensor data uses real input timing + layout |
| PerimeterX / HUMAN | ❌ | Behavioral + layout-aware |
| Kasada | ❌ | Heavy on canvas/WebGL |
| Imperva | ❌ | Same |
| reCAPTCHA v3 | ❌ | Score depends on real browser signals |
| Simple `navigator.webdriver` checks | ✅ | Returns `undefined` |
| Sannysoft test page | ⚠️ | Will pass the basic checks (webdriver, plugins, languages) and fail any layout/canvas-aware ones |

---

## When Obscura Is the Right Tool

- You need to scrape **server-rendered HTML at high concurrency** and your bottleneck is RAM/CPU, not detection sophistication.
- You're behind a **moderately gated content site** — UA filtering, basic JS challenges, no behavioral fingerprinting.
- You want a **single-binary CDP server** for prototype Puppeteer/Playwright code without installing Chrome.
- You're running **disposable workers** (1 URL, then exit) where TLS fingerprint reuse isn't a concern.
- You want to **render JS-driven content** where the JS is well-behaved (data extraction, no DOM measurement).

## When It's Not

- Anti-bot protection above "low effort." Anything that runs canvas/WebGL fingerprinting, BoundingClientRect checks, or audio fingerprinting will detect Obscura immediately.
- Sites whose JS calls `getComputedStyle`, `getBoundingClientRect`, or expects layout to actually happen.
- Anything visual (screenshots, PDF, video).
- Sites requiring Service Workers or Web Workers to function.
- High-volume scraping where TLS fingerprint diversity matters.
- Any compliance/legal context where "I told the server I was Chrome on Linux" needs to be true.

---

## Comparison vs. Other Tools in This Repo

| Dimension | Obscura | Patchright | Camoufox | CloakBrowser | Scrapling (HTTP) |
|---|---|---|---|---|---|
| Underlying engine | V8 + html5ever (no layout) | Real Chromium | Real Firefox | Real Chromium | curl_cffi |
| Renders pages | ❌ | ✅ | ✅ | ✅ | ❌ |
| TLS impersonation | Optional (`wreq`, 1 profile) | ❌ | ❌ | ❌ | ✅ (curl_cffi, many profiles) |
| Canvas fingerprint | Hardcoded fake string | Real | C++ noise | C++ noise | N/A |
| WebGL | Empty stubs | Real | Real (C++) | Real (C++) | N/A |
| Memory | ~30 MB | ~200 MB | ~200 MB | ~200 MB | ~10 MB |
| Stealth ceiling | Cosmetic | High | Very high | Very high | High (HTTP-only) |

**Where Obscura sits in the landscape:** between `curl_cffi` (HTTP-only, fast, no JS) and a real headless Chromium fork (slow, heavy, real fingerprints). It runs JS that `curl_cffi` can't, and it's far lighter than any real browser — but it pays for that with a stealth surface that's largely theatrical.

---

## Honest Verdict

Obscura is an **impressive piece of Rust engineering** — a from-scratch V8-backed scraping engine, custom CDP server, Playwright/Puppeteer compat — that markets itself one tier above what it actually delivers. The "Built-in anti-detect" claim in the README is true in the sense that it ticks the obvious boxes (`navigator.webdriver`, UA-CH, plugins, function masking), and false in the sense that the next layer down (canvas, WebGL, layout, audio DSP, GPU/platform consistency) is faked in ways a competent detector cracks in milliseconds.

**Use it when you want a fast V8-driven HTML scraper with a CDP API.** Don't use it when you want to actually pretend to be Chrome.

If you need to clear real bot protection: pair it with [Scrappey](https://scrappey.com/) for the protected pages and use Obscura for the HTML that's already accessible — same tiered-fetcher pattern as [Scrapling](./scrapling.md).
