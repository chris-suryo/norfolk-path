# Difficulty selector — the knob inventory

Round-3 marked "maybe difficulty settings later" as backlog, your call. If
you ever want an Easy/Normal/Hard row, the good news: almost everything is
already an exported knob, so a selector is a **multiplier table**, not a
redesign. This doc is the inventory so the decision is a menu.

## What a difficulty preset would scale (all exist today)

| Knob | Where | Today |
|---|---|---|
| Enemy HP | `max_hp` export per enemy scene | slime 3 · skeleton 5 · bat 1 · big slime 10 · boss 36 |
| Enemy contact damage | `contact_damage` export | 1 |
| Enemy speed | `move_speed` export | 30 (slime) … 62 (bat) |
| Ranged enemy bolt speed/rate | `bolt_speed` + fire cadence exports | 90 px/s |
| Aggro radii | `aggro_radius` export | ~110 skeleton, camp-gated |
| Boss phase-2 trigger + summon cadence | exported on BossIrene | ½ HP |
| Player max HP / damage | player exports (+ upgrade deltas) | 6 / sword 4 / bow 2 |
| Co-op revive radii | `REVIVE_RADIUS`/`REVIVE_STANDOFF_RADIUS` consts | 130 / 260 |
| Roll i-frames / cooldown | player consts | — |

## Shape if built (S/M)

`Game.difficulty` (saved, additive field like `upgrades`), a
`DIFFICULTY := {easy: {enemy_hp: 0.75, enemy_dmg: 0.5, ...}, ...}` table, and
a multiply-on-spawn in `EncounterManager._spawn_area` + player `_ready`.
Pause-menu row mirrors the Zoom/Speed pattern (now well-trodden). One save
field bump, no new systems.

## Recommendation

**Defer.** The game hasn't had its first full-difficulty playtest since the
bow/enemy-variety expansion; tune ONE difficulty until the gauntlet feels
right, then decide whether presets are even needed. The Speed row (#40)
already gives you a coarse global feel lever for experimentation meanwhile.
