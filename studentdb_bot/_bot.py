import json
import logging
from pathlib import Path
from typing import Optional

from telegram import Update, InlineKeyboardButton, \
    InlineKeyboardMarkup, ParseMode
from telegram.ext import Updater, CallbackContext, \
    CallbackQueryHandler, CommandHandler, \
    PicklePersistence

from ._database import Database
from ._env import env
from ._messages import messages
from .github import check_auth as _check_auth, \
    get_check_auth_url_for_user, get_device_code

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
        update.effective_chat.send_message(text=messages['introMsg'])
        if not context.user_data.get('auth_pass', False):
            button = InlineKeyboardButton('开始认证', callback_data=json.dumps({
                'type': 'auth'
            }))
            reply_markup = InlineKeyboardMarkup.from_button(button)
            update.effective_chat.send_message(text=messages['introMsgAuth'],
                                               reply_markup=reply_markup)
        else:
            start_auth(update, context)

    start_handler = CommandHandler('start', start)
    dispatcher.add_handler(start_handler)

    def start_auth(update: Update, context: CallbackContext):
        if context.user_data.get('auth_pass', False):
            button = InlineKeyboardButton('查看授权', url=get_check_auth_url_for_user())
            reply_markup = InlineKeyboardMarkup.from_button(button)
            update.effective_chat.send_message(text=messages['authHint'],
                                               parse_mode=ParseMode.HTML,
                                               reply_markup=reply_markup,
                                               disable_web_page_preview=True)
        else:
            auth_data = get_device_code()
            message = messages['authStart'] % (auth_data['expires_in'] / 60,
                                               auth_data['verification_uri'],
                                               auth_data['user_code'])
            button = InlineKeyboardButton('已完成认证', callback_data=json.dumps({
                'type': 'auth_check'
            }))
            reply_markup = InlineKeyboardMarkup.from_button(button)
            update.effective_chat.send_message(text=message,
                                               parse_mode=ParseMode.HTML,
                                               reply_markup=reply_markup,
                                               disable_web_page_preview=True)
            context.user_data['auth_data'] = auth_data

    start_auth_handler = CommandHandler('auth', start_auth)
    dispatcher.add_handler(start_auth_handler)

    def check_auth(update: Update, context: CallbackContext):
        if not context.user_data.get('auth_pass', False):
            auth_data: Optional[dict] = context.user_data.get('auth_data')
            if auth_data is not None:
                if _check_auth(auth_data['device_code']):
                    message = messages['authSuccess']
                    button = InlineKeyboardButton('查看授权',
                                                  url=get_check_auth_url_for_user())
                    reply_markup = InlineKeyboardMarkup.from_button(button)
                    context.user_data['auth_pass'] = True
                    del context.user_data['auth_data']
                    update.effective_message.delete()
                    update.effective_user.send_message(text=message,
                                                       reply_markup=reply_markup)
                else:
                    message = messages['authFailed']
                    reply_to = update.effective_message.message_id
                    update.effective_chat.send_message(text=message,
                                                       reply_to_message_id=reply_to)
            else:
                message = messages['authNotStarted']
                button = InlineKeyboardButton('开始认证', callback_data=json.dumps({
                    'type': 'auth'
                }))
                reply_markup = InlineKeyboardMarkup.from_button(button)
                update.effective_message.delete()
                update.effective_chat.send_message(text=message,
                                                   reply_markup=reply_markup)
        else:
            message = messages['authRedundant']
            update.effective_message.delete()
            update.effective_chat.send_message(text=message,
                                               parse_mode=ParseMode.HTML)
            start_auth(update, context)

    def callback_query_callback(update: Update, context: CallbackContext):
        data: dict = json.loads(update.callback_query.data)
        op_type = data.get('type')
        if op_type == 'auth':
            update.effective_message.delete()
            start_auth(update, context)
        elif op_type == 'auth_check':
            check_auth(update, context)

    callback_query_handler = CallbackQueryHandler(callback_query_callback)
    dispatcher.add_handler(callback_query_handler)

    logging.info('Bot initialized')


def run():
    updater.start_polling()
