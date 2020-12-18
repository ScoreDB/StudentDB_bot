from typing import TypedDict, Dict, List


class Manifest(TypedDict):
    patterns: Dict[str, str]
    grades: Dict[str, str]
    photos: List[str]
