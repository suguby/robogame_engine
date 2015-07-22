# -*- coding: utf-8 -*-
from robogame_engine.theme import theme
from robogame_engine.events import EventStoppedAtTargetPoint
from robogame_engine.geometry import normalise_angle, Vector
from robogame_engine.utils import CanLogging


class ObjectState(CanLogging):

    def __init__(self, obj, target=None, speed=None, **kwargs):
        self.obj = obj
        self.kwargs = kwargs
        self.target = target
        self.speed = theme.MAX_SPEED if speed is None else speed
        if self.target:
            self.vector = Vector.from_points(self.obj.coord, self.target, module=self.speed)
        else:
            self.vector = None

    def move(self, target, speed):
        if self.obj.rotate_mode == theme.ROTATE_TURNING:
            self.obj.state = StateTurnToMoving(obj=self.obj, target=target, speed=speed)
        else:
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

    def step(self):
        obj = self.obj
        delta = self.vector.direction - obj.direction
        if abs(delta) < theme.TURN_SPEED:
            obj.state = StateStopped(obj=obj)
        else:
            if -180 < delta < 0 or delta > 180:
                obj.vector.rotate(-theme.TURN_SPEED)
            else:
                obj.vector.rotate(theme.TURN_SPEED)


class StateTurnToMoving(ObjectState):

    def step(self):
        obj = self.obj
        delta = self.vector.direction - obj.direction
        if abs(delta) < theme.TURN_SPEED:
            obj.vector = self.vector
            obj.state = StateMoving(obj=obj, target=self.target, speed=self.speed)
        else:
            if -180 < delta < 0 or delta > 180:
                obj.vector.rotate(-theme.TURN_SPEED)
            else:
                obj.vector.rotate(theme.TURN_SPEED)


class StateMoving(ObjectState):

    def step(self):
        self.obj.coord += self.vector
        self.obj.vector = self.vector
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
