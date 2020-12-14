import logging

from environs import Env as _Env

from .database import Database

# Logging config
logging.basicConfig(format='[%(asctime)s][%(levelname)s] %(message)s',
                    level=logging.INFO)

# Env config
env = _Env()
env.read_env()
logging.info('Env loaded.')
