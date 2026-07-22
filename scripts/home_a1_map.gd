extends RefCounted

## GENERATED interior map — do not hand-edit; regenerate with
## `python tools/bake_interior.py` (emits this + the baked ground PNG).
## Symbols: X wall/solid furniture (collision), _ floor, S spawn,
## > exit mat (back out), ! examine-trigger (walkable; main.gd spawns
## an Interactable here — dialogue id note_<level>_<x>_<y>), P resident
## (walkable; main.gd spawns a VillagerNpc + Interactable person_<lvl>_<x>_<y>).
## Packed into the Web export as a resource; consumed via LevelRegistry.

const MAP := """
XXXXXXXXXXX
XXXXXXXXXXX
XXX______XX
XXX______XX
X!_XXXXX__X
X__XXXXX__X
X_______P_X
X____S____X
XXXXX>XXXXX
"""
