# Stealthfox - Technical Analysis

> **Repository:** [P0st3rw-max/stealthfox](https://github.com/P0st3rw-max/stealthfox)
> **Category:** Custom Firefox build (anti-detect browser)
> **Language:** Python wrapper, C++ Firefox patches (binary-only, not in this repo)
> **Approach:** Patched Firefox 150.0.1 + Bayesian fingerprint sampler + Playwright launcher
> **Maturity:** Brand new — single commit "initial public release" on 2026-05-08, version 0.1.0, 3 stars at audit time
> **Audited commit:** `b796002`

---

## Overview

Stealthfox is a custom Firefox 150 build distributed as a prebuilt binary plus a Playwright-compatible Python wrapper. It positions itself as a Camoufox-style anti-detect browser: C++-level fingerprint patches consumed via a `zoom.stealth.*` pref namespace, a Bayesian sampler that generates coherent per-session fingerprints, SOCKS5 proxy auth, WebRTC leak prevention, and Bezier-curve mouse motion. The Python wrapper is open-source (MIT) and well-engineered; the Firefox patches that actually do the stealth are **not** in any public repo at audit time — the README points to `github.com/P0st3rw-max/firefox-stealth`, which currently returns 404.

---

## Verdict

| Aspect | Rating | Notes |
|--------|--------|-------|
| **Overall Quality** | ⭐⭐⭐⭐ | Wrapper is genuinely well-engineered; Bayesian sampler is sophisticated |
| **Anti-Detection (claimed)** | ⭐⭐⭐⭐⭐ | Strong claims: 0.9 reCAPTCHA v3, 0 CreepJS lies, FP Pro all-clear |
| **Anti-Detection (verifiable)** | ⭐⭐ | Most stealth lives in a separate `firefox-stealth` patches repo that **returns 404** — the C++ side is not auditable from public sources |
| **Ease of Use** | ⭐⭐⭐⭐⭐ | Two-line drop-in for Playwright; `pip install stealthfox && python -m stealthfox fetch` |
| **Maintenance Risk** | ⭐ | One commit, one author, no release history, no CI visible — the highest project-risk tool in this comparison |
| **Documentation** | ⭐⭐⭐⭐ | Well-written README + 143-line `docs/pinning.md`; in-source comments are unusually careful (A/B test notes, dated experiments, FF150 sandbox workarounds) |

**Bottom line:** Stealthfox is the most ambitious-on-paper Camoufox competitor in this list — same approach (custom Firefox + C++ fingerprint patches + Bayesian sampler), arguably a better-designed sampler, and a Playwright wrapper that quietly handles a long tail of FF150-specific gotchas (Fission BC swap races, GPU sandbox on virtual desktops, ICU TZ quirks on Windows). But the actual stealth — the C++ patches that turn `zoom.stealth.*` prefs into modified WebGL/canvas/audio output — is not in any public repo, the patches link 404s, and the project is one commit old. **Treat the published benchmark numbers as unverified marketing until the patch source is published.**

---

## What You Actually Get

The cloned repo is **only the Python wrapper plus a Bayesian profile sampler** — no Firefox source, no patch files, no build system. At runtime:

1. `python -m stealthfox fetch` downloads a **prebuilt Firefox 150.0.1 binary** from `github.com/P0st3rw-max/stealthfox/releases` (~100 MB), SHA256-verified against `checksums.txt` ([download.py:115-151](../../../_scratch/stealthfox/src/stealthfox/download.py)).
2. `Stealthfox()` launches that binary via `playwright.firefox.launch(executable_path=...)`.
3. A coherent fingerprint is sampled from a seed and pushed in via `firefox_user_prefs={...}` ([launcher.py:163-186](../../../_scratch/stealthfox/src/stealthfox/launcher.py)).
4. The patched Firefox reads the `zoom.stealth.*` namespace from C++ and emits the spoofed values through normal Gecko paths.

So the project has **two halves**:
- **Wrapper + sampler (public, audited here):** `~1.6k LOC` in `src/stealthfox/`. Solid.
- **Firefox patches (closed):** README points to `github.com/P0st3rw-max/firefox-stealth` for the patch source. **That URL 404s at audit time.** Whether the patches ever become public is unknown.

---

## How It Works - Technical Deep Dive

### Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                       STEALTHFOX                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────────┐    ┌──────────────────────────────────┐    │
│  │  Stealthfox()   │───▶│  fpforge — Bayesian sampler      │    │
│  │  (sync/async)   │    │  ┌────────────────────────────┐  │    │
│  └────────┬────────┘    │  │ gpu (444-entry pool)       │  │    │
│           │             │  │   └─ gpu_class (6 buckets) │  │    │
│           │             │  │       └─ intra_tier (hidden│  │    │
│           │             │  │           coherence var)   │  │    │
│           │             │  │           ├─ hw_concurrency│  │    │
│           │             │  │           ├─ screen w/h/dpr│  │    │
│           │             │  │           ├─ storage_quota │  │    │
│           │             │  │           ├─ msaa_samples  │  │    │
│           │             │  │           ├─ codec bundle  │  │    │
│           │             │  │           ├─ audio bundle  │  │    │
│           │             │  │           └─ font whitelist│  │    │
│           │             │  └────────────────────────────┘  │    │
│           │             └──────────────┬───────────────────┘    │
│           │                            │                         │
│           ▼                            ▼                         │
│  ┌──────────────────────────────────────────────────┐           │
│  │  prefs.translate_profile_to_prefs                │           │
│  │  • _BASELINE  (~120 prefs: WebRTC, telemetry,    │           │
│  │     Fission off, HTTP/3 off, push/geo killed)    │           │
│  │  • _NAVIGATOR_OVERRIDES  (UA/platform locked     │           │
│  │     to Win10 Firefox 150)                        │           │
│  │  • _WIN_LIGHT_COLORS  (32 ui.* color prefs)      │           │
│  │  • zoom.stealth.*  (consumed by C++ patches)     │           │
│  │  • Linux Xvfb / Windows virtual-desktop fixups   │           │
│  └─────────────────────┬────────────────────────────┘           │
│                        │                                         │
│                        ▼                                         │
│  ┌──────────────────────────────────────────────────┐           │
│  │   playwright.firefox.launch(                     │           │
│  │     executable_path=ensure_binary(),             │           │
│  │     firefox_user_prefs=prefs,                    │           │
│  │     proxy=playwright_proxy)                      │           │
│  └─────────────────────┬────────────────────────────┘           │
│                        │                                         │
│                        ▼                                         │
│  ┌──────────────────────────────────────────────────┐           │
│  │   Patched Firefox 150 binary  [SOURCE NOT PUBLIC] │           │
│  │   • C++ fingerprint hooks read zoom.stealth.*    │           │
│  │   • nsProtocolProxyService SOCKS5 auth patch     │           │
│  │   • Juggler "humanize" Bezier mouse patch        │           │
│  │   • nr_stealth_bridge WebRTC srflx injection     │           │
│  └──────────────────────────────────────────────────┘           │
└─────────────────────────────────────────────────────────────────┘
```

---

### 1. Bayesian Fingerprint Sampler (`src/stealthfox/_fpforge/`)

This is the most impressive piece of public code in the repo and worth dwelling on, because it's qualitatively different from the per-field random sampling most "stealth" tools do.

**Network shape** ([_fpforge/_sampler.py:192-223](../../../_scratch/stealthfox/src/stealthfox/_fpforge/_sampler.py)):

```python
_NETWORK = Network([
    Node("gpu", parents=[], cpt=_gpu_marginal()),                    # 444 real Win ANGLE entries
    Node("gpu_class", parents=["gpu"], classifier=classify_gpu),     # 6 buckets
    Node("intra_tier", parents=["gpu_class"], cpt=_CPT_INTRA_TIER),  # hidden coherence var
    Node("hw_concurrency",   parents=["gpu_class","intra_tier"], cpt=_CPT_HWC),
    Node("screen",           parents=["gpu_class","intra_tier"], cpt=_CPT_SCREEN),
    Node("screen_tier",      parents=["screen"], classifier=_screen_tier),
    Node("msaa_samples",     parents=["gpu_class","screen_tier"],   cpt=_CPT_MSAA),
    Node("codec",            parents=["gpu_class"],                  cpt=_CPT_CODEC),
    Node("storage_quota_mb", parents=["gpu_class","intra_tier"],     cpt=_CPT_STORAGE),
    Node("audio",            parents=["gpu_class"],                  cpt=_CPT_AUDIO),
    Node("dark_theme",       parents=[],                              cpt=_INDEP["dark_theme"]),
])
```

The **hidden `intra_tier` variable** is the key idea: within a GPU class, a "premium" mid-range user systematically has more cores, larger SSD, and a higher-res screen than a "budget" mid-range user. Sampling `hw_concurrency`, `screen`, and `storage_quota_mb` independently from `gpu_class` alone produces noisy combinations (16-core CPU + 1366×768 screen). Conditioning all three on `(gpu_class, intra_tier)` keeps them coherent without enumerating every permutation. This is the kind of detail that matters because **CreepJS-style "lies detectors" specifically look for inter-field implausibility**.

**GPU classifier** ([_fpforge/_sampler.py:98-155](../../../_scratch/stealthfox/src/stealthfox/_fpforge/_sampler.py)) is also notably careful: it explicitly buckets all NVIDIA GeForce cards as `low_end` because Firefox's `SanitizeRenderer.cpp` collapses every NVIDIA GeForce into one of three vintage strings (8800 GTX / GTX 480 / GTX 980), and pairing the vintage renderer string with modern cores would surface as an FP Pro `tampering_ml` flag. This kind of "the renderer string we report is constrained by what Firefox will actually emit" reasoning is the right level of paranoia for this domain.

**CPT data** ships as 11 JSON tables in `_fpforge/data/` — these are the actual conditional probability tables. The README claims they're sampled from "real-world Firefox telemetry." Whether the tables are genuinely from telemetry or hand-tuned is unverifiable from the repo, but the structure is at least correct.

**Coherence rule of thumb** (documented honestly in `docs/pinning.md`): pinning a single field breaks the conditional chain — pin `gpu.renderer = "RTX 4090"` while leaving `screen` unpinned and you may get an RTX 4090 + 1366×768 pairing. The docs say so plainly.

### 2. Pref Translation (`src/stealthfox/prefs.py`)

568 lines, almost entirely a giant dictionary of Firefox prefs. Three layers:

- **`_BASELINE`** (~120 prefs): kills the things that would otherwise leak the bot — `privacy.fingerprintingProtection=False` (so spoofed values match a vanilla user, not a hardened one), WebRTC ICE configured to not leak host, Safebrowsing/telemetry/captive-portal/push/geo all disabled, HTTP/3 + Alt-Svc + speculative parallel disabled (SOCKS5 doesn't speak UDP), Fission disabled, AboutNewTab autoload disabled (otherwise it races `page.goto()` on FF150 and surfaces as `NS_BINDING_ABORTED`). The comments next to each toggle name the specific failure mode they prevent — that's a more empirical pref list than most.

- **`_NAVIGATOR_OVERRIDES`**: UA/platform/oscpu locked to Win10 Firefox 150 regardless of host OS. Notably, `general.buildID.override` was **removed on 2026-04-28** with a comment explaining the previous static buildID was 7.5 years stale relative to the binary's true buildID — flagged as a reCAPTCHA internal-consistency risk and confirmed via "A/B knockout (n=30): F2 delete +0.083 RC vs BASE." This is the kind of in-source A/B note you'd expect from an active research project, not a hobby fork. (It's also one of the only published pieces of evidence that the published benchmark numbers come from real testing rather than a single cherry-picked screenshot.)

- **`zoom.stealth.*`**: ~30 keys consumed by the C++ patches. Examples:
  - `zoom.stealth.canvas.noise_skip_mask` — bitmask controlling per-pixel noise injection rate (1/16 for Intel GPUs, 1/8 for NVIDIA/AMD, with the comment that Intel has lower natural rendering variance so over-noising raises `tampering_ml`).
  - `zoom.stealth.webgl.msaa` / `webgl.msaa-samples` — pinned to 4 on Windows so `gl.SAMPLES` is constant across sessions (different MSAA = different parameters-hash even with the same renderer).
  - `zoom.stealth.audio.sample_rate` / `output_latency_ms` / `max_channel_count`.
  - `zoom.stealth.font.whitelist` + `zoom.stealth.font.metrics` — paired strings, each font has a per-family width-scale factor at least 4 % off 1.0 so it's detectable by width-diff probes.
  - `zoom.stealth.fpp.hw_seed` — int31-clamped (the C++ side declares it as `int32_t` and bails on `seed <= 0`). This is the seed that drives canvas/DWrite-gamma noise on the C++ side.
  - `zoom.stealth.webrtc.host_ip` — synthetic 192.168.x.x address derived from seed, injected by the C++ WebRTC patch when SOCKS5 strips all host candidates.

Cross-platform handling is also unusually thoughtful — on Linux the `webgl.renderer` string is spoofed (so you can run cross-platform sessions reporting Windows GPU); on Windows, spoofing a different GPU than the real ANGLE hardware would mismatch the 81-value `getParameter()` hash and is **explicitly avoided** ([prefs.py:442-460](../../../_scratch/stealthfox/src/stealthfox/prefs.py)). Same idea with font width-scale factors: applied on Linux, **never** on Windows (where they'd distort real Segoe/Arial widths).

### 3. SOCKS5 With Auth (`src/stealthfox/_proxy.py`)

The SOCKS5 path is genuinely something stock Playwright + Firefox can't do — Playwright's `proxy=` kwarg supports SOCKS5 only without auth, because Firefox's `nsProtocolProxyService` historically didn't read `network.proxy.socks_username` / `socks_password` for SOCKS5. Stealthfox routes auth credentials into those prefs and lets the patched browser handle the negotiation:

```python
# _proxy.py:38-47
prefs["network.proxy.type"]            = 1
prefs["network.proxy.socks"]           = host
prefs["network.proxy.socks_port"]      = int(port_str)
prefs["network.proxy.socks_version"]   = 4 if server.lower().startswith("socks4://") else 5
prefs["network.proxy.socks_username"]  = proxy.get("username") or ""
prefs["network.proxy.socks_password"]  = proxy.get("password") or ""
prefs["network.proxy.socks_remote_dns"] = True
```

For HTTP/HTTPS proxies it falls through to Playwright's own kwarg. **The actual SOCKS5 auth handshake lives in the unpublished C++ patch to `nsProtocolProxyService.cpp`** — the wrapper just provides the credentials.

### 4. Headless Without "Headless Mode" (`src/stealthfox/_headless.py`)

`headless=True` does **not** pass `headless=true` to Playwright. Instead it keeps Firefox in headed mode (real rendering pipeline, real WebGL output, real layout timings) and hides the windows on a fresh Xvfb (Linux) or `CreateDesktop` virtual desktop (Windows). This is the same trick Camoufox uses and the right call for stealth: Playwright's actual `headless=true` flips Firefox onto a divergent code path (no widget tree, software-only rendering) that anti-bot stacks can detect through timing and rendering artifacts.

Windows virtual-desktop mode hits a real Bugzilla regression on FF150 — the GPU process sandbox (level=1, default since FF110) tries to parent its compositor window to the parent process's window, and parent and GPU process don't share the desktop on a `CreateDesktop` alt desktop ([prefs.py:374-387](../../../_scratch/stealthfox/src/stealthfox/prefs.py)). Stealthfox's workaround is to set `security.sandbox.gpu.level=0`. **That's a real security regression for a sandbox bypass** — fine for scraping containers, *not* fine on a developer workstation that also browses other sites with the same binary. The wrapper applies it silently when `headless=True` on Windows.

### 5. Humanize Via Juggler (`launcher.py:260-263`)

```python
prefs["stealthfox.humanize"] = bool(self._humanize)
if self._humanize:
    prefs["stealthfox.humanize.maxTime"] = str(self._humanize_max_seconds())
```

Default-on. The Bezier-curve mouse trajectory is implemented in **the patched Juggler** (Firefox's CDP-equivalent automation protocol), so even `page.click(selector)` from vanilla Playwright code generates a curved trajectory on the C++ side. ~10 ms per waypoint, capped at 1.5 s. Source for that path is, again, in the unpublished patches.

### 6. FF150-Specific Bug Workarounds

This is the part I most appreciated reading. Scattered throughout:

- `_patch_sync_new_page_sleep`: 400 ms sleep after `new_page()` because FF150 with Fission emits an `about:newtab` navigation ~100 ms after a tab is created, racing with `goto()` and producing `Navigation interrupted by about:newtab`.
- `_IANA_TO_POSIX_TZ`: maps common IANA zones to POSIX TZ form because Windows MSVCRT only understands the POSIX form, with a specific note that mapping `America/Phoenix` → `MST7MDT` made libc apply DST and FP Pro deduced `vpn_origin_timezone="America/Denver"` → `timezone_mismatch`.
- Per-realm timezone override via `timezone_id=` (Playwright's `docShell.overrideTimezone` → `JS::SetRealmTimezoneOverride`) instead of the global `juggler.timezone.override` pref, because the global path is broken on Windows ICU for no-DST IANA names.
- `zoom.stealth.fpp.hw_seed` clamped to int31 to avoid the C++ `seed <= 0` bail-out producing bit-identical canvas hashes.

You don't write that volume of post-hoc workaround comments without having actually run the thing against detectors many times.

---

## Verifiable vs. Unverifiable Claims

| README claim | Verifiable here? | Notes |
|---|---|---|
| Bayesian fingerprint generator | ✅ | Source + 11 CPT JSON tables in `_fpforge/data/` |
| ~400 coherent prefs | ✅ | Counted 120 in `_BASELINE`, ~30 `zoom.stealth.*`, plus 32 `ui.*` colors and ~15 navigator overrides — close enough |
| Win-locked navigator identity | ✅ | `_NAVIGATOR_OVERRIDES` |
| SOCKS5 auth | ✅ wrapper side, ❌ C++ side | Wrapper writes the prefs; the actual nsProtocolProxyService patch isn't public |
| Mouse Bezier in Juggler | ❌ | Patch source not in this repo |
| Canvas / WebGL C++ pixel substitution | ❌ | Pref keys exist; consumers don't |
| TLS / TCP fingerprint spoofing (claimed Windows JA3/JA4, MNWNNS SYN, wscale 8, TTL 128) | ❌ | **No evidence whatsoever in this repo.** Firefox uses NSS; rewriting NSS's ClientHello at this fidelity is a major patch. Windows-style TCP SYN options would require either a patched winsock layer or a userspace netstack — neither is hinted at in the wrapper |
| WebRTC mDNS obfuscation off + synthetic srflx | ⚠️ partial | `media.peerconnection.ice.obfuscate_host_addresses=false` is a stock pref; the synthetic srflx comes from `nr_stealth_bridge` in the unpublished patches |
| 0.9 reCAPTCHA v3, 0 CreepJS lies, FP Pro all-clear | ❌ | Single screenshot each in `docs/screenshots/`; no public reproducer or test harness |
| Source link `github.com/P0st3rw-max/firefox-stealth` for patches | ❌ | URL **404s** at audit time |

The repo is honest about what it ships ("the patched Firefox binary is distributed under MPL-2.0") but the *implication* — that you can read the patches and verify the C++ behavior matches the claims — is not currently true.

---

## Services Bypassed

Stealthfox's README publishes results against five detector platforms. None of these are independently verified — each is documented by a single screenshot in `docs/screenshots/` with no reproducer script, no detector version, and no proxy/account methodology.

| Service | Claimed Result | Verified? | Notes |
|---------|----------------|-----------|-------|
| Google reCAPTCHA v3 | 0.90 / 1.0 score ("very likely human") | ❌ | Single screenshot. Most stacks plateau at 0.3–0.7; 0.90 is exceptional and would warrant independent reproduction |
| FingerprintJS Pro | bot/VPN/tampering/devtools all "Not detected", confidence 0.9 | ❌ | Single screenshot. The Smart Signals battery is what most stacks fail |
| CreepJS | 0 lies (internally coherent fingerprint) | ❌ | Single screenshot. The Bayesian sampler design supports the *plausibility* of this claim better than most tools, but it isn't proven |
| BrowserLeaks WebRTC | No public IP leak, host candidates LAN-private | ❌ | Single screenshot. Host-candidate suppression is doable via prefs alone; synthetic srflx requires the unpublished C++ patch |
| bot.sannysoft.com | All checks pass (every row green) | ❌ | Single screenshot. Sannysoft is a comparatively easy target — most tools in this comparison pass it |

| Anti-Bot Service | Stealthfox |
|------------------|:----------:|
| Cloudflare WAF | ⚠️ Claimed, unverified |
| Cloudflare Turnstile | ⚠️ Claimed, unverified |
| DataDome | ⚠️ Claimed, unverified |
| Kasada | ⚠️ |
| PerimeterX | ⚠️ |
| Akamai | ⚠️ |
| Imperva | ⚠️ |

⚠️ across the board reflects "the design is sound enough that these should plausibly work, but there is no public evidence."

---

## Pros and Cons

### Pros

1. **Drop-in Playwright API.** Two-line swap from `sync_playwright()` to `Stealthfox()`. Sync, async, `new_page` / `new_context`, screenshots, downloads — all work because the underlying object is a real `playwright.sync_api.Browser`.
2. **Bayesian sampler with hidden coherence variable.** Genuinely better than independent-per-field random sampling. Same conceptual league as Camoufox's BrowserForge, with a different (and arguably tighter) graph.
3. **Pinning API.** `pin={"gpu.class_tier": "low_end"}` lets you steer the whole graph with one root, or pin specific exact strings (`gpu.renderer`) and let the rest re-sample. Documented honestly including the "pinning breaks coherence" gotcha.
4. **Empirically tuned pref baseline.** The in-source A/B notes, dated experiments, and named failure modes ("NS_BINDING_FAILED on push.services + firefox.settings.services", "FF150 Fission BC swap race") suggest the prefs aren't cargo-culted from another fork — someone ran them.
5. **SOCKS5 with auth.** Real differentiator vs vanilla Playwright + Firefox.
6. **Headed-on-virtual-display headless.** Same approach as Camoufox; right answer for stealth.
7. **Cross-platform asymmetry handled correctly.** Windows doesn't get spoofed renderer/extensions/fonts (they'd diverge from the real ANGLE hardware); Linux does. Most tools treat platforms uniformly and lose on this.

### Cons

1. **C++ patches are not public.** README points to `github.com/P0st3rw-max/firefox-stealth`, which **404s**. Every claim that requires C++ implementation — TLS spoofing, TCP SYN options, canvas pixel substitution, SOCKS5 auth handshake, Juggler humanize — is unverifiable from public source. You're trusting a binary.
2. **Trust footprint is binary-only.** `python -m stealthfox fetch` downloads ~100 MB from `github.com/P0st3rw-max/stealthfox/releases`, SHA256-verified against `checksums.txt` — but the SHA256 is signed by the same author. There's no third-party reproducible build, no detached signature, no upstream attestation. You're running a custom Firefox build with weakened sandbox prefs. Sandbox it.
3. **Project age.** One commit, version 0.1.0, "initial public release" 2026-05-08. No release tags visible from this clone, no CI configs, no test runs in git history. By far the youngest tool in this comparison.
4. **TLS / TCP claims are extraordinary.** Spoofing JA3/JA4 to a Windows Firefox profile from a Linux binary requires patching NSS; spoofing TCP SYN options requires patching the OS networking stack or running a userspace netstack. Camoufox doesn't claim either. Either stealthfox has done something Camoufox hasn't, or the claim is overstated. Without the patch source, you can't tell which.
5. **GPU sandbox lowered to 0 silently** when `headless=True` on Windows. Scraping-only environments fine; not appropriate for a desktop machine.
6. **Single platform pair.** Windows x86_64 and Linux x86_64 only ([constants.py:25-36](../../../_scratch/stealthfox/src/stealthfox/constants.py)). No macOS, no ARM.
7. **Single author.** Email `posteririgho@users.noreply.github.com` is the only contributor in `pyproject.toml`. No bus factor.
8. **Benchmarks are screenshots, not reproducers.** The README's reCAPTCHA-0.90 / FP-Pro-clean / CreepJS-0-lies claims have one screenshot each. No script you can run to reproduce, no detector-version pinning, no proxy/account isolation methodology.

---

## Comparison with Camoufox

These two are the closest siblings in this repo — both are custom Firefox builds, both spoof at the C++ level, both ship a Python wrapper, both use a Bayesian / statistical fingerprint generator.

| | Stealthfox | Camoufox |
|---|---|---|
| Firefox base | 150.0.1 | Active port stack (FF146+ at audit time) |
| Patch source public | ❌ (404) | ✅ ([daijro/camoufox](https://github.com/daijro/camoufox)) |
| Build reproducible by user | ❌ (binary only) | ✅ (source + build scripts in repo) |
| Fingerprint generator | Custom Bayesian network with hidden `intra_tier` variable, 444-entry GPU pool, 11 CPT tables | BrowserForge (statistical sampler over public fingerprint dataset) |
| Pinning | Dotted-path `pin={"gpu.class_tier": ...}`, validated keys | BrowserForge constraints |
| Mouse humanize | Juggler-level Bezier (default on) | Juggler-level Bezier (opt-in) |
| SOCKS5 auth | ✅ via patched `nsProtocolProxyService` | ✅ (similar mechanism) |
| Cross-platform spoofing | Windows-as-source-of-truth; Linux spoofs to Windows; macOS unsupported | Multi-platform with platform-aware profiles |
| Project age | Days | Years |
| Star count at audit | 3 | 4-figure |
| Bus factor | 1 | Small but >1 |

**If you can use Camoufox, use Camoufox** — same approach, mature project, auditable patches. Stealthfox is interesting and may be technically equivalent or better in places (the Bayesian graph is genuinely thoughtful), but you cannot currently verify it.

---

## Installation & Usage

```bash
pip install stealthfox
python -m stealthfox fetch    # ~100 MB, SHA256-verified
```

Random seed per session:

```python
from stealthfox import Stealthfox

with Stealthfox() as browser:
    page = browser.new_page()
    page.goto("https://creepjs-api.web.app")
```

Reproducible fingerprint:

```python
with Stealthfox(seed=42) as browser:
    ...   # same GPU, screen, audio, fonts every run
```

With SOCKS5 auth and pinned GPU:

```python
with Stealthfox(
    seed=42,
    proxy={"server": "socks5://gate.example.com:1080", "username": "u", "password": "p"},
    pin={"gpu.class_tier": "high_end", "screen.width": 2560, "screen.height": 1440},
    timezone="America/New_York",
) as browser:
    page = browser.new_page()
    page.goto("https://example.com")
```

Async surface is identical (`from stealthfox.async_api import Stealthfox`).

CLI:

```bash
stealthfox fetch          # download binary
stealthfox path           # print cached path
stealthfox version        # wrapper + binary version
stealthfox clear-cache    # remove all cached binaries
```

---

## When to Use Stealthfox

- You need a **Camoufox-style Firefox stack** but want to evaluate alternatives, and you're willing to trust a young binary-only project.
- You need **SOCKS5 with auth + a custom Firefox** in one package.
- You need **per-session Bayesian fingerprints** with a clean pinning API for A/B testing.
- You want to play with the public fingerprint sampler — `_fpforge` is genuinely good code regardless of the rest of the project.

## When Not To Use

- You need an **auditable** anti-detect stack (compliance, security review, anything that asks "what's in the binary"). Use [Camoufox](./camoufox.md).
- You need **macOS or ARM** support.
- You need **production stability** today. One commit, version 0.1.0, no release history.
- You depend on the **TLS / TCP fingerprint spoofing claims** — they are not currently verifiable.
- You're running this **on the same machine you do other work on** in `headless=True` mode on Windows. The silent `security.sandbox.gpu.level=0` is not appropriate for that environment.

---

## Bottom Line

Stealthfox is more interesting than its 3 stars suggest. The Python side is a careful, empirically-driven piece of work — the Bayesian sampler with `intra_tier`, the dated A/B notes in `prefs.py`, the FF150-specific race-condition workarounds, the platform-asymmetric spoofing logic. Whoever wrote this has shipped a non-trivial amount of detector-vs-stealth iteration.

But the **half of the project that actually does the stealth — the C++ patches that turn the `zoom.stealth.*` prefs into modified canvas/WebGL/audio/WebRTC output — is closed**, and the README's claim that "the patches themselves are maintained in the firefox-stealth source repo" is currently false: that URL 404s. Every benchmark in the README is a single screenshot. Until the patch source is published and a third party reproduces a benchmark, **the right framing is "promising experimental project," not "Camoufox alternative."** If you trust the author and you're in a contained scraping environment, it's worth a look. If you need a tool with audit-grade provenance, use Camoufox.

---

## Resources

- **Repository:** [github.com/P0st3rw-max/stealthfox](https://github.com/P0st3rw-max/stealthfox)
- **PyPI:** `pip install stealthfox`
- **Patch source repo (referenced in README):** [github.com/P0st3rw-max/firefox-stealth](https://github.com/P0st3rw-max/firefox-stealth) — ⚠️ returns 404 at audit time
- **Pinning docs:** [docs/pinning.md](https://github.com/P0st3rw-max/stealthfox/blob/master/docs/pinning.md)
- **Closest alternative:** [Camoufox](./camoufox.md) — same approach, public patches, mature project
- **License:** MIT (wrapper) / MPL-2.0 (Firefox binary)
