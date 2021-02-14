from telegram import ChatAction, Update, InlineKeyboardButton, InlineKeyboardMarkup, ParseMode
from telegram.ext import CallbackContext, CommandHandler

from ..utils import verify_auth, is_group, update_or_reply, encode_data


def start_command(update: Update, context: CallbackContext):
    if not (context.args and ' '.join(context.args) == '_quiet'):
        update.effective_chat.send_chat_action(ChatAction.TYPING)
        update.effective_chat.send_message(text='欢迎使用本 bot，我可以帮你查询 StudentDB 上的数据~')
        if not verify_auth(context.user_data):
            button = InlineKeyboardButton('开始认证', callback_data=encode_data('auth'))
            reply_markup = InlineKeyboardMarkup.from_button(button)
            update_or_reply(update, context,
                            text='不过，在开始之前，我必须验证你的身份',
                            reply_markup=reply_markup)
        if is_group(update):
            update.effective_chat.send_message(text='这好像是一个群组...由于我已开启隐私模式，没法直接看到你们的消息。'
                                                    '如果从我这里查询信息，请使用 <code>/search@StudentDB_bot</code> 命令或者 inline 模式',
                                               parse_mode=ParseMode.HTML)


start_handler = CommandHandler('start', start_command, run_async=True)
