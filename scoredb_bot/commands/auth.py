from requests import RequestException
from scoredb import Client
from telegram import Update, ChatAction, ParseMode, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import CallbackContext, CommandHandler, MessageHandler, Filters
from telegram.utils.helpers import mention_html

from ..matcher import is_token
from ..utils import send_action, is_group, verify_auth, encode_data


@send_action(ChatAction.TYPING)
def start_auth(update: Update, context: CallbackContext):
    if is_group(update):
        mention = mention_html(update.effective_user.id,
                               update.effective_user.name)
        update.effective_chat.send_message(text=f'{mention}，身份认证将在私聊中进行哦~',
                                           parse_mode=ParseMode.HTML)
    if verify_auth(context.user_data):
        button = InlineKeyboardButton('重新认证', callback_data=encode_data('re_auth'))
        reply_markup = InlineKeyboardMarkup.from_button(button)
        update.effective_user.send_message(text='您已完成身份认证，可以开始给我发送要查询的东西啦~ '
                                                '如果密钥因为某种原因失效，可以点击这个按钮重新进行身份认证',
                                           reply_markup=reply_markup)
    else:
        context.user_data.pop('user', None)
        context.user_data.pop('token', None)
        context.user_data['auth_in_progress'] = True
        update.effective_user.send_message(text='请登录 ScoreDB，创建一个包含 '
                                                '<code>studentdb:read</code> '
                                                '权限的 API 密钥，然后在这里发给我',
                                           parse_mode=ParseMode.HTML)


auth_handler = CommandHandler('auth', start_auth)


def auth_callback(update: Update, context: CallbackContext):
    start_auth(update, context)


def re_auth_callback(update: Update, context: CallbackContext):
    context.user_data.pop('user', None)
    context.user_data.pop('token', None)
    context.user_data.pop('auth_in_progress', None)
    start_auth(update, context)


def on_input_token(update: Update, context: CallbackContext):
    if context.user_data.pop('auth_in_progress', False):
        if is_token(token := update.effective_message.text.strip()):
            update.effective_message.delete()
            censored_token = token[:5] + '*' * 10 + token[-3:]
            update.effective_user.send_message(text=f'你输入的密钥是：<code>{censored_token}</code>，'
                                                    f'正在检查密钥有效性...',
                                               parse_mode=ParseMode.HTML)
            try:
                client = Client(token)
                context.user_data['user'] = client.users.get_current_user()
                context.user_data['token'] = token
            except RequestException:
                pass
            if verify_auth(context.user_data):
                update.effective_user.send_message(text='你已完成身份认证，可以开始给我发送要查询的东西啦~')
            else:
                update.effective_user.send_message(text='身份认证失败，可能是由于密钥无效或密钥的权限不足。'
                                                        '请确认你输入了正确的密钥，然后重新开始身份认证')
        else:
            update.effective_user.send_message(text='你输入的似乎不是一个 API 密钥，身份认证已取消')


input_token_handler = MessageHandler(Filters.regex(r'[0-9]*\|.{40}'), on_input_token)
