import json
import logging
from math import floor
from pathlib import Path
from time import time as timestamp
from typing import Any, Optional, Dict

import jwt
import requests

from ._env import env
from ._messages import messages
from .types import Manifest

with env.prefixed('GITHUB_'):
    BASE_URL = env.str('BASE_URL')
    API_BASE_URL = env.str('API_BASE_URL')
    with env.prefixed('STORE_'):
        REPOSITORY = env.str('REPOSITORY')
        MANIFEST = env.str('MANIFEST')
    APP_ID = env.int('APP_ID')
    INSTALLATION_ID = env.int('INSTALLATION_ID')
    CLIENT_ID = env.str('CLIENT_ID')

access_token_cache: Optional[str] = None
access_token_cache_time: int = 0


def _get_private_key() -> bytes:
    directory = Path(__file__).resolve().parent.parent / 'keys'
    for path in directory.iterdir():
        if path.name.endswith('.pem'):
            logging.info(f'Using private key at "{path}"')
            with path.open('rb') as handler:
                return handler.read()
    raise FileNotFoundError(messages['pkNotFound'])


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
        url = f'{API_BASE_URL}/app/installations/{INSTALLATION_ID}/access_tokens'
        response = requests.post(url, headers={
            'Accept': 'application/vnd.github.v3+json',
            'Authorization': f'Bearer {token}'
        })
        response.raise_for_status()
        access_token_cache = response.json()['token']
        access_token_cache_time = timestamp() + 600
    else:
        logging.debug('Using cached access token')
    return access_token_cache


def get_manifest() -> Manifest:
    """
    Get the manifest file from store repository.

    :return: Content of the manifest file.
    """
    return json.loads(get_file(MANIFEST))


def get_file(path) -> bytes:
    token = _get_access_token()
    if path[0] == '/':
        path = path[1:]
    url = f'{API_BASE_URL}/repos/{REPOSITORY}/contents/{path}'
    response = requests.get(url, headers={
        'Accept': 'application/vnd.github.v3.raw',
        'Authorization': f'token {token}'
    })
    response.raise_for_status()
    return response.content


def _get_current_user(token: str) -> Dict[str, str]:
    """
    :return: Current user data
    """
    url = f'{API_BASE_URL}/user'
    response = requests.get(url, headers={
        'Accept': 'application/vnd.github.v3+json',
        'Authorization': f'Bearer {token}'
    })
    response.raise_for_status()
    return response.json()


def _check_permissions(token: str) -> bool:
    """
    Check if an access token can access the store repository.
    """
    access_token = _get_access_token()
    username = _get_current_user(token)['login']
    url = f'{API_BASE_URL}/repos/{REPOSITORY}/collaborators/{username}/permission'
    response = requests.get(url, headers={
        'Accept': 'application/vnd.github.v3+json',
        'Authorization': f'token {access_token}'
    })
    response.raise_for_status()
    return response.json()['permission'] != 'none'


def get_device_code() -> Dict[str, Any]:
    """
    Start a device-flow authorization.

    Reference: https://docs.github.com/developers/apps/authorizing-oauth-apps#device-flow
    """
    url = f'{BASE_URL}/login/device/code'
    response = requests.post(url, headers={
        'Accept': 'application/json'
    }, json={
        'client_id': CLIENT_ID
    })
    response.raise_for_status()
    return response.json()


def check_auth(device_code: str) -> bool:
    """
    Check if a device-flow authorization is successful.
    """
    url = f'{BASE_URL}/login/oauth/access_token'
    response = requests.post(url, headers={
        'Accept': 'application/json'
    }, json={
        'client_id': CLIENT_ID,
        'device_code': device_code,
        'grant_type': 'urn:ietf:params:oauth:grant-type:device_code'
    })
    response.raise_for_status()
    try:
        access_token = response.json()['access_token']
    except KeyError:
        return False
    return _check_permissions(access_token)


def get_check_auth_url_for_user() -> str:
    return f'{BASE_URL}/settings/connections/applications/{CLIENT_ID}'
