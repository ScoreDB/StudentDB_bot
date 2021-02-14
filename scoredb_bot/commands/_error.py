import logging
from sys import exc_info
from traceback import format_tb

from telegram import Update, ParseMode
from telegram.ext import CallbackContext
from telegram.utils.helpers import mention_html

from ..env import env

DEVELOPER_ID = env.str('DEVELOPER_ID', None)

if DEVELOPER_ID is None:
    logging.warning('Developer ID not set, error messages will not be sent.')


def error_handler(update: Update, context: CallbackContext):
    if update.effective_message:
        message = '我在处理这条消息期间遇到了一个错误，相关信息已被反馈至开发者'
        update.effective_message.reply_text(text=message)
    trace = '\n'.join(format_tb(exc_info()[2]))
    payload = ''
    if update.effective_user:
        mention = mention_html(update.effective_user.id,
                               update.effective_user.name)
        payload += f'在与 {mention} '
    if update.effective_chat and update.effective_chat.title:
        payload += f'在 {update.effective_chat.title} 中'
    if update.effective_user:
        payload += '聊天时'
    if update.poll:
        payload += f'在 Poll ({update.poll.id}) 中'
    exception = f'{trace}\n{type(context.error).__name__}: {context.error}'
    message = f'我{payload}遇到了一个错误：\n\n<code>Traceback:\n{exception}</code>'
    context.bot.send_message(DEVELOPER_ID,
                             text=message,
                             parse_mode=ParseMode.HTML)
    raise
