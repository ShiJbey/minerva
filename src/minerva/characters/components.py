# pylint: disable=C0302
"""Components used to model characters."""

from __future__ import annotations

import dataclasses
import enum
from typing import Optional

from ordered_set import OrderedSet

from minerva.datetime import SimDate
from minerva.ecs import Component, Entity, TagComponent
from minerva.stats.base_types import IStatCalculationStrategy, StatComponent


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
    traits: list[str] = dataclasses.field(default_factory=list)
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


class RelationType(enum.Enum):
    """Describes how two characters are related."""

    MOTHER = enum.auto()
    FATHER = enum.auto()
    BIOLOGICAL_FATHER = enum.auto()
    SIBLING = enum.auto()
    CHILD = enum.auto()
    GRANDPARENT = enum.auto()
    GRANDCHILD = enum.auto()
    SPOUSE = enum.auto()
    EX_SPOUSE = enum.auto()
    BETROTHED = enum.auto()
    LOVER = enum.auto()
    HEIR = enum.auto()
    HEIR_TO = enum.auto()


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
        "birth_date",
        "death_date",
        "mother",
        "father",
        "biological_father",
        "siblings",
        "children",
        "grandparents",
        "grandchildren",
        "spouse",
        "former_spouses",
        "marriage",
        "past_marriages",
        "betrothed_to",
        "betrothal",
        "past_betrothals",
        "love_affair",
        "past_love_affairs",
        "lover",
        "is_alive",
        "family",
        "family_roles",
        "birth_family",
        "heir",
        "heir_to",
        "influence_points",
        "killed_by",
    )

    first_name: str
    surname: str
    birth_surname: str
    sex: Sex
    sexual_orientation: SexualOrientation
    species: Species
    life_stage: LifeStage
    age: float
    birth_date: Optional[SimDate]
    death_date: Optional[SimDate]
    mother: Optional[Entity]
    father: Optional[Entity]
    biological_father: Optional[Entity]
    siblings: OrderedSet[Entity]
    children: OrderedSet[Entity]
    grandparents: OrderedSet[Entity]
    grandchildren: OrderedSet[Entity]
    spouse: Optional[Entity]
    former_spouses: OrderedSet[Entity]
    marriage: Optional[Entity]
    past_marriages: OrderedSet[Entity]
    betrothed_to: Optional[Entity]
    betrothal: Optional[Entity]
    past_betrothals: OrderedSet[Entity]
    love_affair: Optional[Entity]
    past_love_affairs: OrderedSet[Entity]
    lover: Optional[Entity]
    is_alive: bool
    family: Optional[Entity]
    birth_family: Optional[Entity]
    heir: Optional[Entity]
    heir_to: Optional[Entity]
    family_roles: FamilyRoleFlags
    influence_points: int
    killed_by: Optional[Entity]

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
        self.birth_date = None
        self.death_date = None
        self.mother = None
        self.father = None
        self.biological_father = None
        self.siblings = OrderedSet([])
        self.children = OrderedSet([])
        self.grandparents = OrderedSet([])
        self.grandchildren = OrderedSet([])
        self.spouse = None
        self.former_spouses = OrderedSet([])
        self.marriage = None
        self.past_marriages = OrderedSet([])
        self.betrothed_to = None
        self.betrothal = None
        self.past_betrothals = OrderedSet([])
        self.love_affair = None
        self.past_love_affairs = OrderedSet([])
        self.lover = None
        self.is_alive = True
        self.family = None
        self.birth_family = None
        self.heir = None
        self.heir_to = None
        self.family_roles = FamilyRoleFlags.NONE
        self.influence_points = 0
        self.killed_by = None

    @property
    def full_name(self) -> str:
        """The combined full name of the character."""
        return f"{self.first_name} {self.surname}"


class Pregnancy(Component):
    """Tags a character as pregnant and tracks relevant information."""

    __slots__ = (
        "assumed_father",
        "actual_father",
        "conception_date",
        "due_date",
    )

    assumed_father: Optional[Entity]
    """The character believed to have impregnated this character."""
    actual_father: Entity
    """The character that actually impregnated this character."""
    conception_date: SimDate
    """The date the child was conceived."""
    due_date: SimDate
    """The date the baby is due to be born."""

    def __init__(
        self,
        assumed_father: Optional[Entity],
        actual_father: Entity,
        conception_date: SimDate,
        due_date: SimDate,
    ) -> None:
        super().__init__()
        self.assumed_father = assumed_father
        self.actual_father = actual_father
        self.conception_date = conception_date
        self.due_date = due_date.copy()

    def __str__(self) -> str:
        return (
            f"Pregnant("
            f"assumed_father={self.assumed_father.name if self.assumed_father else ''}, "
            f"actual_father={self.actual_father.name}, "
            f"conception_date={self.conception_date}, "
            f"due_date={self.due_date}"
            f")"
        )

    def __repr__(self) -> str:
        return (
            f"Pregnant("
            f"assumed_father={self.assumed_father.name if self.assumed_father else ''}, "
            f"actual_father={self.actual_father.name}, "
            f"conception_date={self.conception_date}, "
            f"due_date={self.due_date}"
            f")"
        )


class Betrothal(Component):
    """Information about one character betrothal to another."""

    __slots__ = ("character", "betrothed", "start_date")

    character: Entity
    betrothed: Entity
    start_date: SimDate

    def __init__(
        self, character: Entity, betrothed: Entity, start_date: SimDate
    ) -> None:
        super().__init__()
        self.character = character
        self.betrothed = betrothed
        self.start_date = start_date.copy()


class Marriage(Component):
    """Marriage information from one character to another.

    Marriages objects are uni-directional. Meaning they only track one side of
    the marriage.
    """

    __slots__ = ("character", "spouse", "start_date")

    character: Entity
    spouse: Entity
    start_date: SimDate

    def __init__(self, character: Entity, spouse: Entity, start_date: SimDate) -> None:
        super().__init__()
        self.character = character
        self.spouse = spouse
        self.start_date = start_date.copy()


class RomanticAffair(Component):
    """Information about a character's lover.

    This tracks information about a lover relationship from a single character's POV.
    """

    __slots__ = ("character", "lover", "start_date")

    character: Entity
    lover: Entity
    start_date: SimDate

    def __init__(self, character: Entity, lover: Entity, start_date: SimDate) -> None:
        super().__init__()
        self.character = character
        self.lover = lover
        self.start_date = start_date


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


class Family(Component):
    """A collection of characters joined by blood or marriage."""

    __slots__ = (
        "name",
        "founder",
        "parent_family",
        "branch_families",
        "head",
        "former_heads",
        "active_members",
        "former_members",
        "alliance",
        "home_base",
        "territories_present_in",
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
    parent_family: Optional[Entity]
    """The family that this family branched from."""
    branch_families: OrderedSet[Entity]
    """Branches of this family."""
    head: Optional[Entity]
    """The character that is currently in charge of the family."""
    former_heads: OrderedSet[Entity]
    """Former heads of this family."""
    former_members: OrderedSet[Entity]
    """All people who have left the family."""
    alliance: Optional[Entity]
    """The alliance this family belongs to."""
    home_base: Optional[Entity]
    """The territory this family belongs to."""
    territories_present_in: OrderedSet[Entity]
    """The territories this family has any political influence in."""
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
    ) -> None:
        super().__init__()
        self.name = name
        self.founder = None
        self.parent_family = None
        self.branch_families = OrderedSet([])
        self.head = None
        self.alliance = None
        self.home_base = None
        self.territories_present_in = OrderedSet([])
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
        "_founding_date",
        "current_ruler",
        "previous_rulers",
        "_ending_date",
        "previous_dynasty",
    )

    founder: Entity
    family: Entity
    _founding_date: SimDate
    current_ruler: Optional[Entity]
    previous_rulers: OrderedSet[Entity]
    _ending_date: Optional[SimDate]
    previous_dynasty: Optional[Entity]

    def __init__(
        self,
        founder: Entity,
        family: Entity,
        founding_date: SimDate,
        previous_dynasty: Optional[Entity] = None,
    ) -> None:
        super().__init__()
        self.founder = founder
        self.family = family
        self._founding_date = founding_date.copy()
        self.current_ruler = None
        self.previous_rulers = OrderedSet([])
        self._ending_date = None
        self.previous_dynasty = previous_dynasty

    @property
    def founding_date(self) -> SimDate:
        """The date the dynasty was founded."""
        return self._founding_date

    @founding_date.setter
    def founding_date(self, value: SimDate) -> None:
        """Set the founding date."""
        self._founding_date = value.copy()

    @property
    def ending_date(self) -> Optional[SimDate]:
        """The date the dynasty ended."""
        return self._ending_date

    @ending_date.setter
    def ending_date(self, value: SimDate) -> None:
        """Set the ending date."""
        self._ending_date = value.copy()

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


class Lifespan(StatComponent):
    """Tracks an entity's lifespan."""

    def __init__(
        self,
        calculation_strategy: IStatCalculationStrategy,
        base_value: float = 0,
    ) -> None:
        super().__init__(calculation_strategy, base_value, (0, 999_999), True)


class Fertility(StatComponent):
    """Tracks an entity's fertility."""

    MAX_VALUE: int = 100

    def __init__(
        self,
        calculation_strategy: IStatCalculationStrategy,
        base_value: float = 0,
    ) -> None:
        super().__init__(calculation_strategy, base_value, (0, self.MAX_VALUE), True)


class Stewardship(StatComponent):
    """Tracks an entity's stewardship."""

    MAX_VALUE: int = 100

    def __init__(
        self,
        calculation_strategy: IStatCalculationStrategy,
        base_value: float = 0,
    ) -> None:
        super().__init__(calculation_strategy, base_value, (0, self.MAX_VALUE), True)


class Martial(StatComponent):
    """Tracks an entity's martial."""

    MAX_VALUE: int = 100

    def __init__(
        self,
        calculation_strategy: IStatCalculationStrategy,
        base_value: float = 0,
    ) -> None:
        super().__init__(calculation_strategy, base_value, (0, self.MAX_VALUE), True)


class Intrigue(StatComponent):
    """Tracks an entity's intrigue."""

    MAX_VALUE: int = 100

    def __init__(
        self,
        calculation_strategy: IStatCalculationStrategy,
        base_value: float = 0,
    ) -> None:
        super().__init__(calculation_strategy, base_value, (0, self.MAX_VALUE), True)


class Intelligence(StatComponent):
    """Tracks a character's intelligence stat."""

    MAX_VALUE: int = 100

    def __init__(
        self,
        calculation_strategy: IStatCalculationStrategy,
        base_value: float = 0,
    ) -> None:
        super().__init__(calculation_strategy, base_value, (0, self.MAX_VALUE), True)


class Prowess(StatComponent):
    """Tracks an entityprowess."""

    MAX_VALUE: int = 100

    def __init__(
        self,
        calculation_strategy: IStatCalculationStrategy,
        base_value: float = 0,
    ) -> None:
        super().__init__(calculation_strategy, base_value, (0, self.MAX_VALUE), True)


class Sociability(StatComponent):
    """Tracks an entity's sociability."""

    MAX_VALUE: int = 100

    def __init__(
        self,
        calculation_strategy: IStatCalculationStrategy,
        base_value: float = 0,
    ) -> None:
        super().__init__(calculation_strategy, base_value, (0, self.MAX_VALUE), True)


class Honor(StatComponent):
    """Tracks an entityhonor."""

    MAX_VALUE: int = 100

    def __init__(
        self,
        calculation_strategy: IStatCalculationStrategy,
        base_value: float = 0,
    ) -> None:
        super().__init__(calculation_strategy, base_value, (0, self.MAX_VALUE), True)


class Boldness(StatComponent):
    """Tracks an entity's boldness."""

    MAX_VALUE: int = 100

    def __init__(
        self,
        calculation_strategy: IStatCalculationStrategy,
        base_value: float = 0,
    ) -> None:
        super().__init__(calculation_strategy, base_value, (0, self.MAX_VALUE), True)


class Compassion(StatComponent):
    """Tracks an entity's compassion."""

    MAX_VALUE: int = 100

    def __init__(
        self,
        calculation_strategy: IStatCalculationStrategy,
        base_value: float = 0,
    ) -> None:
        super().__init__(calculation_strategy, base_value, (0, self.MAX_VALUE), True)


class Diplomacy(StatComponent):
    """Tracks an entitydiplomacy."""

    MAX_VALUE: int = 100

    def __init__(
        self,
        calculation_strategy: IStatCalculationStrategy,
        base_value: float = 0,
    ) -> None:
        super().__init__(calculation_strategy, base_value, (0, self.MAX_VALUE), True)


class Greed(StatComponent):
    """Tracks an entity's greed."""

    MAX_VALUE: int = 100

    def __init__(
        self,
        calculation_strategy: IStatCalculationStrategy,
        base_value: float = 0,
    ) -> None:
        super().__init__(calculation_strategy, base_value, (0, self.MAX_VALUE), True)


class Rationality(StatComponent):
    """Tracks an entity's rationality."""

    MAX_VALUE: int = 100

    def __init__(
        self,
        calculation_strategy: IStatCalculationStrategy,
        base_value: float = 0,
    ) -> None:
        super().__init__(calculation_strategy, base_value, (0, self.MAX_VALUE), True)


class Vengefulness(StatComponent):
    """Tracks an entity's vengefulness."""

    MAX_VALUE: int = 100

    def __init__(
        self,
        calculation_strategy: IStatCalculationStrategy,
        base_value: float = 0,
    ) -> None:
        super().__init__(calculation_strategy, base_value, (0, self.MAX_VALUE), True)


class RomancePropensity(StatComponent):
    """Tracks an entity's propensity for romantic actions."""

    MAX_VALUE: int = 100

    def __init__(
        self,
        calculation_strategy: IStatCalculationStrategy,
        base_value: float = 0,
    ) -> None:
        super().__init__(calculation_strategy, base_value, (0, self.MAX_VALUE), True)


class Luck(StatComponent):
    """Tracks an entity's propensity to be successful."""

    MAX_VALUE: int = 100

    def __init__(
        self,
        calculation_strategy: IStatCalculationStrategy,
        base_value: float = 0,
    ) -> None:
        super().__init__(calculation_strategy, base_value, (0, self.MAX_VALUE), True)


class FamilyPrestige(StatComponent):
    """Tracks the prestige level of a family."""

    MAX_VALUE = 999_999

    def __init__(
        self,
        calculation_strategy: IStatCalculationStrategy,
        base_value: float = 0,
    ) -> None:
        super().__init__(calculation_strategy, base_value, (0, self.MAX_VALUE), True)
