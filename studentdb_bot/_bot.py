import json
import logging
import re
import sys
import traceback
from datetime import datetime, timezone, timedelta
from functools import wraps
from math import ceil
from pathlib import Path
from typing import Optional, List

from requests import HTTPError
from telegram import Update, ChatAction, \
    InlineKeyboardButton, InlineKeyboardMarkup, \
    InputMediaPhoto, ParseMode
from telegram.ext import Updater, CallbackContext, \
    CallbackQueryHandler, CommandHandler, Defaults, \
    Filters, MessageHandler, PicklePersistence
from telegram.utils.helpers import mention_html

from ._env import env
from ._messages import messages
from ._oc import ObjectCache
from .algolia import search_grade, search_class, \
    search_student, universal_search
from .github import check_auth as _check_auth, \
    get_check_auth_url_for_user, get_device_code, \
    get_file, get_manifest
from .types import Manifest, Student, GradeData, ClassData

HOST = env.str('HOST', '0.0.0.0')
PORT = env.int('PORT', 8443)
WEBHOOK_URL = env.str('WEBHOOK_URL', None)
TOKEN = env.str('TELEGRAM_TOKEN')
DEVELOPER_ID = env.str('DEVELOPER_ID')

tz = timezone(timedelta(hours=8), 'Asia/Shanghai')

updater: Optional[Updater] = None

manifest: Manifest = get_manifest()

oc: ObjectCache


def send_action(action: str):
    def decorator(func):
        @wraps(func)
        def command_func(update: Update, context: CallbackContext,
                         *args, **kwargs):
            update.effective_chat.send_action(action=action)
            return func(update, context, *args, **kwargs)

        return command_func

    return decorator


def _init_caches(bot_data: dict):
    global oc
    caches = ['grades', 'classes', 'students', 'search', 'object']
    for cache in caches:
        cache_key = f'{cache}_cache'
        if cache_key not in bot_data:
            bot_data[cache_key] = {}
    oc = ObjectCache(bot_data['object_cache'])


def _init_limits(user_data: dict):
    time_now = datetime.now(tz)
    if 'limits_start' not in user_data:
        user_data['limits_start'] = time_now
    delta = time_now - user_data['limits_start']
    if delta.days >= 1 or 'limits_used' not in user_data:
        user_data['limits_start'] = time_now
        user_data['limits_used'] = 0


def gender_emoji(gender: str) -> str:
    if gender == '男':
        return '♂️'
    elif gender == '女':
        return '♀️'


def _match_regex(pattern: str, query: str) -> Optional[str]:
    pattern = manifest['patterns'][pattern]
    regex = re.compile(pattern, re.IGNORECASE)
    result = regex.match(query)
    if result is not None:
        return result.group().upper()
    return None


def init():
    global updater

    persistence_file = Path(__file__).resolve().parent.parent / 'data/persistence.db'
    persistence = PicklePersistence(persistence_file)
    logging.info(f'Using persistence at "{persistence_file}"')

    defaults = Defaults(parse_mode=ParseMode.HTML)
    updater = Updater(TOKEN, use_context=True,
                      persistence=persistence, defaults=defaults)
    dispatcher = updater.dispatcher

    _init_caches(dispatcher.bot_data)

    @send_action(ChatAction.TYPING)
    def start(update: Update, context: CallbackContext):
        update.effective_chat.send_message(text=messages['intro'])
        if not context.user_data.get('auth_pass', False):
            button = InlineKeyboardButton('开始认证', callback_data=json.dumps({
                'type': 'auth'
            }))
            reply_markup = InlineKeyboardMarkup.from_button(button)
            update.effective_chat.send_message(text=messages['introAuth'],
                                               reply_markup=reply_markup)
        else:
            start_auth(update, context)
        if 'group' in update.effective_chat.type:
            update.effective_chat.send_message(text=messages['groupHint'])

    start_handler = CommandHandler('start', start)
    dispatcher.add_handler(start_handler)

    @send_action(ChatAction.TYPING)
    def limits(update: Update, context: CallbackContext):
        _init_limits(context.user_data)
        if update.effective_user:
            mention = mention_html(update.effective_user.id,
                                   update.effective_user.name) + '，'
        else:
            mention = ''
        limits_all = 30
        limits_used = context.user_data['limits_used']
        limits_remain = limits_all - limits_used
        message = messages['limits'] % (mention, limits_all,
                                        limits_used, limits_remain)
        update.effective_chat.send_message(text=message)

    limits_handler = CommandHandler('limits', limits)
    dispatcher.add_handler(limits_handler)

    @send_action(ChatAction.TYPING)
    def start_auth(update: Update, context: CallbackContext):
        if 'group' in update.effective_chat.type:
            mention = mention_html(update.effective_user.id,
                                   update.effective_user.name)
            message = f'{mention}，身份认证将在私聊中进行哦~'
            update.effective_chat.send_message(text=message)
        if context.user_data.get('auth_pass', False):
            button = InlineKeyboardButton('查看授权', url=get_check_auth_url_for_user())
            reply_markup = InlineKeyboardMarkup.from_button(button)
            update.effective_user.send_message(text=messages['authHint'],
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
            update.effective_user.send_message(text=message,
                                               reply_markup=reply_markup,
                                               disable_web_page_preview=True)
            context.user_data['auth_data'] = auth_data

    start_auth_handler = CommandHandler('auth', start_auth)
    dispatcher.add_handler(start_auth_handler)

    @send_action(ChatAction.TYPING)
    def check_auth(update: Update, context: CallbackContext):
        if not context.user_data.get('auth_pass', False):
            auth_data: Optional[dict] = context.user_data.get('auth_data')
            if auth_data is not None:
                if _check_auth(auth_data['device_code']):
                    message = messages['authSuccess']
                    buttons = [
                        InlineKeyboardButton('查看授权',
                                             url=get_check_auth_url_for_user()),
                        InlineKeyboardButton('查看限额',
                                             callback_data=json.dumps({
                                                 'type': 'limits'
                                             }))
                    ]
                    reply_markup = InlineKeyboardMarkup.from_row(buttons)
                    context.user_data['auth_pass'] = True
                    context.user_data.pop('auth_data', None)
                    update.effective_message.delete()
                    update.effective_user.send_message(text=message,
                                                       reply_markup=reply_markup)
                else:
                    message = messages['authFailed']
                    reply_to = update.effective_message.message_id
                    update.effective_user.send_message(text=message,
                                                       reply_to_message_id=reply_to)
            else:
                message = messages['authNotStarted']
                button = InlineKeyboardButton('开始认证', callback_data=json.dumps({
                    'type': 'auth'
                }))
                reply_markup = InlineKeyboardMarkup.from_button(button)
                update.effective_chat.send_message(text=message,
                                                   reply_markup=reply_markup)
        else:
            message = messages['authRedundant']
            update.effective_chat.send_message(text=message)
            start_auth(update, context)

    def _update_or_reply(update: Update, context: CallbackContext, **kwargs):
        if update.effective_message is not None:
            if update.effective_message.from_user.id == context.bot.id:
                update.effective_message.edit_text(**kwargs)
            else:
                update.effective_message.reply_text(quote=True, **kwargs)
        else:
            update.effective_chat.send_message(**kwargs)

    def _render_students_pagination(update: Update, context: CallbackContext,
                                    message: str, data: List[Student],
                                    page_ref: dict):
        students_count = len(data)
        pages_count = ceil(students_count / 9)
        page = page_ref.get('page', 0)
        if page < 0:
            page = 0
        if page >= pages_count:
            page = pages_count - 1
        page_start = page * 9
        page_end = (page + 1) * 9
        if page_end > students_count:
            page_end = students_count
        page_data = data[page_start:page_end]
        message += f'正在显示第 {page + 1} / {pages_count} 页：\n'
        for i, student in enumerate(page_data):
            message += f'{i + 1}. ' \
                       f'<strong>{student["id"]}</strong> ' \
                       f'{student["name"]} ' \
                       f'{gender_emoji(student["gender"])}\n'
        message += '\n点击下方相应按钮可以查看学生详情'
        buttons = [
            [
                InlineKeyboardButton(
                    f'{p * 3 + i + 1}. {student["name"]}',
                    callback_data=oc.store({
                        'type': 'student_data',
                        'data': student['id'],
                        'from': page_ref
                    })
                )
                for i, student in enumerate(page_data[p * 3:(p + 1) * 3])
            ]
            for p in range(0, 3)
        ]
        buttons.append([])
        if page > 0:
            target_page_ref = page_ref.copy()
            target_page_ref['page'] -= 1
            buttons[-1].append(
                InlineKeyboardButton('上一页', callback_data=oc.store(target_page_ref))
            )
        if page < pages_count - 1:
            target_page_ref = page_ref.copy()
            target_page_ref['page'] += 1
            buttons[-1].append(
                InlineKeyboardButton('下一页', callback_data=oc.store(target_page_ref))
            )
        _update_or_reply(update, context, text=message,
                         reply_markup=InlineKeyboardMarkup(buttons))

    def render_grade(update: Update, context: CallbackContext, data: GradeData):
        if data is False:
            return _update_or_reply(update, context, text=messages['noMatch'])
        classes_count = len(data['classes'].keys())
        students_count = sum(data['classes'].values())
        message = f'🏫 <strong>{data["grade"]} 年级</strong>\n\n'
        message += f'此年级共有 {classes_count} 个班级和 {students_count} 名学生：'
        for class_id, count in data['classes'].items():
            message += f'\n🧑‍🏫 <strong>{class_id}</strong> — {count} 名学生'
        _update_or_reply(update, context, text=message)

    def render_class(update: Update, context: CallbackContext,
                     data: ClassData, page=0):
        if data is False:
            return _update_or_reply(update, context, text=messages['noMatch'])
        students_count = len(data['students'])
        message = f'🧑‍🏫 <strong>{data["class_id"]} 班</strong>\n\n'
        message += f'此班级共有 {students_count} 名学生\n'
        _render_students_pagination(update, context, message, data['students'], {
            'type': 'class_data',
            'data': data['class_id'],
            'page': page
        })

    def render_student(update: Update, context: CallbackContext,
                       data: Student, from_page=None):
        if data is False:
            return _update_or_reply(update, context, text=messages['noMatch'])
        gender = gender_emoji(data["gender"])
        message = f'🧑‍🎓 <strong>{data["id"]} {data["name"]}</strong> {gender}\n'
        message += f'🏫 所在班级：{data["classId"]}\n'
        if len(data.get('birthday', '')) > 0:
            parts = data['birthday'].split('-')
            message += f'🎂 生日：{parts[0]} 年 {parts[1]} 月 {parts[2]} 日\n'
        if len(data.get('eduid', '')) > 0:
            message += f'🆔 教育 ID：{data["eduid"]}'
        buttons = []
        if from_page is not None:
            if type(from_page) != str or not oc.exists(from_page):
                from_page = oc.store(from_page)
            buttons.append([
                InlineKeyboardButton('返回上一页', callback_data=from_page)
            ])
        buttons.append([
            InlineKeyboardButton('查看所在班级', callback_data=json.dumps({
                'type': 'search',
                'data': data['classId']
            })),
            InlineKeyboardButton('获取照片', callback_data=json.dumps({
                'type': 'photo',
                'data': data['id']
            }))
        ])
        _update_or_reply(update, context, text=message,
                         reply_markup=InlineKeyboardMarkup(buttons))

    def render_search(update: Update, context: CallbackContext,
                      data: List[Student], raw_query: str, page: int = 0):
        if data is False or len(data) == 0:
            return _update_or_reply(update, context, text=messages['noMatch'])
        if len(data) == 1:
            return render_student(update, context, data[0])
        _render_students_pagination(update, context, '🔍 搜索结果：\n\n', data, {
            'type': 'search',
            'data': raw_query,
            'page': page
        })

    @send_action(ChatAction.TYPING)
    def search(update: Update, context: CallbackContext,
               raw_query: Optional[str] = None, page: int = 0):
        _init_limits(context.user_data)
        if context.user_data['limits_used'] >= 30:
            update.effective_chat.send_message(messages['limitsReached'])
            return

        if context.user_data.get('auth_pass', False):
            query_parts = []
            if raw_query is None:
                raw_query = str(update.effective_message.text)
                if 'group' in update.effective_chat.type and \
                    '/search' not in raw_query and \
                    f'@{context.bot.username}' not in raw_query:
                    return
            for i in raw_query.split(' '):
                i = i.strip()
                if i[0] != '@' and i[0] != '/' and len(i) > 0:
                    query_parts.append(i)
            query = ' '.join(query_parts)

            if len(query) == 0:
                update.effective_chat.send_message(messages['searchNonEmpty'])
                return

            grade_match = _match_regex('grade', query)
            if grade_match is not None:
                logging.debug(f'Grade match: {grade_match}')
                data = context.bot_data['grades_cache'].get(grade_match, None)
                if data is None:
                    data = search_grade(grade_match)
                    context.user_data['limits_used'] += 1
                    context.bot_data['grades_cache'][grade_match] = data
                render_grade(update, context, data)
                return

            class_match = _match_regex('class', query)
            if class_match is not None:
                logging.debug(f'Class match: {class_match}')
                data = context.bot_data['classes_cache'].get(class_match, None)
                if data is None:
                    data = search_class(class_match)
                    context.user_data['limits_used'] += 1
                    context.bot_data['classes_cache'][class_match] = data
                    if data is not False:
                        for student in data['students']:
                            if student['id'] not in context.bot_data['students_cache']:
                                context.bot_data['students_cache'][student['id']] = student
                render_class(update, context, data, page)
                return

            student_match = _match_regex('student', query)
            if student_match is not None:
                logging.debug(f'Student match: {student_match}')
                data = context.bot_data['students_cache'].get(student_match, None)
                if data is None:
                    data = search_student(student_match)
                    context.user_data['limits_used'] += 1
                    context.bot_data['students_cache'][student_match] = data
                render_student(update, context, data)
                return

            facets = {}
            query_parsed = []
            query_parts = query.split(' ')
            if len(query_parts) > 1:
                for part in query_parts:
                    part = part.strip()
                    if len(part) == 0:
                        continue
                    if 'gradeId' not in facets:
                        grade_match = _match_regex('grade', part)
                        if grade_match is not None:
                            facets['gradeId'] = grade_match
                            continue
                    if 'classId' not in facets:
                        class_match = _match_regex('class', part)
                        if class_match is not None:
                            facets['classId'] = class_match
                            continue
                    query_parsed.append(part)
                query = ' '.join(query_parsed).strip()

                if len(query) == 0:
                    logging.debug(f'Class match: {facets["classId"]}')
                    data = context.bot_data['classes_cache'].get(facets["classId"], None)
                    if data is None:
                        data = search_class(facets["classId"])
                        context.user_data['limits_used'] += 1
                        context.bot_data['classes_cache'][facets["classId"]] = data
                        if data is not False:
                            for student in data['students']:
                                if student['id'] not in context.bot_data['students_cache']:
                                    context.bot_data['students_cache'][student['id']] = student
                    render_class(update, context, data, page)
                    return

            logging.debug(f'Search: {query} with facets {facets}')
            cache_key = f'{query},{facets}'
            data = context.bot_data['search_cache'].get(cache_key, None)
            if data is None:
                data = universal_search(query, facets)
                context.user_data['limits_used'] += 1
                context.bot_data['search_cache'][cache_key] = data
                if type(data) == list:
                    for student in data:
                        if student['id'] not in context.bot_data['students_cache']:
                            context.bot_data['students_cache'][student['id']] = student
            render_search(update, context, data, raw_query, page)
        else:
            context.user_data.pop('auth_data', None)
            check_auth(update, context)

    search_handler = MessageHandler(Filters.text & (~Filters.command), search)
    dispatcher.add_handler(search_handler)

    search_command_handler = CommandHandler('search', search)
    dispatcher.add_handler(search_command_handler)

    def get_photo(update: Update, context: CallbackContext,
                  student: str):
        data = context.bot_data['students_cache'].get(student, None)
        if data is None:
            data = search_student(student)
            context.bot_data['students_cache'][student] = data
        if data is not False:
            update.effective_chat.send_action(action=ChatAction.UPLOAD_PHOTO)
            photos = []
            for photo_template in manifest['photos']:
                photo_path = photo_template.format(**data)
                try:
                    photo_url = get_file(photo_path, False)
                    photos.append(photo_url)
                except HTTPError:
                    pass
            if len(photos) > 0:
                medias = [InputMediaPhoto(i) for i in photos]
                update.effective_message.reply_media_group(media=medias,
                                                           quote=True)
                return
        update.effective_message.reply_text(messages['photoNotFound'],
                                            quote=True)

    def callback_query_callback(update: Update, context: CallbackContext):
        raw_data = update.callback_query.data
        if raw_data is None:
            return
        if raw_data[:3] == 'oc:':
            data: dict = oc.get(raw_data)
        else:
            data: dict = json.loads(update.callback_query.data)
        op_type = data.get('type')
        if op_type == 'auth':
            update.effective_message.delete()
            start_auth(update, context)
        elif op_type == 'auth_check':
            check_auth(update, context)
        elif op_type == 'limits':
            limits(update, context)
        elif op_type == 'search':
            page = data.get('page', 0)
            search(update, context, data.get('data', None), page)
        elif op_type == 'class_data':
            class_id = data.get('data', None)
            class_data = context.bot_data['classes_cache'].get(class_id, None)
            page = int(data.get('page', None))
            if class_data is not None and page is not None:
                if class_data is not None:
                    render_class(update, context, class_data, page)
        elif op_type == 'student_data':
            student_id = data.get('data', None)
            student_data = context.bot_data['students_cache'].get(student_id, None)
            if student_data is not None:
                from_page = data.get('from', None)
                render_student(update, context, student_data, from_page)
        elif op_type == 'photo':
            student_id = data.get('data', None)
            if student_id is not None:
                get_photo(update, context, student_id)

    callback_query_handler = CallbackQueryHandler(callback_query_callback)
    dispatcher.add_handler(callback_query_handler)

    def error(update: Update, context: CallbackContext):
        mention = mention_html(update.effective_user.id,
                               update.effective_user.name)
        if update.effective_message:
            message = messages['error']
            update.effective_message.reply_text(text=message)
        trace = ''.join(traceback.format_tb(sys.exc_info()[2]))
        payload = ''
        if update.effective_user:
            payload += f'在与 {mention} '
        if update.effective_chat and update.effective_chat.title:
            mention = mention_html(update.effective_chat.id,
                                   update.effective_chat.title)
            payload += f'在 {mention} 中'
        if update.effective_user:
            payload += '聊天时'
        if update.poll:
            payload += f'在 Poll ({update.poll.id}) 中'
        exception = f'{trace}\n{type(context.error).__name__}: {context.error}'
        message = messages['errorReport'] % (payload, exception)
        context.bot.send_message(DEVELOPER_ID, text=message)
        raise

    dispatcher.add_error_handler(error)

    logging.info('Bot initialized')


def run():
    updater.start_polling()
    updater.idle()


def run_webhook():
    url = WEBHOOK_URL
    if url is None or url == '':
        raise ValueError("Webhook url can't be empty.")
    if url[-1] != '/':
        url += '/'
    url += TOKEN
    updater.start_webhook(HOST, PORT, TOKEN)
    updater.bot.set_webhook(url)
    updater.idle()
