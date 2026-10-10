# Glossary

These are the words Portme uses in [SKILL.md](../SKILL.md) and the reference docs. Each one is defined here so the rest of the docs can stay short.

- **Judge.** The check that says the source and the port behave the same. It might be a test suite, a side-by-side harness, saved scenarios, or (in Quick mode) a written checklist.
- **Referee.** Any mechanical check that grades the work: a compiler, a schema check, a diff, or a test. An agent's opinion is not a referee.
- **Gate.** A stop. The agent shows evidence and waits. Your message is what starts the next phase.
- **Manifest.** The on-disk list of porting units, used in Standard and Large-scale. A unit is done when its output exists and its check passes. Quick mode has no manifest.
- **Authorization bundle.** A SHA-256 hash of the exact manifest bytes plus the names and bytes of the files the checks depend on. Checks run only against a bundle you approved. If those bytes change, the Phase 1 gate opens again. Quick mode has no bundle.
- **Rulebook.** Decisions that two workers could make differently, written down once. When the same mistake keeps showing up, you change the rulebook and regenerate the batch, instead of patching each copy.
- **Fan-out.** Several workers at once. If the tool cannot do that, the same steps run one unit at a time.
- **Contract.** The written list of what "behaves the same" means, before any port code is written.
