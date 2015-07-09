# -*- coding: utf-8 -*-

import math
import random

from robogame_engine import GameObject, Scene
from robogame_engine.constants import ROTATE_FLIP_VERTICAL, ROTATE_TURNING
from robogame_engine.geometry import Point, Vector
from robogame_engine.states import StateMoving
from robogame_engine.theme import theme


class Gun:
    states = ['reloading', 'loaded']

    def __init__(self, owner):
        self.owner = owner
        self.heat = 8
        self._state = 'reloading'

    def _game_step(self):
        """
            Internal function
        """
        if self._state == 'reloading':
            self.heat -= 1
            if not self.heat:
                # перезарядка только что кончилась
                self.owner._events.put(EventGunReloaded())
                self._state = 'loaded'

    def fire(self):
        """
            Fire from gun
        """
        if self._state == 'loaded':
            start_point = Point(self.owner.coord) + \
                          Vector(self.owner.course,
                                          self.owner.radius // 2 + 12)
            shot = Shot(pos=start_point, direction=self.owner.course)
            self.heat = tank_gun_heat_after_fire
            self._state = 'reloading'
            return shot


class Tank(GameObject):
    """
        Tank. May ride on the screen.
    """
    radius = 32
    rotate_mode = ROTATE_TURNING
    selectable = True

    _sprite_filename = 'tank_blue.png'
    _layer = 2

    def __init__(self, pos=None, angle=None):
        """
            create a tank in a specified point on the screen
        """
        GameObject.__init__(self, pos)
        self.gun = Gun(self)
        self._armor = float(theme.TANK_MAX_ARMOR)
        self.explosion = None
        self._events.put(EventBorn())

    @property
    def armor(self):
        return int(self._armor)

    @property
    def gun_heat(self):
        return self.gun.heat

    def _game_step(self):
        """
            Internal function to update the state variables
        """
        if self._armor < tank_max_armor:
            self._armor += tank_armor_renewal_rate
        self.gun._game_step()
        self._update_explosion()
        GameObject._game_step(self)

    def _update_explosion(self):
        """
            Renew exploison at the armor - it must moving with as
        """
        if self.explosion:
            self.explosion.coord = Point(self.coord)
            self.debug("tank course %s explosion.vector.angle %s "
                       "explosion.coord %s", self.course,
                       self.explosion.vector.angle, self.explosion.coord)
            expl_shift = Vector(self.course
                                         + self.explosion.vector.angle,
                                         self.explosion.vector.module)
            self.explosion.coord.add(expl_shift)
            self.debug("after add explosion is %s", self.explosion)

    def fire(self):
        """
            Make shot.
        """
        self.shot = self.gun.fire()
        if self.shot:
            self.shot.owner = self

    def detonate(self):
        """
            Suicide
        """
        self.stop()
        Explosion(self.coord, self)  # взрыв на нашем месте
        if self in self.container:
            self.container.remove(self)

    def hit(self, shot):
        """
            Contact with our tank shell
        """
        self._armor -= shot.power
        self._events.put(EventHit())
        if self._armor <= 0:
            if shot.owner:  # еще не был убит
                shot.owner._events.put(EventTargetDestroyed())
            self.detonate()

    def born(self):
        """
            Event: born
        """
        pass

    def stopped(self):
        """
            Event: stopped
        """
        pass

    def stopped_at_target_point(self, point):
        """
            Event: stopped near the target
        """
        pass

    def gun_reloaded(self):
        """
            Event: the gun is ready to fire
        """
        pass

    def hitted(self):
        """
            Event: contact with our tank shell
        """
        pass

    def collided_with(self, obj):
        """
            Event: contact with our tank shell
        """
        pass

    def target_destroyed(self):
        """
            Event: contact with our tank shell
        """
        pass

    def in_tank_radar_range(self, objects):
        """
            Event: contact with our tank shell
        """
        pass


class StaticTarget(Tank):
    """
        A static target
    """
    _img_file_name = 'tank_red.png'
    _selectable = False  # обьект нельзя выделить мышкой

    def __init__(self, pos=None, angle=None, auto_fire=False):
        Tank.__init__(self, pos=pos, angle=angle)
        self.auto_fire = auto_fire

    def gun_reloaded(self):
        if self.auto_fire:
            self.fire()


class Target(Tank):
    """
        A target
    """
    _img_file_name = 'tank_red.png'
    _selectable = False  # обьект нельзя выделить мышкой

    def __init__(self, pos=None, angle=None, auto_fire=False):
        Tank.__init__(self, pos=pos, angle=angle)
        self.auto_fire = auto_fire

    def born(self):
        self.move_at(target=random_point())

    def stopped(self):
        self.debug("stopped")
        self.move_at(target=random_point())

    def gun_reloaded(self):
        self.debug("gun_reloaded")
        if self.auto_fire:
            self.fire()

    def collided_with(self, obj):
        self.debug("collided_with %s", obj.id)
        self.move_at(target=random_point())


class Shot(GameObject):
    """
        The shell. Flies in a straight until it hits the target.
    """
    _img_file_name = 'shot.png'
    _layer = 3
    radius = 4  # collision detect
    _selectable = False  # обьект нельзя выделить мышкой

    def __init__(self, pos, direction):
        """
            Start a shell from a specified point in the direction of the

            Zapustit' snarjad iz ukazannoj tochki v ukazannom napravlenii
        """
        GameObject.__init__(self, pos, revolvable=False)
        self.move(direction, shot_speed)
        self.life = shot_life
        self.power = shot_power

    def detonate_at(self, obj):
        """
            Explosion!
        """
        SmallExplosion(self.coord, obj)  # взрыв на месте снаряда
        self.container.remove(self)
        if self.owner:
            self.owner.shot = None
            self.owner = None

    def _game_step(self):
        self.debug('%s', self)
        self.life -= 1
        if not self.life or not self._state == 'moving':
            self.owner.shot = None
            self.container.remove(self)
        GameObject._game_step(self)


class Explosion(GameObject):
    """
        The explosion of the tank.
    """
    # TODO подумать куда отнести взрывы,
    # TODO ведь в игоровой механике они не участвуют
    _img_file_name = 'explosion.png'
    _layer = user_interface._max_layers
    radius = 0  # collision detect
    defaultlife = 12
    animcycle = 3
    _selectable = False  # обьект нельзя выделить мышкой
    _animated = True  # надо анимировать обьект TODO сделать анимацию в гифке

    def __init__(self, explosion_coord, hitted_obj):
        GameObject.__init__(self, explosion_coord, revolvable=False)
        self.vector = Vector(hitted_obj.coord, explosion_coord)
        self.vector.angle -= hitted_obj.course  # смещение при отображении
        self.owner = hitted_obj
        self.owner.explosion = self
        self.owner._update_explosion()
        self.life = self.defaultlife

    def _game_step(self):
        self.life -= 1
#        self.image = self.images[self.life // self.animcycle % 2]
        if self.life <= 0:
            self.container.remove(self)
            self.owner.explosion = None
            self.owner = None
        GameObject._game_step(self)


class SmallExplosion(Explosion):
    """
        The explosion of the shell.
    """
    _img_file_name = 'small_explosion.png'


class SimpleTank(Tank):
    _img_file_name = 'tank_blue.png'

    def turn_around(self):
        self.turn_to(self.course + 180)

    def run_away(self, obj):
        to_obj_vector = Vector(self, obj)
        self.move(to_obj_vector.angle + 180, speed=5)

    def to_search(self):
        self.state = 'search'
        self.target = None
        self.move_at(random_point())

    def to_hunt(self, target_candidate):
        self.target = target_candidate
        self.state = 'hunt'
        if self.distance_to(self.target) > 100:
            self.move_at(self.target)
        else:
            self.turn_to(self.target)
        self.fire()

    def make_decision(self, objects=None):
        """
            Принять решение, охотиться ли за обьектами
        """
        target_candidate = None
        if self.target:
            distance_to_target = self.distance_to(self.target)
        else:
            distance_to_target = 100000
        for obj in objects:
            if not isinstance(obj, self.__class__):
                distance_to_candidate = self.distance_to(obj)
                if distance_to_candidate < distance_to_target:
                    target_candidate = obj
                    distance_to_target = distance_to_candidate
        if self.state == 'search':
            if target_candidate:
                self.to_hunt(target_candidate)
        elif self.state == 'hunt':
            if target_candidate:
                self.to_hunt(target_candidate)
            else:
                if self.target:
                    self.to_hunt(self.target)
                else:
                    self.to_search()

    def born(self):
        self.to_search()

    def stopped(self):
        self.to_search()

    def stopped_at_target(self):
        self.to_search()

    def gun_reloaded(self):
        if self.state == 'hunt':
            if self.target and self.target.armor > 0:
                self.fire()
            else:
                self.to_search()

    def target_destroyed(self):
        self.to_search()

    def collided_with(self, obj):
        self.debug("collided_with state %s", self.state)
        if self.state == 'search':
            self.make_decision(objects=[obj])

    def in_tank_radar_range(self, objects):
        for obj in objects:
            self.debug("in radar obj with armor %s", obj.armor)
        self.debug("in_tank_radar_range state %s target",
            self.state, self.target)
        self.make_decision(objects)

    def hearbeat(self):
        self.debug("hearbeat")


class CooperativeTank(Tank):
    """Танк. Может ездить по экрану."""
    _img_file_name = 'tank_green.png'
    all_tanks = []
    target = None
    _min_armor = 50
    _min_distance_to_target = 150
    state = 'at_home'
    retreat_point = Point(100, constants.field_height - 100)

    def born(self):
        self.__class__.all_tanks.append(self)
        self.determine_state()

    def stopped(self):
        self.determine_state()

    def stopped_at_target_point(self, point):
        self.determine_state()

    def gun_reloaded(self):
        self.determine_state()

    def hitted(self):
        self.determine_state()

    def hearbeat(self):
        self.debug("hearbeat")
        self.determine_state()

    def in_tank_radar_range(self, objects):
        self.determine_target(objects)
        self.determine_state()

    def determine_target(self, objects):
        self.target = None
        friends, enemies = [], []
        for obj in objects:
            if self.is_friend(obj):
                friends.append(obj)
            else:
                enemies.append(obj)
        if enemies:
            self.target = self._get_nearest_obj(enemies)
            nearest_friend = self._get_nearest_obj(friends)
            if nearest_friend and self.distance_to(nearest_friend) < self.distance_to(self.target):
                self.target = None

    def follow_target(self, with_move=True):
        if self.is_near_target():
            self.debug("near_target - turned to %s" % self.target)
            self.turn_to(self.target)
            self.fire()
            self.state = 'hunt'
        elif with_move:
            if self.target:
                self.debug("target far away - move to")
                self.move_at(self.target)
                self.state = 'folow_target'
            else:
                self.debug("no target - random")
                self.state = 'search'
                self.move_at(random_point())
        else:
            self.debug("target far away and no move - dancing")
            self.turn_to(self.course + 90)
            self.state = 'search'

    def is_at_home(self):
        return self.distance_to(self.retreat_point) < 50 and self.armor < 90

    def is_near_target(self):
        return (self.target
                and self.target.armor > 0
                and self.distance_to(self.target) < self._min_distance_to_target
            )

    def is_friend(self, obj):
        return isinstance(obj, self.__class__)

    def is_need_retreat(self):
        return self.armor < self._min_armor

    def determine_state(self):
        if self.is_at_home():
            self.debug("at_home")
            self.follow_target(with_move=False)
        elif self.is_need_retreat():
            self.debug("need_retreat")
            self.target = None
            self.move_at(self.retreat_point)
        elif self.target:
            self.debug("i alive and have target")
            self.follow_target()
        else:
            self.debug("check friends targets")
            self.target = None
            for tank in self.__class__.all_tanks:
                if tank is self:
                    continue
                if tank.target and tank.target.armor > 0:
                    self.target = tank.target
                    break
            self.follow_target()

    def _get_nearest_obj(self, objects):
        if objects:
            nearest_obj = objects[0]
            for obj in objects[1:]:
                if self.distance_to(obj) < self.distance_to(nearest_obj):
                    nearest_obj = obj
            return nearest_obj
        return None



class Battlezone(Scene):
    check_collisions = False
    _FLOWER_JITTER = 0.7
    _HONEY_SPEED_FACTOR = 0.02
    __beehives = []

    def prepare(self):
        self._objects_holder = self

if __name__ == '__main__':
    battlezone = Battlezone(
        name="Battlezone: To the dust!",
        # field=(800, 600),
        # theme_mod_path='dark_theme',
    )

    count = 10
    deploy1 = Point(constants.field_width - 100, 100)
    army_1 = [SimpleTank(pos=deploy1) for i in range(5)]

    deploy2 = Point(100, constants.field_height - 100)
    army_2 = [CooperativeTank(pos=deploy2) for i in range(5)]

    deploy3 = Point(100, 100)
    targets = [Target(pos=deploy3) for i in range(4)]
    targets += [Target(pos=deploy3, auto_fire=True) for i in range(4)]

    second_pos = (constants.field_width - 20, constants.field_height - 20)
    targets += [
        StaticTarget(pos=(20, 20), angle=90),
        StaticTarget(pos=second_pos, angle=-90, auto_fire=True)
    ]

    battlezone.go()
