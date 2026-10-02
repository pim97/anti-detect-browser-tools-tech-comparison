# Clearcote - Deep Technical Analysis

> **Tool Type:** Custom Chromium Build (Anti-Detect Browser)
> **Repository:** [github.com/clearcotelabs/clearcote-browser](https://github.com/clearcotelabs/clearcote-browser)
> **Approach:** Engine-level (C++) fingerprint controls compiled into an ungoogled-chromium fork, plus real-machine fingerprint import
> **What is verified:** **37** human-readable patches in `patches/series`, applied over pinned Chromium `150.0.7871.114` (`UPSTREAM_REVISION`) — including `010-user-agent-and-webdriver`, `110-runtime-enable`, `100-webrtc-leak` (**Tier A**). This is the **open** build only: per the project README, the licensed builds (free with a GitHub account, or Pro) carry private patches that are not in the public tree (**Tier B**)
> **Anti-bot service claims:** **none** — publishes open-auditor results (CreepJS) and a self-referential coherence gate, not commercial-WAF pass rates; no named commercial anti-bot service appears anywhere in the public tree (**Tier D** for coverage; the auditor results are **Tier B**). The project's stated position is "don't trust us, verify us."
> **Maintenance:** Active but **experimental pre-release**, and **single-maintainer (1 contributor)** — the lowest contributor count of the ten tools compared. Browser `v0.1.0-pre.23` (2026-09-28; the open build moved from Chromium 149 to 150); SDK `clearcote` **0.33.0** on npm + PyPI (2026-09-29; the NuGet package version in `sdk/dotnet/src/Clearcote/Clearcote.csproj` is also 0.33.0). 170 stars, 27 forks, 9 open issues. BSD-3-Clause.
> **Verified:** 2026-09-30 against `clearcotelabs/clearcote-browser` @ `1596f29`.

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

Clearcote is an **open-source, de-Googled Chromium build** (BSD-3-Clause, built on [ungoogled-chromium](https://github.com/ungoogled-software/ungoogled-chromium)) that moves fingerprint control **into the C++ engine** rather than injecting JavaScript. Like [Camoufox](./camoufox.md) (Firefox) and [CloakBrowser](./cloakbrowser.md) (Chromium), the substitution happens in C++. Unlike either, Clearcote publishes no anti-bot service claims; its published evidence is open-auditor output and a coherence regression gate.

Two things define it:

1. **A coherent identity from one seed.** A single `--fingerprint=<seed>` derives an internally consistent persona (GPU, screen, hardware, locale, audio, fonts, voices) and applies deterministic per-site "farbling" (canvas/WebGL/audio), in the model [Brave](https://brave.com/privacy-updates/3-fingerprint-randomization/) pioneered. Same seed ⇒ same identity; different seed ⇒ an unlinkable one. Notably the noise is derived **per eTLD+1** (registrable domain), not from one global value — `components/ungoogled/farble_seed.{cc,h}` (`ungoogled::GetFarbleSeed64`) mixes the session root with the site so one site is stable while different sites are mutually unlinkable.
2. **Import of a *real* machine's fingerprint.** Beyond synthetic seeds, `--fingerprint-profile=<json>` makes the browser present a captured real Chrome's GPU / screen / fonts / voices / audio / WebGL `getParameter` table. Profiles come from a built-in collector, a curated library ([clearcote-profiles](https://github.com/clearcotelabs/clearcote-profiles)), or a converter for the open [10k-record dataset](https://github.com/Vinyzu/chrome-fingerprints).

Everything in the open build ships as **readable patches** on a pinned Chromium revision (`UPSTREAM_REVISION` → `150.0.7871.114`), with **GPG-signed, SHA-256-checksummed** release builds — the project's stated stance is "don't trust us, verify us." (The build is designed to be reproducible from source; `docs/VERIFY.md` states that Chromium cross-builds are **not yet bit-for-bit deterministic**, so a byte-identical hash match is the goal, not a guarantee today, and full build provenance/attestation is a roadmap item.) Per `CREDITS.md`, the engine-level controls build on adryfish's `fingerprint-chromium`, the farbling model is Brave's, and the in-browser agent layer is ported from `chromiumfish` (MIT).

**Open build vs licensed builds (Tier B — `README.md`, `llms.txt`, SDK READMEs).** The tree describes one open build and one licensed build. The open build needs no account, is described as reproducible from the public source, and exists for Chromium 149 and 150 (the README says new majors reach it about two months after release). The licensed build is free with a GitHub account (one browser at a time) or Pro ($49/month, up to 250 browsers at once); the README lists licensed builds for Chromium 151, 152 and 153, states that the licensed binary is *not* reproducible from public source, and lists as private additions recorded human mouse trajectories (the open build uses synthetic Bézier paths), coalesced pointer samples, WebRTC server-reflexive and host-candidate handling, and request-header hygiene on revalidation. It also states that no tier unlocks more spoofing. The public `100-webrtc-leak` patch already fabricates the srflx candidate and suppresses host candidates, so the README's tier table and the public patch overlap on WebRTC. The SDKs also contain options whose engine support is absent from `patches/` (a search of `patches/` at `1596f29` finds none of `--socks5-credentials`, `--proxy-auth`, `--socks5-udp`, `--fingerprint-schema`, `--fingerprint-gpu-backend-real`, `--disable-fingerprint-voices`); the SDK probes the binary for the switch and warns when it is missing (`sdk/node/src/launchopts.ts:182-233`). The README also advertises *hosted* Clearcote browsers (an API on clearcotelabs.com that returns a CDP URL, residential IP included, billed per GB); that service is not part of the tree and was not examined.

Clearcote is positioned as a **privacy / fingerprint-coherence browser**, not a service-specific bypass tool. Its published evidence comes from open-source fingerprint auditors (below), not commercial-WAF pass rates. Service coverage is therefore evidence Tier D.

---

## How It Works

### Architecture Overview

```
            Chromium (Google, BSD-3)   →  pinned 150.0.7871.114
                │
   ungoogled-chromium  →  removes Google services, telemetry, integration
                │
       Clearcote patches (37, human-readable)  →  engine-level identity controls
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
   Clearcote binary  +  Playwright drop-in SDKs (npm + PyPI + NuGet)
        │
   SDK auto-downloads + SHA-256-verifies the per-OS binary (Win x64 / Linux x64)
```

### Engine-level controls (not JS injection)

Identity getters are intercepted in C++ and seeded from the persona, so there is no JS wrapper, proxy, or `[native code]` mismatch for a page to inspect. The same approach Camoufox uses for Firefox, applied to Chromium across navigator/screen/WebGL/audio plus secondary surfaces (`getBattery`, `navigator.connection`, `keyboard.getLayoutMap`, `getScreenDetails`, CSS `@media`, `MediaCapabilities.decodingInfo()`, `enumerateDevices()`, `storage.estimate()`, `performance.memory`). The unmasked WebGL renderer is **session-constant** (one GPU on every origin, not a per-site tell), and canvas/WebGL/audio noise is **deterministic per eTLD+1** so it is stable within a session.

The patch set (37 diffs, listed in `patches/series` and applied in order) contains the behavioural changes; per `patches/README.md`, `900-windows-build-fixes` and `905-rc-invoked-guard` are Windows cross-build mechanics and `951-gfx-quadf-offset` carries an unused helper with no behaviour. Selected entries:

- `001-farble-seed-core` — the per-eTLD+1 seed engine + the `FingerprintNoiseEnabled()` master toggle behind `--disable-fingerprint-noise`. Since 150 it also exposes `CanvasNoiseEnabled()` behind `--disable-canvas-noise` (canvas 2D only), and `--disable-gpu-string-spoof` (switch defined in `000`) reports the real WebGL vendor/renderer strings while the rest of the persona stays on.
- `002-persona-profile` — the coherent persona engine (`components/ungoogled/persona_profile.{cc,h}`) *and* the profile-import loader `ApplyProfileOverride`.
- `010-user-agent-and-webdriver` — UA / UA-CH (incl. high-entropy `bitness`/`wow64`/`model`), `navigator.platform`, and hiding `navigator.webdriver` + automation/headless tells.
- `070-webgl-gpu` — session-constant unmasked GPU, the full `getParameter` table + `getSupportedExtensions`, plus `--disable-gpu-fingerprint` to present the host's **real** backend coherently.
- `071-webgl2-extension-split` / `955-webgl-persona-parity` (new in 150) — an imported profile's WebGL1 and WebGL2 extension lists apply to their own contexts, and the advertised extension set equals what `getExtension()` returns.
- `075-webgpu-coherence` — `navigator.gpu` adapter vendor/architecture/limits forced coherent with the WebGL GPU (so WebGPU can't contradict WebGL).
- `100-webrtc-leak` — fabricates the srflx candidate at `--webrtc-ip`, sends no real STUN, suppresses host candidates. (`enable_mdns` is `true` in `config/args.gn` since 150; the comment there says this patch, not that flag, decides which candidates exist.)
- `110-runtime-enable` / `120-headless` — the `Runtime.enable` tell is addressed by making the V8 inspector's Runtime agent skip binding registration, stop reporting console messages and report `enabled()` as false (`v8-runtime-agent-impl.{cc,h}`); the headless tell is the product token, changed from `HeadlessChrome` to `Chrome` (`headless_browser_impl.cc`).
- `130-humanized-input` — trusted CDP input + a cursor overlay, plus a cookie-serialization hardening fix. `200-agent-and-humanized-input` carries the in-browser agent (`--agent-llm-*`) and its humanized click path.
- `142-touch-pointer-coherence` (new in 150) — a desktop persona with touch points keeps a mouse as the primary pointer; an imported profile's touch-point count is applied. The patch header records a known gap: the CSS `any-pointer` bit does not follow a profile-imported touch count.
- `210-tls-network-persona` — version-variant TLS ClientHello fields follow a claimed Chromium major (see Network layer).
- `220-no-farble-switch` (new in 150) — a raw-string `--cc-no-farble` switch that keeps the persona and turns the per-site canvas/WebGL/audio/DOM noise off. Its own header says it overlaps `--disable-fingerprint-noise` and "should probably be reconciled", and that the switch is not a declared constant like the others.

### Real-machine fingerprint import

The SDK gzip+base64-encodes a captured profile into `--fingerprint-profile`; the renderer decodes and parses it and **overrides the seed-derived fields** with the real values (GPU vendor/renderer + the full `getParameter` table + extensions, screen geometry, `hardwareConcurrency`/`deviceMemory`, fonts, speech voices, audio metadata, CSS display metadata, media-device roster, codec matrix). Fields absent from the profile fall back to the seed, so partial profiles stay coherent. Notably, it imports the **device** identity but keeps Clearcote's own (current) Chrome version — importing the dataset's older version (records are Chrome ~114/115) would contradict the real UA, a self-inflicted tell (see `tools/fingerprint-collect/convert_dataset.py`, which skips `uaFullVersion` by default).

Since 150 the loader also applies the profile's touch-point count (`142`) and keeps separate WebGL1 and WebGL2 extension lists (`071`); it also reads `navigator.uadata.high_entropy.uaFullVersion` when a profile contains one (`patches/002-persona-profile.patch:267`), which is why the converter leaves it out by default. The SDKs additionally accept `profile="auto"`, which resolves a captured profile for the host from a licensed profile service on clearcotelabs.com (with a local-directory fallback) and sets no seed; SDK comments say a seed alongside a profile engages farbling and makes profile fields apply only partially (`sdk/python/clearcote/__init__.py:322,432`) (**Tier B**).

A bundled `verify_profile.py` launches the binary with a profile, reads the live surfaces, and prints a PASS/FAIL table — so you can confirm the browser is actually presenting what you imported.

### Real-GPU canvas bridge (opt-in)

Because you can't make one GPU emit another GPU's exact pixels in software, spoofing only the GPU *string* leaves a mismatch a strict pixel-vs-hardware check can notice. Clearcote's answer is the **canvas bridge** (`065-canvas-bridge` + the WebGL recorders in `060`/`070`): with `--canvas-bridge-url` set, it forwards canvas/WebGL **operations** (geometry, shaders, uniforms, draws, procedural textures, `readPixels`, `toDataURL`, and `measureText`) over a WebSocket to a real-GPU render host and returns that host's authentic pixels/metrics — so readbacks are coherent with the GPU the profile claims. It carries a **per-origin policy** (`--canvas-bridge-mode=off|all|allow|deny` + allow/deny eTLD+1 lists; default `all`), a cold-miss `--canvas-bridge-fallback=block|local`, and a speculative content-version prefetch. Unset, Clearcote renders locally exactly as before. Sources sourcing a texture from an image/2D-canvas/video, or using 3D textures, auto-fall-back to local rendering. See `docs/CANVAS-BRIDGE.md`, which marks the bridge experimental and lists `--no-sandbox` as required (the renderer opens the bridge socket, which the sandbox blocks; `docs/CANVAS-BRIDGE.md:6,140`); the SDKs add `--no-sandbox` automatically when a bridge URL is set (`sdk/node/src/fingerprint.ts:579-590`, `sdk/python/clearcote/_fingerprint.py:452-472`).

### Network layer

Chromium's TLS and HTTP/2 stack is stock Chrome's by default, so the JA3/JA4 and HTTP/2 shape come from the same Chromium as the JS-visible identity (no spoofed-JS-over-real-TLS mismatch). This is true of any real-Chromium tool; Clearcote is *not* an HTTP-impersonation library and offers no separate headless HTTP tier. One engine patch does sit in this layer: `210-tls-network-persona` (`net/socket/ssl_client_socket_impl.cc` plus new `net/ssl/network_persona.{h,cc}`) swaps only version-variant ClientHello fields — the post-quantum key-share group (X25519Kyber768 for claimed majors 124–130, none below 124) and the ALPS codepoint — when `--fingerprint-tls-profile=chrome-<major>` names a major different from the build's; with a claimed major equal to the build's it is a no-op, and the cipher list and extension permutation are untouched. The SDK passes the switch by default (`tls_profile="match-persona"`, `sdk/python/clearcote/_fingerprint.py:473-480`).

The SDK adds proxy handling: credentialed SOCKS5 proxies are routed via `--proxy-server` plus `--socks5-credentials` (HTTP(S) credentials via `--proxy-auth`) because Playwright rejects SOCKS credentials in its descriptor; neither credential switch appears in `patches/`, so on an engine without them the SDK warns (`sdk/node/src/launchopts.ts:158-169,221-233,265-290`). It sets `--webrtc-ip-handling-policy=disable_non_proxied_udp` by default (`launchopts.ts:135-140`) and disables QUIC/HTTP-3 when a proxy is set (`launchopts.ts:61-63`; a TCP proxy can't carry QUIC — real proxied Chrome falls back to TCP too, and this guarantees no UDP egresses around the proxy). An opt-in `socks5Udp` option relays WebRTC UDP through a SOCKS5 proxy with UDP ASSOCIATE; the SDK documents it as needing a PRO engine 151 r17+ (`launchopts.ts:65-86`, `sdk/node/src/index.ts:217`).

---

## What Makes It Different

Versus the other custom-browser entries here:

| | Clearcote | Camoufox | CloakBrowser |
|---|---|---|---|
| Engine | Chromium (Chrome-compatible) | Firefox | Chromium |
| Spoofing level | C++ engine | C++ engine | C++ engine |
| Source | **Open build**: BSD-3, 37 readable patches (licensed builds add private patches) | Fully open | Wrapper MIT; **binary proprietary** |
| Build verifiability | ✅ open build: build-from-source + GPG-signed + SHA-256 (bit-for-bit determinism = roadmap goal) | ✅ | ❌ (closed binary) |
| Synthetic fingerprint rotation | Per-seed personas | ✅ fpgen (statistical; repo HEAD) | ✅ |
| **Import a real machine's fingerprint** | ✅ + curated library + verifier | ⚠️ synthetic by default; opt-in bundle of pre-captured real presets (see [camoufox.md](./camoufox.md)); no capture-and-verify tool assessed | ❌ |
| Real-GPU render bridge | ✅ (opt-in canvas/WebGL op-forwarding) | ❌ | ❌ |
| Human mouse input | ✅ (trusted CDP `humanize` / `humanizedClick`; recorded human trajectories are licensed-build only per the README) | ✅ | ✅ |
| Platforms | **Windows x64 + Linux x64** | Linux/macOS/Windows | Windows/others |

Per the sources read, this entry has an **open, build-verifiable Chromium patch series** (the open build only — every change in it can be read and rebuilt, versus CloakBrowser's closed binary), **import of a captured machine's fingerprint with a verifier** (Camoufox ships a bundle of pre-captured real presets instead), and the opt-in, experimental **real-GPU canvas bridge** (renders canvas/WebGL on hardware that has the claimed GPU, rather than only spoofing the string); neither other column has a corresponding bridge.

---

## Fingerprint Capabilities

| Category | Controlled (seed *or* imported profile) |
|----------|-----------------------------------------|
| **Navigator** | UA + UA-CH brand/platform/version + high-entropy hints (`bitness`/`wow64`/`model`) (defaults to a real "Google Chrome" brand set), `hardwareConcurrency`, `deviceMemory` (real Chrome's power-of-two steps since 150), languages, `webdriver=false` (C++); `brand` can be Edge and `platform` accepts windows/linux/macos/android personas (UA/UA-CH level — binaries exist for Windows and Linux only) |
| **GPU / WebGL** | Unmasked vendor/renderer (session-constant), the full `getParameter` table (limits, bit depths, aliased ranges, anisotropy), supported-extension list (WebGL1 and WebGL2 lists kept separate, advertised set equals gettable set — 150); `--disable-gpu-fingerprint` presents the host's *real* GPU coherently, `--disable-gpu-string-spoof` swaps only the vendor/renderer strings (150) |
| **WebGPU** | `navigator.gpu` adapter vendor/architecture/device + `adapter.limits` forced coherent with the WebGL GPU |
| **Rendering noise** | Deterministic per-site canvas / WebGL / audio farbling — or **off** via `fingerprintNoise: false` / `--disable-fingerprint-noise` (for detectors that score noise itself as tampering), `--disable-canvas-noise` for canvas 2D only (150), or the raw-string `--cc-no-farble` (patch `220`) — plus an opt-in, experimental **real-GPU canvas bridge** for hardware-accurate readbacks |
| **Screen / window** | width/height/avail, colorDepth, devicePixelRatio, realistic window geometry, `maxTouchPoints=0` by default (honours `--fingerprint-max-touch-points` or an imported profile; a touch-capable desktop persona keeps a mouse as primary pointer — 150), a realistic `jsHeapSizeLimit`, `storage.estimate()` quota |
| **Audio** | AudioContext sampleRate / baseLatency / outputLatency; per-site AudioBuffer farbling |
| **Locale / network** | timezone + `navigator.languages` + `Accept-Language` + the ICU/`Intl` UI locale all pinned to one language (auto-matched to proxy region via `geoip`: the SDK finds the exit IP through the proxy with an IP-echo service and looks it up in an offline GeoIP database it downloads on first use, `sdk/node/src/geoip.ts:1-27`); WebRTC egress IP fabricated coherently (no STUN/LAN leak); TLS ClientHello version-variant fields follow a claimed Chromium major (`210`, no-op when it equals the build's) |
| **Long-tail** | speech voices, installed-font enumeration (per `patches/README.md`, since 150 a default Windows list of about 300 families and 231 metric-compatible substitutes for a Windows persona on Linux; clone fonts live in `assets/fonts/`), CSS `@media` (pointer/hover/color-gamut/resolution), battery, connection, keyboard layout, `getScreenDetails()`, `MediaCapabilities.decodingInfo()` codec matrix, `enumerateDevices()` roster |
| **DRM** | Opt-in Widevine / EME (`widevine=True`) — `requestMediaKeySystemAccess('com.widevine.alpha')` resolves like real Chrome (CDM fetched on demand from Google's own component server; never bundled) |
| **Behavior** | Bézier mouse movement as trusted input (SDK-side paths through Playwright's native mouse, or the engine's `Browser.humanizedClick`), capitals and shifted symbols typed through a real Shift key, humanize's DOM reads run in a CDP isolated world, optional visible cursor (an SDK-injected JS overlay); recorded human trajectories are licensed-build only (README) |

### Published evidence

The project states that each build is audited (**Tier B**) with in-repo scripts (`scripts/creepjs_audit.py`) against open-source fingerprint auditors (CreepJS) on real Windows: `navigator.webdriver = false`, UA ↔ UA-CH version consistent, WebRTC reports the mocked IP with no LAN leak, **0% headless / 0% stealth**, surfaces stable per seed. A **stealth-coherence regression gate** (`scripts/stealth_coherence.py`, documented in `docs/STEALTH-COHERENCE.md`) checks five self-referential invariants against the shipped Windows binary. Four are enforced (`REQUIRED`): `measureText` widths land on Chrome's native 1/512-px grid, agree between the main thread and an `OffscreenCanvas` worker, `getBoundingClientRect` agrees with `Range` rects, and the WebGPU vendor matches the WebGL `UNMASKED_VENDOR` family. The fifth, `origin-invariant` (canvas/WebGL hashes identical across two registrable domains in one session), is a documented `KNOWN_GAP`: readback is keyed by registrable domain by design, so the check is expected to fail and the gate fails only if it unexpectedly passes (`scripts/stealth_coherence.py:85-95`; `docs/STEALTH-COHERENCE.md`, "Current known gaps"). The gate's Windows job downloads the SDK-pinned `chrome.exe` and is called by the `npm.yml` and `pypi.yml` publish workflows (`workflow_call`) and by manual dispatch; it is not called from `nuget.yml` or `docker.yml`, and `docs/RELEASING.md` lists it in the release checklist. A separate `patch-integrity.yml` workflow runs Layer 0 (series ↔ patch files ↔ the 37-entry `scripts/patch_markers.json` manifest) on pushes and PRs that touch `patches/`; Layer 1 (reverse-applying the series against the build tree) is enforced at build time by `scripts/01-apply-patches.sh`; Layers 1 and 2 (marker strings present in the binary) are the mandatory pre-publish step 4a of `docs/RELEASING.md`, and in CI Layer 2 runs on demand against the pinned release binary (`docs/PATCH-INTEGRITY.md`). The repository has nine workflows in all. These are **open auditors, not commercial WAFs** — there are no published commercial-WAF pass rates.

---

## Pros and Cons

### Advantages

| Pro | Details |
|-----|---------|
| **Open + build-verifiable (open build)** | BSD-3, 37 readable patches, GPG-signed + SHA-256-checksummed builds you can rebuild and diff (bit-for-bit reproducibility is the stated goal, not yet guaranteed); the licensed builds are outside this. |
| **Engine-level (C++)** | Native getters — no JS-injection artifacts (`[native code]`, descriptor checks, timing). |
| **Real-fingerprint import** | Present a *real* machine's identity (collector + curated library + dataset converter), with a verifier to confirm it loaded. |
| **Real-GPU canvas bridge** | Opt-in op-forwarding renders canvas/WebGL on hardware that actually has the claimed GPU — coherent readbacks, not just a spoofed string. |
| **Coherent identity** | One seed → a consistent machine, stable per site; session-constant GPU; locale pinned end-to-end. |
| **Cross-platform binary** | Windows x64 (cross-compiled) **and** native Linux x64; runs in Docker (headful on Xvfb by default, headless optional). |
| **Drop-in automation** | Playwright SDKs for Node, Python and .NET (npm, PyPI, NuGet); `launch()` returns a standard Playwright `Browser` (`IBrowser` in .NET); Puppeteer and other CDP clients attach through the `serve()` endpoint; auto-downloads the right per-OS binary. |
| **Other entry points** | Standing CDP endpoint (`serve()` / `clearcote serve`; `serveMultiplex` runs one browser per identity), the `clearcote` CLI, the `clearcote-mcp` server (20 tools), and the `teamflatearth/clearcote` Docker image. |
| **In-browser AI agent** | `launchAgent` / `runAgentTask` + a `clearcote-agent` CLI drive a page from natural-language goals via OpenRouter (or any OpenAI-compatible endpoint), acting through Chrome's Actor framework with real trusted input. |
| **Privacy by default** | De-Googled base; the README states zero telemetry/phone-home (**Tier B**); the open build is free. With a licence key the SDK checks out a seat and keeps a heartbeat to clearcotelabs.com (`sdk/node/src/license.ts`). |
| **Noise toggle** | `fingerprintNoise: false` for sites that flag the noise itself. |

### Disadvantages

| Con | Details |
|-----|---------|
| **No macOS build yet** | Windows x64 + Linux x64 today; macOS + ARM64 are on the roadmap. |
| **Experimental pre-release** | Young project (`v0.1.0-pre.23`); APIs and binaries may change; not battle-tested at scale. |
| **Open/licensed split** | Newer Chromium majors (README: 151–153), recorded mouse motion and the private patches are licence-gated and not in the public tree; the open build trails by about two months per the README; SDK options such as `socks5Udp`, `persona_schema` and `shader_dialect` need an engine that is not in the open build. |
| **Open build is non-official and DCHECK-enabled** | `config/args.gn:41-48`: `is_official_build = false`, so upstream DCHECKs are fatal and can crash a tab on edge inputs; `docs/RELEASE-SMOKE-TEST.md` says the licensed build is an optimized release build that is not affected, and a root container needs `--cap-add=SYS_NICE` for the open build. |
| **No commercial-WAF benchmarks** | Evidence is open-auditor results, not published commercial-WAF pass rates. It is not marketed as a service-specific bypass. |
| **Not yet bit-for-bit reproducible** | Cross-builds aren't byte-deterministic today (embedded paths/timestamps/linker nondeterminism); patches + config are fully auditable, but attested reproducibility is a roadmap item. |
| **No CAPTCHA solving / proxy pool in the SDK** | No built-in solver or proxy pool in the SDK or binary. Separately, the vendor offers hosted browsers with residential IPs included (README, **Tier B**), and `llms.txt` lists a Profile Manager desktop app (a separate repository, not examined). |
| **Single seed = single identity per session** | Per-process persona; rotate by launching with a new seed/profile (`serveMultiplex` starts one browser per identity). |
| **Chromium build effort** | Building from source is a multi-hour job on a 16 GB+ Linux host (the published binary avoids this). |

---

## Installation & Usage

```bash
pip install clearcote          # Python
# or: npm install clearcote    # Node / TypeScript
# or: dotnet add package Clearcote   # .NET
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

The SDK auto-downloads + SHA-256-verifies the pinned binary **for your OS** (Windows x64 or Linux x64; archive and inner-binary hashes, `sdk/node/src/release.ts:35-64`) on first use, then caches it; without a licence key it fetches the open build (Chromium 150). Match a proxy's region automatically with `geoip=True`; add `humanize=True` for trusted mouse movement; `widevine=True` on a persistent context enables opt-in DRM.

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

**Standing CDP endpoint (any CDP client, including Puppeteer):** `clearcote-serve --port 9222 --fingerprint seed-123 --platform windows`, or `serve()` in code; `npx clearcote serve` starts the multi-identity form (one browser per identity, chosen by the connection URL). The MCP server is `npx -y clearcote-mcp` (20 tools).

**Verify what loaded:**

```bash
python tools/fingerprint-collect/verify_profile.py --executable <chrome> profile.json
#   hardwareConcurrency  12   12   PASS   ·   glRenderer  ANGLE (Intel, Arc A770 …)  …  PASS
#   VERIFIED: clearcote is loading the profile.
```

**Run in Docker (Linux):** `docker/Dockerfile` (browser runtime libs + a base font set so canvas/text hashes stay coherent + Xvfb + the SDK) is published as `teamflatearth/clearcote` and serves CDP on :9222; `docker/serve.py` runs the browser headful on Xvfb by default and pure-headless with `CC_HEADLESS=1`, taking the persona from `CC_*` environment variables. On Linux the persona defaults to a coherent **native Linux** identity (Linux-shaped GPU/voices/audio devices); `CC_PLATFORM=windows` / `platform: "windows"` spoofs Windows-on-Linux. Per `docker/README.md` the open build runs with DCHECKs, so a root container needs `--cap-add=SYS_NICE`.

---

## When to Use

### Recommended For

- Chromium-required targets where you want **native (non-JS) fingerprint control**
- Cases where **auditability matters** — you need to read/rebuild/verify the browser, not trust a binary
- Presenting a **specific real machine's** identity (or a library of them), not just random synthetic ones
- Needing **hardware-coherent canvas/WebGL readbacks** (via the real-GPU canvas bridge)
- Privacy-first browsing/automation on **Windows or Linux** (incl. headless in containers)
- Playwright users (Node, Python, .NET) wanting a drop-in with a coherent identity + `geoip`; Puppeteer and other CDP clients through the `serve()` endpoint
- Driving a page with a natural-language **in-browser AI agent** on a coherent identity

### Not Recommended For

- macOS targets (no build yet)
- Production work needing a proven track record against **enterprise anti-bot services** (it's pre-release and unbenchmarked there)
- Built-in **CAPTCHA solving** or a proxy pool in the SDK (the vendor offers hosted browsers separately)
- Firefox impersonation (use [Camoufox](./camoufox.md))

---

## Key Files

| File | Purpose |
|------|---------|
| `patches/` | 37 human-readable engine patches (`series` lists the order) — fingerprint switches, per-eTLD+1 farble core, persona + profile import, UA/webdriver, fonts, canvas + canvas-bridge, WebGL/WebGPU, audio/screen/media/touch, WebRTC leak, Runtime.enable/headless tells, humanized input + in-browser agent, TLS network persona, timezone/locale/geolocation, farble escape switch, Windows build fixes |
| `components/ungoogled/persona_profile.*`, `farble_seed.*` | `DerivePersona(seed)`, the per-eTLD+1 seed engine, and the `--fingerprint-profile` override loader |
| `tools/fingerprint-collect/` | profile collector (`collect.html`/`collect.js`), dataset converter (`convert_dataset.py`), and `verify_profile.py` |
| `tools/canvas-bridge-server/` | reference real-GPU canvas-bridge render host (`server.py`) |
| `sdk/node`, `sdk/python`, `sdk/dotnet` | Playwright drop-in SDKs (npm, PyPI, NuGet), each with a test suite; `clearcote` and `clearcote-agent` CLIs |
| `mcp/`, `docker/` | `clearcote-mcp` server (`mcp/clearcote_mcp/server.py`, 20 tools); Docker image sources (`docker/Dockerfile`, `docker/serve.py`) |
| `config/args.gn`, `config/args.linux.gn` | published GN build arguments (`is_official_build = false`) |
| `scripts/creepjs_audit.py`, `scripts/stealth_coherence.py` | per-build fingerprint audit + the stealth-coherence regression gate |
| `scripts/verify_patches.py`, `scripts/patch_markers.json`, `.github/workflows/` | the patch-integrity gate and its per-patch manifest; nine workflows (SDK publishing, CI, `stealth-coherence.yml`, `patch-integrity.yml`) |
| `docs/VERIFY.md`, `docs/BUILDING.md`, `docs/CANVAS-BRIDGE.md`, `docs/STEALTH-COHERENCE.md`, `docs/PATCH-INTEGRITY.md`, `patches/README.md` | verify a release / build from source / run the bridge / the coherence gate / the patch gate / per-patch notes |

---

## Comparison

| Feature | Clearcote | Camoufox | CloakBrowser | Patchright |
|---------|:---------:|:--------:|:------------:|:----------:|
| Spoofing level | C++ engine | C++ engine | C++ engine | Driver source patch (TypeScript) |
| Engine | Chromium | Firefox | Chromium | Chromium |
| Open source | ✅ open build | ✅ full | ⚠️ wrapper only | ✅ |
| Signed / checksummed builds | ✅ | ✅ | ✅ wrapper verifies a pinned Ed25519 signature over `SHA256SUMS` (binary closed) | N/A |
| Real-fingerprint import | ✅ | ⚠️ presets | ❌ | ❌ |
| Real-GPU render bridge | ✅ | ❌ | ❌ | ❌ |
| Fingerprint rotation | per-seed | ✅ statistical | ✅ | ❌ none in driver source |
| Human mouse | ✅ | ✅ | ✅ | ❌ none first-party |
| Platforms | Win + Linux | Linux/mac/Win | Win/others | cross |

---

## Conclusion

Clearcote's stated position is not service-specific coverage but **"read the source, rebuild it, and verify it"** (`README.md`, `docs/VERIFY.md`). Of the Chromium-engine forks in this report, only its open build publishes both the patch series and the build recipe (CloakBrowser ships a closed binary); it also has real-machine fingerprint import with a bundled verifier and an opt-in, experimental real-GPU canvas bridge, on a Chrome-compatible Chromium base. Since the previous verification (`dea4387`, `v0.1.0-pre.22`, Chromium 149) the open build moved to Chromium 150 (`v0.1.0-pre.23`) with five new patches (`071`, `142`, `220`, `951`, `955`); the SDKs went from 0.26.1 to 0.33.0 and gained the multi-identity CDP endpoint (`serveMultiplex`), a `clearcote` CLI, proxy-credential switches whose engine side is not in the public tree, and isolated-world DOM reads for `humanize`; and the README gained a "Free with GitHub" tier, a 250-browser Pro cap and a hosted-browsers section (Pro, with private patches, was already described at `dea4387` but was not covered on this page). Earlier additions remain: a native Linux x64 build alongside Windows, a multi-OS SDK, WebGPU/locale/speech coherence, opt-in Widevine/EME DRM, a humanized cursor, an in-browser AI agent and the stealth-coherence gate — with the project's own caveat that builds are not yet bit-for-bit reproducible.

**Applicability:** Chromium-based automation on Windows x64 or Linux x64 where the engine source must be readable and rebuildable. Distinguishing verified capabilities of the open build: 37 published patches, GPG-signed and SHA-256-checksummed builds, real-machine fingerprint import with a bundled verifier, and a `110-runtime-enable` patch.

**Constraints:** no macOS build; open browser build is `v0.1.0-pre.23` (non-official, DCHECK-enabled); newer Chromium majors, recorded mouse motion and private patches are in licensed builds that are not in the tree; 1 contributor; no published commercial-WAF results (evidence Tier D for service coverage); builds are not yet bit-for-bit reproducible per the project's own `docs/VERIFY.md`.

**Limitation:** still an early pre-release with **no macOS build** and **no published benchmarks against commercial anti-bot services** — its demonstrated results are against open-source fingerprint auditors (CreepJS, and the self-referential coherence gate).

---

*Analysis conducted for educational purposes. Use responsibly.*
