# -*- coding: utf-8 -*-
from robogame_engine.events import EventStopped
from robogame_engine.geometry import normalise_angle


class ObjectState(object):

    def __init__(self, obj, **kwargs):
        self.obj = obj
        self.kwargs = kwargs

    def move(self, **kwargs):
        raise NotImplementedError()

    def stop(self, **kwargs):
        raise NotImplementedError()

    def turn(self, **kwargs):
        raise NotImplementedError()

    def step(self, **kwargs):
        raise NotImplementedError


class StateTurning(ObjectState):

    def move(self, **kwargs):
        self.obj.state = StateMoving(obj=self.obj, **kwargs)

    def stop(self, **kwargs):
        self.obj.state = StateStopped(obj=self.obj, **kwargs)

    def turn(self, vector, target, **kwargs):
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

    def move(self, target):
        self.target = target

    def stop(self):
        self.obj.state = StateStopped(obj=self.obj)

    def turn(self, target):
        self.obj.state = StateTurning(obj=self.obj, target=target)


class StateStopped(ObjectState):

    def __init__(self, obj, **kwargs):
        super(StateStopped, self).__init__(obj, **kwargs)
        self.obj._events.put(EventStopped())

    def move(self, target):
        self.obj.state = StateMoving(obj=self.obj)

    def stop(self):
        pass

    def turn(self, target):
        self.obj.state = StateTurning(obj=self.obj, target=target)

    def step(self):
        pass


class StateDead(ObjectState):

    def move(self, target):
        pass

    def stop(self):
        pass

    def turn(self, angle):
        pass

    def step(self):
        pass
