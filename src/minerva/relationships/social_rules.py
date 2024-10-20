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

reputation_boost_for_family = SocialRule(
    rule_id="boost_for_family_members",
    precondition=BelongToSameFamily(),
    reputation_modifier=StatModifier(
        modifier_type=StatModifierType.FLAT,
        value=10,
    ),
)

reputation_boost_for_birth_family = SocialRule(
    rule_id="boost_for_birth_family_members",
    precondition=BelongToSameBirthFamily(),
    reputation_modifier=StatModifier(
        modifier_type=StatModifierType.FLAT,
        value=5,
    ),
)

not_attracted_to_parents = SocialRule(
    "not_attracted_to_parents",
    precondition=TargetIsParent(),
    romance_modifier=StatModifier(
        modifier_type=StatModifierType.FLAT,
        value=-50,
    ),
)

reputation_boost_for_parents = SocialRule(
    "reputation_boost_for_parents",
    precondition=TargetIsParent(),
    reputation_modifier=StatModifier(
        modifier_type=StatModifierType.FLAT,
        value=10,
    ),
)

romance_drop_for_children = SocialRule(
    "romance_drop_for_children",
    precondition=TargetIsChild(),
    romance_modifier=StatModifier(
        modifier_type=StatModifierType.FLAT,
        value=-100,
    ),
)

reputation_boost_for_children = SocialRule(
    "reputation_boost_for_children",
    precondition=TargetIsChild(),
    reputation_modifier=StatModifier(
        modifier_type=StatModifierType.FLAT,
        value=10,
    ),
)

romance_drop_for_siblings = SocialRule(
    "romance_drop_for_siblings",
    precondition=TargetIsSibling(),
    romance_modifier=StatModifier(
        modifier_type=StatModifierType.FLAT,
        value=-50,
    ),
)

reputation_boost_for_siblings = SocialRule(
    "reputation_boost_for_siblings",
    precondition=TargetIsSibling(),
    reputation_modifier=StatModifier(
        modifier_type=StatModifierType.FLAT,
        value=10,
    ),
)

reputation_boost_for_spouse = SocialRule(
    "reputation_boost_for_spouse",
    precondition=TargetIsSpouse(),
    reputation_modifier=StatModifier(
        modifier_type=StatModifierType.FLAT,
        value=10,
    ),
)

romance_boost_for_spouse = SocialRule(
    "romance_boost_for_spouse",
    precondition=TargetIsSpouse(),
    romance_modifier=StatModifier(
        modifier_type=StatModifierType.FLAT,
        value=10,
    ),
)
