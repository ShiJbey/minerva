"""Trait rules."""

from minerva.acquired_trait_system import TraitRule, TraitRuleDatabase
from minerva.ecs import World

_RULES = [
    TraitRule(
        name="WarriorQueen",
        traits_to_add=["warrior_queen"],
        traits_to_remove=[],
        query="""
        FIND ?character_uid
        WHERE
            Character(uid=?character_uid, sex="FEMALE", is_alive=TRUE)
            Ruler(character_uid=?character_uid, end_year=NULL)
        """,
    ),
    TraitRule(
        name="WarriorKing",
        traits_to_add=["warrior_king"],
        traits_to_remove=[],
        query="""
        FIND ?character_uid
        WHERE
            Character(uid=?character_uid, sex="MALE", is_alive=TRUE)
            Ruler(character_uid=?character_uid, end_year=NULL)
        """,
    ),
]


def load_rules(world: World) -> None:
    """Load trait rules."""
    world.get_resource(TraitRuleDatabase).add_rules(_RULES)
