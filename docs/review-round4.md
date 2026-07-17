# Review — Round 4 (outside pass: game + codebase)

**Reviewed:** main @ `dc11d4a`, 2026-07-16/17. **How:** ~1h driven native play
(Godot 4.7 editor binary, PostMessage input, PrintWindow capture — the round-1
technique), static review of every baked ground PNG, CI run forensics via `gh`
(including downloaded bot screenshot artifacts), a full code read, computed
map forensics, and a multi-agent analytical pass (mechanics / map / story /
architecture / CI) in which every finding was re-traced by an independent
verifier told to refute it. A separate adversarial pass was then pointed at
**this review's own conclusions** — it corrected one of my findings and
surfaced two critical bugs nothing else caught (R4-43/44); I re-verified both
against the source myself. The live Vercel link could not accept input on the
review machine (browser input is broken there — a machine issue, not a game
issue), so play evidence is native-from-main.
**Provenance tags:** `[PLAYED]` seen live this session · `[CODE]` traced in
source · `[RENDERED]` judged from committed assets · `[CI]` from workflow-run
forensics · `[NV]` not verified, flagged for the human pass.
**Screenshots:** `docs/playtest/round-4/` (01–62 = this session's play;
`bot-17/18/19-*.png` = downloaded CI-bot evidence).

**Caveat on feel:** a scripted driver cannot judge game-feel. Feel claims below
are either mechanical facts (frame data, code constants) or flagged `[NV]` for
Chris's 25-minute protocol in Appendix A. Everything else is evidence-backed.

**The headline finding** (found in the first two minutes of play, and it shapes
several sections): **the dialogue system is completely broken in every
editor/debug run on current main.** `scripts/dialogue_box.gd:18` still types
`_panel` as `NinePatchRect`, but the round-3 dark-panel restyle (`0489e0c`,
PR #18) changed the node to `type="Panel"`. In debug the typed assignment
fails, `_ready()` dies mid-function, and the result is: a permanently visible
empty dark panel covering the bottom of the screen, a permanently visible
"E - TALK" prompt from boot, every NPC mute, boss taunts rendering as
near-invisible dregs inside the dead panel, and one `SCRIPT ERROR` spammed to
the console per input event (465 lines in a few minutes of play). The release
web export skips the typed check, so the deployed build likely works — which
is exactly why nothing caught it (full chain in §7). One-word fix.
`[PLAYED]` (shots 09–12, 60; stderr log) `[CODE]` `[CI]`

---

## Triage board — the actionable list

*Grouped by effort, not by section. Ids link to the detail below; `B-` ids are
in Appendix C (all adversarially verified), `R4-` ids in the numbered sections.*

**Do first — minutes each, high payoff**
| Id | Fix | Why now |
|---|---|---|
| R4-01 | `dialogue_box.gd:18` `NinePatchRect` → `Panel` | One word; restores every NPC + un-breaks the dev build |
| B-27 | Boss deals no contact damage — her override never calls `_try_contact_damage()` | You can stand inside the final boss safely |
| B-16 / R4-39 | Big red slime has no `aggro_radius` override (default 0 = always awake) | **One line.** It walks 1,488px from level load and lands in the camp at ~93s — overloading the hardest fight *and* emptying area 3 |
| R4-10 | Ranged aggro (bowman 130 / mage 140) exceeds the 128×72 half-view, and `_shoot_cd` starts at 0 | Shooters wake and fire from **off-screen with no telegraph** — this is what kills players unfairly |
| B-11 | Irene stays red-tinted forever after the first hit | Her override skips the base modulate reset |
| R4-30 | Delete dead `area_enemies` lines (`enemy.gd:196-197`) | Flagged a round ago, still there |
| §7 QW2 | Make the bot's in-page JS errors fatal (`ci_driver.py:338`) | ~4 lines; turns a silent failure class red |

**Do this week — hours each**
| Id | Fix | Why |
|---|---|---|
| **R4-43/44** | **Scene-crossing state has no owner** — `_apply_resume` early-returns before clearing beaten areas *and* before waking the boss | **Every door round-trip resurrects the whole gauntlet; visiting the library turns Irene into a statue.** Fires every playthrough (top-5 #2) |
| **Cluster A** | Make the win sequence unbreakable (B-01…B-06). **Start with one line:** `get_tree().paused = false` at the top of `Game.change_scene` | Same root cause as above. 5 CONFIRMED ways to lose the quest-complete screen — the project's own definition of SHIPPED. Chain personally re-traced |
| R4-06/07 | **Add sound**; make the *existing* flash readable before adding hit-stop | The one untouched engine subsystem, and the cheapest feel win (top-5 #3) |
| B-07 | Remapping one key deletes every alias on all 16 actions | Silent data loss on a shipped feature |
| B-10 | Boss `take_damage` ungated by `_active` — snipeable from outside her wake line | Free, silent win — skips the entire fight |
| R4-35 | Ranged enemies lack corner steering; bombschroom ignores knockback | Two live bugs from one copy-paste |
| B-12/B-13 | Piercing projectiles hit both players; distant-killer death self-revives free | Fix before judging whether 2P is fun |
| R4-08 | `respawn_at` leaves a wrong-costume idle frame | Visible every death |
| R4-31/32 | Pond villager states the premise; win screen's "Ariana" label gets a real line | 2 lines close both story holes, no new systems |
| R4-42 | Make the chest a talker (4 lines in `_spawn_talkers`) + move it & the windmill into the 76-tile void | The only off-road reward in the game — currently the chest is a decal you can't open |
| R4-20 | Pause value-rows ignore Left/Right (creator implements it, pause doesn't) | Two menus teach contradictory idioms |

**Before the project doubles — the structural three**
| Id | Refactor | Kills |
|---|---|---|
| §6 #1 | Enemy template-method + one `Projectile` script | The copy-drift class (already produced R4-35's two bugs) |
| §6 #2 | Data-driven encounter areas, string keys, `{level, key}` checkpoint | The `BOSS_ID` renumber class; unblocks cove encounters |
| §6 #3 | CI headless **debug** scene-smoke + registry↔map asserts | The typed-cast class (R4-01) *and* the door-coordinate class (R4-37) — both have already shipped bugs |

**Design decisions only Chris can make**
| Id | Question |
|---|---|
| R4-05 | Dying is the only heal (`_hp` is written in exactly 3 places: ready, damage, respawn). Add a real healing mechanic, or embrace death-as-reset? |
| R4-38 | The bow is 1.875 DPS vs the sword's 10.0. Buff the full draw, slow the sword, or accept the bow as a pure-range tool? |
| R4-13/14 | 8 interiors, 0 contents. One findable thing per room, or fewer/richer rooms? |
| R4-23 | Add story flags + gated dialogue (enables a quest loop), or stay ambient-flavor? |
| R4-13 | 8 rooms is a day of content. Do only the library now, or all eight? (The adversarial pass says: only the library, until the boss is worth walking to.) |
| Appx A | The 25-min feel pass — the `[NV]` verdicts (2P fun? boss phases? roll?) are yours |

---

## 1. First five minutes

**What works.** Cold boot to gameplay is fast and friendly: title (dressed
backdrop, campfires, controls summary, version string) → 1P/2P → creator →
village in under a minute of decisions (shots 01–09). The subtitle "A CO-OP
PATH TO IRENE" does real work — it names the goal and the tone. The creator is
a genuine hook: live preview, arrows-or-mouse both work `[PLAYED]` (shots
04–05), Randomize invites one more roll, and the appearance persists into the
save. The village at spawn is the art at its best — lamps, chickens, walkway,
well (shot 09).

**What doesn't.**
- **R4-01 · critical · debug-only:** the dialogue break above means a
  first-time *editor* run — which is how Chris demos it locally — starts with a
  dead panel eating ~15% of the screen and a lying "E - TALK" prompt.
  `[PLAYED]`
- **R4-02 · major:** nothing in the world re-states the goal. The subtitle is
  the only "go east, find Irene" signal; at spawn there is no NPC beat, sign,
  or camera nudge pointing east. With dialogue working (web), villager lines
  hint at it — but only if you happen to talk. `[PLAYED]` `[CODE]
  dialogue_data.gd`
- **R4-03 · major:** the first enemies read as decor and don't stay put. Area-1
  slimes sit motionless like bushes until aggro (shot 14 — two of them posed
  next to benches at the well), then chase indefinitely: they followed me INTO
  the village, ground my HP down through five unnoticed contact ticks, and one
  spent the fight overlapping the farmer villager, who doesn't react (shots
  15–18). First blood in this game is a mugging by furniture. `[PLAYED]`
- **R4-04 · minor:** at true 640×360 the Pixelify subtitle/controls lines are
  crunchy ("CO-OP" ≈ "00-OP", shot 01); legible at larger windows (shot 53).
  `[PLAYED]`

**The ONE change:** a 10-line opening beat — on first spawn, auto-open one
dialogue ("Irene's got Ariana. The road east goes to her library.") and light
the first road-east beacon. Cheapest possible quest hook; reuses systems that
already exist. *(Depends on R4-01's one-word fix.)*

## 2. Combat feel

*Mechanical facts verified; feel verdicts flagged for the human pass.*

**What works.**
- The **charge bow is the best-*designed* system in the game** `[PLAYED]`:
  hold-to-draw with a readable side-profile draw pose (shot 25), arrow visibly
  in flight (shot 26), damage/speed scaling with hold time, and
  slow-walk-while-drawing (kiting identity) — a real risk-reward loop.
  `[CODE player.gd:218-316]` **Its numbers betray it** — see R4-38.
- Sword commitment is a defensible design: rooted for the swing, active-frame
  window, per-swing hit dedupe, visible white arc (shot 17). `[CODE
  player.gd:284-292]`
- The checkpoint spine works: progress-based advance, beacon glow + toast +
  autosave (shot 32), survivors-stay-dead rearm on wipe, boss-only full reset.
  `[PLAYED]` `[CODE encounter_manager.gd:202-289]` **And the camp checkpoint
  placement is genuinely well-tuned** — 260px from the nearest skeleton vs its
  110px aggro; the code comment's claim checks out to the pixel. `[CODE]`
- Enemy variety is real (slime/red slime/skeleton/bowman/mage/bat/big slime/
  bombschroom/2-phase boss) and mostly on ONE data-driven script — adding more
  is cheap. `[CODE]`
- **The speed table is coherent design:** everything is outrunnable (slime
  0.43× the player, skeleton 0.57×, boss 0.23×) *except* the bat at 1.03× —
  and the bat has 1 HP. The one enemy that can catch a fleeing player dies to
  a single swing. That's a deliberate-looking, good rule. `[CODE]`
- **Roll is honest:** 40% iframe uptime cap, and roll-spam travel is only 20%
  faster than walking — no movement exploit hiding in it. `[CODE]`

**What doesn't.**
- **R4-05 · critical (design):** **dying is the only heal in the game.**
  Checkpoint advance saves but does not heal (`encounter_manager.gd:205-222`);
  `respawn_at` restores full HP (`player.gd:352`); no pickup, rest, or regen
  exists anywhere. Since checkpoints are monotonic and killed enemies stay
  dead, the *optimal strategy after any scrape is to walk into an enemy and
  die* — the run costs a beacon walk-back, nothing else (boss fight excepted).
  I "used" this exploit three times tonight without meaning to. `_hp` is
  written in exactly three places in the whole codebase (`_ready`,
  `take_damage`, `respawn_at`) — there is no fourth. In **2P it's worse**: the
  clear-to-revive rule means "let P2 die, walk 130px away" is a free full heal
  on a near-zero-cost loop (B-13). `[CODE]` `[PLAYED]`
- **R4-06 · critical (presentation) — corrected:** my first draft said "death
  is a silent teleport with no animation." **That was wrong, and the error is
  instructive:** a 6-frame death collapse *does* play over `DEATH_DURATION =
  0.7s` (`player.gd:254-260`), and a red/white hurt flash *does* pulse at 20Hz
  (`player.gd:246-251`). My screenshots were 700ms apart — I straddled the
  entire animation and concluded it didn't exist. A scripted driver cannot
  review feel; this is the proof. **The accurate finding is narrower and
  still serious:** the feedback that exists is *too weak and too local to
  read* — a 0.25s flash on a 64px sprite your eyes aren't on, a 0.7s collapse,
  and a corner bar. No hit-stop, no shake, no sound, no card, no death
  counter, and the fade rect that exists is never invoked on death. **Fix what
  is there before adding more** — verify the flash reads at all first.
  `[PLAYED, corrected by CODE]`
- **R4-07 · major:** taking damage is nearly illegible in the heat of it. The
  hurt flash + knockback exist `[CODE player.gd:246-251]` but the only HP
  readout is a small corner bar; I lost 85% HP across a stroll without
  noticing (shots 14–16). No hit-stop, no screen shake, no sound (none exists).
  `[PLAYED]`
- **R4-08 · major:** post-respawn, the idle player renders a wrong-costume
  frame (tan top/orange pants vs saved blue/black — shot 44 vs 48) until first
  movement. Root cause: `respawn_at` → `_enter_normal()` resets state but
  never resets the sprite frame, leaving the death-row frame on the modular
  sheets. `[PLAYED]` `[CODE player.gd:350-360]`
- **R4-43 · critical — NEW, and it fires on every playthrough:** **every door
  round-trip resurrects the entire gauntlet.** `setup()` spawns *every* area's
  enemies unconditionally (`:60-61`), then calls `_apply_resume()`, which
  early-returns at `:188` on `not Game.resume_requested` — **before** the loop
  at `:193-195` that marks already-beaten areas cleared. Every door/edge
  crossing sets `resume_requested = false` (`level_transition.gd:73`). So:
  clear the camp, step into a cottage, step out — the whole camp is alive
  again. Only a *Continue* from the title clears prior areas. Found by the
  adversarial ranking pass; **I verified the chain myself.** `[CODE]`
- **R4-44 · critical (same root cause, worse):** the *same* early-return skips
  `:198-199` (`if Game.checkpoint >= BOSS_ID: _activate_area(BOSS)`) — and
  `_update_checkpoint` can't recover it, because `reached > Game.checkpoint` is
  false once you're at 4. **The geometry makes this the intended path, not an
  edge case:** the boss checkpoint centre is cell (156,26) and the library door
  is at (161,17) — checkpoints are x-only, so *reaching the library at all*
  pushes you past 156 and wakes her. Walk to the library (the quest's
  destination), step inside, step out → **Irene is a permanent statue** you can
  kill for a silent win, having never fought a boss. Verified. `[CODE]`
- **R4-09 · major:** enemies have no leash. A skeleton chased me from the
  east gauntlet across the bridge to the village side and was still there a
  scene later (shot 52); slimes wander the village gardens permanently once
  aggroed (shots 58–59). Combined with R4-03, the peaceful half of the map
  stops being peaceful after one bad pull. `[PLAYED]`
- **R4-10 · major — RESOLVED by the numbers, and it's not my reflexes:**
  **ranged enemies wake and fire from off-screen with zero telegraph.** The
  camera shows 256×144 world px (half-view 128×72), but the bowman's aggro is
  130 and the mage's is **140** — both exceed the horizontal half-view and
  *double* the vertical. Worse, `_shoot_cd` initialises to `0.0`, so a waking
  shooter fires **on its very first awake frame** — no wind-up, no tell. Their
  bolts also outrange your bow (mage 360px, bowman 300px vs your 240px). That
  is why I died twice in ~2s "to a skeleton": a mage I could not see was
  landing 2-damage bolts — a third of the HP bar per hit — from off-screen.
  Area 1's bowman is billed in code as "the player's first taste of dodging
  projectiles"; it sits outside the vertical half-view. `[CODE
  ranged_enemy.gd:19,38-40; enemy_mage.tscn; follow_camera.gd:18]`
- **R4-38 · major (design):** **the bow is a 5.3× trap, not a choice.** Sword
  = 4 dmg ÷ 0.40s = **10.0 DPS**. Full-draw bow = 3 dmg ÷ (0.7 cooldown + 0.9
  draw) = **1.875 DPS**. The most interesting mechanic in the game is strictly
  the worst way to deal damage — the charge is pure ceremony unless you need
  the range. Every enemy except the skeleton (5 HP), big slime (10) and Irene
  (36) dies to **one** sword swing, so there's rarely even a reason to kite.
  Fix is a knob: raise full-draw damage (a 6-dmg full draw ≈ 3.75 DPS still
  loses to the sword but buys the range trade honestly), or slow the sword.
  `[CODE player.gd:50,85,89-98]`
- **R4-39 · major:** **the big red slime walks 1,488 px across the map from
  level load.** It ships with no `aggro_radius` override → default 0 → always
  awake (`enemy.gd:158`). At 16 px/s it leaves its area-3 post at cell (138,26)
  and arrives in the **camp — the game's hardest fight — at about the 93-second
  mark**, simultaneously overloading area 2 with a 10-HP/2-dmg tank and gutting
  area 3 down to two bats guarding nothing. This is the slime that wandered
  into my village (shots 14–18) *and* the one the CI bot "talked" to in the
  forest. **One missing line in `enemy_slime_big.tscn`.** `[CODE]` `[PLAYED]`
  `[CI]`
- **R4-40 · minor:** the bombschroom's advertised dilemma loses by 8 pixels.
  Its docstring promises "get close enough to hit it and you're inside the
  blast" — but sword max reach is **30px** and `detonate_radius` is **22px**,
  so you can stand at 25px and one-shot it (3 HP < 4 dmg) without ever
  triggering the wind-up. `[CODE bomb_enemy.gd:8-25, player.gd:53]`
- **R4-41 · minor:** the "deliberately weightier movement" in `player.gd`'s
  docstring *and* in PROJECT.md's v1 scope isn't in the numbers: 0.12s to top
  speed, 0.075s to stop, a 2.25px slide. That's snappy, not weighty — the
  stated design goal and the shipped constants disagree. `[CODE]`
- **R4-11 · minor:** entering the boss from a checkpoint-4 Continue drops you
  into the fight with a book already airborne and the opening taunt firing
  instantly — no arena threshold beat (shot 60). `[PLAYED]`
- **R4-12 · minor:** facing north, the bow draw is invisible (no overlay,
  no indicator — shot 23 vs 25); there is no charge meter anywhere. `[PLAYED]`
- **From the overnight bug audit (full list + traces in Appendix C), the
  combat-integrity subset:** Irene deals **no contact damage** — hugging her
  is safe (B-27); the bow outranges every aggro radius, so any gated enemy
  can be sniped risk-free without ever waking (B-22); the area-3 big slime
  has no aggro gate and marches off its post from scene load (B-16 — this is
  the slime the CI bot met in the forest); and after any door round-trip at
  checkpoint 4 the boss spawns inert and can be killed for a free, silent
  win (B-09/B-10). All CONFIRMED by adversarial trace. `[CODE]`

**2P co-op:** not driven this session (P2 sim was possible but would have been
more blind flailing — deferred to the human pass, Appendix A §D). Code facts:
midpoint camera with no leash (walk-apart is a known, deliberately unsolved
problem), clear-to-revive at full HP with an enemy-radius gate.
`[CODE midpoint.gd, encounter_manager.gd:242-253]` **Is 2P more fun than 1P —
`[NV]`, Chris's call** — but four CONFIRMED co-op correctness bugs should be
fixed before judging it: piercing projectiles hit both players, distant-killer
deaths self-revive for free, downed bodies soak shots, and a downed player can
pause the fight by opening dialogue (Appendix C cluster C).

**The numbers** *(scene overrides win over script defaults; 60Hz physics.
`player.tscn` overrides nothing — every player constant is a script default.)*

| | HP | speed | contact dmg | aggro | sword TTK | bow TTK | your TTD 1v1 |
|---|---|---|---|---|---|---|---|
| Player | 6 | 60 | — | — | — | — | — |
| Slime | 3 | 26 | 1 | **0 ⚠** | 0.4s | 0.9s | 4.0s |
| Skeleton | 5 | 34 | 2 | 110 | 0.8s | 2.5s | **2.0s** |
| Bowman | 4 | 28 | 1 | **130** | 0.4s | 2.5s | 5.0s |
| Mage | 3 | 22 | 1 (bolt **2**) | **140** | 0.4s | 0.9s | 5.0s |
| Bat | 1 | **62** | 1 | 90 | 0.4s | 0.9s | 4.5s |
| Big slime | 10 | 16 | 2 | **0 ⚠** | 1.2s | 5.7s | **2.0s** |
| Bombschroom | 3 | static | 3 (blast) | 22px | 0.4s | 0.9s | one-shot ½ bar |
| **Irene** | **36** | 14 | **1 — dead code** | — | **3.6s** | 18.5s | **∞** |

Player: sword 4 dmg / 0.18s active window / 0.40s cadence / 30px max reach ·
bow 1–3 dmg, 120–200 px/s, 0.9s full draw, 0.7s cooldown, 240px range · roll
120 px/s for 0.24s with **0.16s iframes (19.2px of travel)**, 0.4s cooldown ·
invuln-after-hurt 0.6s. Boss: 36 HP, phase 2 at HP ≤ 18 (one-shot summon of
**2 bats, no repeat**), books do **1 damage at 75 px/s** — thrown at a player
who moves 60.

**Three things the math says that play alone couldn't:**
1. **Roll iframes clear every enemy's hitbox except the big slime** (19.2px of
   travel vs its 23px reach — fails by 3.8px). And because `enemy.gd:185-186`
   burns the full contact cooldown *even when the hit is refused during
   invuln*, a 0.16s roll actually buys ~1.0s of safety. Rolling works better
   than its own design implies.
2. **Enemy count barely raises melee pressure.** Same mechanism: one hit's
   0.6s invuln makes every *other* touching enemy waste its whole cooldown, so
   a lockstepped 3-skeleton pile deals roughly the contact DPS of one
   skeleton. Hard floor: you cannot die to contact faster than 1.8s. Crowds
   only threaten if arrivals are staggered — or if they shoot.
3. **Arrow tunneling is impossible** (3.33px/frame at max speed vs the bat's
   10px body — a ~3-frame margin). A hypothesis worth killing.

**The curve — enemy count 2 → 2 → **7** → 3 → 1; total HP 6 → 9 → **23** → 12
→ 36:**

| Area | Composition | HP | Verdict |
|---|---|---|---|
| 0 Village | 2× slime | 6 | fine |
| 1 Forest | skeleton + bowman | 9 | fine |
| 2 **Camp** | bombschroom + **3× skeleton** + mage + 2× bat | **23** | **the cliff** |
| 3 Mid-road | big slime + 2× bat | 12 | **slumps** |
| 4 Library | Irene | 36 | can't hurt you |

Area 2 isn't a step, it's a wall: 3 skeletons need 2.4s of swinging but kill
you in 2.0s, so stand-and-fight is a losing trade *before* the off-screen mage
and the two bats you cannot outrun. Then area 3 drops back to half the HP.
It's a lopsided tent — and the climax at the end of it is a boss who
**cannot touch you** (B-27) and whose books do 1 damage at a speed you
outwalk.

**The ONE change:** make damage and death *events*: hit-stop (2–3 frames) +
brief red vignette on player hit, and a ~1.5s death card ("Down. Back to the
lamp.") before respawn. This is the highest fun-per-effort in the whole
review — it makes the existing combat readable, makes death register (R4-06),
and softens R4-05 until healing gets a real design.

*But do the coffee-break fixes first — they're one line each and they repair
fights that are currently broken rather than merely illegible:* give the big
slime an `aggro_radius` (R4-39), pull the mage/bowman aggro inside the 128px
half-view or give `_shoot_cd` a starting wind-up (R4-10), and call
`_try_contact_damage()` in Irene's loop so the final boss can actually touch
you (B-27).

## 3. World and exploration

**What works.** The valley reads as a place: west village (best-dressed area
in the game — shots 09, 14), orchard road, river bridge as a genuine midpoint
landmark (shot 33), forest transition east. Doors got lamps and walkways in
round 3 and it shows (shot 56). The library study is a legitimately nice room
(shelves, benches, clock, plants) `[RENDERED library-ground.png]`, and the barn
looks like a barn.

**What doesn't.** *(interior findings verified against `bake_interior.py`
specs + baked grounds; per-room table in Appendix E)*
- **R4-13 · major:** **the 8 interiors have nothing in them to do.** (There
  are 8, not 9 — cottage, home_a1/a2/g2/j1/e1, barn, library.) Every room:
  fade in, look at furniture, step back on the exit mat. Zero occupants, zero
  interactables, zero items — while all 4 villagers stand *outdoors*, so
  they're a village of show homes. Interiors register `encounters:""` and emit
  only `X/_/S/>` cells, so nothing *can* be placed inside without extending
  the baker. `[RENDERED all 8]` `[CODE level_registry, bake_interior.py]`
- **R4-14 · major:** the rooms are the same room. `{cottage, home_e1, home_j1}`
  are one bedroom in three sizes; `{home_g2, library}` are the same
  shelf/desk/grand-clock kit at two scales — so **home_g2 pre-spoils the
  library's "grandest room" reveal.** Furniture counts across 8 rooms: bed×4,
  teal-rug×4, table×4, lamp×7, clock×5, from a 30-sprite library; the layout
  grammar (door at center-bottom, furniture on row 3, one rug low-center) is
  identical *by construction*. This is the single loudest "generated, not
  authored" tell in the game. `[RENDERED, CODE]`
- **R4-33 · major:** **the library — the story's literal destination — is the
  emptiest promise in the game.** `bake_interior.py` even comments it "pure
  story space… the grandest room in the valley," and it contains no Irene, no
  book, no DVD, no returns desk, no line of text; the one written line
  ("The door stands open — mind the shelves") is on the *outside* door, whose
  talk-prompt sits inside the travel trigger so you likely teleport in before
  reading it. `[CODE bake_interior.py:200, main.gd:214, level_registry.gd:72]`
- **R4-15 · major:** the cove is a postcard, not a place: big lily lake
  (pretty), uniform flower scatter, zero NPCs/encounters/props-with-meaning,
  3 landmarks in 4,608 tiles, and its road just **stops at x=49 of 96** — the
  player walks to a blunt end and turns around. `[RENDERED
  cove-s11-ground.png]` `[COMPUTED]` `[CODE level_registry — encounters "",
  has_shop/ariana false]`
- **R4-42 · major:** **wandering pays literally nothing, and the one object
  that looks like treasure is a decal.** The valley contains exactly one chest
  (165,19) — and it sits 3 tiles from the library (set dressing in a POI
  cluster, not a discovery) *and it cannot be opened*: `main.gd:_spawn_talkers`
  builds Interactables for only `N`/`$`/`L`/`H` — `x` (chest) isn't in the
  list, and no chest logic exists anywhere in the repo. Both signs are
  likewise unreadable (`n` is classed as `"decor"`). Every interactable in the
  game hugs the road (max distance: 10 tiles). Off-road you will find flowers,
  berries, stumps and tree noise — nothing else. `[CODE main.gd:206-217,
  prop_table.gd:205,213]` `[COMPUTED]`
- **R4-16 · minor:** players vanish completely under tree canopies with no
  silhouette/outline (shots 31–32). Standard genre problem, but with combat
  nearby it costs real legibility. `[PLAYED]`
- **R4-17 · minor:** bridge SE corner wedges a pure-east walker (no slide
  assist around the rail corner); trivially escaped by angling, but it's the
  kind of friction a first-timer hits within minutes (shots 33–34). `[PLAYED]`

**Map forensics** *(computed from the ASCII maps; I re-ran the load-bearing
numbers myself with an independent classifier — the shape held, so the
headline below is doubly sourced.)*

| Metric | Valley |
|---|---|
| Dead bands (rows with no path/prop/POI) | top 0–5, bottom 45–47 = **9/48 = 19%** (≈5 rows are genuine waste; the rest is tree border) |
| Rows with zero path tiles | **34/48 = 71%** — all paving lives in rows 18–31 |
| Prop density, **west** (x0–63) | **7.19 / 100 tiles** |
| Prop density, **midlands** (x64–130) | **0.87 / 100** |
| Prop density, **east** (x131–191) | **1.09 / 100** |
| Prop density, **the cove** (worldgen output) | **2.34 / 100** |
| Widest gap between POIs on the road | sign (86,19) → library (162,17) = **76 tiles ≈ 1.9 screens** |
| Interactable objects off the road | **zero** (max distance-to-road of any interactable: 10 tiles) |
| Chests in the entire valley | **1** — and it isn't interactive |

**The finding that reframes the whole map: your procedural map is denser than
your hand-authored one.** The valley's midlands (0.87/100) and east (1.09/100)
are **~2.5× sparser than the cove that a generator produced** (2.34/100). Put
plainly: *the west quarter is authored; the other ~130 columns are
worldgen-grade noise with a road through them.* The density falls off a cliff
at x≈50 and never recovers. `[COMPUTED, verified independently]`

**The "AI giveaway" tell is variance, not density.** The valley's props
*cluster* (nearest-neighbour stdev 3.88 — fences enclose paddocks, lamps flank
paths in pairs); the cove's props *scatter* at near-constant spacing (stdev
1.71 — the signature of Poisson-disc sampling), and 73 of its 100 props are
flowers. The loudest stamped spots: the cove's metronomic flower field (rows
2–17), and its lone chest at (14,8) dropped in blank grass with nothing within
10 tiles — a textbook "place 1 chest" stamp. The cove has **3 landmarks in
4,608 tiles**.

**Correcting my own claim (and the analysis):** there are **zero single-
neighbour dead-ends** in either map — but that metric is structurally blind
here, because the ≥2-tile-wide path rule means a road can never *have* a
1-tile spur. So: the valley road runs unbroken x3→191 and the cove crossing
genuinely works (I'd have flagged it otherwise). But **the cove's own road
stops at x=49 on a 96-wide map** — it simply ends, blunt, 51% across. That's
the dead-end a player actually feels, and it's real. `[COMPUTED]`

**The ONE change — and it's almost free:** **move two characters and add one
loop.** The game's only windmill (a unique silhouette) is buried at (56,39) in
the *west*, where density is already 7.19/100 — the most wasted asset on the
map. Move `z` to ~(120,16) and the chest `x` from (165,19) to ~(120,17): both
land in verified blank grass, ~7 tiles north of the road, **dead centre of the
76-tile void.** Then make the chest real by mirroring the library pattern in
`main.gd:_spawn_talkers`:
```gdscript
for cell in _map.find_all("x"):
    _add_talker("chest_%d_%d" % [cell.x, cell.y], _map.cell_center(cell))
```
That's two edited characters and four lines — and it buys a visible landmark
that pulls players off the road at the emptiest point in the game, with a
payoff at its base: the only "I went off-road and something happened" moment
that would exist. Pair it with a heal item inside the chest and it also dents
R4-05. *(The same `_add_talker` gap is what keeps all 8 interiors empty — fix
it once, spend it everywhere.)*

## 4. UI/UX

**What works.** The round-3 UI pass landed: consistent dark StyleBoxFlat
panels + Pixelify Sans everywhere (title, creator, pause, controls, dialogue
frame); pause menu is clean with save feedback ("Saved 23:36" — shot 52);
controls screen is a proper two-column remap grid with reset (shot 51); mouse
works in menus alongside keyboard `[PLAYED]` (shot 05); boss gets a named HP
bar (shot 60); checkpoint toast exists (shot 32).

**What doesn't.**
- **R4-18 · major (debug):** the broken dialogue panel + stuck prompt (R4-01)
  are UI-facing symptoms; the prompt lies from boot even before the panel
  eats the screen bottom. `[PLAYED]`
- **R4-19 · minor:** the controls screen shows only the primary binding per
  action; the legacy aliases (Space sword, F bow, `/`, `,`, `.` for P2) stay
  live but invisible — a remapper can't see what they're leaving bound.
  `[PLAYED]` `[CODE project.godot input]` — and worse, remapping any ONE key
  permanently deletes every alias on all 16 actions after the next boot
  (**B-07**, CONFIRMED, Appendix C cluster F).
- **R4-20 · minor:** pause "Zoom: Normal" ignored Left/Right; value rows in
  the creator cycle on arrows but pause's don't — inconsistent idiom between
  the two menus. `[PLAYED]` — root cause confirmed in §6: `pause_menu.gd`
  handles only up/down/accept; the creator *does* implement left/right.
- **R4-21 · minor:** P1 HP bar is the only player readout and lives in the far
  corner (R4-07's presentation half). No numbers, no hearts, no damage
  direction. `[PLAYED]`
- **R4-22 · polish:** checkpoint toast is small, top-center, and easy to miss
  during motion (shot 32). `[PLAYED]`

**The ONE change:** folded into §2's hit/death feedback — it's the same fix
seen from the UI side. Second pick if that's taken: show alias bindings on the
controls screen (one extra label per row).

## 5. Story scaffolding

**What works.** The handoff architecture is genuinely good: stable ids, one
data file (`dialogue_data.gd`), fail-soft fallback for renamed cells, and the
writer/coder split documented in the file header. The placeholder lines are
better than placeholder-grade — "Irene takes late returns... personally" and
Ariana's "Quack. / (She seems pleased you stopped by.)" already carry the
tone. The premise (librarian turns a friend into a duck over an overdue DVD)
is coherent across title copy, world brief, and boss taunts. `[CODE]`

**What doesn't.** *(all verified against source this session)*
- **R4-31 · major (coherence):** **the premise is undiscoverable in-game.**
  The whole story — Irene turned Ariana into a duck over an unreturned "Peep
  and the Big Wide World" DVD — exists only in docs. In the game a player
  sees: a duck named Ariana that quacks, one villager hinting "Irene takes
  late returns... personally," then a boss who *opens combat* with "you're
  here about the DVD" — a DVD nothing ever mentioned. `"Peep…"` = 0 hits in
  the repo; `"DVD"` = 1 hit, mid-boss-fight. The inciting incident, the
  transformation, and the goal are all unstated. `[CODE]`
- **R4-32 · major (coherence):** **the quest never resolves — and the closing
  beat was dropped mid-edit.** After the boss dies nothing changes: Ariana
  still says "Quack," the win screen says only "IRENE HAS BEEN DEFEATED." The
  smoking gun: `win_screen.tscn` has a Label *literally named "Ariana"* whose
  text is `"IRENE HAS BEEN DEFEATED."`, and the closing line `world-brief.md`
  promises ("Message received. I'm still renting it again.") has zero hits in
  the repo. Victory reads as "you beat up a librarian," not "you saved your
  friend." `[CODE win_screen.tscn:101-105]`
- **R4-23 · major (gap list):** **zero quest-loop primitives exist.** `game.gd`
  persists exactly one story flag (`boss_defeated`) in a closed 6-key save
  dict — any new flag needs a v5 migration. Verified missing in dependency
  order: quest flags, items/inventory, condition-gated dialogue (`entry()` is
  stateless), door-lock-by-flag, objective UI, event-triggered dialogue (a box
  can only open from an `Interactable`, so nothing can start a conversation on
  boss death), and any way to place an NPC/item *indoors* (the baker emits no
  talker cells). Even "talk to Evan → library line changes" has nothing to
  hang on. `[CODE]`
- **R4-25 · minor:** the game's best joke double-fires. Evan's line 1 duplicates
  the shop-sign ambient line verbatim (`"Toasted, or the old way?"`), *and* the
  "only stand in the valley" punchline is delivered by both Evan and a villager
  4 tiles away — repeated-template humor is a classic generated tell.
  `[CODE dialogue_data.gd:20-22/51, shop_sign.gd:12]`
- **R4-24 · minor:** 4 villagers built from 2 sprites (deterministic by
  x-parity — the pond and shop villagers are identical twins), no indoor
  residents, no quest-giver: nobody actually sends the player east. `[CODE]`
- **R4-34 · minor:** villager ids are welded to map cells (`villager_<x>_<y>`)
  with a *silent* `???`/`...` fallback — moving an NPC one tile detaches its
  lines with no error, against the project's own fail-loud rule. `[CODE
  dialogue_data.gd:63-66]`
- **R4-26 · docs:** `story-handoff.md` still says "~5 hardcoded lines, NOT a
  dialogue system" and would send a story writer to *re-decide things already
  shipped* (Ariana-as-duck, Evan's sprite, library placement) on a 5-line
  budget. What the pass can now actually assume: edit `dialogue_data.gd` (7
  stable ids, arbitrary-length line arrays), 5 boss `@export` slots, the shop
  sign, and 2 win + 2 title labels ≈ 22 strings. Rewrite the prompt around
  that surface first. `[CODE/docs]` (also: `dialogue_data.gd`'s own header
  claims to hold "every talkable thing's lines" but omits Irene, the shop
  sign, and all screen copy — Irene, the game's namesake, has zero lines in
  the file billed as the complete story surface.)

**The ONE change:** two primitives — `var flags := {}` in `game.gd` (persisted,
+v5 migration) and an optional `{"when": flag, "lines":[…]}` variant on
`DialogueData` entries — and the story pass can write an actual quest loop
(give-quest / complete-quest / post-boss Ariana) instead of ambient flavor.
The single highest-leverage story fix, though: **have the pond villager state
the premise** (she's 4 tiles from Ariana and currently pure filler) and **give
the win screen's already-existing "Ariana" label a real closing line** — two
lines close R4-31 and R4-32 with no new systems.

## 6. Codebase

*Verified personally this session; the ranked refactor list lands with the
architecture pass.*

**What works.** The registry-driven world is the right shape: adding a level
is data + a bake, not engine surgery (`level_registry.gd` — verified against
all 10 levels). Generated `prop_table.gd`/interiors with fail-loud validators
keep art data honest. One `Enemy` script parameterized per-scene is the
correct pattern at this scale. The one-Area2D transition mechanism with
arm-on-exit is simple and has survived several bug rounds.

**What doesn't (all verified at exact lines; recon numbers corrected).**
- **R4-27 · critical (class):** the R4-01 break generalizes — any scene
  restyle can silently break a typed `@onready` cast, debug-only. **Good news
  from the audit:** all 25 typed node casts across 13 scripts were checked
  against their scenes, and `dialogue_box.gd:18` is the *only* current
  mismatch. The class is real; the instance count today is one. `[CODE]`
- **R4-35 · major (already two live bugs):** the enemy `_physics_process`
  copy-paste has already drifted. `ranged_enemy.gd` has **no corner-steering
  call** (the round-3 fix only landed in the base class) so a bowman/mage can
  pin on a prop corner forever; and `bomb_enemy.gd` overrides the loop and
  **never applies knockback**, so a sword hit on a bombschroom is a silent
  no-op. Copy-drift, caught in the act. `[CODE enemy.gd:101-133,
  ranged_enemy.gd:22-51, bomb_enemy.gd:31-47]`
- **R4-28 · major:** `player.gd:363-370` sword hits ANY body with
  `take_damage` — guarded only by the `SwordHitbox` collision mask, not a
  group check (unlike arrows and contact damage, which check both). One layer
  edit from friendly fire. Three call sites enforce "damageable" three
  different ways. `[CODE]`
- **R4-36 · major:** encounter areas are hardcoded, positionally numbered, and
  their raw int ids are the saved checkpoint. `BOSS_ID:=4` already documents
  one off-by-one (the boss moved from 3→4 when the mid-road area landed); the
  cove is the *named* next encounter add and will force either another
  hardcoded branch or a renumber that remaps every save. `_area_by_id` misses
  silently to area 0. `[CODE encounter_manager.gd:33-151,330]`
- **R4-37 · major:** `level_registry` entry/transition coordinates are
  hand-derived magic numbers validated by nothing — the exact class that
  shipped the round-3 "entrance not where it looks" and the `2efded1`
  invisible-exit bugs. Meanwhile `main.gd:462` (`_check_symbol_coverage`) is
  the perfect house pattern for a build-time assert; no equivalent guards
  transitions. `[CODE]`
- **R4-29 · major:** `respawn_at` misses a sprite-frame reset (R4-08's cause).
  `[CODE player.gd:350-360]`
- **R4-20 root cause · minor:** pause "Zoom" ignores Left/Right by design —
  `pause_menu.gd:91-110` handles only up/down/accept, while
  `character_creator.gd:90-93` *does* implement left/right on value rows. Two
  menus, two contradictory idioms. `[CODE]`
- **Observation "window 640×360 → 1718×1341" — REFUTED as a game bug:** zero
  code touches window size and `project.godot` sets no override, so the resize
  came from *outside* the process (the native playtest driver / OS). Real
  residual: the desktop build boots at a literal 640×360 window; setting
  `window_width/height_override` to 1280×720 would pin a sane size. `[CODE]`
- **R4-30 · polish:** dead code `area_enemies` (`enemy.gd:196-197`) — flagged
  a review round ago and still present. `[CODE]`

**Corrected recon numbers:** `main.gd` is 484 lines, not 442, and is a *linear
scene-builder*, not a god object — its real smell is a 97-line `ANIMAL_ANIM`
data table (20% of the file) that should live in generated data like
`prop_table.gd`. `Game` autoload is 62 refs / 14 files (not 69/19) — a
reasonable Godot idiom at 4.8k lines; watch the boolean cross-system flags
(`dialogue_active`/`win_pending`) and the scattered `save()` call sites, don't
break it up yet. There are 3 projectile scripts, not 4 (the boss reuses
`book_projectile`). Save migration accepts exactly `{3,4}` — each future bump
strands the oldest cohort silently. Menu SELECTED/DIMMED colors have already
drifted into 4 highlight tints and 3 dim tints for one idiom.

**Top-3 refactors, by payoff before the project doubles:**
1. **Enemy template-method + one `Projectile` script** — base owns the
   preamble/dead-handling/steer/contact and calls an overridable
   `_decide_velocity`. Kills the copy-drift class *that has already produced
   two live bugs* (R4-35) and makes every new enemy cheap — and content
   doubling here is mostly new enemies.
2. **Data-driven encounter areas** — per-level area tables in `LevelRegistry`
   with string keys, checkpoint saved as `{level, key}`, fail-loud
   `_area_by_id`. Kills the `BOSS_ID` renumber class (R4-36) and unblocks the
   cove encounters, the explicitly-named next content step.
3. **Boot-time validation harness** — one CI headless job that instantiates
   every `scenes/*.tscn` and asserts registry transitions/entries land on
   walkable cells, modeled on the existing `_check_symbol_coverage`. Kills the
   debug-only typed-cast class (R4-27) *and* the hand-synced-coordinate class
   (R4-37) in one move — each of which has already shipped a bug. (This is the
   same job §7 arrives at from the CI side.)

## 7. The build/verify loop

*This section is complete — analyzer + adversarial verifier + my own
validations.* `[CI]` `[CODE]`

**What works.** The static layer is genuinely strong for a solo project:
symbol/asset/level-graph/map-rule/character-layer checkers are fail-loud,
auto-discovering (mostly), and encode real past bugs as permanent rules. The
bot's *input-proof* assertion (menu highlight must move) is load-bearing and
robust, and its save-migration check asserts actual content (localStorage
substrings), not pixels.

**What doesn't — demonstrated, not theoretical.** The round-3 dialogue break
is a complete case study in how the loop's blind spots stack:

1. The break is **debug-only** — release exports skip typed-assignment checks,
   so the browser bot (which drives the release export) is *structurally*
   incapable of catching this entire class. `[CI]` (bot frames on the very
   merge that broke it show no stuck panel — `bot-17/18/19-*.png`)
2. The bot's dialogue leg had **already drifted off-course**: checkpoint
   re-numbering moved its blind timed walk, so on run `1d05a42` it wandered
   into the forest, "talked" to a Big Red Slime, took visible HP damage, and
   its ≥5000px "dialogue opened/closed" deltas passed on ambient motion alone
   (4.1% of a world-showing crop). A structural false-green. `[CI]`
   (`ci_driver.py:286-289, :60`)
3. The next run — the one that might have flagged *something* — died as a
   **4-second billing stall** (runner never started), which also trains alarm
   fatigue: red now means "billing", not "bug". `[CI]` (run `dc11d4a`)
4. CI never launches Godot at all (`ci.yml` is lint + stdlib checkers), and
   the bot runs **post-merge only, racing the deploy on the same SHA** — even
   a true red can't stop a broken build from shipping. `[CI]`

**Real regression classes that slip through today, ranked:** debug-only script
errors (one live on main right now) → bot route-drift false-greens (proven) →
post-merge-only gating (deploy races bot) → feel regressions (accepted, human
cadence) → baked-artifact bugs like invisible doors → enemy/boss sheet frame
bugs (chicken-class, unguarded for combat sprites) → deeper-than-v3 save
migrations → deploy-only breaks (no prod probe).

**THE one check** (answering the prompt): a **headless DEBUG scene-
instantiation smoke job** — not a naive boot-and-quit, which would miss the
dialogue bug (the box only instantiates when the game scene builds). ~40-line
`SceneTree` script: instantiate every `scenes/*.tscn`, two frames each, parse
all 10 registered levels, then `grep -E "SCRIPT ERROR|Parser Error"` the log
(Godot exits 0 regardless — the grep IS the assertion). Catches: all typed
mismatches, broken node paths, bad preloads, per-scene `_ready()` crashes, in
debug where Godot actually checks. Would have caught R4-01 on its first run.

**The prompt's test case** ("transition works but the door isn't visible"):
that class lives only in the committed PNG vs the map's `>` cell, invisible to
every existing layer. The fix is a ~35-line Pillow check comparing the baked
doorway tile against its neighboring wall tile. **Validated tonight against
git history: pre-fix library ground = 0/256 pixels differ (walled over —
check fires); current = 256/256 differ (check passes).** Threshold-free,
because the bake pastes byte-identical wall tiles.

**Quick wins (each <30 min):** (1) `dialogue_box.gd:18` one-word type fix;
(2) make the bot's in-page JS errors fatal (`ci_driver.py:338` currently
"logged, not fatal" — turns a silent class red for ~4 lines); (3) ambient-
noise-floor + mean-brightness-drop asserts on the dialogue leg; (4)
`check_map_rules.py` auto-discovery of outdoor maps from the registry; (5)
post-deploy `curl` probe of the prod URL; (6) add `pull_request:` trigger to
`playtest.yml` so the bot gates PRs instead of auditing corpses.

## 8. Missing entirely — ranked by how much the absence hurts right now

1. **Audio** — nothing exists, and I nearly under-ranked it. Two arguments
   moved it to #1. (a) **For a project whose stated purpose is learning Godot
   end-to-end, an entire engine subsystem has never been touched** — no
   `AudioStreamPlayer` appears anywhere in the repo. (b) It is the cheapest
   high-bandwidth feedback available: a sword-hit sound does more for feel
   than screen shake, needs no dependency, and — unlike more pixels — it
   reaches the player when their eyes are on the enemy, not the HP bar. Three
   sounds (hit, death, checkpoint) and one wind loop would change the game
   more per hour than anything else in this section.
2. **Legible damage feedback** — *not* absent (I got that wrong; see R4-06):
   a hurt flash and a death collapse exist, but at 0.25s on a 64px sprite,
   with no hit-stop, no shake, and entirely broken on the boss. The work is
   *strengthening* what's there, which is cheaper than it sounds.
3. **A reason to explore** — no heal, no secret, no collectible, and the one
   chest in the game is a decal you can't open (R4-42). The map is built and
   dressed and pays nothing back.
4. **Difficulty options** — deferred knob; matters more once healing exists.
5. **An onboarding beat** — R4-02's opening line. Lower than I first put it:
   the road genuinely does point east on its own.
6. **Save slots** — genuinely fine to skip for v1; single-slot autosave suits
   the scope. Correctly deferred.

---

## (a) The five highest-impact changes, ranked

*This ranking was stress-tested by an adversarial pass that was told to attack
it. It landed two hits — it caught me overstating the death-feedback finding
(R4-06), and it found R4-43/44, which neither my play nor the 42-bug audit
did. I re-verified both against the code myself and re-ranked. What follows is
the post-challenge order.*

1. **Make Irene a real boss** (B-27, B-11, B-10, R4-44) — **the climax cannot
   touch you.** Her `_physics_process` override never calls
   `_try_contact_damage()`, so the `contact_damage = 1` in her scene is dead
   data; she stays permanently red after the first hit (her override skips the
   base modulate reset); she's snipeable from outside her wake line; and if you
   visit the library — *the quest's own destination, one tile from her* — she
   respawns as a statue. Three of those fire on **every** playthrough. This is
   the payoff the entire game builds to, and it's ~15 minutes of fixes. The
   fun-per-effort here is not close.
2. **Give scene-crossing state an owner** (R4-43, R4-44, Appendix C cluster A)
   — one root cause behind four symptoms: `win_pending`, `resume_requested`,
   `area.cleared` and the boss's `_active` all die or lie when `change_scene`
   frees the level. Today that means every door round-trip **resurrects the
   whole gauntlet**, the boss goes inert, Esc during the win delay hard-freezes
   the game, and a stuck `win_pending` can disable every door for a session.
   Start with the free line (`get_tree().paused = false` in `change_scene`),
   then move the win timer + the cleared/active state somewhere that survives
   the swap.
3. **Add sound, and fix the feedback you already have** (R4-06/07) — the one
   engine subsystem this project has never touched, in a project whose *point*
   is learning the engine end-to-end. A sword-hit sound buys more feel than
   screen shake, costs nothing, and teaches something new. Pair it with making
   the *existing* flash readable (it's 0.25s on a 64px sprite, and entirely
   broken on the boss) — verify what's there reads before building hit-stop on
   top of it.
4. **The debug-smoke CI job** (R4-27, §7) — the `dialogue_box.gd:18` one-word
   fix is a typo, not a work item; do it in 30 seconds. **The job is the
   item**, and it ranks here because *the editor build lying to its author*
   corrupts the feedback loop that produces every other judgment on this list.
   If dialogue is mute locally, you never hear that the lines are hollow.
5. **Two lines of writing + one object in the library** (R4-31/32/33) — the
   boss opens by referencing a DVD the game never mentions; the quest's
   destination is an empty room; the win screen has a Label named "Ariana"
   reading "IRENE HAS BEEN DEFEATED." An hour closes the story loop that
   already exists.

**Explicitly demoted, and why:** *the 8-interiors content day* (R4-13) → do
only the library; the other seven stay empty until the boss is worth walking
to. *The story-flags dict* (R4-23) → YAGNI: two primitives to serve one flag
with no content behind it; write the two lines, build the system when a second
flag exists. *The "go east" opening beat* (R4-02) → the road already does that
job. *The enemy template-method refactor* (R4-35) → real, but it's §6's
structural list, not a fun item; fix the lying docstring today.

## (b) The one thing I would NOT change

**The ASCII-map → generated-artifact pipeline with fail-loud checkers.** The
registry + baked grounds + generated prop table + stdlib validators is the
reason a solo learner ships a connected 10-level world with CI at all. It kept
paying out all night: I proved the invisible-door fix from committed PNGs
alone, computed the entire map critique without launching the game, and
verified the door geometry from source — all because the world is *data*.

Note the distinction, because §3 is harsh about the map: **the criticism is of
the authoring input, not the machine.** "The midlands are worldgen-grade" is a
statement about 130 columns of ASCII, and the fix is editing characters — which
is exactly the cheapness this pipeline was built to buy. Nearly every fix in
this review is small *because* of this backbone. Guard it; the CI suggestions
in §7 exist to protect it, and the one refactor I'd bless (§6 #3) is just
extending its own `_check_symbol_coverage` idea to the things it doesn't cover
yet.

---

## Appendix A — 25-minute human feel pass (Chris)

**Precondition:** apply the `dialogue_box.gd:18` one-word fix first (or play
the web build) — on the editor build every NPC is mute.

**A. Cold start (5 min, fresh save):** where do your eyes go on the title?
Did you know to go east, and what told you? Time-to-first-fight; did the
first slime read as threat or decor? Did you notice your first hit taken?

**B. Combat (10 min, west→east):** sword: does the rooted swing feel
deliberate or sticky? Whiff on purpose — fair recovery? Bow: full-draw while
strafing — readable without a meter? Tap-shot ever worth it? North-draw:
can you tell you're drawing? Roll *through* a contact hit — do the i-frames
ever save you, or is roll just a sprint? Die once on purpose: rate 1–5 "did
the game acknowledge my death". Watch the respawn idle frame (R4-08) — does
it happen on web too? Mid-road & camp: which enemy is most/least readable?
Note your HP arriving at the camp — death sentence or comeback?

**C. Boss (5 min):** books: reaction-dodgeable or memorized? Phase 2: do bats
change how you MOVE or just add chip? On a wipe, is the full-HP boss retry
fair or grindy?

**D. 2P couch (5 min, if you can):** both players walk apart — how fast does
the shared camera become the enemy? P2 numpad 1/2/3 with NumLock OFF on the
web build (open question). Down-and-revive: discoverable without being told?
Verdict the prompt wants: **is 2P actually more fun than 1P?**

**E. World (5 min):** enter three interiors — would you enter a fourth? Walk
to the cove — worth it? Notice the path dead-end? Ultrawide fullscreen: HUD
corners, map dead bands, anything broken?

**Report format (raw fragments welcome):**
`AREA | what happened | how it felt | keep/fix/cut`

## Appendix B — docs drift (cleanup list)

- `PROJECT.md` combat block still says bow = P1 F / P2 comma (superseded by
  G/H + numpad); says main scene is `scenes/main.tscn` (actual:
  `player_select.tscn`); interior count says "6 cottages + barn" (actual: 8
  interiors incl. the library); several `[SUPERSEDED]` blocks worth pruning to
  a current-state snapshot.
- `docs/roadmap.md` "honest snapshot" claims the live game is still the
  walking skeleton — two levels, 8 interiors, and a 2-phase boss ago.
- `docs/combat-slice.md` controls table is two remaps stale.
- `docs/story-handoff.md` still forbids the dialogue system that now exists
  (R4-26) — the highest-cost drift on this list, since it misdirects the next
  story session.
- `docs/world-brief.md` — the map-truth doc a story writer reads — still says
  Ariana is "a chicken stand-in" (she ships as a Duck), that no building asset
  exists for Evan's shop (it renders a Market_Stall), and implies a *sealed*
  library (a door transition ships, and the line says "the door stands open").
  `dialogue_data.gd:9` and `interactable.gd:6` repeat the "sealed" claim.
- **Code comment drift:** `boss_irene.gd:10-12` says "Phase 2 … intentionally
  NOT here yet" while phase 2 is implemented 96 lines below it (`:108-118`).
- Local-serve port is 8642 in `.claude/launch.json`, 8060 in `ci_driver.py`,
  8000 in PROJECT.md — harmless, but pick one.
- **Resolved, not drift:** the "window resizes itself 640×360 → 1718×1341"
  observation from this session's play is *not* a game bug — nothing in the
  project touches window size (see §6). It was the playtest driver/OS.

## Appendix C — latent bug audit (overnight multi-agent hunt, adversarially verified)

*Method: 3 rounds × 4 lenses (state machines, save/persistence, combat math,
web platform) hunting until dry; every candidate independently re-traced by a
strict verifier instructed to refute. 42 findings survived; deduped to 35
below. Verdict CONFIRMED = full code trace reproduced by the verifier.
Severity is mine. Full scenarios + verifier line-by-line traces:*
[review-round4-bugs.json](review-round4-bugs.json) *(B-ids below map to array
order there; duplicates from independent lenses left in as corroboration).*

### Cluster A — the win sequence (fix as one unit; top-5 #1)
The 3-second `WIN_DELAY` window (`encounter_manager.gd:256-261`) is a bug
factory because win orchestration lives on a freeable node, `win_pending` is
only cleared by `reset_run`, and nothing gates player actions during it.
- **B-01 · CONFIRMED · critical:** Esc (or E on a talker) during the delay →
  win screen loads into a *paused* tree → hard freeze, reload required — and
  since `boss_defeated` was already saved, the ending is gone for that save.
- **B-02 · CONFIRMED · critical:** Return-to-Title (or a co-op door race)
  during the delay frees the awaiting EncounterManager → win screen never
  loads AND `win_pending` sticks true → **every door/edge in the game refuses
  travel for the rest of the session.**
- **B-03 · CONFIRMED · critical:** refresh during the delay or on the win
  screen → `boss_defeated=true` was saved before the win → quest-complete
  screen permanently unreachable on that save (recoverable only by New Game).
- **B-04 · CONFIRMED · major:** wiping during the delay (leftover phase-2
  bats) re-arms a full-HP, re-activated Irene *after her defeat was saved*.
- **B-05 · CONFIRMED · major:** Esc during any scene fade carries
  `get_tree().paused` into the next scene — it loads frozen.
- **B-06 · CONFIRMED · critical:** opening dialogue during a fade → paused
  tree + leaked `dialogue_active` → permanent freeze.
**I re-traced this cluster personally** (not just via agents), because it now
leads the top-5. The chain is real and every link is in current main:
`game.gd:71` sets the autoload to `PROCESS_MODE_ALWAYS` and `change_scene`
(`game.gd:94-107`) never touches `get_tree().paused`; `pause_menu.gd:94-99`
gates Esc only on `dialogue_active`, never on `win_pending`; the *only* three
`paused = false` sites in the codebase live in `pause_menu.gd` and
`dialogue_box.gd` — both inside `main.tscn`, which the scene swap frees. Godot's
`create_timer` defaults to `process_always`, so the win timer keeps ticking
through the pause and fires into a scene that no longer has an unpauser.

**Fix direction, cheapest first:** (1) **one line —
`get_tree().paused = false` at the top of `Game.change_scene`** defuses B-01,
B-05 and B-06 together, since every freeze in this cluster is "pause state
outlived the scene that could clear it"; (2) gate pause/dialogue/interact/
travel on `win_pending` and `is_fading()`; (3) structurally, move the win
timer + scene change into the `Game` autoload so a freed node can't strand the
ending (fixes B-02/B-03). Note `change_scene` also silently drops re-entrant
calls (`game.gd:95-96`) — that's the mechanism behind B-02's lost win screen.

### Cluster B — boss-fight integrity
- **B-09 · CONFIRMED · critical:** re-entering the valley through ANY door at
  checkpoint 4 leaves Irene permanently inert (activation only fires on
  checkpoint *advance*, which can't recur at max checkpoint).
- **B-10 · CONFIRMED · major:** `take_damage` isn't gated on `_active` — the
  inert (or not-yet-woken) boss can be arrow-sniped dead from outside her
  activation line for a silent, fight-free win.
- **B-27 · CONFIRMED · major:** **Irene deals no contact damage** — her
  ContactHitbox/`contact_damage=1` are dead code in her overridden loop;
  standing inside her is completely safe. Books are her only threat.
- **B-11 · CONFIRMED · minor:** her hurt-flash never resets — permanently
  red-tinted after the first non-lethal hit (her override skips the base
  modulate reset).

### Cluster C — co-op correctness (pre-reqs for "is 2P more fun?")
- **B-12 · CONFIRMED · major:** projectiles have no consumed-flag — one
  bolt/book damages BOTH players standing in line (and one arrow can hit a
  whole stack of enemies).
- **B-13 · CONFIRMED · major:** the revive gate only checks enemies within
  130px — a bombschroom that self-destructs (or any distant killer) makes
  death instantly self-reviving at full HP: co-op death can be *free*.
- **B-14 · CONFIRMED · minor:** downed players still block enemy projectiles
  and soak melee cooldowns — a corpse is functional cover.
- **B-15 · CONFIRMED · minor:** a downed player can still open NPC dialogue,
  pausing the entire game mid-combat.

### Cluster D — enemies and fairness
- **B-16 · CONFIRMED · major:** the big red slime ships with no
  `aggro_radius` override (default 0 = no gate) — it marches off its post
  from scene load and unravels the area-3 road encounter (it's the slime the
  CI bot met deep in the forest).
- **B-17 · CONFIRMED · major:** wipe-respawn re-arms only the checkpoint's
  own area — aggro-latched pursuers from the NEXT area (bats are faster than
  the player) follow and camp the respawn point.
- **B-22 · CONFIRMED · major:** the bow outranges every aggro radius; any
  gated enemy can be killed without ever waking. Combined with B-10 this
  covers the boss too.
- **B-18 · CONFIRMED · minor:** knockback can shove a player onto an armed
  LevelTransition — involuntary level change mid-fight.
- **B-19 · PLAUSIBLE · minor:** enemy bolts ignore terrain (mask=players
  only) — hits through walls/trees where geometry allows the angle.
- **B-20 · CONFIRMED · polish:** corner-steer can still oscillate forever in
  concave corners (residual hole in the round-3 fix).
- **B-21 · PLAUSIBLE · polish:** getting hurt mid-swing can freeze the white
  sword arc on screen until the next swing.

### Cluster E — save and persistence
- **B-24 · CONFIRMED · major:** Save Now in the cove or an interior, then
  Continue → checkpoint resume logic runs against the wrong level context
  (spawn/teleport mismatch).
- **B-23 · CONFIRMED · major:** failed saves report success — `last_saved`
  is set before the write; the web path swallows localStorage exceptions;
  the pause menu happily shows "Saved HH:MM" for a write that never landed.
- **B-25 · CONFIRMED · minor:** the *implicit* New Game path (no save on
  disk → title skips straight to 1P/2P) never calls `reset_run` — stale
  runtime state can leak into a fresh run.
- **B-26 · CONFIRMED · minor:** `current_entry` survives Return-to-Title and
  hijacks the spawn on the next checkpoint-0 Continue.
- **B-28 · CONFIRMED · minor:** the title menu stays live during the
  Continue fade — a stray Down+Enter runs New Game *over* the accepted
  Continue.
- **B-29 · CONFIRMED · minor:** checkpoint ids above the max area id (hand
  edit / future build) aren't clamped on load.
- **B-30/31/32 · CONFIRMED · polish:** save write is truncate-in-place (no
  temp-file swap); `_apply` isn't type-safe against hand-edited fields; the
  level string round-trips unescaped into a single-quoted JS eval on web.

### Cluster F — controls
- **B-07 · CONFIRMED · major (data loss):** remap ONE key and after the next
  boot ALL legacy alias bindings on all 16 actions are gone — `_save`
  persists only the first key per action and `apply_saved` erases the rest.
  Remapping P1's sword silently deletes Space/F/`/`/`,`/`.` everywhere.
- **B-08 · CONFIRMED · minor (web):** remaps lost if the tab closes shortly
  after rebinding (user:// on web = IndexedDB, async flush).
- **B-33 · CONFIRMED · polish:** rebind capture accepts `physical_keycode 0`,
  leaving that action unpressable for the session.

### Cluster G — web platform
- **B-34 · CONFIRMED · minor:** camera limits are computed once in `_ready` —
  a browser-window resize never recomputes them; interior rooms pin
  off-center with a one-sided void band.
- **B-35 · PLAUSIBLE · polish:** the Build Output staging writes no
  compression/cache headers for the ~45MB payload — delivery rests entirely
  on Vercel edge defaults.

## Appendix D — evidence index

Play evidence `docs/playtest/round-4/`: 01–08 title/creator · 09–16 spawn,
prompt bug, slime aggro drift · 17–29 sword/roll/bow vs slimes, deaths,
respawns · 30–44 road east, bridge wedge, gauntlet deaths, costume bug ·
45–52 pause, zoom, controls, save feedback, unleashed skeleton · 53–59
Continue flow, door approach, garden slimes · 60–62 boss arrival, book, taunt-
in-broken-panel · `bot-17/18/19` CI false-green forensics. Engine stderr log
(SCRIPT ERROR spam): session scratchpad `np-game-out.log.err`.

## Appendix E — per-interior audit

*From `bake_interior.py`'s `INTERIORS` specs + the baked grounds. "Finds" =
what a player can interact with, take, read, or talk to.*

| Room | Size | Contents (spec) | Player finds | 2nd visit? |
|---|---|---|---|---|
| cottage | 13×10 | fireplace, bed, plant, lamp, clock, rug | nothing | no |
| home_a1 | 11×9 | stove, sink, pans, fridge, clock, table+2 chairs, rug | nothing — *best theme (kitchen)* | no |
| home_a2 | 11×9 | 4 plants, bed, rug, lamp | nothing — *theme: plant lover* | no |
| home_g2 | 13×10 | 3 bookshelves, grand clock, desk+chair, lamp, rug | nothing — **= mini-library, pre-spoils the real one** | no |
| home_j1 | 9×8 | bed, rug, plant, lamp (4 items) | nothing — *emptiest* | no |
| home_e1 | 13×10 | fireplace, bed, clock, plant, table+2 chairs, rug | nothing — *= cottage + dining* | no |
| barn_int | 14×11 | 5 barrels, 4 crates | nothing — *distinct at least* | no |
| **library** | 17×12 | 6 shelves, grand clock, 2 desks, 4 chairs, rug, 2 plants | **nothing — no Irene, no book, no DVD, no desk to return it to** | no |

**Near-duplicates:** `{cottage, home_e1, home_j1}` = one bedroom at three
sizes · `{home_g2, library}` = one kit at two scales. **Distinct:** home_a1,
home_a2, barn_int. **Occupants: 0 of 8. Interactables indoors: 0 of 8**
(interior maps emit only `X`/`_`/`S`/`>` — there is no cell type for a talker,
which is the single plumbing gap behind every empty room).
