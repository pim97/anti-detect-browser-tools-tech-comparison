# Anti-Bot Bypass Tools - Technical Deep Dives

> **Honest, no-BS technical analysis of web scraping and anti-bot bypass tools.**
>
> Learn what actually works, how it works under the hood, and which tool fits your use case.

[![GitHub topics](https://img.shields.io/badge/topics-web--scraping%20%7C%20anti--detection%20%7C%20cloudflare--bypass-blue)](#)

### Sponsored by [Scrappey](https://scrappey.com/)

> **[Scrappey.com](https://scrappey.com/)** — Anti-bot bypass API that handles Cloudflare, DataDome, and more. Skip the browser automation complexity and let Scrappey handle the hard parts.

<!--
GitHub Repository Topics (add these in repo settings):
web-scraping, anti-detection, bot-bypass, cloudflare-bypass, captcha-bypass,
playwright, selenium, puppeteer, browser-automation, fingerprint-spoofing,
anti-bot, stealth-browser, datadome-bypass, kasada-bypass, akamai-bypass,
camoufox, patchright, seleniumbase, botasaurus, undetected-chromedriver,
cloakbrowser, scrapling, web-automation, scraping-tools, antibot-bypass, turnstile-bypass,
browser-fingerprinting, cdp-stealth, juggler, firefox-automation
-->

---

## Why This Exists

Every anti-detection tool claims to be "undetectable" or bypass "all bot protection." **Most of that is marketing.**

This repository provides:
- **Source code analysis** - We read the actual code, not just the docs
- **Technical breakdowns** - How each evasion technique works at the protocol level
- **Honest assessments** - Real limitations, not just success stories
- **Comparison guides** - Pick the right tool for your specific use case

---

## Tool Analyses

| Tool | Type | Language | Best For | Analysis |
|------|------|----------|----------|----------|
| [**Camoufox**](./camoufox.md) | Custom Firefox build | Python | C++ level stealth, fingerprint rotation | [Read →](./camoufox.md) |
| [**Patchright**](./patchright.md) | Playwright binary patch | Python, Node.js, .NET | Maximum stealth with Playwright API | [Read →](./patchright.md) |
| [**SeleniumBase**](./seleniumbase.md) | Selenium + UC Mode | Python | CAPTCHA solving, testing framework | [Read →](./seleniumbase.md) |
| [**Botasaurus**](./botasaurus.md) | Selenium wrapper | Python | Human-like mouse movements | [Read →](./botasaurus.md) |
| [**XDriver**](./xdriver.md) | Playwright CDP patch | Python | Quick stealth without code changes | [Read →](./xdriver.md) |
| [**CloakBrowser**](./cloakbrowser.md) | Custom Chromium build | Python, Node.js | C++ stealth + human behavior + Chromium API | [Read →](./cloakbrowser.md) |
| [**Scrapling**](./scrapling.md) | All-in-one scraping framework | Python | TLS stealth + adaptive parsing + spider framework | [Read →](./scrapling.md) |
| [**Obscura**](./obscura.md) | Custom Rust headless engine | Rust (CLI), Puppeteer/Playwright clients | Lightweight V8 scraper with CDP API | [Read →](./obscura.md) |

---

## Quick Comparison

### Stealth Capabilities

| Feature | Camoufox | Patchright | SeleniumBase | Botasaurus | XDriver | CloakBrowser | Scrapling |
|---------|:--------:|:----------:|:------------:|:----------:|:-------:|:------------:|:---------:|
| `navigator.webdriver` bypass | ✅ C++ | ✅ | ✅ | ✅ | ✅ | ✅ C++ | ✅ (via Patchright/Camoufox) |
| `Runtime.enable` bypass | ✅ Juggler | ✅ | ✅ | ❌ | ✅ | ✅ | ✅ (via Patchright) |
| Fingerprint rotation | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐ | ⭐⭐ | ❌ | ⭐⭐⭐⭐ | ❌ |
| Human mouse simulation | ⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐⭐ | ❌ |
| CDP fingerprint evasion | N/A | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ (via Patchright) |
| Cross-platform parity | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ | ⭐ | ⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ |
| CAPTCHA solving | ❌ | ❌ | ⭐⭐⭐⭐⭐ | ⭐⭐ | ❌ | ❌ | ⚠️ Cloudflare only |
| Cloudflare bypass | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ (auto-solve) |
| Ease of use | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| TLS fingerprint impersonation | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ curl_cffi (HTTP tier) |
| Built-in parser | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ (784x faster than BS4) |
| Spider/crawler framework | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ Scrapy-like |
| Cost | Free | Free | Free | Free | Free | Free* | Free |

> **\*** CloakBrowser wrapper is MIT open-source; the Chromium binary is proprietary but free to use. See [security audit notes](./cloakbrowser.md#security-audit).

### Anti-Bot Service Coverage

| Service | Camoufox | Patchright | SeleniumBase | Botasaurus | XDriver | CloakBrowser | Scrapling |
|---------|:--------:|:----------:|:------------:|:----------:|:-------:|:------------:|:---------:|
| Cloudflare WAF | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ (Stealth) / ⚠️ (HTTP) |
| Cloudflare Turnstile | ⚠️ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ (auto-solve) |
| DataDome | ✅ | ✅ | ✅ | ⚠️ | ✅ | ✅ | ✅ (via Patchright/Camoufox) |
| Kasada | ⚠️ | ✅ | ✅ | ❌ | ✅ | ✅ | ✅ (via Patchright) |
| PerimeterX | ✅ | ⚠️ | ✅ | ❌ | ✅ | ✅ | ⚠️ |
| Akamai | ⚠️ | ⚠️ | ⚠️ | ❌ | ⚠️ | ⚠️ | ⚠️ |
| Imperva | ✅ | ⚠️ | ✅ | ❌ | ✅ | ✅ | ⚠️ |

✅ = Reliably bypasses | ⚠️ = Partial/conditional | ❌ = Not effective

> **Note:** Camoufox uses Firefox (~3% market share). Some WAFs may flag Firefox users more aggressively.

---

## Decision Guide

### When to Use What

| Your Situation | Recommended Tool | Why |
|----------------|------------------|-----|
| **Undetectable fingerprint spoofing** | [Camoufox](./camoufox.md) | C++ level = truly native, JS can't detect |
| **Need fingerprint rotation** | [Camoufox](./camoufox.md) | BrowserForge statistical accuracy |
| **Enterprise-level anti-bot** (Akamai, DataDome) | [Patchright](./patchright.md) + [Camoufox](./camoufox.md) | Combine protocol stealth with fingerprint rotation |
| **Need CAPTCHA solving** | [SeleniumBase](./seleniumbase.md) | Built-in Turnstile/reCAPTCHA handling |
| **Maximum Chromium stealth + free** | [Patchright](./patchright.md) | Protocol-level CDP bypass |
| **C++ Chromium stealth + Playwright API** | [CloakBrowser](./cloakbrowser.md) | 33 source-level patches, 0.9 reCAPTCHA score |
| **Human-like behavior (one flag)** | [CloakBrowser](./cloakbrowser.md) | `humanize=True` — Bézier mouse, typing, scroll |
| **Human-like mouse movements** | [Botasaurus](./botasaurus.md) | Best Bézier curve implementation |
| **Existing Playwright code** | [XDriver](./xdriver.md) or [CloakBrowser](./cloakbrowser.md) | No code changes needed (drop-in replacement) |
| **Quick prototype** | [Botasaurus](./botasaurus.md) | Simplest API |
| **Node.js / TypeScript** | [Patchright](./patchright.md) or [CloakBrowser](./cloakbrowser.md) | Multi-language support |
| **Testing framework needed** | [SeleniumBase](./seleniumbase.md) | pytest/unittest integration |
| **All-in-one scraping framework** | [Scrapling](./scrapling.md) | Fetching + parsing + crawling + stealth in one package |
| **HTTP-only stealth (no browser)** | [Scrapling](./scrapling.md) | TLS impersonation via curl_cffi — fastest option |
| **Adaptive scraping (sites change often)** | [Scrapling](./scrapling.md) | Auto-relocates selectors when DOM changes |
| **AI-integrated scraping** | [Scrapling](./scrapling.md) | MCP server for Claude/Cursor workflows |

---

## How Bot Detection Actually Works

Understanding detection helps you choose the right tool:

```
┌──────────────────────────────────────────────────────────────────────┐
│                         DETECTION LAYERS                              │
├──────────────────────────────────────────────────────────────────────┤
│  Layer 1: Protocol Detection                                          │
│  ├─ Runtime.enable timing         [Patchright, XDriver, CloakBrowser]│
│  ├─ Execution context leaks       [Patchright]                       │
│  ├─ Binding exposure              [XDriver]                          │
│  ├─ CDP input behavior mimicking  [CloakBrowser - 5 C++ patches]     │
│  └─ Juggler isolation (Firefox)   [Camoufox - unique]                │
├──────────────────────────────────────────────────────────────────────┤
│  Layer 2: Browser Fingerprinting                                      │
│  ├─ navigator.webdriver           [All tools]                        │
│  ├─ Canvas/WebGL fingerprints     [Camoufox C++, CloakBrowser C++]   │
│  ├─ Screen/Window properties      [Camoufox C++, CloakBrowser C++]   │
│  ├─ Audio context spoofing        [Camoufox C++, CloakBrowser C++]   │
│  └─ Font enumeration              [Camoufox, CloakBrowser]           │
├──────────────────────────────────────────────────────────────────────┤
│  Layer 3: Behavioral Analysis                                         │
│  ├─ Mouse movement patterns       [Botasaurus, Camoufox, CloakBrowser]│
│  ├─ Click timing distribution     [Botasaurus, SeleniumBase, CloakBrowser]│
│  └─ Scroll/navigation patterns    [Botasaurus, CloakBrowser]         │
├──────────────────────────────────────────────────────────────────────┤
│  Layer 4: Network Analysis                                            │
│  ├─ TLS fingerprinting (JA3/JA4)  [Scrapling Fetcher - curl_cffi]    │
│  ├─ WebRTC/UDP leakage            [Camoufox, XDriver, Scrapling]     │
│  ├─ IP reputation scoring         [Use proxies]                      │
│  └─ DNS leakage                   [Use SOCKS5H proxies]              │
└──────────────────────────────────────────────────────────────────────┘
```

---

## The Hard Truth

**No tool is truly undetectable.** Here's what the marketing won't tell you:

| Reality | Implication |
|---------|-------------|
| Detection is an arms race | What works today may fail tomorrow |
| Enterprise ≠ Free tier | Cloudflare Free vs Enterprise are different beasts |
| IP reputation matters most | Best stealth fails with datacenter IPs |
| Behavioral patterns accumulate | Same scraping pattern = eventual detection |
| TLS fingerprinting exists | Browser TLS signatures are nearly impossible to spoof |

### Realistic Success Rates

| Protection Level | Tools Alone | + Residential Proxies |
|-----------------|:-----------:|:---------------------:|
| Basic (CF Free, simple checks) | 90%+ | 99%+ |
| Medium (CF Pro, PerimeterX) | 60-80% | 90%+ |
| Enterprise (Akamai, DataDome) | 20-40% | 70-85% |
| Custom ML-based | <20% | 50-70% |

---

## Detection Test Sites

Test your setup against these:

| Test | What It Checks | URL |
|------|----------------|-----|
| Sannysoft | Automation detection | [bot.sannysoft.com](https://bot.sannysoft.com/) |
| BrowserScan | Comprehensive fingerprint | [browserscan.net](https://www.browserscan.net/bot-detection) |
| Fingerprint.com | Bot detection | [fingerprint.com](https://fingerprint.com/products/bot-detection/) |
| CreepJS | Browser fingerprint | [abrahamjuliot.github.io/creepjs](https://abrahamjuliot.github.io/creepjs/) |
| Pixelscan | Leak detection | [pixelscan.net](https://pixelscan.net/) |

---

## Tool Combination Strategies

For maximum effectiveness, consider combining tools:

### Strategy 1: Undetectable Fingerprint Rotation
```
Camoufox (C++ spoofing + BrowserForge) + Residential Proxies
= Statistically accurate fingerprints + clean IPs
= Best for: High-volume scraping with identity rotation
```

### Strategy 2: Behavioral + Protocol Stealth
```
Botasaurus (human mouse) + Patchright (CDP stealth)
= Human-like behavior + protocol-level evasion
```

### Strategy 3: CAPTCHA + Stealth
```
SeleniumBase UC Mode + Residential Proxies
= Automatic CAPTCHA solving + clean IP reputation
```

### Strategy 4: Quick Testing
```
XDriver (one-command activation) + Sannysoft test
= Fast iteration on stealth configuration
```

### Strategy 5: Firefox-based Maximum Stealth
```
Camoufox (Juggler isolation) + geoip auto-detection
= No automation artifacts visible + locale consistency
= Best for: Sites that don't discriminate against Firefox
```

### Strategy 6: Chromium C++ Stealth + Human Behavior
```
CloakBrowser (33 C++ patches + humanize=True) + Residential Proxies
= Source-level fingerprint spoofing + behavioral evasion + clean IPs
= 0.9 reCAPTCHA v3 score + Cloudflare Turnstile pass
= Best for: Chromium-required sites with behavioral detection
```

### Strategy 7: All-in-One Pipeline with Tiered Stealth
```
Scrapling (Fetcher for bulk HTTP + StealthyFetcher for protected pages)
= TLS-impersonated HTTP for 90% of pages + browser stealth for the rest
= Adaptive selectors survive site redesigns + spider handles crawling
= Best for: Large-scale scraping with mixed protection levels
```

---

## Contributing

Found a tool worth analyzing? Open an issue with:
1. Tool name and repository URL
2. What anti-detection approach it uses
3. What protection systems it claims to bypass

---

## Disclaimer

This repository is for **educational and legitimate purposes**:
- Security research and testing
- Academic study
- Authorized penetration testing
- Personal data retrieval from your own accounts

Always respect `robots.txt`, rate limits, and terms of service.

---

## GitHub Topics

Add these topics to your GitHub repository for better SEO:

```
web-scraping, anti-detection, bot-bypass, cloudflare-bypass, captcha-bypass,
playwright, selenium, puppeteer, browser-automation, fingerprint-spoofing,
anti-bot, stealth-browser, datadome-bypass, kasada-bypass, akamai-bypass,
camoufox, patchright, seleniumbase, botasaurus, undetected-chromedriver,
cloakbrowser, scrapling, web-automation, scraping-tools, antibot-bypass, turnstile-bypass,
browser-fingerprinting, cdp-stealth, perimeter-x, imperva-bypass
```

---

<p align="center">
  <i>Stop believing marketing claims. Read the source code.</i>
</p>
