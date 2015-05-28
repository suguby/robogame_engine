#!/usr/bin/env python
# -*- coding: utf-8 -*-
from multiprocessing import Pipe, Process
import time

from robogame_engine import events, constants, GameObject
from robogame_engine.user_interface import UserInterface


class Scene:
    """
        Game scene. Container for all game objects.
    """

    def __init__(self, name, field=None):
        self.objects = []
        GameObject.set_scene(scene=self, container=self.objects)
        self.hold_state = False  # режим пошаговой отладки
        self._step = 0
        self.name = name
        if field is None:
            field = (1200, 600)
        self.field_width, self.field_height = field
        self.parent_conn = None
        self.ui = None

    def game_step(self):
        """
            Proceed objects states, collision detection, hits
            and radars discovering
        """
        for obj in self.objects:
            obj.proceed_events()
            obj.proceed_commands()
            obj.game_step()

    def get_objects_state(self):
        """

        """
        return []

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

                for obj in self.objects:
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


def start_ui(name, child_conn):
    ui = UserInterface(name)
    ui.run(child_conn)