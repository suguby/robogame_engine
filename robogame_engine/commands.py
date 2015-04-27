# -*- coding: utf-8 -*-
from robogame_engine.geometry import Point, Vector


class Command(object):
    """
        Command to GameObjec-s
    """

    def __init__(self, **kwargs):
        self.kwargs = kwargs

    def execute(self, obj):
        raise NotImplementedError()


class MoveCommand(Command):

    def execute(self, obj):
        obj.state.move(**self.kwargs)


class StopCommand(Command):

    def execute(self, obj):
        obj.state.stop(**self.kwargs)


class TurnCommand(Command):

    def __init__(self, obj, target, **kwargs):
        super(TurnCommand, self).__init__(**kwargs)
        from .objects import GameObject
        self.target = None
        if isinstance(target, GameObject) or isinstance(target, Point):
            self.vector = Vector(obj, target, 0)
            if isinstance(target, GameObject):
                self.target = target
        elif isinstance(target, int) or isinstance(target, float):
            direction = target
            self.vector = Vector(direction, 0)
        else:
            raise Exception("use GameObject.turn_to(GameObject/Point "
                            "or Angle). Your pass %s" % target)

    def execute(self, obj):
        obj.state.turn(vector=self.vector, target=self.target)
