#!/usr/bin/env python
# -*- coding: utf-8 -*-
from multiprocessing import Pipe, Process
import time

from robogame_engine.objects import ObjectStatus, GameObject
from robogame_engine.theme import theme
from robogame_engine.user_interface import UserInterface


class Scene:
    """
        Game scene. Container for all game objects.
    """

    def __init__(self, name='RoboGame', field=None, theme_mod_path=None, **kwargs):
        self.objects = []
        GameObject.set_scene(scene=self, container=self.objects)
        theme.set_theme_module(mod_path=theme_mod_path)
        self.hold_state = False  # режим пошаговой отладки
        self._step = 0
        self.name = name
        if field is None:
            field = (1200, 600)
        self.field_width, self.field_height = field
        self.parent_conn = None
        self.ui = None
        self.prepare(**kwargs)

    def prepare(self, **kwargs):
        raise NotImplementedError()

    def get_objects_by_type(self, cls):
        return [obj for obj in self.objects if isinstance(obj, cls)]

    def game_step(self):
        """
            Proceed objects states, collision detection, hits
            and radars discovering
        """
        for obj in self.objects:
            obj.proceed_events()
            obj.proceed_commands()
            obj.game_step()

    def get_objects_status(self):
        """

        """
        return [ObjectStatus(obj) for obj in self.objects]

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
                    if theme.DEBUG:  # были в режиме отладки
                        self.hold_state = False
                    else:
                        self.hold_state = True
                    theme.DEBUG = not theme.DEBUG

            # шаг игры, если надо
            if not self.hold_state or (ui_state and ui_state.one_step):
                self._step += 1
                self.game_step()
                # отсылаем новое состояние обьектов в UI
                objects_status = self.get_objects_status()
                self.parent_conn.send(objects_status)

            # вычисляем остаток времени на сон
            cycle_time = time.time() - cycle_begin
            cycle_time_rest = theme.GAME_STEP_MIN_TIME - cycle_time
            if cycle_time_rest > 0:
                # о! есть время поспать... :)
                time.sleep(cycle_time_rest)

        # ждем пока потомки помрут
        self.ui.join()

        print 'Thank for playing robopycode! See you in the future :)'


def start_ui(name, child_conn):
    ui = UserInterface(name, theme)
    ui.run(child_conn)
