# Day/night — vibe check + cost

No time-of-day system exists. The question is whether the atmosphere payoff
justifies a system whose feel you can only judge in-engine.

**Vibe reference:** `day-night-vibe.png` (this folder) — the village slice at
current daylight vs. a cheap dusk grade (brightness 0.62 + a 22% cool-blue
blend). This is a Pillow mock of what a full-screen `CanvasModulate` would do;
the real thing is the same idea live.

## Cheapest real version (S)

A `CanvasModulate` node whose color lerps through a fixed day cycle (or is
just SET to dusk for certain beats — e.g. the boss approach). Lamps already
exist as props; at dusk their glow would carry the wayfinding (the Harbor
Road and Overlook lamp avenues were placed with this in mind).

- Cost: S for a static "dusk beat"; M for a rolling cycle (needs a
  time-of-day owner on Game + decisions about whether NPCs/enemies react).
- Risk: pure-tint dusk can read as "my monitor is broken" without lamp glow
  sprites/halos; halos are new art or shader work.

## Recommendation

**Defer past beta.** It's atmosphere-only (no system hooks want it yet), it
competes with audio for the "game feel" budget, and audio is further along
(foundation already landed). If you want ONE taste of it cheap: a fixed dusk
grade on the post-boss walk home would be a single CanvasModulate set + revert
— a scoped beat, not a system.
