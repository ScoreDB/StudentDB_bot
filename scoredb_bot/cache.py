from typing import Optional, Any
from uuid import uuid4 as uuid

from expiringdict import ExpiringDict
from telegram import Update

cache = ExpiringDict(max_len=1000, max_age_seconds=60 * 60 * 24 * 30)


def get_oc(key: str, update: Optional[Update] = None) -> Optional[Any]:
    value = cache.get(key, None)
    if not value and update and update.effective_message:
        update.effective_message.reply_text(text='此会话已过期，请重新发送你的请求',
                                            quote=True)
    return value


def put_oc(value) -> str:
    key = str(uuid())
    cache[key] = value
    return key
