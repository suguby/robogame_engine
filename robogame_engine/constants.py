#!/usr/bin/env python
# -*- coding: utf-8 -*-

TURN_SPEED = 5
MAX_SPEED = 5
HEARTBEAT_INTERVAL = 5
MAX_LAYERS = 5

GAME_STEP_MIN_TIME = 0.015
NEAR_RADIUS = 20

DEBUG = False

ROTATE_TURNING = 'TURNING'
ROTATE_FLIP_VERTICAL = 'FLIP_VERTICAL'
ROTATE_FLIP_HORIZONTAL = 'FLIP_HORIZONTAL'
ROTATE_FLIP_BOTH = 'FLIP_BOTH'
ROTATE_NO_TURN = 'NO_TURN'

BACKGROUND_COLOR = (128, 128, 128)

LOGGING = {
    'version': 1,
    # 'disable_existing_loggers': False,
    'formatters': {
        'console': {
            'format': "[%(levelname)s]: %(message)s",
            'datefmt': "%Y-%m-%d %I:%M:%S"
        },
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'console',
        },
    },
    'loggers': {
        'robogame': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
    }
}
LOGLEVEL = 'WARNING'
