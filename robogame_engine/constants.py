#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os

BACKGROUND_COLOR = (85, 107, 47)
PICTURES_PATH = os.path.join(os.path.dirname(__file__), 'data')

TURN_SPEED = 5
MAX_SPEED = 5
HEARTBEAT_INTERVAL = 5

# engine constants
GAME_STEP_MIN_TIME = 0.015
NEAR_RADIUS = 20

DEBUG = False

try:
    from .costants_local import *
except ImportError:
    pass