# Rulebook — Pocket Tasks port

Decisions any two implementers could make differently, decided once. Cite by ID;
do not edit inside loops.

- **R-001 Response envelope shape.** Every `/interact` success returns exactly
  `{dom:{count,empty,filter,rows,theme,title}, export, focus, liveRegion}` with keys as
  observed. `dom.title` is the constant "Pocket Tasks". No extra keys.
- **R-002 Active count.** `dom.count` = number of tasks with `done==false`, independent of
  the current filter.
- **R-003 Empty message.** `dom.empty` = "No tasks here" iff the *filtered* row list is
  empty; otherwise JSON `null`.
- **R-004 Rows vs export.** `dom.rows` is the filtered view (all/active/done) in insertion
  order. `export` always serializes *all* tasks as `"[ ] text\n"`/`"[x] text\n"`, filter-independent.
- **R-005 Accessible name.** Row `ariaLabel` = `"Mark <text> done"` when active,
  `"Mark <text> active"` when done. `checked` mirrors `done`.
- **R-006 Focus model.** Focus is session state changed only by: add & reset & Escape →
  `new-item`; toggle/delete success → `task-<index>`; filter success → `filter-<value>`.
  All other outcomes (errors, not-found, unknown action, invalid filter, Alt+D, unknown
  shortcut) leave focus unchanged.
- **R-007 Add validation.** `text = (action.get("text") or "").strip()`; empty →
  live "Task cannot be empty", no append; else append and live "Added <text>". Focus →
  new-item in both cases.
- **R-008 Index parsing.** `index = int(action.get("index", -1))`. Missing → -1 → not found.
  Non-numeric string → `int()` raises ValueError (propagates to the 400 error contract).
  In-range → act; out-of-range/negative → live "Task not found", no state/focus change.
- **R-009 Filter/shortcut vocab.** filter value must be in {all,active,done}; shortcut key in
  {Alt+D,Escape}; anything else → live "" and no change. Alt+D toggles theme (live
  "Dark theme"/"Light theme"); Escape sets filter=all + focus new-item + live "Reset view"
  and does NOT change theme.
- **R-010 Error contract.** Transport catches ValueError (incl. JSONDecodeError),
  AttributeError, TypeError and returns HTTP 400 `{"error": type(e).__name__}`. Success is
  200. Unknown path / non-POST /interact → 404. This *reproduces* the observed source error
  surface for parity; see D-CAND-1 for the hardening note (not applied, to preserve parity).
- **R-011 Session key.** `body.get("session")` is the store key; may be `None` (missing field)
  which selects a shared default bucket, matching the observed source.
- **R-012 No branding/assets.** Reproduce only functional strings observed via the API
  ("Pocket Tasks", live-region messages). No logos, styling, or trade dress — none were
  observed and none are in scope (functional-replication fast path).
