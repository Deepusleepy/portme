# Portme and Anthropic's migration kit

Portme is an independent generalization of the method in Anthropic's article ["How Anthropic runs large-scale code migrations with Claude Code"](https://claude.com/blog/ai-code-migration) and the lessons in the companion [code-migration-kit-with-claude-code](https://github.com/anthropics/code-migration-kit-with-claude-code) (Apache-2.0). They fit different jobs. The official kit is the stronger choice for the cases it was built and proven on.

The skill text in this repo was written for this project. Local `research/` notes and `DESIGN-BRIEF.md` are unpublished, git-ignored working files. They are not part of the distribution, and they are not part of the originality claim.

## Where Portme is different

- **It picks a size.** Quick, Standard, and Large-scale exist so a small feature port does not pay for a million-line process. The kit is aimed at large language migrations.
- **It covers more than language ports.** Feature ports, framework and API-version moves, config systems, UI behavior, and apps you can only watch.
- **Extra pieces for those cases.** Authorization bundles (a hash of the manifest and the check files), a capture quarantine for observed-only sources, an explicit cutover phase (drift, rollout, rollback, retirement), and a written behavior contract.

## Where the official kit is stronger

- Large language migrations at production scale, with public evidence (Bun's roughly 1M-line Zig to Rust port, and a 165k-line Python to TypeScript port).
- C/C++ dependency mapping. Portme ships no C/C++ mapper.
- A long-running build daemon that serializes expensive rebuilds. Portme uses an explicit serialized runner instead of a daemon.

Portme does not claim to beat the kit. For a large language migration, use the kit. Use Portme when the job is smaller, mixed, or not a pure language migration. Borrow from both when that helps.
