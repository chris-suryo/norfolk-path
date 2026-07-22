extends RefCounted

## GENERATED interior map — do not hand-edit; regenerate with
## `python tools/bake_interior.py` (emits this + the baked ground PNG).
## Symbols: X wall/solid furniture (collision), _ floor, S spawn,
## > exit mat (back out), ! examine-trigger (walkable; main.gd spawns
## an Interactable here — dialogue id note_<level>_<x>_<y>), P resident
## (walkable; main.gd spawns a VillagerNpc + Interactable person_<lvl>_<x>_<y>).
## Packed into the Web export as a resource; consumed via LevelRegistry.

const MAP := """
XXXXXXXXXXXXX
XXXXXXXXXXXXX
XX_______XX_X
XX_______XX_X
X___XXXXX___X
XX__XXXXX___X
XX_!________X
X________P_XX
X_____S____XX
XXXXXX>XXXXXX
"""
