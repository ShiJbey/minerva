"""Selection strategies for AI,

"""

import logging
import random
from typing import Iterable, Optional

from minerva.actions.base_types import ActionSelectionStrategy, AIAction

_logger = logging.getLogger(__name__)


class MaxUtilActionSelectStrategy(ActionSelectionStrategy):
    """Select the action with the highest utility."""

    __slots__ = ("utility_threshold",)

    utility_threshold: float

    def __init__(self, utility_threshold: float = 0) -> None:
        super().__init__()
        self.utility_threshold = utility_threshold

    def choose_action(self, actions: Iterable[AIAction]) -> AIAction:

        max_utility: float = -999_999
        best_action: Optional[AIAction] = None

        for action in actions:
            utility = action.calculate_utility()

            if utility < self.utility_threshold:
                continue

            if utility > max_utility:
                best_action = action

        if best_action is None:
            raise ValueError(
                "No actions found in list with utility greater than "
                f"{self.utility_threshold}."
            )

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

    def choose_action(self, actions: Iterable[AIAction]) -> AIAction:
        action_list = [*actions]

        if len(action_list) == 0:
            raise ValueError("No actions provided.")

        # Filter those with weights less than or equal to zero
        filtered_actions: list[tuple[AIAction, float]] = []

        for action in action_list:
            utility = action.calculate_utility()

            if utility < self.utility_threshold:
                continue

            filtered_actions.append((action, utility))

        if len(filtered_actions) == 0:
            raise ValueError("No actions found in list after filtering.")

        filtered_actions = sorted(filtered_actions, key=lambda p: p[1])
        top_action_pairs = filtered_actions[-3:]

        top_action_names = [a.get_name() for a, _ in top_action_pairs]

        if "StartWarScheme" in top_action_names:
            _logger.info(
                "D:: (%s)",
                ", ".join([a.get_name() + "==>" + str(u) for a, u in top_action_pairs]),
            )

        top_actions, top_action_weights = zip(*top_action_pairs)

        if self.rng is not None:
            return self.rng.choices(top_actions, top_action_weights, k=1)[0]
        else:
            return random.choices(top_actions, top_action_weights, k=1)[0]
