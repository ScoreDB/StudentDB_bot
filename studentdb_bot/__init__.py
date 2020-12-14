from environs import Env as _Env

from .database import Database

# Env config
env = _Env()
env.read_env()
