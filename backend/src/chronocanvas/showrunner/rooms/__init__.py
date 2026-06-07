"""Showrunner rooms: orchestrate many single-skill calls into room outputs,
detect disagreement, and run greenlight gates (TRD §8)."""

from chronocanvas.showrunner.rooms.definitions import ROOMS, RoomDef, build_requests
from chronocanvas.showrunner.rooms.disagreement import detect_disagreements
from chronocanvas.showrunner.rooms.events import EventType, event_payload

__all__ = [
    "ROOMS", "RoomDef", "build_requests", "detect_disagreements",
    "EventType", "event_payload",
]
