# The testing loop

How this project tests itself, round after round. Three layers, cheapest first;
each catches what the others can't. Written after playtest round 1 + map audit
round 1 proved the shape works.

## Layer 1 — automated gates (every push, zero effort)

| Gate | Workflow | Catches |
|---|---|---|
| GDScript lint | `ci.yml` (gdformat + gdlint) | style/syntax drift |
| Static checks | `ci.yml` → `tools/check_symbols.py`, `check_assets.py`, `check_character_layers.py`, `check_map_rules.py`, `check_levels.py` | missing assets, unhandled map symbols, broken character layers, map-rule regressions (floating beehives, orphan doorsteps, singleton clones), connected-world breaks (dangling transitions, unwalkable arrivals, doorless interiors, uncovered talkers) |
| Map composites | `visual-review.yml` → artifact | layout/composition drift, reviewable by eye |
| **Browser playtest bot** | `playtest.yml` (push to main + manual) → `playtest-<sha>` artifact | build boots, canvas renders, input works, core loop produces sane frames; **plus, live on the real build:** a cottage door loop (transition + fade + return), a seeded v3 save that must migrate to v4 in place (Continue routing, appearances kept), and a full dialogue open/advance/close — 19 screenshots, console errors surface in the job log |

The bot's first assertion is load-bearing: the title-menu highlight must move on
a keypress or the run fails — a green run genuinely means "input reached the
game." Its job log is worth reading even when green (run #1 caught a sprite
frame-index bug as console spam no human playtest had noticed).

## Layer 2 — local Godot round-N (feel, timing, live eyes)

A Godot-capable session (Chris's Windows machine) runs the game for what
automation can't judge: combat feel, timing windows (roll i-frames), animation
readability, and anything the current round's fixes flagged "needs live
re-verify". Driver scripts live in `tools/playtest/` (PostMessage input +
PrintWindow capture — see its README for the recipe and caveats).

Deliverable per round, as a **docs-only PR**:
- `docs/playtest-findings.md` — one entry per issue:
  Area / Severity (blocker|bug|polish) / Observed + repro / Expected / Screenshot.
- Screenshots under `docs/playtest/round-N/`, descriptive filenames.
- Honesty rules: **NOT VERIFIED beats guessed**; a test not run is marked not
  run; retract earlier misreads explicitly.

## Layer 3 — cloud triage + fix slice

The cloud session merges the findings PR, cross-checks every finding against
code and composites, and appends a **triage table** to the findings doc:
verdict (CONFIRMED / NOT A DEFECT with evidence / CORRECTED) + action
(FIXED / DEFERRED with reason / DOCUMENTED as intended). Fixes ship as a PR —
one logical commit per finding, before/after composites for anything visual —
and each fix that automation can't fully verify goes onto the next round's
live checklist. Nothing merges without Chris.

## The cycle

```
fix slice merges to main
  └─ deploy-web ships it + playtest bot screenshots it   (Layer 1, automatic)
       └─ local round-N when live eyes are needed         (Layer 2, on demand)
            └─ findings PR → cloud triage → next fix slice (Layer 3)
```

Roles: **local session** = engine, eyes, timing · **cloud session** = triage,
fixes, CI/deploy, tooling · **Chris** = merges, design decisions, anything
ambiguous (ambiguity produces a question, never a guess).

## Adding a new check (how the loop improves itself)

When a round surfaces a bug class (not just a bug), promote it: encode the rule
in `tools/check_map_rules.py` (map data) or `tools/check_assets.py` (assets/
config) so CI fails on recurrence. The map audit's floating-beehive and
orphan-doorstep findings are the template — found once by vision, enforced
forever by CI.
