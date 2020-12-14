import json
import logging
from pathlib import Path
from typing import Optional

from telegram import Update, InlineKeyboardButton, \
    InlineKeyboardMarkup
from telegram.ext import Updater, CallbackContext, \
    CallbackQueryHandler, CommandHandler, \
    PicklePersistence

from ._database import Database
from ._env import env
from ._messages import messages

with env.prefixed('TELEGRAM_'):
    TOKEN = env.str('TOKEN')

database = Database()
updater: Optional[Updater] = None


def init():
    global updater

    persistence_file = Path(__file__).resolve().parent.parent / 'database/persistence.db'
    persistence = PicklePersistence(persistence_file)
    logging.info(f'Using persistence at "{persistence_file}"')
    updater = Updater(TOKEN, persistence=persistence, use_context=True)
    dispatcher = updater.dispatcher

    def start(update: Update, context: CallbackContext):
        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text=messages['introMsg'])
        if not context.user_data.get('auth_pass', False):
            button = InlineKeyboardButton('开始认证', callback_data=json.dumps({
                'type': 'auth'
            }))
            reply_markup = InlineKeyboardMarkup.from_button(button)
            context.bot.send_message(chat_id=update.effective_chat.id,
                                     text=messages['introMsgAuth'],
                                     reply_markup=reply_markup)

    start_handler = CommandHandler('start', start)
    dispatcher.add_handler(start_handler)

    def callback_query_callback(update: Update, _context):
        data: dict = json.loads(update.callback_query.data)
        op_type = data.get('type')
        if op_type == 'auth':
            update.effective_message.delete()
            # TODO: Start auth flow.

    callback_query_handler = CallbackQueryHandler(callback_query_callback)
    dispatcher.add_handler(callback_query_handler)

    logging.info('Bot initialized')


def run():
    updater.start_polling()
