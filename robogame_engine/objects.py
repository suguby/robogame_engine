#!/usr/bin/env python
# -*- coding: utf-8 -*-

from Queue import Queue
from collections import defaultdict

from robogame_engine.commands import TurnCommand, MoveCommand, StopCommand
from robogame_engine.constants import ROTATE_NO_TURN
from robogame_engine.theme import theme
from .states import StateStopped, StateMoving
from .utils import logger
from .events import (EventHearbeat, EventStopped, EventBorned)
from .geometry import Point


class GameObject(object):
    """
        Main game object
    """
    radius = 10
    animated = False
    rotate_mode = ROTATE_NO_TURN
    selectable = True
    layer = 0

    _sprite_filename = None
    _part_of_team = False
    __objects_count = 0
    __container = None
    _scene = None
    __max_speed = 3  # setted in scene
    _distance_cache = {}  # not used TODO use and clean each game step

    @classmethod
    def link_to_scene(cls, scene, container, max_speed):
        cls._scene = scene
        cls.__container = container
        cls.__max_speed = max_speed

    def __init__(self, pos=None, direction=0):
        if self._scene is None:
            raise Exception("You must create Scene instance at first!")
        self.__container.append(self)
        GameObject.__objects_count += 1
        self.id = GameObject.__objects_count
        self.coord = Point(pos) if pos else Point(0, 0)
        self.course = direction  # TODO везде изменить на direction надо наверно...
        self.target = None
        self.state = StateStopped(obj=self)

        self._heartbeat_tics = theme.HEARTBEAT_INTERVAL
        self._events = Queue()
        self._commands = Queue()
        self._selected = False
        self.add_event(EventBorned(self))
        self.debug('born {coord} {course}')

    @property
    def sprite_filename(self):
        if self._sprite_filename:
            return self._sprite_filename
        else:
            return "{}.png".format(self.__class__.__name__.lower())

    @property
    def x(self):
        return self.coord.x

    @property
    def y(self):
        return self.coord.y

    @property
    def team(self):
        if self._part_of_team:
            return self._scene.get_team(cls=self.__class__)
        return None

    @property
    def meter_1(self):
        return 0.0

    @property
    def meter_2(self):
        return 0.0

    @property
    def counter(self):
        return None

    @property
    def is_moving(self):
        return isinstance(self.state, StateMoving)

    def add_event(self, event):
        self._events.put(event)

    def add_command(self, command):
        self._commands.put(command)

    def proceed_events(self):
        while not self._events.empty():
            event = self._events.get()
            event.handle(obj=self)

    def proceed_commands(self):
        while not self._commands.empty():
            command = self._commands.get()
            command.execute()

    def game_step(self):
        """
            Proceed one game step - do turns, movements and boundary check
        """
        self.debug('step {coord} {course} {state}')
        self.state.step()
        self._check_runout()
        self._heartbeat()

    def _heartbeat(self):
        self._heartbeat_tics -= 1
        if not self._heartbeat_tics:
            event = EventHearbeat()
            self.add_event(event)
            self._heartbeat_tics = theme.HEARTBEAT_INTERVAL

    def _check_runout(self):
        left_ro = self._runout(self.coord.x)
        if left_ro:
            self.coord.x += left_ro + 1
            self.stop()
        botm_ro = self._runout(self.coord.y)
        if botm_ro:
            self.coord.y += botm_ro + 1
            self.stop()
        righ_ro = self._runout(self.coord.x, theme.FIELD_WIDTH)
        if righ_ro:
            self.coord.x -= righ_ro + 1
            self.stop()
        top_ro = self._runout(self.coord.y, theme.FIELD_HEIGHT)
        if top_ro:
            self.coord.y -= top_ro + 1
            self.stop()

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

    def near(self, obj, radius=None):
        """
            Is it near to the <object/point>?
        """
        if radius is None:
            radius = theme.NEAR_RADIUS
        return self.distance_to(obj) <= radius

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

    def __str__(self):
        return 'obj({id}, {coord} cour={course:1f})'.format(**self.__dict__)

    def __repr__(self):
        return str(self)

    def __unicode__(self):
        return str(self)

    # def _need_turning(self):
    # return self.revolvable and int(self.course) != int(self.vector.angle)
    #

    ############# Manage ###############

    def turn_to(self, target):
        """
            Turn to the subject / in that direction
        """
        command = TurnCommand(obj=self, target=target)
        self.add_command(command)

    def move_at(self, target, speed=3):
        """
            Set movement to the specified obj/point
            <object/point/coordinats>, <speed>
        """
        if speed > self.__max_speed:
            speed = self.__max_speed
        command = MoveCommand(obj=self, target=target, speed=speed)
        self.add_command(command)

    def stop(self):
        """
            Unconditional stop
        """
        self.add_command(command=StopCommand(obj=self))
        self.add_event(event=EventStopped())

    ############# Events ###############

    def on_born(self):
        """
            Event: born
        """
        self.info('born at {coord}')

    def on_stop(self):
        """
            Event: stopped
        """
        self.info('stopped at {coord}')

    def on_stop_at_target(self, target):
        """
            Event: stopped at target
        """
        self.info('stopped at target {}'.format(target))

    def on_collide_with(self, obj_status):
        """
            Event: Collide
        """
        self.info('collided with {}'.format(obj_status))

    def on_hearbeat(self):
        """
            Event: Heartbeat
        """
        self.info('heartbeat')


class ObjectStatus:
    """
        Hold game object state, useful for exchange between processes
    """
    SEND_TYPES = (bool, int, float, str, unicode, dict, )
    __fields = defaultdict(list)

    def __init__(self, obj):
        for attr_name in self.fields(obj):
            attr = getattr(obj, attr_name)
            setattr(self, attr_name, attr)

    def fields(self, obj):
        class_name = obj.__class__.__name__
        if class_name not in self.__fields:
            for attr_name in dir(obj):
                if attr_name.startswith('_'):
                    continue
                attr = getattr(obj, attr_name)
                if callable(attr):
                    continue
                for ttype in self.SEND_TYPES:
                    if isinstance(attr, ttype):
                        self.__fields[class_name].append(attr_name)
                        break
        return self.__fields[class_name]

