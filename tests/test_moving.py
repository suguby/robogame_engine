# -*- coding: utf-8 -*-
import unittest
from unittest import mock

from robogame_engine.scene import Scene
from robogame_engine.objects import GameObject
from robogame_engine.geometry import Point


class TestMoving(unittest.TestCase):

    def setUp(self):
        self.scene = Scene(field=(100, 100), theme_mod_path='tests.default_theme')

    def test_move_at_point(self):
        obj = GameObject(coord=Point(x=10, y=10), direction=180)
        obj.on_stop_at_target = mock.MagicMock()
        obj.move_at(target=Point(x=10, y=20), speed=2)
        for i in range(6):  # TODO почему 6 шагов? проверить и понять
            self.scene.game_step()
        self.assertEqual(obj.y, 20)
        self.scene.game_step()  # событие происходит на след шаге игры
        self.assertEqual(obj.on_stop_at_target.call_count, 1)

    def test_boundary_speed_less_radius(self):
        obj = GameObject(coord=Point(x=10, y=10), radius=5)
        obj.move_at(target=Point(x=-10, y=10), speed=3)
        for i in range(5):
            self.scene.game_step()
        # 10 - 3 - 3 - 3 (выход за границы) + 5 (отталкивание) и стоп
        self.assertEqual(obj.x, 6)

    def test_boundary_speed_more_radius(self):
        obj = GameObject(coord=Point(x=5, y=10), radius=2)
        obj.move_at(target=Point(x=-5, y=10), speed=3)
        for i in range(5):
            self.scene.game_step()
        # 5 - 3 - 3 (выход за границы) + 2 (отталкивание) и стоп
        self.assertEqual(obj.x, 3)

