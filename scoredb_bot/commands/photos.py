from typing import List

from telegram import Update, ChatAction, InputMediaPhoto
from telegram.ext import CallbackContext

from ..fetcher import fetch_student_photos
from ..utils import send_action


@send_action(ChatAction.UPLOAD_PHOTO)
def send_photos(update: Update, photos: List[str]):
    medias = [InputMediaPhoto(i) for i in photos]
    update.effective_message.reply_media_group(media=medias, quote=True)


def photos_callback(update: Update, context: CallbackContext,
                    student_id: str):
    token = context.user_data.get('token', None)
    photos = fetch_student_photos(token, student_id)
    if len(photos) == 0:
        update.effective_chat.send_chat_action(ChatAction.TYPING)
        update.effective_message.reply_text(text='未找到请求的照片，可能是由于获取照片所需的数据不足',
                                            quote=True)
    else:
        send_photos(update, photos)


def all_photos_callback(update: Update, context: CallbackContext,
                        students: List[str]):
    token = context.user_data.get('token', None)
    photos = []
    for student_id in students:
        student_photos = fetch_student_photos(token, student_id)
        if len(student_photos) > 0:
            photos.append(student_photos[0])
    if len(photos) == 0:
        update.effective_chat.send_chat_action(ChatAction.TYPING)
        update.effective_message.reply_text(text='本页学生没有相关照片信息',
                                            quote=True)
    else:
        send_photos(update, photos)
