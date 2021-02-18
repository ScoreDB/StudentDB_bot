from requests import HTTPError
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ParseMode, ChatAction
from telegram.ext import CallbackContext, CommandHandler, MessageHandler, Filters

from .auth import re_auth_callback
from ..fetcher import fetch_grade, fetch_class, fetch_student, request_search
from ..matcher import is_grade_id, is_class_id, is_student_id
from ..renderer import render_grade, render_class, render_student, render_search
from ..utils import verify_auth, encode_data, update_or_reply, is_group, send_action


def search(update: Update, context: CallbackContext,
           query: str, page: int = 1):
    if verify_auth(context.user_data):
        token = context.user_data.get('token')
        try:
            if is_grade_id(query):
                render_grade(update, context, fetch_grade(token, query))
            elif is_class_id(query):
                render_class(update, context, fetch_class(token, query), page)
            elif is_student_id(query):
                render_student(update, context, fetch_student(token, query))
            else:
                render_search(update, context, request_search(token, query, page), query)
        except HTTPError as e:
            if e.response.status_code == 403 or e.response.status_code == 401:
                update_or_reply(update, context, text='服务器拒绝访问，请重新进行身份认证')
                re_auth_callback(update, context)
            elif e.response.status_code == 429:
                update_or_reply(update, context, text='请求频率过高，已被服务器限制访问，请一分钟后再试')
            else:
                raise
    else:
        button = InlineKeyboardButton('开始认证', callback_data=encode_data('auth'))
        reply_markup = InlineKeyboardMarkup.from_button(button)
        update_or_reply(update, context,
                        text='你必须先完成身份认证才能开始查询哦',
                        reply_markup=reply_markup)


@send_action(ChatAction.TYPING)
def search_command(update: Update, context: CallbackContext):
    query = ' '.join(context.args) if context.args else None
    if query:
        search(update, context, query)
    else:
        update.effective_chat.send_message(text='搜索请求不能为空，请在命令后面加上要搜索的内容，如 <code>/search abc</code>',
                                           parse_mode=ParseMode.HTML)


command_search_handler = CommandHandler('search', search_command, run_async=True)


def message_search(update: Update, context: CallbackContext):
    if not is_group(update) and update.effective_message.text:
        update.effective_chat.send_chat_action(ChatAction.TYPING)
        search(update, context, update.effective_message.text)


message_search_filters = Filters.text & (~(Filters.command | Filters.via_bot(allow_empty=True)))
message_search_handler = MessageHandler(message_search_filters, message_search, run_async=True)


def class_callback(update: Update, context: CallbackContext,
                   class_id: str, page: int = 1):
    token = context.user_data.get('token', None)
    render_class(update, context, fetch_class(token, class_id), page)


def student_callback(update: Update, context: CallbackContext,
                     student_id: str, from_page: dict = None):
    token = context.user_data.get('token', None)
    render_student(update, context, fetch_student(token, student_id), from_page)


def search_callback(update: Update, context: CallbackContext,
                    query: str, page: int = 1):
    token = context.user_data.get('token', None)
    render_search(update, context, request_search(token, query, page), query)
