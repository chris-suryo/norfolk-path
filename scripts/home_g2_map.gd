extends RefCounted

## GENERATED interior map — do not hand-edit; regenerate with
## `python tools/bake_interior.py` (emits this + the baked ground PNG).
## Symbols: X wall/solid furniture (collision), _ floor, S spawn,
## > exit mat (back out).
## Packed into the Web export as a resource; consumed via LevelRegistry.

const MAP := """
XXXXXXXXXXXXX
XXXXXXXXXXXXX
X_XX_______XX
X_XX_______XX
X___________X
XX__XXXXX___X
XX__XXXXX__XX
X__________XX
X_____S_____X
XXXXXX>XXXXXX
"""
