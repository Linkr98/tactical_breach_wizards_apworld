"""Player-facing yaml options for Tactical Breach Wizards."""

from dataclasses import dataclass

from Options import DeathLink, PerGameCommonOptions, Range


class ConfidencePerBoost(Range):
    """How much confidence each "Confidence Boost" item grants the matching wizard.

    The mod blocks natural confidence earning, so these items are the only way to afford
    outfits at the shop -- and each outfit purchase is a check. Enough boosts are always
    placed for every wizard to clear their whole wardrobe; this value just sets the
    granularity. A lower value means more, smaller boosts (the shop economy is felt more);
    a higher value means fewer, larger boosts (more room for other filler).

    Must be at least 2: at 1 the pool can't hold enough boosts to afford every outfit.
    """
    display_name = "Confidence per Boost"
    range_start = 2
    range_end = 20
    default = 5


class CompletionPerkPercent(Range):
    """Perk-power gate for completing a mission (from Act 2 on), as a percent of the mission's
    recommended PER-SLOT perks (the strongest single wizard the game expects there).

    A wizard's perk power = their perk-tree points (always shuffled in as progression) + 1 if
    their dream ability is unlocked. Because you can field one wizard in multiple slots, the
    check is against your BEST unlocked wizard -- so you can't clear a too-hard late mission
    without at least one suitably strong wizard.
    note: 70 and above will start causing fill issues sometimes.
    """
    display_name = "Completion Perk %"
    range_start = 20
    range_end = 100
    default = 40


class GoalPerkPercent(Range):
    """Perk-power gate for a mission's confidence goals (from Act 2 on), as a percent of the
    mission's recommended per-slot perks, checked against your best unlocked wizard. Confidence
    goals are harder than just clearing the mission, so this defaults higher. 0 disables it.
    note: lower numbers may be impossible
    """
    display_name = "Confidence Goal Perk %"
    range_start = 60
    range_end = 100
    default = 70


@dataclass
class TBWOptions(PerGameCommonOptions):
    confidence_per_boost: ConfidencePerBoost
    completion_perk_percent: CompletionPerkPercent
    goal_perk_percent: GoalPerkPercent
    death_link: DeathLink
