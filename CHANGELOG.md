# Changelog

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
