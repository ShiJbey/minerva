# Minerva: Agent Behavior Systems

Minerva considers agents and settlements to be agents operating within a shared multi-agent domain. As such, each can
perform various behaviors depending on their current state. Minerva uses utility-based AI calculations to determine what
behaviors an agent wants to perform and if they are successful at it.

## Character Motives

Characters have a set of motive stat values that help them determine what behaviors they want to perform. The concept of
character motives for utility AI is adapted from *The Sims 4*. Here we use character motives to represent various needs
for the character. Characters always seek to improve their station in life. So their motives mostly represent
psychological or social aspects of their well-being.

We use the following motives. Represented on a continuous floating-point interval from [0.0, 1.0].

- Money
- Power
- Respect
- Happiness
- Family
- Honor
- Lust
- Dread

We associate these same motives with behaviors. A motive score of 0 represents no improvement to that respective motive,
while a score of 1 represents high improvement.

A characters motive values can be influenced by their current goals and traits. They can also be modified by other
systems within the game. While not the only way behavior utilities are calculated, they are the most basic.

## Character Goals

Goals are additional information tagged to characters that provides more information about their
personality/motivations. They can apply buffs/debuffs to character motives and other stats to influence behavior
selection. Example goals might be things like `GetAJob` or `ExpandLand`.

## List of Behavior Systems

Behaviors are divided into different pools based on the types of agents that can perform the behavior, and each pool is
assigned to a system. Below is a list of Minerva's behavior systems and what types of behaviors/actions they manage.
Each system is run once each timestep. The systems calculate a utility score for all eligible behaviors for a given
agent and randomly choses one to perform from the top scoring behaviors.

- `CharacterBehaviorsSystem`: Handles basic character behaviors like getting a job, getting married, sex, committing
  marriage infidelity, and having children.
- `FamilyHeadBehaviorSystem`: Handles behaviors performed by family heads. These behaviors might include naming an heir,
  increasing taxes on the settlement they control, giving back to the settlement they control, challenging for control
  over the family, betrothing children, assassinating other family heads, making alliances, seizing power over
  uncontrolled settlements, declaring wars on other families, etc.
- `SettlementBehaviorSystem`: Handles behaviors performed by settlements. These behaviors include revolting against the
  current family in charge of the settlement.

## Behavior System Parameters

Set the following parameters in the `settings` dict of your simulation config to adjust the behavior of the behavior
systems listed previously. The following code shows how to add them.

```python
from minerva.config import Config
from minerva.simulation import Simulation

sim_config = Config(
    # Other config settings ...
    settings={
        # The minimum utility score required for a behavior to
        # be considered for execution
        "behavior_utility_threshold": 0.5,
        # Sets the maximum number of 'characters behaviors' a
        # character can perform each timestep/tick
        "character_behaviors_per_tick": 1,
        # Sets the maximum number of 'family head' behaviors a
        # family head can perform each timestep/tick
        "family_head_behaviors_per_tick": 1,
        # Sets the maximum number of 'settlement' behaviors a
        # settlement can perform each timestep/tick
        "settlement_behaviors_per_tick": 1,
        # Other settings ...
    }
)

sim = Simulation(sim_config)

# Run the simulation
```

## Modeling Behaviors in Code

### The Behavior Class

Each behavior is represented using a `Behavior` class instance with the following fields:

- `name: str` - The name of the behavior
- `motive_vector: MotiveVector` - The motivation vector used during utility calculations
- `considerations: list[IActionConsideration]` - A list of consideration functions used to calculate the utility of the
  behavior
- `execution_strategy: IBehaviorStrategy` - A function that defines how the behavior should be performed. The strategy
  instantiates Actions that characters can choose from that help satisfy the behavior.

### AI Behavior Component

Each agent has an `AIBehavior` component that tracks useful information used during behavior selection. Below are the
public fields.

- `last_chosen_behavior: str` - The name of the last behavior chosen by the agent regardless of if they were successful
  at performing it.
