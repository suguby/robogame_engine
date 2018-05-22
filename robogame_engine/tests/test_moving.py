# -*- coding: utf-8 -*-
import unittest

from robogame_engine.scene import Scene
from robogame_engine.objects import GameObject
from robogame_engine.geometry import Point


class TestMoving(unittest.TestCase):

    def setUp(self):
        self.scene = Scene(field=(100, 100), theme_mod_path='robogame_engine.tests.default_theme')

    def test_move_at_point(self):
        obj = GameObject(coord=Point(x=10, y=10))
        obj.move_at(target=Point(x=10, y=300), speed=2)
        for i in range(5):
            self.scene.game_step()
        self.assertEqual(obj.y, 20)

