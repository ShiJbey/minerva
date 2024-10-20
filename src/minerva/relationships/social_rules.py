"""Built-in social rule implementations."""

from minerva.relationships.base_types import SocialRule
from minerva.relationships.preconditions import (
    BelongToSameBirthFamily,
    BelongToSameFamily,
    TargetIsChild,
    TargetIsParent,
    TargetIsSibling,
    TargetIsSpouse,
)
from minerva.stats.base_types import StatModifier, StatModifierType

opinion_boost_for_family = SocialRule(
    rule_id="boost_for_family_members",
    precondition=BelongToSameFamily(),
    opinion_modifier=StatModifier(
        modifier_type=StatModifierType.FLAT,
        value=10,
    ),
)

opinion_boost_for_birth_family = SocialRule(
    rule_id="boost_for_birth_family_members",
    precondition=BelongToSameBirthFamily(),
    opinion_modifier=StatModifier(
        modifier_type=StatModifierType.FLAT,
        value=5,
    ),
)

not_attracted_to_parents = SocialRule(
    "not_attracted_to_parents",
    precondition=TargetIsParent(),
    attraction_modifier=StatModifier(
        modifier_type=StatModifierType.FLAT,
        value=-50,
    ),
)

opinion_boost_for_parents = SocialRule(
    "opinion_boost_for_parents",
    precondition=TargetIsParent(),
    opinion_modifier=StatModifier(
        modifier_type=StatModifierType.FLAT,
        value=10,
    ),
)

attraction_drop_for_children = SocialRule(
    "attraction_drop_for_children",
    precondition=TargetIsChild(),
    attraction_modifier=StatModifier(
        modifier_type=StatModifierType.FLAT,
        value=-100,
    ),
)

opinion_boost_for_children = SocialRule(
    "opinion_boost_for_children",
    precondition=TargetIsChild(),
    opinion_modifier=StatModifier(
        modifier_type=StatModifierType.FLAT,
        value=10,
    ),
)

attraction_drop_for_siblings = SocialRule(
    "attraction_drop_for_siblings",
    precondition=TargetIsSibling(),
    attraction_modifier=StatModifier(
        modifier_type=StatModifierType.FLAT,
        value=-50,
    ),
)

opinion_boost_for_siblings = SocialRule(
    "opinion_boost_for_siblings",
    precondition=TargetIsSibling(),
    opinion_modifier=StatModifier(
        modifier_type=StatModifierType.FLAT,
        value=10,
    ),
)

opinion_boost_for_spouse = SocialRule(
    "opinion_boost_for_spouse",
    precondition=TargetIsSpouse(),
    opinion_modifier=StatModifier(
        modifier_type=StatModifierType.FLAT,
        value=10,
    ),
)

attraction_boost_for_spouse = SocialRule(
    "attraction_boost_for_spouse",
    precondition=TargetIsSpouse(),
    attraction_modifier=StatModifier(
        modifier_type=StatModifierType.FLAT,
        value=10,
    ),
)
