# Methodology

How this comparison is produced, what its claims are worth, and where it stops.

Every non-obvious claim in the report carries an [evidence tier](#evidence-tiers)
indicating whether it was read from source, reported by the vendor, reported by the
community, or not established.

---

## Table of contents

- [Scope](#scope)
- [Evidence tiers](#evidence-tiers)
- [What we did not do](#what-we-did-not-do)
- [Source handling](#source-handling)
- [Version and health data](#version-and-health-data)
- [Conflict of interest](#conflict-of-interest)
- [Rating policy](#rating-policy)
- [How to challenge a claim](#how-to-challenge-a-claim)

---

## Scope

The report covers **open-source and freely-obtainable browser-automation and
anti-detection tooling** that a developer could adopt directly. Nine tools are
tracked; each has a dedicated page.

Explicitly **out of scope**: hosted scraping APIs and commercial proxy networks. They
solve an overlapping problem with a completely different cost and operational model,
and putting a paid API in the same table as an MIT library invites apples-to-oranges
conclusions. Where a hosted service is relevant it is named as context, never scored.

---

## Evidence tiers

Every substantive claim is tagged with the strength of evidence behind it. The tier distinguishes verified,
claimed, and unestablished statements, which are otherwise indistinguishable in prose.

| Tier | Meaning | How it is produced |
|:----:|---------|--------------------|
| **A** | **Verified in source.** We read the code at a known commit and cite the file. | `scripts/sandbox.sh` clones the upstream repo into an isolated container; claims are read out of the actual tree. |
| **B** | **Vendor-reported.** The maintainer publishes this; we located the claim but did not reproduce it. | Quoted from the project's own README, release notes, or docs, with the source named. |
| **C** | **Community-reported.** Circulating in issues, forums, or third-party posts. | Anecdotal. Directionally useful, individually unreliable. |
| **D** | **Not established.** No evidence either way that we could find. | Stated as unknown. **`D` is not a criticism** — it usually means nobody has published a test, not that the tool failed one. |

Two rules keep the tiers honest:

1. **Anti-bot-service outcomes can never be Tier A here.** We do not run a benchmark
   suite against commercial WAFs (see below), so no "beats Cloudflare" claim in this
   repo is ever better than Tier B. A previous revision of this report
   presented such claims as measured; that was incorrect and has been corrected.
2. **A vendor's own benchmark stays Tier B no matter how detailed it is.** Screenshots,
   score tables, and pass/fail grids published by the tool author are evidence of what
   the author observed on their setup, not independent results.

---

## What we did not do

The following were not performed, and no claim in this repository should be read as implying them:

- **No head-to-head anti-bot benchmark.** We did not point these nine tools at
  Cloudflare, DataDome, Kasada, Akamai, PerimeterX, or Imperva and count passes.
  A credible benchmark requires a fixed target list, matched residential IPs, multiple
  trials per cell, and controls for time-of-day and IP reputation. Results produced
  without those controls are not reproducible.
- **No CAPTCHA solve-rate measurement.**
- **No performance benchmarking of our own.** Throughput, memory, and page-load
  figures quoted anywhere in the report are the projects' own numbers (Tier B).
- **No binary analysis of closed builds.** Where a tool ships a proprietary binary
  (CloakBrowser's Pro build), we can read the wrapper but not the binary. Claims about
  what the binary does are Tier B by construction.
- **No dependency-vulnerability scanning.** The [code review](CODE-REVIEW.md) counts
  security-relevant patterns in first-party source; it does not audit transitive
  dependencies for known CVEs.
- **No long-run stability testing.** A tool that works today may be detected next
  week; nothing here measures durability.

Because of the first point, **the anti-bot coverage question is answered with a
provenance table, not a scorecard.** See the report's coverage section.

---

## Source handling

> [!IMPORTANT]
> The nine projects are unaudited third-party code, including stealth browsers and
> patched binaries. They are never cloned onto, or executed on, a workstation.

`scripts/sandbox.sh` (run on a disposable remote host) does the following:

- clones every upstream repo into a **Docker volume**, so the trees never land on the
  host filesystem;
- runs the container with `--cap-drop=ALL`, `--security-opt=no-new-privileges`, a
  `--read-only` root filesystem, and memory/PID limits;
- **severs the network** (`docker network disconnect`) once cloning finishes, so all
  subsequent inspection happens offline;
- exposes the trees only for reading (`rg`, `git log`, `cat`) via `docker exec`.

```bash
./scripts/sandbox.sh up        # build, clone, then cut the network
./scripts/sandbox.sh refresh   # reconnect, fetch, cut again
./scripts/sandbox.sh sh        # offline shell for inspection
./scripts/sandbox.sh nuke      # destroy container and volume
```

**Nothing from these repos is ever installed, built, or executed** as part of
producing this report — not `pip install`, not `npm install`, not a test suite. Tier A
means *we read the code*, not *we ran it*. If a future revision does run something,
it happens in that container and the tier system will say so.

---

## Version and health data

The version and project-health tables in [STATUS.md](STATUS.md) are **generated, not
hand-written**:

```bash
python scripts/verify.py --write
```

It queries PyPI, the npm registry, and the GitHub API, and writes a dated table. This
exists because the previous version of this report drifted roughly five weeks out of
date across nine tools without any visible signal that it had — hand-maintained
version tables always lose. Every claim in STATUS.md is reproducible by re-running one
command.

Health columns are selected for build-decision relevance: **license** (redistribution
and commercial-use constraints), **last push** (commit recency), **contributors**
(maintenance concentration). Star counts are included for completeness; they measure
repository popularity and have no established relationship to detection outcomes.

---

## Conflict of interest

**This repository is sponsored by [Scrappey](https://scrappey.com/), a commercial web-data
API. Scrappey is a paid alternative to doing this yourself with the tools reviewed
here.** The sponsor therefore has a commercial interest in how self-hosted tooling is
portrayed.

Mitigations, so you can judge rather than take our word:

- **Scrappey is not rated.** It appears in no capability matrix, no coverage table, and
  no recommendation row. A sponsor cannot win a comparison it is excluded from.
- **No tool is scored on anything we did not verify or attribute.** The tiers above
  apply uniformly; there is no category where the sponsor's competitors are graded more
  harshly than the evidence supports.
- **The sponsor gets the same skepticism.** Scrappey publishes no independently
  reproduced benchmarks either; any claim it makes about service coverage is Tier B, the
  same as every vendor here.
- **Sponsorship does not buy edits.** If you believe a rating is shaded by the
  sponsorship, open an issue quoting the claim — that is a bug like any other.

---

## Rating policy

Earlier revisions of this report scored tools with five-star ratings across a dozen
capability rows. Those are gone. They were unfalsifiable: no rubric defined what four
stars meant versus five, and no evidence was cited for any individual score, so the
grid read as measurement while being opinion.

What replaced them:

- **Architecture facts** — stated as what the tool actually does, verifiable from
  source (Tier A). "Hides `navigator.webdriver` in C++" is checkable; "⭐⭐⭐⭐ stealth"
  is not.
- **A capability-to-implementation index** — maps a stated technical requirement to
  the tools whose source implements it. It is a lookup derived from the architecture
  tables, not a ranking, and contains no recommendation.

Similarly removed: a "Realistic Success Rates" table giving percentage bands per
protection tier. Those numbers had no measurement, sample size, target list, or date
behind them, and precision like "20-40%" implies a study that never happened.

---

## How to challenge a claim

Open an issue with the claim quoted verbatim and one of:

- a **file and commit** that contradicts it (upgrades or removes a Tier A claim);
- a **link** to vendor documentation that supersedes it (Tier B);
- a **reproducible test** with methodology attached — target, IP type, trial count,
  dates (this is the only thing that can create new high-confidence evidence).

Corrections that arrive with evidence get applied. The report is versioned in git;
[CHANGELOG.md](CHANGELOG.md) records what changed and why.
