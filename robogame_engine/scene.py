#!/usr/bin/env python
# -*- coding: utf-8 -*-
from multiprocessing import Pipe, Process
import time

from core import _in_radar_fork, start_ui
from objects import ObjectState
from robogame_engine import events, constants
import geometry
import objects


class Scene:
    """
        Game scene. Container for all game objects.
    """

    def __init__(self, name):
        self.grounds = []
        self.shots = []
        self.explosions = []

        objects.Shot.container = self.shots
        objects.Explosion.container = self.explosions
        objects.Tank.container = self.grounds

        self.hold_state = False  # режим пошаговой отладки
        self._step = 0
        self.name = name

    def game_step(self):
        """
            Proceed objects states, collision detection, hits
            and radars discovering
        """
        for obj in self.grounds + self.shots:
            obj._distance_cache = {}
        for obj in self.grounds:
            obj._radar_detected_objs = []
            obj._detected_by = []
        searched_left_ids = []
        for left in self.grounds[:]:
            #~ searched_left_ids.append(left.id)
            left.debug(">>> start proceed at scene step")
            left.debug(str(left))
            for right in self.grounds[:]:
                if (right.id == left.id) or (right.id in searched_left_ids):
                    continue
                distance = left.distance_to(right)
                # коллизии
                overlap_distance = int(left.radius + right.radius - distance)
                if overlap_distance > 1:
                    # могут пересекаться одним пикселем
                    step_back_vector = geometry.Vector(right,
                                                       left,
                                                       overlap_distance // 2)
                    left.debug('step_back_vector %s', step_back_vector)
                    left.coord.add(step_back_vector)
                    right.coord.add(-step_back_vector)
                    left._events.put(events.EventCollide(right))
                    right._events.put(events.EventCollide(left))
                # радары
                if distance < constants.tank_radar_range:
                    left.debug("distance < constants.tank_radar_range for %s",
                               right.id)
                    if _in_radar_fork(left, right):
                        left.debug("see %s", right.id)
                        if right.armor > 0:
                            left._radar_detected_objs.append(right)
                            right._detected_by.append(left)
            # попадания (список летяших снарядов может уменьшаться)
            for shot in self.shots[:]:
                if shot.owner and shot.owner == left:
                    continue
                if _collide_circle(shot, left):
                    left.hit(shot)
                    shot.detonate_at(left)
                    # self.shots.remove(shot)
        # после главного цикла - евенты могут меняться
        for obj in self.grounds:
            if obj._radar_detected_objs:
                radar_event = events.EventRadarRange(obj._radar_detected_objs)
                obj._events.put(radar_event)
            obj._proceed_events()
            obj._game_step()

        for obj in self.shots + self.explosions:
            obj._game_step()

    def get_objects_state(self):
        objects_state = {}
        for obj in self.grounds + self.shots + self.explosions:
            objects_state[obj.id] = ObjectState(obj)
        return objects_state

    def go(self):
        """
            Main game cycle - the game begin!
        """
        self.parent_conn, child_conn = Pipe()
        self.ui = Process(target=start_ui, args=(self.name, child_conn,))
        self.ui.start()

        while True:
            cycle_begin = time.time()

            # проверяем, есть ли новое состояние UI на том конце трубы
            ui_state = None
            while self.parent_conn.poll(0):
                # состояний м.б. много, оставляем только последнее
                ui_state = self.parent_conn.recv()

            # состояние UI изменилось - отрабатываем
            if ui_state:
                if ui_state.the_end:
                    break

                for obj in self.grounds:
                    obj._selected = obj.id in ui_state.selected_ids

                # переключение режима отладки
                if ui_state.switch_debug:
                    if common._debug:  # были в режиме отладки
                        self.hold_state = False
                    else:
                        self.hold_state = True
                    common._debug = not common._debug

            # шаг игры, если надо
            if not self.hold_state or (ui_state and ui_state.one_step):
                self._step += 1
                self.game_step()
                # отсылаем новое состояние обьектов в UI
                objects_state = self.get_objects_state()
                self.parent_conn.send(objects_state)

            # вычисляем остаток времени на сон
            cycle_time = time.time() - cycle_begin
            cycle_time_rest = constants.GAME_STEP_MIN_TIME - cycle_time
            if cycle_time_rest > 0:
                # о! есть время поспать... :)
                # print "sleep for %.6f" % cycle_time_rest
                time.sleep(cycle_time_rest)

        # ждем пока потомки помрут
        self.ui.join()

        print 'Thank for playing robopycode! See you in the future :)'

