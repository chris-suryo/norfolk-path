# Web deploy — get a build in front of a browser on another machine

Five-minute loop: pull → export in Godot → drag the export folder onto Vercel →
share the URL. Run this whenever you want a fresh build live (every export is a
new deploy; nothing here is one-time setup).

**Why the build session can't do this part:** the cloud sandbox has no Godot
binary, and its network policy blocks `godotengine.org`/`github.com` release
downloads (that's what an editor + the ~500 MB Web export templates need) — see
`.github/workflows/ci.yml` for the same constraint hit earlier. Exporting has
always been your step; this doc just makes "export → live link" fast.

## 1. Pull the latest

```
git pull
```
on branch `claude/slice-1-godot-toolchain-ij6e9w` (checkout it first if you're
not already on it).

## 2. Export from Godot

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
no server config to fight with.)*

## 3. Deploy — vercel.com dashboard

1. Go to **vercel.com/new**.
2. Drag the whole **`export/web`** folder onto the page (not a zip — the folder
   itself, or select all its files together).
3. Vercel auto-detects it as a static site — no framework, no build command, no
   settings to touch. Click **Deploy**.
4. Copy the URL it gives you and open it on the other laptop.

## 4. Next time

Repeat steps 2–3 after any future export. Dropping onto the same Vercel project
creates a new deployment (keeps a history you can roll back to); dropping as a
new project starts fresh. Either is fine — this is meant to be repeatable, not
a one-off.

## Known risk (nothing to do yet, just watch for it)

Vercel enforces a per-file size limit on static uploads (comfortably large,
but a `.pck` can grow as the world/assets do). If a deploy ever fails on file
size, check the `.pck` size in `export/web/` first — that's almost certainly it.
