import csv
import logging
from io import StringIO
from itertools import product
from typing import List

import pypinyin

from ._database_models import Student
from .algolia import update_students
from .github import get_manifest, get_file


def generate_pinyin(name: str) -> List[str]:
    pinyin = pypinyin.pinyin(name, pypinyin.Style.NORMAL, True,
                             'ignore', False, False, False)
    result = [' '.join(i) for i in (product(*pinyin))]
    result_short = []
    for pinyin in result:
        pinyin_short = ''.join([i[0] for i in pinyin.split(' ')])
        if pinyin_short not in result_short:
            result_short.append(pinyin_short)
    return result + result_short


def update_database():
    logging.info('Fetching manifest...')
    manifest = get_manifest()

    students = []
    for grade, path in manifest['grades'].items():
        logging.info(f'Processing {grade} student info...')
        grade_data = get_file(path).decode('utf-8')
        with StringIO(grade_data) as stream:
            reader = csv.DictReader(stream, skipinitialspace=True)
            for row in reader:
                student: Student = row
                student['gradeId'] = grade
                student['pinyin'] = generate_pinyin(student['name'])
                students.append(student)

    update_students(students)
    logging.info('Database updated')
