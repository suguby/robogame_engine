# -*- coding: utf-8 -*-
from robogame_engine.theme import theme
from robogame_engine.events import EventStoppedAtTargetPoint
from robogame_engine.geometry import normalise_angle, Vector
from robogame_engine.utils import CanLogging


class ObjectState(CanLogging):

    def __init__(self, obj, **kwargs):
        self.obj = obj
        self.kwargs = kwargs
        self.vector = None
        self.target = None

    def move(self, target, speed):
        self.obj.state = StateMoving(obj=self.obj, target=target, speed=speed)

    def stop(self):
        self.obj.state = StateStopped(obj=self.obj)

    def turn(self, vector, target):
        self.obj.state = StateTurning(obj=self.obj, vector=vector, target=target)

    def step(self):
        raise NotImplementedError

    def __str__(self):
        return "{}: {}".format(self.__class__.__name__, self.__dict__)


class StateTurning(ObjectState):

    def turn(self, vector, target):
        self.vector = vector
        self.target = target

    def step(self):
        obj = self.obj
        delta = self.vector.angle - obj.course
        if abs(delta) < theme.TURN_SPEED:
            obj.course = obj.vector.angle
            if self.target:
                obj.state = StateMoving(obj=obj, target=self.target, speed=10)  # TODO понять откуда брать скорость
            else:
                obj.state = StateStopped(obj=obj)
        else:
            if -180 < delta < 0 or delta > 180:
                obj.course -= theme.TURN_SPEED
            else:
                obj.course += theme.TURN_SPEED
            obj.course = normalise_angle(obj.course)


class StateMoving(ObjectState):

    def __init__(self, obj, target, speed, **kwargs):
        super(StateMoving, self).__init__(obj, **kwargs)
        self.target = target
        self.vector = Vector(self.obj.coord, self.target, speed)

    def move(self, target, speed):
        self.target = target
        self.vector = Vector(self.obj.coord, self.target, speed)

    def step(self):
        self.obj.coord.add(self.vector)
        self.obj.course = self.vector.angle
        if self.obj.coord.near(self.target):
            self.obj.state = StateStopped(obj=self.obj)
            event = EventStoppedAtTargetPoint(self.target)
            self.obj.add_event(event)


class StateStopped(ObjectState):

    def stop(self):
        pass

    def step(self):
        pass


class StateDead(ObjectState):

    def move(self, target, speed):
        pass

    def stop(self):
        pass

    def turn(self, vector, target):
        pass

    def step(self):
        pass
