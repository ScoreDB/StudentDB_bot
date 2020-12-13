from pathlib import Path
from time import time as timestamp

import jwt
import requests
from math import floor

from .types import Manifest

BASE_URL = 'https://api.github.com'
REPOSITORY = 'ScoreDB/studentdb-private-store'
MANIFEST_FILE = 'meta.json'

APP_ID = 92513
INSTALLATION_ID = 13498280


def _get_private_key() -> bytes:
    directory = Path(__file__).resolve().parent.parent / 'keys'
    for path in directory.iterdir():
        if path.name.endswith('.pem'):
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
    token = _get_jwt_token()
    response = requests.post(f'{BASE_URL}/app/installations/{INSTALLATION_ID}/access_tokens', headers={
        'Accept': 'application/vnd.github.v3+json',
        'Authorization': f'Bearer {token}'
    })
    response.raise_for_status()
    return response.json()['token']


def _get_manifest(token: str) -> Manifest:
    """
    Get the manifest file from store repository.

    :return: Content of the manifest file.
    """
    response = requests.get(f'{BASE_URL}/repos/{REPOSITORY}/contents/{MANIFEST_FILE}?ref=latest', headers={
        'Accept': 'application/vnd.github.v3.raw+json',
        'Authorization': f'token {token}'
    })
    response.raise_for_status()
    return response.json()
