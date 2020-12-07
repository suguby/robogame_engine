#!/usr/bin/env python
# -*- coding: utf-8 -*-

from .utils import CanLogging


class GameEvent(CanLogging):
    """
        Base class for objects events
    """

    def __init__(self, event_objs=None):  # TODO переделать на кварги
        self._event_objs = event_objs or []

    def get_event_objects(self):
        return self._event_objs

    def handle(self, obj):
        raise NotImplementedError()

    def __str__(self):
        return self.__class__.__name__

    def __unicode__(self):
        return str(self)


class EventBorned(GameEvent):

    def handle(self, obj):
        obj.on_born()


class EventStopped(GameEvent):

    def handle(self, obj):
        obj.on_stop()


class EventStoppedAtTargetPoint(GameEvent):

    def handle(self, obj):
        obj.on_stop_at_target(self._event_objs)


class EventCollide(GameEvent):

    def handle(self, obj):
        obj.on_collide_with(self._event_objs)


class EventOverlap(GameEvent):

    def handle(self, obj):
        obj.on_overlap_with(self._event_objs)


class EventHeartbeat(GameEvent):

    def handle(self, obj):
        obj.on_heartbeat()
