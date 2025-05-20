"""Selection strategies for AI,"""

import random
from typing import Optional

from minerva.actions.base_types import (
    ActionSelectionStrategy,
    AIAction,
    ProclivityScores,
)


class MaxUtilActionSelectStrategy(ActionSelectionStrategy):
    """Select the action with the highest utility."""

    __slots__ = ("utility_threshold",)

    utility_threshold: float

    def __init__(self, utility_threshold: float = 0) -> None:
        super().__init__()
        self.utility_threshold = utility_threshold

    def choose_action(self, action_scores: ProclivityScores) -> Optional[AIAction]:

        max_utility: float = -999_999
        best_action: Optional[AIAction] = None

        num_actions = len(action_scores.actions)

        for i in range(num_actions):
            action_instance = action_scores.actions[i]
            score = action_scores.scores[i]

            if score < self.utility_threshold:
                continue

            if score > max_utility:
                best_action = action_instance

        return best_action


class WeightedActionSelectStrategy(ActionSelectionStrategy):
    """Perform weighted random selection using the utility is the weight."""

    __slots__ = ("utility_threshold", "rng")

    utility_threshold: float
    rng: Optional[random.Random]

    def __init__(
        self, utility_threshold: float = 0, rng: Optional[random.Random] = None
    ) -> None:
        super().__init__()
        self.utility_threshold = utility_threshold
        self.rng = rng

    def choose_action(self, action_scores: ProclivityScores) -> AIAction:
        if len(action_scores.actions) == 0:
            raise ValueError("No actions provided.")

        # Filter those with weights less than or equal to zero
        filtered_actions: list[tuple[AIAction, float]] = []

        num_actions = len(action_scores.actions)
        for i in range(num_actions):
            action_instance = action_scores.actions[i]
            score = action_scores.scores[i]

            if score < self.utility_threshold:
                continue

            filtered_actions.append((action_instance, score))

        if len(filtered_actions) == 0:
            raise ValueError("No actions found in list after filtering.")

        filtered_actions = sorted(filtered_actions, key=lambda p: p[1])
        top_action_pairs = filtered_actions[-3:]

        top_actions, top_action_weights = zip(*top_action_pairs)

        if self.rng is not None:
            return self.rng.choices(top_actions, top_action_weights, k=1)[0]
        else:
            return random.choices(top_actions, top_action_weights, k=1)[0]
