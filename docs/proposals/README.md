# Beta decision proposals — Chris's calls, prepped

Each doc here is a decision the build session deliberately did NOT make
autonomously (per the no-major-design-choices rule). Each comes with scoped
options, a recommendation, and the cost of each path — so deciding is a
read-and-pick, not a design session.

| Decision | Doc | Recommendation (mine, not binding) |
|---|---|---|
| Shop / economy | `economy-options.md` | Option B (barter chains, no currency) |
| 2P camera rule | `coop-camera.md` | Option A (soft leash) |
| Difficulty selector | `difficulty-knobs.md` | Defer; ship one tuned difficulty |
| Day/night | `day-night.md` | Defer past beta; cheap dusk-tint if wanted |

Two quick yes/no calls that need no doc:

- **Boss contact damage** — Irene's `ContactHitbox` exists but is inert:
  touching her costs nothing, so the optimal strategy is face-hugging. Turning
  it on is one flag + a damage value, but it changes fight difficulty — your
  call. (Round-4 finding; deliberately excluded from the bug-fix PRs.)
- **Cove: keep or cut for beta** — round 4 said "give it a purpose or cut
  it." The Harbor Road PR (#45) + the queued cove-population slice make the
  "keep" case: guards + the Whetstone chest + a dockhand give it ~5 minutes of
  content for ~0 new systems. If you'd rather cut, the east-edge transition is
  one registry line to remove; everything else stays valley-only.

Also parked here for the record: **paid-pack licensing** — the exported web
build ships art from the paid Cute Fantasy pack (the repo itself is private;
the deployed game is public). Itch asset licenses generally allow use in
builds while forbidding redistribution of raw assets — the baked-into-a-game
case is normally fine, but confirming the exact license text is a 2-minute
read on the pack page that only you (the purchaser) can do.
