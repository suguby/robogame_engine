#!/usr/bin/env python
# -*- coding: utf-8 -*-

from Queue import Queue
from random import randint

from core import logger
from events import (EventHearbeat, EventStoppedAtTargetPoint, EventStopped)
from geometry import Point, Vector, normalise_angle


class GameObject():
    """
        Main game object
    """
    radius = 1
    _objects_count = 0
    states = ['stopped', 'turning', 'moving']
    container = None
    _animated = True

    def __init__(self, pos, revolvable=True, angle=None):
        self.coord = Point(pos)
        self.target_coord = Point(0, 0)

        if angle is None:
            angle = randint(0, 360)
        self.vector = Vector(angle, 0)
        self.course = self.vector.angle
        self.shot = False
        self._revolvable = revolvable
        self.load_value = 0
        self._distance_cache = {}
        self._events = Queue()
        self._selected = False
        self._state = 'stopped'
        self._need_moving = False

        # container - это список обьектов игры по типам,
        # инициализируется в Scene
        if self.container is None:
            raise Exception("You must create robopycode.engine.Scene"
                            " instance at first!")
        self.container.append(self)

        GameObject._objects_count += 1
        self.id = GameObject._objects_count
        self.debug('born %s', self)

        self._heartbeat_tics = 5

    def __str__(self):
        return 'obj(%s, %s %s cour=%.1f %s)' \
                % (self.id, self.coord, self.vector,
                   self.course, self._state)

    def __repr__(self):
        return str(self)

    def debug(self, pattern, *args):
        """
            Show debug information if DEBUG mode
        """
        if isinstance(self, Tank):
            if self._selected:
                logger.debug('%s:%s' % (self.id, pattern), *args)
        else:
            logger.debug('%s:%s:%s' % (self.__class__.__name__,
                                           self.id, pattern), *args)

    def _need_turning(self):
        return self._revolvable and int(self.course) != int(self.vector.angle)

    def turn_to(self, arg1):
        """
            Turn to the subject / in that direction
        """
        if isinstance(arg1, GameObject) or arg1.__class__ == Point:
            self.vector = Vector(self, arg1, 0)
        elif arg1.__class__ == int or arg1.__class__ == float:
            direction = arg1
            self.vector = Vector(direction, 0)
        else:
            raise Exception("use GameObject.turn_to(GameObject/Point "
                            "or Angle). Your pass %s" % arg1)
        self._state = 'turning'

    def move(self, direction, speed=3):
        """
            Ask movement in the direction of <angle>, <speed>
        """
        if speed > tank_speed:
            speed = tank_speed
        self.vector = Vector(direction, speed)
        self.target_coord = self.coord + self.vector * 100  # далеко-далеко...
        self._need_moving = True
        if self._need_turning():
            self._state = 'turning'
        else:
            self._state = 'moving'

    def move_at(self, target, speed=3):
        """
            Ask movement to the specified point
            <object/point/coordinats>, <speed>
        """
        if type(target) in (type(()), type([])):
            target = Point(target)
        elif target.__class__ == Point:
            pass
        elif isinstance(target, GameObject):
            target = target.coord
        else:
            raise Exception("move_at: target %s must be coord "
                            "or point or GameObject!" % target)
        if speed > tank_speed:
            speed = tank_speed
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
        self.debug('obj step %s', self)
        if self._revolvable and self._state == 'turning':
            delta = self.vector.angle - self.course
            if abs(delta) < tank_turn_speed:
                self.course = self.vector.angle
                if self._need_moving:
                    self._state = 'moving'
                else:
                    self._state = 'stopped'
                    self._events.put(EventStopped())
            else:
                if -180 < delta < 0 or delta > 180:
                    self.course -= tank_turn_speed
                else:
                    self.course += tank_turn_speed
                self.course = normalise_angle(self.course)

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
            self._heartbeat_tics = 5

    def _runout(self, coordinate, hight_bound=None):
        """
            proverka vyhoda za granicy igrovogo polja
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
        if obj.__class__ == Point:
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
        logger.info('Object {} stopped'.format(self.id))

    def stopped_at_target(self):
        """
            Event: stopped at target
        """
        logger.info('Object {} stopped at target'.format(self.id))

    def hearbeat(self):
        """
            Event: Heartbeat
        """
        logger.info('Object {} heartbeat'.format(self.id))


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