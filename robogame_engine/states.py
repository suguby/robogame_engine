# -*- coding: utf-8 -*-
from robogame_engine.events import EventStopped, EventStoppedAtTargetPoint
from robogame_engine.geometry import normalise_angle, Vector


class ObjectState(object):

    def __init__(self, obj, **kwargs):
        self.obj = obj
        self.kwargs = kwargs

    def move(self, target, speed):
        self.obj.state = StateMoving(obj=self.obj, target=target, speed=speed)

    def stop(self):
        self.obj.state = StateStopped(obj=self.obj)

    def turn(self, vector, target):
        self.obj.state = StateTurning(obj=self.obj, vector=vector, target=target)

    def step(self):
        raise NotImplementedError


class StateTurning(ObjectState):

    def turn(self, vector, target):
        self.vector = vector
        self.target = target

    def step(self):
        obj = self.obj
        if obj.rotatable:
            delta = self.vector.angle - obj.course
            if abs(delta) < obj.TURN_SPEED:
                obj.course = obj.vector.angle
                if self.target:
                    obj.state = StateMoving(obj=obj, target=self.target)
                else:
                    obj.state = StateStopped(obj=obj)
            else:
                if -180 < delta < 0 or delta > 180:
                    obj.course -= obj.TURN_SPEED
                else:
                    obj.course += obj.TURN_SPEED
                obj.course = normalise_angle(obj.course)


class StateMoving(ObjectState):

    def __init__(self, obj, **kwargs):
        super(StateMoving, self).__init__(obj, **kwargs)
        self.target = None

    def move(self, target, speed):
        self.vector = Vector(self.obj.coord, self.target, speed)

    def step(self):
        self.obj.coord.add(self.vector)
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
