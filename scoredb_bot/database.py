import logging
from pathlib import Path

from telegram.ext import PicklePersistence


def get_persistence():
    persistence_file = Path(__file__).resolve().parent.parent / 'data/persistence.db'
    logging.info(f'Using persistence at "{persistence_file}"')
    return PicklePersistence(persistence_file)
