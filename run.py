#!/usr/bin/env python3

import logging

from environs import Env

import scoredb_bot

env = Env()
env.read_env()

debug = env.bool('DEBUG', default=False)
logging_level = logging.DEBUG if debug else logging.INFO

logger = logging.getLogger()
logger.setLevel(logging_level)

stream = logging.StreamHandler()
stream.setLevel(logging_level)

formatter = logging.Formatter('[%(asctime)s][%(levelname)s] (%(module)s) %(message)s')
stream.setFormatter(formatter)

logger.handlers = []
logger.addHandler(stream)

scoredb_bot.init()
scoredb_bot.run()
