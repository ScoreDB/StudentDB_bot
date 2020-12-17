import logging
from typing import List

from algoliasearch.search_client import SearchClient

from ._database_models import Student
from ._env import env

with env.prefixed('ALGOLIA_'):
    APP_ID = env.str('APP_ID')
    API_KEY = env.str('API_KEY')

client = SearchClient.create(APP_ID, API_KEY)

index = client.init_index('students')

logging.info('Algolia initialized.')


def update_students(students: List[Student]):
    logging.info('Uploading students\' data...')
    index.replace_all_objects(students, {
        'autoGenerateObjectIDIfNotExist': True
    })
