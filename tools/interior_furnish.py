#!/usr/bin/env python3
"""Deterministic, template-driven procedural furnisher for interior rooms.

Pure Python — no engine, no Pillow, no norfolk-path imports. Given a room type +
size + window columns + a seed + a sprite catalog (name -> (fw, fh, kind)), it
returns a furniture list ``[(name, col, row), ...]`` in DRAW ORDER (underlays
first, then solids, then wall items) that satisfies
``bake_interior.validate_and_stamp`` **by construction**: footprints stay in the
floor region (rows WALL_TOP_ROWS..h-2, cols 1..w-2), never overlap another solid,
and never touch the door pocket. A tall wall anchor may poke a row up into the
hanging band (like the hand-authored fireplace), which the baker also permits.

The ``Placer`` + the seed discipline are the REUSABLE core; ``ROOM_TEMPLATES`` is
the game-specific layer — swap it and the catalog to furnish a different game's
spaces. The design principle is **authored coherence + seeded variation** (rules,
not noise): the same (room_type, size, windows, seed) yields an identical layout
every time. Every draw goes through one ``random.Random(seed)``; every candidate
list is sorted before sampling; nothing reads the wall clock.
"""

import random

WALL_TOP_ROWS = 2  # mirrors bake_interior: the top two rows are the hanging band


class Placer:
    """Occupancy-aware, seeded furniture placer for one room.

    Coordinates match the baker: ``(col, row)`` is a piece's BOTTOM-LEFT cell and
    its footprint spans ``cols [col, col+fw-1] x rows [row-fh+1, row]``.
    """

    def __init__(self, size, windows, catalog, rng):
        self.w, self.h = size
        self.windows = set(windows)
        self.catalog = catalog
        self.rng = rng
        self.door = self.w // 2
        self._occupied = set()  # floor cells taken by solids (rugs never occupy)
        self.underlays = []  # (name, col, row) — rugs; drawn first
        self.solids = []
        self.wall_items = []

    # --- geometry ---------------------------------------------------------
    def foot(self, name):
        fw, fh, _kind = self.catalog[name]
        return fw, fh

    def kind(self, name):
        return self.catalog[name][2]

    def _cells(self, name, col, row):
        fw, fh = self.foot(name)
        return [(c, r) for c in range(col, col + fw) for r in range(row - fh + 1, row + 1)]

    def _is_floor(self, c, r):
        return WALL_TOP_ROWS <= r <= self.h - 2 and 1 <= c <= self.w - 2

    def _is_pocket(self, c, r):
        return (c, r) == (self.door, self.h - 1) or (c, r) == (self.door, self.h - 2)

    def fits(self, name, col, row, band_poke=0):
        """True if a solid/underlay footprint fits: every floor cell free, the top
        may poke up to ``band_poke`` rows into the hanging band, nothing out of
        bounds / on the door pocket / clipping a side or bottom wall."""
        for c, r in self._cells(name, col, row):
            if not (0 <= c < self.w and 0 <= r < self.h):
                return False
            if self._is_pocket(c, r):
                return False
            if self._is_floor(c, r):
                if (c, r) in self._occupied:
                    return False
            elif r < WALL_TOP_ROWS and r >= WALL_TOP_ROWS - band_poke and 1 <= c <= self.w - 2:
                continue  # permitted poke into the top band (drawn over wall)
            else:
                return False
        return True

    def place(self, name, col, row, band_poke=0):
        """Place ``name`` if it fits; return True on success. Wall-kind items never
        collide and are always accepted. Records into the correct draw bucket."""
        if self.kind(name) == "wall":
            self.wall_items.append((name, col, row))
            return True
        if not self.fits(name, col, row, band_poke):
            return False
        if self.kind(name) == "underlay":
            self.underlays.append((name, col, row))  # rugs don't occupy
            return True
        for c, r in self._cells(name, col, row):
            if self._is_floor(c, r):
                self._occupied.add((c, r))
        self.solids.append((name, col, row))
        return True

    def result(self):
        """Furniture in draw order: rugs, then solids, then wall-mounted decor."""
        return self.underlays + self.solids + self.wall_items

    # --- seeded helpers ---------------------------------------------------
    def pick(self, palette):
        """One seeded choice from a palette (a sorted-order list)."""
        return palette[self.rng.randrange(len(palette))]

    def chance(self, p):
        return self.rng.random() < p

    def _zone_cols(self, fw, zone):
        """Leftmost columns where a width-``fw`` piece fits horizontally, filtered
        to a horizontal third (``left``/``center``/``right``/``any``). Sorted."""
        lo, hi = 1, self.w - 1 - fw  # inclusive leftmost range keeping it in bounds
        if hi < lo:
            return []
        third = self.w / 3.0
        bands = {
            "left": (1, third),
            "center": (third, 2 * third),
            "right": (2 * third, self.w),
            "any": (0, self.w),
        }
        blo, bhi = bands.get(zone, bands["any"])
        return [c for c in range(lo, hi + 1) if blo <= c + fw / 2.0 <= bhi] or list(range(lo, hi + 1))

    # --- placement primitives (the reusable vocabulary) -------------------
    def anchor_top(self, palette, zone="any", poke=0):
        """Stand one piece against the top wall inside a horizontal zone. ``poke``
        lets a tall piece (fireplace) reach a row into the band. Seeded column."""
        name = self.pick(palette)
        _fw, fh = self.foot(name)
        row = WALL_TOP_ROWS - poke + fh - 1
        cols = [c for c in self._zone_cols(self.foot(name)[0], zone) if self.fits(name, c, row, poke)]
        if not cols:
            return None
        col = self.pick(cols)
        return (name, col, row) if self.place(name, col, row, poke) else None

    def against_side(self, palette, side, row_zone="mid"):
        """Stand one piece flush against the left or right wall. Seeded row within a
        vertical zone (``top``/``mid``/``low``)."""
        name = self.pick(palette)
        fw, fh = self.foot(name)
        col = 1 if side == "left" else self.w - 1 - fw
        r_lo, r_hi = WALL_TOP_ROWS + fh - 1, self.h - 2
        span = {"top": (r_lo, r_lo + 1), "mid": ((r_lo + r_hi) // 2 - 1, (r_lo + r_hi) // 2 + 1)}
        span["low"] = (r_hi - 1, r_hi)
        z_lo, z_hi = span.get(row_zone, (r_lo, r_hi))
        rows = [r for r in range(max(r_lo, z_lo), min(r_hi, z_hi) + 1) if self.fits(name, col, r)]
        if not rows:
            rows = [r for r in range(r_lo, r_hi + 1) if self.fits(name, col, r)]
        if not rows:
            return None
        row = self.pick(rows)
        return (name, col, row) if self.place(name, col, row) else None

    def rug(self, palette, center=None, base=None):
        """Lay a rug (underlay) on open floor, nudging off any solid it would cover
        (rugs are drawn first, so a bed placed BEFORE this stays on top of nothing —
        the fit check keeps the rug clear of the bed)."""
        name = self.pick(palette)
        rw, _rh = self.foot(name)
        if center is None:
            center = self.w // 2
        if base is None:
            base = self.h - 3
        col = center - rw // 2
        for dr in (0, -1, 1, -2, 2):
            for dc in (0, -1, 1):
                if self.fits(name, col + dc, base + dr):
                    return self.place(name, col + dc, base + dr)
        return False

    def seating_group(self, rug_palette, table, left_chairs, right_chairs, center=None, base=None):
        """A rug with a table on it and a chair flanking each side — the room's
        social centre. Placed as a unit; skipped whole if it can't fit."""
        rug = self.pick(rug_palette)
        rw, rh = self.foot(rug)
        tw, th = self.foot(table)
        if center is None:
            center = self.w // 2
        rc = center - rw // 2
        if base is None:
            base = self.h - 3
        # Try the ideal spot, then nudge up/left a little until the unit fits.
        for dr in (0, -1, 1, -2):
            for dc in (0, -1, 1):
                rcx, brow = rc + dc, base + dr
                tcol = rcx + (rw - tw) // 2
                trow = brow - (rh - th) - 1 if rh > th else brow - 1
                lchair = self.pick(left_chairs)
                rchair = self.pick(right_chairs)
                lc, rcc = rcx - 1, rcx + rw
                if (
                    self.fits(rug, rcx, brow)
                    and self.fits(table, tcol, trow)
                    and self.fits(lchair, lc, trow)
                    and self.fits(rchair, rcc, trow)
                ):
                    self.place(rug, rcx, brow)
                    self.place(table, tcol, trow)
                    self.place(lchair, lc, trow)
                    self.place(rchair, rcc, trow)
                    return True
        return False

    def top_wall_bank(self, shelf, small, feature, feature_palette):
        """Line the top wall with a run of shelves around a central feature (the
        grand clock). Fills left-to-right with a gap reserved for the feature."""
        sw, sh = self.foot(shelf)
        row = WALL_TOP_ROWS + sh - 1
        fname = self.pick(feature_palette)
        fw, fh = self.foot(fname)
        frow = WALL_TOP_ROWS + fh - 1
        fcol = self.door - fw // 2  # centre the feature over the doorway line
        # never let the feature sit on the door pocket columns' reserved cells
        placed_feature = self.fits(fname, fcol, frow) and self.place(fname, fcol, frow)
        c = 1
        while c <= self.w - 2:
            if placed_feature and fcol - 1 <= c <= fcol + fw:
                c = fcol + fw + 1
                continue
            piece = shelf if c + sw - 1 <= self.w - 2 else small
            pw = self.foot(piece)[0]
            prow = WALL_TOP_ROWS + self.foot(piece)[1] - 1
            if c + pw - 1 <= self.w - 2 and self.fits(piece, c, prow):
                self.place(piece, c, prow)
                c += pw
            else:
                c += 1

    def corner_fill(self, palette, corners):
        """Drop a decorative piece into named corners (``tl``/``tr``/``bl``/``br``),
        seeded variant each. Silently skips a corner that's occupied."""
        for corner in corners:
            name = self.pick(palette)
            fw, fh = self.foot(name)
            side = "l" if corner[1] == "l" else "r"
            col = 1 if side == "l" else self.w - 1 - fw
            row = (WALL_TOP_ROWS + fh - 1) if corner[0] == "t" else (self.h - 2)
            if self.fits(name, col, row):
                self.place(name, col, row)

    def scatter(self, palette, count, zone="any"):
        """Seeded filler: drop ``count`` pieces onto free floor cells, sampled from
        a sorted candidate list. Skips a pick that no longer fits."""
        placed = 0
        attempts = 0
        while placed < count and attempts < count * 6:
            attempts += 1
            name = self.pick(palette)
            fw, fh = self.foot(name)
            cands = sorted(
                (c, r)
                for c in range(1, self.w - fw)
                for r in range(WALL_TOP_ROWS + fh - 1, self.h - 1)
                if self.fits(name, c, r)
            )
            if zone == "wall":
                cands = [(c, r) for c, r in cands if c == 1 or c + fw == self.w - 1]
            if not cands:
                continue
            col, row = cands[self.rng.randrange(len(cands))]
            if self.place(name, col, row):
                placed += 1

    def band(self, palette, count):
        """Hang ``count`` wall pieces (clocks) in the top band, off the window
        columns, at seeded columns."""
        free_cols = sorted(c for c in range(2, self.w - 2) if c not in self.windows)
        self.rng.shuffle(free_cols)
        for col in free_cols[:count]:
            self.place(self.pick(palette), col, 1)


# --- room templates: authored coherence, seeded variation --------------------
# Palettes are sorted so a seeded index is stable. Each template composes the
# Placer vocabulary above into a believable room; the RNG only chooses among
# equally-good options (variant, side, filler count/spot), never whether the room
# makes sense.

RUGS = ["rug_green", "rug_teal"]
PLANTS = ["plant_blue", "plant_leafy", "plant_sunflower"]
LAMPS = ["lamp_cream", "lamp_gold", "lamp_teal"]


def _bedroom(p):
    side = p.pick(["left", "right"])
    opp = "right" if side == "left" else "left"
    p.anchor_top(["bed"], zone=side, poke=0)  # bed first so the rug stays clear of it
    p.rug(RUGS, center=p.w // 2, base=p.h - 3)
    p.against_side(LAMPS, opp, "top")  # a floor lamp in the far-top corner
    p.corner_fill(PLANTS + ["crate"], ["bl", "br"])  # both bottom corners
    p.band(["clock_wall"], 1)


def _parlor(p):
    p.seating_group(RUGS, "table_dark", ["chair_right"], ["chair_left"])
    p.anchor_top(["fireplace"], zone=p.pick(["left", "right"]), poke=1)
    p.corner_fill(PLANTS, ["tr", "br"] if p.chance(0.5) else ["tl", "br"])
    p.against_side(LAMPS, "left", "mid")
    p.scatter(PLANTS, p.pick([0, 1]))
    p.band(["clock_wall"], 1)


def _library(p):
    p.top_wall_bank("bookshelf_big", "bookshelf_small", "clock_grand", ["clock_grand"])
    # two reading desks straddling the centre aisle
    quarter = p.w // 4
    left_ok = p.seating_group(RUGS, "table_dark", ["chair_right"], ["chair_left"], center=quarter, base=p.h - 4)
    right_ok = p.seating_group(
        RUGS, "table_dark", ["chair_right"], ["chair_left"], center=p.w - quarter, base=p.h - 4
    )
    if not (left_ok or right_ok):
        p.seating_group(RUGS, "table_dark", ["chair_right"], ["chair_left"])
    p.corner_fill(PLANTS, ["bl", "br"])
    p.against_side(LAMPS, "left", "mid")
    p.band(["clock_wall"], p.pick([0, 1]))


ROOM_TEMPLATES = {
    "bedroom": _bedroom,
    "parlor": _parlor,
    "library": _library,
}


def furnish(room_type, size, windows, seed, catalog):
    """Generate a furniture list for one room. ``catalog`` maps every sprite name
    a template may use to ``(fw, fh, kind)``. Deterministic per (args)."""
    if room_type not in ROOM_TEMPLATES:
        raise SystemExit(
            "interior_furnish: unknown room type %r (have %s)"
            % (room_type, ", ".join(sorted(ROOM_TEMPLATES)))
        )
    rng = random.Random("norfolk-interior:%s" % seed)
    placer = Placer(size, windows, catalog, rng)
    ROOM_TEMPLATES[room_type](placer)
    return placer.result()
