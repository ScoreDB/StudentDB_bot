import re


def _match(pattern: str, subject: str):
    regex = re.compile(pattern)
    result = regex.match(subject)
    if result is not None:
        return result.group()
    return None


def is_token(subject: str):
    return _match(r'^[0-9]*\|.{40}$', subject) is not None


def is_grade_id(subject: str):
    return _match(r'^[xXcCgG][0-9]{2}$', subject)


def is_class_id(subject: str):
    return _match(r'^[xXcCgG][0-9]{4}$', subject)


def is_student_id(subject: str):
    return _match(r'(^[xXcCgG][0-9]{6}$)|(^[0-9]{8}$)$', subject)
