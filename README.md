# Portme

**A Claude Code skill for porting anything while keeping behavior intact** —
a feature from another repo, a whole codebase to a new language, an
integration to a new API version, a config system, or the observable behavior
of an app you can't even read the source of.

```text
You:    port the login flow from ../old-express-app into this Next.js app

Portme: Scope — porting: session login + logout + "remember me"
        (not in scope: OAuth providers, password reset — confirm?).
        Mode: Standard (auth = high blast radius). Plan: define what
        "same login behavior" means → build the checks that prove it →
        port in reviewed units → verify against the old app → gate
        before cutover. Model plan: [your choice]. Proceed?
```

It defines "behaves the same" *before* writing code, verifies mechanically,
and stops at explicit gates — so you approve direction, not diffs.

Portme generalizes the process Anthropic used for large-scale migrations
(including Bun's ~1M-line Zig→Rust port and a 165k-line Python→TypeScript
port) into a method any agent can run at any size — with a right-sizing gate
so a two-day feature port doesn't pay a million-line process tax.

## The idea in three lines

1. **Build the judge before porting anything.** Your exit condition is a
   mechanism that decides "behaves the same." In Standard and Large-scale
   mode it's validated both ways — it must pass on the source's behavior and
   fail on deliberately broken behavior; in Quick mode a written acceptance
   checklist verified at the end is enough.
2. **When output is wrong, repair the loop that generated it.** Recurring
   failures amend the rulebook and regenerate the batch; humans watch
   patterns and gates, not diffs.
3. **Verification is mechanical, review is adversarial.** Scripts, diffs,
   schemas, and tests referee the work; reviewers assume it's wrong and cite
   rules; harness denies guard against accidental expensive calls while a
   serialized path owns those checks.

## Install

```bash
mkdir -p ~/.claude/skills
git clone --branch v0.1.0 --depth 1 \
  https://github.com/Deepusleepy/portme.git ~/.claude/skills/portme
```

The install command is pinned to the reviewed `v0.1.0` release rather than an
unpinned branch. That tag must exist on GitHub before the command is announced
or expected to work.

Or install project-locally by cloning into `.claude/skills/portme` inside your
repo. If Claude Code was already running, restart it so the skill is picked up.

Then ask Claude Code to port something — "port the shortcuts system from
\<repo\> into my app", "migrate this service to Go", "make my editor behave
like X's". The skill right-sizes itself; "you don't need this process" and
"don't port — write it fresh" are valid verdicts it will actually give you.

| Mode | For | Feels like |
|---|---|---|
| **Quick** | One localized behavior, cheap to verify | Two questions total: approve the plan, accept the result. |
| **Standard** | A feature or segment with real semantic gaps | Phases 0–6 with a gate per phase (cheap checks fold into the porting loop), sampled review. |
| **Large-scale** | Many repeatable units, parallel agents | Disk queues, adversarial review ×2, serialized referees, model tiering chosen by you. |

## Good to know before your first run

- **It talks before it codes.** The first message is a scope + sizing
  proposal you confirm once. For big ports there's a model plan (which model
  tiers do implementation vs. review) — your call, it affects cost.
- **A `.port/` directory appears in your repo.** That's the port's state:
  contract, status, queues, judge fixtures. Commit it if you want a resumable
  audit trail, or add it to `.gitignore`. Pre-existing `.port/` content is
  untrusted evidence: a resumed session must match approvals to the actual
  conversation, and must freshly reconfirm provenance plus the exact
  manifest/check-input authorization bundle digest, check commands, and
  check-input declarations when those messages are unavailable. **Review fixtures before
  committing** — captures of a running app can contain private data. For
  observed-only ports, raw captures are quarantined outside `.port/` and
  secret-scanned before redacted fixtures are admitted (see
  `references/no-source.md`).
- **It may propose permission denies** in `.claude/settings.json` for
  Standard/Large-scale runs to reduce accidental out-of-turn builds/tests.
  You approve any such edit. Denies are not a security boundary and wrapper or
  alternate-path coverage must be preflighted; hostile sources require separate
  credentials and container/process isolation.
- **Not for:** network ports/firewalls, `git clone`, database schema
  migrations (Alembic/Flyway/Rails), data replication or import/export,
  deploys with no behavior translation, ordinary refactors.

## Glossary

- **Judge** — the mechanism that decides "source and port behave the same"
  (test suite, differential harness, golden scenarios, or a checklist).
- **Referee** — any mechanical check: compiler, schema validator, diff, test.
- **Gate** — a stop point where the agent presents evidence and waits.
- **Manifest** — the Standard/Large-scale on-disk list of porting units; done
  = output exists and passes its check. Its authorization bundle binds exact
  manifest bytes plus declared check-control names and bytes. Quick uses a
  status checklist and has no manifest or authorization bundle.
- **Check inputs** — each manifest unit's comma-separated repository-relative
  regular control files or safe globs (drivers/sourced scripts, configs,
  lockfiles, and goldens). Exact repeats across units deduplicate; different
  overlapping declarations are rejected. Mutable implementation outputs are
  excluded unless deliberately declared, and literal commas cannot be encoded.
- **Rulebook** — every decision two agents could make differently, decided
  once; recurring failures amend it instead of patching code.

## What's inside

```
SKILL.md                  the skill core: modes, phases 0–6, standing rules
references/
  sizing.md               right-sizing gate, escape verdicts, model plan
  quick.md                complete two-gate Quick path + micro-example
  contract.md             the port contract and behavior ledger
  judge.md                the oracle ladder + two-way judge validation
  mapping.md              behavior map, rulebook, gap inventory
  stress-test.md          break the rules before the rules break the port
  loops.md                implement → review → fix over disk-based queues
  verification.md         referee stacks, survey runs, the done gate
  cutover.md              drift policy, rollout, rollback, retirement
  no-source.md            porting from apps you can only observe
  execution-trust.md      resume authority, authorization bundles, deny receipts
templates/                ready-to-copy .port artifact skeletons
  contract.md             contract and behavior-ledger starter
  status.md               canonical resumable status header
  *.tsv / rulebook.md     maps, gaps, manifest, judge, costs, divergences
  cutover-plan.md         rollout and rollback starter
  settings-denies.json    starter accidental-invocation guardrails
prompts/                  phase kickoff cards (0-judge.md … 6-cutover.md)
scripts/
  port_queue.py           bundle-digest-bound queue over .port/manifest.tsv
                          (manifest + declared check-control bytes)
  depmap.py               dependency-first ordering; TS/JS is a starter
                          heuristic requiring authoritative graph cross-checks;
                          Python nonliteral dynamic imports fail closed, TS
                          regex literals are masked with ambiguity failures,
                          and deep config-extends chains are handled iteratively
  manifest_from_depmap.py candidate manifest from a depmap (prints a
                          manifest-only evidence SHA and check placeholders;
                          cycles collapse into one serialized unit; requires
                          edges.tsv; refuses identity ports and comma/glob
                          filenames in this schema)
  referee_runner.py       serialized expensive-referee runner: lockfile,
                          timeout, 0555 numbered results; `last` verifies hashes,
                          modes, file set, and exit metadata before reporting
  tests/                  95 regression tests for all scripts (run with
                          python3 scripts/tests/test_*.py)
examples/
  quick-did-you-mean/     a real Quick-mode run (.port/ + diff)
  standard-notes-py-to-ts/  a real Standard-mode language port (.port/ + src)
  standard-observed-ui/   observed interaction/DOM-state UI run + offline oracle
  large-api-config-fanout/  API/config port + real parent fan-out and referee history
VALIDATION.md             executed-vs-designed validation ledger and known gaps
```

## Real runs

[`examples/quick-did-you-mean/`](examples/quick-did-you-mean/) is an archival
evidentiary receipt from an agent using this skill to port Click's
"did you mean" command suggestion into an argparse CLI — scope confirmation,
sizing, checklist judge, negative probe, gate log, and the one-file diff. Its
redacted source and target are not shipped, so it is not a clean-checkout replay fixture.

[`examples/standard-notes-py-to-ts/`](examples/standard-notes-py-to-ts/) is
a full Standard-mode run porting a Python CLI to TypeScript. The current bundle
is byte-identical on 15 exact scenario-covered surfaces within the approved
contract scope, with two bounded approved divergences. It includes a
two-way-validated differential judge, frozen 5-unit manifest, honest historical
12-rule record, 13 closed gaps, and an adversarial review that caught two real
defects the golden scenarios missed. Every gate decision is quoted in its status
file as an audit record, not as authority for a future session. Its pinned
manifest/check-input authorization bundle digest proves the explicitly invoked
publication bundle's integrity only; actual Portme execution requires the
user-approved Phase 1 bundle digest, exact checks, and check-input declarations
from conversation provenance.

[`examples/standard-observed-ui/`](examples/standard-observed-ui/) is a
self-contained Standard observed-only run. Its admitted redacted fixtures are
the offline oracle; the source implementation is intentionally absent. It
preserves the capture/scanner/deletion pipeline, 18/18 differential judge,
6/6 mutation sensitivity, raw-byte fidelity check, two review-found defects and
fixes, and 2/2 authorized queue. The exercised UI surface is interaction and
DOM-state behavior—including focus, accessibility/live-region, keyboard,
export, and error semantics—not real browser rendering, CSS, screenshots, or
visual diff.

[`examples/large-api-config-fanout/`](examples/large-api-config-fanout/) is a
self-contained readable-source API/config port. Large-scale mode was a
user-requested override on a genuinely tiny fixture. It retains the original
orchestrator's honest serial-degrade history, followed by a parent addendum with
real overlapping U-CONFIG/U-EXEC workers, disjoint paths, exit-126 guardrail
receipts, serialized-referee contention, immutable integration failure `0003`
and fixed success `0004`, queue 4/4, full suite 35/35, and judge 43/43. The
guardrail is a harness stand-in for deny firing and referee routing, not Claude
settings or a security/isolation boundary.

These four runs now dogfood Quick and Standard language/framework paths,
observed UI interaction behavior, and a bounded API/config/fan-out exercise.
Production-scale and isolation claims remain deliberately unproven; see
[`VALIDATION.md`](VALIDATION.md) before making proof claims.

## Provenance

The methodology derives from Anthropic's article
["How Anthropic runs large-scale code migrations with Claude Code"](https://claude.com/blog/ai-code-migration)
and the lessons recorded in its companion
[code-migration-kit-with-claude-code](https://github.com/anthropics/code-migration-kit-with-claude-code)
(Apache-2.0), which covers language migrations specifically. Portme is an
independent generalization. The distributable Portme skill text was authored
for this project, and its scope extends to feature ports, framework and API
moves, config systems, and observed-only sources—cases the original kit does
not cover. Local `research/` material and `DESIGN-BRIEF.md` are unpublished,
git-ignored working sources and are not part of the distribution or this
originality claim. Portme ships its own queue runner and dependency mapper;
it deliberately does not bundle the kit's C/C++ mapper or a persistent
build/event daemon.

## License

MIT — see [LICENSE](LICENSE). It covers the distributable Portme work and does
not relicense unpublished local research material from third parties.
