from typing import Dict, Any
from uuid import uuid4 as uuid


class ObjectCache:
    cache: Dict[str, Any]

    def __init__(self, cache: dict):
        self.cache = cache

    def get(self, key: str, default=None):
        return self.cache.get(key, default)

    def store(self, value) -> str:
        key = 'oc:' + str(uuid())
        self.cache[key] = value
        return key

    def exists(self, key):
        return key in self.cache
