# invisible_playwright - Technical Analysis

> **Tool Type:** Custom Firefox Build (Anti-Detect Browser) driven by stock Playwright
> **Repository:** [github.com/feder-cr/invisible_playwright](https://github.com/feder-cr/invisible_playwright) (wrapper) · [feder-cr/invisible_core](https://github.com/feder-cr/invisible_core) (config/download) · [feder-cr/firefox_antidetect_patch](https://github.com/feder-cr/firefox_antidetect_patch) (the engine)
> **Approach:** Firefox patched in C++ source and rebuilt; fingerprint produced by the engine rather than injected into the page. The Playwright client is unmodified.
> **Verified in source (Tier A):** the engine is a genuine GitHub fork of `mozilla-firefox/firefox`. The stealth work is on branches `stealth/150` and `stealth/151`, **not** on `main`. A diffable tag pair `stealth-base/v150.0.1` → `stealth-head/v150.0.1` resolves to **20 commits / 104 files changed**.
> **Anti-bot service claims:** none. The project publishes detector-suite results (CreepJS, BotD, FingerprintJS, fpscanner, Sannysoft, BrowserLeaks, reCAPTCHA scoring) rather than WAF pass rates — **Tier B** for the results, **Tier D** for commercial-service coverage.
> **Maintenance:** wrapper `0.7.0` (2026-08-11); engine release `firefox-19` (2026-08-11, Firefox 151). 1.9k stars, 215 forks, 2 contributors. Wrapper MIT; engine fork inherits MPL-2.0 from mozilla-central (GitHub reports `NOASSERTION`).
> **Verified:** 2026-08-14 against `invisible_playwright` @ `f777798`, `invisible_core` 19.14.0, `firefox_antidetect_patch` @ `d5457fa7` (`stealth/151`).

> [!IMPORTANT]
> **The shipped browser contacts GitHub once on every launch.** It is disclosed and
> disableable, but the disclosure is not in the package most people install. Details in
> [Launch telemetry](#launch-telemetry) — read that section before deploying this.

---

## Table of Contents

- [Are the patches public?](#are-the-patches-public)
- [Launch telemetry](#launch-telemetry)
- [What the patches actually change](#what-the-patches-actually-change)
- [Supply chain](#supply-chain)
- [Other network activity](#other-network-activity)
- [Code quality](#code-quality)
- [Claims versus source](#claims-versus-source)
- [Comparison](#comparison)
- [Applicability](#applicability)

---

## Are the patches public?

**Yes — verifiably, and the fork relationship is machine-checkable.** This was the first
thing checked, because a C++-patched browser distributed as a binary is only as
trustworthy as the source behind it.

| Check | Result |
|---|---|
| `firefox_antidetect_patch` is a real fork of `mozilla-firefox/firefox` | **Yes** — GitHub API reports `fork: true`, parent `mozilla-firefox/firefox` |
| Repository public | Yes, ~4,960 MB |
| Stealth work present | Yes, on `stealth/150` and `stealth/151` |
| Diffable base provided | Yes — tags `stealth-base/v150.0.1` and `stealth-head/v150.0.1` |
| That comparison resolves to | **20 commits, 104 files changed** |
| Built binaries published | Yes — release tags `firefox-14` … `firefox-19`, per-platform tarballs + `checksums.txt` |

### Three caveats that matter more than the headline

**1. The default branch shows none of it.** `main` is 5 commits ahead of upstream and
changes **2 files** — README and CI only. A reviewer who checks the repository's default
branch for patches concludes there are none. The wrapper repositories reinforce this:
`invisible_playwright` contains **zero** `.cc`/`.cpp`/`.h` files, **zero** `.patch`
files, and no `patches/` directory. Nothing in the packages a user installs points at
the branch where the engine work lives.

**2. GitHub cannot render the current diff.** Comparing `last-mozilla-central...stealth/151`
returns HTTP 422, *"Sorry, this diff is taking too long to generate."* The 150-line pair
works because it is smaller. Auditing the shipping line requires a local clone of a
multi-gigabyte tree.

**3. The patch series exists but is not public.** The branch carries a
`STEALTH_BRANCH_README.md` documenting the workflow, and it is explicit that a numbered
series (`0001-build-infra.patch` … `0015-storage-quota.patch`) was maintained in a
separate repository, regenerated with:

```bash
git format-patch stealth-base/v150.0.1..stealth/150 -o ../firefox-stealth/
```

That repository — `feder-cr/firefox-stealth` — **returns HTTP 404**. So the readable,
titled series referenced by the project's own documentation is not publicly available;
only the forked tree and the base/head tag pair are. You can regenerate an equivalent
series yourself with the command above once you have cloned the fork, which is more than
[CloakBrowser](./cloakbrowser.md) offers, but less than [Camoufox](./camoufox.md)
(34 `.patch` files) or [Clearcote](./clearcote.md) (32 in `patches/series`), where the
diffs can be read in an afternoon without cloning anything.

**Net:** *auditable in principle, considerably harder in practice.* That is a real
distinction from [CloakBrowser](./cloakbrowser.md), whose engine source is not published
at all — but it is not equivalent to a readable patch series.

---

## Launch telemetry

**The patched browser issues one HTTPS GET to GitHub every time the process starts.**
Verified in source, not inferred:

```javascript
// browser/components/BrowserGlue.sys.mjs:392-408  (branch stealth/151)
// Gate via pref `invisible_firefox.usage_ping.enabled` (default true).
// To permanently disable, remove this block and rebuild from source.
// Full disclosure: "Anonymous launch counter" in this repo's README.
try {
  if (Services.prefs.getBoolPref("invisible_firefox.usage_ping.enabled", true)) {
    fetch("https://github.com/feder-cr/invisible_firefox/releases/download/usage-counter/launch.txt",
          { method: "GET", credentials: "omit", cache: "no-store" })
      .catch(() => {});
  }
} catch (e) {}
```

```javascript
// browser/app/profile/firefox.js:3618
pref("invisible_firefox.usage_ping.enabled", true);
```

The asset's GitHub `download_count` is used as a global launch counter for a badge.

### Assessment

| Property | Finding |
|---|---|
| **Enabled by default** | Yes — `pref(..., true)` |
| **What is transmitted** | An HTTP GET with a standard Firefox User-Agent. `credentials: "omit"` (no cookies), `cache: "no-store"`, no payload, no identifier, no query string |
| **When** | At `final-ui-startup`, before any tab exists |
| **Failure behaviour** | Fire-and-forget; `.catch(() => {})`, wrapped in `try/catch`. The browser never blocks on it |
| **Does it respect the proxy?** | **Yes.** It is a privileged `fetch()` through Firefox's own network stack, so it follows the `network.proxy.*` prefs `invisible_core` sets. `prefs.py` also sets `network.proxy.failover_direct = False` and `socks_remote_dns = True`, so there is no direct-connection fallback and no DNS leak if the proxy is down |
| **Opt-out** | `invisible_firefox.usage_ping.enabled = false` via `about:config` or `extra_prefs={...}` at launch; permanently by removing the block and rebuilding |
| **Disclosed** | Yes — a dedicated "Anonymous launch counter" section in the engine repo's README, plus comments at both source sites |

> [!WARNING]
> **The disclosure is absent from the package most users install.** Searching the entire
> `invisible_playwright` repository — README, docs, source, tests — for `usage_ping`,
> `launch counter`, `launch.txt`, or `usage-counter` returns **0 matches**. A developer
> who runs `pip install invisible-playwright` and reads its documentation will not learn
> that their browser contacts GitHub on every launch. The disclosure lives in a
> different repository that most users have no reason to open.

**Is this "bad stuff"?** No. It is a counter, not surveillance: no identifier, no
payload, no cookies, disclosed in plain language at the engine repo, gated behind a
documented pref, and routed through the same proxy as everything else. The honest
criticism is placement, not intent — the disclosure belongs in the README of the package
being installed, and the ping arguably should be opt-in for a tool whose entire purpose
is not being seen. Anyone running this against a target that also observes GitHub
traffic should turn it off.

---

## What the patches actually change

Areas touched by the 104-file `stealth-base → stealth-head` diff, grouped by tree
location. This maps cleanly onto the [detection-layer taxonomy](README.md#detection-layers-and-which-tools-address-them):

| Area | Files | Layer |
|------|------:|-------|
| `juggler/**` (screencast, content, protocol, pipe, components) | 41 | automation protocol — Playwright's Firefox transport |
| `netwerk/**` (socket, http, base) | 9 | 4 — network |
| `gfx/thebes` | 6 | 2 — fonts, graphics |
| `dom/media/webrtc/transport` + `nICEr/src/ice` | 6 | 4 — WebRTC IP |
| `dom/base` | 5 | 2 — navigator surfaces |
| `dom/media/webaudio` | 4 | 2 — audio fingerprint |
| `js/src/vm`, `js/src/debugger` | 4 | 1 — JS engine / debugger tells |
| `dom/media/webspeech/synth` | 2 | 2 — speech voices |
| `modules/libpref/init` | 2 | defaults (includes the usage-ping pref) |

> [!NOTE]
> **The Juggler files do not contradict "stock Playwright".** Playwright drives Firefox
> over Juggler, which is not part of upstream Firefox — any Firefox intended to be driven
> by Playwright must carry it. What is unmodified here is the **Playwright client**
> (`pip install playwright`), not Juggler. [Camoufox](./camoufox.md) makes the same
> trade differently: it patches Juggler *and* ships its own launcher.

This is a coherent anti-detect patch set with no components that look out of place for
the stated purpose.

### Is it substantive, or superficial pref-flipping?

**Substantive.** The diff is **+14,279 / −59 lines**. Read at the code level, three
things establish that this is real engine work rather than configuration:

**1. A C++ fingerprint surface driven by static prefs.** `StaticPrefList.yaml` adds 20+
`zoom.stealth.*` entries, read inside the engine:

```
zoom.stealth.fpp.hw_seed            zoom.stealth.webgl.renderer
zoom.stealth.screen.width/height    zoom.stealth.webgl.vendor
zoom.stealth.audio.sample_rate      zoom.stealth.webgl.extensions
zoom.stealth.audio.output_latency_ms  zoom.stealth.webgl.int_params
zoom.stealth.audio.max_channel_count  zoom.stealth.webgl.shader_precisions
zoom.stealth.hw_concurrency         zoom.stealth.font.metrics
zoom.stealth.voices.list            zoom.stealth.canvas.noise_skip_mask
zoom.stealth.timezone               zoom.stealth.canvas.substitute_pixels
```

Architecturally this is the same pattern as Camoufox's `MaskConfig`: one seeded config
consumed by C++ getters, so there is no JS wrapper to inspect. (The `zoom.` prefix is
reuse of an existing pref branch that already had `mirror:always` plumbing to reach all
processes — pragmatic, but it does mean the namespace reads oddly.)

**2. Canvas noise written against specific detector internals.** From
`CanvasRenderingContext2D.cpp`, applied to the pixel buffer *before* `toDataURL` /
`getImageData` return:

- Skips canvases below 64×64 — reCAPTCHA probe canvases and favicon-sized assets — "to
  avoid altering signals reCAPTCHA uses for behavioural coherence".
- Skips the alpha channel to preserve transparency.
- **Skips zero-valued channels specifically to survive CreepJS's `clearRect` trap** —
  CreepJS draws, clears, then re-reads; if cleared pixels are not 0 it sets `lied=true`.
- ±1 on a single channel for ~12.5% of pixels, via a configurable skip mask; the comment
  notes Intel HD profiles use ~6.25% "to stay below FP Pro's `tampering_ml` threshold".
- Seed → Fibonacci hash mixed with pixel index, so it is deterministic per seed.

Knowing that CreepJS flags non-zero cleared pixels, and tuning noise density against a
named detector's ML threshold, is not something a superficial patch set contains.

**3. A full SOCKS5 UDP ASSOCIATE implementation.** `nsSOCKSUDPIOLayer.cpp` (+423) adds
greeting, optional user/password auth, UDP associate, relay addressing and logging —
alongside +2,037 lines in nICEr's `ice_component.c`. Firefox does not proxy WebRTC UDP
natively; this is what lets media traffic traverse a SOCKS proxy instead of revealing
the host address. It is the single largest and hardest piece of work in the diff, and it
targets the leak channel that defeats most proxy setups.

Font handling shows similar care: `zoom.stealth.font.metrics` accepts either a
multiplicative factor or an absolute px target, with the arithmetic done in C++ so one
pref value behaves identically on a Linux host presenting a Windows persona.

**Assessment:** comparable in ambition and detector-awareness to Camoufox. The claim
"the fingerprint is produced by the engine instead of injected into the page" is
supported by the code.

---

## Supply chain

| Property | Finding | Tier |
|---|---|:--:|
| Binary origin | `https://github.com/feder-cr/firefox_antidetect_patch/releases/download/{tag}/{asset}` — same org as the source, public | **A** |
| Checksums published | `checksums.txt` in every release | **A** |
| Checksums verified in code | **Yes** — `download.py` uses `hashlib`, `_sha256_file`, `_parse_checksums`, `verify_engine` | **A** |
| Cached binaries re-verified | **Yes** — verification runs against already-cached engines, not just fresh downloads | **A** |
| Dependency pinning | `invisible-core==19.14.0`, an exact `==` specifier rather than a git direct reference, with an import-time assertion in `_pin.py` | **A** |
| Dangerous constructs | **None found**: no `eval`/`exec`, no `pickle.load`, no `shell=True`, no `verify=False` in either package | **A** |

Re-verifying cached engines is better practice than most tools here — it catches a
tampered cache, not just a tampered download. The pinning rationale is documented at
length in `pyproject.toml`: they moved off a git direct reference specifically because
`pip check` cannot detect a violated direct reference and reports success.

---

## Other network activity

Every external host referenced in the two installed packages:

| Host | Purpose | Trigger |
|------|---------|---------|
| `github.com` | engine binary download | first run / version change |
| `api.github.com` | release lookup | download path |
| `api.ipify.org`, `icanhazip.com`, `checkip.amazonaws.com` | public-IP echo for `timezone="auto"` geo resolution; routed through the proxy when one is set | only when timezone auto-resolution is used |
| `pypi.org` | version checks in maintainer tooling | not the runtime path |

A fourth package, [`invisible_firefox`](https://github.com/feder-cr/invisible_firefox)
(a desktop profile manager), integrates the commercial proxy provider `api.sx.org` using
a key the user supplies. **It is not a dependency of `invisible_playwright`** — that
package requires only `invisible-core` and `playwright` — so it is not in the install
path being reviewed here.

---

## Code quality

Production code only; tests and vendored trees excluded. Method and comparison against
the other tools: [CODE-REVIEW.md](CODE-REVIEW.md).

| Metric | `invisible_playwright` | `invisible_core` |
|---|---:|---:|
| Production LOC | 6,744 | 10,536 |
| Test files | 48 | 40 |
| Bare `except:` | 2 | 0 |
| Broad `except` | 36 (5.3/kLOC) | 37 (3.5/kLOC) |
| `print(` | 394 | 156 |
| `time.sleep` | 33 | 3 |
| TODO/FIXME | 0 | 0 |
| `shell=True` / `eval` / `pickle` / `verify=False` | 0 / 0 / 0 / 0 | 0 / 0 / 0 / 0 |

Notable: **88 test files across two small packages** is a high ratio — comparable to
Scrapling's discipline and far above Botasaurus's driver (zero). Broad-exception density
(~5.3/kLOC in the wrapper) is on the higher end, similar to SeleniumBase and Clearcote.
The comment style is unusually discursive: `pyproject.toml` carries ~25 lines explaining
one version pin, and commit subjects read as prose rather than conventional-commit
prefixes.

---

## Claims versus source

The submission stated *"I would rather give you what is measured than what is claimed."*
That holds up better than most:

| Claim | Status |
|---|---|
| Firefox patched in C++ and rebuilt | **Verified (A)** — 104 files across `gfx`, `dom`, `netwerk`, `js/src` |
| Fingerprint set in the engine, no JS shims on the page | **Consistent with the diff (A)** — changes are in C++ engine paths, not content scripts |
| Driven by stock Playwright | **Verified (A)** — wrapper depends on unmodified `playwright`; Juggler lives in the browser, as it must |
| Same seed reproduces the same machine | **Not verified (D)** — no run was performed |
| Test harness is public and reproducible | **Verified present (A)** — 48 test files, 9 CI workflows, all six named detectors plus reCAPTCHA referenced throughout |
| Detector-suite results in the README | **Tier B** — author-run, not reproduced here |
| Anti-bot service coverage | **Not claimed** — the project makes no Cloudflare/DataDome/Kasada assertions |

Declining to claim WAF coverage while publishing detector results is the same posture
[Clearcote](./clearcote.md) takes, and it is more checkable than a vendor grid.

---

## Comparison

Against the other engine-level Firefox and Chromium entries:

| | invisible_playwright | Camoufox | Clearcote | CloakBrowser |
|---|---|---|---|---|
| Engine | Firefox 151 fork | Firefox 152 fork | Chromium 149 (ungoogled) | Chromium 150 |
| Spoofing level | C++ engine | C++ engine | C++ engine | C++ engine |
| Engine source published | **Yes** — full fork | Yes | Yes | **No** |
| Patch readability | tree diff, no series | 34 `.patch` files | 32 in `patches/series` | n/a |
| Client | **stock Playwright** | own launcher | Playwright/Puppeteer SDK | Playwright/Puppeteer SDK |
| Launch telemetry | **yes, on by default** | none found | none found | none found |
| Binary checksum verified in code | Yes, incl. cached | Yes | Yes (+ GPG) | Yes (Ed25519) |
| Fingerprint rotation | per-seed | BrowserForge statistical | per-seed / real-profile import | per-seed |

It is the **only tool in this comparison whose browser makes an unsolicited network
request at startup by default**, and the only Firefox entry driven by an unmodified
Playwright client.

---

## Applicability

**Suited to:** Playwright codebases that want engine-level Firefox fingerprinting without
adopting a bespoke launcher API — existing `playwright` code runs against it unchanged.
Also to reviewers who want to read the actual engine changes, provided they are willing
to clone a multi-gigabyte tree.

**Constraints:** Firefox only, so targets that probe SpiderMonkey engine behaviour
identify the browser family regardless of configuration — the same structural limit
Camoufox documents. Two contributors. The engine fork is large and awkward to audit, and
the shipping line's diff exceeds what GitHub will render. Turn the launch ping off if
startup traffic to `github.com` is in your threat model.

**Before deploying:**

```python
browser = firefox.launch(extra_prefs={"invisible_firefox.usage_ping.enabled": False})
```

---

*Analysis conducted for educational purposes against the source at the commits above,
read in an isolated container — see [METHODOLOGY.md](METHODOLOGY.md#source-handling).
Nothing was installed, built, or executed. Use responsibly.*
