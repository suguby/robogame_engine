# -*- coding: utf-8 -*-
import unittest

from unittest import mock

from robogame_engine.scene import Scene
from robogame_engine.objects import GameObject
from robogame_engine.geometry import Point


class TestTurning(unittest.TestCase):

    def setUp(self):
        self.scene = Scene(field=(100, 100), theme_mod_path='tests.default_theme')

    def test_turn_to_direction(self):
        obj = GameObject(coord=Point(x=10, y=10), direction=0)
        obj.turn_to(target=30, speed=10)
        obj.on_stop = mock.MagicMock()
        for _ in range(3):
            self.scene.game_step()
        self.scene.game_step()  # событие происходит на след шаге игры
        self.assertEqual(obj.on_stop.call_count, 1)

