# -*- coding: utf-8 -*-
from robogame_engine.exceptions import RobogameException
from .theme import theme
from .geometry import Point, Vector
from .utils import CanLogging


class Command(CanLogging):
    """
        Command to GameObjects
    """

    def __init__(self, obj, **kwargs):
        self.obj = obj
        self.kwargs = kwargs

    def execute(self):
        raise NotImplementedError()

    def __str__(self):
        return '{name} {obj} kw={kwargs}'.format(
            name=self.__class__.__name__,
            obj=self.obj,
            kwargs=self.kwargs,
        )

    def __repr__(self):
        return str(self)

    def __unicode__(self):
        return str(self)


class MoveCommand(Command):

    def __init__(self, obj, target, speed, **kwargs):
        super(MoveCommand, self).__init__(obj, **kwargs)
        from .objects import GameObject
        if isinstance(target, (Point, GameObject)):
            self.target = target
        else:
            raise RobogameException("Target {} must be one of Point, GameObject, Image".format(target))
        self.speed = speed

    def execute(self):
        self.obj.state.move(target=self.target, speed=self.speed, **self.kwargs)

    def __str__(self):
        return super(MoveCommand, self).__str__() + " tgt={} spd={}".format(self.target, self.speed)


class TurnCommand(Command):

    def __init__(self, obj, target, **kwargs):
        super(TurnCommand, self).__init__(obj, **kwargs)
        from .objects import GameObject
        self.target = target
        if isinstance(target, (GameObject, )):
            self.vector = Vector.from_points(self.obj.coord, target.coord)
        elif isinstance(target, Point):
            self.vector = Vector.from_points(self.obj.coord, target)
        elif isinstance(target, (int, float)):
            # TODO убрать поддержку поворота к направлению ???
            direction = target
            self.vector = Vector.from_direction(direction, theme.MAX_SPEED)
            self.target = obj.coord + self.vector * 100
        else:
            raise RobogameException("use GameObject.turn_to(GameObject/Point "
                            "or Angle). Your pass {}".format(target))

    def execute(self):
        self.obj.state.turn(vector=self.vector, target=self.target)

    def __str__(self):
        return super(TurnCommand, self).__str__() + " tgt={}".format(self.target)


class StopCommand(Command):

    def execute(self):
        self.obj.state.stop(**self.kwargs)
