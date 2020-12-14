import logging

from environs import Env

env = Env()
env.read_env()

debug = env.bool('DEBUG', default=False)
logging_level = logging.DEBUG if debug else logging.INFO

logger = logging.getLogger()
logger.setLevel(logging_level)

stream = logging.StreamHandler()
stream.setLevel(logging_level)

formatter = logging.Formatter('[%(asctime)s][%(levelname)s] %(message)s')
stream.setFormatter(formatter)

logger.addHandler(stream)
