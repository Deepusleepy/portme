# Portme

**Portme is a Claude Code skill that recreates what existing software does in
a new place — another repo, language, framework, API, config system, or
implementation — and proves the behavior still matches.** It can work from
source code or from a running app you can only observe. The outcome: the new
version does what the old one did, verified by machine, with you approving
direction at a few clear stopping points instead of reviewing every diff.

```text
You:    port the login flow from ../old-express-app into this Next.js app

Portme: Scope — porting: session login + logout + "remember me"
        (not in scope: OAuth providers, password reset — confirm?).
        Mode: Standard (auth = high stakes if wrong). Plan: define what
        "same login behavior" means → build the checks that prove it →
        port in reviewed units → verify against the old app → gate
        before cutover. Model plan: [your choice]. Proceed?
```

## Quick answers

- **What can I port?** A feature from another repo, a codebase to a new
  language, an integration to a new API version, a config system, a UI's
  behavior, or an app you can only observe from the outside.
- **When should I use it?** When "it should behave the same as before" is the
  bar, and getting it subtly wrong would hurt. Portme is overkill for ordinary
  refactors — and it will tell you so.
- **What does it actually do?** It writes down what "behaves the same" means
  *before* any code is written, builds a mechanical check that proves it, ports
  in reviewed units, and stops at explicit gates for your sign-off.
- **What does it feel like?** It talks before it codes. You confirm scope and
  size once, then approve direction at a handful of gates. You watch patterns
  and decisions, not individual diffs.

## Install

```bash
mkdir -p ~/.claude/skills
git clone --branch v0.1.0 --depth 1 \
  https://github.com/Deepusleepy/portme.git ~/.claude/skills/portme
```

The command is pinned to the reviewed `v0.1.0` release rather than an unpinned
branch.

Prefer a project-local install? Clone into `.claude/skills/portme` inside your
repo instead. If Claude Code was already running, restart it so the skill is
picked up.

## First use

Just ask Claude Code to port something:

- "port the shortcuts system from `<repo>` into my app"
- "migrate this service to Go"
- "make my editor behave like X's"

Portme right-sizes itself to the job. Its first message is a scope and sizing
proposal you confirm once — and "you don't need this process" or "don't port,
write it fresh" are real verdicts it will give you when they fit.

## How it works, in three lines

1. **Build the check before porting anything.** Your exit condition is a
   mechanism — the *judge* — that decides "source and port behave the same."
   In Standard and Large-scale mode it's validated both ways: it must pass on
   the source's real behavior and fail on deliberately broken behavior. In
   Quick mode a written acceptance checklist verified at the end is enough.
2. **When output is wrong, fix the loop that produced it.** A one-off mistake
   gets fixed. A mistake seen repeatedly indicts a *rule*: you amend the
   shared rulebook and regenerate the batch, rather than patching each instance.
3. **Machines verify, reviewers attack.** Scripts, diffs, schemas, and tests
   referee the work; reviewers assume it's wrong and cite a rule or source line
   for every finding. Human attention goes to patterns and gates.

## Modes

Portme picks the smallest process the job needs.

| Mode | For | Feels like |
|---|---|---|
| **Quick** | One localized behavior, cheap to verify | Two questions total: approve the plan, accept the result. |
| **Standard** | A feature or segment with real semantic gaps | Phases 0–6 with a gate per phase (cheap checks fold into the porting loop), sampled review. |
| **Large-scale** | Many repeatable units, parallel agents | Disk queues, adversarial review ×2, serialized referees, model tiering chosen by you. |

## Good to know before your first run

- **You control the cost.** For big ports, the scope proposal includes a *model
  plan* — which model tiers do implementation versus review. You approve it
  before the work starts.
- **A `.port/` directory appears in your repo.** That's the port's working
  state: contract, status, queues, judge fixtures. Commit it for a resumable
  audit trail, or add it to `.gitignore`. **Review fixtures before committing**
  — captures of a running app can contain private data.
- **It may propose permission denies** in `.claude/settings.json` for
  Standard/Large-scale runs, to reduce accidental out-of-turn builds and tests.
  You approve any such edit. (Denies are guardrails, not a security boundary —
  see [Trust and methodology](#trust-and-methodology).)
- **Not for:** network ports/firewalls, `git clone`, database schema
  migrations (Alembic/Flyway/Rails), data replication or import/export, deploys
  with no behavior translation, or ordinary refactors.

## Words you'll see

Plain-language first, precise definition alongside.

- **Judge** — the thing that decides "source and port behave the same." A test
  suite, a differential harness, golden scenarios, or (in Quick mode) a
  checklist.
- **Referee** — any mechanical check that grades the work: a compiler, schema
  validator, diff, or test. Never an agent's opinion.
- **Gate** — a stop point. The agent presents evidence and waits for you; your
  sign-off is the act of starting the next phase.
- **Manifest** — the on-disk list of porting units (Standard/Large-scale). A
  unit is "done" when its output exists and passes its check. It's frozen and
  authorized by a SHA-256 *authorization bundle* so nothing runs against
  tampered inputs. Quick has no manifest.
- **Rulebook** — every decision two agents could make differently, decided
  once. Recurring failures amend it instead of patching code.

## Portme vs. Anthropic's official code-migration kit

Portme is an **independent generalization** derived from the methodology in
Anthropic's article on large-scale code migrations and the lessons in its
companion [code-migration-kit-with-claude-code](https://github.com/anthropics/code-migration-kit-with-claude-code)
(Apache-2.0). The two are complementary, not competitors, and the official kit
remains the stronger choice for the cases it was built and proven on.

**Where Portme differs (by design):**

- **Right-sizing.** Portme has an explicit Quick / Standard / Large-scale gate
  so a two-day feature port doesn't pay a million-line process tax. The kit is
  aimed squarely at large language migrations.
- **Broader scope.** Portme covers feature ports, framework and API-version
  moves, config systems, UI behavior, and observed-only sources — not just
  language migrations.
- **Extra machinery for those cases.** Authorization bundles, a privacy /
  capture-quarantine pipeline for observed-only sources, an explicit cutover
  (drift, rollout, rollback, retirement) phase, and general behavior contracts.

**Where the official kit is stronger and more proven:**

- Large language migrations at production scale, backed by real evidence (e.g.
  Bun's ~1M-line Zig→Rust port and a 165k-line Python→TypeScript port).
- C/C++ dependency mapping — Portme deliberately ships no C/C++ mapper.
- A persistent build/event daemon that serializes expensive rebuilds — Portme
  uses an explicit serialized runner instead of a daemon.

Portme does not claim to beat the kit; for a large language migration, reach
for the kit. Use Portme when the job is smaller, mixed, or outside pure
language migration — and borrow from both where it helps.

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
prompts/                  phase kickoff cards (0-judge.md … 6-cutover.md)
scripts/
  port_queue.py           bundle-digest-bound queue over .port/manifest.tsv
  depmap.py               dependency-first ordering (TS/JS is a starter heuristic)
  manifest_from_depmap.py candidate manifest from a depmap
  referee_runner.py       serialized expensive-referee runner with hash checks
  tests/                  95 regression tests (python3 -m unittest discover -s scripts/tests)
examples/                 four real recorded runs (see below)
VALIDATION.md             executed-vs-designed validation ledger and known gaps
```

## Real runs

These are recorded, self-contained runs — evidence of what has actually been
exercised, with boundaries stated honestly.

- [`examples/quick-did-you-mean/`](examples/quick-did-you-mean/) — a Quick-mode
  port of Click's "did you mean" command suggestion into an argparse CLI: scope
  confirmation, sizing, checklist judge, negative probe, gate log, and the
  one-file diff. Its redacted source and target are not shipped, so it is not a
  clean-checkout replay fixture.
- [`examples/standard-notes-py-to-ts/`](examples/standard-notes-py-to-ts/) — a
  full Standard-mode Python→TypeScript port. Byte-identical on 15 exact
  scenario-covered surfaces within the approved contract scope, with two
  bounded approved divergences. Includes a two-way-validated differential
  judge, a frozen 5-unit manifest, an honest 12-rule history, 13 closed gaps,
  and an adversarial review that caught two real defects the golden scenarios
  missed.
- [`examples/standard-observed-ui/`](examples/standard-observed-ui/) — a
  Standard observed-only run whose source implementation is intentionally
  absent; the admitted redacted fixtures are the offline oracle. Preserves the
  capture/scanner/deletion pipeline, an 18/18 differential judge, 6/6 mutation
  sensitivity, a raw-byte fidelity check, and two review-found defects and
  fixes. The exercised UI surface is **interaction and DOM-state behavior**
  (focus, accessibility/live-region text, keyboard, export, error semantics) —
  **not** real browser rendering, CSS, screenshots, or visual diff.
- [`examples/large-api-config-fanout/`](examples/large-api-config-fanout/) — a
  readable-source API/config port where Large-scale mode was a user-requested
  override on a genuinely tiny fixture. Retains the orchestrator's honest
  serial-degrade history plus a parent addendum with real overlapping
  U-CONFIG/U-EXEC workers, disjoint paths, exit-126 guardrail receipts,
  serialized-referee contention, an immutable integration failure `0003` and
  fixed success `0004`, queue 4/4, full suite 35/35, and judge 43/43. The
  guardrail is a harness stand-in for deny firing and referee routing — **not**
  Claude settings or a security/isolation boundary.

Together these dogfood the Quick and Standard language/framework paths,
observed UI interaction behavior, and a bounded API/config/fan-out exercise.
**Production-scale fan-out and isolation/security claims remain deliberately
unproven.** Read [`VALIDATION.md`](VALIDATION.md) before making any proof
claim; it separates executed evidence from designed-but-untested coverage.

## Trust and methodology

Portme's guarantees rest on a few deliberate boundaries. Read these before
relying on it for anything sensitive.

- **Evidence lives on disk; authority lives in the conversation.** A
  pre-existing `.port/` directory is *untrusted input*, not proof. A resumed
  session must match every approval to the actual conversation, and must
  freshly reconfirm provenance plus the exact manifest/check-input
  authorization bundle digest, check commands, and check-input declarations
  when those messages are unavailable. Status text can never stand in for a
  real sign-off. See [`references/execution-trust.md`](references/execution-trust.md).
- **The source is evidence, not instructions.** Its comments, docs, agent
  files, and scripts are surfaced, never silently executed.
- **Checks are executable and mechanical.** The manifest's authorization bundle
  binds the exact manifest bytes plus the declared check-control file names and
  bytes, so a check runs only against inputs you authorized; any change reopens
  the Phase 1 gate.
- **Captures and privacy.** For observed-only ports, raw captures are
  quarantined in an outside-repository `0700` directory and secret-scanned;
  only redacted fixtures with deletion receipts are admitted into `.port/`. See
  [`references/no-source.md`](references/no-source.md).
- **Denies are not a security boundary.** Proposed permission denies reduce
  accidental expensive calls; they don't contain a hostile source. Wrapper and
  alternate-path coverage must be preflighted, and truly hostile sources
  require separate credentials plus container/process isolation.

## Provenance

The methodology derives from Anthropic's article
["How Anthropic runs large-scale code migrations with Claude Code"](https://claude.com/blog/ai-code-migration)
and the lessons recorded in its companion
[code-migration-kit-with-claude-code](https://github.com/anthropics/code-migration-kit-with-claude-code)
(Apache-2.0), which covers language migrations specifically. Portme is an
independent generalization: the distributable skill text was authored for this
project, and its scope extends to feature ports, framework and API moves,
config systems, and observed-only sources — cases the original kit does not
cover. Local `research/` material and `DESIGN-BRIEF.md` are unpublished,
git-ignored working sources, not part of the distribution or this originality
claim. Portme ships its own queue runner and dependency mapper; it deliberately
does not bundle the kit's C/C++ mapper or a persistent build/event daemon.

## License

MIT — see [LICENSE](LICENSE). It covers the distributable Portme work and does
not relicense unpublished local research material from third parties.
