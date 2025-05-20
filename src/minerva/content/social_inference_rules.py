"""Social Inference Rules."""

from minerva.acquired_trait_system import (
    SocialInferenceRule,
    SocialInferenceRuleDatabase,
)
from minerva.ecs import World

_RULES = [
    SocialInferenceRule(
        name="UsurpVendetta",
        traits_to_add=["vendetta"],
        traits_to_remove=[],
        query="""
        FIND ?avenger, ?usurper
        WHERE
            UsurpThroneEvent(subject=?usurper, ruler=?avenger_parent)
            RelationshipTrait(owner_uid=?avenger_parent, target_uid=?avenger, trait_id="child")
            RelationshipTrait(owner_uid=?avenger_parent, target_uid=?avenger, trait_id="heir")
            Character(uid=?avenger, is_alive=TRUE)
            Character(uid=?usurper, is_alive=TRUE)
        """,
    )
]


def load_rules(world: World) -> None:
    """Load social inference rules."""
    world.get_resource(SocialInferenceRuleDatabase).add_rules(_RULES)
