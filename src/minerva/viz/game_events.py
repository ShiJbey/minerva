"""Static event bus for the PyGame visualization."""

from minerva.event_emitter import EventEmitter

simulation_started = EventEmitter[None]()

simulation_paused = EventEmitter[None]()

gameobject_wiki_shown = EventEmitter[int]()
