# Scrapling - Deep Technical Analysis

> **Tool Type:** All-in-One Web Scraping Framework (Fetching + Parsing + Crawling + Stealth)
> **Repository:** [github.com/D4Vinci/Scrapling](https://github.com/D4Vinci/Scrapling)
> **Approach:** Three-tier fetching (HTTP/Dynamic/Stealth) + adaptive element tracking + spider framework
> **What is verified:** `pyproject.toml` pins `curl_cffi>=0.16.0` (HTTP-tier TLS impersonation) and `patchright>=1.61.2` — **the browser-tier evasion is Patchright's**, inherited wholesale rather than implemented here (**Tier A**)
> **Anti-bot service claims:** Cloudflare Turnstile handled out of the box (**Tier B**). Notably candid: the README **defers Akamai, DataDome, Kasada and Incapsula to a third-party paid API** rather than claiming them — an unusually honest scoping among the tools here.
> **Maintenance:** Actively developed — **v0.4.14** (2026-08-10); 0.4.11–0.4.13 added feed spiders, AutoThrottle, and a smarter MCP server. 73.9k stars, 30 contributors, only 3 open issues. BSD-3-Clause.
> **Verified:** 2026-08-14 against `D4Vinci/Scrapling` @ `5d213a2`.

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

**Project facts (verified against source, 2026-08-14):**

| Attribute | Value | Evidence |
|-----------|-------|----------|
| Current version | **0.4.14** | `pyproject.toml` `version = "0.4.14"`, `scrapling/__init__.py` `__version__ = "0.4.14"`; PyPI upload 2026-08-10 |
| Release cadence | fortnightly-to-monthly point releases | GitHub: 0.4.14 (Aug 10), 0.4.13 (Aug 9), 0.4.12 (Jul 26), 0.4.11 (Jul 12), 0.4.10 (Jul 4) |
| Last commit | 2026-08-11 (`5d213a2`) | `git log -1` on the sandboxed clone |
| Community | 73.9k stars, 30 contributors, 3 open issues | GitHub API |
| Language | **Python only** (CPython) | `Programming Language :: Python :: 3 :: Only` classifier |
| Python versions | **3.10 – 3.13** | `requires-python = ">=3.10"` |
| License | **BSD 3-Clause** | `LICENSE`; `License :: OSI Approved :: BSD License` |
| Author/maintainer | Karim Shoair (D4Vinci) | `pyproject.toml` authors |
| Dev status | `4 - Beta` | `pyproject.toml` classifier |

> **Correction vs. previous edition of this page:** the page previously said "v0.4.2" and described StealthyFetcher as "Patchright **or Camoufox**" with a `use_camoufox=True` switch. As of 0.4.10 **Camoufox has been removed entirely** — `grep -r camoufox scrapling/` returns nothing, `camoufox` is not a dependency in `pyproject.toml`, and no `use_camoufox` parameter exists. StealthyFetcher is now a **Chromium/Patchright-only** engine. See [Anti-Detection Mechanisms](#anti-detection-mechanisms).

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
│  │  │ Speed: ⭐⭐⭐⭐⭐│    │ Speed: ⭐⭐⭐           │   │        │
│  │  │ Stealth: ⭐⭐    │    │ Stealth: ⭐⭐⭐         │   │        │
│  │  └──────────────────┘    └──────────────────────────┘   │        │
│  │                                                           │        │
│  │  Tier 3: StealthyFetcher                                 │        │
│  │  ┌──────────────────────────────────────────────────┐   │        │
│  │  │ Patchright (Chromium, CDP stealth)               │   │        │
│  │  │ Canvas noise flag        Cloudflare auto-solve    │   │        │
│  │  │ WebRTC → proxy-only      Timezone/locale match    │   │        │
│  │  │ WebGL toggle             real_chrome / cdp_url    │   │        │
│  │  │ Speed: ⭐⭐⭐            Stealth: ⭐⭐⭐⭐⭐     │   │        │
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
│  │  CLI: shell / extract / mcp   │   MCP Server (10 tools)   │        │
│  │  Scrapy integration (@scrapling_response decorator)      │        │
│  └─────────────────────────────────────────────────────────┘        │
└─────────────────────────────────────────────────────────────────────┘
```

**API note (changed in 0.3):** the fetchers are now driven through **classmethods** and a `.fetch()` entrypoint, not instance construction. `Fetcher.get(...)`, `StealthyFetcher.fetch(...)`, and `DynamicFetcher.fetch(...)` are the current shapes (`scrapling/fetchers/requests.py` decorates `get`/`post` with `@classmethod`; `scrapling/fetchers/stealth_chrome.py` exposes `fetch`). The old `Fetcher(auto_match=False).get(...)` instance style and the `auto_match=` keyword were renamed — the adaptive feature is now the `adaptive` attribute/keyword. Persistent `FetcherSession` / `DynamicSession` / `StealthySession` classes (added in 0.3) are the way to reuse a browser/session across requests.

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
    stealthy_headers=True,     # real browser headers via browserforge
    follow_redirects=True,
)
```

**Why this matters for anti-detection:**
- `curl_cffi` sends HTTP requests with the exact TLS ClientHello that Chrome/Firefox/Safari would send.
- JA3/JA4 fingerprinting services see a real browser signature, not Python's `requests` or `aiohttp`.
- `browserforge` generates statistically accurate headers matching the impersonated browser.
- No JavaScript execution = no browser-DOM fingerprinting surface at all (but also no JS-rendered content).

**Impersonation targets:** Scrapling's `impersonate` argument (`ImpersonateType = BrowserTypeLiteral | List[...] | None`, in `scrapling/engines/_browsers/_types.py`) is passed straight through to **curl_cffi**, so the concrete browser/version list is whatever the installed `curl_cffi` (>=0.15.0) supports. You pass a family name like `chrome`, `firefox`, `safari` (defaults to the latest Chrome), or a list to randomize per-request. Note: HTTP/3 is available but the code warns it may conflict with `impersonate` (`scrapling/engines/static.py`).

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

**Limited anti-detection** — this is essentially vanilla Playwright Chromium. Detectable by standard checks (`navigator.webdriver`, CDP leaks, etc.). Use StealthyFetcher when you need stealth.

#### Tier 3: StealthyFetcher — Maximum Anti-Detection

This is where Scrapling gets interesting from an anti-detection perspective. It is built **on top of a Chromium browser driven by [Patchright](./patchright.md)** (`scrapling/engines/_browsers/_stealth.py` imports `from patchright.sync_api import sync_playwright` / `patchright.async_api`; `patchright==1.61.1` is pinned in `pyproject.toml`). The class docstring states it is "completely stealthy built on top of Chromium."

```python
from scrapling.fetchers import StealthyFetcher

response = StealthyFetcher.fetch(
    'https://protected-site.com',
    headless=True,
    solve_cloudflare=True,    # auto-solve Turnstile / Interstitial
    block_webrtc=True,        # force WebRTC to respect proxy (no local-IP leak)
    hide_canvas=True,         # add canvas noise (anti-fingerprinting)
    allow_webgl=True,         # WebGL ON by default; set False to disable (not recommended)
    block_ads=True,           # block ~3,525 known ad/tracking domains
    dns_over_https=True,      # route DNS via Cloudflare DoH (prevents DNS leak on proxies)
    google_search=True,       # send a Google referer (on by default)
)
```

**What StealthyFetcher does under the hood (as of 0.4.14):**

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
│     ├─ block_ads → drops requests to ~3,525 ad/tracker domains    │
│     ├─ locale / timezone_id matching                              │
│     └─ real browser UA generation                                 │
│                                                                    │
│  3. Cloudflare Handling (if solve_cloudflare=True)                │
│     ├─ _detect_cloudflare(): classify Turnstile / Interstitial /  │
│     │    embedded turnstile challenge from page content           │
│     ├─ _cloudflare_solver(): wait for challenge box, click, poll  │
│     └─ Retry until challenge disappears (or timeout)              │
│                                                                    │
│  4. Page Loading & Content Extraction                              │
│     ├─ network_idle / load_dom / wait_selector                    │
│     ├─ optional page_setup + page_action callbacks                │
│     └─ Return Response object with parsed HTML                     │
│                                                                    │
└──────────────────────────────────────────────────────────────────┘
```

> **Corrections vs. previous edition:** (1) `disable_webgl=True` is not the real parameter — WebGL is controlled by `allow_webgl` (default **True**; the docstring warns disabling it is risky because many WAFs now check WebGL is present). (2) `block_webrtc` does **not** "block" WebRTC — it forces Chromium to route WebRTC only through the proxy (`disable_non_proxied_udp`), preventing local-IP leaks. (3) `hide_canvas` is a native Chromium **launch flag** (`--fingerprinting-canvas-image-data-noise`), not JS-injected canvas noise. (4) There is no Camoufox/Firefox path anymore.

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
| DNS leak on proxy | N/A | ❌ | ✅ `dns_over_https` |
| Ad/tracker beacons | N/A | ⚠️ | ✅ `block_ads` (~3,525 domains) |
| Cloudflare Turnstile/Interstitial | ❌ | ❌ | ✅ Auto-solved (`solve_cloudflare`) |
| Browser header consistency | ✅ browserforge | ⚠️ Basic | ✅ Full spoofing |
| HTTP/2 & HTTP/3 | ✅ (HTTP/3 optional) | ✅ | ✅ |

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

- `_detect_cloudflare(page_content)` (in `_base.py`) classifies the challenge type (waits for the `challenges.cloudflare.com` script / turnstile iframe).
- `_cloudflare_solver(page)` waits for the challenge widget, clicks it, and polls until the challenge page disappears (retrying if it reappears). There is both a sync and an async implementation.

**Important caveat:** This works because the Patchright-driven Chromium passes Cloudflare's browser-environment checks. It is **not** solving the CAPTCHA cryptographically — it is presenting a browser Cloudflare trusts enough to auto-pass a Turnstile/Interstitial. It does **not** cover Akamai, DataDome, Kasada, or Incapsula (the project's own README points users to a paid third-party token API for those).

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

The default backend is `SQLiteStorageSystem` (opened in thread-safe mode 1); `StorageSystemMixin` is the ABC you subclass for Redis or any other store. See `scrapling/core/storage.py`.

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

Numbers straight from the project's `benchmarks.py` / README (**Tier B** — the maintainer's own benchmark, not reproduced here):

| # | Library | Time (ms) | vs Scrapling |
|---|---------|:---------:|:------------:|
| 1 | **Scrapling** | **2.02** | **1.0x (baseline)** |
| 2 | Parsel / Scrapy | 2.04 | 1.01x |
| 3 | Raw lxml | 2.54 | 1.257x |
| 4 | PyQuery | 24.17 | ~12x |
| 5 | Selectolax | 82.63 | ~41x |
| 6 | MechanicalSoup | 1,549.71 | ~767.1x |
| 7 | **BS4 + lxml** | **1,584.31** | **~784.3x** |
| 8 | BS4 + html5lib | 3,391.91 | ~1679.1x |

> **"784x faster than BS4" — CONFIRMED.** The figure is BS4-with-lxml (1,584.31 ms) vs Scrapling (2.02 ms) ≈ 784.3x, from the maintainer's own `benchmarks.py`. Caveat as always: this is a **parser micro-benchmark** on a synthetic 5000-node document, and Scrapling and Parsel share the same lxml core (hence the ~1.01x tie). It is not an end-to-end scraping benchmark.

### Adaptive Element Finding

| Library | Time (ms) | vs Scrapling |
|---------|:---------:|:------------:|
| **Scrapling** | **2.39** | **1.0x** |
| AutoScraper | 12.45 | ~5.2x slower |

### Other Performance Features

- **orjson** for JSON serialization (README claims ~10x faster than stdlib `json`).
- Lazy-imported fetchers/sessions (`scrapling/fetchers/__init__.py` uses a `_LAZY_IMPORTS` map so importing the package doesn't pull Playwright/curl_cffi until used).
- 0.3 rewrite claims "Fetcher ~4x faster, DynamicFetcher ~60% faster" vs 0.2 (maintainer's release notes; not independently benchmarked here).
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
| **Link extraction** | `LinkExtractor`, `CrawlSpider`, `SitemapSpider` templates | `spiders/links.py`, `spiders/templates/` |
| **Streaming mode** | Async generator for real-time item processing | `spiders/engine.py` |
| **Stats tracking** | `CrawlStats` real-time metrics | `spiders/result.py` |

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
scrapling mcp --http --host 0.0.0.0 --port 8080
```

The CLI (`scrapling/cli.py`) exposes `--impersonate` (single or comma-separated for random selection) and an `--executable-path` to point the MCP browser tools at a custom Chromium-compatible browser (added in 0.4.10).

### MCP Server (AI Integration)

The MCP server (`scrapling/core/ai.py`, `serve()`) registers **10 tools** via `FastMCP` (the previous edition said 6 — session-management and screenshot tools were added since):

| Tool | Description |
|------|------------|
| `open_session` | Open a persistent browser/HTTP session |
| `close_session` | Close a session |
| `list_sessions` | List active sessions |
| `get` | Fast HTTP with TLS impersonation |
| `bulk_get` | Parallel multi-URL HTTP |
| `fetch` | Dynamic content via browser |
| `bulk_fetch` | Parallel multi-URL dynamic |
| `stealthy_fetch` | Anti-bot bypass via stealth (Patchright) browser |
| `bulk_stealthy_fetch` | Parallel multi-URL stealth |
| `screenshot` | Capture page as an image content block |

It runs over stdio by default or `streamable-http` with `--http`. Smart CSS pre-processing extracts the relevant HTML before sending to the model to reduce token usage; the project also ships an "agent skill" bundle (`agent-skill/`) and registers on the MCP registry (`server.json`, `io.github.D4Vinci/Scrapling`, also published as an OCI image `ghcr.io/d4vinci/scrapling`).

---

## Pros and Cons

### Advantages

| Pro | Details |
|-----|---------|
| **All-in-one framework** | Fetching + parsing + crawling + stealth + AI in one package |
| **Three fetch tiers** | HTTP-only (curl_cffi), dynamic (Playwright), or full stealth (Patchright) |
| **TLS impersonation** | curl_cffi matches real browser JA3/JA4 signatures at the HTTP tier |
| **Adaptive tracking** | Auto-relocate elements when sites change DOM (genuinely uncommon) |
| **Blazing-fast parser** | Tied with Parsel, ~784x faster than BeautifulSoup4 (parser micro-benchmark) |
| **Cloudflare auto-solve** | Built-in Turnstile/Interstitial handling, no external API |
| **Mature-ish spider framework** | Concurrency, pause/resume, caching, proxy rotation, robots.txt |
| **Scrapy interop** | `@scrapling_response` drops Scrapling parsing into existing Scrapy spiders |
| **MCP / AI integration** | 10-tool MCP server + agent-skill bundle; on the MCP registry |
| **Actively maintained** | Frequent releases (0.4.14 on 2026-08-10), commits within days, ~92% coverage |
| **Permissive license** | BSD 3-Clause |

### Disadvantages

| Con | Details |
|-----|---------|
| **Python only** | No Node.js, .NET, or other language bindings |
| **Stealth is borrowed** | StealthyFetcher wraps Patchright — the anti-detection is Patchright's, not Scrapling's own innovation |
| **Chromium-only stealth now** | The Firefox/Camoufox engine was removed; no Firefox stealth path anymore |
| **Heavy optional deps** | Full install pulls Playwright + Patchright (pinned to 1.61.x) + curl_cffi + browserforge + fingerprint datapoints + mcp, etc. |
| **No human-behavior simulation** | No Bézier mouse movement or click/scroll timing models (use [Botasaurus](./botasaurus.md)) |
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
| TLS impersonation (HTTP tier) | **Yes** — `curl_cffi>=0.16.0`, `--impersonate` with Chrome/Firefox/Safari profiles | **A** | Real JA3/JA4 impersonation. The most concretely verifiable stealth feature here. |
| Cloudflare Turnstile / Interstitial solver | **Yes** — `solve_cloudflare` in StealthyFetcher | **A** | The code path exists and is first-party. Whether it succeeds on a given deployment is untested here. |
| CDP-level automation-tell removal | **Delegated** — `patchright>=1.61.2` | **A** | Not Scrapling's work. Its browser-tier evasion is exactly Patchright's, with Patchright's strengths and limits. |
| Fingerprint spoofing (canvas/WebGL/audio) | **No** first-party implementation | **A** | Exposes flags (canvas noise, WebGL toggle, timezone/locale match, WebRTC→proxy) but implements no engine-level spoofing. Camoufox was removed entirely in the 0.4.x line. |
| DataDome / Kasada / Akamai / Incapsula | **No** first-party handling | **A** | Notably, the project **does not claim these** — its README routes them to a third-party paid token API. |

**The maintainer's own scoping is the most useful signal on this page.** Rather than
asserting broad coverage, Scrapling's README explicitly hands Akamai, DataDome, Kasada
and Incapsula to an external paid service. That is a narrower claim than several
competing tools make, and narrower claims that match the source are worth more than
broad ones that don't. Any assessment of Scrapling against those four services is
really an assessment of Patchright plus your IP reputation.

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
| Fingerprint rotation | ⚠️ headers only (browserforge) | ✅ BrowserForge | ⚠️ | ⚠️ |
| CLI tools | ✅ | ❌ | ❌ | ❌ |
| MCP/AI integration | ✅ (10 tools) | ❌ | ❌ | ❌ |
| Multi-language | Python only | Python | Python, Node, .NET | Python |

### vs. Scraping Frameworks

> **Star ratings below are the author's editorial judgment, not measurement.**
> No rubric defines the scale and no benchmark backs any cell. They are retained
> only as a rough relative ordering — see [METHODOLOGY.md](METHODOLOGY.md#rating-policy).


| Feature | Scrapling | Scrapy | BeautifulSoup4 | Playwright (raw) |
|---------|:---------:|:------:|:--------------:|:----------------:|
| Parse speed (relative) | 1.0x | ~1.01x | ~784x slower | N/A |
| Anti-detection built-in | ✅ Three tiers | ❌ | ❌ | ❌ |
| Adaptive element tracking | ✅ | ❌ | ❌ | ❌ |
| Spider framework | ✅ | ✅ (more mature) | ❌ | ❌ |
| JS rendering | ✅ | Via Splash/Playwright | ❌ | ✅ |
| Scrapy interop | ✅ (`@scrapling_response`) | — | ❌ | ❌ |
| Middleware ecosystem | Limited | ⭐⭐⭐⭐⭐ | ❌ | ❌ |
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

# Everything (fetchers + shell + AI)
pip install "scrapling[all]"

# Install the browser binaries + fingerprints
scrapling install
```

Extras (from `pyproject.toml`): `fetchers` (curl_cffi, playwright==1.61.0, patchright==1.61.1, browserforge, apify-fingerprint-datapoints, msgspec, protego), `ai` (mcp, markdownify, + fetchers), `shell` (IPython, markdownify, + fetchers), `all` (ai + shell). Core deps are lxml ≥6.1.1, cssselect, orjson, tld, w3lib.

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
- **AI-integrated scraping** — the 10-tool MCP server for Claude/Cursor-driven workflows.
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
| Browser launch flags | `scrapling/engines/_browsers/_base.py` | canvas noise, WebRTC policy, WebGL, DoH, ad-block |
| Parser / selectors | `scrapling/parser.py` (lxml + cssselect) | CSS/XPath/regex/text + adaptive |
| Adaptive storage | `scrapling/core/storage.py` (`SQLiteStorageSystem`, `StorageSystemMixin`) | signature persistence |
| Spider framework | `scrapling/spiders/` | concurrency, checkpoint, cache, proxy, robots |
| Ad/tracker list | `scrapling/engines/toolbelt/ad_domains.py` | ~3,525 domains |
| Proxy rotation | `scrapling/engines/toolbelt/proxy_rotation.py` (`ProxyRotator`) | thread-safe rotation |
| Scrapy interop | `scrapling/integrations/scrapy.py` | `@scrapling_response` decorator |
| MCP / AI server | `scrapling/core/ai.py` (FastMCP, 10 tools) | AI assistant integration |
| CLI | `scrapling/cli.py` | `shell` / `extract` / `mcp` / `install` |
| `browserforge` | dependency | statistically accurate browser headers |
| `orjson` | dependency | fast JSON serialization |

---

## Conclusion

Scrapling is a **framework, not a stealth engine**. Its browser anti-detection is inherited from **Patchright** (a patched Chromium/Playwright); what Scrapling adds is the *framework around it*: a unified classmethod API, a three-tier fetching strategy (curl_cffi HTTP → Playwright → Patchright stealth), adaptive element tracking, an async spider framework with checkpoints and proxy rotation, Scrapy interop, CLI tools, and a 10-tool MCP server.

**Best for:** Teams that want an all-in-one Python scraping solution with built-in TLS/browser stealth options and adaptive parsing, especially against Cloudflare-Turnstile-class protection.

**Honest assessment:** If you only need browser stealth, use Patchright (or Camoufox for Firefox) directly. If you need a full scraping pipeline with stealth baked in, Scrapling is one of the most complete single-package options — and it is genuinely well-maintained (0.4.10 shipped 2026-07-04, commits within days, ~92% coverage, BSD-3). Just size your expectations: its published benchmarks are parser speed, not WAF pass-rates, and its heavy-hitter stealth is only as good as the Patchright Chromium and proxies you give it.

**Unique value:** The adaptive element tracking system remains the standout — automatic selector recovery when a site's DOM changes is something none of the other tools analyzed in this repository provide.

---

*Analysis conducted for educational purposes against Scrapling v0.4.14 source (`5d213a2`, read 2026-08-14 in an isolated container). Use responsibly.*
