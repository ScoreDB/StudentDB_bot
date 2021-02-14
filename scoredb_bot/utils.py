import json
from functools import wraps
from typing import Optional

from scoredb.models import User
from telegram import Update
from telegram.ext import CallbackContext

from .cache import put_oc


def encode_data(event_type: str, **kwargs) -> str:
    kwargs['type'] = event_type
    json_data = json.dumps(kwargs)
    if len(json_data.encode()) > 100:
        return 'oc:' + put_oc(kwargs)
    else:
        return json_data


def gender_emoji(gender: str) -> str:
    if gender == '男':
        return '♂️'
    elif gender == '女':
        return '♀️'


def is_group(update: Update):
    return 'group' in update.effective_chat.type


def send_action(action: str):
    def decorator(func):
        @wraps(func)
        def command_func(update: Update, context: CallbackContext,
                         *args, **kwargs):
            if update.effective_chat is not None:
                update.effective_chat.send_action(action=action)
            return func(update, context, *args, **kwargs)

        return command_func

    return decorator


def update_or_reply(update: Update, context: Optional[CallbackContext] = None, **kwargs):
    if update.effective_message is not None:
        if context and update.effective_message.from_user.id == context.bot.id:
            update.effective_message.edit_text(**kwargs)
        else:
            update.effective_message.reply_text(quote=True, **kwargs)
    else:
        update.effective_chat.send_message(**kwargs)


def verify_auth(user_data: dict):
    token = user_data.get('token', None)
    user: Optional[User] = user_data.get('user', None)
    if token and user:
        return user.check_access(['studentdb:read'])
    return False
