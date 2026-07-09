# Tactical Breach Wizards — Archipelago apworld

The **generation/server side** of the Tactical Breach Wizards Archipelago integration.
The matching in-game client is the BepInEx + Harmony C# mod in the game's plugins folder
(`...\Tactical Breach Wizards\BepInEx\plugins\Tactical Breach Wizards Archipelago Mod\`
— start with its `README.md`). The two halves agree on the frozen item/location id
contract in `../tactical_breach_wizards/ap_data.json`.

## Layout (inside `C:\ProgramData\Archipelago\custom_worlds\`)

```
custom_worlds/
  tactical_breach_wizards.apworld <- the INSTALLED world (a zip of the source below).
                                     This is what Archipelago loads. Never edit it;
                                     rebuild it with build_apworld.py after source edits.
  _tactical_breach_wizards_apworld/             <- this folder. The "_" prefix hides it from Archipelago
                                   (this frozen AP build can only load .apworld zips,
                                   not unpacked folders — verified the hard way).
    tactical_breach_wizards/    <- the world SOURCE you edit
      __init__.py               <- World subclass, item/region/rule wiring, slot_data
      data.py                   <- loads ap_data.json; name<->id maps; logic helpers
      options.py                <- yaml options (confidence_per_boost, completion_perk_percent,
                                   goal_perk_percent, death_link)
      rules.py                  <- access logic (act gate, character/ability/goal/outfit rules)
      ap_data.json              <- FROZEN id contract + logic metadata (generated - do not hand-edit)
      docs/setup_en.md          <- player setup guide (shown on the AP website)
    archipelago.json            <- apworld manifest (packed at the archive root when building)
    build_apworld.py            <- zips the source AND installs it into custom_worlds/
    test_world.py               <- standalone sanity checks (no AP install required)
    README.md                   <- you are here
```

## What it does

- **Items shuffled:** 5 wizards, 29 mission-access unlocks, **14 abilities** (4 PerkUnlock
  "dream" specials + 10 base-kit abilities — base abilities are `useful` until a requirement
  references them), perk points (perk-tree upgrades, progression: Zan 7 / Jen 5 / Banks 5 /
  Dall 5 / Rion 4 = 26), 5 per-character **Confidence Boost**
  items (the only confidence source — see economy below), and generic **Donut** filler.
  **82 item codes** (the 23 outfit item ids exist in the contract but are intentionally
  never placed — buying an outfit at the shop is the check and already grants the
  cosmetic; their pool slots become Donuts).
- **Locations (checks):** 29 mission completions, **23 mission halfway checkpoints**
  (fires partway through every multi-room mission — easy early checks), 154 in-mission
  confidence goals, 23 outfit purchases, **4 ability unlocks** (the dream-perk rewards),
  5 recruitments = **238 total**.

### Confidence economy

The mod blocks natural confidence earning, so confidence comes only from `Confidence Boost:
<Char>` items (each worth `confidence_per_boost`, default 5). Outfit purchases are checks
gated by a per-character **staircase**: the i-th costliest outfit needs total confidence ≥
the cumulative cost. Enough boosts are always placed for each wizard to clear their whole
wardrobe, so the shop stays fully reachable. This makes Confidence Boosts **progression**.

- **Start:** one random wizard (precollected with their full base kit and 1 perk point),
  plus one random valid early mission (see `data.is_valid_opener`).
- **Goal:** complete "Counterheist: The Roof".

### Logic model

Loose ordering, not a strict chain. Later acts are gated behind accumulated power
(number of recruited characters): act 0 free, act 1 needs ≥2 characters, act 2 ≥3,
act 3 (finale) all 5. Mission regions also enforce per-mission character requirements —
**including the mission's own recruit** if listed (no recruit exemption: controlling a
wizard always means having unlocked them first, even the one that mission would normally
hand you). Each **anxiety dream** requires the wizard it's about (e.g. Banks's "Death's
Door" needs Banks). Missions, halfway checkpoints, and goals can also require specific
**abilities** and extra **heroes** — fill these in as you find them (`FIRM_REQUIRED*`,
`HALF_REQUIRED*`, `GOAL_REQUIREMENTS` in the mod repo's `tools/generate_ap_data.py`;
see `HOWTO-add-mission-requirements.md` there). See `rules.py` /
`data.effective_required_characters` for the full model.

**Halfway checkpoints** are requirement-free by default (just reach the mission), which
is what makes them good early checks; the full completion automatically inherits any
half requirements you add.

**Perk-power gating.** A wizard's perk power = their perk-tree points (always shuffled in
as progression) + 1 if their dream ability is unlocked (max: Zan 7, Jen/Banks/Dall 6,
Rion 5; Zan has no dream perk since SeerFinale was removed). Because a wizard can be
fielded in **multiple slots**, the binding constraint is your *best* unlocked wizard, not
the team total. So the gate is **per-slot**: each mission has a recommended per-slot value
(the strongest single wizard the game expects there, from the `PerkProgress` dev
snapshots). A mission's **completion** (from Act 3 on) needs your best unlocked wizard ≥
`completion_perk_percent`% of it; its **confidence goals** (from Act 2 on) need ≥
`goal_perk_percent`%. Act 1 stays ungated.

## Day-to-day development

1. Edit the source in `tactical_breach_wizards/` (usually `rules.py`, or — for
   requirement/data changes — regenerate from the mod repo's
   `tools/generate_ap_data.py`, which auto-copies `ap_data.json` here).
2. `python test_world.py` — fast sanity checks: id/name uniqueness, frozen counts,
   pool math for every possible starting hero, and a max-reachability sweep proving no
   location can be permanently locked.
3. `python build_apworld.py` — rebuilds `../tactical_breach_wizards.apworld`, i.e.
   **installs** your edits. Forgetting this step = Archipelago silently keeps using the
   old version (historically the #1 source of "my change didn't take" bugs).
4. Generate for real: put a yaml in Archipelago's `Players/` folder (options described
   in `tactical_breach_wizards/docs/setup_en.md`, or use the Launcher's "Generate
   Template Options") and run `ArchipelagoGenerate`.

## Sharing with other players

Send them the same `custom_worlds/tactical_breach_wizards.apworld` the build step
produced; they double-click it (Archipelago Launcher installs it) or drop it in their
own `custom_worlds/`.

## Updating the id contract

`ap_data.json` is **frozen** — never renumber or remove existing ids (generated seeds
depend on id stability), and never hand-edit it. It is regenerated append-only in the mod
repo (`tools/generate_ap_data.py`), which auto-copies the result here. After updating it,
re-run `test_world.py` (it asserts the 82/238 counts — update those asserts when you
intentionally append content).
