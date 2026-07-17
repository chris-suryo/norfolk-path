extends RefCounted

## GENERATED interior map — do not hand-edit; regenerate with
## `python tools/bake_interior.py` (emits this + the baked ground PNG).
## Symbols: X wall/solid furniture (collision), _ floor, S spawn,
## > exit mat (back out).
## Packed into the Web export as a resource; consumed via LevelRegistry.

const MAP := """
XXXXXXXXXXXXXX
XXXXXXXXXXXXXX
XXX________XXX
XXX_________XX
XX__________XX
XX____XX_____X
X_____X______X
X_____X_____XX
X_X_________XX
X______S_____X
XXXXXXX>XXXXXX
"""
