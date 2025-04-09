"""Traits Adapted from Crusader Kings III.

Source: https://ck3.paradoxwikis.com/Traits
"""

from minerva.actions.base_types import Proclivity
from minerva.ecs import World
from minerva.stats.base_types import StatModifier, StatModifierType
from minerva.traits.base_types import CharacterTrait, CharacterTraitDatabase
from minerva.traits.effects import (
    AddDiplomacyModifier,
    AddFertilityModifier,
    AddIntrigueModifier,
    AddLifespanModifier,
    AddMartialModifier,
    AddProclivity,
    AddProwessModifier,
    AddStewardshipModifier,
)


def load_traits(world: World) -> None:
    """Load trait definitions."""
    trait_library = world.get_resource(CharacterTraitDatabase)

    trait_library.add_trait(
        CharacterTrait(
            trait_id="royal_blood",
            name="Royal Blood",
            spawn_frequency=0,
            inheritance_chance_single=1.0,
            inheritance_chance_both=1.0,
            effects=[
                AddProclivity(Proclivity(5).where(lambda a: "succession" in a.tags))
            ],
        )
    )

    trait_library.add_trait(
        CharacterTrait(
            trait_id="brave",
            name="Brave",
            conflicting_traits=["craven"],
            spawn_frequency=1,
            effects=[
                AddMartialModifier(StatModifier(10)),
                AddProwessModifier(StatModifier(15)),
            ],
        )
    )

    trait_library.add_trait(
        CharacterTrait(
            trait_id="craven",
            name="Craven",
            tags=["personality"],
            conflicting_traits=["brave"],
            spawn_frequency=1,
            effects=[
                AddMartialModifier(StatModifier(-10)),
                AddProwessModifier(StatModifier(-15)),
            ],
        )
    )

    trait_library.add_trait(
        CharacterTrait(
            trait_id="calm",
            name="Calm",
            tags=["personality"],
            conflicting_traits=["wrathful"],
            spawn_frequency=1,
            effects=[
                AddDiplomacyModifier(StatModifier(10)),
                AddIntrigueModifier(StatModifier(-20)),
            ],
        )
    )

    trait_library.add_trait(
        CharacterTrait(
            trait_id="wrathful",
            name="Wrathful",
            tags=["personality"],
            conflicting_traits=["calm"],
            spawn_frequency=1,
            effects=[
                AddIntrigueModifier(StatModifier(-10)),
                AddDiplomacyModifier(StatModifier(-10)),
            ],
        )
    )

    trait_library.add_trait(
        CharacterTrait(
            trait_id="chaste",
            name="Chaste",
            tags=["personality"],
            conflicting_traits=["lustful"],
            spawn_frequency=1,
            effects=[
                AddFertilityModifier(StatModifier(25, StatModifierType.PERCENT)),
            ],
        )
    )

    trait_library.add_trait(
        CharacterTrait(
            trait_id="lustful",
            name="Trait",
            tags=["personality"],
            conflicting_traits=["chaste"],
            spawn_frequency=1,
            effects=[
                AddFertilityModifier(StatModifier(25, StatModifierType.PERCENT)),
            ],
        )
    )

    trait_library.add_trait(
        CharacterTrait(
            trait_id="content",
            name="Content",
            tags=["personality"],
            conflicting_traits=["ambitious"],
            spawn_frequency=1,
            effects=[],
        )
    )

    trait_library.add_trait(
        CharacterTrait(
            trait_id="ambitious",
            name="Ambitious",
            tags=["personality"],
            conflicting_traits=["content"],
            spawn_frequency=1,
            effects=[
                AddStewardshipModifier(StatModifier(10)),
                AddDiplomacyModifier(StatModifier(10)),
            ],
        )
    )

    trait_library.add_trait(
        CharacterTrait(
            trait_id="diligent",
            name="Diligent",
            tags=["personality"],
            conflicting_traits=["lazy"],
            spawn_frequency=1,
            effects=[
                AddDiplomacyModifier(StatModifier(25)),
                AddStewardshipModifier(StatModifier(25)),
            ],
        )
    )

    trait_library.add_trait(
        CharacterTrait(
            trait_id="lazy",
            name="Lazy",
            tags=["personality"],
            conflicting_traits=["diligent"],
            spawn_frequency=1,
            effects=[
                AddDiplomacyModifier(StatModifier(25)),
                AddStewardshipModifier(StatModifier(-15)),
            ],
        )
    )

    trait_library.add_trait(
        CharacterTrait(
            trait_id="generous",
            name="Generous",
            tags=["personality"],
            conflicting_traits=["greedy"],
            spawn_frequency=1,
            effects=[
                AddDiplomacyModifier(StatModifier(20)),
            ],
        )
    )

    trait_library.add_trait(
        CharacterTrait(
            trait_id="greedy",
            name="Greedy",
            tags=["personality"],
            conflicting_traits=["generous"],
            spawn_frequency=1,
            effects=[
                AddDiplomacyModifier(StatModifier(-20)),
            ],
        )
    )

    trait_library.add_trait(
        CharacterTrait(
            trait_id="gregarious",
            name="Gregarious",
            tags=["personality"],
            conflicting_traits=["shy"],
            spawn_frequency=1,
            effects=[
                AddDiplomacyModifier(StatModifier(20)),
            ],
        )
    )

    trait_library.add_trait(
        CharacterTrait(
            trait_id="shy",
            name="Shy",
            tags=["personality"],
            conflicting_traits=["gregarious"],
            effects=[],
        )
    )

    trait_library.add_trait(
        CharacterTrait(
            trait_id="compassionate",
            name="Compassionate",
            tags=["personality"],
            conflicting_traits=["callous", "sadistic"],
            spawn_frequency=1,
            effects=[
                AddDiplomacyModifier(StatModifier(25)),
                AddProclivity(Proclivity(3).where(lambda a: "generous" in a.tags)),
            ],
        )
    )

    trait_library.add_trait(
        CharacterTrait(
            trait_id="honest",
            name="Honest",
            tags=["personality"],
            conflicting_traits=["deceitful"],
            effects=[
                AddDiplomacyModifier(StatModifier(10)),
                AddIntrigueModifier(StatModifier(-35)),
                AddProclivity(Proclivity(5).where(lambda a: "infidelity" in a.tags)),
                AddProclivity(Proclivity(-7).where(lambda a: "deceit" in a.tags)),
            ],
        )
    )

    trait_library.add_trait(
        CharacterTrait(
            trait_id="deceitful",
            name="Deceitful",
            tags=["personality"],
            conflicting_traits=["honest"],
            effects=[
                AddDiplomacyModifier(StatModifier(-10)),
                AddIntrigueModifier(StatModifier(35)),
                AddProclivity(Proclivity(7).where(lambda a: "infidelity" in a.tags)),
                AddProclivity(Proclivity(7).where(lambda a: "deceit" in a.tags)),
            ],
        )
    )

    trait_library.add_trait(
        CharacterTrait(
            trait_id="callous",
            name="Callous",
            tags=["personality"],
            conflicting_traits=["compassion", "sadistic"],
            spawn_frequency=1,
            effects=[
                AddDiplomacyModifier(StatModifier(-10)),
            ],
        )
    )

    trait_library.add_trait(
        CharacterTrait(
            trait_id="sadistic",
            name="Sadistic",
            tags=["personality"],
            conflicting_traits=["compassion", "callous"],
            spawn_frequency=1,
            effects=[],
        )
    )

    trait_library.add_trait(
        CharacterTrait(
            trait_id="fickle",
            name="Fickle",
            tags=["personality"],
            conflicting_traits=["stubborn", "eccentric"],
            spawn_frequency=1,
            effects=[
                AddStewardshipModifier(StatModifier(-15)),
                AddDiplomacyModifier(StatModifier(15)),
                AddProclivity(Proclivity(5).where(lambda a: "diplomacy" in a.tags)),
            ],
        )
    )

    trait_library.add_trait(
        CharacterTrait(
            trait_id="stubborn",
            name="Stubborn",
            tags=["personality"],
            conflicting_traits=["fickle", "eccentric"],
            spawn_frequency=1,
            effects=[
                AddStewardshipModifier(StatModifier(20)),
                AddLifespanModifier(StatModifier(5)),
            ],
        )
    )

    trait_library.add_trait(
        CharacterTrait(
            trait_id="eccentric",
            name="Eccentric",
            conflicting_traits=["fickle", "stubborn"],
            spawn_frequency=1,
            effects=[
                AddDiplomacyModifier(StatModifier(-15)),
                AddProclivity(Proclivity(2).where(lambda a: "diplomacy" in a.tags)),
            ],
        )
    )
