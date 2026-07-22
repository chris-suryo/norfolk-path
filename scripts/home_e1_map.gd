extends RefCounted

## GENERATED interior map — do not hand-edit; regenerate with
## `python tools/bake_interior.py` (emits this + the baked ground PNG).
## Symbols: X wall/solid furniture (collision), _ floor, S spawn,
## > exit mat (back out), ! examine-trigger (walkable; main.gd spawns
## an Interactable here — dialogue id note_<level>_<x>_<y>).
## Packed into the Web export as a resource; consumed via LevelRegistry.

const MAP := """
XXXXXXXXXXXXX
XXXXXXXXXXXXX
XXX___XX___XX
XXX___XX___XX
XXX____!____X
X___XXXXX__XX
X___XXXXX__XX
X___________X
X_____S_____X
XXXXXX>XXXXXX
"""
