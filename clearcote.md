# Clearcote - Deep Technical Analysis

> **Tool Type:** Custom Chromium Build (Anti-Detect Browser)
> **Repository:** [github.com/clearcotelabs/clearcote-browser](https://github.com/clearcotelabs/clearcote-browser)
> **Approach:** Engine-level (C++) fingerprint controls compiled into an ungoogled-chromium fork, plus real-machine fingerprint import
> **What is verified:** **62** human-readable patches in `patches/series`, applied over pinned Chromium `151.0.7922.108` (`UPSTREAM_REVISION`) — including `010-user-agent-and-webdriver`, `110-runtime-enable`, `100-webrtc-leak` (**Tier A**). A separate open macOS build on Chromium 150 adds three font patches kept outside `series` (`patches/macos-150/`). This is the **open** build only: per the project README, the licensed builds (free with a GitHub account, or Pro) carry private patches that are not in the public tree (**Tier B**)
> **Anti-bot service claims:** **none** — publishes open-auditor results (CreepJS) and a self-referential coherence gate, not commercial-WAF pass rates (**Tier D** for coverage; the auditor results are **Tier B**). One commercial bot detector is now named in source: SDK comments say fingerprint.com's agent reported bot "bad" (`chromium_automation`) when Playwright's `--disable-features=MediaRouter` was in effect, measured by the vendor on 2026-11-01, and the SDK keeps MediaRouter enabled for that reason (`sdk/node/src/launchopts.ts:107-113`; the result is **Tier B**). The project's stated position is "don't trust us, verify us."
> **Maintenance:** Active but **experimental pre-release**, and **single-maintainer (1 contributor)** — the lowest contributor count of the ten tools compared. Browser `v0.1.0-pre.25` (GitHub release 2026-10-28; the open Windows and Linux build moved from Chromium 150 to 151 and is now an official build); `v0.1.0-pre.24` is an open **macOS arm64** build on Chromium 150 (`sdk/node/src/release.ts:65-82`). SDK `clearcote` **0.70.1** on npm + PyPI (2026-11-19; the NuGet package version in `sdk/dotnet/src/Clearcote/Clearcote.csproj:13` is also 0.70.1); `clearcote-mcp` 0.3.1. 272 stars, 37 forks, 5 open issues. BSD-3-Clause. **The `main` history was rewritten:** neither `fb3e7bb` nor `c1c4a03` is an ancestor of the current `main`, which starts at a root commit (`d5af782`, 2026-10-29) that adds the whole tree, followed by 55 commits. The sandbox clone has no SDK tag between `sdk-v0.49.0` and `sdk-v0.67.0` and no `v0.1.0-pre.24`/`pre.25` tag, so this pass compared trees (`fb3e7bb` and `c1c4a03` against `389653c`), not commits.
> **Verified:** 2026-11-20 against `clearcotelabs/clearcote-browser` @ `389653c` (`sdk-v0.70.1`; the tree pins `v0.1.0-pre.25`); `clearcote-profiles` @ `a5f6459`.

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

1. **A coherent identity from one seed.** A single `--fingerprint=<seed>` derives an internally consistent persona (GPU, screen, hardware, audio-context metadata, voices) and applies deterministic per-site "farbling" (canvas/WebGL), in the model [Brave](https://brave.com/privacy-updates/3-fingerprint-randomization/) pioneered. The font list is not drawn from the seed: the engine uses one canonical list per claimed OS, or an imported profile's own list (`patches/040-fonts.patch`, unchanged since `pre.23`; the engine side is described in `sdk/python/clearcote/_fontpersona.py:8-14`), and the README now says fonts, languages and timezone do not come from the seed (languages and timezone come from options or `geoip`) (**Tier B**). Same seed ⇒ same identity; different seed ⇒ an unlinkable one. Notably the noise is derived **per eTLD+1** (registrable domain), not from one global value — `components/ungoogled/farble_seed.{cc,h}` (`ungoogled::GetFarbleSeed64`) mixes the session root with the site so one site is stable while different sites are mutually unlinkable.
2. **Import of a *real* machine's fingerprint.** Beyond synthetic seeds, `--fingerprint-profile=<json>` makes the browser present a captured real Chrome's GPU / screen / fonts / voices / audio / WebGL `getParameter` table. Profiles come from a built-in collector, a curated library ([clearcote-profiles](https://github.com/clearcotelabs/clearcote-profiles)), or a converter for the open [10k-record dataset](https://github.com/Vinyzu/chrome-fingerprints).

Everything in the open build ships as **readable patches** on a pinned Chromium revision (`UPSTREAM_REVISION` → `151.0.7922.108`), with **GPG-signed, SHA-256-checksummed** release builds — the project's stated stance is "don't trust us, verify us." (The build is designed to be reproducible from source; `docs/VERIFY.md` states that Chromium cross-builds are **not yet bit-for-bit deterministic**, so a byte-identical hash match is the goal, not a guarantee today, and full build provenance/attestation is a roadmap item. Since `pre.25` the Windows and Linux builds are official ThinLTO + PGO builds using Chromium's own PGO profile, which the Windows build downloads separately from the source tarball, `config/args.gn:42-60`. `config/` holds GN arguments for Windows and Linux only; no build configuration for the open macOS build was found.) Per `CREDITS.md`, the engine-level controls build on adryfish's `fingerprint-chromium`, the farbling model is Brave's, and the in-browser agent layer is ported from `chromiumfish` (MIT).

**Open build vs licensed builds (Tier B — `README.md`, `llms.txt`, SDK READMEs).** The tree describes one open build and one licensed build. The open build needs no account, is described as reproducible from the public source, and exists for Chromium 149, 150 and 151 (151 since `v0.1.0-pre.25`; the README estimates 152 and 153 for November 2026, 154 and 155 for December, 156 and 157 for January 2027, "estimates ... not promises"). The licensed build is free with a GitHub account at least 30 days old (one browser at a time, latest build only) or Pro ($49/month, up to 250 browsers at once, older builds and version pinning); the README's November 2026 table lists licensed builds up to Chromium 157 (`157.0.8103.78`, Windows and Linux; macOS stops at 155), states that the licensed binary is *not* reproducible from public source, and lists as licensed-only "private stealth patches, recorded human motion, profile library". The per-feature table in `sdk/node/README.md` names the private additions: recorded human mouse trajectories (the open build uses synthetic Bézier paths), coalesced pointer samples, WebRTC server-reflexive and host-candidate handling, and request-header hygiene on revalidation. The README also states that no tier unlocks more spoofing. The public `100-webrtc-leak` patch already fabricates the srflx candidate and suppresses host candidates, so the README's tier table and the public patch overlap on WebRTC; the SDK and Docker comments nevertheless treat the open engine as having "no WebRTC UDP egress block" (see Network layer). Several switches the SDKs send that were absent from `patches/` at `fb3e7bb` are now in the open 151 series: `--socks5-credentials` (`963`, `984`), `--proxy-auth` (`978`), `--socks5-udp` (`973`), `--fingerprint-schema` and `--fingerprint-gpu-backend-real` (`980`), plus `--portable-profile` / `--profile-encryption-key` (`964`). A search of `patches/` at `389653c` still finds none of `--disable-fingerprint-voices`, `--allow-third-party-cookies`, `--block-third-party-cookies`, `--disable-runtime-suppression`, `--enable-runtime-bindings`, `--webrtc-direct-stun`, `--fingerprint-passthrough`, `--transparent-proxy`, `--fingerprint-noise-per-profile`, `--fingerprint-noise-flat-areas`, `--fingerprint-webgl-no-read-margin`, `--disable-socks5-udp-quic` or `cc-persona-host-facts`. The SDK probes the binary for a switch name before sending it (`sdk/node/src/launchopts.ts:507`), drops the gated ones it does not find, with a warning except for the cookie and noise-style switches (`:975-1033`), and its comments tie newer options to licensed engine revisions (`personaSchema` 3 to 7 to engines 154 r36 to 156 r51, `:669-686`; `noisePerProfile` to r60, `:988-990`). Some SDK comments still describe now-public features as licensed-only (`socks5Udp` "Needs a PRO engine 151 r17+", `sdk/node/src/index.ts:391-392`; `shaderDialect` "Requires a PRO engine ... 151 r15+", `shaderdialect.ts:23`), although `973` and `966` are in the open series.

**Server-side personas on licensed engines.** From licensed engine r51, per the SDK, the engine derives no persona of its own: before each launch the SDK asks a persona service (`persona.clearcotelabs.com` or `persona-us.clearcotelabs.com`) for a signed persona token, sending the persona switches, the host GPU vendor and, for an imported profile, the profile's exact JSON; the engine refuses to start without the token (`sdk/node/src/persona.ts:1-19,32-36`). The SDK sends nothing for engines without the r51 marker switch (`persona.ts:84-86`), which includes the open build. The engine side is in the licensed build and is **Tier B**. The README also advertises *hosted* Clearcote browsers (an API on clearcotelabs.com that returns a CDP URL, residential IP included, €1 per GB) and hosted agent runs; since SDK 0.41–0.44 the SDKs reach them through `launch(cloud=True)` / `CLEARCOTE_CLOUD=1` and a `Cloud` client (`sdk/node/src/cloud.ts:1-24`, humanized in the SDK by default). The service itself is not part of the tree and was not examined.

Clearcote is positioned as a **privacy / fingerprint-coherence browser**, not a service-specific bypass tool. Its published evidence comes from open-source fingerprint auditors (below), not commercial-WAF pass rates. Service coverage is therefore evidence Tier D.

---

## How It Works

### Architecture Overview

```
            Chromium (Google, BSD-3)   →  pinned 151.0.7922.108
                │
   ungoogled-chromium  →  removes Google services, telemetry, integration
                │
       Clearcote patches (62, human-readable)  →  engine-level identity controls
                │
        ┌───────┴────────────────────────────────┐
        │  --fingerprint=<seed>                   │   one seed → a coherent
        │     → DerivePersona(seed)               │   machine (per-eTLD+1 farble)
        │  --fingerprint-profile=<gzip+b64 JSON>  │   import a real machine's
        │     → ApplyProfileOverride(...)         │   exact identity
        └───────┬────────────────────────────────┘
                │
   official ThinLTO + PGO build (cross-compiled Windows /
   native Linux)  →  GPG-signed + SHA-256-checksummed binary
                │
   Clearcote binary  +  Playwright drop-in SDKs (npm + PyPI + NuGet)
        │
   SDK auto-downloads + SHA-256-verifies the per-OS binary
   (Win x64 / Linux x64: 151; macOS arm64: open 150 build, unsigned)
```

### Engine-level controls (not JS injection)

Identity getters are intercepted in C++ and seeded from the persona, so there is no JS wrapper, proxy, or `[native code]` mismatch for a page to inspect. The same approach Camoufox uses for Firefox, applied to Chromium across navigator/screen/WebGL/audio plus secondary surfaces (`getBattery`, `navigator.connection`, `keyboard.getLayoutMap`, `getScreenDetails`, CSS `@media`, `MediaCapabilities.decodingInfo()`, `enumerateDevices()`, `storage.estimate()`, `performance.memory`). The unmasked WebGL renderer is **session-constant** (one GPU on every origin, not a per-site tell), and canvas/WebGL noise is **deterministic per eTLD+1** so it is stable within a session. Audio samples are not noised: `020-audio` defines frame-count and sample-rate noise helpers, but their only call site is commented out (`patches/020-audio.patch:71,94,115`), so the patch sets `AudioContext` sample rate and latencies from the persona and leaves rendered samples as stock Blink produces them; the project README now says the same (`patches/README.md` still describes `AudioBuffer` farbling).

The patch set (62 diffs, listed in `patches/series` and applied in order) contains the behavioural changes; per `patches/README.md`, `900-windows-build-fixes` and `905-rc-invoked-guard` are Windows cross-build mechanics. Since `pre.23`, `951-gfx-quadf-offset` (an unused helper) was removed, 26 patches `960`–`985` were added, and stray backup-file hunks were dropped from `010`, `060` and `130` (no `.bak`-style target remains in `patches/`). Patches `956`–`958` (macOS persona fonts) apply only to the open 150 macOS build and are not in `series` (`patches/macos-150/README.md`). Selected entries:

- `001-farble-seed-core` — the per-eTLD+1 seed engine + the `FingerprintNoiseEnabled()` master toggle behind `--disable-fingerprint-noise`. Since 150 it also exposes `CanvasNoiseEnabled()` behind `--disable-canvas-noise` (canvas 2D only), and `--disable-gpu-string-spoof` (switch defined in `000`) reports the real WebGL vendor/renderer strings while the rest of the persona stays on.
- `002-persona-profile` — the coherent persona engine (`components/ungoogled/persona_profile.{cc,h}`) *and* the profile-import loader `ApplyProfileOverride`.
- `010-user-agent-and-webdriver` — UA / UA-CH (incl. high-entropy `bitness`/`wow64`/`model`), `navigator.platform`, and hiding `navigator.webdriver` + automation/headless tells.
- `070-webgl-gpu` — session-constant unmasked GPU, the full `getParameter` table + `getSupportedExtensions`, plus `--disable-gpu-fingerprint` to present the host's **real** backend coherently.
- `071-webgl2-extension-split` / `955-webgl-persona-parity` (new in 150) — an imported profile's WebGL1 and WebGL2 extension lists apply to their own contexts, and the advertised extension set equals what `getExtension()` returns.
- `075-webgpu-coherence` — `navigator.gpu` adapter vendor/architecture/limits forced coherent with the WebGL GPU (so WebGPU can't contradict WebGL).
- `100-webrtc-leak` — fabricates the srflx candidate at `--webrtc-ip`, sends no real STUN, suppresses host candidates, and with `--webrtc-ip` set turns non-proxied UDP back on (see Network layer). (`enable_mdns` is `true` in `config/args.gn` since 150; the comment there says this patch, not that flag, decides which candidates exist.)
- `110-runtime-enable` / `120-headless` — the `Runtime.enable` tell is addressed by making the V8 inspector's Runtime agent skip binding registration, stop reporting console messages and report `enabled()` as false (`v8-runtime-agent-impl.{cc,h}`); the headless tell is the product token, changed from `HeadlessChrome` to `Chrome` (`headless_browser_impl.cc`). An SDK comment records the side effects with Playwright (`setContent()` times out, the `console` and `pageerror` page events receive nothing, and `exposeFunction()`/`exposeBinding()` stop working after a navigation) and adds an opt-in `stockRuntime` that passes `--disable-runtime-suppression` only on licensed engines r32+, which carry a private patch (`1043`) restoring stock behaviour; on the open build the option is not applied and the SDK warns (`sdk/node/src/launchopts.ts:1060-1100`). A narrower opt-in, `runtimeBindings` (`--enable-runtime-bindings`), restores only `exposeFunction()`/`exposeBinding()` across navigations on licensed engines r54+ and is likewise not applied on the open build (`launchopts.ts:1115-1150`).
- `130-humanized-input` — trusted CDP input + a cursor overlay, plus a cookie-serialization hardening fix. `200-agent-and-humanized-input` carries the in-browser agent (`--agent-llm-*`) and its humanized click path.
- `142-touch-pointer-coherence` (new in 150) — a desktop persona with touch points keeps a mouse as the primary pointer; an imported profile's touch-point count is applied. The patch header records a known gap: the CSS `any-pointer` bit does not follow a profile-imported touch count. `977-persona-active-predicate` (151) states that it closes this: a touch-capable desktop persona now also reports `any-pointer:coarse`, and a profile import drives the same surfaces as a seed (`patches/977-persona-active-predicate.patch:14-16,277-307`).
- `210-tls-network-persona` — version-variant TLS ClientHello fields follow a claimed Chromium major (see Network layer).
- `220-no-farble-switch` (new in 150) — a raw-string `--cc-no-farble` switch that keeps the persona and turns the per-site canvas/WebGL/DOM noise off (it also gates `020`'s unused audio-noise helpers). Its own header says it overlaps `--disable-fingerprint-noise` and "should probably be reconciled", and that the switch is not a declared constant like the others.
- New in 151 (`960`–`985`, per `patches/README.md` and the patch headers): `960` removes the page-visible `fakeShadowRoot` attribute that `050` exposed and moves the version pool to 151; `961`/`962` make `Sec-CH-DPR`, the `resolution` media query, `srcset`/`image-set()` and pointer-event screen coordinates follow the persona; `963`/`984` (RFC 1929 SOCKS5 authentication, `--socks5-credentials`), `978` (`--proxy-auth`, engine-side HTTP proxy authentication) and `973` (SOCKS5 UDP ASSOCIATE behind `--socks5-udp`, plus a developer smoke-test tool); `964` (portable cookie key, opt-in); `965` (bit-exact Windows `Math.tanh` for a Windows persona); `966` (opt-in HLSL shader dialect via `CLEARCOTE_SHADER_DIALECT=hlsl`); `967`–`970`, `982`, `983`, `985` (WebGPU limits clamped to the real adapter, D3D11 shader precision, no ASTC/ETC for a Windows persona on a non-D3D host, `bgra8unorm` preferred format, WebGPU features and architecture per GPU model, stencil masks); `971`, `972`, `975` (system-ui font, window frame, initial window fits the work area); `974` (`--clearcote-validate-persona`, a cross-surface self-check that prints a report and exits); `976` (Android uniform limits); `977` (one persona-activation rule: no persona = host values, seed = persona plus per-site noise, profile = capture without noise); `979` (battery values substituted at the dispatcher); `980`/`981` (opt-in persona schema 2, `--fingerprint-schema=2`).

### Real-machine fingerprint import

The SDK gzip+base64-encodes a captured profile into `--fingerprint-profile`; the renderer decodes and parses it and **overrides the seed-derived fields** with the real values (GPU vendor/renderer + the full `getParameter` table + extensions, screen geometry, `hardwareConcurrency`/`deviceMemory`, fonts, speech voices, audio metadata, CSS display metadata, media-device roster, codec matrix). Fields absent from the profile fall back to the seed (with no seed, to the seed-0 base persona, and with no per-site noise; `patches/977-persona-active-predicate.patch:10-13`), so partial profiles stay coherent. The README now says to use a profile *instead of* a seed: a seed next to a profile adds canvas noise that strict checkers score as tampering (**Tier B**). Notably, it imports the **device** identity but keeps Clearcote's own (current) Chrome version — importing the dataset's older version (records are Chrome ~114/115) would contradict the real UA, a self-inflicted tell (see `tools/fingerprint-collect/convert_dataset.py`, which skips `uaFullVersion` by default).

Since 150 the loader also applies the profile's touch-point count (`142`) and keeps separate WebGL1 and WebGL2 extension lists (`071`); it also reads `navigator.uadata.high_entropy.uaFullVersion` when a profile contains one (`patches/002-persona-profile.patch:267`), which is why the converter leaves it out by default; since 151 a capture's version is honoured only within the engine's own major (`977-persona-active-predicate.patch:14`). Since SDK 0.69.1 `encodeProfile` adds the PCI device id that Chrome 118+ prints to the WebGL renderer string of older captures (`sdk/node/src/angledeviceid.ts`; the same table is applied to `clearcote-profiles` at `a5f6459`). The SDKs additionally accept `profile="auto"`, which resolves a captured profile for the host from a licensed profile service on clearcotelabs.com (with a local-directory fallback) and sets no seed; SDK comments say a seed alongside a profile engages farbling and makes profile fields apply only partially (`sdk/python/clearcote/__init__.py:441-449,693-695`) (**Tier B**). On licensed r51+ engines the profile no longer travels on the command line but goes to the persona service (`sdk/node/src/persona.ts:14-16`).

A bundled `verify_profile.py` launches the binary with a profile, reads the live surfaces, and prints a PASS/FAIL table — so you can confirm the browser is actually presenting what you imported.

### Real-GPU canvas bridge (opt-in)

Because you can't make one GPU emit another GPU's exact pixels in software, spoofing only the GPU *string* leaves a mismatch a strict pixel-vs-hardware check can notice. Clearcote's answer is the **canvas bridge** (`065-canvas-bridge` + the WebGL recorders in `060`/`070`): with `--canvas-bridge-url` set, it forwards canvas/WebGL **operations** (geometry, shaders, uniforms, draws, procedural textures, `readPixels`, `toDataURL`, and `measureText`) over a WebSocket to a real-GPU render host and returns that host's authentic pixels/metrics — so readbacks are coherent with the GPU the profile claims. It carries a **per-origin policy** (`--canvas-bridge-mode=off|all|allow|deny` + allow/deny eTLD+1 lists; default `all`), a cold-miss `--canvas-bridge-fallback=block|local`, and a speculative content-version prefetch. Unset, Clearcote renders locally exactly as before. Sources sourcing a texture from an image/2D-canvas/video, or using 3D textures, auto-fall-back to local rendering. See `docs/CANVAS-BRIDGE.md`, which marks the bridge experimental and lists `--no-sandbox` as required (the renderer opens the bridge socket, which the sandbox blocks; `docs/CANVAS-BRIDGE.md:6,140`); the SDKs add `--no-sandbox` automatically when a bridge URL is set (`sdk/node/src/fingerprint.ts:746-757`, `sdk/python/clearcote/_fingerprint.py:615-636`).

### Network layer

Chromium's TLS and HTTP/2 stack is stock Chrome's by default, so the JA3/JA4 and HTTP/2 shape come from the same Chromium as the JS-visible identity (no spoofed-JS-over-real-TLS mismatch). This is true of any real-Chromium tool; Clearcote is *not* an HTTP-impersonation library and offers no separate headless HTTP tier. One engine patch does sit in this layer: `210-tls-network-persona` (`net/socket/ssl_client_socket_impl.cc` plus new `net/ssl/network_persona.{h,cc}`) swaps only version-variant ClientHello fields — the post-quantum key-share group (X25519Kyber768 for claimed majors 124–130, none below 124) and the ALPS codepoint — when `--fingerprint-tls-profile=chrome-<major>` names a major different from the build's; with a claimed major equal to the build's it is a no-op, and the cipher list and extension permutation are untouched. The SDK passes the switch by default (`tls_profile="match-persona"`, `sdk/python/clearcote/_fingerprint.py:637-644`).

The SDK adds proxy handling: credentialed SOCKS5 proxies are routed via `--proxy-server` plus `--socks5-credentials`, and HTTP(S) credentials via `--proxy-auth` when the binary carries that switch (otherwise they stay with Playwright, whose credential handling turns on request interception), because Playwright rejects SOCKS credentials in its descriptor (`sdk/node/src/launchopts.ts:725-756`). Both switches are now in the open 151 build (`963`/`984`, `978`); on an engine without SOCKS5 authentication the SDK warns (`launchopts.ts:689-690`). It sets `--webrtc-ip-handling-policy=disable_non_proxied_udp` by default (`launchopts.ts:410-415`) and disables QUIC/HTTP-3 when a proxy is set (`launchopts.ts:211-221`; a TCP proxy can't carry QUIC — real proxied Chrome falls back to TCP too). On the open build that policy does not hold once a WebRTC IP is given: `100-webrtc-leak` sets `enable_nonproxied_udp = true` whenever `--webrtc-ip` is present (`patches/100-webrtc-leak.patch:34-41`, unchanged since `pre.23`), and the SDK's own comment says the open build "has no WebRTC UDP egress block", so a page's TURN server could read the real address; the SDK therefore drops a WebRTC IP that its *default* geo lookup filled on open-build launches through a proxy, but keeps one set explicitly or with `geoip: true` (`sdk/node/src/geoip.ts:476-494`). An opt-in `socks5Udp` option relays WebRTC UDP through a SOCKS5 proxy with UDP ASSOCIATE; the engine side (`973`) is now in the open build, although the SDK still documents it as needing a PRO engine 151 r17+ (`launchopts.ts:226-249`, `sdk/node/src/index.ts:382-393`). Since SDK 0.67.0 the SDK first asks the proxy for a UDP association and launches without the relay, with a warning, when the proxy refuses (`launchopts.ts:331-349`); on licensed r54+ engines HTTP/3 is carried through the relay (`launchopts.ts:215-224`). Since SDK 0.45.0 every launch also sends `--allow-third-party-cookies` (or `--block-third-party-cookies` with `allowThirdPartyCookies: false`); neither switch is in `patches/`, and the SDK drops them without a warning on an engine that lacks them (`launchopts.ts:995-1003,1036-1053`). Per the SDK's option comment an engine before 152 r22 always blocks third-party cookies (`sdk/node/src/index.ts:297-301`), so the open 151 build blocks them whatever the option says (**Tier B**, engine behaviour not in the public patches).

---

## What Makes It Different

Versus the other custom-browser entries here:

| | Clearcote | Camoufox | CloakBrowser |
|---|---|---|---|
| Engine | Chromium (Chrome-compatible) | Firefox | Chromium |
| Spoofing level | C++ engine | C++ engine | C++ engine |
| Source | **Open build**: BSD-3, 62 readable patches (licensed builds add private patches) | Fully open | Wrapper MIT; **binary proprietary** |
| Build verifiability | ✅ open build: build-from-source + GPG-signed + SHA-256 (bit-for-bit determinism = roadmap goal) | ✅ | ❌ (closed binary) |
| Synthetic fingerprint rotation | Per-seed personas | ✅ fpgen (statistical; repo HEAD) | ✅ |
| **Import a real machine's fingerprint** | ✅ + curated library + verifier | ⚠️ synthetic by default; opt-in bundle of pre-captured real presets (see [camoufox.md](./camoufox.md)); no capture-and-verify tool assessed | ❌ |
| Real-GPU render bridge | ✅ (opt-in canvas/WebGL op-forwarding) | ❌ | ❌ |
| Human mouse input | ✅ (trusted CDP `humanize` / `humanizedClick`; recorded human trajectories are licensed-build only per the README) | ✅ | ✅ |
| Platforms | **Windows x64 + Linux x64** (open 151); **macOS arm64** (open 150, unsigned); Intel macOS through the Docker image | Linux/macOS/Windows | Windows/others |

Per the sources read, this entry has an **open, build-verifiable Chromium patch series** (the open build only — every change in it can be read and rebuilt, versus CloakBrowser's closed binary), **import of a captured machine's fingerprint with a verifier** (Camoufox ships a bundle of pre-captured real presets instead), and the opt-in, experimental **real-GPU canvas bridge** (renders canvas/WebGL on hardware that has the claimed GPU, rather than only spoofing the string); neither other column has a corresponding bridge.

---

## Fingerprint Capabilities

| Category | Controlled (seed *or* imported profile) |
|----------|-----------------------------------------|
| **Navigator** | UA + UA-CH brand/platform/version + high-entropy hints (`bitness`/`wow64`/`model`) (defaults to a real "Google Chrome" brand set), `hardwareConcurrency`, `deviceMemory` (real Chrome's power-of-two steps since 150), languages, `webdriver=false` (C++); `brand` can be Edge and `platform` accepts windows/linux/macos/android personas (UA/UA-CH level — binaries exist for Windows, Linux and Apple Silicon macOS) |
| **GPU / WebGL** | Unmasked vendor/renderer (session-constant), the full `getParameter` table (limits, bit depths, aliased ranges, anisotropy), supported-extension list (WebGL1 and WebGL2 lists kept separate, advertised set equals gettable set — 150); `--disable-gpu-fingerprint` presents the host's *real* GPU coherently, `--disable-gpu-string-spoof` swaps only the vendor/renderer strings (150); for a Windows persona on a non-D3D host, D3D11 shader precision, no ASTC/ETC extensions and an opt-in HLSL shader dialect (151: `966`, `968`, `969`); stencil masks from the persona (`985`) |
| **WebGPU** | `navigator.gpu` adapter vendor/architecture/device + `adapter.limits` forced coherent with the WebGL GPU; since 151 limits are clamped to the real adapter, features and architecture follow the GPU model, and `getPreferredCanvasFormat()` is `bgra8unorm` for a Windows persona (`967`, `970`, `982`, `983`) |
| **Rendering noise** | Deterministic per-site canvas / WebGL farbling (audio samples are not noised, see above) — or **off** via `fingerprintNoise: false` / `--disable-fingerprint-noise` (for detectors that score noise itself as tampering), `--disable-canvas-noise` for canvas 2D only (150), or the raw-string `--cc-no-farble` (patch `220`) — plus an opt-in, experimental **real-GPU canvas bridge** for hardware-accurate readbacks. SDK options for licensed engines only: one noise seed per profile instead of per site (`noisePerProfile`, r60) and the r57 noise placement (`flatAreaNoise`, `webglReadMargin`) (`sdk/node/src/launchopts.ts:979-1005`) |
| **Screen / window** | width/height/avail, colorDepth, devicePixelRatio (also `Sec-CH-DPR`, the `resolution` media query and `srcset` since 151: `961`, `962`), realistic window geometry (window frame and initial window fit the persona's work area since 151: `972`, `975`), `maxTouchPoints=0` by default (honours `--fingerprint-max-touch-points` or an imported profile; a touch-capable desktop persona keeps a mouse as primary pointer — 150), a realistic `jsHeapSizeLimit`, `storage.estimate()` quota |
| **Audio** | AudioContext sampleRate / baseLatency / outputLatency from the persona (host values when no persona is active, `977`); rendered samples are not noised (`020-audio.patch:115`) |
| **Locale / network** | timezone + `navigator.languages` + `Accept-Language` + the ICU/`Intl` UI locale all pinned to one language (matched to the exit IP's region by `geoip`: the SDK finds the exit IP through the proxy with an IP-echo service (`api.ipify.org`, `icanhazip.com`, or `CLEARCOTE_GEOIP_ECHO_URL`) and looks it up in an offline GeoIP database it downloads on first use; the ip-api.com fallback is off by default, `sdk/node/src/geoip.ts:1-20,30-39`). **The lookup now runs by default**: with `geoip` unset ("auto" mode) the SDK fills any unset timezone, language, location and WebRTC IP and, on failure, warns and launches; `geoip: false` or `CLEARCOTE_GEOIP=off` skips it, `geoip: true` fails closed (`geoip.ts:402-407,448-474`; called on every launch path, `sdk/node/src/index.ts:1167,1328,1686`). WebRTC egress IP fabricated coherently (no STUN/LAN leak; see Network layer for UDP on the open build); TLS ClientHello version-variant fields follow a claimed Chromium major (`210`, no-op when it equals the build's) |
| **Long-tail** | speech voices, installed-font enumeration (per `patches/README.md`, since 150 a default Windows list of about 300 families and 231 metric-compatible substitutes for a Windows persona on Linux; `system-ui` resolves to Segoe UI for a Windows persona on Linux since 151, `971`; clone fonts live in `assets/fonts/`), bit-exact Windows `Math.tanh` for a Windows persona (`965`), CSS `@media` (pointer/hover/color-gamut/resolution), battery (substituted at the dispatcher since 151, `979`), connection, keyboard layout, `getScreenDetails()`, `MediaCapabilities.decodingInfo()` codec matrix, `enumerateDevices()` roster |
| **DRM** | Widevine / EME — `requestMediaKeySystemAccess('com.widevine.alpha')` resolves like real Chrome (CDM fetched on demand from Google's own component server; never bundled). Opt-in (`widevine=True`) for open-build launches; since SDK 0.48.0 on by default for licensed launches on an engine r32+ (`sdk/node/src/widevine.ts:13-22,403-413`) |
| **Behavior** | Bézier mouse movement as trusted input (SDK-side paths through Playwright's native mouse; an engine-routed click is opt-in via `CLEARCOTE_HUMANIZE_ENGINE_CLICKS`), with a per-seed motor persona (arcs, overshoot; since SDK 0.68.0 per-identity speed and rhythm, a longest step of 55–110 px drawn per persona, `sdk/node/src/motion.ts:655-664`, and the pointer moving off after a click), paths paced against a wall clock, scrolling in whole wheel notches, key rollover, and humanized form filling (selects, ranges, date segments, `maxlength`, masked fields; `sdk/node/src/forms.ts`, shared test vectors across the three SDKs); since SDK 0.68.0 a reading pause of 0.8–4 s after a page load before the next action, on by default (`attention: false` opts out; `sdk/node/src/attention.ts:1-14`); capitals and shifted symbols typed through a real Shift key, humanize's DOM reads run in a CDP isolated world, optional visible cursor (an SDK-injected JS overlay); recorded human trajectories are licensed-build only (README) |

### Published evidence

The project states that each build is audited (**Tier B**) with in-repo scripts (`scripts/creepjs_audit.py`) against open-source fingerprint auditors (CreepJS) on real Windows: `navigator.webdriver = false`, UA ↔ UA-CH version consistent, WebRTC reports the mocked IP with no LAN leak, **0% headless / 0% stealth**, surfaces stable per seed. A **stealth-coherence regression gate** (`scripts/stealth_coherence.py`, documented in `docs/STEALTH-COHERENCE.md`) checks five self-referential invariants against the shipped Windows binary. Four are enforced (`REQUIRED`): `measureText` widths land on Chrome's native 1/512-px grid, agree between the main thread and an `OffscreenCanvas` worker, `getBoundingClientRect` agrees with `Range` rects, and the WebGPU vendor matches the WebGL `UNMASKED_VENDOR` family. The fifth, `origin-invariant` (canvas/WebGL hashes identical across two registrable domains in one session), is a documented `KNOWN_GAP`: readback is keyed by registrable domain by design, so the check is expected to fail and the gate fails only if it unexpectedly passes (`scripts/stealth_coherence.py:85-95`; `docs/STEALTH-COHERENCE.md`, "Current known gaps"). The gate's Windows job downloads the SDK-pinned `chrome.exe` and is called by the `npm.yml`, `pypi.yml` and `nuget.yml` publish workflows (`workflow_call`; `nuget.yml:46`) and by manual dispatch; it is not called from `docker.yml`, and `docs/RELEASING.md` lists it in the release checklist. A separate `patch-integrity.yml` workflow runs Layer 0 (series ↔ patch files ↔ the 62-entry `scripts/patch_markers.json` manifest) on pushes and PRs that touch `patches/`; Layer 1 (reverse-applying the series against the build tree) is enforced at build time by `scripts/01-apply-patches.sh`; Layers 1 and 2 (marker strings present in the binary) are the mandatory pre-publish step 4a of `docs/RELEASING.md`, and in CI Layer 2 runs on demand against the pinned release binary (`docs/PATCH-INTEGRITY.md`). The repository has ten workflows in all (an `mcp-registry.yml` that publishes the MCP registry entry was added). These are **open auditors, not commercial WAFs** — there are no published commercial-WAF pass rates.

---

## Pros and Cons

### Advantages

| Pro | Details |
|-----|---------|
| **Open + build-verifiable (open build)** | BSD-3, 62 readable patches, GPG-signed + SHA-256-checksummed builds you can rebuild and diff (bit-for-bit reproducibility is the stated goal, not yet guaranteed); the licensed builds are outside this. |
| **Engine-level (C++)** | Native getters — no JS-injection artifacts (`[native code]`, descriptor checks, timing). |
| **Real-fingerprint import** | Present a *real* machine's identity (collector + curated library + dataset converter), with a verifier to confirm it loaded. |
| **Real-GPU canvas bridge** | Opt-in op-forwarding renders canvas/WebGL on hardware that actually has the claimed GPU — coherent readbacks, not just a spoofed string. |
| **Coherent identity** | One seed → a consistent machine, stable per site; session-constant GPU; locale pinned end-to-end; since 151 one persona-activation rule across surfaces (`977`) and a built-in persona self-check (`--clearcote-validate-persona`, `974`). |
| **Cross-platform binary** | Windows x64 (cross-compiled) **and** native Linux x64 (open 151); an open **macOS arm64** build (Chromium 150, `v0.1.0-pre.24`, unsigned and not notarized, `docs/VERIFY.md` §2a) that the SDK runs natively on Apple Silicon without a licence key since SDK 0.68.4 (`sdk/node/src/release.ts:65-82`); runs in Docker (headful on Xvfb by default, headless optional); on an Intel Mac `launch()` starts the Docker image through Docker Desktop (`sdk/node/src/docker.ts:1-17`). |
| **Drop-in automation** | Playwright SDKs for Node, Python and .NET (npm, PyPI, NuGet); `launch()` returns a standard Playwright `Browser` (`IBrowser` in .NET); Puppeteer and other CDP clients attach through the `serve()` endpoint; auto-downloads the right per-OS binary. |
| **Other entry points** | Standing CDP endpoint (`serve()` / `clearcote serve`; `serveMultiplex` runs one browser per identity), the `clearcote` CLI, the `clearcote-mcp` server (0.3.1; 20 tools, plus `run_task` when `CLEARCOTE_API_KEY` is set, `mcp/clearcote_mcp/server.py:536-538`; also packaged as an MCPB bundle in `mcp/mcpb/`), the Docker image (`teamflatearth/clearcote`, also pushed to `ghcr.io/clearcotelabs/clearcote` by `docker.yml`), and hosted browsers through `launch(cloud=True)` (vendor service, not examined). |
| **In-browser AI agent** | `launchAgent` / `runAgentTask` + a `clearcote-agent` CLI drive a page from natural-language goals via OpenRouter (or any OpenAI-compatible endpoint), acting through Chrome's Actor framework with real trusted input. |
| **De-Googled browser** | De-Googled base (ungoogled-chromium removes Google services and telemetry); `AGENTS.md:121` tells contributors not to add phone-home calls; the open build is free. No browser-originated launch request was found. SDK network calls outside the page: **by default on every launch**, the `geoip` lookup (an IP echo to `api.ipify.org` / `icanhazip.com`, through the proxy when one is set; direct lookups are cached for 10 minutes; the GeoIP database from GitHub on first use and when older than 30 days), skipped with `geoip: false` or `CLEARCOTE_GEOIP=off` (`sdk/node/src/geoip.ts:30-39,402-474`); with a licence key, a seat checkout and heartbeat to `lease.clearcotelabs.com` (fallback `www.clearcotelabs.com`, `sdk/node/src/license.ts:20-38`) and, on r51+ licensed engines, a persona-token request per launch (`persona.ts`); with `profile="auto"`, the profile service; with `version`, the version catalog on clearcotelabs.com (`download.ts:1336-1338,1372-1375`); the Widevine CDM fetch from Google when Widevine is on; an opt-in CRLSet fetch from Google's component updater (`crlset`, `sdk/node/src/index.ts:346-361`). |
| **Noise toggle** | `fingerprintNoise: false` for sites that flag the noise itself. |

### Disadvantages

| Con | Details |
|-----|---------|
| **macOS: one major behind, unsigned, arm64 only** | The open macOS build is Chromium 150 (`v0.1.0-pre.24`) while Windows and Linux are on 151; it is not signed with an Apple Developer ID or notarized, so the quarantine flag must be cleared (`docs/VERIFY.md` §2a; the SDK clears it after the hash check, `release.ts:65-69`); its three font patches are not rebased to 151 and no macOS GN configuration is published (`patches/macos-150/README.md`, `config/`). Intel Macs get the linux/amd64 Docker image instead. |
| **Experimental pre-release** | Young project (`v0.1.0-pre.25`); APIs and binaries may change; not battle-tested at scale. |
| **Open/licensed split** | Newer Chromium majors (README: licensed up to 157, open 151), recorded mouse motion and the private patches are licence-gated and not in the public tree; the open build trails by about two months per the README; SDK options such as `personaSchema` 3–7, `stockRuntime`, `runtimeBindings`, `noisePerProfile`, pass-through (`fingerprint: "off"`), `transparentProxy` and the third-party-cookie switches need an engine that is not in the open build (`socks5Udp`, `personaSchema` 2 and the HLSL shader dialect now have their engine side in the open 151 series); on r51+ licensed engines every launch also depends on the vendor's persona service; Free with GitHub is latest-build only (pinning is Pro). |
| **Open 150 and older were DCHECK-enabled** | Up to `pre.23` the open build was non-official, so upstream DCHECKs were fatal ("page crashed!" / `STATUS_BREAKPOINT`) and a root container needed `--cap-add=SYS_NICE`. Since `pre.25` (151) it is an official build with DCHECKs compiled out (`config/args.gn:42-48`; `docs/RELEASE-SMOKE-TEST.md:76-83`; `docker/README.md:355-359`). The open macOS build is Chromium 150; whether it was built official is not stated in the tree (**Tier D**). |
| **No commercial-WAF benchmarks** | Evidence is open-auditor results, not published commercial-WAF pass rates. It is not marketed as a service-specific bypass. |
| **Not yet bit-for-bit reproducible** | Cross-builds aren't byte-deterministic today (embedded paths/timestamps/linker nondeterminism); patches + config are fully auditable, but attested reproducibility is a roadmap item. |
| **No CAPTCHA solving / proxy pool in the SDK** | No built-in solver or proxy pool in the SDK or binary. Separately, the vendor offers hosted browsers with residential IPs included (README, **Tier B**), and `llms.txt` lists a Profile Manager desktop app (a separate repository, not examined). |
| **Single seed = single identity per session** | Per-process persona; rotate by launching with a new seed/profile (`serveMultiplex` starts one browser per identity). |
| **Chromium build effort** | Since 151 the official ThinLTO build of the Windows target takes about 12 hours on 8 cores and about 31 GB of RAM at the link (`docs/BUILDING.md:21,105`, `config/args.gn:45-46`; vendor figures, **Tier B**); the published binary avoids this. |

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

# or import a real machine's identity (ready-made profile from clearcote-profiles);
# the README says to pass a profile instead of a seed, not with one
browser = launch(fingerprint_profile="clearcote-profiles/samples/vinyzu-04201.json")
page = browser.new_page()
page.goto("https://example.com")
browser.close()
```

The SDK auto-downloads + SHA-256-verifies the pinned binary **for your OS** (Windows x64, Linux x64 or Apple Silicon macOS; archive and inner-binary hashes, `sdk/node/src/release.ts:37-85`) on first use, then caches it; without a licence key it fetches the open build (Chromium 151 on Windows and Linux, 150 on macOS). The proxy-region lookup runs by default; `geoip=True` makes a failed lookup abort the launch and `geoip=False` turns it off. Add `humanize=True` for trusted mouse movement; `widevine=True` on a persistent context enables DRM (on by default for licensed launches since 0.48.0). On an Intel Mac, `launch()` runs the Docker image (`docker=False` turns that off).

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

**Run in Docker (Linux):** `docker/Dockerfile` (browser runtime libs + a base font set so canvas/text hashes stay coherent + Xvfb + the SDK) is published as `teamflatearth/clearcote` and serves CDP on :9222; `docker/serve.py` runs the browser headful on Xvfb by default and pure-headless with `CC_HEADLESS=1`, taking the persona from `CC_*` environment variables; with `CC_SCREEN` unset (the default since SDK 0.60) the virtual display takes the seed's own screen size (`docker/README.md:60`). On Linux the persona defaults to a coherent **native Linux** identity (Linux-shaped GPU/voices/audio devices); `CC_PLATFORM=windows` / `platform: "windows"` spoofs Windows-on-Linux. The image runs as the non-root user `cc`; running as root no longer needs `--cap-add=SYS_NICE` from the open 151 build on (`docker/README.md:355-359`). The image runs Chrome **with** its sandbox when started with the seccomp profile shipped in the image (`--security-opt seccomp=...`; `docker/README.md:215-235`, `docker/sandbox_check.py`, `docker/serve.py:705-718`); without it, it falls back to `--no-sandbox` and logs why. The SDKs pass that profile only to an x86_64 Docker daemon (`sdk/node/src/docker.ts:36-44,757-767`). With a licence key and `CC_WEBRTC_IP` unset, the container looks up its WebRTC address at start (the proxy's exit, or its own public address) through the SDK's IP-echo services; the open engine is not filled, and `CC_WEBRTC_IP=off` skips the lookup (`docker/webrtc_ip.py:1-17`, `docker/README.md:72,154-200`). The README asks for a named cache volume on every run because each container without it downloads the licensed engine (about 164 MB) again, counted against the key's download limit (**Tier B**). The image is also published to `ghcr.io/clearcotelabs/clearcote`.

---

## When to Use

### Recommended For

- Chromium-required targets where you want **native (non-JS) fingerprint control**
- Cases where **auditability matters** — you need to read/rebuild/verify the browser, not trust a binary
- Presenting a **specific real machine's** identity (or a library of them), not just random synthetic ones
- Needing **hardware-coherent canvas/WebGL readbacks** (via the real-GPU canvas bridge)
- Privacy-first browsing/automation on **Windows or Linux** (incl. headless in containers), or on Apple Silicon macOS with the open 150 build
- Playwright users (Node, Python, .NET) wanting a drop-in with a coherent identity + `geoip`; Puppeteer and other CDP clients through the `serve()` endpoint
- Driving a page with a natural-language **in-browser AI agent** on a coherent identity

### Not Recommended For

- Intel macOS (Docker route only), or macOS work that needs the current open Chromium major or a signed, notarized app
- Production work needing a proven track record against **enterprise anti-bot services** (it's pre-release and unbenchmarked there)
- Built-in **CAPTCHA solving** or a proxy pool in the SDK (the vendor offers hosted browsers separately)
- Firefox impersonation (use [Camoufox](./camoufox.md))

---

## Key Files

| File | Purpose |
|------|---------|
| `patches/` | 62 human-readable engine patches (`series` lists the order) — fingerprint switches, per-eTLD+1 farble core, persona + profile import, UA/webdriver, fonts, canvas + canvas-bridge, WebGL/WebGPU, audio/screen/media/touch, WebRTC leak, Runtime.enable/headless tells, humanized input + in-browser agent, TLS network persona, timezone/locale/geolocation, farble escape switch, Windows build fixes, SOCKS5 authentication and UDP relay, HTTP proxy authentication, portable profile key, persona validator and schema 2; `patches/macos-150/` holds three font patches for the open macOS 150 build only |
| `components/ungoogled/persona_profile.*`, `farble_seed.*` | `DerivePersona(seed)`, the per-eTLD+1 seed engine, and the `--fingerprint-profile` override loader |
| `tools/fingerprint-collect/` | profile collector (`collect.html`/`collect.js`), dataset converter (`convert_dataset.py`), and `verify_profile.py` |
| `tools/canvas-bridge-server/` | reference real-GPU canvas-bridge render host (`server.py`) |
| `sdk/node`, `sdk/python`, `sdk/dotnet` | Playwright drop-in SDKs (npm, PyPI, NuGet), each with a test suite; `clearcote` and `clearcote-agent` CLIs |
| `mcp/`, `docker/` | `clearcote-mcp` server (`mcp/clearcote_mcp/server.py`, 20 tools; `mcp/mcpb/` bundle); Docker image sources (`docker/Dockerfile`, `docker/serve.py`, `docker/webrtc_ip.py`) |
| `config/args.gn`, `config/args.linux.gn` | published GN build arguments for Windows and Linux (`is_official_build = true` and PGO since 151); none for macOS |
| `scripts/creepjs_audit.py`, `scripts/stealth_coherence.py` | per-build fingerprint audit + the stealth-coherence regression gate |
| `scripts/verify_patches.py`, `scripts/patch_markers.json`, `.github/workflows/` | the patch-integrity gate and its per-patch manifest (62 entries); ten workflows (SDK publishing, CI, MCP publishing, `stealth-coherence.yml`, `patch-integrity.yml`) |
| `docs/VERIFY.md`, `docs/BUILDING.md`, `docs/CANVAS-BRIDGE.md`, `docs/STEALTH-COHERENCE.md`, `docs/PATCH-INTEGRITY.md`, `docs/MACOS-FONTS.md`, `patches/README.md` | verify a release (incl. the macOS quarantine step) / build from source / run the bridge / the coherence gate / the patch gate / macOS persona fonts / per-patch notes |

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
| Platforms | Win + Linux + macOS arm64 (Intel macOS via Docker) | Linux/mac/Win | Win/others | cross |

---

## Conclusion

Clearcote's stated position is not service-specific coverage but **"read the source, rebuild it, and verify it"** (`README.md`, `docs/VERIFY.md`). Of the Chromium-engine forks in this report, only its open build publishes both the patch series and the build recipe (CloakBrowser ships a closed binary); it also has real-machine fingerprint import with a bundled verifier and an opt-in, experimental real-GPU canvas bridge, on a Chrome-compatible Chromium base. Between `fb3e7bb` and `389653c` (2026-11-20 refresh, compared tree to tree because `main` was rewritten) the open Windows and Linux build moved to Chromium 151 (`v0.1.0-pre.25`) as an official ThinLTO + PGO build with DCHECKs compiled out, the series grew from 37 to 62 patches (SOCKS5 authentication and UDP relay, engine-side HTTP proxy authentication, a portable cookie key, a persona self-check, persona schema 2, and WebGL/WebGPU/DPR/window coherence for cross-OS personas), and an open macOS arm64 build on Chromium 150 (`v0.1.0-pre.24`, unsigned) appeared; the SDKs went from 0.49.0 to 0.70.1 and now run the `geoip` lookup by default, run the macOS build natively on Apple Silicon, give humanized input per-identity pacing and a default reading pause, and, on licensed r51+ engines, fetch every persona from a vendor service. At the 2026-09-30 refresh, relative to the verification before it (`dea4387`, `v0.1.0-pre.22`, Chromium 149) the open build moved to Chromium 150 (`v0.1.0-pre.23`) with five new patches (`071`, `142`, `220`, `951`, `955`); the SDKs went from 0.26.1 to 0.33.0 and gained the multi-identity CDP endpoint (`serveMultiplex`), a `clearcote` CLI, proxy-credential switches whose engine side is not in the public tree, and isolated-world DOM reads for `humanize`; and the README gained a "Free with GitHub" tier, a 250-browser Pro cap and a hosted-browsers section (Pro, with private patches, was already described at `dea4387` but was not covered on this page). Between `1596f29` and `fb3e7bb` (2026-10-13 refresh) the engine was unchanged (no new browser tag, no change under `patches/` or `config/`); the SDKs went from 0.33.0 to 0.49.0 with hosted-browser launch (`cloud=True`), macOS via the Docker image, humanized form filling and paced, persona-shaped motion, Widevine on by default for licensed launches, third-party cookies allowed by default on engines that support it, the ip-api.com GeoIP fallback turned off by default, and options gated to licensed engines (`stockRuntime`, `personaSchema` 3 and 4); the Docker image gained a sandboxed mode with a shipped seccomp profile. Earlier additions remain: a native Linux x64 build alongside Windows, a multi-OS SDK, WebGPU/locale/speech coherence, opt-in Widevine/EME DRM, a humanized cursor, an in-browser AI agent and the stealth-coherence gate — with the project's own caveat that builds are not yet bit-for-bit reproducible.

**Applicability:** Chromium-based automation on Windows x64 or Linux x64 (Apple Silicon macOS on the older open 150 build) where the engine source must be readable and rebuildable. Distinguishing verified capabilities of the open build: 62 published patches, GPG-signed and SHA-256-checksummed builds, real-machine fingerprint import with a bundled verifier, and a `110-runtime-enable` patch.

**Constraints:** the macOS build is one major behind, unsigned and arm64 only (Intel Macs use Docker); open browser build is `v0.1.0-pre.25`; the SDK's `geoip` lookup now contacts IP-echo services by default unless turned off; newer Chromium majors, recorded mouse motion and private patches are in licensed builds that are not in the tree; 1 contributor; no published commercial-WAF results (evidence Tier D for service coverage); builds are not yet bit-for-bit reproducible per the project's own `docs/VERIFY.md`.

**Limitation:** still an early pre-release with **no published benchmarks against commercial anti-bot services** — its demonstrated results are against open-source fingerprint auditors (CreepJS, and the self-referential coherence gate).

---

*Analysis conducted for educational purposes. Use responsibly.*
