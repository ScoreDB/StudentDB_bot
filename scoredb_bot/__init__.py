import logging
from typing import Optional

from pytz import timezone
from telegram.ext import Defaults, Updater

from .commands import register_commands
from .database import get_persistence
from .env import env

TOKEN = env.str('TELEGRAM_TOKEN')

updater: Optional[Updater] = None


def init():
    logging.info('Initializing bot...')

    global updater
    updater = Updater(TOKEN, use_context=True,
                      defaults=Defaults(tzinfo=timezone('Asia/Shanghai')),
                      persistence=get_persistence())

    register_commands(updater.dispatcher)

    logging.info('Bot initialized')


def run():
    if updater is None:
        raise RuntimeError('Please initialize the bot first.')
    updater.start_polling()
    updater.idle()
