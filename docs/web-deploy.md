# Web deploy — get a build in front of a browser on another machine

## Automatic (default, once set up)

Every push to `claude/slice-1-godot-toolchain-ij6e9w` triggers
`.github/workflows/deploy-web.yml`: it headlessly exports the Godot **Web**
preset and deploys straight to the existing Vercel project's **production**
URL. No local export, no manual drag-and-drop — push and it's live in a couple
of minutes.

**Why this can run in GitHub Actions but not the cloud build session:** that
sandbox's egress policy blocks `godotengine.org`/`github.com` release downloads
(that's what the editor + the ~500 MB Web export templates need — see
`.github/workflows/ci.yml`'s history for the same wall hit earlier). GitHub's
own Actions runners aren't behind that block, so the export genuinely happens
there instead.

### One-time setup (you have to do this — nothing here is automatable from either session)

1. **Get a Vercel token:** vercel.com → **Settings → Tokens → Create**.
2. **Get your org/project IDs** — either run `vercel link` once locally in the
   repo (writes `.vercel/project.json` with both `orgId` and `projectId` — read
   them out, don't commit the file) or copy them straight from the existing
   Vercel project's **Settings** page.
3. **Add all three as GitHub repo secrets:** on the repo, **Settings → Secrets
   and variables → Actions → New repository secret** —
   - `VERCEL_TOKEN`
   - `VERCEL_ORG_ID`
   - `VERCEL_PROJECT_ID`

Once those three secrets exist, every push deploys automatically. Watch it run
under the repo's **Actions** tab.

*(Pinned to your exact local Godot build — `v4.7-stable, official [5b4e0cb0f]`
— via `.github/workflows/deploy-web.yml`. If you ever upgrade Godot locally,
that workflow's two download URLs need bumping to match, or CI and your local
editor will drift apart.)*

## Manual fallback (still works, useful if CI is down or you want an instant local check)

Five-minute loop: pull → export in Godot → drag the export folder onto Vercel →
share the URL.

### 1. Pull the latest

```
git pull
```
on branch `claude/slice-1-godot-toolchain-ij6e9w` (checkout it first if you're
not already on it).

### 2. Export from Godot

Open the project in Godot 4.7 → **Project > Export…** → select the **Web**
preset (already configured, nothing to change) → **Export Project** → save to
`export/web/index.html` (the preset's default path — just confirm it, don't
retype it).

This produces a **folder**, `export/web/`, containing `index.html` plus a
`.wasm`, a `.pck`, and one or more `.js` files. You need the whole folder — the
game won't run from `index.html` alone.

*(Why this is simple: the Web preset already has threads OFF
(`variant/thread_support=false`), a deliberate choice so the build needs no
COOP/COEP cross-origin-isolation headers and runs from any plain static host —
no server config to fight with. Same reason the automated pipeline above needs
no special Vercel configuration either.)*

### 3. Deploy — vercel.com dashboard

1. Go to **vercel.com/new**.
2. Drag the whole **`export/web`** folder onto the page (not a zip — the folder
   itself, or select all its files together).
3. Vercel auto-detects it as a static site — no framework, no build command, no
   settings to touch. Click **Deploy**.
4. Copy the URL it gives you and open it on the other laptop.

Repeat steps 2–3 after any future manual export. Dropping onto the same Vercel
project creates a new deployment (keeps a history you can roll back to).

## Known risk (nothing to do yet, just watch for it)

Vercel enforces a per-file size limit on static uploads (comfortably large,
but a `.pck` can grow as the world/assets do). If a deploy ever fails on file
size — automatic or manual — check the `.pck` size in `export/web/` first;
that's almost certainly it.
