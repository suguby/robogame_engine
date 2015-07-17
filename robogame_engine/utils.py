#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging
import logging.config
from robogame_engine.theme import theme


def _collide_circle(left, right):
    """
        Detect collision by radius of objects
    """
    return left.distance_to(right) <= left.radius + right.radius


def _overlapped(left, right):
    """
        Is two objects overlapped
    """
    return int((left.radius + right.radius) - left.distance_to(right))


class CanLogging(object):
    __logger = None

    @classmethod
    def get_logger(cls):
        if cls.__logger is None:
            logging.config.dictConfig(theme.LOGGING)
            cls.__logger = logging.getLogger('robogame')
            if theme.DEBUG:
                cls.__logger.setLevel('DEBUG')
            else:
                cls.__logger.setLevel(theme.LOGLEVEL)
        return cls.__logger

    @property
    def logger(self):
        return CanLogging.get_logger()

    def debug(self, pattern, **kwargs):
        self._log(self.logger.debug, pattern, kwargs)

    def info(self, pattern, **kwargs):
        self._log(self.logger.info, pattern, kwargs)

    def warning(self, pattern, **kwargs):
        self._log(self.logger.warning, pattern, kwargs)

    def error(self, pattern, **kwargs):
        self._log(self.logger.error, pattern, kwargs)

    def _log(self, log_fun, pattern, kwargs):
        kwargs['cls'] = self.__class__.__name__
        kwargs.update(self.__dict__)
        if 'id' in kwargs:
            pattern = '{cls}:{id}: ' + pattern
        else:
            pattern = '{cls}: ' + pattern
        log_fun(pattern.format(**kwargs))
