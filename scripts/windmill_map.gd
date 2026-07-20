extends RefCounted

## GENERATED interior map — do not hand-edit; regenerate with
## `python tools/bake_interior.py` (emits this + the baked ground PNG).
## Symbols: X wall/solid furniture (collision), _ floor, S spawn,
## > exit mat (back out).
## Packed into the Web export as a resource; consumed via LevelRegistry.

const MAP := """
XXXXXXXXXXX
XXXXXXXXXXX
XXX_____XXX
XXX_____XXX
XX__XXX__XX
XX__XXX__XX
XXX_____XXX
XX___S___XX
XXXXX>XXXXX
"""
