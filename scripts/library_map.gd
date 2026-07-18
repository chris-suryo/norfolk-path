extends RefCounted

## GENERATED interior map — do not hand-edit; regenerate with
## `python tools/bake_interior.py` (emits this + the baked ground PNG).
## Symbols: X wall/solid furniture (collision), _ floor, S spawn,
## > exit mat (back out).
## Packed into the Web export as a resource; consumed via LevelRegistry.

const MAP := """
XXXXXXXXXXXXXXXXX
XXXXXXXXXXXXXXXXX
XXXXXXX_X_XXXXXXX
XXXXXXX_X_XXXXXXX
XX______________X
XXXXXXX____XXXXXX
X_XXXXX____XXXXXX
X_______________X
X_______________X
XX_____________XX
XX______S______XX
XXXXXXXX>XXXXXXXX
"""
