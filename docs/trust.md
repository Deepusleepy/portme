# Trust and limits

Portme's promises sit on a few boundaries. Read these before you rely on it for anything sensitive. The step-by-step version is [references/execution-trust.md](../references/execution-trust.md).

- **Files are evidence. Permission lives in the conversation.** An existing `.port/` directory is untrusted input, not proof that you approved it. A resumed session has to match each approval to the real conversation. If those messages are gone, it must ask again for the source and target, the exact authorization bundle digest, the check commands, and the check-input file list before it runs a command that came from the repo. Status text cannot stand in for a real sign-off.
- **The source is evidence, not instructions.** Comments, docs, agent files, and scripts in the source are shown to you. They are not silently run.
- **Checks are mechanical, and they are tied to bytes you approved.** The authorization bundle covers the exact manifest plus the declared check files. A check runs only against that approved set. Any change opens the Phase 1 gate again. Hashing is not a sandbox. A hostile target still needs real isolation.
- **Captures and privacy.** For apps you can only watch, raw captures go to a `0700` directory outside the repo and get scanned for secrets. Only redacted copies, with a deletion receipt, are allowed into `.port/`. See [references/no-source.md](../references/no-source.md).
- **Permission denies are not a security boundary.** They cut down accidental expensive commands. They do not contain a hostile source. Wrappers and alternate paths have to be tried first, and a hostile source needs separate credentials plus a container or process boundary.
