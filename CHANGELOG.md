# Changelog

## 2026-11-20 — Re-verification against upstream (all ten tools)

Every tool page, the README tables, the code review and the interactive matrix were
re-read against the upstream trees in the sandbox; the previous pass was 2026-10-13.
STATUS.md was regenerated the same day. Nine of the ten tools changed; XDriver did not.
Nothing from the upstream trees was installed, built or executed. The sandbox clones are
shallow (depth 50), so where more than 50 commits had landed the comparison is a tree diff
between the two pins, and no commit older than the clone's boundary was read on its own.

### Versions and commits read

| Tool | Documented on 2026-10-13 | Now | Commit read |
|------|--------------------------|-----|-------------|
| Camoufox | browser `v156.0.1-beta.38` (pre-release, Firefox 156.0.1), PyPI `0.5.8` | browser `v159.0-beta.42` (2026-11-15, pre-release, Firefox 159.0; latest non-pre-release `v158.0.1-beta.41`, 2026-10-29), PyPI `0.5.9` (2026-11-01, no matching tag), library pre-release `v0.5.10b1` | `4c909d6` |
| Patchright | `1.63.0` (GitHub/npm/PyPI); `main` had one unreleased fix (`86be858`) | GitHub release `v1.64.1` (2026-10-15; `v1.64.0` and `v1.64.1` tag the same commit `2d2b887`), npm `1.64.3` and PyPI `1.64.4` (2026-11-02, no matching tags); `86be858` shipped in `v1.64.0`; three code commits on `main` after the last tag | `521ad98` (python `8727f3b`, nodejs `a2e746c`, dotnet `6d20770`) |
| SeleniumBase | `4.56.1` | `4.58.2` (2026-11-19) | `11f3610` |
| Botasaurus | core `4.0.97`, driver `4.0.101` | unchanged on PyPI; 13 monorepo commits, all in the Node packages | `3873a56`, `db1d291` |
| XDriver | `v1.0.1` | unchanged, no commits since 2025-09-10 | `b610852` (rebrowser-patches statements checked at `31b5135`) |
| CloakBrowser | wrapper `0.6.2`, Pro Chromium 154 on every platform | wrapper `0.7.3` (2026-11-20), Chromium `156.0.8078.47.1` on every platform for free and paid keys; keyless download removed in 0.7.0 | `fa3716e` |
| Scrapling | `0.4.15` | `0.5.1` (2026-11-04), after `0.5` (2026-10-17); `main` has 7 docs/sponsor/CI-only commits after the tag | `2998c9e` |
| Obscura | `v0.2.4`; `main` 59 commits past the tag | `v0.2.7` (2026-11-13), after `v0.2.5` (2026-10-17) and `v0.2.6` (2026-10-31); `main` 100 commits past the tag (373 since `8edfe48`, GitHub compare) | `58a04dd` |
| invisible_playwright | wrapper `0.35.3`, core `41.39.0`, engine `firefox-41` (Firefox 151.0) | wrapper `0.57.1`, core `67.79.0` (both 2026-11-20), engine `firefox-67` (Firefox 159.0); the engine repository was re-rooted as a patch series | `d1bfea3`, core `191f0fa`, engine `9110d5d` |
| Clearcote | browser `pre.23` (Chromium 150), SDK `0.49.0` | browser `v0.1.0-pre.25` (2026-10-28; open Windows/Linux build on Chromium 151) plus `v0.1.0-pre.24` (2026-10-21, pre-release; open macOS arm64 build on Chromium 150); SDK `0.70.1` (2026-11-19) | `389653c` (291 commits after `fb3e7bb`, GitHub compare) |

### What changed upstream

- **Camoufox**: Firefox 156.0.1 to **159.0**. Top-level patches 42 to **65** (64 in
  release `v159.0-beta.42`): removed `audio-fingerprint-manager` and `no-search-engines`;
  added 25, among them `cpu-vendor-estimates` (canvas and Opus computed as a claimed Intel
  or AMD CPU, ARM64/x86-64 emulated; new `cpu` option), `webrtc-socks5-udp` (WebRTC UDP
  through a SOCKS5 relay; no invented srflx candidate), `zz-stock-cost-parity` (spoofed
  getters do stock's work first so they are not faster than stock),
  `per-context-http-user-agent`, `windows-crt-math` and `windows-keyboard` (a Windows
  identity on another host), `headless-software-webgl`, and background-traffic patches
  (Remote Settings from pinned dumps, Push on demand). **Audio noise removed**: no
  `audio:seed`; the render is stock's per CPU architecture. Window `innerWidth`/`screenX`
  getters no longer read the config; the real window is sized and placed instead. No
  `policies.json`; stock search engines return. Config keys 78 to 79 live, 54 to 65 marked
  `removed`. Releases ride a twice-monthly train (1st and 15th). After the latest release,
  humanized input left the browser: `humanize=True` runs the pinned `myuri` 4.0.0 package
  in the launcher, the vendored LGPL cursory-js and the `humanize*` config keys are gone,
  and Python `^3.11` is required.
- **Patchright** 1.63.0 to 1.64.1 (GitHub), npm 1.64.3 / PyPI 1.64.4: the Playwright 1.64.0
  port (`79fc6fc`) adapts the patches to Playwright's selector-target API, registers init
  scripts with `runImmediately` after the binding wrappers are installed, and has the page
  call upstream's `updateRequestInterception()` instead of always enabling interception.
  After the `v1.64.1` tag, `main` keeps Chromium's `MediaRouter` feature enabled
  (`929d804`), drops two `framesPatch.ts` overrides (`bd714e6`), and fixes restarted
  requests hanging behind authenticated proxies (`f14e043`); whether npm 1.64.3 / PyPI
  1.64.4 contain them is not recorded. The route-injection list is still never populated.
- **SeleniumBase** 4.56.1 to 4.58.2: UC and CDP Mode stop passing `--test-type` unless a
  proxy is set (new `no_tt` option drops it with a proxy too) and keep IPC flooding
  protection on unless Fast Mode is set; Chrome for Testing gets `--disable-infobars`;
  `--disable-popup-blocking` and the `MediaRouter` disabled feature were dropped. CDP
  typing on Windows and macOS wraps uppercase letters and shifted symbols in Shift key
  events (Linux still sends `char` events). The DataDome slider is found in nested iframes.
  `selenium` 4.53.0; PyOTP replaced by an in-house TOTP routine; README rewritten again.
- **Botasaurus**: no PyPI release and no Python change. The JS driver's Chrome launcher
  tracks and force-kills launched Chrome processes; the Node server gained task abort,
  retried data-file writes and NDJSON streaming.
- **XDriver**: no change. rebrowser-patches, the lineage it repackages, resumed releases
  (v1.1.0 to v1.1.3) with patch sets for `playwright-core` 1.64.1 and fixes XDriver's 2025
  bundle predates.
- **CloakBrowser** 0.6.2 to 0.7.3: **every launch now needs a licence key** (0.7.0). A
  launch with no key offers a free key by email (one concurrent session) in a terminal or,
  without one, raises with a sign-up link and polls cloakbrowser.dev for the key in the
  background (every 15 s, up to 10 min). The keyless Chromium 146 download, the GitHub
  Releases fallback, GitHub sign-in, `CLOAKBROWSER_DOWNLOAD_URL` and
  `CLOAKBROWSER_SKIP_CHECKSUM` are gone, and the Docker image no longer contains a binary.
  Pro moved 154 to 155 to **156** on every platform (87 claimed patches); the README says
  free and paid keys get the same build. Humanize retuned (0.6.3). Playwright capped below
  1.66 (.NET below 1.65). The release-archive attestation workflow was deleted (`91effe4`)
  while the README still documents `gh attestation verify`. Sandbox default unchanged.
- **Scrapling** 0.4.15 to 0.5.1 (breaking): the plain-Playwright
  `DynamicFetcher`/`DynamicSession` tier is removed, so every browser path is Patchright;
  `cdp_url` moved to new `RemoteSession` classes that attach over CDP with no launch flags;
  `capture_xhr` replaced by session network recording; `save_state()`/`load_state()`;
  `pierce_shadow`; `STEALTH_ARGS` 53 to 54. The Cloudflare solver waits up to ~5 s for late
  widgets and clicks embedded widgets through a checkbox locator (still max 3 re-solves).
  The MCP server moved to `scrapling/core/ai/` and grew from 13 to 17 tools (page actions,
  network history, `browser_observe` frame sampling); the README now says agents can
  "bypass any CAPTCHA" through it (Tier B). `curl_cffi>=0.16.3`.
- **Obscura** v0.2.4 to v0.2.7: still 14 CDP domains, 117 to 122 methods; MCP still 38
  tools plus an opt-in `web_search` that sends queries to the third-party Keenable API.
  Render engine 72,401 to 74,722 lines. `--user-agent` became a global flag that reaches
  stealth builds' UA while their platform fields and Chrome 145 TLS profile stay fixed.
  Worker recycling, per-connection storage isolation and a CDP `Origin` allowlist. Stealth
  form POST navigations use the wreq client. Fingerprint pools, canvas, audio and WebGL
  unchanged.
- **invisible_playwright** 0.35.3 to 0.57.1 (core 41.39.0 to 67.79.0; engine `firefox-41`
  to `firefox-67`): the engine repository was re-rooted on 2026-10-27 (`eefcdbb`, no
  parents): the full-tree `stealth/150`/`stealth/151` branches are gone, and `main` and the
  release tags hold a patch series against Mozilla's `FIREFOX_159_0_RELEASE`, 79 feature
  folders (75 with a `hooks.patch`, 665 added files). Firefox 151.0 to 159.0 at
  `firefox-54`. **The launch counter has had no pref since `firefox-64`**: the URL is a
  constant (`StealthLaunchCounter.sys.mjs`), so it cannot be turned off or redirected and
  the `extra_prefs` opt-out this report documented no longer works; both READMEs now
  describe it. By the source it is held until the core names the session proxy and then
  uses it (read, not run). Behind a proxy, names resolve by DoH through the proxy and
  WebRTC/HTTP3 UDP goes through the SOCKS5 relay when the core measures the UDP exit as
  matching the TCP exit; the synthetic server-reflexive candidate is gone. 2D canvas reads
  back as drawn since `firefox-52` (noise on WebGL/WebGPU only). On a cold cache the core
  downloads Mozilla's intermediate-certificate list from the host's own address.
  `launch_server()` serves the browser to stock Playwright clients (0.48.0). Linux arm64
  dropped. The projects moved to the `oss-invisible` GitHub organisation. The core wheel
  ships Firefox branding archives (MPL-2.0) not named in its licence field. The update
  check to aus5.mozilla.org goes out again (download and install refused). 50 static
  `zoom.stealth.*` prefs (46).
- **Clearcote**: the open Windows/Linux build moved from Chromium 150 to 151
  (`v0.1.0-pre.25`) and is now an official ThinLTO + PGO build with DCHECKs compiled out.
  Patches 37 to 62: `951` removed; `960`–`985` added (SOCKS5 authentication and UDP
  ASSOCIATE relay, engine-side HTTP proxy authentication, portable cookie key, a
  `--clearcote-validate-persona` self-check, opt-in persona schema 2, and WebGL/WebGPU/DPR
  coherence for cross-OS personas); stray backup hunks dropped. A separate open **macOS
  arm64** build on Chromium 150 (`v0.1.0-pre.24`, unsigned, not notarized). SDKs 0.49.0 to
  0.70.1: the `geoip` lookup now runs by default (IP echo plus GeoIP database download;
  `geoip: false` turns it off); native launch of the macOS build on Apple Silicon (Docker
  only on Intel Macs); per-identity humanize pacing and a post-load reading pause; on
  licensed r51+ engines a signed persona is fetched from `persona.clearcotelabs.com` on
  every launch, and an imported profile's JSON is sent there.

### Corrections

| Tool | Previous statement | Verified state |
|------|--------------------|----------------|
| Camoufox | The default `os` is a random pick of Windows, macOS and Linux, so a default launch claims another OS than the host's in most draws | With no `os`, `generate_fingerprint()` passes no OS condition and fpgen draws the OS from its own model; its weighting was not read (fpgen is not in the sandbox), so "most draws" is unestablished (Tier D) |
| Patchright | `chromiumSwitchesPatch.ts` removes "the big `--disable-features=...` blob" | The switch was always kept: Playwright builds it as `'--disable-features=' + disabledFeatures.join(',')`, so the literal string in the removal list never matched. Since `929d804` only `MediaRouter` is dropped from the list |
| Patchright | `patchright.patch` 50,211 lines, +20,568 / −10,826, `driver_patches/` 5,091 lines | Those were `26ab9ae` figures; at `ba8bd9b` 50,277 lines, +20,622 / −10,828, 5,136 lines |
| Botasaurus | `Runtime.enable` "not addressed; the only source reference is a commented-out line at `connection.py:219`" | `connection.py:219` is `self.websocket.close()`. The driver contains no `Runtime.enable` send: domains are enabled only for registered event handlers (`core/connection.py:318-349`), and the Runtime handlers are commented out "to avoid runtime detection" (`core/tab.py:165-173`). Botasaurus is now listed under "`Runtime.enable` addressed" with "not tested at runtime" |
| Botasaurus | "58 generated binding files" in `botasaurus_driver/cdp/` | 54 domain modules plus `__init__.py`, `util.py`, `README.md` and `py.typed` |
| Botasaurus | Driver repo "last public commit 2025-06" | 2026-07-30 (`db1d291`) |
| SeleniumBase | A fingerprint-term search hits only a `--use-angle=swiftshader-webgl` option and recorder JS | It also hits the `--enable-3d-apis` option and `base_case.py` canvas-drawing test helpers; still no fingerprint-rewriting code |
| XDriver | 295 lines "across `x_driver/*.py`" | `x_driver/*.py` is 262 lines; the 295 includes the 33-line `setup.py` |
| XDriver | The README's PyPI badge "links nowhere" | A static v0.0.1 badge linking to the pypi.org home page |
| CloakBrowser | README stealth table and matrix: "Chromium 152 fork (Pro; 151 on macOS)" | Already Chromium 154 on every platform at `485f678` (the page and changelog said so; these two cells were missed). Now 156 |
| CloakBrowser | CODE-REVIEW finding 1: `cloakserve` builds its arguments at `bin/cloakserve:353-354` | `:354-355` at `485f678`; `:367-373` now |
| Obscura | In a non-render build, screenshot/PDF/screencast return "…not supported by Obscura: no layout or paint engine" | They return "Page.<method> requires a build with the render feature"; the quoted string belongs to `Page.captureSnapshot`, refused in every build |
| Obscura | Interception types re-exported at `crates/obscura/src/lib.rs:19-27` | Lines 30-32 |
| Obscura | `op_computed_style` signature without `frame_id` | It also takes the calling frame's id |
| Clearcote | Per-site audio (`AudioBuffer`) farbling from the seed | The noise helpers in `020-audio` are never called: their only call site is commented out (`020-audio.patch:71,94,115`, the same at `pre.23`). `patches/README.md` still says otherwise |
| Clearcote | One seed derives locale and fonts | The font list is one canonical list per claimed OS (or an imported profile's); languages and timezone come from options or `geoip` |
| Clearcote | The SDK's default `disable_non_proxied_udp` keeps WebRTC UDP behind the proxy | On the open build `100-webrtc-leak` re-enables non-proxied UDP whenever `--webrtc-ip` is set (`100-webrtc-leak.patch:34-41`, unchanged since `pre.23`) |
| Clearcote | No named commercial anti-bot service appears in the public tree | SDK comments already named reCAPTCHA as a bot detector at `fb3e7bb`; they now also cite a fingerprint.com verdict. Neither is a pass-rate claim |
| Clearcote | Usage example passed a seed together with `fingerprint_profile` | The SDK warns against that; the example now uses the profile alone |
| invisible_playwright | The page's comparison table gave Camoufox "Firefox 152 fork, 44 `.patch` files" and CloakBrowser "Chromium 152 (Pro)" | Already stale on 2026-10-13 (Camoufox 156.0.1 with 42 patches, CloakBrowser 154); the page now defers those cells to the tools' own pages |
| invisible_playwright | "The one content hash on the reuse path is `omni.ja` on Windows" | The `omni.ja` comparison runs only when adopting an unstamped tree; a stamped cache hit runs `verify_engine` only (`download.py:546-559`, `:671-672` at `191f0fa`; the same at `415bbd8`) |

### Code metrics

`scripts/codemetrics.py` was changed in two ways before the tables were regenerated, so
some figures do not compare directly with 2026-10-13:

- **Pattern counts now cover source files only** (the same extensions as the line counts,
  plus `*.sh` and `Dockerfile*`). They used to scan every non-excluded file, Markdown
  included. Scrapling's translated documentation took its `print(` count from 192 to 891
  without a code change; the source-only figure is 34. CloakBrowser's `--no-sandbox`
  count drops from 4 to 3 (the fourth was its CHANGELOG), and Clearcote's is 67 (84 at
  2026-10-13 with documentation included).
- **`*_tests.rs` files count as tests.** Obscura declares five sibling test modules as
  `#[cfg(test)] mod x_tests;`; counted as production they added 50 `.unwrap()` lines and
  4 `panic!` (103 and 1 without them).

Both new largest files are generated tables: Camoufox's
`browser/additions/gfx/skia/skia/src/opts/SkCpuEstimateTables.h` and `invisible_core`'s
`juggler/keylayouts_windows.py`; they are labelled as such.

### Pass notes

- METHODOLOGY.md gained [inclusion criteria](METHODOLOGY.md#inclusion-criteria) for
  proposed tools (readable engine or wide adoption, a release in the last 90 days, one
  non-alpha platform), written up after the Hexium Browser request in issue #2, which does
  not meet them as of this pass.
- Two slices of this pass first mistook the sandbox's shallow-clone boundary for a history
  rewrite (Camoufox, Clearcote). GitHub's compare API shows both old pins as plain
  ancestors of the new ones; the claims were removed before publication.
- The invisible_playwright engine fork really was re-rooted: its history now starts at
  `eefcdbb` (2026-10-27, no parents per the GitHub API), a patch series rebuilt from the
  old full-tree branch. Its tag `firefox-67` was cloned in full into the sandbox so the
  series could be read rather than inferred from commit messages.

## 2026-10-13 — Re-verification against upstream (all ten tools)

Every tool page, the README tables, the code review and the interactive matrix were
re-read against the upstream trees in the sandbox; the previous pass was 2026-09-30.
STATUS.md was regenerated the same day. Nothing was installed, built or executed. The
invisible_playwright engine fork was read from its git objects without a checkout.

### Versions and commits read

| Tool | Documented on 2026-09-30 | Now | Commit read |
|------|--------------------------|-----|-------------|
| Camoufox | browser `v156.0.1-beta.33`, PyPI `0.5.6` | browser `v156.0.1-beta.38` (pre-release, still Firefox 156.0.1), PyPI `0.5.8` (fpgen-based), library pre-releases `0.5.9b1`–`b3` | `4559d01` |
| Patchright | `1.63.0` | unchanged; `main` has one unreleased driver fix (`86be858`) | `ba8bd9b` |
| SeleniumBase | `4.54.13` | `4.56.1` (2026-10-12) | `be6514f` |
| Botasaurus | core `4.0.97`, driver `4.0.101` | unchanged, no commits | `6c9260d`, `db1d291` |
| XDriver | `v1.0.1` | unchanged, no commits | `b610852` |
| CloakBrowser | wrapper `0.5.11`, Pro Chromium 152 (macOS 151) | wrapper `0.6.2`, Pro Chromium 154 on every platform | `485f678` |
| Scrapling | `0.4.15` | unchanged; `main` has 24 docs/sponsor-only commits after the tag | `7a68493` |
| Obscura | `v0.2.3` | `v0.2.4` (2026-10-04); `main` is 59 commits past the tag | `8edfe48` |
| invisible_playwright | wrapper `0.25.7`, core `34.31.0`, engine `firefox-34` | wrapper `0.35.3`, core `41.39.0`, engine `firefox-41` (Firefox 151.0) | `91ea73b`, core `415bbd8`, engine `a3819a7` |
| Clearcote | browser `pre.23`, SDK `0.33.0` | browser unchanged, SDK `0.49.0` (2026-10-12) | `fb3e7bb` |

### What changed upstream

- **Camoufox**: repository split into `browser/`, `python/` and `typescript/` (every path
  citation changed); 44 to 42 top-level patches (removed `browser-init`,
  `global-style-sheets`, `pin-addons`, `windows-theming-bug-modified`; added
  `camoufox-window-module`, `user-agent-app-name`); vendored LibreWolf/Ghostery patches
  14 to 2. Juggler loads from `resource://gre/modules/juggler/` instead of a `chrome://`
  package, and the build sets `MOZILLA_OFFICIAL`. When the identity claims an OS or GPU
  other than the host's, canvas and WebGL readback return `privacy.resistFingerprinting`'s
  random placeholder by default (new `canvas_noise` option); the default `os` is a random
  pick, so most default launches claim a non-host OS. WebGPU follows the claimed device.
  Per-context identities on a launch without the placeholder keep the host's OS and GPU.
  78 live config keys (was 82). Browser releases declare an `interface` number; `geoip`
  defaults to the GeoIP AIO database. The npm package is renamed `camoufox`. The canvas,
  Juggler and restructure changes are in the `0.5.9b*` pre-releases and browser
  `beta.37`/`beta.38` only.
- **invisible_playwright**: the Juggler client moved from the wrapper into
  `invisible_core.juggler` (core 38.34.0 / wrapper 0.30.0); the core is now
  `MIT AND Apache-2.0`. Since core 41.35.0 the core sends `Browser.setBrowserProxy`, still
  after the readiness line, so the launch ping still precedes it. Engine `firefox-35` to
  `firefox-41`: window geometry from a device-pixel frame, `Browser.setServiceWorkersBlocked`,
  zoom-corrected pointer input, per-context worker locale, a Linux WebRTC-behind-SOCKS
  wildcard fix; `zoom.stealth.*` prefs 44 to 46. Firefox's shutdown telemetry pings now
  leave through the session proxy (`firefox-40`). The launch ping is unchanged.
- **CloakBrowser** 0.5.11 to 0.6.2: Pro Chromium 154 on every platform (87 claimed patches,
  unchanged). Humanize rewritten (0.6.0) around Playwright's InjectedScript in an isolated
  world: full selector syntax, strict mode, real Playwright errors; Playwright >= 1.53
  required. Persistent profiles keep one fingerprint seed. First-run downloads extract into
  a private staging directory. A one-time warning that Playwright's request client
  bypasses SOCKS5 or credentialed HTTP proxies. Sandbox default unchanged.
- **Clearcote**: no engine change (Chromium 150, 37 patches). SDKs 0.33.0 to 0.49.0: hosted
  browsers (`launch(cloud=True)`), a Docker route on macOS, humanized form filling,
  Widevine on by default for licensed launches, `--allow-third-party-cookies` by default,
  ip-api.com GeoIP fallback off by default. The Docker image runs Chrome with its sandbox
  only when given the bundled seccomp profile, which the SDKs pass only on x86_64. MCP
  server gained an egress guard. The project README no longer states zero telemetry.
- **Obscura** v0.2.3 to v0.2.4: intercepted XHR reported as `Xhr` (was `Fetch`); the
  multi-worker balancer restarts exited workers; `Page.close` with `beforeunload`,
  `Page.stopLoading`, `Runtime.getHeapUsage`, `HeapProfiler.collectGarbage` and others
  (111 to 117 CDP methods); MCP tools 37 to 38 on `main`; render engine 72,401 lines. No
  change to the fingerprint surface.
- **SeleniumBase** 4.54.13 to 4.56.1: opt-in Fast Mode that skips built-in waits (the
  project notes it "may impact stealth"); shorter default waits; `selenium` 4.51.0;
  README rewrite dropping the "Stealthy Chromium Automation" subtitle. UC and CDP driver
  code unchanged.
- **Patchright**: one unreleased fix on `main` (request-listener leak and crash-retry loop);
  no claim affected.

### Corrections

| Tool | Previous statement | Verified state |
|------|--------------------|----------------|
| SeleniumBase | Imperva/Incapsula example labelled "WAF + hCaptcha" | The project heading says "invisible reCAPTCHA" (at both commits); the `sb_cdp` handler is an hCaptcha click |
| CloakBrowser | Shift-symbol typing falls back to `page.evaluate` | Since 0.6.0 always CDP `Input.dispatchKeyEvent`; the fallback survives only in the exported `human_type` helper |
| CloakBrowser | Version pinning works for keyless and paid keys (README) | README now says paid key only; the keyless code path still honours a pin |
| Scrapling | Post-tag commits touch only README, docs, images and `zensical.toml` | They also touch `CONTRIBUTING.md` and `.gitignore`; no code |
| Clearcote | README states zero telemetry/phone-home | No longer in the README; the page lists the SDK's own outbound calls |
| Camoufox | `1-leak-fixes.patch` also reverts Playwright's policies provider | It changes only `Navigator.cpp`; the provider hunk was removed from `0-playwright.patch` |

### Other

- `scripts/codemetrics.py` now excludes the vendored `invisible_core/juggler/injected.js`
  (8,121 lines) as well as the wrapper's old `_juggler/injected.js`. All CODE-REVIEW and
  matrix metrics were regenerated with it.
- On 2026-10-13 GitHub no longer flagged Clearcote's `v0.1.0-pre.23` release as a
  pre-release, so STATUS.md shows it without the marker; the tag name, `llms.txt` and the
  build configuration still describe it as a pre-release.

## 2026-09-30 — Re-verification against upstream (all ten tools)

Every tool page, the README tables, the code review and the interactive matrix were
re-read against the upstream trees in the sandbox. The previous full pass was
2026-08-14. Versions and health figures are in [STATUS.md](STATUS.md), regenerated the
same day. Nothing was installed, built or executed; Tier A still means the code was read.

### Versions and commits read

| Tool | Documented on 2026-08-14 | Now | Commit read |
|------|--------------------------|-----|-------------|
| Camoufox | browser `v152.0.4-beta.28`, PyPI `0.5.4` | browser `v156.0.1-beta.33` (pre-release; latest non-pre-release `v152.0.4-beta.30`), PyPI `0.5.6`, repo `0.5.7` | `2f30fea` |
| Patchright | driver/Node `1.61.1`, Python `1.61.2` | `1.63.0` on GitHub and npm (2026-09-08), PyPI (2026-09-20) | `26ab9ae` |
| SeleniumBase | `4.51.12` | `4.54.13` (2026-09-30) | `f9955d0` |
| Botasaurus | core `4.0.97`, driver `4.0.101` | unchanged | `6c9260d`, `db1d291` |
| XDriver | `v1.0.1` | unchanged, no commits since 2025-09-10 | `b610852` |
| CloakBrowser | wrapper `0.5.7`, Pro Chromium 150 | wrapper `0.5.11`, Pro Chromium 152 (macOS Pro 151) | `f44864b` |
| Scrapling | `0.4.14` | `0.4.15` (2026-08-23); `main` has 15 docs-only commits after it | `b11da90` |
| Obscura | `v0.2.0` | `v0.2.3` (2026-09-20); `main` is 66 commits past the tag | `a005d16` |
| invisible_playwright | wrapper `0.7.0`, engine `firefox-19` | wrapper `0.25.7` (2026-09-25), engine `firefox-34` (Firefox 151.0) | `3218090`, core `0f4a30c`, engine `fec80c8` |
| Clearcote | browser `pre.22`, SDK `0.26.1` | browser `pre.23` (2026-09-28), SDK `0.33.0` | `1596f29` |

### What changed upstream

- **Camoufox**: Firefox 152.0.4 to 156.0.1; 34 to 44 top-level patches (2 in
  `patches/playwright/` unchanged); fpgen replaces BrowserForge at repository HEAD (PyPI
  0.5.6 still depends on BrowserForge); a coherence check on every generated identity; the
  C++ `MouseTrajectories.hpp` was removed and the cursor is now a replay of recorded
  movements (Cursory, vendored, LGPLv3-or-later) in Juggler JS; per-context setters are
  created sealed; glyph-spacing noise removed; the `outerWidth`/`outerHeight`, scroll
  min/max, `history.length`, battery and WebGL context-attribute hooks were removed; a
  TypeScript launcher and a release pipeline were added; bundled real presets 312 to 285.
- **invisible_playwright**: the wrapper vendors a modified copy of Playwright's Python
  client (`_pw/`, since 0.7.3) and an in-process Python Juggler server (`_juggler/`, which
  replaced the Node driver in 0.8.0); `playwright` is no longer a dependency; macOS support
  dropped; the `invisible_firefox` repository was deleted on 2026-08-18; the engine fork
  gained a bundled font set and a screencast rework. The launch ping is still on by
  default; its URL is now a pref that the core sets.
- **Clearcote**: open build on Chromium 150 with 37 patches (new: `071`, `142`, `220`,
  `951`, `955`); `enable_mdns` turned on; SDKs 0.26.1 to 0.33.0 (`clearcote` CLI, `serve()`
  multiplexer, isolated-world DOM reads for `humanize`, MCP server, Docker image); the
  project README now describes a free-with-GitHub tier and hosted browsers (**Tier B**).
- **CloakBrowser**: Pro binary Chromium 150 to 152 with 87 claimed patches (was 71); a
  free GitHub-sign-in key tier; an invalid or unvalidatable key and a failed GeoIP lookup
  now abort the launch instead of falling back; archives are unpacked without per-entry
  screening after the signature check; the sandbox default is unchanged.
- **Obscura** v0.2.0 to v0.2.3: token authentication for CDP and MCP endpoints on
  non-loopback binds (v0.2.3), a tenth workspace crate (`obscura-ssrf`), `deno_core` 0.350
  to 0.412, render engine 66,826 to 69,866 lines, Docker image running as non-root.
- **Patchright** 1.61.x to 1.63.0: 32 to 34 driver modules; since 2026-08-17 init scripts
  are registered only through CDP `Page.addScriptToEvaluateOnNewDocument` in the current
  source (the README still describes route-based injection; read, not run); new Python
  and .NET download paths that fetch `patchright-core`.
- **Scrapling** 0.4.15: MCP tools 10 to 13 (`get` renamed `make_request`); the HTTP
  transport refuses to start without a token; the Cloudflare solver is bounded to three
  attempts; tab reuse; `locale` is passed as launch flags.
- **SeleniumBase** 4.51.12 to 4.54.13: no change to the UC patcher; an in-tree MCP server
  (2,056 lines, 24 tools); Python 3.10 minimum; `fast_type`/`fast_keys`; command-injection
  fix in console scripts (`os.system` 51 to 27 occurrences).
- **Botasaurus**: no new release; the driver repository's last commit is 2026-07-30 and
  the JS driver is on npm at 4.0.135 (2026-07-25).

### Corrections: claims that were already wrong at the 2026-08-14 commits

| Tool | Previous statement | Verified state |
|------|--------------------|----------------|
| Camoufox | Per-context seeds for audio, canvas and font-spacing noise | Only an audio seed. No canvas noise patch existed at the previous commit (`ci/tribal-rules.yml`, "canvas-is-not-noised"); glyph-spacing noise has since been removed |
| Camoufox | Hooks for `navigator.vendor`, `deviceMemory` and `languages`; "no timing difference between real and spoofed values" | None of the three was ever hooked (Firefox has no `deviceMemory`); a patch comment says uncached config reads are about 20 times slower |
| Camoufox | `new_context()` mints a real-preset identity by default | The default is a synthetic identity; real presets are opt-in (`fingerprint_preset=True`) |
| Camoufox | "v152.0.x drops 32-bit and macOS x86_64" | Not supported: the release matrix still includes macOS x86_64 and Windows i686 (`release.yml:140-152`) |
| Camoufox | `1-leak-fixes.patch` also neutralises other automation tells (enterprise-policy hints, etc.); an invented source comment in a quoted snippet | The patch changes exactly two files (`Navigator::Webdriver()` and the policies provider); the snippet is replaced by the real hunks |
| Scrapling | Camoufox removed "as of 0.4.10" | Removed in 0.3.13 (2026-01-01) |
| Scrapling | Benchmark table figures | Did not match the README; replaced (Selectolax 82.63 to 197.02 ms, BS4+lxml 1,584.31 to 1,562.1 ms, adaptive 2.39 vs 12.45 to 2.3 vs 12.58 ms) |
| Scrapling | MCP server has 10 tools, built on `FastMCP`; `patchright==1.61.1` / `playwright==1.61.0` pinned | 13 tools on `mcp.server.MCPServer`; the dependencies are minimum versions (`>=`) |
| Scrapling | DynamicFetcher lacks DNS-over-HTTPS and ad blocking; browserforge generates request headers | Both options exist on DynamicFetcher; with `impersonate` set, `curl_cffi` generates the headers and browserforge supplies only the browser tiers' User-Agent |
| SeleniumBase | Input simulation at `browser_launcher.py:1071-1082` | Wrong lines at both commits; the PyAutoGUI move and click are at `:1244-1271` |
| SeleniumBase | PyAutoGUI is an optional extra, installed on first use | An `install_requires` dependency on Linux; the extra applies to other platforms |
| SeleniumBase | All 42 `shell=True` calls are in CLI tooling | 31 are under `seleniumbase/` (8 in `console_scripts/`, 12 in `core/` launch helpers, 10 in `selenium_grid/`, 1 in `behave/`) and 11 in `examples/` |
| Patchright | `…OrThrow(` counts of 47 / 40 / 36 in `crPagePatch.ts` / `framesPatch.ts` / `crNetworkManagerPatch.ts` | Never reproduced: 222 across `driver_patches/`, with 33 / 27 / 28 in those three files |
| Patchright | 30 driver modules; patch of about 5,928 inserted lines; CSP headers "stripped"; Playwright checked out as a submodule | 32 modules at the previous commit (34 now); `patchright.patch` is a 50,211-line documentation diff that is not applied; `_fixCSP` rewrites directives; Playwright is cloned, the only submodule is `patchright-nodejs` |
| CloakBrowser | GeoIP failures "degrade gracefully" | Resolution failure aborts the launch (0.5.10) |
| CloakBrowser | Quoted phrases "goes stale within weeks", "native `getOwnPropertyDescriptor`", "no timing differences", "~65% market share"; storage quota "normalised to pass FingerprintJS" | None is in the README at either commit; the README says the quota tuning is unrelated to FingerprintJS |
| Obscura | WebGL shim with string stubs and random `readPixels` bytes | No such code since v0.2.0: `getContext('webgl')` returns `null` |
| Obscura | Canvas `toDataURL` returns a fixed string, not a valid image | A JS software rasteriser; `toDataURL` encodes a valid PNG (text glyphs are synthetic) |
| Obscura | 23 ops; 7,878-line `bootstrap.js`; 12 CDP domains; about 244 method arms; 32 MCP tools; eight crates | 47 ops and 14,635 lines at the previous commit (64 and 16,770 now); 14 domains (IO and Emulation were omitted); 111 method names; 37 tools (35 without render); nine crates at the previous commit (ten now) |
| Obscura | `userAgentData` brand order permuted per session seed; default persona Windows / Chrome 145; release step `continue-on-error`; cross-compiled releases | Brands are derived from the Chrome major; ordinary builds default to Chrome 143 (145 only in `stealth` builds); no `continue-on-error` in the workflow; releases are built on native runners |
| Obscura | CODE-REVIEW finding 4: 2,326 `.unwrap()`, 21 `panic!`, per-file counts in `io.rs`/`domsnapshot.rs`/`target.rs`, `catch_unwind` in four named files | Test-inflated. Non-test: 102 and 1 at the previous commit (91 and 1 now); the per-file counts were inside `#[cfg(test)]`; `util.rs` is a test and `serialize.rs` a comment |
| invisible_playwright | SOCKS5 UDP ASSOCIATE "lets media traffic traverse a SOCKS proxy"; "+2,037 lines in `ice_component.c`" | The engine layer is gated by `network.proxy.socks_remote_udp` (default false) and the core does not set it; `ice_component.c` was a whole added file, not 2,037 lines of new logic |
| invisible_playwright | Cached engines are re-hashed, which "catches a tampered cache"; checksums verified through `_parse_checksums` | Cache hits get an identity check (version, build ID, markers); `_parse_checksums` has no caller; fresh downloads are verified against a digest shipped in the wheel |
| invisible_playwright | 0 matches for `usage-counter` in the wrapper README | The badge link at `f777798` contained `usage-counter` (no explanation); the substance is unchanged |
| Clearcote | The stealth-coherence gate asserts that canvas and WebGL hashes are identical across two registrable domains | That check (`origin-invariant`) is a documented known gap; the gate enforces four other checks and fails if the gap check unexpectedly passes |
| Clearcote | "Does not touch Chromium's network stack" | Patch `210-tls-network-persona` changes the post-quantum key-share group and the ALPS codepoint when the claimed major differs from the build's |
| Clearcote | Patch `110` suppresses the `Runtime.enable` tell; a "Linux persona coherence" patch | `110` returns early from `addBindings()`, comments out console reporting and makes `enabled()` return false; there is no Linux persona patch in the series |
| botasaurus-driver | Last public commit 2025-06-11; JS driver on npm at 4.0.134 | Last commits 2026-07-27 and 2026-07-30; npm 4.0.135 |

Cross-page and README corrections of the same kind: the comparison tables on the
Camoufox, Clearcote and CloakBrowser pages labelled Patchright "Binary" and credited it
with partial fingerprint rotation and human-mouse support (it is a TypeScript source patch
of Playwright's driver with no such code); the Clearcote comparison row listed CloakBrowser
downloads as not signed or checksummed (the wrapper verifies a pinned Ed25519 signature
over `SHA256SUMS`, Tier A); the README said "three of the four" independent engines were
Chromium-derived (two are); the README said `check_patch_impact.yml` opens an issue on
breaking changes (the release workflow passes `create_issue: false`; a failed release test
run opens an issue and a draft PR). Scrapling's "cleanest Python" label was replaced by the
figures, because two newly measured repositories have higher annotation coverage.
CODE-REVIEW finding 1 no longer says there is no supported configuration with spoofing and
the sandbox both enabled (the README documents `stealth_args=False` with hand-written
`--fingerprint` flags) and now records that Playwright itself adds `--no-sandbox`; finding 6
withdraws the proxy statement (the session proxy is no longer written to `network.proxy.*`)
and the "0 matches" claim (the wrapper CHANGELOG now describes the ping).

### Methodology and tooling

`scripts/codemetrics.py` now generates every number in the CODE-REVIEW tables. Five
defects in how the earlier tables were produced were fixed, so some old numbers are not
comparable with the new ones:

- ripgrep gives the **last** matching glob precedence, and the extension includes came
  after the excludes, so `*.hpp` re-included the vendored `json.hpp` and `*.js` re-included
  minified files. Camoufox's previous count was 50,116 lines; the corrected figure for the
  same commit is 25,351.
- The `eval`/`exec` search needed `-P` for its lookbehind and returned 0 for every
  repository. It now runs, but its hits are mostly comments, method names and test
  helpers, so it is not shown as a column.
- The annotation rule now includes `*args`, `**kwargs` and positional-only parameters.
- Line counts follow `wc -l`; the old counts were one higher per file.
- Rust counts strip `#[cfg(test)]` items and `#[test]` functions. Obscura's previous
  `.unwrap()` figure of 2,326 becomes 102 at the same commit (3,262 raw, 91 now), and
  `panic!` 21 becomes 1.

The counting rules also now exclude invisible_playwright's vendored Playwright-Python fork
(`_pw/`) and its bundled `_juggler/injected.js`, which are not first-party code.

`scripts/sandbox.sh` gained the three `feder-cr` repositories. `feder-cr/invisible_firefox`
and `feder-cr/firefox-stealth` return HTTP 404 on 2026-09-30; the engine is read from
`firefox_antidetect_patch`.

### Removed

Rating rows and lines with no source behind them: "Detection Difficulty" (Camoufox and
CloakBrowser pages), the CloakBrowser "reCAPTCHA v3 Score" comparison row, "Detection
bypass" and "Effectiveness Rating" (Patchright), "Detection ceiling" and "Effectiveness
Rating: Moderate" (Obscura), and the "Most Effective Python Solution" and "proven bypass"
wording (SeleniumBase). The "only tool of the nine" phrasing was updated to ten on the
Camoufox, Clearcote, CloakBrowser and SeleniumBase pages.

### Updated

README (tables, lineage, capability index, health, "Changes since" section),
CODE-REVIEW.md (findings 1 to 4 and 6, per-tool assessment, metrics), STATUS.md, all ten
tool pages, `docs/index.html` (data, findings, lineage with invisible_playwright added),
`scripts/codemetrics.py`, `scripts/sandbox.sh`. METHODOLOGY.md needed no change.

---

## 2026-08-14e — Added invisible_playwright (tenth tool)

Added from [issue #1](https://github.com/pim97/anti-detect-browser-tools-tech-comparison/issues/1).
Full analysis: **[invisible-playwright.md](invisible-playwright.md)**.

### Are the patches public? Yes — with three caveats

The submission claimed "Firefox patched in the C++ source and rebuilt". Verified:

- `feder-cr/firefox_antidetect_patch` is a **genuine GitHub fork** of
  `mozilla-firefox/firefox` (API reports `fork: true`, parent confirmed).
- The diffable tag pair `stealth-base/v150.0.1` → `stealth-head/v150.0.1` resolves to
  **20 commits, 104 files, +14,279 / −59 lines**.
- **The default branch shows none of it.** `main` is 5 commits ahead of upstream,
  changing 2 files, both README/CI. The installed packages contain zero `.cc`/`.cpp`
  files and no `patches/` directory.
- **GitHub cannot render the shipping diff** — `last-mozilla-central...stealth/151`
  returns HTTP 422, "this diff is taking too long to generate".
- **The readable patch series is not public.** The branch's own
  `STEALTH_BRANCH_README.md` documents a numbered series (`0001-…` … `0015-…`)
  maintained in `feder-cr/firefox-stealth` — that repository returns **404**. You can
  regenerate an equivalent series yourself with `git format-patch` after cloning.

### The patches are substantive, not pref-flipping

Read at code level: 20+ `zoom.stealth.*` static prefs consumed by C++ getters (same
architecture as Camoufox's `MaskConfig`); canvas noise that skips sub-64×64 canvases to
avoid disturbing reCAPTCHA probes and **skips zero-valued channels specifically to
survive CreepJS's `clearRect` trap**, tuned "to stay below FP Pro's `tampering_ml`
threshold"; a complete **SOCKS5 UDP ASSOCIATE implementation** (+423 lines, plus +2,037
in nICEr) so WebRTC media can traverse a SOCKS proxy rather than leaking the host
address. Detector-aware engineering, comparable in ambition to Camoufox.

### Security finding: the browser phones home on every launch

`BrowserGlue.sys.mjs:392-408` fires a fire-and-forget `fetch()` to a GitHub release
asset at `final-ui-startup`, gated on `invisible_firefox.usage_ping.enabled`, which
`firefox.js:3618` defaults to **true**.

The request is benign — `credentials: "omit"`, `cache: "no-store"`, no payload, no
identifier — and it follows the configured proxy, with `failover_direct = False` and
`socks_remote_dns = True` set by the tool, so a dead proxy yields no direct fallback and
no DNS leak.

**The defect is placement.** Searching the entire `invisible_playwright` repository for
`usage_ping`, `launch counter`, `launch.txt` or `usage-counter` returns **0 matches**.
The disclosure lives in a different repository. Disable with
`extra_prefs={"invisible_firefox.usage_ping.enabled": False}`.

No other tool in this comparison makes an unsolicited network request at startup, so the
architecture matrix gains a **"Startup network traffic"** row.

### Nothing malicious found

No `eval`/`exec`, no `pickle.load`, no `shell=True`, no `verify=False` in either
installed package. The downloader performs real SHA-256 verification and **re-verifies
already-cached engines**, which is better practice than most tools here. The dependency
is pinned with an exact `==` specifier, with the rationale documented.

### Updated

README (tables, lineage diagram, capability index, health), STATUS.md,
CODE-REVIEW.md (metrics rows + finding 6), METHODOLOGY.md, `scripts/verify.py`,
and `docs/index.html` (tenth column, telemetry row, new filter, critical finding).

---

## 2026-08-14d — Interactive evidence matrix; GitHub-native docs

### Added

- **[`docs/index.html`](docs/index.html)** — a self-contained interactive view of the
  whole dataset: requirement filters, the architecture matrix with a tier chip on every
  claim, findings ordered by consequence, metric bars, and the lineage graph. No build
  step, no dependencies, GitHub Pages-ready.

  Design constraints, which follow from what this dataset is:

  - **Evidence tier is a first-class visual channel**, not a footnote. Tier is *ordinal
    confidence*, so it uses one hue dark→light rather than four categorical colours.
  - **Tier D is drawn hollow and dashed**, never the same as "does not implement" —
    it is also distinguished by shape, so identity is never colour-alone.
  - **No composite score, no ranking, no red/green ramp.** A quality ramp would
    reintroduce exactly the judgment this report removed. Colour encodes provenance and
    category; one reserved status colour is used only for the security finding.
  - **Interaction is requirement-led** ("I need X" → which tools implement it), matching
    how the decision is actually made, rather than presenting a winner.
  - Verified: contrast ≥ 4.5:1 for every text/background pair in both themes, no
    horizontal page overflow at 375 px, wide content scrolls in its own containers.

- **Lineage diagram** (mermaid, renders natively on GitHub) in the README. Nine tools
  reduce to five implementation families; Scrapling's browser tier *is* Patchright,
  SeleniumBase's CDP Mode is NoDriver-derived, and XDriver and Botasaurus's JS driver
  both descend from rebrowser-patches. Selecting two tools for redundancy can mean
  selecting one implementation twice. Every edge verified in source.

### Changed

- GitHub alert callouts for the points most often misread: the sponsorship disclosure,
  Tier D not being a negative finding, the unbenchmarked coverage table, the security
  finding, and the source-handling rule.
- Long metric tables in the code review collapsed behind `<details>` so the findings
  stay the first thing on the page.

---

## 2026-08-14c — Code review added

Added **[CODE-REVIEW.md](CODE-REVIEW.md)**: an engineering assessment of all nine
codebases covering structure, typing, tests, error handling, dependency hygiene, and
security-relevant patterns, with file-and-line citations. Metrics are reproducible via
`scripts/codemetrics.py`, which runs inside the sandbox and reads files as text/AST only.

### Findings

| Finding | Evidence |
|---------|----------|
| **CloakBrowser disables the Chromium sandbox on every launch** | `--no-sandbox` hardcoded in `cloakbrowser/config.py:54-66`. The arg merge (`browser.py:1395-1425`) overrides flags but cannot remove them; the only opt-out, `stealth_args=False`, also drops the fingerprint seed. Not mentioned in the project README. Combined with a closed binary: unauditable native code, no OS sandbox, hostile input |
| **XDriver ships a frozen bundle with no drift detection** | 295 lines of first-party Python, zero tests, prebuilt `playwright-core` 1.49.0 |
| **Patchright's patching is engineered to fail loudly** | `*OrThrow` ts-morph accessors throughout (47 in `crPagePatch.ts`, 40 in `framesPatch.ts`); `check_patch_impact.yml` diffs Playwright versions and can file an issue on breaking changes |
| **SeleniumBase is large and effectively untyped** | 99,701 production lines; `base_case.py` 17,670 lines / 579 methods / 2 classes; 2.7% of 3,902 functions annotated; 506 broad excepts; 548 sleep calls. Its 42 `shell=True` calls are all in `console_scripts/` CLI tooling, not the driving path |
| **Obscura relies on panic-on-failure** | 2,326 `.unwrap()` in production Rust, concentrated in CDP handlers (`io.rs` 18, `domsnapshot.rs` 10, `target.rs` 8); `catch_unwind` in only four files |
| **Botasaurus swallows errors; driver is untested** | 38 bare `except:`; `botasaurus-driver` has zero test files across 50,169 lines |
| **Scrapling has the cleanest Python in the set** | 83.5% annotation coverage, 59.1% docstrings, 0 bare excepts, 59 test files, the only pre-commit config |

### Method note

An earlier draft of the metrics applied vendored-directory exclusions to the line counts
but not to the pattern searches, and reported 116 `eval` calls in a 295-line project
because it was scanning a bundled Playwright tree. Both passes now share the same
exclusions, and tests are separated from production code. The corrected figures are the
ones published.

---

## 2026-08-14b — Full claim re-verification; all evaluative content removed

Re-verified every asserted numeric and behavioural claim against source, and removed
remaining subjective content so the report states only what is checkable.

### Claims corrected on re-verification

Three were wrong in the 2026-08-14a revision published earlier the same day; two had
been wrong since before it.

| Claim | Prior state | Verified state |
|-------|-------------|----------------|
| SeleniumBase `Runtime.enable` handling | Stated as handled via CDP Mode (also asserted in the July revision) | **No handling located in source.** Downgraded to Tier D. CDP Mode attaches no WebDriver, but no explicit countermeasure exists in the tree |
| CloakBrowser `Runtime.enable` handling | Stated as a C++ patch (also asserted in the July revision) | **Not addressed in the wrapper README's patch list**, and the binary is closed. Downgraded to Tier D |
| SeleniumBase input simulation | Stated as present | **No mouse-motion model exists.** Input realism is OS-level PyAutoGUI clicks (`browser_launcher.py:1071-1082`) plus timing jitter. Zero Bézier/trajectory matches in the tree |
| Camoufox patch count | 32 stealth patches + 2 Playwright | **34** in `patches/` + **2** in `patches/playwright/` |
| XDriver bundle package name | Asserted the name was misspelled "turnstilebroweser" in source | The name is **`turnstilebrowser-playwright-core`**, spelled correctly. The typo claim was false |
| XDriver original code size | "~200 lines" | **295 lines** across `x_driver/*.py` |

Also verified as correct and left unchanged: Camoufox Firefox base 152.0.4 and 3
`humanize` config properties; Patchright driver patch 265 lines; Clearcote 32 patches on
Chromium 149.0.7827.114; Botasaurus 58 CDP binding files and zero Selenium imports;
SeleniumBase 4.51.12 and 187 CDP-related files; Scrapling 0.4.14 with `curl_cffi>=0.16.0`
and `patchright>=1.61.2`; Obscura render engine 66,826 lines with `default = []`;
CloakBrowser 71 patches on Chromium 150 and 58 on 146.

### Evaluative content removed

- **All star ratings deleted** (previously 40+ cells across five pages). Labelling them
  as editorial was insufficient; they are replaced by mechanism descriptions and
  measurable facts.
- **Per-tool "Assessment" blocks** replaced with technical-summary tables stating
  verified state and evidence tier per property.
- **"Best for" / "Best Use" / "Recommendation" lines** replaced with applicability
  statements naming the verified capability and the constraints that bound it.
- **Evaluative vocabulary removed** throughout: "best-in-class", "gold standard",
  "excellent", "superior", "honest assessment", "disqualifying", "reality check",
  "impossible to detect", and comparable terms.
- **README decision guide** replaced with a capability-to-implementation index derived
  from the architecture tables — a lookup, not a ranking.
- **Overstatement corrected**: "impossible for JavaScript to detect" (Camoufox) now
  states which specific detection methods the mechanism defeats and notes the residual
  SpiderMonkey signal the project itself documents.

### Structural changes

- README no longer duplicates generated counts. Stars, forks, contributors, open issues,
  and versions live only in [STATUS.md](STATUS.md). Cross-checking found the Camoufox
  open-issue count had already drifted (121 → 122) within hours of being written.
- Every table verified well-formed; every internal link and anchor verified to resolve.

---

## 2026-08-14a — Objectivity pass + refresh against upstream

Re-verified all nine tools against upstream source and published releases, and
reworked the report's evidence handling. The previous revision was dated 2026-07-06;
seven of the nine tools had shipped releases since.

### Corrections — claims that were wrong or unsupported

| Claim (previous revision) | Status | Correction |
|---------------------------|--------|------------|
| **Obscura has no layout engine**; `getBoundingClientRect` "returns 0s", `getComputedStyle` "stubs" | **Obsolete** | v0.2.0 (2026-08-08) added a native Rust rendering engine — block/inline layout, flexbox, grid, tables, floats, transforms, plus screenshots and PDF export. Verified: `crates/obscura-render`, ~66.8k LOC; `getComputedStyle` is now renderer-computed. |
| CloakBrowser "66 source-level patches" (Chromium 148) | **Stale** | Pro binary is now Chromium 150 with **71** patches; free is 146/58; macOS free is 145/26. Verified in the project's own platform table. |
| CloakBrowser "33 C++ patches" (Strategy 6) | **Stale + self-contradictory** | Contradicted the same file's "66" and the tool page's explicit note that 33 was outdated. Removed. |
| 7 services × 9 tools ✅/⚠️/❌ coverage grid | **Unsupported** | 63 verdicts presented as measurement, none benchmarked. Replaced with a provenance table recording *who claims what* and at which evidence tier. |
| "Realistic Success Rates" (90%+, 60–80%, 20–40%, <20%) | **Unsourced** | No targets, sample size, or dates behind the figures. Replaced with the qualitative factors that dominate outcomes. |
| Five-star capability ratings across ~15 rows | **Unfalsifiable** | No rubric defined the scale and no evidence backed any cell. Replaced with a source-verified architecture matrix (Tier A facts) plus a capability-to-implementation index. |
| Sponsorship shown without conflict-of-interest context | **Incomplete** | The sponsor is a commercial competitor to every tool rated. Now disclosed up front, with the mitigations stated. |

### Version refresh (verified 2026-08-14)

| Tool | Was documented | Now |
|------|----------------|-----|
| Camoufox | browser `v152.0.2-alpha`, py `0.4.11` | browser **`v152.0.4-beta.28`** (2026-07-19), py **`0.5.4`** |
| Patchright | `1.61.x` | unchanged — driver/Node `1.61.1`, Python `1.61.2` |
| SeleniumBase | `4.50.5` | **`4.51.12`** (2026-08-10, CDP Mode patch 128) |
| Botasaurus | core `4.0.97`, driver `4.0.92` | core unchanged; driver **`4.0.101`** on PyPI (repo `setup.py` still reads 4.0.92 — PyPI is ahead of GitHub) |
| XDriver | `v1.0.1`, dormant | unchanged — still no commits since 2025-09-10 |
| CloakBrowser | wrapper `0.4.8`, Chromium 148 Pro | wrapper **`0.5.7`**, Pro **Chromium 150** |
| Scrapling | `0.4.10` | **`0.4.14`** (2026-08-10) |
| Obscura | `v0.1.9` | **`v0.2.0`** (2026-08-08) — see correction above |
| Clearcote | browser `pre.17`, SDK `0.11.1` | browser **`pre.22`**, SDK **`0.26.1`** (Chromium base still 149) |

### Added

- **[METHODOLOGY.md](METHODOLOGY.md)** — evidence tiers, scope, what was not tested,
  conflict-of-interest policy, and how to challenge a claim.
- **[STATUS.md](STATUS.md)** — generated version and project-health tables.
- **[`scripts/verify.py`](scripts/verify.py)** — regenerates STATUS.md from PyPI, npm,
  and the GitHub API. Stdlib only.
- **[`scripts/sandbox.sh`](scripts/sandbox.sh)** — clones the upstream trees into a
  hardened, network-severed Docker container so unaudited code is never cloned onto or
  executed on a workstation.
- Project-health signals chosen for build decisions: license, last push, contributor
  count (bus factor), open issues.

### Changed

- Title and framing moved from "Anti-Bot Bypass Tools" to a comparison framing;
  headline superlatives removed in favour of scoped statements.
- Sponsor blurb rewritten to describe the product without circumvention wording or
  third-party vendor names — nominative references to vendors remain throughout the
  editorial sections, where they are necessary and appropriate.
- Duplicate SEO keyword blocks consolidated to one.

---

## 2026-07-06 — Refresh against current source

Re-verified all tool analyses and the README against upstream (July 2026).

## Earlier

Added Clearcote; added CloakBrowser, Scrapling, Obscura; initial analyses.
