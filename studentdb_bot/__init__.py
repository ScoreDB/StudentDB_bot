from ._bot import init as _init, run
from ._database import update_database

_init()

__all__ = [
    update_database,
    run
]
