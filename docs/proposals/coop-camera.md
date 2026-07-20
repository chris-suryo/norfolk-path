# 2P camera rule — the deliberately-unsolved problem

Today the camera tracks the midpoint of both players with **no constraint**:
walk apart and both players drift to the screen edges, then off them. This was
left unsolved on purpose so the real failure could be felt in playtest first.
Deciding the rule changes how co-op FEELS, so it's yours. Three candidate
rules, all implementable in `follow_camera.gd`/`midpoint.gd` without touching
the viewport pipeline:

## Option A — soft leash (RECOMMENDED)

Players can't move further than ~0.8 screen-widths apart: the trailing
player's movement away from the midpoint is damped to zero at the leash
limit (classic beat-em-up rule).

- Feel: cooperative by force — you stay on one screen, period.
- Cost: S. One clamp in Player movement against the camera rect.
- Risk: the damping can feel like an invisible wall; needs feel-tuning
  (which is exactly what your playtest is for).

## Option B — auto zoom-out

The camera zooms out (within Far..Normal bounds) as players separate, zooms
back in as they regroup. No movement constraint.

- Feel: freedom preserved; the world literally gets smaller when you split up.
- Cost: S/M. Zoom = f(player distance), clamped, slewed; interacts with the
  new zoom-persist rule (#39) — the auto-zoom must not clobber the chosen
  preset when players regroup.
- Risk: ultrawide is a first-class target — at Far zoom on ultrawide the
  16px art gets small; and free zoom-out is a stealth difficulty cheat
  (see more enemies sooner).

## Option C — soft split-screen

When separation exceeds a threshold, the viewport splits into two half-width
cameras; merges back on regroup (Lego-games style).

- Feel: the premium solution; genuinely lets players do different things.
- Cost: L — SubViewports, two cameras, the merge/split transition, HUD
  duplication questions. "True split-screen cameras" is on the explicit v1
  exclusion list.
- Risk: biggest engineering item on the menu for a mode you haven't yet
  confirmed is fun.

## Decision needed

A / B / C — or "leave unsolved for beta" (legitimate: solo is the primary
mode). If A or B, I'd stage it behind the co-op correctness fixes (#46) so
feel-judgment isn't polluted by the projectile/revive bugs.
