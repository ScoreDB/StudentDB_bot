import json

from telegram import Update
from telegram.ext import CallbackContext, CallbackQueryHandler

from .auth import auth_callback, re_auth_callback
from .photos import photos_callback
from .search import class_callback, student_callback, search_callback
from ..cache import get_oc

callbacks = {
    'auth': auth_callback,
    're_auth': re_auth_callback,
    'class': class_callback,
    'student': student_callback,
    'search': search_callback,
    'photos': photos_callback
}


def answer(update: Update, context: CallbackContext):
    context.bot.answer_callback_query(update.callback_query.id)


def callback(update: Update, context: CallbackContext):
    raw_data = update.callback_query.data
    if raw_data:
        if raw_data[:3] == 'oc:':
            data: dict = get_oc(raw_data[3:], update)
        else:
            data: dict = json.loads(update.callback_query.data)
        if data:
            event_type = data.pop('type', None)
            if event_type in callbacks.keys():
                callbacks[event_type](update, context, **data)
    answer(update, context)


callback_handler = CallbackQueryHandler(callback)
