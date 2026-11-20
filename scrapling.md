# Scrapling - Deep Technical Analysis

> **Tool Type:** All-in-One Web Scraping Framework (Fetching + Parsing + Crawling + Stealth)
> **Repository:** [github.com/D4Vinci/Scrapling](https://github.com/D4Vinci/Scrapling)
> **Approach:** Two fetch engines (`curl_cffi` HTTP / Patchright Chromium, plus CDP remote sessions) + adaptive element tracking + spider framework
> **What is verified:** `pyproject.toml` requires `curl_cffi>=0.16.3` (HTTP-tier TLS impersonation) and `patchright>=1.62.1` (minimum versions, not exact pins). Since 0.5 every browser path — `StealthyFetcher`, the sessions, `RemoteSession`, the MCP server — imports `patchright` only; **the browser-tier evasion is Patchright's**, inherited wholesale rather than implemented here (**Tier A**)
> **Anti-bot service claims:** Cloudflare Turnstile handled out of the box (**Tier B**). The README's sponsor table (`README.md:131-137`) **lists a third-party paid token API for Akamai, DataDome, Kasada and Incapsula** rather than claiming coverage of them. Since 0.5 the README also says the MCP server lets suitable AI models "bypass any CAPTCHA" (`README.md:292`; **Tier B**, no measurement published).
> **Maintenance:** latest release **v0.5.1** (2026-11-04), after **v0.5** (2026-10-17). 0.5 removed the plain-Playwright `DynamicFetcher`/`DynamicSession` tier, `capture_xhr` and `keep_cdata`, rebuilt the MCP server (17 tools) and added network recording, saved login state and Shadow DOM capture; 0.5.1 moved CDP connections to new `RemoteSession` classes. The 7 commits after the v0.5.1 tag touch README, docs, images, `includes/` and a stale-issue workflow; no code. 104.6k stars, 52 contributors, 24 open issues. BSD-3-Clause.
> **Verified:** 2026-11-20 against `D4Vinci/Scrapling` @ `2998c9e`.

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

**What makes it different from the other tools analyzed here:** The tools in this repo ([Camoufox](./camoufox.md), [Patchright](./patchright.md), [SeleniumBase](./seleniumbase.md), etc.) are **browser automation stealth tools**. Scrapling is a **scraping framework** that *uses* one of them (Patchright) under the hood for its browser tier, and layers fetching / parsing / crawling on top. It's a layer above, not a competitor.

**Project facts (verified against source, 2026-11-20):**

| Attribute | Value | Evidence |
|-----------|-------|----------|
| Current version | **0.5.1** | `pyproject.toml:8` `version = "0.5.1"`, `scrapling/__init__.py:2` `__version__ = "0.5.1"`; GitHub release `v0.5.1` and PyPI upload 2026-11-04 |
| Release cadence | v0.4.15 (2026-08-23), v0.5 (2026-10-17), v0.5.1 (2026-11-04); the minor bump carries breaking changes listed in `docs/migrating-to-v0.5.md` | `docs/changelog.md:10`, `59`, `142` (the changelog moved from the repository root to `docs/changelog.md` in 0.5) |
| Last commit | 2026-11-17 (`2998c9e`, sponsor edit); last commit touching `scrapling/` or `pyproject.toml`: 2026-11-04 (`fb26a7a`) | `git log -1`; `git diff --stat v0.5.1..HEAD` lists README, docs, images, `includes/sponsors.html`, `.github/workflows/stale.yml` |
| Community | 104,584 stars, 10,940 forks, 52 contributors, 24 open issues (2026-11-20) | GitHub API |
| Language | **Python only** (CPython) | `Programming Language :: Python :: 3 :: Only` classifier |
| Python versions | **3.10 – 3.13** | `requires-python = ">=3.10"` |
| License | **BSD 3-Clause** | `LICENSE`; `License :: OSI Approved :: BSD License` |
| Author/maintainer | Karim Shoair (D4Vinci) | `pyproject.toml` authors |
| Dev status | `4 - Beta` | `pyproject.toml:38` classifier |

> **Correction vs. earlier editions of this page:** the page once said "v0.4.2" and described StealthyFetcher as "Patchright **or Camoufox**" with a `use_camoufox=True` switch. Since **0.3.13** (2026-01-01; `docs/changelog.md:720-728`) **the package no longer uses Camoufox** — `rg -i camoufox scrapling/ pyproject.toml tests/` returns nothing at `2998c9e`, and no `use_camoufox` parameter exists. The user-side recipe for swapping Camoufox back in by subclassing `StealthySession`, which the 2026-10-13 edition located at `docs/fetching/stealthy.md:264-340`, is no longer in the current docs; the 0.3.13 changelog entry links to the copy in the `v0.3.13`-tagged docs (`docs/changelog.md:724`).

> **Corrections in the 2026-09-30 re-verification:** (1) the benchmark tables now match the README; (2) the MCP server was registered through `MCPServer` from the `mcp` SDK, not `FastMCP`; (3) `patchright` and `playwright` are minimum versions (`>=`), not exact pins; (4) with `impersonate` set, request headers come from `curl_cffi`, not `browserforge`; (5) `SQLiteStorageSystem` is described by what its code sets (`check_same_thread=False`, `RLock`, WAL); (6) `scrapling install` runs Playwright's Chromium and system-dependency install, not a fingerprint download; (7) `dns_over_https` and `block_ads` were also accepted by the (since removed) `DynamicFetcher`.

---

## How It Works

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                     SCRAPLING ARCHITECTURE (0.5.x)                   │
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
│  │                  FETCHING ENGINES                         │        │
│  │                                                           │        │
│  │  HTTP: Fetcher / FetcherSession                          │        │
│  │  ┌──────────────────┐                                    │        │
│  │  │ curl_cffi        │  no browser process,               │        │
│  │  │ TLS impersonation│  Chrome/FF/Safari profiles         │        │
│  │  └──────────────────┘                                    │        │
│  │                                                           │        │
│  │  Browser: StealthyFetcher / StealthySession              │        │
│  │           RemoteSession (CDP attach, 0.5.1)              │        │
│  │  ┌──────────────────────────────────────────────────┐   │        │
│  │  │ Patchright (Chromium, CDP stealth)               │   │        │
│  │  │ Canvas noise flag        Cloudflare auto-solve    │   │        │
│  │  │ WebRTC → proxy-only      Timezone/locale          │   │        │
│  │  │ WebGL toggle             real_chrome              │   │        │
│  │  │ network recording · saved state · Shadow DOM     │   │        │
│  │  └──────────────────────────────────────────────────┘   │        │
│  └───────────────────────┬─────────────────────────────────┘        │
│                          │                                           │
│  ┌───────────────────────▼─────────────────────────────────┐        │
│  │               PARSER / SELECTOR ENGINE                    │        │
│  │  lxml + cssselect (CSS3, XPath, Regex, Text search)      │        │
│  │  Adaptive element tracking (SQLite / custom backends)     │        │
│  │  Similar element finding (fuzzy structural matching)      │        │
│  │  orjson serialization                                      │        │
│  └─────────────────────────────────────────────────────────┘        │
│                                                                      │
│  ┌─────────────────────────────────────────────────────────┐        │
│  │  CLI: shell / extract / mcp / install │ MCP Server (17)  │        │
│  │  Scrapy integration (@scrapling_response decorator)      │        │
│  └─────────────────────────────────────────────────────────┘        │
└─────────────────────────────────────────────────────────────────────┘
```

**API note:** the fetchers are driven through **classmethods** and a `.fetch()` entrypoint (since 0.3): `Fetcher.get(...)` (`scrapling/fetchers/requests.py:31-44`) and `StealthyFetcher.fetch(...)` (`scrapling/fetchers/stealth_chrome.py:13-14`). The adaptive feature is the `adaptive` attribute/keyword (renamed from `auto_match` in 0.3). Persistent `FetcherSession` / `StealthySession` / `AsyncStealthySession` classes reuse a session across requests; `scrapling.fetchers` exports exactly these plus `Fetcher`, `AsyncFetcher`, `ProxyRotator`, `RemoteSession` and `AsyncRemoteSession` (`scrapling/fetchers/__init__.py:11-32`).

**Breaking changes in 0.5 / 0.5.1 (Tier A, `docs/migrating-to-v0.5.md`, confirmed in source):**

- **`DynamicFetcher`, `DynamicSession`, `AsyncDynamicSession` and `PlayWrightFetcher` are removed**, with `scrapling/fetchers/chrome.py` and `engines/_browsers/_controllers.py`. The migration guide maps each to its stealthy counterpart. No module imports the `playwright` package any more; every browser import is `patchright` (`_stealth.py:7-10`, `_base.py:6-17`, `_page.py:4-5`, `toolbelt/convertor.py:7-9`, `toolbelt/navigation.py:7-9`).
- **`cdp_url` moved to `RemoteSession` / `AsyncRemoteSession`** (0.5.1, `scrapling/engines/_browsers/_remote.py`). Passing `cdp_url` or `new_context` to `StealthyFetcher`/`StealthySession` raises `TypeError`, as do `capture_xhr` (replaced by `record_requests=True` plus `session.network`) and `real_chrome` on a remote session (`_validators.py:187-195`, `259-265`).
- **`extra_flags` adds to the built-in stealth flags** instead of replacing them (`_base.py:541-542`; release note `docs/changelog.md:102`).
- **`keep_cdata` is removed** from the parser and fetcher configuration.

Browser sessions keep their tabs open after a request and reuse a free tab, re-applying the request's settings on each reuse (since 0.4.15); `close_pages()` closes every open tab (`_base.py:86-90`, `_page.py:78`, `93`; `docs/fetching/stealthy.md:197-207`).

### Fetching Engines

#### HTTP: Fetcher — TLS Impersonation

The fastest option. Uses `curl_cffi` to send HTTP requests with **real browser TLS fingerprints** (JA3/JA4), avoiding the most common non-browser detection vector. (`scrapling/engines/static.py:7-9` imports from `curl_cffi`; the `impersonate` parameter is applied at `static.py:108-109`, `130`.)

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
- With `impersonate` set (default `"chrome"`, `static.py:74`), `curl_cffi` supplies the browser's headers and Scrapling adds only a Google `referer` when `stealthy_headers=True`; `browserforge` generates headers only when `impersonate` is disabled (`static.py:179-205`). Since 0.5 a per-request header replaces a session header of the same name regardless of letter case (`static.py:185-192`).
- No JavaScript execution = no browser-DOM fingerprinting surface at all (but also no JS-rendered content).

**Impersonation targets:** Scrapling's `impersonate` argument (`ImpersonateType = BrowserTypeLiteral | List[...] | None`, `scrapling/engines/_browsers/_types.py:27`) is passed straight through to **curl_cffi**, so the concrete browser/version list is whatever the installed `curl_cffi` (>=0.16.3) supports. You pass a family name like `chrome`, `firefox`, `safari` (defaults to the latest Chrome), or a list to randomize per-request (`_select_random_browser`, `static.py:37-48`). HTTP/3 is available but the code warns it may conflict with `impersonate` (`static.py:170-174`).

> **Verification note:** an earlier edition's table of exact versions ("Chrome 99–136, Firefox 91–135, Safari 15.3–18, Edge 99–136, Tor") is **not defined in Scrapling** — those come from curl_cffi and drift with its releases. Scrapling itself only defines the family-name plumbing.

#### Browser: StealthyFetcher — Patchright Chromium

Since 0.5 this is the **only** local browser engine. It is built **on top of a Chromium browser driven by [Patchright](./patchright.md)** (`scrapling/engines/_browsers/_stealth.py:7-10` imports `patchright.sync_api` / `patchright.async_api`; the `fetchers` extra requires `patchright>=1.62.1`, `pyproject.toml:77`). The class docstring states it is "completely stealthy built on top of Chromium" (`stealth_chrome.py:8`).

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
    pierce_shadow=False,      # 0.5: include open Shadow DOM in the HTML
)
```

> **Former `DynamicFetcher` tier:** through 0.4.15 a second browser class drove Chromium through the unpatched `playwright` package without `STEALTH_ARGS`. It was removed in 0.5; `scrapling extract fetch` and the shell's `fetch()` now call `StealthyFetcher` (`cli.py:589-661`, `scrapling/core/shell.py:559`; `docs/migrating-to-v0.5.md`). The `PlaywrightConfig` struct survives only as the base class of `StealthConfig` (`_validators.py:59`, `139`).

**What StealthyFetcher does under the hood (as of 0.5.1; identical on `2998c9e`):**

```
┌──────────────────────────────────────────────────────────────────┐
│                    STEALTHY FETCHER PIPELINE                       │
├──────────────────────────────────────────────────────────────────┤
│                                                                    │
│  1. Browser Engine                                                 │
│     └─ Chromium via Patchright (CDP stealth). Camoufox NOT used.   │
│        real_chrome=True → your installed Chrome (channel=chrome); │
│        RemoteSession(cdp_url=...) → attach to a running browser.  │
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
│     └─ browserforge User-Agent pinned to Patchright's Chromium    │
│                                                                    │
│  3. Cloudflare Handling (if solve_cloudflare=True)                │
│     ├─ _detect_cloudflare(): classify Turnstile / Interstitial /  │
│     │    embedded turnstile challenge from page content           │
│     ├─ _cloudflare_solver(): wait for challenge, click, poll      │
│     └─ Retry until challenge clears (max 3 re-solves)             │
│                                                                    │
│  4. Page Loading & Content Extraction                              │
│     ├─ network_idle / load_dom / wait_selector                    │
│     ├─ optional page_setup + page_action callbacks                │
│     ├─ optional network recording (record_requests=True)          │
│     └─ Return Response object with parsed HTML                     │
│                                                                    │
└──────────────────────────────────────────────────────────────────┘
```

> **Corrections vs. earlier editions:** (1) `disable_webgl=True` is not the real parameter — WebGL is controlled by `allow_webgl` (default **True**, `_validators.py:140`; the docstring warns disabling it is risky because many WAFs now check WebGL is present). (2) `block_webrtc` does **not** "block" WebRTC — it forces Chromium to route WebRTC only through the proxy (`disable_non_proxied_udp`), preventing local-IP leaks. (3) `hide_canvas` is a native Chromium **launch flag** (`--fingerprinting-canvas-image-data-noise`), not JS-injected canvas noise. (4) There is no Camoufox/Firefox path. All four at `_base.py:592-601`.

**Fixed launch and context settings (Tier A, `2998c9e`):** the stealth engine launches Chromium with the 54-entry `STEALTH_ARGS` set (includes `--disable-blink-features=AutomationControlled`; 0.5 added `--do-not-de-elevate` for elevated Windows shells) plus 11 `DEFAULT_ARGS`, removes 5 `HARMFUL_ARGS` from Playwright's defaults (including `--enable-automation`), and sets `is_mobile=False`, `has_touch=False`, `service_workers="allow"`, `ignore_https_errors=True`, a 1920x1080 screen and viewport, and `permissions=["geolocation", "notifications"]` (`scrapling/engines/constants.py:15-98`; `_base.py:503-506`, `578-589`). `color_scheme="dark"` and `device_scale_factor=2` are set on every browser context (`_base.py:502`; the code comment says dark mode avoids a CreepJS preferred-light-colour check). A `locale` is applied through `--lang` and `--accept-lang` launch flags rather than the Playwright context option (`_base.py:545-548`). When headless and no `useragent` is given, the context gets a generated User-Agent (`_base.py:527-532`) whose Chrome major is rewritten to the version Patchright's bundled `browsers.json` names (`toolbelt/fingerprints.py:46`, `87-89`; it read `playwright`'s first before 0.5).

**Remote sessions (0.5.1, Tier A):** `RemoteSession` / `AsyncRemoteSession` subclass the stealth sessions but call `connect_over_cdp` on an existing browser (`_remote.py:40-48`, `69-79`), so **none of the launch flags above apply** (`_browser_options = {}`, `_remote.py:13`). With the default `new_context=True` they create a context with the usual context options, `locale` passed as a context option (`_remote.py:14-17`); with `new_context=False` they borrow the browser's default context and ignore `useragent`, `locale`, `timezone_id`, `proxy`, `proxy_rotator` and `additional_args` (`_remote.py:18-19`; `_validators.py:157-160`), leaving that context and its tabs open on close (`_remote.py:38`; `_base.py:100`).

---

## Anti-Detection Mechanisms

### Per-Engine Stealth Comparison

| Detection Method | Fetcher (HTTP) | StealthyFetcher / StealthySession | RemoteSession (CDP attach) |
|-----------------|:--------------:|:---------------:|:---------------:|
| TLS fingerprinting (JA3/JA4) | ✅ Impersonated (curl_cffi) | ✅ Real browser | ✅ Real browser (whatever is attached) |
| `navigator.webdriver` | N/A (no JS) | ✅ Bypassed (Patchright) | depends on the attached browser's launch; Patchright client |
| `Runtime.enable` CDP leak | N/A | ✅ Patchright bypass | Patchright client |
| Canvas fingerprinting | N/A | ✅ Noise flag (`hide_canvas`) | ❌ launch flags not applied |
| WebRTC local-IP leak | N/A | ✅ Proxy-only routing (`block_webrtc`) | ❌ launch flags not applied |
| WebGL fingerprinting | N/A | ⚠️ Can disable (`allow_webgl=False`, not recommended) | ❌ launch flags not applied |
| DNS leak on proxy | N/A | ✅ `dns_over_https` (opt-in) | ❌ launch flag not applied |
| Ad/tracker beacons | N/A | ✅ `block_ads` (opt-in; 3,526 domains) | ✅ `block_ads` (request routing) |
| Cloudflare Turnstile/Interstitial | ❌ | ✅ Auto-solved (`solve_cloudflare`) | ✅ same solver |
| Header / User-Agent handling | `curl_cffi` profile headers (browserforge only if `impersonate` is off) | browserforge-generated User-Agent when headless; Chromium's own headers | context UA only with `new_context=True` |
| HTTP/2 & HTTP/3 | ✅ (HTTP/3 optional) | ✅ | ✅ |

> The browser cells describe which code path applies (`patchright` plus `STEALTH_ARGS` and the context options in `_base.py:578-601`; `connect_over_cdp` with no launch options in `_remote.py`); detection outcomes were not tested here (**Tier D**). Whether Patchright's driver-side patches carry over to a `connect_over_cdp` attachment was not established from Scrapling's source (**Tier D**; see [Patchright](./patchright.md)).

### TLS Fingerprint Impersonation (Fetcher)

This is the **most important stealth feature** for HTTP-only scraping. Most bot detection starts with TLS fingerprinting — Python's `requests` library has a distinctive JA3 hash that instantly flags it as non-browser traffic.

```python
# Standard Python requests → distinctive Python/OpenSSL JA3 → flagged as bot

# Scrapling Fetcher with curl_cffi → matches a real Chrome ClientHello
response = Fetcher.get('https://example.com')   # impersonates latest Chrome by default
```

The impersonation is entirely `curl_cffi`'s doing — Scrapling wires the `impersonate` argument (and a `_select_random_browser` helper for list-based randomization) into `curl_cffi.requests.Session`. See `scrapling/engines/static.py`.

### Cloudflare Auto-Solving (StealthyFetcher)

The `solve_cloudflare=True` parameter handles Turnstile and Interstitial challenges without external CAPTCHA-solving APIs. Implemented in `scrapling/engines/_browsers/_stealth.py` (sync solver `107-222`, async solver from `419`):

- `_detect_cloudflare(page_content)` (`_base.py:604-636`) classifies the challenge from the `cType: 'non-interactive'`, `'managed'` or `'interactive'` strings in the page source, or as `embedded` when a `challenges.cloudflare.com/turnstile/v…` script tag is present.
- `_cloudflare_solver(page)` first polls for a challenge for up to about 5 s, re-reading the page every fifth 100 ms poll, so a widget that appears late is still found (0.5; `_stealth.py:116-126`). For an **embedded** widget it clicks the `input[type="checkbox"]` inside the challenge iframe through a Playwright locator with a 100–200 ms press delay (`_stealth.py:135-146`). For an **interstitial** it waits up to 20 × 500 ms for the challenge iframe and up to 20 × 500 ms for it to become visible, then clicks at a randomized offset (x + 26–28, y + 25–27 px from the widget box, 100–200 ms press delay) and polls until the challenge page disappears (`_stealth.py:159-222`). A **non-interactive** page is waited out for up to 10 × 1 s (`_stealth.py:147-157`). It re-solves at most 3 times (`__CF_MAX_SOLVE_ATTEMPTS__`, `_stealth.py:21`, checked at `130-132`) and then returns the page as is. `solve_cloudflare=True` raises the timeout floor to 60,000 ms (`_validators.py:149-150`). 0.4.15 made detection locale-independent and capped the retries; 0.5 added delayed-widget detection and bounded the passive-challenge and hidden-frame loops (`docs/changelog.md:100`).

**Important caveat:** The solver drives the Patchright Chromium to the challenge widget and clicks it; it is **not** solving the CAPTCHA cryptographically, and whether Cloudflare accepts the resulting browser session was not tested here (**Tier D**). It does **not** cover Akamai, DataDome, Kasada, or Incapsula (the project's own README points users to a paid third-party token API for those). The MCP server's agent-driven browser actions (below) are a separate, model-driven route; nothing in the source solves any other CAPTCHA by itself.

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

The default backend is `SQLiteStorageSystem` (`check_same_thread=False`, an `RLock`, and `PRAGMA journal_mode=WAL`; `scrapling/core/storage.py:74-92`); `StorageSystemMixin` (`storage.py:14`) is the ABC you subclass for Redis or any other store. Saved data per element is the tag, attributes, text, DOM path, parent tag/attributes/text, sibling tags and child tags (`scrapling/core/utils/_utils.py:84-109`); candidates are scored as averaged `difflib.SequenceMatcher` ratios over those fields, with a default `percentage` threshold of 40 (`scrapling/parser.py:528`, `823-894`).

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

Numbers from the project's README (`README.md:497-525`, which points to `benchmarks.py` for methodology; **Tier B** — the maintainer's own benchmark, not reproduced here; unchanged since 2026-10-13):

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

- **orjson** for JSON serialization (README claims "10x faster than the standard library", `README.md:299`).
- Lazy-imported fetchers/sessions (`scrapling/fetchers/__init__.py:11-41` uses a `_LAZY_IMPORTS` map so importing the package doesn't pull Patchright/curl_cffi until used).
- 0.3 rewrite claims "Fetcher is now 4 times faster" and a ~60% faster `DynamicFetcher` (now removed) vs 0.2 (maintainer's release notes, `docs/changelog.md:1020-1021`; not independently benchmarked here).
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

Since 0.5 `response.follow()` no longer copies the previous request's method, params or body; a followed link starts as a plain GET (`docs/migrating-to-v0.5.md`, "Pass request data again when following a link").

### Spider Features (from `scrapling/spiders/`)

| Feature | Details | Source |
|---------|---------|--------|
| **Concurrent requests** | Async scheduler with configurable concurrency | `spiders/scheduler.py`, `spiders/engine.py` |
| **Multi-session support** | Mix `FetcherSession` (HTTP) and `AsyncStealthySession` (browser) per request | `spiders/session.py:7-9` |
| **Pause/Resume** | Checkpoint system — survives Ctrl+C, resumes crawl; since 0.5 the checkpoint is kept when a crawl ends with an exception | `spiders/checkpoint.py` |
| **Response caching** | Local cache for iterating on parse logic without re-fetching; since 0.5 blocked responses are not cached | `spiders/cache.py` |
| **Proxy rotation** | Thread-safe `ProxyRotator` across all fetchers | `engines/toolbelt/proxy_rotation.py` |
| **robots.txt compliance** | Honors `Crawl-delay` / `Request-rate` via `protego`; since 0.5 a failed robots.txt fetch blocks that domain | `spiders/robotstxt.py` |
| **Link extraction and templates** | `LinkExtractor`; `CrawlSpider` (0.5: `crawl_strategy="bfs"`/`"dfs"`), `SitemapSpider`, `ShopifySpider`, `XMLFeedSpider` / `CSVFeedSpider`, and `ContentSpider` (alias `SiteToMarkdownSpider`, 0.4.15), which crawls a site into one Markdown item per page | `spiders/links.py`, `spiders/templates/` (`crawler.py:61`, `site_to_markdown.py:30`, `96`) |
| **Streaming mode** | Async generator for real-time item processing | `spiders/engine.py` |
| **Stats tracking** | `CrawlStats` real-time metrics | `spiders/result.py` |
| **AutoThrottle** | Opt-in per-domain delay adjusted from measured response times (`autothrottle_enabled`, default off; 0.4.12) | `spiders/throttle.py`, `spiders/spider.py:89-93` |

### Scrapy Integration

0.4.x added a bridge for existing Scrapy projects (`scrapling/integrations/scrapy.py`): decorate a spider callback with `@scrapling_response` (`scrapy.py:59`) or call `convert_response` (`scrapy.py:24`) and you receive a Scrapling `Response` — with the full parsing/adaptive API — instead of the native Scrapy response, without changing how the spider crawls.

---

## CLI & MCP Server

### CLI Tools

```bash
# Interactive scraping shell (IPython-based)
scrapling shell

# Extract content without writing code
scrapling extract get 'https://example.com' output.md
scrapling extract fetch 'https://protected.com' output.md --solve-cloudflare   # StealthyFetcher since 0.5

# Launch MCP server for AI integration
scrapling mcp
scrapling mcp --http --auth-token <token> --port 8080   # binds 127.0.0.1 unless --host is given
```

The CLI (`scrapling/cli.py`) exposes `--impersonate` (single or comma-separated for random selection, `cli.py:103-105`) and an `--executable-path` (or `SCRAPLING_EXECUTABLE_PATH`, `cli.py:583`) to point the MCP browser tools and `extract fetch` at a custom Chromium-compatible browser. **`extract stealthy-fetch` was removed in 0.5**; `extract fetch` now runs `StealthyFetcher` (`cli.py:589-661`) and takes `--pierce-shadow`. `scrapling install` still runs `python -m playwright install chromium` and `install-deps chromium`, then refreshes the `tld` name list (`cli.py:110-143`) — the `playwright` package is now used for this alone, while the browser is launched through Patchright. Whether the two always agree on a Chromium revision depends on the installed `playwright` and `patchright` versions and was not tested here (**Tier D**). A `scrapling-mcp` entry point maps to `scrapling mcp` (`pyproject.toml:113`).

### MCP Server (AI Integration)

The MCP server moved from `scrapling/core/ai.py` to the `scrapling/core/ai/` package in 0.5 (`server.py`, `_browser_actions.py`, `_network_formatting.py`, `_snapshot_search.py`). `_build_server()` (`server.py:1048`) registers **17 tools** through `MCPServer` from the `mcp>=2.0.0` SDK (`server.py:16`, `1077-1188`). 0.4.15 had 13; 0.5 removed every bulk tool and the dynamic/stealthy split (all browser tools use the stealthy backend), renamed the browser tools with a `browser_` prefix, and added page actions, extraction, JavaScript, network history and saved state; 0.5.1 added `browser_observe` and split drag-and-drop into separate mouse-down/up actions (`docs/changelog.md:20-25`, `69-75`; `docs/migrating-to-v0.5.md`, "MCP server"):

| Tool | Description |
|------|------------|
| `browser_open` | Open a persistent stealth browser session; with `cdp_url` it opens an `AsyncRemoteSession` instead (`server.py:281-355`) |
| `browser_save_state` / `browser_load_state` | Save or restore cookies, local storage and IndexedDB as Playwright-compatible JSON |
| `open_request_session` | Open a persistent HTTP session (no browser) that keeps cookies and the impersonated fingerprint |
| `close_session` | Close a session |
| `list_sessions` | List active sessions with their effective settings |
| `make_request` | One-shot HTTP request with TLS impersonation, any method |
| `browser_fetch_once` | One-shot fetch through its own stealth browser (replaces `fetch`, `stealthy_fetch` and the bulk tools) |
| `browser_fetch` | Fetch through an opened browser session (was `session_fetch`) |
| `session_make_request` | Request through an opened HTTP session |
| `browser_extract` | HTML, Markdown, text or an ARIA snapshot of the current page without reloading |
| `browser_actions` | Ordered page actions: click, move/hover, `mouse_down`/`mouse_up`, wheel, key presses, dialogs, waits, form filling (`_browser_actions.py:22-143`) |
| `browser_evaluate` | Run JavaScript; `isolated_context` selects Patchright's isolated world or the page's own (`server.py:591-611`) |
| `browser_network_requests` / `browser_network_request` | Search and read the session's recorded traffic |
| `browser_screenshot` | Capture the current page (no navigation since 0.5) as an image content block |
| `browser_observe` | Sample 2–20 timestamped viewport frames over 100–5,000 ms through a screencast, for moving or timed challenges (`server.py:669-700`; 0.5.1) |

The mouse actions are Playwright primitives: a `move` is `page.mouse.move(x, y, steps=N)` with `steps` defaulting to 1, and `mouse_down`/`mouse_up` are separate actions (`_browser_actions.py:49-51`, `229-242`); there is no motion model. The server's instructions tell the agent, for sliders "with changing speed", not to release the mouse before checking the page (`server.py:1068`). Any CAPTCHA solving through these tools is the calling model's work, not Scrapling's; the README's "bypass any CAPTCHA" wording (`README.md:292`) is **Tier B** and unmeasured.

It runs over stdio by default or `streamable-http` with `--http`. Since 0.4.15 the HTTP transport refuses to start without a bearer token (`--auth-token` or `SCRAPLING_MCP_AUTH_TOKEN`) unless `--no-auth` is passed, binds `127.0.0.1` by default, and `--allowed-host` turns on DNS-rebinding protection (`cli.py:145-197`, `server.py:1038-1046`, `1190-1239`). Smart CSS pre-processing extracts the relevant HTML before sending to the model to reduce token usage, and hidden or prompt-injection content is stripped by `Convertor._sanitize_for_ai` (`scrapling/core/shell.py:648-664`; 0.5 also drops hidden slots and keeps visible near-opaque elements); the project also ships an "agent skill" bundle (`agent-skill/`) and a registry manifest (`server.json`, name `io.github.D4Vinci/Scrapling`, version `0.5.1`, PyPI package and OCI image `ghcr.io/d4vinci/scrapling`).

Not MCP-specific: `Response.markdown()` (`scrapling/engines/toolbelt/custom.py:92`, 0.4.15) applies the same sanitising before converting a response to Markdown, through the `rag` extra (`markdownify` plus the fetchers). 0.5 added session-level network recording (`record_requests=True`, up to 1,000 requests, bodies capped at 1 MiB each and 20 MiB in total; `scrapling/engines/_browsers/_network.py:9-20`, `78`), `save_state()`/`load_state()` (`_base.py:68-84`) and `pierce_shadow` for open Shadow DOM.

---

## Pros and Cons

### Advantages

| Pro | Details |
|-----|---------|
| **All-in-one framework** | Fetching + parsing + crawling + stealth + AI in one package |
| **Two fetch engines** | HTTP-only (curl_cffi) or Patchright Chromium, plus CDP attach through `RemoteSession` |
| **TLS impersonation** | curl_cffi matches real browser JA3/JA4 signatures at the HTTP tier |
| **Adaptive tracking** | Auto-relocates elements when sites change DOM; no equivalent code found in the other cloned trees |
| **Parser speed** | Near-tie with Parsel, ~785x faster than BeautifulSoup4 + lxml per the README (parser micro-benchmark, Tier B) |
| **Cloudflare auto-solve** | Built-in Turnstile/Interstitial handling, no external API |
| **Spider framework** | Concurrency, pause/resume, caching, proxy rotation, robots.txt, AutoThrottle, BFS/DFS order |
| **Scrapy interop** | `@scrapling_response` drops Scrapling parsing into existing Scrapy spiders |
| **MCP / AI integration** | 17-tool MCP server with page actions, network history and saved state; agent-skill bundle; registry manifest in `server.json` |
| **Maintenance activity** | 0.5 (2026-10-17) and 0.5.1 (2026-11-04), 52 contributors; README states 92% test coverage (`README.md:300`, Tier B) |
| **Permissive license** | BSD 3-Clause |

### Disadvantages

| Con | Details |
|-----|---------|
| **Python only** | No Node.js, .NET, or other language bindings |
| **Stealth is borrowed** | StealthyFetcher wraps Patchright — the anti-detection is Patchright's, not Scrapling's own innovation |
| **Chromium-only stealth** | The Firefox/Camoufox engine was dropped in 0.3.13; no Firefox stealth path in the package |
| **No unpatched browser option** | 0.5 removed the plain-Playwright tier; every local browser fetch is Patchright with `STEALTH_ARGS` (Patchright evaluates JavaScript in an isolated context by default, per the migration guide) |
| **Breaking 0.5 line** | Removed classes, the `cdp_url` move, MCP tool renames, and changed request-fingerprint, `follow()` and robots.txt behaviour require code and checkpoint changes (`docs/migrating-to-v0.5.md`) |
| **Optional dependency footprint** | Full install pulls Playwright (`>=1.62.0`, now used only by `scrapling install`) + Patchright (`>=1.62.1`) + curl_cffi + browserforge + fingerprint datapoints + mcp, etc.; both browser packages are minimum versions, not pins |
| **No human-behavior simulation** | No Bézier mouse movement or click/scroll timing models; the Cloudflare solver randomizes only its click offset and press delay (`_stealth.py:141`, `199-202`), and the MCP mouse moves are linear `steps` interpolation (see [Botasaurus](./botasaurus.md)) |
| **No self-run anti-bot benchmarks** | The repo publishes parser speed, not pass-rates against commercial WAFs |
| **Adaptive tracking has limits** | Major redesigns can still break saved signatures; needs an initial `auto_save` run |
| **Browser speed** | Browser-based stealth is inherently slower than the HTTP tier |
| **Beta status** | `Development Status :: 4 - Beta` in metadata |

---

## Anti-bot handling — what exists in the code, and what the project claims

> An earlier edition of this page carried a ✅/⚠️/❌ coverage grid with the legend
> "✅ = Reliably bypasses." Scrapling publishes no pass-rate benchmarks and none were
> run here, so that grid asserted more than anyone knows. It has been replaced with
> what is actually checkable: which mechanisms exist in the source, and what the
> maintainer claims. See [METHODOLOGY.md](METHODOLOGY.md#evidence-tiers).

| Capability | Present in source? | Tier | Notes |
|---|---|:--:|---|
| TLS impersonation (HTTP tier) | **Yes** — `curl_cffi>=0.16.3`, `--impersonate` with Chrome/Firefox/Safari profiles | **A** | Real JA3/JA4 impersonation. The most concretely verifiable stealth feature here. |
| Cloudflare Turnstile / Interstitial solver | **Yes** — `solve_cloudflare` in StealthyFetcher and the sessions | **A** | The code path exists and is first-party. Whether it succeeds on a given deployment is untested here. |
| CDP-level automation-tell removal | **Delegated** — `patchright>=1.62.1` | **A** | Not Scrapling's work. Its browser-tier evasion is exactly Patchright's, with Patchright's strengths and limits. |
| Fingerprint spoofing (canvas/WebGL/audio) | **No** first-party implementation | **A** | Exposes flags (canvas noise, WebGL toggle, timezone/locale, WebRTC→proxy) but implements no engine-level spoofing. Camoufox has not been used since 0.3.13. The README's feature list (`README.md:277`) describes the stealth fetcher as including fingerprint spoofing (**Tier B**); in source it is launch flags and context options, as above. |
| Agent-driven CAPTCHA interaction (MCP) | **Tools only** — screenshots, frame sampling, mouse/keyboard actions | **A** (tools) / **B** (claim) | The tools exist (`core/ai/`); the README's "bypass any CAPTCHA" claim depends on the calling model and is unmeasured. |
| DataDome / Kasada / Akamai / Incapsula | **No** first-party handling | **A** | Notably, the project **does not claim these** — its README routes them to a third-party paid token API. |

**Scope stated by the project.** Scrapling's README routes Akamai, DataDome, Kasada,
and Incapsula to an external paid token API rather than claiming coverage
(`README.md:131-137`). This matches the source: no first-party handling for those four
exists in the tree. Any evaluation of Scrapling against them is an evaluation of
Patchright plus the caller's IP reputation.

> **Honest note:** Scrapling's own README says it handles **Cloudflare Turnstile** out of the box (`README.md:135`) and points users to a paid third-party token API for **Akamai / DataDome / Kasada / Incapsula**. Treat any "bypasses DataDome/Kasada" claim as "only insofar as a well-configured Patchright Chromium + clean proxy does" — Scrapling adds no dedicated solver for those. The confident ✅ marks for DataDome/Kasada via Camoufox in an early edition no longer apply (Camoufox is gone).

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
| CAPTCHA solving | ⚠️ Cloudflare Turnstile only (in-library) | ❌ | ❌ | ✅ Multiple |
| Human behavior simulation | ❌ | ✅ Mouse | ❌ | ✅ |
| Fingerprint rotation | ⚠️ User-Agent only for browsers (browserforge); `curl_cffi` profiles for HTTP | see [Camoufox](./camoufox.md) | ⚠️ | ⚠️ |
| CLI tools | ✅ | ❌ | ❌ | ❌ |
| MCP/AI integration | ✅ (17 tools) | ❌ | ❌ | see [SeleniumBase](./seleniumbase.md) |
| Multi-language | Python only | Python | Python, Node, .NET | Python |

### vs. Scraping Frameworks

| Feature | Scrapling | Scrapy | BeautifulSoup4 | Playwright (raw) |
|---------|:---------:|:------:|:--------------:|:----------------:|
| Parse speed (relative) | 1.0x | ~1.035x | ~785x slower | N/A |
| Anti-detection built-in | ✅ HTTP + browser engines | ❌ | ❌ | ❌ |
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

# With fetchers (HTTP TLS impersonation + Patchright; also pulls playwright for `scrapling install`)
pip install "scrapling[fetchers]"

# With AI/MCP extras
pip install "scrapling[ai]"

# With Markdown/RAG extras (Response.markdown(), ContentSpider)
pip install "scrapling[rag]"

# Everything (fetchers + shell + AI)
pip install "scrapling[all]"

# Install Playwright's Chromium + its system dependencies
scrapling install
```

Extras (from `pyproject.toml:72-100`): `fetchers` (click, `curl_cffi>=0.16.3`, `playwright>=1.62.0`, `patchright>=1.62.1`, browserforge, apify-fingerprint-datapoints, msgspec, anyio, protego), `rag` (markdownify, + fetchers), `ai` (`mcp>=2.0.0`, markdownify, + fetchers), `shell` (IPython, markdownify, + fetchers), `all` (ai + shell). Core deps are lxml ≥6.1.1, cssselect, orjson, tld, w3lib, typing_extensions.

### Basic Fetching

```python
from scrapling.fetchers import Fetcher, StealthyFetcher, RemoteSession

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

# Attach to an already-running Chromium over CDP (0.5.1; no launch flags apply)
with RemoteSession(cdp_url='http://localhost:9222') as session:
    resp = session.fetch('https://example.com')
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
- **AI-integrated scraping** — the 17-tool MCP server for Claude/Cursor-driven workflows, including page actions and network history.
- **Existing Scrapy shops** — drop Scrapling parsing into current spiders via `@scrapling_response`.
- **Python teams** already fluent in CSS/XPath selectors.

### Not Recommended For

- **Maximum browser stealth / fine control** — use [Patchright](./patchright.md) directly, or [Camoufox](./camoufox.md) for Firefox-level C++ fingerprinting (Scrapling no longer bundles Camoufox).
- **Human-behavior simulation** — no Bézier mouse / click timing / scroll models (use [Botasaurus](./botasaurus.md)).
- **Non-Python projects** — Python only.
- **DataDome / Akamai / Kasada / Incapsula** — no dedicated solver; you get whatever a good Patchright + proxy setup achieves.
- **Multi-CAPTCHA solving** — only Cloudflare Turnstile in the library (use [SeleniumBase](./seleniumbase.md) for reCAPTCHA/hCaptcha).
- **Pinned 0.4.x code** — 0.5 removed `DynamicFetcher` and moved `cdp_url`; budget a migration.
- **When you only need one specific stealth tool** — Scrapling's framework overhead is unnecessary.

---

## Key Files & Dependencies

| Component | Location / Package | Purpose |
|-----------|--------------------|---------|
| HTTP engine (TLS impersonation) | `scrapling/engines/static.py` (curl_cffi) | JA3/JA4 impersonation |
| Stealth browser engine | `scrapling/engines/_browsers/_stealth.py` (patchright) | session lifecycle + Cloudflare solver |
| Remote browser sessions | `scrapling/engines/_browsers/_remote.py` | `RemoteSession` / `AsyncRemoteSession` over CDP (0.5.1) |
| Browser launch flags | `scrapling/engines/_browsers/_base.py` | canvas noise, WebRTC policy, WebGL, DoH, locale flags; `_detect_cloudflare` |
| Network recording | `scrapling/engines/_browsers/_network.py` (`NetworkRecorder`) | `record_requests` history (0.5) |
| Flag sets | `scrapling/engines/constants.py` | `DEFAULT_ARGS` (11), `STEALTH_ARGS` (54), `HARMFUL_ARGS` (5), `EXTRA_RESOURCES` (10) |
| Tab pool | `scrapling/engines/_browsers/_page.py` | ready/busy/error pages reused across requests (0.4.15) |
| Parser / selectors | `scrapling/parser.py` (lxml + cssselect) | CSS/XPath/regex/text + adaptive |
| Adaptive storage | `scrapling/core/storage.py` (`SQLiteStorageSystem`, `StorageSystemMixin`) | signature persistence |
| Spider framework | `scrapling/spiders/` | concurrency, checkpoint, cache, proxy, robots |
| Ad/tracker list | `scrapling/engines/toolbelt/ad_domains.py` | 3,526 domains |
| Proxy rotation | `scrapling/engines/toolbelt/proxy_rotation.py` (`ProxyRotator`) | thread-safe rotation |
| Scrapy interop | `scrapling/integrations/scrapy.py` | `@scrapling_response` decorator |
| MCP / AI server | `scrapling/core/ai/` (`server.py`, `MCPServer`, 17 tools) | AI assistant integration |
| CLI | `scrapling/cli.py` | `shell` / `extract` / `mcp` / `install` |
| `browserforge` | dependency | statistically accurate browser headers |
| `orjson` | dependency | fast JSON serialization |

---

## Conclusion

Scrapling is a **framework, not a stealth engine**. Its browser anti-detection is inherited from **Patchright** (a patched Playwright driver for Chromium); what Scrapling adds is the *framework around it*: a unified classmethod API, two fetch engines (curl_cffi HTTP and Patchright Chromium, with CDP attach through `RemoteSession`), adaptive element tracking, an async spider framework with checkpoints and proxy rotation, Scrapy interop, CLI tools, and a 17-tool MCP server.

**Applicability:** Python pipelines needing fetching, parsing, and crawling in one package. Verified first-party capabilities: `curl_cffi` TLS impersonation on the HTTP tier, a `solve_cloudflare` code path, adaptive element tracking, and a spider framework. Browser-tier evasion is Patchright's, reached via `patchright>=1.62.1`; since 0.5 there is no unpatched-Playwright browser path in the package.

**Constraints:** no first-party fingerprint spoofing, and no first-party handling for Akamai, DataDome, Kasada, or Incapsula — the project routes those to an external paid API. Using Patchright directly provides the same browser-tier evasion without the framework layer.

**Scope summary:** Scrapling's browser-tier stealth is Patchright's implementation, reached through a dependency (`patchright>=1.62.1`). Using Patchright directly provides the same evasion without the framework. Scrapling adds the HTTP tier (`curl_cffi` TLS impersonation), the parser, adaptive element tracking, the spider framework and the MCP tooling. Project state at 2026-11-20: 0.5.1 shipped 2026-11-04, 52 contributors, 24 open issues, 92% test coverage stated in the README (Tier B), BSD-3-Clause. Its published benchmarks measure parser throughput, not WAF outcomes.

**Unique value:** The adaptive element tracking system remains the standout — automatic selector recovery when a site's DOM changes is something none of the other tools analyzed in this repository provide.

---

*Analysis conducted for educational purposes against Scrapling v0.5.1 source (`2998c9e`, read 2026-11-20 in an isolated container; the `scrapling/` tree is identical to the v0.5.1 tag). Use responsibly.*
