# Shop / economy — three scoped options

Today "the shop" is Evan's stall with a proximity one-liner. There is **no
currency, no inventory, no buy/sell anywhere**. Whatever you pick shapes the
reward loop for the rest of the game, which is why this is your call.

## Option A — keep the sign (do nothing)

The stall stays flavor. Chests remain the only reward channel.

- Cost: zero.
- Risk: "shop" keeps reading as a missing feature to playtesters.
- Fits: if beta scope is "finish the quest loop, polish what exists."

## Option B — barter chains, no currency (RECOMMENDED)

Evan (and later the dockhand) offers 1-2 **trades**: bring item X, get
upgrade/keepsake Y. X is a new quest-item class ("honey from the beehives",
"a book from the library") tracked as flags in the save — the same curated
additive-array pattern `upgrades`/`opened_chests` already use.

- Cost: S/M — a `quest_items` array on Game (save-additive), a trade branch in
  dialogue, 1-2 fetchable item spawns. No HUD changes needed beyond the
  existing pickup message.
- Why recommended: it makes the shop DO something and gives the world fetch
  reasons (lived-in!) without inventing money, prices, a shop UI, or balance
  work. Barter is also tonally right for a 6-cottage village.
- Risk: quest-item spawns need map/interior placement (pairs well with the
  queued interior-interactables slice).

## Option C — coins + a real shop UI

Enemies/chests drop coins; Evan sells 3 SKUs (heal, arrow upgrade, a vanity).

- Cost: L — currency field in the save, drop tables, a shop UI screen, price
  balancing, HUD coin counter. Every future reward needs pricing thought.
- Why not recommended (yet): it's the biggest system on the menu and mostly
  duplicates what chests already deliver. Worth revisiting if the game grows
  past one valley.

## Decision needed

Pick A, B, or C (or B-then-C). B can start immediately after the current PR
queue merges — its save-field pattern is already proven.
