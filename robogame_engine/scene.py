#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function

from collections import defaultdict, OrderedDict
from multiprocessing import Pipe, Process
from random import randint
import time

from robogame_engine.constants import GAME_OVER
from robogame_engine.exceptions import RobogameException
from .events import EventCollide, EventOverlap
from .geometry import Vector, Point
from .objects import ObjectStatus, GameObject
from .theme import theme
from .user_interface import UserInterface
from .utils import CanLogging


class Scene(CanLogging):
    """
        Game scene. Container for all game objects.
    """
    check_collisions = True
    detect_overlaps = False
    __teams = OrderedDict()

    def __init__(self, name='RoboGame', field=None, theme_mod_path=None, speed=1, headless=False, **kwargs):
        theme.set_theme_module(mod_path=theme_mod_path)
        self.objects = []
        self.time_sleep = theme.GAME_STEP_MIN_TIME
        if speed <= 0:
            raise RobogameException("Game speed can't be zero or negative!")
        elif speed > 1:
            self.game_speed = int(speed)
        else:
            self.game_speed = 1
            self.time_sleep /= speed
        GameObject.link_to_scene(
            scene=self,
            container=self.objects,
        )
        self.init_kwargs = kwargs
        self.hold_state = False  # режим пошаговой отладки
        self.name = name
        self.field = field
        if field:
            theme.FIELD_WIDTH, theme.FIELD_HEIGHT = field
        self.parent_conn = None
        self.ui = None
        self._step = 0
        self.__overlap_map = None
        self.headless = headless

    def register_to_team(self, obj):
        if obj.team not in self.__teams:
            if self.teams_count >= theme.TEAMS_COUNT:
                raise RobogameException(
                    "Only {} teams! Can't create team for {}".format(
                        theme.TEAMS_COUNT, obj.team))
            self.__teams[obj.team] = []
        self.__teams[obj.team].append(obj)

    def get_team_number(self, team):
        if team is None:
            return None
        return list(self.__teams).index(team) + 1

    @property
    def teams(self):
        return self.__teams.copy()

    @property
    def teams_count(self):
        return len(self.__teams)

    def prepare(self, **kwargs):
        pass

    def remove_object(self, obj):
        try:
            self.objects.remove(obj)
        except ValueError:
            self.logger.warning("Try to remove unexists obj {}".format(obj))

    def get_objects_by_type(self, cls=None, cls_name=None):
        if cls:
            return [obj for obj in self.objects if issubclass(obj.__class__, cls)]
        elif cls_name is None:
            raise RobogameException('get_objects_by_type need ether cls or cls_name!')
        return [obj for obj in self.objects if obj.__class__.__name__ == cls_name]

    def game_step(self):
        """
            Proceed objects states, collision detection, hits
            and radars discovering
        """
        self.__overlap_map = self.__get_overlap_map()
        for obj in self.objects:
            obj.proceed_events()
            obj.proceed_commands()
            obj.game_step()
            if self.check_collisions:
                self._check_collisions(obj)
            elif self.detect_overlaps:
                self._detect_overlaps(obj)

    def __get_overlap_map(self):
        overlap_map = defaultdict(list)
        for i, left in enumerate(self.objects):
            for right in self.objects[i+1:]:
                try:
                    if right.owner == left or left.owner == right:
                        continue
                except AttributeError:
                    pass
                summ_radius = left.radius + right.radius
                if abs(left.x - right.x) > summ_radius and abs(left.y - right.y) > summ_radius:
                    continue
                distance = left.distance_to(right)
                overlap_distance = int(summ_radius - distance)
                if overlap_distance > 1:
                    overlap_map[left].append((overlap_distance, right))
                    overlap_map[right].append((overlap_distance, left))
        return overlap_map

    def __get_overlap_objects(self, left):
        return self.__overlap_map.get(left, [])

    def _detect_overlaps(self, left):
        for _, right in self.__get_overlap_objects(left):
            left.add_event(EventOverlap(right))
            right.add_event(EventOverlap(left))

    def _check_collisions(self, left):
        for overlap_distance, right in self.__get_overlap_objects(left):
            module = overlap_distance // 2
            step_back_vector = Vector.from_points(right.coord, left.coord, module=module)
            left.debug('step_back_vector {}'.format(step_back_vector))
            left.coord += step_back_vector
            right.coord -= step_back_vector
            left.add_event(EventCollide(right))
            right.add_event(EventCollide(left))

    def get_objects_status(self):
        # TODO скорее get_statuses
        return dict([(obj.id, ObjectStatus(obj)) for obj in self.objects])

    def get_game_result(self):
        """
        Вычисление результатов игры
        :return: boolean True если надо игру закончить, dict(team=stats, ...) статистика покамандно
        """
        return False, {}

    def go(self):
        """
            Main game cycle - the game begin!
        """
        self.prepare(**self.init_kwargs)
        if not self.headless:
            self.parent_conn, child_conn = Pipe()
            self.ui = Process(target=start_ui, args=(self.name, child_conn, theme.mod_path, self.field))
            self.ui.start()

        is_game_over, game_results = False, {}
        while True:
            cycle_begin = time.time()

            ui_state = None
            if self.parent_conn:
                # проверяем, есть ли новое состояние UI на том конце трубы
                while self.parent_conn.poll(0):
                    # состояний м.б. много, оставляем только последнее
                    ui_state = self.parent_conn.recv()

                # состояние UI изменилось - отрабатываем
                if ui_state:
                    if ui_state.the_end:
                        break

                    for obj in self.objects:
                        obj._selected = obj.id in ui_state.selected_ids

                    # переключение режима отладки
                    if ui_state.switch_debug:
                        if theme.DEBUG:  # были в режиме отладки
                            self.hold_state = False
                        else:
                            self.hold_state = True
                        theme.DEBUG = not theme.DEBUG
            is_game_over, game_results = self.get_game_result()
            if is_game_over:
                if self.parent_conn:
                    self.parent_conn.send(GAME_OVER)
                else:
                    break
            elif (not self.hold_state) or (ui_state and ui_state.one_step):
                # шаг игры, если надо
                self._step += 1
                self.info('Game step {}'.format(self._step))
                self.game_step()
                if self.parent_conn and (self._step % self.game_speed == 0 or (ui_state and ui_state.one_step)):
                    # отсылаем новое состояние обьектов в UI раз в self.game_speed
                    objects_status = self.get_objects_status()
                    self.parent_conn.send(objects_status)
                    # вычисляем остаток времени на сон
                    cycle_time = time.time() - cycle_begin
                    cycle_time_rest = self.time_sleep - cycle_time
                    if cycle_time_rest > 0:
                        # о! есть время поспать... :)
                        time.sleep(cycle_time_rest)

        # ждем пока потомки помрут
        if self.ui:
            self.ui.join()

        print('Thank for playing with robogame! See you in the future :)')
        return game_results


def start_ui(name, child_conn, theme_mod_path, field=None):
    ui = UserInterface(name, theme_mod_path, field)
    ui.run(child_conn)


def random_point():
    x = randint(0, theme.FIELD_WIDTH)
    y = randint(0, theme.FIELD_HEIGHT)
    return Point(x, y)
