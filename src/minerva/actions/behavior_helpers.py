"""Helper classes and functions for character behaviors."""

import numpy as np

from minerva.actions.base_types import IAIBehavior
from minerva.characters.motive_helpers import MotiveVector


def get_behavior_utility(
    character_motives: MotiveVector, behavior: IAIBehavior
) -> tuple[MotiveVector, float]:
    """Calculates a the motive vect and utility for a given behavior for a character."""
    utility_vect = behavior.get_motive_vect().vect * (character_motives.vect * 2)
    utility_score = float(np.sum(utility_vect) / 9)  # total of 9 motives

    return MotiveVector.from_array(utility_vect), utility_score
