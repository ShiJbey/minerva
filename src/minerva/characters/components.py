# pylint: disable=C0302
"""Components used to model characters."""

from __future__ import annotations

import enum
from typing import Optional

import pydantic
from ordered_set import OrderedSet

from minerva import constants
from minerva.constants import CHARACTER_MOTIVE_BASE, CHARACTER_MOTIVE_MAX
from minerva.datetime import SimDate
from minerva.ecs import Component, GameObject, TagComponent
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


class SpeciesType(pydantic.BaseModel):
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
    traits: list[str] = pydantic.Field(default_factory=list)
    """IDs of traits characters of this species get at creation."""
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
    spawn_frequency: int = 1
    """How likely a character will spawn of this species."""

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

    species: dict[str, SpeciesType]
    """Species instances."""

    def __init__(self) -> None:
        super().__init__()
        self.species = {}

    def add_species(self, species: SpeciesType) -> None:
        """Add species to the library."""
        self.species[species.definition_id] = species

    def get_species(self, definition_id: str) -> SpeciesType:
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
        "birth_date",
        "death_date",
        "mother",
        "father",
        "biological_father",
        "siblings",
        "children",
        "spouse",
        "lover",
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
    species: SpeciesType
    life_stage: LifeStage
    age: float
    birth_date: Optional[SimDate]
    death_date: Optional[SimDate]
    mother: Optional[GameObject]
    father: Optional[GameObject]
    biological_father: Optional[GameObject]
    siblings: list[GameObject]
    children: list[GameObject]
    spouse: Optional[GameObject]
    lover: Optional[GameObject]
    is_alive: bool
    family: Optional[GameObject]
    birth_family: Optional[GameObject]
    heir: Optional[GameObject]
    heir_to: Optional[GameObject]
    family_roles: FamilyRoleFlags
    influence_points: int

    def __init__(
        self,
        first_name: str,
        surname: str,
        sex: Sex,
        species: SpeciesType,
        birth_surname: str = "",
        sexual_orientation: SexualOrientation = SexualOrientation.HETEROSEXUAL,
        life_stage: LifeStage = LifeStage.CHILD,
        age: float = 0,
        birth_date: Optional[SimDate] = None,
        death_date: Optional[SimDate] = None,
        mother: Optional[GameObject] = None,
        father: Optional[GameObject] = None,
        biological_father: Optional[GameObject] = None,
        siblings: Optional[list[GameObject]] = None,
        spouse: Optional[GameObject] = None,
        lover: Optional[GameObject] = None,
        is_alive: bool = True,
        family: Optional[GameObject] = None,
        birth_family: Optional[GameObject] = None,
        heir: Optional[GameObject] = None,
        heir_to: Optional[GameObject] = None,
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
        self.birth_date = birth_date
        self.death_date = death_date
        self.mother = mother
        self.father = father
        self.biological_father = biological_father
        self.siblings = siblings if siblings is not None else []
        self.children = []
        self.spouse = spouse
        self.lover = lover
        self.is_alive = is_alive
        self.family = family
        self.birth_family = birth_family
        self.heir = heir
        self.heir_to = heir_to
        self.family_roles = FamilyRoleFlags.NONE
        self.influence_points = constants.INFLUENCE_POINTS_BASE

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

    assumed_father: Optional[GameObject]
    """The character believed to have impregnated this character."""
    actual_father: GameObject
    """The character that actually impregnated this character."""
    conception_date: SimDate
    """The date the child was conceived."""
    due_date: SimDate
    """The date the baby is due to be born."""

    def __init__(
        self,
        assumed_father: Optional[GameObject],
        actual_father: GameObject,
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


class Marriage(Component):
    """Marriage information from one character to another.

    Marriages objects are uni-directional. Meaning they only track one side of
    the marriage.
    """

    __slots__ = ("character", "spouse", "start_date")

    character: GameObject
    spouse: GameObject
    start_date: SimDate

    def __init__(
        self, character: GameObject, spouse: GameObject, start_date: SimDate
    ) -> None:
        super().__init__()
        self.character = character
        self.spouse = spouse
        self.start_date = start_date.copy()


class MarriageTracker(Component):
    """Tracks a character's current and past marriages."""

    __slots__ = ("current_marriage", "past_marriage_ids")

    current_marriage: Optional[GameObject]
    past_marriage_ids: list[int]

    def __init__(self) -> None:
        super().__init__()
        self.current_marriage = None
        self.past_marriage_ids = []


class RomanticAffair(Component):
    """Information about a character's lover.

    This tracks information about a lover relationship from a single character's POV.
    """

    __slots__ = ("character", "lover", "start_date")

    character: GameObject
    lover: GameObject
    start_date: SimDate

    def __init__(
        self, character: GameObject, lover: GameObject, start_date: SimDate
    ) -> None:
        super().__init__()
        self.character = character
        self.lover = lover
        self.start_date = start_date


class RomanticAffairTracker(Component):
    """Tracks character's current and past love affairs."""

    __slots__ = ("current_affair", "past_affair_ids")

    current_affair: Optional[GameObject]
    past_affair_ids: list[int]

    def __init__(self) -> None:
        super().__init__()
        self.current_affair = None
        self.past_affair_ids = []


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
        "parent_family",
        "branch_families",
        "head",
        "former_heads",
        "active_members",
        "former_members",
        "alliance",
        "home_base",
        "territories",
        "warriors",
        "advisors",
        "color_primary",
        "color_secondary",
        "color_tertiary",
        "banner_symbol",
    )

    name: str
    """The name of the family."""
    parent_family: Optional[GameObject]
    """The family that this family branched from."""
    branch_families: OrderedSet[GameObject]
    """Branches of this family."""
    head: Optional[GameObject]
    """The character that is currently in charge of the family."""
    former_heads: OrderedSet[GameObject]
    """Former heads of this family."""
    former_members: OrderedSet[GameObject]
    """All people who have left the family."""
    alliance: Optional[GameObject]
    """The alliance this family belongs to."""
    home_base: Optional[GameObject]
    """The settlement this family belongs to."""
    territories: OrderedSet[GameObject]
    """The settlements this family has control over."""
    active_members: OrderedSet[GameObject]
    """Characters actively a part of this family."""
    warriors: OrderedSet[GameObject]
    """Characters responsible for strength during wars."""
    advisors: OrderedSet[GameObject]
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
        self.parent_family = None
        self.branch_families = OrderedSet([])
        self.head = None
        self.alliance = None
        self.home_base = None
        self.territories = OrderedSet([])
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

    family: GameObject
    """The family they are the head of."""

    def __init__(self, family: GameObject) -> None:
        super().__init__()
        self.family = family


class Emperor(TagComponent):
    """Tags the character as the emperor of the land."""


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

    founder: GameObject
    family: GameObject
    _founding_date: SimDate
    current_ruler: Optional[GameObject]
    previous_rulers: OrderedSet[GameObject]
    _ending_date: Optional[SimDate]
    previous_dynasty: Optional[GameObject]

    def __init__(
        self,
        founder: GameObject,
        family: GameObject,
        founding_date: SimDate,
        previous_dynasty: Optional[GameObject] = None,
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
    def last_ruler(self) -> Optional[GameObject]:
        """Get the last ruler of the dynasty."""
        if self.previous_rulers:
            return self.previous_rulers[-1]
        return None


class DynastyTracker:
    """A shared singleton that tracks the current royal family and dynasty."""

    __slots__ = ("current_dynasty", "previous_dynasties", "all_rulers")

    current_dynasty: Optional[GameObject]
    previous_dynasties: OrderedSet[GameObject]
    all_rulers: OrderedSet[GameObject]

    def __init__(self) -> None:
        self.current_dynasty = None
        self.previous_dynasties = OrderedSet([])
        self.all_rulers = OrderedSet([])

    @property
    def last_ruler(self) -> Optional[GameObject]:
        """Get a reference to the last character that ruled."""
        if self.all_rulers:
            return self.all_rulers[-1]

        return None

    @property
    def last_dynasty(self) -> Optional[GameObject]:
        """Get the previous dynasty."""
        if self.previous_dynasties:
            return self.previous_dynasties[-1]

        return None


class MoneyMotive(StatComponent):
    """Tracks a character's want for money."""

    def __init__(self, calculation_strategy: IStatCalculationStrategy) -> None:
        super().__init__(
            calculation_strategy,
            CHARACTER_MOTIVE_BASE,
            (0, CHARACTER_MOTIVE_MAX),
            True,
        )


class PowerMotive(StatComponent):
    """Tracks a character's want for power."""

    def __init__(self, calculation_strategy: IStatCalculationStrategy) -> None:
        super().__init__(
            calculation_strategy,
            CHARACTER_MOTIVE_BASE,
            (0, CHARACTER_MOTIVE_MAX),
            True,
        )


class RespectMotive(StatComponent):
    """Tracks a character's want for respect."""

    def __init__(self, calculation_strategy: IStatCalculationStrategy) -> None:
        super().__init__(
            calculation_strategy,
            CHARACTER_MOTIVE_BASE,
            (0, CHARACTER_MOTIVE_MAX),
            True,
        )


class HappinessMotive(StatComponent):
    """Tracks a character's want for happiness."""

    def __init__(self, calculation_strategy: IStatCalculationStrategy) -> None:
        super().__init__(
            calculation_strategy,
            CHARACTER_MOTIVE_BASE,
            (0, CHARACTER_MOTIVE_MAX),
            True,
        )


class FamilyMotive(StatComponent):
    """Tracks a character's want for family."""

    def __init__(self, calculation_strategy: IStatCalculationStrategy) -> None:
        super().__init__(
            calculation_strategy,
            CHARACTER_MOTIVE_BASE,
            (0, CHARACTER_MOTIVE_MAX),
            True,
        )


class HonorMotive(StatComponent):
    """Tracks a character's want for honor."""

    def __init__(self, calculation_strategy: IStatCalculationStrategy) -> None:
        super().__init__(
            calculation_strategy,
            CHARACTER_MOTIVE_BASE,
            (0, CHARACTER_MOTIVE_MAX),
            True,
        )


class SexMotive(StatComponent):
    """Tracks a character's want for sex."""

    def __init__(self, calculation_strategy: IStatCalculationStrategy) -> None:
        super().__init__(
            calculation_strategy,
            CHARACTER_MOTIVE_BASE,
            (0, CHARACTER_MOTIVE_MAX),
            True,
        )


class DreadMotive(StatComponent):
    """Tracks a character's want for dread."""

    def __init__(self, calculation_strategy: IStatCalculationStrategy) -> None:
        super().__init__(
            calculation_strategy,
            CHARACTER_MOTIVE_BASE,
            (0, CHARACTER_MOTIVE_MAX),
            True,
        )


class Lifespan(StatComponent):
    """Tracks a GameObject's lifespan."""

    __stat_name__ = "Lifespan"

    def __init__(
        self,
        calculation_strategy: IStatCalculationStrategy,
        base_value: float = 0,
    ) -> None:
        super().__init__(calculation_strategy, base_value, (0, 999_999), True)


class Fertility(StatComponent):
    """Tracks a GameObject's fertility."""

    __stat_name__ = "Fertility"

    MAX_VALUE: int = 100

    def __init__(
        self,
        calculation_strategy: IStatCalculationStrategy,
        base_value: float = 0,
    ) -> None:
        super().__init__(calculation_strategy, base_value, (0, self.MAX_VALUE), True)


class Stewardship(StatComponent):
    """Tracks a GameObject's stewardship."""

    __stat_name__ = "Stewardship"

    MAX_VALUE: int = 100

    def __init__(
        self,
        calculation_strategy: IStatCalculationStrategy,
        base_value: float = 0,
    ) -> None:
        super().__init__(calculation_strategy, base_value, (0, self.MAX_VALUE), True)


class Martial(StatComponent):
    """Tracks a GameObject's martial."""

    __stat_name__ = "Martial"

    MAX_VALUE: int = 100

    def __init__(
        self,
        calculation_strategy: IStatCalculationStrategy,
        base_value: float = 0,
    ) -> None:
        super().__init__(calculation_strategy, base_value, (0, self.MAX_VALUE), True)


class Intrigue(StatComponent):
    """Tracks a GameObject's intrigue."""

    __stat_name__ = "Intrigue"

    MAX_VALUE: int = 100

    def __init__(
        self,
        calculation_strategy: IStatCalculationStrategy,
        base_value: float = 0,
    ) -> None:
        super().__init__(calculation_strategy, base_value, (0, self.MAX_VALUE), True)


class Learning(StatComponent):
    """Tracks a GameObject's learning."""

    __stat_name__ = "Learning"

    MAX_VALUE: int = 100

    def __init__(
        self,
        calculation_strategy: IStatCalculationStrategy,
        base_value: float = 0,
    ) -> None:
        super().__init__(calculation_strategy, base_value, (0, self.MAX_VALUE), True)


class Prowess(StatComponent):
    """Tracks a GameObject's prowess."""

    __stat_name__ = "Prowess"

    MAX_VALUE: int = 100

    def __init__(
        self,
        calculation_strategy: IStatCalculationStrategy,
        base_value: float = 0,
    ) -> None:
        super().__init__(calculation_strategy, base_value, (0, self.MAX_VALUE), True)


class Sociability(StatComponent):
    """Tracks a GameObject's sociability."""

    __stat_name__ = "Sociability"

    MAX_VALUE: int = 100

    def __init__(
        self,
        calculation_strategy: IStatCalculationStrategy,
        base_value: float = 0,
    ) -> None:
        super().__init__(calculation_strategy, base_value, (0, self.MAX_VALUE), True)


class Honor(StatComponent):
    """Tracks a GameObject's honor."""

    __stat_name__ = "Honor"

    MAX_VALUE: int = 100

    def __init__(
        self,
        calculation_strategy: IStatCalculationStrategy,
        base_value: float = 0,
    ) -> None:
        super().__init__(calculation_strategy, base_value, (0, self.MAX_VALUE), True)


class Boldness(StatComponent):
    """Tracks a GameObject's boldness."""

    __stat_name__ = "Boldness"

    MAX_VALUE: int = 100

    def __init__(
        self,
        calculation_strategy: IStatCalculationStrategy,
        base_value: float = 0,
    ) -> None:
        super().__init__(calculation_strategy, base_value, (0, self.MAX_VALUE), True)


class Compassion(StatComponent):
    """Tracks a GameObject's compassion."""

    __stat_name__ = "Compassion"

    MAX_VALUE: int = 100

    def __init__(
        self,
        calculation_strategy: IStatCalculationStrategy,
        base_value: float = 0,
    ) -> None:
        super().__init__(calculation_strategy, base_value, (0, self.MAX_VALUE), True)


class Diplomacy(StatComponent):
    """Tracks a GameObject's diplomacy."""

    __stat_name__ = "Diplomacy"

    MAX_VALUE: int = 100

    def __init__(
        self,
        calculation_strategy: IStatCalculationStrategy,
        base_value: float = 0,
    ) -> None:
        super().__init__(calculation_strategy, base_value, (0, self.MAX_VALUE), True)


class Greed(StatComponent):
    """Tracks a GameObject's greed."""

    __stat_name__ = "Greed"

    MAX_VALUE: int = 100

    def __init__(
        self,
        calculation_strategy: IStatCalculationStrategy,
        base_value: float = 0,
    ) -> None:
        super().__init__(calculation_strategy, base_value, (0, self.MAX_VALUE), True)


class Rationality(StatComponent):
    """Tracks a GameObject's rationality."""

    __stat_name__ = "Rationality"

    MAX_VALUE: int = 100

    def __init__(
        self,
        calculation_strategy: IStatCalculationStrategy,
        base_value: float = 0,
    ) -> None:
        super().__init__(calculation_strategy, base_value, (0, self.MAX_VALUE), True)


class Vengefulness(StatComponent):
    """Tracks a GameObject's vengefulness."""

    __stat_name__ = "Vengefulness"

    MAX_VALUE: int = 100

    def __init__(
        self,
        calculation_strategy: IStatCalculationStrategy,
        base_value: float = 0,
    ) -> None:
        super().__init__(calculation_strategy, base_value, (0, self.MAX_VALUE), True)


class Zeal(StatComponent):
    """Tracks a GameObject's zeal."""

    __stat_name__ = "Zeal"

    MAX_VALUE: int = 100

    def __init__(
        self,
        calculation_strategy: IStatCalculationStrategy,
        base_value: float = 0,
    ) -> None:
        super().__init__(calculation_strategy, base_value, (0, self.MAX_VALUE), True)


class RomancePropensity(StatComponent):
    """Tracks a GameObject's propensity for romantic actions."""

    __stat_name__ = "RomancePropensity"

    MAX_VALUE: int = 100

    def __init__(
        self,
        calculation_strategy: IStatCalculationStrategy,
        base_value: float = 0,
    ) -> None:
        super().__init__(calculation_strategy, base_value, (0, self.MAX_VALUE), True)


class ViolencePropensity(StatComponent):
    """Tracks a GameObject's propensity for violent actions."""

    __stat_name__ = "ViolencePropensity"

    MAX_VALUE: int = 100

    def __init__(
        self,
        calculation_strategy: IStatCalculationStrategy,
        base_value: float = 0,
    ) -> None:
        super().__init__(calculation_strategy, base_value, (0, self.MAX_VALUE), True)


class WantForPower(StatComponent):
    """Tracks a GameObject's propensity to take actions that increase social power."""

    __stat_name__ = "WantForPower"

    MAX_VALUE: int = 100

    def __init__(
        self,
        calculation_strategy: IStatCalculationStrategy,
        base_value: float = 0,
    ) -> None:
        super().__init__(calculation_strategy, base_value, (0, self.MAX_VALUE), True)


class WantForChildren(StatComponent):
    """Tracks a GameObject's propensity to have children."""

    __stat_name__ = "WantForChildren"

    MAX_VALUE: int = 100

    def __init__(
        self,
        calculation_strategy: IStatCalculationStrategy,
        base_value: float = 0,
    ) -> None:
        super().__init__(calculation_strategy, base_value, (0, self.MAX_VALUE), True)


class WantToWork(StatComponent):
    """Tracks a GameObject's propensity to find and stay at a job."""

    __stat_name__ = "WantToWork"

    MAX_VALUE: int = 100

    def __init__(
        self,
        calculation_strategy: IStatCalculationStrategy,
        base_value: float = 0,
    ) -> None:
        super().__init__(calculation_strategy, base_value, (0, self.MAX_VALUE), True)


class Luck(StatComponent):
    """Tracks a GameObject's propensity to be successful."""

    __stat_name__ = "Luck"

    MAX_VALUE: int = 100

    def __init__(
        self,
        calculation_strategy: IStatCalculationStrategy,
        base_value: float = 0,
    ) -> None:
        super().__init__(calculation_strategy, base_value, (0, self.MAX_VALUE), True)


class WantForMarriage(StatComponent):
    """Tracks a GameObject's propensity to be married."""

    __stat_name__ = "WantForMarriage"

    MAX_VALUE: int = 100

    def __init__(
        self,
        calculation_strategy: IStatCalculationStrategy,
        base_value: float = 0,
    ) -> None:
        super().__init__(calculation_strategy, base_value, (0, self.MAX_VALUE), True)
