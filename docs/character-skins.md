# Character skins and creator contract

Character Creator v1 stores two JSON-safe appearance profiles with these keys:
`hair_style`, `hair_color`, `shirt_style`, `shirt_color`, `pants_color`,
`shoes_color`, and `hat`. They affect art only; collision, combat values, input,
and camera behavior are independent of a profile.

## V1 catalog

- Hair styles 1-6 in Black, Blonde, Brown, Ginger, and Grey.
- Farmer, Lumberjack, and Classic shirts in their authored colors.
- Classic pants and shoes in their authored colors; optional Farmer Hat.
- The base face is fixed. Eyes and expressions are deliberately deferred until
  they have compatible overlay art.

## Adding a project skin later

Put source-controlled assets under `assets/game/creator/` and add their IDs to
`scripts/appearance_catalog.gd`. Every modular layer must be a transparent
`576x3584` PNG: 9 columns x 56 rows of 64px frames, aligned to the supplied body
sheet. It must provide the current animated rows: idle 0-2, walk 3-5, sword
6/9/12, roll 17-19, and downed row 53. The supplied sword is a separate
`256x576` 4-column × 9-row attack overlay; a custom playable skin needs an
equivalent weapon overlay for attack frames.

Run `python tools/check_character_layers.py` and inspect the Visual Review
`character-creator.png` before publishing. Runtime browser file upload is not a
V1 feature: imported skins are added to the project and deployed normally.
