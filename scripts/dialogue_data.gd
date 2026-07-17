class_name DialogueData
extends RefCounted

## THE story handoff file: every talkable thing's name + lines live here, keyed
## by npc id. The story session edits ONLY this file (same writer/coder split as
## the map briefs) — ids are stable, the build session never rewords content.
##
## Ids: villagers are "villager_<map x>_<map y>" (their cell in island_map.gd),
## plus "ariana" (the goose) and "library_door" (Irene at the library).
##
## Lines are the round-4 story pass — final copy, wired in verbatim.

const LINES := {
	"villager_63_19":
	{
		"name": "Villager",
		"lines":
		[
			"I don't know what a 'six-inch' is. I ask for one every week.",
			"He used to do surgery, you know. Now it's the sandwiches. Good for him.",
		],
	},
	"villager_166_20":
	{
		"name": "Villager",
		"lines":
		[
			"Best advice: don't mention the DVD, don't make eye contact.",
			"If it comes to that, most people would rather be the goose. Just so you know.",
		],
	},
	"villager_175_28":
	{
		"name": "Villager",
		"lines":
		[
			"I've named every duck on this pond. She's not even a duck — that's the trouble.",
			"Not really a goose either, if you want the truth. Library business. Irene doesn't warn twice.",
		],
	},
	"villager_46_30":
	{
		"name": "Villager",
		"lines":
		[
			"I've narrowed it down to three suspects. I'm not naming names yet.",
			"The blacksmith has an alibi. The blacksmith always has an alibi.",
		],
	},
	"ariana":
	{
		"name": "Ariana",
		"lines": ["Honk.", "(Translation: she literally does not care.)"],
	},
	"evan":
	{
		"name": "Evan",
		"lines":
		[
			"Welcome to Subway. What can I get started for you today?",
			"Six-inch or footlong?",
		],
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
