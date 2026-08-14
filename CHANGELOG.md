# Changelog

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
