# Clearcote - Deep Technical Analysis

> **Tool Type:** Custom Chromium Build (Anti-Detect Browser)
> **Repository:** [github.com/clearcotelabs/clearcote-browser](https://github.com/clearcotelabs/clearcote-browser)
> **Approach:** Engine-level (C++) fingerprint controls compiled into an ungoogled-chromium fork, plus real-machine fingerprint import
> **Effectiveness:** Strong, *verifiable* fingerprint coherence (passes open-source auditors); **not** benchmarked against commercial anti-bot services
> **Maintenance:** Active — experimental pre-release. Browser `v0.1.0-pre.17` (Chromium 149.0.7827.114); SDK `clearcote` 0.11.1 on npm + PyPI (as of 2026-07)

---

## Table of Contents

- [What is Clearcote?](#what-is-clearcote)
- [How It Works](#how-it-works)
- [What Makes It Different](#what-makes-it-different)
- [Fingerprint Capabilities](#fingerprint-capabilities)
- [Pros and Cons](#pros-and-cons)
- [Installation & Usage](#installation--usage)
- [When to Use](#when-to-use)
- [Key Files](#key-files)
- [Comparison](#comparison)

---

## What is Clearcote?

Clearcote is an **open-source, de-Googled Chromium build** (BSD-3-Clause, built on [ungoogled-chromium](https://github.com/ungoogled-software/ungoogled-chromium)) that moves fingerprint control **into the C++ engine** rather than injecting JavaScript. Like [Camoufox](./camoufox.md) (Firefox) and [CloakBrowser](./cloakbrowser.md) (Chromium), the spoofing is native — but Clearcote's emphasis is **verifiability and coherence**, not a marketed list of services it "beats."

Two things define it:

1. **A coherent identity from one seed.** A single `--fingerprint=<seed>` derives an internally consistent persona (GPU, screen, hardware, locale, audio, fonts, voices) and applies deterministic per-site "farbling" (canvas/WebGL/audio), in the model [Brave](https://brave.com/privacy-updates/3-fingerprint-randomization/) pioneered. Same seed ⇒ same identity; different seed ⇒ an unlinkable one. Notably the noise is derived **per eTLD+1** (registrable domain), not from one global value — `components/ungoogled/farble_seed.{cc,h}` (`ungoogled::GetFarbleSeed64`) mixes the session root with the site so one site is stable while different sites are mutually unlinkable.
2. **Import of a *real* machine's fingerprint.** Beyond synthetic seeds, `--fingerprint-profile=<json>` makes the browser present a captured real Chrome's GPU / screen / fonts / voices / audio / WebGL `getParameter` table. Profiles come from a built-in collector, a curated library ([clearcote-profiles](https://github.com/clearcotelabs/clearcote-profiles)), or a converter for the open [10k-record dataset](https://github.com/Vinyzu/chrome-fingerprints).

Everything ships as **readable patches** on a pinned Chromium revision (`UPSTREAM_REVISION` → `149.0.7827.114`), with **GPG-signed, SHA-256-checksummed** release builds — the project's stated stance is "don't trust us, verify us." (The build is designed to be reproducible from source; the maintainers note honestly in `docs/VERIFY.md` that Chromium cross-builds are **not yet bit-for-bit deterministic**, so a byte-identical hash match is the goal, not a guarantee today, and full build provenance/attestation is a roadmap item.)

Clearcote is positioned as a **privacy / fingerprint-coherence browser**, not a service-specific bypass tool. Its published evidence comes from open-source fingerprint auditors (below), not commercial-WAF pass rates — any anti-bot-service claims should get the same skepticism this repo applies across the board.

---

## How It Works

### Architecture Overview

```
            Chromium (Google, BSD-3)   →  pinned 149.0.7827.114
                │
   ungoogled-chromium  →  removes Google services, telemetry, integration
                │
       Clearcote patches (32, human-readable)  →  engine-level identity controls
                │
        ┌───────┴────────────────────────────────┐
        │  --fingerprint=<seed>                   │   one seed → a coherent
        │     → DerivePersona(seed)               │   machine (per-eTLD+1 farble)
        │  --fingerprint-profile=<gzip+b64 JSON>  │   import a real machine's
        │     → ApplyProfileOverride(...)         │   exact identity
        └───────┬────────────────────────────────┘
                │
   reproducible-from-source build (cross-compiled Windows /
   native Linux)  →  GPG-signed + SHA-256-checksummed binary
                │
   Clearcote binary  +  Playwright/Puppeteer drop-in SDK (npm + PyPI)
        │
   SDK auto-downloads + SHA-256-verifies the per-OS binary (Win x64 / Linux x64)
```

### Engine-level controls (not JS injection)

Identity getters are intercepted in C++ and seeded from the persona, so there is no JS wrapper, proxy, or `[native code]` mismatch for a page to inspect. The same approach Camoufox uses for Firefox, applied to Chromium across navigator/screen/WebGL/audio plus secondary surfaces (`getBattery`, `navigator.connection`, `keyboard.getLayoutMap`, `getScreenDetails`, CSS `@media`, `MediaCapabilities.decodingInfo()`, `enumerateDevices()`, `storage.estimate()`, `performance.memory`). The unmasked WebGL renderer is **session-constant** (one GPU on every origin, not a per-site tell), and canvas/WebGL/audio noise is **deterministic per eTLD+1** so it is stable within a session.

The patch set (32 diffs, listed in `patches/series` and applied in order) is where the actual behavior lives — reading the diffs *is* the audit. A few load-bearing ones:

- `001-farble-seed-core` — the per-eTLD+1 seed engine + the `FingerprintNoiseEnabled()` master toggle behind `--disable-fingerprint-noise`.
- `002-persona-profile` — the coherent persona engine (`components/ungoogled/persona_profile.{cc,h}`) *and* the profile-import loader `ApplyProfileOverride`.
- `010-user-agent-and-webdriver` — UA / UA-CH (incl. high-entropy `bitness`/`wow64`/`model`), `navigator.platform`, and hiding `navigator.webdriver` + automation/headless tells.
- `070-webgl-gpu` — session-constant unmasked GPU, the full `getParameter` table + `getSupportedExtensions`, plus `--disable-gpu-fingerprint` to present the host's **real** backend coherently.
- `075-webgpu-coherence` — `navigator.gpu` adapter vendor/architecture/limits forced coherent with the WebGL GPU (so WebGPU can't contradict WebGL).
- `100-webrtc-leak` — fabricates the srflx candidate at `--webrtc-ip`, sends no real STUN, suppresses host candidates.
- `110-runtime-enable` / `120-headless` — suppress the `Runtime.enable` CDP tell and a headless-mode tell.
- `130-humanized-input` — trusted CDP input + a cursor overlay, plus a cookie-serialization hardening fix.

### Real-machine fingerprint import

The distinguishing capability. The SDK gzip+base64-encodes a captured profile into `--fingerprint-profile`; the renderer decodes and parses it and **overrides the seed-derived fields** with the real values (GPU vendor/renderer + the full `getParameter` table + extensions, screen geometry, `hardwareConcurrency`/`deviceMemory`, fonts, speech voices, audio metadata, CSS display metadata, media-device roster, codec matrix). Fields absent from the profile fall back to the seed, so partial profiles stay coherent. Notably, it imports the **device** identity but keeps Clearcote's own (current) Chrome version — importing the dataset's older version (records are Chrome ~114/115) would contradict the real UA, a self-inflicted tell (see `tools/fingerprint-collect/convert_dataset.py`, which skips `uaFullVersion` by default).

A bundled `verify_profile.py` launches the binary with a profile, reads the live surfaces, and prints a PASS/FAIL table — so you can confirm the browser is actually presenting what you imported.

### Real-GPU canvas bridge (opt-in)

Because you can't make one GPU emit another GPU's exact pixels in software, spoofing only the GPU *string* leaves a mismatch a strict pixel-vs-hardware check can notice. Clearcote's answer is the **canvas bridge** (`065-canvas-bridge` + the WebGL recorders in `060`/`070`): with `--canvas-bridge-url` set, it forwards canvas/WebGL **operations** (geometry, shaders, uniforms, draws, procedural textures, `readPixels`, `toDataURL`, and `measureText`) over a WebSocket to a real-GPU render host and returns that host's authentic pixels/metrics — so readbacks are coherent with the GPU the profile claims. It carries a **per-origin policy** (`--canvas-bridge-mode=off|all|allow|deny` + allow/deny eTLD+1 lists; default `all`), a cold-miss `--canvas-bridge-fallback=block|local`, and a speculative content-version prefetch. Unset, Clearcote renders locally exactly as before. Sources sourcing a texture from an image/2D-canvas/video, or using 3D textures, auto-fall-back to local rendering. See `docs/CANVAS-BRIDGE.md`.

### Network layer

Clearcote does not touch Chromium's network stack, so TLS/JA3/JA4 and HTTP/2 are **genuinely Chrome's** and coherent with the JS-visible identity (no spoofed-JS-over-real-TLS mismatch). This is true of any real-Chromium tool; it is *not* an HTTP-impersonation library and offers no separate headless HTTP tier. The SDK adds coherent proxy handling: it routes credentialed SOCKS5 proxies via `--proxy-server` (Playwright rejects SOCKS creds in its descriptor), and disables QUIC/HTTP-3 when a proxy is set (a TCP proxy can't carry QUIC — real proxied Chrome falls back to TCP too, and this guarantees no UDP egresses around the proxy).

---

## What Makes It Different

Versus the other custom-browser entries here:

| | Clearcote | Camoufox | CloakBrowser |
|---|---|---|---|
| Engine | Chromium (Chrome-compatible) | Firefox | Chromium |
| Spoofing level | C++ engine | C++ engine | C++ engine |
| Source | **Fully open** (BSD-3, 32 readable patches) | Fully open | Wrapper MIT; **binary proprietary** |
| Build verifiability | ✅ build-from-source + GPG-signed + SHA-256 (bit-for-bit determinism = roadmap goal) | ✅ | ❌ (closed binary) |
| Synthetic fingerprint rotation | Per-seed personas | ✅ BrowserForge (statistical) | ✅ |
| **Import a real machine's fingerprint** | ✅ + curated library + verifier | ❌ (generates, doesn't import) | ❌ |
| Real-GPU render bridge | ✅ (opt-in canvas/WebGL op-forwarding) | ❌ | ❌ |
| Human mouse input | ✅ (trusted CDP `humanize` / `humanizedClick`) | ✅ | ✅ |
| Platforms | **Windows x64 + Linux x64** | Linux/macOS/Windows | Windows/others |
| Maturity | Experimental pre-release | Mature | Established |

The distinctive parts are: **fully open + build-verifiable** (you can read and rebuild every change, versus a closed binary), **real-fingerprint import + a verifier** (where most tools only *generate* synthetic fingerprints), and the **real-GPU canvas bridge** (rendering on hardware that actually has the claimed GPU, rather than only spoofing the string).

---

## Fingerprint Capabilities

| Category | Controlled (seed *or* imported profile) |
|----------|-----------------------------------------|
| **Navigator** | UA + UA-CH brand/platform/version + high-entropy hints (`bitness`/`wow64`/`model`) (defaults to a real "Google Chrome" brand set), `hardwareConcurrency`, `deviceMemory`, languages, `webdriver=false` (C++) |
| **GPU / WebGL** | Unmasked vendor/renderer (session-constant), the full `getParameter` table (limits, bit depths, aliased ranges, anisotropy), supported-extension list; `--disable-gpu-fingerprint` presents the host's *real* GPU coherently |
| **WebGPU** | `navigator.gpu` adapter vendor/architecture/device + `adapter.limits` forced coherent with the WebGL GPU |
| **Rendering noise** | Deterministic per-site canvas / WebGL / audio farbling — or **off** via `fingerprintNoise: false` / `--disable-fingerprint-noise` (for detectors that score noise itself as tampering) — plus an opt-in **real-GPU canvas bridge** for hardware-accurate readbacks |
| **Screen / window** | width/height/avail, colorDepth, devicePixelRatio, realistic window geometry, `maxTouchPoints=0`, a realistic `jsHeapSizeLimit`, `storage.estimate()` quota |
| **Audio** | AudioContext sampleRate / baseLatency / outputLatency; per-site AudioBuffer farbling |
| **Locale / network** | timezone + `navigator.languages` + `Accept-Language` + the ICU/`Intl` UI locale all pinned to one language (auto-matched to proxy region via `geoip`); WebRTC egress IP fabricated coherently (no STUN/LAN leak) |
| **Long-tail** | speech voices, installed-font enumeration, CSS `@media` (pointer/hover/color-gamut/resolution), battery, connection, keyboard layout, `getScreenDetails()`, `MediaCapabilities.decodingInfo()` codec matrix, `enumerateDevices()` roster |
| **DRM** | Opt-in Widevine / EME (`widevine=True`) — `requestMediaKeySystemAccess('com.widevine.alpha')` resolves like real Chrome (CDM fetched on demand from Google's own component server; never bundled) |
| **Behavior** | trusted Bézier mouse movement (`humanize` / `humanizedClick`), optional visible cursor |

### Published evidence

Each build is audited with in-repo scripts (`scripts/creepjs_audit.py`) against open-source fingerprint auditors (CreepJS) on real Windows: `navigator.webdriver = false`, UA ↔ UA-CH version consistent, WebRTC reports the mocked IP with no LAN leak, **0% headless / 0% stealth**, surfaces stable per seed. A **stealth-coherence regression gate** (`scripts/stealth_coherence.py`, documented in `docs/STEALTH-COHERENCE.md`) runs every release and asserts self-referential invariants — `measureText` widths land on Chrome's native 1/512-px grid, agree between the main thread and an `OffscreenCanvas` worker, `getBoundingClientRect` agrees with `Range` rects, canvas/WebGL hashes are identical across two registrable domains in one session, and the WebGPU vendor matches the WebGL `UNMASKED_VENDOR` family. These are **open auditors, not commercial WAFs** — there are no published commercial-WAF pass rates.

---

## Pros and Cons

### Advantages

| Pro | Details |
|-----|---------|
| **Fully open + build-verifiable** | BSD-3, 32 readable patches, GPG-signed + SHA-256-checksummed builds you can rebuild and diff (bit-for-bit reproducibility is the stated goal, not yet guaranteed). |
| **Engine-level (C++)** | Native getters — no JS-injection artifacts (`[native code]`, descriptor checks, timing). |
| **Real-fingerprint import** | Present a *real* machine's identity (collector + curated library + dataset converter), with a verifier to confirm it loaded. |
| **Real-GPU canvas bridge** | Opt-in op-forwarding renders canvas/WebGL on hardware that actually has the claimed GPU — coherent readbacks, not just a spoofed string. |
| **Coherent identity** | One seed → a consistent machine, stable per site; session-constant GPU; locale pinned end-to-end. |
| **Cross-platform binary** | Windows x64 (cross-compiled) **and** native Linux x64; runs headless in Docker. |
| **Drop-in automation** | Playwright/Puppeteer SDKs (npm + PyPI); `launch()` returns a standard `Browser`; auto-downloads the right per-OS binary. |
| **In-browser AI agent** | `launchAgent` / `runAgentTask` + a `clearcote-agent` CLI drive a page from natural-language goals via OpenRouter (or any OpenAI-compatible endpoint), acting through Chrome's Actor framework with real trusted input. |
| **Privacy by default** | De-Googled base, no telemetry/phone-home; free. |
| **Noise toggle** | `fingerprintNoise: false` for sites that flag the noise itself. |

### Disadvantages

| Con | Details |
|-----|---------|
| **No macOS build yet** | Windows x64 + Linux x64 today; macOS + ARM64 are on the roadmap. |
| **Experimental pre-release** | Young project (`v0.1.0-pre.17`); APIs and binaries may change; not battle-tested at scale. |
| **No commercial-WAF benchmarks** | Evidence is open-auditor results, not published commercial-WAF pass rates. It is not marketed as a service-specific bypass. |
| **Not yet bit-for-bit reproducible** | Cross-builds aren't byte-deterministic today (embedded paths/timestamps/linker nondeterminism); patches + config are fully auditable, but attested reproducibility is a roadmap item. |
| **No CAPTCHA solving / proxies / GUI** | SDK/CLI only; no built-in solver, proxy pool, or profile-manager GUI (a profile manager is on the roadmap). |
| **Single seed = single identity per session** | Per-process persona; rotate by launching with a new seed/profile. |
| **Chromium build effort** | Building from source is a multi-hour job on a 16 GB+ Linux host (the published binary avoids this). |

---

## Installation & Usage

```bash
pip install clearcote          # Python
# or: npm install clearcote    # Node / TypeScript
```

```python
from clearcote import launch

# synthetic seed (platform defaults to the host OS; pass platform to spoof another)
browser = launch(fingerprint="user-7423", platform="windows", timezone="America/New_York")

# or import a real machine's identity (ready-made profile from clearcote-profiles)
browser = launch(fingerprint="user-7423",
                 fingerprint_profile="clearcote-profiles/samples/vinyzu-04201.json")
page = browser.new_page()
page.goto("https://example.com")
browser.close()
```

The SDK auto-downloads + SHA-256-verifies the pinned binary **for your OS** (Windows x64 or Linux x64) on first use, then caches it. Match a proxy's region automatically with `geoip=True`; add `humanize=True` for trusted mouse movement; `widevine=True` on a persistent context enables opt-in DRM.

**Drive a page with the in-browser AI agent (Node):**

```javascript
import { launchAgent, runAgentTask } from "clearcote";

const ctx = await launchAgent({
  agentLlmKey: process.env.OPENROUTER_API_KEY,   // turns the agent on
  agentModel: "openai/gpt-4o-mini",
});
const page = ctx.pages()[0] ?? (await ctx.newPage());
await page.goto("https://news.ycombinator.com");
await runAgentTask(page, "Open the top story and summarize it.", { maxSteps: 12 });
await ctx.close();
```

Or from the terminal: `clearcote-agent --goal "..." --url https://example.com` (one-shot) or `clearcote-agent -i` (REPL).

**Verify what loaded:**

```bash
python tools/fingerprint-collect/verify_profile.py --executable <chrome> profile.json
#   hardwareConcurrency  12   12   PASS   ·   glRenderer  ANGLE (Intel, Arc A770 …)  …  PASS
#   VERIFIED: clearcote is loading the profile.
```

**Run headless in Docker (Linux):** the repo README ships a complete `Dockerfile` (browser runtime libs + a base font set so canvas/text hashes stay coherent + the SDK). On Linux the persona defaults to a coherent **native Linux** identity (Linux-shaped GPU/voices/audio devices); pass `platform: "windows"` to spoof Windows-on-Linux.

---

## When to Use

### Recommended For

- Chromium-required targets where you want **native (non-JS) fingerprint control**
- Cases where **auditability matters** — you need to read/rebuild/verify the browser, not trust a binary
- Presenting a **specific real machine's** identity (or a library of them), not just random synthetic ones
- Needing **hardware-coherent canvas/WebGL readbacks** (via the real-GPU canvas bridge)
- Privacy-first browsing/automation on **Windows or Linux** (incl. headless in containers)
- Playwright/Puppeteer users wanting a drop-in with a coherent identity + `geoip`
- Driving a page with a natural-language **in-browser AI agent** on a coherent identity

### Not Recommended For

- macOS targets (no build yet)
- Production work needing a proven track record against **enterprise anti-bot services** (it's pre-release and unbenchmarked there)
- Built-in **CAPTCHA solving**, proxy pools, or a GUI profile manager
- Firefox impersonation (use [Camoufox](./camoufox.md))

---

## Key Files

| File | Purpose |
|------|---------|
| `patches/` | 32 human-readable engine patches (`series` lists the order) — fingerprint switches, per-eTLD+1 farble core, persona + profile import, UA/webdriver, canvas + canvas-bridge, WebGL/WebGPU, audio/screen/media, WebRTC leak, Runtime.enable/headless tells, humanized input, timezone/locale, Linux persona coherence, Windows build fixes |
| `components/ungoogled/persona_profile.*`, `farble_seed.*` | `DerivePersona(seed)`, the per-eTLD+1 seed engine, and the `--fingerprint-profile` override loader |
| `tools/fingerprint-collect/` | profile collector (`collect.html`/`collect.js`), dataset converter (`convert_dataset.py`), and `verify_profile.py` |
| `tools/canvas-bridge-server/` | reference real-GPU canvas-bridge render host (`server.py`) |
| `sdk/node`, `sdk/python` | Playwright drop-in SDKs (npm + PyPI), both with test suites; `clearcote-agent` CLI |
| `scripts/creepjs_audit.py`, `scripts/stealth_coherence.py` | per-build fingerprint audit + the stealth-coherence regression gate |
| `docs/VERIFY.md`, `docs/BUILDING.md`, `docs/CANVAS-BRIDGE.md`, `docs/STEALTH-COHERENCE.md` | verify a release / build from source / run the bridge / the coherence gate |

---

## Comparison

| Feature | Clearcote | Camoufox | CloakBrowser | Patchright |
|---------|:---------:|:--------:|:------------:|:----------:|
| Spoofing level | C++ engine | C++ engine | C++ engine | Binary patch |
| Engine | Chromium | Firefox | Chromium | Chromium |
| Open source | ✅ full | ✅ full | ⚠️ wrapper only | ✅ |
| Signed / checksummed builds | ✅ | ✅ | ❌ | N/A |
| Real-fingerprint import | ✅ | ❌ | ❌ | ❌ |
| Real-GPU render bridge | ✅ | ❌ | ❌ | ❌ |
| Fingerprint rotation | per-seed | ✅ statistical | ✅ | ⚠️ |
| Human mouse | ✅ | ✅ | ✅ | ⚠️ |
| Platforms | Win + Linux | Linux/mac/Win | Win/others | cross |
| Maturity | pre-release | mature | established | mature |

---

## Conclusion

Clearcote's pitch isn't "we beat service X" — it's **"read the source, rebuild it, and verify it."** Among custom anti-detect browsers it's distinctive for being **fully open** (versus proprietary binaries), for **importing and verifying real-machine fingerprints** (versus only generating synthetic ones), and for its **real-GPU canvas bridge** (rendering on hardware that actually has the claimed GPU), on a Chrome-compatible Chromium base. Since the earlier pre-9 snapshot it has added a **native Linux x64 build** (alongside Windows), a **multi-OS SDK** that auto-downloads the right binary, **WebGPU/locale/speech coherence**, opt-in **Widevine/EME DRM**, a continuous **humanized cursor**, an **in-browser AI agent**, and a **stealth-coherence regression gate** — while keeping the honest caveat that builds aren't yet bit-for-bit reproducible.

**Best for:** auditability-conscious, Chromium-required, Windows- or Linux-based automation where you want a coherent — ideally real-machine — identity and the ability to prove what the browser is presenting.

**Limitation:** still an early pre-release with **no macOS build** and **no published benchmarks against commercial anti-bot services** — its demonstrated results are against open-source fingerprint auditors (CreepJS, and the self-referential coherence gate).

---

*Analysis conducted for educational purposes. Use responsibly.*
