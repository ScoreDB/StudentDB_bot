from math import ceil
from typing import Optional, Union, List

from dateutil.parser import parse
from scoredb.client import Pagination
from scoredb.models import Grade, Class, StudentSummary, Student
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ParseMode
from telegram.ext import CallbackContext

from .utils import update_or_reply, gender_emoji, encode_data


def render_grade(update: Update, context: CallbackContext,
                 grade: Optional[Grade]):
    if not grade:
        return update_or_reply(update, context, text='未找到匹配的年级')
    message = f'🏫 <strong>{grade.id} 年级</strong>\n\n'
    message += f'此年级共有 {grade.classesCount} 个班级和 {grade.studentsCount} 名学生：'
    for class_ in grade.classes:
        message += f'\n🧑‍🏫 <strong>{class_.id}</strong> — {class_.studentsCount} 名学生'
    update_or_reply(update, context,
                    text=message,
                    parse_mode=ParseMode.HTML)


def render_class(update: Update, context: CallbackContext,
                 class_: Optional[Class], page: int = 1):
    if not class_:
        return update_or_reply(update, context, text='未找到匹配的班级')
    message = f'🧑‍🏫 <strong>{class_.id} 班</strong>\n\n'
    message += f'此班级共有 {class_.studentsCount} 名学生：\n'
    kwargs = render_students_pagination(class_.students, message, {
        'event_type': 'class',
        'class_id': class_.id,
        'page': page
    })
    update_or_reply(update, context, **kwargs)


def render_student(update: Update, context: CallbackContext,
                   student: Optional[Student],
                   from_page: Optional[dict] = None):
    if not student:
        return update_or_reply(update, context, text='未找到匹配的学生')
    gender = gender_emoji(student.gender)
    message = f'🧑‍🎓 <strong>{student.id} {student.name}</strong> {gender}\n'
    message += f'🏫 所在班级：{student.classId}\n'
    if student.birthday:
        birthday = parse(student.birthday)
        message += f'🎂 生日：{birthday.year} 年 {birthday.month} 月 {birthday.day} 日\n'
    if student.eduid:
        message += f'🆔 教育 ID：{student.eduid}'
    buttons = []
    if from_page:
        buttons.append([
            InlineKeyboardButton('返回上一页', callback_data=encode_data(**from_page))
        ])
    buttons.append([
        InlineKeyboardButton('查看所在班级', callback_data=encode_data('class', class_id=student.classId)),
        InlineKeyboardButton('获取照片', callback_data=encode_data('photos', student_id=student.id))
    ])
    update_or_reply(update, context,
                    text=message,
                    reply_markup=InlineKeyboardMarkup(buttons),
                    parse_mode=ParseMode.HTML)


def render_search(update: Update, context: CallbackContext,
                  pagination: Pagination[StudentSummary],
                  query: str):
    if pagination.count() == 0:
        update_or_reply(update, context, text='未搜索到符合条件的结果')
    else:
        message = f'🔍 “<strong>{query}</strong>” 的搜索结果：\n\n'
        kwargs = render_students_pagination(pagination, message, {
            'event_type': 'search',
            'query': query,
            'page': pagination.current_page
        })
        update_or_reply(update, context, **kwargs)


def render_students_pagination(pagination: Union[Pagination[StudentSummary], List[StudentSummary]],
                               prepend_message: str,
                               page_ref: dict):
    message = prepend_message

    def create_pagination(students: List[StudentSummary], current_page: int) -> Pagination[StudentSummary]:
        count_all = len(students)
        pages = ceil(count_all / 9)
        size = 9
        if current_page < 1:
            current_page = 1
        if current_page > pages:
            current_page = pages
        start = (current_page - 1) * size
        end = current_page * size
        if end > count_all:
            end = count_all
        data = students[start:end]
        return Pagination(data, current_page, pages)

    if type(pagination) != Pagination:
        pagination = create_pagination(pagination, page_ref.get('page', 1))

    message += f'正在显示第 {pagination.current_page} / {pagination.pages} 页：\n'
    for i, student in enumerate(pagination.data):
        message += f'{i + 1}. ' \
                   f'<strong>{student.id}</strong> ' \
                   f'{student.name} ' \
                   f'{gender_emoji(student.gender)}\n'
    message += '\n点击下方相应按钮可以查看学生详情'

    buttons = [
        [
            InlineKeyboardButton(
                f'{p * 3 + i + 1}. {student.name}',
                callback_data=encode_data('student', student_id=student.id, from_page=page_ref)
            )
            for i, student in enumerate(pagination.data[p * 3:(p + 1) * 3])
        ]
        for p in range(0, 3)
    ]

    buttons.append([
        InlineKeyboardButton('⚠ 获取本页所有照片')
    ])

    switch_page_buttons = []
    if pagination.has_previous_page():
        target_page_ref = page_ref.copy()
        target_page_ref['page'] -= 1
        switch_page_buttons.append(
            InlineKeyboardButton('上一页', callback_data=encode_data(**target_page_ref))
        )
    if pagination.has_next_page():
        target_page_ref = page_ref.copy()
        target_page_ref['page'] += 1
        switch_page_buttons.append(
            InlineKeyboardButton('下一页', callback_data=encode_data(**target_page_ref))
        )

    if len(switch_page_buttons) > 0:
        buttons.append(switch_page_buttons)

    return {
        'text': message,
        'reply_markup': InlineKeyboardMarkup(buttons),
        'parse_mode': ParseMode.HTML
    }
