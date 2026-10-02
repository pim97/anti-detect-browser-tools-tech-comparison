# Scrapling - Deep Technical Analysis

> **Tool Type:** All-in-One Web Scraping Framework (Fetching + Parsing + Crawling + Stealth)
> **Repository:** [github.com/D4Vinci/Scrapling](https://github.com/D4Vinci/Scrapling)
> **Approach:** Three-tier fetching (HTTP/Dynamic/Stealth) + adaptive element tracking + spider framework
> **What is verified:** `pyproject.toml` requires `curl_cffi>=0.16.1` (HTTP-tier TLS impersonation) and `patchright>=1.62.1` (minimum versions, not exact pins) — **the browser-tier evasion is Patchright's**, inherited wholesale rather than implemented here (**Tier A**)
> **Anti-bot service claims:** Cloudflare Turnstile handled out of the box (**Tier B**). The README's sponsor table (line 134) **lists a third-party paid token API for Akamai, DataDome, Kasada and Incapsula** rather than claiming coverage of them.
> **Maintenance:** latest release **v0.4.15** (2026-08-23); 0.4.11–0.4.15 added feed spiders, AutoThrottle, a reworked 13-tool MCP server, and browser-tab reuse. No release since; the 15 commits after the v0.4.15 tag touch only README, docs, images and `zensical.toml`. 84.6k stars, 31 contributors, 9 open issues. BSD-3-Clause.
> **Verified:** 2026-09-30 against `D4Vinci/Scrapling` @ `b11da90`.

---

## Table of Contents

- [What is Scrapling?](#what-is-scrapling)
- [How It Works](#how-it-works)
- [Anti-Detection Mechanisms](#anti-detection-mechanisms)
- [Adaptive Element Tracking](#adaptive-element-tracking)
- [Performance](#performance)
- [Spider Framework](#spider-framework)
- [CLI & MCP Server](#cli--mcp-server)
- [Pros and Cons](#pros-and-cons)
- [Installation & Usage](#installation--usage)
- [Comparison with Alternatives](#comparison-with-alternatives)
- [When to Use](#when-to-use)

---

## What is Scrapling?

Scrapling is an **all-in-one Python web scraping framework** that bundles fetching, parsing, anti-detection, crawling, and AI integration into a single package. Unlike the other tools in this repository that focus solely on browser stealth, Scrapling is a full scraping pipeline.

**Key differentiator:** It combines several worlds — `curl_cffi` for TLS-impersonated HTTP requests, [Patchright](./patchright.md) for CDP stealth on a Chromium browser, a Scrapy-like spider framework, and a fast lxml-based parser — all behind a unified API. Its adaptive element tracking system can auto-relocate selectors when websites change their DOM structure.

**What makes it different from the other tools analyzed here:** The tools in this repo ([Camoufox](./camoufox.md), [Patchright](./patchright.md), [SeleniumBase](./seleniumbase.md), etc.) are **browser automation stealth tools**. Scrapling is a **scraping framework** that *uses* one of them (Patchright) under the hood for its stealth tier, and layers fetching / parsing / crawling on top. It's a layer above, not a competitor.

**Project facts (verified against source, 2026-09-30):**

| Attribute | Value | Evidence |
|-----------|-------|----------|
| Current version | **0.4.15** | `pyproject.toml` `version = "0.4.15"`, `scrapling/__init__.py` `__version__ = "0.4.15"`; GitHub release `v0.4.15` and PyPI upload 2026-08-23 |
| Release cadence | point releases between 1 day and 4 weeks apart from June to August 2026; none after 0.4.15 as of 2026-09-30 | `CHANGELOG.md`: 0.4.15 (Aug 23), 0.4.14 (Aug 10), 0.4.13 (Aug 9), 0.4.12 (Jul 26), 0.4.11 (Jul 12), 0.4.10 (Jul 4) |
| Last commit | 2026-09-29 (`b11da90`, docs/sponsor edit); last commit touching `scrapling/`, `tests/` or `pyproject.toml`: 2026-08-23 (`3e03f78`) | `git log -1` on the sandboxed clone; `git diff --stat v0.4.15..HEAD` lists only README, docs, images, `zensical.toml` |
| Community | 84,635 stars, 31 contributors, 9 open issues | GitHub API |
| Language | **Python only** (CPython) | `Programming Language :: Python :: 3 :: Only` classifier |
| Python versions | **3.10 – 3.13** | `requires-python = ">=3.10"` |
| License | **BSD 3-Clause** | `LICENSE`; `License :: OSI Approved :: BSD License` |
| Author/maintainer | Karim Shoair (D4Vinci) | `pyproject.toml` authors |
| Dev status | `4 - Beta` | `pyproject.toml` classifier |

> **Correction vs. previous edition of this page:** the page previously said "v0.4.2" and described StealthyFetcher as "Patchright **or Camoufox**" with a `use_camoufox=True` switch. Since **0.3.13** (2026-01-01; `CHANGELOG.md:562-566`) **the package no longer uses Camoufox** (an earlier revision of this page dated that to 0.4.10) — `rg -i camoufox scrapling/ pyproject.toml tests/` returns nothing, `camoufox` is not a dependency in `pyproject.toml`, and no `use_camoufox` parameter exists. StealthyFetcher is now a **Chromium/Patchright-only** engine. The upstream docs keep a user-side recipe for swapping Camoufox back in by subclassing `StealthySession` (`docs/fetching/stealthy.md:264-340`); it is not part of the package. See [Anti-Detection Mechanisms](#anti-detection-mechanisms).

> **Corrections in the 2026-09-30 re-verification:** (1) the benchmark tables now match the README (the earlier figures, e.g. 2.02 ms / 1,584.31 ms / ~784x, do not appear in it); (2) the MCP server registers 13 tools through `MCPServer` from the `mcp` SDK, not 10 through `FastMCP` (13 since 0.4.15); (3) `patchright` and `playwright` are minimum versions (`>=`), not exact pins; (4) with `impersonate` set, request headers come from `curl_cffi`, not `browserforge`; (5) `SQLiteStorageSystem` is described by what its code sets (`check_same_thread=False`, `RLock`, WAL), not a "mode 1" setting; (6) `scrapling install` runs Playwright's Chromium and system-dependency install, not a fingerprint download; (7) `dns_over_https` and `block_ads` are also accepted by `DynamicFetcher`.

---

## How It Works

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                     SCRAPLING ARCHITECTURE                           │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌─────────────────────────────────────────────────────────┐        │
│  │                   SPIDER FRAMEWORK                       │        │
│  │  ┌──────────┐  ┌──────────┐  ┌───────────────────────┐ │        │
│  │  │ Requests │  │ Callbacks│  │ Pause/Resume          │ │        │
│  │  │ Scheduler│  │ (parse)  │  │ (Checkpoint System)   │ │        │
│  │  └──────────┘  └──────────┘  └───────────────────────┘ │        │
│  │  robots.txt · proxy rotation · streaming · CrawlStats   │        │
│  └───────────────────────┬─────────────────────────────────┘        │
│                          │                                           │
│  ┌───────────────────────▼─────────────────────────────────┐        │
│  │              THREE-TIER FETCHING SYSTEM                   │        │
│  │                                                           │        │
│  │  Tier 1: Fetcher          Tier 2: DynamicFetcher         │        │
│  │  ┌──────────────────┐    ┌──────────────────────────┐   │        │
│  │  │ curl_cffi        │    │ Playwright (Chromium)    │   │        │
│  │  │ TLS impersonation│    │ JS rendering             │   │        │
│  │  │ Chrome/FF/Safari │    │ Network idle detection   │   │        │
│  │  │ no browser proc  │    │ full browser process     │   │        │
│  │  │ TLS impersonated │    │ real Chrome TLS          │   │        │
│  │  └──────────────────┘    └──────────────────────────┘   │        │
│  │                                                           │        │
│  │  Tier 3: StealthyFetcher                                 │        │
│  │  ┌──────────────────────────────────────────────────┐   │        │
│  │  │ Patchright (Chromium, CDP stealth)               │   │        │
│  │  │ Canvas noise flag        Cloudflare auto-solve    │   │        │
│  │  │ WebRTC → proxy-only      Timezone/locale match    │   │        │
│  │  │ WebGL toggle             real_chrome / cdp_url    │   │        │
│  │  │ full browser process, CDP tells patched out      │   │        │
│  │  └──────────────────────────────────────────────────┘   │        │
│  └───────────────────────┬─────────────────────────────────┘        │
│                          │                                           │
│  ┌───────────────────────▼─────────────────────────────────┐        │
│  │               PARSER / SELECTOR ENGINE                    │        │
│  │  lxml + cssselect (CSS3, XPath, Regex, Text search)      │        │
│  │  Adaptive element tracking (SQLite / custom backends)     │        │
│  │  Similar element finding (fuzzy structural matching)      │        │
│  │  orjson serialization (~10x faster than stdlib json)      │        │
│  └─────────────────────────────────────────────────────────┘        │
│                                                                      │
│  ┌─────────────────────────────────────────────────────────┐        │
│  │  CLI: shell / extract / mcp   │   MCP Server (13 tools)   │        │
│  │  Scrapy integration (@scrapling_response decorator)      │        │
│  └─────────────────────────────────────────────────────────┘        │
└─────────────────────────────────────────────────────────────────────┘
```

**API note (changed in 0.3):** the fetchers are now driven through **classmethods** and a `.fetch()` entrypoint, not instance construction. `Fetcher.get(...)`, `StealthyFetcher.fetch(...)`, and `DynamicFetcher.fetch(...)` are the current shapes (`scrapling/fetchers/requests.py` decorates `get`/`post` with `@classmethod`; `scrapling/fetchers/stealth_chrome.py` exposes `fetch`). The old `Fetcher(auto_match=False).get(...)` instance style and the `auto_match=` keyword were renamed — the adaptive feature is now the `adaptive` attribute/keyword. Persistent `FetcherSession` / `DynamicSession` / `StealthySession` classes (added in 0.3) are the way to reuse a browser/session across requests. Since 0.4.15 the browser sessions keep their tabs open after a request and reuse a free tab (the request's settings are re-applied on each reuse), and `close_pages()` closes every open tab (`scrapling/engines/_browsers/_base.py:66`, `_page.py:78`; `docs/fetching/stealthy.md:255`); versions 0.3.2–0.4.14 closed each tab after its request.

### Three-Tier Fetching System

#### Tier 1: Fetcher — HTTP with TLS Impersonation

The fastest option. Uses `curl_cffi` to send HTTP requests with **real browser TLS fingerprints** (JA3/JA4), avoiding the most common non-browser detection vector. (`scrapling/engines/static.py` imports from `curl_cffi.requests` and drives the `impersonate` parameter.)

```python
from scrapling.fetchers import Fetcher

# Impersonates Chrome's TLS fingerprint at the protocol level.
# `impersonate` defaults to "chrome" (latest available Chrome in curl_cffi).
response = Fetcher.get(
    'https://example.com',
    impersonate='chrome',      # or a list e.g. ['chrome','firefox','safari'] → random pick
    stealthy_headers=True,     # adds a Google referer; browserforge headers only if impersonate is off
    follow_redirects=True,
)
```

**Why this matters for anti-detection:**
- `curl_cffi` sends HTTP requests with the exact TLS ClientHello that Chrome/Firefox/Safari would send.
- JA3/JA4 fingerprinting services see a real browser signature, not Python's `requests` or `aiohttp`.
- With `impersonate` set (default `"chrome"`), `curl_cffi` supplies the browser's headers and Scrapling adds only a Google `referer` when `stealthy_headers=True`; `browserforge` generates headers only when `impersonate` is disabled (`scrapling/engines/static.py:73`, `168-186`).
- No JavaScript execution = no browser-DOM fingerprinting surface at all (but also no JS-rendered content).

**Impersonation targets:** Scrapling's `impersonate` argument (`ImpersonateType = BrowserTypeLiteral | List[...] | None`, in `scrapling/engines/_browsers/_types.py`) is passed straight through to **curl_cffi**, so the concrete browser/version list is whatever the installed `curl_cffi` (>=0.16.1) supports. You pass a family name like `chrome`, `firefox`, `safari` (defaults to the latest Chrome), or a list to randomize per-request. Note: HTTP/3 is available but the code warns it may conflict with `impersonate` (`scrapling/engines/static.py`).

> **Verification note:** the previous edition's table of exact versions ("Chrome 99–136, Firefox 91–135, Safari 15.3–18, Edge 99–136, Tor") is **not defined in Scrapling** — those come from curl_cffi and drift with its releases. Treat the supported set as "whatever your curl_cffi version ships." Scrapling itself only defines the family-name plumbing.

#### Tier 2: DynamicFetcher — Playwright Browser

For JavaScript-rendered content. Standard Playwright (Chromium) automation with convenience features (`network_idle`, `wait_selector`, resource blocking, retries).

```python
from scrapling.fetchers import DynamicFetcher

response = DynamicFetcher.fetch(
    'https://spa-site.com',
    headless=True,
    wait_selector='div.content',  # wait for specific element
    network_idle=True,            # wait until network is quiet
)
```

**No Patchright and no stealth launch flags** — `DynamicFetcher` drives Chromium through the unpatched `playwright` package (`scrapling/engines/_browsers/_controllers.py:4-9`) with `DEFAULT_ARGS` and `ignore_default_args=HARMFUL_ARGS` (which includes `--enable-automation`); it does not receive the `STEALTH_ARGS` set or the stealth context options (`_base.py:444-448`, `542-579`; `scrapling/engines/constants.py:15-92`). Detection outcomes for this tier were not tested here (**Tier D**). `block_ads` and `dns_over_https` are available on this tier as well (`scrapling/fetchers/chrome.py:18-19`).

#### Tier 3: StealthyFetcher — Maximum Anti-Detection

This is where Scrapling gets interesting from an anti-detection perspective. It is built **on top of a Chromium browser driven by [Patchright](./patchright.md)** (`scrapling/engines/_browsers/_stealth.py` imports `from patchright.sync_api import sync_playwright` / `patchright.async_api` at lines 8-9; the `fetchers` extra requires `patchright>=1.62.1`, `pyproject.toml:77`). The class docstring states it is "completely stealthy built on top of Chromium."

```python
from scrapling.fetchers import StealthyFetcher

response = StealthyFetcher.fetch(
    'https://protected-site.com',
    headless=True,
    solve_cloudflare=True,    # auto-solve Turnstile / Interstitial
    block_webrtc=True,        # force WebRTC to respect proxy (no local-IP leak)
    hide_canvas=True,         # add canvas noise (anti-fingerprinting)
    allow_webgl=True,         # WebGL ON by default; set False to disable (not recommended)
    block_ads=True,           # block 3,526 known ad/tracking domains (off by default)
    dns_over_https=True,      # route DNS via Cloudflare DoH (prevents DNS leak on proxies)
    google_search=True,       # send a Google referer (on by default)
)
```

**What StealthyFetcher does under the hood (as of 0.4.15; identical on `b11da90`):**

```
┌──────────────────────────────────────────────────────────────────┐
│                    STEALTHY FETCHER PIPELINE                       │
├──────────────────────────────────────────────────────────────────┤
│                                                                    │
│  1. Browser Engine                                                 │
│     └─ Chromium via Patchright (CDP stealth). Camoufox NOT used.   │
│        real_chrome=True → your installed Chrome; cdp_url → attach  │
│        to an existing browser over CDP.                            │
│                                                                    │
│  2. Anti-Detection Layers (implemented as Chromium launch flags)   │
│     ├─ Patchright CDP hardening (Runtime.enable leak, webdriver)  │
│     ├─ hide_canvas → --fingerprinting-canvas-image-data-noise     │
│     ├─ block_webrtc → --webrtc-ip-handling-policy=                 │
│     │                    disable_non_proxied_udp (+ force flag)    │
│     ├─ allow_webgl=False → disables WebGL / WebGL2                 │
│     ├─ dns_over_https → --dns-over-https-templates=...cloudflare   │
│     ├─ block_ads → drops requests to 3,526 ad/tracker domains     │
│     ├─ locale → --lang / --accept-lang flags; timezone_id         │
│     └─ real browser UA generation                                 │
│                                                                    │
│  3. Cloudflare Handling (if solve_cloudflare=True)                │
│     ├─ _detect_cloudflare(): classify Turnstile / Interstitial /  │
│     │    embedded turnstile challenge from page content           │
│     ├─ _cloudflare_solver(): wait for challenge box, click, poll  │
│     └─ Retry until challenge clears (max 3 re-solves)             │
│                                                                    │
│  4. Page Loading & Content Extraction                              │
│     ├─ network_idle / load_dom / wait_selector                    │
│     ├─ optional page_setup + page_action callbacks                │
│     └─ Return Response object with parsed HTML                     │
│                                                                    │
└──────────────────────────────────────────────────────────────────┘
```

> **Corrections vs. previous edition:** (1) `disable_webgl=True` is not the real parameter — WebGL is controlled by `allow_webgl` (default **True**; the docstring warns disabling it is risky because many WAFs now check WebGL is present). (2) `block_webrtc` does **not** "block" WebRTC — it forces Chromium to route WebRTC only through the proxy (`disable_non_proxied_udp`), preventing local-IP leaks. (3) `hide_canvas` is a native Chromium **launch flag** (`--fingerprinting-canvas-image-data-noise`), not JS-injected canvas noise. (4) There is no Camoufox/Firefox path anymore.

**Fixed launch and context settings (Tier A, `b11da90`):** the stealth tier launches Chromium with the 53-entry `STEALTH_ARGS` set (includes `--disable-blink-features=AutomationControlled`) plus 11 `DEFAULT_ARGS`, removes 5 `HARMFUL_ARGS` from Playwright's defaults (including `--enable-automation`), and sets `is_mobile=False`, `has_touch=False`, `ignore_https_errors=True`, a 1920x1080 screen and viewport, and `permissions=["geolocation", "notifications"]` (`scrapling/engines/constants.py:15-92`; `_base.py:547-554`). `color_scheme="dark"` and `device_scale_factor=2` are set for both browser tiers (`_base.py:444`; the code comment says dark mode avoids a CreepJS preferred-light-colour check). A `locale` is applied through `--lang` and `--accept-lang` launch flags rather than the Playwright context option, except on `cdp_url` sessions (`_base.py:468-470`, `491-500`; 0.4.15).

---

## Anti-Detection Mechanisms

### Per-Tier Stealth Comparison

| Detection Method | Fetcher (HTTP) | DynamicFetcher | StealthyFetcher |
|-----------------|:--------------:|:--------------:|:---------------:|
| TLS fingerprinting (JA3/JA4) | ✅ Impersonated (curl_cffi) | ✅ Real browser | ✅ Real browser |
| `navigator.webdriver` | N/A (no JS) | ❌ Detectable | ✅ Bypassed (Patchright) |
| `Runtime.enable` CDP leak | N/A | ❌ Detectable | ✅ Patchright bypass |
| Canvas fingerprinting | N/A | ❌ Exposed | ✅ Noise flag (`hide_canvas`) |
| WebRTC local-IP leak | N/A | ❌ Exposed | ✅ Proxy-only routing (`block_webrtc`) |
| WebGL fingerprinting | N/A | ❌ Exposed | ⚠️ Can disable (`allow_webgl=False`, not recommended) |
| DNS leak on proxy | N/A | ✅ `dns_over_https` (opt-in) | ✅ `dns_over_https` (opt-in) |
| Ad/tracker beacons | N/A | ✅ `block_ads` (opt-in) | ✅ `block_ads` (opt-in; 3,526 domains) |
| Cloudflare Turnstile/Interstitial | ❌ | ❌ | ✅ Auto-solved (`solve_cloudflare`) |
| Header / User-Agent handling | `curl_cffi` profile headers (browserforge only if `impersonate` is off) | browserforge-generated User-Agent when headless; Chromium's own headers | same as DynamicFetcher |
| HTTP/2 & HTTP/3 | ✅ (HTTP/3 optional) | ✅ | ✅ |

> The DynamicFetcher and StealthyFetcher cells describe which code path applies (stock `playwright` versus `patchright` plus `STEALTH_ARGS` and the context options in `_base.py:542-579`); detection outcomes were not tested here (**Tier D**).

### TLS Fingerprint Impersonation (Fetcher)

This is the **most important stealth feature** for HTTP-only scraping. Most bot detection starts with TLS fingerprinting — Python's `requests` library has a distinctive JA3 hash that instantly flags it as non-browser traffic.

```python
# Standard Python requests → distinctive Python/OpenSSL JA3 → flagged as bot

# Scrapling Fetcher with curl_cffi → matches a real Chrome ClientHello
response = Fetcher.get('https://example.com')   # impersonates latest Chrome by default
```

The impersonation is entirely `curl_cffi`'s doing — Scrapling wires the `impersonate` argument (and a `_select_random_browser` helper for list-based randomization) into `curl_cffi.requests.Session`. See `scrapling/engines/static.py`.

### Cloudflare Auto-Solving (StealthyFetcher)

The `solve_cloudflare=True` parameter handles Turnstile and Interstitial challenges without external CAPTCHA-solving APIs. Implemented in `scrapling/engines/_browsers/_stealth.py`:

- `_detect_cloudflare(page_content)` (`_base.py:581`) classifies the challenge from the `cType: 'non-interactive'`, `'managed'` or `'interactive'` strings in the page source, or as `embedded` when a `challenges.cloudflare.com/turnstile/v…` script tag is present.
- `_cloudflare_solver(page)` waits for the challenge widget (up to 20 × 500 ms for the iframe), clicks it at a randomized offset (x + 26–28, y + 25–27 px from the widget box, 100–200 ms press delay), and polls until the challenge page disappears. It re-solves at most 3 times (`__CF_MAX_SOLVE_ATTEMPTS__`, `_stealth.py:20`, `108-193`) and then returns the page as is. There is both a sync and an async implementation, and `solve_cloudflare=True` raises the timeout floor to 60,000 ms (`_validators.py:154-155`). 0.4.15 made detection independent of the browser locale and capped the retries (`CHANGELOG.md:55`).

**Important caveat:** The solver drives the Patchright Chromium to the challenge widget and clicks it; it is **not** solving the CAPTCHA cryptographically, and whether Cloudflare accepts the resulting browser session was not tested here (**Tier D**). It does **not** cover Akamai, DataDome, Kasada, or Incapsula (the project's own README points users to a paid third-party token API for those).

---

## Adaptive Element Tracking

This is Scrapling's **most distinctive feature** — no other tool in this repository offers automatic selector recovery.

### The Problem

Websites change their HTML structure regularly. A CSS selector that works today (`div.product-card > h2.title`) may break tomorrow when the site renames classes or restructures the DOM.

### How Scrapling Solves It

```python
from scrapling.fetchers import StealthyFetcher

StealthyFetcher.adaptive = True   # enable adaptive tracking

# First run: finds elements and saves their "signatures"
page = StealthyFetcher.fetch('https://shop.com')
products = page.css('.product-card', auto_save=True)  # saves fingerprint to SQLite

# Later run: site changed .product-card to .item-listing
page = StealthyFetcher.fetch('https://shop.com')
products = page.css('.product-card', adaptive=True)   # relocates via saved signature
```

**API note:** the feature was renamed from `auto_match` → `adaptive` in 0.3. On the parser (`scrapling/parser.py`) it appears as the `adaptive` attribute/keyword plus per-call `adaptive=` / `auto_save=` / `percentage=` arguments; the storage backend is pluggable via the `storage` argument.

**How it works internally:**

```
┌─────────────────────────────────────────────────────────┐
│              ADAPTIVE ELEMENT TRACKING                     │
├─────────────────────────────────────────────────────────┤
│                                                           │
│  1. First scrape (auto_save=True):                       │
│     Element found via CSS selector                        │
│     ├─ Record tag name, attributes, text content          │
│     ├─ Record parent chain (structural position)          │
│     ├─ Record sibling context                             │
│     └─ Save signature to SQLite (or custom backend)       │
│                                                           │
│  2. Subsequent scrape (adaptive=True, selector fails):    │
│     ├─ Load saved signature by identifier                 │
│     ├─ Score all elements by similarity                    │
│     │   ├─ Tag match                                      │
│     │   ├─ Attribute similarity                           │
│     │   ├─ Text content similarity                        │
│     │   ├─ Structural position similarity                 │
│     │   └─ Sibling context similarity                     │
│     └─ Return best match above `percentage` threshold     │
│                                                           │
│  Storage backends (scrapling/core/storage.py):            │
│     ├─ SQLiteStorageSystem (default, thread-safe mode)    │
│     └─ Any custom backend subclassing StorageSystemMixin  │
│        (implement save() / retrieve())                    │
│                                                           │
└─────────────────────────────────────────────────────────┘
```

The default backend is `SQLiteStorageSystem` (`check_same_thread=False`, an `RLock`, and `PRAGMA journal_mode=WAL`; `scrapling/core/storage.py:74-92`); `StorageSystemMixin` (`storage.py:14`) is the ABC you subclass for Redis or any other store. Saved data per element is the tag, attributes, text, DOM path, parent tag/attributes/text, sibling tags and child tags (`scrapling/core/utils/_utils.py:84-109`); candidates are scored as averaged `difflib.SequenceMatcher` ratios over those fields, with a default `percentage` threshold of 40 (`scrapling/parser.py:533`, `822-887`).

### Similar Element Finding

Related feature — find elements structurally similar to a known element:

```python
# Find one product card
card = page.css('.product-card')[0]

# Find all elements with similar structure (even if classes differ)
all_cards = card.find_similar()
```

---

## Performance

### Text-Extraction Speed (5000 nested elements, 100+ runs)

Numbers from the project's README (`README.md:498-523`, which points to `benchmarks.py` for methodology; **Tier B** — the maintainer's own benchmark, not reproduced here):

| # | Library | Time (ms) | vs Scrapling |
|---|---------|:---------:|:------------:|
| 1 | **Scrapling** | **1.99** | **1.0x (baseline)** |
| 2 | Parsel / Scrapy | 2.06 | 1.035x |
| 3 | Raw lxml | 2.56 | 1.286x |
| 4 | PyQuery | 23.98 | ~12x |
| 5 | Selectolax | 197.02 | ~99x |
| 6 | MechanicalSoup | 1,545.15 | ~776.5x |
| 7 | **BS4 + lxml** | **1,562.1** | **~785.0x** |
| 8 | BS4 + html5lib | 3,412.73 | ~1714.9x |

> **The README's "~785x faster than BS4" figure** is BS4-with-lxml (1,562.1 ms) vs Scrapling (1.99 ms) ≈ 785.0x (**Tier B**). Caveat as always: this is a **parser micro-benchmark** on a synthetic 5000-node document, and Scrapling and Parsel share the same lxml core (hence the ~1.035x near-tie). It is not an end-to-end scraping benchmark.

### Adaptive Element Finding

| Library | Time (ms) | vs Scrapling |
|---------|:---------:|:------------:|
| **Scrapling** | **2.3** | **1.0x** |
| AutoScraper | 12.58 | 5.47x slower |

### Other Performance Features

- **orjson** for JSON serialization (README claims ~10x faster than stdlib `json`).
- Lazy-imported fetchers/sessions (`scrapling/fetchers/__init__.py` uses a `_LAZY_IMPORTS` map so importing the package doesn't pull Playwright/curl_cffi until used).
- 0.3 rewrite claims "Fetcher ~4x faster, DynamicFetcher ~60% faster" vs 0.2 (maintainer's release notes, `CHANGELOG.md:854-855`; not independently benchmarked here).
- HTTP/3 support in the Fetcher tier (optional; may conflict with `impersonate`).

---

## Spider Framework

Scrapling includes a Scrapy-like async spider framework (added in 0.4, under `scrapling/spiders/`) for large-scale crawling:

```python
from scrapling.spiders import Spider, Response

class ProductSpider(Spider):
    name = "products"
    start_urls = ['https://shop.com/products']

    async def parse(self, response: Response):
        for product in response.css('.product-card'):
            yield {
                'name': product.css('h2::text').get(),
                'price': product.css('.price::text').get(),
            }
        next_page = response.css('a.next::attr(href)').get()
        if next_page:
            yield response.follow(next_page, callback=self.parse)

ProductSpider().start()
```

### Spider Features (from `scrapling/spiders/`)

| Feature | Details | Source |
|---------|---------|--------|
| **Concurrent requests** | Async scheduler with configurable concurrency | `spiders/scheduler.py`, `spiders/engine.py` |
| **Multi-session support** | Mix Fetcher / DynamicFetcher / StealthyFetcher per request | `spiders/session.py` |
| **Pause/Resume** | Checkpoint system — survives Ctrl+C, resumes crawl | `spiders/checkpoint.py` |
| **Response caching** | Local cache for iterating on parse logic without re-fetching | `spiders/cache.py` |
| **Proxy rotation** | Thread-safe `ProxyRotator` across all fetchers | `engines/toolbelt/proxy_rotation.py` |
| **robots.txt compliance** | Honors `Crawl-delay` / `Request-rate` via `protego` | `spiders/robotstxt.py` |
| **Link extraction and templates** | `LinkExtractor`; `CrawlSpider`, `SitemapSpider`, `ShopifySpider`, `XMLFeedSpider` / `CSVFeedSpider`, and (0.4.15) `SiteToMarkdownSpider`, which crawls a site into one Markdown item per page | `spiders/links.py`, `spiders/templates/` |
| **Streaming mode** | Async generator for real-time item processing | `spiders/engine.py` |
| **Stats tracking** | `CrawlStats` real-time metrics | `spiders/result.py` |
| **AutoThrottle** | Opt-in per-domain delay adjusted from measured response times (`autothrottle_enabled`, default off; 0.4.12) | `spiders/throttle.py`, `spiders/spider.py:89-93` |

### Scrapy Integration (new)

0.4.x added a bridge for existing Scrapy projects (`scrapling/integrations/scrapy.py`): decorate a spider callback with `@scrapling_response` (or call `convert_response`) and you receive a Scrapling `Response` — with the full parsing/adaptive API — instead of the native Scrapy response, without changing how the spider crawls.

---

## CLI & MCP Server

### CLI Tools

```bash
# Interactive scraping shell (IPython-based)
scrapling shell

# Extract content without writing code
scrapling extract get 'https://example.com' output.md
scrapling extract fetch 'https://spa-site.com' output.md          # Dynamic
scrapling extract stealthy-fetch 'https://protected.com' output.md  # Stealth

# Launch MCP server for AI integration
scrapling mcp
scrapling mcp --http --auth-token <token> --port 8080   # binds 127.0.0.1 unless --host is given
```

The CLI (`scrapling/cli.py`) exposes `--impersonate` (single or comma-separated for random selection) and an `--executable-path` (or `SCRAPLING_EXECUTABLE_PATH`) to point the MCP browser tools (0.4.10) and the `extract fetch` / `extract stealthy-fetch` commands (0.4.11) at a custom Chromium-compatible browser. `scrapling install` runs `python -m playwright install chromium` and `install-deps chromium`, then refreshes the `tld` name list (`cli.py:110-143`). A `scrapling-mcp` entry point maps to `scrapling mcp` (0.4.13).

### MCP Server (AI Integration)

The MCP server (`scrapling/core/ai.py`, `_build_server()` at line 1069) registers **13 tools** through `MCPServer` from the `mcp>=2.0.0` SDK (`ai.py:8`, `1103-1188`). It had 10 tools through 0.4.14 and 6 in an earlier edition of this page; 0.4.15 renamed `get` to `make_request` and added `open_request_session`, `session_fetch` and `session_make_request` (`CHANGELOG.md:44-48`):

| Tool | Description |
|------|------------|
| `open_session` | Open a persistent browser session (`dynamic` or `stealthy`; accepts a CDP URL) |
| `open_request_session` | Open a persistent HTTP session (no browser) that keeps cookies and the impersonated fingerprint |
| `close_session` | Close a session |
| `list_sessions` | List active sessions with their effective settings |
| `make_request` | One-shot HTTP request with TLS impersonation, any method (was `get`) |
| `bulk_get` | Parallel multi-URL GET |
| `fetch` | One-shot dynamic content via browser |
| `bulk_fetch` | Parallel multi-URL dynamic |
| `stealthy_fetch` | One-shot fetch through the stealth (Patchright) browser |
| `bulk_stealthy_fetch` | Parallel multi-URL stealth |
| `session_fetch` | Fetch through an opened browser session |
| `session_make_request` | Request through an opened HTTP session |
| `screenshot` | Capture page as an image content block |

It runs over stdio by default or `streamable-http` with `--http`. Since 0.4.15 the HTTP transport refuses to start without a bearer token (`--auth-token` or `SCRAPLING_MCP_AUTH_TOKEN`) unless `--no-auth` is passed, binds `127.0.0.1` by default, and `--allowed-host` turns on DNS-rebinding protection (`cli.py:152-197`, `ai.py:1190-1239`; before 0.4.15 it only logged a warning and defaulted to `0.0.0.0`). Smart CSS pre-processing extracts the relevant HTML before sending to the model to reduce token usage, and hidden or prompt-injection content is stripped by `Convertor._sanitize_for_ai` (`scrapling/core/shell.py:596-604`); the project also ships an "agent skill" bundle (`agent-skill/`) and a registry manifest (`server.json`, name `io.github.D4Vinci/Scrapling`, PyPI package and OCI image `ghcr.io/d4vinci/scrapling`).

Not MCP-specific: 0.4.15 added `Response.markdown()` (`scrapling/engines/toolbelt/custom.py:88`), which applies the same sanitising before converting a response to Markdown, and a `rag` extra (`markdownify` plus the fetchers) for it.

---

## Pros and Cons

### Advantages

| Pro | Details |
|-----|---------|
| **All-in-one framework** | Fetching + parsing + crawling + stealth + AI in one package |
| **Three fetch tiers** | HTTP-only (curl_cffi), dynamic (Playwright), or full stealth (Patchright) |
| **TLS impersonation** | curl_cffi matches real browser JA3/JA4 signatures at the HTTP tier |
| **Adaptive tracking** | Auto-relocates elements when sites change DOM; no equivalent code found in the other cloned trees |
| **Parser speed** | Near-tie with Parsel, ~785x faster than BeautifulSoup4 + lxml per the README (parser micro-benchmark, Tier B) |
| **Cloudflare auto-solve** | Built-in Turnstile/Interstitial handling, no external API |
| **Spider framework** | Concurrency, pause/resume, caching, proxy rotation, robots.txt, AutoThrottle |
| **Scrapy interop** | `@scrapling_response` drops Scrapling parsing into existing Scrapy spiders |
| **MCP / AI integration** | 13-tool MCP server + agent-skill bundle; registry manifest in `server.json` |
| **Maintenance activity** | Latest release 0.4.15 (2026-08-23); later commits are docs/sponsor edits; README states 92% test coverage (Tier B) |
| **Permissive license** | BSD 3-Clause |

### Disadvantages

| Con | Details |
|-----|---------|
| **Python only** | No Node.js, .NET, or other language bindings |
| **Stealth is borrowed** | StealthyFetcher wraps Patchright — the anti-detection is Patchright's, not Scrapling's own innovation |
| **Chromium-only stealth** | The Firefox/Camoufox engine was dropped in 0.3.13; no Firefox stealth path in the package |
| **Optional dependency footprint** | Full install pulls Playwright (`>=1.62.0`) + Patchright (`>=1.62.1`) + curl_cffi + browserforge + fingerprint datapoints + mcp, etc.; both browser packages are minimum versions, not pins |
| **No human-behavior simulation** | No Bézier mouse movement or click/scroll timing models; the Cloudflare solver randomizes only its click offset and press delay (`_stealth.py:170-173`) (see [Botasaurus](./botasaurus.md)) |
| **No self-run anti-bot benchmarks** | The repo publishes parser speed, not pass-rates against commercial WAFs |
| **Adaptive tracking has limits** | Major redesigns can still break saved signatures; needs an initial `auto_save` run |
| **StealthyFetcher speed** | Browser-based stealth is inherently slower than the HTTP tier |
| **Beta status** | `Development Status :: 4 - Beta` in metadata |

---

## Anti-bot handling — what exists in the code, and what the project claims

> The previous edition of this page carried a ✅/⚠️/❌ coverage grid with the legend
> "✅ = Reliably bypasses." Scrapling publishes no pass-rate benchmarks and none were
> run here, so that grid asserted more than anyone knows. It has been replaced with
> what is actually checkable: which mechanisms exist in the source, and what the
> maintainer claims. See [METHODOLOGY.md](METHODOLOGY.md#evidence-tiers).

| Capability | Present in source? | Tier | Notes |
|---|---|:--:|---|
| TLS impersonation (HTTP tier) | **Yes** — `curl_cffi>=0.16.1`, `--impersonate` with Chrome/Firefox/Safari profiles | **A** | Real JA3/JA4 impersonation. The most concretely verifiable stealth feature here. |
| Cloudflare Turnstile / Interstitial solver | **Yes** — `solve_cloudflare` in StealthyFetcher | **A** | The code path exists and is first-party. Whether it succeeds on a given deployment is untested here. |
| CDP-level automation-tell removal | **Delegated** — `patchright>=1.62.1` | **A** | Not Scrapling's work. Its browser-tier evasion is exactly Patchright's, with Patchright's strengths and limits. |
| Fingerprint spoofing (canvas/WebGL/audio) | **No** first-party implementation | **A** | Exposes flags (canvas noise, WebGL toggle, timezone/locale match, WebRTC→proxy) but implements no engine-level spoofing. Camoufox has not been used since 0.3.13. The README's feature list (line 277) describes the stealth tier as including fingerprint spoofing (**Tier B**); in source it is launch flags and context options, as above. |
| DataDome / Kasada / Akamai / Incapsula | **No** first-party handling | **A** | Notably, the project **does not claim these** — its README routes them to a third-party paid token API. |

**Scope stated by the project.** Scrapling's README routes Akamai, DataDome, Kasada,
and Incapsula to an external paid token API rather than claiming coverage. This matches
the source: no first-party handling for those four exists in the tree. Any evaluation of
Scrapling against them is an evaluation of Patchright plus the caller's IP reputation.

> **Honest note:** Scrapling's own README explicitly says it handles **Cloudflare Turnstile** out of the box and points users to a paid third-party token API for **Akamai / DataDome / Kasada / Incapsula**. Treat any "bypasses DataDome/Kasada" claim as "only insofar as a well-configured Patchright Chromium + clean proxy does" — Scrapling adds no dedicated solver for those. The previous edition's confident ✅ marks for DataDome/Kasada via Camoufox no longer apply (Camoufox is gone).

---

## Comparison with Alternatives

### vs. Dedicated Anti-Detection Tools

| Feature | Scrapling | Camoufox | Patchright | SeleniumBase |
|---------|:---------:|:--------:|:----------:|:------------:|
| HTTP-only stealth (TLS) | ✅ | ❌ | ❌ | ❌ |
| Browser stealth | ✅ (via Patchright) | ✅ Native | ✅ Native | ✅ Native |
| HTML parser built-in | ✅ (fast lxml tier) | ❌ | ❌ | ❌ |
| Adaptive element tracking | ✅ Uncommon | ❌ | ❌ | ❌ |
| Spider/crawler framework | ✅ | ❌ | ❌ | ❌ |
| CAPTCHA solving | ⚠️ Cloudflare Turnstile only | ❌ | ❌ | ✅ Multiple |
| Human behavior simulation | ❌ | ✅ Mouse | ❌ | ✅ |
| Fingerprint rotation | ⚠️ User-Agent only for browsers (browserforge); `curl_cffi` profiles for HTTP | ✅ BrowserForge (PyPI 0.5.6); fpgen at repo HEAD | ⚠️ | ⚠️ |
| CLI tools | ✅ | ❌ | ❌ | ❌ |
| MCP/AI integration | ✅ (13 tools) | ❌ | ❌ | ❌ |
| Multi-language | Python only | Python | Python, Node, .NET | Python |

### vs. Scraping Frameworks

| Feature | Scrapling | Scrapy | BeautifulSoup4 | Playwright (raw) |
|---------|:---------:|:------:|:--------------:|:----------------:|
| Parse speed (relative) | 1.0x | ~1.035x | ~785x slower | N/A |
| Anti-detection built-in | ✅ Three tiers | ❌ | ❌ | ❌ |
| Adaptive element tracking | ✅ | ❌ | ❌ | ❌ |
| Spider framework | ✅ | ✅ (more mature) | ❌ | ❌ |
| JS rendering | ✅ | Via Splash/Playwright | ❌ | ✅ |
| Scrapy interop | ✅ (`@scrapling_response`) | — | ❌ | ❌ |
| Middleware ecosystem | limited | extensive (Scrapy) | none | none |
| Community/plugins | Growing | Massive | Massive | Large |
| Async support | ✅ | ✅ | ❌ | ✅ |

---

## Installation & Usage

### Quick Start

```bash
# Core only (parsing)
pip install scrapling

# With fetchers (HTTP TLS impersonation + Playwright + Patchright)
pip install "scrapling[fetchers]"

# With AI/MCP extras
pip install "scrapling[ai]"

# With Markdown/RAG extras (Response.markdown(), SiteToMarkdownSpider)
pip install "scrapling[rag]"

# Everything (fetchers + shell + AI)
pip install "scrapling[all]"

# Install Playwright's Chromium + its system dependencies
scrapling install
```

Extras (from `pyproject.toml:73-100`): `fetchers` (click, `curl_cffi>=0.16.1`, `playwright>=1.62.0`, `patchright>=1.62.1`, browserforge, apify-fingerprint-datapoints, msgspec, anyio, protego), `rag` (markdownify, + fetchers), `ai` (`mcp>=2.0.0`, markdownify, + fetchers), `shell` (IPython, markdownify, + fetchers), `all` (ai + shell). Core deps are lxml ≥6.1.1, cssselect, orjson, tld, w3lib, typing_extensions.

### Basic Fetching

```python
from scrapling.fetchers import Fetcher, StealthyFetcher

# Fast HTTP with TLS impersonation
resp = Fetcher.get('https://example.com')
print(resp.status)
print(resp.css('title::text').get())

# Stealth with Cloudflare bypass
resp = StealthyFetcher.fetch(
    'https://protected.com',
    solve_cloudflare=True,
    headless=True,
)
```

### Selection Methods

```python
# CSS3 selectors with pseudo-elements
titles = resp.css('h2.title::text').getall()

# XPath
prices = resp.xpath('//span[@class="price"]/text()').getall()

# BeautifulSoup-style filter search
links = resp.find_all('a', class_='product-link')

# Text search
elem = resp.find_by_text('Add to Cart', partial=True)

# Regex
emails = resp.find_by_regex(r'[\w.]+@[\w.]+\.\w+')

# Find structurally similar elements
first_card = resp.css('.product-card')[0]
all_cards = first_card.find_similar()
```

---

## When to Use

### Recommended For

- **All-in-one scraping projects** — you don't want to stitch Scrapy + Playwright + a stealth plugin together yourself.
- **Adaptive scraping** — target sites that frequently change their DOM (the adaptive tracker is the standout feature).
- **HTTP-only stealth** — you need TLS impersonation without browser overhead (the fastest tier).
- **Mixed stealth requirements** — some pages need HTTP-only, others need full Chromium stealth.
- **Cloudflare Turnstile targets** — the built-in solver covers Turnstile/Interstitial with no extra API.
- **AI-integrated scraping** — the 13-tool MCP server for Claude/Cursor-driven workflows.
- **Existing Scrapy shops** — drop Scrapling parsing into current spiders via `@scrapling_response`.
- **Python teams** already fluent in CSS/XPath selectors.

### Not Recommended For

- **Maximum browser stealth / fine control** — use [Patchright](./patchright.md) directly, or [Camoufox](./camoufox.md) for Firefox-level C++ fingerprinting (Scrapling no longer bundles Camoufox).
- **Human-behavior simulation** — no Bézier mouse / click timing / scroll models (use [Botasaurus](./botasaurus.md)).
- **Non-Python projects** — Python only.
- **DataDome / Akamai / Kasada / Incapsula** — no dedicated solver; you get whatever a good Patchright + proxy setup achieves.
- **Multi-CAPTCHA solving** — only Cloudflare Turnstile (use [SeleniumBase](./seleniumbase.md) for reCAPTCHA/hCaptcha).
- **When you only need one specific stealth tool** — Scrapling's framework overhead is unnecessary.

---

## Key Files & Dependencies

| Component | Location / Package | Purpose |
|-----------|--------------------|---------|
| HTTP engine (TLS impersonation) | `scrapling/engines/static.py` (curl_cffi) | JA3/JA4 impersonation |
| Stealth browser engine | `scrapling/engines/_browsers/_stealth.py` (patchright) | CDP stealth + Cloudflare solver |
| Browser launch flags | `scrapling/engines/_browsers/_base.py` | canvas noise, WebRTC policy, WebGL, DoH, locale flags |
| Flag sets | `scrapling/engines/constants.py` | `DEFAULT_ARGS` (11), `STEALTH_ARGS` (53), `HARMFUL_ARGS` (5), `EXTRA_RESOURCES` (10) |
| Tab pool | `scrapling/engines/_browsers/_page.py` | ready/busy/error pages reused across requests (0.4.15) |
| Parser / selectors | `scrapling/parser.py` (lxml + cssselect) | CSS/XPath/regex/text + adaptive |
| Adaptive storage | `scrapling/core/storage.py` (`SQLiteStorageSystem`, `StorageSystemMixin`) | signature persistence |
| Spider framework | `scrapling/spiders/` | concurrency, checkpoint, cache, proxy, robots |
| Ad/tracker list | `scrapling/engines/toolbelt/ad_domains.py` | 3,526 domains |
| Proxy rotation | `scrapling/engines/toolbelt/proxy_rotation.py` (`ProxyRotator`) | thread-safe rotation |
| Scrapy interop | `scrapling/integrations/scrapy.py` | `@scrapling_response` decorator |
| MCP / AI server | `scrapling/core/ai.py` (`MCPServer`, 13 tools) | AI assistant integration |
| CLI | `scrapling/cli.py` | `shell` / `extract` / `mcp` / `install` |
| `browserforge` | dependency | statistically accurate browser headers |
| `orjson` | dependency | fast JSON serialization |

---

## Conclusion

Scrapling is a **framework, not a stealth engine**. Its browser anti-detection is inherited from **Patchright** (a patched Chromium/Playwright); what Scrapling adds is the *framework around it*: a unified classmethod API, a three-tier fetching strategy (curl_cffi HTTP → Playwright → Patchright stealth), adaptive element tracking, an async spider framework with checkpoints and proxy rotation, Scrapy interop, CLI tools, and a 13-tool MCP server.

**Applicability:** Python pipelines needing fetching, parsing, and crawling in one package. Verified first-party capabilities: `curl_cffi` TLS impersonation on the HTTP tier, a `solve_cloudflare` code path, adaptive element tracking, and a spider framework. Browser-tier evasion is Patchright's, reached via `patchright>=1.62.1`.

**Constraints:** no first-party fingerprint spoofing, and no first-party handling for Akamai, DataDome, Kasada, or Incapsula — the project routes those to an external paid API. Using Patchright directly provides the same browser-tier evasion without the framework layer.

**Scope summary:** Scrapling's browser-tier stealth is Patchright's implementation, reached through a dependency (`patchright>=1.62.1`). Using Patchright directly provides the same evasion without the framework. Scrapling adds the HTTP tier (`curl_cffi` TLS impersonation), the parser, adaptive element tracking, and the spider framework. Project state at 2026-09-30: 0.4.15 shipped 2026-08-23, 31 contributors, 9 open issues, 92% test coverage stated in the README (Tier B), BSD-3-Clause. Its published benchmarks measure parser throughput, not WAF outcomes.

**Unique value:** The adaptive element tracking system remains the standout — automatic selector recovery when a site's DOM changes is something none of the other tools analyzed in this repository provide.

---

*Analysis conducted for educational purposes against Scrapling v0.4.15 source (`b11da90`, read 2026-09-30 in an isolated container; the `scrapling/` tree is identical to the v0.4.15 tag). Use responsibly.*
