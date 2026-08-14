# Anti-Detect Browser Tools — Technical Comparison

> Source-verified comparison of nine open-source browser-automation and anti-detection
> tools. Every non-obvious claim carries an **evidence tier**, so you can tell what was
> read out of the source from what a vendor asserted on their own README.

[![Last verified](https://img.shields.io/badge/last%20verified-2026--08--14-brightgreen)](STATUS.md)
[![Methodology](https://img.shields.io/badge/methodology-documented-blue)](METHODOLOGY.md)
[![Tools tracked](https://img.shields.io/badge/tools-9-informational)](#the-nine-tools)

**Last verified: 2026-08-14.** Versions and project health are machine-generated —
see **[STATUS.md](STATUS.md)**, regenerate with `python scripts/verify.py --write`.
Method, limits, and how to challenge a claim: **[METHODOLOGY.md](METHODOLOGY.md)**.

---

## Disclosure

**This repository is sponsored by [Scrappey](https://scrappey.com/), a commercial
web-data API — a paid alternative to running the tooling reviewed here.** The sponsor
has an obvious interest in how self-hosted tools are portrayed, so:

- **Scrappey is not rated.** It appears in no matrix, no coverage table, and no
  recommendation. A sponsor cannot win a comparison it is excluded from.
- **Every vendor gets identical skepticism**, sponsor included. No hosted service's
  claims are reproduced here either.
- If you think a judgment is shaded by the sponsorship, [open an issue](../../issues)
  quoting it. That is a bug like any other.

Full policy: [METHODOLOGY.md § Conflict of interest](METHODOLOGY.md#conflict-of-interest).

---

## Why this exists

Every tool in this space claims to be undetectable. Most of that is marketing, and
most comparisons repeat it — including, until this revision, this one.

What this report does differently:

- **Reads the source.** Claims tagged **Tier A** were verified in the actual code at a
  known commit, in an isolated container.
- **Separates verified from claimed.** A vendor's benchmark is evidence of what the
  vendor saw. It is labelled as such, never as measurement.
- **Says what it doesn't know.** No head-to-head anti-bot benchmark was run here, so
  no "beats X" claim in this repo is better than second-hand. Sections that used to
  imply otherwise have been rewritten.
- **Regenerates its own facts.** Versions drift within weeks; a script refreshes them.

### Evidence tiers

| Tier | Meaning |
|:----:|---------|
| **A** | **Verified in source** — read at a known commit, file cited |
| **B** | **Vendor-reported** — the maintainer claims it; not reproduced here |
| **C** | **Community-reported** — issues, forums, anecdote |
| **D** | **Not established** — no evidence found either way (*not* a mark against the tool) |

---

## The nine tools

| Tool | What it actually is | Language | License | Analysis |
|------|--------------------|----------|---------|----------|
| **Camoufox** | Firefox fork with fingerprint spoofing compiled into C++ | Python | MPL-2.0 | [Read →](./camoufox.md) |
| **Patchright** | Playwright driver with automation tells patched out at build time | Python, Node, .NET | Apache-2.0 | [Read →](./patchright.md) |
| **SeleniumBase** | Test framework + patched ChromeDriver (UC Mode) + CDP-native driver | Python | MIT | [Read →](./seleniumbase.md) |
| **Botasaurus** | Raw-CDP driver + scraping framework with human-input simulation | Python | MIT | [Read →](./botasaurus.md) |
| **XDriver** | File-swap patcher shipping a prebuilt `playwright-core` fork | Python | Apache-2.0 | [Read →](./xdriver.md) |
| **CloakBrowser** | Chromium fork with C++ patches; open wrapper, proprietary binary | Python, Node, .NET | MIT wrapper / proprietary binary | [Read →](./cloakbrowser.md) |
| **Scrapling** | Scraping framework: HTTP/browser tiers, parser, spider | Python | BSD-3-Clause | [Read →](./scrapling.md) |
| **Obscura** | Browser engine written from scratch in Rust | Rust, CDP clients | Apache-2.0 | [Read →](./obscura.md) |
| **Clearcote** | ungoogled-chromium fork; open patches, real-fingerprint import | Python, Node | BSD-3-Clause | [Read →](./clearcote.md) |

Current versions, release dates, stars, contributor counts, and last-push dates are in
**[STATUS.md](STATUS.md)** — generated, so they cannot silently rot.

> **Changed since the July 2026 revision:** seven of nine tools shipped releases.
> Most consequential: **Obscura v0.2.0 added a real layout and rendering engine**,
> invalidating this report's previous "no layout engine" analysis, and **CloakBrowser's
> Pro binary moved to Chromium 150 with 71 patches** (previously documented as 148/66,
> and as "33" in one stale sentence). See [CHANGELOG.md](CHANGELOG.md).

---

## Architecture — what each tool actually does

**Tier A.** Read from source in the sandbox; these are mechanical facts, not ratings.
Where a tool delegates to another, that is stated rather than credited to it.

| | Camoufox | Patchright | SeleniumBase | Botasaurus | XDriver | CloakBrowser | Scrapling | Obscura | Clearcote |
|---|---|---|---|---|---|---|---|---|---|
| **Browser engine** | Firefox 152 fork | stock Chromium | stock Chromium | stock Chromium | stock Chromium | Chromium fork | delegates | own Rust engine | Chromium fork (ungoogled) |
| **Where the stealth lives** | C++ source patches (**34** patch files) | AST rewrite of the Playwright driver (`ts-morph`, 265-line patch script) | patched ChromeDriver + CDP-native driver | raw CDP from Python | prebuilt patched `playwright-core` bundle | C++ source patches (**71** on Pro/Chromium 150) | delegates to Patchright / Camoufox | JS shims in its own runtime | C++ patches (**32**) on Chromium 149 |
| **`navigator.webdriver`** | C++ | driver patch | driver patch | CDP | bundled patch | C++ | inherited | runtime shim | C++ (`010-user-agent-and-webdriver`) |
| **`Runtime.enable` tell** | N/A — uses Juggler, not CDP | avoided via isolated execution contexts; Console API disabled | CDP Mode | not addressed | rebrowser-derived patch | C++ patch | inherited | own CDP server | patch `110-runtime-enable` |
| **TLS/JA3 impersonation** | no — real Firefox TLS | no — real Chrome TLS | no | no | no | no | **yes** — `curl_cffi` (HTTP tier only) | **optional** — `wreq` behind `--features stealth` | no — real Chrome TLS |
| **Real layout & rendering** | yes (Gecko) | yes (Blink) | yes (Blink) | yes (Blink) | yes (Blink) | yes (Blink) | yes (browser tier) | **yes since v0.2.0** — own engine, 66.8k LOC; on in prebuilt archives, `--features render` from source | yes (Blink) |
| **HTML parser included** | no | no | no | no | no | no | **yes** | **yes** (`html5ever`) | no |
| **Crawler / spider** | no | no | no | yes | no | no | **yes** | no | no |
| **Human input simulation** | yes | no | yes | yes (Bézier) | no | yes | no | no | yes (trusted CDP) |
| **Ships a binary you can't read** | no | no | no | no | yes (prebuilt bundle) | **yes** (Pro/free binaries) | no | no | no |

**Reading notes.**

- *"Delegates"* is not a weakness — Scrapling wiring Patchright and Camoufox into a
  framework is a legitimate design. It does mean Scrapling's browser-tier evasion is
  Patchright's evasion, and inherits its strengths and failures. Verified: Scrapling's
  `pyproject.toml` pins `patchright>=1.61.2` and `curl_cffi>=0.16.0`.
- *Patch counts are not quality.* 71 patches is not "2.2× better" than 32. Different
  projects split changes differently. The number tells you the surface area touched.
- *No TLS impersonation is normal.* Real-browser tools have real browser TLS, which is
  correct by construction. It matters only for the HTTP-only tiers.

---

## Anti-bot service coverage — what is claimed, and by whom

**This is the section most likely to mislead you elsewhere, including in the previous
version of this document.**

The earlier revision presented a 7-services × 9-tools grid of ✅ / ⚠️ / ❌ — 63 verdicts
implying measurement. **No benchmark was ever run to produce them.** That grid has been
removed rather than refreshed.

What can be stated honestly is *who claims what*:

| Tool | Services the project itself claims | Evidence | Notes |
|------|-----------------------------------|:--------:|-------|
| **Patchright** | Cloudflare, Kasada, Akamai, DataDome | **B** | Listed with ✅ in its own README; no methodology published |
| **XDriver** | Cloudflare WAF, Turnstile, DataDome, Kasada | **B** | Claims are from Sept 2025 and the bundle is pinned to `playwright-core` 1.49.0 — **stale by construction**; no commits since 2025-09-10 |
| **Botasaurus** | Cloudflare WAF, Turnstile, DataDome | **B** | Links live demo targets; markets itself as building "undefeatable" scrapers |
| **CloakBrowser** | Turnstile, FingerprintJS, reCAPTCHA v3 score 0.9, "30+ detection sites" | **B** | **Pro binary only.** The free binary is not claimed to reach these numbers |
| **SeleniumBase** | A Cloudflare challenge page | **B** | Narrower and more checkable than most: ships a runnable example script rather than a grid |
| **Scrapling** | Cloudflare Turnstile | **B** | Notably candid — its README *defers* Akamai, DataDome, Kasada and Incapsula to a third-party paid API rather than claiming them |
| **Camoufox** | *none* | **D** | Makes no service claims at all; its README instead **documents a limitation** (some WAFs probe SpiderMonkey engine behaviour, which a Firefox fork cannot hide) |
| **Obscura** | *none* | **D** | No anti-bot service claims in the README |
| **Clearcote** | *none* | **D** | Explicitly positions as a privacy/coherence browser; publishes open-auditor results (CreepJS), not WAF pass rates |

**How to read this table.** It is a map of marketing, not of capability. Three things
follow from it that a ✅/❌ grid would have hidden:

1. **A blank row is not a weak tool.** Camoufox and Clearcote make no service claims
   and are among the most technically serious projects here. Silence often means the
   maintainer declines to claim what they cannot measure.
2. **The loudest claims come from the least maintained project.** XDriver asserts the
   broadest coverage and has not been touched since September 2025.
3. **Vendor ✅s are not comparable across projects.** Each used its own targets, dates,
   IPs, and pass criteria — none published. Two ✅s in the same column may mean very
   different things.

If you need real coverage numbers for *your* targets, you have to test against them,
with your own proxies. Nobody's table substitutes for that.

---

## Project health

Full generated table in **[STATUS.md](STATUS.md)**. The parts that should change a
build decision:

| Signal | What to watch for | Current outliers (2026-08-14) |
|--------|-------------------|-------------------------------|
| **License** | Copyleft or proprietary components affect what you can ship | CloakBrowser: MIT wrapper, **proprietary binary**. Camoufox: MPL-2.0 |
| **Bus factor** | One-maintainer projects can stop overnight | **Clearcote: 1 contributor.** XDriver: 2 |
| **Actually maintained** | Anti-detection rots fast; a stale repo is a liability | **XDriver: no commits in ~11 months** — treat as abandoned |
| **Issue backlog** | Unresponsive maintainers surface here | CloakBrowser: 194 open. Camoufox: 121 |

Stars are in STATUS.md for completeness, but popularity is not stealth — Scrapling has
~74k stars and openly defers the hardest protections to a paid third party.

---

## Decision guide

**Editorial, not measured.** This is the report author's judgment given the
architecture above. Reasoning is stated so you can disagree with the reasoning.

| If you need… | Consider | Because |
|--------------|----------|---------|
| Fingerprint spoofing JS cannot detect | [Camoufox](./camoufox.md), [Clearcote](./clearcote.md), [CloakBrowser](./cloakbrowser.md) | Spoofing lives in C++; there is no JS wrapper to catch |
| Statistical fingerprint rotation | [Camoufox](./camoufox.md) | BrowserForge-generated fingerprints with real-world distributions |
| To present a *specific real machine* | [Clearcote](./clearcote.md) | Imports a captured profile and ships a verifier to confirm it loaded |
| A drop-in for existing Playwright code | [Patchright](./patchright.md) | Same API, patched driver. Prefer it over XDriver, which is the dormant repackage |
| CAPTCHA solving in-framework | [SeleniumBase](./seleniumbase.md) | Built-in click/slide solving; the only one here that seriously attempts it |
| Human-like mouse behaviour | [Botasaurus](./botasaurus.md), [CloakBrowser](./cloakbrowser.md) | Bézier-curve cursor paths; CloakBrowser exposes it as one flag |
| An all-in-one scraping stack | [Scrapling](./scrapling.md) | Fetching, parsing, crawling, stealth in one package |
| HTTP-only speed with TLS impersonation | [Scrapling](./scrapling.md) | `curl_cffi` tier — no browser, ~10 MB per worker |
| High concurrency on ordinary pages | [Obscura](./obscura.md) | ~30 MB per instance; now renders properly since v0.2.0 |
| To audit and rebuild the browser yourself | [Clearcote](./clearcote.md) | 32 readable patches, signed builds, reproducibility as a stated goal |
| Node.js or .NET | [Patchright](./patchright.md), [CloakBrowser](./cloakbrowser.md), [Clearcote](./clearcote.md) | Multi-language SDKs |
| To avoid proprietary binaries | anything **except** CloakBrowser | Only CloakBrowser's engine is closed |

**Not recommended:** [XDriver](./xdriver.md) for new work. It is a repackaged
`rebrowser-patches` fork pinned to `playwright-core` 1.49.0, unmaintained since
September 2025. Use Patchright, which is the maintained expression of the same idea.

---

## How bot detection actually works

Understanding the layers explains why no single tool covers all of them.

```
┌──────────────────────────────────────────────────────────────────────────┐
│  Layer 1 · Protocol / automation tells                                   │
│  ├─ Runtime.enable timing          Patchright, CloakBrowser, Clearcote   │
│  ├─ Execution-context leaks        Patchright                            │
│  ├─ CDP input characteristics      CloakBrowser, Clearcote               │
│  └─ Juggler instead of CDP         Camoufox (Firefox — sidesteps it)     │
├──────────────────────────────────────────────────────────────────────────┤
│  Layer 2 · Browser fingerprinting                                        │
│  ├─ navigator.webdriver            all tools                             │
│  ├─ Canvas / WebGL                 Camoufox, CloakBrowser, Clearcote     │
│  ├─ Screen / window geometry       Camoufox, CloakBrowser, Clearcote     │
│  ├─ AudioContext                   Camoufox, CloakBrowser, Clearcote     │
│  └─ Font enumeration               Camoufox, CloakBrowser, Clearcote     │
├──────────────────────────────────────────────────────────────────────────┤
│  Layer 3 · Behaviour                                                     │
│  ├─ Mouse movement                 Botasaurus, CloakBrowser, Camoufox    │
│  ├─ Click / keystroke timing       Botasaurus, SeleniumBase, CloakBrowser│
│  └─ Navigation patterns            your code's problem, not the tool's   │
├──────────────────────────────────────────────────────────────────────────┤
│  Layer 4 · Network                                                       │
│  ├─ TLS fingerprint (JA3/JA4)      Scrapling (curl_cffi), Obscura (wreq) │
│  ├─ WebRTC / UDP leakage           Camoufox, Clearcote                   │
│  ├─ IP reputation                  no tool fixes this — use proxies      │
│  └─ DNS leakage                    use SOCKS5H proxies                   │
├──────────────────────────────────────────────────────────────────────────┤
│  Layer 5 · Layout & rendering probes                                     │
│  ├─ getBoundingClientRect          real browsers; Obscura v0.2.0 render  │
│  ├─ getComputedStyle               real browsers; Obscura v0.2.0 render  │
│  └─ Actual canvas/WebGL output     real-browser tools; Clearcote can     │
│                                    forward to real GPU hardware          │
│  Note: Obscura only clears this layer in a render-enabled build.         │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## What actually determines whether you get through

The previous revision published a table of success-rate percentages by protection tier
(«90%+», «20-40%»…). **Those numbers had no study behind them** — no targets, no sample
size, no dates — so they have been removed rather than adjusted. Precision you cannot
source is worse than an honest qualitative answer.

What is defensible, and consistent across practitioner accounts:

| Factor | Why it dominates |
|--------|------------------|
| **IP reputation** | Routinely decides the outcome before a single fingerprint is read. Excellent stealth on a flagged datacenter IP loses to mediocre stealth on clean residential. |
| **Request patterns** | Volume, timing regularity, and path order identify automation that no fingerprint patch touches. |
| **Tier of the same product** | "Cloudflare" is not one system. Free, Pro, Business, and Enterprise configurations differ enormously — claims rarely say which was tested. |
| **Account and session age** | On logged-in targets, history often outweighs the browser entirely. |
| **Time** | Detection is adversarial. Any result decays; a passing test proves *that target, that day*. |
| **The tool** | Real, and necessary — but usually not the binding constraint once the above are wrong. |

The honest summary: tooling gets you to the starting line. Infrastructure and
behaviour determine whether you finish.

---

## Detection test sites

Useful for checking your own setup. All are consistency auditors or demos — passing
them is **not** evidence of defeating a commercial WAF.

| Test | What it checks | URL |
|------|----------------|-----|
| Sannysoft | Basic automation tells | [bot.sannysoft.com](https://bot.sannysoft.com/) |
| BrowserScan | Broad fingerprint surface | [browserscan.net](https://www.browserscan.net/bot-detection) |
| CreepJS | Fingerprint coherence and lies | [abrahamjuliot.github.io/creepjs](https://abrahamjuliot.github.io/creepjs/) |
| Fingerprint.com | Commercial bot-detection demo | [fingerprint.com](https://fingerprint.com/products/bot-detection/) |
| Pixelscan | Leak and consistency detection | [pixelscan.net](https://pixelscan.net/) |

---

## Reproduce this report

```bash
python scripts/verify.py --write     # refresh STATUS.md from PyPI / npm / GitHub
```

Source verification runs in an isolated container, never on a workstation — the trees
are unaudited third-party code:

```bash
./scripts/sandbox.sh up              # clone into a Docker volume, then cut the network
./scripts/sandbox.sh sh              # offline shell for reading the source
./scripts/sandbox.sh nuke            # destroy container and volume
```

Nothing from those repos is installed, built, or executed to produce this report.
Details: [METHODOLOGY.md § Source handling](METHODOLOGY.md#source-handling).

---

## Contributing

Corrections are welcome, especially ones that move a claim up a tier. Open an issue
with the claim quoted and either a file + commit that contradicts it, vendor
documentation that supersedes it, or a reproducible test with methodology attached
(target, IP type, trial count, dates).

New tools: include the repository URL, the anti-detection approach, and what it claims
to handle.

---

## Disclaimer

For security research, academic study, authorised testing, and retrieving your own
data. Respect `robots.txt`, rate limits, and terms of service. Laws on automated access
vary by jurisdiction — this document is not legal advice.

---

<!--
Repository topics: web-scraping, anti-detection, bot-detection, browser-automation,
fingerprint-spoofing, stealth-browser, playwright, selenium, puppeteer, cdp,
browser-fingerprinting, camoufox, patchright, seleniumbase, botasaurus, cloakbrowser,
scrapling, obscura, clearcote, firefox-automation, chromium, rust, web-automation
-->

<p align="center">
  <i>Read the source. Check the date. Distrust the grid.</i>
</p>
