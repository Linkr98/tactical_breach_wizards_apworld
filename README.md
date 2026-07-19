# Tactical Breach Wizards Multiworld Setup Guide

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

## Installing the apworld

1. Download `tactical_breach_wizards.apworld`.
2. Double-click it (it associates with the Archipelago Launcher), **or** copy it into
   your Archipelago install's `custom_worlds/` folder.

## Creating a config (.yaml)

In the Archipelago Launcher, generate a template yaml ("Generate Template Options")
and edit the **Tactical Breach Wizards** section. Options:

- `completion_perk_percent` — from Act 2 on, completing a mission requires your best wizard
  to have this percent of its recommended per-slot perks (default 25; 0 disables).
- `goal_perk_percent` — same idea for confidence goals, also from Act 2 on, defaulting higher
  (default 50; 0 disables). A wizard's perk power counts their perk points + their dream
  ability, and one strong wizard can be fielded in multiple slots, so these check your
  strongest unlocked wizard — keeping you from being underpowered for a late mission.
- `confidence_per_boost` — how much confidence each "Confidence Boost" item grants
  (default 5). Confidence is earned only from these items and is spent at the outfit shop.
- `death_link` — optional; off by default. When anyone in the multiworld dies, one of
  your wizards gets a lethal condition they must out-run by finishing the room's
  objectives that turn — and your deaths are shared the same way.

## What is randomized

- **Items found in the multiworld:** the five wizards, access to each campaign mission,
  14 abilities (each wizard's base kit plus the four special dream abilities), perk
  points, and per-character Confidence Boosts (the only way to earn confidence to spend
  at the shop). Cosmetic outfits are not items — buying one at the shop is itself a
  check, and the purchase gives you the outfit as normal.
- **Checks (locations):** completing each mission, reaching each mission's halfway
  point, each in-mission confidence goal, buying each outfit in the shop, unlocking each
  dream ability, and recruiting each wizard — 238 in all.

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

Claude was used in the making of most of both the mod and the AP world but I have been testing and tweaking logic myself.

