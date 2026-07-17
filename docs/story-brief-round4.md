# Story brief — the dialogue/writing pass (self-contained)

**For Chris, to do offline.** This is pure data + text: editing it cannot break
the build. It supersedes `docs/story-handoff.md`, which is stale (it still
says "~5 hardcoded lines, NOT a dialogue system" — a real dialogue system
shipped, and you have more room than that doc thinks).

Everything here traces to findings in [review-round4.md](review-round4.md)
§5 (R4-31, R4-32, R4-25, R4-24, R4-26, R4-34).

---

## The story you're telling (locked, from world-brief.md)

Irene the librarian turned **Ariana** into a **duck** over an unreturned copy
of the DVD **"Peep and the Big Wide World."** The player walks west→east to her
library to set it right. Ariana lives at the pond.

**The problem: none of that is in the game.** A first-time player sees a duck
that quacks, one villager muttering about late returns, and then a boss who
*opens combat* with "you're here about the DVD" — a DVD the game never
mentioned. The premise, the transformation, and the goal are all unstated, and
the quest never resolves (Ariana stays a duck; the victory reads as "you beat
up a librarian"). Your job is to make the story *legible in-game* with the
strings that already exist.

## The four beats to land (in priority order)

1. **State the premise early.** The pond villager (`villager_175_28`) stands 4
   tiles from Ariana and currently says pure filler. Give her the setup: the
   duck *is* Ariana, and Irene did it over the overdue DVD. Two lines close the
   biggest hole in the game.
2. **Set up the boss's opener.** Irene's first line ("Oh — you're here about
   the DVD…") should feel earned by the time you reach her — the villager beat
   above plus the existing library warnings do that. Optionally sharpen her
   five lines (they're decent already).
3. **Resolve it.** After the boss, nothing changes at the pond and the win
   screen only says "Irene has been defeated." **The win screen already has a
   Label named `Ariana`** (in `win_screen.tscn`) — it just holds Irene's text
   by mistake. Give it Ariana's actual closing line (world-brief promises
   "Message received. I'm still renting it again." — or write a better one).
4. **Kill the duplicate joke.** Evan's first dialogue line is the *same string*
   as his shop sign ("Toasted, or the old way?"), and the "only stand in the
   valley" punchline is told by both Evan and a nearby villager. Give each
   speaker a distinct line.

## Your writable surface (~22 strings total)

| Where | File | What lives there |
|---|---|---|
| Villagers, Ariana, Evan, library door | `scripts/dialogue_data.gd` | 7 stable ids, **arbitrary-length** line arrays + a name label each |
| Irene's 5 fight lines | `scripts/boss_irene.gd` | `start_line`/`early_line`/`mid_line`/`late_line`/`defeat_line` `@export`s (float over her head 3.5s — NOT via the dialogue box) |
| Shop sign one-liner | `scripts/shop_sign.gd` | the proximity label |
| Win screen | `scenes/win_screen.tscn` | two Labels (`Title`, `Ariana`) |
| Title | `scenes/player_select.tscn` | title + subtitle |

### The dialogue ids (in `dialogue_data.gd`) and where they stand
- `villager_63_19` — by Evan's stall (west)
- `villager_166_20` — near the library approach (east) — the Irene-warner
- `villager_175_28` — **the pond villager, next to Ariana** — give this one the premise
- `villager_46_30` — by the windmill (west)
- `ariana` — the duck at the pond (179,28)
- `evan` — the shopkeeper at his stall (62,16)
- `library_door` — the line shown at the library entrance

## Rules and gotchas

- **Don't move NPCs.** Villager ids are welded to their map cell
  (`villager_<x>_<y>`); if a villager is relocated in the map, its lines
  silently detach and it says "…". If you want a new speaker, it needs a
  matching `N` cell in `island_map.gd` first (that's a code/map task, not
  yours — flag it).
- **No branching, conditions, or portraits exist.** Lines are linear, advance
  on the interact key, and can't (yet) react to game state. A *conditional*
  post-boss Ariana line needs a small code primitive (R4-23) — if you want it,
  ask; otherwise write her one line and it's fine.
- **Say "pond," not "lake"** — world-brief and Ariana's home are the pond, but
  a placeholder line calls it a lake. Keep it consistent.
- **The title subtitle currently spoils the antagonist** ("A CO-OP PATH TO
  IRENE") on a screen that also offers 1-player. Consider something
  premise-flavored that doesn't name the boss ("RETURN THE DVD." sets up her
  opener for free).
- **Keep it short and spoken.** The current placeholders that read as
  generated ("They say the path east goes somewhere new," "Nobody remembers
  who built it") are patch-note voice — no villager talks like that.

## Handing it back

Edit `scripts/dialogue_data.gd` (and the four other text locations if you want
them), commit on `story/dialogue-pass`, open a PR. It touches no shared
hotspot, so it merges independently of every other track.
