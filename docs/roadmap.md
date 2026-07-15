# norfolk-path — build roadmap (how we finish v1)

Strategy doc written at Chris's request: how to move from "impressive world
previews" to a **finished, playable v1**, and how the storyline/content work
slots in. Synthesizes a cited research pass on finishing small solo RPGs (see
Sources) with our actual constraints. Companion: `docs/pack-arrival.md` (the
morning checklist once the paid art lands).

## Where we actually are (honest snapshot)

- **Playable today:** the walking skeleton — a placeholder island, two players
  walking, one shop with a proximity line, a chicken. Verified in-browser.
- **Designed but NOT playable yet:** the whole enriched world (cove-3 variants
  with farmland/animals/props). It lives only as preview images + ASCII sources.
  **The live game still has the old placeholder map.**
- **The gap:** we've done ~4 rounds of *previewing*. The highest-value next move
  is to **land a chosen world into the actual game** and then build the
  remaining v1 systems. Previewing more has diminishing returns; playing it does
  not.

## The one rule that matters most: finish small

The research is unambiguous: the thing that kills a solo first game is **scope
creep + perfectionism**, not lack of skill — nobody's there to veto "just one
more feature." Adopt these verbatim:

- **"If a player can beat your game without crashing it, it's shippable."**
  (Derek Yu.) That's the v1 bar. We already have a beatable path spec'd —
  protect it, reach it early.
- **Never build an "engine" for a one-level game.** The specific temptation here
  is building *a dialogue system* or *a combat framework* instead of *the
  dialogue* and *the fight*. Hardcode the level and its handful of lines;
  generalize only the second time you need something.
- **Aim for completion, not perfection.** Timebox polish.

## Build sequence (revised per the research)

Ordered so there's a **beatable, demoable build as early as possible**, the
riskiest web-specific unknown (save) is validated with buffer time, and the most
"engine-tempting" piece (combat) sits in the middle where the game is still
simple. Each step leaves the game playable.

1. **Land the world in-engine** *(next; unblocks all placement)*
   Apply the chosen cove variant to `island_map.gd`; teach `level.gd`/`main.gd`
   the farmland terrain + every prop/animal symbol. Outcome: walk the *real*
   island in the browser. Biggest visual leap. (Details: `docs/pack-arrival.md`.)

2. **Player-select (1P/2P) + a `Game` autoload for state**
   A tiny menu scene (two options) that sets `player_count` on an Autoload
   singleton, then changes scene into the level. This also gives us the global
   state holder (a few flags: `boss_defeated`, etc.) everything else will read,
   and is the natural place to finally **settle the 2P camera rule**
   (leash / zoom-out / clamp) since 1-vs-2 becomes a real choice.

3. **NPC proximity dialogue — hardcoded lines, no system**
   Generalize the shop's Area2D→label pattern to any NPC: sprite + trigger + a
   line (or a few) held in an **`@export var` string**, exactly like the
   movement constants. The story session writes the *text*; the build session
   wires it — same writer/coder split as the map, WITHOUT a dialogue engine.
   (Research + Godot forums: Dialogue Manager / Dialogic are overkill for a
   handful of lines. A ~20-line home-rolled text box is correct for v1.)

4. **Quest-complete screen + a STUBBED win trigger**
   Build the end scene now and trigger it from a stub (reach the library / a
   debug key) *before combat exists*, so the whole path is **beatable
   end-to-end**. This hits Derek Yu's shippable bar early — from here you always
   have a demoable game.

5. **The boss fight (HP + Attack, real-time, minimal)**
   Simplest that works for ONE fight, per the research: Irene = a body with
   `@export hp` + `@export attack`; player has `hp` + one attack (bump-to-hit or
   one button spawning a short Area2D hitbox); dumb "move toward player, damage
   on contact via a cooldown" AI; `hp <= 0` emits a signal → swap the stub for
   the real win. **No turn queue, no menus, no skills/items** (out of scope).
   Reflavor through Irene's dialogue, not mechanics.

6. **Local browser save — validate on a REAL web export, not the editor**
   This is the piece most likely to work in-editor and silently fail on web.
   Use `user://` + `FileAccess` (a `Resource` or small dict). Web gotchas the
   research surfaced, bake these in:
   - On HTML5, `user://` is IndexedDB, synced **asynchronously** via Emscripten
     `FS.syncfs()`. Modern Godot 4 triggers the sync when a written file is
     **closed** — so **always close the file after writing**, and **don't spam
     saves** (save at events: after the NPC beat, after the boss win), and don't
     save in the instant before the tab closes.
   - Bulletproof alternative for our tiny save (a few flags): write to
     **localStorage via `JavaScriptBridge.eval()`** — synchronous, persists
     immediately; branch web-vs-desktop. Fine for a web-first game.
   - Verify "refresh → progress survives" on the hosted/exported build early.

7. **Polish, then stop.** Movement feel, the duck swap for Ariana, the COOP/COEP
   serve story for a shareable link, a final pass against "SHIPPED means…".
   Timeboxed — resist step 8.

## How the story/build split continues (content, not systems)

The map pipeline worked because the **story session owned intent** and the
**build session owned code**, meeting at a data file. For v1's *content*, the
honest version is smaller than I first sketched:

- **Dialogue is ~5 lines total** (Evan's one line; Irene's ~3 boss lines, already
  drafted in the brief; Ariana's closing line). **Hardcode them as exported
  strings** — the story session still authors the *words*, the build session
  drops them in. That IS the split; it doesn't need a data format or a dialogue
  addon. (Data-driven content earns its keep at many entities, not at N≈5 — the
  research is explicit that building the pipeline here is the tools-trap.)
- **The one place a data file (a Godot `Resource`/`.tres`) IS worth it: the save
  file** — type-safe, one-line save/load, native Godot types. Overkill for
  content, right for the save.
- If v2 ever grows real branching conversation, revisit **Dialogue Manager**
  (Nathan Hoad) — mature and well-regarded — as a *new dependency to ask about*
  then. Not now.

## Division of labor from here

- **Story session** owns: the world brief (done), the handful of dialogue lines
  and boss script (drafted), any new flavor text — authored as words the build
  session pastes into exported strings.
- **Build session (me)** owns: landing the world, the minimal runtime systems,
  wiring content, keeping it exporting + shippable.
- **Chris** owns: aesthetic picks, sourcing art, the engine/playtest/feel loop,
  and the "is it fun / does it ship" call.

## Risks / scope discipline

- **Preview-vs-play drift** (our current risk): keep landing things in the real
  game; don't let previews outrun the build.
- **The tools-trap**: hardcode dialogue + combat. No dialogue engine, no combat
  framework, no turn system. HP + one attack is the *whole* combat system.
- **Web save**: test persistence in the *exported* build early; mind the
  `syncfs`-on-close behavior; consider localStorage for the tiny payload.
- **The web black-screen gotcha**: Godot 4 web + threads needs COOP/COEP
  (SharedArrayBuffer) — we already chose threads-OFF for Slice 1 to dodge this;
  revisit only if we turn threads on.
- **Art re-work**: the paid pack changes buildings, so don't hand-wire buildings
  until it's committed (see `docs/pack-arrival.md`).

## Immediate next steps (morning)

1. Chris picks a `cove3-rich` variant and commits the paid pack (`__MACOSX`
   cleaned).
2. Build session runs `docs/pack-arrival.md`: distinct shop/library buildings +
   a horse, re-render, then **apply the world live** (step 1 above).
3. Proceed down the build sequence — player-select + autoload next, then the
   hardcoded NPC dialogue.

## Sources (from the research pass; some hosts were proxy-blocked, noted there)

- Derek Yu, *How to Finish a Game* / "want to be an indie? learn to finish
  games" (Game Developer) — the shippable-bar + death-loop framing.
- *Scope Creep: The Silent Killer of Solo Indie Game Development* (Wayline);
  *Killing Scope Creep and Finishing Your Game* (GameMakerBlog).
- Godot docs — *Singletons (Autoload)*; *Exporting for the Web*.
- Godot issue #39643 + PR #42266 — HTML5 save persistence / `syncfs`-on-close;
  Emscripten `FS.syncfs` discussion.
- GDQuest / alegrium — *Resources vs JSON* for save data.
- Dialogue Manager (Nathan Hoad); Godot forum consensus that Dialogic/Dialogue
  Manager are overkill for simple games.
- GameDev Academy dialogue-box + beginner melee/combat tutorials (bump/one-button
  real-time boss pattern).

**Uncertainty flags from the research:** verify `syncfs`-on-close against our
specific Godot 4.7 build with a real refresh test; the Derek Yu points came via
a mirror (primary page 403'd); real-time vs turn-based combat is a judgment call
(real-time is simpler to code, turn-based avoids twitch input but costs more).
