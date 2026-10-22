# Tactical Breach Wizards Multiworld Setup Guide

**Version 0.2.0** — tested on Archipelago 0.6.8. Use with the matching 0.2.0 release of
the [game mod](https://github.com/Linkr98/Tactical-Breach-Wizards-Archipelago-Mod).

> **This project is no longer actively maintained.** It's shared as-is; issues may not
> get answered. Forks and continuations are welcome.

## Beta

Logic is currently work in progress. There is a chance that there are unreachable locations in logic and because of that it is possible to get an impossible seed. Using /send_location or 'Skip Level' may be require if you soft lock.

Defaults for `completion_perk_percent`and `goal_perk_percent` have not been fully balanced setting them to high or to low may result generation failures or impossible seeds.

If you have a better filler item name then Donut please let me know.

## Required Software

- A copy of **Tactical Breach Wizards** on PC.
- The [**Tactical Breach Wizards Archipelago client mod**](https://github.com/Linkr98/Tactical-Breach-Wizards-Archipelago-Mod) (BepInEx + Harmony plugin),
  installed into the game's `BepInEx/plugins` folder.
- The `tactical_breach_wizards.apworld` file (this world), installed into your
  Archipelago installation.

## Recommended: Universal Tracker

**Play with [Universal Tracker](https://github.com/FarisTheAncient/Archipelago/releases)
(UT).** The game itself gives you no way to tell which checks are currently in logic. UT reads this world's rules and shows you, live, which of your locations are reachable with the items you have. Its useful if you want to tell if you should keep trying for a level confidence goal or come back when you have more perks, also just seeing when things in already unlocked mission come into logic.

1. Download `tracker.apworld` from the UT releases page and install it the same way as
   this apworld (double-click, or drop it into `custom_worlds/`).
2. Open **Universal Tracker** from the Archipelago Launcher and connect with the same
   address and slot name as the game. The **Tracker** tab lists your in-logic checks.

You do **not** need your yaml for this: the world sends everything UT needs (your options
and your random starting wizard/mission) in the slot data, so tracking also works for
seeds someone else generated.

## Installing the apworld

1. Download `tactical_breach_wizards.apworld`.
2. Double-click it (it associates with the Archipelago Launcher), **or** copy it into
   your Archipelago install's `custom_worlds/` folder.

## Creating a config (.yaml)

In the Archipelago Launcher, generate a template yaml ("Generate Template Options")
and edit the **Tactical Breach Wizards** section. Options:

- `completion_perk_percent` — completing a mission (or reaching its halfway checkpoint)
  requires this percent of its recommended per-slot perks (default 50, range 25–100).
- `goal_perk_percent` — same idea for confidence goals (default 60, range 25–100); keep it
  at or above `completion_perk_percent`. A wizard's perk power counts their perk points + their dream ability, and one strong wizard can be fielded
  in multiple slots, so these check your strongest unlocked wizard — except in anxiety
  dreams, whose squad is scripted: there the gate checks the dream's own cast.
- `starting_hero` — which wizard you start with: `zan`, `jen`, `banks`, `dall`, `rion`,
  or `random` (the default) to let the seed pick.
- `confidence_boosts_per_wizard` — how many "Confidence Boost" items it takes to clear a
  wizard's whole wardrobe (default 10). Each boost's value scales with that wizard's total
  wardrobe cost, so every wizard needs the same number of boosts. Confidence is earned only
  from these items and is spent at the outfit shop.
- `extra_confidence_boosts` — spare boosts per wizard on top of that (default 2). Not
  required by logic; they give slack so one missing boost doesn't hold everything up.
- `death_link` — optional; off by default. When anyone in the multiworld dies, one of
  your wizards gets a lethal condition they must out-run by finishing the room's
  objectives that turn — and your deaths are shared the same way.
- `shuffle_base_abilities` — off by default: every wizard has their full base kit as soon
  as you unlock them, and only the four anxiety-dream ability upgrades are shuffled. Turn on
  to shuffle the base abilities (Predictive Bolt, Broom Breach, Spectral Skull, ...) into the
  multiworld too — a new wizard may be missing part of their kit until you find it.
- `armoury_caches_goal` — off by default: Dall's "Destroy the Caches" goal in The B Team's
  Armoury room is far harder than any other goal, so it isn't a check unless you turn this on.

## What is randomized

- **Items found in the multiworld:** the five wizards, access to each campaign mission,
  the four special dream abilities (plus each wizard's base kit if `shuffle_base_abilities`
  is on), perk points, and per-character Confidence Boosts (the only way to earn confidence to spend
  at the shop). Cosmetic outfits are not items — buying one at the shop is itself a
  check, and the purchase gives you the outfit as normal.
- **Checks (locations):** completing each mission, reaching each mission's halfway
  point, each in-mission confidence goal, buying each outfit in the shop, unlocking each
  dream ability, and recruiting each wizard — 238 in all (237 with the Armoury caches goal
  left out, the default).

You start with **one random wizard** (with their full base kit and one perk point) and
**one random early mission**. Everything else is reached through the mod's mission
board: later acts open up as you recruit more wizards, and each anxiety dream requires
the wizard it's about.

## Goal

Complete the campaign finale, **"Counterheist: The Roof"**.

## Joining a game

1. Launch the game with the mod installed.
2. The connect dialog appears when you start a new save. Always create the new save using the switch save menu. If you see a world map then you have not connected to the archipelago.
   - enter the server address, your slot name, and password if any.
3. Play. Completed checks are sent automatically; received items unlock in-game.

## Notes

- This will not save a save game to your saves list
- Upon getting the halfway or mission completion check for every level you will be able to do level select for relacent levels
- Pressing START without selecting your characters will use the defaults which you may not have unlock so just use Esc->Restart Level
- Incoming Deathlinks are granted on the start of your next turn
- Outgoing Deathlinks are sent if one of your wizards is dead when you press End Turn that was alive during your turn.

## AI Disclosure

All of the code in this project was generated by AI (Claude). The ideas, design
decisions, and all testing were done by me — I decided what the randomizer should do,
directed the implementation, played, and tested it.

