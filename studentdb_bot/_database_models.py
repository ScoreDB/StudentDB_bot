from typing import TypedDict, Optional, List


class Student(TypedDict):
    id: str
    gradeId: str
    classId: str
    name: str
    pinyin: List[str]
    gender: str
    birthday: Optional[str]
    eduid: Optional[str]
