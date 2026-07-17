extends RefCounted

## GENERATED interior map — do not hand-edit; regenerate with
## `python tools/bake_interior.py` (emits this + the baked ground PNG).
## Symbols: X wall/solid furniture (collision), _ floor, S spawn,
## > exit mat (back out).
## Packed into the Web export as a resource; consumed via LevelRegistry.

const MAP := """
XXXXXXXXXXX
XXXXXXXXXXX
XXXX__XX_XX
XXXX__XX_XX
XXX_______X
XX_______XX
XX_______XX
X____S____X
XXXXX>XXXXX
"""
