# Code Review

Engineering assessment of the ten tools' codebases: structure, typing, test coverage, error
handling, dependency hygiene, and security-relevant patterns.

This page answers questions the [comparison](README.md) does not: *can I read this,
modify it, debug it at 3am, and ship it in production?* Detection capability and code
quality are independent properties — the tool with the most stealth features is not the
one with the most maintainable code.

**Verified 2026-10-13** against the commits listed under
[Commits reviewed](#commits-reviewed). Metrics are reproducible: `scripts/codemetrics.py`, run inside the sandbox
(see [How the numbers were produced](#how-the-numbers-were-produced)).

---

## Contents

- [Findings that should change a decision](#findings-that-should-change-a-decision)
- [Metrics](#metrics)
- [Per-tool assessment](#per-tool-assessment)
- [How the numbers were produced](#how-the-numbers-were-produced)
- [Limits of this review](#limits-of-this-review)

---

## Findings that should change a decision

### 1. CloakBrowser disables the Chromium sandbox by default and the Playwright sandbox switch cannot restore it

> [!CAUTION]
> `--no-sandbox` is part of CloakBrowser's default launch arguments in all three
> wrappers, so Playwright's `chromium_sandbox=True` cannot restore the sandbox. The only
> way out is `stealth_args=False`, which also drops the wrapper's fingerprint seed and
> platform flags. Combined with a closed engine binary, the default configuration runs
> unauditable native code against hostile web content with no OS-level sandbox.

`cloakbrowser/config.py:155-177` — `--no-sandbox` is hardcoded into the base argument
list (`:164-167`) returned by `get_default_stealth_args()`:

```python
def get_default_stealth_args() -> list[str]:
    seed = _random_seed()
    system = platform.system()

    base = [
        "--no-sandbox",
        f"--fingerprint={seed}",
    ]
```

The string appears exactly once in the Python package. The Node and .NET wrappers
carry the same default (`js/src/config.ts:433`, `dotnet/src/CloakBrowser/Config.cs:207`),
and `bin/cloakserve:353-354` builds its arguments from the same list with no opt-out.
The argument merge in `build_args()` (`browser.py:1439-1460`) deduplicates by flag key and lets caller
`args` override defaults, but it only adds and overrides — **it cannot remove a flag**.
The sole opt-out is `stealth_args=False` (`browser.py:325`), which skips the whole list,
including `--fingerprint=<seed>` and the platform flags. The project README shows those
being re-added by hand (`launch(stealth_args=False, args=["--fingerprint=42069",
"--fingerprint-platform=windows"])`, `README.md:822-825`), so spoofing without the
wrapper's `--no-sandbox` is possible. It is not the default, and the README does not
present it as a sandbox setting.

Playwright itself adds `--no-sandbox` whenever `chromiumSandbox` is not `true`
(`playwright-core/src/server/chromium/chromium.ts`, as carried in Patchright's
`patchright.patch`), so every Playwright-driven Chromium in this comparison runs without
the sandbox unless the caller passes `chromium_sandbox=True`. What is specific to
CloakBrowser is that its wrapper adds the flag itself, so that switch has no effect
under its default arguments.

The README does not mention `--no-sandbox` or justify it; the CHANGELOG mentions the
flag (`CHANGELOG.md:494`) and, at `:157`, the sandbox being disabled when running as
root. All of the above was re-read at `485f678` (wrapper 0.6.2); the v0.6.0 changes
(per-profile fingerprint seeds, the unified humanize engine) did not touch this
default.

**Why this matters more here than elsewhere:** the Chromium sandbox is the boundary that
contains a compromised renderer. Disabling it while processing untrusted web content
removes that boundary. CloakBrowser is also the only tool of the ten whose engine is a
**closed binary** — so a user is running unauditable native code, with the OS-level
sandbox off, against hostile input. Those two properties are individually defensible and
jointly significant.

For contrast, Clearcote's SDKs add `--no-sandbox` only conditionally on a native launch:
for the optional canvas-bridge feature, with the reason documented
(`docs/CANVAS-BRIDGE.md`: the renderer opens the bridge socket, which the sandbox
blocks), and when `serve()` runs as root on Linux, where Chromium refuses to start
without it. Neither is in the default native launch path. **There is one default route
without the sandbox:** Clearcote has no native macOS build, so on macOS `launch()` runs
the Clearcote Docker image (`sdk/python/clearcote/_docker.py:1-13`). The image runs a
sandbox probe and falls back to `--no-sandbox`, with a log line saying why, when the
probe fails (`docker/sandbox_check.py`, `docker/serve.py:455-464`). The probe passes only
when the container is started with the shipped seccomp profile, and the SDKs pass that
profile only on an x86_64 Docker daemon (`sdk/node/src/docker.ts:34-39`; Python
`_docker.py:35-40`, `:90`). On Apple Silicon, where the image runs emulated, and on a
Docker that refuses the profile, the browser therefore runs with `--no-sandbox` by
default. See footnote ⁵ under the security metrics.

**Mitigation if you use it:** run it in a container with a restricted seccomp profile
and dropped capabilities, treat the browser process as untrusted, and do not run it on a
host holding credentials.

### 2. Patchright's fragile-by-design approach is engineered correctly

> [!TIP]
> This is the pattern to copy if you maintain patches against someone else's source:
> throwing accessors so drift breaks the build, plus CI that diffs upstream versions.

Rewriting another project's source with an AST tool is inherently brittle. Patchright
handles that better than any other patching tool here, and it is worth stating because
the pattern generalises:

- **It fails loudly.** The patch modules use ts-morph's throwing accessors
  consistently — `getClassOrThrow`, `getMethodOrThrow`, `getImportDeclarationOrThrow`
  (225 `…OrThrow(` calls across `driver_patches/`: 38 in `crNetworkManagerPatch.ts`,
  33 in `crPagePatch.ts`, 27 in `framesPatch.ts`, at `ba8bd9b`). If Playwright moves a symbol, the build breaks at patch
  time rather than producing a silently unpatched driver that looks fine and leaks.
- **It detects upstream drift in CI.** `.github/workflows/check_patch_impact.yml` diffs
  two Playwright versions and writes a report. In the release workflow it runs with
  `create_issue: false` (`patchright_release.yml:103`); an issue and a draft PR come
  from the failure-notification job when the patched driver fails its test run
  (`patchright_release.yml:146`, `:347-353`).
- **Patches are per-file modules** (`driver_patches/*.ts`) rather than one script, so a
  break localises.

The failure mode this avoids is the one XDriver has: a **frozen prebuilt bundle**
(`playwright-core` 1.49.0) with no mechanism to detect that upstream has moved on. A
silently-stale stealth patch is worse than a loudly-broken one, because you deploy it
believing it works.

### 3. SeleniumBase's size and typing make it hard to modify safely

The most feature-complete tool here is also the least statically checkable:

| Measure | Value |
|---|---|
| Production code | 102,429 lines |
| Largest file | `seleniumbase/fixtures/base_case.py` — **17,703 lines; `BaseCase` has 579 methods** |
| Functions with any type annotation | **3.4%** of 3,946 |
| `except Exception` / `except BaseException` | 514 (5.0 per kLOC) |
| `time.sleep` / `asyncio.sleep` calls | 551 |
| `print(` in library code | 1,140 (11.1 per kLOC) |

`BaseCase` at 579 methods in one file is a god object: every capability is reachable
from one class, so IDE navigation, type inference, and reasoning about state are all
degraded. At 3.4% annotation coverage a type checker cannot help you, and 514 broad
`except` handlers mean failures surface as behaviour changes rather than tracebacks. 551
sleep calls indicate timing-based synchronisation, which is the usual source of flaky
automation.

None of this makes the tool ineffective — it is actively maintained, releases frequently
(5 version bumps, 4.55.0 to 4.56.1, between 2026-10-01 and 2026-10-12; the earlier
figure of 26 bumps in the 38 days to 2026-09-30 cannot be recomputed from the current
clone, whose history starts at 2026-09-29), and has 117 test files. It does mean **forking or patching it is expensive**, and
debugging a failure deep in the stack will be slower than in a 15k-line codebase.

**Most of the 42 `shell=True` calls are outside the browser-driving path, but not
all of them.** The distribution is unchanged at `be6514f`: 8 are in `seleniumbase/console_scripts/` (`sb_behave_gui.py`,
`sb_recorder.py`, `sb_commander.py`, `sb_caseplans.py` — developer CLI tooling that
builds pytest invocations from local paths), 10 in `utilities/selenium_grid/`, 11 in
`examples/` and 1 in `behave/`. The remaining 12 are in `core/`: `browser_launcher.py`
(10) runs `"<driver path>" --version` and `sbase get chromedriver <version>` while
preparing a launch, and `detect_b_ver.py` (2) probes the installed browser version. Those
interpolate local file paths and version strings, not page content. (An earlier revision
of this review stated that all 42 were in `console_scripts/`; that was already wrong at
the 2026-08-14 commit.)

### 4. Obscura's panic containment is partial and depends on per-connection threads

Obscura is 179,727 production lines, mostly Rust, in ten member crates. With inline
`#[cfg(test)]` modules and `#[test]` functions stripped, it contains **95 matching lines
of `.unwrap()`**, 1 `panic!` (`obscura-dom/src/tree_sink.rs:126`) and 30 `unsafe` blocks
(91, 1 and 20 at the 2026-09-30 revision). The `unsafe` lines are in
`obscura-js/src/runtime.rs` (11), `obscura-browser/src/idle_deadline.rs` (7),
`obscura-cli/src/main.rs` (4), `obscura-cdp/src/server.rs` (3), the non-member
`crates/test-support/allocations.rs` (3), `obscura-render/src/style.rs` (1) and
`obscura-js/src/ops.rs` (1).
Earlier revisions of this review reported 2,326 `.unwrap()`, 21 `panic!` and 11 `unsafe`
blocks. The first two counts included inline unit-test modules (at the 2026-08-14 commit
the non-test figures are 102 and 1), and the per-file counts quoted then (`io.rs` 18,
`domsnapshot.rs` 10, `target.rs` 8) were all inside `#[cfg(test)]` modules.

**Where the non-test unwraps are.** The largest concentration is `obscura-mcp/src/lib.rs`
(26, mostly `serde_json::to_string(&str).unwrap()`, which cannot fail for string inputs),
then `obscura-js/src/ops.rs` (8), `obscura-cli/src/main.rs` (7), 6 each in
`obscura-cdp/src/domains/accessibility.rs` (on JSON objects the code has just built) and
`obscura-browser/src/page.rs`, and 5 in `obscura-js/src/cdp_watchdog.rs`. The whole CDP
crate (`obscura-cdp`) has 9. Several sites acquire a `Mutex` or `RwLock` with `.unwrap()`
(`obscura-net/src/client.rs:907`, `:918`, `:1257`, `:1334`; `robots.rs:36-58`;
`cdp_watchdog.rs:52`, `:96`, `:117`).

**How panics are contained** (Tier A, read in source):

- `Cargo.toml:72-73` sets `[profile.release] panic = "unwind"`; the comment at `:68-71`
  says abort would turn every catchable op panic into a hard crash. `release-dist`
  inherits it.
- `obscura serve` runs each CDP connection on its own OS thread (`obscura-cdp-conn`) with
  its own current-thread Tokio runtime (`obscura-cdp/src/server.rs:797` `run_connection`, thread `:825`, runtime `:833`). A
  `SlotGuard` drop releases the connection-cap slot "however it exits" (`:806`), and the
  cap is 128 connections (`:45`). A panic on one connection's thread therefore ends that
  connection and its pages, not the other connections. `serve --workers N` adds process
  isolation behind a TCP balancer (`obscura-cli/src/main.rs:640` `run_multi_worker_serve`). Since `f2b9e99`
  (2026-10-04) the balancer reaps a worker that exits and starts a replacement
  (`main.rs:735-756`); the README states that a crash still closes the existing sessions
  on that worker (`README.md:478-481`).
- `catch_unwind` recovery sits at the JS-op and URL-op boundaries
  (`obscura-js/src/ops.rs:1879` in `op_dom`, commented "Anti-panic boundary" at `:1873`;
  the URL ops at `:6588`, `:6666`, `:6716`; also `op_initial_frame` at `:6035` and the
  two layout-caret ops at `:8114` and `:8131`), around module evaluation
  (`obscura-js/src/runtime.rs:3027`) and around each render-resource load (`:2280`). The four-file list in earlier revisions was
  wrong: `obscura-cdp/src/util.rs:164` is a test, `obscura-dom/src/serialize.rs:6` is a
  comment (the serialiser was made iterative because a stack overflow cannot be caught),
  and `runtime.rs:203` catches and re-raises.
- A V8 near-heap-limit guard (`runtime.rs:157-175`) and a per-command CDP watchdog
  (`obscura-cdp/src/dispatch.rs:766-789`, `OBSCURA_CDP_COMMAND_TIMEOUT_MS`) bound runaway
  pages.

**Residual risks still present in the source** (not exercised):

- Lock poisoning: the `Mutex` and `RwLock` `.unwrap()` sites above turn one poisoned lock
  into panics in later users. Commit `b3475a5` (2026-09-26) fixed the cookie jar only;
  the lock sites listed above are still present at `8edfe48`.
- Not recoverable with `catch_unwind`: non-V8 stack overflow, allocation failure and V8
  fatal errors abort the whole process. Recent upstream fixes show these occurred
  (transform-layer OOM abort `8395f29`, a `taffy` float abort `aaf189f`, a
  `set_v8_flags` abort `c5d26e6`, a frame-realm segfault `b185a44`, and several resource
  caps `c2e6fb2`, `bbcfbca`, `cfda91b`, `3a32fe8`).

In a CLI that fetches one page, a panic is an exit code. In `obscura serve` handling
concurrent sessions, containment is per connection thread and at specific op boundaries
rather than per page, and the abort classes above affect every connection in the process.
If you deploy Obscura as a long-running service, load-test it against hostile and
malformed HTML before trusting it; `serve --workers N` limits the blast radius to one
worker process, which the balancer now restarts.

Obscura's smell counts are low for its size: 1 broad catch, 1 TODO and 17 prints across
179,727 lines.

### 5. Botasaurus swallows errors more than any other codebase here

38 bare `except:` clauses across the two repos (17 in `botasaurus`, 21 in
`botasaurus-driver`) — the only tools in this set with double-digit bare excepts. A bare
`except:` catches `KeyboardInterrupt` and `SystemExit` as well as errors, so it can make
a process hard to interrupt and hides the cause of failures. Neither repository has a
commit after July 2026 (`6c9260d`, `db1d291`), so these figures are unchanged.

`botasaurus-driver` also has **zero test files** despite being 50,169 lines and the
component that actually implements the stealth. Much of that line count is generated CDP
bindings (`cdp/network.py` alone is 4,616 lines), which need no tests — but the
hand-written driver logic has none either.

### 6. invisible_playwright's browser makes a GitHub request on every launch, and the wrapper README does not describe it

> [!WARNING]
> The patched Firefox issues an HTTPS GET to GitHub on **every launch**, enabled by
> default. It is described in the engine README and in the wrapper's CHANGELOG, but not
> in the wrapper README's text or docs.

`BrowserGlue.sys.mjs:387-423` on branch `stealth/151` (inside `_beforeUIStartup`, called
from the `final-ui-startup` observer at `:194-195`) fires a fire-and-forget `fetch()` to a
GitHub release asset, gated on `invisible_firefox.usage_ping.enabled` (`:416`), which
`firefox.js:3683` defaults to `true`. The asset's download counter drives a badge. The URL
is no longer a literal: it is read from a second pref, `invisible_firefox.usage_ping.url`
(default at `firefox.js:3689`, fallback literal at `BrowserGlue.sys.mjs:419`), and
`invisible_core` sets that pref for every session (`prefs.py:361-362`, `:1990-2000`, at
`20da2af`). The
core never sets `enabled`, so neither package turns the ping off; it stays on unless the
caller passes `extra_prefs`. Engines older than `firefox-21` do not read the URL pref and
use a compiled address. The engine-side citations in this finding (`BrowserGlue.sys.mjs`,
`firefox.js`, and `Juggler.js` / `NetworkObserver.js` below) were re-read on 2026-10-13
from the git objects of the engine fork at `a3819a7` (`firefox-41`, the engine sealed by
core 41.39.0).

The request itself is benign: `credentials: "omit"`, `cache: "no-store"`, no payload, no
identifier, errors swallowed.

**Proxy behaviour (earlier statement withdrawn).** A previous revision said the request
follows the `network.proxy.*` prefs and that a dead proxy produces no direct fallback.
That no longer holds as written. The session proxy is not written to `network.proxy.*`
any more (`invisible_core/_proxy.py:145-148`). Since core 41.35.0 the proxy command is
sent by the Juggler client in the core rather than by each wrapper: `juggler.launch()`
sends `Browser.setBrowserProxy` after the readiness line and before any page exists, and
closes the browser if the engine refuses it (`invisible_core/juggler/connection.py:983-997`,
called from `_juggler/server.py:4338-4341` in the wrapper). The ping `fetch()` is issued
from the same `final-ui-startup` notification that starts Juggler's
network observer (`Juggler.js:92-96`, `NetworkObserver.js:647-675`). By source order the
ping is still created before the proxy command can have arrived. Whether it leaves through the
session proxy or from the host address was not run (**Tier D**).

**Disclosure.** A previous revision reported 0 matches for `usage_ping`, `launch counter`,
`launch.txt` or `usage-counter` in the whole `invisible_playwright` repository. At wrapper
0.35.3, `CHANGELOG.md:1349-1355` (0.12.2, 2026-09-05) describes the launch counter, the URL
pref and the opt-out, and `CHANGELOG.md:1356-1361` re-adds a "browser launches" badge, which
`README.md:309` shows with no explanation or link. The wrapper's README text and `docs/`
still contain 0 matches (apart from the badge image itself, `docs/badges/launches.svg`).
At the 2026-09-30 revision the engine README kept an "Anonymous launch counter" section
but named the deleted `feder-cr/invisible_firefox` repository as the host; that was not
re-checked for this refresh. The remaining
gap is placement: the explanation sits in the changelog and the engine repository rather
than in the README and docs that a `pip install invisible-playwright` user reads.

**Mitigation:** `InvisiblePlaywright(extra_prefs={"invisible_firefox.usage_ping.enabled": False})`.

### 7. Registry artifacts do not always correspond to published source

> [!WARNING]
> Reviewing the `botasaurus-driver` GitHub tree does not tell you what
> `pip install botasaurus-driver` puts on disk — PyPI is nine patch versions ahead of
> the published `setup.py`.

`botasaurus-driver` publishes **4.0.101** to PyPI (2026-08-10) while the repository's
`setup.py` reads **4.0.92** (still so at `db1d291`; the PyPI figure is from the
2026-09-30 registry check in [STATUS.md](STATUS.md)). The installed artifact does not correspond to any tagged
commit in the public repository, so source review of the GitHub tree does not tell you
what `pip install botasaurus-driver` puts on disk. For a stealth driver — where the
threat model includes supply chain — that gap matters.

---

## Metrics

Production code only. Test files, vendored trees, generated bundles, and minified assets
excluded. Raw counts are not quality scores; the per-kLOC columns exist because a
514-count in 102k lines and a 7-count in 16k lines are not comparable.

<details>
<summary><b>Size and test presence</b></summary>


| Repo | Prod LOC | Test files | Test LOC | Largest file |
|------|---------:|-----------:|---------:|--------------|
| `camoufox` | 42,918 | 179 | 31,707 | `typescript/src/fingerprints.ts` (1,981) |
| `patchright` | 7,736 | 2 | 0 | `driver_patches/framesPatch.ts` (1,336) |
| `patchright-python` | 1,098 | 0 | 0 | `patch_python_package.py` (843) |
| `SeleniumBase` | 102,429 | 117 | 3,616 | `seleniumbase/fixtures/base_case.py` (17,703) |
| `botasaurus` | 31,005 | 13 | 572 | `js/botasaurus-server-js/src/routes-db-logic.ts` (1,835) |
| `botasaurus-driver` | 50,169 | 0 | 0 | `botasaurus_driver/cdp/network.py` (4,616, generated) |
| `XDriver` | 295 | 0 | 0 | `x_driver/activator_script.py` (107) |
| `CloakBrowser` | 32,953 | 92 | 30,348 | `cloakbrowser/browser.py` (1,861) |
| `Scrapling` | 16,219 | 63 | 13,497 | `scrapling/engines/toolbelt/ad_domains.py` (3,537, data) |
| `obscura` | 179,727 | 83 | 19,426 | `crates/obscura-js/src/runtime.rs` (24,644) |
| `invisible_playwright` | 13,612 | 129 | 28,360 | `src/invisible_playwright/_juggler/server.py` (4,455) |
| `invisible_core` | 26,504 | 92 | 29,455 | `src/invisible_core/prefs.py` (2,024) |
| `clearcote-browser` | 63,262 | 219 | 60,945 | `sdk/dotnet/src/Clearcote/Humanize.cs` (2,709) |

Since `invisible_core` 38.34.0 (`1c23ba6`, 2026-10-09) the Juggler client, including the
bundled `injected.js`, lives in the core rather than the wrapper, which accounts for part
of the wrapper's drop from 21,406 lines. The bundle (`src/invisible_core/juggler/injected.js`,
8,121 lines) is excluded at its new path.

</details>

<details>
<summary><b>Typing and documentation (Python only)</b></summary>


Measured by AST over non-test Python: a function counts as annotated if any parameter or
the return carries an annotation.

| Repo | Functions | Annotated | Docstrings |
|------|----------:|----------:|-----------:|
| `CloakBrowser` | 422 | 95.7% | 51.2% |
| `invisible_core` | 716 | 93.6% | 64.1% |
| `invisible_playwright` | 529 | 91.1% | 43.5% |
| `Scrapling` | 558 | 85.5% | 60.4% |
| `botasaurus-driver` | 2,742 | 81.2%¹ | 27.5% |
| `camoufox` | 695 | 79.4% | 63.5% |
| `patchright-python` | 7 | 42.9% | 0.0% |
| `obscura` (Python parts) | 80 | 25.0% | 40.0% |
| `clearcote-browser` | 1,419 | 21.7% | 53.8% |
| `botasaurus` | 1,012 | 14.0% | 14.9% |
| `XDriver` | 12 | 8.3% | 33.3% |
| `SeleniumBase` | 3,946 | 3.4% | 21.0% |

¹ Inflated by generated CDP bindings, which are uniformly annotated. Hand-written driver
code is less consistent.

</details>

<details>
<summary><b>Error handling and code smells</b></summary>


| Repo | bare `except:` | broad `except` | per kLOC | `print(` | per kLOC | sleep calls | TODO/FIXME |
|------|---------------:|---------------:|---------:|---------:|---------:|------------:|-----------:|
| `camoufox` | 1 | 15 | 0.3 | 138 | 3.2 | 3 | 7 |
| `patchright` | 0 | 0 | 0.0 | 0 | 0.0 | 0 | 2 |
| `patchright-python` | 2 | 2 | 1.8 | 0 | 0.0 | 0 | 2 |
| `SeleniumBase` | 0 | 514 | 5.0 | 1,140 | 11.1 | 551 | 0 |
| `botasaurus` | 17 | 5 | 0.2 | 191 | 6.2 | 5 | 15 |
| `botasaurus-driver` | 21 | 3 | 0.1 | 59 | 1.2 | 22 | 11 |
| `XDriver` | 0 | 0 | 0.0 | 0 | 0.0 | 0 | 0 |
| `CloakBrowser` | 1 | 30 | 0.9 | 107 | 3.2 | 9 | 3 |
| `Scrapling` | 0 | 7 | 0.4 | 192 | 11.8² | 0 | 0 |
| `obscura` | 0 | 1 | 0.0 | 17 | 0.1 | 0 | 1 |
| `invisible_playwright` | 1 | 67 | 4.9 | 574 | 42.2 | 48 | 0 |
| `invisible_core` | 0 | 62 | 2.3 | 251 | 9.5 | 15 | 0 |
| `clearcote-browser` | 0 | 194 | 3.1 | 149 | 2.4 | 152 | 0 |

² Scrapling ships a CLI and an MCP server, where `print` is output rather than debug
residue. Counts alone do not distinguish the two.

</details>

<details>
<summary><b>Security-relevant patterns (production code)</b></summary>


| Repo | `shell=True` | `pickle.load` | `verify=False` | `--no-sandbox` | `unsafe` | `.unwrap()` |
|------|-------------:|--------------:|---------------:|---------------:|---------:|------------:|
| `camoufox` | 0 | 0 | 0 | 0 | – | – |
| `patchright` | 0 | 0 | 0 | 0 | – | – |
| `patchright-python` | 0 | 0 | 0 | 0 | – | – |
| `SeleniumBase` | 42³ | 1 | 3 | 11 | – | – |
| `botasaurus` | 21³ | 0 | 0 | 4 | – | – |
| `botasaurus-driver` | 0 | 0 | 0 | 2 | – | – |
| `XDriver` | 0 | 0 | 0 | 0 | – | – |
| `CloakBrowser` | 0 | 0 | 0 | 4⁴ | – | – |
| `Scrapling` | 0 | 1 | 0 | 0 | – | – |
| `obscura` | 0 | 0 | 0 | 1 | 30 | 95 |
| `invisible_playwright` | 0 | 0 | 0 | 0 | – | – |
| `invisible_core` | 0 | 0 | 0 | 0 | – | – |
| `clearcote-browser` | 0 | 0 | 1 | 84⁵ | – | – |

³ Botasaurus: all in CLI and server tooling (`bota/`, `botasaurus_server/`). SeleniumBase: 12
are in `core/` launch helpers (driver `--version` probes and driver installs), the rest in
CLI, grid and example code; see [finding 3](#3-seleniumbases-size-and-typing-make-it-hard-to-modify-safely).
⁴ Three of these are the same unconditional default in the Python, Node and .NET
wrappers; the fourth is a CHANGELOG line. See [finding 1](#1-cloakbrowser-disables-the-chromium-sandbox-by-default-and-the-playwright-sandbox-switch-cannot-restore-it).
⁵ Conditional on a native launch. The SDKs add it when `serve()` runs as root on Linux
(`sdk/python/clearcote/_launchopts.py:744-749`, used at `_serve.py:225-226`;
`sdk/node/src/index.ts:1420-1422`, call site `:1537`;
`sdk/dotnet/src/Clearcote/LaunchOpts.cs:604-607`) or when the opt-in canvas bridge is
enabled (`sdk/python/clearcote/_fingerprint.py:498-499`, `sdk/node/src/fingerprint.ts:614`,
`sdk/dotnet/src/Clearcote/Fingerprint.cs:462`). The Docker image, which is the default
route on macOS, runs `--no-sandbox` unless the container gets the shipped seccomp profile,
which the SDKs pass only on an x86_64 Docker (`sdk/node/src/docker.ts:34-39`); see
[finding 1](#1-cloakbrowser-disables-the-chromium-sandbox-by-default-and-the-playwright-sandbox-switch-cannot-restore-it).
29 of the 84 hits are in that Docker code and its documentation (`docker/`,
`_docker.py`, `docker.ts`, `DockerLaunch.cs`), up from 47 hits in all at 2026-09-30; the
remaining hits are docs, smoke scripts and tooling.

</details>

<details>
<summary><b>Project hygiene</b></summary>


| Repo | CI workflows | `py.typed` | pre-commit | Dependabot | CONTRIBUTING | SECURITY.md | CHANGELOG |
|------|-------------:|:----------:|:----------:|:----------:|:------------:|:-----------:|:---------:|
| `camoufox` | 2 | yes | – | – | yes | – | – |
| `patchright` | 6 | – | – | – | – | – | – |
| `patchright-python` | 2 | – | – | – | – | – | – |
| `SeleniumBase` | 6 | – | – | – | yes | yes | yes |
| `botasaurus` | 14 | – | – | – | yes | yes | – |
| `botasaurus-driver` | 0 | yes | – | – | – | – | – |
| `XDriver` | 1 | – | – | – | – | – | – |
| `CloakBrowser` | 3 | – | – | yes | – | – | yes |
| `Scrapling` | 4 | yes | yes | – | yes | – | yes |
| `obscura` | 3 | – | – | – | yes | yes | – |
| `invisible_playwright` | 9 | yes | – | – | yes | yes | yes |
| `invisible_core` | 3 | yes | – | – | – | – | – |
| `clearcote-browser` | 9 | – | – | – | yes | yes | – |

Only Scrapling runs pre-commit; only CloakBrowser configures Dependabot. Notable CI:
Patchright's `check_patch_impact.yml` (upstream drift detection), Clearcote's
`patch-integrity.yml` and `stealth-coherence` gate, Scrapling's `code-quality.yml`,
SeleniumBase's nightly matrix across macOS/Ubuntu/Windows.

---

</details>

## Per-tool assessment

**Camoufox** — 42.9k production lines of Python, TypeScript, JS and the C++ additions
(the 42 top-level `.patch` files under `browser/patches/`, plus 4 in its subdirectories,
are not in that count). On 2026-10-10 the repository was reorganised (#846, `cbca509`):
`patches/`, `additions/`, `settings/`, `Makefile` and `upstream.sh` moved under
`browser/`, and `pythonlib/camoufox/` became `python/src/camoufox/`; `6c3850f` removed
dead and duplicated launcher, script and CI code (net about 2,400 lines). The drop from
53.5k at 2026-09-30 is not decomposed further here. 179 test files and 31.7k test lines
(129 and 23k at 2026-09-30); Playwright's own suite is still not carried in-tree
(`make tests` in `browser/Makefile` runs it through `ci/run_playwright.py`, which applies
`ci/skiplist.yml`). 79.4% annotation and 63.5% docstring coverage on the Python side,
1 bare except and 15 broad ones (0.3/kLOC). The TypeScript launcher (`typescript/`) and
the `ci/` release pipeline sit beside the Python package. The C++ patch stack is the part
you would have to modify, and it requires a full Firefox build to validate;
`browser/Makefile` and `browser/upstream.sh` automate the fetch-and-patch cycle, and
fonts are an 843 MB pinned release asset (`docs/FONTS.md`) unpacked by
`make fonts-extract`.

**Patchright** — 7,736 lines of TypeScript, mostly AST surgery (`driver_patches/` is
5,136 lines in 36 modules), plus 1,098 lines of Python packaging code in
`patchright-python`. The metric tables count 2 test files; `utils/custom_tests/` holds 3
custom specs and `utils/` a detection smoke test, and each release is gated in CI on
Playwright's own `chromium-page` and `chromium-library` suites run against the patched
driver (`patchright_tests.yml:101`, `:108`), together with fail-loud accessors. The code
is per-file modular.

**SeleniumBase** — see [finding 3](#3-seleniumbases-size-and-typing-make-it-hard-to-modify-safely).
102k production lines, 3.4% annotation coverage and a single 17.7k-line class. Release
cadence: 5 version bumps (4.55.0 to 4.56.1) between 2026-10-01 and 2026-10-12, and a
nightly three-OS CI matrix (`python-nightly-{mac,ubuntu,windows}.yml`).

**Botasaurus** — split across a framework monorepo and a driver repo with different
standards. 38 bare excepts; the driver has no tests; PyPI is ahead of the published
source. The Bézier input implementation (`human_curve_generator.py`) is the most
readable part and is self-contained enough to lift out.

**XDriver** — 295 lines, zero tests, zero smells (trivially — there is almost no code).
The engineering content is in a prebuilt bundle nobody in this repository built. Nothing
to review, and nothing to maintain.

**CloakBrowser** — 33.0k lines of wrapper across Python, TypeScript, and C#. 92 test
files and 30.3k test lines. 95.7% annotation coverage and 30 broad excepts (0.9/kLOC),
against 81.0% and 95 (2.7/kLOC) at 2026-09-30; the change follows the v0.6.0 rewrite of
the humanize layer into one engine for every action (`d4924d9`, clean-up `15cb83e`),
after which `cloakbrowser/human/__init__.py` (3,083 lines then) is no longer the largest
file. The engine is closed, so half the system cannot be reviewed from source. Ships
Dependabot and a release-attestation workflow. Since 0.5.11 the wrapper unpacks
signature-verified archives without per-entry screening (`download.py:986-1002` at
0.6.2), and a supplied key that cannot be validated or a failed GeoIP lookup now aborts
the launch. See
[finding 1](#1-cloakbrowser-disables-the-chromium-sandbox-by-default-and-the-playwright-sandbox-switch-cannot-restore-it).

**Scrapling** — 85.5% annotation coverage, 60.4% docstrings, 0 bare excepts, 7 broad
excepts (0.4/kLOC) across 16.2k lines, 63 test files (0.4.15 added tests for the
Cloudflare solver, page reuse and Markdown conversion), and the only pre-commit
configuration; none of these figures moved between 2026-09-30 and `7a68493`.
CloakBrowser (95.7%), `invisible_core` (93.6%) and `invisible_playwright` (91.1%) have
higher annotation coverage, with broad-except densities of 0.9, 2.3 and 4.9 per kLOC.
Scrapling's largest file is a data table (`ad_domains.py`, 3,537 lines), not logic.

**Obscura** — 179.7k production lines, mostly Rust, in ten member crates (plus the
non-member `crates/test-support`), the largest codebase here by line count. The largest
file is `obscura-js/src/runtime.rs` (24,644 lines); `obscura-render/src/dom.rs` is 22,182,
and `obscura-js` also carries an 18,007-line `js/bootstrap.js`. Smell counts are low for
its size (1 broad catch, 1 TODO, 17 prints). The error strategy is in
[finding 4](#4-obscuras-panic-containment-is-partial-and-depends-on-per-connection-threads).

**Clearcote** — 63k lines of SDK, tooling and script code (Python, TypeScript, C#), up
from 33k at 2026-09-30; 57.1k of it is the three SDKs, where the humanized-input work of
SDK 0.33.0 to 0.49.0 landed, and the largest file is now
`sdk/dotnet/src/Clearcote/Humanize.cs` (2,709). Alongside are 37 readable patch files that
are not in that count, 219 test files and 9 CI workflows including a patch-integrity check
and a stealth-coherence regression gate (four required checks and one documented known
gap). 194 broad excepts (3.1/kLOC) is the third-highest density in the metrics table,
after SeleniumBase (5.0) and `invisible_playwright` (4.9); at 2026-09-30 Clearcote's
5.1 was the highest. Three of the patches still contain four diffs for stray backup files
(`patches/010:464`, `060:1045`, `130:572`, `130:1942`). One contributor, so review depth
and continuity depend on one person.

**invisible_playwright** — two packages. The wrapper is 13.6k first-party lines, counted
without the vendored Playwright-Python fork (`_pw/`, 61,997 lines); its largest file is
the in-process Juggler server (`_juggler/server.py`, 4,455 lines). Since wrapper 0.30.0
and core 38.34.0 (2026-10-09) the Juggler client and its bundled `injected.js` live in
`invisible_core`, which is 26.5k first-party lines without that bundle. Together: 129 and
92 test files, 91.1% and 93.6% annotation coverage, 43.5% and 64.1% docstrings, 67 and 62
broad excepts (4.9 and 2.3 per kLOC), 574 and 251 `print(` calls and 48 and 15 sleep
calls. Neither package contains C/C++ sources or a patch series; the engine changes live
in the separate `firefox_antidetect_patch` fork. `playwright` is no longer a runtime
dependency. The `eval`/`exec` pattern search (not shown in the tables) hits the wrapper 4
times, all in documentation prose and none in code; the excluded `injected.js` bundle has
5 lines matching `eval(`. See
[finding 6](#6-invisible_playwrights-browser-makes-a-github-request-on-every-launch-and-the-wrapper-readme-does-not-describe-it).

---

## How the numbers were produced

```bash
./scripts/sandbox.sh up
ssh <box> 'docker exec -i antidetect-box python3 -' < scripts/codemetrics.py > metrics.json
```

Every table in the metrics section is that script's output; none of it is hand-counted.
The script reads files as text, and Python through `ast.parse`; no project code is
imported or executed. Counting rules:

- **Vendored and generated trees excluded**: `node_modules`, `bundles`, `dist`, `build`,
  `target`, `vendor`, `third_party`, `__pycache__`, minified JS, lockfiles, `.patch`
  files, the vendored `json.hpp`, and invisible_playwright's vendored Playwright-Python
  fork (`_pw/`) and the bundled Juggler `injected.js` (at `_juggler/injected.js` in the
  wrapper until 2026-10-09, now at `juggler/injected.js` in `invisible_core`). The
  2026-10-13 run first missed the new path, which added 8,121 lines and an `eval` hit to
  `invisible_core`; the script was corrected and re-run before these tables were filled.
- **Test files excluded from production counts** and reported separately. For the
  Rust-only counts (`unsafe`, `.unwrap()`, `panic!`), items gated by `#[cfg(test)]`
  or `#[cfg(all(test, ...))]` and `#[test]` functions are also stripped, because Rust
  keeps unit tests inline in production files.
- **Lines** are counted the way `wc -l` counts them, over source extensions only (`py`,
  `js`, `ts`, `rs`, `cc`, `cpp`, `h`, `hpp`, `cs`). Pattern searches (smells, security)
  run over every non-excluded file, including docs and scripts.
- **Annotated** means at least one parameter (including `*args`, `**kwargs` and
  positional-only parameters) or the return carries an annotation.

The exclusion rules are load-bearing. An earlier revision of this review applied the
exclusions to the line counts but not to the pattern searches, and reported 116 `eval`
calls in a 295-line project because it was scanning a vendored Playwright bundle. Any
metric here that looks implausible for a codebase's size should be checked against that
class of error first.

The 2026-09-30 revision found and fixed five defects in how the earlier tables were
produced, so some old numbers do not compare directly with the new ones. Details are in
the [changelog](CHANGELOG.md):

- ripgrep gives the **last** matching glob precedence, and the extension includes came
  after the excludes, so `*.hpp` re-included `json.hpp`. Camoufox's production count
  included the vendored 24,765-line `json.hpp`; at the 2026-08-14 commit the corrected
  figure is 25,351 lines, not 50,116.
- The `eval`/`exec` search used a lookbehind that ripgrep rejects without `-P`, so it
  returned 0 for every repository. It now runs, but its hits are mostly comments,
  method names and test helpers, so it is not shown as a security column.
- The typing figures ignored annotations on `*args`, `**kwargs` and positional-only
  parameters, which the stated rule includes.
- Largest-file and test-line figures counted one extra line per file.
- Obscura `.unwrap()` and `panic!` counts included inline Rust test modules. At the
  2026-08-14 commit the non-test figures are 102 matching lines and 1 `panic!`, not
  2,326 and 21; at 2026-09-30 they are 91 and 1, and at 2026-10-13, 95 and 1.

---

### Commits reviewed

Source trees as of 2026-10-13 (`git log -1` in the sandbox):

| Tool | Repo | Commit | Date |
|------|------|--------|------|
| Camoufox | `camoufox` | `4559d01` | 2026-10-13 |
| Patchright | `patchright` | `ba8bd9b` | 2026-10-11 |
| Patchright | `patchright-python` | `c4064f5` | 2026-09-20 |
| SeleniumBase | `SeleniumBase` | `be6514f` | 2026-10-12 |
| Botasaurus | `botasaurus` | `6c9260d` | 2026-07-26 |
| Botasaurus | `botasaurus-driver` | `db1d291` | 2026-07-30 |
| XDriver | `XDriver` | `b610852` | 2025-09-10 |
| CloakBrowser | `CloakBrowser` | `485f678` | 2026-10-13 |
| Scrapling | `Scrapling` | `7a68493` | 2026-10-11 |
| Obscura | `obscura` | `8edfe48` | 2026-10-12 |
| invisible_playwright | `invisible_playwright` | `91ea73b` | 2026-10-13 |
| invisible_playwright | `invisible_core` | `20da2af` | 2026-10-13 |
| Clearcote | `clearcote-browser` | `fb3e7bb` | 2026-10-12 |

---

## Limits of this review

- **Static only.** Nothing was built, installed, or executed. Runtime behaviour, actual
  test pass rates, and performance are out of scope.
- **Counts are proxies, not verdicts.** `except Exception` is sometimes correct; `print`
  is output in a CLI and residue in a library. Every count in this document should be
  read with its location, which is why the findings section quotes file and line.
- **Closed components are unreviewable.** CloakBrowser's binary, XDriver's bundle and
  Clearcote's licensed builds cannot be assessed from source at all; their rows measure
  the public code only.
- **Generated code inflates some measures.** `botasaurus-driver`'s annotation coverage
  and Obscura's line count both include machine-generated files.
- **No dependency-vulnerability scan** was run, and no review of transitive dependencies.
  That is a worthwhile addition and is not present here.
- **Single reviewer, single pass.** No second opinion, and shallow clones (depth 50)
  limit history-based analysis.
