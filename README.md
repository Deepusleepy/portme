# Portme

Portme is a Claude Code skill that ports a feature, codebase, or API into a new place and checks that the new version behaves the same.

```text
You:    port the login flow from ../old-express-app into this Next.js app

Portme: Scope: session login, logout, and "remember me".
        Out of scope: OAuth providers and password reset. Confirm?
        Mode: Standard (login is costly if it is wrong).
        Plan: write down what "same login" means, build the checks,
        port in reviewed pieces, compare with the old app, and stop
        for your OK before switching over. Model plan: your choice.
        Proceed?
```

It can start from source code, or from a running app you can only watch from the outside.

## Install

```bash
mkdir -p ~/.claude/skills
git clone --branch v0.1.0 --depth 1 \
  https://github.com/Deepusleepy/portme.git ~/.claude/skills/portme
```

That clone is pinned to the reviewed `v0.1.0` release. For a project-local install, clone into `.claude/skills/portme` inside the repo. Restart Claude Code if it was already running.

## How to use

Ask Claude Code to port something:

- "port the shortcuts system from `<repo>` into my app"
- "migrate this service to Go"
- "make my editor behave like X's"

Portme restates the scope and picks a size. You confirm that once. It will also say when you do not need this process, or when you should write the feature fresh instead.

## Modes

| Mode | Use it for | What you do |
|---|---|---|
| **Quick** | One local behavior, cheap to check | Approve the plan, then accept the result. |
| **Standard** | A feature with real behavior gaps | Phases 0–6, with a stop for you at each phase. |
| **Large-scale** | Many similar units, several workers | The same phases, with queues, two reviewers per unit, and a model plan you approve. |

## Good to know

- Big ports include a model plan: which model does the writing, and which does the review. You approve it before the work starts.
- A `.port/` directory holds the contract, status, and check fixtures. Commit it if you want a trail you can resume, or gitignore it. Review fixtures before you commit them. Captures from a running app can contain private data.
- It may ask to add permission denies in `.claude/settings.json` so expensive checks do not run by accident. You approve that edit. Denies are a guardrail, not a security boundary. See [Trust](docs/trust.md).
- Do not use it for network ports or firewalls, `git clone`, database schema migrations (Alembic, Flyway, Rails), data copy or import/export, deploys that do not change behavior, or ordinary refactors.

## Read next

- [Glossary](docs/glossary.md)
- [Trust and limits](docs/trust.md)
- [Compared with Anthropic's migration kit](docs/anthropic-kit.md)
- [Recorded examples](docs/examples.md)
- [Validation ledger](VALIDATION.md): what has actually been run
- [SKILL.md](SKILL.md): modes, phases 0–6, and the standing rules
- References: [sizing](references/sizing.md), [quick](references/quick.md), [contract](references/contract.md), [judge](references/judge.md), [mapping](references/mapping.md), [stress test](references/stress-test.md), [loops](references/loops.md), [verification](references/verification.md), [cutover](references/cutover.md), [observed-only sources](references/no-source.md), [trust details](references/execution-trust.md)
- [Templates](templates/), [phase cards](prompts/), and [scripts](scripts/) (`port_queue.py`, `depmap.py`, `manifest_from_depmap.py`, `referee_runner.py`; tests in `scripts/tests/`)

## Provenance

The method comes from Anthropic's article ["How Anthropic runs large-scale code migrations with Claude Code"](https://claude.com/blog/ai-code-migration) and the companion kit [code-migration-kit-with-claude-code](https://github.com/anthropics/code-migration-kit-with-claude-code) (Apache-2.0), which is about language migrations. Portme is an independent generalization. The skill text was written for this project, and the scope also covers feature ports, framework and API moves, config systems, and apps you can only watch. Local `research/` notes and `DESIGN-BRIEF.md` are unpublished git-ignored working files, not part of this distribution. Portme ships its own queue runner and dependency mapper. It does not include the kit's C/C++ mapper or a long-running build daemon. A longer comparison is in [docs/anthropic-kit.md](docs/anthropic-kit.md).

## License

MIT. See [LICENSE](LICENSE). It covers the distributable Portme work and does not relicense unpublished local research material from third parties.
