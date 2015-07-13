# -*- coding: utf-8 -*-
from importlib import import_module
from robogame_engine import constants


class Theme(object):
    mod_path = None
    module = constants

    def set_theme_module(self, mod_path=None):
        self.mod_path = 'default_theme' if mod_path is None else mod_path
        try:
            self.module = import_module(self.mod_path)
        except ImportError:
            raise Exception("Can't load theme {}".format(self.mod_path))

    def __getattr__(self, item):
        if item not in self.__dict__:
            try:
                value = getattr(self.module, item)
            except AttributeError:
                try:
                    value = getattr(constants, item)
                except AttributeError:
                    raise AttributeError(
                        "No constant {} in theme {} and constants".format(
                            item, self.mod_path
                        ))
            self.__dict__[item] = value
        return self.__dict__[item]  # todo через setattr

theme = Theme()
