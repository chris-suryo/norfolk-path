# Playtest automation

Two complementary rigs drive the actual game with scripted input. Neither
replaces a human run — they make regressions cheap to catch between human runs.

## 1. CI browser playtest (`.github/workflows/playtest.yml`)

**What:** GitHub Actions job (manual `workflow_dispatch` for now) that exports
the Web preset with the exact pinned steps deploy-web uses, serves it on
localhost inside the runner, and runs `tools/playtest/ci_driver.py`: Playwright
Chromium (software WebGL via SwiftShader), real trusted keyboard input, and a
screenshot at every checkpoint.

**Flow it exercises:** boot → title renders → **input-proof assertion** (the
menu highlight must move on ArrowDown, else the run fails immediately — no
vacuous passes) → 1-player → creator (two option cycles) → confirm → in-game
walk in all four directions → sword swing → dodge roll.

**Output:** artifact `playtest-<sha>` (13 numbered PNGs). Review them like the
visual-review artifact; any blank frame fails the job on its own.

**How to run:** Actions tab → playtest → Run workflow (pick the branch), or
`POST /repos/.../actions/workflows/playtest.yml/dispatches`.

**Limits (deliberate):**
- Pixel-level assertions only. Game-state hooks (`window.np_debug`) are a
  recorded deferral in docs/playtest-findings.md — revisit if pixel checks
  prove too blunt.
- No timing-sensitive tests (roll i-frames, max-range spacing): a scripted
  driver cannot time 0.16 s windows honestly. Those stay on the human/local
  round-2 checklist.
- 2P co-op is scriptable later (both key sets are one keyboard) — start 1P.

## 2. Local Windows rig (`tools/playtest/` driver scripts)

The round-1 playtest drove the NATIVE build with Win32 `PostMessage` scan-code
input + `PrintWindow` capture — blind but real engine input, no browser layer.
The scripts live in `tools/playtest/` (committed from the local session; see
docs/playtest-findings.md "Methodology" for the recipe if they're missing).
Use that rig for anything the CI bot can't reach: native-only behavior, editor
builds, manual-timing assists.

## Feeding results back

Findings from either rig go into `docs/playtest-findings.md` in the structured
per-issue format (Area / Severity / Observed / Expected / Screenshot), same as
round 1. The cloud session triages and fixes from there.
