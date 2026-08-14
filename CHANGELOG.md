# Changelog

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
