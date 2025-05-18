# pylint: disable=C0302
"""Components used to model characters."""

from __future__ import annotations

import dataclasses
import enum
from typing import Optional

from ordered_set import OrderedSet

from minerva.ecs import Component, Entity, TagComponent
from minerva.stats.base_types import Stat

FERTILITY_MIN = 0
FERTILITY_MAX = 100
SKILL_MIN = 0
SKILL_MAX = 100
LIFESPAN_MIN = 0

SKILL_EXCELLENT = 85
SKILL_GOOD = 60
SKILL_NEUTRAL = 20
SKILL_BAD = 15
SKILL_TERRIBLE = 0


class LifeStage(enum.IntEnum):
    """All the age ranges characters can pass through."""

    CHILD = 0
    ADOLESCENT = 1
    YOUNG_ADULT = 2
    ADULT = 3
    SENIOR = 4


class Sex(enum.IntEnum):
    """The biological sex of the character."""

    MALE = 0
    FEMALE = 1


class SexualOrientation(enum.IntEnum):
    """Characters sexual preference."""

    HETEROSEXUAL = 0
    HOMOSEXUAL = 1
    BISEXUAL = 2
    ASEXUAL = 3


@dataclasses.dataclass
class Species:
    """Configuration information about a character's species."""

    definition_id: str
    """The unique ID of this species definition."""
    name: str
    """The name of this species."""
    description: str
    """A short text description."""
    adolescent_age: int
    """The age when this species is considered an adolescent."""
    young_adult_age: int
    """The age when this species is considered a young adult."""
    adult_age: int
    """The age when this species is considered an adult."""
    senior_age: int
    """The age when this species is considered a senior."""
    lifespan: tuple[int, int]
    """A lifespan interval for characters of this species."""
    can_physically_age: bool
    """Can characters of this species age."""
    adolescent_male_fertility: int
    """Max fertility for adolescent males."""
    young_adult_male_fertility: int
    """Max fertility for young adult males."""
    adult_male_fertility: int
    """Max fertility for adult males."""
    senior_male_fertility: int
    """Max fertility for senior males."""
    adolescent_female_fertility: int
    """Max fertility for adolescent females."""
    young_adult_female_fertility: int
    """Max fertility for young adult females."""
    adult_female_fertility: int
    """Max fertility for adult females."""
    senior_female_fertility: int
    """Max fertility for senior females."""
    fertility_cost_per_child: int
    """Fertility reduction each time a character births a child."""
    traits: list[str] = dataclasses.field(default_factory=list)  # type: ignore
    """IDs of traits characters of this species get at creation."""
    spawn_frequency: int = 1
    """How likely a character will spawn of this species."""

    def get_max_fertility(self, sex: Sex, life_stage: LifeStage) -> int:
        """Get the max fertility for the given life stage and sex."""
        if life_stage == LifeStage.SENIOR:
            fertility_max = (
                self.senior_male_fertility
                if sex == Sex.MALE
                else self.senior_female_fertility
            )

            return fertility_max

        if life_stage == LifeStage.ADULT:
            fertility_max = (
                self.adult_male_fertility
                if sex == Sex.MALE
                else self.adult_female_fertility
            )
            return fertility_max

        if life_stage == LifeStage.YOUNG_ADULT:
            fertility_max = (
                self.young_adult_male_fertility
                if sex == Sex.MALE
                else self.young_adult_female_fertility
            )

            return fertility_max

        if life_stage == LifeStage.ADOLESCENT:
            fertility_max = (
                self.adolescent_male_fertility
                if sex == Sex.MALE
                else self.adolescent_female_fertility
            )

            return fertility_max

        else:
            return 100

    def get_life_stage_for_age(self, age: int) -> LifeStage:
        """Get the life stage for a character with a given species and age."""

        if age >= self.senior_age:
            return LifeStage.SENIOR
        elif age >= self.adult_age:
            return LifeStage.ADULT
        elif age >= self.young_adult_age:
            return LifeStage.YOUNG_ADULT
        elif age >= self.adolescent_age:
            return LifeStage.ADOLESCENT

        return LifeStage.CHILD


class SpeciesLibrary:
    """Manages species definitions and instances."""

    _slots__ = ("species",)

    species: dict[str, Species]
    """Species instances."""

    def __init__(self) -> None:
        super().__init__()
        self.species = {}

    def add_species(self, species: Species) -> None:
        """Add species to the library."""
        self.species[species.definition_id] = species

    def get_species(self, definition_id: str) -> Species:
        """Get a species instance."""
        return self.species[definition_id]


class Character(Component):
    """A character that inhabits the world."""

    __slots__ = (
        "first_name",
        "surname",
        "birth_surname",
        "sex",
        "sexual_orientation",
        "species",
        "life_stage",
        "age",
        "birth_year",
        "death_year",
        "mother",
        "father",
        "biological_father",
        "siblings",
        "children",
        "grandparents",
        "grandchildren",
        "spouse",
        "marriage",
        "is_alive",
        "family",
        "family_roles",
        "birth_family",
        "heir",
        "heir_to",
        "influence_points",
    )

    first_name: str
    surname: str
    birth_surname: str
    sex: Sex
    sexual_orientation: SexualOrientation
    species: Species
    life_stage: LifeStage
    age: float
    birth_year: Optional[int]
    death_year: Optional[int]
    mother: Optional[Entity]
    father: Optional[Entity]
    biological_father: Optional[Entity]
    siblings: OrderedSet[Entity]
    children: OrderedSet[Entity]
    grandparents: OrderedSet[Entity]
    grandchildren: OrderedSet[Entity]
    spouse: Optional[Entity]
    marriage: Optional[Entity]
    is_alive: bool
    family: Optional[Entity]
    birth_family: Optional[Entity]
    heir: Optional[Entity]
    heir_to: Optional[Entity]
    family_roles: FamilyRoleFlags
    influence_points: int

    def __init__(
        self,
        first_name: str,
        surname: str,
        sex: Sex,
        species: Species,
        birth_surname: str = "",
        sexual_orientation: SexualOrientation = SexualOrientation.HETEROSEXUAL,
        life_stage: LifeStage = LifeStage.CHILD,
        age: float = 0,
    ) -> None:
        super().__init__()
        self.first_name = first_name
        self.surname = surname
        self.birth_surname = birth_surname
        self.sex = sex
        self.sexual_orientation = sexual_orientation
        self.species = species
        self.life_stage = life_stage
        self.age = age
        self.birth_year = None
        self.death_year = None
        self.mother = None
        self.father = None
        self.biological_father = None
        self.siblings = OrderedSet([])
        self.children = OrderedSet([])
        self.grandparents = OrderedSet([])
        self.grandchildren = OrderedSet([])
        self.spouse = None
        self.marriage = None
        self.is_alive = True
        self.family = None
        self.birth_family = None
        self.heir = None
        self.heir_to = None
        self.family_roles = FamilyRoleFlags.NONE
        self.influence_points = 0

    @property
    def full_name(self) -> str:
        """The combined full name of the character."""
        return f"{self.first_name} {self.surname}"


class Pregnancy(Component):
    """Tags a character as pregnant and tracks relevant information."""

    __slots__ = (
        "assumed_father",
        "actual_father",
        "conception_year",
        "due_year",
    )

    assumed_father: Optional[Entity]
    """The character believed to have impregnated this character."""
    actual_father: Entity
    """The character that actually impregnated this character."""
    conception_year: int
    """The date the child was conceived."""
    due_year: int
    """The date the baby is due to be born."""

    def __init__(
        self,
        assumed_father: Optional[Entity],
        actual_father: Entity,
        conception_year: int,
        due_year: int,
    ) -> None:
        super().__init__()
        self.assumed_father = assumed_father
        self.actual_father = actual_father
        self.conception_year = conception_year
        self.due_year = due_year

    def __str__(self) -> str:
        return (
            f"Pregnant("
            f"assumed_father={self.assumed_father.name if self.assumed_father else ''}, "
            f"actual_father={self.actual_father.name}, "
            f"conception_year={self.conception_year}, "
            f"due_year={self.due_year}"
            f")"
        )

    def __repr__(self) -> str:
        return (
            f"Pregnant("
            f"assumed_father={self.assumed_father.name if self.assumed_father else ''}, "
            f"actual_father={self.actual_father.name}, "
            f"conception_year={self.conception_year}, "
            f"due_year={self.due_year}"
            f")"
        )


class Marriage(Component):
    """Marriage information from one character to another.

    Marriages objects are uni-directional. Meaning they only track one side of
    the marriage.
    """

    __slots__ = ("character", "spouse", "start_year")

    character: Entity
    spouse: Entity
    start_year: int

    def __init__(self, character: Entity, spouse: Entity, start_year: int) -> None:
        super().__init__()
        self.character = character
        self.spouse = spouse
        self.start_year = start_year


class FamilyRoleFlags(enum.IntFlag):
    """Roles a character can be appointed to within their family."""

    NONE = 0
    """The character is an ordinary member."""
    WARRIOR = enum.auto()
    """The character is assigned a warrior seat."""
    ADVISOR = enum.auto()
    """The character is assigned an advisor seat."""
    HEAD = enum.auto()
    """The character is the head of their family."""


class FamilyRank(enum.IntEnum):
    """Family rank levels."""

    RANK_1 = 1
    RANK_2 = 2
    RANK_3 = 3
    RANK_4 = 4
    RANK_5 = 5


class Family(Component):
    """A collection of characters joined by blood or marriage."""

    __slots__ = (
        "name",
        "founder",
        "head",
        "rank",
        "former_heads",
        "active_members",
        "former_members",
        "alliance",
        "home_base",
        "controlled_territories",
        "warriors",
        "advisors",
        "color_primary",
        "color_secondary",
        "color_tertiary",
        "banner_symbol",
    )

    name: str
    """The name of the family."""
    founder: Optional[Entity]
    """The character that founded the family."""
    head: Optional[Entity]
    """The character that is currently in charge of the family."""
    rank: FamilyRank
    """The rank of this family."""
    former_heads: OrderedSet[Entity]
    """Former heads of this family."""
    former_members: OrderedSet[Entity]
    """All people who have left the family."""
    alliance: Optional[Entity]
    """The alliance this family belongs to."""
    home_base: Optional[Entity]
    """The territory this family belongs to."""
    controlled_territories: OrderedSet[Entity]
    """The territories this family has control over."""
    active_members: OrderedSet[Entity]
    """Characters actively a part of this family."""
    warriors: OrderedSet[Entity]
    """Characters responsible for strength during wars."""
    advisors: OrderedSet[Entity]
    """Characters responsible for maintaining diplomatic stability."""
    color_primary: str
    """The primary color associated with this family."""
    color_secondary: str
    """The secondary color associated with this family."""
    color_tertiary: str
    """The tertiary color associated with this family."""
    banner_symbol: str
    """The symbol displayed on this family's banner."""

    def __init__(
        self,
        name: str,
        color_primary: str,
        color_secondary: str,
        color_tertiary: str,
        banner_symbol: str,
        rank: FamilyRank = FamilyRank.RANK_1,
    ) -> None:
        super().__init__()
        self.name = name
        self.founder = None
        self.head = None
        self.rank = rank
        self.alliance = None
        self.home_base = None
        self.controlled_territories = OrderedSet([])
        self.active_members = OrderedSet([])
        self.former_members = OrderedSet([])
        self.warriors = OrderedSet([])
        self.advisors = OrderedSet([])
        self.former_heads = OrderedSet([])
        self.color_primary = color_primary
        self.color_secondary = color_secondary
        self.color_tertiary = color_tertiary
        self.banner_symbol = banner_symbol


class HeadOfFamily(Component):
    """Marks a character as being the head of a family."""

    __slots__ = ("family",)

    family: Entity
    """The family they are the head of."""

    def __init__(self, family: Entity) -> None:
        super().__init__()
        self.family = family


class FormerFamilyHead(Component):
    """Marks a character as being a former head of a family."""

    __slots__ = ("family",)

    family: Entity
    """The family they were the head of."""

    def __init__(self, family: Entity) -> None:
        super().__init__()
        self.family = family


class Ruler(TagComponent):
    """Tags the character as the ruler of the land."""


class Dynasty(Component):
    """Information about a dynasty."""

    __slots__ = (
        "founder",
        "family",
        "founding_year",
        "current_ruler",
        "previous_rulers",
        "ending_year",
        "previous_dynasty",
    )

    founder: Entity
    family: Entity
    founding_year: int
    current_ruler: Optional[Entity]
    previous_rulers: OrderedSet[Entity]
    ending_year: Optional[int]
    previous_dynasty: Optional[Entity]

    def __init__(
        self,
        founder: Entity,
        family: Entity,
        founding_year: int,
        previous_dynasty: Optional[Entity] = None,
    ) -> None:
        super().__init__()
        self.founder = founder
        self.family = family
        self.founding_year = founding_year
        self.current_ruler = None
        self.previous_rulers = OrderedSet([])
        self.ending_year = None
        self.previous_dynasty = previous_dynasty

    @property
    def last_ruler(self) -> Optional[Entity]:
        """Get the last ruler of the dynasty."""
        if self.previous_rulers:
            return self.previous_rulers[-1]
        return None


class DynastyTracker:
    """A shared singleton that tracks the current royal family and dynasty."""

    __slots__ = ("current_dynasty", "previous_dynasties", "all_rulers")

    current_dynasty: Optional[Entity]
    previous_dynasties: OrderedSet[Entity]
    all_rulers: OrderedSet[Entity]

    def __init__(self) -> None:
        self.current_dynasty = None
        self.previous_dynasties = OrderedSet([])
        self.all_rulers = OrderedSet([])

    @property
    def last_ruler(self) -> Optional[Entity]:
        """Get a reference to the last character that ruled."""
        if self.all_rulers:
            return self.all_rulers[-1]

        return None

    @property
    def last_dynasty(self) -> Optional[Entity]:
        """Get the previous dynasty."""
        if self.previous_dynasties:
            return self.previous_dynasties[-1]

        return None


class CharacterStat(enum.IntEnum):
    """Enums for each stat associated with characters."""

    LIFESPAN = enum.auto()
    FERTILITY = enum.auto()
    STEWARDSHIP = enum.auto()
    MARTIAL = enum.auto()
    INTRIGUE = enum.auto()
    PROWESS = enum.auto()
    DIPLOMACY = enum.auto()
    LUCK = enum.auto()


class Lifespan(Stat):
    """Tracks an entity's lifespan."""


class Fertility(Stat):
    """Tracks an entity's fertility."""


class Stewardship(Stat):
    """Tracks an entity's stewardship."""


class Martial(Stat):
    """Tracks an entity's martial."""


class Intrigue(Stat):
    """Tracks an entity's intrigue."""


class Prowess(Stat):
    """Tracks an entity's prowess."""


class Diplomacy(Stat):
    """Tracks an entity's diplomacy stat."""


class Luck(Stat):
    """Tracks an entity's propensity to be successful."""


class Prestige(Stat):
    """Tracks the prestige level of a family."""

    def __init__(self, base_value: int = 0) -> None:
        super().__init__(base_value, 0, 100)
