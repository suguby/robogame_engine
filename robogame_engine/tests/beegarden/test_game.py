# -*- coding: utf-8 -*-

import math
import random

from robogame_engine import GameObject, Scene
from robogame_engine.constants import ROTATE_FLIP_VERTICAL
from robogame_engine.geometry import Point
from robogame_engine.states import StateMoving
from robogame_engine.theme import theme


class HoneyHolder:
    """Класс объекта, который может нести мёд"""
    _honey_speed = 1
    _honey = 0
    _max_honey = 0
    _honey_source = None
    _honey_state = 'hold'

    def set_inital_honey(self, loaded, maximum):
        """Задать начальние значения: honey_loaded - сколько изначально мёда, honey_max - максимум"""
        self._honey = loaded
        if maximum == 0:
            raise Exception("honey_max can't be zero!")
        self._max_honey = maximum

    @property
    def honey(self):
        return self._honey

    @property
    def meter_1(self):
        return self._honey / float(self._max_honey)

    def _end_exchange(self, event):
        self._honey_source = None
        self._honey_state = 'hold'
        event()

    def _stop_loading_honey(self):
        self._honey_source = None
        self._honey_state = 'hold'

    def _update(self, is_moving=False):
        """Внутренняя функция для обновления переменных отображения"""
        if is_moving or (self._honey_source and not self.near(self._honey_source)):
            self._stop_loading_honey()
        elif self._honey_state == 'loading':
            honey = self._honey_source._get_honey()
            if not honey or not self._put_honey(honey):
                self._end_exchange(event=self.on_honey_loaded)
        elif self._honey_state == 'unloading':
            honey = self._get_honey()
            if not honey or not self._honey_source._put_honey(honey):
                self._end_exchange(event=self.on_honey_unloaded)

    def _get_honey(self):
        if self._honey > self._honey_speed:
            self._honey -= self._honey_speed
            return self._honey_speed
        elif self._honey > 0:
            value = self._honey
            self._honey = 0
            return value
        return 0.0

    def _put_honey(self, value):
        self._honey += value
        if self._honey > self._max_honey:
            self._honey = self._max_honey
            return False
        return True

    def on_honey_loaded(self):
        """Обработчик события 'мёд загружен' """
        pass

    def on_honey_unloaded(self):
        """Обработчик события 'мёд разгружен' """
        pass

    def load_honey_from(self, source):
        """Загрузить мёд от ... """
        self._honey_state = 'loading'
        self._honey_source = source

    def unload_honey_to(self, target):
        """Разгрузить мёд в ... """
        self._honey_state = 'unloading'
        self._honey_source = target

    def is_full(self):
        """полностью заполнен?"""
        return self.honey >= self._max_honey


class SceneObjectsGetter:
    _objects_holder = None
    __flowers = None
    __bees = None
    __beehives = None

    @property
    def flowers(self):
        if self.__flowers is None:
            self.__flowers = self._objects_holder.get_objects_by_type(cls=Flower)
        return self.__flowers

    @property
    def bees(self):
        if self.__bees is None:
            self.__bees = self._objects_holder.get_objects_by_type(cls=Bee)
        return self.__bees

    @property
    def beehives(self):
        if self.__beehives is None:
            self.__beehives = self._objects_holder.get_objects_by_type(cls=BeeHive)
        return self.__beehives


class Bee(HoneyHolder, GameObject, SceneObjectsGetter):
    _MAX_HONEY = 100
    _sprite_filename = 'bee.png'
    rotate_mode = ROTATE_FLIP_VERTICAL
    radius = 44
    _part_of_team = True
    __my_beehive = None

    def __init__(self, pos=None):
        super(Bee, self).__init__(pos=self.my_beehive)
        self.set_inital_honey(loaded=0, maximum=self._MAX_HONEY)
        self._objects_holder = self._scene

    @property
    def sprite_filename(self):
        return 'bee-{}.png'.format(self.team)

    @property
    def my_beehive(self):
        if self.__my_beehive is None:
            try:
                self.__my_beehive = self._scene.get_beehive(team=self.team)
            except IndexError:
                raise Exception("No beehive for {} - check beehives_count!".format(self.__class__.__name__))
        return self.__my_beehive

    def game_step(self):
        super(Bee, self).game_step()
        self._update(is_moving=isinstance(self.state, StateMoving))

    def on_stop_at_target(self, target):
        """Обработчик события 'остановка у цели' """
        if isinstance(target, Flower):
            self.on_stop_at_flower(target)
        elif isinstance(target, BeeHive):
            self.on_stop_at_beehive(target)
        else:
            pass

    def on_stop_at_flower(self, flower):
        pass

    def on_stop_at_beehive(self, beehive):
        pass


class Flower(HoneyHolder, GameObject):
    radius = 50
    selectable = False
    _MIN_HONEY = 100
    _MAX_HONEY = 200
    counter_attrs = dict(size=20, position=(43, 45), color=(128, 128, 128))

    def __init__(self, pos, max_honey=None):
        super(Flower, self).__init__(pos=pos)
        if max_honey is None:
            max_honey = random.randint(self._MIN_HONEY, self._MAX_HONEY)
        self.set_inital_honey(loaded=max_honey, maximum=max_honey)

    def update(self):
        pass

    @property
    def counter(self):
        return self.honey


class BeeHive(HoneyHolder, GameObject):
    radius = 75
    selectable = False
    counter_attrs = dict(size=30, position=(60, 92), color=(255, 255, 0))

    def __init__(self, pos, max_honey):
        super(BeeHive, self).__init__(pos=pos)
        self.set_inital_honey(loaded=0, maximum=max_honey)

    @property
    def counter(self):
        return self.honey


class Rect:

    def __init__(self, x=0, y=0, w=10, h=10):
        self.x = x
        self.y = y
        self.w = w
        self.h = h

    def reduce(self, dw=0, dh=0):
        self.w -= dw
        self.h -= dh

    def shift(self, dx=0, dy=0):
        self.x += dx
        self.y += dy

    def __str__(self):
        return "{}x{} ({}, {})".format(self.w, self.h, self.x, self.y)


class Beegarden(Scene, SceneObjectsGetter):
    check_collisions = False
    _FLOWER_JITTER = 0.7
    _HONEY_SPEED_FACTOR = 0.02
    __beehives = []

    def prepare(self, flowers_count=5, beehives_count=1):
        self._place_flowers_and_beehives(
            flowers_count=flowers_count,
            beehives_count=beehives_count,
        )
        self._objects_holder = self
        honey_speed = int(self._max_speed * self._HONEY_SPEED_FACTOR)
        if honey_speed < 1:
            honey_speed = 1
        HoneyHolder._honey_speed = honey_speed

    def _place_flowers_and_beehives(self, flowers_count, beehives_count):
        if beehives_count > theme.TEAMS_COUNT:
            raise Exception('Only {} beehives!'.format(theme.TEAMS_COUNT))

        field = Rect(w=theme.FIELD_WIDTH, h=theme.FIELD_HEIGHT)
        field.reduce(dw=BeeHive.radius * 2, dh=BeeHive.radius * 2)
        if beehives_count >= 2:
            field.reduce(dw=BeeHive.radius * 2)
        if beehives_count >= 3:
            field.reduce(dh=BeeHive.radius * 2)
        if field.w < Flower.radius or field.h < Flower.radius:
            raise Exception("Too little field...")
        if theme.DEBUG:
            print "Initial field", field

        cells_in_width = int(math.ceil(math.sqrt(float(field.w) / field.h * flowers_count)))
        cells_in_height = int(math.ceil(float(flowers_count) / cells_in_width))
        cells_count = cells_in_height * cells_in_width
        if theme.DEBUG:
            print "Cells count", cells_count, cells_in_width, cells_in_height
        if cells_count < flowers_count:
            print u"Ну я не знаю..."

        cell = Rect(w=field.w / cells_in_width, h=field.h / cells_in_height)

        if theme.DEBUG:
            print "Adjusted cell", cell

        cell_numbers = [i for i in range(cells_count)]

        jit_box = Rect(w=int(cell.w * self._FLOWER_JITTER), h=int(cell.h * self._FLOWER_JITTER))
        jit_box.shift(dx=(cell.w - jit_box.w) // 2, dy=(cell.h - jit_box.h) // 2)
        if theme.DEBUG:
            print "Jit box", jit_box

        field.w = cells_in_width * cell.w + jit_box.w
        field.h = cells_in_height * cell.h + jit_box.h
        if theme.DEBUG:
            print "Adjusted field", field

        field.x = BeeHive.radius * 2
        field.y = BeeHive.radius * 2
        if theme.DEBUG:
            print "Shifted field", field

        max_honey = 0
        i = 0
        while i < flowers_count:
            cell_number = random.choice(cell_numbers)
            cell_numbers.remove(cell_number)
            cell.x = (cell_number % cells_in_width) * cell.w
            cell.y = (cell_number // cells_in_width) * cell.h
            dx = random.randint(0, jit_box.w)
            dy = random.randint(0, jit_box.h)
            pos = Point(field.x + cell.x + dx, field.y + cell.y + dy)
            flower = Flower(pos)
            max_honey += flower.honey
            i += 1
        max_honey /= float(beehives_count)
        max_honey = int(round((max_honey / 1000.0) * 1.3)) * 1000
        if max_honey < 1000:
            max_honey = 1000
        for team in range(beehives_count):
            if team == 0:
                pos = Point(90, 75)
            elif team == 1:
                pos = Point(theme.FIELD_WIDTH - 90, 75)
            elif team == 2:
                pos = Point(90, theme.FIELD_HEIGHT - 75)
            else:
                pos = Point(theme.FIELD_WIDTH - 90, theme.FIELD_HEIGHT - 75)
            beehive = BeeHive(pos=pos, max_honey=max_honey)
            self.__beehives.append(beehive)

    def get_beehive(self, team):
        return self.__beehives[team - 1]


class WorkerBee(Bee):
    all_bees = []

    def is_other_bee_target(self, flower):
        for bee in WorkerBee.all_bees:
            if hasattr(bee, 'flower') and bee.flower and bee.flower.id == flower.id:
                return True
        return False

    def get_nearest_flower(self):
        flowers_with_honey = [flower for flower in self.flowers if flower.honey > 0]
        if not flowers_with_honey:
            return None
        nearest_flower = None
        for flower in flowers_with_honey:
            if self.is_other_bee_target(flower):
                continue
            if nearest_flower is None or self.distance_to(flower) < self.distance_to(nearest_flower):
                nearest_flower = flower
        return nearest_flower

    def go_next_flower(self):
        if self.is_full():
            self.move_at(self.my_beehive)
        else:
            self.flower = self.get_nearest_flower()
            if self.flower is not None:
                self.move_at(self.flower)
            elif self.honey > 0:
                self.move_at(self.my_beehive)
            else:
                i = random.randint(0, len(self.flowers) - 1)
                self.move_at(self.flowers[i])

    def on_born(self):
        WorkerBee.all_bees.append(self)
        self.go_next_flower()

    def on_stop_at_flower(self, flower):
        for bee in self.bees:
            if not isinstance(bee, self.__class__) and self.near(bee):
                self.sting(bee)
        else:
            if flower.honey > 0:
                self.load_honey_from(flower)
            else:
                self.go_next_flower()

    def on_honey_loaded(self):
        self.go_next_flower()

    def on_stop_at_beehive(self, beehive):
        self.unload_honey_to(beehive)

    def on_honey_unloaded(self):
        self.go_next_flower()

    def sting(self, bee):
        pass


class GreedyBee(WorkerBee):

    def get_nearest_flower(self):
        flowers_with_honey = [flower for flower in self.flowers if flower.honey > 0]
        if not flowers_with_honey:
            return None
        nearest_flower = None
        max_honey = 0
        for flower in flowers_with_honey:
            if self.is_other_bee_target(flower):
                continue
            if flower.honey > max_honey:
                nearest_flower = flower
                max_honey = flower.honey
        if nearest_flower:
            return nearest_flower
        return random.choice(flowers_with_honey)


class NextBee(GreedyBee):
    pass


class Next2Bee(GreedyBee):
    pass


if __name__ == '__main__':
    beegarden = Beegarden(
        name="My little garden",
        beehives_count=4,
        flowers_count=80,
        speed=3,
        # field=(800, 600),
        # theme_mod_path='dark_theme',
    )

    count = 10
    bees = [WorkerBee(pos=Point(400,400)) for i in range(count)]
    bees_2 = [GreedyBee() for i in range(count)]
    bees_3 = [NextBee() for i in range(count)]
    bees_4 = [Next2Bee() for i in range(count)]

    bee = WorkerBee()
    bee.move_at(Point(1000, 1000))  # проверка на выход за границы экрана

    beegarden.go()
