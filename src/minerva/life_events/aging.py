"""Life Events for character aging."""

from minerva.ecs import GameObject
from minerva.life_events.base_types import LifeEvent


class BecomeAdolescentEvent(LifeEvent):
    """Event dispatched when a character becomes an adolescent."""

    __event_type__ = "become-adolescent"

    __slots__ = ("character",)

    character: GameObject

    def __init__(self, character: GameObject) -> None:
        super().__init__(world=character.world)
        self.character = character
        self.data = {"character": character}

    def __str__(self) -> str:
        return f"{self.character.name} became an adolescent."


class BecomeYoungAdultEvent(LifeEvent):
    """Event dispatched when a character becomes a young adult."""

    __event_type__ = "become-young-adult"

    character: GameObject

    def __init__(self, character: GameObject) -> None:
        super().__init__(world=character.world)
        self.character = character
        self.data = {"character": character}

    def __str__(self) -> str:
        return f"{self.character.name} became a young adult."


class BecomeAdultEvent(LifeEvent):
    """Event dispatched when a character becomes an adult."""

    __event_type__ = "become-adult"

    __slots__ = ("character",)

    character: GameObject

    def __init__(self, character: GameObject) -> None:
        super().__init__(world=character.world)
        self.character = character
        self.data = {"character": character}

    def __str__(self) -> str:
        return f"{self.character.name} became an adult."


class BecomeSeniorEvent(LifeEvent):
    """Event dispatched when a character becomes a senior."""

    __event_type__ = "become-senior"

    __slots__ = ("character",)

    character: GameObject

    def __init__(self, character: GameObject) -> None:
        super().__init__(world=character.world)
        self.character = character
        self.data = {"character": character}

    def __str__(self) -> str:
        return f"{self.character.name} became a senior."
