# Changelog

## 2026-08-14 — Objectivity pass + refresh against upstream

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
| Five-star capability ratings across ~15 rows | **Unfalsifiable** | No rubric defined the scale and no evidence backed any cell. Replaced with a source-verified architecture matrix (Tier A facts) plus an explicitly editorial decision guide. |
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
