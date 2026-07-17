extends RefCounted

## GENERATED interior map — do not hand-edit; regenerate with
## `python tools/bake_interior.py` (emits this + the baked ground PNG).
## Symbols: X wall/solid furniture (collision), _ floor, S spawn,
## > exit mat (back out).
## Packed into the Web export as a resource; consumed via LevelRegistry.

const MAP := """
XXXXXXXXXXXXX
XXXXXXXXXXXXX
XXX___XX___XX
XXX___XX___XX
XXX_________X
X___XXXXX__XX
X___XXXXX__XX
X___________X
X_____S_____X
XXXXXX>XXXXXX
"""
