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
	# PLACEHOLDER — the onboarding guide at the village spawn. Chris's locked
	# round-5 copy replaces these lines (quest + teach-the-ropes; see the story
	# brief). Keeping the control keys in-text is a stand-in until then.
	"guide":
	{
		"name": "Guide",
		"lines":
		[
			"You saw it too, then. The goose — that was Ariana.",
			"Irene runs the library. She does this when a book comes back late.",
			"Move with WASD. Talk with E. The library's east. Go bring her home.",
		],
	},
	"library_door":
	{
		"name": "Irene",
		"lines":
		[
			"You're here for Ariana. I assumed as much.",
			"Go on, then — why are you here?",
		],
		"choices":
		{
			"at": 1,
			"options":
			[
				{
					"label": "To return the DVD.",
					"reply": "Good. That's all this ever needed to be.",
					"flag": "dvd",
				},
				{
					"label": "To bring my friend back.",
					"reply": "That's not really what this is about. But go ahead.",
					"flag": "friend",
				},
			],
		},
	},
	# PLACEHOLDER — interior examine-triggers (the "!" cells baked into each
	# room). Ids are note_<level>_<x>_<y>, one per readable spot; the comment on
	# each says which piece it sits in front of, so Chris's real copy is a
	# find-and-fill. These give every house a bit of story surface without a new
	# system (pure DialogueBox reuse). Move/add/remove by editing the room's
	# "notes" in tools/bake_interior.py + re-baking; check_levels enforces that
	# every "!" cell has an entry here and vice versa.
	"note_cottage_2_4":
	{
		"name": "Hearth",
		"lines": ["[PLACEHOLDER] Cold ashes, and a mantel worn smooth by somebody's habit."],
	},
	"note_home_a1_1_4":
	{
		"name": "Stove",
		"lines": ["[PLACEHOLDER] A pot left on the hob. Whoever lives here left in a hurry."],
	},
	"note_home_a2_3_5":
	{
		"name": "Plants",
		"lines":
		["[PLACEHOLDER] Every pot is labelled in a careful hand. This one just says 'DO NOT'."],
	},
	"note_home_g2_3_6":
	{
		"name": "Fireside",
		"lines": ["[PLACEHOLDER] Two chairs pulled close. A conversation paused mid-sentence."],
	},
	"note_home_j1_3_4":
	{
		"name": "Bedside",
		"lines": ["[PLACEHOLDER] A book face-down on the covers. The bookmark is a library slip."],
	},
	"note_home_e1_7_4":
	{
		"name": "Family hearth",
		"lines": ["[PLACEHOLDER] Chalk marks up the chimney brick — a family measuring the years."],
	},
	"note_library_4_4":
	{
		"name": "Shelves",
		"lines":
		["[PLACEHOLDER] Overdue notices, filed alphabetically. Yours would be near the front."],
	},
	"note_library_11_4":
	{
		"name": "Shelves",
		"lines":
		["[PLACEHOLDER] A gap where one book should be. The card still lists who took it."],
	},
	"note_barn_int_3_4":
	{
		"name": "Stores",
		"lines": ["[PLACEHOLDER] Barrels tallied in chalk. Someone's counting is optimistic."],
	},
	"note_windmill_3_6":
	{
		"name": "Worktable",
		"lines": ["[PLACEHOLDER] A miller's ledger, open to a page of debts. One name is circled."],
	},
	# PLACEHOLDER — interior residents (the "P" cells baked into each room). Ids
	# are person_<level>_<x>_<y>, one standing villager per house; Chris's real
	# copy is a find-and-fill. Move/add/remove by editing the room's "people" in
	# tools/bake_interior.py + re-baking; check_levels enforces every "P" cell has
	# an entry here and vice versa.
	"person_cottage_9_7":
	{
		"name": "Resident",
		"lines": ["[PLACEHOLDER] Mind the ashes — that hearth's older than the house."],
	},
	"person_home_a1_8_6":
	{
		"name": "Cook",
		"lines": ["[PLACEHOLDER] I'd offer you something, but the pot's been on since morning."],
	},
	"person_home_a2_7_6":
	{
		"name": "Gardener",
		"lines": ["[PLACEHOLDER] Don't touch the one marked 'DO NOT'. I mean it."],
	},
	"person_home_g2_9_7":
	{
		"name": "Resident",
		"lines": ["[PLACEHOLDER] Pull up a chair. We were just talking about you. ...Not really."],
	},
	"person_home_j1_6_5":
	{
		"name": "Lodger",
		"lines": ["[PLACEHOLDER] Spare room, spare bed. You're welcome to neither."],
	},
	"person_home_e1_10_7":
	{
		"name": "Resident",
		"lines":
		["[PLACEHOLDER] The chalk marks on the chimney? One for every winter we've stayed."],
	},
	"person_library_13_9":
	{
		"name": "Reader",
		"lines": ["[PLACEHOLDER] Quietly, please. Irene hears everything in here."],
	},
	"person_barn_int_10_8":
	{
		"name": "Farmhand",
		"lines":
		["[PLACEHOLDER] Careful past the barrels — the tally's optimistic, the floor isn't."],
	},
	"person_windmill_7_6":
	{
		"name": "Miller",
		"lines":
		["[PLACEHOLDER] Grain in, flour out. The debts in the ledger stay right where they are."],
	},
}

const DEFAULT := {"name": "???", "lines": ["..."]}


## The entry for an id; a missing id gets the silent fallback instead of a
## crash, so a renamed villager cell can never break the build.
static func entry(npc_id: String) -> Dictionary:
	return LINES.get(npc_id, DEFAULT)
