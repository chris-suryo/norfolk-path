class_name BuildInfo
extends RefCounted

## Build identity for the title screen. SHA stays "dev" in the repo; CI
## (deploy-web + playtest workflows) sed-replaces it with the short commit
## hash right before the export, so every shipped build names its exact
## commit — "what version am I on" is never a mystery again (round-2 ask).

const SHA := "dev"
