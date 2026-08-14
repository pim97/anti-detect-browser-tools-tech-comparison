# Code Review

Engineering assessment of the nine codebases: structure, typing, test coverage, error
handling, dependency hygiene, and security-relevant patterns.

This page answers questions the [comparison](README.md) does not: *can I read this,
modify it, debug it at 3am, and ship it in production?* Detection capability and code
quality are independent properties — the tool with the most stealth features is not the
one with the most maintainable code.

**Verified 2026-08-14** against the commits in [STATUS.md](STATUS.md). Metrics are
reproducible: `scripts/codemetrics.py`, run inside the sandbox
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

### 1. CloakBrowser disables the Chromium sandbox for every user, unconditionally

`cloakbrowser/config.py:54-66` — `--no-sandbox` is hardcoded into the base argument
list returned by `get_default_stealth_args()`:

```python
def get_default_stealth_args() -> list[str]:
    seed = random.randint(10000, 99999)
    system = platform.system()

    base = [
        "--no-sandbox",
        f"--fingerprint={seed}",
    ]
```

The string appears exactly once in the Python package. The argument merge in
`browser.py:1395-1425` deduplicates by flag key and lets caller `args` override
defaults, but it only adds and overrides — **it cannot remove a flag**. The sole
opt-out is `stealth_args=False` (`browser.py:323`), which skips the whole list and
therefore also drops `--fingerprint=<seed>`, i.e. the tool's primary function. There is
no supported configuration with fingerprint spoofing *and* the sandbox enabled.

The README does not mention `--no-sandbox` or justify it.

**Why this matters more here than elsewhere:** the Chromium sandbox is the boundary that
contains a compromised renderer. Disabling it while processing untrusted web content
removes that boundary. CloakBrowser is also the only tool of the nine whose engine is a
**closed binary** — so a user is running unauditable native code, with the OS-level
sandbox off, against hostile input. Those two properties are individually defensible and
jointly significant.

For contrast, Clearcote also requires `--no-sandbox`, but only for the optional
canvas-bridge feature, and documents the reason (`docs/CANVAS-BRIDGE.md:140`: the
renderer opens the bridge socket, which the sandbox blocks). Its 30 occurrences are in
tests and docs, not in the SDK's default launch path.

**Mitigation if you use it:** run it in a container with a restricted seccomp profile
and dropped capabilities, treat the browser process as untrusted, and do not run it on a
host holding credentials.

### 2. Patchright's fragile-by-design approach is engineered correctly

Rewriting another project's source with an AST tool is inherently brittle. Patchright
handles that better than any other patching tool here, and it is worth stating because
the pattern generalises:

- **It fails loudly.** The patch modules use ts-morph's throwing accessors
  consistently — `getClassOrThrow`, `getMethodOrThrow`, `getImportDeclarationOrThrow`
  (47 occurrences in `crPagePatch.ts`, 40 in `framesPatch.ts`, 36 in
  `crNetworkManagerPatch.ts`). If Playwright moves a symbol, the build breaks at patch
  time rather than producing a silently unpatched driver that looks fine and leaks.
- **It detects upstream drift in CI.** `.github/workflows/check_patch_impact.yml` diffs
  two Playwright versions and can open a GitHub issue when breaking changes are found.
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
| Production Python | 99,701 lines |
| Largest file | `seleniumbase/fixtures/base_case.py` — **17,670 lines, 579 methods, 2 classes** |
| Functions with any type annotation | **2.7%** (106 of 3,902) |
| `except Exception` / `except BaseException` | 506 (5.1 per kLOC) |
| `time.sleep` / `asyncio.sleep` calls | 548 |
| `print(` in library code | 1,122 (11.3 per kLOC) |

`BaseCase` at 579 methods in one file is a god object: every capability is reachable
from one class, so IDE navigation, type inference, and reasoning about state are all
degraded. At 2.7% annotation coverage a type checker cannot help you, and 506 broad
`except` handlers mean failures surface as behaviour changes rather than tracebacks. 548
sleep calls indicate timing-based synchronisation, which is the usual source of flaky
automation.

None of this makes the tool ineffective — it is actively maintained, releases near-daily,
and has 117 test files. It does mean **forking or patching it is expensive**, and
debugging a failure deep in the stack will be slower than in a 15k-line codebase.

**The 42 `shell=True` calls are less alarming than the raw count suggests.** All of them
are in `seleniumbase/console_scripts/` (`sb_commander.py`, `sb_recorder.py`,
`sb_caseplans.py`, `sb_behave_gui.py`) — developer CLI tooling that builds pytest
invocations from local paths. None are in the library's browser-driving path. The
exposure is a developer running the GUI tools over an untrusted test directory, not a
scraper at runtime.

### 4. Obscura's error strategy is panic-on-failure in a long-running server

142,368 lines of production Rust containing **2,326 `.unwrap()` calls**, 21 `panic!`, and
11 `unsafe` blocks. `catch_unwind` appears in only four files (`obscura-cdp/src/util.rs`,
`obscura-dom/src/serialize.rs`, `obscura-js/src/ops.rs`, `obscura-js/src/runtime.rs`), so
panic recovery exists at the JS-op and DOM-serialisation boundaries but not broadly.

Unwrap density is highest where it matters most — the CDP domain handlers that service
a long-lived server: `io.rs` (18), `domsnapshot.rs` (10), `target.rs` (8).

In a CLI that fetches one page, a panic is an exit code. In `obscura serve` handling
concurrent sessions, an unwrap on malformed input from one page can take down work that
does not belong to it. Bounded by the catch_unwind boundaries where they exist. If you
deploy Obscura as a long-running service, load-test it against hostile and malformed
HTML before trusting it.

Offsetting this: Obscura has the cleanest smell profile of the nine — 1 broad catch, 1
TODO, 16 prints across 142k lines.

### 5. Botasaurus swallows errors more than any other codebase here

38 bare `except:` clauses across the two repos (17 in `botasaurus`, 21 in
`botasaurus-driver`) — the only tools in this set with double-digit bare excepts. A bare
`except:` catches `KeyboardInterrupt` and `SystemExit` as well as errors, so it can make
a process hard to interrupt and hides the cause of failures.

`botasaurus-driver` also has **zero test files** despite being 50,169 lines and the
component that actually implements the stealth. Much of that line count is generated CDP
bindings (`cdp/network.py` alone is 4,617 lines), which need no tests — but the
hand-written driver logic has none either.

### 6. Registry artifacts do not always correspond to published source

`botasaurus-driver` publishes **4.0.101** to PyPI (2026-08-10) while the repository's
`setup.py` reads **4.0.92**. The installed artifact does not correspond to any tagged
commit in the public repository, so source review of the GitHub tree does not tell you
what `pip install botasaurus-driver` puts on disk. For a stealth driver — where the
threat model includes supply chain — that gap matters.

---

## Metrics

Production code only. Test files, vendored trees, generated bundles, and minified assets
excluded. Raw counts are not quality scores; the per-kLOC columns exist because a
506-count in 100k lines and a 7-count in 16k lines are not comparable.

### Size and test presence

| Repo | Prod LOC | Test files | Test LOC | Largest file |
|------|---------:|-----------:|---------:|--------------|
| `camoufox` | 50,116 | 208 | 29,418 | — (largest is vendored `json.hpp`) |
| `patchright` | 6,833 | 2 | 0 | `driver_patches/framesPatch.ts` (1,287) |
| `patchright-python` | 1,057 | 0 | 0 | `patch_python_package.py` (809) |
| `SeleniumBase` | 99,701 | 117 | 3,714 | `fixtures/base_case.py` (**17,670**) |
| `botasaurus` | 31,005 | 13 | 75 | `js/…/routes-db-logic` (1,836) |
| `botasaurus-driver` | 50,169 | **0** | 0 | `cdp/network.py` (4,617, generated) |
| `XDriver` | 295 | **0** | 0 | `x_driver/activator_script.py` (108) |
| `CloakBrowser` | 32,574 | 78 | 28,388 | `cloakbrowser/human/__init__.py` (3,128) |
| `Scrapling` | 15,768 | 59 | 12,389 | `engines/toolbelt/ad_domains.py` (3,538, data) |
| `obscura` | 142,368 | 34 | 11,137 | `crates/obscura-render/src/dom.rs` (20,284) |
| `clearcote-browser` | 23,136 | 65 | 8,401 | `sdk/python/clearcote/_humanize.py` (991) |

### Typing and documentation (Python only)

Measured by AST over non-test Python: a function counts as annotated if any parameter or
the return carries an annotation.

| Repo | Functions | Annotated | Docstrings |
|------|----------:|----------:|-----------:|
| `Scrapling` | 538 | **83.5%** | **59.1%** |
| `botasaurus-driver` | 2,742 | 81.1%¹ | 27.5% |
| `CloakBrowser` | 518 | 80.5% | 40.7% |
| `camoufox` | 451 | 59.0% | 55.7% |
| `patchright-python` | 7 | 42.9% | 0% |
| `clearcote-browser` | 540 | 31.7% | 45.9% |
| `obscura` (Python parts) | 80 | 27.5% | 38.8% |
| `botasaurus` | 1,006 | 13.5% | 14.4% |
| `XDriver` | 12 | 8.3% | 33.3% |
| `SeleniumBase` | 3,902 | **2.7%** | 20.5% |

¹ Inflated by generated CDP bindings, which are uniformly annotated. Hand-written driver
code is less consistent.

### Error handling and code smells

| Repo | bare `except:` | broad `except` | per kLOC | `print(` | per kLOC | sleep calls | TODO/FIXME |
|------|---------------:|---------------:|---------:|---------:|---------:|------------:|-----------:|
| `camoufox` | 1 | 27 | 0.5 | 210 | 4.2 | 4 | 8 |
| `patchright` | 0 | 0 | 0.0 | 0 | 0.0 | 0 | 2 |
| `SeleniumBase` | 0 | **506** | **5.1** | **1,122** | **11.3** | **548** | 0 |
| `botasaurus` | **17** | 5 | 0.2 | 191 | 6.2 | 5 | 15 |
| `botasaurus-driver` | **21** | 3 | 0.1 | 59 | 1.2 | 22 | 11 |
| `XDriver` | 0 | 0 | 0.0 | 0 | 0.0 | 0 | 0 |
| `CloakBrowser` | 0 | 110 | 3.4 | 105 | 3.2 | 13 | 3 |
| `Scrapling` | 0 | 7 | 0.4 | 192 | 12.2² | 0 | 0 |
| `obscura` | 0 | **1** | **0.0** | 16 | 0.1 | 0 | 1 |
| `clearcote-browser` | 0 | 127 | 5.5 | 108 | 4.7 | 45 | 0 |

² Scrapling ships a CLI and an MCP server, where `print` is output rather than debug
residue. Counts alone do not distinguish the two.

### Security-relevant patterns (production code)

| Repo | `shell=True` | `pickle.load` | `verify=False` | `--no-sandbox` | `unsafe` | `.unwrap()` |
|------|-------------:|--------------:|---------------:|---------------:|---------:|------------:|
| `SeleniumBase` | **42**³ | 1 | 3 | 11 | – | – |
| `botasaurus` | 21³ | 0 | 0 | 4 | – | – |
| `CloakBrowser` | 0 | 0 | 0 | **4**⁴ | – | – |
| `clearcote-browser` | 1 | 0 | 1 | 30⁵ | – | – |
| `Scrapling` | 0 | 1 | 0 | 0 | – | – |
| `camoufox` | 0 | 0 | 1 | 0 | – | – |
| `obscura` | 0 | 0 | 0 | 1 | **11** | **2,326** |
| `patchright` | 0 | 0 | 0 | 0 | – | – |
| `XDriver` | 0 | 0 | 0 | 0 | – | – |

³ All in CLI/developer tooling, not the browser-driving path.
⁴ One of these is the unconditional default — see [finding 1](#1-cloakbrowser-disables-the-chromium-sandbox-for-every-user-unconditionally).
⁵ Tests and docs; the canvas bridge requires it and documents why.

### Project hygiene

| Repo | CI workflows | `py.typed` | pre-commit | Dependabot | CONTRIBUTING | SECURITY.md | CHANGELOG |
|------|-------------:|:----------:|:----------:|:----------:|:------------:|:-----------:|:---------:|
| `camoufox` | 2 | yes | – | – | yes | – | – |
| `patchright` | 6 | – | – | – | – | – | – |
| `SeleniumBase` | 5 | – | – | – | yes | yes | yes |
| `botasaurus` | 14 | – | – | – | yes | yes | – |
| `botasaurus-driver` | **0** | yes | – | – | – | – | – |
| `XDriver` | 1 | – | – | – | – | – | – |
| `CloakBrowser` | 3 | – | – | **yes** | – | – | yes |
| `Scrapling` | 4 | yes | **yes** | – | yes | – | – |
| `obscura` | 3 | – | – | – | yes | yes | – |
| `clearcote-browser` | 8 | – | – | – | yes | yes | – |

Only Scrapling runs pre-commit; only CloakBrowser configures Dependabot. Notable CI:
Patchright's `check_patch_impact.yml` (upstream drift detection), Clearcote's
`patch-integrity.yml` and `stealth-coherence` gate, Scrapling's `code-quality.yml`,
SeleniumBase's nightly matrix across macOS/Ubuntu/Windows.

---

## Per-tool assessment

**Camoufox** — 50k production lines split across C++ patches, Python, and JS. 208 test
files and 29k test lines, the largest test suite here. 59% annotation and 56% docstring
coverage on the Python side, 1 bare except across the tree. The C++ patch stack is the
part you would have to modify, and it requires a full Firefox build to validate; the
Makefile and `upstream.sh` automate the fetch-and-patch cycle.

**Patchright** — 6,833 lines of TypeScript doing AST surgery. No traditional test suite
(2 test files), which is a real gap, but partly compensated by fail-loud accessors and
CI that validates patches against real Playwright releases. The code is per-file modular
and readable. Smallest, most focused codebase that does something non-trivial.

**SeleniumBase** — see [finding 3](#3-seleniumbases-size-and-typing-make-it-hard-to-modify-safely).
Broadest feature set, weakest static-checkability, heaviest maintenance burden if you
fork it. Best-in-set release cadence and a nightly three-OS CI matrix.

**Botasaurus** — split across a framework monorepo and a driver repo with different
standards. 38 bare excepts; the driver has no tests; PyPI is ahead of the published
source. The Bézier input implementation (`human_curve_generator.py`) is the most
readable part and is self-contained enough to lift out.

**XDriver** — 295 lines, zero tests, zero smells (trivially — there is almost no code).
The engineering content is in a prebuilt bundle nobody in this repository built. Nothing
to review, and nothing to maintain.

**CloakBrowser** — 32.5k lines of wrapper across Python, TypeScript, and C#. 78 test
files and 28k test lines. 80.5% annotation coverage. Well-organised wrapper; the engine is
closed, so half the system is unreviewable. Ships Dependabot and a release-attestation
workflow. See [finding 1](#1-cloakbrowser-disables-the-chromium-sandbox-for-every-user-unconditionally).

**Scrapling** — the cleanest Python codebase in the set: 83.5% annotation coverage, 59.1%
docstrings, 0 bare excepts, 7 broad excepts across 15.7k lines, 59 test files, and the
only pre-commit configuration. If you want a codebase to read to learn the domain, or to
fork with confidence, this is it. Its largest file is a data table, not logic.

**Obscura** — 142k lines of Rust, by far the largest and the most disciplined on smells,
but with an error strategy built on `.unwrap()`. `dom.rs` at 20,284 lines is a very
large module even by Rust standards. Workspace split into nine focused crates is good
structure. See [finding 4](#4-obscuras-error-strategy-is-panic-on-failure-in-a-long-running-server).

**Clearcote** — 23k lines across 32 readable C++ patches and multi-language SDKs, with 65
test files and 8 CI workflows including a patch-integrity check and a stealth-coherence
regression gate. 127 broad excepts (5.5/kLOC) is the second-highest density here. One
contributor, so review depth and continuity depend on one person.

---

## How the numbers were produced

```bash
./scripts/sandbox.sh up
ssh <box> 'docker exec -i antidetect-box python3 -' < scripts/codemetrics.py > metrics.json
```

The script reads files as text and AST only; no project code is imported or executed.
Counting rules:

- **Vendored and generated trees excluded**: `node_modules`, `bundles`, `dist`, `build`,
  `target`, `vendor`, `third_party`, `__pycache__`, minified JS, lockfiles, `.patch`
  files, and the vendored `json.hpp`.
- **Test files excluded from production counts** and reported separately.

Both rules are load-bearing. An earlier revision of this review applied the exclusions
to the line counts but not to the pattern searches, and reported 116 `eval` calls in a
295-line project because it was scanning a vendored Playwright bundle. Any metric here
that looks implausible for a codebase's size should be checked against that class of
error first.

---

## Limits of this review

- **Static only.** Nothing was built, installed, or executed. Runtime behaviour, actual
  test pass rates, and performance are out of scope.
- **Counts are proxies, not verdicts.** `except Exception` is sometimes correct; `print`
  is output in a CLI and residue in a library. Every count in this document should be
  read with its location, which is why the findings section quotes file and line.
- **Closed components are unreviewable.** CloakBrowser's binary and XDriver's bundle
  cannot be assessed from source at all; their rows measure wrapper code only.
- **Generated code inflates some measures.** `botasaurus-driver`'s annotation coverage
  and Obscura's line count both include machine-generated files.
- **No dependency-vulnerability scan** was run, and no review of transitive dependencies.
  That is a worthwhile addition and is not present here.
- **Single reviewer, single pass.** No second opinion, and shallow clones (depth 50)
  limit history-based analysis.
