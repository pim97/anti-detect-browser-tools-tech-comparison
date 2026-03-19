# Scrapling - Deep Technical Analysis

> **Tool Type:** All-in-One Web Scraping Framework (Fetching + Parsing + Crawling + Stealth)
> **Repository:** [github.com/D4Vinci/Scrapling](https://github.com/D4Vinci/Scrapling)
> **Approach:** Three-tier fetching (HTTP/Dynamic/Stealth) + adaptive element tracking + spider framework
> **Effectiveness:** High (StealthyFetcher achieves 5/5 stealth with Patchright + Camoufox under the hood)
> **Maintenance:** Active development (v0.4.2, 92% test coverage)

---

## Table of Contents

- [What is Scrapling?](#what-is-scrapling)
- [How It Works](#how-it-works)
- [Anti-Detection Mechanisms](#anti-detection-mechanisms)
- [Adaptive Element Tracking](#adaptive-element-tracking)
- [Performance](#performance)
- [Spider Framework](#spider-framework)
- [Pros and Cons](#pros-and-cons)
- [Installation & Usage](#installation--usage)
- [Comparison with Alternatives](#comparison-with-alternatives)
- [When to Use](#when-to-use)

---

## What is Scrapling?

Scrapling is an **all-in-one Python web scraping framework** that bundles fetching, parsing, anti-detection, crawling, and AI integration into a single package. Unlike the other tools in this repository that focus solely on browser stealth, Scrapling is a full scraping pipeline.

**Key differentiator:** It combines the best of multiple worlds — `curl_cffi` for TLS-impersonated HTTP requests, Patchright for CDP stealth, Camoufox for Firefox-based evasion, and a Scrapy-like spider framework — all behind a unified API. Its adaptive element tracking system can auto-relocate selectors when websites change their DOM structure.

**What makes it different from the other tools analyzed here:** The tools in this repo (Camoufox, Patchright, SeleniumBase, etc.) are **browser automation stealth tools**. Scrapling is a **scraping framework** that *uses* those tools under the hood. It's a layer above, not a competitor.

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
│  │  │ Queue    │  │ (parse)  │  │ (Checkpoint System)   │ │        │
│  │  └──────────┘  └──────────┘  └───────────────────────┘ │        │
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
│  │  │ Patchright (Chromium) OR Camoufox (Firefox)      │   │        │
│  │  │ CDP runtime isolation    Canvas noise injection   │   │        │
│  │  │ WebRTC leak blocking     Cloudflare auto-solve   │   │        │
│  │  │ Headless spoofing        Timezone/locale match    │   │        │
│  │  │ Speed: ⭐⭐⭐            Stealth: ⭐⭐⭐⭐⭐     │   │        │
│  │  └──────────────────────────────────────────────────┘   │        │
│  └───────────────────────┬─────────────────────────────────┘        │
│                          │                                           │
│  ┌───────────────────────▼─────────────────────────────────┐        │
│  │               PARSER / SELECTOR ENGINE                    │        │
│  │  lxml + cssselect (CSS3, XPath, Regex, Text search)      │        │
│  │  Adaptive element tracking (SQLite / custom backends)     │        │
│  │  Similar element finding (fuzzy structural matching)      │        │
│  │  orjson serialization (10x faster than stdlib)            │        │
│  └─────────────────────────────────────────────────────────┘        │
│                                                                      │
│  ┌─────────────────────────────────────────────────────────┐        │
│  │  CLI: shell, extract, mcp   │   MCP Server (6 tools)   │        │
│  └─────────────────────────────────────────────────────────┘        │
└─────────────────────────────────────────────────────────────────────┘
```

### Three-Tier Fetching System

#### Tier 1: Fetcher — HTTP with TLS Impersonation

The fastest option. Uses `curl_cffi` to send HTTP requests with **real browser TLS fingerprints** (JA3/JA4), avoiding the most common non-browser detection vector.

```python
from scrapling import Fetcher

fetcher = Fetcher(auto_match=False)

# Impersonates Chrome's TLS fingerprint at the protocol level
response = fetcher.get(
    'https://example.com',
    stealthy_headers=True,   # Real browser headers via browserforge
    google_search=True,      # Referer: Google search (mimics organic traffic)
    follow_redirects=True,
)
```

**Why this matters for anti-detection:**
- `curl_cffi` sends HTTP requests with the exact TLS ClientHello that Chrome/Firefox/Safari would send
- JA3/JA4 fingerprinting services see a real browser signature, not Python's `requests` or `aiohttp`
- `browserforge` generates statistically accurate headers matching the impersonated browser
- No JavaScript execution = no browser fingerprinting surface at all

**Supported impersonation targets:**

| Browser | Versions |
|---------|----------|
| Chrome | 99-136+ |
| Firefox | 91-135+ |
| Safari | 15.3-18+ |
| Edge | 99-136+ |
| Tor Browser | ✅ |

#### Tier 2: DynamicFetcher — Playwright Browser

For JavaScript-rendered content. Standard Playwright automation with some convenience features.

```python
from scrapling import DynamicFetcher

fetcher = DynamicFetcher(auto_match=False)

response = fetcher.get(
    'https://spa-site.com',
    headless=True,
    wait_selector='div.content',  # Wait for specific element
    network_idle=True,            # Wait until network is quiet
)
```

**No special anti-detection** — this is vanilla Playwright. Detectable by standard checks (`navigator.webdriver`, CDP leak, etc.). Use StealthyFetcher when you need stealth.

#### Tier 3: StealthyFetcher — Maximum Anti-Detection

This is where Scrapling gets interesting from an anti-detection perspective. It wraps **Patchright** (default) or **Camoufox** as the browser engine:

```python
from scrapling import StealthyFetcher

fetcher = StealthyFetcher(auto_match=False)

response = fetcher.get(
    'https://protected-site.com',
    headless=True,
    solve_cloudflare=True,    # Auto-solve Turnstile/Interstitial
    block_webrtc=True,        # Prevent IP leakage via WebRTC
    hide_canvas=True,         # Inject canvas noise (anti-fingerprinting)
    disable_webgl=True,       # Disable WebGL to prevent GPU fingerprinting
)
```

**With Camoufox (Firefox engine):**

```python
response = fetcher.get(
    'https://protected-site.com',
    headless=True,
    solve_cloudflare=True,
    block_webrtc=True,
    hide_canvas=True,
    use_camoufox=True,        # Switch from Patchright to Camoufox
)
```

**What StealthyFetcher does under the hood:**

```
┌──────────────────────────────────────────────────────────────────┐
│                    STEALTHY FETCHER PIPELINE                       │
├──────────────────────────────────────────────────────────────────┤
│                                                                    │
│  1. Browser Engine Selection                                       │
│     ├─ Default: Patchright (Chromium, CDP stealth)                │
│     └─ Optional: Camoufox (Firefox, C++ fingerprint injection)    │
│                                                                    │
│  2. Anti-Detection Layers Applied                                  │
│     ├─ CDP Runtime.enable bypass (Patchright)                     │
│     ├─ navigator.webdriver = false                                 │
│     ├─ Canvas noise injection (if hide_canvas=True)               │
│     ├─ WebRTC blocking (if block_webrtc=True)                     │
│     ├─ WebGL disable (if disable_webgl=True)                      │
│     ├─ Timezone/Locale matching (if timezone_id set)              │
│     └─ Headless detection circumvention                            │
│                                                                    │
│  3. Cloudflare Handling (if solve_cloudflare=True)                │
│     ├─ Detect Turnstile challenge page                             │
│     ├─ Wait for challenge iframe                                   │
│     ├─ Auto-interact with challenge                                │
│     └─ Wait for redirect to target page                            │
│                                                                    │
│  4. Page Loading & Content Extraction                              │
│     ├─ Network idle detection                                      │
│     ├─ Optional wait_selector                                      │
│     └─ Return Response object with parsed HTML                     │
│                                                                    │
└──────────────────────────────────────────────────────────────────┘
```

---

## Anti-Detection Mechanisms

### Per-Tier Stealth Comparison

| Detection Method | Fetcher (HTTP) | DynamicFetcher | StealthyFetcher |
|-----------------|:--------------:|:--------------:|:---------------:|
| TLS fingerprinting (JA3/JA4) | ✅ Impersonated | ✅ Real browser | ✅ Real browser |
| `navigator.webdriver` | N/A (no JS) | ❌ Detectable | ✅ Bypassed |
| `Runtime.enable` CDP leak | N/A | ❌ Detectable | ✅ Patchright bypass |
| Canvas fingerprinting | N/A | ❌ Exposed | ✅ Noise injection |
| WebRTC IP leak | N/A | ❌ Exposed | ✅ Blocked |
| WebGL fingerprinting | N/A | ❌ Exposed | ✅ Can disable |
| Headless detection | N/A | ❌ Detectable | ✅ Circumvented |
| Cloudflare Turnstile | ❌ | ❌ | ✅ Auto-solved |
| Browser header consistency | ✅ browserforge | ⚠️ Basic | ✅ Full spoofing |
| HTTP/2 & HTTP/3 | ✅ | ✅ | ✅ |

### TLS Fingerprint Impersonation (Fetcher)

This is the **most important stealth feature** for HTTP-only scraping. Most bot detection starts with TLS fingerprinting — Python's `requests` library has a distinctive JA3 hash that instantly flags it as non-browser traffic.

```python
# Standard Python requests - INSTANTLY detected
# JA3: 771,4866-4867-4865-49196-49200-159-52393-52392-52394...
# → Known bot signature

# Scrapling Fetcher with curl_cffi
# JA3: matches real Chrome 131 exactly
# → Passes TLS fingerprint check
response = fetcher.get('https://example.com')  # Impersonates Chrome by default
```

### Cloudflare Auto-Solving (StealthyFetcher)

The `solve_cloudflare=True` parameter handles both Turnstile challenges and interstitial pages without external CAPTCHA-solving APIs:

```python
response = StealthyFetcher().get(
    'https://cloudflare-protected.com',
    solve_cloudflare=True,
    # Internally:
    # 1. Detects challenge page
    # 2. Waits for Turnstile iframe to load
    # 3. Interacts with challenge
    # 4. Waits for redirect
    # 5. Returns the actual page content
)
```

**Important caveat:** This works because Patchright/Camoufox pass the browser environment checks. It's not solving the CAPTCHA — it's presenting a browser that Cloudflare trusts enough to auto-pass.

---

## Adaptive Element Tracking

This is Scrapling's **most unique feature** — no other tool in this repository offers anything like it.

### The Problem

Websites change their HTML structure regularly. A CSS selector that works today (`div.product-card > h2.title`) may break tomorrow when the site renames classes or restructures the DOM.

### How Scrapling Solves It

```python
from scrapling import Fetcher

fetcher = Fetcher(auto_match=True)  # Enable adaptive tracking

# First run: finds elements and saves their "signatures"
response = fetcher.get('https://shop.com')
products = response.css('.product-card')  # Saves element fingerprint to SQLite

# Later run: site changed .product-card to .item-listing
response = fetcher.get('https://shop.com')
products = response.css('.product-card')  # Auto-finds .item-listing via saved signature
```

**How it works internally:**

```
┌─────────────────────────────────────────────────────────┐
│              ADAPTIVE ELEMENT TRACKING                     │
├─────────────────────────────────────────────────────────┤
│                                                           │
│  1. First scrape:                                        │
│     Element found via CSS selector                        │
│     ├─ Record tag name, attributes, text content          │
│     ├─ Record parent chain (structural position)          │
│     ├─ Record sibling context                             │
│     └─ Save signature to SQLite (or custom backend)       │
│                                                           │
│  2. Subsequent scrape (selector fails):                   │
│     ├─ Load saved signature                               │
│     ├─ Score all elements by similarity                    │
│     │   ├─ Tag match                                      │
│     │   ├─ Attribute similarity                           │
│     │   ├─ Text content similarity                        │
│     │   ├─ Structural position similarity                 │
│     │   └─ Sibling context similarity                     │
│     ├─ Return best match above threshold                  │
│     └─ Update signature with new element data             │
│                                                           │
│  Storage backends:                                        │
│     ├─ SQLite (default, thread-safe)                      │
│     ├─ Redis (custom, via StorageSystemMixin)             │
│     └─ Any custom backend (implement save/retrieve)       │
│                                                           │
└─────────────────────────────────────────────────────────┘
```

### Similar Element Finding

Related feature — find elements structurally similar to a known element:

```python
# Find one product card
card = response.css('.product-card').first

# Find all elements with similar structure (even if classes differ)
all_cards = card.find_similar()
```

---

## Performance

### Parsing Benchmarks (5000 nested elements, 100+ runs)

| Library | Average Time | vs Scrapling |
|---------|:----------:|:------------:|
| **Scrapling** | **2.02ms** | **1.0x (baseline)** |
| Parsel (Scrapy) | 2.04ms | 1.01x |
| Raw lxml | 2.54ms | 1.26x |
| PyQuery | 24.17ms | ~12x slower |
| BeautifulSoup4 | 1,584.31ms | **~784x slower** |

### Adaptive Element Finding

| Library | Average Time | vs Scrapling |
|---------|:----------:|:------------:|
| **Scrapling** | **2.39ms** | **1.0x (baseline)** |
| AutoScraper | 12.45ms | 5.2x slower |

### Other Performance Features

- **orjson** for JSON serialization (10x faster than stdlib `json`)
- Lazy-loaded sessions (created on-demand)
- Memory-efficient element iteration
- HTTP/3 support in Fetcher tier

---

## Spider Framework

Scrapling includes a Scrapy-like spider framework for large-scale crawling:

```python
from scrapling import Spider, Request

class ProductSpider(Spider):
    start_urls = ['https://shop.com/products']

    async def parse(self, response):
        for product in response.css('.product-card'):
            yield {
                'name': product.css('h2::text').get(),
                'price': product.css('.price::text').get(),
            }

        # Follow pagination
        next_page = response.css('a.next::attr(href)').get()
        if next_page:
            yield Request(url=next_page, callback=self.parse)

# Run the spider
result = ProductSpider().run()
```

### Spider Features

| Feature | Details |
|---------|---------|
| **Concurrent requests** | Configurable per-spider concurrency |
| **Per-domain throttling** | `wait_between_requests` delay |
| **Multi-session support** | Mix Fetcher, DynamicFetcher, StealthyFetcher in one spider |
| **Pause/Resume** | Checkpoint system with `crawldir` — survives Ctrl+C |
| **Streaming mode** | `spider.stream()` async generator for real-time processing |
| **Blocked request detection** | Auto-detect and retry with custom logic |
| **Export formats** | JSON, JSONL built-in |
| **Stats tracking** | `CrawlStats` with real-time metrics |

### Multi-Session Spider

Route different requests through different fetcher tiers:

```python
class MultiSpider(Spider):
    start_urls = ['https://shop.com']

    def setup(self):
        # Register sessions by ID
        self.register_session('fast', FetcherSession())
        self.register_session('stealth', StealthySession())

    async def parse(self, response):
        # Use fast HTTP for product listing
        for url in response.css('a.product::attr(href)').getall():
            yield Request(url=url, callback=self.parse_product, session_id='fast')

        # Use stealth for protected pages
        yield Request(
            url='https://shop.com/api/prices',
            callback=self.parse_prices,
            session_id='stealth'
        )
```

---

## CLI & MCP Server

### CLI Tools

```bash
# Interactive scraping shell (IPython-based)
scrapling shell

# Extract content without writing code
scrapling extract get 'https://example.com' output.md
scrapling extract fetch 'https://spa-site.com' output.md        # Dynamic
scrapling extract stealthy-fetch 'https://protected.com' output.md  # Stealth

# Launch MCP server for AI integration
scrapling mcp
scrapling mcp --http --port 8080
```

### MCP Server (AI Integration)

Exposes 6 tools for AI assistants (Claude, Cursor, etc.):

| Tool | Description |
|------|------------|
| `get` | Fast HTTP with TLS impersonation |
| `bulk_get` | Parallel multi-URL HTTP |
| `fetch` | Dynamic content via browser |
| `bulk_fetch` | Parallel multi-URL dynamic |
| `stealthy_fetch` | Anti-bot bypass via stealth browser |
| `bulk_stealthy_fetch` | Parallel multi-URL stealth |

Smart CSS pre-processing extracts relevant HTML before sending to the AI model, reducing token usage.

---

## Pros and Cons

### Advantages

| Pro | Details |
|-----|---------|
| **All-in-one framework** | Fetching + parsing + crawling + stealth in one package |
| **Three stealth tiers** | Pick the right level: HTTP-only, dynamic, or full stealth |
| **TLS impersonation** | curl_cffi matches real browser JA3/JA4 signatures |
| **Adaptive tracking** | Auto-relocate elements when sites change DOM |
| **Blazing fast parser** | Tied with Parsel, 784x faster than BeautifulSoup4 |
| **Cloudflare auto-solve** | Built-in Turnstile/Interstitial handling, no API needed |
| **Spider framework** | Scrapy-like crawling with pause/resume |
| **Multi-engine stealth** | Patchright (Chromium) or Camoufox (Firefox) |
| **MCP integration** | Native AI assistant support |
| **Well-tested** | 92% coverage, full type hints, active development |

### Disadvantages

| Con | Details |
|-----|---------|
| **Python only** | No Node.js, .NET, or other language support |
| **Stealth is borrowed** | StealthyFetcher wraps Patchright/Camoufox — not its own anti-detection innovation |
| **Heavy dependencies** | Full install pulls Playwright, curl_cffi, Patchright, browserforge, etc. |
| **Newer project** | Less battle-tested at scale compared to Scrapy ecosystem |
| **No human behavior simulation** | No Bézier mouse movements or click timing randomization |
| **Adaptive tracking has limits** | Major site redesigns can still break saved signatures |
| **StealthyFetcher speed** | Browser-based stealth is inherently slower than HTTP-only |

---

## Services Bypassed

| Service | Fetcher (HTTP) | StealthyFetcher (Patchright) | StealthyFetcher (Camoufox) |
|---------|:--------------:|:----------------------------:|:--------------------------:|
| Cloudflare WAF | ⚠️ Basic only | ✅ | ✅ |
| Cloudflare Turnstile | ❌ | ✅ Auto-solved | ⚠️ |
| DataDome | ❌ | ✅ (via Patchright) | ✅ (via Camoufox) |
| Kasada | ❌ | ✅ (via Patchright) | ⚠️ |
| PerimeterX | ❌ | ⚠️ | ✅ (via Camoufox) |
| Akamai | ❌ | ⚠️ | ⚠️ |
| TLS fingerprint checks | ✅ Impersonated | ✅ Real browser | ✅ Real browser |

✅ = Reliably bypasses | ⚠️ = Partial/conditional | ❌ = Not effective

> **Note:** Scrapling's anti-bot effectiveness in StealthyFetcher mode is **inherited from Patchright and Camoufox**. Its unique value-add is the framework around them (adaptive parsing, spider, multi-session, CLI/MCP), not the stealth itself.

---

## Comparison with Alternatives

### vs. Dedicated Anti-Detection Tools

| Feature | Scrapling | Camoufox | Patchright | SeleniumBase |
|---------|:---------:|:--------:|:----------:|:------------:|
| HTTP-only stealth (TLS) | ✅ | ❌ | ❌ | ❌ |
| Browser stealth | ✅ (via Patchright/Camoufox) | ✅ Native | ✅ Native | ✅ Native |
| HTML parser built-in | ✅ (fastest tier) | ❌ | ❌ | ❌ |
| Adaptive element tracking | ✅ Unique | ❌ | ❌ | ❌ |
| Spider/crawler framework | ✅ | ❌ | ❌ | ❌ |
| CAPTCHA solving | ⚠️ Cloudflare only | ❌ | ❌ | ✅ Multiple |
| Human behavior simulation | ❌ | ✅ Mouse | ❌ | ✅ |
| Fingerprint rotation | ❌ | ✅ BrowserForge | ⚠️ | ⚠️ |
| CLI tools | ✅ | ❌ | ❌ | ❌ |
| MCP/AI integration | ✅ | ❌ | ❌ | ❌ |
| Multi-language | Python only | Python | Python, Node, .NET | Python |

### vs. Scraping Frameworks

| Feature | Scrapling | Scrapy | BeautifulSoup4 | Playwright (raw) |
|---------|:---------:|:------:|:--------------:|:----------------:|
| Parse speed (relative) | 1.0x | 1.01x | 784x slower | N/A |
| Anti-detection built-in | ✅ Three tiers | ❌ | ❌ | ❌ |
| Adaptive element tracking | ✅ | ❌ | ❌ | ❌ |
| Spider framework | ✅ | ✅ (more mature) | ❌ | ❌ |
| JS rendering | ✅ | Via Splash/Playwright | ❌ | ✅ |
| Middleware ecosystem | Limited | ⭐⭐⭐⭐⭐ | ❌ | ❌ |
| Community/plugins | Growing | Massive | Massive | Large |
| Async support | ✅ | ✅ | ❌ | ✅ |

---

## Installation & Usage

### Quick Start

```bash
# Core only (parsing)
pip install scrapling

# With HTTP fetcher (TLS impersonation)
pip install scrapling[fetcher]

# With all fetchers (HTTP + Dynamic + Stealth)
pip install scrapling[all]

# Install browsers
scrapling install
```

### Basic Fetching

```python
from scrapling import Fetcher, StealthyFetcher

# Fast HTTP with TLS impersonation
resp = Fetcher(auto_match=False).get('https://example.com')
print(resp.status)
print(resp.css('title::text').get())

# Stealth with Cloudflare bypass
resp = StealthyFetcher(auto_match=False).get(
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

# Filter-based search
links = resp.find_all('a', class_='product-link')

# Text search
elem = resp.find_by_text('Add to Cart', partial=True)

# Regex
emails = resp.find_by_regex(r'[\w.]+@[\w.]+\.\w+')

# Find structurally similar elements
first_card = resp.css('.product-card').first
all_cards = first_card.find_similar()
```

---

## When to Use

### Recommended For

- **All-in-one scraping projects** — don't want to stitch Scrapy + Playwright + stealth plugins together
- **Adaptive scraping** — target sites that frequently change their DOM structure
- **HTTP-only stealth** — need TLS impersonation without browser overhead
- **Mixed stealth requirements** — some pages need HTTP-only, others need full browser stealth
- **AI-integrated scraping** — MCP server for Claude/Cursor-driven scraping workflows
- **Python teams** already familiar with CSS/XPath selectors
- **Rapid prototyping** — CLI `extract` command for quick one-off scrapes

### Not Recommended For

- **Maximum browser stealth** — use Camoufox or Patchright directly for finer control
- **Human behavior simulation** — no Bézier mouse, click timing, or scroll patterns (use Botasaurus)
- **Non-Python projects** — Python only
- **Massive scale crawling** — Scrapy's middleware ecosystem and community is more mature
- **Multi-CAPTCHA solving** — only handles Cloudflare (use SeleniumBase for reCAPTCHA, hCaptcha, etc.)
- **When you need one specific tool** — if you only need stealth browsing, Scrapling's framework overhead is unnecessary

---

## Key Files & Dependencies

| Component | Technology | Purpose |
|-----------|-----------|---------|
| `curl_cffi` | HTTP client | TLS fingerprint impersonation |
| `browserforge` | Header generation | Statistically accurate browser headers |
| `patchright` | Patched Playwright | CDP stealth (StealthyFetcher default) |
| `camoufox` | Custom Firefox | C++ fingerprint injection (StealthyFetcher alt) |
| `lxml` + `cssselect` | Parser | High-performance HTML parsing |
| `orjson` | Serialization | 10x faster JSON |
| `playwright` | Browser automation | DynamicFetcher engine |

---

## Conclusion

Scrapling is a **framework, not a stealth tool**. Its anti-detection capabilities are inherited from Patchright and Camoufox — what it adds is the *framework around them*: a unified API, three-tier fetching strategy, adaptive element tracking, a spider framework, CLI tools, and MCP integration.

**Best for:** Teams that want an all-in-one Python scraping solution with built-in stealth options and adaptive parsing.

**Honest assessment:** If you only need browser stealth, use Patchright or Camoufox directly. If you need a full scraping pipeline with stealth baked in, Scrapling is the most complete single-package option available.

**Unique value:** The adaptive element tracking system is genuinely novel — no other tool analyzed in this repository offers automatic selector recovery when websites change.

---

*Analysis conducted for educational purposes. Use responsibly.*
