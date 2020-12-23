import logging
from typing import List, Union, Optional

from algoliasearch.search_client import SearchClient

from ._env import env
from .types import GradeData, ClassData, Student

with env.prefixed('ALGOLIA_'):
    APP_ID = env.str('APP_ID')
    API_KEY = env.str('API_KEY')

client = SearchClient.create(APP_ID, API_KEY)

index = client.init_index('students')

logging.info('Algolia initialized')


def update_students(students: List[Student]):
    logging.info('Uploading students\' data...')
    index.replace_all_objects(students, {
        'autoGenerateObjectIDIfNotExist': True
    })


def search_grade(query: str) -> Union[GradeData, bool]:
    response = index.search_for_facet_values('classId', '', {
        'facetFilters': [f'gradeId:{query}'],
        'maxFacetHits': 100,
        'sortFacetValuesBy': 'alpha'
    })['facetHits']
    return {
        'grade': query,
        'classes': {i['value']: i['count'] for i in response}
    } if len(response) > 0 else False


def search_class(query: str) -> Union[ClassData, bool]:
    response = index.search('', {
        'attributesToHighlight': [],
        'facetFilters': [f'classId:{query}'],
        'hitsPerPage': 1000
    })['hits']
    return {
        'class_id': query,
        'students': response
    } if len(response) > 0 else False


def search_student(query: str) -> Union[Student, bool]:
    response = index.search('', {
        'attributesToHighlight': [],
        'facetFilters': [[f'id:{query}', f'eduid:{query}']],
        'hitsPerPage': 1
    })['hits']
    return response[0] if len(response) > 0 else False


def universal_search(query: str, facets: Optional[dict] = None) -> Union[List[Student], bool]:
    if facets is None:
        facets = {}
    response = index.search(query, {
        'attributesToHighlight': [],
        'facetFilters': [f'{k}:{v}' for k, v in facets.items()],
        'hitsPerPage': 1000
    })['hits']
    return response if len(response) > 0 else False
