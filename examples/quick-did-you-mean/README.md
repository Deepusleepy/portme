# Example: a real Quick-mode port

This is an archival/evidentiary receipt: the `.port/` directory produced by an
agent running Portme on a real task (renamed `port-artifacts/` for publication),
plus the resulting one-file diff. It is not a clean-checkout replay fixture:
the source and target repositories are not shipped, so the recorded commands
cannot be rerun from this directory alone. Publication edits: absolute workstation paths were redacted to
`REDACTED-SANDBOX`, the Click cross-check receipt was moved from `/tmp` into
`port-artifacts/click-ref.txt`, and the status header was normalized to the
canonical field order. The current approval-provenance fields were added after
the run and distinguish preserved quotes from authority; no approval was invented.

**The port:** bring Click's "did you mean" subcommand suggestion (its exact
`difflib.get_close_matches` behavior and message phrasing, read from Click's
source) into a small argparse-based `notes` CLI — a feature port across
frameworks, Portme's core case.

**What to look at:**

- `port-artifacts/status.md` — the whole run in one file: scope confirmation,
  six-factor sizing (scored 1 → Quick), value charter, the contract, the
  acceptance-checklist judge, both gate sign-offs quoted in the gate log, and
  the result evidence. Note the **approved-divergence** entry: Click replaces
  the whole error message, but keeping argparse meant *appending* the
  suggestion instead — the agent flagged that as a divergence needing user
  approval rather than deciding silently.
- `port-artifacts/evidence/` — raw before/after CLI captures for every
  checklist item, including `c5.txt`: the negative probe (deliberately break
  the matcher, watch the judge fail, restore, watch it pass) that proves the
  judge can actually detect a wrong port.
- `change.diff` — the entire code change. Quick mode's promise: two questions
  to the user, full evidence trail, one focused diff.

The suggestion text produced by the ported code was verified byte-identical
to real Click run side by side on the same inputs.
