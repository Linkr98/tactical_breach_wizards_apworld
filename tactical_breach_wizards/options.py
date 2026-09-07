"""Player-facing yaml options for Tactical Breach Wizards."""

from dataclasses import dataclass

from Options import Choice, DeathLink, PerGameCommonOptions, Range


class StartingHero(Choice):
    """Which wizard you start with (plus their base kit and 1 perk point). The starting
    mission is then picked at random from the early missions winnable with just that wizard.

    "random" (the default) picks one of the five for you.
    """
    display_name = "Starting Hero"
    option_zan = 0
    option_jen = 1
    option_banks = 2
    option_dall = 3
    option_rion = 4
    default = "random"


class ConfidenceBoostsPerWizard(Range):
    """How many "Confidence Boost" items it takes to clear a wizard's whole wardrobe.

    The mod blocks natural confidence earning, so these items are the only way to afford
    outfits at the shop -- and each outfit purchase is a check. Every wizard gets this many
    boosts in the pool, and each boost's VALUE scales with that wizard's total wardrobe cost
    (ceil(total / this count)) -- so an expensive wardrobe (Jen, 60) and a cheap one
    (Rion, 12) both clear in the same number of boosts, just bigger ones for Jen.

    A lower count means fewer, larger boosts (more room for other filler); a higher count
    means more, smaller boosts (the shop economy is felt more).
    """
    display_name = "Confidence Boosts per Wizard"
    range_start = 1
    range_end = 20
    default = 5


class ExtraConfidenceBoosts(Range):
    """Extra Confidence Boost items per wizard, on top of the amount needed to clear their
    wardrobe. Each is worth that wizard's boost value, replaces one generic filler (Donut)
    in the pool, and is NOT required by logic -- pure slack.

    The slack cushions out-of-order shop purchases (buying below an unbought cheaper outfit
    can otherwise strand you short of it) and gets shop checks in reach a little sooner.
    """
    display_name = "Extra Confidence Boosts"
    range_start = 0
    range_end = 10
    default = 2


class CompletionPerkPercent(Range):
    """Perk-power gate for completing a mission AND for reaching its halfway checkpoint, as a
    percent of the mission's recommended PER-SLOT perks (the strongest single wizard the game
    expects there). 0 disables it.

    A wizard's perk power = their perk-tree points (always shuffled in as progression) + 1 if
    their dream ability is unlocked. Because you can field one wizard in multiple slots, the
    check is against your BEST unlocked wizard -- EXCEPT in anxiety dreams, whose squad is
    fully scripted: there it's the best of that forced cast (Rion's dream needs a perked
    Rion, not a strong Zan), with the threshold capped at what that cast can ever reach.
    """
    display_name = "Completion Perk %"
    range_start = 0
    range_end = 100
    default = 25


class GoalPerkPercent(Range):
    """Perk-power gate for a mission's confidence goals, as a percent of the mission's
    recommended per-slot perks -- checked against your best unlocked wizard (or, in anxiety
    dreams, their forced cast, like completion_perk_percent). Confidence goals are harder
    than just clearing the mission, so this defaults higher. 0 disables it.
    """
    display_name = "Confidence Goal Perk %"
    range_start = 0
    range_end = 100
    default = 50


@dataclass
class TBWOptions(PerGameCommonOptions):
    starting_hero: StartingHero
    confidence_boosts_per_wizard: ConfidenceBoostsPerWizard
    extra_confidence_boosts: ExtraConfidenceBoosts
    completion_perk_percent: CompletionPerkPercent
    goal_perk_percent: GoalPerkPercent
    death_link: DeathLink
