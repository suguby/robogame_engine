# -*- coding: utf-8 -*-
from robogame_engine import GameObject


class Bee(GameObject):
    sprite_filename = 'bee.jpg'  # TODO вынести в тему, по имени класса

    def __init__(self, pos):
        super(Bee, self).__init__(pos)

    def update(self):
        pass


