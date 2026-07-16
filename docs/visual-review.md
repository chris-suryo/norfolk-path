# Visual review

Use a visual-review snapshot whenever the map, prop placement, terrain, or
ambient-life behavior changes. The point is not pixel-perfect approval; it is a
repeatable way to catch mechanical repetition, unclear navigation, awkward
overlap, and layout choices that make the world feel generated instead of
authored.

## Capture

From the repository root:

```powershell
python tools\capture_visual_review.py
```

The command creates a revision-labelled folder under
`artifacts/visual-review/`. Each folder contains:

- `overview.png` — the whole 192 x 48 map;
- `west.png`, `middle.png`, and `east.png` — consistent zone crops;
- `manifest.json` — revision and capture metadata;
- `README.md` — the review checklist packaged with the images.

The folder is local/generated and ignored by Git. On every push and pull
request, GitHub Actions captures the same set and saves it as a **Visual Review**
workflow artifact for 90 days.

To produce a named comparison set while iterating locally:

```powershell
python tools\capture_visual_review.py --label before-farm-polish
python tools\capture_visual_review.py --label after-farm-polish
```

## Review loop

1. Compare the overview first: route clarity, visual rhythm, and whether each
   zone has a distinct identity.
2. Review each crop at 100%: repeated sprites, lone props, crowded clusters,
   arbitrary straight lines, and bad tall-sprite overlaps.
3. Play the affected area in Godot. The image renderer is the source of truth
   for layout, but the game is the source of truth for collision, animation,
   camera, and feel.
4. Record each finding as a blocker, traversal issue, animation issue, or
   polish item. Fix the smallest coherent group, capture again, then compare.

### Authoring checks

- Does each prop support a place or activity, rather than merely fill space?
- Do groups vary in spacing, facing, animation phase, and behavior?
- Are paths purposeful and do they leave comfortable room beside buildings?
- Do foreground objects frame the player rather than hide points of interest?
- Would a player infer a story from the scene without needing an explanation?

For live-game moments that the map renderer cannot show—such as animal motion,
combat, menus, or collision—capture a normal screenshot with `Win` + `Shift` +
`S` and attach it with the relevant snapshot name.
