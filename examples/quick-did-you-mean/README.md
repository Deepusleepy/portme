# Example: a real Quick-mode port

This folder is the record of a real Portme run, plus the one-file diff it produced. The `.port/` directory is published as `port-artifacts/`. It is not a clean-checkout replay: the source and target repos are not here, so the recorded commands cannot be rerun from this directory alone.

Publication edits: absolute workstation paths were redacted to `REDACTED-SANDBOX`, the Click cross-check receipt was moved from `/tmp` into `port-artifacts/click-ref.txt`, and the status header was put in the canonical field order. The approval-provenance fields were added after the run. They separate preserved quotes from authority. No approval was invented.

**The port:** bring Click's "did you mean" subcommand suggestion (the same `difflib.get_close_matches` behavior and message text, read from Click's source) into a small argparse `notes` CLI. That is a feature port across frameworks.

**What to look at:**

- `port-artifacts/status.md`: the whole run in one file. Scope, six-factor score (1, so Quick), why the port is worth doing, the contract, the checklist, both gate sign-offs quoted in the log, and the result. Click replaces the whole error message. Keeping argparse meant appending the suggestion instead. That difference is recorded as an approved divergence, not a silent choice.
- `port-artifacts/evidence/`: raw before/after CLI captures for every checklist item, including `c5.txt`, the negative probe (break the matcher, watch the check fail, restore it, watch it pass).
- `change.diff`: the entire code change. Quick mode's promise is two questions, a full evidence trail, and one focused diff.

The suggestion text was checked byte-identical against real Click, side by side, on the same inputs.
