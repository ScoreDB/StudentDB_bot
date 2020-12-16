from typing import TypedDict, Dict, List


class Manifest(TypedDict):
    grades: Dict[str, str]
    photos: List[str]
