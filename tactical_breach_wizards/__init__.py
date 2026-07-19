"""Archipelago world definition for **Tactical Breach Wizards**.

Generation/server side of the integration. The matching in-game client is a BepInEx +
Harmony C# mod that lives in the game's plugins folder; the two halves agree on the
frozen item/location id contract carried in ``ap_data.json``.

What gets shuffled:
  * 5 playable wizards (characters)
  * 29 campaign mission-access unlocks
  * 14 abilities (4 special "dream" PerkUnlocks + 10 base-kit abilities)
  * perk points (progression; exactly each wizard's perk-tree size)
  * per-character "Confidence Boost" items (the only confidence source)
  * "Donut" filler pads the remainder
    (cosmetic outfits are NOT shuffled in -- see create_items)

What gets checked (locations):
  * mission completions, in-mission confidence goals, outfit purchases,
    ability unlocks, and character recruitments.

Goal: complete the finale, "Counterheist: The Roof".
"""

from typing import Dict, List

from BaseClasses import Item, ItemClassification, Location, Region, Tutorial
from worlds.AutoWorld import WebWorld, World

from . import data, rules
from .options import TBWOptions

_CLASSIFICATION = {
    "progression": ItemClassification.progression,
    "useful": ItemClassification.useful,
    "filler": ItemClassification.filler,
}


class TBWItem(Item):
    game = data.GAME_NAME


class TBWLocation(Location):
    game = data.GAME_NAME


def _build_item_name_groups() -> Dict[str, List[str]]:
    groups: Dict[str, List[str]] = {}
    by_category: Dict[str, List[str]] = {}
    # Retired items (never placed; kept only for id stability) stay out of every group.
    live_items = [it for it in data.ITEMS if not it.get("retired")]
    for it in live_items:
        by_category.setdefault(it["category"], []).append(it["name"])
    groups["Characters"] = by_category.get("character", [])
    groups["Mission Access"] = by_category.get("mission_access", [])
    groups["Abilities"] = by_category.get("ability", [])
    groups["Perk Points"] = by_category.get("perk_point", [])
    groups["Outfits"] = by_category.get("outfit", [])
    # Per-character convenience groups (e.g. "Zan" -> all of Zan's items).
    for it in live_items:
        internal = it.get("internal") or it.get("character")
        if internal in data.NAME_MAP:
            groups.setdefault(data.NAME_MAP[internal], []).append(it["name"])
    return groups


def _build_location_name_groups() -> Dict[str, List[str]]:
    groups: Dict[str, List[str]] = {}
    label = {
        "mission_complete": "Mission Completions",
        "mission_half": "Mission Halfway Points",
        "confidence_goal": "Confidence Goals",
        "outfit_purchase": "Outfit Purchases",
        "ability_unlock": "Ability Unlocks",
        "recruit": "Recruitments",
    }
    for loc in data.LOCATIONS:
        groups.setdefault(label[loc["category"]], []).append(loc["name"])
    return groups


class TBWWeb(WebWorld):
    theme = "dirt"
    tutorials = [
        Tutorial(
            "Multiworld Setup Guide",
            "A guide to playing Tactical Breach Wizards with Archipelago.",
            "English",
            "setup_en.md",
            "setup/en",
            ["Lincoln Tanner"],
        )
    ]


class TBWWorld(World):
    """Tactical Breach Wizards."""

    game = data.GAME_NAME
    web = TBWWeb()

    options_dataclass = TBWOptions
    options: TBWOptions

    item_name_to_id = data.item_name_to_id
    location_name_to_id = data.location_name_to_id
    item_name_groups = _build_item_name_groups()
    location_name_groups = _build_location_name_groups()

    # set in generate_early
    start_hero: str
    start_mission: str

    # ------------------------------------------------------------------ helpers
    def create_item(self, name: str) -> TBWItem:
        info = data.ITEM_BY_NAME[name]
        return TBWItem(name, _CLASSIFICATION[info["classification"]], self.item_name_to_id[name], self.player)

    def create_event(self, name: str) -> TBWItem:  # pragma: no cover - unused but conventional
        return TBWItem(name, ItemClassification.progression, None, self.player)

    def get_filler_item_name(self) -> str:
        return data.FILLER_ITEM_NAME

    # -------------------------------------------------------------- generation
    def generate_early(self) -> None:
        # Random starting wizard AND random starting mission. The opener is chosen only from
        # EARLY missions (act <= data.OPENER_MAX_ACT) winnable from scratch -- reachable with
        # just that one wizard + their single head-start perk and no abilities (see
        # data.is_valid_opener). No forced scripted pair: the player reaches everything else
        # through the mission-select board.
        self.start_hero = self.random.choice(data.PLAYABLE_CHARACTERS)
        pct = self.options.completion_perk_percent.value
        openers = [m for m in data.MISSIONS if data.is_valid_opener(m, self.start_hero, pct)]
        if not openers:  # safety net; should never happen (The Asset always qualifies)
            openers = [data.MISSION_BY_STAGE[data.START_MISSION_STAGE]]
        self.start_mission = self.random.choice(openers)["stageID"]

        self.multiworld.push_precollected(self.create_item(data.CHARACTER_ITEM_NAME[self.start_hero]))
        self.multiworld.push_precollected(self.create_item(data.MISSION_ITEM_NAME[self.start_mission]))
        # Head-start: 1 perk point on the starting wizard. Seeds the perk-gating ladder and
        # widens the otherwise-tight opening, easing generation. (One copy comes out of the pool.)
        self.multiworld.push_precollected(self.create_item(data.PERK_ITEM_NAME[self.start_hero]))
        # ...and the starting wizard's full base kit, so they're penalty-free (see the missing-
        # ability penalty in rules): this gives the fill one reliable wizard to satisfy perk
        # gates through. Other wizards still start kitless and must earn their kit to count.
        for base_item in data.BASE_ABILITY_ITEMS_BY_CHARACTER.get(self.start_hero, []):
            self.multiworld.push_precollected(self.create_item(base_item))
        # Widen the opening for the FILL: force two more valid-opener mission accesses into
        # the earliest reachable checks (AP early_items). A single-room opener can make
        # sphere 0 exactly ONE location (its Complete check); threading ~180 progression
        # items through that 1-wide bottleneck made ~15% of real generations FillError
        # (repro: seeds 3/4 with any knobs). The items still shuffle -- only their sphere
        # is pinned early -- and the player experience is "your first checks open more
        # missions", which is the pacing the fill needed anyway.
        extra_openers = [m for m in openers if m["stageID"] != self.start_mission]
        self.random.shuffle(extra_openers)
        for m in extra_openers[:2]:
            self.multiworld.early_items[self.player][data.MISSION_ITEM_NAME[m["stageID"]]] = 1

    def create_items(self) -> None:
        pool: List[Item] = []

        for it in data.ITEMS:
            cat = it["category"]
            if cat == "character":
                if it["internal"] == self.start_hero:
                    continue  # precollected
                pool.append(self.create_item(it["name"]))
            elif cat == "mission_access":
                stage = it["key"].split(":", 1)[1]
                if stage == self.start_mission:
                    continue  # precollected
                pool.append(self.create_item(it["name"]))
            elif cat == "ability":
                if it.get("retired"):
                    continue  # defined for id stability only; never placed
                if it.get("baseKit") and it.get("character") == self.start_hero:
                    continue  # precollected as the start hero's kit
                pool.append(self.create_item(it["name"]))
            # outfit items are intentionally NOT placed: buying an outfit at the shop is a
            # location check (and grants the cosmetic in-game already), and there is no mechanism
            # to equip an AP-received outfit separately, so they'd be inert. The freed pool slots
            # become generic filler (Donut) via the remainder fill below. The outfit item ids stay
            # defined in the contract (unused) so the frozen id scheme is untouched.
            # perk_point and filler handled below

        # Perk points (progression): exactly each wizard's perk-tree size. With the dream
        # abilities, these are the "perk power" the completion/goal gates check against.
        for internal, count in data.PERK_POINTS_PER_CHARACTER.items():
            placed = count - 1 if internal == self.start_hero else count  # 1 precollected for hero
            for _ in range(placed):
                pool.append(self.create_item(data.PERK_ITEM_NAME[internal]))

        # Confidence boosts: the only source of confidence (natural earning is blocked), so
        # place enough of each wizard's that their whole wardrobe stays affordable on the
        # staircase -- ceil(total outfit cost / confidence_per_boost).
        k = self.options.confidence_per_boost.value
        for internal in data.PLAYABLE_CHARACTERS:
            total_cost = data.OUTFIT_TOTAL_COST_PER_CHARACTER[internal]
            count = -(-total_cost // k) if total_cost else 0  # ceil
            for _ in range(count):
                pool.append(self.create_item(data.CONFIDENCE_ITEM_NAME[internal]))

        # The second mission is no longer auto-handed to the player on finishing the first: it's
        # a normal shuffled mission_access item now (above), so the opening isn't a forced linear
        # pair. Only the start character + start mission are precollected (see generate_early); the
        # player reaches everything else through the mission-select board.

        # Fill the remainder with generic filler ("Donut"). No location is pre-locked now, so the
        # pool fills all of them.
        remainder = len(data.LOCATIONS) - len(pool)
        for _ in range(remainder):
            pool.append(self.create_item(data.FILLER_ITEM_NAME))

        self.multiworld.itempool += pool

    def create_regions(self) -> None:
        player = self.player
        mw = self.multiworld
        k = self.options.confidence_per_boost.value
        completion_pct = self.options.completion_perk_percent.value
        goal_pct = self.options.goal_perk_percent.value

        menu = Region("Menu", player, mw)
        shop = Region("Outfit Shop", player, mw)
        mw.regions += [menu, shop]
        menu.connect(shop, "To Outfit Shop")

        region_by_stage: Dict[str, Region] = {}
        for mission in data.MISSIONS:
            region = Region(mission["name"], player, mw)
            mw.regions.append(region)
            region_by_stage[mission["stageID"]] = region
            menu.connect(region, f"To {mission['name']}", rules.make_mission_rule(player, mission))

        for loc in data.LOCATIONS:
            cat = loc["category"]
            if cat == "outfit_purchase":
                region = shop
            else:
                region = region_by_stage[data.region_stage_for_location(loc)]

            location = TBWLocation(player, loc["name"], self.location_name_to_id[loc["name"]], region)

            if cat == "confidence_goal":
                rule = rules.make_confidence_goal_rule(player, loc, goal_pct)
                if rule is not None:
                    location.access_rule = rule
            elif cat == "mission_complete":
                rule = rules.make_completion_rule(player, loc, completion_pct)
                if rule is not None:
                    location.access_rule = rule
            elif cat == "mission_half":
                rule = rules.make_half_rule(player, loc)
                if rule is not None:
                    location.access_rule = rule
            elif cat == "outfit_purchase":
                location.access_rule = rules.make_outfit_rule(player, loc, k)
            elif cat == "ability_unlock":
                # Fires exactly when its dream's mission-complete check fires (the mod reports
                # it on completion), so it must carry the SAME rule as that completion location
                # -- completion/halfway abilities and the perk gate -- on top of the shared
                # region rule. Region reachability alone made e.g. Unlock: Unlock_DeathsFloor
                # look reachable when the dream itself couldn't be finished.
                comp_loc = data.LOCATION_BY_KEY.get("mission:" + str(loc.get("missionStageID")))
                if comp_loc is not None:
                    rule = rules.make_completion_rule(player, comp_loc, completion_pct)
                    if rule is not None:
                        location.access_rule = rule
            elif cat == "recruit":
                # Recruits also fire on their mission's COMPLETION (the mod reports them from
                # ReportMissionComplete), so they carry the same rule as that completion check
                # -- e.g. Recruit: Rion demands actually being able to BEAT The Siege Cleric
                # (Banks for the resurrect objective, perk gate), not merely enter it.
                comp_loc = data.LOCATION_BY_KEY.get("mission:" + str(loc.get("stageID")))
                if comp_loc is not None:
                    rule = rules.make_completion_rule(player, comp_loc, completion_pct)
                    if rule is not None:
                        location.access_rule = rule

            region.locations.append(location)

    def set_rules(self) -> None:
        # Victory = finish the finale AND (per the contract's goal flags) hold the full
        # roster + every ability item. The extras live ONLY here on the completion
        # condition; location/region rules stay untouched so the fill is unconstrained.
        extra_items = tuple(data.GOAL_REQUIRED_ITEM_NAMES)
        self.multiworld.completion_condition[self.player] = (
            lambda state: state.can_reach_location(data.GOAL_LOCATION_NAME, self.player)
            and state.has_all(extra_items, self.player)
        )

    # ------------------------------------------------------------- slot data
    def fill_slot_data(self) -> Dict:
        return {
            "death_link": bool(self.options.death_link.value),
            "goal": "finale_roof",
            # How much confidence each "Confidence Boost" item grants -- the mod needs this
            # to apply received confidence items in-game.
            "confidence_per_boost": self.options.confidence_per_boost.value,
            # Convenience extras; the client also learns these via ReceivedItems.
            "start_character": self.start_hero,
            "start_mission": self.start_mission,
        }
