"""War Casualty Mechanic Test.

This script contains prototype code for how casualties would bw calculated at the
conclusion of a war. I think the best way to handle it might be weighted random
selection on the union set of all warriors for each side (one set for the offense,
another for the defense).

- In 1v1 scenarios, casualties happen evenly on both sides, with each characters,
  likelihood of surviving calculated independently.
- In 2v1 scenarios, ...

How likely is someone to die?
-----------------------------

The probability of a character dying as a casualty of war is based on their standard
deviation from the mean prowess (combat) skill level.
- prowess < -2 std dev:  80% chance
- -2 <= prowess < -1:    40%
- -1 <= prowess < 0:     25%
- 0 <= prowess < 1:      12%
- 1 <= prowess < 2:      10%
- prowess > 2:            0%

We then add an additional boost to the death probability based on if they were on the
losing side of the war. We could also add additional modifiers to the probability for
characters with high intelligence or high stewardship skills. This would help non-combat-
oriented family heads to still maintain some chance of minimizing their loss in war.
We could also add a (0.6 * intelligence) boost to their score when calculating their
probability of winning the war. Highly intelligent characters should be able to
defeat those with power and little intelligence.

When alliances are involved, the same criteria applies. However, the scores for each
side are the summed combat scores of each family. Then we apply boosts for
intelligence and stewardship greater than 0 and penalties for values below 0

For Intelligence:
- [0 - 10] => -40% points  (Low intelligence)
- [11 - 30] => -10% points
- [50 - 90] => +10% points
- [91 - 100] => +40% points

Stewardship buffs are only applied when an alliance is involved. The stewardship skill
of the war aggressors council. So, if an alliance has five or more members, the
following penalities are applied to the final combat score:

- [0 - 10] => -50%
- [11 - 20] => -40%
- [21 - 49] => -25%

How does luck play into this?
-----------------------------

Characters with high amount of luck can get boosts added to their probability of winning
after all the combat scoring above. This is balanced out with any luck that the opponent
has. So if they are both lucky, then nobody is lucky

- Luck [0 - 10] => -10%
- Luck [90 - 10] => +10%
"""

import enum
import random
import statistics
from dataclasses import dataclass, field

EXCELLENT_STAT_THRESHOLD = 85
GOOD_STAT_THRESHOLD = 20
NEUTRAL_STAT_THRESHOLD = -20
BAD_STAT_THRESHOLD = 15


class StatLevel(enum.Enum):
    """A general interval for a stat."""

    TERRIBLE = enum.auto()
    BAD = enum.auto()
    NEUTRAL = enum.auto()
    GOOD = enum.auto()
    EXCELLENT = enum.auto()


@dataclass
class SimpleCharacter:
    """Represents a simplified character."""

    name: str
    intelligence: int = field(default_factory=lambda: random.randint(0, 100))
    stewardship: int = field(default_factory=lambda: random.randint(0, 100))
    martial: int = field(default_factory=lambda: random.randint(0, 100))
    prowess: int = field(default_factory=lambda: random.randint(0, 100))
    luck: int = field(default_factory=lambda: random.randint(0, 100))


def get_intelligence_level(character: SimpleCharacter) -> StatLevel:
    """Get the stat level for a character's intelligence stat."""
    stat_value = character.intelligence

    if stat_value >= EXCELLENT_STAT_THRESHOLD:
        return StatLevel.EXCELLENT
    elif stat_value >= GOOD_STAT_THRESHOLD:
        return StatLevel.GOOD
    elif stat_value >= NEUTRAL_STAT_THRESHOLD:
        return StatLevel.NEUTRAL
    elif stat_value >= BAD_STAT_THRESHOLD:
        return StatLevel.BAD
    else:
        return StatLevel.TERRIBLE


def get_stewardship_level(character: SimpleCharacter) -> StatLevel:
    """Get the stat level for a character's stewardship stat."""
    stat_value = character.stewardship

    if stat_value >= EXCELLENT_STAT_THRESHOLD:
        return StatLevel.EXCELLENT
    elif stat_value >= GOOD_STAT_THRESHOLD:
        return StatLevel.GOOD
    elif stat_value >= NEUTRAL_STAT_THRESHOLD:
        return StatLevel.NEUTRAL
    elif stat_value >= BAD_STAT_THRESHOLD:
        return StatLevel.BAD
    else:
        return StatLevel.TERRIBLE


def get_martial_level(character: SimpleCharacter) -> StatLevel:
    """Get the stat level for a character's martial stat."""
    stat_value = character.martial

    if stat_value >= EXCELLENT_STAT_THRESHOLD:
        return StatLevel.EXCELLENT
    elif stat_value >= GOOD_STAT_THRESHOLD:
        return StatLevel.GOOD
    elif stat_value >= NEUTRAL_STAT_THRESHOLD:
        return StatLevel.NEUTRAL
    elif stat_value >= BAD_STAT_THRESHOLD:
        return StatLevel.BAD
    else:
        return StatLevel.TERRIBLE


def get_luck_level(character: SimpleCharacter) -> StatLevel:
    """Get the stat level for a character's luck stat."""
    stat_value = character.luck

    if stat_value >= EXCELLENT_STAT_THRESHOLD:
        return StatLevel.EXCELLENT
    elif stat_value >= GOOD_STAT_THRESHOLD:
        return StatLevel.GOOD
    elif stat_value >= NEUTRAL_STAT_THRESHOLD:
        return StatLevel.NEUTRAL
    elif stat_value >= BAD_STAT_THRESHOLD:
        return StatLevel.BAD
    else:
        return StatLevel.TERRIBLE


def get_prowess_level(character: SimpleCharacter) -> StatLevel:
    """Get the stat level for a character's prowess stat."""
    stat_value = character.prowess

    if stat_value >= EXCELLENT_STAT_THRESHOLD:
        return StatLevel.EXCELLENT
    elif stat_value >= GOOD_STAT_THRESHOLD:
        return StatLevel.GOOD
    elif stat_value >= NEUTRAL_STAT_THRESHOLD:
        return StatLevel.NEUTRAL
    elif stat_value >= BAD_STAT_THRESHOLD:
        return StatLevel.BAD
    else:
        return StatLevel.TERRIBLE


@dataclass
class SimpleFamily:
    """Represents a simplified family."""

    name: str
    head: SimpleCharacter
    warriors: list[SimpleCharacter]
    advisors: list[SimpleCharacter]


@dataclass
class SimpleWar:
    """A simplified war representation."""

    aggressor: SimpleFamily
    defender: SimpleFamily
    aggressor_allies: list[SimpleFamily]
    defender_allies: list[SimpleFamily]


def calculate_warrior_prowess_dist(war: SimpleWar) -> tuple[float, float]:
    """Calculate the mean and std deviation of prowess scores for all warriors."""
    prowess_scores: list[int] = []

    for warrior in war.aggressor.warriors:
        prowess_scores.append(warrior.prowess)

    for warrior in war.defender.warriors:
        prowess_scores.append(warrior.prowess)

    for family in war.aggressor_allies:
        for warrior in family.warriors:
            prowess_scores.append(warrior.prowess)

    for family in war.defender_allies:
        for warrior in family.warriors:
            prowess_scores.append(warrior.prowess)

    score_mean = statistics.mean(prowess_scores)
    score_stdev = statistics.stdev(prowess_scores)

    return score_mean, score_stdev


def calculate_war_score(lead_family: SimpleFamily, allies: list[SimpleFamily]) -> int:
    """Calculate a strength score for a family and their allies in a war."""

    total_prowess: int = 0

    for warrior in lead_family.warriors:
        total_prowess += warrior.prowess

    for family in allies:
        for warrior in family.warriors:
            total_prowess += warrior.prowess

    final_score = total_prowess

    # Apply changes for lead family head martial skill
    martial_skill_level = get_martial_level(lead_family.head)

    if martial_skill_level == StatLevel.TERRIBLE:
        final_score = final_score * 0.6  # Final score - 40%

    elif martial_skill_level == StatLevel.BAD:
        final_score = final_score * 0.9  # Final score - 10%

    elif martial_skill_level == StatLevel.GOOD:
        final_score = final_score * 1.1  # Final score + 10%

    elif martial_skill_level == StatLevel.EXCELLENT:
        final_score = final_score * 1.4  # Final score + 40%

    # Apply changes for lead family head stewardship
    if allies:
        stewardship_skill_level = get_stewardship_level(lead_family.head)

        if stewardship_skill_level == StatLevel.TERRIBLE:
            final_score = final_score * 0.5  # Final score - 50%
        elif stewardship_skill_level == StatLevel.BAD:
            final_score = final_score * 0.6  # Final score - 40%

    return int(final_score)


def calculate_aggressor_win_probability(
    aggressor_score: int, defender_score: float
) -> float:
    """Return the probability of the aggressor defeating the defender."""
    return aggressor_score / (aggressor_score + defender_score)


def get_casualty_chance(
    prowess_mean: float, prowess_stdev: float, prowess: int
) -> float:
    """Get the probability of a character dying in a war."""

    normalized_prowess = (float(prowess) - prowess_mean) / (prowess_stdev + 1e-10)

    if normalized_prowess >= 2:
        return 0.0
    elif normalized_prowess >= 1:
        return 0.1
    elif normalized_prowess >= 0:
        return 0.12
    elif normalized_prowess >= -1:
        return 0.25
    elif normalized_prowess >= -2:
        return 0.4
    else:
        return 0.8


def simulate_war(war: SimpleWar) -> None:
    """Simulate a war between families."""

    prowess_mean, prowess_stdev = calculate_warrior_prowess_dist(war)
    aggressor_score = calculate_war_score(war.aggressor, war.aggressor_allies)
    defender_score = calculate_war_score(war.defender, war.defender_allies)
    base_aggressor_win_probability = calculate_aggressor_win_probability(
        aggressor_score, defender_score
    )
    aggressor_win_probability = base_aggressor_win_probability

    # Adjust win probability based on aggressor luck
    aggressor_luck_level = get_luck_level(war.aggressor.head)
    if aggressor_luck_level == StatLevel.TERRIBLE:
        aggressor_win_probability -= 0.1
    elif aggressor_luck_level == StatLevel.EXCELLENT:
        aggressor_win_probability += 0.1

    # Adjust win probability based on defender luck
    defender_luck_level = get_luck_level(war.defender.head)
    if defender_luck_level == StatLevel.TERRIBLE:
        aggressor_win_probability += 0.1
    elif defender_luck_level == StatLevel.EXCELLENT:
        aggressor_win_probability -= 0.1

    # Random roll to see who wins
    if random.random() < aggressor_win_probability:
        winner = war.aggressor
        winner_allies = war.aggressor_allies
        loser = war.defender
        loser_allies = war.defender_allies
    else:
        winner = war.defender
        winner_allies = war.defender_allies
        loser = war.aggressor
        loser_allies = war.aggressor_allies

    # Determine casualties
    casualties: list[tuple[SimpleCharacter, int, SimpleFamily]] = []

    for warrior in winner.warriors:
        casualty_chance = get_casualty_chance(
            prowess_mean, prowess_stdev, warrior.prowess
        )

        # Adjust Casualty Chance based on luck
        warrior_luck_level = get_luck_level(warrior)
        if warrior_luck_level == StatLevel.TERRIBLE:
            casualty_chance += 0.1
        elif warrior_luck_level == StatLevel.EXCELLENT:
            casualty_chance -= 0.1

        # Roll for casualty
        if random.random() < casualty_chance:
            casualties.append((warrior, warrior.prowess, winner))

    for family in winner_allies:
        for warrior in family.warriors:
            casualty_chance = get_casualty_chance(
                prowess_mean, prowess_stdev, warrior.prowess
            )

            # Adjust Casualty Chance based on luck
            warrior_luck_level = get_luck_level(warrior)
            if warrior_luck_level == StatLevel.TERRIBLE:
                casualty_chance += 0.1
            elif warrior_luck_level == StatLevel.EXCELLENT:
                casualty_chance -= 0.1

            # Roll for casualty
            if random.random() < casualty_chance:
                casualties.append((warrior, warrior.prowess, family))

    for warrior in loser.warriors:
        casualty_chance = get_casualty_chance(
            prowess_mean, prowess_stdev, warrior.prowess
        )

        # Adjust because they lost
        casualty_chance += 0.15

        # Adjust Casualty Chance based on luck
        warrior_luck_level = get_luck_level(warrior)
        if warrior_luck_level == StatLevel.TERRIBLE:
            casualty_chance += 0.1
        elif warrior_luck_level == StatLevel.EXCELLENT:
            casualty_chance -= 0.1

        # Roll for casualty
        if random.random() < casualty_chance:
            casualties.append((warrior, warrior.prowess, loser))

    for family in loser_allies:
        for warrior in family.warriors:
            casualty_chance = get_casualty_chance(
                prowess_mean, prowess_stdev, warrior.prowess
            )

            # Adjust because they lost
            casualty_chance += 0.15

            # Adjust Casualty Chance based on luck
            warrior_luck_level = get_luck_level(warrior)
            if warrior_luck_level == StatLevel.TERRIBLE:
                casualty_chance += 0.1
            elif warrior_luck_level == StatLevel.EXCELLENT:
                casualty_chance -= 0.1

            # Roll for casualty
            if random.random() < casualty_chance:
                casualties.append((warrior, warrior.prowess, family))

    print("-------")
    print(f"Simulated war Between {war.aggressor.name} and {war.defender.name}.")
    print(f"Aggressor Allies: {', '.join(x.name for x in war.aggressor_allies)}")
    print(f"Defender Allies: {', '.join(x.name for x in war.defender_allies)}")
    print(f"Prowess Stats: mean={prowess_mean}, stdev={prowess_stdev}")
    print(f"Aggressor War Score: {aggressor_score}")
    print(f"Defender War Score: {defender_score}")
    print(f"Base Aggressor Win Probability: {base_aggressor_win_probability}")
    print(f"Final Aggressor Win Probability: {aggressor_win_probability}")
    print(f"Winner: {winner.name}")
    print(f"Loser: {loser.name}")
    print("Casualties:")
    for entry in casualties:
        print(f"- {entry[0].name} from {entry[2].name} (Prowess: {entry[1]})")
    print("=======")


def main():
    """main function."""

    # Create characters
    character_a = SimpleCharacter(name="A")
    character_b = SimpleCharacter(name="B")
    character_c = SimpleCharacter(name="C")
    character_d = SimpleCharacter(name="D")
    character_e = SimpleCharacter(name="E")
    character_f = SimpleCharacter(name="F")
    character_g = SimpleCharacter(name="G")
    character_h = SimpleCharacter(name="H")
    character_i = SimpleCharacter(name="I")
    character_j = SimpleCharacter(name="J")
    character_k = SimpleCharacter(name="K")
    character_l = SimpleCharacter(name="L")
    character_m = SimpleCharacter(name="M")

    # Create Families
    family_a = SimpleFamily(
        name="Family A",
        head=character_a,
        warriors=[character_b, character_c],
        advisors=[character_b],
    )

    family_d = SimpleFamily(
        name="Family D",
        head=character_d,
        warriors=[character_d, character_e, character_f],
        advisors=[character_f],
    )

    family_g = SimpleFamily(
        name="Family G",
        head=character_g,
        warriors=[character_g],
        advisors=[character_h, character_i],
    )

    family_j = SimpleFamily(
        name="Family J",
        head=character_j,
        warriors=[character_k, character_l, character_m],
        advisors=[character_k, character_m],
    )

    # Simulate War Scenarios
    simulate_war(
        SimpleWar(
            aggressor=family_a,
            defender=family_d,
            aggressor_allies=[],
            defender_allies=[],
        )
    )

    simulate_war(
        SimpleWar(
            aggressor=family_a,
            defender=family_g,
            aggressor_allies=[],
            defender_allies=[],
        )
    )

    simulate_war(
        SimpleWar(
            aggressor=family_a,
            defender=family_d,
            aggressor_allies=[family_g],
            defender_allies=[family_j],
        )
    )

    simulate_war(
        SimpleWar(
            aggressor=family_a,
            defender=family_d,
            aggressor_allies=[family_g, family_j],
            defender_allies=[],
        )
    )

    simulate_war(
        SimpleWar(
            aggressor=family_a,
            defender=family_d,
            aggressor_allies=[],
            defender_allies=[family_g, family_j],
        )
    )


if __name__ == "__main__":
    main()
