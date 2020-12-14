import logging
from pathlib import Path

from sqlalchemy import create_engine

from ._database_models import Base


class Database:

    def __init__(self):
        path = Path(__file__).resolve().parent.parent / 'database/database.sqlite'
        enable_echo = logging.getLogger().level <= logging.DEBUG
        self.engine = create_engine(f'sqlite:///{path}', echo=enable_echo)
        logging.info(f'Using database at "{path}"')
        Base.metadata.create_all(self.engine)
        logging.debug(f'Tables created')

    def get_user(self, user_id: int):
        pass
