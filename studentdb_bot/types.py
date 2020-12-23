from typing import TypedDict, Dict, List, Optional


class Manifest(TypedDict):
    patterns: Dict[str, str]
    grades: Dict[str, str]
    photos: List[str]


class Student(TypedDict):
    id: str
    gradeId: str
    classId: str
    name: str
    pinyin: Optional[List[str]]
    gender: str
    birthday: Optional[str]
    eduid: Optional[str]


class GradeData(TypedDict):
    grade: str
    classes: Dict[str, int]


class ClassData(TypedDict):
    class_id: str
    students: List[Student]
