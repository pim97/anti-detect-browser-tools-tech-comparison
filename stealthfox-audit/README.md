# Stealthfox Security Audit — Is the Closed-Source Binary Safe?

**TL;DR:** A Docker-based behavioral audit of the Stealthfox patched-Firefox binary. Same methodology as the CloakBrowser audit, adapted for Firefox. **Results below are placeholders until you run the container** — the harness is provided so anyone can produce their own evidence rather than trust a single party's screenshots.

> **Disclaimer:** This audit harness is provided strictly for educational and informational purposes. The author(s) of this repository are **not affiliated with Stealthfox or its author** in any way. This is an independent, third-party analysis tool. **No guarantee of safety or security is provided.** Behavioral testing reflects a point-in-time observation — it does not constitute a certification, endorsement, or warranty that the software is safe to use. **You run any third-party binary entirely at your own risk.** The author(s) accept no responsibility or liability for any damage, data loss, security breach, or other consequences resulting from using Stealthfox or any other software mentioned in this repository. Always perform your own due diligence before running closed-source executables.

---

## Why This Audit Exists

[Stealthfox](https://github.com/P0st3rw-max/stealthfox) is a stealth browser automation tool that ships a **closed-source, patched Firefox 150.0.1 binary**. The Python wrapper is MIT-licensed and fully readable. The binary itself, plus the Firefox C++ source patches that produce it, are **not public** — the README points to `github.com/P0st3rw-max/firefox-stealth` for the patches, but **that URL returns 404 at audit time**. The wrapper-vs-binary trust split is even more pronounced than CloakBrowser's, because there isn't even a published patch repo to read.

**The question:** When you run `pip install stealthfox && python -m stealthfox fetch` and it downloads a ~100 MB Firefox binary from `github.com/P0st3rw-max/stealthfox/releases`, how do you know it's not doing something malicious?

**You don't — not with certainty.** But you *can* observe its behavior. That's what this audit does.

---

## How Stealthfox Works Internally

```
User Code (Python)
    │
    ▼
┌──────────────────────────────────────────────────┐
│  Stealthfox()  (sync_api.py / async_api.py)      │
│                                                  │
│  1. ensure_binary()       → download patched FF  │
│  2. generate_profile(seed)→ Bayesian fingerprint │
│  3. translate_profile_to_prefs() → ~150 prefs    │
│  4. configure_proxy()     → SOCKS5 auth via prefs│
│  5. playwright.firefox.launch(executable_path,   │
│        firefox_user_prefs=…)                     │
└──────────────────────────────────────────────────┘
    │
    ▼
┌──────────────────────────────────────────────────┐
│  Playwright (Firefox CDP-equivalent: Juggler)    │
└──────────────────────────────────────────────────┘
    │
    ▼
┌──────────────────────────────────────────────────┐
│  Patched Firefox 150.0.1 binary  (CLOSED SOURCE) │
│  ~100 MB, ELF x86-64 (Linux) / PE (Windows)      │
│  Patches consume the zoom.stealth.* pref space:  │
│  • Canvas pixel substitution (per-seed noise)    │
│  • WebGL renderer/vendor/MSAA spoofing           │
│  • AudioContext sample-rate / latency / channels │
│  • Font enumeration whitelist + width metrics    │
│  • nsProtocolProxyService SOCKS5-with-auth patch │
│  • nr_stealth_bridge synthetic WebRTC srflx      │
│  • Juggler "humanize" Bezier mouse trajectory    │
│  • (Claimed) JA3/JA4 + Windows-style TCP SYN     │
└──────────────────────────────────────────────────┘
```

### The Trust Model

| Component | Source Available | Can You Audit It? |
|-----------|:-:|---|
| Python wrapper (`src/stealthfox/`) | Yes (MIT) | Fully readable, ~1.6k LOC, well-engineered |
| Bayesian sampler + CPT data | Yes (MIT) | Source + 11 JSON tables under `_fpforge/data/` |
| Firefox binary (`firefox`) | **No** (proprietary build) | **Cannot inspect the C++ patches** |
| Firefox patch source | **No** (`firefox-stealth` repo 404s) | **Worse than CloakBrowser** — there isn't even a private-but-claimed-public source repo to point at |
| SHA-256 checksums | Fetched from same GitHub release | Self-referential — if the release assets are compromised, both change |

### Binary Download Chain

```
pip install stealthfox
    → python -m stealthfox fetch
    → downloads from github.com/P0st3rw-max/stealthfox/releases/download/firefox-1/
       • firefox-150.0.1-stealth-linux-x86_64.tar.gz  (or -win-x86_64.zip)
       • checksums.txt   (signed by the same release tag)
    → SHA-256 verifies against checksums.txt
    → extracts to platformdirs.user_cache_dir("stealthfox")/firefox-1/
    → entry: firefox (Linux) / firefox.exe (Windows)
```

### Auto-Update Behavior

Unlike CloakBrowser, Stealthfox **does not auto-update**. The wrapper has no background daemon and no PyPI/GitHub polling. The binary is fetched once on first use (via `ensure_binary()` or the `stealthfox fetch` CLI) and cached forever under the version key `BINARY_VERSION = "firefox-1"` ([constants.py:10](https://github.com/P0st3rw-max/stealthfox/blob/master/src/stealthfox/constants.py)). To pull a newer version you have to bump `BINARY_VERSION` in the wrapper and reinstall — i.e. it's an explicit user action.

This is **good for trust** (no surprise replacement of a binary you've already audited) but **bad for security patches** (you'll keep running a stale Firefox until you manually update). FF150 ships with whatever CVEs were unpatched at the time of the stealth build.

### Sandbox Caveat (Windows headless mode only)

The wrapper silently sets `security.sandbox.gpu.level = 0` when `headless=True` on Windows ([prefs.py:386](https://github.com/P0st3rw-max/stealthfox/blob/master/src/stealthfox/prefs.py)). This is a real sandbox weakening of the Firefox GPU process. **This audit is Linux-only and does not exercise that code path** — it's flagged here as a separate concern that the behavioral tests cannot catch.

---

## Audit Methodology

We build a Docker container that:

1. Installs Stealthfox and downloads the Firefox binary
2. Runs the binary visiting only `about:blank` (no real websites)
3. Monitors everything: network traffic, file access, DNS queries, process tree, environment variables
4. Sets decoy secrets (fake AWS keys, GitHub tokens) and checks if they're exfiltrated
5. Blocks all network access and checks if the browser still works (malware often crashes without its C2 server)

### Test Environment (template — fill in after running)

| Property | Value |
|----------|-------|
| Date | _TBD — set when you run the audit_ |
| Binary | `firefox-150.0.1-stealth-linux-x86_64` |
| SHA-256 | _TBD — printed by the audit_ |
| Size | ~100 MB |
| Base image | `python:3.12-slim` (Debian Trixie) |
| Tools | tcpdump, strace, readelf, ldd, iptables, strings |

---

## Tests

Each test below describes **what is checked** and **what a clean result looks like**. Results columns are placeholders — populate them after running `docker run --rm --cap-add=NET_ADMIN stealthfox-audit`.

### Test 1: Binary Strings Analysis

Extracts all printable strings from the binary and searches for suspicious content.

| Check | Clean result looks like… | Your run |
|-------|--------------------------|---------|
| Suspicious URLs/domains | Only Mozilla/Firefox internals (OCSP, bugzilla, CRL endpoints, w3.org / unicode / IETF namespaces, test domains) | _TBD_ |
| Data exfiltration keywords | Matches are all standard DevTools / WebRTC / media APIs / Mozilla telemetry strings (which are pref-disabled at runtime) | _TBD_ |
| Crypto/wallet strings | Matches are standard Firefox autofill / crypto-policies / WebCrypto, not actual mining or wallet code | _TBD_ |
| Hardcoded IPs | Only well-known public DNS resolvers (Quad9, Cloudflare, Google) | _TBD_ |
| Base64 payloads | Long base64 strings decode to garbage (icon data, font tables, etc.) | _TBD_ |
| `zoom.stealth.*` prefs in strings | **Many entries present** — confirms binary really is a stealthfox build, not a stock Firefox swapped in | _TBD_ |

The last check is stealthfox-specific: the wrapper emits prefs in a `zoom.stealth.*` namespace that no upstream Firefox understands. If those strings are absent from the binary, the binary isn't actually the stealth build it claims to be.

### Test 2: Network Connection Monitoring

Launches browser visiting `about:blank` for 30 seconds with full packet capture.

**Expected baseline:** Stealthfox's [`_BASELINE`](https://github.com/P0st3rw-max/stealthfox/blob/master/src/stealthfox/prefs.py) pref dict explicitly disables every Mozilla service that would otherwise phone home: captive-portal detection, push services, telemetry, healthreport, geolocation, settings sync (`services.settings.server = ""`), regional defaults, search updates, addon updates, app updates, and Normandy. With those prefs applied, **about:blank should produce zero outbound traffic.**

| Check | Clean result | Your run |
|-------|--------------|---------|
| Total non-localhost packets | 0–small handful (any traffic warrants investigation) | _TBD_ |
| Destination IPs | None | _TBD_ |
| Unexpected connections | None | _TBD_ |
| Binary phoning home | No | _TBD_ |

If **any** non-trivial outbound traffic appears on `about:blank`, the binary is bypassing the wrapper's pref configuration — that's a serious flag because the wrapper relies on those prefs being honored for every other stealth claim too.

### Test 3: File System Access Audit

Runs the browser under `strace` capturing every `open` / `openat` / `read` / `write` / `connect` syscall.

| Check | Clean result | Your run |
|-------|--------------|---------|
| SSH keys (`~/.ssh/`) | Not accessed | _TBD_ |
| AWS credentials (`~/.aws/`) | Not accessed | _TBD_ |
| `.env` files anywhere | Not accessed | _TBD_ |
| Crypto wallets | Not accessed | _TBD_ |
| Cloud creds (`~/.gcloud`, `~/.azure`, `~/.kube`) | Not accessed | _TBD_ |
| Other Firefox profiles (`key4.db`, `logins.json`, `signons.*`) | Not accessed (would be browser-credential theft) | _TBD_ |
| Files opened | `/etc/localtime`, `/etc/os-release`, `/etc/resolv.conf`, GTK theme files, fontconfig caches, the cached `firefox-1/` profile, Xvfb sockets | _TBD_ |

The Firefox-specific extra check (vs the CloakBrowser audit) is `key4.db` / `logins.json` / `signons.*`. A malicious Firefox build might attempt to read **other Firefox profiles** on the host to steal saved passwords and cookies. Stock Firefox never reaches outside its own profile dir; if stealthfox does, that's a major flag.

### Test 4: Process Tree Audit

| Process | Expected? | Purpose |
|---------|:-:|---------|
| `firefox` (parent) | Yes | Main browser process |
| `firefox -contentproc` (1+) | Yes | Content rendering. Stealthfox disables Fission (`fission.autostart = False`), so expect *fewer* content processes than vanilla FF150 |
| `firefox -contentproc -isForBrowser` socket | Yes | Networking process |
| `firefox -contentproc … gpu` | Maybe | GPU process; may be absent in headless/Xvfb |
| `crashreporter` / `crashhelper` | Yes | Crash reporting. The wrapper does **not** disable Mozilla's crash reporter via prefs — flag if it phones home |
| **Unknown processes** | None | _Your run: TBD_ |

### Test 5: DNS Query Audit

Captures all DNS queries during browser operation on `about:blank`.

**Expected baseline:** with all baseline prefs applied, **zero DNS queries**. Any query at all is investigable. Even queries to mozilla.org domains are suspicious here, because the wrapper claims to have disabled every channel that would resolve them.

| Check | Clean result | Your run |
|-------|--------------|---------|
| Total DNS queries | 0 | _TBD_ |
| Domains queried | None | _TBD_ |

### Test 6: Binary Section Analysis

| Check | Clean result | Your run |
|-------|--------------|---------|
| File type | `ELF 64-bit LSB pie executable, x86-64` | _TBD_ |
| Build ID | A unique build ID is present (`readelf -n`) | _TBD_ |
| Shared libraries | All standard Firefox runtime deps (gtk, dbus-glib, nss, X11, alsa, pulse, gbm, fontconfig, freetype, harfbuzz, etc.) | _TBD_ |
| Suspicious shared libraries | None — no unknown `.so` linked | _TBD_ |
| `application.ini` shipped alongside | Present, names "stealthfox" / version / buildID | _TBD_ |

The wrapper ([prefs.py:38-46](https://github.com/P0st3rw-max/stealthfox/blob/master/src/stealthfox/prefs.py)) explicitly notes a 2026-04-28 fix where the previous static `general.buildID.override` value was replaced with the binary's compiled-in `buildID` — this test surfaces whether `application.ini` actually contains a fresh, plausible buildID, and whether it matches the value the binary emits at runtime.

### Test 7: Environment Variable Sniffing (Canary Test)

Plants decoy secrets in environment variables, then monitors whether the browser reads or exfiltrates them.

```
AWS_SECRET_ACCESS_KEY=DECOY_aws_key_12345_CANARY
DATABASE_URL=postgresql://admin:DECOY_password@db.example.com/prod
GITHUB_TOKEN=ghp_DECOY_token_67890_CANARY
STRIPE_SECRET_KEY=sk_live_DECOY_stripe_CANARY
PRIVATE_KEY=-----BEGIN RSA PRIVATE KEY-----DECOY_CANARY
```

| Check | Clean result | Your run |
|-------|--------------|---------|
| `/proc/self/environ` reads | 0 attempts | _TBD_ |
| Cross-process `/proc/*/environ` reads | 0 attempts | _TBD_ |
| Canary strings in network traffic | None | _TBD_ |

> **Note:** the wrapper deliberately propagates `STEALTHFOX_WEBRTC_PUBLIC_IP` into the Firefox subprocess env if it's set ([launcher.py:281-286](https://github.com/P0st3rw-max/stealthfox/blob/master/src/stealthfox/launcher.py)). That's documented and intentional — used by `nr_stealth_bridge` to inject a synthetic WebRTC srflx. Don't confuse it with exfiltration.

### Test 8: Behavior When Network is Blocked

Blocks all outbound traffic with `iptables`, then launches the browser. Malware that phones home tends to crash, hang, or refuse to operate when its C2 server is unreachable.

| Check | Clean result | Your run |
|-------|--------------|---------|
| Browser launch | Succeeds | _TBD_ |
| `page.goto("about:blank")` | Succeeds | _TBD_ |
| Browser close | Clean | _TBD_ |

Stealthfox's baseline disables `network.captive-portal-service.enabled`, `network.connectivity-service.enabled`, and `app.update.enabled` precisely because the author saw those services compete with proxied page loads — so a fully network-blocked launch should be a non-event for a legitimate stealthfox build.

### Test 9: VirusTotal Hash Lookup

Submits the binary's SHA-256 hash to VirusTotal's API to check against 70+ antivirus engines.

| Check | Clean result | Your run |
|-------|--------------|---------|
| Hash lookup | Either NOT FOUND (binary too obscure to have been uploaded) or 0–3 false positives common for patched browser builds | _TBD_ |
| Malware flags | 0 high-confidence detections | _TBD_ |

To run: pass a free [VT API key](https://www.virustotal.com/gui/my-apikey):

```bash
docker run --rm --cap-add=NET_ADMIN -e VT_API_KEY=your_key stealthfox-audit
```

---

## Overall Verdict

```
┌─────────────────────────────────────────────────────────────┐
│  X / 9 TESTS PASSED                                         │
│  (Run the audit to populate this section.)                  │
└─────────────────────────────────────────────────────────────┘
```

### What "Pass" Means

The binary behaves like a legitimate patched Firefox: only accesses files a normal browser would, doesn't read your secrets, doesn't connect to unknown servers, doesn't spawn suspicious processes, and works fine offline.

### What This Does NOT Mean

This audit **cannot prove** the binary is safe. A sophisticated backdoor could:

| Evasion Technique | Test Catches It? |
|-------------------|:---:|
| Always-on data exfiltration | Yes |
| Time bomb (activates after N days) | **No** |
| Conditional trigger (specific sites/conditions) | **No** |
| Piggyback exfiltration (hides data in normal browsing traffic) | **No** |
| Targeted payload (only activates for specific users) | **No** |
| Encrypted exfiltration (blends with HTTPS traffic) | **No** |

The only guarantee is auditable source code — which Stealthfox's binary does not provide, and whose claimed patch repo (`P0st3rw-max/firefox-stealth`) currently 404s.

### Risk Comparison

| Tool | Wrapper Source | Patches Source | Binary Auditable | Risk Level |
|------|:-:|:-:|:-:|---|
| **Camoufox** | Open (MIT) | Open ([daijro/camoufox](https://github.com/daijro/camoufox)) | Yes — compile yourself | Lowest |
| **Patchright** | Open (MIT) | Open | Yes — compile yourself | Lowest |
| **CloakBrowser** | Open (MIT) | Closed | No — proprietary binary, but wrapper is mature | Medium |
| **Stealthfox** | Open (MIT) | **404 / not published** | **No** — proprietary binary, 1-commit project, single author, zero public reproducers | **Medium-High** |
| Random GitHub binary | — | — | — | High |

Stealthfox sits a notch above CloakBrowser on the risk axis specifically because (a) the patches are not just closed but unfindable, (b) the project is days old with no track record, and (c) every benchmark in the README is a single screenshot with no reproducer.

---

## Mitigation Recommendations

If you choose to use Stealthfox, reduce risk with:

```bash
# 1. Pin the binary version. The wrapper key is BINARY_VERSION = "firefox-1"
#    in src/stealthfox/constants.py. Don't bump it without re-running this audit.

# 2. Run inside Docker with no host filesystem mounted.
docker run --rm --network=custom-bridge -v /dev/shm:/dev/shm stealthfox-app

# 3. Block egress except to your scraping targets and proxy.
#    Stealthfox needs zero internet for itself — only for the pages you load.

# 4. Don't share Firefox profiles, ~/.mozilla, ~/.ssh, or any credentials with
#    the container. Run as a non-root user with no other secrets in env.

# 5. Verify the SHA-256 your wrapper downloaded matches what others see.
python3 -c "from stealthfox.download import ensure_binary; print(ensure_binary())" \
    | xargs sha256sum
# Compare against the checksums.txt from the GitHub release AND any community
# postings. If you're the only person ever to have seen this hash, that's data.
```

If you can't isolate it: **don't run it.** Use Camoufox instead — same approach, auditable patches, multi-year track record.

---

## Run the Audit Yourself

```bash
# Clone this comparison repo
git clone <this-repo>
cd anti-detect-browser-tools-tech-comparison/stealthfox-audit

# Build the audit container
docker build -f Dockerfile.security-audit -t stealthfox-audit .

# Run all 9 tests
docker run --rm --cap-add=NET_ADMIN stealthfox-audit

# Interactive inspection (browse artifacts manually)
docker run -it --cap-add=NET_ADMIN stealthfox-audit bash
# Then:  cat /tmp/binary_strings.txt | less
#        cat /tmp/strace_output.txt | less
#        bash /audit/07_env_sniff_test.sh
```

`--cap-add=NET_ADMIN` is needed for Test 8 (iptables network blocking). Without it, Test 8 will skip gracefully.

### What Each Test Does

| Test | Script | Technique | Duration |
|------|--------|-----------|----------|
| 1. Strings Analysis | `01_strings_analysis.sh` | `strings` + grep for URLs, exfil keywords, crypto, IPs, base64, `zoom.stealth.*` namespace check | ~5 s |
| 2. Network Monitor | `02_network_monitor.sh` | `tcpdump` during 30 s browser session on `about:blank` | ~35 s |
| 3. File Access | `03_file_access_audit.sh` | `strace` all `open/openat/read/write/connect` syscalls | ~25 s |
| 4. Process Tree | `04_process_monitor.sh` | `ps auxf` during browser session | ~25 s |
| 5. DNS Audit | `05_dns_audit.sh` | `tcpdump port 53` during browser session | ~25 s |
| 6. Binary Analysis | `06_binary_analysis.sh` | `readelf`, `ldd`, `file`, `application.ini` dump | ~2 s |
| 7. Env Sniffing | `07_env_sniff_test.sh` | Plant decoy secrets, `strace` for `/proc/*/environ`, capture network for canary strings | ~35 s |
| 8. Network Blocked | `08_blocked_network_test.sh` | `iptables -j DROP`, launch browser, check behavior | ~25 s |
| 9. VirusTotal | `09_virustotal.sh` | SHA-256 hash lookup against 70+ AV engines via VT API | ~5 s |

**Total runtime:** ~3 minutes.

---

## Artifacts

After running the audit, these files are available inside the container for manual inspection:

| File | Contents |
|------|----------|
| `/tmp/binary_strings.txt` | All extracted strings from the binary |
| `/tmp/network_capture.txt` | Full packet capture during Test 2 |
| `/tmp/strace_output.txt` | All syscalls (file + network) during Test 3 |
| `/tmp/dns_queries.txt` | DNS queries during Test 5 |
| `/tmp/strace_env.txt` | Strace log from canary test (Test 7) |
| `/tmp/env_pcap.pcap` | Network capture during canary test (Test 7) |

---

## Differences vs the CloakBrowser Audit

For anyone comparing the two harnesses side by side:

| Concern | CloakBrowser | Stealthfox |
|---------|-------------|------------|
| Engine | Chromium (`chrome` binary, `--no-sandbox`) | Firefox 150 (Gecko, native sandbox respected on Linux) |
| Auto-update | Yes — background daemon polls PyPI + GitHub hourly | **No** — explicit, version-pinned, one-time fetch |
| Expected `about:blank` traffic | Some (PyPI/GitHub update check from wrapper) | **Zero** (wrapper baseline kills every Mozilla service) |
| Process tree | Chromium zygote / renderer / GPU / utility | Firefox parent / contentproc / socket / GPU (Fission disabled → fewer procs) |
| Browser-credential theft test | Not specifically targeted | **Added** — checks for `key4.db` / `logins.json` / `signons.*` access |
| Sandbox caveat | Wrapper passes `--no-sandbox` (auditable) | Wrapper sets `security.sandbox.gpu.level=0` only on Windows headless mode (Linux audit doesn't exercise it) |
| Patch repo | Closed | **404 — claimed-public, actually unreachable** |
| Project age | Years | **Days** (1 commit at audit time) |

---

## Conclusion

Run the audit. Publish your hash + your nine results. The whole point of behavioral testing on a closed binary is that **anyone can produce evidence** — there's no need to trust the author of the tool *or* the author of this audit. Match what others see and you've got a reproducible signal; diverge and you've got something to investigate.

If you need guaranteed safety: use [Camoufox](https://github.com/daijro/camoufox) (open-source Firefox with public C++ patches and a reproducible build).

If you're comfortable with the risk and the audit comes back clean on your machine: Stealthfox appears to be doing what it claims — based on what behavioral testing can see.

---

## Disclaimer

THIS REPOSITORY IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED. THE AUTHOR(S) ARE NOT RESPONSIBLE FOR ANY CONSEQUENCES ARISING FROM THE USE OF THIS INFORMATION OR THE SOFTWARE ANALYZED HEREIN. THIS IS NOT A SECURITY CERTIFICATION. BEHAVIORAL TESTS CANNOT PROVE THE ABSENCE OF MALICIOUS CODE — ONLY SOURCE CODE REVIEW CAN. THE AUTHOR(S) ARE NOT AFFILIATED WITH, ENDORSED BY, OR CONNECTED TO STEALTHFOX OR ITS AUTHOR. USE AT YOUR OWN RISK.
