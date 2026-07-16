# Demo polish plan

This is the active work order for the playable demo. It supersedes the older
"next" notes in historical planning documents without rewriting that history.

## 1. Visual baseline — delivered

Run `python tools/capture_visual_review.py` before and after every world-layout
change. Review the overview plus the west, middle, and east crops for repeated
motifs, unclear routes, isolated props, and awkward tall-sprite overlaps.
GitHub Actions retains an equivalent snapshot for every push and pull request.

## 2. World traversal and composition — first pass delivered

- Building blockers are inset and shifted to allow close wall approach and
  corner travel without allowing entry into buildings.
- Generic door-to-road cobble strips are now short, intentional doorsteps.
- The windmill is beside the wheat rather than on it; stray farm hives were
  consolidated into one purposeful orchard-edge hive.

## 3. Ambient-life variety — first pass delivered

- Ambient actors start on independent animation phases and facing directions.
- Chickens now have low-radius wandering; butterflies follow small flying loops.
- Keep ambient actors non-blocking and visually separated so repeated sprites
  read as a flock rather than copied stamps.

## 4. Readability pass — first pass delivered

- Pause-menu and mode-select option contrast is raised.
- Correct animal and player placements that visually land on roofs or clip
  foreground art.

## 5. Demo replay — next

Run a fresh two-player path from title to Irene. Use those findings to decide
whether the following slice is distinct player art or further combat/content
work. Boss Phase 2 remains deferred until this loop is stable.
