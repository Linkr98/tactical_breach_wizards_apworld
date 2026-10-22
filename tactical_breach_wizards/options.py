"""Player-facing yaml options for Tactical Breach Wizards."""

from dataclasses import dataclass

from Options import Choice, DeathLink, PerGameCommonOptions, Range, Toggle


class StartingHero(Choice):
    """Which wizard you start with. Starting wizard stats with 1 perk point and all abilities unlocked(If ShuffleBaseAbilities = true). 
    """
    display_name = "Starting Hero"
    option_zan = 0
    option_jen = 1
    option_banks = 2
    option_dall = 3
    option_rion = 4
    default = "random"


class ConfidenceBoostsPerWizard(Range):
    """How many "Confidence Boost" items to unlock all outfit checks for each wizard.
    More of these reduces filler.
    """
    display_name = "Confidence Boosts per Wizard"
    range_start = 1
    range_end = 20
    default = 10


class ExtraConfidenceBoosts(Range):
    """Extra Confidence Boost items per wizard, on top of the amount needed to clear their
    wardrobe. Gives same amount of points as the normal ones but not required for logic so your less likely to get hard stuck, or soft lock yourself.
    If there is a low number of boosts per wizard, you will want a low number of this to avoid breaking logic to much.
    It is designed for if you have a large number of items, missing one confidence boost dosn't hold everything up/
    """
    display_name = "Extra Confidence Boosts"
    range_start = 0
    range_end = 10
    default = 2


class CompletionPerkPercent(Range):
    """What percent of the perks you would have at the point of the story is needed for logic to think a mission is beatable.
    This math uses the total perks for your team and will count your best wizard multiple times, so the game expects things like a team of 5 Zan's.
    """
    display_name = "Completion Perk %"
    range_start = 25
    range_end = 100
    default = 50


class GoalPerkPercent(Range):
    """Same as CompletionPerkPercent but for confidence goals. Should always be higher then Completion perk percent.
    """
    display_name = "Confidence Goal Perk %"
    range_start = 25
    range_end = 100
    default = 60


class ShuffleBaseAbilities(Toggle):
    """Shuffle each wizard's BASE-KIT abilities (Zan's Predictive Bolt / Time Boost / False
    Prophet, Jen's Broom Breach / Gale Grenade / Chain Bolt, Banks's Spectral Skull /
    Transference, Rion's Spore Grenade) into the multiworld as items.
    """
    display_name = "Shuffle Base Abilities"


class ArmouryCachesGoal(Toggle):
    """Include Dall's "Destroy the Caches" confidence goal in The B Team's fifth room (The
    Armoury) as a check.

    This goal is for some reason one of the hardest things in the game.
    I dont like it and I didnt want it to skew the Goal Perk % too much, so I made removed by default.
    """
    display_name = "Armoury Caches Goal"


@dataclass
class TBWOptions(PerGameCommonOptions):
    starting_hero: StartingHero
    shuffle_base_abilities: ShuffleBaseAbilities
    armoury_caches_goal: ArmouryCachesGoal
    confidence_boosts_per_wizard: ConfidenceBoostsPerWizard
    extra_confidence_boosts: ExtraConfidenceBoosts
    completion_perk_percent: CompletionPerkPercent
    goal_perk_percent: GoalPerkPercent
    death_link: DeathLink
