# invisible_playwright - Technical Analysis

> **Tool Type:** Custom Firefox Build (Anti-Detect Browser) driven through a vendored, modified copy of Playwright's Python client
> **Repository:** [github.com/feder-cr/invisible_playwright](https://github.com/feder-cr/invisible_playwright) (wrapper) · [feder-cr/invisible_core](https://github.com/feder-cr/invisible_core) (config/download) · [feder-cr/firefox_antidetect_patch](https://github.com/feder-cr/firefox_antidetect_patch) (the engine)
> **Approach:** Firefox patched in C++ source and rebuilt; fingerprint produced by the engine rather than injected into the page. Since wrapper `0.7.3` the Python client is a **modified, vendored copy of Playwright** (`invisible_playwright._pw`), and since `0.8.0` the Node driver is gone: a Python server in `_juggler/` speaks the Juggler protocol to the browser directly. See [The client](#the-client-vendored-playwright-and-an-in-process-juggler-server).
> **Verified in source (Tier A):** the engine is a genuine GitHub fork of `mozilla-firefox/firefox` (GitHub API, 2026-08-14). The stealth work is on branches `stealth/150` and `stealth/151`, **not** on `main`; the branch that ships is `stealth/151`, whose commit `a3819a7` (tag `firefox-41`) is sealed into the core the wrapper pins as engine `firefox-41`. A diffable tag pair `stealth-base/v150.0.1` → `stealth-head/v150.0.1` resolves to **104 files changed, +14,279 / −59** (20 commits per GitHub's compare view on 2026-08-14; the sandbox clone is shallow).
> **Anti-bot service claims:** none as pass rates. The project publishes detector-suite results (CreepJS, BotD, FingerprintJS, fpscanner, Sannysoft, BrowserLeaks, reCAPTCHA scoring) rather than WAF pass rates — **Tier B** for the results, **Tier D** for commercial-service coverage. Its README names reCAPTCHA, hCaptcha and Cloudflare Turnstile as the scorers of the "two questions" it says it answers (`README.md:18`) and links per-vendor explainer articles.
> **Maintenance:** wrapper `0.35.3` (2026-10-13), pinning `invisible-core` `41.39.0` (2026-10-13); engine release `firefox-41` (Firefox 151.0, tag dated 2026-10-11). A `firefox-42` tag (2026-10-13) and an unreleased core commit sealing it (`20da2af`, "42.39.0") exist; no published core carried it at this revision. 3,135 stars, 304 forks, 8 contributors, 5 open issues (2026-10-13). The wrapper declares `MIT AND Apache-2.0` (the vendored Playwright client is Apache-2.0; GitHub reports MIT), and since `38.34.0` the core declares the same (`pyproject.toml:17-22`), because it now carries the Juggler client and Playwright's injected script; the engine fork inherits MPL-2.0 from mozilla-central (GitHub reports `NOASSERTION`).
> **Verified:** 2026-10-13 against `invisible_playwright` @ `91ea73b` (0.35.3), `invisible_core` @ `415bbd8` (v41.39.0), `firefox_antidetect_patch` @ `a3819a7` (`stealth/151`, tag `firefox-41`).

> [!IMPORTANT]
> **The shipped browser contacts GitHub once on every launch.** It is disclosed and
> disableable. The engine repository's README and the wrapper's `CHANGELOG.md` describe it;
> the wrapper's README does not. Details in [Launch telemetry](#launch-telemetry).

---

## Table of Contents

- [Are the patches public?](#are-the-patches-public)
- [Launch telemetry](#launch-telemetry)
- [What the patches actually change](#what-the-patches-actually-change)
- [The client: vendored Playwright and an in-process Juggler server](#the-client-vendored-playwright-and-an-in-process-juggler-server)
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
| `firefox_antidetect_patch` is a real fork of `mozilla-firefox/firefox` | **Yes** — GitHub API reported `fork: true`, parent `mozilla-firefox/firefox` (2026-08-14; the API was not re-queried on 2026-09-30 or 2026-10-13). The clone also carries upstream history, e.g. `0a95d145f7` "Merge autoland to mozilla-central" (2026-05-18) |
| Repository public | Yes, ~4,960 MB (API, 2026-08-14) |
| Stealth work present | Yes — `origin/stealth/151` (the sealed `firefox-41` commit is `a3819a7`, 2026-10-11; the branch head `e1d45b2d5e`, 2026-10-12, carries `firefox-42`) and the `stealth/150` tag pair; `main` carries no engine patches. Further remote branches hold work in progress (`next/firefox-43`, `next/firefox-41-b149`, `fix/*`, `research/*`) |
| Diffable base provided | Yes — tags `stealth-base/v150.0.1` and `stealth-head/v150.0.1`, unchanged since 2026-08-14 |
| That comparison resolves to | **104 files changed, +14,279 / −59** (re-derived with `git diff --shortstat` on 2026-10-13); 20 commits per GitHub's compare view on 2026-08-14 |
| Built binaries published | Yes — git tags `firefox-21` … `firefox-42` in the clone; `firefox-41` (2026-10-11) is the tag the seal in `invisible-core` 41.39.0 pins (`seal.json`, `source_commit` `a3819a7`). Per-platform archives (Windows x86_64 `.zip`, Linux x86_64 and arm64 `.tar.gz`) plus a `checksums.txt` generated by the release workflow (`.github/workflows/release.yml:523-528`). macOS legs were removed from the release pipeline on 2026-08-26 (`eed9abeffe`) |

### Three caveats that matter more than the headline

**1. The default branch shows none of the engine work.** `main` is 10 commits after the
last mozilla-central merge in the clone (`0a95d145f7`) and changes **5 files** —
`README.md` and four CI workflows (`mac-font-probe.yml`, `republish.yml`,
`verify-assets.yml`, `verify-cloak.yml`). On 2026-08-14 it was 5 commits and 2 files. The
`main` README does say that `stealth/151` "is the source of truth" (`README.md:18-20`),
alongside a stale "Current release: firefox-18". The wrapper repositories contain **zero**
`.cc`/`.cpp`/`.h` files, **zero** `.patch` files, and no `patches/` directory
(`git ls-files` over `invisible_playwright` and `invisible_core` at the pinned commits).
The wrapper README links to the repository `feder-cr/firefox_antidetect_patch`, not to a
branch.

**2. GitHub could not render the shipping diff.** Comparing
`last-mozilla-central...stealth/151` returned HTTP 422, *"Sorry, this diff is taking too
long to generate."* (observed 2026-08-14; not re-queried). The 150-line pair works because
it is smaller. Auditing the shipping line requires a local clone of a multi-gigabyte
tree. Between `d5457fa` and `fec80c8` the tree changed in 116 files; the sandbox clone is
shallow and shows at least 41 commits in that span (its history for the branch begins on
2026-08-23). From `fec80c8` to `a3819a7` a further 50 files changed (+1,915 / −680, 35
commits); `d5457fa` to `a3819a7` is 150 files.

**3. The titled patch series is not public.** The branch carries a
`STEALTH_BRANCH_README.md` (byte-identical at `d5457fa`, `fec80c8` and `a3819a7`, and still written
for `stealth/150`). It says that a companion repository, `feder-cr/firefox-stealth`, held a
numbered series (`0001-build-infra.patch` … `0015-storage-quota.patch`), that the series
was consolidated into the branch as commits, and (line 66) how to regenerate one:

```bash
git format-patch stealth-base/v150.0.1..stealth/150 -o ../firefox-stealth/
```

That repository — `feder-cr/firefox-stealth` — **returns HTTP 404** (2026-08-14, and
again on 2026-10-13), as does `feder-cr/invisible_firefox`, the repository named in the
file's clone instructions (line 39; checked 2026-10-13). So the readable, titled series
referenced by the project's own documentation is not publicly available; only the forked
tree and the base/head tag pair are. You can regenerate an equivalent series yourself with
the command above once you have cloned the fork, which is more than
[CloakBrowser](./cloakbrowser.md) offers, but less than [Camoufox](./camoufox.md) (44
`.patch` files in `patches/`) or [Clearcote](./clearcote.md) (37 in `patches/series`), where
the diffs can be read in an afternoon without cloning anything.

**Net:** *auditable in principle, considerably harder in practice.* That is a real
distinction from [CloakBrowser](./cloakbrowser.md), whose engine source is not published
at all — but it is not equivalent to a readable patch series.

---

## Launch telemetry

**The patched browser issues one HTTPS GET to GitHub every time the process starts.**
Verified in source, not inferred. The address is now a preference rather than a literal
(it was a literal at `d5457fa`):

```javascript
// browser/components/BrowserGlue.sys.mjs:387-423  (stealth/151 @ a3819a7, unchanged since fec80c8; comments abridged)
// Gate via pref `invisible_firefox.usage_ping.enabled` (default true).
// To permanently disable, remove this block and rebuild from source.
// Full disclosure: "Anonymous launch counter" in this repo's README.
try {
  if (Services.prefs.getBoolPref("invisible_firefox.usage_ping.enabled", true)) {
    const usagePingUrl = Services.prefs.getStringPref(
      "invisible_firefox.usage_ping.url",
      "https://github.com/feder-cr/invisible_playwright/releases/download/usage-counter/launch.txt");
    fetch(usagePingUrl, { method: "GET", credentials: "omit", cache: "no-store" })
      .catch(() => {});
  }
} catch (e) {}
```

```javascript
// browser/app/profile/firefox.js:3683 and :3689
pref("invisible_firefox.usage_ping.enabled", true);
pref("invisible_firefox.usage_ping.url", "https://github.com/feder-cr/firefox_antidetect_patch/releases/download/usage-counter/launch.txt");
```

```python
# invisible_core  src/invisible_core/prefs.py:361-362 and :1983  (@ v41.39.0), applied to every session
USAGE_PING_URL = ("https://github.com/feder-cr/firefox_antidetect_patch"
                  "/releases/download/usage-counter/launch.txt")
prefs.setdefault("invisible_firefox.usage_ping.url", USAGE_PING_URL)
```

The asset's GitHub `download_count` is used as a global launch counter for a badge
(rendered at `README.md:309` of the wrapper).

**What changed since 2026-08-14.** At `d5457fa` the address was a literal,
`https://github.com/feder-cr/invisible_firefox/releases/download/usage-counter/launch.txt`
(`BrowserGlue.sys.mjs:404`). The comment now in the block (`:396-408`) records that the
counter "has died twice" because the address was a repository name compiled into every
binary: a repository name was reused on 2026-07-22, and the hosting repository was
deleted on 2026-08-18. The `invisible_firefox` repository returns HTTP 404 (checked
2026-10-13). The pref was introduced with `firefox-21`; engines older than that do not
read it (`invisible_core/prefs.py:1979-1980`). The check is still present, still on by
default, and still gated by `invisible_firefox.usage_ping.enabled`.

### Assessment

| Property | Finding |
|---|---|
| **Enabled by default** | Yes — `pref(..., true)` (`firefox.js:3683`). Neither `invisible_playwright` nor `invisible_core` sets `invisible_firefox.usage_ping.enabled`; the only assignment of it in either tree is a test (`invisible_core/tests/test_usage_ping_address.py:49-50`) |
| **What is transmitted** | An HTTP GET with a standard Firefox User-Agent. `credentials: "omit"` (no cookies), `cache: "no-store"`, no payload, no identifier, no query string |
| **Where it goes** | The URL in pref `invisible_firefox.usage_ping.url`. The engine default (`firefox.js:3689`) and the value the core declares for every session (`prefs.py:361-362`) are the same address on `firefox_antidetect_patch`; the literal fallback if the pref is absent points at `invisible_playwright` (`BrowserGlue.sys.mjs:419`) |
| **When** | At `final-ui-startup`, before any tab exists: `_beforeUIStartup` (`BrowserGlue.sys.mjs:386`) is called from the `final-ui-startup` case (`:194-195`) |
| **Failure behaviour** | Fire-and-forget; `.catch(() => {})`, wrapped in `try/catch` (`:415-423`). The browser never blocks on it |
| **Does it respect the proxy?** | **Not established, and the source ordering points the other way.** The previous revision of this page said "Yes" on the basis of `network.proxy.*` prefs; that no longer describes the code. Session proxies are no longer written to `network.proxy.*` for any scheme (`invisible_core/_proxy.py:145-150`). Since core `41.35.0` the core's Juggler client sends the engine command `Browser.setBrowserProxy` over the pipe once the browser has printed its readiness line, "before any page exists" (`invisible_core/juggler/connection.py:927-928`, `:985`; until then each client sent it itself), and the engine applies it through a channel filter created in Juggler's own `final-ui-startup` handler (engine files `juggler/components/Juggler.js:92-96`, `juggler/NetworkObserver.js:647-675`, `juggler/TargetRegistry.js:349-386`, with the proxy-to-route logic moved into `juggler/SessionRoute.js` at `3a5f5d4`). The ping `fetch()` is issued from the same notification (`BrowserGlue.sys.mjs:420`), before any command can arrive over that pipe. `prefs.py:448-450` still sets `socks_remote_dns` and `socks5_remote_dns` to `True` and `failover_direct` to `False`. Whether the request leaves through the session proxy was not run — **Tier D** |
| **Opt-out** | `invisible_firefox.usage_ping.enabled = false` via `about:config` or `InvisiblePlaywright(extra_prefs={...})` (`launcher.py:107`); permanently by removing the block and rebuilding |
| **Disclosed** | Engine repository: an "Anonymous launch counter" section in its README (`README.md:52-88` at `a3819a7`, which still names `feder-cr/invisible_firefox` as the host at `:55` and `:63`), plus comments at both source sites. Wrapper: `CHANGELOG.md:1346-1361` (0.12.2, 2026-09-05) and a badge image (`README.md:309`). The comment at `firefox.js:3682` points to the README of `invisible_playwright` as the full disclosure |

> [!WARNING]
> **The wrapper's README does not disclose it.** Searching the `invisible_playwright`
> repository at `91ea73b` for `usage_ping`, `launch counter`, `launch.txt` or
> `usage-counter` returns matches only in `CHANGELOG.md` (lines 1349-1355, the 0.12.2 entry)
> and in a maintainer script (`scripts/sync_article_pixels.py:11`). `README.md` and
> `docs/` return none, and `README.md:309` shows only a "browser launches" badge image.
> `CHANGELOG.md` is linked from the project URLs (`pyproject.toml:189`) but is not among the
> files the sdist includes (`pyproject.toml:202`). The 2026-08-14 revision of this page
> reported 0 matches in the whole repository; at `f777798` the README already carried a
> badge link whose URL contained `usage-counter`, with no explanation. A user who installs
> the package and reads its README is not told that the browser contacts GitHub on every
> launch.

**What the ping is and is not.** It is a counter, not a profile: no identifier, no
payload, no cookies, a documented pref gates it, and the engine repository documents it.
The open points are where the disclosure sits (engine README and wrapper changelog, not
the wrapper README), the default state (on), and the proxy behaviour above. If the ping
precedes the session proxy, as the source ordering suggests, the request to `github.com`
would not use it; the pref removes the request.

---

## What the patches actually change

Areas touched by the 104-file `stealth-base → stealth-head` diff (the `stealth/150` tag
pair, re-derived 2026-10-13), grouped by tree location. This maps cleanly onto the
[detection-layer taxonomy](README.md#detection-layers-and-which-tools-address-them):

| Area | Files | Layer |
|------|------:|-------|
| `juggler/**` (screencast, content, protocol, pipe, components) | 41 | automation protocol — Playwright's Firefox transport |
| `netwerk/**` (socket, http, base) | 9 | 4 — network |
| `gfx/thebes` | 6 | 2 — fonts, graphics |
| `dom/media/webrtc/transport` (incl. `nICEr/src/ice`) | 7 | 4 — WebRTC IP |
| `dom/base` | 5 | 2 — navigator surfaces |
| `dom/media/webaudio` | 4 | 2 — audio fingerprint |
| `js/src/vm`, `js/src/debugger` | 4 | 1 — JS engine / debugger tells |
| `dom/media/webspeech/synth` | 2 | 2 — speech voices |
| `modules/libpref/init` | 2 | defaults (includes the usage-ping pref) |

The shipping branch has moved since that pair was cut: between `d5457fa` and `fec80c8`
`stealth/151` changed in 116 files (at least 41 commits are visible in the shallow clone),
and by `a3819a7` in 150.
By commit subject and diff, those changes include a
rework of the screencast and hidden-window capture, a visible-pointer overlay
(`juggler/StealthCursor.js`), a bundled font set with a generated metrics manifest
(`browser/fonts/`, `gfx/thebes/StealthBundleFontList.cpp`), removal of the updater from the
build, a fix for authenticated HTTP proxies going out direct, and the removal of macOS from
the release pipeline. Between `fec80c8` and `a3819a7` (engines `firefox-35` to `firefox-41`)
the commit subjects and diffs show: window geometry computed from a device-pixel frame for
the maximized main window and page-opened popups; service workers blockable per context
(`Browser.setServiceWorkersBlocked`); `Page.dispatchMouseEvent` answering once the page has
handled the event; pointer input corrected for page zoom; hand-built `input`/`change` events
replaced by `Page.selectOptions` and `Page.setUserInput` through Firefox's own user paths;
per-context locale for workers and `Accept-Language`; `bypass_csp` read where CSP is applied;
an X11 occlusion pref; and the shutdown-ping change described under
[Other network activity](#other-network-activity). The tables and snippets below describe
the tag pair unless an `a3819a7` line says otherwise.

> [!NOTE]
> **The Juggler files are the part of the engine a Playwright-style client needs.**
> Playwright drives Firefox over Juggler, which is not part of upstream Firefox — any
> Firefox intended to be driven this way must carry it. That is separate from the *client*
> side, which is no longer a stock `playwright` package: see
> [The client](#the-client-vendored-playwright-and-an-in-process-juggler-server).
> [Camoufox](./camoufox.md) makes a different trade: it patches Juggler *and* ships its
> own launcher.

### What the code level shows

The diff is **+14,279 / −59 lines**. Read at the code level, three things stand out:

**1. A C++ fingerprint surface driven by static prefs.** At `stealth-head/v150.0.1`,
`StaticPrefList.yaml` adds 24 `zoom.stealth.*` entries (44 at `fec80c8`, 46 at `a3819a7`),
read inside the engine:

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

At `a3819a7` this list differs. Four tag-head entries are gone (`font.metrics`,
`font.whitelist`, `timezone`, `webrtc.public_ip`; a comment at `StaticPrefList.yaml:20771`
says nothing read `timezone`, and it was removed 2026-08-09), and 26 were added, among them
fonts (`font.fontlist`, `font.system_ui`, `fonts.generics`, `fonts.manifest`,
`text.coverage_ladder`), screen and window geometry (`screen.taskbar_px`, `color_depth`,
`frame_border`, `maximized_ui`, `popup_ui`, `popup_position`, `avail_device_width`,
`avail_device_height`), pointer and touch (`pointer.primary`, `pointer.all`,
`max_touch_points`), media (`media.decode_support`, `media.decoding_info`),
`audio.fp_noise`, `dns.no_local_resolution`, `webrtc.no_direct_udp` and
`widget.occlusion_tracking.enabled`. Between `fec80c8` and `a3819a7` five entries were
removed (`http.accept_language`, which nothing read, and `screen.chrome_w`, `chrome_h`,
`window_x`, `window_y`) and seven added (the last six geometry entries above and the
occlusion pref).

Architecturally this is the same pattern as Camoufox's `MaskConfig`: one seeded config
consumed by C++ getters, so there is no JS wrapper to inspect. (The `zoom.` prefix is
reuse of an existing pref branch that already had `mirror:always` plumbing to reach all
processes — pragmatic, but it does mean the namespace reads oddly.)

**2. Canvas noise written against specific detector internals.** From
`CanvasRenderingContext2D.cpp` (`:2264-2338` at `a3819a7`, unchanged since `fec80c8`;
`:2261-2312` at the tag head),
applied to the pixel buffer *before* `toDataURL` / `getImageData` return:

- Skips canvases below 64×64 — reCAPTCHA probe canvases and favicon-sized assets — "to
  avoid altering signals reCAPTCHA uses for behavioural coherence".
- Skips the alpha channel to preserve transparency.
- **Skips zero-valued channels specifically to survive CreepJS's `clearRect` trap** —
  CreepJS draws, clears, then re-reads; if cleared pixels are not 0 it sets `lied=true`.
- ±1 on a single channel for ~12.5% of pixels, via a configurable skip mask; the comment
  notes Intel HD profiles use ~6.25% "to stay below FP Pro's `tampering_ml` threshold".
- Seed → multiplicative (Fibonacci-style) hash mixed with pixel index, so it is
  deterministic per seed.

The comments name CreepJS's `clearRect` check and FP Pro's `tampering_ml` as the detector
behaviour the density was tuned against. At `a3819a7` the file also has a substitution mode
(`zoom.stealth.canvas.substitute_pixels`) and a skip for privileged readbacks
(`:2345-2352`), and comments in the substitution path (`:2389-2407`) say that the actual
FP Pro `tampering_ml` driver was `OfflineAudioContext` noise (`zoom.stealth.audio.fp_noise`)
and that the earlier small-canvas hypothesis was a red herring.

**3. A SOCKS5 UDP ASSOCIATE implementation in the network stack — present, and gated
off by default.** `nsSOCKSUDPIOLayer.cpp` (+423 lines against upstream, the same at the tag
head, at `fec80c8` and at `a3819a7`) adds greeting, optional user/password auth, UDP associate, relay
addressing and logging. At the tag pair the diff also adds `nICEr/src/ice/ice_component.c`
(2,037 lines; the upstream `150.0.1` tree has `ice_component.cpp`, 1,821 lines, and no
`.c`) and +127 lines in `ice_component.cpp`; at `a3819a7` (as at `fec80c8`) `ice_component.c` is absent and
`ice_component.cpp` is 371 lines larger than the `150.0.1` tree (ignoring line endings).
Firefox does not proxy WebRTC UDP natively, and this layer is what would let media traffic
traverse a SOCKS proxy. It is only hooked in when the pref `network.proxy.socks_remote_udp`
is true (`netwerk/base/nsUDPSocket.cpp:614-624`, default `false`), and `invisible_core` does
not set it: `_proxy.py:278-290` records `UDP_GOES_THROUGH_SOCKS = False` ("UDP goes around
the proxy" without it). Behind a proxy the core sets `zoom.stealth.webrtc.no_direct_udp`
(`_proxy.py:271`) and the engine synthesises a server-reflexive candidate from the exit IP
(`ice_component.cpp`, `nr_stealth_bridge.cpp`). Since `16ef4d9` (2026-10-02) `ice_ctx.cpp`
refuses a wildcard target for its default-route probe, so on Linux behind SOCKS with remote
DNS the candidate path falls back as on Windows (per the commit message, no host candidate
and no synthetic server-reflexive candidate were produced before). The previous revision of this page
described the UDP layer as what carries WebRTC media through a SOCKS proxy; the code
shows it is available but not enabled by the wrapper or core.

Font handling at the tag pair shows similar care: `zoom.stealth.font.metrics` accepts either
a multiplicative factor or an absolute px target (`gfx/thebes/gfxTextRun.cpp:43-65`), with
the arithmetic done in C++ so one pref value behaves identically on a Linux host presenting
a Windows persona. At `a3819a7` that pref is absent and fonts come from a bundled set:
`browser/fonts/` (128 files) with a generated manifest, `bundle-fonts.list`, carrying
per-face vertical metrics (`gfx/thebes/StealthBundleFontList.cpp`).

**Architecture:** the same seeded-config-in-C++ pattern as Camoufox. The claim "the
fingerprint is produced by the engine instead of injected into the page" is consistent
with the code; the client additionally runs a page-side script (`invisible_core/juggler/injected.js`)
in Firefox's utility world for selectors and actionability, and generates pointer motion in
Python (see below).

---

## The client: vendored Playwright and an in-process Juggler server

The first revision of this page described the client as an unmodified `playwright`
package. That was accurate at wrapper `0.7.0` (`playwright>=1.55,<=1.61.0` was a
dependency) and is not accurate at `0.35.3`.

| Property | Finding | Tier |
|---|---|:--:|
| Dependencies | `invisible_core==41.39.0`, `psutil>=5.9`, `pyee>=13,<14`, `greenlet>=3.1.1,<4.0.0`. **`playwright` is not a runtime dependency** (`pyproject.toml:46-117`; the comment at `:73-78` says reintroducing it would not visibly break anything); it appears only in the `dev` extra, pinned `playwright==1.61.0` (`:120`) | **A** |
| What is vendored | Playwright's Python client as `invisible_playwright._pw` (68 files), Apache-2.0 (`_pw/LICENSE`). `THIRD_PARTY_FORK.md:14` gives the version as 1.61.1; `_pw/_repo_version.py` and `_pw/README.md` say 1.61.0. Added in wrapper `0.7.3` (2026-08-26; `CHANGELOG.md:1690-1697`). Imports are rewritten to the `invisible_playwright._pw` namespace so it does not collide with an installed `playwright` (`THIRD_PARTY_FORK.md:16-18`). `pyproject.toml:30` declares `MIT AND Apache-2.0` | **A** |
| What was changed in it | Files carrying a `MODIFIED by invisible_playwright` marker: `_pw/_impl/_connection.py:485`, `_pw/_impl/_playwright.py:44` (chromium and webkit refused), `_pw/_impl/_browser.py:80`, `:127`, `:240` and `_pw/_impl/_browser_context.py:94`, `:400` (page numbering within a session, added since 0.25.7), `_pw/{sync,async}_api/_context_manager.py` (transport selection and a bridge to the in-process server), `_pw/{sync,async}_api/_generated.py` (chromium/webkit accessors raise). The `0.7.3` changelog entry lists four changes over upstream 1.61.1: `set_content` waits for load, ~643 KB of unused subsystems removed (android, electron, bidi, recorder, chromium, webkit), `_exposeConsoleApi` neutralised, `console.debug` dropped from injected code | **A** |
| Node driver | **Removed.** `_driver/` (6 MB of JavaScript) and the 92 MB `node.exe` download are gone (`CHANGELOG.md:1612-1621`, `0.8.0`, 2026-08-30; `THIRD_PARTY_FORK.md:20` dates it 2026-08-28). A first install downloads the browser only | **A** |
| What replaces it | Two layers since wrapper `0.30.0` / core `38.34.0`. The wrapper's `_juggler/` answers the Playwright protocol: `server.py` (4,455 lines), `dispatcher.py`, `transport.py`, `_marshal.py`, `perimeter.py`. The Juggler client it drives moved into the core as `invisible_core.juggler`: `connection.py` (JSON delimited by a zero byte; fd 3/4 on POSIX, inheritable handles on Windows), `protocol.py` (generated from the `Protocol.js` inside the shipped binary; 77 commands, 35 events), `actions.py`, `_motion.py`, `keyboard.py`, `lifecycle.py`, `instance.py`, `injected.py`, `keylayout.py`, and `injected.js` (8,121 lines, extracted from Playwright's injected script, with six marked changes at `:6489`, `:6674`, `:7214`, `:7241`, `:7419`, `:7697`) loaded into Firefox's utility world. The core's `THIRD_PARTY.md` says the same client previously existed as a copy in each of `invisible_playwright`, `invisible_selenium` and `invisible_puppeteer` | **A** |
| Out of scope (refused by name) | Tracing, HAR, video annotations, the recorder, `APIRequestContext`, CDP sessions, clock, WebAuthn, PDF (`_juggler/perimeter.py`); a few operations refuse for lack of an engine command (`setOffline`, `setWebSocketInterceptionPatterns`). The README lists the same area as "tracing, HAR, CDP, the API request context" (`README.md:47`) | **A** |
| Pointer motion | `humanize=True` is the default (`launcher.py:104`). `_cursor.py` wraps the funnel behind `click`/`hover`/`dblclick`/`tap`/`check` and `mouse.move`, and `invisible_core.juggler._motion` plans the path in Python from the session seed, so the browser no longer expands the motion. `show_cursor` draws an overlay in the browser's chrome window. `prep_recaptcha=True` (opt-in; ignored when `profile_dir` is used, `launcher.py:226`) seeds cookies derived from the persona seed (`persona_cookies`, `invisible_core/_cookies.py:292`, called at `launcher.py:504`) | **A** |
| Version coupling | `_engine.assert_playwright_range()` (`_engine.py:71`) compares the **vendored** client's version with the range carried in the seal (`seal.json`: 1.55.0 – 1.61.0) | **A** |

The wrapper's README still says the returned object "is a `playwright.sync_api.Browser`"
(`README.md:79`); `launcher.py:9` imports `Browser` from `invisible_playwright._pw.sync_api`,
the vendored copy. `_fpforge/` and `_webgl_personas.py` inside the wrapper are 17- and 4-line
shims that alias the same modules in `invisible_core`, where the fingerprint sampler and the
GPU persona pool live; `_geo`, `_headless`, `_proxy`, `config`, `constants`, `download` and
`prefs` are 4-line aliases of the same kind.

---

## Supply chain

| Property | Finding | Tier |
|---|---|:--:|
| Binary origin | `https://github.com/feder-cr/firefox_antidetect_patch/releases/download/{tag}/{asset}` (`invisible_core/constants.py:144-146`) — same org as the source, public. The same host also served the profile manager until its deletion on 2026-08-18 (`constants.py:138-143`); releases below `firefox-14` were removed (`download.py:120`, `:157`). The pinned tag is `firefox-41` (`seal.json`) | **A** |
| Checksums published | `checksums.txt` generated by the release workflow (`firefox_antidetect_patch/.github/workflows/release.yml:523-528` @ `a3819a7`) | **A** |
| Checksums verified in code | **Yes — against the seal rather than the release file.** The archive's SHA-256 (`_sha256_file`, `download.py:398`) is compared with the per-asset digest in `seal.json`, which ships inside the `invisible-core` wheel (`download.py:626-634`). `_parse_checksums` (`download.py:406`) is defined and has no caller | **A** |
| Cached binaries re-checked | **Partly.** Each launch path runs `verify_engine` (`seal.py:623`; on a cache hit at `download.py:606`). It compares `application.ini` and `platform.ini` Version and BuildID with the sealed leg and requires the stealth markers in the Juggler entries (`seal.py:584-620`): an identity check, not a re-hash of the tree. The one content hash on the reuse path is `omni.ja` on Windows (`download.py:459-464`); the code prints that a Linux leg has no sealed payload digest (`download.py:465-472`) | **A** |
| Dependency pinning | `invisible_core==41.39.0`, an exact `==` specifier rather than a git direct reference (`pyproject.toml:72`), with an import-time assertion in `_pin.py`. The literal moves on every engine release (`pyproject.toml:61-63`) | **A** |
| Dangerous constructs | **None found** in either package's Python source, including the vendored `_pw/`: no `eval`/`exec`, no `pickle.load`, no `shell=True`, no `verify=False`. The page-side `invisible_core/juggler/injected.js` calls `eval` at `:6521`, `:6668`, `:6697` and `:6987` as part of Playwright's expression evaluation | **A** |

The pinning rationale is documented at length in `pyproject.toml` (`:51-71`): the
maintainers moved off a git direct reference because `pip check` cannot detect a violated
direct reference and reports success.

---

## Other network activity

Every external host referenced in the two installed packages (Python and JSON source; the
wrapper references none, the core's are below). The browser's own launch request is
covered under [Launch telemetry](#launch-telemetry):

| Host | Purpose | Trigger |
|------|---------|---------|
| `github.com` | engine binary download from `firefox_antidetect_patch` releases (`constants.py:144-146`); GeoIP database from `daijro/geoip-all-in-one` (`constants.py:159-163`, `_geoip_db.py:57`) | engine: first run / version change; GeoIP: when timezone or locale resolution is used |
| `api.github.com` | release lookup when `STEALTHFOX_GITHUB_TOKEN` or `GITHUB_TOKEN` is set (`download.py:42-43`, `:99`); latest-tag fallback for the GeoIP database (`_geoip_db.py:69`) | download path |
| `api.ipify.org`, `icanhazip.com`, `checkip.amazonaws.com` (`_geo.py:53-55`) | public-IP echo for timezone and locale resolution; routed through the proxy when one is set, from the host's own address otherwise | **default launch**: `timezone=""` and `locale="auto"` both resolve from the egress IP (`launcher.py:105-106`) |
| `api.ipify.org` over plain HTTP, through the proxy (`_capability.py:112`) | exit-capability probe | only reached if `UDP_GOES_THROUGH_SOCKS` is true (`_geo.py:807-809`); it is `False` (`_proxy.py:290`) |
| `pypi.org` (`release.py:107`) | version checks in maintainer tooling | not the runtime path |

`nodejs.org`, previously the source of the Node runtime, is no longer referenced: the
Node driver was removed in `0.8.0`.

**Firefox's own background traffic is left on by design.** The table above lists hosts
named in the Python packages; the browser also makes the requests a retail Firefox makes.
The core's prefs block for telemetry and data reporting is deliberately empty: a comment
dated 2026-08-19 records that the prefs that suppressed retail traffic (telemetry,
health report, Safe Browsing, Normandy, add-on updates, captive-portal and connectivity
checks, push) were removed so that Gecko's defaults apply (`invisible_core/prefs.py:762-795`).
The one exception is download reputation, `browser.safebrowsing.downloads.remote.enabled`
set to false (`prefs.py:829`), because the build has no Safe Browsing key and the request
would carry a sentinel string. The engine is built with `MOZILLA_OFFICIAL=1`
(`.mozconfig:49` at `a3819a7`), on which Firefox's telemetry reporting defaults on. Since
`firefox-40` (engine commit `3a5f5d4`, 2026-10-11) shutdown telemetry pings are sent by the
engine's own `--backgroundtask pingsender`, which is handed the session's proxy in
`STEALTHFOX_PINGSENDER_ROUTE` (`toolkit/components/telemetry/app/TelemetrySend.sys.mjs:1714-1764`,
`BackgroundTask_pingsender.sys.mjs`), instead of the separate `pingsender[.exe]`; the
commit message reports that the old sender posted to `incoming.telemetry.mozilla.org` from
the host's own address behind SOCKS5 and HTTP proxies (**Tier B**, not measured here). Core
`40.35.0` gives that sender 10 s to finish before the session's processes are ended
(`SENDER_GRACE`, `invisible_core/juggler/_profile.py:34`). Whether background requests
made earlier in startup, before the proxy command arrives, use the session proxy was not
run (**Tier D**).

The repository [`feder-cr/invisible_firefox`](https://github.com/feder-cr/invisible_firefox)
(a desktop profile manager that, in the last copy read, `602f70f` of 2026-08-14,
integrated the commercial proxy provider `api.sx.org` with a user-supplied key) **returns
HTTP 404** as of 2026-10-13. The wrapper's `pyproject.toml:61-63` and the core's
`constants.py:141-142` state that it was deleted on 2026-08-18. It was never a dependency
of `invisible_playwright`, which now requires only `invisible-core`, `psutil`, `pyee` and
`greenlet`; the current wrapper and core trees contain no URL of it except a changelog line
recording the rename (`CHANGELOG.md:1970`).

---

## Code quality

Production code only; tests and vendored trees excluded (here the vendored Playwright
client `_pw/` and the bundled `injected.js`, now `invisible_core/juggler/injected.js`). Method and comparison against the
other tools: [CODE-REVIEW.md](CODE-REVIEW.md).

| Metric | `invisible_playwright` | `invisible_core` |
|---|---:|---:|
| Production LOC | 13,612 | 26,472 |
| Test files | 129 | 90 |
| Bare `except:` | 1 | 0 |
| Broad `except` | 67 (4.9/kLOC) | 62 (2.3/kLOC) |
| `print(` | 574 | 251 |
| `time.sleep` | 48 | 15 |
| TODO/FIXME | 0 | 0 |
| `shell=True` / `eval` / `pickle` / `verify=False` | 0 / 0 / 0 / 0 | 0 / 0 / 0 / 0 |

The wrapper shrank and the core grew because the Juggler client moved from the wrapper to
the core in `38.34.0` (wrapper `0.30.0`). The metrics script's `eval`/`exec` pattern also
matches four mentions in the wrapper's `docs/*.md`; none is in code. For scale: the vendored
`_pw/` is 68 files and 61,997 Python lines (two generated API files of about 23,700 lines
among them), and `invisible_core/juggler/injected.js` is 8,121 lines. The wrapper has
9 CI workflows and the core 3. The comment style is discursive: `pyproject.toml` carries
about 25 lines explaining one version pin (`:47-71`) and commit subjects read as prose
rather than conventional-commit prefixes.

---

## Claims versus source

The submission stated *"I would rather give you what is measured than what is claimed."*
Against the source at the commits above:

| Claim | Status |
|---|---|
| Firefox patched in C++ and rebuilt | **Verified (A)** — 104 files across `gfx`, `dom`, `netwerk`, `js/src` at the `stealth/150` tag pair; `stealth/151` has changed 150 further files between `d5457fa` and `a3819a7` |
| Fingerprint set in the engine, no JS shims on the page | **Consistent with the diff (A)** — changes are in C++ engine paths, not content scripts. The client also runs a page-side script, `invisible_core/juggler/injected.js`, in the utility world for selectors and actionability, with six marked changes |
| Driven by stock Playwright | **No longer accurate (A)** — true of `0.7.0`; at `0.35.3` the wrapper ships a modified vendored client (`_pw/`), no longer depends on `playwright`, and drives Firefox through a Python Juggler server ([The client](#the-client-vendored-playwright-and-an-in-process-juggler-server)). Juggler itself lives in the browser, as it must |
| "Playwright's API, sync and async, with no code changes" (`README.md:47`) | **API-compatible with named exclusions (A)** — tracing, HAR, CDP, `APIRequestContext` and others refuse by name (`_juggler/perimeter.py`); the returned classes are the vendored copy's, not those of an installed `playwright` |
| Same seed reproduces the same machine | **Not verified (D)** — no run was performed |
| Test harness is public and reproducible | **Verified present (A)** — 129 test files (per `scripts/codemetrics.py`), 9 CI workflows; CreepJS, BotD, FingerprintJS, fpscanner, Sannysoft, BrowserLeaks and reCAPTCHA are each referenced under `tests/` (1 to 7 files each), with offline copies of BotD, CreepJS, FingerprintJS and fpscanner in `tests/vendor/` |
| Detector-suite results in the README | **Tier B** — author-run, not reproduced here (e.g. the "5/5 detection suites passed" image, `README.md:14`) |
| Anti-bot service coverage | **Not claimed as pass rates** — the README names reCAPTCHA, hCaptcha and Cloudflare Turnstile as scorers and links explainer articles per vendor, with no pass-rate table |

Declining to publish WAF pass rates while publishing detector results is the same posture
[Clearcote](./clearcote.md) takes.

---

## Comparison

Against the other engine-level Firefox and Chromium entries:

| | invisible_playwright | Camoufox | Clearcote | CloakBrowser |
|---|---|---|---|---|
| Engine | Firefox 151 fork | Firefox 152 fork | Chromium 150 (ungoogled) | Chromium 152 (Pro) |
| Spoofing level | C++ engine | C++ engine | C++ engine | C++ engine |
| Engine source published | **Yes** — full fork | Yes | Yes | **No** |
| Patch readability | tree diff, no series | 44 `.patch` files | 37 in `patches/series` | n/a |
| Client | **vendored, modified Playwright Python client** + in-process Juggler server | own launcher | Playwright/Puppeteer SDK | Playwright/Puppeteer SDK |
| Launch telemetry | **yes, on by default** | none found | none found | none found |
| Binary checksum verified in code | Yes — fresh download against the sealed digest; cached engine: identity check | Yes | Yes (+ GPG) | Yes (Ed25519) |
| Fingerprint rotation | per-seed | BrowserForge statistical | per-seed / real-profile import | per-seed |

It is the **only tool in this comparison whose browser makes an unsolicited network
request at startup by default**. Of the two Firefox entries, Camoufox ships its own
launcher while invisible_playwright keeps the Playwright API shape on a vendored copy of the
client.

---

## Applicability

**Suited to:** Playwright codebases that want engine-level Firefox fingerprinting without
adopting a bespoke launcher API — the README describes a two-line switch from
`playwright.sync_api`, with named exclusions (tracing, HAR, CDP, `APIRequestContext`).
Also to reviewers who want to read the actual engine changes, provided they are willing
to clone a multi-gigabyte tree.

**Constraints:** Firefox only, so targets that probe SpiderMonkey engine behaviour
identify the browser family regardless of configuration — the same structural limit
Camoufox documents. Windows x86_64 and Linux x86_64/arm64 only; macOS support ended with
wrapper `0.7.3`. Eight contributors. The engine fork is large and awkward to audit, the
shipping line's diff exceeded what GitHub would render (2026-08-14), and the wrapper now
carries a modified copy of Playwright's client rather than depending on it. The launch ping
to `github.com` is on by default; see [Launch telemetry](#launch-telemetry).

**Opting out of the launch ping:**

```python
from invisible_playwright import InvisiblePlaywright

with InvisiblePlaywright(extra_prefs={"invisible_firefox.usage_ping.enabled": False}) as browser:
    ...
```

`extra_prefs` is a constructor argument of `InvisiblePlaywright` (`launcher.py:107`).

---

*Analysis conducted for educational purposes against the source at the commits above,
read in an isolated container — see [METHODOLOGY.md](METHODOLOGY.md#source-handling).
Nothing was installed, built, or executed. Use responsibly.*
