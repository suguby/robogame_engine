#!/usr/bin/env python
# -*- coding: utf-8 -*-


class GameEvent:
    """
        Base class for objects events
    """

    def __init__(self, event_objs=None):
        self._event_objs = event_objs or []

    def get_event_objects(self):
        return self._event_objs


class EventStopped(GameEvent):

    def handle(self, obj):
        obj.stopped()


class EventStoppedAtTargetPoint(GameEvent):

    def handle(self, obj):
        obj.stopped_at_target_point(self._event_objs)


class EventCollide(GameEvent):

    def handle(self, obj):
        obj.collided_with(self._event_objs)


class EventHearbeat(GameEvent):

    def handle(self, obj):
        obj.hearbeat()
