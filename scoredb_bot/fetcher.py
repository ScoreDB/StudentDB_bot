from functools import lru_cache

from requests import HTTPError
from scoredb import Client


@lru_cache(maxsize=64)
def fetch_grade(token: str, grade_id: str):
    try:
        return Client(token).studentdb.get_grade_details(grade_id)
    except HTTPError as e:
        if e.response.status_code == 404:
            return None
        raise


@lru_cache(maxsize=64)
def fetch_class(token: str, class_id: str):
    try:
        return Client(token).studentdb.get_class_details(class_id)
    except HTTPError as e:
        if e.response.status_code == 404:
            return None
        raise


@lru_cache(maxsize=256)
def fetch_student(token: str, student_id: str):
    try:
        return Client(token).studentdb.get_student_details(student_id)
    except HTTPError as e:
        if e.response.status_code == 404:
            return None
        raise


@lru_cache(maxsize=128)
def fetch_student_photos(token: str, student_id: str):
    photos = Client(token).studentdb.get_student_photos(student_id)
    if not photos:
        photos = []
    return photos


@lru_cache(maxsize=64)
def request_search(token: str, query: str, page: int = 1):
    return Client(token).studentdb.search_student(query, page)
