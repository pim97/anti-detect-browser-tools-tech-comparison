# Botasaurus - Technical Analysis

> **Repository:** [omkarcloud/botasaurus](https://github.com/omkarcloud/botasaurus)
> **Category:** Browser Automation / Anti-Detection Framework
> **Language:** Python (core + driver); Node/TypeScript (Botasaurus JS Driver, on rebrowser-playwright-core)
> **Type:** CDP-native stealth driver + all-in-one scraping framework with human simulation
> **Approach:** Direct Chrome DevTools Protocol control + Bézier-curve human input + Cloudflare challenge automation
> **What is verified:** **zero** Selenium imports in `botasaurus_driver`; 58 generated CDP binding files under `botasaurus_driver/cdp/`; Bézier cursor paths in `botasaurus_humancursor/.../human_curve_generator.py` (**Tier A**). Any "Selenium wrapper" description of Botasaurus is historical.
> **Anti-bot service claims:** the README claims **Cloudflare WAF, Cloudflare Turnstile, DataDome** with ✅ against linked demo targets, and markets "undefeatable" scrapers (**Tier B** — vendor-selected demo targets, not a benchmark)
> **Maintenance:** Core `botasaurus` **4.0.97** (2026-01-06, unchanged); `botasaurus-driver` **4.0.101** on PyPI (2026-08-10) — note the GitHub `setup.py` still reads 4.0.92, so **PyPI is ahead of the repo**. 5.7k stars, 9 contributors, last push 2026-07-26. MIT.
> **Verified:** 2026-08-14 against `omkarcloud/botasaurus` @ `6c9260d` and `botasaurus-driver` @ `db1d291`.

---

## Overview

Botasaurus is a Python-based web scraping framework that markets itself as "The All in One Framework to Build Undefeatable Scrapers." It bundles a stealth browser driver, a human-input simulation layer, result caching, parallelization, a scraper server/UI, and (since 2024) a desktop-app builder.

**Important correction vs. earlier analysis:** Botasaurus is *no longer a Selenium wrapper*. The current core driver (`botasaurus_driver`) talks to Chrome **directly over the DevTools Protocol WebSocket** (`websocket-client`, a `Connection` class, and generated CDP bindings under `botasaurus_driver/cdp/`). Neither the core `botasaurus` package nor `botasaurus_driver` imports Selenium — the word "selenium" survives only as a PyPI keyword and a single doc comment (`core/browser.py:280`, "convenience function known from selenium"). Treat any "Selenium wrapper" description of Botasaurus as historical. It is closer in architecture to `nodriver`/`zendriver` (raw-CDP drivers) than to Selenium.

## Assessment

> **Editorial judgment, not measurement.** Star ratings were removed from this report
> in the 2026-08-14 revision — no rubric defined them and no evidence backed any cell.
> What follows is reasoning from the verified architecture; disagree with the reasoning.

| | |
|---|---|
| **Strongest at** | Human input simulation. The Bézier trajectory generator (verified in `human_curve_generator.py`) with Gaussian distortion and easing is among the more thorough implementations in this space, and CDP-dispatched events mean `event.isTrusted` is genuinely true. |
| **Also good** | Ergonomics — the decorator-based API is the shortest path from zero to a working scraper of anything here. Documentation is thorough. |
| **Weakest at** | Fingerprint surface. It does nothing about TLS/JA3, canvas, WebGL, or audio fingerprinting. Its evasion is behavioural and protocol-level only. |
| **Watch out for** | The "undefeatable scrapers" marketing, and a maintenance split — the core monorepo is active but `botasaurus-driver`'s public repo lags its own PyPI releases by months. |
| **Reasonable for** | Mid-tier targets where behaviour matters more than fingerprint depth, and for getting something working quickly. |
| **Reach for something else if** | Your target fingerprints the rendering stack — Camoufox, Clearcote, or CloakBrowser address a layer Botasaurus does not touch. |

---

## Version & Maintenance Status (verified 2026-08-14)

Botasaurus does **not** publish GitHub Releases — there are no tags/releases on the repo. Versioning happens by an auto-increment script (`increment_version.py`) that bumps the patch number in `setup.py` and auto-publishes to PyPI/npm (commit messages like `chore: autopublish 2026-06-29...`). So "current version" means "latest published package," not a release note.

| Package | Registry | Version | Published | License |
|---------|----------|---------|-----------|---------|
| `botasaurus` (core) | PyPI | **4.0.97** | 2026-01-06 | MIT |
| `botasaurus-driver` (stealth CDP driver) | PyPI | **4.0.101** | 2026-08-10 | MIT |
| `botasaurus-humancursor` (Bézier input) | PyPI | 4.0.83 | 2025-04-09 | MIT |
| `botasaurus-server` (scraper UI/server) | PyPI | 4.0.61 | 2025-07-29 | MIT |
| `botasaurus-api` (REST client) | PyPI | 4.0.10 | 2025-08-05 | MIT |
| `botasaurus-requests` (hrequests fork, TLS-fingerprint HTTP) | PyPI | 4.0.38 | 2024-09-30 | MIT |
| `botasaurus` (Botasaurus **JS Driver**, Node/TS) | npm | **4.0.134** | 2026-06-29 | Apache-2.0 |

**Activity:** The monorepo (`omkarcloud/botasaurus`) is actively maintained — last push **2026-07-26**. The separate stealth-driver repo (`omkarcloud/botasaurus-driver`) is maintained more sporadically: its last public commit is 2025-06-11 (PyPI is well ahead at 4.0.101, Aug 2026), with commits like "Fixing Chrome v137, Extension Break" showing they patch it to keep pace with new Chrome versions. The `setup.py` in the monorepo still reads `version='4.0.97'`.

**Status: actively maintained** (not abandoned). ~5.7k GitHub stars, 9 contributors, 57 open issues.

---

## How It Works - Technical Deep Dive

### It's NOT Just JavaScript Injection

Botasaurus uses a **multi-layered approach** combining several techniques at different levels. Core detection evasion lives in the separate `botasaurus_driver` package (a native-CDP Chrome driver); the human-input layer lives in `botasaurus_humancursor`.

### 1. Chrome DevTools Protocol (CDP) Mouse Events

Instead of a standard synthetic `.click()`, it dispatches raw mouse events via CDP. From `botasaurus_humancursor/src/botasaurus_humancursor/web_cursor.py` (lines ~122–144):

```python
self.driver.run_cdp_command(
    cdp.input_.dispatch_mouse_event(
        "mousePressed",
        x=x, y=y,
        button=cdp.input_.MouseButton("left"),
        click_count=1,
    )
)
# ... then "mouseReleased" with the same button/click_count
```

**Why it works:** CDP-dispatched `Input.dispatchMouseEvent` events are generated inside the browser's real input pipeline, so `event.isTrusted === true` and the events look like genuine user input rather than JS-synthesized `MouseEvent`s.

### 2. Bézier Curve Mouse Movement (Best-in-Class)

The `HumanizeMouseTrajectory` class in `botasaurus_humancursor/src/botasaurus_humancursor/human_curve_generator.py` generates mathematically realistic mouse paths (verified against source):

```python
class HumanizeMouseTrajectory:
    def generate_curve(self, **kwargs):
        offset_boundary_x = kwargs.get("offset_boundary_x", 80)
        offset_boundary_y = kwargs.get("offset_boundary_y", 80)
        knots_count       = kwargs.get("knots_count", 2)
        distortion_mean   = kwargs.get("distortion_mean", 1)
        distortion_st_dev = kwargs.get("distortion_st_dev", 1)
        distortion_frequency = kwargs.get("distortion_frequency", 0.5)  # ~50% of points get noise
        tween         = kwargs.get("tweening", pytweening.easeOutQuad)
        target_points = kwargs.get("target_points", 100)

        internalKnots = self.generate_internal_knots(...)   # random control knots
        points = self.generate_points(internalKnots)        # Bézier via BezierCalculator
        points = self.distort_points(points, distortion_mean,
                                     distortion_st_dev, distortion_frequency)  # Gaussian noise
        points = self.tween_points(points, tween, target_points)              # easing
        return points
```

**Technical details (confirmed in source):**
- **Bézier curve** built from a start point, random internal knots, and the target point (`BezierCalculator.calculate_points_in_curve`)
- **Gaussian noise** (`np.random.normal(mean=1, std_dev=1)`) applied to a fraction of intermediate points controlled by `distortion_frequency` (default 0.5)
- **Easing** via `pytweening` (default `easeOutQuad`) for natural acceleration/deceleration
- **`target_points=100`** interpolation points per movement (via `tween_points`)
- **`knots_count=2`** default internal knots (previously randomized; the actual per-move randomization is applied by `generate_random_curve_parameters` in `calculate_and_randomize.py`, not hard-coded here)
- A `steady=True` mode tightens the curve (offset boundaries → 10, distortion → 1.2) for precise targets like checkboxes

**Why it works:** Humans don't move mice in straight lines — they curve, overshoot, and have micro-tremors, then accelerate/decelerate. Detection systems flag perfectly linear/instant movements. This is still the most sophisticated human-mouse implementation among the tools analyzed here.

### 3. JavaScript Property Patching (CDP fingerprint fix)

CDP-dispatched mouse events leak a wrong `screenX`/`screenY`. Botasaurus patches `MouseEvent.prototype` before detection scripts run — from `botasaurus_humancursor/.../web_adjuster.py`, method `fix_mouse_move_cursor` (verified):

```javascript
// Injected via driver.run_js(...) once per cursor, guarded by a flag on HTMLMarqueeElement.prototype
Object.defineProperty(MouseEvent.prototype, 'screenX', {
    get: function () { return this.clientX + window.screenX; }
});
Object.defineProperty(MouseEvent.prototype, 'screenY', {
    get: function () { return this.clientY + window.screenY; }
});
```

The idempotency guard is stored on `HTMLMarqueeElement.prototype.<name>` so the override is installed only once. **Why it works:** CDP events report `screenX/Y` equal to `clientX/Y` (missing the window offset), which is a detectable synthetic-origin tell; this getter restores the value a real browser would report.

### 4. Referrer Spoofing

Confirmed in `botasaurus_driver/driver.py` — `google_get` navigates via `get_via(link, referer="https://www.google.com/")`, setting a real `referrer` on the CDP `Page.navigate`:

```python
driver.google_get("https://target-site.com")            # arrive "from" a Google result
driver.get_via("https://target-site.com", referer="...") # explicit referrer control
driver.get_via_this_page("https://target-site.com")      # use current page as referrer
```

`google_get` also has an optional `accept_google_cookies=True` path that clicks Google's consent dialog first. **Why it works:** Direct, no-referrer visits are suspicious; real users usually arrive via search/links.

### 5. Timing Randomization

From `web_cursor.py` (`random_natural_sleep`, verified):

```python
def random_natural_sleep(self):
    sleep(random.randint(170, 280) / 1000)   # 170–280 ms, human reaction-time range
```

Exposed on the driver as `short_random_sleep()` / `long_random_sleep()`. **Why it works:** Bots act instantly or with fixed delays; humans vary.

### 6. Built-in Cloudflare Turnstile / Challenge Automation

A substantial, verifiable feature the earlier page under-credited: `botasaurus_driver/solve_cloudflare_captcha.py` (plus `driver.detect_and_bypass_cloudflare()` and the `bypass_cloudflare=True` argument on `get`/`google_get`/`get_via`) automates Cloudflare's Turnstile/interstitial flow — it finds the Turnstile parent, pierces the (closed) shadow root, waits for `document.readyState`, and clicks the checkbox with a jump-then-human-restore cursor sequence (`click_restoring_human_behaviour`). It reads the Ray ID (`get_rayid`) and raises `CloudflareDetectionException` on failure.

```python
driver.get("https://nopecha.com/demo/cloudflare", bypass_cloudflare=True)
# or
driver.google_get("https://target", bypass_cloudflare=True)
```

**Why it works:** It waits out the JS challenge and clicks the Turnstile widget as a human would, using trusted CDP input. It is *not* a token/captcha-solving service — it automates the interactive challenge, so it works best in headed mode with decent IP reputation.

### 7. Browser Profile Persistence

```python
@browser(
    profile="my_profile",   # full Chrome user-data-dir (cookies, history, localStorage)
    tiny_profile=True,       # lightweight cookie-only profile (profiles/<name>/profile.json)
    user_agent=UserAgent.HASHED,
)
```

- **Full profiles**: real Chrome `--user-data-dir` with cookies/history/localStorage
- **Tiny profiles**: `botasaurus_driver/tiny_profile.py` just serializes the cookie jar to a small JSON file per profile — cheap session persistence without a full profile dir

**Why it works:** Sites weight history and returning-session signals; a profile with state looks more legitimate than a fresh instance.

### 8. Anti-Detect Launch Configuration

The Chrome launch args are relatively conservative (from `botasaurus_driver/core/config.py`, `default_arguments`):

```
--start-maximized  --remote-allow-origins=*  --no-first-run  --no-service-autorun
--no-default-browser-check  --homepage=about:blank  --no-pings  --password-store=basic
--disable-infobars  --disable-breakpad  --disable-dev-shm-usage
--disable-session-crashed-bubble  --disable-features=IsolateOrigins,site-per-process
--disable-search-engine-choice-screen
```

Notably it does **not** rely on `--disable-blink-features=AutomationControlled`. The `navigator.webdriver`/CDP tells are handled at the driver/connection level (native-CDP connection, no chromedriver, no `cdc_` variables), not via a big list of flags. The framework's own docs even advise removing `--no-default-browser-check` for the strictest targets because it can itself be a tell.

---

## Architecture

```
botasaurus/                              # monorepo (omkarcloud/botasaurus)
├── botasaurus/                          # Core framework (@browser/@request/@task decorators)
│   ├── browser_decorator.py            # @browser decorator
│   ├── request_decorator.py            # @request decorator
│   ├── task_decorator.py               # @task decorator
│   ├── cache.py / cache_storage.py     # result caching
│   └── ...                             # profiles, sitemap, soupify, parallel utils
├── botasaurus_humancursor/             # Human simulation (KEY)
│   └── src/botasaurus_humancursor/
│       ├── human_curve_generator.py    # Bézier curves
│       ├── web_cursor.py               # CDP click/drag + timing
│       ├── web_adjuster.py             # screenX/Y JS patch, do_move/move_to
│       └── calculate_and_randomize.py  # per-move curve parameters
├── botasaurus_api/                      # REST API client
├── botasaurus_server/                   # scraper server + web UI
├── bota / botasaurus-controls / close_chrome / *-cache-storage   # helper pkgs
└── docs/                                # documentation

botasaurus-driver/  (separate repo: omkarcloud/botasaurus-driver)
├── botasaurus_driver/
│   ├── driver.py                        # Driver/Tab/Element API (2,300+ lines)
│   ├── solve_cloudflare_captcha.py      # Cloudflare Turnstile/challenge automation
│   ├── opponent.py                      # Opponent.CLOUDFLARE / Opponent.PERIMETER_X
│   ├── tiny_profile.py                  # cookie-only profiles
│   ├── core/ (browser.py, config.py, connection.py, tab.py, element.py)  # native CDP core
│   └── cdp/                             # generated CDP protocol bindings
│       # connection.py uses websocket-client — NO Selenium

Botasaurus JS Driver  (npm "botasaurus" 4.0.x, Apache-2.0, Node/TypeScript, on rebrowser-playwright-core)
└── depends on rebrowser-playwright-core (stealth Playwright fork)
```

---

## Anti-Detection Effectiveness

> **Star ratings below are the author's editorial judgment, not measurement.**
> No rubric defines the scale and no benchmark backs any cell. They are retained
> only as a rough relative ordering — see [METHODOLOGY.md](METHODOLOGY.md#rating-policy).

| Technique | What It Evades | Effectiveness |
|-----------|---------------|---------------|
| CDP Mouse Events (`Input.dispatchMouseEvent`) | `event.isTrusted` checks, coordinate analysis | ⭐⭐⭐⭐⭐ |
| Bézier Curves + easing + noise | Mouse trajectory analysis | ⭐⭐⭐⭐⭐ |
| Cloudflare Turnstile/challenge automation | Interactive CF challenge | ⭐⭐⭐⭐ |
| screenX/Y prototype patch | CDP fingerprint leakage | ⭐⭐⭐ |
| Native-CDP connection (no chromedriver/`cdc_`) | `navigator.webdriver`, driver artifacts | ⭐⭐⭐ |
| Referrer spoofing (`google_get`) | Direct-visit detection | ⭐⭐ |
| Random timing (170–280 ms) | Timing pattern analysis | ⭐⭐⭐ |
| Profile persistence (full + tiny) | Session/history analysis | ⭐⭐⭐ |

---

## What the project claims, and what the test suite actually targets

> **Tier A** for "these test functions exist and target these endpoints" — verified in
> `bot_detection_tests.py`. **Tier B** for the claim that they pass. The tests hit
> vendor *demo* pages, not production deployments, and outcomes depend heavily on IP
> reputation and headed mode. Nothing was executed here.

| Status | Service | Evidence |
|--------|---------|----------|
| ✅ Claimed bypass | Cloudflare WAF | `test_cloudflare_waf` → nopecha.com/demo/cloudflare, `bypass_cloudflare=True` |
| ✅ Claimed bypass | Cloudflare Turnstile | `test_cloudflare_turnstile` → turnstile.zeroclover.io |
| ✅ Claimed bypass | BrowserScan Bot Detection | `test_browserscan_bot_detection` |
| ✅ Claimed bypass | Fingerprint.com Bot Detection | `test_fingerprint_bot_detection` |
| ✅ Claimed bypass | DataDome Bot Detection | `test_datadome_bot_detection` → fingerprint-scan.com |
| ⚠️ Partial | PerimeterX | recognized in `opponent.py` (`Opponent.PERIMETER_X`), detection only — no dedicated solver |
| ❌ Not handled | Akamai / Kasada (enterprise) | no support |
| ❌ Not handled | Canvas / WebGL / audio fingerprinting | no spoofing in driver |
| ❌ Not handled | TLS/JA3 fingerprinting (browser path) | no TLS control in the browser driver |

**Reality check:** These bypasses target vendor demo pages and work under specific conditions (residential IP, headed mode, current Chrome). The README itself warns that headless mode "will surely be identified by services like Cloudflare, Datadome, and Imperva," and that datacenter proxies get flagged. Do not read the ✅ column as "reliably beats production deployments of these vendors."

---

## What It Does NOT Handle

1. **Advanced Fingerprinting** — canvas, WebGL, audio-context, font enumeration, hardware-concurrency, and screen/GPU coherence are not spoofed by the driver. Botasaurus relies on running a *real* Chrome, so the fingerprint is real (and consistent), but it is not *controllable* or *rotatable*.
2. **TLS Fingerprinting (browser)** — the browser's TLS/JA3/JA4 handshake is Chrome's real one; there's no ClientHello spoofing in the browser path. (The separate `botasaurus-requests` package — an hrequests fork — does offer TLS-fingerprint-matching for *HTTP* requests, but that's the non-browser path.)
3. **Behavioral Analysis at Scale** — cross-request/session pattern analysis at CDN scale isn't addressed by mouse realism alone.
4. **External Dependency** — core evasion + Cloudflare automation live in `botasaurus_driver`, a separately versioned package/repo that lags the monorepo's cadence.
5. **IP Reputation** — datacenter IPs are flagged regardless; residential/mobile proxies are required for serious targets.
6. **Enterprise anti-bot** — Akamai, Kasada, and PerimeterX enterprise deployments are not defeated (PerimeterX is only *detected*, not solved).

---

## Usage Example

```python
from botasaurus.browser import browser, Driver

@browser(
    headless=False,              # headed strongly recommended for protected sites
    block_images_and_css=True,   # reduce load / surface
    proxy="http://user:pass@host:port",
    profile="my_profile",        # or tiny_profile=True for cookie-only persistence
    user_agent=UserAgent.HASHED, # consistent UA per profile
)
def scrape_site(driver: Driver, data):
    # Human-like navigation with a Google referrer; auto-solve Cloudflare if present
    driver.google_get("https://example.com", bypass_cloudflare=True)

    driver.enable_human_mode()          # Bézier-curve mouse mode
    driver.click(".login-button")       # CDP click along a human curve
    driver.type(".username", "user@example.com")
    driver.short_random_sleep()         # 170–280 ms

    return driver.select(".results")    # or driver.bs4 / soupify for BeautifulSoup

results = scrape_site(data=["url1", "url2", "url3"])   # parallelized
```

Install:

```bash
python -m pip install botasaurus   # pulls botasaurus-driver, humancursor, api, etc.
```

---

## Pros and Cons

### Advantages

| Advantage | Details |
|-----------|---------|
| **Human Mouse Movement** | ⭐⭐⭐⭐⭐ Best-in-class Bézier curve implementation |
| **Native CDP driver** | No chromedriver/Selenium; fewer classic automation tells |
| **Built-in Cloudflare automation** | `bypass_cloudflare=True` + Turnstile/challenge solver in-driver |
| **Ease of Use** | Decorator-based `@browser`/`@request`/`@task` API is very intuitive |
| **All-in-One** | Scraping + caching + parallelization + REST API + server UI + desktop-app builder |
| **Parallelization** | Easy concurrent browser management |
| **Caching** | Built-in result caching (with pluggable SQLite/Postgres storage) |
| **Profile Management** | Full profiles + lightweight cookie-only "tiny" profiles |
| **Active Development** | Core monorepo last pushed 2026-07-26 |
| **MIT License** | Open source (core + Python packages; the npm JS Driver is Apache-2.0) |

### Limitations

| Limitation | Details |
|------------|---------|
| **"Undefeatable" Claim** | Marketing hyperbole — not truly undefeatable |
| **Headless Mode** | Per the docs, easily detected by Cloudflare/DataDome/Imperva; use headed for protected sites |
| **Advanced Fingerprinting** | No canvas/WebGL/audio/font spoofing; fingerprint is real but not controllable/rotatable |
| **Browser TLS Fingerprinting** | Browser path uses Chrome's real TLS; no ClientHello spoofing |
| **External / lagging Dependency** | Core evasion is in the separately versioned `botasaurus_driver` repo (last public commit 2025-06) |
| **Python Only (browser core)** | Browser scraping is Python; the JS/Node side (npm `botasaurus` JS Driver) is a different product built on `rebrowser-playwright-core`, not the same driver |
| **Resource Intensive** | Real Chrome per worker → significant memory (no published footprint benchmark; **unknown/unbenchmarked**) |
| **No formal releases** | No GitHub Releases/changelog; versions are auto-published patch bumps |

---

## Comparison with Alternatives

| Feature | Botasaurus | Patchright | SeleniumBase | BotBrowser |
|---------|:----------:|:----------:|:------------:|:----------:|
| **Human Mouse** | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐ | ⭐⭐ |
| **CDP Evasion** | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Fingerprint Control** | ⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **CF Challenge Automation** | ⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ |
| **Ease of Use** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ |
| **Language** | Python | Multi | Python | Multi |
| **Cost** | Free | Free | Free | $$ |

---

## When to Use Botasaurus

### Best For:
- Web scraping *applications* (not just automation) — caching, parallelization, server/desktop UI baked in
- Projects needing **human-like mouse movements**
- Sites behind **Cloudflare Turnstile/interstitial** where the built-in solver + a good residential IP is enough
- Building scraper UIs/desktop apps for non-technical users
- Mid-tier protected sites, Python-only environments

### Not Ideal For:
- Enterprise anti-bot (Akamai, Kasada, PerimeterX enterprise)
- Sites relying on advanced device fingerprinting (canvas/WebGL/audio) or browser TLS fingerprinting
- Headless-required protected scraping (headless is a known tell here)
- Fingerprint rotation / one-identity-per-request use cases (Botasaurus runs a real, fixed Chrome fingerprint)

---

## Bottom Line

Botasaurus is a **legitimate, well-engineered** scraping framework. Its human-mouse simulation (Bézier curves + Gaussian noise + easing over trusted CDP input) remains best-in-class among the tools reviewed, and the in-driver Cloudflare Turnstile/challenge automation is a real, useful capability rather than a marketing bullet. The 2024–2026 architecture is a **native-CDP driver, not a Selenium wrapper** — an important correction to older descriptions.

"Undefeatable," however, is hyperbole. It does not control canvas/WebGL/audio/TLS fingerprints, warns against headless for protected sites itself, and only *detects* (doesn't defeat) PerimeterX. For serious anti-bot systems you still need:
- Residential/mobile proxies
- Real profiles with history
- A tool that actually spoofs/rotates fingerprints (Botasaurus doesn't)
- Rate limiting and behavioral variation

**Recommendation:** Excellent choice for mid-tier scraping where human-like behavior and Cloudflare-challenge automation matter, and where an all-in-one framework (caching, parallelism, UI/desktop) saves time. Pair with quality residential proxies; for hard fingerprinting targets, combine with a fingerprint-spoofing browser.

**Effectiveness:** Moderate-High | **Complexity:** Low | **Best Use:** Scraper apps with human-like behavior + Cloudflare challenges

---

## Key Files

- `botasaurus_humancursor/src/botasaurus_humancursor/human_curve_generator.py` — Bézier trajectory generation
- `botasaurus_humancursor/src/botasaurus_humancursor/web_cursor.py` — CDP click/drag + 170–280 ms timing
- `botasaurus_humancursor/src/botasaurus_humancursor/web_adjuster.py` — screenX/Y prototype patch, `move_to`
- `botasaurus_driver/driver.py` — Driver/Tab/Element API, `google_get`, `get_via`, `detect_and_bypass_cloudflare`
- `botasaurus_driver/solve_cloudflare_captcha.py` — Cloudflare Turnstile/challenge automation
- `botasaurus_driver/core/config.py` — Chrome launch arguments
- `botasaurus_driver/core/connection.py` — native CDP WebSocket connection (no Selenium)
- `botasaurus_driver/opponent.py` — recognized detectors (Cloudflare, PerimeterX)
- `botasaurus_driver/tiny_profile.py` — cookie-only profiles
- `bot_detection_tests.py` — the demo bypass test suite

---

## Resources

- [GitHub Repository](https://github.com/omkarcloud/botasaurus)
- [botasaurus-driver repo](https://github.com/omkarcloud/botasaurus-driver)
- [Documentation](https://www.omkar.cloud/botasaurus/)
- [Bot Detection Tests](https://github.com/omkarcloud/botasaurus/blob/master/bot_detection_tests.py)
- [PyPI: botasaurus](https://pypi.org/project/botasaurus/) · [botasaurus-driver](https://pypi.org/project/botasaurus-driver/)
