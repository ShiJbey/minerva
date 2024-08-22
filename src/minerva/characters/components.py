"""Components used to model characters."""

from __future__ import annotations

import enum
from typing import Optional

import pydantic
from ordered_set import OrderedSet

from minerva.datetime import SimDate
from minerva.ecs import Component, GameObject
from minerva.stats.base_types import StatComponent


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


class SpeciesDef(pydantic.BaseModel):
    """A definition for a species type."""

    name: str
    """The name of this species."""
    description: str = ""
    """A short description of the trait."""
    adolescent_age: int
    """Age this species reaches adolescence."""
    young_adult_age: int
    """Age this species reaches young adulthood."""
    adult_age: int
    """Age this species reaches main adulthood."""
    senior_age: int
    """Age this species becomes a senior/elder."""
    lifespan: str
    """A range of of years that this species lives (e.g. 'MIN - MAX')."""
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
    can_physically_age: bool = True
    """Does this character go through the various life stages."""
    traits: list[str] = pydantic.Field(default_factory=list)
    """Traits to apply to characters of this species."""


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
        "partner",
        "lover",
        "is_alive",
        "clan",
        "birth_clan",
        "family",
        "birth_family",
        "household",
        "heir",
        "heir_to",
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
    partner: Optional[GameObject]
    lover: Optional[GameObject]
    is_alive: bool
    clan: Optional[GameObject]
    birth_clan: Optional[GameObject]
    family: Optional[GameObject]
    birth_family: Optional[GameObject]
    household: Optional[GameObject]
    heir: Optional[GameObject]
    heir_to: Optional[GameObject]

    def __init__(
        self,
        first_name: str,
        surname: str,
        sex: Sex,
        species: SpeciesType,
        *,
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
        partner: Optional[GameObject] = None,
        lover: Optional[GameObject] = None,
        is_alive: bool = True,
        clan: Optional[GameObject] = None,
        birth_clan: Optional[GameObject] = None,
        family: Optional[GameObject] = None,
        birth_family: Optional[GameObject] = None,
        household: Optional[GameObject] = None,
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
        self.partner = partner
        self.lover = lover
        self.is_alive = is_alive
        self.clan = clan
        self.birth_clan = birth_clan
        self.family = family
        self.birth_family = birth_family
        self.household = household
        self.heir = heir
        self.heir_to = heir_to

    @property
    def full_name(self) -> str:
        """The combined full name of the character."""
        return f"{self.first_name} {self.surname}"


class KeyRelations(Component):
    """Cache of key people in a character's life, indexed by relationship type."""

    __slots__ = (
        "mother",
        "father",
        "biological_father",
        "spouse",
        "partner",
        "lover",
        "betrothed",
        "heir",
        "heir_to",
        "children",
        "siblings",
        "biological_siblings",
        "biological_children",
        "friends",
        "enemies",
        "crush",
        "best_friends",
        "worst_enemies",
    )

    mother: Optional[GameObject]
    father: Optional[GameObject]
    biological_father: Optional[GameObject]
    spouse: Optional[GameObject]
    partner: Optional[GameObject]
    lover: Optional[GameObject]
    betrothed: Optional[GameObject]
    heir: Optional[GameObject]
    heir_to: Optional[GameObject]
    children: OrderedSet[GameObject]
    biological_children: OrderedSet[GameObject]
    siblings: OrderedSet[GameObject]
    biological_siblings: OrderedSet[GameObject]
    friends: OrderedSet[GameObject]
    enemies: OrderedSet[GameObject]
    crush: Optional[GameObject]
    best_friends: OrderedSet[GameObject]
    worst_enemies: OrderedSet[GameObject]

    def __init__(self) -> None:
        super().__init__()
        self.mother = None
        self.father = None
        self.biological_father = None
        self.spouse = None
        self.partner = None
        self.lover = None
        self.betrothed = None
        self.heir = None
        self.heir_to = None
        self.children = OrderedSet([])
        self.biological_children = OrderedSet([])
        self.siblings = OrderedSet([])
        self.biological_siblings = OrderedSet([])
        self.friends = OrderedSet([])
        self.enemies = OrderedSet([])
        self.crush = None
        self.best_friends = OrderedSet([])
        self.worst_enemies = OrderedSet([])


class Species(Component):
    """Tracks the species a character belongs to."""

    __slots__ = ("species",)

    species: SpeciesType
    """The species the character belongs to."""

    def __init__(self, species: SpeciesType) -> None:
        super().__init__()
        self.species = species


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


class Household(Component):
    """A collection of characters that all live together."""

    __slots__ = ("head", "members", "family")

    head: Optional[GameObject]
    """The head of the household."""
    members: list[GameObject]
    """Other members of the household."""
    family: Optional[GameObject]
    """The family this household belongs to."""

    def __init__(self) -> None:
        super().__init__()
        self.head = None
        self.members = []
        self.family = None


class HeadOfHousehold(Component):
    """Marks a character as being the head of a household."""

    __slots__ = ("household",)

    household: GameObject
    """The household they are the head of."""

    def __init__(self, household: GameObject) -> None:
        super().__init__()
        self.household = household


class Family(Component):
    """A collection of household bearing the same name."""

    __slots__ = ("name", "households", "head", "heir", "members", "clan")

    name: str
    """The name of the family."""
    households: list[GameObject]
    """Households belonging to this family."""
    head: Optional[GameObject]
    """The character that is currently in charge of the family."""
    members: list[GameObject]
    """All members of this family."""
    clan: Optional[GameObject]
    """The clan this family belongs to."""

    def __init__(self, name: str = "") -> None:
        super().__init__()
        self.name = name
        self.households = []
        self.head = None
        self.heir = None
        self.members = []
        self.clan = None


class HeadOfFamily(Component):
    """Marks a character as being the head of a family."""

    __slots__ = ("family",)

    family: GameObject
    """The family they are the head of."""

    def __init__(self, family: GameObject) -> None:
        super().__init__()
        self.family = family


class Clan(Component):
    """A collection of families."""

    __slots__ = (
        "name",
        "families",
        "head",
        "members",
        "home_base",
    )

    name: str
    """The name of the clan."""
    families: list[GameObject]
    """Families that belong to the clan."""
    head: Optional[GameObject]
    """The character that is currently in charge of the clan."""
    members: list[GameObject]
    """All members of this clan."""
    home_base: Optional[GameObject]
    """Set the home base of this clan."""

    def __init__(self, name: str = "") -> None:
        super().__init__()
        self.name = name
        self.families = []
        self.head = None
        self.members = []
        self.home_base = None


class HeadOfClan(Component):
    """Marks a character as being the head of a clan."""

    __slots__ = ("clan",)

    clan: GameObject
    """The clan they are the head of."""

    def __init__(self, clan: GameObject) -> None:
        super().__init__()
        self.clan = clan


class Lifespan(StatComponent):
    """Tracks a GameObject's lifespan."""

    __stat_name__ = "Lifespan"

    def __init__(
        self,
        base_value: float = 0,
    ) -> None:
        super().__init__(base_value, (0, 999_999), True)


class Fertility(StatComponent):
    """Tracks a GameObject's fertility."""

    __stat_name__ = "Fertility"

    MAX_VALUE: int = 100

    def __init__(
        self,
        base_value: float = 0,
    ) -> None:
        super().__init__(base_value, (0, self.MAX_VALUE), True)


class Stewardship(StatComponent):
    """Tracks a GameObject's stewardship."""

    __stat_name__ = "Stewardship"

    MAX_VALUE: int = 100

    def __init__(
        self,
        base_value: float = 0,
    ) -> None:
        super().__init__(base_value, (0, self.MAX_VALUE), True)


class Martial(StatComponent):
    """Tracks a GameObject's martial."""

    __stat_name__ = "Martial"

    MAX_VALUE: int = 100

    def __init__(
        self,
        base_value: float = 0,
    ) -> None:
        super().__init__(base_value, (0, self.MAX_VALUE), True)


class Intrigue(StatComponent):
    """Tracks a GameObject's intrigue."""

    __stat_name__ = "Intrigue"

    MAX_VALUE: int = 100

    def __init__(
        self,
        base_value: float = 0,
    ) -> None:
        super().__init__(base_value, (0, self.MAX_VALUE), True)


class Learning(StatComponent):
    """Tracks a GameObject's learning."""

    __stat_name__ = "Learning"

    MAX_VALUE: int = 100

    def __init__(
        self,
        base_value: float = 0,
    ) -> None:
        super().__init__(base_value, (0, self.MAX_VALUE), True)


class Prowess(StatComponent):
    """Tracks a GameObject's prowess."""

    __stat_name__ = "Prowess"

    MAX_VALUE: int = 100

    def __init__(
        self,
        base_value: float = 0,
    ) -> None:
        super().__init__(base_value, (0, self.MAX_VALUE), True)


class Sociability(StatComponent):
    """Tracks a GameObject's sociability."""

    __stat_name__ = "Sociability"

    MAX_VALUE: int = 100

    def __init__(
        self,
        base_value: float = 0,
    ) -> None:
        super().__init__(base_value, (0, self.MAX_VALUE), True)


class Honor(StatComponent):
    """Tracks a GameObject's honor."""

    __stat_name__ = "Honor"

    MAX_VALUE: int = 100

    def __init__(
        self,
        base_value: float = 0,
    ) -> None:
        super().__init__(base_value, (0, self.MAX_VALUE), True)


class Boldness(StatComponent):
    """Tracks a GameObject's boldness."""

    __stat_name__ = "Boldness"

    MAX_VALUE: int = 100

    def __init__(
        self,
        base_value: float = 0,
    ) -> None:
        super().__init__(base_value, (0, self.MAX_VALUE), True)


class Compassion(StatComponent):
    """Tracks a GameObject's compassion."""

    __stat_name__ = "Compassion"

    MAX_VALUE: int = 100

    def __init__(
        self,
        base_value: float = 0,
    ) -> None:
        super().__init__(base_value, (0, self.MAX_VALUE), True)


class Diplomacy(StatComponent):
    """Tracks a GameObject's diplomacy."""

    __stat_name__ = "Diplomacy"

    MAX_VALUE: int = 100

    def __init__(
        self,
        base_value: float = 0,
    ) -> None:
        super().__init__(base_value, (0, self.MAX_VALUE), True)


class Greed(StatComponent):
    """Tracks a GameObject's greed."""

    __stat_name__ = "Greed"

    MAX_VALUE: int = 100

    def __init__(
        self,
        base_value: float = 0,
    ) -> None:
        super().__init__(base_value, (0, self.MAX_VALUE), True)


class Rationality(StatComponent):
    """Tracks a GameObject's rationality."""

    __stat_name__ = "Rationality"

    MAX_VALUE: int = 100

    def __init__(
        self,
        base_value: float = 0,
    ) -> None:
        super().__init__(base_value, (0, self.MAX_VALUE), True)


class Vengefulness(StatComponent):
    """Tracks a GameObject's vengefulness."""

    __stat_name__ = "Vengefulness"

    MAX_VALUE: int = 100

    def __init__(
        self,
        base_value: float = 0,
    ) -> None:
        super().__init__(base_value, (0, self.MAX_VALUE), True)


class Zeal(StatComponent):
    """Tracks a GameObject's zeal."""

    __stat_name__ = "Zeal"

    MAX_VALUE: int = 100

    def __init__(
        self,
        base_value: float = 0,
    ) -> None:
        super().__init__(base_value, (0, self.MAX_VALUE), True)


class RomancePropensity(StatComponent):
    """Tracks a GameObject's propensity for romantic actions."""

    __stat_name__ = "RomancePropensity"

    MAX_VALUE: int = 100

    def __init__(
        self,
        base_value: float = 0,
    ) -> None:
        super().__init__(base_value, (0, self.MAX_VALUE), True)


class ViolencePropensity(StatComponent):
    """Tracks a GameObject's propensity for violent actions."""

    __stat_name__ = "ViolencePropensity"

    MAX_VALUE: int = 100

    def __init__(
        self,
        base_value: float = 0,
    ) -> None:
        super().__init__(base_value, (0, self.MAX_VALUE), True)


class WantForPower(StatComponent):
    """Tracks a GameObject's propensity to take actions that increase social power."""

    __stat_name__ = "WantForPower"

    MAX_VALUE: int = 100

    def __init__(
        self,
        base_value: float = 0,
    ) -> None:
        super().__init__(base_value, (0, self.MAX_VALUE), True)


class WantForChildren(StatComponent):
    """Tracks a GameObject's propensity to have children."""

    __stat_name__ = "WantForChildren"

    MAX_VALUE: int = 100

    def __init__(
        self,
        base_value: float = 0,
    ) -> None:
        super().__init__(base_value, (0, self.MAX_VALUE), True)


class WantToWork(StatComponent):
    """Tracks a GameObject's propensity to find and stay at a job."""

    __stat_name__ = "WantToWork"

    MAX_VALUE: int = 100

    def __init__(
        self,
        base_value: float = 0,
    ) -> None:
        super().__init__(base_value, (0, self.MAX_VALUE), True)


class Luck(StatComponent):
    """Tracks a GameObject's propensity to be successful."""

    __stat_name__ = "Luck"

    MAX_VALUE: int = 100

    def __init__(
        self,
        base_value: float = 0,
    ) -> None:
        super().__init__(base_value, (0, self.MAX_VALUE), True)


class WantForMarriage(StatComponent):
    """Tracks a GameObject's propensity to be married."""

    __stat_name__ = "WantForMarriage"

    MAX_VALUE: int = 100

    def __init__(
        self,
        base_value: float = 0,
    ) -> None:
        super().__init__(base_value, (0, self.MAX_VALUE), True)
