# Code Review

Engineering assessment of the ten tools' codebases: structure, typing, test coverage, error
handling, dependency hygiene, and security-relevant patterns.

This page answers questions the [comparison](README.md) does not: *can I read this,
modify it, debug it at 3am, and ship it in production?* Detection capability and code
quality are independent properties — the tool with the most stealth features is not the
one with the most maintainable code.

**Verified 2026-11-20** against the commits listed under
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

`cloakbrowser/config.py:139-161` — `--no-sandbox` is hardcoded into the base argument
list (`:148-151`) returned by `get_default_stealth_args()`:

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
carry the same default (`js/src/config.ts:194`, `dotnet/src/CloakBrowser/Config.cs:185`),
and `bin/cloakserve:367-373` builds its arguments from the same list with no opt-out.
The argument merge in `build_args()` (`browser.py:1548-1569`) deduplicates by flag key and lets caller
`args` override defaults, but it only adds and overrides — **it cannot remove a flag**.
The sole opt-out is `stealth_args=False` (`browser.py:1550-1552`; a parameter of `launch()` at `:512` and of `build_launch_options()` at `:381`), which skips the whole list,
including `--fingerprint=<seed>` and the platform flags. The project README shows those
being re-added by hand (`launch(stealth_args=False, args=["--fingerprint=42069",
"--fingerprint-platform=windows"])`, `README.md:780-783`), so spoofing without the
wrapper's `--no-sandbox` is possible. It is not the default, and the README does not
present it as a sandbox setting.

Playwright itself adds `--no-sandbox` whenever `chromiumSandbox` is not `true`
(`playwright-core/src/server/chromium/chromium.ts`, as carried in Patchright's
`patchright.patch`), so every Playwright-driven Chromium in this comparison runs without
the sandbox unless the caller passes `chromium_sandbox=True`. What is specific to
CloakBrowser is that its wrapper adds the flag itself, so that switch has no effect
under its default arguments.

The README does not mention `--no-sandbox` or justify it; the CHANGELOG mentions the
flag (`CHANGELOG.md:553`) and, at `:216`, the sandbox being disabled when running as
root. All of the above was re-read at `fa3716e` (wrapper 0.7.3); the 0.7.0 licence-key
requirement and the 0.6.3 humanize retune did not touch this default.

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
without it. Neither is in the default native launch path. **The Docker route is now the default only on Intel Macs:** since SDK 0.68.4 an Apple
Silicon Mac runs the open native macOS build (Chromium 150, no key needed), and only an
Intel Mac starts the Clearcote Docker image by default (`sdk/python/clearcote/_docker.py:1-15`).
The image runs a sandbox probe and falls back to `--no-sandbox`, with a log line saying
why, when the probe fails (`docker/sandbox_check.py`, `docker/serve.py:705-718`). The probe
passes only when the container is started with the shipped seccomp profile, and the SDKs
pass that profile only on an x86_64 Docker daemon (`sdk/node/src/docker.ts:36-44`,
`:757-767`; Python `_docker.py:41-43`, `:893-899`). A Docker that refuses the profile, and
an explicit `docker=True` on Apple Silicon (emulated), still run the browser with
`--no-sandbox`. See footnote ⁵ under the security metrics.

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
  (229 `…OrThrow(` calls across `driver_patches/`: 38 in `crNetworkManagerPatch.ts`,
  31 in `crPagePatch.ts`, 28 in `framesPatch.ts`, at `521ad98`). If Playwright moves a symbol, the build breaks at patch
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
| Production code | 102,829 lines |
| Largest file | `seleniumbase/fixtures/base_case.py` — **17,724 lines; `BaseCase` has 579 methods** |
| Functions with any type annotation | **3.4%** of 3,951 |
| `except Exception` / `except BaseException` | 510 (5.0 per kLOC) |
| `time.sleep` / `asyncio.sleep` calls | 547 |
| `print(` in library code | 1,104 (10.7 per kLOC) |

`BaseCase` at 579 methods in one file is a god object: every capability is reachable
from one class, so IDE navigation, type inference, and reasoning about state are all
degraded. At 3.4% annotation coverage a type checker cannot help you, and 510 broad
`except` handlers mean failures surface as behaviour changes rather than tracebacks. 547
sleep calls indicate timing-based synchronisation, which is the usual source of flaky
automation.

None of this makes the tool ineffective — it is actively maintained, releases frequently
(9 version bumps, 4.56.2 to 4.58.2, between 2026-10-16 and 2026-11-19, per tag dates in
the shallow sandbox clone), and has 116 test files. It does mean **forking or patching it is expensive**, and
debugging a failure deep in the stack will be slower than in a 15k-line codebase.

**Most of the 42 `shell=True` calls are outside the browser-driving path, but not
all of them.** The distribution is unchanged at `11f3610`: 8 are in `seleniumbase/console_scripts/` (`sb_behave_gui.py`,
`sb_recorder.py`, `sb_commander.py`, `sb_caseplans.py` — developer CLI tooling that
builds pytest invocations from local paths), 10 in `utilities/selenium_grid/`, 11 in
`examples/` and 1 in `behave/`. The remaining 12 are in `core/`: `browser_launcher.py`
(10) runs `"<driver path>" --version` and `sbase get chromedriver <version>` while
preparing a launch, and `detect_b_ver.py` (2) probes the installed browser version. Those
interpolate local file paths and version strings, not page content. (An earlier revision
of this review stated that all 42 were in `console_scripts/`; that was already wrong at
the 2026-08-14 commit.)

### 4. Obscura's panic containment is partial and depends on per-connection threads

Obscura is 202,550 production lines, mostly Rust, in ten member crates. With inline
`#[cfg(test)]` modules, `#[test]` functions and `*_tests.rs` sibling test modules stripped,
it contains **103 matching lines of `.unwrap()`**, 1 `panic!`
(`obscura-dom/src/tree_sink.rs:177`) and 32 `unsafe` blocks (95, 1 and 30 at 2026-10-13).
The `unsafe` lines are in `obscura-js/src/runtime.rs` (11),
`obscura-browser/src/idle_deadline.rs` (7), `obscura-cli/src/main.rs` (5),
`obscura-cdp/src/server.rs` (3), the non-member `crates/test-support/allocations.rs` (3),
`obscura-js/src/ops.rs` (2) and `obscura-render/src/style.rs` (1).
Earlier revisions of this review reported 2,326 `.unwrap()`, 21 `panic!` and 11 `unsafe`
blocks. The first two counts included inline unit-test modules (at the 2026-08-14 commit
the non-test figures are 102 and 1), and the per-file counts quoted then (`io.rs` 18,
`domsnapshot.rs` 10, `target.rs` 8) were all inside `#[cfg(test)]` modules.

**Where the non-test unwraps are.** The largest concentration is `obscura-mcp/src/lib.rs`
(22, mostly `serde_json::to_string(&str).unwrap()`, which cannot fail for string inputs),
then `obscura-js/src/ops.rs` (9), 7 each in `obscura-render/src/paint.rs` and
`obscura-browser/src/page.rs`, 6 in `obscura-js/src/cdp_watchdog.rs` and 5 in
`obscura-cli/src/main.rs`. The whole CDP crate (`obscura-cdp`) has 9. Several sites acquire
a `Mutex` or `RwLock` with `.unwrap()` (`obscura-net/src/client.rs:958`, `:969`, `:1381`,
`:1459`; `robots.rs:36-58`; `cdp_watchdog.rs:109`, `:159`, `:181`, `:192`).

**How panics are contained** (Tier A, read in source):

- `Cargo.toml:66-67` sets `[profile.release] panic = "unwind"`; the comment at `:62-65`
  says abort would turn every catchable op panic into a hard crash. `release-dist`
  inherits it.
- `obscura serve` runs each CDP connection on its own OS thread (`obscura-cdp-conn`) with
  its own current-thread Tokio runtime (`obscura-cdp/src/server.rs:876` `run_connection`, thread `:903-904`, runtime `:914`; a
  second thread per connection handles WebSocket I/O, `:870-875`, `:939`). A
  `SlotGuard` drop releases the connection-cap slot "however it exits" (`:888`), and the
  cap is 128 connections (`:51`). A panic on one connection's thread therefore ends that
  connection and its pages, not the other connections. `serve --workers N` adds process
  isolation behind a TCP balancer (`obscura-cli/src/main.rs:864`). Since `f2b9e99`
  (2026-10-04) the balancer reaps a worker that exits and starts a replacement
  (`respawn_worker`, `main.rs:718`; `supervise_worker`, `:783`), and since v0.2.5 workers
  can also be recycled by connection count, age or RSS (`--worker-max-*`, `main.rs:98-117`);
  the README states that a crash still closes the existing sessions on that worker
  (`README.md:473-475`).
- `catch_unwind` recovery sits at the JS-op and URL-op boundaries
  (`obscura-js/src/ops.rs:2590` in `op_dom`, commented "Anti-panic boundary" at `:2584`;
  the URL ops at `:8356`, `:8434`, `:8484`; also `op_initial_frame` at `:7582` and the
  two layout-caret ops at `:10041` and `:10058`), around module evaluation
  (`obscura-js/src/runtime.rs:3397`) and around each render-resource load (`:2589`). The four-file list in earlier revisions was
  wrong: `obscura-cdp/src/util.rs:164` is a test, `obscura-dom/src/serialize.rs:6` is a
  comment (the serialiser was made iterative because a stack overflow cannot be caught),
  and `runtime.rs:201` catches and re-raises.
- A V8 near-heap-limit guard (`runtime.rs:155-173`) and a per-command CDP watchdog
  (`obscura-cdp/src/dispatch.rs:832-865`, `OBSCURA_CDP_COMMAND_TIMEOUT_MS`, default 60 s)
  bound runaway pages. On `main` since `d93b539` (after v0.2.7) a client can also send
  `Runtime.terminateExecution`, answered on the socket thread (`server.rs:2407`).

**Residual risks still present in the source** (not exercised):

- Lock poisoning: the `Mutex` and `RwLock` `.unwrap()` sites above turn one poisoned lock
  into panics in later users. Commit `b3475a5` (2026-09-26) fixed the cookie jar only;
  the lock sites listed above are still present at `58a04dd`.
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
202,550 lines.

### 5. Botasaurus swallows errors more than any other codebase here

38 bare `except:` clauses across the two repos (17 in `botasaurus`, 21 in
`botasaurus-driver`) — the only tools in this set with double-digit bare excepts. A bare
`except:` catches `KeyboardInterrupt` and `SystemExit` as well as errors, so it can make
a process hard to interrupt and hides the cause of failures. The monorepo's commits
since July 2026 (to `3873a56`) touch only its Node packages and `botasaurus-driver` is
unchanged (`db1d291`), so these figures are unchanged.

`botasaurus-driver` also has **zero test files** despite being 50,169 lines and the
component that actually implements the stealth. Much of that line count is generated CDP
bindings (`cdp/network.py` alone is 4,616 lines), which need no tests — but the
hand-written driver logic has none either.

### 6. invisible_playwright's browser makes a GitHub request on every launch, and since engine firefox-64 it cannot be turned off

> [!WARNING]
> The patched Firefox issues an HTTPS GET to GitHub on **every launch**. Since engine
> `firefox-64` (core 64.69.0, 2026-11-14) no pref gates or redirects it, so it cannot be
> disabled from the package. It is described in the wrapper README and the engine README.

The engine is now a patch series; the counter is the folder `platform/launch-counter`. Its
only hook in Mozilla's code is `try { lazy.StealthLaunchCounter.fire(); } catch (e) {}` as
the first statement of `BrowserGlue._beforeUIStartup` (`platform/launch-counter/hooks.patch:17-18`),
which runs at `final-ui-startup`. The module
(`platform/launch-counter/src/browser/components/StealthLaunchCounter.sys.mjs`, 28 lines)
says "It is MANDATORY: no preference gates it and no preference moves it" (`:11-12`) and
fires one `fetch()` to a constant,
`https://github.com/oss-invisible/firefox_antidetect_patch/releases/download/usage-counter/launch.txt`
(`:15-16`), with `method: "GET"`, `credentials: "omit"`, `cache: "no-store"`, errors
swallowed (`:19-26`). No file in the series declares or reads `invisible_firefox.usage_ping.*`
(only stale descriptions in `FEATURE.md:4` and `MANIFEST.json` mention them). The engine's
own test sets both old prefs and asserts the request still goes, once, to the fixed address
(`src/browser/components/tests/unit/test_stealth_launch_counter.js:62-78`). Engine
citations are at tag `firefox-67` (`9110d5d`); the pre-rewrite pref-gated version is
`BrowserGlue.sys.mjs:387-423` at `a3819a7`.

The request itself is benign: no payload, no identifier, no cookies.

**Proxy behaviour (earlier "Tier D, source order suggests direct" withdrawn).** When the
browser runs under the package (`-juggler-pipe`), Juggler registers a proxy channel filter
at `command-line-startup` (`automation/juggler/src/juggler/components/Juggler.js:81-93`),
before the counter fires. Every http(s) channel is held unanswered until
`Browser.setBrowserProxy` or `Browser.setNoBrowserProxy` arrives
(`network/doh/src/juggler/EarlyProxyHold.js:31-50`, `:78-85`;
`automation/juggler/src/juggler/NetworkObserver.js:712-734`), and the core sends one of the
two as its first command (`invisible_core/juggler/connection.py:1545-1551` at `191f0fa`). A
held channel with no browsing context takes the browser proxy
(`automation/juggler/src/juggler/TargetRegistry.js:521-550`). By the source, the counter
therefore leaves through the session proxy when there is one and directly when there is
none; this was read, not run. A binary started without `-juggler-pipe` has no hold.

**Disclosure.** The wrapper README has a "Launch counter" section (`README.md:223-225` at
`d1bfea3`) and the engine README patch an "Anonymous launch counter" section that says "It is
not optional" (`platform/repo/hooks.patch:147-169`). The wrapper README also says the
launcher and server refuse the two old prefs in `extra_prefs`; no code under the wrapper's or
the core's `src/` names `usage_ping`, and the wrapper's test asserts there is no refusal
(`tests/test_the_server_says_nothing_about_the_launch_counter.py:1-6`, `:34-35`). Such prefs
pass through and the engine ignores them.

**Mitigation:** none in the package or through prefs. Rebuild the engine from the series
without `platform/launch-counter`, or block
`github.com/oss-invisible/firefox_antidetect_patch/releases/download/usage-counter/` on the
network.

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
510-count in 103k lines and a 12-count in 17k lines are not comparable.

<details>
<summary><b>Size and test presence</b></summary>


| Repo | Prod LOC | Test files | Test LOC | Largest file |
|------|---------:|-----------:|---------:|--------------|
| `camoufox` | 56,519 | 306 | 50,360 | `browser/additions/gfx/skia/skia/src/opts/SkCpuEstimateTables.h` (3,098, generated) |
| `patchright` | 7,606 | 2 | 0 | `driver_patches/framesPatch.ts` (1,241) |
| `patchright-python` | 1,101 | 0 | 0 | `patch_python_package.py` (843) |
| `SeleniumBase` | 102,829 | 116 | 3,593 | `seleniumbase/fixtures/base_case.py` (17,724) |
| `botasaurus` | 31,493 | 22 | 1,596 | `js/botasaurus-server-js/src/routes-db-logic.ts` (1,864) |
| `botasaurus-driver` | 50,169 | 0 | 0 | `botasaurus_driver/cdp/network.py` (4,616, generated) |
| `XDriver` | 295 | 0 | 0 | `x_driver/activator_script.py` (107) |
| `CloakBrowser` | 33,318 | 100 | 31,594 | `cloakbrowser/browser.py` (1,915) |
| `Scrapling` | 16,661 | 104 | 27,193 | `scrapling/engines/toolbelt/ad_domains.py` (3,537, data) |
| `obscura` | 202,550 | 123 | 26,773 | `crates/obscura-js/src/runtime.rs` (29,707) |
| `invisible_playwright` | 19,387 | 426 | 79,056 | `src/invisible_playwright/_juggler/server.py` (6,426) |
| `invisible_core` | 46,831 | 209 | 48,809 | `src/invisible_core/juggler/keylayouts_windows.py` (11,029, generated) |
| `clearcote-browser` | 102,810 | 389 | 100,657 | `sdk/python/clearcote/_humanize.py` (4,315) |

Both invisible_playwright packages grew between 2026-10-13 and 2026-11-20 (wrapper 13.6k
to 19.4k lines, core 26.5k to 46.8k, of which 11.0k is the generated
`keylayouts_windows.py`); the wrapper's Juggler server alone went from 4,455 to 6,426
lines. The core's bundled `injected.js` (at `src/invisible_core/juggler/injected.js` since
38.34.0) stays excluded.

</details>

<details>
<summary><b>Typing and documentation (Python only)</b></summary>


Measured by AST over non-test Python: a function counts as annotated if any parameter or
the return carries an annotation.

| Repo | Functions | Annotated | Docstrings |
|------|----------:|----------:|-----------:|
| `CloakBrowser` | 464 | 96.1% | 50.6% |
| `invisible_core` | 1,113 | 94.2% | 64.4% |
| `Scrapling` | 593 | 86.8% | 59.5% |
| `invisible_playwright` | 884 | 85.1% | 42.8% |
| `botasaurus-driver` | 2,742 | 81.2%¹ | 27.5% |
| `camoufox` | 967 | 77.1% | 59.0% |
| `patchright-python` | 7 | 42.9% | 0.0% |
| `obscura` (Python parts) | 80 | 25.0% | 40.0% |
| `clearcote-browser` | 2,190 | 18.9% | 55.4% |
| `botasaurus` | 1,012 | 14.0% | 14.9% |
| `XDriver` | 12 | 8.3% | 33.3% |
| `SeleniumBase` | 3,951 | 3.4% | 21.0% |

¹ Inflated by generated CDP bindings, which are uniformly annotated. Hand-written driver
code is less consistent.

</details>

<details>
<summary><b>Error handling and code smells</b></summary>


| Repo | bare `except:` | broad `except` | per kLOC | `print(` | per kLOC | sleep calls | TODO/FIXME |
|------|---------------:|---------------:|---------:|---------:|---------:|------------:|-----------:|
| `camoufox` | 0 | 18 | 0.3 | 178 | 3.1 | 8 | 5 |
| `patchright` | 0 | 0 | 0.0 | 0 | 0.0 | 0 | 1 |
| `patchright-python` | 2 | 2 | 1.8 | 0 | 0.0 | 0 | 0 |
| `SeleniumBase` | 0 | 510 | 5.0 | 1,104 | 10.7 | 547 | 0 |
| `botasaurus` | 17 | 5 | 0.2 | 151 | 4.8 | 5 | 4 |
| `botasaurus-driver` | 21 | 3 | 0.1 | 56 | 1.1 | 22 | 11 |
| `XDriver` | 0 | 0 | 0.0 | 0 | 0.0 | 0 | 0 |
| `CloakBrowser` | 1 | 25 | 0.8 | 100 | 3.0 | 10 | 0 |
| `Scrapling` | 0 | 12 | 0.7 | 34 | 2.0² | 0 | 0 |
| `obscura` | 0 | 1 | 0.0 | 17 | 0.1 | 0 | 1 |
| `invisible_playwright` | 1 | 81 | 4.2 | 165 | 8.5 | 13 | 0 |
| `invisible_core` | 0 | 84 | 1.8 | 355 | 7.6 | 18 | 0 |
| `clearcote-browser` | 0 | 271 | 2.6 | 165 | 1.6 | 253 | 0 |

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
| `SeleniumBase` | 42³ | 1 | 0 | 10 | – | – |
| `botasaurus` | 21³ | 0 | 0 | 4 | – | – |
| `botasaurus-driver` | 0 | 0 | 0 | 2 | – | – |
| `XDriver` | 0 | 0 | 0 | 0 | – | – |
| `CloakBrowser` | 0 | 0 | 0 | 3⁴ | – | – |
| `Scrapling` | 0 | 1 | 0 | 0 | – | – |
| `obscura` | 0 | 0 | 0 | 1 | 32 | 103 |
| `invisible_playwright` | 0 | 0 | 0 | 0 | – | – |
| `invisible_core` | 0 | 0 | 0 | 0 | – | – |
| `clearcote-browser` | 0 | 0 | 0 | 67⁵ | – | – |

³ Botasaurus: all in CLI and server tooling (`bota/`, `botasaurus_server/`). SeleniumBase: 12
are in `core/` launch helpers (driver `--version` probes and driver installs), the rest in
CLI, grid and example code; see [finding 3](#3-seleniumbases-size-and-typing-make-it-hard-to-modify-safely).
⁴ The same unconditional default in the Python, Node and .NET wrappers
(`cloakbrowser/config.py:149`, `js/src/config.ts:194`, `dotnet/src/CloakBrowser/Config.cs:185`). See [finding 1](#1-cloakbrowser-disables-the-chromium-sandbox-by-default-and-the-playwright-sandbox-switch-cannot-restore-it).
⁵ Conditional on a native launch. The SDKs add it when `serve()` runs as root on Linux
(`sdk/python/clearcote/_launchopts.py:1216-1221`, used at `_serve.py:253-256`;
`sdk/node/src/index.ts:1594-1596`, call site `:1744`;
`sdk/dotnet/src/Clearcote/LaunchOpts.cs:1202-1205`) or when the opt-in canvas bridge is
enabled (`sdk/python/clearcote/_fingerprint.py:635-636`, `sdk/node/src/fingerprint.ts:756`,
`sdk/dotnet/src/Clearcote/Fingerprint.cs:606`). The Docker image, which is the default
route on an Intel Mac, runs `--no-sandbox` unless the container gets the shipped seccomp profile,
which the SDKs pass only on an x86_64 Docker (`sdk/node/src/docker.ts:757-767`); see
[finding 1](#1-cloakbrowser-disables-the-chromium-sandbox-by-default-and-the-playwright-sandbox-switch-cannot-restore-it).
Of the 67 hits in source, 25 are in that Docker code (`docker/`, `_docker.py`,
`docker.ts`, `DockerLaunch.cs`), 36 in the SDKs' launch, fingerprint and download code,
and 6 in smoke scripts and tooling. (The 84 reported at 2026-10-13 also counted
documentation; see [How the numbers were produced](#how-the-numbers-were-produced).)

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
| `CloakBrowser` | 2 | – | – | yes | – | – | yes |
| `Scrapling` | 5 | yes | yes | – | yes | – | yes |
| `obscura` | 4 | – | – | – | yes | yes | – |
| `invisible_playwright` | 12 | yes | – | – | yes | yes | yes |
| `invisible_core` | 4 | yes | – | – | – | – | – |
| `clearcote-browser` | 10 | – | – | – | yes | yes | – |

Only Scrapling runs pre-commit; only CloakBrowser configures Dependabot. Notable CI:
Patchright's `check_patch_impact.yml` (upstream drift detection), Clearcote's
`patch-integrity.yml` and `stealth-coherence` gate, Scrapling's `code-quality.yml`,
SeleniumBase's nightly matrix across macOS/Ubuntu/Windows.

---

</details>

## Per-tool assessment

**Camoufox** — 56.5k production lines of Python, TypeScript, JS and the C++ additions
(the 65 top-level `.patch` files under `browser/patches/`, plus 4 in its subdirectories,
are not in that count). The rise from 42.9k at 2026-10-13 is mostly the CPU-vendor
emulation: `cpu-vendor-estimates` placed its generated Skia/Opus code in
`browser/additions/`, and the largest production file is now the generated
`browser/additions/gfx/skia/skia/src/opts/SkCpuEstimateTables.h` (3,098 lines). 306 test
files and 50.4k test lines (179 and 31.7k at 2026-10-13); Playwright's own suite is still
not carried in-tree (`make tests` in `browser/Makefile` runs it through
`ci/run_playwright.py`, which applies `ci/skiplist.yml`). 77.1% annotation and 59.0%
docstring coverage on the Python side, 0 bare excepts and 18 broad ones (0.3/kLOC). The
TypeScript launcher (`typescript/`) and the `ci/` release pipeline sit beside the Python
package. The C++ patch stack is the part you would have to modify, and it requires a full
Firefox build to validate; `browser/Makefile` and `browser/upstream.sh` automate the
fetch-and-patch cycle, and fonts are an 843 MB pinned release asset (`docs/FONTS.md`)
unpacked by `make fonts-extract`.

**Patchright** — 7,606 lines of TypeScript, mostly AST surgery (`driver_patches/` is
5,029 lines in 36 files: 34 patch modules plus `index.ts` and `utils.ts`), plus 1,101 lines of Python packaging code in
`patchright-python`. The metric tables count 2 test files; `utils/custom_tests/` holds 3
custom specs and `utils/` a detection smoke test, and each release is gated in CI on
Playwright's own `chromium-page` and `chromium-library` suites run against the patched
driver (`patchright_tests.yml:101`, `:108`), together with fail-loud accessors. The code
is per-file modular.

**SeleniumBase** — see [finding 3](#3-seleniumbases-size-and-typing-make-it-hard-to-modify-safely).
103k production lines, 3.4% annotation coverage and a single 17.7k-line class. Release
cadence: 9 version bumps (4.56.2 to 4.58.2) between 2026-10-16 and 2026-11-19, and a
nightly three-OS CI matrix (`python-nightly-{mac,ubuntu,windows}.yml`).

**Botasaurus** — split across a framework monorepo and a driver repo with different
standards. 38 bare excepts; the driver has no tests; PyPI is ahead of the published
source. The Bézier input implementation (`human_curve_generator.py`) is the most
readable part and is self-contained enough to lift out.

**XDriver** — 295 lines (262 in `x_driver/*.py` plus a 33-line `setup.py`), zero tests, zero smells (trivially — there is almost no code).
The engineering content is in a prebuilt bundle nobody in this repository built. Nothing
to review, and nothing to maintain.

**CloakBrowser** — 33.3k lines of wrapper across Python, TypeScript, and C#. 100 test
files and 31.6k test lines. 96.1% annotation coverage and 25 broad excepts (0.8/kLOC),
against 81.0% and 95 (2.7/kLOC) at 2026-09-30, after the v0.6.0 rewrite of the humanize
layer into one engine for every action (`d4924d9`, clean-up `15cb83e`). The engine is
closed, so half the system cannot be reviewed from source. Ships Dependabot; the manual
release-archive attestation workflow (`attest-release.yml`) was deleted in `91effe4`
(2026-11-07), although the README still documents `gh attestation verify` for binary
archives, and `publish.yml` still signs and attests the Docker image. Since 0.5.11 the
wrapper unpacks signature-verified archives without per-entry screening
(`download.py:891-907` at 0.7.3). Since 0.7.0 every launch needs a licence key (free by
email, or paid); a key that cannot be validated or a failed GeoIP lookup aborts the
launch. See
[finding 1](#1-cloakbrowser-disables-the-chromium-sandbox-by-default-and-the-playwright-sandbox-switch-cannot-restore-it).

**Scrapling** — 86.8% annotation coverage, 59.5% docstrings, 0 bare excepts, 12 broad
excepts (0.7/kLOC) across 16.7k lines, 104 test files (0.5 added suites for the MCP
browser tools, network recording, remote sessions, Shadow DOM and the Cloudflare
solver's readiness and polling), and the only pre-commit configuration. 0.5 removed the
plain-Playwright browser tier (`_controllers.py`, `fetchers/chrome.py`) and moved the MCP
server into the `scrapling/core/ai/` package.
CloakBrowser (96.1%) and `invisible_core` (94.2%) have higher annotation coverage, with
broad-except densities of 0.8 and 1.8 per kLOC.
Scrapling's largest file is a data table (`ad_domains.py`, 3,537 lines), not logic.

**Obscura** — 202.6k production lines, mostly Rust, in ten member crates (plus the
non-member `crates/test-support`), the largest codebase here by line count. The largest
file is `obscura-js/src/runtime.rs` (29,707 lines); `obscura-render/src/dom.rs` is 22,832,
and `obscura-js` also carries a 20,622-line `js/bootstrap.js` (plus a 790-line
`indexed_db.js` spliced into it at build time). Smell counts are low for
its size (1 broad catch, 1 TODO, 17 prints). The error strategy is in
[finding 4](#4-obscuras-panic-containment-is-partial-and-depends-on-per-connection-threads).

**Clearcote** — 103k lines of SDK, tooling and script code (Python, TypeScript, C#), up
from 63k at 2026-10-13, as SDKs 0.49.0 to 0.70.1 added persona-service, humanize and launch
code; the largest file is `sdk/python/clearcote/_humanize.py` (4,315). Alongside are 62
readable patch files that are not in that count (37 at 2026-10-13), 389 test files and 10
CI workflows including a patch-integrity check and a stealth-coherence regression gate.
271 broad excepts (2.6/kLOC) is the third-highest density in the metrics table, after
SeleniumBase (5.0) and `invisible_playwright` (4.2). The stray backup-file diffs noted at
2026-10-13 are gone from `patches/`. One contributor, so review depth and continuity
depend on one person.

**invisible_playwright** — two packages. The wrapper is 19.4k first-party lines, counted
without the vendored Playwright-Python fork (`_pw/`, about 62,000 lines); its largest file is
the in-process Juggler server (`_juggler/server.py`, 6,426 lines), which since 0.48.0 can
also serve stock Playwright clients over a WebSocket (`_juggler/remote.py`). The core is
46.8k first-party lines without `injected.js`, 11.0k of them the generated Windows keyboard
tables. Together: 426 and 209 test files, 85.1% and 94.2% annotation coverage, 42.8% and
64.4% docstrings, 81 and 84 broad excepts (4.2 and 1.8 per kLOC), 165 and 355 `print(`
calls, 13 and 18 sleep calls, 12 and 4 CI workflows. Neither package contains C/C++
sources; the engine is a separate patch series (`firefox_antidetect_patch`, 79 feature
folders against Firefox 159.0, read from a full clone of tag `firefox-67`). `playwright` is
not a runtime dependency. The `eval`/`exec` pattern search finds nothing in either
package's source; the excluded `injected.js` bundle has 5 lines matching `eval(`. See
[finding 6](#6-invisible_playwrights-browser-makes-a-github-request-on-every-launch-and-since-engine-firefox-64-it-cannot-be-turned-off).

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
  run over the same source extensions plus shell scripts (`sh`) and `Dockerfile*`. Until
  2026-11-20 they ran over every non-excluded file, Markdown included; Scrapling's
  translated documentation then pushed its `print(` count from 192 to 891 without a
  line of code changing, and CHANGELOG lines counted as `--no-sandbox` hits.
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
  2,326 and 21; at 2026-09-30 they are 91 and 1, at 2026-10-13 95 and 1, and at 2026-11-20
  103 and 1. On 2026-11-20 the script also began treating `*_tests.rs` files as tests: Obscura
  declares five sibling test modules that way (`#[cfg(test)] mod partial_document_tests;`),
  and counting them as production would have added 50 `.unwrap()` lines and 4 `panic!`.

---

### Commits reviewed

Source trees as of 2026-11-20 (`git log -1` in the sandbox):

| Tool | Repo | Commit | Date |
|------|------|--------|------|
| Camoufox | `camoufox` | `4c909d6` | 2026-11-18 |
| Patchright | `patchright` | `521ad98` | 2026-11-12 |
| Patchright | `patchright-python` | `8727f3b` | 2026-11-10 |
| SeleniumBase | `SeleniumBase` | `11f3610` | 2026-11-19 |
| Botasaurus | `botasaurus` | `3873a56` | 2026-11-13 |
| Botasaurus | `botasaurus-driver` | `db1d291` | 2026-07-30 |
| XDriver | `XDriver` | `b610852` | 2025-09-10 |
| CloakBrowser | `CloakBrowser` | `fa3716e` | 2026-11-20 |
| Scrapling | `Scrapling` | `2998c9e` | 2026-11-17 |
| Obscura | `obscura` | `58a04dd` | 2026-11-20 |
| invisible_playwright | `invisible_playwright` | `d1bfea3` | 2026-11-20 |
| invisible_playwright | `invisible_core` | `191f0fa` | 2026-11-20 |
| invisible_playwright | `firefox_antidetect_patch` | `9110d5d` (tag `firefox-67`) | 2026-11-19 |
| Clearcote | `clearcote-browser` | `389653c` | 2026-11-19 |

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
