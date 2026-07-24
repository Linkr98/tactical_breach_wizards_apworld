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
        + len(data.ABILITY_ITEM_NAMES)  # live abilities only -- retired ones are never placed
        + (perk_full - 1)  # perk points minus the 1 precollected on the start hero
    )
    fillable = n_locations  # nothing pre-locked; the pool fills every location
    chars_with_wardrobe = sum(1 for c in data.OUTFIT_TOTAL_COST_PER_CHARACTER.values() if c)
    for k in (2, 5, 20):           # confidence_per_boost extremes + default
        confidence = sum(
            math.ceil(c / k) for c in data.OUTFIT_TOTAL_COST_PER_CHARACTER.values() if c
        )
        for extra in (0, 2, 10):   # extra_confidence_boosts extremes + default (per wizard)
            placed = base + confidence + extra * chars_with_wardrobe
            filler = fillable - placed
            assert filler >= 0, f"negative filler for k={k}, extra={extra}: {filler}"
            assert placed + filler == fillable
    print("[ok] pool math: itempool == 238 across confidence_per_boost 2..20 x extras 0..10")


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

    # Scripted tutorials are exempt from the PERK gate (they may still require abilities and
    # characters, e.g. Rushwater Reunion needs Predictive Bolt + Jen/Zan via HALF_REQUIRED).
    # Verify: with the mission's required abilities and characters but ZERO perks, the
    # completion rule still passes -> no perk requirement is imposed.
    for sid in d.SCRIPTED_TUTORIAL_STAGES:
        loc = next(l for l in d.LOCATIONS if l["category"] == "mission_complete" and l["stageID"] == sid)
        rule = rules.make_completion_rule(PLAYER, loc, 50)
        if rule is None:
            continue  # no requirements at all
        items = [d.ABILITY_ITEM_BY_SAVENAME[sv] for sv in
                 d.mission_required_abilities(sid) + d.mission_half_required_abilities(sid)]
        items += [d.CHARACTER_ITEM_NAME[c] for c in d.mission_half_required_characters(sid)]
        assert rule(FakeState(items)), sid  # abilities+chars only, no perks -> perk-gate exempt
    print(f"[ok] perk gating (best-wizard): max per-slot rec {max_rec} <= strongest wizard {max_single}")


def check_team_ability_gate():
    """Goals with requiredTotalAbilities (e.g. 'use 9 abilities in one turn') gate on the
    team-wide ability count: the room's squadSize best unlocked wizards x (4 - missing
    BASE-KIT items; dream specials are upgrades and don't count)."""
    d = data
    gated = [l for l in d.LOCATIONS
             if l["category"] == "confidence_goal" and l.get("requiredTotalAbilities")]
    assert gated, "expected team-ability gated goals (AbilitiesInOneTurnGoal)"
    # Every gated goal must be satisfiable within ITS OWN room's wizard count.
    for l in gated:
        squad = l.get("squadSize") or rules.DEFAULT_SQUAD_SIZE
        assert l["requiredTotalAbilities"] <= squad * rules.ABILITIES_PER_WIZARD, \
            (l["name"], l["requiredTotalAbilities"], squad)

    # The gate may need ANY live ability item -> every one must be progression for the fill.
    # Retired items (never placed, e.g. the legacy base-kit Death's Floor copy) are exempt.
    ability_cls = {it["classification"] for it in d.ITEMS
                   if it["category"] == "ability" and not it.get("retired")}
    assert ability_cls == {"progression"}, ability_cls

    # Room-size cap: a 3-wizard room fields at most 12 even with everything collected.
    all_items = [it["name"] for it in d.ITEMS]
    assert rules.team_ability_count(FakeState(all_items), PLAYER, 3) == 12
    assert rules.team_ability_count(FakeState(all_items), PLAYER, 5) == 20

    # Dream specials don't count (all four, incl. Death's Floor -- a pure dream reward,
    # NOT part of Banks's base kit): dropping every dream ability item changes nothing.
    no_dreams = [n for n in all_items if n not in set(d.ABILITY_ITEM_FOR_CHARACTER.values())]
    assert rules.team_ability_count(FakeState(no_dreams), PLAYER, 5) == 20

    # Hardest gate (Fort Osprey 16, a 5-wizard room): passes with everything, fails once
    # five base-kit items are missing (room total 20 - 5 = 15 < 16).
    max_need = max(l["requiredTotalAbilities"] for l in gated)
    hardest = next(l for l in gated if l["requiredTotalAbilities"] == max_need)
    rule = rules.make_confidence_goal_rule(PLAYER, hardest, 0)  # percent 0 -> pure ability gate
    assert rule(FakeState(all_items)), "team-ability gate unreachable with all items"
    base_items = [it for ch in d.PLAYABLE_CHARACTERS
                  for it in d.BASE_ABILITY_ITEMS_BY_CHARACTER.get(ch, [])]
    assert not rule(FakeState([n for n in all_items if n not in set(base_items[:5])])), \
        "gate passed despite 5 missing base-kit abilities"
    print(f"[ok] team-ability gate: {len(gated)} goals, max need {max_need} "
          f"(squad {hardest.get('squadSize')}), dream specials excluded")


def check_any_of_gate():
    """OR-gated requirements (FIRM_REQUIRED_ANY): The Recording's gap needs Dall, OR
    Banks + Death's Floor, OR Jen + Broom Breach."""
    d = data
    sid = "Game_The_Recording"
    groups = d.mission_required_any(sid)
    assert len(groups) == 1 and len(groups[0]) == 3, groups
    loc = next(l for l in d.LOCATIONS if l["category"] == "mission_complete" and l["stageID"] == sid)
    rule = rules.make_completion_rule(PLAYER, loc, 0)  # percent 0 -> pure OR-gate, no perk need
    assert rule is not None

    dall = d.CHARACTER_ITEM_NAME["RiotPriest"]
    banks = d.CHARACTER_ITEM_NAME["NecroMedic"]
    jen = d.CHARACTER_ITEM_NAME["WitchCop"]
    floor = d.ABILITY_ITEM_BY_SAVENAME["Unlock_DeathsFloor"]
    broom = d.ABILITY_ITEM_BY_SAVENAME["UnlockBroomBreach"]

    assert not rule(FakeState([]))                       # nothing -> no way across
    assert rule(FakeState([dall]))                       # Dall alone suffices
    assert not rule(FakeState([banks]))                  # Banks without Death's Floor: no
    assert rule(FakeState([banks, floor]))               # Banks + Death's Floor
    assert not rule(FakeState([jen]))                    # Jen without Broom Breach: no
    assert rule(FakeState([jen, broom]))                 # Jen + Broom Breach
    assert not rule(FakeState([floor, broom]))           # abilities without their wizard: no
    # Anyone else entirely -- e.g. Zan + Rion with full kits -- still can't cross.
    others = [d.CHARACTER_ITEM_NAME["NavySeer"], d.CHARACTER_ITEM_NAME["Druid"]]
    others += d.BASE_ABILITY_ITEMS_BY_CHARACTER["NavySeer"] + d.BASE_ABILITY_ITEMS_BY_CHARACTER["Druid"]
    assert not rule(FakeState(others))
    print("[ok] OR-gate: The Recording needs Dall | Banks+Death's Floor | Jen+Broom Breach")


def check_retired_items():
    """Retired items (merged duplicates) keep their frozen id but are invisible to logic:
    the base-kit Death's Floor copy stays defined for old seeds, while the dream item is
    THE Death's Floor -- friendly name, Banks's kit, one item players ever see."""
    d = data
    retired = [it for it in d.ITEMS if it.get("retired")]
    assert [it["key"] for it in retired] == ["ability:UnlockDeathsFloor"], retired
    it = retired[0]
    assert it["id"] == 271829312, it  # frozen id -- old seeds may still send it
    # Excluded from every live lookup: pool names, savename map, victory capstone, base kits.
    assert it["name"] not in d.ABILITY_ITEM_NAMES
    assert "UnlockDeathsFloor" not in d.ABILITY_ITEM_BY_SAVENAME
    assert it["name"] not in d.GOAL_REQUIRED_ITEM_NAMES
    assert all(it["name"] not in items for items in d.BASE_ABILITY_ITEMS_BY_CHARACTER.values())
    # The dream item took over the friendly name and the victory capstone, but stays a pure
    # dream reward: NOT in Banks's base kit (her kit is Spectral Skull + Transference).
    live = d.ABILITY_ITEM_BY_SAVENAME["Unlock_DeathsFloor"]
    assert live == "Ability: Death's Floor (Banks)", live
    assert live not in d.BASE_ABILITY_ITEMS_BY_CHARACTER["NecroMedic"]
    assert len(d.BASE_ABILITY_ITEMS_BY_CHARACTER["NecroMedic"]) == 2
    assert live == d.ABILITY_ITEM_FOR_CHARACTER["NecroMedic"]  # her dream reward (+1 perk)
    assert live in d.GOAL_REQUIRED_ITEM_NAMES
    assert len(d.ABILITY_ITEM_NAMES) == 13, len(d.ABILITY_ITEM_NAMES)  # 14 defined - 1 retired
    print("[ok] retired items: legacy Death's Floor defined-but-unplaced; dream item is THE item")


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
    # NO recruit subtraction (project owner's rule): a mission's own recruit still counts as
    # a requirement wherever listed. The tutorials AUTO-FIELD their casts and the mod refuses
    # to launch them without those wizards (AUTO_GIVEN_CHARACTERS, folded into the contract's
    # requiredCharacters), so their character needs are REGION requirements: The Asset needs
    # Zan (its own recruit!) to even enter; Rushwater needs Jen (its own recruit) and Zan.
    assert d.effective_required_characters(d.MISSION_BY_STAGE["Game_Prologue"]) == ["NavySeer"], \
        d.effective_required_characters(d.MISSION_BY_STAGE["Game_Prologue"])
    assert set(d.effective_required_characters(d.MISSION_BY_STAGE["Game_Witch_Intro"])) == {"WitchCop", "NavySeer"}, \
        d.effective_required_characters(d.MISSION_BY_STAGE["Game_Witch_Intro"])
    # Halfway extras still carried (harmless duplication of the region gate for tutorials).
    assert d.mission_half_required_characters("Game_Prologue") == ["NavySeer"], \
        d.mission_half_required_characters("Game_Prologue")
    # Proof the recruit is NOT stripped: both tutorials recruit a wizard their region requires.
    assert "NavySeer" in d.MISSION_BY_STAGE["Game_Prologue"]["recruits"]
    assert "WitchCop" in d.MISSION_BY_STAGE["Game_Witch_Intro"]["recruits"]
    print("[ok] opening: no recruit subtraction; tutorials' auto-given casts gate their regions")

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
            # OR-gates: every group must have an ability-free alternative the lone hero meets.
            for group in data.mission_required_any(sid) + data.mission_half_required_any(sid):
                assert any(not alt["abilities"] and all(c == hero for c in alt["characters"])
                           for alt in group), (sid, hero)
            all_openers.add(m["name"])
    # The Asset must always qualify for a Zan start (its only requirement is Zan, the start
    # hero in that case; no abilities).
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
    check_team_ability_gate()
    check_any_of_gate()
    check_retired_items()
    check_max_reachability()
    print("\nAll checks passed.")


if __name__ == "__main__":
    main()
