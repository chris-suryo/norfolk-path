class_name DialogueData
extends RefCounted

## THE story handoff file: every talkable thing's name + lines live here, keyed
## by npc id. The story session edits ONLY this file (same writer/coder split as
## the map briefs) — ids are stable, the build session never rewords content.
##
## Ids: villagers are "villager_<map x>_<map y>" (their cell in island_map.gd),
## plus "ariana" (the duck) and "library_door" (Irene's sealed library).
##
## ALL LINES BELOW ARE PLACEHOLDERS awaiting the story pass — deliberately
## bland so nothing here reads as canon.

const LINES := {
	"villager_63_19":
	{
		"name": "Villager",
		"lines":
		[
			"Evan's stand has the freshest goods in the valley.",
			"Well... it has the ONLY goods in the valley.",
		],
	},
	"villager_166_20":
	{
		"name": "Villager",
		"lines":
		[
			"The library? I'd steer clear.",
			"Irene takes late returns... personally.",
		],
	},
	"villager_175_28":
	{
		"name": "Villager",
		"lines": ["Lovely by the lake, isn't it?", "They say the path east goes somewhere new."],
	},
	"villager_46_30":
	{
		"name": "Villager",
		"lines": ["The windmill's been creaking all week.", "Nobody remembers who built it."],
	},
	"ariana":
	{
		"name": "Ariana",
		"lines": ["Quack.", "(She seems pleased you stopped by.)"],
	},
	"evan":
	{
		"name": "Evan",
		"lines": ["Toasted, or the old way?", "Best stand in the valley. Only stand, too."],
	},
	"library_door":
	{
		"name": "Library",
		"lines": ["Irene's library. The door stands open — mind the shelves."],
	},
}

const DEFAULT := {"name": "???", "lines": ["..."]}


## The entry for an id; a missing id gets the silent fallback instead of a
## crash, so a renamed villager cell can never break the build.
static func entry(npc_id: String) -> Dictionary:
	return LINES.get(npc_id, DEFAULT)
