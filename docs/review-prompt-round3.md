# Full-review prompt — post-round-3 beta

Paste everything below the line into a fresh session with a strong model when
you want a full outside critique of the game. It hands over the project
context, where to look, and the shape of feedback that is actually useful.
Update the "state as of" line if you run it much later.

---

You are reviewing **Norfolk Path**, a personal learning project: a top-down
pixel-art fantasy RPG built in **Godot 4.7**, playable solo or local 2-player
on one keyboard, exported to HTML5. It exists so I can learn the engine
end-to-end and end up with a game that is genuinely fun to play — not a
commercial product. I want your honest, structured critique of it as a GAME
and as a CODEBASE.

## How to look at it

- **Play it**: https://norfolk-path.vercel.app (best on a desktop browser;
  ultrawide is a first-class target). 1P: WASD moves, G sword, H bow
  (hold to charge, release to fire), C roll, E talk, Esc pause. 2P: arrows +
  numpad 1/2/3, Enter talk. Key remapping lives in the pause menu.
- **Read it**: repo `chris-suryo/norfolk-path`. Orientation: `PROJECT.md`,
  then `docs/level-design.md` (how the ASCII-map → baked-ground pipeline
  works), `docs/playtest-findings.md` (rounds 1 and 3 of playtesting with
  triage), `docs/testing-loop.md` (the headless verification harness).
  Code entry points: `scripts/main.gd` (scene orchestrator),
  `scripts/level_registry.gd` (the connected world), `scripts/player.gd`,
  `scripts/enemy.gd` + subclasses, `scripts/encounter_manager.gd`,
  `tools/bake_interior.py` and `tools/gen_prop_table.py` (generators),
  `tools/playtest/ci_driver.py` (the pixel-asserting browser bot).

## State as of this prompt (July 2026)

Two connected outdoor levels (valley + cove) with 8 enterable interiors
including a library; dialogue system with placeholder lines awaiting a story
pass; sword + charge-bow combat, 6 enemy types + a 2-phase boss, checkpoints
and co-op revive; character creator with persistent appearances (save v4);
dark-panel UI with key remapping. Known deferred items: audio (none exists),
map top/bottom dead bands, difficulty selector, walkway network polish.

## What I want from you

Go section by section. For each: what works, what does not, and the ONE
change with the highest fun-per-effort. Be specific — name files, screens, or
moments. Do not pad; if a section is fine, say so in a sentence.

1. **First five minutes.** Cold start on the live link: title → creator →
   village. Where does a first-time player get confused,
   bored, or lost? Is it clear what to do and where to go?
2. **Combat feel.** Sword timing/reach, charge bow risk-reward, roll, enemy
   variety and readability, boss phases, difficulty curve across the five
   encounter areas. Is 2P co-op actually more fun than 1P?
3. **World and exploration.** Does the valley reward wandering? Are doors,
   interiors, the cove, and the library worth entering? What would make the
   map feel alive rather than decorated?
4. **UI/UX.** Menus, HUD, dialogue box, creator, remap screen — legibility,
   navigation, consistency, and anything that feels amateur.
5. **Story scaffolding.** The dialogue ids and placeholder lines
   (`scripts/dialogue_data.gd`, `docs/story-handoff.md`): is the structure
   ready for a real story pass? What is missing for even a thin quest loop?
6. **Codebase.** Architecture (registry-driven levels, generated prop table,
   baked grounds, data-driven enemies), test/verification strategy, and the
   top 3 refactors that would pay off before the project doubles in size.
   Flag anything fragile you can see breaking soon.
7. **The build/verify loop.** CI checkers + the playtest bot
   (`.github/workflows/`, `tools/check_*.py`): what real regressions would
   slip through today, and what single check would catch the most?
8. **Missing entirely.** Audio, juice, onboarding, accessibility, save
   slots — rank what absence hurts the most right now.

Finish with: (a) the five highest-impact changes overall, ranked, each with a
one-line why; (b) one thing you would NOT change because it is already
carrying the game.
