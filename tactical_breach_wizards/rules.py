"""Access logic for Tactical Breach Wizards.

Logic model (see APWORLD_HANDOFF.md / ap-id-contract memory):

* **Loose ordering.** The campaign is not a strict chain. Any mission is playable once its
  ``mission_access`` item is held (plus the requirements below).
* **Act-character gate** (currently DISABLED via data.ACT_GATE_ENABLED): when on, late acts
  need an accumulated roster (act 1 >=2 characters, act 2 >=3, act 3 all 5).
* A **mission region** is reachable when the player has its ``mission_access`` item,
  satisfies the act gate, and has every character the mission firmly requires — INCLUDING
  the mission's own recruit if listed (controlling a wizard always means having unlocked
  them first; see data.effective_required_characters).
* **confidence_goal** locations additionally require the goal's character (always, even
  the mission's own recruit) plus a perk-power gate, and -- for goals that need many
  abilities at once (``requiredTotalAbilities``) -- a team-wide ability count.
* **outfit_purchase** locations require the outfit's character plus a soft economy gate
  scaling with the confidence cost.
* **ability_unlock** locations are the reward for the anxiety dream they live in; the dream's
  region rule (mission access + that dream's wizard) is sufficient.
"""

from typing import Dict

from . import data

# The act-character gate (thresholds + on/off toggle) and the perk-gating floors live in
# data.py so the opener logic can share them without a circular import; see
# data.act_character_requirement / data.ACT_GATE_ENABLED / data.PERK_GATE_MIN_ACT_*.
PERK_GATE_MIN_ACT_GOAL = data.PERK_GATE_MIN_ACT_GOAL
PERK_GATE_MIN_ACT_COMPLETION = data.PERK_GATE_MIN_ACT_COMPLETION

# Missing base-kit abilities dock a wizard's effective perk power, but the total dock per
# wizard is CAPPED here so kitless perks aren't worthless (which made generation impossible).
# e.g. cap 2: a wizard missing all 3 base abilities loses 2, not 3.
MAX_MISSING_ABILITY_PENALTY = 2

# Team-wide ability gate (requiredTotalAbilities on a confidence goal, e.g. "use 9 abilities
# in one turn"). A full-kit wizard fields ABILITIES_PER_WIZARD abilities; each BASE-KIT
# ability item they're still missing removes one. Dream specials do NOT count: they upgrade
# an existing base ability rather than add a unique one. Only as many wizards as the goal's
# room actually fields can contribute (the location's squadSize, read from the level's wizard
# prefabs by the generator; DEFAULT_SQUAD_SIZE when unknown) -- and fielding the same wizard
# twice adds no new abilities.
ABILITIES_PER_WIZARD = 4
DEFAULT_SQUAD_SIZE = 4


def character_count(state, player: int) -> int:
    return sum(1 for name in data.CHARACTER_ITEM_NAMES if state.has(name, player))


def effective_perks_for_character(state, player: int, internal: str) -> int:
    """A single wizard's perk power: perk-point items collected, +1 if their dream ability is
    collected, MINUS 1 for each base-kit ability they're still missing (the base game assumes a
    full kit, so a half-kitted wizard is weaker than raw perk count implies). Floored at 0."""
    n = state.count(data.PERK_ITEM_NAME[internal], player)
    ability = data.ABILITY_ITEM_FOR_CHARACTER.get(internal)
    if ability and state.has(ability, player):
        n += 1
    missing = sum(
        1 for base_item in data.BASE_ABILITY_ITEMS_BY_CHARACTER.get(internal, [])
        if not state.has(base_item, player)
    )
    n -= min(missing, MAX_MISSING_ABILITY_PENALTY)
    return max(0, n)


def best_unlocked_perks(state, player: int) -> int:
    """The perk power of the player's strongest UNLOCKED wizard. Because a wizard can be
    fielded in multiple slots (repetition), this -- not the team total -- is what a mission's
    per-slot recommendation is gated against."""
    best = 0
    for internal in data.PLAYABLE_CHARACTERS:
        if has_character(state, player, internal):
            p = effective_perks_for_character(state, player, internal)
            if p > best:
                best = p
    return best


def team_ability_count(state, player: int, squad_size: int = DEFAULT_SQUAD_SIZE) -> int:
    """How many distinct abilities the player's best possible squad for a ``squad_size``-wizard
    room can field: for each UNLOCKED wizard, ABILITIES_PER_WIZARD minus their still-missing
    BASE-KIT ability items (dream specials are upgrades, not extra abilities), summed over the
    best ``squad_size`` wizards."""
    counts = []
    for internal in data.PLAYABLE_CHARACTERS:
        if has_character(state, player, internal):
            missing = sum(
                1 for item in data.BASE_ABILITY_ITEMS_BY_CHARACTER.get(internal, [])
                if not state.has(item, player)
            )
            counts.append(max(0, ABILITIES_PER_WIZARD - missing))
    counts.sort(reverse=True)
    return sum(counts[:squad_size])


def _perk_threshold(recommended: int, percent: int) -> int:
    """ceil(recommended * percent / 100) -- 'at least percent% of the per-slot recommended'."""
    return -(-(recommended * percent) // 100)


def has_abilities(state, player: int, savenames) -> bool:
    """True if the player owns every listed ability (by savename)."""
    for sv in savenames:
        item = data.ABILITY_ITEM_BY_SAVENAME.get(sv)
        if item is None or not state.has(item, player):
            return False
    return True


def make_half_rule(player: int, loc: dict):
    """mission_half gate: the halfway checkpoint of a multi-room mission. It lives in the
    mission's region (so it already inherits mission access + the act gate + the mission's firm
    required characters). On top of that it imposes ONLY the halfway extras (HALF_REQUIRED* in the
    generator) -- no completion-ability or perk gate -- which makes it an easier, EARLIER check
    than finishing the mission. Returns None when there are no halfway extras (region reachability
    is then sufficient)."""
    extra_chars = loc.get("requiredCharacters", [])
    abilities = loc.get("requiredAbilities", [])
    if not extra_chars and not abilities:
        return None

    def rule(state) -> bool:
        for c in extra_chars:
            if not has_character(state, player, c):
                return False
        return has_abilities(state, player, abilities)

    return rule


def make_completion_rule(player: int, loc: dict, percent: int):
    """mission_complete gate: needs every ability required to complete the mission, PLUS every
    halfway extra (a mission can only be finished by first reaching its halfway point, so the full
    completion always assumes the whole restriction set of the half), AND (from Act 2 on) the best
    unlocked wizard at >= percent% of the recommended per-slot perks. Scripted tutorials are exempt
    from the perk gate. Returns None if nothing applies."""
    stage = loc["stageID"]
    # Union the completion abilities with the halfway abilities (full >= half).
    abilities = list(dict.fromkeys(
        data.mission_required_abilities(stage) + data.mission_half_required_abilities(stage)))
    half_chars = data.mission_half_required_characters(stage)
    perk_need = 0
    if stage not in data.SCRIPTED_TUTORIAL_STAGES and loc["act"] >= PERK_GATE_MIN_ACT_COMPLETION:
        perk_need = _perk_threshold(data.recommended_perks_for_stage(stage), percent)
    if not abilities and not half_chars and perk_need <= 0:
        return None

    def rule(state) -> bool:
        if not has_abilities(state, player, abilities):
            return False
        for c in half_chars:
            if not has_character(state, player, c):
                return False
        return best_unlocked_perks(state, player) >= perk_need

    return rule


def has_character(state, player: int, internal: str) -> bool:
    return state.has(data.CHARACTER_ITEM_NAME[internal], player)


def act_reachable(state, player: int, act: int) -> bool:
    return character_count(state, player) >= data.act_character_requirement(act)


def make_mission_rule(player: int, mission: Dict):
    """Entrance rule: Menu -> a mission's region."""
    access_item = data.MISSION_ITEM_NAME[mission["stageID"]]
    act = mission["act"]
    required = data.effective_required_characters(mission)

    def rule(state) -> bool:
        if not state.has(access_item, player):
            return False
        if not act_reachable(state, player, act):
            return False
        return all(has_character(state, player, c) for c in required)

    return rule


def make_confidence_goal_rule(player: int, loc: Dict, percent: int):
    """Location rule on top of the mission region: requires the goal's character (always --
    even the mission's own recruit; controlling a wizard means having unlocked them), any
    extra GOAL_REQUIREMENTS characters/abilities, a team-wide ability count when the goal
    needs many abilities at once (``requiredTotalAbilities``, e.g. "use 9 abilities in one
    turn"), AND (from Act 2 on) the best unlocked wizard at >= percent% of the mission's
    recommended per-slot perks."""
    char = loc["character"]
    char_required = True
    extra_chars = loc.get("requiredCharacters", [])
    abilities = loc.get("requiredAbilities", [])
    team_abilities_needed = int(loc.get("requiredTotalAbilities", 0) or 0)
    squad_size = int(loc.get("squadSize", 0) or 0) or DEFAULT_SQUAD_SIZE
    need = 0
    if loc["missionStageID"] not in data.SCRIPTED_TUTORIAL_STAGES and loc["act"] >= PERK_GATE_MIN_ACT_GOAL:
        need = _perk_threshold(data.recommended_perks_for_stage(loc["missionStageID"]), percent)

    if not char_required and not extra_chars and not abilities and need <= 0 and team_abilities_needed <= 0:
        return None  # region reachability is sufficient

    def rule(state) -> bool:
        if char_required and not has_character(state, player, char):
            return False
        for c in extra_chars:
            if not has_character(state, player, c):
                return False
        if not has_abilities(state, player, abilities):
            return False
        if team_abilities_needed > 0 and team_ability_count(state, player, squad_size) < team_abilities_needed:
            return False
        return best_unlocked_perks(state, player) >= need

    return rule


def make_outfit_rule(player: int, loc: Dict, confidence_per_boost: int):
    """Outfit purchases need the wizard unlocked AND enough confidence to afford this
    outfit on the staircase (total confidence >= cumulative cost up to this outfit).

    Confidence comes only from `Confidence Boost: <Char>` items (natural earning is blocked
    by the mod), each worth ``confidence_per_boost``, so the requirement is a number of that
    wizard's boosts."""
    char = loc["character"]
    confidence_item = data.CONFIDENCE_ITEM_NAME[char]
    threshold = data.OUTFIT_CONFIDENCE_THRESHOLD[loc["name"]]
    needed = -(-threshold // confidence_per_boost)  # ceil(threshold / confidence_per_boost)

    def rule(state) -> bool:
        return has_character(state, player, char) and state.count(confidence_item, player) >= needed

    return rule
