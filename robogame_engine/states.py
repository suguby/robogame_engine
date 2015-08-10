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
        target_coord = target.coord if hasattr(target, 'coord') else target
        if self.target:
            self.vector = Vector.from_points(self.obj.coord, target_coord, module=self.speed)
        else:
            self.vector = None

    def move(self, target, speed):
        if self.obj.rotate_mode == theme.ROTATE_TURNING:
            self.obj.state = StateTurning(obj=self.obj, target=target, speed=speed)
            self.obj.state.move_at_target = True
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
    move_at_target = False

    # def __init__(self, obj, target=None, speed=None, **kwargs):
    #     self.error("obj={obj}, target={target}, speed={speed}, kwargs={kwargs}", obj=obj, target=target, speed=speed, kwargs=kwargs)
    #     if target is None:
    #         self.warning("target is None!")
    #     super(StateTurning, self).__init__(obj, target, speed, **kwargs)

    def step(self):
        obj = self.obj
        delta = self.vector.direction - obj.direction
        if abs(delta) < theme.TURN_SPEED:
            obj.vector = self.vector
            if self.move_at_target:
                obj.state = StateMoving(obj=obj, target=self.target, speed=self.speed)
            else:
                obj.state = StateStopped(obj=obj)
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
