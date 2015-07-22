# -*- coding: utf-8 -*-
from robogame_engine.theme import theme
from robogame_engine.geometry import Point, Vector
from robogame_engine.utils import CanLogging


class Command(CanLogging):
    """
        Command to GameObjects
    """

    def __init__(self, obj, **kwargs):
        self.obj = obj
        self.kwargs = kwargs

    def execute(self):
        raise NotImplementedError()


class MoveCommand(Command):

    def __init__(self, obj, target, speed, **kwargs):
        super(MoveCommand, self).__init__(obj, **kwargs)
        from .objects import GameObject
        if isinstance(target, Point):
            self.target = target
        elif isinstance(target, GameObject):
            self.target = target.coord
        else:
            raise Exception("Target {} must Point or GameObject!".format(target))
        self.speed = speed

    def execute(self):
        self.obj.state.move(target=self.target, speed=self.speed, **self.kwargs)


class TurnCommand(Command):

    def __init__(self, obj, target, **kwargs):
        super(TurnCommand, self).__init__(obj, **kwargs)
        from .objects import GameObject
        self.target = None
        if isinstance(target, GameObject):
            self.vector = Vector.from_points(self.obj, target.coord)
            self.target = target
        elif isinstance(target, Point):
            self.vector = Vector.from_points(self.obj, target)
        elif isinstance(target, int) or isinstance(target, float):
            direction = target
            self.vector = Vector.from_direction(direction, theme.MAX_SPEED)
        else:
            raise Exception("use GameObject.turn_to(GameObject/Point "
                            "or Angle). Your pass {}".format(target))

    def execute(self):
        self.obj.state.turn(vector=self.vector, target=self.target)


class StopCommand(Command):

    def execute(self):
        self.obj.state.stop(**self.kwargs)
