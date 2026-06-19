# Clearcote - Deep Technical Analysis

> **Tool Type:** Custom Chromium Build (Anti-Detect Browser)
> **Repository:** [github.com/clearcotelabs/clearcote-browser](https://github.com/clearcotelabs/clearcote-browser)
> **Approach:** Engine-level (C++) fingerprint controls compiled into an ungoogled-chromium fork, plus real-machine fingerprint import
> **Effectiveness:** Strong, *verifiable* fingerprint coherence (passes open-source auditors); **not** benchmarked against commercial anti-bot services
> **Maintenance:** Early, active — experimental pre-release (`v0.1.0-pre.9`, Chromium 149)

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

1. **A coherent identity from one seed.** A single `--fingerprint=<seed>` derives an internally consistent Windows persona (GPU, screen, hardware, locale, audio, fonts, voices) and applies deterministic per-site "farbling" (canvas/WebGL/audio), in the model [Brave](https://brave.com/privacy-updates/3-fingerprint-randomization/) pioneered. Same seed ⇒ same identity; different seed ⇒ an unlinkable one.
2. **Import of a *real* machine's fingerprint.** Beyond synthetic seeds, `--fingerprint-profile=<json>` makes the browser present a captured real Chrome's GPU / screen / fonts / voices / audio / WebGL `getParameter` table. Profiles come from a built-in collector, a curated library ([clearcote-profiles](https://github.com/clearcotelabs/clearcote-profiles)), or a converter for the open [10k-record dataset](https://github.com/Vinyzu/chrome-fingerprints).

Everything ships as **readable patches** on a pinned Chromium revision, with **signed, checksummed, reproducible** release builds — the project's stated stance is "don't trust us, verify us."

Clearcote is positioned as a **privacy / fingerprint-coherence browser**, not a service-specific bypass tool. Its published evidence comes from open-source fingerprint auditors (below), not commercial-WAF pass rates — any anti-bot-service claims should get the same skepticism this repo applies across the board.

---

## How It Works

### Architecture Overview

```
            Chromium (Google, BSD-3)
                │
   ungoogled-chromium  →  removes Google services, telemetry, integration
                │
       Clearcote patches (25, human-readable)  →  engine-level identity controls
                │
        ┌───────┴────────────────────────────────┐
        │  --fingerprint=<seed>                   │   one seed → a coherent
        │     → DerivePersona(seed)               │   Windows machine
        │  --fingerprint-profile=<gzip+b64 JSON>  │   import a real machine's
        │     → override persona from a capture   │   exact identity
        └───────┬────────────────────────────────┘
                │
   reproducible build  →  signed + checksummed Windows x64 binary
                │
   Clearcote binary  +  Playwright/Puppeteer drop-in SDK (npm + PyPI)
```

### Engine-level controls (not JS injection)

Identity getters are intercepted in C++ and seeded from the persona, so there is no JS wrapper, proxy, or `[native code]` mismatch for a page to inspect. The same approach Camoufox uses for Firefox, applied to Chromium across navigator/screen/WebGL/audio plus secondary surfaces (`getBattery`, `navigator.connection`, `keyboard.getLayoutMap`, `getScreenDetails`, CSS `@media`). The unmasked WebGL renderer is **session-constant** (one GPU on every origin, not a per-site tell), and canvas/WebGL/audio noise is **deterministic per eTLD+1** so it is stable within a session.

### Real-machine fingerprint import

The distinguishing capability. The SDK gzip+base64-encodes a captured profile into `--fingerprint-profile`; the renderer decodes and parses it and **overrides the seed-derived fields** with the real values (GPU vendor/renderer + the full `getParameter` table + extensions, screen geometry, `hardwareConcurrency`/`deviceMemory`, fonts, speech voices, audio metadata, CSS display metadata). Fields absent from the profile fall back to the seed, so partial profiles stay coherent. Notably, it imports the **device** identity but keeps Clearcote's own (current) Chrome version — importing the dataset's older version would contradict the real UA, a self-inflicted tell.

A bundled `verify_profile.py` launches the binary with a profile, reads the live surfaces, and prints a PASS/FAIL table — so you can confirm the browser is actually presenting what you imported.

### Network layer

Clearcote does not touch Chromium's network stack, so TLS/JA3/JA4 and HTTP/2 are **genuinely Chrome's** and coherent with the JS-visible identity (no spoofed-JS-over-real-TLS mismatch). This is true of any real-Chromium tool; it is *not* an HTTP-impersonation library and offers no separate headless HTTP tier.

---

## What Makes It Different

Versus the other custom-browser entries here:

| | Clearcote | Camoufox | CloakBrowser |
|---|---|---|---|
| Engine | Chromium (Chrome-compatible) | Firefox | Chromium |
| Spoofing level | C++ engine | C++ engine | C++ engine |
| Source | **Fully open** (BSD-3, 25 readable patches) | Fully open | Wrapper MIT; **binary proprietary** |
| Build reproducibility | ✅ build-from-source + signed/checksummed | ✅ | ❌ (closed binary) |
| Synthetic fingerprint rotation | Per-seed personas | ✅ BrowserForge (statistical) | ✅ |
| **Import a real machine's fingerprint** | ✅ + curated library + verifier | ❌ (generates, doesn't import) | ❌ |
| Human mouse input | ✅ (trusted CDP `humanize`) | ✅ | ✅ |
| Platforms | **Windows only (today)** | Linux/macOS/Windows | Windows/others |
| Maturity | Experimental pre-release | Mature | Established |

The distinctive parts are: **fully open + reproducible** (you can read and rebuild every change, versus a closed binary), and **real-fingerprint import + a verifier**, where most tools only *generate* synthetic fingerprints.

---

## Fingerprint Capabilities

| Category | Controlled (seed *or* imported profile) |
|----------|-----------------------------------------|
| **Navigator** | UA + UA-CH brand/platform/version (defaults to a real "Google Chrome" brand set), `hardwareConcurrency`, `deviceMemory`, languages, `webdriver=false` (C++) |
| **GPU / WebGL** | Unmasked vendor/renderer (session-constant), the full `getParameter` table (limits, bit depths, aliased ranges, anisotropy), supported-extension list |
| **Rendering noise** | Deterministic per-site canvas / WebGL / audio farbling — or **off** via `--disable-fingerprint-noise` (for detectors that score noise itself as tampering) |
| **Screen / window** | width/height/avail, colorDepth, devicePixelRatio, realistic window geometry, `maxTouchPoints=0`, a realistic `jsHeapSizeLimit` |
| **Audio** | AudioContext sampleRate / latency |
| **Locale / network** | timezone + `navigator.languages` + `Accept-Language` (auto-matched to proxy region via `geoip`); WebRTC egress IP fabricated coherently (no STUN/LAN leak) |
| **Long-tail** | speech voices, installed-font enumeration, CSS `@media` (pointer/hover/color-gamut/resolution), battery, connection, keyboard layout, `getScreenDetails()` |
| **Behavior** | trusted Bézier mouse movement (`humanize`), optional visible cursor |

### Published evidence

Audited each build with an in-repo script against open-source fingerprint auditors (CreepJS) on real Windows: `navigator.webdriver = false`, UA ↔ UA-CH version consistent, WebRTC reports the mocked IP with no LAN leak, **0% headless / 0% stealth**, surfaces stable per seed. These are **open auditors, not commercial WAFs** — there are no published DataDome/Cloudflare/Kasada pass rates.

---

## Pros and Cons

### Advantages

| Pro | Details |
|-----|---------|
| **Fully open + reproducible** | BSD-3, 25 readable patches, signed + checksummed builds you can rebuild and diff. |
| **Engine-level (C++)** | Native getters — no JS-injection artifacts (`[native code]`, descriptor checks, timing). |
| **Real-fingerprint import** | Present a *real* machine's identity (collector + curated library + dataset converter), with a verifier to confirm it loaded. |
| **Coherent identity** | One seed → a consistent machine, stable per site; session-constant GPU. |
| **Drop-in automation** | Playwright/Puppeteer SDKs (npm + PyPI); returns a standard `Browser`. |
| **Privacy by default** | De-Googled base, no telemetry/phone-home; free. |
| **Noise toggle** | `--disable-fingerprint-noise` for sites that flag the noise. |

### Disadvantages

| Con | Details |
|-----|---------|
| **Windows x64 only (today)** | No macOS/Linux build yet. |
| **Experimental pre-release** | Young project; APIs and binaries may change; not battle-tested at scale. |
| **No commercial-WAF benchmarks** | Evidence is open-auditor results, not published DataDome/Cloudflare/Kasada pass rates. It is not marketed as a service-specific bypass. |
| **No CAPTCHA solving / proxies / GUI** | SDK/CLI only; no built-in solver, proxy pool, or profile-manager GUI. |
| **Single seed = single identity per session** | Per-process persona; rotate by launching with a new seed/profile. |
| **Chromium build effort** | Building from source cross-compiles on Linux (the published binary avoids this). |

---

## Installation & Usage

```bash
pip install clearcote          # Python
# or: npm install clearcote    # Node / TypeScript
```

```python
from clearcote import launch

# synthetic seed
browser = launch(fingerprint="user-7423", platform="windows", timezone="America/New_York")

# or import a real machine's identity (ready-made profile from clearcote-profiles)
browser = launch(fingerprint="user-7423",
                 fingerprint_profile="clearcote-profiles/samples/vinyzu-04201.json")
page = browser.new_page()
page.goto("https://example.com")
browser.close()
```

The SDK auto-downloads + SHA-256-verifies the pinned Windows binary on first use. Match a proxy's region automatically with `geoip=True`; add `humanize=True` for trusted mouse movement.

**Verify what loaded:**

```bash
python tools/fingerprint-collect/verify_profile.py --executable <chrome.exe> profile.json
#   hardwareConcurrency  12   12   PASS   ·   glRenderer  ANGLE (Intel, Arc A770 …)  …  PASS
#   VERIFIED: clearcote is loading the profile.
```

---

## When to Use

### Recommended For

- Chromium-required targets where you want **native (non-JS) fingerprint control**
- Cases where **auditability matters** — you need to read/rebuild/verify the browser, not trust a binary
- Presenting a **specific real machine's** identity (or a library of them), not just random synthetic ones
- Privacy-first browsing/automation on Windows
- Playwright/Puppeteer users wanting a drop-in with a coherent identity + `geoip`

### Not Recommended For

- macOS/Linux targets (no build yet)
- Production work needing a proven track record against **enterprise anti-bot services** (it's pre-release and unbenchmarked there)
- Built-in **CAPTCHA solving**, proxy pools, or a GUI profile manager
- Firefox impersonation (use [Camoufox](./camoufox.md))

---

## Key Files

| File | Purpose |
|------|---------|
| `patches/` | 25 human-readable engine patches (fingerprint switches, persona, farbling, WebGL/audio/screen, WebRTC, humanized input) |
| `components/ungoogled/persona_profile.*` | `DerivePersona(seed)` + `--fingerprint-profile` override loader |
| `tools/fingerprint-collect/` | profile collector (`collect.html`), dataset converter (`convert_dataset.py`), and `verify_profile.py` |
| `sdk/node`, `sdk/python` | Playwright drop-in SDKs (npm + PyPI) |
| `docs/VERIFY.md`, `docs/BUILDING.md` | verify a release / build from source |

---

## Comparison

| Feature | Clearcote | Camoufox | CloakBrowser | Patchright |
|---------|:---------:|:--------:|:------------:|:----------:|
| Spoofing level | C++ engine | C++ engine | C++ engine | Binary patch |
| Engine | Chromium | Firefox | Chromium | Chromium |
| Open source | ✅ full | ✅ full | ⚠️ wrapper only | ✅ |
| Reproducible/signed builds | ✅ | ✅ | ❌ | N/A |
| Real-fingerprint import | ✅ | ❌ | ❌ | ❌ |
| Fingerprint rotation | per-seed | ✅ statistical | ✅ | ⚠️ |
| Human mouse | ✅ | ✅ | ✅ | ⚠️ |
| Platforms | Windows | Linux/mac/Win | Win/others | cross |
| Maturity | pre-release | mature | established | mature |

---

## Conclusion

Clearcote's pitch isn't "we beat service X" — it's **"read the source, rebuild it, and verify it."** Among custom anti-detect browsers it's distinctive for being **fully open and reproducible** (versus proprietary binaries) and for **importing and verifying real-machine fingerprints** (versus only generating synthetic ones), on a Chrome-compatible Chromium base.

**Best for:** auditability-conscious, Chromium-required, Windows automation where you want a coherent — ideally real-machine — identity and the ability to prove what the browser is presenting.

**Limitation:** Windows-only and an early pre-release, with no published benchmarks against commercial anti-bot services — its demonstrated results are against open-source fingerprint auditors.

---

*Analysis conducted for educational purposes. Use responsibly.*
