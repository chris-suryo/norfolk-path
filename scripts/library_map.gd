extends RefCounted

## GENERATED interior map — do not hand-edit; regenerate with
## `python tools/bake_interior.py` (emits this + the baked ground PNG).
## Symbols: X wall/solid furniture (collision), _ floor, S spawn,
## > exit mat (back out).
## Packed into the Web export as a resource; consumed via LevelRegistry.

const MAP := """
XXXXXXXXXXXXXXXXX
XXXXXXXXXXXXXXXXX
XXXXXXX_X_XXXXX_X
XXXXXXX_X_XXXXX_X
X_______________X
XXXXXXX__XXXXX__X
XXXXXXX__XXXXX__X
XX____________X_X
XX____________X_X
X_______________X
X_______S_______X
XXXXXXXX>XXXXXXXX
"""
