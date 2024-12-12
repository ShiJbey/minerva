# pylint: disable=C0302
"""Entity Component System

This ECS implementation is modified from the original version used in
Neighborly. Some classes have been renamed to reduce confusion and some
extra features were removed for simplicity. This ECS does not depend on
the esper 2.x library. That code has been adapted into this code since
I have no plans to upgrade to esper 3.x after the switch to module-level
functions and data. Also, the switch allowed us to customize the ECS API
to use Entities and our custom System/System group implementation. Credit
for the base ECS design goes to the esper library (referenced below).
Please check them out if you're looking for something more general-purpose.

This ECS implementation is not thread-safe. It assumes that everything happens
sequentially on the same thread.

There is no external documentation for this ECS. All public classes,
properties, and methods have doc comments to help ease confusion.

References:

- https://github.com/benmoran56/esper
- https://github.com/bevyengine/bevy
- https://github.com/SanderMertens/flecs
- https://unity.com/ecs

"""

from __future__ import annotations

import dataclasses
from abc import ABC, abstractmethod
from queue import PriorityQueue
from typing import (
    Any,
    ClassVar,
    Generator,
    Iterator,
    Optional,
    Type,
    TypeVar,
    Union,
    overload,
)

from ordered_set import OrderedSet

_CT = TypeVar("_CT", bound="Component")
_RT = TypeVar("_RT", bound="Any")
_ST = TypeVar("_ST", bound="System")

EntityId = int
"""Type alias int to entity ID."""


class Entity:
    """A reference to an entity within the world."""

    __slots__ = (
        "_uid",
        "world",
    )

    _uid: EntityId
    """The unique ID of this entity."""
    world: World
    """The world instance this entity belongs to."""

    def __init__(
        self,
        uid: int,
        world: World,
    ) -> None:
        self._uid = uid
        self.world = world

    @property
    def uid(self) -> EntityId:
        """The entity's unique ID."""
        return self._uid

    @property
    def name(self) -> str:
        """The entity's name."""
        return self.world.get_entity_name(self)

    @name.setter
    def name(self, value: str):
        """Set the entity's name."""
        self.world.set_entity_name(self, value)

    @property
    def is_valid(self) -> bool:
        """Check if the entity still exists in the ECS."""
        return self.world.entity_exists(self.uid)

    @property
    def is_active(self) -> bool:
        """Check if a entity is active."""
        return self.has_component(Active)

    @property
    def name_with_uid(self) -> str:
        """Get the name of the entity with the UID."""
        return f"{self.name} ({self._uid})"

    def activate(self) -> None:
        """Tag the entity as active."""
        self.world.activate(self)

    def deactivate(self) -> None:
        """Remove the Active tag from a entity."""
        self.world.deactivate(self)

    def destroy(self) -> None:
        """Remove a entity from the world."""
        self.world.destroy(self)

    def add_component(self, component: _CT) -> _CT:
        """Add a component."""
        return self.world.add_component(self, component)

    def remove_component(self, component_type: Type[Component]) -> bool:
        """Remove a component with the given type."""
        return self.world.remove_component(self, component_type)

    def get_component(self, component_type: Type[_CT]) -> _CT:
        """Get a component with the given type."""
        return self.world.get_component(self, component_type)

    def has_component(self, component_type: Type[Component]) -> bool:
        """Check if this entity has a component."""
        return self.world.has_component(self, component_type)

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Entity):
            return self.uid == other.uid
        return False

    def __hash__(self) -> int:
        return self.uid

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return f"Entity(uid={self.uid!r}, name={self.name!r})"


class Component(ABC):
    """A collection of data associated with an entity."""

    __slots__ = ("_entity",)

    _entity: Entity
    """The entity the component belongs to."""

    @property
    def entity(self) -> Entity:
        """Get the entity instance for this component."""
        return self._entity

    @entity.setter
    def entity(self, value: Entity) -> None:
        """Set the entity instance."""
        # This method should only be called by the ECS
        if not hasattr(self, "_entity"):
            self._entity = value
        else:
            raise RuntimeError("Cannot reassign the component to another entity.")


class TagComponent(Component):
    """An Empty component used to mark a entity as having a state or type."""

    def __str__(self) -> str:
        return self.__class__.__name__

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}()"


class Active(TagComponent):
    """Tags a entity as active within the simulation."""


class System(ABC):
    """Base class for systems, providing implementation for most lifecycle methods."""

    # pylint: disable=W0613

    __system_group__: ClassVar[str] = "UpdateSystems"
    """The system group the system will be added to."""
    __update_order__: ClassVar[tuple[str, ...]] = ()
    """Ordering constraints for when the system should be update."""

    __slots__ = ("_active",)

    _active: bool
    """Will this system update during the next simulation step."""

    def __init__(self) -> None:
        super().__init__()
        self._active = True

    @property
    def is_active(self) -> bool:
        """Is the system active and available to run each timestep."""
        return self._active

    def set_active(self, value: bool) -> None:
        """Toggle if this system is active and will update.

        Parameters
        ----------
        value
            The new active status.
        """
        self._active = value

    def on_add(self, world: World) -> None:
        """Lifecycle method called when the system is added to the world.

        Parameters
        ----------
        world
            The world instance the system is mounted to.
        """
        return

    @abstractmethod
    def on_update(self, world: World) -> None:
        """Run the system.

        Parameters
        ----------
        world
            The world instance the system is updating
        """
        return

    def on_destroy(self, world: World) -> None:
        """Lifecycle method called when a system is removed from the world.

        Parameters
        ----------
        world
            The world instance the system was removed from.
        """
        return

    @classmethod
    def system_name(cls) -> str:
        """Get the name of the system."""
        return cls.__name__

    @classmethod
    def system_group(cls) -> str:
        """Get the name of the system group the system should be added to."""
        return cls.__system_group__

    @classmethod
    def update_order(cls) -> tuple[str, ...]:
        """Get the tuple of update order constraints."""
        return cls.__update_order__


class SystemGroup(System, ABC):
    """A group of ECS systems that run as a unit.

    SystemGroups allow users to better structure the execution order of their systems.
    """

    __slots__ = ("_children",)

    _children: list[System]
    """The systems that belong to this group"""

    def __init__(self) -> None:
        super().__init__()
        self._children = []

    def set_active(self, value: bool) -> None:
        super().set_active(value)
        for child in self._children:
            child.set_active(value)

    def iter_children(self) -> Iterator[System]:
        """Get an iterator for the group's children.

        Returns
        -------
        Iterator[System]
            An iterator for the child system collection.
        """
        return iter(self._children)

    def add_child(self, system: System) -> None:
        """Add a new system as a sub_system of this group.

        Parameters
        ----------
        system
            The system to add to this group.
        """
        self._children.append(system)

    def remove_child(self, system_type: Type[System]) -> None:
        """Remove a child system.

        If for some reason there are more than one instance of the given system type,
        this method will remove the first instance it finds.

        Parameters
        ----------
        system_type
            The class type of the system to remove.
        """
        children_to_remove = [
            child for child in self._children if isinstance(child, system_type)
        ]

        if children_to_remove:
            self._children.remove(children_to_remove[0])

    def on_update(self, world: World) -> None:
        """Run all sub-systems.

        Parameters
        ----------
        world
            The world instance the system is updating
        """
        for child in self._children:
            if child.is_active:
                child.on_update(world)

    def sort_children(self) -> None:
        """Performs topologically sort child systems."""
        self._children = SystemGroup._topological_sort(self._children)

        for child in self._children:
            if isinstance(child, SystemGroup):
                child.sort_children()

    @dataclasses.dataclass
    class _SystemSortNode:
        system: System
        update_first: bool = False
        update_last: bool = False
        order: int = 0

    @dataclasses.dataclass(order=True)
    class _NodeQueueEntry:
        priority: int
        item: SystemGroup._SystemSortNode = dataclasses.field(compare=False)

    @staticmethod
    def _get_incoming_edges(
        edges: list[
            tuple[
                str,
                str,
            ]
        ],
        node: _SystemSortNode,
    ) -> list[str]:
        """Get incoming edges for a node in a system sorting graph."""
        return [n for n, m in edges if m == node.system.system_name()]

    @staticmethod
    def _get_outgoing_edges(
        edges: list[
            tuple[
                str,
                str,
            ]
        ],
        node: _SystemSortNode,
    ) -> list[str]:
        """Get outgoing edges for a node in a system sorting graph."""
        return [m for n, m in edges if n == node.system.system_name()]

    @staticmethod
    def _topological_sort(systems: list[System]) -> list[System]:
        """Perform topological sort on the provided systems."""

        # Convert the systems to nodes
        nodes: dict[str, SystemGroup._SystemSortNode] = {}
        edges: list[tuple[str, str]] = []
        for system in systems:
            node = SystemGroup._SystemSortNode(system=system)

            for constraint in system.update_order():
                if constraint == "first":
                    node.update_first = True
                    node.order -= 1
                elif constraint == "last":
                    node.update_last = True
                    node.order += 1
                else:
                    # We have to parse it
                    command, system_name = tuple(
                        s.strip() for s in constraint.split(":")
                    )

                    if command == "before":
                        edges.append((system.system_name(), system_name))
                    elif command == "after":
                        edges.append((system_name, system.system_name()))
                    else:
                        raise ValueError(
                            f"Unknown update order constraint: {constraint}."
                        )

            if node.update_first and node.update_last:
                raise ValueError(
                    f"'{system.system_name()}' has constraints to update first and last."
                )

            nodes[system.system_name()] = node

        # Remove edges missing nodes
        for i in reversed(range(len(edges))):
            _n, _m = edges[i]

            if _n not in nodes:
                edges.pop(i)
                continue

            if _m not in nodes:
                edges.pop(i)
                continue

        result: list[System] = []

        # Get all nodes with no incoming edges.
        starting_nodes = [
            node
            for node in nodes.values()
            if len(SystemGroup._get_incoming_edges(edges, node)) == 0
        ]

        node_queue: PriorityQueue[SystemGroup._NodeQueueEntry] = PriorityQueue()
        for node in starting_nodes:
            node_queue.put(SystemGroup._NodeQueueEntry(priority=node.order, item=node))

        while not node_queue.empty():
            entry = node_queue.get()
            node = entry.item
            result.append(node.system)

            for dependent_name in SystemGroup._get_outgoing_edges(edges, node):
                dependent = nodes[dependent_name]
                edges.remove((node.system.system_name(), dependent_name))

                if len(SystemGroup._get_incoming_edges(edges, dependent)) == 0:
                    node_queue.put(
                        SystemGroup._NodeQueueEntry(
                            priority=dependent.order, item=dependent
                        )
                    )

        if edges:
            raise ValueError("System ordering contains a dependency cycle.")

        return result


class InitializationSystems(SystemGroup):
    """A group of systems that run once at the beginning of the simulation.

    Any content initialization systems or initial world building systems should
    belong to this group.
    """

    __system_group__ = "SystemManager"
    __update_order__ = ("before:EarlyUpdateSystems", "first")

    def on_update(self, world: World) -> None:
        # Run all child systems first before deactivating
        super().on_update(world)
        self.set_active(False)


class EarlyUpdateSystems(SystemGroup):
    """The early phase of the update loop."""

    __system_group__ = "SystemManager"
    __update_order__ = ("first", "before:UpdateSystems")


class UpdateSystems(SystemGroup):
    """The main phase of the update loop."""

    __system_group__ = "SystemManager"
    __update_order__ = ("before:LateUpdateSystems",)


class LateUpdateSystems(SystemGroup):
    """The late phase of the update loop."""

    __system_group__ = "SystemManager"
    __update_order__ = ("last",)


class SystemManager(SystemGroup):
    """Manages system instances for a single world instance."""

    __slots__ = ("_world",)

    _world: World
    """The world instance associated with the SystemManager."""

    def __init__(self, world: World) -> None:
        super().__init__()
        self._world = world

    def add_system(
        self,
        system: System,
    ) -> None:
        """Add a System instance.

        Parameters
        ----------
        system
            The system to add.
        """

        stack: list[SystemGroup] = [self]
        success: bool = False

        while stack:
            current_sys = stack.pop()

            if current_sys.system_name() == system.system_group():
                current_sys.add_child(system)
                success = True
                break

            for child in current_sys.iter_children():
                if isinstance(child, SystemGroup):
                    stack.append(child)

        if success:
            self.sort_children()
        else:
            raise KeyError(f"Could not find system group: {system.system_group()}.")

    def get_system(self, system_type: Type[_ST]) -> _ST:
        """Attempt to get a System of the given type.

        Parameters
        ----------
        system_type
            The type of the system to retrieve.

        Returns
        -------
        _ST or None
            The system instance if one is found.
        """
        stack: list[tuple[SystemGroup, System]] = [
            (self, child) for child in self._children
        ]

        while stack:
            _, current_sys = stack.pop()

            if isinstance(current_sys, system_type):
                return current_sys

            if isinstance(current_sys, SystemGroup):
                for child in current_sys.iter_children():
                    stack.append((current_sys, child))

        raise KeyError(f"Could not find system with type: {system_type}.")

    def remove_system(self, system_type: Type[System]) -> None:
        """Remove all instances of a system type.

        Parameters
        ----------
        system_type
            The type of the system to remove.

        Notes
        -----
        This function performs a Depth-first search through
        the tree of system groups to find the one with the
        matching type.

        No exception is raised if it does not find a matching
        system.
        """

        stack: list[tuple[SystemGroup, System]] = [
            (self, c) for c in self.iter_children()
        ]

        while stack:
            group, current_sys = stack.pop()

            if isinstance(current_sys, system_type):
                group.remove_child(system_type)
                current_sys.on_destroy(self._world)

            else:
                if isinstance(current_sys, SystemGroup):
                    for child in current_sys.iter_children():
                        stack.append((current_sys, child))

    def update_systems(self) -> None:
        """Update all systems in the manager."""
        self.on_update(self._world)


_T1 = TypeVar("_T1", bound=Component)
_T2 = TypeVar("_T2", bound=Component)
_T3 = TypeVar("_T3", bound=Component)
_T4 = TypeVar("_T4", bound=Component)
_T5 = TypeVar("_T5", bound=Component)
_T6 = TypeVar("_T6", bound=Component)
_T7 = TypeVar("_T7", bound=Component)
_T8 = TypeVar("_T8", bound=Component)


class World:
    """Manages entities, systems, and resources."""

    __slots__ = (
        "_systems",
        "_next_entity_id",
        "_components",
        "_entities",
        "_uid_to_entity_map",
        "_entity_names",
        "_dead_entities",
        "_resources",
    )

    _next_entity_id: int
    """Next ID assigned to a spawned entity."""
    _components: dict[Type[Component], set[EntityId]]
    """Entity component data."""
    _entities: dict[EntityId, dict[Type[Component], Component]]
    """Entity data."""
    _uid_to_entity_map: dict[EntityId, Entity]
    """Map of UIDs to entity instances."""
    _entity_names: dict[EntityId, str]
    """Names of entities."""
    _dead_entities: OrderedSet[Entity]
    """Destroyed entities to clean-up at the start of a world step."""
    _resources: dict[Type[Any], Any]
    """Resources shared by the world instance."""

    def __init__(self) -> None:
        self._resources = {}
        self._systems = SystemManager(self)
        self._systems.add_system(InitializationSystems())
        self._systems.add_system(EarlyUpdateSystems())
        self._systems.add_system(UpdateSystems())
        self._systems.add_system(LateUpdateSystems())
        self._next_entity_id = 0
        self._components = {}
        self._entities = {}
        self._uid_to_entity_map = {}
        self._entity_names = {}
        self._dead_entities = OrderedSet([])

    def initialize(self) -> None:
        """Run initialization systems only."""
        initialization_system_group = self._systems.get_system(InitializationSystems)

        initialization_system_group.on_update(self)

    def step(self) -> None:
        """Advance the simulation as single tick and call all the systems."""
        self._clear_dead_entities()
        self._systems.update_systems()

    def add_system(self, system: System) -> None:
        """Add a System instance.

        Parameters
        ----------
        system
            The system to add.
        """
        self._systems.add_system(system)

    def get_system(self, system_type: Type[_ST]) -> _ST:
        """Attempt to get a System of the given type.

        Parameters
        ----------
        system_type
            The type of the system to retrieve.

        Returns
        -------
        _ST or None
            The system instance if one is found.
        """
        return self._systems.get_system(system_type)

    def remove_system(self, system_type: Type[System]) -> None:
        """Remove all instances of a system type."""
        self._systems.remove_system(system_type)

    def add_resource(self, resource: Any) -> None:
        """Add a shared resource to a world.

        Parameters
        ----------
        resource
            The resource to add
        """
        self._resources[type(resource)] = resource

    def remove_resource(self, resource_type: Type[Any]) -> None:
        """Remove a shared resource to a world.

        Parameters
        ----------
        resource_type
            The class of the resource.
        """
        del self._resources[resource_type]

    def get_resource(self, resource_type: Type[_RT]) -> _RT:
        """Access a shared resource.

        Parameters
        ----------
        resource_type
            The class of the resource.

        Returns
        -------
        _RT
            The instance of the resource.
        """
        return self._resources[resource_type]

    def has_resource(self, resource_type: Type[Any]) -> bool:
        """Check if a world has a shared resource.

        Parameters
        ----------
        resource_type
            The class of the resource.

        Returns
        -------
        bool
            True if the resource exists, False otherwise.
        """
        return resource_type in self._resources

    def entity(
        self,
        components: Optional[list[Component]] = None,
        name: str = "",
    ) -> Entity:
        """Create a new entity and add it to the world.

        Parameters
        ----------
        components
            A collection of component instances to add to the entity.
        name
            A name to give the entity.

        Returns
        -------
        Entity
            The created entity.
        """
        self._next_entity_id += 1

        entity = Entity(uid=self._next_entity_id, world=self)

        if entity.uid not in self._entities:
            self._entities[entity.uid] = {}
            self._uid_to_entity_map[entity.uid] = entity
            self._entity_names[entity.uid] = name

        if components:
            for component in components:
                self.add_component(entity, component)

        entity.activate()

        return entity

    def get_entity(self, uid: EntityId) -> Entity:
        """Get an entity by its UID."""
        return self._uid_to_entity_map[uid]

    def entity_exists(self, uid: EntityId) -> bool:
        """Check if an entity exists using its UID."""
        return uid in self._uid_to_entity_map

    def get_entity_name(self, entity: Entity) -> str:
        """Get the given entity's name."""
        return self._entity_names.get(entity.uid, "")

    def set_entity_name(self, entity: Entity, name: str) -> None:
        """Set the given entity's name."""
        self._entity_names[entity.uid] = name

    def activate(self, entity: Entity) -> None:
        """Tag the entity as active."""
        self.add_component(entity, Active())

    def deactivate(self, entity: Entity) -> None:
        """Remove the Active tag from an entity."""
        self.remove_component(entity, Active)

    def destroy(self, entity: Entity) -> None:
        """Remove an entity from the world."""
        entity.deactivate()
        self._dead_entities.append(entity)

    def _clear_dead_entities(self) -> None:
        """Delete entities that were removed from the world."""
        for entity in self._dead_entities:

            for component_type in self._entities[entity.uid]:
                self._components[component_type].discard(entity.uid)

                if not self._components[component_type]:
                    del self._components[component_type]

            del self._entities[entity.uid]
            del self._uid_to_entity_map[entity.uid]

        self._dead_entities.clear()

    def add_component(self, entity: Entity, component: _CT) -> _CT:
        """Add a component to the given entity and return it."""
        if entity.uid not in self._entities:
            raise ValueError(f"Entity ({entity.uid}) is invalid.")

        component_type = type(component)

        if component_type in self._entities[entity.uid]:
            raise TypeError(
                "Cannot have multiple components of same type. "
                f"Attempted to add {component_type}."
            )

        if component_type not in self._components:
            self._components[component_type] = set()

        self._components[component_type].add(entity.uid)

        self._entities[entity.uid][component_type] = component

        component.entity = entity

        return component

    def remove_component(self, entity: Entity, component_type: Type[Component]) -> bool:
        """Remove a component from the entity.

        Returns
        -------
        bool
            Returns True if component is removed, False otherwise.
        """
        if entity.uid not in self._entities:
            raise ValueError(f"Entity ({entity.uid}) is invalid.")

        if component_type in self._entities[entity.uid]:
            self._components[component_type].remove(entity.uid)

            if not self._components[component_type]:
                del self._components[component_type]

            del self._entities[entity.uid][component_type]

            return True

        return False

    def get_component(self, entity: Entity, component_type: Type[_CT]) -> _CT:
        """Get a component associated with the given entity."""
        if entity.uid not in self._entities:
            raise ValueError(f"Entity ({entity.uid}) is invalid.")

        if component_type in self._entities[entity.uid]:
            return self._entities[entity.uid][component_type]
        else:
            raise KeyError(
                f"Could not find Component with type: {component_type.__name__}."
            )

    def has_component(self, entity: Entity, component_type: Type[Component]) -> bool:
        """Check if this entity has a component."""
        if entity.uid not in self._entities:
            raise ValueError(f"Entity ({entity.uid}) is invalid.")

        return component_type in self._entities[entity.uid]

    @overload
    def query_components(
        self, component_types: tuple[Type[_T1]]
    ) -> Generator[tuple[EntityId, tuple[_T1]], None, None]: ...

    @overload
    def query_components(
        self, component_types: tuple[Type[_T1], Type[_T2]]
    ) -> Generator[tuple[EntityId, tuple[_T1, _T2]], None, None]: ...

    @overload
    def query_components(
        self, component_types: tuple[Type[_T1], Type[_T2], Type[_T3]]
    ) -> Generator[tuple[EntityId, tuple[_T1, _T2, _T3]], None, None]: ...

    @overload
    def query_components(
        self, component_types: tuple[Type[_T1], Type[_T2], Type[_T3], Type[_T4]]
    ) -> Generator[tuple[EntityId, tuple[_T1, _T2, _T3, _T4]], None, None]: ...

    @overload
    def query_components(
        self,
        component_types: tuple[Type[_T1], Type[_T2], Type[_T3], Type[_T4], Type[_T5]],
    ) -> Generator[tuple[EntityId, tuple[_T1, _T2, _T3, _T4, _T5]], None, None]: ...

    @overload
    def query_components(
        self,
        component_types: tuple[
            Type[_T1], Type[_T2], Type[_T3], Type[_T4], Type[_T5], Type[_T6]
        ],
    ) -> Generator[
        tuple[EntityId, tuple[_T1, _T2, _T3, _T4, _T5, _T6]], None, None
    ]: ...

    @overload
    def query_components(
        self,
        component_types: tuple[
            Type[_T1], Type[_T2], Type[_T3], Type[_T4], Type[_T5], Type[_T6], Type[_T7]
        ],
    ) -> Generator[
        tuple[EntityId, tuple[_T1, _T2, _T3, _T4, _T5, _T6, _T7]], None, None
    ]: ...

    @overload
    def query_components(
        self,
        component_types: tuple[
            Type[_T1],
            Type[_T2],
            Type[_T3],
            Type[_T4],
            Type[_T5],
            Type[_T6],
            Type[_T7],
            Type[_T8],
        ],
    ) -> Generator[
        tuple[EntityId, tuple[_T1, _T2, _T3, _T4, _T5, _T6, _T7, _T8]], None, None
    ]: ...

    def query_components(
        self,
        component_types: Union[
            tuple[Type[_T1]],
            tuple[Type[_T1], Type[_T2]],
            tuple[Type[_T1], Type[_T2], Type[_T3]],
            tuple[Type[_T1], Type[_T2], Type[_T3], Type[_T4]],
            tuple[Type[_T1], Type[_T2], Type[_T3], Type[_T4], Type[_T5]],
            tuple[Type[_T1], Type[_T2], Type[_T3], Type[_T4], Type[_T5], Type[_T6]],
            tuple[
                Type[_T1],
                Type[_T2],
                Type[_T3],
                Type[_T4],
                Type[_T5],
                Type[_T6],
                Type[_T7],
            ],
            tuple[
                Type[_T1],
                Type[_T2],
                Type[_T3],
                Type[_T4],
                Type[_T5],
                Type[_T6],
                Type[_T7],
                Type[_T8],
            ],
        ],
    ) -> Union[
        Generator[tuple[EntityId, tuple[_T1]], None, None],
        Generator[tuple[EntityId, tuple[_T1, _T2]], None, None],
        Generator[tuple[EntityId, tuple[_T1, _T2, _T3]], None, None],
        Generator[tuple[EntityId, tuple[_T1, _T2, _T3, _T4]], None, None],
        Generator[tuple[EntityId, tuple[_T1, _T2, _T3, _T4, _T5]], None, None],
        Generator[tuple[EntityId, tuple[_T1, _T2, _T3, _T4, _T5, _T6]], None, None],
        Generator[
            tuple[EntityId, tuple[_T1, _T2, _T3, _T4, _T5, _T6, _T7]], None, None
        ],
        Generator[
            tuple[EntityId, tuple[_T1, _T2, _T3, _T4, _T5, _T6, _T7, _T8]], None, None
        ],
    ]:
        """Get all game objects with the given components.

        Parameters
        ----------
        component_types
            The components to check for
        inactive_ok
            Include inactive entities in the query

        Returns
        -------
        A generator that yields components and their entity.
        """
        try:
            for entity_uid in sorted(  # type: ignore
                set.intersection(*[self._components[ct] for ct in component_types])  # type: ignore
            ):
                yield entity_uid, tuple(  # type: ignore
                    self._entities[entity_uid][ct] for ct in component_types
                )
        except KeyError:
            pass
