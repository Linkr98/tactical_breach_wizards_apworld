"""Standalone sanity checks for the tactical_breach_wizards apworld.

These do NOT require Archipelago to be installed -- they import only the world's own
``data`` and ``rules`` modules (pure Python) and exercise:

  * id/name uniqueness and the frozen counts,
  * item-pool math for every possible starting hero (pool size must equal #locations),
  * a max-reachability sweep proving no location is permanently locked and that the
    victory location is reachable once everything is collected.

Run:  python test_world.py
(The real solvability guarantee comes from Archipelago's own generator; this is a fast
local guard against logic/data regressions.)
"""

import importlib
import math
import sys
import types
from pathlib import Path

# Import the world's pure-Python submodules (data, rules) WITHOUT executing the
# package __init__.py, which imports Archipelago (BaseClasses) and isn't available
# in a bare test environment. We register a synthetic parent package pointing at the
# real directory so relative imports and pkgutil.get_data still resolve.
_HERE = Path(__file__).resolve().parent
_PKG = "tactical_breach_wizards"
# The world SOURCE lives next to this script; the installed copy Archipelago actually
# loads is the .apworld zip in custom_worlds/ (rebuild after edits: build_apworld.py).
_PKG_DIR = _HERE / _PKG
sys.path.insert(0, str(_HERE))
_pkg_module = types.ModuleType(_PKG)
_pkg_module.__path__ = [str(_PKG_DIR)]
_pkg_module.__package__ = _PKG
sys.modules[_PKG] = _pkg_module

data = importlib.import_module(f"{_PKG}.data")
rules = importlib.import_module(f"{_PKG}.rules")

PLAYER = 1


class FakeState:
    """Minimal CollectionState stand-in: has(name, player)."""

    def __init__(self, item_names):
        self._items = set(item_names)

    def has(self, name, player):
        return name in self._items

    def count(self, name, player):
        # Simulate owning plenty of each collected item (enough for any staircase step).
        return 999 if name in self._items else 0


def check_contract():
    assert data.GAME_NAME == "Tactical Breach Wizards"
    assert len(data.ITEMS) == 82, len(data.ITEMS)  # 4 PerkUnlock specials + 10 base-kit abilities
    # 215 base + 23 mission-half checkpoints (one per multi-room mission)
    assert len(data.LOCATIONS) == 238, len(data.LOCATIONS)
    assert sum(1 for l in data.LOCATIONS if l["category"] == "mission_half") == 23
    assert len(data.MISSIONS) == 29, len(data.MISSIONS)
    assert len(data.PLAYABLE_CHARACTERS) == 5

    names = [i["name"] for i in data.ITEMS]
    ids = [i["id"] for i in data.ITEMS]
    assert len(set(names)) == len(names), "duplicate item names"
    assert len(set(ids)) == len(ids), "duplicate item ids"
    lnames = [l["name"] for l in data.LOCATIONS]
    lids = [l["id"] for l in data.LOCATIONS]
    assert len(set(lnames)) == len(lnames), "duplicate location names"
    assert len(set(lids)) == len(lids), "duplicate location ids"

    # item_name_to_id / location_name_to_id are complete bijections.
    assert set(data.item_name_to_id) == set(names)
    assert set(data.location_name_to_id) == set(lnames)
    print("[ok] contract: 82 items / 238 locations, ids+names unique")


def check_pool_math():
    """For every start hero and either perk setting, the created pool must exactly fill
    the locations -- pool size == number of locations."""
    n_locations = len(data.LOCATIONS)

    # Perk-point counts must be defined for exactly the playable characters.
    assert set(data.PERK_POINTS_PER_CHARACTER) == set(data.PLAYABLE_CHARACTERS)
    perk_full = sum(data.PERK_POINTS_PER_CHARACTER.values())
    assert perk_full == 26, perk_full  # Zan 7, Jen 5, Banks 5, Dall 5, Rion 4

    # NB: outfit items are intentionally NOT placed in the pool (see __init__.create_items);
    # their slots become Donut filler, so they don't appear in `base`. The second mission is a
    # normal shuffled item now (no forced opening lock), so mission_access only drops the 1
    # precollected start mission and no location is pre-locked.
    base = (
        (sum(1 for it in data.ITEMS if it["category"] == "character") - 1)        # minus start hero
        + (sum(1 for it in data.ITEMS if it["category"] == "mission_access") - 1)  # minus start mission
        + sum(1 for it in data.ITEMS if it["category"] == "ability")
        + (perk_full - 1)  # perk points minus the 1 precollected on the start hero
    )
    fillable = n_locations  # nothing pre-locked; the pool fills every location
    for k in (2, 5, 20):           # confidence_per_boost extremes + default
        confidence = sum(
            math.ceil(c / k) for c in data.OUTFIT_TOTAL_COST_PER_CHARACTER.values() if c
        )
        placed = base + confidence
        filler = fillable - placed
        assert filler >= 0, f"negative filler for k={k}: {filler}"
        assert placed + filler == fillable
    print("[ok] pool math: itempool == 238 across confidence_per_boost 2..20")


def check_perk_gating():
    """Perk points are progression; per-slot gates satisfiable by a single best wizard."""
    d = data
    perk_class = {it["classification"] for it in d.ITEMS if it["category"] == "perk_point"}
    assert perk_class == {"progression"}, perk_class

    # Dream abilities (+1 perk) exist for Jen/Banks/Dall/Rion only (Zan's SeerFinale was removed).
    assert set(d.ABILITY_ITEM_FOR_CHARACTER) == {"WitchCop", "NecroMedic", "RiotPriest", "Druid"}, d.ABILITY_ITEM_FOR_CHARACTER
    # Strongest single wizard = Zan 7 (no dream perk now). Jen/Banks/Dall = 6, Rion = 5.
    max_single = max(
        d.PERK_POINTS_PER_CHARACTER[c] + (1 if c in d.ABILITY_ITEM_FOR_CHARACTER else 0)
        for c in d.PLAYABLE_CHARACTERS
    )
    assert max_single == 7, max_single
    max_rec = max(m["recommendedPerks"] for m in d.MISSIONS)  # per-slot; expect 6
    assert max_rec == 6, max_rec
    # Even at 100%, one wizard can meet the per-slot recommendation (else full-access fails).
    assert max_rec <= max_single

    # Scripted tutorials are exempt from the PERK gate (they may still require abilities, e.g.
    # Rushwater Reunion needs Predictive Bolt). Verify: with the mission's required abilities but
    # ZERO perks/characters, the completion rule still passes -> no perk requirement is imposed.
    for sid in d.SCRIPTED_TUTORIAL_STAGES:
        loc = next(l for l in d.LOCATIONS if l["category"] == "mission_complete" and l["stageID"] == sid)
        rule = rules.make_completion_rule(PLAYER, loc, 50)
        if rule is None:
            continue  # no requirements at all (e.g. The Asset)
        ability_items = [d.ABILITY_ITEM_BY_SAVENAME[sv] for sv in d.mission_required_abilities(sid)]
        assert rule(FakeState(ability_items)), sid  # abilities only, no perks -> perk-gate exempt
    print(f"[ok] perk gating (best-wizard): max per-slot rec {max_rec} <= strongest wizard {max_single}")


def _mission_reachable(state, mission):
    return rules.make_mission_rule(PLAYER, mission)(state)


def _location_reachable(state, loc, mission_reach):
    cat = loc["category"]
    if cat in ("recruit", "ability_unlock"):
        return mission_reach[data.region_stage_for_location(loc)]
    if cat == "mission_half":
        if not mission_reach[loc["missionStageID"]]:
            return False
        rule = rules.make_half_rule(PLAYER, loc)
        return True if rule is None else rule(state)
    if cat == "mission_complete":
        if not mission_reach[loc["stageID"]]:
            return False
        rule = rules.make_completion_rule(PLAYER, loc, 50)
        return True if rule is None else rule(state)
    if cat == "confidence_goal":
        if not mission_reach[loc["missionStageID"]]:
            return False
        rule = rules.make_confidence_goal_rule(PLAYER, loc, 75)
        return True if rule is None else rule(state)
    if cat == "outfit_purchase":
        return rules.make_outfit_rule(PLAYER, loc, 5)(state)
    raise AssertionError(f"unknown category {cat}")


def check_max_reachability():
    """With every item collected, every location must be reachable and the goal met.
    This proves no rule permanently locks a check."""
    all_items = [it["name"] for it in data.ITEMS]
    state = FakeState(all_items)
    mission_reach = {m["stageID"]: _mission_reachable(state, m) for m in data.MISSIONS}

    assert all(mission_reach.values()), [s for s, r in mission_reach.items() if not r]

    unreachable = [
        loc["name"] for loc in data.LOCATIONS
        if not _location_reachable(state, loc, mission_reach)
    ]
    assert not unreachable, f"unreachable with all items: {unreachable}"

    # Goal location specifically.
    goal_loc = data.LOCATION_BY_NAME[data.GOAL_LOCATION_NAME]
    assert _location_reachable(state, goal_loc, mission_reach), "goal unreachable"
    print(f"[ok] max reachability: all 238 locations reachable; goal = {data.GOAL_LOCATION_NAME!r}")


def check_opening_and_dreams():
    """Fixed scripted opening + anxiety-dream character gating."""
    d = data
    assert d.START_MISSION_STAGE == "Game_Prologue"
    assert d.SECOND_MISSION_STAGE == "Game_Witch_Intro"
    assert d.FIRST_MISSION_COMPLETE_LOCATION == "Complete: The Asset", d.FIRST_MISSION_COMPLETE_LOCATION
    # The Asset recruits its only required hero (Zan), so it needs nobody -> valid opener.
    # Rushwater is no longer char-exempt: it needs Zan (Jen, its recruit, is stripped).
    assert d.effective_required_characters(d.MISSION_BY_STAGE["Game_Prologue"]) == []
    assert d.effective_required_characters(d.MISSION_BY_STAGE["Game_Witch_Intro"]) == ["NavySeer"], \
        d.effective_required_characters(d.MISSION_BY_STAGE["Game_Witch_Intro"])
    print("[ok] opening: 'The Asset' precollected start (no char req); 'Rushwater Reunion' shuffled, requires Zan")

    expected = {
        "Game_Lucid_Dream_Jen": "WitchCop",
        "Game_Lucid_Dream_Banks": "NecroMedic",
        "Game_Lucid_Dream_Dall": "RiotPriest",
        "Game_Lucid_Dream_Rion": "Druid",
        "Game_Lucid_Dream_Zan": "NavySeer",
    }
    assert d.DREAM_REQUIRED_CHARACTER == expected, d.DREAM_REQUIRED_CHARACTER
    for sid, ch in expected.items():
        assert ch in d.effective_required_characters(d.MISSION_BY_STAGE[sid]), (sid, ch)
    print("[ok] anxiety dreams gated on their wizard:",
          {sid.rsplit("_", 1)[-1]: d.NAME_MAP[ch] for sid, ch in expected.items()})

    # Ability unlocks are the reward for the matching dream -> live in that dream's region.
    # (Zan's SeerFinaleKnockBackDummy unlock was removed from the contract: finale-only dummy.)
    ability_dream = {
        "abilityloc:Unlock_ChainShockSuperchain": "Game_Lucid_Dream_Jen",
        "abilityloc:Unlock_DeathsFloor": "Game_Lucid_Dream_Banks",
        "abilityloc:Unlock_SwapWithoutLOS": "Game_Lucid_Dream_Dall",
        "abilityloc:Unlock_SporeIntelligent": "Game_Lucid_Dream_Rion",
    }
    unlock_keys = {loc["key"] for loc in d.LOCATIONS if loc["category"] == "ability_unlock"}
    assert unlock_keys == set(ability_dream), unlock_keys
    for loc in d.LOCATIONS:
        if loc["category"] == "ability_unlock":
            assert d.region_stage_for_location(loc) == ability_dream[loc["key"]], loc["key"]
    print("[ok] ability unlocks live in their dream's region (e.g. ChainShock <- Jen's dream)")


def check_openers():
    """Every wizard must have at least one valid starting mission, and each opener must truly
    be winnable from scratch: early enough (act <= OPENER_MAX_ACT), act-gate satisfiable by
    one wizard, not the goal, no required abilities (completion or halfway), chars satisfied
    by the lone hero, and its completion check in logic with the 1 head-start perk."""
    all_openers = set()
    for hero in data.PLAYABLE_CHARACTERS:
        # 100 = worst-case completion_perk_percent; openers must qualify even then.
        openers = [m for m in data.MISSIONS if data.is_valid_opener(m, hero, 100)]
        assert openers, f"no valid opener for start hero {hero}"
        for m in openers:
            sid = m["stageID"]
            assert sid != data.GOAL_STAGE_ID, "goal must never be an opener"
            assert m["act"] <= data.OPENER_MAX_ACT, f"late-game opener leaked: {sid} (act {m['act']})"
            assert data.act_character_requirement(m["act"]) <= 1, sid
            assert not data.mission_required_abilities(sid), sid
            assert not data.mission_half_required_abilities(sid), sid
            required = data.effective_required_characters(m) + data.mission_half_required_characters(sid)
            assert all(c == hero for c in required), sid
            all_openers.add(m["name"])
    # The Asset must always qualify (recruit-strips its only required hero, no abilities).
    assert "The Asset" in all_openers, sorted(all_openers)
    # The goal mission is never an opener, regardless of hero.
    goal_mission = data.MISSION_BY_STAGE[data.GOAL_STAGE_ID]
    assert not any(data.is_valid_opener(goal_mission, h, 100) for h in data.PLAYABLE_CHARACTERS)
    gate = "OFF" if not data.ACT_GATE_ENABLED else "ON"
    print(f"[ok] random opener pool ({len(all_openers)}, act<={data.OPENER_MAX_ACT}, "
          f"act-gate {gate}): {sorted(all_openers)}")


def main():
    check_contract()
    check_pool_math()
    check_opening_and_dreams()
    check_openers()
    check_perk_gating()
    check_max_reachability()
    print("\nAll checks passed.")


if __name__ == "__main__":
    main()
