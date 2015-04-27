#!/usr/bin/env python
# -*- coding: utf-8 -*-

from Queue import Queue
from random import randint
from robogame_engine.commands import TurnCommand

from .states import StateStopped

from .utils import logger
from .events import (EventHearbeat, EventStoppedAtTargetPoint, EventStopped)
from .geometry import Point, Vector, normalise_angle


class GameObject(object):
    """
        Main game object
    """
    TURN_SPEED = 5
    MAX_SPEED = 5
    HEARTBEAT_INTERVAL = 5
    __objects_count = 0
    container = None  # инициализируется в Scene
    radius = 1
    animated = True
    rotatable = True

    def __init__(self, pos, angle=None):
        GameObject.__objects_count += 1
        self.id = GameObject.__objects_count
        self.coord = Point(pos)
        self.target = None
        if angle is None:
            angle = randint(0, 360)
        self.vector = Vector(angle, 0)
        self.load_value_1 = 0
        self.load_value_2 = 0
        self.state = StateStopped(obj=self)

        if self.container is None:
            raise Exception("You must create Scene instance at first!")
        self.container.append(self)

        self._heartbeat_tics = self.HEARTBEAT_INTERVAL
        self._distance_cache = {}
        self._events = Queue()
        self._commands = Queue()
        self._selected = False

        self.debug('born {coord} {vector}')

    def __str__(self):
        return 'obj({id}, {coord} {vector} cour={course:1f} {_state})'.format(**self.__dict__)

    def __repr__(self):
        return str(self)

    def debug(self, pattern, **kwargs):
        """
            Show debug information if DEBUG mode
        """
        self._log(logger.debug, pattern, kwargs)

    def info(self, pattern, **kwargs):
        self._log(logger.info, pattern, kwargs)

    def _log(self, log_fun, pattern, kwargs):
        kwargs['cls'] = self.__class__.__name__
        kwargs.update(self.__dict__)
        pattern = '{cls}:{id}:' + pattern
        log_fun(pattern.format(**kwargs))

    def _need_turning(self):
        return self.revolvable and int(self.course) != int(self.vector.angle)

    def turn_to(self, target):
        """
            Turn to the subject / in that direction
        """
        command = TurnCommand(target=target)
        self._commands.put(command)

    def move(self, direction, speed=3):
        """
            Set movement in the direction of <angle>, <speed>
        """
        if speed > self.MAX_SPEED:
            speed = self.MAX_SPEED
        self.vector = Vector(direction, speed)
        self.target_coord = self.coord + self.vector * 100  # далеко-далеко...
        self._need_moving = True
        if self._need_turning():
            self._state = 'turning'
        else:
            self._state = 'moving'

    def move_at(self, target, speed=3):
        """
            Set movement to the specified obj/point
            <object/point/coordinats>, <speed>
        """
        if isinstance(target, tuple) or isinstance(target, list):
            target = Point(target)
        elif isinstance(target, Point):
            pass
        elif isinstance(target, GameObject):
            target = target.coord
        else:
            raise Exception("move_at: target %s must be coord "
                            "or point or GameObject!" % target)
        if speed > self.MAX_SPEED:
            speed = self.MAX_SPEED
        self.target_coord = target
        self.vector = Vector(self.coord, self.target_coord, speed)
        self._need_moving = True
        if self._need_turning():
            self._state = 'turning'
        else:
            self._state = 'moving'

    def stop(self):
        """
            Unconditional stop
        """
        self._state = 'stopped'
        self._need_moving = False
        self._events.put(EventStopped())

    def _game_step(self):
        """
            Proceed one game step - do turns, movements and boundary check
        """
        self.debug('step {coord} {vector} {_state}')
        while not self._commands.empty():
            command = self._commands.get()
            command.execute(obj=self)

        # if self.revolvable and self._state == 'turning':
        #     delta = self.vector.angle - self.course
        #     if abs(delta) < self.TURN_SPEED:
        #         self.course = self.vector.angle
        #         if self._need_moving:
        #             self._state = 'moving'
        #         else:
        #             self._state = 'stopped'
        #             self._events.put(EventStopped())
        #     else:
        #         if -180 < delta < 0 or delta > 180:
        #             self.course -= self.TURN_SPEED
        #         else:
        #             self.course += self.TURN_SPEED
        #         self.course = normalise_angle(self.course)

        if self._state == 'moving':
            self.coord.add(self.vector)
            if self.coord.near(self.target_coord):
                self.stop()
                self._events.put(EventStoppedAtTargetPoint(
                    self.target_coord))
        # boundary_check
        left_ro = self._runout(self.coord.x)
        if left_ro:
            self.coord.x += left_ro + 1
            self.stop()
        botm_ro = self._runout(self.coord.y)
        if botm_ro:
            self.coord.y += botm_ro + 1
            self.stop()
        righ_ro = self._runout(self.coord.x, field_width)
        if righ_ro:
            self.coord.x -= righ_ro + 1
            self.stop()
        top_ro = self._runout(self.coord.y, field_height)
        if top_ro:
            self.coord.y -= top_ro + 1
            self.stop()

        self._heartbeat_tics -= 1
        if not self._heartbeat_tics:
            event = EventHearbeat()
            self._events.put(event)
            self.hearbeat()
            self._heartbeat_tics = self.HEARTBEAT_INTERVAL

    def _runout(self, coordinate, hight_bound=None):
        """
            Check runout from battle field
        """
        if hight_bound:
            out = coordinate - (hight_bound - self.radius)
        else:
            out = self.radius - coordinate
        if out < 0:
            out = 0
        return out

    def distance_to(self, obj):
        """
            Calculate distance to <object/point>
        """
        if isinstance(obj, GameObject):  # и для порожденных классов
            return self.coord.distance_to(obj.coord)
        if isinstance(obj, Point):
            return self.coord.distance_to(obj)
        raise Exception("GameObject.distance_to: obj %s "
                        "must be GameObject or Point!" % (obj,))

    def near(self, obj, radius=20):
        """
            Is it near to the <object/point>?
        """
        return self.distance_to(obj) <= radius

    def _proceed_events(self):
        while not self._events.empty():
            event = self._events.get()
            event.handle(self)

    def stopped(self):
        """
            Event: stopped
        """
        self.info('stopped at {coord}')

    def stopped_at_target(self):
        """
            Event: stopped at target
        """
        self.info('stopped at target {coord}')

    def hearbeat(self):
        """
            Event: Heartbeat
        """
        self.info('heartbeat')


class ObjectState:
    """
        Hold game object state, useful for exchange between processes
    """
    params = (
        'id',
        'coord',
        'course',
        'armor',
        'gun_heat',
        '_revolvable',
        '_img_file_name',
        '_layer',
        '_selectable',
        '_animated'
        )

    def __init__(self, obj):
        for param in self.params:
            if hasattr(obj, param):
                val = getattr(obj, param)
                setattr(self, param, val)
        if hasattr(obj, '_detected_by'):
            self._detected_by = [
                detected_by_obj.id
                for detected_by_obj in obj._detected_by
            ]
        else:
            self._detected_by = []