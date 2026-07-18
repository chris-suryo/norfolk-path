extends RefCounted

## GENERATED interior map — do not hand-edit; regenerate with
## `python tools/bake_interior.py` (emits this + the baked ground PNG).
## Symbols: X wall/solid furniture (collision), _ floor, S spawn,
## > exit mat (back out).
## Packed into the Web export as a resource; consumed via LevelRegistry.

const MAP := """
XXXXXXXXXXXXX
XXXXXXXXXXXXX
XX_______XX_X
XX_______XX_X
X___XXXXX___X
XX__XXXXX___X
XX__________X
X__________XX
X_____S____XX
XXXXXX>XXXXXX
"""
