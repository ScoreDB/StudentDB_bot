from telegram import ChatAction, Update, ParseMode
from telegram.ext import CommandHandler

from ..utils import send_action, is_group

message = '欢迎使用 StudentDB Bot！\n' \
          '\n' \
          '通过给我发送消息，可以快速在 ScoreDB 中查询数据\n' \
          '未进行身份认证的用户可以通过 <code>/auth</code> 命令进行身份认证\n' \
          '\n' \
          '用法：\n' \
          '在私聊中，可以直接向我发送要查询的内容\n' \
          '在群组中，可以使用 <code>/search</code> 命令查询\n' \
          '我还支持 Telegram 的 inline 模式，即在聊天框输入 <code>@StudentDB_bot</code> 直接查询\n' \
          '\n' \
          '你可以在 GitHub 的 ' \
          '<a href="https://github.com/ScoreDB/telegram-bot.git">' \
          'ScoreDB/telegram-bot</a> 找到本 bot 的源码'


@send_action(ChatAction.TYPING)
def help_command(update: Update, _context):
    if is_group(update):
        update.effective_user.send_message(text=message, parse_mode=ParseMode.HTML)
        update.effective_message.reply_text(text='为防止刷屏，我已将帮助信息私聊给你', quote=True)
    else:
        update.effective_chat.send_message(text=message, parse_mode=ParseMode.HTML)


help_handler = CommandHandler('help', help_command, run_async=True)
