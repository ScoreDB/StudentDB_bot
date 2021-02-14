from telegram import InputTextMessageContent, Update, InlineQueryResultArticle, ParseMode
from telegram.ext import CallbackContext, InlineQueryHandler
from telegram.utils.helpers import mention_html

from ..fetcher import request_search
from ..utils import verify_auth, gender_emoji


def inline_search(update: Update, context: CallbackContext):
    query = update.inline_query.query.strip()
    results = []
    mention = mention_html(context.bot.id, f'@{context.bot.username}')

    if query and verify_auth(context.user_data):

        token = context.user_data.get('token')
        search_result = request_search(token, query, page_size=20)

        for student in search_result.data:
            gender = gender_emoji(student.gender)
            message = f'🔍 “<strong>{query}</strong>” 的搜索结果：\n\n'
            message += f'🧑‍🎓 <strong>{student.id} {student.name}</strong> {gender}\n\n'
            message += '<i>由于 Telegram 相关限制，inline 模式下无法提供更多信息。' \
                       f'请直接与 {mention} 聊天来查询更多信息。</i>'

            results.append(
                InlineQueryResultArticle(
                    id=f'student_summary_{student.id}',
                    title=f'{student.name} {gender}',
                    description=f'{student.id}',
                    input_message_content=InputTextMessageContent(
                        message_text=message,
                        parse_mode=ParseMode.HTML
                    ),
                    thumb_url='https://avatars.githubusercontent.com/u/74541751?s=128&v=4',
                    thumb_width=128,
                    thumb_height=128
                )
            )
    context.bot.answer_inline_query(update.inline_query.id, results,
                                    cache_time=60,
                                    is_personal=True)


inline_search_handler = InlineQueryHandler(inline_search, run_async=True)
