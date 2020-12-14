import logging
from math import floor
from pathlib import Path
from time import time as timestamp
from typing import Optional

import jwt
import requests

from . import env
from .types import Manifest

with env.prefixed('GITHUB_'):
    BASE_URL = env.str('BASE_URL')
    with env.prefixed('STORE_'):
        REPOSITORY = env.str('REPOSITORY')
        MANIFEST = env.str('MANIFEST')
    APP_ID = env.int('APP_ID')
    INSTALLATION_ID = env.int('INSTALLATION_ID')

access_token_cache: Optional[str] = None
access_token_cache_time: int = 0


def _get_private_key() -> bytes:
    directory = Path(__file__).resolve().parent.parent / 'keys'
    for path in directory.iterdir():
        if path.name.endswith('.pem'):
            logging.info(f'Using private key at "{path}".')
            with path.open('rb') as handler:
                return handler.read()
    raise FileNotFoundError('Private key file not found. Please place your private key in the `keys` directory.')


def _get_jwt_token() -> str:
    """
    Generate a JWT token with the app's private key.

    Reference: https://docs.github.com/developers/apps/authenticating-with-github-apps#authenticating-as-a-github-app

    :return: A JWT token representing the app it self.
    """
    key = _get_private_key()
    time = floor(timestamp())
    return jwt.encode({
        'iat': time,  # Issued at time
        'exp': time + 10 * 60,  # Expiry (10 minutes)
        'iss': APP_ID  # GitHub App's identifier
    }, key, 'RS256').decode('utf-8')


def _get_access_token() -> str:
    """
    Creates an installation access token for the app's installation on an account.

    Reference: https://docs.github.com/rest/reference/apps#create-an-installation-access-token-for-an-app

    :return: An installation access token.
    """
    global access_token_cache
    global access_token_cache_time
    if access_token_cache is None or timestamp() > access_token_cache_time - 60:
        token = _get_jwt_token()
        response = requests.post(f'{BASE_URL}/app/installations/{INSTALLATION_ID}/access_tokens', headers={
            'Accept': 'application/vnd.github.v3+json',
            'Authorization': f'Bearer {token}'
        })
        response.raise_for_status()
        access_token_cache = response.json()['token']
        access_token_cache_time = timestamp() + 600
    else:
        logging.debug('Using cached access token.')
    return access_token_cache


def _get_manifest(token: str) -> Manifest:
    """
    Get the manifest file from store repository.

    :return: Content of the manifest file.
    """
    response = requests.get(f'{BASE_URL}/repos/{REPOSITORY}/contents/{MANIFEST}', headers={
        'Accept': 'application/vnd.github.v3.raw+json',
        'Authorization': f'token {token}'
    })
    response.raise_for_status()
    return response.json()
