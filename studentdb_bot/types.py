from typing import TypedDict


class Manifest(TypedDict):
    grades: dict[str, str]
    photos: list[str]
