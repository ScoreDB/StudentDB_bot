import logging

from environs import Env

env = Env()
env.read_env()
logging.info('Env loaded')
