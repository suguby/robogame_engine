#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging

from robogame_engine.user_interface import UserInterface


def start_ui(name, child_conn):
    ui = UserInterface(name)
    ui.run(child_conn)


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

logger = logging.getLogger()