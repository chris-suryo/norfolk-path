extends RefCounted

## GENERATED interior map — do not hand-edit; regenerate with
## `python tools/bake_interior.py` (emits this + the baked ground PNG).
## Symbols: X wall/solid furniture (collision), _ floor, S spawn,
## > exit mat (back out).
## Packed into the Web export as a resource; consumed via LevelRegistry.

const MAP := """
XXXXXXXXXXX
XXXXXXXXXXX
XXX______XX
XXX______XX
X__XXXXX__X
X__XXXXX__X
X_________X
X____S____X
XXXXX>XXXXX
"""
