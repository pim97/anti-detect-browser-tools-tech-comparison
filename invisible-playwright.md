# invisible_playwright - Technical Analysis

> **Tool Type:** Custom Firefox Build (Anti-Detect Browser) driven through a vendored, modified copy of Playwright's Python client
> **Repository:** [github.com/oss-invisible/playwright](https://github.com/oss-invisible/playwright) (wrapper) · [oss-invisible/core](https://github.com/oss-invisible/core) (config, download, Juggler client) · [oss-invisible/firefox_antidetect_patch](https://github.com/oss-invisible/firefox_antidetect_patch) (the engine). All three were under `feder-cr` until wrapper 0.51.1 (2026-11-13; `CHANGELOG.md:195`, which says the old addresses redirect); the package URLs name the new organisation (wrapper `pyproject.toml:188-193`, core `pyproject.toml:75-78`). The sandbox clones were refreshed through the old `feder-cr` addresses.
> **Approach:** Firefox patched in C++ and rebuilt; fingerprint produced by the engine rather than injected into the page. Since wrapper `0.7.3` the Python client is a **modified, vendored copy of Playwright** (`invisible_playwright._pw`); since `0.8.0` there is no Node driver: a Python server in `_juggler/` answers the client and drives the browser over Juggler. Since `0.48.0` the same server can also be served on a WebSocket to stock Playwright clients (`launch_server()`). See [The client](#the-client-vendored-playwright-and-an-in-process-juggler-server).
> **Verified in source (Tier A):** the engine repository is **no longer a Firefox tree**. Its history was rewritten: the full-tree branches that shipped through 2026-10 (`stealth/150`, `stealth/151`; sealed commit `a3819a7` for `firefox-41`) no longer exist upstream, and GitHub reports no common ancestor between `a3819a7` and the current tags. The current history starts at `eefcdbb` (2026-10-27, "The 157 engine as a patch series, one folder per feature") and holds a **patch series**: 79 feature folders under `automation/`, `fingerprint/`, `network/`, `platform/` and `stillborn/`, each with a `FEATURE.md` and `MANIFEST.json`, 75 with a `hooks.patch` against Mozilla's files, 665 added files under `*/src/`, plus `SERIES`, `UPSTREAM.json` and `tools/engine.py` (`git ls-tree -r` at `9110d5d`, tag `firefox-67`). Core 67.79.0 seals tag `firefox-67`, Firefox **159.0** (`seal.json`: `series_commit` `b6d658d`, `source_commit` `014be51`; the series' own `UPSTREAM.json` names `FIREFOX_159_0_RELEASE`). The series was read from a full shallow clone of `firefox-67`; series paths below are relative to its root and are **Tier A** for what the patch files say, but no tree was rebuilt from them. Commit messages are cited as **Tier B**. Statements citing `a3819a7`, `fec80c8`, `d5457fa` or the `stealth-*/v150.0.1` tags describe the pre-rewrite engine; those objects remain readable in the sandbox's earlier clone.
> **Anti-bot service claims:** none as pass rates. The project publishes detector-suite results (CreepJS, BotD, FingerprintJS, fpscanner, Sannysoft, BrowserLeaks, reCAPTCHA scoring) rather than WAF pass rates — **Tier B** for the results, **Tier D** for commercial-service coverage. Its README names reCAPTCHA, hCaptcha and Cloudflare Turnstile as the scorers of the "two questions" it says it answers (`README.md:28`) and links per-vendor explainer articles.
> **Maintenance:** wrapper `0.57.1` (2026-11-20), pinning `invisible-core` `67.79.0` (2026-11-20); engine release `firefox-67` (Firefox 159.0, merge `9110d5d` of 2026-11-19). GitHub lists engine releases `firefox-63` … `firefox-67` (2026-11-12 … 2026-11-19). The engine moved from Firefox 151.0 (through at least `firefox-52`, `CHANGELOG.md:660-661`) to 159.0 with `firefox-54` (2026-10-31, `CHANGELOG.md:611-612`); 157 appears only as the base the series was first exported from. 2,610 stars (3,135 on 2026-10-13), 279 forks, 8 contributors, 6 open issues, last push 2026-11-20 (GitHub API, 2026-11-20). The wrapper and the core declare `MIT AND Apache-2.0` (wrapper `pyproject.toml:30`, core `pyproject.toml:17-22`; GitHub reports MIT); the core wheel also ships two Firefox branding archives under MPL-2.0 (`src/invisible_core/branding/{official,unofficial}/`, the `official` set's `LICENSE` withholding Mozilla trademark rights), which the licence field and `THIRD_PARTY.md` do not name; `official` is the default (`_fpforge/profile.py:739`). The engine is MPL-2.0 (wrapper `README.md:365`). Both READMEs now open with a sponsored affiliate link to a residential-proxy provider (wrapper `README.md:20-21`, core `README.md:4-5`); no code references it.
> **Verified:** 2026-11-20 against `invisible_playwright` @ `d1bfea3` (0.57.1), `invisible_core` @ `191f0fa` (v67.79.0), `firefox_antidetect_patch` @ `9110d5d` (tag `firefox-67`; full shallow clone of the tag, plus a blobless fetch of its 268-commit history). The wrapper and core clones are shallow (depth 50); both previous-pass commits are inside them, and nothing on this page infers deleted history from either. Previous pass 2026-10-13: `91ea73b` (0.35.3), `415bbd8` (v41.39.0), `a3819a7` (`stealth/151`, tag `firefox-41`).

> [!IMPORTANT]
> **The shipped browser contacts GitHub once on every launch, and since engine `firefox-64`
> it cannot be turned off.** The engine reads no pref for it any more; the opt-out this page
> used to document no longer exists. The wrapper README now describes the request. Details
> in [Launch telemetry](#launch-telemetry).

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

**Yes, and since 2026-10-27 in a readable form: the engine repository is a per-feature
patch series against a Mozilla release tag.** The previous revisions of this page described
a full Firefox fork whose stealth work sat on side branches and could only be audited by
cloning a multi-gigabyte tree; that repository history no longer exists upstream.

| Check | Result |
|---|---|
| Engine source public | **Yes** — `main` and the release tags carry the series (commit `984b71976e`, 2026-11-10: "main is the released firefox-59 series again"). Layout at `firefox-67`: 79 folders (14 `automation/`, 42 `fingerprint/`, 5 `network/`, 14 `platform/`, 4 `stillborn/`); 934 files, of which 665 under `src/` (203 of them with `test` in the path) (**A**, `git ls-tree`) |
| Base | Mozilla's tag `FIREFOX_159_0_RELEASE` of `mozilla-firefox/firefox` (`UPSTREAM.json:2-3`, **A**); 79 folders listed in `SERIES`. First exported against `FIREFOX_157_0_1_RELEASE` (`eefcdbb`), moved to 159.0 in `255271b52d` (2026-10-30) (**B**) |
| Series reproduces the shipped tree | Claimed, not checked: each export commit reports `tools/engine.py verify` "identical" (e.g. `eefcdbb`: identical to `stealth/157`, "70 folders, 208 modified and 233 added files") (**B**). `UPSTREAM.json:4-6` records the export as `source_branch` `port/159-phase4`, `exported_from` `3cecd62`, `exported_tree` `22f5196`; the seal names a different `source_commit`, `014be51`. Neither commit is in the sandbox clones, and whether `UPSTREAM.json` is simply stale was not settled (**D**). Remote branches on 2026-11-20: `main`, `firefox-62`, `port-159`, `phase4`, `layers`, `latitude/*`, `theta/*` |
| Mozilla's files vs the project's own | Logic moved out of Mozilla files into `Stealth*` files; Mozilla files keep short hooks marked `STEALTH-HOOK(<folder>)` (`3a5cf14628`, 2026-10-29: "8719 of our lines in Mozilla files at the start of the day, 1592 now"; `a40cf441d4`, 2026-11-11, reports 2,182 such lines and "files 288 -> 330") (**B**) |
| Relationship to `mozilla-firefox/firefox` | GitHub still marks the repository as a fork of `mozilla-firefox/firefox` (API, 2026-11-20), but the rewritten history contains no Mozilla commit: `eefcdbb` has no parents (API, 2026-11-20) |
| Built binaries published | Windows x86_64 `.zip` and Linux x86_64 `.tar.gz` (`seal.json`: `firefox-159.0-stealth-win-x86_64.zip`, `firefox-159.0-stealth-linux-x86_64.tar.gz`). Linux arm64 ended with `firefox-55` (wrapper `CHANGELOG.md:539-542`, `README.md:66`; engine `e8f0cb8a43`, "two legs, Linux and Windows x86_64"); macOS ended 2026-08-26. The publish workflow still writes and uploads `checksums.txt` (`sha256sum firefox-*-stealth-*`, `platform/ci/src/.github/workflows/publish.yml:98-103`, `:168`) |
| Build infrastructure | x86_64 legs compile on Latitude.sh servers (a Theta node before that); gates and tests stay on GitHub (`1e138d3cb1`, 2026-11-04; `2df8d99cd8`, 2026-11-03) (**B**) |

### Caveats

**1. The folders describe themselves unevenly.** Many `FEATURE.md` files still read
"TODO: one paragraph" and carry inventory notes from the 2026-10-27 export; some are stale.
`platform/launch-counter/FEATURE.md:4` and its `MANIFEST.json:17-18`, `:27` still list the two
`usage_ping` prefs that the code no longer reads (below), and the engine README patch still
says "Current release: **firefox-18**, built from Firefox 151.0. Branch **`stealth/151`** is
the source of truth" (`platform/repo/hooks.patch:113-115`). Read the `src/` files and
`hooks.patch`, not the descriptions.

**2. The binary's source is named by a commit outside the series.** The seal pins both a
`series_commit` (`b6d658d`, in the series' history) and a `source_commit` (`014be51`), and
`UPSTREAM.json` names a third commit (`3cecd62`). An auditor rebuilding from the series has
to trust the project's `verify` step, or obtain the exported tree, to tie the series to the
shipped build.

**3. Earlier caveats, now historical.** Up to `firefox-43` the shipping work lived on
`stealth/151` of a full Firefox fork; `main` carried none of it, GitHub returned HTTP 422 on
the shipping comparison (2026-08-14), and the titled companion series
`feder-cr/firefox-stealth` returned HTTP 404 (2026-08-14 and 2026-10-13). The only diffable
pair was `stealth-base/v150.0.1` → `stealth-head/v150.0.1`, **104 files, +14,279 / −59**
(re-derived 2026-10-13); those two tags remain in the sandbox clone, and whether they still
exist upstream was not checked. Between `d5457fa` and `a3819a7` `stealth/151` changed a
further 150 files. These figures describe Firefox 150/151-era engines and are not a size
measure of the current series.

**Net:** *auditable per feature, with the caveat that the series-to-binary link is a
claim.* That is a large change from the previous revisions' "auditable in principle,
considerably harder in practice", and it puts the engine closer to
[Camoufox](./camoufox.md) and [Clearcote](./clearcote.md), which publish patch files, than
to [CloakBrowser](./cloakbrowser.md), which publishes no engine source.

---

## Launch telemetry

**The patched browser issues one HTTPS GET to GitHub every time it starts, and since
engine `firefox-64` (core 64.69.0, 2026-11-14) nothing in the browser, the core or the
wrapper turns it off.**

### Current state (`firefox-67`, core 67.79.0, wrapper 0.57.1)

| Property | Finding | Tier |
|---|---|:--:|
| **Where the code is** | `platform/launch-counter/`: one hook in Mozilla's `BrowserGlue.sys.mjs`, `try { lazy.StealthLaunchCounter.fire(); } catch (e) {}` as the first statement of `_beforeUIStartup` (`hooks.patch:17-18`), and the module `src/browser/components/StealthLaunchCounter.sys.mjs` (28 lines) | A |
| **No pref, no opt-out** | The module reads no pref. Its header: "It is MANDATORY: no preference gates it and no preference moves it. The address is the constant below, the same in every binary" (`StealthLaunchCounter.sys.mjs:11-12`); the URL is a `const` (`:15-16`). No file in the series names `usage_ping` except stale descriptions (`FEATURE.md:4`, `MANIFEST.json:17-18`, `:27`, `tools/inventory.json`, `platform/prefs/FEATURE.md:4`): no pref declaration, no reader. The engine's own test sets `usage_ping.enabled = false` and `usage_ping.url` to another address and asserts one request still goes to the fixed address (`src/browser/components/tests/unit/test_stealth_launch_counter.js:62-78`), and that the module source contains no `usage_ping` (`:93`). The core's test says the same from its side (`invisible_core/tests/test_the_core_declares_no_launch_counter_pref.py:1-5`, `:15-19`); wrapper `CHANGELOG.md:2442-2443`: "the counter cannot be turned off or redirected" | A |
| **What is transmitted** | `fetch("https://github.com/oss-invisible/firefox_antidetect_patch/releases/download/usage-counter/launch.txt", { method: "GET", credentials: "omit", cache: "no-store" })`, rejection and exceptions swallowed (`StealthLaunchCounter.sys.mjs:15-26`): no payload, no query string, no cookies, a standard Firefox User-Agent. The engine test checks GET, `SEC_COOKIES_OMIT` and `FETCH_CACHE_MODE_NO_STORE` (`test_stealth_launch_counter.js:44-60`). GitHub's `download_count` of that asset is the counter (`scripts/launch_counters.py:12-15`, `:43-45` in the wrapper), shown as the launches badge (`README.md:11`) | A |
| **When** | Once per browser process, from `_beforeUIStartup`, which the module says "runs at final-ui-startup: before any tab is created" (`StealthLaunchCounter.sys.mjs:5-7`) | A |
| **Does it respect the proxy?** | **By the source, yes when the browser is driven by the package; not run.** When Firefox starts with `-juggler-pipe`, Juggler registers a proxy channel filter at `command-line-startup` (`automation/juggler/src/juggler/components/Juggler.js:81-93`), before `final-ui-startup`. Every channel that asks the proxy service (http/https included) is stored unanswered until `Browser.setBrowserProxy` or `Browser.setNoBrowserProxy` arrives (`network/doh/src/juggler/EarlyProxyHold.js:31-50`, `:78-85`; `NetworkObserver.js:712-734`), and the core sends one of the two as its first command (`invisible_core/juggler/connection.py:1545-1551`). A held channel is then answered with the context proxy, or, for a request with no context such as this one, the browser proxy (`TargetRegistry.js:521-550`; `NetworkObserver.js:769-791`). So the counter leaves through the session proxy when there is one, and directly when there is none. A binary started without `-juggler-pipe` (by hand, or by another driver) has no hold, and the request goes out on the host's configuration | A (source), D (run) |
| **Disclosed** | **Yes**: wrapper README "Launch counter" section (`README.md:223-225`); engine README "Anonymous launch counter" section, which says "It is not optional … nothing in the package or in a setting skips it or moves it" (`platform/repo/hooks.patch:147-169`). The wrapper README and its 0.51.0 entry (`CHANGELOG.md:239-241`) also say the launcher and server *refuse* the two `invisible_firefox.usage_ping.*` prefs in `extra_prefs`. No code does: no file under the wrapper's or the core's `src/` names `usage_ping`, and the wrapper test asserts the server has no refusal (`tests/test_the_server_says_nothing_about_the_launch_counter.py:1-6`, `:34-35`). A caller's `usage_ping` prefs pass through as ordinary prefs the engine does not read | A |

### History

| When | State |
|---|---|
| 2026-05-23 (`2850813ea8`) to `d5457fa` (2026-08-14) | Compiled literal, `https://github.com/feder-cr/invisible_firefox/releases/download/usage-counter/launch.txt` (`BrowserGlue.sys.mjs:404`), gated by `invisible_firefox.usage_ping.enabled` (default `true`) |
| wrapper 0.12.2 / core 27.18.0 (2026-09-05) → `a3819a7` | Address read from `invisible_firefox.usage_ping.url`, which the core declared for every session (`prefs.py:361-362` at `415bbd8`); engine default on `firefox_antidetect_patch`, literal fallback on `invisible_playwright`. Opt-out: `extra_prefs={"invisible_firefox.usage_ping.enabled": False}` |
| wrapper 0.51.0 (2026-11-12) | The wrapper refuses the two prefs in `extra_prefs` (`CHANGELOG.md:239-241`) |
| core 64.69.0 / engine `firefox-64` → now | The engine reads no pref; the core declares none; the wrapper neither refuses nor forwards (see above) |

The `firefox-67` code (`platform/launch-counter/src/browser/components/StealthLaunchCounter.sys.mjs:15-28`):

```javascript
const USAGE_PING_URL =
  "https://github.com/oss-invisible/firefox_antidetect_patch/releases/download/usage-counter/launch.txt";

export const StealthLaunchCounter = {
  fire() {
    try {
      fetch(USAGE_PING_URL, {
        method: "GET",
        credentials: "omit",
        cache: "no-store",
      }).catch(() => {});
    } catch (e) {}
  },
};
```

The `a3819a7` code, for comparison (pre-rewrite engine):

```javascript
// browser/components/BrowserGlue.sys.mjs:387-423  (stealth/151 @ a3819a7; comments abridged)
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

It ran from `_beforeUIStartup` (`:386`), called from the `final-ui-startup` case
(`:194-195`); the pref default was `firefox.js:3683`. The engine README of that revision
documented it as an "Anonymous launch counter" (`README.md:52-88` at `a3819a7`).

**What the ping is and is not.** It is a counter, not a profile: no identifier, no
payload, no cookies. What changed is control: it was disclosed but opt-out until engine
`firefox-63`, and it is now disclosed and mandatory. In a session the package drives, the
source routes it through the session proxy; that was read, not run.

---

## What the patches actually change

### The current series (`firefox-67`), by folder

Folder and file counts from `git ls-tree` (**A**). Where a series file is cited below it was
read (**A**); otherwise behaviour is from commit messages and the wrapper changelog (**B**).

| Area | Folders | Files | Layer |
|------|--------:|------:|-------|
| `automation/` (Juggler and its pipe, input, navigation, downloads, file chooser, closed shadow roots, CSP bypass, hybrid X-rays, window size) | 14 | 205 (146 in `automation/juggler`) | automation protocol — Playwright's Firefox transport |
| `fingerprint/` (fonts, screen and window, locale and time, canvas, WebGL, WebGPU, JS surface, media, audio, hardware, geolocation, input timing, WebRTC network) | 42 | 437 (234 in `fingerprint/fonts`, 121 of them under `fonts/bundle/src/browser/fonts/`) | 1–2 — JS engine, navigator, graphics, fonts, audio |
| `network/` (`doh`, `proxy`, `proxy-udp`, `socks`, `ipv6-literal`) | 5 | 70 | 4 — DNS, proxy, WebRTC UDP |
| `platform/` (prefs, CI, release, launch counter, hidden desktop, build config and tools, backports) | 14 | 165 | build, defaults, telemetry |
| `stillborn/` (`api-keys`, `intermediates`, `telemetry`, `updater`) | 4 | 24 | Mozilla services kept from acting or redirected |

Changes since the previous pass that matter to the claims on this page (engine `firefox-42`
to `firefox-67`; **B** unless a series, core or wrapper file is cited):

- **2D canvas is no longer noised.** Since `firefox-52` "a 2D canvas, on the page or
  offscreen, now reads back exactly as it was drawn … the canvas noise is applied to WebGL
  and WebGPU readback only" (`CHANGELOG.md:660-663`). The series agrees: "A 2D canvas is
  never projected (from firefox-52): it reads back as drawn, as on retail"
  (`platform/prefs/src/modules/libpref/init/StealthPrefList.yaml:377-380`); "A 2D or
  bitmaprenderer canvas is a source as it was drawn … the canvas noise is a WebGL/WebGPU
  readback only" (`fingerprint/canvas/noise-projection/src/dom/html/StealthCanvasSnapshot.cpp:31-32`);
  no `hooks.patch` in the series touches `CanvasRenderingContext2D.cpp`. The noise hooks sit
  in `ClientWebGLContext.h`, `dom/webgpu/CanvasContext.cpp`, `OffscreenCanvas*.cpp`,
  `HTMLCanvasElement.cpp` and `gfx/2d/DrawTargetRecording.cpp`
  (`fingerprint/canvas/noise-projection/hooks.patch`) (**A**).
- **WebRTC UDP now uses the proxy.** The SOCKS5 UDP ASSOCIATE layer (now
  `network/proxy-udp/src/netwerk/socket/nsSOCKSUDPIOLayer.cpp`, with `StealthPcUdpProxy.cpp`)
  is in use since `firefox-63`: the core measures, through the proxy's relay, whether a
  SOCKS5 proxy's UDP leaves from its TCP exit and declares the verdict (`coherent`, `no`,
  `unmeasured`) in the `udp` field of `Browser.setBrowserProxy`; "The engine acts on
  `coherent` only" (`invisible_core/_udp_exit.py:1-20`, **A** for the core). Otherwise ICE
  gathers no server-reflexive candidate and HTTP/3 falls back to HTTP/2
  (`CHANGELOG.md:229-233`). The synthetic server-reflexive candidate of the earlier engine
  is gone: `9a1c8cadf7` removes `fingerprint/webrtc/ice-candidates` (`nr_stealth_bridge`,
  `StealthIceGathering`) and adds a declared interface list
  (`fingerprint/webrtc/declared-network`).
- **DNS goes over DoH through the proxy.** Behind a proxy the engine sets TRR mode 3 and the
  core declares the provider, `https://mozilla.cloudflare-dns.com/dns-query` with bootstrap
  address `162.159.61.4` (`invisible_core/prefs.py:453-467`, **A**); a SOCKS5 proxy receives
  addresses, not names (`CHANGELOG.md:234-235`). The core also sets
  `network.proxy.allow_bypass` and `network.proxy.failover_direct` to `false`
  (`_proxy.py:255`, `prefs.py:448`, **A**). The core no longer sets `socks_remote_dns`.
- **Per-context egress.** From `firefox-64` "a request a page causes now leaves in the
  context of that page, by that context's proxy and resolver" — TURN names, OCSP, Safe
  Browsing completions (`CHANGELOG.md:166-169`); an e2e suite with a direct-arrival witness
  exists (`tests/test_nothing_of_a_context_leaves_but_through_its_proxy_e2e.py`), not run here.
- **Intermediate certificates declared, not synced.** From `firefox-67` the engine never
  creates the `security-state/intermediates` collection and reads a list the core writes,
  named by `zoom.stealth.intermediates.file` (`stillborn/intermediates/FEATURE.md:4`, `:9-12`;
  `CHANGELOG.md:31-37`); the core downloads that list itself (see
  [Other network activity](#other-network-activity)).
- **Updater: the update check goes out again.** Since 2026-10-30 the updater is built as
  in a release and "the update check to aus5.mozilla.org goes out as official Firefox sends
  it: same timer, same URL, same headers"; from 2026-08-31 to 2026-10-30 it was not built
  (`stillborn/updater/FEATURE.md:13-18`, `:32-34`). `StealthUpdate.sys.mjs` then reports no
  update whatever the answer, refuses every download and refuses the Windows background-update
  task (`stillborn/updater/src/toolkit/mozapps/update/StealthUpdate.sys.mjs:29-36`, `:49-51`,
  `:62-64`; hooked in `UpdateService.sys.mjs` and `BackgroundUpdate.sys.mjs`,
  `stillborn/updater/hooks.patch`); the build uses the release update channel and MAR channel
  (`platform/build-config/src/.mozconfig:84`, `:207-208`) (**A**). The core's comment that
  "OUR engine has no updater at all" (`invisible_core/prefs.py:857-860`) is stale; the core
  still sets `app.update.auto` to false (`prefs.py:897`).
- **Identity.** Every identity reports Firefox 159's User-Agent, WebGL extensions and
  branding (`CHANGELOG.md:611-613`); a GPU persona stands for one real Windows 11 GPU and
  answers Firefox's blocklist as Firefox 159 for Windows does (0.45.0); the exposed font set
  is 67 families (0.43.0); WebGPU adapters are declared (`fingerprint/webgpu/*`).

### Pre-rewrite engine, read at the code level (`stealth/150` tag pair and `a3819a7`)

The rest of this section is the 2026-10-13 reading of engines up to `firefox-41`, kept for
the history. It was not re-derived against the series; where the series supersedes a point,
the point says so.

Areas touched by the 104-file `stealth-base → stealth-head` diff (Firefox 150.0.1):

| Area | Files | Layer |
|------|------:|-------|
| `juggler/**` (screencast, content, protocol, pipe, components) | 41 | automation protocol |
| `netwerk/**` (socket, http, base) | 9 | 4 — network |
| `gfx/thebes` | 6 | 2 — fonts, graphics |
| `dom/media/webrtc/transport` (incl. `nICEr/src/ice`) | 7 | 4 — WebRTC IP |
| `dom/base` | 5 | 2 — navigator surfaces |
| `dom/media/webaudio` | 4 | 2 — audio fingerprint |
| `js/src/vm`, `js/src/debugger` | 4 | 1 — JS engine / debugger tells |
| `dom/media/webspeech/synth` | 2 | 2 — speech voices |
| `modules/libpref/init` | 2 | defaults (includes the usage-ping pref) |

**1. A C++ fingerprint surface driven by static prefs.** At `stealth-head/v150.0.1`,
`StaticPrefList.yaml` added 24 `zoom.stealth.*` entries (44 at `fec80c8`, 46 at
`a3819a7`), read inside the engine — the same seeded-config pattern as Camoufox's
`MaskConfig`. In the series those prefs moved to their own file,
`platform/prefs/src/modules/libpref/init/StealthPrefList.yaml` (with `StealthPrefs.js`),
and `StaticPrefList.yaml` is "Mozilla's again" except for hooks (`3a5cf14628`). At
`firefox-67` that file declares **50** static `zoom.stealth.*` prefs (`- name:` entries in
`StealthPrefList.yaml`, 588 lines); a few more names are read at runtime without a static
declaration (e.g. `zoom.stealth.intermediates.file`,
`stillborn/intermediates/src/security/manager/ssl/stealth/StealthIntermediates.sys.mjs:35`;
`zoom.stealth.apikey.*`, `stillborn/api-keys`) (**A**). The core names 67 distinct
`zoom.stealth.*` keys (58 at `415bbd8`; a different measure).

**2. Canvas noise written against specific detector internals.** At `a3819a7`
`CanvasRenderingContext2D.cpp:2264-2338` applied ±1 on one channel for ~12.5% of pixels
before `toDataURL`/`getImageData`, skipping canvases below 64×64, the alpha channel and
zero-valued channels — the last explicitly to survive CreepJS's `clearRect` trap — with a
comment naming FP Pro's `tampering_ml` threshold; comments at `:2389-2407` said the actual
`tampering_ml` driver was `OfflineAudioContext` noise. **Superseded for 2D canvas** since
`firefox-52` (above).

**3. SOCKS5 UDP ASSOCIATE in the network stack.** At `a3819a7` `nsSOCKSUDPIOLayer.cpp`
(+423 lines) was present but hooked in only when `network.proxy.socks_remote_udp` was true
(`netwerk/base/nsUDPSocket.cpp:614-624`), which the core did not set
(`_proxy.py:278-290` at `415bbd8`, `UDP_GOES_THROUGH_SOCKS = False`); behind a proxy the
engine synthesised a server-reflexive candidate from the exit IP. **Superseded** since
`firefox-63` (above); `UDP_GOES_THROUGH_SOCKS` and the exit-capability probe
(`_capability.py`) are gone from the core.

Fonts at `a3819a7` came from a bundled set (`browser/fonts/`, 128 files) with a generated
metrics manifest (`gfx/thebes/StealthBundleFontList.cpp`); the series keeps a bundle under
`fingerprint/fonts/bundle/` (121 files under `src/browser/fonts/`).

> [!NOTE]
> **The Juggler files are the part of the engine a Playwright-style client needs.**
> Playwright drives Firefox over Juggler, which is not part of upstream Firefox. In the
> series it is `automation/juggler` (146 files). That is separate from the *client*, which
> is no longer a stock `playwright` package: see
> [The client](#the-client-vendored-playwright-and-an-in-process-juggler-server).

**Architecture:** the same seeded-config-in-C++ pattern as Camoufox. The claim "the
fingerprint is produced by the engine instead of injected into the page" is consistent
with the pre-rewrite code and with the series layout; the client additionally runs a
page-side script (`invisible_core/juggler/injected.js`) in Firefox's utility world for
selectors and actionability, and plans pointer motion in Python (see below).

---

## The client: vendored Playwright and an in-process Juggler server

The first revision of this page described the client as an unmodified `playwright`
package. That was accurate at wrapper `0.7.0` and is not accurate at `0.57.1`.

| Property | Finding | Tier |
|---|---|:--:|
| Dependencies | `invisible_core==67.79.0`, `psutil>=5.9`, `pyee>=13,<14`, `greenlet>=3.1.1,<4.0.0`. **`playwright` is not a runtime dependency** (`pyproject.toml:46-117`; the comment at `:73-78` says reintroducing it would not visibly break anything); it appears only in the `dev` extra, pinned `playwright==1.61.0` (`:121`). A `remote` extra adds `websockets>=13` for `launch_server()` (`:120`) | **A** |
| What is vendored | Playwright's Python client 1.61.0 as `invisible_playwright._pw` (68 files), Apache-2.0 (`_pw/LICENSE`). `THIRD_PARTY_FORK.md:14`, `_pw/README.md:3` and `_pw/_repo_version.py` now all say 1.61.0 (at 0.35.3 `THIRD_PARTY_FORK.md` said 1.61.1). Imports are rewritten to the `invisible_playwright._pw` namespace (`THIRD_PARTY_FORK.md:16-18`, `_pw/README.md:12-16`). `pyproject.toml:30` declares `MIT AND Apache-2.0` | **A** |
| What was changed in it | `MODIFIED by invisible_playwright` markers: `_pw/_impl/_playwright.py:44` (chromium and webkit refused), `_impl/_browser.py:80`, `:127`, `:240` and `_impl/_browser_context.py:94`, `:394` (page numbering), `_impl/_assertions.py:30`, `:110` (new since 0.35.3), `{sync,async}_api/_context_manager.py` (`:60`, `:31`; the in-process transport), `{sync,async}_api/_generated.py` (chromium/webkit accessors raise). The `_impl/_connection.py:485` marker of 0.35.3 is gone. `_pw/README.md:18-30` lists the modified files without `_assertions.py` and says "Everything else is upstream, byte for byte"; `_impl/_connection.py` and `_impl/_dialog.py` changed between the two passes without markers, and were not compared with upstream 1.61.0 (**D** for that statement) | **A** |
| Node driver | **Removed** in `0.8.0` (2026-08-30; `CHANGELOG.md:2700-2708`; `THIRD_PARTY_FORK.md:20` dates it 2026-08-28). A first install downloads the browser only | **A** |
| What replaces it | The wrapper's `_juggler/` answers the Playwright protocol: `server.py` (6,426 lines, was 4,455), `dispatcher.py`, `transport.py`, `_marshal.py`, `perimeter.py`, and since 0.35.3 `pointer.py`, `remote.py`, `wire.py`, `variants.py`, `dialogs.py`, `_bindings.py`, `_reaped.py`, `_threads.py`, `memprobe.py` (10,286 lines in all). The Juggler client lives in the core, `invisible_core.juggler`: `connection.py` (JSON delimited by a zero byte; fd 3/4 on POSIX, inheritable handles on Windows, `:6-13`), `protocol.py` (generated from the shipped `Protocol.js`; **82 commands, 35 events**, `:5`, was 77/35), `actions.py`, `_motion.py`, `_stroke.py`, `keyboard.py`, `keylayouts_windows.py` (11,029 generated lines), `lifecycle.py`, `instance.py`, `injected.py`, `injected.js` (8,121 lines, unchanged; six marked changes at `:6489`, `:6674`, `:7214`, `:7241`, `:7419`, `:7697`). The core's `THIRD_PARTY.md` still records the earlier per-wrapper copies | **A** |
| Served mode | `launch_server()` (0.48.0, `CHANGELOG.md:411-414`) serves one browser on a WebSocket to any Playwright client; identity, prefs and env stay the server's; "There is no version check, no 428" (`_juggler/remote.py:1-40`). Default host `127.0.0.1`, and a wildcard host is rewritten to loopback (`remote.py:78`, `:285-286`) | **A** |
| Out of scope (refused by name) | `APIRequestContext`, tracing and trace artifacts, HAR, CDP sessions and `connectOverCDP`, WebAuthn, PDF, clock, the recorder, video overlays (`_juggler/perimeter.py:25-119`). `set_offline` and downloads work since 0.44.0 (`CHANGELOG.md:618-624`); `expose_function`/`expose_binding` since 0.52.1. README: "tracing, HAR, CDP, the API request context" (`README.md:74`) | **A** |
| Pointer motion | `humanize=True` is the default (`launcher.py:97`). The path is now drawn by the **server** (`_juggler/pointer.py`, 834 lines) for every client, in-process or served; `_cursor.py` (301 lines, was 1,482) only decides who draws and the seed (`_cursor.py:1-12`). The planner is `invisible_core.juggler._motion`; since 0.53.1 a stroke is sent as one timeline (`Actions.walk`). The browser's own motion fallback was removed in 0.55.0 (`CHANGELOG.md:57`). `show_cursor` draws an overlay in the browser's chrome window, on by default (`launcher.py:169-180`, `invisible_core/prefs.py:2159`). `prep_recaptcha=True` (opt-in; ignored with `profile_dir`, `launcher.py:234`) seeds cookies from the persona (`persona_cookies`, `invisible_core/_cookies.py:292`, called at `launcher.py:498`) | **A** |
| Version coupling | `_engine.assert_playwright_range()` (`_engine.py:67`) compares the **vendored** client's version with the seal's range (1.55.0 – 1.61.0); `assert_wire_version()` (`:37`) compares the version the running engine reports with the seal | **A** |

The wrapper's README still says the returned object "is a `playwright.sync_api.Browser`"
(`README.md:106`); `launcher.py:8` imports `Browser` from `invisible_playwright._pw.sync_api`,
the vendored copy. The nine re-export shims (`_fpforge`, `_webgl_personas`, `_geo`,
`_headless`, `_proxy`, `config`, `constants`, `download`, `prefs`) and `_reaper` were
removed in 0.55.0 (`CHANGELOG.md:54-56`); the fingerprint sampler and GPU persona pool are
imported from `invisible_core` directly.

---

## Supply chain

| Property | Finding | Tier |
|---|---|:--:|
| Binary origin | `https://github.com/oss-invisible/firefox_antidetect_patch/releases/download/{tag}/{asset}` (`invisible_core/constants.py:132-134`) — same organisation as the source, public. Pinned tag `firefox-67` (`seal.json`). Old releases were removed on purpose (`download.py:208-231`) | **A** |
| Checksums published | `checksums.txt` (`sha256sum firefox-*-stealth-*`) written and uploaded by the engine's publish workflow (`platform/ci/src/.github/workflows/publish.yml:98-103`, `:168`); the core does not read it | **A** |
| Checksums verified in code | **Yes — against the seal rather than a release file.** The archive's SHA-256 (`_sha256_file`, `download.py:507`) is compared with the per-asset digest in `seal.json`, which ships inside the `invisible-core` wheel (`download.py:699-705`). The unused `_parse_checksums` of 0.35.3 is gone | **A** |
| Cached binaries re-checked | **Partly.** A cache hit runs `verify_engine` (`download.py:671-672`; `seal.py:641`): `application.ini`/`platform.ini` Version and BuildID against the sealed leg plus the stealth markers in the Juggler entries (`seal.py:555-615`) — an identity check, not a re-hash. The `omni.ja` digest is compared only when adopting an unstamped tree, and only if the tree has an `omni.ja` (`download.py:546-559`). The seal now carries an `omni_sha256` for both legs; the code still says the Linux archives ship no `omni.ja` (`seal.py:21`) | **A** |
| Dependency pinning | `invisible_core==67.79.0`, an exact `==` specifier (`pyproject.toml:72`), with an import-time assertion in `_pin.py`. The literal moves on every engine release (`pyproject.toml:61-63`) | **A** |
| Dangerous constructs | **None found** in either package's Python source, including the vendored `_pw/`: no `eval`/`exec`, no `pickle.load`, no `shell=True`, no `verify=False` (`scripts/codemetrics.py`, 2026-11-20). The page-side `invisible_core/juggler/injected.js` calls `eval` at `:6521`, `:6668`, `:6697` and `:6987` as part of Playwright's expression evaluation | **A** |
| Bundled third-party assets | Firefox branding archives (`src/invisible_core/branding/`, from `FIREFOX_159_0_RELEASE` per `SOURCE.json`), MPL-2.0, served to pages through `zoom.stealth.branding.archive` (`_fpforge/profile.py:711-720`); not named in the licence metadata | **A** |

The pinning rationale is documented in `pyproject.toml:51-71`: the maintainers moved off a
git direct reference because `pip check` cannot detect a violated direct reference.

---

## Other network activity

Every external host referenced in the two installed packages' Python source (the wrapper
references none; the core's are below). The browser's launch request is covered under
[Launch telemetry](#launch-telemetry):

| Host | Purpose | Trigger |
|------|---------|---------|
| `github.com` | engine binary from `oss-invisible/firefox_antidetect_patch` releases (`constants.py:132-134`); GeoIP database from `daijro/geoip-all-in-one` (`constants.py:150-152`, `_geoip_db.py:113-114`) | engine: first run / version change; GeoIP: checked at most once a day (`_geoip_db.py:46`) |
| `api.github.com` | release index, asked once per engine download even without a token, then the direct link (`download.py:118-152`); with retries when `STEALTHFOX_GITHUB_TOKEN` or `GITHUB_TOKEN` is set (`download.py:153-170`, `environment.py:35-36`); GeoIP latest-tag fallback (`_geoip_db.py:126`) | download path |
| `api.ipify.org`, `icanhazip.com`, `checkip.amazonaws.com` (`_geo.py:62-66`); `api6.ipify.org`, `ipv6.icanhazip.com` (`:71-74`) | public-IP echo for timezone and locale; through the proxy when one is set, from the host otherwise; the IPv6 echoes only after the IPv4 echo could not connect | **default launch** (`timezone=""`, `locale="auto"`, `launcher.py:98-99`); since 0.57.0 asked on every launch, not cached (`CHANGELOG.md:22`) |
| STUN `141.101.90.1:3478`, `162.159.207.1:3478` (IP literals, `_udp_exit.py:72`; overridable with `udp_stun_servers`) | UDP-exit measurement of a SOCKS5 proxy, sent through the proxy's UDP relay | launch with a SOCKS5 proxy, and every `new_context(proxy=...)` (`CHANGELOG.md:21`) |
| `firefox.settings.services.mozilla.com` (`constants.py:162`) | Mozilla's intermediate-certificate list, fetched by the core's Python with a plain `requests.get` and no proxy argument (`_intermediates.py:111-114`) | a launch on a cold cache, before the browser starts (`launch.py:83`, `_intermediates.py:18-19`); every `invisible-playwright fetch` (`cli.py:93`) |
| `mozilla.cloudflare-dns.com` (`prefs.py:466`, bootstrap `162.159.61.4`) | the browser's DoH resolver | behind a proxy only, through the proxy |
| `pypi.org` (`release.py:107`) | version checks in maintainer tooling | not the runtime path |

**Firefox's own background traffic is left on by design.** The core's telemetry and
data-reporting prefs block is deliberately empty: a comment dated 2026-08-19 records that
the prefs that suppressed retail traffic were removed so Gecko's defaults apply
(`invisible_core/prefs.py:826-868`). The one exception is download reputation,
`browser.safebrowsing.downloads.remote.enabled` set to false (`prefs.py:893`). What the
engine changes on its side is in the `stillborn/` folders: the intermediates collection is
never synced (`stillborn/intermediates/FEATURE.md:9-12`); the update check to
`aus5.mozilla.org` goes out as retail sends it and everything after the answer is refused
(`stillborn/updater/FEATURE.md:13-18`); and the shutdown pingsender "does not start while
the session's proxy is undecided" and otherwise carries the session proxy
(`stillborn/telemetry/FEATURE.md:13-15`, `:19-20`). The build still sets
`MOZILLA_OFFICIAL=1` and the release update channel (`platform/build-config/src/.mozconfig:49`,
`:84`), on which Firefox's telemetry reporting defaults on. The core still gives the sender
10 s before the session's processes are ended (`SENDER_GRACE`,
`invisible_core/juggler/_profile.py:36`). In a session the package drives, every channel
that asks the proxy service is held from `command-line-startup` until the core's first
command and then answered with the context or browser proxy
(`network/doh/src/juggler/EarlyProxyHold.js:31-50`; `TargetRegistry.js:521-550`), so by
the source Firefox's own early requests do not leave before the proxy is known (**A**
source; not run).

The repository [`feder-cr/invisible_firefox`](https://github.com/feder-cr/invisible_firefox)
(a desktop profile manager that, in the last copy read, `602f70f` of 2026-08-14,
integrated the commercial proxy provider `api.sx.org` with a user-supplied key) **returns
HTTP 404** (2026-11-20). The wrapper's `pyproject.toml:61-63` and the core's
`constants.py:127-131` state that it was deleted on 2026-08-18. It was never a dependency
of `invisible_playwright`.

---

## Code quality

Production code only; tests and vendored trees excluded (the vendored Playwright client
`_pw/` and `invisible_core/juggler/injected.js`). `scripts/codemetrics.py`, run on
2026-11-20. Method and comparison against the other tools: [CODE-REVIEW.md](CODE-REVIEW.md).

| Metric | `invisible_playwright` | `invisible_core` |
|---|---:|---:|
| Production LOC | 19,387 (13,612 on 2026-10-13) | 46,831 (26,472), incl. the generated `keylayouts_windows.py` (11,029) |
| Test files | 426 (129) | 209 (90) |
| Bare `except:` | 1 | 0 |
| Broad `except` | 81 (4.2/kLOC) | 84 (1.8/kLOC) |
| `print(` | 165 | 355 |
| `time.sleep` | 13 | 18 |
| TODO/FIXME | 0 | 0 |
| `shell=True` / `eval` / `pickle` / `verify=False` | 0 / 0 / 0 / 0 | 0 / 0 / 0 / 0 |
| CI workflows | 12 | 4 |

For scale: the vendored `_pw/` is 68 files and about 62,000 Python lines (two generated
API files of about 23,700 lines among them), and `invisible_core/juggler/injected.js` is
8,121 lines. The largest first-party files are `_juggler/server.py` (6,426) and the
core's generated `keylayouts_windows.py` (11,029). The comment style is discursive:
`pyproject.toml` spends about 25 lines on one version pin (`:47-71`).

---

## Claims versus source

The submission stated *"I would rather give you what is measured than what is claimed."*
Against the source at the commits above:

| Claim | Status |
|---|---|
| Firefox patched in C++ and rebuilt | **Verified (A) for the pre-rewrite engine** (104 files at the `stealth/150` pair; 150 more on `stealth/151` to `a3819a7`). **Verified (A) for the current series** as patch files: 79 feature folders, 75 `hooks.patch` files against Mozilla's files and 665 added files, against `FIREFOX_159_0_RELEASE`; not rebuilt here |
| Fingerprint set in the engine, no JS shims on the page | **Consistent with the pre-rewrite diff (A)** and with the series layout. The client also runs a page-side script, `invisible_core/juggler/injected.js`, in the utility world for selectors and actionability, with six marked changes |
| Driven by stock Playwright | **No longer accurate (A)** — at `0.57.1` the wrapper ships a modified vendored client (`_pw/`), does not depend on `playwright`, and drives Firefox through a Python Juggler server, which `launch_server()` can also expose to stock clients |
| "Playwright's API, sync and async, with no code changes" (`README.md:74`) | **API-compatible with named exclusions (A)** — tracing, HAR, CDP, `APIRequestContext` and others refuse by name (`_juggler/perimeter.py`); the returned classes are the vendored copy's |
| The series rebuilds the shipped engine | **Tier B** — reported by every export commit ("verify identical"); not reproduced, and the sealed `source_commit` is not in the series history |
| The launcher and server refuse the launch-counter prefs (`README.md:225`) | **Stale (A)** — no `usage_ping` handling exists under the wrapper's or the core's `src/`, and the engine reads neither pref (`StealthLaunchCounter.sys.mjs:11-16`); the wrapper's own test asserts there is no refusal. The engine ignores the prefs, so the outcome (no opt-out) is the same |
| Same seed reproduces the same machine | **Not verified (D)** — no run was performed |
| Test harness is public and reproducible | **Verified present (A)** — 426 test files, 12 CI workflows; CreepJS, BotD, FingerprintJS, fpscanner, Sannysoft, BrowserLeaks and reCAPTCHA are each referenced under `tests/` (1 to 7 files each), with offline copies of BotD, CreepJS, FingerprintJS and fpscanner in `tests/vendor/` |
| Detector-suite results in the README | **Tier B** — author-run, not reproduced here (e.g. the "5/5 detection suites passed" image, `README.md:24`) |
| Anti-bot service coverage | **Not claimed as pass rates** — the README names reCAPTCHA, hCaptcha and Cloudflare Turnstile as scorers and links explainer articles per vendor, with no pass-rate table |

---

## Comparison

Against the other engine-level Firefox and Chromium entries. The invisible_playwright column
is as of 2026-11-20; the other columns are as of their own pages.

| | invisible_playwright | Camoufox | Clearcote | CloakBrowser |
|---|---|---|---|---|
| Engine | Firefox 159.0 (patch series) | Firefox fork (see its page) | Chromium 150 (ungoogled) | Chromium (Pro; see its page) |
| Spoofing level | C++ engine | C++ engine | C++ engine | C++ engine |
| Engine source published | **Yes** — per-feature patch series against Mozilla's tag | Yes | Yes | **No** |
| Patch readability | 79 feature folders (`FEATURE.md`, `hooks.patch`, `src/`) | `.patch` files | 37 in `patches/series` | n/a |
| Client | **vendored, modified Playwright Python client** + in-process Juggler server | own launcher | Playwright/Puppeteer SDK | Playwright/Puppeteer SDK |
| Launch telemetry | **yes, mandatory** (no pref since `firefox-64`) | none found | none found | none found |
| Binary checksum verified in code | Yes — fresh download against the sealed digest; cached engine: identity check | Yes | Yes (+ GPG) | Yes (Ed25519) |
| Fingerprint rotation | per-seed | statistical generator | per-seed / real-profile import | per-seed |

It is the **only tool in this comparison whose browser makes an unsolicited network
request at startup by default**, and now the only one where that request cannot be
switched off by configuration. Of the two Firefox entries, Camoufox ships its own
launcher while invisible_playwright keeps the Playwright API shape on a vendored copy of the
client.

---

## Applicability

**Suited to:** Playwright codebases that want engine-level Firefox fingerprinting without
adopting a bespoke launcher API — the README describes a two-line switch from
`playwright.sync_api`, with named exclusions (tracing, HAR, CDP, `APIRequestContext`) —
and, through `launch_server()`, Playwright clients in other languages. Also to reviewers
who want to read the engine changes feature by feature.

**Constraints:** Firefox only, so targets that probe SpiderMonkey engine behaviour
identify the browser family regardless of configuration — the same structural limit
Camoufox documents. Windows x86_64 and Linux x86_64 only: macOS support ended with wrapper
`0.7.3` and Linux arm64 with engine `firefox-55`. Eight contributors. The link from the
published series to the shipped binary rests on the project's own `verify` step. The
launch ping to `github.com` is mandatory; see [Launch telemetry](#launch-telemetry). On a
cold cache the core fetches Mozilla's intermediate-certificate list from the host's own
address before the browser starts, whatever proxy the session uses.

**Opting out of the launch ping:** not possible through the package since engine
`firefox-64`. Earlier revisions of this page documented
`InvisiblePlaywright(extra_prefs={"invisible_firefox.usage_ping.enabled": False})`; on the
current engine that pref is not read. What remains is outside the package: rebuilding the
engine from the series without `platform/launch-counter`, or blocking the request on the
network.

---

*Analysis conducted for educational purposes against the source at the commits above,
read in an isolated container — see [METHODOLOGY.md](METHODOLOGY.md#source-handling).
Nothing was installed, built, or executed. Use responsibly.*
