class_name AppearanceCatalog
extends RefCounted

## The small, data-driven catalog used by both the character creator and the
## in-world player renderer. Profile values are stable IDs saved as plain JSON.

const ROOT := "res://assets/game/creator"
const BASE_PATH := ROOT + "/body/Player_Base_animations.png"
const HAT_PATH := ROOT + "/accessory/Farmer_Hat_1.png"
const SWORD_PATH := ROOT + "/tool/Iron_Sword.png"
const BOW_PATH := ROOT + "/tool/Wooden_Bow.png"

const HAIR_COLORS := ["Black", "Blonde", "Brown", "Ginger", "Grey"]
const SHIRT_STYLES := ["Farmer_Shirt", "Lumberjack_Shirt", "Classic"]
const PANTS_COLORS := ["Black", "Blue", "Brown", "Green", "Orange", "Pink", "Purple", "Red"]
const SHOES_COLORS := [
	"Black", "Blue", "Brown", "Green", "Orange", "Pink", "Purple", "Red", "White"
]
const SHIRT_COLORS := {
	"Farmer_Shirt":
	["Black", "Blue", "Green", "Orange", "Pink", "Purple", "Red", "White_and_Brown"],
	"Lumberjack_Shirt":
	["Black", "Blue", "Brown", "Green", "Orange", "Pink", "Purple", "Red", "White"],
	"Classic": ["Black", "Blue", "Brown", "Green", "Orange", "Pink", "Purple", "Red"],
}


static func default_profile(player_index: int = 1) -> Dictionary:
	if player_index == 2:
		return normalized(
			{
				"hair_style": 2,
				"hair_color": "Brown",
				"shirt_style": "Lumberjack_Shirt",
				"shirt_color": "Blue",
				"pants_color": "Blue",
				"shoes_color": "Brown",
				"hat": false,
			}
		)
	return normalized(
		{
			"hair_style": 1,
			"hair_color": "Black",
			"shirt_style": "Farmer_Shirt",
			"shirt_color": "Green",
			"pants_color": "Brown",
			"shoes_color": "Brown",
			"hat": false,
		}
	)


static func normalized(profile: Dictionary) -> Dictionary:
	var style := clampi(int(profile.get("hair_style", 1)), 1, 6)
	var hair_color := str(profile.get("hair_color", "Black"))
	if hair_color not in HAIR_COLORS:
		hair_color = HAIR_COLORS[0]

	var shirt_style := str(profile.get("shirt_style", "Farmer_Shirt"))
	if shirt_style not in SHIRT_STYLES:
		shirt_style = SHIRT_STYLES[0]
	var shirt_color := str(profile.get("shirt_color", "Green"))
	if shirt_color not in shirt_colors(shirt_style):
		shirt_color = shirt_colors(shirt_style)[0]

	var pants_color := str(profile.get("pants_color", "Brown"))
	if pants_color not in PANTS_COLORS:
		pants_color = PANTS_COLORS[0]
	var shoes_color := str(profile.get("shoes_color", "Brown"))
	if shoes_color not in SHOES_COLORS:
		shoes_color = SHOES_COLORS[0]

	return {
		"hair_style": style,
		"hair_color": hair_color,
		"shirt_style": shirt_style,
		"shirt_color": shirt_color,
		"pants_color": pants_color,
		"shoes_color": shoes_color,
		"hat": bool(profile.get("hat", false)),
	}


static func hair_path(profile: Dictionary) -> String:
	var value := normalized(profile)
	return ROOT + "/hair/Hair_%d_%s.png" % [value.hair_style, value.hair_color]


static func shirt_path(profile: Dictionary) -> String:
	var value := normalized(profile)
	if value.shirt_style == "Classic":
		return ROOT + "/shirt/Shirt_1_%s.png" % value.shirt_color
	return ROOT + "/shirt/%s_1_%s.png" % [value.shirt_style, value.shirt_color]


static func pants_path(profile: Dictionary) -> String:
	var value := normalized(profile)
	return ROOT + "/pants/Pants_1_%s.png" % value.pants_color


static func shoes_path(profile: Dictionary) -> String:
	var value := normalized(profile)
	return ROOT + "/shoes/Shoes_1_%s.png" % value.shoes_color


static func shirt_colors(style: String) -> Array:
	return SHIRT_COLORS.get(style, SHIRT_COLORS["Farmer_Shirt"])
