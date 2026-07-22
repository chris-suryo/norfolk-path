extends RefCounted

## GENERATED interior map — do not hand-edit; regenerate with
## `python tools/bake_interior.py` (emits this + the baked ground PNG).
## Symbols: X wall/solid furniture (collision), _ floor, S spawn,
## > exit mat (back out), ! examine-trigger (walkable; main.gd spawns
## an Interactable here — dialogue id note_<level>_<x>_<y>).
## Packed into the Web export as a resource; consumed via LevelRegistry.

const MAP := """
XXXXXXXXXXXXXX
XXXXXXXXXXXXXX
XXX________XXX
XXX_________XX
XX_!________XX
XX____XX_____X
X_____X______X
X_____X_____XX
X_X_________XX
X______S_____X
XXXXXXX>XXXXXX
"""
