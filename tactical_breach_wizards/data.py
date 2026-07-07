"""Static data for the Tactical Breach Wizards apworld.

The single source of truth is ``ap_data.json`` (copied verbatim from the mod repo's
``tools/ap_data.json``). It carries the **frozen** item/location id contract that the
in-game BepInEx client also compiles against, plus the rich logic metadata
(per-mission act/order/recruits/required-characters, per-location act/character
linkage) used to build regions and rules.

NEVER hand-edit the ids or renumber them: seeds depend on id stability. New content
is appended only, by regenerating ``ap_data.json`` in the mod repo and re-copying it.
"""

import json
import os
import pkgutil
from typing import Dict, List


def _load_contract() -> Dict:
    """Read ap_data.json. pkgutil.get_data is the zip-safe path (works inside a
    packed .apworld); fall back to reading next to this file for directory installs
    and bare test environments where the package has no loader."""
    try:
        raw = pkgutil.get_data(__package__, "ap_data.json")
    except Exception:
        raw = None
    if raw is not None:
        return json.loads(raw.decode("utf-8"))
    path = os.path.join(os.path.dirname(__file__), "ap_data.json")
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


_DATA = _load_contract()

GAME_NAME: str = _DATA["gameName"]
BASE: int = _DATA["base"]
PLAYABLE_CHARACTERS: List[str] = list(_DATA["playableCharacters"])
NAME_MAP: Dict[str, str] = dict(_DATA["nameMap"])          # internal -> display (Zan, Jen, ...)
GOAL: Dict = dict(_DATA["goal"])
MISSION_ORDER: List[str] = list(_DATA["missionOrder"])

ITEMS: List[Dict] = list(_DATA["items"])
LOCATIONS: List[Dict] = list(_DATA["locations"])
MISSIONS: List[Dict] = list(_DATA["missions"])

# ---------------------------------------------------------------------------
# Name <-> id maps required by the AP World base class.
# ---------------------------------------------------------------------------
item_name_to_id: Dict[str, int] = {it["name"]: it["id"] for it in ITEMS}
location_name_to_id: Dict[str, int] = {loc["name"]: loc["id"] for loc in LOCATIONS}

ITEM_BY_NAME: Dict[str, Dict] = {it["name"]: it for it in ITEMS}
LOCATION_BY_NAME: Dict[str, Dict] = {loc["name"]: loc for loc in LOCATIONS}
MISSION_BY_STAGE: Dict[str, Dict] = {m["stageID"]: m for m in MISSIONS}

# ---------------------------------------------------------------------------
# Convenience lookups for items by their semantic role.
# ---------------------------------------------------------------------------
CHARACTER_ITEM_NAME: Dict[str, str] = {}   # internal char -> item name
PERK_ITEM_NAME: Dict[str, str] = {}        # internal char -> perk-point item name
CONFIDENCE_ITEM_NAME: Dict[str, str] = {}  # internal char -> confidence-boost item name
MISSION_ITEM_NAME: Dict[str, str] = {}     # stageID -> mission-access item name
FILLER_ITEM_NAME: str = ""

for _it in ITEMS:
    cat = _it["category"]
    if cat == "character":
        CHARACTER_ITEM_NAME[_it["internal"]] = _it["name"]
    elif cat == "perk_point":
        PERK_ITEM_NAME[_it["internal"]] = _it["name"]
    elif cat == "confidence":
        CONFIDENCE_ITEM_NAME[_it["internal"]] = _it["name"]
    elif cat == "mission_access":
        # key looks like "missionaccess:Game_Prologue"
        MISSION_ITEM_NAME[_it["key"].split(":", 1)[1]] = _it["name"]
    elif cat == "filler":
        FILLER_ITEM_NAME = _it["name"]

CHARACTER_ITEM_NAMES: List[str] = [CHARACTER_ITEM_NAME[c] for c in PLAYABLE_CHARACTERS]
PERK_ITEM_NAMES: List[str] = [it["name"] for it in ITEMS if it["category"] == "perk_point"]
# All ability item names (4 PerkUnlock "dream" specials + 10 base-kit abilities).
ABILITY_ITEM_NAMES: List[str] = [it["name"] for it in ITEMS if it["category"] == "ability"]
# Ability savename (part after "ability:" in the key) -> item name. Lets mission/goal
# requirements reference abilities by savename (e.g. "UnlockFalseProphet", "Unlock_ChainShockSuperchain").
ABILITY_ITEM_BY_SAVENAME: Dict[str, str] = {
    it["key"].split(":", 1)[1]: it["name"] for it in ITEMS if it["category"] == "ability"
}


def mission_required_abilities(stage_id: str) -> List[str]:
    """Ability savenames required to complete a mission (empty if none)."""
    m = MISSION_BY_STAGE.get(stage_id)
    return list(m.get("requiredAbilities", [])) if m else []


def mission_half_required_abilities(stage_id: str) -> List[str]:
    """Ability savenames required to reach a mission's HALFWAY checkpoint (empty if none).
    These are also folded into the full completion (full mission >= half mission)."""
    m = MISSION_BY_STAGE.get(stage_id)
    return list(m.get("halfRequiredAbilities", [])) if m else []


def mission_half_required_characters(stage_id: str) -> List[str]:
    """Extra characters required to reach a mission's HALFWAY checkpoint (empty if none).
    Also folded into the full completion."""
    m = MISSION_BY_STAGE.get(stage_id)
    return list(m.get("halfRequiredCharacters", [])) if m else []


# Base-kit ability item names per wizard. Each one a wizard is MISSING counts as -1 to their
# effective perk power (the base game assumes a full kit), floored at 0 -- see
# rules.effective_perks_for_character.
BASE_ABILITY_ITEMS_BY_CHARACTER: Dict[str, List[str]] = {}
for _it in ITEMS:
    if _it["category"] == "ability" and _it.get("baseKit"):
        BASE_ABILITY_ITEMS_BY_CHARACTER.setdefault(_it["character"], []).append(_it["name"])


def recommended_perks_for_stage(stage_id: str) -> int:
    """Recommended PER-SLOT perks for a mission -- the strongest single wizard expected
    there (0 if unknown). Gated against the player's best unlocked wizard."""
    m = MISSION_BY_STAGE.get(stage_id)
    return int(m.get("recommendedPerks", 0)) if m else 0

# How many perk points (perk-tree ability upgrades) each wizard can actually spend in
# the base game -- i.e. the number of nodes in their perk tree. The mod suppresses
# natural leveling, so AP perk-point items are the ONLY way to buy upgrades; placing more
# than this many of a character's perk points would just create unspendable dead items.
# Sourced from the campaign's cumulative PerkProgress save totals (NavySeer reaches 7
# once the finale is counted) and confirmed by the project owner. NOT the same thing as
# confidence goals (the 154 in-mission challenge *locations*) or the 5 special "dream"
# ability unlocks (separate `ability` items).
PERK_POINTS_PER_CHARACTER: Dict[str, int] = {
    "NavySeer": 7,
    "WitchCop": 5,
    "NecroMedic": 5,
    "RiotPriest": 5,
    "Druid": 4,
}

# Outfit-shop economy. The mod blocks natural confidence earning, so every outfit purchase
# is gated by confidence that comes only from `Confidence Boost: <Char>` items. To keep the
# shop fully clearable under `accessibility: full`, we model it as a staircase: sort each
# wizard's outfits by cost and require total confidence >= the cumulative cost up to and
# including that outfit. OUTFIT_CONFIDENCE_THRESHOLD maps each outfit_purchase location name
# -> that cumulative cost; OUTFIT_TOTAL_COST_PER_CHARACTER is the per-wizard sum (the most
# expensive step), used to size how many boosts to place in the pool.
OUTFIT_CONFIDENCE_THRESHOLD: Dict[str, int] = {}
OUTFIT_TOTAL_COST_PER_CHARACTER: Dict[str, int] = {c: 0 for c in PLAYABLE_CHARACTERS}

_outfits_by_char: Dict[str, List[Dict]] = {}
for _loc in LOCATIONS:
    if _loc["category"] == "outfit_purchase":
        _outfits_by_char.setdefault(_loc["character"], []).append(_loc)
for _ch, _locs in _outfits_by_char.items():
    _cum = 0
    for _loc in sorted(_locs, key=lambda l: (l["cost"], l["name"])):
        _cum += _loc["cost"]
        OUTFIT_CONFIDENCE_THRESHOLD[_loc["name"]] = _cum
    OUTFIT_TOTAL_COST_PER_CHARACTER[_ch] = _cum

# The victory location: completing the finale roof mission.
GOAL_LOCATION_KEY: str = GOAL["locationKey"]            # "mission:Game_Finale_Roof"
GOAL_LOCATION_NAME: str = next(
    loc["name"] for loc in LOCATIONS if loc["key"] == GOAL_LOCATION_KEY
)


# Opening. Only the start CHARACTER + start MISSION (The Asset) are precollected; the player
# reaches everything else through the mission-select board. The first two missions are still
# scripted tutorials (they supply their own cast) and stay perk-gate-exempt, but the second is
# no longer force-handed on finishing the first -- it's a normal shuffled mission_access item.
START_MISSION_STAGE = "Game_Prologue"        # "The Asset"
SECOND_MISSION_STAGE = "Game_Witch_Intro"    # "Rushwater Reunion"
SCRIPTED_TUTORIAL_STAGES = {START_MISSION_STAGE, SECOND_MISSION_STAGE}
# The first mission's completion location (kept for reference/tests; no longer holds a locked item).
FIRST_MISSION_COMPLETE_LOCATION = next(
    loc["name"] for loc in LOCATIONS if loc["key"] == f"mission:{START_MISSION_STAGE}"
)

# Anxiety-dream missions are gated on the wizard they're about. Their stageID encodes the
# wizard by display name (Game_Lucid_Dream_Banks -> Banks -> NecroMedic).
_DISPLAY_TO_INTERNAL = {v: k for k, v in NAME_MAP.items()}
DREAM_REQUIRED_CHARACTER: Dict[str, str] = {}
for _m in MISSIONS:
    _sid = _m["stageID"]
    if _sid.startswith("Game_Lucid_Dream_"):
        _who = _DISPLAY_TO_INTERNAL.get(_sid.rsplit("_", 1)[-1])
        if _who:
            DREAM_REQUIRED_CHARACTER[_sid] = _who


_ABILITY_NAME_BY_STAGE = {it["stageID"]: it["name"] for it in ITEMS if it["category"] == "ability"}
# internal character -> their dream-ability item name (each dream grants that wizard +1 perk).
ABILITY_ITEM_FOR_CHARACTER: Dict[str, str] = {}
for _loc in LOCATIONS:
    if _loc["category"] == "ability_unlock":
        _ch = DREAM_REQUIRED_CHARACTER.get(_loc["missionStageID"])
        if _ch and _loc["stageID"] in _ABILITY_NAME_BY_STAGE:
            ABILITY_ITEM_FOR_CHARACTER[_ch] = _ABILITY_NAME_BY_STAGE[_loc["stageID"]]


def effective_required_characters(mission: Dict) -> List[str]:
    """Characters that must be unlocked to enter a mission's region.

    - The mission's firm ``requiredCharacters`` minus its own ``recruits`` (a recruitment
      mission must not require the character it recruits -- you get them BY doing it)...
    - ...plus, for an anxiety dream, the wizard that dream is about.

    Scripted tutorials are NOT exempted: they still supply their own cast in-game, but their
    firm requiredCharacters are honoured so the logic never expects a mission before the
    player holds the heroes it needs (e.g. Rushwater Reunion requires Zan). Their own recruit
    is still stripped (Rushwater recruits Jen, so it requires only Zan, not Jen).
    """
    sid = mission["stageID"]
    recruits = set(mission.get("recruits", []))
    req = [c for c in mission.get("requiredCharacters", []) if c not in recruits]
    dream = DREAM_REQUIRED_CHARACTER.get(sid)
    if dream and dream not in req:
        req.append(dream)
    return req


# ---- act-character gate --------------------------------------------------------------------
# How many characters are needed to ENTER each act (0-indexed; act 0 = "Act 1"). This paces late
# acts behind an accumulated roster. Lives here (not rules.py) so the opener logic can share it
# without a circular import; rules.act_reachable reads act_character_requirement().
#
# TOGGLE: the gate is currently DISABLED (project owner) -- flip ACT_GATE_ENABLED back to True to
# re-enable it with exactly these thresholds. While disabled every act needs 0 characters.
ACT_GATE_ENABLED = False
ACT_CHARACTER_GATE: Dict[int, int] = {0: 0, 1: 2, 2: 3, 3: 5}

# Perk-power gating floors (0-indexed acts; act N = the game's "Act N+1"). Confidence goals
# gate from Act 2 (0-idx 1); completions from Act 3 (0-idx 2). Act 1 stays ungated. They live
# here (not rules.py) so the opener logic can share them; rules.py reads these.
PERK_GATE_MIN_ACT_GOAL = 1
PERK_GATE_MIN_ACT_COMPLETION = 2

# The random starting mission is only drawn from acts up to this (0-indexed: 1 = the game's
# Act 2). This caps how late in the campaign a seed can open INDEPENDENTLY of the act-character
# gate above -- with that gate disabled, every low-requirement mission (including finale-act
# ones like the Counterheists) would otherwise qualify as an opener, dropping a lone fresh
# wizard into a mission balanced for a perked-out squad. Raise it for chaos starts.
OPENER_MAX_ACT = 1

# Goal mission (the finale roof); never a valid random opener -- starting on it would win instantly.
GOAL_STAGE_ID: str = GOAL_LOCATION_KEY.split(":", 1)[1]


def act_character_requirement(act: int) -> int:
    """Characters required to enter an act. 0 for every act while the gate is disabled."""
    if not ACT_GATE_ENABLED:
        return 0
    return ACT_CHARACTER_GATE.get(act, 5)


def is_valid_opener(mission: Dict, start_hero: str, completion_perk_percent: int = None) -> bool:
    """Whether a mission can be the randomized starting mission -- i.e. winnable from scratch
    with just the one starting wizard + their single head-start perk and NO abilities.

    Requirements, mirroring the access logic (rules.py):
      * Early enough: act <= OPENER_MAX_ACT (this is what keeps finale-act missions out of the
        opener pool even while the act-character gate is disabled).
      * The act's character-count gate is satisfiable by the lone start hero (<= 1).
      * Not the goal mission (never start on the win).
      * No required abilities -- completion OR halfway -- the player starts with none.
      * Required characters (after recruit-strip, plus halfway extras) all satisfied by the
        single start hero.
      * If the mission's completion is perk-gated (act >= PERK_GATE_MIN_ACT_COMPLETION and a
        percent is given), the head-start power of 1 must satisfy it -- the seed must never
        open on a mission whose own completion check is out of logic.

    NOTE: many missions still have empty requiredCharacters/requiredAbilities in the data, so
    an opener may still be unbeatable in-game (wrong squad) -> add that mission's requirements
    in generate_ap_data.py to drop it from the pool.
    """
    sid = mission["stageID"]
    act = mission.get("act", 0)
    if sid == GOAL_STAGE_ID:
        return False
    if act > OPENER_MAX_ACT:
        return False
    if act_character_requirement(act) > 1:
        return False
    if mission_required_abilities(sid) or mission_half_required_abilities(sid):
        return False
    required = effective_required_characters(mission) + mission_half_required_characters(sid)
    if not all(c == start_hero for c in required):
        return False
    if completion_perk_percent and act >= PERK_GATE_MIN_ACT_COMPLETION:
        rec = recommended_perks_for_stage(sid)
        need = -(-(rec * completion_perk_percent) // 100)  # ceil
        if need > 1:  # head start = 1 perk point on a penalty-free (full-kit) wizard
            return False
    return True


def region_stage_for_location(loc: Dict) -> str:
    """Which mission region a location belongs to (or '' for meta locations).

    ability_unlock checks are the reward for completing the anxiety dream named in
    ``missionStageID``, so they live in that dream's region."""
    cat = loc["category"]
    if cat in ("confidence_goal", "ability_unlock", "mission_half"):
        return loc["missionStageID"]
    if cat in ("mission_complete", "recruit"):
        return loc["stageID"]
    return ""  # outfit_purchase -> shop
