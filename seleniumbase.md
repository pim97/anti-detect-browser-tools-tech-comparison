# SeleniumBase - Technical Analysis

> **Repository:** [seleniumbase/SeleniumBase](https://github.com/seleniumbase/SeleniumBase)
> **Category:** Browser Automation & Testing Framework
> **Language:** Python (100%)
> **Type:** Selenium wrapper with UC Mode + CDP Mode (undetected Chromium automation)
> **Approach:** ChromeDriver binary patching + disconnect/reconnect + CDP-native driver (based on NoDriver) + optional PyAutoGUI CAPTCHA solving
> **What is verified:** `seleniumbase/undetected/` ships `patcher.py`, `cdp.py` and a full `cdp_driver/` package; 187 CDP-related Python files across the tree (**Tier A**)
> **Anti-bot service claims:** narrower and more checkable than most — the README demonstrates **one Cloudflare challenge page** via a runnable example script (`examples/cdp_mode/raw_gitlab.py`) rather than a coverage grid (**Tier B**)
> **Maintenance:** Very actively maintained — **4.51.12** (2026-08-10, "CDP Mode: Patch 128"); near-daily releases. 12.9k stars, 33 contributors, last push 2026-08-14. MIT.
> **Verified:** 2026-08-14 against `seleniumbase/SeleniumBase` @ `7cd42ef`.

---

## Overview

SeleniumBase is a comprehensive Python framework built on Selenium 4.x that combines browser automation, E2E testing, web crawling/scraping, and anti-bot bypass. Its **UC Mode** (Undetected-Chromedriver Mode) and, more importantly now, its **CDP Mode** (a CDP-native driver based on NoDriver) make it one of the most effective Python tools for bypassing modern bot detection.

As of the 4.50.x line, the project's own positioning has shifted: the README now brands SeleniumBase as **"Stealthy Chromium Automation with Python"** and states that **CDP Mode**, not UC Mode, is the recommended path "for maximum stealth." UC Mode is still present and is the on-ramp that launches and patches the browser, but the stealthy driving increasingly happens through CDP Mode and the newer **Stealthy Playwright Mode**.

## Assessment

> **Editorial judgment, not measurement.** Star ratings were removed from this report
> in the 2026-08-14 revision — no rubric defined them and no evidence backed any cell.
> What follows is reasoning from the verified architecture; disagree with the reasoning.

| | |
|---|---|
| **Strongest at** | Breadth. It is the only tool here that combines a stealth driver, a test framework, and built-in click-based CAPTCHA handling (Turnstile, reCAPTCHA, DataDome slider, Friendly Captcha, Incapsula hCaptcha) in one package. |
| **Also good** | Release discipline — near-daily releases, 33 contributors, only 13 open issues. The healthiest maintenance profile of any tool in this report. |
| **Weakest at** | Learning curve and footprint. The breadth that makes it capable also makes it heavy, and stealth is Chromium-only. |
| **Notably honest** | Its claims are narrower than its peers': the README ships a runnable example against one Cloudflare challenge page rather than asserting a coverage grid. That is more checkable than most, and worth more. |
| **Reasonable for** | Teams that need automation *and* testing in one stack, or anyone who needs CAPTCHA handling without bolting on a third-party solver. |
| **Reach for something else if** | You want a minimal dependency footprint (Patchright) or Firefox (Camoufox). |

> **Note on this analysis:** claims below were verified against the SeleniumBase source
> at commit `7cd42ef` (2026-08-14, v4.51.12 line). Some code excerpts were first read at
> v4.50.5 (`4de63c8`); file paths are given so you can check them yourself.

---

## How It Works - Technical Deep Dive

SeleniumBase's stealth is delivered by two cooperating layers plus an optional CAPTCHA layer:

1. **UC Mode** — patches ChromeDriver, launches Chrome, and uses a disconnect/reconnect trick so the browser looks driver-free during detection.
2. **CDP Mode** — a CDP-native driver (a fork based on `ultrafunkamsterdam/nodriver`) that drives Chrome over the DevTools Protocol with **no WebDriver attached at all**. This is now the recommended "maximum stealth" path.
3. **PyAutoGUI CAPTCHA layer** (optional extra) — OS-level mouse clicks for checkbox-style CAPTCHAs.

### UC Mode (Undetected-Chromedriver Mode)

UC Mode is based on the undetected-chromedriver project but with significant enhancements. It uses **three core techniques**:

### 1. ChromeDriver Binary Patching

The patcher modifies the chromedriver executable to remove the JavaScript that injects the `cdc_` markers websites scan for. The real implementation lives in `seleniumbase/undetected/patcher.py` (`Patcher.patch_exe`, lines ~212–248). Rather than just renaming variables, it **overwrites the injected JS with whitespace** (same byte length, so the binary size is preserved) and randomizes the call-function cache name:

```python
# seleniumbase/undetected/patcher.py  (Patcher.patch_exe)
def gen_js_whitespaces(match):
    return b"\n" * len(match.group())          # blank out the injected JS

with io.open(self.executable_path, "r+b") as fh:
    file_bin = fh.read()
    # 1) Neutralize:  window.cdc_<22chars>_(Array|Promise|...) = window.(Array|...)
    file_bin = re.sub(
        b"window\\.cdc_[a-zA-Z0-9]{22}_"
        b"(Array|Promise|Symbol|Object|Proxy|JSON|Window) "
        b"= window\\.(Array|Promise|Symbol|Object|Proxy|JSON|Window);",
        gen_js_whitespaces, file_bin,
    )
    # 2) Neutralize the "|| ..." fallback form as well
    file_bin = re.sub(
        b"window\\.cdc_[a-zA-Z0-9]{22}_"
        b"(Array|Promise|Symbol|Object|Proxy|JSON|Window) \\|\\|",
        gen_js_whitespaces, file_bin,
    )
    # 3) Randomize the '$cdc_<22chars>_' call-function cache name
    file_bin = re.sub(b"'\\$cdc_[a-zA-Z0-9]{22}_';",
                      gen_call_function_js_cache_name, file_bin)
    fh.seek(0)
    fh.write(file_bin)
```

**Why it works:** Websites scan for the `window.cdc_*` / `$cdc_*` markers that chromedriver injects. UC Mode blanks out the injecting JS (replacing it with equal-length whitespace) and randomizes the cache-key name, so detection scripts can't find the markers. `is_binary_patched()` checks for the literal `window.cdc_adoQpoasnfa76pfcZLmcfl_` string to decide whether a re-patch is needed.

### 2. Browser-First Launch Strategy

This is a **key idea** that makes UC Mode effective:

```
Normal Selenium Flow (Detectable):
┌──────────────┐     launches      ┌─────────────┐
│ chromedriver │ ─────────────────→│   Chrome    │
└──────────────┘                   └─────────────┘
     ↑ Bot signatures visible from start

UC Mode Flow (Stealthy):
┌─────────────┐   starts first    ┌─────────────┐
│   Chrome    │ ←─────────────────│  UC Mode    │
└─────────────┘                   └─────────────┘
       ↓ Running clean
┌──────────────┐   connects after  ┌─────────────┐
│ chromedriver │ ─────────────────→│   Chrome    │
└──────────────┘                   └─────────────┘
     ↑ Connects to already-running browser (patched)
```

**Why it works:** Normal Selenium launches Chrome *through* chromedriver, which injects detectable artifacts from the start. UC Mode launches a patched, standalone Chrome and connects afterward, so the browser appears clean during page load.

### 3. Disconnect/Reconnect Mechanism

The signature UC Mode technique — disconnect chromedriver during sensitive moments. The real logic is in `seleniumbase/core/browser_launcher.py` (`uc_open_with_reconnect`, line ~589). Note it navigates by opening the URL in a **new tab via `window.open`** while disconnected, then reconnects and switches to that tab:

```python
# seleniumbase/core/browser_launcher.py  (uc_open_with_reconnect)
if url.startswith("http:") or url.startswith("https:"):
    script = 'window.open("%s","_blank");' % url
    driver.execute_script(script)     # open target in a new tab
    time.sleep(0.05)
    driver.close()                    # close the blank origin tab
    if reconnect_time == "disconnect":
        driver.disconnect()           # stay disconnected
        time.sleep(0.008)
    else:
        driver.reconnect(reconnect_time)   # disconnect, wait, reconnect
        page_actions.switch_to_window(
            driver, driver.window_handles[-1], 2
        )
```

The `reconnect()` / `disconnect()` / `connect()` primitives live in `seleniumbase/undetected/__init__.py` (lines ~469–560). `reconnect(timeout)` stops the chromedriver service, sleeps for `timeout`, then restarts it — so during the wait window the page runs with no WebDriver connection attached.

```python
# High-level SB API (aliases of the above):
sb.uc_open_with_reconnect(url, reconnect_time=4)   # open + reconnect after N sec
sb.uc_open_with_disconnect(url, timeout)           # open + stay disconnected
sb.disconnect(); sb.connect(); sb.reconnect(timeout)
sb.uc_click(selector)                              # click while disconnected
```

**Why it works:** Bot detection scripts check for chromedriver's presence during page load and interactions. By disconnecting during those moments, the browser appears as a normal user session.

### 4. CDP Mode (the recommended maximum-stealth path)

CDP Mode drives Chrome purely over the Chrome DevTools Protocol with **no WebDriver connected**. Its driver is a fork **"based on NoDriver"** (`seleniumbase/undetected/cdp_driver/`, header comment in `cdp_util.py`), i.e. derived from `ultrafunkamsterdam/nodriver`. The high-level wrapper is `seleniumbase/core/sb_cdp.py` (~3,500 lines, 250+ methods) and the entry class is `sb_cdp.Chrome`.

```python
# seleniumbase/fixtures/base_case.py  (activate_cdp_mode)  and
# seleniumbase/core/browser_launcher.py (uc_open_with_cdp_mode)
sb.activate_cdp_mode(url)   # disconnect WebDriver, drive Chrome over CDP only
```

Under the hood, `uc_open_with_cdp_mode` calls `driver.disconnect()`, reads the browser's CDP endpoint, spins up an asyncio event loop, and connects the NoDriver-based `cdp_driver` to the running browser. From then on all interaction goes through CDP:

```python
sb.cdp.open(url)
sb.cdp.click(selector)
sb.cdp.type(selector, text)
sb.cdp.get_text(selector)
sb.cdp.gui_click_element(selector)   # OS-level click via PyAutoGUI
sb.cdp.scroll_down()
```

**CDP Mode advantages:**
- No WebDriver artifacts at all (the WebDriver is disconnected)
- Can be entered from UC Mode mid-session (`sb.activate_cdp_mode()`)
- A "Pure CDP Mode" entry point (`from seleniumbase import sb_cdp; sb = sb_cdp.Chrome()`) runs CDP-only without ever starting a SeleniumBase test/WebDriver session
- Best for heavily protected sites

### 5. Stealthy Playwright Mode (NEW)

New in the 4.5x line: **Stealthy Playwright Mode** (`examples/cdp_mode/playwright/`). It is a subset of CDP Mode where **Playwright attaches to the SeleniumBase-launched stealth browser** via the remote-debugging URL using Playwright's `connect_over_cdp()`. This lets Playwright scripts inherit SeleniumBase's stealth and CAPTCHA-solving while using Playwright's own API.

```python
# examples/cdp_mode/playwright/ (sync format)
from playwright.sync_api import sync_playwright
from seleniumbase import sb_cdp

sb = sb_cdp.Chrome()                      # launch stealthy browser
endpoint_url = sb.get_endpoint_url()      # its CDP endpoint
with sync_playwright() as playwright:
    browser = playwright.chromium.connect_over_cdp(endpoint_url)
    # ...drive with Playwright APIs, backed by SeleniumBase stealth...
```

It ships in three formats: `sb_cdp` "sync", `SB()` "nested sync", and `cdp_driver` "async". Because it attaches to the system Chrome that SeleniumBase already launched (`channel="chrome"` style), you can **skip the large `playwright install` browser download** entirely.

### 6. PyAutoGUI Integration for CAPTCHAs

For checkbox-style CAPTCHAs, UC/CDP Mode uses PyAutoGUI to click at the OS level, outside the browser context. PyAutoGUI is an **optional extra** (`pip install seleniumbase[pyautogui]`), auto-installed on first use by `install_pyautogui_if_missing()`. The click-solving methods are in `seleniumbase/core/browser_launcher.py` and `seleniumbase/core/sb_cdp.py`:

```python
# UC Mode (WebDriver) side — browser_launcher.py
sb.uc_gui_click_captcha()     # auto-detect + click (Turnstile / reCAPTCHA)
sb.uc_gui_click_cf()          # Cloudflare Turnstile checkbox
sb.uc_gui_click_rc()          # Google reCAPTCHA checkbox
sb.uc_gui_handle_captcha()    # auto-detect CF vs reCAPTCHA and handle

# CDP Mode side — sb_cdp.py
sb.cdp.solve_captcha()        # click-solve via CDP (alias: click_captcha())
sb.cdp.gui_click_captcha()    # click-solve via PyAutoGUI
```

The dispatcher `sb_cdp.__click_captcha()` inspects the page source and routes to the correct handler. As of 4.50.x it recognizes **five** CAPTCHA situations (detectors at `sb_cdp.py` ~2177–2220):

- Cloudflare Turnstile (`_on_a_cf_turnstile_page`)
- Google reCAPTCHA (`_on_a_g_recaptcha_page`)
- Incapsula/Imperva hCaptcha (`_on_an_incapsula_hcaptcha_page`)
- DataDome slider CAPTCHA (`_on_a_datadome_slider_page` → `__gui_slide_datadome_captcha`)
- Friendly Captcha (`_on_a_friendly_captcha_page`)

```python
# seleniumbase/core/sb_cdp.py  (__click_captcha dispatcher)
if self._on_a_cf_turnstile_page(source):      pass          # -> Turnstile click
elif self._on_a_g_recaptcha_page(source):     ... recaptcha
elif self._on_an_incapsula_hcaptcha_page():   ... incapsula hcaptcha
elif self._on_a_datadome_slider_page():       ... datadome slider
elif self._on_a_friendly_captcha_page():      ... friendly captcha
```

**Why it works:** PyAutoGUI operates at the OS level, completely outside the browser context, so the click is indistinguishable from a real user's. Note: these are **click/slide solvers** for the "prove you're human" checkbox/slider widgets — they are not image-recognition solvers, and they still require a real display (see limitations).

---

## Architecture

```
SeleniumBase Stealth Stack (v4.50.x):
┌─────────────────────────────────────────────┐
│  Your Code                                   │
│  SB(uc=True) / sb_cdp.Chrome() / sb.cdp.*    │
├─────────────────────────────────────────────┤
│  UC Mode Layer  (browser_launcher.py)        │
│  - ChromeDriver binary patching (cdc_ blank) │
│  - Browser-first launch                      │
│  - disconnect / reconnect / connect          │
├─────────────────────────────────────────────┤
│  CDP Mode Layer  (undetected/cdp_driver/,    │
│                   core/sb_cdp.py)            │
│  - CDP-native driver, based on NoDriver      │
│  - WebDriver fully disconnected              │
│  - asyncio event loop over DevTools Protocol │
│  ├─ Stealthy Playwright Mode                 │
│  │  (Playwright connect_over_cdp)            │
├─────────────────────────────────────────────┤
│  PyAutoGUI Layer (optional extra)            │
│  - OS-level mouse/keyboard for CAPTCHAs      │
│  - Turnstile / reCAPTCHA / DataDome slider / │
│    Friendly Captcha / Incapsula hCaptcha     │
├─────────────────────────────────────────────┤
│  Patched ChromeDriver (UC entry only)        │
│  - cdc_ injection blanked out                │
├─────────────────────────────────────────────┤
│  Chrome / Chromium (also Brave, Edge, Opera) │
│  - Launched independently, connected after   │
└─────────────────────────────────────────────┘
```

---

## Key Methods Reference

### UC Mode Methods (WebDriver, `browser_launcher.py`)
```python
sb.uc_open_with_reconnect(url, reconnect_time=4)   # open + reconnect after N sec
sb.uc_open_with_disconnect(url, timeout)           # open + stay disconnected
sb.uc_click(selector)                              # click while disconnected
sb.uc_gui_click_captcha()                          # PyAutoGUI click (auto-detect)
sb.uc_gui_click_cf()  /  sb.uc_gui_click_rc()      # Turnstile / reCAPTCHA
sb.uc_gui_handle_captcha()                         # auto-detect CF vs reCAPTCHA
sb.disconnect(); sb.connect(); sb.reconnect(timeout)
```

### CDP Mode Methods (`sb_cdp.py`, 250+ methods)
```python
sb.activate_cdp_mode(url)          # switch from UC/WebDriver into CDP Mode
sb.cdp.open(url)
sb.cdp.click(selector)
sb.cdp.type(selector, text)
sb.cdp.get_text(selector)
sb.cdp.gui_click_element(selector) # OS-level click
sb.cdp.solve_captcha()             # click-solve (alias: click_captcha)
sb.cdp.gui_click_captcha()         # click-solve via PyAutoGUI
sb.cdp.get_endpoint_url()          # for Stealthy Playwright attach
```

---

## Targets the project ships examples for

> **This is not a list of confirmed bypasses.** It is a list of protected sites the
> project ships runnable example scripts against — which is a stronger form of evidence
> than a ✅ grid (the file paths are verifiable, and you can run them yourself) but
> weaker than a benchmark. Whether any given script still passes today depends on the
> site's current configuration and your IP. Nothing here was executed. **Tier B.**

Most stealth examples live under `examples/cdp_mode/` (Pure CDP Mode) and `examples/cdp_mode/playwright/` (Stealthy Playwright):

| Service | Protection Type | Example File (verified present) |
|---------|-----------------|---------------------------------|
| Cloudflare (WAF + Turnstile) | WAF + Turnstile | `examples/verify_undetected.py`, `examples/cdp_mode/raw_cdp_turnstile.py`, `raw_cdp_gitlab.py` |
| Imperva/Incapsula | WAF + hCaptcha | `examples/cdp_mode/raw_pokemon.py` |
| DataDome | Behavioral + slider CAPTCHA | `examples/cdp_mode/raw_bestwestern.py`, `raw_antibot.py` |
| Kasada | Advanced bot management | `examples/cdp_mode/raw_hyatt.py`, `raw_cdp_hyatt.py` |
| PerimeterX / general anti-bot | Behavioral / AI detection | `examples/cdp_mode/raw_walmart.py`, `raw_cdp_walmart.py` |
| Google reCAPTCHA | Invisible / checkbox challenges | `examples/cdp_mode/raw_cdp_recaptcha.py` |
| Fingerprint / bot-detection probes | Fingerprint & automation checks | `examples/cdp_mode/raw_browserscan.py`, `raw_cdp_sannysoft.py`, `raw_cdp_fingerprint.py`, `raw_cdp_pixelscan.py` |

**Real-world sites demonstrated (current examples):** GitLab, Pokemon.com, Hyatt.com, BestWestern.com, Walmart.com, Nike, Nordstrom, SeatGeek, Indeed, Idealista, Reddit, Amazon, plus dedicated fingerprint/bot-detection test-site scripts (BrowserScan, Sannysoft, Pixelscan). *(Note: the older top-level `raw_bing.py` referenced in prior docs is no longer present; Bing CAPTCHA examples now live under `examples/cdp_mode/playwright/raw_bing_cap_*.py`.)*

---

## Usage Examples

### Basic UC Mode
```python
from seleniumbase import SB

with SB(uc=True, test=True) as sb:
    sb.uc_open_with_reconnect("https://cloudflare-protected-site.com", 4)
    sb.uc_gui_click_captcha()  # click-solves Turnstile / reCAPTCHA checkbox
    sb.assert_text("Success")
```

### Pure CDP Mode (recommended for maximum stealth)
```python
from seleniumbase import sb_cdp

sb = sb_cdp.Chrome("https://heavily-protected-site.com")
sb.sleep(2)
sb.solve_captcha()            # click-solve if a challenge appears
sb.click("button.submit")
sb.type("input#email", "user@example.com")
```

### UC → CDP hybrid
```python
from seleniumbase import SB

with SB(uc=True, test=True) as sb:
    sb.activate_cdp_mode("https://site.com")   # enter CDP Mode with the URL
    sb.sleep(2)
    sb.cdp.click("#login")
    sb.cdp.type("#email", "test@example.com")
```

### Stealthy Playwright Mode
```python
from playwright.sync_api import sync_playwright
from seleniumbase import sb_cdp

sb = sb_cdp.Chrome()
endpoint_url = sb.get_endpoint_url()
with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp(endpoint_url)
    page = browser.contexts[0].pages[0]
    page.goto("https://site.com")     # Playwright API, SeleniumBase stealth
```

### UC Mode with Proxy
```python
with SB(uc=True, proxy="user:pass@host:port", incognito=True) as sb:
    sb.uc_open_with_reconnect("https://target.com", 4)
```
*(`socks5h://` proxies are also supported, without auth, so DNS resolves through the proxy.)*

---

## Important Limitations

### 1. UC Mode + Headless = Detectable
Confirmed in `help_docs/uc_mode.md`: "UC Mode is detectable in Headless Mode, so don't combine those options." On Linux use a virtual display instead:
```python
# DON'T — detectable
with SB(uc=True, headless=True) as sb: ...

# DO (Linux) — xvfb virtual display (enabled by default when headed/headless not set)
with SB(uc=True, xvfb=True) as sb: ...
```
`xvfb=True` is also **required for PyAutoGUI** CAPTCHA methods on headless Linux, since PyAutoGUI needs a display.

### 2. Reconnect Overhead
Each reconnect adds latency (chromedriver service stop/start plus the reconnect wait window). The framework's default `reconnect_time` is a small constant; the caller usually supplies a larger value (e.g. `4`) to let detection scripts finish.
```
Standard Selenium: Baseline (1x speed)
UC Mode:  slower  (reconnect / disconnect wait windows)
CDP Mode: adds asyncio/CDP round-trip overhead
```
*(Exact slowdown factors are workload-dependent and not benchmarked here — treat "2–5x" style figures as unverified rough guidance, not a measured claim.)*

### 3. PyAutoGUI Requirement (optional extra)
Click-based CAPTCHA handling requires the optional extra plus a real display:
```bash
pip install seleniumbase[pyautogui]     # or auto-installed on first use
# + display server on Linux (xvfb)
```

### 4. Chromium-only stealth
UC Mode / CDP Mode stealth targets Chromium-family browsers (Chrome, Chromium, Brave, Edge, Opera). There is no Firefox stealth path. (Recent releases specifically fixed Brave and Opera automation — see v4.50.5.)

### 5. These are click-solvers, not image solvers
`solve_captcha()` / `uc_gui_click_captcha()` click checkboxes or slide sliders to pass challenges that only require "prove you're human." They do not recognize images or read distorted text; hard interactive challenges (image grids) are not solved.

---

## Pros and Cons

### Advantages

| Advantage | Details |
|-----------|---------|
| **Most Effective Python Solution** | Proven bypasses against major Chromium-facing anti-bots |
| **Multiple Stealth Modes** | UC Mode, CDP Mode (NoDriver-based), Stealthy Playwright Mode |
| **Built-in CAPTCHA click-solving** | Turnstile, reCAPTCHA, DataDome slider, Friendly Captcha, Incapsula hCaptcha |
| **Complete Testing Framework** | pytest / unittest / behave (BDD) integration, Recorder, Dashboard |
| **150+ example scripts** | Working code for real protected + test sites |
| **Very active development** | Current v4.51.12 (2026-08-10); near-daily releases |
| **Production Ready** | CI/CD, Docker, S3 logging, proxy (incl. socks5h) support |
| **MIT licensed** | Fully open source |

### Limitations

| Limitation | Details |
|------------|---------|
| **Complexity** | Large learning curve due to feature breadth |
| **Performance** | UC/CDP Mode slower than plain Selenium (reconnect + CDP overhead) |
| **Headless Limitation** | UC Mode detectable in headless mode; use xvfb on Linux |
| **Heavy Dependencies** | Large dependency tree (Selenium, trio, websockets, pytest, etc.) |
| **PyAutoGUI + display** | CAPTCHA click-solving needs the extra and a real/virtual display |
| **Chromium-Focused** | Stealth is Chromium-only; no Firefox stealth |

---

## Comparison with Alternatives

> **Star ratings below are the author's editorial judgment, not measurement.**
> No rubric defines the scale and no benchmark backs any cell. They are retained
> only as a rough relative ordering — see [METHODOLOGY.md](METHODOLOGY.md#rating-policy).

| Feature | SeleniumBase | Patchright | Botasaurus | CloakBrowser |
|---------|:------------:|:----------:|:----------:|:------------:|
| **Anti-Bot Bypass** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **CAPTCHA (click-solve)** | ⭐⭐⭐⭐⭐ | ❌ | ⭐⭐ | ❌ |
| **Human Mouse** | ⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Testing Framework** | ⭐⭐⭐⭐⭐ | ❌ | ❌ | ❌ |
| **Speed** | ⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐ |
| **Ease of Use** | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| **Cost** | Free (MIT) | Free | Free | $$ |

---

## When to Use SeleniumBase

### Best For:
- Complex Chromium sites with **multiple anti-bot layers**
- Need **click/slide CAPTCHA handling** (Turnstile, reCAPTCHA, DataDome slider)
- Want a **complete testing framework** (pytest/behave, Recorder, Dashboard)
- Python preference with **hundreds of proven bypass examples**
- Want **Playwright's API with SeleniumBase stealth** (Stealthy Playwright Mode)
- Projects requiring **CI/CD integration**

### Not Ideal For:
- High-speed automation (millions of requests) — HTTP-tier tools are faster
- Simple scraping (overkill)
- When you need **true headless UC Mode** (detectable)
- Non-Python environments
- Firefox-based stealth (use a Firefox tool instead)

---

## Performance Characteristics

| Mode | Speed | Stealth | Use Case |
|------|:-----:|:-------:|----------|
| Standard Selenium | ⭐⭐⭐⭐⭐ | ⭐ | No protection |
| UC Mode | ⭐⭐ | ⭐⭐⭐⭐ | Medium protection |
| CDP Mode (NoDriver-based) | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | Heavy protection (recommended) |
| Stealthy Playwright | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | Playwright API + max stealth |

*(Relative speed here is qualitative; SeleniumBase publishes no hard throughput benchmarks and none are asserted in this analysis.)*

---

## Key Files (for source reading)

| Path | What it contains |
|------|------------------|
| `seleniumbase/__version__.py` | Version string (currently `4.50.5`) |
| `seleniumbase/undetected/patcher.py` | ChromeDriver `cdc_` binary patching |
| `seleniumbase/undetected/__init__.py` | `reconnect` / `disconnect` / `connect` primitives |
| `seleniumbase/core/browser_launcher.py` | `uc_open_with_reconnect`, `uc_open_with_disconnect`, `uc_click`, `uc_gui_click_*` |
| `seleniumbase/undetected/cdp_driver/` | CDP-native driver, "based on NoDriver" |
| `seleniumbase/core/sb_cdp.py` | CDP Mode wrapper + `solve_captcha` dispatcher (250+ methods) |
| `seleniumbase/fixtures/base_case.py` | `activate_cdp_mode` and the SB API surface |
| `examples/cdp_mode/` | Pure CDP Mode example scripts (many `raw_*` scripts) |
| `examples/cdp_mode/playwright/` | Stealthy Playwright Mode examples |

---

## Bottom Line

SeleniumBase is the **most comprehensive Python solution** for modern Chromium web automation with anti-bot bypass. The 4.5x line has re-centered around **CDP Mode** (a NoDriver-based, WebDriver-free driver) as the recommended maximum-stealth path, added **Stealthy Playwright Mode** to bring that stealth to Playwright's API, and broadened built-in click-solving to Turnstile, reCAPTCHA, DataDome slider, Friendly Captcha, and Incapsula hCaptcha.

The trade-offs remain complexity and slower performance, and stealth is Chromium-only. For simple scraping it's overkill; for serious Chromium anti-bot bypass with interactive CAPTCHAs, it's the best Python option available.

**Recommendation:** Use CDP Mode (or Stealthy Playwright Mode) for complex protected Chromium sites, especially those with click/slide CAPTCHAs. Combine with residential proxies for best results.

**Effectiveness:** Excellent | **Complexity:** Medium-High | **Best Use:** Complex Chromium sites with CAPTCHAs

---

## Resources

- [GitHub Repository](https://github.com/seleniumbase/SeleniumBase)
- [Documentation](https://seleniumbase.io/)
- [UC Mode Guide](https://github.com/seleniumbase/SeleniumBase/blob/master/help_docs/uc_mode.md)
- [CDP Mode Guide](https://github.com/seleniumbase/SeleniumBase/blob/master/examples/cdp_mode/ReadMe.md)
- [Stealthy Playwright Mode Guide](https://github.com/seleniumbase/SeleniumBase/blob/master/examples/cdp_mode/playwright/ReadMe.md)
- [CDP Mode Methods (Stealth API)](https://github.com/seleniumbase/SeleniumBase/blob/master/help_docs/cdp_mode_methods.md)
- [Discord Community](https://discord.gg/Edhgd7X)

*(Analysis verified against SeleniumBase v4.50.5, commit `4de63c8`, 2026-07-03. Cloned on the research box at `~/research/projects/seleniumbase`, 9.0 MB.)*
